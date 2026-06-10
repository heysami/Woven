# Frosted Glass (canonical glassmorphism) (material)

**Tag:** material-frosted-glass  ·  **Family:** digital  ·  **Category:** glass · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: frosted-glass
  name: Frosted Glass (canonical glassmorphism)
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — top-edge specular highlight, tinted by substrate beneath
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background: rgba(255,255,255,0.18);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 0.5px solid rgba(255,255,255,0.35);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.5),
        inset 0 0 0 1px rgba(255,255,255,0.18),
        0 8px 32px rgba(0,0,0,0.18),
        0 2px 8px rgba(0,0,0,0.08);
      border-radius: 22px;
    svg: optional fffuel-style noise overlay at 3–5% opacity to mask blur banding
    webgl: not needed for this tier
    raster: SUBSTRATE is mandatory — saturated photo or mesh-gradient beneath
    video: looping iridescent-substrate underlay is one variant
  reactiveBehaviors:
    light: substrate visible through the panel changes if the substrate moves (scroll parallax); panel itself is otherwise static
    highlight: top-edge inset highlight is fixed; on tilt the substrate shifts but the highlight does not
    depth: hover lift 2px; press scales 0.99
    parallax: substrate moves slower than glass card on scroll
  pairsWith:
    prototypeStyles: [style-glassmorphism, style-liquid-glass, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-positivity-kawaii]
  killsTheIllusion:
    - blur on flat #fff page (refracts nothing → fogged plastic)
    - missing 1px inset white top-edge highlight (reads as sticker, not lens)
    - body text directly on glass with no vibrancy chip backing
    - 4–6px SaaS radius instead of 16–22px continuous corner
    - stacking glass-on-glass-on-glass (compounds to mush)
    - no `saturate()` boost — blur drains chroma without it, reads grey gauze
  examples:
    - macOS Big Sur sidebars
    - iOS Control Center
    - visionOS materials
    - Microsoft Fluent Acrylic
  references:
    - https://caniuse.com/css-backdrop-filter
    - https://developer.apple.com/videos/play/wwdc2025/219/
```

## Common implementation mistakes (avoid these)

- blur on flat #fff page (refracts nothing → fogged plastic)
- missing 1px inset white top-edge highlight (reads as sticker, not lens)
- body text directly on glass with no vibrancy chip backing

## Pairs with (prototype slugs)

- `style-glassmorphism`
- `style-liquid-glass`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-frutiger-chromecore`
- `aesthetic-y2k-futurism`
- `aesthetic-vaporwave`
- `aesthetic-positivity-kawaii`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 71–119 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
