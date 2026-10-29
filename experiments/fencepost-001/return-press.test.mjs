import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {appendEvent,replay,render,demoJournal,compile,verify} from './return-press.mjs';

const j=()=>demoJournal();
test('synthetic history has an append-only hash chain; no silent overwrite',()=>{
  const a=j(),first=replay(a,4),last=replay(a);
  assert.equal(a.length,11);
  assert.equal(first.accepted.length,1);
  assert.equal(last.accepted.length,2);
  assert.equal(last.refusals,1);
  assert.equal(first.listenReports,undefined);
  assert.equal(last.listens,2);
  assert.equal(last.visits,2);
  assert.deepEqual(last.accepted.map(x=>x.id),['glass-a','echo-a']);
  const forged=structuredClone(a);forged[1].payload.motif='sub';
  assert.throws(()=>replay(forged),/RETURN_PRESS_HOLD_CHAIN/);
  const malformed=[...a];malformed[1]={...malformed[1],previous:'arbitrary'};
  assert.throws(()=>replay(malformed),/RETURN_PRESS_HOLD_CHAIN/);
});
test('consented listening changes history but not a musical stem',()=>{
  const short=j().slice(0,4);
  const original=replay(short);
  const listen=appendEvent(short,{type:'listen',actor:'listener-c',
    payload:{optIn:true,session:'extra-play'}});
  assert.equal(replay(listen).listens,original.listens+1);
  assert.ok(render(replay(short)).equals(render(replay(listen))));
});
test('rights and separate curator review are required to affect sound',()=>{
  let events=[];
  events=appendEvent(events,{type:'propose',actor:'composer-a',
    payload:{id:'p-a',motif:'bells',license:'DEMO_REMIX_ONLY',authorConsent:true}});
  events=appendEvent(events,{type:'accept',actor:'composer-a',
    payload:{id:'p-a',scope:'DEMO_REMIX_ONLY',review:'SYNTHETIC_REVIEW'}});
  assert.throws(()=>replay(events),/RETURN_PRESS_HOLD_INVALID_ACCEPT/);
  const other=appendEvent(events.slice(0,1),{type:'propose',actor:'composer-b',
    payload:{id:'p-b',motif:'echo',license:'ALL_RIGHTS',authorConsent:true}});
  assert.throws(()=>replay(other),/RETURN_PRESS_HOLD_PROPOSAL_RIGHTS/);
});
test('author withdrawal removes only future use of their submitted motif',()=>{
  const a=j(),before=replay(a,6),after=replay(a,8);
  assert.deepEqual(before.accepted.map(x=>x.id),['glass-a','sub-a']);
  assert.deepEqual(after.accepted.map(x=>x.id),['glass-a']);
  assert.equal(after.refusals,1);
  assert.notEqual(before.cutHash,after.cutHash);
  assert.ok(!render(before).equals(render(after)));
});
test('historical cuts produce new WAVs, new audio key, immutable original',()=>{
  const a=compile(j()),b=compile(j());
  assert.deepEqual(a,b);
  const source=a['synthetic-source.wav'],early=a['remix-early.wav'],late=a['remix-late.wav'];
  assert.ok(!source.equals(early));
  assert.ok(!early.equals(late));
  assert.ok(!source.equals(late));
  const l=JSON.parse(a['lineage.json']);
  assert.equal(l.status,'DRAFT_NEVER_PRESSED');
  assert.equal(l.early.cut,4);assert.equal(l.late.cut,11);
  assert.equal(l.early.motifs.length,1);assert.equal(l.late.motifs.length,2);
  assert.equal(l.boundaries.physicalRecords,0);
  assert.equal(l.boundaries.publicReleaseAuthorized,false);
  assert.equal(l.proposedDoors.hauntedToaster,'VISUALSCORE_NOT_RENDERED');
  assert.ok(a['center-label-draft.svg'].includes('NOT FOR MANUFACTURE'));
});
test('cut validation refuses lack of derivative and empty approval',()=>{
  assert.throws(()=>compile(j(),{earlyCut:5,lateCut:5}),/RETURN_PRESS_HOLD_CUT_ORDER/);
  assert.throws(()=>compile(j(),{earlyCut:1,lateCut:4}),/RETURN_PRESS_HOLD_MOTIF_REQUIRED/);
  assert.throws(()=>compile(j(),{earlyCut:4,lateCut:5}),/RETURN_PRESS_HOLD_NOT_A_NEW_REMIX/);
});
test('CLI generates an actual musical demo, verifies receipts and catches tamper',()=>{
  const dir=mkdtempSync(join(tmpdir(),'return-press-'));
  rmSync(dir,{recursive:true,force:true});
  const script=new URL('./return-press.mjs',import.meta.url).pathname;
  try{
    const first=JSON.parse(execFileSync(process.execPath,[script,'demo',dir],{encoding:'utf8',maxBuffer:1024*1024}));
    assert.equal(first.status,'RETURN_PRESS_COLD_REPLAY_VERIFIED');
    assert.equal(first.physicalRecords,0);
    const later=JSON.parse(execFileSync(process.execPath,[script,'verify',dir],{encoding:'utf8'}));
    assert.equal(first.lateAudioKey,later.lateAudioKey);
    assert.equal(verify(dir).lateCut,11);
    const p=join(dir,'lineage.json'),old=readFileSync(p);
    writeFileSync(p,'{}');
    assert.throws(()=>verify(dir),/RETURN_PRESS_HOLD_TAMPER_lineage.json/);
    writeFileSync(p,old);
    assert.throws(()=>execFileSync(process.execPath,[script,'demo',dir],{stdio:'pipe'}),/OUTPUT_EXISTS/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
