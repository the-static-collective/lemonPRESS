import unittest, json
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]

class BatchMaskSchemas(unittest.TestCase):
    def test_schemas_are_valid(self):
        for name in ("manga-reletter-batch-v0.schema.json","manga-reletter-batch-candidate-v0.schema.json","manga-mask-lettering-v0.schema.json","manga-mask-lettering-candidate-v0.schema.json"):
            d=json.loads((ROOT/"schemas"/name).read_text())
            jsonschema.Draft202012Validator.check_schema(d)
    def test_last_stop_declares_59_plus_9(self):
        binding=json.loads((ROOT/"works/the-last-stop-moved-box-binding-001/bindings.json").read_text())
        counts={}
        for b in binding["bindings"]: counts[b["surfaceClass"]]=counts.get(b["surfaceClass"],0)+1
        self.assertEqual(counts,{"solid-dark":34,"solid-light":25,"art":6,"sign":3})
        mask=json.loads((ROOT/"works/the-last-stop-moved-mask-lettering-001/mask.json").read_text())
        self.assertEqual(len(mask["overlays"]),9)
        self.assertEqual(len({x["segmentId"] for x in mask["overlays"]}),9)
        blockers={b["segmentId"] for b in binding["bindings"] if b["surfaceClass"] in ("art","sign")}
        self.assertEqual({x["segmentId"] for x in mask["overlays"]},blockers)
    def test_batch_role_styles_cover_all_roles(self):
        relay=json.loads((ROOT/"works/the-last-stop-moved-translation-relay-001/relay.json").read_text())
        batch=json.loads((ROOT/"works/the-last-stop-moved-reletter-batch-001/batch.json").read_text())
        roles={s["role"] for s in relay["segments"]}
        self.assertTrue(roles <= set(batch["roleStyles"]))
if __name__=="__main__": unittest.main()
