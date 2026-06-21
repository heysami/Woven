---
techniqueId: letterbox-stage
name: Letterbox stage (UI lives in the matte)
category: composition
subCategory: video
role: hero
binding: none
medium: video
pairsPrototypes: [recipe-editorial-magazine, recipe-warm-restraint, aesthetic-dieselpunk, aesthetic-cassette-futurism, aesthetic-dark-academia]
notForUseWhen: The design language is full-bleed everywhere else - one letterboxed scene in an edge-to-edge piece reads as a broken asset, not cinema; commit the whole piece or skip it. Also wrong on portrait/mobile-first viewports, where a 2.39:1 band shrinks to a sliver.
images:
  - src: motion-letterbox-stage-ui.png
    reason: Motion technique UI mockup.
  - src: motion-letterbox-stage-isolated.png
    reason: Signature technique, isolated.
---

# Letterbox stage (UI lives in the matte)

The video plays inside a 2.39:1 cinematic band centered in the viewport while the UI lives in the matte bars - kicker in the top bar, headline + CTA in the bottom bar - and the bars are page-background-coloured, so the stage reads as a deliberate proscenium rather than a cropped or letterboxed file.

## Motion signature

- `binding: none` - the stage composes with any choreography; under wheel-step the band's CONTENT transitions (cut, crossfade) while the bars and their slots stay fixed, which makes letterbox-stage the cinematic sibling of background-swap-fixed-ui.
- The band runs a 6-10s seamless ambient loop with cinematic camera grammar allowed INSIDE the frame (slow push-in ≤5% scale, gentle pan) - the proscenium gives permission for camera moves that full-bleed scenes forbid.
- Bar text changes are the only motion outside the band: 150ms out / 150ms in, in place.
- At 1920×1080 the band is 1920×803: top bar 138px, bottom bar 139px - enough for one kicker line and one display line + CTA respectively. The bars are styled page surface (background-color, maybe a hairline rule along the band edge), never black-by-default.

## Asset generation spec

- **Resolution**: generate at 1920×1080 minimum and CROP to 2.39:1 (1920×803) at build time - prompting native 2.39:1 is unreliable across providers; generating 16:9 with a center-band composition and cropping is deterministic. The crop discards the top and bottom 12.8% - nothing essential may live there.
- **Composition**: compose FOR the band - horizon and subject mass inside the central 74% of frame height; wide cinematic staging (subject on a third WITHIN the band, atmospheric depth, strong horizontals). Prompt the band explicitly: "all key elements within the central horizontal band of frame".
- **In-band quiet zone still applies**: if any UI overlays the band itself (rare - prefer the bars), it obeys quiet-zone-headline; default is ALL type in the matte, band kept pure image.
- **Negative prompt**: no text, no watermark, no letterboxing (the asset itself must be full-frame - WE cut the mattes), no border, no important detail near top or bottom edges, no vertical compositions.

## Interaction binding

```js
// The stage is layout, not listener - bars own the type, the band owns the film.
const W = innerWidth, bandH = Math.round(W / 2.39);
const barH = Math.max((innerHeight - bandH) / 2, 0.12 * innerHeight); // bars never thinner than 12vh
stage.style.gridTemplateRows = `${barH}px 1fr ${barH}px`;
// rows: top bar (kicker) / video band (object-fit: cover) / bottom bar (headline + CTA)
const v = stage.querySelector('video');   // muted + playsinline + loop + autoplay
new IntersectionObserver(([e]) => e.isIntersecting ? v.play() : v.pause(),
  { threshold: 0.2 }).observe(stage);
```

- Below ~1.5:1 viewport aspect the bars eat the screen: at that breakpoint restack to band-top (16:9) + single text panel below - do not let the band fall under 45% of viewport height.
- `muted playsinline` mandatory; poster from the loop's median frame so the pre-play band is already cinematic.

## UI composition rules

- Top bar: kicker / eyebrow only (11-13px caps, tracked +8%), horizontally aligned with the bottom bar's headline for one vertical axis.
- Bottom bar: one display headline (clamp 28-44px - the bar height is the constraint, not the viewport) + one CTA inline to its right; never two lines of headline in a 139px bar.
- Bars match the page background EXACTLY (same token, not "close black") - the moment the bars read as part of the video file, the technique has failed; an optional 1px hairline along each band edge declares the proscenium.

## Example asset prompt template

> Cinematic wide for a letterbox stage: a 1940s diesel locomotive crossing a steel viaduct at dusk, staged wide with all key elements within the central horizontal band of frame and nothing important near the top or bottom edges, locomotive anchored on the left third moving right, warm sodium light against blue dusk haze, very slow push-in, edge-to-edge full-frame render, photoreal film still quality, 1920x1080, 8 second seamless loop, no text, no watermark, no letterboxing, no border, no vertical composition.

## When to use

- Film-grammar brands: heritage, automotive, fashion film, documentary-flavored storytelling.
- Scenes whose footage earns camera moves - the proscenium licenses push-ins that full-bleed forbids.
- Pieces where the type system is strong enough to hold two slim fixed slots for the whole runtime.

## When NOT to use

- Mixed with full-bleed scenes in one piece, or on portrait viewports - see notForUseWhen.
- UI-heavy scenes (spec lists, hotspots) - two slim bars can't hold them; use frame-hold-ui-sync full-bleed.
- When no video provider is wired - degrade to a generated raster in the same 2.39:1 band with a 30s push-in (scale 1.0 → 1.05 on the oversized still); bars and type identical.

## Performance notes

- The band video is smaller than full-bleed (≈74% of the pixels) - ≤6MB loops; `object-fit: cover` inside the band, never scale the element itself.
- Bars are plain DOM on the page background - zero compositing cost; only the band layer composites.
- `prefers-reduced-motion`: pause on the poster frame and disable the push-in; a held cinematic still in a proscenium is a complete composition.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-warm-restraint`
- `aesthetic-dieselpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference - 2.39:1 video band with kicker in the top matte and headline + CTA in the bottom matte -->
