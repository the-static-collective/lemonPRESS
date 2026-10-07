#!/usr/bin/env python3
import argparse,json
from pathlib import Path
INDEX_SCHEMA="lemonpress/manga-corpus-index/v0"
ISSUE_SCHEMA="lemonpress/manga-source-issue/v0"
ANTHOLOGY_SCHEMA="lemonpress/manga-anthology-sequence/v0"
LAWS=["ANTHOLOGY != SOURCE MUTATION","READING ORDER != OWNERSHIP","ORDER != ANCESTRY","SLOT != PAGE IDENTITY","DUPLICATION != NEW SOURCE","SEQUENCE != ADMISSION","CANDIDATE != RELEASE"]
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def pairs(index_path):
    index_path=Path(index_path); index=load(index_path)
    if index.get("schema")!=INDEX_SCHEMA: raise ValueError("unexpected index schema")
    root=index_path.resolve().parents[2]; out=[]
    for seq,ref in enumerate(index["issues"],1):
        if ref["issueSequence"]!=seq: raise ValueError("issue sequence drift")
        m=load(root/ref["manifestPath"])
        if m.get("schema")!=ISSUE_SCHEMA or m["issueSequence"]!=seq or m["issueId"]!=ref["issueId"] or m["title"]!=ref["title"]: raise ValueError("issue manifest mismatch")
        if m["pageCount"]!=len(m["pages"]): raise ValueError("page count mismatch")
        for slot,p in enumerate(m["pages"],1):
            if p["slot"]!=slot: raise ValueError("page slot drift")
        out.append((ref,m))
    return index,out
def verify(index_path):
    index,ps=pairs(index_path); ic=len(ps); pc=sum(m["pageCount"] for _,m in ps)
    if index["issueCount"]!=ic or index["pageCount"]!=pc: raise ValueError("index count mismatch")
    if index["invariants"]!={"issueCount":ic,"pageCount":pc}: raise ValueError("invariant failed")
    return index,ps
def build(index_path,title="THE HOUSE TAKES ATTENDANCE",subtitle="Collected Manga 001–019"):
    index,ps=verify(index_path); slots=[]; n=0; order=[]
    for ref,m in ps:
        order.append(m["issueId"])
        for p in m["pages"]:
            n+=1; slots.append({"slot":n,"issueSequence":m["issueSequence"],"pageSequence":p["slot"],"issueId":m["issueId"],"pageId":p["pageId"],"issueManifestPath":ref["manifestPath"],"displayTitle":p["displayTitle"],"source":p["source"]})
    return {"schema":ANTHOLOGY_SCHEMA,"sequenceId":f"{index['corpusId']}:anthology-001","status":"CANDIDATE","title":title,"subtitle":subtitle,"sourceIndex":{"path":"works/manga-index-001/index.json","corpusId":index["corpusId"]},"issueCount":index["issueCount"],"pageCount":index["pageCount"],"issueOrder":order,"slots":slots,"authority":{"sourceMutation":False,"admission":False,"publication":False,"release":False},"laws":LAWS}
def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    v=sp.add_parser("verify"); v.add_argument("index",type=Path)
    p=sp.add_parser("press"); p.add_argument("index",type=Path); p.add_argument("output",type=Path); p.add_argument("--title",default="THE HOUSE TAKES ATTENDANCE"); p.add_argument("--subtitle",default="Collected Manga 001–019")
    a=sp.add_parser("verify-anthology"); a.add_argument("index",type=Path); a.add_argument("anthology",type=Path)
    x=ap.parse_args()
    if x.cmd=="verify":
        i,ps=verify(x.index); print(f"OK {len(ps)} issues / {i['pageCount']} pages"); return
    if x.cmd=="press":
        o=build(x.index,x.title,x.subtitle); x.output.parent.mkdir(parents=True,exist_ok=True); x.output.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(f"WROTE {x.output} ({o['issueCount']} issues / {o['pageCount']} pages)"); return
    actual=load(x.anthology); expected=build(x.index)
    if actual!=expected: raise ValueError("anthology candidate does not reconstruct from source manifests")
    print(f"OK anthology {actual['issueCount']} issues / {actual['pageCount']} pages")
if __name__=="__main__": main()
