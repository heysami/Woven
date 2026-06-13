---
name: Default Design System
id: default
genre: restrained institutional product UI (neutral product, Plus Jakarta Sans, pill controls)
method: clean hand-authored CSS — sane class names, semantic markup, inline-SVG icons; self-contained single source of truth in this folder
font: Plus Jakarta Sans 300/400/500/600/700 (Google Fonts CDN)
brand:
  brand-blue: "#074ECF"
  brand-red: "#E20E10"
  brand-grey: "#DADFE8"
  brand-gold: "#F5B301"
  brand-sky: "#7FB9EE"
interaction-blue: "#074ECF"
---

# Default Design System

A clean, hand-authored design system **without any vendor
framework baggage**. Every value (colour, type scale, spacing, radii, shadows) and every component
spec is defined here directly; the CSS is written from scratch
with readable BEM-ish class names and inline-SVG icons (no icon font, no framework-prefixed utility classes, no `data-*` gating).

**If you are a chat session reusing this DS: link a page to `design-systems/default/styles.css`
(and `shells/app-shell.css` for the app shell), then compose with the class vocabulary below.
Do not invent new component classes — every pattern this DS needs already has a class here.**

## Files

- `styles.css` — `:root` tokens + every component class. Single source of truth (~50KB, no framework).
- `gallery.html` — kitchen sink: every component, variant and state, organised atomically with a
  scrollspy left-nav. Colour/type render as tables (lightest→darkest); Button / Tag / Badge / Status /
  Text-fields render as **variant × state matrices** (one type at a time).
- `DESIGN.md` — this file: the reuse catalog.
- `meta.json` — machine inventory (id, version, full `components[]` catalog, `templates[]`, `shells[]`).
- `shells/app-shell.{css,html}` — the Default side-menu app shell (navy gradient + wave + logo + rail).
- `templates/*.html` — 6 full page samples (see **Templates** below). These are part of the DS, NOT
  prototype/asset pages — they demonstrate composition and are linked from the gallery's Page Samples.
- `assets/` — `sidebar-grid.svg`, `logo.svg`.

## Tokens (`:root` in styles.css)

```
Brand        --brand-blue #074ECF  --brand-red #E20E10  --brand-grey #DADFE8  --brand-gold #F5B301  --brand-sky #7FB9EE
Ramps        --{primary|secondary|tertiary|error|success|attention|info|neutral}-{50…900}
Semantic     --primary-500 (brand blue #074ECF) + -50 soft … per family
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

## Component catalog — by atomic layer

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
             — soft -50 tint + -700 text ; simple (icon + line) OR long (bold title + description, no icon)
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
             — 9 centered feedback variants: confirmation · action · discard · delete · stop · no-access · info · success · loading
Slideout     .scrim(justify flex-end) › .slideout + --sm|--md|--lg ; --complex (.slideout__main + .slideout__summary) ;
             .slideout__top .title-overlay .slideout__content .slideout__bottom
```

### Navigation / shell
```
Top menu     .topnav (.topnav__logo + img, .topnav__sep, .topnav__title, .topnav__items, .topnav__divider,
             .topnav__item[.is-active] + .caret, .topnav__spacer, .topnav__wave img, .topnav__logout)
             ; mobile: .topnav__burger + logo  — navy gradient horizontal bar, 64px, white items + dropdown carets
Sidebar      .sidebar (.sidebar__wave img, .sidebar__logo, .sidebar__section, .sidebar__nav, .sidebar__user)
             .nav-link.is-active  .nav-link--sub  .icon .nav-label
Sub nav      .subnav .subnav__item.is-active .subnav__count
Top bar      .topbar (holds .breadcrumbs or .title-paragraph)
App shell    .app › .sidebar + .main(.topbar + .content)  — requires shells/app-shell.css
```

### Titles & text utilities
```
.title-page | --overlay | --paragraph | --mini ; .display .h1 .h2 .h3 .h4 .h5 .h6
.text-base .text-s .text-xs ; .text-strong .text-muted .text-subtle
.page-head .row (flex row) .scroll-x .table-scroll
```

## Templates (page samples — `templates/`)

Full composed pages, part of the DS (linked from gallery → Page Samples). Reuse as layout blueprints.

1. `login.html` — full-bleed auth + NovaID SSO + brand masthead + marketing footer (no shell).
2. `user-profile.html` — app shell · two-pane profile card + details (uses shell).
3. `technical-logs.html` — app shell · `.dg-filters` bar + sortable `.table` + `.pagination`.
4. `dashboard.html` — app shell · secondary `.subnav` side-nav + `.feed` + `.pagination`.
5. `basic-form.html` — app shell · `.lifecycle` status bar + `.section-card` + form grid.
6. `exception.html` — 404 / 403 / 400 / session-timeout / expired / maintenance `.exception` cards (no shell).

## Design language

Vivid brand blue (`#074ECF`) for identity surfaces (the side nav, blue gradient + wave) and actions;
brand red (`#E20E10`) as the secondary CTA accent; gold (`#F5B301`) as a warm highlight; cool slate
tertiary for quiet differentiation. **Pill-shaped controls** (buttons, tags, tabs, switches use `--radius-pill`) on
**soft squared surfaces** (inputs/cards/modals 8–16px, `--radius-base`). Plus Jakarta Sans — light 300
display headers tightening to semibold 600 at small sizes; headings line-height 120%, body 160%.
Soft 10%-black elevation, used sparingly. Comfortable density: 40px inputs, 48px table headers,
16px base spacing unit. On coloured/saturated surfaces, prefer tinted backgrounds + dark text (or
darkened -600/-700 fills for white text) to hold WCAG contrast.

## Reuse rules

- Link `styles.css` first; add `shells/app-shell.css` only for shell pages. The font (Plus Jakarta Sans)
  loads via a Google Fonts `@import` inside `styles.css`; pages also include the matching `<link>` for portability.
- Compose from the vocabulary above; **do not author new component classes**. Need a status pill →
  `.status`; a filter bar → `.dg-filters`; an overlay → `.modal`/`.slideout`. It already exists.
- Match the matrix conventions in the gallery when documenting: one type at a time, variant × state.
- Inline-SVG icons only (Fluent System Icons — filled for semantic status, outline for nav/utility).
  No emoji, no icon font.
- Wide tables/matrices go inside `.table-scroll`/`.scroll-x`; flex children that can overflow get
  `min-width:0`. This is what keeps the layout from getting messy at narrow widths.

> This DS is fully self-contained: every token, component class, shell, and page sample lives in
> this folder. No external source, mirror, or research directory is required to use it.
