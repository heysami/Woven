# Canvas audit repairs

Implemented against the 2026-09-24 Woven canvas audit. This records code changes and targeted evidence, not a certification of every editor feature.

| Finding | Repair | Verification |
|---|---|---|
| F01 | One JSON-compatible catalogue, `editor/kinds/logic_nodes.js`, supplies the canvas and all 51 server contracts, named ports, controls, canonical JS/JSON paths, and agent edit destinations. | Every kind validates and resolves an agent edit destination. |
| F02 | Scaffold instructions use `/__workflow/nodes/add` with `addNodes` and `addEdges`; existing spec changes use node status and canonical modules. Commit rejects ignored graph operations and duplicate update attempts. | Execute the documented triangle scaffold, check actual ports, update and commit slots using production handlers. |
| F03 | Both agent playbooks, canvas routing, and capability guidance restrict project agents to project-local specs, custom effects, and sketches. Missing shared-engine capabilities require separate maintenance authorization. | Instruction review. |
| F04 | Capture frames forward gamepad, accelerometer, and MIDI values through tick. | Synthetic device capture through graph-bound outputs. |
| F05 | Per-node pointer/button/coordinate, touch limit/coordinate, scroll unit/clamp, keyboard repeat, gyro smoothing, and audio analyser settings. | Capture-to-tick tests with differently configured nodes; real browser pointer and audio checks. |
| F06 | Audio asset mode decodes the connected file into its own analyser; microphone nodes share device capture with separate analysers. | Deterministic 440 Hz WAV produces level, pitch, and band outputs with zero microphone calls. |
| F07 | Video.asset reaches layer content; the real per-node video is used for rendering and vision; loop/autoplay are honored. | Actual resolver test and browser-generated video decode/playback/stream test. |
| F08 | Vector Scale reads declared v/t ports, retaining legacy a/s compatibility. | All six vector modes checked against declared ports. |
| F09 | N-frame delay returns zero during warm-up and then the sample from exactly N ticks ago. | Ramp and impulse sequences for N=1,2,3. |
| F10 | Feedback state reads precede graph evaluation; state writes follow it. Pure self-loops are rejected. | Accumulating delay feedback in both node orders, latch retention, and cycle rejection. |
| F11 | Detection results are keyed by stream and detector type. | Face and hand results remain independent on one synthetic camera stream. |
| F12 | Live and baked legacy camera-feed/face-3d positioning call the same landmark implementation. Procedural face substitution is removed. | Shared landmark output and empty-detection tests; browser export loads the shared module. |
| F13 | Each composer projects its upstream graph. Force/audio sinks use an explicit ownership wire or composerId. | Two-composer test isolates inputs, forces, sound, sockets, and orphan sinks. |
| F14 | Bakes embed shared ESM dependencies and local media, including HTML raster support and linked HTML styles/images. Missing dependencies fail the bake. | Playback on empty origins with all external requests blocked; assert pointer outputs, changed triangle pixels, and rendered HTML pixels. |
| F15 | Persistence checks HTTP success before stamping bakedPath/bakedAt. Failed writes surface node errors; QA rejects missing artifacts and errored nodes. | Forced HTTP 500 through real persistence callbacks; production QA resolver checks. |
| F16 | Loop labels and documentation explicitly describe bounded sampling of memoized inputs, without promising subgraph execution. | Catalogue and instruction review; existing bounded-loop checks. |
| F17 | WebSockets retry with capped exponential backoff. Graph replacement and iframe teardown close sockets and abort data requests. | Mock socket retry, URL replacement, and disposal checks. |
| F18 | The served catalogue is generated from the shared definitions. String templates support {v}; dataflow docs list sketch param ports and all layer producers. | Generated catalogue coverage and literal template substitution tests. |

Validated commands:

```sh
node editor/tools/_shared/logicgraph.test.mjs
node editor/tools/_shared/canvas-audit.test.mjs
node editor/tools/_shared/canvas-audit.browser.cjs
PYTHONPATH=editor python3 -m unittest editor.tests.test_canvas_audit -q
PYTHONPATH=editor python3 -m kinds.test_io_contract
PYTHONPATH=editor python3 -m kinds.test_routing
```

Results: original 47 logic checks, 19 audit regression groups, 6 browser integration groups, 6 authoring/handler tests (including all 51 kinds), 6 I/O contract tests, and 2 routing tests pass. JavaScript/Python syntax checks and `git diff --check` also pass.

Rollout: restart the Woven daemon and reload the editor. Mount existing composers to generate fresh bakes. Previously global force/audio nodes must be wired to the owning composer or given an explicit composerId; unowned sinks intentionally do not execute. Pixel input coordinates use the render surface's CSS pixels. FFT size rounds to the nearest WebAudio-supported power of two.

No physical camera, microphone, MIDI, accelerometer, or gamepad was accessed. Device forwarding and detector separation used synthetic data; real face/hand inference, permission behavior across devices, and external provider requests remain unverified. Vision model/CDN resources and explicitly remote media still require network access. The export checks certify the tested linked input/render/media paths, not arbitrary nested applications or every legacy positioning mode.
