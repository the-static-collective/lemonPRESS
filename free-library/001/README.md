# Little Free Library — Release 001 — Physical Arm

**Release:** `LP-LFL-001`  
**Surface:** physical  
**Date:** 2026-09-30

This branch records print-facing decisions. It does not replace accepted source ancestors.

## LP-NM-001 — nuMATHELOLOGY

**Production state:** source edition already typeset  
**Declared trim:** **7 × 10 in**  
**Edition:** First Edition  
**Series:** Lemon Press Monographs in Structural Mathematics, Volume I

The accepted First Edition already contains its publisher's cataloging data, preferred citation, edition identifier, and print-block declaration.

**Action for proofing:** preserve the accepted interior as the ancestor. Any printer-specific reflow, margin repair, cover spine calculation, bleed addition, or PDF normalization must become a descendant with its own receipt.

## LP-RD-001 — THE ROAD DREW ITSELF

**Production state:** Source Edition 001 exists.  
**Role:** forward companion object to LP-CLUE-001.

The source edition is already a composed reading cut. Do not silently rewrite its quoted source bodies during print preparation.

**Trim:** not declared by this receipt. Pairing it physically with LP-CLUE-001 is a production option, not an inherited fact.

## LP-CLUE-001 — and THAT... will lead to another clue...

**Production state:** approved proof lineage  
**Declared proof trim:** **6 × 9 in**  
**Role:** backward companion object to LP-RD-001.

The house README already records the 6 × 9 proof lineage. Proof remains distinct from publication.

## Physical law

```text
accepted text != printer normalization
proof         != source
proof         != publication
same trim     != same work
```

When a printer-ready file is produced, record the exact ancestor, export tool, page count, trim, bleed, fonts/embedding state, and output checksum where available.
