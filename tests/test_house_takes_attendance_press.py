import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"works/manga-index-001/press/001"

def test_reader_binding():
    r=json.loads((P/"digital-reader-001.json").read_text())
    assert r["status"]=="CANDIDATE"
    assert r["sourceIndex"]["issueCount"]==19
    assert r["sourceIndex"]["pageCount"]==100
    assert r["reader"]["pdfPageCount"]==102
    assert r["reader"]["sourcePageCount"]==100
    assert sum(r["reader"]["orientationProfile"].values())==100
    assert r["artifact"]["sha256"]=="f965f1325754893d17ec7892228426414d63924cfc4fa6b2cf6f8389488244be"
    assert r["authority"]=={"admission":False,"publication":False,"release":False}

def test_physical_selection_stays_open():
    b=json.loads((P/"physical-brief-001.json").read_text())
    assert b["status"]=="PROPOSAL"
    assert len(b["proposals"])==2
    assert b["authority"]["selection"] is False
    assert "trim selection" in b["heldDecisions"]
