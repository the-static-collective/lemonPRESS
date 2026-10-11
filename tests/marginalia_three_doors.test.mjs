import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile,stat,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {makeThreeDoorScore,composeThreeDoorsLocal,verifyThreeDoorsLocal}
 from '../tools/marginalia_three_doors.mjs';
const sha=s=>'sha256:'+createHash('sha256').update(s,'utf8').digest('hex');
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const time='2026-10-11T16:00:00.000Z';
function fixture(withRelation=true){
 const excerpt='The house takes attendance.';
 const unsigned={
 schema:'goatnote.lemonpress-margin/v0',posture:'PRIVATE_UNADMITTED_CANDIDATE',
 selection:{selected_at:time,method:'HUMAN_EXPLICIT_ONE_MARGIN',scope:'LOCAL_DOWNLOAD_ONLY',publication_grant:false},
 source:{note_id:'n1',version_id:'v1',title:'Odd ledger',version_sha256:'sha256:'+'a'.repeat(64),
 excerpt,excerpt_start:0,excerpt_end:excerpt.length,excerpt_sha256:sha(excerpt),version_body_disclosed:false},
 reading:{margin_id:'m1',kind:'question',text:'Whose noticing counts?',recorded_at:'2026-10-11T15:00:00.000Z'},
 relation:withRelation?{edge_id:'e1',relation_type:'echoes',first_perceived_at:'2026-10-09T14:00:00.000Z',
 recorded_current_status:'perceived',discovery_trace:'A relation became visible later',
 evidence_path:'Two bounded readings, not an external source proof',read_only:true,
 locally_admitted_means_press_admitted:false}:null,
 authority:{goatnote_margin_is_source:false,press_admission:false,house_release:false,
 signer_authenticated:false,version_bytes_included:false}
 };
 return JSON.stringify({...unsigned,checksum:sha('GOATNOTE-LEMONPRESS-MARGIN-001|'+canonical(unsigned))});
}
test('all three doors carry exact quote and margin with independent losses',()=>{
 const raw=fixture(),a=makeThreeDoorScore(raw),b=makeThreeDoorScore(raw);
 assert.deepEqual(a,b);
 assert.equal(a.score.schema,'lemonpress.marginalia-three-doors/v0');
 assert.deepEqual(a.artifacts.map(x=>x.lane),['page','voice','fragment']);
 assert.deepEqual(a.score.slots.map(x=>x.role),
  ['original_excerpt','human_margin','relation_discovery','relation_evidence_path']);
 assert.equal(a.score.boundaries.publication_authorized,undefined);
 assert.equal(a.score.boundaries.published,false);
 assert.equal(a.score.boundaries.rights_grant,false);
 assert.equal(a.score.boundaries.audio_rendered,false);
 assert.equal(a.score.boundaries.print_proof,false);
 assert.equal(a.score.boundaries.web_page,false);
 for(const aItem of a.artifacts){
  assert.match(aItem.content,/The house takes attendance/);
  assert.match(aItem.content,/Whose noticing counts/);
  assert.equal(aItem.receipt.output.sha256,sha(aItem.content));
  assert.equal(aItem.receipt.score_id,a.score.score_id);
  assert.match(aItem.receipt.stop,/HOLD/);
  assert.equal(aItem.receipt.unknown.length,5);
 }
 assert.match(a.artifacts[0].content,/NOT A PRINT PROOF/);
 assert.match(a.artifacts[1].content,/NO AUDIO GENERATED/);
 assert.match(a.artifacts[2].content,/NOT A PUBLISHED WEB PAGE/);
 assert.notEqual(a.artifacts[0].digest,a.artifacts[1].digest);
 assert.notEqual(a.artifacts[1].digest,a.artifacts[2].digest);
});
test('optional selective routing cannot duplicate doors or infer omitted edges',()=>{
 const raw=fixture(false),a=makeThreeDoorScore(raw,{doors:['fragment','page']});
 assert.deepEqual(a.score.doors.map(x=>x.lane),['page','fragment']);
 assert.equal(a.score.slots.length,2);
 assert.ok(!a.artifacts[1].content.includes('A relation became visible later'));
 for(const doors of [[],['page','page'],['manga'],['page','voice','fragment','archive']])
  assert.throws(()=>makeThreeDoorScore(raw,{doors}));
});
test('local private carrier replays exactly and refuses tampered plans, receipts and authority',async()=>{
 const root=await mkdtemp(join(tmpdir(),'lemonpress-three-doors-'));
 try{
  const out=join(root,'reading');
  const built=await composeThreeDoorsLocal(fixture(),out);
  assert.equal(built.published,false);
  assert.equal(built.authority,'NONE');
  assert.deepEqual(built.doors,['page','voice','fragment']);
  assert.deepEqual((await verifyThreeDoorsLocal(out)).verified_doors,built.doors);
  const scorePath=join(out,'score.json'),pagePath=join(out,'page.md'),receiptPath=join(out,'receipts','page.json');
  assert.equal((await stat(out)).mode&0o777,0o700);
  assert.equal((await stat(pagePath)).mode&0o777,0o600);
  await assert.rejects(composeThreeDoorsLocal(fixture(),out),/CREATE_ONLY_OUTPUT_EXISTS/);
  const originalPage=await readFile(pagePath,'utf8');
  await writeFile(pagePath,'FORGED PAGE\n');
  await assert.rejects(verifyThreeDoorsLocal(out),/PROJECTION_REPLAY_MISMATCH/);
  await writeFile(pagePath,originalPage);
  const originalReceipt=await readFile(receiptPath,'utf8');
  const forgedReceipt=JSON.parse(originalReceipt);forgedReceipt.stop='RELEASE WITHOUT REVIEW';
  await writeFile(receiptPath,JSON.stringify(forgedReceipt));
  await assert.rejects(verifyThreeDoorsLocal(out),/RECEIPT_REPLAY_MISMATCH/);
  await writeFile(receiptPath,originalReceipt);
  const originalScore=await readFile(scorePath,'utf8');
  const forgedScore=JSON.parse(originalScore);forgedScore.boundaries.published=true;
  await writeFile(scorePath,JSON.stringify(forgedScore));
  await assert.rejects(verifyThreeDoorsLocal(out),/SCORE_REPLAY_MISMATCH/);
  await writeFile(scorePath,originalScore);
  assert.equal((await verifyThreeDoorsLocal(out)).replayed,true);
 }finally{await rm(root,{recursive:true,force:true});}
});
test('refuses packet promotion, rewritten selected quote, and stale checksum',()=>{
 const raw=fixture(),p=JSON.parse(raw);
 p.authority.press_admission=true;
 assert.throws(()=>makeThreeDoorScore(JSON.stringify(p)),/ILLICIT_PRESS_AUTHORITY/);
 const altered=JSON.parse(raw);altered.source.excerpt='changed';
 assert.throws(()=>makeThreeDoorScore(JSON.stringify(altered)),/SOURCE_EXCERPT_NOT_BOUND/);
 const renamed=JSON.parse(raw);renamed.reading.text='A later rewritten margin';
 assert.throws(()=>makeThreeDoorScore(JSON.stringify(renamed)),/PACKET_CHECKSUM_MISMATCH/);
});
