---
materialId: jacquard-embroidery
name: Jacquard Embroidery (gold-thread brocade on midnight silk)
family: analog
category: textile
surfaceFinish: lustrous (metallic weft on matte silk ground)
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-dark-academia, aesthetic-neoclassical-remix, recipe-brand-story-journey]
images:
  - src: material-jacquard-embroidery.png
    reason: Material fidelity sample.
---

# Jacquard Embroidery (gold-thread brocade on midnight silk)

A woven surface where imagery and letterforms are BUILT AS THREAD: dense gold weft stitches assemble birds, borders and display type row by row on a midnight silk ground, every motif showing its individual stitch texture, with punch-card dot rows as the loom's visible instruction motif.

**Distinct from** `material-silk`, which is the plain drape and sheen of the cloth alone - jacquard carries pictorial weave ON that cloth; from `material-linen-weave`, a flat even weave texture with no figured imagery; and from `illust-3d-knit-yarn-character`, which sculpts yarn in 3D volume - jacquard imagery stays flat, woven into the plane of the fabric.

## Physical behavior

**Surface finish**: lustrous - metallic thread catches light per stitch; the silk ground stays matte-deep

**Transparency**: opaque

**Reacts to light**: yes - stitch-level glints shift as the light angle moves; never a smooth specular sweep

**Deforms**: no (stretched taut, banner-like)

**Age / wear**: ageless when kept taut; loose threads only as deliberate accents

## Implementation strategies

```yaml
css: |
  /* gold thread fill for type and motif shapes */
  color: transparent;
  background:
    repeating-linear-gradient(90deg, #D4AF37 0 2px, #B8932A 2px 3px, #8F6E1D 3px 4px);
  -webkit-background-clip: text; background-clip: text;
  text-shadow: 0 1px 0 rgba(0,0,0,0.6);  /* thread relief against the silk */
  /* silk ground */
  .ground { background: radial-gradient(120% 100% at 50% 0%, #27344F 0%, #0B1330 70%); }
svg: |
  build motifs from short parallel <line> stitch runs whose angle follows the form
  (feather direction, letter stroke direction); cross-stitch display type from a dot
  grid; border bands from repeated diamond stitch clusters
raster: photographed brocade with per-stitch glint is ground truth for hero motifs
usage: |
  object scope: display type, hero motifs (the woven bird), frame borders, button labels
  medium scope: full midnight-silk ground with woven chrome; punch-card cream strips
  (dot-punched rows) as headers/dividers quoting the loom's instructions
```

## Reactive behaviors

**Light**: yes - per-stitch glint: modulate a high-frequency highlight mask by pointer angle, never one big gloss sweep

**Highlight**: individual stitches brighten in bands as --light-angle moves across the weave

**Depth**: slight thread relief - 1px dark edge under each stitch run

**Parallax**: none (the fabric is one taut plane)

## Common implementation mistakes (avoid these)

- flat gold fill (#D4AF37 with no stitch striation reads as plastic, not thread)
- smooth glossy highlight sweeps (thread glints are granular and directional, per stitch)
- imagery that ignores stitch direction (stitch runs must follow the form like pen hatching)
- forgetting the punch-card motif (the dotted instruction rows are what make it JACQUARD, not generic embroidery)
- bright white ground (the register is gold on deep midnight; high-key grounds kill the brocade)

## Examples in the wild

- Jacquard-loom silk brocades and their punched instruction cards
- military and ecclesiastical goldwork banners
- luxury fashion-house monogram jacquards (scarves, upholstery)

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-dark-academia`
- `aesthetic-neoclassical-remix`
- `recipe-brand-story-journey`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
