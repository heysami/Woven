# NES ROM Corruption (palette-flipped sprites, garbled tile data) (material)

**Tag:** material-nes-rom-corruption  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: nes-rom-corruption
  name: NES ROM Corruption (palette-flipped sprites, garbled tile data)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes (tiles re-index, palette swaps)
    age: ageless (feels 1986-Famicom era)
  implementationStrategies:
    css: |
      image-rendering: pixelated;
      filter: hue-rotate(var(--rom-shift, 0deg)) saturate(2);
    webgl: |
      shader samples a palette LUT texture; randomize indices for sprite tiles
      at random intervals; for the deepest corruption, swap tile-index lookup
      tables mid-frame.
    raster: pre-rendered glitched sprite sheets at native NES resolution (256×240)
  reactiveBehaviors:
    light: palette swap is the only response (binary)
    highlight: pointer-press flips a tile region's palette
    depth: stepped only (sprite-sheet frame swap)
    parallax: stepped (8-pixel scroll register only)
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-arcade, aesthetic-cyberpunk, aesthetic-acid-graphics]
  killsTheIllusion:
    - sub-pixel scroll on glitched tiles (NES had no sub-pixel)
    - more than 4 colors in a single sprite (NES sprite limit was 3+transparent)
    - non-8×8 tile alignment
  examples:
    - corrupted Pokemon Red R/B (MissingNo aesthetic)
    - retro homebrew NES demos
    - lospec palette work
  references:
    - https://www.nesdev.org/wiki/PPU_palettes
```

## Common implementation mistakes (avoid these)

- sub-pixel scroll on glitched tiles (NES had no sub-pixel)
- more than 4 colors in a single sprite (NES sprite limit was 3+transparent)
- non-8×8 tile alignment

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-arcade`
- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1146–1182 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
