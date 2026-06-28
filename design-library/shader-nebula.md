---
shaderId: nebula
name: Nebula (deep-space colored gas + stars)
family: source
category: generative-fill
subCategory: light
role: background
defaultBlend: screen
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-cosmic-horizon, aesthetic-bioluminescent-deep, aesthetic-luxury-cinematic-dark, aesthetic-defi-cosmic]
notForUseWhen: bright airy brands, flat utilitarian UI
images:
  - src: shader-nebula.png
    reason: Nebula (deep-space colored gas + stars) - shader fill preview.
---

# Nebula (deep-space colored gas + stars)

Deep-space backgrounds - layered colored gas clouds glowing against black with a scatter of stars, customizable colors and density. The Figma `Nebula` fill. Cosmic, premium, infinite.

## Stack contract

- **Role:** SOURCE (gas field + star layer).
- **Layer:** background.
- **Default blend when stacked:** `screen` / `add` (emissive gas on black).
- **Animated:** yes - gas slowly churns; stars twinkle.
- **Stacks under:** `godrays`, `particle-web` (constellations), `lens-distortion`.

## Implementation strategies

```yaml
webgl: |
  float gas = fbm(uv*u_scale + u_time*0.01);
  vec3 col = mix(u_gasA, u_gasB, gas) * pow(gas, u_density);
  // stars: hash-threshold sparkle, twinkle on time
  float star = step(0.998, hash(floor(uv*u_starGrid))) * (0.5+0.5*sin(u_time*3.0+hash2(uv)));
  col += vec3(star);
engine: |
  Figma fill: `Nebula`. paper-design/shaders: layered noise + stars. mm-composer: `Noise` + particle stars.
css/svg: radial-gradients + a star PNG; static only.
```

## Parameters (knobs)

- `gasColors` (2-3), `density`, `churnSpeed`, `starDensity`, `twinkle`, `coreGlow`.

## Stacking recipes

- Nebula + `particle-web` (screen) = a constellation graph over deep space.
- Nebula + `godrays` from a bright gas core = a forming star.

## Common mistakes (avoid these)

- `normal` blend (gas must emit - screen/add on black).
- Full-saturation gas everywhere (no depth) - let it fall to black in the voids.
- Too many stars (snow, not space) - sparse + twinkle.

## Pairs with (prototype slugs)

- `aesthetic-cosmic-horizon`
- `aesthetic-bioluminescent-deep`
- `aesthetic-luxury-cinematic-dark`
- `aesthetic-defi-cosmic`
