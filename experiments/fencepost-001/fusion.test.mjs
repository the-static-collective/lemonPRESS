import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdtempSync, rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {compileFusion, verifyFusion} from './fusion.mjs';
import {encodePcm16} from './fencepost.mjs';

const sine=(seconds=3, hz=220, rate=8000)=>{
  const s=new Float64Array(seconds*rate);
  for(let i=0;i<s.length;i++)s[i]=0.18*Math.sin(2*Math.PI*hz*i/rate);
  return encodePcm16(s,rate);
};
const unpack=(f,n)=>JSON.parse(f[n]);
test('tandem timing maintains groove radius with physically offset heads',()=>{
  const f=compileFusion(sine(),{mode:'tandem',headOffsetDegrees:120});
  const p=unpack(f,'fusion-plan.json'), q=unpack(f,'fusion-phase-samples.json');
  assert.equal(p.state,'HOLD_SIMULATION_ONLY');
  assert.equal(p.mode,'tandem');
  assert.equal(p.synchronization.nominalFollowLagSeconds,0.444444);
  assert.equal(p.synchronization.actualSurfaceAgeAtEmboss,'UNKNOWN_UNTIL_INSTRUMENTED');
  assert.equal(q.samples[0].grooveRadiusMm,75);
  assert.equal(q.samples[0].embossTimeSeconds,0.444444);
  assert.equal(q.samples.at(-1).embossTimeSeconds,3.444444);
  for(const e of q.samples){
    assert.equal(e.matchedRadiusMm,e.grooveRadiusMm);
    assert.ok(e.embossTimeSeconds >= e.formationTimeSeconds);
  }
  assert.deepEqual(q.commands,[]);
  assert.equal(p.physicalEvidence.recordPlayed,false);
  assert.equal(p.physicalEvidence.materialDeposited,false);
});

test('staged format models printed blank, surface conditioning, embossing separately',()=>{
  const f=compileFusion(sine(),{mode:'staged'});
  const p=unpack(f,'fusion-plan.json');
  const s=unpack(f,'fusion-phase-samples.json');
  assert.deepEqual(p.stageOrder.map(x=>x.name),[
    'form-blank','condition-and-qualify','emboss-on-same-fixture']);
  assert.equal(p.synchronization.nominalFollowLagSeconds,null);
  assert.equal(s.samples[0].embossTimeSeconds,null);
  assert.equal(p.assumptions.surfaceRoughness,'UNMEASURED');
  assert.equal(p.assumptions.thermalOutput,'DISABLED');
  assert.equal(p.conditionsToAdvance.length,6);
});

test('no physical outputs under either mode, and replay is deterministic',()=>{
  for(const mode of ['staged','tandem']){
    const a=compileFusion(sine(),{mode}), b=compileFusion(sine(),{mode});
    assert.deepEqual(a,b);
    const p=unpack(a,'fusion-plan.json');
    for(const key of ['deviceCommands','heaterCommands','depositionCommands','audioDriveCommands'])
      assert.deepEqual(p[key],[]);
    assert.equal(p.physicalEvidence.polymerWindowVerified,false);
    assert.equal(p.assumptions.actualMaterial,'NONE');
    assert.ok(a['fusion-fixture-concept.svg'].startsWith('<svg'));
    assert.equal(Object.keys(a).length,5);
  }
});

test('bad mode, bad geometry, and invalid WAV fail closed',()=>{
  assert.throws(()=>compileFusion(sine(),{mode:'power-on'}),/FUSION_HOLD_MODE/);
  assert.throws(()=>compileFusion(sine(),{headOffsetDegrees:360}),/HEAD_SEPARATION/);
  assert.throws(()=>compileFusion(sine(),{headOffsetDegrees:NaN}),/HEAD_SEPARATION/);
  assert.throws(()=>compileFusion(sine(),{geometry:{rpm:0}}),/SPEED_PITCH/);
  assert.throws(()=>compileFusion(sine(),{geometry:{rpm:100}}),/FENCEPOST_HOLD_GEOMETRY_RANGE/);
  assert.throws(()=>compileFusion(Buffer.from('not wav')),/FENCEPOST_HOLD_WAV_SIZE/);
});

test('cold verification rejects tampering and injected files',()=>{
  const dir=mkdtempSync(join(tmpdir(),'fusion-test-'));
  try{
    const f=compileFusion(sine());
    for(const [name,data] of Object.entries(f))writeFileSync(join(dir,name),data);
    assert.equal(verifyFusion(dir).physicalRecords,0);
    writeFileSync(join(dir,'fusion-fixture-concept.svg'),'<svg/>');
    assert.throws(()=>verifyFusion(dir),/TAMPER_fusion-fixture-concept.svg/);
    writeFileSync(join(dir,'fusion-fixture-concept.svg'),f['fusion-fixture-concept.svg']);
    writeFileSync(join(dir,'unapproved.gcode'),'G1 X1');
    assert.throws(()=>verifyFusion(dir),/UNEXPECTED_FILE/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});

test('CLI demo and cold verification run without hardware',()=>{
  const dir=mkdtempSync(join(tmpdir(),'fusion-cli-'));
  rmSync(dir,{recursive:true,force:true});
  try{
    const script=new URL('./fusion.mjs',import.meta.url).pathname;
    const a=JSON.parse(execFileSync(process.execPath,[script,'demo',dir,'tandem'],{encoding:'utf8'}));
    assert.equal(a.status,'COLD_REPLAY_DIGEST_VERIFIED');
    const b=JSON.parse(execFileSync(process.execPath,[script,'verify',dir],{encoding:'utf8'}));
    assert.equal(b.receiptId,a.receiptId);
    assert.throws(()=>execFileSync(process.execPath,[script,'demo',dir,'tandem'],{stdio:'pipe'}),/OUTPUT_NOT_EMPTY/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
