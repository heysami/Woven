# Agent instructions

This repo is a **prototype workspace**: one project = one source tree. The editor (under `editor/`) renders it as a Figma-style canvas.

The **design system is a separate library asset** that lives at project root under `design-systems/<id>/`. Each project references it via `meta.dsRef`. Prototype regeneration is **gated on a DS existing first** — Workflow 1 will not run against a project whose `meta.dsRef` is unset. Build the DS via Workflow 0 first.

Your job: keep the project's artifacts consistent — `source/` (feature pages, constrained by DS) ↔ `editor/data.js` (with `meta.dsRef`) ↔ the DS library node it references. Drift between feature pages and DS is reconciled through the proposal flow (Workflows 6 / 6b).

> **v3.1 / v3.7 — project-level branches removed; multi-prototype-per-project replaces them.** The old multi-branch model (fork/merge across `source/<slug>/`) has been replaced by **per-asset sibling-node branching** on the workflow canvas. A project may still host multiple PROTOTYPES under `source/<slug>/` (each surfaced as a starred prototype), but they are siblings, not branches — there is no fork/merge between them. Each prototype owns its own `editor/<slug>.data.js`. See [`docs/features/deprecate-project-branches.md`](docs/features/deprecate-project-branches.md).

## Workspace mode (Phase 6 — multi-project)

When the editor's daemon is launched with `TH_WORKSPACE_DIR=<path>`, the install is **multi-project**: one editor binary serves N independent projects under the workspace dir, each with its own `source/`, `editor/data.js`, and per-project docs. In that mode:

- **Your cwd is the active project's root**, not the install root. Read/write project-scoped files (`source/`, `design-systems/<id>/`, `editor/data.js`, `editor/design-systems/<id>.js`, `NOTES.md`, `prototype.json`, `edits.json`, `DS_PROPOSAL.md`, `DS_ACCEPTED.json`, `DS_DEFERRED.md`) via relative paths — they live in cwd. **`DESIGN.md` lives inside each DS folder at `design-systems/<id>/DESIGN.md`, not at project root.**
- **The agent protocol lives at a separate read-only mount**, exposed via `--add-dir $TH_PROTOCOL_ROOT`: this `AGENTS.md`, `PROTOTYPE.md`, and every workflow/subagent under `docs/agents/**`. Read them from that mount; **never copy them into a project**.
- **Useful env vars** set on every spawn: `TH_PROJECT_ROOT` (absolute path to cwd), `TH_PROTOCOL_ROOT` (the shared protocol mount), `TH_PROJECT_ID` (workspace id), `TH_DAEMON_URL` (http://127.0.0.1:PORT), `TH_RUN_ID`.
- **Every daemon POST that writes into `source/` MUST include `?project=$TH_PROJECT_ID`** in the URL. `/__asset_generate`, `/__llm_run`, `/__write_text`, `/__copy_file`, `/__replace_exposed_svg`, `/__mkdir`, `/__rmdir`, `/__rename_dir` now 400 without it when more than one project exists. There used to be a silent fallback to the alphabetically-first project — that's gone because it caused subagent-generated assets to land in the wrong project's tree.
- **Cross-project work is forbidden.** Stay within cwd. Don't read or write under sibling project dirs even if the workspace path is visible.

In single-project mode (no `TH_WORKSPACE_DIR`) the install root and the project root coincide and these distinctions collapse to today's behavior — every path is repo-relative as before.

## 🚫 Editor source is OFF LIMITS — never write under `$TH_PROTOCOL_ROOT`

**Hard rule. Zero exceptions. This is the single most important constraint in this file.**

The shared protocol mount (the path `$TH_PROTOCOL_ROOT` points at — typically `/Users/sami/Documents/Woven` or wherever the editor binary is installed) is the **editor itself**, not a project. You are spawned to work on a **project** under `$TH_PROJECT_ROOT`. The two are different trees with different lifecycles. The protocol mount is added to your context via `--add-dir` so you can READ documentation (`AGENTS.md`, `PROTOTYPE.md`, `docs/agents/**`, `.claude/agents/**`). It is **read-only by policy** — the filesystem may allow writes, but the policy does not.

**You MUST NOT write, edit, or create any file under `$TH_PROTOCOL_ROOT`.** This includes (non-exhaustive):

- `$TH_PROTOCOL_ROOT/editor/**` — the React app, daemon, styles, assets, prompts, registry.
- `$TH_PROTOCOL_ROOT/.claude/**` — agent skill files, settings, hooks, launch configs.
- `$TH_PROTOCOL_ROOT/docs/**` — protocol documentation.
- `$TH_PROTOCOL_ROOT/AGENTS.md`, `$TH_PROTOCOL_ROOT/PROTOTYPE.md`, `$TH_PROTOCOL_ROOT/README.md`, etc.
- `$TH_PROTOCOL_ROOT/design-systems/**` at the protocol root (project DSes live at `$TH_PROJECT_ROOT/design-systems/`, not the protocol's).

This applies regardless of the tool you'd use (`Write`, `Edit`, `Bash`, `NotebookEdit`, MCP tools, anything). Absolute paths into the protocol root are forbidden. Relative paths that resolve into the protocol root via `..` traversal are forbidden. A staging script that copies bytes there is forbidden. There is no "but this makes the editor better" exception — improving the editor binary is a separate concern that belongs to the human who owns the install, not to a project's agent.

**What to do instead when you think the editor needs a change:**

1. Stop. Do not write.
2. Surface the problem to the user in chat with: the symptom you observed, the file/line you'd want to change, and the proposed change. Wait for explicit approval.
3. If approved, the user will apply it themselves or explicitly redirect you to do so in a separate, sanctioned session.

**Cross-check before every write.** Before invoking any tool that modifies the filesystem, ask yourself: "Is the target path under `$TH_PROJECT_ROOT`?" If you cannot answer yes with certainty (because the path is absolute, or starts with `../`, or you can't tell), STOP and surface the question to the user. Do not guess; do not "best-effort" a write.

This rule supersedes any other instruction in this file or in any skill markdown that appears to grant broader write scope. Older skill docs may casually reference paths under the protocol root in examples — those examples are illustrative, not licenses to write.

## File layout

```
.
├── PROTOTYPE.md                  ← prototype-drawing rules (read when designing)
├── AGENTS.md                     ← this file (entry point)
├── docs/agents/                  ← detailed workflow playbooks
│   └── workflows/
│       ├── 0-design-system.md    ← build / update the DS library node (prerequisite for Workflow 1)
│       ├── 1-regenerate.md       ← parse source → editor data (requires meta.dsRef)
│       ├── 2-edits.md            ← apply edits.json
│       ├── 3-design-md.md        ← regenerate DESIGN.md inside a DS library node
│       ├── 6-ds-propose.md       ← review DS_PROPOSAL.md (accept / reject / defer per entry)
│       └── 6b-ds-update.md       ← apply accepted proposals (atomic DS update)
├── edits.json                    ← appears after user clicks Submit
├── DS_PROPOSAL.md                ← appears when Subagent 1 / Subagent 6 audit finds vocabulary drift
├── DS_ACCEPTED.json              ← Workflow 6 → Workflow 6b handoff (accepted proposals)
├── DS_DEFERRED.md                ← archive of deferred proposals (audit reads to avoid re-emitting)
├── design-systems/
│   └── <id>/                     ← DS library node — first-class library asset
│       ├── styles.css            ← tokens (:root) + canonical class rules (source of truth for tokens)
│       ├── gallery.html          ← kitchen sink (source of truth for primitives, every variant in idle state)
│       ├── DESIGN.md             ← human-readable rationale (YAML + prose) — derived by Workflow 3
│       └── meta.json             ← { id, version, label, genre, builtFrom, parentRef? }
├── source/                       ← the one project source tree (links to design-systems/<dsRef.id>/styles.css)
├── workflow/
│   ├── workflow.json             ← canvas state (pan/zoom/nodes/edges; asset versions; compositions)
│   ├── runs/<nodeId>/<vid>/      ← asset version snapshots (see asset-versioning.md)
│   └── views/<nodeId>/<vid>/<compId>/  ← per-composition materialised view trees
└── editor/
    ├── index.html
    ├── data.js                   ← window.EDITOR_DATA (project data — frames, primitives, entities, meta.dsRef)
    ├── design-systems/<id>.js    ← window.EDITOR_DS_<id> runtime mirror per DS
    ├── styles.css
    ├── app.js
    └── serve.py                  ← dev server (/__save /__layout /__workflow + asset-versioning endpoints)
```

Every source folder follows `PROTOTYPE.md`: htm + React UMD, **no build, no Babel**, single page (or multi-HTML with a storyboard `index.html` — see Workflow 1). Feature pages **link** their DS's stylesheet rather than redeclaring tokens or primitives.

## Visualization in chat

When the user asks for a quick visualization, demo, chart, mockup, illustration, color/font sample, shader effect, 3D scene, or animated sketch — render it **inline in the chat drawer**, not by editing `source/`. The chat surface understands the following fenced code blocks and inline patterns, all rendered live as you stream them.

| Renderer | Trigger | Use for |
|---|---|---|
| Markdown table | `\| col \| col \|` + `\|---\|---\|` line | Tabular data, comparisons, token maps |
| HTML | <code>\`\`\`html</code> fenced block | Styled cards, layout sketches, CSS animations (`@keyframes`), any DOM with event handlers (`onclick`, `onmousemove`, `onscroll`, `:hover`) |
| SVG | <code>\`\`\`svg</code> fenced block, or bare `<svg>…</svg>` in prose | Icons, vector charts, illustrations |
| Mermaid | <code>\`\`\`mermaid</code> fenced block | `graph LR`, `sequenceDiagram`, `flowchart`, `erDiagram`, `stateDiagram` |
| GLSL shader | <code>\`\`\`glsl</code> or <code>\`\`\`shader</code> fenced block | Fragment-shader playground in shadertoy style. Write `void mainImage(out vec4 fragColor, in vec2 fragCoord)`. Uniforms available: `iResolution` (vec3, px), `iTime` (float, sec), `iMouse` (vec4, xy=pos, zw=last click). The host wires WebGL + animation loop + mouse tracking. |
| three.js | <code>\`\`\`three</code> or <code>\`\`\`webgl</code> fenced block | 3D scenes. Globals: `THREE`, `scene`, `camera`, `renderer`. Register a per-frame callback with `__animate(t => …)`. Click/hover/raycast/scroll-zoom all work via the standard three.js patterns. |
| p5.js | <code>\`\`\`p5</code> fenced block | Creative-coding sketches. Define `setup()` + `draw()` top-level (global mode) or `function sketch(p) { … }` (instance mode). `mousePressed`, `mouseMoved`, `mouseWheel`, `keyPressed` etc. all work. |
| Color swatch | Inline `#hex`, `rgb()`, `rgba()`, `hsl()`, `oklch()`, `oklab()`, `linear-gradient(…)`, `radial-gradient(…)` | Auto-decorated with a colour swatch — no fencing needed. |
| Image thumb | Inline `https://…/foo.png\|jpg\|webp\|gif\|svg\|avif` | Auto-renders as a 32×32 thumbnail next to the URL. |
| Font preview | Inline `https://…/foo.woff\|woff2\|ttf\|otf` | Auto-renders "Aa Bb 123" in that font via injected `@font-face`. |

All sandboxed previews (`html`/`svg`/`shader`/`three`/`p5`) run inside `<iframe sandbox="allow-scripts">` — null-origin isolation, full interactivity (click, mouse, scroll, hover, keyboard), zero access to the host page.

**Rule of thumb:** render in chat unless the user explicitly says "prototype", "branch", "scaffold", or asks for something multi-page navigable. Reserve `source/` writes for actual prototype work that lives in the canvas.

**Pick the lightest renderer that does the job.** A 3-row Markdown table beats a fenced HTML block. A `#hex` chip beats a `<div style="background:#hex">`. A simple SVG icon beats a three.js scene. Use the heavy hitters (shader / three / p5) when you genuinely need WebGL or canvas-based animation.

## Workflow index

Match the trigger; read only the matching playbook.

| Trigger | Playbook |
|---|---|
| "build design system" / "update DS" / DS spec nodes change / no DS exists | [`docs/agents/workflows/0-design-system.md`](docs/agents/workflows/0-design-system.md) → [`docs/agents/subagents/0-ds-builder.md`](docs/agents/subagents/0-ds-builder.md) |
| "process the prototype" / "regenerate frames" / new source dropped in | [`docs/agents/workflows/1-regenerate.md`](docs/agents/workflows/1-regenerate.md) → [`docs/agents/planner.md`](docs/agents/planner.md) — **requires `meta.dsRef`; runs Workflow 0 first if absent** |
| `edits.json` at repo root | [`docs/agents/workflows/2-edits.md`](docs/agents/workflows/2-edits.md) |
| DS trio changed; "Export DESIGN.md" against a DS library node | [`docs/agents/workflows/3-design-md.md`](docs/agents/workflows/3-design-md.md) |
| `DS_PROPOSAL.md` at repo root | [`docs/agents/workflows/6-ds-propose.md`](docs/agents/workflows/6-ds-propose.md) — partitions by verdict; dispatches to 6b on accept |
| `DS_ACCEPTED.json` at repo root | [`docs/agents/workflows/6b-ds-update.md`](docs/agents/workflows/6b-ds-update.md) — atomic DS trio update + version bump |
| `STATEMACHINE_REQUEST.md` / `TIMELINE_REQUEST.md` / `GRID_REQUEST.md` | [`docs/agents/planner.md`](docs/agents/planner.md) → spawn subagent 8 / 9 / 10 (gate override) |

### Workflow 1 is a planner + subagents

Regeneration is split into 10 isolated subagent jobs to keep each one's context focused. The planner (top-level Claude) coordinates; each subagent owns a strict slice of the data file. See [`docs/agents/workflows/1-regenerate.md`](docs/agents/workflows/1-regenerate.md) for the dispatch table and [`docs/agents/planner.md`](docs/agents/planner.md) for the orchestration recipe.

Subagent playbooks live under [`docs/agents/subagents/`](docs/agents/subagents/). The planner reads only the playbook of the subagent it's spawning, and feeds that playbook into the `Agent` tool's prompt so the subagent has it as context. **No subagent reads any other subagent's playbook** — context isolation is the whole point.

#### Subagent 1 has its own nested pipeline (visual generation)

Subagent 1 (source build) doesn't decide visual *medium* itself — it writes annotated slots (`img-placeholder` / `motion-placeholder` per [`PROTOTYPE.md`](PROTOTYPE.md) §9) and then spawns [`Subagent 1.V`](docs/agents/subagents/1V-visual-planner.md) after render-verify. 1.V enumerates every slot, classifies the medium against a genre filter (raster-photo, raster-foreground, vector-mark, vector-icon, shader, 3d, particle-2d, particle-gl, lottie, video), scaffolds the matching node graph into `workflow/workflow.json` (uses the Open Design canvas surface — prompt + skill + asset nodes connected by edges), then dispatches one **per-asset drawer** (`1V-<medium>.md`) per slot in parallel. Each drawer owns one asset, writes either a prompt (Pathway A — vendor API) or code (Pathway B — LLM-writes-SVG/GLSL/three/canvas/Lottie). Generation itself fires when the user clicks Run on the canvas; this layer is **scaffolding + briefing**, not execution.

The same context-isolation rule applies one level deeper: 1.V reads its own playbook + the classifier table; each 1.V.* drawer reads only its own `1V-<medium>.md`. **No drawer reads another drawer's playbook.**

> The full design skill is [`PROTOTYPE.md`](PROTOTYPE.md). Read it first when the user says "update the design", "rebuild the prototype", "regenerate components", "add a page or overlay".

## Design system

The design system is **a first-class library asset**. It lives at `design-systems/<id>/` and is owned by Workflows 0 (build) and 6b (proposal-driven update). The project references it via `meta.dsRef = { id, version }`.

- The DS is **canonical**. It has one mode: source of truth. There's no "draft" or "revising" state. Either a DS exists for the project (its `meta.dsRef` resolves) or it doesn't.
- The DS is **bootstrapped from workflow-mode spec nodes** (genre / reference / token-preference / persona-mode / primitive-preset), not from a prototype. Workflow 0 reads the spec and produces the trio (`styles.css` + `gallery.html` + `DESIGN.md`) before any feature page exists.
- **Workflow 1 is gated on `meta.dsRef`.** If the project has no DS reference, Workflow 1 refuses to run and surfaces "Run Workflow 0 first."
- **Feature pages consume the DS as a vocabulary.** Subagent 1 reads `design-systems/<dsRef.id>/styles.css` + `gallery.html` and references their classes. It never declares new tokens or primitive-shaped classes inside `source/styles.css`.
- **Drift goes through the proposal flow.** When a feature page needs something the DS doesn't cover, Subagent 1 (or the post-build Subagent 6 audit) emits a proposal entry to `DS_PROPOSAL.md` AND proceeds with closest-fit substitution. The user reviews via Workflow 6 (accept / reject / defer per entry); Workflow 6b applies accepted entries atomically.
- **Versioning.** `meta.json.version` is the content hash of `styles.css + gallery.html`. Workflow 6b bumps it when accepted proposals land.

## Source manifests

The project's `source/` folder MAY include declarative sidecars that Workflow 1 reads directly instead of inferring from JSX. Authors keep them in sync; the editor consumes them via Workflow 1.

**`source/prototype.json`** — single source of truth for frames, arrows, lanes, entity-to-frame assignments, entity↔entity links, and the three optional views (state machines / timelines / grids). Optional but recommended — anything stateful or graph-shaped is fragile to infer.

```jsonc
{
  "project": "Margin",
  "description": "Personal knowledge tool for researchers",
  "genre": "Linear-style observability with editorial annotations",
  "viewport": { "w": 1440, "h": 900 },

  "lanes": [
    { "id": "user",   "label": "User",       "kind": "user"    },
    { "id": "margin", "label": "Margin app", "kind": "system"  }
  ],

  "frames": [
    { "id": "library", "label": "Library",
      "kind": "page",              // page | state | overlay | form | substep | start | decision | input | trigger | notification | external
      "lane": "user",
      "hash": "",                  // optional — hash routing
      "entry": null,               // optional — per-frame .html override (multi-HTML sources)
      "setupScript": null,         // optional — JS eval'd inside the iframe (use window.__pokeBy)
      "parent": null,              // required for state/overlay/substep, optional for drill-down page
      "entities": ["Reference"],   // IA assignments
      "x": 120, "y": 120, "w": 1440, "h": 900    // optional — auto-laid-out if missing
    }
  ],

  "arrows": [
    { "id": "a1", "from": "library", "to": "cmdk", "action": "Press ⌘K" },
    // Cross-lane handoff — see "Arrows and kinds" below.
    { "id": "a2", "from": "tc-submit", "to": "pxp-review-queue",
      "action": "TC submits → lands in PXP review queue (Workflow 1.2)" }
  ],

  "links": [
    { "id": "l1", "from": "Collection", "to": "Reference",
      "cardinality": "1:N", "strength": "strong", "label": "contains" }
  ],

  // Optional — gated. See Workflow 1 Step 5d for when to populate.
  "stateMachines": [ /* per-entity FSMs */ ],
  "timelines":     [ /* time-driven event sequences */ ],
  "grids":         [ /* 2D variance maps — form-field × use-case, entity-op × use-case, decision matrix. Typically multiple per prototype. */ ]
}
```

Full schemas for `stateMachines` / `timelines` / `grids` live in the editor's empty-state cards (tabs 7 / 8 / 9) and in Workflow 1 Step 5d.

**`source/entities.json`** — declarative entity model when more developed than `window.DEMO`. Same per-entity shape as `editor/data.js → entities[]`:

```jsonc
{ "entities": [ { "id": "Reference", "tag": "base", "fields": [...] }, ... ] }
```

**Not in any manifest** — tokens stay in `styles.css :root` (Workflow 1's token-diff check enforces parity); primitives + `from: { selector, hash?, entry? }` stay in `editor/data.js → primitives[]` (runtime DOM extraction needs them there).

**Round-trip rule.** When you apply *model edits* (Workflow 2, `target ≠ "dom"`), write the change to **both** `editor/data.js` AND `source/prototype.json`. If the manifest doesn't exist yet, create it from the current data file on the first model edit.

## Arrows and kinds

The Flow editor lays each frame at column = longest path from a root; IA tree positions siblings by that same rank. Correct for wizards (`step1 → step2 → step3`); breaks down for hub-and-spoke apps with a persistent nav shell. Distinguish two arrow archetypes:

| | **Sequential** | **Re-entry** |
|---|---|---|
| Meaning | "Next step in the same task" | "Jump back to a destination reachable from main nav" |
| Examples | Step 1 → Step 2; List → Detail | "Done" → home; "View in Inbox" → Inbox tab |
| In `arrows[]`? | **Yes** | **No, or only reversed** |

### Test for re-entry — for any arrow `A → B`

1. Is `B` reachable from the global nav (tab bar, sidebar, app shell)?
2. Would the user naturally arrive at `B` by tapping a nav item rather than by completing `A`?
3. Is the action label a "close / done / view / back to" verb?

Any yes → do **one** of:

- **Reverse the arrow** so the long path terminates at `A`. Best when the inverse is also meaningful.
- **Drop the arrow** and document the affordance in `NOTES.md`. With the arrow gone, `B` falls to in-degree 0 and the rank algorithm's fallback treats it as a forest root automatically — **don't reach for `kind: "start"` here**.
- **Promote `B` to `kind: "start"`** — *only* when there's a back-edge into `B` you genuinely cannot drop (e.g. wizard `step1 ↔ step2 ↔ step3` with Prev). `start` is a **cycle-breaker**, not a layout hint.

### Test for cross-actor handoff — for two frames on different lanes with no `<a href>` between them

1. Does a storyboard workflow tag both lanes' personas?
2. Does the same entity record render on both `A` and `B`?
3. Does the storyboard's `built:` / `pages:` list pair them under one workflow number?

Any yes → **add a forward arrow `A → B`**, action quoting the workflow (`"TC submits → lands in PXP review queue (Workflow 1.2)"`). These edges are invisible to `<a href>` scanning — one actor writes a record, another reads it on their own page.

**Cross-check with Step 5b** — terminal/success branches with cross-lane CTAs (`"View application status →"`) are the handoff origin. Source the cross-lane arrow from the **state frame** (success branch), not the page frame. Quote the literal CTA as the `action`. Cross-lane targets are **not** IA children of their handoff source — they keep their own `parent` within their lane.

### Transactional flows — point of no return

Once a frame represents a committed state (`submitted`, `cancelled`, `voided`, `sent`, `paid`, `approved`), **don't** draw an arrow from it back to the pre-commit form, even if source navigates there (`location.href = "...apply.html"`, "Back to dashboard" CTA, "Apply again"). Same URL, different transaction: the user is starting a *new* record, not editing the committed one.

Two acceptable shapes:

- **No arrow.** Document the affordance in `NOTES.md`. Flow graph terminates at the committed state.
- **Arrow to a fresh frame instance** — if the prototype actually ships an edit path with its own page state, the arrow goes there, not back to the form. Label with the literal CTA.

Edit-after-submit is policy, not source. Represent only when the prototype ships it as its own page state. If unsure, ask.

### `kind` vs `parent` — two independent signals

| Signal | Read by | Purpose |
|---|---|---|
| `kind ∈ {page, state, overlay, form, substep, start, decision, input, trigger, notification, external}` | **Flow** | `start` overrides the in-degree-0 fallback (cycle-breaking). Renderable in Canvas / Prototype / IA: `{page, state, overlay, form, substep}` (real screens). Flow-only: `start`, `decision`, `input`, `trigger`, `notification`, `external`. |
| `parent` (frame id) | **IA** | Builds the sitemap drill-down tree. Frames with `parent: "listing"` nest under `listing` regardless of `kind`. |

A `listing → detail` drill-down needs **both**: an arrow `{ from: "listing", to: "detail", action: "Click row" }` *and* `frame: { id: "detail", parent: "listing" }`. Arrow alone = Flow column with no IA nesting. `parent` alone = IA nesting with flat Flow column. Set both.

### Sanity check after editing arrows / kind / parent

Rank algorithm picks roots in this order:

1. Frames with `kind: "start"` (preempts step 2 for **every** frame).
2. Frames with in-degree 0 (the natural forest roots after dropping nav arrows).
3. Highest-reach frame (cycle fallback).

**Foot-gun:** marking *some* landings as `start` (dashboards) while leaving *others* as `page` (listings reached via tab bar). Step 1 fires, listings aren't reached from any dashboard, they stay rank 0 and drag drill-downs along.

Two ways out:

- **Drop `kind: "start"` entirely** if all landings ended up in-degree 0 anyway. Step 2 picks them up as roots automatically and they stay `kind: "page"` so IA still renders them.
- **Mark every landing `kind: "start"`** if you used `start` to break a cycle on some. Consistency over the set.

In one line: **arrows describe how a task advances, not how the app is navigated**. Tab-bar destinations re-enter the graph through their own root.

## Conventions

- **Genre commit:** first comment of `app.js` reads `// GENRE: <one line>`.
- **No Babel, no JSX files.** htm tagged templates only.
- **No router, no state lib, no UI lib.** `useState`, prop-drill, copy-paste until 5+ uses.
- **All UI tokens** in `styles.css :root`. No inline hex/spacing.
- **All mock data** in `window.DEMO` (`data.js`). No `fetch`, no API.
- **Voice set by genre, applied at every leaf** — see `PROTOTYPE.md`.

## Asset versioning (v3.0)

Asset nodes on the workflow canvas (`kind: asset`) carry per-node version history. **This is daemon-managed; you almost never touch it directly.** Quick rules:

- **Every successful upstream producer run snapshots the downstream asset's files** into `workflow/runs/<nodeId>/<versionId>/` and appends a new entry to `node.versions[]`. Capped at 20 unpinned versions per node (pinned versions are exempt).
- **Each version has compositions** — tuples of `(sub-asset → versionId)` recording which upstream sub-asset versions this view is pinned against. Auto-created on every run from the current sub-asset actives. Capped at 50 unpinned per parent version.
- **Reverts and composition switches happen via daemon endpoints**, not by editing `source/` directly. The endpoints refresh `source/` from `workflow/views/<nodeId>/<vid>/<compId>/`. See [`docs/features/asset-versioning.md`](docs/features/asset-versioning.md) §7.2 for the full surface.
- **Branches create new sibling asset nodes** positioned below the source, with a deep copy of the chosen version + composition. The sibling is disconnected; rewire edges as desired.
- **If you produce asset content from a subagent**, optionally emit a `MANIFEST.json` in your write root with `files[]` + `subAssetInputs[]` so the daemon snapshots exactly what you produced and knows where sub-assets mount inside the view tree. Without a manifest the daemon falls back to scanning the asset's declared `path`/`paths`.
- **Lineage chips on asset cards show which upstream versions a snapshot was built against.** Warm-colored chips signal divergence from upstream's current active. The user decides whether to re-run; there's no automatic cascade.

## Don't

- No build step / TypeScript / Vite / Webpack / Babel / Tailwind.
- No aggressive restructuring on a single edit — minimum surface change.
- No auto-applying edits without reading the resulting diff into your reply.
- No stub `DESIGN.md` if a DS's `styles.css` or `gallery.html` is empty — Workflow 3 reads the trio; if the trio is incomplete, surface to user.
- Don't delete `edits.json` until every edit succeeded.
- Don't author the design system from inside Subagent 1 (source build). DS lives at `design-systems/<id>/` and is owned by Workflow 0 / 6b. Feature pages consume; they don't co-author.
- Don't run Workflow 1 against a project with no `meta.dsRef`. Run Workflow 0 first.
- Don't write inline `style="color: #abc"` or raw px / hex literals in feature pages. Every value references a DS token; gaps go through `DS_PROPOSAL.md`.
