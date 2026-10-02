# AUDIO COMPOSER 001 — Resolve Before Rendering

AUDIO COMPOSER 001 is lemonPRESS's first executable audio-composition seam.

It consumes:

- one manuscript body;
- one explicit composition declaration;
- one or more verified `lemonpress/audio-parcel/v0` directories.

It emits:

- `audio-edition-score.json`;
- `resolved-audio-edition.json`;
- `receipt.json`.

It does not render audio.

## Founding law

> COMPOSITION != RENDERING

The declaration proposes structure.
The composer verifies and resolves structure.
A later renderer projects that resolved structure into sound.

The renderer may not silently become an editor.

~~~text
MANUSCRIPT
    +
AUDIO PARCELS
    +
COMPOSITION DECLARATION
        |
        v
AUDIO COMPOSER 001
        |
        +-- bind manuscript SHA-256
        +-- verify parcel PRESS MOUTH receipts
        +-- verify admitted parcel roles
        +-- resolve segment order
        +-- resolve crossfades / gaps / cuts
        +-- resolve layer timing
        +-- resolve gain / trim / ducking directives
        |
        v
AudioEditionScore
        |
        v
ResolvedAudioEdition
        |
        X  renderer boundary
~~~

## Why the declaration is explicit

Composer 001 intentionally does not read prose and pretend an automatically inferred soundtrack is authorial fact.

The declaration is a proposal surface where a human, an AI collaborator, a manuscript-analysis tool, or a later Composer may suggest:

- which manuscript range a segment belongs to;
- which parcel plays which role;
- gain;
- trim;
- layer timing;
- ducking relationships;
- transition behavior.

Those proposals become executable only after the resolver verifies their referenced manuscript and parcel identities.

~~~text
INFERENCE != ADMISSION
CUE != SOURCE TRUTH
ROLE != BODY
RESOLUTION != RENDER
~~~

## Composition declaration

Example:

~~~json
{
  "schema": "lemonpress/audio-composition-declaration/v0",
  "work_id": "example-book",
  "edition_id": "mutation-jazz-001",
  "profile": "mutation-jazz",
  "segments": [
    {
      "id": "opening",
      "sequence": 0,
      "duration_seconds": 42,
      "manuscript": {
        "start_line": 1,
        "end_line": 18
      },
      "layers": [
        {
          "parcel_id": "lp-audio-...",
          "role": "narration",
          "gain_db": -2
        },
        {
          "parcel_id": "lp-audio-...",
          "role": "music-bed",
          "gain_db": -24,
          "duck_under_roles": ["narration"]
        },
        {
          "parcel_id": "lp-audio-...",
          "role": "motif-source",
          "start_offset_seconds": 28,
          "duration_seconds": 9,
          "gain_db": -31
        }
      ],
      "transition_after": {
        "kind": "crossfade",
        "duration_seconds": 4
      }
    }
  ]
}
~~~

## Resolution

The resolved edition contains absolute renderer-neutral timing.

A crossfade is resolved before the renderer sees it.
A gap is resolved before the renderer sees it.
A parcel's admitted role is checked before it can occupy that role in the edition.

The renderer contract currently states:

~~~json
{
  "authority": "projection-only",
  "may_reinterpret_structure": false,
  "may_invent_layers": false,
  "media_resolution": "sha256"
}
~~~

A renderer may choose how to implement a declared gain curve or codec projection only within its later explicit render contract. It does not get to change chapter order, replace a parcel, invent a motif, or silently rewrite a transition.

## Determinism

Given the same:

- manuscript bytes;
- declaration bytes;
- parcel manifests;
- upstream PRESS MOUTH receipts;

the Composer emits the same score identity and resolved structural decisions.

Parcel input order does not change the score hash.

## CLI

~~~bash
npm run audio -- compose \
  --manuscript ./book.md \
  --declaration ./composition.json \
  --parcels ./parcels/lp-audio-one,./parcels/lp-audio-two \
  --out ./out/audio-editions
~~~

The output appears beneath:

~~~text
out/audio-editions/<work-id>/<edition-id>/
  audio-edition-score.json
  resolved-audio-edition.json
  receipt.json
~~~

## Current role vocabulary

The schema does not hard-code a closed vocabulary.

PRESS MOUTH parcels may carry bounded roles such as:

~~~text
narration
dramatic-reading
music-bed
rhythm
motif-source
chapter-transition
atmosphere
ghost
~~~

Composer may use only roles already admitted on the parcel.

This is deliberate: a future Suno stem or dramatic-reading adapter can enter through PRESS MOUTH without changing Composer's core.

## WRENCH receipt

A completed composition crossing records:

~~~text
INPUT
TRANSFORMATION
OUTPUT
RESIDUAL
LOSS
UNKNOWN
STOP
~~~

Composer 001 stops because the next crossing is genuinely different.

The renderer will need to decide such projection-specific matters as:

- audio engine;
- sample rate;
- channel layout;
- loudness target;
- codec;
- limiter;
- fades and ducking implementation;
- output chapter containers.

Those are real decisions and deserve their own receipt.

## What remains closed

AUDIO COMPOSER 001 does not:

- generate narration;
- analyze prose semantically;
- select stems autonomously;
- copy media bodies;
- mix WAV files;
- master loudness;
- encode MP3/FLAC/M4B;
- publish the edition;
- promote a composition proposal into manuscript authority.

## Next doors

This slice intentionally opens three independent next doors:

1. **SUNO PANTRY INTAKE** — admit manually exported stems and dramatic readings as bounded parcels without pretending they came through Vault acquisition.
2. **AUDIO RENDERER 001** — resolve parcel SHA-256 identities to local bodies and execute the already-resolved edition without editorial invention.
3. **COMPOSER MUTATION 002** — propose recurring motifs and future-rearview mutations while keeping proposal separate from resolution.

The first two together are enough to produce a real lemonPRESS audiobook specimen.
