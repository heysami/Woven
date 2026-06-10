---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-bold-display-ui.png
    reason: Style surface UI mockup.
  - src: style-bold-display-isolated.png
    reason: Signature surface, isolated.
---
# Bold display marketing (style)

**Tag:** `style`

**Canonical references:** Apple.com product pages · Linear marketing site · Vercel feature pages · Stripe Sessions site · Framer marketing

## Surface treatment

Large declarative typography on generously padded surfaces. Each surface is its own self-contained slab — soft radius, distinct background, room to breathe. Display copy carries the page; supporting copy is minimal.

### Palette

- Neutral substrate: `#FBFBFD` (off-white) or `#000000` / `#0B0B0F` (true dark)
- Cell substrates: full-bleed solid colors (`#1D1D1F`, `#F5F5F7`, `#FAFAF7`), brand gradients, or imagery
- Text on light: `#1D1D1F` headings, `#6E6E73` secondary
- Text on dark: `#F5F5F7` headings, `#A1A1A6` secondary
- Accent: a single brand hue per page, used sparingly (`#0071E3` Apple blue, `#5E6AD2` Linear indigo, or one custom)
- Never use more than 2 accent hues on one page

### Type stack

```css
--font-display: "SF Pro Display", "Inter Display", -apple-system, system-ui, sans-serif;
--font-text:    "SF Pro Text", "Inter", -apple-system, system-ui, sans-serif;
--font-mono:    "SF Mono", "JetBrains Mono", ui-monospace, monospace;
```

- Display: 48 / 64 / 80 / 96 / 120 px, weight 600–700, letter-spacing `-0.02em` to `-0.04em`, line-height `1.05`
- Headline: 32 / 40 px, weight 600, letter-spacing `-0.02em`, line-height `1.1`
- Body: 17 / 20 px, weight 400, letter-spacing `-0.01em`, line-height `1.47`
- Caption: 14 px, weight 500, letter-spacing `0`, line-height `1.3`
- Eyebrow / label: 12–14 px, weight 600, letter-spacing `0.04em`, uppercase optional

### Geometry

- Surface radius: `16px` standard, `24px` for larger cells, `32px` for hero slabs
- Padding inside surfaces: `32–48px` typical, `56–80px` for hero
- Borders: avoid hairlines on cells; let the background contrast do the separation
- If borders appear, `1px solid rgba(0,0,0,0.06)` on light or `rgba(255,255,255,0.08)` on dark only

### Shadows & depth

- Default: no shadow — surfaces are flat color slabs
- Optional lift on hover: `0 8px 24px rgba(0,0,0,0.08)`
- Hero product imagery may float with `0 30px 60px -20px rgba(0,0,0,0.25)`
- Never stack multiple shadows; never use neumorphic dual shadows

### Gradients

- Permitted as full-surface backgrounds: smooth two-stop linear or radial
- `linear-gradient(135deg, #0B0B0F 0%, #1D1D2F 100%)` or brand-tinted radial vignettes
- Forbidden: rainbow gradients, harsh stop boundaries, gradient text on body copy

### Decoration grammar

- Mandatory: declarative headline as the loudest element on every surface
- Mandatory: one focal object per surface (product shot, chart, icon, screenshot, gradient)
- Allowed: thin keylines around product imagery, monochrome icons at 24–32px
- Forbidden: drop shadows on text, emoji clutter, decorative dividers, "pills" with gradients, glow effects, sparkles

### Motion budget

- Surface entrance: `opacity 0 → 1` + `translateY(12px → 0)`, duration `600ms`, easing `cubic-bezier(0.22, 1, 0.36, 1)`
- Scroll-linked reveal acceptable using `IntersectionObserver` or `scroll-timeline`
- Hover: surface lifts `translateY(-2px)` over `200ms` ease-out
- Forbidden: parallax tilt on cards, infinite shimmer, bouncy springs, autoplay video without mute

## Failure mode

Every surface gets a different gradient + emoji + shadow stack, the "bento grid" becomes a casino of mismatched cells. Display type is set in a generic Google sans at 32px instead of true display weights at 80px. Bodies become walls of text where one headline should sit alone.

## Best for

Product marketing pages, feature announcements, pricing tables, landing pages for SaaS / hardware / consumer apps, conference sites, changelog showcases.

## Pairs well with

- Shells: `shell-bento-grid`, `shell-hero-stack`, `shell-centered-column`, `shell-top-bar-canvas`
- Aesthetics: `aesthetic-anti-design`, `aesthetic-frutiger-aero`, `aesthetic-frutiger-dark-aero`, `aesthetic-y2k-futurism`, `aesthetic-neubrutalism` (loosely), or no aesthetic (pure product-marketing neutral)
