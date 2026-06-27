---
shaderId: slice-shift
name: Slice Shift (angled bands sheared apart)
family: filter
category: image-effect
subCategory: distortion
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-acid-graphics, aesthetic-vaporwave, style-bold-display]
notForUseWhen: calm restrained brands, precise diagrams
---

# Slice Shift (angled bands sheared apart)

Slice the layer beneath into angled bands and shift them apart along the slice axis - a clean shear / datamosh / venetian-blind displacement. The Figma `Slice shift` effect. Glitch with geometry instead of noise.

## Stack contract

- **Role:** FILTER - shears a SOURCE beneath into offset bands.
- **Layer:** top.
- **Default blend when stacked:** `normal`, or `screen` for a light-leak between slices.
- **Animated:** yes - band offsets can jitter (glitch) or travel (shutter wipe); pointer can drive shift.
- **Applies to:** the flattened layers below.

## Implementation strategies

```yaml
webgl: |
  float band = floor(dot(uv, u_axis) * u_count);          // which slice
  float shift = (hash(band)-0.5) * u_amount;               // per-band offset (or sin for shutter)
  vec3 col = texture(u_src, uv + u_axis.yx*vec2(1,-1)*shift).rgb;
engine: |
  Figma effect: `Slice shift`. DOM material twins: material `datamosh-compression-smear`, `rgb-channel-split`.
canvas2d: drawImage band-by-band with per-band dx offset (exact + cheap).
```

## Parameters (knobs)

- `axis` (angle of the slices), `count` (band count), `amount` (max shift), `mode` (random-glitch / shutter-travel / pointer), `gap` (light between bands).

## Stacking recipes

- Slice Shift (random, fast) on a headline = a cyberpunk glitch flash on hover.
- Slice Shift (shutter-travel) as a scene transition = bands wipe the next view in.

## Common mistakes (avoid these)

- Re-randomizing every frame at full strength (epileptic strobe) - throttle + honour reduced-motion.
- Bands so thin they alias - keep count moderate.
- Shifting across the slice axis instead of along it (smears, not shears) - offset parallel to the cut.

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`
- `aesthetic-vaporwave`
- `style-bold-display`
