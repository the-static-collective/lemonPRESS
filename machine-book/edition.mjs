#!/usr/bin/env node
// lemonPRESS MACHINE MANUSCRIPT 001 — creates only HELD editorial proofs.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const sha = x => createHash("sha256").update(typeof x === "string" ? x : JSON.stringify(x)).digest("hex");
const need = (cond, msg) => { if (!cond) throw Error("PRESS_HOLD_" + msg); };
const escape = s => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const safe = s => typeof s === "string" && s.length > 0 && s.length <= 700 && !/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(s);
const exactKeys = (v, keys) => JSON.stringify(Object.keys(v || {}).sort()) === JSON.stringify([...keys].sort());

export function makeEdition(packet) {
  need(exactKeys(packet, ["schema","source","folios","board","status","authority","executed","published","approved"]), "PACKET_FIELDS");
  need(packet.schema === "cannon.machine-folio-review/v1" && packet.status === "HELD_CANDIDATE", "SCHEMA");
  need(packet.authority === "NONE" && packet.executed === false && packet.published === false && packet.approved === false, "AUTHORITY");
  const s = packet.source;
  need(exactKeys(s, ["planzCommit","planzManifestSha256","workbenchCommit","selectedPlanId","candidateDigest"]), "SOURCE_FIELDS");
  need([s.planzCommit, s.workbenchCommit].every(x => /^[0-9a-f]{40}$/.test(x)), "COMMIT");
  need([s.planzManifestSha256, s.candidateDigest].every(x => /^[0-9a-f]{64}$/.test(x)), "SOURCE_DIGEST");
  need(/^plan-[0-9a-f]{24}$/.test(s.selectedPlanId), "PLAN_ID");
  need(Array.isArray(packet.folios) && packet.folios.length >= 2 && packet.folios.length <= 8, "FOLIOS");
  for(const f of packet.folios) {
    need(exactKeys(f, ["id","title","purpose","inputClass","inputPort","outputClass","outputPort","originCutId"]), "FOLIO_FIELDS");
    need([f.id,f.title,f.purpose,f.inputClass,f.inputPort,f.outputClass,f.outputPort,f.originCutId].every(safe), "FOLIO_VALUE");
    need(f.id.length <= 90 && f.title.length <= 120 && f.purpose.length <= 400, "FOLIO_LENGTH");
  }
  need(new Set(packet.folios.map(x=>x.id)).size === packet.folios.length,"FOLIO_IDENTITY");
  const b=packet.board;
  need(exactKeys(b,["status","gaps","nonclaim"]), "BOARD_FIELDS");
  need(["candidate_with_gaps","synthetic_route_matched"].includes(b.status), "BOARD_STATUS");
  need(Array.isArray(b.gaps) && b.gaps.length <= 30 && b.gaps.every(x => x && typeof x === "object"), "GAP_SHAPE");
  need(b.status === (b.gaps.length ? "candidate_with_gaps" : "synthetic_route_matched"), "BOARD_CONTRADICTION");
  need(safe(b.nonclaim) && b.nonclaim.includes("no project action"), "NONCLAIM");
  const plateWidth=900, plateHeight=440;
  const cards=packet.folios.map((f,i)=>{
    const x=44+i*(812/packet.folios.length), width=788/packet.folios.length;
    return '<g><rect x="'+x.toFixed(2)+'" y="118" width="'+width.toFixed(2)+'" height="205" rx="9" fill="#f4eedb" stroke="#344b49" stroke-width="3"/>'+
      '<text x="'+(x+12).toFixed(2)+'" y="150" font-size="18" fill="#314440">FOLIO '+(i+1)+'</text>'+
      '<text x="'+(x+12).toFixed(2)+'" y="185" font-size="13" fill="#314440">'+escape(f.title.slice(0,18))+'</text>'+
      '<text x="'+(x+12).toFixed(2)+'" y="248" font-size="12" fill="#714b3c">'+escape(f.inputClass+":"+f.inputPort).slice(0,28)+'</text>'+
      '<text x="'+(x+12).toFixed(2)+'" y="280" font-size="12" fill="#714b3c">'+escape(f.outputClass+":"+f.outputPort).slice(0,28)+'</text></g>';
  }).join("");
  const plate='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+plateWidth+' '+plateHeight+'" role="img" aria-label="Held machine folio inspection plate">'+
    '<rect width="900" height="440" fill="#dfd2b5"/>'+
    '<text x="44" y="68" fill="#263e3a" font-family="serif" font-size="40">THE BOOK OF MACHINES</text>'+
    '<text x="44" y="98" fill="#714b3c" font-family="monospace" font-size="16">CANDIDATE EDITION · NOT A WORKING MACHINE</text>'+
    '<g font-family="monospace">'+cards+'</g>'+
    '<text x="44" y="370" fill="#714b3c" font-family="serif" font-size="23">PORT INSPECTION: '+escape(b.status)+'</text>'+
    '<text x="44" y="405" fill="#714b3c" font-family="monospace" font-size="14">Unresolved joins: '+b.gaps.length+' · No manufacturing or publishing authorization</text></svg>\n';
  const folios=packet.folios.map((f,i)=>'<section><h2>Folio '+(i+1)+': '+escape(f.title)+'</h2><p>'+escape(f.purpose)+'</p><dl>'+
    '<dt>Input</dt><dd>'+escape(f.inputClass+":"+f.inputPort)+'</dd><dt>Output</dt><dd>'+escape(f.outputClass+":"+f.outputPort)+'</dd>'+
    '<dt>Source angle</dt><dd><code>'+escape(f.originCutId)+'</code></dd></dl></section>').join("");
  const gaps=b.gaps.length ? b.gaps.map((g,i)=>'<li><code>GAP '+(i+1)+'</code> '+escape(JSON.stringify(g).slice(0,380))+'</li>').join("") : '<li>No declared synthetic port mismatch; this does not establish an executable integration.</li>';
  const html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Book of Machines — Held Edition</title>'+
    '<style>body{max-width:58rem;margin:2rem auto;padding:1rem;background:#e6dbc2;color:#263e3a;font:18px/1.6 Georgia,serif}h1{font-size:3rem}section{border-top:1px solid #777;padding:1rem 0}code{overflow-wrap:anywhere}dt{font-weight:bold}dd{margin-bottom:.5rem}.hold{border:2px solid #7a4e37;padding:1rem}</style>'+
    '<main><p class="hold">EXPERIMENTAL EDITORIAL PROOF — HELD · NOT PUBLISHED · NOT FOR FABRICATION · NO EXECUTABLE MACHINE</p>'+
    '<h1>THE BOOK OF MACHINES</h1><p>Machine conjecture from a PlanZ candidate and Workbench port inspection. No actual third-party effects.</p>'+
    '<p>Plan: <code>'+escape(s.selectedPlanId)+'</code><br>PlanZ manifest: <code>'+s.planzManifestSha256+'</code></p>'+
    '<img src="plate.svg" alt="Diagram of proposed machine folios and held inspection" style="max-width:100%">'+folios+
    '<h2>Unresolved mechanical questions</h2><ol>'+gaps+'</ol><p><strong>Source ancestry remains elsewhere.</strong> A folio is an editorial projection, not project authority.</p></main></html>\n';
  const metadata={schema:"lemonpress.machine-manuscript/v1",title:"THE BOOK OF MACHINES / held candidate edition",release:"HOLD_NOT_PUBLISHED",parentPlan:s.selectedPlanId,
    source:s, folioCount:packet.folios.length,sourceBoardStatus:b.status,unresolvedGapCount:b.gaps.length,authority:"NONE",
    machineExecuted:false,pressAuthorized:false,printedCopies:0,sourcePacketSha256:sha(JSON.stringify(packet))};
  const files={"edition.json":JSON.stringify(metadata,null,2)+"\n","index.html":html,"plate.svg":plate};
  const hashes=Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,sha(v)]));
  files["receipt.json"]=JSON.stringify({schema:"lemonpress.machine-manuscript-receipt/v1",status:"HOLD_NOT_PUBLISHED",sourcePacketSha256:metadata.sourcePacketSha256,
     editionFiles:hashes,receiptDigest:sha({metadata,hashes}), nonclaims:["No native Workbench execution certified by this edition","No hardware operation","No author or project owner acceptance","No publication or manufacturing"]},null,2)+"\n";
  return files;
}

function main(args) {
  need(args.length === 5 && ["build","verify"].includes(args[0]) && args[1]==="--in" && args[3]==="--out", "USAGE");
  const mode=args[0], input=resolve(args[2]), output=resolve(args[4]);
  const packet=JSON.parse(readFileSync(input,"utf8"));
  const files=makeEdition(packet);
  if(mode==="build") {
    need(!existsSync(output),"OUTPUT_EXISTS");
    mkdirSync(output,{recursive:false});
    for(const [name,content] of Object.entries(files)) writeFileSync(join(output,name),content,{encoding:"utf8",flag:"wx"});
  }else{
    need(existsSync(output),"OUTPUT_MISSING");
    need(JSON.stringify(readdirSync(output).sort())===JSON.stringify(Object.keys(files).sort()),"FILE_LIST");
    for(const [name,content] of Object.entries(files)) need(readFileSync(join(output,name),"utf8")===content,"TAMPER_"+name);
  }
  process.stdout.write(JSON.stringify({status: mode==="build"?"HELD_EDITORIAL_PROOF":"COLD_REPLAY_VERIFIED",files:Object.keys(files),published:false})+"\n");
}
if(process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)){
  try{main(process.argv.slice(2));}catch(e){process.stderr.write(String(e.message)+"\n");process.exitCode=2;}
}
