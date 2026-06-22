## Four worked end-to-end recipes (copy-pasteable: node list + controls + every edge)

Node ids below are illustrative; pick unique ids. Each recipe ends by wiring into an mm-composer (Interactive composer) and you set Live mode to run it.

RECIPE A - "Camera + hand + fingertip polygon, glitchy camera"
Two HONEST variants - pick by whether the glitch must be CONFINED to the polygon. (The polygon spans ONE hand's fingertips: a single vision-detect(hand) exposes only the primary hand and has no left/right selector - do NOT try to span two hands with two nodes.)
Nodes (both variants):
  - `cam` kind=input-camera (facing=user)
  - `hand` kind=vision-detect (detector=hand, target=location)
  - `poly` kind=shape (closed=true, z=10)
  - `glitch` kind=effect (type=slice  OR  type=pixel-sort  OR  type=crt; there is NO effect literally named "glitch", these read as glitchy)
  - `comp` kind=mm-composer
Shared edges:
  - cam.stream -> hand.stream            (detection feed)
  - hand.thumbTip -> poly.p0 ; hand.indexTip -> poly.p1 ; hand.middleTip -> poly.p2 ; hand.ringTip -> poly.p3 ; hand.pinkyTip -> poly.p4
  - cam.layer -> comp.in                 (the LIVE webcam as a layer)
  - poly.out -> comp.in                  (the polygon, on top)

Variant 1 - WHOLE-FRAME glitch (pure wiring, simplest):
  - glitch.out -> comp.in                (TOP-LEVEL effect: glitches the ENTIRE composite; the polygon is just an outline on top)
  Set poly stroke="#6ee7ff", strokeWidth=3, fill="". The glitch is NOT confined to the polygon - it covers everything. This is the only fully-wireable option.
  Optional reactivity: hand.confidence -> op-map(0..1 -> 0..1) -> glitch.param:intensity (glitch strengthens with detection confidence).

Variant 2 - glitch CONFINED to the polygon (face glitchy only inside the fingertips):
  This needs a layer MASK, which is a COMPOSER-INSPECTOR setting, NOT an edge (there is no mask port; and a wired camera layer ignores wired effects - it has no `in` and synthesizes with an empty effect stack). Wiring gives the skeleton; you finish in the composer.
  - cam.layer -> comp.in   AGAIN (a SECOND camera layer, z above the plain one - this copy gets glitched + clipped)
  - give `poly` a solid FILL (fill="#ffffff") so its interior has coverage; poly.out -> comp.in
  Then in the composer node's inspector: (1) add the `slice` effect to the SECOND camera layer's Effects stack; (2) set that layer's Mask "Masked by" = the poly layer (src=alpha, dst=alpha); (3) hide the poly layer, or drop its fill and keep a thin stroke for a visible outline. See "Masking + region-confined effects" in `runtime`.
  If you cannot reach the inspector programmatically, BUILD the skeleton above and hand the user the two inspector steps as the finish - do NOT silently fall back to Variant 1 and claim the polygon confines the glitch.

NOTE on "the live webcam": the composer renders the live webcam directly - wire `cam.layer` into `comp.in` and the feed shows as a layer. Do NOT claim the composer cannot show a live camera and do NOT build a separate prototype iframe for it - it works natively via the camera layer. (To put a still IMAGE behind instead, use a `layer` with an asset wired in at low z. The `position` mode `camera-feed` is a different thing: it places instances AT detected landmarks, it does not paint the feed - use `cam.layer` for the visible feed.)

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

RECIPE D - "A curtain of letters you can drag with the mouse (interactive physics)"
Nodes:
  - `ptr` kind=input-pointer
  - `pull` kind=force (type=attract, radius=0.35, strength=2, falloff=1)
  - `lay` kind=layer
  - `comp` kind=mm-composer
Layer setup: set the `lay` layer's position mode to `rope-ink` (text="HELLO", anchors ~40, segments ~6). The ink anchors pin the top of each short rope; the rest hangs + swings under the shared world gravity.
Edges:
  - ptr.pos -> pull.pos                   (the mouse position becomes the force center; NOT hardcoded - swap for vision-detect.indexTip to push with a hand)
  - lay.out -> comp.in
Result: the letter-curtain hangs by default; moving the mouse drags the nearby rope nodes toward the pointer (attract). Use type=repel to shove them away, type=vortex to swirl. Add a `gravity` (physics) or `shatter` layer to the SAME composer and its bodies collide with the curtain in the one shared world.
