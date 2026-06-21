---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-neumorphism-ui.png
    reason: Style surface UI mockup.
  - src: style-neumorphism-isolated.png
    reason: Signature surface, isolated.
---
# Neumorphism / Soft UI (style)

**Tag:** `style`

**Canonical references:** Alexander Plyuto Skeuomorph Bank 2019, Michał Malewicz / Hype4 articles, neumorphism.io generator, Themesberg Neumorphism UI kit, CSS-Tricks Neumorphism and CSS.

## Surface treatment

The whole page is one tinted-grey canvas. Each zone (card, dial, toggle group) is ONE extruded container; content inside stays flat. Never extrude text, icons, or rows. The softness comes from the surface, not the letterforms.

**Background:** warm putty grey `#E0E5EC` (canonical Plyuto). Acceptable cousins `#ECF0F3`, `#EFEEEE`. Dark mode `#2D3138` with shadows `#1F2226` / `#3B3F47`. NEVER pure `#FFF` or `#000` - both shadows must stay visible.

**Greys / accent:** container fill equals page background exactly (this is the rule). Text `#2D3142` headings / `#5B6172` body / `#8A8FA3` meta. Single muted accent only - slate-blue `#6B7AFF` or dusty coral `#FF6B8A` at ~70% saturation, used as flat fill on the one primary action per screen, never as a gradient.

**Type stack:** Nunito Sans or Inter for UI; SF Pro Rounded acceptable. Tabular figures for the hero numeral. NO serifs, NO display fonts.

**Sizes:** 12 / 14 / 16 / 20 / 28 / 40 (40 reserved for the single big balance number). Icons 20-24px, line-weight 1.5px.

**Line-height:** 1.5 body / 1.15 display / 1.0 for the hero numeral.

**Radius:** 16px small chip, 22px button, 28-32px card, 50% pill / avatar. Anything under 12px breaks the soft-plastic read.

**Borders:** NONE on extruded surfaces - shadows do the work. 1px `rgba(0,0,0,0.04)` hairline only on inset / pressed states, to anchor the recess.

**Shadow - the mandatory dual recipe:**
- Raised: `box-shadow: 9px 9px 16px #A3B1C6, -9px -9px 16px #FFFFFF` (offsets equal, blur ≈ 2× offset, dark shadow always bottom-right implying top-left light)
- Pressed / active: `inset 6px 6px 12px #A3B1C6, inset -6px -6px 12px #FFFFFF`
- SAME light-source angle everywhere on the page. No per-component shadow tuning.

**Decoration grammar:**
- Mandatory: at least one inset element per screen (search field, slider track, dial groove) to prove the technique works in both directions.
- Forbidden: drop shadows on text, gradient fills, glassmorphism blur, photographic imagery, emoji, any element that competes with the implied light source.

**Voice:** calm, declarative, single-noun labels ("Balance", "Send", "Cards"). Copy stays out of the way.

## Motion budget

- Press: 180ms ease-out (raised → inset shadow swap)
- Hover lift: 240ms (shadow offset 9→12px, blur 16→20px)
- Forbidden: sliding gradients, parallax tilt, anything that exposes the 2D illusion.

## Failure mode

Every element extruded into pressed-foam chaos. Pure white / black background killing one shadow. Symmetric shadows with no implied light source. Saturated gradients breaking the monochrome material. Buttons indistinguishable from inputs from static cards. Sharp <12px radii. Per-component shadow tuning that jumps the light source around.

## Best for

Concept fintech dashboards (balance + send/receive cards), smart-home thermostat & lighting controls, meditation / sleep / wellness timers, audio player concepts with circular dials, calculator and budgeting toys - anything monochrome, tactile, low-stakes, where a single hero number sits inside a single soft container.

## Pairs well with

- Shells: shell-mobile-app, shell-centered-column, shell-bento-grid, shell-two-column-app, shell-hero-stack
- Aesthetics: aesthetic-frutiger-tranquil-serenity, aesthetic-positivity-kawaii, aesthetic-frutiger-eco, aesthetic-anti-design
