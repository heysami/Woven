# Pixel Bitmap (integer-grid surface) (material)

**Tag:** material-pixel-bitmap  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: pixel-bitmap
  name: Pixel Bitmap (integer-grid surface)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no — instant or stepped state changes only
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: none
    highlight: instant palette swap
    depth: 1-frame state flip
    parallax: stepped only (sprite-sheet steps)
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-snes-jrpg, aesthetic-pixel-game-boy-mono, aesthetic-pc-98]
  killsTheIllusion:
    - antialiased SVG icons next to pixel sprites
    - drop-shadow blur on sprites
    - Press Start 2P at 14px (mush)
    - smooth 250ms fades anywhere
  examples:
    - NES.css
    - Pokemon R/B
    - Lospec palettes
    - PICO-8
```

## Common implementation mistakes (avoid these)

- antialiased SVG icons next to pixel sprites
- drop-shadow blur on sprites
- Press Start 2P at 14px (mush)

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-snes-jrpg`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-pc-98`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 791–829 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
