# Little Free Library — Release 001 — Crawler Edition

This branch is a retrieval-native projection of `LP-LFL-001`.

It is designed for partial reading, machine retrieval, source reconstruction, and relation discovery without pretending that retrieval equals complete reading.

## Books

### LP-NM-001 — nuMATHELOLOGY

A text-only crawler projection of the accepted First Edition. The print/source ancestor remains authoritative for typography and pagination.

- [Reader index](numathelology/README.md)
- [Full text projection](numathelology/FULL_TEXT.txt)
- chapter-addressable files in `numathelology/chapters/`

### LP-RD-001 — THE ROAD DREW ITSELF

This work is a composition of verbatim public Git source bodies. Rather than duplicate those bodies again, the crawler edition exposes the exact source-road map recovered from Source Edition 001.

- [Source map](road-drew-itself/SOURCE_MAP.md)

### LP-CLUE-001 — and THAT... will lead to another clue...

This work is also a composition of verbatim source bodies, primarily from `national-treasure`. The crawler edition exposes the source-road map recovered from Source Edition 001.

- [Source map](another-clue/SOURCE_MAP.md)

## Cross-book relation

Read [RELATIONS.md](RELATIONS.md).

The relation map is navigational metadata. It does not merge source authority among the books.

## Retrieval law

```text
fragment       != book
search hit      != context
source map      != source body
shared language != shared authority
projection      != ancestor
```

A crawler may enter anywhere. The edition therefore tries to leave enough local address information for a reader to recover the whole relation.
