---
shaderId: pattern-grid
name: Pattern Grid (geometric repeat fill)
family: source
category: generative-fill
subCategory: screen-pattern
role: background
defaultBlend: normal
animated: no
needsSource: no
stackable: yes
pairsPrototypes: [recipe-swiss-grid, aesthetic-bauhaus, aesthetic-monochrome-tech-editorial, aesthetic-constructivism]
notForUseWhen: organic hand-drawn vibes, photoreal
---

# Pattern Grid (geometric repeat fill)

A tiled geometric pattern fill - dots, crosses, chevrons, custom shapes - with adjustable shape, size and spacing. The Figma `Pattern grid` fill. The quiet structural texture under Swiss / Bauhaus / blueprint layouts.

## Stack contract

- **Role:** SOURCE (repeat-tile pattern).
- **Layer:** background structural texture.
- **Default blend when stacked:** `normal`, or `multiply` at low opacity as a substrate grid.
- **Animated:** optional (usually static - structure should hold; can scroll subtly).
- **Stacks under:** any content; **with:** `moire-interference` (two grids beat).

## Implementation strategies

```yaml
webgl: |
  vec2 c = fract(uv*u_cells) - 0.5;
  float shape = step(length(c), u_dotR);          // dot; swap sdf for cross/chevron/plus
  vec3 col = mix(u_bg, u_mark, shape);
engine: |
  Figma fill: `Pattern grid`. paper-design/shaders: `dotGrid`.
svg: <pattern> with the unit shape - the canonical DOM pattern fill (crisp, cheap, scalable).
css: radial-gradient/background tiling for dots; limited for complex shapes.
```

## Parameters (knobs)

- `shape` (dot / cross / plus / chevron / custom sdf), `cellSize`, `markSize`, `markColor`, `bgColor`, `rotation`.

## Stacking recipes

- Pattern Grid (multiply 8%) under a Swiss layout = the quiet engineering substrate.
- Two Pattern Grids at slightly different cell sizes = `moire-interference`.

## Common mistakes (avoid these)

- Cell size that doesn't divide the viewport (half-marks at edges) - snap to integer cells or bleed.
- Marks too large (reads as content, not texture) - keep it quiet under real content.
- For complex shapes, prefer SVG <pattern> over a per-pixel sdf (sharper, cheaper).

## Pairs with (prototype slugs)

- `recipe-swiss-grid`
- `aesthetic-bauhaus`
- `aesthetic-monochrome-tech-editorial`
- `aesthetic-constructivism`
