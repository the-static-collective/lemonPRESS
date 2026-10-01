#!/usr/bin/env python3
"""lemonPRESS Dispatch Gate 001.

Record carrier crossings for a local Recipient Mailer packet.

This tool does not buy postage or contact carriers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "dispatch-gate-001"
ALLOWED_MARKS = {"tendered", "in_transit", "delivered", "returned", "held"}

TRANSITIONS = {
    "service_selected": {"postage_acquired", "held"},
    "postage_acquired": {"tendered", "held"},
    "tendered": {"in_transit", "delivered", "returned", "held"},
    "in_transit": {"delivered", "returned", "held"},
    "delivered": set(),
    "returned": {"held"},
    "held": {"postage_acquired", "tendered", "in_transit", "returned"},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def packet_manifest(packet_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = packet_dir / "manifest.json"
    data = load_json(path)
    if data.get("packet_version") != "recipient-mailer-001":
        raise ValueError("packet is not a Recipient Mailer 001 packet")
    return path, data


def dispatch_path(packet_dir: Path) -> Path:
    return packet_dir / "dispatch.json"


def append_event(
    record: dict[str, Any],
    event: str,
    note: str = "",
    evidence: dict[str, Any] | None = None,
) -> None:
    item: dict[str, Any] = {"event": event, "at_utc": now(), "note": note}
    if evidence:
        item["evidence"] = evidence
    record.setdefault("events", []).append(item)


def transition(record: dict[str, Any], new_state: str) -> None:
    current = str(record.get("state", ""))
    if new_state not in TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid dispatch transition: {current} -> {new_state}")
    record["state"] = new_state


def cmd_init(args: argparse.Namespace) -> int:
    packet_dir = Path(args.packet_dir)
    manifest_path, packet = packet_manifest(packet_dir)

    if packet.get("state") != "printed" and not args.allow_unprinted:
        raise ValueError(
            "packet must be marked printed before Dispatch Gate init; "
            "use --allow-unprinted only for an explicit test or hold"
        )

    out = dispatch_path(packet_dir)
    if out.exists():
        raise ValueError(f"dispatch already exists: {out}")

    record = {
        "dispatch_version": VERSION,
        "packet_id": packet.get("packet_id"),
        "work_id": packet.get("work_id"),
        "edition_id": packet.get("edition_id"),
        "recipient_id": packet.get("recipient_id"),
        "packet_manifest_sha256": sha256_file(manifest_path),
        "carrier_selection": {
            "carrier": args.carrier,
            "service": args.service,
            "state": "human_selected",
            "selected_at_utc": now(),
        },
        "postage": None,
        "state": "service_selected",
        "events": [],
        "privacy": {
            "record_disposition": "local_only",
            "rule": "DELIVERY DATA != PUBLICATION METADATA",
        },
        "law": [
            "LABEL != POSTAGE",
            "POSTAGE != TENDER",
            "TRACKING CREATED != IN TRANSIT",
            "TENDER != DELIVERY",
            "DELIVERED != READ",
        ],
    }
    append_event(record, "service_selected", args.note or "")
    write_json(out, record)
    print(out)
    return 0


def cmd_postage(args: argparse.Namespace) -> int:
    packet_dir = Path(args.packet_dir)
    path = dispatch_path(packet_dir)
    record = load_json(path)
    if record.get("dispatch_version") != VERSION:
        raise ValueError("unexpected dispatch version")

    transition(record, "postage_acquired")

    evidence: dict[str, Any] = {
        "source": args.source,
        "cost_cents": args.cost_cents,
        "currency": args.currency,
        "tracking": args.tracking,
        "transaction_id": args.transaction_id,
    }

    if args.label:
        source = Path(args.label)
        if not source.is_file():
            raise ValueError(f"label not found: {source}")
        target_dir = packet_dir / "private" / "dispatch"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / ("carrier-label" + source.suffix.lower())
        shutil.copy2(source, target)
        evidence["label"] = {
            "path": target.relative_to(packet_dir).as_posix(),
            "bytes": target.stat().st_size,
            "sha256": sha256_file(target),
        }

    record["postage"] = evidence
    append_event(record, "postage_acquired", args.note or "", {"source": args.source})
    write_json(path, record)
    print("postage_acquired")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    packet_dir = Path(args.packet_dir)
    path = dispatch_path(packet_dir)
    record = load_json(path)
    if record.get("dispatch_version") != VERSION:
        raise ValueError("unexpected dispatch version")

    transition(record, args.event)

    evidence: dict[str, Any] = {}
    if args.tracking:
        evidence["tracking"] = args.tracking

    append_event(record, args.event, args.note or "", evidence or None)
    write_json(path, record)
    print(args.event)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    packet_dir = Path(args.packet_dir)
    _, packet = packet_manifest(packet_dir)
    record = load_json(dispatch_path(packet_dir))

    errors: list[str] = []
    if record.get("dispatch_version") != VERSION:
        errors.append("unexpected dispatch_version")
    if record.get("packet_id") != packet.get("packet_id"):
        errors.append("packet_id mismatch")

    postage = record.get("postage")
    if isinstance(postage, dict) and isinstance(postage.get("label"), dict):
        label = postage["label"]
        label_path = packet_dir / label.get("path", "")
        if not label_path.is_file():
            errors.append("missing recorded carrier label")
        else:
            if label_path.stat().st_size != label.get("bytes"):
                errors.append("carrier label byte mismatch")
            if sha256_file(label_path) != label.get("sha256"):
                errors.append("carrier label sha256 mismatch")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="lemonPRESS Dispatch Gate 001")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="select carrier/service for a printed recipient packet")
    init.add_argument("packet_dir")
    init.add_argument("--carrier", required=True)
    init.add_argument("--service", required=True)
    init.add_argument("--note")
    init.add_argument(
        "--allow-unprinted",
        action="store_true",
        help="test/hold escape hatch; does not imply physical readiness",
    )
    init.set_defaults(func=cmd_init)

    postage = sub.add_parser("postage", help="record postage acquired outside this tool")
    postage.add_argument("packet_dir")
    postage.add_argument("--source", required=True)
    postage.add_argument("--cost-cents", type=int)
    postage.add_argument("--currency", default="USD")
    postage.add_argument("--tracking")
    postage.add_argument("--transaction-id")
    postage.add_argument("--label")
    postage.add_argument("--note")
    postage.set_defaults(func=cmd_postage)

    mark = sub.add_parser("mark", help="record a carrier crossing")
    mark.add_argument("packet_dir")
    mark.add_argument("event", choices=sorted(ALLOWED_MARKS))
    mark.add_argument("--tracking")
    mark.add_argument("--note")
    mark.set_defaults(func=cmd_mark)

    check = sub.add_parser("check", help="verify dispatch identity and private artifacts")
    check.add_argument("packet_dir")
    check.set_defaults(func=cmd_check)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
