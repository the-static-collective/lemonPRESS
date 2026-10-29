# FENCEPOST-001 / REVERSE SEISMOGRAPH

**Status: runnable software proof, not a built or qualified record-cutting machine.**

A seismograph translates motion into a trace. Our reverse-seismograph concept translates an audio trace into a controlled cutting-head motion. The 3D printer **does not** oscillate its X/Y/Z axes at audio rates. A real cutter needs an independently driven, calibrated high-bandwidth cutting head. The repurposed printer's gantry provides only slow radial feed and positioning; an independently controlled platter provides steady rotation and an index signal. This is a *toolhead extension proposal*, not an extruder replacement ready to use.

## Implemented (stdlib-only)

- Generate a synthetic test tone.
- Parse mono/stereo 16-bit PCM WAV and compute a 7-inch 45rpm / configurable-pitch spiral plan.
- Produce **radial-carriage-preview.csv** (positions vs time); **schematic-spiral.svg** (illustrative audio spiral); **printable-seismograph-trace.scad** (a real FDM printable raised-waveform *tile*, NOT a playable record); **reference-mono-NOT-CUTTER-DRIVE.wav** (a reference signal, NOT safely processed for cutter head); and hashed **receipt.json** (explicit HOLD).
- `prusaslicer_hook.py`: a genuine PrusaSlicer post-processing script which appends a *comment-only* provenance header to separately sliced G-code. Never changes or inserts movement commands; a particular G-code print does not become a lathe operation. Never treat this as a hardware driver.
- Dependency-free tests with geometry, gate, tone, hash, hook, and idempotence checks.

```sh
python3 fencepost/fencepost.py tone --out /tmp/fencepost-tone.wav --duration 2 --frequency 440
python3 fencepost/fencepost.py plan /tmp/fencepost-tone.wav --out /tmp/fencepost-proof
python3 -m unittest discover -s fencepost/tests -v
```

Open `/tmp/fencepost-proof/schematic-spiral.svg`. In OpenSCAD, open `/tmp/fencepost-proof/printable-seismograph-trace.scad`, render and export a tile STL to slice normally. This physical tile is a graphical vibration trace only. **Do not play the trace with a record stylus.**

To add metadata while printing the optional tile with PrusaSlicer, configure its *Print settings → Output options → Post-processing scripts* as:

```text
python3 /absolute/path/to/fencepost/prusaslicer_hook.py --receipt /absolute/path/to/fencepost-proof/receipt.json
```

PrusaSlicer adds its temp G-code file as the final argument. This hook only adds a comment identifying the software receipt; it does not drive a spindle or cutter.

## Future physical architecture (not implemented)

```text
WAV / EDITION + explicit RIGHTS GATE
        │
        ├── SEISMOGRAPH PLANNER ──> slow radial carriage command proposal
        │                              (3D-printer X axis, Z lift after safety review)
        └── cutting reference ─────> audio equalization + head driver (independent)
                                                   │
platter tach + index sensor ──> synchronized controller ──> toolhead/cutter
                                                   │
                                            qualified disc blank
                                                   │
                                      physical inspect + play test
                                                   │
                               lemonPRESS physical packet / CANNON receipt
```

**Separation of time scales:** 45 rpm = 0.75 rev/s. At 0.18 mm/revolution, slow radial feed is **0.135 mm/s**. A 440 Hz note needs hundreds of oscillations per second from the cutting head, *not* from a stepper motor. Synchronization between the head signal and turntable phase is an additional system requirement. A plain CSV and a WAV running simultaneously are not sufficient.

**Materials:** The printable waveform tile uses ordinary approved 3D-printer material. Do not melt recycled PVC fencing or pipe in a normal FDM printer, oven or domestic setup. Polyvinyl chloride decomposition produces corrosive hydrogen chloride; legacy plastic additives vary. Recycled-PVC recording media require identification, lab analysis, compounding and industrially controlled thermal processing. Laser-cutting PVC is also hazardous and is outside scope.

**Cut quality:** Proper groove profile, cutter geometry, phono recording pre-emphasis, lead-in/out, playback stylus compatibility, speed stability and acoustic verification are unsolved. The wav output is not RIAA-encoded or amplitude/current limited; it must never be connected directly to a cutter.

**Next machine milestones (requires actual equipment and trained operator):** motor-off clearance and geometric fitting → soft dummy-head motion and closed-loop platter speed test → cutter-driver bench calibration → qualified commercial blank and 1-second test → 30-second mono test → material tests. A human must expressly approve each separate action. No build/test has been performed on physical hardware.

## Gate / integration contract

`receipt.json` is deterministic and content-addresses all local artifacts plus the source WAV. The status is always `HOLD_SIMULATION_ONLY`; unverified rights, material, audio processing, emergency stop and metrology are retained as distinct holds. This is a **candidate** for lemonPRESS's `press/physical` packet. It does **not** alter Press Gate state or manufacture anything, and it does not assert CANNON execution.

## Prior art and platform interfaces

- Amanda Ghassaei, *3D Printed Record* (2012): https://amandaghassaei.com/projects/3D_printed_record/ — experimental enlarged grooves, recognizable audio; not consumer-FDM quality.
- Amanda Ghassaei, *Laser Cut Record* (2013): https://amandaghassaei.com/projects/laser_cut_record/ — waveform-to-spiral concept; **never laser-cut PVC**.
- Prusa, *Post-processing scripts*: https://help.prusa3d.com/article/post-processing-scripts_283913
- IEC 60098:2020 records geometry: https://standards.theiteh.com/catalog/standards/sist/c91e4c30-2cba-4431-9a3e-a95714d2dff7/sist-en-iec-60098-2020
