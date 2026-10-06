# MANGA PARCEL 001 — National Treasure / Seed Zero

**Status:** incubating witness  
**Source:** one exact Google Drive PNG  
**Source SHA-256:** `7531b551c433fe947658bb9731e9271a8636f1e3a5f57b41827c1925bed295ff`  
**Issue-plan SHA-256:** `6f4defc2b216064cd48153cf08c3429679d9a03791b6ca39f97a3129724eb27c`

This is LemonPRESS's first manga parcel experiment.

The source is the 1312 × 1199 National Treasure concept sheet created on 2026-10-06. The experiment does not copy editorial authority into LemonPRESS and does not treat a crop, page, narration, motion pass, or soundtrack as the source.

## Inversion

> **We do not make a manga from assets. We make assets that know how to become manga.**

The parcel carries enough structure to let the same particular become several editions without collapsing their ancestry.

```text
exact source pixels
      ↓
MangaParcelV0
      ↓
five reversible page projections
      ↓
print / narration / motion / music / crawler candidates
      ↓
explicit local admission
      ↓
descendants with retained ancestry
```

## First micro-issue

No new pixels are required for the first proof. `parcel.json` slices the single source witness into five ordered page regions:

1. opening / the question
2. cases 1–4 / control + projection
3. cases 5–8 / memory + road
4. cases 9–12 / particular → pattern
5. field notes / open endedness

These are **virtual pages**, not source mutations. A renderer may crop, scale, letter, narrate, animate, or score them, but every output remains a descendant candidate until explicitly admitted.

## FastTranch posture

Unfinished creative material does not need to become a project before it can be carried.

The parcel exposes unborn descendant slots for print pages, narration, motion, soundtrack/stems, and a crawler edition. A slot may stay unborn forever. Completion is not a prerequisite for provenance.

## reLATTE seam

`relatte-opaque-organ-spec.json` is shaped for reLATTE's existing generic opaque-organ adapter.

reLATTE is allowed to know only that this is an opaque donor artifact with payload references and signed donor claims. It is **not** allowed to learn manga semantics.

```text
LEMONPRESS PARCEL
      ↓
opaque organ spec
      ↓
reLATTE generic adapter
      ↓
signed crossing
      ↓
RECEIVE
      ↓
owner-local HOLD / ADMIT / REFUSE / RETURN
```

This preserves the existing separation:

```text
DONOR SEMANTICS != SUBSTRATE SEMANTICS
SOURCE != PROJECTION
DESCENDANT != ANCESTOR
RENDERING != AUTHORITY
PARCEL MAY CROSS; ADMISSION REMAINS LOCAL
```

## Verification

With the source PNG available locally:

```bash
node verify.mjs parcel.json /path/to/file_000000001164820db1a05ce868d31660.png relatte-opaque-organ-spec.json
```

The verifier checks the exact source hash and size, PNG dimensions, canonical issue-plan hash, parcel identity, page bounds, and the reLATTE seam.

## Rights note

The parcel records the user's declaration that the source is controlled for use. That statement is preserved as provenance metadata and explicitly marked **not independently verified**. Neither LemonPRESS nor reLATTE converts a declaration into a legal determination.

## What this earns

If the verifier passes and reLATTE seals the opaque organ spec without a family-specific branch, this proves one small end-to-end creative seam:

> one immutable image can carry a reproducible manga reading plan, cross a generic substrate, and remain available for multiple descendants without any descendant pretending to be the ancestor.

It does **not** yet prove rendered page output, narration, motion, print production, or publication.
