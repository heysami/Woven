# Kraft Paper (brown unbleached cardstock) (material)

**Tag:** material-kraft-paper  ·  **Family:** analog  ·  **Category:** paper · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: kraft-paper
  name: Kraft Paper (brown unbleached cardstock)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — wrinkles, tears
    age: shows wear (creases at fold)
  implementationStrategies:
    css: |
      background:
        url('kraft-fibre-1024.jpg') center/384px,
        oklch(60% 0.06 60);  /* warm brown */
      background-blend-mode: multiply;
    raster: scan of real brown kraft; visible long fibers
  reactiveBehaviors:
    light: no specular
    highlight: minimal
    depth: yes — paper can curl
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-goblincore, recipe-newspaper-of-record]
  killsTheIllusion:
    - kraft as a solid brown swatch (it needs visible fibers)
    - clean rectangular crop (kraft tears on edges)
  examples:
    - Aesop product wrap
    - Trader Joe's bag aesthetic
    - small-batch coffee bag fronts
```

## Common implementation mistakes (avoid these)

- kraft as a solid brown swatch (it needs visible fibers)
- clean rectangular crop (kraft tears on edges)

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-goblincore`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1815–1846 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
