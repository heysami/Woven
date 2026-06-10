---
materialId: marble
name: Marble (veined stone)
family: analog
category: stone
surfaceFinish: glossy (polished) or matte (honed)
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-vaporwave (the marble bust!), recipe-editorial-magazine]
---

# Marble (veined stone)

A glossy (polished) or matte (honed) surface that reacts to light: yes — soft sheen.

## Physical behavior

**Surface finish**: glossy (polished) or matte (honed)

**Transparency**: opaque

**Reacts to light**: yes — soft sheen

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.2), transparent 35%),
    linear-gradient(135deg, oklch(96% 0.005 0) 0%, oklch(85% 0.008 250) 100%);
  filter: url(#vein);
svg: |
  <filter id="vein">
    <feTurbulence type="turbulence" baseFrequency="0.012" numOctaves="3"/>
    <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.45  0 0 0 0.6 -0.4"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
raster: photographed marble is the highest fidelity
```

## Reactive behaviors

**Light**: soft sheen tracks pointer

**Highlight**: yes

**Depth**: no

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- veins drawn perfectly (real marble is organic chaos)
- matte without sheen (most marble is polished)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`
- `aesthetic-vaporwave (the marble bust!)`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
