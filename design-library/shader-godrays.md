---
shaderId: godrays
name: Godrays (volumetric light shafts from a source)
family: source
category: generative-fill
subCategory: light
role: overlay
defaultBlend: add
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-cosmic-horizon, aesthetic-bioluminescent-deep, aesthetic-solarpunk]
notForUseWhen: flat utilitarian UI, bright airy brands
---

# Godrays (volumetric light shafts from a source)

Volumetric light shafts (crepuscular rays) streaming from one origin point through unseen haze - the radial bloom that makes a dark scene feel lit from within. paper-design's `godRays`: light as a material.

## Stack contract

- **Role:** SOURCE (radial light field) - usually an OVERLAY that adds light to a scene below.
- **Layer:** overlay, high in the stack (light is in front of the haze).
- **Default blend when stacked:** `add` / `screen` (pure light, never darkens).
- **Animated:** yes - rays shimmer and the origin can drift; dust motes optional.
- **Stacks over:** `neuro-noise`, `dither-waves`, any dark base; **pairs with:** `luminance-particles` (motes catch the light).

## Implementation strategies

```yaml
webgl: |
  vec2 d = uv - u_origin;
  float a = atan(d.y, d.x);
  float rays = 0.5 + 0.5*sin(a*u_count + u_time*0.3);    // angular shafts
  rays *= fbm(vec2(a*3.0, u_time*0.1));                  // break with noise
  float fall = smoothstep(1.0, 0.0, length(d));          // radial falloff
  vec3 col = u_lightColor * rays * fall * u_intensity;
engine: |
  paper-design/shaders: `godRays`. mm-composer: radial light custom effect.
css: |
  conic-gradient + radial-gradient mask + blur can FAKE static shafts (cheap, no shimmer).
svg: feGaussianBlur'd radial spokes; static only.
```

## Parameters (knobs)

- `origin` (corner / pointer), `count` (shaft density), `intensity`, `lightColor`, `shimmerSpeed`, `falloff`, `dustMotes` (on/off).

## Stacking recipes

- Godrays (add) over `neuro-noise` = cathedral light through organic haze.
- Origin bound to pointer = the user carries the light source - interactive hero.

## Common mistakes (avoid these)

- `normal` blend (godrays must ADD light, never composite over) - always additive.
- Shafts too uniform (reads as a sunburst sticker) - break the angular function with noise.
- Light on an already-bright base (no contrast, no drama) - godrays need a dark field to read.

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-cosmic-horizon`
- `aesthetic-bioluminescent-deep`
- `aesthetic-solarpunk`
