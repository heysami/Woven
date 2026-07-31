---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-transit-wayfinding-signage-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-transit-wayfinding-signage-isolated.png
    reason: Signature motif, isolated.
---
# Transit wayfinding signage (aesthetic)

**Tag:** airport signage system

**Canonical references:**
- Amsterdam Schiphol (Benno Wissing / Paul Mijksenaar) - the canonical yellow, Frutiger-family humanist sans
- Adrian Frutiger's Roissy / Frutiger typeface - designed to be read at distance and in motion
- AIGA / DOT pictogram set 1974 - the inverted-tile symbol grammar
- Heathrow, Copenhagen, and JR East station signage - arrow-led direction rows on saturated panels

## Cultural identity

The design language of never being lost: a saturated signal-yellow field, humanist sans set black at heavy weights, white-on-black pictogram tiles, and an arrow grammar that always answers "which way." Content is organized like a terminal: destinations as headlines ("Departures", "Baggage Claim", "Gates A1-A12"), each locked to its pictogram tile and its directional arrow, with walk-time chips ("12 min" beside a walking figure) as the humane touch. Surfaces read as physical sign panels - satin-finish enamel, matte pictogram insets, perforated acoustic metal.

Unlike print modernism, this register is BUILT for glance-speed: fewer words, bigger type, one decision per panel. It is public-sector confident - authority without brand ego.

## Palette anchor

One saturated field, then achromatic discipline.
- Airport yellow `oklch(86% 0.17 92)` - the field itself, not an accent
- Jet black `oklch(17% 0 0)` - all type and tiles
- Signal white `oklch(100% 0 0)` - pictograms, reversed panels
- Graphite `oklch(35% 0.005 260)` and concrete `oklch(92% 0.002 90)` as structural neutrals

Yellow-field/black-ink may invert locally (black cards on yellow, yellow chips on black) but no third hue ever enters.

## Decoration motifs

- Inverted pictogram tiles: rounded-square black blocks with white symbols, always leading their label
- The arrow as a first-class glyph - directional chevrons and arrows terminate rows and buttons
- Hairline black rules dividing the field into sign-panel zones
- Walk-time chips: pictogram + minutes, the distance-to-gate gesture
- Satin panel sheen and perforated-metal texture as restrained physical cues
- Range notation ("D1-D57", "Gates A1-A12") set as display type

## Voice register

Directive and calm. "Departures." "Find gates." "Walk to gate: 12 min." Sentence-level copy stays functional-reassuring: "Clear information helps you move with confidence." Never marketing superlatives, never exclamation.

## Failure mode

Yellow demoted to an accent color on a white SaaS page kills it - the yellow IS the surface. Thin geometric type at small sizes fails the glance test; this register needs humanist letterforms at weight. Where `aesthetic-swiss-modernist` and `recipe-swiss-grid` pursue typographic composition on quiet paper, this is signage: if there is no pictogram tile and no arrow, you have drifted back into print modernism.

## Best for

- Travel, transit, and mobility products; maps and navigation flows
- Onboarding and step-by-step processes framed as a journey
- Logistics dashboards, venue and campus guides, event wayfinding
- Any UI whose core promise is "you will not get lost"

## Pairs well with

- Shells: `shell-mobile-app`, `shell-top-bar-canvas`, `shell-centered-column`
- Styles: `style-bold-display`, `style-flat-design`
- Aesthetic kin: `aesthetic-transit-ticket-ephemera` (the document sibling), `aesthetic-swiss-modernist` (the print ancestor to diverge from)
