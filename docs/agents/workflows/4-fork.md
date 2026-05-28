# Workflow 4 — Fork

## 4a. Apply `FORK_REQUEST.md` *(primary path)*

**Trigger:** `FORK_REQUEST.md` appears at repo root.

This is the only fork path now. Editor writes the request; you build the focused prototype + register the branch.

### Shape

```
# Fork request
- Requested at: ISO
- Branch name: <human-readable>
- Suggested slug: <kebab-case>
- Forked from: <parent-slug> (Parent Label)
- Parent project / source root / source entry

## Prompt
<free text>

## Selection
- Frame: <frameId> (Label)
- Frame hash: <hash, optional>
- CSS selector: <selector>

**Snippet at click time:**
```html
<the captured element's outerHTML>
```
```

(May also include `**Scoped frames:**` / `**Scoped primitive variants:**` if no click origin — treat as legacy scope lists.)

### Steps

1. **Reserve a slug.** Use the request's `Suggested slug` if free in `editor/data.js → window.EDITOR_BRANCHES.branches`; else `-2`, `-3`, … Must match `^[a-z0-9][a-z0-9-]{0,40}$`.
2. **Find the element.** Resolve selector against parent source. Drifted → fall back to the snippet's class/text signature; log under `## <ISO> · fork request drift`.
3. **Build a focused prototype** in `source/<slug>/` — **not a clone**:
   - Renders **only** the picked subtree (or a tight composition around it).
   - Inlines **only** CSS and `window.DEMO` keys the subtree transitively reads.
   - Follows `PROTOTYPE.md`.
   - Applies the prompt. Ground each design choice in: token shift, shape change, motion change, or voice change.
   - **Write `prototype.json`** alongside `index.html`. Even for a tiny focused prototype, write at least `{ project, description, genre, viewport, frames: [<one>], arrows: [], lanes: [{ id: "user", label: "User", kind: "user" }], links: [] }`.
4. **Generate the data file** — run Workflow 1 against `source/<slug>/`. Sets `meta.branch`, `meta.branchLabel`, `meta.sourceRoot`, `meta.sourceEntry`, `meta.project` (`<parent> · <branch>`), and `meta.exploration = { prompt, forkedFrom, createdAt, scope, selection }` verbatim.
5. **Register the branch.** Append `{ id, label, file, parent, createdAt }` to `window.EDITOR_BRANCHES.branches` in `editor/data.js`. Leave `active` alone.
6. **Don't touch the parent.** Everything outside `source/<slug>/`, `editor/branches/<slug>.js`, and the `editor/data.js` append stays byte-identical.
7. **Delete `FORK_REQUEST.md`.** Confirm: "Built `<slug>`. Reload the editor to see it."

## 4. Apply `EXPLORATION.md` *(legacy)*

**Trigger:** `source/<slug>/EXPLORATION.md` exists but `source/<slug>/index.html` doesn't.

> Workflow 4a replaces this. Apply only when you find existing manifests or a hand-crafted one.

Same recipe as 4a steps 3–7, but the manifest is named `EXPLORATION.md` and lives inside `source/<slug>/`. Read `forkedFrom`, `prompt`, `scope.frames`, `scope.primitives`, optional `Selection (element-scoped)`. **Don't delete the manifest** — it's the spec of intent.
