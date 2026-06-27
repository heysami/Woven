---
techniqueId: stylize-shader-pass
name: Stylize shader pass (live dither / halftone / ASCII over media)
category: shader-driven
subCategory: post-process
role: hero | texture
binding: time + optional pointer-xy
medium: video-or-raster-through-webgl
pairsPrototypes: [style-pixel-bitmap, aesthetic-web-brutalism, style-brutalist-raw, aesthetic-corporate-grunge]
notForUseWhen: The media's fine detail IS the content (product close-ups, faces that must stay personable), the page already runs another fullscreen shader, or the register is luxe/minimal where lo-fi sampling reads as damage.
images:
  - src: motion-stylize-shader-pass-ui.png
    reason: Motion technique UI mockup.
  - src: motion-stylize-shader-pass-isolated.png
    reason: Signature technique, isolated.
---

# Stylize shader pass (live dither / halftone / ASCII over media)

A video or image is sampled as a texture and re-rendered every frame through a
stylization shader - ordered dither, blue-noise dither, 1-bit threshold, CMYK
halftone dots, line halftone, or an ASCII/braille glyph ramp. The efecto.app
/fx pattern: the SAMPLING GRID becomes the aesthetic, and because the source
keeps playing underneath, the grid seethes with live motion. This is the time
axis the static surface materials (`material-dithered-1bit`,
`material-halftone-cmyk`, `material-ascii-art-surface`) don't have.

## Motion signature

- Source media plays muted/looped into an offscreen `<video>`/`<img>`; a
  fullscreen (or slot-sized) WebGL quad samples it per fragment.
- Per-cell quantization: fragment coords snap to a cell grid (4-16px);
  cell luminance → output decision (dot radius, glyph index, on/off bit).
- The grid is FIXED while the content moves through it - that tension is the
  whole effect. Never animate the grid and the content simultaneously.
- Optional pointer modulation: cell size or threshold eases around the cursor
  (efecto's `mpx/mpy` params) - denser sampling where the visitor looks.
- Subtype is a COMMITMENT per piece, not a carousel: bayer-8 dither ≠ halftone
  ≠ ASCII; pick one register and hold it.

## Subtype menu (commit exactly one)

- **bayer-ordered dither** - crunchy retro-print; pairs pixel/terminal.
- **blue-noise dither** - organic grain; the subtlest, pairs editorial.
- **1-bit threshold** - harshest; pure black/white poster energy.
- **CMYK halftone dots** - rotated per-channel screens; print-shop warmth.
- **line halftone** - luminance → line weight; engraving read.
- **ASCII ramp** - glyph atlas lookup (` .:-=+*#%@`); terminal canon. Render
  the glyph atlas ONCE to a texture; per-cell UV lookup, never per-frame text.

## Implementation skeleton

```glsl
// fragment core - halftone example
vec2 cell = floor(vUv * res / cellPx) * cellPx / res;
float luma = dot(texture2D(uMedia, cell).rgb, vec3(.299,.587,.114));
float d = distance(fract(vUv * res / cellPx), vec2(.5));
float dot_r = (1.0 - luma) * 0.5;                 // dark = big dot
gl_FragColor = vec4(vec3(step(d, dot_r) == 1.0 ? ink : paper), 1.0);
```

```js
// pointer modulation (optional)
target = { x: e.clientX/innerWidth, y: e.clientY/innerHeight };
cur.x += (target.x - cur.x) * 0.07;               // damped, never snapped
uniforms.uCellPx.value = mix(maxCell, minCell, proximity(cur));
```

## Performance notes

- Render at HALF resolution and upscale - the quantization hides it entirely;
  this is the cheapest fullscreen shader family there is.
- `video.requestVideoFrameCallback` (fallback rAF) to avoid re-uploading
  unchanged frames; cap texture at 1280px on the long edge.
- Pause the loop off-screen (IntersectionObserver) and on `document.hidden`.
- `prefers-reduced-motion`: swap the video source for a still poster - the
  shader keeps running on the still (the material survives, the motion stops).

## UI composition rules

- Type sits ON TOP in clean DOM - never inside the shader. The contrast
  between crisp type and seething sampled media is the composition.
- One stylized region per view: full-bleed hero OR one media slot, not both.
- Ink/paper colors come from the page tokens, not pure #000/#fff - tie the
  pass to the palette and it reads designed instead of filtered.

## When to use

- Heroes where licensed/generated footage is too literal - the pass abstracts
  it into texture while keeping its motion alive.
- Terminal/brutalist/zine registers needing motion without breaking the
  print-process discipline.
- Background media under dense dashboards (1-bit or blue-noise at low
  contrast) - motion with near-zero attention cost.

## When NOT to use

- Faces that must stay warm and human (ASCII a face only when alienation is
  the point).
- Pages with another fullscreen GL pass already running (compose into ONE
  pass instead - two fullscreen shaders is a perf foul).
- Luxe minimal registers - sampling grids read lo-fi by design.

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-web-brutalism`
- `style-brutalist-raw`
- `aesthetic-corporate-grunge`
