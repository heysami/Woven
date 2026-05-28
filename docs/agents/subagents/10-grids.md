# Subagent 10 — Grids (lens: 2D variance across forms / entities / use-cases)

You own the **2D-variance lens**. A grid documents how a form's fields, or an entity's behaviour, varies across use-cases. A prototype will typically have **multiple grids** — one per form whose fields shift across statuses, one per entity whose operations gate on lifecycle, plus any classic role × status decision matrices the source genuinely has.

**Read [`../conventions.md`](../conventions.md) before starting** — universal rules.

## Input (envelope only)

- `branchSlug`, `sourceRoot`, `intent`
- `override: true | false` — true if `GRID_REQUEST.md` exists.

## What a grid is (this is the lens reframe — read carefully)

A grid is a **2D variance map**. One axis is *what* (a form's fields, or an entity's operations). The other axis is *use-case* (a status, a field value, a timeline moment, a role, or a compound of those).

Forget the old "role × status decision matrix" framing. That's one of many shapes; it's not the canonical one.

### The canonical shapes

**A. Form × use-case** (most common)
- **Rows** = the form's fields (in source order).
- **Cols** = use-cases that change how those fields behave.
- **Cells** = field state for that use-case — `"required, default 'Standard'"`, `"hidden"`, `"read-only · 'Submitted'"`, `"editable, options [a,b,c]"`, `"—"`.

**B. Entity × use-case**
- **Rows** = the entity (operations / actions / behaviours — `view`, `edit`, `delete`, `publish`, `cite`, `archive`, `comment`).
- **Cols** = use-cases.
- **Cells** = whether that operation is allowed / how it behaves — `"allowed"`, `"blocked"`, `"creates new revision"`, `"requires approval"`, `"—"`.

**C. Decision matrix** (the classic case — still legal, just one shape among many)
- **Rows** = one variable (often role / persona).
- **Cols** = another variable (often status).
- **Cells** = rendered UI / permission — `"Edit form"`, `"Review queue card"`, `"—"`.

### What "use-case" can be on a column header

- **Status / lifecycle stage** of an entity — `"draft"`, `"submitted"`, `"approved"`, `"archived"`.
- **A specific field value that gates logic** — `Application.type` taking `"standard"` / `"premium"` / `"enterprise"` changes which fields appear and what defaults apply.
- **A timeline moment** — `"T+0"`, `"T+5d"`, `"T+14d after submission"`. The cell describes what's different about the form / entity at that moment.
- **A role / persona** — TC, PXP, admin.
- **A compound** — `"status === submitted AND type === premium"` is a single legitimate use-case if source treats it as one.

You can mix kinds of use-case on a single axis if source does. A grid with cols `["draft", "submitted", "premium+submitted", "approved"]` is fine — that fourth column is a compound use-case that earns its own column because source handles it specially.

## You must read source

### Files you may read

- `source/<slug>/*.html`, `*.js` — form definitions, field renderers, conditional logic.
- `source/<slug>/data.js` — `window.DEMO`, status values, entity field defaults.
- `source/<slug>/entities.json` (if present) — for entity field lists.

## Output

Per [`../data-schema.md`](../data-schema.md): `grids[]`. **Expect to emit multiple — one per form / entity / decision matrix that has 2D variance.**

```json
{
  "grids": [
    {
      "id": "application-form-by-status",
      "label": "Application form fields by status",
      "rows": { "axis": "ApplicationForm.field",      "values": ["title", "summary", "type", "amount", "attachments", "reviewerNotes"] },
      "cols": { "axis": "Application.status",         "values": ["draft", "submitted", "approved", "archived"] },
      "cells": [
        { "row": "title",         "col": "draft",     "render": "required, editable" },
        { "row": "title",         "col": "submitted", "render": "read-only" },
        { "row": "summary",       "col": "draft",     "render": "required, max 280ch" },
        { "row": "summary",       "col": "approved",  "render": "read-only" },
        { "row": "type",          "col": "draft",     "render": "select [standard, premium, enterprise]" },
        { "row": "type",          "col": "submitted", "render": "read-only" },
        { "row": "amount",        "col": "draft",     "render": "required if type=premium" },
        { "row": "attachments",   "col": "draft",     "render": "optional, max 5 files" },
        { "row": "reviewerNotes", "col": "draft",     "render": "hidden" },
        { "row": "reviewerNotes", "col": "submitted", "render": "PXP only, editable" },
        { "row": "reviewerNotes", "col": "approved",  "render": "read-only" }
      ]
    },

    {
      "id": "reference-entity-by-status",
      "label": "Reference operations by lifecycle",
      "rows": { "axis": "Reference.operation",        "values": ["view", "edit", "delete", "cite", "export"] },
      "cols": { "axis": "Reference.status",           "values": ["draft", "published", "archived"] },
      "cells": [
        { "row": "view",   "col": "draft",     "render": "owner only" },
        { "row": "view",   "col": "published", "render": "anyone" },
        { "row": "view",   "col": "archived",  "render": "owner + admin" },
        { "row": "edit",   "col": "draft",     "render": "owner" },
        { "row": "edit",   "col": "published", "render": "creates revision" },
        { "row": "edit",   "col": "archived",  "render": "blocked" },
        { "row": "delete", "col": "draft",     "render": "owner" },
        { "row": "delete", "col": "published", "render": "blocked" },
        { "row": "cite",   "col": "published", "render": "allowed" },
        { "row": "export", "col": "published", "render": "allowed" }
      ]
    },

    {
      "id": "application-form-by-type",
      "label": "Application form fields by application type",
      "rows": { "axis": "ApplicationForm.field",      "values": ["title", "summary", "amount", "currency", "milestones", "deliverables"] },
      "cols": { "axis": "Application.type",           "values": ["standard", "premium", "enterprise"] },
      "cells": [
        { "row": "amount",       "col": "standard",   "render": "hidden" },
        { "row": "amount",       "col": "premium",    "render": "required, USD" },
        { "row": "amount",       "col": "enterprise", "render": "required + multi-currency" },
        { "row": "currency",     "col": "enterprise", "render": "select [USD, EUR, GBP, JPY]" },
        { "row": "milestones",   "col": "premium",    "render": "1-3 rows" },
        { "row": "milestones",   "col": "enterprise", "render": "1-12 rows" },
        { "row": "deliverables", "col": "enterprise", "render": "required" }
      ]
    },

    {
      "id": "application-by-role-x-status",
      "label": "Application view by role × status",
      "rows": { "axis": "role",                       "values": ["TC", "PXP", "AEM"] },
      "cols": { "axis": "Application.status",         "values": ["draft", "submitted", "approved"] },
      "cells": [
        { "row": "TC",  "col": "draft",     "render": "Edit form" },
        { "row": "TC",  "col": "submitted", "render": "View status (read-only)" },
        { "row": "PXP", "col": "submitted", "render": "Review queue card" },
        { "row": "PXP", "col": "approved",  "render": "—" },
        { "row": "AEM", "col": "approved",  "render": "Audit log entry" }
      ]
    }
  ]
}
```

That single output has four grids — and that's normal. If you have a multi-form, multi-entity prototype and you emit zero, something's wrong with the grep.

## Gate (broader than before)

Emit a grid for each **form** OR **entity** OR **decision pair** in source where any of these is true (or `override: true`):

1. **Form variance.** A form has 2+ fields whose state (visibility, editability, default, validation, options) varies across 2+ use-cases → emit a form-grid with fields on rows, use-cases on cols.
2. **Entity variance.** An entity has 2+ operations whose behaviour varies across 2+ use-cases → emit an entity-grid with operations on rows, use-cases on cols.
3. **Decision pair.** Source has conditional rendering keyed on two independent variables, both with 2+ values producing different paths → emit a decision-grid.

**Zero grids is suspicious.** Multi-actor prototypes almost always have at least one form whose fields shift across statuses. If your output has `grids: []`, you probably missed something — re-walk source.

Status-pill colour across statuses → NOT 2D variance on its own. But if the form *also* hides certain fields when status changes, the form-grid captures the *real* variance and the pill is just one of many signals.

## Recipe

### Step 1 — Form-grids (the largest source of grids in most prototypes)

1. Grep for `<form>`, `<input>`, `<select>`, `<textarea>`, conditional field renderers (`{showAmount && ...}`, `if (status === "draft") ...`).
2. For each form you find, enumerate its fields in source order.
3. For each field, check across each use-case axis source uses:
   - Status: does the field render differently when `status === "submitted"` vs `"draft"` vs `"approved"`?
   - Field-value gating: does it depend on another field's value (`if type === "premium"`)?
   - Timeline: does it lock / unlock at a specific T?
   - Role: does PXP see something TC doesn't?
4. **If 2+ fields × 2+ use-cases differ → emit one form-grid per (form, axis) pair.** A single form can produce multiple grids — e.g. `ApplicationForm × status` AND `ApplicationForm × type` are two separate grids.

### Step 2 — Entity-grids

1. For each entity (from Subagent 7's catalog, or grepped `DEMO.<key>` patterns), list the operations source allows on it (view, edit, delete, cite, publish, archive, comment, share, export, ...).
2. For each operation, check whether it varies across status / role / timeline / field-value.
3. **If 2+ operations × 2+ use-cases differ → emit one entity-grid per (entity, axis) pair.**

### Step 3 — Decision-grids (the classic case)

1. Grep for two-variable conditional rendering: `if (role === ... && status === ...)`, nested ternaries on two state variables.
2. Each → one decision-grid.

### Step 4 — Cell content

Cell `render` is a short, scannable description of the variance at that intersection:

- Form-grid cells: `"required, default 'Standard'"`, `"hidden"`, `"read-only · 'Submitted'"`, `"editable, options [a, b, c]"`, `"validates 1-99"`, `"—"`.
- Entity-grid cells: `"allowed"`, `"blocked"`, `"creates revision"`, `"requires approval"`, `"owner only"`, `"—"`.
- Decision-grid cells: `"Edit form"`, `"Review queue card"`, `"View status (read-only)"`, `"—"`.

Use `cell.note` for anything that doesn't fit the render line (a quirk, an exception, a TODO).

### Step 5 — Axis ID conventions

- Form-field axis: `<FormName>.field` (e.g. `ApplicationForm.field`). Row values are the field names in source order.
- Entity-operation axis: `<EntityName>.operation`. Row values are the operation IDs.
- Status axis: `<EntityName>.status`. Col values are the literal status strings from source.
- Field-value axis: `<EntityName>.<fieldName>`. Col values are the driving values.
- Timeline axis: `timeline` (or `<EntityName>.timeline`). Col values are T-offsets or timeline event IDs.
- Role axis: `role`. Col values are persona slugs.

### Step 6 — Sanity check

- **Each grid has at least 2 rows × 2 cols.** A 1×N or N×1 is a list, not a matrix.
- **No grid is fully populated with the same `render` value** — that's degenerate; drop it (or surface it as a 1D table).
- **A form/entity that has zero variance** doesn't earn a grid. Skip silently.
- **You probably emit multiple grids** per prototype. Don't try to combine `Form × status` and `Form × type` into one super-grid — that fakes 3D variance and loses scannability.

## Render-verify your slice

After producing your output, load the editor's **Grids** view and verify:

1. Every grid you emitted appears as a table with the right row / column headers.
2. Each cell shows the `render` string you wrote.
3. The grid is non-trivial — i.e. cell values genuinely vary across both axes.
4. Form-field rows match the actual fields in the form (no fabricated fields, no missed ones).
5. Status / type / role / timeline column values match the literal strings in source.

If a grid is empty / trivial / degenerate when rendered, **remove it from your output**. If a form is missing from your grids that obviously should have one, **add it before reporting done**.

**Screenshot required if `grids[]` is non-empty.**

## Self-audit

- [ ] I read `conventions.md`.
- [ ] I grepped source for forms + enumerated each form's fields.
- [ ] I grepped source for entity operations + checked each across status / role / timeline.
- [ ] I considered field-value gating (`type === premium`), not just status.
- [ ] I considered timeline as a use-case axis where applicable.
- [ ] Each emitted grid satisfies one of the gate clauses.
- [ ] Axes are backed by source code — not invented from labels.
- [ ] All cell `row` / `col` values come from the corresponding axis `values[]`.
- [ ] No grid is degenerate (>70% same `render` value) — degenerate matrices are dropped.
- [ ] Each grid has at least 2 rows × 2 cols (unless override).
- [ ] **A prototype with multiple forms and entities produced multiple grids** — if I emitted zero or one for a complex source, I re-walked.
- [ ] I excluded the storyboard.
- [ ] If gate didn't pass for any form/entity and `override: false`, I correctly returned `grids: []`.
- [ ] **I rendered the Grids view in the editor and confirmed every grid is non-trivial and matches source.** (Screenshot required.)

## Common blindspots

- **Only looking for role × status.** That's one of *many* grid shapes — and not the most common. Most prototypes have form-field × status grids.
- **Treating a single form as one grid when it has variance along multiple axes.** A form that varies by both status AND type produces *two* grids, not one merged super-grid.
- **Missing the form-field axis entirely.** If you only think in terms of decision matrices, you'll skip the biggest source of legitimate 2D variance.
- **Confusing 1D permission table with a grid.** "Admins can edit, viewers can't" with no other variance is 1D. But "TC can edit fields 1-3, PXP can edit field 4, admin can edit all" across status `submitted` vs `approved` is 2D and earns a grid.
- **Confusing status-pill colour variance with form-field variance.** Pill colour alone is 1D. But if the same status change *also* shifts form fields, the form-grid is the real artifact — emit it; the pill is incidental.
- **Treating timeline as out of scope.** Use-cases can be `T+0`, `T+5d`, `T+14d`. If a field locks at T+5d, that earns a timeline column.
- **Compound use-cases dropped.** If source has a special branch for `status === submitted && type === premium`, that's a legitimate compound column header — don't collapse it.
- **Field-value gating dropped.** `type === premium` changes which fields appear → that's a separate grid with `Application.type` as the col axis.
- **Override flag without justification.** `override: true` doesn't justify a degenerate matrix — only emit a grid that genuinely shows variance. If override is on but nothing varies, emit `{ grids: [], note: "..." }`.

## Don't

- Don't think of grids as "rare role × status decision matrices." Most grids are form-field × use-case or entity-op × use-case.
- Don't merge two distinct grids (form × status and form × type) into one fake-3D matrix. Emit two separate grids.
- Don't write frames / arrows / entities / state machines / timelines.
- Don't invent axes / fields / operations not in source.
- Don't emit a degenerate matrix where most cells share one `render` value — drop it.
- Don't emit a 1×N or N×1 — that's a list, not a matrix.
- Don't return `grids: []` for a multi-form / multi-entity prototype without re-walking. Zero is suspicious.
