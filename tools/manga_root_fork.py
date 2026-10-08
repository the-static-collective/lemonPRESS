#!/usr/bin/env python3
"""Independent branch histories and exact identified story-receipt crossings."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LAWS = ["ROOT != BRANCH", "SHARED SUBSTRATE != SHARED EVENT", "CROSSING != CANON COLLAPSE", "RECEIPT != SHARED POV", "SHARED PARTICULAR != SHARED HISTORY"]
AUTHORITY = {"houseAdmission": False, "publication": False, "canonOverSibling": False}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate(value, name):
    import jsonschema
    try:
        jsonschema.Draft202012Validator(read(ROOT / "schemas" / name)).validate(value)
    except jsonschema.ValidationError as exc:
        raise ValueError("schema: " + exc.message) from exc


def identified(body):
    value = copy.deepcopy(body)
    value["identity"] = "sha256:" + digest(body)
    return value


def check_identity(value):
    require(value.get("identity") == "sha256:" + digest({k: v for k, v in value.items() if k != "identity"}), "object identity mismatch")


def validate_root(root):
    validate(root, "manga-root-fork-v0.schema.json")
    require(root["laws"] == LAWS and root["authority"] == AUTHORITY, "root law/authority mismatch")
    ids = [b["id"] for b in root["siblings"]]
    require(len(ids) == len(set(ids)), "duplicate sibling id")
    for sibling in root["siblings"]:
        check_admission(sibling["admission"])
    for region in root["sharedRegions"]:
        require(region["page"] <= root["donor"]["pages"], "shared region outside donor")
    return root


def check_admission(admission):
    require((admission["state"] == "pending" and admission["receipt"] is None) or
            (admission["state"] == "admitted" and isinstance(admission["receipt"], str) and bool(admission["receipt"].strip())),
            "admission state requires an independent receipt")


def validate_state(state, root):
    validate(state, "manga-root-branch-state-v0.schema.json")
    require(state["authority"] == AUTHORITY, "branch authority cannot expand")
    check_admission(state["admission"])
    for placement in state["sequence"] + state["crop"]:
        require(placement["page"] <= root["donor"]["pages"], "page outside donor substrate")


def state_of(event):
    return event["state"]


def event(root_ref, branch, previous, kind, state, payload):
    return identified({"schema": "lemonpress/manga-root-event/v0", "forkRef": root_ref,
        "branchId": branch, "previous": previous["identity"] if previous else None,
        "index": previous["index"] + 1 if previous else 0, "kind": kind,
        "state": copy.deepcopy(state), "payload": copy.deepcopy(payload)})


def emit_receipt(root, root_ref, head, particular):
    require(bool(particular["body"].strip()), "empty receipt body")
    body = {"schema": "lemonpress/manga-story-receipt/v0", "forkRef": root_ref,
        "donorFingerprint": root["donor"]["sha256"], "originBranch": head["branchId"],
        "originHistoryHead": head["identity"], "particular": copy.deepcopy(particular),
        "authority": AUTHORITY.copy(), "identification": "content-addressed; not a cryptographic signature"}
    receipt = identified(body)
    validate(receipt, "manga-story-receipt-v0.schema.json")
    return receipt


def receive_receipt(root_ref, head, receipt, emission_ref, disposition, reason):
    check_identity(receipt)
    validate(receipt, "manga-story-receipt-v0.schema.json")
    require(receipt["forkRef"] == root_ref, "receipt from another fork")
    require(receipt["originBranch"] != head["branchId"], "receipt crossing must come from sibling")
    require(disposition in {"HOLD", "ADMIT", "REFUSE", "RETURN"}, "invalid disposition")
    require(isinstance(reason, str) and bool(reason.strip()), "disposition requires reason")
    # Arrival affects local history but leaves POV, sequence and admission independent.
    state = copy.deepcopy(state_of(head))
    state["received"].append({"receiptRef": receipt["identity"], "emissionRef": emission_ref, "disposition": disposition, "reason": reason})
    return event(root_ref, head["branchId"], head, "RECEIVE", state, {"receiptRef": receipt["identity"], "emissionRef": emission_ref})


def build(root, declarations, crossings):
    validate_root(root)
    require(set(declarations) == {b["id"] for b in root["siblings"]}, "branches must exactly cover sibling set")
    frozen_root = identified(root)
    root_ref = frozen_root["identity"]
    objects = {root_ref: frozen_root}
    heads = {}
    emitted = {}
    for sibling in root["siblings"]:
        branch_id = sibling["id"]
        declaration = declarations[branch_id]
        require(set(declaration) == {"initial", "mutations", "emissions"}, "unknown branch declaration")
        state = copy.deepcopy(declaration["initial"])
        validate_state(state, root)
        require(state["admission"] == sibling["admission"], "branch initial admission mismatch")
        require(not state["received"], "genesis cannot invent receipt arrival")
        head = event(root_ref, branch_id, None, "GENESIS", state, {"sharedSubstrateOnly": True})
        objects[head["identity"]] = head
        for mutation in declaration["mutations"]:
            require(set(mutation) == {"state", "reason"} and bool(mutation["reason"].strip()), "invalid local mutation")
            validate_state(mutation["state"], root)
            require(mutation["state"]["received"] == state_of(head)["received"], "mutation cannot invent receipt arrivals")
            head = event(root_ref, branch_id, head, "MUTATE", mutation["state"], {"reason": mutation["reason"]})
            objects[head["identity"]] = head
        for particular in declaration["emissions"]:
            receipt = emit_receipt(root, root_ref, head, particular)
            require(particular["id"] not in emitted, "duplicate receipt particular id")
            objects[receipt["identity"]] = receipt
            head = event(root_ref, branch_id, head, "EMIT", state_of(head), {"receiptRef": receipt["identity"]})
            objects[head["identity"]] = head
            emitted[particular["id"]] = (receipt, head["identity"])
        heads[branch_id] = head
    for crossing in crossings:
        require(set(crossing) == {"receiptId", "receiver", "disposition", "reason"}, "invalid crossing")
        require(crossing["receiptId"] in emitted and crossing["receiver"] in heads, "unknown crossing reference")
        receipt, emission_ref = emitted[crossing["receiptId"]]
        head = heads[crossing["receiver"]]
        require(not any(r["receiptRef"] == receipt["identity"] for r in state_of(head)["received"]), "duplicate receipt arrival")
        next_head = receive_receipt(root_ref, head, receipt, emission_ref, crossing["disposition"], crossing["reason"])
        objects[next_head["identity"]] = next_head
        heads[crossing["receiver"]] = next_head
    packet = {"schema": "lemonpress/manga-root-packet/v0", "forkRef": root_ref,
        "heads": {branch: head["identity"] for branch, head in heads.items()}, "objects": objects}
    verify_packet(packet)
    return packet


def verify_packet(packet):
    require(set(packet) == {"schema", "forkRef", "heads", "objects"} and packet["schema"] == "lemonpress/manga-root-packet/v0", "invalid root packet")
    objects = packet["objects"]
    for ref, value in objects.items():
        check_identity(value)
        require(ref == value["identity"], "object address mismatch")
    require(packet["forkRef"] in objects, "missing root")
    frozen_root = objects[packet["forkRef"]]
    root = {k: v for k, v in frozen_root.items() if k != "identity"}
    validate_root(root)
    siblings = {b["id"]: b for b in root["siblings"]}
    used = set()
    visiting = set()

    def walk(ref):
        require(ref in objects, "missing ancestry object")
        require(ref not in visiting, "ancestry cycle")
        if ref in used:
            return objects[ref]
        visiting.add(ref)
        value = objects[ref]
        if value["schema"] == "lemonpress/manga-root-fork/v0":
            require(ref == packet["forkRef"], "foreign root object")
        elif value["schema"] == "lemonpress/manga-story-receipt/v0":
            validate(value, "manga-story-receipt-v0.schema.json")
            require(value["forkRef"] == packet["forkRef"] and value["donorFingerprint"] == root["donor"]["sha256"], "receipt source mismatch")
            origin = walk(value["originHistoryHead"])
            require(origin["branchId"] == value["originBranch"], "receipt origin branch mismatch")
        else:
            require(set(value) == {"schema", "identity", "forkRef", "branchId", "previous", "index", "kind", "state", "payload"} and value["schema"] == "lemonpress/manga-root-event/v0", "invalid event fields")
            require(value["forkRef"] == packet["forkRef"] and value["branchId"] in siblings, "event source mismatch")
            validate_state(value["state"], root)
            previous = walk(value["previous"]) if value["previous"] else None
            if previous is None:
                require(value["kind"] == "GENESIS" and value["index"] == 0 and value["state"]["received"] == [] and value["state"]["admission"] == siblings[value["branchId"]]["admission"] and value["payload"] == {"sharedSubstrateOnly": True}, "invalid branch genesis")
            else:
                require(previous["schema"] == value["schema"] and previous["branchId"] == value["branchId"] and value["index"] == previous["index"] + 1, "branch histories cannot share event identity")
                if value["kind"] in {"EMIT", "RECEIVE"}:
                    require(set(value["payload"]) == ({"receiptRef"} if value["kind"] == "EMIT" else {"receiptRef", "emissionRef"}), "invalid receipt event payload")
                    receipt = walk(value["payload"]["receiptRef"])
                    require(receipt["schema"] == "lemonpress/manga-story-receipt/v0", "event requires story receipt")
                    if value["kind"] == "EMIT":
                        require(receipt["originBranch"] == value["branchId"] and receipt["originHistoryHead"] == previous["identity"] and value["state"] == previous["state"], "receipt emission mismatch")
                    else:
                        require(receipt["originBranch"] != value["branchId"], "self crossing")
                        received = value["state"]["received"]
                        require(len(received) == len(previous["state"]["received"]) + 1, "arrival must append one receipt")
                        arrival = received[-1]
                        require(arrival["receiptRef"] == receipt["identity"] and not any(r["receiptRef"] == receipt["identity"] for r in previous["state"]["received"]), "arrival receipt mismatch")
                        emission = walk(arrival["emissionRef"])
                        require(emission["kind"] == "EMIT" and emission["branchId"] == receipt["originBranch"] and emission["payload"]["receiptRef"] == receipt["identity"], "receipt emission provenance mismatch")
                        expected = receive_receipt(packet["forkRef"], previous, receipt, arrival["emissionRef"], arrival["disposition"], arrival["reason"])
                        require(expected == value, "arrival cannot inherit sibling POV, chronology, interpretation or admission")
                elif value["kind"] == "MUTATE":
                    require(set(value["payload"]) == {"reason"} and bool(value["payload"]["reason"].strip()), "invalid mutation reason")
                    require(value["state"]["received"] == previous["state"]["received"], "mutation cannot forge arrival")
                else:
                    raise ValueError("unknown event kind")
        visiting.remove(ref)
        used.add(ref)
        return value

    require(bool(packet["heads"]), "packet needs at least one local branch")
    walk(packet["forkRef"])
    for branch, ref in packet["heads"].items():
        head = walk(ref)
        require(branch in siblings and head.get("branchId") == branch, "local head branch mismatch")
    # Verify extra archived objects too, so a corrupted unused cache cannot hide.
    for ref in objects:
        walk(ref)
    return {branch: copy.deepcopy(objects[ref]["state"]) for branch, ref in packet["heads"].items()}


def export_branch(packet, branch):
    verify_packet(packet)
    require(branch in packet["heads"], "unknown export branch")
    selected = {}
    def collect(ref):
        if ref in selected:
            return
        value = packet["objects"][ref]
        selected[ref] = copy.deepcopy(value)
        for key in ("forkRef", "previous", "originHistoryHead"):
            if value.get(key):
                collect(value[key])
        for key in ("receiptRef", "emissionRef"):
            if value.get("payload", {}).get(key):
                collect(value["payload"][key])
    collect(packet["heads"][branch])
    result = {**packet, "heads": {branch: packet["heads"][branch]}, "objects": selected}
    verify_packet(result)
    return result


def verify_donor(root, path):
    data = Path(path).read_bytes()
    require(len(data) == root["donor"]["bytes"] and hashlib.sha256(data).hexdigest() == root["donor"]["sha256"], "donor byte identity mismatch")


def write(path, value):
    data = canon(value) + b"\n"
    path = Path(path)
    if path.exists():
        require(path.read_bytes() == data, "create-only conflict")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["compose", "verify", "export", "cold"])
    parser.add_argument("input")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--branch")
    parser.add_argument("--donor")
    args = parser.parse_args()
    if args.command in {"cold", "export"}:
        packet = read(args.input)
        states = verify_packet(packet)
        if args.donor:
            root = {k: v for k, v in packet["objects"][packet["forkRef"]].items() if k != "identity"}
            verify_donor(root, args.donor)
        if args.command == "export":
            require(args.branch is not None and args.output is not None, "export needs branch and output")
            packet = export_branch(packet, args.branch)
            write(args.output, packet)
    else:
        folder = Path(args.input)
        root = read(folder / "root-fork.json")
        declarations = {b["id"]: read(folder / b["declaration"]) for b in root["siblings"]}
        packet = build(root, declarations, read(folder / "crossings.json"))
        if args.donor:
            verify_donor(root, args.donor)
        require(args.output is not None, "compose/verify needs output")
        if args.command == "verify":
            require(read(args.output) == packet, "packet does not replay")
        else:
            write(args.output, packet)
        states = verify_packet(packet)
    print(json.dumps({"status": "PASS", "forkRef": packet["forkRef"], "branchHeads": packet["heads"], "donorBytes": "VERIFIED" if args.donor else "NOT_CHECKED", "houseAdmission": False}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
