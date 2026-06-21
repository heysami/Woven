---
materialId: parchment
name: Parchment / Vellum (animal hide, premium document)
family: analog
category: paper
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-defi-cosmic (achievement certificates)]
images:
  - src: material-parchment.png
    reason: Material fidelity sample.
---

# Parchment / Vellum (animal hide, premium document)

A matte surface and deforms: yes - curls dramatically at corners.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular but visible thickness

**Deforms**: yes - curls dramatically at corners

**Age / wear**: acquired patina (yellowing, blotches)

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(ellipse at 30% 20%, oklch(94% 0.04 70) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, oklch(86% 0.06 50) 0%, transparent 50%),
    oklch(91% 0.05 60);
  filter: contrast(1.05);
svg: |
  blotch turbulence pattern at low opacity
raster: real parchment scan ideal
```

## Reactive behaviors

**Light**: edge highlight only

**Highlight**: no

**Depth**: corner curl prominent

**Parallax**: no

## Common implementation mistakes (avoid these)

- uniform colour (parchment is naturally splotchy)
- perfect rectangle (parchment has irregular hand-cut edges)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-steampunk`
- `aesthetic-defi-cosmic (achievement certificates)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
