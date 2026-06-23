## Logic kind catalogue (quick reference; ports verified against LOGIC_NODE_DEFS)

Format: `kind` [controls] - ports. (i)=input/accept, (o)=output/provides. dtype in parens.

SOURCES (no inputs):
- `input-pointer` [space, button] - (o) x(number) y(number) isDown(boolean) clicked(event) downX(number) downY(number) upX(number) upY(number) hover(boolean) pos(vector2)
- `input-touch` [maxPoints, space] - (o) count(number) pos(vector2) touches(vector2) isDown(boolean) center(vector2) spread(number) pinchDelta(number) rotation(number) tap(event)
- `input-keyboard` [key, repeat] - (o) key(string) isDown(boolean) pressed(event) released(event) axisX(number) axisY(number)
- `input-scroll` [space, clampMin, clampMax] - (o) deltaY(number) deltaX(number) accumY(number) accumX(number) velocity(number)
- `input-gyro` [smoothing] - (o) alpha(number) beta(number) gamma(number) tilt(vector2) ready(boolean)
- `input-audio` [source, band, fftSize, smoothing] - (i) asset(string) - (o) level(number) pitch(number) band(number) beat(event) spectrum(channel) bands(channel). spectrum = 64-bin FFT, bands = 16 log-spaced energies; both channels - sample/reduce with chan-sample/chan-analyze for audio-reactive params.
- `input-camera` [facing, resolution] - (o) stream(string) ready(boolean) layer(layer). The composer CAN render the live webcam: wire the `layer` output into a composer `in` and the feed becomes a real layer (content.kind camera), with the per-layer effect stack + feedback applying on top. The `stream` output feeds vision-detect / vision-ocr. (The Camera chip in the composer toolbar toggles the webcam on/off and adds the feed layer too.)
- `input-video` [loop, autoplay] - (i) asset(string) - (o) stream(string) t(number) playing(boolean)

PROCESSORS (stream in):
- `vision-detect` [detector(face|hand|object), target, hand(primary|leftmost|rightmost|second)] - (i) stream(string) - (o) present(boolean) count(number) pos(vector2) region(region) gesture(string) confidence(number) AND per-landmark vector2: wrist thumbTip indexTip middleTip ringTip pinkyTip (detector=hand), nose leftEye rightEye (detector=face). A missing point degrades to {x:0,y:0}. The `hand` control picks WHICH detection the pos/region/gesture/landmark outputs reflect (default `primary` = first detection). TWO HANDS: run two vision-detect(hand) nodes off the same camera stream, one `hand=leftmost` and one `hand=rightmost`, to address the two hands separately (e.g. a polygon spanning both). count/present stay global regardless of `hand`.
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

CHOP SIGNAL (generators, time-domain operators, and the `channel` dtype - a Float32Array of samples; bridge it to a scalar with chan-sample/chan-analyze, never wire a channel straight into a scalar param):
- `gen-lfo` [wave: sine|tri|saw|square, freq, phase, lo, hi] - (o) value(number) phase(number). Stateless low-frequency oscillator over time, mapped to lo..hi.
- `gen-noise` [speed, seed, lo, hi] - (o) value(number). Smooth 1D value noise over time.
- `gen-clock` [] - (o) time(number) frame(number) fps(number). Wall clock.
- `op-slope` [] - (i) x(number) - (o) slope(number). Derivative (rate of change per second).
- `chop-filter` [mode: low|high, cutoff] - (i) x(number) - (o) value(number). One-pole low/high-pass.
- `state-delay` [frames] - (i) x(number) - (o) value(number). Delay a number by N frames.
- `state-trigger` [attack, decay, sustain, release] - (i) gate(event) - (o) value(number). ADSR envelope 0..1.
- `state-trail` [length] - (i) x(number) - (o) channel(channel). Record a scalar into a rolling channel (a scope / oscilloscope source).
- `chan-sample` [mode: index|phase] - (i) channel(channel) index(number) phase(number) - (o) value(number). Read one sample.
- `chan-analyze` [mode: avg|min|max|rms|sum] - (i) channel(channel) - (o) value(number). Reduce a channel to a number.

PHYSICS (drives the composer's ONE shared physics world; full force model in the `runtime` section):
- `force` [type: attract|repel|vortex|drag|wind, radius, strength, falloff] - (i) pos(vector2) - (o) none. A GENERIC force field injected into the mm-composer's single shared Matter world. EVERY physics object (position modes `physics`/gravity, `shatter`, `rope`, `rope-ink`, `boids`) lives in that ONE world, so they collide with each other AND react to wired forces. The force is NEVER hardcoded to the mouse: wire ANY vector2 into `pos` (input-pointer.pos, input-touch.pos, vision-detect.indexTip, an op-vector output, ...). `force` has no output - just place it and wire its `pos`; the composer enumerates it.

RENDER (a sink, not engine-evaluated):
- `shape` [closed, fill, stroke, strokeWidth, opacity, blend: normal|multiply|screen|overlay, z, smoothing] - (i) p0..p7(vector2), content(layer/asset/effect) - (o) out(layer). Wire `out` into a composer `in`. fill / stroke are CSS color strings (fill blank = no fill). CONTENT FILL + CLIP: wire `input-camera.layer` or an image `asset` into `content` to fill + clip the polygon with that content (a live-video/image polygon, not a flat color); wire an `effect` into `content` too and it runs ONLY inside the polygon. This is the wireable way to confine an effect to a region (e.g. glitchy face inside a fingertip quad) - see runtime "Region-confined effects".
- `type-motion` (Kinetic Type) [text, font, weight, size, color, tracking, align, behavior, speed, amplitude, stagger, path: straight|arc|circle|wave|ring, pathRadius, pathAmplitude, pathRotate, loop, z, opacity, blend, feedback] - (o) out(layer). Per-glyph animated text drawn STRAIGHT to the canvas (no rasterization). 16 behaviors: none, wave, jitter, rotate-cycle, scale-pulse, slot-cycle, fade-stagger, typewriter, fall-gravity, elastic-hop, weightless-float, rainbow-cycle, skew-sway, blur-in, squash-stretch, orbit. This is the PREFERRED way to put TEXT in the composer. Wire `out` into a composer `in`.
- TEXT-DRIVEN position modes on the `position` node (text made of particles / ropes / outlines): `text-ink`, `rope-ink`, `text-outline`. See the `runtime` section for their params.
