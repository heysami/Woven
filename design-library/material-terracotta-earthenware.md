---
materialId: terracotta-earthenware
name: Terracotta Earthenware (unglazed fired clay with coil logic)
family: analog
category: ceramic
surfaceFinish: matte (rough fired-clay grain)
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-pastoral-serene, aesthetic-cottagecore, recipe-warm-restraint, aesthetic-craft-sketchbook]
images:
  - src: material-terracotta-earthenware.png
    reason: Material fidelity sample.
---

# Terracotta Earthenware (unglazed fired clay with coil logic)

Real fired earth: rough unglazed clay surfaces with granular pore texture and pit flecks, banded courses laid like coil construction, seams of slip-white rope between them, and an earthen palette running terracotta through raw clay, umber and wet-clay dark to dry sand and slip white.

**Distinct from** `material-matte-clay`, the digital claymorphism of soft airbrushed blobs with clean gradients - terracotta is ROUGH, granular, kiln-fired and architectural; and from `material-ceramic-glaze`, whose glassy coat and specular sweep terracotta explicitly lacks - this is the clay BEFORE the glaze.

## Physical behavior

**Surface finish**: matte and toothy - fired clay grain with sand pits; zero specular

**Transparency**: opaque

**Reacts to light**: no gloss - only raking-light relief on coil ridges and stamped marks

**Deforms**: no (fired hard); construction happened BEFORE firing and is frozen into the coils

**Age / wear**: weathers with dignity - sun-fade at edges, compacted-earth darkening at feet

## Implementation strategies

```yaml
css: |
  /* fired-clay slab */
  background:
    url(clay-grain.png) repeat,               /* fine granular pore texture, multiply ~10% */
    linear-gradient(180deg, #C86A4A, #A3553A);
  border-radius: 6px;                          /* softened corners, hand-formed not machined */
  /* slip seam between courses */
  .seam { height: 3px; background: #EDE7DC; border-radius: 2px;
          box-shadow: 0 1px 1px rgba(59,47,40,0.35); }
svg: |
  coil courses as stacked horizontal bands, each with slightly different clay hue and a
  slip-white rope seam; stamped icons as debossed marks (dark inset top, light lower lip)
raster: photographed raw clay + compacted earth tiles as ground-truth fills
usage: |
  object scope: buttons as stamped clay tabs, cards as slip-bordered slabs, icons debossed
  medium scope: the frame as coursed construction - stacked color bands with seams,
  content resting on dry-sand and slip-white fields
```

## Reactive behaviors

**Light**: no highlight tracking - clay is dead matte; relief only

**Highlight**: none (a specular sweep would instantly read as glaze)

**Depth**: press states deboss - active elements darken toward wet clay and inset 1px, like a thumb pressed into the surface

**Parallax**: none (earthen mass does not float)

## Common implementation mistakes (avoid these)

- any gloss or specular sweep (glazed = a different material; terracotta is pre-glaze earth)
- smooth flat fills (fired clay always carries granular pore texture - without it this is just orange UI)
- forgetting the seams (coil logic - courses joined by slip lines - is what makes it construction, not paint)
- neon-clean saturation (earthen pigments are iron oxides; keep chroma muted and warm)
- hard machine corners (hand-built clay rounds every edge slightly)

## Examples in the wild

- coiled earthenware vessels and rammed-earth architecture
- adobe and terracotta facade systems
- slow-craft pottery studio brand sites

## Pairs with (prototype slugs)

- `aesthetic-pastoral-serene`
- `aesthetic-cottagecore`
- `recipe-warm-restraint`
- `aesthetic-craft-sketchbook`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
