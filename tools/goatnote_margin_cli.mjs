#!/usr/bin/env node
/* Explicit local CLI; private candidate never added to a house catalog. */
import {readFile} from 'node:fs/promises';
import {inspectSelectedMargin,composeLocal} from './goatnote_marginalia.mjs';
async function main(){
 const [command,source,dest]=process.argv.slice(2);
 if(!['inspect','compose'].includes(command)||!source||(command==='compose'&&!dest))
  throw Error('usage: node tools/goatnote_margin_cli.mjs inspect <private.json> | compose <private.json> <NEW-directory>');
 const text=await readFile(source,'utf8');
 if(command==='inspect'){
  const result=inspectSelectedMargin(text),p=result.packet;
  console.log(JSON.stringify({
   schema:'lemonpress.goatnote-inspection/v0',state:'PRIVATE_CANDIDATE',
   excerpt_checksum:result.verification.excerpt_checksum,
   source_version_sha256:result.verification.source_version_sha256,
   has_relation:p.relation!==null,authority:'NONE',
   admission:false,publication:false
  },null,2));
 }else console.log(JSON.stringify(await composeLocal(text,dest),null,2));
}
main().catch(e=>{console.error('Private candidate refused: '+String(e.message).slice(0,150));process.exitCode=1;});
