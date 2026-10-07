#!/usr/bin/env python3
"""Suno public-playlist crawler for LemonPRESS.

Stdlib only. Follows a public share URL, extracts structured metadata from HTML,
normalizes tracks into occurrence records, and emits a LemonPRESS crawl envelope
plus a Playdeck traversal packet.

FETCHED != ADMITTED
PUBLIC != LICENSED
OCCURRENCE_ID != SOURCE_ID
PLAYLIST != SONG
ORDER != ANCESTRY
"""

from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.request import Request, urlopen

USER_AGENT = "LemonPRESS-SunoCrawler/0.1 (+https://github.com/the-static-collective/lemonPRESS)"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scripts: list[str] = []
        self.meta: dict[str, str] = {}
        self.canonical: str | None = None
        self._in_script = False
        self._script_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): v for k, v in attrs}
        if tag.lower() == "script":
            self._in_script = True
            self._script_chunks = []
        elif tag.lower() == "meta":
            key = attr.get("property") or attr.get("name")
            value = attr.get("content")
            if key and value:
                self.meta[key.lower()] = value
        elif tag.lower() == "link":
            rel = (attr.get("rel") or "").lower()
            href = attr.get("href")
            if "canonical" in rel and href:
                self.canonical = href

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            body = "".join(self._script_chunks).strip()
            if body:
                self.scripts.append(body)
            self._in_script = False
            self._script_chunks = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._script_chunks.append(data)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_html(url: str, timeout: int = 25) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=timeout) as response:
        body = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": getattr(response, "status", 200),
            "content_type": response.headers.get_content_type(),
            "body": body.decode(charset, errors="replace"),
            "body_sha256": hashlib.sha256(body).hexdigest(),
        }


def json_values_from_html(page: str) -> tuple[PageParser, list[Any]]:
    parser = PageParser()
    parser.feed(page)
    values: list[Any] = []
    for script in parser.scripts:
        candidate = html.unescape(script).strip()
        if not candidate:
            continue
        try:
            values.append(json.loads(candidate))
            continue
        except json.JSONDecodeError:
            pass
        for marker in ("__NEXT_DATA__ =", "window.__INITIAL_STATE__ =", "self.__next_f.push("):
            if marker not in candidate:
                continue
            tail = candidate.split(marker, 1)[1].strip().rstrip(";")
            if marker.endswith("push(") and tail.endswith(")"):
                tail = tail[:-1]
            try:
                values.append(json.loads(tail))
            except json.JSONDecodeError:
                pass
    return parser, values


def walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def tracks_from_candidate(obj: dict[str, Any]) -> list[dict[str, Any]] | None:
    for key in ("tracks", "songs", "clips", "playlist_clips", "playlistClips", "items"):
        val = obj.get(key)
        if not isinstance(val, list) or not val:
            continue
        out = []
        for item in val:
            if isinstance(item, dict):
                out.append(item.get("clip") if isinstance(item.get("clip"), dict) else item)
        if out:
            return out

    val = obj.get("track") or obj.get("itemListElement")
    if isinstance(val, list) and val:
        out = []
        for item in val:
            if isinstance(item, dict):
                out.append(item.get("item") if isinstance(item.get("item"), dict) else item)
        return out or None
    return None


def string_value(obj: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def duration_seconds(obj: dict[str, Any]) -> float | None:
    for key in ("duration_seconds", "durationSeconds", "duration"):
        value = obj.get(key)
        if isinstance(value, (int, float)) and value >= 0:
            return float(value)
        if isinstance(value, str):
            s = value.strip()
            if re.fullmatch(r"\d+(?:\.\d+)?", s):
                return float(s)
            m = re.fullmatch(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)", s)
            if m:
                return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            iso = re.fullmatch(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", s, re.I)
            if iso:
                return int(iso.group(1) or 0) * 60 + float(iso.group(2) or 0)
    return None


def choose_playlist(values: list[Any], expected_title: str | None = None):
    candidates = []
    for value in values:
        for obj in walk(value):
            if not isinstance(obj, dict):
                continue
            tracks = tracks_from_candidate(obj)
            if not tracks:
                continue
            title = string_value(obj, "title", "name", "playlist_name", "playlistName") or ""
            score = len(tracks) * 10
            if expected_title and title.casefold() == expected_title.casefold():
                score += 10000
            if "playlist" in str(obj.get("@type", "")).casefold():
                score += 500
            if any(k in obj for k in ("id", "playlist_id", "playlistId")):
                score += 50
            candidates.append((score, obj, tracks))
    if not candidates:
        raise ValueError("no structured playlist with tracks found in public page")
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, playlist, tracks = candidates[0]
    return playlist, tracks


def normalize_track(item: dict[str, Any], *, source_position: int, playlist_share_url: str):
    title = string_value(item, "title", "name")
    if not title:
        raise ValueError(f"track {source_position} has no title")
    source_id = string_value(item, "id", "clip_id", "clipId", "song_id", "songId")
    occurrence_material = json.dumps(
        {
            "playlist_share_url": playlist_share_url,
            "source_position": source_position,
            "title": title,
            "source_id": source_id,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "occurrence_id": "lp-occurrence:" + sha256_text(occurrence_material),
        "source_id": source_id,
        "source_position": source_position,
        "title": title,
        "duration_seconds": duration_seconds(item),
        "public_url": string_value(item, "url", "share_url", "shareUrl", "web_url", "webUrl"),
        "audio_url": string_value(item, "audio_url", "audioUrl"),
        "image_url": string_value(item, "image_url", "imageUrl", "cover_url", "coverUrl"),
        "created_at": string_value(item, "created_at", "createdAt"),
    }


def crawl_source(source: dict[str, Any], fetcher=fetch_html):
    share_url = source["public_url"]
    fetched = fetcher(share_url)
    parser, values = json_values_from_html(fetched["body"])
    playlist, raw_tracks = choose_playlist(values, source.get("title"))
    tracks = [
        normalize_track(item, source_position=i, playlist_share_url=share_url)
        for i, item in enumerate(raw_tracks, start=1)
    ]
    expected = source.get("expected_track_count")
    if expected is not None and len(tracks) != expected:
        raise ValueError(
            f"{source.get('title', share_url)} expected {expected} tracks, public page yielded {len(tracks)}"
        )
    source_playlist_id = string_value(playlist, "id", "playlist_id", "playlistId")
    title = string_value(playlist, "title", "name", "playlist_name", "playlistName") or source.get("title")
    if source.get("title") and title and title.casefold() != source["title"].casefold():
        raise ValueError(f"playlist title mismatch: expected {source['title']!r}, got {title!r}")
    return {
        "schema_version": "suno-playlist-crawl-v0",
        "source": {
            "share_url": share_url,
            "final_url": fetched["final_url"],
            "canonical_url": parser.canonical,
            "source_playlist_id": source_playlist_id,
            "page_sha256": fetched["body_sha256"],
            "http_status": fetched["status"],
        },
        "playlist": {
            "title": title,
            "track_count": len(tracks),
            "expected_track_count": expected,
            "expected_duration_minutes": source.get("expected_duration_minutes"),
        },
        "tracks": tracks,
        "authority": {
            "admitted": False,
            "licensed_by_fetch": False,
            "source_identity_inferred_when_missing": False,
        },
    }


def build_cycle(spec: dict[str, Any], crawls: list[dict[str, Any]]):
    if len(crawls) != len(spec["sources"]):
        raise ValueError("crawl count does not match source count")
    playlist_nodes = []
    track_total = 0
    for slot, (source, crawl) in enumerate(zip(spec["sources"], crawls), start=1):
        if crawl["source"]["share_url"] != source["public_url"]:
            raise ValueError("source order drift")
        tracks = crawl["tracks"]
        track_total += len(tracks)
        playlist_nodes.append(
            {
                "slot": slot,
                "title": source["title"],
                "share_url": source["public_url"],
                "source_playlist_id": crawl["source"].get("source_playlist_id"),
                "track_occurrences": [t["occurrence_id"] for t in tracks],
                "next_playlist_slot": 1 if slot == len(crawls) else slot + 1,
            }
        )
    expected_total = spec.get("expected_track_count")
    if expected_total is not None and track_total != expected_total:
        raise ValueError(f"cycle expected {expected_total} tracks, got {track_total}")
    aggregate = {
        "schema_version": "lemonpress-2day-crawl-v0",
        "work_id": spec["work_id"],
        "title": spec["title"],
        "kind": "public-playlist-cycle-crawl",
        "track_count": track_total,
        "playlists": crawls,
        "laws": [
            "FETCHED != ADMITTED",
            "PUBLIC != LICENSED",
            "PLAYLIST != SONG",
            "OCCURRENCE_ID != SOURCE_ID",
            "ORDER != ANCESTRY",
            "CYCLE != DUPLICATION",
        ],
    }
    playdeck = {
        "schema_version": "playdeck-cycle-v0",
        "work_id": spec["work_id"],
        "title": spec["title"],
        "entry_playlist_slot": 1,
        "loop": True,
        "playlist_nodes": playlist_nodes,
        "track_count": track_total,
        "authority": {
            "selection": "declared-by-lemonpress-work",
            "admission": "pending",
            "transport": "external-public-source",
        },
    }
    return aggregate, playdeck


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    press = sub.add_parser("press", help="crawl all public playlist sources and build cycle packets")
    press.add_argument("sources", type=Path)
    press.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "press":
        spec = read_json(args.sources)
        crawls = [crawl_source(source) for source in spec["sources"]]
        aggregate, playdeck_packet = build_cycle(spec, crawls)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "crawl.json").write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.out / "playdeck-cycle.json").write_text(json.dumps(playdeck_packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"pressed {aggregate['track_count']} track occurrences across {len(crawls)} playlists")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
