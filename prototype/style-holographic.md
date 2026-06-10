---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-holographic-ui.png
    reason: Style surface UI mockup.
  - src: style-holographic-isolated.png
    reason: Signature surface, isolated.
---
# Holographic / Iridescent (style)

**Tag:** Holographic / Iridescent UI (Apple Pay Cash, visionOS materials, Apple TV+ 2025 rebrand, Robb Owen CSS shaders, Boiler Room 2024 identity)

**Canonical references:** Apple Pay Cash · visionOS materials · Apple TV+ 2025 rebrand · Robb Owen CSS shaders · Boiler Room 2024 identity

> **Raster required:** oil-on-water iridescent material captures or hand-shot iridescent objects. Conic-gradient rainbow alone is the AI tell — real iridescence requires a sampled surface. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

## Surface treatment

**Substrate.** Iridescence MUST sit on dark — white backgrounds kill the specular. Deep cool base `oklch(0.16 0.02 250)` (≈ `#1a1d24`) with a 1200px radial vignette `radial-gradient(ellipse at 50% 30%, oklch(0.22 0.03 250) 0%, oklch(0.12 0.02 250) 70%)`.

**Pearl palette (OKLCH for perceptual smoothness).**
- mint `oklch(0.88 0.09 155)`
- rose `oklch(0.82 0.10 15)`
- lilac `oklch(0.80 0.11 310)`
- sky `oklch(0.84 0.09 230)`
- butter `oklch(0.90 0.08 90)`

**Chrome greys.** `#e8ebf0 / #9098a8 / #5a6172 / #2a2e38`. One neutral accent for actionable text `#f5f7fa`. The rainbow is NEVER the accent — it is the material; type stays cool monochrome.

**Type stack.** SF Pro Display / Inter Variable at weights 510 + 600 for shell (instrument-panel restraint). Söhne Mono or Berkeley Mono for value-readouts and timestamps. NO display serifs, NO script fonts — the surface is the spectacle.

**Sizes.** Hero numeral 72/80 (card balance, wordmark). Display 32/40. Body 15/22. Micro-label 11/16 uppercase tracking 0.08em.

**Line-height.** Body 1.45, display 1.05, micro 1.4.

**Radius.** Hero card 24px (physical credit-card corner scaled). Buttons 999px (pill) or 12px. Panels 16px. Never mix more than two radii on one screen.

**Borders.** 1px hairline `rgba(255,255,255,0.08)` on glass surfaces. 1px inner-highlight `inset 0 1px 0 rgba(255,255,255,0.12)` on the iridescent card to fake a beveled edge. No outline borders on the holo surface itself.

**Shadow.** Holo card on `0 30px 60px -20px rgba(0,0,0,0.55), 0 8px 24px -8px oklch(0.40 0.15 280 / 0.35)` — the second shadow is a tinted spill pulled from one hue in the gradient, never neutral grey. Chrome elements get a flat `0 1px 0 rgba(255,255,255,0.04)` and nothing else.

## Decoration grammar

**Mandatory.**
- ONE specular highlight: soft white linear-gradient at 115° masked into the top-left quadrant via `mix-blend-mode: color-dodge`.
- Conic base gradient in OKLCH at 30-40% opacity over a charcoal layer:
  `conic-gradient(in oklch from 45deg, oklch(0.85 0.10 200), oklch(0.82 0.11 310), oklch(0.88 0.09 60), oklch(0.84 0.10 155), oklch(0.85 0.10 200))`
- Fine grain noise overlay at 4% opacity to break gradient banding.

**Forbidden.** Chrome bevels. Drop shadows on the holo surface (the tinted spill belongs to the substrate). Sparkle particles. Lens flares. Iridescence on body type or form inputs. The words "AI" or "Future" anywhere.

## Motion budget

Iridescence is gyroscope/pointer-driven, NOT autoplaying.

```
transform: rotateX(calc(var(--py) * 8deg)) rotateY(calc(var(--px) * 8deg));
filter: hue-rotate(calc(var(--px) * 25deg));
```

Gradient `background-position` shifts ±15%. Hue traverses a 40-50° arc maximum.

Transitions: `transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1)`, gradient position lerped at 120ms.

If autoplay is unavoidable: 8s ease-in-out cycle through the same narrow arc, NEVER a full 360° spin. Honor `prefers-reduced-motion` by freezing to the centered state.

Forbidden: spinning conic gradients, strobing keyframes under 4s, hue-rotate on body text.

## Failure mode

`conic-gradient(#f0f, #0ff, #ff0, #f0f)` full-bleed behind everything + 2s infinite `hue-rotate(360deg)` spin + iridescence smeared across body type and form inputs + sRGB interpolation producing muddy brown bands at the cyan→magenta crossover + glossy Y2K bevels stacked on top. The tasteful version is ONE pearl object on a dark stage whose hue travels a 40° arc on tilt, with everything else held in cool monochrome.

## Best for

Payment cards and wallet balances. Music release artwork and festival lineups. AR/spatial OS hero materials. Limited-drop product launches (sneakers, vinyl, fragrance). Award/credential surfaces (certificates, membership tiers). AI-model "capability cards" where the material itself signals novelty.

## Pairs well with

- **Shells:** shell-centered-column, shell-mobile-app, shell-hero-stack, shell-canvas-floating, shell-bento-grid
- **Aesthetics:** aesthetic-y2k-futurism, aesthetic-frutiger-chromecore, aesthetic-frutiger-dark-aero, aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-vector-neovectorheart
