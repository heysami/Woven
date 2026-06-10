---
name: step-neg1-draft
description: Step -1 +draft refinement loop — pre-commit, lightweight, single image. Loaded ONLY when the user replies with any of the +draft trigger vocabulary. Strictly forbids orchestrator dispatch and source/ writes.
---

# Step -1 — `+ draft` refinement loop (only when imageGen = wired)

Reached only when the user replies with one of the trigger phrases below. This file is the COMPLETE contract for the +draft turn — what's allowed, what's forbidden, the exact call shape, and the typography prompt-engineering table. The agent must NOT improvise beyond this.

## Trigger vocabulary — these all mean +draft, NOT "build the prototype"

The user's wording for "give me ONE quick preview image before I commit" is highly varied. Treat ALL of the following as +draft requests — pre-commit, lightweight, single image, no orchestrators, no source writes:

- `<N> + draft` / `1 + draft` (the canonical form)
- `option <N>, generate samples` / `generate mockup` / `gen the mockup` / `mockup` / `mock up`
- `generate me the mock up` / `generate mockups` / `show me a mockup`
- `generate image first` / `generate image before locking` / `image first`
- `give me a preview` / `show me a sample` / `preview this`
- `<N> but render it` / `<N> render that` / `try rendering <N>`

The shared signal is "**I want to see what this looks like as a generated image BEFORE you build anything**." That means: produce a single (or at most 2) draft PNG via direct image-gen call, embed it in a re-emitted `<direction-options>` card, then **stop and wait**. Do not start Phase A. Do not commit a genre. Do not write source files. Do not dispatch orchestrators.

If the user's wording is genuinely ambiguous (e.g. "make me the design", "let's build it"), ask one short clarifying question before acting:

> *"Do you want a quick image preview first (no source files), or should I commit the direction and build the prototype? Either is fine."*

## What +draft IS allowed to do — EXACTLY this, nothing more

ONE direct `POST` to `/__asset_generate` per draft image, using:

```bash
curl -X POST "$TH_DAEMON_URL/__asset_generate?project=$TH_PROJECT_ID" \
  -H "Content-Type: application/json" \
  --data-binary @body.json
```

where `body.json` is:

```json
{
  "skill":    "generate-image",
  "provider": "<from capabilities preamble's Image-generation USER DEFAULT row>",
  "model":    "<from same row>",
  "aspect":   "3:2",
  "output":   ".prototype-options/<TURN_SLUG>/draft-<k>.png",
  "prompt":   "<composed prompt — see step 2 below>"
}
```

That's it. ONE call per draft image, direct daemon endpoint, output writes straight to `.prototype-options/<TURN_SLUG>/`.

## What +draft is FORBIDDEN to do

- **No `Task` tool dispatches.** No `visual-orchestrator`, no `photography-orchestrator`, no `illustration-orchestrator`, no `creative-visual-orchestrator`, no `material-orchestrator`, no `interactive-polish-orchestrator`, no `1V-*` per-asset drawer, no other subagent. All orchestrators are POST-build only — they exist to enumerate slots in already-written source HTML. **They do not exist for pre-commit previews. Calling visual-orchestrator before Phase A is a Phase E rule violation.**
- **No HTML files written. The output is a PNG, full stop.** No `frame1.html` / `frame2.html` / `_render/` / `_drafts/` / any `.html` file under `.prototype-options/` or anywhere else. The +draft path does NOT do "render HTML then screenshot it" — that's overengineered for a pre-commit preview. The agent in studio2 did this exact wrong thing (wrote frame1.html + frame2.html to `.prototype-options/<slug>/_render/` then tried to dispatch visual-orchestrator). **The word "frame" used in the +draft invitation does NOT mean HTML frame — it means image frame (a single PNG). Read it as "PNG" everywhere it appears.** Forbidden.
- **No source/ writes at all.** Nothing under `source/<branch>/` until Phase A is reached via an explicit lock-and-build user message.
- **No workflow.json edits.** No nodes scaffolded, no edges added. Phase E owns workflow.json; +draft doesn't touch it.

## Step-by-step

1. Stay in the stop-and-ask phase — **do NOT commit the genre yet, do NOT write any source files, do NOT dispatch any orchestrator.**
2. Compose ONE prompt per draft image from the picked option's:
   - Shell silhouette (a one-line layout description)
   - Style detail file's prompt-friendly mood
   - Aesthetic detail file's named references
   - Palette (passed as hex tokens in the prompt)
   - **Typography as visual-characteristic description** (see *Typography in image-gen prompts* below — never just the bare family name)
   - If a photo register was attached: pull `prompt_keywords` from `design-library/photo-<styleId>.md`
   - If an illust register was attached: pull from `design-library/illust-<styleId>.md`
3. Generate **1 preview PNG by default, 2 PNGs maximum** (one hero, one optional secondary view) at small thumbnail size (≤768px longest side). The default is ONE — the user said "give me a quick preview", not "render the whole site". The word "frame" is forbidden in this step's vocabulary — it has muddled the agent into writing `frame1.html` / `frame2.html` before. The output is a PNG. Save under `.prototype-options/<TURN_SLUG>/draft-<k>.png` using the same TURN_SLUG as the preview recolours.
4. Re-emit ONLY the picked option's card with the real generated image replacing the recoloured preview, the `◉ auto-preview · no LLM` badge **replaced** with `◉ model-generated mockup · composition + palette only · typography is the model's interpretation, the actual build uses the locked face`, and a fresh prompt: `Lock this direction, pick a different option (1/2/3), or describe a swap.`
5. Still wait for user confirmation. The genre is committed only after the user says yes / 1 / lock it / build / similar after seeing the draft.

If the image-gen call fails (network error, quota, content filter), fall back gracefully: re-emit the option card with the original recoloured preview, add a one-line "*image-gen attempted but failed: [short reason]; showing the mechanical preview instead*", and ask the user whether to retry or pick a different option. Do not silently commit the genre on image-gen failure. **DO NOT escalate to visual-orchestrator on failure** — that doesn't help and adds a cascade.

## Typography in image-gen prompts (Option A — visual-characteristic description)

Text-to-image models (FLUX, SDXL, Imagen, DALL-E) **do not recognise font family names**. Asking for "Space Grotesk" produces "vaguely sans"; asking for "Fraunces" produces "vaguely serif". The model has never seen the .ttf file — it knows visual patterns from training data, not foundry catalogues.

To steer the model toward the right typographic feel, the prompt MUST translate the picked option's `<display font>` and `<body font>` into a **visual-characteristic description**, not the family name:

| `<display font>` / `<body font>` | Visual-characteristic description for the image-gen prompt |
|---|---|
| `Inter` | clean modern neo-grotesque sans-serif, slightly humanist warmth, tall x-height, open apertures, two-storey 'a' and 'g', similar to SF Pro / IBM Plex Sans |
| `Space Grotesk` | geometric grotesque sans-serif, slightly compressed, tall x-height, single-storey 'a', sharp angled terminals, modern technical feel, similar to Eurostile or DIN at display sizes |
| `Fraunces` | warm humanist contemporary serif, wavy and high-contrast, ball terminals on 'a' and 'f', distinctive two-storey curvy 'g' descender, somewhere between Cooper and Recoleta |
| `EB Garamond` | classic old-style book serif, low contrast, oblique stress, small x-height, traditional Renaissance feel, similar to Adobe Garamond |
| `Source Serif 4` | refined transitional serif, moderate contrast, slightly modern proportions, similar to Source Serif Pro or PT Serif |
| `IBM Plex Serif` | warm slab-influenced serif with restrained personality, similar to Liberation Serif or PT Serif |
| `Times New Roman` | classic transitional serif, thin strokes, ball terminals, the default-Office serif look — emphasise newspaper / formal-letter associations |
| `JetBrains Mono` | clean technical monospace, distinctive ligatures (=>, !=), slab-like serifs on i/l/1 to disambiguate, IDE-coding feel, similar to Fira Code |
| `Press Start 2P` | pixel-perfect bitmap, 5×7 grid, blocky uppercase 8-bit arcade feel, similar to NES title screens |
| `DM Sans` | rounded geometric sans-serif, warm friendly tone, slightly compressed, similar to Avenir Next or Proxima Soft |
| `Roboto` | neutral utilitarian sans-serif, mechanical skeleton with friendly curves, Android-native feel |
| `Söhne` / `Helvetica Neue` / system-ui fallback | classic neo-grotesque sans-serif, low contrast, tight tracking at display sizes, Swiss-modernist feel, similar to Helvetica or Akzidenz-Grotesk |

For families not in the table, the agent composes a description on the same axes: **classification** (sans / serif / mono / display / slab / script) · **construction** (geometric / humanist / grotesque / transitional / old-style) · **personality** (warm / clinical / technical / decorative) · **distinctive features** (two-storey 'a', ball terminals, sharp angles, etc.) · **similar to** (a well-known reference the model has seen).

**Prompt assembly shape:** prepend the description, then say "all headlines set as" and the headline text. Example for an `oversized-neo-grotesque + Space Grotesk` Option 1:

> `... oversized geometric grotesque sans-serif headlines: tall x-height, single-storey 'a', sharp angled terminals, modern technical feel, similar to Eurostile or DIN at display sizes. All headlines set as "WE DON'T DO QUIET" in the locked accent hex #ff4d2e on warm paper #f4f3ef. Body text in a clean neo-grotesque sans with slight humanist warmth, similar to SF Pro. NEVER mention the family name "Space Grotesk" or "Inter" in the prompt — the model doesn't know those names.`

**Honest about the limit:** even with visual-characteristic descriptions, the model produces an *interpretation*, not pixel-accurate typography. The +draft mockup shows composition direction and palette — type fidelity comes through in the actual build (Phase C+), where the prototype uses the real Google Fonts via `<link>` in the HTML head. The badge replacement in step 4 above makes this explicit to the user.
