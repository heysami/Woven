---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-transit-ticket-ephemera-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-transit-ticket-ephemera-isolated.png
    reason: Signature motif, isolated.
---
# Transit ticket ephemera (aesthetic)

**Tag:** travel-document vernacular

**Canonical references:**
- IATA boarding pass stock - the segmented card, the perforated stub, the machine-readable strip
- Solari and split-flap departure boards - ranked rows, fixed columns, one status word per flight
- Airline rebrand systems (Lufthansa 2018, Swiss) - mono-spaced data grids against generous white card
- Ticket-wallet apps (mobile passes) - the pass as a precious object inside a dark chrome

## Cultural identity

The language of documents that get you somewhere: a white boarding-pass card, segmented into fields by hairlines and a perforated dashed divider, carrying a QR block and mono-spaced data - floated on a near-black gate-board surface whose only color is a single amber alert. Two registers, one system: the PASS is a bright paper artefact (city pairs set huge, "NYC -> PAR", a tear-off stub with seq and seat), and the BOARD is dark tabular rows (rank, time, flight, destination, gate, status) where "ON TIME" is quiet and "DELAYED" or "GATE CHANGED" earns the amber.

The pleasure is bureaucratic precision made tactile - the card feels tearable, the board feels live. Everything is data, but the data is printed on something.

## Palette anchor

Grayscale plus ONE alert. Never two accents.
- Paper white `oklch(100% 0 0)` (the pass)
- Panel gray `oklch(96% 0.003 250)`
- Surface `oklch(24% 0.006 260)` (the board)
- Deep black `oklch(15% 0.004 260)`
- Muted slate `oklch(55% 0.02 260)`
- Alert amber `oklch(83% 0.17 85)` - reserved for change, delay, and the one highlighted row

## Decoration motifs

- The perforated divider: dashed vertical rule separating card body from stub - the signature mark
- QR / barcode blocks as honest functional texture, never decoration
- Mono-spaced condensed caps for ALL data; huge airport-code pairs (three-letter city codes) as display
- Tabular board rows with fixed columns; the active row keylined in amber
- Field microlabels above values (FLIGHT / GATE / SEQ / ZONE), letterspaced tiny caps
- Status chips ("ON TIME", "GATE CHANGED") as small filled or keylined tags

## Voice register

Terse system-of-record. "GATE CHANGED." "BOARDING 14:30." "SEQ 0042." No adjectives, no reassurance beyond the data itself. Labels are nouns; statuses are verdicts.

## Failure mode

Amber used as a brand color on every button collapses the alert semantics - the change signal must stay rare. Rounded friendly sans and pastel chips turn it into a generic travel startup. And a screen of pure data rows with no document artefact is `recipe-bloomberg-dashboard`, not this: here the pass - segmented, perforated, tearable - is the hero object, and the board exists to serve it.

## Best for

- Flight, rail, and transit trackers; trip wallets and itineraries
- Event ticketing, check-in flows, queue and reservation systems
- Logistics and shipment tracking dressed as travel documents
- Any product whose core object is "a thing that admits you somewhere"

## Pairs well with

- Shells: `shell-mobile-app`, `shell-two-column-app`, `shell-centered-column`
- Styles: `style-dense-mono-dark` (the board side), `style-micro-text-frame`, `style-restrained-hairline` (the pass side)
- Aesthetic kin: `aesthetic-transit-wayfinding-signage` (the signage sibling - same airport, different surface)
