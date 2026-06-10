# Smooth Leather (full-grain, polished) (material)

**Tag:** material-smooth-leather  ·  **Family:** analog  ·  **Category:** leather · semi-gloss

A semi-gloss analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: smooth-leather
  name: Smooth Leather (full-grain, polished)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — soft specular sweep
    deforms: yes
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        linear-gradient(115deg, rgba(255,255,255,0.10) 0%, transparent 35%),
        oklch(40% 0.08 40);
    svg: subtle <feTurbulence> at 0.4 baseFrequency for grain
    raster: scanned smooth leather
  reactiveBehaviors:
    light: soft specular tracks pointer at low intensity
    highlight: yes
    depth: hover lift; press inset
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism, aesthetic-dark-academia]
  killsTheIllusion:
    - matte uniform (smooth leather always has subtle sheen)
    - no grain variation
  examples:
    - iBooks library shelf
    - high-end notebook covers
```

## Common implementation mistakes (avoid these)

- matte uniform (smooth leather always has subtle sheen)
- no grain variation

## Pairs with (prototype slugs)

- `style-skeuomorphism`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2519–2549 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
