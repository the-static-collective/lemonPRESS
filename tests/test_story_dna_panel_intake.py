import copy
import importlib.util
import json
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools/story_dna_panel_intake.py"
spec = importlib.util.spec_from_file_location("story_dna_panel_intake", MODULE)
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


def storyboard():
    return {
        "schema": "story-dna/private-local-storyboard-preview/v0",
        "status": "HOLD",
        "source": {"title":"Keep a Place for Me","sha256":intake.SOURCE_SHA,
                   "sizeBytes":intake.SOURCE_BYTES,"durationSeconds":213.12},
        "sourcePlatformTrackId":None,
        "rights":"Public audio and real likeness permissions not established.",
        "panels":[{"id":f"KP{i:02}","at":(i-1)*25,"end":i*25,
                   "title":f"Scene {i}","view":f"A separate fictional candidate scene {i}.",
                   "palette":"Rain blue"} for i in range(1,6)]
    }


def svg(i):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#faf0df"/><path d="M{i} 20L300 440" stroke="#333" stroke-width="9"/></svg>'.encode() + b' '*80


def pictures():
    return {f"KP{i:02}":svg(i) for i in range(1,6)}


def pytest_raises(fn):
    try: fn()
    except (ValueError, FileNotFoundError): return
    assert False, "expected fail-closed refusal"


def test_five_source_pinned_unadmitted_images(tmp_path):
    source=storyboard()
    art=tmp_path/"art";art.mkdir()
    for key,payload in pictures().items(): (art/(key+".svg")).write_bytes(payload)
    j=tmp_path/"story.json";j.write_text(json.dumps(source))
    result=intake.build(j,art,tmp_path/"parcel")
    assert result["status"]=="HOLD" and result["pagesChecked"]==5
    manifest=intake.read_json(tmp_path/"parcel/manifest.json")
    assert manifest["publication"] is False and manifest["renderedVideo"] is False
    assert manifest["source"]["platformTrackId"] is None
    assert manifest["rights"]["sourceAudioBytesCarried"] is False
    assert all(p["caption"]==p["speech"]==p["sfx"]=="" for p in manifest["pages"])
    pytest_raises(lambda:intake.build(j,art,tmp_path/"parcel"))


def test_tampered_image_refused(tmp_path):
    data=storyboard();pictureset=pictures()
    parcel=intake.produce(data,pictureset)
    root=tmp_path; (root/"panels").mkdir()
    for key,payload in pictureset.items():(root/intake.image_path(key)).write_bytes(payload)
    assert intake.verify(parcel,root)["pagesChecked"]==5
    (root/intake.image_path("KP01")).write_bytes(pictureset["KP01"]+b"mutated")
    pytest_raises(lambda:intake.verify(parcel,root))


def test_forbid_scripted_external_or_untrusted_svg():
    for malicious in [
      b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>alert(1)</script></svg>',
      b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><a href="https://example.org">hi</a></svg>',
      b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><image onload="alert(1)" /></svg>',
      b'<!DOCTYPE svg [ <!ENTITY x SYSTEM "file:///etc/passwd"> ]><svg></svg>',
    ]:
      pytest_raises(lambda:intake.checked_svg(malicious+b' '*220))


def test_no_false_identity_canon_or_rights_promotion(tmp_path):
    source=storyboard()
    source["sourcePlatformTrackId"]="assumed-song-id"
    pytest_raises(lambda:intake.produce(source,pictures()))
    source=storyboard()
    source["rights"]="Licensed for worldwide public release"
    pytest_raises(lambda:intake.produce(source,pictures()))
    source=storyboard()
    source["panels"][1]["id"]="KP01"
    pytest_raises(lambda:intake.produce(source,pictures()))
    source=storyboard()
    parcel=intake.produce(source,pictures())
    parcel["ownerAdmission"]="ADMITTED"
    pytest_raises(lambda:intake.verify(parcel,tmp_path))
