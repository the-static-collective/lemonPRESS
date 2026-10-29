import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const matrix = JSON.parse(readFileSync(new URL('./thermo-stylus-002.json', import.meta.url)));
test('thermo stylus proposal remains offline, unheated, and authority-limited',()=>{
  assert.equal(matrix.status, 'RESEARCH_HOLD_NO_ACTUATION');
  assert.equal(matrix.heaterArchitecture.setpointC, null);
  assert.equal(matrix.heaterArchitecture.batteryDirectToNeedle, false);
  assert.deepEqual(matrix.heaterArchitecture.electricalOutputCommands, []);
  for(const key of ['printerCommands','heaterCommands','audioAmplifierCommands']) {
    assert.deepEqual(matrix.experiment[key], []);
  }
  assert.equal(matrix.experiment.directSameGrooveRetraceAllowed, false);
  assert.equal(matrix.material.pvcFenceOrPipe, 'HOLD_LAB_MATERIAL_CHARACTERIZATION');
});
test('three separate unheated audio levels isolate gain without claiming physical cuts',()=>{
  const t = matrix.experiment.trials;
  assert.equal(t.length, 3);
  assert.deepEqual(t.map(x=>x.signalGainDbRelativeToDigitalSource),[-18,-12,-6]);
  assert.equal(new Set(t.map(x=>x.id)).size,3);
  for(const trial of t){
    assert.equal(trial.track,'SEPARATE');
    assert.equal(trial.heat,'OFF');
    assert.equal(trial.recordingExecuted,false);
  }
  assert.equal(3 * 60 / 45, 4);
  assert.equal(Number((3 * 0.3).toFixed(2)),0.9);
});
