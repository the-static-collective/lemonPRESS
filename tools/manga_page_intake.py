#!/usr/bin/env python3
"""PAGE INTAKE 001: exact PDF page rasters become bounded Manga Press page carriers."""
from __future__ import annotations

import argparse
import binascii
import copy
import hashlib
import json
import struct
import sys
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

import jsonschema
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press

SPEC_SCHEMA_NAME = "manga-page-intake-v0.schema.json"
CANDIDATE_SCHEMA_NAME = "manga-page-intake-candidate-v0.schema.json"
SPEC_SCHEMA = "lemonpress/manga-page-intake/v0"
CANDIDATE_SCHEMA = "lemonpress/manga-page-intake-candidate/v0"
PNG_ENCODER = "lemonpress-stored-deflate-rgb8-v0"

LAWS = [
    "PDF != PAGE",
    "RENDER != SOURCE",
    "RASTER != EDITION ADMISSION",
    "RENDERER IS PART OF IDENTITY",
    "SCALE IS DECLARED",
    "PIXEL HASH != SEMANTIC IDENTITY",
    "SOURCE BYTES SURVIVE DESCENDANT",
    "SOURCE ADMISSION != PUBLICATION",
    "PAGE CARRIER != HOUSE RELEASE",
    "INTAKE != CANON",
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


def _relative(value: str, label: str) -> Path:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty")
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts and "\\" not in value and path.as_posix() == value,
            f"{label} must be canonical repository-relative POSIX path")
    return path


def _root_path(root: Path, value: str, label: str) -> Path:
    rel = _relative(value, label)
    path = (root / rel).resolve()
    require(path.is_relative_to(root.resolve()), f"{label} escapes root")
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def _adler32(data: bytes) -> int:
    mod = 65521
    a, b = 1, 0
    for offset in range(0, len(data), 5552):
        for value in data[offset:offset + 5552]:
            a = (a + value) % mod
            b = (b + a) % mod
    return (b << 16) | a


def _stored_zlib(data: bytes) -> bytes:
    # Exact zlib stream made only of uncompressed DEFLATE blocks.
    # This avoids PNG-byte identity depending on a platform zlib compressor.
    out = bytearray(b"\x78\x01")
    offset = 0
    while offset < len(data):
        part = data[offset:offset + 65535]
        offset += len(part)
        final = 1 if offset == len(data) else 0
        out.append(final)
        size = len(part)
        out += struct.pack("<H", size)
        out += struct.pack("<H", 0xFFFF - size)
        out += part
    out += struct.pack(">I", _adler32(data))
    return bytes(out)


def _encode_rgb_png(image) -> tuple[bytes, str]:
    image = image.convert("RGB")
    width, height = image.size
    pixels = image.tobytes()
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", _stored_zlib(bytes(raw)))
        + _chunk(b"IEND", b"")
    )
    pixel_sha = _sha256(struct.pack(">II", width, height) + b"RGB8\x00" + pixels)
    return png, pixel_sha


def validate_spec(root: Path, spec: dict[str, Any]) -> Path:
    validate_schema(spec, SPEC_SCHEMA_NAME)
    require(spec["schema"] == SPEC_SCHEMA, f"expected {SPEC_SCHEMA}")
    require(spec["laws"] == LAWS, "v0 law set must match PAGE INTAKE 001 exactly")
    source_path = _root_path(root, spec["source"]["path"], "source.path")
    require(source_path.is_file(), f"missing source PDF: {spec['source']['path']}")
    source_bytes = source_path.read_bytes()
    require(_sha256(source_bytes) == spec["source"]["sha256"], "source PDF SHA-256 mismatch")
    require(spec["source"]["media_type"] == "application/pdf", "v0 accepts PDF only")
    require(spec["renderer"]["engine"] == "pypdfium2", "v0 renderer must be pypdfium2")
    require(spec["renderer"]["version"] == package_version("pypdfium2"),
            f"renderer version mismatch: expected {spec['renderer']['version']}, got {package_version('pypdfium2')}")
    require(spec["renderer"]["pixel_mode"] == "RGB", "v0 pixel mode must be RGB")
    require(spec["renderer"]["png_encoder"] == PNG_ENCODER, f"v0 PNG encoder must be {PNG_ENCODER}")
    require(spec["renderer"]["scale_milli"] > 0, "scale_milli must be positive")
    _relative(spec["bundle_path"], "bundle_path")
    press.geometry(spec["manga"]["geometry"])
    press.grants(spec["admission"]["grants"])
    return source_path


def _render_pages(source_path: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    pdf = pdfium.PdfDocument(str(source_path))
    require(len(pdf) == spec["source"]["page_count"],
            f"page count mismatch: expected {spec['source']['page_count']}, got {len(pdf)}")
    scale = spec["renderer"]["scale_milli"] / 1000.0
    pages = []
    for index in range(len(pdf)):
        image = pdf[index].render(scale=scale).to_pil().convert("RGB")
        png, pixel_sha = _encode_rgb_png(image)
        pages.append({
            "page": index + 1,
            "width": image.width,
            "height": image.height,
            "pixelSha256": pixel_sha,
            "pngSha256": _sha256(png),
            "png": png,
        })
    expected = spec.get("expected_pages")
    if expected is not None:
        require(len(expected) == len(pages), "expected_pages length mismatch")
        for actual, declared in zip(pages, expected):
            require(declared["page"] == actual["page"], "expected page order mismatch")
            require(declared["width"] == actual["width"] and declared["height"] == actual["height"],
                    f"page {actual['page']} raster dimensions changed")
            require(declared["pixel_sha256"] == actual["pixelSha256"],
                    f"page {actual['page']} pixel SHA-256 changed")
            require(declared["png_sha256"] == actual["pngSha256"],
                    f"page {actual['page']} PNG SHA-256 changed")
    return pages


def _binding(relative: str, data: bytes) -> dict[str, str]:
    return {"path": relative, "sha256": _sha256(data)}


def _candidate_hash(candidate: dict[str, Any]) -> str:
    body = copy.deepcopy(candidate)
    body.pop("candidateHash", None)
    return _sha256(press.canonical_bytes(body))


def build(root: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    root = root.resolve()
    source_path = validate_spec(root, spec)
    source_bytes = source_path.read_bytes()
    rendered = _render_pages(source_path, spec)
    bundle = _relative(spec["bundle_path"], "bundle_path").as_posix()

    files: dict[str, bytes] = {}
    source_rel = f"{bundle}/source.pdf"
    files[source_rel] = source_bytes
    source_ref = _binding(source_rel, source_bytes)

    admission = {
        "state": "admitted",
        "work_id": spec["manga"]["work_id"],
        "source_revision": spec["source"]["revision"],
        "source_sha256": spec["source"]["sha256"],
        "authority_ref": spec["admission"]["authority_ref"],
        "scope": spec["admission"]["scope"],
        "grants": copy.deepcopy(spec["admission"]["grants"]),
        "rights_note": spec["admission"]["rights_note"],
    }
    admission_bytes = press.canonical_bytes(admission) + b"\n"
    admission_rel = f"{bundle}/admission.json"
    files[admission_rel] = admission_bytes
    admission_ref = _binding(admission_rel, admission_bytes)

    page_records = []
    prefix = spec["manga"]["page_prefix"]
    for item in rendered:
        number = item["page"]
        image_rel = f"{bundle}/pixels/page-{number:02d}.png"
        files[image_rel] = item["png"]
        image_ref = _binding(image_rel, item["png"])
        page = press.seal("page", {
            "editionId": spec["manga"]["edition_id"],
            "issueId": spec["manga"]["issue_id"],
            "pageId": f"{prefix}-{number:02d}",
            "logicalPageNumber": number,
            "physicalSheetRelation": None,
            "kind": "content",
            "sourceImage": image_ref,
            "geometry": copy.deepcopy(spec["manga"]["geometry"]),
            "panelMap": None,
            "narrativeReferences": [],
            "dialogueCaptionReferences": [],
            "continuityGroupReferences": [],
            "rightsSource": admission_ref,
            "grants": copy.deepcopy(spec["admission"]["grants"]),
            "internalSemantics": "unknown",
            "sourceLineage": [source_ref],
        })
        page_bytes = press.canonical_bytes(page) + b"\n"
        manifest_rel = f"{bundle}/pages/page-{number:02d}.json"
        files[manifest_rel] = page_bytes
        manifest_ref = _binding(manifest_rel, page_bytes)
        page_records.append({
            "page": number,
            "pageId": page["pageId"],
            "pageHash": page["pageHash"],
            "width": item["width"],
            "height": item["height"],
            "pixelSha256": item["pixelSha256"],
            "sourceImage": image_ref,
            "pageManifest": manifest_ref,
        })

    spec_sha = _sha256(press.canonical_bytes(spec))
    seed = {
        "schema": CANDIDATE_SCHEMA,
        "status": "PAGE_CARRIERS",
        "title": spec["title"],
        "intakeId": spec["id"],
        "specSha256": spec_sha,
        "source": source_ref,
        "sourcePdfSha256": spec["source"]["sha256"],
        "renderer": copy.deepcopy(spec["renderer"]),
        "admission": admission_ref,
        "pageCount": len(page_records),
        "pages": page_records,
        "authority": {
            "sourceAdmission": True,
            "editionAdmission": False,
            "editorialSelection": False,
            "publication": False,
            "houseRelease": False,
        },
        "wrench": {
            "INPUT": {
                "sourcePdfSha256": spec["source"]["sha256"],
                "pageCount": spec["source"]["page_count"],
                "renderer": copy.deepcopy(spec["renderer"]),
            },
            "TRANSFORMATION": "exact declared PDF rasterization to separately hashed whole-page RGB carriers",
            "OUTPUT": {
                "pageIds": [p["pageId"] for p in page_records],
                "pageHashes": [p["pageHash"] for p in page_records],
                "pixelSha256": [p["pixelSha256"] for p in page_records],
            },
            "RESIDUAL": [
                "Exact source PDF bytes are copied unchanged into the portable intake bundle.",
                "No panel, dialogue, character, or narrative semantics are inferred by raster intake.",
            ],
            "LOSS": [
                "PDF vector/text structure is not carried into raster page pixels.",
                "Page carriers encode the declared PDFium rendering at one declared scale, not every possible rendering.",
            ],
            "UNKNOWN": [
                "Edition placement and cover relationships.",
                "Final lettering boxes.",
                "Editorial selection, publication, and house release.",
            ],
            "STOP": "Whole-page Manga Press carriers only. Explicit later edition admission remains required.",
        },
        "laws": copy.deepcopy(spec["laws"]),
    }
    candidate_id = "manga-page-intake:" + _sha256(press.canonical_bytes({
        "specSha256": spec_sha,
        "sourcePdfSha256": spec["source"]["sha256"],
        "renderer": spec["renderer"],
        "pages": [{"pageHash": p["pageHash"], "pixelSha256": p["pixelSha256"]} for p in page_records],
    }))
    candidate = {**seed, "candidateId": candidate_id}
    candidate["candidateHash"] = _candidate_hash(candidate)
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)

    intake_bytes = press.canonical_bytes(candidate) + b"\n"
    files[f"{bundle}/intake.json"] = intake_bytes
    files[f"{bundle}/RECEIPT.md"] = receipt(candidate).encode("utf-8")
    return candidate, files


def verify_candidate(candidate: dict[str, Any]) -> None:
    validate_schema(candidate, CANDIDATE_SCHEMA_NAME)
    require(candidate["candidateHash"] == _candidate_hash(candidate), "candidate hash mismatch")
    require(candidate["laws"] == LAWS, "candidate law set mismatch")
    for page in candidate["pages"]:
        press.digest(page["pageHash"])
        press.digest(page["pixelSha256"])


def receipt(candidate: dict[str, Any]) -> str:
    lines = [
        f"# {candidate['intakeId']} - PAGE INTAKE 001 receipt",
        "",
        f"Status: {candidate['status']}",
        f"Candidate: {candidate['candidateId']}",
        f"Source PDF SHA-256: {candidate['sourcePdfSha256']}",
        f"Renderer: {candidate['renderer']['engine']} {candidate['renderer']['version']}",
        f"Scale: {candidate['renderer']['scale_milli']} / 1000",
        f"PNG encoder: {candidate['renderer']['png_encoder']}",
        "",
        "## Pages",
        "",
        "| page | page id | page hash | pixel sha256 | PNG sha256 |",
        "|---:|---|---|---|---|",
    ]
    for page in candidate["pages"]:
        lines.append(
            f"| {page['page']} | {page['pageId']} | {page['pageHash']} | "
            f"{page['pixelSha256']} | {page['sourceImage']['sha256']} |"
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


def write_bundle(root: Path, files: dict[str, bytes]) -> None:
    root = root.resolve()
    for relative, data in files.items():
        path = _root_path(root, relative, "bundle output")
        _write_create_only(path, data)


def verify_bundle(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    expected, files = build(root, spec)
    for relative, data in files.items():
        path = _root_path(root, relative, "bundle output")
        require(path.is_file(), f"missing output: {relative}")
        require(path.read_bytes() == data, f"output does not deterministically rebuild: {relative}")
    bundle = _relative(spec["bundle_path"], "bundle_path").as_posix()
    actual = press.read_json(_root_path(root, f"{bundle}/intake.json", "intake record"))
    verify_candidate(actual)
    require(press.canonical_bytes(actual) == press.canonical_bytes(expected), "intake.json differs from rebuild")
    for page in actual["pages"]:
        manifest = press.bound_json(root, page["pageManifest"])
        press.verify("page", manifest)
        press.bound_path(root, page["sourceImage"])
    return expected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="PAGE INTAKE 001")
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("compose", "verify"):
        p = sub.add_parser(name)
        p.add_argument("spec")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    spec_path = _root_path(root, args.spec, "spec")
    spec = press.read_json(spec_path)
    if args.command == "compose":
        candidate, files = build(root, spec)
        write_bundle(root, files)
        print(json.dumps({
            "ok": True,
            "candidateId": candidate["candidateId"],
            "pageCount": candidate["pageCount"],
            "sourcePdfSha256": candidate["sourcePdfSha256"],
        }, indent=2))
        return 0

    candidate = verify_bundle(root, spec)
    print(json.dumps({
        "ok": True,
        "candidateId": candidate["candidateId"],
        "pageCount": candidate["pageCount"],
        "verified": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"manga page intake failure: {exc}", file=sys.stderr)
        raise SystemExit(2)
