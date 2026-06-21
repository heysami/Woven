---
techniqueId: lens-magnifier-reveal
name: Lens magnifier reveal (pointer-tracked circle of clarity)
category: pointer-driven
subCategory: dom-or-canvas
role: hero | editorial
binding: pointer-xy
medium: dom-duplicated-layer
pairsPrototypes: [style-oversized-neo-grotesque, aesthetic-monochrome-tech-editorial, recipe-neo-grotesque-portfolio, style-restrained-hairline, aesthetic-anti-design]
notForUseWhen: Touch-dominant audiences (no hover = no lens without a fallback budget), content that must be readable at all times (legal, pricing, forms), or pages already running a cursor-spotlight effect - two pointer-portals compete.
images:
  - src: motion-lens-magnifier-reveal-ui.png
    reason: Motion technique UI mockup.
  - src: motion-lens-magnifier-reveal-isolated.png
    reason: Signature technique, isolated.
---

# Lens magnifier reveal (pointer-tracked circle of clarity)

A circular lens rides the pointer across a deliberately degraded field -
blurred, halftoned, or dimmed - and inside the circle the content renders
SHARP and slightly magnified. The pixlspace pattern: the page withholds
clarity and hands the visitor a loupe; reading becomes a held gesture of
exploring. The inverse of a spotlight (which adds light); the lens adds
FOCUS - and optionally a different rendering register inside (sharp photo
inside halftone field, color inside mono).

## Motion signature

- TWO stacked copies of the same content: base layer degraded (blur 6-10px,
  or halftone material, or 35% dim), top layer clean - clipped to a circle.
- The clip circle tracks the pointer with damped pursuit
  (`cur += (target - cur) * 0.12`, ~120ms lag) - a held instrument, not a
  cursor skin.
- Magnification: the clean layer runs at `scale(1.15-1.4)` with
  `transform-origin` recomputed so the point under the lens stays fixed -
  the loupe physics that sells it.
- Lens diameter 160-280px desktop; a 1px hairline ring + faint inner
  rim-shadow gives the glass edge without skeuomorphic chrome.
- Idle >3s or `pointerleave`: lens eases shut (radius → 0 over 400ms). On
  return it reopens from the entry point.

## Implementation skeleton

```css
.lens-top {
  position: absolute; inset: 0;
  clip-path: circle(var(--r, 0px) at var(--lx) var(--ly));
  transform: scale(var(--mag, 1.25));
  transform-origin: var(--lx) var(--ly);
  will-change: clip-path, transform;
}
.lens-base { filter: blur(8px); }   /* or the halftone/dither material */
```

```js
addEventListener('pointermove', e => { tx = e.clientX; ty = e.clientY; }, { passive: true });
(function tick() {
  lx += (tx - lx) * 0.12;  ly += (ty - ly) * 0.12;
  el.style.setProperty('--lx', lx + 'px');
  el.style.setProperty('--ly', ly + 'px');
  requestAnimationFrame(tick);
})();
```

- The duplicated layer must be `aria-hidden="true"`; the BASE layer keeps the
  real, selectable, accessible text (degrade it visually, never semantically).
- Canvas/WebGL variant for media fields: render sharp into a circular
  scissor/mask - needed when the base runs a stylize-shader-pass.

## UI composition rules

- The degraded field must still COMPOSE - silhouettes of headlines readable,
  layout legible; the lens rewards attention, it must not gate comprehension.
- Nav, CTA, and any always-actionable UI stay OUTSIDE the effect, full-sharp.
- One lens per page. It is a signature, not a system.
- Pair the inside/outside registers deliberately: sharp-in-blur (focus),
  color-in-mono (memory), photo-in-halftone (print coming alive).

## Mobile / fallback

- `(pointer: coarse)`: lens rides a slow autonomous figure-eight path
  (20s loop) so the page still demonstrates itself; tap teleports the lens
  to the tap point with the same damped ease.
- `prefers-reduced-motion`: kill the pursuit; content renders sharp
  everywhere (the degraded field is withheld, not the content).

## Performance notes

- `clip-path` + `transform` only - both compositor-friendly; never animate
  `filter` on the base per frame.
- One rAF loop, passive listeners, no layout reads in the tick.
- The duplicated DOM doubles node count under the hero - keep the duplicated
  region to the hero section, not the whole page.

## When to use

- Editorial/portfolio heroes where "look closer" IS the brand message.
- Halftone/dither registers wanting one precision-optics counterpoint.
- Archive/gallery indexes - the lens as browsing instrument over a wall of
  thumbnails.

## When NOT to use

- Anything the visitor must read to proceed (pricing, forms, docs).
- Combined with cursor-spotlight or magnetic-cursor effects - one pointer
  metaphor per page.
- Dense app UIs - the lens is a marketing/editorial gesture.

## Pairs with (prototype slugs)

- `style-oversized-neo-grotesque`
- `aesthetic-monochrome-tech-editorial`
- `recipe-neo-grotesque-portfolio`
- `style-restrained-hairline`
- `aesthetic-anti-design`
