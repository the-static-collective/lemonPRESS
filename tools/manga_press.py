#!/usr/bin/env python3
"""Manga Press 001: an edition grammar, not another house authority lane."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

from press_gate import sha256_file, cmd_new, cmd_add_artifact, cmd_check, load_manifest, save_manifest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {kind: f"lemonpress/manga-{kind}/v0" for kind in
           ("page", "edition", "print-plan", "print-proof", "performance-handoff", "performance-return")}
HASH_KEYS = {kind: key for kind, key in zip(SCHEMAS, (
    "pageHash", "editionHash", "printPlanHash", "proofHash", "handoffHash", "returnHash"))}
GRANTS = ("pixelReuse", "pixelHarvest", "derivativeReuse", "publicationReuse", "motionAdaptation", "synthesizedSound")
LAWS = [
    "FORM != SOURCE", "EDITION != SOURCE", "PAGE ORDER != CANON AUTHORITY",
    "PAGE != PANEL MAP", "PANEL MAP != SEMANTIC UNDERSTANDING", "IMAGE IDENTITY != CHARACTER IDENTITY",
    "PRINT ADMISSION != PERFORMANCE ADMISSION", "PUBLICATION != ANIMATION", "HANDOFF != RENDER",
    "HANDOFF != STAGING", "HANDOFF != EDITORIAL ADMISSION", "HANDOFF != PIXEL HARVEST AUTHORITY UNLESS EXPLICIT",
    "PUBLICATION CONTEXT != STAGING DECISION", "PRESS != HARVESTER", "PUBLICATION PAGE != PARTS DRAWER",
    "IMPOSITION PLAN != PRINTER ACCEPTANCE", "PROOF != PUBLICATION",
    "PRINT DESCENDANT != PERFORMANCE DESCENDANT", "PERFORMANCE DESCENDANT != PRINT SOURCE",
    "SIBLING DESCENDANTS MAY DIFFER", "RETURN != PUBLICATION", "RENDER EXISTS != HOUSE RELEASE",
    "DESCENDANT != ANCESTOR", "THE WORDS MAY MUTATE. THE RELATION MAY CARRY.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_bytes(value):
    # Same sorted-key, UTF-8, compact JSON convention as the audio Composer.
    # Geometry is integer micrometres; no float/NaN or platform-dependent units.
    def walk(item):
        if isinstance(item, dict):
            require(all(isinstance(k, str) for k in item), "JSON keys must be strings")
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        else:
            require(item is None or type(item) in (str, int, bool), "canonical records forbid floating point")
    walk(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def seal(kind, value):
    body = copy.deepcopy(value)
    body["schema"] = SCHEMAS[kind]
    body.pop(HASH_KEYS[kind], None)
    return {**body, HASH_KEYS[kind]: hashlib.sha256(canonical_bytes(body)).hexdigest()}


def verify(kind, record):
    require(isinstance(record, dict) and record.get("schema") == SCHEMAS[kind], f"expected {SCHEMAS[kind]}")
    require(record == seal(kind, record), f"{kind} hash mismatch")


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "expected exact SHA-256")


def edition_declaration_hash(edition):
    # The edition decision witnesses the declaration before its own receipt is
    # attached. Avoid a circular page -> rights -> page admission hash chain.
    return hashlib.sha256(canonical_bytes({k: v for k, v in edition.items()
        if k not in ("editionHash", "editionAdmission")})).hexdigest()


def text(value):
    require(isinstance(value, str) and bool(value.strip()), "expected nonempty identity/reference")


def integer(value, minimum=0):
    require(type(value) is int and value >= minimum, "expected canonical nonnegative integer")


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: use JSON (also valid YAML), not implicit YAML scalars") from exc
    require(isinstance(result, dict), "manifest must be an object")
    return result


def bound_path(root, ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "binding requires path + sha256")
    text(ref["path"])
    digest(ref["sha256"])
    rel = Path(ref["path"])
    require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in ref["path"] and
            rel.as_posix() == ref["path"], "binding must be canonical repository-relative POSIX path")
    path = (root / rel).resolve()
    require(path.is_relative_to(root.resolve()), "binding escapes repository")
    require(path.is_file(), f"missing evidence: {ref['path']}")
    require(sha256_file(path)[0] == ref["sha256"], f"bound bytes changed: {ref['path']}")
    return path


def bound_json(root, ref):
    return read_json(bound_path(root, ref))


def grants(value):
    require(isinstance(value, dict) and set(value) == set(GRANTS), "every rights door must be explicit")
    require(all(type(v) is bool for v in value.values()), "rights must be booleans, never truthy strings")


def subset(child, parent):
    grants(child)
    grants(parent)
    require(all(not child[key] or parent[key] for key in GRANTS), "rights must not expand")


def geometry(value):
    require(isinstance(value, dict) and set(value) == {"unit", "page", "trim", "bleed", "safeArea"}, "geometry shape")
    require(value["unit"] == "um", "geometry must use integer micrometres")
    for name in ("page", "trim", "safeArea"):
        box = value[name]
        require(isinstance(box, dict) and set(box) == {"x", "y", "width", "height"}, f"{name} rectangle")
        for key in ("x", "y"):
            integer(box[key])
        for key in ("width", "height"):
            integer(box[key], 1)
    page, trim, safe = (value[k] for k in ("page", "trim", "safeArea"))
    require(page["x"] == page["y"] == 0, "page origin must be zero")
    bleed = value["bleed"]
    require(isinstance(bleed, dict) and set(bleed) == {"top", "right", "bottom", "left"}, "explicit bleed edges")
    for v in bleed.values():
        integer(v)
    require(trim["x"] == bleed["left"] and trim["y"] == bleed["top"] and
            page["width"] == trim["width"] + bleed["left"] + bleed["right"] and
            page["height"] == trim["height"] + bleed["top"] + bleed["bottom"], "trim/bleed incompatible with page")
    require(safe["x"] >= trim["x"] and safe["y"] >= trim["y"] and
            safe["x"] + safe["width"] <= trim["x"] + trim["width"] and
            safe["y"] + safe["height"] <= trim["y"] + trim["height"], "safe area outside trim")


def references(root, items):
    require(isinstance(items, list), "references must be an array")
    for ref in items:
        bound_path(root, ref)


def page_identity(edition, page):
    return {"workId": edition["workId"], "editionId": edition["editionId"],
            "editionHash": edition["editionHash"], "issueId": edition["issueId"],
            "pageId": page["pageId"], "pageHash": page["pageHash"],
            "sourceImageSha256": None if page["sourceImage"] is None else page["sourceImage"]["sha256"]}


def validate_page(root, edition, page, admission):
    verify("page", page)
    required = {"editionId", "issueId", "pageId", "logicalPageNumber", "physicalSheetRelation", "kind",
                "sourceImage", "geometry", "panelMap", "narrativeReferences", "dialogueCaptionReferences",
                "continuityGroupReferences", "rightsSource", "grants", "internalSemantics", "sourceLineage"}
    require(set(page) == required | {"schema", "pageHash"}, "incomplete or unsupported page manifest")
    require(page["editionId"] == edition["editionId"] and page["issueId"] == edition["issueId"], "page belongs to another edition/issue")
    text(page["pageId"])
    if page["logicalPageNumber"] is not None:
        integer(page["logicalPageNumber"], 1)
    require(page["physicalSheetRelation"] is None, "physical sheet relation is assigned by this one-leaf composer")
    require(page["kind"] in ("content", "intentional-blank"), "unknown page kind")
    require(page["internalSemantics"] in ("unknown", "externally-referenced"), "no semantic understanding inferred")
    geometry(page["geometry"])
    require(page["geometry"] == edition["geometry"], "incompatible print geometry")
    if page["sourceImage"] is not None:
        bound_path(root, page["sourceImage"])
    if page["kind"] == "intentional-blank":
        require(page["sourceImage"] is None, "intentional blank may not conceal source pixels")
    if page["panelMap"] is not None:
        bound_path(root, page["panelMap"])
    for name in ("narrativeReferences", "dialogueCaptionReferences", "continuityGroupReferences", "sourceLineage"):
        references(root, page[name])
    require(page["rightsSource"] == edition["admission"], "page rights must reference this exact admission")
    subset(page["grants"], admission["grants"])


def validate_edition(root, edition):
    verify("edition", edition)
    required = {"workId", "workManifest", "source", "admission", "editionAdmission", "editionId", "title", "issueId", "issueSequence",
                "readingDirection", "geometry", "colorIntent", "pageCount", "covers", "pageOrdering", "spreads",
                "sourceLineage", "pageManifests", "printIntent", "digitalIntent", "performanceHandoffPolicy",
                "rightsReferences", "grants"}
    require(set(edition) == required | {"schema", "editionHash"}, "incomplete or unsupported edition manifest")
    for key in ("workId", "editionId", "title", "issueId"):
        text(edition[key])
    integer(edition["issueSequence"])
    require(edition["readingDirection"] in ("ltr", "rtl"), "reading direction must be explicit ltr or rtl")
    geometry(edition["geometry"])
    require(edition["colorIntent"] in ("monochrome", "grayscale", "color"), "explicit color intent required")
    work = bound_json(root, edition["workManifest"])
    admission = bound_json(root, edition["admission"])
    edition_admission = bound_json(root, edition["editionAdmission"])
    bound_path(root, edition["source"])
    require(work.get("work_id") == edition["workId"] and work.get("status") in ("admitted", "published"), "work must be admitted")
    require(set(work.get("lanes", [])) <= {"physical", "digital", "crawler", "archive"} and "physical" in work["lanes"], "manga is a form, not a house lane")
    wa = work.get("admission", {})
    require(wa.get("state") == "admitted" and wa.get("receipt") == edition["admission"]["path"], "work admission identity mismatch")
    require(admission.get("state") == "admitted" and admission.get("work_id") == edition["workId"], "source must be explicitly admitted")
    require(edition_admission.get("state") == "admitted" and edition_admission.get("work_id") == edition["workId"] and
            edition_admission.get("edition_id") == edition["editionId"] and edition_admission.get("issue_id") == edition["issueId"] and
            edition_admission.get("declaration_sha256") == edition_declaration_hash(edition), "edition declaration must be explicitly admitted")
    text(edition_admission.get("authority_ref"))
    text(admission.get("authority_ref"))
    require(admission.get("source_sha256") == edition["source"]["sha256"] and
            admission.get("source_revision") == wa.get("source_revision"), "admitted source identity mismatch")
    subset(edition["grants"], admission["grants"])
    for name in ("sourceLineage", "rightsReferences"):
        references(root, edition[name])
        require(bool(edition[name]), f"{name} must retain provenance")
    require(edition["source"] in edition["sourceLineage"] and edition["admission"] in edition["rightsReferences"], "source and rights ancestry required")
    policy = edition["performanceHandoffPolicy"]
    require(set(policy) == {"grants", "allowedAdaptationScope", "externalEditorialAuthorityReference"}, "bounded performance policy required")
    subset(policy["grants"], edition["grants"])
    require(isinstance(policy["allowedAdaptationScope"], list) and all(isinstance(x, str) and x.strip() for x in policy["allowedAdaptationScope"]), "adaptation scope must be explicit")
    if policy["externalEditorialAuthorityReference"] is not None:
        text(policy["externalEditorialAuthorityReference"])
    require(isinstance(edition["digitalIntent"], dict) and set(edition["digitalIntent"]) == {"mode", "publicationAuthority"}
            and edition["digitalIntent"]["mode"] in ("held", "page-sequence")
            and edition["digitalIntent"]["publicationAuthority"] == "none", "digital intent is not release authority")
    pages = {}
    for ref in edition["pageManifests"]:
        page = bound_json(root, ref)
        validate_page(root, edition, page, admission)
        require(page["pageId"] not in pages, "duplicate page identity")
        pages[page["pageId"]] = page
    require(bool(pages), "edition requires pages")
    require(set(edition_admission.get("admitted_page_hashes", [])) == {p["pageHash"] for p in pages.values()}, "page hashes differ from edition admission")
    integer(edition["pageCount"], 1)
    require(isinstance(edition["pageOrdering"], list) and edition["pageCount"] == len(edition["pageOrdering"]), "page count/order mismatch")
    seen_ids, uses = set(), {}
    placements = []
    for position, placement in enumerate(edition["pageOrdering"], 1):
        require(set(placement) == {"placementId", "pageId", "repeatOf"}, "placement must explicitly declare repeatOf, including null")
        text(placement["placementId"])
        require(placement["placementId"] not in seen_ids, "duplicate placement identity")
        require(placement["pageId"] in pages, "placement references unknown page")
        first = uses.get(placement["pageId"])
        require(placement["repeatOf"] == first, "accidental duplicate placement or invalid repeat declaration")
        uses.setdefault(placement["pageId"], placement["placementId"])
        seen_ids.add(placement["placementId"])
        odd = position % 2 == 1
        placements.append({**placement, "position": position, "parity": "odd" if odd else "even",
                           "leaf": (position + 1) // 2, "face": "recto" if odd else "verso",
                           "side": ("right" if odd else "left") if edition["readingDirection"] == "ltr" else ("left" if odd else "right"),
                           "parent": page_identity(edition, pages[placement["pageId"]])})
    require(set(uses) == set(pages), "unplaced page manifest")
    require(len(placements) % 2 == 0, "odd leaf geometry requires an explicitly admitted blank; no auto-padding")
    covers = edition["covers"]
    require(isinstance(covers, dict) and set(covers) == {"front", "insideFront", "insideBack", "back"}, "four explicit cover relationships required")
    require(len(placements) >= 4 and [covers[k] for k in ("front", "insideFront", "insideBack", "back")] == [placements[0]["placementId"], placements[1]["placementId"], placements[-2]["placementId"], placements[-1]["placementId"]], "cover placement mismatch")
    require(len(set(covers.values())) == 4, "cover placements must be distinct")
    lookup = {p["placementId"]: p for p in placements}
    spread_ids, spread_uses = set(), set()
    require(isinstance(edition["spreads"], list), "spreads must be explicit")
    for spread in edition["spreads"]:
        require(set(spread) == {"spreadId", "placements"}, "spread declaration shape")
        text(spread["spreadId"])
        require(spread["spreadId"] not in spread_ids, "duplicate spread identity")
        spread_ids.add(spread["spreadId"])
        pair = spread["placements"]
        require(isinstance(pair, list) and len(pair) == 2 and all(x in lookup for x in pair), "spread requires two known placements")
        a, b = [lookup[x] for x in pair]
        require(a["position"] % 2 == 0 and b["position"] == a["position"] + 1, "spread must join consecutive facing even/odd pages")
        require(not (set(pair) & spread_uses), "placement belongs to multiple spreads")
        require(not (set(pair) & set(covers.values())), "interior spread may not consume a cover")
        spread_uses.update(pair)
    intent = edition["printIntent"]
    require(set(intent) == {"selection", "sheetLayout", "requiredBlanks"}, "explicit selected print intent required")
    require(intent["sheetLayout"] == "one-leaf-two-sides", "vendor signature/folding rules are not implemented")
    selected = bound_json(root, intent["selection"])
    require(selected.get("work_id") == edition["workId"] and selected.get("state") in ("human_selected", "external_fixed"), "Physical Composer proposal is not selection")
    if selected["state"] == "human_selected":
        require(selected.get("composition_version") == "physical-composer-001" and isinstance(selected.get("selection_receipt"), dict), "Physical Composer selection receipt required")
    else:
        text(selected.get("authority_ref"))
    blanks = {p["placementId"] for p in placements if pages[p["pageId"]]["kind"] == "intentional-blank"}
    require(isinstance(intent["requiredBlanks"], list) and len(intent["requiredBlanks"]) == len(set(intent["requiredBlanks"])) and set(intent["requiredBlanks"]) == blanks, "required blank declarations mismatch")
    return pages, placements


def make_handoff(edition, pages, placements, page_ids=None):
    requested = set(pages if page_ids is None else page_ids)
    require(bool(requested) and requested <= pages.keys(), "handoff needs known pages")
    ordered = list(dict.fromkeys(p["pageId"] for p in placements if p["pageId"] in requested))
    policy = edition["performanceHandoffPolicy"]
    effective = {key: policy["grants"][key] and all(pages[p]["grants"][key] for p in ordered) for key in GRANTS}
    return seal("performance-handoff", {
        "workId": edition["workId"], "editionId": edition["editionId"], "editionHash": edition["editionHash"],
        "issueId": edition["issueId"], "source": edition["source"], "admission": edition["admission"], "editionAdmission": edition["editionAdmission"],
        "pages": [{"identity": page_identity(edition, pages[p]), "sourceImage": pages[p]["sourceImage"],
                   "narrativeReferences": pages[p]["narrativeReferences"],
                   "dialogueCaptionReferences": pages[p]["dialogueCaptionReferences"],
                   "panelMap": pages[p]["panelMap"], "internalSemantics": pages[p]["internalSemantics"],
                   "rightsSource": pages[p]["rightsSource"], "grants": pages[p]["grants"]} for p in ordered],
        "orderingContext": {"readingDirection": edition["readingDirection"], "placements": placements, "spreads": edition["spreads"]},
        "allowedAdaptationScope": policy["allowedAdaptationScope"], "grants": effective,
        "externalEditorialAuthorityReference": policy["externalEditorialAuthorityReference"],
        "authority": {"render": False, "staging": False, "editorialAdmission": False, "houseRelease": False},
        "targetVocabulary": {
            "pageSource": "haunted-blender/page-source/v1", "narrativeSource": "haunted-blender/narrative-particular-source/v1",
            "proposal": "haunted-blender/staging-proposal/v1", "admission": "haunted-blender/editorial-admission/v1",
            "plan": "haunted-blender/particular-performance-plan/v1", "ownedPixels": "haunted-blender/owned-pixel-donor/v1"},
        "laws": LAWS,
    })


def compose(root, edition):
    pages, placements = validate_edition(root, edition)
    reverse_covers = {v: k for k, v in edition["covers"].items()}
    sides = [{**p, "role": reverse_covers.get(p["placementId"], "intentional-blank" if pages[p["pageId"]]["kind"] == "intentional-blank" else "interior"),
              "sourceImage": pages[p["pageId"]]["sourceImage"]} for p in placements]
    spreads = []
    for spread in edition["spreads"]:
        pair = [next(p for p in sides if p["placementId"] == name) for name in spread["placements"]]
        spreads.append({**spread, "left": next(p["placementId"] for p in pair if p["side"] == "left"),
                        "right": next(p["placementId"] for p in pair if p["side"] == "right"),
                        "trimWidthUm": edition["geometry"]["trim"]["width"] * 2,
                        "trimHeightUm": edition["geometry"]["trim"]["height"]})
    plan = seal("print-plan", {"workId": edition["workId"], "editionId": edition["editionId"],
        "editionHash": edition["editionHash"], "issueId": edition["issueId"], "readingDirection": edition["readingDirection"],
        "geometry": edition["geometry"], "colorIntent": edition["colorIntent"], "selection": edition["printIntent"]["selection"],
        "sheetLayout": "one-leaf-two-sides", "sides": sides, "spreads": spreads,
        "printerAcceptance": "unknown", "signatureImposition": "not-declared", "publicationAuthority": "none", "laws": LAWS})
    proof = seal("print-proof", {"editionHash": edition["editionHash"], "printPlanHash": plan["printPlanHash"],
        "state": "structural-proof-only", "INPUT": {"work": edition["workManifest"], "source": edition["source"], "admission": edition["admission"], "editionAdmission": edition["editionAdmission"], "pages": edition["pageManifests"]},
        "TRANSFORMATION": "validated exact admitted pages; assigned ordered leaf sides and declared facing spreads",
        "OUTPUT": {"printPlanHash": plan["printPlanHash"], "pageCount": len(sides)},
        "RESIDUAL": ["source bytes and internal semantics remain unchanged"], "LOSS": [],
        "UNKNOWN": ["visual QA", "PDF rendering", "printer acceptance", "paper", "binding", "folding/signatures"],
        "STOP": "before rendered proof, printer acceptance, or house release", "publicationAuthority": "none", "laws": LAWS})
    handoff = make_handoff(edition, pages, placements)
    return {"edition": edition, "pages": sorted(pages.values(), key=lambda p: p["pageId"]),
            "printPlan": plan, "printProof": proof, "handoff": handoff}


def verify_handoff(root, edition, handoff):
    verify("performance-handoff", handoff)
    pages, placements = validate_edition(root, edition)
    ids = [p["identity"]["pageId"] for p in handoff["pages"]]
    require(len(ids) == len(set(ids)), "duplicate handoff page")
    require(handoff == make_handoff(edition, pages, placements, ids), "handoff differs from independently rebuilt evidence/policy")


def accept_return(root, edition, handoff, declaration):
    verify_handoff(root, edition, handoff)
    require(set(declaration) == {"handoffHash", "consumedPages", "descendantId", "renderer", "artifacts", "preservedPages", "omittedMaterial", "mutations"}, "return declaration shape; no publication commands")
    require(declaration["handoffHash"] == handoff["handoffHash"], "return belongs to another handoff")
    text(declaration["descendantId"])
    text(declaration["renderer"])
    known = {p["identity"]["pageId"]: p["identity"] for p in handoff["pages"]}
    consumed = declaration["consumedPages"]
    require(isinstance(consumed, list) and bool(consumed), "return needs consumed identities")
    require(all(isinstance(p, dict) and known.get(p.get("pageId")) == p for p in consumed), "consumed page identity mismatch")
    require(len({p["pageId"] for p in consumed}) == len(consumed), "duplicate consumed page")
    require(declaration["preservedPages"] == consumed, "return must preserve exact consumed ancestry")
    require(isinstance(declaration["artifacts"], list) and bool(declaration["artifacts"]), "return requires artifacts")
    for ref in declaration["artifacts"]:
        bound_path(root, ref)
    for key in ("omittedMaterial", "mutations"):
        require(isinstance(declaration[key], list) and all(isinstance(x, str) and x.strip() for x in declaration[key]), f"renderer must explicitly declare {key}")
    return seal("performance-return", {**declaration, "parents": consumed, "descendantKind": "performance",
        "verification": "artifact bytes and ancestry only; renderer declarations are not independently proven",
        "publicationStateChange": None, "authority": {"houseRelease": False, "editorialAdmission": False}, "laws": LAWS})


def persist_records(out, records):
    encoded = {name: canonical_bytes(value) for name, value in records.items()}
    # Check the whole set before creating anything. Existing conflicting bytes refuse.
    for name, data in encoded.items():
        path = out / name
        require(not path.exists() or path.read_bytes() == data, f"create-only conflict: {name}")
    out.mkdir(parents=True, exist_ok=True)
    for name, data in encoded.items():
        path = out / name
        try:
            with path.open("xb") as stream:
                stream.write(data)
        except FileExistsError:
            require(path.read_bytes() == data, f"create-only conflict: {name}")


def write_bundle(out, bundle):
    persist_records(out, {"edition.json": bundle["edition"], "pages.json": bundle["pages"],
        "print-plan.json": bundle["printPlan"], "print-proof.json": bundle["printProof"], "performance-handoff.json": bundle["handoff"]})


def export_gate(root, edition, out):
    bundle = compose(root, edition)
    require(not out.exists(), "Press Gate export is create-only; choose a new packet path")
    cmd_new(argparse.Namespace(out=str(out), work_id=edition["workId"], edition_id=edition["editionId"], title=edition["title"],
        source_revision=edition["source"]["sha256"], admission_receipt=edition["admission"]["path"], format="manga-issue",
        rights=bound_json(root, edition["workManifest"])["rights"]))
    write_bundle(out / "manga", bundle)
    for name in ("edition", "pages", "print-plan", "print-proof", "performance-handoff"):
        cmd_add_artifact(argparse.Namespace(packet=str(out), file=str(out / "manga" / f"{name}.json"), role=f"manga-{name}", name=None, replace=False))
    # Carry every byte binding into the existing portable packet, with original
    # repository-relative names retained under artifacts/evidence/.
    refs = {}
    def collect(value):
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                refs[value["path"]] = value
            else:
                for child in value.values():
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(bundle)
    for rel, ref in sorted(refs.items()):
        src = bound_path(root, ref)
        name = "evidence/" + rel
        (out / "artifacts" / name).parent.mkdir(parents=True, exist_ok=True)
        cmd_add_artifact(argparse.Namespace(packet=str(out), file=str(src), role="manga-bound-evidence", name=name, replace=False))
    manifest = load_manifest(out)
    manifest["production"].update({"pages": edition["pageCount"], "geometry_um": edition["geometry"], "color": edition["colorIntent"],
        "held_decisions": ["PDF rendering", "visual QA", "binding", "paper", "printer/vendor", "signature/folding rules"]})
    manifest["qa"]["notes"] = ["Manga structural proof only; not approved_print_proof."]
    save_manifest(out, manifest)
    require(cmd_check(argparse.Namespace(packet=str(out))) == 0, "Press Gate failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("compose", "gate"):
        p = sub.add_parser(command)
        p.add_argument("edition", type=Path)
        p.add_argument("out", type=Path)
    p = sub.add_parser("verify")
    p.add_argument("edition", type=Path)
    p.add_argument("bundle", type=Path)
    p = sub.add_parser("return")
    p.add_argument("edition", type=Path)
    p.add_argument("handoff", type=Path)
    p.add_argument("declaration", type=Path)
    p.add_argument("out", type=Path)
    p = sub.add_parser("seal", help="hash a declared page/edition; this does not admit it")
    p.add_argument("kind", choices=("page", "edition"))
    p.add_argument("input", type=Path)
    p.add_argument("out", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "seal":
            persist_records(args.out.parent, {args.out.name: seal(args.kind, read_json(args.input))})
        elif args.command == "compose":
            write_bundle(args.out, compose(args.root, read_json(args.edition)))
        elif args.command == "gate":
            export_gate(args.root, read_json(args.edition), args.out)
        elif args.command == "verify":
            bundle = compose(args.root, read_json(args.edition))
            expected = {"edition.json": bundle["edition"], "pages.json": bundle["pages"], "print-plan.json": bundle["printPlan"],
                        "print-proof.json": bundle["printProof"], "performance-handoff.json": bundle["handoff"]}
            for name, value in expected.items():
                require((args.bundle / name).read_bytes() == canonical_bytes(value), f"verification failure: {name}")
        else:
            result = accept_return(args.root, read_json(args.edition), read_json(args.handoff), read_json(args.declaration))
            persist_records(args.out.parent, {args.out.name: result})
        print(f"MANGA PRESS: PASS ({args.command})")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"MANGA PRESS: REFUSE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
