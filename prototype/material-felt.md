---
materialId: felt
name: Felt (matted wool, fuzzy)
family: analog
category: fabric
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-skeuomorphism (poker felt, billiards), aesthetic-dark-academia, aesthetic-cottagegoth]
---

# Felt (matted wool, fuzzy)

A matte surface and deforms: yes — squashes on press.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: yes — squashes on press

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background: oklch(45% 0.14 145);  /* poker green */
  filter: url(#feltFuzz);
svg: |
  <filter id="feltFuzz">
    <feTurbulence baseFrequency="3" numOctaves="2"/>
    <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0.15 0"/>
  </filter>
raster: photographed felt for accuracy
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: minor press deformation

**Parallax**: no

## Common implementation mistakes (avoid these)

- smooth colour with no fuzz
- no soft edges (felt cuts soft)

## Pairs with (prototype slugs)

- `style-skeuomorphism (poker felt`
- `billiards)`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
