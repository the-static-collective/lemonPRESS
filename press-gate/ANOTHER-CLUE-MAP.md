# Another Clue -> Press Gate 001

This note maps the existing works/another-clue/physical-proof-001/ specimen onto Press Gate 001 without rewriting its history.

| Press Gate concern | Existing carrier |
| --- | --- |
| work identity | manifest.yaml: work_id |
| edition identity | manifest.yaml: edition_id |
| lane | manifest.yaml: lane |
| proof state | manifest.yaml: state |
| source identity | manifest.yaml: source_revision |
| admission | manifest.yaml: admission_receipt |
| trim / pages | manifest.yaml: production |
| rendered object identity | filename + byte count + SHA-256 |
| visual QA | production.rendered_qa + PRINT-RECEIPT.md |
| publication distinction | publication.house_status |
| portable interior | interior.md |

The historical packet does not need to be mutated merely to imitate the new template.

A future descendant can cross through Press Gate 001 as a new production occurrence.

## Discovery carried forward

The useful physical invariant is not "store the PDF in Git."

It is:

> **Identify the exact rendered object strongly enough that its carrier may change without its production identity becoming ambiguous.**

That is why SHA-256, byte count, source revision, edition ID, and QA receipt belong at the gate.
