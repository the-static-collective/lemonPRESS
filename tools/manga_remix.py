#!/usr/bin/env python3
"""Manga Remix 001: deterministic candidate pages from admitted manga parents."""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press

RECIPE_SCHEMA = "lemonpress/manga-remix-recipe/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-remix-candidate/v0"
LAWS = [
    "REMIX != SOURCE",
    "RECIPE != AUTHORITY",
    "SELECTION != ADMISSION",
    "PARENT SURVIVES DESCENDANT",
    "ORDER IS DECLARED",
    "CROP REQUIRES PIXEL HARVEST",
    "RIGHTS INTERSECT; NEVER EXPAND",
    "CANDIDATE != EDITION",
    "OUTPUT != PUBLICATION",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rectangle(value, label):
    require(isinstance(value, dict) and set(value) == {"x", "y", "width", "height"}, f"{label} rectangle")
    for key in ("x", "y", "width", "height"):
        require(type(value[key]) is int, f"{label} must use integers")
    require(value["x"] >= 0 and value["y"] >= 0 and value["width"] > 0 and value["height"] > 0,
            f"{label} rectangle out of range")
    return value


def _identity(edition, page):
    return press.page_identity(edition, page)


def _load_parent(root, declaration):
    require(isinstance(declaration, dict) and set(declaration) == {"parentId", "editionManifest", "pageManifest"},
            "parent requires parentId + editionManifest + pageManifest")
    press.text(declaration["parentId"])
    edition = press.bound_json(root, declaration["editionManifest"])
    pages, _ = press.validate_edition(root, edition)
    page = press.bound_json(root, declaration["pageManifest"])
    press.verify("page", page)
    require(declaration["pageManifest"] in edition["pageManifests"], "page manifest is not bound into parent edition")
    require(page["pageId"] in pages and pages[page["pageId"]]["pageHash"] == page["pageHash"],
            "page identity mismatch inside parent edition")
    require(page["sourceImage"] is not None, "intentional blank cannot be a remix pixel parent")
    source_path = press.bound_path(root, page["sourceImage"])
    press.grants(page["grants"])
    require(page["grants"]["pixelReuse"], f"parent {declaration['parentId']} does not grant pixelReuse")
    require(page["grants"]["derivativeReuse"], f"parent {declaration['parentId']} does not grant derivativeReuse")
    with Image.open(source_path) as image:
        width, height = image.size
    return {
        "parentId": declaration["parentId"],
        "editionManifest": declaration["editionManifest"],
        "pageManifest": declaration["pageManifest"],
        "edition": edition,
        "page": page,
        "identity": _identity(edition, page),
        "sourcePath": source_path,
        "sourceSize": {"width": width, "height": height},
    }


def validate_recipe(root, recipe):
    require(isinstance(recipe, dict), "recipe must be an object")
    required = {"schema", "title", "canvasPx", "backgroundRgba", "parents", "placements"}
    require(set(recipe) == required, "unsupported or incomplete remix recipe")
    require(recipe["schema"] == RECIPE_SCHEMA, f"expected {RECIPE_SCHEMA}")
    press.text(recipe["title"])
    canvas = recipe["canvasPx"]
    require(isinstance(canvas, dict) and set(canvas) == {"width", "height"}, "canvasPx shape")
    require(type(canvas["width"]) is int and type(canvas["height"]) is int and canvas["width"] > 0 and canvas["height"] > 0,
            "canvas dimensions")
    bg = recipe["backgroundRgba"]
    require(isinstance(bg, list) and len(bg) == 4 and all(type(x) is int and 0 <= x <= 255 for x in bg),
            "backgroundRgba must be four bytes")

    declarations = recipe["parents"]
    require(isinstance(declarations, list) and declarations, "at least one parent required")
    parents = {}
    for declaration in declarations:
        loaded = _load_parent(root, declaration)
        pid = loaded["parentId"]
        require(pid not in parents, "duplicate parentId")
        parents[pid] = loaded

    placements = recipe["placements"]
    require(isinstance(placements, list) and placements, "at least one placement required")
    seen = set()
    for placement in placements:
        keys = {"placementId", "parentId", "sourceRectPx", "destinationRectPx", "rotateDeg",
                "mirrorX", "mirrorY", "opacity", "resample"}
        require(isinstance(placement, dict) and set(placement) == keys, "placement shape")
        press.text(placement["placementId"])
        require(placement["placementId"] not in seen, "duplicate placementId")
        seen.add(placement["placementId"])
        require(placement["parentId"] in parents, "placement references unknown parent")
        require(placement["rotateDeg"] in (0, 90, 180, 270), "rotateDeg must be 0/90/180/270")
        require(type(placement["mirrorX"]) is bool and type(placement["mirrorY"]) is bool, "mirror flags must be boolean")
        require(type(placement["opacity"]) is int and 0 <= placement["opacity"] <= 255, "opacity must be 0..255")
        require(placement["resample"] == "nearest", "v0 supports deterministic nearest resampling only")
        dest = rectangle(placement["destinationRectPx"], "destinationRectPx")
        require(dest["x"] + dest["width"] <= canvas["width"] and dest["y"] + dest["height"] <= canvas["height"],
                "destination outside canvas")

        parent = parents[placement["parentId"]]
        width, height = parent["sourceSize"]["width"], parent["sourceSize"]["height"]
        src = placement["sourceRectPx"]
        if src is not None:
            src = rectangle(src, "sourceRectPx")
            require(src["x"] + src["width"] <= width and src["y"] + src["height"] <= height,
                    "source crop outside parent pixels")
            whole = src["x"] == 0 and src["y"] == 0 and src["width"] == width and src["height"] == height
            if not whole:
                require(parent["page"]["grants"]["pixelHarvest"],
                        f"parent {placement['parentId']} crop requires pixelHarvest")
    return parents


def _render(root, recipe, parents):
    canvas = Image.new("RGBA", (recipe["canvasPx"]["width"], recipe["canvasPx"]["height"]),
                       tuple(recipe["backgroundRgba"]))
    losses = []
    transformations = []

    for placement in recipe["placements"]:
        parent = parents[placement["parentId"]]
        with Image.open(parent["sourcePath"]) as opened:
            layer = opened.convert("RGBA")
        width, height = layer.size
        src = placement["sourceRectPx"]
        if src is not None:
            whole = src["x"] == 0 and src["y"] == 0 and src["width"] == width and src["height"] == height
            if not whole:
                layer = layer.crop((src["x"], src["y"], src["x"] + src["width"], src["y"] + src["height"]))
                losses.append(f"{placement['placementId']}: pixels outside declared sourceRectPx omitted")
        if placement["rotateDeg"]:
            layer = layer.rotate(-placement["rotateDeg"], expand=True)
        if placement["mirrorX"]:
            layer = ImageOps.mirror(layer)
        if placement["mirrorY"]:
            layer = ImageOps.flip(layer)

        dest = placement["destinationRectPx"]
        if layer.size != (dest["width"], dest["height"]):
            losses.append(f"{placement['placementId']}: raster resampled to declared destinationRectPx")
            layer = layer.resize((dest["width"], dest["height"]), resample=Image.Resampling.NEAREST)

        if placement["opacity"] != 255:
            alpha = layer.getchannel("A")
            lut = [i * placement["opacity"] // 255 for i in range(256)]
            layer.putalpha(alpha.point(lut))
            losses.append(f"{placement['placementId']}: opacity reduced")

        canvas.alpha_composite(layer, (dest["x"], dest["y"]))
        transformations.append({
            "placementId": placement["placementId"],
            "parentId": placement["parentId"],
            "sourceRectPx": placement["sourceRectPx"],
            "destinationRectPx": placement["destinationRectPx"],
            "rotateDeg": placement["rotateDeg"],
            "mirrorX": placement["mirrorX"],
            "mirrorY": placement["mirrorY"],
            "opacity": placement["opacity"],
            "resample": placement["resample"],
        })

    out = io.BytesIO()
    canvas.save(out, format="PNG", compress_level=9, optimize=False)
    return out.getvalue(), transformations, list(dict.fromkeys(losses))


def _intersection(parents):
    ids = list(parents)
    return {key: all(parents[pid]["page"]["grants"][key] for pid in ids) for key in press.GRANTS}


def build(root, recipe):
    root = Path(root).resolve()
    parents = validate_recipe(root, recipe)
    png_bytes, transformations, losses = _render(root, recipe, parents)
    output_sha = hashlib.sha256(png_bytes).hexdigest()
    recipe_hash = hashlib.sha256(press.canonical_bytes(recipe)).hexdigest()

    ordered_parents = []
    for declaration in recipe["parents"]:
        parent = parents[declaration["parentId"]]
        ordered_parents.append({
            "parentId": parent["parentId"],
            "editionManifest": parent["editionManifest"],
            "pageManifest": parent["pageManifest"],
            "identity": parent["identity"],
        })

    candidate_seed = {
        "schema": CANDIDATE_SCHEMA,
        "status": "CANDIDATE",
        "title": recipe["title"],
        "recipeSha256": recipe_hash,
        "parents": ordered_parents,
        "canvasPx": recipe["canvasPx"],
        "backgroundRgba": recipe["backgroundRgba"],
        "transformations": transformations,
        "outputImage": {
            "mediaType": "image/png",
            "sha256": output_sha,
            "pixelDimensions": copy.deepcopy(recipe["canvasPx"]),
        },
        "effectiveGrants": _intersection(parents),
        "authority": {
            "editorialSelection": False,
            "editionAdmission": False,
            "publication": False,
            "houseRelease": False,
        },
        "wrench": {
            "INPUT": [p["identity"] for p in ordered_parents],
            "TRANSFORMATION": transformations,
            "OUTPUT": {"mediaType": "image/png", "sha256": output_sha},
            "RESIDUAL": ["Every parent page and bound source image remains unchanged and independently addressable."],
            "LOSS": losses,
            "UNKNOWN": ["No panel, character, semantic, or narrative fusion is inferred by this compositor."],
            "STOP": "Candidate page only. Explicit local page/edition admission is still required before issue or publication use.",
        },
        "laws": LAWS,
    }
    candidate_id = "manga-remix:" + hashlib.sha256(
        press.canonical_bytes({"recipeSha256": recipe_hash, "outputSha256": output_sha, "parents": ordered_parents})
    ).hexdigest()
    candidate = {**candidate_seed, "candidateId": candidate_id}
    candidate["candidateHash"] = hashlib.sha256(press.canonical_bytes(candidate)).hexdigest()
    return candidate, png_bytes


def verify_candidate(candidate):
    require(isinstance(candidate, dict) and candidate.get("schema") == CANDIDATE_SCHEMA,
            f"expected {CANDIDATE_SCHEMA}")
    expected = candidate.get("candidateHash")
    body = copy.deepcopy(candidate)
    body.pop("candidateHash", None)
    require(isinstance(expected, str) and expected == hashlib.sha256(press.canonical_bytes(body)).hexdigest(),
            "candidate hash mismatch")


def _write_create_only(path, data):
    if path.exists():
        require(path.read_bytes() == data, f"create-only conflict: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_bundle(out_dir, candidate, png_bytes):
    out = Path(out_dir)
    _write_create_only(out / "remix.png", png_bytes)
    _write_create_only(out / "candidate.json", press.canonical_bytes(candidate) + b"\n")


def verify_bundle(root, recipe, out_dir):
    expected_candidate, expected_png = build(root, recipe)
    out = Path(out_dir)
    actual_png = (out / "remix.png").read_bytes()
    actual_candidate = press.read_json(out / "candidate.json")
    verify_candidate(actual_candidate)
    require(actual_png == expected_png, "remix.png does not independently rebuild")
    require(press.canonical_bytes(actual_candidate) == press.canonical_bytes(expected_candidate),
            "candidate.json does not independently rebuild")
    return expected_candidate


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("compose", "verify"):
        p = sub.add_parser(name)
        p.add_argument("recipe")
        p.add_argument("out_dir")
    args = parser.parse_args(argv)

    recipe = press.read_json(Path(args.recipe))
    if args.command == "compose":
        candidate, png_bytes = build(args.root, recipe)
        write_bundle(args.out_dir, candidate, png_bytes)
        print(json.dumps({"ok": True, "candidateId": candidate["candidateId"],
                          "outputSha256": candidate["outputImage"]["sha256"]}, indent=2))
        return 0

    candidate = verify_bundle(args.root, recipe, args.out_dir)
    print(json.dumps({"ok": True, "candidateId": candidate["candidateId"],
                      "verified": True}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga remix failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
