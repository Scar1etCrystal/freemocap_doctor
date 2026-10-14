"""Dump the structure of a DSH session log (.jsonl.zstd) without printing payloads."""
import sys, json, collections
import zstandard as zstd

path = sys.argv[1]
dctx = zstd.ZstdDecompressor()
with open(path, 'rb') as fh:
    data = dctx.stream_reader(fh).read()
text = data.decode('utf-8', 'replace')
lines = [l for l in text.split('\n') if l.strip()]
print(f"file={path}")
print(f"bytes_decompressed={len(data)} lines={len(lines)}")

counts = collections.Counter()
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
    except Exception as e:
        print(f"[{i}] PARSE ERROR {e}: {line[:200]}")
        continue
    t = obj.get('type') or obj.get('kind') or '?'
    counts[t] += 1
print("types:", dict(counts))

if len(sys.argv) > 2 and sys.argv[2] == 'detail':
    for i, line in enumerate(lines):
        obj = json.loads(line)
        t = obj.get('type') or obj.get('kind') or '?'
        keys = sorted(obj.keys())
        seq = obj.get('seq')
        extra = ''
        payload = obj.get('payload') or obj.get('data') or obj.get('message')
        if isinstance(payload, dict):
            extra = 'payload_keys=' + ','.join(sorted(payload.keys()))[:200]
        print(f"[{i}] type={t} seq={seq} keys={keys} {extra}")
