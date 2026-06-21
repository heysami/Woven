---
materialId: linen-weave
name: Linen Weave (Apple-linen / textbook substrate)
family: analog
category: fabric
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-skeuomorphism (iOS Game Center linen), aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-dark-academia]
images:
  - src: material-linen-weave.png
    reason: Material fidelity sample.
---

# Linen Weave (Apple-linen / textbook substrate)

A matte surface and deforms: yes - fabric drapes.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: yes - fabric drapes

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    repeating-linear-gradient(0deg,
      transparent 0px,
      rgba(0,0,0,0.04) 1px,
      transparent 2px
    ),
    repeating-linear-gradient(90deg,
      transparent 0px,
      rgba(0,0,0,0.04) 1px,
      transparent 2px
    ),
    oklch(80% 0.02 80);  /* warm beige */
svg: <feTurbulence baseFrequency="2"/> noise atop the weave
raster: scanned linen as ground truth
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: very subtle skew on scroll (drape)

**Parallax**: no

## Common implementation mistakes (avoid these)

- the weave at huge scale (you can't see it)
- the weave at sub-pixel scale (Moiré)
- no warmth in the colour (linen is naturally warm-cream)

## Examples in the wild

- iOS Game Center
- Apple Notification Center pre-iOS-7
- book endpapers

## Pairs with (prototype slugs)

- `style-skeuomorphism (iOS Game Center linen)`
- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
