# Asset-node versioning + iteration

Design plan for adding per-asset versioning, sibling-branch iteration, adaptive sizing, and lineage indicators to the workflow canvas. Deprecation of the project-level branch feature follows in a separate change.

## 1. Goals

- **Versioning** - every successful run of an `asset` node produces a new version on disk; prior versions remain restorable until evicted.
- **Iteration** - user can revert to any kept version, pin versions for protection, and branch a sibling asset node below the source to keep two lines alive.
- **Adaptive sizing** - asset cards size themselves from the asset's natural aspect (no more fixed 320×200 cards that crop or float).
- **Lineage** - downstream asset nodes display which upstream versions they consumed and visually signal when an upstream has moved on.
- **No cascading invalidation** - reverts do not silently mark downstream "stale". The lineage chip is the only signal; the user decides whether to re-run.

## 2. Out of scope

- Versioning for non-asset kinds (`prompt`, `skill`, `agent`, `folder`, iterators, `design-system`, `ds-brainstorm`). They keep today's overwrite-only behavior. Their `output` *is* hashed for downstream lineage (see §6.3) but no history is kept.
- Project-level branches (`source/<slug>/`, `editor/branches/<slug>.js`, Workflows 4 + 5, fork/merge subagents). These are removed in a separate follow-up plan once versioning is stable.
- Merging two versions of an asset back together. Branching is one-way; merging is left manual via copy/paste in the editor.

## 3. Data model

### 3.0 Two-tier versioning

Asset nodes have **two independent navigable axes**:

1. **Versions** - snapshots of *this asset's own files* (HTML/CSS/JS for a prototype, the image bytes for an image asset). Capped at 20 unpinned.
2. **Compositions** - per-version tuples of `(sub-asset → sub-version)` describing which versions of *upstream sub-assets* this view is locked against. Compositions are virtually free (just a JSON entry + thumb) and do NOT count against the 20-version cap. Separate cap of **50 unpinned compositions per parent version**.

For an asset with no sub-asset upstream (e.g. a single image), the composition axis is degenerate and the picker hides it.

### 3.1 Asset node shape (additions)

```jsonc
{
  "id": "br_remix_p1_set",
  "kind": "asset",
  "assetKind": "html-set",
  "x": 1200, "y": 400,
  "w": null, "h": null,                // null = adaptive (see §5)
  "size": {
    "naturalAspect": 1.6,              // computed from asset content
    "scale": "fit-canvas",             // small | fit-canvas | large | custom
    "minW": 280, "maxW": 720
  },
  "versions": [
    {
      "id": "v_01HXYZ...",             // ulid; lexicographically sortable
      "createdAt": "2026-06-02T15:30:00Z",
      "runId": "run-uuid",
      "files": [                       // paths relative to the version dir
        "page1.html",
        "styles.css",
        "app.js"
      ],
      "canonicalPaths": [              // paths under source/ that this version materialises to
        "source/_pages/page_1/index.html",
        "source/_pages/page_1/styles.css",
        "source/_pages/page_1/app.js"
      ],
      "thumbPath": "workflow/runs/br_remix_p1_set/v_01HXYZ/thumb.png",
      "label": null,                   // user-set name, optional
      "pinned": false,
      "branchedFrom": null,            // { nodeId, versionId } if this version was seeded by a branch
      "consumedVersions": {
        "<upstream-id>": { "outputHash": "sha256:..." }         // non-asset upstream (no compositions)
      },
      "compositions": [
        {
          "id": "comp_01HXAA...",
          "consumedSubVersions": {                              // sub-asset pins
            "img_hero": "v_h2",
            "nav_icon": "v_n1"
          },
          "thumbPath": "workflow/runs/<nodeId>/<vid>/compositions/<compId>/thumb.png",
          "label": null,
          "pinned": false,
          "createdAt": "..."
        }
      ],
      "activeCompositionId": "comp_01HXAA..."
    }
  ],
  "activeVersionId": "v_01HXYZ..."
}
```

Notes:
- **Asset upstream goes through `compositions[].consumedSubVersions`**, not through the version-level `consumedVersions` (which is now reserved for non-asset upstream).
- **Auto-locked composition on run** - every successful run snapshots the current sub-asset actives as `compositions[0]` of the new version (see §6.0).
- **Compositions are local-view only** - switching a composition does NOT flip sub-asset actives globally (see §6.0 + §7.2).

### 3.2 Sibling-branch shape

When user clicks "Branch from this version" on node `A` version `v_xyz`, a new node `A_branch_1` is inserted on the canvas with:

```jsonc
{
  "id": "A_branch_1",                   // base id + collision suffix
  "kind": "asset",
  "assetKind": "html-set",              // copied from source
  "x": A.x, "y": A.y + A.h + 80,       // see §5.3 for collision-shift
  "branchedFrom": { "nodeId": "A", "versionId": "v_xyz" },
  "versions": [ /* one entry, deep copy of A.versions[v_xyz], with new vid */ ],
  "activeVersionId": "<new vid>"
}
```

Outgoing edges from `A` are not copied. The branched node starts disconnected; user wires consumers as desired.

### 3.3 Lineage

Two upstream cases, two storage slots:

- **Asset upstream** → `versions[].compositions[].consumedSubVersions` records `{ subAssetId: versionId }`. Divergence = sub-asset's `activeVersionId !== versionId` recorded in the active composition.
- **Non-asset upstream** (prompt/skill/agent output) → `versions[].consumedVersions` records `{ outputHash: sha256(node.output) }`. Divergence = upstream's current hash differs.

This keeps non-asset upstream out of the version system, and keeps asset upstream inside the composition layer so combinations are first-class.

### 3.4 Sub-asset declaration

For the daemon to know which upstream edges are sub-assets (versus producer-only upstream like a PRD), the registry per-id config OR the producing subagent's MANIFEST.json declares `subAssetInputs: [<upstreamNodeId>...]`. Anything not in that list is treated as non-asset upstream and goes to `consumedVersions`.

## 4. Storage layout

### 4.1 Disk

```
project-root/
├── source/                                 ← live working tree (single state; mirrors active versions + active composition)
│   ├── _pages/page_1/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   ├── _shared/chrome.html
│   └── _assets/img_hero/hero.png
├── workflow/
│   ├── workflow.json
│   ├── runs/                               ← version archive
│   │   └── <nodeId>/
│   │       ├── <versionId>/
│   │       │   ├── meta.json               ← copy of versions[] entry
│   │       │   ├── thumb.png
│   │       │   ├── index.html
│   │       │   ├── styles.css
│   │       │   ├── app.js
│   │       │   └── compositions/
│   │       │       └── <compositionId>/
│   │       │           ├── meta.json
│   │       │           └── thumb.png
│   │       └── ...
│   └── views/                              ← per-composition materialised trees (hardlinks where possible)
│       └── <nodeId>/<versionId>/<compositionId>/
│           ├── _pages/page_1/index.html    ← from runs/<nodeId>/<vid>/
│           └── _assets/img_hero/hero.png   ← from runs/img_hero/<subVid>/
└── ...
```

### 4.2 Why dual-path (source/ live + workflow/runs/ archive)

Earlier sketch proposed canonical files under `workflow/runs/<nodeId>/<activeVersionId>/`. On closer look, that breaks cross-asset references - e.g. `_pages/page_1/index.html` importing `../_shared/chrome.html` would need traversal across run folders, and would shatter every time either asset gets a new version.

The dual-path model:

- **Subagents keep writing to canonical paths** (`source/_pages/page_1/...`) - no subagent surgery required.
- **Daemon snapshots after each successful run** by copying the just-written files into `workflow/runs/<nodeId>/<newVid>/`.
- **Revert** copies a `workflow/runs/<nodeId>/<vid>/` tree back over `source/<canonical paths>`.
- **Cross-asset references stay relative** under `source/` and never break.

Trade-off: the live tree is always exactly the union of active versions, never an arbitrary mix. That matches the user's "default shows only the latest" intent.

### 4.3 Eviction

Two independent caps:

- **Versions cap: 20 unpinned per node** (overridable per-id). Eviction at end of successful snapshot: if `unpinned > 20`, delete oldest unpinned `versions[]` entries and their `workflow/runs/<nodeId>/<vid>/` dirs (which cascades to all their compositions).
- **Compositions cap: 50 unpinned per parent version** (overridable per-id). Eviction at end of composition save: if `unpinned > 50`, delete oldest unpinned `compositions[]` entries and their materialised `workflow/views/<nodeId>/<vid>/<compId>/` trees.

Active version + active composition are never evicted, regardless of pin state.

### 4.4 View materialisation

When a composition is created or switched to, daemon ensures `workflow/views/<nodeId>/<vid>/<compId>/` exists with:

- The parent asset's own files at their canonical relative paths (hardlinked from `workflow/runs/<nodeId>/<vid>/`).
- Each sub-asset's files at their canonical relative paths (hardlinked from `workflow/runs/<subAssetId>/<subVid>/`).

Hardlinks are zero-cost; fallback to copy on filesystems that don't support them (rare; macOS + Linux fine). The iframe in the canvas loads from this view dir so relative imports inside the HTML just work without rewriting.

The "live" `source/` tree is treated as the materialised view of the currently-active version + active composition: when the user reverts or switches, daemon refreshes `source/` from the corresponding view dir.

## 5. Adaptive sizing

### 5.1 Problem

Today's asset cards have fixed `w, h`. Prototype html-sets either crop (when smaller than card) or float in too-big cards. Branching below stacks unpredictably because heights don't reflect content.

### 5.2 Model

```jsonc
"size": {
  "naturalAspect": 1.6,           // derived per assetKind
  "scale": "fit-canvas",          // small (320w) | fit-canvas (480w) | large (720w) | custom
  "minW": 280, "maxW": 720
}
```

- `naturalAspect` derivation by `assetKind`:
  - `html-set`, `html` → from viewport in producing node's `spec` (e.g. `bp_ds_gen.spec.viewport`), fall back to 16:10.
  - `image` → image intrinsic aspect.
  - `svg` → declared viewBox aspect.
  - `markdown`, `text` → no aspect; bounded height with overflow scroll, height fits content up to `maxH = 480`.
- Card layout:
  - `width = clamp(scale * baseW, minW, maxW)` where `baseW ∈ {320, 480, 720}` per `scale`.
  - `height = width / naturalAspect + chromeHeight` (chrome ≈ title bar + version strip handle ≈ 56px).
- User drag on a resize handle sets explicit `w, h`, switches `scale: "custom"`. A "↺ Auto size" affordance clears `w, h` back to adaptive.
- Every version thumb inside the strip uses the same aspect for visual consistency.

### 5.3 Branch-below placement

- Sibling lands at `(source.x, source.y + source.h + 80)`.
- Collision pass: if any existing node intersects the proposed rect, shift `x` right in 32px steps until clear, capped at +400px; if still colliding, place anyway (user drags).
- Adaptive sizing makes the +80 gutter actually reliable, which is the whole point of fixing sizing first.

## 6. Frontend UI

### 6.0 Composition behaviour

- **Switching a composition is local** - sub-asset nodes' `activeVersionId`s do NOT change. The prototype iframe re-points at the matching `workflow/views/<nodeId>/<vid>/<compId>/` tree.
- **Each sub-asset chip carries a small "↥ follow" affordance** - one click flips the sub-asset's global `activeVersionId` to the version this composition pins. Useful when the user decides the composition is the new truth.
- **Compositions auto-create on prototype run** - every successful run snapshots the current sub-asset actives as `compositions[0]` of the new version. Sequence: snapshot files → record sub-asset pins → save composition → mark both as active.
- A "Save current combination" button in the picker lets the user persist a non-run composition (e.g. they reverted a sub-asset manually and want to bookmark this combination without re-running the prototype).

### 6.1 Asset card (active state)

- Renders the active version's thumb in the body, scaled to card width.
- Title bar shows: title · version label (e.g. `v7` or pinned label) · pin/unpin glyph.
- Footer (always present, low-key): version chip strip - small dots, one per `versions[]` entry, active is bigger; click any dot opens the version picker.
- For non-html assets, body shows the appropriate preview (img tag, markdown render, etc.).

### 6.2 Version picker (two-pane drawer beneath the card)

Two-pane layout: versions on the left, compositions on the right.

- **Left pane - versions** (newest first, scrollable):
  - low-fi thumb (consistent aspect)
  - timestamp (relative: "2m ago", "yesterday 14:32")
  - label if set
  - composition-count chip (e.g. `3 combos`)
  - row actions: **Pin / Unpin** · **Rename** · **Revert** · **Branch below**
  - active version highlighted; pinned versions show a pin badge
  - footer: `"7 of 20"`
- **Right pane - compositions of the selected version** (newest first):
  - composition thumb
  - sub-version line (e.g. `img_hero v1 · nav_icon v2`)
  - label if set
  - row actions: **Pin / Unpin** · **Rename** · **Switch to** · **Branch below**
  - active composition highlighted
  - footer: `"3 of 50"` + a `+ Save current combination` button
- For assets with no sub-asset inputs the right pane is hidden and the drawer collapses to a single pane.
- Overlay rendering; dismissible on outside-click.

### 6.3 Downstream lineage chip

- Each asset card with upstream inputs shows one chip per upstream:
  - **Asset / sub-asset upstream**: `← img_hero v2` (neutral) when active composition's recorded pin == upstream's current active version; `← img_hero v2 → v3` (warm color) when upstream has moved on. A small **↥ follow** glyph on the chip flips the upstream's active to match this composition's pin.
  - **Non-asset upstream**: `← <upstream-id>` with a subtle dot; warm dot when stored `outputHash` differs from current.
- Click a chip → focus the upstream node + open its picker scrolled to the consumed version.

### 6.4 Snapshot capture flow (thumbnails)

- After dispatch completes and SSE emits `{ node, runStatus: "done", newVersionId }`, the frontend:
  1. Creates a hidden iframe pointed at the asset's entry file (or canonical-path entry for html-set).
  2. Waits for `iframe.contentWindow.onload` + one rAF.
  3. Runs `html2canvas-pro` (already loaded) at 320px width, scaled to `naturalAspect`.
  4. POSTs the PNG to `/__workflow/node/<id>/version/<vid>/thumb`.
- For non-html assets (image, svg) the daemon writes the thumb directly during snapshot.

## 7. Daemon (serve.py) changes

### 7.1 Extended `_workflow_node_run` ([serve.py:5595](../../editor/serve.py))

- Before dispatch:
  - Read sub-asset declarations from registry per-id config or producing manifest.
  - Compute `consumedVersions` (non-asset upstream) by hashing each upstream's `output`.
  - Snapshot current sub-asset actives into a pending `consumedSubVersions` map.
- After successful run (status flips to `done`):
  - Allocate `vid = ulid()`.
  - List files the subagent wrote (use MANIFEST.json if present, else scan `outputsRoot`).
  - Copy them to `workflow/runs/<nodeId>/<vid>/`.
  - Append new version entry to `node.versions[]` with the captured `consumedVersions`.
  - Allocate `compId = ulid()`; create `compositions[0]` with the captured `consumedSubVersions`; set `activeCompositionId = compId`.
  - Materialise `workflow/views/<nodeId>/<vid>/<compId>/` (hardlink fallback to copy).
  - Set `node.activeVersionId = vid`.
  - Run version eviction (§4.3 - cascades to per-version composition dirs).
  - Persist workflow.json, emit SSE.
- Failed runs do **not** create a version or composition.

### 7.2 New endpoints

**Version-level:**

| Method | Path | Purpose |
|---|---|---|
| POST | `/__workflow/node/<id>/version/<vid>/revert` | Set `activeVersionId = vid`; activate its `activeCompositionId`; refresh `source/` from the corresponding view dir; emit SSE. |
| POST | `/__workflow/node/<id>/version/<vid>/pin` | Toggle version `pinned`. |
| POST | `/__workflow/node/<id>/version/<vid>/label` | Set/clear version label. |
| POST | `/__workflow/node/<id>/version/branch` | Body: `{sourceVersionId, sourceCompositionId?}`. Create sibling node below; deep-copy version files and the picked composition. |
| POST | `/__workflow/node/<id>/version/<vid>/thumb` | Body: PNG bytes; write `runs/<id>/<vid>/thumb.png`. |
| DELETE | `/__workflow/node/<id>/version/<vid>` | Manual prune. Rejects if active or pinned. Cascades to its compositions. |

**Composition-level:**

| Method | Path | Purpose |
|---|---|---|
| POST | `/__workflow/node/<id>/version/<vid>/composition/<compId>/switch` | Set version's `activeCompositionId = compId`; refresh `source/` from the view dir (no global sub-asset flip). |
| POST | `/__workflow/node/<id>/version/<vid>/composition/<compId>/pin` | Toggle composition `pinned`. |
| POST | `/__workflow/node/<id>/version/<vid>/composition/<compId>/label` | Set/clear composition label. |
| POST | `/__workflow/node/<id>/version/<vid>/composition/<compId>/thumb` | Upload composition thumb (PNG). |
| POST | `/__workflow/node/<id>/version/<vid>/composition` | Body: `{subVersions: {subId: vid}}`. Save current combination as a new composition. |
| DELETE | `/__workflow/node/<id>/version/<vid>/composition/<compId>` | Manual prune. Rejects if active or pinned. |

**Sizing:**

| Method | Path | Purpose |
|---|---|---|
| POST | `/__workflow/node/<id>/size` | Body: `{w, h}` or `{auto: true}`. Persist sizing override. |

All endpoints take the same `?project=` requirement as existing workflow endpoints in workspace mode.

### 7.3 Reconciler updates ([editor/kinds/reconcile.py](../../editor/kinds/reconcile.py))

- On load, migrate legacy asset nodes lacking `versions[]`:
  - If `node.paths[]` and canonical files exist on disk → synthesize `versions[0]` from the current state (no thumb yet; captured next time the canvas loads it).
  - Set `activeVersionId` to the synthesized version.
- Validate: every `activeVersionId` resolves; every `versions[].id` is unique; pinned + active relationship sane.

## 8. Registry contract changes ([editor/kinds/registry.py](../../editor/kinds/registry.py))

Add to `asset` kind:

```python
"versioning": {
    "enabled": True,
    "maxUnpinnedVersions": 20,
    "maxUnpinnedCompositions": 50,
    "snapshotRoot": "workflow/runs/{nodeId}/{versionId}/",
    "viewRoot": "workflow/views/{nodeId}/{versionId}/{compositionId}/",
    "thumbStrategy": "canvas-html2canvas",  # or "daemon-direct" for image/svg
},
"adaptiveSize": {
    "enabled": True,
    "scaleDefault": "fit-canvas",
    "minW": 280,
    "maxW": 720,
    "aspectFrom": "viewport|image|markdown",
}
```

Per-id overrides may:
- raise/lower either cap independently
- declare `subAssetInputs: [<nodeId>...]` if not inferable from edges + producer manifest
- pin specific synthesized versions on first run
- override `naturalAspect` directly (e.g. mobile chrome asset = 9:16)

## 9. Subagent contract impact

Subagents that produce asset content (notably the `1V-*` drawers) need ONE change: emit a `MANIFEST.json` in their write root listing the files they produced. The daemon's snapshot step reads this to know exactly what to copy. Without it, the daemon falls back to scanning the declared `outputsRoot`, which works but is fuzzier when subagents write outside their declared scope.

Manifest format:

```jsonc
{
  "nodeId": "bs_html_1",
  "runId": "run-uuid",
  "files": [
    { "path": "_pages/page_1/index.html",  "role": "entry" },
    { "path": "_pages/page_1/styles.css",  "role": "asset" },
    { "path": "_pages/page_1/app.js",      "role": "asset" }
  ],
  "subAssetInputs": [
    { "nodeId": "img_hero",  "mountPath": "_assets/img_hero/" },
    { "nodeId": "nav_icon",  "mountPath": "_assets/nav_icon/" }
  ]
}
```

`subAssetInputs[].mountPath` tells the daemon where to materialise that sub-asset's files within the view dir. The producing subagent is the only place that knows where in the HTML it references those assets, so it owns this declaration.

This is additive - existing subagents keep working until updated; the fallback handles them.

## 10. Edge cases

- **Concurrent runs of the same node** - already prevented by `runStatus: running` gate. Confirmed safe.
- **Failed runs** - no version or composition created; failed canonical files remain in `source/` (user can see what failed). Next successful run creates the next version.
- **Subagent writes outside declared scope** - fallback scan picks up declared `outputsRoot`; out-of-scope writes are not versioned (warning logged).
- **Branch then immediately re-run source** - sibling is unaffected; lineage on sibling's `branchedFrom` still points at the (now non-active) source version.
- **Delete the source node of a branch** - sibling's `branchedFrom` becomes a dangling reference. Show muted "(source deleted)" in the picker; functionality unaffected.
- **Revert active version / switch active composition** - no-op; UI grays out the action.
- **Pin all 20 versions** - eviction throws; new run still succeeds but emits a warning chip on the node "history full, unpin some versions". Same for 50-composition cap.
- **Pinned version's file deleted out-of-band** - daemon detects on revert; surfaces error toast.
- **Sub-asset upstream node deleted** - its compositions can no longer materialise. Daemon marks affected compositions with `degraded: true`; picker shows a muted "(missing sub-asset)" badge; switching to a degraded composition falls back to the current global active for that slot.
- **Sub-asset version evicted but a composition references it** - promote the composition's referenced version to pinned automatically, OR fail eviction and pick the next-oldest candidate. Pick the latter (simpler, no surprise auto-pins).

## 11. Migration (existing projects)

- On first daemon start after upgrade: walk every project's `workflow.json`, run the reconciler migration in §7.3 for each asset node. Idempotent.
- No data loss: legacy `paths[]` becomes `versions[0]`, file contents on disk become the snapshot, current state becomes active.

## 12. Testing strategy

- **Unit (Python)** - version + composition eviction (independent caps), manifest parsing, sub-asset declaration resolution, lineage hash compute, view-dir hardlink/copy fallback.
- **Integration (daemon)** - POST run → snapshot + auto-composition + view materialised. POST composition switch → view dir refresh, no sub-asset active change. POST sub-asset follow → sub-asset active flips, prototype iframe stays the same. POST branch → sibling with copied files + chosen composition.
- **Frontend manual** - two-pane picker, sub-asset chip + follow glyph, pin/revert/branch flows on both axes, adaptive sizing across `html-set` + `image` + `markdown`, lineage chip changes when sub-asset re-runs.
- **Regression check** - run an existing project through workflow 1 end-to-end; confirm no crash on legacy nodes; confirm assets without sub-asset inputs collapse the right pane.

## 13. Phases

| Phase | Scope | Deliverable |
|---|---|---|
| **1** | Data + storage | Schema + migration + snapshot writer in daemon. No UI yet. |
| **2** | Daemon endpoints | Revert, pin, label, branch, thumb, delete, size endpoints. |
| **3** | Adaptive sizing | Card layout refactor; resize handle; auto-size button. |
| **4** | Version picker | Drawer UI, thumbnail capture, pin/revert/branch flows wired. |
| **5** | Lineage chip | Per-upstream chip on downstream asset cards; click-to-focus upstream. |
| **6** | Documentation | AGENTS.md, orchestrator.md, subagent playbooks, registry README. |
| **7** | (Follow-up) Deprecate project branches | Separate plan. |

## 14. Open questions for future thought

- Should branched sibling auto-receive a label like `"branch of v7"` for quick identification?
- Lineage chip on a multi-page asset that consumes a *set* of upstream assets - show one chip per page, or aggregate?
- When a subagent writes a `MANIFEST.json` but lists a file it didn't actually write, how loud do we fail?
- Should the version picker show diff hints between adjacent versions (file-count delta, "+12 lines in app.js")? Out of scope for v1, worth considering later.
