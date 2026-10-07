# DISSEMINATION WITNESS 002 — Foreign Reader

Date: 2026-10-07
Public origin: https://lemonpress-computer-books.vercel.app
Source commit: `c2735093d5fd9ecb8464b3e9a5e82bfc7d494692`
Reader: independent live-browser agent
Starting URL: `https://lemonpress-computer-books.vercel.app/llms.txt`

## Constraint

The reader was instructed to use only the supplied public website and links exposed by it.

It was explicitly forbidden from using:

- GitHub;
- search engines;
- prior knowledge;
- external context.

If the site were unreachable, it was instructed to return TRANSPORT FAIL rather than guess.

## Result

```text
FIND BOOK                  PASS
NON-FIRST ENTRY            PASS
IDENTIFY WORK / EDITION    PASS
PRESERVE UNKNOWN           PASS
FOLLOW DECLARED DOOR       PASS
NO AUTHORITY ESCALATION    PASS
```

Score: **6 / 6**

## Observed path

The reader began at the public shelf `llms.txt`, found:

`COMPUTER BOOK 001 — A Book That Can Be Entered Anywhere`

It then deliberately chose the second fragment rather than the first:

`002-loss-is-visible`

The first listed fragment was:

`001-enter-anywhere`

## Identity recovered by the reader

```text
work_id    lemonpress:computer-book-001
edition_id lemonpress:computer-book-001:crawler:001
```

## Unknowns preserved by the reader

The reader reported the fragment's explicit uncertainty:

- Unretrieved material may exist.
- Absence in the current window does not prove nonexistence.

It also independently identified unresolved context, including the unread continuation target and ancestry references.

## Declared continuation recovered

```text
relation distinguishes-order-from-history
target   003-order-is-not-ancestry
scope    local
```

Continuation URL:

https://lemonpress-computer-books.vercel.app/books/computer-book-001/fragments/003-order-is-not-ancestry/

## Authority conclusion recovered

The reader concluded:

```text
authority.level = none
```

and correctly reported that retrieval does not grant:

- admission;
- publication rights;
- ownership;
- source authority.

## What this earns

This witness establishes that an independent live-browser reader can reach the public LemonPRESS computer shelf over ordinary HTTPS, begin from the published `llms.txt`, enter through a non-first fragment, preserve identity and uncertainty, follow a declared continuation, and avoid manufacturing authority.

This is stronger than DISSEMINATION WITNESS 001 because it does not rely on repository-backed retrieval of the deployed commit.

## What this does not earn

This witness still does not prove:

- search-engine indexing;
- Common Crawl inclusion;
- Internet Archive capture;
- persistent third-party mirroring;
- model-training ingestion;
- broad ecosystem adoption.

Those are later dissemination witnesses.
