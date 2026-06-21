---
techniqueId: pointer-spotlight-video
name: Pointer spotlight video (cursor develops the living image)
category: pointer-driven
subCategory: video
role: hero
binding: pointer-xy
medium: video
pairsPrototypes: [recipe-ai-foundry-dark, aesthetic-frutiger-dark-aero, aesthetic-cyberpunk, aesthetic-dark-academia]
notForUseWhen: The hero must be fully legible at first paint (the technique deliberately hides most of the scene), touch-only audiences dominate (no pointer to carry the spotlight), or the video and still cannot be generated from the same frame so the reveal mismatches.
images:
  - src: motion-pointer-spotlight-video-ui.png
    reason: Motion technique UI mockup.
  - src: motion-pointer-spotlight-video-isolated.png
    reason: Signature technique, isolated.
---

# Pointer spotlight video (cursor develops the living image)

A full-bleed video plays underneath a dimmed, desaturated still of its own first frame; a soft radial mask follows the pointer and reveals the living video only inside that circle - the visitor's cursor develops the image like light on photographic paper.

## Motion signature

- Two stacked full-bleed elements: the looping video below, the treated still above (`filter: grayscale(0.85) brightness(0.45)` or a pre-baked treated raster); the still carries a CSS `mask-image: radial-gradient()` HOLE that tracks the pointer.
- Spotlight geometry: ~22vmin radius hard-ish core with a 10vmin feather (`transparent 0%, transparent 55%, black 100%` in the mask gradient) - smaller reads as a flashlight gimmick, larger stops being a spotlight.
- Eased pursuit: mask center interpolates at `0.10` per rAF (~150ms lag) - the light has weight; 1:1 tracking feels like a browser demo.
- On `pointerleave`, the radius eases to 0 over 600ms (ease-in-out) - the image "closes" rather than snapping dark.
- The video underneath loops seamlessly the entire time, so any reveal at any moment shows motion mid-life, never a start.

## Asset generation spec

- **Resolution**: 1920×1080 minimum for BOTH assets; the still is the video's exact first frame (extract it, don't regenerate) so the reveal is pixel-registered.
- **Composition**: distributed life across the frame - embers everywhere, rain everywhere, crowd everywhere - because the visitor samples arbitrary regions; a single-subject composition wastes 80% of the spotlight's territory. Keep one quiet third for UI regardless.
- **Continuity**: seamless loop, fixed camera, constant exposure - any luminance drift makes the still and video diverge over the loop.
- **Duration**: 8-12s seamless loop.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no exposure change, no flicker.

## Interaction binding

```js
const still = scene.querySelector('.still');
let tx = innerWidth / 2, ty = innerHeight / 2, cx = tx, cy = ty, r = 0;
addEventListener('pointermove', e => { tx = e.clientX; ty = e.clientY; r = 1; }, { passive: true });
scene.addEventListener('pointerleave', () => { r = 0; });
(function tick() {
  cx += (tx - cx) * 0.10; cy += (ty - cy) * 0.10;
  const rad = r * 22; // vmin
  still.style.maskImage =
    `radial-gradient(${rad}vmin at ${cx}px ${cy}px, transparent 55%, black 100%)`;
  requestAnimationFrame(tick);
})();
```

- Video element: `muted playsinline autoplay loop preload="auto"` - autoplay dies without muted+playsinline.
- Mobile fallback: spotlight follows a slow autonomous Lissajous path (one full figure ~14s), so touch visitors still see the scene breathe open.

## UI composition rules

- UI sits in the quiet third and is NEVER masked - it lives above both layers at full contrast at all times; only the imagery plays the reveal game.
- Verify type contrast against BOTH states: the dimmed still (resting) and the live video (when the user parks the spotlight under the headline).
- A one-line affordance cue ("move to look closer") may fade out after the first 200px of pointer travel - never persists.

## Example asset prompt template

> Atmospheric film: a rain-soaked neon street at night filling the entire frame edge to edge, droplets running on glass and signs flickering in every region of the frame, fixed camera, locked tripod, constant exposure, seamless loop where the final frame matches the first, left third compositionally calmer for interface, photoreal, 1920x1080, 10 seconds, no text, no watermark, no camera movement, no scene cut, no flicker.

## When to use

- Dark, moody, exploratory heroes - night scenes, labs, archives, machinery - where curiosity is the message.
- Briefs that say "reward the visitor for looking" or "the page should feel discovered, not presented."
- Dark-UI prototypes where a full-brightness video hero would overpower the chrome.

## When NOT to use

- Light, airy pages - dimming a bright scene to 45% just looks broken.
- Content-dense viewports where the pointer is busy on UI - the spotlight fights every hover.
- When no video provider is wired - degrade to raster + CSS: the treated still over the untreated still, same mask binding; the reveal becomes color/light instead of motion and still earns its keep.

## Performance notes

- Video ≤10MB (it runs the whole session); the mask repaints on the GPU but throttle mask updates to the rAF, never per-event.
- Pause the video and the rAF when off-screen (`IntersectionObserver`).
- `prefers-reduced-motion`: show the UNTREATED still, no mask, no video - the scene resolves to a clean photograph.

## Pairs with (prototype slugs)

- `recipe-ai-foundry-dark`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-cyberpunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference - spotlight revealing live neon rain inside the dimmed still, headline untouched in the quiet third -->
