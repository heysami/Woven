---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-y2k-futurism-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-y2k-futurism-isolated.png
    reason: Signature motif, isolated.
---
# Y2K Futurism (aesthetic)

**Tag:** aesthetic-y2k-futurism

**Canonical references:**
- Apple Aqua Mac OS X 10.0–10.2 — the pulsing default button, gel transport controls, brushed-metal headers
- Sega Dreamcast OS + Sonic Adventure menus — translucent console plates, swirl logos, optimistic boot
- Windows XP Luna by Frog Design — saturated sky desktop, candy taskbar, friendly gloss
- Tomb Raider Last Revelation / Chronicles menus — vector-grid environments and inventory plates
- WinAMP / Sonique skin culture — chrome wordmarks, LCD readouts, blobject media players

## Cultural identity

A roughly 1998–2003 optimistic-technocratic moment when consumer software believed the future had arrived and wanted to look *inhabitable* — translucent plastic, candy chrome, blobject hardware (iMac G3, iPod, Dreamcast). The interface is the protagonist: an OS window, a console pause-menu, a media-player skin floating on a saturated environment that the plastic actually refracts. Tone is welcoming, slightly civic, never ironic.

Not Y2K-Memphis (poster graphics, terrazzo, squiggles — that's a different aesthetic). Not Vaporwave (post-2010 ironic remix). Not Cyberpunk (dystopian, hostile). This is the *sincere* version: the future as a friendly appliance.

## Palette anchor

- Aqua blue `oklch(72% 0.17 235)` — the pulsing default-button blue, the load-bearing accent
- Bondi teal `oklch(70% 0.12 200)` — iMac G3, the era's signature environment
- Ultramarine `oklch(40% 0.18 260)` — Dreamcast / XP-Luna deep sky for chrome to refract over
- Chrome ramp `#e8e8e8 → #c0c0c0 → #6e6e7a → #2a2a32` for mirror-finish wordmarks
- Citrus accents — tangerine `oklch(75% 0.20 55)` and lime `oklch(85% 0.20 130)` (the candy-iMac flavours)

Never neutral white as the base — translucent plastic has nothing to refract over white.

## Decoration motifs

**Mandatory vocabulary:**
- Mirror-finish wordmarks with a horizontal split at x-height, lower half tinted into the environment colour
- At least one blobject — a 3D-rendered translucent capsule, kidney, or pebble shape with inner gloss
- A vector grid receding to a vanishing point, OR a pinstripe field somewhere on the body
- Gel buttons with a highlight band breaking at ~48% (the Aqua recipe, not a flat pill)

**Permitted:** lens flares on chrome edges, swirl logos, low-poly rotating objects in a viewport, LCD readout strips, traffic-light window controls, filled bitmap icons with bevel.

**Forbidden tells:** terrazzo, squiggles, halftone, dot-grids (those are Memphis), Lucide/Feather stroke icons (era used filled icons), neon-strobe motion.

## Voice register

Optimistic technocratic. Sentence case with terminal period, never marketing exclamatory, never lowercase-defiant. System messages address the user as "you" politely.

- "Welcome."
- "Synchronising…"
- "Now Playing"
- "Press START"
- "1 of 12 items"

## Raster requirement

Chrome 3D renders (Cinema 4D / Blender exports), translucent candy-plastic blobjects, lens flares, mirror-finish wordmark renders, and gel-button references generally need raster assets. CSS-only Y2K Futurism collapses into Aurorism-with-chrome-text-shadow.

Before drawing, follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree: (1) check the harness for image-generation MCPs via `ToolSearch`; (2) `WebFetch` from public-domain archives; (3) check project assets; (4) ask the user; (5) if all fail, switch aesthetic rather than fake it in SVG.

## Failure mode

The cheap AI version: one `linear-gradient(45deg, magenta, cyan)` poured across the whole shell, Orbitron everywhere, Lucide stroke icons on pseudo-Aqua pills, a single `backdrop-filter: blur(20px)` standing in for the full plastic recipe, `border-radius: 9999px` on every element with no tier distinction, chrome wordmarks done as `text-shadow: 1px 1px 0 silver` with no horizontal reflection split, a translucent plate sitting on a white page (nothing to refract), and a flat purple "Sign up" CTA in Inter 14px. That is Y2K cosplay.

The tasteful tell: the gel button has **two stacked gradients with the highlight breaking at 48%**, mirror-finish wordmarks have a **horizontal split at x-height with the lower half inverted-and-tinted into the environment**, and the plate sits over a saturated Bondi/ultramarine field that the translucency actually refracts.

## Best for

- Retro tech-product launches and hardware unboxing microsites
- Music-player and DJ apps (the WinAMP/iPod lineage)
- Console-game menus, pause screens, sci-fi optimistic onboarding
- Early-internet revival sites, Dreamcast/iPod/iMac G3 tribute pages
- Any context where the *interface itself* is the protagonist

Not for: poster graphics, magazine covers, editorial layouts (use Y2K-Memphis-loud for that), or anything that wants to feel ironic / post-internet.

## Pairs well with

- **Shells:** shell-top-bar-canvas (the OS window archetype), shell-canvas-floating (console-menu plate on environment), shell-two-column-app (media-player skin), shell-mobile-app (iPod-style device frame), shell-hero-stack (product-launch microsite)
- **Styles:** style-aurorism (mesh-gradient environment for the plastic to refract over), style-glassmorphism (the translucent-plate recipe), style-holographic (chrome iridescence), style-skeuomorphism (gel buttons and bevelled bitmap icons), style-liquid-glass (modern descendant)
