---
techniqueId: scene-zoom-through
name: Scene zoom-through (dive into the detail)
category: scene-choreography
subCategory: hybrid
role: transition
binding: wheel-step
medium: hybrid
pairsPrototypes: [recipe-scientific-infra-marketing, recipe-devtools-marketing, recipe-ai-foundry-dark, aesthetic-solarpunk, style-glassmorphism]
notForUseWhen: Scenes are thematically parallel rather than nested (three equal product pillars) — zoom implies containment and scale; zooming between siblings lies about the structure. Also wrong when assets cannot be generated as a wide/detail pair of the same world.
images:
  - src: motion-scene-zoom-through-ui.png
    reason: Motion technique UI mockup.
  - src: motion-scene-zoom-through-isolated.png
    reason: Signature technique, isolated.
---

# Scene zoom-through (dive into the detail)

Advancing a wheel-step zooms the camera INTO an authored detail region of scene N — a window, a chip, a leaf — and that detail becomes scene N+1 full-frame; back-stepping reverses the dive, pulling out of the detail into the wide shot, so the whole piece reads as one continuous change of scale.

## Motion signature

- Each scene declares a target rect (e.g. `{x: 0.62, y: 0.38, w: 0.18, h: 0.18}` in frame fractions) — the region scene N+1 "lives inside".
- On advance: scene N scales from 1× toward `1/w` (≈5.5× for an 18% rect) with `cubic-bezier(0.7, 0, 0.3, 1)` over 900–1200ms, transform-origin at the rect center; scene N+1 fades in underneath from 60% of the timeline, scaling from 0.92× to 1×.
- The crossover hides the resolution cliff: scene N is past 3× (soft) exactly when N+1 (sharp) takes over.
- Back-step runs the identical timeline reversed — N+1 scales down into the rect while N scales back to 1×. Debounce 1300ms.

## Asset generation spec

- **Resolution**: 1920×1080 minimum; the OUTGOING asset is the one magnified, so prefer 2560×1440+ for scene N when its rect is under 25% of frame.
- **The pair is one prompt, two distances**: write scene N's prompt, then derive scene N+1's prompt as the magnified detail of the same sentence — same world, same palette, same light direction ("the same greenhouse, now filling the frame, seen from inside the glass panel"). Mismatched light breaks the containment illusion instantly.
- **Composition**: scene N's target rect must sit AWAY from scene N's quiet zone (UI on the left third → rect on the right half); scene N+1 gets its own quiet zone per its storyboard side.
- **Detail seeding**: explicitly prompt the detail INTO the wide shot ("a small glass control room visible at the upper-right") so the destination already exists before the dive.
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no camera move, no scene cut.

## Interaction binding

```js
function diveTo(rect, dir) {            // dir: +1 advance, -1 back
  const s = 1 / rect.w;
  cur.style.transformOrigin = `${rect.x * 100}% ${rect.y * 100}%`;
  cur.animate(
    [{ transform: 'scale(1)' }, { transform: `scale(${s})`, opacity: 0 }],
    { duration: 1100, easing: 'cubic-bezier(0.7,0,0.3,1)', fill: 'forwards', direction: dir > 0 ? 'normal' : 'reverse' }
  );
  next.animate([{ transform: 'scale(0.92)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 }],
    { duration: 440, delay: dir > 0 ? 660 : 0, fill: 'forwards' });
}
```

- Video scenes play `muted playsinline` while held; PAUSE the outgoing video the moment the dive starts — scaling a decoding video doubles compositor load for nothing.
- Wheel handling identical to scene-stepper-wipe (non-passive, quantised, debounced).

## UI composition rules

- Scene UI fades out in the first 250ms of the dive — type magnifying at 4× reads as an error.
- Incoming UI enters 100ms after the new scene settles at 1×, in scene N+1's own quiet zone.
- A persistent scale-breadcrumb (e.g. "campus → greenhouse → leaf", 12px, frame edge) is the one chrome element that survives dives; it is the map of the nesting.

## Example asset prompt template

> Wide establishing shot for a zoom-through pair: a solar research campus at golden hour, main structures across the lower-left, a small glass greenhouse clearly visible at the upper-right of frame about one fifth of frame width (this region becomes the next scene full-frame after a camera dive), large soft sky across the upper-left for a headline, fixed camera, edge-to-edge composition, photoreal, 2560x1440, no text, no watermark, no letterboxing, no camera movement. (Detail clip: the same greenhouse interior filling the frame, same golden-hour light direction.)

## When to use

- Scale-of-the-system stories: infrastructure → rack → chip; planet → city → home; product → mechanism.
- Technical marketing where "look closer" is literally the pitch.
- 3–5 scene dives; one continuous nesting is the memorable unit.

## When NOT to use

- Flat narratives with no containment relationship — use scene-stepper-wipe or scene-crossfade-hold.
- Outgoing assets that cannot survive ~4× magnification before the crossover (noisy, compressed) — bump source resolution or shrink the dive.
- When no video provider is wired — the technique works fully with stills: generate the wide/detail raster pair and run the identical transform timeline.

## Performance notes

- Animate `transform` and `opacity` only; promote both scenes with `will-change: transform` for the dive, remove it after.
- Maximum two scenes mounted during a dive; pre-decode N+1's asset while N holds.
- `prefers-reduced-motion`: replace the dive with a 300ms crossfade plus the breadcrumb update — the nesting is still narrated, just not flown.

## Pairs with (prototype slugs)

- `recipe-scientific-infra-marketing`
- `recipe-devtools-marketing`
- `recipe-ai-foundry-dark`
- `aesthetic-solarpunk`
- `style-glassmorphism`

<!-- image: sample-1.png -->
<!-- reason: representative reference — wide shot with the authored detail rect that becomes the next scene -->
