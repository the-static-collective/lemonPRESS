#!/usr/bin/env node
/* Explicit private local three-door planning. Never a release or renderer. */
import {readFile} from 'node:fs/promises';
import {inspectSelectedMargin} from './goatnote_marginalia.mjs';
import {composeThreeDoorsLocal,verifyThreeDoorsLocal} from './marginalia_three_doors.mjs';
async function main(){
 const [command,arg1,arg2,arg3]=process.argv.slice(2);
 if(command==='inspect'){
  if(!arg1||arg2)throw Error('USAGE inspect selected-margin.json');
  const {packet,verification}=inspectSelectedMargin(await readFile(arg1,'utf8'));
  console.log(JSON.stringify({schema:'lemonpress.marginalia-inspection/v0',
   packet_self_checksum:verification.packet_self_checksum,
   excerpt_checksum:verification.excerpt_checksum,
   source_version_posture:verification.source_version_sha256,
   selected_margin_kind:packet.reading.kind,relation_included:!!packet.relation,
   house_admission:false,publication:false},null,2));
 }else if(command==='compose'){
  if(!arg1||!arg2||arg3?.startsWith('--')===false)
   throw Error('USAGE compose selected-margin.json NEW_DIR [--doors=page,voice,fragment]');
  const options=arg3?{doors:arg3.replace(/^--doors=/,'').split(',')}:{};
  if(arg3&&!arg3.startsWith('--doors='))throw Error('UNSUPPORTED_OPTION');
  console.log(JSON.stringify(await composeThreeDoorsLocal(await readFile(arg1,'utf8'),arg2,options),null,2));
 }else if(command==='verify'){
  if(!arg1||arg2)throw Error('USAGE verify OUTPUT_DIR');
  console.log(JSON.stringify(await verifyThreeDoorsLocal(arg1),null,2));
 }else throw Error('USAGE inspect FILE | compose FILE NEW_DIR [--doors=page,voice,fragment] | verify DIRECTORY');
}
main().catch(e=>{console.error('Three Doors HOLD: '+String(e.message||e).slice(0,240));process.exitCode=1;});
