---
materialId: pencil-graphite
name: Pencil Graphite (HB to 6B sketch)
family: analog
category: ink
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [style-doodle, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-anti-design]
images:
  - src: material-pencil-graphite.png
    reason: Material fidelity sample.
---

# Pencil Graphite (HB to 6B sketch)

A matte surface (translucent) that reacts to light: yes — graphite glints at angle.

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: yes — graphite glints at angle

**Deforms**: no

**Age / wear**: shows wear (smudges)

## Implementation strategies

```yaml
css: |
  mix-blend-mode: multiply;
  filter: url(#graphite) contrast(0.8);
svg: |
  <filter id="graphite">
    <feTurbulence baseFrequency="0.7" numOctaves="2"/>
    <feColorMatrix values="0 0 0 0 0.2  0 0 0 0 0.2  0 0 0 0 0.22  0 0 0 0.5 0"/>
  </filter>
raster: scanned graphite drawing on textured paper
```

## Reactive behaviors

**Light**: subtle glint on hover (pointer-driven)

**Highlight**: minimal

**Depth**: smudge on press

**Parallax**: no

## Common implementation mistakes (avoid these)

- pure black (graphite is blue-grey)
- no paper texture visible underneath

## Examples in the wild

- architectural sketches
- storyboards
- magazine essay illustrations

## Pairs with (prototype slugs)

- `style-doodle`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `aesthetic-anti-design`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
