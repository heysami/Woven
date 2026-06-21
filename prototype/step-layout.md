# Step five - layout via primitives where geometry equals optics

You cannot tune optically. So lean entirely on primitives where the math IS the visual answer. ~95% of layout should come from these.

### Grid is the default


```css
.row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: start;
}
.row-content { min-width: 0; }   /* critical: lets 1fr actually shrink */
```



- **`auto 1fr auto`** for any row with leading + content + trailing.
- **Always `min-width: 0`** on the `1fr` cell. The single most important invisible line in CSS prototype work.
- **Tabular content uses fixed first column**: `grid-template-columns: 130px 1fr` forces every label to end at the same x.
- **`grid-template-areas`** for editorial / asymmetric layouts.

### Gap and padding have separate jobs

- **`gap`** = space *between* siblings. Establishes rhythm. Consistent within a scope.
- **`padding`** = breathing room *inside* an element. Asymmetric is fine - even correct - when responding to content shape (a pill with a leading dot has tighter left padding because the dot needs less air on its outside).

### Tabular numbers auto-align

Numbers in monospace auto-align by character width. For sans-font number columns, `font-variant-numeric: tabular-nums`. A column of `184k`, `61k`, `32k` right-aligns at the digit without any layout work.

### Reach for primitives before `position: absolute`

If you reach for `absolute`, ask once whether `grid-template-areas`, grid spans, or flex with `gap` does it. ~80% of the time, yes. Reserve `absolute` for genuine overlays (modals, tooltips, badges, glass control panels).
