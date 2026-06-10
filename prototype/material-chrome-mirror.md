# Chrome Mirror (Y2K chromecore / cyber-sigil) (material)

**Tag:** material-chrome-mirror  ·  **Family:** digital  ·  **Category:** metal · metallic

A metallic digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: chrome-mirror
  name: Chrome Mirror (Y2K chromecore / cyber-sigil)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: metallic
    transparency: opaque
    reactsToLight: yes — environment reflection, hue shift with angle
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg,
          #f7f7fa 0%,
          #8a8d96 35%,
          #4e525c 55%,
          #c5c8d2 80%,
          #f7f7fa 100%
        );
      /* Chrome read demands a HORIZON-BANDED gradient — not a smooth one */
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.9),
        inset 0 -1px 0 rgba(0,0,0,0.5),
        0 2px 4px rgba(0,0,0,0.3);
      border-radius: 999px;
    svg: optional `<feSpecularLighting>` for high-fidelity
    webgl: cube-map environment lookup for the highest-fidelity chrome
    raster: captured indoor environment photo (4096×2048 equirectangular)
  reactiveBehaviors:
    light: horizon line shifts position with pointer; chrome inverts top↔bottom
    highlight: |
      element.style.setProperty('--horizon', 30 + e.clientY/window.innerHeight * 40 + '%');
      /* gradient stops snap to --horizon */
    depth: no deformation; metal is hard
    parallax: cube-map rotates on `DeviceOrientationEvent`
  pairsWith:
    prototypeStyles: [aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, style-holographic, aesthetic-cyberpunk, aesthetic-urbling]
  killsTheIllusion:
    - smooth grey gradient (chrome is BANDED — sky-on-top, ground-on-bottom)
    - no inset highlight at the seam between bands
    - chrome on a colourful chaotic page (the reflection has to be coherent)
  examples:
    - Y2K Gucci silver
    - Boiler Room 2024 identity
    - Daniel Arsham Drift jewelry mark
  references:
    - https://www.happy-digital.com/freebies/tip_chrome.html
```

## Common implementation mistakes (avoid these)

- smooth grey gradient (chrome is BANDED — sky-on-top, ground-on-bottom)
- no inset highlight at the seam between bands
- chrome on a colourful chaotic page (the reflection has to be coherent)

## Pairs with (prototype slugs)

- `aesthetic-frutiger-chromecore`
- `aesthetic-y2k-futurism`
- `style-holographic`
- `aesthetic-cyberpunk`
- `aesthetic-urbling`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 431–479 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
