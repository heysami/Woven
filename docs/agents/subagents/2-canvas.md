# Subagent 2 - Canvas (lens: visual workspace cards)

You own the **canvas-cards lens**. Read source, enumerate what *you* see as a canvas card (a frame that gets a position on the freeform workspace), and assign cell coordinates.

**Read [`../conventions.md`](../conventions.md) before starting** - universal rules + naming convention.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`
- `defaultFrame: { w, h }` (default 1440×900)
- `canvasGap` (default 120)

No orchestrator-provided inventory. You enumerate.

## Output

Per [`../data-schema.md`](../data-schema.md): `frames[i].col`, `frames[i].row`, optional `w`/`h`, and `sections[]`.

```json
{
  "frames": [
    { "id": "library",       "label": "Library",          "col": 0, "row": 0 },
    { "id": "library-cmdk",  "label": "Command palette",  "col": 1, "row": 0 },
    { "id": "settings",      "label": "Settings",         "col": 0, "row": 2 }
  ],
  "sections": [
    { "id": "reading",  "label": "Reading",  "col": 0, "row": 0, "col2": 1, "row2": 0 },
    { "id": "account",  "label": "Account",  "col": 0, "row": 2, "col2": 1, "row2": 2 }
  ]
}
```

Include `label` so reconciliation has the same name across subagents.

## Sections - name the clusters you place

Placing related screens next to each other is only half the job: the editor draws a **section** band around a named rectangle of cells so a 40-screen flow can be browsed and jumped through by group. You already decide the clusters - `sections[]` is where you name them.

- A section is a rectangle of CELLS: `col`/`row` = top-left cell, `col2`/`row2` = bottom-right cell, **both inclusive**.
- Membership is purely **spatial**. Every frame whose `(col, row)` lands inside the rect belongs to the section - there is no per-frame section field, and none should be invented.
- Sections must **not overlap**. Leave one spare row (or column) between two sections so their bands don't collide.
- Name them the way a designer would say them out loud - "Applicant portal", "Admin review", "Onboarding" - not by file path or route.
- A one-off screen that belongs to no group can sit outside every section. Don't stretch a rect to swallow it.
- Optional `tone` picks the band colour: `accent`, `violet`, `amber`, `cyan`, `rose`, `lime`. Omit it and the editor assigns one.
- Users draw, rename, move and resize sections by hand in the editor, and those edits are written straight back into this same data file - there is no second layout file. So the `sections[]` you read may be the user's, not your last run's: keep `id` stable across runs so a renamed section stays renamed, and treat an existing rect as authoritative unless the screens genuinely moved.

## You must read source

### Files you may read

- `source/*.html` - what UI surfaces exist
- `source/*.js` - useState branches that produce distinct rendered states worth placing
- The prototype's editor data file (`editor/<slug>.data.js`, else `editor/data.js`) - **this is the live canvas**. Its `frames[i].col` / `.row` and its `sections[]` are exactly what the user sees and drags; there is no separate layout file. **Preserve any prior `col`/`row` for frame IDs that match the convention** - users arrange frames by hand and that arrangement must survive every regen.

## Enumerate through your lens

A canvas card is anything with renderable UI that the user would want to see on the workspace. Through the canvas lens:

- **Include**: pages, useState branches with distinct UI, modals/sheets, form sub-screens, **every step of a wizard/stepper** (one card per step - a step chooser is tabs wearing a progress bar; do not collapse a wizard to entry + final step).
- **Exclude (Flow-only kinds)**: triggers, notifications, externals, decisions, starts, inputs. These have no UI to render in an iframe.
- **Exclude**: the storyboard `index.html` (workflow documentation, not a screen the user works with).

If you find yourself enumerating a frame whose source page is the storyboard, stop - see `conventions.md` storyboard-exclusion lens reasoning.

## Recipe

1. **Read existing positions from the editor data file.** If it has `frames[i].col` / `.row` for a frame ID matching the convention, preserve it verbatim - that is the user's own arrangement, not a suggestion. Same for a `sections[]` entry's `id`: reuse it so a section the user renamed keeps its name.
2. **Place new frames** (frames you enumerated that aren't already positioned):
   - You don't have a `parent` field handed to you; infer from source structure. Conventions: a frame whose source declares a useState branch (`if (submitted) return ...`) is a child of its declaring page. A modal whose render is conditional in another page is a child of that page.
   - Top-level (no inferred parent) → column 0, next free row.
   - Children → column 1 of parent's row; if taken, column 2, etc.
   - Keep each cluster (an actor's journey, a role's area, a lifecycle stage) in a contiguous block of rows, and leave one empty row between clusters - that gap is where the section bands breathe.
3. **Don't shift existing frames.** Only place new ones. Positions are stable across regens.
4. **Draw the sections.** For each cluster, emit one `sections[]` entry covering exactly the cells that cluster occupies (top-left → bottom-right, inclusive), named the way a designer would say it. Re-use the section `id` from a previous run when the cluster is the same one, so a user's rename sticks.

## Render-verify your slice

After producing your output (and after the orchestrator has written `editor/data.js`), load the editor's **Canvas** view and verify:

1. Every frame you enumerated is visible as a card on the canvas - no card stacked under another.
2. Cards aren't cut off / off-screen at default zoom - pan to confirm.
3. Cards don't overlap. If two cards land at the same `(col, row)`, something went wrong in placement.
4. Children sit next to (column-adjacent to) their parents, not far across the canvas.
5. If users had dragged any frames in a prior run, those positions were preserved - visual check against any previously taken screenshot.

If a card is missing, stacked, off-screen, or shifted from its preserved position, **fix it before reporting done**. Screenshot required.

## Self-audit

Each item requires **evidence**.

- [ ] I read `conventions.md`.
- [ ] I read the existing editor data file and preserved its `col`/`row` for matching IDs.
- [ ] I scanned source for useState branches + modal renders + page files to enumerate canvas-worthy frames.
- [ ] My frame IDs follow the naming convention.
- [ ] I excluded the storyboard, triggers, notifications, externals, decisions, starts, inputs.
- [ ] Existing IDs retained their positions from the editor data file.
- [ ] I wrote only `id` + `label` + `col` + `row` (+ optional `w`/`h`) per frame, plus `sections[]`.
- [ ] **No two frames share the same `(col, row)` pair.** (Stacking bug.)
- [ ] Every cluster I placed has a named `sections[]` rect around it; no two sections overlap; each rect's cells actually contain the frames I meant to group.
- [ ] **I rendered the Canvas view in the editor and confirmed every card is visible, none stacked, none off-screen.** (Screenshot required.)

## Common blindspots

- **Child placed far from parent.** A useState branch frame placed at `(col: 5, row: 8)` when its parent is at `(col: 0, row: 0)` is visually confusing. Keep children column-adjacent (parent col + 1) on the parent's row.
- **Stacking from sloppy placement.** Two new frames computed to the same `(col, row)` because both walked the "next free slot" rule without checking the other's placement. Validate uniqueness before returning.
- **Forgetting modals.** Modal/sheet/popover frames are real UI surfaces with a state branch - include them even though they aren't whole pages.
- **Collapsing wizards.** A stepper's intermediate steps are real UI surfaces too - a 9-step wizard represented as entry + review loses 7 screens. One card per step, placed as a column-adjacent chain of children off the wizard's page.
- **Including triggers/notifications/decisions.** These are Flow-only kinds with no rendered UI. Excluding them is correct; including them gives the editor empty cards.
- **Clusters with no section.** Placing "the admin screens over here, the applicant screens over there" and shipping no `sections[]` leaves the grouping invisible - the reader has to re-derive it from position. If you clustered it, name it.
- **Overlapping or greedy rects.** A section whose rect swallows a neighbouring cluster's cells silently changes what that cluster means. Bands must not overlap, and a rect should not cover an empty separator row.

## Don't

- Don't invent frames not actually present as UI in source.
- Don't include storyboard or Flow-only kinds.
- Don't shift positions of frames already placed in the editor data file - that file IS the canvas the user is looking at.
- Don't write `kind`, `lane`, `parent`, `entry`, `hash`, `setupScript`, `entities`.
- Don't invent a per-frame `section` field - membership is spatial, read off `(col, row)` against each rect.
