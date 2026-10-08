import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "works/renji-relay-001"
sys.path.insert(0, str(SPECIMEN))
import verify as audit
import run as relay


class RelayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory(prefix="renji-tests-")
        cls.root = Path(cls.base.name)
        cls.spec = cls.root / "spec"
        shutil.copytree(SPECIMEN, cls.spec)
        # Valid synthetic RGB PNG; this tests byte ancestry, not source transcription truth.
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        cls.source_bytes = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB",1,1,8,2,0,0,0)) + chunk(b"IDAT", zlib.compress(b"\x00\x10\x20\x30")) + chunk(b"IEND",b"")
        cls.source = cls.root / "synthetic.png"
        actual_source = os.environ.get("RENJI_SOURCE_PNG")
        if actual_source:
            cls.source_bytes = Path(actual_source).read_bytes()
        cls.source.write_bytes(cls.source_bytes)
        cls.expected = audit.sha(cls.source_bytes)
        manifest = audit.read(cls.spec / "source-manifest.json")
        if actual_source and cls.expected != manifest["sources"][0]["sha256"]:
            raise AssertionError("RENJI_SOURCE_PNG does not match the separately frozen donor manifest")
        manifest["sources"][0].update(sha256=cls.expected, bytes=len(cls.source_bytes))
        (cls.spec / "source-manifest.json").write_bytes(audit.canon(manifest))
        cls.recipe = audit.read(cls.spec / "recipe.json")
        if not actual_source:
            cls.recipe["sourceDimensions"] = [1,1]
            for row in cls.recipe["transcription"]["segments"]:
                row["text"] = "Synthetic fixture particular: " + row["id"]
        (cls.spec / "recipe.json").write_bytes(audit.canon(cls.recipe))
        cls.runtime = os.environ.get("RELATTE_RUNTIME")
        cls.baseline = cls.root / "baseline"
        relay.compose(cls.spec, cls.source, cls.baseline)
        if cls.runtime:
            cls.command(["node", str(cls.spec / "relatte_bridge.mjs"), "seal", str(cls.baseline), cls.runtime])
            cls.command([sys.executable, str(cls.baseline / "foreign_renderer.py"), str(cls.baseline)])
            cls.command(["node", str(cls.spec / "relatte_bridge.mjs"), "receive", str(cls.baseline), cls.runtime, str(cls.root / "private-baseline")])

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    @staticmethod
    def command(args, success=True, cwd=None):
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
        if success and result.returncode:
            raise AssertionError(result.stderr)
        if not success and not result.returncode:
            raise AssertionError("hostile input unexpectedly passed")
        return result

    def clone(self, label):
        folder = self.root / label
        shutil.copytree(self.baseline, folder)
        return folder

    def write_packet(self, folder, packet):
        (folder / "packet.json").write_bytes(audit.canon(packet) + b"\n")

    def cold(self, folder, success=True):
        if not self.runtime:
            self.skipTest("set RELATTE_RUNTIME to pinned reLATTE checkout for signed integration cases")
        result = self.command(["node", str(folder / "verify-crossing.mjs"), str(folder), "--expected-source", self.expected], success=success, cwd=self.root)
        return json.loads(result.stdout) if success else None

    def regenerate(self, label, edit_recipe=None, edit_renderer=None):
        if not self.runtime:
            self.skipTest("set RELATTE_RUNTIME for signed integration cases")
        spec = self.root / (label + "-spec")
        shutil.copytree(self.spec, spec)
        if edit_recipe:
            value = audit.read(spec / "recipe.json")
            edit_recipe(value)
            (spec / "recipe.json").write_bytes(audit.canon(value))
        if edit_renderer:
            path = spec / "foreign_renderer.py"
            path.write_text(edit_renderer(path.read_text()), encoding="utf-8")
        folder = self.root / label
        relay.compose(spec, self.source, folder)
        self.command(["node", str(spec / "relatte_bridge.mjs"), "seal", str(folder), self.runtime])
        self.command([sys.executable, str(folder / "foreign_renderer.py"), str(folder)])
        self.command(["node", str(spec / "relatte_bridge.mjs"), "receive", str(folder), self.runtime, str(self.root / (label + "-private"))])
        return folder

    def test_H01_source_mutation(self):
        folder = self.clone("h01")
        (folder / "source.png").write_bytes(self.source_bytes + b"changed")
        with self.assertRaisesRegex(ValueError,"source byte"):
            audit.verify_bundle(folder, self.expected)

    def test_H02_missing_japanese_intermediate(self):
        folder = self.clone("h02")
        packet = audit.read(folder / "packet.json")
        packet["nodes"].pop(2)
        self.write_packet(folder, packet)
        with self.assertRaisesRegex(ValueError,"ancestry"):
            audit.verify_bundle(folder, self.expected)

    def test_H03_original_identity_claim(self):
        folder = self.clone("h03")
        packet = audit.read(folder / "packet.json")
        packet["recipe"]["press"]["status"] = "ORIGINAL"
        self.write_packet(folder, packet)
        with self.assertRaisesRegex(ValueError,"original/admission"):
            audit.verify_bundle(folder, self.expected)

    def test_H04_undeclared_reorder(self):
        folder = self.clone("h04")
        packet = audit.read(folder / "packet.json")
        packet["nodes"][-1]["body"]["placements"].reverse()
        self.write_packet(folder, packet)
        with self.assertRaisesRegex(ValueError,"ancestry"):
            audit.verify_bundle(folder, self.expected)

    def test_H05_declared_reorder(self):
        folder = self.regenerate("h05", lambda recipe: recipe["remix"]["order"].reverse())
        self.assertEqual(self.cold(folder)["status"],"VALID_ADMISSION")
        self.assertNotEqual(audit.read(folder / "packet.json")["head"], audit.read(self.baseline / "packet.json")["head"])

    def test_H06_declared_renderer_replacement(self):
        folder = self.regenerate("h06", edit_renderer=lambda text: text.replace("foreign:receipt-scroll/v0", "foreign:other-typesetter/v0"))
        self.assertEqual(self.cold(folder)["status"],"VALID_ADMISSION")
        self.assertEqual(audit.read(folder / "render-receipt.json")["renderer"]["id"],"foreign:other-typesetter/v0")

    def test_H07_unrecognizable_render_complete_ancestry(self):
        self.assertEqual(self.cold(self.baseline)["status"],"VALID_ADMISSION")
        self.assertNotEqual((self.baseline / "arrival.html").read_bytes(), self.source_bytes)
        self.assertNotIn("<img", (self.baseline / "arrival.html").read_text())

    def test_H08_no_lemonpress_foreign_machine(self):
        folder = self.clone("h08")
        self.assertEqual(self.cold(folder)["status"],"VALID_ADMISSION")
        # Neither verifier nor renderer imports repo modules or third-party dependencies.
        isolated = self.command([sys.executable, "-I", str(folder / "verify.py"), str(folder), "--expected-source", self.expected], cwd=self.root)
        self.assertEqual(json.loads(isolated.stdout)["status"],"PASS")

    def test_H09_valid_local_refusal(self):
        if not self.runtime: self.skipTest("set RELATTE_RUNTIME")
        folder = self.clone("h09")
        for name in ("receive-receipt.json","local-disposition.json","receiver-snapshot.json","receiver-journal.jsonl"):
            (folder / name).unlink()
        self.command(["node", str(self.spec / "relatte_bridge.mjs"), "receive", str(folder), self.runtime, str(self.root / "private-refusal"), "REFUSE"])
        self.assertEqual(self.cold(folder)["status"],"VALID_REFUSAL")

    def test_H10_valid_local_admission(self):
        value = self.cold(self.baseline)
        self.assertEqual(value["status"],"VALID_ADMISSION")
        self.assertFalse(value["houseAdmission"])
        self.assertEqual(value["signerAuthority"],"NOT_ESTABLISHED")

    def test_H11_forged_source_with_identical_bytes(self):
        folder = self.clone("h11")
        packet = audit.read(folder / "packet.json")
        packet["source"]["sha256"] = "0" * 64
        packet["nodes"] = audit.build_nodes(packet["source"],packet["recipe"],packet["styleInputs"])
        packet["head"] = packet["nodes"][-1]["identity"]
        self.write_packet(folder, packet)
        with self.assertRaisesRegex(ValueError,"source byte"):
            audit.verify_bundle(folder, self.expected)

    def test_H12_pixel_identical_broken_ancestry(self):
        folder = self.clone("h12")
        (folder / "arrival.html").write_bytes(self.source_bytes)
        packet = audit.read(folder / "packet.json")
        packet["nodes"][3]["parent"] = packet["nodes"][0]["identity"]
        self.write_packet(folder, packet)
        with self.assertRaisesRegex(ValueError,"ancestry"):
            audit.verify_bundle(folder, self.expected)

    def test_H13_radically_different_complete_ancestry(self):
        self.assertEqual(self.cold(self.baseline)["status"],"VALID_ADMISSION")
        self.assertTrue(audit.read(self.baseline / "render-receipt.json")["renderer"]["incapableOf"])

    def test_signature_artifact_and_journal_tamper_refuse(self):
        for label, filename, mutate in [
            ("signature", "crossing.json", lambda p: p["signing"].update(signature="A" * 86)),
            ("snapshot", "receiver-snapshot.json", lambda p: p["admitted"].clear()),
            ("render-declaration", "render-receipt.json", lambda p: p["renderer"].update(id="undeclared")),
        ]:
            folder = self.clone(label)
            value = audit.read(folder / filename)
            mutate(value)
            (folder / filename).write_bytes(audit.canon(value))
            self.cold(folder, success=False)

    def test_create_only_and_external_recipe_anchor(self):
        folder = self.clone("create-only")
        relay.compose(self.spec, self.source, folder)
        with self.assertRaisesRegex(ValueError,"recipe anchor"):
            audit.verify_bundle(folder,self.expected,"0" * 64)
        (folder / "press.json").write_bytes(b"conflict")
        with self.assertRaisesRegex(ValueError,"create-only"):
            relay.compose(self.spec,self.source,folder)

    def test_hostile_inventory_is_executable(self):
        cases = audit.read(SPECIMEN / "hostile-cases.json")["cases"]
        self.assertEqual({c["id"] for c in cases},{"H%02d" % i for i in range(1,14)})
        for case in cases:
            self.assertTrue(any(name.startswith("test_" + case["id"] + "_") for name in dir(self)))


class RecordedWitnessTests(unittest.TestCase):
    def test_recorded_witness_matches_current_recipe_and_exact_receipt_bytes(self):
        record = audit.read(SPECIMEN / "witness.json")
        recipe = audit.read(SPECIMEN / "recipe.json")
        self.assertEqual(audit.sha(audit.canon(recipe)),record["recipeSha256"])
        for filename, digest in record["artifactFiles"].items():
            self.assertEqual(audit.sha((SPECIMEN / "witness" / filename).read_bytes()),digest)
        self.assertEqual(audit.read(SPECIMEN / "witness/crossing.json")["crossing_id"],record["crossingId"])
        self.assertEqual(audit.read(SPECIMEN / "witness/render-receipt.json")["outputSha256"],record["arrivalSha256"])

    def test_recorded_native_signatures_verify_independently(self):
        program = """
        import {pathToFileURL} from 'node:url';
        import {readFile} from 'node:fs/promises';
        const {verifySigned} = await import(pathToFileURL(process.argv[2]));
        for (const [name,type] of [['crossing.json','crossing'],['receive-receipt.json','receipt'],['local-disposition.json','receipt']]) {
          await verifySigned(JSON.parse(await readFile(process.argv[3] + '/' + name,'utf8')),type);
        }
        """
        result = subprocess.run(["node","--input-type=module","-e",program,"signature-test",str(SPECIMEN / "verify-crossing.mjs"),str(SPECIMEN / "witness")],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
