# KEEP-A-PLACE-002 — an illustrated comic crosses into lemonPRESS (HELD)

This pilot is the **first actual image-bearing descendant** of the "Keep a Place for Me" Story DNA five-beat proposal. It is not a final manga edition and no public rights or publication authority are implied.

## Source and scope

- Story DNA source: [experimental PR #4](https://github.com/the-static-collective/story-dna/pull/4), owner-uploaded `Keep a Place for Me.mp3` verified locally as **4,586,389 bytes**, SHA-256 `7f16ead290a86a5997e714e1280befe282b4047c1d40de07e36849521cd304d1`.
- Narrative source: separately supplied **`story-dna/private-local-storyboard-preview/v0`** JSON with five factual motif observations and original fictional scene staging.
- Illustrated source: five **new** bounded SVG scenes `KP01.svg`–`KP05.svg`, held by the operator, not uploaded to this public repository and not assumed to be licensed for redistribution.
- The full track, transcript, external Suno ID and real-person likeness are **not in Git**.

The offered composition has five images: a rain-washed window and kettle; a clock with a missing fourth beat, hinge and worn cup; a table with an open chair; a lighted threshold and spare key; and an imperfect house after the rain. The reader may play the owner-held local audio beside them and make separate KEEP/HOLD/REVISE/REFUSE notes. Those notes do not become publication receipts.

## Actual lemonPRESS adapter

`tools/story_dna_panel_intake.py` accepts an owner-held JSON storyboard plus five locally present SVG illustrations. It:

1. Revalidates the exact source track digest and original five panel IDs/time windows.
2. Rejects missing/duplicate pages, overlapping cue ranges, silent rights escalation, guessed platform identity and unbounded notes.
3. Rejects SVG assets containing script tags, inline event handlers, external URLs, data references, foreign objects and other active-content indicators. **This is a constrained static-art intake, not a general-purpose SVG sanitizer.** Never use it as a browser-safe HTML sanitization service.
4. Copies the five distinct art assets into a create-only folder and generates `lemonpress/held-illustrated-panel-parcel/v0`, SHA-256 sealing both the manifest and each image byte payload.
5. Independently rechecks all five file digests, boundaries and the absence of admission, editorial lettering or publication rights before emitting a plain HOLD witness.

The tool is intentionally **not** a `manga-page/v0` **issued** page or a press-gate admission. That existing schema correctly requires a distinct house-level work admission and edition admission. This pilot stops before that gate, and does not forge them for demo convenience.

Example in a trusted operator checkout:

```bash
python3 tools/story_dna_panel_intake.py build \
  /private/Keep_a_Place_First_Crossing.json /private/keep-illustrations/ \
  /private/keep-a-place-held-parcel/
python3 tools/story_dna_panel_intake.py verify \
  /private/keep-a-place-held-parcel/manifest.json \
  /private/keep-a-place-held-parcel/
```

Tests: `pytest -q tests/test_story_dna_panel_intake.py`.

## First verified local operator result (not Git-committed)

A user-downloadable **offline** HTML reading proof contains five actual symbolic vector images with the uploaded audio byte-identical to its local source. The accompanying art-only parcel (five SVGs + manifest) is source-pinned and does **not** distribute the song.

Observed portable art-only parcel digest: `d0d44574ed0a48a4a25fb54106739854e567c8c60459d10a6e5fb780f9c0c5a8`.

## Why a second project matters

Story DNA owns a narrative interpretation. lemonPRESS owns whether those images ever become a work or edition. An image file arriving here cannot grant those decisions. This is a real, inspectable **media carrier crossing** while source admission still remains HOLD.

**SOUND ≠ PUBLIC LICENSE · PANEL ART ≠ CHARACTER LIKENESS · HELD PARCEL ≠ ISSUED EDITION · VIEWER ≠ PUBLICATION.**
