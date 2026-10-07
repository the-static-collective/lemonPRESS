# 2DAY CRAWLER 001

Status: executable adapter, live crawl pending from an environment that can reach Suno.

## Objective

Expand the four declared public Suno playlists in **2DAY** into 39 track occurrences while preserving playlist identity and then emit a Playdeck-ready cyclic traversal packet.

## Command

```bash
python tools/suno_playlist_crawler.py press \
  works/2day-cycle-001/sources.json \
  --out works/2day-cycle-001/crawl
```

Expected success:

```text
pressed 39 track occurrences across 4 playlists
```

The command writes:

- `crawl/crawl.json` — normalized public-source evidence and all recovered track occurrences;
- `crawl/playdeck-cycle.json` — the same four-playlist loop with track occurrence references attached.

## Refusal conditions

The adapter HOLDS rather than silently accepting when:

- a playlist page does not expose a structured track list;
- a playlist title disagrees with the declared source;
- a playlist's recovered track count disagrees with the observed expected count;
- the aggregate does not equal 39 tracks;
- source ordering drifts.

A missing source playlist ID remains `null`. It is never synthesized.

## Laws

```text
FETCHED != ADMITTED
PUBLIC != LICENSED
PLAYLIST != SONG
OCCURRENCE_ID != SOURCE_ID
ORDER != ANCESTRY
CYCLE != DUPLICATION
UNOBSERVED ID != INFERRED ID
```

## Playdeck seam

`playdeck-cycle.json` is a transport-neutral handoff. LemonPRESS owns the declared occurrence order. Playdeck may decide temporal behavior, preload policy, transitions, shuffle overlays, or UI, but those behaviors do not rewrite source playlist ancestry.

The last playlist explicitly points back to slot 1.

## Current evidence boundary

The creator supplied the four public share URLs. Playlist titles, counts and durations were visually observed in the supplied screenshots. This chat runtime could not fetch Suno pages directly, so canonical source IDs and the 39 exact track particulars remain unobserved here.

The adapter is specifically designed so the first successful live run fills those fields from public structured metadata without inventing them.
