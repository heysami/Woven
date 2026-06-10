---
materialId: uncoated-paper
name: Uncoated Paper (soft, porous, ink-absorbing)
family: analog
category: paper
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-cottagegoth, style-raster-cutout]
---

# Uncoated Paper (soft, porous, ink-absorbing)

A matte surface and deforms: yes — wrinkles, tears, dog-ears.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: yes — wrinkles, tears, dog-ears

**Age / wear**: shows wear (yellowing, foxing)

## Implementation strategies

```yaml
css: |
  background:
    url('paper-grain-2048.jpg') center/512px,
    oklch(97% 0.012 85);  /* warm white, never #FFF */
  background-blend-mode: multiply;
svg: |
  <filter id="paperGrain">
    <feTurbulence baseFrequency="0.9" numOctaves="2" seed="3"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.06 0"/>
  </filter>
  <!-- 6% noise opacity -->
raster: 2048×2048 scanned uncoated paper (Crane Lettra, Mohawk Superfine)
```

## Reactive behaviors

**Light**: no specular; ambient only

**Highlight**: minor warmth in hover state

**Depth**: corner curl on hover (CSS mask gradient)

**Parallax**: very subtle on scroll

## Common implementation mistakes (avoid these)

- perfectly flat #FFF background (uncoated is always warm-tinted)
- high-contrast specular highlight (uncoated has none)
- tile pattern visibly repeating (use masking to break the seam)
- body text at 16px with line-height 1.4 (editorial paper wants 18–19px / 1.55)

## Examples in the wild

- The New Yorker print
- Aeon longform
- book covers from Penguin Modern Classics

## References

- https://www.jampaper.com/blog/paper-textures-and-finishes-2/

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-cottagecore`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `style-raster-cutout`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
