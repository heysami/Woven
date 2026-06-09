# Subagent 3 — Prototype (lens: iframe loadability)

You own the **iframe-loadability lens**. For each frame source can render in an iframe, you produce the URL bits that make it load that specific state.

**Read [`../conventions.md`](../conventions.md) before starting** — universal rules + naming + `__pokeBy` is server-injected (see U2).

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`

No orchestrator-provided inventory. You enumerate iframe-loadable frames yourself.

## Output

Per [`../data-schema.md`](../data-schema.md): `frames[i].entry`, `frames[i].hash`, `frames[i].setupScript`, **`frames[i].w`, `frames[i].h`** (REQUIRED — PrototypeView reads `active.w` and `active.h` directly with no fallback to `meta.defaultFrame`; if you omit them the iframe collapses to 0×0).

```json
{
  "frames": [
    { "id": "library",          "label": "Library",          "entry": null,              "hash": "",       "setupScript": null, "w": 1440, "h": 900 },
    { "id": "library-cmdk",     "label": "Command palette",  "entry": null,              "hash": "#cmdk",  "setupScript": null, "w": 1440, "h": 900 },
    { "id": "checkout-payment", "label": "Payment step",     "entry": "checkout.html",   "hash": "#payment","setupScript": null, "w": 1440, "h": 900 },
    { "id": "apply-submitted",  "label": "Application sent", "entry": "lxp-apply.html",  "hash": "",       "setupScript": "window.__pokeBy(\"App\", \"submitted\", true)", "w": 1440, "h": 900 }
  ]
}
```

**`w` / `h` are mandatory on every frame.** Emit `meta.defaultFrame.w` / `.h` (1440 / 900 default) unless the source page explicitly sets a different viewport (e.g. a mobile page that uses `<meta name="viewport" content="width=393">` — then emit 393×852 or whatever the actual viewport is).

## CRITICAL: `__pokeBy` is server-injected by `editor/serve.py`

`window.__pokeBy(componentName, stateName, value)` and `window.__poke(componentName, hookIndex, value)` are **injected by the dev server into every `source/*.html` response at runtime**. They are NOT in source files on disk. Grepping source for `__pokeBy` returns nothing — that is **not** a signal the helper is unavailable.

**The helpers are always available at runtime.** Write `setupScript` freely for any frame that needs a useState branch flipped. Do not return `setupScript: null` because you "couldn't find" the helper — read `editor/serve.py` to confirm the injection.

## You must read source

### Files you may read

- **`editor/serve.py`** — read the `POKE_HELPER` block (around L176) once to confirm the injection contract.
- `source/*.html` — find `<a href>`, hash routes, useState declarations.
- `source/*.js` — find component-name + state-variable identifiers for `__pokeBy`.

## Enumerate through your lens

A frame is iframe-loadable if source has a way to render it. Through your lens:

- **Include**: top-level pages, useState branches the source supports flipping, modals/sheets the source supports opening.
- **Exclude (Flow-only kinds)**: triggers, notifications, externals, decisions, starts, inputs — nothing to load in an iframe.
- **Exclude**: the storyboard (it's a workflow registry, not a screen you'd want to iframe inside the editor).
- **Exclude**: the demo dock (`<div class="demo-dock" data-demo-only="true">`, PROTOTYPE.md §11) — it's scaffolding. Its rows map 1:1 to the view-variant frames you already enumerate via useState detection.

## Recipe

1. **Entry.** For multi-HTML sources, each enumerated frame's source HTML is its `entry` (bare filename). For single-HTML, `entry: null` (use `meta.sourceEntry`).
2. **Hash.** If the frame requires a specific `location.hash` value to render the right state (`#cmdk`, `#page=settings&tab=team`), capture it. Else empty string.
3. **`w` / `h`.** Read `meta.defaultFrame` from the orchestrator's envelope (or default 1440×900). Emit those values on every frame **unless** the source page sets a different viewport explicitly (mobile prototype with `<meta name="viewport" content="width=393">` → emit `w: 393, h: 852`).
4. **setupScript.** For frames whose render requires a useState flag flipped:
   - Identify the component function name where the `useState` lives. `__pokeBy` takes **any** component name and walks the React fiber tree to find it via `findFiber(name)` (see `editor/serve.py` POKE_HELPER lines 237–250). It's NOT limited to `App`.
   - Identify the state-variable name from `useState(...)` declarations.
   - Write `window.__pokeBy("<ComponentName>", "<stateName>", <value>)`.
   - **Value-shape gotcha.** Read where the state is *consumed* in JSX, not just where declared. `<h3>Decline Run ${declineFor}</h3>` expects a primitive that stringifies cleanly; passing an entity object renders `[object Object]`.
   - **Sub-component state — DON'T self-censor.** If the useState lives inside a child component (`LearningTasksCard`, `ReviewQueue`, `Sidebar`), name THAT component, not `App`. The dashboard-tabs failure mode in real prototypes: `App` doesn't have an `active` state, but `LearningTasksCard` (the card with the tabs) does. `__pokeBy("LearningTasksCard", "active", 2)` poking the sub-component's state IS the right call — don't return `setupScript: null` because "the App component doesn't have this state."

### Tab states are the most common case — emit them, don't skip

Tabs almost always share a single `activeTab` / `selectedTab` / `active` useState. The frame for each tab is a `substep` of the parent page; each gets its own setupScript that flips the tab variable to that tab's identifier:

```js
// App-level tabs (state in the root component):
// frame: lxp-inhouse-application-tab-runs
"setupScript": "window.__pokeBy(\"App\", \"activeTab\", \"runs\")"
// frame: lxp-inhouse-application-tab-timeline
"setupScript": "window.__pokeBy(\"App\", \"activeTab\", \"timeline\")"

// Sub-component tabs (state in a child component — index-based):
// LearningTasksCard has  const [active, setActive] = useState(0)
// where active=0 is "All", 1 is "In-house", 2 is "External"
// frame: lxp-dashboard-tab-in-house
"setupScript": "window.__pokeBy(\"LearningTasksCard\", \"active\", 1)"
```

To find which component owns the tab state:

1. Grep for the tab label / tab key (`"runs"`, `"timeline"`, `"in-house"`) in `.js` files.
2. Backtrack from the conditional render (`{activeTab === "runs" ? ...}`) to the `useState` declaration.
3. Walk upward to the enclosing function — that's the component name.
4. If the state is a literal string match, use the string value. If it's a numeric index (`useState(0)`), the value is the index (0, 1, 2, …) — read the JSX to map tab labels to indices.
5. **Verify each `setupScript` by rendering the frame.** The poke helper is fire-and-forget — silent no-op on mismatch (component name, hook index, value shape, fiber-tree timing). Load the editor + the frame, screenshot the result. If the modal / submitted-state isn't visible, the script is wrong — trace consumer, fix, retry. **Do not return `setupScript: null` because you assumed it wouldn't work.**
6. **Render-verify your whole slice.** After producing your output, load the editor's **Prototype** view. Walk every frame in your output via the left nav. Confirm:
   - Each frame's iframe is not collapsed (visible area > 100×100 px).
   - Each frame appears in the nav (no orphaned to "Other screens" except deliberately).
   - Each `setupScript`-driven branch is visible on load.
   If anything's wrong, fix it before reporting done.

## Self-audit (run before returning)

Each item requires **evidence** — a Read / Bash / Grep / screenshot call. Don't tick implicitly.

- [ ] I read `conventions.md` (U2 in particular: `__pokeBy` is server-injected).
- [ ] I read `editor/serve.py` and located the `POKE_HELPER` block. (Read tool call required.)
- [ ] I scanned every `.html` for `<a href>` + `useState(`. (Bash grep required.)
- [ ] I read the relevant `.js` files for component-name and state-variable identifiers.
- [ ] **Every frame has `w` and `h` set** (no missing dimensions — PrototypeView collapses to 0×0 otherwise).
- [ ] For every frame I enumerated whose render requires a useState flag (state / overlay / substep), I wrote a `setupScript` AND rendered the frame to verify the intended branch is visible. (Screenshot required.) **No silent `null` because I "didn't find the helper" — see U2.**
- [ ] **Every `kind: "substep"` frame that represents a tab has a non-null `setupScript`** poking the relevant component's tab variable. A tab substep with `setupScript: null` will load the page with the default tab — not the targeted one. Tab substeps without scripts are the most common silent failure mode.
- [ ] **For sub-component tab state**, I wrote `__pokeBy("<SubComponentName>", "<stateVar>", ...)` not `__pokeBy("App", ...)`. The poke helper walks the fiber tree by name (see `editor/serve.py` POKE_HELPER) — naming the wrong component returns null and silently no-ops.
- [ ] All `entry` values are `null`, bare filename, or editor-relative — never `editor/`-relative.
- [ ] My frame IDs follow the naming convention.
- [ ] I excluded the storyboard + Flow-only kinds.
- [ ] **I rendered the Prototype view in the editor, walked every frame in my output via the nav, and confirmed each iframe loads at full size with the right branch visible.** (Screenshot.)

## Common blindspots

- **Tab substep with `setupScript: null`.** The single most common failure: enumerating four tab substeps, writing entries for them in `frames[]`, but emitting `setupScript: null` for each because "they don't look like App-level booleans." The arrow exists, the iframe loads, but clicking the substep shows the page with the default tab. Always emit `__pokeBy(<owning-component>, <tabStateVar>, <thisTabsValue>)` for every tab substep.
- **Sub-component state self-censored.** "App doesn't have this useState → must not be possible to poke." Wrong — `__pokeBy` works with any component name. `LearningTasksCard`, `Sidebar`, `ReviewQueue`, any function component owns its own hooks; name THAT component.
- **Hash that doesn't actually trigger the state.** You wrote `hash: "#cmdk"` because the UI mentions a command palette, but source never reads `location.hash`. Grep `location.hash` / `hashchange` in source — if absent, that hash is a no-op. Use `setupScript` instead.
- **`setupScript` value-shape mismatch.** Source consumes the state as `<h3>Decline Run ${declineFor}</h3>` (expects a primitive) but you poked an entity object — renders `[object Object]`. Always read the consumer JSX before picking the value shape.
- **Wrong component name.** Source has `createRoot(...).render(html\`<${Shell}/>\`)` but you wrote `__pokeBy("App", ...)`. The component-name string in `__pokeBy` must match the actual function name being rendered.
- **Index vs string mismatch.** `useState(0)` (numeric) → poke with index integer. `useState("draft")` (string) → poke with literal string. Mixing them silently no-ops.
- **Mobile viewport not detected.** Source has `<meta name="viewport" content="width=393">` but you emitted `w: 1440`. The iframe will render desktop-width in a phone-sized region — broken layout.
- **Tab content via hash vs state.** Some tabs use `#tab=team`, others use internal state. Read source carefully — only emit the hash form if source actually parses it.

## Don't

- Don't return `setupScript: null` for a state/overlay/substep frame on the assumption the helper is missing. The helper is server-injected. Render and verify.
- Don't invent frames not enumerable from source.
- Don't include storyboard or Flow-only kinds.
- Don't write `kind`, `lane`, `parent`, `col`, `row`, `entities`.
