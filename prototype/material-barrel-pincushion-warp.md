# Barrel / Pincushion Lens Warp (wide-lens optical distortion) (material)

**Tag:** material-barrel-pincushion-warp  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: barrel-pincushion-warp
  name: Barrel / Pincushion Lens Warp (wide-lens optical distortion)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: no
    deforms: yes — radial geometric distortion
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: none
    highlight: pointer can drag the warp center (off-axis lens)
    depth: warp = depth cue (fish-eye reads as wide-angle)
    parallax: scroll changes warp intensity for "zoom-breath" effect
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-y2k-futurism, aesthetic-cinematic, recipe-aurora-marketing, recipe-bento-marketing]
  killsTheIllusion:
    - applying to UI controls that need precise hit-targeting
    - warping without pixel-snap correction (creates moire)
    - applying without a vignette (real wide lenses also vignette)
  examples:
    - GoPro footage
    - fisheye music videos (early 2010s indie)
    - VR / 360-degree projection
  references:
    - https://en.wikipedia.org/wiki/Distortion_(optics)
```

## Common implementation mistakes (avoid these)

- applying to UI controls that need precise hit-targeting
- warping without pixel-snap correction (creates moire)
- applying without a vignette (real wide lenses also vignette)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-futurism`
- `aesthetic-cinematic`
- `recipe-aurora-marketing`
- `recipe-bento-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1228–1270 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
