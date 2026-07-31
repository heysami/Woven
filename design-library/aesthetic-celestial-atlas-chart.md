---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-celestial-atlas-chart-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-celestial-atlas-chart-isolated.png
    reason: Signature motif, isolated.
---
# Celestial atlas chart (aesthetic)

**Tag:** scientific-romantic cartography

**Canonical references:**
- Johann Bode, *Uranographia* (1801) - the engraved star atlas at maximum ambition
- Elijah Burritt, *Atlas Designed to Illustrate the Geography of the Heavens* (1835)
- Norton's Star Atlas - the working observer's chart conventions
- Magnitude dot scales, right-ascension/declination grids, constellation stick figures
- Engraved compass roses, star-spoke ornaments and hairline chart borders

## Cultural identity

Antique celestial cartography as interface: deep navy chart paper gridded with faint coordinate lines, star fields plotted as white dots sized by a magnitude scale, constellations joined by hairline strokes, and everything measured - right ascension in hours, declination in degrees, values typeset like instrument readings. Display type is an engraved serif with true italics for star and constellation names (Orion, Cassiopeia), captions run in small letterspaced caps, and ember-red accents mark the active object, the compass ornament, the plotted target. The register is scientific-romantic: precision instruments in love with the sky.

Where `aesthetic-cosmic-horizon` renders photoreal space - nebula photography, lens flares, planetary vistas - celestial atlas chart never shows space itself, only the DRAWN MAP of it: dots, grids and engraved rules on paper-flat navy. And where `aesthetic-dark-academia` is bookish atmosphere (worn leather, candlelight, texture), this is drafting-table exactitude - the darkness is a chart ground, not a mood.

## Palette anchor

- Night navy `oklch(18% 0.035 255)`
- Ink blue `oklch(25% 0.045 255)`
- Star white `oklch(95% 0.01 85)`
- Ember red `oklch(62% 0.19 35)`
- Deep amber `oklch(40% 0.10 45)`
- Map amber `oklch(80% 0.11 70)`

Navy ground, white ink, one ember accent. Never a purple-pink nebula gradient; never pure black.

## Decoration motifs

- Coordinate grids: faint curved RA/dec lines at 10-15% white across every large surface
- Magnitude dot scale (six sizes) reused as bullet hierarchy, ratings and status indicators
- Constellation figures: white dots joined by hairline strokes, one glowing ember target ring
- Engraved star-spoke ornaments and compass roses as dividers and section finials
- Hairline double-rule borders with tiny corner stars framing panels and inputs
- Measured metadata everywhere: 05h 35m 17s, -05 deg 23', typeset as instrument readings

## Voice register

Observatory formality with quiet wonder: "The sky, measured." Latinate precision, star names in italics, units always shown. Numbers are the poetry - never exclamation, never space-opera drama, never "explore the infinite cosmos" marketing sublime.

## Failure mode

Swapping the chart ground for a photographic starfield collapses it into `aesthetic-cosmic-horizon` immediately - the drawn map is the whole premise. Glow effects on every star turn the chart into a night-club ceiling; only the active target glows. Randomly scattered decorative stars (not plotted, not sized by magnitude) betray the cartographic logic. A geometric sans display face breaks the engraved register; so does dropping the coordinates and units that make it feel measured.

## Best for

- Planetariums, observatories, astronomy tools and stargazing apps
- Almanacs, calendars, event timelines told as charts
- Navigation, mapping and precision-instrument brands
- Editorial features on the history of science; elegant data lookups

## Pairs well with

- Shells: `shell-infinite-canvas`, `shell-centered-column`, `shell-scroll-journey-scene`
- Styles: `style-restrained-hairline`, `style-editorial-italic-accent`, `style-micro-text-frame`
