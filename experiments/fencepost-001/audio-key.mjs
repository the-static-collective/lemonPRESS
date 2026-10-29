#!/usr/bin/env node
// FENCEPOST-005: a public audio capsule identifies a verified *proposal*, not an execution grant.
// Versioned overt intro/outro FSK. No hidden continuous watermark and no device control.
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {encode as encodeFsk,decode as decodeFsk,toBits,RATE,SAMPLES_PER_BIT} from './groovevault.mjs';
import {encodePcm16,decodePcm16} from './fencepost.mjs';

const MAGIC='GKC1', ROOT='fencepost/audio-capsule-manifest/v1';
const READONLY_VERBS=new Set(['open','preview','inspect','propose']);
const WORLDS=new Set(['revival','reality2','creature-world','cannon','toaster','lemonpress']);
const GAP_SAMPLES=Math.round(RATE*.15);
const FSK_BYTES=4+32;
const MARKER_SAMPLES=2400+(96+(FSK_BYTES+10)*14)*SAMPLES_PER_BIT;
const sha=b=>'sha256:'+createHash('sha256').update(b).digest('hex');
const hash=b=>createHash('sha256').update(b).digest();
const json=o=>JSON.stringify(o,null,2)+'\n';
const hold=(ok,code)=>{if(!ok)throw Error('AUDIO_KEY_HOLD_'+code);};
const keys=(value,accepted)=>Object.keys(value).sort().join('|')===accepted.slice().sort().join('|');
const validText=s=>typeof s==='string' && s.length>0 && s.length<=100 && /^[\w .:/-]+$/.test(s);
const validResourceKey=s=>typeof s==='string' && /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(s);
function assertMaster(buf){
  hold(Buffer.isBuffer(buf)&&buf.length>=46&&buf.length<30000000,'MASTER_SIZE');
  const d=decodePcm16(buf);
  hold(d.sampleRate===RATE && d.channels===1 && buf.length===44+d.samples.length*2,'CANONICAL_MONO_48K');
  hold(buf.toString('ascii',0,4)==='RIFF' && buf.toString('ascii',36,40)==='data' &&
       buf.readUInt32LE(40)===(buf.length-44),'CANONICAL_RIFF');
  return d;
}
function waveWithPayload(payload){
  hold(payload.length/2 < 30000000,'WAVE_CAP');
  const out=encodePcm16(new Float64Array(1),RATE).subarray(0,44);
  out.writeUInt32LE(36+payload.length,4);out.writeUInt32LE(payload.length,40);
  return Buffer.concat([out,payload]);
}
function manifestCheck(m){
  hold(m && typeof m==='object' && !Array.isArray(m) &&
    keys(m,['schema','workId','sourcePcmSha256','doors','rightsState']),'MANIFEST_SHAPE');
  hold(m.schema===ROOT && validText(m.workId) && /^sha256:[a-f0-9]{64}$/.test(m.sourcePcmSha256),'MANIFEST_HEADER');
  hold(['OWNER_DECLARED_NOT_VERIFIED','RIGHTS_HELD'].includes(m.rightsState),'RIGHTS_STATE');
  hold(Array.isArray(m.doors) && m.doors.length>0 && m.doors.length<=12,'DOORS');
  const seen=new Set();
  for(const d of m.doors){
    hold(d&&typeof d==='object'&&!Array.isArray(d)&&
      keys(d,['world','verb','resourceKey'])&&WORLDS.has(d.world) &&
      READONLY_VERBS.has(d.verb) && validResourceKey(d.resourceKey),'DOOR_SCHEMA');
    const identity=d.world+'/'+d.verb+'/'+d.resourceKey;
    hold(!seen.has(identity),'DUPLICATE_DOOR'); seen.add(identity);
  }
  return m;
}
export function canonicalManifest(obj){
  const m=manifestCheck(obj);
  // Explicit canonical projection, independent of the order of incoming JSON keys.
  const normalized={
    schema:m.schema,workId:m.workId,sourcePcmSha256:m.sourcePcmSha256,
    rightsState:m.rightsState,doors:m.doors.map(d=>({
      world:d.world,verb:d.verb,resourceKey:d.resourceKey}))};
  return Buffer.from(json(normalized));
}
export function publicId(manifest){return sha(canonicalManifest(manifest));}
function markerBytes(id){
  hold(/^sha256:[a-f0-9]{64}$/.test(id),'IDENTITY');
  return Buffer.concat([Buffer.from(MAGIC),Buffer.from(id.slice(7),'hex')]);
}
function markerToId(buffer){
  const result=decodeFsk(buffer);
  const payload=result.payload;
  hold(payload.length===FSK_BYTES && payload.subarray(0,4).toString('ascii')===MAGIC,'NOT_CAPSULE');
  return {id:'sha256:'+payload.subarray(4).toString('hex'),
    corrections:result.corrections,leaderErrors:result.leaderErrors};
}
function splitCap(wav){
  assertMaster(wav);
  const whole=wav.subarray(44);
  const markerBytesLen=MARKER_SAMPLES*2;
  hold(whole.length >= markerBytesLen*2+GAP_SAMPLES*4+2,'CAPSULE_DURATION');
  const front=whole.subarray(0,markerBytesLen);
  const back=whole.subarray(whole.length-markerBytesLen);
  const body=whole.subarray(markerBytesLen+2*GAP_SAMPLES,whole.length-markerBytesLen-2*GAP_SAMPLES);
  return {front:waveWithPayload(front),back:waveWithPayload(back),body};
}
export function assemble(master,manifest){
  assertMaster(master);
  const originalPcm=master.subarray(44);
  const m=manifestCheck(manifest);
  hold(sha(originalPcm)===m.sourcePcmSha256,'SOURCE_PCM_HASH');
  const id=publicId(m);
  const marker=encodeFsk(markerBytes(id));
  hold((marker.length-44)===MARKER_SAMPLES*2,'MARKER_LAYOUT');
  const gap=Buffer.alloc(GAP_SAMPLES*2), pcm=Buffer.concat([
    marker.subarray(44),gap,gap,originalPcm,gap,gap,marker.subarray(44)
  ]);
  return {capsuleWav:waveWithPayload(pcm), id,
    sourcePcmSha256:sha(originalPcm),markerDurationSeconds:MARKER_SAMPLES/RATE,
    sourceSeconds:originalPcm.length/2/RATE};
}
export function scanCapsule(wav,manifestIndex={}){
  const s=splitCap(wav);
  const front=markerToId(s.front),back=markerToId(s.back);
  hold(front.id===back.id,'MARKERS_DISAGREE');
  const id=front.id;
  const manifest=manifestIndex[id]??null;
  if(manifest!==null){
    hold(publicId(manifest)===id,'MANIFEST_ID_MISMATCH');
    hold(sha(s.body)===manifest.sourcePcmSha256,'SOURCE_AUDIO_MISMATCH');
  }
  const proposals=manifest?manifest.doors.map(d=>({
    ...d,decision:'HOLD_FOR_EXPLICIT_LOCAL_USER_ACTION',
    executed:false,sourceAuthenticity:'NOT_ESTABLISHED_BY_HASH',
    receiverAuthority:'NOT_ESTABLISHED'
  })):[];
  return {schema:'fencepost/audio-key-scan/v1',publicId:id,
    markersAgree:true,markerErrorCorrections:front.corrections+back.corrections,
    sourcePcmSha256:sha(s.body),sourcePcmVerifiedToManifest:manifest!==null,
    hasKnownManifest:manifest!==null,manifestRightsState:manifest?.rightsState??null,
    manifestSignatureStatus:'UNVERIFIED_NO_TRUST_ANCHOR',
    routeProposals:proposals,
    acceptedActions:0,automaticExecutions:0,
    qualification:'EXACT_DIGITAL_WAV_LAYOUT_ONLY_NO_PHYSICAL_ANALOG_RELIABILITY'};
}
export function createDemoManifest(master){
  const d=assertMaster(master);
  return {
    schema:ROOT,workId:'demo/the-fence-that-sang',sourcePcmSha256:sha(master.subarray(44)),
    rightsState:'OWNER_DECLARED_NOT_VERIFIED',
    doors:[
      {world:'revival',verb:'open',resourceKey:'genesis-1-1-demo'},
      {world:'reality2',verb:'preview',resourceKey:'waseca-room-demo'},
      {world:'creature-world',verb:'propose',resourceKey:'starter-creature-demo'},
      {world:'cannon',verb:'inspect',resourceKey:'candidate-receipt-demo'},
      {world:'toaster',verb:'preview',resourceKey:'visualscore-demo'}
    ]
  };
}
export function buildBundle(master,m){
  const made=assemble(master,m);
  const manifestBytes=canonicalManifest(m),index={ [made.id]: JSON.parse(manifestBytes.toString('utf8'))};
  const scan=scanCapsule(made.capsuleWav,index);
  const files={
    'audio-capsule.wav':made.capsuleWav,
    'manifest.json':manifestBytes,
    'scan-proposals.json':json(scan)
  };
  const receiptBody={
    schema:'fencepost/audio-key-receipt/v1',state:'DIGITAL_CAPSULE_ONLY',
    publicId:made.id,physicalRecords:0,executedCode:0,receiverGrants:0,
    fileHashes:Object.fromEntries(Object.entries(files).map(([k,v])=>[k,sha(v)]))
  };
  files['receipt.json']=json({...receiptBody,receiptId:sha(json(receiptBody))});
  return files;
}
export function verifyBundle(dir){
  const p=resolve(dir),receipt=JSON.parse(readFileSync(join(p,'receipt.json'),'utf8'));
  hold(receipt.schema==='fencepost/audio-key-receipt/v1'&&
       receipt.state==='DIGITAL_CAPSULE_ONLY'&&receipt.physicalRecords===0 &&
       receipt.executedCode===0&&receipt.receiverGrants===0,'RECEIPT_STATE');
  const {receiptId,...body}=receipt;
  hold(sha(json(body))===receiptId,'RECEIPT_TAMPER');
  const expect=[...Object.keys(receipt.fileHashes),'receipt.json'].sort();
  hold(readdirSync(p).sort().join('|')===expect.join('|'),'UNEXPECTED_FILE');
  for(const [name,digest] of Object.entries(receipt.fileHashes)){
    hold(['audio-capsule.wav','manifest.json','scan-proposals.json'].includes(name),'RECEIPT_FILE');
    hold(sha(readFileSync(join(p,name)))===digest,'TAMPER_'+name);
  }
  const manifest=JSON.parse(readFileSync(join(p,'manifest.json'),'utf8'));
  const scanned=scanCapsule(readFileSync(join(p,'audio-capsule.wav')),
    {[receipt.publicId]:manifest});
  hold(JSON.stringify(scanned)===JSON.stringify(JSON.parse(readFileSync(join(p,'scan-proposals.json')),'utf8')),'SCAN_INCONSISTENT');
  return {status:'DIGITAL_AUDIO_CAPSULE_COLD_REPLAY_VERIFIED',publicId:receipt.publicId,
    proposedDoors:scanned.routeProposals.length,executedCode:0,physicalRecords:0};
}
function writeBundle(files,out){
  const p=resolve(out);
  hold(!existsSync(p),'OUTPUT_EXISTS');mkdirSync(p,{recursive:true});
  for(const [name,value] of Object.entries(files))writeFileSync(join(p,name),value,{flag:'wx'});
  return verifyBundle(p);
}
function help(){
  return ['AUDIO KEY-005 (OFFLINE ONLY) — sound as a public pointer, never a bearer authorization',
    'node audio-key.mjs demo OUTPUT_DIR',
    'node audio-key.mjs build MASTER_48K_MONO_PCM16_WAV MANIFEST_JSON OUTPUT_DIR',
    'node audio-key.mjs scan CAPSULE_WAV [MANIFEST_JSON]',
    'node audio-key.mjs verify OUTPUT_DIR'].join('\n');
}
if(process.argv[1]&&resolve(process.argv[1])===new URL(import.meta.url).pathname){
  try{
    const [,,cmd,...a]=process.argv;
    if(cmd==='demo'&&a.length===1){
      const n=RATE*2, wave=new Float64Array(n);
      for(let i=0;i<n;i++)wave[i]=0.13*Math.sin(2*Math.PI*220*i/RATE);
      const source=encodePcm16(wave,RATE);
      console.log(JSON.stringify(writeBundle(buildBundle(source,createDemoManifest(source)),a[0])));
    }else if(cmd==='build'&&a.length===3){
      console.log(JSON.stringify(writeBundle(buildBundle(readFileSync(a[0]),JSON.parse(readFileSync(a[1],'utf8'))),a[2])));
    }else if(cmd==='scan'&&(a.length===1||a.length===2)){
      const manifest=a[1]?JSON.parse(readFileSync(a[1],'utf8')):null;
      const index=manifest?{[publicId(manifest)]:manifest}:{};
      console.log(json(scanCapsule(readFileSync(a[0]),index)));
    }else if(cmd==='verify'&&a.length===1){
      console.log(JSON.stringify(verifyBundle(a[0])));
    }else{console.log(help());if(cmd!=='help'&&cmd!=='--help')process.exitCode=2;}
  }catch(e){console.error(e.message);process.exitCode=2;}
}
