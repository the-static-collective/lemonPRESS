import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import manga_root_fork as fork

FOLDER = fork.ROOT / "works/jubilee-engine-root-fork-001"
A = "branch:the-last-stop-moved"
B = "branch:jubilee-engine"


class RootForkTests(unittest.TestCase):
    def setUp(self):
        self.root = fork.read(FOLDER / "root-fork.json")
        self.declarations = {b["id"]: fork.read(FOLDER / b["declaration"]) for b in self.root["siblings"]}
        self.crossings = fork.read(FOLDER / "crossings.json")

    def build(self):
        return fork.build(self.root, self.declarations, self.crossings)

    def test_founder_and_repeat_replay(self):
        packet = self.build()
        self.assertEqual(packet, self.build())
        states = fork.verify_packet(packet)
        self.assertNotEqual(packet["heads"][A], packet["heads"][B])
        self.assertEqual(states[B]["received"][0]["disposition"], "HOLD")
        self.assertEqual(states[B]["received"][0]["reason"], "someone may still be coming")
        for value in packet["objects"].values():
            if "forkRef" in value:
                self.assertEqual(value["forkRef"], packet["forkRef"])
            if value["schema"] == "lemonpress/manga-story-receipt/v0":
                self.assertEqual(value["donorFingerprint"], self.root["donor"]["sha256"])

    def test_b_mutation_does_not_mutate_a_or_donor(self):
        initial = self.build()
        self.declarations[B]["mutations"][0]["state"]["captions"] = ["independent local caption"]
        changed = self.build()
        self.assertEqual(changed["heads"][A], initial["heads"][A])
        self.assertEqual(changed["forkRef"], initial["forkRef"])
        self.assertNotEqual(changed["heads"][B], initial["heads"][B])

    def test_arrival_does_not_import_pov_interpretation_or_admission(self):
        packet = self.build()
        states = fork.verify_packet(packet)
        local_before = self.declarations[B]["mutations"][-1]["state"]
        for key in ("pov", "localChronology", "interpretation", "admission", "sequence", "captions", "authority"):
            self.assertEqual(states[B][key], local_before[key])
        self.assertNotEqual(states[A]["pov"], states[B]["pov"])

    def test_all_local_dispositions_do_not_promote_branch_admission(self):
        for disposition in ("HOLD", "ADMIT", "REFUSE", "RETURN"):
            self.crossings[0]["disposition"] = disposition
            state = fork.verify_packet(self.build())[B]
            self.assertEqual(state["received"][0]["disposition"], disposition)
            self.assertEqual(state["admission"], {"state": "pending", "receipt": None})
            self.assertEqual(state["authority"], fork.AUTHORITY)

    def test_a_admission_is_independent_of_b(self):
        admitted = {"state": "admitted", "receipt": "declared-local:a-admission-001"}
        self.root["siblings"][0]["admission"] = admitted
        self.declarations[A]["initial"]["admission"] = admitted
        states = fork.verify_packet(self.build())
        self.assertEqual(states[A]["admission"], admitted)
        self.assertEqual(states[B]["admission"]["state"], "pending")

    def test_disappearing_sibling_cache_cold_replay(self):
        for branch in (A, B):
            portable = fork.export_branch(self.build(), branch)
            self.assertEqual(set(portable["heads"]), {branch})
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "branch.json"
                fork.write(path, portable)
                result = subprocess.run([sys.executable, str(fork.ROOT / "tools/manga_root_fork.py"), "cold", str(path)], cwd=folder, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(fork.verify_packet(portable)[branch], fork.verify_packet(self.build())[branch])

    def test_received_receipt_keeps_exact_emission_and_origin_history(self):
        packet = fork.export_branch(self.build(), B)
        arrival = fork.verify_packet(packet)[B]["received"][0]
        receipt = packet["objects"][arrival["receiptRef"]]
        emission = packet["objects"][arrival["emissionRef"]]
        self.assertEqual(emission["kind"], "EMIT")
        self.assertEqual(emission["previous"], receipt["originHistoryHead"])
        self.assertEqual(emission["payload"]["receiptRef"], receipt["identity"])
        del packet["objects"][receipt["originHistoryHead"]]
        with self.assertRaisesRegex(ValueError, "missing ancestry"):
            fork.verify_packet(packet)

    def test_changed_receipt_and_broken_branch_chain_refuse(self):
        packet = self.build()
        receipt = next(v for v in packet["objects"].values() if v["schema"] == "lemonpress/manga-story-receipt/v0")
        receipt["particular"]["body"] = "a different chair"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            fork.verify_packet(packet)
        packet = self.build()
        packet["objects"][packet["heads"][B]]["previous"] = packet["heads"][A]
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            fork.verify_packet(packet)

    def test_rehashed_arrival_cannot_smuggle_source_state(self):
        for field in ("pov", "admission", "interpretation", "localChronology"):
            packet = self.build()
            head = packet["objects"].pop(packet["heads"][B])
            head["state"][field] = copy.deepcopy(packet["objects"][packet["heads"][A]]["state"][field])
            if field == "admission":
                head["state"][field] = {"state": "admitted", "receipt": "forged-arrival-promotion"}
            new = fork.identified({k: v for k, v in head.items() if k != "identity"})
            packet["objects"][new["identity"]] = new
            packet["heads"][B] = new["identity"]
            with self.assertRaisesRegex(ValueError, "arrival cannot inherit"):
                fork.verify_packet(packet)

    def test_foreign_fork_and_self_crossing_refuse(self):
        self.crossings[0]["receiver"] = A
        with self.assertRaisesRegex(ValueError, "sibling"):
            self.build()
        packet = self.build_without_crossing()
        receipt = next(v for v in packet["objects"].values() if v["schema"] == "lemonpress/manga-story-receipt/v0")
        bad = fork.identified({**{k: v for k, v in receipt.items() if k != "identity"}, "forkRef": "sha256:" + "0" * 64})
        with self.assertRaisesRegex(ValueError, "another fork"):
            fork.receive_receipt(packet["forkRef"], packet["objects"][packet["heads"][B]], bad, packet["heads"][A], "HOLD", "local hold")

    def build_without_crossing(self):
        return fork.build(self.root, self.declarations, [])

    def test_unknown_field_law_authority_and_duplicate_sibling_refuse(self):
        for mutate in [lambda r: r.update(secret=True), lambda r: r["laws"].pop(), lambda r: r["authority"].update(canonOverSibling=True), lambda r: r["siblings"].append(copy.deepcopy(r["siblings"][0]))]:
            root = copy.deepcopy(self.root)
            mutate(root)
            with self.assertRaises(ValueError):
                fork.build(root, self.declarations, self.crossings)

    def test_admission_and_receipt_arrival_cannot_be_invented(self):
        self.declarations[B]["initial"]["received"] = [{"receiptRef": "sha256:" + "a" * 64, "emissionRef": "sha256:" + "b" * 64, "disposition": "ADMIT", "reason": "arrival is not genesis"}]
        with self.assertRaisesRegex(ValueError, "genesis"):
            self.build()
        self.declarations[B]["initial"]["received"] = []
        self.declarations[B]["mutations"][0]["state"]["admission"] = {"state": "admitted", "receipt": None}
        with self.assertRaisesRegex(ValueError, "independent receipt"):
            self.build()

    def test_source_bytes_and_create_only(self):
        data = b"synthetic donor for the byte gate"
        self.root["donor"].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "donor.bin"
            path.write_bytes(data)
            fork.verify_donor(self.root, path)
            path.write_bytes(data + b"!")
            with self.assertRaisesRegex(ValueError, "donor byte"):
                fork.verify_donor(self.root, path)
            output = Path(folder) / "packet.json"
            fork.write(output, self.build())
            fork.write(output, self.build())
            with self.assertRaisesRegex(ValueError, "create-only"):
                fork.write(output, {"different": True})

    def test_duplicate_arrival_and_out_of_bounds_region_refuse(self):
        self.crossings.append(copy.deepcopy(self.crossings[0]))
        with self.assertRaisesRegex(ValueError, "duplicate receipt"):
            self.build()
        self.crossings.pop()
        self.declarations[B]["initial"]["crop"] = [{"page": 11, "region": "outside source"}]
        with self.assertRaisesRegex(ValueError, "outside donor"):
            self.build()
