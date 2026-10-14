/**
 * Verify the profile-patch addition:
 *  1. structural equivalence of the overridden preset-standard plugins list with
 *     the shipped declaration — the ONLY permitted difference is the two
 *     summarization fields on the compaction-basic row,
 *  2. YAML validity plus the expected final entries of the profile patch file.
 */
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire('C:/Users/George/dsh-app/node_modules/');
const YAML = require('yaml');

const SHIPPED = 'F:/mocap_ai_doctor/.session_recover/asar_extract/presets_standard.patch.yml';
const SNIPPET = 'F:/mocap_ai_doctor/.session_recover/patch_addition.yml';
const PROFILE = process.argv[2] ?? 'C:/Users/George/.dsh/profiles/desktop/cordis.patch.yml';

/** `!!js` is a loader tag, not data; parse it back to its source text. */
const jsTag = { tag: '!!js', resolve: (value) => ({ __js: value }) };

function parse(text, label) {
  try {
    return YAML.parse(text, { customTags: [jsTag] });
  } catch (error) {
    throw new Error(`${label}: YAML parse failed: ${error.message}`);
  }
}

function findConfig(doc, label) {
  const direct = doc.find((row) => row && row.id === 'preset-standard');
  if (direct !== undefined) return direct.config;
  const inserted = doc.flatMap((row) => (Array.isArray(row?.insert) ? row.insert : []));
  const inner = inserted.find((row) => row?.id === 'preset-standard');
  if (inner === undefined) throw new Error(`${label}: no preset-standard row`);
  return inner.config;
}

/** Every row reachable in a preset plugin list, including nested group configs. */
function* rows(plugins, path = '') {
  for (const [index, row] of plugins.entries()) {
    const at = `${path}${index}:${row.id}`;
    yield [at, row];
    if (Array.isArray(row.config)) yield* rows(row.config, `${at}/`);
  }
}

const shipped = findConfig(parse(readFileSync(SHIPPED, 'utf8'), 'shipped'), 'shipped');
const override = findConfig(parse(readFileSync(SNIPPET, 'utf8'), 'snippet'), 'snippet');

if (shipped.id !== override.id || shipped.order !== override.order) {
  throw new Error(`declaration identity differs: ${JSON.stringify([shipped.id, shipped.order, override.id, override.order])}`);
}

const KEY = 'config.summarizationProvider';
const shippedRows = new Map();
for (const [at, row] of rows(shipped.plugins)) shippedRows.set(at, row);
const overrideRows = new Map();
for (const [at, row] of rows(override.plugins)) overrideRows.set(at, row);

if (shippedRows.size !== overrideRows.size) throw new Error(`row count differs: ${shippedRows.size} vs ${overrideRows.size}`);

const diffs = [];
for (const [at, row] of shippedRows) {
  const mine = overrideRows.get(at);
  if (mine === undefined) {
    diffs.push({ at, reason: 'missing in override' });
    continue;
  }
  const clean = (source) => {
    const copy = structuredClone(source);
    // group rows carry their child list in `config`; children compare on their own
    if (Array.isArray(copy.config)) delete copy.config;
    if (copy.id === 'compaction-basic' && copy.config !== undefined) {
      delete copy.config.summarizationProvider;
      delete copy.config.summarizationModel;
      if (Object.keys(copy.config).length === 0) delete copy.config;
    }
    return copy;
  };
  if (JSON.stringify(clean(row)) !== JSON.stringify(clean(mine))) {
    diffs.push({ at, reason: 'row differs beyond summarization config', shipped: clean(row), override: clean(mine) });
  }
}
if (diffs.length > 0) throw new Error(`plugin rows differ:\n${JSON.stringify(diffs, null, 1)}`);

const compactionRow = [...overrideRows.values()].find((row) => row.id === 'compaction-basic');
const cfg = compactionRow.config ?? {};
if (cfg.summarizationProvider !== 'deepseek-official' || cfg.summarizationModel !== 'deepseek-flash') {
  throw new Error(`unexpected summarization target: ${JSON.stringify(cfg)}`);
}
if (Object.keys(cfg).length !== 2) throw new Error(`compaction-basic config has extra keys: ${JSON.stringify(Object.keys(cfg))}`);
console.log(`preset-standard: ${shippedRows.size} rows identical to shipped (nested groups included); compaction-basic gains ${KEY}=${cfg.summarizationProvider}, summarizationModel=${cfg.summarizationModel}`);

const profileDoc = parse(readFileSync(PROFILE, 'utf8'), 'profile');
const ids = profileDoc.map((row) => row?.id ?? `<insert x${row?.insert?.length ?? 0}>`);
console.log(`profile patch: ${profileDoc.length} top-level entries`);
console.log(`  ${ids.join(', ')}`);
const adapter = profileDoc.find((row) => row?.id === 'llm-deepseek');
if (adapter === undefined) throw new Error('profile patch: llm-deepseek entry missing');
if (adapter.name !== '@deepseek-ai/dsh-llm-deepseek-api-key') throw new Error(`llm-deepseek name mismatch: ${adapter.name}`);
if (adapter.config?.reasoningEffort !== 'max') throw new Error(`llm-deepseek effort mismatch: ${JSON.stringify(adapter.config)}`);
console.log(`llm-deepseek: name=${adapter.name} config=${JSON.stringify(adapter.config)}`);
const presetRow = profileDoc.find((row) => row?.id === 'preset-standard');
if (presetRow === undefined) throw new Error('profile patch: preset-standard entry missing');
if (presetRow.name !== '@deepseek-ai/dsh-agent-preset') throw new Error(`preset-standard name mismatch: ${presetRow.name}`);
console.log(`preset-standard: name=${presetRow.name} plugins=${presetRow.config.plugins.length}`);
console.log('OK');
