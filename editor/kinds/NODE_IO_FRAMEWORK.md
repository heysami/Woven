# NODE_IO_FRAMEWORK.md - the edge I/O contract & how the Agent node adapts

This is the rulebook for how data flows across a **workflow edge**, and how the
**Agent node adapts** to whatever it is wired to. Read it with
[registry.py](registry.py) (the contract) and [README.md](README.md) (the kinds).

## The problem this solves

Edge behaviour used to be hardcoded in three separate, out-of-sync places:

1. the frontend connect-menu typing (`WORKFLOW_CONNECT_DEFS` + a second,
   divergent `workflowPortFlavor` scheme in `app.js`),
2. a UI-only "typed inputs" resolver in `app.js`, and
3. the **real** agent dispatch in `serve.py` - which didn't even handle a
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

### `resolve` strategies - provider node → upstream `<context>` chunk

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

### `ingest` strategies - consumer node → agent `<output-destinations>` instruction

| strategy | what the agent is told | used by |
|---|---|---|
| `context` | (nothing - read-only upstream context; the default) | most accept ports |
| `assetWrite` | "Write your `<assetKind>` output to `<path>`" - format-aware | asset |
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

- composer bakes to absolute-positioned **HTML**, vector to flattened **SVG** -
  neither parses cleanly back into the editor's `layers[]` / `shapes[]`.

So each editTarget kind keeps **two** artifacts:

- a **presentation file** (`composer-<id>.html`, `vector-<id>.svg`) - what
  downstream `bakedFile` / `assetFile` consumers read; and
- a **JSON sidecar** (`composer-<id>.json`, `vector-<id>.json`,
  `spline-<id>.scene.json`) - the **canonical**, lossless, agent-editable
  representation and the **re-import source**.

`io.accepts[].canonical` points at the **JSON**, never the presentation file.
When an agent rewrites the JSON, the daemon's SSE `asset-changed` →
`th:asset-refresh` bus tells the editor node to re-import it live: composer/vector
patch their inline state; spline-3d pushes `spline:set-scene` to its iframe (the
driven-view protocol below). A content-compare against the bytes the node last
wrote stops the node's own write from echoing into a re-import loop.

## Frontend resolution & iframe tools (v4.0)

The backend (`io_resolve.py`) was contract-driven from the start; the **frontend
now matches it**. `app.js` exposes a single resolver that reads the same `io`
contract (served via `/__kinds/registry` → `window.__thKindRegistry`):

```
resolveUpstreamInputs(node, allNodes, allEdges, opts) → ResolvedInput[]
useUpstreamInputs(node, allNodes, allEdges, opts)      // reactive useMemo wrapper
```

It picks each upstream node's `io.provides` entry by the edge's from-port and
normalises by `resolve` + `tags` into typed inputs:
`text | asset | glb-import | palette | typography | design-system | web |
section{children} | unbaked`. Each input also carries `node` (the source node)
so a consumer can reach fields the normalized shape doesn't surface (e.g.
formatted-text reads `typo.node.fontCdn`). `opts`: `{toPort, accept:tagSet}`.

**Every container node uses this - no node hand-rolls an `allEdges` walk:**
composer layer sources, formatted-text typo/text, and the spline-3d import list
all derive from `useUpstreamInputs`. Adding a container kind that consumes inputs
needs **zero** new resolution code - it inherits hydration, reactively.
(The agent node's on-canvas input *summary* is display-only; the agent's real
`/run` input resolution is the backend `io_resolve.py`, already contract-driven.)

**Iframe-embedded tools are DRIVEN VIEWS, never owners of state.** The spline-3d
3D editor is an `<iframe>`; the structural rule that keeps it (and any future
iframe tool) bug-free: the **host node is the single source of truth**, the
iframe holds **no independent persistence** (no localStorage in embedded mode),
and inputs are **pushed reactively** over a postMessage protocol - never baked
one-shot into the iframe URL. Protocol: iframe→node `spline:ready` / `spline:scene`;
node→iframe `spline:init {scene, imports}` / `spline:imports {urls}` /
`spline:set-scene {scene}` (agent editTarget re-import). The node writes the
sidecar (single writer) and stamps `bakedPath`. The earlier "imports passed in
the URL + the tool's own localStorage boot" was the bug class this removes.

## How to add a new node kind (the framework property)

Adding a kind needs a `KIND_IO` entry **and nothing else** for the agent to
adapt to it - the dispatch, edge typing, and section bundling are all
contract-driven:

1. Add `KINDS["<kind>"]` (inputs/outputs/dispatch/…) in `registry.py`.
2. Add `KIND_IO["<kind>"]`:
   - `provides[]` - one per output port, with `tags` and (if it should feed an
     agent as context) a `resolve` strategy.
   - `accepts[]` - one per input port, with `tags` and an `ingest` strategy.
3. If it's **file-backed**, pick `resolve: "bakedFile"` (reads `node.bakedPath`)
   or `"assetFile"` (reads `node.path`).
4. If it's **agent-editable**, add an `edit` accept with `ingest: "editTarget"`
   and a `canonical` JSON sidecar template; in its editor component, bake the
   JSON sidecar AND add a `th:asset-refresh` listener that re-imports it.
   **REQUIRED - every `editTarget` accept MUST also carry an `authoring`
   string** that spells out the canonical file's schema *and* production rules
   (the medium it is, what it can/can't express, any "wire X first" precondition,
   the exact JSON keys + per-entry shape). `editTarget` without `authoring` only
   hands the agent a path with no schema, so it GUESSES and ships something the
   node can't render - the composer "blank hero" / spline "2D-instead-of-3D"
   failure class. Use `{branch}`/`{id}` placeholders (resolved per-target by
   `io_resolve`); follow `_SPLINE_AUTHORING` / `_COMPOSER_AUTHORING` /
   `_VECTOR_AUTHORING` in `registry.py`. This rule is enforced: `registry.py`
   calls `io_contract_violations()` at import and **raises** if any `editTarget`
   lacks a non-empty `authoring`, so `check-compat.sh` (which imports `serve`)
   fails before the contract can be synced. `kinds/test_io_contract.py` is the
   runnable form of the same check.
   - The SAME rule applies to **asset media**: an `asset` node's `assetKind`
     (`shader`/`3d`/`svg`/`image`/`video`/…) is the medium an agent is told to
     produce, and "Write your `<assetKind>` output to `<path>`" alone leaks no
     schema - so a shader node gets the same generic instruction as an image
     and the agent defaults to HTML/CSS (the "glassmorphic button became
     `backdrop-filter`, not GLSL" failure). **Every `assetKind` enum value MUST
     have an `ASSET_KIND_AUTHORING[<kind>]` entry** in `registry.py` stating what
     the medium is + how to produce it + the do-not-substitute guard. It feeds
     both dispatch paths (`io_resolve` assetWrite + the frontend typed-output
     builder via the `/__kinds/registry` payload) and is enforced by the same
     import-time `io_contract_violations()` check.
   - **Medium ≠ storage.** `assetKind` is the STORAGE/embed type; an asset node
     also carries `mediaModel` (the generating media-model id). Many Pathway-B
     models all store `.html` (assetKind `html`) but expect a SPECIFIC result -
     shader (WebGL), viz (chart), threejs (3D scene), motion-gen (GSAP timeline),
     canvas-gen (particle loop), html-page (UI mockup), plus svg-gen / lottie-gen.
     `MEDIA_MODEL_AUTHORING` (keyed by media-model id) carries each contract;
     dispatch prefers it over `ASSET_KIND_AUTHORING` when the node has a matching
     `mediaModel`. The catalog lives in `prompts/media-models.js` (frontend-only),
     so `MEDIA_MODEL_AUTHORING` is the daemon-side mirror; `test_io_contract.py`
     asserts the known specific models stay covered.
   - And to **`sectionWrite`**: a `section` is a FRAME, not a medium, so its
     `authoring` (`_SECTION_AUTHORING`) is a placement+registration PROTOCOL -
     register children into the frame's grid - and is medium-agnostic: each
     child is an `asset` node that delegates to its OWN `assetKind` authoring.
     `io_resolve._section_grid_instr` injects the live canvas rect into that
     contract. It is under the same import-time check (`editTarget` and
     `sectionWrite` both require `authoring`; `folderWrite` is exempt by design
     - `folder` = arbitrary files, `prototype` carries its own delegation block).
5. Frontend: add the `WORKFLOW_NODE_FACTORY` defaults + a render block +
   (optionally) a `WORKFLOW_CONNECT_DEFS` entry mirroring the `io` tags so the
   connect menu offers it. (Edge-drag already allows it via wildcard flavor.)
6. If the node CONSUMES wired inputs, read them with **`useUpstreamInputs(node,
   allNodes, allEdges, opts)`** - never hand-roll an `allEdges` walk. It's
   reactive and contract-driven, so the node hydrates new edges by construction.
7. If the node embeds an **iframe tool**, make it a DRIVEN VIEW: the node owns
   state, the iframe keeps NO independent persistence, inputs are pushed over
   postMessage (not the URL). Follow the spline-3d protocol. This is the rule
   that prevents the iframe + competing-persistence bug class.

The section `sectionBundle` resolver, the frontend `useUpstreamInputs`, and the
agent's backend upstream/downstream walks all pick the new kind up automatically
- no `serve.py` and no per-node edge-walk change.

## Worked example - spline-3d

`spline-3d` is a container kind (`dispatch:"none"`) rendered directly on the
canvas like composer, replacing the old "run a skill to spawn an asset" Tool
pathway. Its `io`:

- `provides out` → `bakedFile` (`scene.json`, tags `[asset, 3d]`) - downstream
  consumers read the scene.
- `accepts in` → `context` (tags `[asset, 3d]`) - wire a `.glb`/`.gltf` in to
  import it.
- `accepts edit` → `editTarget`, canonical `source/{branch}/spline-{id}.scene.json`
  - an agent edits the scene JSON; the node reloads the iframe to show it.

The embedded editor autosaves the scene to the sidecar, so the node is "always
baked" - a downstream agent receives the scene without a manual Bake.
