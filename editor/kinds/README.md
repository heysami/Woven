# editor/kinds — node-kind contracts (human guide)

The single source of truth for every workflow node kind is [`registry.py`](registry.py). This README is the prose companion that explains _why_ each contract is shaped the way it is — read this to understand the system, read the registry to know exactly what fields exist and what's enforced.

Authoritative cross-links: [WORKFLOW_TRUTHFULNESS_PLAN.md](../../WORKFLOW_TRUTHFULNESS_PLAN.md) (project root) is the architectural plan this directory implements.

## The ten principles

Every contract here uphold these (from §1 of the plan):

1. **Single source of truth per fact** — every per-kind claim lives in `registry.py`.
2. **Folder, not list** — producers drop everything into an `outputsRoot` folder; consumers pattern-route the upstream folder.
3. **Must consume (strict)** — unhandled files block `runStatus: done`.
4. **Complexity → agent kind** — full HTML pages, multi-file builds, anything with embedded JS/CSS belong to `agent` kind, not `skill·llm`.
5. **Multiplicity → task-subagents** — N parallel outputs MUST fan out into N cold-isolated subagent sessions in parallel.
6. **Detours preserved by construction** — chat refinements that add new files flow through the folder convention automatically.
7. **Lineage is visible** — every node renders its consumed/produced folder manifest.
8. **Status does not lie** — completion criteria validated; reconciler surfaces drift.
9. **Scaffold is a starting point, not a cap** — `_ds_brainstorm/` can grow to 4, 5, 6+ variants; reconciler auto-promotes.
10. **Canvas refreshes itself** — file-watcher + SSE `asset-changed` event keeps cards in sync without manual reload.

## The kinds catalogue

15 kinds. Group them by category:

### Container kinds — hold data, no dispatch

| Kind | Purpose |
|---|---|
| `folder` | Reads a file or lists a directory. Exposes contents as upstream context. |
| `prompt` | Static markdown. When `auto: true`, hydrated from upstream skill/agent output. |
| `asset` | File reference. Refreshes itself via SSE `asset-changed` (Deliverable 1). |
| `color-palette` | Token set — colors. Wired as upstream into design-system or prototype. |
| `typography` | Token set — fonts/sizes. Wired similarly. |
| `prototype` | Live iframe of the source/ folder. User drives via Expose to create asset children. |

### Producer kinds — make things

| Kind | Dispatch | Why |
|---|---|---|
| `skill` (llm) | `inline-server-call` | RESTRICTED to small pure-text transforms. Chunking, summarization, classification. Not full HTML pages. |
| `agent` | `single-subprocess` | Visible Claude Code session with chat panel + transcript + kill button. For complex artifacts. |
| `ds-brainstorm` | `task-subagents` | Each variant is a cold-isolated subagent session. Diverges on `inputs.spec.genre`. Variant count is open-ended. |

### Consumer kinds — ingest upstream + produce

| Kind | Dispatch | Why |
|---|---|---|
| `design-system` | `single-subprocess` | Reads picked variant's outputsRoot exhaustively (must-consume strict), produces tokens + primitives + shells. Stage D pause-after. |

### Iterator kinds — N parallel outputs

| Kind | Dispatch | Pattern |
|---|---|---|
| `iterator-refiner` | `client-iterator` | Browser-side loop spawning 2 isolated agent sessions in conversation. Already correct. |
| `iterator-remix` | `task-subagents` | N cold-isolated alt subagents per page. 3 pages × 3 alts = 9 concurrent. |
| `iterator-repeater` | `task-subagents` | N cold-isolated repeats of an upstream operation with divergent prompts. |
| `iterator-blend` | `single-subprocess` | N weighted inputs blended into 1 output. Not a fan-out. |

### Decoration kinds — purely visual

| Kind | Notes |
|---|---|
| `section` | Manual-only. Figma-style frame. Never created by orchestrator. |

## Save vs. commit — the most important rule

This is the rule that protects manual canvas use (Principle 11):

```
SAVE   → permissive. Optional fields may be empty.
         A field marked required=True is required AT COMMIT, not at save.
         Only structural fields (id, kind, x, y) are mandatory at save.

COMMIT → strict. Completion criteria checked.
         Must-consume strict — unhandled upstream files block done.

STATUS → permissive for "running", strict for "done".
         Marking done requires completion criteria satisfied.
```

A user dragging a prompt node onto a blank canvas with empty text **must save successfully**. A user wiring up a manual asset node pointing at a file they're about to create **must save successfully**. Only when the producer claims `runStatus: done` does the contract enforce that the work is real.

## The folder convention

Every producer kind declares an `outputsRoot`. Examples:

```
ds-brainstorm  →  source/{branch}/_ds_brainstorm/{variant}/
                    index.html
                    assets/
                      driver-constellation.png
                      net.js
                    spec.json            (optional)

design-system  →  design-systems/{dsId}/
                    styles.css
                    gallery.html
                    DESIGN.md
                    meta.json
                    primitives/          (consumed from upstream)
                    assets/              (consumed from upstream)
                    shells/
                      *.css
                    docs/

agent[<id>]           → <its per-id outputsRoot from the registry>
agent[bs_html_1]      → source/{branch}/_pages/page_1/index.html + assets/
```

Consumers declare `consumeFrom` with pattern routing rules. The `design-system` kind, for example, routes:

```
**/index.html             → extract-variant-spec → meta.json#fromVariant
**/*.css                  → merge-tokens         → primitives/
**/*.js                   → copy                 → primitives/
**/*.{png,jpg,svg,webp}   → copy                 → assets/
**/*.md                   → copy                 → docs/
```

With `unhandled: "reject"`. So if a ds-brainstorm subagent decides to add a `net.js` for a WebGL primitive (which is exactly what super's variant `d` did), the design-system consumer routes it into `primitives/net.js`. **Nothing drops silently.** A detour producing a `motion.json` would fail validation because no rule matches — surfaced as drift with a "extend the contract or route this file" prompt.

## Fan-out, isolation, parallelism

A kind that produces N parallel outputs declares `fanOut`:

```python
"fanOut": {
    "kind":         "task-subagents",   # not "single session writes N files"
    "isolation":    "cold",             # each sibling sees only its diverger
    "parallelism":  "siblings-parallel",# concurrent, never serial
    "count":        "per-instance" | "inputs.n",
    "diverger":     "inputs.spec.genre",# which field differs per sibling
}
```

The orchestrator's [AGENT_HARNESS.md](AGENT_HARNESS.md) translates this into hard rules: synchronous bash for-loops over `/run` are forbidden; siblings must commit from independent Task sessions; the validator detects timing patterns and same-session sibling commits.

## Variants are open-ended

`ds-brainstorm` and `iterator-remix` carry `openEnded: True`. The scaffold creates 3 by default. The user may make 4, 5, 6 — any count — by refining in chat or dragging more nodes. The reconciler walks the producer's parent folder (`_ds_brainstorm/`) and **auto-promotes** any folder with no matching node to a card on the canvas — silently, no Heal click.

This is the structural fix for super's variant `d`: it existed on disk, was picked in `DECISION_cp_ds_pick.json`, but had no card. Under the new system it gets a card automatically.

## Asset versioning (v3.0)

The `asset` kind carries two extra contract blocks — `versioning` and `adaptiveSize` — that no other kind has. See [`../../docs/features/asset-versioning.md`](../../docs/features/asset-versioning.md) for the full design.

```python
"versioning": {
    "enabled":                  True,
    "maxUnpinnedVersions":      20,
    "maxUnpinnedCompositions":  50,
    "snapshotRoot":             "workflow/runs/{nodeId}/{versionId}/",
    "viewRoot":                 "workflow/views/{nodeId}/{versionId}/{compositionId}/",
    "thumbStrategy":            "canvas-html2canvas",
},
"adaptiveSize": {
    "enabled": True, "scaleDefault": "fit-canvas",
    "minW": 280, "maxW": 720,
    "aspectFrom": "viewport|image|markdown",
}
```

Each asset node carries:

- `versions[]` — chronologically appended snapshots of the asset's canonical files. Capped at 20 unpinned per node; active version is always protected from eviction.
- `compositions[]` per version — tuples of `(sub-asset → sub-versionId)` describing which upstream sub-asset versions this view is pinned against. Free-cost JSON entries + view-dir hardlinks. Capped at 50 unpinned per parent version.
- `activeVersionId` + `activeCompositionId` — current head of each axis.
- `consumedVersions` (version-level) — non-asset upstream lineage as `{nodeId: {outputHash}}`.
- `consumedSubVersions` (composition-level) — asset upstream lineage as `{nodeId: versionId}`.

The daemon snapshots an asset's files into `workflow/runs/<nodeId>/<vid>/` after every successful upstream producer run. View dirs are materialised into `workflow/views/<nodeId>/<vid>/<compId>/` via hardlinks (copy fallback) so iframes can load a per-composition tree without rewriting HTML. The live `source/` tree always mirrors the active version + active composition.

Endpoint contract: see `docs/features/asset-versioning.md §7.2` for the complete list. Pattern is `/__workflow/node/<id>/version/<vid>/<action>` and `/__workflow/node/<id>/version/<vid>/composition/<cid>/<action>`.

Adaptive sizing: card layout derives from `node.size.naturalAspect + scale` rather than fixed `w/h`. Drag-resize commits `scale: "custom"` so the user's pick survives re-render; a `↺` button restores adaptive mode.

## When in doubt

If you're writing code that needs to know "what is `kind X`," call `kinds.kind_contract(kind, node_id)` and read what it returns. Do not hardcode. Do not duplicate. If the registry is wrong, fix the registry — not the call site.

If you're an agent reading this: also read [AGENT_HARNESS.md](AGENT_HARNESS.md) — that's the rulebook for how you produce work compatible with these contracts.
