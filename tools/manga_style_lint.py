#!/usr/bin/env python3
"""Lint a stack using the same refusal rules as the resolver."""
import argparse
import json
from pathlib import Path
import sys
from manga_style_resolve import ROOT, read, resolve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stack")
    parser.add_argument("--profiles", default=str(ROOT / "works/styles"))
    args = parser.parse_args()
    stack = read(args.stack)
    profiles = [read(p) for p in sorted(Path(args.profiles).glob("*.json"))]
    result = resolve(stack, profiles)
    catalog = {p["id"]: p for p in profiles}
    dead = []
    for index, entry in enumerate(stack["styles"]):
        for domain, fields in catalog[entry["styleId"]]["behavior"].items():
            for field in fields:
                if domain not in entry["domainMask"] or (entry.get("channelMask") and field not in entry["channelMask"]):
                    dead.append({"entry": index, "field": domain + "." + field, "reason": "excluded by declared scope"})
    print(json.dumps({"status": "PASS", "resolutionHash": result["resolutionHash"], "deadFields": dead}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
