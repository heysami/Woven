# Soft UI / Neumorphic Foam (material)

**Tag:** material-soft-ui-foam  ·  **Family:** digital  ·  **Category:** clay · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: soft-ui-foam
  name: Soft UI / Neumorphic Foam
  family: digital
  category: clay
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — dual highlight + shadow
    deforms: yes (raised ↔ pressed)
    age: ageless
  implementationStrategies:
    css: |
      /* Container background MUST equal page background */
      background: #E0E5EC;
      border-radius: 28px;
      box-shadow:
        9px 9px 16px #A3B1C6,
        -9px -9px 16px #FFFFFF;
      /* Pressed variant */
      .pressed {
        box-shadow:
          inset 6px 6px 12px #A3B1C6,
          inset -6px -6px 12px #FFFFFF;
      }
    raster: none
  reactiveBehaviors:
    light: single committed light direction (top-left); never deviates
    highlight: shadow blur 16 → 20 on hover
    depth: 180ms ease-out swap to inset on press
    parallax: none
  pairsWith:
    prototypeStyles: [style-neumorphism, aesthetic-frutiger-tranquil-serenity, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
  killsTheIllusion:
    - pure #FFF or #000 background (kills one shadow)
    - symmetric shadows with no implied light source
    - per-component shadow tuning (light jumps around)
    - sharp <12px radii (breaks soft-plastic read)
    - text or icons extruded (only containers extrude)
  examples:
    - Alexander Plyuto Skeuomorph Bank 2019
    - neumorphism.io
  references:
    - https://neumorphism.io/
```

## Common implementation mistakes (avoid these)

- pure #FFF or #000 background (kills one shadow)
- symmetric shadows with no implied light source
- per-component shadow tuning (light jumps around)

## Pairs with (prototype slugs)

- `style-neumorphism`
- `aesthetic-frutiger-tranquil-serenity`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 351–394 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
