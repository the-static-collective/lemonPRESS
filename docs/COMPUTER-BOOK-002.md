# COMPUTER BOOK 002 — Severance

Status: executable proof  
Lane: `press/crawler`  
Depends on: COMPUTER BOOK 001

## Objective

Test the founding crawler-press claim under actual loss of local context:

> A severed limb should still know which body it came from.

COMPUTER BOOK 001 proved arbitrary entry while the full local body remained available.

COMPUTER BOOK 002 removes that comfort.

The observer receives one valid fragment and no manifest, no relation file, and no neighboring fragments. The fragment must preserve its own declared identity, ancestry, uncertainty, and no-authority state without fabricating the missing body.

## Core laws

```text
SEVERANCE != ORPHANHOOD
UNAVAILABLE != NONEXISTENT
UNKNOWN != EMPTY
SELF-IDENTIFICATION != COMPLETE RECONSTRUCTION
FRAGMENT != BOOK
RETRIEVAL != AUTHORITY
LOSS != LICENSE TO INVENT
```

## Proof arrangement

The specimen is an exact copy of COMPUTER BOOK 001 fragment `002-loss-is-visible`.

The severance test then copies that fragment into an otherwise empty temporary directory before probing it.

Inside that observation window:

```text
fragment                PRESENT
declared work identity  PRESENT
declared ancestry       PRESENT
manifest                UNAVAILABLE_LOCAL
neighbor fragment       UNAVAILABLE_LOCAL
whole body              UNKNOWN
authority               none
```

The probe may report what is locally present, what the fragment itself declares, and what is unresolved.

It may not turn local absence into a claim of global nonexistence.

## Observation grammar

Every missing referenced object carries two different fields:

```text
availability = UNAVAILABLE_LOCAL
existence    = UNKNOWN
```

That distinction is the point of the specimen.

A machine can know that an artifact did not arrive in its current observation window without knowing that the artifact does not exist.

## Hostile cases

The executable tests require the probe to:

- preserve work, edition, fragment, ancestry, and uncertainty from the severed fragment;
- return UNKNOWN for the missing manifest's existence;
- return UNKNOWN for the missing continuation target's existence;
- refuse authority escalation;
- refuse to guess missing identity;
- ignore unsupported embedded claims that the whole book is complete or canonical;
- preserve byte identity between the source fragment and the severed copy.

## Non-goals

This proof does not recover missing fragments, query the network, infer a complete graph, repair damaged bytes, establish source truth from self-report, or certify that the declared parent work still exists.

Those are later problems.

## Executable check

`python -m unittest tests.test_computer_book_severance -v`

`python tools/computer_book_severance.py specimens/computer-book-002/severed/fragment.json`

## Earned claim

If this passes, LemonPRESS can preserve a bounded, attributable reading occurrence after local context loss without manufacturing the missing world.
