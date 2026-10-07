# TRANSLATION RELAY 001 — language as a declared remix surface

Status: executable v0
Output state: CANDIDATE only
Stacked after: REMIX SEQUENCE 001 / PR #27

TRANSLATION RELAY 001 sends an already-declared text layer through a declared language route and keeps every stage: source English -> frozen Japanese witness -> returned English descendant -> explicit re-letter/selection/admission later.

## Laws

TRANSLATION != REPLACEMENT
RETURN != ORIGINAL
DRIFT != ERROR
LOSS MUST REMAIN VISIBLE
SOURCE SURVIVES RELAY
CLIPPED TEXT != LICENSE TO RECONSTRUCT
LANGUAGE ROUTE IS DECLARED
RENDERING != ADMISSION

## Manga relation

parcel/page = identity + source pixels
pixel remix = visual recomposition
translation relay = text-layer recomposition
sequence = reading-order recomposition
press = explicit admitted issue/page assembly

The relay does not call a translator. Translation generation stays outside the deterministic core. The declaration freezes source, Japanese pivot, returned English, page/locus, clipped-state, and drift labels. LemonPRESS validates and hashes what actually crossed.

## Founding witness

THE LAST STOP MOVED — Issue Cut 001 is frozen as 68 visible text particulars across 10 pages. Cropped fragments remain clipped; the machine is not licensed to reconstruct text outside the crop.

Notable returns include: prophecy -> omen; unclaimed -> belonging to no one; THE PAUSE -> THE INTERVAL; threshold -> boundary; SPINE -> BACKBONE.

These are descendant readings, not silent corrections.

## CLI

python3 tools/manga_translation_relay.py works/the-last-stop-moved-translation-relay-001/relay.json
python3 tools/manga_translation_relay.py works/the-last-stop-moved-translation-relay-001/relay.json --verify

Outputs are create-only candidate.json, RETURN.md, and RECEIPT.md. Identical replay is idempotent; conflicting existing bytes refuse.

## Next aperture

RELETTER 001 should bind a selected relay candidate to explicit page text boxes/balloons and render a new visual candidate without source mutation. The renderer should consume the relay; it should not own translation.
