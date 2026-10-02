import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { admitPantryAsset, admitPantryBatch, normalizePantryDeclaration } from '../src/suno-pantry.mjs';
import { composeAudioEdition } from '../src/audio-composer.mjs';

async function root(name) {
  return mkdtemp(join(tmpdir(), 'lemonpress-pantry-' + name + '-'));
}

test('single dramatic reading becomes a declared-local-export parcel usable by Composer', async () => {
  const base = await root('reading');
  const assetPath = join(base, 'chapter-01.wav');
  const declarationPath = join(base, 'chapter-01.json');
  await writeFile(assetPath, Buffer.from('dramatic-reading-bytes'));
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/suno-pantry-declaration/v0',
    provider: 'suno',
    export_kind: 'dramatic-reading',
    roles: ['narration', 'dramatic-reading'],
    title: 'Chapter One reading',
    provider_track_id: 'declared-provider-id'
  }));

  const admitted = await admitPantryAsset({
    assetPath,
    declarationPath,
    outDir: join(base, 'pantry')
  });

  assert.equal(admitted.authority, 'declared-local-export');
  assert.deepEqual(admitted.roles, ['dramatic-reading', 'narration']);

  const parcel = JSON.parse(await readFile(join(admitted.parcel_dir, 'parcel.json'), 'utf8'));
  const lineage = JSON.parse(await readFile(join(admitted.parcel_dir, 'lineage.json'), 'utf8'));
  const sources = JSON.parse(await readFile(join(admitted.parcel_dir, 'sources.json'), 'utf8'));
  assert.equal(parcel.origin.system, 'suno-pantry');
  assert.equal(parcel.origin.authority, 'declared-local-export');
  assert.equal(lineage.upstream.export_kind, 'dramatic-reading');
  assert.equal(lineage.upstream.provider_track_id, 'declared-provider-id');
  assert.equal(sources.local_body.copied_into_parcel, false);

  const manuscriptPath = join(base, 'book.md');
  const compositionPath = join(base, 'composition.json');
  await writeFile(manuscriptPath, 'Chapter One\nA line of prose.');
  await writeFile(compositionPath, JSON.stringify({
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'pantry-book',
    edition_id: 'dramatic-001',
    segments: [{
      id: 'chapter-one',
      sequence: 0,
      duration_seconds: 12,
      manuscript: { start_line: 1, end_line: 2 },
      layers: [{
        parcel_id: admitted.parcel_id,
        role: 'narration',
        gain_db: -2
      }]
    }]
  }));

  const composed = await composeAudioEdition({
    manuscriptPath,
    declarationPath: compositionPath,
    parcelDirs: [admitted.parcel_dir],
    outDir: join(base, 'edition')
  });

  assert.equal(composed.resolved.tracks[0].inherited_authority, 'declared-local-export');
  assert.equal(composed.resolved.tracks[0].role, 'narration');
});

test('dramatic-reading export refuses a declaration without a reading role', () => {
  assert.throws(
    () => normalizePantryDeclaration({
      schema: 'lemonpress/suno-pantry-declaration/v0',
      provider: 'suno',
      export_kind: 'dramatic-reading',
      roles: ['music-bed']
    }),
    error => error.code === 'ROLE_MISMATCH'
  );
});

test('batch manifest admits many stems and records individual refusals without losing successes', async () => {
  const base = await root('batch');
  const assets = join(base, 'assets');
  await mkdir(assets);
  await writeFile(join(assets, 'drums.wav'), Buffer.from('drums'));
  await writeFile(join(assets, 'jazz.wav'), Buffer.from('smooth-jazz'));
  await writeFile(join(assets, 'ghost.ogg'), Buffer.from('ghost'));

  const manifestPath = join(base, 'pantry.json');
  await writeFile(manifestPath, JSON.stringify({
    schema: 'lemonpress/suno-pantry-batch/v0',
    items: [
      {
        asset: 'assets/drums.wav',
        export_kind: 'stem',
        roles: ['rhythm'],
        title: 'Hand percussion'
      },
      {
        asset: 'assets/jazz.wav',
        export_kind: 'stem',
        roles: ['music-bed', 'motif-source'],
        title: 'Mutation jazz'
      },
      {
        asset: 'assets/ghost.ogg',
        export_kind: 'ambient',
        roles: ['atmosphere', 'ghost']
      },
      {
        asset: 'assets/missing.wav',
        export_kind: 'stem',
        roles: ['rhythm']
      }
    ]
  }));

  const result = await admitPantryBatch({
    manifestPath,
    outDir: join(base, 'out')
  });

  assert.equal(result.receipt.status, 'completed-with-refusals');
  assert.equal(result.receipt.admitted_count, 3);
  assert.equal(result.receipt.refusal_count, 1);
  assert.equal(result.admitted.length, 3);
  assert.equal(result.refusals[0].asset, 'assets/missing.wav');

  const parcelRoot = join(base, 'out', 'parcels');
  const parcels = await readdir(parcelRoot);
  assert.equal(parcels.length, 3);

  const batchReceipt = JSON.parse(await readFile(result.receiptPath, 'utf8'));
  assert.ok(batchReceipt.laws.includes('DECLARED_ORIGIN != REMOTE_VERIFICATION'));
});

test('batch manifest refuses path escape before admitting anything', async () => {
  const base = await root('escape');
  const manifestPath = join(base, 'pantry.json');
  await writeFile(manifestPath, JSON.stringify({
    schema: 'lemonpress/suno-pantry-batch/v0',
    items: [{
      asset: '../outside.wav',
      export_kind: 'stem',
      roles: ['music-bed']
    }]
  }));

  await assert.rejects(
    admitPantryBatch({ manifestPath, outDir: join(base, 'out') }),
    error => error.code === 'INVALID_BATCH_PATH'
  );
});

test('unsupported media is refused instead of becoming an opaque audio parcel', async () => {
  const base = await root('media');
  const assetPath = join(base, 'notes.txt');
  const declarationPath = join(base, 'decl.json');
  await writeFile(assetPath, 'not audio');
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/suno-pantry-declaration/v0',
    provider: 'suno',
    export_kind: 'other',
    roles: ['ghost']
  }));

  await assert.rejects(
    admitPantryAsset({ assetPath, declarationPath, outDir: join(base, 'out') }),
    error => error.code === 'UNSUPPORTED_MEDIA'
  );
});
