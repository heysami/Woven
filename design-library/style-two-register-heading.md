---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-two-register-heading-ui.png
    reason: Style surface UI mockup.
  - src: style-two-register-heading-isolated.png
    reason: Signature surface, isolated.
---
# Two-register heading (style)

**Tag:** `style-two-register-heading`

**Canonical references:** Japanese corporate/recruit site canon (small condensed Latin eyebrow over large native-script heading, shipped as one component) · kome inc. (vertical accent-color micro-labels pinned to section corners) · KAI Group design dept. (dual-script token systems with per-class optical trims)

## Surface treatment

Every section heading is a TYPED PAIR treated as one component: a small,
condensed, letter-spaced eyebrow line in a label register (often caps, often a
second script or the accent color) locked above or beside the large main
heading in the content register. The secondary register also appears as
rotated/vertical micro-labels pinned to section corners — persistent
wayfinding furniture. This is the language-agnostic abstraction of the
Japanese bilingual heading system (EN eyebrow + JP heading): any
label-script/display-script combination works — condensed caps over serif
display, mono over grotesque, second-language over first.

### The grammar

- The pair is ONE component with fixed internal spacing (eyebrow ≈ 11–13px,
  +8–12% tracking, caps; main heading 28–64px), reused verbatim at every
  section — the repetition IS the system
- Eyebrow content is a stable label vocabulary (ABOUT / SERVICE / RECRUIT /
  NEWS or numerals 01–06), not a rewritten kicker per section
- Corner variant: the eyebrow register rotates 90° (`writing-mode:
  vertical-rl` or `transform: rotate(90deg)`) and pins to the section's
  top-left or top-right as a tiny wayfinding label in the accent color
- The two registers NEVER blend mid-line — the eyebrow is its own block;
  mixed-register single lines are a different (italic-accent) device
- Optional third element: a short rule or dot between eyebrow and heading,
  hairline weight

### Background / color

- Substrate-agnostic — the component sits on whatever the host style provides
- The eyebrow is where the accent color lives: accent eyebrow + ink heading is
  the canonical coloring; inverse (ink eyebrow, accent heading) reads louder
  and spends the accent budget faster

### Type stack

- Eyebrow: condensed grotesque, mono, or the display face's caps at small
  size — must contrast the main face in WIDTH or CONSTRUCTION, not just size
- Main heading: the host genre's display face, any script
- Both faces need matched optical alignment: trim leading so the eyebrow's
  baseline-to-heading-cap gap is constant across the site (the JP canon
  trims per-class with negative margin-block)

### Motion

Minimal and sequenced: eyebrow fades/slides in 80–120ms BEFORE the main
heading on scroll entrance — label announces, heading lands. Corner labels are
static. Nothing loops.

## Failure mode

Rewriting the eyebrow as a unique marketing kicker per section (it's a LABEL
system — stable vocabulary or it's just two lines of copy); eyebrow at body
size (the size gap carries the hierarchy: keep ≥3× between registers);
vertical corner labels that are load-bearing navigation (they're wayfinding
echo, not the nav); using three registers (eyebrow + heading + another label
axis = noise); centering the pair when the host grid is asymmetric (the pair
inherits the grid's alignment).

## Best for

Corporate and recruit sites, agency portfolios, multi-section one-pagers,
bilingual or multi-script briefs, any long stack page that needs sections to
feel SYSTEMATIZED rather than art-directed one by one.

## Pairs well with

- Shells: `shell-hero-stack` (the canonical host), `shell-two-column-app`, `shell-centered-column`
- Styles: `style-flat-design`, `style-restrained-hairline`, `style-bold-display` (any can host the pair)
- Aesthetics: `aesthetic-jp-recruit-pop` (native habitat), `aesthetic-japanese-poster-layout`, `aesthetic-swiss-modernist`
