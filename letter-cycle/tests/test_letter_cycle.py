"""Executable local seam checks for LETTER CYCLE 001."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "letter_cycle.py"
ISSUE = ROOT / "letter-cycle" / "001" / "issue.json"
REPLY = ROOT / "letter-cycle" / "001" / "synthetic-response.json"


def run(*args, good=True):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True)
    if good and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    if not good and result.returncode == 0:
        raise AssertionError("unexpected success: " + result.stdout)
    return result


class LetterCycleTest(unittest.TestCase):
    def test_proof_has_three_verified_pdf_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "proof"
            run("proof", ISSUE, "--out", out)
            m = json.loads((out / "manifest.json").read_text())
            self.assertEqual(m["state"], "proof_prepared")
            self.assertEqual({x["role"] for x in m["artifacts"]},
                             {"letter", "branch_card", "return_slip"})
            import hashlib
            for artifact in m["artifacts"]:
                body = (out / artifact["path"]).read_bytes()
                self.assertTrue(body.startswith(b"%PDF-1.4"))
                self.assertEqual(hashlib.sha256(body).hexdigest(), artifact["sha256"])
            run("proof", ISSUE, "--out", out, good=False)

    def test_simulated_return_to_next_candidate_is_private(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            run("proof", ISSUE, "--out", p / "proof")
            run("receive", REPLY, "--manifest", p / "proof" / "manifest.json",
                "--out", p / "private")
            held = json.loads((p / "private" / "intake.json").read_text())
            self.assertEqual(held["state"], "received_held")
            self.assertEqual(held["channel_evidence"], "not_verified")
            run("next", "--hold", p / "private", "--topic", "crease",
                "--out", p / "next.json", good=False)
            run("decide", "--hold", p / "private", "--decision", "consider",
                "--reviewer", "test", good=False)
            run("decide", "--hold", p / "private", "--decision", "consider",
                "--reviewer", "test", "--human-confirmed")
            run("next", "--hold", p / "private", "--topic", "crease",
                "--out", p / "next.json")
            candidate = json.loads((p / "next.json").read_text())
            self.assertIs(candidate["publishable"], False)
            self.assertEqual(candidate["parent_issue_id"], "LP-LTR-001")
            self.assertNotIn("message", candidate)

    def test_no_quote_permission_refuses_consideration(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            run("proof", ISSUE, "--out", p / "proof")
            response = json.loads(REPLY.read_text())
            response["consent"]["may_quote_publicly"] = False
            (p / "reply.json").write_text(json.dumps(response))
            run("receive", p / "reply.json", "--manifest", p / "proof" / "manifest.json",
                "--out", p / "private")
            run("decide", "--hold", p / "private", "--decision", "consider",
                "--reviewer", "test", "--human-confirmed", good=False)

    def test_private_records_refused_inside_house(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            run("proof", ISSUE, "--out", p / "proof")
            run("receive", REPLY, "--manifest", p / "proof" / "manifest.json",
                "--out", ROOT / "letter-cycle" / "forbidden-intake", good=False)
            self.assertFalse((ROOT / "letter-cycle" / "forbidden-intake").exists())

    def test_issue_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            run("proof", ISSUE, "--out", p / "proof")
            response = json.loads(REPLY.read_text())
            response["issue_id"] = "LP-LTR-999"
            (p / "bad.json").write_text(json.dumps(response))
            run("receive", p / "bad.json", "--manifest", p / "proof" / "manifest.json",
                "--out", p / "private", good=False)


if __name__ == "__main__":
    unittest.main()
