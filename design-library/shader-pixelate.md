---
shaderId: pixelate
name: Pixelate (mosaic + tile-scatter)
family: filter
category: image-effect
subCategory: screen-pattern
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-8-bit-generic, aesthetic-vaporwave, aesthetic-cyberpunk, style-pixel-bitmap]
notForUseWhen: high-detail product shots, fine type
---

# Pixelate (mosaic + tile-scatter)

Quantize the layer beneath into chunky tiles - square mosaic, or scatter the tiles into displaced shapes for a shattering / censor / loading-in effect. The Figma `Pixelate` effect.

## Stack contract

- **Role:** FILTER - blocks a SOURCE beneath into tiles.
- **Layer:** top.
- **Default blend when stacked:** `normal`.
- **Animated:** yes - tile size can grow/shrink (resolve-in / dissolve-out); scatter can animate.
- **Applies to:** the flattened layers below.

## Implementation strategies

```yaml
webgl: |
  vec2 cell = floor(uv*u_cells)/u_cells + 0.5/u_cells;   // snap to cell center
  vec2 jit = u_scatter * (hash2(floor(uv*u_cells))-0.5); // optional scatter
  vec3 col = texture(u_src, cell + jit).rgb;
engine: |
  Figma effect: `Pixelate`. DOM material twin: material `pixel`.
css: image-rendering: pixelated on a downscaled copy (cheap mosaic, no scatter).
```

## Parameters (knobs)

- `cellSize`, `shape` (square / circle / triangle tiles), `scatter` (displacement amount), `animateMode` (none / resolve-in / dissolve-out).

## Stacking recipes

- Pixelate animating cellSize large->1 on scroll = a hero that resolves into focus.
- Pixelate + scatter + `gradient-map` = a glitchy datamosh censor block.

## Common mistakes (avoid these)

- Sampling the corner instead of the cell CENTER (the mosaic looks offset/sheared).
- Cell size in CSS px ignored at DPR (tiles double on retina) - compute in device px.
- Scatter so high it is unreadable when it should resolve - ease scatter to zero at the end.

## Pairs with (prototype slugs)

- `aesthetic-8-bit-generic`
- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `style-pixel-bitmap`
