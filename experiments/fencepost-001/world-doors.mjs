#!/usr/bin/env node
// AUDIO-KEY 005: bounded opt-in local fixture actions.
// This module never evals scripts from records or connects to any world backend.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {scanCapsule,publicId} from './audio-key.mjs';

const sha=s=>createHash('sha256').update(s).digest('hex');
const hold=(ok,code)=>{if(!ok)throw Error('WORLD_DOOR_HOLD_'+code);};
const demoTable=Object.freeze({
  'revival/open/genesis-1-1-demo': Object.freeze({
    kind:'READ_ONLY_LOCAL_FIXTURE',world:'revival',room:'genesis-1-1-demo',
    preview:'Genesis 1:1 word room; the actual Revival repository owns the source and projection.',
    actualRevivalInvocation:false,canonicalTextChanged:false
  }),
  'reality2/preview/waseca-room-demo':Object.freeze({
    kind:'READ_ONLY_LOCAL_FIXTURE',world:'reality2',room:'waseca-room-demo',
    preview:'A community-grocery question card awaits independent moderation.',
    submitted:false,published:false,liveData:false
  }),
  'creature-world/propose/starter-creature-demo':Object.freeze({
    kind:'READ_ONLY_LOCAL_FIXTURE',world:'creature-world',species:'tiny-ghost-cowboy',
    proposedOnly:true,ownedCreatureMinted:false,realGameAccountChanged:false
  }),
  'cannon/inspect/candidate-receipt-demo':Object.freeze({
    kind:'READ_ONLY_LOCAL_FIXTURE',world:'cannon',
    preview:'CANNON candidate witness only. Source and owner selection are separate.',
    selectedCanon:false,hardwareActuated:false
  }),
  'toaster/preview/visualscore-demo':Object.freeze({
    kind:'READ_ONLY_LOCAL_FIXTURE',world:'toaster',
    preview:'An imaginary four-beat ghost-cowboy storyboard, not an admitted VisualScore.',
    frames:['door closed','ghost approaches','door creaks','ghost tips hat'],
    kept:false,rendered:false
  })
});
export function listDoors(wav, manifest){
  const id=publicId(manifest);
  return scanCapsule(wav,{[id]:manifest});
}
export function visitDoor(wav,manifest,world,{approval=null}={}){
  const scan=listDoors(wav,manifest);
  hold(scan.hasKnownManifest && scan.markersAgree && scan.sourcePcmVerifiedToManifest,'CAPSULE_NOT_VERIFIED');
  const matched=scan.routeProposals.filter(p=>p.world===world);
  hold(matched.length===1,'UNKNOWN_OR_AMBIGUOUS_WORLD');
  const proposal=matched[0], key=proposal.world+'/'+proposal.verb+'/'+proposal.resourceKey;
  hold(Object.hasOwn(demoTable,key),'NO_INSTALLED_LOCAL_ADAPTER');
  hold(approval==='OPEN_LOCAL_DEMO','LOCAL_OPERATOR_APPROVAL_REQUIRED');
  // Safe code chosen by the *installed* local adapter, not source-provided executable code.
  const data=JSON.parse(JSON.stringify(demoTable[key]));
  const response={
    schema:'fencepost/world-door-local-demo/v1',executionMode:'FIXTURE_ONLY',
    world,resourceKey:proposal.resourceKey,sourceCapsuleId:scan.publicId,
    preview:data, externalSystemsAccessed:0, codeFromDiscExecuted:false,
    publisherAuthenticated:false,remoteEffects:0,realWorldEffects:0,
    receiptId:'sha256:'+sha(JSON.stringify({key,sourceCapsuleId:scan.publicId,data}))
  };
  return response;
}
function help(){
  return [
    'WORLD DOORS — explicit local demonstration, no external app access.',
    'node world-doors.mjs list CAPSULE_WAV MANIFEST_JSON',
    'node world-doors.mjs visit CAPSULE_WAV MANIFEST_JSON WORLD OPEN_LOCAL_DEMO',
    'WORLD: revival | reality2 | creature-world | cannon | toaster',
    'Only exact source-pinned local demo fixtures are installed.'
  ].join('\n');
}
if(process.argv[1]&&resolve(process.argv[1])===new URL(import.meta.url).pathname){
  try{
    const [,,command,...args]=process.argv;
    if(command==='list' && args.length===2){
      const m=JSON.parse(readFileSync(args[1],'utf8'));
      console.log(JSON.stringify(listDoors(readFileSync(args[0]),m),null,2));
    }else if(command==='visit'&&args.length===4){
      const m=JSON.parse(readFileSync(args[1],'utf8'));
      console.log(JSON.stringify(visitDoor(readFileSync(args[0]),m,args[2],{approval:args[3]}),null,2));
    }else{console.log(help());if(!['help','--help'].includes(command))process.exitCode=2;}
  }catch(e){console.error(e.message);process.exitCode=2;}
}
