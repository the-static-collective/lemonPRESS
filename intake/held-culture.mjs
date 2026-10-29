/** lemonPRESS CULTURE RECEIVER 002 — true, independently governed HOLD/REFUSE.
 * Source receipts are not signatures; a successful bytes check grants no publication right.
 * This is an experimental admission candidate outside the house catalog.
 */
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync,existsSync,realpathSync} from 'node:fs';
import {resolve,join} from 'node:path';
const SHA=/^sha256:[a-f0-9]{64}$/;
const fail=(p,m)=>{if(!p)throw Error(m);};
const sha=x=>'sha256:'+createHash('sha256').update(x).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
const isObj=x=>!!x&&typeof x==='object'&&!Array.isArray(x);
const exact=(x,fields)=>isObj(x)&&Object.keys(x).sort().join()===fields.slice().sort().join();
const FILES=['comic.html','field-card.md'];
export const HELD_SCHEMA='lemonpress/held-culture-candidate/v1';
export const RECEIPT_SCHEMA='lemonpress/independent-intake-receipt/v1';
function limited(dir,name){
 fail(typeof dir==='string','DIRECTORY_REQUIRED');
 const root=realpathSync(resolve(dir)),file=join(root,name);
 fail(realpathSync(file)===file,'SYMLINK_OR_PATH_MISMATCH');
 const bytes=readFileSync(file);
 fail(bytes.length>0&&bytes.length<256*1024,'SOURCE_BYTES_UNSAFE');
 return bytes;
}
function readInputs(sourceDir){
 const comic=limited(sourceDir,FILES[0]),card=limited(sourceDir,FILES[1]);
 const rawReceipt=limited(sourceDir,'receipt.json'),rawRequest=limited(sourceDir,'request.json');
 const receipt=JSON.parse(rawReceipt.toString('utf8')),request=JSON.parse(rawRequest.toString('utf8'));
 fail(exact(request,['topic'])&&typeof request.topic==='string'&&request.topic.length>0&&request.topic.length<=240,'REQUEST_INVALID');
 fail(isObj(receipt)&&receipt.schema==='cannon.culture-forge-receipt/v1','CANNON_RECEIPT_UNKNOWN');
 fail(typeof receipt.topic==='string'&&receipt.topic===request.topic,'REQUEST_RECEIPT_MISMATCH');
 fail(SHA.test(receipt.receiptSha256),'RECEIPT_HASH_INVALID');
 const {receiptSha256,...body}=receipt;
 fail(sha(Buffer.from(JSON.stringify(body)))===receiptSha256,'CANNON_RECEIPT_CHANGED');
 fail(exact(receipt.outputs,FILES),'SOURCE_OUTPUT_LIST_INVALID');
 for(const [file,buf] of [[FILES[0],comic],[FILES[1],card]])
   fail(receipt.outputs[file]===sha(buf),'SOURCE_FILE_CHANGED_'+file);
 fail(receipt.status==='SOURCE_PINNED_NATIVE_EXECUTION_LOCAL_ARTIFACT_ONLY','SOURCE_STATUS_ESCALATED');
 fail(receipt.sourceSelection==='EXPLICIT_COMMIT_PINS_NOT_CANON','SOURCE_CANON_ESCALATED');
 fail(receipt.executable?.sourceReposModified===false,'SOURCE_MODIFICATION_CLAIMED');
 fail(receipt.nativeResults?.webz?.schema==='abundent.matter-idea-craft/v1','WEBZ_LINEAGE_MISSING');
 fail(receipt.nativeResults?.gro?.schema==='gro.mattercraft-field-projection/v0','GRO_LINEAGE_MISSING');
 fail(receipt.nativeResults?.gro?.discrepancy==='COUNTS_DISAGREE_HOLD','GRo_MISMATCH_LOST');
 const flags=['canonSelected','rightsAuthenticated','ownerIdentityAuthenticated',
 'liveStewardApproved','sourceCopyrightGranted','reLATTEReceived','externalSettlement'];
 fail(flags.every(f=>receipt.grants?.[f]===false),'SOURCE_AUTHORITY_ESCALATED');
 const effects=['realInventoryChange','fullMeasureDeeds','pennyIssued','marketTokensMinted',
 'payments','thirdPartyMessages'];
 fail(effects.every(f=>receipt.effects?.[f]===0)&&receipt.effects?.publicRelease===false,'SOURCE_EFFECT_ESCALATED');
 fail(/<!doctype html>/i.test(comic.toString('utf8')),'HTML_CARRIER_MISSING');
 fail(!/<script\b|<iframe\b|<object\b|\son[a-z]+\s*=/i.test(comic.toString('utf8')),'ACTIVE_HTML_REFUSED');
 fail(card.toString('utf8').includes(receipt.topic),'FIELD_CARD_TOPIC_MISMATCH');
 return {comic,card,receipt,request};
}
export function inspect(sourceDir,choice='HOLD'){
 fail(choice==='HOLD'||choice==='REFUSE','UNSUPPORTED_INTAKE_DISPOSITION');
 const data=readInputs(sourceDir);
 const fingerprint=sha(Buffer.from(data.receipt.receiptSha256+'\n'+sha(data.comic)+'\n'+sha(data.card)));
 const candidate={
  schema:HELD_SCHEMA,identity:fingerprint,decision:choice==='HOLD'?'HELD_FOR_EDITOR':'REFUSED_BY_RECEIVER',
  question:data.request.topic,creatorIdentity:'NOT_AUTHENTICATED',
  inputProvenance:{cannonReceipt:data.receipt.receiptSha256,
   originalGitWitnessCount:Object.values(data.receipt.sources||{}).flat().length,
   sourceVerification:'CANNON_CLAIM_WITH_HASH_CHECK_NOT_REMOTE_OWNER_AUTHENTICATION'},
  works:[{path:'comic.html',sha256:sha(data.comic),mediaType:'text/html',kind:'SIX_PANEL_COMIC'},
   {path:'field-card.md',sha256:sha(data.card),mediaType:'text/markdown',kind:'FIELD_GUIDE'}],
  rights:'UNREVIEWED_NOT_TRANSFERRED',workAdmission:'NONE',
  editionAdmission:'NONE',catalogRegistered:false,published:false,externalDispatched:false,
  license:'NOT_GRANTED',commercialUse:'NOT_GRANTED',
  authority:'RECEIVER_LOCAL_CANDIDATE_NOT_A_HOUSE_RELEASE',
  nextHumanGate:choice==='HOLD'?'SEPARATE_AUTHENTICATED_EDITORIAL_AND_RIGHTS_REVIEW':'NEW_INDEPENDENT_SUBMISSION_REQUIRED',
  nonClaims:['FILE_INTAKE_NOT_PUBLICATION','NO_LEMONPRESS_HOUSE_ID_GRANTED',
   'SIGNED_OR_HASHED_SOURCE_NOT_CREATOR_RIGHTS','NO_PENNY_OR_FULL_MEASURE_OR_NFT_EFFECT']
 };
 const receiptBody={
  schema:RECEIPT_SCHEMA,source:candidate.identity,sourceReceipt:data.receipt.receiptSha256,
  disposition:candidate.decision,artifacts:candidate.works,
  admission:false,publication:false,financialEffects:0,receiverRole:'INDEPENDENT_LEMONPRESS_EXPERIMENT',
  sourceRightsValidated:false,localChoice:choice};
 const holdReceipt={...receiptBody,receiptId:sha(Buffer.from(JSON.stringify(receiptBody)))};
 return {files:{
  'candidate.json':json(candidate),'hold-receipt.json':json(holdReceipt),
  ...choice==='HOLD'?{'comic.html':data.comic,'field-card.md':data.card}:{}},
  candidate,holdReceipt};
}
export function receiveLocal(sourceDir,outDir,choice='HOLD'){
 const result=inspect(sourceDir,choice);
 fail(!existsSync(outDir),'OUTPUT_ALREADY_EXISTS');
 mkdirSync(outDir,{mode:0o700,recursive:false});
 for(const [name,content] of Object.entries(result.files))
  writeFileSync(join(outDir,name),content,{mode:0o600,flag:'wx'});
 return result.holdReceipt;
}
export function coldVerifyLocal(sourceDir,outDir,choice='HOLD'){
 const expected=inspect(sourceDir,choice);
 fail(realpathSync(resolve(outDir))===resolve(outDir),'OUTPUT_SYMLINK_REFUSED');
 for(const [name,content] of Object.entries(expected.files)){
  const actual=limited(outDir,name);
  fail(actual.equals(Buffer.isBuffer(content)?content:Buffer.from(content)),'RECEIVER_COLD_REPLAY_MISMATCH_'+name);
 }
 const extra=Object.keys(expected.files);
 // Caller-supplied outputs never become extra published material through this verifier.
 return {status:'INDEPENDENT_RECEIVER_COLD_VERIFIED',decision:expected.candidate.decision,
  receiptId:expected.holdReceipt.receiptId,verifiedFiles:extra.length,
  admitted:false,published:false,externalWrites:0};
}
