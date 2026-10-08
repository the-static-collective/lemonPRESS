# RENJI RELAY 001 — The Page That Arrived

**TRANSFORM != SEVER** now has an executed, byte-bound specimen, not just a route declaration. One selected external PNG crosses a frozen EN → JA → EN text route, declared reading-order remix, native style-stack resolution, draft press-candidate assembly, a signed reLATTE crossing, a deliberately incapable foreign renderer, and an experimental receiver's local disposition.

The verified donor is `RENJI_SOURCE_001`, a 1086 × 1448 PNG headed **JUBILEE ENGINE // MID-CLIMAX**, with SHA-256 `bf872940599f2af4114bf75653655dd22e8441bfe436d5d3e53252eb4e3307d5` and 3,806,655 bytes. Its title is observed, not overwritten with a presumed Renji identity. The other four donor hashes remain recorded external declarations; they were not rematerialized in this run.

Eleven explicitly located text particulars enter the translation route. Japanese is an actual hashed intermediate parent of returned English. Ten particulars arrive; the omitted dialogue and all original texts remain in the packet. Drift includes constant → something unchanging, bro → partner, and reaching → extending a hand. The transcript and translations are assistant-authored frozen evidence, not an independent translator or OCR witness.

The standalone renderer consumes Japanese primary / English witness channels and declared order. It cannot decode PNGs, copy art, reconstruct panels or reproduce source pixels. Palette and panel behavior remain declared ancestors, with their loss at the renderer recorded explicitly. Its output is an HTML receipt scroll, not a visually faithful manga page.

## Executed evidence

`witness/` holds the observed signed crossing, RECEIVE and local disposition receipts, public journal, restart snapshot and render receipt. `witness.json` pins the source, recipe, packet, crossing and arrival identities. The source PNG and portable bundle remain external, in the user's Drive arrival folder; no source pixels or private signing keys are vendored into Git.

reLATTE ran unchanged at `dcc8cdca84c440aa4294134f020fb7095bf87f24`. Its native envelope and receipt verifiers accepted the witness; `LocalReceiver.open` reconstructed the same state after restart. The separate cold verifier uses only Node built-ins and Python's standard library. It rechecks source bytes, ancestry, payload binding, P-256 signatures, renderer replay, the signed render declaration, journal chain and receiver state. No LemonPRESS or reLATTE package is required on the far side.

The receiver's **ADMIT** is scoped to `world:renji-receipt-scroll-experiment`. It creates no LemonPRESS house admission, source authority, ownership claim, redistribution grant or publication. Experimental keys prove signature integrity; they do not establish an owner's identity.

## Reproduce

Materialize the exact selected PNG from the grounded Drive ID in `source-manifest.json`. Build and sign in a fresh output directory; reuse recorded signatures for verification rather than re-signing a replay.

```sh
python3 -m pip install -r requirements-style.txt
git clone https://github.com/the-static-collective/reLATTE.git out/relatte
git -C out/relatte checkout dcc8cdca84c440aa4294134f020fb7095bf87f24
npm install --prefix out/relatte --omit=dev --ignore-scripts --no-audit --no-fund
python3 works/renji-relay-001/run.py _external/source.png out/arrival
node works/renji-relay-001/relatte_bridge.mjs seal out/arrival out/relatte
node out/arrival/verify-crossing.mjs out/arrival --expected-source bf872940599f2af4114bf75653655dd22e8441bfe436d5d3e53252eb4e3307d5
python3 out/arrival/foreign_renderer.py out/arrival
node works/renji-relay-001/relatte_bridge.mjs receive out/arrival out/relatte out/private-receiver ADMIT
node out/arrival/verify-crossing.mjs out/arrival --expected-source bf872940599f2af4114bf75653655dd22e8441bfe436d5d3e53252eb4e3307d5
```

For the recorded occurrence, add `--expected-crossing` using the crossing ID in `witness.json`. The source hash must come from a separately trusted manifest. An internally consistent replacement root is not proof of the original source. `verify.py` can additionally require the exact recipe hash with `--expected-recipe`.

The press step is a bounded renderer-neutral **candidate** assembler in this edge specimen. It does not bypass the separately gated Manga Press edition/admission stack. Style resolution uses the native `tools/manga_style_resolve.py` implementation from PR #45; reLATTE signing and local receiver calls use its native runtime. No normative reLATTE semantics are reimplemented or changed by the adapter.

## Hostile checks

```sh
RELATTE_RUNTIME=/absolute/path/to/pinned/relatte python3 -m unittest discover -s tests -p 'test_renji_relay.py' -v
```

CI uses a valid synthetic PNG. With `RENJI_SOURCE_PNG=/absolute/path/to/exact/source.png`, the same 18-test suite runs against the real donor. Both runs passed locally; all 13 named hostile cases are executable and covered, plus signature/artifact tamper, create-only conflicts, inventory and recorded-witness signature checks. Expected outcomes are frozen in `hostile-results.json`.

The center remains:

- pixel-identical output + broken ancestry → FAIL
- radically transformed output + intact declared ancestry → PASS
- valid crossing + local REFUSE → VALID_REFUSAL
- valid crossing + experimental local ADMIT → VALID_ADMISSION

## WRENCH

INPUT: one byte-verified PNG and eleven declared text excerpts. TRANSFORMATION: freeze Japanese and returned-English stages, reorder ten placements, resolve the style stack, assemble a draft carrier, sign and carry it, typeset a foreign scroll, record experimental local ADMIT. OUTPUT: exact arrival HTML and a portable replay bundle. RESIDUAL: immutable PNG, omitted text, original/JA/returned text, profile ancestry, signed receipts and public journal. LOSS: source art, palette, panel geometry, typography and declared semantic nuances. UNKNOWN: semantic equivalence, independent translation quality, owner/signing identity and publication rights. STOP: the experiment earns a traceable transformed arrival; it does not earn a house release or prove aesthetic/semantic sameness.
