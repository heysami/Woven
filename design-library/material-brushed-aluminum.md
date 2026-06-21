---
materialId: brushed-aluminum
name: Brushed Aluminum (anisotropic metal)
family: digital
category: metal
surfaceFinish: semi-gloss
transparency: opaque
pairsPrototypes: [aesthetic-cassette-futurism, aesthetic-dieselpunk, aesthetic-steampunk, style-skeuomorphism (recorder-as-tape-deck)]
images:
  - src: material-brushed-aluminum.png
    reason: Material fidelity sample.
---

# Brushed Aluminum (anisotropic metal)

A semi-gloss surface that reacts to light: yes - anisotropic highlight perpendicular to brush direction.

## Physical behavior

**Surface finish**: semi-gloss

**Transparency**: opaque

**Reacts to light**: yes - anisotropic highlight perpendicular to brush direction

**Deforms**: no

**Age / wear**: shows wear (scratches deepen)

## Implementation strategies

```yaml
css: |
  background:
    repeating-linear-gradient(90deg,
      rgba(255,255,255,0.06) 0px,
      rgba(0,0,0,0.06) 1px,
      rgba(255,255,255,0.06) 2px
    ),
    linear-gradient(180deg, #d6d8db 0%, #a8abb1 100%);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.4),
    inset 0 -1px 0 rgba(0,0,0,0.3),
    0 1px 2px rgba(0,0,0,0.2);
svg: |
  <filter id="brushed">
    <feTurbulence type="turbulence" baseFrequency="0.8 0.01" numOctaves="2"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.18 0"/>
  </filter>
  /* baseFrequency x ≫ y → directional grain */
raster: 2048px scan of real brushed metal at 0.18 opacity multiply
```

## Reactive behaviors

**Light**: highlight stretches ALONG the grain direction on tilt (90deg), never across

**Highlight**: pointer tracks but highlight is elongated

**Depth**: hairline scratch overlay reveals at hover

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- isotropic noise instead of directional grain
- brushed pattern at huge scale (the grain has to be sub-mm)
- circular highlight instead of elongated one

## Examples in the wild

- iPod nano body
- MacBook Pro casing
- Sony WALKMAN front face

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-dieselpunk`
- `aesthetic-steampunk`
- `style-skeuomorphism (recorder-as-tape-deck)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
