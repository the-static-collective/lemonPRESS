import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import manga_style_resolve as style


class StackTests(unittest.TestCase):
    def setUp(self):
        self.profiles = [style.read(p) for p in sorted((style.ROOT / "works/styles").glob("*.json"))]
        self.stack = style.read(style.ROOT / "works/style-stacks/RENJI_JP_RELAY_COLOR_001/stack.json")

    def test_unknown_style_refuses(self):
        self.stack["styles"][0]["styleId"] = "MISSING"
        with self.assertRaisesRegex(ValueError, "unknown style"):
            style.resolve(self.stack, self.profiles)

    def conflicting_palette(self):
        self.stack["styles"].append({**copy.deepcopy(self.stack["styles"][0]), "styleId": "RENJI_MONO_SOURCE_001", "priority": 100})

    def test_ownership_requires_explicit_precedence(self):
        self.conflicting_palette()
        with self.assertRaisesRegex(ValueError, "ownership conflict"):
            style.resolve(self.stack, self.profiles)
        self.stack["resolutionPolicy"] = "explicit-priority"
        result = style.resolve(self.stack, self.profiles)
        self.assertEqual(result["resolvedBehavior"]["visualPalette"]["colors"], ["#101010", "#f4f1e8"])
        self.stack["styles"][-1]["priority"] = self.stack["styles"][0]["priority"]
        with self.assertRaisesRegex(ValueError, "tied ownership"):
            style.resolve(self.stack, self.profiles)

    def test_suggestion_never_overwrites_owner(self):
        # Language suggests receipts at high priority, but the receipt overlay owns them.
        self.stack["styles"][1]["priority"] = 999
        self.stack["styles"].append({**copy.deepcopy(self.stack["styles"][0]), "styleId": "BUREAUCRATIC_RECEIPT_001", "priority": -100})
        result = style.resolve(self.stack, self.profiles)
        self.assertEqual(result["resolvedDomains"]["worldMotifs.receipts"]["styleId"], "BUREAUCRATIC_RECEIPT_001")

    def test_override_wins_and_invalid_or_duplicate_override_refuses(self):
        self.stack["styles"][0]["overrides"] = {"visualPalette.light": "receipt glow"}
        self.assertEqual(style.resolve(self.stack, self.profiles)["resolvedBehavior"]["visualPalette"]["light"], "receipt glow")
        self.stack["styles"][0]["overrides"]["visualPalette.unknown"] = "invented"
        with self.assertRaises(ValueError):
            style.resolve(self.stack, self.profiles)
        self.stack["styles"][0]["overrides"] = {"tone.warmth": "unscoped"}
        with self.assertRaisesRegex(ValueError, "unscoped"):
            style.resolve(self.stack, self.profiles)

    def test_channel_and_domain_scoping(self):
        self.stack["styles"] = [copy.deepcopy(self.stack["styles"][1])]
        entry = self.stack["styles"][0]
        entry.update(mode="channel-scoped", domainMask=["textChannels"], channelMask=["dialogue", "world_text"])
        result = style.resolve(self.stack, self.profiles)
        self.assertEqual(set(result["resolvedBehavior"]), {"textChannels"})
        self.assertEqual(set(result["resolvedBehavior"]["textChannels"]), {"dialogue", "world_text"})
        entry.update(mode="domain-scoped", domainMask=["languageBehavior"])
        del entry["channelMask"]
        self.assertEqual(set(style.resolve(self.stack, self.profiles)["resolvedBehavior"]), {"languageBehavior"})

    def test_absent_renderer_required_behavior_refuses(self):
        with self.assertRaisesRegex(ValueError, "renderer-required"):
            style.resolve(self.stack, self.profiles, ["worldMotifs.screens"])
