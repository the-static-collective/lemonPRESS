import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_sequence as sequence


class MangaSequence(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "schema": "lemonpress/manga-remix-sequence/v0",
            "id": "sequence-test-001",
            "title": "Sequence Test 001",
            "status": "EXECUTION_WITNESS",
            "parents": [
                {"parent_id": "page:a", "kind": "page", "title": "A"},
                {"parent_id": "page:b", "kind": "page", "title": "B"},
                {"parent_id": "candidate:c", "kind": "candidate", "title": "C"},
            ],
            "sequence": [
                {"slot": 1, "source_ref": "page:a", "selection": {"kind": "whole"}},
                {"slot": 2, "source_ref": "page:b", "selection": {"kind": "whole"}},
                {"slot": 3, "source_ref": "candidate:c", "selection": {"kind": "whole"}},
            ],
            "authority": {
                "editorial_selection": False,
                "edition_admission": False,
                "publication": False,
                "house_release": False,
            },
            "laws": list(sequence.LAWS),
        }

    def test_deterministic_replay(self):
        a = sequence.build_candidate(copy.deepcopy(self.spec))
        b = sequence.build_candidate(copy.deepcopy(self.spec))
        self.assertEqual(a["candidate_id"], b["candidate_id"])
        self.assertEqual(a["sequence_sha256"], b["sequence_sha256"])
        self.assertEqual(sequence.canonical_bytes(a), sequence.canonical_bytes(b))

    def test_order_changes_identity(self):
        a = sequence.build_candidate(copy.deepcopy(self.spec))
        changed = copy.deepcopy(self.spec)
        changed["sequence"][0], changed["sequence"][1] = changed["sequence"][1], changed["sequence"][0]
        b = sequence.build_candidate(changed)
        self.assertNotEqual(a["candidate_id"], b["candidate_id"])
        self.assertNotEqual(a["sequence_sha256"], b["sequence_sha256"])

    def test_omission_preserves_provenance(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"] = changed["sequence"][:2]
        candidate = sequence.build_candidate(changed)
        self.assertEqual(candidate["parents"], changed["parents"])
        self.assertIn("omitted from descendant order: candidate:c", candidate["wrench"]["LOSS"])

    def test_duplication_allowed(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"].append(
            {"slot": 4, "source_ref": "page:a", "selection": {"kind": "panel", "panel_id": "p3"}}
        )
        candidate = sequence.build_candidate(changed)
        self.assertEqual(candidate["slots"][-1]["source_ref"], "page:a")

    def test_unknown_source_rejected(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"][1]["source_ref"] = "page:missing"
        with self.assertRaisesRegex(ValueError, "unknown source_ref"):
            sequence.build_candidate(changed)

    def test_duplicate_slot_rejected(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"][1]["slot"] = 1
        with self.assertRaisesRegex(ValueError, "duplicate slot"):
            sequence.build_candidate(changed)

    def test_bad_region_rejected(self):
        for selection in (
            {"kind": "region", "x": -0.1, "y": 0, "width": 0.2, "height": 0.2},
            {"kind": "region", "x": 0.8, "y": 0, "width": 0.3, "height": 0.2},
            {"kind": "region", "x": 0, "y": 0.8, "width": 0.2, "height": 0.3},
        ):
            changed = copy.deepcopy(self.spec)
            changed["sequence"][0]["selection"] = selection
            with self.assertRaises(ValueError):
                sequence.build_candidate(changed)

    def test_panel_without_panel_id_rejected(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"][0]["selection"] = {"kind": "panel"}
        with self.assertRaisesRegex(ValueError, "schema validation failed"):
            sequence.build_candidate(changed)

    def test_slot_order_preserved_exactly(self):
        changed = copy.deepcopy(self.spec)
        changed["sequence"] = [
            {"slot": 30, "source_ref": "candidate:c", "selection": {"kind": "whole"}},
            {"slot": 10, "source_ref": "page:a", "selection": {"kind": "whole"}},
            {"slot": 20, "source_ref": "page:b", "selection": {"kind": "whole"}},
        ]
        candidate = sequence.build_candidate(changed)
        self.assertEqual(candidate["slots"], changed["sequence"])

    def test_parent_identity_and_order_never_rewritten(self):
        before = copy.deepcopy(self.spec["parents"])
        candidate = sequence.build_candidate(self.spec)
        self.assertEqual(self.spec["parents"], before)
        self.assertEqual(candidate["parents"], before)
        self.assertIsNot(candidate["parents"], self.spec["parents"])

    def test_schema_documents_and_generated_candidate_validate(self):
        sequence_schema = json.loads((ROOT / "schemas/manga-remix-sequence-v0.schema.json").read_text())
        candidate_schema = json.loads((ROOT / "schemas/manga-sequence-candidate-v0.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(sequence_schema)
        jsonschema.Draft202012Validator.check_schema(candidate_schema)
        candidate = sequence.build_candidate(copy.deepcopy(self.spec))
        jsonschema.Draft202012Validator(sequence_schema).validate(self.spec)
        jsonschema.Draft202012Validator(candidate_schema).validate(candidate)

    def test_create_only_outputs_and_verify(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            spec_path = work / "sequence.json"
            spec_path.write_text(json.dumps(self.spec, indent=2) + "\n")
            candidate = sequence.build_candidate(copy.deepcopy(self.spec))
            sequence.write_outputs(spec_path, candidate)
            sequence.write_outputs(spec_path, candidate)
            verified = sequence.verify_outputs(spec_path)
            self.assertEqual(candidate["candidate_id"], verified["candidate_id"])
            (work / "candidate.json").write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "create-only conflict"):
                sequence.write_outputs(spec_path, candidate)

    def test_committed_home_grows_open_specimens_rebuild(self):
        first = sequence.verify_outputs(ROOT / "works/home-grows-open-sequence-001/sequence.json")
        second = sequence.verify_outputs(ROOT / "works/home-grows-open-sequence-002/sequence.json")
        self.assertNotEqual(first["candidate_id"], second["candidate_id"])
        self.assertEqual(first["parents"], second["parents"])


if __name__ == "__main__":
    unittest.main()
