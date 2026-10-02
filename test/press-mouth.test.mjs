import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ingestAudioArtifact, inspectParcel } from '../src/press-mouth.mjs';

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function fixtureRoot(name) {
  return mkdtemp(join(tmpdir(), 'lemonpress-' + name + '-'));
}

test('Vault verified bytes become a source-authority parcel without copying the body', async () => {
  const root = await fixtureRoot('vault');
  const body = Buffer.from('lemonpress vault specimen');
  const assetPath = join(root, 'source.wav');
  const receiptPath = join(root, 'vault-receipt.json');
  const outDir = join(root, 'out');
  await writeFile(assetPath, body);
  await writeFile(receiptPath, JSON.stringify({
    schemaVersion: 1,
    runId: 'run-001',
    provider: 'suno',
    providerTrackId: 'track-001',
    assetRole: 'audio_wav',
    state: 'verified',
    observedAt: '2026-10-01T00:00:00.000Z',
    sourceRelativePath: 'assets/track-001/audio_wav.wav',
    byteLength: body.length,
    sha256: sha256(body),
  }));

  const result = await ingestAudioArtifact({
    sourceSystem: 'autodiscography-vault',
    assetPath,
    receiptPath,
    outDir,
    roles: ['music-bed', 'motif-source'],
  });

  assert.equal(result.parcel.origin.authority, 'verified-source');
  assert.equal(result.parcel.identity.sha256, sha256(body));
  assert.equal(result.sources.local_body.copied_into_parcel, false);
  assert.deepEqual(result.parcel.roles, ['motif-source', 'music-bed']);
  assert.deepEqual((await readdir(result.parcelDir)).sort(), [
    'lineage.json',
    'parcel.json',
    'projections.json',
    'receipt.json',
    'sources.json',
  ]);

  const inspected = await inspectParcel(result.parcelDir);
  assert.equal(inspected.source_system, 'autodiscography-vault');
  assert.equal(inspected.publication_status, 'candidate');
});

test('Vault hash mismatch is refused before a parcel is written', async () => {
  const root = await fixtureRoot('vault-mismatch');
  const assetPath = join(root, 'source.wav');
  const receiptPath = join(root, 'vault-receipt.json');
  const body = Buffer.from('actual bytes');
  await writeFile(assetPath, body);
  await writeFile(receiptPath, JSON.stringify({
    schemaVersion: 1,
    runId: 'run-002',
    provider: 'suno',
    providerTrackId: 'track-002',
    assetRole: 'audio_wav',
    state: 'verified',
    observedAt: '2026-10-01T00:00:00.000Z',
    byteLength: body.length,
    sha256: '0'.repeat(64),
  }));

  await assert.rejects(
    ingestAudioArtifact({
      sourceSystem: 'autodiscography-vault',
      assetPath,
      receiptPath,
      outDir: join(root, 'out'),
    }),
    error => error.code === 'BODY_HASH_MISMATCH',
  );
});

test('completed Phonograph projection becomes projection authority with performance lineage', async () => {
  const root = await fixtureRoot('phonograph');
  const body = Buffer.from('MThd fake but identity-bearing midi projection');
  const assetPath = join(root, 'specimen.mid');
  const receiptPath = join(root, 'specimen.receipt.json');
  const digest = sha256(body);
  await writeFile(assetPath, body);
  await writeFile(receiptPath, JSON.stringify({
    schema: 'haunted-phonograph/receipt/v1',
    status: 'completed',
    sourceHash: 'sha256:' + '1'.repeat(64),
    observationHashes: {},
    observationAuthorities: {},
    scoreHash: 'sha256:' + '2'.repeat(64),
    mutation: {
      law: 'test-law',
      stream: 'test-stream',
      seed: 'seed',
      selectedOffset: 1
    },
    resolvedPerformanceHash: 'sha256:' + '3'.repeat(64),
    midi: {
      profile: 'smf0-ppq480/v1',
      sha256: 'sha256:' + digest,
      byteLength: body.length
    },
    retainedUncertaintyRefs: []
  }));

  const result = await ingestAudioArtifact({
    sourceSystem: 'haunted-phonograph',
    assetPath,
    receiptPath,
    outDir: join(root, 'out'),
    roles: ['mutation-bed'],
  });

  assert.equal(result.parcel.origin.authority, 'resolved-performance-projection');
  assert.equal(result.projections.path, 'midi');
  assert.equal(result.lineage.upstream.resolvedPerformanceHash, 'sha256:' + '3'.repeat(64));

  const receipt = JSON.parse(await readFile(join(result.parcelDir, 'receipt.json'), 'utf8'));
  assert.ok(receipt.transformation.includes('DO_NOT_COPY_BODY'));
});

test('Phonograph non-completed receipt is refused', async () => {
  const root = await fixtureRoot('phonograph-incomplete');
  const body = Buffer.from('projection');
  const assetPath = join(root, 'specimen.mid');
  const receiptPath = join(root, 'specimen.receipt.json');
  await writeFile(assetPath, body);
  await writeFile(receiptPath, JSON.stringify({
    schema: 'haunted-phonograph/receipt/v1',
    status: 'failed',
    sourceHash: 'source',
    scoreHash: 'score',
    resolvedPerformanceHash: 'performance',
    midi: {
      sha256: 'sha256:' + sha256(body),
      byteLength: body.length
    }
  }));

  await assert.rejects(
    ingestAudioArtifact({
      sourceSystem: 'haunted-phonograph',
      assetPath,
      receiptPath,
      outDir: join(root, 'out'),
    }),
    error => error.code === 'UPSTREAM_NOT_COMPLETED',
  );
});
