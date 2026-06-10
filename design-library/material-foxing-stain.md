---
materialId: foxing-stain
name: Foxing / Tea Stain (paper aging)
family: analog
category: digital-effect
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [style-serif-warm-paper, aesthetic-dark-academia, aesthetic-cottagecore, aesthetic-cottagegoth]
---

# Foxing / Tea Stain (paper aging)

A matte surface (translucent).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: no

**Deforms**: no

**Age / wear**: acquired patina

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(ellipse at 18% 24%, oklch(70% 0.12 60 / 0.4) 0%, transparent 18%),
    radial-gradient(ellipse at 85% 65%, oklch(60% 0.10 50 / 0.3) 0%, transparent 22%),
    var(--paper);
  mix-blend-mode: multiply;
raster: scanned aged-paper for ground truth
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: tied to paper layer

## Common implementation mistakes (avoid these)

- symmetric stains (real foxing is asymmetric, lives where moisture pooled)
- stains over photos (paper-edge-only)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-dark-academia`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
