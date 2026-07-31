---
materialId: patchwork-quilt
name: Patchwork Quilt (hand-pieced fabric assembly)
family: analog
category: textile
surfaceFinish: matte
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-craft-sketchbook, shell-scrapbook-substrate, style-serif-warm-paper]
images:
  - src: material-patchwork-quilt.png
    reason: Material fidelity sample.
---

# Patchwork Quilt (hand-pieced fabric assembly)

A surface ASSEMBLED from mismatched fabric patches - washed chambray, ticking stripe, worn black twill, cream laundry cloth - each patch cut with pinked zigzag edges, joined by visible red running-stitch seams, and labeled with sewn cloth tags carrying handwriting and stamped caps.

**Distinct from** `material-denim`, one continuous fabric with its own twill grain - patchwork's identity is the JOIN: many fabrics, seams and edge treatments in one plane; and from `material-felt`, whose thick fuzzy die-cut shapes float free - quilt patches are thin woven cloth sewn edge-to-edge.

## Physical behavior

**Surface finish**: matte - washed, sun-faded cloth; no sheen anywhere

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: slight - patches bow gently between seams; nothing lies perfectly flat

**Age / wear**: worn-in by design - fading, fray whisper at pinked edges, mends as ornament

## Implementation strategies

```yaml
css: |
  /* a patch */
  .patch {
    background: #8FA7BD;                        /* per-patch swatch color or fabric tile */
    border: 1.5px dashed #D33A3A;               /* bright running-stitch seam */
    clip-path: polygon(/* zigzag pinked edge points */);
    box-shadow: 0 1px 2px rgba(0,0,0,0.18);     /* patch sits ON the ground */
    transform: rotate(-0.6deg);                  /* hand-pieced, never square */
  }
  /* cloth label */
  .label { background: #F3EFE6; border: 1px dashed #D33A3A; font-family: var(--font-hand); }
svg: |
  pinked edges as a zigzag path filter on rect outlines; seam stitches as
  stroke-dasharray red paths riding exactly on patch boundaries
raster: fabric weave tiles (chambray, ticking stripe, herringbone twill) at low scale,
  multiplied under each patch color so every patch has its own cloth grain
usage: |
  object scope: cards and buttons as sewn-on patches, inputs as cloth labels, nav as a
  strip of joined patches
  medium scope: the whole page as one quilt - blocks of differing fabric joined by
  stitched seams, content living on lighter patches
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: layered - patches cast 1-2px soft shadows on the ground; a pressed (active) patch flattens

**Parallax**: none

## Common implementation mistakes (avoid these)

- one shared fabric texture for every patch (the whole point is MIXED cloths - vary weave, stripe direction, wear per patch)
- clean straight edges (pinked zigzag or slight fray is what says cut-and-sewn)
- seams that do not follow patch boundaries (stitch lines must ride the joins, not float as decoration)
- perfect grid alignment (hand piecing wanders; give each patch sub-degree rotation and a few px of drift)
- pristine saturated color (quilt fabrics are washed and faded; cap saturation and add subtle sun-fade gradients)

## Examples in the wild

- memory quilts sewn from a family's worn garments
- AIDS Memorial Quilt panels
- gee's Bend quilts; craft-revival brand lookbooks

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-craft-sketchbook`
- `shell-scrapbook-substrate`
- `style-serif-warm-paper`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
