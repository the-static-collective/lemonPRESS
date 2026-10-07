# MANGA REMIX 001 — attributable multi-parent page remix

**Status:** draft executable experiment  
**Base:** manga-press-001  
**Output state:** CANDIDATE only

Manga Press already binds admitted pages into issues. Manga Parcel already preserves families of descendants. MANGA REMIX 001 joins those ideas at the narrow seam where several admitted pages may become one new candidate page without pretending that composition changes the parents.

    ADMITTED PAGE A --    ADMITTED PAGE B ----> REMIX RECIPE -> DETERMINISTIC PIXELS -> CANDIDATE PAGE
    ADMITTED PAGE C --/                                      |
                                                            +-- no admission or release authority

## Founding law

> **REMIX != SOURCE**

The compositor never rewrites a parent page, parent edition, admission receipt, or source image. It produces new PNG bytes plus a candidate manifest naming every exact parent.

The candidate is not automatically a page in an edition. A later human/local authority must explicitly admit it.

## v0 operations

tools/manga_remix.py accepts a JSON recipe containing one or more exact admitted Manga Press page parents, an explicit pixel canvas/background, and an ordered placement stack.

Supported transformations are whole-page reuse or explicitly declared crop, deterministic nearest-neighbor scaling, 0/90/180/270 degree rotation, horizontal/vertical mirroring, and explicit opacity.

The placement array is layer order. No semantic interpretation is inferred.

    python3 tools/manga_remix.py compose path/to/recipe.json out/remix
    python3 tools/manga_remix.py verify  path/to/recipe.json out/remix

The bundle contains remix.png and candidate.json. Existing identical output is idempotent; conflicting bytes refuse.

## Parent identity

Each parent carries frozen editionManifest and pageManifest bindings. The tool independently verifies the edition admission, page hash, source-image binding, and that the page is actually bound into that edition.

Parents may come from different admitted works or issues. Shared ancestry is not required.

## Rights pressure

Every used parent must explicitly grant pixelReuse and derivativeReuse. A partial crop additionally requires pixelHarvest.

The candidate's effective grants are the intersection of all parent grants. Rights can narrow but never widen.

Publication permission is not publication authority.

## WRENCH receipt

Every candidate records INPUT, TRANSFORMATION, OUTPUT, RESIDUAL, LOSS, UNKNOWN, and STOP.

LOSS names visible operations such as raster resampling, cropping, or opacity reduction. UNKNOWN refuses to infer panel, character, semantic, or narrative fusion. STOP leaves the artifact before admission.

## Non-collapse laws

    REMIX != SOURCE
    RECIPE != AUTHORITY
    SELECTION != ADMISSION
    PARENT SURVIVES DESCENDANT
    ORDER IS DECLARED
    CROP REQUIRES PIXEL HARVEST
    RIGHTS INTERSECT; NEVER EXPAND
    CANDIDATE != EDITION
    OUTPUT != PUBLICATION

## Prepared flow

    owned / admitted manga particulars
            |
            v
    exact parent page identities
            |
            v
    many-parent remix recipes
            |
            v
    candidate pages
            |
            v
    human selection / admission
            |
            v
    Manga Press issue composition
            |
            v
    physical / digital / performance descendants

The next aperture is an admission bridge: a selected remix candidate can become a new Manga Press page/edition occurrence, but the compositor must never self-admit its own output.
