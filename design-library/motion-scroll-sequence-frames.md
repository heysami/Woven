---
techniqueId: scroll-sequence-frames
name: Scroll-sequence frames (canvas-scrubbed still sequence)
category: scroll-driven
subCategory: raster-sequence
role: product
binding: scroll-progress
medium: raster-sequence
pairsPrototypes: [recipe-bento-marketing, recipe-devtools-marketing, recipe-ai-foundry-dark, aesthetic-frutiger-aero]
notForUseWhen: The motion is continuous atmosphere (smoke, water, weather) - frame-to-frame generation can't hold fluid continuity; or the budget can't carry 40+ image generations for one section.
images:
  - src: motion-scroll-sequence-frames-ui.png
    reason: Motion technique UI mockup.
  - src: motion-scroll-sequence-frames-isolated.png
    reason: Signature technique, isolated.
---

# Scroll-sequence frames (canvas-scrubbed still sequence)

40-120 generated stills are preloaded and drawn to a full-bleed `<canvas>`, the frame index driven by scroll progress through a pinned section - the classic AirPods pattern, and the reliable substitute wherever video `currentTime` seeking is too janky to ship.

## Motion signature

- No video element at all: scroll progress picks `frame = round(progress * (N - 1))` and the rAF loop blits that image to canvas - seeking is O(1) and frame-exact on every browser, which is the entire reason this technique exists.
- Eased index: `current += (target - current) * 0.15` per rAF, rounded at draw time - the sequence carries slight momentum without ever showing a half-frame.
- 60-90 frames over 200-300vh of pinned runway is the sweet spot: below 40 frames the motion strobes; above 120 the preload cost outweighs the smoothness gain.
- Bidirectional and instant in both directions - unlike video, reverse scrubbing costs nothing.
- Draw only when the rounded index changes; a static scroll position burns zero paint.

## Asset generation spec

- **Resolution**: every frame 1920×1080 minimum, edge-to-edge, identical dimensions across the set - one mismatched frame shifts the whole canvas for one tick.
- **Composition**: subject anchored on one third with the opposite third quiet, held in ALL N frames; spot-check frames 1, N/4, N/2, 3N/4, N before accepting the set.
- **Continuity strategy**: each frame is one visual-orchestrator sub-dispatch sharing a single base prompt; only a continuity clause varies - "frame N of M of a continuous 180-degree turntable rotation, rotation at X degrees" with X interpolated per frame. Lock the seed across the whole set and keep sampler/steps identical; describe lighting, lens, and background EXACTLY the same in every dispatch.
- **Frame count**: 40 (simple arcs) to 120 (long pins); name files zero-padded (`frame-0001.webp`) so ordering is mechanical.
- **Negative prompt** (every frame): no text, no watermark, no letterboxing, no background change, no lighting change, no camera move, no style drift.

## Interaction binding

```js
const N = 72, imgs = [], ctx = canvas.getContext('2d');
for (let i = 0; i < N; i++) {
  imgs[i] = new Image();
  imgs[i].src = `frames/frame-${String(i + 1).padStart(4, '0')}.webp`;
}
let target = 0, current = 0, drawn = -1;
addEventListener('scroll', () => {
  const r = pinWrap.getBoundingClientRect();
  target = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
}, { passive: true });
(function tick() {
  current += (target - current) * 0.15;
  const i = Math.round(current * (N - 1));
  if (i !== drawn && imgs[i].complete) { ctx.drawImage(imgs[i], 0, 0, canvas.width, canvas.height); drawn = i; }
  requestAnimationFrame(tick);
})();
```

- Preload all frames before enabling the pin; show frame 0 as a plain `<img>` until the set is warm, then swap the canvas in.
- Canvas sized to device pixels (`canvas.width = clientWidth * devicePixelRatio`) or the stills go soft on retina.

## UI composition rules

- Copy sits in the quiet third shared by all frames; copy blocks may swap at frame milestones (e.g. frame 24 / 48) exactly as in scroll-scrub-rotation.
- Because frames are stills, any single frame can be promoted to the section's social/OG image - pick the most legible one, not frame 0.
- A hairline progress bar tied to the frame index helps the pin read as a sequence rather than a stuck page.

## Example asset prompt template

> Frame 37 of 72 of a continuous 180-degree turntable rotation: a white wireless earbud case on the right third of frame, rotation at 91 degrees, fixed camera, locked tripod, constant soft studio lighting, seamless background exactly #f5f5f7, large empty negative space on the left third, photoreal, 1920x1080, identical lighting and framing to all other frames in the sequence, no text, no watermark, no letterboxing, no style drift.

## When to use

- Product turntables and exploded-view arcs where video seeking stutters on target hardware (notably long-GOP files on low-end Android).
- The mandated no-video fallback for scroll-scrub-rotation and scroll-scrub-journey when no video provider is wired.
- Sequences needing frame-exact copy sync - milestones land on integers, not seek approximations.

## When NOT to use

- Fluid, organic motion (fabric, liquid, hair) - per-frame generation shimmers; use a real video scrub.
- Mostly-mobile audiences on slow networks - 72 frames × ~80KB ≈ 6MB of images before the section works.
- Single-framing sections - one still plus scroll-pinned-transform delivers the same weight for one generation.

## Performance notes

- Budget ~60-100KB per WebP frame (quality 80); 72 frames ≈ 5-7MB - comparable to a video, but cache-friendly and seek-perfect.
- Decode ahead: call `img.decode()` on the next ±3 frames around the current index to avoid first-draw jank.
- `prefers-reduced-motion`: unpin and show the final frame as a static `<img>`; skip the preload of all other frames entirely.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-devtools-marketing`
- `recipe-ai-foundry-dark`
- `aesthetic-frutiger-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference - mid-sequence frame on canvas with copy in the shared quiet third -->
