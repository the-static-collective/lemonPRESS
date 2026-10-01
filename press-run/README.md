# Press Run

Press Run is lemonPRESS's physical queue.

A run contains only works with a real production reason to be there. Registration in the Little Free Library does not automatically enqueue a work.

## Modes

- `compose` — no physical body is established; ask Physical Composer for proposals.
- `gate_preflight` — a physical body/spec already exists; prepare it for Press Gate without recomposing.
- `proof_review` — a proof already exists; inspect the object before changing it.
- `hold` — deliberately stop.

## First run

`001/queue.json` contains the six production-active works from Little Free Library Releases 001 and 002.

Execute it with:

    python tools/press_run.py press-run/001/queue.json --out press-run/001/generated

The runner never performs the human selection step.

> **QUEUE != AUTHORIZATION TO PUBLISH**
