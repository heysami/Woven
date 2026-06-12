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

Thirteen ship today: `visual-orchestrator`, `simulation-orchestrator`,
`interactive-media-orchestrator`, `narrative-experience-orchestrator`,
`game-experience-orchestrator`, `scrapbook-experience-orchestrator`,
`interactive-polish-orchestrator`, `motion-studio-orchestrator`,
`photography-orchestrator`, `illustration-orchestrator`,
`material-orchestrator`, `creative-visual-orchestrator`, and
`hero-3d-orchestrator` (the Spline-grade 3D escalation routed by
visual-orchestrator's `3d-hero` classification — see
`docs/research/spline-grade-3d-study.md`).

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
in `_strip_disabled_orchestrator_blocks` can find it. Look at the existing
orchestrators' patterns (headers as they appear in `capabilities.py`):

- `## Image creation: dispatch visual-orchestrator FIRST`
- `## Live view, 3D, real-world map, or living system: dispatch simulation-orchestrator FIRST`
- `## Interactive piece: dispatch interactive-media-orchestrator FIRST`

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
| photography-orchestrator | `docs/research/photography-library.md` (13K words, 42 styles) | `docs/research/photography-library.index.json` (32 KB) | `design-library/photo-<styleId>.md` (×42) |
| illustration-orchestrator | `docs/research/illustration-library.md` (17K words, 108 styles) | `docs/research/illustration-library.index.json` (84 KB) | `design-library/illust-<styleId>.md` (×108) |
| material-orchestrator | `docs/research/material-library.md` (16K words, 78 materials) | `docs/research/material-library.index.json` (60 KB) | `design-library/material-<materialId>.md` (×78) |
| motion-studio-orchestrator | `docs/research/motion-scene-library.md` (primer, 30 techniques) | `docs/research/motion-scene-library.index.json` (38 KB) | `design-library/motion-<techniqueId>.md` (×30) |

The three-tier layout solves a real problem: a library at 15K+ words is too expensive to read once per slot, and orchestrators routinely dispatch against pages with 10–30 slots. Reading the full library every dispatch would burn 300K+ context tokens before any work begins. The index-first / sed-slice pattern drops per-slot cost by ~95%.

### The three artefacts and what each is for

**1. Primer — `docs/research/<name>-library.md`**

A short prose primer (~2-3K words). Carries fundamentals + universal rules; does NOT carry per-entry data. Required sections:
- §1 Prompting / Implementation fundamentals (the principles primer — film stocks worth naming, lighting setups, material light-interaction, depth cueing, anti-pattern catalogue)
- Decision-tree prose section (the structured decision tree lives in `.index.json`; this section is prose-context for it)
- Universal negative-keyword list
- Implementation / orchestrator-integration notes

The primer is read-once-per-session reference. Not in the dispatch hot-path.

**2. Per-entry source files — `design-library/<prefix>-<entryId>.md`**

**THIS IS THE SOURCE OF TRUTH for each entry.** Hand-edited, one file per entry, ~1-5KB each. YAML frontmatter for structured fields + markdown body for prose. Same model as `design-library/style-glassmorphism.md` and `design-library/aesthetic-vaporwave.md`.

File structure:

```markdown
---
styleId: helmut-newton-flash               # or materialId for material/
name: Helmut Newton on-camera flash glamour
category: editorial-fashion
era: 1970s-1990s
pairsPrototypes: [recipe-editorial-magazine, recipe-warm-restraint, ...]
notForUseWhen: Brief is sincere, sentimental, family-friendly, or wholesome.
---

# Display title

(one-line summary derived from the first visual signature)

## Visual signatures
- ...

## Prompt keywords
**Primary**: ...
**Lighting**: ...
**Camera / lens**: ...
**Film stock / post-processing**: ...
**Mood**: ...
**Avoid (negative prompt)**: ...

## Named references
**Photographers**: ...
**Magazines**: ...

## Example prompt template
> Full paste-ready prompt...

## When to use
...

## When NOT to use
...

## Pairs with (prototype slugs)
- `recipe-editorial-magazine`
- ...

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->
```

To **add a new entry**: create a new `design-library/<prefix>-<entryId>.md` (copy any existing file as a template), then re-run `python3 scripts/build-library-indexes.py` to refresh the index. To **edit an entry**: open its file directly, change what you need, re-run the script.

These files are ALSO the runtime read for the drawer (~1-5KB per dispatch) AND the Design library tab's browseable card (image-sample slot supported via `<!-- image: ... -->` markers).

**3. Index — `docs/research/<name>-library.index.json`**

Auto-generated by `scripts/build-library-indexes.py` (scans `design-library/<prefix>-*.md` files and builds the index from their frontmatter). The orchestrator's discovery layer — read-once-per-session, ~30–80 KB structured JSON, no prose-scanning.

Schema (declared as `version: "2.0"`):

```jsonc
{
  "version": "2.0",
  "library": "<name>",
  "sourceDir": "design-library/",
  "totalEntries": <N>,
  "decisionTree": {
    "<prototypeSlug>": {
      "default":      "<entryId>",
      "alternatives": ["<entryId>", ...]
    }
  },
  "entries": {
    "<entryId>": {
      "name":                "<display name>",
      "category":            "<entry category>",
      "family":              "<digital | analog | hybrid>",  // material only
      "surfaceFinish":       "<matte | glossy | ...>",        // material only
      "era":                 "<decade or 'current'>",         // photo only
      "role":                "<subject | decoration | ...>",  // illust only
      "oneLine":             "<single-sentence summary>",
      "roleAffinity":        ["<role>", ...],
      "notForUseWhen":       "<one line>",
      "pairsPrototypes":     ["<prototypeSlug>", ...],
      "sourceFile":          "design-library/<prefix>-<entryId>.md"
    }
  }
}
```

The `sourceFile` field tells the drawer where to read the entry's full detail. The decision tree is BUILT from each entry's `pairsPrototypes` field — first entry to claim a slug is the default; subsequent ones become alternatives.

### The orchestrator's access pattern (per dispatch)

```
1. Orchestrator §0 — read library.index.json (~30-80 KB structured, ONCE per session).
2. index.decisionTree[committedAesthetic] → {default, alternatives[]}.
3. JSON-only filter on index.entries[styleId].roleAffinity + .notForUseWhen.
   No source file or primer touched yet.
4. Optional: index.entries[secondaryStyleId] for register chaining.
5. Pass picked styleId to the per-slot drawer.
6. Drawer reads index.entries[styleId].sourceFile (design-library/<prefix>-<styleId>.md, ~1-5 KB).
7. Drawer parses frontmatter (structured fields) + markdown sections (prompt template,
   keywords, when-not-to-use) and composes the output.

If sourceFile is missing → runStatus: error. No fallback (the primer no longer has
per-entry data). The user re-runs scripts/build-library-indexes.py after adding the
new design-library/<prefix>-<entryId>.md.
```

Per-slot cost: ~3 KB of index (one-time per session) + ~1-5 KB of per-entry file per slot. A 20-slot page is ~30-100 KB total. The primer file (`docs/research/<name>-library.md`) is never read at dispatch time — only when a human reads it for context.

### Adding a new library-backed orchestrator — checklist

1. **Write the primer** at `docs/research/<name>-library.md`:
   - Fundamentals / principles primer (the "how to think about this medium" prose)
   - Decision-tree prose section (the structured decision tree lives in the index)
   - Universal negative-keyword list
   - Implementation / orchestrator-integration notes
2. **Write each per-entry source file** at `design-library/<prefix>-<entryId>.md`. Each is hand-edited, ~1-5 KB. Use any existing photo/illust/material entry as a template:
   - YAML frontmatter with the stable id field + structured metadata + `pairsPrototypes` list
   - H1 + one-line summary
   - Markdown sections (Visual signatures, Prompt keywords, Example prompt template, When to use, When NOT to use, Pairs with)
   - `<!-- image: ... -->` placeholder for the Design library card
3. **Register the library in `scripts/build-library-indexes.py`** — add a LIBS entry with `{prefix, name, id_key, out}`.
4. **Run the script**: `python3 scripts/build-library-indexes.py`. Verify it scanned the design-library/ files and built `≥1 decisionTree slug`.
5. **Add the prefix to `serve.py:_PROTOTYPE_CATEGORIES`** so the System tab surfaces the new bucket. The 228 photo/illust/material files already do this; mirror the pattern.
6. **Write the orchestrator playbook** following `photography-orchestrator.md` / `material-orchestrator.md` as a template. §0 reads the **index**, NOT the primer. §2 picks candidates from `decisionTree` + filters on JSON fields.
7. **Write the per-slot / per-element drawer playbook** following `photography-style-enricher.md` / `material-fidelity-author.md` as templates. The drawer reads `design-library/<prefix>-<entryId>.md` directly (it's the source of truth — no library slicing).
8. **Drop the manifest** at `.claude/agents/<id>-orchestrator.manifest.json`. Set `documents.designDoc` to the primer path and `documents.policy` (or another `documents.*` field) to the index path so the System tab card shows both as references.

To edit an existing entry: open `design-library/<prefix>-<entryId>.md` directly. Re-run `python3 scripts/build-library-indexes.py` after committing. The primer file is only edited when the FUNDAMENTALS change (e.g. you learned a new film stock worth naming, or a new universal anti-pattern).

### When NOT to use a library-backed pattern

- If the orchestrator's decision is purely structural (no curated knowledge needed), use a flat playbook (e.g. `interactive-polish-orchestrator` has no library — its decisions come from genre + register, not a catalogue).
- If the orchestrator's catalogue would have < 20 entries, inline them in the playbook directly. The index pattern is for catalogues of 30+ entries where the playbook would balloon if everything lived inline.
- If the catalogue changes per-project (not workspace-wide), it doesn't belong in `docs/research/` — surface it via the project's own metadata (e.g. `workflow/<plan>.json`).
