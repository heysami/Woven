---
materialId: torn-edge
name: Torn Edge (paper / fabric / film)
family: analog
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-corporate-grunge]
images:
  - src: material-torn-edge.png
    reason: Material fidelity sample.
---

# Torn Edge (paper / fabric / film)

A matte surface and deforms: yes.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes

**Age / wear**: ageless (or shows wear)

## Implementation strategies

```yaml
css: |
  mask-image: url(torn-edge.svg);
  mask-size: cover;
  filter: drop-shadow(0 2px 1px rgba(0,0,0,0.18));
svg: |
  irregular fractal-noise mask along one edge:
  <feTurbulence baseFrequency="0.06"/> + <feComponentTransfer> threshold
raster: torn-paper PNG with alpha
```

## Reactive behaviors

**Light**: small shadow on hover

**Highlight**: no

**Depth**: hover lift 2px

**Parallax**: optional

## Common implementation mistakes (avoid these)

- rounded "torn" edges (real tear is irregular and SHARP at peaks)
- same tear pattern repeated

## Examples in the wild

- Hack Club Scrapbook
- SSENSE editorial torn type

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `aesthetic-cottagecore`
- `aesthetic-y2k-myspace`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
