import {createHash} from 'node:crypto';
const hash=x=>'sha256:'+createHash('sha256').update(x).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
const refuse=(ok,code)=>{if(!ok)throw Error('VINYL_HOLD_'+code)};
const escape=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
export function compileVinylProof(edition,roomReview){
 refuse(edition?.schema==='opf/press-000/v0'&&edition.state==='EXPERIMENT_HOLD','EXPERIMENT_SOURCE');
 refuse(edition.edition?.kind==='linked-listening-room'&&Array.isArray(edition.edition.side_a)&&edition.edition.side_a.length===1&&edition.edition.side_b.length===0,'SOURCE_SIDE_PLAN');
 refuse(edition.source?.media_bytes==='not obtained'&&edition.edition.physical_master===null,'MEDIA_PROVENANCE');
 refuse(edition.rights?.known_grant?.startsWith('links-only')===true&&edition.rights.physical_manufacture_approval==='NOT_GRANTED'&&edition.rights.master_copy_license==='NOT_GRANTED'&&edition.rights.distribution_approval==='NOT_GRANTED','SOURCE_RIGHTS');
 refuse(roomReview?.schema==='band-runtime/room-encounter-review/v1'&&roomReview.status==='SYNTHETIC_WITNESS_ONLY'&&roomReview.semanticInputs===0&&roomReview.actualRoomWrites===0,'BAND_WITNESS');
 refuse(roomReview.sourceAuthenticated===false&&roomReview.published===false&&roomReview.rightsVerified===false&&roomReview.humanActs===0,'BAND_AUTHORITY');
 refuse(Array.isArray(roomReview.witnessEvents)&&roomReview.witnessEvents.length===5,'BAND_EVENT_COUNT');
 refuse(roomReview.witnessEvents.map(x=>x.type).join(',')==='session.opened,capture.recorded,handoff.recorded,return.recorded,decision.recorded','BAND_WITNESS_SEQUENCE');
 refuse(roomReview.witnessEvents[2]?.payload?.delivery?.status==='DECLARED'&&roomReview.witnessEvents[3]?.payload?.relation?.status==='CLAIMED','FALSE_DELIVERY');
 const a1=edition.edition.side_a[0];
 refuse(a1.slot==='A1'&&a1.title===edition.source.title&&a1.source_url===edition.source.url,'TRACK_IDENTITY');
 const plan={
  schema:'lemonpress/vinyl-preflight/v1',id:'opf-press-001-held-vinyl-proposal',state:'HOLD_NOT_ORDERABLE',
  houseAdmission:'NONE',parentEdition:edition.id,
  upstreamRoom:{schema:roomReview.schema,status:roomReview.status,sourceAuthenticated:false,recordingAdmitted:false,roomEventCount:roomReview.witnessEvents.length},
  product:{medium:'12-inch-vinyl-candidate',format:'UNSELECTED_UNQUOTED',quantity:null,unitCost:null,currency:null,shipping:null,royalty:null,artistCopies:{intent:'ARTIST_COPIES_PROPOSED',count:null,delivery:'NOT_ARRANGED'},pricing:'AT_COST_INTENT_UNCALCULATED',manufacturer:'NONE_SELECTED'},
  releaseIntent:{series:'Other Peoples Fire',targetConcept:{tracks:12,creators:11},countVerified:false},
  sides:{A:[{slot:'A1',title:a1.title,source_url:a1.source_url,masterSha256:null,durationSeconds:null,rights:'LINK_ONLY_NO_AUDIO_COPY',artistCredit:edition.source.displayed_creator,creditVerified:false}],B:[]},
  safety:{audioBytesPresent:false,artworkLicensed:false,realRoom: false,permissionForPhysical:false,manufactureAuthorized:false,publicReleaseAuthorized:false,orderPlaced:false},
  missing:['Independent artist and producer rights for this specific recording','Mastering-ready audio and duration for each track','Consent for compilation, copying, sale and artist copies','Final A/B sequence and physical side capacity','Print-safe jacket/labels and artwork rights','Physical vendor quote, shipping, royalties and artist copy budget','Human lemonPRESS house admission and physical owner approval']
 };
 const receiptWrench={schema:'lemonpress/wrench/v1',input:'Source-linked PRESS 000 A1 + Band Runtime synthetic witness only',transformation:'KEEP source URL / ADD vinyl-shaped label+sleeve proposals / HOLD media copy, pricing and manufacturing',output:'Preflight JSON, timing sheet, decorative non-production sleeve and label',residual:'Other People’s Fire 12-song/11-artist concept not documented or permissioned as final track list',loss:'No native studio audio, master or playable pressing',unknown:'Track lengths, rights, physical quotes, artwork and identity',stop:'Not authorized for reproduction, print, payment, dispatch, publication or a physical record'};
 const label='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img" aria-label="Draft record-label illustration, not for manufacturing"><circle cx="300" cy="300" r="290" fill="#19221f"/><circle cx="300" cy="300" r="160" fill="#cbb58d"/><circle cx="300" cy="300" r="9" fill="#19221f"/><g fill="#19221f" text-anchor="middle" font-family="Georgia,serif"><text x="300" y="228" font-size="28">OTHER PEOPLES FIRE</text><text x="300" y="268" font-size="24">SIDE A · PROPOSAL</text><text x="300" y="350" font-size="19">'+escape(a1.title)+'</text><text x="300" y="387" font-size="18">NO MASTER / NO LICENSE</text></g><text x="300" y="470" fill="#fff" text-anchor="middle" font-size="20">NOT FOR MANUFACTURE</text></svg>\n';
 const sleeve='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PRESS 001 · Draft physical sleeve</title><style>body{background:#101a19;color:#ece2cd;font:18px/1.45 Georgia,serif;padding:2rem;max-width:42rem;margin:auto}.cover{background:#bd9c66;color:#21302b;aspect-ratio:1;max-width:32rem;display:flex;flex-direction:column;justify-content:space-between;padding:2rem;box-sizing:border-box;border:12px solid #403d2f}h1{font-size:clamp(3rem,9vw,6rem);line-height:.9}small{font:14px monospace}strong{font-family:monospace}</style><div class="cover"><small>OTHER PEOPLES FIRE · CANDIDATE EDITION</small><h1>The First Spark</h1><strong>NOT FOR MANUFACTURE · RIGHTS HOLD</strong></div><p>This sleeve is a decorative draft, not a production-ready plate. Side A1: '+escape(a1.title)+' · original linked source only. Side B: open invitation, no recorded track. Real record production requires an approved master, artwork proof, artist consent, timing and quote.</p></html>\n';
 const sheet='# VINYL SIDE / COST / ARTIST-COPY PREFLIGHT — HOLD\n\nParent edition: '+edition.id+'\n\nA1: '+a1.title+' — duration UNKNOWN; exact approved master MISSING; rights LINK ONLY.\nSide B: OPEN (not recorded audio).\n\nProposed 12-track / 11-creator compilation is a concept, not the contents of this one-song proof.\n\nSide A and B running times: UNKNOWN / no cut simulation.\nManufacturer: NOT SELECTED. Quantity: UNKNOWN. Unit cost, tax, packing and delivery: UNKNOWN. Retail price: NOT AUTHORIZED.\nArtist copies: preferred, quantities and financing NOT AGREED.\n\nThis file is NOT an order, quote, press-ready plate, manufacturing instruction, or permission to ship.\n';
 const files={'proof.json':json(plan),'wrench.json':json(receiptWrench),'center-label-draft.svg':label,'sleeve-draft.html':sleeve,'side-and-cost-sheet.md':sheet};
 const body={schema:'lemonpress/vinyl-proof-receipt/v1',parent:edition.id,mediaCopied:false,pressingOrdered:false,houseAdmitted:false,sourceRuntime:'LemonPRESS native vinyl-preflight',files:Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)).map(([p,v])=>[p,hash(v)]))};
 const receipt={...body,receiptId:hash(json(body))}; files['receipt.json']=json(receipt);
 return {files,receipt};
}
export function verifyProof(expected,actual){
 refuse(Object.keys(expected).sort().join('|')===Object.keys(actual).sort().join('|'),'FILES_CHANGED');
 for(const [name,data] of Object.entries(expected))refuse(actual[name]===data,'TAMPER_'+name);
 return true;
}
