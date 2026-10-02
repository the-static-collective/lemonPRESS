import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ingestAudioArtifact } from '../src/press-mouth.mjs';
import { composeAudioEdition } from '../src/audio-composer.mjs';

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function root(name) {
  return mkdtemp(join(tmpdir(), 'lemonpress-composer-' + name + '-'));
}

async function makeVaultParcel(base, name, roles) {
  const body = Buffer.from('audio-body-' + name);
  const assetPath = join(base, name + '.wav');
  const receiptPath = join(base, name + '.vault.json');
  await writeFile(assetPath, body);
  await writeFile(receiptPath, JSON.stringify({
    schemaVersion: 1,
    runId: 'run-' + name,
    provider: 'suno',
    providerTrackId: 'track-' + name,
    assetRole: 'audio_wav',
    state: 'verified',
    observedAt: '2026-10-01T00:00:00.000Z',
    byteLength: body.length,
    sha256: sha256(body)
  }));
  return ingestAudioArtifact({
    sourceSystem: 'autodiscography-vault',
    assetPath,
    receiptPath,
    outDir: join(base, 'parcels'),
    roles
  });
}

test('AUDIO COMPOSER 001 resolves manuscript + parcels into a deterministic renderer-neutral timeline', async () => {
  const base = await root('happy');
  const narration = await makeVaultParcel(base, 'narration', ['narration']);
  const bed = await makeVaultParcel(base, 'bed', ['music-bed', 'motif-source']);

  const manuscriptPath = join(base, 'book.md');
  await writeFile(manuscriptPath, ['one', 'two', 'three', 'four', 'five', 'six'].join('\n'));

  const declarationPath = join(base, 'composition.json');
  const declaration = {
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'specimen-book',
    edition_id: 'mutation-jazz-001',
    profile: 'mutation-jazz',
    segments: [
      {
        id: 'opening',
        sequence: 0,
        duration_seconds: 30,
        manuscript: { start_line: 1, end_line: 3 },
        layers: [
          {
            parcel_id: narration.parcel.parcel_id,
            role: 'narration',
            gain_db: -2
          },
          {
            parcel_id: bed.parcel.parcel_id,
            role: 'music-bed',
            gain_db: -24,
            duck_under_roles: ['narration']
          }
        ],
        transition_after: { kind: 'crossfade', duration_seconds: 5 }
      },
      {
        id: 'second',
        sequence: 1,
        duration_seconds: 20,
        manuscript: { start_line: 4, end_line: 6 },
        layers: [
          {
            parcel_id: narration.parcel.parcel_id,
            role: 'narration',
            trim_start_seconds: 30
          },
          {
            parcel_id: bed.parcel.parcel_id,
            role: 'motif-source',
            start_offset_seconds: 4,
            duration_seconds: 10,
            gain_db: -30
          }
        ],
        transition_after: { kind: 'cut' }
      }
    ]
  };
  await writeFile(declarationPath, JSON.stringify(declaration));

  const first = await composeAudioEdition({
    manuscriptPath,
    declarationPath,
    parcelDirs: [narration.parcelDir, bed.parcelDir],
    outDir: join(base, 'out-a')
  });
  const second = await composeAudioEdition({
    manuscriptPath,
    declarationPath,
    parcelDirs: [bed.parcelDir, narration.parcelDir],
    outDir: join(base, 'out-b')
  });

  assert.equal(first.score.score_hash, second.score.score_hash);
  assert.equal(first.resolved.duration_seconds, 45);
  assert.equal(first.resolved.segments[1].start_seconds, 25);
  assert.equal(first.resolved.tracks.length, 4);
  assert.equal(first.resolved.renderer_contract.may_reinterpret_structure, false);
  assert.equal(first.resolved.renderer_contract.may_invent_layers, false);
  assert.equal(first.receipt.status, 'completed');
  assert.ok(first.receipt.transformation.includes('DO_NOT_RENDER'));

  const written = JSON.parse(await readFile(join(first.editionDir, 'resolved-audio-edition.json'), 'utf8'));
  assert.equal(written.score_hash, first.score.score_hash);
});

test('gap transition extends the resolved duration instead of being invented by a renderer', async () => {
  const base = await root('gap');
  const narration = await makeVaultParcel(base, 'narration', ['narration']);
  const manuscriptPath = join(base, 'book.md');
  await writeFile(manuscriptPath, 'one\ntwo');

  const declarationPath = join(base, 'composition.json');
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'gap-book',
    edition_id: 'reading-room-001',
    segments: [
      {
        id: 'a',
        sequence: 0,
        duration_seconds: 10,
        manuscript: { start_line: 1, end_line: 1 },
        layers: [{ parcel_id: narration.parcel.parcel_id, role: 'narration' }],
        transition_after: { kind: 'gap', duration_seconds: 3 }
      },
      {
        id: 'b',
        sequence: 1,
        duration_seconds: 7,
        manuscript: { start_line: 2, end_line: 2 },
        layers: [{ parcel_id: narration.parcel.parcel_id, role: 'narration' }]
      }
    ]
  }));

  const result = await composeAudioEdition({
    manuscriptPath,
    declarationPath,
    parcelDirs: [narration.parcelDir],
    outDir: join(base, 'out')
  });
  assert.equal(result.resolved.segments[1].start_seconds, 13);
  assert.equal(result.resolved.duration_seconds, 20);
});

test('composer refuses a parcel role that PRESS MOUTH never admitted', async () => {
  const base = await root('role-refusal');
  const bed = await makeVaultParcel(base, 'bed', ['music-bed']);
  const manuscriptPath = join(base, 'book.md');
  await writeFile(manuscriptPath, 'one');
  const declarationPath = join(base, 'composition.json');
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'role-book',
    edition_id: 'edition-001',
    segments: [{
      id: 'a',
      sequence: 0,
      duration_seconds: 10,
      manuscript: { start_line: 1, end_line: 1 },
      layers: [{ parcel_id: bed.parcel.parcel_id, role: 'narration' }]
    }]
  }));

  await assert.rejects(
    composeAudioEdition({
      manuscriptPath,
      declarationPath,
      parcelDirs: [bed.parcelDir],
      outDir: join(base, 'out')
    }),
    error => error.code === 'ROLE_NOT_ADMITTED'
  );
});

test('composer refuses parcel.json tampering against the PRESS MOUTH receipt', async () => {
  const base = await root('tamper');
  const parcel = await makeVaultParcel(base, 'bed', ['music-bed']);
  const parcelPath = join(parcel.parcelDir, 'parcel.json');
  const changed = JSON.parse(await readFile(parcelPath, 'utf8'));
  changed.roles.push('narration');
  await writeFile(parcelPath, JSON.stringify(changed));

  const manuscriptPath = join(base, 'book.md');
  await writeFile(manuscriptPath, 'one');
  const declarationPath = join(base, 'composition.json');
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'tamper-book',
    edition_id: 'edition-001',
    segments: [{
      id: 'a',
      sequence: 0,
      duration_seconds: 1,
      manuscript: { start_line: 1, end_line: 1 },
      layers: [{ parcel_id: changed.parcel_id, role: 'narration' }]
    }]
  }));

  await assert.rejects(
    composeAudioEdition({
      manuscriptPath,
      declarationPath,
      parcelDirs: [parcel.parcelDir],
      outDir: join(base, 'out')
    }),
    error => error.code === 'PARCEL_HASH_MISMATCH'
  );
});

test('composer refuses manuscript references beyond the bound source text', async () => {
  const base = await root('lines');
  const narration = await makeVaultParcel(base, 'narration', ['narration']);
  const manuscriptPath = join(base, 'book.md');
  await writeFile(manuscriptPath, 'one\ntwo');
  const declarationPath = join(base, 'composition.json');
  await writeFile(declarationPath, JSON.stringify({
    schema: 'lemonpress/audio-composition-declaration/v0',
    work_id: 'line-book',
    edition_id: 'edition-001',
    segments: [{
      id: 'a',
      sequence: 0,
      duration_seconds: 1,
      manuscript: { start_line: 1, end_line: 3 },
      layers: [{ parcel_id: narration.parcel.parcel_id, role: 'narration' }]
    }]
  }));

  await assert.rejects(
    composeAudioEdition({
      manuscriptPath,
      declarationPath,
      parcelDirs: [narration.parcelDir],
      outDir: join(base, 'out')
    }),
    error => error.code === 'INVALID_MANUSCRIPT_REF'
  );
});
