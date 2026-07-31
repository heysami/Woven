---
materialId: led-segment-display
name: LED Segment Display (lit segments over ghost cells)
family: hybrid
category: display
surfaceFinish: matte black polymer chassis with emissive segments
scope: object
transparency: opaque chassis; segments emit through a smoked window
pairsPrototypes: [aesthetic-cassette-futurism, aesthetic-rgb-gamer, style-dense-mono-dark, shell-terminal-frame, recipe-terminal-on-web]
images:
  - src: material-led-segment-display.png
    reason: Material fidelity sample.
---

# LED Segment Display (lit segments over ghost cells)

Segmented LED typography as hardware: seven- and fourteen-segment digits glow red, amber, or green with soft bloom, while the UNLIT segments stay faintly visible as ghost cells on a matte black polymer chassis.

## Physical behavior

**Surface finish**: matte fine-textured black polymer; satin metal and perforated mesh as secondary hardware

**Transparency**: opaque; the segment window is a smoked layer the ghosts sit behind

**Reacts to light**: no - it emits; chassis swallows ambient light

**Deforms**: no

**Age / wear**: a dead segment or uneven brightness reads as honest age (use sparingly)

## Implementation strategies

```yaml
css: |
  --led-red: #ff2020; --led-amber: #ffb000; --led-green: #39ff14;
  --ghost: #1a1a1a; --chassis: #080808;
  /* every digit renders TWO layers: full 8888 ghost underneath, value on top */
  .cell { position: relative; }
  .cell .ghost { color: var(--ghost); }
  .cell .lit { position: absolute; inset: 0; color: var(--led-red);
    text-shadow: 0 0 6px rgba(255,32,32,0.9), 0 0 18px rgba(255,32,32,0.45); }
typography: |
  a true segment face (DSEG or SVG segment cells) - every glyph must decompose
  into the same segment skeleton; letters allowed only in 14-segment form
svg: |
  segment cells as polygons with mitered "hourglass" ends and 1px gaps at joints;
  lit = fill + gaussian bloom, unlit = ghost fill, no bloom
color: |
  bloom always carries the LED hue - red blooms red; semantic split is canonical:
  red = primary/time, amber = caution/money, green = positive/score
```

## Reactive behaviors

**Light**: no ambient response; brightness is state

**Highlight**: hover/active raises emission - stronger bloom, slight over-glow onto the chassis; disabled = ghost only

**Depth**: bezel-inset displays (inner shadow around the window); segments themselves are flat

**Parallax**: none; motion is segment-truthful (digits change by re-lighting segments, optionally with a 40-80ms decay)

## Common implementation mistakes (avoid these)

- omitting the unlit ghost cells (the faint 8888 skeleton behind every value is THE fingerprint of the material)
- white or hueless bloom (bloom is the LED color; white glow reads as OLED, not LED)
- generic "digital" fonts without segment logic (every glyph must be buildable from the same segment set)
- lighting the chassis (the polymer stays matte black; only segments and their bloom emit)
- anti-aliased rounded glyphs (segments have mitered ends and hard gaps between them)
- rainbow palettes (a device speaks at most three LED colors, each with a fixed meaning)

## Examples in the wild

- alarm clocks, microwaves, VCR front panels
- gas-station price signs and scoreboards
- rack gear and multimeter front panels

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-rgb-gamer`
- `style-dense-mono-dark`
- `shell-terminal-frame`
- `recipe-terminal-on-web`

## Differentiation

- vs `material-crt-phosphor`: CRT is a raster tube - scanlines, curvature, subpixel triads, whole-frame glow; LED segments are discrete lit shapes with per-cell ghosts on a flat matte chassis, no scan structure at all

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
