import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {compileScreeningProgram,verifyScreeningProgram} from "../src/screening-program.mjs";
const sha=x=>createHash("sha256").update(x).digest("hex");
const ret=(round,route,d)=>({schema:"jarvis.production-return/v1",round,route,
 parentRoundSha256:"c".repeat(64),artifactSha256:d.repeat(64),
 status:"SOURCE_NATIVE_VERIFIED",published:false,rightsGranted:false,realWorldActions:0});
const input={schema:"jarvis.screening-source/v1",projectId:"GENESIS-RETURN-001",
 sourceRoute:"CHECKPOINT_STILL",finalRoute:"MOVING_EXCERPT",
 media:{originalScene:{name:"original-playdeck-excerpt.mp4",sha256:"a".repeat(64)},
 finishedScene:{name:"original-toaster-digested-playdeck.mp4",sha256:"b".repeat(64)}},
 returns:{checkpoint:ret(0,"CHECKPOINT_STILL","d"),moving:ret(1,"MOVING_EXCERPT","e")},
 authority:"REVIEW_ONLY",publishingAllowed:false};
test("original lemonPRESS produces draft and true revised final from source-verified media",()=>{
 const draft=compileScreeningProgram(input);
 const review={schema:"jarvis.screening-editorial-return/v1",
  decision:"REVISE_WITH_VERIFIED_ORIGIN_AND_OUTPUT",
  sourceSha256:sha(JSON.stringify(input,null,2)+"\n"),
  draftReceiptSha256:draft.receipt.receiptSha256,
  mediaHashesVerified:true,publishingAllowed:false};
 const final=compileScreeningProgram(input,{version:"final",review});
 assert.equal(draft.receipt.version,"draft");
 assert.equal(final.receipt.version,"final");
 assert.equal(final.receipt.previousDraftSha256,draft.receipt.receiptSha256);
 assert.notEqual(draft.receipt.receiptSha256,final.receipt.receiptSha256);
 assert.ok(final.files["program.html"].includes('<video controls'));
 assert.ok(final.files["poster.svg"].includes('GENESIS'));
 assert.equal(final.receipt.published,false);
 assert.equal(final.receipt.mediaCopied,false);
 assert.ok(verifyScreeningProgram(final.files,structuredClone(final.files)));
 const tamper={...final.files,"program.html":final.files["program.html"]+"FAKE"};
 assert.throws(()=>verifyScreeningProgram(final.files,tamper),/TAMPER/);
});
test("cannot skip source receipts, editorial feedback or rights boundary",()=>{
 const draft=compileScreeningProgram(input);
 assert.throws(()=>compileScreeningProgram(input,{version:"final"}),/REVIEW_REQUIRED/);
 assert.throws(()=>compileScreeningProgram({...input,publishingAllowed:true}),/SOURCE/);
 assert.throws(()=>compileScreeningProgram({...input,
  returns:{...input.returns,moving:{...input.returns.moving,status:"ASSUMED"}}}),/SOURCE_RETURN/);
 assert.throws(()=>compileScreeningProgram(input,{version:"final",review:{
  schema:"jarvis.screening-editorial-return/v1",sourceSha256:"a".repeat(64),
  draftReceiptSha256:draft.receipt.receiptSha256,mediaHashesVerified:true,
  decision:"REVISE_WITH_VERIFIED_ORIGIN_AND_OUTPUT",publishingAllowed:false}}),/REVIEW_REQUIRED/);
});
