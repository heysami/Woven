---
techniqueId: scroll-entrance-video
name: Scroll-entrance video (asset arrives, then holds)
category: scroll-driven
subCategory: video
role: product
binding: scroll-trigger
medium: video
pairsPrototypes: [recipe-bento-marketing, recipe-devtools-marketing, recipe-scientific-infra-marketing]
notForUseWhen: The section is above the fold on load (there is no scroll-into moment to trigger), or the asset must stay interactive after arrival - this technique ends in a still hold frame.
images:
  - src: motion-scroll-entrance-video-ui.png
    reason: Motion technique UI mockup.
  - src: motion-scroll-entrance-video-isolated.png
    reason: Signature technique, isolated.
---

# Scroll-entrance video (asset arrives, then holds)

A play-once video fires the moment the section scrolls into view: the product slides/rises/unfolds into place and SETTLES on a final hold frame - to the visitor it reads as a static asset that happened to arrive beautifully (the iPhone-17-Pro entrance pattern).

## Motion signature

- Triggered ONCE per page load by `IntersectionObserver` at ~35% visibility; `video.play()`, no loop.
- Ends on the last frame and stays there (`video.pause()` on `ended`, or simply no `loop` attribute) - the hold frame IS the section's resting layout.
- The entrance direction agrees with scroll direction: scrolling down → the asset enters from the bottom or scales up from depth. Entering against scroll feels wrong.
- After the hold, the scene's "always something in motion" duty passes to a secondary layer (specular sweep, ambient particles, type shimmer) - never to the settled product itself.

## Asset generation spec

- **Resolution**: 1920×1080 minimum (2160p preferred for hold-frame crispness - the last frame is stared at).
- **Composition**: the FINAL frame is the layout contract - generate so the settled subject sits exactly where the storyboard anchored it (e.g. center-bottom, right third), with the quiet zone clean for UI in every frame of the entrance.
- **Continuity**: one continuous arrival - object enters from off-frame (bottom/back) and decelerates to a full stop; fixed camera; constant lighting; background matches the page's section background EXACTLY (sample the hex into the prompt) so the video rectangle is invisible.
- **Duration**: 1.5-3.5s. Longer entrances feel like loading.
- **Negative prompt**: no text, no watermark, no camera move, no scene cut, no background drift, no flicker.

## Interaction binding

```js
const io = new IntersectionObserver(([e]) => {
  if (e.isIntersecting && !v.dataset.played) {
    v.dataset.played = '1';
    v.play();
    io.disconnect();
  }
}, { threshold: 0.35 });
io.observe(sceneEl);
v.addEventListener('ended', () => v.pause());
```

- `muted` + `playsinline` are mandatory or autoplay is blocked.
- Poster = FIRST frame (pre-arrival emptiness), so the pre-trigger state looks intentional.
- Re-entry policy: default plays once per page load; storyboard may opt into replay-on-re-enter for gallery contexts.

## UI composition rules

- Headline + copy may pre-exist the arrival (the asset arrives INTO an already-set page) or animate in on `ended` - pick one, never both moving at once.
- UI sits in the quiet zone of the FINAL frame; verify against the hold frame, not the poster.
- If copy appears on `ended`, stagger ≤120ms after the settle - the arrival's deceleration and the type's entrance should read as one gesture.

## Example asset prompt template

> Product film: a matte-black device rises smoothly from the bottom edge of frame and settles motionless at center-bottom, one continuous decelerating motion, fixed camera, seamless background exactly #0b0b0f, soft studio key light, upper half of frame stays empty, photoreal, 1920x1080, 3 seconds, no text, no watermark, no camera movement.

## When to use

- Product reveals inside marketing pages (hardware, devices, packaging, bottles).
- Section openers where one hero object deserves a theatrical arrival.
- Briefs that say "it should feel premium / Apple-like" without ongoing interactivity.

## When NOT to use

- Heroes at the very top of the page - there's no scroll-into moment; use ambient-loop-atmosphere or mouse-scrub instead.
- Assets the user then manipulates (rotate/drag) - use scroll-scrub-rotation.
- When no video provider is wired - degrade to a raster + CSS transform entrance (translateY + scale + blur-out), same storyboard, one generated still of the final frame.

## Performance notes

- ≤5MB target; the clip is short. Preload `auto` only when the section is within 1.5 viewports; `metadata` otherwise.
- The hold frame must be bit-identical to a generated still fallback so reduced-motion can swap it in: `prefers-reduced-motion` shows the final frame immediately, no playback.
- Background-color match is the #1 failure - QA diffs the video edge pixels against the section background.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-devtools-marketing`
- `recipe-scientific-infra-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference - product settled on its hold frame with copy in the quiet zone -->
