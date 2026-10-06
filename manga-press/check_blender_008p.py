#!/usr/bin/env python3
"""Read-only compatibility probe: source construction, never staging or harvest."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as m

BLENDER_SHA = "4e3f098d328a9659d9074852ef7861b7d3078fee"
EDITION = "works/manga-press-specimen/manga/001"


def check(blender_root):
    actual = subprocess.check_output(["git", "-C", str(blender_root), "rev-parse", "HEAD"], text=True).strip()
    m.require(actual == BLENDER_SHA, "compatibility probe requires inspected 008p commit")
    sys.path.insert(0, str(blender_root))
    from haunted_blender import manga_atlas, narrative_performance

    edition = m.read_json(ROOT / EDITION / "edition.yaml")
    handoff = m.read_json(ROOT / EDITION / "blender-compatibility-handoff.json")
    m.verify_handoff(ROOT, edition, handoff)
    page = handoff["pages"][0]
    source = m.bound_json(ROOT, page["narrativeReferences"][0])
    # This is just the future adapter's source vocabulary. It does not choose
    # shots, beats, timing, crops, sound, or editorial admission.
    locator = {"provider": "lemonpress", "publicationPage": page["identity"],
               "sourceEvidence": page["narrativeReferences"], "dialogueCaptionEvidence": page["dialogueCaptionReferences"],
               "handoffHash": handoff["handoffHash"]}
    narrative = narrative_performance.particular_source(
        label=source["label"], source_locator=locator, particulars=source["particulars"])
    m.require(narrative["sourceLocator"]["publicationPage"] == page["identity"], "narrative source lost ancestry")
    m.require(narrative["authority"] == "source-witness-only", "source construction expanded authority")

    # Blender 008m's pixelReuse door enables harvest. The narrower LemonPRESS
    # pixelHarvest door must therefore also be true before forwarding that bit.
    reuse = handoff["grants"]
    quarry_permission = reuse["pixelReuse"] and reuse["pixelHarvest"]
    atlas_source = manga_atlas.source_manifest(m.bound_path(ROOT, page["sourceImage"]), source_class="owned",
        pixel_reuse=quarry_permission, derivative_reuse=reuse["derivativeReuse"], publication_reuse=reuse["publicationReuse"],
        rights_note="Locally generated synthetic fixture only; no real Bus page or house release claimed.", label="Manga Press synthetic page",
        sequence_index=4)
    m.require(atlas_source["sourceSha256"] == page["identity"]["sourceImageSha256"], "page source lost exact pixel identity")
    m.require(not atlas_source["rights"]["pixelReuse"], "specimen's closed harvest door expanded")
    return {"kind": "manga-press-001/blender-008p-source-compatibility-witness", "blenderCommit": actual,
        "handoffHash": handoff["handoffHash"], "publicationPage": page["identity"],
        "narrativeSourceId": narrative["id"], "narrativeSourceSchema": narrative["schema"],
        "sourceLocator": narrative["sourceLocator"], "pageSourceSchema": atlas_source["schema"],
        "sourceImageSha256": atlas_source["sourceSha256"], "pixelDimensions": [atlas_source["width"], atlas_source["height"]],
        "forwardedQuarryRights": atlas_source["rights"],
        "notPerformed": ["page harvest", "staging proposal", "editorial admission", "performance plan", "sound synthesis", "render", "publication"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender-root", required=True, type=Path)
    parser.add_argument("--write-witness", action="store_true")
    args = parser.parse_args()
    witness = check(args.blender_root.resolve())
    path = ROOT / EDITION / "blender-compatibility-witness.json"
    if args.write_witness:
        m.persist_records(path.parent, {path.name: witness})
    else:
        m.require(path.read_bytes() == m.canonical_bytes(witness), "compatibility witness changed")
    print("BLENDER 008p SOURCE COMPATIBILITY: PASS (no harvest, staging, admission, or render)")
