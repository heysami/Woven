## Logic Graph authoring - the map

You are building an INTERACTIVE app node (camera / hand / face detection, pointer or touch or scroll or gyro or audio reactive behaviour, shapes drawn from tracked points, physics you can push with input, effects that react). Build it as a LOGIC GRAPH: typed input nodes feeding processors and operators, whose outputs drive a composer's layer / position / effect params or a `shape` node's points. Build the graph the same way you build any node graph: commit nodes with `addNodes` and wire them with edges. Execution only runs in LIVE mode (the composer's Live / mm:logic-run toggle); in edit mode the graph is inert.

This guide is MODULAR. This index is the always-on summary; fetch a focused section on demand instead of guessing or reading the composer source. You should NEVER need to read mmcomposer/app.js or the composer index.html to learn what the runtime can do - the `runtime` section below documents every position mode, effect type, force, the camera/detector, and feedback. Fetch it.

### Build flow

1. IDENTIFY INPUTS. Map each driver in the request to a source kind (pointer / touch / keyboard / scroll / gyro / audio / camera / video, plus vision-detect / vision-ocr off a camera stream). See `dataflow` + `catalogue`.
2. PICK PROCESSORS. Smooth raw values through `state-smooth`, remap ranges with `op-map`, combine / threshold / branch / accumulate with the operators, control-flow, and state nodes. See `catalogue` + `patterns`.
3. CHOOSE OUTPUTS / TARGETS. Drive a composer's `position` / `effect` params, or a `shape` node's points, or place text with `type-motion`. Pick the position mode + effect type + force from `runtime`.
4. WIRE + LIVE. Place the composer (mm-composer / composer), wire every layer / shape `out` into its `in`, set z-order for behind / front, then put the composition in LIVE mode so the engine ticks the graph against real input.
5. VERIFY. Bake the composer node, then run the visual QA. See `verify`.

### MANDATORY verify

Building the graph is not the same as the effect happening. After you build + bake, you MUST run `GET $TH_DAEMON_URL/__qa/run?project=$TH_PROJECT_ID&node=<composerNodeId>` and only tell the user it is done when the verdict is `pass`. Never judge a capability by reading a baked .html or the runtime source. Details in the `verify` section.

### Sections (fetch on demand)

Each is `GET $TH_DAEMON_URL/__logic_guide?section=<name>&project=$TH_PROJECT_ID`:

- `dataflow` - nodes / edges / dtypes / compatibility, and how an output reaches a target (param bindings, shape points, paramout read-back). Read this first.
- `catalogue` - the node-kind quick reference: sources, processors, literals, operators, control-flow, state, render (shape, type-motion), and the `force` node, with every port + dtype.
- `runtime` - the composer runtime surface: every position mode, every effect type, the shared physics world + force types + collision, the camera / detector, and feedback. This is what stops the source-spelunking. Fetch it before picking a mode / effect / force.
- `patterns` - the reusable composition idioms (remap, smooth, gate, presence-threshold, vision-to-shape, distance / gesture, z-order, physics interactivity, text).
- `recipes` - four copy-pasteable end-to-end recipes (node list + controls + every edge).
- `verify` - the visual-QA protocol + hard rules. MANDATORY before claiming success.
