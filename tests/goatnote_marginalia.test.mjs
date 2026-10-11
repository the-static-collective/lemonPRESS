import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,stat,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {inspectSelectedMargin,composeReadingCandidate,composeLocal}
 from '../tools/goatnote_marginalia.mjs';
const sha=s=>'sha256:'+createHash('sha256').update(s,'utf8').digest('hex');
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const time='2026-10-11T15:30:00.000Z',excerpt='The house takes attendance.',text='A human wonders what changed.';
const unsigned={
 schema:'goatnote.lemonpress-margin/v0',posture:'PRIVATE_UNADMITTED_CANDIDATE',
 selection:{selected_at:time,method:'HUMAN_EXPLICIT_ONE_MARGIN',
  scope:'LOCAL_DOWNLOAD_ONLY',publication_grant:false},
 source:{note_id:'note-1',version_id:'v0',version_sha256:'sha256:'+'a'.repeat(64),
  title:'A Particular',excerpt,excerpt_start:6,excerpt_end:6+excerpt.length,
  excerpt_sha256:sha(excerpt),version_body_disclosed:false},
 reading:{margin_id:'margin-1',kind:'question',text,recorded_at:'2026-10-11T14:30:00.000Z'},
 relation:{edge_id:'edge-1',relation_type:'echoes',
  first_perceived_at:'2026-10-10T10:00:00.000Z',recorded_current_status:'admitted',
  discovery_trace:'New relationship discovered on October 10.',
  evidence_path:'Two saved versions, local declaration only.',read_only:true,
  locally_admitted_means_press_admitted:false},
 authority:{goatnote_margin_is_source:false,press_admission:false,
  house_release:false,signer_authenticated:false,version_bytes_included:false}
};
const seal=obj=>({...obj,checksum:sha('GOATNOTE-LEMONPRESS-MARGIN-001|'+canonical(obj))});
const packet=seal(unsigned),raw=JSON.stringify(packet);
test('private quote is independently verified; omitted original is NOT',()=>{
 const i=inspectSelectedMargin(raw);
 assert.equal(i.verification.excerpt_checksum,'INDEPENDENTLY_MATCHED');
 assert.equal(i.verification.source_version_sha256,'DECLARED_NOT_REVERIFIED_NO_BODY');
 assert.equal(i.verification.source_authority,'NOT_VERIFIED');
 const p=composeReadingCandidate(i);
 assert.equal(p.candidate.state,'PRIVATE_CANDIDATE');
 assert.equal(p.candidate.editorial_selected,false);
 assert.equal(p.candidate.publication_authorized,false);
 assert.equal(p.candidate.rights_granted,false);
 assert.equal(p.candidate.source.original_version_verified,false);
 assert.equal(p.candidate.chronology.relation_first_perceived_at,unsigned.relation.first_perceived_at);
 assert.equal(p.candidate.chronology.margin_recorded_at,unsigned.reading.recorded_at);
 assert.match(p.manuscript,/A later margin/);
 assert.match(p.manuscript,/Human relation first perceived/);
 assert.match(p.manuscript,/NOT a source-event timestamp/);
 assert.ok(!p.manuscript.includes('SOURCE_FULL_PRIVATE'));
});
test('create-only private candidate carries a deterministic editable manuscript',async()=>{
 const base=await mkdtemp(join(tmpdir(),'lp-margin-'));
 try{
  const out=join(base,'selected-reading');
  const created=await composeLocal(raw,out);
  assert.equal(created.state,'PRIVATE_CANDIDATE');
  const manuscript=await readFile(join(out,'candidate.md'),'utf8');
  const metadata=JSON.parse(await readFile(join(out,'candidate.json'),'utf8'));
  assert.equal(metadata.manuscript_sha256,sha(manuscript));
  assert.equal(metadata.id,created.id);
  assert.equal(metadata.work_admitted,false);
  assert.equal(metadata.edition_admitted,false);
  assert.equal(metadata.rights_granted,false);
  assert.equal((await stat(join(out,'candidate.md'))).mode&0o777,0o600);
  await assert.rejects(composeLocal(raw,out),/CREATE_ONLY_OUTPUT_EXISTS/);
  assert.equal(await readFile(join(out,'candidate.md'),'utf8'),manuscript);
 }finally{await rm(base,{recursive:true,force:true});}
});
test('broken hashes and claims refuse even if checksum is recomputed',()=>{
 assert.throws(()=>inspectSelectedMargin(JSON.stringify({...packet,source:{...packet.source,excerpt:'altered'}})),/SOURCE_EXCERPT_NOT_BOUND|PACKET_CHECKSUM_MISMATCH/);
 const modified=seal({...unsigned,source:{...unsigned.source,excerpt:'altered!'}});
 assert.throws(()=>inspectSelectedMargin(JSON.stringify(modified)),/SOURCE_EXCERPT_NOT_BOUND/);
 for(const change of [
  {selection:{...unsigned.selection,publication_grant:true}},
  {authority:{...unsigned.authority,house_release:true}},
  {authority:{...unsigned.authority,signer_authenticated:true}},
  {source:{...unsigned.source,version_body_disclosed:true}},
  {relation:{...unsigned.relation,locally_admitted_means_press_admitted:true}}
 ]){
  const clone=seal({...unsigned,...change});
  assert.throws(()=>inspectSelectedMargin(JSON.stringify(clone)));
 }
});
test('no edge opt-in carries no relation and does not imply adjacency',()=>{
 const p=seal({...unsigned,relation:null});
 const v=composeReadingCandidate(inspectSelectedMargin(JSON.stringify(p)));
 assert.match(v.manuscript,/No GOATedge relation was selected/);
 assert.equal(v.candidate.chronology.relation_first_perceived_at,null);
});
test('untrusted Markdown is rendered only in a content fence',()=>{
 const nasty='Untrusted title <script>!';
 const img='![image](https://private.example/leak) and ' +String.fromCharCode(96).repeat(8);
 const p=seal({...unsigned,source:{...unsigned.source,title:nasty},
  reading:{...unsigned.reading,text:img}});
 const v=composeReadingCandidate(inspectSelectedMargin(JSON.stringify(p)));
 assert.match(v.manuscript,/Untrusted title\s+script/);
 assert.ok(v.manuscript.includes(img));
 assert.ok(v.manuscript.includes(String.fromCharCode(96).repeat(9)+'text'));
});
