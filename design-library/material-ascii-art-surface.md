---
materialId: ascii-art-surface
name: ASCII Art Surface (text-as-pixel)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-terminal-mono, recipe-terminal-on-web, aesthetic-web-brutalism]
images:
  - src: material-ascii-art-surface.png
    reason: Material fidelity sample.
---

# ASCII Art Surface (text-as-pixel)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  font-family: ui-monospace, 'IBM Plex Mono';
  line-height: 1;
  letter-spacing: 0;
  white-space: pre;
webgl: |
  Codrops "Efecto" — quantize image luminance to an ASCII charset, render
  to a font-grid canvas. Charset density carries luminance.
raster: pre-rendered ASCII PNG for static content
```

## Reactive behaviors

**Light**: pointer can resample the ASCII density

**Highlight**: cursor-position changes character density

**Depth**: none

**Parallax**: stepped

## Common implementation mistakes (avoid these)

- proportional font (must be monospace)
- line-height > 1

## Examples in the wild

- tympanus.net Codrops Efecto
- figlet headers

## References

- https://tympanus.net/codrops/2026/01/04/efecto-building-real-time-ascii-and-dithering-effects-with-webgl-shaders/

## Pairs with (prototype slugs)

- `style-terminal-mono`
- `recipe-terminal-on-web`
- `aesthetic-web-brutalism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->
