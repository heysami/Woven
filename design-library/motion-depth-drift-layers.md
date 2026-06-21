---
techniqueId: depth-drift-layers
name: Depth-drift layers (ambient faux-3D, no pointer required)
category: ambient
subCategory: layered-raster
role: background
binding: none
medium: layered-raster
pairsPrototypes: [recipe-scientific-infra-marketing, style-glassmorphism, aesthetic-frutiger-dark-aero, aesthetic-dreamcore, aesthetic-vaporwave]
notForUseWhen: The scene has no plausible depth planes (flat graphic systems), the same viewport already runs pointer-parallax-layers (they are the same stack - pick one driver), or layer-consistent generation budget (3-4 coherent images) isn't available.
images:
  - src: motion-depth-drift-layers-ui.png
    reason: Motion technique UI mockup.
  - src: motion-depth-drift-layers-isolated.png
    reason: Signature technique, isolated.
---

# Depth-drift layers (ambient faux-3D, no pointer required)

Three to four generated raster layers counter-drift autonomously at depth-proportional speeds - background barely creeping, foreground gliding - producing a slow ambient parallax with no input at all; the sibling of pointer-parallax-layers with the pointer removed and time as the driver.

## Motion signature

- Each layer drifts on its own loop: bg ±4px over 60s, mid ±10px over 45s, fg ±18px over 35s, atmosphere ±26px over 28s - near layers move farther AND faster, the parallax law that sells depth.
- Counter-drift: adjacent layers travel in opposing directions (bg drifts left while mid drifts right) - parallel drift reads as a broken pan; opposition reads as depth.
- All travel via `transform: translate3d()` with `ease-in-out` alternating keyframes; mismatched prime-ish durations (60/45/35/28) keep the stack from ever visibly syncing - the full pattern repeats only every ~21 minutes.
- Total apparent motion stays subliminal: no layer exceeds ~1px/s. This is a background; if the visitor watches it move, it's overdriven.
- No idle/active states - it runs whenever on-screen, indifferent to the visitor.

## Asset generation spec

- **Resolution**: every layer 1920×1080 minimum, generated ~6% oversize (2040×1145) so max drift never exposes an edge.
- **Layer strategy**: identical to pointer-parallax-layers - one master scene prompt, split per layer with the master's light direction, palette hexes, and camera repeated verbatim in each ("same scene, same cool light from upper right"); bg full-frame, mid = subject band, fg + atmosphere transparent PNGs on alpha.
- **Composition**: master prompt reserves the quiet zone across all layers AND across the full drift envelope - check the fg layer's extremes (±18px) against the headline box.
- **Consistency check**: composite at rest; any light-direction mismatch between layers reads as collage immediately.
- **Negative prompt**: no text, no watermark, no letterboxing, no vignette, no baked depth-of-field blur in fg layers (blur is CSS, per-layer, tunable).

## Interaction binding

```js
// No input binding - CSS animations drive each layer; JS handles lifecycle only.
const layers = [...scene.querySelectorAll('[data-drift]')];
new IntersectionObserver(([e]) => {
  layers.forEach(l => l.style.animationPlayState = e.isIntersecting ? 'running' : 'paused');
}, { threshold: 0.05 }).observe(scene);
```

```css
.bg  { animation: driftL 60s ease-in-out infinite alternate; }
.mid { animation: driftR 45s ease-in-out infinite alternate; }
.fg  { animation: driftL 35s ease-in-out infinite alternate; }
.atm { animation: driftR 28s ease-in-out infinite alternate; }
@keyframes driftL { from { transform: translate3d(0,0,0); } to { transform: translate3d(-18px,-6px,0); } }
@keyframes driftR { from { transform: translate3d(0,0,0); } to { transform: translate3d(14px,5px,0); } }
```

- This IS the no-video technique - rasters + CSS keyframes, zero provider dependency, zero decode cost.
- Upgrade path: the identical stack accepts the pointer-parallax-layers binding later - build the layers once, choose the driver per page.

## UI composition rules

- UI interleaves into the stack exactly as in pointer-parallax-layers: headline above bg/mid, below fg/atmosphere, so a mist layer occasionally drifts a few pixels over the type - the occlusion is the depth proof.
- Verify type clearance at every layer's drift extreme, not at rest.
- Because motion is autonomous and slow, this is one of the few techniques safe BEHIND moderate content density - cards and short copy can sit on it; long-form reading still can't.

## Example asset prompt template

> Master scene: a deep blue server-hall horizon anchored low in frame, cool light from upper right, calm dark upper-left two-thirds for interface, subtle haze, photoreal, 2040x1145, no text, no watermark, no vignette. Layer 4 of 4: same scene, same cool light from upper right, only the foreground haze wisps, isolated on transparent background, 2040x1145, no depth-of-field blur, no text, no watermark.

## When to use

- Section and page backgrounds needing quiet dimensionality with no video budget and no pointer dependency.
- Touch-first audiences - this delivers what pointer-parallax-layers can't on mobile, with the same assets.
- Scientific / infrastructure registers where motion must feel ambient and systemic, never reactive.

## When NOT to use

- Hero moments that should answer the visitor - use the pointer-driven sibling; ambient drift ignores them by design.
- Single-layer scenes - one drifting image is a slow pan, which is slow-push-zoom's job done worse.
- Pages stacking several drift scenes - more than two in one page turns subliminal into seasick.

## Performance notes

- Stack ≤3MB total (WebP/AVIF; alpha layers are cheap); `will-change: transform` only while running.
- CSS animations cost ~0 main-thread time; the only real cost is compositor memory - flatten to 3 layers on devices reporting `deviceMemory < 4`.
- `prefers-reduced-motion`: pause all animations at the rest composite - the master scene is a finished still by design.

## Pairs with (prototype slugs)

- `recipe-scientific-infra-marketing`
- `style-glassmorphism`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-dreamcore`
- `aesthetic-vaporwave`

<!-- image: sample-1.png -->
<!-- reason: representative reference - layered scene mid-drift with haze crossing the headline edge, no pointer involved -->
