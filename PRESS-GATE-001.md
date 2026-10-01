# PRESS GATE 001

> A work is not ready for matter merely because it has a PDF.

Press Gate is the repeatable crossing between an admitted lemonPRESS work and a proofable physical edition packet.

It does not decide what a book should become. That belongs to the human editor and, later, the Physical Composer.

It answers a narrower question:

> **Can this proposed edition cross into paper without losing identity, provenance, production facts, or unresolved decisions?**

## Gate law

    WORK != EDITION
    EDITION != FILE
    FILE != PRINTED OBJECT
    PROOF != PUBLICATION
    RECOMMENDATION != SELECTION
    LATEST != AUTHORIZED

A successful crossing produces an **edition packet**. The packet is the durable production address for one physical edition.

## Packet contract

Every Press Gate 001 packet contains:

    manifest.json
    SPEC.md
    PRINT-RECEIPT.md
    BACKMATTER.md
    artifacts/

Optional carriers may include interior text, cover notes, vendor notes, QA evidence, or source maps.

The manifest names the admitted work, edition, source revision/admission receipt, gate state, selected physical facts, artifacts and hashes, publication state, and unresolved decisions.

## Gate states

    scaffold
    preflight
    proof_candidate
    approved_print_proof
    released_physical_edition
    held
    rejected

A packet may move backward. A later proof does not erase an earlier proof.

## Fail closed / remain open

Press Gate fails closed on:
- work identity;
- edition identity;
- source/admission provenance;
- artifact integrity;
- proof-versus-publication state.

It may remain open on material decisions if they are explicitly held.

## Existing specimen

works/another-clue/physical-proof-001/ predates this formal gate and already demonstrates most of the law: stable edition identity, exact source revision, byte count, SHA-256, visual QA, and an explicit proof/publication distinction.

Press Gate 001 is therefore a **formalization of discovered practice**, not replacement history.

See press-gate/ANOTHER-CLUE-MAP.md.

## Executable surface

tools/press_gate.py provides a dependency-free local gate.

Example:

    python tools/press_gate.py new       --work-id lemonpress:example       --edition-id lemonpress:example:physical-proof-001       --title "Example"       --source-revision "source locator"       --admission-receipt "main:works/example/ADMISSION.md"       --out works/example/physical-proof-001

    python tools/press_gate.py add-artifact works/example/physical-proof-001 path/to/interior.pdf interior
    python tools/press_gate.py check works/example/physical-proof-001

The script records hashes and checks the packet. It does not decide whether a proof is aesthetically good.

## Physical Composer seam

Press Gate receives decisions. It does not invent them.

The future Physical Composer may propose trim, binding, paper, sequencing, inserts, folds, writable spaces, removable matter, or other material behavior, but its output remains a proposal until a human selects it.

The handoff contract lives at physical-composer/INTERFACE-001.md.

> **The composer imagines the body. The gate proves which body crossed.**
