/* Synthetic only. Verify the *actual* pinned GOATnote exporter, then compose
   private Three Doors files outside the public checkout. */
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {makePressMarginCarrier} from '../../goatnote-source/lemonpress-margin.mjs';
import {composeThreeDoorsLocal} from '../../tools/marginalia_three_doors.mjs';
const root=process.argv[2];
if(!root)throw Error('private output root required');
const long=process.argv.includes('--long');
const malicious=process.argv.includes('--html-escape');
const badFont=process.argv.includes('--missing-font-glyph');
const quote=badFont?'Here is a disallowed emoji \u{1F9D1}':
 malicious?'<img src="https://example.com/steal" onerror="alert(1)">':
 long?'The house takes attendance. '.repeat(70):
 'The house takes attendance. The living answer — π.';
const noteText='PRIVATE PROLOGUE. '+quote+' PRIVATE EPILOGUE.';
const start=noteText.indexOf(quote);
const now='2026-10-11T17:00:00.000Z';
const db={schema:1,notes:[
 {id:'source',title:'The Door Keeps Its Own History',draft:'unselected private draft',
 versions:[{id:'v0',text:noteText,createdAt:'2026-10-08T15:00:00.000Z'}],
 margins:[{id:'margin1',kind:'question',text:long?'A later human margin that refuses to overwrite the original. '.repeat(80):
 'What became visible only after the event?',
 versionId:'v0',createdAt:'2026-10-11T16:00:00.000Z',
 anchor:{start,end:start+quote.length,quote}}],
 returnThreads:[{id:'secret',sourceVersionId:'v0',entries:[{text:'HIDDEN PRIVATE THREAD'}]}]},
 {id:'unselected',title:'SECRET OTHER NOTE',versions:[{id:'v0',text:'PRIVATE OTHER BODY'}],margins:[]}
 ],edges:[{id:'e1',from:{noteId:'source',versionId:'v0',anchor:null},
 to:{noteId:'unselected',versionId:'v0',anchor:null},type:'echoes',
 status:'perceived',firstPerceivedAt:'2026-10-10T12:00:00.000Z',
 discoveryTrace:'The reader discovered a relation yesterday; the source did not change.',
 evidencePath:'Two exact saved versions, no causal proof'}],rooms:[],walks:[]};
await mkdir(root,{recursive:true});
const packet=await makePressMarginCarrier(db,{
 noteId:'source',marginId:'margin1',edgeId:'e1',selectedAt:now});
await writeFile(join(root,'selected-margin.json'),JSON.stringify(packet)+'\n',{mode:0o600});
const result=await composeThreeDoorsLocal(JSON.stringify(packet),join(root,'score'));
console.log(JSON.stringify({result,quote}));
