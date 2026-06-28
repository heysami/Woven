---
shaderId: metaball-merge
name: Metaball Merge (gooey blobs that fuse and split)
family: source
category: generative-fill
subCategory: field
role: background
defaultBlend: normal
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-frutiger-aero, aesthetic-positivity-kawaii, style-claymorphism, aesthetic-y2k-futurism]
notForUseWhen: serious financial UI, dense data
images:
  - src: shader-metaball-merge.png
    reason: Metaball Merge (gooey blobs that fuse and split) - shader fill preview.
---

# Metaball Merge (gooey blobs that fuse and split)

Soft blobs that bulge toward each other and merge into smooth gooey bridges as they meet, then split apart - the Figma `Gooey merge` / classic metaball field. Liquid, lava-lamp, Y2K-aqua motion.

## Stack contract

- **Role:** SOURCE (scalar field thresholded into blobs).
- **Layer:** background or mid.
- **Default blend when stacked:** `normal` (blobs are opaque) or `screen` for glowing-goo.
- **Animated:** yes - blob centers orbit; the merge bridges form from the summed field.
- **Stacks under:** `lens-distortion` (glassy bulge), `gradient-map` (recolor the goo).

## Implementation strategies

```yaml
webgl: |
  float field = 0.0;
  for (int i=0;i<N;i++) field += u_r[i] / length(uv - u_p[i]);  // metaball sum
  float blob = smoothstep(u_thresh-0.02, u_thresh+0.02, field);
  vec3 col = mix(u_bg, u_blob, blob);
engine: |
  Figma effect: `Gooey merge`. paper-design/shaders: `metaballs`.
css/svg: |
  the classic SVG "gooey filter" = feGaussianBlur + feColorMatrix alpha-contrast (real DOM metaballs).
canvas2d: sum the field on a grid; marching-squares or per-pixel threshold.
```

## Parameters (knobs)

- `count`, `blobColor`, `bgColor`, `threshold` (gooeyness), `speed`, `sizeRange`, `glow`.

## Stacking recipes

- Metaball Merge + `lens-distortion` (top) = liquid glass lozenges (Apple-aqua / liquid-glass register).
- `gradient-map` over the goo = recolor the blobs to a brand duotone without touching the sim.

## Common mistakes (avoid these)

- Threshold band too sharp (hard-edged circles, no goo) - widen the smoothstep for the merge bridge.
- Too many blobs (the field saturates into one mass) - 3-6 reads as distinct merging drops.
- Flat fill with no highlight (looks like a stain) - add an inner gloss or stack lens-distortion.

## Pairs with (prototype slugs)

- `aesthetic-frutiger-aero`
- `aesthetic-positivity-kawaii`
- `style-claymorphism`
- `aesthetic-y2k-futurism`
