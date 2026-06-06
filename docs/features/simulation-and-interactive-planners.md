# Simulation + interactive-media planners

Design plan for two new top-level orchestrating subagents that mirror the existing **visual-planner** (Subagent 1.V) but for radically heavier kinds of artefact: a **simulation-planner** (Subagent 1.S) for apps that need to give the user an intuitive mental model of a real-world physical/temporal system, and an **interactive-media-planner** (Subagent 1.I) for apps whose value is a distinct, surprising, TouchDesigner-flavoured interactive piece.

Both ship in v1 with **full surface area, forked family-specific drawers, and PRD-declared auto-firing**.

## 1. Goals

- **Simulation-planner:** when the PRD declares a `simulation` surface, pick a representation paradigm (iconographic-animation / 2D spatial map / 3D environment / hybrid) based on domain research, then scaffold a multi-trio node graph that produces a runnable simulation embedded in the prototype.
- **Interactive-media-planner:** when the PRD declares an `interactive piece`, pick input modalities (mouse, touch, scroll, mic, camera, gyro, MIDI, gamepad, hand-tracking) × output media (canvas, shader, particles, 3D, audio, haptics), design the input→mapping→output graph, and scaffold a node DAG that produces a single self-contained interactive HTML file.
- **First-class canvas presence:** every artefact each planner produces is a workflow node the user can re-Run, re-prompt, version, and inspect — same canvas affordances as visual-planner's asset trios today.
- **Domain research as a planning input:** unlike visual-planner (which only classifies what already exists in source), both new planners begin with a **research stage** that grounds the paradigm/modality choice in real precedents.
- **No silent escape hatches:** every component the planner scaffolds is wired through a per-medium drawer with a contract — same context-isolation guarantee that keeps visual-planner honest.

## 2. Out of scope

- **A general "any complex thing" planner.** These two planners are specialised because they have distinct triggering criteria and distinct decomposition shapes. We don't add a third generic one.
- **Direct OS/native integrations.** Browser-shipped Web APIs only (MediaDevices, WebAudio, WebMIDI, DeviceOrientationEvent, MediaPipe via CDN). No native bridges.
- **Server-driven simulation/audio.** Both runtimes execute fully in the iframe. No daemon-side simulation loops, no server-side DSP. The user's browser is the substrate.
- **Multi-user / networked interactivity.** v1 is single-user, single-tab. Multiplayer is a future surface and would need its own planner.
- **Mid-run mutation of the graph.** A simulation or interactive runtime can re-render and re-Run, but it can't dynamically add new input streams or new entities on the fly. Adding modalities means re-Running the planner.

## 3. Decision audit (informs scope below)

| Decision | Pick | Implication |
|---|---|---|
| Trigger model | **PRD-declared, auto-fires** | New PRD sections (§9.1) drive Phase 2b/2c of `bp_proto_build`. No new canvas buttons. |
| v1 scope | **Full surface area** | All 4 simulation paradigms + every input/output modality. ~18 new drawer playbooks. |
| Drawer reuse | **Forked, family-specific** | Each family owns its own complete drawer set. No cross-family Task dispatch. Higher maintenance, cleaner context isolation. |

## 4. The five-surface contract (mirrors visual-planner)

Each new planner extends the same 5 surfaces visual-planner extends today. The table is the implementation checklist.

| Surface | Visual-planner today | Simulation-planner (NEW) | Interactive-media-planner (NEW) |
|---|---|---|---|
| **Subagent definition** | `.claude/agents/visual-planner.md` | `.claude/agents/simulation-planner.md` | `.claude/agents/interactive-media-planner.md` |
| **Per-component drawers** | 10 mediums under `.claude/agents/` (`raster-foreground.md`, `shader.md`, etc.) | 8 drawers (see §6.1) | 10 drawers (see §7.1) |
| **Skill registry** | `editor/prompts/media-models.js` — `SKILLS = [...]` | + `sim-runtime`, `sim-entities`, `sim-loop`, `sim-controls`, `sim-overlay` | + `im-input`, `im-mapping`, `im-runtime`, `audio-gen` |
| **Node kinds + per-id overrides** | `editor/kinds/registry.py` — `prompt` / `skill` / `asset` / `agent` | + new kind `simulation` (container); `bp_simulation_build` per-id agent override with `extendsGraph: True` | + new kind `interactive-media` (container); `bp_interactive_build` per-id agent override |
| **Dispatch trigger** | `bp_proto_build` Phase 2 in `node_agent_preambles.py` + `onboarding-visual-policy.md` `IMAGERY_PIPELINE` | `bp_proto_build` Phase 2b + new policy block `SIMULATION_PIPELINE` | `bp_proto_build` Phase 2c + new policy block `INTERACTIVITY_PIPELINE` |
| **Protocol playbook** | `docs/agents/subagents/1V-visual-planner.md` + `1V-*.md` per drawer | `docs/agents/subagents/1S-simulation-planner.md` + `1S-*.md` per drawer | `docs/agents/subagents/1I-interactive-media-planner.md` + `1I-*.md` per drawer |

## 5. Trigger model — PRD-declared, auto-fires

### 5.1 New PRD sections (added to `PRD_VISUAL_RULES` in `onboarding-visual-policy.md`)

Two additive sections, both optional. If absent from the refined PRD, the corresponding planner never fires.

**Simulation surfaces** — markdown table with one row per simulation surface:

| col | example | purpose |
|---|---|---|
| `simId` | `warehouse-floor` | Stable slug used as `assetId` analogue across runs |
| `subject` | "warehouse stock + pick paths" | The physical/temporal system being modelled |
| `paradigmHint` | `2d-spatial-map \| 3d-environment \| iconographic-anim \| any` | Optional steer; `any` lets the research stage decide |
| `entityScale` | "~200 items, ~5 active pickers" | Drives tick rate + render strategy |
| `userIntervention` | "user can re-prioritise pick queue" | Tells controls drawer what to wire |
| `surface` | "Dashboard middle panel, 720×540" | Tells source-writer where the slot lives + sizing |

**Interactive pieces** — markdown table with one row per interactive piece:

| col | example | purpose |
|---|---|---|
| `imId` | `tone-mood-painter` | Stable slug |
| `concept` | "voice + camera control a generative shader" | One-line creative brief |
| `inputs[]` | `["mic", "camera", "mouse"]` | Whitelisted modalities; informs permission UX |
| `outputs[]` | `["shader", "audio-gen"]` | Output media to scaffold |
| `mappingStyle` | `direct \| accumulative \| threshold-triggered \| ml-classified` | Drives mapping drawer |
| `surface` | "Hero, full-bleed 1280×720" | Slot location + sizing |

### 5.2 Source-writer slot conventions

Subagent 1 (source) emits these in the HTML, analogous to today's `<img data-slot="...">` for visual-planner:

```html
<!-- Simulation slot — picked up by simulation-planner -->
<div class="sim-placeholder"
     data-sim="warehouse-floor"
     data-paradigm-hint="2d-spatial-map"
     data-entities="~200"
     style="aspect-ratio: 4/3"></div>

<!-- Interactive-media slot — picked up by interactive-media-planner -->
<div class="im-placeholder"
     data-im="tone-mood-painter"
     data-inputs="mic,camera,mouse"
     data-outputs="shader,audio-gen"
     data-mapping="accumulative"
     style="aspect-ratio: 16/9"></div>
```

These slots are inert until the matching planner runs. The placeholders render as labelled rectangles in the iframe (same convention as `img-placeholder`).

### 5.3 `bp_proto_build` becomes three-phase

Current Phase 1 (source skeleton) + Phase 2 (visual-planner) becomes:

- **Phase 1** — source skeleton with all three slot conventions (img / sim / im) where the PRD declares them.
- **Phase 2a** — visual-planner (unchanged).
- **Phase 2b** — simulation-planner, if the source contains any `sim-placeholder`. Dispatched via Task tool with `subagent_type: "simulation-planner"`, project-root cwd.
- **Phase 2c** — interactive-media-planner, if the source contains any `im-placeholder`.

The three Phase-2 dispatches run **in parallel** — they touch disjoint slot conventions and disjoint asset-id namespaces (visual: `p_*/s_*/a_*`, simulation: `sim_*`, interactive: `im_*`), so no reconciliation is needed across them. The `bp_proto_build` preamble in `node_agent_preambles.py` needs the obvious extension; the constraint that they share `workflow/workflow.json` is handled by the same idempotency rules visual-planner already enforces (only mutate nodes in your own namespace).

### 5.4 The "no signal" case

If the PRD has neither table, neither new planner fires. v1 behaviour for projects without a simulation or interactive piece is identical to today.

## 6. Simulation-planner (Subagent 1.S)

### 6.1 Drawer family

8 forked drawers, all under `.claude/agents/`:

| Drawer | Owns | Pathway |
|---|---|---|
| `sim-paradigm-researcher` | Domain research → paradigm choice. Only drawer in the family with WebSearch + WebFetch. Output: `simulation-plan.json#paradigm`. | A (LLM + web tools) |
| `sim-entity-modeler` | Entity schema (fields, ids, relationships), initial state, derived `data.js` patches. | B (LLM writes JS) |
| `sim-2d-spatial-scene-builder` | The renderer when paradigm is `2d-spatial-map`. Writes a canvas-based or SVG scene. | B |
| `sim-3d-scene-builder` | The renderer when paradigm is `3d-environment`. Three.js scene with OrbitControls + entity layer. | B |
| `sim-iconographic-anim-builder` | The renderer when paradigm is `iconographic-anim`. Lottie or motion-gen-style HTML. | B |
| `sim-loop-author` | The tick/update/event loop. Deterministic time stepping (rAF + accumulator pattern), pause/play, time-scrubbing. | B |
| `sim-controls-author` | DOM event handlers → state mutations. Permission gates if the sim needs them. | B |
| `sim-overlay-author` | Status labels, mini-map, hover cards, legend — SVG/CSS chrome over the scene. | B |

**Why fork** instead of reusing existing `3d` / `lottie` / `canvas-gen` drawers: a simulation 3D scene needs to know about entity state, tick-time bindings, and the loop's event protocol — context the standalone `3d` drawer would never have. Forking keeps each drawer's brief tight.

### 6.2 Node graph scaffolded per `simId`

```
sim_research_<id>     (skill·llm)      — frozen research output, sources cited
   ↓
sim_entities_<id>     (skill·sim-entities)   — entity schema + initial state
   ↓
sim_scene_<id>        (asset; medium picked from paradigm) — the renderer
   ↓
sim_loop_<id>         (skill·sim-loop)       — tick/update loop
   ↓
sim_controls_<id>     (skill·sim-controls)   — input → state
   ↓
sim_overlay_<id>     (skill·sim-overlay)    — chrome
   ↓
sim_<id>              (container, kind="simulation") — bound to the slot
```

Edges connect each step to the next; the `simulation` container node is the asset sink (analogous to today's `asset` node for visual-planner) and is `boundTo` the slot.

### 6.3 `workflow/simulation-plan.json`

Sibling of `workflow/visual-plan.json`:

```jsonc
{
  "generatedAt": "2026-06-06T...",
  "simulations": [
    {
      "id": "warehouse-floor",
      "slot": { "file": "source/main/dashboard.html", "line": 142, "selector": ".sim-placeholder[data-sim=\"warehouse-floor\"]" },
      "paradigm": "2d-spatial-map",
      "paradigmRationale": "Domain research (WMS UIs): top-down floor maps with bin overlays are the canonical mental model...",
      "paradigmCitations": ["https://...", "https://..."],
      "entities": { "schema": "...", "initialState": "..." },
      "tickHz": 4,
      "nodeIds": {
        "research":   "sim_research_warehouse_floor",
        "entities":   "sim_entities_warehouse_floor",
        "scene":      "sim_scene_warehouse_floor",
        "loop":       "sim_loop_warehouse_floor",
        "controls":   "sim_controls_warehouse_floor",
        "overlays":   "sim_overlay_warehouse_floor",
        "container":  "sim_warehouse_floor"
      }
    }
  ]
}
```

### 6.4 New `simulation` node kind

In `editor/kinds/registry.py`:

```python
"simulation": {
    "title":      "Simulation (live iframe)",
    "category":   "container",
    "inputs": {
        "simId":          {"type": "text", "userEditable": False, "required": True},
        "paradigm":       {"type": "enum", "values": ["2d-spatial-map","3d-environment","iconographic-anim","hybrid"], "userEditable": False},
        "exposedAssets":  {"type": "array", "userEditable": False},  # like prototype
        "lockedState":    {"type": "object", "userEditable": False},
    },
    "outputs":     {},
    "outputsRoot": None,
    "consumeFrom": None,
    "dispatch":    "none",
    "extendsGraph": True,
    "graphExtensionScope": "asset children for sim_*_<id> component files",
    "runStatusFlow": ["queued", "done"],
    "completion":  {"requires": []},
    "pauseAfter":  False,
    "notes": "Live iframe of a runnable simulation. User-driven. Run re-builds the runtime by re-dispatching simulation-planner.",
},
```

The renderer mirrors `prototype` — a live iframe in the canvas, with a Run button that re-fires the planner.

### 6.5 New `bp_simulation_build` per-id agent override

Added to `KINDS["agent"]["perIdOverrides"]` in `registry.py`:

```python
"bp_simulation_build": {
    "outputsRoot": "source/{branch}/simulations/{simId}/",
    "extendsGraph": True,
    "graphExtensionScope": "per-simId multi-trio (research/entities/scene/loop/controls/overlays + container)",
    "completion": {"requires": ["files: source/{branch}/simulations/{simId}/runtime.html exists"]},
    "notes": "Dispatches simulation-planner for ONE simId. The planner does the multi-drawer fanout.",
},
```

`bp_proto_build`'s Phase 2b spawns one of these per `simId` in the PRD's simulation table.

### 6.6 New skills in `media-models.js`

```js
{ id: "sim-entities", label: "Simulation entities",  pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "js",   pathwayBSystem: "/* schema author */" },
{ id: "sim-loop",     label: "Simulation loop",      pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "js",   pathwayBSystem: "/* deterministic rAF + accumulator */" },
{ id: "sim-controls", label: "Simulation controls",  pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "js",   pathwayBSystem: "/* DOM events → state mutations */" },
{ id: "sim-overlay",  label: "Simulation overlay",   pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "svg",  pathwayBSystem: "/* chrome over the scene */" },
{ id: "sim-runtime",  label: "Simulation runtime",   pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "html", pathwayBSystem: "/* glue: stage + scene + loop + controls + overlays */" },
```

Each `pathwayBSystem` is a curated multi-paragraph brief like today's `motion-gen` brief, encoding the conventions (no `performance.now()` in scene callbacks; read sim time from a global; reduced-motion gate; etc.).

## 7. Interactive-media-planner (Subagent 1.I)

### 7.1 Drawer family

10 forked drawers, all under `.claude/agents/`:

| Drawer | Owns | Pathway |
|---|---|---|
| `im-modality-researcher` | Survey Web API support, permission UX, reference precedents (TouchDesigner / Cycling '74 / P5 / shader playgrounds). Picks input + output stream set. | A (LLM + web tools) |
| `im-input-mouse-touch` | Pointer events → feature stream (position, velocity, pressure, multi-touch). | B |
| `im-input-mic` | `getUserMedia({audio:true})` + AnalyserNode → FFT, RMS, onset detection. | B |
| `im-input-camera` | `getUserMedia({video:true})` + offscreen canvas → brightness, motion, optional MediaPipe hands. | B |
| `im-input-gyro-orientation` | `DeviceOrientationEvent` + permission flow → tilt/yaw stream. | B |
| `im-input-midi-gamepad` | WebMIDI + Gamepad API streams. | B |
| `im-mapping-author` | Pure-function transforms from input feature vectors to output param vectors. Smoothing, threshold, accumulation, classification. | B |
| `im-output-shader-particle` | Shader + particle-gl output bindings; reads mapping params per frame. | B |
| `im-output-3d` | Three.js scene bindings. | B |
| `im-output-audio` | WebAudio synth/sampler. Includes prefers-reduced-motion analogue (`prefers-reduced-transparency`/UA muted flag). | B |
| `im-runtime-composer` | Final single-file HTML — wires inputs → mapping → outputs, exposes permission-prompt panel, gates Start until permissions resolve. | B |

### 7.2 Node graph scaffolded per `imId`

```
im_research_<id>                     (skill·llm)              — frozen research
   ↓
im_input_<id>_<modality>[]           (skill·im-input)         — one per input modality
       ↘
        im_mapping_<id>              (skill·im-mapping)       — input vec → output vec
       ↗
im_output_<id>_<medium>[]            (skill·im-* output)      — one per output medium
   ↓
im_runtime_<id>                      (skill·im-runtime)       — glue HTML
   ↓
im_<id>                              (container, kind="interactive-media") — bound to the slot
```

Inputs and outputs may both fan out (3 inputs × 2 outputs all wired through one mapping). The container node embeds the runtime in a live iframe.

### 7.3 `workflow/interactive-plan.json`

```jsonc
{
  "generatedAt": "2026-06-06T...",
  "interactives": [
    {
      "id": "tone-mood-painter",
      "slot": { "file": "source/main/index.html", "line": 38, "selector": ".im-placeholder[data-im=\"tone-mood-painter\"]" },
      "concept": "voice + camera control a generative shader; mouse adds local accents",
      "inputs":  ["mic", "camera", "mouse"],
      "outputs": ["shader", "audio-gen"],
      "mappingStyle": "accumulative",
      "permissionGates": ["microphone", "camera"],
      "nodeIds": {
        "research":  "im_research_tone_mood_painter",
        "inputs":    { "mic": "im_input_tone_mood_painter_mic", "camera": "im_input_tone_mood_painter_camera", "mouse": "im_input_tone_mood_painter_mouse" },
        "mapping":   "im_mapping_tone_mood_painter",
        "outputs":   { "shader": "im_output_tone_mood_painter_shader", "audio-gen": "im_output_tone_mood_painter_audio" },
        "runtime":   "im_runtime_tone_mood_painter",
        "container": "im_tone_mood_painter"
      }
    }
  ]
}
```

### 7.4 New `interactive-media` node kind

Mirrors §6.4 but adds a `permissionGates: [...]` field surfaced to the user before Run so the canvas can prompt for camera/mic/gyro consent explicitly (rather than the iframe surprising them).

### 7.5 New `bp_interactive_build` per-id agent override

Same shape as §6.5, dispatching `interactive-media-planner` for one `imId`.

### 7.6 New skills in `media-models.js`

```js
{ id: "im-input",   label: "Input stream",       pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "js",   pathwayBSystem: "/* device → feature vector emitter */" },
{ id: "im-mapping", label: "Input→output map",   pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "js",   pathwayBSystem: "/* pure transforms; smoothing/threshold/accumulation/classification */" },
{ id: "im-runtime", label: "Interactive runtime",pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "html", pathwayBSystem: "/* glue file with permission prompts + Start gate */" },
{ id: "audio-gen",  label: "Audio synth/sampler",pathway: "B", inputs: ["prompt"], output: "image", pathwayBExt: "html", pathwayBSystem: "/* WebAudio synth, reduced-motion analogue gates autoplay */" },
```

## 8. Quality pass — loop-until-bar, multi-lens, holistic

Both planners run a post-build quality pass after all drawers return. This is **not** visual-planner's "auto-retry ONCE" pattern — that's appropriate for raster classification but inadequate for TouchDesigner-grade creative coding. Here the QA is a **loop-until-bar** with multi-lens verification and cross-drawer coherence checks. Drawers may be re-dispatched many times, sometimes with adversarial briefs, until the bar is met or the user accepts an override.

### 8.1 Simulation QA

| Check | What to confirm | Action on fail |
|---|---|---|
| Tick rate sane | The loop's tick rate matches `entityScale` (~200 entities at 4 Hz; ~10 entities at 30 Hz). | Re-dispatch `sim-loop-author` with a corrected hint. |
| Paradigm matches subject | A warehouse stock sim shouldn't be a 3D first-person environment. Read the rendered scene; cross-check against `paradigmRationale`. | Re-Run the planner from the paradigm-research drawer. |
| Controls visible & wired | The `userIntervention` PRD field describes a control; the rendered overlay has it. | Re-dispatch `sim-controls-author`. |
| Initial state is realistic | No empty floors, no all-default values. Entity initial state has variety. | Re-dispatch `sim-entity-modeler`. |
| Embeds in slot | The container loads in the iframe at the slot's CSS aspect. | Edit slot CSS or scene CSS. |

### 8.2 Interactive QA

| Check | What to confirm | Action on fail |
|---|---|---|
| Surprise / responsiveness | The output visibly reacts to the input within ~50ms of action. (Watch the rendered iframe; move the mouse / make a sound; observe.) | Re-dispatch `im-mapping-author` to reduce smoothing. |
| Mapping is non-trivial | Output param vector isn't a 1:1 echo of input — there's transform, accumulation, or threshold logic. | Re-dispatch mapping with explicit "accumulative" / "threshold" hint. |
| Permissions gracefully gated | If mic/camera are inputs, the runtime shows a clear Start button + explanation BEFORE prompting. | Re-dispatch `im-runtime-composer`. |
| Prefers-reduced-motion respected | Heavy animation + audio honour the OS preference. | Re-dispatch the offending output drawer. |
| Output medium fits the concept | A "voice mood painter" shouldn't ship as a static text label. | Re-Run from the modality-research drawer. |

Both pass logs append to `simulation-plan.json#qa` / `interactive-plan.json#qa` — same shape as visual-planner's existing `qa` block.

### 8.3 Loop-until-bar with hard ceiling — runs INSIDE the planner subprocess

Per-asset re-dispatch is **not** capped at 1 (visual-planner's rule). Cap is **5 iterations** per drawer per pass.

**Where the loop runs (truthfulness-critical):** the iteration loop happens INSIDE the planner agent's own subprocess, NOT as multiple canvas nodes. The planner calls `Task(subagent_type: "<drawer>")` up to 5 times, each time re-using the same drawer's `outputsRoot` (the drawer's atomic `/commit` overwrites prior bytes via `outputsRoot_staging/` → rename). Lens verdicts (§8.4) are collected each iteration. Only when ≥2/3 lenses pass does the planner emit its OWN `/commit` flipping the component's `runStatus → done`.

The reconciler's `LYING_STATUS` check (`reconcile.py:_detect_lying_status`) catches "files exist but planner never committed done" — so the truthfulness floor is honest: a half-iterated state shows `runStatus: running`, not `done`. Each iteration's drawer output IS a /commit (it has to be — that's how files reach disk), but the parent planner only marks the *component* node done when the bar is met. See §12.5 for the load-bearing completion contract.

If after 5 iterations the bar still isn't met, the planner emits a `<decision-request>` (via workflow-orchestrator's existing pattern) with three options: **Accept** (waive the failing checks; planner commits done + records waiver in `outputs.qaWaivers[]`), **Push deeper** (more iterations, with a user-supplied steer), **Replace** (swap medium/paradigm and start that drawer over from scratch).

The 5-iteration ceiling is a runaway-loop backstop, not a quality budget. Each drawer dispatch is a fresh `claude` subprocess (§12.2) so it gets its own full 200k input context — there's no token starvation across iterations because each is a new session.

### 8.4 Multi-lens adversarial verify — modeled on the coherence-pass pattern

Each artefact is judged by **three independent lenses** dispatched in parallel after each drawer iteration:

- **Craft lens** — is the code/output well-built? Performance budget, deterministic stepping, error handling, accessibility.
- **Aesthetic lens** — does it look/feel right against the project's committed creative brief (§13.1)? Composition, motion quality, density, palette coherence.
- **Concept lens** — does it deliver the surprise/intuition the PRD asked for? Would the user say "ah, I get it" (simulation) or "whoa" (interactive)?

**Workflow primitive:** each lens is an `agent`-kind per-id override (mirroring the coherence pass's `lint_data_coherence` / `lint_chrome_consistency` / `v_<assetId>` shape in `registry.py`). The three lenses share a single `outputsRoot` that accumulates verdict entries — `source/<branch>/QUALITY_REPORT.json` for simulation; `source/<branch>/QUALITY_REPORT_im.json` for interactive. Verdicts are append-only:

```jsonc
{
  "verdicts": [
    { "iso": "2026-06-06T...", "componentId": "sim_scene_warehouse_floor",
      "iteration": 1, "lens": "craft",     "verdict": "fail",
      "reason": "loop uses performance.now() — breaks deterministic stepping" },
    { "iso": "2026-06-06T...", "componentId": "sim_scene_warehouse_floor",
      "iteration": 1, "lens": "aesthetic", "verdict": "pass" },
    { "iso": "2026-06-06T...", "componentId": "sim_scene_warehouse_floor",
      "iteration": 1, "lens": "concept",   "verdict": "pass" }
  ]
}
```

The planner reads the latest verdict per (component, lens) tuple to decide pass/fail (≥2/3 pass advances). Verdict entries persist across iterations so the audit trail survives. A drawer's output advances only when ≥2/3 lenses pass on the latest iteration.

The lenses are themselves cold-isolated subagents reading only their own playbook (`.claude/agents/craft-lens.md` etc.) + the artefact + the creative brief — no cross-talk between lenses, no shared scratch state. Same divergence guarantee as `iterator-remix` siblings.

**Why model this as canvas nodes** rather than internal-to-planner: verdicts become inspectable. The user can open the QUALITY_REPORT in the canvas asset viewer and see WHY a drawer iterated 4 times. Without canvas presence, this debugging is invisible.

### 8.5 Cross-drawer coherence review (interactive only)

After per-drawer verify, one synthesiser subagent reads ALL drawer outputs together and answers: **does this feel like ONE piece?** It can push any individual drawer back with a coherence brief ("the audio output is bright/glassy but the shader output is warm/painterly — they fight; push the audio toward warmer FM tones"). Same 5-iteration ceiling, same decision-request escalation. Simulation has a lighter version of this — does the loop's tick rate match the scene's apparent fluidity? — but creative coherence is the dominant cost in interactive media, not simulation.

### 8.6 Research is multi-angle, not single-pass

Both `sim-paradigm-researcher` and `im-modality-researcher` are upgraded from single-subagent to **research fleets**: N parallel researchers each scoped to one angle, then a synthesiser drawer that picks/composes.

**Simulation research fleet (4 parallel + 1 synthesiser):**
- `sim-research-precedent` — what shipped products represent this domain, and how? (e.g. WMS UIs, garden sims, traffic dashboards).
- `sim-research-technique` — what rendering/animation techniques fit the entity scale? (canvas vs SVG vs three.js, particles vs sprites, tilemaps vs free placement).
- `sim-research-mental-model` — what cognitive model do real users in this domain already have? Don't fight existing models without reason.
- `sim-research-constraint` — what are the platform/perf/accessibility constraints? (mobile? offline? colour-blind? reduced motion?).
- `sim-research-synthesiser` — reads all four outputs, commits the paradigm + rationale + citations.

**Interactive research fleet (5 parallel + 1 synthesiser):**
- `im-research-precedent` — TouchDesigner / Cycling '74 / Norman White / Casey Reas / Robert Hodgin — reference pieces that hit the concept's vibe.
- `im-research-technique` — Web API capabilities for the proposed inputs, feature-extraction libraries (Meyda for audio, MediaPipe for vision), DSP shapes that fit.
- `im-research-mapping-philosophy` — TouchDesigner-style mapping idioms (direct, accumulative, threshold, ML-classified, chaotic) — pick a mapping shape that EARNS the surprise.
- `im-research-permission-ux` — how shipped interactive sites gate camera/mic permission without breaking the magic on first run.
- `im-research-constraint` — perf budget, accessibility analogues, prefers-reduced-motion mapping, mobile vs desktop trade-offs.
- `im-research-synthesiser` — reads all five, commits inputs + outputs + mapping style + permission flow.

Each researcher in a fleet runs cold-isolated and produces a structured note (cited URLs, specific techniques, named precedents). The synthesiser is the only drawer that sees all of them.

### 8.7 Multi-draft at creative crux points — `iterator-remix` shape, `cp_*_pick` gate

Three steps in each pipeline are CREATIVE CRUXES — single-draft work caps quality. At each crux, the planner spawns **3 parallel drafts** via the existing `iterator-remix` kind, then a **`cp_*_pick` checkpoint agent** (modeled on `cp_remix_pick` / `cp_ds_pick` in `registry.py`) lets the user pick the winner. The unpicked drafts remain as visible canvas cards — same UX as Stage F·Remix today, no new primitive required.

| Family | Crux step (becomes an `iterator-remix`-shaped kind) | n | Divergence axis (per-sibling diverger) | Checkpoint id |
|---|---|---|---|---|
| Simulation | `sim_scene_remix_<id>` | 3 | Camera/composition: top-down vs isometric vs cinematic | `cp_sim_scene_pick_<id>` |
| Simulation | `sim_loop_remix_<id>` | 3 | Pacing: deliberate vs lively vs urgent | `cp_sim_loop_pick_<id>` |
| Interactive | `im_mapping_remix_<id>` | 3 | Mapping shape: direct vs accumulative vs threshold-triggered | `cp_im_mapping_pick_<id>` |
| Interactive | `im_runtime_remix_<id>` | 3 | Onboarding feel: invitational vs instructional vs immediate-immersion | `cp_im_runtime_pick_<id>` |
| Interactive | `im_output_remix_<id>` | 3 | Aesthetic register: painterly vs geometric vs synthetic | `cp_im_output_pick_<id>` |

The crux drawer is wrapped in an `iterator-remix` node (the parent), which spawns 3 cold-isolated sibling subagents (n=3, isolation=cold, parallelism=siblings-parallel, diverger=the axis above). Each sibling writes its output into a separate folder under the parent's `outputsRoot`. The downstream `cp_*_pick` checkpoint agent presents the three to the user (live iframe thumbnails) and commits `DECISION_cp_*_pick.json` with the picked variant id. The next stage's `consumeFrom` rule routes `{picked.outputsRoot}` — same machinery as Stage F → Stage G today.

**Why this is truthful:** the reconciler's `_detect_orphan_variants` already auto-promotes any new variant folder to a sibling card silently (per `reconcile.py:_detect_orphan_variants`). If a drawer fails to produce one of the three drafts, the missing variant is detected. If a user wants to push further and add a 4th draft (variant `d`), they can — the system handles it automatically per Rule 9 of `AGENT_HARNESS.md`.

**Optional pre-gate auto-judge:** before the human checkpoint, an `auto-judge` agent (modeled on the `cp_*` decision agents) reads all three drafts + the creative brief + the lens verdicts and produces a recommendation in the checkpoint's pre-filled value. The user can accept the recommendation in one click or override. The judge is a hint, not the gate — the user always commits the final pick.

## 9. Onboarding-policy additions

### 9.1 `SIMULATION_PIPELINE` block in `onboarding-visual-policy.md`

Quoted by `bp_proto_build`'s preamble after the existing `IMAGERY_PIPELINE` quote. Tells the source-writer to honour the PRD's simulation table by emitting `<div class="sim-placeholder" data-sim="...">` slots, and forbids inline canvas/three.js code in the source for those slots.

### 9.2 `INTERACTIVITY_PIPELINE` block

Same shape, for `<div class="im-placeholder">` slots. Adds an explicit forbiddance on naked `getUserMedia()` calls in source — those go through the planner so the permission UX is consistent.

### 9.3 `PRD_VISUAL_RULES` extended

Adds two new mandatory-when-applicable sections to the PRD spec (already described in §5.1): the simulation table and the interactive-piece table. If the PRD's app concept makes simulations or interactivity load-bearing (PRD prose mentions "intuitive visual of inventory" or "playful interactive piece"), the refiner is REQUIRED to emit the table. Otherwise both tables are absent and neither planner fires.

## 10. File layout summary

After v1, a project that uses both planners gets this on disk:

```
source/<branch>/
├── index.html, dashboard.html, ...      ← source-writer, with sim/im placeholders
├── images/                              ← visual-planner output (unchanged)
├── simulations/
│   └── warehouse-floor/
│       ├── runtime.html                 ← sim-runtime drawer output
│       ├── entities.js                  ← sim-entity-modeler
│       ├── scene.html                   ← sim-{2d|3d|iconographic}-scene-builder
│       ├── loop.js                      ← sim-loop-author
│       ├── controls.js                  ← sim-controls-author
│       └── overlay.svg                  ← sim-overlay-author
└── interactives/
    └── tone-mood-painter/
        ├── runtime.html                 ← im-runtime-composer
        ├── input-mic.js                 ← im-input-mic
        ├── input-camera.js              ← im-input-camera
        ├── input-mouse.js               ← im-input-mouse-touch
        ├── mapping.js                   ← im-mapping-author
        ├── output-shader.html           ← im-output-shader-particle
        └── output-audio.html            ← im-output-audio

workflow/
├── workflow.json                        ← scaffolded nodes from all 3 planners
├── visual-plan.json                     ← visual-planner audit (unchanged)
├── simulation-plan.json                 ← NEW
└── interactive-plan.json                ← NEW
```

## 11. Implementation order

Suggested PR sequence to keep each change reviewable in isolation. **Quality scaffolding (§12 + §13) lands BEFORE drawers** — without the bandwidth + brief + iteration contract, drawers built first would have to be retrofitted.

1. **Skills + kinds skeleton** — add the new SKILLS rows + the `simulation` and `interactive-media` kinds to `media-models.js` + `registry.py`. Add the per-id agent overrides including the §12.2 bandwidth fields (200k input / 100k output / 25min hard / expanded tool surface). Pure plumbing; nothing dispatches yet.
2. **Creative-brief surface (§13)** — extend `bp_research` + `bp_prd_final` preambles in `node_agent_preambles.py` to author `workflow/creative-brief.json`. Make `successFeel` mandatory at PRD validation.
3. **Quality-pass infrastructure (§8 + §12.1)** — author the three lens subagents (`craft-lens`, `aesthetic-lens`, `concept-lens`) + the loop-until-bar harness in the planner playbooks. These are SHARED between simulation + interactive families.
4. **Policy doc + PRD schema** — extend `onboarding-visual-policy.md` with `SIMULATION_PIPELINE` + `INTERACTIVITY_PIPELINE` + the two new PRD table sections (`simId` / `imId` tables PLUS the `successFeel` field per row).
5. **Simulation-planner** — write `.claude/agents/simulation-planner.md` + the 4 research drawers + the synthesiser + 7 component drawers + `docs/agents/subagents/1S-*.md`. Each drawer playbook bakes in §12.1 internal refinement loop. Wire `bp_simulation_build` per-id agent. End-to-end test on a project whose PRD declares one simulation; verify per-lens scores accumulate in `simulation-plan.json#qa`.
6. **Interactive-media-planner** — same, with 5 research drawers + synthesiser + 10 component drawers + permission-prompt UX in the runtime composer. End-to-end test on a project with one interactive piece; verify cross-drawer coherence review (§8.5) actually pushes drawers back.
7. **Phase 2b + 2c in `bp_proto_build`** — extend the per-id preamble so the source-writer dispatches both new planners in parallel with visual-planner after source is written. Plumb the §12.4 user-steerage interrupts into the orchestrator's existing `<decision-request>` machinery.
8. **Canvas renderers** — add the live-iframe renderers for the `simulation` and `interactive-media` kinds in `editor/app.js`. Modelled on the existing `prototype` renderer + devtools toggle (§12.3). Multi-draft losers per §8.7 are already visible as `iterator-remix` sibling cards (no new renderer needed for them — Stage F's renderer covers it).

## 12. Per-drawer execution contract (quality + token bandwidth)

The single biggest difference vs visual-planner: a TouchDesigner-grade creative-coding drawer cannot be a fire-and-forget subprocess. Each drawer in both new families MUST run a multi-turn build-test-refine loop INSIDE its own dispatch, before reporting done. This section codifies the contract every drawer playbook must honour.

### 12.1 Inside-dispatch refinement loop (mandatory)

Every drawer (research drawers excepted) follows this loop within its single dispatch:

1. **Read context** — own playbook, slot brief, project creative brief (§13.1), upstream outputs it depends on, prior version on disk if any. Token budget for reads: up to 50k input tokens — do not skim.
2. **Pull reference material** — at least 2 WebFetch'd references for non-trivial techniques (a shader paper, a TouchDesigner patch, a working CodePen). Cite in the output file's header comment.
3. **Draft v1** — write the artefact.
4. **Self-test** — run it. For HTML/JS artefacts, spin up a preview server via `mcp__Claude_Preview__preview_start` + `preview_eval` + `preview_console_logs` + `preview_screenshot`. For pure JS modules, run a smoke test via Bash + Node. The test is part of the drawer's job, not a downstream lens's.
5. **Self-critique** — write a 5-bullet critique against (craft / aesthetic / concept) lenses (§8.4). If <2 lenses pass, GOTO 6; else GOTO 8.
6. **Refine v2** — apply the critique. If a critique points at a missing reference, GOTO 2 first.
7. **Re-test + re-critique** — repeat 4-5. Cap at 3 internal iterations BEFORE returning (the §8.3 outer 5-iteration cap is on top of this).
8. **Return** — final artefact + critique log + iteration count + per-lens self-scores. The planner uses the self-scores to decide whether to dispatch external lenses or accept the drawer's verdict.

A drawer that returns with <2 internal iterations on a non-trivial brief is failing its contract. Playbooks must state this explicitly.

### 12.2 Token bandwidth + tool surface — properties of the dispatch shape, not registry fields

Woven does not (and should not) expose per-node token-budget knobs in `registry.py`. The bandwidth is a property of HOW the drawer is dispatched, and is honest only when dispatch shape matches the work shape:

| Property | How it's guaranteed | Source of truth |
|---|---|---|
| **Input context window** | Each drawer dispatch is a fresh `claude` subprocess via `Task(subagent_type: "<drawer>")`. Fresh subprocess = fresh 200k context. No "slice of parent context"; full window per call. | The agent kind's `dispatch: "single-subprocess"` contract in `registry.py` |
| **Output budget** | Subprocess runs as long as it needs; no Woven-imposed cap. The §12.1 internal loop can consume the full session. | Same |
| **Wall-clock** | Advisory only. SIGTERM available via `POST /__run/<id>/stop`. Each drawer playbook states a soft target so the planner can decide whether to escalate. | Operational, not enforced |
| **Tool surface** | Declared in the drawer's `.claude/agents/<drawer>.md` frontmatter `tools:` line. THIS IS THE ENFORCEMENT POINT. | `tools:` field, parsed by the agent SDK at dispatch |

**Required `tools:` line for every component drawer in both new families** (the visual-planner drawers don't list preview tools today — these new ones must, otherwise drawers write code blind):

```yaml
tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, mcp__Claude_Preview__preview_start, mcp__Claude_Preview__preview_stop, mcp__Claude_Preview__preview_eval, mcp__Claude_Preview__preview_console_logs, mcp__Claude_Preview__preview_network, mcp__Claude_Preview__preview_screenshot, mcp__Claude_Preview__preview_inspect, mcp__Claude_Preview__preview_snapshot, mcp__Claude_Preview__preview_click, mcp__Claude_Preview__preview_fill, mcp__Claude_Preview__preview_resize
```

Research drawers omit the preview-* tools and add WebFetch/WebSearch only. Lens drawers (§8.4) get Read + the preview-* read-only subset (snapshot, screenshot, inspect, console_logs) — they observe, they don't author.

The token bandwidth is large by virtue of "every drawer = fresh subprocess," not by virtue of a Woven config field. The truthfulness layer doesn't need to know about token budgets; it only needs to verify that the drawer's output files exist and the lens verdicts pass.

### 12.3 Test affordances baked into runtimes

`sim-runtime` and `im-runtime-composer` write self-test scaffolding INTO the runtime, gated behind a dev flag (`?devtools=1` URL param or a corner-pinned overlay):

- **FPS counter** (rolling 1-second avg + 1-frame max).
- **Input-echo overlay** (interactive only): for each declared input modality, a tiny live readout of the current feature vector. Lets the drawer (and the user later) confirm the mic is actually picking up sound, the camera is producing motion deltas, etc.
- **State dump panel** (simulation only): current tick number, entity count, last 10 state transitions.
- **Mapping-graph visualiser** (interactive only): a static SVG showing the input→mapping→output graph with current values flowing through.
- **Permission-status badge** (interactive only): which permissions have been granted, which are pending.

These devtools are how the drawer self-tests in §12.1 step 4. They're also how downstream lenses verify in §8.4. Production renders hide them; the iframe URL the user sees on the canvas omits the dev flag.

### 12.4 Per-component completion contracts (truthfulness floor)

Every per-id agent override declared in `kinds/registry.py` carries `outputsRoot` + `completion.requires` so the validator (`kinds/validate.py:validate_node`) can enforce status:done and the reconciler (`kinds/reconcile.py:_detect_lying_status`) catches lying status automatically. Without this, the quality protocol has no enforcement floor — a drawer could write garbage and mark itself done.

**Node-id convention** (locked in v3.3): `<family>_<component>_<assetId>`. The component goes BEFORE the simId/imId so the wildcard key (`sim_research_`, `sim_scene_`, etc.) can match via the longest-prefix-match rule in `registry.py:kind_contract`. Example: `sim_scene_warehouse_floor` matches the `sim_scene_` wildcard, resolves `{simId}` from `node.simId = "warehouse_floor"`.

**Wildcards LANDED in registry.py** (the table below mirrors what's actually in `KINDS["agent"]["perIdOverrides"]` as of v3.3):

| Wildcard key | outputsRoot | completion.requires |
|---|---|---|
| `sim_research_` | `source/{branch}/simulations/{simId}/research.md` | `files: research.md exists, non-empty` |
| `sim_entities_` | `source/{branch}/simulations/{simId}/entities.js` | `files: entities.js exists, non-empty` |
| `sim_scene_` | `source/{branch}/simulations/{simId}/scene.html` | `files: scene.html exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `sim_loop_` | `source/{branch}/simulations/{simId}/loop.js` | `files: loop.js exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `sim_controls_` | `source/{branch}/simulations/{simId}/controls.js` | `files: controls.js exists, non-empty` |
| `sim_overlay_` | `source/{branch}/simulations/{simId}/overlay.svg` | `files: overlay.svg exists` |
| `sim_runtime_` | `source/{branch}/simulations/{simId}/runtime.html` | `files: runtime.html exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `im_research_` | `source/{branch}/interactives/{imId}/research.md` | `files: research.md exists, non-empty` |
| `im_input_` | `source/{branch}/interactives/{imId}/input-{modality}.js` | `files: input-{modality}.js exists, non-empty` |
| `im_mapping_` | `source/{branch}/interactives/{imId}/mapping.js` | `files: mapping.js exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `im_output_` | `source/{branch}/interactives/{imId}/output-{medium}.html` | `files: output-{medium}.html exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `im_runtime_` | `source/{branch}/interactives/{imId}/runtime.html` | `files: runtime.html exists, non-empty` + `outputs.lensVerdict in {pass}` |
| `craft_lens_` / `aesthetic_lens_` / `concept_lens_` | `source/{branch}/QUALITY_REPORT.json` | `files: QUALITY_REPORT.json exists` + `outputs.verdict in {pass, fail}` |
| `cp_sim_scene_pick_` / `cp_sim_loop_pick_` | `DECISION_cp_sim_<component>_pick_{simId}.json` | exists with non-empty values |
| `cp_im_mapping_pick_` / `cp_im_runtime_pick_` / `cp_im_output_pick_` | `DECISION_cp_im_<component>_pick_{imId}.json` | exists with non-empty values |
| `cp_sim_gate_` / `cp_im_gate_` | `DECISION_cp_<family>_gate_<assetId>.json` | exists with non-empty values |

Exact-match overrides (not wildcards):
- `bp_simulation_build` → outputsRoot `source/{branch}/simulations/{simId}/` + completion requires `runtime.html exists, non-empty` + `outputs.lensVerdict in {pass}`
- `bp_interactive_build` → same shape for interactives

**Container kinds** (new top-level entries in `KINDS`, mirroring `prototype`):

```python
"simulation": {
    "completion": {"requires": [
        "outputs.lensVerdict in {pass}",
        "outputs.iterationCount non-empty",
    ]},
    "extendsGraph": True,
    # see registry.py for the full spec landed in v3.3
},
"interactive-media": { ... },
```

**Template var support** (`validate.py:_resolve_path_template`): extended in v3.3 to know `simId`, `imId`, `modality`, `medium` placeholders. The planner sets these as node fields when scaffolding (e.g. `node.simId = "warehouse_floor"`, `node.modality = "mic"`, `node.medium = "shader"`).

**`outputs.X in {set}` parser** (`validate.py:_check_files_exist`): extended in v3.3 with a ~15 LOC parser branch matching `^(\S+)\s+in\s+\{([^}]*)\}\s*$`. A value not in the allowed set raises `REQUIRED_MISSING`. Backwards-compatible: existing `outputs.X non-empty` requirements unchanged.

**This is the truthfulness floor.** Reconciler surfaces `LYING_STATUS` drift whenever a `sim_scene_*` node claims `runStatus: done` but either the file is missing or `outputs.lensVerdict` isn't `"pass"` — the same machinery that catches `bs_html_*` lying status today.

### 12.5 User steerage between phases (Phase 2b/2c interrupts)

After research-fleet synthesis but BEFORE drafting begins, the planner emits a `<decision-request>` summarising the committed paradigm/modalities + a one-paragraph rationale. The user can:

- **Approve** — proceed.
- **Steer** — supply a one-line nudge ("push more accumulative", "swap iconographic-anim for 2d-spatial"); the planner re-runs the synthesiser with the steer.
- **Reject** — start the research fleet over with a different brief.

A second interrupt fires after the multi-draft judging at each creative crux (§8.7) — the planner shows the winner + 1-line judge rationale + thumbnails of the runners-up; user can accept the winner or pick a runner-up. These two interrupt points are the only ones — drawer-internal iteration doesn't surface to the user unless it escalates per §8.3.

## 13. Project-wide creative brief (the unified vibe)

### 13.1 Where it lives + what it carries

Visual-planner already commits a `styleCue` to `workflow/visual-plan.json` at Step 0. For both new planners — where cold-isolated drawers each write one piece of a SYSTEM that has to feel coherent — the brief needs to be richer than a style cue. Add `workflow/creative-brief.json` at project level, written by `bp_research` / `bp_prd_final` / the orchestrator at the start of Phase 2:

```jsonc
{
  "styleCue":         "warm watercolour wizard study, soft graphite + ochre wash, Studio Ghibli memory",
  "interactionPhilosophy": "calm, responsive within 50ms, the user's actions accumulate rather than overwrite",
  "sensoryTargets": {
    "visual":  "painterly · varied · 12fps feels right, 60fps feels wrong",
    "motion":  "slow acceleration, soft easing, no bounce, no spring",
    "audio":   "warm FM, low-passed, no synthetic transients",
    "haptic":  "no haptic"
  },
  "antiPatterns": ["bright tabler chevrons", "ios-rendered emoji", "linear/snappy easing", "default white-noise hiss"],
  "references": ["https://...","https://..."],
  "successFeel": "a one-paragraph description of what 'this hit the bar' looks like — written from the user's POV"
}
```

**EVERY drawer dispatch in both new families is given the entire creative brief verbatim as the first input.** Not paraphrased, not summarised. Drawer playbooks include "FAIL CLOSED" guidance: if your output violates an `antiPattern`, that's an automatic re-draft trigger inside your own refinement loop. This is the unified-vibe enforcement mechanism for cold-isolated drawers.

### 13.2 The `successFeel` field is load-bearing

`successFeel` is what the §8.4 concept lens scores against. It's prose, not metrics — the lens reads the runtime and asks "does this match the prose?" Writing a vague `successFeel` produces vague QA. The PRD refiner is required to produce a concrete `successFeel` per simulation/interactive surface before the planner can fire.

## 14. Truthfulness mapping — every quality claim → its workflow-node primitive

Every quality-protocol step in §8 + §12 + §13 is implemented via an existing Woven primitive (or a per-id override of an existing kind). Nothing in this design requires a new dispatch mechanism, a new validator subsystem, or a new reconciler heuristic. The two new top-level kinds (`simulation`, `interactive-media`) are direct clones of the `prototype` kind's contract shape.

| Quality claim | Workflow-node primitive | Where it's already exercised in Woven |
|---|---|---|
| Planner scaffolds multi-trio node graph per simId/imId | `agent` kind with `extendsGraph: True`; planner's `/commit` carries `addNodes` + `addEdges` | `bp_proto_build` / visual-planner do this today (registry.py L169) |
| Each component (scene, loop, controls, runtime, etc.) is a canvas-visible node | `agent` kind per-id override with `outputsRoot` + `completion.requires`; planner adds them via `addNodes` | `bs_html_1/2/3` (registry.py L199-210), `bp_*` overrides |
| Container node embeds a live iframe with Run button + versioning | New kind that mirrors `prototype` (registry.py L668) | `prototype` kind — copy the contract verbatim and rename |
| Multi-draft fan-out at creative cruxes (§8.7) | `iterator-remix` kind (registry.py L524) — N cold-isolated siblings with stated diverger | Stage F·Remix does exactly this today: 3 alts per page |
| User picks the winning draft | `cp_*_pick` checkpoint agent (registry.py L183, L187) — writes `DECISION_*.json`; downstream `consumeFrom: {picked.outputsRoot}` routes the picked variant | `cp_ds_pick` (Stage D pick) and `cp_remix_pick` (Stage F→G pick) |
| 3 parallel quality lenses per drawer iteration (§8.4) | Per-id `agent` overrides that append to a shared `QUALITY_REPORT.json` | Coherence pass: `lint_data_coherence`, `lint_chrome_consistency`, `v_<assetId>` (registry.py L256, L272, L290 — wildcard `v_` prefix override) |
| Final quality gate before status:done | `cp_*_gate` agent that reads the report, commits a clear/block decision, escalates via `<decision-request>` on block | `cp_coherence_gate` (registry.py L309) — exact template |
| User interrupt + decision points (§12.5) | `pauseAfter: True` on STAGES + `<decision-request>` via workflow-orchestrator | Stages D and G pause today; orchestrator already speaks decision-request |
| Reconciler catches "files exist but quality failed" | `validate.py:_check_required_outputs` enforces `outputs.lensVerdict` non-empty; small extension parses `outputs.X in {set}` for membership | `_check_required_outputs` exists (validate.py L176); extension is ~10 LOC |
| Reconciler catches "claimed done but no files" | `reconcile.py:_detect_lying_status` already does this for every kind with `outputsRoot + completion.requires` | Live today (reconcile.py L145) — works automatically the moment new per-id overrides are added |
| Orphan draft folder auto-promoted to a canvas card | `reconcile.py:_detect_orphan_variants` for any kind with `openEnded: True` + `{variant}` in outputsRoot | Live today (reconcile.py L89) — `iterator-remix` is `openEnded: True` so any 4th-draft folder the user adds shows up automatically |
| Subprocess inherits its own fresh 200k context per dispatch (§12.2) | `dispatch: "single-subprocess"` semantics of the `agent` kind | All `bp_*` and `bs_*` agents work this way today |
| Per-drawer tool surface (`mcp__Claude_Preview__*`, WebFetch, etc.) | `.claude/agents/<drawer>.md` frontmatter `tools:` line, parsed at dispatch | Live today — see `visual-planner.md:4` |
| Drawer iteration history visible to user | Each iteration writes to `outputsRoot_staging/` then atomic-rename → `outputsRoot/`; asset-versioning snapshots prior bytes into `workflow/runs/<nodeId>/<vid>/` | Live today — `versioning.py` snapshots every successful producer run automatically |
| User branches off a non-winning draft post-hoc | `POST /__workflow/node/<id>/version/branch` creates a sibling asset node from any prior version | Live today (serve.py L7248) |
| Coherence report inspectable in the canvas | The `QUALITY_REPORT.json` is just an asset node bound to the file path | Live today — `cp_coherence_gate` writes `COHERENCE_REPORT.json` the same way |

**What doesn't exist yet** (and what we'd actually need to add):

1. The three lens agent definitions (`.claude/agents/craft-lens.md`, `aesthetic-lens.md`, `concept-lens.md`) + their per-id agent overrides in `registry.py`.
2. The two new container kinds (`simulation`, `interactive-media`) — pure clones of `prototype` with renamed fields.
3. The per-id agent overrides for every drawer (§12.4) — pure data in `registry.py`.
4. The ~10-LOC parser extension in `validate.py` to handle `outputs.X in {set}` membership assertions. Without this, the lens-verdict load-bearing check (§12.4) falls back to "outputs.lensVerdict non-empty" — slightly weaker but still meaningful.
5. The drawer playbook .md files themselves (the prose contracts; same shape as today's `1V-*.md` per-medium drawers under `docs/agents/subagents/`).
6. The two new policy blocks in `onboarding-visual-policy.md` (§9.1, §9.2).
7. The Phase 2b/2c addition in `bp_proto_build`'s preamble (§5.3) — one paragraph extension.
8. The canvas renderers for the two new container kinds in `editor/app.js` (~200 LOC each, modelled on existing `prototype` renderer).

Everything else — fan-out shape, cold isolation, atomic commit, status truthfulness, drift detection, sibling branching, versioning, decision checkpoints, asset rendering, sub-agent dispatch via Task — already exists and is exercised daily by Stage A→J today. We are extending the registry's data, not the engine's machinery.

## 15. Risks + open questions

- **Token cost — accepted, with eyes open.** Drawer count is now larger than initial estimate: simulation = 4 research + 1 synth + 7 component + 3 lenses × per-asset = ~15-25 dispatches per simId; interactive = 5 research + 1 synth + 10 component + 3 lenses × per-asset + 1 coherence = ~25-35 dispatches per imId. Each dispatch is a fresh `claude` subprocess with its own full 200k input context (§12.2). A project with 2 simulations + 2 interactive pieces is firing ~100 subprocesses across onboarding, each potentially consuming its full session window. This is the deliberate cost of "no cutting corner on quality" — the alternative (fewer drawers, no fresh-subprocess isolation, no iteration loop) caps the ceiling at "median creative-coding demo." Mitigation: research-drawer outputs cache per-project (§13 brief once written rarely changes); per-drawer dispatch runs in parallel so wall-clock stays bounded to the slowest drawer + lens chain; the user can stop after the research synthesis interrupt (§12.5) if the paradigm is wrong, paying ~5% of the total before commitment.
- **Wall-clock per drawer.** With §12.1 internal refinement + §12.2 25-min hard cap, a worst-case drawer takes 20-25 minutes. Onboarding's total wall-clock is dominated by the slowest crux drawer in each family, not the sum. Still: a project with a complex interactive piece could see a 30-40-minute build for that piece alone. Surface progress aggressively (per-iteration narration lines, not just final completion).
- **Lens subagents need calibration.** The craft/aesthetic/concept lenses are themselves cold subagents reading playbooks. Their pass/fail thresholds determine how much iteration the system spends. If thresholds are too loose, mediocre drawer output ships; too tight, the system loops 5× per drawer and escalates constantly. Plan: hand-author the lens playbooks against ~10 sample interactive pieces of varied quality (clearly bad, mediocre, good, exceptional) and validate the lenses score them in the right order before shipping.
- **`successFeel` quality is on the human.** §13.2 makes it load-bearing. If the PRD refiner writes a vague `successFeel` ("the user enjoys it"), the concept lens has nothing to push against. We need the PRD-refiner playbook to explicitly demand a concrete success-feel and to fail PRD validation otherwise. Risk that users push back on this requirement — needs UX in the wizard.
- **Permission UX consistency.** Two-stage gating (canvas-side gate before the iframe runs + in-iframe Start) is the conservative path; validated with one real interactive piece before generalising. The §8.4 craft lens explicitly checks permission UX so regressions surface.
- **Multi-paradigm simulations.** `paradigmHint: hybrid` is allowed but not specified — the paradigm-research fleet would need rules for combining (e.g. 2D map + iconographic floating overlays). Punt to a follow-up doc once a real project demands it.
- **Cross-planner reconciliation.** A single slot can only host ONE planner output kind (visual / simulation / interactive). Source-writer picks one slot type per region. Namespace separation (`p_*` vs `sim_*` vs `im_*`) keeps reconciliation clean. A "visual hero that's also interactive" surfaces as `im-placeholder` with `im-output-shader-particle`, not a dual-classified slot.
- **Drawer divergence vs DRY.** The forked-drawers decision means `im-output-shader-particle` and visual-planner's `shader` drawer will drift. Schedule a quarterly diff to keep the curated system prompts in sync where the underlying medium is shared. Drift is the explicit price paid for unbounded per-family quality.
- **Deterministic re-runs for interactives.** A simulation's loop is deterministic by construction (accumulator pattern); an interactive runtime depends on live device input. Versioning snapshots the runtime HTML but not the user's input session. v1 accepts this; future work could record an input trace for replay.
- **5-iteration outer cap may be too low for the hardest interactives.** §8.3 caps at 5 then escalates. For a particularly novel concept the system might need 10+. The Push deeper decision-request lets the user opt into more — but if the user isn't watching, the system stops at 5. Future work: a "deep-build" PRD flag that raises the cap to 15 silently for declared-experimental projects.
