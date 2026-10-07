import json
import sys
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import suno_playlist_crawler as crawler

PID = "11111111-2222-3333-4444-555555555555"


class SunoPlaylistCrawlerTests(unittest.TestCase):
    def source(self, title="2day", count=3, url="https://suno.com/s/example"):
        return {
            "title": title,
            "public_url": url,
            "expected_track_count": count,
            "expected_duration_minutes": 10,
        }

    def html_result(self, title="2day", pid=PID, structured=None):
        extra = ""
        if structured is not None:
            extra = '<script type="application/ld+json">' + json.dumps(structured) + "</script>"
        page = (
            "<html><head>"
            f'<link rel="canonical" href="https://suno.com/playlist/{pid}">'
            f'<meta property="og:title" content="{title} by @tester | Suno">'
            + extra
            + "</head></html>"
        )
        return {
            "requested_url": "https://suno.com/s/example",
            "final_url": f"https://suno.com/playlist/{pid}?sh=example",
            "status": 200,
            "content_type": "text/html",
            "body": page,
            "body_sha256": crawler.sha256_text(page),
        }

    def json_fetcher(self, pages):
        state = {"index": 0}

        def fetch(url):
            index = state["index"]
            state["index"] += 1
            data = pages[index] if index < len(pages) else {"playlist_clips": []}
            body = json.dumps(data, sort_keys=True)
            return {
                "requested_url": url,
                "final_url": url,
                "status": 200,
                "body_sha256": crawler.sha256_text(body),
                "data": data,
            }

        return fetch

    def test_resolves_canonical_id_and_paginates_public_api(self):
        pages = [
            {
                "playlist_clips": [
                    {"clip": {"id": "a", "title": "A", "duration": 60}},
                    {"clip": {"id": "b", "title": "B", "duration": 61}},
                ]
            },
            {"playlist_clips": [{"clip": {"id": "c", "title": "C", "duration": 62}}]},
        ]
        got = crawler.crawl_source(
            self.source(),
            html_fetcher=lambda _: self.html_result(),
            json_fetcher=self.json_fetcher(pages),
        )
        self.assertEqual(got["source"]["source_playlist_id"], PID)
        self.assertEqual(got["source"]["extraction"], "public-playlist-api")
        self.assertEqual([t["title"] for t in got["tracks"]], ["A", "B", "C"])
        self.assertEqual(len(got["source"]["api_pages"]), 2)

    def test_structured_html_can_satisfy_without_api(self):
        payload = {
            "@type": "MusicPlaylist",
            "name": "2day",
            "track": [{"name": "A", "id": "a"}],
        }
        got = crawler.crawl_source(
            self.source(count=1),
            html_fetcher=lambda _: self.html_result(structured=payload),
            json_fetcher=lambda _: self.fail("API should not be called"),
        )
        self.assertEqual(got["source"]["extraction"], "html-structured")
        self.assertEqual(got["tracks"][0]["source_id"], "a")

    def test_untitled_api_tombstone_is_not_promoted_to_public_track(self):
        pages = [
            {
                "playlist_clips": [
                    {"clip": {"id": "a", "title": "A"}},
                    {"clip": {"id": "gone", "status": "failed"}},
                    {"clip": {"id": "b", "title": "B"}},
                ]
            }
        ]
        got = crawler.crawl_source(
            self.source(count=2),
            html_fetcher=lambda _: self.html_result(),
            json_fetcher=self.json_fetcher(pages),
        )
        self.assertEqual([t["title"] for t in got["tracks"]], ["A", "B"])
        self.assertEqual(got["source"]["api_pages"][0]["omitted_item_count"], 1)

    def test_complete_empty_title_survives_as_untitled_projection(self):
        pages = [
            {
                "playlist_clips": [
                    {"clip": {"id": "a", "title": "", "status": "complete"}}
                ]
            }
        ]
        got = crawler.crawl_source(
            self.source(count=1),
            html_fetcher=lambda _: self.html_result(),
            json_fetcher=self.json_fetcher(pages),
        )
        self.assertEqual(got["tracks"][0]["source_title"], "")
        self.assertEqual(got["tracks"][0]["title"], "Untitled")
        self.assertEqual(got["tracks"][0]["title_state"], "ui-fallback")

    def test_count_drift_holds(self):
        pages = [{"playlist_clips": [{"clip": {"id": "a", "title": "A"}}]}]
        with self.assertRaises(ValueError):
            crawler.crawl_source(
                self.source(count=2),
                html_fetcher=lambda _: self.html_result(),
                json_fetcher=self.json_fetcher(pages),
            )

    def test_title_drift_holds(self):
        pages = [{"playlist_clips": [{"clip": {"id": "a", "title": "A"}}]}]
        with self.assertRaises(ValueError):
            crawler.crawl_source(
                self.source(count=1),
                html_fetcher=lambda _: self.html_result(title="wrong"),
                json_fetcher=self.json_fetcher(pages),
            )

    def test_cycle_returns_last_playlist_to_first(self):
        spec = {
            "work_id": "lemonpress:test",
            "title": "test",
            "expected_track_count": 2,
            "sources": [
                self.source(title="A", count=1, url="u1"),
                self.source(title="B", count=1, url="u2"),
            ],
        }
        crawls = [
            {"source": {"share_url": "u1", "source_playlist_id": "p1"}, "tracks": [{"occurrence_id": "o1"}]},
            {"source": {"share_url": "u2", "source_playlist_id": "p2"}, "tracks": [{"occurrence_id": "o2"}]},
        ]
        aggregate, playdeck = crawler.build_cycle(spec, crawls)
        self.assertEqual(aggregate["track_count"], 2)
        self.assertTrue(playdeck["loop"])
        self.assertEqual([n["next_playlist_slot"] for n in playdeck["playlist_nodes"]], [2, 1])


if __name__ == "__main__":
    unittest.main()
