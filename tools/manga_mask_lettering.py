#!/usr/bin/env python3
"""MASK LETTERING 001: explicit polygon-matte lettering for art/sign blockers; never inpainting."""
from __future__ import annotations
import argparse, copy, hashlib, io, json, sys
from pathlib import Path
from typing import Any
import jsonschema
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import manga_press as press
import manga_box_binding as boxes
import manga_translation_relay as relay
import manga_reletter as reletter
import manga_reletter_batch as batch

SPEC_SCHEMA_NAME="manga-mask-lettering-v0.schema.json"
CANDIDATE_SCHEMA_NAME="manga-mask-lettering-candidate-v0.schema.json"
SPEC_SCHEMA="lemonpress/manga-mask-lettering/v0"
CANDIDATE_SCHEMA="lemonpress/manga-mask-lettering-candidate/v0"
LAWS=[
 "MASK != INPAINTING","OVERLAY != RECOVERY","ALPHA IS DECLARED","POLYGON != PERSPECTIVE MODEL",
 "BLOCKER COVERAGE MUST BE EXACT","RETURN != ORIGINAL","SOURCE ART SURVIVES OUTSIDE MASK",
 "MASK LETTERING != SELECTION","CANDIDATE != EDITION","OUTPUT != PUBLICATION"
]

def require(c,m):
    if not c: raise ValueError(m)
def _schema(n): return json.loads((ROOT/"schemas"/n).read_text(encoding="utf-8"))
def validate_schema(v,n):
    d=_schema(n); jsonschema.Draft202012Validator.check_schema(d)
    try: jsonschema.Draft202012Validator(d).validate(v)
    except jsonschema.ValidationError as e:
        loc=".".join(str(x) for x in e.absolute_path) or "<root>"; raise ValueError(f"schema validation failed at {loc}: {e.message}") from e
def _root_path(root,rel,label):
    p=Path(rel); require(isinstance(rel,str) and rel.strip() and not p.is_absolute() and ".." not in p.parts and "\\" not in rel and p.as_posix()==rel,f"{label} path")
    out=(root/p).resolve(); require(out.is_relative_to(root.resolve()),f"{label} escapes root"); require(out.is_file(),f"missing {label}: {rel}"); return out
def _sha(b): return hashlib.sha256(b).hexdigest()

def _bbox(poly,w,h):
    require(isinstance(poly,list) and len(poly)>=3,"polygon requires at least 3 points")
    pts=[]
    for p in poly:
        require(isinstance(p,list) and len(p)==2 and all(type(v) is int for v in p),"polygon point shape")
        x,y=p; require(0<=x<w and 0<=y<h,"polygon point outside page"); pts.append((x,y))
    xs=[x for x,_ in pts]; ys=[y for _,y in pts]
    box=(min(xs),min(ys),max(xs)+1,max(ys)+1); require(box[2]>box[0] and box[3]>box[1],"empty polygon")
    return pts,box

def _fit(draw,text,box,style):
    x0,y0,x1,y1=box; pad=style["paddingPx"]; iw=x1-x0-2*pad; ih=y1-y0-2*pad; require(iw>0 and ih>0,"padding consumes polygon box")
    for size in range(style["maxFontPx"],style["minFontPx"]-1,-1):
        font=ImageFont.load_default(size=size); lines=reletter._wrap(draw,text,font,iw)
        b=draw.textbbox((0,0),"Ag",font=font); lh=max(1,b[3]-b[1]); total=len(lines)*lh+max(0,len(lines)-1)*style["lineSpacingPx"]
        if total<=ih: return font,lines,lh,size
    raise ValueError(f"mask text overflow: {text}")

def _load(root,spec):
    validate_schema(spec,SPEC_SCHEMA_NAME); require(spec["schema"]==SPEC_SCHEMA,f"expected {SPEC_SCHEMA}"); require(spec["laws"]==LAWS,"mask law set mismatch")
    batch_spec_path=_root_path(root,spec["batchSpec"],"batchSpec"); batch_spec=press.read_json(batch_spec_path)
    batch_candidate=batch.verify_outputs(root,batch_spec,_root_path(root,spec["batchOutputCandidate"],"batchOutputCandidate").parent)
    box_spec=press.read_json(_root_path(root,spec["boxBindingSpec"],"boxBindingSpec")); box_candidate=boxes.build(root,box_spec)
    relay_spec=relay.read_json(_root_path(root,box_spec["relaySpec"],"relaySpec")); relay_candidate=relay.build_candidate(relay_spec)
    return batch_candidate,box_candidate,relay_candidate

def build(root,spec):
    root=Path(root).resolve(); batch_candidate,box_candidate,relay_candidate=_load(root,spec)
    blockers={b["segmentId"]:b for b in box_candidate["renderStrategyBlockers"]}
    overlays={o["segmentId"]:o for o in spec["overlays"]}
    require(len(overlays)==len(spec["overlays"]),"duplicate mask segmentId")
    require(set(overlays)==set(blockers),"mask overlays must cover blocker set exactly")
    segments={s["segment_id"]:s for s in relay_candidate["segments"]}
    batch_dir=_root_path(root,spec["batchOutputCandidate"],"batchOutputCandidate").parent
    by_page={}
    for o in spec["overlays"]: by_page.setdefault(o["page"],[]).append(o)
    outputs={}; page_records=[]; transforms=[]
    for p in batch_candidate["pages"]:
        n=p["page"]; src=batch_dir/f"pages/page-{n:02d}.png"; require(src.is_file(),f"missing batch page {n}")
        require(_sha(src.read_bytes())==p["outputPngSha256"],f"batch page hash mismatch: {n}")
        with Image.open(src) as im: canvas=im.convert("RGBA")
        draw=ImageDraw.Draw(canvas); applied=[]
        for o in by_page.get(n,[]):
            sid=o["segmentId"]; require(blockers[sid]["page"]==n,f"mask page mismatch: {sid}"); seg=segments[sid]; text=seg["return"]; require(all(ord(ch)<128 for ch in text),f"mask v0 ASCII only: {sid}")
            pts,box=_bbox(o["polygonPx"],canvas.width,canvas.height)
            layer=Image.new("RGBA",canvas.size,(0,0,0,0)); ld=ImageDraw.Draw(layer)
            ld.polygon(pts,fill=tuple(o["matteRgba"]))
            canvas=Image.alpha_composite(canvas,layer); draw=ImageDraw.Draw(canvas)
            font,lines,lh,font_px=_fit(draw,text,box,o["style"])
            x0,y0,x1,y1=box; y=y0+o["style"]["paddingPx"]
            for line in lines:
                tw=reletter._text_width(draw,line,font)
                align=o["style"]["align"]
                x=x0+o["style"]["paddingPx"] if align=="left" else (x0+(x1-x0-tw)//2 if align=="center" else x1-o["style"]["paddingPx"]-tw)
                draw.text((x,y),line,font=font,fill=tuple(o["foregroundRgba"])); y+=lh+o["style"]["lineSpacingPx"]
            t={"segmentId":sid,"page":n,"surfaceClass":blockers[sid]["surfaceClass"],"polygonPx":copy.deepcopy(o["polygonPx"]),
               "matteRgba":copy.deepcopy(o["matteRgba"]),"foregroundRgba":copy.deepcopy(o["foregroundRgba"]),
               "fontPx":font_px,"returnedText":text,"returnedTextSha256":_sha(text.encode())}
            transforms.append(t); applied.append(sid)
        out=io.BytesIO(); canvas.save(out,format="PNG",compress_level=9,optimize=False); data=out.getvalue()
        outputs[f"pages/page-{n:02d}.png"]=data
        page_records.append({"page":n,"inputPngSha256":p["outputPngSha256"],"outputPngSha256":_sha(data),"maskedParticulars":applied})
    spec_sha=_sha(press.canonical_bytes(spec))
    seed={"schema":CANDIDATE_SCHEMA,"status":"COMPLETE_VISUAL_CANDIDATE","title":spec["title"],"specSha256":spec_sha,
          "batchCandidateId":batch_candidate["candidateId"],"boxBindingCandidateId":box_candidate["candidateId"],
          "relayCandidateId":relay_candidate["candidate_id"],"pageCount":len(page_records),
          "solidRenderedParticularCount":batch_candidate["renderedParticularCount"],"maskedParticularCount":len(transforms),
          "totalReturnedParticularCount":batch_candidate["renderedParticularCount"]+len(transforms),
          "pages":page_records,"transformations":transforms,
          "authority":{"editorialSelection":False,"editionAdmission":False,"publication":False,"houseRelease":False},
          "wrench":{"INPUT":{"batchCandidateId":batch_candidate["candidateId"],"blockers":len(blockers)},
                    "TRANSFORMATION":"explicit semi-transparent polygon matte + returned-English text over every art/sign blocker",
                    "OUTPUT":{"pages":len(page_records),"solidRendered":batch_candidate["renderedParticularCount"],"maskedRendered":len(transforms)},
                    "RESIDUAL":["all pixels outside declared polygons survive from the batch parent","no source art is reconstructed or inferred beneath matte pixels"],
                    "LOSS":["declared polygon matte overlays cover or blend source pixels inside the mask","axis-aligned text inside polygon bounds is not a perspective reconstruction"],
                    "UNKNOWN":["human aesthetic preference","editorial selection","edition admission","publication","house release"],
                    "STOP":"complete visual candidate only; no returned wording or page is admitted as an edition"},
          "laws":copy.deepcopy(spec["laws"])}
    cid="manga-mask-lettering:"+_sha(press.canonical_bytes({"specSha256":spec_sha,"batchCandidateId":batch_candidate["candidateId"],"pages":page_records,"transformations":transforms}))
    c={**seed,"candidateId":cid}; c["candidateHash"]=_sha(press.canonical_bytes(c)); validate_schema(c,CANDIDATE_SCHEMA_NAME)
    outputs["candidate.json"]=press.canonical_bytes(c)+b"\n"; outputs["RECEIPT.md"]=receipt(c).encode("utf-8")
    return c,outputs

def receipt(c):
    lines=[f"# MASK LETTERING 001 - {c['title']}","",f"Status: {c['status']}",f"Candidate: {c['candidateId']}",
           f"Solid returned particulars: {c['solidRenderedParticularCount']}",f"Masked returned particulars: {c['maskedParticularCount']}",
           f"Total returned particulars: {c['totalReturnedParticularCount']}","","## Masks",""]
    for t in c["transformations"]: lines.append(f"- {t['segmentId']} / page {t['page']} / {t['surfaceClass']} / matte {t['matteRgba']} / font {t['fontPx']}")
    lines+=["","## Boundary","",c["wrench"]["STOP"],"","## Laws","",*c["laws"],""]
    return "\n".join(lines)

def _write(path,data):
    if path.exists(): require(path.read_bytes()==data,f"create-only conflict: {path}"); return
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
def write_outputs(out_dir,files):
    out=Path(out_dir)
    for rel,data in files.items(): _write(out/rel,data)
def verify_outputs(root,spec,out_dir):
    c,files=build(root,spec); out=Path(out_dir)
    for rel,data in files.items():
        p=out/rel; require(p.is_file(),f"missing output: {rel}"); require(p.read_bytes()==data,f"output does not rebuild: {rel}")
    return c
def main(argv=None):
    ap=argparse.ArgumentParser(description="MASK LETTERING 001"); ap.add_argument("--root",default=str(ROOT))
    sub=ap.add_subparsers(dest="cmd",required=True)
    for n in ("compose","verify"):
        p=sub.add_parser(n); p.add_argument("spec"); p.add_argument("out_dir")
    a=ap.parse_args(argv); root=Path(a.root).resolve(); spec=press.read_json(_root_path(root,a.spec,"spec"))
    if a.cmd=="compose":
        c,f=build(root,spec); write_outputs(a.out_dir,f); print(json.dumps({"ok":True,"candidateId":c["candidateId"],"returned":c["totalReturnedParticularCount"]},indent=2)); return 0
    c=verify_outputs(root,spec,a.out_dir); print(json.dumps({"ok":True,"candidateId":c["candidateId"],"verified":True},indent=2)); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"manga mask lettering failure: {e}",file=sys.stderr); raise SystemExit(2)
