---
materialId: pixel-bitmap
name: Pixel Bitmap (integer-grid surface)
family: digital
category: digital-effect
surfaceFinish: matte
scope: both
fxStack: [pixelate]
transparency: opaque
pairsPrototypes: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-snes-jrpg, aesthetic-pixel-game-boy-mono, aesthetic-pc-98]
images:
  - src: material-pixel-bitmap.png
    reason: Material fidelity sample.
---

# Pixel Bitmap (integer-grid surface)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no - instant or stepped state changes only

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  image-rendering: pixelated;
  -webkit-font-smoothing: none;
  border-radius: 0;
  box-shadow:
    inset 0 0 0 2px var(--ink),
    2px 2px 0 var(--ink),
    4px 4px 0 var(--shade);
  transition: none;
raster: pixel-perfect bitmap at exact native resolution
```

## Reactive behaviors

**Light**: none

**Highlight**: instant palette swap

**Depth**: 1-frame state flip

**Parallax**: stepped only (sprite-sheet steps)

## Common implementation mistakes (avoid these)

- antialiased SVG icons next to pixel sprites
- drop-shadow blur on sprites
- Press Start 2P at 14px (mush)
- smooth 250ms fades anywhere

## Examples in the wild

- NES.css
- Pokemon R/B
- Lospec palettes
- PICO-8

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-snes-jrpg`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-pc-98`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
