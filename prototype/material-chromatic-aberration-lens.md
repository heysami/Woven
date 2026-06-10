# Lens Chromatic Aberration (radial RGB split toward corners) (material)

**Tag:** material-chromatic-aberration-lens  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: chromatic-aberration-lens
  name: Lens Chromatic Aberration (radial RGB split toward corners)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — CA peaks at high-contrast luminance transitions
    deforms: no (channels shift radially)
    age: ageless
  implementationStrategies:
    css: |
      /* limited — CSS can fake at edges with two filter layers */
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
      Real lenses bias the red toward the edge — tune signs accordingly.
    raster: not appropriate
  reactiveBehaviors:
    light: aberration peaks at content high-contrast edges
    highlight: pointer position can simulate "focal point" (zero CA at pointer)
    depth: stronger at edges = depth cue
    parallax: scroll velocity doesn't move CA (it's optical, not motion)
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cinematic, recipe-bento-marketing, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, recipe-restrained-ai-marketing]
  killsTheIllusion:
    - uniform CA across the frame (real lens CA is radial)
    - very large displacement (becomes glitch, not optics — see rgb-channel-split for that)
    - applied to text without limit (illegibility)
  examples:
    - Anamorphic lens cinematography
    - high-quality digital camera RAW files
    - subtle film-emulation effects
  references:
    - https://en.wikipedia.org/wiki/Chromatic_aberration
```

## Common implementation mistakes (avoid these)

- uniform CA across the frame (real lens CA is radial)
- very large displacement (becomes glitch, not optics — see rgb-channel-split for that)
- applied to text without limit (illegibility)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cinematic`
- `recipe-bento-marketing`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`
- `recipe-restrained-ai-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1183–1227 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
