import json
import sys
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import suno_playlist_crawler as crawler


class SunoPlaylistCrawlerTests(unittest.TestCase):
    def source(self, title, count, url):
        return {
            "title": title,
            "public_url": url,
            "expected_track_count": count,
            "expected_duration_minutes": 10,
        }

    def page(self, title, tracks, playlist_id="playlist-1"):
        payload = {
            "@context": "https://schema.org",
            "@type": "MusicPlaylist",
            "name": title,
            "id": playlist_id,
            "track": [
                {
                    "@type": "MusicRecording",
                    "name": item["title"],
                    "id": item.get("id"),
                    "duration": item.get("duration", "PT1M0S"),
                }
                for item in tracks
            ],
        }
        return (
            '<html><head><link rel="canonical" href="https://suno.com/playlist/example">'
            '<script type="application/ld+json">'
            + json.dumps(payload)
            + "</script></head></html>"
        )

    def fetcher_for(self, page):
        def fetcher(url):
            return {
                "requested_url": url,
                "final_url": "https://suno.com/playlist/example",
                "status": 200,
                "content_type": "text/html",
                "body": page,
                "body_sha256": crawler.sha256_text(page),
            }
        return fetcher

    def test_extracts_playlist_and_track_particulars(self):
        source = self.source("2day", 2, "https://suno.com/s/example")
        page = self.page("2day", [{"title": "A", "id": "a"}, {"title": "B", "id": "b"}])
        result = crawler.crawl_source(source, self.fetcher_for(page))
        self.assertEqual(result["playlist"]["track_count"], 2)
        self.assertEqual(result["source"]["source_playlist_id"], "playlist-1")
        self.assertEqual([t["title"] for t in result["tracks"]], ["A", "B"])
        self.assertTrue(result["tracks"][0]["occurrence_id"].startswith("lp-occurrence:"))

    def test_count_drift_holds_instead_of_silently_accepting(self):
        source = self.source("2day", 3, "https://suno.com/s/example")
        page = self.page("2day", [{"title": "A"}, {"title": "B"}])
        with self.assertRaises(ValueError):
            crawler.crawl_source(source, self.fetcher_for(page))

    def test_title_drift_holds(self):
        source = self.source("2day", 1, "https://suno.com/s/example")
        page = self.page("not-2day", [{"title": "A"}])
        with self.assertRaises(ValueError):
            crawler.crawl_source(source, self.fetcher_for(page))

    def test_source_id_can_remain_unobserved(self):
        source = self.source("2day", 1, "https://suno.com/s/example")
        page = self.page("2day", [{"title": "A"}], playlist_id="")
        result = crawler.crawl_source(source, self.fetcher_for(page))
        self.assertIsNone(result["source"]["source_playlist_id"])
        self.assertIsNone(result["tracks"][0]["source_id"])

    def test_cycle_returns_last_playlist_to_first(self):
        spec = {
            "work_id": "lemonpress:test",
            "title": "test",
            "expected_track_count": 2,
            "sources": [
                self.source("A", 1, "u1"),
                self.source("B", 1, "u2"),
            ],
        }
        crawls = [
            {"source": {"share_url": "u1", "source_playlist_id": None}, "tracks": [{"occurrence_id": "o1"}]},
            {"source": {"share_url": "u2", "source_playlist_id": None}, "tracks": [{"occurrence_id": "o2"}]},
        ]
        aggregate, playdeck = crawler.build_cycle(spec, crawls)
        self.assertEqual(aggregate["track_count"], 2)
        self.assertTrue(playdeck["loop"])
        self.assertEqual(playdeck["playlist_nodes"][1]["next_playlist_slot"], 1)


if __name__ == "__main__":
    unittest.main()
