---
materialId: denim
name: Denim (twill weave, indigo fade)
family: analog
category: fabric
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-y2k-myspace, aesthetic-cottagecore, aesthetic-corporate-grunge]
images:
  - src: material-denim.png
    reason: Material fidelity sample.
---

# Denim (twill weave, indigo fade)

A matte surface and deforms: yes — soft drape.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: yes — soft drape

**Age / wear**: acquired patina (whiskers, fade at stress points)

## Implementation strategies

```yaml
css: |
  background:
    repeating-linear-gradient(45deg,
      oklch(35% 0.10 250) 0px,
      oklch(40% 0.10 250) 2px,
      oklch(33% 0.10 250) 4px
    );
svg: noise + slight horizontal-fade gradient at wear points (whiskers)
raster: scanned denim is the truth
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: yes — drape

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- perfect uniform indigo (denim is uneven)
- no twill direction visible
- no fade at stress points

## Examples in the wild

- Levi's tab stitching
- fashion editorial denim closeups

## Pairs with (prototype slugs)

- `aesthetic-y2k-myspace`
- `aesthetic-cottagecore`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
