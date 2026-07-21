# Game/scene seam contract

BINDING for every `game-*` and `s3d-*` drawer. This is the single source for the conventions
and machine contracts at the sim-to-render seam. Never restate these in a playbook, an
envelope, or research prose; reference this file. Never invent a convention this file
already fixes. The daemon enforces the machine contracts with deterministic code
(`editor/tools/qa/visual_qa.py` seam test): a build that violates them FAILS the QA gate
before any lens runs - there is no fallback path.

## Fixed conventions (never negotiable, never restated)

1. **Model forward is -Z.** Every authored/generated character or vehicle mesh faces
   world -Z at rest, so `object3D.getWorldDirection()` IS its forward. A subsystem author
   who receives a +Z-facing mesh wraps it in a group rotated PI once, at build time.
2. **Facing crosses the seam as a VECTOR, never a bare angle.** `setPose(position, forward)`
   takes `{x,z}` / `[x,z]` (sim heading, unnormalized ok). The renderer converts internally
   (`rotation.y = Math.atan2(x, z) + PI` under convention 1). An angle-only pose API is a
   build error: two agents cannot share a zero-direction through a comment.
3. **Units**: 1 unit = 1 m, +Y up. Yaw positive = counterclockwise seen from above
   (three.js). Normalized handles (wind, dayPhase, glint) take 0..1.
4. **Handles are copied, not summarized.** A research handle line is NAME + ARGS + MEANING
   + WHO CALLS IT. Any envelope or plan that mentions a subsystem carries its handle lines
   verbatim. A handle nobody is assigned to call (e.g. a walk-cycle rate) is a research
   bug: every handle line names its caller.
5. **Shared renderer values live in ONE composer.** When a game composes scene3d
   subsystems, it imports/copies the scene3d composer's committed env values (exposure,
   gradientMap bands, fog init, bloom, dome hexes) verbatim with a `// match scene3d
   composer` comment. Any later retune lands in both files in the same commit.

## The `window.__game` harness (composer builds it; daemon preflight hard-fails without it)

**This contract is CODE, not prose to re-implement: `editor/kinds/game-seam.js`.** The composer copies it into the game dir as `seam.js`, loads it first, and calls `window.__seam.makeHarness(cfg)` - the library installs the exact shape below plus the error ring and the qa probes under the fixed conventions above (`applyFacing`/`forwardToYaw` are exported for the render seam too). The QA runner re-syncs the copy verbatim from the canonical library on every run; never hand-edit the copy. Hand-rolling `window.__game` instead of calling `makeHarness` is a build error.

```js
window.__game = {
  state,                       // the loop's live state (read-only use)
  intents: [...],              // every intent kind injectFakeInput accepts
  injectFakeInput(kind, opts), // never throws; returns false when ignored in this phase
  tick(seconds),               // deterministic fast-forward through the fixed-step loop
  snapshot(),                  // { phase, avatar: { pos:[x,y,z], forward:[x,z], speed }, ... }
                               //   + every field the overlay binds, at its documented path
  errors: [],                  // ring of last 10 { message, stack, phase } from global handlers
  qa: {
    modelForward(),            // RENDERED avatar model's world forward [x,y,z] (getWorldDirection)
    animState(),               // { name, clockAdvancing } - clockAdvancing: active clip moved last frame
    debug(on),                 // compass + forward-gizmo + breadcrumb-trail overlay
    spawnTarget(x,y,z,label),  // optional; aim/collision verification
  },
};
```

## Daemon seam test (deterministic, no LLM, runs before lenses)

For any `games/<id>/runtime.html` target the QA gate:

1. **Hard-fails when `test-cases.json` is missing** next to research.md. No generic-battery fallback.
2. **Preflight**: `window.__game` must expose every key above. Missing key = FAIL naming the key.
3. **Facing**: start, `injectFakeInput('move', forward)`, `tick(1)`; assert the avatar moved AND
   `dot(qa.modelForward(), moveDelta) > 0.5` - the model faces where it travels.
4. **Animation alive**: while moving, `qa.animState().clockAdvancing === true`; at rest the
   position holds still.
5. **No errors**: `__game.errors` stays empty through the drive.

These asserts target the failure class state-level QA cannot see: a model rendered 180
degrees from its travel direction while every state number reads correct, a walk state
whose clip clock nobody advances (frozen legs gliding), a clip cut below its own duration.
Only screen-side asserts catch them.
