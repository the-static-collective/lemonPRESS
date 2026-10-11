/* Actual GOATnote 004 exporter → LemonPRESS 001 intake → THREE DOORS 002 replay.
 * This test imports the pinned public GOATnote exporter code from a separate
 * checkout. No manually re-implemented serializer and no private user records.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {makePressMarginCarrier} from '../goatnote-source/lemonpress-margin.mjs';
import {inspectSelectedMargin,composeReadingCandidate} from '../tools/goatnote_marginalia.mjs';
import {makeThreeDoorScore,composeThreeDoorsLocal,verifyThreeDoorsLocal} from '../tools/marginalia_three_doors.mjs';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const time='2026-10-11T17:00:00.000Z';
const quote='We meet where the old sign leans';
const original='Before it begins.\n'+quote+'\nAfter it changes.';
const anchorStart=original.indexOf(quote);
const db={schema:1,notes:[
 {id:'synthetic-source',title:'A House Takes Attendance',
  draft:'later revised draft, never to send',versions:[
   {id:'v0',text:original,createdAt:'2026-10-01T10:00:00.000Z'},
   {id:'v1',text:'This is a later version only.',createdAt:time}
  ],margins:[{id:'margin-1',kind:'question',versionId:'v0',
   createdAt:time,anchor:{start:anchorStart,end:anchorStart+quote.length,quote},
   text:'Who was invited in?'}],
  returnThreads:[{id:'not-disclosed',sourceVersionId:'v0',
   entries:[{id:'secret',text:'A private return thread must not escape'}]}]},
 {id:'private',title:'Not a selected book',draft:'PRIVATE_BACKSTORY',
  versions:[{id:'private-v0',text:'PRIVATE SOURCE FULL TEXT'}],margins:[]}
],edges:[{
 id:'relation-1',type:'echoes',status:'perceived',firstPerceivedAt:'2026-10-08T09:00:00.000Z',
 discoveryTrace:'A reader noticed a textual echo later than either source',
 evidencePath:'A bounded pairing, no proof of causation',
 from:{noteId:'synthetic-source',versionId:'v0',anchor:null},
 to:{noteId:'private',versionId:'private-v0',anchor:null}
}],walks:[],rooms:[]};

test('same packet from REAL GOATnote exporter is independently accepted by LemonPRESS and scored',async()=>{
 const packet=await makePressMarginCarrier(db,{
  noteId:'synthetic-source',marginId:'margin-1',edgeId:'relation-1',selectedAt:time
 });
 const raw=JSON.stringify(packet);
 for(const leak of ['PRIVATE_BACKSTORY','PRIVATE SOURCE FULL TEXT','A private return thread','later revised draft','Before it begins.','After it changes.'])
  assert.ok(!raw.includes(leak),'Undisclosed source escaped: '+leak);
 const verified=inspectSelectedMargin(raw);
 assert.equal(verified.verification.excerpt_checksum,'INDEPENDENTLY_MATCHED');
 assert.equal(verified.verification.source_version_sha256,'DECLARED_NOT_REVERIFIED_NO_BODY');
 const candidate=composeReadingCandidate(verified);
 assert.equal(candidate.candidate.state,'PRIVATE_CANDIDATE');
 const composed=makeThreeDoorScore(raw);
 assert.deepEqual(composed.score.slots.map(x=>x.role),
 ['original_excerpt','human_margin','relation_discovery','relation_evidence_path']);
 assert.equal(composed.score.boundaries.published,false);
 const root=await mkdtemp(join(tmpdir(),'cross-repo-press-'));
 try{
  const out=join(root,'private-score');
  await composeThreeDoorsLocal(raw,out);
  const replay=await verifyThreeDoorsLocal(out);
  assert.equal(replay.replayed,true);
  assert.equal(replay.original_source_verified,false);
  assert.deepEqual(replay.verified_doors,['page','voice','fragment']);
  const score=JSON.parse(await readFile(join(out,'score.json'),'utf8'));
  assert.equal(score.base_candidate_id,candidate.candidate.id);
  assert.equal(score.packet_checksum,packet.checksum);
 }finally{await rm(root,{recursive:true,force:true});}
});
