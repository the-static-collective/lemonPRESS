#!/usr/bin/env python3
"""lemonPRESS Press Run 001.

Turns a physical queue into an inspectable run report and, for queue items
explicitly marked "compose", Physical Composer proposal files.

No human selection and no publication authorization occur here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from physical_composer import VERSION as COMPOSER_VERSION
from physical_composer import compose

RUN_VERSION = "press-run-001"
ALLOWED_MODES = {"compose", "gate_preflight", "proof_review", "hold"}


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


def validate_queue(queue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if queue.get("press_run_version") != RUN_VERSION:
        errors.append(f"press_run_version must be {RUN_VERSION}")
    for key in ("run_id", "title", "items"):
        if key not in queue:
            errors.append(f"queue missing key: {key}")
    items = queue.get("items", [])
    if not isinstance(items, list):
        return errors + ["items must be an array"]

    seen_queue: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"item[{index}] must be an object")
            continue
        for key in ("queue_id", "house_id", "work_id", "title", "mode", "reason"):
            if not str(item.get(key, "")).strip():
                errors.append(f"item[{index}] missing {key}")
        queue_id = str(item.get("queue_id", ""))
        if queue_id in seen_queue:
            errors.append(f"duplicate queue_id: {queue_id}")
        seen_queue.add(queue_id)
        if item.get("mode") not in ALLOWED_MODES:
            errors.append(f"item[{index}] unknown mode: {item.get('mode')!r}")
        if item.get("mode") == "compose" and not isinstance(item.get("brief"), dict):
            errors.append(f"item[{index}] compose mode requires brief object")
        if item.get("mode") == "proof_review" and not isinstance(item.get("existing_proof"), dict):
            errors.append(f"item[{index}] proof_review mode requires existing_proof object")
    return errors


def build_brief(item: dict[str, Any]) -> dict[str, Any]:
    source = dict(item.get("brief", {}))
    return {
        "work_id": item["work_id"],
        "title": item["title"],
        "edition_intent": source.get("edition_intent", ""),
        "content": source.get("content", {}),
        "constraints": source.get("constraints", {}),
        "affordances": source.get("affordances", []),
        "notes": source.get("notes", []),
    }


def mode_next_action(item: dict[str, Any]) -> str:
    mode = item["mode"]
    if mode == "compose":
        return "Review Physical Composer proposals; explicitly select or hold a body."
    if mode == "gate_preflight":
        return "Build/verify a Press Gate packet from the established physical body without recomposing it."
    if mode == "proof_review":
        return "Inspect the existing proof as a physical object; revise only from observed evidence."
    return "Hold. Do not advance until the queue item is deliberately reopened."


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['run_id']} — Run Report",
        "",
        f"**Queue:** {report['title']}",
        "",
        "> QUEUE != AUTHORIZATION TO PUBLISH",
        "",
        "| # | House ID | Work | Mode | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        title = str(item["title"]).replace("|", "\\|")
        action = str(item["next_action"]).replace("|", "\\|")
        lines.append(
            f"| {item['queue_id']} | {item['house_id']} | {title} | "
            f"{item['mode']} | {action} |"
        )

    lines.extend(["", "## Composition outputs", ""])
    composed = [x for x in report["items"] if x.get("composition_file")]
    if not composed:
        lines.append("None.")
    else:
        for item in composed:
            lines.append(
                f"- **{item['house_id']}** → `{item['composition_file']}` "
                f"({len(item.get('candidates', []))} candidates)"
            )

    lines.extend([
        "",
        "## Crossing law",
        "",
        "    RECOMMENDATION != SELECTION",
        "    PROOF != PUBLICATION",
        "    EXISTING PROOF != NEED TO RECOMPOSE",
        "    PRIOR EDITION SPEC != INHERITED SPEC",
        "",
    ])
    return "\n".join(lines)


def run_queue(queue: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    items_out: list[dict[str, Any]] = []

    for item in queue["items"]:
        record: dict[str, Any] = {
            "queue_id": item["queue_id"],
            "house_id": item["house_id"],
            "work_id": item["work_id"],
            "title": item["title"],
            "mode": item["mode"],
            "reason": item["reason"],
            "next_action": mode_next_action(item),
        }

        if item["mode"] == "compose":
            brief = build_brief(item)
            candidates = compose(brief)
            composition = {
                "composition_version": COMPOSER_VERSION,
                "press_run_id": queue["run_id"],
                "queue_id": item["queue_id"],
                "house_id": item["house_id"],
                "work_id": item["work_id"],
                "title": item["title"],
                "edition_intent": brief["edition_intent"],
                "authority": {
                    "mode": "proposal_only",
                    "law": "RECOMMENDATION != SELECTION",
                },
                "candidates": candidates,
                "selection": None,
            }
            filename = f"{item['queue_id']}-{item['house_id']}-composition.json"
            write_json(out_dir / filename, composition)
            record["composition_file"] = filename
            record["candidates"] = [
                {"candidate_id": c["candidate_id"], "name": c["name"]}
                for c in candidates
            ]
        elif item["mode"] == "gate_preflight":
            record["fixed"] = item.get("fixed", {})
            record["held"] = item.get("held", [])
        elif item["mode"] == "proof_review":
            record["existing_proof"] = item.get("existing_proof", {})

        items_out.append(record)

    return {
        "press_run_version": RUN_VERSION,
        "run_id": queue["run_id"],
        "title": queue["title"],
        "source_queue": "queue.json",
        "authority": {
            "mode": "orchestration_only",
            "law": "QUEUE != AUTHORIZATION TO PUBLISH",
        },
        "items": items_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="lemonPRESS Press Run 001")
    parser.add_argument("queue")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    queue_path = Path(args.queue)
    out_dir = Path(args.out)

    try:
        queue = load_json(queue_path)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    errors = validate_queue(queue)
    if errors:
        print("PRESS RUN: FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    report = run_queue(queue, out_dir)
    write_json(out_dir / "run-report.json", report)
    (out_dir / "RUN-REPORT.md").write_text(render_markdown(report), encoding="utf-8")

    counts = {mode: 0 for mode in sorted(ALLOWED_MODES)}
    for item in queue["items"]:
        counts[item["mode"]] += 1

    print("PRESS RUN: PASS")
    print(f"run_id: {queue['run_id']}")
    print(f"items: {len(queue['items'])}")
    for mode, count in counts.items():
        if count:
            print(f"{mode}: {count}")
    print(f"output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
