---
materialId: suminagashi-marbling
name: Suminagashi Marbling (monochrome ink-ring drift)
family: analog
category: print
surfaceFinish: matte
transparency: translucent (dilute ink veils)
scope: both
pairsPrototypes: [style-restrained-hairline, recipe-warm-restraint, aesthetic-japanese-poster-layout, aesthetic-chinese-curated-modernist, shell-centered-column]
images:
  - src: material-suminagashi-marbling.png
    reason: Material fidelity sample.
---

# Suminagashi Marbling (monochrome ink-ring drift)

A matte monochrome print of ink floated on still water: concentric rings widen from each dropped touch, currents pull the rings into feathered filaments, and the whole drift lifts onto white paper as veils of indigo-black over vast quiet margins.

**Distinct from** `material-ink-wash-sumi-e`, which is a brushed gesture - suminagashi has no stroke at all, only un-touched ink drifting on water; and from `paper-marbling-ebru`, which is polychrome and deliberately combed into figures - suminagashi is monochrome, uncombed, and shaped only by breath and current.

## Physical behavior

**Surface finish**: matte (dilute ink on soft white paper)

**Transparency**: translucent (each ring is a thin veil; overlaps darken)

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* concentric alternating ink/clear rings, then current-warped */
  background:
    repeating-radial-gradient(circle at 60% 40%,
      rgba(11,29,58,0.35) 0 1px, transparent 1px 14px,
      rgba(36,58,99,0.18) 14px 15px, transparent 15px 34px),
    #F6F7F8;
  filter: url(#sumi-current);
svg: |
  feTurbulence baseFrequency="0.002 0.008" octaves="3" + feDisplacementMap scale="140"
  warps the ring set into current filaments; a second faint turbulence layer at higher
  frequency gives the misted-gray dispersion where ink breaks into droplets
raster: scanned suminagashi sheet as ground truth; crops for card faces, wisps for edges
usage: |
  object scope: card faces, focused-input auras (a small ring set blooming at the caret)
  medium scope: one drifting current crossing an otherwise white frame - never full coverage
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: subtle - ring layers at 2-3 different scroll rates read as ink at different depths in the bath

## Common implementation mistakes (avoid these)

- adding color (suminagashi is indigo-black to misted gray on white; a second hue makes it ebru)
- uniform ring spacing (real rings crowd where the current compresses them and open where it pulls)
- covering the whole frame (the medium is 80 percent white water - restraint IS the material)
- hard ring edges everywhere (edges feather into droplet mist where the ink disperses)
- treating rings as decoration stamps (each ring set implies one dropped touch - place them like events, not pattern)

## Examples in the wild

- 12th-century Japanese suminagashi papers
- contemporary bookbinders' monochrome marbled endpapers
- meditation and tea-ceremony brand sites using drifting-ink heroes

## Pairs with (prototype slugs)

- `style-restrained-hairline`
- `recipe-warm-restraint`
- `aesthetic-japanese-poster-layout`
- `aesthetic-chinese-curated-modernist`
- `shell-centered-column`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
