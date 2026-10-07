import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"works/manga-index-001/index.json"
ANTH=ROOT/"works/manga-index-001/anthologies/the-house-takes-attendance-001.json"
TOOL=ROOT/"tools/manga_corpus.py"
def run(*a): return subprocess.run([sys.executable,str(TOOL),*map(str,a)],cwd=ROOT,check=True,capture_output=True,text=True)
def test_index_invariants(): assert "OK 19 issues / 100 pages" in run("verify",INDEX).stdout
def test_anthology_reconstructs(): assert "OK anthology 19 issues / 100 pages" in run("verify-anthology",INDEX,ANTH).stdout
def test_slots_and_authority():
    a=json.loads(ANTH.read_text(encoding="utf-8"))
    assert [s["slot"] for s in a["slots"]]==list(range(1,101))
    assert a["issueCount"]==19 and a["pageCount"]==100 and len(a["issueOrder"])==19
    assert a["authority"]=={"sourceMutation":False,"admission":False,"publication":False,"release":False}
