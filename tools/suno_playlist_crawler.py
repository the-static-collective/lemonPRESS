#!/usr/bin/env python3
"""Public Suno playlist metadata crawler for LemonPRESS.

Stdlib only. It resolves a public Suno share URL, preserves the canonical
playlist identifier actually returned by Suno, fetches public playlist metadata,
normalizes track occurrences, and emits a Playdeck cycle packet.

FETCHED != ADMITTED
PUBLIC != LICENSED
OCCURRENCE_ID != SOURCE_ID
PLAYLIST != SONG
ORDER != ANCESTRY
UNOBSERVED ID != INFERRED ID
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

USER_AGENT = "LemonPRESS-SunoCrawler/0.2 (+https://github.com/the-static-collective/lemonPRESS)"
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


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
        tag = tag.lower()
        if tag == "script":
            self._in_script = True
            self._script_chunks = []
        elif tag == "meta":
            key = attr.get("property") or attr.get("name")
            value = attr.get("content")
            if key and value:
                self.meta[key.lower()] = value
        elif tag == "link":
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


def fetch_json(url: str, timeout: int = 25) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        body = response.read()
        text = body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        return {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": getattr(response, "status", 200),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "data": json.loads(text),
        }


def parse_page(page: str) -> PageParser:
    parser = PageParser()
    parser.feed(page)
    return parser


def public_title(parser: PageParser) -> str | None:
    value = parser.meta.get("og:title")
    if not value:
        return None
    if " by @" in value:
        value = value.split(" by @", 1)[0]
    elif value.endswith(" | Suno"):
        value = value[:-7]
    return value.strip() or None


def canonical_playlist_id(parser: PageParser, final_url: str) -> str | None:
    for value in (parser.canonical, final_url):
        if not value:
            continue
        match = UUID_RE.search(value)
        if match:
            return match.group(0).lower()
    return None


def json_values_from_html(page: str) -> list[Any]:
    parser = parse_page(page)
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
        if "self.__next_f.push(" in candidate:
            tail = candidate.split("self.__next_f.push(", 1)[1].strip()
            if tail.endswith(")"):
                tail = tail[:-1]
            try:
                pushed = json.loads(tail)
            except json.JSONDecodeError:
                continue
            values.append(pushed)
            if isinstance(pushed, list) and len(pushed) > 1 and isinstance(pushed[1], str):
                for line in pushed[1].splitlines():
                    _, sep, record = line.partition(":")
                    if not sep:
                        continue
                    record = record.strip()
                    if record.startswith(("{", "[")):
                        try:
                            values.append(json.loads(record))
                        except json.JSONDecodeError:
                            pass
    return values


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
        if isinstance(val, list) and val:
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
            candidates.append((score, obj, tracks))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1], candidates[0][2]


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
    meta = obj.get("metadata")
    if isinstance(meta, dict) and meta is not obj:
        return duration_seconds(meta)
    return None


def normalize_track(item: dict[str, Any], *, source_position: int, playlist_share_url: str):
    source_id = string_value(item, "id", "clip_id", "clipId", "song_id", "songId")
    raw_title = None
    for key in ("title", "name"):
        if key in item and isinstance(item[key], str):
            raw_title = item[key]
            break
    if raw_title is None:
        raise ValueError(f"track {source_position} has no title field")
    title = raw_title.strip() or "Untitled"
    title_state = "source" if raw_title.strip() else "ui-fallback"
    material = json.dumps(
        {
            "playlist_share_url": playlist_share_url,
            "source_position": source_position,
            "source_title": raw_title,
            "source_id": source_id,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "occurrence_id": "lp-occurrence:" + sha256_text(material),
        "source_id": source_id,
        "source_position": source_position,
        "title": title,
        "source_title": raw_title,
        "title_state": title_state,
        "duration_seconds": duration_seconds(item),
        "public_url": string_value(item, "url", "share_url", "shareUrl", "web_url", "webUrl"),
        "audio_url": string_value(item, "audio_url", "audioUrl"),
        "image_url": string_value(item, "image_url", "imageUrl", "cover_url", "coverUrl"),
        "created_at": string_value(item, "created_at", "createdAt"),
    }


def extract_api_items(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    containers = [data]
    for key in ("playlist", "data", "result"):
        if isinstance(data.get(key), dict):
            containers.append(data[key])
    for obj in containers:
        for key in ("playlist_clips", "playlistClips", "clips", "tracks", "items"):
            value = obj.get(key)
            if isinstance(value, list):
                out = []
                for item in value:
                    if isinstance(item, dict):
                        out.append(item.get("clip") if isinstance(item.get("clip"), dict) else item)
                return out
    return []


def fetch_public_playlist_tracks(
    playlist_id: str,
    *,
    expected_count: int | None,
    json_fetcher=fetch_json,
    max_pages: int = 100,
):
    tracks: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        url = f"https://studio-api.prod.suno.com/api/playlist/{playlist_id}/?page={page}"
        fetched = json_fetcher(url)
        items = extract_api_items(fetched["data"])
        if not items:
            pages.append(
                {
                    "page": page,
                    "url": fetched["final_url"],
                    "status": fetched["status"],
                    "body_sha256": fetched["body_sha256"],
                    "item_count": 0,
                    "public_track_item_count": 0,
                    "omitted_item_count": 0,
                }
            )
            break
        added = 0
        omitted = 0
        for item in items:
            sid = string_value(item, "id", "clip_id", "clipId", "song_id", "songId")
            title = string_value(item, "title", "name")
            status = string_value(item, "status")
            if not title and not (sid and status == "complete"):
                omitted += 1
                continue
            identity = sid or sha256_text(json.dumps(item, ensure_ascii=False, sort_keys=True, default=str))
            if identity in seen:
                continue
            seen.add(identity)
            tracks.append(item)
            added += 1
        pages.append(
            {
                "page": page,
                "url": fetched["final_url"],
                "status": fetched["status"],
                "body_sha256": fetched["body_sha256"],
                "item_count": len(items),
                "public_track_item_count": added,
                "omitted_item_count": omitted,
            }
        )
        if expected_count is not None and len(tracks) >= expected_count:
            break
        if added == 0:
            break
    if not tracks:
        raise ValueError("public playlist API returned no track metadata")
    return tracks, pages


def crawl_source(source: dict[str, Any], html_fetcher=fetch_html, json_fetcher=fetch_json):
    share_url = source["public_url"]
    fetched = html_fetcher(share_url)
    parser = parse_page(fetched["body"])

    observed_title = public_title(parser)
    expected_title = source.get("title")
    if expected_title and observed_title and observed_title.casefold() != expected_title.casefold():
        raise ValueError(f"playlist title mismatch: expected {expected_title!r}, got {observed_title!r}")

    expected_count = source.get("expected_track_count")
    playlist_id = canonical_playlist_id(parser, fetched["final_url"])

    structured = choose_playlist(json_values_from_html(fetched["body"]), expected_title)
    api_pages: list[dict[str, Any]] = []
    extraction = "html-structured"
    if structured:
        playlist_obj, raw_tracks = structured
        if not playlist_id:
            playlist_id = string_value(playlist_obj, "id", "playlist_id", "playlistId")
    else:
        if not playlist_id:
            raise ValueError("public page returned no canonical playlist id")
        raw_tracks, api_pages = fetch_public_playlist_tracks(
            playlist_id,
            expected_count=expected_count,
            json_fetcher=json_fetcher,
        )
        extraction = "public-playlist-api"

    tracks = [
        normalize_track(item, source_position=i, playlist_share_url=share_url)
        for i, item in enumerate(raw_tracks, start=1)
    ]
    if expected_count is not None and len(tracks) != expected_count:
        raise ValueError(
            f"{expected_title or share_url} expected {expected_count} tracks, public source yielded {len(tracks)}"
        )

    return {
        "schema_version": "suno-playlist-crawl-v0",
        "source": {
            "share_url": share_url,
            "final_url": fetched["final_url"],
            "canonical_url": parser.canonical,
            "source_playlist_id": playlist_id,
            "page_sha256": fetched["body_sha256"],
            "http_status": fetched["status"],
            "extraction": extraction,
            "api_pages": api_pages,
        },
        "playlist": {
            "title": observed_title or expected_title,
            "track_count": len(tracks),
            "expected_track_count": expected_count,
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
    nodes = []
    track_total = 0
    for slot, (source, crawl) in enumerate(zip(spec["sources"], crawls), start=1):
        if crawl["source"]["share_url"] != source["public_url"]:
            raise ValueError("source order drift")
        tracks = crawl["tracks"]
        track_total += len(tracks)
        nodes.append(
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
    return (
        {
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
        },
        {
            "schema_version": "playdeck-cycle-v0",
            "work_id": spec["work_id"],
            "title": spec["title"],
            "entry_playlist_slot": 1,
            "loop": True,
            "playlist_nodes": nodes,
            "track_count": track_total,
            "authority": {
                "selection": "declared-by-lemonpress-work",
                "admission": "pending",
                "transport": "external-public-source",
            },
        },
    )


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
        aggregate, playdeck = build_cycle(spec, crawls)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "crawl.json").write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.out / "playdeck-cycle.json").write_text(json.dumps(playdeck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"pressed {aggregate['track_count']} track occurrences across {len(crawls)} playlists")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
