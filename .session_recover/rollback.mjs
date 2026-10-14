/**
 * Roll back a DSH session log to before a failed compaction.
 *
 * Reads <session.v4.jsonl.zstd>, drops the trailing events with seq > BOUNDARY,
 * rewrites the artifact as checksummed zstd frames (frame 1 = header line only,
 * matching the JSONL backend's layout contract), and reports the surface fold
 * before/after using DSH's own codec.
 *
 * Usage:
 *   node rollback.mjs <session.v4.jsonl.zstd> <boundarySeq> [--write <outPath>]
 * Dry run (no --write): prints diagnostics only.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { zstdDecompressSync, zstdCompressSync, constants } from 'node:zlib';
import { pathToFileURL } from 'node:url';

const SESSION_LIB = 'C:/Users/George/.dsh/profiles/node_modules/@deepseek-ai/dsh-session/lib/index.js';
const { decodeStorageRecord, foldSurface } = await import(pathToFileURL(SESSION_LIB).href);

const ZSTD_MAGIC = 4247762216;
const CHECKSUM_OPTIONS = { params: { [constants.ZSTD_c_checksumFlag]: 1 } };
const MAX_FRAME_PLAINTEXT = 4 * 1024 * 1024;

/** Copy of the backend's structural frame scanner. */
function scanFrames(buffer) {
  const frames = [];
  let offset = 0;
  while (offset < buffer.length) {
    const start = offset;
    if (buffer.length - offset < 4) return { frames, tornStart: start };
    if (buffer.readUInt32LE(offset) !== ZSTD_MAGIC) throw new Error(`invalid frame magic at byte ${offset}`);
    offset += 4;
    if (offset === buffer.length) return { frames, tornStart: start };
    const descriptor = buffer.readUInt8(offset);
    offset += 1;
    if ((descriptor & 24) !== 0) throw new Error(`reserved frame-header bit at byte ${offset - 1}`);
    const contentSizeFlag = descriptor >>> 6;
    const singleSegment = (descriptor & 32) !== 0;
    const checksum = (descriptor & 4) !== 0;
    const dictionaryFlag = descriptor & 3;
    const dictionaryBytes = dictionaryFlag === 3 ? 4 : dictionaryFlag;
    const contentSizeBytes = contentSizeFlag === 0 ? (singleSegment ? 1 : 0) : 1 << contentSizeFlag;
    const remainingHeaderBytes = (singleSegment ? 0 : 1) + dictionaryBytes + contentSizeBytes;
    if (buffer.length - offset < remainingHeaderBytes) return { frames, tornStart: start };
    offset += remainingHeaderBytes;
    for (;;) {
      if (buffer.length - offset < 3) return { frames, tornStart: start };
      const blockHeader = buffer.readUIntLE(offset, 3);
      offset += 3;
      const lastBlock = (blockHeader & 1) !== 0;
      const blockType = (blockHeader >>> 1) & 3;
      const blockSize = blockHeader >>> 3;
      if (blockType === 3) throw new Error(`reserved block type at byte ${offset - 3}`);
      const payloadBytes = blockType === 1 ? 1 : blockSize;
      if (buffer.length - offset < payloadBytes) return { frames, tornStart: start };
      offset += payloadBytes;
      if (lastBlock) break;
    }
    if (checksum) {
      if (buffer.length - offset < 4) return { frames, tornStart: start };
      offset += 4;
    }
    frames.push({ start, end: offset });
  }
  return { frames };
}

function decodeLog(path) {
  const raw = readFileSync(path);
  const { frames, tornStart } = scanFrames(raw);
  if (tornStart !== undefined) throw new Error(`torn frame at byte ${tornStart}`);
  const plaintexts = frames.map((f) => zstdDecompressSync(raw.subarray(f.start, f.end)));
  const text = Buffer.concat(plaintexts).toString('utf8');
  const lines = text.split('\n');
  if (lines.at(-1) !== '') throw new Error('log does not end with a newline');
  lines.pop();
  const headerLine = lines[0];
  const header = JSON.parse(headerLine);
  if (header.type !== 'session') throw new Error('first line is not a session header');
  const events = [];
  const lineOfEvent = [];
  for (let li = 1; li < lines.length; li += 1) {
    for (const event of decodeStorageRecord(JSON.parse(lines[li]))) {
      events.push(event);
      lineOfEvent.push(li);
    }
  }
  for (const [index, event] of events.entries()) {
    if (event.seq !== index) throw new Error(`seq continuity broken at index ${index}: seq=${event.seq}`);
  }
  const firstFrameLines = zstdDecompressSync(raw.subarray(frames[0].start, frames[0].end)).toString('utf8');
  return { raw, frames, lines, headerLine, header, events, lineOfEvent, firstFramePlaintext: firstFrameLines };
}

const [, , logPath, boundaryArg, ...rest] = process.argv;
if (logPath === undefined || boundaryArg === undefined) {
  console.error('usage: node rollback.mjs <session.v4.jsonl.zstd> <boundarySeq> [--write <outPath>]');
  process.exit(2);
}
const boundary = Number(boundaryArg);
const writeIndex = rest.indexOf('--write');
const outPath = writeIndex === -1 ? undefined : rest[writeIndex + 1];

const log = decodeLog(logPath);
const last = log.events.at(-1).seq;
console.log(`file                 : ${logPath}`);
console.log(`frames               : ${log.frames.length}  firstFrameLines=${JSON.stringify(log.firstFramePlaintext.length > 60 ? log.firstFramePlaintext.slice(0, 60) + '…' : log.firstFramePlaintext)}`);
console.log(`header               : id=${log.header.id} createdAt=${log.header.createdAt} cwd=${log.header.cwd}`);
console.log(`events decoded       : ${log.events.length} (last seq ${last})`);
console.log(`lines                : ${log.lines.length}`);

const before = foldSurface(log.events);
console.log(`surface BEFORE       : nodes=${before.nodes.length} replacements=${before.replacements.length} lastNode=${before.nodes.at(-1)}`);
console.log(`  tail nodes         : ${before.nodes.slice(-6).join(', ')}`);

const keptEvents = log.events.slice(0, boundary + 1);
const droppedEvents = log.events.slice(boundary + 1);
const after = foldSurface(keptEvents);
console.log(`boundary seq         : ${boundary} -> ${keptEvents.at(-1).type} / dropped ${droppedEvents.length} events (seq ${droppedEvents[0]?.seq}..${droppedEvents.at(-1)?.seq})`);
console.log(`surface AFTER        : nodes=${after.nodes.length} replacements=${after.replacements.length} lastNode=${after.nodes.at(-1)}`);
console.log(`  tail nodes         : ${after.nodes.slice(-6).join(', ')}`);

const lastKeptLine = Math.max(...log.lineOfEvent.slice(0, boundary + 1));
const droppedLines = new Set(log.lineOfEvent.slice(boundary + 1));
for (const li of droppedLines) {
  if (li <= lastKeptLine) throw new Error(`line ${li} carries both kept and dropped events`);
}
console.log(`kept lines           : 0..${lastKeptLine} (of ${log.lines.length - 1} event lines); dropped lines ${Math.min(...droppedLines)}..${log.lines.length - 1}`);
console.log(`dropped record types : ${JSON.stringify([...droppedLines].map((li) => JSON.parse(log.lines[li]).type))}`);

if (outPath !== undefined) {
  const keptLines = log.lines.slice(1, lastKeptLine + 1);
  const chunks = [];
  let current = [];
  let currentBytes = 0;
  for (const line of keptLines) {
    const size = Buffer.byteLength(line, 'utf8') + 1;
    if (current.length > 0 && currentBytes + size > MAX_FRAME_PLAINTEXT) {
      chunks.push(current);
      current = [];
      currentBytes = 0;
    }
    current.push(line);
    currentBytes += size;
  }
  if (current.length > 0) chunks.push(current);
  const out = [zstdCompressSync(Buffer.from(`${log.headerLine}\n`, 'utf8'), CHECKSUM_OPTIONS)];
  for (const chunk of chunks) out.push(zstdCompressSync(Buffer.from(`${chunk.join('\n')}\n`, 'utf8'), CHECKSUM_OPTIONS));
  const buffer = Buffer.concat(out);
  writeFileSync(outPath, buffer);
  console.log(`wrote                : ${outPath} (${buffer.length} bytes, ${out.length} frames)`);

  const verify = decodeLog(outPath);
  if (verify.headerLine !== log.headerLine) throw new Error('verify: header changed');
  if (verify.firstFramePlaintext !== `${log.headerLine}\n`) throw new Error('verify: first frame is not exactly the header line');
  if (verify.events.length !== keptEvents.length) throw new Error('verify: event count mismatch');
  const verifyFold = foldSurface(verify.events);
  if (verifyFold.nodes.join(',') !== after.nodes.join(',')) throw new Error('verify: surface fold differs');
  console.log(`verify OK            : ${verify.frames.length} frames, ${verify.events.length} events, last seq ${verify.events.at(-1).seq}, surface nodes=${verifyFold.nodes.length}`);
}
