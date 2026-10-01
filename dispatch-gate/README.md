# Dispatch Gate 001

Dispatch Gate begins after a recipient packet physically exists.

Recipient Mailer answers who the packet is for and prepares the private delivery data, note, book, and label. Dispatch Gate owns the next boundary: carrier/service selection, postage evidence, physical tender, transit, delivery, return, and hold.

```text
RECIPIENT MAILER
   prepared / printed packet
          ↓
   DISPATCH GATE
          ↓
 SERVICE SELECTED
          ↓
 POSTAGE ACQUIRED
          ↓
      TENDERED
          ↓
     IN TRANSIT
       ↙      ↘
 DELIVERED   RETURNED
```

## Laws

```text
LABEL != POSTAGE
POSTAGE != TENDER
TRACKING CREATED != IN TRANSIT
TENDER != DELIVERY
DELIVERED != READ
RETURNED != REJECTED
CARRIER EVENT != HUMAN INTERPRETATION
```

A tracking number proves only what the carrier record can support.

A delivered scan does not prove the recipient opened, read, liked, understood, or endorsed the work.

## Local-only data

A dispatch record may contain carrier transaction IDs, tracking numbers, postage prices, and local paths to provider labels. Treat the dispatch file as private fulfillment data.

Do not commit real dispatch records to the public repository.

## Commands

Initialize after Recipient Mailer reaches `printed`:

```bash
python tools/dispatch_gate.py init /tmp/lemonpress-example-mail \
  --carrier USPS \
  --service "Ground Advantage"
```

Record postage acquired through a carrier counter, website, or future adapter:

```bash
python tools/dispatch_gate.py postage /tmp/lemonpress-example-mail \
  --source "carrier website" \
  --cost-cents 487 \
  --currency USD \
  --tracking EXAMPLE123 \
  --label /path/to/carrier-label.pdf
```

Record physical crossings:

```bash
python tools/dispatch_gate.py mark /tmp/lemonpress-example-mail tendered \
  --note "accepted at counter"

python tools/dispatch_gate.py mark /tmp/lemonpress-example-mail in_transit
python tools/dispatch_gate.py mark /tmp/lemonpress-example-mail delivered
```

Other states:
- `held`
- `returned`

The state machine rejects impossible forward claims such as `delivered` before `tendered`.

## Future adapter seam

A postage adapter may eventually automate the external acquisition step. Its contract should return provider evidence only:

```text
carrier
service
transaction_id
cost
currency
tracking
label artifact
provider timestamp
```

The adapter may purchase postage only with explicit user authorization and a connected provider.

It does not gain authority to choose recipients, rewrite books, infer addresses, or treat delivery as readership.

## House fit

Physical Composer:
> What body could the work become?

Press Gate:
> Which physical edition actually crossed?

Recipient Mailer:
> Which particular person is this packet prepared for?

Dispatch Gate:
> What carrier crossing actually occurred?
