#!/usr/bin/env python3
"""Probe one severed LemonPRESS computer-book fragment without inventing missing context."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from computer_book import ComputerBookError, inspect_fragment


def local_availability(fragment_path: Path, locator: str):
    path = (fragment_path.parent / locator).resolve()
    return {
        "locator": locator,
        "availability": "PRESENT_LOCAL" if path.exists() else "UNAVAILABLE_LOCAL",
        "existence": "KNOWN" if path.exists() else "UNKNOWN",
    }


def probe_severed(fragment_path: Path):
    fragment_path = Path(fragment_path)
    fragment = inspect_fragment(fragment_path)

    manifest = local_availability(fragment_path, fragment["retrieval"]["manifest"])
    continuations = []
    for edge in fragment["retrieval"]["continuations"]:
        relation, target, scope = edge.get("relation"), edge.get("target"), edge.get("scope")
        if not relation or not target or scope not in ("local", "external"):
            raise ComputerBookError(f"{fragment_path}: malformed continuation")

        if scope == "local":
            candidate = fragment_path.parent / f"{target}.json"
            availability = "PRESENT_LOCAL" if candidate.exists() else "UNAVAILABLE_LOCAL"
            existence = "KNOWN" if candidate.exists() else "UNKNOWN"
        else:
            availability = "NOT_QUERIED"
            existence = "UNKNOWN"

        continuations.append({
            "relation": relation,
            "target": target,
            "scope": scope,
            "availability": availability,
            "existence": existence,
        })

    return {
        "observation": "SEVERED_FRAGMENT",
        "work_id": fragment["work_id"],
        "edition_id": fragment["edition_id"],
        "fragment_id": fragment["fragment_id"],
        "body_identity": "DECLARED_BY_FRAGMENT",
        "fragment_status": "PRESENT",
        "manifest": manifest,
        "continuations": continuations,
        "ancestry": fragment["ancestry"],
        "uncertainty": fragment["uncertainty"],
        "whole_body_state": "UNKNOWN",
        "authority": "none",
        "laws": {
            "unavailable_is_nonexistent": False,
            "unknown_is_empty": False,
            "fragment_is_book": False,
            "severance_changes_ancestry": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fragment", type=Path)
    args = parser.parse_args()

    try:
        result = probe_severed(args.fragment)
    except ComputerBookError as exc:
        parser.exit(2, f"computer-book severance probe failed: {exc}\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
