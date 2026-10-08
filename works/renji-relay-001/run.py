#!/usr/bin/env python3
"""Materialize a create-only portable packet from exact selected donor bytes."""
import argparse
from pathlib import Path
import struct
import sys
import json
from verify import AUTHORITY, build_nodes, canon, read, require, sha, verify_bundle

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import manga_style_resolve as style


def compose(specimen, source_path, out):
    specimen = Path(specimen)
    recipe = read(specimen / "recipe.json")
    manifest = read(specimen / "source-manifest.json")
    require(manifest["law"] == "TRANSFORM != SEVER", "missing law")
    sources = manifest["sources"]
    require(len(sources) == 5 and len({s["slot"] for s in sources}) == 5, "five distinct declared donor slots required")
    selected = next((s for s in sources if s["slot"] == recipe["selectedSource"]), None)
    require(selected is not None, "unknown selected donor")
    data = Path(source_path).read_bytes()
    require(sha(data) == selected["sha256"] and len(data) == selected["bytes"], "selected donor bytes do not match manifest")
    require(data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR", "donor is not PNG")
    width, height = struct.unpack(">II", data[16:24])
    require(recipe["sourceDimensions"] == [width, height], "dimensions mismatch")
    source = {"slot": selected["slot"], "sha256": selected["sha256"], "bytes": len(data), "width": width, "height": height, "mediaType": "image/png"}
    stack_path = (ROOT / recipe["styleStackRef"]).resolve()
    require(stack_path.is_relative_to(ROOT / "works/style-stacks"), "stack path escape")
    stack = read(stack_path)
    profiles = [read(ROOT / "works/styles" / (key + ".json")) for key in sorted({e["styleId"] for e in stack["styles"]})]
    resolution = style.resolve(stack, profiles, ["textChannels.caption", "textChannels.dialogue", "visualPalette.colors"])
    inputs = {"stack": stack, "profiles": profiles, "resolution": resolution}
    nodes = build_nodes(source, recipe, inputs)
    packet = {"schema": "lemonpress/renji-relay-packet/v0", "source": source, "recipe": recipe, "styleInputs": inputs, "nodes": nodes, "head": nodes[-1]["identity"]}
    files = {"source.png": data, "packet.json": canon(packet) + b"\n", "press.json": canon(nodes[-1]["body"]) + b"\n"}
    for name in ("verify.py", "foreign_renderer.py", "verify-crossing.mjs"):
        files[name] = (specimen / name).read_bytes()
    out = Path(out)
    for name, body in files.items():
        require(not (out / name).exists() or (out / name).read_bytes() == body, "create-only conflict: " + name)
    for name, body in files.items():
        style.write_create_only(out / name, body)
    verify_bundle(out, selected["sha256"], sha(canon(recipe)))
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("out")
    args = parser.parse_args()
    packet = compose(Path(__file__).parent, args.source, args.out)
    print(json.dumps({"status": "CANDIDATE", "head": packet["head"], "sourceSha256": packet["source"]["sha256"], "recipeSha256": sha(canon(packet["recipe"])), "authority": AUTHORITY}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, struct.error) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
