---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-dancehall-fluoro-card-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-dancehall-fluoro-card-isolated.png
    reason: Signature motif, isolated.
---
# Dancehall fluoro card (aesthetic)

**Tag:** Soundsystem street poster - heavy black ink screened on fluorescent card stock

**Canonical references:**
- Jamaican dancehall / soundsystem session posters (Kingston, 1980s-2000s) - one ink, fluorescent day-glo card, stapled to poles and zinc fences
- UK reggae / bashment club flyers - the diaspora inheritance of the same print shop economics
- Letterpress-and-screenprint job-shop lineage: whatever wood type fits the sheet, printed heavy, misregistered where it lands
- Boxing and wrestling fight bills - the tabular date/venue skeleton the dance poster borrowed

## Cultural identity

The economics of the print shop ARE the aesthetic: one pass of heavy black ink over the loudest card stock the supplier carries (fluorescent yellow, then fluorescent pink when yellow runs out). Outline block caps stacked edge to edge so the sound names read from across the street; a brush-slash banner cutting across for the venue; and a tabular grid of date / day / act rows doing the information work. Coarse screened halftones stand in for photographs because photos cost a second pass.

The defining gesture is **the stack and the table**: names screamed in outline caps top-to-bottom, then dates settled in ruled rows - poster theater above, timetable bureaucracy below, on the same sheet.

Where `aesthetic-monochrome-pop-poster` floods the viewport with one clean saturated hue and stages a hero product in modern condensed caps, dancehall fluoro is CHEAP on purpose - the color comes pre-printed in the card, the ink sits coarse and slightly starved on top, and the layout skeleton is a job-shop table, not a campaign grid. And unlike `illust-typo-wood-type-letterpress` (a lettering treatment), this is a whole world: stock, ink, banner, table, and voice together.

## Palette anchor

Two substrates, one ink - never more:
- Fluo yellow card `oklch(94% 0.19 108)`
- Fluo pink card `oklch(72% 0.22 356)`
- Ink black `oklch(16% 0.01 0)`
- Screened black (halftone at 60%) reads as `oklch(55% 0.09 100)` over yellow
- Optional second-run pink ink `oklch(68% 0.24 358)` for a banner only

The card color is the background of EVERYTHING - no white anywhere, no gradients, no third hue.

## Decoration motifs

- Outline block caps (double-stroked, slightly rough) stacked full-width as the display voice
- One diagonal brush-slash banner in solid ink carrying the venue or date, knocked-out text inside
- Ruled tabular rows (date / day / act) as the structural skeleton - the table IS the layout
- Coarse halftone screens standing in for imagery; visible dot gain, clipped shadows
- Starved-ink and over-inked patches; edge wear from the staple gun
- Condensed all-caps body type, set tight, never lowercase

**Raster required:** the ink itself - brush-slash banner strokes, coarse halftone screen fills, and starved/heavy ink texture overlays (raster-foreground on transparent). The fluorescent card is CSS; the screenprint grit is not.

## Voice register

MC hype cadence, all caps, short: "BIG NIGHT.", "EARLY WARM.", "STRICTLY VIBES." Names before adjectives, dates before descriptions. Never explains, never apologizes, never lowercase.

## Failure mode

Clean vector outlines on a smooth gradient background with a drop shadow = a gig poster template, not a screened card. If the black is pure and crisp everywhere, the press ran too clean. White backgrounds, rounded-corner cards, or more than two stock colors on one page all break the print-shop economics that make the look. The table rows going borderless-minimal kills the skeleton.

## Best for

- Club nights, soundsystem sessions, festival lineups, mixtape drops
- Music-label and artist sites that want street-print urgency
- Event series with recurring date tables (residencies, weekly sessions)
- Merch drops and ticket pages where loud + cheap is the brand

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`, `shell-editorial-broken-grid`
- Styles: `style-bold-display`, `style-outline-marquee`, `style-brutalist-raw`
