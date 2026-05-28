# Workflow 2 — Apply `edits.json`

**Trigger:** `edits.json` appears at repo root.

Edits target the branch named in `edits.json → sourceRoot`. **Never cross branches.**

## Shape

```json
{
  "project": "…", "sourceRoot": "../source/<slug>", "submittedAt": "ISO",
  "edits": [
    { "kind": "...", "frameId": "...", "selector": "...", "side": "top|right|bottom|left",
      "snippet": "...", "text": "...", "libId": "Button.primary",
      "parent": {
        "selector": "...", "tag": "div", "snippet": "...",
        "childCount": 12, "childIndex": 5,
        "layout": { "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
                    "flexDirection": "row", "gap": "32px", "alignItems": "stretch",
                    "justifyContent": "normal", "padding": "0px" }
      }
    }
  ],
  "annotations": [ … ]
}
```

**Order:** model edits (`target ≠ "dom"`) before DOM edits in the same file — renames must be in effect when selectors resolve.

## DOM edit kinds (`target = "dom"` or implicit)

- **`duplicate`** — clone element at `selector` as sibling on `side` (top/left → before; bottom/right → after).
- **`primitive`** — insert a primitive matching surrounding voice/density. Defaults: Pill near text metadata · Button at row trailing · Row free-standing.
- **`library`** — insert `libId` from `editor/data.js → library`. Honor its `compose` block (`role`, `spaceFromText`, `avoidIn`).
- **`blank`** — empty placeholder. In a grid, inherits column rhythm; otherwise empty `<div>` sized to neighbours.
- **`text`** — replace text content. Compare `oldText` with current source. Drifted → log in `NOTES.md`, don't overwrite. Only touch text nodes.
- **`delete`** — remove element. If its data lived in `window.DEMO`, remove that entry too. Inside a hand-counted grid `repeat(N, …)`, decrement `N`.
- **`replace`** (`edit.replace === true`) — replace with `libId` or blank. Data-type-aware: same entity → copy fields; different → stock values + `NOTES.md` note.
- **`style`** — inline-style override. Payload `styles: {…}`. Mode keys (`widthMode` etc.) are editor state — don't write to source. Use `parent.layout.display` to decide materialisation: in flex, `width: 100%` may need `flex: 1 1 0`; centering = `margin-inline: auto`.
- **`move`** — DOM-order shuffle within flex/grid, `direction: "prev" | "next"`. Multiple moves accumulate; after each, update other edits' selectors (`:nth-of-type` shifts).
- **`comment`** — **don't modify source.** Answer + append resolution to `NOTES.md` under `## <selector> on <frameId>`.

**Grid semantics** when `parent.layout.display === "grid"`:
- `add` / `duplicate` / `primitive` / `library` / `blank` → adds a column.
- `delete` → removes that column; decrement hand-counted `grid-template-columns`.
- `replace` → replaces column content; keeps the track.

## Model edit kinds (`target ≠ "dom"`)

Mutate `editor/branches/<slug>.js`. Preserve `meta.branch`, `meta.branchLabel`, `meta.sourceRoot`, `meta.sourceEntry`, `meta.exploration` verbatim.

**Round-trip rule.** Every model edit also writes to `source/<slug>/prototype.json` so Workflow 1 re-runs don't undo it. If the manifest doesn't exist, create it from the current data file on the first model edit.

| Edit `target` | Editor data path | Manifest path |
|---|---|---|
| `frame.*` | `frames[]` | `frames[]` |
| `arrow.*` | `arrows[]` | `arrows[]` |
| `link.*` | `links[]` | `links[]` |
| `meta.lane.*` | `meta.lanes[]` | `lanes[]` |
| `ia.entity.assign / unassign` | per-frame `entities[]` | per-frame `entities[]` |
| `entity.*` (incl. `property.*`) | `entities[]` + `window.DEMO` | `entities.json` (if it exists) |
| `*.comment` | nothing (append to `NOTES.md`) | nothing |

### `target: "entity"`

- `add` — append `{ id, tag, x, y, w, fields }`; seed matching empty `window.DEMO` array.
- `rename` (`entityId` → `newId`) — rewrite every `fk` / `type` that referenced the old id, plus the `window.DEMO` key.
- `delete` — drop `fk` references (convert to `string`, note in `NOTES.md`), remove source-data array.
- `property.add` / `rename` / `delete` — apply to `fields[]` and every `window.DEMO` row.
- `*.comment` — log under `## entity · <id>` or `## field · <entityId>.<fieldName>`.

### `target: "link"`

Entity↔entity links in `links[]`. `add` / `update` / `delete` by `id`. Cardinality `1:1` / `1:N` / `N:1` / `N:N`; strength `strong` / `weak` / `assoc`. Materialise source implications: 1:N strong → FK on the many side; N:N association → join entity with `tag: "assoc"`.

### `target: "frame"`

- `add` — `{ id, label, kind, lane?, parent?, hash?, x, y, w, h }`. New frame with a `hash` needs a source route (component or `setupScript`).
- `rename` — change `label`; don't auto-rename `id`.
- `delete` — remove frame + all touching arrows.
- `move` — update `lane` / `rank` / `parent` / `kind_` (frame kind renamed — `kind` is reserved on the edit).
- `comment` — log under `## frame · <id>`.

### `target: "arrow"`

- `add` / `update` / `delete` by id.
- `split` (`{ arrowId, newFrame, actionA, actionB }`) — insert `newFrame` between A and B; rewrite original's action to `actionA`; append `newFrame → B` with `actionB`.

### `target: "ia"`

Frame-level metadata, no source change. `entity.assign` / `entity.unassign` toggle in the frame's `entities: [...]`. `comment` → `## ia · <frameId>` in `NOTES.md`.

### `target: "meta"`

- `lane.add` — append `{ id, label, kind: "user|system|service" }` to `meta.lanes`.
- `lane.rename` / `lane.delete` by `laneId`.

If source visibly drifts from a model edit (renamed entity demands renamed `window.DEMO` key, new frame demands a route), apply the source change too. Non-trivial diffs → one bullet under `## <date> · model edits` in `NOTES.md`.

## Annotations

One entry per annotated frame:

```json
{ "frameId": "...", "frameLabel": "...", "frameHash": "...", "sourceUrl": "...",
  "strokes": [{ "points": [{"x":120,"y":40}, …] }],
  "comment": "...", "screenshot": "data:image/png;base64,…" }
```

- `screenshot` is iframe-body + strokes rasterised in red. **No editor chrome.** May be `null` — fall back to the live page at `sourceUrl`.
- `strokes[].points` in iframe-content pixels.
- Visual feedback, not structural. Interpret strokes + comment together; respond as a `comment`-style action. **Don't silently mutate DOM.** Log interpretation under `## annotation · <frameLabel>` in `NOTES.md`.

## Per-edit Design audit (mandatory)

Apply one edit at a time. Don't batch.

1. **Grid integrity** — `repeat(N, …)` and insert past `N`? Bump `N` or switch to `repeat(auto-fit, minmax(…, 1fr))`. Never mix `1fr` with hardcoded widths unless source does.
2. **Spacing** — parent has `gap` → fine. Otherwise `margin-block-start: var(--pad-sm)`. **Never literal px** — promote to a token.
3. **Alignment** — centred flex/grid → set `align-self` (`start` on a pill among headings; `end` on a trailing button).
4. **Voice match** — insert overshadows neighbours? Downgrade (e.g., `Filter.pressed` → `Filter.default`). User asked for the loud one? Leave it + note the trade-off.

**Verification:** `preview_screenshot` the affected frame. Cramped/misaligned → one correction round, re-screenshot. **Cap at two passes** — third means the edit is wrong at spec level; log in `NOTES.md`.

## Source-vs-preview parity

`htmlByVariant` drift is the most common bug. Each primitive variant declares `from: { selector, hash? }` and `htmlByVariant[v]` is copied from rendered source.

DS view badges: `live` (extracted now) · `stale` (selector didn't match — fix selector or set `hash`) · (none) (no `from` declared — only acceptable on the canonical stub).

If you change a primitive's source behaviour, re-run Workflow 1. Don't patch `htmlByVariant` by hand.

## After all edits

1. Re-run Workflow 1 if structure shifted.
2. Re-run Workflow 3 if tokens or primitives changed.
3. Delete `edits.json`.
