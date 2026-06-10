---
materialId: watercolor-wash
name: Watercolor Wash (wet-on-wet, granulation)
family: analog
category: wash
surfaceFinish: matte
transparency: translucent (multiple washes)
pairsPrototypes: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore, style-doodle]
images:
  - src: material-watercolor-wash.png
    reason: Material fidelity sample.
---

# Watercolor Wash (wet-on-wet, granulation)

A matte surface (translucent (multiple washes)).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent (multiple washes)

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  mix-blend-mode: multiply;
  filter: url(#watercolor);
svg: |
  <filter id="watercolor">
    <feTurbulence type="turbulence" baseFrequency="0.01 0.05" numOctaves="2"/>
    <feDisplacementMap in="SourceGraphic" scale="8"/>
    <feGaussianBlur stdDeviation="0.4"/>
  </filter>
  <!-- Higher numOctaves for granulation; scale ≥10 starts shifting too much -->
raster: scanned real watercolor wash as substrate
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no (paper underneath has depth)

**Parallax**: yes — washes layer at different scroll rates

## Common implementation mistakes (avoid these)

- hard edges (watercolor bleeds — edges must be soft)
- perfectly even wash (real watercolor pools at edges)
- no paper substrate visible through the wash

## Examples in the wild

- Beatrix Potter botanical plates
- children's book illustration
- botanical print apothecary brands

## References

- https://codepen.io/origan/pen/YOGpjp
- https://andyjakubowski.com/tutorial/ink-bleed-effect-with-svg-filters

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-fairycore`
- `style-doodle`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
