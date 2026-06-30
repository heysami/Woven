---
materialId: chromatic-aberration-lens
name: Lens Chromatic Aberration (radial RGB split toward corners)
family: digital
category: digital-effect
surfaceFinish: glossy
scope: both
fxStack: [chromatic-aberration]
transparency: opaque
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-cinematic, recipe-bento-marketing, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero]
images:
  - src: material-chromatic-aberration-lens.png
    reason: Material fidelity sample.
---

# Lens Chromatic Aberration (radial RGB split toward corners)

A glossy surface that reacts to light: yes - CA peaks at high-contrast luminance transitions.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes - CA peaks at high-contrast luminance transitions

**Deforms**: no (channels shift radially)

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* limited - CSS can fake at edges with two filter layers */
  filter: drop-shadow(-1px 0 0 #ff0044) drop-shadow(1px 0 0 #00ddff);
svg: |
  <feOffset> per channel via <feColorMatrix>, scaled by radial distance
  from frame center using <feDisplacementMap>.
webgl: |
  vec2 dir = uv - 0.5;
  float r = length(dir);
  vec3 rgb = vec3(
    sample(uv + dir * r * 0.012).r,
    sample(uv).g,
    sample(uv - dir * r * 0.012).b
  );
  Real lenses bias the red toward the edge - tune signs accordingly.
raster: not appropriate
```

## Reactive behaviors

**Light**: aberration peaks at content high-contrast edges

**Highlight**: pointer position can simulate "focal point" (zero CA at pointer)

**Depth**: stronger at edges = depth cue

**Parallax**: scroll velocity doesn't move CA (it's optical, not motion)

## Common implementation mistakes (avoid these)

- uniform CA across the frame (real lens CA is radial)
- very large displacement (becomes glitch, not optics - see rgb-channel-split for that)
- applied to text without limit (illegibility)

## Examples in the wild

- Anamorphic lens cinematography
- high-quality digital camera RAW files
- subtle film-emulation effects

## References

- https://en.wikipedia.org/wiki/Chromatic_aberration

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cinematic`
- `recipe-bento-marketing`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
