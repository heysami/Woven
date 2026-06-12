---
techniqueId: focus-pull-type
name: Focus pull (rack-focus blur between sections / type planes)
category: scroll-driven
subCategory: dom
role: editorial | transition
binding: scroll-progress (or hover)
medium: dom-filter
pairsPrototypes: [aesthetic-monochrome-tech-editorial, style-oversized-neo-grotesque, recipe-readcv, style-restrained-hairline, aesthetic-sculptural-minimal]
notForUseWhen: Long-form reading surfaces (blur on prose you intend people to read is hostile), low-end-device audiences (filter: blur on large type is paint-expensive), or pages where every section must be skimmable at speed.
images:
  - src: motion-focus-pull-type.png
    reason: Representative technique still.
---

# Focus pull (rack-focus blur between sections / type planes)

The camera language of rack focus translated to scroll: the section (or type
plane) currently "in focus" renders sharp while its neighbors sit soft — and
as the visitor scrolls, focus PULLS from one plane to the next, blur easing
off the incoming content while the outgoing melts. The pixlspace scroll
transition: depth-of-field as information hierarchy, the page deciding what
the eye should hold the way a cinematographer does.

## Motion signature

- Each focus plane (section, headline, paragraph block) gets a blur amount
  driven by its distance from the focal point — the viewport center or a
  committed focal line at 40% height.
- `blur = clamp(|planeCenter - focalLine| / viewportH * maxBlur, 0, maxBlur)`
  with maxBlur 6–10px; ease the mapping (quadratic), don't linearize it —
  real lenses snap into focus near the plane.
- Opacity rides along subtly (sharp 1.0 → soft 0.7) — blur alone leaves soft
  planes too loud.
- A focus pull takes the duration of the scroll gesture itself — NEVER a
  timed animation racing the scroll; bind to scroll-progress and the pull is
  inherently interruptible and reversible.
- Optional letter-scale micro-shift: the incoming plane settles from
  `scale(1.015)` to 1.0 as it sharpens — the breathing a lens does as it
  finds the plane.

## Implementation skeleton

```js
const planes = [...document.querySelectorAll('[data-focus-plane]')];
(function tick() {
  const focal = innerHeight * 0.4;
  for (const p of planes) {
    const r = p.getBoundingClientRect();              // batched: read phase
    const d = Math.abs((r.top + r.height / 2) - focal) / innerHeight;
    const t = Math.min(d * 1.6, 1) ** 2;              // quadratic ease
    p.style.filter  = `blur(${(t * 8).toFixed(1)}px)`;
    p.style.opacity = (1 - t * 0.3).toFixed(2);
  }
  requestAnimationFrame(tick);
})();
```

- CSS Scroll-Driven Animations variant (Chrome/Edge 115+, Safari 26+):
  `animation-timeline: view()` driving a blur keyframe per plane — zero JS,
  use it when the support matrix allows and JS-fallback the rest.
- Hover variant (small doses): card grids where the hovered card sharpens
  and siblings soften 2–3px — same physics, pointer as focal point.

## UI composition rules

- MAXIMUM one plane fully soft-adjacent on each side of the focal plane —
  three visible planes total; a page of six blurred ghosts is fog, not depth.
- Nav and persistent UI never blur.
- Type scale must survive softening: planes at body size disappear when
  blurred — the technique wants display/headline scale (it is a poster
  gesture, not a paragraph gesture).
- Pairs naturally as the BASE layer under `motion-lens-magnifier-reveal`
  (lens = manual focus override inside an auto-focus page).

## Performance notes

- `filter: blur()` on large boxes is paint-heavy: promote planes with
  `will-change: filter` (sparingly), cap maxBlur at 10px, quantize written
  blur values to 0.5px steps so unchanged frames skip paint entirely.
- Batch all reads before all writes in the rAF; or use IntersectionObserver
  thresholds to skip off-screen planes.
- `prefers-reduced-motion`: everything sharp, focus expressed by opacity
  only (1.0 vs 0.75).

## When to use

- Portfolio/editorial scroll journeys with 3–6 statement sections.
- Manifesto pages — one sentence in focus at a time, the page as teleprompter.
- Above a hero object scene: copy planes pulling focus while the object
  holds sharp (the object reads as the camera's true subject).

## When NOT to use

- Docs, dashboards, anything skimmed — blur taxes every glance.
- Together with heavy backdrop-filter surfaces (two blur systems = paint
  storm on mid-range hardware).
- More than ~8 planes per page — the rAF read loop and paint cost compound.

## Pairs with (prototype slugs)

- `aesthetic-monochrome-tech-editorial`
- `style-oversized-neo-grotesque`
- `recipe-readcv`
- `style-restrained-hairline`
- `aesthetic-sculptural-minimal`
