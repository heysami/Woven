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

    # ── browser ───────────────────────────────────────────────────────────
    "browser": {
        "title":        "Web browser",
        "category":     "container",
        "inputs": {
            "url":   {"type": "text", "label": "URL", "userEditable": True, "required": True},
            "title": {"type": "text", "label": "Display name", "userEditable": True},
        },
        "outputs": {
            "text": {"type": "text", "required": False,
                     "doc": "The rendered page's readable text. Wire into an agent / skill as context, or clip the current selection into a prompt node."},
        },
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "inline-server-call",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False,
        "runStatusFlow": ["queued", "done", "error"],
        "completion":   {"requires": ["inputs.url loads (sites that refuse embedding are re-served via the daemon proxy)"]},
        "pauseAfter":   False,
        "notes": "Embedded public-website browser. Renders the page live inside the node; select the node to scroll / click / select text. The out port carries the page's readable text.",
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
            "set extendsGraph=True for visual-orchestrator-shaped subagents that "
            "scaffold downstream nodes."
        ),
        "perIdOverrides": {
            # ──────────────────────────────────────────────────────────────────
            # v3.5 — Onboarding cut. The guided-new-project pipeline (research,
            # PRD, DS, source-scaffold, brainstorm, coherence-pass, vision-verify)
            # was removed wholesale. The visual / simulation / interactive /
            # narrative orchestrators stay; their drawer overrides + per-id wildcards
            # are below. Chat dispatches orchestrators directly via Path A/B in
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

            # ── Hero-3d component drawers (wildcard prefixes) ──────────────────
            "h3d_research_": {
                "outputsRoot": "source/{prototype}/hero3d/{heroId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
                "notes": (
                    "Committed stack: integration mode, renderer config, post "
                    "chain, material cast, interaction grammar, quiet zone."
                ),
            },
            "h3d_material_": {
                "outputsRoot": "source/{prototype}/hero3d/{heroId}/materials.js",
                "completion": {"requires": [
                    "files: materials.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Material cast factories (transmission/chrome/iridescence). "
                    "Lens-gated on craft + aesthetic."
                ),
            },
            "h3d_scene_": {
                "outputsRoot": "source/{prototype}/hero3d/{heroId}/scene.js",
                "completion": {"requires": [
                    "files: scene.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": "World + lighting + camera + composition. Lens-gated.",
            },
            "h3d_interaction_": {
                "outputsRoot": "source/{prototype}/hero3d/{heroId}/interaction.js",
                "completion": {"requires": [
                    "files: interaction.js exists, non-empty",
                ]},
                "notes": (
                    "Damped pointer parallax / orbit / scroll-scrub. "
                    "Lens-gated on craft (passive listeners, no scroll trap)."
                ),
            },
            "h3d_runtime_": {
                "outputsRoot": "source/{prototype}/hero3d/{heroId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": "Composer + post chain + veil + harness. All three lenses.",
            },

            # ── Scene-3d component drawers (the SHARED WebGL render layer) ─────
            # scene-3d-orchestrator is to 3D what visual-orchestrator is to flat
            # assets. It fans the render work out by SUBSYSTEM: research emits a
            # subsystems[] decomposition, the orchestrator scaffolds one
            # s3d_subsystem_ node per entry (dispatched in PARALLEL), and each
            # one renders + is verified STANDALONE before composition. Generalises
            # + replaces the four bespoke 3D builders (h3d-scene-author /
            # sim-3d-scene-builder / game-world-builder / im-output-3d). Linked by
            # simulation / narrative / game / interactive-media / motion-studio for
            # their heavy-3D render; used directly for the hero slot. Output is a
            # DRIVABLE scene (window.__scene3d) the caller's loop can step().
            # Node-id convention: s3d_<component>_<sceneId>
            #   s3d_subsystem_loom_hero_thread-graph  (sceneId + sysId)
            "s3d_research_": {
                "outputsRoot": "source/{prototype}/scene3d/{sceneId}/research.md",
                "completion": {"requires": ["files: research.md exists, non-empty"]},
                "notes": (
                    "Committed stack + the subsystems[] decomposition: integration, "
                    "drive mode, SHARED renderer config, post chain, camera grammar, "
                    "quiet zone, perf rungs, and one subsystem entry per heavy effect."
                ),
            },
            "s3d_subsystem_": {
                "outputsRoot": "source/{prototype}/scene3d/{sceneId}/subsystems/{sysId}.js",
                "completion": {"requires": [
                    "files: subsystems/{sysId}.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "ONE effect's {geometry+material+sim}, rendered + verified "
                    "STANDALONE on the shared renderer/env before composition. "
                    "Dispatched in parallel, one per research subsystems[] entry. "
                    "Lens-gated craft+aesthetic (+concept for the lead subsystem)."
                ),
            },
            "s3d_interaction_": {
                "outputsRoot": "source/{prototype}/scene3d/{sceneId}/interaction.js",
                "completion": {"requires": [
                    "files: interaction.js exists, non-empty",
                ]},
                "notes": (
                    "Damped pointer parallax / orbit / scroll-scrub over the merged "
                    "subsystem handles. Render-only ambient when host-driven. "
                    "Lens-gated on craft (passive listeners, no scroll trap)."
                ),
            },
            "s3d_runtime_": {
                "outputsRoot": "source/{prototype}/scene3d/{sceneId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Composes all N subsystems under one renderer/env/post chain + "
                    "veil + harness; exposes the drivable scene API window.__scene3d "
                    "(self-driven rAF OR host-driven step()). All three lenses."
                ),
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
            "cp_h3d_material_pick_": {
                "outputsRoot": "DECISION_cp_h3d_material_pick_{heroId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_h3d_material_pick_{heroId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 lead-material drafts (iterator-remix).",
            },
            "cp_h3d_scene_pick_": {
                "outputsRoot": "DECISION_cp_h3d_scene_pick_{heroId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_h3d_scene_pick_{heroId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 camera-axis scene drafts (iterator-remix).",
            },
            "cp_h3d_runtime_pick_": {
                "outputsRoot": "DECISION_cp_h3d_runtime_pick_{heroId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_h3d_runtime_pick_{heroId}.json exists with non-empty values",
                ]},
            },
            "cp_s3d_subsystem_pick_": {
                "outputsRoot": "DECISION_cp_s3d_subsystem_pick_{sceneId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_s3d_subsystem_pick_{sceneId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 lead-subsystem drafts (iterator-remix).",
            },
            "cp_s3d_runtime_pick_": {
                "outputsRoot": "DECISION_cp_s3d_runtime_pick_{sceneId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_s3d_runtime_pick_{sceneId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 ambient-energy runtime drafts (iterator-remix).",
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
            "cp_h3d_gate_": {
                "outputsRoot": "DECISION_cp_h3d_gate_{heroId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_h3d_gate_{heroId}.json exists with non-empty values",
                ]},
                "notes": "Same as cp_sim_gate_ for hero-3d family.",
            },
            "cp_s3d_gate_": {
                "outputsRoot": "DECISION_cp_s3d_gate_{sceneId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_s3d_gate_{sceneId}.json exists with non-empty values",
                ]},
                "notes": "Same as cp_sim_gate_ for the shared scene-3d render layer.",
            },

            # ──────────────────────────────────────────────────────────────────
            # v3.3 — NARRATIVE-EXPERIENCE orchestrator (the poetic cousin of sim).
            # See docs/features/simulation-and-interactive-orchestrators.md
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
            # v3.3 — GAME-EXPERIENCE orchestrator (the fifth sibling).
            # See docs/features/game-experience-orchestrator.md.
            # Inherits simulation-orchestrator's contract shape with three
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
            # v3.3 — SCRAPBOOK-EXPERIENCE orchestrator (the sixth sibling).
            # See docs/features/scrapbook-experience-orchestrator.md.
            # Inherits simulation-orchestrator's contract shape with two
            # distinctives: (1) the composition drawer co-dispatches
            # visual-orchestrator per IMAGE INVENTORY entry —
            # this is the most visual-orchestrator-heavy drawer in the system;
            # (2) PNG sequences substitute for transparent GIFs (each frame
            # is a separate visual-orchestrator sub-dispatch). Node-id
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
                    "co-dispatch of visual-orchestrator per asset."
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
                    "visual-orchestrator per inventory entry "
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
                    "typography (commissioned via visual-orchestrator). "
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
            # v3.3 — INTERACTIVE-POLISH orchestrator (the seventh sibling — POST-PASS).
            # See docs/features/interactive-polish-orchestrator.md.
            # Unlike the other six orchestrators, this runs LAST in the pipeline:
            # after another primary orchestrator's build phase (or after chat-Claude
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
                    "Per orchestrator-vs-drawer split: identifies WHERE + TYPE only — "
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
                    "visual-orchestrator with the shader skill to commission the "
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

            # ──────────────────────────────────────────────────────────────────
            # MOTION-STUDIO orchestrator (library-backed — cinematic full-bleed
            # video/raster + UI choreographed as LINEAR full-screen scenes; the
            # Apple-product-page / motionsites register). Library:
            # docs/research/motion-scene-library.index.json → per-technique
            # entries at design-library/motion-<techniqueId>.md. Node-id
            # convention: ms_<component>_<msId>, e.g. ms_storyboard_hero_reveal.
            # Unique trigger shape: mode=brainstorm runs BEFORE the shell exists
            # (claims surfaces, returns ms-mount slot tags); mode=build is the
            # standard enumerate + scaffold pass. See motion-studio-orchestrator.md.
            # ──────────────────────────────────────────────────────────────────

            # ── Motion-studio component drawers (wildcard prefixes) ───────────
            "ms_research_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/research.md",
                "completion": {"requires": [
                    "files: research.md exists, non-empty",
                ]},
                "notes": (
                    "Single tech + choreography researcher. Commits binding "
                    "(self vs host-scroll) + assetPolicy (video-first vs "
                    "raster-first, validated against live provider "
                    "availability) + scene count (2-6) + per-scene technique "
                    "candidates from the motion-scene library index + "
                    "transition register + the opt-in multiDraftRecommendation."
                ),
            },
            "ms_storyboard_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/storyboard.json",
                "completion": {"requires": [
                    "files: storyboard.json exists, non-empty",
                    "files: storyboard.md exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "THE canonical scene-plan contract every downstream drawer "
                    "reads: linear scenes[] with techniqueId + asset spec "
                    "(medium, subjectAnchor, quietZone, interactionClause, "
                    "holdFrames) + ui placement + holdBeats + transitions. "
                    "§8.7 crux — 3-draft remix on the scene-split axis when "
                    "research recommends. Lens-gated on concept + aesthetic."
                ),
            },
            "ms_concept_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/concept/concept.json",
                "completion": {"requires": [
                    "files: concept/concept.json exists, non-empty",
                    "files: one concept/<sceneId>.png plate per storyboard scene, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "CONCEPT PLATES — the cheap-stills-before-expensive-video "
                    "planning gate. Per scene, ONE hi-res (1920x1080) generated "
                    "design plate of the full composed frame (asset + UI drawn "
                    "together, real copy) via visual-orchestrator co-dispatch, "
                    "then visually inspected to extract concept.json (observed "
                    "subject/UI positions, verified quiet zone, palette, type "
                    "tone, scrim needs, assetPromptNotes + uiBuildNotes). The "
                    "caller MUST surface the plates to the user (approve / "
                    "steer / re-draft) BEFORE dispatching ms_scenes_ — video "
                    "budget is only spent on approved plates, which become the "
                    "composition contract (and the i2v image reference where "
                    "the provider supports one). §8.7 crux — 3-draft remix on "
                    "the layout axis (counterweight / monumental-center / "
                    "cinema-band). Lens-gated on aesthetic + concept; craft "
                    "light. Plates are PLANS — production text ships as DOM, "
                    "never as pixels."
                ),
            },
            "ms_scenes_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/scenes.html",
                "completion": {"requires": [
                    "files: scenes.html exists, non-empty",
                    "files: scenes.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Commissions every storyboard asset via visual-orchestrator "
                    "co-dispatch AGAINST the user-approved concept plates "
                    "(assetPromptNotes reproduced in every prompt; plate passed "
                    "as i2v reference where supported; UI styled from "
                    "uiBuildNotes) (hi-res >=1920x1080 edge-to-edge; "
                    "subjectAnchor + quietZone + interactionClause INTO the "
                    "generation prompt; degradation ladder video -> raster-"
                    "sequence -> raster+CSS motion -> Hyperframes motion "
                    "LAST and only when research committed hyperframesEligible "
                    "(vector-native register; photoreal/immersive registers "
                    "stop at raster+CSS)), then "
                    "assembles full-bleed scene sections with UI in each "
                    "asset's quiet zone. All 3 lenses gate."
                ),
            },
            "ms_motion_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/motion.js",
                "completion": {"requires": [
                    "files: motion.js exists, non-empty",
                    "files: motion.css exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "The scene engine: linear back-and-forth stepper, "
                    "per-technique transitions, within-scene hold beats "
                    "(video pauses on authored frames while UI animates in), "
                    "entrance choreography, always-in-motion ambient duty, "
                    "reduced-motion branch. §8.7 crux — 3-draft remix on the "
                    "transition-register axis (seamless-cinematic / "
                    "staged-theatrical / kinetic-snap). All 3 lenses gate."
                ),
            },
            "ms_interactions_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/interactions.js",
                "completion": {"requires": [
                    "files: interactions.js exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "The input layer: pointer-x/xy scrub (eased pursuit), "
                    "wheel-step/swipe navigation events, host-scroll "
                    "postMessage bridge when binding=host-scroll (never traps "
                    "scroll), gyro/autonomous fallbacks. Emits events "
                    "__msMotion consumes; owns no scene state. Lens-gated on "
                    "craft only (<=50ms latency, passive listeners, debounce, "
                    "pointer-capture hygiene)."
                ),
            },
            "ms_runtime_": {
                "outputsRoot": "source/{prototype}/motionscenes/{msId}/runtime.html",
                "completion": {"requires": [
                    "files: runtime.html exists, non-empty",
                    "outputs.lensVerdict in {pass}",
                ]},
                "notes": (
                    "Composed runtime — wires scenes + motion + interactions, "
                    "implements the preload strategy (poster-first paint, "
                    "current+next preload, off-screen pause), reduced-motion + "
                    "failed-video fallbacks, and the §12.3 devtools harness "
                    "(window.__ms). §8.7 crux — remix on the pacing axis. "
                    "Full lens trio — this IS the user-facing artefact."
                ),
            },

            # ── Multi-draft pick checkpoints ──────────────────────────────────
            "cp_ms_storyboard_pick_": {
                "outputsRoot": "DECISION_cp_ms_storyboard_pick_{msId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_ms_storyboard_pick_{msId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 storyboard drafts (scene-split axis).",
            },
            "cp_ms_concept_pick_": {
                "outputsRoot": "DECISION_cp_ms_concept_pick_{msId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_ms_concept_pick_{msId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 concept-plate sets (layout axis), or approves/steers the single set at the mandatory plate-review gate.",
            },
            "cp_ms_motion_pick_": {
                "outputsRoot": "DECISION_cp_ms_motion_pick_{msId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_ms_motion_pick_{msId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 motion drafts (transition-register axis).",
            },
            "cp_ms_runtime_pick_": {
                "outputsRoot": "DECISION_cp_ms_runtime_pick_{msId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_ms_runtime_pick_{msId}.json exists with non-empty values",
                ]},
                "notes": "User picks 1 of 3 runtime drafts (pacing axis).",
            },

            # ── Family release gate ───────────────────────────────────────────
            "cp_ms_gate_": {
                "outputsRoot": "DECISION_cp_ms_gate_{msId}.json",
                "completion": {"requires": [
                    "files: DECISION_cp_ms_gate_{msId}.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads QUALITY_REPORT.json. If all lens verdicts for this "
                    "msId are pass, commits value='clear' and releases the "
                    "motion-studio container. On any block-fail at iteration "
                    "5, emits <decision-request> with Retry / Patch / "
                    "Accept-override. Direct clone of cp_sim_gate_ semantics."
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
            "visual-orchestrator via the Task tool, SCOPED TO THIS VARIANT'S "
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
            # Real node fields are canvasW/canvasH (the factory + sidecar
            # re-import use these); the old width/height keys never matched
            # anything on the node, so editable-field tracking missed the
            # canvas size. Mirror the actual schema.
            "layers":     {"type": "array",  "userEditable": True},
            "canvasW":    {"type": "number", "userEditable": True},
            "canvasH":    {"type": "number", "userEditable": True},
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

    # ── spline-3d ─────────────────────────────────────────────────────────
    # v4.0 — Inline 3D scene editor (three.js), rendered DIRECTLY as a node
    # like composer / vector-editor — no more run-a-skill-to-spawn-an-asset
    # two-step. The editor (editor/tools/spline3d/index.html) is embedded in an
    # iframe; the scene autosaves to a JSON sidecar at
    # source/<branch>/spline-<id>.scene.json (the canonical, shareable,
    # repo-resident artifact). Downstream consumers read bakedPath as a 3D
    # scene asset; an agent wired to the `edit` port rewrites the .scene.json
    # and the node re-imports it live. io contract lives in KIND_IO.
    "spline-3d": {
        "title":        "3D editor (Spline-style)",
        "category":     "container",
        "inputs": {
            "scene":   {"type": "object", "userEditable": True},   # last serialized scene (cache)
            "imports": {"type": "array",  "userEditable": False},  # linked .glb/.gltf asset paths
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
        "notes": (
            "User-driven inline 3D editor. The embedded three.js tool autosaves "
            "the scene to source/<branch>/spline-<id>.scene.json; downstream "
            "consumers read that sidecar as a 3D asset via bakedPath. An agent "
            "wired to the `edit` port may rewrite the .scene.json (read it, edit "
            "the JSON, write it back) and the node re-imports it live. "
            "SCENE JSON IS RIGGABLE + ANIMATABLE — do NOT tell the user it's a "
            "static/posed format. The MOTION IS NOT a fixed preset menu; YOU "
            "derive a rig + animation from the specific model you build, because "
            "you are the only thing that knows what it is (a giraffe's legs, an "
            "orca's spine). Schema: {v:1, "
            "objects:[{name:'legFL', kind, pos, rot(radians), scl, color, ...}], "
            "rig:{ joints:[{name, parent|null, pos:[x,y,z] world pivot}], "
            "bind:{'<partName>':'<jointName>'} }, "
            "anim:{ duration, loop, "
            "tracks:[{joint:'<name>', type:'rotation'|'position'|'scale', "
            "times:[s,..], values:[[x,y,z],..] (rotation = euler radians/key)}], "
            "ik:[{chain:['hip','knee'], effector:'foot', target:[x,y,z]}] }}. "
            "Parts bound to a joint follow it; rotating joints over keyframes is "
            "the animation. DERIVE motion from the model: a quadruped → hip/knee/"
            "ankle joints per leg + a gait of rotation keyframes (legs step, "
            "weight shifts); a fish/orca → a spine chain + a travelling "
            "undulation; a bird → wing joints + a flap. Do NOT slap one generic "
            "wiggle on every subject. Everything plays live AND bakes into glTF "
            "AnimationClips on Export .glb, so it survives into <model-viewer> / "
            "GLTFLoader on a website."
        ),
    },

    # ── App-node family (Phase: app-nodes) ────────────────────────────────
    # Eight new driven-view editors, all modelled on spline-3d/composer:
    # the iframe tool at editor/tools/<tool>/index.html owns NO persistence;
    # the node autosaves a JSON sidecar (the canonical, agent-editable file);
    # downstream consumers read bakedPath. io contracts live in KIND_IO.
    "font-editor": {
        "title":        "Font creator",
        "category":     "container",
        "inputs": {
            "font":      {"type": "object", "userEditable": True},   # serialized font spec (cache)
            "baseFont":  {"type": "object", "userEditable": True},
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
        "notes": "User-driven inline font editor (opentype.js). Pick a base font, edit glyphs as vector outlines or borrow glyphs from other fonts; bake compiles source/<branch>/fonts/font-<id>.otf. Agent edits source/<branch>/font-<id>.json.",
    },
    "image-editor": {
        "title":        "Image editor",
        "category":     "container",
        "inputs": {
            "doc":       {"type": "object", "userEditable": True},
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
        "notes": "User-driven raster painter with layers, free-lasso selection, per-pixel alpha-mask layer, and gradient-map. Bake flattens to source/<branch>/images/image-<id>.png. Agent edits source/<branch>/image-<id>.json (structure/grades/selection, not pixels).",
    },
    "pixel-editor": {
        "title":        "Pixel editor",
        "category":     "container",
        "inputs": {
            "doc":       {"type": "object", "userEditable": True},
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
        "notes": "User-driven pixel-art editor with a code/data generator mode AND a manual draw mode (also an ASCII canvas). Bake → source/<branch>/images/pixel-<id>.png (+ .txt in ASCII mode). Agent edits source/<branch>/pixel-<id>.json.",
    },
    "voxel-3d": {
        "title":        "Voxel editor",
        "category":     "container",
        "inputs": {
            "grid":      {"type": "object", "userEditable": True},
            "imports":   {"type": "array",  "userEditable": False},
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
        "notes": "User-driven voxel editor on a fixed grid (three.js), reusing the spline-3d material set (glass/metal/plastic + metaball/fur/cloth). Autosaves source/<branch>/voxel-<id>.json; exports .glb to models/. Agent edits the JSON.",
    },
    "synth": {
        "title":        "Synth / percussion",
        "category":     "container",
        "inputs": {
            "patch":     {"type": "object", "userEditable": True},
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
        "notes": "User-driven WebAudio synth + percussion engine for sound effects. Offline-renders a one-shot to source/<branch>/audio/synth-<id>.wav. Agent drives it by editing source/<branch>/synth-<id>.json (the patch).",
    },
    "music": {
        "title":        "Music maker",
        "category":     "container",
        "inputs": {
            "song":      {"type": "object", "userEditable": True},
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
        "notes": "User-driven algorithmic sample-based sequencer (Tidal/Strudel-style mini-notation). Samples come from wired audio assets / synth nodes. Offline-renders source/<branch>/audio/music-<id>.wav. Agent edits source/<branch>/music-<id>.json.",
    },
    "material-lab": {
        "title":        "Material Lab",
        "category":     "container",
        "inputs": {
            "doc":       {"type": "object", "userEditable": True},
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
        "notes": "User-driven 2D material/shader editor — UI elements with live materials (Apple Liquid Glass via WebGL refraction over a backdrop texture) that react to mouse / nearby elements / backdrop. Bakes an interactive source/<branch>/material-<id>.html. Agent edits source/<branch>/material-<id>.json.",
    },
    "mm-composer": {
        "title":        "Interactive multimedia composer",
        "category":     "container",
        "inputs": {
            "doc":       {"type": "object", "userEditable": True},
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
        "notes": "User-driven layered interactive surface. Each layer = {positioning · trigger · effects}: grid/instance/physics/drawn/rope/camera-feed positioning, mouse/timeline/audio/camera triggers that cross-affect layers, and GPU/shader effects (shader-lab taxonomy). Bakes interactive source/<branch>/mm-<id>.html. Agent edits source/<branch>/mm-<id>.json.",
    },

    # ── Composable spec nodes (Layer / Position / Trigger / Effect) ────────
    # Typed providers (like color-palette/typography): a small JSON `spec` on
    # the node flows into a host editor which APPLIES it. Also agent-editable
    # (editTarget → a JSON sidecar the node re-imports). io contracts in KIND_IO.
    "effect": {
        "title":        "Effect",
        "category":     "container",
        "inputs":       {"spec": {"type": "object", "userEditable": True}},
        "outputs":      {}, "outputsRoot": None, "consumeFrom": None,
        "dispatch":     "none", "fanOut": None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False, "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []}, "pauseAfter": False,
        "notes": "Composable GPU/shader post-effect (shader-lab taxonomy). Wire into a host editor's effect port; agent edits source/<branch>/effect-<id>.json.",
    },
    "position": {
        "title":        "Position",
        "category":     "container",
        "inputs":       {"spec": {"type": "object", "userEditable": True}},
        "outputs":      {}, "outputsRoot": None, "consumeFrom": None,
        "dispatch":     "none", "fanOut": None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False, "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []}, "pauseAfter": False,
        "notes": "Composable placement scheme (grid/instances/physics/drawn/rope/camera-feed + 3D modes). Wire into a host's position port; agent edits source/<branch>/position-<id>.json.",
    },
    "trigger": {
        "title":        "Trigger",
        "category":     "container",
        "inputs":       {"spec": {"type": "object", "userEditable": True}},
        "outputs":      {}, "outputsRoot": None, "consumeFrom": None,
        "dispatch":     "none", "fanOut": None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False, "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []}, "pauseAfter": False,
        "notes": "Composable reactivity source + cross-layer impacts (mouse/hover/position/timeline/audio/camera). Wire into a layer/host; agent edits source/<branch>/trigger-<id>.json.",
    },
    "layer": {
        "title":        "Layer",
        "category":     "container",
        "inputs":       {"spec": {"type": "object", "userEditable": True}},
        "outputs":      {}, "outputsRoot": None, "consumeFrom": None,
        "dispatch":     "none", "fanOut": None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": False, "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": []}, "pauseAfter": False,
        "notes": "One composition layer. Wire asset (content) + optional position/trigger/effect into its in-port, then wire its out into a host (mm-composer/image/composer). Agent edits source/<branch>/layer-<id>.json.",
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
    # See docs/features/simulation-and-interactive-orchestrators.md §6.4.
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
            "via re-dispatching simulation-orchestrator. "
            "Component children own their own files and lens verdicts; this "
            "container is marked done only when the orchestrator's commit carries "
            "outputs.lensVerdict='pass'."
        ),
    },

    # ── interactive-media (v3.3 — live iframe for TouchDesigner-grade pieces)
    # See docs/features/simulation-and-interactive-orchestrators.md §7.4.
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

    # ── hero-3d (v1.0 — live iframe for Spline-grade 3D hero scenes) ──────
    # The escalation container above the plain `3d` drawer trio. Routed by
    # visual-orchestrator's `3d-hero` classification or direct dispatch.
    # See `hero-3d-orchestrator.md` + docs/research/spline-grade-3d-study.md.
    "hero-3d": {
        "title":        "Hero 3D scene (live iframe)",
        "category":     "container",
        "inputs": {
            "heroId":         {"type": "text",   "userEditable": False, "required": True},
            "integration":    {"type": "enum",
                                "values": ["full-bleed", "inline-object",
                                           "scroll-scrubbed"],
                                "userEditable": False},
            "materialCast":   {"type": "array",  "userEditable": False},
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
        "graphExtensionScope": "component children (research/material/scene/interaction/runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a Spline-grade 3D hero scene. Run re-builds via "
            "re-dispatching hero-3d-orchestrator. materialCast lists the "
            "design-library materialIds the scene wears. Component children "
            "own their files + lens verdicts; this container is marked done "
            "only when the orchestrator's commit carries lensVerdict='pass'."
        ),
    },

    # ── scene-3d (v1.0 — the SHARED WebGL render layer) ──────────────────
    # Symmetric to visual-orchestrator but for 3D. Built by
    # scene-3d-orchestrator via a per-SUBSYSTEM fan-out (research → N parallel
    # s3d_subsystem_ chunks each rendering standalone → interaction → runtime).
    # Output is a DRIVABLE scene (window.__scene3d): self-driven for a hero
    # slot, or host-driven so a linking orchestrator (simulation / narrative /
    # game / interactive-media / motion-studio) drives the handles each frame
    # from its own loop. Replaces the four bespoke 3D builders.
    # See `scene-3d-orchestrator.md` + docs/research/spline-grade-3d-study.md.
    "scene-3d": {
        "title":        "Scene 3D (drivable WebGL render)",
        "category":     "container",
        "inputs": {
            "sceneId":        {"type": "text",   "userEditable": False, "required": True},
            "integration":    {"type": "enum",
                                "values": ["full-bleed", "inline-object",
                                           "scroll-scrubbed"],
                                "userEditable": False},
            "driveMode":      {"type": "enum",
                                "values": ["self-driven", "host-driven"],
                                "userEditable": False},
            "subsystems":     {"type": "array",  "userEditable": False},
            "handles":        {"type": "array",  "userEditable": False},
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
        "graphExtensionScope": "component children (research / subsystem ×N / interaction / runtime)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "The shared drivable-3D render container. Run re-builds via "
            "re-dispatching scene-3d-orchestrator. subsystems lists the render "
            "chunks; handles lists the entity/camera handles a host-driven "
            "caller drives via window.__scene3d.step(). Component children own "
            "their files + lens verdicts (each subsystem proves a standalone "
            "frame); this container is marked done only when the orchestrator's "
            "commit carries lensVerdict='pass'."
        ),
    },

    # ── narrative-experience (v3.3 — poetic cousin of `simulation`) ──────
    # The user-facing artefact container for one immersive walk-into-this-
    # place piece. Mirrors `simulation` shape with three substitutions:
    # spine (scripted timeline) instead of loop, camera-as-narrator instead
    # of free controls, ambient (soundscape) as a new first-class channel.
    # See `narrative-experience-orchestrator.md`.
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
    # drawer alongside world and runtime. See `game-experience-orchestrator.md`.
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
    # The composition drawer co-dispatches visual-orchestrator per
    # IMAGE INVENTORY entry — this is the most visual-orchestrator-heavy container
    # in the system. PNG sequences substitute for transparent GIFs (each frame
    # = one visual-orchestrator sub-dispatch). See `scrapbook-experience-orchestrator.md`.
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
        "graphExtensionScope": "component children (research/composition/typography/motion/interactions/runtime) + N visual-orchestrator-co-dispatched asset trios",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a raster-heavy collage piece. Aesthetics are "
            "named cores (vaporwave / cottagecore / dreamcore / Y2K / "
            "lo-fi / etc.) — the orchestrator DOES NOT serve CSS-driven aesthetics "
            "(Bauhaus / Swiss-grid / terminal-on-web etc.); those redirect to "
            "visual-orchestrator for hero assets in a CSS-restrained app. Composition "
            "drawer co-dispatches visual-orchestrator per IMAGE "
            "INVENTORY entry — N entries = N sub-dispatches. PNG sequences "
            "substitute for transparent GIFs (each frame = one sub-dispatch). "
            "Typography splits between web fonts (body / microtype via "
            "Google Fonts) + raster handlettering (display words / "
            "signatures / marker annotations via visual-orchestrator)."
        ),
    },

    # ── interactive-polish (v3.3 — seventh sibling; POST-PASS orchestrator) ────
    # Different shape from the other six: runs LAST in the pipeline, after
    # another primary orchestrator's build phase (or after chat-Claude has
    # hand-written source), BEFORE Step-8 QA. Reads existing source,
    # identifies SITES of opportunity for interactive enrichment, dispatches
    # per-type drawers that decide the SPECIFIC improvement. Writes
    # supplemental files to source/<branch>/_polish/<polishId>/ — existing
    # source stays intact; the caller applies minimal <link>/<script> edits
    # per host page from the runtime drawer's integration-instructions.md.
    # See `interactive-polish-orchestrator.md`.
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
                                    "doc": "Subset of {polish_microanimation_, polish_pointer_, polish_hover_, polish_shader_, polish_runtime_} that ran. Drawers may be SKIPPED if their type has 0 sites — unlike the other six orchestrators where every drawer fires."},
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
        "graphExtensionScope": "component children (research/microanimation/pointer/hover/shader/runtime) + optional visual-orchestrator-co-dispatched shader trio",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Post-pass enrichment container — runs after another primary "
            "orchestrator's build phase, before Step-8 QA. Existing source is "
            "preserved; polish files live in source/<branch>/_polish/<polishId>/. "
            "Each host page in pagesIntegrated received TWO new tags (a "
            "single <link> + a single <script>) — and ONE more <div> if the "
            "shader-overlay drawer ran. Zero-site outcomes (source already "
            "richly polished, no opportunity types identified) are valid; "
            "the runtime drawer writes an empty composite.css + composite.js "
            "+ integration-instructions.md saying 'no edits needed'. The "
            "interactive-polish container is the ONE post-pass artefact in "
            "the orchestrator system; the other six containers (prototype, "
            "simulation, interactive-media, narrative-experience, game-"
            "experience, scrapbook-experience) are primary build artefacts."
        ),
    },

    # ── motion-studio (library-backed — cinematic linear-scene presentation) ──
    # Presentation-first sections/pages: full-bleed generated video (or motion
    # raster) + UI choreographed as a LINEAR sequence of full-screen scenes
    # with within-scene hold beats. Library: docs/research/motion-scene-
    # library.index.json → design-library/motion-<techniqueId>.md. Unique
    # trigger shape: mode=brainstorm runs BEFORE the shell exists. See
    # `motion-studio-orchestrator.md`.
    "motion-studio": {
        "title":        "Motion studio (live iframe)",
        "category":     "container",
        "inputs": {
            "msId":              {"type": "text",   "userEditable": False, "required": True},
            "binding":           {"type": "enum",
                                   "values": ["self", "host-scroll"],
                                   "userEditable": False,
                                   "doc": "self: the iframe owns wheel/swipe scene stepping (full-page pieces). host-scroll: the host forwards scroll progress via postMessage; the iframe never traps scroll (sections inside a scrolling page)."},
            "assetPolicy":       {"type": "enum",
                                   "values": ["video-first", "raster-first"],
                                   "userEditable": False,
                                   "doc": "Committed by research against live provider availability. Degradation ladder: video → raster-sequence → raster + CSS motion → Hyperframes motion (LAST, genre-gated: only vector-native registers; photoreal/immersive registers stop at raster + CSS)."},
            "sceneCount":        {"type": "number", "userEditable": False,
                                   "doc": "Linear full-screen scenes (2–6, presentation-first)."},
            "transitionRegister": {"type": "enum",
                                    "values": ["seamless-cinematic",
                                               "staged-theatrical",
                                               "kinetic-snap"],
                                    "userEditable": False,
                                    "doc": "Picked at the §8.7 motion crux when research recommends; otherwise from research."},
            "assetCount":        {"type": "number", "userEditable": False,
                                   "doc": "Total generated assets (videos + stills + sequence frames + parallax layers) commissioned via visual-orchestrator co-dispatch."},
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
        "graphExtensionScope": "component children (research/storyboard/concept/scenes/motion/interactions/runtime) + N visual-orchestrator-co-dispatched plate + asset trios",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.lensVerdict in {pass}",
            "outputs.iterationCount non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Live iframe of a cinematic linear-scene presentation piece — "
            "the Apple-product-page / motionsites register. The aesthetic "
            "payload is tightly choreographed full-bleed video/raster + UI; "
            "the piece MUST NOT be complex (no app features, no data, no "
            "branching) — linear back-and-forth scene stepping only, with "
            "within-scene hold beats (video pauses on an authored frame, UI "
            "animates in, next input releases). Hard composition law: assets "
            "generate hi-res (>=1920x1080) edge-to-edge with subjectAnchor + "
            "quietZone + interactionClause IN the generation prompt, and UI "
            "placement follows the asset's composition (subject right → UI "
            "left). Always >=1 living layer per scene at rest; all video "
            "muted+playsinline; no audio, no permission gates. Per scene, a "
            "hi-res CONCEPT PLATE (full composed frame, UI included) is "
            "generated and user-approved BEFORE any video budget is spent; "
            "the approved plate is the composition contract asset generation "
            "+ UI build + Step-8 QA obey. Scene assets are then commissioned "
            "via visual-orchestrator co-dispatch per storyboard entry."
        ),
    },

    # ── photography-enrichment (container) ───────────────────────────────
    # The user-facing artefact container for one photography art-direction
    # pass. Committed by photography-orchestrator AFTER every pe_photo_<slotId>
    # enrichment node is done. visual-orchestrator finds enrichments by id
    # pattern, not by edges — this container is the audit surface, not a
    # dependency hub. See `photography-orchestrator.md §4`.
    "photography-enrichment": {
        "title":        "Photography enrichments",
        "category":     "container",
        "inputs": {
            "projectId":   {"type": "text",   "userEditable": False, "required": True},
            "totalSlots":  {"type": "number", "userEditable": False,
                             "doc": "Photographic slots enriched (one pe_photo_<slotId> node each)."},
            "stylesUsed":  {"type": "array",  "userEditable": False,
                             "doc": "Library styleIds picked across slots (one or two per project for coherence)."},
            "boundTo":     {"type": "object", "userEditable": False,
                             "doc": "{documentSetId: <branch>} — which source branch the enrichments target."},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "pe_photo_<slotId> enrichment nodes (one per photographic slot)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.enrichmentNodes non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Art-direction pre-pass container — committed BEFORE "
            "visual-orchestrator's per-medium dispatch. Each pe_photo_<slotId> "
            "child carries a paste-ready promptForRasterPhoto + negativePrompt "
            "+ film/lens/lighting/mood hints sourced from the photography "
            "library's per-entry file (design-library/photo-<styleId>.md). "
            "visual-orchestrator Step 0a reads the children by id pattern; no "
            "edges connect the two orchestrators. Degrade-gracefully: when "
            "this container is absent, raster-photo drawers proceed with "
            "default prompts."
        ),
    },

    # ── illustration-enrichment (container) ──────────────────────────────
    # Sibling of photography-enrichment — same shape, illustration library.
    # See `illustration-orchestrator.md §3`.
    "illustration-enrichment": {
        "title":        "Illustration enrichments",
        "category":     "container",
        "inputs": {
            "projectId":      {"type": "text",   "userEditable": False, "required": True},
            "totalSlots":     {"type": "number", "userEditable": False,
                                "doc": "Illustrative slots enriched (one pe_illust_<slotId> node each)."},
            "stylesUsed":     {"type": "array",  "userEditable": False,
                                "doc": "Library styleIds picked across slots."},
            "categoriesUsed": {"type": "array",  "userEditable": False,
                                "doc": "Library categories in play (3D / flat-vector / hand-drawn / anime / ...)."},
            "boundTo":        {"type": "object", "userEditable": False,
                                "doc": "{documentSetId: <branch>}."},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "pe_illust_<slotId> enrichment nodes (one per illustrative slot)",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.enrichmentNodes non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Art-direction pre-pass container — committed BEFORE "
            "visual-orchestrator's per-medium dispatch. Each pe_illust_<slotId> "
            "child carries promptForRasterForeground + negativePrompt + "
            "material/line/color/role hints from the illustration library's "
            "per-entry file (design-library/illust-<styleId>.md). "
            "visual-orchestrator Step 0a reads the children by id pattern when "
            "dispatching raster-foreground / depictive vector-mark. May coexist "
            "with photography-enrichment on the same project (different slots)."
        ),
    },

    # ── creative-visual-promotion (container) ────────────────────────────
    # Post-pass container — flat <img> slots promoted into creative
    # compositions (text-as-mask, asset-bleed, clip-path, drop-cap, bullets,
    # cut-into-letters). Editorial-loud aesthetics only.
    # See `creative-visual-orchestrator.md §5`.
    "creative-visual-promotion": {
        "title":        "Creative visual promotions",
        "category":     "container",
        "inputs": {
            "projectId":                  {"type": "text",   "userEditable": False, "required": True},
            "promotionCount":             {"type": "number", "userEditable": False},
            "promotionsApplied":          {"type": "array",  "userEditable": False,
                                            "doc": "Promotion types applied: text-as-mask / asset-bleed-into-paragraph / irregular-clip-path / asset-as-drop-cap / asset-as-bullet / asset-cut-into-letters."},
            "supplementalAssetsGenerated":{"type": "number", "userEditable": False,
                                            "doc": "Masking-geometry / replacement assets co-dispatched through visual-orchestrator."},
            "stylesReplaced":             {"type": "number", "userEditable": False,
                                            "doc": "Slots whose photo/illust style was re-picked to fit the promoted composition."},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "cv_<slotId> promotion nodes + optional visual-orchestrator-co-dispatched supplemental asset trios",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.promotionNodes non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Post-pass promotion container — runs AFTER visual-orchestrator "
            "completes, BEFORE material-orchestrator and interactive-polish. "
            "Gated on editorial-loud / typography-driven aesthetics (or "
            "explicit user request). Each cv_<slotId> child rewrites the host "
            "HTML (SVG mask / clip-path / pseudo-element composition) and "
            "appends supplemental CSS; outputs.hostHTMLChanges records each "
            "file touched with a diff summary."
        ),
    },

    # ── material-fidelity (container) ─────────────────────────────────────
    # Late-pass container — material aesthetics (glass / clay / chrome /
    # holographic / paper / grain / glitch / ...) implemented per element with
    # reactive behaviours, within the committed reactiveBudget.
    # See `material-orchestrator.md §4`.
    "material-fidelity": {
        "title":        "Material fidelity pass",
        "category":     "container",
        "inputs": {
            "projectId":        {"type": "text",   "userEditable": False, "required": True},
            "materialCount":    {"type": "number", "userEditable": False,
                                  "doc": "Elements that received a material assignment (one mat_<elementHash> node each)."},
            "materialsUsed":    {"type": "array",  "userEditable": False,
                                  "doc": "Library materialIds assigned across elements."},
            "reactiveBudget":   {"type": "enum",
                                  "values": ["subtle", "rich", "theatrical"],
                                  "userEditable": False,
                                  "doc": "Committed via decision-request: how much input-driven reactivity (pointer / scroll / gyro)."},
            "permissionGates":  {"type": "array",  "userEditable": False,
                                  "doc": "Permissions the reactive layer requests behind a user gesture (e.g. gyro)."},
            "additionalAssets": {"type": "number", "userEditable": False,
                                  "doc": "Textures / shaders / videos co-commissioned via visual-orchestrator for materials."},
        },
        "outputs":      {},
        "outputsRoot":  None,
        "consumeFrom":  None,
        "dispatch":     "none",
        "fanOut":       None,
        "visibility":   {"transcript": False, "chatPanel": False, "perChildKill": False},
        "extendsGraph": True,
        "graphExtensionScope": "mat_<elementHash> implementation nodes + optional visual-orchestrator-co-dispatched texture/shader trios",
        "runStatusFlow": ["queued", "done"],
        "completion":   {"requires": [
            "outputs.materialNodes non-empty",
        ]},
        "pauseAfter":   False,
        "notes": (
            "Late material pass — runs AFTER visual-orchestrator + "
            "creative-visual-orchestrator (if any), BEFORE interactive-polish "
            "and Step-8 QA. Implementation files live in "
            "source/<branch>/_material/<elementHash>.{css,svg,glsl,js}, "
            "concatenated into composite.css + composite.js per page "
            "(outputs.compositeCSSPath / compositeJSPath). Honours "
            "prefers-reduced-motion and keeps every reactive behaviour inside "
            "the committed reactiveBudget."
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


# ─── the edge I/O contract (single source of truth) ────────────────────────
#
# `KIND_IO` declares, per kind, how that kind behaves on a workflow EDGE — what
# it PROVIDES to downstream consumers and what it ACCEPTS from upstream / from
# an agent wiring INTO it. This is the one table that the three previously
# divergent sites read:
#   1. serve.py's agent/skill dispatch (kinds/io_resolve.py walks it to build
#      the <context> and <output-destinations> blocks for the running agent),
#   2. the frontend connect-menu + edge-compatibility (derived from `tags`),
#   3. the section bundle resolver (recurses through provider `resolve`s).
#
# Because all three read THIS table, adding a new node kind needs only a new
# KIND_IO entry — the agent node, edge typing, and dispatch adapt with zero
# other code changes. See kinds/NODE_IO_FRAMEWORK.md for the full guide.
#
# Port entry shape:
#   provides[]: {port, label, tags[], resolve?, resolveArgs?}
#       resolve ∈ text | folder | webfetch | bakedFile | assetFile | typed |
#                 dsRef | sectionBundle   (omit → frontend-only, no upstream
#                 context contribution)
#   accepts[]:  {port, label, tags[], ingest?, canonical?}
#       ingest  ∈ context | assetWrite | folderWrite | editTarget | sectionWrite
#       canonical (editTarget only): path template the agent edits & the editor
#                 re-imports. {branch}/{id} resolved like outputsRoot.
#
# `tags` is the single merged vocabulary (text/text-gen/asset/asset-gen/palette/
# typography/folder/section/3d/remixable/blendable/folder-write/…). Two ports
# are compatible when their tag sets intersect (or either is empty = wildcard).
#
# `authoring` (editTarget ports only) is the instruction an agent receives so it
# can actually PRODUCE the target's content — what the node IS, the canonical
# file's SCHEMA, and the production modes. Without this an agent wired to a
# complex editor has no idea what format to write and falls back to generic
# motion/HTML generation (the "agent made a 2D thing in the 3D editor" bug).
# {branch}/{id} are resolved like outputsRoot; JSON braces in the schema are
# left intact (token-replace, not str.format).
_SPLINE_AUTHORING = (
    "Accepts: a 3D SCENE, in one of exactly two forms (produce one). It is a "
    "Spline-style WebGL scene editor; the only things it can render are the scene "
    "JSON below or an imported mesh — that JSON (or registered .glb) IS the deliverable.\n"
    "  (A) Scene JSON at `source/{branch}/spline-{id}.scene.json`, in EXACTLY this schema "
    "(loaded directly; re-imported live on write):\n"
    "      {\"v\":1,\n"
    "       \"objects\":[{\"name\":\"<unique part name>\",\"kind\":\"box|sphere|cylinder|cone|torus|torusknot|icosahedron|pyramid|helix\","
    "\"pos\":[x,y,z],\"rot\":[x,y,z],\"scl\":[x,y,z],\"mode\":\"solid|toon|matcap|normal|fresnel\","
    "\"color\":\"#rrggbb\",\"rough\":0.0,\"metal\":0.0,\"trans\":0.0,\"ior\":1.5}],\n"
    "       \"rig\":{\"joints\":[{\"name\":\"<jointName>\",\"parent\":\"<parentJointName|null>\",\"pos\":[x,y,z]}],"
    "\"bind\":{\"<partName>\":\"<jointName>\"}},\n"
    "       \"anim\":{\"duration\":<sec>,\"loop\":true,\"tracks\":[{\"joint\":\"<jointName>\","
    "\"type\":\"rotation|position|scale\",\"times\":[t0,t1,..],\"values\":[[x,y,z],..]}],"
    "\"ik\":[{\"chain\":[\"<joint>\",..],\"effector\":\"<joint>\",\"target\":[x,y,z]}]},\n"
    "       \"blob\":null}\n"
    "      Build the subject by composing/transforming/colouring those primitives. Units ~metres; "
    "the camera frames about -3..3. Each object needs at least kind+pos; other fields are optional.\n"
    "      ANIMATION IS SUPPORTED — this format is NOT static/posed-only; never tell the user otherwise. "
    "DERIVE the rig + motion FROM THE MODEL YOU BUILT (you know which parts are legs / spine / wings — "
    "do NOT apply one generic wiggle to everything):\n"
    "        • `rig.joints` is a parented skeleton; each joint's `pos` is its WORLD pivot. `rig.bind` "
    "attaches a named part to a joint so the part follows that joint (give every animated part a "
    "`name`). Rotating joints over `anim.tracks` keyframes IS the animation (rotation values are "
    "euler radians per key).\n"
    "        • Quadruped (giraffe/dog) → hip/knee/ankle joints PER LEG + a gait: legs swing fore/aft "
    "(rotate about the side axis) out of phase, weight shifts. Fish/orca → a head→tail SPINE chain + a "
    "travelling undulation (a fish wags side-to-side = rotate about the vertical Y axis; a whale/orca/"
    "dolphin pumps up-and-down = rotate about the lateral X axis), amplitude growing toward the tail, "
    "phase increasing down the chain. Bird → wing joints + a flap. Floating/idle object → gentle "
    "position/rotation tracks.\n"
    "        • Optional `anim.ik`: the editor solves the chain so the effector joint reaches `target` "
    "(use for planting a foot/hand). Everything plays live AND bakes into glTF clips on Export.\n"
    "  (B) A textured .glb under `source/{branch}/spline-imports/`, whose source-relative path you "
    "then register on this node: POST /__workflow/node/{id}/status {\"imports\":[\"source/{branch}/spline-imports/<file>.glb\"]} "
    "(only a .glb you actually created)."
)

_COMPOSER_AUTHORING = (
    "This is a COMPOSER — a responsive layered CANVAS that composites WIRED ASSET NODES "
    "into a stack. It is NOT an HTML/CSS layout surface: it CANNOT render text, shapes, "
    "buttons, gradients, or CSS you write inline. The ONLY thing it draws is a list of "
    "layers, and EVERY layer must be backed by an asset node wired into this composer's "
    "input — so the composer JSON places assets, it does not author content.\n"
    "  HARD RULE — each `layers[].assetId` MUST equal the node id of an asset already "
    "wired into this composer. A layer whose `assetId` is not wired in is DROPPED at bake; "
    "a composer with no wired assets bakes to nothing but its `background`. So if the brief "
    "needs imagery/video that is not wired yet, you must FIRST create the asset nodes (generate "
    "the images, e.g. via the visual pipeline) and wire them into this composer — do NOT invent "
    "inline layer content, and do NOT fabricate assetIds. If nothing is wired, say so rather than "
    "writing dead layers.\n"
    "  Write the canonical file `source/{branch}/composer-{id}.json` (read the existing file first; "
    "re-imported live on write). ONLY these keys are honored:\n"
    "      {\"canvasW\":<px>,\"canvasH\":<px>,\"maxWidth\":<px|null>,\"maxHeight\":<px|null>,"
    "\"background\":\"<css color or gradient>\",\n"
    "       \"layers\":[{\"assetId\":\"<id of a WIRED asset node>\",\"opacity\":0..1,"
    "\"anchor\":\"top-left|top-center|top-right|middle-left|center|middle-right|bottom-left|"
    "bottom-center|bottom-right|fill|stretch-h|stretch-v\",\"offsetX\":<px>,\"offsetY\":<px>,"
    "\"width\":<px|null>,\"height\":<px|null>,\"visible\":true}]}\n"
    "  Array order is z-order (later = on top). `width`/`height` null = natural size; `fill` covers "
    "the canvas, `stretch-h`/`stretch-v` span one axis. Preserve the assetIds of layers already "
    "present. Any other key (type/text/shape/button/css/responsive/layout) is ignored — there is no "
    "such thing as a text or shape layer here.\n"
    "  TEXT — the composer has NO text primitive, so raw text NEVER renders. To put a headline / "
    "label / body text into the composition you MUST first produce a text-bearing ASSET and wire it "
    "in as a layer: either a `formatted-text` node (it bakes to an HTML asset) or an `svg` asset that "
    "renders the words as <text>/paths (a raster image with the text baked in also works). Create that "
    "asset, wire its output into this composer's input, then add a layer referencing its assetId. Do "
    "NOT write the text as a layer field and expect it to show — it will be dropped.\n"
    "  For a hero SECTION with live, selectable text + CTAs, the composer is the WRONG medium; that "
    "is a prototype/HTML job."
)

_VECTOR_AUTHORING = (
    "This is a VECTOR EDITOR — an inline-SVG drawing surface. Unlike the composer it DOES author "
    "content directly: the deliverable is the `shapes[]` array, which bakes to a self-contained .svg "
    "(no wired assets needed). It is a VECTOR illustration tool — do NOT produce a raster/photo, a "
    "motion/HTML asset, or anything that is not SVG shapes.\n"
    "  Write the canonical file `source/{branch}/svg/vector-{id}.json` (read the existing file first; "
    "re-imported live on write). ONLY these keys are honored:\n"
    "      {\"canvasW\":<px>,\"canvasH\":<px>,\"background\":\"<css color>\",\"shapes\":[ ... ]}\n"
    "  Coordinates are in canvas units (the viewBox is canvasW×canvasH). Every shape carries a unique "
    "`id` plus optional style fields: `fill`,`stroke`,`strokeWidth`,`strokeDasharray`,`strokeLinecap`,"
    "`opacity`(0..1),`rotation`(deg),`name`,`visible`(default true),`locked`,`shadow`,`blur`. "
    "Shape types + their geometry:\n"
    "      • rect    — {\"type\":\"rect\",\"x\":,\"y\":,\"w\":,\"h\":,\"rx\":<corner radius, optional>}\n"
    "      • ellipse — {\"type\":\"ellipse\",\"cx\":,\"cy\":,\"rx\":,\"ry\":}\n"
    "      • line    — {\"type\":\"line\",\"x1\":,\"y1\":,\"x2\":,\"y2\":}\n"
    "      • path    — {\"type\":\"path\",\"d\":\"<SVG path data>\"}  (the workhorse for any custom curve)\n"
    "      • text    — {\"type\":\"text\",\"x\":,\"y\":,\"content\":\"...\",\"fontSize\":,\"fontWeight\":,"
    "\"textAnchor\":\"start|middle|end\",\"fontFamily\":\"<family id>\"}\n"
    "  Compose the illustration from these primitives; array order is paint order (later = on top)."
)

_FONT_AUTHORING = (
    "This is a FONT CREATOR (opentype.js). The deliverable is a font spec whose glyph outlines "
    "are SVG path data in FONT UNITS (y-up, origin at the baseline). It is NOT a raster/illustration "
    "tool — produce glyph outlines, not pictures.\n"
    "  Write the canonical file `source/{branch}/font-{id}.json` (read the existing file first; "
    "re-imported live on write). Schema:\n"
    "      {\"v\":1,\"familyName\":\"...\",\"unitsPerEm\":1000,\"ascender\":800,\"descender\":-200,\n"
    "       \"baseFont\":{\"source\":\"upload|google|none\",\"ref\":\"<google family name or asset path>\"},\n"
    "       \"glyphs\":{\"A\":{\"from\":\"base|font:<ref>|custom\",\"advanceWidth\":600,\"path\":\"<SVG path data, font units, y-up>\"}}}\n"
    "  `glyphs` is keyed by the character. `from:\"base\"` keeps the base font's outline; `from:\"custom\"` "
    "uses your `path`; `from:\"font:<google family>\"` borrows that character from another font (the tool "
    "resolves it). Only include glyphs you change — unlisted characters fall back to the base font. "
    "Coordinates are in font units (unitsPerEm tall); the baseline is y=0, ascenders are POSITIVE y."
)

_IMAGE_AUTHORING = (
    "This is an IMAGE EDITOR — a layered raster compositor. You author the layer STRUCTURE, gradient-map "
    "grades, blend/opacity, and lasso selection — you do NOT paint pixels (raster pixel data lives in "
    "referenced PNGs the user/asset pipeline produces). Do not invent pixel content inline.\n"
    "  Write the canonical file `source/{branch}/image-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"w\":1024,\"h\":1024,\n"
    "       \"layers\":[\n"
    "         {\"id\":\"l1\",\"name\":\"paint\",\"type\":\"raster\",\"src\":\"image-{id}/l1.png\",\"opacity\":1,\"blend\":\"normal|multiply|screen|overlay\",\"visible\":true},\n"
    "         {\"id\":\"m1\",\"name\":\"mask\",\"type\":\"alpha-mask\",\"target\":\"l1\",\"src\":\"image-{id}/m1.png\"},\n"
    "         {\"id\":\"g1\",\"name\":\"grade\",\"type\":\"gradient-map\",\"target\":\"l1\",\"stops\":[{\"t\":0,\"color\":\"#000\"},{\"t\":1,\"color\":\"#fff\"}]}\n"
    "       ],\n"
    "       \"selection\":{\"type\":\"lasso\",\"points\":[[x,y],[x,y]]}}\n"
    "  Array order is z-order (later = on top). A gradient-map layer maps its target's luminance through "
    "the color `stops` (t in 0..1). An alpha-mask layer multiplies its target's alpha by the mask's luminance."
)

_PIXEL_AUTHORING = (
    "This is a PIXEL editor. Pixels can be DECLARED by data/code (Data-Pixels style) or drawn manually; "
    "you produce the data. In ASCII mode the palette entries are glyphs instead of colors.\n"
    "  Write the canonical file `source/{branch}/pixel-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"w\":32,\"h\":32,\"mode\":\"code|draw\",\"scale\":12,\n"
    "       \"palette\":[\"#00000000\",\"#1a1c2c\",\"#5d275d\"],   (or [\" \",\".\",\"#\",\"@\"] for ASCII)\n"
    "       \"pixels\":\"<w*h palette indices, row-major, as a JSON array OR a compact run-length string 'count:index,...'>\",\n"
    "       \"code\":\"(x,y)=>/* return a palette index */ ((x^y)&7)\"}\n"
    "  In `mode:\"code\"` the `code` arrow-function is evaluated per cell (x,y from 0) and must return a "
    "palette index; in `mode:\"draw\"` the `pixels` grid is authoritative. Index 0 is conventionally "
    "transparent/empty. Keep w*h reasonable (<=256x256)."
)

_VOXEL_AUTHORING = (
    "This is a VOXEL editor — voxels on a fixed integer grid (a Minecraft/MagicaVoxel-style block scene). "
    "It reuses the 3D editor's materials but the geometry is voxels only; do NOT emit free meshes or "
    "primitives. The deliverable is the voxel list + palette.\n"
    "  Write the canonical file `source/{branch}/voxel-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"grid\":[64,64,64],\"voxelSize\":1,\n"
    "       \"palette\":[{\"color\":\"#aabbcc\",\"mode\":\"solid|glass|metal|plastic\",\"rough\":0.5,\"metal\":0,\"trans\":0}],\n"
    "       \"voxels\":[[x,y,z,paletteIndex]],   (sparse; only filled cells. A compact run string is also accepted: 'x,y,z,idx;...')\n"
    "       \"blob\":null,\"fur\":null,\"cloth\":null}\n"
    "  Coordinates are integer grid cells 0..grid-1 (y-up). Build the subject by filling cells and assigning "
    "each a palette index. `blob`/`fur`/`cloth` mirror the 3D editor's optional effects and may stay null."
)

_SYNTH_AUTHORING = (
    "This is a SYNTH / percussion patch (WebAudio). The deliverable is a patch the tool renders to audio; "
    "do NOT write an audio file yourself — describe the synth, the tool renders the .wav.\n"
    "  Write the canonical file `source/{branch}/synth-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\n"
    "       \"voice\":{\"osc\":[{\"type\":\"sine|saw|square|triangle|noise\",\"detune\":0,\"gain\":0.6}],\n"
    "                 \"filter\":{\"type\":\"lowpass|highpass|bandpass\",\"cutoff\":1200,\"q\":1},\n"
    "                 \"amp\":{\"a\":0.01,\"d\":0.2,\"s\":0.5,\"r\":0.3},\n"
    "                 \"fx\":[{\"type\":\"reverb|delay|drive\",\"wet\":0.2}]},\n"
    "       \"percussion\":{\"mode\":false,\"pitchEnv\":[200,40],\"noise\":0.5},\n"
    "       \"render\":{\"note\":\"C3\",\"durationMs\":800}}\n"
    "  ADSR times are seconds. For percussion set `percussion.mode:true` (a kick = noise + a fast downward "
    "`pitchEnv`; a snare = noise-heavy + short decay). `render` is the one-shot the bake produces."
)

_MUSIC_AUTHORING = (
    "This is an ALGORITHMIC MUSIC maker — a sample sequencer using Tidal/Strudel-style mini-notation. "
    "The deliverable is the song spec; the tool renders the audio.\n"
    "  Write the canonical file `source/{branch}/music-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"bpm\":120,\"swing\":0,\"bars\":4,\n"
    "       \"samples\":[{\"id\":\"bd\",\"src\":\"<wired audio asset path, or synth:<node id>>\"}],\n"
    "       \"tracks\":[{\"name\":\"drums\",\"pattern\":\"bd ~ sd ~ bd bd sd ~\",\"gain\":0.9},\n"
    "                   {\"name\":\"bass\",\"pattern\":\"c2 ~ eb2 g2\",\"instrument\":\"synth:<node id>\"}]}\n"
    "  In a `pattern` string, tokens are sample ids (or note names for an `instrument`), `~` is a rest, "
    "and the tokens are spread evenly across one bar (space-separated steps). Samples must reference a "
    "wired audio asset or a wired synth node — do NOT fabricate sample sources."
)

_MATERIAL_AUTHORING = (
    "This is MATERIAL LAB — a 2D surface of UI ELEMENTS, each wearing a live SHADER MATERIAL (Apple "
    "Liquid Glass and friends) that refracts the backdrop and reacts to the mouse / nearby elements / "
    "what is behind it. You author the elements + their material params + reactivity; the tool renders "
    "the WebGL. Do NOT write CSS backdrop-filter — the material IS a refraction shader.\n"
    "  Write the canonical file `source/{branch}/material-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"canvasW\":1200,\"canvasH\":800,\"background\":\"#111\",\n"
    "       \"elements\":[{\"id\":\"E1\",\"name\":\"card\",\"shape\":\"squircle|rounded-rect|circle|path\",\n"
    "         \"rect\":[x,y,w,h],\"radius\":28,\"z\":0,\n"
    "         \"content\":{\"kind\":\"asset|text|color\",\"assetId\":\"<wired node id>\",\"text\":\"...\",\"color\":\"#fff\"},\n"
    "         \"material\":{\"type\":\"liquid-glass|frosted|holographic|metal|chrome|plastic\",\"ior\":1.5,\"thickness\":12,\n"
    "                     \"profile\":\"squircle|convex|concave|lip\",\"refraction\":0.7,\"dispersion\":0.3,\"frost\":0.2,\"specular\":0.6,\"tint\":\"#ffffff22\"},\n"
    "         \"reactivity\":{\"mouse\":true,\"neighbors\":true,\"backdrop\":true,\"mouseDrives\":[\"lightDir\",\"refraction\"],\"neighborRadius\":120}}]}\n"
    "  `profile:\"squircle\"` (Apple's preference) gives the smoothest bezel. `refraction` scales the "
    "backdrop displacement, `dispersion` the edge chromatic aberration, `frost` the blur, `specular` the "
    "rim light. Elements refer to wired asset nodes by id for their content."
)

_MM_AUTHORING = (
    "This is the INTERACTIVE MULTIMEDIA COMPOSER — a stack of LAYERS where each layer = "
    "{content + positioning + trigger + effects}. You author the whole reactive graph in JSON; the tool "
    "runs it per frame. Content that is an asset MUST reference a node wired into this composer (like the "
    "plain composer) — do not fabricate assetIds.\n"
    "  Write the canonical file `source/{branch}/mm-{id}.json` (read it first; re-imported live). Schema:\n"
    "      {\"v\":1,\"canvasW\":1280,\"canvasH\":720,\"background\":\"#000\",\"inputs\":{\"camera\":false,\"mic\":false},\n"
    "       \"layers\":[{\"id\":\"L1\",\"name\":\"...\",\"z\":0,\"visible\":true,\n"
    "         \"content\":{\"kind\":\"asset|text|shape|generator\",\"assetId\":\"<wired node>\",\"text\":\"...\"},\n"
    "         \"positioning\":{\"mode\":\"single|grid|instances|physics|drawn|rope|camera-feed|face-3d\", ...mode params },\n"
    "         \"trigger\":{\"source\":\"none|mouse-click|hover|position|timeline|audio|camera\", ...source params,\n"
    "             \"impacts\":[{\"target\":\"<layer id>\",\"param\":\"opacity|scale|position|effect.intensity\",\"map\":\"linear|threshold\",\"range\":[0,1]}]},\n"
    "         \"effects\":{\"stack\":[{\"type\":\"pixel-mosh|chromatic-aberration|particle-float|halftone|ascii|displace|bloom|shader\",\"params\":{},\"glsl\":\"<optional custom fragment shader>\",\"intensity\":1}]}\n"
    "       }]}\n"
    "  positioning modes: grid {cols,rows,placement:'fixed|random'}; instances {source:'mouse|random|interaction',count,physics:true}; "
    "physics {engine:'matter',gravity:[0,1]}; drawn {paths:[[x,y]]}; rope {anchors,segments,stiffness}; "
    "camera-feed {detector:'hand|face|object|ocr',source:'camera|video:<assetId>'}; face-3d {meshId:'<voxel/spline node>'}. "
    "trigger.audio {sourceId:'<synth/music/audio node>',feature:'loudness|pitch|band'}; trigger.camera {detector,event:'present|gesture|count'}; "
    "trigger.timeline {keys:[{t,...}],loop:true}. A trigger's `impacts` route its value onto OTHER layers' params — "
    "that is how layers cross-affect. Effects are a post-process chain (shader-lab taxonomy)."
)

# ── Composable spec-node authoring (Layer / Position / Trigger / Effect) ──────
# These four are "typed" providers (like color-palette/typography) whose JSON
# spec flows into a host editor which APPLIES it. They are ALSO agent-editable
# (editTarget): the agent writes the canonical file, the node re-imports it.
_EFFECT_AUTHORING = (
    "This is an EFFECT spec node — a GPU/shader post-effect (shader-lab taxonomy) that a host "
    "editor applies to its output. Write `source/{branch}/effect-{id}.json`: "
    "{\"v\":1,\"type\":\"chromatic-aberration|pixelate|dither|posterize|pixel-sort|ascii|crt|halftone|"
    "ink|edge-detect|directional-blur|displacement|particle-grid|pattern|custom\","
    "\"intensity\":0..1,\"params\":{ ...effect-specific... },"
    "\"glsl\":\"<optional custom WebGL2 fragment shader, used only when type=custom>\"}. "
    "Wire this node's out into a host (image / pixel / voxel / mm-composer / material-lab); the host "
    "runs it as a fullscreen pass over its rendered frame. Keep `intensity` in 0..1."
)
_POSITION_AUTHORING = (
    "This is a POSITION spec node — how a host places its content/instances. Write "
    "`source/{branch}/position-{id}.json`: {\"v\":1,\"mode\":\"single|grid|instances|physics|drawn|rope|"
    "camera-feed|grid-3d|scatter-3d|surface\",\"params\":{ ... }}. 2D modes: grid{cols,rows,placement:"
    "'fixed|random'}; instances{source:'mouse|random',count}; physics{gravity:[x,y]}; drawn{paths:"
    "[[x,y]]}; rope{anchors,segments,stiffness}; camera-feed{detector:'hand|face|object|ocr'}. 3D modes "
    "(voxel/spline): grid-3d{cols,rows,layers,spacing}; scatter-3d{count,bounds:[x,y,z]}; surface{meshId}. "
    "Wire out into a host editor to arrange its content."
)
_TRIGGER_AUTHORING = (
    "This is a TRIGGER spec node — what drives reactivity and which other layers it impacts. Write "
    "`source/{branch}/trigger-{id}.json`: {\"v\":1,\"source\":\"none|mouse-click|hover|position|timeline|"
    "audio|camera\",\"params\":{ ... },\"impacts\":[{\"target\":\"<layer id>\",\"param\":\"opacity|scale|"
    "position|effect.intensity\",\"map\":\"linear|threshold\",\"range\":[0,1]}]}. params per source: "
    "timeline{keys:[{t,...}],loop}; audio{sourceId,feature:'loudness|pitch|band'}; camera{detector,event:"
    "'present|gesture|count'}. Wire out into a layer or a host; `impacts` routes the trigger's value onto "
    "other layers' params."
)
_LAYER_AUTHORING = (
    "This is a LAYER node — one layer of a composition. Write `source/{branch}/layer-{id}.json`: "
    "{\"v\":1,\"name\":\"...\",\"z\":0,\"opacity\":0..1,\"blend\":\"normal|multiply|screen|overlay\","
    "\"visible\":true}. The layer's CONTENT + behaviour come from what you WIRE into its in-port: an "
    "asset (the content), and optionally a position / trigger / effect spec node. Then wire this layer's "
    "out into a host (mm-composer / image / composer). The layer binds content+position+trigger+effect "
    "together as one stackable unit — do not inline content here, wire it."
)

# Per-assetKind authoring — the `assetWrite` analogue of editTarget's `authoring`.
# An `asset` node carries an `assetKind` (see KINDS["asset"].inputs.assetKind enum);
# "Write your <assetKind> output to <path>" names the medium but leaks no schema, so
# an agent wired to a shader/3d/lottie node DEFAULTS to plain HTML/CSS (the
# "glassmorphic button became backdrop-filter, not GLSL" failure). Each entry below
# states what the medium IS + how to produce it + the do-NOT-substitute guard. Both
# dispatch paths read it: io_resolve.resolve_downstream (backend <output-destinations>)
# and app.js's typed-output builder (frontend). Keyed by assetKind; {branch}/{id}
# templated per target. EVERY assetKind enum value MUST have an entry (enforced at
# import by io_contract_violations()).
ASSET_KIND_AUTHORING = {
    "shader": (
        "This is a SHADER asset — a GLSL fragment shader rendered to a <canvas>, NOT an "
        "HTML/CSS effect. Do NOT produce a div with `backdrop-filter`/gradients/box-shadow. "
        "Deliverable: a self-contained `.html` (or the file at the target path) whose visible "
        "output is a full-bleed WebGL/WebGL2 canvas driven by a fragment shader — `precision "
        "highp float;`, `uniform float u_time;`, `uniform vec2 u_resolution;` (+ `u_mouse` if "
        "interactive), animated in a rAF loop. The look must be MATH in the shader, not DOM. "
        "If the brief is a UI surface that merely looks glassy, that is a CSS/HTML asset, not a "
        "shader — say so rather than faking a shader with CSS.\n"
        "  MUST RENDER A VISIBLE RESULT — never a blank/black canvas (the #1 failure). "
        "Prefer WebGL2 (`getContext('webgl2')`, `#version 300 es`, `out vec4`) so `fwidth`/"
        "derivatives and precision work WITHOUT extensions. GLSL ES 3.00 GOTCHA: a fragment "
        "shader has NO default float precision, so `precision highp float;` MUST come BEFORE any "
        "float-typed declaration — including `out vec4 fragColor;` — or it fails to compile on "
        "strict drivers (ANGLE/Chrome) and you get a blank frame. Also do NOT use GLSL RESERVED "
        "words as identifiers (`half`, `input`, `output`, `sample`, `filter`, `active`, …) — a "
        "variable named `half` is a compile error. If you stay on WebGL1 AND use "
        "`fwidth`/`dFdx`/`dFdy`, you MUST `getExtension('OES_standard_derivatives')` AND prepend "
        "`#extension GL_OES_standard_derivatives : enable` — and gracefully degrade (drop the "
        "derivative-based AA) if it's missing rather than failing to compile. ALWAYS check "
        "`COMPILE_STATUS` + `LINK_STATUS`; on failure, clear the canvas to a visible color and "
        "surface the infoLog — do NOT leave a silent black frame. Size the drawing buffer from "
        "the canvas's own client size (it is embedded in an iframe), and call resize once before "
        "the first frame."
    ),
    "3d": (
        "This is a 3D asset — an interactive WebGL scene (Three.js or raw WebGL), NOT a flat "
        "image or CSS pseudo-3D. Deliverable: a self-contained `.html`/JS module that builds a "
        "scene (geometry + materials + lights + camera + rAF render loop), resizes to its "
        "container, and respects prefers-reduced-motion. Do NOT substitute a static PNG or a "
        "CSS transform; if a real 3D scene is overkill for the brief, say so.\n"
        "  MUST RENDER A VISIBLE RESULT — never a black void: add ambient + key light, point the "
        "camera AT the subject and frame it, give meshes lit materials (not unlit black). Size the "
        "renderer from the canvas's client size (embedded in an iframe) and resize once before the "
        "first frame."
    ),
    "svg": (
        "This is an SVG asset — inline vector markup written to the target path. Deliverable: a "
        "valid standalone `<svg>` with a viewBox, authored paths/shapes, and currentColor where "
        "it should inherit. Do NOT embed a raster `<image>` or rasterize; this is vector."
    ),
    "image": (
        "This is a RASTER image asset. You cannot hand-draw it as quality SVG/CSS — generate it "
        "(return base64 PNG bytes in the typed-output `imageBase64`, or delegate to the image "
        "pipeline / a raster subagent). Do NOT substitute an emoji, a CSS gradient, or a "
        "stick-figure inline SVG for a real picture."
    ),
    "video": (
        "This is a VIDEO asset (mp4/webm). Produce or fetch the clip and write it to the target "
        "path; reference it via a <video> tag with poster + autoplay/loop/muted/playsinline as "
        "appropriate. Do NOT substitute a CSS animation or an animated GIF for a real video."
    ),
    "audio": (
        "This is an AUDIO asset. Produce or fetch the sound file at the target path. Do NOT "
        "substitute Web Audio synthesis code unless the brief is explicitly a synth."
    ),
    "html": (
        "This is an HTML asset — a SELF-CONTAINED `.html` document (inline CSS/JS, no external "
        "build step) written to the target path. It is embedded via <iframe>, so it must stand "
        "alone. Realize the brief in HTML/CSS/JS; for non-trivial imagery inside it, delegate "
        "raster/illustration to the visual subagents rather than hand-drawing."
    ),
    "html-set": (
        "This is an HTML-SET asset — a small set of linked self-contained `.html` pages under "
        "the target folder (e.g. index + sub-pages), each standalone and inter-linked with "
        "relative hrefs. Same self-containment rule as a single HTML asset."
    ),
    "markdown": (
        "This is a MARKDOWN asset — write GitHub-flavored Markdown to the target path. Prose + "
        "structure only; no HTML scaffolding or build artifacts."
    ),
    "text": (
        "This is a TEXT asset — write plain text to the target path. No markup, no code fences."
    ),
}

# Per-MEDIA-MODEL authoring. `assetKind` is the STORAGE type; `mediaModel` is the
# PRODUCTION medium. Many Pathway-B generators (see prompts/media-models.js) all
# write `.html` (assetKind "html") but each expects a SPECIFIC kind of result —
# a shader scene, a data-viz chart, a three.js scene, a GSAP motion piece, a
# canvas particle loop. Keyed on the media-model id so an agent wired to such a
# node gets the right contract instead of the generic-HTML one. Dispatch prefers
# this map over ASSET_KIND_AUTHORING when the node carries a matching `mediaModel`.
# NOTE: the media-model catalog lives in the frontend (window.TH_MEDIA); the
# daemon can't read it, so this map is the daemon-side mirror of those contracts.
# test_io_contract.py asserts the known specific media models are covered.
MEDIA_MODEL_AUTHORING = {
    "shader": ASSET_KIND_AUTHORING["shader"],
    "viz": (
        "This is a DATA-VISUALIZATION asset — a self-contained `.html` page rendering a real "
        "chart/graph (D3 v7, Observable Plot, or vanilla SVG; CDN imports OK). If the brief gives "
        "no data, INVENT a small plausible inline dataset and label it synthetic. Responsive SVG "
        "(viewBox + 100% width), accessible color (no red/green-only encoding), restrained axis "
        "chrome. Do NOT produce a generic page, a static image, or a decorative graphic — the "
        "deliverable is an actual data visualization."
    ),
    "threejs": (
        "This is a 3D-SCENE asset — a self-contained `.html` page with an INTERACTIVE three.js "
        "scene (r155+ via CDN ES modules): PerspectiveCamera, ambient + directional light, "
        "OrbitControls, at least one animated element, full-window <canvas> with resize handling "
        "and pixelRatio capped at 2. Do NOT produce a flat image, a CSS pseudo-3D effect, or a "
        "static render — it must be a live WebGL scene.\n"
        "  MUST RENDER A VISIBLE RESULT — never a black void: lights present, camera framed on the "
        "subject, lit materials. Size the renderer from the canvas's client size (it's embedded in "
        "an iframe) and resize once before the first frame. If the CDN import fails, surface it "
        "visibly rather than leaving a black canvas."
    ),
    "motion-gen": (
        "This is a MOTION asset — a self-contained `.html` motion piece on the Hyperframes model: "
        "a `#stage`, child `clip` elements timed via data-attributes, driven by a PAUSED GSAP "
        "timeline (GSAP from CDN). It must play standalone AND render deterministically to video. "
        "Do NOT produce a static page or a loose CSS animation — the deliverable is a timed motion "
        "composition on a GSAP timeline."
    ),
    "canvas-gen": (
        "This is a CANVAS-MOTION / PARTICLE asset — a self-contained `.html` page driven by a "
        "real-time canvas2D or WebGL requestAnimationFrame loop (particles, dust/snow/confetti/"
        "sparks, flow fields, generative motion). canvas2D for ≤500 particles; WebGL instanced for "
        "more. Do NOT fake it with CSS keyframes or a static image — the idiom is a live render loop.\n"
        "  MUST RENDER A VISIBLE RESULT — never a blank/black canvas: clear to a visible background "
        "each frame and keep particles within view. Size the canvas from its client size (embedded "
        "in an iframe) and resize once before the first frame. For WebGL, check COMPILE/LINK status "
        "and fall back visibly rather than leaving a silent black frame."
    ),
    "html-page": (
        "This is a UI-PAGE MOCKUP asset — ONE self-contained `.html` screen mockup (inline <style> "
        "with CSS-custom-property tokens; a CDN/Google font OK; NO React/Vue/build step, NO chart "
        "libraries unless the brief is a dashboard). It must be a REALISTIC, POPULATED mockup — "
        "named entities, specific numbers, voiced microcopy; never 'User 1' / 'Lorem'. Fit a "
        "1280×800 viewport without horizontal scroll."
    ),
    "svg-gen": (
        "This is an SVG ILLUSTRATION asset — ONE valid self-contained `<svg>` with a viewBox, "
        "cleanly STRUCTURED (layered <g> groups bg→mid→fg with descriptive ids), no bitmap "
        "`<image href>`, no JS unless requested. Do NOT rasterize or embed a photo; this is "
        "authored vector art."
    ),
    "lottie-gen": (
        "This is a LOTTIE asset — ONE Bodymovin `.json` conforming to the Lottie schema (v 5.7+): "
        "top-level `v`, `fr` (default 30), `ip`, `op`, `w`, `h`, `layers[]` (with `ty`, `ks` "
        "transforms, `shapes`). Author keyframe-driven path morphs / transforms with Bézier easing; "
        "NO external asset references. Do NOT write HTML/CSS or a video — the deliverable is Lottie "
        "JSON a player ingests."
    ),
}

# Section authoring — the sectionWrite analogue. A section is a FRAME/CONTAINER,
# not a medium, so its contract is a placement+registration PROTOCOL, not a
# per-medium schema: register one child node per piece of content into the
# frame's grid. The medium is DELEGATED — each child is an `asset` node whose own
# `assetKind` authoring (ASSET_KIND_AUTHORING) governs how that medium is made.
# `{rect}` is filled per-target by io_resolve with the live canvas bounds.
_SECTION_AUTHORING = (
    "Generate INTO this section frame ({rect}). After writing each output file under "
    "source/, register it as a node INSIDE that rect via POST /__workflow/node/{id}/commit "
    "with addNodes: [{\"id\": \"<fresh id>\", \"kind\": \"asset\", \"assetKind\": "
    "\"image|html|svg|shader|3d|…\", \"path\": \"source/…\", \"x\": …, \"y\": …, \"w\": 320, "
    "\"h\": 240}]. A section is medium-AGNOSTIC: children may be any assetKind, and EACH child "
    "asset is produced per ITS OWN medium contract (the assetKind authoring) — the section only "
    "governs WHERE/HOW children are placed, not what medium they are. Lay nodes out as a grid "
    "inside the bounds: start ~24px in from the left edge and ~48px below the top (the title "
    "strip), step by node width/height + 40px gaps, and keep every node FULLY inside the rect. "
    "If they don't fit, shrink w/h per node rather than overflowing the frame."
)
KIND_IO = {
    "prompt": {
        "provides": [{"port": "out", "label": "Text", "tags": ["text", "runnable", "blendable"],
                       "resolve": "text", "resolveArgs": {"fields": ["text"]}}],
        "accepts":  [{"port": "in", "label": "Generate text with", "tags": ["text-gen"], "ingest": "context"}],
    },
    "folder": {
        "provides": [{"port": "out", "label": "Folder scope", "tags": ["folder"], "resolve": "folder"}],
        "accepts":  [{"port": "in", "label": "Write into", "tags": ["folder-write"], "ingest": "folderWrite"}],
    },
    "browser": {
        "provides": [{"port": "out", "label": "Page capture", "tags": ["asset", "remixable", "blendable"],
                       "resolve": "webfetch", "resolveArgs": {"cap": 16000}}],
        "accepts":  [],
    },
    "asset": {
        "provides": [{"port": "out", "label": "Asset", "tags": ["asset", "remixable", "blendable"],
                       "resolve": "assetFile"}],
        "accepts":  [{"port": "in", "label": "Generate with", "tags": ["asset-gen"],
                       "ingest": "assetWrite"}],
    },
    "color-palette": {
        "provides": [{"port": "out", "label": "Palette", "tags": ["palette"],
                       "resolve": "typed", "resolveArgs": {"flavor": "palette"}}],
        "accepts":  [{"port": "in", "label": "Generate with", "tags": ["palette-gen"], "ingest": "context"}],
    },
    "typography": {
        "provides": [{"port": "out", "label": "Type scale", "tags": ["typography"],
                       "resolve": "typed", "resolveArgs": {"flavor": "typography"}}],
        "accepts":  [{"port": "in", "label": "Generate with", "tags": ["typography-gen"], "ingest": "context"}],
    },
    "design-system": {
        "provides": [{"port": "out", "label": "DS reference", "tags": ["design-system", "folder"],
                       "resolve": "dsRef"}],
        "accepts":  [{"port": "in", "label": "Direction input",
                       "tags": ["palette", "typography", "asset", "folder", "section"], "ingest": "context"}],
    },
    "section": {
        "provides": [{"port": "out", "label": "Section contents", "tags": ["section"],
                       "resolve": "sectionBundle"}],
        "accepts":  [{"port": "in", "label": "Generate into section",
                       "tags": ["text-gen", "asset-gen"], "ingest": "sectionWrite",
                       "authoring": _SECTION_AUTHORING}],
    },
    "skill": {
        "dynamic": True,   # ports depend on node.skill; frontend keeps a capability resolver
        "provides": [{"port": "out", "label": "Generated output", "tags": ["text-gen", "asset-gen", "runnable"],
                       "resolve": "text", "resolveArgs": {"fields": ["output", "text"]}}],
        "accepts":  [{"port": "in", "label": "Prompt / input", "tags": ["text", "asset", "section"],
                       "ingest": "context"}],
    },
    "agent": {
        "provides": [
            {"port": "output", "label": "Output",
              "tags": ["text-gen", "asset-gen", "palette-gen", "typography-gen", "runnable"],
              "resolve": "text", "resolveArgs": {"fields": ["output", "text"], "headerKind": True}},
            {"port": "folder-write", "label": "Writes folder", "tags": ["folder-write"]},
        ],
        "accepts":  [
            {"port": "input", "label": "Context input",
              "tags": ["text", "asset", "palette", "typography", "design-system", "section", "3d"],
              "ingest": "context"},
            {"port": "system-in", "label": "System prompt", "tags": ["text"], "ingest": "context"},
            {"port": "folder-read", "label": "Read scope", "tags": ["folder"], "ingest": "context"},
        ],
    },
    "prototype": {
        "provides": [{"port": "source-read", "label": "Source folder", "tags": ["folder"]}],
        "accepts":  [{"port": "source-write", "label": "Built by", "tags": ["folder-write"],
                       "ingest": "folderWrite"}],
    },
    "ds-brainstorm": {
        "provides": [{"port": "out", "label": "Runnable", "tags": ["runnable"],
                       "resolve": "text", "resolveArgs": {"fields": ["output", "text"], "headerKind": True}}],
        "accepts":  [{"port": "in", "label": "Reference folder", "tags": ["folder"], "ingest": "context"}],
    },
    "iterator-repeater": {
        "provides": [],
        "accepts":  [{"port": "in", "label": "Runnable to repeat", "tags": ["runnable"], "ingest": "context"}],
    },
    "iterator-remix": {
        "provides": [{"port": "out", "label": "Remixed", "tags": ["runnable"],
                       "resolve": "text", "resolveArgs": {"fields": ["output", "text"], "headerKind": True}}],
        "accepts":  [{"port": "in", "label": "Source to remix", "tags": ["remixable"], "ingest": "context"}],
    },
    "iterator-blend": {
        "provides": [{"port": "out", "label": "Blended output", "tags": ["asset-gen"]}],
        "accepts":  [{"port": "input-*", "label": "Blend input", "tags": ["blendable"], "ingest": "context"}],
    },
    "iterator-refiner": {
        "provides": [{"port": "out", "label": "Refined prompt", "tags": ["text-gen"]}],
        "accepts":  [{"port": "in", "label": "Prompt to refine", "tags": ["text"], "ingest": "context"}],
    },
    "composer": {
        "provides": [{"port": "out", "label": "Baked HTML", "tags": ["asset", "blendable"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "html"}}],
        "accepts":  [
            {"port": "in", "label": "Layer", "tags": ["asset", "layer"], "ingest": "context"},
            {"port": "pos", "label": "Position", "tags": ["position"], "ingest": "context"},
            {"port": "edit", "label": "Edit composer", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/composer-{id}.json",
              "authoring": _COMPOSER_AUTHORING},
        ],
    },
    "vector-editor": {
        "provides": [{"port": "out", "label": "Baked SVG", "tags": ["asset"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "svg"}}],
        "accepts":  [
            {"port": "in", "label": "Trace image", "tags": ["asset", "layer"], "ingest": "context"},
            {"port": "pos", "label": "Position", "tags": ["position"], "ingest": "context"},
            {"port": "edit", "label": "Edit vector", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/svg/vector-{id}.json",
              "authoring": _VECTOR_AUTHORING},
        ],
    },
    "formatted-text": {
        "provides": [{"port": "out", "label": "Baked HTML", "tags": ["asset"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "html"}}],
        "accepts":  [{"port": "in", "label": "Text / typography", "tags": ["text", "typography"],
                       "ingest": "context"}],
    },
    "spline-3d": {
        "provides": [{"port": "out", "label": "3D scene", "tags": ["asset", "3d"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "scene.json"}}],
        "accepts":  [
            # A .glb asset wired here imports directly; an AGENT wired here is told
            # to AUTHOR the scene (or generate+register a model) — both via the
            # editTarget authoring instruction. The frontend resolver routes a
            # .glb asset → import and the node consumes node.imports the agent sets.
            {"port": "in", "label": "Model / author scene", "tags": ["asset", "3d", "text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/spline-{id}.scene.json",
              "authoring": _SPLINE_AUTHORING},
            {"port": "pos", "label": "Position (3D)", "tags": ["position"], "ingest": "context"},
            {"port": "edit", "label": "Edit 3D scene", "tags": ["text-gen", "asset-gen", "3d"],
              "ingest": "editTarget", "canonical": "source/{branch}/spline-{id}.scene.json",
              "authoring": _SPLINE_AUTHORING},
        ],
    },
    "font-editor": {
        "provides": [{"port": "out", "label": "Font", "tags": ["asset", "font"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "otf"}}],
        "accepts":  [
            {"port": "in", "label": "Base font", "tags": ["asset", "font"], "ingest": "context"},
            {"port": "edit", "label": "Edit font", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/font-{id}.json",
              "authoring": _FONT_AUTHORING},
        ],
    },
    "image-editor": {
        "provides": [{"port": "out", "label": "Baked image", "tags": ["asset", "remixable", "blendable"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "png"}}],
        "accepts":  [
            {"port": "in", "label": "Layer", "tags": ["asset", "layer"], "ingest": "context"},
            {"port": "fx", "label": "Effect", "tags": ["effect"], "ingest": "context"},
            {"port": "pos", "label": "Position", "tags": ["position"], "ingest": "context"},
            {"port": "edit", "label": "Edit image", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/image-{id}.json",
              "authoring": _IMAGE_AUTHORING},
        ],
    },
    "pixel-editor": {
        "provides": [{"port": "out", "label": "Baked pixels", "tags": ["asset", "remixable"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "png"}}],
        "accepts":  [
            {"port": "in", "label": "Source image", "tags": ["asset"], "ingest": "context"},
            {"port": "pos", "label": "Position", "tags": ["position"], "ingest": "context"},
            {"port": "fx", "label": "Effect", "tags": ["effect"], "ingest": "context"},
            {"port": "edit", "label": "Edit pixels", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/pixel-{id}.json",
              "authoring": _PIXEL_AUTHORING},
        ],
    },
    "voxel-3d": {
        "provides": [{"port": "out", "label": "3D mesh (.glb)", "tags": ["asset", "3d"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "glb"}}],
        "accepts":  [
            {"port": "in", "label": "Model / author scene", "tags": ["asset", "3d", "text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/voxel-{id}.json",
              "authoring": _VOXEL_AUTHORING},
            {"port": "pos", "label": "Position (3D)", "tags": ["position"], "ingest": "context"},
            {"port": "edit", "label": "Edit voxels", "tags": ["text-gen", "asset-gen", "3d"],
              "ingest": "editTarget", "canonical": "source/{branch}/voxel-{id}.json",
              "authoring": _VOXEL_AUTHORING},
        ],
    },
    "synth": {
        "provides": [{"port": "out", "label": "Sound", "tags": ["asset", "audio"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "wav"}}],
        "accepts":  [
            {"port": "edit", "label": "Edit patch", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/synth-{id}.json",
              "authoring": _SYNTH_AUTHORING},
        ],
    },
    "music": {
        "provides": [{"port": "out", "label": "Track", "tags": ["asset", "audio"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "wav"}}],
        "accepts":  [
            {"port": "in", "label": "Sample / instrument", "tags": ["asset", "audio"], "ingest": "context"},
            {"port": "edit", "label": "Edit song", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/music-{id}.json",
              "authoring": _MUSIC_AUTHORING},
        ],
    },
    "material-lab": {
        "provides": [{"port": "out", "label": "Baked HTML", "tags": ["asset", "blendable"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "html"}}],
        "accepts":  [
            {"port": "in", "label": "Element content", "tags": ["asset", "layer"], "ingest": "context"},
            {"port": "fx", "label": "Effect", "tags": ["effect"], "ingest": "context"},
            {"port": "edit", "label": "Edit materials", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/material-{id}.json",
              "authoring": _MATERIAL_AUTHORING},
        ],
    },
    "mm-composer": {
        "provides": [{"port": "out", "label": "Baked HTML", "tags": ["asset", "blendable"],
                       "resolve": "bakedFile", "resolveArgs": {"ext": "html"}}],
        "accepts":  [
            {"port": "in", "label": "Layer content", "tags": ["asset", "layer"], "ingest": "context"},
            {"port": "fx", "label": "Effect", "tags": ["effect"], "ingest": "context"},
            {"port": "pos", "label": "Position", "tags": ["position"], "ingest": "context"},
            {"port": "trig", "label": "Trigger", "tags": ["trigger"], "ingest": "context"},
            {"port": "edit", "label": "Edit composition", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/mm-{id}.json",
              "authoring": _MM_AUTHORING},
        ],
    },
    # ── Composable spec nodes (typed providers + agent-editable) ───────────
    "effect": {
        "provides": [{"port": "out", "label": "Effect", "tags": ["effect"],
                       "resolve": "typed", "resolveArgs": {"flavor": "effect"}}],
        "accepts":  [
            {"port": "edit", "label": "Edit effect", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/effect-{id}.json",
              "authoring": _EFFECT_AUTHORING},
        ],
    },
    "position": {
        "provides": [{"port": "out", "label": "Position", "tags": ["position"],
                       "resolve": "typed", "resolveArgs": {"flavor": "position"}}],
        "accepts":  [
            {"port": "edit", "label": "Edit position", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/position-{id}.json",
              "authoring": _POSITION_AUTHORING},
        ],
    },
    "trigger": {
        "provides": [{"port": "out", "label": "Trigger", "tags": ["trigger"],
                       "resolve": "typed", "resolveArgs": {"flavor": "trigger"}}],
        "accepts":  [
            {"port": "edit", "label": "Edit trigger", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/trigger-{id}.json",
              "authoring": _TRIGGER_AUTHORING},
        ],
    },
    "layer": {
        "provides": [{"port": "out", "label": "Layer", "tags": ["layer"],
                       "resolve": "typed", "resolveArgs": {"flavor": "layer"}}],
        "accepts":  [
            {"port": "in", "label": "Content + behaviour", "tags": ["asset", "position", "trigger", "effect"], "ingest": "context"},
            {"port": "edit", "label": "Edit layer", "tags": ["text-gen", "asset-gen"],
              "ingest": "editTarget", "canonical": "source/{branch}/layer-{id}.json",
              "authoring": _LAYER_AUTHORING},
        ],
    },
}

# Merge the I/O contract onto each kind so kind_contract() + to_jsonable()
# (and therefore the /__kinds/registry endpoint the frontend reads) carry it.
for _io_kind, _io_block in KIND_IO.items():
    if _io_kind in KINDS:
        KINDS[_io_kind]["io"] = _io_block


def io_contract_violations():
    """Static integrity check on KIND_IO — returns a list of human-readable
    problems (empty == healthy). The load-bearing rule:

      Every `editTarget` accept MUST carry a non-empty `authoring` string.

    `editTarget` tells an agent "rewrite this node's canonical JSON", but the
    canonical path alone leaks no schema — so without `authoring` the agent
    GUESSES the file shape and produces something the node can't render (this
    is the composer "blank hero" + spline "2D-instead-of-3D" failure class).
    `authoring` is the slot that carries the target's schema + production modes
    (see io_resolve.resolve_downstream + NODE_IO_FRAMEWORK.md §"How to add a
    new node kind"). Making it REQUIRED here means a new editTarget kind cannot
    ship without it: this runs at import, so `check-compat.sh` (import serve)
    fails before the broken contract can be synced to the daemon.
    """
    # Productive ingests that hand an agent a SCHEMA/PROTOCOL to follow MUST
    # carry a non-empty `authoring` string — else the agent guesses and ships
    # the wrong medium (the composer "blank hero" / shader→CSS / section
    # no-grid failure class). `editTarget` additionally needs a `canonical`
    # file template. `assetWrite` is handled per-assetKind below; `folderWrite`
    # is intentionally schema-less (folder = arbitrary files; prototype carries
    # its own delegation block) so it is exempt.
    _AUTHORING_REQUIRED = {"editTarget", "sectionWrite"}
    problems = []
    for kind, io in KIND_IO.items():
        for accept in (io.get("accepts") or []):
            ingest = accept.get("ingest")
            if ingest not in _AUTHORING_REQUIRED:
                continue
            port = accept.get("port", "?")
            if ingest == "editTarget" and not accept.get("canonical"):
                problems.append(
                    f"{kind}.{port}: editTarget accept has no `canonical` file template")
            authoring = accept.get("authoring")
            if not (isinstance(authoring, str) and authoring.strip()):
                problems.append(
                    f"{kind}.{port}: {ingest} accept is missing a non-empty `authoring` "
                    f"contract — an agent wired here would have to GUESS what to produce. "
                    f"Add an `authoring` instruction (see _SPLINE_AUTHORING / "
                    f"_COMPOSER_AUTHORING / _SECTION_AUTHORING; NODE_IO_FRAMEWORK.md step 4).")

    # Same rule for asset MEDIA: every assetKind an agent can be told to produce
    # must carry a per-medium authoring string, else the dispatch is medium-blind
    # and the agent defaults to HTML/CSS (the shader→backdrop-filter failure).
    asset_kind_spec = (KINDS.get("asset", {}).get("inputs", {}).get("assetKind", {}))
    for ak in (asset_kind_spec.get("values") or []):
        auth = ASSET_KIND_AUTHORING.get(ak)
        if not (isinstance(auth, str) and auth.strip()):
            problems.append(
                f"asset.assetKind={ak!r}: no entry in ASSET_KIND_AUTHORING — an agent wired to "
                f"a {ak!r} asset would not be told what the medium is or how to produce it. Add "
                f"an ASSET_KIND_AUTHORING[{ak!r}] entry (NODE_IO_FRAMEWORK.md step 4).")
    return problems


_io_problems = io_contract_violations()
if _io_problems:
    raise RuntimeError(
        "KIND_IO contract integrity check failed — productive ingests (editTarget / "
        "sectionWrite / asset media) need an `authoring` contract (see NODE_IO_FRAMEWORK.md):"
        "\n  - " + "\n  - ".join(_io_problems))


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
    return {"KINDS": KINDS, "STAGES": STAGES,
            "ASSET_KIND_AUTHORING": ASSET_KIND_AUTHORING,
            "MEDIA_MODEL_AUTHORING": MEDIA_MODEL_AUTHORING}
