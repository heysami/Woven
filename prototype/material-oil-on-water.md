# Oil-on-Water Iridescence (organic dichroic) (material)

**Tag:** material-oil-on-water  ·  **Family:** digital  ·  **Category:** iridescent · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: oil-on-water
  name: Oil-on-Water Iridescence (organic dichroic)
  family: digital
  category: iridescent
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — chaotic hue swirls
    deforms: yes — surface ripples
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at 30% 40%, oklch(75% 0.18 200), transparent 30%),
        radial-gradient(circle at 70% 60%, oklch(75% 0.18 310), transparent 30%),
        radial-gradient(circle at 50% 30%, oklch(75% 0.18 60), transparent 30%),
        oklch(15% 0.02 250);
      filter: blur(20px) saturate(180%);
    svg: |
      <feTurbulence baseFrequency="0.008" numOctaves="3"/>
      <feDisplacementMap scale="40"/>
      /* swirls the radial blobs into oil-slick patterns */
    webgl: real-time noise + UV distort gives the highest fidelity
    raster: stock oil-on-water photograph at substrate
  reactiveBehaviors:
    light: distort scale increases on pointer proximity
    highlight: tracks pointer
    depth: surface ripples on press (canvas ripple shader)
    parallax: subtle on scroll
  pairsWith:
    prototypeStyles: [style-aurorism, style-holographic, aesthetic-vaporwave, aesthetic-cyberpunk]
  killsTheIllusion:
    - regular gradient blobs without displacement
    - sRGB hue mixing (always OKLCH for iridescence)
  examples:
    - Linear visual ID
    - Apple TV+ marketing background
```

### 3.5 Aurora and gradient family

```yaml
```

## Common implementation mistakes (avoid these)

- regular gradient blobs without displacement
- sRGB hue mixing (always OKLCH for iridescence)

## Pairs with (prototype slugs)

- `style-aurorism`
- `style-holographic`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 656–697 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
