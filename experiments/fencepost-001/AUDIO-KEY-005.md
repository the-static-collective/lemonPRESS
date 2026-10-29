# FENCEPOST-005 — AUDIO KEY (the playable link-wallet capsule)

**Status: tested digital FSK intro/outro capsule; NO continuous in-song watermark, physical record, signature, or execution.**

## Design

A record carries **(1) an overt machine-readable opening marker**, **(2) the untouched audio PCM**, and **(3) an identical ending marker**. Each marker encodes a four-byte magic string and a 32-byte SHA-256 digest of an exact, canonical **manifest**. The 300-baud FSK modem is GROOVEVAULT-004; its carrier uses audible 1200/2400 Hz tones. Short silence isolates the two markers from the music. This is not yet a record-mastering-ready WAV.

The manifest points to *inert proposed doors* to independent worlds. The scanner compares the recovered ID against a **local known manifest** and checks its unmodified source PCM's hash. The scanner returns proposals only; **it runs no arbitrary code and grants no privileges**.

    DISK/CATALOG MANIFEST (canonical, with source PCM SHA-256)
             |                   |
             |  SHA256(manifest) |
             v                   v
           PUBLIC CONTENT ADDRESS
             |            |
        FSK INTRO       FSK OUTRO
             \            /
         ORIGINAL SONG (unchanged PCM)
                 |
          DIGITAL SCANNER
                 |
          MATCH BOTH MARKERS
                 |
       LOOKUP KNOWN MANIFEST
                 |
       RECHECK SOURCE PCM HASH
                 |
       READ-ONLY WORLD DOOR MENU
                 |
         HUMAN-CHOSEN OPEN/PREVIEW
           (not implemented)

### Purpose of four separate identifiers

- **Master source hash**: exact original mono PCM used to create this test capsule. Independent of later header/outro additions.
- **Capsule ID**: SHA-256 digest of canonical manifest bytes; content addressing, **not** an authentication token.
- **Carrier WAV digest**: SHA-256 of the actual resulting WAV, stored in the standalone output receipt. Changes with markers and layout.
- **Acoustic fingerprint** (future): robust recognition of the underlying song after lossy playback, *not a cryptographic equality proof*. Chromaprint/AcoustID is relevant prior art: https://acoustid.org/chromaprint

**A hash is not a signing key.** Anyone who hears the marker can replay it, and anyone can author a different manifest. A signed manifest with a verified publisher trust anchor is needed before attributing the artifact to an owner. Even successful signature verification must never by itself authorize receiver effects, spending, private data reads, or code execution.

## Cross-world route semantics

Example proof routes (all synthetic, untrusted and non-actuating):

| World | Safe proposed door | Prohibited inferred authority |
| --- | --- | --- |
| Revival | Open pinned Genesis 1:1 demonstration room | Change canonical Scripture witness |
| Reality 2.0 | Preview a Waseca room candidate | Publish/moderate a real submission |
| Creature-world (Pokemon-inspired exploration) | Propose a fictional starter-creature demo | Mint ownership or modify an actual game account |
| CANNON | Inspect a candidate receipt | Select/admit canon or run physical hardware |
| Haunted Toaster | Preview a VisualScore demo | KEEP, mutate or publish without consent |
| lemonPRESS | Inspect a held publication candidate | Print, charge, mail or grant distribution rights |

This code creates **no live adapters** to those repositories, Supabase, games, user accounts or hardware. A future receiver must independently decide whether it recognizes the manifest publisher, whether the specific user is authorized, and whether a stated action is allowable. An audible marker is a **public link**, never a bearer capability secret.

## Actual code invocation: local demo interpreter, not privileges

The `world-doors.mjs` interpreter recognizes **only five hard-coded local fixtures** and runs their bounded JSON-view generators. This is actual deterministic Node code reached via the captured sound ID, but not any source-provided code, live game logic or external service. Nothing touches Revival, Reality 2.0's database, a Pokémon service, CANNON admission or Haunted Toaster's real render path.

    node experiments/fencepost-001/world-doors.mjs list /tmp/audio-key-demo/audio-capsule.wav /tmp/audio-key-demo/manifest.json
    node experiments/fencepost-001/world-doors.mjs visit /tmp/audio-key-demo/audio-capsule.wav /tmp/audio-key-demo/manifest.json creature-world OPEN_LOCAL_DEMO
    node --test experiments/fencepost-001/world-doors.test.mjs

**The explicit `OPEN_LOCAL_DEMO` argument is a simulation switch, not identity or security authentication.** A real receiver would require separately verified owner signing keys, a scoped user grant, replay/idempotency rules and an auditable executable package pinned to its approved publisher. The audio capsule should never contain secrets, shell commands or transferable capabilities.

## Why NOT just one ultrasonic frequency?

One frequency is mostly a recognizable tone, not a reliable ID. An inaudible watermark could use spread-spectrum coding, repeated synchronization blocks, psychoacoustic masking, and timebase compensation. Analog vinyl adds wow, flutter, scratches, noise, distortion, and filtering. A strong robust audio watermark suitable for repeated detection through a record player is **research work**, not implemented. The usable first experiment is explicit header/outro FSK, with a fingerprint-based *fallback* for song identity.

Read [Nadeau & Sharma's analog-playback watermark research](https://hajim.rochester.edu/ece/sites/gsharma/papers/NadeauAnalogPlaybkAudioWMSynchTIFS2017.pdf). It directly targets synchronization drift during analog playback. Chromaprint recognizes near-identical recordings but is not a signature or tamper-proof integrity primitive.

## Reproduce

Requires Node.js 22, no external dependencies. Run from the lemonPRESS repository checkout:

    node experiments/fencepost-001/audio-key.mjs demo /tmp/audio-key-demo
    node experiments/fencepost-001/audio-key.mjs verify /tmp/audio-key-demo
    node --test experiments/fencepost-001/audio-key.test.mjs

With an actual **canonical 48 kHz, 16-bit, mono PCM WAV**:

    node experiments/fencepost-001/audio-key.mjs build my-song.wav my-manifest.json /tmp/my-audio-key
    node experiments/fencepost-001/audio-key.mjs scan /tmp/my-audio-key/audio-capsule.wav /tmp/my-audio-key/manifest.json

The manifest must name the input source's exact PCM SHA-256, a work ID, rights state, and a bounded list of supported inert world doors. The CLI demo generates a deterministic synthetic tone and matching demo manifest.

Outputs: audio-capsule.wav; manifest.json; scan-proposals.json; receipt.json. Verify checks file hashes and replays the digital scan.

### What counts as proof

**Proven by the running digital program:** two identical marker frames are decoded from the planned source WAV, recovered IDs match, a known manifest's hash resolves, source PCM is byte-identical, and proposed world doors remain HOLD.

**Not proven:** reliable physical vinyl playback, actual watermark hidden in music, signature validity, live Reality 2.0 / Revival / Pokemon integrations, code execution, actual sound quality or physical-record groove manufacturing.

Next physical proof: short overt code recorded on a professional test blank, played through a known phono preamp and captured digitally, with independent checksum validation and measured failure rate. If physical modulation fails due to speed drift, use pilot-tone timebase recovery, repeated packets and shorter blocks before claiming physical functionality.

**Identity ≠ authority · Carrier ≠ source · Watermark ≠ signature · Recognition ≠ consent · Invitation ≠ execution.**
