---
shaderId: fractal-noise
name: Fractal Noise (Perlin / Value / Voronoise procedural fill)
family: source
category: generative-fill
subCategory: noise
role: background
defaultBlend: overlay
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [recipe-ai-foundry-dark, aesthetic-dark-botanical-maximalism, aesthetic-cosmic-horizon, aesthetic-cottagegoth]
notForUseWhen: crisp flat UI, hard-edged poster
---

# Fractal Noise (Perlin / Value / Voronoise procedural fill)

The raw procedural noise fill - Perlin, Value, or Voronoise fbm - the Figma `Fractal noise` fill and the substrate under half the effects in this library. Clouds, smoke, organic grain, and the displacement source other shaders sample.

## Stack contract

- **Role:** SOURCE (the canonical procedural texture).
- **Layer:** background base, or a mid-layer texture / displacement source.
- **Default blend when stacked:** `overlay` / `soft-light` as texture; `normal` as a base.
- **Animated:** yes - the noise field evolves slowly on `u_time` (a 3rd noise dimension).
- **Stacks under:** almost anything (it is the generic ground); feeds `organic-distortion` as a displacement map.

## Implementation strategies

```yaml
webgl: |
  float n = 0.0, a = 0.5; vec2 p = uv*u_scale;
  for (int i=0;i<OCTAVES;i++){ n += a*noise(p + u_time*0.05); p*=2.0; a*=0.5; }
  vec3 col = mix(u_c1, u_c2, n);        // type: perlin | value | voronoise
engine: |
  Figma fill: `Fractal noise` (Perlin / Value / Voronoise). paper-design/shaders: `perlinNoise` / `simplexNoise`.
  mm-composer: `Noise` effect. Sibling organic variant in this lib: `neuro-noise` (domain-warped).
svg: feTurbulence(type=fractalNoise|turbulence) is the DOM twin (static).
```

## Parameters (knobs)

- `noiseType` (perlin / value / voronoise), `octaves`, `scale`, `evolveSpeed`, `colorA`, `colorB`, `contrast`.

## Stacking recipes

- Fractal Noise (overlay, 6%) over any flat fill = the anti-banding grain every gradient needs.
- Fractal Noise as the displacement input to `organic-distortion` = organic liquid warp.

## Common mistakes (avoid these)

- One octave (looks like blurry blobs) - stack 4-6 for fractal detail.
- High evolve speed (boiling TV static) - keep it a slow drift.
- Forgetting it is the cheap fix for gradient banding (overlay at low opacity).

## Pairs with (prototype slugs)

- `recipe-ai-foundry-dark`
- `aesthetic-dark-botanical-maximalism`
- `aesthetic-cosmic-horizon`
- `aesthetic-cottagegoth`
