---
techniqueId: slow-push-zoom
name: Slow push zoom (Ken-Burns gravity on an oversized still)
category: ambient
subCategory: raster
role: hero
binding: none
medium: raster
pairsPrototypes: [recipe-editorial-magazine, recipe-neo-grotesque-portfolio, style-bold-display, aesthetic-dieselpunk, aesthetic-dark-academia]
notForUseWhen: The brief demands genuinely living imagery (a zoom on a frozen crowd reads as a haunted photograph — use video techniques), the asset can only be generated at 1080p (the push will soften it), or the section cycles many images fast (push-zoom needs dwell time to register).
images:
  - src: motion-slow-push-zoom-ui.png
    reason: Motion technique UI mockup.
  - src: motion-slow-push-zoom-isolated.png
    reason: Signature technique, isolated.
---

# Slow push zoom (Ken-Burns gravity on an oversized still)

A single oversized generated still scales and pans almost imperceptibly — a 1.0→1.08× push over 20–40 seconds — giving a static hero cinematic gravity with zero video dependency; the cheapest "always something in motion" in the catalogue.

## Motion signature

- Scale travels 1.0→1.06–1.08× over a 20–40s cycle with `ease-in-out`, then reverses (alternate) — at this rate motion is subliminal; visitors feel the image is alive without seeing it move.
- Pair the push with a drift: simultaneous translate of 1–2% of frame width along ONE axis, direction chosen to move INTO the subject (push toward the lighthouse, not away).
- Alternate direction per scene: hero pushes in, the next push-zoom section pulls out — two consecutive same-direction zooms read as a slideshow template.
- Never faster than 0.3%/s of scale. The moment a visitor can watch the edge of the image crawl, the technique has failed.
- `transform: scale() translate()` on the image only — animating width/background-size causes constant raster resampling.

## Asset generation spec

- **Resolution**: 2560×1440 minimum (2.5K+), ideally 3200×1800 — the 1.08× push crops into the image, and a 1080p source goes soft exactly when the visitor is most invested. Generate large; the push must never resample above 1:1.
- **Composition**: subject on one third, quiet zone opposite for UI; CRITICALLY, compose for both ends of the push — the quiet zone must survive the 8% crop, so keep a 10% safety margin between the subject and the quiet zone boundary at scale 1.0.
- **Detail density**: push-zooms reward texture (fog, brick, crowd, machinery) — flat gradients show banding when scaled.
- **Negative prompt**: no text, no watermark, no letterboxing, no vignette (vignettes visibly slide during pans), no border.

## Interaction binding

```js
// No input binding — ambient CSS drives everything.
const img = scene.querySelector('.push');
img.style.animation = 'push 32s ease-in-out infinite alternate';
new IntersectionObserver(([e]) => {
  img.style.animationPlayState = e.isIntersecting ? 'running' : 'paused';
}, { threshold: 0.05 }).observe(scene);
```

```css
@keyframes push {
  from { transform: scale(1) translate(0, 0); }
  to   { transform: scale(1.08) translate(-1.5%, -0.8%); }
}
.push { will-change: transform; transform-origin: 62% 45%; /* the subject */ }
```

- `transform-origin` sits ON the subject so the push moves toward it; origin at center pushes into nothing.
- This technique IS its own no-video fallback — it's the canonical raster + CSS answer, and the standard degrade target other entries point to.

## UI composition rules

- UI fixed and still in the quiet zone; verify clearance at scale 1.08, the tight end of the push.
- Pure inversion of duty: the image moves, the UI never does — adding entrance animations on top of a push-zoom double-books the motion budget.
- Multi-scene pages: stagger cycle lengths (28s / 32s / 38s) so sections never sync up and pulse together.

## Example asset prompt template

> Cinematic wide still: a fog-wrapped brick lighthouse on a cliff anchored at the right third, textured storm sky and detailed sea filling the frame edge to edge, the left third compositionally calm and open for interface, dramatic side light, extremely high detail, photoreal, 3200x1800, no text, no watermark, no letterboxing, no vignette, no border.

## When to use

- Heroes and section openers when no video provider is wired — the default ambient move of the raster-only stack.
- Editorial and documentary registers where a photograph's stillness is the point but dead pixels aren't.
- Budget-constrained builds: one generation, zero decode cost, full-session motion.

## When NOT to use

- Scenes whose content implies motion (waves mid-crash, a runner mid-stride) — zooming a frozen instant feels eerie; pick a settled scene or use video.
- Under reading-length text — even subliminal drift below paragraphs is fatigue.
- Stacked with any other animated layer in the same scene — push-zoom is a solo instrument.

## Performance notes

- One image, WebP/AVIF, ≤1.5MB at 2.5K+ — compress aggressively; the slow motion hides compression artifacts well.
- `will-change: transform` only while on-screen; remove it when paused to release the compositor layer.
- `prefers-reduced-motion`: `animation: none`, hold at scale 1.0 — the composition was designed to stand still.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-neo-grotesque-portfolio`
- `style-bold-display`
- `aesthetic-dieselpunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference — oversized still mid-push with the headline holding the untouched quiet third -->
