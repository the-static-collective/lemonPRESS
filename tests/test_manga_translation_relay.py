import copy, json, sys, tempfile, unittest
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import manga_translation_relay as relay

class TranslationRelay(unittest.TestCase):
    def setUp(self):
        self.spec={"schema":relay.SPEC_SCHEMA,"id":"relay-test-001","title":"Relay Test","status":"EXECUTION_WITNESS","source":{"source_id":"source:a","kind":"issue","title":"A","pages":2,"sha256":"0"*64},"route":[{"language":"en","role":"source"},{"language":"ja","role":"pivot"},{"language":"en","role":"return"}],"segments":[{"segment_id":"p01-01","page":1,"locus":"caption","role":"caption","visibility":"complete","source":"Leave one place unclaimed.","pivot":"ひとつの場所を、誰のものにもせず残しておく。","return":"Leave one place belonging to no one.","drift":[{"kind":"ownership_shift","note":"unclaimed becomes belonging to no one"}]}],"authority":{"source_mutation":False,"editorial_selection":False,"edition_admission":False,"publication":False,"house_release":False},"laws":list(relay.LAWS)}
    def test_deterministic(self):
        self.assertEqual(relay.build_candidate(copy.deepcopy(self.spec)),relay.build_candidate(copy.deepcopy(self.spec)))
    def test_return_changes_identity(self):
        a=relay.build_candidate(copy.deepcopy(self.spec)); x=copy.deepcopy(self.spec); x["segments"][0]["return"]="Leave one place unowned."; b=relay.build_candidate(x); self.assertNotEqual(a["candidate_id"],b["candidate_id"])
    def test_source_survives(self):
        before=copy.deepcopy(self.spec); relay.build_candidate(self.spec); self.assertEqual(self.spec,before)
    def test_clipped_recorded_as_loss(self):
        x=copy.deepcopy(self.spec); x["segments"][0]["visibility"]="clipped"; c=relay.build_candidate(x); self.assertTrue(any("clipped" in s for s in c["wrench"]["LOSS"]))
    def test_bad_page_rejected(self):
        x=copy.deepcopy(self.spec); x["segments"][0]["page"]=3
        with self.assertRaisesRegex(ValueError,"outside source range"): relay.build_candidate(x)
    def test_duplicate_segment_rejected(self):
        x=copy.deepcopy(self.spec); x["segments"].append(copy.deepcopy(x["segments"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate segment_id"): relay.build_candidate(x)
    def test_schemas(self):
        for f in ["manga-translation-relay-v0.schema.json","manga-translation-candidate-v0.schema.json"]:
            jsonschema.Draft202012Validator.check_schema(json.loads((ROOT/"schemas"/f).read_text()))
    def test_last_stop_witness_builds(self):
        spec=relay.read_json(ROOT/"works/the-last-stop-moved-translation-relay-001/relay.json")
        candidate=relay.build_candidate(spec)
        self.assertEqual(68,len(candidate["segments"]))
        self.assertTrue(candidate["candidate_id"].startswith("manga-translation-relay:"))
if __name__=="__main__": unittest.main()
