---
techniqueId: ambient-loop-atmosphere
name: Ambient loop atmosphere (the page breathes under the UI)
category: ambient
subCategory: video
role: background
binding: none
medium: video
pairsPrototypes: [recipe-aurora-marketing, recipe-warm-restraint, style-liquid-glass, aesthetic-solarpunk, aesthetic-frutiger-aero]
notForUseWhen: The viewport is data-dense (dashboards, tables, forms — motion under inputs is hostile), the brand register is strictly flat/graphic with no photographic license, or the loop cannot be made seamless and a visible reset would interrupt long dwell times.
---

# Ambient loop atmosphere (the page breathes under the UI)

A seamless full-bleed atmospheric video — sky, water, smoke, fabric, dust — loops autonomously beneath the page's UI, generated with a deliberately quiet, light region where the type sits so the scene reads as a living backdrop, not a video with text on it (the aethera-hero pattern).

## Motion signature

- Autonomous and indifferent: `autoplay muted playsinline loop`, no input binding of any kind — the atmosphere was moving before the visitor arrived and continues after they leave.
- Motion budget: slow and large-scale — clouds shear, water swells, smoke curls at roughly 10–20px/s of apparent drift at 1080p. Fast or small-scale motion (flicker, sparkle) under UI causes reading fatigue inside a minute.
- One motion system per scene: sky OR water OR smoke. Two competing systems under static type reads as weather, not atmosphere.
- The loop seam is the make-or-break: 10–20s duration, last frame rejoining the first invisibly; visitors dwell on heroes for minutes and will catch a hard cut on the third pass.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; 2560×1440 if the layout letterboxes tall (object-fit: cover crops the safe areas — generate with margins in mind).
- **Composition**: prompt a deliberate quiet/light region matching the storyboard's type placement — e.g. "the upper half is calm, bright, near-uniform pale sky; all cloud activity stays in the lower third." The asset's luminance map IS the layout: type goes where the prompt put the calm.
- **Continuity**: fixed camera, constant exposure, seamless loop stated explicitly in the prompt ("seamless loop, the final frame matches the first").
- **Duration**: 10–20s. Under 8s the repetition becomes legible.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no exposure shift, no birds or objects crossing the quiet region.

## Interaction binding

```js
const v = scene.querySelector('video');
// No input binding — ambient. Lifecycle only:
new IntersectionObserver(([e]) => {
  e.isIntersecting ? v.play() : v.pause();
}, { threshold: 0.05 }).observe(scene);
// Crossfade-loop fallback for non-seamless sources:
v.addEventListener('timeupdate', () => {
  if (v.duration - v.currentTime < 1.0) scene.classList.add('xfade'); // 1s overlap clone
});
```

- `muted` + `playsinline` mandatory or autoplay is blocked; `poster` = a mid-loop frame, never frame 0 of a non-seamless source.
- Crossfade fallback: when a truly seamless generation fails, run two staggered copies of the clip and crossfade 1s before each end — costs one extra decode, saves the illusion.

## UI composition rules

- Type sits ONLY in the generated quiet region; measure it — sample the region's luminance across the whole loop and require ≥4.5:1 against body text at the worst frame, not the poster.
- A scrim is admission of failure: if you need `rgba(0,0,0,0.4)` over the whole frame, the prompt's quiet zone was wrong — regenerate, don't dim.
- UI never animates in sympathy with the atmosphere; the still chrome against drifting backdrop IS the composition.

## Example asset prompt template

> Atmospheric background film: vast pale dawn sky filling the frame edge to edge, the upper half calm, bright and near-uniform soft light, slow large cumulus drifting only through the lower third from left to right, fixed camera, locked tripod, constant exposure, seamless loop where the final frame matches the first, photoreal, 1920x1080, 15 seconds, no text, no watermark, no birds, no camera movement, no scene cut, no exposure shift.

## When to use

- Top-of-page heroes with no scroll-into moment — this is the default opening move where scroll-entrance-video can't fire.
- Brand registers built on calm, air, light, nature, or material (wellness, hospitality, fragrance, climate).
- Any storyboard whose "always something in motion" duty has no other owner in the viewport.

## When NOT to use

- Behind reading-length text columns — drift under paragraphs measurably slows reading; keep it to hero/section heights.
- Abstract-brand-color briefs — use living-gradient-video; this technique is photographic atmosphere.
- When no video provider is wired — degrade to raster + CSS: one generated still, with a 60–90s CSS background-position drift plus a slow opacity-breathing gradient overlay (raster + CSS, no sequence needed at this motion scale).

## Performance notes

- ≤8MB for a 15s loop; it plays the entire session, so cap bitrate at ~4Mbps and prefer H.265/AV1 with H.264 fallback.
- Pause when off-screen and when `document.hidden`; resume position is irrelevant for a seamless loop.
- `prefers-reduced-motion`: a single mid-loop still — the prompt's quiet-zone discipline means the still already works as the layout.

## Pairs with (prototype slugs)

- `recipe-aurora-marketing`
- `recipe-warm-restraint`
- `style-liquid-glass`
- `aesthetic-solarpunk`
- `aesthetic-frutiger-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference — headline sitting in the calm bright upper sky while clouds drift through the lower third -->
