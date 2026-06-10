---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-dense-mono-dark-ui.png
    reason: Style surface UI mockup.
  - src: style-dense-mono-dark-isolated.png
    reason: Signature surface, isolated.
---
# Dense mono dark (Bloomberg-style) (style)

**Tag:** `style`

**Canonical references:** Bloomberg Terminal · IDE inspectors (VS Code, JetBrains) · Refinitiv Eikon · trading-desk dashboards · `htop` / `btop`.

## Surface treatment

Information surface — every pixel earns its keep. Dark by default, near-monochrome chassis with saturated accents reserved for live data. Type is the primary visual element; chrome recedes.

**Colors (OKLCH)**
- Background: `oklch(0.18 0.01 250)` (panel) / `oklch(0.14 0.008 250)` (canvas)
- Foreground: `oklch(0.92 0.01 250)` primary / `oklch(0.65 0.012 250)` secondary / `oklch(0.45 0.01 250)` tertiary
- Borders / hairlines: `oklch(0.28 0.008 250)`
- Accent (live data): amber `oklch(0.78 0.14 75)`, cyan `oklch(0.78 0.13 220)`, green `oklch(0.78 0.15 145)`, magenta `oklch(0.72 0.16 340)`
- Semantic: positive = green; negative = magenta or red `oklch(0.65 0.18 25)`; warning = amber.
- Greys held at chroma 0.008–0.012; accents 0.13–0.16. No mid-saturation tints.

**Type**
- Mono: `JetBrains Mono` Medium / `Berkeley Mono` / `IBM Plex Mono` — for all numeric data, identifiers, code, tabular text. This is the default voice.
- Sans: `Inter` / `IBM Plex Sans` — only for paragraph prose and headers. Same x-height family as the mono where possible.
- Sizes: 10 / 11 / 12 / 13 / 14 px. Body is 12. Headers max 14.
- Line-height: 1.25–1.35 — tight.
- Tracking: 0 on mono; -0.005em on sans.

**Geometry**
- Radius: 2 / 3 / 4 px. Most surfaces 0. Never above 4.
- Row height: 22–24 px. Padding: 4 / 6 / 8 px.
- Borders: 1px hairlines, single color, no double-strokes. Use border to separate, never shadow.
- Shadows: none on internal panels. One soft shadow allowed on a top-most overlay.
- Gradients: forbidden, except 1-stop status pill backgrounds at 8% alpha.

**Decoration grammar**
- Mandatory: tabular-nums everywhere numbers appear; uppercase column headers at 10px; aligned decimals; sparkline + delta-pair (value + change) as the canonical data atom.
- Mandatory: status as a 1-letter prefix or a 6-px dot, never a full pill.
- Forbidden: rounded buttons, illustration, drop shadows, blur, glow, marketing copy, emoji, photographic imagery, gradient text, large display type.
- Forbidden: any decorative element that doesn't carry data.

**Motion**
- Cell flashes: 120ms background fade on value change (green-up / red-down), then 600ms decay to neutral.
- Hover: instant, no transition.
- Panel transitions: 80–120ms ease-out, opacity + 2px translate max.
- No spring physics. No parallax. No scroll-driven animation.

## Failure mode

Pretending to be a "dashboard" by stacking gradient KPI cards with neon accents, oversized numbers, and a chart per card with no data behind it. Real dense-mono-dark is hostile to decoration: if there's whitespace, it's because the data isn't there yet, not because a designer balanced the composition. The AI tell is generous padding, rounded-2xl panels, and accents used for emphasis instead of signal.

## Best for

- Trading, monitoring, observability, infra ops, financial terminals.
- Tools whose users are paid to read them for hours.
- Audiences that read numbers faster than they read words.
- Power-user IDEs, inspectors, profilers, log explorers.

## Pairs well with

- Shells: `shell-three-column-app`, `shell-top-bar-canvas`, `shell-two-column-app`, `shell-canvas-floating`, `shell-terminal-frame`.
- Aesthetics: `aesthetic-cyberpunk`, `aesthetic-cassette-futurism`, `aesthetic-atompunk` (dark-aero variant), `aesthetic-anti-design`.
