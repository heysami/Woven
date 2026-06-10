---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-aero-ui.png
    reason: Generated UI mockup committing this aesthetic's vocabulary at a usable density — palette, type tone, decoration motifs in context.
  - src: aesthetic-frutiger-aero-isolated.png
    reason: Isolated subject sample — the aesthetic's signature motif / texture / illustration treatment on a neutral background.
---
# Frutiger Aero (aesthetic)

**Tag:** `aesthetic-frutiger-aero`

**Canonical references:**
- Windows Vista / 7 Aero (2006–2009) — translucent chrome over photographic wallpapers, the canonical glass window
- iOS 1–6 Springboard (2007–2013) — glossy lozenge icons, linen, status-bar humanism
- Nintendo Wii Menu (2006) — friendly grouped tiles on cool grey, optimistic chime
- Skype pre-2011 — cloud-and-sky brand world, warm-corporate voice
- TomTom GO / Google Earth — data rendered onto a real photographed planet, not a flat map

## Cultural identity

A late-2000s consumer-technology optimism: the post-Y2K, pre-flat era (roughly 2004–2013) when computing finally felt warm, watery, and lived-in. Vista shipped, the iPhone arrived, the Wii won the living room. The shared mood was "technology has joined nature": sky, water, grass, fish, dolphins, koi, bokeh, lens flare — paired with refractive glass surfaces and humanist sans typography.

Spiritually it's the inverse of both Brutalism and Flat: surfaces want to feel **inhabitable** rather than informational. A button is a wet object you could touch. A panel is a fogged pane over a real sky. The aesthetic is unapologetically corporate-optimistic — Microsoft, Apple, Nintendo, Skype, Sony Ericsson — but the warmth came from photography and atmospheric light, not from grit.

**Raster is the law of the land.** Pure-CSS Frutiger Aero is Aurorism in disguise. Before drawing, follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree: (1) check the harness for image-generation MCPs via `ToolSearch`; (2) `WebFetch` from public-domain archives; (3) check project assets; (4) ask the user; (5) if all fail, switch aesthetic rather than fake it in SVG.

## Palette anchor

Sky, water, grass — never sepia, never paper-white.

- Anchor blue `#0689e4`
- Deep blue `#0032db`
- Sky `#6fd7ec`
- Ice `#9ceff2`
- Grass green `#71ab23`
- Amber accent `#fbb905` (status only, never primary)

Greys are warm-blue-tinted, never neutral. Body ink sits around `oklch(22% 0.02 240)` — never `#000`.

## Decoration motifs

Choose ONE atmospheric motif per page and commit:

- Bubbles rising (foreground sharp + background blurred for depth)
- Water droplets on glass
- A single dolphin or koi silhouette
- Grass blades along the bottom edge
- Aurora bokeh
- Lens flare in one corner

Photographic or carefully-3D-rendered only. **Vector dolphins forbidden.** Layering depth (one motif near, one far) beats piling five motifs on top of each other.

Typography is single-family humanist sans — Segoe UI, Lucida Grande, Myriad, Frutiger — with open apertures on a / c / e / s. No mono, no serif: this aesthetic does not code-switch.

## Voice register

Warm-corporate optimistic, full sentences, contractions allowed. "Welcome back, Sarah." "Your photos are ready to share." "Sign in to your account." Never terse-technical, never ironic, never lowercase-Linear. The era believed in the customer.

## Failure mode

- `backdrop-filter: blur()` over a flat grey page with no photographic plate to refract — there is nothing for the glass to be glass *of*
- Button highlight covering the full button height instead of the canonical top 45% — the wet-button gloss collapses into a generic gradient
- Geometric sans (Inter, Poppins, Geist) instead of humanist — the warmth dies instantly
- AI-generated vector dolphins / fish pasted into corners (Demopoulos: "ruins the aura")
- Pure-black text on pure-white cards instead of warm-blue-tinted surfaces
- Modern `0 8px 24px` floating-card shadows instead of period-correct convex `inset 0 1px 0 white` + `0 1px 3px black`
- More bubbles to compensate for a missing photographic plate — the plate is non-negotiable

## Best for

- Nostalgic consumer launches — music players, photo apps, messaging
- Mid-2000s product-anniversary microsites
- Kids' and family software
- Weather, travel, and mapping apps with real-place imagery
- Eco-tech and sustainability brands (blue + green + nature is exactly the brief)
- Music-discovery sites with album-art-as-backdrop

## Pairs well with

- Shells: `shell-mobile-app`, `shell-bento-grid`, `shell-hero-stack`, `shell-canvas-floating`, `shell-top-bar-canvas`, `shell-centered-column`, `shell-two-column-app`
- Styles: `style-glassmorphism`, `style-aurorism`, `style-skeuomorphism`, `style-holographic`, `style-liquid-glass`
