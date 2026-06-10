---
materialId: wood-grain-walnut
name: Wood Grain (walnut, dark, vertical grain)
family: analog
category: wood
surfaceFinish: semi-gloss (varnished) or matte (raw)
transparency: opaque
pairsPrototypes: [style-skeuomorphism (library-as-wood-shelf), aesthetic-cottagecore, aesthetic-steampunk, aesthetic-dark-academia]
images:
  - src: material-wood-grain-walnut.png
    reason: Material fidelity sample.
---

# Wood Grain (walnut, dark, vertical grain)

A semi-gloss (varnished) or matte (raw) surface that reacts to light: yes — anisotropic along grain.

## Physical behavior

**Surface finish**: semi-gloss (varnished) or matte (raw)

**Transparency**: opaque

**Reacts to light**: yes — anisotropic along grain

**Deforms**: no

**Age / wear**: acquired patina (darkening over time)

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(180deg, oklch(35% 0.08 40) 0%, oklch(22% 0.06 30) 100%);
  filter: url(#grain);
svg: |
  <filter id="grain">
    <feTurbulence type="turbulence" baseFrequency="0.02 0.3" numOctaves="3"/>
    <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.06  0 0 0 0 0.04  0 0 0 0.4 0"/>
  </filter>
  /* baseFrequency y ≫ x → vertical grain */
raster: scanned walnut at 2048px, mask with noise to hide tile seam
```

## Reactive behaviors

**Light**: glint travels along grain on tilt

**Highlight**: yes — narrow strip along grain

**Depth**: minor for varnished

**Parallax**: no

## Common implementation mistakes (avoid these)

- regularly repeating tile (mask with noise)
- isotropic noise (wood grain is directional)
- perfect varnish gloss without grain

## Examples in the wild

- iBooks wooden shelf
- GarageBand stage skin
- vintage radio cabinets

## Pairs with (prototype slugs)

- `style-skeuomorphism (library-as-wood-shelf)`
- `aesthetic-cottagecore`
- `aesthetic-steampunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
