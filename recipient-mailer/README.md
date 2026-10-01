# Recipient Mailer 001

Recipient Mailer is the last-mile physical crossing for lemonPRESS.

It takes an already selected physical edition artifact and prepares a **particular mail packet for a particular recipient** without mutating the master edition or pretending that delivery data belongs in publication metadata.

The first specimen came from a simple real workflow:

```text
WRITE / EDIT MASTER
        ↓
SELECT PHYSICAL EDITION
        ↓
PRESS GATE
        ↓
PARTICULAR RECIPIENT
        ↓
COVER NOTE + BOOK + MAILING LABEL
        ↓
PRINT
        ↓
MAIL
        ↓
DELIVER / RETURN / HOLD
```

## Core law

```text
MASTER != RECIPIENT COPY
RECIPIENT COPY != NEW CANON
PARTICULAR != MARKET SEGMENT
DELIVERY DATA != PUBLICATION METADATA
PREPARED != PRINTED
PRINTED != MAILED
MAILED != DELIVERED
```

A book may be written **for** one person or group. That does not make the person a demographic abstraction.

A normal edition may also be sent to one person with a particular note. That does not silently rewrite the edition.

## Two valid routes

### 1. Gift / review copy

The admitted or selected edition stays unchanged.

Recipient Mailer adds a separate cover note and mailing label around it.

Use this when the relation belongs to the **delivery occurrence**, not the book body.

### 2. Recipient edition

If the recipient-specific material genuinely belongs inside the book, first create and admit/select that descendant edition through the normal lemonPRESS ancestry and Press Gate workflow.

Then Recipient Mailer fulfills that edition.

This keeps:

```text
PERSONALIZATION != SILENT SOURCE MUTATION
```

## Privacy boundary

Postal addresses are operational delivery data.

**Do not commit generated recipient packets to a public repository.**

Recipient Mailer stores the street address only in the generated mailing-label artifact. Its manifest stores a SHA-256 fingerprint of the private recipient block so a local operator can detect accidental changes without promoting the address into house metadata.

Example files in this directory use fictional addresses only.

## Prepare a packet

Create a job JSON from `example-job.json`.

The `source_artifact` may be an existing print-ready PDF or another selected physical artifact. Relative paths resolve relative to the job file.

```bash
python tools/recipient_mailer.py prepare recipient-mailer/example-job.json \
  --out /tmp/lemonpress-example-mail
```

Output:

```text
/tmp/lemonpress-example-mail/
  README.md
  manifest.json
  artifacts/
    book.pdf
    cover-note.pdf
    mailing-label-4x6.pdf

/tmp/lemonpress-example-mail.zip
```

The renderer uses only the Python standard library. Cover notes are deliberately constrained to one page; the tool refuses overflow rather than silently truncating it.

## Verify

```bash
python tools/recipient_mailer.py check /tmp/lemonpress-example-mail
```

The check verifies declared byte counts and SHA-256 hashes.

## Record fulfillment

```bash
python tools/recipient_mailer.py mark /tmp/lemonpress-example-mail printed \
  --note "double-sided long edge"

python tools/recipient_mailer.py mark /tmp/lemonpress-example-mail mailed \
  --note "USPS"

python tools/recipient_mailer.py mark /tmp/lemonpress-example-mail delivered
```

Supported states:

- `prepared`
- `printed`
- `mailed`
- `delivered`
- `returned`
- `held`

The zip snapshot is refreshed when an event is marked.

## What this tool does not do

Recipient Mailer 001 does **not**:

- write the book;
- decide who deserves a book;
- scrape or infer postal addresses;
- buy postage;
- contact a recipient;
- declare delivery merely because a label exists;
- merge a personalized note into the canonical book body;
- authorize publication.

Those remain separate human or system crossings.

## House fit

Physical Composer asks:

> What body could this work become?

Press Gate asks:

> Which selected physical body actually crossed, and what are its receipts?

Recipient Mailer asks:

> Which particular person is this physical occurrence being carried toward, and what evidence distinguishes prepared, mailed, and delivered?
