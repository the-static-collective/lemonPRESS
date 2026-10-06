# MANGA PRESS 001 — Page, issue, print, and performance handoff

An admitted work can now acquire an independently admitted manga edition, an
ordered issue of independently hashed pages, an exact print plan and structural
proof, and a bounded performance handoff. Manga is an **edition/form grammar**;
the house lanes remain physical, digital, crawler, and archive.

This experiment starts at `press/physical` commit
`c07c7972e937b7ef443b412869c9cef4915eebf8`, the merged Road Grammar 001 descendant
of Physical Composer, Press Gate, and Press Run. The separately drafted Press
Mouth → Audio Composer → Suno Pantry stack was inspected at
`6f97f8c6c79397a557ce66e3a6045ee689ad66af`; its sorted-key compact JSON/SHA-256
convention is retained, without merging a separate production floor.

## Run the founding specimen

Python 3.10+ and npm are sufficient for composition. Runtime has no third-party
dependencies. Tests additionally use `requirements-test.txt`.

```sh
python3 -m pip install -r requirements-test.txt
npm test
npm run manga -- compose works/manga-press-specimen/manga/001/edition.yaml out/issue
npm run manga -- verify works/manga-press-specimen/manga/001/edition.yaml out/issue
npm run manga -- gate works/manga-press-specimen/manga/001/edition.yaml out/packet
python3 tools/press_gate.py check out/packet
npm run manga -- --root out/packet/artifacts/evidence verify out/packet/manga/edition.json out/packet/manga
```

The `edition.yaml` and `work.yaml` carriers use JSON, which is valid YAML. This
small vertical deliberately accepts that explicit subset, without YAML scalar
coercion or a new parser. Arbitrary existing YAML needs an explicit conversion;
the composer never pulls or rewrites a latest source.

The founding specimen is **synthetic**, not a house admission of a real manga.
It has eight placements: front cover, inside front cover, three interior pages,
an intentional blank, inside back cover, back cover. Positions 4–5 form a
declared spread. Geometry is a 120 × 180 mm trim, 3 mm bleed, and 5 mm inset safe
area. All canonical dimensions use integer micrometres. Carrier `page-05` is
interior logical page 3 and carries one pictured-bell particular and a caption.
No panel map or character identity is asserted from its whole-page pixels.

The synthetic source and edition receipts explicitly declare fixture-only
admission. They do not impersonate human admission of a real work. Pixel reuse,
derivative reuse, and a bounded motion proposal door are declared; pixel harvest,
synthesized sound, and publication reuse remain false. Editorial authority is
unknown. These are source-scope constraints, never executable admissions.

The Blender Bus Page 5 specimen contains a frozen beat sheet, whereas 008p's
owned-pixel donor names a different image and a tiny derivative. We did not
invent a LemonPRESS admission or assert that donor was the page. The separate
synthetic specimen exercises the same interface without importing those claims.

## Source, edition, and page identity

`schemas/work-manifest.schema.json` is the existing house schema copied unchanged
from main. Work and source admission are bound by repository-relative path and
exact file SHA; their IDs and admitted revision must agree. The edition has a
second, explicit receipt admitting its exact declaration and exact page hashes.
Source admission alone cannot admit a new page sequence or print geometry.

The declaration receipt hashes the canonical edition declaration before that
receipt's own reference is attached. The completed edition hash then includes
the receipt binding. Pages refer to the earlier source/rights admission, avoiding
a circular page-hash → admission-hash → page-hash dependency.

Canonical records use UTF-8 compact JSON with sorted object keys, preserved array
order, SHA-256, and no floating point. A record's hash excludes only its own hash
field. Duplicate JSON keys refuse. `seal page|edition INPUT OUTPUT` hashes an
already declared record; it does not admit it or construct an admission receipt.
Schemas are versioned in `schemas/manga-*.schema.json`; runtime additionally
checks bound bytes and cross-record relationships which JSON Schema cannot prove.

Page manifests bind edition/issue/page IDs, logical page number, exact optional
image SHA, geometry, optional panel-map binding, narrative/caption/continuity
references, rights origin, performed publication ancestry, and independent hash.
Whole-page pixels with unknown internal semantics are legal. A page's physical
sheet relation is initially null; the print plan supplies leaf, face, parity,
and left/right relation for each **placement**, including explicit repeats.

Ordering comes exclusively from `pageOrdering`, not file discovery or object
serialization order. Every placement has its own ID. A repeat names the first
placement explicitly; accidental duplicates refuse. Every page must be placed.
LTR/RTL is mandatory and does not reverse an already declared reading sequence:
it controls physical left/right relations. Cover roles name placements, not an
inferred filename. Facing spreads must join consecutive even/odd interior
positions. Required blanks are explicit admitted pages; no auto-padding occurs.

## What the print operation proves

`compose` emits `edition.json`, `pages.json`, `print-plan.json`, `print-proof.json`,
and `performance-handoff.json`. Identical replay is byte-identical and idempotent.
Conflicting existing bytes refuse. `verify` independently reconstructs the whole
bundle from bound input evidence instead of trusting stored hashes or claims.

The plan is a **one-leaf/two-sides** layout: exact ordered surfaces, recto/verso,
odd/even, reading-side geometry, cover roles, intentional blanks, and declared
facing spreads. It validates trim/bleed/safe-area nesting and exact page geometry
compatibility. It is renderer-neutral, with printer acceptance explicitly
unknown. It makes no folding/signature, binding, paper, or vendor assumptions.

The WRENCH-shaped proof records INPUT, TRANSFORMATION, OUTPUT, RESIDUAL, LOSS,
UNKNOWN, and STOP. Its state is `structural-proof-only`. It is neither a rendered
PDF nor an approved visual print proof. It grants no publication authority.

`gate` uses the existing Press Gate scaffold, artifact copying/hashing, manifest,
and checks. All bound evidence travels in the portable packet, with original
relative identities preserved under `artifacts/evidence/`. The packet remains
`physical` / `preflight`; house publication state remains undeclared. Physical
Composer proposals cannot enter as selected print facts: an existing
`human_selected` receipt or explicitly referenced `external_fixed` constraints
are required. Press Run and Road Grammar remain unchanged.

The next mechanical print aperture is exact pixel-to-box registration followed
by deterministic PDF proof rendering. The specimen exposes why that step needs
a decision: its 64 × 96 image ratio differs from its 126 × 186 mm bleed canvas.
This experiment does not silently stretch, crop, or fit those pixels.

## What the Blender crossing proves

Blender was inspected read-only through 008m → 008n → 008o → 008p, ending at
`4e3f098d328a9659d9074852ef7861b7d3078fee`. No Blender file is changed.

The committed `blender-compatibility-handoff.json` selects carrier page 05 and
retains work → edition → issue → page → exact page SHA, the edition and page
hashes, exact narrative/caption evidence, full ordering context, rights origin,
adaptation scope, explicit permission bits, and optional external editorial
reference. It contains no shots, staging, timings, crops, or admitted beats.

The read-only compatibility probe calls the actual pinned Blender
`particular_source` and `source_manifest` functions:

```sh
python3 manga-press/check_blender_008p.py --blender-root /path/to/pinned-blender
```

The resulting narrative source preserves the complete LemonPRESS page identity
inside `sourceLocator`, with `source-witness-only` authority. The page-source
function reads the exact synthetic pixels and preserves their SHA. Its rights
are narrowed: 008m's `pixelReuse` can open harvest, so this probe forwards that
bit only when **both** LemonPRESS pixel reuse and pixel harvest are explicit.
The founding specimen's closed harvest door remains closed. The deterministic
compatibility witness is committed and rebuilt in CI against the pinned repo.

This proves source-vocabulary compatibility and ancestry sufficient to construct
a later proposal. It does **not** implement a production adapter, harvest a page,
retain Press identity through Parts Drawer crops, propose staging, grant editorial
admission, synthesize sound, or render an owned-pixel manga film. A publication
page is not a Parts Drawer. The handoff's render/staging/editorial/release authority
bits are permanently false; rights permissions are constraints on later doors.

## Sibling lineage and returns

```text
admitted work → admitted manga edition → issue → exact admitted page
                                               ├─ print-plan placement / structural proof
                                               ├─ digital page intent (no produced file)
                                               └─ performance door
                                                  └─ independently produced descendant
```

Both print plan and handoff name the same page parent. A performance return's
parents are those consumed page identities, never the print plan or proof.
Neither projection replaces the other or retroactively changes the source.

`return EDITION HANDOFF DECLARATION OUTPUT` admits a renderer's **receipt of
existence**, not its creative or publication authority. The declaration requires
the handoff hash, consumed exact identities, descendant ID, renderer ID, exact
artifact file bindings, preserved identities, omissions, and declared mutations.
The composer independently rebuilds the handoff and verifies returned artifact
bytes. It does not independently prove the renderer's claimed transformations,
quality, rights compliance, or staging admission. The resulting versioned
`manga-performance-return/v0` has null `publicationStateChange`, false house
release authority, and no mutation of work/source/edition state.

Future source replacement needs new bindings, admission, and edition identity.
A new source file cannot retroactively update a frozen edition; overwriting a
bound source or page refuses verification.

## Proven and held

Tests cover canonical replay, independent page/edition hashes, exact byte
binding, object serialization independence, explicit LTR/RTL, repeats and
duplicate refusals, spreads and covers, blank and odd/even constraints, geometry,
no source rewriting, separate source/edition admission, bounded rights, unknown
semantics, create-only persistence, independent verification, portable Press Gate
replay, sibling parents, non-publishing returns, the inherited Road Grammar
regression, the complete Press Run queue, and the local mail/dispatch lifecycle.
CI also runs all 14 existing tests at the inspected, unchanged Audio Composer /
Suno Pantry snapshot, without asserting integration of that separate stack.

The compatibility check proves the actual pinned Blender source constructors
accept the retained identity and exact pixels. PDF output, visual QA, physical
printer acceptance, signature imposition, a real manga admission, production
quarry/performance adapters, animation/audio production, and house release remain
unproven. No license, source facts, or human editorial decision are inferred.

## Founding laws

```text
FORM != SOURCE
EDITION != SOURCE
PAGE ORDER != CANON AUTHORITY
PAGE != PANEL MAP
PANEL MAP != SEMANTIC UNDERSTANDING
IMAGE IDENTITY != CHARACTER IDENTITY
PRINT ADMISSION != PERFORMANCE ADMISSION
PUBLICATION != ANIMATION
HANDOFF != RENDER
HANDOFF != STAGING
HANDOFF != EDITORIAL ADMISSION
HANDOFF != PIXEL HARVEST AUTHORITY UNLESS EXPLICIT
PUBLICATION CONTEXT != STAGING DECISION
PRESS != HARVESTER
PUBLICATION PAGE != PARTS DRAWER
IMPOSITION PLAN != PRINTER ACCEPTANCE
PROOF != PUBLICATION
PRINT DESCENDANT != PERFORMANCE DESCENDANT
PERFORMANCE DESCENDANT != PRINT SOURCE
SIBLING DESCENDANTS MAY DIFFER
RETURN != PUBLICATION
RENDER EXISTS != HOUSE RELEASE
DESCENDANT != ANCESTOR
THE WORDS MAY MUTATE. THE RELATION MAY CARRY.
```

The aperture exposed by the running Blender probe is an **origin-preserving
page adapter**: 008m's page-source constructor preserves pixel SHA but has no
Press work/edition/issue/page locator, and its pixel-reuse bit also opens harvest.
The next crossing must carry the exact publication identity through authorized
quarry descendants while translating those narrower permissions without granting
staging or publication authority.
