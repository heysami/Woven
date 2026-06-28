---
shaderId: dither-waves
name: Dither Waves (luminous wave bands, error-diffusion screen)
family: source
category: generative-fill
subCategory: screen-pattern
role: background
defaultBlend: screen
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-cassette-futurism, recipe-ai-foundry-dark, aesthetic-y2k-futurism]
notForUseWhen: flat clean SaaS, photographic hero
images:
  - src: shader-dither-waves.png
    reason: Dither Waves (luminous wave bands, error-diffusion screen) - shader fill preview.
---

# Dither Waves (luminous wave bands, error-diffusion screen)

Smooth luminous sine-bands of light advected across the frame, then quantized through an ordered (Bayer) or error-diffusion (Floyd-Steinberg / Atkinson) dither so the gradient breaks into a living grid of 1-bit / 2-bit pixels. The Figma `Glowing wave` fill run through the `Dither` effect - retro-CRT light that never bands.

## Stack contract

- **Role:** SOURCE (generates its own field; no layer needed beneath).
- **Layer:** background / full-bleed base.
- **Default blend when stacked:** `screen` or `add` over a near-black field.
- **Animated:** yes - bands phase-scroll on `u_time`; dither matrix is static (dither must NOT crawl or it shimmers).
- **Stacks under:** `particle-web`, `godrays`, `color-outline` (as the glowing substrate).

## Implementation strategies

```yaml
webgl: |
  // band field
  float w = 0.5 + 0.5*sin(uv.y*8.0 + uv.x*2.0 + u_time*0.6);
  w *= smoothstep(0.0,0.3,uv.y)*smoothstep(1.0,0.7,uv.y);
  // 4x4 Bayer ordered dither (threshold map)
  float bayer = bayer4x4(gl_FragCoord.xy);     // 0..1
  float bit = step(bayer, w);                   // 1-bit quantize
  vec3 col = mix(u_bg, u_glow, bit);
engine: |
  mm-composer `wave` effect as the source pass + a dither post pass.
  paper-design/shaders: `dithering`. Figma: `Glowing wave` fill + `Dither` effect stacked.
canvas2d: ImageData loop with Floyd-Steinberg error diffusion (cheaper, no GL).
css/svg: not appropriate - dithering needs per-pixel quantization.
```

## Parameters (knobs)

- `palette` (1-bit mono / 2-bit / brand duotone), `ditherAlgo` (bayer4 / bayer8 / floyd / atkinson),
  `pixelSize` (dot scale), `waveSpeed`, `bandFrequency`, `glowColor`.

## Stacking recipes

- Dither Waves (base, screen) + `magnetic-field` (mid, add) = animated synthwave control-room backdrop.
- Quantize to a 2-color brand palette to keep it on-brand instead of generic CRT green.

## Common mistakes (avoid these)

- Animating the dither threshold matrix (causes a crawling-ant shimmer) - phase the WAVE, freeze the matrix.
- pixelSize=1 (the dither is invisible at retina DPR - clamp to >=2 device px).
- Full RGB gradient dithered to 1-bit (mud) - dither a 2-3 stop ramp.

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `recipe-ai-foundry-dark`
- `aesthetic-y2k-futurism`
