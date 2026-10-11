#!/usr/bin/env python3
"""LemonPRESS MARGINALIA PROOF 003.
Render a *private* real PDF and offline HTML proof from replay-verified Three Doors.
Record one explicit human editorial choice WITHOUT publication authority.
Node 24, reportlab 4.4.9, pypdf 5.9.0, local DejaVu fonts.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from reportlab import Version as REPORTLAB_VERSION
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "lemonpress.marginalia-printproof/v0"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REGULAR = FONT_DIR / "DejaVuSans.ttf"
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
SUPPORTED_LANES = {"page": "page.pdf", "fragment": "fragment.html"}


def refuse(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    refuse(isinstance(value, dict), "JSON_OBJECT_REQUIRED")
    return value


def private_location(path: Path) -> Path:
    target = path.resolve()
    refuse(target != REPO and REPO not in target.parents, "NO_PRIVATE_OUTPUT_INSIDE_PUBLIC_REPO")
    return target


def verify_upstream(source: Path) -> dict:
    """Run independent Node cold replay; a filename or digest alone is insufficient."""
    source = private_location(source)
    refuse(source.is_dir(), "SCORE_DIRECTORY_REQUIRED")
    proc = subprocess.run(
        ["node", str(REPO / "tools/marginalia_three_doors_cli.mjs"), "verify", str(source)],
        text=True, capture_output=True, timeout=50, cwd=REPO, check=False,
    )
    refuse(proc.returncode == 0, "UPSTREAM_THREE_DOORS_REPLAY_FAILED:" + proc.stderr[-350:])
    report = json.loads(proc.stdout)
    refuse(report.get("replayed") is True and report.get("publication_authorized") is False
           and report.get("original_source_verified") is False, "UPSTREAM_AUTHORITY_MISMATCH")
    score = read_json(source / "score.json")
    packet = read_json(source / "source-selection.json")
    refuse(score.get("schema") == "lemonpress.marginalia-three-doors/v0",
           "INVALID_THREE_DOORS_SCORE")
    bounds = score.get("boundaries", {})
    refuse(bounds.get("private_only") is True and all(bounds.get(k) is False for k in
           ("house_admission", "editorial_selection", "rights_grant", "published", "deployed",
            "audio_rendered", "print_proof", "web_page")), "SOURCE_NOT_PRIVATE_CANDIDATE")
    refuse(score.get("packet_checksum") == packet.get("checksum"), "PARENT_PACKET_CHANGED")
    refuse(isinstance(score.get("score_id"), str), "SCORE_ID_REQUIRED")
    return {"score": score, "packet": packet, "verified": report}


def fonts():
    refuse(REGULAR.is_file() and BOLD.is_file(), "DEJAVU_FONTS_REQUIRED")
    if not pdfmetrics.getRegisteredFontNames() or "LPDejaVu" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("LPDejaVu", str(REGULAR)))
        pdfmetrics.registerFont(TTFont("LPDejaVu-Bold", str(BOLD)))
        pdfmetrics.registerFontFamily("LPDejaVu", normal="LPDejaVu", bold="LPDejaVu-Bold")
    return {"regular": sha(REGULAR.read_bytes()), "bold": sha(BOLD.read_bytes())}


def glyph_gate(values):
    # ReportLab may silently show tofu for missing font glyphs; reject them instead.
    font = pdfmetrics.getFont("LPDejaVu")
    glyphs = font.face.charToGlyph
    for value in values:
        refuse(isinstance(value, str), "EXPECTED_TEXT")
        for c in value:
            n = ord(c)
            refuse(c in "\n\t" or (n >= 32 and n != 127),
                   "SOURCE_HAS_UNPRINTABLE_CONTROL")
            if c not in "\n\t":
                refuse(n in glyphs and glyphs[n] != 0, "UNSUPPORTED_FONT_GLYPH_U+" + f"{n:04X}")


def pdf_bytes(packet: dict, score: dict) -> bytes:
    refuse("page" in [d["lane"] for d in score["doors"]], "PAGE_DOOR_NOT_SELECTED")
    s, m, e = packet["source"], packet["reading"], packet["relation"]
    texts = [s["title"], s["excerpt"], m["text"], m["kind"], m["recorded_at"]]
    if e:
        texts += [e["relation_type"], e["first_perceived_at"], e["discovery_trace"],
                  e["evidence_path"], e["recorded_current_status"]]
    glyph_gate(texts)
    data = io.BytesIO()
    greens = colors.HexColor("#285646")
    grey = colors.HexColor("#606b62")
    paper = colors.HexColor("#fcfaf4")
    ink = colors.HexColor("#202d27")
    page_size = (6*inch, 9*inch)

    def pdf_canvas(*args, **kwargs):
        kwargs.update(invariant=1, pageCompression=1)
        return canvas.Canvas(*args, **kwargs)

    doc = SimpleDocTemplate(data, pagesize=page_size, leftMargin=51,
        rightMargin=51, topMargin=65, bottomMargin=64, title="LemonPRESS Private Marginalia Proof",
        author="LemonPRESS (experimental private candidate)", pageCompression=1)
    styles = {
      "top": ParagraphStyle("top", fontName="LPDejaVu-Bold",fontSize=8.2,leading=12,
        textColor=greens,spaceAfter=22),
      "title": ParagraphStyle("title",fontName="LPDejaVu-Bold",fontSize=16,leading=22,
        textColor=ink,spaceAfter=14),
      "section": ParagraphStyle("section",fontName="LPDejaVu-Bold",fontSize=9,leading=14,
        textColor=greens,spaceBefore=21,spaceAfter=8),
      "body": ParagraphStyle("body",fontName="LPDejaVu",fontSize=10.1,leading=16,
        alignment=TA_LEFT,textColor=ink,spaceAfter=8,splitLongWords=1),
      "meta": ParagraphStyle("meta",fontName="LPDejaVu",fontSize=7,leading=12,
        textColor=grey,spaceBefore=6,spaceAfter=6,splitLongWords=1),
    }
    escaped = lambda value: html.escape(str(value), quote=True).replace("\n", "<br/>")
    story = [
      Paragraph("THE STATIC COLLECTIVE / LEMONPRESS", styles["top"]),
      Paragraph(escaped(s["title"]),styles["title"]),
      HRFlowable(width="100%",thickness=1,color=greens),
      Paragraph("01 / ORIGINAL PASSAGE",styles["section"]),
      Paragraph(escaped(s["excerpt"]),styles["body"]),
      Paragraph("Frozen version pointer: "+escaped(s["version_id"]),styles["meta"]),
      Paragraph("02 / A HUMAN MARGIN, RECORDED LATER",styles["section"]),
      Paragraph(escaped(m["text"]),styles["body"]),
      Paragraph("Kind: "+escaped(m["kind"])+"   |   Recorded: "+escaped(m["recorded_at"]),styles["meta"])
    ]
    if e:
        story += [
            Paragraph("03 / THE CONNECTION BECAME VISIBLE",styles["section"]),
            Paragraph(escaped(e["discovery_trace"]),styles["body"]),
            Paragraph("First perceived: "+escaped(e["first_perceived_at"])+"   |   Status: "+
              escaped(e["recorded_current_status"]),styles["meta"]),
            Paragraph("Evidence path (human declaration):",styles["meta"]),
            Paragraph(escaped(e["evidence_path"]),styles["body"]),
        ]
    story += [
       Spacer(1,22),HRFlowable(width="100%",thickness=.6,color=greens),
       Paragraph("This is a selected excerpt, not the whole original. "
        "The margin and connection were recorded separately. Full version bytes are omitted; "
        "their declared SHA-256 is NOT independently verified here.",styles["meta"]),
       Paragraph("PRIVATE PHYSICAL PROOF ONLY / RIGHTS NOT REVIEWED / NOT ADMITTED OR PUBLISHED",
                 styles["meta"])
    ]
    def footer(canv, doc):
        canv.saveState()
        w,h = page_size
        canv.setFillColor(paper)
        canv.rect(0,0,w,h,fill=1,stroke=0)
        # This is only the page background. Content is drawn after onPage.
        canv.setFillColor(greens)
        canv.rect(0,h-9,w,9,fill=1,stroke=0)
        canv.setFillColor(grey)
        canv.setFont("LPDejaVu",6.5)
        canv.drawString(51,37,"UNADMITTED PROOF  /  NO RELEASE")
        canv.drawRightString(w-51,37,"p. "+str(doc.page))
        canv.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer,canvasmaker=pdf_canvas)
    return data.getvalue()


def html_bytes(packet: dict, score: dict) -> bytes:
    refuse("fragment" in [d["lane"] for d in score["doors"]], "FRAGMENT_DOOR_NOT_SELECTED")
    s,m,e = packet["source"],packet["reading"],packet["relation"]
    t = lambda v: html.escape(str(v),quote=True)
    relation = (
       '<section id="relation" aria-labelledby="rel-h"><h2 id="rel-h">03 / When the connection appeared</h2>'
       '<p class="voice">' + t(e["discovery_trace"]) + '</p>'
       '<p class="meta">First perceived: <time>' + t(e["first_perceived_at"]) +
       '</time>. GOATedge: ' + t(e["recorded_current_status"]) +
       '. Neither is LemonPRESS admission.</p><p>' + t(e["evidence_path"]) + '</p></section>'
       if e else
       '<section id="relation"><h2>03 / No relation disclosed</h2>'
       '<p>Omission is not evidence of nonexistence.</p></section>'
    )
    css = (
      ":root{color-scheme:light;font-family:ui-serif,Georgia,serif;background:#f7f4e9;color:#24362f}"
      "body{max-width:48rem;margin:auto;padding:clamp(1.1rem,4vw,4rem);line-height:1.6}"
      "header{border-bottom:3px double #315b48;padding-bottom:1.3rem}"
      "small,.meta{color:#50635a}h1{line-height:1.18}h2{color:#315b48;font-size:1.05rem}"
      "nav a{margin-right:1rem;color:#315b48}section{margin-block:3rem}"
      "blockquote{margin:1rem 0;padding:1rem 1.4rem;border-left:4px solid #577965;background:#fffdf7}"
      ".voice{white-space:pre-wrap}footer{border-top:1px solid #a7b6aa;padding-top:1rem}"
      ".warning{font:700 .8rem/1.5 ui-sans-serif,system-ui,sans-serif}"
    )
    markup = (
      '<!doctype html><html lang="en"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      '<meta name="robots" content="noindex,nofollow,noarchive">'
      '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'; connect-src \'none\'; img-src \'none\'">'
      '<title>' + t(s["title"]) + ' — private reading proof</title>'
      '<style>'+css+'</style></head><body>'
      '<header><small>THE STATIC COLLECTIVE / LEMONPRESS</small>'
      '<h1>'+t(s["title"])+'</h1><p class="warning">PRIVATE FRAGMENT PROOF / NOT PUBLICLY RELEASED</p>'
      '<nav aria-label="Three ways to enter">'
      '<a href="#source">Source</a><a href="#margin">Later reading</a>'
      '<a href="#relation">Relation</a></nav></header>'
      '<main><section id="source"><h2>01 / A selected original excerpt</h2>'
      '<blockquote class="voice">'+t(s["excerpt"])+'</blockquote>'
      '<p class="meta">Exact excerpt SHA-256: '+t(s["excerpt_sha256"])+'</p>'
      '<p class="meta">Full source version hash (DECLARED, BYTES OMITTED): '+
      t(s["version_sha256"])+'</p></section>'
      '<section id="margin"><h2>02 / A later human reading</h2>'
      '<blockquote class="voice">'+t(m["text"])+'</blockquote>'
      '<p class="meta">Recorded: <time>'+t(m["recorded_at"])+'</time> / '+
      t(m["kind"])+'</p></section>'
      +relation+'</main><footer><p>Source ≠ margin. Discovery ≠ source birthday. '
      'Fragment ≠ complete reading. Rendering ≠ publication.</p>'
      '<p class="warning">No network assets. No source body. No house admission. Private file only.</p>'
      '</footer></body></html>'
    )
    return markup.encode("utf-8")


def expected_proofs(source: Path):
    witness = verify_upstream(source)
    fonts_digest = fonts()
    packet,score = witness["packet"],witness["score"]
    artifacts = {}
    if "page" in witness["verified"]["verified_doors"]:
        artifacts["page.pdf"] = pdf_bytes(packet,score)
    if "fragment" in witness["verified"]["verified_doors"]:
        artifacts["fragment.html"] = html_bytes(packet,score)
    refuse(bool(artifacts), "NO_RENDERABLE_DOORS_VOICE_SCRIPT_ONLY")
    manifest = {
      "schema":SCHEMA,"state":"PRIVATE_RENDERED_PROOF","score_id":score["score_id"],
      "source_packet_checksum":packet["checksum"],
      "original_source_version_verified":False,
      "source_attested":False,"rights_cleared":False,
      "author_identity_authenticated":False,
      "human_editorial_selection":False,
      "edition_admitted":False,"published":False,"print_run":False,
      "crawler_deployed":False,"voice_rendered":False,
      "font_identity":fonts_digest,"renderer":"reportlab-"+REPORTLAB_VERSION+"+offline-html-v0",
      "proofs":[{"door":next(k for k,v in SUPPORTED_LANES.items() if v==name),
        "file":name,"bytes":len(blob),"sha256":sha(blob)} for name,blob in sorted(artifacts.items())],
      "wrench":{"input":score["score_id"],
        "transformation":"Physical PDF proof and offline human-readable HTML projection",
        "output":"Local immutable candidate proofs only",
        "residual":"Full GOATnote source, unselected margins and live relations stay outside",
        "loss":"Full source context, rendering glyphs outside supplied font set, and live navigation",
        "unknown":"Rights, authorship, external provenance, real printed inspection",
        "stop":"HOLD at a private rendered proof pending human inspection and separate decision"}
    }
    return manifest,artifacts


def render(source: Path,out: Path):
    out=private_location(out)
    refuse(not out.exists(),"CREATE_ONLY_PROOF_EXISTS")
    manifest,artifacts=expected_proofs(source)
    out.mkdir(mode=0o700)
    for name,blob in artifacts.items():
        (out/name).write_bytes(blob)
        os.chmod(out/name,0o600)
    (out/"proof-manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",
        encoding="utf-8")
    os.chmod(out/"proof-manifest.json",0o600)
    return manifest


def verify(source: Path,proof: Path,check_decision: bool=True):
    proof=private_location(proof)
    expected,artifacts=expected_proofs(source)
    actual=read_json(proof/"proof-manifest.json")
    refuse(actual==expected,"PROOF_MANIFEST_REPLAY_MISMATCH")
    for name,blob in artifacts.items():
        refuse((proof/name).read_bytes()==blob,"RENDERED_PROOF_REPLAY_MISMATCH:"+name)
    # Reject unsafely added proof carriers; a reviewer must know what exists.
    refuse(set(x.name for x in proof.iterdir()) <=
           {"proof-manifest.json","page.pdf","fragment.html","decision.json"},
           "UNREVIEWED_EXTRA_PROOF_FILES")
    if check_decision and (proof/"decision.json").exists():
        decision=read_json(proof/"decision.json")
        refuse(decision.get("schema")=="lemonpress.marginalia-editorial-decision/v0"
            and decision.get("proof_manifest_sha256")==sha((proof/"proof-manifest.json").read_bytes())
            and decision.get("score_id")==expected["score_id"]
            and decision.get("publication_authorized") is False
            and decision.get("house_admission") is False
            and decision.get("rights_grant") is False
            and decision.get("external_reviewer_identity_verified") is False
            and decision.get("decision") in ("HOLD","REFUSE","SELECT_FOR_REVIEW"),
            "INVALID_EDITORIAL_DECISION")
        if decision["decision"]=="SELECT_FOR_REVIEW":
            refuse(decision.get("selected_door") in [x["door"] for x in expected["proofs"]],
                "CANNOT_SELECT_UNRENDERED_DOOR")
            proof_name=SUPPORTED_LANES[decision["selected_door"]]
            refuse(decision.get("selected_proof_sha256")==sha(artifacts[proof_name]),
                "EDITORIAL_SELECTION_PROOF_MISMATCH")
        else:
            refuse(decision.get("selected_door") is None and decision.get("selected_proof_sha256") is None,
                "NON_SELECTION_MUST_NOT_PICK_DOOR")
    return {"proofs_verified":len(artifacts),"state":"PRIVATE_RENDERED_PROOF",
        "score_id":actual["score_id"],"published":False,
        "editorial_decision":("RECORDED" if (proof/"decision.json").exists() else "NOT_RECORDED"),
        "full_source_verified":False}


def decide(source: Path,proof: Path,decision: str,reviewer: str,selected: str | None,human: bool):
    proof=private_location(proof)
    refuse(human is True,"EXPLICIT_HUMAN_CONFIRMATION_REQUIRED")
    refuse(isinstance(reviewer,str) and 1<=len(reviewer.strip())<=120,
           "REVIEWER_DECLARATION_REQUIRED")
    refuse(decision in ("HOLD","REFUSE","SELECT_FOR_REVIEW"),"INVALID_DECISION")
    refuse(not (proof/"decision.json").exists(),"CREATE_ONLY_EDITORIAL_DECISION_EXISTS")
    proof_status=verify(source,proof)
    if decision=="SELECT_FOR_REVIEW":
        refuse(selected in SUPPORTED_LANES and (proof/SUPPORTED_LANES[selected]).is_file(),
               "RENDERED_DOOR_SELECTION_REQUIRED")
    else:
        refuse(selected is None,"HOLD_OR_REFUSE_HAS_NO_SELECTED_DOOR")
    manifest_bytes=(proof/"proof-manifest.json").read_bytes()
    record={
      "schema":"lemonpress.marginalia-editorial-decision/v0",
      "score_id":proof_status["score_id"],
      "proof_manifest_sha256":sha(manifest_bytes),
      "decision":decision,"selected_door":selected,
      "selected_proof_sha256":sha((proof/SUPPORTED_LANES[selected]).read_bytes()) if selected else None,
      "reviewer_declaration":reviewer.strip(),
      "human_confirmed":True,
      "recorded_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "private_local_only":True,
      "publication_authorized":False,"house_admission":False,"rights_grant":False,
      "external_reviewer_identity_verified":False,
      "stop":"Editorial review can select an internal proof. Publication remains a separate house crossing."
    }
    with (proof/"decision.json").open("x",encoding="utf-8") as fh:
        json.dump(record,fh,indent=2,sort_keys=True)
        fh.write("\n")
    os.chmod(proof/"decision.json",0o600)
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    r=sub.add_parser("render");r.add_argument("score_dir");r.add_argument("new_proof_dir")
    v=sub.add_parser("verify");v.add_argument("score_dir");v.add_argument("proof_dir")
    d=sub.add_parser("decide");d.add_argument("score_dir");d.add_argument("proof_dir")
    d.add_argument("--decision",choices=["HOLD","REFUSE","SELECT_FOR_REVIEW"],required=True)
    d.add_argument("--selected-door",choices=["page","fragment"])
    d.add_argument("--reviewer",required=True);d.add_argument("--human-confirmed",action="store_true")
    args=parser.parse_args(argv)
    if args.command=="render":
        result=render(Path(args.score_dir),Path(args.new_proof_dir))
    elif args.command=="verify":
        result=verify(Path(args.score_dir),Path(args.proof_dir))
    else:
        result=decide(Path(args.score_dir),Path(args.proof_dir),args.decision,
                      args.reviewer,args.selected_door,args.human_confirmed)
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:
        print("PRINT PROOF HOLD: "+str(error),file=sys.stderr)
        raise SystemExit(1)
