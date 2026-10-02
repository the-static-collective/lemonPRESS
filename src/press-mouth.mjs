import { createHash } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { basename, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HEX_64 = /^[a-f0-9]{64}$/;
const ROLE = /^[a-z0-9][a-z0-9-]{0,63}$/;

function fail(code, message) {
  const error = new Error(message);
  error.code = code;
  throw error;
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value).sort().map(key => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

export function canonicalStringify(value) {
  return JSON.stringify(canonicalize(value));
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function normalizeSha256(value, label) {
  if (typeof value !== 'string') fail('INVALID_SHA256', label + ' must be a SHA-256 string');
  const normalized = value.startsWith('sha256:') ? value.slice(7) : value;
  if (!HEX_64.test(normalized)) fail('INVALID_SHA256', label + ' must be lowercase SHA-256 hex');
  return normalized;
}

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    fail('INVALID_RECEIPT', label + ' must be an object');
  }
  return value;
}

function mediaTypeForPath(path) {
  const extension = extname(path).toLowerCase();
  if (extension === '.wav') return 'audio/wav';
  if (extension === '.mp3') return 'audio/mpeg';
  if (extension === '.flac') return 'audio/flac';
  if (extension === '.mid' || extension === '.midi') return 'audio/midi';
  if (extension === '.m4a') return 'audio/mp4';
  if (extension === '.ogg') return 'audio/ogg';
  return 'application/octet-stream';
}

function normalizeRoles(roles) {
  const input = Array.isArray(roles) ? roles : String(roles || 'music-bed').split(',');
  const normalized = [...new Set(input.map(role => String(role).trim()).filter(Boolean))].sort();
  if (normalized.length === 0) fail('INVALID_ROLE', 'at least one role is required');
  for (const role of normalized) {
    if (!ROLE.test(role)) fail('INVALID_ROLE', 'invalid role: ' + role);
  }
  return normalized;
}

function getPath(object, dottedPath) {
  return dottedPath.split('.').reduce((value, key) => {
    if (!value || typeof value !== 'object') return undefined;
    return value[key];
  }, object);
}

function verifyBodyAgainstProjection(projection, identity, label) {
  requireObject(projection, label);
  const upstreamSha = normalizeSha256(projection.sha256, label + '.sha256');
  if (upstreamSha !== identity.sha256) {
    fail('BODY_HASH_MISMATCH', label + ' SHA-256 does not match local body');
  }
  if (projection.byteLength !== undefined && projection.byteLength !== identity.byte_length) {
    fail('BODY_LENGTH_MISMATCH', label + ' byte length does not match local body');
  }
}

function adaptVaultReceipt(receipt, receiptSha256, identity) {
  requireObject(receipt, 'Vault receipt');
  if (receipt.schemaVersion !== 1) fail('UNSUPPORTED_RECEIPT', 'Vault schemaVersion must be 1');
  if (receipt.state !== 'verified') {
    fail('UPSTREAM_NOT_VERIFIED', 'Vault receipt must be in verified state');
  }
  const upstreamSha = normalizeSha256(receipt.sha256, 'Vault receipt sha256');
  if (upstreamSha !== identity.sha256) {
    fail('BODY_HASH_MISMATCH', 'Vault receipt SHA-256 does not match local body');
  }
  if (receipt.byteLength !== identity.byte_length) {
    fail('BODY_LENGTH_MISMATCH', 'Vault receipt byte length does not match local body');
  }

  return {
    origin: {
      system: 'autodiscography-vault',
      authority: 'verified-source',
      upstream_receipt_sha256: receiptSha256,
    },
    lineage: {
      schema: 'lemonpress/audio-lineage/v0',
      source_system: 'autodiscography-vault',
      upstream: {
        schemaVersion: receipt.schemaVersion,
        runId: receipt.runId ?? null,
        provider: receipt.provider ?? null,
        providerTrackId: receipt.providerTrackId ?? null,
        assetRole: receipt.assetRole ?? null,
        state: receipt.state,
        observedAt: receipt.observedAt ?? null,
        sourceRelativePath: receipt.sourceRelativePath ?? null,
        sha256: upstreamSha,
        byteLength: receipt.byteLength,
      },
    },
    projection: {
      schema: 'lemonpress/audio-projections/v0',
      kind: 'source-body',
      upstream_role: receipt.assetRole ?? 'other',
      source_sha256: upstreamSha,
    },
  };
}

function topLevelProjectionCandidates(receipt) {
  return Object.entries(receipt)
    .filter(([, value]) => value && typeof value === 'object' && !Array.isArray(value))
    .filter(([, value]) => typeof value.sha256 === 'string');
}

function choosePhonographProjection(receipt, identity, projectionPath) {
  if (projectionPath) {
    const projection = getPath(receipt, projectionPath);
    verifyBodyAgainstProjection(projection, identity, 'Phonograph projection ' + projectionPath);
    return { path: projectionPath, projection };
  }

  const matches = [];
  for (const [path, projection] of topLevelProjectionCandidates(receipt)) {
    try {
      const candidateSha = normalizeSha256(projection.sha256, 'Phonograph projection ' + path + '.sha256');
      const lengthMatches = projection.byteLength === undefined || projection.byteLength === identity.byte_length;
      if (candidateSha === identity.sha256 && lengthMatches) matches.push({ path, projection });
    } catch {
      // Invalid unrelated projection metadata is not silently selected.
    }
  }

  if (matches.length === 0) {
    fail('PROJECTION_NOT_FOUND', 'no Phonograph projection matches the local body');
  }
  if (matches.length > 1) {
    fail('AMBIGUOUS_PROJECTION', 'multiple Phonograph projections match; pass --projection path');
  }
  return matches[0];
}

function adaptPhonographReceipt(receipt, receiptSha256, identity, projectionPath) {
  requireObject(receipt, 'Phonograph receipt');
  if (receipt.schema !== 'haunted-phonograph/receipt/v1') {
    fail('UNSUPPORTED_RECEIPT', 'Phonograph receipt schema must be haunted-phonograph/receipt/v1');
  }
  if (receipt.status !== 'completed') {
    fail('UPSTREAM_NOT_COMPLETED', 'Phonograph receipt must be completed');
  }
  for (const key of ['sourceHash', 'scoreHash', 'resolvedPerformanceHash']) {
    if (typeof receipt[key] !== 'string' || receipt[key].length === 0) {
      fail('BROKEN_LINEAGE', 'Phonograph receipt missing ' + key);
    }
  }

  const selected = choosePhonographProjection(receipt, identity, projectionPath);
  const projectionSha = normalizeSha256(selected.projection.sha256, 'Phonograph projection sha256');

  return {
    origin: {
      system: 'haunted-phonograph',
      authority: 'resolved-performance-projection',
      upstream_receipt_sha256: receiptSha256,
    },
    lineage: {
      schema: 'lemonpress/audio-lineage/v0',
      source_system: 'haunted-phonograph',
      upstream: {
        sourceHash: receipt.sourceHash,
        scoreHash: receipt.scoreHash,
        resolvedPerformanceHash: receipt.resolvedPerformanceHash,
        mutation: receipt.mutation ?? null,
        retainedUncertaintyRefs: receipt.retainedUncertaintyRefs ?? [],
      },
      projection: {
        path: selected.path,
        sha256: projectionSha,
        byteLength: selected.projection.byteLength ?? identity.byte_length,
        profile: selected.projection.profile ?? null,
      },
    },
    projection: {
      schema: 'lemonpress/audio-projections/v0',
      kind: 'resolved-performance-projection',
      path: selected.path,
      resolved_performance_hash: receipt.resolvedPerformanceHash,
      sha256: projectionSha,
      profile: selected.projection.profile ?? null,
    },
  };
}

function adaptSunoPantryReceipt(receipt, receiptSha256, identity, requestedRoles) {
  requireObject(receipt, 'Suno Pantry receipt');
  if (receipt.schema !== 'lemonpress/suno-pantry-receipt/v0') {
    fail('UNSUPPORTED_RECEIPT', 'Suno Pantry receipt schema must be lemonpress/suno-pantry-receipt/v0');
  }
  if (receipt.status !== 'locally-witnessed') {
    fail('UPSTREAM_NOT_WITNESSED', 'Suno Pantry receipt must be locally-witnessed');
  }
  if (receipt.provider !== 'suno') {
    fail('INVALID_PROVIDER', 'Suno Pantry receipt provider must be suno');
  }
  requireObject(receipt.asset, 'Suno Pantry receipt asset');
  const witnessedSha = normalizeSha256(receipt.asset.sha256, 'Suno Pantry asset sha256');
  if (witnessedSha !== identity.sha256) {
    fail('BODY_HASH_MISMATCH', 'Suno Pantry receipt SHA-256 does not match local body');
  }
  if (receipt.asset.byte_length !== identity.byte_length) {
    fail('BODY_LENGTH_MISMATCH', 'Suno Pantry receipt byte length does not match local body');
  }

  const witnessedRoles = normalizeRoles(receipt.roles);
  for (const role of requestedRoles) {
    if (!witnessedRoles.includes(role)) {
      fail('ROLE_NOT_WITNESSED', 'requested role was not declared by Suno Pantry receipt: ' + role);
    }
  }

  return {
    origin: {
      system: 'suno-pantry',
      authority: 'declared-local-export',
      upstream_receipt_sha256: receiptSha256,
    },
    lineage: {
      schema: 'lemonpress/audio-lineage/v0',
      source_system: 'suno-pantry',
      upstream: {
        provider: receipt.provider,
        status: receipt.status,
        export_kind: receipt.export_kind ?? null,
        declaration_sha256: receipt.declaration_sha256 ?? null,
        provider_track_id: receipt.provider_track_id ?? null,
        parent_provider_track_id: receipt.parent_provider_track_id ?? null,
        title: receipt.title ?? null,
        roles: witnessedRoles,
        sha256: witnessedSha,
        byte_length: receipt.asset.byte_length,
      },
    },
    projection: {
      schema: 'lemonpress/audio-projections/v0',
      kind: 'declared-local-export',
      export_kind: receipt.export_kind ?? 'other',
      source_sha256: witnessedSha,
    },
  };
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

export async function ingestAudioArtifact({
  sourceSystem,
  assetPath,
  receiptPath,
  outDir,
  roles = ['music-bed'],
  projectionPath = null,
}) {
  if (!['autodiscography-vault', 'haunted-phonograph', 'suno-pantry'].includes(sourceSystem)) {
    fail('UNSUPPORTED_SOURCE_SYSTEM', 'unsupported source system: ' + sourceSystem);
  }
  if (!assetPath || !receiptPath || !outDir) {
    fail('MISSING_INPUT', 'assetPath, receiptPath, and outDir are required');
  }

  const [body, receiptBytes] = await Promise.all([
    readFile(assetPath),
    readFile(receiptPath),
  ]);

  let upstreamReceipt;
  try {
    upstreamReceipt = JSON.parse(receiptBytes.toString('utf8'));
  } catch {
    fail('INVALID_RECEIPT', 'upstream receipt is not valid JSON');
  }

  const identity = {
    sha256: sha256Hex(body),
    byte_length: body.length,
    media_type: mediaTypeForPath(assetPath),
    filename_hint: basename(assetPath),
  };
  const upstreamReceiptSha256 = sha256Hex(receiptBytes);
  const normalizedRoles = normalizeRoles(roles);

  const adapted = sourceSystem === 'autodiscography-vault'
    ? adaptVaultReceipt(upstreamReceipt, upstreamReceiptSha256, identity)
    : sourceSystem === 'haunted-phonograph'
      ? adaptPhonographReceipt(upstreamReceipt, upstreamReceiptSha256, identity, projectionPath)
      : adaptSunoPantryReceipt(upstreamReceipt, upstreamReceiptSha256, identity, normalizedRoles);

  const parcelSeed = {
    identity,
    origin: adapted.origin,
    roles: normalizedRoles,
    lineage: adapted.lineage,
  };
  const parcelId = 'lp-audio-' + sha256Hex(Buffer.from(canonicalStringify(parcelSeed))).slice(0, 20);
  const records = {
    sources: 'sources.json',
    lineage: 'lineage.json',
    projections: 'projections.json',
    receipt: 'receipt.json',
  };
  const parcel = {
    schema: 'lemonpress/audio-parcel/v0',
    parcel_id: parcelId,
    identity,
    origin: adapted.origin,
    roles: normalizedRoles,
    publication_status: 'candidate',
    body_policy: {
      embedded: false,
      resolution: 'sha256',
    },
    records,
  };
  const sources = {
    schema: 'lemonpress/audio-sources/v0',
    parcel_id: parcelId,
    body_identity: identity,
    upstream_receipt: {
      system: sourceSystem,
      sha256: upstreamReceiptSha256,
      body_copied: false,
    },
    local_body: {
      copied_into_parcel: false,
      resolve_by: 'sha256',
    },
  };
  const lineage = {
    ...adapted.lineage,
    parcel_id: parcelId,
  };
  const projections = {
    ...adapted.projection,
    parcel_id: parcelId,
  };
  const parcelSha256 = sha256Hex(Buffer.from(canonicalStringify(parcel)));
  const pressReceipt = {
    schema: 'lemonpress/press-mouth-receipt/v0',
    status: 'completed',
    parcel_id: parcelId,
    input: {
      source_system: sourceSystem,
      asset_sha256: identity.sha256,
      upstream_receipt_sha256: upstreamReceiptSha256,
    },
    transformation: [
      'VERIFY_BODY',
      'VERIFY_UPSTREAM_RECEIPT',
      'CLASSIFY_AUTHORITY',
      'BIND_RELATION',
      'DO_NOT_COPY_BODY',
    ],
    output: {
      parcel: 'parcel.json',
      parcel_sha256: parcelSha256,
    },
    residual: [
      'publication role remains candidate until an editorial admission crossing',
    ],
    loss: [
      'upstream receipt body is referenced by hash rather than copied into the parcel',
    ],
    unknown: [],
    stop: 'PRESS MOUTH 001 stops after truthful ingestion; composition and publication remain separate crossings.',
  };

  const parcelDir = join(resolve(outDir), parcelId);
  await mkdir(parcelDir, { recursive: true });
  await writeJsonAtomic(join(parcelDir, 'parcel.json'), parcel);
  await writeJsonAtomic(join(parcelDir, 'sources.json'), sources);
  await writeJsonAtomic(join(parcelDir, 'lineage.json'), lineage);
  await writeJsonAtomic(join(parcelDir, 'projections.json'), projections);
  await writeJsonAtomic(join(parcelDir, 'receipt.json'), pressReceipt);

  return Object.freeze({
    parcelDir,
    parcel,
    sources,
    lineage,
    projections,
    receipt: pressReceipt,
  });
}

export async function inspectParcel(parcelDir) {
  const root = resolve(parcelDir);
  const [parcel, lineage, projections, receipt] = await Promise.all(
    ['parcel.json', 'lineage.json', 'projections.json', 'receipt.json'].map(async file => {
      const bytes = await readFile(join(root, file), 'utf8');
      return JSON.parse(bytes);
    }),
  );

  if (parcel.schema !== 'lemonpress/audio-parcel/v0') {
    fail('INVALID_PARCEL', 'unsupported parcel schema');
  }
  if (receipt.status !== 'completed' || receipt.parcel_id !== parcel.parcel_id) {
    fail('INVALID_PARCEL', 'parcel receipt does not bind this parcel');
  }

  return Object.freeze({
    parcel_id: parcel.parcel_id,
    source_system: parcel.origin.system,
    authority: parcel.origin.authority,
    sha256: parcel.identity.sha256,
    byte_length: parcel.identity.byte_length,
    media_type: parcel.identity.media_type,
    roles: parcel.roles,
    publication_status: parcel.publication_status,
    lineage,
    projection: projections,
  });
}

function parseFlags(argv) {
  const flags = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag || !flag.startsWith('--') || value === undefined) {
      fail('INVALID_ARGUMENTS', 'arguments must be --name value pairs');
    }
    const key = flag.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    flags[key] = value;
  }
  return flags;
}

async function runCli(argv) {
  const [command, ...rest] = argv;
  if (command === 'ingest') {
    const flags = parseFlags(rest);
    const result = await ingestAudioArtifact({
      sourceSystem: flags.sourceSystem,
      assetPath: flags.asset,
      receiptPath: flags.receipt,
      outDir: flags.out,
      roles: flags.roles ?? 'music-bed',
      projectionPath: flags.projection ?? null,
    });
    process.stdout.write(JSON.stringify({
      parcelDir: result.parcelDir,
      parcel_id: result.parcel.parcel_id,
      authority: result.parcel.origin.authority,
    }, null, 2) + '\n');
    return;
  }

  if (command === 'inspect') {
    if (rest.length !== 1) fail('INVALID_ARGUMENTS', 'inspect requires one parcel directory');
    process.stdout.write(JSON.stringify(await inspectParcel(rest[0]), null, 2) + '\n');
    return;
  }

  fail('INVALID_ARGUMENTS', 'usage: mouth ingest --source-system NAME --asset FILE --receipt FILE --out DIR [--roles a,b] [--projection path] | mouth inspect PARCEL_DIR');
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  try {
    await runCli(process.argv.slice(2));
  } catch (error) {
    process.stderr.write('press-mouth refused [' + (error.code ?? 'ERROR') + ']: ' + (error.message ?? 'unknown failure') + '\n');
    process.exitCode = 1;
  }
}
