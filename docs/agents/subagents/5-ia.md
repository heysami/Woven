# Subagent 5 - Information architecture (lens: sitemap)

You own the **sitemap lens**. Enumerate what *you* see as a sitemap node, and decide which entities each renders.

**Read [`../conventions.md`](../conventions.md) before starting** - universal rules + naming.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`

No orchestrator-provided inventory or entity list. You enumerate. You'll cross-check entity assignments with Subagent 7's output during reconciliation - for now, identify entity IDs via the naming convention (singular PascalCase of `DEMO.<key>`).

## Output

Per [`../data-schema.md`](../data-schema.md): `frames[i].parent`, `frames[i].entities`.

```json
{
  "frames": [
    { "id": "library",              "label": "Library",        "parent": null,      "entities": ["Reference", "Collection"] },
    { "id": "library-cmdk",         "label": "Command palette","parent": "library", "entities": [] },
    { "id": "settings",             "label": "Settings",       "parent": null,      "entities": [] },
    { "id": "settings-tab-team",    "label": "Settings · Team","parent": "settings","entities": ["Member"] }
  ]
}
```

## CRITICAL: You must grep, not guess from frame labels

The single most common failure: assigning entities based on the frame's label (`"lxp-dashboard" → ["Task"]`) instead of reading the frame's source page. This always undercounts and often picks the wrong entity.

**For every frame you enumerate, run `grep -E 'DEMO\.\w+'` on its source HTML file** and enumerate every `DEMO.<name>` reference. The `entities[]` you write for that frame is the set of entity IDs derived from those `DEMO.<name>` matches (singular PascalCase per `conventions.md`).

Frame labels are a hint about purpose, not a substitute for grepping.

## You must read source

### Files you may read

- `source/*.html` - pages + their `DEMO.<name>` rendering patterns.
- `source/*.js` - included by HTML; same lens.
- `source/data.js` - `window.DEMO` shape (to know which `DEMO.<name>` keys are valid).
- Existing `source/prototype.json` - preserve prior `parent` / `entities` for unchanged frame IDs.

## Enumerate through your lens

A sitemap node is a place in the app's structural hierarchy. Through your lens:

- **Include**: pages (top-level + drill-down), state/overlay/substep children of pages, form sub-screens.
- **Exclude (Flow-only kinds)**: triggers, notifications, externals, decisions, starts, inputs - these aren't sitemap locations.
- **Exclude**: the storyboard - it's metadata describing the sitemap, not a node in it.

You enumerate frames + assign `parent` + assign `entities[]`. All three through this lens.

## Recipe - `parent` (sitemap nesting)

For each enumerated frame:

- **Top-level page** → `parent: null`.
- **Overlay / state / substep / drill-down page** under another → `parent: "<parentId>"`. Required for overlay/state/substep.
- **`parent` is intra-lane** (U6). If you'd cross lanes, that's a cross-lane handoff - reconciliation owns those as arrows, not your IA `parent`.

You don't have a pre-handed `lane` per frame - Subagent 4 (Flow) owns lanes. To enforce intra-lane parent, read source: if a frame's source page declares persona affinity (`<button>View as TC</button>` selected, or in a TC-folder), it's in the TC lane. The reconciliation step cross-checks your `parent` choices against Subagent 4's lane assignments - flagging cross-lane parents.

## Recipe - `entities[]` (mandatory grep)

For every frame you enumerate:

```
grep -E 'DEMO\.\w+' source/<frame.entry || sourceEntry>
```

Map each `DEMO.<name>` to its entity ID per the naming convention:

- `DEMO.applications` → `Application`
- `DEMO.references` → `Reference`
- `DEMO.inhouseTasks` → `InhouseTask`
- `DEMO.classesToAttend` → `ClassToAttend`

Order entities by first appearance in the frame. Zero entities is fine (settings tab with only a form). Multiple is fine (list page + detail-on-hover preview).

**Don't invent entities not present as `DEMO.<key>`.** If you grep `DEMO.foo` but `DEMO.foo` isn't a real array in `data.js`, that's a source bug - surface to user, don't write the entity.

## Render-verify your slice

After producing your output (and after the orchestrator has written `editor/data.js`), load the editor's **IA** view and verify:

1. The sitemap renders as a tree, not a flat list - frames with `parent` actually nest under their parent.
2. No frame is orphaned to a phantom parent (a `parent` value that doesn't exist in the inventory).
3. Each frame's entity badges/chips show the entity IDs you assigned - and a dashboard / library / feed frame is NOT showing an empty entity list when its source clearly renders records.
4. Cross-lane parents render correctly OR are surfaced as a warning (you shouldn't have any - `parent` is intra-lane).

If the tree looks wrong (orphan, missing nest, empty entities on a list page), **fix it before reporting done**. Screenshot required.

## Self-audit (run before returning)

Each item requires **evidence** - a Read / Bash / Grep / screenshot call. Don't tick implicitly.

- [ ] I read `conventions.md`.
- [ ] For every frame I enumerated, I ran `grep -E 'DEMO\.\w+'` on its source file and recorded the matches. (Bash tool call required per frame.)
- [ ] No frame's `entities[]` was assigned based on the frame's label alone - every assignment is backed by a grep finding.
- [ ] Dashboard / home / library / feed frames: I grepped their source and listed every entity for each `DEMO.<name>` found. (Empty `entities[]` on a dashboard is rare and suspicious.)
- [ ] My frame IDs follow the naming convention.
- [ ] I excluded the storyboard + Flow-only kinds from `frames[]`.
- [ ] All `parent` values are within the same lane (per source's persona affinity).
- [ ] I wrote only `id` + `label` + `parent` + `entities`.
- [ ] **Every `parent` value points to a frame that exists in my enumeration** - no orphaned nesting.
- [ ] **I rendered the IA view in the editor and confirmed the tree nests correctly, no orphans, no obviously-empty dashboard entity lists.** (Screenshot required.)

## Common blindspots

- **Dashboard with `entities: []`.** A dashboard / library / feed / overview page almost always renders one or more entity lists. If your grep returned nothing, you grepped the wrong file (maybe the storyboard not the actual dashboard) - re-check.
- **Substep parent missed.** A form's `step1`, `step2`, `step3` substeps have the form page as `parent` - not `null`. Same for tabs (`settings-tab-team` → parent `settings`).
- **Cross-lane parent leak.** A frame in `pxp` lane with `parent` pointing to a frame in `tc` lane is illegal - that's a cross-actor handoff (arrow), not nesting. Flag both lanes, set parent to a same-lane frame instead.
- **Entity name singularization wrong.** `DEMO.classesToAttend` → `ClassToAttend`, not `ClassesToAttend`. Read `conventions.md` lane/entity naming closely; common irregular plurals trip this up.
- **Inferring entity from frame label when grep finds none.** "References page" with no `DEMO.references` grep hit = a hard-coded reference list (Subagent 1 bug). Don't fabricate `entities: ["Reference"]` to fill the gap - surface to user.
- **Modal with no parent.** A `library-cmdk` modal that opens *from* the library page has `parent: "library"`. Top-level modals (none) only exist if source renders them at the app shell level.

## Don't

- Don't assign `entities[]` based on frame labels. **Grep the source.**
- Don't invent entities not in `window.DEMO`.
- Don't include the storyboard or Flow-only kinds.
- Don't set `parent` to a frame in a different lane (U6).
- Don't write `kind`, `lane`, `col`, `row`, `entry`, `hash`, `setupScript`.
