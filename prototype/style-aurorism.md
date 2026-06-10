---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-aurorism-ui.png
    reason: Generated UI mockup showing this style's surface treatment — type, color, shadow, corner, and component register together.
  - src: style-aurorism-isolated.png
    reason: Isolated subject sample — the style's signature surface (component, card, or hero element) on a neutral background.
---
# Aurorism / Mesh-Gradient (style)

**Tag:** `style-aurorism`

**Canonical references:** Stripe · Linear · Vercel · Cron/Notion Calendar · Cosmos

## Surface treatment

Mesh-gradient field appears exactly once per screen behind hero text, never tiled, never repeated section-to-section. The gradient carries all the atmosphere; the rest of the surface is 99% achromatic so the aurora reads as a singular event.

### Background

- Light: `#fafafa` (Vercel) or `#ffffff` (Stripe)
- Dark: `#08090a` true black (Linear)
- Mesh built from 3-4 radial-gradient layers, each fading center-to-transparent over the base

### Color

- Ink: `#061b31` (Stripe) / `#171717` (Vercel) / `#f7f8f8` on dark (Linear)
- Hairlines: `#ebebeb` light or `rgba(255,255,255,0.08)` dark
- Muted text: `#50617a`
- Chromatic stops (pick one set, 3-4 stops):
  - Stripe: `#6ec3f4` sky · `#3a3aff` indigo · `#ff61ab` pink · `#E63946` coral
  - Linear: `#5e6ad2` indigo wash + `#e4f222` acid-lime CTA (reserved for exactly one button)
  - Vercel prism: `#eec32d` · `#ec4b4b` · `#709ab9` · `#4dffbf`
  - Cron: `#b6a8ff` lilac · `#ffb39a` peach · `#a7d3f2` sky
- Each stop fades center-to-transparent — never solid-to-solid

### Type stack

- Display + body: Söhne-var (Stripe), Inter Variable 510/590 (Linear), or Geist Sans (Vercel)
- Stat numerals + code chips: Geist Mono / SF Mono
- No serif, no Poppins

### Sizes

- Display: 56-72px
- H2: 32-40px
- H3: 20-24px
- Body: 16px
- Caption: 13-14px

### Line-height

- Display: 1.0-1.05
- Body: 1.5
- Mono: 1.4

### Radius

- 4px interactive (buttons, inputs)
- 12-16px cards
- 40px gradient containers
- 999px pill chips

### Borders

1px hairlines `#ebebeb` light / `rgba(255,255,255,0.08)` dark — never on top of the mesh, only on cards below it.

### Shadow

One soft lift `rgba(23,23,23,0.06) 0 3px 6px` on cards. The gradient itself replaces shadow as the depth cue — never combine heavy drop-shadows with aurora.

### Decoration grammar

Mandatory:
- `blur(60-100px)` on every gradient blob
- Opacity 0.6-0.85, not 1.0
- SVG grain/noise overlay at 4-8% opacity to kill banding
- Transparent endpoints on every color stop
- White/dark scrim under text so contrast holds

Forbidden:
- Second gradient on the CTA
- Repeated mesh in every section
- Gradient applied to icons or borders
- Emoji
- Glassmorphism cards stacked on top of the mesh

### Motion

Gradient drifts via `12s linear infinite` + `8s linear infinite` counter-rotation (`transform: rotate(1turn) translate(60-100px) rotate(-1turn)`) at most, or a single WebGL minigl noise loop. Everything else still — no parallax, no scroll-jacking, no bouncy springs. Text uses `200ms ease-out` fade-in only.

## Failure mode

Full-saturation rainbow blobs with no transparent falloff, no blur, no grain, repeated behind every section, with Poppins-700 headings and a second gradient on the button — the unmistakable AI mesh-gradient template look.

## Best for

Developer tools, payments and fintech infrastructure, calendar and productivity apps, AI model marketing, design-tool landing pages, and creator-platform homepages where the product is mostly text and screenshots and the gradient carries all the atmosphere.

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`, `shell-bento-grid`, `shell-top-bar-canvas`, `shell-two-column-app`, `shell-three-column-app`
- Aesthetics: `aesthetic-frutiger-aero`, `aesthetic-frutiger-dark-aero`, `aesthetic-frutiger-tranquil-serenity`, `aesthetic-cyberpunk`, `aesthetic-vaporwave`, `aesthetic-solarpunk`
