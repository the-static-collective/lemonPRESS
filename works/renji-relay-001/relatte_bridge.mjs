// Production-side adapter; the foreign renderer and cold signature verifier do not import reLATTE.
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { resolve, join, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const PIN = 'dcc8cdca84c440aa4294134f020fb7095bf87f24';
const here = dirname(fileURLToPath(import.meta.url));
const [command, folderArg, runtimeArg, receiverArg, dispositionArg = 'ADMIT'] = process.argv.slice(2);
const folder = resolve(folderArg ?? '.');
const runtime = resolve(runtimeArg ?? '.');
const read = async name => JSON.parse(await readFile(join(folder, name), 'utf8'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
async function createOnly(name, value) {
  const bytes = Buffer.from(JSON.stringify(value, null, 2) + '\n');
  try {
    const old = await readFile(join(folder, name));
    if (!old.equals(bytes)) throw Error('CREATE_ONLY_CONFLICT:' + name);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    await writeFile(join(folder, name), bytes, { flag: 'wx' });
  }
}
try {
  if (!['seal', 'receive', 'verify-native'].includes(command)) throw Error('COMMAND_REQUIRED');
  const commit = execFileSync('git', ['-C', runtime, 'rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
  if (commit !== PIN) throw Error('RELATTE_COMMIT_MISMATCH');
  execFileSync('git', ['-C', runtime, 'diff', '--exit-code', 'HEAD', '--', 'src', 'package.json'], {stdio:'pipe'});
  const dep = JSON.parse(await readFile(join(runtime, 'node_modules/json-canonicalize/package.json'), 'utf8'));
  if (dep.version !== '3.0.1') throw Error('CANONICALIZER_VERSION_MISMATCH');
  const { generateP256KeyPair, sealCrossingEnvelope, verifyCrossingEnvelope, verifyReceipt } = await import(pathToFileURL(join(runtime, 'src/protocol.ts')));
  const { LocalReceiver } = await import(pathToFileURL(join(runtime, 'src/receiver.ts')));
  const packet = await read('packet.json');
  const manifest = JSON.parse(await readFile(join(here, 'source-manifest.json'), 'utf8'));
  const expected = manifest.sources.find(s => s.slot === packet.source.slot)?.sha256;
  if (!expected) throw Error('UNKNOWN_SOURCE');
  execFileSync('python3', [join(folder, 'verify.py'), folder, '--expected-source', expected], {stdio:'pipe'});
  const pressBytes = await readFile(join(folder, 'press.json'));
  if (command === 'seal') {
    // Signing is a new occurrence. Replays reuse the recorded signature, never re-sign.
    const draft = {schema:'relatte.crossing-envelope/v0',protocol_version:'0',
      source_particular:'sha256:' + packet.head,source_world:'world:lemonpress-renji-experiment',
      source_history_head:'sha256:' + packet.head,parents:['sha256:' + expected],declared_kind:'RENJI_RELAY_DRAFT',
      payload_refs:[{address:'sha256:' + sha(pressBytes),role:'press-candidate',media_type:'application/json'}],
      requested_effect:{kind:'local-render-request',authority:'receiver-local'},capability_ref:null,
      privacy_policy:{scope:'user-directed private experiment'},audience_policy:null,return_address:null,
      created_at:new Date().toISOString(),extensions:{renji_relay:{schema:'lemonpress/renji-crossing/v0',
        packet_sha256:sha(await readFile(join(folder, 'packet.json'))),source_sha256:expected,
        authority_claim:'NONE',admission_claim:'NONE',relatte_commit:PIN}}};
    const crossing = await sealCrossingEnvelope(draft, await generateP256KeyPair());
    if (!await verifyCrossingEnvelope(crossing)) throw Error('NATIVE_CROSSING_REFUSED');
    await createOnly('crossing.json', crossing);
  } else {
    const crossing = await read('crossing.json');
    if (!await verifyCrossingEnvelope(crossing)) throw Error('INVALID_CROSSING');
    if (command === 'receive') {
      if (!receiverArg) throw Error('PRIVATE_RECEIVER_PATH_REQUIRED');
      execFileSync('node', [join(folder, 'verify-crossing.mjs'), folder], {stdio:'pipe'});
      execFileSync('python3', [join(folder, 'foreign_renderer.py'), folder, '--verify'], {stdio:'pipe'});
      const localRoot = resolve(receiverArg);
      let receiver;
      try { receiver = await LocalReceiver.open(localRoot); }
      catch (error) {
        if (error.code !== 'ENOENT') throw error;
        receiver = await LocalReceiver.create(localRoot, {world_id:'world:renji-receipt-scroll-experiment',
          receiver_particular:'particular:experimental-arrival-room',contract_ref:'contract:private-draft-render/v0'});
      }
      const received = await receiver.receive(crossing, new Date().toISOString());
      const render = await read('render-receipt.json');
      if (!['ADMIT','REFUSE','HOLD','RETURN'].includes(dispositionArg)) throw Error('INVALID_LOCAL_DISPOSITION');
      const admitted = await receiver.dispose(crossing.crossing_id, dispositionArg, new Date().toISOString(), {
        admit_effect:'experimental-local-render-retained',descendant_refs:dispositionArg === 'ADMIT' ? ['sha256:' + render.outputSha256] : [],
        note:'render-receipt-sha256:' + sha(await readFile(join(folder, 'render-receipt.json'))) + '; experimental local ' + dispositionArg + '; no LemonPRESS house admission, source authority or publication.'});
      const reopened = await LocalReceiver.open(localRoot);
      if (JSON.stringify(reopened.snapshot()) !== JSON.stringify(receiver.snapshot())) throw Error('RESTART_MISMATCH');
      await createOnly('receive-receipt.json', received);
      await createOnly('local-disposition.json', admitted);
      await createOnly('receiver-snapshot.json', reopened.snapshot());
      // Public journal is portable; private receiver-key.json stays outside the bundle.
      const journal = await readFile(join(localRoot, 'journal.jsonl'));
      try {
        await writeFile(join(folder, 'receiver-journal.jsonl'), journal, {flag:'wx'});
      } catch (error) {
        if (error.code !== 'EEXIST' || !(await readFile(join(folder, 'receiver-journal.jsonl'))).equals(journal)) throw error;
      }
    } else {
      for (const name of ['receive-receipt.json','local-disposition.json']) {
        if (!await verifyReceipt(await read(name))) throw Error('INVALID_NATIVE_RECEIPT:' + name);
      }
    }
  }
  console.log(JSON.stringify({status:'PASS',command,relatteCommit:PIN,signatureProves:'integrity under experimental keys; no owner/source authority'}));
} catch (error) {
  console.error(JSON.stringify({status:'FAIL',error:error.message}));
  process.exitCode = 2;
}
