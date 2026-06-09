# Orchestrator system — registry, discovery, disable

The orchestrator registry surfaces every top-level orchestrator agent the app
ships and lets the user disable any of them per project (or workspace-wide
from the landing page).

Adding a new orchestrator is a **single-file** operation: drop a manifest next
to the playbook and everything else picks it up automatically — the landing
page Orchestrators tab, the daemon's `/__orchestrators` endpoint, the spawn preamble's
"dispatch this orchestrator FIRST" hard-rule, and the per-project disable toggle.

## What counts as a orchestrator

A orchestrator is a top-level orchestrating agent that:
- Has a single self-contained playbook at `.claude/agents/<name>.md`
- Dispatches multiple downstream subagents (drawers, researchers, lenses)
  to produce a complex multi-component artefact
- Is the right entry point for a particular kind of user request
  (image, simulation, interactive piece, future: 3D scene, document, etc.)

`visual-orchestrator`, `simulation-orchestrator`, and `interactive-media-orchestrator` are
the three shipped today.

A subagent that just produces one file (a drawer, a researcher, a lens) is
NOT a orchestrator — it's a component. Don't manifest it here.

## The contract — three files

### 1. The playbook — `.claude/agents/<id>.md`

Standard Claude Code subagent definition. YAML frontmatter (name, description,
tools) + body. Same shape as the existing orchestrator playbooks.

### 2. The manifest — `.claude/agents/<id>.manifest.json`

Pure declarative metadata. Schema:

```jsonc
{
  "id":             "my-new-orchestrator",          // matches the playbook's filename
  "label":          "My New",                  // shown on the card
  "tagline":        "Single sentence about what it does",
  "version":        "v1.0",
  "defaultEnabled": true,                      // shipped-on; user can disable
  "subagentName":   "my-new-orchestrator",          // exact subagent_type for Task dispatch
  "playbookPath":   ".claude/agents/my-new-orchestrator.md",

  "description":    "Longer prose — explains the pipeline shape, the loop-until-bar pattern, multi-draft cruxes if any, what makes this orchestrator the right choice for its trigger.",

  "triggers": [
    { "mode": "chat", "title": "Path A — \"build an app\" with this slot",
      "rule":       "Top-level Claude scaffolds the app shell first (with the orchestrator's placeholder), then dispatches the orchestrator per slot.",
      "ruleSource": "editor/kinds/capabilities.py — '<your hard-rule section title>' Path A" },
    { "mode": "chat", "title": "Path B — ",
      "rule":       "User wants the artefact itself; Claude dispatches the orchestrator directly in ",
      "ruleSource": "editor/kinds/capabilities.py — '<your hard-rule section title>' Path B" }
  ],

  "dispatches": {
    // Group your dispatched subagents by phase. All four keys are optional;
    // include the ones that apply. The UI renders each group with its label.
    "research":   ["my-research-precedent", "my-research-..."],
    "components": ["my-component-author-1", "my-component-author-2"],
    "drawers":    ["my-medium-1", "my-medium-2"],          // visual-orchestrator-style per-medium drawers
    "lenses":     ["craft-lens", "aesthetic-lens", "concept-lens"]
  },

  "skills": ["generate-image", "my-new-skill"],            // skill ids from editor/prompts/media-models.js

  "nodeKinds": {
    "container":         ["my-container-kind"],
    "agent_overrides":   ["my_*_", "cp_my_*_pick_", "cp_my_gate_"],
    "trios_scaffolded":  ["p_<id>", "s_<id>", "a_<id>"]    // visual-orchestrator-style
  },

  "documents": {
    "designDoc":   "docs/features/<your-feature>.md",
    "calibration": ".claude/lens-calibration/fixtures/my-*"
  }
}
```

### 3. The capabilities-preamble hard-rule (if chat-triggerable)

If your orchestrator should be auto-dispatched from chat (), add a
hard-rule section to `editor/kinds/capabilities.py:capabilities_preamble()`
matching the existing pattern:

```markdown
## <Family> surfaces: dispatch <id>-orchestrator FIRST (v<X> hard rule)

When the user's message mentions <triggers>... your FIRST action is a Task
call to `<id>-orchestrator` in \`\`\`
Task(subagent_type: "<id>-orchestrator",
     description: "...",
     prompt: "...")
\`\`\`

### Do NOT do any of these:
- ❌ ...

### Decision rule:
| User said… | Your first move |
|---|---|
| "..." | `Task(<id>-orchestrator, …)` |
```

The section header **must** start with exactly the phrase used in the
`triggers[].ruleSource` field of your manifest, so the disable-strip logic
in `_strip_disabled_orchestrator_blocks` can find it. Look at the three existing
orchestrators' patterns:

- `## Image creation: dispatch visual-orchestrator FIRST`
- `## Simulation surfaces: dispatch simulation-orchestrator FIRST`
- `## Interactive pieces: dispatch interactive-media-orchestrator FIRST`

ALSO add a row to `_strip_disabled_orchestrator_blocks`'s `SECTIONS` list with
your section's exact header marker + your orchestrator's id, so the disable
filter knows which prose to strip when the user turns your orchestrator off.

## Disable mechanism

Per-target disable file: `<targetRoot>/.orchestrators-disabled.json`:

```json
{ "disabled": ["my-new-orchestrator", "another-orchestrator"] }
```

Resolution:
- Landing page (no project) → file at workspace root (workspace-wide)
- Inside a project → file at project root (per-project override)

When a orchestrator is in the disable list:
- Its hard-rule block is removed from the spawn preamble for that project
  (or workspace if no project active)
- The Orchestrators tab card is visually dimmed + the toggle shows OFF
- Spawned Claude sessions in that scope don't see "dispatch this orchestrator
  FIRST" cues
- The orchestrator agent ITSELF still exists — user can manually invoke via
  `Task(subagent_type: "<id>", prompt: "...")` if they know the name

This is intentional: disabling cuts AUTO-DISPATCH, not capability.

## Surface map

- **HTTP**: `GET /__orchestrators[?project=<id>]` returns the registry +
  per-target enabled state.
- **HTTP**: `POST /__orchestrators/disable[?project=<id>]` with
  `{orchestratorId, enabled}` flips one orchestrator's state.
- **Landing UI**: `editor/app.js:OrchestratorsLanding` — tab next to Projects.
- **Spawn preamble**: `editor/kinds/capabilities.py:capabilities_preamble`
  takes `project_root` and strips disabled-orchestrator blocks before return.

## Adding a new orchestrator — checklist

1. Write the playbook at `.claude/agents/<id>.md`.
2. Drop the manifest at `.claude/agents/<id>.manifest.json` (this file's §"Contract" §2 schema).
3. If chat-triggerable: add a hard-rule section to `capabilities.py:capabilities_preamble`
   AND add the section's header to `_strip_disabled_orchestrator_blocks`'s
   `SECTIONS` table.
4. If it adds new node kinds: declare them in `editor/kinds/registry.py`
   (per-id overrides + container kinds).
5. (Optional but recommended) Hand-author calibration fixtures at
   `.claude/lens-calibration/fixtures/<id>-*` if it dispatches lens-gated
   components.

The Orchestrators tab on the landing page auto-discovers the new manifest on
next reload. No other UI code change needed.
