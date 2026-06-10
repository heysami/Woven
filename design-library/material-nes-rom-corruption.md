---
materialId: nes-rom-corruption
name: NES ROM Corruption (palette-flipped sprites, garbled tile data)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-arcade, aesthetic-cyberpunk, aesthetic-acid-graphics]
---

# NES ROM Corruption (palette-flipped sprites, garbled tile data)

A matte surface and deforms: yes (tiles re-index, palette swaps).

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes (tiles re-index, palette swaps)

**Age / wear**: ageless (feels 1986-Famicom era)

## Implementation strategies

```yaml
css: |
  image-rendering: pixelated;
  filter: hue-rotate(var(--rom-shift, 0deg)) saturate(2);
webgl: |
  shader samples a palette LUT texture; randomize indices for sprite tiles
  at random intervals; for the deepest corruption, swap tile-index lookup
  tables mid-frame.
raster: pre-rendered glitched sprite sheets at native NES resolution (256×240)
```

## Reactive behaviors

**Light**: palette swap is the only response (binary)

**Highlight**: pointer-press flips a tile region's palette

**Depth**: stepped only (sprite-sheet frame swap)

**Parallax**: stepped (8-pixel scroll register only)

## Common implementation mistakes (avoid these)

- sub-pixel scroll on glitched tiles (NES had no sub-pixel)
- more than 4 colors in a single sprite (NES sprite limit was 3+transparent)
- non-8×8 tile alignment

## Examples in the wild

- corrupted Pokemon Red R/B (MissingNo aesthetic)
- retro homebrew NES demos
- lospec palette work

## References

- https://www.nesdev.org/wiki/PPU_palettes

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-arcade`
- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
