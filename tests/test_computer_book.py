import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from computer_book import ComputerBookError, inspect_fragment, reconstruct, verify  # noqa: E402

SPECIMEN = REPO / "specimens" / "computer-book-001"


class ComputerBookTests(unittest.TestCase):
    def copy_specimen(self):
        tmp = tempfile.TemporaryDirectory()
        dest = Path(tmp.name) / "specimen"
        shutil.copytree(SPECIMEN, dest)
        return tmp, dest

    def test_reference_specimen_verifies(self):
        result = verify(SPECIMEN)
        self.assertEqual(result["fragment_count"], 3)
        self.assertEqual(result["authority"], "none")

    def test_every_fragment_knows_its_body(self):
        for path in sorted((SPECIMEN / "fragments").glob("*.json")):
            fragment = inspect_fragment(path)
            self.assertEqual(fragment["work_id"], "lemonpress:computer-book-001")
            self.assertEqual(fragment["edition_id"], "lemonpress:computer-book-001:crawler:001")
            self.assertEqual(fragment["retrieval"]["warning"], "FRAGMENT != BOOK")
            self.assertEqual(fragment["authority"]["level"], "none")
            self.assertTrue(fragment["ancestry"])
            self.assertTrue(fragment["uncertainty"])

    def test_arbitrary_entry_reconstructs_same_body(self):
        expected = {"001-enter-anywhere", "002-loss-is-visible", "003-order-is-not-ancestry"}
        for start in expected:
            result = reconstruct(SPECIMEN, start)
            self.assertEqual(set(result["reachable_set"]), expected)
            self.assertEqual(result["authority"], "none")

    def test_manifest_reordering_does_not_change_identity_or_authority(self):
        tmp, dest = self.copy_specimen()
        self.addCleanup(tmp.cleanup)
        path = dest / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["fragments"] = list(reversed(manifest["fragments"]))
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        result = verify(dest)
        self.assertEqual(result["work_id"], "lemonpress:computer-book-001")
        self.assertEqual(result["authority"], "none")

    def test_fragment_cannot_claim_authority(self):
        tmp, dest = self.copy_specimen()
        self.addCleanup(tmp.cleanup)
        path = dest / "fragments" / "001-enter-anywhere.json"
        fragment = json.loads(path.read_text())
        fragment["authority"]["level"] = "admitted"
        path.write_text(json.dumps(fragment, indent=2) + "\n")
        with self.assertRaisesRegex(ComputerBookError, "cannot grant authority"):
            verify(dest)

    def test_identity_mismatch_is_rejected(self):
        tmp, dest = self.copy_specimen()
        self.addCleanup(tmp.cleanup)
        path = dest / "fragments" / "002-loss-is-visible.json"
        fragment = json.loads(path.read_text())
        fragment["work_id"] = "lemonpress:other-work"
        path.write_text(json.dumps(fragment, indent=2) + "\n")
        with self.assertRaisesRegex(ComputerBookError, "work_id does not match"):
            verify(dest)

    def test_missing_local_target_is_rejected(self):
        tmp, dest = self.copy_specimen()
        self.addCleanup(tmp.cleanup)
        path = dest / "fragments" / "003-order-is-not-ancestry.json"
        fragment = json.loads(path.read_text())
        fragment["retrieval"]["continuations"][0]["target"] = "999-missing"
        path.write_text(json.dumps(fragment, indent=2) + "\n")
        with self.assertRaisesRegex(ComputerBookError, "unresolved local target"):
            verify(dest)

    def test_relations_file_must_match_fragment_local_edges(self):
        tmp, dest = self.copy_specimen()
        self.addCleanup(tmp.cleanup)
        path = dest / "relations.jsonl"
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaisesRegex(ComputerBookError, "relation disagreement"):
            verify(dest)


if __name__ == "__main__":
    unittest.main()
