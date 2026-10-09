# MATERIAL MEMORY 001
## PROVENANCE IS NOT PRESENTATION

**Status:** founding visual law and proposed executable seam; not an admitted work, rendered edition, or proof of an event.

**Origin:** critique of an ALEX ghost-hunting illustration. Every notebook, evidence bag, photograph, and written receipt was turned toward the reader. The illustration conveyed the facts it wanted read, but the depicted room did not convincingly possess a history independent of the camera.

> The evidence should not be arranged to communicate with the reader. It should be arranged by the history of what happened to it. The reader arrives afterward.

The original human insight was **spatial composition as material memory**: evidence arranged so that its present relationships carry implicit sequences of handling, concealment, wear, neglect and human imperfection — like the rings of a tree. Not maximal clutter. Not perfect exposition. **Human entropy** and **missed threads**.

## Rules

```text
PROVENANCE IS NOT PRESENTATION
OBJECT != LABEL
POSITION != POSE
TRACE != EVENT
PROVENANCE != VERDICT
ENTROPY != RANDOM NOISE
MISSED THREAD != FAILED PLOT
CAMERA != OMNISCIENCE
SOURCE != INTERPRETATION
VISIBILITY != EXISTENCE
GENERATED DEPICTION != REAL EVIDENCE
```

1. **World before shot.** The objects and their history exist as a separate declaration before viewpoint, layout, palette and panel composition are selected.
2. **History changes state.** Events may place, handle, rotate, spill, wear, mark, repair, cover, damage or remove objects, with physical and temporal constraints.
3. **Camera changes observations only.** Viewpoint, crop, field of view, occlusion, lighting, legibility and depth alter what can be seen; they do not move an object to face the audience.
4. **No pristine omniscience.** A scene may omit the most important particular, hide it behind a hand, catch only half a label or frame the wrong room.
5. **Human entropy is causal.** Repeated use, fatigue, interrupted intentions, imperfect filing, a hasty repair, a spilled drink and an unfinished annotation produce situated imperfection. Uncaused random clutter is not a substitute.
6. **Some threads are missed.** A causal trace may never be noticed, interpreted, used or resolved. Narrative payoff is not a requirement of existence.
7. **Source, observation and inference are different.** A photograph's existence or provenance, what a witness says it shows, and what an investigator concludes must retain separate attribution and uncertainty.
8. **Chronology may be partial.** Unknown or contradictory ordering is not repaired with a fabricated total order. Keep causal dependencies and conflicting reports distinguishable.
9. **Provenance belongs to particulars.** Identical-looking copies, reconstructions, edits, captions, and screenshots cannot silently inherit source identity.
10. **Style never grants authority.** A beautifully rendered ghost or official-looking receipt is not evidence of an actual supernatural event or a real-world forensic conclusion.

## Ownership split

| Layer | Owns | Must not do |
| --- | --- | --- |
| Object/world ledger | Stable object and event identities, state transitions, declared source status, unknowns | Fit objects to camera for legibility |
| Scene reconstruction | Causally reachable object state and unresolved alternatives | Invent missing past events as fact |
| Observation/camera | Position, crop, sight lines, occlusion, lighting, visible surfaces | Rewrite world state |
| Style-stack resolution | Palette, language/text channels, bounded art behavior | Become source/event/semantic authority |
| Editorial interpretation | Annotations, theories, narrative emphasis, character beliefs | Mutate source history or observation records |
| Press/admission | Separately authorized edition/production choices | Infer publication/rights from rendering |

This law is **orthogonal** to `MANGA STYLE PROFILE 001` (issue #43 / draft PR #45). It may be expressed through reusable policies or style-stack adapters, but object history is not a visual-palette field. In particular, `ARTIFACT_COLLAGE_001` may decide how to depict distinct artifacts, not invent why those artifacts are there.

## Minimal record contract (proposal, not yet implemented)

```json
{
  "schema": "lemonpress/material-memory-ledger/v0",
  "id": "MM-DESK-001",
  "fictional": true,
  "objects": [
    {"id": "photo-1", "kind": "photograph"},
    {"id": "notebook-1", "kind": "notebook"},
    {"id": "mug-1", "kind": "mug"}
  ],
  "events": [
    {"id": "e1", "order": [], "kind": "place", "participants": ["photo-1"], "source": "declared-fiction"},
    {"id": "e2", "order": ["e1"], "kind": "partially-cover", "participants": ["notebook-1", "photo-1"], "source": "declared-fiction"},
    {"id": "e3", "order": ["e2"], "kind": "ring-stain", "participants": ["mug-1", "photo-1"], "source": "declared-fiction"}
  ],
  "unknowns": ["exact elapsed time", "whether anyone noticed the stain"],
  "interpretations": []
}
```

The sample deliberately **does not** pretend to be a sufficient geometry, physics, renderer or chain-of-custody schema. A working implementation must formally specify coordinates, object state, event effects, causal and observational constraints, source binding and uncertainty rather than silently fill them from prose.

## Founding specimen: one desk, three times

**T0:** Photograph partly under notebook; mug ring forms across one exposed corner. No camera-facing orientation requirement.

**T1:** An investigator shifts the notebook, compares another image, writes on loose paper over the photograph (leaving pressure impressions), and does not restore the stack exactly.

**T2:** ALEX returns. Mug covers much of the stain, one image points away, the indentation catches grazing light. A viewpoint from the door misses the indentation. An oblique close-up may reveal part of it. Both viewpoints are valid observations of one unchanged physical state.

The reader receives T2 before (or without) T0/T1. The story does not promise to explain every feature.

## Anti-perfection test harness — future implementation

- **Camera rotation invariant:** a second camera leaves the reconstructed world state byte-identical; only the observation changes.
- **Occlusion honesty:** hidden text cannot be copied into the visible-observation record merely because the renderer knows it.
- **No audience-facing correction:** the visual planner does not orient labels, bags, photographs or notebooks toward the viewer absent a recorded cause.
- **No phantom entropy:** introduced marks, wear, damage and displaced objects have an event/cause or a marked unknown origin. The system does not claim an invented cause is known.
- **Competing testimony:** two observations can conflict without either overwriting the other.
- **Clue removal:** remove one trace; the room remains a consistent state even if a proposed plot solution fails.
- **Partial chronology:** invalid dependencies refuse; genuinely unknown order remains unresolved.
- **Interpretation independence:** change a character's ghost theory, keep the photo and custody record unchanged.
- **Cold replay:** identical ledger, policy, viewpoint and deterministic settings recreate the same observation plan and ancestry.
- **Loss accounting:** document information rendered unreadable, cropped, destroyed, absent, speculative or never observed.
- **Publication separation:** a verified visual plan remains draft/non-authoritative until separately admitted.

## WRENCH-style receipt

- **INPUT:** declared fictional objects, events, causal dependencies, provenance claims, unknowns, and camera settings.
- **TRANSFORMATION:** reconstruct the reachable material state; apply a bounded witness viewpoint; produce a visible-observation plan.
- **OUTPUT:** draft image plan, state identity, observation identity, ancestry, unresolved traces.
- **RESIDUAL:** original event claims, source artifacts, alternative interpretations and unseen particulars.
- **LOSS:** inaccessible, obscured, cropped, degraded and unobserved information.
- **UNKNOWN:** missing causes, contested dates, conflicting accounts and unresolved implications.
- **STOP:** refuse impossible causal dependencies, invented evidentiary authority or presentation rules that rewrite world state.

## First implementation door

Issue **#48** tracks schemas, a three-time fixture, cold replay, invariant tests, renderer-facing plans and an optional ALEX scene. The current document establishes the law and its non-collapse boundary; it does **not** claim the runtime is built.

A room does not face the reader. **The reader finds the room.**
