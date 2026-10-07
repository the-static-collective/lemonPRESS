#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, math, sys
from pathlib import Path
from typing import Any
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SPEC_SCHEMA_NAME = "manga-translation-relay-v0.schema.json"
CANDIDATE_SCHEMA_NAME = "manga-translation-candidate-v0.schema.json"
SPEC_SCHEMA = "lemonpress/manga-translation-relay/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-translation-candidate/v0"
LAWS = [
    "TRANSLATION != REPLACEMENT",
    "RETURN != ORIGINAL",
    "DRIFT != ERROR",
    "LOSS MUST REMAIN VISIBLE",
    "SOURCE SURVIVES RELAY",
    "CLIPPED TEXT != LICENSE TO RECONSTRUCT",
    "LANGUAGE ROUTE IS DECLARED",
    "RENDERING != ADMISSION",
]

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def read_json(path: Path) -> dict[str, Any]:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, f"duplicate JSON key: {key}")
            out[key] = value
        return out
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), "relay spec must be one JSON object")
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
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

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

def validate_spec(spec: dict[str, Any]) -> None:
    validate_schema(spec, SPEC_SCHEMA_NAME)
    require(spec["schema"] == SPEC_SCHEMA, f"expected {SPEC_SCHEMA}")
    require(spec["laws"] == LAWS, "v0 law set must match TRANSLATION RELAY 001 exactly")
    ids = [segment["segment_id"] for segment in spec["segments"]]
    require(len(ids) == len(set(ids)), "duplicate segment_id")
    pages = spec["source"]["pages"]
    for segment in spec["segments"]:
        require(1 <= segment["page"] <= pages, f"segment page outside source range: {segment['segment_id']}")
        for key in ("source", "pivot", "return"):
            require(segment[key] != "", f"empty {key}: {segment['segment_id']}")

def hash_projection(spec: dict[str, Any], key: str) -> str:
    projection = [
        {"segment_id": s["segment_id"], "page": s["page"], "locus": s["locus"], key: s[key]}
        for s in spec["segments"]
    ]
    return hashlib.sha256(canonical_bytes(projection)).hexdigest()

def candidate_identity(spec: dict[str, Any]) -> str:
    return "manga-translation-relay:" + hashlib.sha256(canonical_bytes(spec)).hexdigest()

def build_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": candidate_identity(spec),
        "status": "CANDIDATE",
        "title": spec["title"],
        "relay_id": spec["id"],
        "source": copy.deepcopy(spec["source"]),
        "route": copy.deepcopy(spec["route"]),
        "source_text_sha256": hash_projection(spec, "source"),
        "pivot_text_sha256": hash_projection(spec, "pivot"),
        "return_text_sha256": hash_projection(spec, "return"),
        "segments": copy.deepcopy(spec["segments"]),
        "authority": copy.deepcopy(spec["authority"]),
        "laws": copy.deepcopy(spec["laws"]),
    }
    clipped = [s["segment_id"] for s in spec["segments"] if s["visibility"] == "clipped"]
    losses = []
    if clipped:
        losses.append("source contains clipped visible fragments: " + ", ".join(clipped))
    for s in spec["segments"]:
        if any(d["kind"] == "loss" for d in s["drift"]):
            losses.append("declared semantic loss: " + s["segment_id"])
    candidate["wrench"] = {
        "INPUT": {"source": copy.deepcopy(spec["source"]), "segment_count": len(spec["segments"]), "route": copy.deepcopy(spec["route"])},
        "TRANSFORMATION": "declared English -> Japanese -> English translation relay with frozen intermediate and return text",
        "OUTPUT": {"candidate_id": candidate["candidate_id"], "return_text_sha256": candidate["return_text_sha256"]},
        "RESIDUAL": "source text and source artifact remain unchanged and independently addressable",
        "LOSS": losses + ["semantic identity is not assumed across the relay"],
        "UNKNOWN": ["visual re-lettering quality", "editorial selection", "issue admission", "publication status"],
        "STOP": "candidate only; returned text may be selected for re-lettering but does not replace or admit the source by itself",
    }
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    return candidate

def _esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")

def return_script(candidate: dict[str, Any]) -> str:
    lines = [
        f"# {candidate['title']} — returned English",
        "",
        f"Candidate: {candidate['candidate_id']}",
        "",
        "This is a descendant text layer. The source remains unchanged.",
        "",
    ]
    current_page = None
    for segment in candidate["segments"]:
        if segment["page"] != current_page:
            current_page = segment["page"]
            lines += [f"## Page {current_page}", ""]
        lines.append(f"- **{segment['locus']}** — {segment['return']}")
    lines.append("")
    return "\n".join(lines)

def receipt(candidate: dict[str, Any]) -> str:
    lines = [
        f"# {candidate['relay_id']} — TRANSLATION RELAY 001 receipt",
        "",
        f"Status: {candidate['status']}",
        f"Candidate: {candidate['candidate_id']}",
        f"Source text SHA-256: {candidate['source_text_sha256']}",
        f"Japanese text SHA-256: {candidate['pivot_text_sha256']}",
        f"Return text SHA-256: {candidate['return_text_sha256']}",
        "",
        "| page | locus | source | Japanese | return | drift |",
        "|---:|---|---|---|---|---|",
    ]
    for segment in candidate["segments"]:
        drift = ", ".join(d["kind"] for d in segment["drift"]) or "none"
        lines.append(
            f"| {segment['page']} | {_esc(segment['locus'])} | {_esc(segment['source'])} | "
            f"{_esc(segment['pivot'])} | {_esc(segment['return'])} | {drift} |"
        )
    wrench = candidate["wrench"]
    lines += [
        "",
        "## WRENCH",
        "",
        f"- TRANSFORMATION: {wrench['TRANSFORMATION']}",
        f"- RESIDUAL: {wrench['RESIDUAL']}",
        f"- LOSS: {'; '.join(wrench['LOSS'])}",
        f"- UNKNOWN: {'; '.join(wrench['UNKNOWN'])}",
        f"- STOP: {wrench['STOP']}",
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

def write_outputs(relay_path: Path, candidate: dict[str, Any], out_dir: Path | None = None) -> None:
    destination = out_dir or relay_path.parent
    _write_create_only(destination / "candidate.json", canonical_bytes(candidate) + b"\n")
    _write_create_only(destination / "RETURN.md", return_script(candidate).encode("utf-8"))
    _write_create_only(destination / "RECEIPT.md", receipt(candidate).encode("utf-8"))

def verify_outputs(relay_path: Path, out_dir: Path | None = None) -> dict[str, Any]:
    spec = read_json(relay_path)
    expected = build_candidate(spec)
    destination = out_dir or relay_path.parent
    actual = read_json(destination / "candidate.json")
    validate_schema(actual, CANDIDATE_SCHEMA_NAME)
    require(canonical_bytes(actual) == canonical_bytes(expected), "candidate.json does not deterministically rebuild")
    require((destination / "RETURN.md").read_text(encoding="utf-8") == return_script(expected), "RETURN.md does not deterministically rebuild")
    require((destination / "RECEIPT.md").read_text(encoding="utf-8") == receipt(expected), "RECEIPT.md does not deterministically rebuild")
    return expected

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TRANSLATION RELAY 001")
    parser.add_argument("relay")
    parser.add_argument("--out-dir")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    relay_path = Path(args.relay)
    out_dir = Path(args.out_dir) if args.out_dir else None
    if args.verify:
        candidate = verify_outputs(relay_path, out_dir)
        print(json.dumps({"ok": True, "candidate_id": candidate["candidate_id"], "verified": True}, indent=2))
        return 0
    candidate = build_candidate(read_json(relay_path))
    write_outputs(relay_path, candidate, out_dir)
    print(json.dumps({"ok": True, "candidate_id": candidate["candidate_id"], "return_text_sha256": candidate["return_text_sha256"], "status": candidate["status"]}, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga translation relay failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
