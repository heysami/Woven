---
shaderId: clouds
name: Clouds (procedural turbulent cloud texture)
family: source
category: generative-fill
subCategory: noise
role: background
defaultBlend: normal
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-solarpunk, aesthetic-coastal-grandmother, aesthetic-frutiger-aero, aesthetic-dreamcore]
notForUseWhen: hard tech UI, dense dashboards
---

# Clouds (procedural turbulent cloud texture)

Soft, billowing procedural clouds with customizable colors and turbulence - the Figma `Clouds` fill. Frutiger-Aero skies, dream-soft backdrops, drifting fog. Domain-warped fbm shaped into puffs with a sky gradient behind.

## Stack contract

- **Role:** SOURCE (sky + cloud field).
- **Layer:** background.
- **Default blend when stacked:** `normal` (it is the sky), or `screen` for mist over a scene.
- **Animated:** yes - clouds drift + slowly reshape on `u_time`.
- **Stacks under:** `godrays` (sun through clouds), `water-caustics`, `lens-distortion`.

## Implementation strategies

```yaml
webgl: |
  float c = fbm(uv*u_scale + vec2(u_time*0.02,0.0));       // drifting fbm
  c = smoothstep(u_cover-0.15, u_cover+0.15, c);            // coverage threshold
  vec3 sky = mix(u_skyLow, u_skyHigh, uv.y);
  vec3 col = mix(sky, u_cloud, c);
engine: |
  Figma fill: `Clouds`. paper-design/shaders: `smokeRing` / fbm. mm-composer: `Noise` shaped.
css/svg: feTurbulence + feColorMatrix fakes a static cloud; no drift.
```

## Parameters (knobs)

- `coverage`, `turbulence` (octaves), `driftSpeed`, `cloudColor`, `skyLow`, `skyHigh`, `softness`.

## Stacking recipes

- Clouds + `godrays` (origin top) = sunbeams breaking through - solarpunk hero.
- Tint clouds pink/lilac + slow drift = dreamcore sky.

## Common mistakes (avoid these)

- Sharp coverage threshold (hard-edged blobs, not clouds) - wide smoothstep for fluffy edges.
- No sky gradient (clouds float in void) - always a graded sky behind.
- Fast drift (reads as smoke, not sky) - very slow.

## Pairs with (prototype slugs)

- `aesthetic-solarpunk`
- `aesthetic-coastal-grandmother`
- `aesthetic-frutiger-aero`
- `aesthetic-dreamcore`
