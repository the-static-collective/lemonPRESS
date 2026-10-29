#!/usr/bin/env node
// FENCEPOST-003: audio -> material formation -> audio-embossing coordination.
// ALL OUTPUTS ARE SIMULATIONS. NOT G-CODE, MACHINE CONTROL, OR VERIFIED MATERIAL SCIENCE.
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {encodePcm16, planWav} from './fencepost.mjs';

const digest = data => 'sha256:' + createHash('sha256').update(data).digest('hex');
const json = data => JSON.stringify(data, null, 2) + '\n';
const number = x => Number(x.toFixed(6));
const hold = (ok, code) => {if (!ok) throw Error('FUSION_HOLD_' + code);};
const modes = ['staged','tandem'];
const S = 'fencepost/form-and-sing/v1';

function validate(config) {
  hold(config && typeof config === 'object' && !Array.isArray(config), 'CONFIG');
  const {mode='staged', headOffsetDegrees=120, geometry={}} = config;
  hold(modes.includes(mode), 'MODE');
  const g = {rpm:45, pitchMm:0.3, outerRadiusMm:75, innerRadiusMm:55, ...geometry};
  for (const key of ['rpm','pitchMm','outerRadiusMm','innerRadiusMm'])
    hold(Number.isFinite(g[key]), 'FINITE_GEOMETRY');
  hold(Number.isFinite(headOffsetDegrees) && headOffsetDegrees > 0 &&
    headOffsetDegrees < 360, 'HEAD_SEPARATION');
  hold(g.rpm > 0 && g.pitchMm > 0, 'SPEED_PITCH');
  return {mode, headOffsetDegrees, geometry:g};
}

function fixtureSvg(mode, lagSeconds, headOffsetDegrees) {
  const escape = x => String(x).replaceAll('&','&amp;').replaceAll('<','&lt;');
  return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 300" role="img" aria-label="FENCEPOST experimental two-head material and audio arrangement">',
    '<rect width="740" height="300" rx="16" fill="#f7f3e9"/>',
    '<circle cx="175" cy="150" r="113" fill="#25372f" stroke="#9fbb9b" stroke-width="3"/>',
    '<circle cx="175" cy="150" r="9" fill="#dbc89f"/>',
    '<circle cx="175" cy="150" r="74" fill="none" stroke="#c2d6a7" stroke-width="1.5" stroke-dasharray="3 4"/>',
    '<path d="M175 60 L175 107" stroke="#f5ab62" stroke-width="7"/>',
    '<circle cx="175" cy="107" r="7" fill="#f5ab62"/>',
    '<path d="M247 202 L216 177" stroke="#8fc4e0" stroke-width="7"/>',
    '<circle cx="216" cy="177" r="7" fill="#8fc4e0"/>',
    '<g font-family="Arial,sans-serif" fill="#182b25">',
    '<text x="30" y="289" font-size="14">Schematic only; no verified tool position, heat, or clearance</text>',
    '<text x="328" y="65" font-size="23" font-weight="bold">FORM + SING</text>',
    '<text x="328" y="104" font-size="16">Orange: surface-forming tool</text>',
    '<text x="328" y="136" font-size="16">Blue: audio-coupled embossing stylus</text>',
    '<text x="328" y="177" font-size="16">Mode: '+escape(mode)+'</text>',
    '<text x="328" y="209" font-size="16">Nominal angular offset: '+headOffsetDegrees.toFixed(1)+' deg</text>',
    '<text x="328" y="241" font-size="16">Nominal phase lag: '+lagSeconds.toFixed(6)+' sec</text>',
    '<text x="328" y="273" font-size="13">Materials, sensors, and both heads UNVALIDATED</text>',
    '</g></svg>\n'].join('');
}

/**
 * Produce a timing relationship between a proposed deposited spiral and the
 * same spiral observed by an offset stylus. This is geometrical *planning*
 * for two indexed tools, not evidence of a usable polymer groove.
 */
export function compileFusion(wav, rawConfig={}) {
  hold(Buffer.isBuffer(wav), 'WAV_REQUIRED');
  const {mode, headOffsetDegrees, geometry} = validate(rawConfig);
  const parentFiles = planWav(wav, geometry);
  const parent = JSON.parse(parentFiles['plan.json']);
  const radial = JSON.parse(parentFiles['radial-axis-plan.json']);
  const rpm = parent.geometry.rpm;
  const phaseLagSeconds = mode === 'tandem' ? headOffsetDegrees / 360 * 60 / rpm : null;
  const events = radial.samples.map(sample => ({
    grooveTimeSeconds: sample.elapsedSeconds,
    grooveTurns:sample.turns,
    grooveRadiusMm:sample.carriageRadiusMm,
    formationTimeSeconds: mode === 'tandem' ? sample.elapsedSeconds : null,
    embossTimeSeconds: mode === 'tandem' ? number(sample.elapsedSeconds + phaseLagSeconds) : null,
    // Both share the same radius for an indexed location at different wall-clock
    // times. Independent carriage calibration will be necessary.
    matchedRadiusMm:sample.carriageRadiusMm
  }));
  const assumptions = {
    stationGeometry:'CONCEPT_ONLY',
    indexing:'SPINDLE_INDEX_REQUIRED_UNIMPLEMENTED',
    materialTransition:'UNMEASURED',
    surfaceRoughness:'UNMEASURED',
    stylusContact:'DISABLED',
    thermalOutput:'DISABLED',
    extruderOutput:'DISABLED',
    actualMaterial:'NONE',
    referenceGroove:'NON_PLAYABLE_MODEL',
    prototypeMode: 'SIMULATION_ONLY'
  };
  const stages = mode === 'tandem'
    ? [
      {name:'material-forming', status:'HOLD_NO_DEPOSITION', referenceClock:'rotational-indexed-proposal'},
      {name:'time-offset-emboss', status:'HOLD_NO_STYLUS', referenceClock:'source-time-plus-lag'}
    ] : [
      {name:'form-blank', status:'HOLD_NO_DEPOSITION', completionCriteria:['dimensional-inspection','surface-profilometry']},
      {name:'condition-and-qualify', status:'HOLD_UNKNOWN_POLYMER_STATE',
        completionCriteria:['material-identity','surface-finish','flatness','electrical-safety']},
      {name:'emboss-on-same-fixture', status:'HOLD_NO_STYLUS',
        completionCriteria:['spindle-index','head-lift','force-limit','geometry-calibration']}
    ];
  const plan = {
    schema:S, state:'HOLD_SIMULATION_ONLY', sourceSha256:digest(wav),
    underlyingSpiralPlanSha256:digest(parentFiles['plan.json']),
    design:'One machine; a surface-forming station and a separate audio-driven stylus station.',
    mode, compatibility:'NO_DIRECT_SLICER_OR_PRINTER_PLUGIN',
    stageOrder:stages, geometry:parent.geometry,
    synchronization:{
      spindleRpm:rpm, angularOffsetDegrees:headOffsetDegrees,
      nominalFollowLagSeconds: phaseLagSeconds === null ? null : number(phaseLagSeconds),
      motion:'INDEPENDENT_RADIAL_CARRIAGES_WITH_SHARED_INDEXED_SPINDLE',
      headDrive:'CALIBRATED_AUDIO_TRANSDUCER_REQUIRED',
      phaseFeedback:'UNIMPLEMENTED',
      actualSurfaceAgeAtEmboss:'UNKNOWN_UNTIL_INSTRUMENTED'
    },
    assumptions, deviceCommands:[], heaterCommands:[], depositionCommands:[], audioDriveCommands:[],
    physicalEvidence:{materialDeposited:false, grooveEmbossed:false,
      recordPlayed:false, polymerWindowVerified:false, surfaceFinishMeasured:false},
    conditionsToAdvance:[
      'Independent material selection and identity/temperature assessment',
      'Metrology to show the deposited surface is sufficiently smooth and stable',
      'Calibrated groove cross-section and independently current-limited voice-coil head',
      'Spindle-index feedback and phase/position alignment under measured load',
      'Emergency cutoff, head lift, enclosure and validated material emissions controls',
      'A real measurement demonstrating a viable post-deposition embossing window'
    ],
    cautions:[
      'Typical FDM layer/line roughness dwarfs many standard record-groove features.',
      'Nominal angular delay is not an actual polymer softening or solidification model.',
      'Head position, groove dimensions and timebase are illustrative only.',
      'Do not melt reclaimed PVC pipe or fencing outdoors or in an unvalidated printer.'
    ]
  };
  const phase = {schema:'fencepost/fusion-phase-samples/v1', state:'NONACTUATING',
    note:'The schedule is not G-code; no nozzle flow, motor speed or head current are supplied.',
    samples:events, commands:[]};
  const evidence = {
    schema:'fencepost/fusion-measurement-gates/v1', state:'NO_HARDWARE_VALIDATION',
    material:{identity:null,manufacturerDatasheet:null,additivesAssessed:false},
    geometry:{flatnessMeasured:false, surfaceRoughnessMeasured:false, profileScanned:false},
    machine:{spindleFeedbackVerified:false, carriageRepeatabilityMeasured:false,
      headLiftVerified:false, eStopVerified:false},
    recording:{headFrequencyResponseMeasured:false, contactForceMeasured:false,
      distortionMeasured:false, playbackTestPassed:false},
    decision:'HOLD'
  };
  const files = {
    'fusion-plan.json':json(plan),
    'fusion-phase-samples.json':json(phase),
    'fusion-measurement-gates.json':json(evidence),
    'fusion-fixture-concept.svg':fixtureSvg(mode, phaseLagSeconds ?? 0, headOffsetDegrees)
  };
  const body={schema:'fencepost/fusion-receipt/v1', parentSpiralPlanSha256:digest(parentFiles['plan.json']),
    inputWavSha256:digest(wav), mode,
    outputs:Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,digest(v)])),
    materialProcessed:false, physicalMachineryActuated:false, physicalRecordProduced:false};
  files['fusion-receipt.json']=json({...body, receiptId:digest(json(body))});
  return files;
}

export function verifyFusion(dir) {
  const out=resolve(dir), receipt=JSON.parse(readFileSync(join(out,'fusion-receipt.json'),'utf8'));
  hold(receipt.schema==='fencepost/fusion-receipt/v1' &&
    receipt.materialProcessed===false && receipt.physicalMachineryActuated===false &&
    receipt.physicalRecordProduced===false, 'INVALID_RECEIPT');
  const names=[...Object.keys(receipt.outputs),'fusion-receipt.json'].sort();
  hold(names.join('|')===readdirSync(out).sort().join('|'), 'UNEXPECTED_FILE');
  for (const [name,hash] of Object.entries(receipt.outputs)){
    hold(/^[a-z0-9-]+\.(json|svg)$/.test(name),'UNSAFE_FILE');
    hold(digest(readFileSync(join(out,name)))===hash,'TAMPER_'+name);
  }
  const {receiptId,...body}=receipt;
  hold(digest(json(body))===receiptId,'RECEIPT_TAMPER');
  return {status:'COLD_REPLAY_DIGEST_VERIFIED', receiptId, physicalRecords:0};
}

export function writeFusion(files, dir) {
  const out=resolve(dir);
  if(existsSync(out)) hold(readdirSync(out).length===0, 'OUTPUT_NOT_EMPTY');
  else mkdirSync(out,{recursive:true});
  for (const [filename,body] of Object.entries(files))
    writeFileSync(join(out,filename),body,{flag:'wx'});
  return verifyFusion(out);
}

function help() {
  return ['FENCEPOST-003: FORM + SING / NO HARDWARE CONTROL',
    'node fusion.mjs demo OUTPUT_DIR [staged|tandem]',
    'node fusion.mjs plan INPUT_PCM16_WAV OUTPUT_DIR [staged|tandem] [OFFSET_DEGREES]',
    'node fusion.mjs verify OUTPUT_DIR',
    'The tandem mode models angular offset and gives no verified polymer window.'
  ].join('\n');
}

if(process.argv[1] && resolve(process.argv[1])===new URL(import.meta.url).pathname){
  try{
    const [,,cmd,...args]=process.argv;
    if(cmd==='demo' && (args.length===1 || args.length===2)){
      const s=new Float64Array(3*8000);
      for(let i=0;i<s.length;i++)s[i]=0.16*Math.sin(2*Math.PI*220*i/8000);
      console.log(JSON.stringify(writeFusion(compileFusion(encodePcm16(s),{mode:args[1]??'tandem'}),args[0])));
    }else if(cmd==='plan' && args.length>=2 && args.length<=4){
      const offset=args[3]===undefined?120:Number(args[3]);
      console.log(JSON.stringify(writeFusion(compileFusion(readFileSync(args[0]),{
        mode:args[2]??'staged',headOffsetDegrees:offset}),args[1])));
    }else if(cmd==='verify'&&args.length===1){
      console.log(JSON.stringify(verifyFusion(args[0])));
    }else{console.log(help());if(cmd!=='help'&&cmd!=='--help')process.exitCode=2;}
  }catch(e){console.error(String(e.message)); process.exitCode=2;}
}
