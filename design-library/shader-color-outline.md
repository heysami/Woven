---
shaderId: color-outline
name: Color Outline (stacked offset outlines + gradient edge line-art)
family: filter
category: image-effect
subCategory: edge
role: overlay
defaultBlend: screen
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-acid-design, aesthetic-neubrutalism, aesthetic-monochrome-pop-poster, aesthetic-y2k-memphis-loud]
notForUseWhen: photoreal product, subtle luxury
---

# Color Outline (stacked offset outlines + gradient edge line-art)

Detect the layer's edges and re-draw them as crisp colored contour lines - one outline, or a stack of concentric offset outlines in shifting hues (the Figma `Outlines` + `Colored edges` effects). Turns any image or shape into vibrant poster line-art.

## Stack contract

- **Role:** FILTER - reads a SOURCE beneath (its edges / luminance gradient).
- **Layer:** top - drawn over the content (or replacing it for pure line-art).
- **Default blend when stacked:** `screen` (glowing lines on dark) or `normal` (poster ink on light).
- **Animated:** optional - hue can cycle along the outline stack; offsets can pulse.
- **Applies to:** the layer below; strongest on high-contrast shapes and type.

## Implementation strategies

```yaml
webgl: |
  // Sobel edge magnitude
  float e = sobel(u_src, uv, u_texel);
  // map edge -> N stacked rings by thresholding at increasing radii (dilate)
  // color each ring from a gradient ramp by index
  vec3 col = gradientRamp(edgeBand(e)) * step(u_thresh, e);
engine: |
  Figma effects: `Outlines` (stacked spacing/thickness) + `Colored edges` (gradient line-art).
  mm-composer: `text-outline` (the live outline effect) extended to N rings.
svg: feMorphology (dilate) + feComposite to ring + feColorMatrix per ring - true DOM stacked outlines.
css: -webkit-text-stroke for type only; no image edges.
```

## Parameters (knobs)

- `ringCount`, `spacing`, `thickness`, `gradient` (hue ramp across rings), `edgeThreshold`, `mode` (lines-only / lines-over-fill).

## Stacking recipes

- Color Outline (rings, screen) over `gradient-map` = duotone fill with rainbow contour halo - peak acid-poster.
- Single thick black outline (normal) over a flat shape = neubrutalist sticker.

## Common mistakes (avoid these)

- Edge threshold too low (every JPEG artifact becomes a line - noise) - clamp and pre-blur the source.
- Rainbow rings on a busy photo (chaos) - reserve stacked-hue rings for simple shapes / type.
- Outline thickness uniform at all DPRs (vanishes on retina) - scale by device px.

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-neubrutalism`
- `aesthetic-monochrome-pop-poster`
- `aesthetic-y2k-memphis-loud`
