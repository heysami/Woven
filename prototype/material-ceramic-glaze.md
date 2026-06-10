# Ceramic Glaze (high-gloss porcelain finish) (material)

**Tag:** material-ceramic-glaze  ·  **Family:** digital  ·  **Category:** ceramic · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: ceramic-glaze
  name: Ceramic Glaze (high-gloss porcelain finish)
  family: digital
  category: ceramic
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — sharp specular sweep
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.65), transparent 35%),
        linear-gradient(135deg, oklch(75% 0.06 200) 0%, oklch(60% 0.08 200) 100%);
      box-shadow: 0 12px 32px -8px rgba(0,0,0,0.25);
      border-radius: 50%;
    raster: optional photo of real ceramic at 8% multiply
  reactiveBehaviors:
    light: highlight tracks pointer at 0.5× pointer speed
    highlight: --hl-x/--hl-y custom props update specular position
    depth: minimal — glaze is hard
    parallax: none
  pairsWith:
    prototypeStyles: [style-skeuomorphism (porcelain mascot), aesthetic-cottagecore (enamelware)]
  killsTheIllusion:
    - matte fill (ceramic without glaze isn't ceramic — it's terracotta)
    - off-centre highlight stuck at fixed position
  examples:
    - Apple memoji ceramic mode
    - 3D-icon stocks (Iconscout)
```

### 3.3 Metal family

```yaml
```

## Common implementation mistakes (avoid these)

- matte fill (ceramic without glaze isn't ceramic — it's terracotta)
- off-centre highlight stuck at fixed position

## Pairs with (prototype slugs)

- `style-skeuomorphism (porcelain mascot)`
- `aesthetic-cottagecore (enamelware)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 395–430 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
