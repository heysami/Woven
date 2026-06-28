---
shaderId: halftone
name: Halftone (vintage print / comic dot screen)
family: filter
category: image-effect
subCategory: halftone
role: overlay
defaultBlend: multiply
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [recipe-editorial-magazine, aesthetic-y2k-memphis-loud, aesthetic-anti-design, aesthetic-monochrome-pop-poster]
notForUseWhen: smooth gradient hero, photoreal product
images:
  - src: shader-halftone.png
    reason: Halftone (vintage print / comic dot screen) - shader fill preview.
---

# Halftone (vintage print / comic dot screen)

Re-screen the layer beneath as vintage print / comic-book halftone - a rotated grid of dots whose size tracks luminance, with controls for color separation and dot size. The Figma `Halftone` effect: the static filter twin of `fluid-halftone`.

## Stack contract

- **Role:** FILTER - re-screens a SOURCE beneath (image / illustration).
- **Layer:** top print pass.
- **Default blend when stacked:** `multiply` (ink dots on paper), or `normal` for mono.
- **Animated:** NO (the dot grid is locked; only dot RADIUS tracks the static source). Animate the source if motion is wanted.
- **Applies to:** the layer below; strongest on simple high-contrast subjects.

## Implementation strategies

```yaml
webgl: |
  float l = luma(texture(u_src, uv).rgb);
  vec2 g = rotate2d(u_angle) * gl_FragCoord.xy / u_cell;
  float d = length(fract(g)-0.5);
  float dot = step(d, (1.0-l)*0.7);               // bigger dot in darker areas
  vec3 col = mix(u_paper, u_ink, dot);
engine: |
  Figma effect: `Halftone`. Sibling fluid source in this lib: `fluid-halftone`.
  DOM material twins: material `halftone`, illust `halftone-shape`.
svg: <pattern> of radial dots + feColorMatrix per channel; static.
css: radial-gradient dot tiles (static, mono).
```

## Parameters (knobs)

- `cellSize`, `screenAngle` (per channel for CMYK separation), `inkColors`, `paperTint`, `dotShape` (round / square / line).

## Stacking recipes

- Halftone over `gradient-map` (duotone) = a classic 2-color comic print.
- Three Halftone passes at 15/75/0 degrees in C/M/K = full-color newsprint.

## Common mistakes (avoid these)

- One angle for all channels (moire clash) - 30 degree offsets per ink.
- Cell too small (reads as grain) or too big (polka dots) - 6-14px.
- Animating dot position instead of radius - the grid stays locked.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-anti-design`
- `aesthetic-monochrome-pop-poster`
