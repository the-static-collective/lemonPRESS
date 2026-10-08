#!/usr/bin/env python3
"""A text-only foreign renderer: no image decoding and no LemonPRESS imports."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys

RENDERER = {"id": "foreign:receipt-scroll/v0", "version": "1", "requiresLemonpress": False,
    "capabilities": ["plain HTML", "Japanese primary text", "English witness", "declared reading order"],
    "incapableOf": ["decoding PNG", "copying source art", "reconstructing panels", "matching source pixels"],
    "styleDisposition": "language/channel behavior consumed; source palette, panel layout, tone and motifs retained as evidence only"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def render(press, crossing_id):
    if press["status"] != "CANDIDATE" or press["authority"] != {"semantic": False, "houseAdmission": False, "publication": False}:
        raise ValueError("renderer accepts only non-authoritative candidates")
    esc = html.escape
    rows = []
    for index, placement in enumerate(press["placements"], 1):
        rows.append(f'<article id="{esc(placement["id"], quote=True)}"><small>{index:02d} / {esc(placement["channel"])}</small><p lang="ja" class="primary">{esc(placement["primary"])}</p><p lang="en" class="gloss">{esc(placement["gloss"])}</p><details><summary>Source witness and drift</summary><p>{esc(placement["sourceText"])}</p><p>{esc(placement["drift"])}</p><small>{esc(placement["locus"])}</small></details></article>')
    losses = "".join("<li>" + esc(item) + "</li>" for item in press["loss"])
    return ('<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RENJI RELAY 001 — The Page That Arrived</title><style>body{margin:0;background:#f3eee3;color:#243832;font-family:Georgia,serif}main{max-width:720px;margin:auto;padding:56px 24px}h1{font-size:42px;line-height:1.05}small{font-family:monospace;overflow-wrap:anywhere}article{border-top:1px solid #a6ada1;padding:28px 0}.primary{font-size:26px;line-height:1.7}.gloss{font-size:19px;line-height:1.5}details{font-size:14px;color:#52615a}footer{border-top:3px double #52615a;margin-top:40px;padding-top:24px}li{margin:8px 0}</style><main><small>RENJI RELAY 001 / FOREIGN ARRIVAL</small><h1>The page that arrived</h1><p>A selected page crossed languages and reading order. This room can typeset its text; it cannot reproduce its art.</p><p><strong>TRANSFORM ≠ SEVER</strong><br>Japanese primary · English returned witness · draft descendant</p>' + "".join(rows) + '<footer><h2>What the door kept</h2><p>The source byte identity, declared text particulars, Japanese intermediate, returned-English drift, reading-order declaration and style ancestry remain addressable in the accompanying packet.</p><h2>What the door lost</h2><ul>' + losses + '</ul><small>Source SHA-256: ' + esc(press["sourceSha256"]) + '<br>Crossing: ' + esc(crossing_id) + '<br>Renderer: foreign:receipt-scroll/v0</small><p>This arrival carries ancestry. Local experiment admission grants no house publication or source authority.</p></footer></main></html>\n').encode("utf-8")


def compose(folder):
    folder = Path(folder)
    carrier = (folder / "press.json").read_bytes()
    crossing = json.loads((folder / "crossing.json").read_text(encoding="utf-8"))
    if crossing["payload_refs"] != [{"address": "sha256:" + digest(carrier), "role": "press-candidate", "media_type": "application/json"}]:
        raise ValueError("crossing payload is not exact press carrier")
    body = render(json.loads(carrier), crossing["crossing_id"])
    renderer = {**RENDERER, "codeSha256": digest(Path(__file__).read_bytes())}
    receipt = {"schema": "lemonpress/renji-foreign-render/v0", "crossingId": crossing["crossing_id"],
        "inputSha256": digest(carrier), "outputSha256": digest(body), "renderer": renderer,
        "authority": {"semantic": False, "houseAdmission": False, "publication": False},
        "loss": ["all source pixels and panel geometry omitted", "foreign presentation replaces the requested palette and layout; original style stays in ancestry"],
        "unknown": ["semantic equivalence", "font availability", "aesthetic quality"]}
    return body, (json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    body, receipt = compose(args.bundle)
    files = {"arrival.html": body, "render-receipt.json": receipt}
    for name, data in files.items():
        path = Path(args.bundle) / name
        if args.verify or path.exists():
            if not path.exists() or path.read_bytes() != data: raise ValueError("render does not replay: " + name)
    if not args.verify:
        for name, data in files.items():
            path = Path(args.bundle) / name
            if not path.exists():
                with path.open("xb") as stream: stream.write(data)
    print(json.dumps({"status": "PASS", "outputSha256": digest(body), "signatureCheck": "run verify-crossing.mjs before trusting the crossing"}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
