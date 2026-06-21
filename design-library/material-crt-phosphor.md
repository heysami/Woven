---
materialId: crt-phosphor
name: CRT Phosphor (raster scan with subpixel RGB)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-vaporwave, aesthetic-cyberpunk, style-pixel-bitmap]
images:
  - src: material-crt-phosphor.png
    reason: Material fidelity sample.
---

# CRT Phosphor (raster scan with subpixel RGB)

A glossy surface that reacts to light: yes - phosphor glow blooms with viewing angle.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes - phosphor glow blooms with viewing angle

**Deforms**: no - but the surface curves

**Age / wear**: shows wear (burn-in)

## Implementation strategies

```yaml
css: |
  .crt::after {
    content: '';
    position: absolute; inset: 0;
    background:
      repeating-linear-gradient(0deg,
        rgba(0,0,0,0.15) 0px,
        transparent 1px,
        transparent 2px,
        rgba(0,0,0,0.15) 3px
      ),
      repeating-linear-gradient(90deg,
        rgba(255,0,0,0.06) 0px,
        rgba(0,255,0,0.06) 1px,
        rgba(0,0,255,0.06) 2px
      );
    mix-blend-mode: multiply;
    pointer-events: none;
  }
svg: |
  barrel-distortion via <feDisplacementMap> driven by a radial gradient
  gives the CRT curvature
webgl: |
  fragment shader with phosphor mask, scanline darkness, and bloom is the
  highest-fidelity path. libretro CRT-Royale is the reference.
raster: optional CRT-curvature mask PNG
```

## Reactive behaviors

**Light**: phosphor bloom intensifies on bright content

**Highlight**: scanlines roll slowly (subtle pause-frame look)

**Depth**: barrel distortion is static

**Parallax**: none

## Common implementation mistakes (avoid these)

- scanlines on already-pixel content (double pattern fights)
- scanlines without subpixel RGB
- flat scanline opacity (real phosphor varies)
- missing the curvature (CRT is convex)

## Examples in the wild

- libretro/glsl-shaders CRT-Royale
- Vayce CRT Screen Effect

## References

- https://deepwiki.com/libretro/glsl-shaders/3.5-crt-aperture-and-specialized-effects

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `style-pixel-bitmap`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
