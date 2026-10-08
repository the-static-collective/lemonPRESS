#!/usr/bin/env python3
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).parent
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
m=json.loads((ROOT/"source-manifest.json").read_text())
r=json.loads((ROOT/"route.json").read_text())
errors=[]
if m.get("law")!="TRANSFORM != SEVER": errors.append("missing core law")
ids=[s["slot"] for s in m["sources"]]
if len(ids)!=5 or len(set(ids))!=5: errors.append("source set must contain five unique slots")
for s in m["sources"]:
    if len(s.get("sha256",""))!=64: errors.append(f"bad digest: {s['slot']}")
ops=r.get("operations",[])
kinds=[o.get("kind") for o in ops]
required=["translate.through","remix.sequence","style.stack","lemonpress.press","relatte.crossing","local.render"]
if kinds!=required: errors.append("route is missing, reordered, or hiding an operation")
cross=next((o for o in ops if o.get("kind")=="relatte.crossing"),{})
if cross.get("authority_claim")!="NONE" or cross.get("admission_claim")!="NONE": errors.append("crossing inherited authority/admission")
foreign=next((o for o in ops if o.get("kind")=="local.render"),{})
if foreign.get("requires_lemonpress") is not False: errors.append("foreign renderer improperly depends on LemonPRESS")
if foreign.get("similarity_requirement")!="NONE": errors.append("visual similarity became an identity test")
root=hashlib.sha256(canon({"sources":m["sources"],"operations":ops})).hexdigest()
print(json.dumps({"specimen":m["specimen"],"status":"FAIL" if errors else "PASS","declared_root":root,"errors":errors},indent=2))
sys.exit(bool(errors))
