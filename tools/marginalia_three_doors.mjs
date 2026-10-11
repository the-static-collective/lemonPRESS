/* LemonPRESS MARGINALIA THREE DOORS 002.
 * Bound, deterministic, private projections of one selected GOATnote margin.
 * No house admission, edition selection, rights elevation, publication or rendering.
 */
import {createHash} from 'node:crypto';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {inspectSelectedMargin,composeReadingCandidate} from './goatnote_marginalia.mjs';

export const SCORE_SCHEMA='lemonpress.marginalia-three-doors/v0';
const LANES=['page','voice','fragment'];
const sha=s=>'sha256:'+createHash('sha256').update(s,'utf8').digest('hex');
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const insist=(yes,message)=>{if(!yes)throw Error(message);};
const safe=s=>String(s).replace(/[\r\n]+/g,' ').replace(/[<>[\]#*]/g,' ').slice(0,90);
const quote=s=>{
 const tick=String.fromCharCode(96),runs=s.match(new RegExp(tick+'+','g'))||[];
 const fence=tick.repeat(Math.max(3,...runs.map(t=>t.length+1)));
 return fence+'text\n'+s+'\n'+fence;
};
function requested(request){
 insist(Array.isArray(request)&&request.length>=1&&request.length<=3,'SELECT_ONE_TO_THREE_DOORS');
 insist(request.every(x=>LANES.includes(x))&&new Set(request).size===request.length,'INVALID_OR_DUPLICATE_DOOR');
 return LANES.filter(x=>request.includes(x));
}
const p=(role,text,observedAt,source)=>({
 role,text,observed_at:observedAt||null,
 source_layer:source,source_is_original:source==='selected_exact_excerpt',
 evidence_level:source==='selected_exact_excerpt'?'QUOTED_DECLARED_VERSION':'HUMAN_INTERPRETATION'
});
function parts(packet){
 const s=packet.source,m=packet.reading,e=packet.relation;
 const arr=[
  p('original_excerpt',s.excerpt,null,'selected_exact_excerpt'),
  p('human_margin',m.text,m.recorded_at,'human_margin')
 ];
 if(e){
  arr.push(p('relation_discovery',e.discovery_trace,e.first_perceived_at,'human_relation'));
  arr.push(p('relation_evidence_path',e.evidence_path,e.first_perceived_at,'human_relation'));
 }
 return arr;
}
function page(packet){
 const s=packet.source,m=packet.reading,e=packet.relation;
 const lines=[
  '# Page door · '+safe(s.title),'',
  '**PRIVATE LAYOUT DRAFT · NOT A PRINT PROOF OR PUBLICATION**','',
  '> Source excerpt, separately selected from one frozen version','',
  quote(s.excerpt),'',
  '---','',
  'Marginal note · '+m.kind+' · '+m.recorded_at,'',quote(m.text),''
 ];
 if(e)lines.push('Connection noticed: '+e.first_perceived_at,
  'Relation status at selection: '+e.recorded_current_status,'',
  'A later human relation, not part of the original source.','');
 lines.push('','Colophon: full source version omitted; printed rights unreviewed.','');
 return lines.join('\n');
}
function voice(packet){
 const s=packet.source,m=packet.reading,e=packet.relation;
 const lines=['# Voice door · '+safe(s.title),'',
  '**SCRIPT ONLY · NO AUDIO GENERATED, MIXED, ADMITTED OR RELEASED**','',
  '[Voice A / original passage · quote, not witness testimony invented by this script]','',
  quote(s.excerpt),'',
  '[Short unscored silence — optional editorial suggestion, not duration authority]','',
  '[Voice B / later reader · marginal interpretation at '+m.recorded_at+']','',
  quote(m.text),''];
 if(e)lines.push('[Voice B / later connection discovered '+e.first_perceived_at+']','',
  quote(e.discovery_trace),'','[Evidence-path declaration from GOATnote, not independent proof]','',
  quote(e.evidence_path),'');
 lines.push('','Audio assets: NONE. Narrator identity/consent: NOT VERIFIED.',
  'PRESS MOUTH/Suno Pantry parcels: NOT PROVIDED. Audio Composer rendering: NOT PERFORMED.','');
 return lines.join('\n');
}
function fragment(packet){
 const s=packet.source,m=packet.reading,e=packet.relation;
 const lines=['# Fragment door · '+safe(s.title),'',
  '**PRIVATE CRAWLER-NATIVE DRAFT · NOT A PUBLISHED WEB PAGE**','',
  'Entry point: selected passage. Out-of-order readers must preserve source / margin distinction.','',
  '## Fragment 001 · Selected quote','',
  quote(s.excerpt),'',
  'Selected excerpt digest: '+s.excerpt_sha256,
  'Parent full-version digest: '+s.version_sha256+' (DECLARED / BODY ABSENT)','',
  '## Fragment 002 · The reader speaks later','',
  quote(m.text),'',
  'Human margin observed: '+m.recorded_at,'',
  '## Fragment 003 · Relational continuity',''];
 if(e)lines.push('Connection first perceived: '+e.first_perceived_at,
  'Source occurrence time: UNKNOWN',
  'GOATedge local status at selection: '+e.recorded_current_status+' (NOT PRESS ADMISSION)','',
  quote(e.discovery_trace),'');
 else lines.push('NO RELATION DISCLOSED. This omission does not assert no relationship exists.');
 lines.push('','Retrieval disclaimer: excerpt is not the full source. This candidate has NO public URL.','');
 return lines.join('\n');
}
function receipt(lane,packet,content,candidateId){
 const losses={
  page:'Interactivity, full version, live margins, and later updates are absent',
  voice:'Page position and typographic adjacency are absent; timing and sound remain unrendered',
  fragment:'Original full-source context, unselected margins and external retrieval provenance are absent'
 };
 const transforms={
  page:'Arrange one exact quote and a later human margin as a private page draft',
  voice:'Sequence one exact quote and later human voices as a script without audio',
  fragment:'Split the explicit selection into arbitrary-entry private text fragments'
 };
 return {
  schema:'lemonpress/wrench-projection-receipt/v0',
  input:{candidate_id:candidateId,packet_sha256:packet.checksum,
   exact_excerpt_sha256:packet.source.excerpt_sha256,
   full_source_verification:'UNAVAILABLE_SOURCE_BODY_OMITTED'},
  transformation:transforms[lane],
  output:{lane,kind:'UNADMITTED_PROJECTION_PLAN',sha256:sha(content),file:lane+'.md'},
  residual:'Original complete GOATnote note, other margins, unselected sources and human consent remain outside this plan',
  loss:losses[lane],
  unknown:['external source signer','original full-version authenticity','publication rights',
   'human performance consent','future editorial selection'],
  stop:'HOLD: no renderer, no issue admission, no rights or house release'
 };
}
export function makeThreeDoorScore(raw,{doors=['page','voice','fragment']}={}){
 const chosen=requested(doors);
 const inspected=inspectSelectedMargin(raw);
 const {packet,verification}=inspected;
 const {candidate,manuscript}=composeReadingCandidate(inspected);
 insist(candidate.state==='PRIVATE_CANDIDATE'&&candidate.rights_granted===false&&
  candidate.publication_authorized===false,'UNSAFE_PARENT_CANDIDATE');
 const selected=parts(packet);
 const names={page,voice,fragment};
 const artifacts=chosen.map(lane=>{
  const content=names[lane](packet);
  return {lane,file:lane+'.md',content,digest:sha(content),receipt:receipt(lane,packet,content,candidate.id)};
 });
 const scoreCore={
  schema:SCORE_SCHEMA,
  state:'PRIVATE_UNADMITTED_PLANS',
  base_candidate_id:candidate.id,
  packet_checksum:packet.checksum,
  source_version_sha256:packet.source.version_sha256,
  source_version_posture:'DECLARED_NOT_REVERIFIED_NO_BODY',
  exact_quote_sha256:packet.source.excerpt_sha256,
  quote_posture:verification.excerpt_checksum,
  slots:selected.map((s,i)=>({
   slot:i+1,role:s.role,source_layer:s.source_layer,
   observed_at:s.observed_at,evidence_level:s.evidence_level,
   content_sha256:sha(s.text)
  })),
  doors:artifacts.map(a=>({lane:a.lane,file:a.file,sha256:a.digest,
   receipt:'receipts/'+a.lane+'.json'})),
  boundaries:{house_admission:false,editorial_selection:false,
   rights_grant:false,published:false,deployed:false,audio_rendered:false,
   print_proof:false,web_page:false,private_only:true}
 };
 const score={...scoreCore,score_id:'lp-three-doors:'+sha(canonical(scoreCore)).slice(7)};
 const compiled=artifacts.map(a=>({...a,receipt:{...a.receipt,score_id:score.score_id}}));
 return {score,manuscript,candidate,artifacts:compiled};
}
export async function composeThreeDoorsLocal(raw,outdir,{doors}={}){
 insist(typeof outdir==='string'&&outdir.trim(),'OUTPUT_DIRECTORY_REQUIRED');
 const result=makeThreeDoorScore(raw,doors?{doors}:{});
 const path=resolve(outdir);
 insist(!existsSync(path),'CREATE_ONLY_OUTPUT_EXISTS');
 await mkdir(path,{recursive:false,mode:0o700});
 await mkdir(join(path,'receipts'),{mode:0o700});
 const save=(relative,contents)=>writeFile(join(path,relative),contents,{encoding:'utf8',flag:'wx',mode:0o600});
 await save('source-selection.json',raw);
 await save('score.json',JSON.stringify(result.score,null,2)+'\n');
 await save('reading-candidate.json',JSON.stringify(result.candidate,null,2)+'\n');
 await save('reading-candidate.md',result.manuscript);
 for(const a of result.artifacts){
  await save(a.file,a.content);
  await save('receipts/'+a.lane+'.json',JSON.stringify(a.receipt,null,2)+'\n');
 }
 return {score_id:result.score.score_id,state:result.score.state,
  doors:result.artifacts.map(a=>a.lane),outdir:path,
  authority:'NONE',published:false};
}

/* Independent cold replay from portable private files. No trust in hashes alone. */
export async function verifyThreeDoorsLocal(outdir){
 const path=resolve(outdir);
 const raw=await readFile(join(path,'source-selection.json'),'utf8');
 const stored=JSON.parse(await readFile(join(path,'score.json'),'utf8'));
 insist(stored?.schema===SCORE_SCHEMA&&Array.isArray(stored.doors),'INVALID_STORED_SCORE');
 const doors=stored.doors.map(d=>d.lane);
 const result=makeThreeDoorScore(raw,{doors});
 insist(canonical(stored)===canonical(result.score),'SCORE_REPLAY_MISMATCH');
 const other=JSON.parse(await readFile(join(path,'reading-candidate.json'),'utf8'));
 insist(canonical(other)===canonical(result.candidate),'CANDIDATE_REPLAY_MISMATCH');
 insist(await readFile(join(path,'reading-candidate.md'),'utf8')===result.manuscript,
  'MANUSCRIPT_REPLAY_MISMATCH');
 for(const a of result.artifacts){
  insist(await readFile(join(path,a.file),'utf8')===a.content,'PROJECTION_REPLAY_MISMATCH_'+a.lane);
  const r=JSON.parse(await readFile(join(path,'receipts',a.lane+'.json'),'utf8'));
  insist(canonical(r)===canonical(a.receipt),'RECEIPT_REPLAY_MISMATCH_'+a.lane);
 }
 return {score_id:result.score.score_id,replayed:true,
  verified_doors:doors,publication_authorized:false,
  original_source_verified:false,externally_authenticated:false};
}
