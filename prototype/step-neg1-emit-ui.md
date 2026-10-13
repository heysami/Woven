---
name: step-neg1-emit-ui
description: Step -1 emission details - how to compose and emit the `<direction-options>` block. Loaded only when a Step -1 trigger has fired AND the agent is about to emit the stop-and-ask UI.
---

# Step -1 - Emit the stop-and-ask UI

Reached only when a Step -1 trigger fires (A: no DS + new prototype, B: vague/incomplete direction, C: direction-vs-audience mismatch) AND none of the four carve-outs applies. The decision logic for "should I fire?" lives in `PROTOTYPE.md` Step -1; this file is the implementation of WHAT to emit.

## The chat-native primitive - `<direction-options>`

The Woven chat ships a dedicated rich primitive for this Step - `<direction-options>` - that takes compact structured data and renders palette + typography + image natively. **The agent does NOT generate HTML, does NOT write iframe-preview files, does NOT inline `<style>` blocks.** Wrong attempts to do that (e.g. emitting `<decision-request>` with `preview=".../option-N-preview.html"`) waste tokens AND ship a broken-image iframe because sandboxed-iframe Referrer-Policy strips the project context from relative `<img src>` requests.

## Turn shape - what the agent does in order

0. **Research any named real-world reference FIRST.** If the brief (or a steer reply) names a real game / film / brand / product / place as the look reference, WebSearch/WebFetch how the real thing ACTUALLY presents (dimensionality, camera, materials, layout register, palette, era) before composing options or characterizing it anywhere. Training-data recall about a named reference is banned as the sole source - it is routinely outdated or plain wrong, and a wrong rider written into an option label or ledger detail becomes the committed vision downstream. This applies to the steer menus you offer too: never offer a choice set built from recall (e.g. one that omits the reference's real presentation). Do the research silently as normal grounding work - no meta commentary about rules or traps.
1. **Compose the three direction picks** (shell / style / aesthetic / palette / type-family / candidate brief strings / why / trade-off / register / raster-risk flag).
2. **Pick a per-turn unique slug** for the preview files: `TURN_SLUG="$(date +%s)-$(openssl rand -hex 2)"`. The slug protects chat history - without it, a re-ask overwrites prior PNGs and old messages silently swap their preview image.
3. **Recolour the library image per option** (see *Recoloring the library image* section below) → `.prototype-options/<TURN_SLUG>/option-<N>.png`. **One PNG per option.** No preview HTML, no font CSS - the chat owns rendering.
4. **Emit ONE chat message** in the shape below, containing markdown text + a single `<direction-options>` block, with every `<image src="..."/>` carrying the slug.
5. **STOP** the turn. No detail-file reads for the picked option, no genre commit, no `<artifact>`, no TodoWrite. Wait for the user's reply.

## Emit exactly this message shape

```
I want to lock direction before drawing - taste decisions belong to you, not me.

[INCLUDE ONLY IF imageGen = missing:]
> ⚠ **No image-generation model is wired into this session.** The palette, type
> samples, and preview image below are produced **mechanically** - the recolour
> is deterministic OKLab math (`scripts/prototype-recolor.py`), the type sample
> is just the brief's candidate strings rendered in real Google Fonts, nothing
> is drawn by an LLM. Options that depend on raster imagery (photo, illustration,
> raster cutouts, pixel sprites, anime portraits) **cannot be fully realised in
> the final build** without an image-gen route - they are flagged ⚠ raster-risk
> below. Wire image-gen first, or pick a CSS/SVG-realisable option.

**What I'm reading from your brief:**
- Subject: <one line, or "unclear - please name">
- Audience: <one line, or "unclear">
- Activity: <one line, or "unclear">
- Screens I'd draw: <2-6 named views, or "unclear">

[INCLUDE ONLY IF Trigger C fired:]
**Tension I'm seeing:** <one short paragraph - e.g. "You named brutalist but the audience is six-year-olds; brutalist is high-friction at that age. Keep brutalist as a deliberate move, or swap to a kids-friendly direction?">

<direction-options id="prototype-direction" prompt="Pick a direction - palette, typography, and a recoloured library preview shown per option">

  <opt value="1" recommended>
    <label><recipe-or-combo human label, e.g. "Neo-grotesque agency portfolio"></label>
    <axes>Shell: <shell-X> · Style: <style-Y> · Aesthetic: <aesthetic-Z or none></axes>
    <vibe><one-word vibe, e.g. "confident-Swiss"></vibe>
    <why><one sentence why this is the safest pick - tied to brief tags></why>
    <palette>#bg,#surface,#fg,#muted,#border,#accent</palette>
    <display font="<Google-Fonts family name, e.g. Inter>"><real candidate display headline from brief - NOT "Lorem"></display>
    <body font="<Google-Fonts family name>"><real candidate body sentence from brief - 1-2 sentences></body>
    <!-- aesthetic + style + shell ALWAYS emit, in this order. When the option's aesthetic is "(none)",
         the aesthetic IMAGE still emits using the representative-fallback rule above; only the
         committed <axes> text says "(none)". -->
    <image axis="aesthetic" src=".prototype-options/<TURN_SLUG>/option-1-aesthetic.png" alt="Aesthetic · <aesthetic-Z or representative-fallback>"/>
    <image axis="style"     src=".prototype-options/<TURN_SLUG>/option-1-style.png"     alt="Style · <style-Y>"/>
    <image axis="shell"     src=".prototype-options/<TURN_SLUG>/option-1-shell.png"     alt="Shell · <shell-X>"/>
    <!-- emit photo / illust ONLY when the decisionTree hits AND the orchestrator gate is open (step-neg1-register.md) -->
    <image axis="photo"     src=".prototype-options/<TURN_SLUG>/option-1-photo.png"     alt="Photo · <photo-styleId>"/>
    <image axis="illust"    src=".prototype-options/<TURN_SLUG>/option-1-illust.png"    alt="Illust · <illust-styleId>"/>
    <badge>auto-preview · no LLM · 5 axes recoloured from design-library/</badge>
  </opt>

  <opt value="2">
    <label><human label></label>
    <axes>Shell: <…> · Style: <…> · Aesthetic: (none)</axes>
    <vibe><one word></vibe>
    <why>Trade-off vs Option 1: <what you gain, what you lose></why>
    <palette>#…,#…,#…,#…,#…,#…</palette>
    <display font="<family>"><display sample></display>
    <body font="<family>"><body sample></body>
    <!-- Aesthetic image STILL emits even when the committed aesthetic is "(none)" - uses the
         style→representative-aesthetic fallback (e.g. restrained-hairline → anti-design,
         dense-mono-dark → cassette-futurism). The image is illustrative; the build will honour
         the committed (none). -->
    <image axis="aesthetic" src=".prototype-options/<TURN_SLUG>/option-2-aesthetic.png" alt="Aesthetic · <representative-fallback-id>"/>
    <image axis="style"     src=".prototype-options/<TURN_SLUG>/option-2-style.png"     alt="Style · <style-Y>"/>
    <image axis="shell"     src=".prototype-options/<TURN_SLUG>/option-2-shell.png"     alt="Shell · <shell-X>"/>
    <!-- omit photo / illust <image> tags when the decisionTree returns no hit, the orchestrator gate is closed, or the source PNG hasn't been added to the library yet - the text register strip from step-neg1-register.md still carries that info -->
    <badge>auto-preview · no LLM · 3 axes recoloured from design-library/</badge>
  </opt>

  <opt value="3">
    [same shape - third distinct direction; emit aesthetic + style + shell always (3 images) + photo / illust when their gates open (4-5 images)]
  </opt>

</direction-options>

[INCLUDE ONLY IF imageGen = wired:]
**Want a real preview image first?** Type `1 + draft` (or `2 + draft` / `3 + draft`) into chat instead of clicking the card, and I'll spend one extra turn generating a single preview PNG with the wired image-gen model (no HTML, no source files - just the image), then re-show the option with the real preview replacing the recoloured one. The direction still isn't locked until you confirm after seeing the preview.

[INCLUDE ALWAYS as a final line:]
Don't see what you want? Type your own direction in chat - e.g. *"option 1 but in warm cream, no accent"* or *"give me a dark-mode dense dashboard instead"*.
```

After this message: **stop the turn.** The chat renders the `<direction-options>` block as `DirectionOptionsCard` (defined in `editor/app.js`) - three clickable buttons laid out in a CSS grid, each showing palette chips + display sample + body sample + a horizontal strip of axis-labelled recoloured thumbnails (one per `<image axis="...">` tag, captioned with the axis name) + label/axes/vibe/why/badge. Every image loads via `apiUrl(src)` so project context is preserved. The first click POSTs `[decision:prototype-direction] N - <label>` as the next user message.

## The `<direction-options>` tag - element reference

Top-level attributes on `<direction-options>`:

- `id="..."` (**required**) - checkpoint identifier the chat correlates the response to. For Step -1, always use `id="prototype-direction"`.
- `prompt="..."` (optional) - header sentence shown above the three option buttons.

Per-`<opt>` attributes:

- `value="..."` (**required**) - short id the user message will carry (`1` / `2` / `3` is enough; can also be a slug like `editorial-warm`).
- `recommended` (optional, presence-only) - flags one option with a star and a "recommended" pill.

Per-`<opt>` child tags (all optional, but `<label>` is effectively required because the submitted message includes the label):

- `<label>...</label>` - short human title shown beside the value pill. Keep ≤ 80 chars.
- `<axes>...</axes>` - one line summarising shell / style / aesthetic picks, with ` · ` separators.
- `<vibe>...</vibe>` - one word.
- `<why>...</why>` - one sentence rationale (for Option 1) OR trade-off vs Option 1 (for Options 2/3).
- `<palette>#hex,#hex,#hex,#hex,#hex,#hex</palette>` - exactly 6 hex tokens, comma-separated. Order: `bg,surface,fg,muted,border,accent`. The LAST chip is rendered as the accent (highlighted ring).
- `<display font="<Google-Fonts family>">text</display>` - display sample. The chat lazy-loads the family via Google Fonts CSS link and renders the text in that family with a tasteful display weight (700-800) and tight tracking. Use a REAL candidate headline from the brief, not "Aa Bb" placeholder.
- `<body font="<Google-Fonts family>">text</body>` - body sample. Same shape as `<display>` but rendered at body size with normal weight. Use a REAL candidate body sentence from the brief.
- `<image axis="aesthetic|style|shell|photo|illust" src="..." alt="..."/>` - per-axis recoloured library preview. **Emit one `<image>` tag per always-emit + registered axis** (3 to 5 per option: aesthetic + style + shell always; photo / illust only when the corresponding decisionTree hits AND the orchestrator gate is open AND the source PNG exists). The chat renders them as a horizontal strip with the axis name as caption under each thumbnail; the strip wraps to a second row when there are more than 3 cells. The `axis="..."` attribute is REQUIRED - it drives the caption and the layout order (**aesthetic · style · shell · photo · illust**, left to right, top to bottom - aesthetic and style first because they're the visually decisive pair). The chat resolves `src` via `apiUrl()`, so project context is preserved automatically. Click-to-zoom wired by default.
- `<badge>...</badge>` - short footer line, typically `auto-preview · no LLM · N axes recoloured from design-library/` where N is the actual count of `<image>` tags this option emits (3-5). The chat prepends an `◉` glyph in the accent colour.

What the agent does NOT need to emit:

- No `<style>` block, no CSS, no font URLs - the chat owns layout + font loading.
- No `<!doctype html>`, no `<html>`, no iframes, no preview-HTML files.
- No `<link rel="stylesheet">` - `ensureGoogleFontFamily` injects the link automatically per family.
- No image `width`/`height` - sized by CSS.

## Google Fonts family hints by style

Pick from this small canonical map per picked style so the rendered sample matches the genre. The agent supplies `font="<family>"` per option; the chat lazy-loads:

| Picked style | `display font=` | `body font=` |
|---|---|---|
| `oversized-neo-grotesque` | `Inter` | `Inter` |
| `restrained-hairline` | `Inter` | `Inter` |
| `bold-display` | `Inter` | `Inter` |
| `cream-humanist` | `Fraunces` | `Inter` |
| `serif-warm-paper` | `EB Garamond` | `EB Garamond` |
| `agate-broadsheet` | `Source Serif 4` | `IBM Plex Serif` |
| `web-brutalism` | `Times New Roman` (system fallback OK) | `JetBrains Mono` |
| `brutalist-raw` | `Times New Roman` | `IBM Plex Mono` |
| `dense-mono-dark` | `JetBrains Mono` | `JetBrains Mono` |
| `terminal-mono` | `JetBrains Mono` | `JetBrains Mono` |
| `material-m3` / `material-m1m2` | `Roboto` | `Roboto` |
| `sf-pro-ios` | `Inter` (closest free SF stand-in) | `Inter` |
| `pixel-bitmap` | `Press Start 2P` | `Press Start 2P` |
| `flat-design` | `Inter` | `Inter` |
| `claymorphism` | `DM Sans` | `DM Sans` |
| `aurorism` / `holographic` | `Space Grotesk` | `Inter` |
| any other / no preference | `Inter` | `Inter` |

If a style's preferred face isn't on Google Fonts, fall back to the closest free alternative - system fallback handles non-loaded faces gracefully.

## The `◉ auto-preview · no LLM` badge

Each `<opt>` emits a `<badge>` child whose text the chat prepends with a `◉` glyph in the accent colour. The badge is honest about provenance:

- **Palette swatches** - the 6 hex tokens are committed by the agent's axis pick. The chat renders them as 24px CSS chips.
- **Type sample** - the candidate strings come from the brief; the chat's `ensureGoogleFontFamily` lazy-loads the family via a `<link>` and renders in the real face.
- **Library preview images** - `scripts/prototype-recolor.py` is pure OKLab/RBF math, no model. A deterministic colour swap of baked references (one per axis), NOT a fresh generation.

Recommended badge text per option: `auto-preview · no LLM · N axes recoloured from design-library/` where N is the actual `<image>` tag count for that option (3-5: always aesthetic + style + shell; +1 each for photo / illust when those gates open). Under 80 chars. The `◉` glyph is added automatically; do NOT include it yourself.

## Which library images to preview per option - ONE image PER COMMITTED + REGISTERED AXIS

**The rule: emit one `<image axis="...">` per committed or registered axis on each option. Aesthetic and style are the visually decisive pair - they ALWAYS emit. Shell is the layout chassis (less informative at the vibe-pick stage) - it emits AFTER aesthetic + style. Never a single recipe summary image.**

The user is comparing three directions across multiple axes (aesthetic, style, shell, and - when the option's picks resolve to raster registers - photography and illustration). One merged "most-decisive" thumbnail hides what each axis contributes - the user can't tell whether they're picking that *aesthetic*, that *style*, that *shell*, that *photography register*, that *illustration register*, or some inseparable combination. Showing each axis as its own thumbnail makes the contribution legible and makes "option 1 but with option 3's aesthetic" or "option 2 but with option 1's photo register" a sayable thing.

**The five axes, in left-to-right strip order (most-decisive first):**

| Axis | When to emit | Source PNG path |
|---|---|---|
| `aesthetic` | ALWAYS. When the option's *committed* aesthetic is `(none)`, the agent still picks a **representative** aesthetic for the visual - closest-shipped fit for the option's style (see "(none)" fallback rules below). The committed `<axes>` text on the option still reads `Aesthetic: (none)`; the image is illustrative only. | `design-library/aesthetic-<id>-ui.png` |
| `style` | ALWAYS | `design-library/style-<id>-ui.png` |
| `shell` | ALWAYS | `design-library/shell-<id>-ui.png` |
| `photo` | When the option's picks resolve to a photography decisionTree hit AND the photography orchestrator is on AND `imageGen` is wired (see step-neg1-register.md gates) | `design-library/photo-<styleId>-ui.png` |
| `illust` | When the option's picks resolve to an illustration decisionTree hit AND the illustration orchestrator is on AND `imageGen` is wired (see step-neg1-register.md gates) | `design-library/illust-<styleId>-ui.png` |

### Aesthetic `(none)` fallback - which representative aesthetic to use

Many adult-pro directions (Linear, Bloomberg, Read.cv, Aesop) intentionally have no aesthetic - that's how the committed direction reads in the `<axes>` text. But the per-option thumbnail strip still ships an `<image axis="aesthetic">`, because aesthetic + style together is what the user reads to grasp the vibe - dropping the aesthetic cell when "(none)" is committed leaves a hole that makes the option harder to compare against options that DO have an aesthetic.

Pick the representative aesthetic from this style → aesthetic-id table (extend as needed; when the style isn't listed, pick the closest sibling):

| Committed style | Representative aesthetic (when option's aesthetic is `(none)`) |
|---|---|
| `restrained-hairline` | `aesthetic-anti-design` (Dieter Rams orthodoxy - "(none)" closest to zero-ornament adult-pro) |
| `oversized-neo-grotesque` | `aesthetic-swiss-modernist` (Müller-Brockmann / Vignelli - the canonical typographic register) |
| `cream-humanist` | `aesthetic-maximalism` (Gentlewoman-considered, when warmth wants a cultural anchor) |
| `serif-warm-paper-editorial` | `aesthetic-maximalism` |
| `dense-mono-dark` | `aesthetic-cassette-futurism` (CRT-phosphor adjacency - closest cultural sibling) |
| `agate-numeric-broadsheet` | `aesthetic-swiss-modernist` |
| `bold-display-marketing` | `aesthetic-bauhaus` (primary-color editorial confidence) |
| `flat-design` | `aesthetic-de-stijl-neoplasticism` (primary-color flat geometric - closest movement) |
| `material-elevation-m1m2` / `material-dynamic-m3` | `aesthetic-bauhaus` (when no era is named) |
| `sf-pro-system-ios` | `aesthetic-frutiger-aero` (consumer-warm system surface) |
| `aurorism-mesh-gradient` | `aesthetic-frutiger-aero` |
| `glassmorphism` / `liquid-glass` | `aesthetic-frutiger-aero` |
| `terminal-mono` | `aesthetic-cassette-futurism` |
| `brutalist-raw-web` | `aesthetic-web-brutalism-original` |

The representative pick is illustrative, NOT committal - when the user picks the option, the agent reads the committed `<axes>` text ("Aesthetic: (none)") and does NOT pull the representative aesthetic into the build. The recoloured representative image only helps the user feel the vibe.

**Result:** each option emits **2 to 5 `<image>` tags** depending on its picks and the orchestrator gates. The chat renders them as one horizontal strip with the axis name as caption under each thumbnail; the strip wraps to a second row when there are more than 3 cells.

**Sourcing photo / illust `styleId`.** Read [`step-neg1-register.md`](./step-neg1-register.md) for the decisionTree resolution rules (`recipe-<id>` → `aesthetic-<id>` → `style-<id>` → `shell-<id>`, take the `default`). Same `styleId` becomes the per-axis filename: photo decisionTree → `design-library/photo-<styleId>-ui.png`; illust decisionTree → `design-library/illust-<styleId>-ui.png`.

**Subject-heavy brief override** (a portfolio, brand mark, mascot is central) - swap `-ui.png` for `-isolated.png` for any axis whose library entry has an `-isolated.png` variant. Per-axis: shell rarely has isolated; style sometimes; aesthetic often; photo / illust often. Check existence first (`ls design-library/<file>`) and fall back to `-ui.png` if the isolated variant doesn't exist for that axis.

**Recipes do NOT get their own image.** When a recipe is the picked option, decompose it into its constituent shell + style + aesthetic (read by the recipe file's first lines or its `axes` tag), THEN run the same photo / illust decisionTree lookup against the decomposed picks, and emit one `<image>` tag per resulting axis. The user sees the same axes regardless of whether the agent reached them via recipe shortcut or ad-hoc composition.

**Existence check before each recolor call.** `ls design-library/<file>` to confirm the source PNG is on disk. If a per-axis image is missing entirely, skip THAT axis's `<image>` tag for THAT option only - don't fall back to an unrelated axis, don't invent a path, don't drop the whole option. Photography + illustration libraries currently ship as `.md` text-only entries; their `-ui.png` samples are added incrementally - skip the `<image axis="photo">` / `<image axis="illust">` tag when its source PNG hasn't been added yet AND let [`step-neg1-register.md`](./step-neg1-register.md)'s text-only register strip carry that information instead. A 4-image option is fine; a 3-image option is fine; zero-image option (no axis-image available at all) is the failure case where you emit no `<image>` tags and add a `<badge>library images unavailable for this combo - palette + type only</badge>`.

## Recoloring the library image - per-turn unique slug

For each of the three options, the agent writes ONE file before emitting the `<direction-options>` block. That's it - no preview HTML, no inline style, no font CSS.

**Critical: every Step -1 emission MUST use a per-turn unique slug in the path.** Otherwise a re-ask, redo, or new round of options overwrites the previous turn's PNGs and the old chat-history previews silently change.

**Pick the slug ONCE at the start of the turn**, before any recolor call:

```bash
TURN_SLUG="$(date +%s)-$(openssl rand -hex 2)"     # e.g. 1781067126-a3f9
mkdir -p ".prototype-options/${TURN_SLUG}"
```

Then run the recolor **once per axis × per option** into the slugged subdirectory. Build a per-option axis list in display order - aesthetic + style + shell always; plus photo / illust when the corresponding decisionTree returns a hit AND the orchestrator gate from step-neg1-register.md is open. The same option palette goes to every axis call - the user is comparing axes of ONE direction, so they must share tokens:

```bash
# Run for option N. Repeat for each option 1..3.
# AXES list is built per-option in display order:
#   - aesthetic: ALWAYS. If option's aesthetic == "(none)", use the representative
#                aesthetic from the style→aesthetic-id fallback table above
#                (e.g. restrained-hairline → anti-design).
#   - style:    ALWAYS.
#   - shell:    ALWAYS.
#   - photo:    if photography decisionTree hits for this option AND photo gate is open.
#   - illust:   if illustration decisionTree hits for this option AND illust gate is open.
# IDS holds the per-axis library styleId for this option, e.g.
#   aesthetic=anti-design  style=restrained-hairline  shell=two-column-app
#   photo=aesop-apothecary illust=blush-cool-kids

for AXIS in $AXES; do
  STYLE_ID="${IDS[$AXIS]}"                 # e.g. anti-design when AXIS=aesthetic + (none) fallback fired
  SRC="design-library/${AXIS}-${STYLE_ID}-ui.png"
  if [ ! -f "$SRC" ]; then continue; fi    # skip axis if PNG hasn't been added to the library yet
  python scripts/prototype-recolor.py \
      "$SRC" \
      ".prototype-options/${TURN_SLUG}/option-<N>-${AXIS}.png" \
      --tokens "#bg,#surface,#fg,#muted,#border,#accent"
done
```

Per option this produces 3-5 output PNGs:

```
.prototype-options/<TURN_SLUG>/option-1-aesthetic.png    (ALWAYS - representative fallback used when option's aesthetic is "(none)")
.prototype-options/<TURN_SLUG>/option-1-style.png        (ALWAYS)
.prototype-options/<TURN_SLUG>/option-1-shell.png        (ALWAYS)
.prototype-options/<TURN_SLUG>/option-1-photo.png        (omitted if no photo decisionTree hit or gate closed or PNG missing)
.prototype-options/<TURN_SLUG>/option-1-illust.png       (omitted if no illust decisionTree hit or gate closed or PNG missing)
```

And reference each slugged path in its own `<image axis="...">` tag inside the `<opt>`, **in display order - aesthetic + style + shell + photo + illust**:

```
<image axis="aesthetic" src=".prototype-options/<TURN_SLUG>/option-1-aesthetic.png" alt="Aesthetic · <aesthetic-id-or-fallback>"/>
<image axis="style"     src=".prototype-options/<TURN_SLUG>/option-1-style.png"     alt="Style · <style-id>"/>
<image axis="shell"     src=".prototype-options/<TURN_SLUG>/option-1-shell.png"     alt="Shell · <shell-id>"/>
<image axis="photo"     src=".prototype-options/<TURN_SLUG>/option-1-photo.png"     alt="Photo · <photo-styleId>"/>
<image axis="illust"    src=".prototype-options/<TURN_SLUG>/option-1-illust.png"    alt="Illust · <illust-styleId>"/>
```

The wrapper extracts the source palette in OKLab, identifies the source accent (highest chroma) and source neutrals (the rest), matches them by lightness to the option's tokens, and writes a smooth perceptual recolor. Under the hood it calls `scripts/recolor_palette.py` (Chang-et-al palette-based recoloring). Read `scripts/recolor_palette.GUIDE.md` for finer control.

The chat resolves the `src` via `apiUrl()` automatically - project-id query parameter appended at render time, so the daemon routes the image to the correct project root.

**Output path convention:** `.prototype-options/<TURN_SLUG>/option-<N>.png` at the project root. The folder is append-only across turns - old slugs stay on disk so prior chat-history messages keep rendering correctly. Don't delete old slugs unless the user explicitly asks for cleanup. If `numpy`/`pillow` aren't available (`python3 -c "import numpy, PIL"` fails), `pip install numpy pillow` first. If the recolor fails for any reason, point the `<image src=...>` at the original library reference and add a one-line `<badge>colours illustrative - original library reference shown</badge>`; never drop the visuals entirely.

**Quick verify the recoloured PNGs exist** before emitting the `<direction-options>`: `ls .prototype-options/${TURN_SLUG}/` in one Bash call is enough.

## Side-by-side compact layout when only one axis varies

The `<direction-options>` card lays out three options in a CSS grid - side-by-side is the default rendering, no manual table needed.

When only one axis varies, two things change:

1. **The `prompt="..."` attribute names the axis.** Use `prompt="Aesthetic varies - pick one (Shell + Style shared)"` or `prompt="Style varies - pick one (Shell + Aesthetic shared)"` or `prompt="Shell varies - pick one (Style + Aesthetic shared)"`.
2. **The `<axes>` and `<why>` lines collapse to the varying axis only.** No need to repeat the shared shell / style across all three options.

The palette + display + body + image inside each `<opt>` still show the full visual differentiators along the varying axis. When the three options differ on **two or three axes**, keep the full `<axes>` line spelling out all picks.

## Diversity rule for the three options

The three must differ on at least one axis - ideally the aesthetic axis (the taste call). Show genuine alternatives, e.g. `mobile-app + claymorphism + positivity-kawaii` vs `mobile-app + doodle + cottagecore` vs `mobile-app + cream-humanist + (none)`. **When Trigger C fired, one of the three MUST be the brief's stated direction and one MUST be the audience/objective-aligned alternative** - make the trade-off visible.
