import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {inspect,receiveLocal,coldVerifyLocal} from '../intake/held-culture.mjs';
const sha=x=>'sha256:'+createHash('sha256').update(x).digest('hex');
function fixture(fn){
 const d=mkdtempSync(join(tmpdir(),'lp-002-'));const source=join(d,'source'),out=join(d,'out');
 mkdirSync(source);
 const comic='<!doctype html><html lang="en"><body><h1>One room</h1></body></html>\n';
 const card='# A ROOM\n\nOne room, one changed idea.\n';
 const request={topic:'One room, one changed idea.'};
 const body={
  schema:'cannon.culture-forge-receipt/v1',topic:request.topic,
  status:'SOURCE_PINNED_NATIVE_EXECUTION_LOCAL_ARTIFACT_ONLY',
  sourceSelection:'EXPLICIT_COMMIT_PINS_NOT_CANON',
  outputs:{'comic.html':sha(Buffer.from(comic)),'field-card.md':sha(Buffer.from(card))},
  sources:{webz:[{blob:'a'.repeat(40)}],gro:[{blob:'b'.repeat(40)}]},
  nativeResults:{webz:{schema:'abundent.matter-idea-craft/v1'},gro:{schema:'gro.mattercraft-field-projection/v0',discrepancy:'COUNTS_DISAGREE_HOLD'}},
  executable:{sourceReposModified:false},grants:{
   canonSelected:false,rightsAuthenticated:false,ownerIdentityAuthenticated:false,
   liveStewardApproved:false,sourceCopyrightGranted:false,reLATTEReceived:false,externalSettlement:false
  },effects:{realInventoryChange:0,fullMeasureDeeds:0,pennyIssued:0,marketTokensMinted:0,payments:0,thirdPartyMessages:0,publicRelease:false}
 };
 const receipt={...body,receiptSha256:sha(Buffer.from(JSON.stringify(body)))};
 for(const [name,c] of Object.entries({'comic.html':comic,'field-card.md':card,
  'request.json':JSON.stringify(request),'receipt.json':JSON.stringify(receipt)}))
   writeFileSync(join(source,name),c);
 try{return fn({source,out,body,receipt})}finally{rmSync(d,{recursive:true,force:true})}
}
test('native owner-local candidate copies actual bytes, never house admits',()=>fixture(({source,out})=>{
 const x=receiveLocal(source,out);
 assert.equal(x.admission,false);assert.equal(x.publication,false);
 const candidate=JSON.parse(readFileSync(join(out,'candidate.json')));
 assert.equal(candidate.decision,'HELD_FOR_EDITOR');assert.equal(candidate.workAdmission,'NONE');
 assert.equal(candidate.catalogRegistered,false);assert.equal(candidate.works.length,2);
 assert.equal(readFileSync(join(out,'comic.html'),'utf8'),readFileSync(join(source,'comic.html'),'utf8'));
 assert.equal(coldVerifyLocal(source,out).status,'INDEPENDENT_RECEIVER_COLD_VERIFIED');
 assert.throws(()=>receiveLocal(source,out),/OUTPUT_ALREADY_EXISTS/);
}));
test('receiver may REFUSE separately with no copied cultural bytes',()=>fixture(({source,out})=>{
 const x=receiveLocal(source,out,'REFUSE');assert.equal(x.disposition,'REFUSED_BY_RECEIVER');
 assert.equal(existsSync(join(out,'comic.html')),false);
 assert.equal(coldVerifyLocal(source,out,'REFUSE').verifiedFiles,2);
 assert.throws(()=>coldVerifyLocal(source,out,'HOLD'));
}));
test('detect donor byte change and receiver byte change',()=>fixture(({source,out})=>{
 receiveLocal(source,out);
 writeFileSync(join(out,'comic.html'),'imposter');
 assert.throws(()=>coldVerifyLocal(source,out),/RECEIVER_COLD_REPLAY_MISMATCH/);
 writeFileSync(join(source,'comic.html'),'imposter');
 assert.throws(()=>inspect(source),/SOURCE_FILE_CHANGED/);
}));
test('no fake rights, human deed, custody or token effect can pass',()=>fixture(({source,body})=>{
 for(const change of [
  b=>b.grants.rightsAuthenticated=true,
  b=>b.effects.pennyIssued=1,
  b=>b.effects.fullMeasureDeeds=1,
  b=>b.nativeResults.gro.discrepancy='COUNTS_AGREE',
  b=>b.effects.publicRelease=true]){
  const altered=structuredClone(body);change(altered);
  const r={...altered,receiptSha256:sha(Buffer.from(JSON.stringify(altered)))};
  writeFileSync(join(source,'receipt.json'),JSON.stringify(r));
  assert.throws(()=>inspect(source));
 }
}));
test('active HTML, forged request, and invalid choice fail',()=>fixture(({source,body})=>{
 assert.throws(()=>inspect(source,'ACCEPT'),/UNSUPPORTED_INTAKE_DISPOSITION/);
 writeFileSync(join(source,'request.json'),JSON.stringify({topic:'other'}));
 assert.throws(()=>inspect(source),/REQUEST_RECEIPT_MISMATCH/);
 writeFileSync(join(source,'request.json'),JSON.stringify({topic:body.topic}));
 const active='<!doctype html><script>alert(1)</script>';
 const changed=structuredClone(body);changed.outputs['comic.html']=sha(Buffer.from(active));
 writeFileSync(join(source,'comic.html'),active);
 writeFileSync(join(source,'receipt.json'),JSON.stringify({...changed,receiptSha256:sha(Buffer.from(JSON.stringify(changed)))}));
 assert.throws(()=>inspect(source),/ACTIVE_HTML_REFUSED/);
}));
