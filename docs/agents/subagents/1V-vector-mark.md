# Subagent 1.V.vector-mark — Asset drawer (medium: vector identity mark)

You own **ONE asset** of medium `vector-mark` — a brand logo, partner mark, monogram, or single-color silhouette that needs to scale crisply and tint via `currentColor`. **Pathway B**: you write the SVG code directly. There is no external generator call.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5. Pathway-B mediums don't use the prompt node — you write code straight into the skill node.

```
pipeline=["prompt","svg-gen"]
nodeIds: { prompt, skill, asset }
```

(The prompt node is kept for human auditability — you write a 1-sentence design intent there as documentation.)

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<1-sentence design intent — what this mark represents>",
  "skillCode": "<the full SVG as a single string>",
  "params": {
    "viewBox": "0 0 24 24",
    "tint": "currentColor" | "fixed"
  },
  "slotEditDiff": "<diff that swaps the slot's <img> for inline <svg>>"
}
```

## Recipe

### 1. Read the slot

`Read slot.file` from `slot.line − 10` to `slot.line + 10`. Identify:
- Is the slot an `<img src="…logo.svg">` reference, or a `<div>` mask-tint, or a placeholder?
- What's the surrounding component (a partner strip? a header brand block? a footer signature?)
- What size renders (header logos ≈ 32px tall; partner marks ≈ 20–24px; footer monograms ≈ 14–16px)

### 2. Read the genre row

Open [`../../../PROTOTYPE.md`](../../../PROTOTYPE.md) §"Genre playbook". The genre dictates:
- **Shape language** — Linear/Vercel marks tend toward hairline geometry; brutalist marks tend toward pure type or harsh slabs; editorial monograms lean serif-derived.
- **Stroke vs fill** — the shape-language tokens (`--stroke`, `--icon-fill`) tell you whether marks should be outline, solid, or duotone. Match the existing icon family.

### 3. Write the SVG — six required properties

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 24 24"
     fill="none" stroke="currentColor"
     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
     aria-label="<assetId>">
  <!-- paths here -->
</svg>
```

1. **`viewBox`** — `0 0 24 24` for icon-sized marks, `0 0 32 32` for header logos with detail, `0 0 64 64` for partner marks with type. Pick once; geometry follows.
2. **`fill="none"` + `stroke="currentColor"`** — for outline-family genres (Linear, Vercel). OR **`fill="currentColor"`** for solid-family (Read.cv, Material). Never mix unless the design system explicitly has a duotone mark.
3. **`stroke-width`** — match the prototype's `--stroke` token (typical: 1.4–1.6 for 24-viewBox, 1.6–1.75 for 32-viewBox). Read it from `styles.css :root`.
4. **`stroke-linecap`** — match the `--endcap` token from `styles.css` (`round` / `butt` / `square`). Default `round`.
5. **`aria-label`** — descriptive name.
6. **Paths** — built from `M / L / H / V / Q / C / Z` primitives. No `<image>`, no `<text>` (use vector paths for letterforms), no embedded raster, no scripts, no styles.

### 4. Construct the geometry

Mark geometry comes from one of three sources:

| Source | When | Approach |
|---|---|---|
| A real brand reference Subagent 1 named in the brief | "ACME Coffee logo" | Recreate the mark as you remember it — simple, blocked-out, no trademark infringement risk because it's a low-fidelity sketch. If unsure, return `error: "cannot recreate trademark without reference"`. |
| An invented brand for the prototype | "Margin", "PXP", "test-harness" | Compose from the project's initial letters in the prototype's secondary font, or build a geometric monogram (overlapping circles, intersecting strokes). Stay restrained — one shape, no flourishes. |
| An abstract identity mark | "partner mark", "footer ornament" | Pick one geometric primitive (triangle, square inscribed in circle, hex, plus-glyph) and apply the genre's shape language to it. |

### 5. Validate the SVG renders

Inline-mount the SVG into your own head: it should be a self-contained string starting with `<svg` and ending with `</svg>`. No external references. No CSS classes (so it inherits feature-page styles via `currentColor`). No `<style>` tag.

### 6. Emit the slot diff

If the slot was `<img src="…logo.svg">`, swap it for the inline SVG:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<img src=\"./assets/logos/<id>.svg\" alt=\"<…>\" class=\"<…>\">",
  "replace": "<span class=\"<…>\" aria-label=\"<…>\"><svg …>…</svg></span>"
}
```

Inline SVG inherits `currentColor` from the surrounding text color, which is what the design system wants. If the slot is a CSS `mask:` reference (icon-style), leave it as a file write to `slot.outputPath` instead — write the SVG content there via `skillCode` and `outputPath`.

## Self-audit

- [ ] My SVG has `viewBox`, no `width` / `height` (sizing comes from CSS).
- [ ] Stroke / fill uses `currentColor` so the token system tints it.
- [ ] `stroke-width` matches the prototype's `--stroke` token.
- [ ] No `<style>` tag, no embedded raster, no `<text>` element, no scripts.
- [ ] No external references (`xlink:href`, `<image href>`, `url(…)`).
- [ ] `aria-label` is set.
- [ ] If the slot was an `<img>`, I emitted a diff to inline-mount the SVG instead.
- [ ] The mark's geometry matches the genre's shape language (outline vs solid, stroke weight, endcap style).

## Don't

- Don't reproduce trademarked logos at high fidelity. Low-fi reconstructions from memory are fine for prototypes; pixel-perfect copies invite legal pushback.
- Don't write `<svg width="24" height="24">` — sizing belongs in CSS. The SVG should scale with its container.
- Don't import an icon library. You're the generator.
- Don't add gradients / filters / animations — those are decoration, and `vector-mark` is identity, not decoration.
