#!/usr/bin/env node
import {receiveLocal,coldVerifyLocal} from './held-culture.mjs';
const [cmd,source,out,choice='HOLD']=process.argv.slice(2);
try{
 if(!['receive','verify'].includes(cmd)||!source||!out)throw Error('USAGE: receive|verify SOURCE_DIR OUT_DIR [HOLD|REFUSE]');
 console.log(JSON.stringify(cmd==='receive'?receiveLocal(source,out,choice):coldVerifyLocal(source,out,choice),null,2));
}catch(e){console.error('HOLD:',String(e.message).slice(0,350));process.exitCode=2}
