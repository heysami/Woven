---
materialId: ink-wash-sumi-e
name: Ink Wash (sumi-e / brush-and-ink)
family: analog
category: ink
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [aesthetic-anti-design, aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-vaporwave (Japanese gloss element)]
images:
  - src: material-ink-wash-sumi-e.png
    reason: Material fidelity sample.
---

# Ink Wash (sumi-e / brush-and-ink)

A matte surface (translucent).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  color: #1a1a1a;
  filter: url(#sumiEdge);
svg: |
  <filter id="sumiEdge">
    <feTurbulence baseFrequency="0.04" numOctaves="2"/>
    <feDisplacementMap scale="3"/>
  </filter>
  <!-- Edge irregularity at SMALL scale - sumi brush keeps a recognizable form -->
raster: scanned sumi-e brushwork is the most direct path
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- regular vector stroke (sumi varies in pressure)
- black at #000 (sumi ink is dark grey with brown undertone)
- no paper bleed at terminals

## Pairs with (prototype slugs)

- `aesthetic-anti-design`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `aesthetic-vaporwave (Japanese gloss element)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
