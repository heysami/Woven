# Shader Library (Illustrative Shaders) - research dossier

> Canonical reference for the **illustrative-shaders** family: stackable, animated, full-frame GLSL/WebGL effects in the register of [shaders.figma.com](https://shaders.figma.com/), [paper-design/shaders](https://github.com/paper-design/shaders), and brik.space. The kind of effect that is BETTER expressed as math than as a baked raster - dither waves, fluid halftone, particle web, magnetic field, particle stretch, lens distortion, color outline, luminance particles, riso print, organic distortion, and friends.
>
> Per-entry source files: `design-library/shader-<shaderId>.md` (YAML frontmatter for the stack contract + markdown body for technique + a YAML codeblock holding the implementation strategies). Machine index: `docs/research/shader-library.index.json` (regenerate via `python3 scripts/build-library-indexes.py`). **The index is the runtime read; this file is the primer.**
>
> Distinct from `material-library.md`: a MATERIAL makes one element FEEL like a real substance (glass refracts, clay deforms, paper grains) and is usually CSS/SVG-first and bound to a single element. An ILLUSTRATIVE SHADER is a full-canvas procedural LAYER you STACK and BLEND with other shaders to build a composed visual field - GLSL/WebGL-first, animated, and authored to be combined. They overlap at the edges (lens-distortion, riso-print, chromatic aberration appear in both registers); pick the shader card when the brief wants a composable animated layer, the material card when it wants a single reactive surface.

---

## 1. The stacking model (the load-bearing idea)

Like the Figma Shaders panel and paper-design's layered canvases, every effect here is one LAYER in a stack. Two things decide how a layer behaves:

### 1.1 SOURCE vs FILTER (`family` in the frontmatter)

- **`source`** - generates its own field from nothing (noise, particles, light, a procedural fill). It needs no layer beneath. Examples: `neuro-noise`, `dither-waves`, `particle-web`, `magnetic-field`, `godrays`, `metaball-merge`, `water-caustics`, `moire-interference`, `fluid-halftone`.
- **`filter`** - reads the layer(s) BENEATH it and transforms them (`needsSource: yes`). It is dead on its own. Examples: `lens-distortion`, `organic-distortion`, `particle-stretch`, `color-outline`, `riso-print`, `gradient-map`, `luminance-particles`.

A valid stack is therefore: **one or more sources at the bottom → optional filters above them → a top color/optical pass that unifies everything.** A filter with nothing under it is a build error; surface it.

### 1.2 Blend + layer order (`defaultBlend`, `role`)

Each card commits a `defaultBlend` (the blend mode it wants when composited onto the layers below) and a `role` (`background` / `overlay` / `accent`) that hints its z-position:

- **Light-emitting effects** (`godrays`, `water-caustics`, `particle-web`, `magnetic-field`, `dither-waves`) blend `add`/`screen` and want a DARK base to read against. They never darken.
- **Ink/print effects** (`riso-print`, `fluid-halftone`) blend `multiply` and build hue where they overlap; they want a paper base.
- **Optical/color passes** (`lens-distortion`, `gradient-map`, `color-outline`) go on TOP and re-sample the flattened stack - they are how you make five disparate layers read as one shot.
- **Generative bases** (`neuro-noise`, `metaball-merge`) are the bottom of the stack.

### 1.3 The composition contract

When a build stacks N shaders, render each `source` to its own buffer, composite in role order with each layer's `defaultBlend`, then run `filter` passes over the flattened result. Animate per-layer on a shared `u_time`. Three rules that keep a stack from turning to mud:

1. **One unifier on top.** A `gradient-map` or `lens-distortion` top pass ties the stack into one palette / one lens. Without it, stacked sources fight.
2. **Animate motion, freeze structure.** Phase the WAVE, not the dither matrix; orbit the blob centers, not the threshold; drift the moire angle, not the line frequency. Animating the structural grid causes shimmer/crawl.
3. **Honour `prefers-reduced-motion`.** Every animated layer needs a still fallback (freeze `u_time`); `moire-interference` and fast strobing layers MUST respect it (eye-strain / discomfort risk).

---

## 2. The catalog (32 entries: 16 sources + 16 filters)

This family is **full parity with Figma's official "created by Figma" shader catalog** (every fill + every effect) PLUS the popular community-gallery / paper-design effects the user named (`particle-web`, `magnetic-field`, `godrays`, `luminance-particles`, `riso-print`, `fluid-halftone`). The 2 trivial photo-correction utilities Figma ships (`Color adjustment`, `Filter presets`) are deliberately NOT cards - they are CSS `filter` tokens; use `channel-mixer` / `gradient-map` for real recolors.

### Sources (16 - generate their own field, `needsSource: no`)

| shaderId | one-liner | blend | named in |
|---|---|---|---|
| `mesh-gradient` | animated 16-point color mesh (premium SaaS backdrop) | normal | Figma Mesh gradient, paper meshGradient |
| `fractal-noise` | Perlin / Value / Voronoise procedural texture | overlay | Figma Fractal noise |
| `clouds` | procedural turbulent cloud sky | normal | Figma Clouds |
| `nebula` | deep-space colored gas + twinkling stars | screen | Figma Nebula |
| `glowing-wave` | luminous emitted wave bands | screen | Figma Glowing wave |
| `concentric-patterns` | bold nested ring / polygon shapes | normal | Figma Concentric patterns |
| `pattern-grid` | geometric repeat-tile fill (dots / crosses / chevrons) | normal | Figma Pattern grid |
| `moire-interference` | beating line/dot fields + RGB separation | screen | Figma Moire |
| `dither-waves` | glowing wave quantized through dither (source combo) | screen | Figma (Glowing wave + Dither) |
| `fluid-halftone` | curl-noise fluid re-screened as CMYK halftone dots | multiply | Figma gallery |
| `neuro-noise` | marbled domain-warped fbm ridges (AI-landing texture) | overlay | paper neuroNoise |
| `metaball-merge` | gooey blobs that fuse and split | normal | Figma Gooey merge, paper metaballs |
| `water-caustics` | shimmering refracted-light vein net | add | Figma Water caustic, paper voronoi |
| `godrays` | volumetric light shafts from a source point | add | paper godRays (gallery) |
| `particle-web` | drifting points linked to near neighbours (constellation) | screen | Figma gallery, paper dotOrbit |
| `magnetic-field` | curl flow-field filaments bending around poles | add | Figma gallery, paper neuroNoise |

### Filters (16 - transform the layer beneath, `needsSource: yes`)

| shaderId | one-liner | blend | named in |
|---|---|---|---|
| `gradient-map` | luminance remapped to a custom color ramp (duotone) | normal | Figma Gradient map |
| `channel-mixer` | false-color / duotone via an R/G/B mix matrix | normal | Figma Channel mixer |
| `dither` | standalone Atkinson / Floyd / Bayer screen of a layer | normal | Figma Dither |
| `halftone` | vintage print / comic dot screen of a layer | multiply | Figma Halftone |
| `hatching` | cross-hatch engraving line shading from luminance | multiply | Figma Hatching |
| `color-outline` | stacked offset outlines + gradient edge line-art | screen | Figma Outlines + Colored edges |
| `lens-distortion` | barrel/pincushion warp + radial chromatic aberration | normal | Figma Lens distortion |
| `organic-distortion` | ripple/swirl/twist/bulge domain-warp | normal | Figma Warp |
| `pattern-refraction` | refraction through a ribbed/lens pattern (reeded glass) | normal | Figma Pattern refraction |
| `particle-stretch` | directional pixel-smear motion trails | normal | Figma Pixel stretch |
| `pixelate` | chunky mosaic + optional tile-scatter | normal | Figma Pixelate |
| `slice-shift` | angled bands sheared apart (geometric glitch) | normal | Figma Slice shift |
| `chromatic-metal` | inflated glossy liquid-metal finish + RGB split | normal | Figma Chromatic metal |
| `bokeh-blur` | depth-of-field blur with highlight-disc bloom | normal | Figma Bokeh blur |
| `riso-print` | 2-3 ink re-screen with grain + registration shift | multiply | Figma gallery (Riso print) |
| `luminance-particles` | image dissolves into glowing motes by luminance | add | Figma gallery |

---

## 3. Prototype-style decision tree (prose)

The machine `decisionTree` in the index maps each `pairsPrototypes` slug → a default shader + alternatives. The shape of the mapping:

- **Dark tech / AI / crypto** (`recipe-ai-foundry-dark`, `aesthetic-cyberpunk`, `aesthetic-crypto-degen`, `recipe-devtools-marketing`, `aesthetic-depin-hardware`, `recipe-scientific-infra-marketing`, `aesthetic-blueprint-hologram`) → `neuro-noise` / `particle-web` / `magnetic-field` / `dither-waves`, finished with `godrays`.
- **Cinematic / cosmic / deep** (`aesthetic-luxury-cinematic-dark`, `aesthetic-cosmic-horizon`, `aesthetic-bioluminescent-deep`) → `godrays` + `luminance-particles` + `water-caustics` over `neuro-noise`.
- **Print / editorial / zine** (`recipe-editorial-magazine`, `recipe-readcv`, `aesthetic-anti-design`, `style-raster-cutout`) → `riso-print` / `fluid-halftone`, optionally `gradient-map`.
- **Loud / acid / poster / op-art** (`aesthetic-acid-design`, `aesthetic-acid-graphics`, `aesthetic-y2k-memphis-loud`, `aesthetic-op-art`, `aesthetic-monochrome-pop-poster`, `aesthetic-neubrutalism`) → `color-outline` / `moire-interference` / `gradient-map` / `organic-distortion`.
- **Aqua / soft / playful** (`aesthetic-frutiger-aero`, `aesthetic-positivity-kawaii`, `style-claymorphism`, `aesthetic-y2k-futurism`) → `metaball-merge` (+ `lens-distortion` for liquid glass).
- **Optical / motion** (`style-bold-display`, `style-oversized-neo-grotesque`) → `particle-stretch` on type; `lens-distortion` as the universal top pass.

Each card's `notForUseWhen` records where it actively breaks (e.g. `gradient-map` not on brand photos that must keep true color; `moire-interference` not on accessibility-first UI).

---

## 4. Engine + implementation register

These are WebGL/canvas effects first. Cards list, per entry, the cheapest faithful route in priority order:

1. **`webgl`** - the canonical fragment-shader sketch (full-screen quad, `u_time`/`u_mouse`/`u_src` uniforms). This is what the `shader` skill writes.
2. **`engine`** - the live in-app path. **22 of these effects are now FIRST-CLASS, STACKABLE effects in the live fx engine** (`editor/tools/_shared/fx.js` `EFFECTS` registry, surfaced on the **Effect building-block node** + inside the **mm-composer** via `fxProgramSpecs()`, and baked into the standalone twin). You can drop them on an Effect node and stack/blend them today. They are scalar-uniform (colour via `hue`/`saturation`/`value` knobs - stack a `gradient-map` / `color` / `lookup` pass to rebrand). The card names the matching live effect id and/or the paper-design/shaders + Figma equivalents.
3. **`canvas2d`** - a no-GL fallback (ImageData / drawImage) where viable.
4. **`svg` / `css`** - the DOM-register approximation (often static-only). Many of these have a sibling `material-*` card that is the CSS/SVG-first twin (e.g. `material-chromatic-aberration-lens`, `material-risograph`, `material-op-art`).

### 4.1 Live in the engine (Effect-node type ids)

**Now shipping as fx.js effects** (added in the illustrative-shaders port): SOURCES `mesh-gradient` · `fractal-noise` · `clouds` · `nebula` · `glowing-wave` · `neuro-noise` · `godrays` · `water-caustics` · `particle-web` · `magnetic-field` · `metaball-merge` · `moire-interference` · `concentric-patterns` · `dither-waves`; FILTERS `gradient-map` · `color-outline` · `channel-mixer` · `hatching` · `pattern-refraction` · `chromatic-metal` · `bokeh-blur` · `riso-print`.

**Already lived in the engine before the port** (the partials): the library's `dither` / `halftone` / `pixelate` / `slice-shift` / `lens-distortion` / `particle-stretch` / `organic-distortion` / `pattern-grid` map onto the pre-existing fx ids `dither` / `halftone` / `pixelate` / `slice` / `lens-distort` + `chromatic-aberration` / `directional-blur` / `displacement` / `pattern`. `fluid-halftone` = the live `fluid` source stacked under `halftone`.

So every one of the 32 library cards now has a live, stackable engine route. The cards remain the art-direction reference the `shader` skill reads when writing bespoke prototype GLSL (richer than the scalar-uniform node version - e.g. true RGB brand colours, multi-input sampling).

The `shader` skill (`.claude/agents/shader.md`) is the per-slot drawer that writes one of these for a `<canvas>` slot; it reads the index + the matching card's `webgl` strategy and exposes 3-6 live knobs per the asset-controls contract.

---

## 5. Anti-patterns (apply across the family)

- **Stacking without a unifier** - five sources at full saturation with no top `gradient-map`/`lens-distortion` = mud. Always commit a top pass.
- **A filter with no source** - `riso-print` / `gradient-map` / `lens-distortion` over nothing renders empty or black. Validate `needsSource`.
- **Crawling structure** - animating the dither matrix / halftone grid / moire frequency instead of the wave/flow/phase. Freeze the grid.
- **Wrong blend for light** - additive effects (`godrays`, caustics, web, field) composited `normal` lose their glow and darken the scene. Light ADDS.
- **Ignoring DPR** - thin lines / small dots / 1px dither vanish at retina. Scale feature sizes by device px.
- **Ignoring reduced-motion** - every animated layer needs a frozen fallback; strobing/moire layers MUST honour it.
- **Heavy full-screen shaders on mobile** - cap DPR, drop the most expensive layer first; lean ambient by default (the `shader` skill's standing guidance).

---

## 6. References

- Figma shaders + effects: https://shaders.figma.com/ and https://help.figma.com/hc/en-us/articles/41409034424215
- paper-design/shaders (open-source, the canonical stackable set): https://github.com/paper-design/shaders and https://shaders.paper.design/
- The Book of Shaders (fragment-shader fundamentals): https://thebookofshaders.com/
- Curl noise for flow fields: https://www.bit-101.com/blog/2021/07/curl-noise/
