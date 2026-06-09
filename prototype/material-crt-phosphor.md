# CRT Phosphor (raster scan with subpixel RGB) (material)


**Tag:** material-crt-phosphor
  ·  **Family:** digital  ·  **Category:** digital-effect  ·  **Surface:** glossy  ·  **Transparency:** opaque

A glossy surface that reacts to light: yes — phosphor glow blooms with viewing angle.

**Examples in the wild**

- libretro/glsl-shaders CRT-Royale
- Vayce CRT Screen Effect

**Common implementation mistakes (avoid these)**

- scanlines on already-pixel content (double pattern fights)
- scanlines without subpixel RGB
- flat scanline opacity (real phosphor varies)

**Pairs with** (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `style-pixel-bitmap`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of the material -->

---

_Full entry in [docs/research/material-library.md](../docs/research/material-library.md)._
