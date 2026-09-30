# lemonPRESS House Constitution

lemonPRESS is one publishing house with multiple production floors.

The branch is a production context, not an authority rank.

## Shared identity

`main` owns only house-level facts:

- work identifiers
- catalog state
- house laws
- admission receipts
- declared relationships among works and editions
- the list of production lanes

It should not become the canonical storage location for every physical, digital, crawler, or archival artifact.

## Production floors

- `press/physical`
- `press/digital`
- `press/crawler`
- `press/archive`

A work may enter one lane, several lanes, or none.

Each lane may make format-native decisions while preserving declared ancestry.

## Admission

Drafting is not publication.

A work enters lemonPRESS when a house-level admission record identifies a specific source state strongly enough that later descendants can point back to it.

```text
AUTHORING / SOURCE WORLD
        ↓
   HUMAN ADMISSION
        ↓
   WORK OCCURRENCE
        ↓
 ┌──────┼────────┬─────────┐
 ↓      ↓        ↓         ↓
PRINT  DIGITAL  CRAWLER   ARCHIVE
```

The production branches do not silently pull "latest."

## Non-collapse laws

```text
SOURCE       != PROJECTION
WORK         != EDITION
EDITION      != FILE
FILE         != READING
RETRIEVAL    != COMPLETE READING
PROOF        != PUBLICATION
LATEST       != AUTHORIZED
DESCENDANT   != ANCESTOR
ARCHIVE      != VERDICT
```

## Version law

Old published editions remain historical occurrences.

A later edition may supersede one for ordinary distribution without erasing the earlier edition's birthday.

## Licensing

No house-wide license is assumed.

Each admitted work or edition must declare its applicable license or rights statement before public release.

## House question

> Can a work change carrier, scale, reader, medium, and production surface without losing where it came from?
