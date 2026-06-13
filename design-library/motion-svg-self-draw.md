---
techniqueId: svg-self-draw
name: SVG self-draw (hand-made marks draw themselves in on scroll)
category: scroll-driven
subCategory: dom
role: entrance | chrome
binding: scroll-trigger
medium: dom-svg
pairsPrototypes: [style-doodle, style-outline-wireframe, style-kinetic-line-accents, aesthetic-cottagecore, aesthetic-craft-sketchbook, recipe-editorial-magazine]
notForUseWhen: The page's graphics are raster or filled-vector with no stroke skeleton (nothing to draw), the register is cool/corporate-precise (a hand drawing itself reads as warmth — kinetic-line-accents is the licensed cold variant), or there are more than ~12 draw-on moments per page (the device dies by repetition).
images:
  - src: motion-svg-self-draw-ui.png
    reason: Motion technique UI mockup.
  - src: motion-svg-self-draw-isolated.png
    reason: Signature technique, isolated.
---

# SVG self-draw (hand-made marks draw themselves in on scroll)

Every hand-made SVG on the page — lettered headlines, nav labels, full scene
illustrations, underlines, arrows — enters by drawing itself stroke-by-stroke,
as if an invisible hand sketches the interface in while you scroll. Observed as
a SYSTEM (not a one-off) on Japanese campaign sites: the entire chrome is
hand-drawn and the draw-on IS the page's entrance grammar.

## Motion signature

- The mechanism: `stroke-dasharray: L; stroke-dashoffset: L → 0` where `L =
  path.getTotalLength()`, triggered when the element enters the viewport
  (IntersectionObserver or ScrollTrigger), 600–1200ms per mark, ease-out.
- Filled artwork variant: draw the STROKE skeleton first, then cross-fade the
  fill in over the last 200ms (convert fill→stroke, animate, restore fill) —
  the mark sketches, then inks.
- Stagger multi-path drawings 60–120ms per path in drawing order (the order a
  human would draw: outline → details → hatching). Random order breaks the
  hand illusion.
- Radial variant for round marks (circles, crayon scribbles): a conic
  `clip-path` sweep around the center reads as one continuous stroke.
- Play ONCE per element, hold forever — re-drawing on every re-entry turns
  craft into a gimmick. Bidirectional scrubbing is wrong here.

## Asset requirements

- Source SVGs must be genuine stroke paths (hand-traced or plotter-style),
  variable in width if possible; `vector-effect: non-scaling-stroke` keeps
  strokes honest across breakpoints.
- Stroke timing budget: short marks (underline, arrow) 400–600ms; word-length
  lettering 800–1200ms; full scene illustrations 1500–2500ms with stagger.
  Nothing on screen should still be drawing 3s after it entered.
- The marks should be imperfect — wobble, pressure variation, overshoot at
  terminals. A geometrically perfect path drawing itself is kinetic-line-accents
  (its own entry), not this.

## Interaction binding

```js
document.querySelectorAll('.selfdraw path').forEach(p => {
  const L = p.getTotalLength();
  p.style.strokeDasharray = L;
  p.style.strokeDashoffset = L;
});
const io = new IntersectionObserver(es => es.forEach(e => {
  if (!e.isIntersecting) return;
  e.target.querySelectorAll('path').forEach((p, i) => {
    p.style.transition = `stroke-dashoffset .9s ${i * 0.08}s cubic-bezier(.4,0,.2,1)`;
    p.style.strokeDashoffset = 0;
  });
  io.unobserve(e.target);          // draw once, hold forever
}), { threshold: 0.35 });
document.querySelectorAll('.selfdraw').forEach(el => io.observe(el));
```

- `prefers-reduced-motion`: skip the animation, show all marks fully drawn.
- Pre-compute `getTotalLength()` once at load — never per frame.

## UI composition rules

- The draw-on applies to the page's GRAPHIC layer (lettered display, marks,
  illustrations); body copy stays webfont and appears by plain fade — text you
  read never draws itself.
- One mark drawing at a time per viewport region; simultaneous draws compete
  and neither reads.
- Pairs naturally with a paper-textured substrate (uncoated/linen/kraft) — the
  hand needs something to draw ON.

## When to use

- Hand-crafted registers: sketchbook campaigns, kids/education services,
  artisan/craft brands, illustrated storytelling.
- As the entrance system for `style-doodle` pages — doodle gives the skin,
  this gives it the hand.

## When NOT to use

- Precise/corporate registers (use `style-kinetic-line-accents` — same
  mechanism, ruler instead of hand).
- Pages with zero stroke-based art — retrofitting strokes onto filled logos
  reads as a loading glitch.

## Performance notes

- `stroke-dashoffset` animates cheaply, but >40 simultaneously-transitioning
  paths jank on low-end — batch by drawing, not by path.
- Inline the SVGs (fetch+inject if authored externally); `<img src>` SVGs
  can't be path-animated.

## Pairs with (prototype slugs)

- `style-doodle`
- `style-outline-wireframe`
- `style-kinetic-line-accents`
- `aesthetic-craft-sketchbook`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference — a hand-lettered headline two-thirds drawn, stroke skeleton visible, on warm paper -->
