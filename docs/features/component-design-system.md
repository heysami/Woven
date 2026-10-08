# Component design systems in Woven

Status: plan. Nothing built. First real project: suss-cal, see [suss-cal-component-ds-plan.md](suss-cal-component-ds-plan.md).

## In short

Today, an agent reads a design system's docs and then writes every page by hand. Hand-writing is where drift comes from. This feature adds a second kind of design system to Woven: a **library of blocks**. Each block is real code (markup, CSS, behavior, rules) sharing the same token variables. Agents build pages by **placing blocks from a catalog**, never by writing the markup themselves. Every rule of the system is either code the agent calls or a check that runs.

Any Woven project can choose it. suss-cal is the test case, because it is a real project with real drift: about half its pages are built in JS, and the same behaviors are rewritten in many files.

## Two kinds, chosen per design system

| | Document DS (today, stays the default) | Component DS (new) |
|---|---|---|
| Agent reads | DESIGN.md, then greps the gallery for markup | a catalog, one line per block |
| Agent writes | full HTML with DS classes | blocks plus props plus content |
| Drift caught by | lint, guardian subagent, Jev (after the fact) | checker in a hook (same turn, deterministic) |
| Block update | every page must be re-edited | every page picks it up on reload |
| Best for | marketing, expressive work, early exploration | product UI, client DS fidelity, multi-page apps |

`meta.json` gets `kind: "document" | "component"`. If `kind` is missing, the DS is a document DS, so existing projects are unaffected.

## The whole system, not just components

| Layer | Becomes code as | Checked by |
|---|---|---|
| Tokens (color, space, radius, type, motion, z-index) | one `tokens.css` | no raw values in pages or blocks |
| Layout (spacing rhythm, grid, density) | layout blocks that only take token steps: `stack`, `cluster`, `grid` | no free margins, padding or px |
| Typography | roles, not sizes: `<ds-text role="title-page">` | no font-size or weight in pages |
| Components | block folders | schema plus "replaces" list |
| Behaviors (sort, filter, paginate, open/close, validate, upload) | inside the block, written once | no per-page copies |
| Patterns (data-grid page, detail page, form section, wizard) | pattern blocks built from blocks | page uses the pattern, not loose parts |
| Shells (app frame, navigation) | shell blocks | one shell per page |
| Shared functions (toast, overlays, icons, date and money formats, title case) | services | no page-level re-implementations |
| States and a11y | shipped inside each block | required states present |
| Content rules (casing, label length, fixed copy) | prop constraints in the schema | prop value rules |

## Structure

```
design-systems/<id>/
  meta.json               kind: "component"
  tokens/tokens.css       single source of every variable
  foundations/            base, typography roles, layout blocks
  components/<name>/      one folder per block
    component.json        props, variants, slots, events, contains, replaces, usage rules
    template.html         its markup
    style.css             its CSS only, token variables only
    behavior.js           optional: its interaction (delegated, survives re-renders)
    examples.json         what the gallery shows
  patterns/<name>/        same shape, built from blocks
  shells/<name>/          same shape, page frames and navigation
  services/               toast, overlay, float positioning, icons, formats, validation
  themes/                 token overrides only (dark, styles)
  build/                  GENERATED: ds-runtime.js, ds.css, CATALOG.md, gallery.html
  DESIGN.md               principles plus rules that cannot be code
```

## How blocks connect

| Shared thing | How |
|---|---|
| Look | blocks use token variables only; a theme or brand is a token override |
| CSS order | one generated stylesheet: tokens, foundations, blocks (contained blocks first), themes; specificity works as in any hand-written file |
| Parent styling a child | the parent owns the rule and declares `contains: [...]` |
| Blocks talking to each other | attributes plus events: `<ds-filter-chip for="apps">` filters `<ds-data-grid id="apps">`, and the grid emits `ds:sort`, `ds:page`, `ds:select` |
| Shared functions | services: `DS.toast()`, `DS.overlay.open()`, `DS.icon()`, `DS.format.date()` |
| Data | grids and lists take `columns` and `rows` from JS; a column `type` picks the block and formatter |

## How a page uses blocks

- **Static HTML:** `<ds-button variant="outline">Edit</ds-button>`.
- **JS-built UI:** `DS.html("button", { variant: "outline", label: "Edit" })` returns the final markup string. `<ds-*>` tags inserted later through `innerHTML` are also expanded before the next paint.
- **Blocks expand into plain DS markup.** At load, a tag is replaced by exactly the markup the block's template defines, plus a `data-ds` marker. No wrapper elements are left behind, so CSS child selectors, `:has()`, frame setupScripts, comments, Figma export and QA all work on the real markup.
- **Editor save-back** (selection tool, annotate, draft mode): elements carrying `data-ds` collapse back into their `<ds-*>` tag, so files keep the short form.
- **Escape hatch:** `<ds-custom reason="...">` holds raw HTML (token-only). It is counted per page, and repeated reasons surface as candidates for a new block.

## Enforcement

- **`ds_check.py`** (stdlib, Python 3.9) checks page source:
  - unknown block, prop or enum value
  - missing required prop
  - slot child the parent's schema doesn't allow
  - raw markup a block replaces (`<select>`, `<button>`, `<table>`)
  - a DS class used on hand-written markup
  - page CSS touching DS classes
  - `ds-custom` without a reason
- **Runtime self-check (dev mode):** any element in the live page that carries a DS class but no `data-ds` was hand-built. The runtime logs it to the console, and `/__qa/run` collects it. This catches markup built in JS, which a source linter cannot see.
- **Hook:** runs `ds_check` after every page write on a component-DS project, so errors return in the same turn. On codex and opencode, which have no hooks, the preamble tells the agent to run it, and the qa gate runs it regardless.
- **On a DS change:** check every page to find which ones the change breaks.

## What the agent sees

For a component DS, the preamble embeds `CATALOG.md` instead of DESIGN.md:

```
<ds-filter-chip label! for field options:list size:m|s>  Table filter trigger. Not for form fields (ds-select). Replaces <select>.
<ds-data-grid id! columns! rows sortable filterable page-size bulk>  Filter + search + table + pagination pattern.
```

It comes with three rules: place blocks only; raw HTML only inside `ds-custom`; never style a DS class. The catalog is about one line per block, so it is far smaller than the DESIGN.md files it replaces (suss: 97k characters).

## Woven changes

| Area | Change |
|---|---|
| `meta.json` | `kind` field |
| `capabilities._resolve_ds_binding` | return `kind` |
| `capabilities._design_system_catalog` / `_ds_guard_stub` | for `kind: component`, embed the catalog and the checker rules instead of DESIGN.md and the guardian |
| New `editor/tools/ds/` | the generator (blocks to `build/`), the runtime source, and `ds_check.py` |
| Hook | `ds_check` after page writes, in the spawn settings |
| Selection, annotate, draft mode save-back | collapse `data-ds` elements to tags |
| `data-th-patch` replay | fingerprint the block plus its prop, not its insides |
| DS creation wizard | choose the kind: "Guidelines" or "Components" |
| DS canvas node | block list, generated gallery, `ds-custom` count and promotion candidates |
| "Convert to component DS" action | runs the conversion pipeline (below) on any existing document DS |
| `serve.py:_ds_trio_version` and the global DS library | hash and copy `components/`, `patterns/`, `shells/`, `services/` |
| `editor/default-design-system/` | ships a component version as the starter |

## Converting an existing DS (generic pipeline, proven on suss-cal first)

1. **Clean:** fix token-name drift between the docs and the CSS, undefined tokens, literals, and gallery gaps.
2. **Split the CSS into blocks:** each rule goes to the block that owns it, and parent-context rules go to the parent. The result must be pixel-identical before and after.
3. **Templates and schemas:** seeded from `ds_contract.py` (parts, variants), the gallery's sections (markup) and DESIGN.md (usage rules).
4. **Behaviors:** find the copies scattered across the project's pages and JS, show how they differ, let the user approve one canonical version, then move it into the block.
5. **Patterns and shells:** taken from how the project's pages actually combine blocks.
6. **Convert pages:** static pages to tags, and JS builders to `DS.html`. Each page must screenshot-match the original.

## Status (2026-10-08)

Shipped in Woven:
- `editor/tools/ds/`: `build_ds.py` (generator), `ds_check.py` + `ds_page.py` + `ds_model.py` (checker and validator), `runtime/ds-runtime.src.js` (runtime), and a worked fixture at `fixtures/mini-project/`.
- Preamble: `capabilities._resolve_ds_binding` returns `kind`. For a component DS, agents get the block catalog (always embedded, even with the DS check off) and the deterministic guard instead of DESIGN.md and the ds-guardian subagent.
- Hook: `.claude/hooks/ds-check-on-write.py` (PostToolUse, registered in `serve.py:_ensure_harness_settings`). A page write runs `ds_check`, and errors return in the same turn. A block source edit rebuilds `build/`. The per-thread "Checks" toggle stamps `TH_DS_GUARD=0`.
- Editor save-back: `pickSerializeClean` collapses blocks to `<ds-*>` tags through the page's `DS.serialize`.
- `/__design_systems` reports `kind`, and the single-DS endpoint serves component DSes (their stylesheet is `build/ds.css`). The generator mirrors the gallery to the DS root so every existing DS surface opens it.
- Tests: `editor/tests/test_component_ds.py` and `editor/tests/test-component-ds-runtime.cjs` (Playwright).

Not yet:
- DS creation wizard kind choice, DS node block list, the "Convert to component DS" action.
- Visual-editor insert (`edit-components.js` reads gallery samples and would insert expanded markup; for a component DS it must insert `<ds-*>` tags).
- Global DS pull for a component DS (pull rewrites the document trio; it should copy the folders and rebuild).
- `data-th-patch` fingerprints that target a block plus its prop.

## Rollout

1. Build the Woven tooling: generator, runtime, checker, preamble branch, hook, save-back collapse.
2. Pilot on a copy of suss-cal ([plan](suss-cal-component-ds-plan.md)).
3. Turn what the pilot needed into the generic "Convert" action.
4. Make the default starter DS a component DS, and add the wizard choice.
5. Instance UX: a props panel when a block is selected on a page, and one-click "promote this ds-custom to a block".

## Risks

- **A thin catalog means everything ends up in `ds-custom`.** The `ds-custom` count is the early warning.
- **Block API design is the real work.** Bad props push agents to fork. Missing variants must be added to the DS, never forked in a page.
- **Pages need JS** for blocks to expand. A no-JS prerender for publish can come later.
- **Save-back collapse** (slots, nested blocks) needs fixture tests first.
- **Exploration feels stricter.** That is why the document kind stays the default.
