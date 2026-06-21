---
techniqueId: drag-physics-cluster
name: Drag physics cluster (grabbable floating object swarm)
category: pointer-driven
subCategory: webgl-physics
role: hero
binding: pointer-drag
medium: webgl (three.js + rapier/cannon-es) or 2D fallback (matter.js)
pairsPrototypes: [recipe-restrained-ai-marketing, style-glassmorphism, recipe-bento-marketing, aesthetic-frutiger-aero, recipe-devtools-marketing]
notForUseWhen: The hero must communicate a SPECIFIC product image (the toy abstracts it away), touch-scroll-critical mobile heroes (drag fights scroll), or pages with another physics/simulation surface already running.
images:
  - src: motion-drag-physics-cluster-ui.png
    reason: Motion technique UI mockup.
  - src: motion-drag-physics-cluster-isolated.png
    reason: Signature technique, isolated.
---

# Drag physics cluster (grabbable floating object swarm)

A loose cluster of 8-30 identical 3D primitives - glass cubes, spheres,
branded tokens - floats weightless in the hero, and the visitor can GRAB any
of them: drag it, fling it, watch the cluster absorb the disturbance with
springy joints and settle back into formation. The "Interactive AI website"
pattern: the hero is a desk toy, the first three seconds of the visit become
play, and the material quality (transmission glass, soft studio light) does
the brand work while the physics does the delight.

## Motion signature

- Idle state is ALIVE: zero gravity, tiny per-body noise drift + slow
  collective rotation (one lap / 60-90s) - the cluster breathes; it never
  sits frozen waiting to be discovered.
- Bodies bind to a home anchor via spring joints (stiffness low, damping
  ~0.85 of critical) - displaced bodies return in 1.5-3s with ONE soft
  overshoot, never oscillating more than twice.
- Grab: raycast on `pointerdown` → kinematic drag via a pointer-spring (the
  body chases the cursor at damped lag, tilting from drag torque - rigid
  cursor-locking kills the mass illusion).
- Release: velocity carries (clamped to ~1.5 viewport-widths/s), neighbors
  get shoved, the swarm redistributes - collisions ON between bodies.
- Cursor states do real work: `grab` over a body, `grabbing` while held -
  the only affordance hint the toy needs.

## Implementation skeleton

```js
// three.js + rapier - per body: home spring + drag spring
world.timestep = 1 / 60;                       // fixed step, accumulator loop
for (const b of bodies) {
  const toHome = home[b.i].sub(b.translation());
  b.addForce(toHome.scale(STIFF).sub(b.linvel().scale(DAMP)), true);
}
if (held) {
  const toPtr = pointerWorld.sub(held.translation());
  held.addForce(toPtr.scale(DRAG_STIFF).sub(held.linvel().scale(DRAG_DAMP)), true);
}
```

- InstancedMesh for the bodies (one draw call); copy physics transforms into
  instance matrices per frame with interpolation on the render alpha.
- Material canon: MeshPhysicalMaterial transmission glass or soft matte clay
  - the cluster sells material fidelity at 20 samples per frame, so the
  material entry chosen (frosted-glass / dispersion-prism / matte-clay)
  carries half the effect.
- 2D fallback (no WebGL budget): matter.js circles under DOM/SVG sprites -
  same spring-home grammar, flat render.

## Interaction binding

- `pointerdown` on canvas → raycast; HIT: capture pointer, body to
  drag-spring. MISS: let the event fall through to the page (the canvas must
  not eat scroll/selection - `touch-action: pan-y` and only
  `preventDefault()` after a confirmed hit).
- Mobile: tap-flick works (drag during touch, release flings); cluster also
  responds to `deviceorientation` tilt (±15° gravity vector) behind the
  standard gyro gate.
- Idle >8s after interaction: a random body gets a gentle 1-body nudge -
  the toy reminds the visitor it's alive, once.

## UI composition rules

- Cluster anchored to one third of the hero, copy in the opposite quiet zone
  - and the home anchors define a BOUNDARY: springs strengthen near the copy
  column so no fling parks a cube over the headline.
- Bodies never exceed ~30; past that the read shifts from "objects" to
  "particles" (a different, cheaper technique).
- One cluster per page, hero only.

## Performance notes

- Fixed-step physics (accumulator), render-interpolated; sleep bodies at
  rest (rapier auto-sleep) so idle cost is the drift noise only.
- Pause the whole world off-screen and on `document.hidden`.
- `prefers-reduced-motion`: bodies freeze at home formation, drag still
  works (response without ambient motion).
- DPR cap 1.5-2; soft shadows from ONE light or baked AO sprite under the
  cluster - live shadow maps for 30 bodies are not worth it.

## When to use

- AI/SaaS heroes that want "approachable, alive, premium" without a literal
  product screenshot.
- Brand-token playgrounds (the primitives wear the logo/material).
- Moments where dwell time is the metric - play measurably holds visitors.

## When NOT to use

- Heroes that must show the actual product UI.
- Mobile-first audiences where the hero is the scroll path (drag vs scroll
  is unresolvable without shrinking the canvas).
- Alongside any other physics surface - two simulations split the toy's
  authority.

## Pairs with (prototype slugs)

- `recipe-restrained-ai-marketing`
- `style-glassmorphism`
- `recipe-bento-marketing`
- `aesthetic-frutiger-aero`
- `recipe-devtools-marketing`
