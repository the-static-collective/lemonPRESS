#!/usr/bin/env python3
"""RELETTER BATCH 001: render all solid-surface box bindings as returned-English page candidates."""
from __future__ import annotations
import argparse, copy, hashlib, io, json, sys
from pathlib import Path
from typing import Any
import jsonschema
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import manga_press as press
import manga_page_intake as intake
import manga_box_binding as boxes
import manga_reletter as reletter

SPEC_SCHEMA_NAME="manga-reletter-batch-v0.schema.json"
CANDIDATE_SCHEMA_NAME="manga-reletter-batch-candidate-v0.schema.json"
SPEC_SCHEMA="lemonpress/manga-reletter-batch/v0"
CANDIDATE_SCHEMA="lemonpress/manga-reletter-batch-candidate/v0"
LAWS=[
 "BATCH != ADMISSION","SOLID PATCH != SOURCE RESTORATION","BLOCKED REGION SURVIVES UNCHANGED",
 "FIT != EDITORIAL SELECTION","RETURN != ORIGINAL","PAGE ORDER SURVIVES BATCH",
 "RIGHTS NEVER EXPAND","PARTIAL RENDER != COMPLETE EDITION","OUTPUT != PUBLICATION"
]

def require(c,m):
    if not c: raise ValueError(m)

def _schema(n): return json.loads((ROOT/"schemas"/n).read_text(encoding="utf-8"))
def validate_schema(v,n):
    d=_schema(n); jsonschema.Draft202012Validator.check_schema(d)
    try: jsonschema.Draft202012Validator(d).validate(v)
    except jsonschema.ValidationError as e:
        loc=".".join(str(x) for x in e.absolute_path) or "<root>"
        raise ValueError(f"schema validation failed at {loc}: {e.message}") from e

def _root_path(root,rel,label):
    p=Path(rel); require(isinstance(rel,str) and rel.strip() and not p.is_absolute() and ".." not in p.parts and "\\" not in rel and p.as_posix()==rel,f"{label} path")
    out=(root/p).resolve(); require(out.is_relative_to(root.resolve()),f"{label} escapes root"); return out

def _sha(b): return hashlib.sha256(b).hexdigest()

def _fit(text,rect,role_style,surface_style):
    dummy=Image.new("RGB",(1,1)); draw=ImageDraw.Draw(dummy)
    pad=role_style["paddingPx"]; spacing=role_style["lineSpacingPx"]
    iw=rect["width"]-2*pad; ih=rect["height"]-2*pad
    require(iw>0 and ih>0,"padding consumes box")
    for size in range(role_style["maxFontPx"],role_style["minFontPx"]-1,-1):
        font=ImageFont.load_default(size=size)
        lines=reletter._wrap(draw,text,font,iw)
        bbox=draw.textbbox((0,0),"Ag",font=font)
        lh=max(1,bbox[3]-bbox[1])
        total=len(lines)*lh+max(0,len(lines)-1)*spacing
        if total<=ih:
            return {"backgroundRgba":surface_style["backgroundRgba"],"foregroundRgba":surface_style["foregroundRgba"],
                    "font":"pillow-default","fontPx":size,"paddingPx":pad,"lineSpacingPx":spacing,"align":role_style["align"]}
    raise ValueError(f"text cannot fit declared box within font range: {text}")

def _load(root,spec):
    validate_schema(spec,SPEC_SCHEMA_NAME); require(spec["schema"]==SPEC_SCHEMA,f"expected {SPEC_SCHEMA}"); require(spec["laws"]==LAWS,"batch law set mismatch")
    box_path=_root_path(root,spec["boxBindingSpec"],"boxBindingSpec"); box_spec=press.read_json(box_path); box_candidate=boxes.build(root,box_spec)
    intake_path=_root_path(root,spec["pageIntakeSpec"],"pageIntakeSpec"); intake_spec=press.read_json(intake_path); intake_candidate=intake.verify_bundle(root,intake_spec)
    require(box_candidate["pageCount"]==intake_candidate["pageCount"],"box/intake page count mismatch")
    pages={p["page"]:p for p in intake_candidate["pages"]}
    return box_candidate,intake_candidate,pages,box_spec

def build(root,spec):
    root=Path(root).resolve(); box_candidate,intake_candidate,pages,box_spec=_load(root,spec)
    by_page={n:[] for n in pages}
    blocked=[]
    for b in box_candidate["bindings"]:
        if b["surfaceClass"] in ("solid-dark","solid-light"): by_page[b["page"]].append(b)
        else: blocked.append({"segmentId":b["segmentId"],"page":b["page"],"surfaceClass":b["surfaceClass"],"rectPx":b["rectPx"]})
    outputs={}; page_records=[]
    for n in sorted(pages):
        p=pages[n]; manifest=press.bound_json(root,p["pageManifest"])
        bindings=by_page[n]
        if bindings:
            placements=[]
            for b in bindings:
                role_style=spec["roleStyles"][b["role"]]
                style=_fit(b["returnedText"],b["rectPx"],role_style,spec["surfaceStyles"][b["surfaceClass"]])
                placements.append({"placementId":"batch-"+b["segmentId"],"segmentId":b["segmentId"],"rectPx":copy.deepcopy(b["rectPx"]),"style":style})
            recipe={"schema":reletter.RECIPE_SCHEMA,"title":f"{spec['title']} - page {n:02d}",
                    "relaySpec":box_spec["relaySpec"],"stage":"return",
                    "parent":{"parentId":p["pageId"],"pageManifest":copy.deepcopy(p["pageManifest"])},"placements":placements}
            rc,png=reletter.build(root,recipe)
            page_records.append({"page":n,"pageId":p["pageId"],"mode":"reletter","inputPngSha256":p["sourceImage"]["sha256"],
                                 "outputPngSha256":_sha(png),"reletterCandidateId":rc["candidateId"],
                                 "renderedParticulars":[x["segmentId"] for x in bindings]})
        else:
            png=press.bound_path(root,manifest["sourceImage"]).read_bytes()
            page_records.append({"page":n,"pageId":p["pageId"],"mode":"passthrough","inputPngSha256":p["sourceImage"]["sha256"],
                                 "outputPngSha256":_sha(png),"reletterCandidateId":None,"renderedParticulars":[]})
        outputs[f"pages/page-{n:02d}.png"]=png
    spec_sha=_sha(press.canonical_bytes(spec))
    seed={"schema":CANDIDATE_SCHEMA,"status":"PARTIAL_CANDIDATE","title":spec["title"],"specSha256":spec_sha,
          "boxBindingCandidateId":box_candidate["candidateId"],"pageIntakeCandidateId":intake_candidate["candidateId"],
          "pageCount":len(page_records),"renderedParticularCount":sum(len(x["renderedParticulars"]) for x in page_records),
          "blockedParticulars":blocked,"pages":page_records,
          "authority":{"editorialSelection":False,"editionAdmission":False,"publication":False,"houseRelease":False},
          "wrench":{"INPUT":{"boxBindingCandidateId":box_candidate["candidateId"],"pageIntakeCandidateId":intake_candidate["candidateId"]},
                    "TRANSFORMATION":"returned-English solid-surface reletter across all page carriers with deterministic shrink-to-fit",
                    "OUTPUT":{"pages":len(page_records),"rendered":sum(len(x["renderedParticulars"]) for x in page_records),"blocked":len(blocked)},
                    "RESIDUAL":["art/sign blocker pixels remain byte-identical to the PAGE INTAKE parent in this batch pass","source PDF and page manifests remain unchanged"],
                    "LOSS":["solid text regions are replaced by declared flat patches and default-font returned English"],
                    "UNKNOWN":["mask-lettering result for blocked regions","editorial selection","edition admission","publication","house release"],
                    "STOP":"partial returned-English page set only; blocked art/sign regions remain unresolved and no edition is admitted"},
          "laws":copy.deepcopy(spec["laws"])}
    cid="manga-reletter-batch:"+_sha(press.canonical_bytes({"specSha256":spec_sha,"boxBindingCandidateId":box_candidate["candidateId"],"pages":page_records}))
    candidate={**seed,"candidateId":cid}; candidate["candidateHash"]=_sha(press.canonical_bytes(candidate))
    validate_schema(candidate,CANDIDATE_SCHEMA_NAME)
    outputs["candidate.json"]=press.canonical_bytes(candidate)+b"\n"
    outputs["RECEIPT.md"]=receipt(candidate).encode("utf-8")
    return candidate,outputs

def receipt(c):
    lines=[f"# RELETTER BATCH 001 - {c['title']}","",f"Status: {c['status']}",f"Candidate: {c['candidateId']}",
           f"Rendered particulars: {c['renderedParticularCount']}",f"Blocked particulars: {len(c['blockedParticulars'])}","","## Pages",""]
    for p in c["pages"]: lines.append(f"- page {p['page']:02d}: {p['mode']} / {len(p['renderedParticulars'])} returned particulars / {p['outputPngSha256']}")
    lines+=["","## Blockers",""]
    for b in c["blockedParticulars"]: lines.append(f"- {b['segmentId']} / page {b['page']} / {b['surfaceClass']} / {b['rectPx']}")
    lines+=["","## Boundary","",c["wrench"]["STOP"],"","## Laws","",*c["laws"],""]
    return "\n".join(lines)

def _write(path,data):
    if path.exists(): require(path.read_bytes()==data,f"create-only conflict: {path}"); return
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)

def write_outputs(out_dir,files):
    out=Path(out_dir)
    for rel,data in files.items(): _write(out/rel,data)

def verify_outputs(root,spec,out_dir):
    expected,files=build(root,spec); out=Path(out_dir)
    for rel,data in files.items():
        p=out/rel; require(p.is_file(),f"missing output: {rel}"); require(p.read_bytes()==data,f"output does not rebuild: {rel}")
    return expected

def main(argv=None):
    ap=argparse.ArgumentParser(description="RELETTER BATCH 001"); ap.add_argument("--root",default=str(ROOT))
    sub=ap.add_subparsers(dest="cmd",required=True)
    for n in ("compose","verify"):
        p=sub.add_parser(n); p.add_argument("spec"); p.add_argument("out_dir")
    a=ap.parse_args(argv); root=Path(a.root).resolve(); spec=press.read_json(_root_path(root,a.spec,"spec"))
    if a.cmd=="compose":
        c,f=build(root,spec); write_outputs(a.out_dir,f); print(json.dumps({"ok":True,"candidateId":c["candidateId"],"rendered":c["renderedParticularCount"],"blocked":len(c["blockedParticulars"])},indent=2)); return 0
    c=verify_outputs(root,spec,a.out_dir); print(json.dumps({"ok":True,"candidateId":c["candidateId"],"verified":True},indent=2)); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"manga reletter batch failure: {e}",file=sys.stderr); raise SystemExit(2)
