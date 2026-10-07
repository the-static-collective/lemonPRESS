import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
BOOK = SITE / "books" / "computer-book-001"
ORIGIN = "https://lemonpress-computer-books.vercel.app"


class Dissemination001Tests(unittest.TestCase):
    def test_root_discovery_files_exist(self):
        for name in ("index.html", "llms.txt", "robots.txt", "sitemap.xml", "feed.xml", "catalog.json"):
            self.assertTrue((SITE / name).is_file(), name)

    def test_catalog_names_canonical_origin(self):
        catalog = json.loads((SITE / "catalog.json").read_text())
        self.assertEqual(catalog["canonical_origin"], ORIGIN)
        self.assertEqual(catalog["books"][0]["work_id"], "lemonpress:computer-book-001")

    def test_robots_advertises_sitemap(self):
        text = (SITE / "robots.txt").read_text()
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /", text)
        self.assertIn(f"Sitemap: {ORIGIN}/sitemap.xml", text)

    def test_sitemap_is_valid_xml_and_contains_fragment_pages(self):
        root = ET.parse(SITE / "sitemap.xml").getroot()
        urls = {node.text for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
        self.assertIn(f"{ORIGIN}/books/computer-book-001/", urls)
        for fragment_id in ("001-enter-anywhere", "002-loss-is-visible", "003-order-is-not-ancestry"):
            self.assertIn(f"{ORIGIN}/books/computer-book-001/fragments/{fragment_id}/", urls)

    def test_atom_feed_is_valid_xml(self):
        root = ET.parse(SITE / "feed.xml").getroot()
        self.assertEqual(root.tag, "{http://www.w3.org/2005/Atom}feed")

    def test_every_fragment_has_three_carriers_and_machine_links(self):
        manifest = json.loads((BOOK / "manifest.json").read_text())
        for entry in manifest["fragments"]:
            directory = BOOK / "fragments" / entry["fragment_id"]
            self.assertTrue((directory / "index.html").is_file())
            self.assertTrue((directory / "index.md").is_file())
            self.assertTrue((directory / "fragment.json").is_file())
            html = (directory / "index.html").read_text()
            self.assertIn('rel="alternate" type="text/markdown"', html)
            self.assertIn('rel="alternate" type="application/json"', html)
            self.assertIn('rel="describedby"', html)
            carrier = json.loads((directory / "fragment.json").read_text())
            self.assertEqual(carrier["fragment_id"], entry["fragment_id"])
            self.assertEqual(carrier["authority"]["level"], "none")
            self.assertEqual(carrier["retrieval"]["warning"], "FRAGMENT != BOOK")

    def test_no_noindex_directive(self):
        for path in SITE.rglob("*.html"):
            self.assertNotIn("noindex", path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
