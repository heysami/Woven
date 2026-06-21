---
techniqueId: scene-stepper-wipe
name: Scene stepper wipe (one notch, one scene)
category: scene-choreography
subCategory: hybrid
role: transition
binding: wheel-step
medium: hybrid
pairsPrototypes: [recipe-bento-marketing, recipe-neo-grotesque-portfolio, recipe-editorial-magazine, style-oversized-neo-grotesque, style-bold-display]
notForUseWhen: The piece needs free scrolling or anchor links into the middle (the stepper owns the wheel completely), or there are fewer than 3 scenes - a wipe between two states reads as a glitchy tab switch, not choreography.
images:
  - src: motion-scene-stepper-wipe-ui.png
    reason: Motion technique UI mockup.
  - src: motion-scene-stepper-wipe-isolated.png
    reason: Signature technique, isolated.
---

# Scene stepper wipe (one notch, one scene)

Full-screen scenes advance exactly one per wheel-notch / swipe / arrow-key with a directional wipe or slide (next scene pushes in from the bottom on advance, from the top on back-step) - the piece is a strictly linear deck the visitor steps through, never a scroll.

## Motion signature

- One input = one scene. The wheel is consumed (`preventDefault` on a non-passive listener) and quantised: any `deltaY` beyond ±10 counts as one step; everything during the debounce window is swallowed.
- Debounce ≥600ms from transition START - trackpads emit 40+ wheel events per flick; without the gate one flick skips three scenes.
- The wipe itself runs 550-700ms with `cubic-bezier(0.22, 1, 0.36, 1)` (decisive arrival, no bounce). Direction always matches input: advance pushes up, back-step pushes down.
- A fixed dot-rail (right edge, 8px dots, 16px gap, active dot 1.5× and full-opacity) shows position; dots are also click targets but only step ±1 toward the clicked dot - linearity is the contract.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, every asset full-bleed edge-to-edge - the wipe exposes the incoming asset's leading edge first, so edges must be clean (no vignette, no border).
- **Composition**: each scene's subject anchored to one third with a quiet zone opposite for that scene's UI; ALTERNATE the side scene-to-scene so consecutive wipes read as a rhythm, not a stutter.
- **Hybrid medium**: stills and ambient-loop videos mix freely in one deck; loops keep playing only while their scene holds (pause on exit, resume on re-entry).
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no vignette, no scene cut.

## Interaction binding

```js
let i = 0, lock = 0;
const go = d => {
  const now = performance.now();
  if (now - lock < 600) return;
  const next = Math.min(Math.max(i + d, 0), scenes.length - 1);
  if (next === i) return;
  lock = now;
  wipe(scenes[i], scenes[next], d); // translateY push, 650ms
  i = next;
};
addEventListener('wheel', e => { e.preventDefault(); if (Math.abs(e.deltaY) > 10) go(Math.sign(e.deltaY)); }, { passive: false });
addEventListener('keydown', e => { if (e.key === 'ArrowDown') go(1); if (e.key === 'ArrowUp') go(-1); });
```

- Touch: vertical swipe ≥60px within 400ms maps to the same `go(±1)`; pinch and horizontal gestures are ignored.
- Video scenes use `muted playsinline` and `play()` on scene entry - never before, or autoplay budget is wasted off-screen.

## UI composition rules

- Per-scene UI lives in that scene's generated quiet zone and wipes WITH its scene - only the dot-rail and a small wordmark persist across the cut.
- Incoming UI may stagger in 80-120ms after the wipe settles, but never animates during the wipe itself; two simultaneous motions read as chaos.
- The dot-rail must clear both scenes' quiet zones - right edge, vertically centered, is safe when subjects sit on thirds.

## Example asset prompt template

> Full-bleed scene for a stepped presentation: a sculptural product hero anchored on the right third of frame, large clean low-detail negative space across the left third for a headline, edge-to-edge composition with no border or vignette so the frame survives a vertical push-wipe transition, fixed camera, soft directional light, photoreal, 1920x1080, no text, no watermark, no letterboxing, no scene cut.

## When to use

- Launch pieces, keynotes-on-the-web, and portfolios where the author controls pacing scene by scene.
- Mixed still/video decks - the wipe is medium-agnostic, so stills and loops sit in one sequence.
- Briefs that say "like a presentation, not a page."

## When NOT to use

- Content people need to skim or deep-link - use a normal scroll page with scroll-entrance-video sections.
- More than ~9 scenes; past that the dot-rail and the visitor's patience both break.
- When no video provider is wired - the technique already works with stills only; generate every scene as a raster and keep the identical wipe.

## Performance notes

- Keep at most 3 scenes mounted (previous / current / next); preload the next scene's asset during the hold, not during the wipe.
- The wipe animates `transform` only (translateY on two compositor layers) - never `top`, never layout.
- `prefers-reduced-motion`: replace the wipe with a 200ms opacity cut; keep the debounce and dot-rail unchanged.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-neo-grotesque-portfolio`
- `recipe-editorial-magazine`
- `style-oversized-neo-grotesque`
- `style-bold-display`

<!-- image: sample-1.png -->
<!-- reason: representative reference - mid-wipe between two scenes with the dot-rail showing position -->
