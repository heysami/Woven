## Composer runtime surface (the design-library for app-nodes)

This is the authoritative reference for what the mm-composer runtime actually does at run time: every `position` mode, every `effect` type, the shared physics world + forces, the camera / detector, and feedback. Use this instead of reading the composer source. Names + param ranges below are verified against SPEC_SOURCE_TEMPLATES + SPEC_NODE_DEFS in app.js. Params are wired by binding a logic output into `position.param:<name>` / `effect.param:<name>` (NUMBER controls only; see `dataflow`).

A composer LAYER is: content (an asset / camera / video / a wired position+effect output) placed by ONE position mode, with a stack of effects, a blend mode, an opacity, a z, and a feedback amount. Layers sort ascending by z (lower z paints behind). Drive a layer by driving the `position` / `effect` node wired into it (layers have no param ports).

### Position modes (the `position` node, control `mode`)

15 modes. "params" lists each mode's authored controls (name: default, range, meaning). The numeric ones are bindable as `position.param:<name>`.

- `single` - place ONE instance. params: x (0, -5000..5000, px offset), y (0, same), scale (1, 0.01..10), rotation (0, -360..360 deg), rotateX / rotateY (0, -180..180 deg, 3D tilt), rotateZ (0, -360..360). Use for a single layer you transform. Bind x/y/scale/rotation to drive it live.
- `grid` - tile instances in a cols x rows grid. params: cols (20, 1..200), rows (20, 1..200), spanCols / spanRows (1, cell span), gap (0, 0..120 px), placement (fixed|random), fit (contain|cover|fill|none), alignX (left|center|right), alignY (top|center|bottom), tile (bool), shiftX / shiftY (0, -1000..1000), rotation + rotateX/Y/Z. Use for repeated-content mosaics / contact sheets.
- `instances` - scatter N instances from a seed point (phyllotaxis spiral). params: source (mouse|random|interaction, the seed), count (24, 1..2000), jitter (0.25, 0..1, spread), physics (bool - hand off to the world). NOT a physics body unless physics=true. Use for sprinkles / particle bursts that follow the mouse.
- `physics` (template label "Physics / gravity", mode value `physics`) - N circle bodies (radius from size) fall + bounce + COLLIDE in the shared world. params: gravity (980, -2000..2000, downward pull; pushed to the shared world), bounce (0.55, 0..1, restitution). 3 static walls contain them. Use for falling / piling objects. gotcha: ONE shared world gravity, last writer wins across physics+shatter layers.
- `shatter` - voronoi-fracture the layer into N rigid shards that fly apart on a trigger then fall under gravity. params: count (24, 2..160 shards), gravity (1.4, -3..3), burst (0.04, 0..0.2, initial fling), spin (0.4, 0..3, tumble), slowmo (1, 0.05..2, time scale), period (3, 0.5..12 s, auto re-burst interval), trigger (text "click", what fires the burst). Shards tile the image at rest. Use for "image explodes on click."
- `boids` - N flocking agents (Reynolds separation / alignment / cohesion), gravity-cancelled (they fly). params: count (60, 1..600), separation (1, 0..4), alignment (1, 0..4), cohesion (1, 0..4), perception (0.12, 0.01..0.6, neighbour radius), maxSpeed (0.35, 0.01..2), size (0.05, 0.005..0.3). Collidable + force-reactive in the shared world. Use for swarms / schools.
- `drawn` - place instances along an author-typed polyline. params: paths (text "0,0 120,40 240,0"; multiple paths separated by `|`), closed (bool). Use for content following a fixed hand-drawn path.
- `text-ink` - sample a string's ink into an UNORDERED point cloud (one instance per point). params: text ("INK"), font ("sans-serif"), weight (700, 100..900), density (200, 1..800, point count), jitter (0, 0..1), drift (0, 0..2, drift speed), size (0.02, 0.005..0.2). Pair drift>0 with layer feedback for letter-disintegration. Cached by text/font/weight/density/WxH (not re-sampled per frame).
- `text-outline` - ORDERED contour points of the glyphs (marching-squares trace + RDP simplify), each with a tangent rot. params: text ("INK"), font, weight (700), density (120, 3..800, points per contour), simplify (0.6, 0..4, RDP epsilon), size (0.02). Use for content running ALONG letter outlines / stroke reveals. Ordered, unlike text-ink.
- `rope` - a hanging chain of `segments+1` bodies, node 0 pinned, stiff distance constraints; hangs + swings under shared gravity. params: anchors (text "0,0 300,0", pin points), segments (12, 2..128), stiffness (0.72, 0..1). The free end NO LONGER follows the mouse automatically - wire a `force` for that. Use for chains / vines / strands.
- `rope-ink` - one short verlet rope per glyph-ink anchor (node 0 pinned to the ink point); a curtain of letters. params: text ("INK"), font, weight (700), anchors (40, 1..300, ropes), segments (6, 1..24, per rope), gravity (1, 0..3), stiffness (0.8, 0.05..1), damping (0.99, 0.8..1), size (0.02). Use for "a curtain of letters you can drag" (wire a force into pos).
- `camera-feed` - place instances AT detected landmarks (NOT the visible feed). params: detector (hand|face|object|ocr), source (text "camera"), confidence (0.6, 0..1, min). gotcha: this does NOT paint the webcam - for the visible feed wire `input-camera.layer` into the composer. Use for "stickers pinned to fingertips / face."
- `grid-3d` - a cols x rows x layers 3D lattice. params: cols (4, 1..48), rows (4), layers (3, depth slabs), spacing (1, 0.01..100), rotateX/Y/Z. Use for volumetric grids.
- `scatter-3d` - N points scattered in a 3D box. params: count (80, 1..10000), boundsX / boundsY / boundsZ (6, 0.01..1000, box size), rotateX/Y/Z. Use for 3D point fields / starfields.
- `surface` - project instances onto a referenced mesh surface. params: meshId (text, the mesh), density (0.5, 0..1), offset (0, -100..100, along normal). Use when you have a mesh to scatter content over. (Niche; needs a meshId.)

### Effect types (the `effect` node, control `type`; every effect also has `intensity` 0..1)

18 types. Bind `effect.param:intensity` (universal) or a per-type numeric param. An effect wired into a generic `layer` node's `in` applies to THAT layer only; wired into the composer top-level (`comp.in`) it applies to the WHOLE frame. CAVEAT: a wired CAMERA / SHAPE / Kinetic-Type layer IGNORES effects you wire toward it (it always synthesizes with an empty effect stack, and `input-camera` has no `in` port to begin with) - add its effect in the composer inspector's Effects accordion instead. To confine an effect to a REGION (e.g. only inside a polygon) you need a layer MASK - see "Masking + region-confined effects" below.

- `chromatic-aberration` - RGB split. params: amount (0.01, 0..0.1), angle (0, -180..180 deg). Glitchy fringe.
- `directional-blur` - motion blur along an angle. params: length (0.02, 0..0.2), angle (0, -180..180 deg).
- `displacement` - warp by a noise field. params: scale (0.03, 0..0.3). Liquid / heat-haze.
- `slice` - horizontal/vertical slice-shift glitch. params: count (16, 1..128 slices), offset (0.1, 0..0.5), vertical (bool). Reads as glitchy.
- `pixelate` - blocky downsample. params: size (8, 1..120, block px). Bind size for a reveal.
- `dither` - ordered-dither to N levels. params: levels (4, 2..16).
- `posterize` - quantize color to N levels. params: levels (5, 2..32).
- `pixel-sort` - sort pixels above a threshold. params: threshold (0.5, 0..1), vertical (bool). Reads as glitchy.
- `ascii` - render as ASCII cells. params: cell (8, 2..48 px).
- `crt` - scanline + curvature + vignette CRT look. params: scanline (0.6, 0..1), curvature (0.15, 0..0.6), vignette (0.4, 0..1). Reads as retro / glitchy.
- `halftone` - print halftone dots. params: cell (8, 2..48), angle (15, -90..90 deg).
- `ink` - threshold to ink levels (woodcut). params: threshold (0.25, 0..1), levels (4, 2..16).
- `edge-detect` - Sobel edges. params: none (intensity only).
- `particle-grid` - dissolve into a drifting particle grid. params: cell (12, 2..64), drift (0, 0..1).
- `pattern` - overlay a procedural pattern. params: scale (12, 1..64), mix (0.5, 0..1).
- `fluid` - REAL-TIME Stam stable-fluids (GPU, CPU fallback). The layer pixels are the dye; the pointer injects velocity + dye. params: viscosity (0.2, 0..1), force (1, 0..4, injection strength), fade (0.04, 0..0.5, dye decay), radius (0.12, 0.02..0.5, injection radius), grid (128, 16..512, solver grid), iterations (24, 1..60, pressure solve; GPU only), curl (0, 0..50, vorticity / swirl; GPU only). Use for interactive smoke / ink / fluid.
- `face-morph` - parametric facial-landmark mesh warp (CPU, FaceLandmarker; still image OR throttled camera/video). params: amount (1, 0..2), smile (0, -1..1), browRaise (-1..1), eyeWiden (-1..1), jawDrop (0..1), cheekPuff (0..1), headTilt (-1..1), track (bool, exaggerate live expression), source (auto|image|camera). Fails soft to no warp if no face. Use for expression puppeteering.
- `custom` (template "Custom shader effect") - your own GLSL fragment. controls: intensity, plus author-defined params; write `fragmentShader(values)` returning the body (friendly aliases tex / uv / uRes / o; runtime supplies the #version header). Use when no built-in fits.

There is NO effect literally named "glitch" - use `slice`, `pixel-sort`, or `crt`, which read as glitchy.

### Masking + region-confined effects (one layer masked by another)

A layer can be MASKED by another layer's pixels: the mask layer's chosen channel multiplies a channel of the masked layer, so the masked layer only shows where the mask has coverage. This is the ONLY way to confine content or an effect to a REGION (e.g. "glitch only inside the polygon", "video only inside the circle"). Fields on the masked layer: `by` (id of the layer read as the mask; "" = no mask), `src` (channel READ off the mask layer: lum|alpha|r|g|b; lum = luminance x the mask's own alpha), `dst` (channel of THIS layer to multiply: alpha|r|g|b|rgb; alpha is the usual "clip to the mask shape"). The mask layer can be hidden (visible=false) and still drive - mask sources render in a pre-pass.

IMPORTANT - what you WIRE vs what you set in the COMPOSER inspector:
- The mask binding has NO node port. You CANNOT wire "shape masks layer" as an edge. Set it in the composer node's inspector: select the layer to be masked, open its Mask accordion, set "Masked by" to the mask layer and pick src/dst. It persists with the composer (STATE.wiredMasks).
- The mask layer needs COVERAGE in the channel you read. A `shape` with `fill=""` (stroke only) masks just along the outline. For "fill the region" give the shape a solid `fill` (e.g. "#ffffff") so its interior has alpha/luminance; keep a second stroked shape on top if you also want a visible border.
- Per-layer effects on a wired camera/shape/type layer are ALSO inspector-only (see the effect note above). So a region-confined effect is: WIRE the skeleton (layers + the shape's live points), then in the composer add the effect to the target layer's stack AND set its "Masked by". This last step is not expressible as edges - do it in the composer, or hand it to the user as the finishing step.

Worked example - "glitchy face inside a fingertip polygon":
  Wire (skeleton): `input-camera.layer -> comp.in` (z 0, the plain face behind); `input-camera.layer -> comp.in` a SECOND time (z 10, the copy to be glitched + clipped); `cam.stream -> vision-detect(hand)`; the fingertips -> a FILLED `shape` (closed, fill="#ffffff", z 20) `.p0..p4`; `shape.out -> comp.in`.
  Then in the composer inspector: (1) add a `slice` (or pixel-sort / crt) effect to the SECOND camera layer's Effects stack; (2) set that layer's Mask "Masked by" = the shape layer (src=alpha, dst=alpha); (3) hide the shape layer, or drop its fill and keep a thin stroke for a visible border. Result: the top camera copy is glitched and clipped to the polygon, over the untouched face.
  The pure-wiring shortcut (NOT confined to the polygon): `effect.out -> comp.in` glitches the entire composite - simpler, but the polygon then does nothing to it.

### The shared physics world + forces

The composer has ONE shared Matter.js world per instance. EVERY physics object (`physics`/gravity, `shatter`, `rope`, `rope-ink`, `boids`) lives in it, so they COLLIDE with each other AND react to wired `force` nodes. Stepping is a fixed-timestep accumulator (capped substeps). Body cap is 3000 total. All jitter is seeded (deterministic).

Collision: categories DEFAULT / ROPE / BOIDS / WALL, all with mask 0xFFFF, so EVERYTHING collides with everything. The only suppression is intra-rope: each rope chain gets a unique negative collision group so its own segments pass through each other while still hitting every other object.

The `force` node is the ONLY way to make physics interactive. It is a sink: wire a vector2 into its `pos` and the composer applies the field each frame to all bodies within `radius` (normalized, scaled by max(W,H)). `pos` is NEVER hardcoded to the mouse - any vector2 source works. controls: type, radius, strength (can be negative to invert), falloff (edge softness; fall = pow(1 - dist/radius, falloff), 1 at center, 0 at edge).

Force types:
- `attract` - pull bodies toward `pos`, magnitude strength * fall.
- `repel` - push bodies away from `pos`.
- `vortex` - tangential (perpendicular) force + slight inward pull = a swirl.
- `drag` - scale body velocity down near `pos` (thickens the medium there).
- `wind` - NO center; `pos` is read as a DIRECTION (heading from center 0.5,0.5) applied as a constant push to every dynamic body.

With NO force wired, the world runs its defaults: ropes hang + swing, boids flock, shatter shatters - now collidable and force-ready. Do NOT claim the composer cannot do interactive physics. Example: `input-pointer.pos -> force(attract).pos` drags a rope-ink curtain toward the mouse; `vision-detect.indexTip -> force(repel).pos` lets a hand push particles away.

### Camera + detector

`input-camera` provides two distinct things:
- `layer` (dtype layer) - the LIVE webcam as a real composer layer (content.kind camera). Wire it into a composer `in` (low z) to SHOW the feed; the per-layer effect stack + feedback apply on top. This is how you put the live camera behind something. (The Camera chip in the composer toolbar also toggles the webcam on and adds this feed layer.)
- `stream` (dtype string) - the detection feed. Wire it into `vision-detect.stream` (face|hand|object) or `vision-ocr.stream`. vision-detect emits present / count / pos / region / gesture / confidence plus per-landmark vector2 points (hand: wrist, thumbTip, indexTip, middleTip, ringTip, pinkyTip; face: nose, leftEye, rightEye). Feed those landmarks into a `shape` (p0..p7) or a `force.pos`.

The `camera-feed` POSITION mode is a different thing: it places instances AT landmarks, it does NOT paint the feed. For the visible feed always use `input-camera.layer`.

HAND CAVEAT: vision-detect emits the PRIMARY detection's landmarks only, and `target` is present|count|location|gesture (there is NO left/right hand selector). With two hands in frame, two vision-detect(hand) nodes both read the SAME primary hand - you cannot build a polygon spanning the left hand AND the right hand from two nodes. Build a fingertip polygon from ONE hand's five points (thumbTip, indexTip, middleTip, ringTip, pinkyTip).

### Feedback (per-layer trail)

Every layer (and type-motion) has a `feedback` control (0..1). 0 = clear the layer buffer each frame (default). >0 = fade the PRIOR buffer by (1 - feedback) instead of clearing, so previous frames decay into a trail; feedback=1 never fades. Pair feedback>0 with a moving / drifting position mode (e.g. text-ink drift, boids, physics) for motion trails and disintegration looks.

### Text guidance

To put TEXT in the composer use `type-motion` (Kinetic Type, per-glyph animated, drawn straight to canvas) or a `layer` with `text` content (static), or the text-driven position modes (`text-ink` / `rope-ink` / `text-outline`) for letters-as-particles / ropes / outlines. Do NOT use a `formatted-text` (HTML) node as composer layer content: HTML cannot draw to a canvas directly, so the composer would have to rasterize it with html2canvas (refresh lag, same-origin only). Reserve `formatted-text` for rich static HTML OUTSIDE the live composer.

### Live mode + bake

The graph only ticks in LIVE mode (the composer's Live / mm:logic-run toggle: `LogicBridge.setLive(playing && logicRun)`). In edit mode the graph is inert. BAKE the composer node to produce the standalone runtime (the slimPlayer carries a faithful physics-world twin, so editor preview and the baked player behave identically), then run the visual QA (see `verify`).
