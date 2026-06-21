---
materialId: holographic-foil
name: Holographic Foil (Pokemon card / Apple Pay Cash)
family: digital
category: iridescent
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [style-holographic, aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, aesthetic-vaporwave, style-liquid-glass]
images:
  - src: material-holographic-foil.png
    reason: Material fidelity sample.
---

# Holographic Foil (Pokemon card / Apple Pay Cash)

A glossy surface that reacts to light: yes - full spectrum hue shift on angle.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes - full spectrum hue shift on angle

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    conic-gradient(
      in oklch from 45deg,
      oklch(85% 0.10 200),
      oklch(82% 0.11 310),
      oklch(88% 0.09 60),
      oklch(84% 0.10 155),
      oklch(85% 0.10 200)
    );
  filter: hue-rotate(calc(var(--px,0) * 25deg));
  transform: rotateX(calc(var(--py,0) * 8deg)) rotateY(calc(var(--px,0) * 8deg));
  mix-blend-mode: color-dodge;  /* atop a dark substrate */
svg: |
  grain noise overlay at 4% to break the conic bands
webgl: |
  fragment shader: sample HDR environment cubemap, modulate by surface
  angle; gives true Pokemon-card foil. ~5ms/frame budget on M-series.
raster: oil-on-water iridescent photographs for the highest fidelity
```

## Reactive behaviors

**Light**: hue rotates ±25deg on pointer X; rotateY/rotateX on pointer

**Highlight**: yes (the conic gradient IS the highlight)

**Depth**: hover scale 1.02; press 0.98

**Parallax**: gyro-driven on mobile via DeviceOrientationEvent

## Common implementation mistakes (avoid these)

- conic-gradient(#f0f, #0ff, #ff0, #f0f) in sRGB - muddy brown bands at cyan→magenta
- autoplay 2s infinite hue-rotate spin (epileptic + tells "AI generated")
- iridescence on body type or form inputs
- light substrate (kills the specular - iridescence needs dark backing)
- full 360° hue traversal (real iridescence travels 40-50° arc)

## Examples in the wild

- Apple Pay Cash
- Apple TV+ 2025 rebrand
- poke-holo.simey.me reverse-engineered Pokemon
- Boiler Room 2024 identity

## References

- https://poke-holo.simey.me/
- https://github.com/simeydotme/pokemon-cards-css

## Pairs with (prototype slugs)

- `style-holographic`
- `aesthetic-frutiger-chromecore`
- `aesthetic-y2k-futurism`
- `aesthetic-vaporwave`
- `style-liquid-glass`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
