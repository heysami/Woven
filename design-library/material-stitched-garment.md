---
materialId: stitched-garment
name: Stitched Garment (tailored construction chrome on dark silk)
family: analog
category: textile
surfaceFinish: matte (fine silk nap with metallic hardware)
transparency: opaque
scope: object
pairsPrototypes: [aesthetic-luxury-cinematic-dark, recipe-object-stage-hero, style-restrained-hairline, aesthetic-monochrome-tech-editorial]
images:
  - src: material-stitched-garment.png
    reason: Material fidelity sample.
---

# Stitched Garment (tailored construction chrome on dark silk)

Garment CONSTRUCTION as interface chrome: near-black tailored silk panels bounded by dashed stitch channels, with functional gold drawcords threaded through concealed channels, brass eyelets as terminals, and cord ends marking state - the atelier's engineering made visible as thin luminous hardware on darkness.

**Distinct from** `material-silk`, which is the fabric's drape and sheen alone - stitched-garment is about the TAILORING: seams, channels, cords and eyelets doing structural work; and from `material-smooth-leather`, whose thick hide panels and heavy saddle stitching read as leather goods - this is fine cloth with threaded cordage, precise and lightweight.

## Physical behavior

**Surface finish**: matte silk with tiny warm-metal accents (eyelets, cord tips)

**Transparency**: opaque

**Reacts to light**: barely - graphite-on-black panel seams; only the gold cord and eyelets glint

**Deforms**: yes - pulling a drawcord gathers the channel; panels curve under cord tension

**Age / wear**: ageless (couture-kept)

## Implementation strategies

```yaml
css: |
  /* stitch-channel panel */
  .panel {
    background: linear-gradient(160deg, #0B0B0D, #17181B);
    border: 1px dashed #3E424A;                 /* graphite stitch channel */
    border-radius: 10px;
  }
  /* drawcord */
  .cord {
    height: 2px;
    background: repeating-linear-gradient(90deg, #D4AF37 0 3px, #8F6E1D 3px 5px); /* braid twist */
  }
  /* eyelet terminal */
  .eyelet {
    width: 10px; height: 10px; border-radius: 50%;
    border: 2px solid #B8932A; background: #0B0B0D;
  }
svg: |
  cords as <path> with a two-tone braid stroke pattern, ALWAYS terminating in an eyelet
  ring; sliders and progress = a cord drawn through eyelets, pulled length = value;
  tension curve on drag via slight quadratic bend of the cord path
usage: |
  object scope only: buttons as stitched tabs with cord-and-eyelet ends, sliders as
  drawcords, cards as tailored panels whose active state tightens the stitch border
  and pulls the cord taut; keep the medium itself plain dark silk
```

## Reactive behaviors

**Light**: minimal - static low sheen on silk; cord glints on hover

**Highlight**: the gold cord brightens and its dashes tighten on the active control

**Depth**: channel relief - dashed seams sit in a 1px groove (dark top inner shadow)

**Parallax**: cord tension - on drag, cords bow and straighten with eased spring, like real cordage

## Common implementation mistakes (avoid these)

- cords that end nowhere (every cord passes through or terminates in an eyelet - unanchored cords break the construction logic)
- flat solid gold lines (a drawcord is braided; give it the two-tone twist striation)
- bright borders everywhere (the register is near-black on black; graphite seams barely visible, gold reserved for the functional cord)
- decorating with hardware (eyelets and cords must map to actual affordances - controls, progress, ties - or they read as costume)
- stiff instant motion (cord interactions ease like tensioned cloth, with a tiny overshoot and settle)

## Examples in the wild

- technical-fashion drawcord garments (transforming capes, cinched silhouettes)
- luxury packaging with cord-and-eyelet closures
- high-end tailoring lookbooks shot on black

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `recipe-object-stage-hero`
- `style-restrained-hairline`
- `aesthetic-monochrome-tech-editorial`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
