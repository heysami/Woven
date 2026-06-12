---
techniqueId: hover-activate-loop
name: Hover-activate loop (still wakes into its living version)
category: pointer-driven
subCategory: video
role: gallery
binding: hover
medium: video
pairsPrototypes: [recipe-neo-grotesque-portfolio, recipe-editorial-magazine, recipe-brutalist-web, style-oversized-neo-grotesque]
notForUseWhen: The grid has more than ~12 video tiles in one viewport (decode budget collapses), the tiles are smaller than ~240px wide (motion at thumbnail scale reads as noise), or hover has no meaning for the audience (touch-first) and no tap-to-play substitute is storyboarded.
images:
  - src: motion-hover-activate-loop-ui.png
    reason: Motion technique UI mockup.
  - src: motion-hover-activate-loop-isolated.png
    reason: Signature technique, isolated.
---

# Hover-activate loop (still wakes into its living version)

Gallery tiles and case-study cards each hold a poster still that crossfades into its own living loop on hover or keyboard focus — the grid is calm at rest, and whichever item the visitor considers wakes up under their attention.

## Motion signature

- Two stacked children per tile: the poster `<img>` above, the loop `<video>` below. Hover/focus: `video.play()` then fade the poster to opacity 0 over 240ms ease-out; leave: fade back over 320ms, `video.pause()` after the fade completes.
- Play is debounced 120ms — a cursor crossing the grid diagonally must not detonate every tile it grazes.
- The loop starts where it left off (`currentTime` preserved), so re-hovering continues the life rather than restarting a clip — restarts read as GIFs.
- Exactly one tile alive at a time is the default discipline; the storyboard may allow two adjacent for masonry layouts, never more.
- Optional 1.03× scale on the tile over the same 240ms — keep transform and crossfade on identical easing (`cubic-bezier(0.25, 0.1, 0.25, 1)`) so they read as one gesture.

## Asset generation spec

- **Resolution**: generate every loop at 1920×1080 even for tile display — tiles open into lightboxes/case pages and the asset must survive full-bleed; serve scaled.
- **Pair strategy**: still + loop generated from the SAME prompt and seed — the still is the loop's first frame (extract, don't regenerate), so the crossfade is invisible and the wake-up feels like time starting, not an image swap.
- **Composition**: subject centered or per the card's crop spec; motion contained within the subject (steam rises, fabric sways, screen scrolls) — camera moves inside a tile make the whole grid lurch.
- **Continuity**: seamless 4–8s loop, fixed camera, constant exposure; the last frame must rejoin the first invisibly.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no flicker.

## Interaction binding

```js
scene.querySelectorAll('.tile').forEach(tile => {
  const v = tile.querySelector('video');
  let t;
  const wake = () => { t = setTimeout(() => { v.play(); tile.classList.add('live'); }, 120); };
  const rest = () => {
    clearTimeout(t);
    tile.classList.remove('live');
    setTimeout(() => v.paused || v.pause(), 320); // after crossfade
  };
  tile.addEventListener('pointerenter', wake);
  tile.addEventListener('pointerleave', rest);
  tile.addEventListener('focusin', wake);
  tile.addEventListener('focusout', rest);
});
```

- Videos: `muted playsinline loop preload="metadata"` — metadata only; a 12-tile grid preloading `auto` is a megabyte bonfire.
- Touch fallback: first tap wakes the tile, second tap navigates; or storyboard a per-tile `IntersectionObserver` auto-wake at 60% visibility for mobile.

## UI composition rules

- Card chrome (title, tag, arrow) sits on the card surface OUTSIDE the asset crop, or in a fixed gradient scrim along the asset's bottom 22% — never floating mid-frame where the loop's motion runs under it.
- Hover state of the chrome (underline, arrow nudge) fires on the SAME 240ms clock as the crossfade — two timing systems on one card reads as jank.
- The poster, not the loop, is the layout contract: art-direct crops against stills.

## Example asset prompt template

> Case-study loop: a ceramic studio worktable, hands off-frame, a thrown vase spinning slowly on the wheel at center while everything else stays still, fixed camera, locked tripod, soft window light, constant exposure, seamless loop where the final frame matches the first, photoreal, 1920x1080, 6 seconds, no text, no watermark, no camera movement, no scene cut.

## When to use

- Portfolio grids, case-study indexes, product category tiles — anywhere a calm grid should reward consideration.
- Briefs that say "alive but not noisy" — the rest state is genuinely still.
- Editorial article cards where each story has a signature living image.

## When NOT to use

- Heroes — a single full-bleed asset waiting for hover wastes the viewport; use ambient-loop-atmosphere.
- Grids dense enough that several tiles sit under the pointer path constantly — the calm/wake contrast dies.
- When no video provider is wired — degrade to still-pair crossfade (two generated stills, same seed, "moment A" / "moment B") or a 12-frame raster sequence flipped at 8fps on hover.

## Performance notes

- ≤2.5MB per loop; cap simultaneous playing videos at 1 (enforce in code, not hope).
- Release decoded video memory on rest: after 30s un-hovered, set `v.src = ''` and restore lazily on next wake (keep the poster, the user never sees it).
- `prefers-reduced-motion`: posters only, hover does nothing to the imagery — card chrome hover states still work.

## Pairs with (prototype slugs)

- `recipe-neo-grotesque-portfolio`
- `recipe-editorial-magazine`
- `recipe-brutalist-web`
- `style-oversized-neo-grotesque`

<!-- image: sample-1.png -->
<!-- reason: representative reference — one grid tile awake and moving while its neighbors hold their posters -->
