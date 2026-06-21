# Subagent 1.V.raster-foreground - Asset drawer (medium: raster foreground cutout)

You own **ONE asset** of medium `raster-foreground` - a subject that needs to composite over UI with a transparent background. The pipeline is **generate-then-cutout**: prompt the model to render the subject on a chroma-key (greenscreen) background, then post-process via `rembg` to produce a true transparent PNG with anti-aliased edges.

Pathway A for the generation step (Volcengine / OpenAI / Recraft), Pathway B is a no-op here - `rembg` does the cutout deterministically.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5. Verbatim fields plus:

```
pipeline=["prompt","image-gen","rembg"]
nodeIds: { prompt, skill, post, asset }   ← post is the rembg node
```

You may read: `slot.file`, `PROTOTYPE.md` §9 + genre row, this playbook.

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<the full prompt, ending with the chroma-key directive>",
  "params": {
    "aspect": "1:1" | "3:4" | "4:3" | …,
    "model": "gpt-image-1",
    "style": "photo" | "illustration",
    "transparent": true,
    "chromaKey": "oklch(70% 0.35 145)"
  },
  "slotEditDiff": null
}
```

## Recipe

### 1. Confirm the slot really needs cutout

A `raster-foreground` asset is one that **composites over UI** - sitting on a card, layered above text, dragged into another panel. If the slot is a full-bleed hero with nothing layered on top of it, that's `raster-photo`, not foreground. Return `error: "slot is full-bleed; medium should be raster-photo"` if you spot this.

### 2. Read the slot + genre row

Same as `raster-photo` §1-2. Add: confirm the slot's container has `position: relative` or is otherwise compositing-ready - your output relies on the transparent PNG layering correctly.

### 3. Write the prompt - seven clauses (six + chroma-key)

Same six as `raster-photo`, plus a **mandatory chroma-key clause** as the final sentence:

7. **Chroma-key directive** - verbatim: *"Subject is fully isolated on a flat, evenly-lit `<chromaKey>` background with no shadow, no ground plane, and no environmental reflection. The background must be a single solid color with sharp edges around the subject."*

`<chromaKey>` defaults to `oklch(70% 0.35 145)` (saturated lime green - far from skin / metal / common product hues). If your subject IS green (e.g. a green coffee cup, a fern), substitute `oklch(60% 0.30 30)` (saturated coral) or `oklch(70% 0.32 300)` (magenta) and record the substitution in `params.chromaKey`.

**Example (Editorial genre, partner logo cutout):**

> A cast-iron espresso machine, eye-level 50mm equivalent, subject filling the frame with breathing room. Soft three-quarter lighting from camera-left, gentle highlights along chrome, no harsh shadows. Warm neutrals - bone, graphite, oxidised brass. Visible product-photography polish, faint paper-grain texture. No people, no text, no watermarks, no logos beyond the machine's own. Subject is fully isolated on a flat, evenly-lit `oklch(70% 0.35 145)` background with no shadow, no ground plane, and no environmental reflection. The background must be a single solid color with sharp edges around the subject.

### 4. Set params

| Param | Decide by |
|---|---|
| `aspect` | Read `data-aspect`; if absent, default `1:1` (cutouts overwhelmingly want square crops). |
| `model` | Default `gpt-image-1`. |
| `style` | `"photo"` unless the genre row mandates illustration (e.g. Editorial mascot, Marketing illustration). |
| `transparent` | Always `true`. This routes the call through the cutout pipeline (rembg node executes after image-gen). |
| `chromaKey` | Default `oklch(70% 0.35 145)`. Substitute only if the subject is itself green/magenta/coral. |

### 5. Slot edit diff

Same as `raster-photo` - none unless `data-aspect` needs updating. Note: `raster-foreground` outputs are PNGs with alpha, so the slot should use `<img>` not `<div style="background-image">`. If the slot is currently `background-image:`, emit a diff to convert to `<img>`:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"hero-bg\" style=\"background-image:url(…);\">",
  "replace": "<div class=\"hero-bg\"><img src=\"<outputPath>\" alt=\"\"></div>"
}
```

Background-image doesn't preserve alpha consistently across browsers / blend modes; cutouts compositing reliably wants `<img>`.

## Self-audit

- [ ] My prompt ends with the verbatim chroma-key directive (sentence 7).
- [ ] `params.transparent` is `true`.
- [ ] `params.chromaKey` is recorded - default or substituted with reason.
- [ ] The slot composites over UI (not a full-bleed hero - that'd be `raster-photo`).
- [ ] If slot was `background-image:`, I emitted a diff to swap to `<img>`.
- [ ] No part of the prompt requests "transparent background" in plain English - the generator can't reliably honor that; the chroma-key + rembg pipeline is the actual mechanism.

## Don't

- Don't ask the model directly for "transparent background" / "alpha channel" / "PNG cutout". Generative APIs don't reliably honor that. The chroma-key + rembg chain is the workaround - trust the pipeline.
- Don't omit the chroma-key sentence. Without it, rembg cuts against a noisy real background and edges look like a 2000s magazine cutout.
- Don't pick a chroma color that overlaps the subject. Green + plant subject → magenta substitute.
- Don't request shadows / ground planes / environmental reflections - they bleed onto the cutout edge.
