---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-glassmorphism-ui.png
    reason: Style surface UI mockup.
  - src: style-glassmorphism-isolated.png
    reason: Signature surface, isolated.
---
# Glassmorphism (style)

**Tag:** style-glassmorphism

**Canonical references:** macOS Big Sur, iOS 14 Control Center, Apple TV+, visionOS materials, Microsoft Fluent Acrylic

> **Raster required:** a saturated photographic substrate (wallpaper, hero photo, or mesh-gradient) for the glass to refract. Glass on flat white reads as dirty paper. Before drawing, follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Surface treatment

**Substrate (mandatory, beneath every glass surface):** full-bleed saturated gradient `linear-gradient(135deg, oklch(70% 0.18 280) 0%, oklch(65% 0.20 220) 50%, oklch(72% 0.16 340) 100%)` or a real photo at `filter: saturate(1.1)`. Light mode prefers warm-sunset / aurora hues, dark mode prefers deep indigo/violet (`oklch(20% 0.08 270)` → `oklch(25% 0.10 310)`).

**Glass surface - light mode:** `background: rgba(255,255,255,0.12)` (.thin) → `0.22` (.thick).
**Glass surface - dark mode:** `background: rgba(20,20,28,0.45)` (.thin) → `rgba(28,28,36,0.62)` (.thick). Darker glass needs MORE opacity than lighter glass to maintain contrast.
**Tint accent (Fluent-style):** `color-mix(in oklch, var(--brand) 8%, transparent)` layered under the white wash.

**Greys (vibrancy-tinted, never solid):** primary ink `rgba(255,255,255,0.95)` on dark glass / `rgba(15,15,20,0.92)` on light glass; secondary `0.65`; tertiary `0.40` - Apple's three-tier vibrancy scale.

**Accent:** a single saturated brand color visible THROUGH the glass from the substrate; on-glass UI accents use `oklch(70% 0.18 250)` system-blue or platform tint at full saturation - glass desaturates everything, so accents must be vivid to survive.

**Type stack:** SF Pro Display / SF Pro Text (Apple), Inter (web fallback), Segoe UI Variable (Fluent). Body text on glass is bumped one weight - body uses **Medium not Regular**, titles use **Bold not Semibold**, tracking widened `+0.005em` - because blur softens letterforms.

**Sizes:** 11 / 13 / 15 / 17 (body) / 22 / 28 / 34 / 48 (display) - iOS scale.
**Line-height:** 1.3 body, 1.1 display (tight - glass favours compact label-like text, not long-form prose).

**Radius - continuous corners only:** `border-radius: 16px` on cards, `22px` on sheets, `28px` on iOS-style modals, `9999px` on Control Center pills/toggles. Use `--apple-squircle` CSS or elliptical `border-radius: 28px / 32px` for the superellipse look. Never 4-6px SaaS radius - that's the AI tell.

**Borders - mandatory:** `border: 1px solid rgba(255,255,255,0.35)` on the top + left edge of every glass panel (catches light); often implemented as `box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.5), inset 0 0 0 1px rgba(255,255,255,0.18)` for a brighter top-edge highlight and a dimmer wrap-around.

**Shadow:** soft, large, low-opacity - `0 8px 32px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.08)`. Never the sharp Material `0 1px 2px` - glass casts diffuse drop shadows like a real frosted panel.

**Backdrop-filter recipe - the load-bearing line:**
- `.thin` (chips, toggles): `backdrop-filter: blur(12px) saturate(140%)`
- `.regular` (panels, navbars): `backdrop-filter: blur(24px) saturate(180%)`
- `.thick` (modals, sheets): `backdrop-filter: blur(40px) saturate(160%)`

Always include the `-webkit-backdrop-filter` twin. **The `saturate(160-180%)` boost is non-negotiable** - without it the blur drains colour and the glass looks like grey gauze. `@supports (backdrop-filter: blur(1px))` fallback substitutes `rgba(28,28,36,0.85)` solid.

**Optional noise:** `background-image: url("data:image/svg+xml,<noise>")` at 3-5% opacity over the glass - Fluent's secret weapon for masking blur banding; visionOS includes it implicitly.

**Motion:** spring-easing `cubic-bezier(0.32, 0.72, 0, 1)` (iOS standard) at 0.35-0.5s for panel entrance; sheets slide up from bottom; modals scale 0.96 → 1.0 + fade; hover-tint shifts opacity by 0.05 over 0.18s. **No parallax tilt, no shine sweep, no chromatic-aberration animation** (TikTok-glass AI tells). Respect `prefers-reduced-motion: reduce` by killing all spring and falling back to 0.15s opacity-only.

**Decoration - mandatory:** the 1px top-edge highlight border; the saturated substrate visible through every panel.
**Forbidden:** stacked glass-on-glass (more than 2 z-depths of blur compound to mush); glass on flat white pages; glass cards as primary form-input substrate; sharp shadows; gradients painted ON the glass surface (gradients belong on the substrate beneath); border-radius < 12px on cards.

## Failure mode

Backdrop-blur over a flat `#fff` page with no saturated substrate (reads as dirty paper) + uneven blur values across sibling panels + missing the 1px inset white top-edge border + body text directly on glass with no vibrancy backing failing WCAG against bright wallpaper sections + 6-8px SaaS radius instead of 16-22px continuous-corner. Apple-tasteful glass always has SOMETHING saturated to refract through, the same blur recipe everywhere, the highlight border lit on top, and text either backed by a vibrancy chip or set in Medium/Bold weight to survive.

## Best for

iOS/iPadOS/macOS/visionOS-feeling app chrome, Control Center / Notification Center / Now-Playing widgets, lock screens, weather apps, music players, mindfulness apps, hotel & airline check-in flows, premium-streaming overlays (Apple TV+, Disney+), smart-home dashboards, AR/spatial UI, premium SaaS settings sheets and command palettes - anywhere a saturated photographic / cinematic substrate already exists and a translucent overlay reads as "lifted from the content beneath."

## Pairs well with

- **Shells:** shell-mobile-app, shell-canvas-floating, shell-top-bar-canvas, shell-bento-grid, shell-hero-stack, shell-three-column-app, shell-two-column-app
- **Aesthetics:** aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-solarpunk, aesthetic-positivity-kawaii
