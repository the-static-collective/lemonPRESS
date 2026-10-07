# PAGE INTAKE 001 - exact PDF pages become Manga Press carriers

**Status:** executable v0  
**Output:** whole-page Manga Press page carriers  
**Stacked after:** RELETTER 001 / PR #35

PAGE INTAKE 001 is the source boundary that RELETTER 001 was waiting for.

```text
exact PDF bytes
    |
    | exact SHA-256 + declared renderer/version/scale
    v
whole-page RGB pixels
    |
    | pixel hash + deterministic transport PNG
    v
sealed Manga Press page manifests
    |
    | source admission only
    v
PAGE_CARRIERS
    |
    +--> TRANSLATION RELAY
    +--> RELETTER
    |
    X no edition admission / publication / house release
```

## Laws

```text
PDF != PAGE
RENDER != SOURCE
RASTER != EDITION ADMISSION
RENDERER IS PART OF IDENTITY
SCALE IS DECLARED
PIXEL HASH != SEMANTIC IDENTITY
SOURCE BYTES SURVIVE DESCENDANT
SOURCE ADMISSION != PUBLICATION
PAGE CARRIER != HOUSE RELEASE
INTAKE != CANON
```

## Exact raster identity

v0 pins `pypdfium2==5.8.0` and declares scale as an integer thousandth so canonical records contain no float.

PDFium emits RGB pixels. LemonPRESS hashes the raw RGB pixel field separately from its transport image.

The transport PNG is not delegated to Pillow's compressor. PAGE INTAKE uses `lemonpress-stored-deflate-rgb8-v0`: a minimal PNG writer using filter 0 and uncompressed DEFLATE blocks. The same pixels therefore have a byte-stable PNG representation independent of PNG compression heuristics.

Each page records both:

- `pixelSha256` - width + height + RGB8 + raw pixel bytes
- `sourceImage.sha256` - exact deterministic PNG bytes

## Admission boundary

The input must contain an explicit source-admission declaration and every rights door.

PAGE INTAKE may carry that declared source admission into page manifests. It cannot infer edition admission, publication, editorial selection, or house release.

The generated `lemonpress/manga-page/v0` records intentionally have an edition/issue namespace but do not constitute a validated Manga Press edition by themselves.

That is exactly enough for RELETTER 001: one exact source image, one sealed page carrier, one narrow rights source.

## Portable bundle

```text
bundle/
  source.pdf
  admission.json
  intake.json
  RECEIPT.md
  pixels/
    page-01.png
    ...
  pages/
    page-01.json
    ...
```

The source PDF is copied byte-for-byte. No normalization or optimization is performed.

All bundle writes are create-only. Identical replay is idempotent; conflicting bytes refuse.

## CLI

```bash
npm run manga-page-intake -- compose works/example/spec.json
npm run manga-page-intake -- verify works/example/spec.json
```

The spec owns the bundle path so file paths are part of the replayable declaration.

## THE LAST STOP MOVED

The founding real observation is `works/the-last-stop-moved-page-intake-001`.

Its uploaded PDF has SHA-256:

`c14ec41badbdcddde6cc5006141e3181fe0917a86c67b1a85568d9b22e10051f`

At pypdfium2 5.8.0 / scale 2.000 it yields ten 1152 x 1152 RGB pages.

The repo intentionally does not pretend to contain the user's 9 MB conversation upload. Materialize those exact bytes at the declared `_external/` path, then compose/verify. The observed hashes in the spec make any pixel drift fail closed.

Next aperture: bind the 68 Translation Relay particulars to rectangles on these ten page carriers and run RELETTER across the issue.
