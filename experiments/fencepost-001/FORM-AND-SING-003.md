# FENCEPOST-003 — FORM + SING
## Dual-station record making: form a surface, then write sound

**Implementation:** executable **offline coordination simulator** named fusion.mjs, complementing FENCEPOST-001. No hardware movement, heater operation, melting, G-code, or playable record is claimed.

## Mechanism

    Audio file ---------> separate calibrated audio actuator
         |                           |
         v                           v
     Spiral planner             Embossing stylus
         |                           |
         +----> indexed rotating spindle <---- phase sensor
                              |
                    Material-forming tool
                              |
                    Surface characterization
                              |
                    Emboss within a validated
                     material working window
                              |
                    Cool, inspect, playback

The printer motion system supplies **slow radial feed**, not audio-frequency vibration. The voice coil produces the acoustic modulation, while the moving disc provides the continuous surface. This design requires two independent, physically cleared tool placements.

## STAGED — feasible first mechanical architecture

1. Form a blank and smooth top surface on a suitable apparatus.
2. Characterize flatness, top-surface texture, chemical identity, and hardness (not merely a time delay).
3. Hold or transfer into an indexed spindle fixture.
4. Emboss a continuous mono lateral groove with a calibrated recording head, initially in a known commercial blank.
5. Inspect groove microgeometry and only then attempt sacrificial playback.

A normal FDM print is **not assumed playable**. Extrusion lines and layer steps are often much larger than record-groove audio features, so surface finishing or a different deposition technology could be necessary.

## TANDEM — experimental “while malleable” architecture

- Surface head A deposits material onto a rotating, phase-tracked disc.
- Separate stylus head B, at a known fixed angle, reaches the corresponding location later.
- Both tools follow coordinated radial spirals, using the same indexed rotational clock.
- Head B uses a *separate* audio transducer. A printer stepper cannot oscillate at audio-band frequencies.

**Simulated example:** At 45 RPM with a 120-degree head offset, the lag between tools is **0.444444 seconds**. At 0.30 mm per turn the radial feed is **0.225 mm/s**. The downstream head must track the radius deposited at an earlier time, not merely the other carriage's current radius.

**This is a clock relationship, not a measured polymer cooling window.** We do not know whether extruded polymer will stay smooth, soft, geometrically stable or safe for embossing for that duration.

## Run the simulation

Requires Node.js 20+, no packages, no machinery:

    node experiments/fencepost-001/fusion.mjs demo /tmp/fusion-demo tandem
    node experiments/fencepost-001/fusion.mjs verify /tmp/fusion-demo
    node --test experiments/fencepost-001/fusion.test.mjs

To plan a short mono/stereo **16-bit PCM WAV** locally without machine commands:

    node experiments/fencepost-001/fusion.mjs plan /path/to/short.wav /tmp/fusion-plan staged
    node experiments/fencepost-001/fusion.mjs plan /path/to/short.wav /tmp/fusion-tandem tandem 120

Outputs: fusion-plan.json (process gates), fusion-phase-samples.json (matched clocks/radii), fusion-measurement-gates.json (unfulfilled material and hardware evidence), fusion-fixture-concept.svg (non-dimensional visual), fusion-receipt.json (input/output digests). The earlier FENCEPOST-001 spiral model remains the digital reference. All device, extrusion, heater and audio-drive command arrays are **empty**.

## Critical unknowns and hard constraints

- Ordinary FDM print ridges may dominate the microscopic groove shape and produce unplayable distortion/noise.
- Newly deposited polymer may slump or shrink, lose groove features, damage styli, or develop unacceptable surface roughness.
- The process needs a compatible V-shaped stylus profile, geometry/force calibration, accurate spindle speed, safe tool lift, and a verified working window.
- The demo does **not** provide cutter-head mastering/EQ or direct speaker drive.
- Reclaimed PVC pipe/fencing has unknown additive and contamination profiles. It must not be heated in a backyard maker experiment: outside air alone is not adequate exposure control. Work on recycled PVC is a separate material-analysis and industrial-process frontier.

## Milestone ladder

1. Digital timing proof with stable hashes and fail-closed tests — **implemented**.
2. Printer-specific harmless fixture model, guarded spindle indexing, dry non-contact motion — **not built**.
3. Material coupon studies with identified formulation, emissions review, profilometry and cooling/hardness measurements — **not built**.
4. Independent stylus-drive calibration, force limiting and electrical isolation without a plastic blank — **not built**.
5. Unheated test cuts in commercially specified embossing blanks — **not built**.
6. Measured viable deposited-surface window and physically isolated tandem heads — **not built**.
7. Inspection and playback on sacrificial equipment — **not built**.
8. Separate laboratory/industrial route for qualifying recycled pipe/fencing PVC — **not built**.

## Sources

- [Amanda Ghassaei: 3D Printed Record (2012)](https://amandaghassaei.com/projects/3D_printed_record/) — high-resolution resin approach and low-fidelity playable result.
- [Raspberry Pi Magazine: groove feature scale](https://magazine.raspberrypi.com/articles/3d-printed-record) — compares printed features to standard grooves.
- [Takt Direct: vinyl mastering groove specifications](https://www.takt-direct.com/templates-faq/) — typical grooves around tens of microns.
- [SL-24 open-source lathe](https://slyka.net/lathe/) — separate rotation, feed and mechanical cutter-head precedent.

**Boundaries:** modeled != manufactured; soft ≠ embossable; nominal lag != measured window; outside != adequate emissions control; user authorization != motion-controller authorization.
