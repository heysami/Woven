# Gold Leaf (rich warm metal) (material)

**Tag:** material-gold-leaf  ·  **Family:** digital  ·  **Category:** metal · metallic

A metallic digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: gold-leaf
  name: Gold Leaf (rich warm metal)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: metallic
    transparency: opaque
    reactsToLight: yes — warm specular, slight wrinkle
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg,
          oklch(95% 0.10 90) 0%,
          oklch(70% 0.14 75) 50%,
          oklch(50% 0.12 60) 100%
        );
      box-shadow:
        inset 0 1px 0 rgba(255,250,210,0.9),
        inset 0 -1px 0 rgba(80,40,0,0.5),
        0 2px 6px rgba(80,40,0,0.3);
    svg: |
      crinkle texture via <feTurbulence> baseFrequency="0.04" numOctaves="3"
      blended at mix-blend-mode: overlay, opacity 0.25
    raster: scanned gold-leaf texture at 1024px tile, multiplied
  reactiveBehaviors:
    light: warm highlight tracks pointer; on tilt, deep amber shadows emerge
    highlight: yes via pointer
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-urbling, style-holographic]
  killsTheIllusion:
    - cool-white gold (gold is warm — pull hue toward 80–90 in OKLCH)
    - smooth perfect surface (real gold leaf wrinkles)
  examples:
    - religious iconography
    - Nike Mag chrome
    - DeFi-cosmic certificate cards
```

## Common implementation mistakes (avoid these)

- cool-white gold (gold is warm — pull hue toward 80–90 in OKLCH)
- smooth perfect surface (real gold leaf wrinkles)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`
- `aesthetic-urbling`
- `style-holographic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 526–566 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
