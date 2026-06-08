"""editor/kinds/registry.py — single source of truth for node-kind contracts.

See WORKFLOW_TRUTHFULNESS_PLAN.md §3. Every per-kind fact (form fields,
output shape, dispatch shape, fan-out, completion criteria) lives here.
The frontend renderer, server-side validator, reconciler drift checks,
and orchestrator preamble all derive from this dict — no parallel
sources of truth.

CRITICAL RULES (from §1 Principles + §4 AGENT_HARNESS):
  • Save is PERMISSIVE — drafts with empty optional fields always succeed.
    "required" in a field spec means required-at-COMMIT, not at save.
  • Commit is STRICT — completion criteria + must-consume rules enforced.
  • Complexity → agent kind (full HTML page, multi-file build, embedded JS).
  • Multiplicity → task-subagents fan-out (siblings-parallel + cold isolation).
  • Folder-as-handoff — producers drop into outputsRoot; consumers route
    everything in the upstream folder per consumeFrom rules.
"""

# ── STAGES — gone in v3.5 (onboarding cut) ──
# The guided pipeline (A through J) was wired to bp_* preambles that no
# longer exist. STAGES is now an empty list, kept only because /__kinds
# legacy clients still read the key. `stage_pause_after` always returns
# False. Both will be removed entirely once no client references remain.
STAGES: list = []


# Common dispatch shapes (for documentation in entries):
#   none                   - no run (folder, prompt, asset, decoration)
#   inline-server-call     - daemon makes an inline LLM call; small text only
#   single-subprocess      - one visible Claude Code session (agent-kind)
#   task-subagents         - parent dispatches N cold-isolated Task subagents
#   client-iterator        - browser-side loop (e.g. iterator-refiner)

# ── Manual-canvas-use guarantee ──────────────────────────────────────────
# A field marked required=True is REQUIRED AT COMMIT, not at save. The only
# fields required at save are the structural ones (id, kind, x, y). This
# preserves the manual-canvas-use principle (#11): drafts with empty
# optional fields always persist.
_EVERYTHING_OPTIONAL_AT_SAVE = True   # invariant constant; do not flip


KINDS = {

    # ── folder ────────────────────────────────────────────────────────────
    "folder": {
        "title":        "Folder / file reader",
        "category":     "container",
        "inputs": {
            "path":  {"type": "text", "label": "Path", "userEditable": True, "required": True},
            "title": {"type": "text", "label": "Display name", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "inline-server-call",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done", "error"],
        "completion":   {"requires": ["inputs.path exists on disk"]},
        "pauseAfter":   False,
        "notes": "Reads a file or lists a directory. Synchronous, no side effects.",
    },

    # ── prompt ────────────────────────────────────────────────────────────
    "prompt": {
        "title":        "Prompt (markdown)",
        "category":     "container",
        "inputs": {
            "text":  {"type": "markdown", "label": "Prompt text", "userEditable": True},
            "auto":  {"type": "bool", "default": False, "userEditable": False,
                      "doc": "When True, text is hydrated from upstream skill/agent output via existing textProjectedFrom projection."},
            "title": {"type": "text", "label": "Title", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},   # prompt may be empty-as-draft
        "pauseAfter":   False,
        "notes": "Static markdown container. When auto=True, text is hydrated from upstream's `output`.",
    },

    # ── skill (LLM, restricted to small text ops) ─────────────────────────
    "skill": {
        "title":        "Skill — small text op",
        "category":     "producer",
        "inputs": {
            "text":     {"type": "markdown", "label": "Prompt template", "userEditable": True},
            "skill":    {"type": "text", "label": "Skill", "default": "llm", "userEditable": False},
            "provider": {"type": "enum", "values": ["anthropic", "openai"], "default": "anthropic", "userEditable": True},
            "model":    {"type": "text", "default": "claude-opus-4-7", "userEditable": True},
        },
        "outputs": {
            "output": {"type": "text", "required": True,
                       "doc": "LLM response text. Downstream consumers read this; the existing serve.py projection wires it into auto-prompts."},
        },
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "inline-server-call",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion":   {"requires": ["outputs.output non-empty"]},
        "pauseAfter":   False,
        "notes": (
            "RESTRICTED to small pure-text transforms: chunking, classification, "
            "normalization, summarization, extraction. Output ≤ ~one structured "
            "payload with no embedded code/files. Anything producing a full HTML "
            "page, multi-file build, or rich self-contained artifact MUST be "
            "agent-kind instead (Principle 4)."
        ),
    },

    # ── agent ─────────────────────────────────────────────────────────────
    "agent": {
        "title":        "Agent — Claude Code subprocess",
        "category":     "producer",
        "inputs": {
            "name":         {"type": "text", "label": "Name", "userEditable": True},
            "systemPreset": {"type": "text", "userEditable": False},
            "preset":       {"type": "text", "userEditable": False},
            "conversation": {"type": "array", "userEditable": False},
        },
        "outputs": {
            "output":   {"type": "text", "required": False},
            "runRunId": {"type": "text", "required": True},
        },
        "outputsRoot":  "source/",     # overridden per per-id
        "consumeFrom":  None,
        "dispatch":     "single-subprocess",
        "fanOut":       None,
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": True},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion":   {"requires": ["subprocess exit_code == 0 OR runStatus posted explicitly"]},
        "pauseAfter":   False,
        "notes": (
            "Spawns a Claude Code subprocess with a per-id system preamble. "
            "Per-id overrides supply preamble text and outputsRoot, and may "
            "set extendsGraph=True for visual-planner-shaped subagents that "
            "scaffold downstream nodes."
        ),
        "perIdOverrides": {
            # ──────────────────────────────────────────────────────────────────
            # v3.5 — Onboarding cut. The guided-new-project pipeline (research,
            # PRD, DS, source-scaffold, brainstorm, coherence-pass, vision-verify)
            # was removed wholesale. The visual / simulation / interactive /
            # narrative planners stay; their drawer overrides + per-id wildcards
            # are below. Chat dispatches planners directly via Path A/B in
            # capabilities.py — no bp_*_build harness intermediary anymore.
            # Wildcard keys end in "_" per kind_contract's longest-prefix-match.
            # Node-id convention: <family>_<component>_<assetId>
            #   sim_scene_warehouse_floor       (NOT sim_warehouse_floor_scene)
            #   im_input_tone_mood_painter_mic  (etc.)
            # ──────────────────────────────────────────────────────────────────

            # ── Simulation component drawers (wildcard prefixes) ──────────────
            "sim_research_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
                "notes": "Synthesised paradigm pick + citations from the 4-researcher fleet.",
            },
            "sim_entities_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/entities.js",
                "completion": {"requires": ["files: entities.js exists, non-empty"]},
                "notes": "Entity schema + initial state. SoT for scene/loop/controls.",
            },
            "sim_scene_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/scene.html",
                "completion": {"requires": [
                    "files: scene.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": "Renderer. Medium picked by paradigm. Lens-gated.",
            },
            "sim_loop_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/loop.js",
                "completion": {"requires": [
                    "files: loop.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Deterministic accumulator tick. Lens-gated on craft "
                    "(no performance.now() in tick callback)."
                ),
            },
            "sim_controls_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/controls.js",
                "completion": {"requires": ["files: controls.js exists, non-empty"]},
                "notes": "DOM events → state mutations.",
            },
            "sim_overlay_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/overlay.svg",
                "completion": {"requires": ["files: overlay.svg exists"]},
                "notes": "Chrome over the scene.",
            },
            "sim_runtime_": {
                "outputsRoot": "source/{prototype}/simulations/{simId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": "Glue. Lens-gated on craft + aesthetic + concept.",
            },

            # ── Interactive component drawers (wildcard prefixes) ─────────────
            "im_research_": {
                "outputsRoot": "source/{prototype}/interactives/{imId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
            },
            "im_input_": {
                "outputsRoot": "source/{prototype}/interactives/{imId}/input-{modality}.js",
                "completion": {"requires": ["files: input-{modality}.js exists, non-empty"]},
                "notes": (
                    "Per-modality input drawer. "
                    "{modality} ∈ {mic, camera, mouse, gyro, midi, gamepad}."
                ),
            },
            "im_mapping_": {
                "outputsRoot": "source/{prototype}/interactives/{imId}/mapping.js",
                "completion": {"requires": [
                    "files: mapping.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Pure-function input→output transforms. Lens-gated on craft "
                    "(no side effects) + aesthetic (non-triviality vs brief)."
                ),
            },
            "im_output_": {
                "outputsRoot": "source/{prototype}/interactives/{imId}/output-{medium}.html",
                "completion": {"requires": [
                    "files: output-{medium}.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Per-medium output drawer. "
                    "{medium} ∈ {shader, particle, 3d, audio}."
                ),
            },
            "im_runtime_": {
                "outputsRoot": "source/{prototype}/interactives/{imId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": "Glue + permission UX. Lens-gated on all three lenses.",
            },

            # ── Lens agents (wildcard — one dispatch per drawer iteration) ────
            "craft_lens_": {
                "outputsRoot": "source/{prototype}/QUALITY_REPORT.json",
                "completion": {"requires": [
                    "files: QUALITY_REPORT.json exists",
                    "outputs.verdict in {pass, fail}",
                ]},
                "notes": (
                    "Code health / perf / deterministic stepping / permission UX. "
                    "Cold-isolated. Appends one verdict to QUALITY_REPORT.json. "
                    "See .claude/agents/craft-lens.md."
                ),
            },
            "aesthetic_lens_": {
                "outputsRoot": "source/{prototype}/QUALITY_REPORT.json",
                "completion": {"requires": [
                    "files: QUALITY_REPORT.json exists",
                    "outputs.verdict in {pass, fail}",
                ]},
                "notes": (
                    "Style coherence vs workflow/creative-brief.json. "
                    "Cold-isolated. See .claude/agents/aesthetic-lens.md."
                ),
            },
            "concept_lens_": {
                "outputsRoot": "source/{prototype}/QUALITY_REPORT.json",
                "completion": {"requires": [
                    "files: QUALITY_REPORT.json exists",
                    "outputs.verdict in {pass, fail}",
                ]},
                "notes": (
                    "Delivers PRD successFeel? Hardest lens; skips cheap "
                    "component kinds with verdict=pass+skipped=true. "
                    "See .claude/agents/concept-lens.md."
                ),
            },

            # ── Multi-draft pick checkpoints (mirror cp_remix_pick) ───────────
            "cp_sim_scene_pick_": {
                "outputsRoot": "DECISION_cp_sim_scene_pick_{simId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sim_scene_pick_{simId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 scene drafts produced by iterator-remix.",
            },
            "cp_sim_loop_pick_": {
                "outputsRoot": "DECISION_cp_sim_loop_pick_{simId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sim_loop_pick_{simId}.json exists with non-empty values",
                ]},
            },
            "cp_im_mapping_pick_": {
                "outputsRoot": "DECISION_cp_im_mapping_pick_{imId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_im_mapping_pick_{imId}.json exists with non-empty values",
                ]},
            },
            "cp_im_runtime_pick_": {
                "outputsRoot": "DECISION_cp_im_runtime_pick_{imId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_im_runtime_pick_{imId}.json exists with non-empty values",
                ]},
            },
            "cp_im_output_pick_": {
                "outputsRoot": "DECISION_cp_im_output_pick_{imId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_im_output_pick_{imId}.json exists with non-empty values",
                ]},
            },

            # ── Family release gates (mirror cp_coherence_gate) ───────────────
            "cp_sim_gate_": {
                "outputsRoot": "DECISION_cp_sim_gate_{simId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sim_gate_{simId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this simId "
                    "are pass, commits value='clear' and releases the simulation "
                    "container. On any block-fail at iteration 5, emits "
                    "<decision-request> with Retry / Patch / Accept-override. "
                    "Direct clone of cp_coherence_gate semantics."
                ),
            },
            "cp_im_gate_": {
                "outputsRoot": "DECISION_cp_im_gate_{imId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_im_gate_{imId}.json exists with non-empty values",
                ]},
                "notes": "Same as cp_sim_gate_ for interactive-media family.",
            },

            # ──────────────────────────────────────────────────────────────────
            # v3.3 — NARRATIVE-EXPERIENCE planner (the poetic cousin of sim).
            # See docs/features/simulation-and-interactive-planners.md
            # (narrative addendum). Mirrors sim's contract shape with three
            # substitutions: spine (scripted timeline) instead of loop,
            # camera (path-driven progression) instead of controls, ambient
            # (soundscape) as a new first-class channel.
            # Node-id convention: nx_<component>_<nxId>
            #   nx_scene_vermeer_studio    (NOT nx_vermeer_studio_scene)
            # ──────────────────────────────────────────────────────────────────

            # ── Narrative component drawers (wildcard prefixes) ───────────────
            "nx_research_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
                "notes": (
                    "Synthesised aesthetic + emotional register + pacing + "
                    "camera idiom + sonic register + spine outline + citations "
                    "from the 5-researcher fleet."
                ),
            },
            "nx_spine_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/spine.js",
                "completion": {"requires": [
                    "files: spine.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Scripted timeline — what's revealed when, by which voice, "
                    "at what depth. Lens-gated on craft (clean module shape) + "
                    "concept (do the beats earn the successFeel)."
                ),
            },
            "nx_scene_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/scene.html",
                "completion": {"requires": [
                    "files: scene.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "three.js / WebGL scene of the 'place'. §8.7 crux — "
                    "3-draft remix on aestheticRegister axis (painterly / "
                    "volumetric / sketch-like). All 3 lenses gate."
                ),
            },
            "nx_ambient_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/ambient.html",
                "completion": {"requires": [
                    "files: ambient.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Soundscape (ambient room-tone + optional voice tracks). "
                    "§8.7 crux — 3-draft remix on sonicRegister axis "
                    "(silence-dominant / room-tone-dominant / voice-led). "
                    "Permission-gated via INTERACTIVITY_PIPELINE pattern "
                    "(canvas-side gate + iframe-side Start)."
                ),
            },
            "nx_reveal_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/reveals.js",
                "completion": {"requires": [
                    "files: reveals.js exists, non-empty",
                ]},
                "notes": (
                    "Gentle interactive accents (hover to brighten, click to "
                    "expand, dwell to deepen). Lightly lens-gated — craft + "
                    "restrained aesthetic (must NOT feel gamey)."
                ),
            },
            "nx_overlay_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/overlay.svg",
                "completion": {"requires": [
                    "files: overlay.svg exists",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Poetic captions / mood text overlaid on the scene at "
                    "spine-driven moments. Lens-gated on aesthetic + concept "
                    "(does the language land the felt-state at each beat?)."
                ),
            },
            "nx_runtime_": {
                "outputsRoot": "source/{prototype}/narratives/{nxId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Glue file — composes scene + camera + ambient + reveals + "
                    "overlay + spine + scroll handling + §12.3 dev harness. "
                    "§8.7 crux — 3-draft remix on pacingFeel axis (slow-bath / "
                    "progressive-reveal / immediate-immersion). Full lens trio "
                    "— this IS the composed user-facing artefact."
                ),
            },

            # ── Multi-draft pick checkpoints (mirror cp_remix_pick) ───────────
            "cp_nx_scene_pick_": {
                "outputsRoot": "DECISION_cp_nx_scene_pick_{nxId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_nx_scene_pick_{nxId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 scene drafts (aestheticRegister axis).",
            },
            "cp_nx_ambient_pick_": {
                "outputsRoot": "DECISION_cp_nx_ambient_pick_{nxId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_nx_ambient_pick_{nxId}.json exists with non-empty values",
                ]},
            },
            "cp_nx_runtime_pick_": {
                "outputsRoot": "DECISION_cp_nx_runtime_pick_{nxId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_nx_runtime_pick_{nxId}.json exists with non-empty values",
                ]},
            },

            # ── Family release gate (mirror cp_coherence_gate) ────────────────
            "cp_nx_gate_": {
                "outputsRoot": "DECISION_cp_nx_gate_{nxId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_nx_gate_{nxId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this "
                    "nxId are pass, commits value='clear' and releases the "
                    "narrative-experience container. On any block-fail at "
                    "iteration 5, emits <decision-request> with Retry / Patch "
                    "/ Accept-override. Direct clone of cp_sim_gate_ semantics."
                ),
            },

            # ──────────────────────────────────────────────────────────────────
            # v3.3 — GAME-EXPERIENCE planner (the fifth sibling).
            # See docs/features/game-experience-planner.md.
            # Inherits simulation-planner's contract shape with three
            # substitutions: objective (goal/score/win-condition) is first-
            # class; physics is its own engine module; feedback (juice —
            # particles/screen-shake/audio) is the §8.7 crux drawer alongside
            # world and runtime. Node-id convention: game_<component>_<gameId>
            #   game_world_paper_plane_throw   (NOT game_paper_plane_throw_world)
            # ──────────────────────────────────────────────────────────────────

            # ── Game component drawers (wildcard prefixes) ────────────────────
            "game_research_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
                "notes": (
                    "Single tech-stack researcher. Picks paradigm + render "
                    "strategy + physics engine + tick rate + input modalities "
                    "+ objective shape + juice register + multi-draft cruxes."
                ),
            },
            "game_objective_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/objective.js",
                "completion": {"requires": [
                    "files: objective.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Single source of truth for score / streak / progress / "
                    "win-condition / lose-condition / round reset. Read by "
                    "every other game drawer. Lens-gated on concept (delivers "
                    "successFeel?) — the gamification core."
                ),
            },
            "game_world_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/world.html",
                "completion": {"requires": [
                    "files: world.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Full-bleed living scene. §8.7 crux — 3-draft remix on "
                    "camera/perspective axis (2d-side / 2d-topdown / "
                    "3d-environment / iconographic-physics). Must have "
                    "ambient motion at rest (no flat resting state). All "
                    "3 lenses gate."
                ),
            },
            "game_physics_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/physics.js",
                "completion": {"requires": [
                    "files: physics.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Physics engine setup (matter.js / planck.js / cannon-es "
                    "/ rapier3d-compat / custom verlet). Lens-gated on craft "
                    "(deterministic step, no allocation in step, correct "
                    "collision categories)."
                ),
            },
            "game_input_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/input-{modality}.js",
                "completion": {"requires": [
                    "files: input-{modality}.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Per-modality input drawer. "
                    "{modality} ∈ {pointer, touch, multi-touch, gyro, gamepad}. "
                    "Lens-gated on craft (≤50ms latency, no allocation per "
                    "event, multi-touch correctness)."
                ),
            },
            "game_feedback_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/feedback.js",
                "completion": {"requires": [
                    "files: feedback.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Juice / particles / screen-shake / audio cues. §8.7 crux "
                    "— 3-draft remix on juice axis (restrained / juicy / "
                    "juice-overload). All 3 lenses gate. The drawer that "
                    "decides between Vlambeer-juicy and contemplative-restraint."
                ),
            },
            "game_loop_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/loop.js",
                "completion": {"requires": [
                    "files: loop.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Master tick loop — fixed-step accumulator composing "
                    "physics.step → objective.update → feedback.dispatch + "
                    "spawn rules + win/lose check. Lens-gated on craft "
                    "(deterministic, no allocation in tick, 60 FPS at peak)."
                ),
            },
            "game_overlay_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/overlay.svg",
                "completion": {"requires": [
                    "files: overlay.svg exists",
                    "files: overlay.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Minimal UI peek (score corner, progress edge, control "
                    "hint, win/lose card). Lens-gated on aesthetic (must NOT "
                    "box the world; ≤12% screen coverage during play) + "
                    "craft (no layout thrash)."
                ),
            },
            "game_runtime_": {
                "outputsRoot": "source/{prototype}/games/{gameId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Glue file — composes world + physics + input(s) + "
                    "objective + feedback + loop + overlay + §12.3 dev "
                    "harness + two-gate permission UX (audio + gyro). §8.7 "
                    "crux — 3-draft remix on pacing axis (meditative / "
                    "paced / frantic). Full lens trio — this IS the composed "
                    "user-facing artefact."
                ),
            },

            # ── Multi-draft pick checkpoints ──────────────────────────────────
            "cp_game_world_pick_": {
                "outputsRoot": "DECISION_cp_game_world_pick_{gameId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_game_world_pick_{gameId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 world drafts (camera/perspective axis).",
            },
            "cp_game_feedback_pick_": {
                "outputsRoot": "DECISION_cp_game_feedback_pick_{gameId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_game_feedback_pick_{gameId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 feedback drafts (juice axis).",
            },
            "cp_game_runtime_pick_": {
                "outputsRoot": "DECISION_cp_game_runtime_pick_{gameId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_game_runtime_pick_{gameId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 runtime drafts (pacing axis).",
            },

            # ── Family release gate ───────────────────────────────────────────
            "cp_game_gate_": {
                "outputsRoot": "DECISION_cp_game_gate_{gameId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_game_gate_{gameId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this "
                    "gameId are pass, commits value='clear' and releases the "
                    "game-experience container. On any block-fail at iteration "
                    "5, emits <decision-request> with Retry / Patch / "
                    "Accept-override. Direct clone of cp_sim_gate_ semantics."
                ),
            },

            # ──────────────────────────────────────────────────────────────────
            # v3.3 — SCRAPBOOK-EXPERIENCE planner (the sixth sibling).
            # See docs/features/scrapbook-experience-planner.md.
            # Inherits simulation-planner's contract shape with two
            # distinctives: (1) the composition drawer co-dispatches
            # visual-planner per IMAGE INVENTORY entry —
            # this is the most visual-planner-heavy drawer in the system;
            # (2) PNG sequences substitute for transparent GIFs (each frame
            # is a separate visual-planner sub-dispatch). Node-id
            # convention: sb_<component>_<sbId>
            #   sb_composition_vaporwave_portfolio_hero
            # ──────────────────────────────────────────────────────────────────

            # ── Scrapbook component drawers (wildcard prefixes) ───────────────
            "sb_research_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/research.md",
                "completion": {"requires": [
                    "files: research.md exists, non-empty",
                    "files: inventory.json exists, non-empty",
                ]},
                "notes": (
                    "Single tech-stack + aesthetic researcher. Picks core "
                    "aesthetic + composition idiom + density + motion register "
                    "+ interaction primitive + the IMAGE INVENTORY. The "
                    "inventory.json drives the composition drawer's "
                    "co-dispatch of visual-planner per asset."
                ),
            },
            "sb_composition_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/composition.html",
                "completion": {"requires": [
                    "files: composition.html exists, non-empty",
                    "files: composition.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Layered HTML/CSS scrapbook composition. Co-dispatches "
                    "visual-planner per inventory entry "
                    "(this drawer is the cost-heavy one). §8.7 crux — "
                    "3-draft remix on density axis (sparse / medium / dense). "
                    "All 3 lenses gate."
                ),
            },
            "sb_typography_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/typography.css",
                "completion": {"requires": [
                    "files: typography.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Web font picks (Google Fonts) + handcrafted raster "
                    "typography (commissioned via visual-planner). "
                    "Lens-gated on aesthetic (type tone matches coreAesthetic) "
                    "+ craft (web fonts load without FOIT, raster headlines "
                    "have correct alt text)."
                ),
            },
            "sb_motion_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/motion.css",
                "completion": {"requires": [
                    "files: motion.css exists, non-empty",
                    "files: motion.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "CSS drift animations + PNG-sequence loops (transparent "
                    "GIF substitute) + scroll-linked parallax + idle wobbles. "
                    "§8.7 crux — 3-draft remix on motion register axis "
                    "(still-with-twitches / drifting-ambient / "
                    "aggressive-vaporwave). All 3 lenses gate."
                ),
            },
            "sb_interactions_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/interactions.js",
                "completion": {"requires": [
                    "files: interactions.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Hover-tilt / scroll-reveal / drag-to-rearrange / "
                    "click-to-flip / tap-to-reveal / multi-touch-stack. "
                    "Lens-gated on craft (no scroll-jacking, no event "
                    "leaks, ≤50ms hover response, touch-action correctness)."
                ),
            },
            "sb_runtime_": {
                "outputsRoot": "source/{prototype}/scrapbooks/{sbId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Composed runtime — inlines composition + typography + "
                    "motion + interactions; wires Google Fonts; sets pacing. "
                    "§8.7 crux — 3-draft remix on pacing axis (calm-browse "
                    "/ scroll-revelation / interactive-discovery). Full lens "
                    "trio — this IS the composed user-facing artefact."
                ),
            },

            # ── Multi-draft pick checkpoints ──────────────────────────────────
            "cp_sb_composition_pick_": {
                "outputsRoot": "DECISION_cp_sb_composition_pick_{sbId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sb_composition_pick_{sbId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 composition drafts (density axis).",
            },
            "cp_sb_motion_pick_": {
                "outputsRoot": "DECISION_cp_sb_motion_pick_{sbId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sb_motion_pick_{sbId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 motion drafts (motion register axis).",
            },
            "cp_sb_runtime_pick_": {
                "outputsRoot": "DECISION_cp_sb_runtime_pick_{sbId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sb_runtime_pick_{sbId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 runtime drafts (pacing axis).",
            },

            # ── Family release gate ───────────────────────────────────────────
            "cp_sb_gate_": {
                "outputsRoot": "DECISION_cp_sb_gate_{sbId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_sb_gate_{sbId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this "
                    "sbId are pass, commits value='clear' and releases the "
                    "scrapbook-experience container. On any block-fail at "
                    "iteration 5, emits <decision-request> with Retry / Patch "
                    "/ Accept-override. Direct clone of cp_sim_gate_ semantics."
                ),
            },

            # ──────────────────────────────────────────────────────────────────
            # v3.3 — INTERACTIVE-POLISH planner (the seventh sibling — POST-PASS).
            # See docs/features/interactive-polish-planner.md.
            # Unlike the other six planners, this runs LAST in the pipeline:
            # after another primary planner's build phase (or after chat-Claude
            # has hand-written source), BEFORE Step-8 QA. The research drawer
            # identifies SITES + TYPES of opportunity (microanimation / pointer /
            # scroll / hover-surprise / shader-overlay); the per-type drawers
            # decide the SPECIFIC implementation. Output goes to
            # source/<branch>/_polish/<polishId>/ as supplemental files; the
            # runtime drawer writes integration-instructions.md describing the
            # minimal <link>/<script> edits the caller applies to host pages.
            # ──────────────────────────────────────────────────────────────────

            # ── Polish component drawers (wildcard prefixes) ──────────────────
            "polish_research_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/research.md",
                "completion": {"requires": [
                    "files: research.md exists, non-empty",
                    "files: polish-plan.json exists, non-empty",
                ]},
                "notes": (
                    "Surveys existing source HTML/CSS/JS, identifies SITES of "
                    "opportunity (microanimation / pointer / scroll / "
                    "hover-surprise / shader-overlay), commits polish register "
                    "(subtle / playful / theatrical) per genre. The site map "
                    "drives which drawers fire + which selectors they target. "
                    "Per planner-vs-drawer split: identifies WHERE + TYPE only — "
                    "drawers decide WHAT the specific improvement looks like."
                ),
            },
            "polish_microanimation_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/microanim.css",
                "completion": {"requires": [
                    "files: microanim.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Decides WHAT microanimation each microanimation-typed "
                    "site becomes (idle-breath, soft-glow, type-on, drop-cap-"
                    "drop, etc.). Writes microanim.css + optional microanim.js. "
                    "Lens-gated on craft (compositor-only properties, "
                    "prefers-reduced-motion) + aesthetic (pattern fits "
                    "register × genre)."
                ),
            },
            "polish_pointer_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/pointer.js",
                "completion": {"requires": [
                    "files: pointer.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Decides WHAT each pointer-tinted + scroll-driven site "
                    "becomes (cursor-spotlight, magnetic-pull, card-tilt-3d, "
                    "scroll-fade-in, sticky-condensing-nav, parallax-hero, "
                    "scroll-progress-bar, etc.). Lens-gated on craft (passive "
                    "listeners, no scroll-jacking, rAF-driven, touch gates)."
                ),
            },
            "polish_hover_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/hover.css",
                "completion": {"requires": [
                    "files: hover.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Decides WHAT each hover-surprise site becomes (scale-"
                    "shadow-lift, peek-secondary-content, card-flip-3d, "
                    "slide-reveal-action, dim-siblings, etc.). Writes hover.css "
                    "+ optional hover.js. Lens-gated on craft (keyboard "
                    "equivalent for :hover via :focus-visible, no layout shift)."
                ),
            },
            "polish_shader_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/shader.html",
                "completion": {"requires": [
                    "files: shader.html exists, non-empty",
                    "files: shader-mount.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Decides WHAT shader overlay effect (halftone-print, "
                    "paper-grain, dither, CRT-scanline, chromatic-aberration, "
                    "glitch, noise-wash, vignette-fade, moire). CO-DISPATCHES "
                    "visual-planner with the shader skill to commission the "
                    "actual GLSL. §8.7 crux drawer — multi-draft on shader-"
                    "effect axis when research recommends. All 3 lenses gate."
                ),
            },
            "polish_runtime_": {
                "outputsRoot": "source/{prototype}/_polish/{polishId}/composite.css",
                "completion": {"requires": [
                    "files: composite.css exists",
                    "files: composite.js exists",
                    "files: integration-instructions.md exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Concatenates microanim.css + hover.css + shader-mount.css "
                    "into composite.css; concatenates microanim.js + pointer.js "
                    "+ hover.js into composite.js; writes integration-"
                    "instructions.md describing the minimal HTML edits the "
                    "caller applies per host page (single <link> + <script> + "
                    "optional shader-mount <div>). Lens-gated on craft."
                ),
            },

            # ── Multi-draft pick checkpoint (shader effect only) ──────────────
            "cp_polish_shader_pick_": {
                "outputsRoot": "DECISION_cp_polish_shader_pick_{polishId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_polish_shader_pick_{polishId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 shader effect drafts (e.g. halftone vs paper-grain vs dither).",
            },

            # ── Family release gate ───────────────────────────────────────────
            "cp_polish_gate_": {
                "outputsRoot": "DECISION_cp_polish_gate_{polishId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_polish_gate_{polishId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this "
                    "polishId are pass, commits value='clear' and releases the "
                    "interactive-polish container. On any block-fail at "
                    "iteration 5, emits <decision-request> with Retry / Patch / "
                    "Drop-site / Accept-override. Direct clone of cp_sim_gate_."
                ),
            },
        },
    },

    # ── ds-brainstorm ─────────────────────────────────────────────────────
    "ds-brainstorm": {
        "title":        "DS variant brainstorm",
        "category":     "producer",
        "inputs": {
            "variant":               {"type": "text", "label": "Variant id (a/b/c/d/...)", "userEditable": False},
            "spec.mode":             {"type": "enum", "values": ["dark", "light", "any"], "default": "any", "userEditable": True},
            "spec.genre":            {"type": "markdown", "label": "Direction", "userEditable": True},
            "spec.compatibleShells": {"type": "array", "userEditable": True},
            "spec.primaryShell":     {"type": "text", "userEditable": True},
            "spec.label":            {"type": "text", "userEditable": True},
        },
        "outputs": {
            "label":            {"type": "text", "required": True},
            "direction":        {"type": "text", "required": True},
            "primaryShell":     {"type": "text", "required": True},
            "compatibleShells": {"type": "array", "required": True},
        },
        "outputsRoot":  "source/{prototype}/_ds_brainstorm/{variant}/",
        # v2.50 — idTemplate: when the reconciler finds an orphan variant
        # folder on disk that has no matching node, auto-heal substitutes
        # {variant} here to build the new node id. Without this, auto-heal
        # would have to hardcode the prefix per kind — exactly the
        # "list of names" anti-pattern.
        "idTemplate":         "bs_ds_{variant}",
        # The auto-healed node wires into this checkpoint node so the
        # user-pick step sees the new variant immediately. Absent → no
        # checkpoint wiring (kind doesn't have one).
        "checkpointNodeId":   "cp_ds_pick",
        "consumeFrom":  None,
        "dispatch":     "task-subagents",
        "fanOut": {
            "kind":         "task-subagents",
            "isolation":    "cold",
            "parallelism":  "siblings-parallel",
            "count":        "per-instance",
            "diverger":     "inputs.spec.genre",
        },
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": True},
        "extendsGraph": True,
        "graphExtensionScope": "per-variant image-pipeline trios (p_*, s_*, r_*, a_*) attached under this variant's card",
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion": {
            "requires": [
                "files: outputsRoot/index.html exists",
                "outputs.label set",
                "outputs.primaryShell set in compatibleShells",
            ],
        },
        "pauseAfter":   False,
        "openEnded":    True,
        "notes": (
            "Each ds-brainstorm node is a COLD-ISOLATED subagent session that "
            "diverges on its own spec.genre. The producer drops EVERYTHING "
            "(index.html, assets/, sparkline.js, any new modules) into "
            "outputsRoot. Siblings never see each other's context — divergence "
            "is structural.\n\n"
            "VARIANT COUNT IS OPEN-ENDED. Scaffold creates a/b/c by default but "
            "the user may make d/e/f/... via chat refinement. The reconciler "
            "auto-promotes any new variant folder under _ds_brainstorm/ to a "
            "ds-brainstorm card silently (no Heal click required).\n\n"
            "After writing the variant folder, the subagent dispatches the "
            "visual-planner via the Task tool, SCOPED TO THIS VARIANT'S "
            "outputsRoot only. Image-pipeline trios are committed with a "
            "parentVariant reference so they render visually grouped under "
            "this variant's card."
        ),
    },

    # ── design-system ─────────────────────────────────────────────────────
    "design-system": {
        "title":        "Generate design system",
        "category":     "consumer",
        "inputs": {
            "dsId":  {"type": "text", "default": "main", "userEditable": False},
            "spec":  {"type": "object", "userEditable": True},
        },
        "outputs": {
            "version": {"type": "text", "required": True},   # content hash
            "label":   {"type": "text", "required": True},   # v1, v2, ...
        },
        "outputsRoot":  "design-systems/{dsId}/",
        "consumeFrom": {
            "source": "{picked.outputsRoot}",   # resolved from DECISION_cp_ds_pick
            "rules": [
                {"match": "**/index.html",        "handler": "extract-variant-spec", "target": "meta.json#fromVariant"},
                {"match": "**/*.css",             "handler": "merge-tokens",         "target": "primitives/"},
                {"match": "**/*.js",              "handler": "copy",                 "target": "primitives/"},
                {"match": "**/*.png",             "handler": "copy",                 "target": "assets/"},
                {"match": "**/*.jpg",             "handler": "copy",                 "target": "assets/"},
                {"match": "**/*.jpeg",            "handler": "copy",                 "target": "assets/"},
                {"match": "**/*.svg",             "handler": "copy",                 "target": "assets/"},
                {"match": "**/*.webp",            "handler": "copy",                 "target": "assets/"},
                {"match": "**/*.md",              "handler": "copy",                 "target": "docs/"},
                {"match": "**/spec.json",         "handler": "merge-spec",           "target": "meta.json#fromVariant"},
            ],
            "unhandled": "reject",
        },
        "dispatch":     "single-subprocess",
        "fanOut":       None,
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion": {
            "requires": [
                "files: outputsRoot/styles.css exists",
                "files: outputsRoot/gallery.html exists",
                "files: outputsRoot/meta.json exists",
                "files: outputsRoot/shells/ contains at least one .css",
                "consumeFrom: 0 unhandled files",
            ],
        },
        "pauseAfter":   True,        # stage D — major artifact, pause for review
        "notes": (
            "Consumes the picked ds-brainstorm folder EXHAUSTIVELY (must-consume "
            "strict mode). Every file in upstream's outputsRoot MUST be routed "
            "by a consumeFrom rule; an unhandled file is a hard validation "
            "failure. This is the rule that prevents super's net.js + "
            "driver-constellation.png orphans."
        ),
    },

    # ── asset ─────────────────────────────────────────────────────────────
    "asset": {
        "title":        "Asset (file reference)",
        "category":     "container",
        "inputs": {
            "path":      {"type": "text", "label": "File path", "userEditable": True, "required": True},
            "paths":     {"type": "array", "label": "File paths (set)", "userEditable": False,
                          "doc": "html-set / multi-file assets use this in addition to (or in place of) path."},
            "assetKind": {"type": "enum",
                          "values": ["image","html","html-set","svg","video","audio","3d","shader","markdown","text"],
                          "userEditable": False},
            "boundTo":   {"type": "object", "userEditable": False},
            "title":     {"type": "text", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done", "error"],
        "completion":   {"requires": ["files: inputs.path exists on disk"]},
        "pauseAfter":   False,
        # ── Asset-versioning contract (docs/features/asset-versioning.md §3, §8)
        # The daemon snapshots an asset's referenced files after every
        # upstream producer run completes. Each snapshot becomes a new
        # version on the asset node; sub-asset upstream is captured per
        # version as compositions (a tuple of sub-asset → sub-version).
        "versioning": {
            "enabled":                  True,
            "maxUnpinnedVersions":      20,
            "maxUnpinnedCompositions":  50,
            "snapshotRoot":             "workflow/runs/{nodeId}/{versionId}/",
            "viewRoot":                 "workflow/views/{nodeId}/{versionId}/{compositionId}/",
            "thumbStrategy":            "canvas-html2canvas",   # or "daemon-direct" for image/svg
        },
        "adaptiveSize": {
            "enabled":        True,
            "scaleDefault":   "fit-canvas",
            "minW":           280,
            "maxW":           720,
            "aspectFrom":     "viewport|image|markdown",
        },
        "notes": "Display wrapper. Refresh on file change via SSE asset-changed (D1). Versioned: every upstream-producer run snapshots the asset's files into workflow/runs/, with an auto-locked composition capturing sub-asset pins.",
    },

    # ── iterator-refiner ──────────────────────────────────────────────────
    "iterator-refiner": {
        "title":        "Iterator — refiner (2-agent interview loop)",
        "category":     "iterator",
        "inputs": {
            "goal":               {"type": "markdown", "userEditable": True},
            "focus":              {"type": "markdown", "userEditable": True},
            "pushPast":           {"type": "array",    "userEditable": True},
            "maxTurns":           {"type": "number",   "default": 8, "userEditable": True},
            "interviewerAgentId": {"type": "text", "userEditable": False},
            "intervieweeAgentId": {"type": "text", "userEditable": False},
            "outputPromptId":     {"type": "text", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "client-iterator",   # browser-side loop
        "fanOut":       None,
        "visibility":   {"transcript": True, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "5 children: 2 prompts + 2 agents wired in a loop",
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion":   {"requires": ["outputPromptId.text non-empty", "[STOP] observed OR maxTurns reached"]},
        "pauseAfter":   False,
        "notes": "Already correct. Two isolated agent sessions converse via [STOP]. No change.",
    },

    # ── iterator-remix ────────────────────────────────────────────────────
    "iterator-remix": {
        "title":        "Iterator — remix (N parallel HTML variants)",
        "category":     "iterator",
        "inputs": {
            "n":        {"type": "number", "default": 3, "userEditable": True},
            "variants": {"type": "array",  "userEditable": True},
            "model":    {"type": "text",   "default": "claude-opus-4-7", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  "source/{prototype}/_remix/p{pageIdx}/",
        "consumeFrom": {
            "source": "{upstream.outputsRoot}",
            "rules": [
                {"match": "**/*.html", "handler": "use-as-base", "target": "(input)"},
                {"match": "**/*.css",  "handler": "preserve",    "target": "(input)"},
                {"match": "**/*.png",  "handler": "use-as-base", "target": "(input)"},
                {"match": "**/*.jpg",  "handler": "use-as-base", "target": "(input)"},
                {"match": "**/*.svg",  "handler": "use-as-base", "target": "(input)"},
            ],
            "unhandled": "warn",   # remix may ignore peripheral upstream files
        },
        "dispatch":     "task-subagents",
        "fanOut": {
            "kind":         "task-subagents",
            "isolation":    "cold",
            "parallelism":  "siblings-parallel",
            "count":        "inputs.n",
            "diverger":     "inputs.variants[i]",
        },
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": True},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion": {
            "requires": [
                "files: each variant outputsRoot/{a,b,c}/ non-empty",
                "each variant folder contains an *.html",
            ],
        },
        "pauseAfter":   False,
        "openEnded":    True,
        "notes": (
            "3 remix nodes × 3 alt subagents = 9 concurrent Claude Code "
            "sessions at peak. No concurrency cap. Rate-limited siblings "
            "surface as drift with retry affordance in the reconciler panel."
        ),
    },

    # ── iterator-repeater ─────────────────────────────────────────────────
    "iterator-repeater": {
        "title":        "Iterator — repeater (N text variants)",
        "category":     "iterator",
        "inputs": {
            "n":        {"type": "number", "default": 3, "userEditable": True},
            "variants": {"type": "array",  "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "task-subagents",
        "fanOut": {
            "kind":         "task-subagents",
            "isolation":    "cold",
            "parallelism":  "siblings-parallel",
            "count":        "inputs.n",
            "diverger":     "inputs.variants[i]",
        },
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": True},
        "extendsGraph": True,
        "graphExtensionScope": "N child nodes downstream",
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion":   {"requires": ["all N child nodes runStatus == done"]},
        "pauseAfter":   False,
        "notes": "Cold-isolated repeater for text variants.",
    },

    # ── iterator-blend ────────────────────────────────────────────────────
    "iterator-blend": {
        "title":        "Iterator — blend (N inputs → 1 output)",
        "category":     "iterator",
        "inputs": {
            "n":          {"type": "number", "default": 2, "userEditable": True},
            "slots":      {"type": "array",  "userEditable": True},
            "outputKind": {"type": "enum",   "values": ["image","text"], "userEditable": True},
            "model":      {"type": "text",   "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  "source/{prototype}/_blend/{id}/",
        "consumeFrom": {
            "source": "{upstream[0..n].outputsRoot}",
            "rules":  [{"match": "**/*", "handler": "include-with-weight", "target": "(input)"}],
            "unhandled": "warn",
        },
        "dispatch":     "single-subprocess",
        "fanOut":       None,
        "visibility":   {"transcript": True, "chatPanel": True, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "running", "done", "error"],
        "completion":   {"requires": ["files: outputsRoot non-empty"]},
        "pauseAfter":   False,
        "notes": "Single blended output from N weighted inputs. Not a fan-out.",
    },

    # ── color-palette ─────────────────────────────────────────────────────
    "color-palette": {
        "title":        "Color palette",
        "category":     "container",
        "inputs": {
            "swatches": {"type": "array", "userEditable": True},
            "name":     {"type": "text",  "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "Read-only reference wired into design-system or prototype.",
    },

    # ── typography ────────────────────────────────────────────────────────
    "typography": {
        "title":        "Typography",
        "category":     "container",
        "inputs": {
            "tokens": {"type": "array", "userEditable": True},
            "name":   {"type": "text",  "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "Read-only reference wired into design-system or prototype.",
    },

    # ── prototype ─────────────────────────────────────────────────────────
    "prototype": {
        "title":        "Prototype (live iframe)",
        "category":     "container",
        "inputs": {
            "branch":         {"type": "text",   "userEditable": False},
            "instanceId":     {"type": "text",   "userEditable": False},
            "exposedAssets":  {"type": "array",  "userEditable": False},
            "lockedState":    {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "asset child nodes for exposed files",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "Live iframe. User-driven. Expose button creates asset children with boundTo set.",
    },

    # ── frames ───────────────────────────────────────────────────────────
    # Canvas-frames viewer. Slim companion to `prototype`: an iframe
    # rendering the editor's Canvas tab (view=canvas + embed=1) for a
    # given prototype's branch. Spawned from the prototype-node bar's
    # Canvas-frames button; carries `branch` (which prototype/source it
    # mirrors) and `host` (the prototype node id it was spawned from,
    # used for placement + future "follow the prototype" semantics).
    # Read-only — no agent dispatch, no versioning, no ports. The
    # underlying frames data lives in editor/data.js, regenerated by
    # Workflow 1 (frames+arrows slice when the user picks "generate
    # now" from the missing-data prompt).
    "frames": {
        "title":        "Canvas frames (live editor view)",
        "category":     "container",
        "inputs": {
            "branch":     {"type": "text", "userEditable": False},
            "host":       {"type": "text", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "Live editor Canvas-tab iframe. User-driven. Spawned from prototype node; offers Workflow 1 (frames slice) when data is missing.",
    },

    # ── composer ─────────────────────────────────────────────────────────
    # v3.4.37 — Responsive layered canvas. Each wired asset becomes a
    # layer inside an aspect-ratio frame; per-layer state carries
    # opacity, anchor (12 modes incl. stretch/fill), offset, sizing.
    # Output is a rendered HTML view that downstream prototype/HTML
    # consumers can embed or screenshot.
    "composer": {
        "title":        "Composer (responsive canvas)",
        "category":     "container",
        "inputs": {
            "layers":     {"type": "array",  "userEditable": True},
            "width":      {"type": "number", "userEditable": True},
            "height":     {"type": "number", "userEditable": True},
            "maxWidth":   {"type": "number", "userEditable": True},
            "maxHeight":  {"type": "number", "userEditable": True},
            "background": {"type": "text",   "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "User-driven. Asset inputs are layered onto a responsive canvas with per-layer anchor/opacity.",
    },

    # ── vector-editor ────────────────────────────────────────────────────
    # Inline SVG drawing tool. Three-pane layout: tools+layers (left),
    # SVG stage (middle), properties (right). Shapes are stored inline
    # on the node; Bake serializes them into a self-contained .svg
    # written to source/<branch>/vector-<nodeId>.svg so downstream
    # composer/agent/prototype nodes can consume it like a regular SVG
    # asset.
    "vector-editor": {
        "title":        "Vector editor",
        "category":     "container",
        "inputs": {
            "shapes":     {"type": "array",  "userEditable": True},
            "canvasW":    {"type": "number", "userEditable": True},
            "canvasH":    {"type": "number", "userEditable": True},
            "background": {"type": "text",   "userEditable": True},
            "activeTool": {"type": "text",   "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "User-driven inline vector tool. Bake writes source/<branch>/vector-<id>.svg; downstream consumers read bakedPath as an SVG asset.",
    },

    # ── formatted-text ───────────────────────────────────────────────────
    # v3.4.37 — Rich text node. The body is edited in-place via
    # contentEditable, and the user can select a range to apply a
    # typography level from a wired Typography node. A plain Prompt
    # wired to `text-in` overwrites the body when its content changes.
    # Output is the rendered HTML so downstream consumers (composer,
    # prototype) can embed it.
    "formatted-text": {
        "title":        "Formatted text",
        "category":     "container",
        "inputs": {
            "html":     {"type": "text", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "User-driven. Typography input enables a selection-based level picker.",
    },

    # ── mermaid ──────────────────────────────────────────────────────────
    # v3.4.38 — Mermaid diagram node. The body renders via the mermaid.js
    # CDN bundle pinned in editor/index.html. Source code is stored
    # inline on the node, edited via a tailored code panel (same </>
    # affordance as the asset code panel) that surfaces a diagram-type
    # dropdown above the textarea so the user can switch between
    # flowchart / sequence / class / state / er / pie / etc.
    "mermaid": {
        "title":        "Mermaid diagram",
        "category":     "container",
        "inputs": {
            "code":         {"type": "text", "userEditable": True},
            "diagramType":  {"type": "text", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "User-driven. Renders Mermaid source via the CDN bundle in editor/index.html.",
    },

    # ── simulation (v3.3 — live iframe for runnable simulation) ──────────
    # See docs/features/simulation-and-interactive-planners.md §6.4.
    # Mirrors `prototype` shape; the component drawers that produce the
    # files this container points at are agent-kind per-id overrides
    # (sim_research_*, sim_scene_*, sim_loop_*, etc.).
    "simulation": {
        "title":        "Simulation (live iframe)",
        "category":     "container",
        "inputs": {
            "simId":          {"type": "text",   "userEditable": False, "required": True},
            "paradigm":       {"type": "enum",
                                "values": ["2d-spatial-map", "3d-environment",
                                           "iconographic-anim", "hybrid"],
                                "userEditable": False},
            "exposedAssets":  {"type": "array",  "userEditable": False},
            "lockedState":    {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/entities/scene/loop/controls/overlay/runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a runnable simulation. User-driven. Run re-builds "
            "via re-dispatching simulation-planner. "
            "Component children own their own files and lens verdicts; this "
            "container is marked done only when the planner's commit carries "
            "outputs.lensVerdict='pass'."
        ),
    },

    # ── interactive-media (v3.3 — live iframe for TouchDesigner-grade pieces)
    # See docs/features/simulation-and-interactive-planners.md §7.4.
    "interactive-media": {
        "title":        "Interactive media (live iframe)",
        "category":     "container",
        "inputs": {
            "imId":             {"type": "text",   "userEditable": False, "required": True},
            "declaredInputs":   {"type": "array",  "userEditable": False},
            "declaredOutputs":  {"type": "array",  "userEditable": False},
            "mappingStyle":     {"type": "enum",
                                  "values": ["direct", "accumulative",
                                             "threshold-triggered", "ml-classified"],
                                  "userEditable": False},
            "permissionGates":  {"type": "array",  "userEditable": False},
            "exposedAssets":    {"type": "array",  "userEditable": False},
            "lockedState":      {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/modality/input[]/mapping/output[]/runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of an interactive piece. permissionGates surfaced "
            "to the canvas BEFORE Run so the user grants camera/mic/etc. "
            "consent at the canvas-side prompt rather than being surprised "
            "by the iframe. Component children own their files + lens verdicts."
        ),
    },

    # ── narrative-experience (v3.3 — poetic cousin of `simulation`) ──────
    # The user-facing artefact container for one immersive walk-into-this-
    # place piece. Mirrors `simulation` shape with three substitutions:
    # spine (scripted timeline) instead of loop, camera-as-narrator instead
    # of free controls, ambient (soundscape) as a new first-class channel.
    # See `narrative-experience-planner.md`.
    "narrative-experience": {
        "title":        "Narrative experience (live iframe)",
        "category":     "container",
        "inputs": {
            "nxId":              {"type": "text",   "userEditable": False, "required": True},
            "paradigm":          {"type": "enum",
                                   "values": ["2d-illustrative",
                                              "3d-environment",
                                              "iconographic-anim",
                                              "hybrid"],
                                   "userEditable": False,
                                   "doc": "Same shape as simulation's paradigm field. 3d-environment covers EVERYTHING from scripted three.js flythroughs to walkable WASD/orbit-controlled spaces — how the camera binds + how much freedom the user has is a property of how the spine + camera drawers are written, not a separate field."},
            "aestheticRegister": {"type": "enum",
                                   "values": ["painterly", "volumetric", "sketch", "mixed-media"],
                                   "userEditable": False},
            "emotionalRegister": {"type": "enum",
                                   "values": ["contemplative", "reverent", "wistful",
                                              "unsettling", "luminous"],
                                   "userEditable": False},
            "pacingFeel":        {"type": "enum",
                                   "values": ["slow-bath", "progressive-reveal",
                                              "immediate-immersion"],
                                   "userEditable": False},
            "exposedAssets":     {"type": "array",  "userEditable": False},
            "lockedState":       {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/spine/scene/camera/ambient/reveal/overlay/runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of an immersive narrative experience. Same 4-paradigm "
            "structure as `simulation` (2d-illustrative / 3d-environment / "
            "iconographic-anim / hybrid) with three substitutions in the drawer "
            "family: spine (scripted timeline; may contain free regions) "
            "replaces loop; reveals (user input → progressive discovery OR "
            "free-roam navigation) replaces controls; ambient (soundscape) is "
            "a new first-class channel. Walkable 3D pieces live inside the "
            "3d-environment paradigm — how much freedom the user has is a "
            "property of how spine + camera-handling are written, not a "
            "separate enum. Permission UX gates ambient audio via the two-"
            "gate pattern (canvas-side + iframe-side Start) inherited from "
            "INTERACTIVITY_PIPELINE — audio context requires user gesture."
        ),
    },

    # ── game-experience (v3.3 — fifth sibling of simulation/interactive/narrative)
    # The user-facing artefact container for one game-like immersive piece.
    # Same shape as `simulation` with three substitutions: objective (goal /
    # score / win-condition) is first-class; physics is its own engine module;
    # feedback (juice — particles / screen-shake / audio) is the §8.7 crux
    # drawer alongside world and runtime. See `game-experience-planner.md`.
    "game-experience": {
        "title":        "Game experience (live iframe)",
        "category":     "container",
        "inputs": {
            "gameId":          {"type": "text",   "userEditable": False, "required": True},
            "paradigm":        {"type": "enum",
                                 "values": ["2d-side", "2d-topdown",
                                            "3d-environment",
                                            "iconographic-physics", "hybrid"],
                                 "userEditable": False,
                                 "doc": "The world's camera/perspective axis. Picked at §8.7 multi-draft crux when research recommends; otherwise from research's single recommendation."},
            "objective":       {"type": "text",   "userEditable": False,
                                 "doc": "One-line goal verbatim (e.g. 'fly as far as possible; collect mugs for +score; hit walls = end')."},
            "juiceRegister":   {"type": "enum",
                                 "values": ["restrained", "paced", "juicy", "juice-overload"],
                                 "userEditable": False,
                                 "doc": "Picked at §8.7 feedback crux when research recommends; otherwise from research."},
            "pacingFeel":      {"type": "enum",
                                 "values": ["meditative", "paced", "frantic"],
                                 "userEditable": False,
                                 "doc": "Picked at §8.7 runtime crux when research recommends; otherwise from research."},
            "declaredInputs":  {"type": "array",  "userEditable": False,
                                 "doc": "Modalities the piece accepts. Subset of {pointer, touch, multi-touch, gyro, gamepad}."},
            "permissionGates": {"type": "array",  "userEditable": False,
                                 "doc": "Canvas-side gates the editor renders before Run. Subset of {audio, gyro}."},
            "exposedAssets":   {"type": "array",  "userEditable": False},
            "lockedState":     {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/objective/world/physics/input(s)/feedback/loop/overlay/runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a game-like immersive piece. Same shape as "
            "`simulation` / `narrative-experience` with three substitutions in "
            "the drawer family: objective (goal/score/win-condition) is "
            "first-class; physics is its own engine module; feedback (juice "
            "— particles/shake/audio) is the §8.7 crux drawer alongside world "
            "and runtime. The world is full-bleed with NO flat resting state "
            "— ambient motion always plays. The overlay PEEKS at the edges "
            "(score corner, progress edge, control hint) — never frames the "
            "action. Permission UX gates audio (and gyro on mobile) via the "
            "two-gate pattern (canvas-side + iframe-side Start) inherited "
            "from INTERACTIVITY_PIPELINE — audio context requires user gesture."
        ),
    },

    # ── scrapbook-experience (v3.3 — sixth sibling of simulation/interactive/narrative/game)
    # The user-facing artefact container for one raster-heavy collage piece.
    # Aesthetic categories: vaporwave / internetcore / cottagecore / dreamcore /
    # weirdcore / Y2K / lo-fi / mixtape / zine / mood-board / lookbook / hybrid.
    # The composition drawer co-dispatches visual-planner per
    # IMAGE INVENTORY entry — this is the most visual-planner-heavy container
    # in the system. PNG sequences substitute for transparent GIFs (each frame
    # = one visual-planner sub-dispatch). See `scrapbook-experience-planner.md`.
    "scrapbook-experience": {
        "title":        "Scrapbook experience (live iframe)",
        "category":     "container",
        "inputs": {
            "sbId":              {"type": "text",   "userEditable": False, "required": True},
            "coreAesthetic":     {"type": "enum",
                                   "values": ["vaporwave", "internetcore",
                                              "cottagecore", "dreamcore",
                                              "weirdcore", "Y2K", "lo-fi",
                                              "mixtape", "zine", "mood-board",
                                              "lookbook", "hybrid"],
                                   "userEditable": False,
                                   "doc": "Committed by research; multi-draft is a separate axis (density)."},
            "density":           {"type": "enum",
                                   "values": ["sparse", "medium", "dense"],
                                   "userEditable": False,
                                   "doc": "Picked at §8.7 composition crux when research recommends; otherwise from research."},
            "motionRegister":    {"type": "enum",
                                   "values": ["still-with-twitches",
                                              "drifting-ambient",
                                              "aggressive-vaporwave"],
                                   "userEditable": False,
                                   "doc": "Picked at §8.7 motion crux when research recommends; otherwise from research."},
            "pacingFeel":        {"type": "enum",
                                   "values": ["calm-browse",
                                              "scroll-revelation",
                                              "interactive-discovery"],
                                   "userEditable": False,
                                   "doc": "Picked at §8.7 runtime crux when research recommends; otherwise from research."},
            "interactionPrimitive": {"type": "enum",
                                      "values": ["scroll-reveal",
                                                 "hover-tilt",
                                                 "drag-to-rearrange",
                                                 "click-to-flip",
                                                 "tap-to-reveal",
                                                 "multi-touch-stack"],
                                      "userEditable": False},
            "imageCount":        {"type": "number", "userEditable": False,
                                   "doc": "Total raster assets in inventory (entries + total PNG-sequence frames)."},
            "exposedAssets":     {"type": "array",  "userEditable": False},
            "lockedState":       {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/composition/typography/motion/interactions/runtime) + N visual-planner-co-dispatched asset trios",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a raster-heavy collage piece. Aesthetics are "
            "named cores (vaporwave / cottagecore / dreamcore / Y2K / "
            "lo-fi / etc.) — the planner DOES NOT serve CSS-driven aesthetics "
            "(Bauhaus / Swiss-grid / terminal-on-web etc.); those redirect to "
            "visual-planner for hero assets in a CSS-restrained app. Composition "
            "drawer co-dispatches visual-planner per IMAGE "
            "INVENTORY entry — N entries = N sub-dispatches. PNG sequences "
            "substitute for transparent GIFs (each frame = one sub-dispatch). "
            "Typography splits between web fonts (body / microtype via "
            "Google Fonts) + raster handlettering (display words / "
            "signatures / marker annotations via visual-planner)."
        ),
    },

    # ── interactive-polish (v3.3 — seventh sibling; POST-PASS planner) ────
    # Different shape from the other six: runs LAST in the pipeline, after
    # another primary planner's build phase (or after chat-Claude has
    # hand-written source), BEFORE Step-8 QA. Reads existing source,
    # identifies SITES of opportunity for interactive enrichment, dispatches
    # per-type drawers that decide the SPECIFIC improvement. Writes
    # supplemental files to source/<branch>/_polish/<polishId>/ — existing
    # source stays intact; the caller applies minimal <link>/<script> edits
    # per host page from the runtime drawer's integration-instructions.md.
    # See `interactive-polish-planner.md`.
    "interactive-polish": {
        "title":        "Interactive polish (post-pass)",
        "category":     "container",
        "inputs": {
            "polishId":           {"type": "text",   "userEditable": False, "required": True},
            "polishRegister":     {"type": "enum",
                                    "values": ["subtle", "playful", "theatrical"],
                                    "userEditable": False,
                                    "doc": "Committed by research per genre × envelope."},
            "siteCount":          {"type": "number", "userEditable": False,
                                    "doc": "Total enrichment sites across all opportunity types."},
            "siteCountByType":    {"type": "object", "userEditable": False,
                                    "doc": "Per-type breakdown: microanimation / pointer-tinted / scroll-driven / hover-surprise / shader-overlay."},
            "drawersDispatched":  {"type": "array",  "userEditable": False,
                                    "doc": "Subset of {polish_microanimation_, polish_pointer_, polish_hover_, polish_shader_, polish_runtime_} that ran. Drawers may be SKIPPED if their type has 0 sites — unlike the other six planners where every drawer fires."},
            "pagesIntegrated":    {"type": "array",  "userEditable": False,
                                    "doc": "Host pages that received the <link>/<script>/shader-mount edits applied by the caller."},
            "exposedAssets":      {"type": "array",  "userEditable": False},
            "lockedState":        {"type": "object", "userEditable": False},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "component children (research/microanimation/pointer/hover/shader/runtime) + optional visual-planner-co-dispatched shader trio",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Post-pass enrichment container — runs after another primary "
            "planner's build phase, before Step-8 QA. Existing source is "
            "preserved; polish files live in source/<branch>/_polish/<polishId>/. "
            "Each host page in pagesIntegrated received TWO new tags (a "
            "single <link> + a single <script>) — and ONE more <div> if the "
            "shader-overlay drawer ran. Zero-site outcomes (source already "
            "richly polished, no opportunity types identified) are valid; "
            "the runtime drawer writes an empty composite.css + composite.js "
            "+ integration-instructions.md saying 'no edits needed'. The "
            "interactive-polish container is the ONE post-pass artefact in "
            "the planner system; the other six containers (prototype, "
            "simulation, interactive-media, narrative-experience, game-"
            "experience, scrapbook-experience) are primary build artefacts."
        ),
    },

    # ── section (manual-only) ─────────────────────────────────────────────
    "section": {
        "title":        "Section (group frame)",
        "category":     "decoration",
        "inputs": {
            "title": {"type": "text",   "userEditable": True},
            "w":     {"type": "number", "userEditable": True},
            "h":     {"type": "number", "userEditable": True},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued"],
        "completion":   {"requires": []},
        "pauseAfter":   False,
        "notes": "Pure UI grouping. No semantics. Never created by the orchestrator; manual only.",
    },
}


# ─── helpers ──────────────────────────────────────────────────────────────

def kind_contract(node_kind: str, node_id: str = None):
    """Resolve a kind contract, applying per-id overrides if present.
    Returns a merged dict, or None if the kind is unknown.

    Per-id overrides support TWO forms:
      • exact match — overrides[node_id]
      • prefix wildcard — overrides["prefix_"] applies to any id starting with
        "prefix_". Used for openEnded per-instance contracts like the Coherence
        Pass's `v_<assetId>` vision-verify nodes (one per visual trio)."""
    base = KINDS.get(node_kind)
    if not base:
        return None
    if not node_id:
        return base
    overrides = base.get("perIdOverrides") or {}
    # Exact match first
    if node_id in overrides:
        out = dict(base)
        for k, v in overrides[node_id].items():
            out[k] = v
        return out
    # Prefix wildcard: look for keys ending in "_" that prefix this node_id.
    best_prefix = ""
    for key in overrides:
        if key.endswith("_") and node_id.startswith(key) and len(key) > len(best_prefix):
            best_prefix = key
    if best_prefix:
        out = dict(base)
        for k, v in overrides[best_prefix].items():
            out[k] = v
        return out
    return base


def stage_pause_after(code: str) -> bool:  # noqa: ARG001 — kept for API compat
    """Legacy stage-pause check. STAGES list is empty post-v3.5, so always False."""
    return False


def editable_field_keys(node) -> list:
    """Return the field keys this node's kind treats as user-editable.
    The frontend's dirty-tracking machinery (savedSnapshotRef) consults this.
    Mirrors the legacy app.js _editableFieldsForKind function but derived
    from the registry — single source of truth (Principle 1)."""
    if not isinstance(node, dict): return []
    kind = node.get("kind")
    if not kind: return []
    contract = kind_contract(kind, node.get("id"))
    if not contract: return []
    out = []
    for key, spec in (contract.get("inputs") or {}).items():
        if isinstance(spec, dict) and spec.get("userEditable"):
            # Dotted keys like "spec.genre" map to nested fields; the
            # frontend's snapshot keys use the top-level field. Collapse
            # spec.* → spec so the merge handles the whole spec object.
            top = key.split(".", 1)[0]
            if top not in out:
                out.append(top)
    return out


def to_jsonable():
    """Return the registry as a plain JSON-serializable dict, for the
    /__kinds/registry endpoint and offline tooling."""
    return {"KINDS": KINDS, "STAGES": STAGES}
