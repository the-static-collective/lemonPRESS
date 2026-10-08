// Independent cold verifier: Node built-ins only. No LemonPRESS or reLATTE imports.
import { readFile, access } from 'node:fs/promises';
import { createHash, webcrypto } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const CROSSING_KEYS = ['schema','crossing_id','protocol_version','source_particular','source_world','source_history_head','parents','declared_kind','payload_refs','requested_effect','capability_ref','privacy_policy','audience_policy','return_address','created_at','signing','extensions'];
const RECEIPT_KEYS = ['schema','receipt_id','crossing_id','world_id','receiver_particular','kind','semantic_effect','contract_ref','pre_state_ref','post_state_ref','descendant_refs','residual_refs','note','created_at','signing','extensions'];
function require(ok, message) { if (!ok) throw Error(message); }
function keys(value, expected) { require(value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).sort().join('|') === [...expected].sort().join('|'), 'INVALID_FIELDS'); }
function canonical(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') { require(Number.isSafeInteger(value), 'UNSAFE_CANONICAL_NUMBER'); return JSON.stringify(value); }
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  require(typeof value === 'object', 'INVALID_CANONICAL_VALUE');
  return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
}
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const domainHash = (domain, value) => sha(Buffer.from(domain + canonical(value)));
const same = (a,b) => canonical(a) === canonical(b);
function publicIdentity(signing, type) {
  keys(signing,['algorithm','public_key','signature','domain']);
  keys(signing.public_key,['kty','crv','x','y']);
  require(signing.algorithm === 'ECDSA-P256-SHA256' && signing.domain === `relatte.${type}-signature/v0`, 'SIGNING_DOMAIN_MISMATCH');
  require(signing.public_key.kty === 'EC' && signing.public_key.crv === 'P-256', 'INVALID_KEY');
  for (const coordinate of ['x','y']) {
    const value = signing.public_key[coordinate];
    const bytes = Buffer.from(value, 'base64url');
    require(bytes.length === 32 && bytes.toString('base64url') === value, 'INVALID_KEY_ENCODING');
  }
  return {algorithm:signing.algorithm,public_key:signing.public_key,domain:signing.domain};
}
export async function verifySigned(value, type) {
  keys(value, type === 'crossing' ? CROSSING_KEYS : RECEIPT_KEYS);
  require(value.schema === `relatte.${type === 'crossing' ? 'crossing-envelope' : 'receipt'}/v0`, 'INVALID_SCHEMA');
  const signing = publicIdentity(value.signing, type);
  const idKey = type === 'crossing' ? 'crossing_id' : 'receipt_id';
  const body = {...value,signing};
  delete body[idKey];
  const idDomain = type === 'crossing' ? 'reLATTE-CrossingEnvelope-v0|' : 'reLATTE-Receipt-v0|';
  const idPrefix = type === 'crossing' ? 'relatte-crossing-v0:' : 'relatte-receipt-v0:';
  require(value[idKey] === idPrefix + domainHash(idDomain, body), 'SIGNED_ID_MISMATCH');
  const sigDomain = type === 'crossing' ? 'reLATTE-CrossingSignature-v0|' : 'reLATTE-ReceiptSignature-v0|';
  const bytes = Buffer.from(value.signing.signature, 'base64url');
  require(bytes.length === 64 && bytes.toString('base64url') === value.signing.signature, 'INVALID_SIGNATURE_ENCODING');
  const key = await webcrypto.subtle.importKey('jwk', signing.public_key, {name:'ECDSA',namedCurve:'P-256'}, false, ['verify']);
  require(await webcrypto.subtle.verify({name:'ECDSA',hash:'SHA-256'}, key, bytes, Buffer.from(sigDomain + canonical({[idKey]:value[idKey],...body}))), 'INVALID_SIGNATURE');
  return true;
}

export async function verifyBundle(folder, expectedSource = null, expectedCrossing = null) {
  const file = name => join(folder,name);
  const read = async name => JSON.parse(await readFile(file(name),'utf8'));
  const exists = async name => {try {await access(file(name)); return true;} catch {return false;}};
  const packet = await read('packet.json');
  execFileSync('python3', [file('verify.py'), folder, '--expected-source', expectedSource ?? packet.source.sha256], {stdio:'pipe'});
  const crossing = await read('crossing.json');
  await verifySigned(crossing,'crossing');
  if (expectedCrossing) require(crossing.crossing_id === expectedCrossing,'CROSSING_ANCHOR_MISMATCH');
  const ext = crossing.extensions.renji_relay;
  require(ext && ext.authority_claim === 'NONE' && ext.admission_claim === 'NONE', 'INHERITED_AUTHORITY');
  require(ext.packet_sha256 === sha(await readFile(file('packet.json'))) && ext.source_sha256 === packet.source.sha256, 'PACKET_CROSSING_MISMATCH');
  require(crossing.source_particular === 'sha256:' + packet.head && crossing.source_history_head === crossing.source_particular && same(crossing.parents,['sha256:' + packet.source.sha256]), 'SOURCE_ANCESTRY_MISMATCH');
  require(same(crossing.payload_refs,[{address:'sha256:' + sha(await readFile(file('press.json'))),role:'press-candidate',media_type:'application/json'}]), 'PAYLOAD_MISMATCH');
  require(same(crossing.requested_effect,{kind:'local-render-request',authority:'receiver-local'}) && crossing.capability_ref === null, 'AUTHORITY_REQUEST_MISMATCH');
  const renderFiles = await Promise.all(['arrival.html','render-receipt.json'].map(exists));
  if (renderFiles.some(Boolean)) {
    require(renderFiles.every(Boolean),'PARTIAL_RENDER');
    execFileSync('python3',[file('foreign_renderer.py'),folder,'--verify'],{stdio:'pipe'});
  }
  const localFiles = ['receive-receipt.json','local-disposition.json','receiver-snapshot.json','receiver-journal.jsonl'];
  const presence = await Promise.all(localFiles.map(exists));
  if (!presence.some(Boolean)) return {status:'VALID_CROSSING',localDisposition:'ABSENT',sourceAnchor:expectedSource ? 'EXTERNAL' : 'SELF_DECLARED',crossingId:crossing.crossing_id};
  require(presence.every(Boolean) && renderFiles.every(Boolean),'PARTIAL_LOCAL_EVIDENCE');
  const received = await read('receive-receipt.json');
  const disposed = await read('local-disposition.json');
  await verifySigned(received,'receipt');
  await verifySigned(disposed,'receipt');
  require(received.crossing_id === crossing.crossing_id && disposed.crossing_id === crossing.crossing_id && received.kind === 'RECEIVED' && received.semantic_effect === 'none', 'RECEIVE_MISMATCH');
  require(same(received.signing.public_key,disposed.signing.public_key) && received.world_id === disposed.world_id && received.receiver_particular === disposed.receiver_particular && received.contract_ref === disposed.contract_ref, 'RECEIVER_IDENTITY_MISMATCH');
  require(['R3_HOLD','R3_ADMIT','R3_REFUSE','R3_RETURN'].includes(disposed.kind),'INVALID_DISPOSITION');
  const disposition = disposed.kind.slice(3);
  require(disposed.note.startsWith('render-receipt-sha256:' + sha(await readFile(file('render-receipt.json'))) + ';'), 'RENDER_RECEIPT_SIGNATURE_BINDING_MISMATCH');
  const extension = disposed.extensions.local_receiver;
  require(extension.disposition === disposition && extension.receive_receipt_id === received.receipt_id && extension.protected_payload_effect === (disposition === 'ADMIT'), 'DISPOSITION_CHAIN_MISMATCH');
  if (disposition === 'ADMIT') {
    require(disposed.semantic_effect === 'experimental-local-render-retained' && same(disposed.descendant_refs,['sha256:' + (await read('render-receipt.json')).outputSha256]), 'ADMISSION_RENDER_MISMATCH');
  } else {
    require(disposed.semantic_effect === (disposition === 'RETURN' ? 'return-created' : 'none') && same(disposed.descendant_refs,[]),'DISPOSITION_EFFECT_MISMATCH');
  }
  const stateRef = status => 'relatte-local-state-v0:' + domainHash('reLATTE-LocalReceiverState-v0|',{
    world_id:received.world_id,receiver_particular:received.receiver_particular,status});
  require(received.pre_state_ref === stateRef([]) && received.post_state_ref === received.pre_state_ref,'RECEIVE_STATE_MISMATCH');
  require(disposed.pre_state_ref === stateRef([{crossing_id:crossing.crossing_id,disposition:'RECEIVED'}]) && disposed.post_state_ref === stateRef([{crossing_id:crossing.crossing_id,disposition}]),'DISPOSITION_STATE_MISMATCH');
  const journal = (await readFile(file('receiver-journal.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
  require(journal.length === 2,'JOURNAL_LENGTH_MISMATCH');
  let head = null;
  for (const [i,event] of journal.entries()) {
    keys(event,['schema','seq','previous_hash','event_type','crossing_id','crossing','receipt','created_at','event_hash']);
    const body = {...event}; delete body.event_hash;
    require(event.schema === 'relatte.local-receiver-event/v0' && event.seq === i + 1 && event.previous_hash === head && event.crossing_id === crossing.crossing_id,'JOURNAL_CHAIN_MISMATCH');
    require(event.event_type === (i === 0 ? 'RECEIVE' : 'DISPOSITION') && same(event.receipt,i === 0 ? received : disposed) && same(event.crossing,i === 0 ? crossing : null) && event.created_at === event.receipt.created_at,'JOURNAL_RECEIPT_MISMATCH');
    head = 'relatte-local-event-v0:' + domainHash('reLATTE-LocalReceiverEvent-v0|',body);
    require(event.event_hash === head,'JOURNAL_HASH_MISMATCH');
  }
  require(extension.history_head_before === journal[0].event_hash,'DISPOSITION_HISTORY_MISMATCH');
  const expected = {schema:'relatte.local-receiver-snapshot/v0',world_id:received.world_id,receiver_particular:received.receiver_particular,history_head:head,received:[crossing.crossing_id],held:[],admitted:[],refused:[],returned:[],state_ref:disposed.post_state_ref};
  expected[{HOLD:'held',ADMIT:'admitted',REFUSE:'refused',RETURN:'returned'}[disposition]] = [crossing.crossing_id];
  require(same(await read('receiver-snapshot.json'),expected),'SNAPSHOT_REPLAY_MISMATCH');
  return {status:disposition === 'REFUSE' ? 'VALID_REFUSAL' : disposition === 'ADMIT' ? 'VALID_ADMISSION' : 'VALID_' + disposition,crossingId:crossing.crossing_id,localDisposition:disposition,houseAdmission:false,signerAuthority:'NOT_ESTABLISHED',sourceAnchor:expectedSource ? 'EXTERNAL' : 'SELF_DECLARED'};
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const args = process.argv.slice(2);
    const option = name => args.includes(name) ? args[args.indexOf(name) + 1] : null;
    console.log(JSON.stringify(await verifyBundle(resolve(args[0]), option('--expected-source'),option('--expected-crossing')),null,2));
  } catch (error) {
    console.error(JSON.stringify({status:'FAIL',error:error.message}));
    process.exitCode = 2;
  }
}
