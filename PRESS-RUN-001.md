# PRESS RUN 001 — THE QUEUE

Press Run is the orchestration layer above Physical Composer and Press Gate.

It does not mean "print everything."

It means:

> **Give every admitted physical candidate an explicit next crossing.**

## Pipeline

    HOUSE / ADMISSION
          |
          v
       QUEUE ITEM
          |
          +--> compose
          |      |
          |      v
          |  Physical Composer
          |      |
          |      v
          |  HUMAN SELECTION
          |
          +--> gate_preflight
          |      |
          |      v
          |   Press Gate
          |
          +--> proof_review
                 |
                 v
           existing proof lineage

A queue state is operational context, not a rank or verdict on the work.

## First queue

Press Run 001 is grounded in the six works already released into lemonPRESS production through Little Free Library Releases 001 and 002.

It does **not** pull the entire held shelf into print.

The first six crossings are:

- LP-NM-001 — nuMATHELOLOGY, First Edition
- LP-RD-001 — THE ROAD DREW ITSELF
- LP-CLUE-001 — ¿another clue?
- LP-NM-002 — nuMATHELOLOGY, Second Edition
- LP-NNM-TM-002 — nunuMath v0.2
- LP-NNM-101-001 — nunuMATH 101

## Queue laws

    REGISTRATION != PRINT QUEUE
    QUEUE != AUTHORIZATION TO PUBLISH
    RECOMMENDATION != SELECTION
    PROOF != PUBLICATION
    PRIOR EDITION SPEC != INHERITED SPEC
    EXISTING PROOF != NEED TO RECOMPOSE

## Executable surface

Run:

    python tools/press_run.py press-run/001/queue.json --out press-run/001/generated

The runner:
- validates queue identity;
- preserves items that already have a proof or fixed physical body;
- invokes Physical Composer only for items explicitly marked compose;
- emits a run report plus one composition JSON per compose item.

It does not make human selections.

## Next physical action

The generated report divides the stack into three practical piles:

1. **COMPOSE** — needs material-form proposals.
2. **GATE PREFLIGHT** — body/spec already exists; establish an edition packet without inventing new form.
3. **PROOF REVIEW** — a proof lineage already exists; inspect the actual object before mutating it.

That is enough machinery to turn the printing stack into a production line without flattening the books into sameness.
