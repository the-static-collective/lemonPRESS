#!/usr/bin/env node
// FENCEPOST-001: offline reverse-seismograph planning plugin.
// No device drivers, extrusion commands, thermal processing, or physical authority.
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const SCHEMA = 'fencepost/reverse-seismograph-plan/v1';
const sha = b => 'sha256:' + createHash('sha256').update(b).digest('hex');
const j = o => JSON.stringify(o, null, 2) + '\n';
function hold(ok, code) { if (!ok) throw new Error('FENCEPOST_HOLD_' + code); }
function fixed(x) { return Number(x.toFixed(6)); }

export function encodePcm16(samples, sampleRate = 8000) {
  hold(Number.isInteger(sampleRate) && sampleRate >= 8000 && sampleRate <= 96000, 'SAMPLE_RATE');
  const n = samples.length, out = Buffer.alloc(44 + n * 2);
  out.write('RIFF', 0); out.writeUInt32LE(36 + n * 2, 4); out.write('WAVEfmt ', 8);
  out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(1, 22);
  out.writeUInt32LE(sampleRate, 24); out.writeUInt32LE(sampleRate * 2, 28);
  out.writeUInt16LE(2, 32); out.writeUInt16LE(16, 34);
  out.write('data', 36); out.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) out.writeInt16LE(Math.round(Math.max(-1, Math.min(1, samples[i])) * 32767), 44 + i * 2);
  return out;
}

export function decodePcm16(buf) {
  hold(Buffer.isBuffer(buf) && buf.length >= 44 && buf.length <= 30000000, 'WAV_SIZE');
  hold(buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WAVE', 'WAV_HEADER');
  let pos = 12, fmt = null, data = null;
  while (pos + 8 <= buf.length) {
    const id = buf.toString('ascii', pos, pos + 4);
    const size = buf.readUInt32LE(pos + 4), start = pos + 8;
    hold(start + size <= buf.length, 'WAV_CHUNK');
    if (id === 'fmt ') {
      hold(size >= 16, 'WAV_FMT');
      fmt = {type: buf.readUInt16LE(start), channels: buf.readUInt16LE(start + 2),
        sampleRate: buf.readUInt32LE(start + 4), alignment: buf.readUInt16LE(start + 12),
        bits: buf.readUInt16LE(start + 14)};
    }
    if (id === 'data') data = buf.subarray(start, start + size);
    pos = start + size + (size % 2);
  }
  hold(fmt && data, 'WAV_CHUNKS_MISSING');
  hold(fmt.type === 1 && (fmt.channels === 1 || fmt.channels === 2) &&
       fmt.bits === 16 && fmt.alignment === fmt.channels * 2 &&
       fmt.sampleRate >= 8000 && fmt.sampleRate <= 96000, 'WAV_ONLY_PCM16');
  hold(data.length % (2 * fmt.channels) === 0 && data.length > 0, 'WAV_FRAME_LENGTH');
  const frames = data.length / (2 * fmt.channels), samples = new Float64Array(frames);
  for (let i = 0; i < frames; i++) {
    const a = data.readInt16LE(i * fmt.channels * 2) / 32768;
    const b = fmt.channels === 2 ? data.readInt16LE(i * 4 + 2) / 32768 : a;
    samples[i] = (a + b) / 2;
  }
  return { sampleRate: fmt.sampleRate, channels: fmt.channels, samples };
}

export function planWav(buf, { rpm = 45, pitchMm = 0.3, outerRadiusMm = 75, innerRadiusMm = 55 } = {}) {
  for (const x of [rpm, pitchMm, outerRadiusMm, innerRadiusMm]) hold(Number.isFinite(x), 'FINITE_OPTIONS');
  hold(rpm >= 20 && rpm <= 90 && pitchMm >= 0.15 && pitchMm <= 1 &&
       outerRadiusMm > innerRadiusMm && innerRadiusMm >= 35 && outerRadiusMm <= 84,
       'GEOMETRY_RANGE');
  const decoded = decodePcm16(buf), { sampleRate, channels, samples } = decoded;
  const seconds = samples.length / sampleRate, turns = seconds * rpm / 60;
  const endRadiusMm = outerRadiusMm - turns * pitchMm;
  hold(seconds <= 180 && endRadiusMm >= innerRadiusMm, 'SIDE_CAPACITY');
  const maxAmplitudeMm = 0.022;
  hold(pitchMm > 2 * maxAmplitudeMm + 0.06, 'ADJACENT_GROOVE_MARGIN');
  const linearMmPerSecInner = 2 * Math.PI * endRadiusMm * rpm / 60;
  const waveLengthMmAt5KHz = linearMmPerSecInner / 5000;
  // This waveform is unmastered: no RIAA pre-emphasis, cutter calibration or feedback.
  const headReference = encodePcm16(samples, sampleRate);
  const axis = [], stepTurn = 0.25;
  for (let rev = 0; rev < turns; rev += stepTurn) {
    axis.push({ elapsedSeconds: fixed(rev * 60 / rpm), turns: fixed(rev),
      carriageRadiusMm: fixed(outerRadiusMm - pitchMm * rev) });
  }
  axis.push({ elapsedSeconds: fixed(seconds), turns: fixed(turns), carriageRadiusMm: fixed(endRadiusMm) });
  // Decimated *visualization* only: cannot be used as a cutter or printer toolpath.
  const stride = Math.max(1, Math.ceil(samples.length / 9000));
  const points = [];
  for (let i = 0; i < samples.length; i += stride) {
    const t = i / sampleRate;
    const theta = 2 * Math.PI * rpm / 60 * t;
    const r = outerRadiusMm - pitchMm * rpm / 60 * t + maxAmplitudeMm * samples[i];
    points.push((points.length ? 'L' : 'M') + (90 + r * Math.cos(theta)).toFixed(3) +
      ',' + (90 + r * Math.sin(theta)).toFixed(3));
  }
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180" role="img" aria-label="Simulated mono spiral; not a toolpath">\n' +
    '<rect width="180" height="180" fill="#f5f2ea"/><circle cx="90" cy="90" r="84" fill="#24302a"/>' +
    '<circle cx="90" cy="90" r="36" fill="#f5f2ea"/><path d="' + points.join(' ') +
    '" fill="none" stroke="#d9c19b" stroke-width=".07"/>' +
    '<circle cx="90" cy="90" r="3.6" fill="#24302a"/>' +
    '<text x="90" y="172" fill="#24302a" font-size="5" text-anchor="middle">SIMULATION ONLY / NO CUT PATH</text></svg>\n';
  const manifest = {
    schema: SCHEMA, releaseState: 'HOLD_SIMULATION_ONLY', mode: 'MONO_LATERAL_EMBOSSING_CONCEPT',
    plugin: 'reverse-seismograph', sourceSha256: sha(buf), sampleRate, sourceChannels: channels,
    seconds: fixed(seconds), revolutions: fixed(turns),
    geometry: { rpm, pitchMm, outerRadiusMm, innerRadiusMm,
      endRadiusMm: fixed(endRadiusMm), maxVisualizationAmplitudeMm: maxAmplitudeMm,
      minimumNominalTrackClearanceMm: fixed(pitchMm - 2 * maxAmplitudeMm - 0.06),
      innerLinearSpeedMmPerSec: fixed(linearMmPerSecInner),
      innerWavelengthAt5000HzMm: fixed(waveLengthMmAt5KHz) },
    architecture: { platter: 'EXTERNAL_SPINDLE_NOT_CONTROLLED',
      printerCarriage: 'SLOW_RADIAL_FEED_ONLY',
      cutterHead: 'INDEPENDENT_AUDIO_FREQUENCY_ACTUATOR_NOT_CONTROLLED',
      synchronization: 'SPINDLE_INDEX_FEEDBACK_REQUIRED_NOT_IMPLEMENTED',
      toolLift: 'HARDWARE_INTERLOCK_REQUIRED_NOT_IMPLEMENTED',
      audioChain: 'UNMASTERED_REFERENCE_NOT_CALIBRATED',
      thermalProcessing: 'NOT_SUPPORTED', physicalBlank: 'NOT_SELECTED_OR_VERIFIED' },
    evidence: { audioDigitallyDecoded: true, previewProduced: true,
      cutPerformed: false, recordPressed: false, deviceConnected: false,
      recordPlayable: 'UNTESTED' },
    warnings: ['Do not load SVG as G-code or use reference WAV to drive a cutter without a calibrated head and amplifier.',
      'Mechanical printer axes cannot carry audio-band modulation; use a purpose-built transducer.',
      'Unknown PVC waste must not be melted or softened in an unventilated maker setup.',
      'The groove preview is decimated and exaggerated; it is not dimensionally suitable for manufacture.']
  };
  const files = {
    'plan.json': j(manifest),
    'radial-axis-plan.json': j({ schema: 'fencepost/radial-axis-plan/v1', state: 'OFFLINE_NO_DEVICE_COMMANDS',
      coordinateSystem: 'RADIUS_MM_NOT_PRINTER_XY', samples: axis, spindleIndexRequired: true,
      commands: [] }),
    'groove-preview.svg': svg,
    'head-reference.wav': headReference
  };
  const receiptBody = { schema: 'fencepost/proof-receipt/v1', mode: 'DIGITAL_DRY_RUN',
    inputs: { wav: sha(buf) }, outputs: Object.fromEntries(Object.entries(files).sort(([a],[b]) => a.localeCompare(b)).map(([k,v]) => [k, sha(v)])),
    actuation: false, manufacturing: false, approval: 'NONE' };
  files['receipt.json'] = j({ ...receiptBody, receiptId: sha(j(receiptBody)) });
  return files;
}

export function verifyDirectory(out) {
  const receipt = JSON.parse(readFileSync(join(out, 'receipt.json'), 'utf8'));
  hold(receipt.schema === 'fencepost/proof-receipt/v1' && receipt.actuation === false &&
    receipt.manufacturing === false && receipt.approval === 'NONE', 'RECEIPT');
  const expected = [...Object.keys(receipt.outputs), 'receipt.json'].sort();
  hold(readdirSync(out).sort().join('|') === expected.join('|'), 'UNEXPECTED_FILES');
  for (const [name, digest] of Object.entries(receipt.outputs)) {
    hold(!name.includes('/') && sha(readFileSync(join(out, name))) === digest, 'TAMPER_' + name);
  }
  const { receiptId, ...body } = receipt;
  hold(sha(j(body)) === receiptId, 'RECEIPT_DIGEST');
  return {status: 'COLD_REPLAY_DIGEST_VERIFIED', physicalRecords: 0, ...{receiptId}};
}

function writeProof(files, destination) {
  const out = resolve(destination);
  if (existsSync(out)) hold(readdirSync(out).length === 0, 'OUTPUT_NOT_EMPTY');
  else mkdirSync(out, {recursive: true});
  for (const [name, value] of Object.entries(files)) writeFileSync(join(out, name), value, {flag: 'wx'});
  return verifyDirectory(out);
}

function help() {
  return [
    'FENCEPOST — Reverse Seismograph 001 (OFFLINE SIMULATION ONLY)',
    'node fencepost.mjs demo OUTPUT_DIR',
    'node fencepost.mjs plan INPUT_PCM16_WAV OUTPUT_DIR [RPM]',
    'node fencepost.mjs verify OUTPUT_DIR',
    'No actuators, printer G-code, heat, or motor commands are emitted.'
  ].join('\n');
}

if (process.argv[1] && resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  try {
    const [, , cmd, ...args] = process.argv;
    if (cmd === 'demo' && args.length === 1) {
      const rate = 8000, audio = new Float64Array(rate * 3);
      for (let i = 0; i < audio.length; i++) {
        const t = i / rate, fade = Math.min(1, t * 10, (3 - t) * 10);
        audio[i] = 0.22 * Math.sin(2 * Math.PI * 220 * t) * Math.max(0, fade);
      }
      console.log(JSON.stringify(writeProof(planWav(encodePcm16(audio, rate)), args[0])));
    } else if (cmd === 'plan' && (args.length === 2 || args.length === 3)) {
      const rpm = args[2] === undefined ? 45 : Number(args[2]);
      console.log(JSON.stringify(writeProof(planWav(readFileSync(args[0]), {rpm}), args[1])));
    } else if (cmd === 'verify' && args.length === 1) {
      console.log(JSON.stringify(verifyDirectory(args[0])));
    } else { console.log(help()); if (cmd !== '--help' && cmd !== 'help') process.exitCode = 2; }
  } catch (e) { console.error(String(e.message)); process.exitCode = 2; }
}
