## Dataflow + edge model, and how an output reaches a target

### 1. Dataflow + edge model

- Nodes live in `data.nodes` as `{ id, kind, spec:{ v:1, kind, params:{...} } }`. For a logic node the `params` are its compiled control values (see each kind's controls in the `catalogue` section). A node placed with default controls already has a valid spec.
- Wires live in `data.edges` as `{ from:"<nodeId>.<port>", to:"<nodeId>.<port>" }`. Always `nodeId.port` on both sides. Example: `{ from:"cam1.stream", to:"hand1.stream" }`.
- Logic ports are TYPED with a `dtype`. A wire is valid only if the dtypes are compatible:
  - same dtype always connects (number to number, vector2 to vector2, event to event, ...).
  - `event` connects to `boolean` (the pulse reads as true the frame it fires).
  - `number` and `boolean` interconnect (0 = false, nonzero = true).
  - `vector2` and `region` do NOT auto-coerce: break them into components with `op-vector` (mode `break`) before feeding a number port.
  - to reach a `string` input, go through `op-tostring` (the only coercion path to string).
- dtypes in play: `event`, `number`, `vector2` ({x,y} normalized 0..1 by default), `region` (bbox), `boolean`, `string`, `color`, and `layer` (shape.out, input-camera.layer, input-video.layer, type-motion.out, and sketch.out).

### 2. How an output reaches a target

There are exactly two sinks a logic output can drive:

(a) PARAM BINDING. Wire a logic node's OUTPUT port into a target node's `param:<key>` INPUT port. The editor writes `spec._bindings[<key>] = { kind:"logic", ref:{ node, port } }` and the runtime reads that value from the engine each frame instead of a static control value. Edge shape: `{ from:"smooth1.value", to:"fx1.param:intensity" }`.
   - `param:<key>` INPUT ports exist ONLY on these kinds, and only for their NUMBER / RANGE controls: `position`, `effect`, `trigger`, `number-generator`, `sketch`. So you can drive `effect.param:intensity` (every effect has `intensity`), `effect.param:size` (pixelate), `effect.param:scanline` (crt), `position.param:<numericMode controls>`, etc. The exact numeric controls per mode / effect are in the `runtime` section.
   - A LAYER node has NO `param:` input ports. You do NOT drive a layer node directly. To make a layer react, drive the Effect or Position node that is wired into that layer. The layer exposes only a READ-BACK output `paramout:opacity` (its current opacity, for logic to READ).
   - READ-BACK: `position` / `effect` / `trigger` also expose `paramout:<key>` OUTPUT ports (current resolved value this frame) and `layer` exposes `paramout:opacity`. Wire a `paramout:` port INTO a logic accept port to feed a target's live value back into the graph.

(b) SHAPE POINTS. The `shape` node has eight `vector2` INPUT ports `p0..p7`. Wire any logic `vector2` output into them (e.g. `vision-detect.indexTip`). The editor writes `spec._points[pK] = { kind:"logic", ref:{ node, port } }`. The shape's `out` (dtype `layer`) wires into a composer / mm-composer `in` port, where it joins the z-stack + effect + blend pipeline exactly like a layer. Points are the polygon vertices IN ORDER p0, p1, ... up to the highest wired index; unwired points are skipped, so a partially wired shape still draws.

### Composition ownership and temporal behavior

Only upstream nodes of the owning composer run. Wire force.out and audio-out.out to composer.in, or supply an explicit composerId on the sink. Unwired sinks do not run globally.

Input coordinates, button filters, touch limits, scroll clamp/units, keyboard repeat, and gyro smoothing are per node. Capture supplies raw shared device data. Audio nodes use separate analysers (FFT size is rounded to the nearest supported power of two), sharing microphone capture only for source=mic. source=asset reads the wired asset URL and never falls back to a microphone.

state-delay returns zero during its N-frame warm-up, then the input from exactly N ticks ago. Feedback states read saved state before evaluating the graph and update after the graph. Pure combinational cycles, including self-loops, are errors.

flow-while (Bounded sample) and flow-repeat (Repeat sample) sample memoized inputs. They do not re-execute an upstream subgraph or mutate its state per iteration. Only external number-source expressions can see an iteration index.

dat-websocket retries closed connections while the graph runs, with exponential backoff from 1 to 30 seconds. Graph replacement disposes sockets and aborts in-flight data requests.
