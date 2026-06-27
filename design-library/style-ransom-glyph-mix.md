---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-ransom-glyph-mix-ui.png
    reason: Style surface UI mockup.
  - src: style-ransom-glyph-mix-isolated.png
    reason: Signature surface, isolated.
---
# Ransom glyph mix (style)

**Tag:** `style-ransom-glyph-mix`

**Canonical references:** GYRE Gallery exhibition microsites (per-character font classes over a hairline editorial chassis) · Tokyo exhibition-poster lineage (Tadanori Yokoo's collage-type descendants) · ransom-note paste-up canon laundered through contemporary art direction

## Surface treatment

Headlines and emphasized words are set CHARACTER BY CHARACTER across 4-6
deliberately clashing typefaces - one glyph ultra-bold, the next outline, the
next pixel, the next calligraphic serif, the next hand-drawn - while
everything else on the page stays quiet and systematic. The contrast engine is
*typeface plurality at the glyph level*, not size: body text can stay 14px and
headings 42px, and the page still reads as loud. Works in any script - the
device is per-glyph alternation, not any particular alphabet.

### The grammar

- Define 4-6 named display roles (e.g. `._heavy ._outline ._pixel ._script
  ._hand`) and wrap each heading character in a span carrying one role
- Distribution is ART-DIRECTED, not random-per-render: the same heading always
  wears the same sequence (decide once, bake it), with bold glyphs anchoring
  first/last positions
- Apply to: page title, section headings, 1-3 emphasized words inside prose
  pull-quotes. NEVER to: body copy, nav, buttons, captions
- The chassis around it is restrained-hairline discipline - hairline rules,
  small quiet labels, generous white. The ransom headline is the only loud
  layer; two loud layers and the page collapses
- Optional roulette entrance: glyphs slot-machine through 3-5 typeface states
  (80-120ms steps) before settling into their final face - settle order
  left-to-right, total under 900ms, play once

### Background / color

- Paper white `#ffffff` or near-white, ink `#333`-`#000`; the mixed glyphs
  themselves stay INK-colored by default - the clash is typographic, not
  chromatic
- ONE accent permitted, used on at most one glyph per heading or on the
  highlight-box behind an emphasized word
- Dark variant: ink field, paper glyphs; same one-accent rule

### Type stack

- The roles need genuine DISTANCE: pick one ultra-bold display, one
  outline/inline face, one pixel/bitmap face, one high-contrast serif or
  script, one hand-drawn - five weights of the same grotesque is NOT this style
- Body and UI run on one quiet sans (the system voice) at normal sizes
- Per-glyph kerning needs manual attention - clashing faces have clashing
  sidebearings; tighten optically, glyph pair by glyph pair

### Motion

Roulette shuffle on entrance (once) and optionally on hover for linked
headings; `steps()` timing, never smooth crossfades (the paste-up is discrete
by nature). Respect `prefers-reduced-motion`: glyphs render settled.

## Failure mode

Randomizing the faces per page-load (it's art direction, not a slot machine -
bake the sequence); applying the mix to body text or nav (instant illegibility
and the AI-collage tell); five similar grotesques instead of five different
TOOLS; adding a second loud system (marquee rows, sticker chaos) on top -
ransom headlines demand a silent room; using it at 14px (the device needs
display size to show each face's identity).

## Best for

Exhibition and gallery microsites, culture/music editorial, festival
identities, zine-register brand sites, any page whose subject IS plurality,
collision, or curation of many voices.

## Pairs well with

- Shells: `shell-centered-column`, `shell-editorial-broken-grid`, `shell-scroll-journey-scene`
- Styles: `style-restrained-hairline` (the mandatory quiet chassis)
- Aesthetics: `aesthetic-monochrome-tech-editorial`, `aesthetic-zine-type-wall`, `aesthetic-japanese-poster-layout`
