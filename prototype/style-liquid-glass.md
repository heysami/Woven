---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-liquid-glass-ui.png
    reason: Style surface UI mockup.
  - src: style-liquid-glass-isolated.png
    reason: Signature surface, isolated.
---
# Liquid Glass / Liquidism (style)

**Tag:** `style-liquid-glass`

**Canonical references:** Apple HIG Materials; WWDC25 "Meet Liquid Glass"; Linear's adaptation; visionOS Glass Materials; Lickability/Halide iOS 26 patterns.

> **Raster required:** glass needs a saturated, busy content layer (photo, map, video, multi-stop gradient) underneath to refract. On a flat white page, Liquid Glass reads as fogged plastic. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

## Surface treatment

**Color / tokens.** Glass surfaces are computed, not painted — pull neutrals from the underlying content via blur. Don't set greys explicitly on chrome. Tokens: `--glass-regular: rgba(255,255,255,0.18)` for light scenes, `rgba(20,20,22,0.35)` for dark. System tints reserved for the *active* state of a single control: Blue `#0A84FF`, Indigo `#5E5CE6`, Pink `#FF375F`, Orange `#FF9F0A`, Green `#30D158`. Label colors are the only fixed greys: `rgba(0,0,0,0.85)` / `rgba(255,255,255,0.92)`.

**Type stack.** `-apple-system, "SF Pro Text", "SF Pro Display", "Inter", system-ui`. SF Pro Text below 20pt; SF Pro Display at 20pt+. iOS 26 is bolder than predecessors — titles shifted Regular → Bold, body Regular → Medium. Left-aligned alerts/onboarding.

**Sizes.** Large Title 34/Bold (-0.4), Title 1 28/Bold (-0.36), Title 2 22/Bold (-0.26), Title 3 20/Semibold (-0.2), Headline 17/Semibold (-0.4), Body 17/Regular (-0.4), Callout 16/Regular (-0.32), Subhead 15/Regular (-0.24), Footnote 13/Regular (-0.08), Caption 12/Regular (0). Never below 13pt over glass.

**Line-height.** Body 1.29 (22/17). Display 1.07 (36/34) — tight, because Display is optical-size tuned.

**Radius.** Capsule (`border-radius: 9999px`) for navigation bars, tab bars, primary action buttons — they are pills, not rounded rects. 22px concentric outer / 16px inner for cards; 12px for inline chips; 28px for sheets. Concentric rule: outer minus padding equals inner.

**Borders.** Every glass surface gets a 0.5px hairline outer stroke `rgba(255,255,255,0.30)` (the lens edge) PLUS a 1px inset specular highlight `box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), inset 0 -1px 0 rgba(255,255,255,0.10)` (light catching the top bevel). Increase Contrast mode swaps both for a single solid 1.5px black or white outline.

**Shadow.** Contact shadow only — `box-shadow: 0 1px 2px rgba(0,0,0,0.08), 0 8px 24px -12px rgba(0,0,0,0.18)` plus the inset specular. Never `0 20px 60px` blur clouds. This is not 2021 glassmorphism.

**The refraction recipe.** Regular variant: `backdrop-filter: blur(20px) saturate(180%) brightness(108%)`. Clear variant: `blur(30px) saturate(150%)` plus a 12% black dimming layer. Advanced version layers an SVG `feDisplacementMap scale="20"` (never above 30 — text starts swimming) with `feGaussianBlur stdDeviation="1"` on a chromatic-noise turbulence source, applied **only to chrome shapes, never to text**.

## Decoration grammar

Mandatory: a visible saturated content layer beneath every glass surface (photo, map, multi-stop gradient — never flat white); SF Symbols for every icon, weight matched to the type; the 1px inset white specular rim; the 0.5px hairline outer stroke.

Forbidden: drop shadows over 8px blur; glass nested inside glass (HIG explicitly forbids it); brand color baked into the glass fill; gradient borders; decorative noise textures; skeuomorphic "frosted" gradient overlays that *mimic* refraction instead of computing it; conic-gradient rainbow rims.

## Motion

250ms `cubic-bezier(0.32, 0.72, 0, 1)` (Apple's "smooth" spring) for hover/press. Controls *morph* into each other via FLIP / matched-geometry rather than fade — a tab bar expanding into a search field is one continuous shape. The specular highlight subtly shifts ~2–4px on device tilt or pointer movement (gyro/mousemove driven, never autoplay).

Forbidden: looping shimmer, autoplay shine sweeps, parallax on text, conic-gradient rainbow rotation on the rim.

## Voice (chrome only)

Apple-marketing-clean — single noun labels ("Search", "Library", "Now Playing"), sentence case, no microcopy under buttons, no emoji in chrome, system language in alerts ("Are you sure you want to delete this?" not "Wait! You sure??").

## Failure mode

Blur on a white page (refracts nothing → fogged plastic). Missing the 1px white inset specular (panel reads as a sticker not a lens). Refraction displacement applied to text (illegible). Glass-on-glass-on-glass stacking. Brand color baked into the fill instead of inherited from content. Heavy 2021-era glassmorphism drop-shadow clouds. Conic-gradient rainbow shimmer on the rim. No Reduce Transparency / Increase Contrast fallback.

## Best for

Photo and video apps (Halide, Photos, Apple TV); map and travel interfaces; music and media players where album art does the heavy lifting; visionOS spatial apps; lock-screen widgets; anything where the content is the star and the chrome politely steps aside. Not for dense dashboards, spreadsheets, code editors, or document-first writing tools — Linear correctly stripped refraction for exactly this reason.

## Pairs well with

- **Shells:** shell-mobile-app, shell-canvas-floating, shell-top-bar-canvas, shell-hero-stack, shell-bento-grid, shell-masonry, shell-centered-column
- **Aesthetics:** aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-holographic, aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-solarpunk, aesthetic-positivity-kawaii
