---
name: onboarding-visual-policy
description: Visual-content rules the orchestrator quotes into every stage's dispatched prompt — biases brainstorms toward bespoke fonts + imagery, PRD toward concrete visual sections, refiner toward a visual axis, and codifies the multi-shell DS contract. Read once per session and substitute named blocks verbatim into stage prompts.
---

# Visual policy for onboarding orchestration

Four named blocks. The orchestrator quotes each verbatim into the relevant stage's dispatched prompt — DO NOT paraphrase, summarise, or strip the prose. The rules are written assuming a reader will follow them literally.

When orchestration is in "no-reference" mode (`reference.mode == "brainstorm"` in `.onboarding-pending.inputs`), append the marked **// no-reference tightening** sub-block to BRAINSTORM_VISUAL_RULES at dispatch time.

---

## BRAINSTORM_VISUAL_RULES

Used by: Stage C (`bs_ds_a/b/c` ds-brainstorm sample HTMLs).

> Every brainstorm sample MUST satisfy ALL of these. A sample that violates any rule is a re-do, not a "good enough":
>
> 1. **No safe-default fonts.** Inter, Geist, Helvetica, Arial, Roboto, San Francisco system stack, Segoe UI are FORBIDDEN as the primary display face. Pick a display font with character — Fraunces, Söhne, Domaine Display, GT America, IBM Plex Serif, Spectral, Source Serif Pro, Pirelli, Eiko, PP Editorial New, JetBrains Mono Italic display sizes, Migra, or anything similarly committed. Body face MAY be a workhorse (Inter, IBM Plex Sans, Geist) IF the display face is not. Pair on contrast — serif display × sans body, mono display × serif body, etc.
> 2. **At least one photographic OR illustrative image — generated through the visual-planner pipeline.** Not a placeholder block, not a coloured rectangle, not "Image placeholder" text. NOT `picsum.photos` / `source.unsplash.com` either (v2.46 removed that carveout — the previous policy allowed throwaway-stage placeholders but the user wants real assets across all exploration stages so what they pick looks like what they'll ship). Use image slot markers per IMAGERY_PIPELINE below and dispatch visual-planner after writing the HTML. The brainstorm becomes a real picture of the direction, not a picture of "what the direction would look like if we had real images." Match the image topic to the app domain. Image must do work — convey mood, anchor the layout, frame the brand — not just exist.
> 3. **Show ONE real page, not a token gallery.** Each variant's sample HTML renders ONE page the app would have — login, primary task surface (e.g. dashboard / inbox / feed), success state, error state, OR loading state. NOT a styles-only gallery, NOT a typography sample, NOT a colour palette swatch sheet. The DS gallery is Workflow 0's job downstream; the brainstorm's job is "what does the app feel like."
> 4. **State variety across the 3 variants.** Pick three DIFFERENT page types across the three variants so the user is comparing directions, not the same screen three ways. E.g. variant A = login, B = dashboard, C = success state. Don't show three logins.
> 5. **Real product copy, not lorem.** Write actual headings, real button labels, real placeholder text. The user can't judge a direction off "Heading 1" + "Subhead text here" — they're judging tone, voice, density.
> 6. **No emoji decoration.** UI icons are fine (use inline SVG or a real icon font); decorative emoji as visual filler is forbidden. Emoji read as a tonal shortcut — directions earn tone through type + colour + spacing, not 🎯 stickers.

### // no-reference tightening (append when `reference.mode == "brainstorm"`)

> 7. **Extra-bespoke font policy.** Beyond the forbidden list above, ALSO avoid the top 20 SaaS-default fonts: Manrope, DM Sans, Public Sans, Open Sans, Nunito, Lato, Poppins, Source Sans, Quicksand, Work Sans, Sora, Outfit, Plus Jakarta Sans, Karla, Mulish, Spline Sans, Hanken Grotesk, Onest, Geist Mono, Cabinet Grotesk. Reach for editorial / display / mono families with strong character: Migra, Editorial New, Reckless, Domaine, GT Sectra, Söhne Breit, Tiempos, Recoleta, NB International, ABC Diatype, Tobias, JetBrains Mono Italic at large sizes.
> 8. **One unconventional pairing per variant.** Each variant's type stack should include at least one pairing that would feel weird in a default SaaS app — mono display + serif body, condensed grotesk + warm serif, italic display + sans body. Lean into the unfamiliarity; it's what makes the brainstorm useful instead of three near-duplicates.

---

## BRAINSTORM_SHELL_RULES

Used by: Stage C alongside BRAINSTORM_VISUAL_RULES. Frames the multi-shell DS contract introduced in v2.

> Each DS variant declares a **direction**, NOT a single shell. The variant spec MUST include a `compatibleShells` list naming 2–4 shells from the PROTOTYPE.md §2 menu:
>
> - `3-col-app` (nav · canvas · inspector)
> - `2-col-app` (nav · canvas)
> - `top-bar-canvas-footer` (header · main · footer)
> - `centered-narrow` (max-width: 65–72ch, margin auto)
> - `hero-features` (hero · feature stack · CTA)
> - `bento` (12-col asymmetric spans)
> - `masonry` (CSS columns / grid auto-flow dense)
> - `full-bleed-floating` (canvas + glass overlays)
> - `mobile-top-tabs` (header · scroll · bottom tabs)
> - `editorial-broken` (grid-template-areas with overlap)
>
> Pick shells the direction's type + spacing + color CHOICES would work in. An Editorial Mono direction works in `centered-narrow` + `editorial-broken`; a Trading Floor direction works in `3-col-app` + `full-bleed-floating`. Cross-shell coherence is the test: would these tokens still feel right in any of the named shells?
>
> The sample HTML you write shows ONE shell from the list — pick the one that most clearly communicates the direction. The other compatible shells get their own stylesheets downstream at Stage D / H (Workflow 0 / 6+6b emit `design-systems/<id>/shells/<shell>.css` per compatible shell). Stage E's chunking then picks one shell per page.
>
> Output shape (embed at the top of the sample HTML as a JSON comment, OR in a `<script type="application/json" id="variant-spec">` block, OR at the top of the sample HTML's `<head>` as an HTML comment — whichever survives the sample's render best):
> ```json
> {
>   "label": "<short variant name>",
>   "direction": "<one-sentence vibe>",
>   "compatibleShells": ["<shell-id>", "<shell-id>", ...],
>   "primaryShell": "<shell-id-shown-in-sample>"
> }
> ```

---

## PRD_VISUAL_RULES

Used by: Stage B (`bp_prd_refine` prompt) and Stage G (`bp_prd_final` prompt).

> The PRD is a design document, not a feature list. It MUST include — as explicit, named sections — ALL of:
>
> 1. **Visual identity cues** — 3 mood words (e.g. "calm, precise, warm") + 3 reference URLs (real apps, sites, or visual references that capture the vibe). Not vague adjectives like "modern" or "clean."
> 2. **State coverage matrix** — for every major surface (login, primary task, list/feed, detail, settings, etc.), enumerate the states the design must handle: idle, empty, loading, partial, success, error, offline, permission-denied. Not every surface needs every state, but the matrix forces the question. Format as a small markdown table.
> 3. **Key imagery list** — explicit list of visual artefacts the prototype must produce: login splash imagery, hero illustration, empty-state illustration, success illustration, error illustration, avatar placeholders, hero photography, decorative imagery. For each: a one-line treatment ("warm photographic, soft-focus background", "line illustration, single accent colour", "abstract data viz, no people"). This drives the asset spec downstream.
> 4. **Page-to-shell map** — for every page named in the page inventory, name the recommended shell from BRAINSTORM_SHELL_RULES with a one-line rationale ("alert detail = centered-narrow because read-decide-act, not monitoring"). Format as a small markdown table.
>
> Existing standard PRD sections (Problem, Audience, Goals, Pages, Key flows, Tone) ALSO remain required — these visual sections are additive, not replacements.

---

## IMAGERY_PIPELINE

Used by: Stage C (`bs_ds_a/b/c`), Stage E (`bs_html_*`), Stage F (`br_remix_p*` remix alts), and Stage I (`bp_proto_build`). ALSO referenced indirectly by PRD_VISUAL_RULES (the "key imagery list" downstream consumers act on).

> v2.46 — ALL stages use this pipeline. The previous policy let throwaway exploration stages (C / E / F) embed `picsum.photos` / `source.unsplash.com` URLs inline as a cost shortcut. User reversed it: brainstorm/quick-html/remix samples are what the user evaluates the direction against, so they must show real generated assets, not stock photos. Every image in every stage goes through the visual-planner pipeline, becoming a first-class workflow asset node the user can re-run, re-prompt, and inspect on the canvas.
>
> **Cost trade-off:** C has 3 variants, E has 3 pages, F has 9 remix cells. At ~3-5 images per HTML page, this is roughly 45-75 image generations across the throwaway stages alone. Acceptable because (a) the user can stop after Stage C if they don't like any direction without paying for E + F, (b) per-image gen is cheap relative to opus-driven HTML gen, (c) the picked variant's assets carry forward into Stage I refinement.
>
> ### How it works
>
> The Source subagent (Subagent 1, dispatched by stage I) writes HTML with **image slot markers** instead of real URLs:
>
> - **Raster (photo / illustration / mascot):** `<img src="images/<assetId>.png" alt="<one-line intent>" data-intent="<one-line intent>">`
> - **Vector icon:** `<img src="icons/<assetId>.svg">` OR inline `<svg>…</svg>` if hand-drawn
> - **Vector mark / logo:** inline `<svg>…</svg>` if simple, OR `<img src="marks/<assetId>.svg">`
> - **Shader / particle / canvas effect:** `<canvas data-asset="<assetId>"></canvas>`
> - **3D scene:** `<canvas data-asset="<assetId>" data-medium="three"></canvas>`
> - **Video / Lottie / GIF:** `<video src="video/<assetId>.mp4" autoplay loop muted>` / `<div class="lottie" data-src="lottie/<assetId>.json">`
>
> Each slot's `data-intent` (or a nearby comment) carries a one-line description of what should be there ("morning routine flat illustration", "habit-tracker mascot waving", "ambient particles drifting up").
>
> After source is written, stage I dispatches the **visual-planner** subagent via the Task tool. visual-planner:
> 1. Enumerates every slot it finds in source/`<branch>`/*.
> 2. Classifies each by medium (raster-foreground, raster-photo, vector-icon, vector-mark, shader, particle-2d/gl, lottie, 3d, video).
> 3. Scaffolds a per-asset node trio into `workflow/workflow.json` — `prompt` (the creative brief), `skill` (the generator), `asset` (the file sink). The user SEES these nodes appear on their canvas.
> 4. Dispatches the matching per-medium drawer subagent (e.g. raster-photo, vector-icon) per asset. Each drawer fills its trio's prompt + dispatches the generator.
>
> Result: every image in the prototype is a real asset under `source/images/` (or `icons/`, `marks/`, `video/`, `lottie/`) generated through the proper pipeline. The user can re-run any asset individually from the canvas, edit the prompt, swap mediums, etc.
>
> ### What stages C / E / F / I must do (v2.46 — uniform)
>
> 1. **Phase 1 — Source skeleton with slot markers.** Write the HTML with image SLOTS (not URLs). Use stable `assetId` slugs scoped to the stage: Stage C variants under `_ds_brainstorm/<x>_assets/`, Stage E pages under `_pages/page_<N>_assets/`, Stage F remix cells under `_remix/p<N>_<x>_assets/`, Stage I final source under `source/images/` (and `icons/`, `marks/`, `video/`, `lottie/`). Honour the imagery list from the upstream spec.
> 2. **Phase 2 — Dispatch visual-planner.** Use the Task tool: `subagent_type: "visual-planner"`, prompt = "HTML at `<path>` is written; enumerate image slots and scaffold the per-asset node trios + generate assets." Wait for return.
> 3. **Forbidden in ALL stages:** `picsum.photos`, `source.unsplash.com`, `placeholder.com`, base64 data URIs that aren't tiny icons (>200 chars), or any other "fake image" URL. If you find yourself reaching for these, STOP — the right answer is an asset slot + visual-planner dispatch.
>
> ### When the user re-runs orchestration
>
> If stages D + H regenerate the DS (different palette, different mood), the visual-planner doesn't auto-re-trigger — image regeneration would be wasteful when only some assets need updates. The user re-runs the per-asset nodes manually from the canvas (each is a first-class node). Future v3 might auto-detect DS changes that imply imagery re-gen.

---

## CONTENT_DISCIPLINE

Used by: Stage E (`bs_html_*` html-gen), Stage F (`br_remix_p*` remix alts), and Stage I (`bp_proto_build` source skeleton).

> Every HTML page you write — brainstorm sample, exploration html, remix alt, OR final source — MUST satisfy these rules. Length without substance is a re-do, not a "good enough":
>
> 1. **≤ 200 lines of code per page.** Hard ceiling. If you're past 200 LOC, you're padding — strip the filler. Use the DS's primitive classes and let `design-systems/<id>/styles.css` carry the heavy CSS; per-page CSS in `<style>` blocks is for shell-specific layout overrides only.
> 2. **Every block must earn its place.** Each `<section>`, `<div>`, `<aside>`, `<header>`, `<footer>` must demonstrate EITHER (a) a unique component the DS hasn't shown elsewhere, OR (b) a unique state of an already-shown component (loading, empty, error, success, partial). Decorative wrappers, "spacer divs", repeated "feature card #3" that mirrors #1 with different copy — STRIP.
> 3. **No filler copy.** Lorem ipsum is forbidden. Generic SaaS marketing prose ("Streamline your workflow", "Unlock productivity", "Built for teams") is forbidden — write copy specific to the app domain from the PRD (`bp_prd_text` or `cp_ctx_prd_upload`). Headings must say what the section IS, not gesture at vibes.
> 4. **No more than 3 nesting levels deep without justification.** Excessive nesting is a tell that the component model is wrong — flatten or invent a primitive name for the deep structure and reference it from `design-systems/<id>/styles.css`.
> 5. **No dead links.** Every `href`, `onclick`, or `<a>` either (a) navigates to a real page in this prototype, (b) opens a modal/drawer that's also implemented, OR (c) has `href="#"` with `aria-disabled="true"` AND a `data-todo="<why disabled>"` attribute. Phantom navigation is a lie.
> 6. **No commented-out code shipped.** If you backed out a decision, delete the lines. The agent before you doesn't need a record; git does.
> 7. **Substance per line.** A 200-LOC page that's 80% navbar boilerplate and 20% one card is failing rule 2. A 60-LOC page that shows the same card three times is failing rule 2. The right shape varies by surface: a dashboard needs density (many small components, each earning its slot); a settings page needs sections (each a distinct decision); a login needs focus (one form, one mood image, one decision).
>
> ### Per-stage variations
>
> - **Brainstorm samples (Stage C):** ≤ 150 LOC. The brainstorm is direction-setting, not content-rich — one real page, hero, optional secondary surface. Don't pad to fill 200.
> - **Exploration HTML (Stage E):** ≤ 180 LOC. Slightly bigger than brainstorms because the user is starting to evaluate flow.
> - **Remix alts (Stage F):** ≤ 200 LOC. Same surface 3 ways — the WHOLE point is meaningful difference per alt; don't pad to make alts feel "complete."
> - **Final prototype (Stage I):** ≤ 200 LOC per page, but the prototype has MORE pages. The discipline is per-page, not per-prototype. A 10-page prototype that's 1500 LOC total is fine if each page averages 150 LOC of substance.

---

## REFINER_VISUAL_AXIS

Used by: Stage G's `bp_prd_final` (the picked-cell-refines-PRD step) and any future iterative-refinement loop.

> When refining the PRD with the picked remix variant:
>
> 1. **At least one scoring axis MUST be visual.** Don't refine on feature completeness alone. Score the picked variant on (at minimum) ONE of: visual density gradient, type-pair coherence, imagery treatment consistency, motion economy, decoration discipline, colour temperature, whitespace mass. Quote a specific observation from the picked HTML to anchor the axis ("the picked Alt B uses a 65ch column with serif body — implies the PRD's audience expects a long-read posture, update the audience truth section to reflect that").
> 2. **The "push past X to Y" mechanism MUST offer a visual-push option each cycle.** Generic version: "the picked design is currently at <safe direction>; the bolder direction available without breaking the brief is <Y>." E.g. "currently warm-photographic / could push to mixed-media collage", "currently centered-narrow / could push to editorial-broken grid", "currently muted greys / could push to one full-saturation accent." User decides whether to push; the option is always offered.
> 3. **Never silently strip a visual section from the PRD.** If a refine cycle would remove the state coverage matrix, key imagery list, page-to-shell map, or visual identity cues — STOP and emit a `<decision-request>` asking whether that's intentional. The visual scaffolding survives refinement by default.
