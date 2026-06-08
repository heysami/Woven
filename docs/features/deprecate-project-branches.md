# Deprecate project-level branches → multi-prototype-per-project

**Status:** v3.7 — branch deprecation finally finished. The lingering `branch` vocabulary has been renamed to `prototype` everywhere it referred to a `source/<slug>/` subtree.

## Backstory

v3.1 declared project-level branches deprecated. Goal at the time: *"One project owns one `source/` tree. No `source/<slug>/` nesting."* Workflows 4 (fork) and 5 (merge) were removed, `EDITOR_BRANCHES` was deleted, the diff-badge UI was ripped out. The deep cleanup landed.

But v3.4.31 quietly re-introduced `source/<slug>/` nesting under a new name: **starred prototypes**. The projects-landing surfaces multiple starred prototypes per project; each star clicks into the editor with `?branch=<slug>` in the URL; the editor's `D.meta.sourceRoot` mutates accordingly. Same on-disk shape (`source/<slug>/`) as the old branch storage, new conceptual name.

The vocabulary lag meant the codebase still called these things "branches" everywhere — `node.branch`, `?branch=`, `meta.branch`, `branch_dir`, `branch-docs`, `_chat_jsonl_path(project_root, branch)`, the registry's `{branch}` template token. Comments routinely said "branch" when they meant "prototype slug." User reports of this confusion (e.g. the demo-inhouse Canvas-frames node showing 404'd content for `main2` because `editor/data.js` was pinned to `main`) triggered this cleanup.

## What v3.7 ships

### Storage model

- Each project still has ONE `editor/data.js` as a fallback (pre-v3.7 layout).
- Per-prototype data files live at `editor/<slug>.data.js`. Served by `serve.py:translate_path` when the request carries `?prototype=<slug>` (legacy: `?branch=<slug>`).
- Layout sidecar `editor/<slug>.layout.js` is now read AND written per-prototype — `index.html`'s inline loader picks the slug from the URL (was hardcoded to `main.layout.js`).
- Chat history stays project-wide at `editor/chat.jsonl` — no per-prototype chat ledger, consistent with v3.1's earlier decision.

### Vocabulary rename

- URL param: `?prototype=<slug>` is canonical. `?branch=<slug>` accepted as a legacy alias by both the editor boot handler and `serve.py:_qs_prototype()`.
- Workflow-node field: `node.prototype = "<slug>"` for prototype-kind nodes. `node.branch` accepted as a legacy alias by `nodePrototype(node)` (app.js).
- Meta keys: `D.meta.prototype` / `D.meta.prototypeLabel` / `D.meta.activePrototype` are canonical. `D.meta.branch` / `D.meta.branchLabel` / `D.meta.activeBranch` mirrored at boot for back-compat.
- Path template token: `{prototype}` is canonical in `editor/kinds/registry.py` outputsRoot templates. `{branch}` accepted as a legacy alias by the substitution code in `serve.py` and `editor/kinds/reconcile.py`.
- CSS class: `.prototype-docs` / `.prototype-docs-btn` (was `.branch-docs` / `.branch-docs-btn`). The dead `.branch-picker` / `.branch-trigger` / `.branch-menu` / `.branch-item` classes from the v3.1 deletion are untouched here — they have zero references in `app.js` and can be deleted in a follow-up sweep.

### What did NOT change

- **Asset-versioning's "branch" verb stays.** Sibling-asset nodes are still created via `VersioningApi.branch(nodeId, versionId, compositionId)`. That's a different concept from project-level branches — explicitly out of scope per the original v3.1 deprecation doc.
- **`git branch`** references in comments. Different concept again.
- **The screenshot job-queue schema** still uses `job.branch` as a field — that daemon owns its own job shape and gets renamed in its own commit.

## Migration

No automatic migration is run. Existing projects keep working because:
- `nodePrototype(node)` reads `node.prototype || node.branch`, so workflow.json files with `branch:` fields keep loading.
- `_qs_prototype(qs)` reads `prototype || branch` from URL/body, so old browser bookmarks and old client builds keep working.
- The path-template substitution applies `{prototype}` then `{branch}` so registry contracts written either way both resolve.
- A project without a per-prototype `editor/<slug>.data.js` falls back to the project-level `editor/data.js`.

To MIGRATE a project to per-prototype data files (e.g. so multiple prototypes inside one project each get correct frames + sourceRoot): run the frames+arrows slice of Workflow 1 (`Open canvas frames` on the prototype node — confirm prompt offers to generate when no frames data exists for that prototype slug) targeting `source/<slug>/`. The agent writes `editor/<slug>.data.js`.

## Anti-goals (still anti-goals)

- Don't bring back the diff-badge UI. Asset-versioning's lineage chip is the only "what's changed?" affordance going forward.
- Don't try to expose `.archive/branches/` in the editor. It's a one-way escape hatch for the v3.1 migration; users who want to browse it use the filesystem.
- Don't add a "soft branch" replacement (project clone). Asset-versioning's sibling-branch + multi-prototype-per-project already cover the explore-alternatives need.

## Follow-up work

- Delete the dead CSS classes (`.branch-picker`, `.branch-trigger`, `.branch-menu`, `.branch-item`, etc.) in `editor/styles.css` once a manual scan confirms zero references.
- Rename `_chat_jsonl_path(project_root, branch="main")`'s parameter to `_slug` (currently kept for ABI compat, value already ignored).
- Sweep `docs/agents/**/*.md` for `source/<branch>/` references and rename to `source/<prototype>/` to match `capabilities.py` (already renamed).
- Consider migrating existing `workflow.json` files on disk to use `prototype:` instead of `branch:` on prototype-kind nodes. The reader handles both — this would just clean up the on-disk shape.
