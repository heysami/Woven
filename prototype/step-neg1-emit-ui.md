---
name: step-neg1-emit-ui
description: Step -1 emission details — how to compose and emit the `<direction-options>` block. Loaded only when a Step -1 trigger has fired AND the agent is about to emit the stop-and-ask UI.
---

# Step -1 — Emit the stop-and-ask UI

Reached only when a Step -1 trigger fires (A: no DS + new prototype, B: vague/incomplete direction, C: direction-vs-audience mismatch) AND none of the four carve-outs applies. The decision logic for "should I fire?" lives in `PROTOTYPE.md` Step -1; this file is the implementation of WHAT to emit.

## The chat-native primitive — `<direction-options>`

The Woven chat ships a dedicated rich primitive for this Step — `<direction-options>` — that takes compact structured data and renders palette + typography + image natively. **The agent does NOT generate HTML, does NOT write iframe-preview files, does NOT inline `<style>` blocks.** Wrong attempts to do that (e.g. emitting `<decision-request>` with `preview=".../option-N-preview.html"`) waste tokens AND ship a broken-image iframe because sandboxed-iframe Referrer-Policy strips the project context from relative `<img src>` requests.

## Turn shape — what the agent does in order

1. **Compose the three direction picks** (shell / style / aesthetic / palette / type-family / candidate brief strings / why / trade-off / register / raster-risk flag).
2. **Pick a per-turn unique slug** for the preview files: `TURN_SLUG="$(date +%s)-$(openssl rand -hex 2)"`. The slug protects chat history — without it, a re-ask overwrites prior PNGs and old messages silently swap their preview image.
3. **Recolour the library image per option** (see *Recoloring the library image* section below) → `.prototype-options/<TURN_SLUG>/option-<N>.png`. **One PNG per option.** No preview HTML, no font CSS — the chat owns rendering.
4. **Emit ONE chat message** in the shape below, containing markdown text + a single `<direction-options>` block, with every `<image src="..."/>` carrying the slug.
5. **STOP** the turn. No detail-file reads for the picked option, no genre commit, no `<artifact>`, no TodoWrite. Wait for the user's reply.

## Emit exactly this message shape

```
I want to lock direction before drawing — taste decisions belong to you, not me.

[INCLUDE ONLY IF imageGen = missing:]
> ⚠ **No image-generation model is wired into this session.** The palette, type
> samples, and preview image below are produced **mechanically** — the recolour
> is deterministic OKLab math (`scripts/prototype-recolor.py`), the type sample
> is just the brief's candidate strings rendered in real Google Fonts, nothing
> is drawn by an LLM. Options that depend on raster imagery (photo, illustration,
> raster cutouts, pixel sprites, anime portraits) **cannot be fully realised in
> the final build** without an image-gen route — they are flagged ⚠ raster-risk
> below. Wire image-gen first, or pick a CSS/SVG-realisable option.

**What I'm reading from your brief:**
- Subject: <one line, or "unclear — please name">
- Audience: <one line, or "unclear">
- Activity: <one line, or "unclear">
- Screens I'd draw: <2–6 named views, or "unclear">

[INCLUDE ONLY IF Trigger C fired:]
**Tension I'm seeing:** <one short paragraph — e.g. "You named brutalist but the audience is six-year-olds; brutalist is high-friction at that age. Keep brutalist as a deliberate move, or swap to a kids-friendly direction?">

<direction-options id="prototype-direction" prompt="Pick a direction — palette, typography, and a recoloured library preview shown per option">

  <opt value="1" recommended>
    <label><recipe-or-combo human label, e.g. "Neo-grotesque agency portfolio"></label>
    <axes>Shell: <shell-X> · Style: <style-Y> · Aesthetic: <aesthetic-Z or none></axes>
    <vibe><one-word vibe, e.g. "confident-Swiss"></vibe>
    <why><one sentence why this is the safest pick — tied to brief tags></why>
    <palette>#bg,#surface,#fg,#muted,#border,#accent</palette>
    <display font="<Google-Fonts family name, e.g. Inter>"><real candidate display headline from brief — NOT "Lorem"></display>
    <body font="<Google-Fonts family name>"><real candidate body sentence from brief — 1–2 sentences></body>
    <image src=".prototype-options/<TURN_SLUG>/option-1.png" alt="Recoloured library reference"/>
    <badge>auto-preview · no LLM · recoloured from prototype/<picked-library>.png</badge>
  </opt>

  <opt value="2">
    <label><human label></label>
    <axes>Shell: <…> · Style: <…> · Aesthetic: <…></axes>
    <vibe><one word></vibe>
    <why>Trade-off vs Option 1: <what you gain, what you lose></why>
    <palette>#…,#…,#…,#…,#…,#…</palette>
    <display font="<family>"><display sample></display>
    <body font="<family>"><body sample></body>
    <image src=".prototype-options/<TURN_SLUG>/option-2.png" alt="Recoloured library reference"/>
    <badge>auto-preview · no LLM</badge>
  </opt>

  <opt value="3">
    [same shape — third distinct direction]
  </opt>

</direction-options>

[INCLUDE ONLY IF imageGen = wired:]
**Want real samples before you commit?** Type `1 + draft` (or `2 + draft` / `3 + draft`) into chat instead of clicking the card, and I'll spend one extra turn generating 2–3 actual mockup frames using the wired image-gen model, then re-show the option with the real samples. The direction still isn't locked until you confirm after seeing the drafts.

[INCLUDE ALWAYS as a final line:]
Don't see what you want? Type your own direction in chat — e.g. *"option 1 but in warm cream, no accent"* or *"give me a dark-mode dense dashboard instead"*.
```

After this message: **stop the turn.** The chat renders the `<direction-options>` block as `DirectionOptionsCard` (defined in `editor/app.js`) — three clickable buttons laid out in a CSS grid, each showing palette chips + display sample + body sample + recoloured image + label/axes/vibe/why/badge. The image loads via `apiUrl(src)` so project context is preserved. The first click POSTs `[decision:prototype-direction] N — <label>` as the next user message.

## The `<direction-options>` tag — element reference

Top-level attributes on `<direction-options>`:

- `id="..."` (**required**) — checkpoint identifier the chat correlates the response to. For Step -1, always use `id="prototype-direction"`.
- `prompt="..."` (optional) — header sentence shown above the three option buttons.

Per-`<opt>` attributes:

- `value="..."` (**required**) — short id the user message will carry (`1` / `2` / `3` is enough; can also be a slug like `editorial-warm`).
- `recommended` (optional, presence-only) — flags one option with a star and a "recommended" pill.

Per-`<opt>` child tags (all optional, but `<label>` is effectively required because the submitted message includes the label):

- `<label>...</label>` — short human title shown beside the value pill. Keep ≤ 80 chars.
- `<axes>...</axes>` — one line summarising shell / style / aesthetic picks, with ` · ` separators.
- `<vibe>...</vibe>` — one word.
- `<why>...</why>` — one sentence rationale (for Option 1) OR trade-off vs Option 1 (for Options 2/3).
- `<palette>#hex,#hex,#hex,#hex,#hex,#hex</palette>` — exactly 6 hex tokens, comma-separated. Order: `bg,surface,fg,muted,border,accent`. The LAST chip is rendered as the accent (highlighted ring).
- `<display font="<Google-Fonts family>">text</display>` — display sample. The chat lazy-loads the family via Google Fonts CSS link and renders the text in that family with a tasteful display weight (700–800) and tight tracking. Use a REAL candidate headline from the brief, not "Aa Bb" placeholder.
- `<body font="<Google-Fonts family>">text</body>` — body sample. Same shape as `<display>` but rendered at body size with normal weight. Use a REAL candidate body sentence from the brief.
- `<image src="..." alt="..."/>` — the per-option recoloured library preview. The chat resolves `src` via `apiUrl()`, so project context is preserved automatically. Click-to-zoom wired by default.
- `<badge>...</badge>` — short footer line, typically `auto-preview · no LLM · recoloured from prototype/<picked-library>.png`. The chat prepends an `◉` glyph in the accent colour.

What the agent does NOT need to emit:

- No `<style>` block, no CSS, no font URLs — the chat owns layout + font loading.
- No `<!doctype html>`, no `<html>`, no iframes, no preview-HTML files.
- No `<link rel="stylesheet">` — `ensureGoogleFontFamily` injects the link automatically per family.
- No image `width`/`height` — sized by CSS.

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

If a style's preferred face isn't on Google Fonts, fall back to the closest free alternative — system fallback handles non-loaded faces gracefully.

## The `◉ auto-preview · no LLM` badge

Each `<opt>` emits a `<badge>` child whose text the chat prepends with a `◉` glyph in the accent colour. The badge is honest about provenance:

- **Palette swatches** — the 6 hex tokens are committed by the agent's axis pick. The chat renders them as 24px CSS chips.
- **Type sample** — the candidate strings come from the brief; the chat's `ensureGoogleFontFamily` lazy-loads the family via a `<link>` and renders in the real face.
- **Library preview image** — `scripts/prototype-recolor.py` is pure OKLab/RBF math, no model. A deterministic colour swap of a baked reference, NOT a fresh generation.

Recommended badge text per option: `auto-preview · no LLM · recoloured from prototype/<picked-library>.png`. Under 80 chars. The `◉` glyph is added automatically; do NOT include it yourself.

## Which library image to preview per option (axis-decisiveness)

For each option, pick **one** library image — the one belonging to the **most-decisive axis** for that option. Decisiveness order: aesthetic > style > shell. The rule is "if the lower axis already carries the vibe, do not stack a higher-axis image on top of it":

- **Aesthetic named** (not *none*) → use `prototype/aesthetic-<id>-ui.png`.
- **Aesthetic is none, style is the decisive call** (oversized-neo-grotesque, dense-mono-dark, skeuomorphism, etc.) → use `prototype/style-<id>-ui.png`.
- **Aesthetic is none AND style is the conventional pairing for the shell** (mobile-app + sf-pro-ios, three-column-app + restrained-hairline) → use `prototype/shell-<id>-ui.png`.
- **Recipe was the pick** → prefer `prototype/recipe-<id>-ui.png`.
- **Subject-heavy brief** (a portfolio, brand mark, mascot is central) → swap `-ui.png` for `-isolated.png` from the same axis.

If the chosen file doesn't exist on disk (`ls prototype/<file>` to confirm before the recolor call), fall back to the next axis down. Never invent a path.

## Recoloring the library image — per-turn unique slug

For each of the three options, the agent writes ONE file before emitting the `<direction-options>` block. That's it — no preview HTML, no inline style, no font CSS.

**Critical: every Step -1 emission MUST use a per-turn unique slug in the path.** Otherwise a re-ask, redo, or new round of options overwrites the previous turn's PNGs and the old chat-history previews silently change.

**Pick the slug ONCE at the start of the turn**, before any recolor call:

```bash
TURN_SLUG="$(date +%s)-$(openssl rand -hex 2)"     # e.g. 1781067126-a3f9
mkdir -p ".prototype-options/${TURN_SLUG}"
```

Then run the recolor **once per option** into the slugged subdirectory:

```bash
python scripts/prototype-recolor.py \
    prototype/<picked-library-image>.png \
    ".prototype-options/${TURN_SLUG}/option-<N>.png" \
    --tokens "#bg,#surface,#fg,#muted,#border,#accent"
```

And reference the slugged path in each `<opt>`:

```
<image src=".prototype-options/<TURN_SLUG>/option-1.png" alt="Recoloured library reference"/>
```

The wrapper extracts the source palette in OKLab, identifies the source accent (highest chroma) and source neutrals (the rest), matches them by lightness to the option's tokens, and writes a smooth perceptual recolor. Under the hood it calls `scripts/recolor_palette.py` (Chang-et-al palette-based recoloring). Read `scripts/recolor_palette.GUIDE.md` for finer control.

The chat resolves the `src` via `apiUrl()` automatically — project-id query parameter appended at render time, so the daemon routes the image to the correct project root.

**Output path convention:** `.prototype-options/<TURN_SLUG>/option-<N>.png` at the project root. The folder is append-only across turns — old slugs stay on disk so prior chat-history messages keep rendering correctly. Don't delete old slugs unless the user explicitly asks for cleanup. If `numpy`/`pillow` aren't available (`python3 -c "import numpy, PIL"` fails), `pip install numpy pillow` first. If the recolor fails for any reason, point the `<image src=...>` at the original library reference and add a one-line `<badge>colours illustrative — original library reference shown</badge>`; never drop the visuals entirely.

**Quick verify the recoloured PNGs exist** before emitting the `<direction-options>`: `ls .prototype-options/${TURN_SLUG}/` in one Bash call is enough.

## Side-by-side compact layout when only one axis varies

The `<direction-options>` card lays out three options in a CSS grid — side-by-side is the default rendering, no manual table needed.

When only one axis varies, two things change:

1. **The `prompt="..."` attribute names the axis.** Use `prompt="Aesthetic varies — pick one (Shell + Style shared)"` or `prompt="Style varies — pick one (Shell + Aesthetic shared)"` or `prompt="Shell varies — pick one (Style + Aesthetic shared)"`.
2. **The `<axes>` and `<why>` lines collapse to the varying axis only.** No need to repeat the shared shell / style across all three options.

The palette + display + body + image inside each `<opt>` still show the full visual differentiators along the varying axis. When the three options differ on **two or three axes**, keep the full `<axes>` line spelling out all picks.

## Diversity rule for the three options

The three must differ on at least one axis — ideally the aesthetic axis (the taste call). Show genuine alternatives, e.g. `mobile-app + claymorphism + positivity-kawaii` vs `mobile-app + doodle + cottagecore` vs `mobile-app + cream-humanist + (none)`. **When Trigger C fired, one of the three MUST be the brief's stated direction and one MUST be the audience/objective-aligned alternative** — make the trade-off visible.
