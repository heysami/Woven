---
materialId: decollage-poster-layers
name: Decollage Poster Layers (stratified torn billboard skins)
family: analog
category: paper
surfaceFinish: matte (weathered paste-board, halftone ink grain)
scope: both
transparency: opaque (each skin hides the one beneath until torn)
pairsPrototypes: [aesthetic-corporate-grunge, aesthetic-zine-type-wall, style-raster-cutout, style-ransom-glyph-mix, shell-scrapbook-substrate, recipe-editorial-magazine]
images:
  - src: material-decollage-poster-layers.png
    reason: Material fidelity sample.
---

# Decollage Poster Layers (stratified torn billboard skins)

A stratigraphy of pasted poster skins: hand-rips expose older ink layers beneath, and type survives only as cropped fragments.

## Physical behavior

**Surface finish**: matte paste-board; each skin carries its own flat ink color and screen-ink grain

**Transparency**: opaque per skin; depth comes from tearing, never from blending

**Reacts to light**: no

**Deforms**: tears, curls at rip edges; every rip exposes a white fibrous deckle lip

**Age / wear**: heavily weathered - sun-faded inks, paste ghosting, scuffed halftone

## Implementation strategies

```yaml
css: |
  /* each poster skin is an absolutely-positioned layer with a jagged clip-path */
  .skin { position: absolute; inset: 0; clip-path: polygon(/* irregular, hand-drawn verts */); }
  .skin-indigo { background: #56728a; } .skin-red { background: #c94b4a; }
  .skin-night { background: #0e1a27; } .skin-chalk { background: #f2ece1; }
  /* the fibrous white rip lip: a pale offset shadow hugging the torn contour */
  .skin { filter: drop-shadow(0 1.5px 0 rgba(242,236,225,0.9)); }
  /* type fragments: oversized display caps, deliberately cropped by the tear */
  .fragment { font-size: clamp(4rem, 18vw, 14rem); overflow: hidden; }
svg: |
  tear contours as <clipPath> paths with small-amplitude jitter (5-15px verts);
  halftone dot <pattern> multiplied into each ink skin
raster: scanned billboard rips for ground-truth edge fiber and paste ghosting
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: stacking order IS the material - hover can peel a rip slightly wider (clip-path transition), revealing more of the layer beneath

**Parallax**: subtle - deeper skins scroll a touch slower, selling the stratigraphy

## Common implementation mistakes (avoid these)

- a single decorative rip on one card (that is material-torn-edge; decollage needs a STACK, minimum three ink skins visible through each other)
- reusing one clip-path polygon (every tear is a different hand-rip; repeat = instant fake)
- rips without the white fiber lip (a torn poster always shows the paper core at the tear)
- pristine flat inks (skins must carry grain, fade, and scuff - they have lived outdoors)
- whole words surviving intact (fragments crop mid-letter; legibility loss is the aesthetic)
- blending layers with opacity (skins are opaque; only tearing reveals)

## Examples in the wild

- Jacques Villegle and Raymond Hains torn-poster works
- Mimmo Rotella decollage canvases
- weathered city hoarding walls and gig-poster pillars

## Pairs with (prototype slugs)

- `aesthetic-corporate-grunge`
- `aesthetic-zine-type-wall`
- `style-raster-cutout`
- `style-ransom-glyph-mix`
- `shell-scrapbook-substrate`
- `recipe-editorial-magazine`

## Differentiation

- vs `material-torn-edge`: torn-edge is one deckled rip on a single sheet; decollage is a multi-layer poster archaeology - stacked opaque ink skins, each tear a window into the stratum below, with type fragments cropped by the rips

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
