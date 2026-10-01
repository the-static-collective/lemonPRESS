#!/usr/bin/env python3
"""lemonPRESS Press Gate 001.

Dependency-free tooling for creating, hashing, and checking physical-edition
packets. This verifies production identity and file integrity. It does not
perform visual QA and does not authorize publication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

PACKET_VERSION = "press-gate-001"
REQUIRED_FILES = ("manifest.json", "SPEC.md", "PRINT-RECEIPT.md", "BACKMATTER.md")
ALLOWED_STATES = {
    "scaffold", "preflight", "proof_candidate", "approved_print_proof",
    "released_physical_edition", "held", "rejected",
}


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_manifest(packet: Path) -> dict[str, Any]:
    path = packet / "manifest.json"
    if not path.exists():
        raise ValueError(f"missing {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest.json must contain one JSON object")
    return data


def save_manifest(packet: Path, manifest: dict[str, Any]) -> None:
    (packet / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cmd_new(args: argparse.Namespace) -> int:
    packet = Path(args.out)
    if packet.exists() and any(packet.iterdir()):
        print(f"refusing to scaffold non-empty directory: {packet}", file=sys.stderr)
        return 2

    packet.mkdir(parents=True, exist_ok=True)
    (packet / "artifacts").mkdir(exist_ok=True)

    manifest = {
        "packet_version": PACKET_VERSION,
        "work_id": args.work_id,
        "edition_id": args.edition_id,
        "lane": "physical",
        "state": "scaffold",
        "title": args.title,
        "source_revision": args.source_revision,
        "admission_receipt": args.admission_receipt,
        "production": {
            "format": args.format,
            "trim_inches": None,
            "binding": None,
            "paper": None,
            "color": None,
            "pages": None,
            "held_decisions": [
                "trim", "binding", "paper", "color", "page count", "printer/vendor"
            ],
        },
        "artifacts": [],
        "qa": {"status": "not_run", "receipt": "PRINT-RECEIPT.md", "notes": []},
        "publication": {
            "house_status": "not_yet_declared_published",
            "note": "PROOF != PUBLICATION",
        },
        "rights": args.rights,
    }
    save_manifest(packet, manifest)

    write_text(packet / "SPEC.md", f"""# Physical specification — {args.title}

**Edition:** {args.edition_id}
**Gate state:** scaffold

## Selected

- format: {args.format}

## Held

- trim
- binding
- paper
- color process
- page count
- printer/vendor
- cover construction
- bleed strategy
- special fabrication

## Material intent

Describe what the physical carrier should do that the digital carrier cannot.

## Accessibility

Record relevant type size, contrast, paper glare, handling, weight, navigation, or alternate-format considerations.

RECOMMENDATION != SELECTION
""")

    write_text(packet / "PRINT-RECEIPT.md", f"""# Print receipt — {args.title}

**Edition:** {args.edition_id}

INPUT
: {args.work_id} / {args.source_revision}

TRANSFORMATION
: scaffolded a Press Gate 001 packet; no print artifact has crossed yet.

OUTPUT
: manifest, physical specification, receipt, backmatter carrier, and artifact directory.

RESIDUAL
: production decisions remain held.

LOSS
: none claimed at scaffold stage.

UNKNOWN
: trim, binding, paper, page count, printer/vendor, cover construction, visual QA.

STOP
: before claiming a proof exists.

## QA

No visual QA has been performed yet.

PROOF != PUBLICATION
""")

    write_text(packet / "BACKMATTER.md", f"""# Edition backmatter — {args.title}

lemonPRESS physical edition

Edition ID: {args.edition_id}
Work ID: {args.work_id}
Upstream source: {args.source_revision}
Admission receipt: {args.admission_receipt}

Physical production may alter pagination, typography, dimensions, sequencing furniture, and material behavior without changing the admitted source.

Rights: {args.rights}

PHYSICAL FORM != SOURCE AUTHORITY
""")

    print(packet)
    return 0


def cmd_add_artifact(args: argparse.Namespace) -> int:
    packet = Path(args.packet)
    src = Path(args.file)
    if not src.is_file():
        print(f"artifact does not exist: {src}", file=sys.stderr)
        return 2

    try:
        manifest = load_manifest(packet)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    artifacts_dir = packet / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    dest = artifacts_dir / (args.name or src.name)

    if dest.exists() and not args.replace:
        print(f"artifact already exists: {dest}; use --replace", file=sys.stderr)
        return 2

    shutil.copy2(src, dest)
    digest, size = sha256_file(dest)
    rel = dest.relative_to(packet).as_posix()
    entry = {"role": args.role, "path": rel, "bytes": size, "sha256": digest}

    kept = [
        item for item in manifest.get("artifacts", [])
        if isinstance(item, dict) and item.get("path") != rel
    ]
    kept.append(entry)
    manifest["artifacts"] = kept
    if manifest.get("state") == "scaffold":
        manifest["state"] = "preflight"
    save_manifest(packet, manifest)

    print(json.dumps(entry, indent=2))
    return 0


def check_manifest_shape(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "packet_version", "work_id", "edition_id", "lane", "state", "title",
        "source_revision", "admission_receipt", "production", "artifacts",
        "publication", "rights",
    )
    for key in required:
        if key not in manifest:
            errors.append(f"manifest missing key: {key}")

    if manifest.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet_version must be {PACKET_VERSION}")
    if manifest.get("lane") != "physical":
        errors.append("lane must be physical")
    if manifest.get("state") not in ALLOWED_STATES:
        errors.append(f"unknown gate state: {manifest.get('state')!r}")
    if not isinstance(manifest.get("production"), dict):
        errors.append("production must be an object")
    if not isinstance(manifest.get("artifacts"), list):
        errors.append("artifacts must be an array")
    if not isinstance(manifest.get("publication"), dict):
        errors.append("publication must be an object")
    return errors


def cmd_check(args: argparse.Namespace) -> int:
    packet = Path(args.packet)
    errors: list[str] = []
    warnings: list[str] = []

    if not packet.is_dir():
        print(f"packet directory does not exist: {packet}", file=sys.stderr)
        return 2

    for name in REQUIRED_FILES:
        if not (packet / name).is_file():
            errors.append(f"missing required file: {name}")

    try:
        manifest = load_manifest(packet)
    except ValueError as exc:
        errors.append(str(exc))
        manifest = {}

    if manifest:
        errors.extend(check_manifest_shape(manifest))

        for index, artifact in enumerate(manifest.get("artifacts", [])):
            if not isinstance(artifact, dict):
                errors.append(f"artifact[{index}] must be an object")
                continue
            for key in ("role", "path", "bytes", "sha256"):
                if key not in artifact:
                    errors.append(f"artifact[{index}] missing key: {key}")

            rel = artifact.get("path")
            if not isinstance(rel, str):
                continue

            path = packet / rel
            try:
                path.resolve().relative_to(packet.resolve())
            except ValueError:
                errors.append(f"artifact[{index}] escapes packet directory: {rel}")
                continue

            if not path.is_file():
                errors.append(f"artifact[{index}] missing file: {rel}")
                continue

            digest, size = sha256_file(path)
            if artifact.get("sha256") != digest:
                errors.append(f"artifact[{index}] SHA-256 mismatch: {rel}")
            if artifact.get("bytes") != size:
                errors.append(f"artifact[{index}] byte-count mismatch: {rel}")

            if path.suffix.lower() == ".pdf":
                with path.open("rb") as stream:
                    if stream.read(5) != b"%PDF-":
                        errors.append(
                            f"artifact[{index}] has .pdf suffix but no PDF signature: {rel}"
                        )

        publication = manifest.get("publication", {})
        if isinstance(publication, dict):
            status = publication.get("house_status")
            if manifest.get("state") == "released_physical_edition" and status in (
                None, "", "not_yet_declared_published"
            ):
                errors.append(
                    "released_physical_edition requires explicit published house_status"
                )

        qa = manifest.get("qa", {})
        if manifest.get("state") == "approved_print_proof":
            if not isinstance(qa, dict) or qa.get("status") in (None, "", "not_run"):
                errors.append("approved_print_proof requires a non-empty QA status")
            if not manifest.get("artifacts"):
                errors.append("approved_print_proof requires at least one hashed artifact")

        production = manifest.get("production", {})
        if isinstance(production, dict) and production.get("held_decisions"):
            warnings.append(
                "held production decisions remain: "
                + ", ".join(map(str, production.get("held_decisions", [])))
            )

    if errors:
        print("PRESS GATE: FAIL")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
        return 1

    print("PRESS GATE: PASS")
    for item in warnings:
        print(f"WARN: {item}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="lemonPRESS Press Gate 001")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="scaffold a physical-edition packet")
    new.add_argument("--work-id", required=True)
    new.add_argument("--edition-id", required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--source-revision", required=True)
    new.add_argument("--admission-receipt", required=True)
    new.add_argument("--out", required=True)
    new.add_argument("--format", default="book")
    new.add_argument(
        "--rights",
        default=(
            "All rights reserved by the respective rightsholders unless otherwise "
            "stated; repository publication grants no additional license."
        ),
    )
    new.set_defaults(func=cmd_new)

    add = sub.add_parser("add-artifact", help="copy and hash an artifact into a packet")
    add.add_argument("packet")
    add.add_argument("file")
    add.add_argument("role")
    add.add_argument("--name")
    add.add_argument("--replace", action="store_true")
    add.set_defaults(func=cmd_add_artifact)

    check = sub.add_parser("check", help="verify packet structure and artifact integrity")
    check.add_argument("packet")
    check.set_defaults(func=cmd_check)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
