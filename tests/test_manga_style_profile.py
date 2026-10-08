import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import manga_style_resolve as style


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.profiles = [style.read(p) for p in sorted((style.ROOT / "works/styles").glob("*.json"))]
        self.language = copy.deepcopy(next(p for p in self.profiles if p["id"] == "LANGUAGE_THROUGH_MANGA_001"))

    def test_founding_profiles_validate(self):
        self.assertEqual(len(self.profiles), 8)
        for profile in self.profiles:
            style.validate_profile(profile)

    def test_unknown_fields_and_domains_refuse(self):
        for edit in [lambda p: p["domains"].update({"plot": "own"}), lambda p: p["behavior"]["languageBehavior"].update({"secret": True})]:
            value = copy.deepcopy(self.language)
            edit(value)
            with self.assertRaises(ValueError):
                style.validate_profile(value)

    def test_ambiguous_declaration_refuses(self):
        self.language["domains"]["languageBehavior"] = "none"
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            style.validate_profile(self.language)

    def test_missing_law_and_authority_assertion_refuse(self):
        for key in style.AUTHORITY:
            value = copy.deepcopy(self.language)
            value["authority"][key] = True
            with self.assertRaises(ValueError):
                style.validate_profile(value)
        self.language["laws"].remove("GLOSS != REPLACEMENT")
        with self.assertRaisesRegex(ValueError, "missing"):
            style.validate_profile(self.language)

    def test_gloss_and_world_text_cannot_collapse(self):
        self.language["behavior"]["textChannels"]["dialogue"]["gloss"] = "ja"
        with self.assertRaisesRegex(ValueError, "gloss collapse"):
            style.validate_profile(self.language)
        self.language["behavior"]["textChannels"]["dialogue"]["gloss"] = "en"
        self.language["behavior"]["textChannels"]["world_text"]["purpose"] = "dialogue"
        with self.assertRaisesRegex(ValueError, "channel identity"):
            style.validate_profile(self.language)
