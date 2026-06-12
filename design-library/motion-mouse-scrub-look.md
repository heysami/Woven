---
techniqueId: mouse-scrub-look
name: Mouse-scrub look (subject follows the cursor)
category: pointer-driven
subCategory: video
role: hero
binding: pointer-x
medium: video
pairsPrototypes: [recipe-neo-grotesque-portfolio, recipe-editorial-magazine, aesthetic-cyberpunk, aesthetic-y2k-futurism, style-oversized-neo-grotesque]
notForUseWhen: The slot is informational (dashboard, docs, data table), the subject has no face/front (abstract texture), or touch-only audiences dominate — pointer-x has no mobile equivalent without a gyro fallback.
images:
  - src: motion-mouse-scrub-look-ui.png
    reason: Motion technique UI mockup.
  - src: motion-mouse-scrub-look-isolated.png
    reason: Signature technique, isolated.
---

# Mouse-scrub look (subject follows the cursor)

A full-bleed video of a subject turning its head (or rotating its front) left-to-right is paused and SCRUBBED by the pointer's horizontal position — the subject appears to watch the cursor, following the visitor around the frame.

## Motion signature

- The video never plays linearly. `video.pause()` on load; each `pointermove` maps `clientX / innerWidth` → `currentTime = progress * duration`.
- Eased pursuit: the scrub target is interpolated (`current += (target - current) * 0.08` per rAF), so the subject lags the cursor by ~200ms — pursuit, not telepathy. Instant 1:1 mapping reads as glitch, not gaze.
- Idle behaviour: when the pointer leaves or rests >4s, drift slowly back to the center frame (the "at ease" pose).
- The illusion REQUIRES the generation prompt and the binding to agree: one continuous motion axis, no cuts, fixed camera.

## Asset generation spec

- **Resolution**: 1920×1080 minimum; H.264/H.265 MP4 + WebM, high keyframe density (`-g 12` or lower) — scrubbing seeks constantly; sparse keyframes make seeks visibly snap.
- **Composition**: subject anchored at one third (left or right per the storyboard's UI counterweight), edge-to-edge background, deliberate quiet zone on the opposite third for headline + CTA.
- **Continuity**: ONE continuous motion across the whole clip — head turns from full-left at t=0 to full-right at t=end. No blinks-as-cuts, no camera move, no lighting change.
- **Duration**: 4–8s is plenty; the clip is a position axis, not a story.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera shake, no scene cut, no zoom.

## Interaction binding

```js
const v = scene.querySelector('video');
v.pause();
let target = 0.5, current = 0.5;
addEventListener('pointermove', e => { target = e.clientX / innerWidth; }, { passive: true });
(function tick() {
  current += (target - current) * 0.08;
  if (v.duration) v.currentTime = current * v.duration;
  requestAnimationFrame(tick);
})();
```

- Mobile fallback: bind to `deviceorientation.gamma` when available (behind the standard gyro gate), else slow autonomous pan loop so the scene never sits dead.
- `preload="auto"` is mandatory — scrubbing an unbuffered video stalls.

## UI composition rules

- UI lives in the generated quiet zone (subject right → UI left, and vice versa). Never center type over the subject's face.
- Type must survive every frame of the scrub — check contrast at t=0, t=0.5, t=1, not just the poster.
- Keep UI static while the subject moves: the contrast between still type and tracking gaze IS the effect.

## Example asset prompt template

> Cinematic studio portrait, a chrome-visored figure centered on the right third of frame, slowly turning their head from far left to far right in one single continuous motion, fixed camera, locked tripod, seamless studio backdrop with soft gradient light, large empty negative space on the left third, photoreal, 1920x1080, no cuts, no zoom, no text, no watermark.

## When to use

- Portfolio / brand heroes where presence and eye-contact are the message.
- Character-led products (avatars, agents, fashion, eyewear, audio).
- Any brief that says "it should feel like it notices you."

## When NOT to use

- Subjects without an obvious front (landscapes, textures) — use pointer-parallax-layers instead.
- Dense pages where the hero shares the viewport with content the pointer is busy on.
- When no video provider is wired — degrade to a 25–40 frame raster sequence scrubbed by pointer-x (same prompt, "frame N of head turn" per frame).

## Performance notes

- One video element, ≤8MB target; provide `poster` from the center frame.
- Pause all rAF work when the scene is off-screen (`IntersectionObserver`).
- `prefers-reduced-motion`: freeze at the center frame, disable scrub.

## Pairs with (prototype slugs)

- `recipe-neo-grotesque-portfolio`
- `recipe-editorial-magazine`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-futurism`
- `style-oversized-neo-grotesque`

<!-- image: sample-1.png -->
<!-- reason: representative reference — subject tracking the cursor with headline in the quiet zone -->
