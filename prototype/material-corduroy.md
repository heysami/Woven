# Corduroy (ribbed pile fabric) (material)

**Tag:** material-corduroy  ·  **Family:** analog  ·  **Category:** fabric · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: corduroy
  name: Corduroy (ribbed pile fabric)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — directional pile reflects per-rib
    deforms: yes
    age: ageless
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(90deg,
          rgba(0,0,0,0.18) 0px,
          transparent 6px,
          rgba(255,255,255,0.06) 8px,
          rgba(0,0,0,0.18) 12px
        ),
        oklch(50% 0.10 60);
    raster: corduroy photograph
  reactiveBehaviors:
    light: rib shadow band shifts with pointer (corduroy's signature)
    highlight: per-rib gradient updates
    depth: minor press
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-coastal-grandmother]
  killsTheIllusion:
    - ribs without highlight asymmetry
    - rib spacing too small (becomes Moiré) or too large (becomes stripes)
```

### 4.5 Leather and skin family

```yaml
```

## Common implementation mistakes (avoid these)

- ribs without highlight asymmetry
- rib spacing too small (becomes Moiré) or too large (becomes stripes)

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-dark-academia`
- `aesthetic-coastal-grandmother`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2442–2477 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
