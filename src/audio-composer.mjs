import { createHash } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonicalStringify } from './press-mouth.mjs';

const ID = /^[a-z0-9][a-z0-9._-]{0,127}$/;
const ROLE = /^[a-z0-9][a-z0-9-]{0,63}$/;

function fail(code, message) {
  const error = new Error(message);
  error.code = code;
  throw error;
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function finiteNumber(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value)) fail('INVALID_NUMBER', label + ' must be finite');
  return value;
}

function boundedNumber(value, label, min, max) {
  const number = finiteNumber(value, label);
  if (number < min || number > max) fail('INVALID_NUMBER', label + ' out of range');
  return number;
}

function requireId(value, label) {
  if (typeof value !== 'string' || !ID.test(value)) fail('INVALID_ID', label + ' is invalid');
  return value;
}

async function readJson(path, label) {
  let value;
  try {
    value = JSON.parse(await readFile(path, 'utf8'));
  } catch (error) {
    if (error instanceof SyntaxError) fail('INVALID_JSON', label + ' is not valid JSON');
    throw error;
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('INVALID_JSON', label + ' must be an object');
  return value;
}

async function writeJsonAtomic(path, value) {
  const tempPath = path + '.partial-' + process.pid;
  await rm(tempPath, { force: true });
  try {
    await writeFile(tempPath, canonicalStringify(value) + '\n', { encoding: 'utf8', flag: 'wx' });
    await rename(tempPath, path);
  } finally {
    await rm(tempPath, { force: true }).catch(() => {});
  }
}

async function loadParcel(parcelDir) {
  const root = resolve(parcelDir);
  const [parcel, receipt] = await Promise.all([
    readJson(join(root, 'parcel.json'), 'parcel.json'),
    readJson(join(root, 'receipt.json'), 'receipt.json'),
  ]);

  if (parcel.schema !== 'lemonpress/audio-parcel/v0') fail('INVALID_PARCEL', 'unsupported audio parcel schema');
  if (receipt.schema !== 'lemonpress/press-mouth-receipt/v0' || receipt.status !== 'completed') {
    fail('INVALID_PARCEL', 'parcel requires a completed PRESS MOUTH receipt');
  }
  if (receipt.parcel_id !== parcel.parcel_id) fail('INVALID_PARCEL', 'parcel receipt ID mismatch');

  const parcelHash = sha256Hex(Buffer.from(canonicalStringify(parcel)));
  if (receipt.output?.parcel_sha256 !== parcelHash) {
    fail('PARCEL_HASH_MISMATCH', 'parcel body does not match PRESS MOUTH receipt');
  }
  if (!Array.isArray(parcel.roles) || parcel.roles.length === 0) fail('INVALID_PARCEL', 'parcel has no roles');

  return Object.freeze({
    root,
    parcel,
    receipt,
    parcelHash,
  });
}

function normalizeTransition(input, segmentId) {
  if (input === undefined || input === null) return { kind: 'cut', duration_seconds: 0 };
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    fail('INVALID_TRANSITION', segmentId + ' transition_after must be an object');
  }
  if (!['cut', 'crossfade', 'gap'].includes(input.kind)) {
    fail('INVALID_TRANSITION', segmentId + ' transition kind is unsupported');
  }
  const duration = input.kind === 'cut'
    ? 0
    : boundedNumber(input.duration_seconds, segmentId + ' transition duration', 0, 3600);
  return { kind: input.kind, duration_seconds: duration };
}

function normalizeLayer(input, segment, parcelMap, index) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    fail('INVALID_LAYER', segment.id + ' layer ' + index + ' must be an object');
  }
  const parcelId = requireId(input.parcel_id, segment.id + ' layer parcel_id');
  const role = requireId(input.role, segment.id + ' layer role');
  if (!ROLE.test(role)) fail('INVALID_ROLE', segment.id + ' layer role is invalid');

  const admitted = parcelMap.get(parcelId);
  if (!admitted) fail('UNKNOWN_PARCEL', segment.id + ' references unknown parcel ' + parcelId);
  if (!admitted.parcel.roles.includes(role)) {
    fail('ROLE_NOT_ADMITTED', parcelId + ' is not admitted for role ' + role);
  }

  const startOffset = boundedNumber(input.start_offset_seconds ?? 0, segment.id + ' layer start offset', 0, segment.duration_seconds);
  const available = segment.duration_seconds - startOffset;
  const duration = input.duration_seconds === undefined
    ? available
    : boundedNumber(input.duration_seconds, segment.id + ' layer duration', 0, available);
  const gain = boundedNumber(input.gain_db ?? 0, segment.id + ' layer gain', -96, 24);
  const trimStart = boundedNumber(input.trim_start_seconds ?? 0, segment.id + ' layer trim start', 0, 86400);

  let duckUnderRoles = [];
  if (input.duck_under_roles !== undefined) {
    if (!Array.isArray(input.duck_under_roles)) fail('INVALID_LAYER', 'duck_under_roles must be an array');
    duckUnderRoles = [...new Set(input.duck_under_roles.map((value, duckIndex) => {
      if (typeof value !== 'string' || !ROLE.test(value)) {
        fail('INVALID_ROLE', segment.id + ' duck role ' + duckIndex + ' is invalid');
      }
      return value;
    }))].sort();
  }

  return Object.freeze({
    parcel_id: parcelId,
    role,
    order: Number.isSafeInteger(input.order) ? input.order : index,
    start_offset_seconds: startOffset,
    duration_seconds: duration,
    trim_start_seconds: trimStart,
    gain_db: gain,
    duck_under_roles: duckUnderRoles,
    parcel_sha256: admitted.parcel.identity.sha256,
    parcel_manifest_sha256: admitted.parcelHash,
    inherited_authority: admitted.parcel.origin.authority,
  });
}

function normalizeDeclaration(declaration, lineCount, parcelMap) {
  if (declaration.schema !== 'lemonpress/audio-composition-declaration/v0') {
    fail('UNSUPPORTED_DECLARATION', 'composition declaration schema is unsupported');
  }
  const workId = requireId(declaration.work_id, 'work_id');
  const editionId = requireId(declaration.edition_id, 'edition_id');
  const profile = requireId(declaration.profile ?? 'reading-room', 'profile');
  if (!Array.isArray(declaration.segments) || declaration.segments.length === 0) {
    fail('INVALID_DECLARATION', 'at least one segment is required');
  }

  const seenIds = new Set();
  const seenSequences = new Set();
  const segments = declaration.segments.map((raw, index) => {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) fail('INVALID_SEGMENT', 'segment must be an object');
    const id = requireId(raw.id, 'segment id');
    if (seenIds.has(id)) fail('DUPLICATE_SEGMENT', 'duplicate segment id ' + id);
    seenIds.add(id);

    const sequence = raw.sequence;
    if (!Number.isSafeInteger(sequence) || sequence < 0) fail('INVALID_SEGMENT', id + ' sequence must be a nonnegative integer');
    if (seenSequences.has(sequence)) fail('DUPLICATE_SEQUENCE', 'duplicate segment sequence ' + sequence);
    seenSequences.add(sequence);

    const duration = boundedNumber(raw.duration_seconds, id + ' duration', 0.001, 86400);
    const manuscript = raw.manuscript;
    if (!manuscript || typeof manuscript !== 'object' || Array.isArray(manuscript)) {
      fail('INVALID_MANUSCRIPT_REF', id + ' manuscript reference is required');
    }
    if (!Number.isSafeInteger(manuscript.start_line) || !Number.isSafeInteger(manuscript.end_line)
      || manuscript.start_line < 1 || manuscript.end_line < manuscript.start_line || manuscript.end_line > lineCount) {
      fail('INVALID_MANUSCRIPT_REF', id + ' manuscript line range is invalid');
    }

    const shell = { id, sequence, duration_seconds: duration };
    if (!Array.isArray(raw.layers) || raw.layers.length === 0) fail('INVALID_SEGMENT', id + ' requires at least one layer');
    const layers = raw.layers.map((layer, layerIndex) => normalizeLayer(layer, shell, parcelMap, layerIndex))
      .sort((a, b) => a.order - b.order || a.parcel_id.localeCompare(b.parcel_id) || a.role.localeCompare(b.role));

    return Object.freeze({
      id,
      sequence,
      duration_seconds: duration,
      manuscript: {
        start_line: manuscript.start_line,
        end_line: manuscript.end_line,
      },
      layers,
      transition_after: normalizeTransition(raw.transition_after, id),
    });
  }).sort((a, b) => a.sequence - b.sequence || a.id.localeCompare(b.id));

  for (let index = 0; index < segments.length - 1; index += 1) {
    const segment = segments[index];
    const next = segments[index + 1];
    if (segment.transition_after.kind === 'crossfade'
      && segment.transition_after.duration_seconds > Math.min(segment.duration_seconds, next.duration_seconds)) {
      fail('INVALID_TRANSITION', segment.id + ' crossfade exceeds an adjacent segment duration');
    }
  }

  return Object.freeze({
    schema: declaration.schema,
    work_id: workId,
    edition_id: editionId,
    profile,
    segments,
  });
}

function resolveTimeline(score) {
  let cursor = 0;
  const segments = [];
  const tracks = [];

  for (let index = 0; index < score.segments.length; index += 1) {
    const segment = score.segments[index];
    const start = cursor;
    const end = start + segment.duration_seconds;

    const resolvedLayers = segment.layers.map(layer => {
      const layerStart = start + layer.start_offset_seconds;
      const layerEnd = layerStart + layer.duration_seconds;
      const track = {
        segment_id: segment.id,
        parcel_id: layer.parcel_id,
        role: layer.role,
        start_seconds: layerStart,
        end_seconds: layerEnd,
        duration_seconds: layer.duration_seconds,
        trim_start_seconds: layer.trim_start_seconds,
        gain_db: layer.gain_db,
        duck_under_roles: layer.duck_under_roles,
        parcel_sha256: layer.parcel_sha256,
        inherited_authority: layer.inherited_authority,
      };
      tracks.push(track);
      return track;
    });

    segments.push({
      id: segment.id,
      sequence: segment.sequence,
      manuscript: segment.manuscript,
      start_seconds: start,
      end_seconds: end,
      duration_seconds: segment.duration_seconds,
      layers: resolvedLayers,
      transition_after: segment.transition_after,
    });

    if (index < score.segments.length - 1) {
      const transition = segment.transition_after;
      if (transition.kind === 'crossfade') cursor = end - transition.duration_seconds;
      else if (transition.kind === 'gap') cursor = end + transition.duration_seconds;
      else cursor = end;
    } else {
      cursor = end;
    }
  }

  return {
    schema: 'lemonpress/resolved-audio-edition/v0',
    score_hash: score.score_hash,
    work_id: score.work_id,
    edition_id: score.edition_id,
    profile: score.profile,
    duration_seconds: cursor,
    segments,
    tracks,
    renderer_contract: {
      authority: 'projection-only',
      may_reinterpret_structure: false,
      may_invent_layers: false,
      media_resolution: 'sha256',
    },
  };
}

export async function composeAudioEdition({
  manuscriptPath,
  declarationPath,
  parcelDirs,
  outDir,
}) {
  if (!manuscriptPath || !declarationPath || !outDir) fail('MISSING_INPUT', 'manuscriptPath, declarationPath, and outDir are required');
  if (!Array.isArray(parcelDirs) || parcelDirs.length === 0) fail('MISSING_INPUT', 'at least one parcel directory is required');

  const [manuscriptBytes, declarationBytes, admittedParcels] = await Promise.all([
    readFile(manuscriptPath),
    readFile(declarationPath),
    Promise.all(parcelDirs.map(loadParcel)),
  ]);

  let rawDeclaration;
  try {
    rawDeclaration = JSON.parse(declarationBytes.toString('utf8'));
  } catch {
    fail('INVALID_JSON', 'composition declaration is not valid JSON');
  }

  const parcelMap = new Map();
  for (const admitted of admittedParcels) {
    if (parcelMap.has(admitted.parcel.parcel_id)) fail('DUPLICATE_PARCEL', 'duplicate parcel ' + admitted.parcel.parcel_id);
    parcelMap.set(admitted.parcel.parcel_id, admitted);
  }

  const manuscriptText = manuscriptBytes.toString('utf8');
  const lineCount = manuscriptText.length === 0 ? 0 : manuscriptText.split(/\r?\n/).length;
  if (lineCount === 0) fail('EMPTY_MANUSCRIPT', 'manuscript may not be empty');

  const normalized = normalizeDeclaration(rawDeclaration, lineCount, parcelMap);
  const declarationSha256 = sha256Hex(declarationBytes);
  const manuscriptSha256 = sha256Hex(manuscriptBytes);

  const scoreBody = {
    schema: 'lemonpress/audio-edition-score/v0',
    work_id: normalized.work_id,
    edition_id: normalized.edition_id,
    profile: normalized.profile,
    authority: 'composition-proposal',
    manuscript: {
      sha256: manuscriptSha256,
      byte_length: manuscriptBytes.length,
      line_count: lineCount,
    },
    declaration: {
      sha256: declarationSha256,
    },
    parcels: [...parcelMap.values()].map(admitted => ({
      parcel_id: admitted.parcel.parcel_id,
      parcel_manifest_sha256: admitted.parcelHash,
      body_sha256: admitted.parcel.identity.sha256,
      authority: admitted.parcel.origin.authority,
      roles: admitted.parcel.roles,
    })).sort((a, b) => a.parcel_id.localeCompare(b.parcel_id)),
    segments: normalized.segments,
  };
  const scoreHash = sha256Hex(Buffer.from(canonicalStringify(scoreBody)));
  const score = {
    ...scoreBody,
    score_hash: scoreHash,
  };

  const resolved = resolveTimeline(score);
  const resolvedHash = sha256Hex(Buffer.from(canonicalStringify(resolved)));
  const receipt = {
    schema: 'lemonpress/audio-composer-receipt/v0',
    status: 'completed',
    work_id: score.work_id,
    edition_id: score.edition_id,
    input: {
      manuscript_sha256: manuscriptSha256,
      declaration_sha256: declarationSha256,
      parcel_manifest_sha256s: score.parcels.map(parcel => parcel.parcel_manifest_sha256),
    },
    transformation: [
      'VERIFY_PARCELS',
      'BIND_MANUSCRIPT',
      'ADMIT_EXPLICIT_CUES',
      'RESOLVE_SEQUENCE',
      'RESOLVE_TRANSITIONS',
      'RESOLVE_MIX_DIRECTIVES',
      'DO_NOT_RENDER',
    ],
    output: {
      score: 'audio-edition-score.json',
      score_sha256: scoreHash,
      resolved: 'resolved-audio-edition.json',
      resolved_sha256: resolvedHash,
    },
    residual: [
      'media bodies remain external and SHA-addressed',
      'renderer selection remains open',
    ],
    loss: [],
    unknown: [
      'renderer-specific loudness, codec, and mastering choices',
    ],
    stop: 'AUDIO COMPOSER 001 stops at renderer-neutral resolved structure. Rendering is a later projection crossing.',
  };

  const editionDir = join(resolve(outDir), score.work_id, score.edition_id);
  await mkdir(editionDir, { recursive: true });
  await writeJsonAtomic(join(editionDir, 'audio-edition-score.json'), score);
  await writeJsonAtomic(join(editionDir, 'resolved-audio-edition.json'), resolved);
  await writeJsonAtomic(join(editionDir, 'receipt.json'), receipt);

  return Object.freeze({
    editionDir,
    score,
    resolved,
    receipt,
  });
}

function parseCli(argv) {
  const flags = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith('--') || value === undefined) fail('INVALID_ARGUMENTS', 'arguments must be --name value pairs');
    flags[flag.slice(2).replace(/-([a-z])/g, (_, char) => char.toUpperCase())] = value;
  }
  return flags;
}

async function runCli(argv) {
  const [command, ...rest] = argv;
  if (command !== 'compose') {
    fail('INVALID_ARGUMENTS', 'usage: audio compose --manuscript FILE --declaration FILE --parcels DIR,DIR --out DIR');
  }
  const flags = parseCli(rest);
  const result = await composeAudioEdition({
    manuscriptPath: flags.manuscript,
    declarationPath: flags.declaration,
    parcelDirs: String(flags.parcels ?? '').split(',').filter(Boolean),
    outDir: flags.out,
  });
  process.stdout.write(JSON.stringify({
    editionDir: result.editionDir,
    score_hash: result.score.score_hash,
    duration_seconds: result.resolved.duration_seconds,
    tracks: result.resolved.tracks.length,
  }, null, 2) + '\n');
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  try {
    await runCli(process.argv.slice(2));
  } catch (error) {
    process.stderr.write('audio-composer refused [' + (error.code ?? 'ERROR') + ']: ' + (error.message ?? 'unknown failure') + '\n');
    process.exitCode = 1;
  }
}
