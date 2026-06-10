---
materialId: displacement-ripple
name: Displacement Ripple (interactive pointer-driven warp)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [style-liquid-glass, style-glassmorphism, style-aurorism, aesthetic-dreamcore, aesthetic-frutiger-aero, recipe-aurora-marketing]
images:
  - src: material-displacement-ripple.png
    reason: Material fidelity sample.
---

# Displacement Ripple (interactive pointer-driven warp)

A glossy surface (translucent) that reacts to light: yes (the ripple bends light) and deforms: yes — local UV displacement.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes (the ripple bends light)

**Deforms**: yes — local UV displacement

**Age / wear**: ageless

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: ripple bends light around the displacement

**Highlight**: pointer is the ripple origin

**Depth**: ripple = local depth perturbation

**Parallax**: subtle ripple on scroll velocity

## Common implementation mistakes (avoid these)

- ripple amplitude > 30px (too cartoonish)
- ripple over text (always readable rests > ripple)
- displacement without coherent damping (rings should fade with distance)

## Examples in the wild

- Apple Liquid Glass material (2025)
- WebGL water demos
- shadertoy ripple references

## References

- https://www.shadertoy.com/view/3lsXR4

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `style-aurorism`
- `aesthetic-dreamcore`
- `aesthetic-frutiger-aero`
- `recipe-aurora-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
