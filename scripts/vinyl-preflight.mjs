import {readFileSync,writeFileSync,existsSync,mkdtempSync,mkdirSync,renameSync,rmSync,readdirSync,realpathSync,lstatSync} from 'node:fs';
import {resolve,join,dirname} from 'node:path';
import {compileVinylProof,verifyProof} from '../src/vinyl-proof.mjs';
const [cmd,...args]=process.argv.slice(2);
const hold=(v,why)=>{if(!v)throw Error('VINYL_HOLD_'+why)};
try{
 hold(['build','verify'].includes(cmd)&&args.length%2===0,'USAGE');
 const f={};for(let i=0;i<args.length;i+=2){hold(['--edition','--room','--out','--authorize'].includes(args[i])&&!Object.hasOwn(f,args[i])&&args[i+1],'FLAGS');f[args[i]]=args[i+1]}
 hold(f['--edition']&&f['--room']&&f['--out'],'INPUTS');
 hold(cmd==='build'?f['--authorize']==='LOCAL_DRAFT_ONLY':!f['--authorize'],'AUTHORIZATION');
 const out=resolve(f['--out']),parent=realpathSync(dirname(out));
 hold(join(parent,out.split('/').at(-1))===out,'PARENT_SYMLINK');
 hold(cmd==='build'?!existsSync(out):existsSync(out)&&lstatSync(out).isDirectory()&&!lstatSync(out).isSymbolicLink(),'OUTPUT_STATE');
 const result=compileVinylProof(JSON.parse(readFileSync(resolve(f['--edition']),'utf8')),JSON.parse(readFileSync(resolve(f['--room']),'utf8')));
 const read=()=>Object.fromEntries(readdirSync(out,{withFileTypes:true}).map(x=>{hold(x.isFile()&&!x.isSymbolicLink(),'UNSAFE_OUTPUT');return [x.name,readFileSync(join(out,x.name),'utf8')]}));
 if(cmd==='verify')verifyProof(result.files,read());
 else{
  const temp=mkdtempSync(join(parent,'.vinyl-preflight-'));
  try{const payload=join(temp,'packet');mkdirSync(payload);for(const [p,v] of Object.entries(result.files))writeFileSync(join(payload,p),v,{flag:'wx'});renameSync(payload,out)}
  finally{rmSync(temp,{recursive:true,force:true})}
 }
 console.log(JSON.stringify({status:cmd==='build'?'VINYL_DRAFT_HOLD':'VINYL_COLD_REPLAY_VERIFIED',receiptId:result.receipt.receiptId,physicalRecords:0,artistCopiesSent:0}));
}catch(e){console.error(String(e.message));process.exitCode=2}
