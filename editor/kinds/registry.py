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

# ── STAGES — the canonical pipeline phases (mirrors prompts/stages.py) ───
#
# `pauseAfter: True` stages cause the orchestrator to halt and ask for user
# confirmation before advancing. C and F have inherent decision checkpoints
# (cp_ds_pick / cp_remix_pick) so they don't need pauseAfter.
STAGES = [
    {"code": "A",  "short": "Intake",            "pauseAfter": False, "title": "Intake (3 questions + reference)"},
    {"code": "B",  "short": "Refine PRD",        "pauseAfter": False, "title": "Refine PRD"},
    {"code": "C",  "short": "DS brainstorm",     "pauseAfter": False, "title": "DS brainstorm — N variants"},
    {"code": "D",  "short": "Generate DS",       "pauseAfter": True,  "title": "Generate Design System"},
    {"code": "E",  "short": "Quick HTML",        "pauseAfter": False, "title": "Chunk PRD → 3 quick HTML pages"},
    {"code": "F",  "short": "Remix alts",        "pauseAfter": False, "title": "Remix — 3 alternatives per page"},
    {"code": "G",  "short": "Refine with pick",  "pauseAfter": True,  "title": "Refine PRD with picked alts"},
    {"code": "H",  "short": "Update DS",         "pauseAfter": False, "title": "Update DS from refined PRD"},
    {"code": "H2", "short": "Realign PRD",       "pauseAfter": False, "title": "Realign PRD with updated DS"},
    {"code": "I",  "short": "Build prototype",   "pauseAfter": False, "title": "Build prototype source"},
    {"code": "J",  "short": "Design brief",      "pauseAfter": False, "title": "Design brief + storyboard"},
]


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
            "bp_research": {
                "outputsRoot": "source/{branch}/",
                "completion": {"requires": ["files: source/{branch}/research.md exists"]},
                "notes": "WebSearch + WebFetch + write source/{branch}/research.md.",
            },
            "bp_proto_build": {
                "outputsRoot": "source/{branch}/",
                "extendsGraph": True,
                "graphExtensionScope": "per-image-slot subagent trios",
                "completion": {"requires": ["files: source/{branch}/index.html exists"]},
            },
            "bp_design_brief": {
                "outputsRoot": "DESIGN_BRIEF.html",
                "extendsGraph": True,
                "graphExtensionScope": "per-screen breakdown subagents",
            },
            "bp_ds_update": {
                "outputsRoot": "DS_PROPOSAL.md",
                "extendsGraph": True,
                "graphExtensionScope": "per-section + per-shell subagents",
            },
            "cp_ds_pick": {
                "notes": "Minimal decision agent. Writes DECISION_cp_ds_pick.json.",
                "completion": {"requires": ["files: DECISION_cp_ds_pick.json exists with non-empty values"]},
            },
            "cp_remix_pick": {
                "notes": "Like cp_ds_pick, but for the 3 picks across remixed pages.",
                "completion": {"requires": ["files: DECISION_cp_remix_pick.json exists with 3 values"]},
            },
            # D6 migration targets — bs_html_* moves from skill·llm to agent.
            # Outputs are FLAT files (source/<branch>/_pages/page_N.html) so the
            # downstream `bs_html_N_asset` card + the orchestrator skill's
            # path table + runRemix's fetch all resolve to the same place.
            # An earlier experiment used a folder convention
            # (`_pages/page_N/index.html`) but the scaffold + orchestrator
            # never migrated, so downstream fetches 404'd — the source of the
            # user-visible "could not read upstream HTML" error.
            "bs_html_1": {
                "outputsRoot": "source/{branch}/_pages/page_1.html",
                "completion": {"requires": ["files: source/{branch}/_pages/page_1.html exists, non-empty"]},
                "downstreamLink": "br_remix_p1",
                "notes": "Generates one full HTML page. Visible subprocess. Dispatched in parallel with siblings bs_html_2/3.",
            },
            "bs_html_2": {
                "outputsRoot": "source/{branch}/_pages/page_2.html",
                "completion": {"requires": ["files: source/{branch}/_pages/page_2.html exists, non-empty"]},
                "downstreamLink": "br_remix_p2",
            },
            "bs_html_3": {
                "outputsRoot": "source/{branch}/_pages/page_3.html",
                "completion": {"requires": ["files: source/{branch}/_pages/page_3.html exists, non-empty"]},
                "downstreamLink": "br_remix_p3",
            },
            # Long-form PRD writes — complex artifact, must be agent-kind not skill·llm.
            "bp_prd_refine":   {"outputsRoot": "source/{branch}/prd.md",         "completion": {"requires": ["files: source/{branch}/prd.md exists"]}},
            "bp_prd_final":    {"outputsRoot": "source/{branch}/prd-final.md",   "completion": {"requires": ["files: source/{branch}/prd-final.md exists"]}},
            "bp_prd_align":    {"outputsRoot": "source/{branch}/prd-aligned.md", "completion": {"requires": ["files: source/{branch}/prd-aligned.md exists"]}},
            # ── COHERENCE PASS (Subagent 11) — see COHERENCE_PHASE_PLAN.md ───────
            # Upstream contract producers: ONE source of truth before page generation.
            # cp_fixture canonicalises every numeric/named fact (entities) so pages
            # cannot drift (the `38` vs `312` super bug).
            "cp_fixture": {
                "outputsRoot": "source/{branch}/_coherence/",
                "completion": {"requires": [
                    "files: source/{branch}/_coherence/model.json exists",
                    "files: source/{branch}/data.js exists",
                ]},
                "extendsGraph": False,
                "notes": (
                    "Reads the PRD's 'System mechanics + data model' section and writes "
                    "BOTH model.json (canonical entity store; every fact declared once) "
                    "AND data.js (window.DEMO surface views, each value REFERENCED from "
                    "model.json, never re-typed). Downstream bs_html_* generators consume "
                    "data.js; they MUST NOT author numeric/named facts inline. If a fact "
                    "isn't in the model, request it — don't invent it."
                ),
            },
            # cp_chrome writes ONE chrome contract every page must include.
            "cp_chrome": {
                "outputsRoot": "source/{branch}/_coherence/",
                "completion": {"requires": [
                    "files: source/{branch}/_coherence/chrome.html exists",
                    "files: source/{branch}/_coherence/chrome.contract.json exists",
                ]},
                "notes": (
                    "Reads the DS (shells + styles.css) + PRD page-to-shell map; writes "
                    "chrome.html (the canonical partial: ONE brand <symbol>, ONE nav, ONE seal slot) "
                    "+ chrome.contract.json (machine-readable assertion target: "
                    "{brandSymbolId, navItems[], sealSelector, navLocation}). Page generators "
                    "include the partial verbatim and may set only the active nav item; "
                    "they must NOT redefine the brand, nav, or seal."
                ),
            },
            # Downstream auditors: read the canonical contracts + final pages, emit COHERENCE_REPORT.json.
            "lint_data_coherence": {
                "outputsRoot": "source/{branch}/COHERENCE_REPORT.json",
                "completion": {"requires": [
                    "files: source/{branch}/COHERENCE_REPORT.json exists",
                ]},
                "notes": (
                    "Reads model.json + every final source/<branch>/*.html + data.js. "
                    "Lint rules (block severity on 1-3): "
                    "(1) No contradiction — facts in prose that map to a model entity must "
                    "equal the model value. "
                    "(2) Single value per key — same entity must not resolve to two values. "
                    "(3) Cross-surface continuity — same caseId carries same grade/confidence "
                    "everywhere. "
                    "(4 warn) — orphan facts: prose figures with no backing model entity."
                ),
            },
            "lint_chrome_consistency": {
                "outputsRoot": "source/{branch}/COHERENCE_REPORT.json",
                "completion": {"requires": [
                    "files: source/{branch}/COHERENCE_REPORT.json exists",
                ]},
                "notes": (
                    "Reads chrome.contract.json + every final page. "
                    "Lint rules (block on 1, 2, 4): "
                    "(1) Identical brand — <symbol>/markup hashes equal across pages. "
                    "(2) Identical nav — same item set, order, classes, and LOCATION. "
                    "(3 warn) Fixed seal — same selector/position/scale everywhere. "
                    "(4) One nav paradigm — flag pages whose nav diverges from "
                    "contract.navLocation (the left-rail-vs-top-bar split in super)."
                ),
            },
            # Vision-verify is per-asset; node id is "v_<assetId>".
            # We document the contract under a wildcard key the validator falls
            # back to when checking per-id.
            "v_": {
                "outputsRoot": "source/{branch}/COHERENCE_REPORT.json",
                "completion": {"requires": [
                    # No file required beyond the appended verdict; the report
                    # accumulates entries from many v_<id> commits.
                ]},
                "notes": (
                    "Vision-verify node appended to every visual trio "
                    "(prompt → skill → asset → VERIFY). Reads the generated PNG + the "
                    "asset's intent + constraints[]. Flags: medium mismatch (diagram vs "
                    "photographic still); constraint violation (recognizable person, "
                    "saturated where intent said desaturated); duplication (asset redraws "
                    "something already rendered live, e.g. the coord-graph); subject "
                    "mismatch. On fail, AUTO-RETRY the prompt drawer ONCE with the failure "
                    "reason fed back; on second fail, mark block and escalate."
                ),
            },
            # Final release gate before prototype: aggregates lint + verify reports,
            # emits <decision-request> on any block-severity finding.
            "cp_coherence_gate": {
                "outputsRoot": "DECISION_cp_coherence.json",
                "completion": {"requires": [
                    "files: DECISION_cp_coherence.json exists with non-empty values",
                ]},
                "notes": (
                    "Reads COHERENCE_REPORT.json. If all findings are warn-or-lower, "
                    "commits DECISION_cp_coherence.json with value='clear' and releases "
                    "the prototype node. If any block-severity finding exists, emits a "
                    "<decision-request> via workflow-orchestrator with options: "
                    "Retry (re-run offending generator with finding fed back) · "
                    "Patch (Subagent 11 applies minimal source fix, e.g. reconcile a "
                    "number to the model) · Accept-override (human waives, recorded)."
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
        "outputsRoot":  "source/{branch}/_ds_brainstorm/{variant}/",
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
        "outputsRoot":  "source/{branch}/_remix/p{pageIdx}/",
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
        "outputsRoot":  "source/{branch}/_blend/{id}/",
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


def stage_pause_after(code: str) -> bool:
    """True if the orchestrator must halt for user confirmation after this stage."""
    for s in STAGES:
        if s["code"] == code:
            return bool(s.get("pauseAfter"))
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
