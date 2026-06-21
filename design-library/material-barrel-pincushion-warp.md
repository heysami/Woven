---
materialId: barrel-pincushion-warp
name: Barrel / Pincushion Lens Warp (wide-lens optical distortion)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-y2k-futurism, aesthetic-cinematic, recipe-aurora-marketing, recipe-bento-marketing]
images:
  - src: material-barrel-pincushion-warp.png
    reason: Material fidelity sample.
---

# Barrel / Pincushion Lens Warp (wide-lens optical distortion)

A glossy surface and deforms: yes - radial geometric distortion.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes - radial geometric distortion

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* faked via transform: perspective + radial mask */
  transform: perspective(800px) rotateX(0.01deg);
  mask: radial-gradient(circle, black 60%, transparent 100%);
svg: |
  <feDisplacementMap scale="<intensity>"> driven by a radial gradient
  (white in center, black at edges) gives proper barrel distortion;
  invert the gradient for pincushion.
webgl: |
  vec2 ctr = uv - 0.5;
  float r2 = dot(ctr, ctr);
  uv -= ctr * r2 * k;       // k > 0 = barrel, k < 0 = pincushion
  Common k = 0.15-0.35 for noticeable warp.
raster: not appropriate
```

## Reactive behaviors

**Light**: none

**Highlight**: pointer can drag the warp center (off-axis lens)

**Depth**: warp = depth cue (fish-eye reads as wide-angle)

**Parallax**: scroll changes warp intensity for "zoom-breath" effect

## Common implementation mistakes (avoid these)

- applying to UI controls that need precise hit-targeting
- warping without pixel-snap correction (creates moire)
- applying without a vignette (real wide lenses also vignette)

## Examples in the wild

- GoPro footage
- fisheye music videos (early 2010s indie)
- VR / 360-degree projection

## References

- https://en.wikipedia.org/wiki/Distortion_(optics)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-futurism`
- `aesthetic-cinematic`
- `recipe-aurora-marketing`
- `recipe-bento-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
