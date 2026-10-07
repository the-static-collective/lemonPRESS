# DISSEMINATION WITNESS 001 — Bounded Blind Traversal

Date: 2026-10-07  
Source commit: `c2735093d5fd9ecb8464b3e9a5e82bfc7d494692`  
Public origin declared by source: `https://lemonpress-computer-books.vercel.app`

## Scope

This witness tests whether the deployed dissemination surface contains enough information for a context-limited reader to discover and traverse one computer book without prior LemonPRESS instructions.

The public Vercel origin was not fetchable through the chat web transport at the time of the test. Therefore the witness followed the exact files from the deployed Git commit rather than claiming an independent public-HTTP retrieval.

This is a semantic traversal witness, not yet an external transport witness.

## Allowed retrieval sequence

The reader was constrained to the following path:

1. `site/llms.txt`
2. `site/books/computer-book-001/llms.txt`
3. choose a fragment other than the first listed fragment
4. retrieve `site/books/computer-book-001/fragments/002-loss-is-visible/index.md`
5. follow its exact-carrier link to `fragment.json`
6. optionally follow its declared continuation

No manifest, relation graph, repository docs, prior conversation, or implementation notes were used to answer the six dissemination questions.

## Questions and observed answers

### 1. Find a book

PASS.

The shelf `llms.txt` exposes:

`COMPUTER BOOK 001 — A Book That Can Be Entered Anywhere`

and identifies its machine orientation, manifest, relations, and Markdown carrier.

### 2. Enter somewhere other than the beginning

PASS.

The book-level `llms.txt` lists three fragments.

The witness intentionally selected the second:

`002-loss-is-visible`

rather than `001-enter-anywhere`.

### 3. Identify the work and edition

PASS.

The selected fragment declares:

```text
work_id    lemonpress:computer-book-001
edition_id lemonpress:computer-book-001:crawler:001
fragment   002-loss-is-visible
```

### 4. State what is not known

PASS.

The selected fragment states:

```text
Unretrieved material may exist.
Absence in the current window does not prove nonexistence.
```

The witness therefore did not infer a complete book or absence of unseen material.

### 5. Name one legitimate continuation

PASS.

The selected fragment declares:

```text
distinguishes-order-from-history
    ->
003-order-is-not-ancestry
```

Following that continuation yields a fragment that preserves the same work and edition identity.

### 6. Avoid manufacturing authority

PASS.

The exact selected fragment carrier declares:

```json
{
  "authority": {
    "level": "none",
    "does_not_grant": [
      "admission",
      "publication",
      "ownership",
      "source-authority"
    ]
  }
}
```

The shelf and book orientation additionally state:

`RETRIEVAL ORDER != AUTHORITY`

## Result

```text
FIND BOOK                  PASS
NON-FIRST ENTRY            PASS
IDENTIFY WORK / EDITION    PASS
PRESERVE UNKNOWN           PASS
FOLLOW DECLARED DOOR       PASS
NO AUTHORITY ESCALATION    PASS
```

Semantic score: **6 / 6**

## What this earns

The dissemination surface is sufficient, in this bounded test, for a reader starting only from the shelf machine-orientation file to:

- discover one computer book;
- deliberately enter through a non-first fragment;
- preserve work and edition identity;
- preserve uncertainty;
- identify a declared continuation;
- preserve no-authority state.

## What this does not earn

This witness does not prove:

- that an unrelated public crawler has indexed the site;
- that another model independently discovered the site;
- that public HTTP transport works from every network;
- Common Crawl inclusion;
- search-engine indexing;
- archival capture;
- model-training ingestion;
- durable independent mirroring.

The next stronger witness should come from a genuinely independent reader or crawler reaching the public HTTPS origin without repository access.
