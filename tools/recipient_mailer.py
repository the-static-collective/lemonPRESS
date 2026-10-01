#!/usr/bin/env python3
"""lemonPRESS Recipient Mailer 001.

Prepare a local, inspectable mail packet from an already-selected physical edition.

This tool packages; it does not authorize publication, purchase postage, or mail anything.
Postal addresses are delivery data and should not be committed to the public repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "recipient-mailer-001"
EVENTS = {"prepared", "printed", "held"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "recipient"


def validate_job(job: dict[str, Any]) -> None:
    required = ("work_id", "edition_id", "title", "source_artifact", "recipient", "cover_note")
    missing = [key for key in required if not job.get(key)]
    if missing:
        raise ValueError("job missing: " + ", ".join(missing))

    recipient = job.get("recipient")
    if not isinstance(recipient, dict):
        raise ValueError("recipient must be an object")
    for key in ("recipient_id", "display_name", "address_lines"):
        if not recipient.get(key):
            raise ValueError(f"recipient missing: {key}")
    lines = recipient.get("address_lines")
    if not isinstance(lines, list) or not all(isinstance(x, str) and x.strip() for x in lines):
        raise ValueError("recipient.address_lines must be a non-empty array of non-empty strings")

    note = job.get("cover_note")
    if not isinstance(note, dict) or not str(note.get("body", "")).strip():
        raise ValueError("cover_note.body is required")

    privacy = job.get("privacy", {})
    if privacy and privacy.get("address_disposition") not in {None, "local_only"}:
        raise ValueError("Recipient Mailer 001 only supports privacy.address_disposition=local_only")


def pdf_escape(value: str) -> str:
    try:
        raw = value.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "PDF renderer encountered a character outside WinAnsi/CP1252; "
            "use ASCII/Western punctuation or replace it explicitly"
        ) from exc
    return raw.decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_text_pdf(
    path: Path,
    lines: list[str],
    *,
    width: int,
    height: int,
    margin: int,
    font_size: int,
    leading: int,
) -> None:
    """Write a minimal one-page PDF using only the Python standard library."""
    content_parts = ["BT", f"/F1 {font_size} Tf", f"{margin} {height - margin} Td"]
    first = True
    for line in lines:
        if not first:
            content_parts.append(f"0 -{leading} Td")
        content_parts.append(f"({pdf_escape(line)}) Tj")
        first = False
    content_parts.append("ET")
    stream = "\n".join(content_parts).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode(),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(out)


def wrap_paragraphs(body: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in body.splitlines():
        paragraph = paragraph.rstrip()
        if not paragraph:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width, break_long_words=False, break_on_hyphens=False) or [""])
    return lines


def recipient_fingerprint(recipient: dict[str, Any]) -> str:
    private = {
        "recipient_id": recipient.get("recipient_id"),
        "display_name": recipient.get("display_name"),
        "attention": recipient.get("attention"),
        "address_lines": recipient.get("address_lines"),
    }
    payload = json.dumps(private, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def artifact_record(role: str, path: Path, root: Path) -> dict[str, Any]:
    return {
        "role": role,
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def zip_packet(packet_dir: Path) -> Path:
    zip_path = packet_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(packet_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(packet_dir.parent))
    return zip_path


def build_packet(job_path: Path, out_dir: Path) -> Path:
    job = load_json(job_path)
    validate_job(job)

    source = Path(job["source_artifact"]).expanduser()
    if not source.is_absolute():
        source = (job_path.parent / source).resolve()
    if not source.is_file():
        raise ValueError(f"source artifact not found: {source}")

    recipient = job["recipient"]
    cover = job["cover_note"]
    packet_id = str(job.get("packet_id") or f"{slugify(job['edition_id'])}--{slugify(recipient['recipient_id'])}")

    out_dir.mkdir(parents=True, exist_ok=False)
    artifacts = out_dir / "artifacts"
    artifacts.mkdir()
    private = out_dir / "private"
    private.mkdir()

    book_name = "book" + source.suffix.lower()
    book_path = artifacts / book_name
    shutil.copy2(source, book_path)

    note_lines = []
    note_title = str(cover.get("heading") or f"A copy for {recipient['display_name']}")
    note_lines.extend(textwrap.wrap(note_title, width=64))
    note_lines.append("")
    note_lines.extend(wrap_paragraphs(str(cover["body"]), width=82))
    signoff = str(cover.get("signoff", "")).strip()
    if signoff:
        note_lines.extend(["", signoff])

    if len(note_lines) > 48:
        raise ValueError("cover note exceeds one-page renderer capacity; shorten it rather than silently truncating")
    cover_pdf = artifacts / "cover-note.pdf"
    make_text_pdf(cover_pdf, note_lines, width=612, height=792, margin=54, font_size=11, leading=15)

    label_lines = [recipient["display_name"]]
    attention = str(recipient.get("attention", "")).strip()
    if attention:
        label_lines.append(attention)
    label_lines.extend(recipient["address_lines"])
    label_pdf = artifacts / "mailing-label-4x6.pdf"
    make_text_pdf(label_pdf, label_lines, width=288, height=432, margin=36, font_size=14, leading=24)

    write_json(private / "delivery.json", {"recipient": recipient})

    manifest = {
        "packet_version": VERSION,
        "packet_id": packet_id,
        "work_id": job["work_id"],
        "edition_id": job["edition_id"],
        "title": job["title"],
        "recipient_id": recipient["recipient_id"],
        "recipient_display_name": recipient["display_name"],
        "recipient_fingerprint_sha256": recipient_fingerprint(recipient),
        "privacy": {
            "address_disposition": "local_only",
            "rule": "DELIVERY DATA != PUBLICATION METADATA",
        },
        "state": "prepared",
        "artifacts": [],
        "events": [],
        "law": [
            "MASTER != RECIPIENT COPY",
            "RECIPIENT != MARKET SEGMENT",
            "DELIVERY DATA != PUBLICATION METADATA",
            "PREPARED != PRINTED",
            "PRINTED != DISPATCHED",
        ],
    }

    manifest["artifacts"] = [
        artifact_record("book", book_path, out_dir),
        artifact_record("cover_note", cover_pdf, out_dir),
        artifact_record("mailing_label", label_pdf, out_dir),
    ]
    write_json(out_dir / "manifest.json", manifest)

    readme = f"""# lemonPRESS recipient mail packet

Packet: `{packet_id}`

Work: `{job['work_id']}`
Edition: `{job['edition_id']}`
Recipient: `{recipient['display_name']}`

This directory is a local fulfillment packet.

**Do not commit this directory to a public repository.** The mailing-label artifact contains delivery data.

Laws:

- MASTER != RECIPIENT COPY
- RECIPIENT != MARKET SEGMENT
- DELIVERY DATA != PUBLICATION METADATA
- PREPARED != PRINTED
- PRINTED != DISPATCHED

Structured address data lives only in `private/delivery.json` inside this local packet. The manifest intentionally stores a fingerprint of that private recipient block rather than the street address itself.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    return zip_packet(out_dir)


def check_packet(packet_dir: Path) -> list[str]:
    manifest_path = packet_dir / "manifest.json"
    if not manifest_path.is_file():
        return ["missing manifest.json"]
    manifest = load_json(manifest_path)
    errors: list[str] = []
    if manifest.get("packet_version") != VERSION:
        errors.append(f"unexpected packet_version: {manifest.get('packet_version')}")
    for artifact in manifest.get("artifacts", []):
        path = packet_dir / artifact["path"]
        if not path.is_file():
            errors.append(f"missing artifact: {artifact['path']}")
            continue
        if path.stat().st_size != artifact.get("bytes"):
            errors.append(f"byte mismatch: {artifact['path']}")
        if sha256_file(path) != artifact.get("sha256"):
            errors.append(f"sha256 mismatch: {artifact['path']}")
    return errors


def mark_event(packet_dir: Path, event: str, note: str | None) -> None:
    if event not in EVENTS:
        raise ValueError("event must be one of: " + ", ".join(sorted(EVENTS)))
    manifest_path = packet_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("events", []).append(
        {
            "event": event,
            "at_utc": datetime.now(timezone.utc).isoformat(),
            "note": note or "",
        }
    )
    manifest["state"] = event
    write_json(manifest_path, manifest)
    if packet_dir.with_suffix(".zip").exists():
        zip_packet(packet_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="lemonPRESS Recipient Mailer 001")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="prepare a local recipient mail packet")
    prepare.add_argument("job")
    prepare.add_argument("--out", required=True)

    check = sub.add_parser("check", help="verify packet artifact hashes")
    check.add_argument("packet_dir")

    mark = sub.add_parser("mark", help="record a fulfillment event")
    mark.add_argument("packet_dir")
    mark.add_argument("event", choices=sorted(EVENTS))
    mark.add_argument("--note")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "prepare":
            zip_path = build_packet(Path(args.job), Path(args.out))
            print(zip_path)
            return 0
        if args.command == "check":
            errors = check_packet(Path(args.packet_dir))
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print("OK")
            return 0
        if args.command == "mark":
            mark_event(Path(args.packet_dir), args.event, args.note)
            print(args.event)
            return 0
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
