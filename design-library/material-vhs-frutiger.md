---
materialId: vhs-frutiger
name: VHS-Frutiger (Frutiger Aero with VHS distortion)
family: hybrid
category: digital-effect
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-cassette-futurism]
images:
  - src: material-vhs-frutiger.png
    reason: Material fidelity sample.
---

# VHS-Frutiger (Frutiger Aero with VHS distortion)

A glossy surface (translucent) that reacts to light: yes and deforms: yes — VHS tracking bars.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes

**Deforms**: yes — VHS tracking bars

**Age / wear**: shows wear (drop-outs)

## Implementation strategies

```yaml
css: |
  filter: contrast(1.05) saturate(1.05);
svg: glass panel + VHS chromatic-aberration filter stack
raster: photographic plate + VHS overlay
video: 30fps VHS distortion loop atop the Frutiger glass scene
```

## Reactive behaviors

**Light**: glass highlight via pointer; VHS shifts at periodic intervals

**Highlight**: yes

**Depth**: minimal

**Parallax**: substrate parallaxes

## Common implementation mistakes (avoid these)

- VHS effect blocking the Frutiger water/sky motif (riso-style overlay should let plate through)

## Examples in the wild

- corporate-melancholic Vektroid record sleeves
- PrismCorp fake-multinational catalogues

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-y2k-myspace`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
