---
techniqueId: pointer-parallax-layers
name: Pointer parallax layers (faux-3D depth from stacked rasters)
category: pointer-driven
subCategory: layered-raster
role: hero
binding: pointer-xy
medium: layered-raster
pairsPrototypes: [recipe-editorial-magazine, style-aurorism, aesthetic-frutiger-aero, aesthetic-dreamcore, aesthetic-solarpunk]
notForUseWhen: The scene has no natural depth planes (flat graphic, single object on void), the hero must carry real photographic continuity (layer seams betray themselves on humans mid-frame), or the page already runs a heavier pointer binding in the same viewport.
images:
  - src: motion-pointer-parallax-layers-ui.png
    reason: Motion technique UI mockup.
  - src: motion-pointer-parallax-layers-isolated.png
    reason: Signature technique, isolated.
---

# Pointer parallax layers (faux-3D depth from stacked rasters)

Three to six generated raster layers — background, midground, foreground, atmosphere — translate at different rates as the pointer moves, so the flat hero acquires believable depth that tilts toward the visitor (the moooi a-life-extraordinary pattern).

## Motion signature

- Each layer gets a depth coefficient: bg ±6px, mid ±14px, fg ±28px, atmosphere ±36px of total travel at full pointer deflection — near layers move MORE and opposite-feeling, exactly like looking past a window frame.
- Pointer position normalized to −1…1 from viewport center; layers translate via `transform: translate3d()` only — never top/left.
- Eased pursuit per layer: `current += (target - current) * 0.06` per rAF; deeper layers may use 0.04 so the stack settles back-to-front, adding ~150ms of organic lag gradient.
- Optional ±1.5° rotateX/rotateY on the whole stack (perspective: 1200px) for the tilt-card read — beyond 2° the layer edges show.
- No idle animation needed: the resting composition is the generated scene itself.

## Asset generation spec

- **Resolution**: every layer 1920×1080 minimum, generated ~8% oversize (2080×1170) so max translation never exposes a raw edge.
- **Layer strategy**: write ONE master scene prompt first, then split it into per-layer prompts that each repeat the master's light direction, palette hexes, and camera ("same scene, same golden side light from upper left"): bg = full-frame environment; mid = the subject band; fg + atmosphere = transparent PNGs (cutout foliage, particles, mist) on alpha.
- **Composition**: master prompt anchors the subject on one third and reserves the opposite third quiet across ALL layers — a foreground branch drifting over the headline at full deflection is the classic failure.
- **Consistency check**: composite the stack at rest before shipping; mismatched light direction between layers reads instantly as collage.
- **Negative prompt**: no text, no watermark, no letterboxing, no vignette, no depth-of-field blur baked into fg layers (blur belongs to CSS, per-layer, tunable).

## Interaction binding

```js
const layers = [...scene.querySelectorAll('[data-depth]')];
let tx = 0, ty = 0, cx = 0, cy = 0;
addEventListener('pointermove', e => {
  tx = (e.clientX / innerWidth - 0.5) * 2;
  ty = (e.clientY / innerHeight - 0.5) * 2;
}, { passive: true });
(function tick() {
  cx += (tx - cx) * 0.06; cy += (ty - cy) * 0.06;
  layers.forEach(l => {
    const d = +l.dataset.depth; // 6, 14, 28, 36
    l.style.transform = `translate3d(${-cx * d}px, ${-cy * d}px, 0)`;
  });
  requestAnimationFrame(tick);
})();
```

- Mobile fallback: `deviceorientation` beta/gamma onto the same −1…1 axes (gyro gate), else hand the stack to the depth-drift-layers autonomous behaviour.
- This IS the no-video technique — rasters + CSS transforms, no provider dependency.

## UI composition rules

- UI sits between layers, not on top: slot the headline above bg/mid but below fg/atmosphere (`z-index` interleave) so a mist layer drifts OVER the type by a few pixels — that occlusion sells the depth more than any translation.
- Verify type clearance at all four pointer extremes, not just rest.
- UI itself may carry depth 2–4px maximum; more and the text smears while reading.

## Example asset prompt template

> Master scene: a lone lighthouse on a cliff anchored on the left third, vast pastel dawn sky filling the right two thirds, golden side light from upper right, painterly photoreal, 2080x1170, no text, no watermark, no vignette. Layer 2 of 4: same scene, same golden side light from upper right, only the midground cliff and lighthouse, isolated on transparent background, 2080x1170, no depth-of-field blur, no text, no watermark.

## When to use

- Scenic, environmental, or illustrated heroes — landscapes, interiors, dioramas, dream spaces.
- Briefs that ask for "depth" or "a world you could step into" without WebGL.
- The default substitute wherever mouse-scrub-look was rejected for having no face.

## When NOT to use

- Single-object-on-void heroes — one layer parallaxing alone is just a wobbly image; use mouse-scrub-orbit.
- Photographic humans crossing layer boundaries — hair and shoulders seam visibly.
- Budget for only one generated asset — this technique needs 3–6 coherent generations or it isn't this technique.

## Performance notes

- Total stack weight ≤3MB (WebP/AVIF per layer, fg alphas are cheap); `will-change: transform` on layers, removed when off-screen.
- One shared rAF loop for all layers; pause via `IntersectionObserver`.
- `prefers-reduced-motion`: render the resting composite, no pointer binding — the scene is a finished still by design.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `style-aurorism`
- `aesthetic-frutiger-aero`
- `aesthetic-dreamcore`
- `aesthetic-solarpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference — layered scene tilted at pointer extreme with headline interleaved between mid and fg layers -->
