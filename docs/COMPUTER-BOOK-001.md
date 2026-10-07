# COMPUTER BOOK 001 — Native Literature for Partial Retrieval

Status: executable proof  
Lane: `press/crawler`

## Objective

Promote LemonPRESS's existing crawler-edition practice into a reusable computer-book contract.

A computer book is a publication form that remains attributable and navigable under partial retrieval, arbitrary entry, chunking, caching, quotation, embedding, or damaged context.

It is not a database pretending to be a book. It is not SEO attached to a human edition. It is a book whose publication grammar treats machine retrieval as a first-class reading condition.

## Core laws

```text
RETRIEVED != READ
CHUNK != BOOK
FRAGMENT != CONTEXT
SOURCE != PROJECTION
DISCOVERY != ENDORSEMENT
READING ORDER != ANCESTRY
RETRIEVAL ORDER != AUTHORITY
SEVERANCE != ORPHANHOOD
ABSENCE != NONEXISTENCE
```

A severed limb should still know which body it came from.

## First proof obligation

Given any one fragment from the specimen, a reader or program can identify:

- the work occurrence;
- the crawler edition;
- the fragment itself;
- declared ancestry;
- neighboring relations / legitimate continuations;
- explicit uncertainty;
- that the fragment is not the whole book;
- that retrieval grants no admission, publication, ownership, or source authority.

When the complete specimen is available, entering from any fragment must reconstruct the same reachable local body without changing identity or authority.

## Native anatomy

```text
computer-book/
├── manifest.json
├── fragments/
├── relations.jsonl
└── RECEIPT.md
```

The manifest describes the body. Each fragment carries enough local identity to survive severance. Relations describe traversal without redefining source ancestry. The verifier checks the non-collapse laws mechanically.

## Non-goals

COMPUTER BOOK 001 does not crawl the public web, decide what deserves publication, infer ownership or copyright, convert discovery into admission, define a universal ontology for literature, require a canonical first fragment, or claim that a graph replaces prose, sequence, voice, or editorial judgment.

Crawler/scout intake can become a later organ. This slice proves the publication form first.

## Executable checks

`python tools/computer_book.py verify specimens/computer-book-001`

`python tools/computer_book.py reconstruct specimens/computer-book-001 002-loss-is-visible`

Passing this proof establishes only that LemonPRESS can encode and verify one small computer-native book whose identity and local traversal survive arbitrary entry.
