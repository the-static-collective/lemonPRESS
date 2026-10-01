# Press Gate

Press Gate is the physical-edition boundary for lemonPRESS.

It turns an admitted work plus selected production decisions into a portable, inspectable edition packet.

## Minimal packet

    manifest.json
    SPEC.md
    PRINT-RECEIPT.md
    BACKMATTER.md
    artifacts/

Use tools/press_gate.py new to scaffold one.

Use tools/press_gate.py add-artifact to copy and hash a production artifact into the packet.

Use tools/press_gate.py check to verify packet identity, required files, declared artifacts, SHA-256 values, byte counts, and PDF signatures.

## What the gate does not do

It does not decide that a work should be published, silently select "latest," choose a printer, declare a proof visually correct, collapse an edition into a file, or turn a Physical Composer recommendation into a human selection.

The first physical proof of Another Clue predates this folder contract and remains valid historical evidence. See ANOTHER-CLUE-MAP.md.

> **PROOF != PUBLICATION**
