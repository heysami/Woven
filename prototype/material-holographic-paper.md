---
materialId: holographic-paper
name: Holographic-Paper (iridescent foil on textured paper)
family: hybrid
category: iridescent
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [style-holographic, aesthetic-y2k-futurism, recipe-editorial-magazine]
---

# Holographic-Paper (iridescent foil on textured paper)

A glossy surface that reacts to light: yes — strong on foil, none on paper and deforms: yes — paper underneath.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes — strong on foil, none on paper

**Deforms**: yes — paper underneath

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* foil regions get the holographic recipe; rest is paper */
  background:
    url('paper-grain.jpg'),
    conic-gradient(in oklch from 45deg, /* full iridescence */) ;
raster: paper texture as ground; holographic mask
```

## Reactive behaviors

**Light**: foil reacts to pointer/gyro; paper doesn't

**Highlight**: yes — masked to foil region only

**Depth**: paper deformation possible

**Parallax**: paper static; foil rotates with gyro

## Common implementation mistakes (avoid these)

- iridescence over the whole card (must be foil REGIONS, like a Pokemon card)

## Examples in the wild

- foil-stamped business cards
- Pokemon card (the canonical reference)

## Pairs with (prototype slugs)

- `style-holographic`
- `aesthetic-y2k-futurism`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
