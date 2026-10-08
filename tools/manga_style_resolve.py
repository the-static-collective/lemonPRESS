#!/usr/bin/env python3
"""Resolve frozen style behavior. No renderer, model, or admission is invoked."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "languageBehavior": {"primaryLanguage", "glossLanguage", "routeVisible", "sourceTraceVisible"},
    "textChannels": {"dialogue", "caption", "world_text", "signage", "sfx", "title_card", "meta_text", "screen_ui", "handwriting", "embedded_source_text"},
    "visualPalette": {"colors", "contrast", "light"},
    "panelBehavior": {"rhythm", "insets", "architecture"},
    "tone": {"presence", "tension", "warmth"},
    "worldMotifs": {"doors", "rooms", "receipts", "screens", "artifacts"},
}
LAWS = ["STYLE != CONTENT", "STYLE != AUTHORITY", "STYLE != ADMISSION", "COMPOSITION != COLLAPSE", "LAYER != REPLACEMENT", "PRIMARY != GLOSS", "GLOSS != REPLACEMENT", "WORLD TEXT != DIALOGUE", "STYLE CONFLICT MUST BE RESOLVED EXPLICITLY", "SOURCE TRACE MAY SURVIVE", "LANGUAGE PASSAGE MAY REMAIN VISIBLE", "STACK CHANGE != SAME CANDIDATE"]
AUTHORITY = {"semanticAuthority": False, "admission": False, "publication": False}


def require(value, message):
    if not value:
        raise ValueError(message)


def canon(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def validate(value, kind):
    import jsonschema
    schema = read(ROOT / "schemas" / f"manga-style-{kind}-v0.schema.json")
    try:
        jsonschema.Draft202012Validator(schema).validate(value)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"{kind} schema: {exc.message}") from exc


def validate_profile(profile):
    validate(profile, "profile")
    require(set(LAWS) <= set(profile["laws"]), "missing non-collapse law")
    require(profile["authority"] == AUTHORITY, "style cannot assert authority")
    for domain, declaration in profile["domains"].items():
        behavior = profile["behavior"].get(domain, {})
        require(bool(behavior) == (declaration != "none"), "ambiguous domain declaration: " + domain)
    language = profile["behavior"].get("languageBehavior", {})
    require(not language or language.get("primaryLanguage") != language.get("glossLanguage"), "primary and gloss must remain distinct")
    for name, channel in profile["behavior"].get("textChannels", {}).items():
        require(channel["primary"] != channel["gloss"] and channel["relation"] == "witness", "gloss collapse")
        require(channel["purpose"] == name, "world text and dialogue cannot exchange channel identity")


def resolve(stack, profiles, required_fields=()):
    validate(stack, "stack")
    require(set(LAWS) <= set(stack["laws"]), "stack missing non-collapse law")
    require(len({p["id"] for p in profiles}) == len(profiles), "duplicate profile id")
    catalog = {p["id"]: p for p in profiles}
    for profile in profiles:
        validate_profile(profile)
    offers, overrides, applied = {}, {}, []
    for index, entry in enumerate(stack["styles"]):
        require(entry["styleId"] in catalog, "unknown style: " + entry["styleId"])
        profile = catalog[entry["styleId"]]
        mask = entry["domainMask"]
        require(len(mask) == len(set(mask)), "duplicate domain mask")
        channels = entry.get("channelMask", [])
        if entry["mode"] == "channel-scoped":
            require(mask == ["textChannels"] and bool(channels), "channel scope requires explicit text-channel mask")
        else:
            require(not channels, "channelMask requires channel-scoped mode")
        if entry["mode"] == "global":
            require(set(mask) == set(FIELDS), "global style must declare all domain masks")
        scoped_paths = set()
        for domain in mask:
            for field, value in profile["behavior"].get(domain, {}).items():
                if channels and field not in channels:
                    continue
                path = domain + "." + field
                scoped_paths.add(path)
                offers.setdefault(path, []).append({"value": value, "declaration": profile["domains"][domain],
                    "priority": entry["priority"], "styleId": profile["id"], "index": index})
        for path, value in entry["overrides"].items():
            require(path in scoped_paths, "unknown or unscoped override target: " + path)
            require(path not in overrides, "multiple explicit overrides: " + path)
            # Validate override values with the profile's own field schema.
            domain, field = path.split(".")
            changed = copy.deepcopy(profile)
            changed["behavior"][domain][field] = value
            validate_profile(changed)
            overrides[path] = {"value": value, "styleId": profile["id"]}
        applied.append({"entry": copy.deepcopy(entry), "profileHash": digest(profile)})
    result, provenance, warnings = {}, {}, []
    for path, choices in sorted(offers.items()):
        owners = [c for c in choices if c["declaration"] == "own"]
        candidates = owners or choices
        candidates = sorted(candidates, key=lambda c: (-c["priority"], c["index"]))
        if path in overrides:
            selected = overrides[path]
            rule = "explicit-override"
        else:
            if len(owners) > 1:
                require(stack["resolutionPolicy"] == "explicit-priority", "unresolved ownership conflict: " + path)
                require(candidates[0]["priority"] != candidates[1]["priority"], "tied ownership conflict: " + path)
            if not owners and len(candidates) > 1:
                require(candidates[0]["priority"] != candidates[1]["priority"] or all(c["value"] == candidates[0]["value"] for c in candidates), "ambiguous suggestions: " + path)
            selected = candidates[0]
            rule = "owner" if owners else "suggestion"
        domain, field = path.split(".")
        result.setdefault(domain, {})[field] = copy.deepcopy(selected["value"])
        provenance[path] = {"styleId": selected["styleId"], "rule": rule}
    for path in required_fields:
        require(path in provenance, "renderer-required behavior absent: " + path)
    laws = sorted(set(stack["laws"]).union(*(p["laws"] for p in catalog.values() if p["id"] in {e["styleId"] for e in stack["styles"]})))
    resolution = {"schema": "lemonpress/manga-style-resolution/v0", "styleStackId": stack["id"],
        "stackHash": digest(stack), "resolvedDomains": provenance, "resolvedBehavior": result,
        "appliedStyles": applied, "conflicts": [], "warnings": warnings, "laws": laws, "authority": AUTHORITY.copy()}
    # Combined language behavior must also obey the non-collapse rules.
    combined = result.get("languageBehavior", {})
    require(not combined or combined.get("primaryLanguage") != combined.get("glossLanguage"), "resolved gloss collapse")
    resolution["resolutionHash"] = digest(resolution)
    validate(resolution, "resolution")
    return resolution


def candidate_identity(parent_sha256, resolution):
    validate(resolution, "resolution")
    require(len(parent_sha256) == 64 and all(c in "0123456789abcdef" for c in parent_sha256), "invalid parent SHA-256")
    body = {k: v for k, v in resolution.items() if k != "resolutionHash"}
    require(digest(body) == resolution["resolutionHash"], "resolution hash mismatch")
    return "manga-style-candidate:" + digest({"parent": parent_sha256, "styleStackHash": resolution["stackHash"], "resolutionHash": resolution["resolutionHash"]})


def write_create_only(path, data):
    path = Path(path)
    if path.exists():
        require(path.read_bytes() == data, "create-only conflict: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["compose", "verify"])
    parser.add_argument("stack")
    parser.add_argument("output")
    parser.add_argument("--profiles", default=str(ROOT / "works/styles"))
    parser.add_argument("--require-field", action="append", default=[])
    args = parser.parse_args()
    profiles = [read(p) for p in sorted(Path(args.profiles).glob("*.json"))]
    resolution = resolve(read(args.stack), profiles, args.require_field)
    data = canon(resolution) + b"\n"
    if args.command == "verify":
        require(Path(args.output).read_bytes() == data, "resolution does not replay")
    else:
        write_create_only(args.output, data)
    print(json.dumps({"status": "VERIFIED" if args.command == "verify" else "CANDIDATE", "resolutionHash": resolution["resolutionHash"], "authority": AUTHORITY}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
