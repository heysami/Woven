# Silk / Chrome Flow (style)

**Tag:** `style-silk-chrome-flow`

**Canonical references:** 2025-26 dark AI-SaaS hero wave (motionsites.ai corpus: Grow, Luminex, Power AI, ClearInvoice, Taskora, Wealth) · Stripe Sessions openers · high-end agency reels

## Surface treatment

ONE iridescent silk ribbon / chrome membrane flows across a near-black field, behind or beneath the hero type. It is a rendered 3D material with specular flow — visible folds, highlights that travel — not a blurred gradient (that's `style-aurorism`). Everything else on the page is severe and achromatic so the ribbon reads as the single living thing.

### Background

- Base: `#050507` – `#0a0a0f` near-black, slight blue or violet cast
- The ribbon occupies the lower or trailing third of the hero — never wallpapering the whole viewport
- Sections after the hero drop the ribbon entirely; at most a thin echo (a 2px iridescent rule) recalls it

### Color

- Ink: `#f4f4f6` headlines, `#9b9ba6` body
- Ribbon material, pick ONE family per project:
  - **Aurora silk**: `#3b6cff` → `#7a4dff` → `#c44dff` (blue-violet)
  - **Rose chrome**: `#ff4d8c` → `#b14dff` → `#3b2a66` (pink-magenta)
  - **Petrol silk**: `#0fc4d4` → `#2a4dff` → `#0a1033` (cyan-indigo)
  - **Liquid pewter**: `#cfd4dd` → `#6b7280` → `#1a1d24` (achromatic chrome)
- One accent only, sampled FROM the ribbon, used on exactly one CTA

### Type stack

- Display: Inter/Geist/Söhne 500-600, tight tracking (-2%), 56-88px
- Optional single italic-serif accent word inside the headline (see `style-editorial-italic-accent` — the two styles co-occur constantly in the reference corpus)
- Mono for stat chips and nav meta

### Radius / borders / shadow

- 8-12px cards, 999px pills
- Hairlines `rgba(255,255,255,0.08)`; no drop shadows — the ribbon's specular glow is the only luminance event
- Buttons: 1px hairline ghost + one filled accent

### Decoration grammar

Mandatory:
- ONE ribbon per page, flowing through the hero
- Visible material behavior: folds, specular streaks, depth-of-field falloff at the edges
- Grain overlay 4-6% to kill banding
- Text never sits ON the brightest fold — reserve a quiet dark zone for the headline

Forbidden:
- Two ribbons, or ribbon repeated per section
- Flat mesh-gradient pretending to be silk (no fold = aurorism, different style)
- Rainbow hue sweeps (pick one 2-3 stop family)
- Glassmorphism panels stacked over the ribbon

### Motion

The ribbon flows — slow continuous undulation (20-40s loop), specular highlight traveling along the folds. Implementation: pre-rendered video loop (`motion` medium), WebGL shader (`shader` medium), or a 3D scene (`3d`). Static fallback: a single high-res render frame. Everything else still; type fades in 200ms.

## Failure mode

A blurred purple gradient blob labeled "silk", repeated behind every section, with the headline dropped on the brightest fold so contrast dies, plus glass cards floating on top — reads as a template, not a material. The tell of the real thing: you can see the fabric fold.

## Best for

AI/SaaS dark heroes, fintech wealth platforms, premium agency reels, keynote/launch landings — anywhere "premium intelligence" is the one-word brief and the product is mostly text + screenshots.

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`, `shell-top-bar-canvas`
- Styles: `style-editorial-italic-accent` (the signature pairing), `style-restrained-hairline` for the post-hero sections
- Aesthetics: `aesthetic-luxury-cinematic-dark`, `aesthetic-cosmic-horizon`, `aesthetic-defi-cosmic`
- Media: visual-orchestrator `shader` / `motion` / `3d` drawers own the ribbon asset
