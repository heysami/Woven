# Canonical data schema

**This is the single source of truth for where every field lives in `editor/branches/<slug>.js` and `source/<slug>/prototype.json`.** Every subagent that writes a field must reference this doc to know where its output slots in. The planner uses this as the assembly spec in Step 11.

If a subagent and this doc disagree, **this doc wins.** Surface the conflict to the planner.

---

## `editor/branches/<slug>.js`

```js
window.EDITOR_DATA = {
  meta: {
    project:      "Margin",                    // string — display title
    branch:       "main",                      // string — slug; preserved verbatim
    branchLabel:  "Main",                      // string — display name; preserved verbatim
    sourceRoot:   "../source/main",            // string — editor-relative
    sourceEntry:  "../source/main/index.html", // string — editor-relative
    notes:        "Free-text genre/voice note",// string — fed to DESIGN.md description
    defaultFrame: { w: 1440, h: 900 },          // object — Canvas grid cell size
    canvasGap:    120,                          // number — Canvas grid gap
    lanes: [                                    // ← LANES GO HERE, NOT TOP-LEVEL
      { id: "tc",  label: "Training Coordinator", kind: "user"    },
      { id: "pxp", label: "Programme Experience Partner", kind: "user" }
    ],
    dsRef:        { id: "main", version: "<hash>" }, // ← Design system reference. REQUIRED before Workflow 1 runs. See "Design system library nodes" below.
    exploration: { /* present only on exploration branches; preserved verbatim */ }
  },

  // tokens / primitives / library are READ-ONLY mirrors of the DS library node
  // identified by meta.dsRef. The planner writes them by reading the DS file at
  // build time; subagents NEVER write these fields directly. Their canonical
  // home is design-systems/<dsRef.id>/. See "Design system library nodes" below.
  tokens: {
    surfaces: [{ name: "--bg",     value: "oklch(99% 0 0)" }, /* ... */],
    text:     [{ name: "--text",   value: "oklch(20% 0 250)" }, /* ... */],
    semantic: [{ name: "--accent", value: "oklch(54% 0.16 252)", soft: "..." }, /* ... */],
    type:     [{ name: "Display", px: 32, weight: 600, font: "Inter",
                 sample: "...", from: { selector: "...", hash: "" } }, /* ... */],
    radii:    [{ name: "--radius-sm", value: "4px" }, /* ... */],
    shadows:  [{ name: "--shadow-sm", preview: "..." }, /* ... */],
    spacing:  [{ name: "--pad",   value: "16px" }, /* ... */]
  },

  primitives: [
    {
      name:     "Button",
      variants: ["primary", "ghost", "danger"],
      from: {
        primary: { selector: "button.btn-primary", hash: "" },
        ghost:   { selector: "button.btn-ghost",   hash: "" },
        danger:  { selector: "button.btn-danger",  hash: "" }
      },
      htmlByVariant: {
        primary: "<button class=\"btn btn-primary\">Save</button>"
        /* ... */
      }
    }
  ],

  library: [
    { id: "Button.primary", from: "Button", variant: "primary" }
    /* ... */
  ],

  frames: [
    {
      id:          "library",          // string — primary key
      label:       "Library",          // string — display title
      kind:        "page",             // page | state | overlay | form | substep | start | decision | input | trigger | notification | external
      lane:        "user",             // string — references meta.lanes[*].id
      parent:      null,               // string | null — intra-lane only
      hash:        "",                 // string — "#"-prefixed or empty
      entry:       null,               // string | null — bare filename or editor-relative
      setupScript: null,               // string | null — JS evaluated in iframe after load (use window.__pokeBy)
      col:         0,                  // number — Canvas grid column
      row:         0,                  // number — Canvas grid row
      w:           1440,               // number — REQUIRED, owned by Subagent 3 (PrototypeView reads active.w directly; missing = collapse)
      h:           900,                // number — REQUIRED, owned by Subagent 3 (same)
      entities:    ["Reference"]       // string[] — references entities[*].id
    }
  ],

  arrows: [
    { id: "a1", from: "library", to: "library-cmdk", action: "Press ⌘K" }
  ],

  entities: [
    {
      id:    "Reference",
      tag:   "base",                   // base | merged | variant | assoc
      x:     60,                       // number — REQUIRED, owned by Subagent 7 (EntitiesView reads entity.x directly; missing = all cards stack at 0,0)
      y:     60,                       // number — REQUIRED, owned by Subagent 7
      w:     280,                      // number — REQUIRED, owned by Subagent 7 (card width)
      fields: [
        { name: "id",      type: "string", pk: true },
        { name: "title",   type: "string" },
        { name: "authors", type: "string[]" },
        { name: "year",    type: "number" }
      ],
      mergedFrom: undefined,           // string[] — present when tag: "merged"
      extends:    undefined            // string — present when tag: "variant"
    }
  ],

  stateMachines: [
    {
      id:    "application-fsm",
      label: "Application lifecycle",
      entity: "Application",
      field:  "status",
      states: [
        { id: "draft",     label: "Draft",     kind: "initial"  },
        { id: "submitted", label: "Submitted", kind: "pending"  },
        { id: "approved",  label: "Approved",  kind: "terminal" }
      ],
      transitions: [
        { from: "draft",     to: "submitted", on: "TC submits"  },
        { from: "submitted", to: "approved",  on: "PXP approves" }
      ]
    }
  ],

  timelines: [
    {
      id:     "application-timeline",
      label:  "Application review lifecycle",
      anchor: "Application.submittedAt",
      events: [
        { id: "submitted", at: "T+0",  label: "TC submits",         kind: "user"   },
        { id: "queue",     at: "T+1h", label: "PXP queue receives", kind: "system" }
      ]
    }
  ],

  // grids[] documents 2D variance — typically MULTIPLE per prototype. See
  // docs/agents/subagents/10-grids.md for the full lens. The three canonical
  // shapes: form-field × use-case, entity-operation × use-case, classic
  // decision matrix. Use-case axes can be status, gating field-value,
  // timeline, role, or compound.
  grids: [
    {
      id:    "application-form-by-status",
      label: "Application form fields by status",
      rows:  { axis: "ApplicationForm.field",     values: ["title", "summary", "type", "amount", "reviewerNotes"] },
      cols:  { axis: "Application.status",        values: ["draft", "submitted", "approved"] },
      cells: [
        { row: "title",         col: "draft",     render: "required, editable" },
        { row: "title",         col: "submitted", render: "read-only" },
        { row: "type",          col: "draft",     render: "select [standard, premium, enterprise]" },
        { row: "amount",        col: "draft",     render: "required if type=premium" },
        { row: "reviewerNotes", col: "draft",     render: "hidden" },
        { row: "reviewerNotes", col: "submitted", render: "PXP only, editable" }
      ]
    },
    {
      id:    "reference-entity-by-status",
      label: "Reference operations by lifecycle",
      rows:  { axis: "Reference.operation",       values: ["view", "edit", "delete", "cite"] },
      cols:  { axis: "Reference.status",          values: ["draft", "published", "archived"] },
      cells: [
        { row: "edit",   col: "published", render: "creates revision" },
        { row: "delete", col: "published", render: "blocked" },
        { row: "cite",   col: "published", render: "allowed" }
      ]
    },
    {
      id:    "application-by-role-x-status",
      label: "Application view by role × status (classic decision matrix)",
      rows:  { axis: "role",                      values: ["TC", "PXP", "AEM"] },
      cols:  { axis: "Application.status",        values: ["draft", "submitted", "approved"] },
      cells: [
        { row: "TC",  col: "draft",     render: "Edit form" },
        { row: "TC",  col: "submitted", render: "View status (read-only)" },
        { row: "PXP", col: "submitted", render: "Review queue card" }
      ]
    }
  ]
};
```

**Critical placements (these have actually drifted in prior runs — pin them):**

| Field | Lives at | Common wrong placement / failure |
|---|---|---|
| **lanes** | `meta.lanes` | top-level `lanes` (silently ignored — editor reads `D.meta.lanes`) |
| **defaultFrame** | `meta.defaultFrame` | top-level `defaultFrame` |
| **canvasGap** | `meta.canvasGap` | top-level `canvasGap` |
| **frames[i].w/h** | per frame, REQUIRED | omitted → PrototypeView iframe collapses to 0×0 (no default fallback) |
| **frames[i].setupScript** | per frame | per-state-machine or elsewhere |
| **entities[i].x/y/w** | per entity, REQUIRED | omitted → EntitiesView stacks every card at (0,0) |
| **entities per frame** | `frames[i].entities` (array of ID strings) | top-level mapping object |
| **stateMachines / timelines / grids** | top-level | nested under `meta` or `frames` |

---

## Design system library nodes

The **design system is a first-class library asset**, owned by a separate workflow (Workflow 0 / Subagent 0), not by Subagent 1. Branches reference it via `meta.dsRef = { id, version }`. The DS itself lives at project root under `design-systems/<id>/`:

```
design-systems/
└── <id>/                       ← e.g. "main", "dense-rows-experiment"
    ├── styles.css              ← Tokens (:root) + canonical class rules. Source of truth for tokens.
    ├── gallery.html            ← The kitchen-sink page (formerly source/<slug>/design-system.html).
    │                              Every primitive variant rendered in idle state, no behaviour gating.
    │                              Source of truth for primitives.
    ├── DESIGN.md               ← Human-readable rationale: YAML frontmatter + prose.
    │                              Derived by Workflow 3 from styles.css + gallery.html.
    └── meta.json               ← { id, version, label, genre, builtFrom, parentRef? }
                                   version = content hash of (styles.css + gallery.html + DESIGN.md)
                                   builtFrom = workflow-mode spec nodes that generated this DS
                                   parentRef = optional cross-branch reference
```

The editor consumes the DS via a runtime mirror at `editor/design-systems/<id>.js`:

```js
window.EDITOR_DS_<id> = {
  id:       "main",
  version:  "a3f9b2…",
  label:    "v3 — denser rows",
  trio: {
    tokensCss:   "/* :root { … } */",     // verbatim from design-systems/<id>/styles.css
    galleryHtml: "<!doctype html>…",      // verbatim from design-systems/<id>/gallery.html
    designMd:    "---\nname: …"           // verbatim from design-systems/<id>/DESIGN.md
  },
  tokens:     { /* same shape as EDITOR_DATA.tokens — enumerated from styles.css :root */ },
  primitives: [ /* same shape as EDITOR_DATA.primitives — enumerated from gallery.html sections */ ],
  library:    [ /* same shape as EDITOR_DATA.library — one entry per primitive variant */ ],
  meta: {
    genre:     "Linear-style observability — OKLCH greys, hairline borders…",
    builtFrom: [ /* workflow-mode spec nodes that generated this DS */ ],
    parentRef: { branch: "main", version: "…" } // optional — exploration branches inherit main's DS
  }
};
```

### Why DS lives outside source/

Today's `source/<slug>/styles.css` and `source/<slug>/design-system.html` co-locate the DS with feature pages, making them sibling files Subagent 1 has to keep in sync by hand. That's the drift mechanism. Moving the DS to `design-systems/<id>/` makes it a peer of `source/<slug>/`, not a child — so the DS workflow has its own ownership boundary and feature-page generation reads from it instead of writing it.

### How feature pages reference the DS

Each `source/<slug>/index.html` (and every multi-HTML page) loads DS styles via a relative import:

```html
<link rel="stylesheet" href="../../design-systems/<dsRef.id>/styles.css"/>
<link rel="stylesheet" href="styles.css"/>   <!-- optional branch-specific overrides; ideally empty -->
```

DS styles cascade first; branch styles compose on top but **must not** redefine DS-owned class rules. Audit (Subagent 6) checks this.

### Versioning

`meta.json.version` is the content hash of the trio (`styles.css + gallery.html + DESIGN.md`). Branches pin to a version in `meta.dsRef.version`. When Workflow 6b accepts a proposal and updates the DS, the hash changes, and all referencing branches are flagged "regen recommended" (not forced). Branches can be re-pinned by re-running Workflow 1.

### Schema and field ownership

The DS library node is written exclusively by Workflows 0 and 6b. No view subagent writes into `design-systems/<id>/`. Subagent 6 (audit) reads it but does not write it.

| Artifact | Written by | Read by |
|---|---|---|
| `design-systems/<id>/styles.css` | Workflow 0 / 6b | Subagent 1 (via link), Workflow 3, editor |
| `design-systems/<id>/gallery.html` | Workflow 0 / 6b | Subagent 6 (audit), Workflow 3, editor |
| `design-systems/<id>/DESIGN.md` | Workflow 3 (from styles.css + gallery.html) | Editor (DESIGN.md toggle) |
| `design-systems/<id>/meta.json` | Workflow 0 / 6b | Planner (for `meta.dsRef.version`), editor |
| `editor/design-systems/<id>.js` | Workflow 0 / 6b (runtime mirror) | Editor |
| `editor/branches/<slug>.js → meta.dsRef` | Planner (Workflow 1) | Editor, Subagent 1, Subagent 6 |
| `DS_PROPOSAL.md` (at project root) | Subagent 6 (audit) | Workflow 6 (review) |

---

## `source/<slug>/prototype.json`

Same shape as above, minus `tokens` / `primitives` / `library` (those live in source CSS/JSX, not the manifest). `meta` is flattened — its fields become top-level in the manifest:

```jsonc
{
  "project":     "Margin",
  "description": "...",
  "genre":       "...",
  "viewport":    { "w": 1440, "h": 900 },
  "lanes":       [ /* same as meta.lanes above */ ],
  "frames":      [ /* same as EDITOR_DATA.frames */ ],
  "arrows":      [ /* same */ ],
  "links":       [ /* entity↔entity links — see AGENTS.md */ ],
  "stateMachines": [ /* same */ ],
  "timelines":   [ /* same */ ],
  "grids":       [ /* same */ ]
}
```

---

## Subagent → field ownership

Use this table to know which subagent's output writes which field. The planner merges into the schema above; subagents return only their owned slices.

| Subagent | Writes |
|---|---|
| 0 DS-builder | `design-systems/<id>/styles.css, gallery.html, meta.json`; `editor/design-systems/<id>.js` |
| 1 Source | `source/<slug>/*.html, *.js, *.css, data.js` (NOT the data file, NOT `design-systems/`) |
| 2 Canvas | `frames[i].col`, `frames[i].row` |
| 3 Prototype | `frames[i].entry`, `frames[i].hash`, `frames[i].setupScript`, **`frames[i].w`**, **`frames[i].h`** |
| 4 User flow | `frames[i].kind`, `frames[i].lane`, `arrows[]` |
| 5 IA | `frames[i].entities` (echoes `frames[i].parent` from its own enumeration) |
| 6 DS-audit | `DS_PROPOSAL.md` at project root. Does NOT write `tokens` / `primitives` / `library` — those mirror the DS library node, populated by the planner. |
| 7 Entities | `entities[]` (incl. `entities[i].x`, `entities[i].y`, `entities[i].w`), `demoPatches` |
| 8 State machine | `stateMachines[]` |
| 9 Timeline | `timelines[]` |
| 10 Grids | `grids[]` |
| **Planner (Step 4 merge)** | `frames[i].id`, `frames[i].label` (merged from subagents); `meta.lanes` (from Subagent 4); resolves convention-mismatched IDs |
| **Planner (Step 5 meta)** | `meta.project`, `meta.branch`, `meta.branchLabel`, `meta.sourceRoot`, `meta.sourceEntry`, `meta.notes`, `meta.defaultFrame`, `meta.canvasGap`, `meta.exploration`, `meta.dsRef` |
| **Planner (Step 5 DS mirror)** | `tokens`, `primitives`, `library` — copied verbatim from the DS library node identified by `meta.dsRef`. Read, don't enumerate. |
| **Planner (Step 4c reconciliation)** | additional cross-actor handoff arrows → `arrows[]` |

---

## Cross-references in playbooks

Every subagent playbook's Output section should match this schema. If you find a mismatch, this doc is canonical — update the playbook to match, not the other way around.
