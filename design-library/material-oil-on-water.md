---
materialId: oil-on-water
name: Oil-on-Water Iridescence (organic dichroic)
family: digital
category: iridescent
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [style-aurorism, style-holographic, aesthetic-vaporwave, aesthetic-cyberpunk]
---

# Oil-on-Water Iridescence (organic dichroic)

A glossy surface (translucent) that reacts to light: yes — chaotic hue swirls and deforms: yes — surface ripples.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes — chaotic hue swirls

**Deforms**: yes — surface ripples

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(circle at 30% 40%, oklch(75% 0.18 200), transparent 30%),
    radial-gradient(circle at 70% 60%, oklch(75% 0.18 310), transparent 30%),
    radial-gradient(circle at 50% 30%, oklch(75% 0.18 60), transparent 30%),
    oklch(15% 0.02 250);
  filter: blur(20px) saturate(180%);
svg: |
  <feTurbulence baseFrequency="0.008" numOctaves="3"/>
  <feDisplacementMap scale="40"/>
  /* swirls the radial blobs into oil-slick patterns */
webgl: real-time noise + UV distort gives the highest fidelity
raster: stock oil-on-water photograph at substrate
```

## Reactive behaviors

**Light**: distort scale increases on pointer proximity

**Highlight**: tracks pointer

**Depth**: surface ripples on press (canvas ripple shader)

**Parallax**: subtle on scroll

## Common implementation mistakes (avoid these)

- regular gradient blobs without displacement
- sRGB hue mixing (always OKLCH for iridescence)

## Examples in the wild

- Linear visual ID
- Apple TV+ marketing background

## Pairs with (prototype slugs)

- `style-aurorism`
- `style-holographic`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
