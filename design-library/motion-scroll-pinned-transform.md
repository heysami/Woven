---
techniqueId: scroll-pinned-transform
name: Scroll-pinned transform (asset morphs while copy swaps)
category: scroll-driven
subCategory: hybrid
role: product
binding: scroll-progress
medium: hybrid
pairsPrototypes: [recipe-bento-marketing, recipe-editorial-magazine, recipe-warm-restraint, style-oversized-neo-grotesque]
notForUseWhen: There's only one copy block to show (a pin with one message is a pointless scroll tax), or the asset has no detail worth zooming into - the transform must reveal something at each step.
images:
  - src: motion-scroll-pinned-transform-ui.png
    reason: Motion technique UI mockup.
  - src: motion-scroll-pinned-transform-isolated.png
    reason: Signature technique, isolated.
---

# Scroll-pinned transform (asset morphs while copy swaps)

A section pins while its full-bleed asset scales, pans, and crops under CSS transforms driven by scroll progress, and successive copy blocks crossfade in the quiet zone - one asset, three or four framings, each paired with its own message (the classic Apple pinned sequence).

## Motion signature

- The section pins for 100vh per copy step (3 steps → 300vh runway); within each step the asset interpolates between two keyframed transforms (`scale`, `translate`, `clip-path` inset).
- Transforms are eased per step, not linearly across the pin: each step uses `cubic-bezier(0.4, 0, 0.2, 1)` mapped over its own progress slice, so every framing decelerates into a deliberate rest.
- Copy crossfades at step boundaries: outgoing block fades over 200ms, incoming enters 100ms later with a 12px rise - never two blocks visible at full opacity.
- The asset itself never plays as video during the pin; the motion IS the transform. A video asset contributes hold-frames (seek to a fixed `currentTime` per step), a still contributes its full resolution to zoom into.
- Bidirectional: scrolling up reverses transforms and copy in perfect symmetry - pure functions of progress, no tweens with internal state.

## Asset generation spec

- **Resolution**: 1920×1080 minimum for the base framing; generate at 3840×2160 when any step zooms past `scale(1.4)` - CSS zoom into a 1080p still goes soft exactly when the visitor is staring closest.
- **Composition**: the asset must contain every step's crop: a wide master framing whose regions of interest sit where the step transforms will center them; the quiet zone must stay clean in EVERY step's framing, not just the master.
- **Continuity**: for video-sourced hold-frames, one continuous clip with constant lighting so any seeked frame matches any other; for stills, a single generation - never composite two generations into one zoom path.
- **Step count**: 3-4 framings; beyond 4 the pin overstays and visitors rage-scroll.
- **Negative prompt**: no text, no watermark, no letterboxing, no vignette (it travels visibly during pans), no depth-of-field blur on regions a later step zooms into.

## Interaction binding

```js
const steps = [
  { t: 'scale(1) translate(0,0)',        copy: 0 },
  { t: 'scale(1.6) translate(-12%,8%)',  copy: 1 },
  { t: 'scale(2.2) translate(10%,-14%)', copy: 2 },
];
addEventListener('scroll', () => {
  const r = pinWrap.getBoundingClientRect();
  const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
  const i = Math.min(steps.length - 1, Math.floor(p * steps.length));
  asset.style.transform = steps[i].t;       // CSS transition handles the ease
  copyBlocks.forEach((b, j) => b.classList.toggle('active', j === steps[i].copy));
}, { passive: true });
```

- The asset element carries `transition: transform 700ms cubic-bezier(0.4,0,0.2,1)` so steps glide instead of snap; `will-change: transform` on the asset only.
- If the asset is video, set `muted` + `playsinline`, `pause()` immediately, and seek once per step - never leave it playing under transforms.

## UI composition rules

- Copy blocks all occupy the SAME quiet-zone slot (e.g. left third, vertically centered) - the constancy of position against the moving asset is the rhythm.
- Each step's framing must keep that slot clean; QA every step's transform against copy legibility, not just step one.
- Step boundaries need a scroll affordance on first pin (a "3 steps" dot rail) so the pin reads as a sequence, not a freeze.

## Example asset prompt template

> Ultra-detailed wide product still: a precision espresso machine centered on the right two-thirds of frame against a seamless warm-grey studio background, sharp focus across the entire machine including the group head, dial cluster, and steam wand (each will be zoomed into), the left third of frame completely empty and clean, photoreal, 3840x2160, even soft lighting, no text, no watermark, no vignette, no depth-of-field blur.

## When to use

- Feature walkthroughs of one hero object - overview, then detail A, then detail B.
- Briefs that need Apple-style pinned storytelling without a video pipeline (a single 4K still carries the whole section).
- Editorial product deep-dives where copy and crop must advance in lockstep.

## When NOT to use

- True rotation or articulation (parts moving) - CSS can't fake that; use scroll-scrub-rotation or scroll-sequence-frames.
- Pages where the pin would trap the only path to critical content (pricing, signup) behind 300vh of theater.
- Single-message sections - use scroll-entrance-video and let the page keep flowing.

## Performance notes

- One transformed element only; transforms are compositor-cheap, but a 4K image layer costs ~33MB of GPU memory - ship 2160p only above 1280px viewports.
- Toggle classes on scroll, let CSS transitions animate - no rAF loop needed for this technique.
- `prefers-reduced-motion`: unpin and stack the steps as static cropped images, each with its copy block beside it.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-editorial-magazine`
- `recipe-warm-restraint`
- `style-oversized-neo-grotesque`

<!-- image: sample-1.png -->
<!-- reason: representative reference - pinned asset at a zoomed step with the second copy block active in the quiet zone -->
