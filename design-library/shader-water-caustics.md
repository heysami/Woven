---
shaderId: water-caustics
name: Water Caustics (shimmering refracted light net)
family: source
category: generative-fill
subCategory: light
role: overlay
defaultBlend: add
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-bioluminescent-deep, aesthetic-coastal-grandmother, aesthetic-solarpunk, aesthetic-frutiger-aero]
notForUseWhen: corporate dashboards, hard tech UI
images:
  - src: shader-water-caustics.png
    reason: Water Caustics (shimmering refracted light net) - shader fill preview.
---

# Water Caustics (shimmering refracted light net)

The dancing net of bright veins that refracted sunlight casts on a pool floor - overlapping ridged noise cells that shimmer and drift. The Figma `Water caustics` fill: sunlight underwater.

## Stack contract

- **Role:** SOURCE (caustic light field) - usually an OVERLAY adding rippling light onto a scene.
- **Layer:** overlay over a base color / image (a pool floor, a surface to be lit).
- **Default blend when stacked:** `add` / `overlay` (caustics are light cast onto a surface).
- **Animated:** yes - the cells drift and the ridges pulse on `u_time`.
- **Stacks over:** a teal/sand base or a product shot; **under:** `lens-distortion` for underwater depth.

## Implementation strategies

```yaml
webgl: |
  // ridged voronoi/worley distance -> bright veins where cells meet
  float c = 1.0 - worley(uv*u_scale + flow(uv,u_time));
  c = pow(c, u_sharp);                            // sharpen the veins
  vec3 col = u_lightColor * c * u_intensity;
engine: |
  Figma fill: `Water caustics`. paper-design/shaders: `voronoi` / `water`.
css/svg: feTurbulence + high-contrast feColorMatrix fakes a static caustic; no shimmer.
canvas2d: precompute worley to a texture, scroll + warp (per-pixel worley is slow on CPU).
```

## Parameters (knobs)

- `scale` (cell size), `sharpness` (vein thinness), `flowSpeed`, `lightColor`, `intensity`, `depthTint`.

## Stacking recipes

- Water Caustics (add) over a sandy gradient = a sunlit pool floor.
- Over a product shot with low intensity = "submerged" hero; add `lens-distortion` for the water surface above.

## Common mistakes (avoid these)

- Plain voronoi (cells, not veins) - INVERT and sharpen so only the cell boundaries glow.
- `normal` blend (caustics are cast light, must be additive).
- Too fast (boiling, not lapping) - real caustics drift slowly.

## Pairs with (prototype slugs)

- `aesthetic-bioluminescent-deep`
- `aesthetic-coastal-grandmother`
- `aesthetic-solarpunk`
- `aesthetic-frutiger-aero`
