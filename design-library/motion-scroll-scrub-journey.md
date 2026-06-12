---
techniqueId: scroll-scrub-journey
name: Scroll-scrub journey (camera travels as you scroll)
category: scroll-driven
subCategory: video
role: hero
binding: scroll-progress
medium: video
pairsPrototypes: [recipe-aurora-marketing, recipe-scientific-infra-marketing, style-aurorism, aesthetic-solarpunk, aesthetic-cyberpunk]
notForUseWhen: The page is short (a journey needs 300vh+ of runway to feel like travel), the content is informational (docs, dashboards), or the brief has no environment to travel through — a journey with no destination is just a long scrub.
---

# Scroll-scrub journey (camera travels as you scroll)

A full-bleed camera flythrough of an environment is paused and SCRUBBED by scroll progress: scrolling down dollies the camera forward through the space, scrolling up backs it out — the page becomes a place you travel through rather than a document you read.

## Motion signature

- The video never plays. `video.pause()` on load; progress through a 300–500vh pinned runway maps to `currentTime = progress * duration`.
- Eased scrub with heavier damping than a turntable: `current += (target - current) * 0.06` per rAF (~300ms lag) — camera moves carry mass; a 1:1 mapping reads as VR judder, not travel.
- Scroll direction = travel direction, always: down is forward, up is reverse. The visitor's thumb is the throttle; symmetry is the contract.
- One continuous camera path, ZERO cuts — a single cut mid-scrub teleports the visitor and breaks spatial trust permanently.
- Waypoints in the path (a clearing at 0.4, a structure at 0.8) become the page's section anchors; copy swaps as each waypoint fills the frame.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; MP4 + WebM, keyframe interval `-g 12` or lower — the whole clip is random-access.
- **Composition**: keep one vertical third compositionally quiet along the ENTIRE path (path hugs one side of the environment; major subjects pass on the other) so UI has a persistent home; verify at progress 0, 0.25, 0.5, 0.75, 1.
- **Continuity**: one continuous dolly/flythrough, constant speed or a single smooth ease, no cuts, no whip pans, consistent lighting and weather across the whole path.
- **Duration**: 8–15s — longer than scrub-rotation clips because the runway is longer; aim for roughly 30 frames of video per 100vh of scroll.
- **Negative prompt**: no text, no watermark, no letterboxing, no scene cut, no camera shake, no speed ramps, no lens flares crossing the quiet zone.

## Interaction binding

```js
const v = scene.querySelector('video');
v.pause();
let target = 0, current = 0;
addEventListener('scroll', () => {
  const r = journeyWrap.getBoundingClientRect();
  target = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
}, { passive: true });
(function tick() {
  current += (target - current) * 0.06;
  if (v.duration) v.currentTime = current * v.duration;
  requestAnimationFrame(tick);
})();
```

- The pin: 400vh wrapper, video `position: sticky; top: 0; height: 100vh`.
- `preload="auto"` + `muted` + `playsinline` mandatory; consider fetching the full file via `fetch` → blob URL so seeks never hit the network.

## UI composition rules

- Copy lives in the quiet third and swaps at waypoints — crossfade ≤300ms, triggered at fixed progress thresholds, never mid-flight between anchors.
- Type stays screen-fixed while the world moves behind it: the still/moving contrast is what sells the travel.
- Add a subtle progress indicator (vertical hairline mapping the journey) — visitors need to know how much road is left.

## Example asset prompt template

> Cinematic camera flythrough: slow steady forward dolly along the left side of a vast bioluminescent canyon, passing glowing rock formations on the right side of frame, one single continuous camera move with no cuts, constant speed, consistent twilight lighting throughout, the left third of frame stays compositionally quiet and open, photoreal, 1920x1080, 12 seconds, no text, no watermark, no camera shake, no scene cuts.

## When to use

- Hero narratives where the product IS a world (games, spatial computing, infrastructure, travel).
- "From X to Y" stories — the camera path literalizes the transformation arc.
- Long-form marketing scrollers with 3+ sections that can ride one environment.

## When NOT to use

- Short pages or above-the-fold-only heroes — under 300vh of runway the journey feels like a stumble.
- Motion-sensitive contexts (health, accessibility-first audiences) — sustained optical flow is the most nausea-prone pattern in this library.
- When no video provider is wired — degrade to a 80–120 frame raster sequence on canvas, same path prompt ("frame N of M along the dolly path"), or to layered stills with scroll parallax.

## Performance notes

- ≤15MB target even at the longer duration; ship a 1280×720 rendition below 768px viewports.
- Pause the rAF loop off-screen; never write `currentTime` more than once per frame.
- `prefers-reduced-motion`: unpin and show three static waypoint frames (start / middle / destination) as a normal stacked section.

## Pairs with (prototype slugs)

- `recipe-aurora-marketing`
- `recipe-scientific-infra-marketing`
- `style-aurorism`
- `aesthetic-solarpunk`
- `aesthetic-cyberpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference — mid-journey frame with the path's quiet third carrying the copy -->
