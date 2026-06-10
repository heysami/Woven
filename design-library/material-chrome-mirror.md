---
materialId: chrome-mirror
name: Chrome Mirror (Y2K chromecore / cyber-sigil)
family: digital
category: metal
surfaceFinish: metallic
transparency: opaque
pairsPrototypes: [aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, style-holographic, aesthetic-cyberpunk, aesthetic-urbling]
images:
  - src: material-chrome-mirror.png
    reason: Material fidelity sample.
---

# Chrome Mirror (Y2K chromecore / cyber-sigil)

A metallic surface that reacts to light: yes — environment reflection, hue shift with angle.

## Physical behavior

**Surface finish**: metallic

**Transparency**: opaque

**Reacts to light**: yes — environment reflection, hue shift with angle

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: horizon line shifts position with pointer; chrome inverts top↔bottom

**Highlight**: |

## Common implementation mistakes (avoid these)

- smooth grey gradient (chrome is BANDED — sky-on-top, ground-on-bottom)
- no inset highlight at the seam between bands
- chrome on a colourful chaotic page (the reflection has to be coherent)

## Examples in the wild

- Y2K Gucci silver
- Boiler Room 2024 identity
- Daniel Arsham Drift jewelry mark

## References

- https://www.happy-digital.com/freebies/tip_chrome.html

## Pairs with (prototype slugs)

- `aesthetic-frutiger-chromecore`
- `aesthetic-y2k-futurism`
- `style-holographic`
- `aesthetic-cyberpunk`
- `aesthetic-urbling`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
