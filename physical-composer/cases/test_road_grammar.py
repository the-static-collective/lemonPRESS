#!/usr/bin/env python3
"""Regression: the Road specimen must teach reusable grammar."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from physical_composer import compose  # noqa: E402

brief = json.loads(
    (Path(__file__).with_name("road-drew-itself.json")).read_text(encoding="utf-8")
)
candidate_ids = {candidate["candidate_id"] for candidate in compose(brief)}

required = {"route-book", "trace-edition", "companion-geometry", "codex"}
missing = required - candidate_ids
if missing:
    raise SystemExit(f"ROAD GRAMMAR REGRESSION FAIL: missing {sorted(missing)}")
if "field-book" in candidate_ids:
    raise SystemExit("ROAD GRAMMAR REGRESSION FAIL: source receipt collapsed into writable field-book")

print("ROAD GRAMMAR REGRESSION: PASS")
print("candidates:", ", ".join(sorted(candidate_ids)))
