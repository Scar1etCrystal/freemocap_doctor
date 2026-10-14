"""Roll a DSH session log back to before a failed compaction.

Usage:
  python rollback.py <session.v4.jsonl.zstd> <boundarySeq> [--write <outPath>]

Dry run prints the surface fold before/after; --write emits a re-framed artifact
(checksummed zstd frames, first frame exactly the header line) and verifies it.
"""
import io
import json
import struct
import sys

import zstandard as zstd


def decompress_frame(payload):
    """Streaming decompress of one frame (writer frames omit the content size)."""
    return zstd.ZstdDecompressor().stream_reader(io.BytesIO(payload)).read()


def make_compressor():
    """Match the writer: checksummed frames without a declared content size."""
    return zstd.ZstdCompressor(write_checksum=True, write_content_size=False)

ZSTD_MAGIC = 0xFD2FB528
MAX_FRAME_PLAINTEXT = 4 * 1024 * 1024
SURFACE_TYPES = {"system/message", "user/message", "assistant/message", "tool/result"}


def scan_frames(buffer):
    """Structural zstd frame scan, mirroring the JSONL backend's scanZstdFrames."""
    frames = []
    offset = 0
    total = len(buffer)
    while offset < total:
        start = offset
        if total - offset < 4:
            return frames, start
        if struct.unpack_from("<I", buffer, offset)[0] != ZSTD_MAGIC:
            raise ValueError(f"invalid frame magic at byte {offset}")
        offset += 4
        if offset == total:
            return frames, start
        descriptor = buffer[offset]
        offset += 1
        if descriptor & 24:
            raise ValueError(f"reserved frame-header bit at byte {offset - 1}")
        content_size_flag = descriptor >> 6
        single_segment = bool(descriptor & 32)
        checksum = bool(descriptor & 4)
        dictionary_flag = descriptor & 3
        dictionary_bytes = 4 if dictionary_flag == 3 else dictionary_flag
        content_size_bytes = (1 if single_segment else 0) if content_size_flag == 0 else 1 << content_size_flag
        remaining_header_bytes = (0 if single_segment else 1) + dictionary_bytes + content_size_bytes
        if total - offset < remaining_header_bytes:
            return frames, start
        offset += remaining_header_bytes
        while True:
            if total - offset < 3:
                return frames, start
            block_header = int.from_bytes(buffer[offset:offset + 3], "little")
            offset += 3
            last_block = bool(block_header & 1)
            block_type = (block_header >> 1) & 3
            block_size = block_header >> 3
            if block_type == 3:
                raise ValueError(f"reserved block type at byte {offset - 3}")
            payload_bytes = 1 if block_type == 1 else block_size
            if total - offset < payload_bytes:
                return frames, start
            offset += payload_bytes
            if last_block:
                break
        if checksum:
            if total - offset < 4:
                return frames, start
            offset += 4
        frames.append((start, offset))
    return frames, None


def decode_log(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    frames, torn = scan_frames(raw)
    if torn is not None:
        raise ValueError(f"torn frame at byte {torn}")
    dctx = zstd.ZstdDecompressor()
    plaintexts = [decompress_frame(raw[a:b]) for a, b in frames]
    text = b"".join(plaintexts).decode("utf-8")
    lines = text.split("\n")
    if lines[-1] != "":
        raise ValueError("log does not end with a newline")
    lines.pop()
    header = json.loads(lines[0])
    if header.get("type") != "session":
        raise ValueError("first line is not a session header")
    first_frame_text = plaintexts[0].decode("utf-8")
    records = [json.loads(line) for line in lines[1:]]
    return {
        "raw": raw,
        "frames": frames,
        "lines": lines,
        "records": records,
        "header_line": lines[0],
        "header": header,
        "first_frame_text": first_frame_text,
    }


def fold_surface(records):
    """Left-to-right surface fold over stored records (v-live rules)."""
    nodes = []
    for rec in records:
        if rec.get("type") not in SURFACE_TYPES:
            continue
        op = rec.get("surfaceOp")
        if op is None:
            continue
        seq = rec["seq"]
        if op == "append":
            nodes.append(seq)
            continue
        start_seq, end_seq = op["startSeq"], op["endSeq"]
        start_idx = nodes.index(start_seq)
        end_idx = nodes.index(end_seq)
        if start_idx > end_idx:
            raise ValueError(f"replace range inverted at seq {seq}")
        shadowed = nodes[start_idx:end_idx + 1]
        declared = rec.get("sourceEventSeqs")
        if declared is not None:
            missing = [s for s in shadowed if s not in declared]
            if missing:
                raise ValueError(f"replace at seq {seq} misses shadowed nodes {missing[:5]}")
        nodes[start_idx:end_idx + 1] = [seq]
    return nodes


def frame_lines(lines, first_line):
    """Header line alone in frame 1, then chunks of whole event lines."""
    out = [make_compressor().compress((first_line + "\n").encode("utf-8"))]
    chunk, size = [], 0
    for line in lines:
        line_size = len(line.encode("utf-8")) + 1
        if chunk and size + line_size > MAX_FRAME_PLAINTEXT:
            out.append(make_compressor().compress(("\n".join(chunk) + "\n").encode("utf-8")))
            chunk, size = [], 0
        chunk.append(line)
        size += line_size
    if chunk:
        out.append(make_compressor().compress(("\n".join(chunk) + "\n").encode("utf-8")))
    return b"".join(out), len(out)


def main(argv):
    log_path, boundary = argv[0], int(argv[1])
    out_path = argv[argv.index("--write") + 1] if "--write" in argv else None

    log = decode_log(log_path)
    records = log["records"]
    for index, rec in enumerate(records):
        if rec.get("seq") != index:
            raise ValueError(f"seq continuity broken at index {index}")
    print(f"file            : {log_path}")
    print(f"frames          : {len(log['frames'])}; first frame = {log['first_frame_text'][:40]!r}")
    print(f"header          : id={log['header']['id']} cwd={log['header'].get('cwd')}")
    print(f"records         : {len(records)} (last seq {records[-1]['seq']} {records[-1]['type']})")

    live_nodes = fold_surface(records)
    print(f"surface CURRENT : {len(live_nodes)} nodes, tail={live_nodes[-5:]}")

    kept = records[:boundary + 1]
    dropped = records[boundary + 1:]
    restored_nodes = fold_surface(kept)
    print(f"boundary        : seq {boundary} = {kept[-1]['type']} (turn {kept[-1].get('data', {}).get('turn')})")
    print(f"dropped         : {len(dropped)} records: {[r['type'] for r in dropped]}")
    print(f"surface RESTORED: {len(restored_nodes)} nodes, tail={restored_nodes[-5:]}")
    print(f"  first 8 nodes : {restored_nodes[:8]}")

    if out_path is not None:
        payload, frame_count = frame_lines([line for line in log["lines"][1:boundary + 2]], log["header_line"])
        with open(out_path, "wb") as fh:
            fh.write(payload)
        print(f"wrote           : {out_path} ({len(payload)} bytes, {frame_count} frames)")

        check = decode_log(out_path)
        assert check["header_line"] == log["header_line"], "header changed"
        assert check["first_frame_text"] == log["header_line"] + "\n", "first frame is not exactly the header line"
        assert len(check["records"]) == boundary + 1, "record count mismatch"
        assert check["records"][-1] == kept[-1], "last record mismatch"
        assert fold_surface(check["records"]) == restored_nodes, "surface fold differs"
        print(f"verify OK       : {len(check['frames'])} frames, {len(check['records'])} records, "
              f"last seq {check['records'][-1]['seq']}, surface nodes {len(restored_nodes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
