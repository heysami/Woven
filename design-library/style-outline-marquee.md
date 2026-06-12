---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-outline-marquee-ui.png
    reason: Style surface UI mockup.
  - src: style-outline-marquee-isolated.png
    reason: Signature surface, isolated.
---
# Outline marquee (style)

**Tag:** `style-outline-marquee`

**Canonical references:** NLF / Geex-Arts dark galleries (Fairs — Galleries — Information rows) · fashion-week microsites · kinetic-type posters translated to web

## Surface treatment

Display-size OUTLINE type repeated in horizontally drifting marquee rows — the typography is the texture, the wallpaper, and the navigation at once. Filled type is reserved for the focused/hovered item; everything else is stroke-only.

### The grammar

- 2-6 stacked marquee rows of display text (nav labels, section names, brand words), each drifting at slightly different speeds/directions
- Type is `-webkit-text-stroke: 1-2px` outline; the ACTIVE word fills solid on hover/focus
- Rows sit behind or between content layers — a floating image card can ride above them
- Drift is slow (30-80s per loop) and pauses on hover

### Background / color

- Dark default: `#0c0c0e` ground, outline strokes `rgba(255,255,255,0.35-0.6)`, filled state `#ffffff`
- Light variant: `#f4f3f0` ground, strokes `#1a1a1a` at 40%
- ONE accent permitted for the filled/hovered state

### Type stack

- Condensed or standard grotesque at 64-160px (Druk, Neue Haas Display, Archivo Expanded for wide variants)
- Stroke weight scales with size: 1px below 80px, 2px above
- Body copy elsewhere stays small and quiet — the marquees own all display energy

### Motion

`transform: translateX` loops via CSS animation (duplicate row content for seamless wrap); `animation-play-state: paused` on hover; respect `prefers-reduced-motion` (static rows, no drift).

## Failure mode

Fast scrolling-ticker speeds (it's ambient drift, not a stock ticker); outline type used for body copy (illegible); five accent colors; marquees plus another loud background system (the rows ARE the background).

## Best for

Galleries and exhibition sites, fashion and editorial archives, agency portfolios, event/festival navigation screens — anywhere the section NAMES are glamorous enough to be the decor.

## Pairs well with

- Shells: `shell-horizontal-scroll-stage` (the canonical pairing), `shell-canvas-floating`, `shell-editorial-broken-grid`
- Styles: `style-oversized-neo-grotesque` (host), `style-restrained-hairline` for content layers
- Aesthetics: `aesthetic-monochrome-tech-editorial`, fashion-editorial registers
