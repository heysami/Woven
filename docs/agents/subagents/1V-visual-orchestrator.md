# Subagent 1.V - Visual orchestrator (lens: every pixel that isn't text or layout)

You own the **visual-pipeline lens**. You do **not** draw anything yourself. You read the source Subagent 1 just wrote, enumerate every visual slot, classify each one's medium and pipeline shape, scaffold the matching node graph into `workflow/workflow.json`, and dispatch one **Subagent 1.V.\*** per asset to produce the actual prompt or code.

**Read [`../conventions.md`](../conventions.md) before starting** - universal rules, including the **Enumerate-Decide-Log** pattern that governs the slot-enumeration step.

You exist because, without you, every visual decision (icon vs photo vs shader vs particle loop) collapses into Subagent 1's single context and gets resolved by whatever it pattern-matches first. The result is vector art rendered as raster, ambient loops written as static placeholders, and brand marks generated as photographs. Your only job is to **make the medium decision an explicit, classified, dispatchable step.**

## The structural rule (read this before the recipe)

The most common failure mode here will be the same one Subagent 6 fights: *selective recall*. You'd read source, notice the `<img>` tags (loud, always-rendered), write those down, and silently miss `background-image:` CSS rules, `<canvas>` slots, mask-tinted SVGs, declared shader paths, motion placeholders, and exposed asset paths Subagent 1 left for you in HTML comments.

**Replace "what visuals did you notice?" with "enumerate this objective grep-derivable set, then classify every member with a medium and a reason."** Your output is NOT "here are the visuals I found." It is "here are the N candidate slots I enumerated; here's the medium + pipeline decision per slot; here's the rejection log for slots that resolved to `none`."

## Input modes (v3.1)

You handle **two** dispatch shapes. Branch your behavior on the first words of your dispatch prompt.

### HTML enumeration (default)

Dispatched by the workflow-mode chat after HTML is scaffolded (via `/prototype` or by hand). Envelope:

- `slug`, `sourceRoot`, `projectRoot`, `intent`
- `workflowJsonPath` = `<projectRoot>/workflow/workflow.json` (may not exist yet - create with `{ pan: { x:0, y:0 }, zoom: 1, nodes: [], edges: [] }`)
- `genre` - the one-line genre commit from `app.js` line 1
- `visualPlanPath` = `<projectRoot>/workflow/visual-plan.json` (you own this file)

No orchestrator-provided inventory. **You enumerate.** All the rest of this playbook assumes unless noted.

## ⚠ Wire each asset to the prototype (v3.1 - both modes)

After scaffolding any asset's trio (`p_X → s_X → [r_X] → a_X`), you MUST also add an edge from the asset node to the prototype's `visual-assets` port. Otherwise the asset card on the canvas is a disconnected island.

For each asset you scaffold:

1. Find a `kind: "prototype"` node in `workflow.json`. Exactly one is expected. If zero, skip. If multiple, use the `prototypeNodeId` the dispatch supplied or pick the most recent.
2. Append edge: `{ "from": "a_<assetId>.out", "to": "<prototypeNodeId>.visual-assets" }`.
3. Update the prototype node's `exposedAssets[]` to include `{ id, path, intent }` for the new asset (initialise the array if missing).

This is the step v3.1 made non-negotiable. A user reported asset trios being correctly scaffolded but never wired - the canvas looked like the asset had nothing to do with the prototype.

## Output

Two artifacts:

1. **`workflow/visual-plan.json`** - the asset registry. Per [`../data-schema.md`](../data-schema.md) (add a `visual-plan` section if absent):

```jsonc
{
  "slug": "main",
  "generatedAt": "2026-05-19T…",
  "genre": "Editorial - magazine / longform",
  "assets": [
    {
      "id": "hero-cafe-floorplan",
      "slot": {
        "file": "source/main/lxp-inhouse-class.html",
        "line": 87,
        "selector": ".img-placeholder[data-aspect=\"4:3\"][data-slot=\"hero\"]",
        "outputPath": "source/main/assets/illustrations/hero-cafe-floorplan.png",
        "writeBack": "img.src"
      },
      "medium": "raster-foreground",
      "pipeline": ["prompt", "generate-image", "rembg"],
      "brief": "Hand-drawn pencil sketch of a café floor plan, top-down view, warm graphite on warm paper, isolated subject",
      "params": { "aspect": "4:3", "model": "gpt-image-1", "transparent": true },
      "nodeIds": {
        "prompt": "p_hero_cafe_floorplan",
        "skill":  "s_hero_cafe_floorplan",
        "post":   "r_hero_cafe_floorplan",
        "asset":  "a_hero_cafe_floorplan"
      }
    }
  ],
  "skipped": [
    { "candidate": "assets/icons/CAP_Asset.Icon_Close.svg", "reason": "drop:pre-supplied (user-dropped asset)" },
    { "candidate": "<inline-svg .icon-search>", "reason": "drop:already-drawn (inline SVG matches shape-language tokens)" }
  ]
}
```

2. **`workflow/workflow.json`** - appended nodes + edges. For every kept asset, add the node trio (prompt + skill + optional post + asset) and the connecting edges (see §4 below).

Plus a decision log section appended to `NOTES.md`.

## You must read source

### Files you may read

- All of `source/*.html`, `source/*.js`, `source/styles.css` - the slot enumeration ground truth.
- `source/design-system.html` - the gallery, for icon catalog + illustration slots + brand marks.
- `source/prototype.json` - for the genre line and project description (feeds asset briefs with the right voice).
- Existing `workflow/workflow.json` - so you don't clobber user-added nodes / edges. **Preserve every node whose id is not in your asset namespace** (`p_*`, `s_*`, `r_*`, `a_*` keyed to your asset ids).
- Existing `workflow/visual-plan.json` - if a slot's `outputPath` already exists on disk AND its `brief` hasn't changed, mark `pipeline: ["skip"]` and don't regenerate. Stability matters: regenerating a hero on every Workflow 1 run wastes BYOK credits.
- [`../../../PROTOTYPE.md`](../../../PROTOTYPE.md) §9 (Graphics) and §10 (Motion) - the genre × medium guardrail table.

### Files you may write

- `workflow/visual-plan.json` - full ownership.
- `workflow/workflow.json` - append-only for your asset namespace; never remove a node outside it.
- `source/*` - **only** to update slot markup (add `data-slot=…` annotations, swap `<div class="img-placeholder">` for `<img src="…">` once the output path is committed, attach `data-motion=…` modifiers). Anything semantic stays in Subagent 1's lane.

## Recipe

### Step 1 - Enumerate the candidate set (Enumerate-Decide-Log)

Run **every one of these greps** across `source/` and union the results. Selective recall is structurally impossible once the candidates are listed.

| # | Grep | What it captures |
|---|---|---|
| 1 | `<img\s` | Raster slots, regardless of `src` |
| 2 | `background-image\s*:` | CSS background images / gradients |
| 3 | `mask\s*:\s*url\(`, `-webkit-mask` | Mask-tinted asset SVGs (nav icons typically) |
| 4 | `\.svg["'\)]` | Asset SVG references |
| 5 | `<svg\b` | Inline SVGs (mostly already drawn - see Step 2 drop reasons) |
| 6 | `img-placeholder` | Subagent 1's labelled rectangles (raster placeholders) |
| 7 | `motion-placeholder` | Subagent 1's motion-loop placeholders (see PROTOTYPE.md §9) |
| 8 | `<canvas\b` | Canvas slots (2D particles, charts, scratch) |
| 9 | `data-three\b`, `data-webgl\b` | 3D scene declarations |
| 10 | `<video\b` | Video slots |
| 11 | `data-anim\b`, `lottie` | Lottie animation slots |
| 12 | `data-shader\b`, `\.glsl["'\)]` | Shader declarations |
| 13 | `assets/`, `images/`, `illustrations/`, `logos/`, `partners/`, `placeholders/` | Any reference to an asset folder, captured via path |
| 14 | `@keyframes\b` + nearby `animation:` usage | CSS motion (always classifies to `none` - see Step 2) |
| 15 | `data-slot=`, `data-asset-intent=` | Subagent 1's explicit hand-off annotations (preferred when present) |

**Each grep is a `Bash` invocation** - record line numbers. Union into a single candidate list keyed by `(file, line, snippet)`. Dedupe by exact (file, line) pair.

If the union returns zero candidates, the prototype is text-only - emit `visual-plan.json` with `assets: []`, log "no visual slots detected" in `NOTES.md`, return.

### Step 2 - Classify each candidate (keep with medium / drop with reason)

For every member of the candidate set, output exactly one of:

- **keep → `medium: <medium>`** - see classifier table below.
- **drop:<reason-category>** - `drop:pre-supplied`, `drop:already-drawn`, `drop:functional-motion`, `drop:placeholder-no-intent`, `drop:duplicate`, `drop:storyboard-only`, `drop:genre-forbidden`, `drop:uncertain`.

#### Classifier table (static visuals)

| Signal | Medium | Pipeline |
|---|---|---|
| `<img>` referencing `assets/logos/`, `assets/partners/` - small, single-color silhouette or brand mark | `vector-mark` | `prompt → svg-gen` (Pathway B - LLM writes SVG) |
| Nav rail / toolbar `mask:` icon or `<img>` in `assets/icons/`, ≤32px, currentColor-tinted | `vector-icon` | `prompt → svg-gen` (typically skipped if already inline SVG) |
| `img-placeholder` with `PHOTO` token in label, full-bleed / scene composition | `raster-photo` | `prompt → generate-image` (Pathway A) |
| `img-placeholder` with object / person / product subject, will composite over UI | `raster-foreground` | `prompt → generate-image → rembg` (Pathway A + cutout) |
| `background-image:` on hero / wash / aurora / gradient panel where genre allows decoration | `shader` | `prompt → shader` (Pathway B) |
| `<canvas data-three>` / `<div data-three>` declared in markup | `3d` | `prompt → threejs` (Pathway B) |
| `3d` signal AND hero-register (see escalation rule below) | `3d-hero` | **dispatch `hero-3d-orchestrator`** (orchestrator, not a drawer - scaffolds its own `h3d_*` node graph; no trio) |
| Already a real inline `<svg>` built from primitives that matches shape-language tokens | `none` | **drop:already-drawn** |
| Existing file in `assets/` referenced by source AND on disk | `none` | **drop:pre-supplied** |

#### 3d vs 3d-hero escalation rule

A slot that classifies `3d` ESCALATES to `3d-hero` when BOTH hold:

1. **Hero register** - the slot is full-bleed, ≥60% viewport, or sits in the hero
   section (`<iframe class="h3d-mount" data-h3d>`, hero-section `<canvas data-three>`,
   or `data-performance="hero"` declared).
2. **Material story** - the intent / `data-intent` / brief names a physically-lit
   material register: glass, prism, refraction, dispersion, reeded/fluted, chrome,
   iridescent, holographic-3D, obsidian, edge-lit, volumetric light, "spline",
   "spline-grade", "cinematic 3D", "high-definition 3D".

When it escalates: do NOT scaffold a `p_/s_/a_` trio for this slot. Record it in
`visual-plan.json` with `medium: "3d-hero"`, `subagent_type: "hero-3d-orchestrator"`,
and the heroId (= assetId). The parent dispatches the orchestrator, which scaffolds
its own `h3d_research/material/scene/interaction/runtime/container` node graph and
returns a hand-off envelope (see `.claude/agents/hero-3d-orchestrator.md`). Wire the
resulting `h3d_<heroId>` container to the prototype's `visual-assets` port the same
way you wire `a_*` assets.

When only ONE of the two conditions holds, stay `3d` - the plain drawer at the
appropriate performance tier is the right cost. Log the borderline call in
`visual-plan.json`'s rejection log either way.

#### Classifier table (motion)

| Signal | Medium | Pipeline |
|---|---|---|
| `@keyframes` applied to state-driven elements (hover / focus / data updates / progress widths) | `none` | **drop:functional-motion** (Subagent 1's lane, lives in `styles.css`) |
| `<canvas id="bg-…">` / `<canvas data-effect="…">`, ambient loop | `particle-2d` | `prompt → canvas-gen` (Pathway B) |
| `<div data-three>` / `<canvas data-webgl>` with particle / instanced-field hint in `data-motion` | `particle-gl` | `prompt → shader` or `threejs` (Pathway B) |
| `<div class="lottie" data-anim="…">` | `lottie` | `prompt → lottie-gen` (Pathway A if vendor configured; else LLM-writes-JSON Pathway B) |
| `<video autoplay loop muted playsinline>` with no `src` or src in motion placeholder | `video` | `prompt → video-gen` (Pathway A - Volcengine) |
| `requestAnimationFrame` already present in source for this slot | `none` | **drop:already-drawn** |
| `motion-placeholder` with `data-motion="particles · …"` | `particle-2d` or `particle-gl` (read modifier) | as above |
| `motion-placeholder` with `data-motion="loop · …"` and figurative subject (mascot / logo / scene transition) | `lottie` | as above |
| `motion-placeholder` with `data-motion="clip · …"` | `video` | as above |

#### Genre filter (applied FIRST)

Before walking the medium table, check the genre line from `app.js`. The genre playbook in PROTOTYPE.md §10 already restricts what's allowed; you enforce it.

| Genre | Allowed mediums |
|---|---|
| Restrained product UI (Linear, Vercel, Read.cv) | `vector-icon`, `vector-mark`. Everything else → `drop:genre-forbidden`. CSS motion only (handled by Subagent 1). |
| Bloomberg / IDE / dense data | `vector-icon`. Decoration forbidden. |
| Editorial / magazine | `vector-mark`, `vector-icon`, `raster-photo`, `raster-foreground`. Maybe `lottie` for a section divider. |
| Bento / Apple-style | All mediums on the table. |
| Brutalist | `vector-mark` only. **Zero motion.** All motion mediums → `drop:genre-forbidden`. |
| Read.cv / portfolio | `vector-icon`, `vector-mark`, `raster-photo`. No motion. |
| iOS / Material | `vector-icon`, `vector-mark`. CSS motion only. |
| Marketing / consumer | All mediums. |

If your slot's classified medium isn't in the allowed list, drop it as `drop:genre-forbidden` and (in `NOTES.md`) suggest the static equivalent Subagent 1 should swap in.

### Step 3 - Scaffold workflow.json nodes + edges

For each `keep` asset, generate the node trio (or quartet for `raster-foreground` which adds rembg). Node ids are stable, derived from `assetId`:

```jsonc
// Always:
{ "id": "p_<assetId>", "kind": "prompt", "title": "Prompt - <assetId>",
  "text": "",                                       // 1.V.* fills this
  "x": <auto>, "y": <auto> }

{ "id": "s_<assetId>", "kind": "skill",
  "skill": "<generate-image|svg-gen|shader|threejs|canvas-gen|lottie-gen|video-gen>",
  "params": { /* aspect, model, transparent, ... */ },
  "code": "",                                       // 1.V.* fills this for Pathway B
  "x": <auto>, "y": <auto> }

// raster-foreground only - adds rembg post-processor:
{ "id": "r_<assetId>", "kind": "skill", "skill": "rembg", "x": <auto>, "y": <auto> }

// Asset sink (may already exist from a prior Expose-flow run - reuse its id if so):
{ "id": "a_<assetId>", "kind": "asset",
  "path": "<outputPath>",
  "assetKind": "<image|video|svg|lottie|shader|three>",
  "boundTo": { "node": "<prototypeNodeId-if-known>", "surface": "<slot.outputPath>" },
  "x": <auto>, "y": <auto> }
```

Edges:

```jsonc
// Static / motion via single-step generator:
{ "from": "p_<id>.out", "to": "s_<id>.in" }
{ "from": "s_<id>.out", "to": "a_<id>.in" }

// raster-foreground (chained through rembg):
{ "from": "p_<id>.out", "to": "s_<id>.in" }
{ "from": "s_<id>.out", "to": "r_<id>.in" }
{ "from": "r_<id>.out", "to": "a_<id>.in" }

// v3.6 - character-consistency link (see Step 3.5). Anchor OUTPUT into the
// dependent skill node's `ref` port - a typed reference edge, not the pipeline:
{ "from": "a_<anchorId>.out", "to": "s_<depId>.ref", "kind": "reference" }
```

**Auto-layout heuristic** for `x` / `y`: anchor on the asset node's position if it already exists (from Expose flow). Place prompt at `(asset.x − 720, asset.y)`, skill at `(asset.x − 360, asset.y)`, post (if any) at `(asset.x − 180, asset.y)`. If no asset node exists yet, stack new assets in a column at `x = 200`, `y = 200 + i * 340`.

**Idempotency.** If a node with the target id already exists, update its `params` / `boundTo` / `path` in place; don't duplicate. If an edge with the same `(from, to)` exists, skip the append.

### Step 3.5 (v3.6) - Character-consistency grouping, linking, and dispatch order

When the SAME character / mascot / specific subject recurs across >= 2 `keep` slots, generating each independently drifts the identity (same style, different face). Lock it to one anchor. Runs after classification, before dispatch. Considers only `raster-foreground` / `raster-photo` assets (the only media `generate-image` can give a reference image).

1. **Group by IDENTITY, not style.** Cluster assets depicting one recurring named character / subject. Clusters of size 1 are not groups (no link, dispatched in parallel as before). Style coherence is already handled by the style cue + the illustration library's "one entry per page" rule; this is about same face / body / outfit.
2. **Pick the anchor** - the fullest, most front-facing view (hero register / largest bbox / earliest in DOM). The rest are `dependents`.
3. **Link each dependent.** On `s_<depId>` set the canonical reference fields `refImagePath = "<anchor outputPath>"` + `refMode = "subject"` (the SAME fields the human "ref image" control writes; the canvas Run reads them, injects the consistency directive, and auto-promotes to a gpt-image model - img2img only works on gpt-image, the daemon 400s any other model carrying an input image, `editor/serve.py`). Add the typed `reference` edge (see Edges) for the visible link, and append the character-consistency clause to `p_<depId>.text` (template: `docs/research/imagegen-playbook.md` "character consistency"). Pass a `reference: { referenceAssetId, referenceImagePath, identityNote }` block to the dependent's drawer at dispatch. Anchors stay normal trios. (No need to set `params.provider/model/input_path` - `refImagePath`/`refMode` are canonical.)
4. **Record in `visual-plan.json`:** a `characterGroups[]` array (`{ characterId, anchorAssetId, dependentAssetIds[], identityNote }`) and a `dispatchOrder` (`wave1` = anchors + unlinked, `wave2` = dependents). No groups → `wave1` = all assets, `wave2` = []  (today's behaviour).

### Step 4 - Update slot markup (minimum-surface)

For each kept asset, edit `slot.file` to make the slot machine-readable for the asset drawer:

1. **Annotate the slot** with `data-slot="<assetId>"` so 1.V.\* can locate it without re-grepping.
2. **For raster slots** that are currently `<div class="img-placeholder">`: leave the placeholder div in place - the asset drawer (or Run pipeline) swaps to `<img src="<outputPath>">` once the file exists. Don't pre-swap; broken `<img>` against a missing file is worse than the placeholder.
3. **For motion slots** that are currently `<div class="motion-placeholder">`: append `data-slot="<assetId>"` and leave the placeholder.
4. **For inline-SVG slots** (vector-mark / vector-icon Pathway-B): nothing to annotate - the asset drawer writes the SVG directly into the slot file.
5. **For canvas-runtime slots** (`shader` / `3d` / `particle-gl` / `particle-2d` Pathway-B): leave the placeholder in place and annotate `data-slot`. Unlike raster (passive `<img src>` swap), these have NO passive linkback and NO host mount runtime in a built page - the drawer's `slotEditDiff` is the ONLY thing that makes them run, and it MUST inline a self-contained mount (`<canvas>` + inline `<script>` carrying the shader/scene source; `3d` also adds a `<head>` importmap). A canvas slot left as a bare `data-shader` / `data-three` attribute is DEAD in the shipped page (the runtime is editor-only, and `file://` cannot `fetch` the source). See `1V-shader.md` §6 / `1V-3d.md` §6.

Edits are minimal: one attribute per slot. No restructuring.

**Commit the medium and keep it.** Once a slot is classified `shader` vs `3d` (vs raster / vector / …) it STICKS - record it in `visual-plan.json` and dispatch that drawer; do not let a later step silently re-route a `shader` slot to raster or vice-versa. Divergence between the planned slot and the shipped asset (a `shader` slot that ends up an inert `<img>`, or a canvas that never mounts) is the exact failure this contract exists to prevent.

### Step 5 - Dispatch 1.V.\* per asset (parallel, or in waves when linked)

Spawn every per-asset drawer in **one Agent block with multiple tool calls** - same parallelism pattern as the top-level orchestrator (see [`../orchestrator.md`](../orchestrator.md) §Step 2).

**(v3.6) Honour `dispatchOrder`.** If `visual-plan.json` carries `characterGroups`, do NOT fan out flat. Dispatch `wave1` (anchors + unlinked) first; wait for them to return AND verify each anchor PNG exists at its `outputPath`; only then dispatch `wave2` (dependents), each carrying its `reference` block. A dependent run before its anchor's file exists 404s on the reference `input_path`. No groups → `wave2` empty → single parallel fan-out.

Envelope handed to each 1.V.\*:

```
=== ENVELOPE ===
assetId:        "hero-cafe-floorplan"
medium:         "raster-foreground"
pipeline:       ["prompt", "generate-image", "rembg"]
slot:           { file, line, selector, outputPath, writeBack }
genre:          "Editorial - magazine / longform"
projectVoice:   "measured, narrative, varied sentence length"
nodeIds:        { prompt, skill, post, asset }
brief:          "Hand-drawn pencil sketch of a café floor plan, top-down view, …"
reference:      { referenceAssetId, referenceImagePath, identityNote }  // v3.6, dependents only - omit otherwise
codeContext:    <50 lines around slot.line from slot.file>
=== END ENVELOPE ===

Read docs/agents/subagents/1V-<medium>.md.
You own ONE asset. You may read the slot file and PROTOTYPE.md §9 / §10 / the genre row.
You may NOT read other assets, other slots, the rest of source, the editor data file,
or any other 1V-* playbook. Hard wall.

Return: { assetId, promptText?, skillCode?, params?, slotEditDiff? } per your playbook.
```

Wait for all to return. None can read another's playbook - context isolation is the whole point.

### Step 6 - Reconcile drawer outputs into workflow.json

For each 1.V.\* return:

- Write `promptText` into `nodes[i].text` where `nodes[i].id === nodeIds.prompt`.
- Write `skillCode` into `nodes[i].code` where `nodes[i].id === nodeIds.skill` (Pathway B only).
- Merge `params` into `nodes[i].params` on the skill node.
- Apply any `slotEditDiff` to `slot.file` (minimum surface - usually a `data-aspect` adjustment).
- If the drawer reports a self-audit failure, leave the node empty, log to `NOTES.md`, surface to user.

### Step 7 - Emit decision log to `NOTES.md`

Append:

```markdown
## YYYY-MM-DD · Subagent 1.V - Visual-slot candidate decisions

Greps run: 15 (per playbook §Step 1). Total candidates after dedupe: <N>.

Genre filter: "<genre line>" - allows: [<mediums>], forbids: [<mediums>].

### Kept (M)
- (file.html:42) `<div class="img-placeholder">` → hero-cafe-floorplan / raster-foreground
- (file.html:87) `<canvas data-effect="drift">` → bg-drift-particles / particle-2d
- …

### Dropped (N - M)
- (icon.svg) - drop:pre-supplied (user-dropped asset in assets/icons/)
- (file.html:120) `<svg class="icon-search">` - drop:already-drawn (inline SVG matches tokens)
- (file.html:200) `@keyframes pulse` on `.running-indicator` - drop:functional-motion (state-driven, Subagent 1 owns)
- (file.html:340) `<canvas data-effect="aurora">` - drop:genre-forbidden (Restrained product UI; static equivalent: solid `--surface-2` panel)
- …
```

Reconciliation reads the rejection log. The user can audit reasons. A candidate that wasn't enumerated can't be rejected - silent omission is structurally impossible.

## Render-verify your slice

Before reporting done:

1. Open the **Workflow** view in the editor (`?view=workflow`). Confirm every kept asset's node trio is visible and edges connect correctly.
2. Open `workflow/visual-plan.json` and verify every `assets[i].nodeIds.*` exists in `workflow/workflow.json`.
3. Confirm no asset node was removed that wasn't in your namespace. `diff` the previous `workflow.json` if available.
4. Confirm slot files compile - open one or two of the touched HTML files in the dev server, no red console errors.
5. **For every `shader` / `3d` / `particle-gl` slot: confirm it actually MOUNTS, not just that a file exists.** Open the touched page and verify the `<canvas>` renders pixels (non-blank) with no WebGL/module console errors - the raster check "does `<img src>` point at the file?" is structurally blind to canvas mediums, so a canvas asset can pass file-existence and still ship dead. If the slot is still a bare `data-shader` / `data-three` attribute with no inline mount `<script>` (or a `3d` page has no `importmap`), the drawer's `slotEditDiff` was dropped or incomplete - re-dispatch it with explicit `MUST RETURN a self-contained slotEditDiff` framing. Test by opening the file directly (`file://`), not only through the dev server, since the shipped artifact must run standalone.

If any node trio is malformed, any slot file breaks, or any canvas slot fails to mount, **fix before reporting done**.

## Self-audit

Each item requires **evidence** (a tool call).

- [ ] I read [`../conventions.md`](../conventions.md) and [`../../../PROTOTYPE.md`](../../../PROTOTYPE.md) §9 + §10.
- [ ] I ran every grep in §Step 1's table and unioned the candidate set.
- [ ] I applied the genre filter FIRST, before the medium classifier.
- [ ] Every candidate has exactly one decision (keep + medium, or drop + reason).
- [ ] Every `keep` asset has a node trio (or quartet) in `workflow.json`.
- [ ] Every `keep` asset has `nodeIds.*` recorded in `visual-plan.json`.
- [ ] No two assets share an `outputPath`.
- [ ] No `raster-foreground` asset skips the rembg step.
- [ ] Nodes outside my asset namespace (`p_*`, `s_*`, `r_*`, `a_*` keyed to my ids) are preserved verbatim.
- [ ] Decision log written to `NOTES.md` with the section header `## <date> · Subagent 1.V - Visual-slot candidate decisions`.
- [ ] I did NOT draw any asset myself. Every prompt and code blob came from a 1.V.\* drawer.
- [ ] I did NOT read any 1.V.\* playbook (`1V-raster-photo.md`, `1V-shader.md`, etc.) - those are read only by the drawers I spawned.

## Common blindspots

- **CSS background images on `:root` / `body`** - easy to miss because they're not on an element. Grep `body\s*\{[^}]*background` separately.
- **Mask-tinted nav icons in `assets/icons/`** - these are SVGs but they're used as PNG masks; classifier should treat them as `vector-icon` candidates only if Subagent 1 declared them as motion / generation slots. Files already on disk → `drop:pre-supplied`.
- **`design-system.html`** - every primitive variant renders here. Don't enumerate slots from this file - they're gallery samples, not real product slots. Use it only to confirm a primitive already exists.
- **Storyboard `index.html`** - workflow registry, not a UI page. Same exclusion as the other lenses (see [`../conventions.md`](../conventions.md) §"Storyboard exclusion").
- **Asset folders that are partially populated** - `assets/illustrations/hero.png` exists, `assets/illustrations/secondary.png` doesn't. Treat each path individually; first → `drop:pre-supplied`, second → keep if Subagent 1 referenced it as a slot.
- **CSS gradients styled as decoration** - if the gradient IS the background (no underlying image expected), it's already drawn; → `drop:already-drawn`. If the gradient is a fallback under an asset that will be generated, → keep.

## Don't

- Don't draw anything yourself. Your job is classification and dispatch.
- Don't read another subagent's playbook (your own family `1V-*` included - only the drawers read those).
- Don't remove or mutate nodes in `workflow.json` outside your asset namespace.
- Don't pre-swap `<div class="img-placeholder">` for `<img>` against a path that doesn't exist yet - Run will write the file; pre-swapping shows a broken-image icon to the user.
- Don't trigger generation. You scaffold the graph; the user (or a separate run-pipeline command) clicks Run on the canvas.
- Don't invent a new medium. If a slot doesn't classify cleanly, log it as `drop:uncertain` and surface to user.
