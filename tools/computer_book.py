#!/usr/bin/env python3
"""Verify and reconstruct LemonPRESS computer-book specimens using stdlib only."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path


FALSE_LAWS = (
    "retrieved_is_read",
    "chunk_is_book",
    "fragment_is_context",
    "retrieval_order_is_authority",
    "reading_order_is_ancestry",
)


class ComputerBookError(ValueError):
    pass


def load_json(path: Path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ComputerBookError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ComputerBookError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ComputerBookError(f"expected JSON object: {path}")
    return value


def inspect_fragment(path: Path):
    fragment = load_json(path)
    required = (
        "schema_version", "work_id", "edition_id", "fragment_id", "title",
        "carrier", "retrieval", "ancestry", "authority", "uncertainty",
    )
    missing = [key for key in required if key not in fragment]
    if missing:
        raise ComputerBookError(f"{path}: missing fields: {', '.join(missing)}")
    if fragment["schema_version"] != "computer-book-fragment-v0":
        raise ComputerBookError(f"{path}: unsupported fragment schema")
    retrieval = fragment["retrieval"]
    if not isinstance(retrieval, dict) or retrieval.get("warning") != "FRAGMENT != BOOK":
        raise ComputerBookError(f"{path}: fragment must declare FRAGMENT != BOOK")
    if not retrieval.get("manifest") or not isinstance(retrieval.get("continuations"), list):
        raise ComputerBookError(f"{path}: fragment must expose manifest and continuations")
    if not isinstance(fragment["ancestry"], list) or not fragment["ancestry"]:
        raise ComputerBookError(f"{path}: fragment must carry ancestry")
    if not isinstance(fragment["authority"], dict) or fragment["authority"].get("level") != "none":
        raise ComputerBookError(f"{path}: retrieval fragment cannot grant authority")
    if not isinstance(fragment["uncertainty"], list):
        raise ComputerBookError(f"{path}: uncertainty must be an array")
    return fragment


def load_relations(path: Path):
    if not path.exists():
        return []
    out = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            edge = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ComputerBookError(f"invalid JSONL: {path}:{number}: {exc}") from exc
        if not isinstance(edge, dict):
            raise ComputerBookError(f"expected relation object: {path}:{number}")
        out.append(edge)
    return out


def verify(root: Path):
    root = Path(root)
    manifest = load_json(root / "manifest.json")
    required = ("schema_version", "work_id", "edition_id", "lane", "title", "retrieval_contract", "fragments")
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ComputerBookError(f"manifest missing fields: {', '.join(missing)}")
    if manifest["schema_version"] != "computer-book-manifest-v0":
        raise ComputerBookError("unsupported manifest schema")
    if manifest["lane"] != "crawler":
        raise ComputerBookError("computer-book specimen must declare crawler lane")

    contract = manifest["retrieval_contract"]
    if not isinstance(contract, dict):
        raise ComputerBookError("retrieval_contract must be an object")
    for law in FALSE_LAWS:
        if contract.get(law) is not False:
            raise ComputerBookError(f"retrieval contract must declare {law}=false")

    declared = manifest["fragments"]
    if not isinstance(declared, list) or not declared:
        raise ComputerBookError("manifest must declare at least one fragment")

    by_id = {}
    paths = {}
    for entry in declared:
        if not isinstance(entry, dict):
            raise ComputerBookError("fragment entries must be objects")
        fragment_id = entry.get("fragment_id")
        relpath = entry.get("path")
        if not fragment_id or not relpath:
            raise ComputerBookError("fragment entry requires fragment_id and path")
        if fragment_id in by_id:
            raise ComputerBookError(f"duplicate fragment id: {fragment_id}")
        path = root / relpath
        fragment = inspect_fragment(path)
        if fragment["fragment_id"] != fragment_id:
            raise ComputerBookError(f"{path}: fragment_id does not match manifest")
        if fragment["work_id"] != manifest["work_id"]:
            raise ComputerBookError(f"{path}: work_id does not match manifest")
        if fragment["edition_id"] != manifest["edition_id"]:
            raise ComputerBookError(f"{path}: edition_id does not match manifest")
        by_id[fragment_id] = fragment
        paths[fragment_id] = path

    local_edges = set()
    for fragment_id, fragment in by_id.items():
        for edge in fragment["retrieval"]["continuations"]:
            if not isinstance(edge, dict):
                raise ComputerBookError(f"{paths[fragment_id]}: continuation must be an object")
            relation, target, scope = edge.get("relation"), edge.get("target"), edge.get("scope")
            if not relation or not target or scope not in ("local", "external"):
                raise ComputerBookError(f"{paths[fragment_id]}: malformed continuation")
            if scope == "local":
                if target not in by_id:
                    raise ComputerBookError(f"{paths[fragment_id]}: unresolved local target: {target}")
                local_edges.add((fragment_id, relation, target))

    relation_edges = set()
    for edge in load_relations(root / "relations.jsonl"):
        source, relation, target = edge.get("from"), edge.get("relation"), edge.get("to")
        scope = edge.get("scope", "local")
        if not source or not relation or not target:
            raise ComputerBookError("relations.jsonl edge requires from, relation, to")
        if scope == "local":
            if source not in by_id or target not in by_id:
                raise ComputerBookError(f"relations.jsonl unresolved local edge: {source} -> {target}")
            relation_edges.add((source, relation, target))

    if relation_edges != local_edges:
        raise ComputerBookError(
            f"relation disagreement: missing={sorted(local_edges - relation_edges)!r} "
            f"extra={sorted(relation_edges - local_edges)!r}"
        )

    return {
        "work_id": manifest["work_id"],
        "edition_id": manifest["edition_id"],
        "fragment_ids": sorted(by_id),
        "fragment_count": len(by_id),
        "authority": "none",
        "local_edges": sorted(local_edges),
    }


def reconstruct(root: Path, start_fragment_id: str):
    root = Path(root)
    verified = verify(root)
    manifest = load_json(root / "manifest.json")
    by_id = {
        entry["fragment_id"]: inspect_fragment(root / entry["path"])
        for entry in manifest["fragments"]
    }
    if start_fragment_id not in by_id:
        raise ComputerBookError(f"unknown start fragment: {start_fragment_id}")

    queue = deque([start_fragment_id])
    visited, seen = [], set()
    ancestry, ancestry_seen = [], set()
    uncertainty, uncertainty_seen = [], set()

    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        visited.append(current)
        fragment = by_id[current]

        for item in fragment["ancestry"]:
            key = json.dumps(item, sort_keys=True, separators=(",", ":"))
            if key not in ancestry_seen:
                ancestry_seen.add(key)
                ancestry.append(item)

        for item in fragment["uncertainty"]:
            if item not in uncertainty_seen:
                uncertainty_seen.add(item)
                uncertainty.append(item)

        for edge in fragment["retrieval"]["continuations"]:
            if edge["scope"] == "local" and edge["target"] not in seen:
                queue.append(edge["target"])

    return {
        "work_id": verified["work_id"],
        "edition_id": verified["edition_id"],
        "start_fragment_id": start_fragment_id,
        "reachable_fragments": visited,
        "reachable_set": sorted(seen),
        "authority": "none",
        "ancestry": ancestry,
        "uncertainty": uncertainty,
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("verify")
    check.add_argument("root", type=Path)
    rebuild = sub.add_parser("reconstruct")
    rebuild.add_argument("root", type=Path)
    rebuild.add_argument("fragment_id")
    args = parser.parse_args()

    try:
        result = verify(args.root) if args.command == "verify" else reconstruct(args.root, args.fragment_id)
    except ComputerBookError as exc:
        parser.exit(2, f"computer-book verification failed: {exc}\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
