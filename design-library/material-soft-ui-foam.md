---
materialId: soft-ui-foam
name: Soft UI / Neumorphic Foam
family: digital
category: clay
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-neumorphism, aesthetic-frutiger-tranquil-serenity, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
---

# Soft UI / Neumorphic Foam

A matte surface that reacts to light: yes — dual highlight + shadow and deforms: yes (raised ↔ pressed).

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — dual highlight + shadow

**Deforms**: yes (raised ↔ pressed)

**Age / wear**: ageless

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: single committed light direction (top-left); never deviates

**Highlight**: shadow blur 16 → 20 on hover

**Depth**: 180ms ease-out swap to inset on press

**Parallax**: none

## Common implementation mistakes (avoid these)

- pure #FFF or #000 background (kills one shadow)
- symmetric shadows with no implied light source
- per-component shadow tuning (light jumps around)
- sharp <12px radii (breaks soft-plastic read)
- text or icons extruded (only containers extrude)

## Examples in the wild

- Alexander Plyuto Skeuomorph Bank 2019
- neumorphism.io

## References

- https://neumorphism.io/

## Pairs with (prototype slugs)

- `style-neumorphism`
- `aesthetic-frutiger-tranquil-serenity`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
