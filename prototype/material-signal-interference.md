# Signal Interference (hum bars, sync errors, vertical hold drift) (material)


**Tag:** material-signal-interference
  ·  **Family:** digital  ·  **Category:** digital-effect  ·  **Surface:** glossy  ·  **Transparency:** opaque

A glossy surface that reacts to light: yes — interference modulates with content luminance and deforms: yes (frame skew, scroll, sync loss).

**Examples in the wild**

- 1980s broadcast TV
- VHS recorded off-air
- synthwave music video establishing shots

**Common implementation mistakes (avoid these)**

- regular sine-wave (real interference is stochastic)
- hum bars at the same position every frame (real ones drift)
- applying with linear blend (use mix-blend-mode: screen or color-dodge)

**Pairs with** (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-cyberpunk`
- `recipe-terminal-on-web`
- `style-dense-mono-dark`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of the material -->

---

_Full entry in [docs/research/material-library.md](../docs/research/material-library.md)._
