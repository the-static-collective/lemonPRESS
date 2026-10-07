# MANGA INDEX 001 — 19-issue source corpus and anthology press

**Status:** indexed source assemblies + anthology candidate  
**Base:** MANGA REMIX 001  
**Corpus:** 19 issues / 100 pages  
**Publication state:** none

MANGA INDEX 001 freezes the human-declared issue/page order of the assembled Google Drive manga shelf without copying image bytes into Git and without treating Drive folder order as authority.

## Laws

**ISSUE != FILE COLLECTION**  
**INDEX != ADMISSION**  
**DRIVE LOCATION != AUTHORITY**  
**ORDER != ANCESTRY**  
**ANTHOLOGY != SOURCE MUTATION**  
**READING ORDER != OWNERSHIP**  
**SLOT != PAGE IDENTITY**  
**SEQUENCE != ADMISSION**  
**CANDIDATE != RELEASE**

## Execute

```bash
python3 tools/manga_corpus.py verify works/manga-index-001/index.json
python3 tools/manga_corpus.py verify-anthology works/manga-index-001/index.json works/manga-index-001/anthologies/the-house-takes-attendance-001.json
python3 tools/manga_corpus.py press works/manga-index-001/index.json /tmp/anthology.json
```

The press emits declared reading order only. It never mutates, admits, publishes, downloads, or re-encodes a source page.
