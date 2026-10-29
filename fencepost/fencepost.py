#!/usr/bin/env python3
"""FENCEPOST-001: offline reverse-seismograph research and dry-run planner.

No motor, heater, cutter, spindle, or machine command is generated here.
"""
from __future__ import annotations

import argparse
from array import array
import csv
import hashlib
import json
import math
import sys
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

VERSION = "fencepost-001.0"


@dataclass(frozen=True)
class Parameters:
    rpm: float = 45.0
    groove_pitch_mm: float = 0.18
    start_radius_mm: float = 76.0
    min_radius_mm: float = 48.0
    max_duration_s: float = 30.0
    carriage_hz: int = 10

    def check(self, duration: float) -> None:
        vals = (self.rpm, self.groove_pitch_mm, self.start_radius_mm,
                self.min_radius_mm, self.max_duration_s)
        if not all(math.isfinite(x) for x in vals):
            raise ValueError("All numeric settings must be finite")
        if not 16 <= self.rpm <= 90:
            raise ValueError("RPM outside research range 16..90")
        if not 0.08 <= self.groove_pitch_mm <= 0.5:
            raise ValueError("Pitch outside research range 0.08..0.5 mm/rev")
        if not 0 < self.min_radius_mm < self.start_radius_mm <= 80:
            raise ValueError("For 7-inch research blank, require 0 < inner < outer <= 80 mm")
        if not 0 < duration <= self.max_duration_s <= 60:
            raise ValueError("Duration outside research window or maximum duration <= 60 seconds")
        if not 1 <= self.carriage_hz <= 50:
            raise ValueError("Carriage preview sample rate must be 1..50 Hz")
        if self.start_radius_mm - self.groove_pitch_mm * self.rpm * duration / 60 < self.min_radius_mm:
            raise ValueError("Audio duration would exceed minimum permitted groove radius")


def _read_pcm(path: Path, duration_limit_s: float) -> tuple[int, array]:
    with wave.open(str(path), "rb") as w:
        channels, width, fs, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        if channels not in (1, 2) or width != 2 or not 8000 <= fs <= 96000:
            raise ValueError("Only mono/stereo 16-bit PCM WAV at 8–96 kHz supported")
        if frames < 1 or frames / fs > duration_limit_s:
            raise ValueError("WAV must have 1 or more frames and fit duration limit")
        raw = w.readframes(frames)
    pcm = array('h')
    pcm.frombytes(raw)
    if sys.byteorder != 'little':
        pcm.byteswap()
    if channels == 1:
        return fs, pcm
    mono = array('h', (int((pcm[i] + pcm[i + 1]) / 2) for i in range(0, len(pcm), 2)))
    return fs, mono


def _write_wav(path: Path, fs: int, mono: array) -> None:
    data = array('h', mono)
    if sys.byteorder != 'little':
        data.byteswap()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(data.tobytes())


def radius_at(t: float, p: Parameters) -> float:
    """Steady spiral; printer carriage motion is low frequency, not audio modulation."""
    return p.start_radius_mm - t * p.rpm * p.groove_pitch_mm / 60


def _carriage_csv(path: Path, duration: float, p: Parameters) -> int:
    n = math.ceil(duration * p.carriage_hz)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "platter_revolutions", "head_radius_mm", "radial_feed_mm_per_s", "simulation_only"])
        for i in range(n + 1):
            t = min(duration, i / p.carriage_hz)
            writer.writerow([f"{t:.6f}", f"{t*p.rpm/60:.6f}", f"{radius_at(t,p):.6f}",
                             f"{-p.groove_pitch_mm*p.rpm/60:.6f}", "TRUE"])
    return n + 1


def _svg(path: Path, fs: int, mono: array, p: Parameters) -> None:
    """Schematic sampled spiral; high-frequency actual grooves are NOT represented."""
    duration = len(mono) / fs
    count = min(24000, max(500, math.ceil(duration * 650)))
    c = 425.0
    scale = 4.8
    points = []
    for k in range(count + 1):
        t = duration*k/count
        sample_index = min(len(mono)-1, int(t*fs))
        angle = -2*math.pi*p.rpm*t/60
        # Waveform exaggerated for legible preview; not physical machine geometry.
        r = scale * (radius_at(t, p) + 0.04 * (mono[sample_index]/32768))
        points.append(f"{c+r*math.cos(angle):.2f},{c+r*math.sin(angle):.2f}")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 850" role="img" aria-label="Schematic audio spiral">
<title>FENCEPOST-001 radial feed preview — schematic only</title>
<rect width="850" height="850" fill="#f8f7f3"/>
<circle cx="425" cy="425" r="{scale*p.start_radius_mm:.2f}" fill="none" stroke="#ccc" stroke-width="1"/>
<circle cx="425" cy="425" r="22" fill="#eee" stroke="#777" stroke-width="2"/>
<polyline fill="none" stroke="#252525" stroke-width="1.2" points="{' '.join(points)}"/>
<text x="25" y="33" font-family="monospace" font-size="15">FENCEPOST / SCHEMATIC (NOT CUTTER PATH)</text>
<text x="25" y="813" font-family="monospace" font-size="13">{p.rpm:g} rpm · {duration:.2f}s · pitch {p.groove_pitch_mm:g} mm/rev · waveform exaggerated</text>
</svg>'''
    path.write_text(svg, encoding='utf-8')


def _trace_scad(path: Path, fs: int, mono: array) -> None:
    """Printable *raised trace plate*, not a playable record or cutter fixture."""
    n = min(240, len(mono))
    seg = min(len(mono), int(fs * 0.20))
    vals = []
    for j in range(n):
        idx = min(seg-1, int(j*seg/n))
        vals.append(mono[idx] / 32768)
    pts = []
    for j, y in enumerate(vals):
        pts.append(f"[{5 + j*110/max(1,n-1):.3f},{15 + 6*y + 0.7:.3f}]")
    for j in range(n-1, -1, -1):
        pts.append(f"[{5 + j*110/max(1,n-1):.3f},{15 + 6*vals[j] - 0.7:.3f}]")
    scad = '''// Reverse seismography: 3D-PRINTABLE WAVEFORM TRACE, NOT AUDIO GROOVE.
// Ordinary FDM plastic demonstration, 120 x 30 x 3.2 mm nominal.
// No PVC extrusion, no lathe fixtures, no proof of playable sound.
union() {
  cube([120,30,2.4]);
  translate([0,0,2.4]) linear_extrude(height=0.8)
    polygon(points=[\n    ''' + ',\n    '.join(pts) + '''\n  ]);
}
'''
    path.write_text(scad, encoding='utf-8')


def run_plan(source: Path, out: Path, p: Parameters) -> dict:
    if not source.is_file():
        raise ValueError(f"Missing WAV input: {source}")
    fs, mono = _read_pcm(source, p.max_duration_s)
    duration = len(mono)/fs
    p.check(duration)
    out.mkdir(parents=True, exist_ok=True)
    _write_wav(out / 'reference-mono-NOT-CUTTER-DRIVE.wav', fs, mono)
    rows = _carriage_csv(out / 'radial-carriage-preview.csv', duration, p)
    _svg(out / 'schematic-spiral.svg', fs, mono, p)
    _trace_scad(out / 'printable-seismograph-trace.scad', fs, mono)
    outputs = {}
    for name in ('reference-mono-NOT-CUTTER-DRIVE.wav', 'radial-carriage-preview.csv',
                 'schematic-spiral.svg', 'printable-seismograph-trace.scad'):
        outputs[name] = hashlib.sha256((out / name).read_bytes()).hexdigest()
    receipt = {
        'schema': 'fencepost-001/dry-run/v1', 'version': VERSION,
        'status': 'HOLD_SIMULATION_ONLY', 'physical_record_made': False,
        'cutting_authorized': False, 'motor_commands_generated': False,
        'source': {'filename': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                   'frames': len(mono), 'sample_rate_hz': fs, 'duration_s': round(duration, 6)},
        'planner': {**asdict(p), 'revolutions': round(duration*p.rpm/60,6),
                    'final_radius_mm': round(radius_at(duration,p),6),
                    'feed_rate_mm_per_s': round(-p.groove_pitch_mm*p.rpm/60,8),
                    'carriage_preview_rows': rows},
        'outputs_sha256': outputs,
        'holds': ['Rights for recorded work not verified', 'Blank material and additives not verified',
                  'Platter closed-loop speed/phase not measured', 'Mechanical travel/end stops not validated',
                  'Independent cutter-head driver and safe current limiting not designed',
                  'RIAA recording pre-emphasis / anti-alias / playback not verified',
                  'Groove geometry, tracking, runout and quality not verified',
                  'Emergency stop, tooling, chip capture, ventilation and operator training not verified'],
        'integration': {'lemonpress': 'physical-edition candidate only',
                        'cannon': 'receipt candidate; NOT an executed manufacturing event',
                        'printer_adapter': 'PrusaSlicer metadata hook; no motor-control G-code'},
    }
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n',encoding='utf-8')
    return receipt


def run_tone(out: Path, duration: float, fs: int, frequency: float) -> None:
    if not (0 < duration <= 30 and 8000 <= fs <= 96000 and 20 <= frequency <= 2000):
        raise ValueError("Tone requires 0<seconds<=30, 8k<=Hz<=96k and 20<=frequency<=2000")
    pcm = array('h', (int(9000*math.sin(2*math.pi*frequency*i/fs)) for i in range(int(fs*duration))))
    out.parent.mkdir(parents=True, exist_ok=True)
    _write_wav(out, fs, pcm)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='FENCEPOST reverse seismograph — OFFLINE/DRY-RUN')
    sub = ap.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('tone', help='Create synthetic lab WAV, no copyrighted source required')
    g.add_argument('--out', type=Path, required=True)
    g.add_argument('--duration', type=float, default=2.0)
    g.add_argument('--frequency', type=float, default=440.)
    g.add_argument('--sample-rate', type=int, default=44100)
    p = sub.add_parser('plan', help='Preview 7-inch spiral; NO MOTOR COMMANDS')
    p.add_argument('wav', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--rpm', type=float, default=45.0)
    p.add_argument('--pitch-mm', type=float, default=0.18)
    p.add_argument('--start-radius-mm', type=float, default=76.)
    p.add_argument('--min-radius-mm', type=float, default=48.)
    p.add_argument('--duration-limit-s', type=float, default=30.)
    args=ap.parse_args(argv)
    try:
        if args.mode == 'tone':
            run_tone(args.out, args.duration, args.sample_rate, args.frequency)
            print(f'Wrote {args.out} (LAB TONE)')
        else:
            config=Parameters(rpm=args.rpm,groove_pitch_mm=args.pitch_mm,
                              start_radius_mm=args.start_radius_mm,min_radius_mm=args.min_radius_mm,
                              max_duration_s=args.duration_limit_s)
            r=run_plan(args.wav,args.out,config)
            print(json.dumps({'status':r['status'],'output':str(args.out), 'geometry':r['planner']},indent=2))
        return 0
    except (ValueError,wave.Error,OSError,OverflowError) as e:
        ap.error(str(e))
        return 2

if __name__=='__main__':
    raise SystemExit(main())
