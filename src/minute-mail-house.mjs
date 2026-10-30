// lemonPRESS-MINUTE-001 — a self-contained, playable/printable
// original minute-return kit with a source-bound editorial revision.
// The timer is client-only and never transmits or claims a verified good deed.
import {createHash} from "node:crypto";
const sha=x=>createHash("sha256").update(x).digest("hex");
const json=x=>JSON.stringify(x,null,2)+"\n";
const fail=(yes,s)=>{if(!yes)throw Error("LEMON_MINUTE_HOLD_"+s)};
const esc=x=>String(x).replaceAll("&","&amp;").replaceAll("<","&lt;")
 .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;");
function validSource(i){
 fail(i?.schema==="jarvis.minute-mail-kit-source/v1"
  &&i.title==="THE LOST MINUTE POST OFFICE"
  &&i.project==="MINUTE-MAIL-001"
  &&i.intent?.schema==="planz.minute-mail-creative-intent/v1"
  &&typeof i.intent.usefulAct==="string"
  &&i.intent.usefulAct.length>12&&i.intent.usefulAct.length<80
  &&i.media?.proof?.file==="proof-film.mp4"
  &&i.media?.revised?.file==="revised-film.mp4"
  &&/^[a-f0-9]{64}$/.test(i.media.proof.sha256)
  &&/^[a-f0-9]{64}$/.test(i.media.revised.sha256)
  &&i.media.proof.sha256!==i.media.revised.sha256
  &&i.sourcePlanSha256!==i.revisionPlanSha256
  &&i.originalNativeReceiptsVerified===true
  &&i.publicRelease===false&&i.rightsGranted===false,"SOURCE");
 return i;
}
export function compileMinuteMailKit(input,{version="draft",review=null}={}){
 const i=validSource(input);
 fail(["draft","final"].includes(version),"VERSION");
 if(version==="draft")fail(review===null,"DRAFT_REVIEW");
 else fail(review?.schema==="jarvis.minute-mail-editorial-review/v1"
  &&review.status==="REVISE_CLARITY_WITH_SOURCE_EVIDENCE"
  &&review.sourceSha256===sha(json(i))
  &&/^[a-f0-9]{64}$/.test(review.draftReceiptSha256)
  &&review.firstVideoChecked===true&&review.secondVideoChecked===true
  &&review.releaseAllowed===false,"REVIEW");
 const tagline=version==="draft"?"A curious little film about returning a lost minute.":
  "A tiny service station for attention: choose one act, give one minute, and leave no trace.";
 const title="THE LOST MINUTE POST OFFICE";
 const instructions=version==="draft"?
  "Choose one small kindness. This is a private draft; nothing is sent.":
  "Choose a doable kindness, then try it away from the screen. You can skip, stop or return.";
 const svg='<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1060" viewBox="0 0 800 1060" role="img" aria-label="Three return-to-sender minute stamps"><rect width="800" height="1060" fill="#f0dfbc"/><g stroke="#152d32" stroke-width="9" fill="none"><rect x="44" y="40" width="712" height="980"/><rect x="82" y="90" width="635" height="235"/><rect x="82" y="382" width="635" height="235"/><rect x="82" y="674" width="635" height="235"/></g><g fill="#152d32" font-family="Georgia,serif" text-anchor="middle"><text x="400" y="170" font-size="45">ONE MINUTE</text><text x="400" y="245" font-size="33">LISTEN</text><text x="400" y="466" font-size="45">ONE MINUTE</text><text x="400" y="543" font-size="33">HELP</text><text x="400" y="758" font-size="45">ONE MINUTE</text><text x="400" y="837" font-size="33">NOTICE</text><text x="400" y="972" font-size="22">RETURN TO SENDER • NOTHING TRACKED</text></g></svg>\n';
 const page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>body{margin:0;background:#101d23;color:#fff0d0;font:18px/1.55 system-ui}main{max-width:780px;padding:2rem;margin:auto}h1{font:clamp(3rem,9vw,6rem) Georgia,serif;line-height:.98}a{color:#ebc786}button{background:#e9bc75;color:#102129;padding:.8rem 1.3rem;border:0;border-radius:1rem;font:bold 17px system-ui;cursor:pointer}button:focus-visible{outline:4px solid white}.card{background:#20343c;border:1px solid #74908e;border-radius:1rem;padding:1rem;margin:1rem 0}video{max-width:100%;border-radius:.7rem}#clock{font:3rem monospace}small{color:#a5c3c7}@media print{button,video,.screen{display:none}body{background:white;color:black}.card{break-inside:avoid;color:black;background:white}}</style><main><p>EXPEDITION 001 • LOCAL / UNPUBLISHED</p><h1>'+title+'</h1><p>'+esc(tagline)+'</p><div class="card"><h2>From the workshop</h2><video controls playsinline preload="metadata" src="./media/revised-film.mp4" aria-label="A new original audiovisual minute postcard"></video><p><small>A first-cut film and independently revised original Toaster film, both verified by their source receipts. No external distribution permission is implied.</small></p></div><div class="card"><h2>THE COUNTER OF SMALL RETURNS</h2><p>'+esc(instructions)+'</p><p>Suggested act: <strong>'+esc(i.intent.usefulAct)+'</strong></p><button type="button" id="start">Begin a minute</button> <button type="button" id="stop">Stop</button><p id="clock" aria-live="polite">1:00</p><p id="message">No account. No streak. No notification. Nothing transmitted.</p></div><div class="card"><h2>Three stamps you cannot purchase</h2><p>LISTEN · HELP · NOTICE. A stamp is an invitation, not proof of another person’s consent or a completed act.</p><a href="./minute-stamps.svg">Open printable stamps</a></div><div class="card"><h2>What came back</h2><p>Proof film: <code>'+esc(i.media.proof.sha256)+'</code></p><p>Revised film: <code>'+esc(i.media.revised.sha256)+'</code></p><p>Version: '+esc(version)+'. No person or neighbor is named, contacted, tracked, or verified.</p></div><script>(function(){let t=null,end=0;const el=document.getElementById("clock");function halt(){if(t){clearInterval(t);t=null;}}document.getElementById("start").onclick=function(){halt();end=Date.now()+60000;el.textContent="1:00";t=setInterval(function(){const n=Math.max(0,Math.ceil((end-Date.now())/1000));el.textContent=Math.floor(n/60)+":"+String(n%60).padStart(2,"0");if(n===0){halt();document.getElementById("message").textContent="Your minute is yours. No receipt of your life was collected."; }},200)};document.getElementById("stop").onclick=function(){halt();el.textContent="Stopped";};})();</script></main></html>\n';
 const letter="# The Lost Minute Post Office\n\n"+tagline+"\n\nSuggested act: "+i.intent.usefulAct+"\n\nThe first short film was a proof. The second was genuinely re-rendered based on its receipt.\n\nPrint three minute stamps. Offer one unrecorded act of care. No request for personal information, claims of successful help, external release, or earned rewards.\n\nSource video: "+i.media.proof.sha256+"\nRevised video: "+i.media.revised.sha256+"\n";
 const files={"index.html":page,"minute-stamps.svg":svg,"letter.md":letter};
 const b={schema:"lemonpress.minute-mail-kit/v1",version,title,
  sourceSha256:sha(json(i)),reviewSha256:review?sha(json(review)):null,
  previousDraftSha256:review?.draftReceiptSha256??null,
  originalProofFilmSha256:i.media.proof.sha256,
  revisedNativeFilmSha256:i.media.revised.sha256,
  originalSourceOwners:["planZ","CANNON","the-haunted-toaster"],
  allLocalOnly:true,published:false,rightsGranted:false,
  tracksPeople:false,claimsRealWorldAct:false,
  files:Object.fromEntries(Object.entries(files).map(([n,v])=>[n,sha(v)]))};
 const receipt={...b,receiptSha256:sha(json(b))};
 files["receipt.json"]=json(receipt);
 return {files,receipt};
}
export function verifyMinuteKit(expected,actual){
 fail(Object.keys(expected).sort().join("|")===Object.keys(actual).sort().join("|"),"FILES");
 for(const [k,v] of Object.entries(expected))fail(actual[k]===v,"TAMPER_"+k);
 return true;
}
