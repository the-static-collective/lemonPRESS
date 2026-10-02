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

## PRESS MOUTH 001

PRESS MOUTH is the first executable intake seam for audio-family artifacts.

It currently admits verified Autodiscography Vault bodies and completed Haunted Phonograph projections into small, SHA-addressed `lemonpress/audio-parcel/v0` records without copying the media body into Git or inheriting upstream authority.

~~~text
VAULT / PHONOGRAPH
        |
 receipt + local body
        v
  PRESS MOUTH 001
        |
        v
 AUDIO PARCEL
~~~

See [`docs/PRESS-MOUTH-001.md`](docs/PRESS-MOUTH-001.md).

## AUDIO COMPOSER 001

AUDIO COMPOSER binds manuscript identity to admitted audio parcels and resolves explicit composition cues into a renderer-neutral timeline.

~~~text
MANUSCRIPT + AUDIO PARCELS + CUES
               |
               v
      AUDIO COMPOSER 001
               |
      AudioEditionScore
               |
      ResolvedAudioEdition
               |
         renderer boundary
~~~

The renderer is projection-only: it may not reinterpret the structure or invent layers.

See [`docs/AUDIO-COMPOSER-001.md`](docs/AUDIO-COMPOSER-001.md).

## First live work

**¿another clue?** is lemonPRESS's first admitted multi-branch specimen.

Admitted on **2026-09-30** from a frozen Google Docs source revision, it immediately crossed into physical, digital, crawler, and archival production lanes. Those descendants are allowed to differ honestly while remaining attributable to the same admitted work.

The physical arm begins as an approved 6 × 9 print proof; **proof is not publication**. A later release may name that proof as an ancestor without changing the work's admission birthday.

## Little Free Library intake

The recovered book shelf is registered under [`library/`](library/README.md). Registration gives a work a house address without automatically publishing its private source body.

See [`library/catalog.yaml`](library/catalog.yaml) for the current machine-readable register.
