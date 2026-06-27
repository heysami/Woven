---
techniqueId: mouse-scrub-orbit
name: Mouse-scrub orbit (object turns on a turntable arc)
category: pointer-driven
subCategory: video
role: product
binding: pointer-x
medium: video
pairsPrototypes: [recipe-bento-marketing, recipe-devtools-marketing, style-bold-display, aesthetic-cassette-futurism]
notForUseWhen: The subject has a face or front that should "look" at the visitor (use mouse-scrub-look), the object is flat or symmetric so rotation reads as nothing, or the section is touch-dominant with no gyro fallback budgeted.
images:
  - src: motion-mouse-scrub-orbit-ui.png
    reason: Motion technique UI mockup.
  - src: motion-mouse-scrub-orbit-isolated.png
    reason: Signature technique, isolated.
---

# Mouse-scrub orbit (object turns on a turntable arc)

A full-bleed video of a product rotating ±30-45° on a turntable is paused and SCRUBBED by pointer-x - the object presents its angles to the visitor like a salesperson turning a watch under the light, the sibling of mouse-scrub-look for things instead of faces.

## Motion signature

- The video never plays linearly. `video.pause()` on load; `pointermove` maps `clientX / innerWidth` → `currentTime = progress * duration`, where t=0 is full-left rotation and t=end is full-right.
- Keep the arc tight: ±30-45° total. A full 360° turn scrubbed across one screen width spins too fast per pixel and shows the unlit back of the object.
- Eased pursuit: `current += (target - current) * 0.07` per rAF (~250ms lag) - the object follows the cursor's lead like mass on a bearing, never snaps.
- Idle return: pointer rest >4s or `pointerleave` → ease `target` back to 0.5 (the hero three-quarter angle) over ~2s.
- Generation prompt and binding must agree: one continuous rotation, fixed camera, constant lighting - any cut or light shift breaks the turntable illusion.

## Asset generation spec

- **Resolution**: 1920×1080 minimum; MP4 (H.264) + WebM, dense keyframes (`-g 12` or lower) - constant seeking on sparse keyframes snaps visibly.
- **Composition**: object anchored on one third (left or right per the storyboard's UI counterweight), edge-to-edge background, the opposite third a deliberate quiet zone for headline + CTA across EVERY frame of the arc.
- **Continuity**: ONE continuous turntable rotation, full-left at t=0 to full-right at t=end, pivot through the hero angle at midpoint; fixed camera, locked lighting, no reflections that jump.
- **Duration**: 4-6s - the clip is a rotation axis, not a film.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no zoom, no lighting change.

## Interaction binding

```js
const v = scene.querySelector('video');
v.pause();
let target = 0.5, current = 0.5, idleTimer;
addEventListener('pointermove', e => {
  target = e.clientX / innerWidth;
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { target = 0.5; }, 4000);
}, { passive: true });
(function tick() {
  current += (target - current) * 0.07;
  if (v.duration) v.currentTime = current * v.duration;
  requestAnimationFrame(tick);
})();
```

- Mobile fallback: `deviceorientation.gamma` mapped to the same 0-1 axis (behind the standard gyro gate); else a slow autonomous 12s ping-pong scrub so the object never sits dead.
- `preload="auto"` is mandatory - scrubbing an unbuffered clip stalls mid-turn.

## UI composition rules

- UI lives in the generated quiet zone opposite the object; the object's widest silhouette (the extremes of the arc) defines the boundary, not the hero pose.
- Check type contrast at t=0, t=0.5, t=1 - a glossy product throws different highlights at each angle.
- Keep UI static; the contrast between still type and the turning object IS the effect. Spec line ("titanium / 38g / IP68") may sit in the quiet zone but never tracks the rotation.

## Example asset prompt template

> Product film: a brushed-aluminum headphone on an invisible turntable, anchored on the right third of frame, rotating smoothly from 40 degrees left to 40 degrees right of its front face in one single continuous motion, fixed camera, locked tripod, seamless dark studio backdrop, soft constant key light, large empty negative space on the left third, photoreal, 1920x1080, no cuts, no zoom, no text, no watermark, no lighting change.

## When to use

- Hardware / device / packaging sections where the side profile sells (watches, audio gear, bottles, controllers).
- Briefs that say "let them turn it over in their hands" without a 3D engine.
- Product roles inside marketing pages where mouse-scrub-look is already spent on the hero.

## When NOT to use

- Faces or characters - gaze-tracking (mouse-scrub-look) is the stronger read.
- Objects with no depth cues (flat cards, screens dead-on) - rotation reads as warping.
- When no video provider is wired - degrade to a 25-40 frame raster sequence scrubbed by pointer-x (same prompt, "frame N of 32, object rotated X degrees" per frame).

## Performance notes

- One video element, ≤8MB target; `poster` from the midpoint hero frame.
- Pause the rAF loop when off-screen (`IntersectionObserver`); kill the idle timer too.
- `prefers-reduced-motion`: freeze at the hero angle (t=0.5), disable scrub entirely.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-devtools-marketing`
- `style-bold-display`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference - product mid-arc on the right third with spec copy in the quiet zone -->
