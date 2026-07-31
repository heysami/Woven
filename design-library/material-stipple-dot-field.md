---
materialId: stipple-dot-field
name: Stipple Dot Field (variable-density ink dots as the medium)
family: analog
category: print
surfaceFinish: matte (crisp ink dots on warm paper)
scope: medium
transparency: opaque per dot; fields read lighter or heavier by density
pairsPrototypes: [style-cream-humanist, style-serif-warm-paper, aesthetic-craft-sketchbook, style-doodle, aesthetic-organic-overgrowth]
images:
  - src: material-stipple-dot-field.png
    reason: Material fidelity sample.
---

# Stipple Dot Field (variable-density ink dots as the medium)

Pointillist print-register where the dot is the only mark: letterforms, borders, fills, and flow-lines are all built from fields of crisp ink dots whose DENSITY carries weight, tone, and emphasis on warm paper.

## Physical behavior

**Surface finish**: matte; each dot is crisp-edged ink sitting on cream paper tooth

**Transparency**: dots are opaque; apparent tone is purely spatial density

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless; at most a slight ink-spread softening on heavy fields

## Implementation strategies

```yaml
css: |
  --paper: #f4f1ea; --ink-rust: #8b3a2c; --ink-teal: #18b7c6; --ink-ridge: #2a1e1b;
  body { background: var(--paper); }
  /* dotted borders are honest CSS, but vary the register */
  .chip { border: 2px dotted var(--ink-rust); border-radius: 999px; }
svg: |
  letterforms: use the glyph as a <clipPath> over a dot field whose density
  is driven by a gradient mask - sparse at "light" weight, packed at "heavy";
  dots jitter position (+-30% cell) and radius (+-25%) so no grid shows
  flow-lines: rows of dots following a sine path, density pulsing along travel
canvas: |
  stipple renderer: sample source luminance, place dots via poisson-disc with
  radius/spacing mapped to darkness; single ink color per pass
webgl: |
  shader variant only for animated fields (pattern travel, density breathing);
  keep dots round, crisp, unblurred
raster: none needed - the medium is fully procedural
```

## Reactive behaviors

**Light**: no

**Highlight**: emphasis = density - active elements pack their dots tighter and may swap ink (rust to teal); nothing glows

**Depth**: no; hierarchy is density plus ink color

**Parallax**: dot fields can TRAVEL - patterns migrate slowly across a surface like tide marks, one dot-row at a time

## Common implementation mistakes (avoid these)

- a uniform mechanical grid of dots (stipple density varies organically; jitter every dot or it becomes a halftone screen)
- blur or glow on dots (dots are crisp ink on paper - softness kills the print register)
- pure black ink on pure white (the register is warm: rust, sepia, teal inks on cream paper)
- outlining letterforms with a stroke and sprinkling dots inside (the dots ARE the letterform; no continuous outline anywhere)
- tone via opacity (lighter passages use FEWER dots, never faded ones)

## Examples in the wild

- pointillist and stipple scientific illustration
- cephalopod-skin and reaction-diffusion pattern studies
- hand-stippled editorial lettering and map shading

## Pairs with (prototype slugs)

- `style-cream-humanist`
- `style-serif-warm-paper`
- `aesthetic-craft-sketchbook`
- `style-doodle`
- `aesthetic-organic-overgrowth`

## Differentiation

- vs `material-halftone-cmyk`: halftone is a mechanical screen - fixed angles, rosettes, dot-size modulation in four process inks; stipple is organic single-ink dot PLACEMENT, jittered and hand-dense, no screen angle anywhere
- vs `shader-luminance-particles`: those are emissive screen-space glow particles; stipple is matte ink on warm paper - zero glow, zero motion blur

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
