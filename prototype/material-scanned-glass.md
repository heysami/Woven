# Scanned Glass (digital glass on analog paper substrate) (material)

**Tag:** material-scanned-glass  ·  **Family:** hybrid  ·  **Category:** glass · glossy

A glossy hybrid surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: scanned-glass
  name: Scanned Glass (digital glass on analog paper substrate)
  family: hybrid
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: no
    age: shows wear
  implementationStrategies:
    css: |
      /* Layer 1: paper substrate. Layer 2: glass panel. */
      background:
        url('paper-texture.jpg'),
        rgba(255,255,255,0.18);
      backdrop-filter: blur(20px) saturate(180%);
    svg: paper grain + glass refraction filters stacked
    raster: REQUIRED — paper substrate is the load-bearing element
  reactiveBehaviors:
    light: glass highlight tracks pointer; paper substrate doesn't
    highlight: yes
    depth: hover lift glass slightly above paper
    parallax: paper stays put; glass moves with viewport
  pairsWith:
    prototypeStyles: [aesthetic-cottagegoth, aesthetic-dark-academia, recipe-editorial-magazine]
  killsTheIllusion:
    - both layers at same z (glass must SIT ON paper)
    - no paper grain visible behind glass
  examples:
    - editorial book design (glass insert over endpaper)
    - museum archival labels (modern UI under aged paper)
```

## Common implementation mistakes (avoid these)

- both layers at same z (glass must SIT ON paper)
- no paper grain visible behind glass

## Pairs with (prototype slugs)

- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2986–3018 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
