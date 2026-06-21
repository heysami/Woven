---
materialId: material-tonal-surface
name: Material 3 Tonal Surface (dynamic-color elevation)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-material-m3, recipe-material-3, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
images:
  - src: material-material-tonal-surface.png
    reason: Material fidelity sample.
---

# Material 3 Tonal Surface (dynamic-color elevation)

A matte surface that reacts to light: yes via subtle tint shift on elevation.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes via subtle tint shift on elevation

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  :root {
    --primary: oklch(58% 0.15 268);
    --surface: oklch(98% 0.005 268);
  }
  .elev-1 { background: color-mix(in oklch, var(--primary) 5%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 1px 3px 1px rgb(0 0 0 / 0.15); }
  .elev-2 { background: color-mix(in oklch, var(--primary) 8%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 2px 6px 2px rgb(0 0 0 / 0.15); }
  .elev-3 { background: color-mix(in oklch, var(--primary) 11%, var(--surface)); box-shadow: 0 4px 8px 3px rgb(0 0 0 / 0.15), 0 1px 3px rgb(0 0 0 / 0.3); }
raster: none
```

## Reactive behaviors

**Light**: state layers (hover 8% / focus 12% / press 16% on-color overlay)

**Highlight**: ripple from touch point on press, 0.4s expansion

**Depth**: containment morph - FAB expands into bottom sheet via shared bounds

**Parallax**: none

## Common implementation mistakes (avoid these)

- applying M3 tokens without surface-tint ladder (flat white-on-white)
- mixing Material Symbols Outlined with Rounded
- seed colour not propagated into containers and on-colors

## Examples in the wild

- Android 14/15 system UI
- Google Calendar / Keep / Tasks 2023+
- Pixel Launcher dynamic theming

## References

- https://m3.material.io/blog/tone-based-surface-color-m3

## Pairs with (prototype slugs)

- `style-material-m3`
- `recipe-material-3`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
