---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-scroll-journey-scene-ui.png
    reason: Shell structure UI mockup.
  - src: shell-scroll-journey-scene-isolated.png
    reason: Signature structure, isolated.
# Orchestrator hint for the plan gate. NOT a mandate: the gate still proposes
# and the user still decides. It exists because this entry's defining quality
# NEEDS a medium a CSS build cannot reach, and that intent was previously only
# prose no gate could read.
suggestsOrchestrator:
  - motion-studio-orchestrator
suggestsOrchestratorWhy: The shell IS a scrubbed full-bleed media stage: one continuous scene the scroll travels through, copy held in a quiet zone.
---
# Scroll journey scene shell

**Tag:** `[narrative · single continuous scene · scroll-scrubbed]`

## Structure

ONE continuous scene - illustrated, photographic, or 3D - that the scroll position travels through. There are no sections; there are stations.

- Fixed full-bleed scene layer (canvas / WebGL / layered images, `position: fixed`, z-0)
- Tall scroll spacer (400-1200vh) whose progress drives the scene: camera dolly, dive depth, product rotation, time-of-day
- Station overlays: copy blocks that fade/rise in at fixed progress marks (10-20% apart), one thought per station, max ~40 words
- Persistent journey indicator: depth meter, route line, chapter dots, or progress thread - themed to the scene (a depth gauge for a dive, a road marker for a drive)
- Entry hint ("scroll to begin ↓") that fades after first input
- Exit: the journey ENDS somewhere - a final station with CTA / colophon, scene settles to rest

## Macro proportions

Scene is always 100vw × 100vh. Copy stations max-width 480-640px, anchored to the scene's quiet zone (left or right third, never center-blocking the subject). Total journey 30-90 seconds of average scrolling.

## Density

Lowest of all shells. The scene is the content; text is captioning. If the brief needs tables, cards, or forms, this is the wrong shell (or those live on a sibling page).

## Mandatory interactions

Scroll-scrub binding with easing (scene lags scroll by a lerp, never 1:1 jitter). Stations announce themselves (fade + rise ≥300ms). Scene must respond continuously - every scroll tick visibly moves the world, no dead zones. Touch + keyboard equivalents. `prefers-reduced-motion`: replace scrub with stepped scene stills per station. Preload/buffer the scene asset before unlocking scroll (loading veil with progress).

## Forbidden

Section boundaries that reset the scene (it's one world, not slides). Autoplay that moves without scroll input (the user drives). Copy walls. Multiple competing subjects in frame at once. Scrubbing video by `currentTime` without keyframe-dense encoding (judder).

## Best for

Product reveals (macro flight around a watch/shoe/device), brand origin stories, underwater/space/landscape explainers, data-driven documentary pieces, museum single-artifact deep-dives, luxury campaign microsites.

## Pairs well with

Style: restrained-hairline (let the scene carry), serif editorial for station copy. Aesthetic: surreal-dream-stage, luxury-cinematic-dark, bioluminescent-deep, cosmic-horizon, pastoral-serene. Motion library: `scroll-scrub-journey`, `scroll-sequence-frames`, `scene-zoom-through`, `slow-push-zoom`. Orchestrators: this shell is the natural host page pattern for a narrative-experience (nx) slot.
