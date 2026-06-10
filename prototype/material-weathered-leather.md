# Weathered Leather (vintage, distressed) (material)

**Tag:** material-weathered-leather  ·  **Family:** analog  ·  **Category:** leather · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: weathered-leather
  name: Weathered Leather (vintage, distressed)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: minor specular at non-worn areas
    deforms: yes — creases at handle points
    age: acquired patina (cracks, discoloration)
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 25% 75%, rgba(0,0,0,0.3), transparent 35%),
        radial-gradient(ellipse at 75% 25%, rgba(255,255,255,0.06), transparent 35%),
        oklch(30% 0.06 35);
    svg: |
      crack pattern via <feTurbulence baseFrequency="0.08"/> threshold-passed
    raster: photograph of real weathered leather is essential
  reactiveBehaviors:
    light: minor specular at un-worn patches
    highlight: low intensity, asymmetric
    depth: subtle crease deepening on hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-cottagegoth, aesthetic-corporate-grunge]
  killsTheIllusion:
    - uniform wear (real wear lives at touch-points)
    - no creases at all
    - bright fresh leather colour
```

### 4.6 Film / video / capture family

```yaml
```

## Common implementation mistakes (avoid these)

- uniform wear (real wear lives at touch-points)
- no creases at all
- bright fresh leather colour

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-steampunk`
- `aesthetic-dieselpunk`
- `aesthetic-cottagegoth`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2550–2584 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
