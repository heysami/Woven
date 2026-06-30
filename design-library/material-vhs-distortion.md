---
materialId: vhs-distortion
name: VHS Distortion (chromatic aberration + scanlines + bleed)
family: analog
category: film
surfaceFinish: glossy
scope: medium
fxStack: [crt, chromatic-aberration, slice]
transparency: opaque
pairsPrototypes: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-cyberpunk, aesthetic-y2k-myspace, aesthetic-acid-graphics]
images:
  - src: material-vhs-distortion.png
    reason: Material fidelity sample.
---

# VHS Distortion (chromatic aberration + scanlines + bleed)

A glossy surface and deforms: yes - tape head distortion bands.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes - tape head distortion bands

**Age / wear**: shows wear (drop-outs)

## Implementation strategies

```yaml
css: |
  filter: contrast(1.05) saturate(1.1);
svg: |
  <feOffset in="SourceGraphic" dx="2" dy="0" result="R"/>
  <feOffset in="SourceGraphic" dx="-2" dy="0" result="B"/>
  <feColorMatrix in="R" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/>
  <feColorMatrix in="B" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"/>
  <feBlend mode="screen"/>
webgl: |
  RGB-shift in fragment shader; horizontal scanline darken; periodic
  vertical roll bar at 6s interval (the tape-tracking jitter)
raster: real VHS rip overlay at multiply
video: looping VHS distortion source at overlay
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: no

## Common implementation mistakes (avoid these)

- static RGB shift (real VHS varies)
- no scanlines (VHS interlace is signature)
- no horizontal bleed

## Examples in the wild

- 90s home video aesthetic
- vaporwave music videos

## References

- https://halisavakis.com/write-up-vhs-image-effect/

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-myspace`
- `aesthetic-acid-graphics`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
