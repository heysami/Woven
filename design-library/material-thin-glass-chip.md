---
materialId: thin-glass-chip
name: Thin Glass Chip (iOS-style toggle, Control Center pill)
family: digital
category: glass
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [style-glassmorphism, style-liquid-glass, recipe-ios-system]
images:
  - src: material-thin-glass-chip.png
    reason: Material fidelity sample.
---

# Thin Glass Chip (iOS-style toggle, Control Center pill)

A glossy surface (translucent) that reacts to light: yes - but lighter than full glass; substrate shows through more.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes - but lighter than full glass; substrate shows through more

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  backdrop-filter: blur(12px) saturate(140%);
  background: rgba(255,255,255,0.22);
  border: 0.5px solid rgba(255,255,255,0.4);
  border-radius: 9999px;
  padding: 6px 12px;
svg: none
raster: requires saturated substrate
```

## Reactive behaviors

**Light**: substrate shifts on scroll

**Highlight**: subtle on hover (background opacity +0.04)

**Depth**: 1px lift on hover

**Parallax**: tracks scroll

## Common implementation mistakes (avoid these)

- too much blur (the chip becomes invisible)
- chip on flat solid colour with no substrate

## Examples in the wild

- iOS Control Center toggles
- Apple Maps mode pills

## Pairs with (prototype slugs)

- `style-glassmorphism`
- `style-liquid-glass`
- `recipe-ios-system`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
