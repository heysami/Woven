---
name: step-neg1-register
description: Photography + illustration register strip — adds a per-option line naming the production photo/illust style. Loaded only when composing `<direction-options>` and at least one option's direction maps to a register decisionTree entry.
---

# Step -1 — Photography + illustration register strip

Loaded only when composing the `<direction-options>` UI AND at least one option's recipe/style/aesthetic maps to a register decisionTree entry. Adds a small text line under each option's library-image preview that names the production photography or illustration style the orchestrator would pick — cheap (just a text line), no orchestrator dispatch.

## Why this exists

Recipes / aesthetics / styles that resolve to raster-photo slots (editorial, lookbook, warm-restraint, cottagecore, coastal-grandmother, cream-humanist, serif-warm-paper, etc.) and ones that resolve to illustrated raster slots (maximalism, positivity-kawaii, corporate-memphis, Y2K-memphis-loud, etc.) ship with curated photography / illustration registers the production-time orchestrators would pick. The user picking direction should see THAT pick too — but cheaply, without spawning the orchestrator.

## Sourcing — read the prebuilt indexes, never the orchestrators

```bash
# Built by scripts/build-library-indexes.py (run after editing prototype/photo-* or prototype/illust-*)
docs/research/photography-library.index.json    # decisionTree + per-entry summary for the 42 photo styles
docs/research/illustration-library.index.json   # decisionTree + per-entry summary for the 108 illust styles
```

Each index's `decisionTree` is keyed by prototype slug (`recipe-warm-restraint`, `style-cream-humanist`, `aesthetic-cottagecore`, `shell-mobile-app`, etc.) and yields `{ default: <styleId>, alternatives: [<styleId>, …] }`. For one option, resolve in this order until you find a hit:

1. `recipe-<id>` (if the option committed a recipe)
2. `aesthetic-<id>` (if aesthetic ≠ *none*)
3. `style-<id>`
4. `shell-<id>`

Take the **default** styleId from the first matched key. If no key matches the option's picks, the option doesn't ship a register strip — that's fine, omit it. Pull the one-line summary and named references from `prototype/photo-<styleId>.md` or `prototype/illust-<styleId>.md` (frontmatter + first ## header).

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

## Strip shape (inline, single short line per register)

```
Photo register · `aesop-apothecary` — warm apothecary still-life, soft daylight, ceramic textures · refs: Aesop product, Toast magazine
Illust register · `blush-cool-kids` — bold pattern flat-vector with chunky bodies and saturated palette · refs: Irene Falgueras
```

No raster image is embedded in the strip — only inline text. The chat renderer's hex / type / mention chips handle styling. If you want a colour cue, append the dominant 2–3 hex values pulled from the photo/illust .md's palette / colour-hint section to the end of the line — but don't run the recolor wrapper here; the strip is text-only and cheap.
