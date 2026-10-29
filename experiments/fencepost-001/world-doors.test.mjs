import test from 'node:test';
import assert from 'node:assert/strict';
import {writeFileSync,readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {encodePcm16} from './fencepost.mjs';
import {createDemoManifest,assemble,publicId} from './audio-key.mjs';
import {listDoors,visitDoor} from './world-doors.mjs';

const make=()=>{
  const samples=new Float64Array(48000);
  for(let i=0;i<samples.length;i++)samples[i]=Math.sin(i*2*Math.PI*220/48000)*.18;
  const master=encodePcm16(samples,48000),manifest=createDemoManifest(master);
  return {manifest,wav:assemble(master,manifest).capsuleWav};
};
test('five source-verified local doors require explicit approval and never run source code',()=>{
  const {manifest,wav}=make();
  assert.equal(listDoors(wav,manifest).routeProposals.length,5);
  for(const world of ['revival','reality2','creature-world','cannon','toaster']){
    assert.throws(()=>visitDoor(wav,manifest,world),/WORLD_DOOR_HOLD_LOCAL_OPERATOR_APPROVAL_REQUIRED/);
    const done=visitDoor(wav,manifest,world,{approval:'OPEN_LOCAL_DEMO'});
    assert.equal(done.world,world);
    assert.equal(done.sourceCapsuleId,publicId(manifest));
    assert.equal(done.executionMode,'FIXTURE_ONLY');
    assert.equal(done.externalSystemsAccessed,0);
    assert.equal(done.realWorldEffects,0);
    assert.equal(done.codeFromDiscExecuted,false);
    assert.equal(done.publisherAuthenticated,false);
    assert.equal(done.receiptId,visitDoor(wav,manifest,world,{approval:'OPEN_LOCAL_DEMO'}).receiptId);
  }
});
test('unknown worlds and uninstalled fixtures cannot cause execution',()=>{
  const {manifest,wav}=make();
  assert.throws(()=>visitDoor(wav,manifest,'admin',{approval:'OPEN_LOCAL_DEMO'}),/WORLD_DOOR_HOLD_UNKNOWN_OR_AMBIGUOUS_WORLD/);
  const modified={...manifest,doors:[{world:'revival',verb:'inspect',resourceKey:'custom-command-demo'}]};
  // different manifest ID is refused before any world interpretation.
  assert.throws(()=>visitDoor(wav,modified,'revival',{approval:'OPEN_LOCAL_DEMO'}),/AUDIO_KEY_HOLD_MANIFEST_ID_MISMATCH|WORLD_DOOR_HOLD_CAPSULE_NOT_VERIFIED|AUDIO_KEY_HOLD_SOURCE_AUDIO_MISMATCH/);
  const newMarker=assemble(encodePcm16(new Float64Array(48000),48000),
    createDemoManifest(encodePcm16(new Float64Array(48000),48000)));
  const other={...manifest,workId:'demo/other'};
  assert.throws(()=>visitDoor(wav,other,'revival',{approval:'OPEN_LOCAL_DEMO'}),/AUDIO_KEY_HOLD_MANIFEST_ID_MISMATCH/);
});
test('CLI lists proposals and executes only an explicit local fixture',()=>{
  const {manifest,wav}=make(),d=mkdtempSync(join(tmpdir(),'world-doors-'));
  try{
    const a=join(d,'song.wav'),m=join(d,'manifest.json');
    writeFileSync(a,wav);writeFileSync(m,JSON.stringify(manifest));
    const script=new URL('./world-doors.mjs',import.meta.url).pathname;
    const listed=JSON.parse(execFileSync(process.execPath,[script,'list',a,m],{encoding:'utf8'}));
    assert.equal(listed.routeProposals.length,5);
    const item=JSON.parse(execFileSync(process.execPath,[script,'visit',a,m,'creature-world','OPEN_LOCAL_DEMO'],{encoding:'utf8'}));
    assert.equal(item.preview.species,'tiny-ghost-cowboy');
    assert.equal(item.preview.realGameAccountChanged,false);
    assert.throws(()=>execFileSync(process.execPath,[script,'visit',a,m,'creature-world','yes'],{stdio:'pipe'}),/LOCAL_OPERATOR_APPROVAL_REQUIRED/);
  }finally{rmSync(d,{recursive:true,force:true});}
});
