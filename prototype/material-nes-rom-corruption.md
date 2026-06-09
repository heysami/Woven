# NES ROM Corruption (palette-flipped sprites, garbled tile data) (material)


**Tag:** material-nes-rom-corruption
  ·  **Family:** digital  ·  **Category:** digital-effect  ·  **Surface:** matte  ·  **Transparency:** opaque

A matte surface and deforms: yes (tiles re-index, palette swaps).

**Examples in the wild**

- corrupted Pokemon Red R/B (MissingNo aesthetic)
- retro homebrew NES demos
- lospec palette work

**Common implementation mistakes (avoid these)**

- sub-pixel scroll on glitched tiles (NES had no sub-pixel)
- more than 4 colors in a single sprite (NES sprite limit was 3+transparent)
- non-8×8 tile alignment

**Pairs with** (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-arcade`
- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of the material -->

---

_Full entry in [docs/research/material-library.md](../docs/research/material-library.md)._
