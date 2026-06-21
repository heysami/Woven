## Four worked end-to-end recipes (copy-pasteable: node list + controls + every edge)

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
