---
shaderId: magnetic-field
name: Magnetic Field (curl flow-field streamlines)
family: source
category: generative-fill
subCategory: flow-field
role: background
defaultBlend: add
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-depin-hardware, recipe-scientific-infra-marketing, aesthetic-blueprint-hologram, aesthetic-cosmic-horizon]
notForUseWhen: playful kids brands, dense text UI
images:
  - src: shader-magnetic-field.png
    reason: Magnetic Field (curl flow-field streamlines) - shader fill preview.
---

# Magnetic Field (curl flow-field streamlines)

Thousands of short filaments tracing a curl-noise vector field, bending around invisible poles like iron filings over a magnet - slow, scientific, hypnotic. Field lines that flow and re-form as the poles drift.

## Stack contract

- **Role:** SOURCE (vector field rendered as streamlines or advected particles).
- **Layer:** background.
- **Default blend when stacked:** `add` / `screen` (filaments glow on dark).
- **Animated:** yes - poles orbit slowly; filaments are short-lived particles re-seeded each cycle.
- **Stacks under:** `particle-web` (shared field), `godrays`; **over:** a deep-space gradient.

## Implementation strategies

```yaml
webgl: |
  // curl noise gives a divergence-free field -> filaments never bunch unnaturally
  vec2 v = curlNoise(p*scale + u_time*0.05);
  // advect a particle along v for K steps, draw the trail with fading alpha
canvas2d: |
  // seed P particles; each frame step along curlNoise; draw faded trail; respawn on age.
engine: |
  paper-design/shaders: `neuroNoise` (field) + custom advection. Figma gallery: `Magnetic field`.
  mm-composer: a custom-stateful particle effect reading a noise field.
css/svg: not appropriate.
```

## Parameters (knobs)

- `poles` (count + polarity), `lineDensity`, `fieldScale`, `flowSpeed`, `lineColor`, `trailLength`.

## Stacking recipes

- Magnetic Field (add) + a faint `dither-waves` base = a blueprint-hologram instrument panel.
- Two opposing poles drifting in a slow Lissajous = the field continually inverts; mesmerizing for a long-scroll hero.

## Common mistakes (avoid these)

- Plain Perlin instead of CURL noise (filaments bunch into sources/sinks) - use curl for clean flow.
- Trails too long (smears to soup) - keep filaments short and re-seeded.
- Field scale too high (turbulent noise, no readable poles) - low frequency = legible magnetic shape.

## Pairs with (prototype slugs)

- `aesthetic-depin-hardware`
- `recipe-scientific-infra-marketing`
- `aesthetic-blueprint-hologram`
- `aesthetic-cosmic-horizon`
