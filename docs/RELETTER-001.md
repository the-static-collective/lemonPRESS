# RELETTER 001 — returned language becomes a page descendant

**Status:** executable v0  
**Output state:** CANDIDATE only  
**Stacked after:** TRANSLATION RELAY 001 / PR #34

RELETTER 001 is the missing bridge between semantic relay and visible manga.

```text
admitted Manga Press page pixels
          +
TRANSLATION RELAY candidate
          +
explicit segment -> rectangle bindings
          |
          v
deterministic returned-English reletter.png
          |
          v
CANDIDATE only
          |
          v
later explicit page / edition admission
```

## Founding laws

```text
RELETTER != SOURCE
RETURN != ORIGINAL
MASK != PARENT ERASURE
PIXEL PATCH != TEXT TRUTH
OVERFLOW != SILENT TRUNCATION
UNSUPPORTED GLYPH != SUBSTITUTE
PARENT SURVIVES DESCENDANT
RIGHTS NEVER EXPAND
CANDIDATE != EDITION
RENDERING != ADMISSION
```

## Native seam

RELETTER 001 consumes one exact Manga Press page manifest. The page manifest binds the source pixels and rights. The tool requires `pixelReuse` and `derivativeReuse`; it does not infer `pixelHarvest`, publication, selection, or edition authority.

The relay remains a separate parent. RELETTER rebuilds its candidate from the frozen relay declaration, selects only the declared `return` stage, and binds exact segment IDs to exact pixel rectangles.

No OCR occurs. No balloon detector occurs. No inpainting occurs. v0 paints a declared solid rectangle and deterministically draws returned English into it.

## Typography boundary

v0 uses Pillow 12.1.1's pinned default font and ASCII returned text only.

Unsupported glyphs refuse. Text that cannot fit the declared rectangle refuses. There is no silent truncation, substitution, font fallback, or automatic box growth.

That limitation is intentional. A later typography aperture can add explicitly admitted font assets and Japanese/CJK rendering without changing v0 meaning.

## CLI

```bash
npm run manga-reletter -- compose witnesses/reletter-001/recipe.json out/reletter-001
npm run manga-reletter -- verify witnesses/reletter-001/recipe.json out/reletter-001
```

Outputs:

- `reletter.png`
- `candidate.json`
- `RECEIPT.md`

All outputs are create-only. An identical replay is idempotent. Conflicting existing bytes refuse.

## Relation to the manga stack

```text
Manga Press          = admitted page identity + pixels + rights
Manga Remix          = visual recomposition
Translation Relay    = semantic language recomposition
RELETTER             = returned text -> declared visible page regions
Remix Sequence       = occurrence / reading order
Manga Press admission= explicit local constitution of a selected descendant
```

RELETTER does not become a hidden admission bridge. The returned page is still only a candidate.
