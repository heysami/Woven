---
materialId: ink-bleed-on-paper
name: Ink Bleed (fountain pen / felt-tip on uncoated)
family: analog
category: ink
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-raster-cutout, style-doodle, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
---

# Ink Bleed (fountain pen / felt-tip on uncoated)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  filter: url(#inkBleed);
svg: |
  <filter id="inkBleed">
    <feMorphology operator="dilate" radius="0.4"/>
    <feGaussianBlur stdDeviation="0.6"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 12 -4"/>
  </filter>
raster: scanned ink for the highest fidelity
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: no

## Common implementation mistakes (avoid these)

- perfect type (ink bleeds organically)
- uniform stroke width (ink width varies with paper absorbency)

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `style-doodle`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
