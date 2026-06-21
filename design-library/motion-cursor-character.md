---
techniqueId: cursor-character
name: Cursor as character (velocity-deforming, identity-swapping pointer)
category: pointer-driven
subCategory: dom
role: chrome
binding: pointer-xy
medium: dom-svg
pairsPrototypes: [aesthetic-positivity-kawaii, aesthetic-y2k-memphis-loud, style-doodle, aesthetic-zine-type-wall, recipe-neo-grotesque-portfolio]
notForUseWhen: Touch-primary audiences (no cursor exists - the entire device evaporates on mobile), data-dense or form-heavy surfaces (precision pointing beats personality), or restrained registers where an expressive cursor is the loudest thing on the page.
images:
  - src: motion-cursor-character-ui.png
    reason: Motion technique UI mockup.
  - src: motion-cursor-character-isolated.png
    reason: Signature technique, isolated.
---

# Cursor as character (velocity-deforming, identity-swapping pointer)

The pointer stops being an arrow and becomes a SUBJECT: it squashes and
stretches with velocity, rotates to its direction of travel, swaps identity by
context (a character sprite per section, a labeled lozenge over draggables),
and can shed a decaying trail of images along its path. Observed as a defining
device on Japanese editorial/toy sites - the cursor carries personality the
layout deliberately withholds.

## Motion signature

- A fixed-position element follows the pointer through a damped pursuit
  (`cur += (target - cur) * 0.18` per frame) - the lag is the life; a cursor
  glued 1:1 to the pointer is just a skin.
- Velocity deformation: from per-frame delta, derive speed and heading; apply
  `rotate(heading) scaleX(1 + k·speed) scaleY(1 − k·speed)` (k ≈ 0.004,
  clamped ±0.35). At rest it relaxes to a circle - squash-and-stretch straight
  from animation canon.
- Identity swaps: body classes (`cursor-1`…`cursor-n`, plus `-hover`
  variants) swap the cursor's sprite/shape per hovered context - a character
  per section, "DRAG" / "VIEW" / "PLAY" labels over interactive zones. Swap by
  crossfade (120ms), never instant.
- Trail variant: over designated zones the cursor spawns elements along its
  path (thumbnails, glyphs, petals) from a pre-mounted pool; each scales in,
  drifts, and fades over 600-1200ms. Pool size 30-50, recycled - never
  allocate per move.
- The native cursor is hidden ONLY where the custom one is active
  (`cursor: none` scoped, not global); over text inputs and selectable prose
  the native I-beam returns.

## Interaction binding

```js
let x = 0, y = 0, tx = 0, ty = 0, px = 0, py = 0;
addEventListener('pointermove', e => { tx = e.clientX; ty = e.clientY; }, { passive: true });
(function frame() {
  x += (tx - x) * 0.18; y += (ty - y) * 0.18;
  const vx = x - px, vy = y - py; px = x; py = y;
  const speed = Math.min(Math.hypot(vx, vy), 80);
  const ang = speed > 1 ? Math.atan2(vy, vx) : 0;
  const s = Math.min(speed * 0.004, 0.35);
  el.style.transform =
    `translate(${x}px,${y}px) rotate(${ang}rad) scale(${1 + s},${1 - s}) rotate(${-ang}rad)`;
  requestAnimationFrame(frame);
})();
```

- The double-rotate sandwich deforms along the travel axis without spinning
  the sprite's artwork.
- Touch devices: feature-detect (`matchMedia('(pointer: fine)')`) and mount
  nothing otherwise - the page must lose zero meaning without the cursor.
- `prefers-reduced-motion`: keep the identity swaps (they're informational),
  drop deformation and trails.

## UI composition rules

- The cursor is the ONE expressive chrome element - if the page also has
  marquees, confetti, and wobble, the cursor competes instead of starring.
- Contextual labels on the cursor ("DRAG", "VIEW") must duplicate, never
  replace, visible affordances - keyboard and touch users get the same
  information another way.
- Trail zones are bounded (a hero, a gallery), never page-wide.

## When to use

- Editorial/zine registers, portfolios, toy-like experience sites - anywhere
  the brief says "playful" and the layout itself stays disciplined.
- Drag-heavy galleries where a labeled cursor genuinely teaches the
  interaction.

## When NOT to use

- Mobile-first briefs (build something else; this is desktop-only charisma).
- Forms, tables, docs - anywhere precision pointing is the job.

## Performance notes

- One rAF loop for the whole system; transform-only (no layout/paint
  properties); the trail pool pre-mounted and recycled.
- Hide the element via `opacity` when the pointer leaves the viewport
  (`pointerleave` on `document`) or it ghosts at the last position.

## Pairs with (prototype slugs)

- `aesthetic-positivity-kawaii`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-zine-type-wall`
- `style-doodle`
- `recipe-neo-grotesque-portfolio`

<!-- image: sample-1.png -->
<!-- reason: representative reference - a blob cursor mid-flight, stretched along its travel direction, trailing three fading thumbnails -->
