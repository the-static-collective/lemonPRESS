#!/usr/bin/env python3
"""lemonPRESS LETTER CYCLE 001.

Proof an addressable letter, branching index card and return slip.
Record a private reply, explicit human editorial review, and an
unpublished next-issue candidate. No print, delivery or audience claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from recipient_mailer import make_text_pdf, wrap_paragraphs

VERSION = "letter-cycle-001"
REPO = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read JSON: " + str(path)) from exc
    if not isinstance(obj, dict):
        raise ValueError("expected a JSON object: " + str(path))
    return obj


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def private_output(path: Path) -> None:
    target = path.resolve()
    if target == REPO or REPO in target.parents:
        raise ValueError("private cycle data must be stored outside the public repository")


def new_directory(path: Path) -> None:
    if path.exists():
        raise ValueError("output already exists: " + str(path))
    path.mkdir(parents=True)


def limit_lines(lines: list[str], *, width: int, height: int, margin: int, leading: int) -> list[str]:
    max_lines = 1 + (height - 2 * margin) // leading
    if len(lines) > max_lines:
        raise ValueError("page would overflow; edit the issue rather than truncate it")
    return lines


def issue_lines(issue: dict[str, Any]) -> list[str]:
    letter = issue["letter"]
    lines = ["THE STATIC LETTER / PROOF ONLY", issue["issue_id"], "", str(letter["title"]), ""]
    lines.extend(wrap_paragraphs(str(letter["body"]), width=86))
    lines.extend(["", "SOURCE ROAD / POINTERS, NOT REPRINTS"])
    for src in issue["sources"]:
        lines.extend(textwrap.wrap(str(src["label"]) + ": " + str(src["locus"]), width=86, break_long_words=False))
    lines.extend(["", "NOT RELEASED. No subscription or delivery is claimed."])
    return limit_lines(lines, width=612, height=792, margin=50, leading=15)


def card_lines(issue: dict[str, Any]) -> list[str]:
    card = issue["card"]
    lines = ["AN INDEX CARD THAT CAN BRANCH", "", "Address: " + card["address"],
             "Parent: " + card["parent"], ""]
    lines.extend(wrap_paragraphs(card["claim"], width=48))
    lines.extend(["", "Try this branch:", card["branch_address"]])
    lines.extend(wrap_paragraphs(card["branch_question"], width=48))
    lines.extend(["", "Locator != authority. Keep the source."])
    return limit_lines(lines, width=432, height=288, margin=22, leading=13)


def return_lines(issue: dict[str, Any]) -> list[str]:
    return [
        "THE STATIC LETTER / RETURN SLIP",
        "Reply to: " + issue["issue_id"], "",
        "What did this change or make you notice?",
        "________________________________________",
        "________________________________________",
        "________________________________________",
        "________________________________________", "",
        "[ ] Private only (default)",
        "[ ] May quote my words in future work",
        "[ ] May credit me by name",
        "Name (optional): ______________________", "",
        "No reply is public by default.",
        "Keep this slip or use an agreed channel.",
    ]


def cmd_proof(args: argparse.Namespace) -> None:
    issue = read_json(Path(args.issue))
    if issue.get("cycle_version") != VERSION or issue.get("state") != "candidate":
        raise ValueError("issue must be a letter-cycle-001 candidate")
    if not re.fullmatch(r"LP-LTR-[0-9]{3}", str(issue.get("issue_id", ""))):
        raise ValueError("issue_id must look like LP-LTR-001")
    for key in ("letter", "card", "sources"):
        if not issue.get(key):
            raise ValueError("issue missing " + key)
    if not isinstance(issue["sources"], list) or not all(
        isinstance(src, dict) and src.get("label") and src.get("locus")
        for src in issue["sources"]
    ):
        raise ValueError("sources must carry label and locus")
    for key in ("title", "body"):
        if not str(issue["letter"].get(key, "")).strip():
            raise ValueError("letter missing " + key)
    for key in ("address", "parent", "claim", "branch_address", "branch_question"):
        if not str(issue["card"].get(key, "")).strip():
            raise ValueError("card missing " + key)

    letter = issue_lines(issue)
    card = card_lines(issue)
    slip = limit_lines(return_lines(issue), width=432, height=288, margin=22, leading=13)
    out = Path(args.out)
    new_directory(out)
    artifacts = [
        ("letter", "letter.pdf", letter, dict(width=612, height=792, margin=50, font_size=11, leading=15)),
        ("branch_card", "index-card-4x6.pdf", card, dict(width=432, height=288, margin=22, font_size=10, leading=13)),
        ("return_slip", "return-slip-4x6.pdf", slip, dict(width=432, height=288, margin=22, font_size=10, leading=13)),
    ]
    records = []
    for role, name, lines, geometry in artifacts:
        path = out / name
        make_text_pdf(path, lines, **geometry)
        records.append({"role": role, "path": name, "bytes": path.stat().st_size, "sha256": digest(path)})
    write_json(out / "manifest.json", {
        "cycle_version": VERSION,
        "issue_id": issue["issue_id"],
        "source_issue_sha256": fingerprint(issue),
        "state": "proof_prepared",
        "address": issue["card"]["address"],
        "source_pointers": issue["sources"],
        "artifacts": records,
        "limits": ["PROOF != PUBLICATION", "PREPARED != PRINTED", "PRINTED != MAILED",
                   "DELIVERED != READ", "REPLY != ADMISSION", "CONSENT != EDITORIAL SELECTION"],
    })
    print(out / "manifest.json")


def cmd_receive(args: argparse.Namespace) -> None:
    manifest = read_json(Path(args.manifest))
    response = read_json(Path(args.response))
    if manifest.get("cycle_version") != VERSION or manifest.get("state") != "proof_prepared":
        raise ValueError("not a prepared letter cycle")
    if response.get("issue_id") != manifest.get("issue_id"):
        raise ValueError("response targets a different issue")
    if response.get("kind") not in ("synthetic", "human"):
        raise ValueError("response.kind must be synthetic or human")
    if not isinstance(response.get("message"), str) or not response["message"].strip():
        raise ValueError("response message required")
    if not isinstance(response.get("consent"), dict):
        raise ValueError("consent must be explicit; no public permission is inferred")
    if response["consent"].get("may_quote_publicly") not in (True, False):
        raise ValueError("consent.may_quote_publicly must be a boolean")
    if response["consent"].get("may_credit_name") not in (True, False):
        raise ValueError("consent.may_credit_name must be a boolean")
    if response["kind"] == "synthetic" and response.get("channel") != "simulation":
        raise ValueError("synthetic replies must declare channel simulation")
    out = Path(args.out)
    private_output(out)
    new_directory(out)
    write_json(out / "private-response.json", response)
    write_json(out / "intake.json", {
        "cycle_version": VERSION,
        "issue_id": response["issue_id"],
        "submission_fingerprint_sha256": fingerprint(response),
        "kind": response["kind"],
        "channel_claimed": response.get("channel", "unspecified"),
        "channel_evidence": "not_verified",
        "state": "received_held",
        "consent": response["consent"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "storage": "private_local_only",
        "law": "RECEIVED != REVIEWED != ADMITTED != PUBLISHED",
    })
    print(out / "intake.json")


def cmd_decide(args: argparse.Namespace) -> None:
    hold = Path(args.hold)
    private_output(hold)
    intake = read_json(hold / "intake.json")
    if intake.get("state") != "received_held":
        raise ValueError("only a held intake can be reviewed")
    if (hold / "decision.json").exists():
        raise ValueError("decision already exists: use a new review lineage")
    if not args.human_confirmed or not args.reviewer.strip():
        raise ValueError("explicit --human-confirmed and --reviewer are required")
    if args.decision == "consider" and intake["consent"]["may_quote_publicly"] is not True:
        raise ValueError("cannot consider public quotation without affirmative consent")
    write_json(hold / "decision.json", {
        "cycle_version": VERSION,
        "issue_id": intake["issue_id"],
        "submission_fingerprint_sha256": intake["submission_fingerprint_sha256"],
        "decision": args.decision,
        "reviewer_declaration": args.reviewer,
        "state": "human_review_recorded",
        "authority": "declared human editorial act; not verified identity",
        "publication": "not_authorized",
    })
    print(hold / "decision.json")


def cmd_next(args: argparse.Namespace) -> None:
    hold = Path(args.hold)
    private_output(hold)
    intake = read_json(hold / "intake.json")
    review = read_json(hold / "decision.json")
    if review.get("decision") != "consider" or review.get("state") != "human_review_recorded":
        raise ValueError("next-issue consideration requires a human-reviewed consider decision")
    if intake.get("submission_fingerprint_sha256") != review.get("submission_fingerprint_sha256"):
        raise ValueError("review/intake mismatch")
    out = Path(args.out)
    private_output(out)
    if out.exists():
        raise ValueError("output already exists")
    write_json(out, {
        "cycle_version": VERSION,
        "state": "candidate_only",
        "parent_issue_id": intake["issue_id"],
        "input_reply_sha256": intake["submission_fingerprint_sha256"],
        "candidate_topic": args.topic,
        "quotation": "omitted_until_separately_selected",
        "publishable": False,
        "evidence": "private local intake and explicit review, not proof of postal delivery",
        "law": "CONSIDERATION != SELECTION != PUBLICATION",
    })
    print(out)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    proof = sub.add_parser("proof")
    proof.add_argument("issue")
    proof.add_argument("--out", required=True)
    proof.set_defaults(func=cmd_proof)
    receive = sub.add_parser("receive")
    receive.add_argument("response")
    receive.add_argument("--manifest", required=True)
    receive.add_argument("--out", required=True)
    receive.set_defaults(func=cmd_receive)
    decide = sub.add_parser("decide")
    decide.add_argument("--hold", required=True)
    decide.add_argument("--decision", required=True, choices=("hold", "decline", "consider"))
    decide.add_argument("--reviewer", required=True)
    decide.add_argument("--human-confirmed", action="store_true")
    decide.set_defaults(func=cmd_decide)
    nxt = sub.add_parser("next")
    nxt.add_argument("--hold", required=True)
    nxt.add_argument("--out", required=True)
    nxt.add_argument("--topic", required=True)
    nxt.set_defaults(func=cmd_next)
    return p


if __name__ == "__main__":
    try:
        args = parser().parse_args()
        args.func(args)
    except (ValueError, OSError) as exc:
        print("LETTER CYCLE HOLD: " + str(exc), file=sys.stderr)
        sys.exit(2)
