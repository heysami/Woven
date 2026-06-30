---
materialId: photocopy-xerox
name: Photocopy / Xerox (toner crush)
family: analog
category: print
surfaceFinish: matte
scope: medium
fxStack: [posterize, dither]
transparency: opaque
pairsPrototypes: [aesthetic-corporate-grunge, aesthetic-cottagegoth, aesthetic-web-brutalism, aesthetic-acid-graphics, aesthetic-curly-girly]
images:
  - src: material-photocopy-xerox.png
    reason: Material fidelity sample.
---

# Photocopy / Xerox (toner crush)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: shows wear (streaks, dirt)

## Implementation strategies

```yaml
css: |
  filter: grayscale(1) contrast(1.8);
  mix-blend-mode: multiply;
svg: |
  <feComponentTransfer> with steep sigmoid for toner crush;
  <feGaussianBlur stdDeviation="0.4"/> + <feColorMatrix> threshold for toner spread
webgl: |
  sigmoid contrast → grayscale → noise overlay → soft blur → threshold -
  matches CopyCat / Vayce algorithms
raster: photocopy texture overlays (Indieground packs) at multiply
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: stepped

## Common implementation mistakes (avoid these)

- clean colour photocopy (the look is mono-thresholded)
- no streaks or dirt (real Xerox is messy)
- smooth midtones (toner crushes midtones to black/white)

## Examples in the wild

- punk flyers
- underground zines
- photocopy-noise stock packs (Indieground)

## References

- https://vayce.app/tools/photocopy-scan-lines-effect/
- https://effect.app/effects/xerox

## Pairs with (prototype slugs)

- `aesthetic-corporate-grunge`
- `aesthetic-cottagegoth`
- `aesthetic-web-brutalism`
- `aesthetic-acid-graphics`
- `aesthetic-curly-girly`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
