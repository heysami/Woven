---
materialId: halftone-cmyk
name: Halftone CMYK (newspaper / comic process)
family: analog
category: print
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-corporate-grunge, style-raster-cutout, aesthetic-acid-design, aesthetic-y2k-memphis-loud, recipe-newspaper-of-record]
images:
  - src: material-halftone-cmyk.png
    reason: Material fidelity sample.
---

# Halftone CMYK (newspaper / comic process)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: shows wear

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(circle at center, #000 0.5px, transparent 1.5px) 0 0/4px 4px;
  transform: rotate(45deg);  /* black at 45° */
svg: |
  Per-channel halftone: C @ 15°, M @ 75°, Y @ 0°, K @ 45° - the rosette
  pattern that hides moiré. Use <pattern> with rotated transforms.
webgl: |
  Sample image luminance, per-channel threshold against rotated dot grid.
raster: stack of 4 PNG halftone screens at correct angles
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: stepped only

## Common implementation mistakes (avoid these)

- grid-aligned dots for all channels (must rotate per channel)
- dot size too uniform (real halftone is luminance-driven)
- moiré-pattern alarms (caused by wrong screen angles)

## Examples in the wild

- Lichtenstein paintings
- Marvel comics 1960s
- daily newspaper photos

## References

- http://the-print-guide.blogspot.com/2009/05/halftone-screen-angles.html

## Pairs with (prototype slugs)

- `aesthetic-corporate-grunge`
- `style-raster-cutout`
- `aesthetic-acid-design`
- `aesthetic-y2k-memphis-loud`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
