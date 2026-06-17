# NODE_IO_FRAMEWORK.md — the edge I/O contract & how the Agent node adapts

This is the rulebook for how data flows across a **workflow edge**, and how the
**Agent node adapts** to whatever it is wired to. Read it with
[registry.py](registry.py) (the contract) and [README.md](README.md) (the kinds).

## The problem this solves

Edge behaviour used to be hardcoded in three separate, out-of-sync places:

1. the frontend connect-menu typing (`WORKFLOW_CONNECT_DEFS` + a second,
   divergent `workflowPortFlavor` scheme in `app.js`),
2. a UI-only "typed inputs" resolver in `app.js`, and
3. the **real** agent dispatch in `serve.py` — which didn't even handle a
   composer/vector wired straight into an agent.

So an agent couldn't reliably adapt: wiring a Composer into it gave the running
agent *nothing*, and its output was a dumb "write to path X" hint with no sense
of what the consumer actually wanted.

## The fix: one declarative `io` contract

Every kind declares an `io` block. It is the single source of truth all three
sites read. It lives in **`KIND_IO`** in [registry.py](registry.py) and is
merged onto each kind (so `kind_contract()`, `to_jsonable()`, and the
`/__kinds/registry` endpoint the frontend reads all carry it).

```python
"io": {
  "provides": [   # downstream-facing output ports
    {"port": "out", "label": "...", "tags": [...],
     "resolve": "<strategy>", "resolveArgs": {...}},
  ],
  "accepts": [    # upstream / agent-edit input ports
    {"port": "in", "label": "...", "tags": [...],
     "ingest": "<strategy>", "canonical": "<path template, editTarget only>"},
  ],
}
```

`tags` is the **single merged vocabulary** (`text`, `text-gen`, `asset`,
`asset-gen`, `palette`, `typography`, `folder`, `folder-write`, `section`,
`3d`, `runnable`, `remixable`, `blendable`, …). Two ports are compatible when
their tag sets intersect (or either side is empty = wildcard).

### `resolve` strategies — provider node → upstream `<context>` chunk

| strategy | what it contributes | used by |
|---|---|---|
| `text` | a field's text (`resolveArgs.fields` in order; `headerKind` adds `(kind)`) | prompt, skill, agent, ds-brainstorm, iterator-remix |
| `folder` | the wired file's contents (read-only, `_safe_join` guarded) | folder |
| `webfetch` | the page's readable text (`resolveArgs.cap`; degrades to a note) | browser |
| `bakedFile` | the node's baked artifact, read from `node.bakedPath` | composer, vector-editor, formatted-text, spline-3d |
| `assetFile` | a path descriptor for the wired asset | asset |
| `typed` | flattened palette swatches / type scale (`resolveArgs.flavor`) | color-palette, typography |
| `dsRef` | design-system id + local fonts | design-system |
| `sectionBundle` | the combined contents of every node whose centre is inside the frame | section |

Omit `resolve` → the port is **frontend-only** (typing/menu) and contributes no
upstream context.

### `ingest` strategies — consumer node → agent `<output-destinations>` instruction

| strategy | what the agent is told | used by |
|---|---|---|
| `context` | (nothing — read-only upstream context; the default) | most accept ports |
| `assetWrite` | "Write your `<assetKind>` output to `<path>`" — format-aware | asset |
| `folderWrite` | "Write outputs into `<path>`" | folder, prototype |
| `editTarget` | "EDIT this node: rewrite its canonical file `<canonical>` (JSON); the editor re-imports it live" | composer, vector-editor, spline-3d |
| `sectionWrite` | the addNodes-grid layout contract (generate INTO the frame) | section |

A downstream kind with a registry `outputsRoot` but no matching accept ingest
falls back to "it expects its inputs under `<outputsRoot>`".

The whole walk is implemented once in [io_resolve.py](io_resolve.py)
(`resolve_upstream` / `resolve_downstream`) and called from `serve.py`'s `/run`.

## The dual-artifact rule (editTarget kinds)

An agent wired into a complex node (composer / vector-editor / spline-3d) **edits
it**. But the baked *presentation* artifact can't round-trip:

- composer bakes to absolute-positioned **HTML**, vector to flattened **SVG** —
  neither parses cleanly back into the editor's `layers[]` / `shapes[]`.

So each editTarget kind keeps **two** artifacts:

- a **presentation file** (`composer-<id>.html`, `vector-<id>.svg`) — what
  downstream `bakedFile` / `assetFile` consumers read; and
- a **JSON sidecar** (`composer-<id>.json`, `vector-<id>.json`,
  `spline-<id>.scene.json`) — the **canonical**, lossless, agent-editable
  representation and the **re-import source**.

`io.accepts[].canonical` points at the **JSON**, never the presentation file.
Bake writes both. When an agent rewrites the JSON, the daemon's SSE
`asset-changed` → `th:asset-refresh` bus tells the editor node to re-import it
live (composer/vector patch their inline state; spline reloads its iframe with
`forceSidecar=1` so the on-disk scene wins over local autosave). A
`selfWriteRef` / timestamp guard stops the node's own write from echoing into a
re-import loop.

## How to add a new node kind (the framework property)

Adding a kind needs a `KIND_IO` entry **and nothing else** for the agent to
adapt to it — the dispatch, edge typing, and section bundling are all
contract-driven:

1. Add `KINDS["<kind>"]` (inputs/outputs/dispatch/…) in `registry.py`.
2. Add `KIND_IO["<kind>"]`:
   - `provides[]` — one per output port, with `tags` and (if it should feed an
     agent as context) a `resolve` strategy.
   - `accepts[]` — one per input port, with `tags` and an `ingest` strategy.
3. If it's **file-backed**, pick `resolve: "bakedFile"` (reads `node.bakedPath`)
   or `"assetFile"` (reads `node.path`).
4. If it's **agent-editable**, add an `edit` accept with `ingest: "editTarget"`
   and a `canonical` JSON sidecar template; in its editor component, bake the
   JSON sidecar AND add a `th:asset-refresh` listener that re-imports it.
5. Frontend: add the `WORKFLOW_NODE_FACTORY` defaults + a render block +
   (optionally) a `WORKFLOW_CONNECT_DEFS` entry mirroring the `io` tags so the
   connect menu offers it. (Edge-drag already allows it via wildcard flavor.)

The section `sectionBundle` resolver and the agent's upstream/downstream walks
pick the new kind up automatically — no `serve.py` change.

## Worked example — spline-3d

`spline-3d` is a container kind (`dispatch:"none"`) rendered directly on the
canvas like composer, replacing the old "run a skill to spawn an asset" Tool
pathway. Its `io`:

- `provides out` → `bakedFile` (`scene.json`, tags `[asset, 3d]`) — downstream
  consumers read the scene.
- `accepts in` → `context` (tags `[asset, 3d]`) — wire a `.glb`/`.gltf` in to
  import it.
- `accepts edit` → `editTarget`, canonical `source/{branch}/spline-{id}.scene.json`
  — an agent edits the scene JSON; the node reloads the iframe to show it.

The embedded editor autosaves the scene to the sidecar, so the node is "always
baked" — a downstream agent receives the scene without a manual Bake.
