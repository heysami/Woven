# Subagent 1.V.vector-icon - Asset drawer (medium: functional inline icon)

You own **ONE asset** of medium `vector-icon` - a functional icon (nav rail, toolbar, status indicator). **Pathway B**: you write the SVG code directly.

The difference from `vector-mark`: icons are *functional* (they label an action), marks are *identity*. Icons must match an existing family by stroke, endcap, and corner radius. Marks have more compositional freedom.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5. Same envelope as `vector-mark`.

```
pipeline=["prompt","svg-gen"]
nodeIds: { prompt, skill, asset }
```

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<1-sentence design intent - what action this icon represents>",
  "skillCode": "<the full SVG as a single string, ≤6 paths>",
  "params": { "viewBox": "0 0 24 24", "tint": "currentColor" },
  "slotEditDiff": "<diff or null>"
}
```

## Recipe

### 1. Read the slot + read the existing icon family

Critical - icons are family members. Before writing, identify the prototype's icon family:

1. `Bash: grep -E "const Icon\s*=\s*\{" slot.file` - find the local icon map if Subagent 1 used one.
2. `Read styles.css` `:root` block - capture `--stroke`, `--endcap`, `--icon-fill` tokens.
3. Pick one existing icon from the map (`Icon.search`, `Icon.menu`) and read its SVG. **Your icon must match its visual properties exactly**:
   - Same `viewBox`
   - Same `stroke-width`
   - Same `stroke-linecap` / `stroke-linejoin`
   - Same `fill` strategy (none vs currentColor)
   - Same density (number of paths, level of detail)

A `vector-icon` that doesn't match the family looks like an Inter icon dropped into a Material-Symbols app - wrong even if the geometry is correct.

### 2. Write the SVG - same shape as `vector-mark` but stricter on family conformance

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="<from existing family>"
     fill="<from existing family>"
     stroke="currentColor"
     stroke-width="<from existing family>"
     stroke-linecap="<from --endcap token>"
     stroke-linejoin="round"
     aria-label="<assetId>">
  <!-- 1-6 paths max - icons are spare -->
</svg>
```

| Rule | Why |
|---|---|
| ≤6 paths | More than that = illustration, not icon |
| One visual idea per icon | "Send" = paper plane, not "paper plane + speed lines + sparkle" |
| Stroke version: closed shapes use one path each | One `<circle>` is fine for a literal circle, but prefer `<path>` for consistency |
| No `<g transform>` nesting | Flatten the geometry; transforms make extraction fragile |
| Letterforms in icons (e.g. `A`, `T`) → vector paths, not `<text>` | Same as `vector-mark` |

### 3. Common icon recipes (consult only if helpful - geometry is not memorized)

| Icon | Approach |
|---|---|
| Search | Circle + diagonal line tail at SE quadrant |
| Menu (hamburger) | Three horizontal lines |
| Close (X) | Two diagonal lines from corner to corner |
| Settings (gear) | 8-tooth gear (octagon outline + inner circle) or single slider triplet |
| Bell | Bell silhouette + small circle hanger + flat line under bell |
| Calendar | Rounded rect + two top tabs (binders) + optional horizontal divider |
| Arrow (right) | Horizontal line + chevron at end |
| Plus | Horizontal + vertical line crossing at center |
| Check | Two-segment polyline, short-then-long |

### 4. Emit slot diff (if needed)

If the slot is `<img src="./assets/icons/foo.svg">`, swap to inline SVG (so `currentColor` works):

```jsonc
"slotEditDiff": { "file": "...", "find": "...", "replace": "<inline SVG span>" }
```

If the slot is already a CSS `mask:` reference, write the SVG to `slot.outputPath` and emit no diff.

## Self-audit

- [ ] I read the existing icon family in `slot.file` (or other source files) and matched its `viewBox`, `stroke-width`, `stroke-linecap`, `fill` strategy.
- [ ] ≤6 paths. One visual idea.
- [ ] `currentColor` for tint.
- [ ] No `<style>`, no scripts, no external refs, no `<g transform>` nesting.
- [ ] `aria-label` is set and matches the action verb (`"search"`, not `"magnifying glass"`).
- [ ] If the slot was a CSS `mask:`, I wrote to `slot.outputPath` instead of swapping to inline.

## Don't

- Don't import / reference Lucide / Heroicons / Phosphor. You're the generator.
- Don't draw "an icon for X" without first reading two existing icons in the family. Family conformance is the whole job.
- Don't combine multiple concepts in one icon. If the action is compound ("export to PDF"), the surrounding text labels it; the icon picks one concept (export = arrow-out-of-box).
- Don't use `<text>` for letterforms. Convert to path geometry.
