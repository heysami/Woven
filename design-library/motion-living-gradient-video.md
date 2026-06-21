---
techniqueId: living-gradient-video
name: Living gradient video (the brand palette as weather)
category: ambient
subCategory: video
role: background
binding: none
medium: video
pairsPrototypes: [recipe-aurora-marketing, recipe-ai-foundry-dark, style-aurorism, style-holographic, aesthetic-vaporwave]
notForUseWhen: The brand is flat/graphic with hard-edged color systems (a drifting gradient contradicts the language), the palette hexes aren't pinned down yet (the prompt needs exact colors), or CSS mesh gradients already deliver the brief - don't spend a video on what two animated radial-gradients can do.
images:
  - src: motion-living-gradient-video-ui.png
    reason: Motion technique UI mockup.
  - src: motion-living-gradient-video-isolated.png
    reason: Signature technique, isolated.
---

# Living gradient video (the brand palette as weather)

A generated abstract color-field - ink in water, aurora curtains, molten gradient, slow smoke in brand hues - loops full-bleed beneath the page content, turning the palette itself into a living material instead of a fill.

## Motion signature

- Autonomous: `autoplay muted playsinline loop`, no binding; the gradient is substrate, never subject.
- Motion scale is glacial: color regions migrate across maybe 15% of the frame over the whole 12-20s loop. Fast-swirling color under type is the single most common way this technique fails review.
- Hue discipline: the loop must stay inside the declared palette at every frame - generation models love to pass through unplanned intermediate hues mid-blend; the prompt names every permitted hex explicitly and forbids others.
- Seamless loop or 1s crossfade-loop fallback (two staggered copies, crossfade before each end) - gradients make seams MORE visible than photographic scenes, not less, because there's nothing else to look at.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; gradients survive upscale poorly when banded, so request high bit-depth / dithered output where available.
- **Palette binding**: name every hue per-hex in the prompt - "deep indigo #1a1040, electric violet #7c3aed, soft cyan #67e8f9" - never "purple and blue"; the video must drop into the design system, not near it.
- **Composition / luminance discipline**: prompt a quiet-zone luminance contract just like photographic atmosphere - e.g. "the upper-left two-thirds remains dark, below 20% luminance, at all times; the bright cyan activity stays in the lower-right." Type placement is decided by that sentence.
- **Duration**: 12-20s seamless loop.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no flicker, no colors outside the named palette, no white flashes.

## Interaction binding

```js
const v = scene.querySelector('video');
// No input binding - lifecycle only.
new IntersectionObserver(([e]) => {
  e.isIntersecting ? v.play() : v.pause();
}, { threshold: 0.05 }).observe(scene);
document.addEventListener('visibilitychange', () => {
  document.hidden ? v.pause() : v.play();
});
```

- `muted playsinline loop preload="auto"` for the hero instance; `metadata` for any below-fold reuse.
- `poster` = a mid-loop frame whose quiet zone is at its darkest - the worst-case frame for type is the honest poster.
- Tint safety net: a CSS `background` on the scene set to the dominant hex, visible for the frames before the video decodes - no white flash into color.

## UI composition rules

- Type sits only in the luminance-contracted quiet zone; QA samples that region across the WHOLE loop and requires ≥4.5:1 contrast at the worst frame.
- Glass / blur panels (backdrop-filter) are this technique's natural companions - the gradient motion refracting through frosted cards is free production value; keep blur ≥24px so moving color becomes glow, not distraction.
- Never key UI colors off the video's current frame at runtime; the palette is fixed in tokens, the video conforms to it - not the other way around.

## Example asset prompt template

> Abstract background film: slow liquid ink clouds in deep indigo #1a1040 and electric violet #7c3aed with occasional soft cyan #67e8f9 wisps, drifting almost imperceptibly, the upper-left two-thirds of frame staying dark and calm below 20 percent luminance at all times, all bright activity confined to the lower-right, no recognizable shapes, fixed camera, constant exposure, seamless loop where the final frame matches the first, 1920x1080, 16 seconds, no text, no watermark, no flicker, no colors outside the named palette, no white flashes.

## When to use

- AI, dev-tools, and aurora-register marketing where the brand IS a gradient and it should feel alive.
- Dark heroes needing depth and motion with zero photographic content.
- Behind glassmorphic or holographic component systems that want something to refract.

## When NOT to use

- Light, paper-like, or editorial registers - a living gradient is loud even when slow.
- Anywhere CSS gradients suffice - two layered radial-gradients on a 30s hue-rotate cost 0 bytes of media; reach for video only when the brief needs organic texture (ink grain, aurora filament) CSS can't fake.
- When no video provider is wired - degrade to raster + CSS: one generated gradient still, oversized 130%, on a 45s background-position drift with a counter-rotating CSS gradient overlay at 30% opacity.

## Performance notes

- ≤6MB; gradients compress horribly at low bitrate (banding) - prefer AV1/H.265, allocate bitrate to smoothness over resolution.
- One instance per page; reusing the texture elsewhere should reuse the SAME element via CSS, not decode a second copy.
- `prefers-reduced-motion`: the poster still - its quiet-zone-at-darkest framing was chosen for exactly this swap.

## Pairs with (prototype slugs)

- `recipe-aurora-marketing`
- `recipe-ai-foundry-dark`
- `style-aurorism`
- `style-holographic`
- `aesthetic-vaporwave`

<!-- image: sample-1.png -->
<!-- reason: representative reference - type resting in the dark contracted zone while brand-hex ink drifts through the lower right -->
