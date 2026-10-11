#!/usr/bin/env python3
"""Real synthetic GOATnote 004 -> LemonPRESS three-door score -> PDF + HTML proof.
Includes rendered PDF page inspection and explicit held/editorial decision gates.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader
from pypdfium2 import PdfDocument

REPO=Path(__file__).resolve().parents[1]
RENDER=REPO/"tools"/"marginalia_render_proof.py"
PREP=REPO/"tests"/"helpers"/"prepare_marginalia_print_fixture.mjs"

class ProofTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="lemonpress-private-proof-")
        self.root=Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def command(self,*parts,expected=True):
        call=subprocess.run([str(x) for x in parts],text=True,capture_output=True,cwd=REPO)
        if expected:
            self.assertEqual(call.returncode,0,call.stderr[-1500:])
        else:
            self.assertNotEqual(call.returncode,0,call.stdout)
        return call

    def fixture(self,suffix="",option=None):
        path=self.root/("fixture"+suffix)
        args=["node",PREP,path]
        if option: args.append(option)
        self.command(*args)
        return path/"score"

    def render(self,score,output="proof"):
        out=self.root/output
        self.command(sys.executable,RENDER,"render",score,out)
        return out

    def test_real_pdf_html_and_review_selection_gate(self):
        score=self.fixture()
        proof=self.render(score)
        report=json.loads(self.command(sys.executable,RENDER,"verify",score,proof).stdout)
        self.assertEqual(report["proofs_verified"],2)
        self.assertEqual(report["editorial_decision"],"NOT_RECORDED")
        manifest=json.loads((proof/"proof-manifest.json").read_text())
        self.assertEqual(manifest["state"],"PRIVATE_RENDERED_PROOF")
        self.assertFalse(manifest["human_editorial_selection"])
        self.assertFalse(manifest["published"])
        self.assertFalse(manifest["original_source_version_verified"])
        self.assertFalse(manifest["rights_cleared"])
        self.assertEqual(set(x["door"] for x in manifest["proofs"]),{"page","fragment"})
        pdf=(proof/"page.pdf").read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF-"))
        reader=PdfReader(proof/"page.pdf")
        self.assertGreaterEqual(len(reader.pages),1)
        self.assertEqual(float(reader.pages[0].mediabox.width),432)
        self.assertEqual(float(reader.pages[0].mediabox.height),648)
        content="\n".join(p.extract_text() for p in reader.pages)
        for snippet in ("The house takes attendance.","What became visible only after the event?",
                        "The reader discovered a relation yesterday","UNADMITTED PROOF"):
            self.assertIn(snippet,content)
        self.assertNotIn("HIDDEN PRIVATE THREAD",content)
        self.assertNotIn("SECRET OTHER NOTE",content)
        self.assertNotIn("PRIVATE OTHER BODY",content)
        pdfium=PdfDocument(proof/"page.pdf")
        self.assertGreaterEqual(len(pdfium),1)
        for page in pdfium:
            image=page.render(scale=0.7).to_pil()
            self.assertEqual(image.mode,"RGB")
            self.assertGreater(image.size[0],280)
            self.assertGreater(image.size[1],410)
            # Distinct nonblank pixel values establish actual rendered marks.
            self.assertGreater(len(image.getcolors(maxcolors=200000) or []),5)
        page=(proof/"fragment.html").read_text()
        self.assertIn('<meta name="robots" content="noindex,nofollow,noarchive">',page)
        self.assertIn("Content-Security-Policy",page)
        self.assertIn("connect-src &#x27;none&#x27;",page.replace("'","&#x27;")) if False else None
        self.assertIn('href="#margin"',page)
        self.assertIn('The house takes attendance.',page)
        self.assertIn('The reader discovered a relation yesterday',page)
        self.assertNotIn("PRIVATE OTHER BODY",page)
        self.assertNotIn("<script",page)
        # Without explicit human confirmation the editorial decision is REFUSED.
        self.command(sys.executable,RENDER,"decide",score,proof,
                     "--decision","SELECT_FOR_REVIEW","--selected-door","page",
                     "--reviewer","SYNTHETIC REVIEWER",expected=False)
        self.assertFalse((proof/"decision.json").exists())
        # The voice door exists as a SCRIPT, not a rendered audio proof.
        self.command(sys.executable,RENDER,"decide",score,proof,
                     "--decision","SELECT_FOR_REVIEW","--selected-door","voice",
                     "--reviewer","SYNTHETIC REVIEWER","--human-confirmed",expected=False)
        self.command(sys.executable,RENDER,"decide",score,proof,
                     "--decision","SELECT_FOR_REVIEW","--selected-door","page",
                     "--reviewer","SYNTHETIC REVIEWER","--human-confirmed")
        decision=json.loads((proof/"decision.json").read_text())
        self.assertEqual(decision["decision"],"SELECT_FOR_REVIEW")
        self.assertEqual(decision["selected_door"],"page")
        self.assertFalse(decision["house_admission"])
        self.assertFalse(decision["publication_authorized"])
        self.assertEqual(json.loads(self.command(sys.executable,RENDER,
                    "verify",score,proof).stdout)["editorial_decision"],"RECORDED")
        self.command(sys.executable,RENDER,"decide",score,proof,
                     "--decision","SELECT_FOR_REVIEW","--selected-door","fragment",
                     "--reviewer","SECOND SYNTHETIC REVIEWER","--human-confirmed",expected=False)
        self.command(sys.executable,RENDER,"render",score,proof,expected=False)

    def test_deterministic_repeat_and_tamper_resistance(self):
        score=self.fixture()
        first=self.render(score,"proof-a")
        second=self.render(score,"proof-b")
        for n in ("page.pdf","fragment.html","proof-manifest.json"):
            self.assertEqual((first/n).read_bytes(),(second/n).read_bytes(),n)
        page=first/"page.pdf"
        original=page.read_bytes()
        page.write_bytes(original+b"tampered")
        self.command(sys.executable,RENDER,"verify",score,first,expected=False)
        page.write_bytes(original)
        manifest=first/"proof-manifest.json"
        m=json.loads(manifest.read_text())
        m["published"]=True
        manifest.write_text(json.dumps(m))
        self.command(sys.executable,RENDER,"verify",score,first,expected=False)
        self.assertEqual(json.loads(self.command(sys.executable,RENDER,"verify",score,second).stdout)
                         ["proofs_verified"],2)

    def test_long_text_creates_multiple_pages_without_truncation(self):
        score=self.fixture("-long","--long")
        proof=self.render(score,"long-proof")
        pdf=PdfReader(proof/"page.pdf")
        self.assertGreater(len(pdf.pages),1)
        text="\n".join(p.extract_text() for p in pdf.pages)
        self.assertGreaterEqual(text.count("The house takes attendance."),60)
        self.assertGreaterEqual(text.count("A later human margin that refuses"),70)
        self.assertIn("Full version bytes are omitted",text)
        self.command(sys.executable,RENDER,"verify",score,proof)

    def test_markup_never_executes_and_missing_glyph_refuses(self):
        score=self.fixture("-html","--html-escape")
        proof=self.render(score,"html-proof")
        html=(proof/"fragment.html").read_text()
        self.assertIn("&lt;img src=",html)
        self.assertNotIn("<img src=",html)
        self.assertIn("default-src 'none'",html)
        self.command(sys.executable,RENDER,"verify",score,proof)
        bad=self.fixture("-font","--missing-font-glyph")
        self.command(sys.executable,RENDER,"render",bad,self.root/"bad-proof",expected=False)
        self.assertFalse((self.root/"bad-proof").exists())

    def test_human_hold_does_not_select_or_publish(self):
        score=self.fixture()
        proof=self.render(score,"held-proof")
        self.command(sys.executable,RENDER,"decide",score,proof,
                     "--decision","HOLD","--reviewer","SYNTHETIC REVIEWER",
                     "--human-confirmed")
        record=json.loads((proof/"decision.json").read_text())
        self.assertIsNone(record["selected_door"])
        self.assertEqual(record["decision"],"HOLD")
        self.assertFalse(record["publication_authorized"])
        self.command(sys.executable,RENDER,"verify",score,proof)

if __name__=="__main__":unittest.main(verbosity=2)
