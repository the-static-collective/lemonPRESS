import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {compileVinylProof,verifyProof} from '../src/vinyl-proof.mjs';
const edition=JSON.parse(readFileSync(new URL('../works/other-peoples-fire/press-000/edition.json',import.meta.url)));
const hash=x=>'sha256:'+x.repeat(64);
const room={schema:'band-runtime/room-encounter-review/v1',status:'SYNTHETIC_WITNESS_ONLY',semanticInputs:0,actualRoomWrites:0,sourceAuthenticated:false,published:false,rightsVerified:false,humanActs:0,witnessEvents:[
{type:'session.opened'},{type:'capture.recorded'},{type:'handoff.recorded',payload:{delivery:{status:'DECLARED'}}},{type:'return.recorded',payload:{relation:{status:'CLAIMED'}}},{type:'decision.recorded'}]};
const make=(e=edition,r=room)=>compileVinylProof(e,r);
test('one source-linked A1 is proof only and never a manufacturing instruction',()=>{
 const p=make().files,plan=JSON.parse(p['proof.json']);assert.equal(plan.state,'HOLD_NOT_ORDERABLE');
 assert.equal(plan.sides.A.length,1);assert.equal(plan.sides.B.length,0);
 assert.equal(plan.sides.A[0].masterSha256,null);assert.equal(plan.product.unitCost,null);
 assert.equal(plan.releaseIntent.targetConcept.tracks,12);assert.equal(plan.releaseIntent.targetConcept.creators,11);
 assert.equal(plan.safety.audioBytesPresent,false);assert.equal(plan.safety.orderPlaced,false);
 assert.ok(p['sleeve-draft.html'].includes('NOT FOR MANUFACTURE'));
 assert.equal(make().receipt.receiptId,make().receipt.receiptId);
});
test('source permission and candidate conditions are binding',()=>{
 assert.throws(()=>make({...edition,rights:{...edition.rights,physical_manufacture_approval:'GRANTED'}}),/SOURCE_RIGHTS/);
 assert.throws(()=>make({...edition,source:{...edition.source,media_bytes:'included'}}),/MEDIA_PROVENANCE/);
 assert.throws(()=>make({...edition,state:'PUBLISHED'}),/EXPERIMENT_SOURCE/);
});
test('room observation cannot become production, rights or human authorization',()=>{
 for(const p of [{published:true},{rightsVerified:true},{semanticInputs:1},{actualRoomWrites:1},{sourceAuthenticated:true}])
 assert.throws(()=>make(edition,{...room,...p}),/BAND/);
 assert.throws(()=>make(edition,{...room,witnessEvents:[...room.witnessEvents.slice(0,3),{type:'return.recorded',payload:{relation:{status:'WITNESSED'}}},room.witnessEvents[4]]}),/FALSE_DELIVERY/);
});
test('verifier refuses file omission injection and forged side plan',()=>{
 const p=make().files;assert.equal(verifyProof(p,{...p}),true);
 assert.throws(()=>verifyProof(p,{...p,extra:'x'}),/FILES_CHANGED/);
 assert.throws(()=>verifyProof(p,{...p,'proof.json':'forged'}),/TAMPER/);
});
