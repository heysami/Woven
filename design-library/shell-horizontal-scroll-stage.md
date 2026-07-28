---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-horizontal-scroll-stage-ui.png
    reason: Shell structure UI mockup.
  - src: shell-horizontal-scroll-stage-isolated.png
    reason: Signature structure, isolated.
# Orchestrator hint for the plan gate. NOT a mandate: the gate still proposes
# and the user still decides. It exists because this entry's defining quality
# NEEDS a medium a CSS build cannot reach, and that intent was previously only
# prose no gate could read.
suggestsOrchestrator:
  - motion-studio-orchestrator
suggestsOrchestratorWhy: Full-bleed chaptered panels on a wheel-driven linear track - the same stage-plus-quiet-zone shape, on the X axis.
---
# Horizontal scroll stage shell

**Tag:** `[showcase · horizontal axis · chaptered panels]`

## Structure

Full-bleed horizontal track of chapter panels; vertical wheel/scroll input is translated to X-axis travel.

- Fixed viewport stage (100vw × 100vh, `overflow: hidden`)
- Inner track: N chapter panels laid out in a row (`display: flex`), each 60-100vw wide
- Wheel / trackpad / drag input maps to `translateX` on the track (scroll-jacking is the point here - this is the ONE shell where it's licensed)
- Progress affordance: thin track-position bar, chapter index ("02 / 07"), or named chapter tabs - always visible
- Fixed chrome: logo top-left, menu top-right, progress bottom - chrome never travels with the track
- Optional mixed-axis moments: one panel can release the X-lock and scroll vertically (gallery insert), then re-lock

## Macro proportions

Panels 60-100vw. Content inside each panel max-width 1080px, vertically centered. Gutters between panels 8-16vw so arrival at each chapter reads as an event. Track length sweet spot: 4-8 panels - fewer reads as a carousel, more exhausts the wheel hand.

## Density

Low per panel - one idea per panel (a project, a product, a year, a chapter). The traversal is the experience; cramming a panel kills the rhythm.

## Mandatory interactions

Wheel→X translation with inertial easing (lerp ~0.08-0.12, no instant snap). Keyboard ← → support. Drag/swipe on touch. Panel-arrival triggers (label rise, image settle) per chapter. Deep-link per chapter (`#chapter-3` scrolls the track). Progress indicator updates continuously, not per-snap. `prefers-reduced-motion`: fall back to native vertical scroll with panels stacked.

## Forbidden

Mixed free vertical scroll AND horizontal lock on the same panel (pick the axis per panel). Scrollbars on the track. More than one velocity (no fast-then-slow zones inside a single panel). Hijacking without a visible progress affordance - the user must always know where they are and how much remains.

## Best for

Portfolios and agency project reels, lookbooks, product-line walkthroughs (one product per panel), timelines and anniversary/heritage sites, museum/exhibition chapter tours, annual reports with chaptered storytelling.

## Pairs well with

Style: bold-display, oversized-neo-grotesque, restrained-hairline, raster-cutout. Aesthetic: editorial registers (monochrome-tech-editorial, fashion poster), luxury-cinematic-dark for product reels, vintage heritage stories. Motion library: `scroll-scrub-journey`, `scene-stepper-wipe`, `scroll-speed-ramp`.
