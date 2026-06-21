# Woven Logic Graph - design contract (Wave 0)

Status: DRAFT for review. This is the shared contract every implementation subagent
codes against. Nothing here is built yet.

Goal: replace the limited "trigger" node (one `sample()` → one layer param via
`impacts`) with a real **atomic node-graph visual programming language**
(Blueprints / TouchDesigner style): typed input nodes → operators → control flow →
outputs wired into position / effect / layer params. v1 covers pointer, camera
detection (face/hand/object), and video OCR.

---

## 0. Bedrock: how the existing value pipeline works (study before extending)

We are EXTENDING the existing per-frame binding pipeline, not inventing a new one.

- **Spec nodes** (`number-generator`, `timeline`, `effect`, `position`, `trigger`,
  `layer`) are authored as a JS module string in `SPEC_SOURCE_TEMPLATES`
  (app.js ~60391). Each module:
  - `export const controls = {...}` - typed control schema. Control types:
    `{type:"number", value, step?, min?, max?}`, `{type:"text", value}`,
    `{type:"boolean", value}`, `{type:"select", value, options:[...]}`.
  - `export function buildSpec(values)` → the canonical persisted spec object.
  - optional runtime fn: number → `value(ctx)`, trigger → `sample(state,values)`.
  - `_compileSpecSource(kind, source)` (app.js ~60828) strips exports, runs the
    module via `Function()`, reads `controls` → default `values`, calls
    `buildSpec(values)`.
- **Numeric controls auto-expose `param:<key>` INPUT ports** for kinds in
  `WORKFLOW_PARAM_PORT_KINDS = {position, effect, trigger, number-generator}`
  (app.js ~60925). Wiring a number/timeline `.out` into `target.param:<key>` writes
  a binding.
- **Binding shape** (app.js `_specParamBindings` ~59496, doc in sources.js header):
  ```
  spec._bindings[param] = { kind:"number-generator"|"timeline", spec:{...} }
  spec._overrides[index] = { x, y, scale, rotation, ... }   // per-cell manual
  ```
- **Runtime evaluation** lives in the composer/layer tool iframe via the shared
  `tools/_shared/sources.js` → `Sources.eval(src, ctx) → number`, with
  `ctx = { index, count, time, u, v, cols, rows }`. Scalar bindings broadcast one
  value; VECTOR bindings (`vector:true`, or sub `algorithmic`/`random`/`pixel-map`)
  evaluate per instance. `Sources.applyScalar/applyVector/applyOverrides` overlay
  values onto resolved transforms.
- **`number-generator` is the canonical value source** and already covers:
  constant, algorithmic expression (`i,t,n,u,v,cols,rows`), seeded random, and
  pixel-map - scalar and vector. The logic graph REUSES it; we do not duplicate it.

Edges are global `data.edges = [{from:"node.port", to:"node.port"}]`
(`workflowParseEdgeRef` ~23572). Source ports: `out`, `layerout:*`, proto/agent
right sides (`workflowIsSourcePort` ~23619).

---

## 1. Typed port system (NEW)

Today ports match by string `tags`. Logic ports need a real data type so we can
validate edges and color them. Add a per-port `dtype`:

| dtype     | meaning                              | literal node     |
|-----------|--------------------------------------|------------------|
| `event`   | discrete pulse this frame (click)    | -                |
| `number`  | scalar float (or per-instance vector)| `number-generator`|
| `vector2` | `{x,y}` (normalized 0..1 by default) | `value-vec2`     |
| `region`  | bbox `{x,y,w,h}` normalized          | -                |
| `boolean` | true/false                           | `value-bool`     |
| `string`  | text                                 | `value-string`   |
| `color`   | `{r,g,b,a}` 0..1                      | -                |

Compatibility rules (validated in the connect path + colored on the wire):
- same dtype always connects.
- `event` → `boolean` allowed (pulse read as true the frame it fires).
- `number` ↔ `boolean` allowed (0=false, !=0=true).
- `vector2`/`region` expose component sub-ports (see `op-vector`) rather than
  auto-coercing.
- everything may connect to a `string` only via explicit `op-tostring` (no silent
  coercion).

Type → CSS color tokens defined once (e.g. number=teal, boolean=amber,
vector2=violet, region=blue, string=grey, event=pink). Reuse existing wire CSS;
add `data-dtype` to ports + edges.

Mechanically `dtype` lives alongside `tags` in `WORKFLOW_CONNECT_DEFS[kind]
.provides/.accepts[port]`. The existing tag check still runs; the dtype check is
additional and only enforced when BOTH endpoints carry a dtype (logic nodes do;
legacy nodes don't, so legacy wiring is unaffected).

---

## 2. Node taxonomy (NEW palette section "Logic")

Every logic node is authored with the SAME `controls`/`buildSpec` convention as
number-generator so it inherits the controls UI, dropdowns, and serialization.
Glyphs are unicode marks (no emoji), consistent with `◇ ⊞ ✲ # ⧖`.

### 2.1 Sources (no inputs; emit typed outputs)
Glyphs below are placeholder unicode marks (consistent with existing `◇ ⊞ ✲ # ⧖`);
final affordances SHOULD use the inline `Icon.*` SVG set (currentColor) per the
no-emoji rule - pick non-emoji-rendering marks in W1A.

- **`input-pointer`** `⊹` - mouse/single-pointer on the render surface.
  out: `x:number`, `y:number` (normalized 0..1), `isDown:boolean`,
  `clicked:event`, `downX:number`, `downY:number`, `upX:number`, `upY:number`,
  `hover:boolean`, `pos:vector2`.
  controls: `{ space:select[normalized,pixels], button:select[any,left,right,middle] }`.
- **`input-touch`** `⊛` - multi-touch on the render surface.
  out: `count:number`, `pos:vector2` (primary touch), `touches:vector2`(per-instance
  vector of all points), `isDown:boolean`, `center:vector2` (centroid),
  `spread:number` (pinch distance), `pinchDelta:number`, `rotation:number` (two-finger
  twist), `tap:event`. controls: `{ maxPoints:number, space:select[normalized,pixels] }`.
- **`input-keyboard`** `⎄` - keyboard on the render surface.
  out: `key:string` (last key), `isDown:boolean`, `pressed:event`,
  `released:event`, `axisX:number` (-1..1 from arrows/AD), `axisY:number` (from
  arrows/WS). controls: `{ key:text (filter to one key; blank=any),
  repeat:boolean }`.
- **`input-scroll`** `⇕` - wheel / scroll on the render surface.
  out: `deltaY:number`, `deltaX:number`, `accumY:number` (running total),
  `accumX:number`, `velocity:number`. controls: `{ space:select[normalized,pixels],
  clampMin:number, clampMax:number }`.
- **`input-gyro`** `◑` - device orientation (mobile-primary).
  out: `alpha:number`, `beta:number`, `gamma:number` (degrees), `tilt:vector2`
  (normalized beta/gamma), `ready:boolean`. controls: `{ smoothing:number }`.
  Permission-gated on iOS 13+ via `DeviceOrientationEvent.requestPermission()` from a
  user gesture (see §6).
- **`input-audio`** `▿` - microphone (or wired audio asset) level/pitch/bands.
  out: `level:number` (loudness 0..1), `pitch:number`, `band:number` (selected
  band energy), `beat:event`. controls: `{ source:select[mic,asset],
  band:select[bass,mid,treble,full], fftSize:number, smoothing:number }`.
  in (optional): `asset` (audio node when source=asset). Permission-gated for mic
  (getUserMedia audio). NOTE: lift the existing `trigger` audio template
  (app.js ~60704) for the loudness/pitch/band extraction math.
- **`input-camera`** `⊙` - live webcam stream handle. out: `stream:string`
  (opaque handle id), `ready:boolean`. controls: `{ facing:select[user,environment],
  resolution:select[low,medium,high] }`. Permission-gated (see §6).
- **`input-video`** `▷` - a video asset/clip as a stream handle. in: `asset` (video
  node). out: `stream:string`, `t:number`, `playing:boolean`. controls:
  `{ loop:boolean, autoplay:boolean }`.

### 2.2 Processors (stream in → structured data out) - either source feeds either
- **`vision-detect`** `◉` - MediaPipe Tasks Vision. in: `stream:string`.
  controls: `{ detector:select[face,hand,object], target:select[present,count,
  location,gesture] }`. out: `present:boolean`, `count:number`, `pos:vector2`
  (primary centroid), `region:region`, `gesture:string`, `confidence:number`.
- **`vision-ocr`** `⊜` - tesseract.js. in: `stream:string`. controls:
  `{ query:text, interval:number(ms, throttle) }`. out: `text:string`,
  `matched:boolean` (query found), `region:region`, `count:number`.

### 2.3 Literals (number is covered by number-generator - NOT re-added here)
- **`value-bool`** `⊤` - out `value:boolean`. controls `{ value:boolean }`.
- **`value-string`** `⊏` - out `value:string`. controls `{ value:text }`.
- **`value-vec2`** `⊕` - out `value:vector2`. controls `{ x:number, y:number }`.

### 2.4 Operators (pure, stateless)
- **`op-math`** `∑` - in `a:number`, `b:number`; out `r:number`.
  controls `{ op:select[add,sub,mul,div,mod,min,max,pow,atan2] }`.
- **`op-unary`** `ƒ` - in `a:number`; out `r:number`.
  controls `{ op:select[abs,neg,floor,round,sin,cos,sqrt,sign] }`.
- **`op-compare`** `≷` - in `a:number`, `b:number`; out `r:boolean`.
  controls `{ op:select[eq,ne,lt,gt,le,ge], epsilon:number }`.
- **`op-logic`** `&` - in `a:boolean`, `b:boolean`; out `r:boolean`.
  controls `{ op:select[and,or,xor,nand,nor] }`. (NOT = `op-unary`-style single in.)
- **`op-map`** `↦` - in `x:number`; out `r:number`. remap + clamp + ease.
  controls `{ inMin,inMax,outMin,outMax:number, clamp:boolean, ease:select[linear,
  in,out,inout] }`. (Mirrors `Sources._interp` easing names.)
- **`op-vector`** `⊿` - make/break/measure vec2. controls `{ mode:select[make,
  break,distance,add,scale,lerp] }`; ports vary by mode (make: `x,y`→`v:vector2`;
  break: `v`→`x,y`; distance: `a,b`→`d:number`; etc.).
- **`op-tostring`** `“”` - in `a:number|boolean|vector2`; out `s:string`.
  controls `{ template:text(e.g. "x={x}") }`.

### 2.5 Control flow
- **`flow-if`** `⋔` - in `cond:boolean`, `then:any`, `else:any`; out `r:any`.
  Select/branch: passes `then` when cond else `else`. (dtype of `r` follows the
  connected branches; validated to match.)
- **`flow-gate`** `⊳` - in `value:any`, `open:boolean`; out `r:any`. Passes
  `value` only while `open`; otherwise holds last (controls `{ holdLast:boolean }`).
- **`flow-while`** `↻` - bounded per-frame loop. in `cond:boolean`, `body:number`;
  out `count:number`, `last:number`. controls `{ maxIterations:number }`. Evaluates
  the `body` subexpression repeatedly within one frame while `cond` holds, capped
  by maxIterations (no infinite loops - strictly bounded). Primarily for
  accumulation; most "loop" needs are better served by `flow-repeat` + state.
- **`flow-repeat`** `⟳` - in `n:number`, `body:number`; out `sum:number`,
  `values:number`(vector). Runs `body` n times with `i=0..n-1` available in ctx;
  emits per-iteration vector (drives per-instance layers).

### 2.6 State (reactive memory - the practical "while/loop")
All carry internal state in the engine, keyed by node id; they are the legal cycle
breakers (a graph cycle must pass through a state node).
- **`state-counter`** `№` - in `inc:event`, `reset:event`; out `count:number`.
  controls `{ step:number, wrap:number(0=off) }`.
- **`state-toggle`** `⇄` - in `flip:event`; out `on:boolean`. controls `{ initial:boolean }`.
- **`state-latch`** `⎍` - in `set:boolean`, `hold:any`; out `value:any`. samples
  `hold` when `set` rises, keeps it.
- **`state-timer`** `⧗` - in `start:event`, `stop:event`; out `elapsed:number`,
  `running:boolean`. controls `{ autostart:boolean }`.
- **`state-smooth`** `∿` - in `target:number`; out `value:number`. critically-damped
  pursuit. controls `{ stiffness:number, damping:number }`. (the smoothing every
  pointer-driven value should pass through.)

### 2.7 Output sink (writing back)
Logic outputs reach targets by an edge into an existing `param:<key>` port. To also
let logic READ a target's current value and to write structured transforms:
- **position / effect / layer gain `param:<key>` OUTPUT ports** (read-back) in
  addition to their existing input ports (§5).
- **`output-binding`** `⊨` (optional convenience) - in `value:number`; controls
  `{ target:select[wired layers], param:select[x,y,scale,rotation,opacity,...] }`.
  Emits the same `_bindings` entry an edge-into-`param:` would; useful when the
  target param isn't a numeric control port. MVP can skip this and rely on edges.

---

## 3. Serialized subgraph schema

The logic graph is NOT a separate document - its nodes live in `data.nodes` and its
wires in `data.edges` like every other node. What the runtime needs is a PROJECTION
of just the logic-relevant slice, assembled by the editor and passed to the tool
iframe alongside `effects/positions/triggers/layers`:

```js
logic = {
  nodes: [
    { id, kind, params },          // params = compiled `values` from controls
    ...
  ],
  edges: [
    { from:{node,port,dtype}, to:{node,port,dtype} },
    ...
  ],
  outputs: [                        // logic.out → target.param: edges, pre-resolved
    { sourceNode, sourcePort, targetNode, targetParam },
    ...
  ],
}
```

Each `data.nodes` logic entry persists as `{ id, kind, spec }` where
`spec = { v:1, kind, params:{...} }` (built by its `buildSpec`). The projection is
derived; the canvas remains the single source of truth.

---

## 4. Engine API - `tools/_shared/logicgraph.js` (sibling of sources.js)

Pure module, no DOM/IO. Mirrors the `Sources` shape so tools import it the same way.

```js
export const LogicGraph = {
  // Build an executable plan from the serialized subgraph (topo sort, cycle
  // detection through state nodes, per-node eval closures). Call once when the
  // graph changes.
  compile(logic) -> plan,

  // Advance state nodes + recompute. `inputs` is the global frame state:
  //   { pointer:{x,y,isDown,clicked,downX,...}, streams:{<id>:{detections,ocr}},
  //     dt, time }
  // `ctx` mirrors Sources ctx for per-instance eval: {index,count,time,u,v,cols,rows}
  // Returns an output map: { "<targetNode>.<param>": value, ... }
  tick(plan, inputs, ctx) -> outputs,

  // Single output read (used by the binding resolver, see §5).
  read(plan, outputs, targetNode, param) -> value,

  // Per-node pure evaluators, keyed by kind (the bulk of the work). Each is
  // (node, inPorts, frame, ctx) -> outPorts. State kinds also receive/mutate
  // plan.state[node.id].
  evaluators: { "op-math": ..., "op-compare": ..., "flow-if": ..., ... },
};
```

Evaluation model: one `tick` per animation frame. Topo order; each node's outputs
memoized for the frame; `event` outputs are true only on the frame they fire;
`state-*` nodes read previous-frame state and write next. Cycles not passing through
a state node are a compile error (surfaced on the node).

Reuse `Sources` primitives where possible (`_interp` easing in `op-map`, hash/random
in any future noise op). Numbers coming from a wired `number-generator` are fetched
via `Sources.eval` and entered into the frame as that port's value.

---

## 5. Runtime integration

1. **Editor projection:** extend the payload `WorkflowDrivenToolNode` sends to the
   composer/layer tool to include `logic` (§3). Build it next to where
   `effects/positions/triggers/layers` are gathered (app.js ~59585).
2. **Binding kind `logic`:** extend `_specParamBindings` (app.js ~59496) so an edge
   `logicNode.<port>` → `target.param:<key>` writes
   `spec._bindings[key] = { kind:"logic", ref:{ node:logicNodeId, port } }`.
3. **Evaluator consult:** in the tool's per-frame resolve, when a binding has
   `kind:"logic"`, read its value from `LogicGraph.tick(...)` output map instead of
   `Sources.eval`. `Sources.applyScalar/applyVector` get a small branch (or the tool
   pre-merges logic outputs into the params object before calling them).
4. **Read-back ports:** add `param:<key>` to `provides` (outputs) for `position`,
   `effect`, `layer` in `WORKFLOW_CONNECT_DEFS` + `workflowPortPosition`. Value =
   the target's current resolved param this frame, exposed back into the engine via
   `inputs.readback[targetNode][param]`.
5. **Live/share parity:** load `logicgraph.js` + the input capture in the
   live/share runtime so a published piece reacts to real input, not just the editor.

---

## 6. Input / CV plumbing (v1 = all three)

- **Pointer / touch / keyboard / scroll:** capture the relevant DOM events on the
  render surface; normalize positions to 0..1 over the stage. Touch uses
  `PointerEvent`/`TouchEvent` with per-touch tracking + pinch/twist math; keyboard
  listens at the surface (focusable) and derives `axisX/axisY` from arrows/WASD;
  scroll uses a passive `wheel` listener and accumulates. No per-frame
  `getBoundingClientRect` (cache rect, update on resize) - per the canvas-rect memory.
- **Gyro:** `DeviceOrientationEvent`; on iOS 13+ call
  `DeviceOrientationEvent.requestPermission()` from a user gesture (same gesture-gated
  overlay as camera/mic). Smooth via the node's `smoothing` control.
- **Audio (mic):** `getUserMedia({audio})` + `AudioContext` + `AnalyserNode`
  (gesture-gated). Reuse the existing `trigger` audio extraction math
  (app.js ~60704). `source:asset` path taps a wired audio node instead of the mic.
- **Camera:** `getUserMedia({video})` behind a user-gesture permission overlay
  (custom UI - NO native dialogs; use the editor's uiAlert/uiConfirm pattern in
  chrome, a custom in-iframe overlay in the runtime, per the two-gate pattern).
  One shared stream per `input-camera` node id; processors subscribe by handle.
- **Detection:** MediaPipe Tasks Vision via CDN (FaceLandmarker / HandLandmarker /
  ObjectDetector), lazy-loaded per detector. Runs in the render rAF, frame-rate
  limited. Emits `{detections:[{x,y,w,h,confidence,gesture?}]}` into `inputs.streams`.
- **OCR:** tesseract.js via CDN, throttled to the node's `interval` (OCR is slow);
  emits `{text, words:[{text,bbox}]}`. Either a camera or video stream may feed
  `vision-detect` OR `vision-ocr` (and vice versa).
- Everything via CDN script/ESM - no build step. Backend stays Python 3.9-safe.

### 6.1 W2C <-> W2D module interface (so the two waves own disjoint files)

W2D writes NEW shared modules only (no app.js / tool-file edits). W2C imports them
and does all wiring. Both code against this interface:

- `editor/tools/_shared/logicinputs.js` (W2D):
  ```js
  export const LogicInputs = {
    // Attach DOM listeners to the render surface. Returns a handle.
    // No getUserMedia/gyro permission here - those are camera/audio/gyro nodes,
    // requested lazily on a user gesture via requestStream/requestSensor below.
    attach(surfaceEl, opts) -> {
      sample() -> { pointer, touch, keyboard, scroll, gyro, audio, dt, time },
      requestSensor(kind) -> Promise<bool>,   // 'gyro' | 'audio' (mic), gesture-gated
      dispose(),
    },
  }
  ```
- `editor/tools/_shared/logicvision.js` (W2D):
  ```js
  export const LogicVision = {
    requestCamera(opts) -> Promise<streamHandle>,   // getUserMedia, gesture-gated
    attachVideo(videoEl) -> streamHandle,
    // Lazy-load MediaPipe / tesseract per processor; run frame-limited.
    detect(streamHandle, { detector, target }) -> { present,count,pos,region,gesture,confidence },
    ocr(streamHandle, { query, interval }) -> { text, matched, region, count },
    frame(streamHandles) -> { '<handle>': { detections, ocr } },  // call once per rAF
    dispose(),
  }
  ```
- Permission overlay (W2D): `editor/tools/_shared/logicpermission.js` exporting a
  custom in-iframe overlay (NO native dialog) that resolves on the user gesture, used
  by `requestSensor`/`requestCamera`.

W2C builds the per-frame `inputs` object for `LogicGraph.tick` by merging
`LogicInputs.sample()` with `{ streams: LogicVision.frame(handles) }`, then writes
the resolved outputs into the layer/effect/position params (see §5).

---

## 7. Authoring UX

- New palette section "Logic" listing §2 kinds with glyphs + one-line descriptions
  (next to the existing Building blocks section, app.js ~42074).
- Compact node body: dropdowns for `select` controls, inline fields for
  number/text/boolean, typed colored ports per §1.
- Edge type-coloring + compatibility highlight while dragging (extend the existing
  pending-edge snap logic).
- Live value preview on ports (mirror the existing binding-tick preview ~59555):
  when in Run/Live mode, each output port shows its current value.
- **Run/Live toggle:** a mode where the graph executes and captures real input vs.
  edit mode where it's inert. Reuse/extend any existing preview-play state.

---

## 8. Constraints (non-negotiable)

- No build step (UMD/ESM via CDN). Python 3.9-safe backend (future-annotations;
  run `editor/check-compat.sh` before sync).
- No native dialogs (uiAlert/uiConfirm/uiPrompt; custom overlay in iframe).
- No emoji as UI icons - unicode marks / inline SVG (currentColor).
- No em/en dashes anywhere.
- No per-frame `getBoundingClientRect` in the eval/render loop.
- Mirror to the IN-USE copy wholesale (rsync editor/), never per-edit.

---

## 9. Build waves (subagent decomposition)

- **W0 (this doc)** - contract. ← review gate.
- **W1A Skeleton+ports:** typed-port system; register all §2 kinds in
  `WORKFLOW_NODE_FACTORY` / `WORKFLOW_CONNECT_DEFS` / `SPEC_SOURCE_TEMPLATES` /
  palette / glyphs. Nodes place + wire with type validation; no behavior.
- **W1B Engine:** `logicgraph.js` (§4) + a standalone test harness; reuses Sources.
- **W2C Runtime integration:** §5 (projection, `kind:"logic"` binding, evaluator
  consult, read-back ports, live/share parity).
- **W2D Inputs/CV:** §6 (pointer node, camera/video sources, vision-detect,
  vision-ocr, permission UX).
- **W3E Authoring UX:** §7.
- **W3F Demo + verify + memory:** end-to-end graph (e.g. hover → smooth →
  layer.opacity; face.x → layer.position.x), verify in editor + live, update memory.

Dependencies: W1A+W1B parallel after W0; W2C needs W1A+W1B; W2D needs W1A (+W1B for
wiring); W3E needs W1A; W3F last.
```
