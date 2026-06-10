# Silk (lustrous fabric) (material)

**Tag:** material-silk  ·  **Family:** analog  ·  **Category:** fabric · semi-gloss

A semi-gloss analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: silk
  name: Silk (lustrous fabric)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — anisotropic lustre
    deforms: yes — flowing drape
    age: shows wear (fray, water spots)
  implementationStrategies:
    css: |
      background:
        linear-gradient(135deg,
          rgba(255,255,255,0.3) 0%,
          transparent 30%,
          rgba(255,255,255,0.2) 60%,
          transparent 100%
        ),
        oklch(75% 0.12 350);
    raster: silk photograph
  reactiveBehaviors:
    light: lustre band shifts with pointer angle
    highlight: yes — narrow band perpendicular to fibre direction
    depth: drape via scroll-driven skewY
    parallax: yes — gentle
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-coastal-grandmother, aesthetic-defi-cosmic]
  killsTheIllusion:
    - flat fabric (silk is always shifting in light)
    - no drape (silk hangs)
```

## Common implementation mistakes (avoid these)

- flat fabric (silk is always shifting in light)
- no drape (silk hangs)

## Pairs with (prototype slugs)

- `aesthetic-y2k-futurism`
- `aesthetic-vaporwave`
- `aesthetic-coastal-grandmother`
- `aesthetic-defi-cosmic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2379–2410 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
