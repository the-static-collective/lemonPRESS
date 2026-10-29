# GROOVEVAULT-004 — A physical-disc data modem

**Status:** Working offline binary-data -> audio WAV -> binary-data digital round-trip, not yet recorded onto a physical disc.

## Precedent

- 1977 Interface Age magazine [Floppy ROM](https://tangiblemediacollection.com/artifacts/floppy-rom) used a sound sheet to carry BASIC code.
- [BYTE June 1977](https://vintageapple.org/byte/pdf/197706_Byte_Magazine_Vol_02-06_Cognitive_Robot.pdf) documents the 300 baud program-disc technique.
- [VinylVideo](https://www.vinylvideo.com/press/02_text/02_vv_about.html) stored low-bandwidth video signals in record grooves.
- [Kansas City-standard audio interface](https://deramp.com/swtpc.com/AC30/AC30_Index.htm) used 1200/2400 Hz FSK at 300 baud. Our frame and error correction are a new format, NOT compatible with a vintage computer cassette loader.

## Implemented signal path

    Original bytes
          |
    Magic / length / CRC32
          |
    Hamming 7,4 per nibble
          |
    Frequency shift keying
    0 = 1200Hz, 1 = 2400Hz
          |
    48 kHz / 16-bit mono WAV
          |
    (physical record not built)
          |
    Digital waveform decoder
          |
    Correct errors / verify CRC32
          |
    Exact recovered source bytes

Leader: 96 alternating bits. Encoded packet: 4-byte magic GVR1, 2-byte length, payload, 4-byte CRC32. Hamming(7,4) handles one corrupted bit per 7-bit codeword. Multiple-bit corruption can be detected using CRC32, with the usual nonzero collision risk.

## Reproduce (Node.js 22, no dependencies)

    node experiments/fencepost-001/groovevault.mjs demo /tmp/gv-demo
    node experiments/fencepost-001/groovevault.mjs verify /tmp/gv-demo
    node --test experiments/fencepost-001/groovevault.test.mjs

To encode a file of 2,048 bytes or less:

    node experiments/fencepost-001/groovevault.mjs encode ./message.txt /tmp/gv-message

To recover data from a supported digital audio recording:

    node experiments/fencepost-001/groovevault.mjs decode ./playback.wav /tmp/recovered.bin

The decoder accepts 48 kHz mono 16-bit PCM and searches a short offset range for the leader. The code assumes a stable recording clock, mostly intact leader, sufficient audio level, and high enough signal quality. It is not tested with a phonograph or real RIAA record-playback chain. No motor, printer, amplifier, cutter or heater commands are produced.

## Storage estimates (unverified on real vinyl)

At 300 bits per second a 20 minute side offers at most 45,000 raw byte-equivalents. Hamming 7,4 coding reduces this to roughly 25,700 bytes *before* synchronization, framing, additional protection, and mechanical groove constraints. This is an upper-bound planning estimate, not measured physical storage capacity. The experimental software caps individual files at 2,048 bytes to constrain memory usage; multi-block, dropout-tolerant files are future work.

## Fun payloads

- Tiny self-contained games, BASIC-style programs or deterministic creative seeds.
- A 1 kB Haunted Toaster creature recipe; CANNON or lemonPRESS source integrity receipt.
- A record with a song on one side and computer-readable liner notes on the other.
- An encoded letter, a monochrome sprite, a tiny low-fidelity animation sequence.
- A sound sculpture that generates geometry as the record turns.

## Proof requirements for real records

1. Audio-line DAC/ADC tests, including varied levels and measured clock drift.
2. Per-block sync, speed correction, dropout handling, multiple framing packets.
3. Calibrated commercial blank and record lathe; separate encoder output is NOT cut-safe mastering.
4. Actual turntable -> appropriate RIAA preamp -> captured WAV -> validated checksum, measured error rate.
5. Material and stylus compatibility; no backyard heating of unknown PVC piping or fencing.

**Boundaries:** digital round trip != record recording; raw baud != recoverable payload; hash verifies recovered bytes, not physical persistence. Never use a prototype disc as the only copy of important data.
