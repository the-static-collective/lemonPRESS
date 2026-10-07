# 2DAY CRAWLER HANDOFF

Status: declared house-level handoff.  
Executable implementation: `press/crawler` lane, PR #32.

## Objective

Expand the four declared public Suno playlists in **2DAY** into exactly 39 track occurrences while preserving each playlist as its own source object, then emit a Playdeck-ready cyclic traversal packet.

The main work declares the requirement. The crawler lane owns the implementation.

## Required result

A successful crawler crossing must return:

- four source playlist records in declared order;
- exactly 39 track occurrences total;
- each occurrence attached to its source playlist and source position;
- source IDs only when actually observed;
- the cycle `1 -> 2 -> 3 -> 4 -> 1`;
- a Playdeck handoff that does not mutate source ancestry.

## Refusal conditions

HOLD rather than silently accepting when:

- a public source cannot be read;
- structured playlist / track metadata is absent;
- a playlist title disagrees with the declared source;
- a per-playlist count disagrees with 11 / 7 / 12 / 9;
- the aggregate is not 39;
- source ordering drifts.

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

## Evidence boundary

The creator supplied the four public share URLs. Playlist titles, counts and durations were visually observed in the supplied screenshots. Canonical source IDs and the 39 exact track particulars remain unobserved in this house-level record until the crawler lane returns them from actual public source evidence.

The executable adapter, tests and schema live on the crawler production lane rather than being promoted into main merely because this work needs them.
