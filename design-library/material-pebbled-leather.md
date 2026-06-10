---
materialId: pebbled-leather
name: Pebbled Leather (luxury goods finish)
family: analog
category: leather
surfaceFinish: semi-gloss
transparency: opaque
pairsPrototypes: [style-skeuomorphism (leather wallet), aesthetic-dark-academia, aesthetic-defi-cosmic]
---

# Pebbled Leather (luxury goods finish)

A semi-gloss surface that reacts to light: yes — per-pebble micro-highlight and deforms: yes — bends.

## Physical behavior

**Surface finish**: semi-gloss

**Transparency**: opaque

**Reacts to light**: yes — per-pebble micro-highlight

**Deforms**: yes — bends

**Age / wear**: acquired patina (shines at touch points)

## Implementation strategies

```yaml
css: |
  background: oklch(35% 0.04 50);
  filter: url(#pebble);
svg: |
  <filter id="pebble">
    <feTurbulence type="fractalNoise" baseFrequency="0.18" numOctaves="3"/>
    <feSpecularLighting surfaceScale="2" specularConstant="0.8" specularExponent="20" lighting-color="#fff">
      <feDistantLight azimuth="225" elevation="45"/>
    </feSpecularLighting>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
raster: scanned pebbled leather is the gold standard
```

## Reactive behaviors

**Light**: per-pebble highlight tracks light direction

**Highlight**: yes via DeviceOrientation/pointer

**Depth**: hover lift; press depresses

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- perfectly uniform pebble pattern (real pebble varies)
- no specular per pebble (luxury leather glints)
- cold colour (leather is warm)

## Examples in the wild

- vintage iCal leather header
- Saffiano luxury wallets
- bookbinding spines

## References

- https://leathera.com/textured-leather

## Pairs with (prototype slugs)

- `style-skeuomorphism (leather wallet)`
- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
