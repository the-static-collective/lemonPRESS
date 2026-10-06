#!/usr/bin/env python3
"""Rebuild only the openly synthetic, local Manga Press 001 test specimen."""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as manga

BASE = "works/manga-press-specimen"
EDITION = BASE + "/manga/001"


def write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(manga.canonical_bytes(value))
    return {"path": relative, "sha256": manga.sha256_file(path)[0]}


def png(index):
    # Exact whole-page pixels; rectangles carry no asserted panel/character meaning.
    width, height = 64, 96
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            value = 255 if x < 5 or y < 5 or x >= 59 or y >= 91 else (32 + 19 * index if x % 21 == 0 or y % 29 == 0 else 240)
            raw.extend((value, value, value))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def build(root=ROOT):
    work_id = "lemonpress:manga-press-synthetic-001"
    edition_id, issue_id = work_id + ":manga-001", work_id + ":issue-001"
    permissions = {k: k in ("pixelReuse", "derivativeReuse", "motionAdaptation") for k in manga.GRANTS}
    source = write(root, BASE + "/source-001.json", {
        "kind": "synthetic-narrative-source", "label": "A test page with a pictured bell",
        "particulars": [{"id": "bell-001", "kind": "visible-sound-source", "text": "A bell hangs beside a rectangular window.", "observable": True}],
        "dialogueCaptions": [{"id": "caption-001", "text": "A test page you could hear."}],
        "note": "Synthetic interface evidence. Not The Bus That Joined the Band; no character or real-source facts claimed."})
    admission = write(root, BASE + "/admission-001.json", {
        "state": "admitted", "work_id": work_id, "source_revision": "synthetic-source-001",
        "source_sha256": source["sha256"], "authority_ref": "fixture-declaration:manga-press-001",
        "scope": "synthetic test only; no real work, release, editorial, or renderer admission",
        "grants": permissions, "rights_note": "Locally generated synthetic fixture bytes; these narrow test doors are explicitly declared, not inherited from a real source."})
    work = write(root, BASE + "/work.yaml", {"work_id": work_id, "title": "Manga Press synthetic specimen", "status": "admitted",
        "admission": {"state": "admitted", "receipt": admission["path"], "source_revision": "synthetic-source-001"},
        "lanes": ["physical", "digital", "archive"], "rights": "Synthetic test fixture only; no house release or general publication grant.",
        "relations": [{"type": "synthetic-interface-specimen", "target": "manga-press-001"}]})
    selection = write(root, EDITION + "/selection.json", {"work_id": work_id, "state": "external_fixed",
        "authority_ref": "fixture-declaration:manga-press-001:unbound-leaf-proof", "production": {"format": "unbound-proof"},
        "note": "Externally fixed test constraints, not a Physical Composer recommendation selected by this tool."})
    geo = {"unit": "um", "page": {"x": 0, "y": 0, "width": 126000, "height": 186000},
           "trim": {"x": 3000, "y": 3000, "width": 120000, "height": 180000},
           "bleed": {"left": 3000, "right": 3000, "top": 3000, "bottom": 3000},
           "safeArea": {"x": 8000, "y": 8000, "width": 110000, "height": 170000}}
    refs, pages = [], []
    for number in range(1, 9):
        image = None
        if number != 6:
            relative = EDITION + f"/pixels/page-{number:02}.png"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png(number))
            image = {"path": relative, "sha256": manga.sha256_file(path)[0]}
        page = manga.seal("page", {"editionId": edition_id, "issueId": issue_id, "pageId": f"page-{number:02}",
            "logicalPageNumber": number - 2 if number in (3, 4, 5) else None,
            "physicalSheetRelation": None, "kind": "intentional-blank" if number == 6 else "content",
            "sourceImage": image, "geometry": geo, "panelMap": None, "internalSemantics": "unknown",
            "narrativeReferences": [source] if number == 5 else [], "dialogueCaptionReferences": [source] if number == 5 else [],
            "continuityGroupReferences": [], "rightsSource": admission, "grants": permissions, "sourceLineage": [source]})
        pages.append(page)
        refs.append(write(root, EDITION + f"/pages/page-{number:02}.json", page))
    edition = manga.seal("edition", {"workId": work_id, "workManifest": work, "source": source, "admission": admission,
        "editionId": edition_id, "title": "Manga Press 001 — synthetic issue", "issueId": issue_id, "issueSequence": 1,
        "readingDirection": "ltr", "geometry": geo, "colorIntent": "grayscale", "pageCount": 8,
        "covers": {"front": "place-01", "insideFront": "place-02", "insideBack": "place-07", "back": "place-08"},
        "pageOrdering": [{"placementId": f"place-{n:02}", "pageId": f"page-{n:02}", "repeatOf": None} for n in range(1, 9)],
        "spreads": [{"spreadId": "spread-001", "placements": ["place-04", "place-05"]}],
        "sourceLineage": [source], "pageManifests": refs, "printIntent": {"selection": selection, "sheetLayout": "one-leaf-two-sides", "requiredBlanks": ["place-06"]},
        "digitalIntent": {"mode": "page-sequence", "publicationAuthority": "none"},
        "performanceHandoffPolicy": {"grants": permissions, "allowedAdaptationScope": ["pictured-source test staging proposals; motion requires independent editorial admission"], "externalEditorialAuthorityReference": None},
        "rightsReferences": [admission], "grants": permissions})
    edition_admission = write(root, EDITION + "/admission-001.json", {"state": "admitted", "work_id": work_id,
        "edition_id": edition_id, "issue_id": issue_id, "authority_ref": "fixture-declaration:manga-press-001:edition",
        "declaration_sha256": manga.edition_declaration_hash(edition), "admitted_page_hashes": [p["pageHash"] for p in pages],
        "scope": "Exact synthetic declaration only; no publication or performance admission."})
    edition["editionAdmission"] = edition_admission
    edition = manga.seal("edition", edition)
    write(root, EDITION + "/edition.yaml", edition)
    bundle = manga.compose(root, edition)
    _, placements = manga.validate_edition(root, edition)
    handoff = manga.make_handoff(edition, {p["pageId"]: p for p in bundle["pages"]}, placements, ["page-05"])
    write(root, EDITION + "/blender-compatibility-handoff.json", handoff)
    return edition


if __name__ == "__main__":
    build()
