---
materialId: liquid-glass
name: Liquid Glass (Apple WWDC25)
family: digital
category: glass
surfaceFinish: glossy
transparency: transparent
pairsPrototypes: [style-liquid-glass, style-glassmorphism, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-holographic, aesthetic-y2k-futurism]
images:
  - src: material-liquid-glass.png
    reason: Material fidelity sample.
---

# Liquid Glass (Apple WWDC25)

A glossy surface (transparent) that reacts to light: yes - specular highlight tracks tilt/pointer; chromatic edge and deforms: minor on press.

## Physical behavior

**Surface finish**: glossy

**Transparency**: transparent

**Reacts to light**: yes - specular highlight tracks tilt/pointer; chromatic edge

**Deforms**: minor on press

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  backdrop-filter: blur(20px) saturate(180%) brightness(108%);
  background: rgba(255,255,255,0.12);
  border: 0.5px solid rgba(255,255,255,0.30);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.75),
    inset 0 -1px 0 rgba(255,255,255,0.10),
    0 1px 2px rgba(0,0,0,0.08),
    0 8px 24px -12px rgba(0,0,0,0.18);
  border-radius: 9999px;   /* pills for nav; 22px concentric for cards */
svg: |
  <filter id="liquidRefract">
    <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="2"/>
    <feDisplacementMap in="SourceGraphic" scale="20"/>
    <feGaussianBlur stdDeviation="1"/>
  </filter>
  /* Apply to chrome shapes ONLY - text becomes illegible above scale=20 */
webgl: |
  Real-time variant: sample the page-behind-canvas as a render-target, do
  fragment-shader refraction (UV offset by gradient of pressed region) at
  30fps. WebGL2 + drawingBufferStorage. ~3ms/frame budget.
raster: substrate required (photo / map / multi-stop gradient)
video: video underlay works (live wallpapers)
```

## Reactive behaviors

**Light**: |

## Common implementation mistakes (avoid these)

- displacement map applied to text (illegible)
- displacement scale > 30 (text swims even on chrome)
- glass nested inside glass (HIG explicitly forbids it)
- brand colour baked into the fill instead of inherited from content
- conic-gradient rainbow rotation on the rim (TikTok-glass tell)
- autoplay shine sweeps

## Examples in the wild

- iOS 26 system
- Apple Music 2025
- visionOS Glass Materials
- Halide camera app

## References

- https://developer.apple.com/videos/play/wwdc2025/219/
- https://en.wikipedia.org/wiki/Liquid_Glass

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-holographic`
- `aesthetic-y2k-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
