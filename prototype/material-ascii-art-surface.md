# ASCII Art Surface (text-as-pixel) (material)

**Tag:** material-ascii-art-surface  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: ascii-art-surface
  name: ASCII Art Surface (text-as-pixel)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      font-family: ui-monospace, 'IBM Plex Mono';
      line-height: 1;
      letter-spacing: 0;
      white-space: pre;
    webgl: |
      Codrops "Efecto" — quantize image luminance to an ASCII charset, render
      to a font-grid canvas. Charset density carries luminance.
    raster: pre-rendered ASCII PNG for static content
  reactiveBehaviors:
    light: pointer can resample the ASCII density
    highlight: cursor-position changes character density
    depth: none
    parallax: stepped
  pairsWith:
    prototypeStyles: [style-terminal-mono, recipe-terminal-on-web, aesthetic-web-brutalism]
  killsTheIllusion:
    - proportional font (must be monospace)
    - line-height > 1
  examples:
    - tympanus.net Codrops Efecto
    - figlet headers
  references:
    - https://tympanus.net/codrops/2026/01/04/efecto-building-real-time-ascii-and-dithering-effects-with-webgl-shaders/
```

### 3.7 Glitch / distortion / vector-line family

Digital materials whose "physical" behaviour is the texture of the medium itself — codec failure, signal interference, lens optics, plotter pen on paper, schematic engraving. These are NOT analog (they're born digital or are simulated digitally), and they're not UI-surface materials (glass / clay) — they're the texture of digital media as material.

```yaml
```

## Common implementation mistakes (avoid these)

- proportional font (must be monospace)
- line-height > 1

## Pairs with (prototype slugs)

- `style-terminal-mono`
- `recipe-terminal-on-web`
- `aesthetic-web-brutalism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 923–964 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
