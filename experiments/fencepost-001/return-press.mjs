#!/usr/bin/env node
// RETURN PRESS 006: history -> different synthetic digital compositions.
// Never manufactures records, retrieves lived history, or runs world actions.
import {createHash} from 'node:crypto';
import {mkdirSync,existsSync,readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {encodePcm16} from './fencepost.mjs';
import {assemble,publicId,scanCapsule} from './audio-key.mjs';

const RATE=48000, BPM=92, LENGTH=Math.floor((4*3*60/BPM)*RATE);
const EVENT='fencepost/return-event/v1', LINEAGE='fencepost/return-lineage/v1';
const MOTIFS=new Set(['bells','sub','shimmer','echo']);
const sha=b=>'sha256:'+createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
const hold=(x,code)=>{if(!x)throw Error('RETURN_PRESS_HOLD_'+code);};
const token=s=>typeof s==='string'&&/^[a-z0-9][a-z0-9-]{0,63}$/.test(s);
const clamp=n=>Math.min(1,Math.max(-1,n));
const eventHash=e=>{const {hash,...body}=e;return sha(json(body));};
export function appendEvent(log,{type,actor,payload}){
  hold(Array.isArray(log)&&token(actor),'EVENT');
  const e={schema:EVENT,seq:log.length+1,previous:log.length?log.at(-1).hash:'ROOT',
    origin:'SYNTHETIC_FIXTURE',type,actor,payload};
  return [...log,{...e,hash:eventHash(e)}];
}
function validateEvent(e){
  const p=e.payload;
  hold(p&&typeof p==='object'&&!Array.isArray(p),'PAYLOAD');
  switch(e.type){
    case 'listen':
      hold(p.optIn===true&&token(p.session),'LISTEN_CONSENT');break;
    case 'visit':
      hold(p.optIn===true&&['revival','reality2','creature-world','toaster'].includes(p.world)
        &&token(p.room),'WORLD_CONSENT');break;
    case 'propose':
      hold(token(p.id)&&MOTIFS.has(p.motif)&&p.authorConsent===true&&
        p.license==='DEMO_REMIX_ONLY','PROPOSAL_RIGHTS');break;
    case 'accept':
      hold(token(p.id)&&p.scope==='DEMO_REMIX_ONLY'&&p.review==='SYNTHETIC_REVIEW',
        'ACCEPT_REVIEW');break;
    case 'refuse':
      hold(token(p.id)&&p.reason==='AUTHOR_WITHDRAWAL','REFUSAL');break;
    default:throw Error('RETURN_PRESS_HOLD_TYPE');
  }
}
export function replay(log,cut=log.length){
  hold(Array.isArray(log)&&Number.isInteger(cut)&&cut>=0&&cut<=log.length,'CUT');
  const proposals=new Map(),accepted=new Map(),refused=new Set();
  let previous='ROOT',listens=0,visits=0;
  for(let i=0;i<log.length;i++){
    const e=log[i];
    hold(e&&e.schema===EVENT&&e.seq===i+1&&e.previous===previous&&
      e.hash===eventHash(e)&&e.origin==='SYNTHETIC_FIXTURE'&&token(e.actor),'CHAIN');
    validateEvent(e);previous=e.hash;
    if(i>=cut)continue;
    const p=e.payload;
    if(e.type==='listen')listens++;
    if(e.type==='visit')visits++;
    if(e.type==='propose'){
      hold(!proposals.has(p.id),'DUPLICATE');
      proposals.set(p.id,{...p,by:e.actor});}
    if(e.type==='accept'){
      const proposal=proposals.get(p.id);
      hold(proposal&&proposal.by!==e.actor&&!refused.has(p.id)&&
        !accepted.has(p.id),'INVALID_ACCEPT');
      accepted.set(p.id,{...proposal,approvedBy:e.actor,acceptedAt:e.seq});
    }
    if(e.type==='refuse'){
      const proposal=proposals.get(p.id);
      hold(proposal&&(e.actor===proposal.by||e.actor===accepted.get(p.id)?.approvedBy),
        'INVALID_REFUSAL');
      refused.add(p.id);accepted.delete(p.id);
    }
  }
  return {cut,cutHash:cut?log[cut-1].hash:'ROOT',listens,visits,
    proposals:proposals.size,refusals:refused.size,
    accepted:[...accepted.values()].sort((a,b)=>a.acceptedAt-b.acceptedAt)};
}
function note(s,start,duration,freq,volume,kind='bell'){
  const from=Math.floor(start*RATE),end=Math.min(s.length,Math.floor((start+duration)*RATE));
  for(let i=Math.max(0,from);i<end;i++){
    const t=i/RATE-start,env=Math.min(1,t/.018)*Math.exp(-3*t/duration);
    const bass=Math.sin(2*Math.PI*freq*t);
    const wave=kind==='sub'?bass+.08*Math.sin(4*Math.PI*freq*t):
      kind==='shimmer'?.7*bass+.2*Math.sin(4.02*Math.PI*freq*t):
      kind==='echo'?bass*Math.sin(5*Math.PI*t):
      .8*bass+.2*Math.sin(4*Math.PI*freq*t);
    s[i]+=volume*env*wave;
  }
}
export function render(snapshot){
  hold(Array.isArray(snapshot?.accepted),'SNAPSHOT');
  const s=new Float64Array(LENGTH),beat=60/BPM,bar=beat*3;
  const roots=[196,174.614,155.563,174.614];
  for(let b=0;b<4;b++){
    note(s,b*bar,bar*.95,roots[b]/2,.15,'sub');
    for(let k=0;k<6;k++)note(s,b*bar+k*beat/2,beat*.4,
      roots[b]*[1,1.5,2,1.5,1.25,1.5][k],.11);
  }
  const frequencies={bells:[440,523.25,659.25,783.99],sub:[55,65.41,73.42,82.41],
    shimmer:[392,493.88,587.33,739.99],echo:[261.63,293.66,329.63,392]};
  for(const m of snapshot.accepted){
    const salt=[...m.id].reduce((x,c)=>x+c.charCodeAt(0),0)%4,tones=frequencies[m.motif];
    for(let b=0;b<4;b++){
      if(m.motif==='sub')note(s,b*bar,bar*.85,tones[(b+salt)%4],.24,'sub');
      else if(m.motif==='echo')note(s,b*bar+beat*.25,beat*1.5,
        tones[(b+salt)%4],.18,'echo');
      else for(let k=0;k<3;k++)note(s,b*bar+beat*(k+.4),beat*.62,
        tones[(b+k+salt)%4],m.motif==='shimmer'?.12:.19,m.motif);
    }
  }
  for(let i=0;i<s.length;i++)s[i]=clamp(s[i]*.76);
  return encodePcm16(s,RATE);
}
export function demoJournal(){
  const cases=[
    ['listen','listener-a',{session:'first-play',optIn:true}],
    ['propose','composer-a',{id:'glass-a',motif:'bells',authorConsent:true,license:'DEMO_REMIX_ONLY'}],
    ['visit','visitor-a',{world:'revival',room:'genesis-demo',optIn:true}],
    ['accept','curator-a',{id:'glass-a',scope:'DEMO_REMIX_ONLY',review:'SYNTHETIC_REVIEW'}],
    ['propose','composer-b',{id:'sub-a',motif:'sub',authorConsent:true,license:'DEMO_REMIX_ONLY'}],
    ['accept','curator-b',{id:'sub-a',scope:'DEMO_REMIX_ONLY',review:'SYNTHETIC_REVIEW'}],
    ['listen','listener-b',{session:'second-play',optIn:true}],
    ['refuse','composer-b',{id:'sub-a',reason:'AUTHOR_WITHDRAWAL'}],
    ['propose','composer-c',{id:'echo-a',motif:'echo',authorConsent:true,license:'DEMO_REMIX_ONLY'}],
    ['accept','curator-c',{id:'echo-a',scope:'DEMO_REMIX_ONLY',review:'SYNTHETIC_REVIEW'}],
    ['visit','visitor-b',{world:'creature-world',room:'ghost-demo',optIn:true}]
  ];
  let result=[];
  for(const [type,actor,payload] of cases)result=appendEvent(result,{type,actor,payload});
  return result;
}
function motifList(snapshot){
  return snapshot.accepted.map(x=>({id:x.id,motif:x.motif,by:x.by,approvedBy:x.approvedBy}));
}
export function compile(log,{earlyCut=4,lateCut=log.length}={}){
  hold(earlyCut>0&&earlyCut<lateCut&&lateCut<=log.length,'CUT_ORDER');
  const early=replay(log,earlyCut),late=replay(log,lateCut);
  hold(early.accepted.length&&late.accepted.length,'MOTIF_REQUIRED');
  const source=render({accepted:[]}),first=render(early),second=render(late);
  hold(sha(first)!==sha(second),'NOT_A_NEW_REMIX');
  const masterHash=sha(second.subarray(44));
  const manifest={schema:'fencepost/audio-capsule-manifest/v1',workId:'demo/return-press-006',
    sourcePcmSha256:masterHash,rightsState:'OWNER_DECLARED_NOT_VERIFIED',
    doors:[{world:'cannon',verb:'inspect',resourceKey:'return-press-demo'},
      {world:'toaster',verb:'preview',resourceKey:'remix-visualscore-demo'},
      {world:'revival',verb:'open',resourceKey:'genesis-1-1-demo'}]};
  const capsule=assemble(second,manifest),id=publicId(manifest);
  hold(capsule.id===id&&scanCapsule(capsule.capsuleWav,{[id]:manifest}).sourcePcmVerifiedToManifest,
    'CAPSULE');
  const journal=json({schema:'fencepost/return-journal/v1',state:'SYNTHETIC_ONLY',events:log});
  const lineage={schema:LINEAGE,status:'DRAFT_NEVER_PRESSED',
    source:{kind:'SYNTHETIC_GENERATED_6_8',wavSha256:sha(source),journalSha256:sha(journal)},
    early:{cut:early.cut,cutHash:early.cutHash,wavSha256:sha(first),motifs:motifList(early),
      listenReports:early.listens,visitReports:early.visits},
    late:{cut:late.cut,cutHash:late.cutHash,wavSha256:sha(second),motifs:motifList(late),
      listenReports:late.listens,visitReports:late.visits,audioCapsuleId:id},
    boundaries:{consentedFixtureOnly:true,physicalRecords:0,publicReleaseAuthorized:false,
      rightsFromRealAuthorsGranted:false,realWorldVisitsVerified:false},
    proposedDoors:{bandRuntime:'HISTORY_IMPORT_NOT_CONNECTED',tranchNode:'LINEAGE_NOT_CONNECTED',
      planZ:'HUMAN_REVIEW_NOT_CONNECTED',staticLive:'NO_LIVE_PERFORMANCE',
      hauntedToaster:'VISUALSCORE_NOT_RENDERED',cannon:'NOT_SELECTED',
      lemonpress:'NOT_ADMITTED'}};
  const label='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img" aria-label="Draft return record label; not press ready"><circle cx="300" cy="300" r="285" fill="#21372e"/><circle cx="300" cy="300" r="175" fill="#d4b787"/><circle cx="300" cy="300" r="7" fill="#21372e"/><g font-family="monospace" text-anchor="middle" fill="#21372e"><text x="300" y="220" font-size="22">RETURN PRESS 006</text><text x="300" y="270" font-size="23">THE HISTORY BLOOMS</text><text x="300" y="394" font-size="16">THE SOURCE SURVIVES</text></g><text x="300" y="546" font-size="15" font-family="monospace" text-anchor="middle" fill="#f4efe1">DRAFT / NOT FOR MANUFACTURE</text></svg>\n';
  const files={'synthetic-source.wav':source,'remix-early.wav':first,'remix-late.wav':second,
    'remix-late-capsule.wav':capsule.capsuleWav,'remix-late-manifest.json':json(manifest),
    'history-journal.json':journal,'lineage.json':json(lineage),'center-label-draft.svg':label};
  const receipt={schema:'fencepost/return-receipt/v1',state:'DIGITAL_SYNTHETIC_ONLY',physicalRecords:0,
    liveWorldCalls:0,files:Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,sha(v)]))};
  files['receipt.json']=json({...receipt,receiptId:sha(json(receipt))});
  return files;
}
export function verify(folder){
  const dir=resolve(folder),r=JSON.parse(readFileSync(join(dir,'receipt.json'),'utf8'));
  hold(r.schema==='fencepost/return-receipt/v1'&&r.physicalRecords===0&&
    r.liveWorldCalls===0&&r.state==='DIGITAL_SYNTHETIC_ONLY','RECEIPT');
  const {receiptId,...body}=r;
  hold(sha(json(body))===receiptId,'RECEIPT_HASH');
  hold([...Object.keys(r.files),'receipt.json'].sort().join('|')===readdirSync(dir).sort().join('|'),
    'FILES');
  for(const [name,hash] of Object.entries(r.files)){
    hold(/^[a-z0-9-]+\.(wav|json|svg)$/.test(name),'FILE_PATH');
    hold(sha(readFileSync(join(dir,name)))===hash,'TAMPER_'+name);
  }
  const journal=JSON.parse(readFileSync(join(dir,'history-journal.json'),'utf8'));
  hold(journal.state==='SYNTHETIC_ONLY','JOURNAL');
  replay(journal.events);
  const l=JSON.parse(readFileSync(join(dir,'lineage.json'),'utf8'));
  hold(l.source.journalSha256===sha(readFileSync(join(dir,'history-journal.json'))),'JOURNAL_HASH');
  hold(l.early.wavSha256===sha(readFileSync(join(dir,'remix-early.wav'))) &&
    l.late.wavSha256===sha(readFileSync(join(dir,'remix-late.wav'))),'MUSIC_HASH');
  const m=JSON.parse(readFileSync(join(dir,'remix-late-manifest.json'),'utf8'));
  const scan=scanCapsule(readFileSync(join(dir,'remix-late-capsule.wav')),
    {[l.late.audioCapsuleId]:m});
  hold(scan.sourcePcmVerifiedToManifest&&scan.publicId===l.late.audioCapsuleId,'AUDIO_CAPSULE');
  return {status:'RETURN_PRESS_COLD_REPLAY_VERIFIED',earlyCut:l.early.cut,lateCut:l.late.cut,
    earlyMotifs:l.early.motifs.length,lateMotifs:l.late.motifs.length,
    lateAudioKey:scan.publicId,physicalRecords:0};
}
export function write(files,dest){
  const dir=resolve(dest);hold(!existsSync(dir),'OUTPUT_EXISTS');
  mkdirSync(dir,{recursive:true});
  for(const [name,data] of Object.entries(files))writeFileSync(join(dir,name),data,{flag:'wx'});
  return verify(dir);
}
if(process.argv[1]&&resolve(process.argv[1])===new URL(import.meta.url).pathname){
  try{
    const [,,cmd,...args]=process.argv;
    if(cmd==='demo'&&args.length===1)console.log(JSON.stringify(write(compile(demoJournal()),args[0])));
    else if(cmd==='verify'&&args.length===1)console.log(JSON.stringify(verify(args[0])));
    else if(cmd==='compile'&&args.length===2){
      const log=JSON.parse(readFileSync(args[0],'utf8'));
      hold(log.schema==='fencepost/return-journal/v1'&&log.state==='SYNTHETIC_ONLY',
        'JOURNAL_FORMAT');
      console.log(JSON.stringify(write(compile(log.events),args[1])));
    }else{
      console.log('RETURN PRESS: demo OUTPUT_DIR | compile SYNTHETIC_JOURNAL_JSON OUTPUT_DIR | verify OUTPUT_DIR');
      if(cmd!=='help'&&cmd!=='--help')process.exitCode=2;
    }
  }catch(e){console.error(e.message);process.exitCode=2;}
}
