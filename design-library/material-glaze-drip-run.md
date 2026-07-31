---
materialId: glaze-drip-run
name: Glaze Drip Run (gravity-run cobalt glaze on porcelain)
family: analog
category: ceramic
surfaceFinish: glossy (runny glaze) over matte porous shelf
transparency: translucent where thin, pooling opaque
scope: object
pairsPrototypes: [aesthetic-industrial-catalog, aesthetic-monochrome-tech-editorial, style-micro-text-frame]
images:
  - src: material-glaze-drip-run.png
    reason: Material fidelity sample.
---

# Glaze Drip Run (gravity-run cobalt glaze on porcelain)

Ceramic glaze caught mid-run: deep cobalt flowing down chalk-white ware under kiln gravity, thinning to translucent sapphire at the top, gathering into runny beads and drip fingers along lower edges, and stopping in glassy pooled feet just before the shelf - the material's entire story is WHERE THE FLOW STOPPED.

**Distinct from** `material-ceramic-glaze`, which is a uniform high-gloss coat with a centered specular sweep and no history - drip-run is glaze WITH GRAVITY IN IT: uneven coverage, directional beads, pooled bottoms, and bare ware where the glaze never reached.

## Physical behavior

**Surface finish**: glossy where glazed (deepening with thickness), matte chalk where bare

**Transparency**: translucent at thin top veils, saturating to opaque near-black in fused pools

**Reacts to light**: yes - wet-look gloss on beads and pools; the bare shelf stays dead flat

**Deforms**: no - the run is arrested by the kiln; drips never move again

**Age / wear**: ageless (vitrified)

## Implementation strategies

```yaml
css: |
  /* an element's bottom edge as a glaze run */
  .glazed {
    background: linear-gradient(180deg, #163E8C 0%, #1E3FAE 70%, #0B1A33 100%); /* thickens downward */
    border-radius: 8px 8px 10px 10px;
  }
  .glazed::after {                              /* drip fringe */
    content: ""; position: absolute; inset: auto 0 -10px 0; height: 12px;
    background: inherit;
    -webkit-mask: url(#drip-fringe);            /* irregular finger silhouettes, varied lengths */
            mask: url(#drip-fringe);
  }
svg: |
  drip fringe as a path of alternating finger lobes - widths 4-14px, lengths 4-16px,
  each ending in a rounded bead; one or two long runners allowed per edge; add a 1px
  white sliver highlight down each bead's left side for the wet glint
raster: macro photo of test-tile drips for hero surfaces
usage: |
  object scope only: primary buttons and active cards grow drips on their bottom edge,
  section headers bleed a single runner into the page, status chips pool at their feet;
  the surrounding page stays chalk-white matte shelf
```

## Reactive behaviors

**Light**: yes - a narrow wet glint rides each bead; shifts subtly with pointer

**Highlight**: pools carry a small fixed skylight reflection; thin veils carry none

**Depth**: thickness = darkness - encode state weight as glaze depth (hover thin, active pooled)

**Parallax**: none, but drips may EXTEND slowly on press-and-hold, arrested on release

## Common implementation mistakes (avoid these)

- uniform even drips (equal-length equal-width fingers read as a picket fence; real runs are irregular, a few long runners among short beads)
- drips on all four sides (gravity has one direction - bottom edges only, always)
- flat single-blue fill (glaze DEEPENS with thickness: translucent sapphire to near-black pool is the signature gradient)
- gloss on the ground (the shelf/page must stay matte chalk so the wet glaze reads wet by contrast)
- animated dripping loops (the kiln arrested the flow; motion is only ever a one-shot extension, then stillness)

## Examples in the wild

- high-fire cobalt and tenmoku glaze runs on studio pottery
- kiln-shelf test tiles documenting glaze flow
- oribe and copper-red ware with deliberate pooled feet

## Pairs with (prototype slugs)

- `aesthetic-industrial-catalog`
- `aesthetic-monochrome-tech-editorial`
- `style-micro-text-frame`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
