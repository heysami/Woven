# Spline-grade 3D & shader-effects study — 10 reference deconstruction

> Study of ten user-supplied references (efecto.app /fx + nine Spline community
> scenes) identifying each one's style, aesthetic, and material vocabulary;
> grouping them into families; and indexing the new design-library entries the
> study produced. Companion to the hero-3d orchestrator discussion: these
> references define the QUALITY BAR — physically-based materials, studio
> lighting, eased choreography, UI seamlessly layered with the scene.

---

## 1. Per-reference identification

### R1 — efecto.app /fx (dither / ASCII / halftone media processing)

- **What it is:** real-time stylization shaders over arbitrary media (video/image): ordered dither, blue-noise dither, 1-bit threshold, CMYK halftone dots, line halftone, ASCII glyph ramp — with live params (cell size, threshold, pointer-driven density).
- **Style:** print-process / terminal lo-fi applied to MOTION media — the sampling grid is the aesthetic.
- **Aesthetic:** web-brutalism / corporate-grunge / terminal registers.
- **Material:** `material-dithered-1bit`, `material-halftone-cmyk`, `material-ascii-art-surface` (all EXIST) — but as static surfaces. The gap is the TIME axis: media running through the sampler live.
- **Library gap → NEW:** `motion-stylize-shader-pass`.

### R2 — "Reeded liquid glass — Prism hero section concept"

- **What it is:** mint-green monochrome hero; a vertical fluted/reeded glass panel slices a glossy green sphere behind it into displaced vertical strips. UI text sits left on the flat field; the refraction IS the spectacle.
- **Style:** liquid-glass family, monochrome-pop product stage.
- **Aesthetic:** pastel-pop / monochrome-pop-poster (single-hue scene discipline).
- **Material:** reeded glass — per-slat cylindrical-lens refraction. NOT in library (frosted scatters uniformly; dispersion-prism splits spectrum; neither slices).
- **Library gap → NEW:** `material-reeded-fluted-glass`.

### R3 — "Interactive AI website" (draggable cubes)

- **What it is:** cluster of glossy blue tinted-glass cubes floating over an icy white-blue gradient; user drags cubes around, they spring and resettle. Corporate-AI landing copy on the left.
- **Style:** glassmorphism taken to 3D; soft cool corporate.
- **Aesthetic:** frutiger-adjacent soft AI marketing (restrained-ai-marketing posture with one playful toy).
- **Material:** tinted transmission glass cubes — coverable by `material-frosted-glass` + `material-dispersion-prism-glass`. The signature is the INTERACTION, not the surface.
- **Library gap → NEW:** `motion-drag-physics-cluster`.

### R4 — "Tick Tock — Interactive Landing"

- **What it is:** black field, oversized white grotesque "TICK TOCK" with echo-outline repeats stacked behind; a dark smoked-glass cube floats OVER the type, refracting and smearing the letterforms through its body; film grain; mono micro-labels at the corners (FORM EARTH / TARGET MARS).
- **Style:** `style-oversized-neo-grotesque` (EXISTS) + echo type.
- **Aesthetic:** `aesthetic-monochrome-pop-poster` (EXISTS).
- **Material:** smoked/obsidian dark glass whose whole job is refracting TYPOGRAPHY behind it. Distinct from dispersion-prism (optically pure, spectral) — this is dark, smoky, blurring.
- **Library gap → NEW:** `material-smoked-obsidian-glass`.

### R5 — "Elegant Beauty of Dark Aesthetics"

- **What it is:** chrome-extruded display type ("ELEGANT BEAUTY OF DARK AESTHETICS") floating over a field of wet black volcanic-rock blobs; dark luxe, specular sweeps crawl across the letter faces.
- **Style:** typography AS the 3D object — extruded, env-mapped chrome.
- **Aesthetic:** `aesthetic-luxury-cinematic-dark` (EXISTS).
- **Material:** chrome type (new — `material-liquid-chrome-silk` is a cloth surface, `material-chrome-mirror` is a UI surface; neither is type-as-object); obsidian rock clusters (skip — raster/3D asset territory, low reuse).
- **Library gap → NEW:** `material-chrome-extruded-type`.

### R6 — "Clarity Stream"

- **What it is:** thousands of hairline luminous strands flowing as one silk ribbon across a black field; iridescent micro-hues (orange/blue/violet) live INSIDE the strand bundle; type floats above in quiet space.
- **Style:** `style-silk-chrome-flow` adjacent — but the existing entry is a continuous mirrored-cloth SURFACE; this is discrete 1px filaments with additive glow (fiber-optic read).
- **Aesthetic:** restrained dark marketing; cosmic-horizon adjacent.
- **Library gap → NEW:** `material-filament-strand-ribbon`.

### R7 — "HOVER + SCROLL EFFECT" (pixlspace)

- **What it is:** white Scandinavian-minimal page; halftone-dot logotype; body copy sits OUT of focus (gaussian blur) except where a circular lens — tracking the pointer — magnifies and sharpens it; scroll transitions rack focus between sections.
- **Style:** dot-matrix type + camera-optics play on an editorial-minimal field.
- **Aesthetic:** monochrome-tech-editorial (EXISTS).
- **Material:** halftone type — `material-halftone-cmyk` / `material-dithered-1bit` cover the surface.
- **Library gaps → NEW:** `motion-lens-magnifier-reveal` + `motion-focus-pull-type` (two distinct optical techniques in one piece).

### R8 — "Chainmail background"

- **What it is:** full-bleed interlocked chainmail of anodized chrome rings (blue→violet→pink sheen) on near-black; oversized white headline over it ("DATA SECURITY FOR GenAI AND CLOUD"). Built from 2 rings + 1 cloner — instanced geometry.
- **Style:** hardware-luxe substrate under brutalist-scale type.
- **Aesthetic:** cyber-industrial; crypto/security infra register.
- **Material:** anodized interlocked metal mesh — env-mapped, thin-film iridescent, INSTANCED. Nothing in the library covers a metal substrate built from repeated interlocking units.
- **Library gap → NEW:** `material-anodized-chainmail`.

### R9 — "Connecting Card"

- **What it is:** dark matte hardware-noir scene; a frosted acrylic boarding-pass card glows from within; above it floats a dark chip card with QR; a warm orange volumetric bloom fills the air gap BETWEEN them — the glow announces the connection. Glowing mono HUD type.
- **Style:** sci-fi hardware noir; dense-mono HUD labels.
- **Aesthetic:** `aesthetic-depin-hardware` / `aesthetic-cassette-futurism` (dark) (EXIST).
- **Material:** edge-lit frosted acrylic + volumetric light spill between objects. `material-atmosphere-rim-glow` is an emissive EDGE; this is light living inside translucent volume and in the air gap.
- **Library gap → NEW:** `material-edge-lit-acrylic`.

### R10 — "The Eternal ARC"

- **What it is:** monochrome museum scene — a glossy black torus ring suspended in void, raked by soft volumetric light shafts from upper-right; hairline-bordered ghost CTA; "engineered beyond symmetry" copy. Cinematic stillness, slow drift.
- **Style:** sculptural object on a plinth of darkness.
- **Aesthetic:** `aesthetic-sculptural-minimal` (dark variant) + `aesthetic-luxury-cinematic-dark` (EXIST).
- **Material:** polished onyx/ceramic (coverable by ceramic-glaze/chrome on dark) + VOLUMETRIC LIGHT SHAFTS — god rays as a first-class material. `material-volumetric-cloud` is cotton-volume; rays are a different physics (light scattering in air, not surface).
- **Library gap → NEW:** `material-volumetric-light-shaft`.

---

## 2. Grouping — four families + one register

### Family A — Refractive glass stage (R2, R3, R4)

Glass whose job is DISTORTING what sits behind it: reeded slats slicing a
sphere, tinted cubes bending a gradient, smoked cube smearing typography.
The shared physics: transmission + IOR + something worth refracting behind.
The shared composition: refractor as hero object, UI on the flat field.

### Family B — Chrome & metal luxe (R5, R6, R8)

Environment-mapped metal carrying the spectacle: extruded chrome type,
filament strand ribbons, anodized chainmail. The shared physics: metalness 1
+ env map + anisotropic or thin-film color response. The AI-tell to avoid:
gradient-only "chrome" with no environment lookup (reads as plastic).

### Family C — Cinematic light-on-dark stage (R9, R10)

Light itself as the material: volumetric shafts raking a sculpture, edge-lit
acrylic glowing from within, warm bloom in the air gap between two objects.
The shared discipline: near-black matte substrate, ONE light story, slow
drift, mono/HUD type.

### Family D — Print-process optics (R1, R7)

The sampling grid as aesthetic: dither/halftone/ASCII passes over live media,
halftone type, plus camera-optics play (rack focus, magnifier lens). 2D
shader territory — no 3D engine needed, pairs with terminal/brutalist/
editorial registers.

### Cross-cutting register — the Object Stage (R2–R10, all Spline refs)

Every Spline reference shares one composition contract: a single hero
3D object (or object cluster) studio-lit on a disciplined monochrome field,
ambient motion always running, pointer-eased response (damped lerp, never
snap), and UI text laid INTO the scene's quiet zone — not boxed beside it.
Captured as `recipe-object-stage-hero`.

---

## 3. New library entries (12)

| Entry | Type | From | Family |
|---|---|---|---|
| `material-reeded-fluted-glass` | material | R2 | A |
| `material-smoked-obsidian-glass` | material | R4 | A |
| `material-chrome-extruded-type` | material | R5 | B |
| `material-filament-strand-ribbon` | material | R6 | B |
| `material-anodized-chainmail` | material | R8 | B |
| `material-edge-lit-acrylic` | material | R9 | C |
| `material-volumetric-light-shaft` | material | R10 | C |
| `motion-stylize-shader-pass` | motion | R1 | D |
| `motion-lens-magnifier-reveal` | motion | R7 | D |
| `motion-focus-pull-type` | motion | R7 | D |
| `motion-drag-physics-cluster` | motion | R3 | A |
| `recipe-object-stage-hero` | recipe | R2–R10 | register |

Already covered (no new entry needed): dither/halftone/ascii SURFACES
(`material-dithered-1bit`, `material-halftone-cmyk`,
`material-ascii-art-surface`), spectral prism (`material-dispersion-prism-glass`),
chrome cloth (`material-liquid-chrome-silk`), dark-luxe and sculptural
aesthetics (`aesthetic-luxury-cinematic-dark`, `aesthetic-sculptural-minimal`),
oversized echo type (`style-oversized-neo-grotesque` +
`aesthetic-monochrome-pop-poster`).

## 4. Orchestrator routing (from the companion discussion)

- Family A + B + C hero objects → the proposed **hero-3d orchestrator**
  (Spline-grade three.js: transmission/dispersion materials, HDRI lighting,
  post chain, damped interaction). Interim: `3d` drawer at `performance: hero`.
- Family D → `interactive-polish-orchestrator` (overlay) /
  `visual-orchestrator` shader drawer (per-slot) /
  `interactive-media-orchestrator` (input-reactive).
- Materials worn by DOM elements (reeded glass pane over a DOM image,
  edge-lit cards) → `material-orchestrator`.
