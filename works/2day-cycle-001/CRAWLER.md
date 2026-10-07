# 2DAY CRAWLER 001

Status: executable adapter; live four-playlist proof succeeded.

## Objective

Expand the four declared public Suno playlists in **2DAY** into exactly 39 track occurrences while preserving playlist identity, then emit a Playdeck-ready cyclic traversal packet.

## Command

```bash
python tools/suno_playlist_crawler.py press \
  works/2day-cycle-001/sources.json \
  --out works/2day-cycle-001/crawl
```

Success:

```text
pressed 39 track occurrences across 4 playlists
```

The command writes:

- `crawl/crawl.json` — normalized public-source evidence and recovered track occurrences;
- `crawl/playdeck-cycle.json` — the four-playlist loop with exact track occurrence references attached.

## Public-source path

For each source, the adapter:

1. follows the creator-supplied `suno.com/s/...` share URL;
2. records the canonical Suno playlist UUID returned by the public redirect / canonical URL;
3. retrieves public playlist metadata;
4. preserves source order and source IDs;
5. emits a separate LemonPRESS occurrence identity;
6. refuses the crossing if expected playlist or aggregate counts drift.

## Refusal conditions

The adapter HOLDS rather than silently accepting when:

- a public source cannot be read;
- canonical playlist identity cannot be established;
- a playlist title disagrees with the declared source;
- a playlist's recovered track count disagrees with 11 / 7 / 12 / 9;
- the aggregate does not equal 39 tracks;
- source ordering drifts.

A missing source ID is never invented.

One real source particular exposed an empty source title while remaining a complete track. Suno's UI presents that item as **Untitled**. The crawler therefore preserves both facts: `source_title: ""`, `title: "Untitled"`, and `title_state: "ui-fallback"`.

## Laws

```text
FETCHED != ADMITTED
PUBLIC != LICENSED
PLAYLIST != SONG
OCCURRENCE_ID != SOURCE_ID
ORDER != ANCESTRY
CYCLE != DUPLICATION
UNOBSERVED ID != INFERRED ID
EMPTY SOURCE TITLE != MISSING TRACK
UI FALLBACK != SOURCE REWRITE
```

## Playdeck seam

`playdeck-cycle.json` is a transport-neutral handoff. LemonPRESS owns declared occurrence order. Playdeck may decide temporal behavior, preload policy, transitions, shuffle overlays, or UI, but those behaviors do not rewrite source playlist ancestry.

The final playlist explicitly returns to slot 1.

## Proof

The first successful hosted run recovered all four canonical playlist identities and exactly **39** track occurrences from the live public sources. Unit tests and the live-crawl assertion both passed.

The committed live receipt / track witness records the specific proof run and its artifact digest. Formal LemonPRESS admission remains separate.
