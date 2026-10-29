import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { makeEdition } from "./edition.mjs";

const h="a".repeat(64), c="b".repeat(40),cut="cut-"+"d".repeat(24),plan="plan-"+"e".repeat(24);
const packet=()=>({
  schema:"cannon.machine-folio-review/v1",
  source:{planzCommit:c,planzManifestSha256:h,workbenchCommit:c,selectedPlanId:plan,candidateDigest:h},
  folios:[
    {id:"first",title:"Lens: ABSENCE",purpose:"Find missing port",inputClass:"prompt",inputPort:"proposed",outputClass:"candidate",outputPort:"held",originCutId:cut},
    {id:"second",title:"Receiving world",purpose:"Require independent admission",inputClass:"candidate",inputPort:"accepted",outputClass:"receipt",outputPort:"hold",originCutId:cut}
  ],
  board:{status:"candidate_with_gaps",gaps:[{reason:"concrete_lift_gap",index:0}],nonclaim:"Only declared ports have been checked; no project action is authorized or executed."},
  status:"HELD_CANDIDATE",authority:"NONE",executed:false,published:false,approved:false
});

test("native publisher produces legible visual and independent held receipt",()=>{
 const x=makeEdition(packet());
 assert.deepEqual(Object.keys(x).sort(),["edition.json","index.html","plate.svg","receipt.json"]);
 assert.equal(JSON.parse(x["edition.json"]).release,"HOLD_NOT_PUBLISHED");
 assert.equal(JSON.parse(x["receipt.json"]).status,"HOLD_NOT_PUBLISHED");
 assert.match(x["plate.svg"],/THE BOOK OF MACHINES/);
 assert.match(x["index.html"],/NOT PUBLISHED/);
 assert.equal(JSON.stringify(x),JSON.stringify(makeEdition(packet())));
});
test("HTML never evaluates imported invention text",()=>{
 const x=packet(); x.folios[0].title='<script>alert(1)</script>';
 const result=makeEdition(x);
 assert.ok(!result["index.html"].includes("<script>"));
 assert.ok(!result["plate.svg"].includes("<script>"));
 assert.match(result["index.html"],/&lt;script&gt;/);
});
test("no publication, fabricated approvals, missing ancestry, or contradictory gaps",()=>{
 for(const [field,value] of [["published",true],["executed",true],["approved",true],["authority","OWNER"]]){
  const x=packet();x[field]=value;assert.throws(()=>makeEdition(x),/AUTHORITY/);
 }
 let x=packet();x.source.planzCommit="moving-main";assert.throws(()=>makeEdition(x),/COMMIT/);
 x=packet();x.board.gaps=[];assert.throws(()=>makeEdition(x),/BOARD_CONTRADICTION/);
 x=packet();x.folios[0].foo="unknown permission";assert.throws(()=>makeEdition(x),/FOLIO_FIELDS/);
});
test("CLI holds, independently verifies, and refuses tampered output",()=>{
 const dir=mkdtempSync(join(tmpdir(),"lemon-machine-"));
 try{
  const input=join(dir,"input.json"), out=join(dir,"proof");
  writeFileSync(input,JSON.stringify(packet()));
  const run=mode=>spawnSync(process.execPath,[new URL("./edition.mjs",import.meta.url).pathname,mode,"--in",input,"--out",out],{encoding:"utf8"});
  assert.equal(run("build").status,0);
  assert.equal(run("verify").status,0);
  assert.notEqual(run("build").status,0);
  writeFileSync(join(out,"index.html"),"FORGED APPROVAL");
  assert.notEqual(run("verify").status,0);
 }finally{rmSync(dir,{recursive:true,force:true})}
});
