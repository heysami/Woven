---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-data-sublime-datamatics-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-data-sublime-datamatics-isolated.png
    reason: Signature motif, isolated.
---
# Data sublime / datamatics (aesthetic)

**Tag:** black-white data-as-surface minimalism

**Canonical references:**
- Ryoji Ikeda, *datamatics* / *test pattern* / *data-verse* - the founding corpus: pure data rendered at overwhelming density and scale.
- Carsten Nicolai (alva noto) - grid, sine, and interference works; the visual language of raster-noton.
- raster-noton sleeve design - barcode fields and hairline mono type as record-cover grammar.
- Ikeda's *the transfinite* installation - the floor-to-ceiling barcode strobe as physical space.
- Early oscilloscope and waveform test-pattern photography - the instrument imagery the movement abstracted.

## Cultural identity

The data sublime: information rendered so dense and so absolute that it tips into awe. The world is **pure black and pure white** - no grays as color, only optical grays produced by stripe density - and the decorative surface IS the data: **barcode stripe fields** whose widths encode signal, **sine lattices** drawn in hairline white, **numeric rasters** - columns of values ("000128  0.98321") - filling margins the way ornament once did. Type is hairline mono, letterspaced, small; the drama comes from scale contrast between a huge sparse headline and micro-dense data fields. Inversion is the only state change: white-on-black becomes black-on-white, instantly, without transition easing.

This is NOT `style-dense-mono-dark` - that is a product-UI style with charcoal surfaces, accent colors, and readable dashboards; datamatics is an ART register: absolute 1-bit contrast, zero accent hues, and data pushed past legibility into texture. And it is NOT `material-monospace-code-grid` - that is a background texture of code behind a normal UI; here the numeric raster is the entire compositional system - foreground, structure, and ornament at once.

## Palette anchor

Two values. That is the whole system:
- Field white `oklch(100% 0 0)` (#ffffff)
- Field black `oklch(0% 0 0)` (#000000)

No third color ever. Apparent midtones must be optical - produced by stripe frequency, dot density, or numeral crowding - never by a gray hex. Inversion (swapping the two) is the sole highlight, hover, and active mechanic.

## Decoration motifs

- **Barcode stripe fields** - vertical hairline-to-block stripes of varying width as headers, fills, button flanks, and dividers.
- **Sine lattices** - overlapping thin sine curves drifting through stripe fields and card interiors.
- **Numeric rasters** - dense columns of indexed values and binary matrices as marginal texture and card metadata.
- **Hairline rules** - 1px white (or black) borders; no fills, no shadows, no radius.
- **Scale violence** - display type enormous and sparse against data fields tiny and dense; nothing in between.
- **Inversion blocks** - active states as hard black/white swaps, including split half-inverted swatches.
- **Waveform readouts** - small sine/noise thumbnails as row ornaments in lists and streams.

## Voice register

Instrument nomenclature, uppercase mono, no rhetoric: "FIELD_01", "COHERENCE 0.88321", "SAMPLE RATE 48K", "EXECUTE", "ANALYZE". Underscores and indices instead of names; values instead of adjectives. The system does not address the user - it publishes its state. Any marketing warmth breaks the register instantly.

## Failure mode

A charcoal `#111` background with gray cards and a cyan accent = dense-mono product UI, not datamatics. The real thing tolerates no third value: black is #000, white is #fff, and every apparent gray must dissolve into stripes or digits on inspection. Also fatal: rounded corners, drop shadows, eased animations (state flips are instant), decorative glitch effects, or data that is obviously fake-random filler at low density - the sublime needs genuine overwhelming density, or the surface reads as a template with a barcode sticker.

## Best for

- Electronic-music releases, festivals, and label identities in the raster-noton lineage.
- Data-art installations, generative-art platforms, algorithm showcases.
- Research and instrumentation brands that want austere authority.
- Portfolio and gallery sites where the work benefits from a silent absolute frame.

## Pairs well with

- Shells: `shell-centered-column`, `shell-terminal-frame`, `shell-top-bar-canvas`
- Styles: `style-dense-mono-dark` (nearest product-UI kin when a build must soften), `style-micro-text-frame`, `style-restrained-hairline`
