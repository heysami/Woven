---
materialId: corduroy
name: Corduroy (ribbed pile fabric)
family: analog
category: fabric
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-coastal-grandmother]
---

# Corduroy (ribbed pile fabric)

A matte surface that reacts to light: yes — directional pile reflects per-rib and deforms: yes.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — directional pile reflects per-rib

**Deforms**: yes

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    repeating-linear-gradient(90deg,
      rgba(0,0,0,0.18) 0px,
      transparent 6px,
      rgba(255,255,255,0.06) 8px,
      rgba(0,0,0,0.18) 12px
    ),
    oklch(50% 0.10 60);
raster: corduroy photograph
```

## Reactive behaviors

**Light**: rib shadow band shifts with pointer (corduroy's signature)

**Highlight**: per-rib gradient updates

**Depth**: minor press

**Parallax**: no

## Common implementation mistakes (avoid these)

- ribs without highlight asymmetry
- rib spacing too small (becomes Moiré) or too large (becomes stripes)

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-dark-academia`
- `aesthetic-coastal-grandmother`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
