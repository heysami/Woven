# Displacement Ripple (interactive pointer-driven warp) (material)

**Tag:** material-displacement-ripple  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: displacement-ripple
  name: Displacement Ripple (interactive pointer-driven warp)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes (the ripple bends light)
    deforms: yes — local UV displacement
    age: ageless
  implementationStrategies:
    css: |
      /* limited — pure CSS can't do per-pixel displacement */
      transition: transform 0.3s ease-out;
      &:hover { transform: scale(1.02); }
    svg: |
      <feTurbulence baseFrequency="0.02 0.04" seed="<random>" /> →
      <feDisplacementMap scale="20" /> applied to backdropFilter.
      Animate seed for live ripple.
    webgl: |
      fragment shader: sample with uv displaced by sin(distance_from_pointer * k - time * v).
      Provides genuine ripple/wave deformation driven by pointer position.
    raster: not appropriate (needs live interaction)
  reactiveBehaviors:
    light: ripple bends light around the displacement
    highlight: pointer is the ripple origin
    depth: ripple = local depth perturbation
    parallax: subtle ripple on scroll velocity
  pairsWith:
    prototypeStyles: [style-liquid-glass, style-glassmorphism, style-aurorism, aesthetic-dreamcore, aesthetic-frutiger-aero, recipe-aurora-marketing]
  killsTheIllusion:
    - ripple amplitude > 30px (too cartoonish)
    - ripple over text (always readable rests > ripple)
    - displacement without coherent damping (rings should fade with distance)
  examples:
    - Apple Liquid Glass material (2025)
    - WebGL water demos
    - shadertoy ripple references
  references:
    - https://www.shadertoy.com/view/3lsXR4
```

## Common implementation mistakes (avoid these)

- ripple amplitude > 30px (too cartoonish)
- ripple over text (always readable rests > ripple)
- displacement without coherent damping (rings should fade with distance)

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `style-aurorism`
- `aesthetic-dreamcore`
- `aesthetic-frutiger-aero`
- `recipe-aurora-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1271–1311 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
