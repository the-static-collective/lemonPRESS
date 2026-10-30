#!/usr/bin/env node
import {readFileSync,writeFileSync,mkdtempSync,mkdirSync,renameSync,rmSync,readdirSync,
 existsSync,lstatSync,realpathSync} from "node:fs";
import {resolve,join,dirname,basename} from "node:path";
import {compileScreeningProgram,verifyScreeningProgram} from "../src/screening-program.mjs";
function hold(v,x){if(!v)throw Error("LEMONPRESS_SCREENING_HOLD_"+x)}
const [mode,...rest]=process.argv.slice(2);
try{
 hold(["build","verify"].includes(mode)&&rest.length%2===0,"USAGE");
 const o={};for(let i=0;i<rest.length;i+=2){
  hold(["--input","--version","--review","--out","--authorize"].includes(rest[i])
   &&rest[i+1]&&!Object.hasOwn(o,rest[i]),"OPTIONS");o[rest[i]]=rest[i+1];
 }
 hold(o["--input"]&&o["--version"]&&o["--out"],"REQUIRED");
 hold(mode==="build"?o["--authorize"]==="LOCAL_DRAFT_ONLY":!o["--authorize"],"AUTH");
 const version=o["--version"];
 hold(["draft","final"].includes(version)
  &&(version==="final"?!!o["--review"]:!o["--review"]),"VERSION_REVIEW");
 const input=JSON.parse(readFileSync(resolve(o["--input"]),"utf8"));
 const review=version==="final"?JSON.parse(readFileSync(resolve(o["--review"]),"utf8")):null;
 const result=compileScreeningProgram(input,{version,review});
 const out=resolve(o["--out"]),parent=realpathSync(dirname(out));
 hold(join(parent,basename(out))===out,"SYMLINK_PARENT");
 if(mode==="verify"){
  hold(existsSync(out)&&lstatSync(out).isDirectory()&&!lstatSync(out).isSymbolicLink(),"OUTPUT");
  const actual=Object.fromEntries(readdirSync(out).map(n=>[n,readFileSync(join(out,n),"utf8")]));
  verifyScreeningProgram(result.files,actual);
 }else{
  hold(!existsSync(out),"OUTPUT_EXISTS");
  const tmp=mkdtempSync(join(parent,".screening-program-"));
  try{
   const packet=join(tmp,"packet");mkdirSync(packet);
   for(const [n,v] of Object.entries(result.files))writeFileSync(join(packet,n),v,{flag:"wx"});
   renameSync(packet,out);
  }finally{rmSync(tmp,{force:true,recursive:true})}
 }
 console.log(JSON.stringify({status:mode==="build"?"SCREENING_PROGRAM_LOCAL_ONLY":"SCREENING_PROGRAM_COLD_VERIFIED",
  version,receiptSha256:result.receipt.receiptSha256,published:false}));
}catch(e){console.error(String(e.message??e));process.exitCode=2}
