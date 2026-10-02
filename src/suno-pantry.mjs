import { createHash } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonicalStringify, ingestAudioArtifact } from './press-mouth.mjs';

const ROLE = /^[a-z0-9][a-z0-9-]{0,63}$/;
const EXPORT_KINDS = new Set(['stem', 'dramatic-reading', 'full-mix', 'ambient', 'other']);

function fail(code, message) {
  const error = new Error(message);
  error.code = code;
  throw error;
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function mediaTypeForPath(path) {
  const extension = extname(path).toLowerCase();
  if (extension === '.wav') return 'audio/wav';
  if (extension === '.mp3') return 'audio/mpeg';
  if (extension === '.flac') return 'audio/flac';
  if (extension === '.m4a') return 'audio/mp4';
  if (extension === '.ogg') return 'audio/ogg';
  fail('UNSUPPORTED_MEDIA', 'Suno Pantry accepts WAV, MP3, FLAC, M4A, or OGG audio');
}

function optionalString(value, label) {
  if (value === undefined || value === null) return null;
  if (typeof value !== 'string' || value.trim().length === 0) {
    fail('INVALID_DECLARATION', label + ' must be a non-empty string when present');
  }
  return value.trim();
}

function normalizeRoles(input) {
  if (!Array.isArray(input) || input.length === 0) {
    fail('INVALID_ROLE', 'roles must be a non-empty array');
  }
  const roles = [...new Set(input.map(role => String(role).trim()).filter(Boolean))].sort();
  for (const role of roles) {
    if (!ROLE.test(role)) fail('INVALID_ROLE', 'invalid role: ' + role);
  }
  return roles;
}

export function normalizePantryDeclaration(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    fail('INVALID_DECLARATION', 'Suno Pantry declaration must be an object');
  }
  if (input.schema !== 'lemonpress/suno-pantry-declaration/v0') {
    fail('UNSUPPORTED_DECLARATION', 'Suno Pantry declaration schema is unsupported');
  }
  if (input.provider !== 'suno') {
    fail('INVALID_PROVIDER', 'Suno Pantry declaration provider must be suno');
  }
  if (!EXPORT_KINDS.has(input.export_kind)) {
    fail('INVALID_EXPORT_KIND', 'unsupported Suno Pantry export_kind');
  }

  const roles = normalizeRoles(input.roles);
  if (input.export_kind === 'dramatic-reading'
    && !roles.includes('dramatic-reading')
    && !roles.includes('narration')) {
    fail('ROLE_MISMATCH', 'dramatic-reading exports must declare dramatic-reading or narration role');
  }

  return Object.freeze({
    schema: input.schema,
    provider: 'suno',
    export_kind: input.export_kind,
    roles,
    title: optionalString(input.title, 'title'),
    provider_track_id: optionalString(input.provider_track_id, 'provider_track_id'),
    parent_provider_track_id: optionalString(input.parent_provider_track_id, 'parent_provider_track_id'),
    exported_at: optionalString(input.exported_at, 'exported_at'),
    note: optionalString(input.note, 'note'),
  });
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

async function readJson(path, label) {
  let parsed;
  try {
    parsed = JSON.parse(await readFile(path, 'utf8'));
  } catch (error) {
    if (error instanceof SyntaxError) fail('INVALID_JSON', label + ' is not valid JSON');
    throw error;
  }
  return parsed;
}

async function admitWithDeclaration({ assetPath, declaration, outDir }) {
  const normalized = normalizePantryDeclaration(declaration);
  const body = await readFile(assetPath);
  const mediaType = mediaTypeForPath(assetPath);
  const bodySha256 = sha256Hex(body);
  const declarationSha256 = sha256Hex(Buffer.from(canonicalStringify(normalized)));

  const witness = {
    schema: 'lemonpress/suno-pantry-receipt/v0',
    status: 'locally-witnessed',
    provider: 'suno',
    export_kind: normalized.export_kind,
    roles: normalized.roles,
    declaration_sha256: declarationSha256,
    source_assertion: {
      provider_origin: 'declared-not-independently-verified',
      local_body_identity: 'verified-by-lemonpress',
    },
    asset: {
      sha256: bodySha256,
      byte_length: body.length,
      media_type: mediaType,
      filename_hint: basename(assetPath),
    },
    ...(normalized.title ? { title: normalized.title } : {}),
    ...(normalized.provider_track_id ? { provider_track_id: normalized.provider_track_id } : {}),
    ...(normalized.parent_provider_track_id ? { parent_provider_track_id: normalized.parent_provider_track_id } : {}),
    ...(normalized.exported_at ? { exported_at: normalized.exported_at } : {}),
    ...(normalized.note ? { note: normalized.note } : {}),
  };

  const witnessDir = join(resolve(outDir), 'witnesses');
  await mkdir(witnessDir, { recursive: true });
  const witnessId = sha256Hex(Buffer.from(canonicalStringify(witness))).slice(0, 24);
  const witnessPath = join(witnessDir, witnessId + '.suno-pantry.receipt.json');
  await writeJsonAtomic(witnessPath, witness);

  const ingested = await ingestAudioArtifact({
    sourceSystem: 'suno-pantry',
    assetPath,
    receiptPath: witnessPath,
    outDir: join(resolve(outDir), 'parcels'),
    roles: normalized.roles,
  });

  return Object.freeze({
    asset_path: resolve(assetPath),
    declaration: normalized,
    declaration_sha256: declarationSha256,
    witness_path: witnessPath,
    witness_sha256: sha256Hex(Buffer.from(canonicalStringify(witness) + '\n')),
    parcel_dir: ingested.parcelDir,
    parcel_id: ingested.parcel.parcel_id,
    body_sha256: bodySha256,
    authority: ingested.parcel.origin.authority,
    roles: ingested.parcel.roles,
  });
}

export async function admitPantryAsset({ assetPath, declarationPath, outDir }) {
  if (!assetPath || !declarationPath || !outDir) {
    fail('MISSING_INPUT', 'assetPath, declarationPath, and outDir are required');
  }
  const declaration = await readJson(declarationPath, 'Suno Pantry declaration');
  return admitWithDeclaration({ assetPath, declaration, outDir });
}

function resolveBatchAsset(manifestPath, item, index) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) {
    fail('INVALID_BATCH', 'batch item ' + index + ' must be an object');
  }
  if (typeof item.asset !== 'string' || item.asset.length === 0) {
    fail('INVALID_BATCH', 'batch item ' + index + ' requires asset');
  }
  if (isAbsolute(item.asset)) {
    fail('INVALID_BATCH_PATH', 'batch item asset paths must be relative to the manifest');
  }
  const manifestRoot = dirname(resolve(manifestPath));
  const assetPath = resolve(manifestRoot, item.asset);
  if (assetPath !== manifestRoot && !assetPath.startsWith(manifestRoot + '/')
    && !assetPath.startsWith(manifestRoot + '\\')) {
    fail('INVALID_BATCH_PATH', 'batch item escapes the manifest directory');
  }
  return assetPath;
}

export async function admitPantryBatch({ manifestPath, outDir }) {
  if (!manifestPath || !outDir) fail('MISSING_INPUT', 'manifestPath and outDir are required');
  const manifest = await readJson(manifestPath, 'Suno Pantry batch manifest');
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)
    || manifest.schema !== 'lemonpress/suno-pantry-batch/v0'
    || !Array.isArray(manifest.items)
    || manifest.items.length === 0) {
    fail('INVALID_BATCH', 'invalid or empty Suno Pantry batch manifest');
  }

  const normalizedItems = manifest.items.map((item, index) => ({
    assetPath: resolveBatchAsset(manifestPath, item, index),
    declaration: normalizePantryDeclaration({
      schema: 'lemonpress/suno-pantry-declaration/v0',
      provider: 'suno',
      export_kind: item.export_kind,
      roles: item.roles,
      title: item.title,
      provider_track_id: item.provider_track_id,
      parent_provider_track_id: item.parent_provider_track_id,
      exported_at: item.exported_at,
      note: item.note,
    }),
  }));

  const results = [];
  const refusals = [];
  for (let index = 0; index < normalizedItems.length; index += 1) {
    const item = normalizedItems[index];
    try {
      const admitted = await admitWithDeclaration({
        assetPath: item.assetPath,
        declaration: item.declaration,
        outDir,
      });
      results.push({
        index,
        asset: manifest.items[index].asset,
        parcel_id: admitted.parcel_id,
        parcel_dir: admitted.parcel_dir,
        body_sha256: admitted.body_sha256,
        witness_sha256: admitted.witness_sha256,
        authority: admitted.authority,
        roles: admitted.roles,
      });
    } catch (error) {
      refusals.push({
        index,
        asset: manifest.items[index].asset,
        code: error.code ?? 'ERROR',
        message: error.message ?? 'unknown failure',
      });
    }
  }

  const manifestCanonical = {
    schema: manifest.schema,
    items: manifest.items,
  };
  const batchReceipt = {
    schema: 'lemonpress/suno-pantry-batch-receipt/v0',
    status: refusals.length === 0 ? 'completed' : 'completed-with-refusals',
    manifest_sha256: sha256Hex(Buffer.from(canonicalStringify(manifestCanonical))),
    admitted_count: results.length,
    refusal_count: refusals.length,
    admitted: results,
    refusals,
    laws: [
      'DECLARED_ORIGIN != REMOTE_VERIFICATION',
      'LOCAL_BYTE_IDENTITY != PROVIDER_ATTESTATION',
      'PANTRY_ADMISSION != PUBLICATION',
      'BODY != ROLE',
    ],
  };

  const receiptPath = join(resolve(outDir), 'batch-receipt.json');
  await mkdir(resolve(outDir), { recursive: true });
  await writeJsonAtomic(receiptPath, batchReceipt);

  return Object.freeze({
    receiptPath,
    receipt: batchReceipt,
    admitted: results,
    refusals,
  });
}

function parseFlags(argv) {
  const flags = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith('--') || value === undefined) {
      fail('INVALID_ARGUMENTS', 'arguments must be --name value pairs');
    }
    flags[flag.slice(2).replace(/-([a-z])/g, (_, char) => char.toUpperCase())] = value;
  }
  return flags;
}

async function runCli(argv) {
  const [command, ...rest] = argv;
  const flags = parseFlags(rest);

  if (command === 'admit') {
    const result = await admitPantryAsset({
      assetPath: flags.asset,
      declarationPath: flags.declaration,
      outDir: flags.out,
    });
    process.stdout.write(JSON.stringify({
      parcel_id: result.parcel_id,
      parcel_dir: result.parcel_dir,
      authority: result.authority,
      roles: result.roles,
    }, null, 2) + '\n');
    return;
  }

  if (command === 'batch') {
    const result = await admitPantryBatch({
      manifestPath: flags.manifest,
      outDir: flags.out,
    });
    process.stdout.write(JSON.stringify({
      receipt: result.receiptPath,
      status: result.receipt.status,
      admitted: result.admitted.length,
      refused: result.refusals.length,
    }, null, 2) + '\n');
    if (result.refusals.length > 0) process.exitCode = 2;
    return;
  }

  fail('INVALID_ARGUMENTS', 'usage: pantry admit --asset FILE --declaration FILE --out DIR | pantry batch --manifest FILE --out DIR');
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  try {
    await runCli(process.argv.slice(2));
  } catch (error) {
    process.stderr.write('suno-pantry refused [' + (error.code ?? 'ERROR') + ']: ' + (error.message ?? 'unknown failure') + '\n');
    process.exitCode = 1;
  }
}
