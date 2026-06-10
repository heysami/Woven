---
materialId: datamosh-compression-smear
name: Datamosh (codec interpolation failure)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-acid-design, aesthetic-y2k-futurism, aesthetic-dreamcore, aesthetic-weirdcore]
---

# Datamosh (codec interpolation failure)

A matte surface and deforms: yes — frame motion stretches old pixels along predicted vectors.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes — frame motion stretches old pixels along predicted vectors

**Age / wear**: ageless (or feels 2008-Tumblr era)

## Implementation strategies

```yaml
css: |
  /* approximation only — true datamosh needs WebGL */
  filter: blur(0.5px) saturate(1.2);
  mix-blend-mode: screen;
webgl: |
  sample previous frame, displace UVs by motion vectors derived from current
  frame's flow field; never refresh the I-frame. Shadertoy "datamosh" examples
  from beesandbombs and dwitter are the references. Best driven by an
  input video (mp4) and shader stage.
raster: pre-rendered datamosh video texture under content (looped mp4 or webm)
```

## Reactive behaviors

**Light**: none — datamosh smears existing pixels

**Highlight**: pointer can seed the motion-vector field for interactive smear

**Depth**: stuck-frame "pause" reads as compressed time

**Parallax**: motion compounds with scroll position (each scroll-tick adds a smear)

## Common implementation mistakes (avoid these)

- datamosh over still imagery (it needs motion to smear)
- clean cuts between datamoshed clips (real datamosh is continuous)
- excessive opacity (datamosh reads as material, not as filter)

## Examples in the wild

- Kanye West "Welcome to Heartbreak" music video
- Takeshi Murata datamosh fine-art
- Sapeur album covers

## References

- https://www.shadertoy.com/results?query=datamosh

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `aesthetic-acid-design`
- `aesthetic-y2k-futurism`
- `aesthetic-dreamcore`
- `aesthetic-weirdcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
