---
name: Template Design System
id: default
genre: restrained institutional product UI (neutral product, Plus Jakarta Sans, pill controls)
method: clean hand-authored CSS - sane class names, semantic markup, inline-SVG icons; self-contained single source of truth in this folder
font: Plus Jakarta Sans 300/400/500/600/700 (Google Fonts CDN)
---

# Template Design System

A clean, hand-authored design system **without any vendor
framework baggage**. Every value (colour, type scale, spacing, radii, shadows) and every component
spec is defined here directly; the CSS is written from scratch
with readable BEM-ish class names and inline-SVG icons (no icon font, no framework-prefixed utility classes, no `data-*` gating).

**If you are a chat session reusing this DS: link a page to `design-systems/default/styles.css`
(and `shells/app-shell.css` for the app shell), then compose with the class vocabulary below.
Do not invent new component classes - every pattern this DS needs already has a class here.**

**Need the newer components (data-dense / document / charts / mobile) or want the page to be
style-switchable? Link `all.css` instead of `styles.css` (plus a shell css if used). One
`<link rel="stylesheet" href="../all.css">` pulls in base tokens + every component partial +
all 8 style overlays in cascade order. Then flip the look with `<html data-theme="NAME">`.**

## Files

- `styles.css` - `:root` tokens + the 47 base component classes. Single source of truth (~50KB, no framework).
- `all.css` - aggregator. One link that `@import`s, in cascade order: `styles.css` → the three component
  partials (`components/data-dense.css`, `components/doc.css`, `components/charts.css`) → the 8 style
  overlays (`themes/*.css`). **Order is the contract** - partials come after base so their modifiers win
  equal-specificity ties; themes come last so `[data-theme="x"]` overrides win over both. Link this
  (not `styles.css`) when a page needs the new components or wants to be style-switchable.
- `components/*.css` - three component partials added on top of base (data-dense, doc, charts). Token-only,
  so the 8 styles re-skin them for free. See **Component partials** below.
- `gallery.html` - kitchen sink: every component, variant and state, organised atomically with a
  scrollspy left-nav. Colour/type render as tables (lightest→darkest); Button / Tag / Badge / Status /
  Text-fields render as **variant × state matrices** (one type at a time).
- `DESIGN.md` - this file: the reuse catalog.
- `meta.json` - machine inventory (id, version, `styles[]`, full `components[]` catalog, `templates[]`, `shells[]`).
- `shells/app-shell.{css,html}` - the Default side-menu app shell (navy gradient + wave + logo + rail).
- `shells/mobile-shell.{css,html}` - the phone shell (status bar → scrollable screen → bottom tab bar).
- `shells/marketing-shell.{css,html}` - public-site chrome (sticky `.topbar--marketing` masthead + `.footer--marketing`).
- `shells/storefront-shell.{css,html}` - e-commerce chrome (`.topbar--store` bar + cart + `.footer--store`).
- `themes/*.css` - 8 style overlays (the dark style lives inside `styles.css`). See **Styles** below.
- `templates/*.html` - 14 full page samples (see **Templates** below). These are part of the DS, NOT
  prototype/asset pages - they demonstrate composition and are linked from the gallery's Page Samples.
- `assets/` - `sidebar-grid.svg`, `logo.svg`.

## Tokens (`:root` in styles.css)

```
Ramps        --{primary|secondary|tertiary|error|success|attention|info|neutral}-{50…900}
Semantic     --primary-500 (identity) + -50 soft … per family
Surfaces     --surface --surface-default --surface-medium --surface-strong --surface-inverse
             --primary-surface --primary-surface-muted --primary-surface-subtle
Text         --fg-default #252628  --fg-muted  --fg-subtle  --fg-on-surface ; --primary-fg --primary-fg-emphasis
Border       --border-default  --tint-30 (on-navy hairlines)
Type         --display 48.16 / --text-h1 42.4 / h2 37.12 / h3 28.64 / h4 23.68 / h5 18.24 / h6 12.32
             --text-base 16 / --text-s 14.08 / --text-xs 12.32 ; headings lh 120%, body 160%
Radius       --radius-xs .. --radius-2xl ; --radius-base 8 (inputs/cards) ; --radius-pill (buttons/tags/tabs/switch)
Shadow       --shadow-xs .. --shadow-xl, --shadow-hard ; 10%-black elevation, used sparingly
Spacing      --space-3xs .. --space-3xl ; base unit 16px
```

## Styles (`<html data-theme="NAME">`)

10 looks share the one class vocabulary - each is a token remap + a few scoped `[data-theme="x"]`
component overrides (mirrors how `dark` lives in `styles.css`). Activate by setting the attribute on the
root element; `default` is the plain light style (no attribute). The dark style is built into `styles.css`;
the other 8 live in `themes/*.css` and load via `all.css`. Components inherit the new look for free because
every value references a token.

**Colour scheme + dark mode.** Every style FOLLOWS the selected colour scheme: none of them re-define the
`--primary-/--secondary-/--tertiary-` ramps (the customizer writes those on `:root`); instead each derives
its accent/brand roles from the ramp via `var(--primary-NNN)` / `color-mix()` (the glassmorphism pattern).
Each style also ships a dark variant scoped to `:root.ds-scheme-dark[data-theme="x"]` - the class the editor
toggles for a dark preview while `data-theme` stays the style name. (`default`/`dark`/`glassmorphism` were
already correct; the rest were brought in line.) All themes are pure CSS - only `glassmorphism` carries a
WebGL runtime (`themes/glassmorphism.js`); `claymorphism` is CSS-only.

| Style | Attribute | Signature technique · helper tokens |
| --- | --- | --- |
| Default | _(none)_ | Base light style - restrained institutional product UI. |
| Dark | `data-theme="dark"` | Dark scheme - remapped surfaces/text/brand roles (in `styles.css`). |
| Minimal | `data-theme="minimal"` | Maximal restraint: one accent hue, everything else neutral grey; gradient gone, hairline borders + near-flat shadows in place of elevation. |
| Pastel | `data-theme="pastel"` | Soft desaturated wash (a faint tint of the scheme hue), pastel nav surface, tinted fills with deeper-hue text; no gradients, no bold fills. |
| Glassmorphism | `data-theme="glassmorphism"` | iOS liquid-glass: translucent `backdrop-filter` panes over a gradient-mesh body + dispersion-prism edge. `--glass-bg/-faint/-strong`, `--glass-blur/-strong`, `--glass-border`, `--glass-specular`, `--glass-shadow`. |
| Claymorphism | `data-theme="claymorphism"` | Soft-UI foam: chunky remapped radii + warm-cream surfaces + dual-light clay shadow (outer drop + inner highlight); the CTA follows the scheme; buttons puff and depress on `:active`. Pure CSS (no shader). `--clay-shadow/-sm`, `--clay-inset`, `--clay-press`. |
| Neumorphism | `data-theme="neumorphism"` | Soft UI: ONE shared base colour for page + every control; depth comes only from a fixed top-left dual shadow (raised vs inset), monochrome. `--neu-base/-light/-dark`, `--neu-raise/-sm/-lg`, `--neu-inset/-sm`, `--neu-accent`. |
| Tech-minimalism | `data-theme="techminimalism"` | Frutiger-DORFic / Teenage Engineering: concrete off-white + graphite, ONE hot signal on the primary role (follows the scheme), small uppercase tracked mono labels, near-zero radii, flattened shadows. `--font-mono`. |
| Neobrutalism | `data-theme="neobrutalism"` | Editorial brutalism: uncoated-cream paper + warm dark ink, ZERO radius, 2-3px ink borders, hard zero-blur offset shadow, `:active` translate(2px,2px) press, ~6% paper grain; the primary accent fills follow the scheme (scheme block + ink border + ink shadow). `--nb-paper/-bright/-shade/-deep`, `--nb-ink/-soft`, `--nb-greige`. |
| Analog | `data-theme="analog"` | "Pastel + film": pastel base + a fixed full-viewport real monochrome film-grain overlay (baked alpha tile painted in the ink colour, `mix-blend-mode:multiply` so it reads on light paper; flips to `screen` in dark). Reusable `.grain` class; `.grain--halftone` swaps grain for a REAL amplitude-modulated halftone screen (dot size encodes tone, diagonal ramp). `--grain-opacity`, `--halftone-opacity`, `--halftone-color`. |

## Component catalog - by atomic layer

State hooks are shared: `.is-active .is-focus .is-selected .is-disabled .is-readonly .is-error .is-valid .is-sortable .is-asc/.is-desc`.

### Atoms
```
Button       .btn + --primary | --outline | --light | --outline-mono | --outline-mono-shadow
                  | --well | --text | --tertiary | --tertiary-mono ; sizes --l/--s/--xs ; --icon
             .btn-group .btn.is-active[.is-readonly] ; .btn-split .btn-split__caret
Link         .link  .link--mono  .is-disabled
Tag          .tag + --light|--outline|--secondary|--tertiary|--mono ; --sm|--xs
Badge        .badge + --light|--outline|--secondary|--tertiary|--mono|--positive|--attention|--negative
                  | --dot | --text ; --sm|--xs
Status       .status + --success|--attention|--error|--info|--disabled ; forms: --box | --icon-text
                  | --icon-only ; --sm|--xs   (filled Fluent icon via currentColor + white knockout)
Avatar       .avatar [--lg|--sm] ; .avatar-stack (overlapping + "+N")
Input        .input  .is-focus .is-error .is-valid [disabled] ; .input--pill (search/filter only)
Select       .select  .is-focus .is-error [disabled]
Textarea     .textarea  + .textarea-counter
Input affix  .input-icon[.input-icon--right] (leading/trailing SVG) ; .input-affix .input-affix__pre/__post
                  ; .stepper-btn ; .otp (segment inputs)
Checkbox     .checkbox  [.checkbox--circle] .is-error  (appearance:none + SVG check)
Radio        .radio ; .dot-select (filled dot)
Check button .check-btn .is-active   (pill choice)
Switch       .switch button.is-active  .is-readonly   (Yes/No segmented toggle)
Progress     .progress [--pending|--error|--success] .progress__fill (set width%) [.is-light]
Chip         .chip .chip__thumb .chip__close
Tooltip      .tooltip__bubble
Separator    .separator[--label|--thick] ; .separator-v[--base] (vertical)
```

### Molecules
```
Field        .field .field__label (.req for *) .field__hint .field__error .field__ok ; .field--readonly
Segmented    .segmented[--outline] button.is-active  (Day/Week/Month, Yes/No)
Tabs         .tabs + --underline | --cards | --buttons ; .tab.is-active ; .tab__count ; .tab--stacked .tab__sub
Breadcrumbs  .breadcrumbs a .sep .current ; .crumb-more (truncate) ; .breadcrumb-back
Alert        .alert + --success|--attention|--error|--info ; .alert__icon .alert__title  (title neutral, filled icon at main -500)
Toast        .toast + --success|--error|--info|--attention ; .toast__icon (filled -500) .toast__body .toast__title .toast__close
             - soft -50 tint + -700 text ; simple (icon + line) OR long (bold title + description, no icon)
Menu         .menu .menu__item
Pagination   .pagination .pagination__item[.is-active|--icon|--more] ; .pagination__info ("1 to N of M records")
```

### Organisms
```
Table        .table ; thead th[.is-sortable.is-asc/.is-desc] .sort (SVG arrow-sort) ;
             tr.is-selected ; tr.is-disabled (whole row greyed) ; .cell-title .cell-sub
DataGrid     .dg-filters (.dg-filters__search .dg-filters__row .dg-filters__chips .dg-chip[.--more]
                  .dg-filters__actions) ; .dg-bulk .dg-bulk__act[--assign|--delete|--approve|--reject|--sendback]
             .dg-legend .dg-legend__item.legend-hi/.legend-lo ; cells: .cell-navto .cell-reorder
                  .cell-range .cell-chips .dg-badge[--primary] ; wrap wide tables in .table-scroll / .scroll-x
Card         .card [--plain|--filled]
Section card .section-card .section-card__head .section-card__title .section-card__desc
             ; .kv-grid (--kv-cols:N) .kv .kv__label .kv__value
List         .list[--card|--simple] .list__item
Feed         .feed .feed__item .feed__body .feed__title .feed__desc .feed__meta
Timeline     .timeline__item + .timeline--current-pending|--future-pending|--success|--unsuccessful|--cancelled ; .timeline__icon
Wizard       .steps[.steps--vertical] .step.step--done|--current .step__badge .step__label ; .steps__line.is-done
Empty state  .blank-slate[--nodata|--noresults|--noaccess] .blank-slate__icon .blank-slate__title
Lifecycle    .lifecycle .lifecycle__row .lifecycle__callout[--attention]
```

### Overlays
```
Modal        .scrim › .modal + --sm|--md|--lg ; --centered (feedback modals) ;
             .modal__close .modal__status[ filled-disc: --question|--info (teal) · --success (green) · --stop (red)
                  | shape: --warn|--noaccess|--loading (orange) · --discard (teal) · --delete (red) ] (SVG .spinner) ;
             .modal__title .modal__sub ; .modal__head .modal__body .modal__foot[--form] .modal__actions ; .modal-row
             - 9 centered feedback variants: confirmation · action · discard · delete · stop · no-access · info · success · loading
Slideout     .scrim(justify flex-end) › .slideout + --sm|--md|--lg ; --complex (.slideout__main + .slideout__summary) ;
             .slideout__top .title-overlay .slideout__content .slideout__bottom
```

### Navigation / shell
```
Top menu     .topnav (.topnav__logo + img, .topnav__sep, .topnav__title, .topnav__items, .topnav__divider,
             .topnav__item[.is-active] + .caret, .topnav__spacer, .topnav__wave img, .topnav__logout)
             ; mobile: .topnav__burger + logo  - navy gradient horizontal bar, 64px, white items + dropdown carets
Sidebar      .sidebar (.sidebar__wave img, .sidebar__logo, .sidebar__section, .sidebar__nav, .sidebar__user)
             .nav-link.is-active  .nav-link--sub  .icon .nav-label
Sub nav      .subnav .subnav__item.is-active .subnav__count
Top bar      .topbar (holds .breadcrumbs or .title-paragraph)
App shell    .app › .sidebar + .main(.topbar + .content)  - requires shells/app-shell.css
```

**Canonical chrome roles (read this before composing any chrome).** Top bars / side rails /
footers MUST carry a canonical role class so styles AND the glass overlay bind to them - the
glass runtime keys off these names, so reusing them means glass works with zero per-page wiring:
```
.topbar    any top bar / masthead   (skins: .topbar--marketing, .topbar--store; app = plain .topbar)
.sidebar   any side rail
.footer    any footer               (skins: .footer--marketing, .footer--store)  - NOT a glass surface
.appbar / .tabbar   mobile chrome
[data-glass]   escape hatch: stamp on ANY bespoke chrome to opt it into the glass overlay
```
Do NOT invent a private chrome namespace (e.g. `.bm-topbar`, `.site-nav`): the glass overlay
will not find it and the bar renders flat under the glass style. Reuse a shell, or at minimum
put `.topbar`/`.sidebar`/`.footer` (or `[data-glass]`) on your chrome element.

### Titles & text utilities
```
.title-page | --overlay | --paragraph | --mini ; .display .h1 .h2 .h3 .h4 .h5 .h6
.text-base .text-s .text-xs ; .text-strong .text-muted .text-subtle
.page-head .row (flex row) .scroll-x .table-scroll
```

## Component partials (loaded via `all.css`)

Token-only add-ons layered on the base. Theme-agnostic - the 8 styles re-skin them automatically.
Link `all.css` (or the individual partial after `styles.css`) to use them.

### Data-dense / flat (`components/data-dense.css`)
Ultra-high-density flat tables in the Linear / Bloomberg / finance register - hairline rows, tabular
numerals, no card chrome. The density is the point.
```
Flat table   .table--flat (modifier on .table - strips card chrome, 32px rows, sticky flat header,
                  hairline row separators only) ; .table--dense (28px rows + --text-xs)
Numeric      .cell--num (right-aligned tabular nums) ; .tnum (lock tabular nums anywhere)
Delta        .cell--delta + .is-up (success) | .is-down (error)
KPI strip    .kpi-strip (hairline-divided flex row) > .kpi .kpi__label .kpi__value
                  .kpi__delta[.is-up|.is-down]
Sparkline    .spark (~72×22 inline-SVG, currentColor) [.is-up|.is-down]
Toolbar      .toolbar--dense (~36px flat filter/action bar) .toolbar__spacer
Row state    .row--selected ; .row--active (flat brand-soft wash + inset active rail)
```

### Document / boxless (`components/doc.css`)
"Boxless" editing register (Notion / Google Docs / Word): plain text until you interact - affordance on
hover, low-key underline on focus. An alternative input style over the base `.input`/`.field`/`.textarea`.
```
Boxless input   .input--bare ; .textarea--bare (border + bg drop away, focus = single underline)
Boxless field   .field--bare > .field__label (muted floating label)
Doc canvas      .doc (centred editable column) ; .doc__title (large, empty → "Untitled")
                  .doc-h1 / .doc-h2 / .doc-h3 (inline-editable boxless headings)
Content block   .doc-block (gutter affordances on hover) > .doc-block__handle (drag grip)
                  .doc-block__add (+ button) - both drawn in CSS, no icon font
Placeholders    .doc-placeholder (data-placeholder empty-state) ; .slash-hint
                  ("Type '/' for commands", shown only on empty focused block)
Rail / toolbar  .doc-rail (comments/outline, hairline left border) ; .doc-toolbar (floating format bar)
```

### Charts + hero graphics (`components/charts.css`)
STATIC, theme-able mock charts - shapes drawn with inline SVG + CSS, no JS, no runtime deps. Series
colours pull from `--series-*` so a style swap reflows the whole dashboard's palette.
```
Stat hero    .stat-hero (flagship KPI) > .stat-hero__label .stat-hero__value
                  .stat-hero__delta[.is-up|.is-down] .stat-hero__spark
Chart        .chart + --bar | --line | --area | --donut (SVG carries the class; inner
                  rect/path/polyline/circle reference --series-* + .axis/.grid/.tick) ; copy-paste
                  markup for each variant lives in the partial header
Sparkline    .sparkline (tiny axis-less inline-SVG trend) [.is-up|.is-down]
Legend       .legend > .legend__item > .legend__swatch[--1..5]
Chart card   .chart-card > __title __body __legend (titled SVG-chart wrapper)
Metric tile  .metric-tile > __label __value __trend[.is-up|.is-down] ; .bignum / .bignum__label
                  (large tabular-nums figure, usable standalone)
Tokens       --series-1..5 (lead→accent) ; --chart-grid (gridlines/ticks) ; --chart-axis (axis lines/labels)
                  - themes override these in their own :root to re-skin every chart at once
```

### Mobile shell (`shells/mobile-shell.{css,html}`)
Frames content as a phone for mobile screen samples: status bar → scrollable screen → bottom tab bar.
Theme-agnostic; depends on `styles.css` tokens.
```
Phone frame  .phone > .phone__status (status bar) + .phone__screen (scroll area) + .phone__tabbar
App bar      .appbar (sticky in-screen top bar) > .appbar__icon-btn .appbar__title[--center] .appbar__action
Tab bar      .tabbar > .tabbar__item[.is-active] > .tabbar__icon .tabbar__label
                  (active item gets a pill-backed icon)
Mobile list  .list-mobile > .list-mobile__row > __body (__title __sub) + .list-mobile__chevron
Touch helper .cell-lg (56px touch target) ; .segmented--mobile (full-width segmented control)
```

### Marketing shell (`shells/marketing-shell.{css,html}`)
Public-site chrome for landing / marketing / product-homepage builds: a sticky frosted
masthead + a multi-column footer. Token-driven; depends on `styles.css` (or `all.css`).
The masthead carries `.topbar` so it glasses for free under `data-theme="glassmorphism"`.
```
Masthead     <header class="topbar topbar--marketing"> > <nav class="shell-wrap topbar__nav">
                  .topbar__brand (logo) + .topbar__links (a…) + .topbar__cta (buttons)
Footer       <footer class="footer footer--marketing"> > .shell-wrap >
                  .footer__cols (.footer__brand + .footer__col > h4 + a…) + .footer__bar (legal row)
Container    .shell-wrap (centered max-width column; reuse for page sections too)
```

### Storefront shell (`shells/storefront-shell.{css,html}`)
E-commerce chrome: a sticky top bar (brand + category nav + search + cart) and a single-row
footer. Token-driven; depends on `styles.css` (or `all.css`). The top bar carries `.topbar`.
```
Top bar      <header class="topbar topbar--store"> > <div class="shell-wrap topbar__nav">
                  .topbar__brand + .topbar__cats (a[.is-active]) + .topbar__search (>input) + .cart-btn(.badge)
Footer       <footer class="footer footer--store"> > .shell-wrap.footer__in (brand + links)
Container    .shell-wrap (centered max-width column)
```

## Templates (page samples - `templates/`)

Full composed pages, part of the DS (linked from gallery → Page Samples). Reuse as layout blueprints.

1. `login.html` - full-bleed auth + NovaID SSO + brand masthead + marketing footer (no shell).
2. `user-profile.html` - app shell · two-pane profile card + details (uses shell).
3. `technical-logs.html` - app shell · `.dg-filters` bar + sortable `.table` + `.pagination`.
4. `dashboard.html` - app shell · secondary `.subnav` side-nav + `.feed` + `.pagination`; now also
   carries a `.stat-hero` card + `.chart` mini charts (charts partial).
5. `basic-form.html` - app shell · `.lifecycle` status bar + `.section-card` + form grid.
6. `exception.html` - 404 / 403 / 400 / session-timeout / expired / maintenance `.exception` cards (no shell).
7. `landing.html` - marketing site · masthead + hero + features + metrics + CTA band + footer (uses marketing-shell).
8. `ecommerce.html` - interactive storefront · product grid → cart `.slideout` → checkout → payment → confirmation (uses storefront-shell).
9. `density.html` - app shell · ultra-dense markets (Linear/Bloomberg register) - `.kpi-strip` +
   `.table--flat`/`--dense` + `.spark` sparklines + mini `.chart`s (data-dense + charts partials).
10. `document.html` - app shell · boxless editor (Notion/Docs register) - click-to-edit `.doc__title` /
    `.doc-block` / `.field--bare` + `.doc-rail` comments (doc partial).
11. `tables.html` - app shell · five table variations: standard, flat-dense, selectable + bulk,
    rich-cell datagrid, grouped.
12. `mobile-home.html` - mobile shell · home/feed - hero stat card + quick actions + activity list + `.tabbar`.
13. `mobile-profile.html` - mobile shell · profile header + stats + settings `.list-mobile` + `.switch` + sign-out.
14. `mobile-list.html` - mobile shell · searchable grouped `.list-mobile` rows with avatars + trailing meta + `.tabbar`.

## Design language

Vivid brand blue (`#074ECF`) for identity surfaces (the side nav, blue gradient + wave) and actions;
brand red (`#E20E10`) as the secondary CTA accent; gold (`#F5B301`) as a warm highlight; cool slate
tertiary for quiet differentiation. **Pill-shaped controls** (buttons, tags, tabs, switches use `--radius-pill`) on
**soft squared surfaces** (inputs/cards/modals 8-16px, `--radius-base`). Plus Jakarta Sans - light 300
display headers tightening to semibold 600 at small sizes; headings line-height 120%, body 160%.
Soft 10%-black elevation, used sparingly. Comfortable density: 40px inputs, 48px table headers,
16px base spacing unit. On coloured/saturated surfaces, prefer tinted backgrounds + dark text (or
darkened -600/-700 fills for white text) to hold WCAG contrast.

## Reuse rules

- Link `styles.css` first; add the shell CSS only for the shell you use - `shells/app-shell.css`
  (apps/dashboards/dense/document), `shells/mobile-shell.css` (phone screens),
  `shells/marketing-shell.css` (landing/marketing), or `shells/storefront-shell.css` (shops). The font
  (Plus Jakarta Sans) loads via a Google Fonts `@import` inside `styles.css`; pages also include the
  matching `<link>` for portability.
- **Chrome MUST be reusable, never bespoke.** Every top bar / side rail / footer either comes from a
  shell or carries a canonical role class (`.topbar`/`.sidebar`/`.footer`, see *Navigation / shell*).
  A private chrome namespace (e.g. `.bm-topbar`, `.site-nav`) is forbidden: the glass overlay binds by
  role/`.topbar`/`[data-glass]`, so private names render flat under `data-theme="glassmorphism"`. For
  one-off chrome that genuinely cannot use a shell class, stamp `[data-glass]` on it.
- Need the data-dense / document / charts components, the mobile shell, or a switchable style? Link
  `all.css` instead of `styles.css` (it `@import`s base + partials + all 8 overlays in cascade order), then
  set `<html data-theme="NAME">` to pick a style. Don't author new partial classes - the catalog covers it.
- Compose from the vocabulary above; **do not author new component classes**. Need a status pill →
  `.status`; a filter bar → `.dg-filters`; an overlay → `.modal`/`.slideout`. It already exists.
- Match the matrix conventions in the gallery when documenting: one type at a time, variant × state.
- Inline-SVG icons only (Fluent System Icons - filled for semantic status, outline for nav/utility).
  No emoji, no icon font.
- Wide tables/matrices go inside `.table-scroll`/`.scroll-x`; flex children that can overflow get
  `min-width:0`. This is what keeps the layout from getting messy at narrow widths.

> This DS is fully self-contained: every token, component class, shell, and page sample lives in
> this folder. No external source, mirror, or research directory is required to use it.
