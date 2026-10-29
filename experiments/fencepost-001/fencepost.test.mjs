import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync, writeFileSync, readFileSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {decodePcm16, encodePcm16, planWav, verifyDirectory} from './fencepost.mjs';

const sine = (sec = 2, hz = 220, rate = 8000) => {
  const x = new Float64Array(Math.round(sec * rate));
  for (let i = 0; i < x.length; i++) x[i] = 0.25 * Math.sin(2 * Math.PI * hz * i / rate);
  return encodePcm16(x, rate);
};

test('mono source generates deterministic receipts and useful offline artifacts', () => {
  const a = planWav(sine()), b = planWav(sine());
  assert.equal(a['receipt.json'], b['receipt.json']);
  assert.deepEqual(Object.keys(a).sort(), ['groove-preview.svg','head-reference.wav','plan.json','radial-axis-plan.json','receipt.json']);
  const p = JSON.parse(a['plan.json']);
  assert.equal(p.releaseState, 'HOLD_SIMULATION_ONLY');
  assert.equal(p.evidence.cutPerformed, false);
  assert.equal(p.evidence.recordPlayable, 'UNTESTED');
  assert.equal(p.seconds, 2);
  assert.equal(p.revolutions, 1.5);
  assert.equal(p.geometry.endRadiusMm, 74.55);
  assert.ok(a['groove-preview.svg'].includes('SIMULATION ONLY'));
  assert.equal(JSON.parse(a['radial-axis-plan.json']).commands.length, 0);
  assert.equal(decodePcm16(a['head-reference.wav']).samples.length, 16000);
});

test('audio sample count controls spiral duration, feed and radial clearance', () => {
  const a = JSON.parse(planWav(sine(10))['plan.json']);
  assert.equal(a.revolutions, 7.5);
  assert.equal(a.geometry.endRadiusMm, 72.75);
  assert.ok(a.geometry.minimumNominalTrackClearanceMm > 0);
  assert.ok(a.geometry.innerWavelengthAt5000HzMm < 0.1);
});

test('capacity and malformed or unsupported input fail closed', () => {
  assert.throws(() => planWav(sine(100)), /SIDE_CAPACITY/);
  assert.throws(() => planWav(sine(), {rpm: 100}), /GEOMETRY_RANGE/);
  assert.throws(() => planWav(sine(), {pitchMm: 0.02}), /GEOMETRY_RANGE/);
  assert.throws(() => planWav(Buffer.from('not a wave')), /WAV_SIZE|WAV_HEADER/);
  const floatOnly = Buffer.from(sine()); floatOnly.writeUInt16LE(3, 20);
  assert.throws(() => planWav(floatOnly), /WAV_ONLY_PCM16/);
});

test('cold receipt verification detects unauthorized mutation and extra files', () => {
  const dir = mkdtempSync(join(tmpdir(), 'fencepost-test-'));
  try {
    const files = planWav(sine());
    for (const [name, value] of Object.entries(files)) writeFileSync(join(dir, name), value);
    assert.equal(verifyDirectory(dir).physicalRecords, 0);
    writeFileSync(join(dir, 'plan.json'), 'forged');
    assert.throws(() => verifyDirectory(dir), /TAMPER_plan.json/);
    writeFileSync(join(dir, 'plan.json'), files['plan.json']);
    writeFileSync(join(dir, 'sidecar.txt'), 'not admitted');
    assert.throws(() => verifyDirectory(dir), /UNEXPECTED_FILES/);
  } finally {rmSync(dir, {recursive: true, force: true});}
});

test('public CLI runs demo and verifier without hardware drivers', () => {
  const dir = mkdtempSync(join(tmpdir(), 'fencepost-cli-'));
  rmSync(dir, {recursive: true, force: true});
  try {
    const script = new URL('./fencepost.mjs', import.meta.url).pathname;
    const first = JSON.parse(execFileSync(process.execPath, [script, 'demo', dir], {encoding:'utf8'}));
    assert.equal(first.status, 'COLD_REPLAY_DIGEST_VERIFIED');
    assert.equal(first.physicalRecords, 0);
    const replay = JSON.parse(execFileSync(process.execPath, [script, 'verify', dir], {encoding:'utf8'}));
    assert.equal(first.receiptId, replay.receiptId);
    assert.throws(() => execFileSync(process.execPath, [script, 'demo', dir]), /OUTPUT_NOT_EMPTY/);
  } finally {rmSync(dir, {recursive: true, force: true});}
});
