# JAPANESE EDITION 001 — Codex implementation brief

## PR title

`JAPANESE EDITION 001 — native Japanese manga edition branch through declared language + style profiles`

## Base

Stack after `RELETTER BATCH 001 + MASK LETTERING 001` / PR #40.

## Objective

Make Japanese a first-class visible edition branch in LemonPRESS rather than an invisible translation pivot.

The implementation must take the already-frozen:

- exact PAGE INTAKE page carriers
- TRANSLATION RELAY source / Japanese pivot / returned-English witness
- BOX BINDING geometry
- RELETTER / MASK groundwork

and produce a **Japanese visual candidate** whose page lettering, orientation, role behavior, and sound/sign treatment are declared explicitly.

The Japanese candidate must preserve its full ancestry and must not self-admit as an edition, publication, or house release.

## Core laws

```text
LANGUAGE EDITION != SOURCE REPLACEMENT
JAPANESE EDITION != RETURNED ENGLISH
TRANSLATION ROUTE MUST REMAIN DECLARED
RENDERING != ADMISSION
STYLE != SEMANTIC AUTHORITY
VERTICAL TEXT != REORDERED NARRATIVE
SFX != CAPTION
SIGN TEXT != DIALOGUE
RETURN != ORIGINAL
LANGUAGE PASSAGE IS PART OF THE WORK
```

## Required architecture

```text
source PDF
  -> PAGE INTAKE 001
  -> exact page carriers
  -> TRANSLATION RELAY 001
  -> BOX BINDING 001
  -> JAPANESE EDITION PROFILE 001
  -> JAPANESE LETTERING 001
  -> JAPANESE_VISUAL_CANDIDATE
  -> optional RETURN VOICE 001
  -> returned-English descendant
```

The Japanese branch must consume the relay's `pivot` text directly. It must not regenerate Japanese from the returned-English layer.

## New schemas

### `schemas/manga-japanese-edition-profile-v0.schema.json`

Required fields:

- `schema`
- `id`
- `title`
- `language` = `ja`
- `readingDirectionPolicy`
- `orientationPolicies`
- `roleStyles`
- `surfacePolicies`
- `sfxPolicy`
- `signPolicy`
- `lineBreakPolicy`
- `fitPolicy`
- `authority`
- `laws`

Minimum orientation vocabulary:

```text
horizontal
vertical
vertical_preferred
horizontal_preferred
context_declared
```

Minimum role vocabulary must cover every existing relay role:

```text
brand
heading
subheading
caption
dialogue
sign
embedded_source_text
receipt
code
```

### `schemas/manga-japanese-edition-candidate-v0.schema.json`

Required fields:

- `schema`
- `status` = `JAPANESE_VISUAL_CANDIDATE`
- `title`
- `profileSha256`
- `relayCandidateId`
- `relayPivotTextSha256`
- `boxBindingCandidateId`
- `pageIntakeCandidateId`
- `renderTarget` = `pivot`
- `language` = `ja`
- `pageCount`
- `renderedParticularCount`
- `blockedParticulars`
- `pages`
- `transformations`
- `authority`
- `wrench`
- `laws`
- `candidateId`
- `candidateHash`

Authority must remain:

```json
{
  "editorialSelection": false,
  "editionAdmission": false,
  "publication": false,
  "houseRelease": false
}
```

### `schemas/manga-return-voice-v0.schema.json`

Required fields:

- `schema`
- `id`
- `title`
- `sourceJapaneseCandidateId`
- `mode`
- `linePolicy`
- `cadencePolicy`
- `driftPolicy`
- `authority`
- `laws`

Allowed initial modes:

```text
literal
manga-natural
drift-preserving
poetic
editorial
```

RETURN VOICE 001 is a declaration surface only in this PR unless an executable deterministic operation can be implemented without inventing language content.

## New tools

### `tools/manga_japanese_edition.py`

Responsibilities:

1. Validate Japanese edition profile.
2. Rebuild TRANSLATION RELAY candidate.
3. Rebuild BOX BINDING candidate.
4. Verify PAGE INTAKE parent identity.
5. Require render target = `pivot`.
6. Require each bound relay particular to resolve to its Japanese pivot text.
7. Render Japanese into declared regions according to role + orientation policy.
8. Carry exact source/pivot/return ancestry into the candidate.
9. Refuse unsupported glyph coverage, geometry overflow, or missing font assets.
10. Emit create-only:
   - `pages/page-XX.png`
   - `candidate.json`
   - `RECEIPT.md`
11. Support `compose` and `verify`.

### `tools/manga_return_voice.py`

For v0, prefer a declaration/verification tool over a language-generation tool.

Responsibilities:

1. Validate return profile.
2. Bind profile to one exact Japanese candidate.
3. Bind profile to the existing TRANSLATION RELAY returned-English witness.
4. Verify that no returned-English text silently replaces the Japanese candidate.
5. Emit a receipt describing the declared return mode and ancestry.
6. Do not synthesize prose unless a later explicit generation boundary is added.

## Typography requirement

Do not rely on Pillow's default ASCII font for the Japanese edition.

The implementation must use an explicitly declared Japanese-capable font asset or font family already available to the runtime/repository environment.

Rules:

```text
FONT ASSET MUST BE DECLARED
FONT FALLBACK MUST NOT BE SILENT
UNSUPPORTED GLYPH != SUBSTITUTE
FONT CHOICE != SEMANTIC AUTHORITY
```

If a Japanese-capable font cannot be deterministically established, the implementation must stop at a profile/candidate planning boundary rather than emit tofu boxes or silent substitutions.

Do not commit or redistribute font binaries merely to make the test pass.

## Japanese lettering behavior

### Dialogue

- vertical preferred
- centered inside declared dialogue region
- Japanese-native line breaking
- no horizontal squeeze to force fit
- overflow refuses

### Narration / caption

- horizontal or vertical according to declared profile
- rectangular caption treatment
- denser line wrapping permitted

### Embedded source text

- masked/polygon overlay when required
- orientation declared per binding
- preserve locality to the source object

### Sign

- context-declared orientation
- use existing polygon support where possible
- perspective reconstruction is not required in v0
- geometry must remain explicit

### SFX

SFX must not be treated as ordinary captions.

Initial policies:

```text
preserve_source
translate_visible
translate_with_gloss
dual_track
```

A Japanese SFX render must record:

- original source token
- Japanese pivot token
- visible token
- policy used
- exact region
- style transformation

## Japanese line-breaking rules

Implement a bounded v0 line-break policy.

Minimum requirements:

- no whitespace dependency for Japanese wrapping
- character-aware wrapping
- no silent text truncation
- explicit punctuation handling
- vertical mode orders characters top-to-bottom within each column
- column order must be declared
- no narrative/page-order mutation implied by vertical layout

Avoid pretending to implement full Japanese typography if the engine only supports a subset. Record the subset in the receipt.

## Founding profile

Add:

`works/the-last-stop-moved-japanese-edition-001/profile.json`

Suggested defaults:

```text
language: ja
page order: preserve source
dialogue: vertical_preferred
caption: horizontal_preferred
heading: horizontal_preferred
subheading: horizontal_preferred
receipt: horizontal
code: horizontal
embedded_source_text: context_declared
sign: context_declared
sfx: translate_visible
```

The profile must reference the existing:

- `works/the-last-stop-moved-translation-relay-001/relay.json`
- `works/the-last-stop-moved-box-binding-001/bindings.json`
- `works/the-last-stop-moved-page-intake-001/spec.json`

## Founding return profile

Add:

`works/the-last-stop-moved-return-voice-001/return-profile.json`

Default mode:

`drift-preserving`

The receipt must explain that the returned-English layer already exists in TRANSLATION RELAY 001 and is being declared as a descendant interpretation of the Japanese branch, not regenerated or substituted in-place.

## Target files

```text
schemas/
  manga-japanese-edition-profile-v0.schema.json
  manga-japanese-edition-candidate-v0.schema.json
  manga-return-voice-v0.schema.json
  manga-return-voice-candidate-v0.schema.json

tools/
  manga_japanese_edition.py
  manga_return_voice.py

tests/
  test_manga_japanese_edition.py
  test_manga_return_voice.py

docs/
  JAPANESE-EDITION-001.md

works/
  the-last-stop-moved-japanese-edition-001/
    profile.json
    README.md

  the-last-stop-moved-return-voice-001/
    return-profile.json
    README.md
```

Do not commit generated page PNGs unless existing LemonPRESS policy explicitly admits them as repository fixtures. Generated runtime output belongs under `out/`.

## CLI

```bash
npm run manga-japanese-edition -- compose \
  works/the-last-stop-moved-japanese-edition-001/profile.json \
  out/the-last-stop-moved-japanese-edition-001

npm run manga-japanese-edition -- verify \
  works/the-last-stop-moved-japanese-edition-001/profile.json \
  out/the-last-stop-moved-japanese-edition-001

npm run manga-return-voice -- compose \
  works/the-last-stop-moved-return-voice-001/return-profile.json \
  out/the-last-stop-moved-return-voice-001

npm run manga-return-voice -- verify \
  works/the-last-stop-moved-return-voice-001/return-profile.json \
  out/the-last-stop-moved-return-voice-001
```

## Tests

At minimum:

1. profile schema validates
2. candidate schema validates
3. return-profile schema validates
4. all 68 relay particulars resolve to Japanese pivot text
5. source English is never used as Japanese render text
6. returned English is never used as Japanese render text
7. every rendered particular remains bound to the same relay segment id
8. every rendered particular remains on the same page
9. parent page pixels survive unchanged outside declared masks/patches
10. unsupported Japanese glyph coverage refuses
11. missing declared font refuses
12. overflow refuses
13. vertical mode is deterministic
14. horizontal mode is deterministic
15. switching orientation changes candidate identity
16. switching SFX policy changes candidate identity
17. switching Japanese font declaration changes candidate identity
18. source PDF and PAGE INTAKE bundle remain unchanged
19. candidate has no editorial/publication/house authority
20. create-only output is idempotent
21. conflicting output refuses
22. verify independently rebuilds exact candidate + pixels
23. all 10 THE LAST STOP MOVED pages are accounted for
24. all 68 Japanese pivot particulars are accounted for
25. RETURN VOICE candidate is ancestry-only and performs no hidden language rewrite

## Execution phases

### Phase A — contracts

Implement schemas, profile parsing, ancestry binding, candidate hashing, and tests without rendering.

Gate: exact 68 / 68 Japanese pivot coverage.

### Phase B — Japanese horizontal renderer

Implement deterministic Japanese glyph rendering + character-aware wrapping.

Gate: no missing glyphs and exact replay.

### Phase C — vertical renderer

Implement vertical text for dialogue/context-declared regions.

Gate: deterministic layout and no page-order mutation.

### Phase D — SFX / sign / embedded modes

Reuse explicit polygon/mask geometry from the current visual stack.

Gate: all remaining art/sign surfaces have an explicit declared strategy.

### Phase E — full founding witness

Materialize the exact PAGE INTAKE source and run all ten pages.

Expected result:

```text
10 / 10 Japanese page candidates
68 / 68 Japanese pivot particulars represented
0 source-page mutations
0 hidden text substitutions
0 edition/publication authority
```

### Phase F — RETURN VOICE receipt

Bind the Japanese candidate to a declared `drift-preserving` return profile and the existing returned-English relay witness.

Do not claim the return voice has been generated from the rendered Japanese unless that generation is separately observed.

## Stop conditions

Refuse rather than improvise if any of these occurs:

- Japanese-capable font unavailable
- a pivot string contains unsupported glyphs
- a binding cannot fit under declared rules
- a segment is missing from relay / binding / page intake
- orientation policy is absent
- an art/sign region requires undeclared geometry
- a renderer would silently substitute glyphs
- a tool would need to reconstruct text outside a clipped source region
- a candidate would need to claim admission/publication to proceed

## Success condition

JAPANESE EDITION 001 is complete when LemonPRESS can truthfully say:

> These ten page candidates visibly render the exact declared Japanese pivot layer of THE LAST STOP MOVED, through a declared Japanese manga lettering profile, with every source relationship intact and without admitting the result as an edition.

RETURN VOICE 001 is complete when LemonPRESS can truthfully say:

> This returned-English descendant is bound to that Japanese edition branch by an explicit return profile, and the system preserves the fact that the work passed through Japanese rather than collapsing the path back into the original English.
