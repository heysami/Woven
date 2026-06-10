# Thin Glass Chip (iOS-style toggle, Control Center pill) (material)

**Tag:** material-thin-glass-chip  ·  **Family:** digital  ·  **Category:** glass · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: thin-glass-chip
  name: Thin Glass Chip (iOS-style toggle, Control Center pill)
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — but lighter than full glass; substrate shows through more
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      backdrop-filter: blur(12px) saturate(140%);
      background: rgba(255,255,255,0.22);
      border: 0.5px solid rgba(255,255,255,0.4);
      border-radius: 9999px;
      padding: 6px 12px;
    svg: none
    raster: requires saturated substrate
  reactiveBehaviors:
    light: substrate shifts on scroll
    highlight: subtle on hover (background opacity +0.04)
    depth: 1px lift on hover
    parallax: tracks scroll
  pairsWith:
    prototypeStyles: [style-glassmorphism, style-liquid-glass, recipe-ios-system]
  killsTheIllusion:
    - too much blur (the chip becomes invisible)
    - chip on flat solid colour with no substrate
  examples:
    - iOS Control Center toggles
    - Apple Maps mode pills
```

## Common implementation mistakes (avoid these)

- too much blur (the chip becomes invisible)
- chip on flat solid colour with no substrate

## Pairs with (prototype slugs)

- `style-glassmorphism`
- `style-liquid-glass`
- `recipe-ios-system`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 185–217 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
