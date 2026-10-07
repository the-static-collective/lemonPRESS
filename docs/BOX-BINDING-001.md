# BOX BINDING 001 - all language particulars acquire declared pixel regions

**Status:** executable v0  
**Output state:** BOUND_CANDIDATE only  
**Stacked after:** PAGE INTAKE 001 / PR #36

BOX BINDING 001 joins the semantic relay to the page-pixel carriers without changing either.

```text
TRANSLATION RELAY
68 text particulars
      +
PAGE INTAKE
10 exact page-pixel identities
      +
declared visible rectangles
      |
      v
BOX BINDING
one particular -> one non-overlapping region
      |
      +--> solid surfaces may enter RELETTER v0
      |
      +--> art/sign surfaces stop for explicit render strategy
```

## Laws

```text
TEXT ID != PIXEL REGION
BOX != SEMANTIC TRUTH
BINDING != SELECTION
BINDING != MASK
GEOMETRY != RENDER AUTHORITY
ONE PARTICULAR == ONE DECLARED REGION
CLIPPED SOURCE REMAINS CLIPPED
ART SURFACE REQUIRES EXPLICIT RENDER STRATEGY
ALL PARTICULARS MUST BE ACCOUNTED FOR
BOX BINDING != ADMISSION
```

## What v0 proves

- every relay particular appears exactly once
- every binding stays on the relay's declared page
- every rectangle stays inside the exact intake dimensions
- no two text regions overlap on a page
- each binding carries the exact source page raw-pixel and PNG identities
- returned text, locus, role, and clipped-state remain attached
- complete coverage is required; omission refuses

No OCR is performed. No text detector is claimed. The boxes are declarations from visual observation of the exact rendered pages.

## Surface classes

`solid-dark` and `solid-light` are mechanically eligible for RELETTER 001's current solid-patch renderer.

`art` and `sign` are deliberate stop states. Repainting those rectangles with a flat patch would destroy source image structure or perspective, so they require a separately declared render strategy.

Surface class is not a semantic claim about the whole panel. It is a rendering constraint on the bounded text region.

## THE LAST STOP MOVED

The founding witness binds all 68 Translation Relay particulars across all 10 PAGE INTAKE carriers.

Current inventory:

- solid-dark: 34
- solid-light: 25
- art: 6
- sign: 3
- directly eligible for RELETTER v0: 59
- explicit render-strategy blockers: 9

That means the issue is no longer waiting on text geometry. The remaining hard seam is narrow and visible: six text regions sit directly on art and three live on physical signs.

## CLI

```bash
npm run manga-box-binding -- works/the-last-stop-moved-box-binding-001/bindings.json
npm run manga-box-binding -- works/the-last-stop-moved-box-binding-001/bindings.json --verify
```

Outputs are create-only `candidate.json` and `BOX-RECEIPT.md`.

## Next aperture

RELETTER BATCH 001 can now generate the 59 solid-surface returned-English replacements immediately from the materialized PAGE INTAKE packet.

The nine art/sign regions should not be flattened. They need one bounded next primitive: MASK LETTERING 001, with declared source mask and geometric transform rather than hidden inpainting.
