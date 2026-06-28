---
shaderId: particle-web
name: Particle Web (proximity-linked constellation field)
family: source
category: generative-fill
subCategory: particle
role: background
defaultBlend: screen
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [recipe-ai-foundry-dark, aesthetic-crypto-degen, recipe-devtools-marketing, aesthetic-cyberpunk]
notForUseWhen: warm editorial, hand-drawn / organic vibes
images:
  - src: shader-particle-web.png
    reason: Particle Web (proximity-linked constellation field) - shader fill preview.
---

# Particle Web (proximity-linked constellation field)

A drifting field of points that draw connecting lines to their near neighbours, the web thickening where points cluster and snapping as they part - the canonical tech-hero 'network' backdrop, but as a real GPU/2D particle sim rather than a static SVG.

## Stack contract

- **Role:** SOURCE (point field). Optionally pointer-reactive (nodes flee / attract to cursor).
- **Layer:** overlay on a dark base, OR background.
- **Default blend when stacked:** `screen` / `add` (lines glow).
- **Animated:** yes - Brownian / flow-field drift; lines recomputed per frame by distance threshold.
- **Stacks over:** `neuro-noise` or `dither-waves` as the glowing graph layer.

## Implementation strategies

```yaml
webgl: |
  // GPU instanced points; lines via a spatial-hash neighbour pass.
  // line alpha = 1.0 - dist / linkRadius  (fade with distance)
canvas2d: |
  // N points {x,y,vx,vy}; O(n^2) or grid-bucketed neighbour test.
  for each pair within linkRadius: ctx.globalAlpha = 1-d/r; lineTo.
engine: |
  mm-composer `particles` effect. paper-design/shaders: `dotOrbit` (orbital variant).
  Figma gallery: `Particle web`.
css/svg: not appropriate (needs per-frame neighbour graph).
```

## Parameters (knobs)

- `count`, `linkRadius`, `driftSpeed`, `nodeColor`, `lineColor`, `pointerForce` (attract/repel/off), `lineWidth`.

## Stacking recipes

- Particle Web (screen) over `magnetic-field` = nodes that ride the flow lines (share the same vector field).
- Tint nodes to the brand accent, lines to 12% white = restrained AI-foundry backdrop.

## Common mistakes (avoid these)

- count too high - the web turns into a solid mesh (cap ~120 nodes; thin lines).
- O(n^2) at high count on the CPU (jank) - bucket into a grid.
- Pointer force so strong it looks gimmicky - keep it a gentle lean, not a magnet.

## Pairs with (prototype slugs)

- `recipe-ai-foundry-dark`
- `aesthetic-crypto-degen`
- `recipe-devtools-marketing`
- `aesthetic-cyberpunk`
