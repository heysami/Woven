# Subagent 2 — Canvas (lens: visual workspace cards)

You own the **canvas-cards lens**. Read source, enumerate what *you* see as a canvas card (a frame that gets a position on the freeform workspace), and assign cell coordinates.

**Read [`../conventions.md`](../conventions.md) before starting** — universal rules + naming convention.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`
- `defaultFrame: { w, h }` (default 1440×900)
- `canvasGap` (default 120)

No planner-provided inventory. You enumerate.

## Output

Per [`../data-schema.md`](../data-schema.md): `frames[i].col`, `frames[i].row`, optional `w`/`h`.

```json
{
  "frames": [
    { "id": "library",       "label": "Library",          "col": 0, "row": 0 },
    { "id": "library-cmdk",  "label": "Command palette",  "col": 1, "row": 0 },
    { "id": "settings",      "label": "Settings",         "col": 0, "row": 1 }
  ]
}
```

Include `label` so reconciliation has the same name across subagents.

## You must read source

### Files you may read

- `source/*.html` — what UI surfaces exist
- `source/*.js` — useState branches that produce distinct rendered states worth placing
- Existing `source/prototype.json` — **preserve any prior `col`/`row` for frame IDs that match the convention**. Users drag frames manually; positions must be stable across regens.

## Enumerate through your lens

A canvas card is anything with renderable UI that the user would want to see on the workspace. Through the canvas lens:

- **Include**: pages, useState branches with distinct UI, modals/sheets, form sub-screens.
- **Exclude (Flow-only kinds)**: triggers, notifications, externals, decisions, starts, inputs. These have no UI to render in an iframe.
- **Exclude**: the storyboard `index.html` (workflow documentation, not a screen the user works with).

If you find yourself enumerating a frame whose source page is the storyboard, stop — see `conventions.md` storyboard-exclusion lens reasoning.

## Recipe

1. **Read existing positions.** If `source/prototype.json` has `frames[i].col` / `.row` for a frame ID matching the convention, preserve it.
2. **Place new frames** (frames you enumerated that aren't already positioned):
   - You don't have a `parent` field handed to you; infer from source structure. Conventions: a frame whose source declares a useState branch (`if (submitted) return ...`) is a child of its declaring page. A modal whose render is conditional in another page is a child of that page.
   - Top-level (no inferred parent) → column 0, next free row.
   - Children → column 1 of parent's row; if taken, column 2, etc.
3. **Don't shift existing frames.** Only place new ones. Positions are stable across regens.

## Render-verify your slice

After producing your output (and after the planner has written `editor/data.js`), load the editor's **Canvas** view and verify:

1. Every frame you enumerated is visible as a card on the canvas — no card stacked under another.
2. Cards aren't cut off / off-screen at default zoom — pan to confirm.
3. Cards don't overlap. If two cards land at the same `(col, row)`, something went wrong in placement.
4. Children sit next to (column-adjacent to) their parents, not far across the canvas.
5. If users had dragged any frames in a prior run, those positions were preserved — visual check against any previously taken screenshot.

If a card is missing, stacked, off-screen, or shifted from its preserved position, **fix it before reporting done**. Screenshot required.

## Self-audit

Each item requires **evidence**.

- [ ] I read `conventions.md`.
- [ ] I read existing `prototype.json` and preserved its `col`/`row` for matching IDs.
- [ ] I scanned source for useState branches + modal renders + page files to enumerate canvas-worthy frames.
- [ ] My frame IDs follow the naming convention.
- [ ] I excluded the storyboard, triggers, notifications, externals, decisions, starts, inputs.
- [ ] Existing IDs from `prototype.json` retained their positions.
- [ ] I wrote only `id` + `label` + `col` + `row` (+ optional `w`/`h`).
- [ ] **No two frames share the same `(col, row)` pair.** (Stacking bug.)
- [ ] **I rendered the Canvas view in the editor and confirmed every card is visible, none stacked, none off-screen.** (Screenshot required.)

## Common blindspots

- **Child placed far from parent.** A useState branch frame placed at `(col: 5, row: 8)` when its parent is at `(col: 0, row: 0)` is visually confusing. Keep children column-adjacent (parent col + 1) on the parent's row.
- **Stacking from sloppy placement.** Two new frames computed to the same `(col, row)` because both walked the "next free slot" rule without checking the other's placement. Validate uniqueness before returning.
- **Forgetting modals.** Modal/sheet/popover frames are real UI surfaces with a state branch — include them even though they aren't whole pages.
- **Including triggers/notifications/decisions.** These are Flow-only kinds with no rendered UI. Excluding them is correct; including them gives the editor empty cards.

## Don't

- Don't invent frames not actually present as UI in source.
- Don't include storyboard or Flow-only kinds.
- Don't shift positions of frames already placed in `prototype.json`.
- Don't write `kind`, `lane`, `parent`, `entry`, `hash`, `setupScript`, `entities`.
