---
techniqueId: pointer-magnetic-subject
name: Pointer-magnetic subject (a lean, not a stare)
category: pointer-driven
subCategory: raster-sequence
role: hero
binding: pointer-xy
medium: raster-sequence
pairsPrototypes: [recipe-warm-restraint, recipe-restrained-ai-marketing, style-glassmorphism, aesthetic-cottagecore, aesthetic-fairycore]
notForUseWhen: The brief wants overt acknowledgement (use mouse-scrub-look - this technique is deliberately subliminal), the subject is rigid with no plausible sway (architecture, typography), or the frames cannot be generated with consistent identity across the sequence.
images:
  - src: motion-pointer-magnetic-subject-ui.png
    reason: Motion technique UI mockup.
  - src: motion-pointer-magnetic-subject-isolated.png
    reason: Signature technique, isolated.
---

# Pointer-magnetic subject (a lean, not a stare)

A short generated frame sequence of a subject swaying through a tiny arc is micro-scrubbed by pointer position - the subject leans and drifts a few degrees toward the cursor, ±8 frames around center, presence without the full head-turn theatre of mouse-scrub-look.

## Motion signature

- Sequence of 17 frames (center frame 8, ±8 either side) covering roughly ±6° of body lean / weight shift - NOT a head turn; the gaze never visibly locks onto the cursor.
- Pointer-x picks the frame: `frame = 8 + round(nx * 8)` where `nx` is −1…1 from viewport center; pointer-y modulates a ±4px translateY on the image for a faint toward/away breath.
- Heavy easing is the whole technique: interpolate the frame index at `0.04` per rAF (~400ms lag) and round only at paint - the subject responds like someone shifting weight, not tracking a fly.
- Dead zone: the center ±10% of the viewport maps to frame 8 - the subject holds still until the visitor commits to a side.
- Idle: pointer rest >5s eases back to frame 8 over 3s. The right intensity is "did it just move?"; if a visitor consciously notices the mechanic, halve the arc.

## Asset generation spec

- **Resolution**: every frame 1920×1080 minimum, identical framing and crop across all 17.
- **Sequence strategy**: one master prompt + per-frame pose deltas ("frame N of 17: subject's weight shifted X degrees to the left, gaze and expression unchanged"); same seed/reference throughout - identity drift between adjacent frames reads as morphing and kills the effect instantly.
- **Composition**: subject on one third, quiet zone opposite for headline + CTA; the lean must stay inside the subject's third at both extremes - frame 1 and frame 17 define the layout envelope.
- **Continuity**: constant light, constant camera, constant expression; ONLY posture changes. Adjacent frames should differ less than 1% of pixels outside the subject.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no expression change, no background change between frames.

## Interaction binding

```js
const frames = [...scene.querySelectorAll('img.frame')]; // 17 preloaded
let target = 8, current = 8, shown = 8;
addEventListener('pointermove', e => {
  let nx = (e.clientX / innerWidth - 0.5) * 2;
  if (Math.abs(nx) < 0.1) nx = 0;                  // dead zone
  target = 8 + nx * 8;
}, { passive: true });
(function tick() {
  current += (target - current) * 0.04;
  const next = Math.round(current);
  if (next !== shown) {
    frames[shown].style.opacity = 0;
    frames[next].style.opacity = 1;
    shown = next;
  }
  requestAnimationFrame(tick);
})();
```

- All frames stacked absolutely, opacity-swapped - never `src` swaps (decode hitching).
- Mobile fallback: gyro gamma onto the same axis, else a 20s autonomous sway loop through frames 5-11.
- This is already the no-video technique; if a video provider IS wired, the same effect can micro-scrub a 2s sway clip, but the raster sequence is the canonical form.

## UI composition rules

- UI in the quiet zone opposite the subject; verify clearance against frames 1 and 17, the extremes.
- UI stays perfectly static - the technique's whole register is "the page is calm, the subject is alive"; any UI parallax on top buries the micro-motion.
- Pairs naturally with a slow ambient layer behind the subject (gradient drift) since the subject itself is mostly still.

## Example asset prompt template

> Portrait series, frame 9 of 17: a woman in a linen coat standing on the right third of frame, weight shifted 1.5 degrees toward camera-left compared to the neutral pose, gaze soft and forward, expression unchanged, fixed camera, locked tripod, warm seamless studio backdrop, large empty negative space on the left third, identical framing and light to all other frames, photoreal, 1920x1080, no text, no watermark, no camera movement, no expression change.

## When to use

- Quiet, premium heroes - apothecary, fashion, craft, wellness - where overt tracking would feel cheap.
- Character or founder portraits that should feel present, not performing.
- Briefs that say "subtle", "restrained", or "you can't quite tell why it feels alive."

## When NOT to use

- Briefs wanting obvious delight or demo-ability - visitors will miss it, by design; use mouse-scrub-look.
- Multiple subjects in frame - synchronized leaning reads as wind, not attention.
- Tight asset budgets - 17 consistent frames is a real generation cost; below ~11 usable frames the motion steps visibly.

## Performance notes

- 17 frames × WebP/AVIF ≈ 2-4MB total; preload all before enabling the binding (show frame 8 as the static poster meanwhile).
- One rAF loop, paused off-screen via `IntersectionObserver`.
- `prefers-reduced-motion`: frame 8 only, binding disabled - the hero is simply a fine portrait.

## Pairs with (prototype slugs)

- `recipe-warm-restraint`
- `recipe-restrained-ai-marketing`
- `style-glassmorphism`
- `aesthetic-cottagecore`
- `aesthetic-fairycore`

<!-- image: sample-1.png -->
<!-- reason: representative reference - subject mid-lean toward the cursor side, headline static in the opposite quiet zone -->
