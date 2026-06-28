---
shaderId: dither
name: Dither (Atkinson / Floyd-Steinberg / Bayer screen)
family: filter
category: image-effect
subCategory: screen-pattern
role: overlay
defaultBlend: normal
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-8-bit-generic, style-pixel-bitmap, aesthetic-cassette-futurism, aesthetic-monochrome-pop-poster]
notForUseWhen: smooth premium gradients, photoreal hero
images:
  - src: shader-dither.png
    reason: Dither (Atkinson / Floyd-Steinberg / Bayer screen) - shader fill preview.
---

# Dither (Atkinson / Floyd-Steinberg / Bayer screen)

Stylized dithering of the layer beneath using the classic algorithms - Atkinson, Floyd-Steinberg, ordered Bayer - quantizing it to 1-bit / 2-bit / a small palette. The Figma `Dither` effect: the standalone screen you drop on ANY layer (the filter twin of `dither-waves`).

## Stack contract

- **Role:** FILTER - quantizes a SOURCE beneath (image / gradient / shader stack).
- **Layer:** top finishing screen.
- **Default blend when stacked:** `normal` (it replaces with the quantized result).
- **Animated:** NO - the dither matrix MUST be frozen (an animating matrix crawls). Let the SOURCE move instead.
- **Applies to:** the flattened layers below.

## Implementation strategies

```yaml
webgl: |
  float l = luma(texture(u_src, uv).rgb);
  float t = (u_algo==0) ? bayer8(gl_FragCoord.xy)        // ordered
                        : floydThreshold(uv);            // error-diffusion (multi-pass)
  vec3 col = paletteSnap(l, t, u_palette);               // 1-bit / 2-bit / N colors
engine: |
  Figma effect: `Dither`. paper-design/shaders: `dithering`. As a SOURCE+dither combo see `dither-waves`.
canvas2d: ImageData Floyd-Steinberg error diffusion (true serpentine pass).
svg: not appropriate (no per-pixel quantization).
```

## Parameters (knobs)

- `algorithm` (atkinson / floyd / bayer4 / bayer8), `levels` (1-bit .. N), `palette`, `pixelSize`.

## Stacking recipes

- Dither on top of `glowing-wave` = `dither-waves`. Dither over `mesh-gradient` = retro pixel-poster.
- Dither over a photo at a 2-color brand palette = on-brand 1-bit portrait.

## Common mistakes (avoid these)

- Animating the threshold matrix (crawling ants) - freeze it.
- pixelSize 1 (invisible at retina DPR) - clamp >= 2 device px.
- Dithering a full-color image to 1-bit (mud) - posterize to a small palette first.

## Pairs with (prototype slugs)

- `aesthetic-8-bit-generic`
- `style-pixel-bitmap`
- `aesthetic-cassette-futurism`
- `aesthetic-monochrome-pop-poster`
