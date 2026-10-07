import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_page_intake as intake
import manga_press as press


def minimal_pdf(shades=(0.85, 0.25)):
    objects = []
    kids = []
    page_numbers = []
    content_numbers = []
    next_obj = 3
    for _ in shades:
        page_numbers.append(next_obj)
        content_numbers.append(next_obj + 1)
        kids.append(f"{next_obj} 0 R")
        next_obj += 2
    objects.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objects.append((2, f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(shades)} >>".encode()))
    for page_obj, content_obj, shade in zip(page_numbers, content_numbers, shades):
        stream = f"{shade:.2f} g 0 0 72 72 re f".encode()
        objects.append((page_obj, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] /Resources << >> /Contents {content_obj} 0 R >>".encode()))
        objects.append((content_obj, b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"))
    objects.sort()
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for number, body in objects:
        offsets[number] = len(out)
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    max_obj = max(offsets)
    out += f"xref\n0 {max_obj + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for number in range(1, max_obj + 1):
        out += f"{offsets[number]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


class PageIntake(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / "fixtures/source.pdf"
        source.parent.mkdir(parents=True)
        source.write_bytes(minimal_pdf())
        self.spec = {
            "schema": intake.SPEC_SCHEMA,
            "id": "page-intake-test-001",
            "title": "Page Intake Test",
            "status": "EXECUTION_WITNESS",
            "bundle_path": "out/intake",
            "source": {
                "path": "fixtures/source.pdf",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "media_type": "application/pdf",
                "page_count": 2,
                "revision": "fixture-001",
            },
            "renderer": {
                "engine": "pypdfium2",
                "version": intake.package_version("pypdfium2"),
                "scale_milli": 2000,
                "pixel_mode": "RGB",
                "png_encoder": intake.PNG_ENCODER,
            },
            "manga": {
                "work_id": "lemonpress:page-intake-test",
                "edition_id": "lemonpress:page-intake-test:source-pages",
                "issue_id": "lemonpress:page-intake-test:issue",
                "page_prefix": "source-page",
                "geometry": {
                    "unit": "um",
                    "page": {"x": 0, "y": 0, "width": 25400, "height": 25400},
                    "trim": {"x": 0, "y": 0, "width": 25400, "height": 25400},
                    "bleed": {"left": 0, "right": 0, "top": 0, "bottom": 0},
                    "safeArea": {"x": 1000, "y": 1000, "width": 23400, "height": 23400},
                },
            },
            "admission": {
                "authority_ref": "fixture:page-intake-001",
                "scope": "source rasterization + reletter test only; no edition or publication admission",
                "rights_note": "synthetic fixture",
                "grants": {
                    "pixelReuse": True,
                    "pixelHarvest": False,
                    "derivativeReuse": True,
                    "publicationReuse": False,
                    "motionAdaptation": False,
                    "synthesizedSound": False,
                },
            },
            "laws": list(intake.LAWS),
        }

    def test_deterministic_build_and_source_survives(self):
        source = (self.root / "fixtures/source.pdf").read_bytes()
        a, a_files = intake.build(self.root, copy.deepcopy(self.spec))
        b, b_files = intake.build(self.root, copy.deepcopy(self.spec))
        self.assertEqual(press.canonical_bytes(a), press.canonical_bytes(b))
        self.assertEqual(a_files, b_files)
        self.assertEqual(source, (self.root / "fixtures/source.pdf").read_bytes())
        self.assertEqual(a["pageCount"], 2)
        self.assertEqual(len({p["pixelSha256"] for p in a["pages"]}), 2)

    def test_compose_verify_and_page_manifests(self):
        candidate, files = intake.build(self.root, copy.deepcopy(self.spec))
        intake.write_bundle(self.root, files)
        intake.write_bundle(self.root, files)
        verified = intake.verify_bundle(self.root, copy.deepcopy(self.spec))
        self.assertEqual(candidate["candidateId"], verified["candidateId"])
        for page in candidate["pages"]:
            manifest = press.bound_json(self.root, page["pageManifest"])
            press.verify("page", manifest)
            self.assertEqual(manifest["sourceImage"], page["sourceImage"])
            self.assertFalse(manifest["grants"]["publicationReuse"])

    def test_source_tamper_refuses(self):
        (self.root / "fixtures/source.pdf").write_bytes(b"not the source")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            intake.build(self.root, copy.deepcopy(self.spec))

    def test_page_count_refuses(self):
        changed = copy.deepcopy(self.spec)
        changed["source"]["page_count"] = 3
        with self.assertRaisesRegex(ValueError, "page count mismatch"):
            intake.build(self.root, changed)

    def test_expected_page_hashes_are_enforced(self):
        candidate, _ = intake.build(self.root, copy.deepcopy(self.spec))
        changed = copy.deepcopy(self.spec)
        changed["expected_pages"] = [
            {
                "page": p["page"], "width": p["width"], "height": p["height"],
                "pixel_sha256": p["pixelSha256"], "png_sha256": p["sourceImage"]["sha256"],
            } for p in candidate["pages"]
        ]
        intake.build(self.root, changed)
        changed["expected_pages"][0]["pixel_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "pixel SHA-256 changed"):
            intake.build(self.root, changed)

    def test_renderer_version_is_identity_gate(self):
        changed = copy.deepcopy(self.spec)
        changed["renderer"]["version"] = "0.0.0"
        with self.assertRaisesRegex(ValueError, "renderer version mismatch"):
            intake.build(self.root, changed)

    def test_create_only_conflict_refuses(self):
        candidate, files = intake.build(self.root, copy.deepcopy(self.spec))
        intake.write_bundle(self.root, files)
        image = self.root / candidate["pages"][0]["sourceImage"]["path"]
        image.write_bytes(b"conflicting bytes")
        with self.assertRaisesRegex(ValueError, "create-only conflict"):
            intake.write_bundle(self.root, files)

    def test_schemas_validate(self):
        for name in (intake.SPEC_SCHEMA_NAME, intake.CANDIDATE_SCHEMA_NAME):
            schema = json.loads((ROOT / "schemas" / name).read_text())
            jsonschema.Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
