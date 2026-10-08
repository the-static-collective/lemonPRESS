#!/usr/bin/env python3
"""Cold Relay ancestry audit. Standard library only; never infers admission."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

LAWS = ["TRANSFORM != SEVER", "THROUGH != TO", "RETURN != ORIGINAL", "DRIFT != FAILURE", "ANCESTRY != AUTHORITY", "RENDERING != AUTHORITY"]
KINDS = ["source.png", "text.transcription", "translate.pivot", "translate.return", "remix.sequence", "style.stack", "lemonpress.press"]
AUTHORITY = {"semantic": False, "houseAdmission": False, "publication": False}


def require(value, message):
    if not value:
        raise ValueError(message)


def canon(value):
    # ASCII keys and safe integers give identical Python/JS canonical bytes.
    def check(item):
        if isinstance(item, dict):
            require(all(isinstance(k, str) and k.isascii() for k in item), "non-ASCII object key")
            for child in item.values(): check(child)
        elif isinstance(item, list):
            for child in item: check(child)
        else:
            require(item is None or type(item) in (str, int, bool), "unsupported canonical value")
            if type(item) is int: require(abs(item) <= 9007199254740991, "unsafe integer")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
        parse_constant=lambda v: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def check_digest(value):
    require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "invalid SHA-256")


def node(kind, parent, body):
    value = {"schema": "lemonpress/renji-relay-node/v0", "kind": kind, "parent": parent,
             "body": body, "laws": LAWS, "authority": AUTHORITY}
    value["identity"] = sha(canon(value))
    return value


def validate_recipe(recipe):
    require(set(recipe) == {"schema", "id", "selectedSource", "sourceDimensions", "transcription", "translation", "remix", "styleStackRef", "press", "rights", "loss", "unknown"}, "unknown/missing recipe field")
    require(recipe["schema"] == "lemonpress/renji-relay-recipe/v0", "wrong recipe schema")
    require(recipe["rights"] == {"scope": "user-directed private experiment", "publication": False, "redistributionGrant": False}, "experiment cannot expand rights")
    source = recipe["transcription"]
    require(set(source) == {"method", "coverage", "segments", "omitted"} and source["coverage"] == "selected-excerpts", "transcription coverage must be explicit")
    require(source["method"] == "assistant visual transcription; frozen declaration", "undeclared transcription method")
    ids = [s["id"] for s in source["segments"]]
    require(bool(ids) and len(ids) == len(set(ids)), "nonunique or empty segments")
    for s in source["segments"]:
        require(set(s) == {"id", "locus", "channel", "text", "visibility"} and s["visibility"] == "complete", "invalid transcription segment")
        require(s["channel"] in {"caption", "dialogue", "world_text"} and all(isinstance(s[k], str) and bool(s[k]) for k in ("id", "locus", "text")), "invalid text/channel")
    translation = recipe["translation"]
    require(set(translation) == {"method", "route", "pivot", "return", "semanticEquivalence"} and translation["route"] == ["en", "ja", "en"] and translation["semanticEquivalence"] is False, "invalid language-through route")
    require(translation["method"] == "assistant-authored frozen stages; not an independent translator witness", "translation method must be explicit")
    for key in ("pivot", "return"):
        rows = translation[key]
        require([s["id"] for s in rows] == ids, "translation intermediate/return must cover exact source order")
        for s in rows:
            require(set(s) == {"id", "text", "drift"} and isinstance(s["text"], str) and bool(s["text"]), "invalid translation row")
            require(isinstance(s["drift"], str) and bool(s["drift"]), "drift must be declared")
    remix = recipe["remix"]
    require(set(remix) == {"order", "omit", "reason"} and bool(remix["order"]), "invalid remix")
    require(len(remix["order"]) == len(set(remix["order"])) and len(remix["omit"]) == len(set(remix["omit"])), "distinct placement ids required")
    require(set(remix["order"]).isdisjoint(remix["omit"]) and set(remix["order"]) | set(remix["omit"]) == set(ids), "remix must account for all particulars")
    require(recipe["press"] == {"issueId": "RENJI_RELAY_001", "status": "CANDIDATE", "readingDirection": "top-to-bottom"}, "press candidate cannot claim original/admission")
    require(isinstance(recipe["styleStackRef"], str) and recipe["styleStackRef"].startswith("works/style-stacks/") and recipe["styleStackRef"].endswith("/stack.json") and ".." not in recipe["styleStackRef"], "invalid style-stack reference")


def build_nodes(source, recipe, style_inputs):
    validate_recipe(recipe)
    require(set(style_inputs) == {"stack", "profiles", "resolution"}, "invalid style inputs")
    stack, profiles, resolution = (style_inputs[k] for k in ("stack", "profiles", "resolution"))
    require(set(resolution) == {"schema", "styleStackId", "stackHash", "resolvedDomains", "resolvedBehavior", "appliedStyles", "conflicts", "warnings", "laws", "authority", "resolutionHash"}, "invalid style resolution")
    require(resolution["authority"] == {"semanticAuthority": False, "admission": False, "publication": False}, "style authority expansion")
    require(resolution["resolutionHash"] == sha(canon({k: v for k, v in resolution.items() if k != "resolutionHash"})), "style resolution hash mismatch")
    require(resolution["stackHash"] == sha(canon(stack)), "stack ancestry mismatch")
    catalog = {p["id"]: p for p in profiles}
    require(len(catalog) == len(profiles) and {e["styleId"] for e in stack["styles"]} == set(catalog), "style profile coverage mismatch")
    require(resolution["appliedStyles"] == [{"entry": entry, "profileHash": sha(canon(catalog[entry["styleId"]]))} for entry in stack["styles"]], "style ancestry mismatch")
    require(resolution["styleStackId"] == stack["id"] and resolution["conflicts"] == [], "style unresolved")
    nodes = []
    def add(kind, value):
        nodes.append(node(kind, nodes[-1]["identity"] if nodes else None, value))
    add("source.png", source)
    add("text.transcription", recipe["transcription"])
    add("translate.pivot", {"language": "ja", "method": recipe["translation"]["method"], "segments": recipe["translation"]["pivot"], "semanticEquivalence": False})
    add("translate.return", {"language": "en", "derivedFrom": "ja", "segments": recipe["translation"]["return"], "semanticEquivalence": False})
    add("remix.sequence", recipe["remix"])
    add("style.stack", {"styleStackRef": recipe["styleStackRef"], **style_inputs})
    originals = {s["id"]: s for s in recipe["transcription"]["segments"]}
    pivots = {s["id"]: s for s in recipe["translation"]["pivot"]}
    returns = {s["id"]: s for s in recipe["translation"]["return"]}
    placements = [{"id": key, "channel": originals[key]["channel"], "locus": originals[key]["locus"],
                   "primary": pivots[key]["text"], "gloss": returns[key]["text"],
                   "sourceText": originals[key]["text"], "drift": returns[key]["drift"]} for key in recipe["remix"]["order"]]
    channels = resolution["resolvedBehavior"].get("textChannels", {})
    for placement in placements:
        channel = channels.get(placement["channel"], {})
        require(channel.get("primary") == "ja" and channel.get("gloss") == "en" and channel.get("relation") == "witness" and channel.get("purpose") == placement["channel"], "renderer-required language/channel behavior absent")
    add("lemonpress.press", {**recipe["press"], "placements": placements, "styleStackRef": recipe["styleStackRef"],
        "stackHash": resolution["stackHash"], "resolutionHash": resolution["resolutionHash"],
        "sourceSha256": source["sha256"], "sourceSlot": source["slot"], "styleParent": nodes[-1]["identity"],
        "loss": recipe["loss"], "unknown": recipe["unknown"], "rights": recipe["rights"], "authority": AUTHORITY})
    return nodes


def verify_bundle(folder, expected_source, expected_recipe=None):
    folder = Path(folder)
    packet = read(folder / "packet.json")
    require(set(packet) == {"schema", "source", "recipe", "styleInputs", "nodes", "head"} and packet["schema"] == "lemonpress/renji-relay-packet/v0", "invalid packet")
    check_digest(expected_source)
    source = packet["source"]
    require(set(source) == {"slot", "sha256", "bytes", "width", "height", "mediaType"}, "invalid source declaration")
    data = (folder / "source.png").read_bytes()
    require(source["sha256"] == expected_source == sha(data) and source["bytes"] == len(data), "source byte identity mismatch")
    require(data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR", "source is not a PNG")
    require(struct.unpack(">II", data[16:24]) == (source["width"], source["height"]), "source dimensions mismatch")
    recipe = packet["recipe"]
    require(recipe["selectedSource"] == source["slot"] and recipe["sourceDimensions"] == [source["width"], source["height"]], "recipe source mismatch")
    if expected_recipe:
        require(sha(canon(recipe)) == expected_recipe, "recipe anchor mismatch")
    expected = build_nodes(source, recipe, packet["styleInputs"])
    require(packet["nodes"] == expected and [n["kind"] for n in packet["nodes"]] == KINDS and packet["head"] == expected[-1]["identity"], "broken, missing or undeclared ancestry")
    require((folder / "press.json").read_bytes() == canon(expected[-1]["body"]) + b"\n", "press carrier mismatch")
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    parser.add_argument("--expected-source", required=True, help="SHA-256 from a separately trusted manifest")
    parser.add_argument("--expected-recipe")
    args = parser.parse_args()
    packet = verify_bundle(args.bundle, args.expected_source, args.expected_recipe)
    print(json.dumps({"status": "PASS", "claim": "byte-bound declared ancestry; not semantic equivalence or signer authority", "sourceSha256": packet["source"]["sha256"], "recipeSha256": sha(canon(packet["recipe"])), "head": packet["head"], "crossingSignatures": "NOT_CHECKED: run verify-crossing.mjs", "localAdmission": "NOT_INFERRED"}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, struct.error) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        sys.exit(2)
