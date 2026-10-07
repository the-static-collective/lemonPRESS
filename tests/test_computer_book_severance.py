import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from computer_book import ComputerBookError
from computer_book_severance import probe_severed

SOURCE = REPO / "specimens" / "computer-book-001" / "fragments" / "002-loss-is-visible.json"
SEVERED = REPO / "specimens" / "computer-book-002" / "severed" / "fragment.json"


class ComputerBookSeveranceTests(unittest.TestCase):
    def isolated_copy(self):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "fragment.json"
        shutil.copyfile(SEVERED, path)
        return tmp, path

    def test_severed_fragment_is_exact_copy_of_001(self):
        self.assertEqual(SOURCE.read_bytes(), SEVERED.read_bytes())

    def test_fragment_alone_preserves_identity_and_ancestry(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        result = probe_severed(path)
        self.assertEqual(result["work_id"], "lemonpress:computer-book-001")
        self.assertEqual(result["edition_id"], "lemonpress:computer-book-001:crawler:001")
        self.assertEqual(result["fragment_id"], "002-loss-is-visible")
        self.assertEqual(result["body_identity"], "DECLARED_BY_FRAGMENT")
        self.assertTrue(result["ancestry"])
        self.assertEqual(result["authority"], "none")

    def test_missing_manifest_is_unavailable_but_existence_unknown(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        manifest = probe_severed(path)["manifest"]
        self.assertEqual(manifest["availability"], "UNAVAILABLE_LOCAL")
        self.assertEqual(manifest["existence"], "UNKNOWN")

    def test_missing_neighbor_is_unknown_not_nonexistent(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        edge = probe_severed(path)["continuations"][0]
        self.assertEqual(edge["availability"], "UNAVAILABLE_LOCAL")
        self.assertEqual(edge["existence"], "UNKNOWN")

    def test_whole_body_remains_unknown(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        result = probe_severed(path)
        self.assertEqual(result["whole_body_state"], "UNKNOWN")
        self.assertFalse(result["laws"]["fragment_is_book"])
        self.assertFalse(result["laws"]["unknown_is_empty"])

    def test_fragment_cannot_escalate_authority_after_severance(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        fragment = json.loads(path.read_text())
        fragment["authority"]["level"] = "admitted"
        path.write_text(json.dumps(fragment))
        with self.assertRaisesRegex(ComputerBookError, "cannot grant authority"):
            probe_severed(path)

    def test_missing_identity_refuses_instead_of_guessing(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        fragment = json.loads(path.read_text())
        del fragment["work_id"]
        path.write_text(json.dumps(fragment))
        with self.assertRaisesRegex(ComputerBookError, "missing fields: work_id"):
            probe_severed(path)

    def test_embedded_whole_book_claim_does_not_override_probe(self):
        tmp, path = self.isolated_copy()
        self.addCleanup(tmp.cleanup)
        fragment = json.loads(path.read_text())
        fragment["whole_body_state"] = "COMPLETE"
        fragment["authority_claim"] = "canonical"
        path.write_text(json.dumps(fragment))
        result = probe_severed(path)
        self.assertEqual(result["whole_body_state"], "UNKNOWN")
        self.assertEqual(result["authority"], "none")


if __name__ == "__main__":
    unittest.main()
