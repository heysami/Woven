---
shaderId: luminance-particles
name: Luminance Particles (image dissolves into glowing motes)
family: filter
category: image-effect
subCategory: particle
role: overlay
defaultBlend: add
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-cosmic-horizon, aesthetic-bioluminescent-deep]
notForUseWhen: crisp product shots that must stay legible
---

# Luminance Particles (image dissolves into glowing motes)

An image or text layer sampled into a particle field, where each particle's brightness, size and drift come from the underlying luminance - bright areas bloom into dense glowing motes, dark areas fall to dust. The picture re-assembles out of light.

## Stack contract

- **Role:** FILTER - needs a SOURCE beneath (image / text / video) to sample.
- **Layer:** overlay directly above its source; the source is usually hidden and the particles ARE the render.
- **Default blend when stacked:** `add` / `screen` (motes are light).
- **Animated:** yes - particles drift, twinkle, and ease back toward their luminance home.
- **Stacks over:** any raster; **under:** `godrays` for a volumetric finish.

## Implementation strategies

```yaml
webgl: |
  // sample source texture at each particle's home uv
  float lum = dot(texture(u_src, home).rgb, vec3(0.299,0.587,0.114));
  // size/alpha scale with lum; idle drift + spring back to home*lum
  gl_PointSize = mix(0.0, u_maxSize, lum);
engine: |
  paper-design/shaders `dotGrid` reading an image. Figma gallery: `Luminance particles`.
  mm-composer: particle effect with an image input (eff.inputs).
canvas2d: sample getImageData on a grid; emit a particle per bright cell.
css/svg: not appropriate.
```

## Parameters (knobs)

- `density` (sample grid), `lumThreshold` (darkness that drops to zero), `maxSize`, `drift`, `twinkle`,
  `moteColor` (or sample from source), `settleSpring`.

## Stacking recipes

- Luminance Particles over a logo (source hidden) = the mark forms out of embers - hero reveal on scroll.
- Add `godrays` keyed to the brightest cluster = the motes cast light.

## Common mistakes (avoid these)

- Sampling every pixel (millions of particles, dead GPU) - sample on a grid, 1 particle per cell.
- No settle spring (the image never reads) - particles must home toward their luminance position.
- moteColor pure white on a bright source (blows out) - tint and clamp additive bloom.

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-cosmic-horizon`
- `aesthetic-bioluminescent-deep`
