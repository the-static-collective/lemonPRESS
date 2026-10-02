# PRESS MOUTH 001 — Audio Parcel Ingestion

PRESS MOUTH 001 gives lemonPRESS one bounded way to eat audio-family outputs without absorbing the authority of the systems that produced them.

## Founding law

> THE MOUTH MAY DIGEST A RELATION. IT MAY NOT COUNTERFEIT THE SOURCE.

The first admitted upstream systems are:

- Autodiscography Vault;
- The Haunted Phonograph.

The mouth does not copy the large media body into Git. It verifies the local body, binds its SHA-256 identity to the upstream receipt, extracts only the lineage needed by lemonPRESS, and writes a small parcel.

~~~text
upstream system
      |
receipt + local body
      |
      v
PRESS MOUTH 001
      |
      +-- verify body identity
      +-- verify upstream state
      +-- classify inherited authority
      +-- bind lineage
      +-- refuse body copying
      |
      v
lemonpress/audio-parcel/v0
~~~

## Authority mapping

### Autodiscography Vault

A Vault input is admitted only when:

- receipt schemaVersion is 1;
- receipt state is verified;
- local body SHA-256 equals the receipt SHA-256;
- local byte length equals the receipt byte length.

The parcel authority is:

~~~text
verified-source
~~~

This means only that the parcel points truthfully to a byte body verified by the Vault receipt. It does not make lemonPRESS the preservation authority.

### Haunted Phonograph

A Phonograph input is admitted only when:

- receipt schema is haunted-phonograph/receipt/v1;
- receipt status is completed;
- sourceHash, scoreHash, and resolvedPerformanceHash are present;
- one declared output projection matches the local body by SHA-256 and, when supplied, byte length.

The parcel authority is:

~~~text
resolved-performance-projection
~~~

The projection remains downstream of the Phonograph resolved performance. lemonPRESS does not relabel it as source evidence.

Current specimen receipts expose MIDI as the projection. Future WAV/stem renderers can use the same mouth when their receipts expose byte-addressed projection entries. When multiple projections match, the caller must name the projection path rather than allowing ambiguous selection.

## Parcel shape

Each ingestion writes:

~~~text
<out>/<parcel-id>/
  parcel.json
  sources.json
  lineage.json
  projections.json
  receipt.json
~~~

It intentionally does not write the WAV, MIDI, stem, or other large media body.

The body is resolved externally by SHA-256.

~~~text
CATALOG ENTRY != FILE COPY
ADMISSION != DUPLICATION
UPSTREAM RECEIPT != DOWNSTREAM AUTHORITY
MIX != COMPOSITION
~~~

## CLI

Requires Node.js 22 or newer.

Vault example:

~~~bash
npm run mouth -- ingest \
  --source-system autodiscography-vault \
  --asset /vault/assets/track/audio_wav.wav \
  --receipt /vault/receipts/one-receipt.json \
  --out ./out/audio-parcels \
  --roles music-bed,motif-source
~~~

Phonograph example:

~~~bash
npm run mouth -- ingest \
  --source-system haunted-phonograph \
  --asset ../the-haunted-phonography/out/specimen-001.mid \
  --receipt ../the-haunted-phonography/out/specimen-001.receipt.json \
  --out ./out/audio-parcels \
  --roles mutation-bed
~~~

If a receipt contains more than one eligible projection:

~~~bash
npm run mouth -- ingest \
  --source-system haunted-phonograph \
  --asset ./render.wav \
  --receipt ./render.receipt.json \
  --projection outputs.master \
  --out ./out/audio-parcels
~~~

Inspect a completed parcel:

~~~bash
npm run mouth -- inspect ./out/audio-parcels/lp-audio-...
~~~

Run the bounded verification suite:

~~~bash
npm test
~~~

## WRENCH receipt

Every completed ingestion leaves a PRESS MOUTH receipt answering:

- INPUT;
- TRANSFORMATION;
- OUTPUT;
- RESIDUAL;
- LOSS;
- UNKNOWN;
- STOP.

The first mouth stops deliberately before composition.

A later Audio Composer may consume audio parcels, manuscripts, narration takes, Suno stem pantry material, and book-specific rules. That will be a separate crossing with a separate authority surface.

## What remains closed

PRESS MOUTH 001 does not:

- publish a work;
- declare editorial admission;
- copy corpus media into Git;
- generate an audiobook;
- mix stems;
- mutate upstream evidence;
- promote a Phonograph proposal into source truth;
- weaken Vault verification;
- infer missing lineage.

The next useful slice is AUDIO COMPOSER 001 after this mouth has proved it can ingest real specimens from both upstream systems.
