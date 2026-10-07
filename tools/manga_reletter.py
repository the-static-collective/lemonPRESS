#!/usr/bin/env python3
"""RELETTER 001: deterministic returned-English lettering over one admitted Manga Press page."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press
import manga_translation_relay as relay

RECIPE_SCHEMA_NAME = "manga-reletter-recipe-v0.schema.json"
CANDIDATE_SCHEMA_NAME = "manga-reletter-candidate-v0.schema.json"
RECIPE_SCHEMA = "lemonpress/manga-reletter-recipe/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-reletter-candidate/v0"

LAWS = [
    "RELETTER != SOURCE",
    "RETURN != ORIGINAL",
    "MASK != PARENT ERASURE",
    "PIXEL PATCH != TEXT TRUTH",
    "OVERFLOW != SILENT TRUNCATION",
    "UNSUPPORTED GLYPH != SUBSTITUTE",
    "PARENT SURVIVES DESCENDANT",
    "RIGHTS NEVER EXPAND",
    "CANDIDATE != EDITION",
    "RENDERING != ADMISSION",
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


def _resolve(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "path must be non-empty and relative")
    root = root.resolve()
    path = (root / relative).resolve()
    require(path == root or root in path.parents, "path escapes root")
    return path


def _rect(value: dict[str, Any], width: int, height: int) -> dict[str, int]:
    require(isinstance(value, dict) and set(value) == {"x", "y", "width", "height"}, "rectPx shape")
    require(all(type(value[k]) is int for k in value), "rectPx must use integers")
    require(value["x"] >= 0 and value["y"] >= 0 and value["width"] > 0 and value["height"] > 0, "rectPx out of range")
    require(value["x"] + value["width"] <= width and value["y"] + value["height"] <= height, "rectPx outside parent pixels")
    return value


def _load_parent(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(declaration, dict) and set(declaration) == {"parentId", "pageManifest"},
            "parent requires parentId + pageManifest")
    press.text(declaration["parentId"])
    page = press.bound_json(root, declaration["pageManifest"])
    press.verify("page", page)
    require(page["sourceImage"] is not None, "intentional blank cannot be relettered")
    press.grants(page["grants"])
    require(page["grants"]["pixelReuse"], "reletter parent requires pixelReuse")
    require(page["grants"]["derivativeReuse"], "reletter parent requires derivativeReuse")
    source_path = press.bound_path(root, page["sourceImage"])
    with Image.open(source_path) as image:
        width, height = image.size
    return {
        "parentId": declaration["parentId"],
        "pageManifest": copy.deepcopy(declaration["pageManifest"]),
        "page": page,
        "sourcePath": source_path,
        "sourceSize": {"width": width, "height": height},
        "identity": {
            "editionId": page["editionId"],
            "issueId": page["issueId"],
            "pageId": page["pageId"],
            "pageHash": page["pageHash"],
        },
    }


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    if not text:
        return 0
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _break_word(draw: ImageDraw.ImageDraw, word: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for ch in word:
        probe = current + ch
        if current and _text_width(draw, probe, font) > max_width:
            chunks.append(current)
            current = ch
        else:
            current = probe
        require(_text_width(draw, current, font) <= max_width, f"glyph cannot fit declared box: {ch!r}")
    if current:
        chunks.append(current)
    return chunks


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    require(max_width > 0, "no text width remains after padding")
    lines: list[str] = []
    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        if paragraph == "":
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for word in words:
            if not word:
                continue
            pieces = [word] if _text_width(draw, word, font) <= max_width else _break_word(draw, word, font, max_width)
            for piece in pieces:
                probe = piece if not line else line + " " + piece
                if _text_width(draw, probe, font) <= max_width:
                    line = probe
                else:
                    if line:
                        lines.append(line)
                    line = piece
        if line:
            lines.append(line)
    return lines or [""]


def _render(root: Path, recipe: dict[str, Any], parent: dict[str, Any], relay_candidate: dict[str, Any]):
    segment_map = {s["segment_id"]: s for s in relay_candidate["segments"]}
    with Image.open(parent["sourcePath"]) as opened:
        canvas = opened.convert("RGBA")
    width, height = canvas.size
    draw = ImageDraw.Draw(canvas)
    transformations = []
    losses = []

    for placement in recipe["placements"]:
        require(placement["segmentId"] in segment_map, f"unknown segmentId: {placement['segmentId']}")
        segment = segment_map[placement["segmentId"]]
        text_value = segment[recipe["stage"]]
        require(text_value and all(ord(ch) < 128 for ch in text_value),
                f"v0 default font supports ASCII returned text only: {placement['segmentId']}")
        rect = _rect(placement["rectPx"], width, height)
        style = placement["style"]
        require(style["font"] == "pillow-default", "v0 font must be pillow-default")
        require(style["fontPx"] > 0 and style["paddingPx"] >= 0 and style["lineSpacingPx"] >= 0, "invalid lettering metrics")
        font = ImageFont.load_default(size=style["fontPx"])
        inner_width = rect["width"] - 2 * style["paddingPx"]
        inner_height = rect["height"] - 2 * style["paddingPx"]
        require(inner_width > 0 and inner_height > 0, "padding consumes declared box")
        lines = _wrap(draw, text_value, font, inner_width)
        sample_box = draw.textbbox((0, 0), "Ag", font=font)
        line_height = max(1, sample_box[3] - sample_box[1])
        total_height = len(lines) * line_height + max(0, len(lines) - 1) * style["lineSpacingPx"]
        require(total_height <= inner_height,
                f"text overflow refuses instead of truncating: {placement['placementId']}")

        x0, y0 = rect["x"], rect["y"]
        x1, y1 = x0 + rect["width"], y0 + rect["height"]
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=tuple(style["backgroundRgba"]))
        y = y0 + style["paddingPx"]
        for line in lines:
            line_width = _text_width(draw, line, font)
            if style["align"] == "left":
                x = x0 + style["paddingPx"]
            elif style["align"] == "center":
                x = x0 + (rect["width"] - line_width) // 2
            else:
                x = x1 - style["paddingPx"] - line_width
            draw.text((x, y), line, font=font, fill=tuple(style["foregroundRgba"]))
            y += line_height + style["lineSpacingPx"]

        transformations.append({
            "placementId": placement["placementId"],
            "segmentId": placement["segmentId"],
            "locus": segment["locus"],
            "stage": recipe["stage"],
            "renderedText": text_value,
            "renderedTextSha256": hashlib.sha256(text_value.encode("utf-8")).hexdigest(),
            "rectPx": copy.deepcopy(rect),
            "style": copy.deepcopy(style),
        })
        losses.append(f"{placement['placementId']}: descendant pixels inside rectPx replaced by declared solid patch + returned text")

    out = io.BytesIO()
    canvas.save(out, format="PNG", compress_level=9, optimize=False)
    return out.getvalue(), transformations, losses


def validate_recipe(root: Path, recipe: dict[str, Any]):
    validate_schema(recipe, RECIPE_SCHEMA_NAME)
    require(recipe["schema"] == RECIPE_SCHEMA, f"expected {RECIPE_SCHEMA}")
    require(recipe["stage"] == "return", "v0 reletters returned English only")
    parent = _load_parent(root, recipe["parent"])

    relay_path = _resolve(root, recipe["relaySpec"])
    relay_spec_bytes = relay_path.read_bytes()
    relay_spec = relay.read_json(relay_path)
    relay_candidate = relay.build_candidate(relay_spec)
    relay_spec_sha = hashlib.sha256(relay_spec_bytes).hexdigest()

    seen = set()
    for placement in recipe["placements"]:
        pid = placement["placementId"]
        require(pid not in seen, f"duplicate placementId: {pid}")
        seen.add(pid)
        _rect(placement["rectPx"], parent["sourceSize"]["width"], parent["sourceSize"]["height"])
    return parent, relay_candidate, relay_spec_sha


def build(root, recipe):
    root = Path(root).resolve()
    parent, relay_candidate, relay_spec_sha = validate_recipe(root, recipe)
    png_bytes, transformations, losses = _render(root, recipe, parent, relay_candidate)
    output_sha = hashlib.sha256(png_bytes).hexdigest()
    recipe_sha = hashlib.sha256(press.canonical_bytes(recipe)).hexdigest()

    candidate_seed = {
        "schema": CANDIDATE_SCHEMA,
        "status": "CANDIDATE",
        "title": recipe["title"],
        "recipeSha256": recipe_sha,
        "relaySpecSha256": relay_spec_sha,
        "relayCandidateId": relay_candidate["candidate_id"],
        "relayReturnTextSha256": relay_candidate["return_text_sha256"],
        "stage": recipe["stage"],
        "parent": {
            "parentId": parent["parentId"],
            "pageManifest": parent["pageManifest"],
            "identity": parent["identity"],
            "sourceImage": copy.deepcopy(parent["page"]["sourceImage"]),
        },
        "transformations": transformations,
        "outputImage": {
            "mediaType": "image/png",
            "sha256": output_sha,
            "pixelDimensions": copy.deepcopy(parent["sourceSize"]),
        },
        "effectiveGrants": copy.deepcopy(parent["page"]["grants"]),
        "authority": {
            "editorialSelection": False,
            "editionAdmission": False,
            "publication": False,
            "houseRelease": False,
        },
        "wrench": {
            "INPUT": {
                "page": parent["identity"],
                "relayCandidateId": relay_candidate["candidate_id"],
                "stage": recipe["stage"],
                "placements": [t["placementId"] for t in transformations],
            },
            "TRANSFORMATION": transformations,
            "OUTPUT": {"mediaType": "image/png", "sha256": output_sha},
            "RESIDUAL": [
                "Parent page manifest and source pixels remain unchanged and independently addressable.",
                "Relay source, Japanese pivot, and returned English remain addressable as separate text witnesses.",
            ],
            "LOSS": losses + [
                "The descendant uses the pinned Pillow default typeface rather than the source lettering.",
                "No semantics are inferred from source pixels outside declared text bindings.",
            ],
            "UNKNOWN": [
                "Human lettering quality and balloon fit beyond geometric non-overflow.",
                "Editorial selection, issue admission, publication, and house release.",
            ],
            "STOP": "Relettered candidate page only; explicit local page/edition admission remains required.",
        },
        "laws": LAWS,
    }
    candidate_id = "manga-reletter:" + hashlib.sha256(press.canonical_bytes({
        "recipeSha256": recipe_sha,
        "relayCandidateId": relay_candidate["candidate_id"],
        "parent": parent["identity"],
        "outputSha256": output_sha,
    })).hexdigest()
    candidate = {**candidate_seed, "candidateId": candidate_id}
    candidate["candidateHash"] = hashlib.sha256(press.canonical_bytes(candidate)).hexdigest()
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    return candidate, png_bytes


def verify_candidate(candidate):
    require(isinstance(candidate, dict) and candidate.get("schema") == CANDIDATE_SCHEMA, f"expected {CANDIDATE_SCHEMA}")
    expected = candidate.get("candidateHash")
    body = copy.deepcopy(candidate)
    body.pop("candidateHash", None)
    require(isinstance(expected, str) and expected == hashlib.sha256(press.canonical_bytes(body)).hexdigest(),
            "candidate hash mismatch")


def receipt(candidate: dict[str, Any]) -> str:
    lines = [
        "# RELETTER 001 receipt",
        "",
        f"Status: {candidate['status']}",
        f"Candidate: {candidate['candidateId']}",
        f"Relay candidate: {candidate['relayCandidateId']}",
        f"Return text SHA-256: {candidate['relayReturnTextSha256']}",
        f"Output PNG SHA-256: {candidate['outputImage']['sha256']}",
        "",
        "## Bindings",
        "",
    ]
    for t in candidate["transformations"]:
        lines.append(f"- {t['placementId']}: {t['segmentId']} / {t['locus']} -> {t['rectPx']} -> {t['renderedText']}")
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


def write_bundle(out_dir, candidate, png_bytes):
    out = Path(out_dir)
    _write_create_only(out / "reletter.png", png_bytes)
    _write_create_only(out / "candidate.json", press.canonical_bytes(candidate) + b"\n")
    _write_create_only(out / "RECEIPT.md", receipt(candidate).encode("utf-8"))


def verify_bundle(root, recipe, out_dir):
    expected_candidate, expected_png = build(root, recipe)
    out = Path(out_dir)
    actual_png = (out / "reletter.png").read_bytes()
    actual_candidate = press.read_json(out / "candidate.json")
    verify_candidate(actual_candidate)
    require(actual_png == expected_png, "reletter.png does not independently rebuild")
    require(press.canonical_bytes(actual_candidate) == press.canonical_bytes(expected_candidate),
            "candidate.json does not independently rebuild")
    require((out / "RECEIPT.md").read_text(encoding="utf-8") == receipt(expected_candidate),
            "RECEIPT.md does not independently rebuild")
    return expected_candidate


def main(argv=None):
    parser = argparse.ArgumentParser(description="RELETTER 001")
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("compose", "verify"):
        p = sub.add_parser(name)
        p.add_argument("recipe")
        p.add_argument("out_dir")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    recipe = press.read_json(_resolve(root, args.recipe))
    if args.command == "compose":
        candidate, png_bytes = build(root, recipe)
        write_bundle(args.out_dir, candidate, png_bytes)
        print(json.dumps({"ok": True, "candidateId": candidate["candidateId"],
                          "outputSha256": candidate["outputImage"]["sha256"]}, indent=2))
        return 0

    candidate = verify_bundle(root, recipe, args.out_dir)
    print(json.dumps({"ok": True, "candidateId": candidate["candidateId"], "verified": True}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga reletter failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
