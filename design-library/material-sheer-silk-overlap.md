---
materialId: sheer-silk-overlap
name: Sheer Silk Overlap (translucent fields that mix color)
family: analog
category: textile
surfaceFinish: matte (soft sheer sheen)
transparency: translucent (per fabric layer)
scope: both
pairsPrototypes: [style-aurorism, recipe-aurora-marketing, aesthetic-sculptural-minimal, aesthetic-swiss-modernist]
images:
  - src: material-sheer-silk-overlap.png
    reason: Material fidelity sample.
---

# Sheer Silk Overlap (translucent fields that mix color)

Layered planes of sheer dyed silk - indigo, madder red, saffron - stretched taut against light, each field translucent on its own and optically MIXING wherever two overlap: indigo over saffron yields violet, madder over indigo a deep plum, the crossings becoming new named colors with crisp straight edges.

**Distinct from** `material-vellum-translucency`, a neutral frosted paper that dims what is behind it without creating hue - sheer silk overlaps GENERATE new color; and from `material-frosted-glass`, which blurs its backdrop - sheer silk keeps every edge crisp and mixes chroma, not focus.

## Physical behavior

**Surface finish**: matte with a faint directional sheen along the weave

**Transparency**: translucent - each layer passes light; two layers multiply into a third hue

**Reacts to light**: yes - the fabric glows when backlit; fine diagonal weave striations show in raking light

**Deforms**: gentle - fields billow slowly like canopy cloth in air

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* each field is one sheer layer; overlaps do the mixing */
  .sheer {
    background: color-mix(in srgb, var(--dye) 72%, transparent);
    mix-blend-mode: multiply;      /* the load-bearing line - overlap = new hue */
    clip-path: polygon(...);       /* straight angled edges, canopy geometry */
  }
  .sheer--indigo  { --dye: #2A34BE; }
  .sheer--madder  { --dye: #B02E4A; }
  .sheer--saffron { --dye: #F0A21A; }
svg: |
  add a barely-there diagonal weave: repeating-linear-gradient 45deg at 2% white,
  masked inside each field so the striation direction differs per layer
webgl: |
  for hero canopies: quads with slow vertex billow + multiplicative blending;
  subtle per-layer noise in alpha for dye unevenness
usage: |
  object scope: secondary/active button fills as one sheer layer sliding over another,
  card headers as overlap crossings
  medium scope: full-bleed canopy hero - 3-4 angled fields crossing high in the frame,
  content on white below
```

## Reactive behaviors

**Light**: yes - backlight glow: fields nearest a light source lift in luminance

**Highlight**: none (no specular - sheer fabric has sheen, not gloss)

**Depth**: layer order is legible - each field's edge shows THROUGH the fields above it

**Parallax**: yes - layers drift at different rates on scroll; overlap colors shift as crossings move

## Common implementation mistakes (avoid these)

- alpha stacking without multiply (plain rgba overlap washes toward gray - the material NEEDS multiplicative mixing to make violet from indigo and saffron)
- blur on the layers (blur says glass; sheer silk stays crisp-edged)
- too many layers (past 3-4 dyes every crossing goes muddy brown; the exemplar palettes name each crossing)
- static composition (canopies breathe; a few px of slow billow keeps the cloth alive)
- ignoring the crossings (design the overlap zones deliberately - they are the palette's derived colors, name them in tokens)

## Examples in the wild

- dyed-silk canopy installations against the sky
- theater scrims lit from behind
- color-field textile art (overlapping chiffon panels)

## Pairs with (prototype slugs)

- `style-aurorism`
- `recipe-aurora-marketing`
- `aesthetic-sculptural-minimal`
- `aesthetic-swiss-modernist`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
