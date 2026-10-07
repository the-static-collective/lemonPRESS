#!/usr/bin/env python3
"""REMIX SEQUENCE 001: deterministic reading-order candidates without source mutation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_SCHEMA_NAME = "manga-remix-sequence-v0.schema.json"
CANDIDATE_SCHEMA_NAME = "manga-sequence-candidate-v0.schema.json"
SEQUENCE_SCHEMA = "lemonpress/manga-remix-sequence/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-sequence-candidate/v0"

LAWS = [
    "REORDER != SOURCE MUTATION",
    "ORDER != ANCESTRY",
    "READING ORDER != OWNERSHIP",
    "SEQUENCE != ADMISSION",
    "OMISSION != DELETION",
    "DUPLICATION != NEW SOURCE",
    "SLOT != PAGE IDENTITY",
    "CANDIDATE != ISSUE",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), "sequence spec must be one JSON object")
    return value


def canonical_bytes(value: Any) -> bytes:
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            require(all(isinstance(k, str) for k in item), "JSON keys must be strings")
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, float):
            require(math.isfinite(item), "canonical JSON forbids NaN and infinity")
        else:
            require(item is None or type(item) in (str, int, bool), "unsupported canonical JSON value")

    walk(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def validate_schema(value: dict[str, Any], name: str) -> None:
    document = schema(name)
    jsonschema.Draft202012Validator.check_schema(document)
    try:
        jsonschema.Draft202012Validator(document).validate(value)
    except jsonschema.ValidationError as exc:
        location = ".".join(str(x) for x in exc.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {location}: {exc.message}") from exc


def _validate_region(selection: dict[str, Any]) -> None:
    x = selection["x"]
    y = selection["y"]
    width = selection["width"]
    height = selection["height"]
    require(x + width <= 1, "region x + width must be <= 1")
    require(y + height <= 1, "region y + height must be <= 1")


def validate_sequence(spec: dict[str, Any]) -> None:
    validate_schema(spec, SEQUENCE_SCHEMA_NAME)
    require(spec["schema"] == SEQUENCE_SCHEMA, f"expected {SEQUENCE_SCHEMA}")
    require(spec["laws"] == LAWS, "v0 law set must match REMIX SEQUENCE 001 exactly")

    parent_ids = [parent["parent_id"] for parent in spec["parents"]]
    require(len(parent_ids) == len(set(parent_ids)), "duplicate parent_id")
    declared = set(parent_ids)

    slots = set()
    for occurrence in spec["sequence"]:
        slot = occurrence["slot"]
        require(slot not in slots, f"duplicate slot: {slot}")
        slots.add(slot)
        require(occurrence["source_ref"] in declared, f"unknown source_ref: {occurrence['source_ref']}")
        selection = occurrence["selection"]
        if selection["kind"] == "region":
            _validate_region(selection)
        elif selection["kind"] == "panel":
            require(bool(selection["panel_id"].strip()), "panel selection requires panel_id")


def sequence_hash(spec: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(spec["sequence"])).hexdigest()


def candidate_identity(spec: dict[str, Any]) -> str:
    return "manga-sequence:" + hashlib.sha256(canonical_bytes(spec)).hexdigest()


def build_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    validate_sequence(spec)
    sequence_sha256 = sequence_hash(spec)
    candidate_id = candidate_identity(spec)

    used = {slot["source_ref"] for slot in spec["sequence"]}
    omitted = [parent["parent_id"] for parent in spec["parents"] if parent["parent_id"] not in used]
    losses = [f"omitted from descendant order: {parent_id}" for parent_id in omitted]
    losses.append("descendant order preserves no source adjacency unless explicitly declared by neighboring slots")

    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": candidate_id,
        "status": "CANDIDATE",
        "title": spec["title"],
        "sequence_sha256": sequence_sha256,
        "sequence_id": spec["id"],
        "slots": copy.deepcopy(spec["sequence"]),
        "parents": copy.deepcopy(spec["parents"]),
        "authority": copy.deepcopy(spec["authority"]),
        "laws": copy.deepcopy(spec["laws"]),
        "wrench": {
            "INPUT": copy.deepcopy(spec["parents"]),
            "TRANSFORMATION": "declared reading-order remix with slot-preserving sequence",
            "OUTPUT": {
                "schema": CANDIDATE_SCHEMA,
                "candidate_id": candidate_id,
                "sequence_sha256": sequence_sha256,
            },
            "RESIDUAL": "all parent particulars remain unchanged and independently addressable",
            "LOSS": losses,
            "UNKNOWN": [
                "publication status",
                "canon status",
                "issue admission status",
            ],
            "STOP": "candidate only; explicit local selection/admission required before becoming issue/page authority",
        },
    }
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    return candidate


def receipt(candidate: dict[str, Any]) -> str:
    lines = [
        f"# {candidate['sequence_id']} — REMIX SEQUENCE 001 receipt",
        "",
        f"Status: {candidate['status']}",
        f"Candidate: {candidate['candidate_id']}",
        f"Sequence SHA-256: {candidate['sequence_sha256']}",
        "",
        "## Declared order",
        "",
    ]
    for slot in candidate["slots"]:
        selection = json.dumps(slot["selection"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        lines.append(f"{slot['slot']}. {slot['source_ref']} — {selection}")

    lines += ["", "## Provenance", ""]
    for parent in candidate["parents"]:
        lines.append(f"- {parent['parent_id']} — {parent['kind']} — {parent['title']}")

    lines += [
        "",
        "## WRENCH",
        "",
        f"- TRANSFORMATION: {candidate['wrench']['TRANSFORMATION']}",
        f"- RESIDUAL: {candidate['wrench']['RESIDUAL']}",
        f"- LOSS: {'; '.join(candidate['wrench']['LOSS'])}",
        f"- UNKNOWN: {'; '.join(candidate['wrench']['UNKNOWN'])}",
        f"- STOP: {candidate['wrench']['STOP']}",
        "",
        "## Authority",
        "",
        "No editorial selection, edition admission, publication, or house release authority is granted by this candidate.",
        "",
        "## Laws",
        "",
        *candidate["laws"],
        "",
    ]
    return "\n".join(lines)


def _write_create_only(path: Path, data: bytes) -> None:
    if path.exists():
        require(path.read_bytes() == data, f"create-only conflict: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_outputs(sequence_path: Path, candidate: dict[str, Any], out_dir: Path | None = None) -> None:
    destination = out_dir or sequence_path.parent
    _write_create_only(destination / "candidate.json", canonical_bytes(candidate) + b"\n")
    _write_create_only(destination / "RECEIPT.md", receipt(candidate).encode("utf-8"))


def verify_outputs(sequence_path: Path, out_dir: Path | None = None) -> dict[str, Any]:
    spec = read_json(sequence_path)
    expected = build_candidate(spec)
    destination = out_dir or sequence_path.parent
    actual = read_json(destination / "candidate.json")
    validate_schema(actual, CANDIDATE_SCHEMA_NAME)
    require(canonical_bytes(actual) == canonical_bytes(expected), "candidate.json does not deterministically rebuild")
    require(
        (destination / "RECEIPT.md").read_text(encoding="utf-8") == receipt(expected),
        "RECEIPT.md does not deterministically rebuild",
    )
    return expected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="REMIX SEQUENCE 001")
    parser.add_argument("sequence", help="path to sequence.json")
    parser.add_argument("--out-dir")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)

    sequence_path = Path(args.sequence)
    out_dir = Path(args.out_dir) if args.out_dir else None

    if args.verify:
        candidate = verify_outputs(sequence_path, out_dir)
        print(json.dumps({"ok": True, "candidate_id": candidate["candidate_id"], "verified": True}, indent=2))
        return 0

    spec = read_json(sequence_path)
    candidate = build_candidate(spec)
    write_outputs(sequence_path, candidate, out_dir)
    print(json.dumps({
        "ok": True,
        "candidate_id": candidate["candidate_id"],
        "sequence_sha256": candidate["sequence_sha256"],
        "status": candidate["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga sequence failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
