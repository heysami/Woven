# Desktop OS metaphor shell

**Tag:** `[portfolio · draggable windows · spatial clutter]`

## Structure

The page IS a desktop: a wallpapered surface strewn with draggable windows, file icons, sticky notes, and media players — content lives inside the windows.

- Full-viewport "desktop" ground: wallpaper, subtle texture, or live scene
- 4-12 window objects: project windows, an "about.txt", a music player, folder icons, image viewers — each with title bar + close/min affordances
- Windows are draggable; z-order rises on focus; some start minimized to taskbar/dock
- A menu bar or dock anchors navigation (the one fixed element)
- Optional: right-click context menu easter eggs, trash can, clock
- Deliberate initial scatter — composed chaos, art-directed positions per breakpoint

## Macro proportions

Windows 280-560px wide; never let one window exceed ~50vw (it stops reading as a desktop). 15-30% of wallpaper stays visible at all times. Initial layout is hand-placed, not grid-snapped.

## Density

Medium-high visual, low informational — each window holds ONE small thing. Long content gets a scrollbar INSIDE its window, never page scroll.

## Mandatory interactions

Drag with momentum-free 1:1 follow; focus brings to front; close/minimize actually work (minimize to dock with animation). Double-click icons to open windows. Keyboard: Tab cycles windows, Esc closes. Mobile fallback: windows become a vertical card stack (drag disabled) — never ship broken dragging on touch.

## Forbidden

Page scroll as the primary axis (the desktop is the viewport). Real OS chrome cloned pixel-perfect (evoke, don't counterfeit). More than one window auto-opening on load. Windows the user can drag fully off-screen and lose.

## Best for

Personal portfolios with playful registers, creative-studio sites, music/zine drops, retrospective "my computer in 2009" pieces, Y2K/vaporwave-adjacent briefs that want interactivity beyond collage.

## Pairs well with

Style: skeuomorphism (window chrome), pixel-bitmap (retro OS), raster-cutout. Aesthetic: y2k-myspace, vaporwave (Win95 chrome variant), cassette-futurism, frutiger-aero (Vista variant). Shell kin: `shell-canvas-floating` (the professional cousin), `shell-scrapbook-substrate` (the analog cousin).
