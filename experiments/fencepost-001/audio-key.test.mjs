import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {encodePcm16} from './fencepost.mjs';
import {assemble,scanCapsule,publicId,buildBundle,verifyBundle,createDemoManifest} from './audio-key.mjs';

const RATE=48000;
function tone(){
  const s=new Float64Array(RATE*2);
  for(let i=0;i<s.length;i++)s[i]=0.14*Math.sin(2*Math.PI*220*i/RATE);
  return encodePcm16(s,RATE);
}
test('canonical manifest identity is stable under key reordering',()=>{
  const src=tone(),m=createDemoManifest(src);
  const reordered={doors:m.doors,sourcePcmSha256:m.sourcePcmSha256,rightsState:m.rightsState,workId:m.workId,schema:m.schema};
  assert.equal(publicId(m),publicId(reordered));
});
test('source PCM remains byte exact and front/back capsule resolves five held doors',()=>{
  const source=tone(),m=createDemoManifest(source);
  const {capsuleWav,id,sourceSeconds,markerDurationSeconds}=assemble(source,m);
  assert.equal(sourceSeconds,2);
  assert.ok(markerDurationSeconds>2 && markerDurationSeconds<3);
  const scan=scanCapsule(capsuleWav,{[id]:m});
  assert.equal(scan.publicId,id);
  assert.equal(scan.markersAgree,true);
  assert.equal(scan.sourcePcmVerifiedToManifest,true);
  assert.equal(scan.hasKnownManifest,true);
  assert.equal(scan.routeProposals.length,5);
  assert.deepEqual(scan.routeProposals.map(x=>x.world),['revival','reality2','creature-world','cannon','toaster']);
  for(const door of scan.routeProposals){
    assert.equal(door.decision,'HOLD_FOR_EXPLICIT_LOCAL_USER_ACTION');
    assert.equal(door.executed,false);
    assert.equal(door.receiverAuthority,'NOT_ESTABLISHED');
  }
  assert.equal(scan.acceptedActions,0);
  assert.equal(scan.automaticExecutions,0);
  assert.equal(scan.manifestSignatureStatus,'UNVERIFIED_NO_TRUST_ANCHOR');
});
test('unrecognized public id is discovery only and cannot run cross-world actions',()=>{
  const s=tone(),m=createDemoManifest(s),c=assemble(s,m);
  const scan=scanCapsule(c.capsuleWav,{});
  assert.equal(scan.hasKnownManifest,false);
  assert.equal(scan.routeProposals.length,0);
  assert.equal(scan.sourcePcmVerifiedToManifest,false);
});
test('changed master rejected even if manifest id remains the same',()=>{
  const s=tone(),m=createDemoManifest(s),f=Buffer.from(s);
  f.writeInt16LE(123,1000);
  assert.throws(()=>assemble(f,m),/AUDIO_KEY_HOLD_SOURCE_PCM_HASH/);
  const c=assemble(s,m),edited=Buffer.from(c.capsuleWav);
  const center=Math.floor(edited.length/2);
  edited.writeInt16LE(123,center%2===0?center:center-1);
  assert.throws(()=>scanCapsule(edited,{[c.id]:m}),/AUDIO_KEY_HOLD_SOURCE_AUDIO_MISMATCH/);
});
test('conflicting head/tail marker fails, rather than trusting first marker',()=>{
  const s=tone(),m=createDemoManifest(s),a=assemble(s,m);
  const m2={...m,workId:'demo/alternate-sound'};
  const b=assemble(s,m2);
  const altered=Buffer.from(a.capsuleWav);
  // Copy just B's encoded tail into A's tail.
  const markerByteLength=Math.round(a.markerDurationSeconds*RATE)*2;
  b.capsuleWav.copy(altered,altered.length-markerByteLength,b.capsuleWav.length-markerByteLength);
  assert.throws(()=>scanCapsule(altered),/AUDIO_KEY_HOLD_MARKERS_DISAGREE/);
});
test('manifest rejects code execution verbs, untrusted worlds and extra unsafe fields',()=>{
  const s=tone(),m=createDemoManifest(s);
  for(const changed of [
    {...m,doors:[{world:'revival',verb:'execute',resourceKey:'genesis-1-1-demo'}]},
    {...m,doors:[{world:'root',verb:'open',resourceKey:'genesis-1-1-demo'}]},
    {...m,doors:[{world:'revival',verb:'open',resourceKey:'../../etc/passwd'}]},
    {...m,doors:[{world:'revival',verb:'open',resourceKey:'genesis-1-1-demo',shell:'run'}]},
    {...m,rightsState:'SIGNED_AND_TRUSTED'}
  ])assert.throws(()=>publicId(changed),/AUDIO_KEY_HOLD_/);
});
test('bundles are deterministic, cold verifiable, and tamper evident',()=>{
  const s=tone(),m=createDemoManifest(s);
  const a=buildBundle(s,m),b=buildBundle(s,m);
  assert.deepEqual(a,b);
  const dir=mkdtempSync(join(tmpdir(),'audio-key-test-'));
  try{
    for(const [name,data] of Object.entries(a))writeFileSync(join(dir,name),data);
    assert.equal(verifyBundle(dir).executedCode,0);
    writeFileSync(join(dir,'manifest.json'),'{}');
    assert.throws(()=>verifyBundle(dir),/AUDIO_KEY_HOLD_TAMPER_manifest.json/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('CLI performs the demonstrable offline proof, no physical or code action',()=>{
  const dir=mkdtempSync(join(tmpdir(),'audio-key-cli-'));
  rmSync(dir,{recursive:true,force:true});
  const script=new URL('./audio-key.mjs',import.meta.url).pathname;
  try{
    const a=JSON.parse(execFileSync(process.execPath,[script,'demo',dir],{encoding:'utf8'}));
    assert.equal(a.status,'DIGITAL_AUDIO_CAPSULE_COLD_REPLAY_VERIFIED');
    assert.equal(a.proposedDoors,5);
    const b=JSON.parse(execFileSync(process.execPath,[script,'verify',dir],{encoding:'utf8'}));
    assert.equal(b.publicId,a.publicId);
    const scan=JSON.parse(execFileSync(process.execPath,[script,'scan',
      join(dir,'audio-capsule.wav'),join(dir,'manifest.json')],{encoding:'utf8'}));
    assert.equal(scan.routeProposals.length,5);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
