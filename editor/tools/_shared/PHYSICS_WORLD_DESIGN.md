# Unified Physics World (mm-composer)

One shared matter.js `Engine`/`World` per composer instance. Every physics object
lives in that ONE world, so objects (1) COLLIDE / interact with each other and
(2) respond to GENERIC FORCES that are wired from ANY input. The mouse is just one
possible force source: nothing in the world is hardcoded to it.

This design is implemented twice, in parity:
- editor runtime: the `PW` object + the rewritten Positioning physics modes in
  `editor/tools/mmcomposer/index.html`.
- baked standalone player: the `PW` twin + the rewritten `positions()` branches
  inside `slimPlayer(...)` in the same file (serialized via `.toString()`).

## The world

- ONE `Matter.Engine` (`PW.engine`) + `World` (`PW.world`), lazy-created the first
  frame any physics object exists (`PW.ensure(W,H)`), via the same `loadMod('matter')`
  / `loadMatter()` CDN import the old per-mode sims used. No new bundler.
- World gravity defaults to downward `(0, 1)`. The `gravity`/physics and `shatter`
  modes push their authored gravity onto the shared world each frame
  (`PW.setGravity`); a single shared world has ONE gravity vector (last writer wins).
  `rope-ink` uses its `gravity` control as the downward pull. Boids cancel gravity
  (they fly): their per-frame `Body.setVelocity` overwrites any accumulated fall.
- Stepping is a FIXED-TIMESTEP ACCUMULATOR (`PW.beginFrame(dt, forceList, slow)`),
  called ONCE per render frame from `Engine.render` (editor) / `frame` (slim),
  BEFORE pass A reads body transforms. It (a) applies all wired forces, then (b)
  consumes the accumulator in `1/60 s` steps (capped at 5 substeps so a backgrounded
  tab resuming cannot explode the solver). `slow` is the shatter time-scale (the
  smallest slowmo across shatter layers; 1 = realtime).
- Bodies are REUSED across frames. A layer rebuilds its bodies only when its sim
  SIGNATURE changes (count / WxH / segments / text / anchors / stiffness). Each
  physics mode just READS `body.position` / `body.angle` each frame and emits the
  normalized `[{x,y,scale,rot}]` instance contract unchanged.
- Body cap: `PW._bodyCap = 3000` total. `PW.register` clamps a layer's bodies to
  the remaining budget and logs once (`[PhysicsWorld] body cap ... reached`).
- Determinism: all spawn jitter is `mulberry(hash(...))`. No `Math.random`. No
  per-frame `getBoundingClientRect`.
- Lifecycle: `PW.prune(liveSet)` removes records for layers that are gone OR no
  longer a physics mode this frame; `PW.reset()` drops the whole world on project
  reload / resize (bodies rebuild lazily). `PW.remove(id)` tears one layer's bodies
  + constraints out of the world.

## Mode -> bodies mapping

| Mode        | Bodies                                                                 | Collision category | Self-collision |
|-------------|-----------------------------------------------------------------------|--------------------|----------------|
| `physics`/gravity | N circles (radius from `size`), `restitution=bounce` + 3 static walls | `DEFAULT` (walls `WALL`) | n/a (all collide) |
| `shatter`   | voronoi-cell `fromVertices` shard bodies + 4 static walls             | `DEFAULT` (walls `WALL`) | n/a (all collide) |
| `rope`      | chain of `segments+1` circles, node 0 static (pinned), stiff distance constraints | `ROPE` | per-rope negative GROUP |
| `rope-ink`  | one such chain per glyph-ink anchor (node 0 pinned to the ink point)  | `ROPE` | per-rope negative GROUP |
| `boids`     | N circles, gravity-cancelled, flocking velocity set per frame         | `BOIDS` | n/a (all collide) |
| `instances` | NOT in the world (pure formula layout, unchanged)                     | -                  | - |

Collision categories (bit flags): `DEFAULT=1`, `ROPE=2`, `BOIDS=4`, `WALL=8`. Every
body uses `mask:0xFFFF`, so by default EVERYTHING collides with everything. The only
suppression is intra-rope: each rope chain gets a unique NEGATIVE `collisionFilter.group`
(`PW.nextRopeGroup()`); matter.js never collides two bodies that share the same
negative group, so a rope's own segments pass through each other while still colliding
with every other object (different/zero groups fall back to category+mask).

Rope/rope-ink keep the hanging-under-gravity look as the DEFAULT (node 0 pinned,
the rest hang + swing). The OLD hardcoded "last node follows the mouse" pin is GONE -
that interaction is now expressed generically with a wired `force` (see below).

## The generic `force` node + force model

`force` is a logic kind (`LOGIC_NODE_DEFS` in `app.js`, section "Physics", glyph `⌖`).
It is a SINK with one accept `pos` (vector2) and controls `type`, `radius`, `strength`,
`falloff`; it has no output port. `app.js`'s `_logicProjection` collects every force
node into `projection.forces = [{ id, params, pos:{kind:"logic",ref:{node,port}}|null }]`,
always projecting it (and its upstream `pos` chain) so the source ticks.

Each frame the composer resolves the list: `LogicBridge.forces()` (editor) /
`LB.forces()` (slim) reads each force's `pos` via `vec(ref)` from THIS frame's ticked
ports - so `pos` can be `input-pointer.pos`, `input-touch.pos`, `vision-detect.indexTip`,
an `op-vector` output, ANYTHING. `PW.applyForces` then applies the field to all world
bodies within `radius` (normalized, scaled by `max(W,H)`):

- `attract` / `repel`: force along `(pos - body)`, magnitude `strength * fall`, sign
  per type. `fall = pow(1 - dist/radius, falloff)` (1 at center, 0 at the edge).
- `vortex`: tangential (perpendicular) force + a slight inward pull = a swirl.
- `drag`: scales body velocity down near `pos` (thickens the medium there).
- `wind`: no center; `pos` is read as a DIRECTION (heading from center 0.5,0.5) and
  applied as a constant push to every dynamic body.

`strength` can be negative to invert. With NO force wired the world just runs its
defaults (gravity hang/swing, flock, shatter) - now collidable and force-ready.

This is the generalization the mandate asks for:
- mouse-drag curtain = `input-pointer.pos -> force(attract) -> composer`
- hand pushing particles = `vision-detect.indexTip -> force(repel) -> composer`

## Baked parity

The slimPlayer carries a faithful `PW` twin (same categories, accumulator, body cap,
force model, per-rope group) and the same per-mode body mapping inside `positions()`,
fed by the same `projection.forces` baked into the published config's `logic`. Editor
preview and exported player behave identically. The lazy matter.js import already
existed in the baked player (`loadMatter`).

## What may visually shift vs the old per-mode sims

- Objects of DIFFERENT physics layers now COLLIDE (e.g. shatter shards pile on gravity
  balls; boids bump ropes). Previously each mode had its own isolated engine.
- Rope's free end NO LONGER follows the mouse automatically. Wire a `force` for that.
- Rope/rope-ink nodes are real rigid circles joined by stiff constraints (was verlet);
  motion reads slightly springier and they now bump other objects.
- Boids are circles that resolve overlaps on contact (slight separation jitter at high
  density) and can be nudged by forces.
- A single shared gravity vector: if two gravity/shatter layers set different gravity,
  the last-resolved one wins for the whole world that frame.
