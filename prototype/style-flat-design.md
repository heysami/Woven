# Flat Design (style)

**Tag:** iOS 7 2013 · Windows 8 Metro 2012 · Spotify 2013 desktop · NN/g flat-design canon · W3Schools Metro palette

**Canonical references:** iOS 7 (2013), Windows 8 Metro (2012), Spotify 2013 desktop, NN/g flat-design articles, Metro tile palette.

## Surface treatment

**Background:** pure `#ffffff` (iOS flavor) or pure `#000000` (Spotify flavor) or one saturated tile color (Metro: `#2d89ef` / `#b91d47` / `#99b433` / `#ff0097` / `#ffc40d` / `#00aba9`). Never a gradient. Never off-white.

**Accent:** one vivid accent does all interactive work — iOS `#007aff`, Spotify `#1db954`, or one Metro tile pick. Flat solid fills only, zero gradients, zero tints.

**Grays:** iOS exactly `#8e8e93` / `#c7c7cc` / `#efeff4`. Dark variant `#1d1d1d` / `#333` / `#666`.

**Semantic:** red `#ff3b30`, green `#4cd964`, orange `#ff9500`.

**Type stack:** Helvetica Neue (iOS 7) or Segoe UI (Metro) or Proxima Nova (Spotify). One family, no secondary — typography does the hierarchy work shadows used to do.

**Sizes:** Metro scale 42 / 20 / 15 / 11 / 9 pt. iOS 7 scale 34 / 28 / 22 / 17 / 15 / 13 / 11 px. Display weight 100-300 (UltraLight / Light). Body weight 400. Never bold body.

**Line-height:** 1.2 for display (tight, big type carries itself). 1.4 for body. Never 1.6+ (reads as web-content, not app).

**Radius:** 0 everywhere for Metro purist, or exactly 4px iOS-style on buttons/inputs, full pill (`border-radius: 999px`) only on tag chips, app icons at iOS 7's superellipse ~22%. Never 8px / 12px / 16px (that reads as Material).

**Borders:** 1px hairline `#c7c7cc` (or 0.5px on retina via `transform: scaleY(0.5)`) for row separators only. Zero borders on buttons. Zero borders on cards because there are no cards.

**Shadow:** none. Not subtle, not `0 1px 2px rgba(0,0,0,0.05)` — none. Depth comes from translucency (iOS 7 frosted nav at `backdrop-filter: blur(20px) saturate(180%)`) or from solid color blocks butting against each other.

## Decoration grammar

**Mandatory:**
- Generous negative space (40-60% of any screen)
- Single-color line icons at 1.5-2px stroke (iOS 7 Glyphs style) or solid silhouette icons (Metro style)
- Large numeric or single-word headlines as the primary visual
- Sections separated by either a 1px hairline or a full-bleed color block

**Forbidden:**
- Gradients, drop shadows, bevels, inner shadows
- Textures, long shadows at 45 degrees
- Faux-3D icons, illustrations of pastel humans, stock photography of smiling teams
- The Flat UI Bootstrap palette (`#1abc9c` / `#2ecc71` / `#3498db` / `#9b59b6` / `#e74c3c`) used as a rainbow
- Card containers with shadows

## Motion budget

- 200-300ms ease-in-out cross-fades and slides
- Push transitions between views at 350ms `cubic-bezier(0.4, 0.0, 0.2, 1)`
- Parallax on the iOS 7 wallpaper at ~10px max
- Forbidden: spring bounces, scale-pop, ripple effects, anything that implies a physical material

## Failure mode

Every element at the same visual elevation so buttons read as labels and inputs read as buttons (the clickability crisis NN/g documented). Helvetica UltraLight at body size on a 1x display (unreadable). Long-shadow icons in an otherwise shadowless UI. Four different blues used across header / CTA / link / icon. Pill CTAs on white cards on white background with no separation. The AI-generated "flat" landing page with a hero of geometric humans.

## Best for

Native mobile OS shells, music / podcast apps where album art is the only image, dashboards and admin tools where data density wins, news readers, transit and weather apps, brand sites for companies that want to read as "software not marketing".

Wrong for content-heavy editorial, e-commerce product detail (kills affordance), anything pitching itself as warm / handmade / premium.

## Pairs well with

- **Shells:** shell-mobile-app, shell-two-column-app, shell-three-column-app, shell-top-bar-canvas, shell-bento-grid, shell-centered-column, shell-hero-stack
- **Aesthetics:** aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-y2k-futurism, aesthetic-corporate-memphis, aesthetic-positivity-kawaii, aesthetic-anti-design
