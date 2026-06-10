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

---

## Library-backed orchestrators (read if your orchestrator references a curated catalogue)

Some orchestrators carry a curated reference — a body of structured knowledge that drives every dispatch decision. Examples shipped today:

| Orchestrator | Library (full prose) | Index (structured lookup) | Per-entry detail |
|---|---|---|---|
| photography-orchestrator | `docs/research/photography-library.md` (13K words, 42 styles) | `docs/research/photography-library.index.json` (32 KB) | `prototype/photo-<styleId>.md` (×42) |
| illustration-orchestrator | `docs/research/illustration-library.md` (17K words, 108 styles) | `docs/research/illustration-library.index.json` (84 KB) | `prototype/illust-<styleId>.md` (×108) |
| material-orchestrator | `docs/research/material-library.md` (16K words, 78 materials) | `docs/research/material-library.index.json` (60 KB) | `prototype/material-<materialId>.md` (×78) |

The three-tier layout solves a real problem: a library at 15K+ words is too expensive to read once per slot, and orchestrators routinely dispatch against pages with 10–30 slots. Reading the full library every dispatch would burn 300K+ context tokens before any work begins. The index-first / sed-slice pattern drops per-slot cost by ~95%.

### The three artefacts and what each is for

**1. Full library — `docs/research/<name>-library.md`**

The canonical reference. Prose where prose matters (prompting fundamentals, principles, anti-pattern explanations); YAML-in-markdown for per-entry data (keywords, prompt templates, implementation snippets, line counts vary 30–150 per entry). This file is the source of truth — every other artefact derives from it. Edit only this; regenerate the others.

Required sections:
- §1 Prompting / Implementation fundamentals (prose primer)
- §2 Entry library (YAML-in-markdown, one block per entry)
- §3 (photo/illust) or §7 (material) Decision tree (markdown table: prototype slug → default + alternatives)
- §4 Universal negative-keyword list
- §5+ Implementation / orchestrator-integration notes

Per-entry YAML must include a stable id field (`styleId` for photo + illust, `materialId` for material) — the slug used by every downstream artefact.

**2. Index — `docs/research/<name>-library.index.json`**

Auto-generated by `scripts/build-library-indexes.py`. The orchestrator's discovery layer — small enough to read on every dispatch (~30–80 KB), structured for pure-JSON decision-making with no prose-scanning.

Schema (declared as `version: "1.0"`):

```jsonc
{
  "version": "1.0",
  "source":  "docs/research/<name>-library.md",
  "library": "<name>",
  "totalEntries": <N>,
  "decisionTree": {
    "<prototypeSlug>": {
      "default":      "<entryId>",
      "alternatives": ["<entryId>", ...],
      "decoration":   "<entryId>",  // illustration only — for decoration-role slots
      "notes":        "<advisory prose, optional>"
    }
  },
  "entries": {
    "<entryId>": {
      "name":                "<display name>",
      "category":            "<entry category>",
      "family":              "<digital | analog | hybrid>",  // material only
      "surfaceFinish":       "<matte | glossy | ...>",        // material only
      "era":                 "<decade or 'current'>",
      "oneLine":             "<single-sentence summary>",
      "roleAffinity":        ["<role>", ...],
      "notForUseWhen":       "<one line>",
      "antiPatternKeywords": ["<keyword>", ...],
      "pairsPrototypes":     ["<prototypeSlug>", ...],
      "lineRange":           [<start>, <end>]
    }
  }
}
```

The `lineRange` is load-bearing — it's how the drawer slices the targeted entry's YAML from the full library without reading the whole file (`sed -n '<start>,<end>p'`).

**3. Per-entry detail — `prototype/<prefix>-<entryId>.md`**

Generated by `/tmp/gen-library-details.py` (one-off script — re-derive on schema change). Surfaces every library entry in the System tab → Design library as a browsable card with image-sample slot. Same shape as `prototype/aesthetic-*.md` and `prototype/style-*.md`. Drop reference images per entry at `prototype/<sample>.png`; the catalog UI surfaces them.

The prefix maps to a category in `serve.py:_PROTOTYPE_CATEGORIES`:
- `photo-` → Photography bucket
- `illust-` → Illustration bucket
- `material-` → Materials bucket

### The orchestrator's access pattern (per dispatch)

```
1. Orchestrator §0 — read library.index.json (~30-80 KB structured).
2. index.decisionTree[committedAesthetic] → {default, alternatives[]}.
3. JSON-only filter on index.entries[styleId].roleAffinity + .antiPatternKeywords + .notForUseWhen.
   No library file touched yet.
4. Optional: index.entries[secondaryStyleId] for register chaining.
5. Pass picked styleId + lineRange to the per-slot drawer.
6. Drawer sed-slices the entry: sed -n '<start>,<end>p' library.md → ~30-150 lines.
7. Drawer reads YAML fields (examplePromptTemplate, keywords, anti-patterns, implementation snippets) and composes the output.
```

Per-slot cost: ~3 KB of index (one-time per session) + ~600 tokens of slice per slot. A 20-slot page is ~15 K tokens total instead of 300 K.

### Adding a new library-backed orchestrator — checklist

1. **Write the library** at `docs/research/<name>-library.md`:
   - §1 Fundamentals / principles primer
   - §2 Per-entry YAML blocks with a stable id field
   - §3 (or §7) Decision tree table mapping prototype slugs → entry ids
   - §4 Universal negative-keyword / anti-pattern list
2. **Register the library in `scripts/build-library-indexes.py`** — add a LIBS entry with `{name, source, id_key, tree_section}`.
3. **Run the script**: `python3 scripts/build-library-indexes.py`. Verify the index parses ≥1 decisionTree slug and ≥1 entry per category.
4. **Generate the per-entry detail files**: adapt `/tmp/gen-library-details.py` (or write a new script) to emit `prototype/<prefix>-<entryId>.md` per entry. One-time per schema change.
5. **Add the prefix to `serve.py:_PROTOTYPE_CATEGORIES`** so the System tab surfaces the new bucket.
6. **Write the orchestrator playbook** following `photography-orchestrator.md` / `material-orchestrator.md` as a template. §0 reads the **index**, not the full library. §2 picks candidates from `decisionTree` + filters on JSON fields. The drawer dispatches the actual library slice.
7. **Write the per-slot / per-element drawer playbook** following `photography-style-enricher.md` / `material-fidelity-author.md` as templates. The drawer is where the `sed -n '<start>,<end>p'` slice happens — never in the orchestrator.
8. **Drop the manifest** at `.claude/agents/<id>-orchestrator.manifest.json`. Set `documents.designDoc` to the library path and `documents.policy` (or another `documents.*` field) to the index path so the System tab card shows both as references.

The library is the source of truth. Edit it, then re-run `scripts/build-library-indexes.py` to regenerate the index. The per-entry detail files only need re-generation when a library entry is added, removed, or has its identity-fields (id, name, category, signatures, pairs-with) changed.

### When NOT to use a library-backed pattern

- If the orchestrator's decision is purely structural (no curated knowledge needed), use a flat playbook (e.g. `interactive-polish-orchestrator` has no library — its decisions come from genre + register, not a catalogue).
- If the orchestrator's catalogue would have < 20 entries, inline them in the playbook directly. The index pattern is for catalogues of 30+ entries where the playbook would balloon if everything lived inline.
- If the catalogue changes per-project (not workspace-wide), it doesn't belong in `docs/research/` — surface it via the project's own metadata (e.g. `workflow/<plan>.json`).
