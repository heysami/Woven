---
techniqueId: cinemagraph-still
name: Cinemagraph still (one thing moves, everything else is frozen)
category: ambient
subCategory: video
role: section
binding: none
medium: video
pairsPrototypes: [recipe-editorial-magazine, recipe-warm-restraint, aesthetic-dark-academia, aesthetic-cottagecore]
notForUseWhen: The scene wants whole-frame life (use ambient-loop-atmosphere), the moving element can't loop seamlessly (one-way motion like a falling object), or the section is so small the single moving element drops below ~80px rendered and the effect vanishes.
---

# Cinemagraph still (one thing moves, everything else is frozen)

A photograph in which exactly ONE element moves — steam off a cup, hair in a draft, a flag, rain on glass — while every other pixel holds frozen; the uncanny stillness-with-life makes a section image feel enchanted rather than animated.

## Motion signature

- The power is the ratio: ≥95% of the frame is perfectly static, one bounded element carries 100% of the motion. The moment a second thing moves (a shadow, a background passer-by) it's just video.
- Autonomous: `autoplay muted playsinline loop`, no binding — cinemagraphs are objects of contemplation, not interaction.
- The moving element loops seamlessly on a 4–8s cycle; periodic motions (steam, rain, flame, fabric) loop honestly — choose the element FOR its loopability.
- Motion amplitude stays small: the element moves within its own footprint, never travels across the frame.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge.
- **Composition**: the moving element placed as the focal accent on one third; the opposite side quiet for the section's copy. The frozen majority of the frame is your guaranteed-stable canvas — exploit it: UI may overlap frozen regions freely.
- **Continuity**: the prompt must demand the freeze explicitly — "static camera, frozen scene, only the steam moves" — generation models default to ambient life everywhere and that default is this technique's enemy.
- **Duration**: 4–8s seamless loop.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no background motion, no flicker, no person blinking or shifting (unless the person IS the moving element).

## Interaction binding

```js
const v = scene.querySelector('video');
// No input binding — lifecycle only.
new IntersectionObserver(([e]) => {
  e.isIntersecting ? v.play() : v.pause();
}, { threshold: 0.2 }).observe(scene);
```

- `muted playsinline loop preload="metadata"` — sections below the fold must not preload `auto`.
- `poster` = any frame (they're 95% identical); use the loop midpoint so the moving element is mid-gesture, which reads as a still photo until it moves.
- QA gate: difference-blend first and last frames — anything nonzero outside the moving element's mask is a regeneration.

## UI composition rules

- Copy may sit ON frozen regions at full confidence — this is the one video technique where overlap with imagery is contractually safe, because the prompt froze it.
- Keep a 10% padding halo between UI and the moving element; type brushing against the steam kills the spell.
- Caption-style microcopy near the moving element (an editorial credit line) works beautifully — the eye is already there.

## Example asset prompt template

> Cinemagraph: a writing desk by a tall window, a cup of tea on the left third with steam rising gently and continuously, static camera, completely frozen scene, only the steam moves, every other element motionless including curtains, papers and light, fixed camera, locked tripod, constant exposure, seamless loop where the final frame matches the first, photoreal, 1920x1080, 6 seconds, no text, no watermark, no camera movement, no background motion, no flicker.

## When to use

- Editorial sections, chapter openers, about pages — anywhere a photograph would go but should hold attention twice as long.
- Quiet luxury and craft registers where full-motion video is too loud.
- Mid-page rhythm: between two static sections, one cinemagraph re-arms the page's sense of life at minimal motion cost.

## When NOT to use

- Heroes that must carry the whole brand energy — a cinemagraph whispers; use ambient-loop-atmosphere or pointer-spotlight-video.
- Scenes with no naturally periodic element — don't force a loop onto one-way motion.
- When no video provider is wired — degrade to raster + CSS: generate the still, isolate the moving element's region, and animate it with CSS (a masked steam layer with translateY + opacity keyframes, 6s infinite) — crude but the frozen-majority contract survives.

## Performance notes

- ≤3MB — 95% static frames compress brilliantly; crank quality up, not bitrate.
- Multiple cinemagraphs per page are affordable (unlike full-motion loops) but cap simultaneous playback at 2 via the shared `IntersectionObserver`.
- `prefers-reduced-motion`: the midpoint still — by construction it's a complete photograph.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-warm-restraint`
- `aesthetic-dark-academia`
- `aesthetic-cottagecore`

<!-- image: sample-1.png -->
<!-- reason: representative reference — frozen desk scene with only the steam alive, copy resting on the still region -->
