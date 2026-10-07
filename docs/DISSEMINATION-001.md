# DISSEMINATION 001 — Throw One Book Into the Sea

Status: executable publication slice  
Depends on: COMPUTER BOOK 001 and COMPUTER BOOK 002

## Objective

Publish one LemonPRESS computer book onto ordinary HTTPS so an unknown human, crawler, search system, archive, or agent can encounter it without first understanding LemonPRESS.

The public surface must remain useful under both ordinary browsing and partial machine retrieval.

## Canonical public origin

`https://lemonpress-computer-books.vercel.app`

## Publication surface

```text
/
├── index.html
├── llms.txt
├── robots.txt
├── sitemap.xml
├── feed.xml
├── catalog.json
└── books/
    └── computer-book-001/
        ├── index.html
        ├── index.md
        ├── manifest.json
        ├── relations.jsonl
        ├── llms.txt
        └── fragments/
            ├── 001-enter-anywhere/
            ├── 002-loss-is-visible/
            └── 003-order-is-not-ancestry/
```

Each fragment directory exposes HTML, Markdown, and the exact structural JSON carrier.

## Laws

```text
MIRROR != SOURCE
INDEXED != ENDORSED
CACHE != CANON
DISCOVERY != ADMISSION
COPY != NEW OCCURRENCE
POPULARITY != AUTHORITY
LINK != OWNERSHIP
```

## Discovery rule

Use boring web standards first.

- HTML for ordinary readers and crawlers.
- Markdown as a clean alternate carrier.
- JSON for exact computer-book structure.
- `llms.txt` for machine orientation.
- `robots.txt` + XML sitemap for crawler discovery.
- Atom feed for release discovery.
- JSON catalog for deterministic shelf enumeration.

No client-side JavaScript is required to retrieve the book.

## First outside-reader experiment

Give an unfamiliar reader only `https://lemonpress-computer-books.vercel.app/llms.txt`.

Do not explain LemonPRESS.

Ask it to:

1. find a book;
2. enter somewhere other than the beginning;
3. identify the work and edition;
4. state what it does not know;
5. name one legitimate continuation;
6. avoid manufacturing authority from retrieval.

That result becomes DISSEMINATION WITNESS 001.

## Stop

This slice publishes one small proof book. It does not yet claim search-engine indexing, Common Crawl inclusion, archival capture, human readership, model ingestion, or independent reconstruction.
