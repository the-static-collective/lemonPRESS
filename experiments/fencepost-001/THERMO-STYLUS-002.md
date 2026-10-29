# FENCEPOST-002 — Thermo-Stylus: the heated needle experiment

**Research only. No physical build, heater circuit, battery connection, thermal setpoint, G-code, or cutting run is authorized by this document.**

The user's insight is sound: **a heated stylus already exists in record mastering**. A specialized cutter head vibrates in response to audio while a heater independently warms the stylus. RCA's 1953 [induction-heater patent](https://patents.google.com/patent/US2627416A/en) and [1956 stylus heater-wire patent](https://patents.google.com/patent/US2746130A/en) describe relevant prior art. The latter shows that the heater wire's added mass affects high-frequency cutter response. A contemporary professional lathe offers stylus heat Off/Low/Medium/High, with fused heater-current monitoring, *separate* from the regulated disc heater. [Reccut technical details](https://reccut-audio.com/en/home/products/technical_data).

## Two separate circuits

1. **Audio path**: mono master → calibrated current-limited cutter amplifier → moving coil / stylus → modulated lateral groove.
2. **Thermal path**: isolated current-limited heater → measured stylus temperature; independent cutoff and no coupling into audio amplifier.

**Do not connect a battery directly across a metal stylus.** That can create a short, uncontrolled hot spot, distortion, damaged electronics, and burns. A soldering-iron tip is not a precision record-cutter profile.

## What do "three times" and "three volumes" mean?

At 45 rpm, 3 whole revolutions = **4 seconds**. The **one continuous groove is a spiral**: with 0.30 mm per revolution, after three turns it has advanced 0.90 mm radially. Recording audio during those three turns is normal, *not* repeated passes over one groove.

**Writing over the same groove three times at three amplitudes is not a good baseline.** The second/third pass can deform or erase earlier modulations. Re-registering phase and radial location to microscopic accuracy is difficult, especially with heat.

The useful version of the idea is a three-arm experiment **on three fresh sections/blanks**:
- A: identical short source, digital reference gain -18 dB, heater OFF.
- B: identical source, digital reference gain -12 dB, heater OFF.
- C: identical source, digital reference gain -6 dB, heater OFF.

These numbers are proposed **digital reference levels, NOT amplifier output voltage or physical cutting depth**. They must first be translated through a calibrated actuator. Compare resulting groove geometry, surface noise, clipping/distortion, stylus load, and playback on sacrificial equipment.

Only after the baseline should we hold the audio level constant and compare heater OFF against a qualified, regulated LOW heater setting on new blanks. That isolates heat's effect from level's effect.

**Low heat is not automatically safe PVC processing.** Reclaimed pipe/fencing has unknown additives, and localized hot spots at the needle can exceed the temperature suggested by a heater setting. Outside does not eliminate inhalation exposure. Keep reclaimed PVC heating on hold pending material analysis and an engineered extraction / gas-control setup. [ILO/WHO PVC chemical hazard card](https://chemicalsafety.ilo.org/dyn/icsc/showcard.display?p_card_id=1487&p_lang=en&p_version=2).

## Hardware concept

```
              WAV                  thermal setpoint + sensor
               |                             |
     recording-head amplifier         protected heater controller
               |                             |
         moving coil + suspension    heater on stylus shank
                 \                         /
                  precision stylus tip
                         |
               approved rotating blank
                         |
     slow printer carriage + indexed spindle
```

The existing FENCEPOST-001 offline planner is the appropriate place to prototype signal gain comparisons and keep receipts. Machine adapters remain **unimplemented**. Future prototype reviews must cover spindle index, head lift, emergency stop, thermal sensor and cutoff, force control, fume extraction, tool geometry, material compatibility, electrical isolation, and genuinely measurable sound-quality criteria.

See `thermo-stylus-002.json` for the machine-readable experiment matrix. It explicitly contains **no heater or motion commands**.

**Model ≠ Toolpath. Three comparisons ≠ three recuts. Outside ≠ industrial ventilation.**
