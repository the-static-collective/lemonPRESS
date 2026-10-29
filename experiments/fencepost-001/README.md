# FENCEPOST-001 / Reverse Seismograph

**Status: executable digital dry-run, NOT a physical record cutter.**
First carrier: lemonPRESS experiment/fencepost-reverse-seismograph-001. This experiment is independent of the rights-held Other People's Fire vinyl preflight; it does not take custody of its source music or admit a release.

## The idea

A seismograph: vibrating ground -> moving needle -> recorded trace.
A reverse seismograph: electrical audio -> **voice-coil / cutter-head transducer** -> moving stylus -> **lateral modulation in one spiral groove**.

This is essentially how mono record lathes work. It is not simply playing music into a conventional speaker beside warm plastic: the stylus must be mechanically coupled to a calibrated actuator. The blank rotates at constant speed while a separate low-speed feed moves the head toward the center. Existing open source examples include [SL-24](https://slyka.net/lathe/) and a [printer-mainboard-based DIY record lathe](https://hackaday.io/project/202908-vinyl-record-cutting-lathe/details). Amanda Ghassaei [3D printed records](https://amandaghassaei.com/projects/3D_printed_record/) by a *different*, non-real-time process.

### Proposed 3D-printer extension (not yet an installable printer plugin)

             local WAV
                |
        OFFLINE FENCEPOST PLANNER (this code)
           /          |          \
    digest receipt  preview SVG  radial carriage schedule
                                |
              FUTURE HARDWARE ADAPTER (NOT IMPLEMENTED)
                 |                  |
         printer axis: slow    spindle index feedback
           radial feed         + interlocked head lift
                 |                  |
                 +------ calibrated cutter head <--- audio driver

- **Printer chassis/rails:** support the radial carriage and stylus mount, not an audio-rate toolpath. Print the *fixture*, not a 5 kHz G-code waveform.
- **Spindle:** a separately driven and sensed disc platter; position feedback and hard stops are essential.
- **Cutter head:** a properly suspended electromagnetic transducer or voice coil, stylus, amplifier and monitoring; mono lateral modulation first. A full speaker cone or ordinary playback cartridge is not a calibrated recording head.
- **Material:** first tests should use commercially specified polycarbonate embossing blanks. Embossing displaces material; cutting removes material. Both exist in professional practice.
- **Soft-deposition mode:** coupling a stylus to *freshly extruded or cured* polymer would be a distinct research lane, with unresolved flow, temperature, shrinkage, groove collapse and tracking. It is NOT assumed feasible.
- **Reclaimed PVC:** segregated research lane only. Unknown old PVC pipe/fencing may contain stabilizers and other additives; do not heat it in a home printer or improvised oven. No heat or extruder control is supplied by this module.

The motion needs **two timescales**. At 45 rpm and 0.30 mm pitch, the slow carriage feeds inward at **0.225 mm/s**. At 60 mm radius, surface velocity is about **283 mm/s**; a 5 kHz tone occupies about **57 micrometers of groove travel per cycle**. The carriage stepper cannot independently articulate those audio cycles. The voice coil must do that.

## What runs today

Requires Node.js 20+; no packages or device connection.

    node experiments/fencepost-001/fencepost.mjs demo /tmp/fencepost-demo
    node experiments/fencepost-001/fencepost.mjs verify /tmp/fencepost-demo
    node --test experiments/fencepost-001/fencepost.test.mjs

To plan your **owned/permissioned 16-bit PCM WAV**, mono or stereo:

    node experiments/fencepost-001/fencepost.mjs plan ./my-song.wav /tmp/fencepost-song 45

The planner downmixes stereo to mono for an unmastered WAV *reference* only, generates illustrative groove geometry, computes a bounded sequence of radius-vs-time samples, and hashes every output in a repeatable receipt. The WAV is **not** EQ'd, frequency/velocity limited for a cutter, or safe to send to a physical head.

Outputs:
- groove-preview.svg — **decimated visual simulation** only, not a slicer path or record groove.
- radial-axis-plan.json — slow feed samples plus empty commands; no printer execution.
- head-reference.wav — plain mono audio reference, not calibrated cutter-drive audio.
- plan.json — numeric bounds, absent equipment, spindle-index requirement, HOLD state.
- receipt.json — source and output SHA-256, no false claims of manufacturing.

The baseline geometry is **illustrative, not a selected mastering format**: 7-inch concept, 45 rpm, 75 mm outer radius, 55 mm minimum inner radius, 0.30 mm/revolution spiral pitch, 0.022 mm nominal visual lateral modulation. A true record needs mastering, groove-profile tooling, run-in/run-out, calibrated speed and depth, appropriate pitch, and quality tests.

## Plugin extension interface (future)

extension.json declares an offline interface and explicitly denies actuator, hotend, spindle, network and extrusion permissions. A future printer host could call the offline planner and display the receipt/preview. **It must not interpret radial-axis-plan.json as direct G-code.** A machine-specific adapter is deliberately absent until a real printer, spindle and cutter head are known.

A physical prototype would require, at minimum: guarded spindle and speed feedback; mechanically constrained stylus suspension with lift, adjustable pressure and force measurement; head current/thermal protection; independent hard-stop and emergency power isolation; a separated cutter drive and motion controller; suitable licensed audio; a tested blank; and verified geometry calibration.

### Proposed commissioning sequence

1. Generate a three-second reference tone and prove repeatable receipts (done in code).
2. Inspect and measure geometry on screen; print fixtures on a **normal 3D printer** (CAD not yet designed).
3. Design a non-contact head lift and carriage dry-run with an actual named printer model.
4. Verify spindle speed and index sensor with the head fully raised.
5. Validate transducer movement against calibrated targets **without contacting a blank**.
6. Move to professional embossing blanks after mechanical, electrical and material review, first tests with short mono tones.
7. Measure playback and compare to the source; only then investigate reclaimed-material chemistry with a qualified recycling/compounding partner.

**Laws:** MODEL != TOOLPATH · WAVEFORM != CALIBRATED HEAD DRIVE · PRINTED FIXTURE != RECORD · TESTED AUDIO != PRODUCED VINYL · RIGHTS != INFERRED · EXECUTION REQUIRES LOCAL HUMAN AUTHORIZATION.

## Sources / prior art

- SL-24 open-source cutting/embossing lathe: https://slyka.net/lathe/
- Repurposed 3D printer controller lathe experiment: https://hackaday.io/project/202908-vinyl-record-cutting-lathe/details
- Mono polycarbonate embossing in production: https://townlathe.com/faq
- Ghassaei high-resolution 3D printed groove experiment: https://amandaghassaei.com/projects/3D_printed_record/
- Original lemonPRESS vinyl-shaped **rights-held preflight** remains separately on experiment/opf-vinyl-preflight-001, not a physical manufacturing authorization.
