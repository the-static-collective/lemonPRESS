import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync, mkdtempSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {execFileSync} from 'node:child_process';
import {encodePcm16,decodePcm16} from './fencepost.mjs';
import {encode,decode,toBits,packetFor,manifest,verify,BAUD,MAX_BYTES,RATE,SAMPLES_PER_BIT} from './groovevault.mjs';

const data=Buffer.from('The Fence That Sang. Seed: CANNON + LEMONPRESS + TOASTER.\n');
test('data-to-FSK and FSK-to-data is exact and deterministic',()=>{
  const wav=encode(data), another=encode(data),read=decode(wav);
  assert.ok(wav.equals(another));
  assert.ok(read.payload.equals(data));
  assert.equal(read.corrections,0);
  assert.equal(read.baud,300);
  assert.equal(decodePcm16(wav).sampleRate,48000);
  assert.equal(toBits(data).length,96+(data.length+10)*14);
  assert.equal(packetFor(data).readUInt16BE(4),data.length);
  const m=manifest(data,wav,read);
  assert.equal(m.digitalProof.exactRoundTrip,true);
  assert.equal(m.physicalProof.playedFromVinyl,false);
});

test('empty payload is valid but physical claims remain false',()=>{
  const zero=Buffer.alloc(0), recovery=decode(encode(zero));
  assert.ok(recovery.payload.equals(zero));
  assert.equal(manifest(zero,encode(zero),recovery).physicalProof.verifiedDataCapacityBytes,null);
});

test('single corrupted FSK symbol corrected using Hamming parity',()=>{
  const wav=encode(data),bits=toBits(data);
  const targetBit=96+6*14+1; // one bit in payload, not the leader
  const {samples}=decodePcm16(wav);
  const opposite=1-bits[targetBit], frequency=opposite?2400:1200;
  const offset=2400+targetBit*SAMPLES_PER_BIT;
  for(let i=0;i<SAMPLES_PER_BIT;i++)
    samples[offset+i]=0.52*Math.sin(2*Math.PI*frequency*i/RATE);
  const recovered=decode(encodePcm16(samples,RATE));
  assert.ok(recovered.payload.equals(data));
  assert.ok(recovered.corrections>=1);
});

test('two corrupted bits in the same codeword cause CRC rejection',()=>{
  const wav=encode(data),bits=toBits(data),{samples}=decodePcm16(wav);
  for(const targetBit of [96+6*14,96+6*14+1]){
    const frequency=bits[targetBit]?1200:2400;
    const offset=2400+targetBit*SAMPLES_PER_BIT;
    for(let i=0;i<SAMPLES_PER_BIT;i++)
      samples[offset+i]=0.52*Math.sin(2*Math.PI*frequency*i/RATE);
  }
  assert.throws(()=>decode(encodePcm16(samples,RATE)),/GROOVEVAULT_HOLD_CRC32/);
});

test('small deterministic surface noise does not destroy a clean WAV round-trip',()=>{
  const wav=encode(data),{samples}=decodePcm16(wav);
  for(let i=0;i<samples.length;i++){
    samples[i]=Math.max(-1,Math.min(1,samples[i]+0.045*Math.sin(i*7.307)));
  }
  const recovered=decode(encodePcm16(samples,RATE));
  assert.ok(recovered.payload.equals(data));
});

test('bad audio and overlarge data are refused',()=>{
  assert.throws(()=>encode(Buffer.alloc(MAX_BYTES+1)),/GROOVEVAULT_HOLD_DATA_LIMIT_2K/);
  assert.throws(()=>encode('not buffer'),/GROOVEVAULT_HOLD_DATA_LIMIT_2K/);
  assert.throws(()=>decode(Buffer.from('not audio')),/FENCEPOST_HOLD_WAV_SIZE/);
  const bad=Buffer.from(encode(data));bad.writeUInt32LE(44100,24);
  assert.throws(()=>decode(bad),/GROOVEVAULT_HOLD_48K_MONO_ONLY/);
});

test('CLI demo and cold receipt verification have no physical execution',()=>{
  const dir=mkdtempSync(join(tmpdir(),'gv-'));
  rmSync(dir,{recursive:true,force:true});
  const script=new URL('./groovevault.mjs',import.meta.url).pathname;
  try{
    const proof=JSON.parse(execFileSync(process.execPath,[script,'demo',dir],{encoding:'utf8'}));
    assert.equal(proof.status,'GROOVEVAULT_COLD_DIGITAL_ROUNDTRIP_VERIFIED');
    assert.equal(proof.physicalRecords,0);
    assert.equal(verify(dir).receiptId,proof.receiptId);
    const p=join(dir,'payload.bin'),old=readFileSync(p);
    writeFileSync(p,'tampered');
    assert.throws(()=>verify(dir),/GROOVEVAULT_HOLD_TAMPER_payload.bin/);
    writeFileSync(p,old);
    assert.throws(()=>execFileSync(process.execPath,[script,'demo',dir],{stdio:'pipe'}),/OUTPUT_EXISTS/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
