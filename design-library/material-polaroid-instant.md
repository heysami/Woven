---
materialId: polaroid-instant
name: Polaroid / Instant Photo (square frame, faded chemistry)
family: analog
category: film
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-coastal-grandmother, recipe-readcv]
images:
  - src: material-polaroid-instant.png
    reason: Material fidelity sample.
---

# Polaroid / Instant Photo (square frame, faded chemistry)

A glossy surface that reacts to light: yes - reflective sheen and deforms: minimal.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes - reflective sheen

**Deforms**: minimal

**Age / wear**: acquired patina (yellowing, fade)

## Implementation strategies

```yaml
css: |
  .polaroid {
    background: #f4ede1;
    padding: 12px 12px 56px;
    box-shadow:
      0 1px 2px rgba(0,0,0,0.2),
      0 14px 28px -8px rgba(0,0,0,0.4);
    transform: rotate(-2deg);
    font-family: 'Caveat', cursive;
  }
  .polaroid img { filter: saturate(0.85) contrast(0.95); }
raster: polaroid frame PNG
```

## Reactive behaviors

**Light**: subtle gloss on hover

**Highlight**: minimal

**Depth**: hover lifts the frame

**Parallax**: in scrapbook layouts, yes

## Common implementation mistakes (avoid these)

- all polaroids at the same angle (real ones scatter)
- no chemistry fade
- caption in a digital font (must be handwritten)

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `aesthetic-cottagecore`
- `aesthetic-y2k-myspace`
- `aesthetic-coastal-grandmother`
- `recipe-readcv`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
