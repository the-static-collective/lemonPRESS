"""Materialize the versioned, renderer-neutral JSON contracts (dev tool only)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://github.com/the-static-collective/lemonPRESS/schemas/"
S = {"type": "string", "minLength": 1}
N = {"type": "null"}
I = {"type": "integer", "minimum": 0}
POS = {"type": "integer", "minimum": 1}
H = {"type": "string", "pattern": "^[0-9a-f]{64}$"}


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def arr(item, **kwargs):
    return {"type": "array", "items": item, **kwargs}


def nullable(item):
    return {"anyOf": [item, N]}


def ref(name):
    return {"$ref": "#/$defs/" + name}


GRANT_NAMES = ["pixelReuse", "pixelHarvest", "derivativeReuse", "publicationReuse", "motionAdaptation", "synthesizedSound"]
RECT = obj({"x": I, "y": I, "width": POS, "height": POS})
DEFS = {
    "binding": obj({"path": S, "sha256": H}),
    "geometry": obj({"unit": {"const": "um"}, "page": RECT, "trim": RECT,
                     "bleed": obj({k: I for k in ("left", "right", "top", "bottom")}), "safeArea": RECT}),
    "grants": obj({k: {"type": "boolean"} for k in GRANT_NAMES}),
    "identity": obj({"workId": S, "editionId": S, "editionHash": H, "issueId": S, "pageId": S,
                     "pageHash": H, "sourceImageSha256": nullable(H)}),
    "placement": obj({"placementId": S, "pageId": S, "repeatOf": nullable(S)}),
    "spread": obj({"spreadId": S, "placements": arr(S, minItems=2, maxItems=2, uniqueItems=True)}),
}
DEFS["performedPlacement"] = obj({**DEFS["placement"]["properties"], "position": POS, "parity": {"enum": ["odd", "even"]},
    "leaf": POS, "face": {"enum": ["recto", "verso"]}, "side": {"enum": ["left", "right"]}, "parent": ref("identity")})
B = ref("binding")
G = ref("geometry")
R = ref("grants")
LAWS = arr(S)
PAGE = {
    "editionId": S, "issueId": S, "pageId": S, "logicalPageNumber": nullable(POS), "physicalSheetRelation": N,
    "kind": {"enum": ["content", "intentional-blank"]}, "sourceImage": nullable(B), "geometry": G,
    "panelMap": nullable(B), "narrativeReferences": arr(B), "dialogueCaptionReferences": arr(B),
    "continuityGroupReferences": arr(B), "rightsSource": B, "grants": R,
    "internalSemantics": {"enum": ["unknown", "externally-referenced"]}, "sourceLineage": arr(B),
}
EDITION = {
    "workId": S, "workManifest": B, "source": B, "admission": B, "editionAdmission": B,
    "editionId": S, "title": S, "issueId": S, "issueSequence": I, "readingDirection": {"enum": ["ltr", "rtl"]},
    "geometry": G, "colorIntent": {"enum": ["monochrome", "grayscale", "color"]}, "pageCount": POS,
    "covers": obj({k: S for k in ("front", "insideFront", "insideBack", "back")}), "pageOrdering": arr(ref("placement"), minItems=4),
    "spreads": arr(ref("spread")), "sourceLineage": arr(B, minItems=1), "pageManifests": arr(B, minItems=1),
    "printIntent": obj({"selection": B, "sheetLayout": {"const": "one-leaf-two-sides"}, "requiredBlanks": arr(S, uniqueItems=True)}),
    "digitalIntent": obj({"mode": {"enum": ["held", "page-sequence"]}, "publicationAuthority": {"const": "none"}}),
    "performanceHandoffPolicy": obj({"grants": R, "allowedAdaptationScope": arr(S), "externalEditorialAuthorityReference": nullable(S)}),
    "rightsReferences": arr(B, minItems=1), "grants": R,
}
HANDOFF = {
    "workId": S, "editionId": S, "editionHash": H, "issueId": S, "source": B, "admission": B, "editionAdmission": B,
    "pages": arr(obj({"identity": ref("identity"), "sourceImage": nullable(B), "narrativeReferences": arr(B),
        "dialogueCaptionReferences": arr(B), "panelMap": nullable(B), "internalSemantics": PAGE["internalSemantics"], "rightsSource": B, "grants": R}), minItems=1),
    "orderingContext": obj({"readingDirection": EDITION["readingDirection"], "placements": arr(ref("performedPlacement")), "spreads": arr(ref("spread"))}),
    "allowedAdaptationScope": arr(S), "grants": R, "externalEditorialAuthorityReference": nullable(S),
    "authority": obj({k: {"const": False} for k in ("render", "staging", "editorialAdmission", "houseRelease")}),
    "targetVocabulary": obj({k: S for k in ("pageSource", "narrativeSource", "proposal", "admission", "plan", "ownedPixels")}), "laws": LAWS,
}
RETURN_DECLARATION = {"handoffHash": H, "consumedPages": arr(ref("identity"), minItems=1), "descendantId": S, "renderer": S,
    "artifacts": arr(B, minItems=1), "preservedPages": arr(ref("identity"), minItems=1), "omittedMaterial": arr(S), "mutations": arr(S)}
RETURN = {**RETURN_DECLARATION, "parents": arr(ref("identity"), minItems=1), "descendantKind": {"const": "performance"},
    "verification": S, "publicationStateChange": N, "authority": obj({k: {"const": False} for k in ("houseRelease", "editorialAdmission")}), "laws": LAWS}
PLAN = {"workId": S, "editionId": S, "editionHash": H, "issueId": S, "readingDirection": EDITION["readingDirection"], "geometry": G,
    "colorIntent": EDITION["colorIntent"], "selection": B, "sheetLayout": {"const": "one-leaf-two-sides"},
    "sides": arr(obj({**DEFS["performedPlacement"]["properties"], "role": {"enum": ["front", "insideFront", "insideBack", "back", "interior", "intentional-blank"]}, "sourceImage": nullable(B)})),
    "spreads": arr(obj({**DEFS["spread"]["properties"], "left": S, "right": S, "trimWidthUm": POS, "trimHeightUm": POS})),
    "printerAcceptance": {"const": "unknown"}, "signatureImposition": {"const": "not-declared"}, "publicationAuthority": {"const": "none"}, "laws": LAWS}
PROOF = {"editionHash": H, "printPlanHash": H, "state": {"const": "structural-proof-only"},
    "INPUT": obj({"work": B, "source": B, "admission": B, "editionAdmission": B, "pages": arr(B)}), "TRANSFORMATION": S,
    "OUTPUT": obj({"printPlanHash": H, "pageCount": POS}), "RESIDUAL": arr(S), "LOSS": arr(S), "UNKNOWN": arr(S), "STOP": S,
    "publicationAuthority": {"const": "none"}, "laws": LAWS}


def build():
    common = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE + "manga-common.schema.json", "$defs": DEFS}
    (ROOT / "schemas/manga-common.schema.json").write_text(json.dumps(common, indent=2) + "\n")
    for kind, key, properties in (("page", "pageHash", PAGE), ("edition", "editionHash", EDITION),
            ("performance-handoff", "handoffHash", HANDOFF), ("performance-return", "returnHash", RETURN),
            ("print-plan", "printPlanHash", PLAN), ("print-proof", "proofHash", PROOF)):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE + f"manga-{kind}.schema.json",
            "title": f"lemonpress/manga-{kind}/v0", "$defs": {name: {"$ref": "manga-common.schema.json#/$defs/" + name} for name in DEFS},
            **obj({"schema": {"const": f"lemonpress/manga-{kind}/v0"}, **properties, key: H})}
        (ROOT / "schemas" / f"manga-{kind}.schema.json").write_text(json.dumps(schema, indent=2) + "\n")


if __name__ == "__main__":
    build()
