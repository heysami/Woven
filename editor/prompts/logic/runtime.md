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

Built-in types are listed below (the originals first, then 22 stackable illustrative shaders). SPEC SHAPE: author an effect as `{ type, intensity (0..1), params:{ ...per-type numeric params... } }` - keep `type` and `intensity` at the TOP level, NOT nested inside `params` (a nested `type` is read as undefined and the effect is silently dropped). Bind `effect.param:intensity` (universal) or a per-type numeric param. An effect wired into a generic `layer` node's `in` - OR into a `shape` node's `content` port - applies to THAT layer only; wired into the composer top-level (`comp.in`) it applies to the WHOLE frame. To confine an effect to a polygon REGION, wire it into a `shape.content` alongside the content to clip - see "Region-confined effects" below.

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

Transform / colour / filter super-nodes:
- `transform` - 2D UV transform. params: tx (0, -1..1), ty (0, -1..1), rot (0, -180..180 deg), scale (1, 0.1..4), wrap (0 clamp / 1 tile / 2 mirror).
- `color` - colour grade. params: brightness (0, -1..1), contrast (1, 0..2), gamma (1, 0.1..4), saturation (1, 0..2), hue (0, 0..1), invert (bool).
- `tonemap` - HDR->LDR tone map. params: mode (0 ACES / 1 Reinhard), exposure (1, 0..4).
- `convolve` - 3x3 kernel. params: mode (0 edge / 1 box-blur / 2 sharpen), amount (1, 0..1).
- `lens-distort` - radial barrel/pincushion. params: amount (0.2, -1..1; >0 barrel, <0 pincushion).

Multi-input effects (read a SECOND wired layer - wire it into the effect's extra input in the composer inspector):
- `displace-by` - warp this layer by a second layer's R/G channels as a signed offset (the displacement map). params: amount (0.05, 0..0.5).
- `blend` - composite this layer with a second layer in a mode. params: mode (0 over / 1 add / 2 multiply / 3 screen / 4 difference / 5 subtract / 6 darken / 7 lighten / 8 overlay / 9 exclusion).
- `matte` - drive this layer's alpha by a channel of a second layer (key). params: channel (0 luma / 1 r / 2 g / 3 b / 4 a), invert (bool).
- `lookup` - grade this layer through a second layer used as a gradient/LUT, indexed by luminance. params: none.

Frame-history effects (read the per-layer ring of recent frames - auto-maintained, no wiring):
- `row-delay` - rolling shutter: each row shows the frame from N frames ago. params: maxDelay (16, 0..60), curve (1, 0.1..8), vertical (bool).
- `cache-select` - echo: show the whole frame from `delay` frames ago (ghost / trail). params: delay (8, 0..60).
- `optical-flow` - per-pixel motion between the current + previous frame, encoded RG (feed into `displace-by`). params: scale (10, 0..50).

- `custom` (template "Custom shader effect") - your own GLSL fragment. controls: intensity, plus author-defined params; write `fragmentShader(values)` returning the body (friendly aliases tex / uv / uRes / o; runtime supplies the #version header). Use when no built-in fits.

#### Illustrative shaders (stackable Figma-shaders / paper-design register)

22 more built-in effects in the shaders.figma.com / paper-design-shaders register. They STACK + blend like every other effect: wire several into one layer's `in` (or the composer's `comp.in`) and they apply in order as that layer's / the frame's effect stack. Two classes: **SOURCES** generate their own field and IGNORE the layer beneath (drop one on a layer / comp at intensity 1 to FILL it; light-emitting ones want a dark base); **FILTERS** transform the pixels beneath. Colour is driven by scalar `hue` / `saturation` / `value` params (0..1) - stack a `gradient-map` or `color` pass on top to force a brand palette. For an exact brand-hex procedural fill in a prototype (not an app node), the `shader` skill + `docs/research/shader-library.md` write richer bespoke GLSL.

SOURCES (generate their own field):
- `mesh-gradient` - animated multi-point colour mesh (premium SaaS backdrop). params: hue (0.6, 0..1), spread (0.3, 0..0.5), speed (0.2, 0..2), value (0.9, 0..1).
- `fractal-noise` - Perlin/value fbm texture (anti-band grain / smoke base). params: scale (3, 0.5..16), speed (0.05, 0..1), hue (0.6, 0..1), saturation (0, 0..1), contrast (1, 0.2..3).
- `clouds` - drifting procedural cloud sky. params: cover (0.5, 0..1), scale (3, 0.5..12), speed (0.02, 0..0.5), hue (0.6, 0..1).
- `nebula` - deep-space gas + twinkling stars. params: hue (0.72, 0..1), density (1.5, 0.2..4), speed (0.01, 0..0.3), stars (0.6, 0..1).
- `glowing-wave` - luminous emitted wave bands. params: hue (0.55, 0..1), frequency (8, 1..40), speed (0.6, 0..3), glow (2, 0.2..6).
- `neuro-noise` - marbled domain-warped fbm ridges (AI-landing texture). params: hue (0.6, 0..1), folds (3, 1..8), scale (2, 0.5..8), speed (0.02, 0..0.3).
- `godrays` - volumetric light shafts from an origin. params: hue (0.12, 0..1), count (14, 2..60), gain (1, 0..3), originX (0.5, 0..1), originY (0.15, 0..1). Additive - needs a dark base.
- `water-caustics` - shimmering refracted-light vein net. params: hue (0.5, 0..1), scale (6, 1..20), sharpness (2, 0.5..6), speed (0.3, 0..2).
- `particle-web` - drifting nodes + proximity web (constellation). params: count (10, 2..30), hue (0.6, 0..1), speed (0.3, 0..2), link (0.6, 0..1).
- `magnetic-field` - curl flow-field filaments (iron filings). params: scale (3, 0.5..10), hue (0.6, 0..1), speed (0.05, 0..0.5), density (40, 5..120).
- `metaball-merge` - gooey blobs that fuse + split. params: count (5, 1..8), hue (0.55, 0..1), speed (0.4, 0..2), threshold (1, 0.3..2).
- `moire-interference` - beating line fields (op-art shimmer). params: frequencyA (40, 5..120), frequencyB (42, 5..120), angle (0.08, 0..1.57 rad), hue (0.6, 0..1), speed (0.02, 0..0.3).
- `concentric-patterns` - nested rings/squares from center. params: frequency (20, 2..80), hue (0.05, 0..1), speed (0.3, 0..2), shape (0 circle / 1 square).
- `dither-waves` - glowing wave quantized through ordered dither (retro CRT). params: hue (0.45, 0..1), frequency (8, 1..40), speed (0.6, 0..3), levels (2, 2..8).

FILTERS (transform the layer beneath):
- `gradient-map` - remap luminance to a hue ramp (duotone). params: hueLow (0.66, 0..1), hueHigh (0.12, 0..1), saturation (0.6, 0..1). The universal palette-unifier - put on TOP of a stack.
- `color-outline` - stacked coloured edge contours (poster line-art). params: threshold (0.2, 0..1), hue (0.6, 0..1), thickness (1, 0.5..4).
- `channel-mixer` - false-colour / duotone. params: mode (1 = swap / 2 = thermal / 3 = sepia / 0 = none, 0..3), amount (1, 0..1).
- `hatching` - cross-hatch engraving from luminance. params: frequency (140, 30..400).
- `pattern-refraction` - refraction through a ribbed pattern (reeded glass). params: frequency (30, 4..120), strength (0.02, 0..0.1), angle (0, 0..1.57 rad), speed (0, 0..2).
- `chromatic-metal` - inflated glossy metal sheen + RGB split (best on shapes / type). params: bands (3, 1..10), aberration (0.01, 0..0.05).
- `bokeh-blur` - depth-of-field blur with highlight-disc bloom. params: radius (0.012, 0..0.06), threshold (0.7, 0..1), bloom (2, 0..6).
- `riso-print` - 2-colour riso re-screen with grain + registration shift. params: cell (6, 2..24), hueA (0.92, 0..1), hueB (0.5, 0..1), registration (0.004, 0..0.02).

There is NO effect literally named "glitch" - use `slice`, `pixel-sort`, or `crt`, which read as glitchy.

### Region-confined effects (clip content + an effect to a polygon)

To confine content OR an effect to a REGION (e.g. "glitchy face only inside the fingertip polygon", "video only inside a circle") the FIRST-CLASS, fully-wireable way is the `shape` node's `content` port:

- Wire a layer-flavored source into `shape.content` to FILL + CLIP the polygon with that content instead of a flat color: `input-camera.layer -> shape.content` (live webcam, mirrored to match the feed) or an image `asset -> shape.content`. The shape's drawn pixels become that content, clipped to the polygon path the `p0..p7` points define.
- Wire an `effect` into `shape.content` too (`glitch.out -> shape.content`) and it runs ONLY on this shape layer's pixels - i.e. ONLY inside the polygon. (`content` is a multi-wire port like `layer.in`: it takes the content source AND the effect.) Bind `effect.param:intensity` as usual for reactive strength.
- This is all EDGES - no composer-inspector step, no second layer, no `mask.by`. The polygon is the clip.

Worked recipe - "glitchy face inside a fingertip polygon" (fully wired):
```
cam   = input-camera
poly  = shape (closed)
glitch= effect (type=slice | pixel-sort | crt)
comp  = mm-composer
cam.stream -> vision-detect(hand)              # detect the hand(s)
<fingertip vector2 ports> -> poly.p0..pN       # the polygon corners
cam.layer  -> comp.in                          # clean camera underneath (z low)
cam.layer  -> poly.content                     # fill the polygon with the camera
glitch.out -> poly.content                     # glitch ONLY inside the polygon
poly.out   -> comp.in                          # the clipped, glitched polygon on top (z high)
```
Result: clean feed everywhere, glitch + distortion confined to the polygon, over the untouched face. (For TWO hands forming the quad, use two vision-detect(hand) nodes with `hand=leftmost` / `hand=rightmost` - see the camera section.)

### Masking one whole layer by another (general, inspector-set)

For masking a NON-shape layer (e.g. clip a video layer to a separate logo's alpha) there is also the layer MASK: a layer's chosen channel is multiplied by another layer's channel. Fields on the masked layer: `by` (id of the mask layer), `src` (channel read off the mask: lum|alpha|r|g|b), `dst` (channel multiplied: alpha|r|g|b|rgb). The mask layer can be `visible:false` (it still renders in a pre-pass). This binding has no node port - set it in the composer node's inspector (the layer's Mask accordion). Prefer the `shape.content` route above for the common "effect inside a polygon" case; reach for `mask.by` only when the mask is a separate non-polygon layer.

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

TWO HANDS: by default vision-detect emits the PRIMARY detection's landmarks (dets[0]). To address two hands separately, set the `hand` control: run two vision-detect(hand) nodes off the SAME camera stream, one `hand=leftmost` and one `hand=rightmost`, and each emits that hand's landmarks - so a polygon can span the left hand AND the right hand (e.g. thumb+index of each forming a quad around the face). `hand` also offers `primary` (default, dets[0]) and `second` (dets[1]). Selection picks by on-screen x, which is self-consistent with the landmark coords a shape/mask reads off the same detection. count/present stay global. (A single-hand polygon from one hand's five fingertips - thumbTip, indexTip, middleTip, ringTip, pinkyTip - is still the simplest option when one hand is enough.)

### Feedback (per-layer trail)

Every layer (and type-motion) has a `feedback` control (0..1). 0 = clear the layer buffer each frame (default). >0 = fade the PRIOR buffer by (1 - feedback) instead of clearing, so previous frames decay into a trail; feedback=1 never fades. Pair feedback>0 with a moving / drifting position mode (e.g. text-ink drift, boids, physics) for motion trails and disintegration looks.

### Text guidance

To put TEXT in the composer use `type-motion` (Kinetic Type, per-glyph animated, drawn straight to canvas) or a `layer` with `text` content (static), or the text-driven position modes (`text-ink` / `rope-ink` / `text-outline`) for letters-as-particles / ropes / outlines. Do NOT use a `formatted-text` (HTML) node as composer layer content: HTML cannot draw to a canvas directly, so the composer would have to rasterize it with html2canvas (refresh lag, same-origin only). Reserve `formatted-text` for rich static HTML OUTSIDE the live composer.

### Live mode + bake

The graph only ticks in LIVE mode (the composer's Live / mm:logic-run toggle: `LogicBridge.setLive(playing && logicRun)`). In edit mode the graph is inert. BAKE the composer node to produce the standalone runtime (the slimPlayer carries a faithful physics-world twin, so editor preview and the baked player behave identically), then run the visual QA (see `verify`).
