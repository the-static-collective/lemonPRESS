/* LemonPRESS x GOATnote 001: private, unadmitted reading-edition composer. */
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {join} from 'node:path';
export const CANDIDATE_SCHEMA='lemonpress.goatnote-reading-candidate/v0';
const MAX=32768;
const kinds=['witness','question','interpretation','correction','carry','connection'];
const statuses=['perceived','proposed','admitted','weakened','refused','unresolved'];
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const ok=(v,e)=>{if(!v)throw Error(e);};
const sha=s=>'sha256:'+createHash('sha256').update(s,'utf8').digest('hex');
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
const iso=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(x)&&!Number.isNaN(Date.parse(x));
const str=(x,n)=>typeof x==='string'&&x.length>0&&x.length<=n;
const exact=(x,keys)=>ok(object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k)),'UNEXPECTED_PACKET_FIELDS');
const digest=x=>typeof x==='string'&&/^sha256:[a-f0-9]{64}$/.test(x);
export function inspectSelectedMargin(raw){
 ok(typeof raw==='string'&&Buffer.byteLength(raw,'utf8')<=MAX,'PRIVATE_CARRIER_SIZE_LIMIT');
 let p;try{p=JSON.parse(raw);}catch{throw Error('INVALID_PRIVATE_CARRIER_JSON');}
 exact(p,['schema','posture','selection','source','reading','relation','authority','checksum']);
 ok(p.schema==='goatnote.lemonpress-margin/v0'&&p.posture==='PRIVATE_UNADMITTED_CANDIDATE','NOT_A_SELECTED_GOATNOTE_MARGIN');
 exact(p.selection,['selected_at','method','scope','publication_grant']);
 ok(iso(p.selection.selected_at)&&p.selection.method==='HUMAN_EXPLICIT_ONE_MARGIN'&&
  p.selection.scope==='LOCAL_DOWNLOAD_ONLY'&&p.selection.publication_grant===false,'NOT_HUMAN_SCOPED');
 exact(p.source,['note_id','version_id','version_sha256','title','excerpt','excerpt_start','excerpt_end','excerpt_sha256','version_body_disclosed']);
 const s=p.source;
 ok(str(s.note_id,256)&&str(s.version_id,256)&&digest(s.version_sha256)&&
  str(s.title,300)&&str(s.excerpt,2000)&&Number.isInteger(s.excerpt_start)&&
  Number.isInteger(s.excerpt_end)&&s.excerpt_start>=0&&
  s.excerpt_end-s.excerpt_start===s.excerpt.length&&
  digest(s.excerpt_sha256)&&sha(s.excerpt)===s.excerpt_sha256&&
  s.version_body_disclosed===false,'SOURCE_EXCERPT_NOT_BOUND');
 exact(p.reading,['margin_id','kind','text','recorded_at']);
 const m=p.reading;
 ok(str(m.margin_id,256)&&kinds.includes(m.kind)&&str(m.text,6000)&&iso(m.recorded_at),'INVALID_MARGIN_READING');
 if(p.relation!==null){
  exact(p.relation,['edge_id','relation_type','first_perceived_at','recorded_current_status','discovery_trace','evidence_path','read_only','locally_admitted_means_press_admitted']);
  const e=p.relation;
  ok(str(e.edge_id,256)&&str(e.relation_type,120)&&iso(e.first_perceived_at)&&
   statuses.includes(e.recorded_current_status)&&str(e.discovery_trace,2000)&&
   str(e.evidence_path,2000)&&e.read_only===true&&e.locally_admitted_means_press_admitted===false,'INVALID_RELATION_DISPOSITION');
 }
 exact(p.authority,['goatnote_margin_is_source','press_admission','house_release','signer_authenticated','version_bytes_included']);
 ok(Object.values(p.authority).every(x=>x===false),'ILLICIT_PRESS_AUTHORITY');
 ok(digest(p.checksum),'INVALID_PACKET_CHECKSUM');
 const {checksum,...unsigned}=p;
 ok(sha('GOATNOTE-LEMONPRESS-MARGIN-001|'+canonical(unsigned))===checksum,'PACKET_CHECKSUM_MISMATCH');
 return {packet:p,verification:{
  packet_self_checksum:'MATCHES_UNSIGNED_PACKET',excerpt_checksum:'INDEPENDENTLY_MATCHED',
  source_version_sha256:'DECLARED_NOT_REVERIFIED_NO_BODY',source_authority:'NOT_VERIFIED',
  human_ownership:'NOT_VERIFIED',permission_to_publish:false,external_signer_authenticated:false
 }};
}
function block(s){
 const tick=String.fromCharCode(96);
 const runs=s.match(new RegExp(tick+'+','g'))||[];
 const fence=tick.repeat(Math.max(3,...runs.map(x=>x.length+1)));
 return fence+'text\n'+s+'\n'+fence;
}
function title(s){return s.replace(/[\r\n]+/g,' ').replace(/[<>\\[\]#*!_]/g,' ').split(String.fromCharCode(96)).join(' ').slice(0,100);}
export function composeReadingCandidate(inspected){
 const {packet:p,verification:v}=inspected||{};
 ok(p&&v&&v.packet_self_checksum==='MATCHES_UNSIGNED_PACKET'&&v.permission_to_publish===false,'CANDIDATE_INSPECTION_REQUIRED');
 const id='lp-goatnote-candidate:'+p.checksum.slice(7),s=p.source,m=p.reading,e=p.relation;
 const lines=['# Reading-edition candidate — '+title(s.title),'',
  '**PRIVATE EDITORIAL CANDIDATE. NOT A RELEASE OR HOUSE ADMISSION.**','',
  '## The selected particular','',
  'Frozen GOATnote source version: '+s.version_id,
  'Selected quote (excerpt digest independently checked):','',block(s.excerpt),'',
  '## A later margin','','Kind: '+m.kind,'Recorded at: '+m.recorded_at,
  'Human reading (not original-source testimony):','',block(m.text),'','## Relationship in time',''];
 if(e)lines.push('Human relation first perceived: '+e.first_perceived_at,
  'Relation status at selection: '+e.recorded_current_status,
  'Declared relation type: '+title(e.relation_type),
  'Discovery declaration:','',block(e.discovery_trace),'',
  'Evidence-path declaration:','',block(e.evidence_path),'',
  'This is a dated human relation, NOT a source-event timestamp or publication grant.');
 else lines.push('No GOATedge relation was selected for disclosure.');
 lines.push('','## Source and publication boundaries','',
  'Exact note-version SHA-256 (declared, body omitted): '+s.version_sha256,
  'Exact selected excerpt SHA-256: '+s.excerpt_sha256,
  'Selection recorded: '+p.selection.selected_at,
  'A version identity is NOT independently reproducible from this excerpt.',
  'Marginalia is NOT an edit or correction of the original source.',
  'LemonPRESS candidate is NOT house selection, admission, licensing, edition or release.',
  'This material remains private until separate rights review and explicit editorial action.','');
 const manuscript=lines.join('\n');
 const candidate={schema:CANDIDATE_SCHEMA,id,state:'PRIVATE_CANDIDATE',
  work_admitted:false,edition_admitted:false,publication_authorized:false,
  rights_granted:false,editorial_selected:false,
  source:{origin_schema:p.schema,origin_packet_checksum:p.checksum,
   source_version_sha256:s.version_sha256,source_version_bytes_present:false,
   selected_excerpt_sha256:s.excerpt_sha256,quote_verified:true,
   original_version_verified:false},
  chronology:{source_version_time:'NOT_ASSERTED',margin_recorded_at:m.recorded_at,
   relation_first_perceived_at:e?.first_perceived_at||null,press_selection_at:p.selection.selected_at},
  authority:v,manuscript_sha256:sha(manuscript),
  warnings:['PRIVATE_NOT_FOR_PUBLIC_CATALOG','NO_RIGHTS_OR_OWNER_AUTHENTICATION',
   'NO_VERIFICATION_OF_OMITTED_FULL_SOURCE']};
 return {candidate,manuscript};
}
export async function composeLocal(raw,outdir){
 ok(typeof outdir==='string'&&outdir.length>0,'OUTPUT_DIRECTORY_REQUIRED');
 const {candidate,manuscript}=composeReadingCandidate(inspectSelectedMargin(raw));
 ok(!existsSync(outdir),'CREATE_ONLY_OUTPUT_EXISTS');
 await mkdir(outdir,{recursive:false});
 await writeFile(join(outdir,'candidate.md'),manuscript,{flag:'wx',mode:0o600});
 await writeFile(join(outdir,'candidate.json'),JSON.stringify(candidate,null,2)+'\n',{flag:'wx',mode:0o600});
 return {id:candidate.id,outdir,state:candidate.state,files:['candidate.md','candidate.json']};
}
