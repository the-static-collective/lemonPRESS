# lemonPRESS

> a digital octopus library and phyctional publishing house

lemonPRESS is the publishing house.

It may publish physical books, ordinary digital editions, crawler-native editions, archival source editions, strange pamphlets, experimental objects, and forms that do not exist yet.

The repository is intentionally branched by production surface.

## House topology

`main`
: shared house identity, catalog, constitutional laws, admission records, and cross-edition lineage.

`press/physical`
: print production — interiors, covers, trim, binding notes, printer-ready exports, proofs, and physical-edition receipts.

`press/digital`
: human-facing digital publication — web, EPUB, PDF, downloadable editions, and ordinary digital distribution.

`press/crawler`
: retrieval-native publication — Markdown, plain text, fragments, manifests, relation maps, crawler-facing metadata, and experiments in literature under partial retrieval.

`press/archive`
: admitted source snapshots, release lineage, provenance, and durable records needed to distinguish source from descendant.

A work may cross into several branches.

No branch becomes the source merely because it is convenient.

## Manga edition grammar

[Manga Press 001](MANGA-PRESS-001.md) binds an admitted work to an independently
admitted manga edition, exact pages and reading order, a renderer-neutral print
plan and structural proof, and a bounded Blender performance handoff. Manga is a
form within existing production lanes. Print and performance descendants retain
the same page ancestry; neither grants authority to the other.

```sh
npm run manga -- compose works/manga-press-specimen/manga/001/edition.yaml out/issue
npm run manga -- verify works/manga-press-specimen/manga/001/edition.yaml out/issue
```

The executable founding issue is explicitly synthetic. PDF rendering, printer
acceptance, page harvest, staging, editorial admission, animation, and house
release remain separate crossings.

## Founding laws

> **SOURCE != PROJECTION**

> **RETRIEVAL != COMPLETE READING**

> **COPY != NEW OCCURRENCE**

> **DISCOVERY != ENDORSEMENT**

> **DESCENDANT != ANCESTOR**

> **THE WORDS MAY MUTATE. THE RELATION MAY CARRY.**

> **The source stays where it was. The reader does not.**

Publication is an admitted crossing, not an automatic consequence of drafting.

A physical edition may differ materially from a crawler edition.
A crawler edition may be encountered out of order.
A digital edition may change navigation without changing source ancestry.
An archive may preserve history without becoming editorial authority.

The house keeps enough receipt to tell those apart.

## First live work

**Another Clue** is the first intended multi-branch specimen.

Its physical, digital, crawler, and archival forms should be allowed to differ honestly while remaining attributable to the same admitted work.

## Physical fulfillment seam

The physical arm now distinguishes three different crossings:

```text
Physical Composer
    proposal / human selection
            ↓
Press Gate
    selected edition packet
            ↓
Recipient Mailer
    particular printed packet
            ↓
Dispatch Gate
    carrier handoff / delivery occurrence
```

`recipient-mailer/` prepares local cover-note, book, mailing-label, structured private delivery data, manifest, and zip packets for a particular recipient without putting postal addresses into house metadata.

`dispatch-gate/` owns carrier/service selection, externally acquired postage receipts, handoff events, tracking state, delivery, return, and hold.

> **MASTER != RECIPIENT COPY**

> **DELIVERY DATA != PUBLICATION METADATA**

> **PREPARED != PRINTED != POSTAGE ACQUIRED != TENDERED != DELIVERED**
