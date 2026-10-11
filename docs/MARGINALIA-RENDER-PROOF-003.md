# Marginalia Rendered Proof and Editorial Gate 003

**Experimental / private / unmerged / undeployed. No real personal material used.**

## Actual artifacts, not only textual projection plans

This branch extends MARGINALIA THREE DOORS 002 with two *rendered* carriers from one independently replay-verified, human-selected GOATnote margin:

- **Page door:** an actual **6 × 9-inch vector-text PDF**, with source quotation, later human margin, optional dated discovery relation, provenance qualifications and repeated private-proof footer on every page. Supports ordinary Western/Greek characters via local DejaVu fonts; refuses unsupported glyphs rather than silently replacing them. Long text flows to subsequent pages. This is a **private print proof**, NOT printer-ready approval or publication.
- **Fragment door:** one **offline HTML file**, with accessible landmarks and internal-only fragment links, content escaped from Markdown/HTML injection, CSP blocking external network access, and noindex hints. This is a locally inspectable private proof, NOT a live public crawler page.
- **Voice door:** remains a *script* only. No audio bytes are synthesized, mixed, recorded, reviewed, licensed or released. A voice script cannot be selected as an actual rendered proof.

A synthetic fixture does exercise the **actual GOATnote 004** margin exporter and the LemonPRESS 001 + Three Doors 002 verifier/composer. No private notes or source bytes are committed.

## Exact local execution

Requires Node 24, Python 3.12, reportlab 4.4.9, pypdf 5.9.0 and local system DejaVuSans regular/bold fonts. All output directories must be **outside the public Git checkout**.

Start with GOATnote's deliberately downloaded selected-margin JSON and make the Three Doors local score:

    node tools/marginalia_three_doors_cli.mjs compose /private/selected.json /private/new-three-doors
    node tools/marginalia_three_doors_cli.mjs verify /private/new-three-doors

Render to a brand-new private directory:

    python tools/marginalia_render_proof.py render /private/new-three-doors /private/new-rendered-proof
    python tools/marginalia_render_proof.py verify /private/new-three-doors /private/new-rendered-proof

Inspect both real files (page.pdf and fragment.html). The proof-manifest.json includes exact SHA-256 and bytes of each output; its source score remains PRIVATE and source-authorship/rights remain UNVERIFIED. Its SHA is a replay aid, NOT a signed reLATTE crossing or a proof of owner consent.

**Human editorial choice is separate from rendering** and can only be captured after byte-for-byte cold replay of the PDF/HTML proof. Reviewer identity is a *local declaration, not authenticated identity*. Allowed decisions:

    python tools/marginalia_render_proof.py decide /private/new-three-doors /private/new-rendered-proof --decision HOLD --reviewer "reviewer declaration" --human-confirmed

or:

    python tools/marginalia_render_proof.py decide /private/new-three-doors /private/new-rendered-proof --decision REFUSE --reviewer "reviewer declaration" --human-confirmed

or:

    python tools/marginalia_render_proof.py decide /private/new-three-doors /private/new-rendered-proof --decision SELECT_FOR_REVIEW --selected-door page --reviewer "reviewer declaration" --human-confirmed

The action records **one immutable create-only decision** in decision.json, bound to the exact proof-manifest SHA-256 and selected proof hash. It does NOT make the work a house-admitted work, grant quotation rights, confer an author identity, authorize publication, print, mail, generate an audio edition, deploy a web page or release any private words.

## Verification and new failure surfaces

- Prior source-selection packet must pass the independent Node cold-replay verifier; stale scores / receipts / source packets HOLD.
- The renderer refuses unsupported characters, bad source structure, output inside public repository, existing output path, or a voice-only selection without renderable evidence.
- PDF pages are rendered to pixels in tests and checked for source/margin/discovery text, multi-page continuation and no silent truncation.
- HTML quotes are escaped as literal text, and it includes no remote network assets or scripts.
- Same input and exact fonts produce byte-for-byte identical PDF and HTML across separate runs.
- Changes to proof files, approval flags, manifests or upstream projection files HOLD.
- Select-for-review requires human confirmation, a reviewer declaration, a prior actual rendered door, and exact proof hash; holding/refusing selects no door.
- Re-deciding overwrites nothing. Later different choices require a new explicit branch of the history.
- Tests use **synthetic only** data and use the actual pinned upstream GOATnote exporter from commit 95e63de4fdbbe1132294a5798a81b8d1a745fb18.

## Status: release gates still on HOLD

The CI PDF pixel witness is **not real handset visual QA**, nor does it prove high-quality font coverage for all possible languages, physical printer output, accessibility with assistive technologies, rights clearance, owner consent or house admission. The HTML never leaves the user's local machine in this workflow.

The larger press topology remains distinct: **PRIVATE DRAFT → RENDERED PRIVATE PROOF → LOCAL HUMAN REVIEW → (SEPARATE HOUSE ADMISSION / EDITION / RIGHTS / RELEASE GATES)**.

**PAGE PROOF ≠ PRINT RUN · HTML PROOF ≠ PUBLIC WEB PAGE · SCRIPT ≠ RECORDED AUDIO · LOCAL EDITORIAL SELECTION ≠ PRESS ADMISSION · RENDER ≠ RELEASE.**

## Inspectable CI specimen

A successful workflow run includes a short-lived downloadable artifact named
`marginalia-render-proof-003-SYNTHETIC`, containing a real rendered `page.pdf`,
`fragment.html`, and their `proof-manifest.json`. The specimen is deliberately
fabricated for automated QA (not a user's private GOATnote reading). Artifacts
expire after seven days. The synthetic proof is not a house publication or edition
admission; individual private proofs are never uploaded by the CLI.
