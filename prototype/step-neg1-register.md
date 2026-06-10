---
name: step-neg1-register
description: Photography + illustration register handling — drives two surfaces per option when at least one option's direction maps to a register decisionTree entry: (1) a recoloured `<image axis="photo">` / `<image axis="illust">` thumbnail in the per-option strip when the library PNG exists, and (2) a text register strip naming the production style. Loaded together with step-neg1-emit-ui.md when composing `<direction-options>`.
---

# Step -1 — Photography + illustration register

Loaded only when composing the `<direction-options>` UI AND at least one option's recipe/style/aesthetic maps to a register decisionTree entry. This file drives **two surfaces** per option:

1. **Per-axis thumbnail** in the option's strip (`<image axis="photo">` / `<image axis="illust">`) — recoloured from `design-library/<axis>-<styleId>-ui.png` when that PNG exists. Same recolour pipeline + per-option palette as the shell / style / aesthetic axes. See [`step-neg1-emit-ui.md`](./step-neg1-emit-ui.md) §"Which library images to preview per option" for the image emission shape.
2. **Text register strip** under the per-option image area — a short line naming the styleId + a one-line summary, ALWAYS emitted when the decisionTree hits (regardless of whether the `-ui.png` for the thumbnail exists yet). The text strip is the textual fallback that carries the orchestrator's pick even when the library hasn't been populated with photo / illust sample PNGs yet.

Both surfaces share the same decisionTree resolution and the same toggle gates — they're two views of the same pick. The thumbnail is forward-compatible (skipped silently when its source PNG is missing); the text strip is always available because it reads from the `.md` frontmatter that already exists.

## Why this exists

Recipes / aesthetics / styles that resolve to raster-photo slots (editorial, lookbook, warm-restraint, cottagecore, coastal-grandmother, cream-humanist, serif-warm-paper, etc.) and ones that resolve to illustrated raster slots (maximalism, positivity-kawaii, corporate-memphis, Y2K-memphis-loud, etc.) ship with curated photography / illustration registers the production-time orchestrators would pick. The user picking direction should see THAT pick too — but cheaply, without spawning the orchestrator.

## Sourcing — read the prebuilt indexes, never the orchestrators

```bash
# Built by scripts/build-library-indexes.py (run after editing design-library/photo-* or design-library/illust-*)
docs/research/photography-library.index.json    # decisionTree + per-entry summary for the 42 photo styles
docs/research/illustration-library.index.json   # decisionTree + per-entry summary for the 108 illust styles
```

Each index's `decisionTree` is keyed by prototype slug (`recipe-warm-restraint`, `style-cream-humanist`, `aesthetic-cottagecore`, `shell-mobile-app`, etc.) and yields `{ default: <styleId>, alternatives: [<styleId>, …] }`. For one option, resolve in this order until you find a hit:

1. `recipe-<id>` (if the option committed a recipe)
2. `aesthetic-<id>` (if aesthetic ≠ *none*)
3. `style-<id>`
4. `shell-<id>`

Take the **default** styleId from the first matched key. If no key matches the option's picks, the option doesn't ship a register strip — that's fine, omit it. Pull the one-line summary and named references from `design-library/photo-<styleId>.md` or `design-library/illust-<styleId>.md` (frontmatter + first ## header).

## Toggle gate — suppress when the orchestrator is off OR image-gen is missing

The strip is dropped from every option this turn if **any one** of these is true:

1. **Image-gen missing.** The image-gen availability check returned `imageGen = missing`. Without a generation route, the photo / illust style would have nowhere to land in the final build, so showing a register would mislead the user. Drop both strips entirely; the missing-image-gen banner at the top of the UI already explains the constraint.
2. **Orchestrator manifest disabled.** `.claude/agents/photography-orchestrator.manifest.json` → `defaultEnabled: false` drops the photo strip; likewise for `.claude/agents/illustration-orchestrator.manifest.json` and the illust strip.
3. **Project-level override.** The active project's `prototype.json` → `orchestrators.photography` / `orchestrators.illustration` boolean — when present and `false`, it suppresses regardless of the manifest.

Absent fields = orchestrator default (on). Photo and illust gates are independent — image-gen missing drops BOTH; a single manifest disable drops only its own strip.

## Which strip(s) to include per option — never pile both onto every card

- The strip is a *companion* to the library-image preview, not a third visual. Add **at most one** strip per option in the common case.
- **Photo strip** when the option's direction reads as editorial / lifestyle / lookbook / warm-restraint / longform / luxury-apothecary — i.e. the photo decisionTree returns a default AND no illust hit feels primary.
- **Illust strip** when the option's direction reads as product-marketing / kids / kawaii / Y2K-memphis-loud / corporate-memphis / maximalism / character-led — i.e. the illust decisionTree returns a default AND the photo hit (if any) is secondary.
- **Both strips** only when both decisionTrees hit AND the direction genuinely uses both (an editorial site with an illustrated mascot in the masthead). When in doubt, take the photo strip.
- **No strip** when neither decisionTree has a key matching the option's picks. Restrained-hairline Linear-style and dense-mono-dark Bloomberg-style directions typically fall here — they ship without raster register, and the preview row stays clean.

## Per-axis thumbnail (when the source PNG exists)

When the photo or illust decisionTree returns a hit AND the toggle gates above are open AND `design-library/<axis>-<styleId>-ui.png` exists on disk, emit a `<image axis="photo">` / `<image axis="illust">` tag inside that option's `<opt>` block. The recolour pipeline matches the shell / style / aesthetic path exactly — same per-turn slug, same per-option palette, same wrapper script. See [`step-neg1-emit-ui.md`](./step-neg1-emit-ui.md) for the bash loop + path convention.

The library's photo / illust entries are text-first by design — many ship without a `-ui.png` sample yet. The text register strip below is the fallback that always works; the thumbnail is the upgrade that lights up as PNGs get added incrementally.

## Text register strip (inline, single short line per register — ALWAYS when decisionTree hits)

```
Photo register · `aesop-apothecary` — warm apothecary still-life, soft daylight, ceramic textures · refs: Aesop product, Toast magazine
Illust register · `blush-cool-kids` — bold pattern flat-vector with chunky bodies and saturated palette · refs: Irene Falgueras
```

No raster image is embedded in the text strip — only inline text. The chat renderer's hex / type / mention chips handle styling. If you want a colour cue, append the dominant 2–3 hex values pulled from the photo/illust .md's palette / colour-hint section to the end of the line — but don't run the recolor wrapper here; the strip is text-only and cheap. Emit the text strip ALONGSIDE the per-axis thumbnail when both fire (they reinforce each other: the thumbnail shows the *look*; the text names the *style + references*); emit the text strip alone when no `-ui.png` exists for the chosen `styleId` (forward-compatible — the strip keeps working until PNGs land).
