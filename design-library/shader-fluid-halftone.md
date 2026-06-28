---
shaderId: fluid-halftone
name: Fluid Halftone (advected ink re-screened as dots)
family: source
category: generative-fill
subCategory: halftone
role: background
defaultBlend: multiply
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-acid-graphics, aesthetic-y2k-memphis-loud, recipe-editorial-magazine, aesthetic-vaporwave]
notForUseWhen: minimal corporate, dense data UI
images:
  - src: shader-fluid-halftone.png
    reason: Fluid Halftone (advected ink re-screened as dots) - shader fill preview.
---

# Fluid Halftone (advected ink re-screened as dots)

A slow curl-noise fluid field (ink swirling in water) sampled through a rotated halftone dot grid, so the flowing density resolves into CMYK-style print dots that grow and shrink as the fluid moves. Print-press texture that is alive.

## Stack contract

- **Role:** SOURCE (self-generating fluid field). Can also run as a FILTER re-screening a layer beneath (set `sampleSource: true`).
- **Layer:** background, or mid-layer texture.
- **Default blend when stacked:** `multiply` (ink on paper) over a warm paper base; `screen` for glow-ink.
- **Animated:** yes - curl-noise advection on `u_time`.
- **Stacks over:** a paper/grain base; **under:** `riso-print` registration shift for a double-screen zine look.

## Implementation strategies

```yaml
webgl: |
  float d = fbm(uv*3.0 + curl(uv, u_time));     // fluid density 0..1
  // halftone: rotate grid, compare cell distance to density radius
  vec2 g = rotate2d(0.26) * uv * u_cells;       // ~15deg screen angle
  vec2 c = fract(g) - 0.5;
  float dot = step(length(c), d*0.7);
  vec3 col = mix(u_paper, u_ink, dot);
engine: |
  mm-composer `fluid` effect as the field + a halftone screen pass.
  paper-design/shaders: `water` / `warp` as the field. Figma gallery: `Fluid halftone`.
canvas2d: offscreen fluid -> sample on a dot grid, fillRect per dot.
css/svg: SVG <pattern> dots can FAKE a static halftone but not the fluid motion.
```

## Parameters (knobs)

- `screenAngle` (per channel for CMYK), `cellSize`, `inkColors` (1-4), `flowSpeed`, `viscosity`, `paperTint`.

## Stacking recipes

- Fluid Halftone (multiply) over a flat brand color = animated risograph background for an editorial hero.
- Three stacked passes at 15/75/0 degree screen angles in C/M/K = true 4-color-print shimmer.

## Common mistakes (avoid these)

- One screen angle for all inks (moire clash) - offset each channel 30 degrees.
- Dots too small (reads as noise) or too big (reads as polka dots) - tune cellSize to ~8-16px.
- Animating dot positions instead of dot SIZE - the grid must stay locked; only radius breathes.

## Pairs with (prototype slugs)

- `aesthetic-acid-graphics`
- `aesthetic-y2k-memphis-loud`
- `recipe-editorial-magazine`
- `aesthetic-vaporwave`
