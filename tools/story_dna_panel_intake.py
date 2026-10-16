"""lemonPRESS KEEP-A-PLACE-002: accept illustrated Story DNA candidate as a held local parcel.

No network, Git change, external publication, media upload, edition admission, or license.
Use: python3 tools/story_dna_panel_intake.py build storyboard.json art/ held-parcel/
     python3 tools/story_dna_panel_intake.py verify held-parcel/manifest.json held-parcel/
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "lemonpress/held-illustrated-panel-parcel/v0"
INPUT_SCHEMA = "story-dna/private-local-storyboard-preview/v0"
SOURCE_SHA = "7f16ead290a86a5997e714e1280befe282b4047c1d40de07e36849521cd304d1"
SOURCE_BYTES = 4586389
EXPECTED = [f"KP{i:02}" for i in range(1, 6)]
DANGEROUS = re.compile(
    r"<!DOCTYPE|<!ENTITY|<script\b|<foreignObject\b|<iframe\b|"
    r"\bon[a-z]+\s*=|\b(?:href|xlink:href)\s*=|\burl\s*\(\s*['\"]?\s*(?:https?:|data:|javascript:)",
    re.IGNORECASE
)


def require(cond, reason):
    if not cond:
        raise ValueError(reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(body) -> bytes:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def checked_storyboard(raw):
    require(isinstance(raw, dict) and raw.get("schema") == INPUT_SCHEMA and raw.get("status") == "HOLD", "held storyboard required")
    src = raw.get("source", {})
    require(src.get("sha256") == SOURCE_SHA and src.get("sizeBytes") == SOURCE_BYTES, "owner-local audio identity mismatch")
    require(raw.get("sourcePlatformTrackId") is None, "Suno track id not established")
    require(isinstance(raw.get("rights"), str) and "not established" in raw["rights"], "not a rights-approved source")
    panels = raw.get("panels")
    require(isinstance(panels, list) and len(panels) == 5, "requires five distinct panels")
    require([p.get("id") for p in panels] == EXPECTED, "unknown or reordered panel identity")
    prev = -1
    for p in panels:
        require(isinstance(p.get("at"), (float, int)) and not isinstance(p["at"], bool) and
                isinstance(p.get("end"), (float, int)) and not isinstance(p["end"], bool) and
                0 <= p["at"] < p["end"] <= src.get("durationSeconds", 0) + 0.001 and p["at"] >= prev, "overlapping or impossible music cue")
        prev = p["end"]
        for key in ("title", "view", "palette"):
            require(isinstance(p.get(key), str) and 0 < len(p[key].strip()) < 1600, "missing or unbounded creative note")
    return panels


def checked_svg(payload: bytes) -> None:
    require(200 <= len(payload) <= 150000, "SVG size outside bounded input")
    text = payload.decode("utf-8")
    require(text.lstrip().startswith("<svg") and "</svg>" in text, "expected standalone local SVG")
    require(not DANGEROUS.search(text), "SVG has scripting, remote, data or event-bearing references")
    require("xmlns=\"http://www.w3.org/2000/svg\"" in text, "SVG namespace missing")
    require("viewBox=" in text, "SVG must declare an inspectable viewport")


def image_path(panel_id: str):
    require(panel_id in EXPECTED, "unrecognized panel id")
    return f"panels/{panel_id}.svg"


def produce(storyboard, illustrations: dict):
    panels = checked_storyboard(storyboard)
    require(set(illustrations) == set(EXPECTED), "five exact independent SVG assets required")
    body = {
        "schema": SCHEMA,
        "state": "HOLD",
        "selection": "NONE",
        "ownerAdmission": "NOT_REQUESTED",
        "publication": False,
        "renderedVideo": False,
        "rights": {
            "sourceAudioRelease": "UNVERIFIED",
            "illustratedCandidateEditorialStatus": "UNSELECTED",
            "publicAudioIncluded": False,
            "sourceAudioBytesCarried": False,
            "fictionalSubjectOnly": True
        },
        "source": {
            "schema": INPUT_SCHEMA,
            "title": storyboard["source"]["title"],
            "sha256": storyboard["source"]["sha256"],
            "bytes": storyboard["source"]["sizeBytes"],
            "platformTrackId": None,
            "sourceOriginalNotRewritten": True
        },
        "pages": []
    }
    for p in panels:
        payload = illustrations[p["id"]]
        checked_svg(payload)
        body["pages"].append({
            "id": p["id"],
            "cue": {"startSeconds": p["at"], "endSeconds": p["end"], "approximate": True},
            "image": {"path": image_path(p["id"]), "sha256": digest(payload), "bytes": len(payload), "mime": "image/svg+xml"},
            "creativeNote": p["view"],
            "title": p["title"],
            "palette": p["palette"],
            "caption": "",
            "speech": "",
            "sfx": "",
            "selection": "HOLD"
        })
    return {**body, "parcelSha256": digest(canonical(body))}


def verify(manifest, root: Path):
    require(manifest.get("schema") == SCHEMA, "parcel schema mismatch")
    provided = manifest.get("parcelSha256")
    require(isinstance(provided, str) and re.fullmatch(r"[0-9a-f]{64}", provided), "parcel digest missing")
    body = {k: v for k, v in manifest.items() if k != "parcelSha256"}
    require(digest(canonical(body)) == provided, "parcel content mutated")
    require(manifest.get("state") == "HOLD" and manifest.get("selection") == "NONE" and
            manifest.get("ownerAdmission") == "NOT_REQUESTED" and
            manifest.get("publication") is False and manifest.get("renderedVideo") is False, "attempted authority escalation")
    require(manifest.get("source", {}).get("sha256") == SOURCE_SHA and manifest.get("source", {}).get("bytes") == SOURCE_BYTES and
            manifest["source"].get("platformTrackId") is None, "source mismatch")
    require(manifest.get("rights", {}).get("sourceAudioRelease") == "UNVERIFIED" and
            manifest["rights"].get("publicAudioIncluded") is False and
            manifest["rights"].get("sourceAudioBytesCarried") is False, "rights escalation")
    pages = manifest.get("pages")
    require(isinstance(pages, list) and [p.get("id") for p in pages] == EXPECTED, "page identities incomplete")
    for p in pages:
        img = p.get("image", {})
        path = image_path(p["id"])
        require(img.get("path") == path and img.get("mime") == "image/svg+xml", "invalid page path or type")
        data = (root / path).read_bytes()
        checked_svg(data)
        require(len(data) == img.get("bytes") and digest(data) == img.get("sha256"), "page content changed")
        require(p.get("selection") == "HOLD" and p.get("caption") == "" and p.get("speech") == "" and p.get("sfx") == "",
                "human selection / lettered edition does not exist")
    return {"schema": "lemonpress/held-illustrated-panel-parcel-witness/v0", "source": SOURCE_SHA,
            "parcel": provided, "pagesChecked": 5, "authority": "NONE", "status": "HOLD"}


def build(source_path: Path, art_root: Path, output: Path):
    storyboard = read_json(source_path)
    illustrations = {id: (art_root / f"{id}.svg").read_bytes() for id in EXPECTED}
    parcel = produce(storyboard, illustrations)
    require(not output.exists(), "output exists; refusing overwrite")
    # create-only: never modify an existing edition or parcel
    output.mkdir(parents=True)
    (output / "panels").mkdir()
    for id in EXPECTED:
        (output / image_path(id)).write_bytes(illustrations[id])
    (output / "manifest.json").write_text(json.dumps(parcel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return verify(parcel, output)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    buildp = sub.add_parser("build"); buildp.add_argument("storyboard", type=Path); buildp.add_argument("art_dir", type=Path); buildp.add_argument("output", type=Path)
    verify_p = sub.add_parser("verify"); verify_p.add_argument("manifest", type=Path); verify_p.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        result = build(args.storyboard, args.art_dir, args.output) if args.cmd == "build" else verify(read_json(args.manifest), args.root)
        print(json.dumps(result, indent=2))
    except (ValueError, FileNotFoundError, UnicodeDecodeError) as exc:
        parser.exit(1, f"HOLD: {exc}\n")


if __name__ == "__main__":
    main()
