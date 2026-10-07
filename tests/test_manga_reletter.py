import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press
import manga_reletter as reletter

BASE = "works/manga-press-specimen"
WITNESS = "witnesses/reletter-001"


class MangaReletter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / BASE, self.root / BASE)
        shutil.copytree(ROOT / WITNESS, self.root / WITNESS)
        self.recipe_path = self.root / WITNESS / "recipe.json"
        self.recipe = press.read_json(self.recipe_path)

    def inventory(self):
        return {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in (self.root / BASE).rglob("*")
            if p.is_file()
        }

    def test_deterministic_build_and_parent_survives(self):
        before = self.inventory()
        a, a_png = reletter.build(self.root, copy.deepcopy(self.recipe))
        b, b_png = reletter.build(self.root, copy.deepcopy(self.recipe))
        self.assertEqual(press.canonical_bytes(a), press.canonical_bytes(b))
        self.assertEqual(a_png, b_png)
        self.assertEqual(before, self.inventory())
        self.assertTrue(a["candidateId"].startswith("manga-reletter:"))
        self.assertEqual(a["stage"], "return")

    def test_rights_and_authority_do_not_expand(self):
        candidate, _ = reletter.build(self.root, copy.deepcopy(self.recipe))
        self.assertTrue(candidate["effectiveGrants"]["pixelReuse"])
        self.assertTrue(candidate["effectiveGrants"]["derivativeReuse"])
        self.assertFalse(candidate["effectiveGrants"]["publicationReuse"])
        self.assertFalse(any(candidate["authority"].values()))
        self.assertEqual(candidate["status"], "CANDIDATE")

    def test_unknown_segment_refuses(self):
        changed = copy.deepcopy(self.recipe)
        changed["placements"][0]["segmentId"] = "p99-missing"
        with self.assertRaisesRegex(ValueError, "unknown segmentId"):
            reletter.build(self.root, changed)

    def test_overflow_refuses_instead_of_truncating(self):
        changed = copy.deepcopy(self.recipe)
        changed["placements"][0]["rectPx"] = {"x": 8, "y": 58, "width": 12, "height": 8}
        with self.assertRaisesRegex(ValueError, "overflow|padding consumes|glyph cannot fit"):
            reletter.build(self.root, changed)

    def test_parent_pixel_tamper_refuses(self):
        page = press.bound_json(self.root, self.recipe["parent"]["pageManifest"])
        source = press.bound_path(self.root, page["sourceImage"])
        source.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            reletter.build(self.root, copy.deepcopy(self.recipe))

    def test_return_text_change_changes_candidate_and_pixels(self):
        a, a_png = reletter.build(self.root, copy.deepcopy(self.recipe))
        relay_path = self.root / WITNESS / "relay.json"
        spec = press.read_json(relay_path)
        spec["segments"][0]["return"] = "THE BELL WAITS."
        relay_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        b, b_png = reletter.build(self.root, copy.deepcopy(self.recipe))
        self.assertNotEqual(a["candidateId"], b["candidateId"])
        self.assertNotEqual(a_png, b_png)

    def test_create_only_bundle_and_verify(self):
        out = self.root / "out"
        candidate, png_bytes = reletter.build(self.root, copy.deepcopy(self.recipe))
        reletter.write_bundle(out, candidate, png_bytes)
        reletter.write_bundle(out, candidate, png_bytes)
        verified = reletter.verify_bundle(self.root, copy.deepcopy(self.recipe), out)
        self.assertEqual(candidate["candidateId"], verified["candidateId"])
        (out / "reletter.png").write_bytes(b"conflict")
        with self.assertRaisesRegex(ValueError, "create-only conflict"):
            reletter.write_bundle(out, candidate, png_bytes)

    def test_schemas_validate_witness(self):
        recipe_schema = json.loads((ROOT / "schemas/manga-reletter-recipe-v0.schema.json").read_text())
        candidate_schema = json.loads((ROOT / "schemas/manga-reletter-candidate-v0.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(recipe_schema)
        jsonschema.Draft202012Validator.check_schema(candidate_schema)
        jsonschema.Draft202012Validator(recipe_schema).validate(self.recipe)
        candidate, _ = reletter.build(self.root, copy.deepcopy(self.recipe))
        jsonschema.Draft202012Validator(candidate_schema).validate(candidate)


if __name__ == "__main__":
    unittest.main()
