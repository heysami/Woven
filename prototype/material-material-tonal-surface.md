# Material 3 Tonal Surface (dynamic-color elevation) (material)

**Tag:** material-material-tonal-surface  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: material-tonal-surface
  name: Material 3 Tonal Surface (dynamic-color elevation)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes via subtle tint shift on elevation
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      :root {
        --primary: oklch(58% 0.15 268);
        --surface: oklch(98% 0.005 268);
      }
      .elev-1 { background: color-mix(in oklch, var(--primary) 5%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 1px 3px 1px rgb(0 0 0 / 0.15); }
      .elev-2 { background: color-mix(in oklch, var(--primary) 8%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 2px 6px 2px rgb(0 0 0 / 0.15); }
      .elev-3 { background: color-mix(in oklch, var(--primary) 11%, var(--surface)); box-shadow: 0 4px 8px 3px rgb(0 0 0 / 0.15), 0 1px 3px rgb(0 0 0 / 0.3); }
    raster: none
  reactiveBehaviors:
    light: state layers (hover 8% / focus 12% / press 16% on-color overlay)
    highlight: ripple from touch point on press, 0.4s expansion
    depth: containment morph — FAB expands into bottom sheet via shared bounds
    parallax: none
  pairsWith:
    prototypeStyles: [style-material-m3, recipe-material-3, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
  killsTheIllusion:
    - applying M3 tokens without surface-tint ladder (flat white-on-white)
    - mixing Material Symbols Outlined with Rounded
    - seed colour not propagated into containers and on-colors
  examples:
    - Android 14/15 system UI
    - Google Calendar / Keep / Tasks 2023+
    - Pixel Launcher dynamic theming
  references:
    - https://m3.material.io/blog/tone-based-surface-color-m3
```

### 3.6 Pixel / retro digital family

```yaml
```

## Common implementation mistakes (avoid these)

- applying M3 tokens without surface-tint ladder (flat white-on-white)
- mixing Material Symbols Outlined with Rounded
- seed colour not propagated into containers and on-colors

## Pairs with (prototype slugs)

- `style-material-m3`
- `recipe-material-3`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 749–790 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
