---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-kinetic-line-accents-ui.png
    reason: Style surface UI mockup.
  - src: style-kinetic-line-accents-isolated.png
    reason: Signature surface, isolated.
---
# Kinetic line accents (style)

**Tag:** `style-kinetic-line-accents`

**Canonical references:** Tresmares Capital (Awwwards SOTD - Swiss corporate grid energized by red animated strokes) · REF Digital · Swiss-poster lineage (Müller-Brockmann diagonals) translated to motion

## Surface treatment

A disciplined Swiss/corporate grid - generous whitespace, grotesque type, hairline rules - energized by ANIMATED LINE WORK: strokes that draw themselves on scroll, diagonal dashes that sweep through the grid, rules that extend to underline arriving content. The lines are the only expressive element; everything else stays still and rational.

### Background

- Paper: `#f5f5f3` - `#ededed` warm-gray or pure `#ffffff`
- Dark variant: `#111214` with lines in the accent color

### Color

- Ink: `#1a1a1a`; muted `#6e6e6e`
- Hairline gray `#d8d8d8` for the static grid rules
- ONE accent for the kinetic lines: signal red `#e8312a` (canonical), cobalt `#1f3fff`, or safety orange `#ff5a1f`
- Accent appears ONLY as line work + tiny markers (a square bullet, an index number) - never as filled panels or button backgrounds

### Line grammar

- Stroke weight 2-4px; diagonals at consistent angle (one angle per project, 12-30°)
- Lines DRAW (stroke-dashoffset / scaleX from one end), 400-700ms, ease-out, triggered at section entry
- Underline rules extend under headlines as they arrive
- A long diagonal may cross section boundaries - the page's signature gesture, max 2-3 per page
- Data moments: lines become the chart (sparklines, allocation bars) in the same stroke vocabulary

### Type stack

- Grotesque only: Helvetica Now / Neue Haas / Suisse Int'l, 400-700
- Numerals prominent (index numbers, stats) - tabular, oversized, often outlined
- No serif, no italic accents - the lines are the warmth here

### Radius / shadow

- 0-2px radius; no shadows; depth comes from layered line crossings only

## Failure mode

Lines everywhere on every scroll tick (the page vibrates); accent color leaking into buttons and backgrounds; mixed angles per section; bouncy spring easings on what should be drafting-table precision. The reference register is an engineer's pen, not confetti.

## Best for

Investment firms, infrastructure and industrial corporates, B2B consultancies, architecture practices, annual reports - restrained-register briefs that need motion-life WITHOUT abandoning Swiss discipline. (Note for the polish gate: this style IS the licensed way to animate a restrained-register project - the lines belong to the design language, they're not bolt-on polish.)

## Pairs well with

- Shells: `shell-centered-column`, `shell-hero-stack`, `shell-bento-grid`
- Styles: `style-restrained-hairline` (host), `style-oversized-neo-grotesque` (display moments)
- Aesthetics: `aesthetic-swiss-modernist`, `aesthetic-constructivism` (heavier ideological flavor)
- Recipes: `recipe-swiss-grid` as the base bundle
