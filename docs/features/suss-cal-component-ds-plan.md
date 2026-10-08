# Pilot: suss-cal on a component design system

Status: plan. Nothing built.

This is the first real project for the Woven feature in [component-design-system.md](component-design-system.md). The Woven-wide pieces (structure, runtime, checker, editor changes) live in that doc. This doc covers only what suss-cal needs, and what it should teach us before the "Convert to component DS" action is generalized for every project.

## In one paragraph

Duplicate suss-cal. In the copy, turn the `suss` design system from "CSS plus docs the AI reads" into a library of blocks. Each block is its own folder holding its markup, its CSS, its behavior and its rules, and all blocks share the same token variables. Pages stop hand-writing markup and place blocks instead: `<ds-filter-chip>` in HTML, `DS.html("filter-chip", {...})` in JS. Done means every page looks the same as the original, with zero hand-built DS markup left.

## What we found

- **The DS is CSS only:** 57 components, 266 tokens, no behavior code.
- **62 product pages:** 22 static, 9 hybrid and 31 built entirely in JS by string concatenation plus `innerHTML`. Converting the HTML alone would miss half of the UI.
- **The same behavior is rewritten over and over:**
  - `toast()` in 14 files
  - dropdown, chip and multi-select open/close in about 14 to 16 files each
  - table sorting in about 26 places
  - the pager in 6 files
  - modal and slideout open/close on each page
  - validators on each page
- **An unofficial library already exists.** `fa-form.js` builds field, select, kv and card markup as strings, and 26 pages use it.
- **Drift today:**
  - 4466 lines of page `<style>` and 2310 inline styles
  - ds_lint reports 178 findings, including 68 invented components (sp-card, auth-card, doc-table and others)
  - ds_lint cannot see markup built in JS
- **styles.css is tangled:**
  - 33 components are split across several sections (`btn` is in 7)
  - 161 selectors cross components
  - 37 `:has()` rules
- **Editor features depend on today's markup:**
  - 68 frame setupScripts click DS selectors
  - 48 comments are anchored by structural CSS paths
  - 2 pages carry `data-th-patch` replay scripts

## Key design choice: blocks expand into the SAME markup

`<ds-button variant="outline">Edit</ds-button>` is replaced at load by exactly the markup the DS uses today: `<button class="btn btn--outline" data-ds="button">Edit</button>`. The final page has no extra wrapper elements, so everything that relies on today's markup keeps working unchanged: DS CSS (child selectors, `:has()`), the 68 setupScripts, comments, Figma export and QA.

- **Static HTML:** the runtime expands every `<ds-*>` tag at load. The page stays hidden until that finishes, which takes about one frame.
- **JS-built UI:** builders call `DS.html("button", props)`, which returns the final markup string. Any `<ds-*>` tag inserted later through `innerHTML` is also expanded, by an observer that runs before the next paint.
- **Saving from the editor** (selection tool, draft mode): elements carrying `data-ds` are collapsed back into their `<ds-*>` tag, so the files keep the short form.

## The new structure

```
design-systems/suss/        converted in place inside the copy (same id, page links keep working)
  meta.json                 kind: "component"
  tokens/tokens.css         the 266 tokens, cleaned, the single source
  foundations/              base, typography roles, layout blocks (stack, cluster, grid, kv-grid)
  components/<name>/        one folder per block
    component.json          props, variants, slots, events, tokens used,
                            usage rules ("use for", "not for", raw elements it replaces)
    template.html           its markup
    style.css               its CSS only, token variables only
    behavior.js             optional: its interaction (one delegated listener, survives re-renders)
    examples.json           the cases the gallery shows
  patterns/<name>/          same shape, built FROM components: data-grid, detail header,
                            form section, decision slideout, wizard, empty states, exception page
  shells/<name>/            admin (absorbs admin-nav.js), applicant (topnav + portal rail), auth
  services/                 shared code every block uses: toast, overlay (open/close, scrim,
                            motion, z-index), float positioning, icons, formats (date "1 Jun 2026",
                            money), title case, validation
  build/                    GENERATED: ds-runtime.js, ds.css, CATALOG.md, gallery.html
  DESIGN.md                 shrinks to principles plus the rules that cannot be code
```

### How blocks connect

| Shared thing | How |
|---|---|
| Look | Every `style.css` uses token variables only, from one `tokens.css`. A brand change is a token change. |
| CSS order | `@layer tokens, base, atoms, molecules, organisms, patterns, shells`. This ends the "later rule overrides earlier rule" fights (for example `.badge` set to 26px, then 20px further down the file). |
| Parent styling a child | The parent owns the rule. `.modal__actions .btn` lives in the modal's CSS, and modal's `component.json` declares `contains: [button]`. |
| Blocks talking to each other | Through attributes and events. `<ds-filter-chip for="apps" field="status">` filters `<ds-data-grid id="apps">`. The grid emits `ds:sort`, `ds:page` and `ds:select`, and page JS listens to the same events. |
| Common functions | Services: `DS.toast()`, `DS.overlay.open()`, `DS.format.date()`, `DS.icon()`. Each is written once and used by every block. |
| Data | Grids and lists take `columns` and `rows` from JS. Fixtures like `FA_APPS` stay as they are. A column `type` (status, date, money, link, actions) picks the right block and formatter. |

## Steps

### 0. Duplicate
Use the existing Duplicate action on the projects screen to create `suss-cal-lib`. The original stays untouched as the comparison baseline.

### 1. Clean the DS first (in the copy)
- **DESIGN.md token table:** it uses names that don't exist (`--primary-500`, `--text-h1`, and so on). Fix them to the real names.
- **Tokens in the CSS:** define `--color-success-border-fg-emphasis`, which is used but never defined. Move the 11 hex and rgba literals into tokens.
- **Leftovers:** `app-shell.html` still uses the removed `.tag`. `.flowsteps` is named in meta but missing from the CSS.
- **Gallery gaps:** add the 4 components it is missing (Lifecycle, Feed, Sub nav, Nav ask).
- **dsRef:** the 4 places that record it hold 4 different versions. Make them agree.
- **Page cleanup:** bake the 2 `data-th-patch` pages into their source, drop the 4 `__poke` probes, and delete the orphaned `components/` snippets.
- **Icons:** build the icon service on Fluent, with filled as the default and outline as an option. Map every Feather icon to its Fluent equivalent.

### 2. Split the CSS into blocks (no visual change)
A tool sorts every rule in `styles.css` and `app-shell.css` into the block that owns it, based on the subject's class. Parent-context rules go to the parent. The output is bundled in layer order.

Check: the gallery and all 62 pages must screenshot pixel-identical before and after. This is the riskiest step, so it runs alone, before anything else changes.

### 3. Write the template and rules for each block
The inputs already exist:
- `ds_contract.py` gives parts and variants for 156 entries.
- The gallery's 48 sections and 180 cells give the canonical markup.
- DESIGN.md gives the usage rules.

An agent drafts each `component.json` and template. The generated gallery must match the old one.

### 4. Move the behaviors into the DS
One canonical version of each. For each behavior, first list how its existing copies differ, then get approval before choosing the canonical version.

| Behavior | Today | Becomes |
|---|---|---|
| Toast | `toast()` in 14 files | `services/toast` |
| Dropdown, multi-select, filter chip (open/close, positioning) | about 14 to 16 files each | each block's behavior, plus `services/float` |
| Table sort | about 26 places | data-grid behavior |
| Pagination | 6 files | pagination behavior |
| Bulk select | `fa-queue.js` | data-grid behavior |
| Modal, slideout, drawer, plus motion | each page, plus `overlay-motion.js` | `services/overlay` |
| Date picker | `datepicker.js` (already solid) | date-picker behavior, moved as is |
| Upload, password field, tabs | various | their own blocks |
| Field validation | each page | rules in `component.json`, plus a form block |

### 5. Patterns and shells
These come from how the pages actually combine things:
- **Data-grid page:** filters, search, table, bulk select and pagination (22 static pages plus 9 built in JS).
- **Detail page:** page head, lifecycle and section cards.
- **Form section.**
- **Wizard:** replaces the 4 hand-rolled steppers.
- **Decision slideout.**
- **Exception page.**

Shells:
- **Admin** (43 pages): absorbs `admin-nav.js` and the role switch.
- **Applicant:** replaces the 15 hand-copied topnavs plus the portal rail.
- **Auth.**

### 6. Woven tooling
This is built once for every project. See "Woven changes" in [component-design-system.md](component-design-system.md). For suss-cal specifically, the runtime self-check matters most, because 31 pages build their markup in JS, where today's linter is blind.

### 7. Pilot 3 pages, then the rest
Pilot one page of each kind:
- `applicants-list` (static)
- `fa-application` (hybrid)
- `fa-monitoring` (built in JS)

A page passes when:
- it pixel-matches the original project's page
- the runtime finds zero hand-built DS markup
- its setupScripts and comments still work

Then convert the rest in waves by shell: admin, then applicant, then standalone. `fa-form.js` and its siblings first become thin wrappers over `DS.html`, then go away.

### 8. The real test
Give the agent the same brief for one new screen in both projects, the original and the copy. Count the violations in each and compare.

## Done means
- Every page visually matches the original (screenshot diff).
- The runtime finds zero hand-built DS markup, and no page redefines a DS class.
- Each behavior exists once, inside the DS.
- The agent's DS context is the catalog, an estimated 10k characters against the 97k DESIGN.md today.

## Decisions
1. **Icons (decided 2026-10-08):** Fluent only. The icon block gets `style="filled|outline"`, with filled as the default. All Feather icons (646 uses) are converted.
2. **Behaviors (decided 2026-10-08):** review each one before merging. For each behavior in step 4, list the differences between the existing copies, then get approval before choosing the canonical version.
3. **Comments (decided 2026-10-08):** ignore. The 11 open review comments are out of scope for the pilot.
4. **Off-DS pages (decided 2026-10-08):** leave them out. payment-gateway, hyperframes and mm are not converted and not checked.
