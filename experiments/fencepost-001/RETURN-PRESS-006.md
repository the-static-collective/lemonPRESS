# RETURN PRESS-006 — THE RECORD THAT GROWS A NEW RECORD

**Digital proof (implemented):** An append-only, deliberately synthetic participation journal compiles into two distinct playable WAV remixes, a new hashed AUDIO KEY capsule for the later edition, an immutable source WAV, a causal-cut lineage, a held LemonPRESS center-label draft, and exact cold-replay receipts. No physical record has been produced or any real-world encounter logged.

## The insight

A physical record has a stable body and identifier. It cannot independently observe who listened to it or learn new experiences. **Only separately consented, attributable receipts** can append new history. They can accumulate without modifying the historical record or claiming that a turntable sensed an event it did not sense.

Those receipts can eventually inform a *new independently licensed derivative edition*. The new pressing has its own hash, date, mastering and audio, and points to the preserved first pressing.

    RECORD A / fixed AUDIO KEY
          |
    opted-in events and explicitly authored contributions
          |
    append-only local encounter / ledger
          |                            non-consented private data -> EXCLUDED
    review, refusal and material permissions
          |
    exact causal cut / authorized motif set
          |
    REMIX COMPILER -> separate recorded sound / candidate score
          |
    AUDIO KEY B -> hash & public doors
          |
    LemonPRESS edition packet: DRAFT / NOT RELEASED
          |
    FENCEPOST physical pressing: NOT IMPLEMENTED

## Actual native executable

Node.js 22. All sound is synthesized here from mathematical oscillators. No user music is downloaded, copied or included.

    node --test experiments/fencepost-001/return-press.test.mjs
    node experiments/fencepost-001/return-press.mjs demo /tmp/return-press-demo
    node experiments/fencepost-001/return-press.mjs verify /tmp/return-press-demo

The generated directory contains the original synthetic 6/8 song, an earlier remix, a later remix, an AUDIO KEY digital capsule of the later remix, a held center-label SVG, a rights-scoped synthetic event journal, a lineage JSON and receipt. GitHub CI executes these commands and attaches the whole bundle as an artifact.

## Actual tested event semantics

Event types:
- `listen`: an explicitly opted-in listening report; may affect the displayed history count **but never automatically changes the music**.
- `visit`: consented world-room report. **Synthetic only**; not an assertion about Revival / Reality 2.0 / Pokémon actual state.
- `propose`: an author supplies a named creative motif and an exact `DEMO_REMIX_ONLY` license.
- `accept`: a distinct synthetic curator explicitly accepts the proposed motif within the same narrow scope.
- `refuse`: the contribution author or accepting curator withdraws future use, preserving the prior receipt.

All events are validated through a hash-linked, append-only local journal. **Hash chaining does not establish signatures, human identities, consent authenticity, or independence.** Those need source-owned identity and verification systems before real intake.

Demo causal cuts:
- Cut 4: accepted glass-bell contribution; listen and visit reports retained separately.
- Cut 6: a second bass motif has been accepted.
- Cut 8: that motif's author withdraws it from **future** output. The prior historical cut is not erased.
- Cut 11: a later echo contribution is accepted; the new sonic projection differs from cut 4.

The program renders the same eight-second-scale 6/8 source and creates genuinely different PCM audio for cuts 4 and 11, without pretending either contains live performances. Re-running the compiler generates byte-identical WAVs and receipts.

The later remix's AUDIO KEY capsule references the exact new audio and three public **proposal-only** doors: CANNON candidate, Haunted Toaster VisualScore candidate, Revival text-room preview. The referenced tools have not been run. The old key and old audio remain independent.

## Cross-project seam — deliberately not live

| Source owner | Role in future real crossing | What today's demonstration DOES NOT claim |
| --- | --- | --- |
| Band Runtime / Groove Rooms | Consented participant contribution and encounter history | Live encounter or independently recorded performers |
| TranchNode | Exact lineage, disagreement, refusal, causal replay | Adoption as native shared history |
| planZ | Open remix plan, next human review and hold gates | Scheduled execution or plan authority |
| Static Live | Performance packet and alternative mix from an actual roster | Actual performance by humans |
| Haunted Toaster | Derive a VisualScore from an approved remix | Rendered or published music video |
| AUDIO KEY / FENCEPOST | Physical ID and eventual record manufacture | A record that has actually been cut or pressed |
| LemonPRESS | Physical publishing gate, artist rights, printed sleeve | Manufacturing order or public release |
| CANNON | Verify evidence and optionally select an exact candidate | Automatic owner admission or executable permission |
| Revival, Reality 2.0 and creature worlds | Explicitly authorized experiences keyed by edition | Private-world access, user rights or real-world observation |

## Interesting extensions

1. **Community album as season:** a record helps people discover a local concert, food table, or volunteer task; returned receipts are separately consented and validated. A later, licensed compilation can feature actual authorized contributions. The act of listening never becomes a duty or involuntary data harvest.
2. **Autonomous remix nursery:** planZ can propose alternate arrangements; Haunted Toaster can render candidate visual organisms; the artist keeps or rejects. **No automatic source admission.**
3. **Needle remembers surface:** stylus metrology measures wear on a well-characterized test record; FENCEPOST can report physical changes over time, not invent human experiences.
4. **Generative collector edition:** an AUDIO KEY opens a tiny signed recipe. Authorized physical editions may use a unique musical arrangement while retaining source ancestry. A copied public hash is not a unique ownership token.
5. **Alternative live version:** Static Live can create a performance packet for a new arrangement; live participants are attributed only where supported by event evidence.

## Hard barriers before actual release

- Real masters and each contributor's independently verifiable permission to sample/transform, distribute and press.
- Authenticated participant identity, privacy, revocation, consent and public attribution rules.
- Source-owned event imports; no synthetic events presented as real history.
- Appropriate mastering, accurate physical record-cutting/pressing equipment, emissions and material controls.
- Release-level decisions for formerly licensed-but-later-withdrawn contributions. Earlier historical snapshots do not automatically establish continuing reproduction rights.
- Signed edition manifests and receiver-local action permissions. The AUDIO KEY remains a **public address**, not a bearer privilege.

**HISTORY != LICENSE · LISTEN != CONSENT TO REMIX · ACCEPTANCE != ETERNAL PERMISSION · MASTER != DESCENDANT · REFUSAL != ERASURE · GENERATED MUSIC != HUMAN PERFORMANCE.**
