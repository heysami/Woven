---
materialId: scanned-glass
name: Scanned Glass (digital glass on analog paper substrate)
family: hybrid
category: glass
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [aesthetic-cottagegoth, aesthetic-dark-academia, recipe-editorial-magazine]
---

# Scanned Glass (digital glass on analog paper substrate)

A glossy surface (translucent) that reacts to light: yes.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes

**Deforms**: no

**Age / wear**: shows wear

## Implementation strategies

```yaml
css: |
  /* Layer 1: paper substrate. Layer 2: glass panel. */
  background:
    url('paper-texture.jpg'),
    rgba(255,255,255,0.18);
  backdrop-filter: blur(20px) saturate(180%);
svg: paper grain + glass refraction filters stacked
raster: REQUIRED — paper substrate is the load-bearing element
```

## Reactive behaviors

**Light**: glass highlight tracks pointer; paper substrate doesn't

**Highlight**: yes

**Depth**: hover lift glass slightly above paper

**Parallax**: paper stays put; glass moves with viewport

## Common implementation mistakes (avoid these)

- both layers at same z (glass must SIT ON paper)
- no paper grain visible behind glass

## Examples in the wild

- editorial book design (glass insert over endpaper)
- museum archival labels (modern UI under aged paper)

## Pairs with (prototype slugs)

- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
