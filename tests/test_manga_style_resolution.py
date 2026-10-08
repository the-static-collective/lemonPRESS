import copy
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import manga_style_resolve as style


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.profiles = [style.read(p) for p in sorted((style.ROOT / "works/styles").glob("*.json"))]
        self.stack = style.read(style.ROOT / "works/style-stacks/RENJI_JP_RELAY_COLOR_001/stack.json")

    def test_founding_stacks_repeat_exactly(self):
        for path in (style.ROOT / "works/style-stacks").glob("*/stack.json"):
            stack = style.read(path)
            a = style.resolve(stack, self.profiles)
            self.assertEqual(style.canon(a), style.canon(style.resolve(stack, self.profiles)))
            style.validate(a, "resolution")
            self.assertEqual(a["authority"], style.AUTHORITY)
            self.assertIn("WORLD TEXT != DIALOGUE", a["laws"])
            self.assertIn("GLOSS != REPLACEMENT", a["laws"])

    def test_order_override_and_profile_change_affect_candidate(self):
        baseline = style.resolve(self.stack, self.profiles)
        parent = "a" * 64
        variants = []
        changed = copy.deepcopy(self.stack)
        changed["styles"].reverse()
        variants.append(style.resolve(changed, self.profiles))
        changed = copy.deepcopy(self.stack)
        changed["styles"][0]["overrides"] = {"visualPalette.light": "another world"}
        variants.append(style.resolve(changed, self.profiles))
        profiles = copy.deepcopy(self.profiles)
        next(p for p in profiles if p["id"] == "HOUSE_WARMTH_001")["behavior"]["tone"]["warmth"] = "quiet welcome"
        variants.append(style.resolve(self.stack, profiles))
        for resolution in variants:
            self.assertNotEqual(resolution["resolutionHash"], baseline["resolutionHash"])
            self.assertNotEqual(style.candidate_identity(parent, resolution), style.candidate_identity(parent, baseline))

    def test_tampered_resolution_and_create_only_conflict_refuse(self):
        value = style.resolve(self.stack, self.profiles)
        value["resolvedBehavior"]["visualPalette"]["light"] = "tampered"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            style.candidate_identity("a" * 64, value)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "resolution.json"
            style.write_create_only(path, b"first")
            style.write_create_only(path, b"first")
            with self.assertRaisesRegex(ValueError, "create-only"):
                style.write_create_only(path, b"second")
