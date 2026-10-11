# MARGINALIA THREE DOORS 002 — one reading, three candidate forms

**Experimental private composition only. Draft/unmerged/undeployed.** Builds on MARGINALIA PRESS 001 and the exact GOATnote 004 selected-margin carrier.

A human-selected, source-linked passage may be composed into three **different** working forms without turning any of them into a release or pretending the missing original source was retrieved.

## Three doors

- **Page** is a literal Markdown page-layout draft. One exact quoted passage and one human margin are separately labeled. The output is not a PDF, printed sheet, print proof, physical carrier, or rights clearance.
- **Voice** is a human-readable audio performance **script**, marked by voice and silence suggestion. No audio file, Suno stem, voice synthesis, admitted PRESS MOUTH parcel, Audio Composer run, or recording permission is implied.
- **Fragment** is a private crawler-native text *draft* with explicit excerpt, human margin, relation date, hashes, and incomplete-retrieval warnings. It is not deployed, indexed, available at a public URL, or a full computer-book edition.

Each door has its own actual draft manuscript and a distinct WRENCH receipt with exact:
**INPUT / TRANSFORMATION / OUTPUT / RESIDUAL / LOSS / UNKNOWN / STOP**.
The receipts are not signed reLATTE receipts. They are local computation and editorial provenance summaries.

## Source-bound contract

An approved local operator supplies one plain-text JSON selected-margin carrier from GOATnote, created after GOATnote's disclosure confirmation. LemonPRESS independently verifies the declared packet self-check and exact quoted excerpt.

- The full immutable GOATnote source text is **not included**.
- Its version SHA-256 is **DECLARED_NOT_REVERIFIED_NO_BODY**. No upstream signer, actual author, rights owner, or permission is established.
- The quote is source text as selected and declared, the margin is **later human interpretation**. The relation first-perceived timestamp is **the human discovery date**, not the source creation date.
- No private Return Threads, other source bodies or unselected margins may be carried.
- A GOATedge marked admitted is STILL NOT a LemonPRESS admission.
- No edition, work, publication, release, mailing, or recording rights are granted.

All generated artifacts are **private local files**. The output directory is create-only and needs to be new; the CLI never overwrites an existing run.

## Run locally (Node 24, in the experiment branch)

1. Export the selected margin from GOATnote (no direct cross-app sync).
2. Inspect the local carrier:

       node tools/marginalia_three_doors_cli.mjs inspect /private/selected-margin.json

3. Prepare all three private candidate forms in a new directory:

       node tools/marginalia_three_doors_cli.mjs compose /private/selected-margin.json /private/new-edition-set

   Or opt into a subset (order canonicalized to page, voice, fragment):

       node tools/marginalia_three_doors_cli.mjs compose /private/selected-margin.json /private/new-two-doors --doors=page,voice

4. Cold-verify every private manuscript, score, source-selection packet and receipt:

       node tools/marginalia_three_doors_cli.mjs verify /private/new-edition-set

The directory contains source-selection.json, score.json, reading-candidate.json, reading-candidate.md, the selected subset of page.md / voice.md / fragment.md, and one corresponding receipts/*.json per door. The manifest and receipts carry source hashes and explicitly deny any authority lift.

Keep this output OUTSIDE public Git branches, shared sites or connected Drive folders until human privacy, ownership, and publishing-rights decisions are separately made. Files are plaintext, created with restrictive POSIX permissions, which do not constitute encryption or guarantee device privacy.

## Gates and hostile witnesses

Node tests exercise canonical lane selection, no duplicate/dangerous doors, independent losses, receipt hashes, create-only local output, and cold replay. They edit page output, WRENCH receipt and score state to ensure replay catches all three corruptions.

A separate **real cross-repo interoperability** test checks out the actual GOATnote selected-margin exporter at public commit 95e63de4fdbbe1132294a5798a81b8d1a745fb18. It builds a synthetic GOATnote notebook, produces a packet through the actual upstream function, and feeds it into the LemonPRESS verifier and all three door composers. No private notebook or live user data enters source control.

## Limits still held

- These are three candidate **drafts**, not actual PDF, synthesized music, audio recordings, or deployed crawler pages.
- The entire copy stays on operator's local filesystem and no automatic sync/backups exist.
- Real physical-device review, editorial selection, signer verification, license/rights, format-specific editions and deployment are NOT COMPLETE.
- The visual page and voice script are proposed transformations. A subsequent actual renderer and edition gate must create evidence of an actual edition.

**SOURCE ≠ MARGIN · MARGIN ≠ EDITION · CANDIDATE ≠ ADMISSION · SCORE ≠ RENDER · RENDER ≠ RELEASE · RELATION ≠ AUTHORITY · LOSS MUST BE VISIBLE.**
