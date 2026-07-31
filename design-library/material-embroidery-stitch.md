---
materialId: embroidery-stitch
name: Embroidery Stitch (hand-stitched thread on quilted fabric)
family: analog
category: textile
surfaceFinish: matte (soft nap with raised thread)
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-craft-sketchbook, aesthetic-cottagecore, style-doodle, shell-scrapbook-substrate]
images:
  - src: material-embroidery-stitch.png
    reason: Material fidelity sample.
---

# Embroidery Stitch (hand-stitched thread on quilted fabric)

Sparse hand stitches on a fabric ground: letterforms drawn in chain-stitch and backstitch thread, rules and dividers as dashed running stitches, and panels bounded by quilted padded seams - every line visibly made of short thread segments with a soft raised profile.

**Distinct from** `material-felt`, which is fuzzy die-cut shapes with no thread linework - stitch is LINE, felt is SHAPE; and from `jacquard-embroidery`, whose dense machine-woven imagery covers whole motifs - hand stitch stays sparse, linear, and visibly hand-paced.

## Physical behavior

**Surface finish**: matte - cotton thread sheen on brushed fabric nap

**Transparency**: opaque

**Reacts to light**: barely - a soft top-light picks out the raised thread and quilt padding

**Deforms**: yes - quilted panels puff between seams; stitches pucker the cloth slightly

**Age / wear**: gentle - the charm allows small stitch irregularity, never fraying chaos

## Implementation strategies

```yaml
css: |
  /* running-stitch rule */
  border: none;
  background-image: repeating-linear-gradient(90deg, #F5F6F8 0 8px, transparent 8px 15px);
  height: 2px; border-radius: 1px;
  /* quilted panel */
  .panel {
    background: #0B132B;
    border: 2px dashed rgba(245,246,248,0.7);
    border-radius: 14px;
    box-shadow: inset 0 2px 6px rgba(255,255,255,0.06), inset 0 -3px 8px rgba(0,0,0,0.45);
  }
svg: |
  stitched lettering: stroke-dasharray="9 6" stroke-linecap="round" on letterform paths,
  with a 1px darker duplicate path offset y+1 as the needle-hole shadow; chain stitch as
  a chain of small overlapping ellipses along the path
raster: macro photo of real chain stitch for hero wordmarks
animation: stroke-dashoffset draw-on = thread being sewn; use sparingly, one element at a time
usage: |
  object scope: headings as stitched script, dashed borders on buttons/cards, seam dividers
  medium scope: quilted dark-canvas ground with district-patch color fields sewn together
```

## Reactive behaviors

**Light**: minimal - fixed soft top-light on thread relief; no tracking

**Highlight**: none

**Depth**: quilt puff - inner shadow pair (light top, dark bottom) inside every seam-bounded panel

**Parallax**: none

## Common implementation mistakes (avoid these)

- plain CSS dashed borders as-is (equal machine-perfect dashes read as CAD, not sewing - round the caps, jitter the rhythm)
- stitches without holes (each stitch enters and exits the cloth; hint needle-hole shadow at segment ends)
- dense coverage (hand embroidery is sparse and linear; solid filled imagery drifts into jacquard territory)
- flat ground (without quilt padding shadows the fabric reads as printed paper)
- perfectly straight runs (hand stitch rows wander a degree or two; add slight path wobble)

## Examples in the wild

- embroidered samplers and hoop art
- quilted map wall hangings with stitched place names
- craft-brand packaging with running-stitch borders

## Pairs with (prototype slugs)

- `aesthetic-craft-sketchbook`
- `aesthetic-cottagecore`
- `style-doodle`
- `shell-scrapbook-substrate`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
