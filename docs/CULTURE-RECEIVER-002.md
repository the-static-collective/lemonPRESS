# CULTURE RECEIVER 002 — independent lemonPRESS source/edition HOLD

**2026-10-29 / experimental branch only / not a house admission or publication.**

Receives **actual CANNON-generated `comic.html` and `field-card.md`**, verifies each exact SHA-256 in the original CANNON receipt, recomputes its unsiged source manifest digest, and makes an independently authored receiver-local decision: `HOLD` or `REFUSE`. The human editorial and rights review is separate and never silently converted to `ADMIT`.

A successful `HOLD` creates a new folder with exact unchanged `comic.html`, `field-card.md`, `candidate.json`, and `hold-receipt.json`. A `REFUSE` writes only its candidate and receipt; it does **not** copy source media into a publishing shelf.

The existing [lemonPRESS HOUSE constitution](../HOUSE.md) says **source != projection**, **work != edition**, and **proof != publication**; house admission belongs to independent editorial action. This receiver is isolated from `library/catalog.yaml` and `admissions/`: no house work ID, edition, print permission or catalog entry is registered.

This is intentionally an original **lemonPRESS native source function**, not a CANNON-created mock that impersonates the press. It can be run independently:

```sh
node --test tests/held-culture.test.mjs
node intake/held-culture-cli.mjs receive ../culture-out ../press-held HOLD
node intake/held-culture-cli.mjs verify ../culture-out ../press-held HOLD
```

No npm packages, network, signatures, monetary systems, human identity systems or publishing system needed.

## What is verified vs unknown

CANNON verifies source commit and output bytes in its own repository, at an independently reproducible exact source pin. lemonPRESS independently checks the CANNON **receipt bytes and artifact hashes**, and can reject forged publication/rights/money fields. **This is integrity, not authentication of a human, source owner or actual copyrighted work.** The receiving review has no author license or publisher grant. Do not distribute unreviewed source as an official edition.

The receiver's candidate is non-economic and has no right to issue PENNY/Deeds, transfer title, set prices, mint NFTs, send emails or publish to Abundent. An externally visible source artifact uploaded by CANNON Actions is still **not an admitted lemonPRESS edition**.

A future release needs source-author verification, editorial authority, a rights statement, distinct edition selection, optional physical print QA, and an actual publication decision recorded by the publishing house.

## Independent recipient acceptance test

The next CANNON integration should download/pin this exact lemonPRESS source commit, **execute this original `receiveLocal` and `coldVerifyLocal` after the native CANNON 001 build**, verify byte-equal receipt lineage and reviewer HOLD, and upload both original artifacts and independently owned held press packet. This qualifies as an actual cross-repo execution, still synthetic and not an external publication.
