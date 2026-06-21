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
  PLUS per-landmark `vector2` ports reading the PRIMARY detection's named points
  (normalized 0..1; missing point degrades to `{x:0,y:0}`):
  - detector=hand: `wrist`(0), `thumbTip`(4), `indexTip`(8), `middleTip`(12),
    `ringTip`(16), `pinkyTip`(20) - the 21-point MediaPipe HandLandmarker indices.
  - detector=face: `nose`(1), `leftEye`(33), `rightEye`(263) - FaceLandmarker
    canonical mesh indices.
  These let apps draw between individual fingertips (e.g. a polygon via the
  `shape` node, §10). The full per-point list is also carried on each detection
  as `detection.landmarks = [{x,y}]` for any consumer that needs all points.
- **`vision-ocr`** `⊜` - tesseract.js. in: `stream:string`. controls:
  `{ query:text, interval:number(ms, throttle) }`. out: `text:string`,
  `matched:boolean` (query found), `region:region`, `count:number`.
- **`palette`** `◧` - image dominant-color extraction (DONE; see §13). in:
  `image:string` (an asset/image node). controls: `{ count:number(2-8),
  quality:number(sample-stride) }`. out: `color0`..`color7` (dtype `color`),
  `dominant` (color), `domR`/`domG`/`domB` (number 0..1, the dominant color's
  channels so it can ALSO drive numeric params), `ready:boolean`, `count:number`.
  Extraction (downsample + median-cut) runs in the RUNTIME (canvas decode, like
  number-generator pixel-map), cached by image-url + count; the colors reach the
  engine via `frame.palettes[nodeId]` exactly how vision-detect reaches it via
  `frame.streams`. The "image palette extraction" gap is DONE.

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

### 2.8 Render (renderable composition primitive, NOT a pure logic node)
- **`shape`** `⬡` - draws a polygon / polyline from wired logic vector2 points.
  in: `p0:vector2` .. `p7:vector2` (eight point inputs; wire as many as needed,
  unused are skipped). out: `out:layer` (wire into a composer / mm-composer `in`
  port, where it joins the z-stack + effect + blend pipeline exactly like a
  layer). controls: `{ closed:boolean, fill:text(css color, blank=none),
  stroke:text(css color), strokeWidth:number, opacity:number,
  blend:select[normal,multiply,screen,overlay], z:number, smoothing:number }`.
  See §10 for the full contract.
- **`type-motion`** `⒜` (label "Kinetic Type") - draws PER-GLYPH animated text
  (kinetic typography) into a layer buffer. No inputs (v1). out: `out:layer`
  (wire into a composer / mm-composer `in` port, where it joins the z-stack +
  effect + feedback + blend pipeline exactly like a layer). controls:
  `{ text, font(css family), weight:number(100-900), size:number, color:text,
  tracking:number(letter-spacing em), align:select[center,left,right],
  behavior:select[...16], speed:number, amplitude:number, stagger:number(per-glyph
  delay), path:select[straight,arc,circle,wave,ring], pathRadius:number,
  pathAmplitude:number, pathRotate:boolean, loop:boolean, opacity:number,
  blend:select[...], z:number, feedback:number }`. See §12 for the full contract +
  behavior list (12.3) and the text-on-path placement (12.6).

### 2.7 Output sink (writing back)
Logic outputs reach targets by an edge into an existing `param:<key>` port. To also
let logic READ a target's current value and to write structured transforms:
- **position / effect / layer gain `param:<key>` OUTPUT ports** (read-back) in
  addition to their existing input ports (§5).
- **`output-binding`** `⊨` (optional convenience) - in `value:number`; controls
  `{ target:select[wired layers], param:select[x,y,scale,rotation,opacity,...] }`.
  Emits the same `_bindings` entry an edge-into-`param:` would; useful when the
  target param isn't a numeric control port. MVP can skip this and rely on edges.

### 2.9 Output (audio synth SINK) - DONE (see §14)
- **`audio-out`** `◢` - the missing "audio output / image->sound" category. A
  WebAudio synth voice driven by the logic graph. accepts: `frequency:number`,
  `gain:number(0..1)`, `cutoff:number`, `trigger:event` (note-on). controls:
  `{ waveform:select[sine,square,saw,triangle], frequency, gain, cutoff }` (the
  numeric inputs fall back to these when unwired). It is a true logic SINK: the
  engine evaluates it (republishing the resolved params + an edge-detected
  trigger), and the mmcomposer LogicBridge feeds those values into
  `LogicAudio.set()` each frame while Live. WebAudio graph: oscillator (waveform)
  -> gain -> lowpass filter -> destination; the AudioContext is created behind a
  user gesture via the logicpermission overlay (NO native dialog, NO autostart at
  load). Baked slimPlayer parity: a published piece can also produce audio
  (gesture-gated). Wire number-generator / timeline / vision / palette ->
  `audio-out.frequency` to make sound react to visuals. The "audio-output node"
  gap is DONE.

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

---

## 10. The `shape` render node (polygon / polyline primitive)

`shape` `⬡` is a RENDERABLE composition primitive that draws a polygon or
polyline from up to eight wired logic vector2 points. It is the counterpart to a
layer: it lives in the "Logic / Render" palette section and is registered
client-side like the other logic kinds (LOGIC_NODE_DEFS in app.js), but unlike a
pure logic node it is NEVER evaluated by the engine - it is a SINK that emits a
layer. `_isLogicKind("shape")` returns false for exactly this reason, so the
projection (§3) does not try to tick it.

### 10.1 Ports + controls
- INPUTS (accepts, dtype `vector2`): `p0` .. `p7`. Wire any subset; unwired or
  unresolved points are skipped (a partially-wired shape still draws). Points are
  the polygon vertices IN ORDER (p0 -> p1 -> ... -> highest wired index).
- OUTPUT (provides): `out` (dtype `layer`, tags `["layer"]`). Wire into a
  composer / mm-composer `in` port - the same accept a `layer` node uses.
- CONTROLS (authored with the shared controls/buildSpec convention):
  `closed:boolean` (polygon vs polyline), `fill:text` (css color, blank = no
  fill), `stroke:text` (css color), `strokeWidth:number`, `opacity:number`,
  `blend:select[normal,multiply,screen,overlay]`, `z:number`,
  `smoothing:number` (0 = straight segments; >0 blends a Catmull-Rom curve).

### 10.2 How points resolve from the LogicBridge (no parallel eval loop)
At projection time the editor (app.js `_shapePointBindings`) collects every edge
`<logicNode>.<port> -> shape.pK` into `spec._points[pK] = { kind:"logic",
ref:{ node, port } }` - the SAME binding shape used for `kind:"logic"` param
bindings, except the point ports are not `param:` ports so they need this
dedicated extractor. The shape spec also carries `_shape:true` so the runtime
recognizes it. The source logic node (e.g. `vision-detect`) is force-included in
the projection so its ports compute each frame even when it ONLY feeds a shape.

At runtime the composer's per-frame render reads each point via
`LogicBridge.vec(ref)` -> the engine's per-frame `_ports[node][port]` (the exact
path `LogicBridge.value` uses for scalars, returning the full `{x,y}` instead of
just `x`). Normalized 0..1 points are mapped to the cached W x H stage rect
(`x*W, y*H`); there is no per-frame `getBoundingClientRect` (W/H are the cached
composition dims passed down from `render()`).

### 10.3 Z-order + effect compatibility
The shape becomes a wired LAYER (`buildWiredRuntimeLayers` emits a layer whose
`content.kind === "polyshape"`), so it participates in the existing layer stack:
- z-order: the layer's `z` (from the shape's `z` control) places it in the
  ascending z sort; PASS B composites it among the other layers.
- opacity + blend: the shape's `opacity` / `blend` controls drive the layer's
  `_opacity` / `_blend`, applied at composite exactly like every wired layer.
- effects: to get "a glitchy image behind the polygon", put an image layer at a
  LOWER `z` with a glitch/crt/pixelate effect, and the shape at a HIGHER `z`
  (or vice-versa). The shape's own layer is also effect-capable through the same
  per-layer effect path - z-order + effects work because the shape IS a layer.

## 11. Composer capability extensions (camera/video layers, boids, feedback)
Three additive extensions to the mmcomposer runtime + the baked slimPlayer. All
default to current behavior (no regression to layers / effects / triggers /
positions / the number-timeline-logic binding pipeline).

### 11.1 Live camera / video as a renderable, effect-able LAYER
`input-camera` and `input-video` gained a `layer` output port (dtype `layer`,
tags `["layer"]`) ALONGSIDE their existing detection / stream ports. Wiring
`input-camera.layer` (or `input-video.layer`) into a composer `in` makes the live
feed a renderable layer that runs the full per-layer effect stack (pixelate,
ascii, edge-detect, crt, slice, dither, chromatic-aberration, ...).

Client side (app.js), this mirrors the `shape` node exactly:
- `workflowKindIo` special-cases `input-camera` / `input-video` to return
  `_CAMERA_KIND_IO` (the `layer` port resolves `typed`, flavor `layer`) since
  logic kinds are not in the backend KIND_IO registry.
- `_wiredLayerSpec` tags the spec: `input-camera` -> `_camera:true,
  _cameraKind:"camera"`; `input-video` -> `_camera:true,
  _cameraKind:"videostream"`. The node id flows through as `i.layerId`.
- The detection ports stay intact (camera-feed / vision-detect still work via the
  logic projection; the `layer` port is the only one resolved as an upstream
  input).

Runtime side (mmcomposer/index.html), `buildWiredRuntimeLayers` has a `_camera`
branch BEFORE the `_shape` branch:
- `_cameraKind === "camera"` -> `content = { kind:"camera" }` and forces
  `STATE.inputs.camera = true`. `Engine.ensureCameraContent()` (called each frame)
  requests the webcam once via `enableCamera()` when a camera-content layer
  exists (the permCam chip stays the manual fallback; getUserMedia may need a
  gesture).
- `_cameraKind === "videostream"` -> if a wired child carries a clip url, reuse
  the existing video-asset path (push to CONTENT, `content.kind:"asset"`);
  otherwise `content = { kind:"videostream", nodeId }`, keyed to a per-node
  `<video>` (logicinputs stream capture may set its srcObject).

`drawContent` (editor) + `drawC` (slimPlayer): `kind:"camera"` draws
`Input.cam.video` cover-fit + horizontally mirrored (selfie-cam); `kind:
"videostream"` draws the node's `<video>`. Both draw NOTHING until the element is
ready (`readyState >= 2`, no throw). Effects apply on top via the existing stack,
exactly like an `asset` video.

User wiring: drop an `input-camera` (or `input-video`) Source node, wire its
`Layer` output into the composer's `in` port. Add effect nodes / a layer effect
stack as usual; they run on the live feed.

### 11.2 Boids flocking position mode
`boids` is a new position mode beside `physics` / `rope`. `Positioning.boids(L,p)`
keeps per-layer agent state `{x,y,vx,vy}` on `L._boids` across frames (like rope's
`s.pts`). Each frame it applies Reynolds separation + alignment + cohesion within
the `perception` radius, clamps to `maxSpeed`, bounces at the 0..1 bounds, and
returns instances with `rot` from heading. dt comes from `Input.clock` (the frame
dt), normalized to a ~60fps cadence. Params: `count`, `separation`, `alignment`,
`cohesion`, `perception`, `maxSpeed`, `size`. The position-node template
`boids` ("Boids flock") exposes those numeric controls; the editor inspector adds
the matching sliders; slimPlayer keeps parity (state on `SIM[L.id].a` flagged
`boids:true`). `L._boids` is runtime-only and stripped at bake.

### 11.3 Per-layer feedback / trail buffer
Every layer gained a numeric `feedback` field (0..1, default 0), editable in the
composer inspector (a new "Layer" accordion for inline layers; a read-only field
+ a Layer-node control + `_specDefault` default for wired layers). In PASS A,
when `feedback > 0` the per-layer buffer is NOT cleared: instead a
`destination-out` fade with alpha `(1 - feedback)` is drawn over the prior buffer
so previous frames decay into a trail, then this frame's content is drawn on top.
The buffer persists across frames because it lives in the existing per-layer
buffer pool keyed by id (no reallocation when feedback > 0). `feedback === 0`
keeps the full `clearRect` = current behavior. slimPlayer mirrors this on its
persistent per-layer buffer.

### 11.4 Text-ink position mode (glyph-ink -> point cloud)
`text-ink` ("Text ink") is a position mode beside `drawn` / `boids` / `rope` that
turns a CSS-font text string into a NORMALIZED point cloud, then renders the
layer content (a small shape/asset) at each point - "text made of particles".

Ink-sampling approach (font-agnostic, NO opentype in the runtime): draw the text
large + centered on an OFFSCREEN 2D canvas sized to the layer bounds (W x H),
`getImageData`, collect the pixels whose alpha clears a threshold (>40),
deterministically Fisher-Yates shuffle them with a `mulberry` RNG seeded by
`hash(L.id + ':text-ink')` (NO `Math.random`), and take `density` of them
normalized to 0..1. A small raster stride keeps very large canvases cheap. Works
with ANY `font-family` because we sample drawn INK, not glyph outlines. The helper
is `sampleTextInk(text,font,weight,density,W,H,seed)` (editor, module top-level)
with a parity copy `sampleInk(...)` inside the baked slimPlayer.

Caching (do NOT re-sample every frame, mirrors `drawn`/`rope`): the sampled cloud
+ its signature live on `L._textInk = { sig, base }` (editor) / `SIM[L.id] =
{ tiSig, base, parts }` (slimPlayer). The signature is
`text|font|weight|density|WxH`; the offscreen canvas is re-sampled ONLY when the
signature changes (or, in the editor, when a sampling-affecting inspector control
nulls `L._textInk`). The mode switch + control edits clear the cache so the cloud
refreshes immediately.

Params: `text`, `font` (css family), `weight` (100-900), `density` (target point
count, 1-800), `jitter` (per-point spread), `drift` (0 = static cloud; >0 =
disintegration), `size` (per-instance scale). The position-node template
`text-ink` exposes these; the editor inspector adds the matching fields; slimPlayer
keeps parity. `L._textInk` is runtime-only and stripped at bake.

Particle / dust + disintegration recipe (text-ink + drift + feedback): with
`drift = 0` the cloud is static (a per-point deterministic `jitter` is the only
spread). With `drift > 0` the cloud SEEDS a verlet particle per ink point
(`parts`, integrated each frame under gravity `0.0006 * drift` + an optional
time-varying jitter), so the letters fall apart into drifting dust. Pair drift
with a non-zero layer `feedback` (11.3) and the disintegrating particles leave
decaying trails - "letters disintegrate into particles". Because text-ink returns
a normal instance array `[{x,y,scale,rot}]`, it flows through PASS A exactly like
any mode: each instance is drawn via `drawContent`, so the per-layer EFFECT stack
+ feedback + blend compose on top for free. The drift is SELF-CONTAINED in the
mode (no change to the Matter.js `physics` mode, which spawns random bodies and
does not consume a base instance set - seeding it would have been invasive, so the
disintegration drift was kept inside `textInk` instead, additive and non-
regressing).

Rope-anchored-to-ink: SHIPPED as its own `rope-ink` position mode (see 11.5). The
earlier worry about re-architecting the 2-anchor `rope` was sidestepped: rather
than overload `rope`, `rope-ink` is a separate, additive mode that samples the ink
into an N-point ANCHOR cloud and grows ONE short verlet rope per anchor. The
shipped `rope` (exactly two anchors, pointer-draggable free end) is untouched.

Finer follow-ups (DONE): ORDERED-OUTLINE-for-shape - this `text-ink` sampler
returns an unordered shuffled cloud (ideal for particles/dust + ink anchors); the
contour-ordered variant now SHIPS as the `text-outline` position mode (see 11.6),
whose ordered boundary points can feed a closed `shape`/polyline that strokes the
glyph outline.

### 11.5 Rope-ink position mode (physics ropes anchored to glyph ink)
`rope-ink` ("Rope ink") is a position mode beside `text-ink` / `rope` that
delivers the "Elastic Type" look: physics ropes hanging + swinging from the glyph
ink. It REUSES the 11.4 ink sampler to get a LOW-density ANCHOR cloud, then grows
a short verlet rope (a chain of `segments` nodes) from each anchor and relaxes it
each frame under gravity - identical verlet + constraint math to the shipped
`rope`, just one chain PER ink point instead of a single 2-anchor span.

Anchors: `sampleTextInk(text,font,weight,anchors,W,H,hash(L.id+':rope-ink'))`
(editor) / `sampleInk(...)` (baked) with `anchors` (the anchor count) passed as
the sampler's `density`. Each returned ink point becomes the FIXED top (node 0) of
one rope.

Per-rope verlet (mirrors `rope`): each rope seeds `segments+1` nodes hanging
straight down from its anchor at a rest length `clamp(0.12/segments,0.004,0.2)`.
Per frame every node verlet-integrates (`x += (x-px)*damping`,
`y += (y-py)*damping + 0.0006*gravity`), node 0 is re-pinned to its anchor, then 6
relaxation passes pull each segment toward `rest` (node 0 immovable). Each emitted
instance carries `rot = atan2` of its local segment heading so the layer content
orients along the swinging rope. Returns ALL rope nodes flattened into one
`[{x,y,scale,rot}]` array (length `anchors * (segments+1)`), so it flows through
PASS A like every mode (effects + feedback + blend compose for free).

Caching (NO per-frame re-sampling, NO `getBoundingClientRect`): the anchor cloud +
all per-rope verlet state live on `L._ropeInk = { sig, ropes }` (editor) /
`SIM[L.id] = { riSig, ropes }` (slimPlayer). The signature is
`text|font|weight|anchors|segments|WxH`; the ink is re-sampled and the ropes
re-seeded ONLY when the signature changes (or, in the editor, when a
sampling-affecting inspector control nulls `L._ropeInk`). The verlet node state
PERSISTS across frames like `rope`'s `s.pts`, so the ropes keep swinging.

Params: `text`, `font` (css family), `weight` (100-900), `anchors` (anchor count =
low-density ink sample, 1-300), `segments` (per-rope chain length, 1-24),
`gravity` (0-3, scales the per-frame fall), `stiffness` (0.05-1, constraint
strength), `damping` (0.8-1, verlet velocity retention), `size` (per-instance
scale). The position-node template `rope-ink` (app.js) exposes these with
`sampleAnchors` + `stepRope` buildSpec helpers; the editor inspector adds the
matching fields (sampling-affecting ones null `L._ropeInk`); the baked slimPlayer
keeps parity (same anchors via `sampleInk`, same verlet integration). `L._ropeInk`
is runtime-only and stripped at bake.

This SUPERSEDES the deferred phase-2b note (full rope-anchored-to-ink) recorded in
11.4 + 12.5: that follow-up is now built as `rope-ink`.

### 11.6 Text-outline position mode (ordered glyph-OUTLINE contour tracing)
`text-outline` ("Text outline") is a position mode beside `text-ink` / `rope-ink`
that delivers ORDERED glyph boundary loops - the long-deferred "ordered glyph
OUTLINE" follow-up from 11.4 + 12.5, now SHIPPED. Where `text-ink` returns an
unordered shuffled point CLOUD (good for particles/dust), `text-outline` walks the
glyph boundary IN ORDER, so a layer renders content ALONG the outlines
(stroked-outline text, marching dots around the letters) and the ordered points can
later feed a closed `shape`/polyline. Each emitted instance carries `rot = local
tangent` so oriented content (dashes, arrows) follows the contour direction.

Tracing method (canvas-only, NO opentype, build-less): `traceTextOutline(...)`
(editor) / `traceInk(...)` (baked) draw the text large + centered on the SAME
offscreen alpha canvas approach as `sampleTextInk`, threshold the alpha into a
1px-padded BINARY GRID (downsampled on a stride so big canvases stay cheap, grid
capped ~220 cells on the long axis), then BORDER-FOLLOW / marching-squares trace
each filled-region boundary into an ORDERED loop (Moore 8-neighbour tracing,
clockwise from the backtrack direction, starting only at the left edge of a run so
each contour is visited once). Letter outlines AND their counters (holes) come out
as separate loops. Each contour is then Ramer-Douglas-Peucker simplified
(`simplify` epsilon, in grid cells; RDP split on a closed loop at its two
farthest-apart points), resampled to `density` evenly arc-length-spaced points,
normalized 0..1, and tagged with the local tangent `rot`. All contours are
concatenated into one ordered `[{x,y,scale,rot}]` array that flows through PASS A
like every mode (effects + feedback + blend compose for free). Pure +
DETERMINISTIC (no `Math.random`; tracing order is grid-scan deterministic) and no
`getBoundingClientRect`.

Caching (NO per-frame re-trace): the traced loops live on
`L._textOutline = { sig, pts }` (editor) / `SIM[L.id] = { toSig, pts }`
(slimPlayer). Signature = `text|font|weight|density|simplify|size|WxH`; the glyph
alpha is re-traced ONLY when the signature changes (or, in the editor, when a
sampling-affecting inspector control nulls `L._textOutline`). `L._textOutline` is
runtime-only and stripped at bake; the baked CFG carries the positioning params so
the slimPlayer `traceInk` reproduces the SAME loops.

Params: `text`, `font` (css family), `weight` (100-900), `density` (points PER
contour after resample, 3-800), `simplify` (RDP epsilon in grid cells, 0-4; 0 =
no simplify), `size` (per-instance scale). The position-node template
`text-outline` (app.js) exposes these with a `traceTextOutline` + `rdp` /
`rdpClosed` / `resampleClosed` buildSpec helper bundle; the editor inspector adds
the matching fields (all null `L._textOutline`); the baked slimPlayer keeps parity
via `traceInk` + `rdpB` / `rdpClosedB` / `resampleClosedB`.

### 11.7 Fluid effect (real-time Stam stable-fluids, GPU stateful + CPU fallback) - DONE
The long-noted "Navier-Stokes fluid" gap is DONE. `fluid` SHIPS as a per-LAYER
effect (composer-local catalog `FX_TYPES_LOCAL` / `FX_LABELS_LOCAL`, picker label
"Fluid (real-time)"). It now runs on the GPU via the SHARED fx.js STATEFUL-FX
foundation (below), with the original CPU solver kept as a fallback.

Stateful-FX foundation (fx.js, NEW - the part the GPU fluid stands on):
apply()/applyToImageData() are STATELESS - every effect is one fullscreen pass and
the two ping-pong FBOs are transient (never read across frames). Some effects need
PERSISTENT per-instance state. fx.js adds a stateful subsystem ALONGSIDE the
stateless chain (additive, the 15 stateless effects + apply()/applyToImageData()
are byte-for-byte unchanged). Public API on the chain:
`chain.stepStateful(instanceId, type, { params, intensity, source, pointer:{x,y,
dx,dy,down,hover}, dt, time, iterations, target })` lazily creates an instance's
PERSISTENT textures (single or ping-pong pairs) keyed by `instanceId` (the layer
id) + sized to the source, runs the effect's ordered MULTI-PASS sequence (with a
configurable solver iteration count) into those textures, then a DISPLAY pass to a
2D canvas (or `target`). `chain.disposeStateful(instanceId)` frees one instance;
`dispose()` frees all; `chain.hasStateful(type)` / `chain.statefulAvailable()`
report capability (the WebGL2-unavailable STUB returns null from stepStateful so
callers fall back to CPU). Stateful effects are declared in `STATEFUL_EFFECTS`:
each entry lists its persistent `textures` ({channels, ping, filter, wrap}), its
`programs` (fragment sources, compiled once per chain, shared by all instances),
and a `display` pass. The foundation is GENERIC: feedback (one ping texture + a
fade/composite pass) and GPU particles (a position/velocity ping pair + update +
draw passes) can be added as further `STATEFUL_EFFECTS` entries with NO runtime
changes (see 11.9). Float render targets (RGBA16F via EXT_color_buffer_float,
probed for framebuffer-completeness) are used when available, falling back to
RGBA8 (LINEAR filtering on float falls back to NEAREST without
OES_texture_float_linear).

GPU fluid (first `STATEFUL_EFFECTS` entry): a Stam stable-fluids solver fully on
the GPU. Persistent per-layer textures: velocity (RG, ping-pong), pressure (R,
ping-pong), divergence (R, single), dye (RGBA, ping-pong), curl (R, single). The
sim runs on a coarse grid (control `grid`, default 128 on the long axis, clamped
32-512; short axis from the source aspect); the display pass samples the full-res
source. Per-step pass sequence: (1) seed dye - refresh a fraction (6%, full on the
first frame) of the dye from the LAYER's rendered pixels so the flow stirs the
real content; (2) splat - inject velocity + dye from the pointer (gaussian splat,
only while hovering/down, driven by `pointer.dx/dy`); (3) advect velocity
(semi-Lagrangian; `viscosity` acts as velocity dissipation); (4) optional
vorticity confinement (`curl` amount > 0: curl pass then a vorticity force pass);
(5) divergence; (6) pressure Jacobi x N (`iterations`, default 24, clamped 1-60);
(7) gradient subtract (divergence-free velocity); (8) advect dye + fade (`fade`);
(9) display - composite stirred dye over the source by `uIntensity`. Controls map
to the existing `fluid` template: `viscosity`, `force`, `fade`, `radius`, `grid`,
plus NEW `iterations` and `curl` (added to `_effectTemplate("fluid")` in app.js +
`FLUID_UNIFORMS` in the composer). NO `getBoundingClientRect`, NO `Math.random`,
build-less raw WebGL2.

CPU fallback (kept, unchanged math): the original Jos Stam coarse solver
(`FluidSim` editor / `fluidStep` baked) - semi-Lagrangian advection, velocity
diffusion, a fixed 12-iteration Jacobi projection (two projects/frame), the layer
pixels as dye (6% refresh), gaussian pointer splat, bilinear upsample. It runs
when WebGL2/float is unavailable (the chain is a stub, or `stepStateful` returns
null). It honors `viscosity`/`force`/`fade`/`radius`/`grid` (the `iterations` /
`curl` refinements are GPU-only).

Composer wiring: a `stepFluid(cv,id,params,dt,time)` dispatcher (editor) /
`stepFluid(cv,id,params,dt)` (baked) prefers the GPU path and falls back to CPU,
writing the result back into the layer buffer `cv` so masking + the stateless GL
effect chain compose on top exactly as before. It runs in PASS B right before
masking, and the GL chain still filters `type==='fluid'` out so it is never
(mis)compiled as a shader pass. GPU buffers are disposed when a layer (or its
fluid effect) is removed (`disposeFluid` editor / `disposeFlu` baked, driven off
the live-layer prune in PASS A) and on `rebuild()`. Per-frame pointer deltas are
tracked once in `Input.tick()` (editor `Input.pdx/pdy`) / the baked frame loop
(`IN.pdx/pdy`) - no per-frame getBoundingClientRect. Baked parity: the standalone
slimPlayer inlines a self-contained GPU fluid (`GFLU`) on its existing WebGL2
context using the SAME shaders + pass sequence + param mapping as fx.js, with the
baked `fluidStep` CPU solver as the same fallback, so editor + export stir
identically.

### 11.8 Shatter position mode (voronoi fracture + matter.js rigid bodies) - DONE
The long-noted "fracture + rigidbody" gap is now DONE. `shatter` SHIPS as a
position mode beside `physics` (it does NOT touch the existing `physics` mode).

Fracture: `buildVoronoiCells(count, W, H, seed)` (editor) / `voronoiCells` (baked)
scatters `count` sites DETERMINISTICALLY (mulberry seeded by the layer-id file
hash, NO `Math.random`), then builds each convex Voronoi cell by Sutherland-Hodgman
clipping the W x H bounds rectangle against the perpendicular-bisector half-plane
between the site and every other site. The cells tile the rectangle EXACTLY
(verified 100% area coverage), so the shards re-assemble the image at rest.

Rigid bodies: each cell becomes a matter.js body via `Bodies.fromVertices` (the
SAME engine the `physics` mode loads on demand from esm.sh; the baked player adds
its own `import('https://esm.sh/matter-js@0.19.0')` loader since it is otherwise
self-contained), centered at the cell centroid, with floor + side + ceiling walls
so shards settle on screen. At rest the bodies sit at the centroids (rot 0). On a
trigger - `Input.clickPulse` edge (burst from the click point) or a clock-cadence
`auto` burst (`period`) - `shatterBurst` applies an outward impulse from the burst
point + a small upward kick + a random angular velocity (deterministic mulberry),
so shards fly and tumble apart under gravity. `slowmo` scales the engine substep
(slow-motion). The mode returns the per-shard transforms `[{x,y,scale,rot,
_shard}]` ([{x,y,scale,rot}] plus the cell for clipping).

Shard clipping: `drawContent` (editor) / `drawC` (baked) detect `inst._shard` and
draw the WHOLE intact layer content (cover-fit via `drawShatterContent` /
`drawShatterC`) CLIPPED to the cell polygon (translated to the cell's rest
centroid), under the body's live `{x,y,rot}` transform. So each shard carries its
own exact slice of the image and they reassemble seamlessly at rest. This is the
true per-shard cell clip (not a simplified transformed-piece approximation).

Caching: the voronoi + bodies are cached on `Positioning.sim[id]` (editor) /
`SIM[id]` (baked) by a signature of `count` + bounds; changing the shard count or
canvas size rebuilds, everything else (gravity / burst / spin / slowmo / trigger)
is applied live without a rebuild. Controls: `count` (shards), `gravity`, `burst`
(force), `spin`, `slowmo` (time scale), `trigger` (click / auto) + `period`.
app.js registers `_positionTemplate("shatter", "Shatter", "shatter", ...)` with a
`fracture(count, W, H, rng)` buildSpec helper, the `shatter` option in the
position-node field list, and `shatter` in the per-instance override panel (1D
count, like instances). Baked parity is full (same voronoi + matter setup + burst
math + shard clip). matter.js bodies are runtime-only and never serialized.

### 11.9 Face-morph effect (facial-landmark mesh warp, Parametric Portrait Morph) - DONE
The long-noted "facial-landmark morph" gap is now DONE. `face-morph` SHIPS as a
per-LAYER CPU effect in the composer, intercepted in PASS B exactly like `fluid`
(the GL chain filters `type==='face-morph'` out so it is never compiled as a
shader pass). It reads the layer's rendered pixels as the source texture, detects
478-point FaceMesh landmarks, triangulates, warps by parametric expression
controls, and composites back into the layer buffer so the existing effect stack
+ feedback still apply.

Detection (via `logicvision`, lazy CDN, fail-soft): two paths were added to
`LogicVision`. Still IMAGE portraits use `detectFaceImage(img, key)` - a one-shot
FaceLandmarker run in IMAGE running-mode, cached by the asset url (NO per-frame
re-detect; re-detect only on url change; resolves to `[]` on no-face / no-model so
it is not retried forever). Live camera/video use `detectFaceVideo(videoEl, key)` -
a VIDEO running-mode detect throttled to `DETECT_INTERVAL_MS` (the same ~15fps cap
as the streaming detector), state per key so several effects on one feed share one
inference. Both return the SAME shape (`faceDetsFromRaw`: per-face normalized 478
mesh + bbox + named points), so the morph reads one shape regardless of source.
The IMAGE-mode task is a SEPARATE FaceLandmarker instance (`'faceImage'`) since
MediaPipe ties running-mode to the instance. Everything stays lazy + fail-soft: a
missing model means no warp, never a throw.

Mesh: `FaceMorph.buildMesh` (editor) / `FM.build` (baked) collects a curated
COARSE FaceMesh subset (`FACEMORPH_GROUPS` mouth/brow/jaw/cheek + `FACEMORPH_EYE`
lids + `FACEMORPH_RING` silhouette + `FACEMORPH_NOSE`) plus 4 image corners and 4
edge midpoints as fixed anchors (so the background outside the face is held still),
and triangulates with a deterministic Bowyer-Watson `delaunay` (NO `Math.random`;
super-triangle + circumcircle test, returns a flat vertex-index list). The base
mesh is cached by a low-precision point-hash signature: a still image builds it
once; a live feed rebuilds on detection change.

Parametric deform (`FaceMorph.deform` / `FM.deform`): starts from identity (every
anchor fixed) and moves landmark groups, all scaled by the master `amount` and by
the ring-derived face scale. `smile` lifts/spreads the mouth corners (up+out) and
nudges the lips; `browRaise` lifts both brows; `eyeWiden` opens the lids (upper up,
lower down); `jawDrop` drops chin/jaw + lower lip; `cheekPuff` bulges the cheeks
outward from center; `headTilt` rotates the whole face region about the face
center (anchors stay put). Dest points are clamped to 0..1 so sampling stays
finite.

Render (`warpMeshAffine` / `bWarp`): per-triangle affine texture map on canvas2d
(no WebGL). The current layer pixels are snapshotted into an offscreen texture;
for each triangle the canvas is clipped to the DEST triangle (outset ~0.6px toward
its centroid for seam coverage) and the texture is drawn under the affine that maps
the SRC triangle onto the DEST triangle (the 6-coefficient solve is finite-guarded;
degenerate triangles are skipped).

Live track: when `track` is on AND the source is a live feed, `trackExpression` /
`bTrack` derive coarse expression signals (mouth width/openness, brow-eye gap, eye
openness, each scale-normalized by the inter-ocular distance with a neutral
baseline subtracted) and ADD an exaggerated copy to the manual sliders - a
funhouse-mirror that mimics the user. Still images ignore `track`.

Controls: `amount`, `smile`, `browRaise`, `eyeWiden`, `jawDrop`, `cheekPuff`,
`headTilt`, `track` (boolean), `source` (auto/image/camera). app.js registers
`_effectTemplate("face-morph", "Face morph", "face-morph", ...)` buildSpec + the
`face-morph` option in the effect-node field list. Baked parity is full (same
subset constants + `bDel` Delaunay + `bWarp` affine + `deform` + `bTrack`, plus a
lazy `logicvision` import when any baked layer carries the effect). Camera
permission stays gesture-gated via the existing `ensureCameraContent` / `ensureCam`
path (a `source==='camera'` morph counts as needing the webcam). NO `Math.random`,
NO per-frame `getBoundingClientRect`, fail-soft to identity.

### 11.10 Next on the stateful-FX path (feedback / particles) - NOT YET DONE
The stateful-FX foundation in fx.js (see 11.7) is GENERIC by design - a stateful
effect is just an entry in `STATEFUL_EFFECTS` declaring its persistent textures +
ordered passes + a display pass, with NO runtime changes needed to add one. Two
existing composer features are natural candidates to migrate onto it later (not
done yet, called out so a future wave does not re-invent the plumbing):
- Per-layer feedback / trail (11.3) is today a CPU `destination-out` fade on the
  layer 2D buffer. It could become a stateful effect with ONE ping texture (the
  trail accumulator) + a fade/composite pass, keeping the trail in GPU memory
  instead of round-tripping pixels.
- GPU particles could become a stateful effect with a position/velocity ping pair
  (update pass) + a draw pass, replacing CPU verlet point clouds where density
  warrants the GPU.
Both would reuse `stepStateful` / `disposeStateful` and the float-or-RGBA8 target
handling verbatim. Until then they keep their current CPU implementations.

---

## 12. The `type-motion` render node (Kinetic Type, per-glyph animated text)

`type-motion` `⒜` (palette label "Kinetic Type") is a RENDERABLE composition
primitive in the "Logic / Render" palette section, registered client-side in
`LOGIC_NODE_DEFS` (app.js) like `shape` - NOT in the backend KIND_IO registry.
It draws per-glyph animated text (slot-machine logos, weightless floating
letters, elastic letter hops, etc.) into a layer buffer, so it joins the
composer z-stack + per-layer effect + feedback + blend pipeline exactly like
every other layer. `_isLogicKind("type-motion")` returns false (it is a sink,
not a node the engine evaluates), mirroring `shape`.

### 12.1 Ports + controls
- in: none (v1). out: `out:layer` (dtype "layer", tags ["layer"]).
- controls: `text`, `font` (css family stack), `weight` (100-900), `size` (px),
  `color` (css), `tracking` (letter-spacing in em), `align` (center/left/right),
  `behavior` (the library below), `speed`, `amplitude`, `stagger` (per-glyph
  delay in seconds), `loop` (boolean), the TEXT-ON-PATH controls (`path`,
  `pathRadius`, `pathAmplitude`, `pathRotate` - see 12.6), plus the layer-shared
  `opacity`, `blend`, `z`, `feedback`.

### 12.2 Wiring + ingest path (mirrors `shape`)
- app.js `workflowKindIo("type-motion")` returns `_TYPEMOTION_KIND_IO`, whose
  `out` resolves with flavor "layer" so `resolveUpstreamInputs` ingests it as a
  layer (`i.type === "layer"`).
- `_wiredLayerSpec` tags the spec `_typemotion:true`; all authored controls ride
  on `spec.params` and pass through unchanged.
- mmcomposer `buildWiredRuntimeLayers` sees `spec._typemotion` and emits a layer
  whose `content.kind === "typemotion"` (carrying every param), with `z` /
  `opacity` / `blend` / `feedback` from the controls.
- `drawContent` branch `c.kind==='typemotion'` calls `drawTypeMotion(ctx, c,
  Input.clock)`; the baked slimPlayer mirrors it via `drawTM(c, IN.clock)`. The
  per-glyph math lives in `typeMotionXform` (editor) / `tmXform` (baked) - kept
  identical so export matches the editor. No `getBoundingClientRect` in the draw
  loop; layout uses `ctx.measureText` advances + the `tracking` control, baseline
  middle, aligned per `align`.

### 12.3 Behavior library (16, switched by the `behavior` control)
Each animates per-glyph from `(i, n, t=clock, speed, amplitude, stagger)`:
`none`, `wave` (sine y by i), `jitter` (deterministic pseudo-noise dx/dy/rot),
`rotate-cycle`, `scale-pulse`, `slot-cycle` (vertical slot-machine roll per
glyph), `fade-stagger`, `typewriter` (reveal glyph i over time), `fall-gravity`
(drop + settle bounce), `elastic-hop` (elastic ease-out bounce),
`weightless-float` (summed-sine drift in x+y+rot), `rainbow-cycle` (hue per i+t),
`skew-sway`, `blur-in` (alpha + scale ramp; blur faked via scale for perf),
`squash-stretch`, `orbit` (each glyph circles its slot). Behaviors whose dy/dx is
em-relative set `_em` so the drawer multiplies by `size`. `rainbow-cycle`
overrides per-glyph color via `hsl(...)`; all others honor the `color` control.

### 12.4 Effect + feedback composition (free, because it IS a layer)
Because the glyphs render into the same per-layer buffer that `text` / `polyshape`
/ `asset` use, the existing per-layer EFFECT stack and the FEEDBACK / trail
control compose on top automatically: a wired Effect node on the layer post-
processes the rasterised glyphs, and a non-zero `feedback` leaves a decaying
trail of the moving letters. z-order + opacity + blend behave like any layer.

### 12.5 Phase-2 bridge (glyph-ink -> points: PARTIALLY built)
The "text -> point cloud" bridge now SHIPS as the `text-ink` POSITION mode (see
11.4), taking a different route than originally sketched: instead of `opentype`
glyph-outline tessellation, it samples drawn glyph INK from an offscreen canvas
(`getImageData`, alpha-threshold, deterministic shuffle, normalize). This is
font-agnostic (any css `font-family`) and needs no opentype in the runtime. The
particle / dust + letter-disintegration consumer is fully built (`text-ink` +
`drift` + layer `feedback`), and the physics-rope-anchored-to-ink consumer now
SHIPS as the `rope-ink` position mode (see 11.5) - the deferred phase-2b
rope-anchored-to-ink note is superseded. The ordered glyph-OUTLINE variant is now
also DONE: it SHIPS as the `text-outline` POSITION mode (see 11.6), which border-
follows / marching-squares traces the glyph alpha into ORDERED contour loops (still
canvas-only, no opentype) suitable for feeding a closed `shape`/polyline or
marching dots. Still NOT built: `type-motion` EXPOSING the cloud as vector2 `out`
ports on the node itself (the cloud / outline currently lives in the position
modes, not as node outputs) - a finer follow-up.

### 12.6 Text on path (per-glyph BASE placement along a curve)
`type-motion` can lay each glyph's BASE position along a curve instead of the
straight x-axis baseline, via four controls: `path`
(straight/arc/circle/wave/ring), `pathRadius` (em-fraction of the block-width
proxy `ref`, used by arc/circle/ring), `pathAmplitude` (px, used by wave), and
`pathRotate` (rotate each glyph to the path tangent). `path=straight` is the
LEGACY layout - identical math, NO regression. The per-glyph BEHAVIOR animation
(12.3) still applies ON TOP of the path placement: for non-straight paths the
behavior dx/dy offset is applied in the glyph's LOCAL frame (after the tangent
rotation), so wave/jitter/orbit/etc. read correctly along the curve.

`path=circle` / `path=ring` + `behavior=rotate-cycle` delivers the "Spoke & Word
Type" text-wraps-around-a-wheel look. The placement helper
`typeMotionPathPoint(path, s, total, radius, amplitude, ref)` (editor) /
`tmPathPoint(...)` (baked - kept identical) maps each glyph's CENTER arc-length
`s` (measured by `ctx.measureText` advances, the same advance walk the straight
layout uses) to a base `{x,y,rot}`: circle/ring spread evenly over 2*pi by
arc-length fraction starting at top; arc bows a ~210deg partial circle; wave is a
sinusoidal y over the straight x with a slope-following tangent. All math is finite
for `total=0`. No `getBoundingClientRect`; the params ride on `content` (typemotion
layer) so the baked CFG carries them and `drawTM` reproduces the path identically.

---

## 13. The `palette` extraction node (image -> N dominant colors) - DONE

`palette` `◧` is a logic SOURCE/processor over a wired IMAGE. It is a true logic
node (`_isLogicKind("palette")` is true), so the engine evaluates it and its
outputs reach targets through the normal `kind:"logic"` binding path (numeric
ports into `param:<key>`) PLUS a new color path into a `shape`'s fill/stroke.

### 13.1 Ports + controls
- accepts: `image` (dtype `string`, tags `["asset","image"]`) - wire an asset
  node here (mirrors `input-audio`'s `asset` accept).
- controls: `count` (2-8 dominant colors), `quality` (sample-stride; higher =
  faster + coarser).
- provides: `color0`..`color7` (dtype `color` = `{r,g,b,a}` 0..1, sorted most
  populous first), `dominant` (color = `color0`), `domR`/`domG`/`domB` (number
  0..1 - the dominant color's channels, so it can drive numeric params with NO new
  engine path), `ready` (boolean), `count` (number).

### 13.2 Extraction (runtime, cached, never per-frame)
The pure engine has no canvas/Image, so extraction runs in the RUNTIME exactly
like number-generator pixel-map. At PROJECTION time the editor resolves the wired
image url (`_paletteImageUrl`, mirrors `_numberPixmapUrl`) and bakes it onto the
projection node as `params._imageUrl`, so the runtime knows what to decode without
re-walking the graph. The runtime (`_extractPalette` editor / `extractPalette`
baked, identical math) downsamples the image to <=160px on the long axis, samples
pixels on the `quality` stride (skipping transparent), then `_medianCut` /
`medianCut` recursively splits the pixel set on the widest channel into `count`
buckets and averages each. The result is cached by `url + '@' + count` and NEVER
re-extracted per frame (mirrors `Sources._pixel`'s `_imgCache`). The colors are
entered into `frame.palettes[nodeId] = { colors:[{r,g,b,a}], dominant }` - EXACTLY
how vision-detect results reach the engine via `frame.streams`. Deterministic (no
`Math.random`), no `getBoundingClientRect`, build-less (native canvas).

### 13.3 Consuming paths (both wired + working)
1. NUMERIC: `palette.domR/domG/domB` -> any numeric `param:<key>` (e.g. an effect
   color channel, a position param) via the existing `kind:"logic"` binding +
   `LogicBridge.applyScalar` - zero new engine code.
2. COLOR: `palette.color0..7 / dominant` -> a `shape` node's NEW `fill` / `stroke`
   color accept ports (dtype `color`). Collected at projection time into
   `spec._colorPoints[fill|stroke] = { kind:"logic", ref:{node,port} }`
   (`_shapeColorBindings`, the color sibling of `_shapePointBindings`); the runtime
   resolves the full `{r,g,b,a}` via `LogicBridge.color(ref)` -> a CSS `rgba(...)`
   string and overrides the shape's drawn fill / stroke (the text controls remain
   the fallback when unwired). Editor `drawPolyShape` + baked `drawPoly` honor it.
   This is the working color->control binding path the contract asked for.

## 14. The `audio-out` synth node (audio output / image->sound) - DONE

`audio-out` `◢` is a true logic SINK that produces sound. See §2.9 for ports.

### 14.1 Engine (sink republishing)
The engine evaluator resolves `frequency` / `gain` / `cutoff` from wired inputs
(falling back to the node's controls when unwired), reads `waveform` from the
control, and edge-detects `trigger` into a one-frame note-on pulse
(`LogicGraph._rise`). It emits these as the node's out-ports so the runtime bridge
can read them. Pure + deterministic (no DOM in the engine).

### 14.2 Runtime module (`editor/tools/_shared/logicaudio.js`)
`LogicAudio.attach(opts) -> { set(params), suspend(), resume(), dispose() }`
mirrors the LogicInputs / LogicVision shape. WebAudio graph:
`oscillator(waveform) -> gain -> lowpass filter -> destination`. The AudioContext
is NEVER created at module load (per §6 / the im-permission rules): `attach()`
returns a context-less handle, and the FIRST `set()` that wants sound
(`on !== false && gain > 0`) creates the context behind the `LogicPermission`
overlay (gate 1 = our explanatory prompt on the user gesture; the browser's own
audio unlock is implicit on the same gesture). Until the user allows it, `set()`
is a silent no-op (nothing throws, nothing autostarts). Once a context exists,
`set()` is a cheap per-frame ramp: frequency / gain / cutoff use
`setTargetAtTime` (no zipper noise), the waveform swaps only on change (no node
churn), and a rising `trigger` fires a short attack-decay note-on envelope.

### 14.3 Bridge feed (per frame, Live only)
The mmcomposer LogicBridge collects every `audio-out` node id from the projection,
lazy-loads `logicaudio.js`, and after each `LogicGraph.tick` calls
`LogicBridge._driveAudio` -> `audioHandle.set({frequency,gain,cutoff,waveform,
trigger,on:true})` from the resolved out-ports (MVP = one mono voice from the first
audio-out node). Pausing (`setLive(false)`) suspends the context; resuming resumes
it. The baked slimPlayer mirrors this verbatim (`LB.driveAudio` in `LB.tick`,
loading `logicaudio.js` by absolute URL), so the published piece produces audio
too (gesture-gated). No CDN (WebAudio is native), no `getBoundingClientRect`.

## 15. Editor tool features (spline-3d, vector-editor)

These ship inside the standalone editor tools (not the logic graph), tracked
here so the long-noted gaps are visible.

### 15.1 3D text in the spline-3d tool - DONE
The "3D text" gap is DONE. `editor/tools/spline3d/index.html` now adds a
"3D Text" object via the toolbar (`data-add="text3d"`) and a "3D Text" inspector
panel (text / font / size / depth / bevel). It is rendered as REAL extruded +
beveled glyph geometry with three.js `TextGeometry` + `FontLoader` (typeface.json
fonts loaded from the same esm.sh CDN as the rest of the tool's three.js, cached
per font, FAIL-SOFT: a missing CDN flashes a notice and removes the placeholder
rather than throwing). TextGeometry was chosen over troika-three-text because the
extrude/bevel + the tool's MeshPhysicalMaterial modes (glass / metal / clearcoat)
are exactly what TextGeometry gives for free, whereas troika's SDF shader is flat
and ignores those material modes. The text object reuses the existing material
system, orbits / lights like every other object, serialises into the scene JSON
(`userData.text3d` → `serializeScene`/`restoreScene`, rebuilt async on load) and
bakes into the `.glb` on Export via the generic object-export path. Additive: the
existing primitives, SVG-extrude, boolean/CSG, blob, cloth, liquid and export
paths are untouched. No `getBoundingClientRect` per frame; deterministic.

### 15.2 SVG path-offset in the vector-editor - DONE
The "SVG path-offset" gap is DONE. The vector-editor (in `editor/app.js`) gains an
"Offset path" operation alongside the boolean-ops / convert-text-to-outlines
affordances. Controls: distance (canvas units, negative = inset), steps
(concentric count 1..24 for the "Expansive" offset look) and join (miter / round).
Algorithm (`_vecOffsetRing` / `_vecOffsetShapeRings` / `_vecRingsToD`): each
selected shape is sampled into closed rings (reusing `_vecShapeToPolygon`); every
vertex is displaced along its corner bisector (average of the two adjacent edge
normals), winding-normalised by signed area so a positive distance always inflates;
convex corners are finished with a miter join clamped to a miter limit (no infinite
spikes at acute angles) or a round join that fans arc points past that limit.
Negative distance insets. For steps > 1 it emits N concentric copies (step k
offset by k·distance). When the vendored polygon-clipping lib is present the offset
rings are unioned to drop self-overlaps from large offsets; otherwise the raw
offset stands (robust + finite on its own). Each result is inserted as a new
editable `path` shape inheriting the source paint (recolorable), so it bakes to the
`.svg` like every other shape. Additive: draw / boolean / text-outline / trace /
node-edit paths are untouched. Deterministic (no randomness, time or layout reads).
