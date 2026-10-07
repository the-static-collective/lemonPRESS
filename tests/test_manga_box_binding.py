import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_box_binding as boxes


class BoxBinding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "relay.json").write_text(json.dumps({
            "schema":"lemonpress/manga-translation-relay/v0","id":"r","title":"R","status":"EXECUTION_WITNESS",
            "source":{"source_id":"s","kind":"issue","title":"S","pages":1,"sha256":"0"*64},
            "route":[{"language":"en","role":"source"},{"language":"ja","role":"pivot"},{"language":"en","role":"return"}],
            "segments":[
                {"segment_id":"p01-01","page":1,"locus":"a","role":"caption","visibility":"complete","source":"A","pivot":"ア","return":"A again","drift":[{"kind":"none","note":"same"}]},
                {"segment_id":"p01-02","page":1,"locus":"b","role":"caption","visibility":"complete","source":"B","pivot":"ビー","return":"B again","drift":[{"kind":"none","note":"same"}]}
            ],
            "authority":{"source_mutation":False,"editorial_selection":False,"edition_admission":False,"publication":False,"house_release":False},
            "laws":["TRANSLATION != REPLACEMENT","RETURN != ORIGINAL","DRIFT != ERROR","LOSS MUST REMAIN VISIBLE","SOURCE SURVIVES RELAY","CLIPPED TEXT != LICENSE TO RECONSTRUCT","LANGUAGE ROUTE IS DECLARED","RENDERING != ADMISSION"]
        }, ensure_ascii=False), encoding="utf-8")
        (self.root / "intake.json").write_text(json.dumps({
            "schema":"lemonpress/manga-page-intake/v0","id":"i","title":"I","status":"EXECUTION_WITNESS","bundle_path":"bundle",
            "source":{"path":"_external/s.pdf","sha256":"1"*64,"media_type":"application/pdf","page_count":1,"revision":"r1"},
            "renderer":{"engine":"pypdfium2","version":"5.8.0","scale_milli":2000,"pixel_mode":"RGB","png_encoder":"lemonpress-stored-deflate-rgb8-v0"},
            "manga":{"work_id":"w","edition_id":"e","issue_id":"i","page_prefix":"page","geometry":{"unit":"um","page":{"x":0,"y":0,"width":100,"height":100},"trim":{"x":0,"y":0,"width":100,"height":100},"bleed":{"left":0,"right":0,"top":0,"bottom":0},"safeArea":{"x":0,"y":0,"width":100,"height":100}}},
            "admission":{"authority_ref":"a","scope":"s","rights_note":"r","grants":{"pixelReuse":True,"pixelHarvest":False,"derivativeReuse":True,"publicationReuse":False,"motionAdaptation":False,"synthesizedSound":False}},
            "expected_pages":[{"page":1,"width":100,"height":100,"pixel_sha256":"2"*64,"png_sha256":"3"*64}],
            "laws":list(boxes.intake.LAWS)
        }), encoding="utf-8")
        self.spec={
            "schema":boxes.SPEC_SCHEMA,"id":"b","title":"B","status":"EXECUTION_WITNESS",
            "basis":"declared_visual_observation","relaySpec":"relay.json","pageIntakeSpec":"intake.json",
            "bindings":[
                {"segmentId":"p01-01","page":1,"rectPx":{"x":0,"y":0,"width":40,"height":20},"surfaceClass":"solid-light"},
                {"segmentId":"p01-02","page":1,"rectPx":{"x":50,"y":0,"width":40,"height":20},"surfaceClass":"art"}
            ],
            "authority":{"editorialSelection":False,"editionAdmission":False,"publication":False,"houseRelease":False},
            "laws":list(boxes.LAWS)
        }

    def test_complete_deterministic_binding(self):
        a=boxes.build(self.root, copy.deepcopy(self.spec))
        b=boxes.build(self.root, copy.deepcopy(self.spec))
        self.assertEqual(a,b)
        self.assertEqual(a["particularCount"],2)
        self.assertEqual(a["solidPatchReadyCount"],1)
        self.assertEqual(len(a["renderStrategyBlockers"]),1)

    def test_missing_particular_refuses(self):
        x=copy.deepcopy(self.spec); x["bindings"].pop()
        with self.assertRaisesRegex(ValueError,"unbound relay particulars"): boxes.build(self.root,x)

    def test_duplicate_particular_refuses(self):
        x=copy.deepcopy(self.spec); x["bindings"][1]["segmentId"]="p01-01"
        with self.assertRaisesRegex(ValueError,"duplicate segment binding"): boxes.build(self.root,x)

    def test_page_mismatch_refuses(self):
        x=copy.deepcopy(self.spec); x["bindings"][0]["page"]=2
        with self.assertRaisesRegex(ValueError,"page mismatch"): boxes.build(self.root,x)

    def test_out_of_bounds_refuses(self):
        x=copy.deepcopy(self.spec); x["bindings"][0]["rectPx"]["width"]=101
        with self.assertRaisesRegex(ValueError,"outside page"): boxes.build(self.root,x)

    def test_overlap_refuses(self):
        x=copy.deepcopy(self.spec); x["bindings"][1]["rectPx"]={"x":20,"y":0,"width":40,"height":20}
        with self.assertRaisesRegex(ValueError,"overlap"): boxes.build(self.root,x)

    def test_create_only_and_verify(self):
        spec_path=self.root/"binding.json"; spec_path.write_text(json.dumps(self.spec),encoding="utf-8")
        candidate=boxes.build(self.root,copy.deepcopy(self.spec))
        boxes.write_outputs(spec_path,candidate)
        boxes.write_outputs(spec_path,candidate)
        verified=boxes.verify_outputs(self.root,spec_path)
        self.assertEqual(candidate["candidateId"],verified["candidateId"])

    def test_schemas(self):
        for name in (boxes.SPEC_SCHEMA_NAME,boxes.CANDIDATE_SCHEMA_NAME):
            document=json.loads((ROOT/"schemas"/name).read_text())
            jsonschema.Draft202012Validator.check_schema(document)

    def test_last_stop_all_68_particulars_are_bound(self):
        real = json.loads((ROOT/"works/the-last-stop-moved-box-binding-001/bindings.json").read_text())
        candidate = boxes.build(ROOT, real)
        self.assertEqual(candidate["particularCount"], 68)
        self.assertEqual(candidate["pageCount"], 10)
        self.assertEqual(candidate["solidPatchReadyCount"], 59)
        self.assertEqual(candidate["surfaceCounts"], {"art": 6, "sign": 3, "solid-dark": 34, "solid-light": 25})
        self.assertEqual(len(candidate["renderStrategyBlockers"]), 9)
        self.assertEqual(len({item["segmentId"] for item in candidate["bindings"]}), 68)


if __name__=="__main__":
    unittest.main()
