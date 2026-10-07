#!/usr/bin/env python3
"""BOX BINDING 001: bind translation particulars to exact page-pixel rectangles without rendering."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press
import manga_translation_relay as relay
import manga_page_intake as intake

SPEC_SCHEMA_NAME = "manga-box-binding-v0.schema.json"
CANDIDATE_SCHEMA_NAME = "manga-box-binding-candidate-v0.schema.json"
SPEC_SCHEMA = "lemonpress/manga-box-binding/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-box-binding-candidate/v0"

LAWS = [
    "TEXT ID != PIXEL REGION",
    "BOX != SEMANTIC TRUTH",
    "BINDING != SELECTION",
    "BINDING != MASK",
    "GEOMETRY != RENDER AUTHORITY",
    "ONE PARTICULAR == ONE DECLARED REGION",
    "CLIPPED SOURCE REMAINS CLIPPED",
    "ART SURFACE REQUIRES EXPLICIT RENDER STRATEGY",
    "ALL PARTICULARS MUST BE ACCOUNTED FOR",
    "BOX BINDING != ADMISSION",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def validate_schema(value: dict[str, Any], name: str) -> None:
    document = _schema(name)
    jsonschema.Draft202012Validator.check_schema(document)
    try:
        jsonschema.Draft202012Validator(document).validate(value)
    except jsonschema.ValidationError as exc:
        location = ".".join(str(x) for x in exc.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {location}: {exc.message}") from exc


def _root_path(root: Path, relative: str, label: str) -> Path:
    require(isinstance(relative, str) and relative.strip(), f"{label} must be nonempty")
    rel = Path(relative)
    require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in relative and rel.as_posix() == relative,
            f"{label} must be canonical repository-relative POSIX path")
    path = (root / rel).resolve()
    require(path.is_relative_to(root.resolve()), f"{label} escapes root")
    require(path.is_file(), f"missing {label}: {relative}")
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rect(value: dict[str, Any], width: int, height: int, label: str) -> dict[str, int]:
    require(isinstance(value, dict) and set(value) == {"x", "y", "width", "height"}, f"{label} rectPx shape")
    require(all(type(value[k]) is int for k in value), f"{label} rectPx must use integers")
    require(value["x"] >= 0 and value["y"] >= 0 and value["width"] > 0 and value["height"] > 0,
            f"{label} rectPx out of range")
    require(value["x"] + value["width"] <= width and value["y"] + value["height"] <= height,
            f"{label} rectPx outside page")
    return value


def _intersects(a: dict[str, int], b: dict[str, int]) -> bool:
    return max(a["x"], b["x"]) < min(a["x"] + a["width"], b["x"] + b["width"]) and \
           max(a["y"], b["y"]) < min(a["y"] + a["height"], b["y"] + b["height"])


def _load_sources(root: Path, spec: dict[str, Any]):
    relay_path = _root_path(root, spec["relaySpec"], "relaySpec")
    intake_path = _root_path(root, spec["pageIntakeSpec"], "pageIntakeSpec")
    relay_bytes = relay_path.read_bytes()
    intake_bytes = intake_path.read_bytes()

    relay_spec = relay.read_json(relay_path)
    relay_candidate = relay.build_candidate(relay_spec)

    intake_spec = press.read_json(intake_path)
    intake.validate_schema(intake_spec, intake.SPEC_SCHEMA_NAME)
    require(intake_spec["schema"] == intake.SPEC_SCHEMA, f"expected {intake.SPEC_SCHEMA}")
    require(intake_spec["laws"] == intake.LAWS, "PAGE INTAKE law set mismatch")
    expected = intake_spec.get("expected_pages")
    require(isinstance(expected, list) and len(expected) == intake_spec["source"]["page_count"],
            "page intake spec must freeze expected_pages before box binding")

    pages = {}
    prefix = intake_spec["manga"]["page_prefix"]
    for page in expected:
        number = page["page"]
        require(number not in pages, f"duplicate intake page: {number}")
        pages[number] = {
            "page": number,
            "pageId": f"{prefix}-{number:02d}",
            "width": page["width"],
            "height": page["height"],
            "pixelSha256": page["pixel_sha256"],
            "pngSha256": page["png_sha256"],
        }
    return relay_candidate, pages, _sha256(relay_bytes), _sha256(intake_bytes)


def validate_spec(root: Path, spec: dict[str, Any]):
    validate_schema(spec, SPEC_SCHEMA_NAME)
    require(spec["schema"] == SPEC_SCHEMA, f"expected {SPEC_SCHEMA}")
    require(spec["laws"] == LAWS, "v0 law set must match BOX BINDING 001 exactly")

    relay_candidate, pages, relay_spec_sha, intake_spec_sha = _load_sources(root, spec)
    segments = {s["segment_id"]: s for s in relay_candidate["segments"]}
    require(len(segments) == len(relay_candidate["segments"]), "relay candidate has duplicate segment ids")

    seen = set()
    by_page = defaultdict(list)
    enriched = []
    for binding in spec["bindings"]:
        segment_id = binding["segmentId"]
        require(segment_id in segments, f"unknown segmentId: {segment_id}")
        require(segment_id not in seen, f"duplicate segment binding: {segment_id}")
        seen.add(segment_id)
        segment = segments[segment_id]
        require(binding["page"] == segment["page"],
                f"binding page mismatch for {segment_id}: relay page {segment['page']}, binding page {binding['page']}")
        require(binding["page"] in pages, f"unknown intake page: {binding['page']}")
        page = pages[binding["page"]]
        rect = copy.deepcopy(_rect(binding["rectPx"], page["width"], page["height"], segment_id))
        for prior_id, prior_rect in by_page[binding["page"]]:
            require(not _intersects(rect, prior_rect),
                    f"binding rectangles overlap on page {binding['page']}: {prior_id} / {segment_id}")
        by_page[binding["page"]].append((segment_id, rect))
        enriched.append({
            "segmentId": segment_id,
            "page": binding["page"],
            "pageId": page["pageId"],
            "pagePixelSha256": page["pixelSha256"],
            "pagePngSha256": page["pngSha256"],
            "rectPx": rect,
            "surfaceClass": binding["surfaceClass"],
            "visibility": segment["visibility"],
            "locus": segment["locus"],
            "role": segment["role"],
            "returnedText": segment["return"],
        })

    missing = sorted(set(segments) - seen)
    extra = sorted(seen - set(segments))
    require(not missing, "unbound relay particulars: " + ", ".join(missing))
    require(not extra, "bindings reference non-relay particulars: " + ", ".join(extra))
    require(len(enriched) == len(segments), "binding coverage count mismatch")
    return relay_candidate, pages, relay_spec_sha, intake_spec_sha, enriched


def build(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    relay_candidate, pages, relay_spec_sha, intake_spec_sha, enriched = validate_spec(root, spec)
    surface_counts = Counter(item["surfaceClass"] for item in enriched)
    blockers = [
        {
            "segmentId": item["segmentId"],
            "page": item["page"],
            "surfaceClass": item["surfaceClass"],
            "reason": "requires an explicit non-solid render strategy before RELETTER may alter pixels",
        }
        for item in enriched if item["surfaceClass"] in ("art", "sign")
    ]
    spec_sha = _sha256(press.canonical_bytes(spec))
    seed = {
        "schema": CANDIDATE_SCHEMA,
        "status": "BOUND_CANDIDATE",
        "title": spec["title"],
        "bindingId": spec["id"],
        "basis": spec["basis"],
        "specSha256": spec_sha,
        "relaySpecSha256": relay_spec_sha,
        "relayCandidateId": relay_candidate["candidate_id"],
        "relayReturnTextSha256": relay_candidate["return_text_sha256"],
        "pageIntakeSpecSha256": intake_spec_sha,
        "pageCount": len(pages),
        "particularCount": len(enriched),
        "bindings": enriched,
        "surfaceCounts": dict(sorted(surface_counts.items())),
        "solidPatchReadyCount": sum(surface_counts[k] for k in ("solid-dark", "solid-light")),
        "renderStrategyBlockers": blockers,
        "authority": copy.deepcopy(spec["authority"]),
        "wrench": {
            "INPUT": {
                "relayCandidateId": relay_candidate["candidate_id"],
                "pageCount": len(pages),
                "particularCount": len(enriched),
            },
            "TRANSFORMATION": "declared one-to-one binding of every translation-relay particular to one non-overlapping page-pixel rectangle",
            "OUTPUT": {
                "boundParticulars": len(enriched),
                "solidPatchReady": sum(surface_counts[k] for k in ("solid-dark", "solid-light")),
                "explicitRenderStrategyRequired": len(blockers),
            },
            "RESIDUAL": [
                "Page pixels remain unchanged.",
                "Translation source, Japanese pivot, returned English, and clipped-state remain unchanged.",
                "Boxes state where a text particular visibly resides; they do not claim semantic understanding of surrounding pixels.",
            ],
            "LOSS": [
                "A rectangle is a coarse visible-region declaration, not the exact glyph silhouette.",
                "Perspective, rotation, texture, and source typeface are not encoded by v0 box geometry.",
            ],
            "UNKNOWN": [
                "Final mask/inpainting strategy for art and sign surfaces.",
                "Typography, font assets, perspective lettering, editorial selection, edition admission, publication, and house release.",
            ],
            "STOP": "Geometry candidate only. No source pixels are changed and no returned wording is selected for publication.",
        },
        "laws": copy.deepcopy(spec["laws"]),
    }
    candidate_id = "manga-box-binding:" + _sha256(press.canonical_bytes({
        "specSha256": spec_sha,
        "relayCandidateId": relay_candidate["candidate_id"],
        "pageIntakeSpecSha256": intake_spec_sha,
        "bindings": enriched,
    }))
    candidate = {**seed, "candidateId": candidate_id}
    candidate["candidateHash"] = _sha256(press.canonical_bytes(candidate))
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    return candidate


def verify_candidate(candidate: dict[str, Any]) -> None:
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    expected = candidate["candidateHash"]
    body = copy.deepcopy(candidate)
    body.pop("candidateHash", None)
    require(expected == _sha256(press.canonical_bytes(body)), "candidate hash mismatch")
    require(candidate["laws"] == LAWS, "candidate law set mismatch")


def receipt(candidate: dict[str, Any]) -> str:
    lines = [
        f"# {candidate['bindingId']} - BOX BINDING 001 receipt",
        "",
        f"Status: {candidate['status']}",
        f"Candidate: {candidate['candidateId']}",
        f"Relay candidate: {candidate['relayCandidateId']}",
        f"Pages: {candidate['pageCount']}",
        f"Particulars bound: {candidate['particularCount']}",
        f"Solid-patch ready: {candidate['solidPatchReadyCount']}",
        f"Explicit render-strategy blockers: {len(candidate['renderStrategyBlockers'])}",
        "",
        "## Surface inventory",
        "",
    ]
    for name, count in candidate["surfaceCounts"].items():
        lines.append(f"- {name}: {count}")
    lines += [
        "",
        "## Bindings",
        "",
        "| segment | page | locus | surface | rect x,y,w,h | returned text |",
        "|---|---:|---|---|---|---|",
    ]
    for item in candidate["bindings"]:
        rect = item["rectPx"]
        text = item["returnedText"].replace("|", "\\|").replace("\n", "<br>")
        lines.append(
            f"| {item['segmentId']} | {item['page']} | {item['locus']} | {item['surfaceClass']} | "
            f"{rect['x']},{rect['y']},{rect['width']},{rect['height']} | {text} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        candidate["wrench"]["STOP"],
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


def write_outputs(spec_path: Path, candidate: dict[str, Any], out_dir: Path | None = None) -> None:
    destination = out_dir or spec_path.parent
    _write_create_only(destination / "candidate.json", press.canonical_bytes(candidate) + b"\n")
    _write_create_only(destination / "BOX-RECEIPT.md", receipt(candidate).encode("utf-8"))


def verify_outputs(root: Path, spec_path: Path, out_dir: Path | None = None) -> dict[str, Any]:
    spec = press.read_json(spec_path)
    expected = build(root, spec)
    destination = out_dir or spec_path.parent
    actual = press.read_json(destination / "candidate.json")
    verify_candidate(actual)
    require(press.canonical_bytes(actual) == press.canonical_bytes(expected),
            "candidate.json does not deterministically rebuild")
    require((destination / "BOX-RECEIPT.md").read_text(encoding="utf-8") == receipt(expected),
            "BOX-RECEIPT.md does not deterministically rebuild")
    return expected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="BOX BINDING 001")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("spec")
    parser.add_argument("--out-dir")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    spec_path = _root_path(root, args.spec, "binding spec")
    out_dir = Path(args.out_dir) if args.out_dir else None
    if args.verify:
        candidate = verify_outputs(root, spec_path, out_dir)
        print(json.dumps({"ok": True, "candidateId": candidate["candidateId"], "verified": True}, indent=2))
        return 0

    candidate = build(root, press.read_json(spec_path))
    write_outputs(spec_path, candidate, out_dir)
    print(json.dumps({
        "ok": True,
        "candidateId": candidate["candidateId"],
        "particularCount": candidate["particularCount"],
        "solidPatchReadyCount": candidate["solidPatchReadyCount"],
        "renderStrategyBlockers": len(candidate["renderStrategyBlockers"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga box binding failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
