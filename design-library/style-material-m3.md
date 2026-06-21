---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-material-m3-ui.png
    reason: Style surface UI mockup.
  - src: style-material-m3-isolated.png
    reason: Signature surface, isolated.
---
# Material Design (M3, dynamic-color) (style)

**Tag:** `style-material-m3`

**Canonical references:** Material 3 spec (m3.material.io) · Android 14/15 system UI · Google Calendar / Keep / Tasks 2023+ · Pixel Launcher dynamic theming · Material Symbols variable font.

## Surface treatment

**Color (dynamic, seed-driven).** Pick one seed and derive the rest. Express in OKLCH so tonal steps stay perceptually even.
- `--seed: oklch(58% 0.15 268)` (example: violet)
- `--primary: var(--seed)`
- `--on-primary: oklch(99% 0.01 268)`
- `--primary-container: oklch(92% 0.05 268)`
- `--on-primary-container: oklch(20% 0.08 268)`
- `--surface: oklch(98% 0.005 268)` (light) / `oklch(18% 0.01 268)` (dark)
- `--surface-dim/bright/container-low/container/container-high/container-highest`: tonal ladder, each step ~3% lightness apart
- `--outline: oklch(60% 0.02 268)`, `--outline-variant: oklch(85% 0.01 268)`
- Surface tinting is mandatory: `background: color-mix(in oklch, var(--primary) 5%, var(--surface))` for low elevation, 8% for medium, 11% for high. Never raw white-on-white between elevations.

**Type.** Roboto Flex (preferred, variable: `wght 100-1000`, `wdth 25-151`, `GRAD -200-150`) or Inter as fallback. Material Symbols Rounded for icons (variable: `FILL`, `wght`, `GRAD`, `opsz`).
- Display L 57/64, Display M 45/52, Display S 36/44
- Headline L 32/40, Headline M 28/36, Headline S 24/32
- Title L 22/28, Title M 16/24 (wght 500), Title S 14/20 (wght 500)
- Body L 16/24, Body M 14/20, Body S 12/16
- Label L 14/20 (wght 500), Label M 12/16 (wght 500), Label S 11/16 (wght 500)
- Letter-spacing: tighter on display (-0.25 to 0), looser on label (+0.1 to +0.5).

**Radius (elevation-graded).** Extra-small 4, Small 8, Medium 12, Large 16, Extra-large 28, Full 9999. FAB = 16, chip = full, card = 12, dialog = 28, button = full. Mixing radii within one component is forbidden - pick one tier.

**Elevation (5 levels, tint + shadow).** Elevation is tint first, shadow second.
- Level 0: `--surface`, no shadow
- Level 1: tint 5%, shadow `0 1px 2px rgb(0 0 0 / 0.3), 0 1px 3px 1px rgb(0 0 0 / 0.15)`
- Level 2: tint 8%, shadow `0 1px 2px rgb(0 0 0 / 0.3), 0 2px 6px 2px rgb(0 0 0 / 0.15)`
- Level 3: tint 11%, shadow `0 4px 8px 3px rgb(0 0 0 / 0.15), 0 1px 3px rgb(0 0 0 / 0.3)`
- Level 4: tint 12%, shadow `0 6px 10px 4px rgb(0 0 0 / 0.15), 0 2px 3px rgb(0 0 0 / 0.3)`
- Level 5: tint 14%, shadow `0 8px 12px 6px rgb(0 0 0 / 0.15), 0 4px 4px rgb(0 0 0 / 0.3)`

**Decoration grammar.**
- State layers are mandatory: hover = 8% on-color overlay, focus/pressed = 12%, dragged = 16%. Apply via `::before` with `mix-blend-mode: plus-lighter` or a translucent overlay.
- Filled, Tonal, Outlined, Elevated, Text - five button variants, never invent a sixth.
- Ripple from touch point on press (radial gradient expanding to bounds, ~0.4s).
- Icons: Material Symbols only. Rounded grade by default. Filled state for selected nav items.
- No skeuomorphic shadows, no glassmorphism, no gradients other than ripples and the implicit surface tint.

## Motion budget

- Emphasized easing: `cubic-bezier(0.2, 0, 0, 1)` (decelerate), `cubic-bezier(0.3, 0, 0.8, 0.15)` (accelerate), `cubic-bezier(0.2, 0, 0, 1)` (standard).
- Durations: short 50-200ms (state changes), medium 250-400ms (transitions), long 450-600ms (large surface changes).
- Spring for FAB and shared-axis transitions: `transition: all 0.3s cubic-bezier(0.2, 0, 0, 1)`.
- Containment morph: FAB expands into bottom sheet with shared bounds - radius animates from `--shape-full` to `--shape-large`.
- No bouncy overshoots, no parallax, no scroll-jacking.

## Failure mode

The trashy tell: applying M3 tokens without the surface tint ladder - flat white cards on flat white scaffolds, no elevation differentiation. Or: using Material Symbols Outlined when the rest of the app uses Rounded (or mixing fill states arbitrarily). Or: a seed color picked but never propagated into containers and on-colors, so chips and FABs read as random brand accents instead of derived from the same seed.

## Best for

Android-first products, multi-surface apps that need dynamic theming (per-user wallpaper-derived palettes), productivity tools where state layers and elevation must communicate interactive affordances, design systems that want a generated tonal palette from one seed.

## Pairs well with

- Shells: `shell-mobile-app`, `shell-two-column-app`, `shell-three-column-app`, `shell-top-bar-canvas`, `shell-bento-grid`
- Aesthetics: `aesthetic-positivity-kawaii`, `aesthetic-frutiger-eco`, `aesthetic-solarpunk`, `aesthetic-corporate-memphis`
