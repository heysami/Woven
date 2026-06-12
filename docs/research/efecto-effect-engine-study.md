# Efecto /fx effect-engine study — why their dither/ASCII/halftone feels better

> Reverse-study of https://efecto.app/fx (bundle archaeology, June 2026 —
> 105 Next.js chunks pulled, 73 GLSL shaders extracted). Canonical reference
> for upgrading our stylize-pass quality: the gap is NOT the core sampling
> math (ours matches theirs) — it is the CHASSIS around it. Read alongside
> `design-library/motion-stylize-shader-pass.md`.

---

## 1. Architecture — the two-stage pipeline

Efecto is **three.js + pmndrs `postprocessing`**. Every piece is:

```
INPUT STAGE  (a live three.js scene)        STYLIZATION STAGE  (postprocessing Effect)
┌─────────────────────────────────┐         ┌──────────────────────────────────┐
│ media: uploaded video / image    │   ───►  │ ascii | dither | halftone |      │
│ shader: meshGradient, particles, │  full-  │ dotGrid | led | glitch family    │
│  voronoi, pulsar, blackHole,     │  screen │ (one Effect subclass each,       │
│  torus, fireworks, glass, chrome │  buffer │  merged into ONE fullscreen pass) │
└─────────────────────────────────┘         └──────────────────────────────────┘
```

**This is the "combination" feel.** The input is ALIVE before stylization:
either a video playing, or a procedural scene (mesh gradient drifting,
particles orbiting, voronoi crawling). The stylization then adds its OWN
motion layer on top (jitter, wave, scanline, noise). Two independent motion
sources compose — our single-shader approach has one.

The `in=` URL param picks the input (`media` | `shader`); the rest of the
URL serializes the full uniform state — every piece is a shareable preset.

## 2. The standard effect chassis — every effect gets the same stack

Extracted verbatim from their ASCII effect (the others share it): every
stylization Effect carries a TIERED uniform contract, applied in fixed order:

```
PRE  (Tier 2 — distorts the sampling space, before quantization):
  curvature            — CRT barrel: centered *= 1 + curvature*dot(c,c)
  waveAmplitude/Freq/Speed — sinusoidal UV warp
  aberrationStrength   — R/B sample offset (per-channel texture taps)
  noiseIntensity/Scale/Speed — animated value noise added to the sample
  brightnessAdjust / contrastAdjust

CORE (the actual stylization):
  cellSize             — resolution/cellSize grid; sample at CELL CENTER
  jitterIntensity/Speed — per-cell random offset, time-stepped (floor(t*speed))
  glitchIntensity/Freq — per-ROW horizontal cell shifts at random rows
  invert, colorMode (mono vs per-cell color), asciiStyle / charRotation

POST (Tier 1 — over the stylized result):
  colorPalette         — int enum: none/green/amber/cyan/blue terminal tints
  mouseGlowEnabled/Radius/Intensity — exp(-dist/radius) glow AT THE CURSOR
  scanlineIntensity/Count — sin(uv.y * count * π) darkening
  vignetteIntensity/Radius
```

Plus two chassis uniforms that matter disproportionately:

- **`targetFPS`** — `time = floor(time*fps)/fps` — quantizes ALL effect
  motion to 8/12/24fps. The stepped cadence reads as deliberate retro
  hardware, not as smooth CSS. This is the single cheapest "designed" signal
  they have.
- **`contentBounds` (vec4 x,y,w,h normalized)** — the effect KNOWS where the
  subject sits and can inset/frame the stylization around it rather than
  treating the viewport as one undifferentiated field.

## 3. The pointer system — history, not position

Three pointer integrations, increasing in craft:

1. **`mousePos`** in every effect → mouse-glow post layer (brightness lifts
   near the cursor — the stylized field "notices" the visitor).
2. **`uMouseHistory[8]`** in the procedural scenes — the last 8 pointer
   positions as a uniform array → trails, wakes, and inertia. The cursor has
   MASS in their scenes; ours is a point.
3. **`uClickTime`** — click bursts: `timeSinceClick` drives one-shot
   radial spark/ripple responses inside the scene shader.

## 4. Core sampling math (matches ours — not the gap)

- ASCII: luminance per cell (rec601 dot), glyphs drawn PROCEDURALLY from a
  4×4 sub-grid lookup per brightness band (no glyph texture at the low end;
  a `uCharacters` texture path exists for the full charset mode).
- Dither: classic 8×8 Bayer `int[64]` matrix, `step(bayer*threshold, luma)`,
  two-color palette mix (`uColor1`/`uColor2` — INK AND PAPER ARE TOKENS, not
  hardcoded black/white).
- Halftone: dot-grid (`uDotSize/uSpacing/uContrast/uRandomness`), line
  engraving (`uSpacing/uMinThickness/uMaxThickness/uAngle` — luminance →
  line weight), and a rotated-screen CMYK port of three.js HalftoneShader.
- Glitch family: VHS (RGB shift + scanline + tracking), digital block
  displacement, "weird" slice/flip — each its own Effect, composable.

## 5. Why theirs feels better — ranked, actionable

1. **Two-stage composition** (input scene alive + effect motion on top).
   → Our stylize-shader-pass should accept EITHER a video texture OR one of
   our existing procedural shader scenes as input — one render target,
   effect pass reads it.
2. **The chassis is standard equipment.** Scanline, vignette, palette,
   curvature, jitter, mouse-glow ship with EVERY effect at tasteful defaults.
   Our drawers generate the core math and stop. The polish IS the chassis.
   → Bake the tier stack into the shader drawer's skill as a fixed scaffold.
3. **targetFPS time quantization** — stepped motion cadence. One line; huge
   register shift.
4. **Pointer history + click time** — cursor with inertia and memory.
5. **postprocessing library discipline** — `mainImage(inputColor, uv,
   outputColor)` convention, sRGB-correct buffers, all effects merged into
   one fullscreen pass (no pass-per-effect overdraw).
6. **Tokens, not constants** — ink/paper colors, palettes, cell sizes all
   uniforms, all URL-serializable. Every output is a tweakable preset, which
   is also why their defaults are good: they were FOUND by tweaking, not
   guessed.

## 6. Routing into our system

- The chassis scaffold + two-stage input contract belongs in the `shader`
  drawer skill (visual-orchestrator dispatch) and
  `polish-shader-author` — same scaffold, overlay-flavored defaults.
- An input-reactive piece (pointer history, click bursts) routes to
  `interactive-media-orchestrator` with `im-output-shader-particle`; the
  chassis uniforms map 1:1 onto its input→mapping→output contract
  (mousePos/history = input features, tier uniforms = output params).
- Reference shaders extracted to `/tmp/efecto-study/glsl/` during the study;
  the load-bearing excerpts are inlined above — regenerate via bundle pull
  if ever needed again.
