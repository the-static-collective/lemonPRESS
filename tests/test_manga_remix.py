import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as press
import manga_remix as remix

BASE = "works/manga-press-specimen"
EDITION = BASE + "/manga/001"


class MangaRemix(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / BASE, self.root / BASE)
        self.edition_path = self.root / EDITION / "edition.yaml"
        self.edition = press.read_json(self.edition_path)
        self.edition_ref = {
            "path": EDITION + "/edition.yaml",
            "sha256": press.sha256_file(self.edition_path)[0],
        }
        self.recipe = {
            "schema": "lemonpress/manga-remix-recipe/v0",
            "title": "Synthetic two-parent remix candidate",
            "canvasPx": {"width": 64, "height": 96},
            "backgroundRgba": [255, 255, 255, 255],
            "parents": [
                {
                    "parentId": "left-parent",
                    "editionManifest": self.edition_ref,
                    "pageManifest": self.edition["pageManifests"][2],
                },
                {
                    "parentId": "right-parent",
                    "editionManifest": self.edition_ref,
                    "pageManifest": self.edition["pageManifests"][4],
                },
            ],
            "placements": [
                {
                    "placementId": "left",
                    "parentId": "left-parent",
                    "sourceRectPx": None,
                    "destinationRectPx": {"x": 0, "y": 0, "width": 32, "height": 96},
                    "rotateDeg": 0,
                    "mirrorX": False,
                    "mirrorY": False,
                    "opacity": 255,
                    "resample": "nearest",
                },
                {
                    "placementId": "right",
                    "parentId": "right-parent",
                    "sourceRectPx": None,
                    "destinationRectPx": {"x": 32, "y": 0, "width": 32, "height": 96},
                    "rotateDeg": 0,
                    "mirrorX": False,
                    "mirrorY": False,
                    "opacity": 255,
                    "resample": "nearest",
                },
            ],
        }

    def inventory(self):
        return {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in (self.root / BASE).rglob("*")
            if p.is_file()
        }

    def test_deterministic_build_and_parent_bytes_survive(self):
        before = self.inventory()
        a, a_png = remix.build(self.root, self.recipe)
        b, b_png = remix.build(self.root, self.recipe)
        self.assertEqual(press.canonical_bytes(a), press.canonical_bytes(b))
        self.assertEqual(a_png, b_png)
        self.assertEqual(before, self.inventory())
        remix.verify_candidate(a)
        self.assertTrue(a["candidateId"].startswith("manga-remix:"))
        self.assertEqual(len(a["parents"]), 2)

    def test_rights_intersect_and_candidate_has_no_authority(self):
        candidate, _ = remix.build(self.root, self.recipe)
        self.assertTrue(candidate["effectiveGrants"]["pixelReuse"])
        self.assertTrue(candidate["effectiveGrants"]["derivativeReuse"])
        self.assertFalse(candidate["effectiveGrants"]["pixelHarvest"])
        self.assertFalse(candidate["effectiveGrants"]["publicationReuse"])
        self.assertFalse(any(candidate["authority"].values()))
        self.assertEqual(candidate["status"], "CANDIDATE")
        self.assertIn("Explicit local page/edition admission", candidate["wrench"]["STOP"])

    def test_crop_requires_explicit_pixel_harvest(self):
        self.recipe["placements"][0]["sourceRectPx"] = {"x": 0, "y": 0, "width": 32, "height": 96}
        with self.assertRaisesRegex(ValueError, "pixelHarvest"):
            remix.build(self.root, self.recipe)

    def test_parent_binding_tamper_refuses(self):
        page = press.bound_json(self.root, self.edition["pageManifests"][2])
        source_path = press.bound_path(self.root, page["sourceImage"])
        source_path.write_bytes(b"not the admitted pixels")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            remix.build(self.root, self.recipe)

    def test_declared_parent_choice_changes_candidate(self):
        a, a_png = remix.build(self.root, self.recipe)
        changed = copy.deepcopy(self.recipe)
        changed["placements"][0]["parentId"] = "right-parent"
        changed["placements"][1]["parentId"] = "left-parent"
        b, b_png = remix.build(self.root, changed)
        self.assertNotEqual(a["candidateId"], b["candidateId"])
        self.assertNotEqual(a["outputImage"]["sha256"], b["outputImage"]["sha256"])
        self.assertNotEqual(a_png, b_png)

    def test_create_only_bundle_and_independent_verify(self):
        out = self.root / "out"
        candidate, png_bytes = remix.build(self.root, self.recipe)
        remix.write_bundle(out, candidate, png_bytes)
        remix.write_bundle(out, candidate, png_bytes)
        verified = remix.verify_bundle(self.root, self.recipe, out)
        self.assertEqual(candidate["candidateId"], verified["candidateId"])
        (out / "remix.png").write_bytes(b"conflicting bytes")
        with self.assertRaisesRegex(ValueError, "create-only conflict"):
            remix.write_bundle(out, candidate, png_bytes)
        with self.assertRaisesRegex(ValueError, "independently rebuild"):
            remix.verify_bundle(self.root, self.recipe, out)

    def test_candidate_tamper_refuses(self):
        candidate, png_bytes = remix.build(self.root, self.recipe)
        out = self.root / "out"
        remix.write_bundle(out, candidate, png_bytes)
        candidate["title"] = "forged title"
        (out / "candidate.json").write_bytes(press.canonical_bytes(candidate) + b"\n")
        with self.assertRaisesRegex(ValueError, "candidate hash mismatch"):
            remix.verify_bundle(self.root, self.recipe, out)

    def test_v0_schema_validates_recipe_and_candidate(self):
        schemas = [json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.schema.json")]
        registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas])
        recipe_schema = json.loads((ROOT / "schemas/manga-remix-recipe.schema.json").read_text())
        candidate_schema = json.loads((ROOT / "schemas/manga-remix-candidate.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(recipe_schema)
        jsonschema.Draft202012Validator.check_schema(candidate_schema)
        candidate, _ = remix.build(self.root, self.recipe)
        jsonschema.Draft202012Validator(recipe_schema, registry=registry).validate(self.recipe)
        jsonschema.Draft202012Validator(candidate_schema, registry=registry).validate(candidate)


if __name__ == "__main__":
    unittest.main()
