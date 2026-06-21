---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-op-art-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-op-art-isolated.png
    reason: Signature motif, isolated.
---
# Op Art / Moiré (aesthetic)

**Tag:** `aesthetic-op-art`

**Canonical references:**
- Bridget Riley - sine-warped grids and Cataract vermillion/turquoise stripes; the patient eye.
- Victor Vasarely - Vega cobalt/orange optical cubes; rigorous geometry as a popular language.
- MoMA "The Responsive Eye" 1965 - the moment Op Art entered the museum and the magazine cover.
- The Designers Republic - Sheffield post-punk graphic rigor; pattern as identity, not garnish.
- HelloMe for Warp Records - contemporary heirs; moiré sleeves for Oneohtrix Point Never, Aphex Twin reissues.

## Cultural identity

A mid-1960s art movement that treated the page as a perceptual instrument: rigorous black-and-white (or strict two-tone) geometry tuned to vibrate against the retina. Peaks at the "Responsive Eye" show, gets absorbed into Pan Am-era Swiss graphic design, then into Sheffield/Warp electronic-music sleeves in the 1990s, then into contemporary type-foundry and gallery microsites. The mood is editorial-museum, not psychedelic: cool, mathematical, declarative - the illusion does the emotional work, the chrome stays austere.

It signals: this object is a considered art object, the reader is being trusted with their own eyes, the brand owns its own grammar. It rejects: warmth, ornament, persuasion. Adjacent but distinct from psychedelia (which is hot, organic, hand-drawn) and brutalism (which is messy, anti-design); Op Art is cold, geometric, and pristinely produced.

## Palette anchor

- Ground: paper `#FAFAF7` or ink `#0A0A0A` - pick one, the other is the figure.
- Optical mid-grey `#8A8A8A` for hover/disabled only.
- Limited-palette dialect: exactly one saturated pair, never three accents.
  - Warp purple `#5B2E91`
  - Riley Cataract: vermillion `#E63946` + turquoise `#2EC4B6`
  - Vasarely Vega: cobalt `#1E3A8A` + orange `#F77F00`

## Decoration motifs

- Moiré interference: two layers of 1px strokes with a 2px gap, offset 1-3px and/or rotated 0.5-2°.
- Vertical stripes at integer pixel widths (3/3 or 4/4) - never anti-aliased mush.
- Concentric rings, sine-warped grids, optical cubes (Vasarely), bent-square fields (Riley).
- Catalogue numbering (WARP001, FIG. 03) as ornament - print-edition culture.
- Hard rectangular print-poster frames with generous quiet margins so the vibration is contained.

Forbidden vocabulary: gradients, gloss, drop-shadows, glows, blur, photographic imagery mixed with pattern, rainbow rather than strict two-tone. Op Art is mathematically flat.

## Voice register

Editorial, declarative, museum-wall-text. All-caps labels with letterspacing. Catalogue-numbered. No emoji, no exclamation marks, no marketing softeners. Microcopy reads like a Stedelijk caption or a Warp tracklist: "FIG. 03 / CATARACT / 1967 / EMULSION ON LINEN."

## Failure mode

Animated moiré spinning behind body text so paragraphs vibrate unreadable. Rainbow stripes instead of strict two-tone (gradients destroy the value contrast the illusion needs). Drop-shadows or glows on the pattern. Serif or trendy display type instead of Swiss grotesque editorial chrome. Buttons styled as pattern tiles indistinguishable from decoration. Non-integer stroke widths producing anti-aliased mush instead of crisp fringes. Zero quiet zones - every surface vibrating, nowhere for the eye to rest.

## Best for

- Electronic music labels and album landing pages.
- Contemporary art gallery exhibition microsites.
- Type-foundry specimens and editorial showcases.
- Fashion-house lookbook pages.
- Generative-art portfolios.
- Festival and rave identity sites.
- Brutalist-adjacent editorial magazines.

Bad for: warm consumer products, anything that needs to feel cozy or human, dashboards with long reading sessions on patterned surfaces.

## Pairs well with

- Shells: `shell-editorial-broken-grid`, `shell-centered-column`, `shell-hero-stack`, `shell-bento-grid`, `shell-masonry`, `shell-canvas-floating`
- Styles: `style-oversized-neo-grotesque`, `style-restrained-hairline`, `style-brutalist-raw`, `style-terminal-mono`
