---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-cosmic-horizon-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-cosmic-horizon-isolated.png
    reason: Signature motif, isolated.
---
# Cosmic Horizon (aesthetic)

**Tag:** Orbital-frontier tech (NASA/SpaceX webcast frames; Starlink coverage maps; The Blue Marble / Earthrise photography; 2025-26 dark-SaaS "planet horizon" hero wave)

**Canonical references:**
- *Earthrise* (Apollo 8) and *The Blue Marble* - the founding images: a planet's limb glowing against void.
- SpaceX launch webcast UI - telemetry chrome over orbital cinematography.
- Starlink / Planet Labs marketing - constellation-over-Earth as product shot.
- motionsites.ai corpus: WISA Space, Bloom AI, Apex, Planet Orbit, Weblex (×7 in one showcase crop).

## Cultural identity

The 2020s "orbital frontier" register: photoreal space as the stage for engineering ambition. Unlike `aesthetic-defi-cosmic` (mystic-crypto nebulas, tarot energy) this is NASA-photoreal and operational - the planet is real, the satellites are hardware, the glow is atmosphere scattering, and the UI floating above it is mission telemetry. The mood is awe with competence: "we operate at planetary scale, calmly."

The defining gesture is the **planet limb** - a horizon arc entering from a corner or the bottom edge, atmosphere rim-glow tracing it, content set in the black above.

**Palette anchor:** void black `#020308` - `#06080f`, atmosphere rim `#4da6ff` → `#8fd0ff` (or teal `#39e6c3` / signal green `#aef252` for energy-brands), cloud-lit planet surface blues `#10263f`, ink `#eef2f7`, telemetry muted `#7c8aa0`.

## Motifs / imagery vocabulary

- **One planet limb** per page (hero) - bottom arc or corner crop, never a full centered globe sticker.
- Satellites / spacecraft rendered as hardware (panels, foil, antennae) - photoreal, lit by the planet.
- Atmosphere rim-glow as THE luminance event; everything else near-black.
- Telemetry chrome: mono labels, coordinates, pass times, thin crosshairs - sparse, functional.
- Night-side city lights or aurora as optional texture on the planet surface.
- Stars faint and sparse (real-exposure density), never a dense starfield wallpaper.

**Raster required:** the planet limb and any spacecraft are photoreal renders/photography (`raster-photo` via photo `orbital-space`); a CSS gradient arc reads as a logo, not a planet.

## Voice register

Mission-control calm: short declaratives, planetary-scale numbers stated plainly ("Tracking 4,212 assets across 14 orbits"). Engineering nouns over hype adjectives. Never "to infinity and beyond", never sci-fi pulp.

## Failure mode

Centered cartoon globe + dense starfield + purple nebula gradient + "reach for the stars" copy = pitch-deck clipart. The tell of the real thing: the horizon is CROPPED (you're in orbit, not looking at a marble), the rim-glow is thin and physical, and the rest of the frame is disciplined black.

## Best for

Space/satellite/geo products, global infrastructure and logistics platforms, climate and earth-observation tools, "planet-scale" AI/data platforms, fintech with global-rails positioning.

## Pairs well with

- **Shells:** `shell-hero-stack` (canonical), `shell-scroll-journey-scene` (orbit-to-surface dive), `shell-top-bar-canvas` (telemetry product UI).
- **Styles:** `style-restrained-hairline` (dark), `style-silk-chrome-flow` (aurora-silk family), `style-editorial-italic-accent`, terminal-mono chips for telemetry.
- **Photo:** `orbital-space` (the load-bearing asset). **Sim pairing:** globe.gl / three-globe when the brief needs a LIVE orbital view - that's simulation-orchestrator territory, not a static hero.
