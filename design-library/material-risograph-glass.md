---
materialId: risograph-glass
name: Risograph-Glass (frosted glass under riso grain)
family: hybrid
category: glass
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [aesthetic-acid-design, aesthetic-corporate-grunge, aesthetic-y2k-myspace]
images:
  - src: material-risograph-glass.png
    reason: Material fidelity sample.
---

# Risograph-Glass (frosted glass under riso grain)

A matte surface (translucent) that reacts to light: minimal.

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: minimal

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  backdrop-filter: blur(20px) saturate(160%);
  mix-blend-mode: multiply;
svg: |
  stack riso ink halftone over glass panel, slight offset
raster: riso grain overlay + photographic substrate
```

## Reactive behaviors

**Light**: no — riso kills the gloss

**Highlight**: no

**Depth**: hover lift only

**Parallax**: substrate parallaxes

## Common implementation mistakes (avoid these)

- glass sheen visible through the riso (riso must dominate top)

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-corporate-grunge`
- `aesthetic-y2k-myspace`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
