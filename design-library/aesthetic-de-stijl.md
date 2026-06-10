---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-de-stijl-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-de-stijl-isolated.png
    reason: Signature motif, isolated.
---
# De Stijl / Neoplasticism (aesthetic)

**Tag:** aesthetic

**Canonical references:**
- Mondrian *Composition with Red Blue and Yellow* 1930 — the canonical asymmetric primary-on-white composition
- Rietveld Schroder House 1924 — the aesthetic translated into inhabitable architecture
- Theo van Doesburg / De Stijl journal masthead (1917-32) — the typographic manifesto
- YSL Mondrian collection 1965 — proof the aesthetic survives translation into another medium
- Architype Van Doesburg / Aubette — the 5x5 raster alphabet that IS the type system

## Cultural identity

A Dutch 1917-1931 art-and-architecture movement built on a single belief: reduce visual language to plane, primary colour, and right angle, and you reach a universal grammar. Mondrian, Van Doesburg, Rietveld, Huszar. It is the moment European modernism decided ornament was a failure of nerve.

The aesthetic carries the weight of manifesto. It is not "minimalist" in the contemporary sense — it is doctrinal. Every choice is an exclusion. Curves are forbidden. Diagonals are forbidden (until Van Doesburg's late counter-composition heresy of 1924). Greys are forbidden. The white is not absence — it is the dominant element, ~60-70% of any composition, against which the three primaries are placed in unequal weight.

Invoking this aesthetic asserts cultural lineage with European high modernism: Bauhaus-adjacent, pre-war, intellectual, museum-grade. It is the opposite of warmth, intimacy, or play. It signals "we descend from manifestos."

## Palette anchor

Four colours, never more, never substituted:
- Titanium white `#F4F1EA` — oil-paint warm white, never `#FFFFFF`
- Red `#D9302F` — muted vermilion, not sRGB `#FF0000`
- Yellow `#F4D03F` — cadmium, not sRGB `#FFFF00`
- Blue `#1F4FA8` — ultramarine, not sRGB `#0000FF`
- Black `#0E0E0E` — never pure `#000`

The hexes matter because the sRGB primaries register as "Mondrian poster from a dorm room." The oil-paint values register as the actual canvases.

## Decoration motifs

- Heavy black bars (8-16px) as structural grid lines — they ARE the design, not borders
- Asymmetric blocks of unequal weight, anchored to corners, never centered
- One dominant colour per composition (typically blue or red), the others subordinate, yellow smallest
- Architype Van Doesburg / Aubette display lettering — the 5x5 raster alphabet
- Block-letter stencil numerals: `NR. 03 / 1924`, `COMPOSITIE`
- Forbidden: icons, chevrons, underlines, rounded corners, shadows, gradients, diagonals (except Van Doesburg counter-composition), greys, serifs

## Voice register

Declarative nouns and dates. Uppercase or sentence-case capitalised. No marketing register, no sentences, no second-person address.

- `COMPOSITIE`
- `INDEX`
- `NR. 03 / 1924`
- `RED YELLOW BLUE`
- `STEDELIJK / SCHILDERIJEN / 1917-1931`

Never: "Welcome to," "Discover," "Get started," "Learn more."

## Failure mode

The dorm-room Mondrian-tile-soup: a symmetric `repeat(3, 1fr)` grid where every cell is a primary colour (real Mondrians are ~70% white); `1px` CSS borders instead of `8-16px` structural black bars; sRGB primaries `#FF0000 #FFFF00 #0000FF` instead of the oil-paint values; Helvetica or Inter body type inside coloured cells; any `border-radius`, any `box-shadow`, any hover-lift; a "Sign up" pill anywhere on the canvas. The cheap version reads as Mondrian-by-IKEA. The genuine version reads as Stedelijk.

## Best for

- Art museums, especially Dutch / Bauhaus-lineage institutions
- Design schools and type foundries
- Fashion houses with a modernist lineage (post-YSL-Mondrian)
- Architecture practices
- Classical-music or chamber-ensemble sites
- Archive / index pages for cultural institutions
- Single-page manifestos or about pages where brand needs to assert intellectual lineage over usability
- Type-specimen pages for geometric grotesques

Not for: consumer SaaS, fintech, anything friendly, anything that needs to scale to many content types, anything where the user is supposed to feel welcomed.

## Pairs well with

- Shells: `shell-bento-grid` (asymmetric primary blocks as bento cells), `shell-editorial-broken-grid` (the orthogonal break-grid is native to De Stijl), `shell-hero-stack` (one dominant primary field as hero), `shell-centered-column` (for manifesto / about pages)
- Styles: `style-flat-design` (the plane-geometry substrate), `style-oversized-neo-grotesque` (when Architype is unavailable), `style-brutalist-raw` (shares the no-shadow / no-radius discipline), `style-restrained-hairline` (only if the bars are kept heavy elsewhere)
