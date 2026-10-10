# LETTER CYCLE 001 — The Static Letter

**State: executable internal proof candidate; not a published newsletter, postal dispatch, real subscriber, or verified reader response.**

Existing source and existing physical fulfillment remain independent:

    ¿another clue? — admitted book and approved print proof
      + Daily Slice — dated public witness
      -> letter-cycle editorial candidate
      -> letter PDF + branching 4x6 index card PDF + 4x6 return slip PDF
      -> operator proof review / deliberate print decision (not done)
      -> Recipient Mailer / Dispatch Gate (not done)
      -> human reply held privately
      -> explicit editorial review
      -> unpublished next-issue candidate

The letter is newly written editorial copy, **not** an automatic reprint of the manuscript. The source pointers are separate and traceable. The card grammar is Zettelkasten/Antinet-inspired; it neither reproduces a commercial course nor claims formal adoption of a particular branded method.

## Pilot 001: make a proof

Run from a checkout of this experiment branch:

    python tools/letter_cycle.py proof letter-cycle/001/issue.json --out /tmp/static-letter-001

Generated artifacts:

    /tmp/static-letter-001/letter.pdf
    /tmp/static-letter-001/index-card-4x6.pdf
    /tmp/static-letter-001/return-slip-4x6.pdf
    /tmp/static-letter-001/manifest.json

Inspect the **rendered pages** before printing. Each page has a size and an overflow guard. The script uses the existing stdlib-only PDF primitive in Recipient Mailer. It does not provide graphic design, print imposition, postal address collection, postage, accessibility assurance, or a real return address.

## Test a synthetic return, without inventing a recipient

    python tools/letter_cycle.py receive letter-cycle/001/synthetic-response.json \
      --manifest /tmp/static-letter-001/manifest.json \
      --out /tmp/static-letter-001-private

    python tools/letter_cycle.py decide \
      --hold /tmp/static-letter-001-private \
      --decision consider --reviewer "local test operator" --human-confirmed

    python tools/letter_cycle.py next \
      --hold /tmp/static-letter-001-private \
      --topic "Can a crease become a source?" \
      --out /tmp/static-letter-002-candidate.json

The fictional test reply explicitly declares SIMULATION and produces only a **non-public candidate pointer**. Reply text is never automatically copied into the next issue. This does **not** prove printing, mail carriage, response rates, commercial viability, delivery, or readership.

Run tests:

    python -m unittest discover -s letter-cycle/tests -v

## House boundaries

- The title **The Static Letter**, the page layout, and this publication proposal are editorial candidates, not formal public releases.
- Proofing an internal new letter does not publish *¿another clue?*, or license other sources.
- Local reply, consent, editor and contributor details must never be committed to this public repository. Receive, decide and next require destinations **outside** the checkout.
- A checkbox on a physical return slip is not a verified machine permission record. Real consent must be recorded accurately at local intake and remain revocable under the eventual submission policy.
- Existing tools/recipient_mailer.py and tools/dispatch_gate.py govern recipient and carrier boundaries. No duplicate mailer or invented tracking record is introduced.
- The human reviewer explicitly chooses between hold, decline or consider; even consider is **not** an admission to publication or canon. A named reviewer is a declaration, not cryptographic identity verification.
- The next issue will require independent editorial composition and a new proof or release decision.
- Real-world distribution needs a real return channel, opt-in recipient, privacy notice, production budget and operator review.

    SOURCE != PROJECTION
    PROOF != PUBLICATION
    REPLY != CONSENT
    CONSENT != ADMISSION
    CONSIDERATION != SELECTION
    DELIVERY != READERSHIP

**Next physical test:** operator visually reviews the three PDFs, chooses one consenting test recipient, uses existing last-mile boundaries for the *actual* sending, and records any *actual* return without confusing it with the synthetic fixture.
