---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-cream-humanist-ui.png
    reason: Style surface UI mockup.
  - src: style-cream-humanist-isolated.png
    reason: Signature surface, isolated.
---
# Cream humanist serif (style)

**Tag:** `style`

**Canonical references:** Aesop, Le Labo, Byredo, Headspace, Tiempos / GT Sectra in editorial commerce.

## Surface treatment

- **Background**: cream `#FBF8F3` / `#F4EDE0` / `#EEEAE0` — **never pure white**.
- **Type ink**: warm dark grey `#544D4B` / `#403A38` — **never pure black**.
- **Greys**: warm, low chroma — `oklch(60% 0.01 60)` to `oklch(40% 0.015 60)`.
- **Accent**: a single warm semantic accent — earth-orange `oklch(60% 0.13 50)`, terracotta `oklch(55% 0.12 35)`, or sage `oklch(55% 0.08 130)`. **Never blue. Never two accents at once.**
- **Type stack**: humanist serif primary (Optima, Tiempos Text, GT Sectra Display, Caslon) for brand / display / body running text + neutral grotesque secondary (Suisse Int'l, Söhne, Maison Neue) for chrome, prices, table labels. Serif does the brand work, sans does the plumbing.
- **Sizes**: 11 / 13 / 15 / 22 / 32 / 48 / 72.
- **Line-height**: 1.5–1.65 body (generous, gentle), 1.1–1.2 display.
- **Radius**: 0 on cards and panels; 2–4px on buttons (and only when needed). **Never the SaaS-default 8px+ pill.**
- **Borders**: hairline `1px solid oklch(50% 0.005 60 / 0.18)` (warm-translucent), used only on table rows, price strips, and ingredient lists.
- **Shadow**: none on artwork or product imagery; a very rare `0 1px 2px oklch(0% 0 0 / 0.04)` on overlay panels only.
- **Gradients**: forbidden. Cream substrate carries the warmth; no gradient washes, no glow.
- **Decoration grammar**: amber/glass product photography is the visual core (Aesop direction). Soft pencil or watercolor illustration is OPTIONAL (Headspace allows it; Aesop forbids it — pick once per project, never both). No icons except small functional glyphs in the chrome.
- **Motion budget**: slow fades only — `0.6–0.9s ease-out`. No spring physics, no hover-pop, no rotation, no parallax, no scroll-jacked reveals. Hovers shift opacity by a few percent, not transform.
- **Voice cue (since it bleeds into the surface)**: restrained sensory phrasing. Never marketing-flat exclamation.

## Failure mode

Cream background + Inter at 14px + system-blue "Add to cart" button + soft 8px drop shadow = warm-washed SaaS. Reaching for a system blue, pure white, a rounded pill, or a hover spring means you've drifted out of the style and into Stripe-cosplay.

## Best for

Skincare, fragrance, wellness, cosmetics, candles and homeware DTC, beverage (natural wine, tea, coffee), hospitality, meditation apps, editorial commerce, slow-living publications.

## Pairs well with

- Shells: shell-centered-column, shell-editorial-broken-grid, shell-hero-stack, shell-masonry, shell-bento-grid (sparingly), shell-two-column-app (for catalogue / journal layouts).
- Aesthetics: aesthetic-anti-design, aesthetic-frutiger-eco, aesthetic-frutiger-tranquil-serenity, aesthetic-solarpunk (restrained variant), aesthetic-cottagecore (when paired with photography, not illustration), aesthetic-coastal-grandmother, aesthetic-dark-academia (with a darker cream-to-bone substrate).
