---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-claymorphism-ui.png
    reason: Generated UI mockup showing this style's surface treatment — type, color, shadow, corner, and component register together.
  - src: style-claymorphism-isolated.png
    reason: Isolated subject sample — the style's signature surface (component, card, or hero element) on a neutral background.
---
# Claymorphism (style)

**Tag:** Coursera 2022 rebrand · Pitch key visuals · Matter app · Aimchess · Meta Horizon Worlds · clay.css by Adrian Bece

**Canonical references:** Coursera 2022 rebrand · Pitch key visuals · Matter app · clay.css by Adrian Bece · Meta Horizon Worlds

## Surface treatment

Soft puffed pastel volumes with the three-shadow clay recipe applied to ONE layer per screen — never clay-on-clay-on-clay. The signature is the dual inset highlight + dark inset shadow that gives surfaces a doughy, pressable feel. Flat chrome surrounds the one clay moment.

**Background:** warm-pastel wash `oklch(97% 0.02 80)` (cream) or `oklch(96% 0.025 240)` (sky); Coursera-sunrise variant `linear-gradient(180deg, oklch(97% 0.03 80) 0%, oklch(95% 0.04 30) 100%)`.

**Color palette:** low-chroma pastels only — lavender `oklch(82% 0.07 290)`, peach `oklch(85% 0.08 50)`, mint `oklch(88% 0.06 160)`, sky `oklch(86% 0.07 230)`, butter `oklch(90% 0.08 90)`. Greys are warm: `oklch(60% 0.01 60)` and `oklch(40% 0.012 60)`.

**Accent:** one full-saturation accent for the primary CTA — purple `oklch(60% 0.18 280)` or orange `oklch(65% 0.16 40)`. Never neutral grey CTAs.

**Type stack:** Nunito 700/800 for display + Inter 400/500 for body and chrome. Sora is the alternative display face. Both must have round terminals — one serif anywhere = drift.

**Sizes:** 12 / 14 / 16 / 20 / 28 / 40 / 56.
**Line-height:** body 1.55, display 1.15, button 1.

**Radius:** graded — buttons 12px, inputs 14px, cards 20–24px, clay illustrations 32–48px (only the decorative clay layer goes above 24px). Pills 999px stay flat, never clay.

**Borders:** none on clay surfaces (the inner highlight does the edge work). 1px `oklch(90% 0.01 80)` hairlines on flat chrome rows and table dividers.

**Shadow (the clay recipe):** applied to the *one* clay surface per screen.
```
box-shadow:
  8px 8px 16px 0 oklch(50% 0.04 280 / 0.18),
  inset -6px -6px 12px 0 oklch(45% 0.06 280 / 0.22),
  inset 8px 8px 12px 0 oklch(100% 0 0 / 0.45);
```
Rules: outer offset = inner offset, blur = 2× offset, outer tinted with the surface hue (not black). Flat chrome cards get a single soft `0 1px 2px oklch(0% 0 0 / 0.04)` and nothing more.

## Decoration grammar

- Mandatory: exactly ONE clay scene per page (hero blob group, mascot, or empty-state) + rounded-corner SVG icons at 1.75–2px stroke with round endcaps.
- Forbidden: 3D-emoji icons used functionally, clay-on-every-card, gradient borders, neon glows, glassmorphic overlays mixed in, clay extended to dark mode.

## Motion

Soft squash on hover: `transform: scale(1.03) translateY(-2px)` with `transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)` — one gentle overshoot, never a bouncy spring.

Illustration bob (hero clay artwork only, never UI): `@keyframes bob { 50% { transform: translateY(-6px) } }` at 3s ease-in-out infinite.

## Failure mode

Every container puffed instead of clay reserved for one layer + saturated chroma 0.20+ pastels where the canon uses 0.04–0.08 + uniform 32–50px radius on buttons and cards alike + the dark bottom-right inset shadow missing (so clay reads as a flat pastel pill with a glow) + drop shadow blackened to `rgba(0,0,0,0.25)` on white instead of tinted to the surface hue + Fredoka One / Baloo / Comic Sans display instead of Nunito + Microsoft Fluent / Apple memoji 3D emoji used as functional icons + clay extended to dark mode (where the inset highlight stops reading and it collapses into neumorphism).

## Best for

Edtech and learning apps (Coursera, Duolingo-adjacent, Khan-style), kids' apps, wellness and meditation, habit trackers, gamified onboarding, deck/presentation marketing pages (Pitch), wholesome consumer DTC (oat milk, plant care, sleep), conference/event microsites where one mascot carries the brand.

## Pairs well with

- Shells: shell-centered-column, shell-two-column-app, shell-mobile-app, shell-hero-stack, shell-bento-grid
- Aesthetics: aesthetic-positivity-kawaii, aesthetic-frutiger-eco, aesthetic-frutiger-tranquil-serenity, aesthetic-corporate-memphis, aesthetic-frutiger-bright-tertiaries
