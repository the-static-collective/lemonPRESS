import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {compileMinuteMailKit,verifyMinuteKit} from "../src/minute-mail-house.mjs";
const sha=x=>createHash("sha256").update(x).digest("hex");
const input={schema:"jarvis.minute-mail-kit-source/v1",project:"MINUTE-MAIL-001",
 title:"THE LOST MINUTE POST OFFICE",intent:{schema:"planz.minute-mail-creative-intent/v1",
 usefulAct:"Ask a neighbor what would help."},
 media:{proof:{file:"proof-film.mp4",sha256:"a".repeat(64)},
 revised:{file:"revised-film.mp4",sha256:"b".repeat(64)}},
 sourcePlanSha256:"c".repeat(64),revisionPlanSha256:"d".repeat(64),
 originalNativeReceiptsVerified:true,publicRelease:false,rightsGranted:false};
test("original lemonPRESS generates a functional offline time-return kit and revises it",()=>{
 const draft=compileMinuteMailKit(input);
 const review={schema:"jarvis.minute-mail-editorial-review/v1",status:"REVISE_CLARITY_WITH_SOURCE_EVIDENCE",
 sourceSha256:sha(JSON.stringify(input,null,2)+"\n"),draftReceiptSha256:draft.receipt.receiptSha256,
 firstVideoChecked:true,secondVideoChecked:true,releaseAllowed:false};
 const final=compileMinuteMailKit(input,{version:"final",review});
 assert.notEqual(draft.receipt.receiptSha256,final.receipt.receiptSha256);
 assert.equal(final.receipt.published,false);
 assert.equal(final.receipt.tracksPeople,false);
 assert.ok(final.files["index.html"].includes("Date.now()+60000"));
 assert.ok(final.files["minute-stamps.svg"].includes("RETURN TO SENDER"));
 assert.ok(verifyMinuteKit(final.files,{...final.files}));
 assert.throws(()=>verifyMinuteKit(final.files,{...final.files,"letter.md":"forged"}),/TAMPER/);
});
test("unlicensed publishing and invented editorial reviews are refused",()=>{
 assert.throws(()=>compileMinuteMailKit({...input,publicRelease:true}),/SOURCE/);
 assert.throws(()=>compileMinuteMailKit(input,{version:"final"}),/REVIEW/);
 assert.throws(()=>compileMinuteMailKit({...input,media:{...input.media,proof:input.media.revised}}),/SOURCE/);
});
