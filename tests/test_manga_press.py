import argparse
import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manga_press as m
import physical_composer
import press_gate
import press_run
import recipient_mailer
import dispatch_gate
import jsonschema
from referencing import Registry, Resource

BASE = "works/manga-press-specimen"
EDITION = BASE + "/manga/001"


class MangaPress(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / BASE, self.root / BASE)
        self.edition = m.read_json(self.root / EDITION / "edition.yaml")

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(m.canonical_bytes(value))
        return {"path": relative, "sha256": m.sha256_file(path)[0]}

    def admit(self):
        # Test-only external re-admission of a changed declaration. Production
        # compose/seal do not edit or fabricate this receipt.
        self.edition = m.seal("edition", self.edition)
        admission = m.bound_json(self.root, self.edition["editionAdmission"])
        admission["declaration_sha256"] = m.edition_declaration_hash(self.edition)
        admission["admitted_page_hashes"] = [m.bound_json(self.root, r)["pageHash"] for r in self.edition["pageManifests"]]
        self.edition["editionAdmission"] = self.write(EDITION + "/admission-001.json", admission)
        self.edition = m.seal("edition", self.edition)
        return self.edition

    def change_page(self, index, edit):
        ref = self.edition["pageManifests"][index]
        page = m.bound_json(self.root, ref)
        edit(page)
        self.edition["pageManifests"][index] = self.write(ref["path"], m.seal("page", page))
        self.admit()

    def compose(self):
        return m.compose(self.root, self.edition)

    def declaration(self, handoff):
        artifact = self.write("returned/performance.json", {"kind": "synthetic-renderer-test-artifact", "actualAnimation": False})
        identity = handoff["pages"][0]["identity"]
        return {"handoffHash": handoff["handoffHash"], "consumedPages": [identity], "descendantId": "synthetic:performance-001",
                "renderer": "test-renderer-declaration-only", "artifacts": [artifact], "preservedPages": [identity],
                "omittedMaterial": ["all other pages"], "mutations": ["synthetic record, no film rendered"]}

    def test_byte_identical_replay_edition_and_page_hashes(self):
        a, b = self.compose(), self.compose()
        self.assertEqual(m.canonical_bytes(a), m.canonical_bytes(b))
        m.verify("edition", a["edition"])
        for p in a["pages"]:
            m.verify("page", p)
        out = self.root / "out"
        m.write_bundle(out, a)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        m.write_bundle(out, b)
        self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_object_serialization_and_manifest_file_listing_do_not_order_pages(self):
        original = self.compose()
        # Canonical object order is irrelevant, including the cover map.
        self.edition = dict(reversed(list(self.edition.items())))
        self.edition["covers"] = dict(reversed(list(self.edition["covers"].items())))
        self.assertEqual(m.canonical_bytes(original), m.canonical_bytes(self.compose()))
        self.edition["pageManifests"].reverse()
        self.admit()
        self.assertEqual(original["printPlan"]["sides"][3]["pageId"], self.compose()["printPlan"]["sides"][3]["pageId"])

    def test_ltr_rtl_explicit_and_spread_sides_flip(self):
        ltr = self.compose()["printPlan"]
        self.edition["readingDirection"] = "rtl"
        self.admit()
        rtl = self.compose()["printPlan"]
        self.assertEqual(ltr["spreads"][0]["left"], "place-04")
        self.assertEqual(rtl["spreads"][0]["left"], "place-05")
        self.assertEqual(ltr["spreads"][0]["trimWidthUm"], 240000)
        self.assertEqual([p["pageId"] for p in ltr["sides"]], [p["pageId"] for p in rtl["sides"]])
        for direction in (None, "", "auto"):
            self.edition["readingDirection"] = direction
            self.admit()
            with self.assertRaisesRegex(ValueError, "explicit ltr or rtl"):
                self.compose()

    def test_accidental_duplicate_refuses_declared_repeat_survives(self):
        original = copy.deepcopy(self.edition)
        repeat = {"placementId": "repeat-03", "pageId": "page-03", "repeatOf": None}
        repeat2 = {"placementId": "repeat-03b", "pageId": "page-03", "repeatOf": "place-03"}
        self.edition["pageOrdering"][6:6] = [repeat, repeat2]
        self.edition["pageCount"] = 10
        self.admit()
        with self.assertRaisesRegex(ValueError, "accidental duplicate"):
            self.compose()
        repeat["repeatOf"] = "place-03"
        # admit() deep-copies the input, so update its actual declaration.
        self.edition["pageOrdering"][6]["repeatOf"] = "place-03"
        self.admit()
        bundle = self.compose()
        self.assertEqual(len(bundle["printPlan"]["sides"]), 10)
        self.assertEqual(len(bundle["pages"]), len(original["pageManifests"]))

    def test_unique_page_and_placement_identities(self):
        self.edition["pageManifests"].append(self.edition["pageManifests"][0])
        self.admit()
        with self.assertRaisesRegex(ValueError, "duplicate page identity"):
            self.compose()

    def test_duplicate_placement_identity_refuses(self):
        self.edition["pageOrdering"][2]["placementId"] = "place-01"
        self.admit()
        with self.assertRaisesRegex(ValueError, "duplicate placement"):
            self.compose()

    def test_unplaced_and_unknown_pages_refuse(self):
        self.edition["pageOrdering"][2]["pageId"] = "missing-page"
        self.admit()
        with self.assertRaisesRegex(ValueError, "unknown page"):
            self.compose()

    def test_spreads_need_actual_facing_even_odd_pair(self):
        for pair in (["place-03", "place-04"], ["place-04", "place-06"], ["place-02", "place-03"]):
            self.edition["spreads"][0]["placements"] = pair
            self.admit()
            with self.assertRaises(ValueError):
                self.compose()

    def test_duplicate_spread_refuses(self):
        self.edition["spreads"].append(copy.deepcopy(self.edition["spreads"][0]))
        self.admit()
        with self.assertRaisesRegex(ValueError, "duplicate spread"):
            self.compose()

    def test_trim_bleed_safe_area_validation(self):
        valid = copy.deepcopy(self.edition["geometry"])
        for box, key, val in (("trim", "x", 0), ("safeArea", "width", 120001), ("bleed", "top", -1), ("page", "width", 0), ("trim", "width", 120000.0)):
            geo = copy.deepcopy(valid)
            geo[box][key] = val
            with self.assertRaises(ValueError):
                m.geometry(geo)

    def test_page_geometry_must_match_issue(self):
        self.change_page(2, lambda p: p["geometry"]["safeArea"].update(width=109000))
        with self.assertRaisesRegex(ValueError, "incompatible print geometry"):
            self.compose()

    def test_cover_placement_refuses(self):
        self.edition["covers"]["front"] = "place-03"
        self.admit()
        with self.assertRaisesRegex(ValueError, "cover placement"):
            self.compose()

    def test_required_blanks_and_no_automatic_padding(self):
        self.edition["printIntent"]["requiredBlanks"] = []
        self.admit()
        with self.assertRaisesRegex(ValueError, "blank declarations"):
            self.compose()

    def test_odd_leaf_geometry_refuses_without_inventing_page(self):
        self.edition["pageOrdering"].insert(6, {"placementId": "repeat-03", "pageId": "page-03", "repeatOf": "place-03"})
        self.edition["pageCount"] = 9
        self.admit()
        with self.assertRaisesRegex(ValueError, "explicitly admitted blank"):
            self.compose()

    def test_page_bytes_cannot_mutate_under_frozen_sha(self):
        page = m.bound_json(self.root, self.edition["pageManifests"][4])
        (self.root / page["sourceImage"]["path"]).write_bytes(b"mutated pixels")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            self.compose()

    def test_page_and_edition_hash_tampering_refuses(self):
        self.edition["title"] = "unbound title"
        with self.assertRaisesRegex(ValueError, "edition hash mismatch"):
            self.compose()
        p = m.bound_json(self.root, self.edition["pageManifests"][0])
        p["pageId"] = "tampered"
        with self.assertRaisesRegex(ValueError, "page hash mismatch"):
            m.verify("page", p)

    def test_edition_admission_not_inherited_from_source(self):
        self.edition["title"] = "new edition decision"
        self.edition = m.seal("edition", self.edition)
        with self.assertRaisesRegex(ValueError, "declaration must be explicitly admitted"):
            self.compose()

    def test_source_replacement_does_not_retroactively_update_edition(self):
        old = self.compose()
        replacement = self.write(BASE + "/source-002.json", {"kind": "new source", "particulars": []})
        self.assertEqual(m.canonical_bytes(old), m.canonical_bytes(self.compose()))
        self.edition["source"] = replacement
        self.admit()
        with self.assertRaisesRegex(ValueError, "source identity mismatch"):
            self.compose()

    def test_composition_never_rewrites_input_or_source(self):
        def inventory():
            return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in (self.root / BASE).rglob("*") if p.is_file()}
        before = inventory()
        self.compose()
        self.assertEqual(before, inventory())

    def test_unknown_page_semantics_are_legal(self):
        page = self.compose()["pages"][4]
        self.assertIsNone(page["panelMap"])
        self.assertEqual(page["internalSemantics"], "unknown")
        self.assertIsNotNone(page["sourceImage"])

    def test_proof_and_handoff_grant_no_execution_or_release(self):
        b = self.compose()
        self.assertEqual(b["printProof"]["state"], "structural-proof-only")
        self.assertEqual(b["printProof"]["publicationAuthority"], "none")
        self.assertFalse(any(b["handoff"]["authority"].values()))
        self.assertIsNone(b["handoff"]["externalEditorialAuthorityReference"])
        self.assertFalse(b["handoff"]["grants"]["pixelHarvest"])
        self.assertFalse(b["handoff"]["grants"]["synthesizedSound"])

    def test_rights_cannot_expand_at_edition_or_handoff(self):
        self.edition["performanceHandoffPolicy"]["grants"]["publicationReuse"] = True
        self.admit()
        with self.assertRaisesRegex(ValueError, "rights must not expand"):
            self.compose()

    def test_page_rights_cannot_expand(self):
        self.change_page(4, lambda p: p["grants"].update(pixelHarvest=True))
        with self.assertRaisesRegex(ValueError, "rights must not expand"):
            self.compose()

    def test_narrower_page_rights_narrow_handoff(self):
        self.change_page(4, lambda p: p["grants"].update(motionAdaptation=False))
        self.assertFalse(self.compose()["handoff"]["grants"]["motionAdaptation"])

    def test_false_string_is_not_permission(self):
        self.edition["grants"]["pixelHarvest"] = "false"
        self.admit()
        with self.assertRaisesRegex(ValueError, "booleans"):
            self.compose()

    def test_handoff_independent_rebuild_rejects_forged_claims(self):
        h = self.compose()["handoff"]
        h["authority"]["render"] = True
        h = m.seal("performance-handoff", h)
        with self.assertRaisesRegex(ValueError, "independently rebuilt"):
            m.verify_handoff(self.root, self.edition, h)

    def test_founding_compatibility_specimen_preserves_full_identity(self):
        h = m.read_json(self.root / EDITION / "blender-compatibility-handoff.json")
        m.verify_handoff(self.root, self.edition, h)
        p = h["pages"][0]
        self.assertEqual(p["identity"]["pageId"], "page-05")
        self.assertEqual(p["identity"]["workId"], self.edition["workId"])
        self.assertEqual(p["identity"]["issueId"], self.edition["issueId"])
        self.assertEqual(p["identity"]["editionId"], self.edition["editionId"])
        self.assertEqual(p["identity"]["sourceImageSha256"], p["sourceImage"]["sha256"])
        self.assertEqual(h["targetVocabulary"]["narrativeSource"], "haunted-blender/narrative-particular-source/v1")

    def test_return_and_print_are_siblings_no_auto_publish(self):
        b = self.compose()
        h = b["handoff"]
        before = (self.root / BASE / "work.yaml").read_bytes()
        declaration = self.declaration(h)
        receipt = m.accept_return(self.root, self.edition, h, declaration)
        print_parent = b["printPlan"]["sides"][0]["parent"]
        self.assertEqual(receipt["parents"][0], print_parent)
        self.assertEqual(receipt["descendantKind"], "performance")
        self.assertNotIn("printPlanHash", receipt)
        self.assertIsNone(receipt["publicationStateChange"])
        self.assertFalse(receipt["authority"]["houseRelease"])
        self.assertEqual(before, (self.root / BASE / "work.yaml").read_bytes())
        self.assertEqual(m.canonical_bytes(receipt), m.canonical_bytes(m.accept_return(self.root, self.edition, h, declaration)))

    def test_return_tampered_artifact_or_ancestry_refuses(self):
        h = self.compose()["handoff"]
        declaration = self.declaration(h)
        (self.root / declaration["artifacts"][0]["path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "bound bytes changed"):
            m.accept_return(self.root, self.edition, h, declaration)
        declaration = self.declaration(h)
        declaration["consumedPages"][0] = {**declaration["consumedPages"][0], "pageHash": "a" * 64}
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            m.accept_return(self.root, self.edition, h, declaration)

    def test_return_cannot_change_publication_state(self):
        h = self.compose()["handoff"]
        declaration = self.declaration(h)
        declaration["publicationStateChange"] = "published"
        with self.assertRaisesRegex(ValueError, "no publication commands"):
            m.accept_return(self.root, self.edition, h, declaration)

    def test_create_only_conflicting_bytes_refuse(self):
        out = self.root / "out"
        m.write_bundle(out, self.compose())
        (out / "edition.json").write_bytes(b"conflicting bytes")
        with self.assertRaisesRegex(ValueError, "create-only conflict"):
            m.write_bundle(out, self.compose())

    def test_binding_path_confinement(self):
        with self.assertRaisesRegex(ValueError, "repository-relative"):
            m.bound_path(self.root, {"path": "../escape", "sha256": "a" * 64})
        outside = self.root.parent / "outside-manga-evidence"
        outside.write_text("outside")
        self.addCleanup(outside.unlink)
        (self.root / "escape").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            m.bound_path(self.root, {"path": "escape", "sha256": "a" * 64})

    def test_duplicate_json_keys_refuse(self):
        path = self.root / "duplicate.json"
        path.write_text('{"readingDirection":"ltr","readingDirection":"rtl"}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            m.read_json(path)

    def test_press_gate_portable_packet_and_independent_integrity_check(self):
        out = self.root / "gate"
        with contextlib.redirect_stdout(io.StringIO()):
            m.export_gate(self.root, self.edition, out)
            self.assertEqual(press_gate.cmd_check(argparse.Namespace(packet=str(out))), 0)
        packet_root = out / "artifacts" / "evidence"
        portable = m.compose(packet_root, self.edition)
        self.assertEqual(m.canonical_bytes(portable), m.canonical_bytes(self.compose()))
        manifest = press_gate.load_manifest(out)
        self.assertEqual(manifest["lane"], "physical")
        self.assertEqual(manifest["state"], "preflight")
        self.assertEqual(manifest["publication"]["house_status"], "not_yet_declared_published")
        with self.assertRaisesRegex(ValueError, "create-only"):
            m.export_gate(self.root, self.edition, out)

    def test_proposal_cannot_be_print_selection(self):
        ref = self.edition["printIntent"]["selection"]
        selected = m.bound_json(self.root, ref)
        selected["state"] = "recommended"
        self.edition["printIntent"]["selection"] = self.write(ref["path"], selected)
        self.admit()
        with self.assertRaisesRegex(ValueError, "not selection"):
            self.compose()

    def test_manga_never_adds_a_house_lane(self):
        work = m.bound_json(self.root, self.edition["workManifest"])
        work["lanes"].append("manga")
        self.edition["workManifest"] = self.write(BASE + "/work.yaml", work)
        self.admit()
        with self.assertRaisesRegex(ValueError, "form, not a house lane"):
            self.compose()

    def test_cli_rebuild_refuses_persisted_forged_plan(self):
        out = self.root / "out"
        m.write_bundle(out, self.compose())
        (out / "print-plan.json").write_bytes(b"forged")
        run = subprocess.run([sys.executable, str(ROOT / "tools/manga_press.py"), "--root", str(self.root), "verify",
                              str(self.root / EDITION / "edition.yaml"), str(out)], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("verification failure", run.stderr)

    def test_versioned_json_schemas_validate_all_records_and_work(self):
        schemas = [json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.schema.json")]
        registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas])
        b = self.compose()
        records = {"edition": b["edition"], "print-plan": b["printPlan"], "print-proof": b["printProof"],
                   "performance-handoff": b["handoff"], "performance-return": m.accept_return(self.root, self.edition, b["handoff"], self.declaration(b["handoff"]))}
        records["page"] = b["pages"][4]
        for kind, record in records.items():
            schema = json.loads((ROOT / "schemas" / f"manga-{kind}.schema.json").read_text())
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.Draft202012Validator(schema, registry=registry).validate(record)
        work_schema = json.loads((ROOT / "schemas/work-manifest.schema.json").read_text())
        jsonschema.Draft202012Validator(work_schema).validate(m.bound_json(self.root, self.edition["workManifest"]))
        bad = copy.deepcopy(records["performance-handoff"])
        bad["authority"]["render"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/manga-performance-handoff.schema.json").read_text()), registry=registry).validate(bad)


class InheritedPhysical(unittest.TestCase):
    def test_complete_press_run_queue_remains_proposal_only(self):
        queue = press_run.load_json(ROOT / "press-run/001/queue.json")
        self.assertEqual(press_run.validate_queue(queue), [])
        with tempfile.TemporaryDirectory() as tmp:
            report = press_run.run_queue(queue, Path(tmp))
            self.assertEqual(report["authority"]["mode"], "orchestration_only")
            for file in Path(tmp).glob("*composition.json"):
                composition = json.loads(file.read_text())
                self.assertIsNone(composition["selection"])
                self.assertEqual(composition["grammar_version"], physical_composer.GRAMMAR_VERSION)

    def test_recipient_mailer_and_dispatch_boundaries(self):
        recipient_mailer.validate_job(json.loads((ROOT / "recipient-mailer/example-job.json").read_text()))
        state = {"state": "service_selected"}
        with self.assertRaisesRegex(ValueError, "invalid dispatch transition"):
            dispatch_gate.transition(state, "delivered")
        self.assertEqual(state["state"], "service_selected")

    def test_inherited_recipient_packet_and_dispatch_lifecycle(self):
        # Entirely local, using the pre-existing synthetic address. No postage,
        # carrier request, delivery, or external messaging takes place.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book = root / "book.pdf"
            recipient_mailer.make_text_pdf(book, ["Synthetic inherited proof"], width=432, height=648, margin=36, font_size=12, leading=16)
            job = json.loads((ROOT / "recipient-mailer/example-job.json").read_text())
            job["source_artifact"] = "book.pdf"
            job_file = root / "job.json"
            job_file.write_text(json.dumps(job))
            packet = root / "mail"
            recipient_mailer.build_packet(job_file, packet)
            self.assertEqual(recipient_mailer.check_packet(packet), [])
            init = argparse.Namespace(packet_dir=str(packet), carrier="synthetic-carrier", service="synthetic-service", allow_unprinted=False, note="test only")
            with self.assertRaisesRegex(ValueError, "must be marked printed"):
                dispatch_gate.cmd_init(init)
            recipient_mailer.mark_event(packet, "printed", "synthetic lifecycle only")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(dispatch_gate.cmd_init(init), 0)
                self.assertEqual(dispatch_gate.cmd_check(argparse.Namespace(packet_dir=str(packet))), 0)


if __name__ == "__main__":
    unittest.main()
