---
techniqueId: scroll-scrub-rotation
name: Scroll-scrub rotation (product turns as you scroll)
category: scroll-driven
subCategory: video
role: product
binding: scroll-progress
medium: video
pairsPrototypes: [recipe-bento-marketing, recipe-restrained-ai-marketing, recipe-devtools-marketing, style-bold-display, aesthetic-cassette-futurism]
notForUseWhen: The subject looks the same from every angle (spheres, flat cards, gradients — rotation reveals nothing), or the page can't afford a pinned section (short utility pages, docs), or scroll must keep its native meaning throughout.
---

# Scroll-scrub rotation (product turns as you scroll)

A full-bleed turntable video of the product rotating from its back to its front is paused and SCRUBBED by scroll progress through a pinned section — scrolling down turns the object toward you, scrolling up turns it away (the iPhone-Air reveal pattern).

## Motion signature

- The video never plays. `video.pause()` on load; section progress (0→1 across the pinned range) maps to `currentTime = progress * duration`.
- The section pins for 150–250vh of scroll runway while the asset stays fixed full-bleed; rotation is the ONLY thing scroll does inside the pin.
- Eased scrub: `current += (target - current) * 0.12` per rAF — the object carries ~150ms of momentum, so flick-scrolling reads as a weighted physical turn, not a slideshow.
- Bidirectional by construction: scrubbing is symmetric, so scrolling back up reverses the rotation perfectly. Never fake this with two clips.
- The generation prompt and the binding must agree: one continuous rotation axis, constant lighting, fixed camera — any cut or light shift becomes a visible glitch mid-scroll.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; H.264/H.265 MP4 + WebM, high keyframe density (`-g 12` or lower) — scroll seeks every frame; sparse keyframes snap.
- **Composition**: product anchored on one third (left or right per the storyboard's UI counterweight), seamless edge-to-edge background, the opposite third kept clean in EVERY frame of the rotation — swinging edges (cables, straps) must never cross the quiet zone.
- **Continuity**: ONE continuous turntable rotation, back-facing at t=0 to front-facing at t=end (180°, or 360° for loop-capable subjects), constant lighting rig, locked camera, no exposure drift.
- **Duration**: 4–6s — the clip is a rotation axis, not a film; more frames per degree means smoother seeks.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no lighting change, no background drift.

## Interaction binding

```js
const v = scene.querySelector('video');
v.pause();
let target = 0, current = 0;
addEventListener('scroll', () => {
  const r = pinWrap.getBoundingClientRect();
  target = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
}, { passive: true });
(function tick() {
  current += (target - current) * 0.12;
  if (v.duration) v.currentTime = current * v.duration;
  requestAnimationFrame(tick);
})();
```

- The pin: a wrapper of 250vh with the video `position: sticky; top: 0; height: 100vh` inside it.
- `preload="auto"` + `muted` + `playsinline` mandatory — scrubbing an unbuffered video stalls, and iOS refuses inline video without the attributes.

## UI composition rules

- UI lives in the generated quiet zone (product right → copy left). Copy blocks may swap at rotation milestones (e.g. 0.33 / 0.66 progress) to caption what the turn just revealed.
- Type must survive every frame — check contrast at progress 0, 0.25, 0.5, 0.75, 1, not just the poster.
- A thin progress affordance (hairline bar or "keep scrolling" hint at 0 progress) prevents visitors from thinking the page is stuck while pinned.

## Example asset prompt template

> Product turntable film: a brushed-aluminum device on the right third of frame rotating smoothly from fully back-facing to fully front-facing in one single continuous 180-degree turn, fixed camera, locked tripod, constant soft studio lighting, seamless background exactly matching the page section, large empty negative space on the left third in every frame, photoreal, 1920x1080, no cuts, no zoom, no text, no watermark, no lighting changes.

## When to use

- Hardware and device reveals where the back-to-front turn IS the narrative (ports, then face).
- Pinned mid-page product sections in marketing scrollers.
- Briefs that say "let the user inspect it" without real 3D.

## When NOT to use

- Above-the-fold heroes — there's no scroll runway yet; use scroll-entrance-video or mouse-scrub-look.
- When video seeking is janky on target devices — switch to scroll-sequence-frames (same turntable prompt, 60–90 stills on canvas).
- When no video provider is wired — degrade to a 40–90 frame raster sequence scrubbed by the same progress value ("frame N of M of turntable rotation" per frame).

## Performance notes

- One video element, ≤10MB target; `poster` from the t=0 (back-facing) frame so the pre-scroll state is intentional.
- Pause the rAF loop when the pin is off-screen (`IntersectionObserver`); throttle `currentTime` writes to one per frame.
- `prefers-reduced-motion`: unpin the section and show the front-facing final frame as a static image.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-restrained-ai-marketing`
- `recipe-devtools-marketing`
- `style-bold-display`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference — product mid-turn in a pinned section with copy in the quiet zone -->
