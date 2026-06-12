---
techniqueId: scene-crossfade-hold
name: Scene crossfade hold (worlds dissolve, each one breathes)
category: scene-choreography
subCategory: video
role: transition
binding: wheel-step
medium: video
pairsPrototypes: [recipe-aurora-marketing, recipe-warm-restraint, recipe-restrained-ai-marketing, style-aurorism, aesthetic-dreamcore]
notForUseWhen: Scenes are hard-edged or graphic (UI screenshots, type-led boards) — a dissolve between crisp rectangles reads as a rendering bug; use scene-stepper-wipe. Also wrong when scenes must feel causally connected — crossfade says "elsewhere", not "therefore".
---

# Scene crossfade hold (worlds dissolve, each one breathes)

Each full-screen scene is its own ambient video loop; advancing one wheel-step crossfades the outgoing world into the incoming one over 800–1200ms — held scenes keep breathing on their internal loop, and both videos play simultaneously ONLY during the cross.

## Motion signature

- While held, a scene plays its own 6–10s seamless ambient loop (slow drift, atmosphere, no event) — the piece is never still.
- On step: incoming video starts from t=0 at opacity 0, fades to 1 over 800–1200ms with `ease-in-out`; outgoing fades to 0 on the same clock, then `pause()` + unload.
- 1000ms is the default; go 800ms for bright/energetic worlds, 1200ms for dark/atmospheric ones. Under 600ms reads as a cut, over 1500ms as a loading state.
- Input debounce equals the cross duration + 200ms — a step during a cross is swallowed, never queued; queued dissolves stack into mud.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, full-bleed edge-to-edge; both clips are visible at partial opacity during the cross, so neither may carry a border, vignette, or letterbox.
- **Composition**: each scene's quiet zone per its own storyboard side; adjacent scenes should share an overall luminance family (within ~±20% average luma) so the mid-cross blend never flashes.
- **Loop**: generate explicitly seamless — last frame matches first frame, motion continuous across the wrap; prompt the loop, do not rely on editing.
- **Duration**: 6–10s per loop; shorter loops show their seam under a long hold.
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no scene cut, no flicker, no sudden movement.

## Interaction binding

```js
let i = 0, busy = false;
async function step(d) {
  if (busy) return;
  const next = i + d;
  if (next < 0 || next >= scenes.length) return;
  busy = true;
  const out = scenes[i].video, inn = scenes[next].video;
  inn.currentTime = 0; await inn.play();          // muted + playsinline
  crossfade(out, inn, 1000);                       // opacity only, ease-in-out
  setTimeout(() => { out.pause(); busy = false; }, 1200);
  i = next;
}
addEventListener('wheel', e => { e.preventDefault(); if (Math.abs(e.deltaY) > 10) step(Math.sign(e.deltaY)); }, { passive: false });
```

- `muted` + `playsinline` on every video or the incoming `play()` is blocked mid-cross.
- Start the incoming `play()` BEFORE the fade so its first decoded frame is ready at opacity > 0.

## UI composition rules

- Scene UI fades on its own slightly tighter clock: out by 40% of the cross, in from 60% — type at half-opacity over two blended worlds is unreadable, so keep the mid-cross type-free.
- Each scene's UI sits in its OWN quiet zone; the dissolve excuses nothing — verify contrast against the held loop across its full duration, not one frame.
- Persistent chrome (progress dots, wordmark) never fades; it is the fixed point the dissolve moves around.

## Example asset prompt template

> Seamless ambient loop for a crossfade scene sequence: slow-drifting aurora light over a dark still lake, subject mass kept to the lower-right third, large calm low-detail sky across the upper-left for a headline, continuous gentle motion that loops perfectly with last frame matching first, fixed camera, edge-to-edge composition with no border or vignette so it can dissolve into the next scene, 1920x1080, 8 seconds, no text, no watermark, no letterboxing, no scene cut, no flicker.

## When to use

- Atmospheric brand pieces where each scene is a place or mood (travel, wellness, ambient AI, fragrance).
- Decks of 3–7 worlds that should feel dreamed-between rather than navigated.
- Briefs that say "soft", "cinematic", "it should never jolt".

## When NOT to use

- Sharp product-spec storytelling — use frame-hold-ui-sync or scene-stepper-wipe.
- Scenes with wildly mismatched luminance (noon beach → midnight city) — the blend flashes grey; reorder or bridge.
- When no video provider is wired — degrade to per-scene raster stills with the identical 1000ms opacity crossfade plus a 20s Ken-Burns scale (1.0 → 1.04) while held.

## Performance notes

- Exactly two videos decode at once, and only during the cross; held state is one playing video. Unload (`removeAttribute('src')` + `load()`) anything ±2 scenes away.
- ≤8MB per loop; `preload="auto"` only for current and next scene.
- `prefers-reduced-motion`: pause all loops on their poster frame; keep the crossfade but shorten to 400ms.

## Pairs with (prototype slugs)

- `recipe-aurora-marketing`
- `recipe-warm-restraint`
- `recipe-restrained-ai-marketing`
- `style-aurorism`
- `aesthetic-dreamcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference — two ambient worlds mid-dissolve with persistent dot-rail chrome -->
