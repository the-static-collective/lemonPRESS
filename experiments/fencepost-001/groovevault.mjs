#!/usr/bin/env node
// GROOVEVAULT-004: Binary bytes <-> audio FSK for physical-disc *research*.
// Sound files only. This is NOT a proven record-storage system or cutter driver.
import {readFileSync,writeFileSync,mkdirSync,existsSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {encodePcm16,decodePcm16} from './fencepost.mjs';

export const RATE=48000, BAUD=300, SAMPLES_PER_BIT=RATE/BAUD;
export const MAX_BYTES=2048;
const LEADER_BITS=96, LEAD_SILENCE=2400, AMP=0.52;
const TONES=[1200,2400], MAGIC=Buffer.from('GVR1','ascii');
const json=obj=>JSON.stringify(obj,null,2)+'\n';
const sha=b=>'sha256:'+createHash('sha256').update(b).digest('hex');
function check(condition,code){if(!condition)throw Error('GROOVEVAULT_HOLD_'+code);}

function crc32(bytes){
  let c=0xFFFFFFFF;
  for(const byte of bytes){
    c^=byte;
    for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xEDB88320:0);
  }
  return (c^0xFFFFFFFF)>>>0;
}
function hammingBits(n){
  const d=[(n>>3)&1,(n>>2)&1,(n>>1)&1,n&1];
  return [d[0]^d[1]^d[3], d[0]^d[2]^d[3],d[0],
    d[1]^d[2]^d[3],d[1],d[2],d[3]];
}
function decodeHammingBits(bits){
  check(bits.length===7,'CODEWORD_LENGTH');
  const b=[0,...bits],p1=b[1]^b[3]^b[5]^b[7];
  const p2=b[2]^b[3]^b[6]^b[7],p4=b[4]^b[5]^b[6]^b[7];
  const syndrome=p1+2*p2+4*p4;
  if(syndrome)b[syndrome]^=1;
  return {nibble:(b[3]<<3)|(b[5]<<2)|(b[6]<<1)|b[7],corrections:syndrome?1:0};
}
function dataBits(packet){
  const bits=[];
  for(const byte of packet){
    bits.push(...hammingBits(byte>>>4),...hammingBits(byte&15));
  }
  return bits;
}
function fromBits(bits){
  check(bits.length%14===0,'INCOMPLETE_CODEWORDS');
  const result=Buffer.alloc(bits.length/14);
  let corrections=0;
  for(let i=0;i<result.length;i++){
    const a=decodeHammingBits(bits.slice(i*14,i*14+7));
    const b=decodeHammingBits(bits.slice(i*14+7,i*14+14));
    result[i]=(a.nibble<<4)|b.nibble;
    corrections+=a.corrections+b.corrections;
  }
  return {result,corrections};
}
export function packetFor(data){
  check(Buffer.isBuffer(data)&&data.length<=MAX_BYTES,'DATA_LIMIT_2K');
  const head=Buffer.alloc(6);
  MAGIC.copy(head,0);head.writeUInt16BE(data.length,4);
  const core=Buffer.concat([head,data]), crc=Buffer.alloc(4);
  crc.writeUInt32BE(crc32(core));
  return Buffer.concat([core,crc]);
}
export function toBits(data){
  return [...Array.from({length:LEADER_BITS},(_,i)=>i%2),...dataBits(packetFor(data))];
}
function modulate(bits){
  const samples=new Float64Array(LEAD_SILENCE+bits.length*SAMPLES_PER_BIT);
  for(let k=0;k<bits.length;k++){
    const omega=2*Math.PI*TONES[bits[k]]/RATE, start=LEAD_SILENCE+k*SAMPLES_PER_BIT;
    for(let i=0;i<SAMPLES_PER_BIT;i++)samples[start+i]=AMP*Math.sin(omega*i);
  }
  return encodePcm16(samples,RATE);
}
export function encode(data){return modulate(toBits(data));}
function classify(samples,start,cosTables,sinTables){
  let p0s=0,p0c=0,p1s=0,p1c=0;
  for(let i=0;i<SAMPLES_PER_BIT;i++){
    const v=samples[start+i];
    p0s+=v*sinTables[0][i];p0c+=v*cosTables[0][i];
    p1s+=v*sinTables[1][i];p1c+=v*cosTables[1][i];
  }
  const p0=p0s*p0s+p0c*p0c,p1=p1s*p1s+p1c*p1c;
  return {bit:p1>p0?1:0,confidence:Math.abs(p1-p0)/(p0+p1+1e-15)};
}
export function decode(wav){
  const {samples,sampleRate,channels}=decodePcm16(wav);
  check(sampleRate===RATE && channels===1,'48K_MONO_ONLY');
  const sinTables=[],cosTables=[];
  for(const freq of TONES){
    const s=[],c=[];
    for(let i=0;i<SAMPLES_PER_BIT;i++){
      const theta=2*Math.PI*freq*i/RATE;
      s.push(Math.sin(theta));c.push(Math.cos(theta));
    }
    sinTables.push(s);cosTables.push(c);
  }
  // Locate the signal onset. Try nearby alignments against 96 known alternating bits.
  let first=-1;
  for(let i=0;i<samples.length;i++){
    if(Math.abs(samples[i])>0.15){first=i;break;}
  }
  check(first>=0,'NO_SIGNAL');
  const candidates=[];
  for(let base=Math.max(0,first-12);base<=first+5;base++){
    if(base+(LEADER_BITS+84)*SAMPLES_PER_BIT>samples.length)continue;
    let errors=0,sum=0;
    for(let b=0;b<32;b++){
      const r=classify(samples,base+b*SAMPLES_PER_BIT,cosTables,sinTables);
      if(r.bit!==b%2)errors++;
      sum+=r.confidence;
    }
    candidates.push({base,errors,score:sum});
  }
  check(candidates.length>0,'TRUNCATED_LEADER');
  candidates.sort((a,b)=>a.errors-b.errors||b.score-a.score);
  const start=candidates[0].base;
  check(candidates[0].errors<=2,'LEADER_SYNC');
  const count=Math.floor((samples.length-start)/SAMPLES_PER_BIT);
  check(count>=LEADER_BITS+84,'TRUNCATED_HEADER');
  const readBits=(offset,n)=>{
    check(offset+n<=count,'TRUNCATED_DATA');
    const bits=[];
    for(let k=0;k<n;k++)bits.push(classify(samples,start+(offset+k)*SAMPLES_PER_BIT,cosTables,sinTables).bit);
    return bits;
  };
  const leader=readBits(0,LEADER_BITS);
  check(leader.reduce((errors,b,i)=>errors+(b!==i%2?1:0),0)<=6,'LEADER_DAMAGED');
  const prefix=fromBits(readBits(LEADER_BITS,6*14));
  check(prefix.result.subarray(0,4).equals(MAGIC),'MAGIC');
  const length=prefix.result.readUInt16BE(4);
  check(length<=MAX_BYTES,'DECLARED_SIZE');
  const data=fromBits(readBits(LEADER_BITS,(10+length)*14));
  const packet=data.result,body=packet.subarray(0,6+length);
  const expected=packet.readUInt32BE(6+length);
  check(crc32(body)===expected,'CRC32');
  return {payload:Buffer.from(packet.subarray(6,6+length)), corrections:data.corrections,
    detectedSampleOffset:start, leaderErrors:leader.reduce((n,b,i)=>n+(b!==i%2?1:0),0),
    baud:BAUD, modulation:'FSK1200_2400_HZ',
    note:'Digital WAV decoding does not establish recovery from a physical record.'};
}

export function manifest(data,wav,decoded=null){
  const bits=toBits(data);
  return {schema:'fencepost/groovevault-data-audio/v1',state:'DIGITAL_WAV_ONLY',
    modulation:{baud:BAUD,f0Hz:1200,f1Hz:2400,sampleRate:RATE,
      errorCorrection:'HAMMING_7_4_PER_NIBBLE',integrity:'CRC32',bitOrder:'MSB_FIRST',
      preambleBits:LEADER_BITS},
    input:{bytes:data.length,sha256:sha(data)},
    waveform:{durationSeconds:Number((wav.length/2/RATE).toFixed(3)),
      actualWavSeconds:Number(((wav.length-44)/2/RATE).toFixed(6)),wavSha256:sha(wav),
      transmittedBits:bits.length},
    digitalProof:{decodedBytes:decoded?.payload.length??null,
      exactRoundTrip:decoded?decoded.payload.equals(data):null,
      bitCorrections:decoded?.corrections??null},
    physicalProof:{recordCut:false,playedFromVinyl:false,wetSurfaceTried:false,
      verifiedDataCapacityBytes:null,playbackErrorRate:null},
    cautions:[
      'This WAV is deliberately loud data tones, not pleasant or safe to play at high volume.',
      'The decoder assumes stable 48 kHz playback; real vinyl speed drift, dropout, equalization and noise need field testing.',
      'The modern digital packet framing is inspired by 300-baud Kansas City tape encoding, not wire-compatible with legacy machines.',
      'Physical record mastering, material, stylus and playback remain separate HOLD gates.',
      'Do not store unique secrets or sole backups on an experimental physical medium.'
    ]};
}

function writeProof(data,dir){
  const out=resolve(dir);check(!existsSync(out),'OUTPUT_EXISTS');
  mkdirSync(out,{recursive:true});
  const wav=encode(data),recovered=decode(wav);
  check(recovered.payload.equals(data),'ROUNDTRIP');
  const files={
    'data-fsk.wav':wav,
    'payload.bin':data,
    'groovevault-manifest.json':json(manifest(data,wav,recovered))
  };
  const receipt={schema:'fencepost/groovevault-receipt/v1',
    state:'DIGITAL_WAV_ONLY',physicalRecords:0,
    hashes:Object.fromEntries(Object.entries(files).map(([k,v])=>[k,sha(v)]))};
  files['groovevault-receipt.json']=json({...receipt,receiptId:sha(json(receipt))});
  for(const [name,value] of Object.entries(files))writeFileSync(join(out,name),value,{flag:'wx'});
  return verify(out);
}
export function verify(outdir){
  const out=resolve(outdir),receipt=JSON.parse(readFileSync(join(out,'groovevault-receipt.json'),'utf8'));
  check(receipt.state==='DIGITAL_WAV_ONLY' && receipt.physicalRecords===0,'RECEIPT_STATE');
  const {receiptId,...body}=receipt;
  check(sha(json(body))===receiptId,'RECEIPT_DIGEST');
  const expected=[...Object.keys(receipt.hashes),'groovevault-receipt.json'].sort();
  check(readdirSync(out).sort().join('|')===expected.join('|'),'UNEXPECTED_FILE');
  for(const [name,hash] of Object.entries(receipt.hashes)){
    check(['data-fsk.wav','payload.bin','groovevault-manifest.json'].includes(name),'UNSAFE_FILE');
    check(sha(readFileSync(join(out,name)))===hash,'TAMPER_'+name);
  }
  const wav=readFileSync(join(out,'data-fsk.wav'),payload=readFileSync(join(out,'payload.bin'));
  check(decode(wav).payload.equals(payload),'DIGITAL_ROUNDTRIP');
  return {status:'GROOVEVAULT_COLD_DIGITAL_ROUNDTRIP_VERIFIED',receiptId,bytes:payload.length,physicalRecords:0};
}
function help(){
  return ['GROOVEVAULT-004: binary data → 300-baud FSK WAV → recovered binary',
    'node groovevault.mjs demo OUTPUT_DIR',
    'node groovevault.mjs encode INPUT_FILE OUTPUT_DIR (max 2048 bytes)',
    'node groovevault.mjs decode INPUT_PCM16_WAV OUTPUT_FILE',
    'node groovevault.mjs verify OUTPUT_DIR',
    'Offline simulation only; physical vinyl decoding NOT demonstrated.'].join('\n');
}
if(process.argv[1] && resolve(process.argv[1])===new URL(import.meta.url).pathname){
  try{
    const [,,cmd,...args]=process.argv;
    if(cmd==='demo'&&args.length===1){
      const data=Buffer.from('A record is a physical computer program. FENCEPOST-004\\n','utf8');
      console.log(JSON.stringify(writeProof(data,args[0])));
    }else if(cmd==='encode'&&args.length===2){
      console.log(JSON.stringify(writeProof(readFileSync(args[0]),args[1])));
    }else if(cmd==='decode'&&args.length===2){
      check(!existsSync(args[1]),'OUTPUT_EXISTS');
      const result=decode(readFileSync(args[0]));
      writeFileSync(args[1],result.payload,{flag:'wx'});
      console.log(JSON.stringify({status:'DIGITAL_DECODE_ONLY',bytes:result.payload.length,
        corrections:result.corrections,physicalRecords:0}));
    }else if(cmd==='verify'&&args.length===1){
      console.log(JSON.stringify(verify(args[0])));
    }else{
      console.log(help());if(cmd!=='help'&&cmd!=='--help')process.exitCode=2;
    }
  }catch(e){console.error(e.message);process.exitCode=2;}
}
