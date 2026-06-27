---
shaderId: neuro-noise
name: Neuro Noise (organic marbled / neural fold field)
family: source
category: generative-fill
subCategory: noise
role: background
defaultBlend: overlay
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [recipe-ai-foundry-dark, aesthetic-bioluminescent-deep, aesthetic-dark-botanical-maximalism]
notForUseWhen: hard-edged brutalist, flat poster
---

# Neuro Noise (organic marbled / neural fold field)

Layered domain-warped fbm folded into organic ridges - the marbled, brain-coral, liquid-walnut texture that paper-design's `neuroNoise` made ubiquitous on AI landing pages. Slow, premium, alive, never repeating.

## Stack contract

- **Role:** SOURCE (pure procedural field).
- **Layer:** background / full-bleed base.
- **Default blend when stacked:** `overlay` / `soft-light` over a brand base, or `normal` as the base itself.
- **Animated:** yes - the warp evolves slowly (very low speed - it should feel like breathing, not flowing).
- **Stacks under:** `particle-web`, `godrays`, `magnetic-field` as the organic substrate.

## Implementation strategies

```yaml
webgl: |
  vec2 q = uv;
  for (int i=0;i<3;i++) q += 0.4*vec2(fbm(q+u_time*0.02), fbm(q.yx+3.1));
  float n = fbm(q*2.0);
  float ridge = abs(2.0*fract(n*u_folds)-1.0);   // fold into ridges
  vec3 col = mix(u_c1, u_c2, smoothstep(0.2,0.8,ridge));
engine: |
  paper-design/shaders: `neuroNoise`, `simplexNoise`, `perlinNoise`. mm-composer: `Noise` effect.
canvas2d: precompute to an offscreen texture (fbm is expensive per-pixel on CPU).
css/svg: feTurbulence(type=fractalNoise) is a static DOM cousin.
```

## Parameters (knobs)

- `colorA` / `colorB` (brand duotone), `scale`, `warpDepth`, `folds`, `speed`, `contrast`.

## Stacking recipes

- Neuro Noise (base) + `godrays` (screen) = a lit organic cavern - bioluminescent-deep hero.
- Tint to two near-black brand grays for a restrained, expensive AI-foundry backdrop.

## Common mistakes (avoid these)

- High speed (it churns and looks cheap) - AI-landing neuro noise is nearly still.
- Full-saturation two-color ramp (garish) - keep low chroma for the premium read.
- One fbm octave (flat) - the domain-warp folds are what make it organic.

## Pairs with (prototype slugs)

- `recipe-ai-foundry-dark`
- `aesthetic-bioluminescent-deep`
- `aesthetic-dark-botanical-maximalism`
