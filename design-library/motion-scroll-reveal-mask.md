---
techniqueId: scroll-reveal-mask
name: Scroll-reveal mask (aperture opens onto full-bleed video)
category: scroll-driven
subCategory: video
role: hero
binding: scroll-progress
medium: video
pairsPrototypes: [recipe-neo-grotesque-portfolio, recipe-editorial-magazine, recipe-y2k-memphis-loud, style-bold-display, aesthetic-dreamcore]
notForUseWhen: The video must be legible from the first pixel (the early mask hides 95% of it), or the page background and the brief reject a hard graphic gesture — the mask IS a loud editorial move, not a neutral one.
---

# Scroll-reveal mask (aperture opens onto full-bleed video)

Scroll progress expands a mask — a circle, the headline's own glyphs, or a widening aperture — over an already-playing full-bleed video, until the opening swallows the viewport and the video stands edge-to-edge as the section's hero.

## Motion signature

- The video loops quietly underneath from load (`autoplay muted playsinline loop`); scroll drives only the MASK, never playback — decoupling them keeps both cheap and smooth.
- Progress 0→1 across a 150–200vh pinned runway maps to the mask radius: `clip-path: circle(calc(4% + progress * 146%) at 50% 45%)` — 150% final radius guarantees full coverage at every aspect ratio.
- Eased: apply progress through `easeInCubic` (`p*p*p`) so the opening starts as a keyhole and accelerates into the engulf — linear growth feels bureaucratic.
- Glyph variant: the headline is an SVG `<mask>` over the video; scroll scales the text from 1× to ~40× around its optical center until the counters of one letter become the frame.
- Bidirectional: scrolling up irises the mask closed again — pure function of progress.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; the clip is a seamless ambient loop, 6–10s, loop point invisible (first and last frame match).
- **Composition**: the video must read at TWO scales — a focal point at the mask's origin (50% 45%) that intrigues through a 4%-radius keyhole, and a full-frame composition with a quiet zone (one third) for the post-reveal UI.
- **Continuity**: continuous ambient motion (drift, shimmer, slow flow), no cuts, no camera moves — a cut glimpsed through a half-open mask reads as a malfunction.
- **Loudness gradient**: motion should be calm at the origin point and may grow bolder toward the edges — the reveal then escalates naturally as more frame appears.
- **Negative prompt**: no text, no watermark, no letterboxing, no scene cut, no camera movement, no strobe or flicker.

## Interaction binding

```js
const v = scene.querySelector('video'); // autoplay muted playsinline loop
addEventListener('scroll', () => {
  const r = maskWrap.getBoundingClientRect();
  const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
  const e = p * p * p; // easeInCubic — keyhole first, engulf last
  frame.style.clipPath = `circle(calc(4% + ${e * 146}%) at 50% 45%)`;
}, { passive: true });
```

- The pin: 200vh wrapper; the masked frame `position: sticky; top: 0; height: 100vh`.
- Apply `clip-path` to a wrapper div, not the `<video>` element directly — Safari repaints masked video poorly; the wrapper keeps the video layer untouched.

## UI composition rules

- Pre-reveal, the page surface OUTSIDE the mask is the UI surface: headline and kicker sit on the solid page background beside the keyhole.
- At progress ≈0.6 the page-surface copy fades out (200ms); post-reveal UI fades into the video's quiet zone at progress ≈0.85 — never both visible while the mask moves.
- The mask origin must not sit under the pre-reveal headline; offset one of them so the opening never eats the words mid-read.

## Example asset prompt template

> Seamless ambient loop: slow-drifting iridescent ink clouds in deep water, the calmest and most luminous swirl centered slightly above frame center, motion growing bolder toward the frame edges, the right third comparatively dark and quiet, no cuts, fixed camera, loops perfectly with matching first and last frame, photoreal, 1920x1080, 8 seconds, no text, no watermark, no letterboxing, no flicker.

## When to use

- Editorial and portfolio heroes that earn a theatrical curtain-up.
- Brand moments where the headline-glyph variant fuses wordmark and world.
- Second-screen sections following a quiet text opener — the contrast is the point.

## When NOT to use

- Conversion-critical heroes where the CTA must be visible immediately — the reveal delays everything by 150vh.
- Subtle, restrained briefs (warm-restraint, hairline systems) — an iris wipe is inherently loud.
- When no video provider is wired — degrade to a generated still under the same scroll-driven `clip-path` plus a 20s CSS `transform: scale(1→1.06)` drift on the still.

## Performance notes

- ≤8MB loop; `preload="auto"` since the video is visible (through the keyhole) from the start.
- `clip-path: circle()` animates on the compositor in Blink/WebKit; avoid `mask-image` with animated gradients — it repaints every frame.
- `prefers-reduced-motion`: skip the pin entirely; show the video's poster frame full-bleed (mask open) as a static hero.

## Pairs with (prototype slugs)

- `recipe-neo-grotesque-portfolio`
- `recipe-editorial-magazine`
- `recipe-y2k-memphis-loud`
- `style-bold-display`
- `aesthetic-dreamcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference — half-open circular mask over the loop with the pre-reveal headline beside it -->
