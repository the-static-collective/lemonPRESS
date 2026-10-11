# GOATnote Marginalia Press 001 — a private reading edition

**State: experiment / candidate / NOT ADMITTED / NOT RELEASED.** This is a deliberately separate LemonPRESS branch. Nothing is automatically added to catalog.yaml or admissions/, nor to physical, digital, crawler, or archive production lanes.

## New workflow

1. A person in GOATnote deliberately selects one exact source passage with a previously saved margin and optionally a source-bound GOATedge. GOATnote downloads one private, plain-text JSON packet with a self-checksum. No full note text, unrelated margins, Return Threads, or private notebook data are carried.
2. The person decides independently whether to hand that file to LemonPRESS's local CLI. There is no background synchronization, automatic publication, or network transfer.
3. Run inspection first:

       node tools/goatnote_margin_cli.mjs inspect /path/to/selected-margin.json

   This prints only summary status and integrity classes, not confidential quote or marginal words.
4. Compose a **private local candidate**, choosing a NEW directory whose parent exists and that is **outside the public Git repository**:

       node tools/goatnote_margin_cli.mjs compose /path/to/selected-margin.json /private/path/new-reading-candidate

   This writes two files with create-only semantics: candidate.md and candidate.json. Their manuscript and IDs are deterministic for an identical packet. The Markdown includes the selected source excerpt as a literal fenced text block and later margin separately. Relation first-perceived time is labeled as a human observation, not original source occurrence time. Metadata explicitly refuses house admission, editorial selection, rights grants, publication and external signer identity.
5. Later editorial selection, rights review, source verification, edition composition or Press Gate crossing must be separate explicit work. This primitive cannot do them.

## Verified / unverified distinction

The importer verifies a SHA-256 self-checksum of the packet and the **selected quote**. No third party is authenticated: a malicious actor can rewrite a packet and recompute both self-checksums. The **complete GOATnote source-version bytes are absent**; its declared SHA-256 cannot be independently recomputed from the quote. Press carries that distinction as DECLARED_NOT_REVERIFIED_NO_BODY.

GOATedge's status (including locally admitted) is local human navigation data. It is **not** a lemonPRESS work admission. Publication rights and consent remain ungranted. No personal testimony should be copied into a public PR, GitHub commit, shared Drive or publishing folder without deliberate separate review.

## Candidate composition grammar

The private markdown manuscript preserves:
- Selected source title, immutable version pointer, precise excerpt, quote digest.
- Later human marginalia, its kind and recorded date.
- Optional GOATedge type, first-perceived time, selected status, discovery trace and declared evidence path.
- Source hashes, imported declaration posture and authority disclaimers.
- Source and descendant identity as separate things.

Arbitrary source text is placed in variable-length literal Markdown code fences so embedded code/HTML/images/links are not rendered as live markup. This is an **editorial draft**, not an output renderer or rights validator.

## Verification

- Node 24 native tests: tests/goatnote_marginalia.test.mjs.
- New GitHub Actions workflow: .github/workflows/goatnote-marginalia.yml.
- Synthetic fixtures only; no private GOATnote material committed.
- Separate GOATnote branch tests the browser-export UI with mobile/nested Chromium.
- Physical-device delivery, printed copies, public crawlers and user-approved editorial publication remain **NOT CLAIMED**.

**THE SOURCE STAYS WHERE IT WAS. THE READER DOES NOT.**

**SOURCE != PROJECTION · MARGIN != SOURCE · RELATION BIRTH != SOURCE BIRTH · PRIVATE CANDIDATE != HOUSE ADMISSION · PROOF != PUBLICATION.**
