# PHYSICAL PRESS

This branch produces physical lemonPRESS objects.

## Scope

- print interiors
- covers and jackets
- trim and paper decisions
- binding notes
- printer-ready exports
- proof records
- edition-specific colophons
- physical object identifiers and receipts

## Reusable crossing

**Press Gate 001** is the reusable boundary between an admitted work and a proofable physical edition packet.

See:
- PRESS-GATE-001.md
- press-gate/README.md
- tools/press_gate.py

**Physical Composer 001** proposes material form before the gate. It does not silently authorize selections.

See:
- physical-composer/README.md
- physical-composer/INTERFACE-001.md
- tools/physical_composer.py

**Press Run 001** turns the real production stack into explicit next crossings without enqueuing the whole held shelf.

See:
- PRESS-RUN-001.md
- press-run/README.md
- press-run/001/queue.json
- tools/press_run.py

## Law

[Manga Press 001](MANGA-PRESS-001.md) adds an edition/form grammar within this
lane, using existing Physical Composer selection and Press Gate packets. It
also records bounded digital intent and performance doors without admitting
those descendants or creating a new house lane.

A physical edition is a material descendant of an admitted work.

It may change pagination, typography, dimensions, sequencing furniture, cover matter, and production details without claiming those changes were present in the admitted source.

> **PHYSICAL FORM != SOURCE AUTHORITY**

> **PROOF != PUBLICATION**

> **PRINT RUN != NEW WORK**

> **RECOMMENDATION != SELECTION**

> **QUEUE != AUTHORIZATION TO PUBLISH**

Every released physical edition should name the admitted work and the exact production revision from which it was made.
