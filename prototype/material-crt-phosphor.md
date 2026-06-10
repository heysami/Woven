# CRT Phosphor (raster scan with subpixel RGB) (material)

**Tag:** material-crt-phosphor  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: crt-phosphor
  name: CRT Phosphor (raster scan with subpixel RGB)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — phosphor glow blooms with viewing angle
    deforms: no — but the surface curves
    age: shows wear (burn-in)
  implementationStrategies:
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
  reactiveBehaviors:
    light: phosphor bloom intensifies on bright content
    highlight: scanlines roll slowly (subtle pause-frame look)
    depth: barrel distortion is static
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-vaporwave, aesthetic-cyberpunk, style-pixel-bitmap]
  killsTheIllusion:
    - scanlines on already-pixel content (double pattern fights)
    - scanlines without subpixel RGB
    - flat scanline opacity (real phosphor varies)
    - missing the curvature (CRT is convex)
  examples:
    - libretro/glsl-shaders CRT-Royale
    - Vayce CRT Screen Effect
  references:
    - https://deepwiki.com/libretro/glsl-shaders/3.5-crt-aperture-and-specialized-effects
```

## Common implementation mistakes (avoid these)

- scanlines on already-pixel content (double pattern fights)
- scanlines without subpixel RGB
- flat scanline opacity (real phosphor varies)

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `style-pixel-bitmap`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 830–884 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
