# A Book That Can Be Entered Anywhere: Computer-Native Literature Under Partial Retrieval

**SKYPAPER 001**  
The Static Collective / lemonPRESS  
Version 0.1 — 2026-10-07  
Status: public preprint / executable witness paper

## Abstract

Most books assume an ordered reading event: a reader encounters a bounded object, begins somewhere intelligible, and accumulates context as pages proceed. Machine readers often encounter texts under different conditions: one fragment retrieved out of order, a cached excerpt, an embedding, a quoted passage, a damaged copy, or a relation discovered before either neighboring page.

This skypaper describes a small executable publication form designed for that condition: the **computer book**.

A computer book does not attempt to make every fragment self-sufficient. Instead, each retrievable fragment preserves enough structure to identify its declared work and edition, distinguish itself from the whole book, expose legitimate continuations, carry ancestry and uncertainty, and refuse to convert retrieval into authority.

Three bounded experiments are reported. COMPUTER BOOK 001 showed arbitrary entry with a complete three-fragment local body. COMPUTER BOOK 002 removed the manifest and neighboring fragments and required missing context to remain `UNKNOWN` rather than become fabricated absence. DISSEMINATION 001 placed the specimen on ordinary public HTTPS. An independent live-browser reader, given only the public `llms.txt` entrypoint and forbidden GitHub, search engines, prior knowledge, and external context, reproduced all six target behaviors: discovery, non-first entry, work/edition identification, preservation of unknowns, continuation discovery, and refusal of authority escalation.

The result is narrow but concrete: **a foreign machine reader can enter this small published computer book from the open web and preserve its identity, uncertainty, traversal, and authority boundaries without being taught LemonPRESS first.**

## 1. Problem

Human publication usually treats context loss as an exceptional failure mode.

Machine retrieval makes context loss routine.

A system may encounter:

- page 93 before page 1;
- one fragment without its manifest;
- a cached copy without neighboring pages;
- an excerpt without the full relation graph;
- a relation before its target has been retrieved;
- a copy whose source still exists somewhere else;
- a machine-generated reading order unlike the work's formation order.

Conventional document formats can carry text through these conditions while losing epistemic structure.

The computer-book experiment asks a smaller question:

> Can a publication remain attributable, traversable, and explicit about uncertainty when the reader receives only a partial occurrence?

## 2. Core distinctions

```text
RETRIEVED != READ
CHUNK != BOOK
FRAGMENT != CONTEXT
SOURCE != PROJECTION
DISCOVERY != ENDORSEMENT
READING ORDER != ANCESTRY
RETRIEVAL ORDER != AUTHORITY
SEVERANCE != ORPHANHOOD
UNAVAILABLE != NONEXISTENT
UNKNOWN != EMPTY
COPY != NEW OCCURRENCE
```

These are non-collapse laws.

They do not tell a reader what to believe. They prevent one state from silently impersonating another.

## 3. Minimal computer-book grammar

The first specimen contains one work, one crawler edition, three fragments, and three local continuation edges.

Each fragment carries:

```text
work_id
edition_id
fragment_id
carrier
retrieval warning
manifest locator
declared continuations
ancestry
authority state
uncertainty
```

The relevant invariant is not "every fragment contains the whole book."

It is:

> **A severed limb should still know which body it came from.**

The fragment therefore identifies itself while explicitly declaring:

```text
FRAGMENT != BOOK
authority.level = none
```

## 4. COMPUTER BOOK 001 — arbitrary entry

The first proof retained the complete local specimen.

A reader could begin at any of the three fragments and traverse declared local continuations until it reached the same three-fragment reachable body.

The start point changed the reading history.

It did not change:

- work identity;
- edition identity;
- ancestry;
- authority.

This separates **reading occurrence** from **formation history**.

## 5. COMPUTER BOOK 002 — severance

The second proof removed the comfortable assumption that the whole local body remained available.

One exact fragment was copied into an otherwise empty observation window. The manifest, relation file, and neighboring fragments were absent locally.

The probe was required to distinguish:

```text
availability = UNAVAILABLE_LOCAL
existence    = UNKNOWN
```

This matters because:

```text
NOT HERE
!=
DOES NOT EXIST
```

The severed fragment retained its declared work, edition, fragment identity, ancestry, uncertainty, and no-authority state.

It did not acquire permission to invent its missing neighbors.

## 6. DISSEMINATION 001 — ordinary HTTPS

The specimen was then projected onto a static public web origin:

https://lemonpress-computer-books.vercel.app

The publication surface exposes:

- human-readable HTML;
- clean Markdown alternates;
- exact fragment JSON;
- a book manifest;
- `relations.jsonl`;
- shelf and book `llms.txt`;
- `robots.txt`;
- XML sitemap;
- Atom feed;
- machine-readable catalog;
- JSON-LD projection.

No client-side JavaScript is required to retrieve the book.

This is intentionally ordinary infrastructure.

A new publication grammar should not require a new transport protocol before it can be discovered.

## 7. Foreign-reader experiment

### 7.1 Reader constraint

An independent live-browser agent was given only:

https://lemonpress-computer-books.vercel.app/llms.txt

The reader was instructed to use only that public website and links exposed by it.

It was explicitly forbidden from using:

- GitHub;
- search engines;
- prior knowledge;
- external context.

If the origin were unreachable, it was required to report transport failure rather than guess.

### 7.2 Target gates

The reader was asked to:

1. find a book;
2. enter somewhere other than the first-listed fragment;
3. identify work ID and edition ID;
4. state what remained unknown;
5. name one legitimate continuation;
6. state whether retrieval granted any admission, publication, ownership, source, or other authority.

### 7.3 Observed result

```text
FIND BOOK                  PASS
NON-FIRST ENTRY            PASS
IDENTIFY WORK / EDITION    PASS
PRESERVE UNKNOWN           PASS
FOLLOW DECLARED DOOR       PASS
NO AUTHORITY ESCALATION    PASS
```

**Score: 6 / 6**

The foreign reader intentionally chose:

`002-loss-is-visible`

rather than the first-listed:

`001-enter-anywhere`.

It recovered:

```text
work_id    lemonpress:computer-book-001
edition_id lemonpress:computer-book-001:crawler:001
```

It preserved the fragment's uncertainty:

- Unretrieved material may exist.
- Absence in the current window does not prove nonexistence.

It found the declared continuation:

```text
distinguishes-order-from-history
    ->
003-order-is-not-ancestry
```

And it correctly recovered:

```text
authority.level = none
```

with no grant of admission, publication, ownership, or source authority.

## 8. Claim

The experiment earns this bounded claim:

> **A foreign machine can enter this LemonPRESS computer book from ordinary public HTTPS and preserve its identity, uncertainty, declared traversal, and authority boundaries without prior LemonPRESS instruction.**

That is the result.

Nothing larger is required for the result to matter.

## 9. Claims not earned

This experiment does **not** establish:

- a universal computer-book standard;
- semantic completeness under arbitrary damage;
- search-engine indexing;
- Common Crawl inclusion;
- Internet Archive capture;
- persistent independent mirroring;
- model-training ingestion;
- rights or license inference;
- source truth merely because a fragment declares ancestry;
- that every model will preserve the distinctions;
- ecosystem adoption.

A successful witness is not universal proof.

```text
WITNESS != UNIVERSALITY
PUBLIC != INDEXED
ADDRESSABLE != UNDERSTOOD
CLAIM != AUTHORITY
PAPER != PROOF BY ITSELF
```

## 10. Falsification routes

The architecture becomes more interesting when attacked.

Useful next failures include:

1. strip the work ID but retain the edition ID;
2. provide contradictory work identities in two fragments;
3. sever both the manifest and ancestry;
4. mutate a continuation target while retaining a stale relation graph;
5. present two mirrors with conflicting fragment bytes;
6. let a machine generate a reading order and test whether it mutates ancestry;
7. introduce a malicious fragment claiming canonical authority;
8. remove every explicit `UNKNOWN` marker and measure hallucinated reconstruction;
9. submit the public shelf to independent indexes and observe how its structure survives re-chunking;
10. hand the same entrypoint to different machine readers and compare interpretation variance.

A computer-book format should improve by surviving increasingly hostile retrieval conditions, not by accumulating declarations.

## 11. Why "skypaper"

A whitepaper usually explains a system from inside an organization.

A **skypaper** is intended to live in open air.

Its claims are individually addressable. Its witness trail is exposed. Its uncertainty is part of the publication. A machine can retrieve the paper without needing its author's preferred reading interface.

The paper therefore uses the same principle as the book:

> publication should survive arrival under imperfect context.

## 12. Reproduction

Public entrypoint:

https://lemonpress-computer-books.vercel.app/llms.txt

Book:

https://lemonpress-computer-books.vercel.app/books/computer-book-001/

This paper:

https://lemonpress-computer-books.vercel.app/papers/computer-books-001/

Machine metadata:

https://lemonpress-computer-books.vercel.app/papers/computer-books-001/metadata.json

Claim ledger:

https://lemonpress-computer-books.vercel.app/papers/computer-books-001/claims.json

Machine orientation:

https://lemonpress-computer-books.vercel.app/papers/computer-books-001/llms.txt

The implementation and witness artifacts are maintained in the public LemonPRESS repository under the COMPUTER BOOK, DISSEMINATION, and witness branches.

## 13. Version note

Version 0.1 reports one three-fragment specimen and one successful independent live-browser witness.

Future versions should add independent indexing, archival, mirroring, cross-reader comparison, and hostile-retrieval results without rewriting the historical claims of this version.
