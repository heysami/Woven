---
techniqueId: background-swap-fixed-ui
name: Background swap, fixed UI (the world changes around the chrome)
category: scene-choreography
subCategory: video
role: background
binding: wheel-step
medium: video
pairsPrototypes: [recipe-restrained-ai-marketing, recipe-aurora-marketing, recipe-warm-restraint, style-glassmorphism, aesthetic-frutiger-aero]
notForUseWhen: Each scene needs a different layout (headline left on one, product grid on the next) - the technique's whole value is the unmoving chrome; if the UI must reflow per scene, use scene-stepper-wipe instead.
images:
  - src: motion-background-swap-fixed-ui-ui.png
    reason: Motion technique UI mockup.
  - src: motion-background-swap-fixed-ui-isolated.png
    reason: Signature technique, isolated.
---

# Background swap, fixed UI (the world changes around the chrome)

The UI chrome - headline rail, nav dots, CTA - is laid out ONCE and never moves; each wheel-step swaps only the full-bleed background video behind it, so continuity lives in the stable interface while change lives entirely in the world.

## Motion signature

- Chrome is position-fixed and persists across all scenes; only the per-scene headline/body TEXT swaps inside the fixed rail (out 150ms, in 150ms, 80ms gap - the slot never moves, only its contents).
- Background swap: incoming video fades in over the outgoing across 600-900ms `ease-in-out` while both play; outgoing pauses at opacity 0. Shorter than scene-crossfade-hold because the fixed chrome already provides continuity - the background may move faster.
- Each held background runs its own 6-10s seamless ambient loop; the page is never still.
- Wheel quantised to ±1 scene, debounce 900ms; dot-rail in the fixed chrome advances with the swap.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, full-bleed edge-to-edge; backgrounds sit behind chrome at z-index 0 with no border or vignette.
- **Composition - one contract for ALL scenes**: the fixed chrome defines ONE quiet-zone map (e.g. headline rail on the left third, CTA lower-left, dots right edge), and EVERY background prompt must reserve that exact map - subject mass on the right two-thirds, low-detail left third, calm lower-left. This is the inversion of per-scene composition: the chrome dictates, every asset obeys.
- **Luminance band**: all backgrounds within one exposure family (target the headline zone at <35% or >65% average luma consistently across the set, never mixed) so one fixed text color survives every scene.
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no scene cut, no flicker, no bright highlights in the left third.

## Interaction binding

```js
let i = 0, busy = false;
async function swapBg(d) {
  if (busy) return; busy = true;
  const next = clamp(i + d, 0, bgs.length - 1);
  if (next === i) { busy = false; return; }
  bgs[next].currentTime = 0; await bgs[next].play();   // muted + playsinline
  bgs[next].style.opacity = 1;                          // 750ms ease-in-out CSS transition
  swapRailText(scenes[next]);                           // 150ms out / 80ms gap / 150ms in
  setTimeout(() => { bgs[i].pause(); bgs[i].style.opacity = 0; i = next; busy = false; }, 900);
}
addEventListener('wheel', e => { e.preventDefault(); if (Math.abs(e.deltaY) > 10) swapBg(Math.sign(e.deltaY)); }, { passive: false });
```

- All background videos `muted playsinline preload="metadata"`; bump current and next to `auto`.
- Text swap and background fade start on the same frame - one gesture, two layers.

## UI composition rules

- The chrome is designed FIRST, against the shared quiet-zone map, then every asset is generated to honor it - verify each background's headline zone across its full loop, not one frame.
- A 0-25% scrim gradient behind the headline rail is the permitted safety net; if any background needs more than 25%, the asset fails QA and is re-generated.
- Nothing in the chrome may ever animate position; the only chrome motion is text content swapping in place and the active dot growing 1.5×.

## Example asset prompt template

> Full-bleed ambient background loop, scene 3 of a fixed-chrome set: warm coastal fog rolling over dark cliffs, all landscape mass kept to the right two-thirds of frame, the left third a calm low-detail fog bank with average luminance under 35% reserved for a fixed white headline rail, lower-left corner quiet for a button, slow continuous motion looping seamlessly with last frame matching first, fixed camera, edge-to-edge, 1920x1080, 8 seconds, no text, no watermark, no letterboxing, no flicker, no bright highlights in the left third.

## When to use

- Multi-mood brand pieces with ONE message structure: same claim shape, five worlds behind it.
- Restrained marketing where the brief says "calm, confident, the UI should feel inevitable".
- Sets where assets are generated in bulk against a single composition contract - cheapest choreography per scene.

## When NOT to use

- Scene-specific layouts or per-scene CTAs - the fixed rail cannot serve them; use scene-stepper-wipe.
- Backgrounds that cannot share a luminance band (day scenes mixed with night) without per-scene text-color logic.
- When no video provider is wired - degrade to raster backgrounds with the identical 750ms opacity swap plus a 20s drift (`scale(1)` → `scale(1.05)`) while held.

## Performance notes

- One playing video while held, two only during the 900ms swap; unload backgrounds more than one scene away.
- ≤8MB per loop; the fixed chrome lives in its own compositor layer (`transform: translateZ(0)`) so background fades never repaint type.
- `prefers-reduced-motion`: hold each background on its poster frame; keep the text swap and a 300ms background cut.

## Pairs with (prototype slugs)

- `recipe-restrained-ai-marketing`
- `recipe-aurora-marketing`
- `recipe-warm-restraint`
- `style-glassmorphism`
- `aesthetic-frutiger-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference - identical chrome over two different background worlds mid-swap -->
