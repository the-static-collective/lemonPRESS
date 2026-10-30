#!/usr/bin/env node
import {readFileSync,writeFileSync,mkdtempSync,mkdirSync,renameSync,rmSync,readdirSync,
 existsSync,lstatSync,realpathSync} from "node:fs";
import {resolve,join,dirname,basename} from "node:path";
import {compileMinuteMailKit,verifyMinuteKit} from "../src/minute-mail-house.mjs";
const hold=(v,m)=>{if(!v)throw Error("LEMON_MINUTE_HOLD_"+m)};
const [mode,...args]=process.argv.slice(2);
try{
 hold(["build","verify"].includes(mode)&&args.length%2===0,"USAGE");
 const o={};for(let i=0;i<args.length;i+=2){hold(["--input","--version","--review","--out","--authorize"].includes(args[i])
  &&args[i+1]&&!Object.hasOwn(o,args[i]),"FLAGS");o[args[i]]=args[i+1]}
 hold(o["--input"]&&o["--version"]&&o["--out"]
  &&(mode==="build"?o["--authorize"]==="LOCAL_DRAFT_ONLY":!o["--authorize"])
  &&["draft","final"].includes(o["--version"])
  &&(o["--version"]==="final"?!!o["--review"]:!o["--review"]),"AUTH");
 const input=JSON.parse(readFileSync(resolve(o["--input"]),"utf8"));
 const review=o["--review"]?JSON.parse(readFileSync(resolve(o["--review"]),"utf8")):null;
 const kit=compileMinuteMailKit(input,{version:o["--version"],review});
 const out=resolve(o["--out"]),parent=realpathSync(dirname(out));
 hold(join(parent,basename(out))===out,"SYMLINK");
 if(mode==="build"){
  hold(!existsSync(out),"EXISTS");
  const tmp=mkdtempSync(join(parent,".minute-kit-"));
  try{const p=join(tmp,"kit");mkdirSync(p);
   for(const [n,v] of Object.entries(kit.files))writeFileSync(join(p,n),v,{flag:"wx"});
   renameSync(p,out)}finally{rmSync(tmp,{recursive:true,force:true})}
 }else{
  hold(existsSync(out)&&lstatSync(out).isDirectory()&&!lstatSync(out).isSymbolicLink(),"DIR");
  const files=Object.fromEntries(readdirSync(out).map(n=>[n,readFileSync(join(out,n),"utf8")]));
  verifyMinuteKit(kit.files,files);
 }
 console.log(JSON.stringify({status:mode==="build"?"LEMON_MINUTE_KIT_BUILT_LOCAL":"LEMON_MINUTE_KIT_COLD_VERIFIED",
  version:o["--version"],receiptSha256:kit.receipt.receiptSha256,published:false}));
}catch(e){console.error(String(e.message??e));process.exitCode=2}
