#!/usr/bin/env python3
"""lemonPRESS Physical Composer 001.

A deterministic material-form proposer for physical editions.
It proposes; it never silently selects.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VERSION = "physical-composer-001"


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


def words(brief: dict[str, Any]) -> set[str]:
    chunks = [
        str(brief.get("title", "")),
        str(brief.get("edition_intent", "")),
        " ".join(map(str, brief.get("affordances", []))),
        " ".join(map(str, brief.get("notes", []))),
    ]
    return {w.strip(".,:;!?()[]{}\"'").lower() for w in " ".join(chunks).split()}


def candidate(
    cid: str,
    name: str,
    format_name: str,
    moves: list[str],
    reasons: list[str],
    production: dict[str, Any],
    risks: list[str] | None = None,
    held: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": cid,
        "name": name,
        "state": "recommended",
        "format": format_name,
        "material_moves": moves,
        "fit_evidence": reasons,
        "production": production,
        "risks": risks or [],
        "held": held or [],
    }


def compose(brief: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = words(brief)
    content = brief.get("content", {}) if isinstance(brief.get("content"), dict) else {}
    constraints = brief.get("constraints", {}) if isinstance(brief.get("constraints"), dict) else {}
    pages = content.get("estimated_pages")
    images = content.get("image_density", "unknown")
    home = bool(constraints.get("home_printable", False))
    budget = str(constraints.get("budget", "standard")).lower()

    out: list[tuple[int, dict[str, Any]]] = []

    codex = candidate(
        "codex",
        "Ordinary Codex",
        "book",
        ["conventional bound reading sequence", "edition-local colophon"],
        ["stable baseline against which stranger forms can be compared"],
        {"binding": "perfect_bound", "trim_inches": None, "paper": None, "color": None},
    )
    out.append((2, codex))

    if (isinstance(pages, int) and pages <= 64) or home or budget == "low":
        reasons = []
        if isinstance(pages, int) and pages <= 64:
            reasons.append(f"estimated page count is {pages}, within booklet territory")
        if home:
            reasons.append("brief asks for home-printable behavior")
        if budget == "low":
            reasons.append("brief declares a low production budget")
        out.append((7, candidate(
            "saddle-booklet",
            "Saddle-Stitched Booklet",
            "booklet",
            ["folded signatures", "visible center seam", "low-cost proofability"],
            reasons,
            {"binding": "saddle_stitch", "trim_inches": "5.5x8.5", "paper": None, "color": None},
        )))

    returnish = {"return", "reread", "again", "recurring", "loop", "stair", "reentry", "echo"}
    if tokens & returnish:
        out.append((10, candidate(
            "staircase",
            "Staircase Edition",
            "book",
            ["narrow or inset return leaves", "visible fore-edge rhythm", "tactile rereading"],
            [f"brief contains return/repetition language: {', '.join(sorted(tokens & returnish))}"],
            {"binding": None, "trim_inches": None, "paper": None, "color": None},
        )))

    writable = {"write", "writable", "journal", "field", "receipt", "workbook", "notes"}
    if tokens & writable:
        out.append((8, candidate(
            "field-book",
            "Field / Receipt Book",
            "workbook",
            ["writable margins", "receipt leaves", "durable navigation", "intentional blank space"],
            [f"brief asks for participation/marking: {', '.join(sorted(tokens & writable))}"],
            {"binding": "lay_flat_preferred", "trim_inches": None, "paper": "uncoated_writable", "color": None},
        )))

    modular = {"modular", "cluster", "pamphlet", "parts", "chapters", "bundle", "series"}
    if tokens & modular:
        out.append((8, candidate(
            "pamphlet-cluster",
            "Pamphlet Cluster",
            "multi_object_set",
            ["multiple saddle-stitched units", "paper band or sleeve", "reader-controlled order"],
            [f"brief contains modular structure language: {', '.join(sorted(tokens & modular))}"],
            {"binding": "mixed_saddle_stitch", "trim_inches": None, "paper": None, "color": None},
        )))

    routeish = {"road", "route", "path", "trail", "journey", "sequence", "traversal", "walk", "stations"}
    if tokens & routeish:
        out.append((11, candidate(
            "route-book",
            "Route / Traversal Book",
            "route_book",
            [
                "section openings behave as stations rather than generic chapters",
                "visible route markers accumulate as the reader advances",
                "source-road or route receipt remains physically inspectable",
                "binding may open into a continuous route rather than a closed codex spine",
            ],
            [f"brief contains traversal grammar: {', '.join(sorted(tokens & routeish))}"],
            {"binding": "lay_flat_or_accordion_candidate", "trim_inches": None, "paper": None, "color": None},
            risks=[
                "road language can become decorative if material sequence does not carry actual navigation",
                "accordion construction may become impractical at high page counts",
            ],
            held=["exact binding depends on page count, printer limits, and proof handling"],
        )))

    traceish = {"found", "source", "receipt", "trace", "archive", "provenance", "quoted", "citation"}
    if tokens & traceish:
        out.append((10, candidate(
            "trace-edition",
            "Trace / Receipt Edition",
            "documentary_book",
            [
                "source labels become navigation furniture rather than footnote clutter",
                "quoted source body and connective tissue remain visibly distinguishable",
                "a rear source road or foldout receipt preserves the route back",
                "physical production matter is marked as descendant matter",
            ],
            [f"brief contains source/provenance grammar: {', '.join(sorted(tokens & traceish))}"],
            {"binding": None, "trim_inches": None, "paper": None, "color": None},
            risks=["receipt furniture can overwhelm the reading experience if every trace is promoted equally"],
            held=["density and placement of source receipts require an edition-specific proof"],
        )))

    companionish = {"companion", "paired", "pair", "partner", "paired_with"}
    if tokens & companionish:
        out.append((9, candidate(
            "companion-geometry",
            "Companion Pair Geometry",
            "paired_volume",
            [
                "preserve independent edition identities while designing a deliberate relationship",
                "use shared or inverse physical cues only after both bodies are independently known",
                "a removable band, sleeve, mirrored edge, or opposed orientation may carry the relation",
                "pairing must remain removable so one volume still reads lawfully alone",
            ],
            [f"brief contains companion/pair grammar: {', '.join(sorted(tokens & companionish))}"],
            {"binding": None, "trim_inches": None, "paper": None, "color": None},
            risks=["pairing pressure can silently force one book to inherit the other's trim or production assumptions"],
            held=["partner dimensions and final relation remain open until both editions have independent physical selections"],
        )))

    if str(images).lower() in {"high", "heavy", "image-heavy", "image_heavy"} or "visual" in tokens:
        out.append((7, candidate(
            "folio",
            "Folio / Insert Edition",
            "folio",
            ["large image surfaces", "removable or nested inserts", "spread-first sequencing"],
            ["brief is image-heavy or explicitly visual"],
            {"binding": None, "trim_inches": None, "paper": None, "color": "color_candidate"},
        )))

    experimental = {"fold", "gatefold", "translucent", "edge", "insert", "removable", "decoder", "tactile"}
    if tokens & experimental:
        out.append((9, candidate(
            "mechanical-book",
            "Mechanical Book",
            "experimental_object",
            ["folds/inserts/removable matter", "carrier-specific reveal", "handling as sequence"],
            [f"brief names material mechanics: {', '.join(sorted(tokens & experimental))}"],
            {"binding": None, "trim_inches": None, "paper": None, "color": None},
        )))

    out.sort(key=lambda item: (-item[0], item[1]["candidate_id"]))
    return [item for _, item in out[:6]]


def cmd_compose(args: argparse.Namespace) -> int:
    try:
        brief = load_json(Path(args.brief))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    required = ("work_id", "title", "edition_intent")
    missing = [k for k in required if not str(brief.get(k, "")).strip()]
    if missing:
        print("brief missing: " + ", ".join(missing), file=sys.stderr)
        return 2

    result = {
        "composition_version": VERSION,
        "work_id": brief["work_id"],
        "title": brief["title"],
        "edition_intent": brief["edition_intent"],
        "authority": {
            "mode": "proposal_only",
            "law": "RECOMMENDATION != SELECTION",
        },
        "candidates": compose(brief),
        "selection": None,
    }
    write_json(Path(args.out), result)
    print(args.out)
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    try:
        composition = load_json(Path(args.composition))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    candidates = composition.get("candidates", [])
    chosen = next(
        (c for c in candidates if isinstance(c, dict) and c.get("candidate_id") == args.candidate_id),
        None,
    )
    if chosen is None:
        print(f"unknown candidate_id: {args.candidate_id}", file=sys.stderr)
        return 2

    selection = {
        "composition_version": composition.get("composition_version"),
        "work_id": composition.get("work_id"),
        "title": composition.get("title"),
        "candidate_id": chosen["candidate_id"],
        "name": chosen["name"],
        "state": "human_selected",
        "production": chosen.get("production", {}),
        "material_moves": chosen.get("material_moves", []),
        "fit_evidence": chosen.get("fit_evidence", []),
        "selection_receipt": {
            "mechanism": "explicit select command",
            "note": "The tool changed state only because a human named the candidate.",
        },
    }
    write_json(Path(args.out), selection)
    print(args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="lemonPRESS Physical Composer 001")
    sub = parser.add_subparsers(dest="command", required=True)

    compose_parser = sub.add_parser("compose", help="generate material-form proposals")
    compose_parser.add_argument("brief")
    compose_parser.add_argument("--out", required=True)
    compose_parser.set_defaults(func=cmd_compose)

    select_parser = sub.add_parser("select", help="record an explicit human selection")
    select_parser.add_argument("composition")
    select_parser.add_argument("candidate_id")
    select_parser.add_argument("--out", required=True)
    select_parser.set_defaults(func=cmd_select)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
