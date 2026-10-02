# SUNO PANTRY INTAKE 001 — Declared Local Export

SUNO PANTRY INTAKE 001 gives lemonPRESS a practical path for exported Suno stems, dramatic readings, mixes, and ambience to enter PRESS MOUTH without pretending that a local file proves remote provider state.

## Founding law

> DECLARED ORIGIN != REMOTE VERIFICATION

A human may know that a WAV came from Suno because they just exported it.
lemonPRESS can verify the local bytes in front of it.
Those are different facts.

PANTRY preserves the distinction.

~~~text
SUNO
  |
human export
  |
local audio body + declaration
  |
  v
SUNO PANTRY 001
  |
  +-- hash exact local bytes
  +-- bind declared roles
  +-- preserve provider-origin uncertainty
  +-- emit local witness receipt
  |
  v
PRESS MOUTH
  |
  v
lemonpress/audio-parcel/v0
  authority: declared-local-export
~~~

## What lemonPRESS actually claims

For a Pantry parcel, lemonPRESS may truthfully say:

- these exact local bytes were witnessed;
- their SHA-256 and byte length were computed;
- a declaration identified them as a Suno export;
- the declaration assigned bounded roles;
- PRESS MOUTH admitted the relation.

It may not silently upgrade that into:

- independent verification of Suno's servers;
- proof of generation time;
- proof of a provider track ID;
- proof that a stem is musically what its filename says;
- source authority equivalent to an Autodiscography Vault verified receipt.

~~~text
LOCAL BYTE IDENTITY != PROVIDER ATTESTATION
BODY != ROLE
PANTRY ADMISSION != PUBLICATION
~~~

## Single-file intake

Create a declaration:

~~~json
{
  "schema": "lemonpress/suno-pantry-declaration/v0",
  "provider": "suno",
  "export_kind": "dramatic-reading",
  "roles": ["narration", "dramatic-reading"],
  "title": "Chapter One reading",
  "provider_track_id": "optional-declared-id",
  "note": "optional human note"
}
~~~

Then admit it:

~~~bash
npm run pantry -- admit \
  --asset ./exports/chapter-01.wav \
  --declaration ./exports/chapter-01.json \
  --out ./out/suno-pantry
~~~

The intake writes a local witness receipt and then feeds the body + receipt through PRESS MOUTH.

The audio body is not copied into the parcel.

## Export kinds

PANTRY 001 recognizes:

~~~text
stem
dramatic-reading
full-mix
ambient
other
~~~

A dramatic-reading export must declare at least one of:

~~~text
dramatic-reading
narration
~~~

Roles remain open-ended bounded identifiers so the house can grow without changing Composer core.

Useful initial roles include:

~~~text
narration
dramatic-reading
music-bed
rhythm
motif-source
chapter-transition
atmosphere
ghost
bass
harmony
percussion
voice-fragment
~~~

PRESS MOUTH will only admit roles carried by the Pantry witness receipt.

## Batch intake

For a large export folder, put the manifest beside or above the files:

~~~json
{
  "schema": "lemonpress/suno-pantry-batch/v0",
  "items": [
    {
      "asset": "stems/drums.wav",
      "export_kind": "stem",
      "roles": ["rhythm", "percussion"],
      "title": "Hand drums"
    },
    {
      "asset": "stems/jazz.wav",
      "export_kind": "stem",
      "roles": ["music-bed", "motif-source"],
      "title": "Smooth mutation jazz"
    },
    {
      "asset": "readings/ch01.wav",
      "export_kind": "dramatic-reading",
      "roles": ["narration", "dramatic-reading"]
    }
  ]
}
~~~

Run:

~~~bash
npm run pantry -- batch \
  --manifest ./exports/pantry.json \
  --out ./out/suno-pantry
~~~

Batch asset paths must be relative to the manifest and may not escape the manifest directory.

The batch keeps valid admissions even when another item refuses. It then writes:

~~~text
batch-receipt.json
~~~

with admitted items and refusals kept distinct.

This is intentional resumability, not partial-success laundering.

## Output topology

~~~text
out/suno-pantry/
  witnesses/
    <witness-id>.suno-pantry.receipt.json
  parcels/
    lp-audio-.../
      parcel.json
      sources.json
      lineage.json
      projections.json
      receipt.json
  batch-receipt.json
~~~

The original audio remains wherever the operator keeps the pantry.

## Composer crossing

After intake, Audio Composer needs no Suno-specific logic.

~~~text
SUNO STEM -----------\
SUNO READING ----------> PANTRY -> PRESS MOUTH -> AudioParcel
SUNO AMBIENCE --------/                         |
                                                 v
                                          AUDIO COMPOSER
~~~

This means one edition may combine:

- Vault-verified recordings;
- Phonograph resolved-performance projections;
- Pantry-declared Suno stems;
- Pantry-declared Suno dramatic readings.

Each track retains its inherited authority in the resolved edition.

## Infinite-stem workflow

The intended practical loop is:

~~~text
GENERATE MANY
    |
EXPORT MANY
    |
CLASSIFY LIGHTLY
    |
PANTRY BATCH
    |
PARCEL LIBRARY
    |
COMPOSE SELECTIVELY
~~~

The point is not to make every generated stem important.

The point is to make abundance cheap while keeping selection explicit.

## What remains closed

PANTRY 001 does not:

- download from Suno;
- inspect Suno sessions, cookies, tokens, or hidden endpoints;
- claim remote provenance;
- automatically decide literary meaning;
- publish anything;
- render an audiobook;
- copy the pantry corpus into Git.

## Next crossing

With PANTRY + PRESS MOUTH + AUDIO COMPOSER in place, the remaining mechanical gap to a first real audiobook specimen is AUDIO RENDERER 001:

~~~text
ResolvedAudioEdition
        +
SHA-resolved local audio bodies
        |
        v
AUDIO RENDERER 001
        |
        v
WAV / FLAC / MP3 / M4B projection + receipt
~~~

Renderer authority remains projection-only.
