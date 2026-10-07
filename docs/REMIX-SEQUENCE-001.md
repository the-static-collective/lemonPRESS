# REMIX SEQUENCE 001 — declared reading-order remix

**Status:** executable v0  
**Output state:** CANDIDATE only  
**Stacked after:** MANGA REMIX 001 / PR #25

REMIX SEQUENCE 001 gives LemonPRESS a deterministic reading-order primitive. It declares how already-addressable pages, panels, regions, or candidate descendants occur in a new sequence without changing the parents.

~~~text
declared parents
      |
      v
sequence.json
      |
      v
schema + invariant checks
      |
      v
deterministic candidate.json + RECEIPT.md
      |
      v
explicit later selection / admission
~~~

## What this is

A sequence is a declared descendant order.

v0 supports:

- reorder
- omit
- repeat
- whole-item selection
- normalized region selection
- opaque panel references

A repeated source_ref is another slot occurrence. It is not a new source identity.

An omitted parent remains in parents[]. It disappears only from descendant order.

## What this is not

It is not source mutation, editorial selection, issue admission, publication, canonization, ownership transfer, or house release.

The tool is intentionally byte-blind. It does not fetch or rewrite parent media. It validates that every source_ref is declared and that selectors are structurally valid.

## Non-collapse laws

~~~text
REORDER != SOURCE MUTATION
ORDER != ANCESTRY
READING ORDER != OWNERSHIP
SEQUENCE != ADMISSION
OMISSION != DELETION
DUPLICATION != NEW SOURCE
SLOT != PAGE IDENTITY
CANDIDATE != ISSUE
~~~

## CLI

~~~bash
python3 tools/manga_sequence.py works/home-grows-open-sequence-001/sequence.json
python3 tools/manga_sequence.py works/home-grows-open-sequence-001/sequence.json --verify
~~~

By default the tool writes candidate.json and RECEIPT.md beside sequence.json.

Outputs are create-only: an identical replay is idempotent; conflicting existing bytes refuse.

## Deterministic identity

Canonical JSON uses sorted object keys, UTF-8, compact separators, and finite JSON numbers.

sequence_sha256 hashes the declared sequence[] exactly.

candidate_id hashes the complete validated v0 sequence declaration:

~~~text
manga-sequence:sha256(canonical_json(sequence_spec))
~~~

Therefore declared order, selectors, parent provenance, sequence ID/title, authority boundary, or law-set changes produce a different candidate identity. Incidental formatting does not.

Array order is never silently sorted. slots[] preserves sequence[] exactly.

## Selectors

Whole:

~~~json
{"kind":"whole"}
~~~

Region:

~~~json
{"kind":"region","x":0.12,"y":0.08,"width":0.43,"height":0.52}
~~~

Region coordinates are normalized 0..1; width/height must be positive and the rectangle must remain inside the unit square.

Panel:

~~~json
{"kind":"panel","panel_id":"p3"}
~~~

Panel IDs are opaque in v0. This primitive does not extract or infer panels.

## WRENCH

Every candidate records:

- INPUT — all declared parents, including omitted ones
- TRANSFORMATION — declared slot-preserving reading-order remix
- OUTPUT — candidate identity plus sequence hash
- RESIDUAL — parent particulars remain unchanged and independently addressable
- LOSS — omitted parents plus the loss of undeclared source adjacency
- UNKNOWN — publication, canon, and issue-admission state
- STOP — candidate only; explicit local selection/admission remains required

## HOME GROWS OPEN witnesses

Both specimens declare the same four parent particulars:

1. Rosemary Violet Home
2. Fidelity Friday — Small Things Grow
3. Last Light / Open Circuit
4. HOME GROWS OPEN remix candidate

Sequence 001 is the plain narrative arc.

Sequence 002 moves the remix candidate directly after Rosemary Violet Home.

The parent set is unchanged. The order differs. The candidate IDs and sequence hashes differ. No source is mutated.

Only the Rosemary Violet Home Drive ID was already part of the implementation brief. The other three are intentionally carried as opaque witness references rather than invented remote IDs. Sequence semantics do not depend on network resolution.

## Relation to LemonPRESS primitives

~~~text
parcel       = identity / provenance
pixel remix  = visual recomposition
sequence     = reading-order recomposition
press        = admitted issue/page assembly
~~~

MANGA REMIX 001 can create a visual candidate. REMIX SEQUENCE 001 can then declare where that candidate occurs among other parents. Neither primitive self-admits.

## Relation to Playdeck

LemonPRESS sequence decides occurrence order.

Playdeck decides temporal behavior.

A future handoff may import a sequence candidate into Playdeck, but timing, animation, audio, transitions, and performance remain outside this primitive.

## Deferred extensions

Do later, behind new declarations rather than by changing v0 meaning:

- named interleave operators
- splice operators
- reverse operators
- grouped sub-sequences
- alternate reading paths
- branching issue futures
- actual panel extraction
- rendered contact sheets
- issue-admission bridge
- direct Playdeck importer

Manual alternation is already representable in v0 by explicit slots; the deferred interleave feature means a higher-order declarative operator, not hidden inference.
