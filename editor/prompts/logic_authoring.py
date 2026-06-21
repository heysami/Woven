"""Agent authoring guide for the Woven Logic Graph.

This module exports ONE string constant, ``LOGIC_AUTHORING_GUIDE``, that the
capabilities preamble (``editor/kinds/capabilities.py``) appends to the chat
agent's system prompt in the workflow-building context. It teaches the agent
how to turn a natural-language app request ("a camera that detects a hand,
draws a polygon between the fingertips, with a glitchy image behind") into a
concrete wired logic graph: which node kinds to place, which ports to wire,
which controls to set, and how outputs reach their targets.

ACCURACY CONTRACT: every kind / port / dtype named below is verified against
``LOGIC_NODE_DEFS`` in ``editor/app.js`` (the authoritative client-side
registry) and against the spec-node connect defs in ``WORKFLOW_CONNECT_DEFS``
+ the spec templates. If you edit the registry, update this guide to match.

3.9-safe: pure module-level string, no annotations needing evaluation, no
3.10+ syntax. No em or en dashes anywhere in the text.
"""
from __future__ import annotations

LOGIC_AUTHORING_GUIDE = r"""## Logic Graph authoring - turn an interactive-app request into a wired node graph

When the user asks for an INTERACTIVE app (camera / hand / face detection, pointer or touch or scroll or gyro or audio reactive behaviour, shapes drawn from tracked points, effects that react to input), build it as a LOGIC GRAPH: typed input nodes feeding processors and operators, whose outputs drive a composer's layer / position / effect params or a `shape` node's points. This section is the complete authoring contract. Build the graph the same way you build any node graph: commit nodes with `addNodes` and wire them with edges. Execution only runs in LIVE mode (the composer's Live / mm:logic-run toggle); in edit mode the graph is inert.

### 1. Dataflow + edge model

- Nodes live in `data.nodes` as `{ id, kind, spec:{ v:1, kind, params:{...} } }`. For a logic node the `params` are its compiled control values (see each kind's controls below). A node placed with default controls already has a valid spec.
- Wires live in `data.edges` as `{ from:"<nodeId>.<port>", to:"<nodeId>.<port>" }`. Always `nodeId.port` on both sides. Example: `{ from:"cam1.stream", to:"hand1.stream" }`.
- Logic ports are TYPED with a `dtype`. A wire is valid only if the dtypes are compatible:
  - same dtype always connects (number to number, vector2 to vector2, event to event, ...).
  - `event` connects to `boolean` (the pulse reads as true the frame it fires).
  - `number` and `boolean` interconnect (0 = false, nonzero = true).
  - `vector2` and `region` do NOT auto-coerce: break them into components with `op-vector` (mode `break`) before feeding a number port.
  - to reach a `string` input, go through `op-tostring` (the only coercion path to string).
- dtypes in play: `event`, `number`, `vector2` ({x,y} normalized 0..1 by default), `region` (bbox), `boolean`, `string`, `color`, and `layer` (only the `shape` node's `out`).

### 2. How an output reaches a target

There are exactly two sinks a logic output can drive:

(a) PARAM BINDING. Wire a logic node's OUTPUT port into a target node's `param:<key>` INPUT port. The editor writes `spec._bindings[<key>] = { kind:"logic", ref:{ node, port } }` and the runtime reads that value from the engine each frame instead of a static control value. Edge shape: `{ from:"smooth1.value", to:"fx1.param:intensity" }`.
   - `param:<key>` INPUT ports exist ONLY on these kinds, and only for their NUMBER / RANGE controls: `position`, `effect`, `trigger`, `number-generator`. So you can drive `effect.param:intensity` (every effect has `intensity`), `effect.param:size` (pixelate), `effect.param:scanline` (crt), `position.param:<numericMode controls>`, etc.
   - A LAYER node has NO `param:` input ports. You do NOT drive a layer node directly. To make a layer react, drive the Effect or Position node that is wired into that layer. The layer exposes only a READ-BACK output `paramout:opacity` (its current opacity, for logic to READ).
   - READ-BACK: `position` / `effect` / `trigger` also expose `paramout:<key>` OUTPUT ports (current resolved value this frame) and `layer` exposes `paramout:opacity`. Wire a `paramout:` port INTO a logic accept port to feed a target's live value back into the graph.

(b) SHAPE POINTS. The `shape` node has eight `vector2` INPUT ports `p0..p7`. Wire any logic `vector2` output into them (e.g. `vision-detect.indexTip`). The editor writes `spec._points[pK] = { kind:"logic", ref:{ node, port } }`. The shape's `out` (dtype `layer`) wires into a composer / mm-composer `in` port, where it joins the z-stack + effect + blend pipeline exactly like a layer. Points are the polygon vertices IN ORDER p0, p1, ... up to the highest wired index; unwired points are skipped, so a partially wired shape still draws.

### 3. Logic kind catalogue (quick reference; ports verified against LOGIC_NODE_DEFS)

Format: `kind` [controls] - ports. (i)=input/accept, (o)=output/provides. dtype in parens.

SOURCES (no inputs):
- `input-pointer` [space, button] - (o) x(number) y(number) isDown(boolean) clicked(event) downX(number) downY(number) upX(number) upY(number) hover(boolean) pos(vector2)
- `input-touch` [maxPoints, space] - (o) count(number) pos(vector2) touches(vector2) isDown(boolean) center(vector2) spread(number) pinchDelta(number) rotation(number) tap(event)
- `input-keyboard` [key, repeat] - (o) key(string) isDown(boolean) pressed(event) released(event) axisX(number) axisY(number)
- `input-scroll` [space, clampMin, clampMax] - (o) deltaY(number) deltaX(number) accumY(number) accumX(number) velocity(number)
- `input-gyro` [smoothing] - (o) alpha(number) beta(number) gamma(number) tilt(vector2) ready(boolean)
- `input-audio` [source, band, fftSize, smoothing] - (i) asset(string) - (o) level(number) pitch(number) band(number) beat(event)
- `input-camera` [facing, resolution] - (o) stream(string) ready(boolean) layer(layer). The composer CAN render the live webcam: wire the `layer` output into a composer `in` and the feed becomes a real layer (content.kind camera), with the per-layer effect stack + feedback applying on top. The `stream` output feeds vision-detect / vision-ocr. (The Camera chip in the composer toolbar toggles the webcam on/off and adds the feed layer too.)
- `input-video` [loop, autoplay] - (i) asset(string) - (o) stream(string) t(number) playing(boolean)

PROCESSORS (stream in):
- `vision-detect` [detector(face|hand|object), target] - (i) stream(string) - (o) present(boolean) count(number) pos(vector2) region(region) gesture(string) confidence(number) AND per-landmark vector2: wrist thumbTip indexTip middleTip ringTip pinkyTip (detector=hand), nose leftEye rightEye (detector=face). A missing point degrades to {x:0,y:0}.
- `vision-ocr` [query, interval] - (i) stream(string) - (o) text(string) matched(boolean) region(region) count(number)

LITERALS (number is `number-generator`, NOT re-added here):
- `value-bool` [value] - (o) value(boolean)
- `value-string` [value] - (o) value(string)
- `value-vec2` [x, y] - (o) value(vector2)

OPERATORS (pure, stateless):
- `op-math` [op: add|sub|mul|div|mod|min|max|pow|atan2] - (i) a(number) b(number) - (o) r(number)
- `op-unary` [op: abs|neg|floor|round|sin|cos|sqrt|sign] - (i) a(number) - (o) r(number)
- `op-compare` [op: eq|ne|lt|gt|le|ge, epsilon] - (i) a(number) b(number) - (o) r(boolean)
- `op-logic` [op: and|or|xor|nand|nor] - (i) a(boolean) b(boolean) - (o) r(boolean)
- `op-map` [inMin, inMax, outMin, outMax, clamp, ease: linear|in|out|inout] - (i) x(number) - (o) r(number). Remap + clamp + ease.
- `op-vector` [mode: make|break|distance|add|scale|lerp] - (i) x(number) y(number) v(vector2) a(vector2) b(vector2) t(number) - (o) v(vector2) x(number) y(number) d(number). Ports are a superset; the engine reads only the ones the mode uses (make: x,y -> v; break: v -> x,y; distance: a,b -> d; add: a,b -> v; scale: v,t -> v; lerp: a,b,t -> v).
- `op-tostring` [template] - (i) a(number) - (o) s(string). Template like "x={v}".

CONTROL FLOW:
- `flow-if` [] - (i) cond(boolean) then(number) else(number) - (o) r(number)
- `flow-gate` [holdLast] - (i) value(number) open(boolean) - (o) r(number)
- `flow-while` [maxIterations] - (i) cond(boolean) body(number) - (o) count(number) last(number)
- `flow-repeat` [] - (i) n(number) body(number) - (o) sum(number) values(number, per-instance vector)

STATE (reactive memory; the legal cycle breakers):
- `state-counter` [step, wrap] - (i) inc(event) reset(event) - (o) count(number)
- `state-toggle` [initial] - (i) flip(event) - (o) on(boolean)
- `state-latch` [] - (i) set(boolean) hold(number) - (o) value(number)
- `state-timer` [autostart] - (i) start(event) stop(event) - (o) elapsed(number) running(boolean)
- `state-smooth` [stiffness, damping] - (i) target(number) - (o) value(number). Critically-damped pursuit. Pass EVERY raw pointer / sensor value through this before it drives a param.

RENDER (a sink, not engine-evaluated):
- `shape` [closed, fill, stroke, strokeWidth, opacity, blend: normal|multiply|screen|overlay, z, smoothing] - (i) p0..p7(vector2) - (o) out(layer). Wire `out` into a composer `in`. fill / stroke are CSS color strings (fill blank = no fill).
- `type-motion` (Kinetic Type) [text, font, weight, size, color, tracking, align, behavior, speed, amplitude, stagger, path: straight|arc|circle|wave|ring, pathRadius, pathAmplitude, pathRotate, loop, z, opacity, blend, feedback] - (o) out(layer). Per-glyph animated text drawn STRAIGHT to the canvas (no rasterization). 16 behaviors: none, wave, jitter, rotate-cycle, scale-pulse, slot-cycle, fade-stagger, typewriter, fall-gravity, elastic-hop, weightless-float, rainbow-cycle, skew-sway, blur-in, squash-stretch, orbit. This is the PREFERRED way to put TEXT in the composer. Wire `out` into a composer `in`.
- TEXT-DRIVEN position modes on the `position` node (text made of particles / ropes / outlines): `text-ink` (samples a string's ink into a point cloud; pair with physics + layer feedback for letter-disintegration), `rope-ink` (verlet ropes anchored to glyph ink), `text-outline` (ordered contour points of the letters). Each carries text / font / weight controls.

### 4. Composition patterns (the reusable idioms)

- REMAP a raw value to a useful range: `source.<num>` -> `op-map` (set inMin/inMax to the input range, outMin/outMax to the target range) -> `target.param:<key>`.
- SMOOTH a jittery pointer / sensor value: `source.<num>` -> `state-smooth.target`, then `state-smooth.value` -> downstream. Always smooth pointer.x/y, gyro tilt components, audio level before they drive params.
- GATE events / values: `flow-gate` passes `value` only while `open` is true (else holds last). For event sources, `flow-gate` plus a `value-bool` or a compare drives conditional behaviour.
- PRESENCE-THRESHOLDED EFFECT: `vision-detect.present` (boolean) -> `effect.param:intensity`. present reads as 1 when detected, 0 otherwise, so the effect turns on only when a hand / face is present. For a smoother ramp use `vision-detect.confidence` (number) -> `op-map` -> `effect.param:intensity`.
- FEED VISION POINTS INTO A SHAPE: `vision-detect` (detector=hand) fingertip outputs -> `shape.p0..p4`, shape `out` -> composer `in`. Draws a polygon spanning the fingertips.
- DISTANCE / GESTURE FROM TWO POINTS: two vector2 outputs -> `op-vector` (mode=distance) a,b -> d(number) -> op-map -> a param (e.g. pinch distance drives scale).
- LAYER Z-ORDER for behind / front: give the background layer a LOWER `z`, the foreground shape a HIGHER `z`. The composer sorts ascending by z, so lower z paints first (behind).
- EFFECT ON A LAYER: wire an `effect` node into the layer's `in` port (the layer accepts `effect` tagged inputs). The effect applies to THAT layer only. Drive the effect live by binding a logic output into `effect.param:<key>`.
- TEXT IN THE COMPOSER: use the `type-motion` (Kinetic Type) node for animated text, or a `layer` with `text` content for plain static text. Both draw STRAIGHT to the canvas and are the correct primitives here. Do NOT use a `formatted-text` (HTML) node as composer layer content: HTML cannot be drawn to a canvas directly, so the composer has to rasterize it with html2canvas (adds refresh lag, same-origin only). Reserve `formatted-text` for rich static HTML used OUTSIDE the live composer.

### 5. Three worked end-to-end recipes (copy-pasteable: node list + controls + every edge)

Node ids below are illustrative; pick unique ids. Each recipe ends by wiring into an mm-composer (Interactive composer) and you set Live mode to run it.

RECIPE A - "Camera + hand + fingertip polygon + glitchy live camera behind"
Nodes:
  - `cam` kind=input-camera (facing=user)
  - `hand` kind=vision-detect (detector=hand, target=location)
  - `poly` kind=shape (closed=true, stroke="#6ee7ff", strokeWidth=3, fill="", z=10)
  - `glitch` kind=effect (type=slice  OR  type=pixel-sort  OR  type=crt; there is NO effect literally named "glitch", these read as glitchy)
  - `comp` kind=mm-composer
Edges:
  - cam.stream -> hand.stream            (detection feed)
  - hand.thumbTip -> poly.p0
  - hand.indexTip -> poly.p1
  - hand.middleTip -> poly.p2
  - hand.ringTip -> poly.p3
  - hand.pinkyTip -> poly.p4
  - cam.layer -> comp.in                 (the LIVE webcam as a layer, low z = behind)
  - glitch.out -> <the cam layer>.in     (apply the glitch effect to the camera layer; the cam.layer is a real layer that accepts effects)
  - poly.out -> comp.in                  (shape layer, high z = in front)
(To put a still IMAGE behind instead of the camera, use a `layer` with an asset wired in at low z; for the LIVE camera, cam.layer is the right output.)
Optional reactivity: hand.confidence -> map1(op-map 0..1 -> 0..1) -> glitch.param:intensity so the glitch strengthens with detection confidence.
NOTE on "the webcam behind": the composer renders the live webcam directly - wire `cam.layer` into `comp.in` (low z) and the feed shows as a layer; the glitch effect on that layer + the polygon (high z) compose on top. Do NOT claim the composer cannot show a live camera and do NOT build a separate prototype iframe for it - it works natively via the camera layer. (The `position` mode `camera-feed` is a different thing: it places instances AT detected landmarks, it does not paint the feed - use the `cam.layer` output for the visible feed.)

RECIPE B - "Tilt your phone to pan a parallax layer, brightness reacts to mic"
Nodes:
  - `gyro` kind=input-gyro (smoothing=0.2)
  - `mic` kind=input-audio (source=mic, band=full)
  - `smx` kind=state-smooth (stiffness=8, damping=1)
  - `vbreak` kind=op-vector (mode=break)
  - `panMap` kind=op-map (inMin=-1, inMax=1, outMin=0, outMax=1, clamp=true)
  - `pos` kind=position (mode=single)
  - `fx` kind=effect (type=posterize)
  - `lay` kind=layer
  - `comp` kind=mm-composer
Edges:
  - gyro.tilt -> vbreak.v
  - vbreak.x -> smx.target
  - smx.value -> panMap.x
  - panMap.r -> pos.param:<x-control>     (the position mode's numeric x control)
  - mic.level -> fx.param:intensity
  - pos.out -> lay.in
  - fx.out -> lay.in
  - lay.out -> comp.in

RECIPE C - "Click to advance a counter; show count; pinch-to-scale on touch"
Nodes:
  - `ptr` kind=input-pointer
  - `cnt` kind=state-counter (step=1, wrap=0)
  - `touch` kind=input-touch (maxPoints=2)
  - `pinchMap` kind=op-map (inMin=0, inMax=0.5, outMin=0.5, outMax=2.5, clamp=true)
  - `smx` kind=state-smooth (stiffness=10)
  - `pos` kind=position (mode=single)
  - `lay` kind=layer
  - `comp` kind=mm-composer
Edges:
  - ptr.clicked -> cnt.inc               (event -> event)
  - touch.spread -> pinchMap.x
  - pinchMap.r -> smx.target
  - smx.value -> pos.param:<scale-control>
  - pos.out -> lay.in
  - lay.out -> comp.in
  (cnt.count can drive any numeric param, e.g. position.param:rotation, via an op-map if you want a counted rotation.)

### 6. Translation procedure (user sentence -> wired graph)

1. IDENTIFY INPUTS. Map each driver in the request to a source kind: "camera / hand / face" -> input-camera + vision-detect; "mouse / click / hover" -> input-pointer; "touch / pinch" -> input-touch; "tilt / phone orientation" -> input-gyro; "mic / sound / beat" -> input-audio; "scroll / wheel" -> input-scroll; "keyboard / WASD / arrows" -> input-keyboard; "read text in the video" -> vision-ocr.
2. PICK PROCESSORS. Smooth raw pointer / sensor values through `state-smooth`. Remap ranges with `op-map`. Combine / threshold with `op-math` / `op-compare` / `op-logic`. Derive points / distances with `op-vector`. Hold or branch with `flow-gate` / `flow-if`. Accumulate with `state-counter` / `state-latch` / `state-timer`.
3. CHOOSE OUTPUTS / TARGETS. To show TEXT -> `type-motion` (Kinetic Type, animated) or a `layer` with `text` content (static); NOT `formatted-text` (that needs rasterizing in the composer). To draw between tracked points -> `shape` (p0..p7) -> composer. To animate a transform -> `position.param:<key>`. To drive a visual effect -> `effect.param:intensity` (or per-type params). Remember: layers have no param ports, drive their wired position / effect instead.
4. WIRE + SET LIVE. Place the composer (mm-composer / composer), wire every layer / shape `out` into its `in`, set z-order for behind / front, then put the composition in LIVE mode so the engine ticks the graph against real input.
"""
