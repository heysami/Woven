---
materialId: paper-marbling-ebru
name: Paper Marbling Ebru (combed floated-pigment print)
family: analog
category: print
surfaceFinish: matte
transparency: opaque
scope: both
pairsPrototypes: [style-serif-warm-paper, style-editorial-italic-accent, recipe-brand-story-journey, shell-centered-column, aesthetic-dark-academia]
images:
  - src: material-paper-marbling-ebru.png
    reason: Material fidelity sample.
---

# Paper Marbling Ebru (combed floated-pigment print)

A matte one-contact print: pigment floats on a thickened bath, is dragged into figures with a comb or stylus, then lifts onto paper in a single touch - crisp swirl edges, stone rings, and fine granular speckle frozen mid-flow.

**Distinct from** `material-watercolor-wash`, where pigment blooms INTO wet paper with soft feathered halos - ebru pigment sits ON a bath and keeps knife-sharp figure edges; and from `shader-organic-distortion`, a procedural live warp - ebru is a still, granular, physically lifted print with paper tooth in it.

## Physical behavior

**Surface finish**: matte (pigment film on soft cream paper)

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no - the figures are frozen at the moment of lift

**Age / wear**: ageless (archival print)

## Implementation strategies

```yaml
css: |
  /* Deep ink ground carrying combed veins of rose, indigo and ochre */
  background:
    radial-gradient(ellipse 12% 8% at 62% 30%, #D4A84C 0%, transparent 60%),  /* stone drop */
    conic-gradient(from 210deg at 40% 55%, #0F1F3A, #4D6A87 18%, #C97A7E 34%, #F5F1E6 46%, #0F1F3A 62%, #C97A7E 80%, #0F1F3A);
  /* comb-drag: repeat the figure vertically with alternating phase */
  filter: url(#ebru-comb);  /* feTurbulence + feDisplacementMap, LOW frequency, high amplitude */
svg: |
  feTurbulence baseFrequency="0.004 0.02" + feDisplacementMap scale="120" over striped
  gradients gives the getgel/nonpareil comb figure; overlay a sparse feTurbulence
  fractalNoise speckle layer for pigment granulation
raster: a real lifted marble scan is ground truth - tile crops for fills, strips for edges
usage: |
  object scope: fills inside display glyphs, button faces, card headers, hairline edge strips
  medium scope: full-bleed endpaper ground behind a calm cream content panel
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: subtle - the marbled ground may drift at a slower scroll rate than content, like paper behind a mat

## Common implementation mistakes (avoid these)

- soft blurry figure edges (ebru edges are crisp - blur reads as watercolor, not marbling)
- perfect symmetry (comb figures repeat with hand-drag wobble; use phase jitter per row)
- missing pigment granulation (flat vector swirls read as 90s clipart - add fine speckle)
- marbling everything (traditional ebru frames calm paper; keep large quiet cream fields)
- animating the swirls (the medium's whole character is arrested motion - one contact, one lift)

## Examples in the wild

- Ottoman and Turkish ebru manuscript borders
- marbled endpapers in classic bookbinding
- Payhip / craft-stationery brand identities using scanned marble crops

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `style-editorial-italic-accent`
- `recipe-brand-story-journey`
- `shell-centered-column`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
