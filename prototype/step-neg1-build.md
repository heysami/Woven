---
name: step-neg1-build
description: Step -1 post-pick build pipeline - Phases A through F, including the MANDATORY Phase A.5 orchestrator plan gate (multi-select decision card, proposed roster pre-checked, user edits + approves before any dispatch). Loaded ONLY after the user picks an option (numbered pick, "you pick", "lock it", "build", etc.). Locks the picked option's exact typography + palette into the build and runs the orchestrator-dispatch chain on the approved roster.
---

# Step -1 - After the user picks (Phases A → F)

Reached when the user has committed an option (clicked a button, said "option N", said "you pick" / "lock it" / "build", or named a fresh direction that's now coherent). This file is the COMPLETE post-pick build contract.

**Critical structural rule:** Step -1's stop-and-ask is the FIRST stage of the existing Woven build pipeline, not a self-contained mini-protocol that ends in "write some files." After the pick, the agent MUST execute Phases A → F below in order - **including the Phase A.5 orchestrator plan gate, the flow's second and last stop-and-ask** - integrating with the existing orchestrator fan-out documented in `AGENTS.md` and `docs/agents/subagents/`. Skipping Phase E or improvising inside Phase C is what produced studio's "picked Space Grotesk + JetBrains Mono, built Anton + Space Mono, skipped photography-orchestrator despite picking acid-design (raster-heavy)" failure.

## Phase A - Lock the contract from the picked `<opt>` (IMMUTABLE through build)

The picked option's child tags are the **immutable contract** for everything downstream. Re-read them from the emitted `<direction-options>` block (they're in your conversation history), and bind them verbatim - no improvisation:

| Picked-opt tag | Locked into | Notes |
|---|---|---|
| `<palette>#bg,#surface,#fg,#muted,#border,#accent</palette>` | `:root` CSS variables in `styles.css` | One CSS var per token. Don't invent extra tokens of different hue; derive shades via `oklch()` from THESE. |
| `<display font="X">` | `--font-display: "X", <sensible fallbacks>;` AND a Google-Fonts `<link>` in every page's `<head>` | If `X` is a system font (Times New Roman, Georgia, Arial, etc.), skip the `<link>` - the family resolves locally. |
| `<body font="X">` | `--font-body: "X", <sensible fallbacks>;` AND a `<link>` for the family (one combined Google Fonts `<link>` if both display + body are Google). | Same system-font carve-out. |
| `<axes>Shell: <shell-X> · Style: <style-Y> · Aesthetic: <aesthetic-Z></axes>` | The three detail files to Read in Phase B | These IDs identify exactly which files under `./prototype/` to inherit vocabulary from. A committed aesthetic (≠ none) is authoritative over the style's native look per Phase B.5 - it is a lock on the build's cultural register, not a hint. |
| `<vibe>…</vibe>` + `<why>…</why>` + `<label>…</label>` | The genre-commit one-line comment at the top of `styles.css` (or `app.js` line 1) | Captures the WHY for downstream readers. |
| `<image src="…option-N.png"/>` | (Reference only - do NOT embed the preview PNG in `source/`; it was for the chat preview, not the build.) | Stays in `.prototype-options/` as ephemera. |

**The lock is verbatim, not "inspired by".** If the picked option has `<display font="Space Grotesk">`, the `:root` line is:

```css
--font-display: "Space Grotesk", "Helvetica Neue", Arial, sans-serif;
```

NOT `"Anton"`, NOT `"Inter"`, NOT "whatever the agent thinks fits the genre better." The user picked Space Grotesk; the build ships Space Grotesk.

Same for the palette: every hex in `<palette>` becomes a `:root` var. Don't substitute "warmer slate" for `#161616`. If you derive a hover state, do it via `oklch(from var(--accent) calc(l - 0.1) c h)` - anchored to the locked token.

## Phase A.6 - Drop the design materials onto the workflow canvas (only when this pick IS the design-system lock-in)

The Step -1 pick is the moment the project's design language gets locked - and that lock should leave a visible, editable artefact on the canvas, not just live inside `styles.css`. **When this build is the project's design-system commit** (Trigger A - no DS existed and the user just picked a direction; equivalently `meta.dsRef` is still unset), materialise the locked contract as a **"Design materials" section** so the palette, typography, and the picked direction's imagery sit together on the canvas where the user (and later passes) can see and reuse them.

Skip this phase when a DS already existed (Step -1 carve-out 1 - you inherited vocabulary, didn't lock a new one) or when the user is editing an existing prototype in place.

**Build the nodes from the locked Phase-A contract** and append them in ONE race-safe call to `POST $TH_DAEMON_URL/__workflow/nodes/add?project=$TH_PROJECT_ID` (this endpoint APPENDS - it never rewrites the whole canvas, so it can't clobber the editor's in-flight edits; do NOT GET-then-POST the full `/__workflow`). Containment is geometric - a node belongs to the section when its CENTRE falls inside the section's rect - so there are NO edges to add; just place each child's `x/y/w/h` inside the section rect.

Pick a clear spot for the section (`SX`,`SY` - anywhere not overlapping existing nodes, e.g. to the right of the prototype node). The body of the POST is `{ "addNodes": [ … ] }` containing:

- **1 `section`** - `{ "id":"sec_materials", "kind":"section", "x":SX, "y":SY, "w":1180, "h":760, "title":"Design materials" }`
- **1 `color-palette`** - every hex from the locked `<palette>` as a swatch (keep the token names you used in `:root`): `{ "id":"mat_palette", "kind":"color-palette", "x":SX+28, "y":SY+64, "w":320, "h":280, "name":"Palette", "swatches":[ {"name":"--bg","value":"#…"}, {"name":"--surface","value":"#…"}, {"name":"--fg","value":"#…"}, {"name":"--muted","value":"#…"}, {"name":"--border","value":"#…"}, {"name":"--accent","value":"#…"} ] }`
- **1 `typography`** - the locked display + body families: `{ "id":"mat_type", "kind":"typography", "x":SX+372, "y":SY+64, "w":360, "h":360, "name":"Type", "fontFamily":"<display family>", "fontCdn":"<the Google Fonts css2 URL you linked, or omit for system fonts>", "monoFamily":"<body family>", "monoCdn":"<its css2 URL>", "levels":[ {"name":"Display","size":40,"weight":700,"lineHeight":1.1,"sample":"<the display sample from the picked opt>"}, {"name":"Body","size":16,"weight":400,"lineHeight":1.5,"sample":"<the body sample from the picked opt>"} ] }`  ‹fontFamily = display, monoFamily = body - the node shows both as the two specimen rows.›
- **N `asset` (image)** - one per recoloured preview PNG the picked `<opt>` carried (`aesthetic` / `style` / `shell`, plus `photo` / `illust` if present). Lay them in a row below: for the i-th image `{ "id":"mat_img_<axis>", "kind":"asset", "assetKind":"image", "path":".prototype-options/<TURN_SLUG>/option-<N>-<axis>.png", "x":SX+28+i*324, "y":SY+460, "w":300, "h":200 }`. These PNGs already exist from the emit step - reference them, don't regenerate.

The grid above is already tidy; if you add or remove items and want it re-packed, the section's **⊞ Tidy** button (top-right of the section bar) re-flows the contained nodes into a grid and resizes the section to fit. Mention it once to the user.

> **Quick imagegen mockups land here too.** Later in the project, when the user asks for a quick imagegen mockup (and an image-gen model is wired), after generating the asset, append it as one more `asset` (image) node INSIDE the existing "Design materials" section (find it in `GET /__workflow`, place the new node's centre within its rect, `POST /__workflow/nodes/add`). One home for every material the project accumulates.

## Phase A.5 - Orchestrator plan gate (MANDATORY stop-and-ask, second and last gate of the flow)

Which orchestrator passes run on this build is a taste + budget decision, and - exactly like the direction pick - it belongs to the user. After locking the Phase A contract, **compose the orchestrator roster proposal from the locked axes + the brief's surfaces, emit it as a multi-select `<decision-request>` card, END YOUR TURN, and wait.** Phases B → F run only after the user's reply. Do NOT silently dispatch the Phase E chain; do NOT bury the roster in prose and proceed.

**Carve-outs that skip this gate (and only these):**

1. **The user delegated this turn** - the pick message (or an earlier message in this turn-chain) says "just build", "you pick", "no questions", or an obvious equivalent. Use your proposed roster, name it in the Phase F report.
2. **The pick message already settled the roster** - it explicitly names which orchestrator passes to run or skip with nothing left ambiguous ("option 2, photos + material, no polish"). Honor it verbatim.
3. **The current message IS the reply to this gate** (a `[decision:orchestrator-plan]` message or a prose roster edit). Apply it and proceed to Phase B.

**DS build policy seeds this gate.** If the inherited DS declares a `buildPolicy` (in `meta.json`, also returned by `GET /__design_systems` as `buildPolicy`), it is the starting point for this proposal - the DS owner already made these calls, so don't re-decide them from scratch:
- `buildPolicy.orchestrators` is a list → propose **exactly** those orchestrators pre-ticked, and list the rest unticked (the user can still opt in, but the DS's choice is the default). `"auto"`/absent → propose as you normally would.
- `buildPolicy.imagery` is a list → the media kinds the build USES (a directive, not just a ceiling). Two directions, both binding:
  - **Excluded kinds are off.** Do NOT propose orchestrators whose only output is an excluded kind; visual-orchestrator must classify excluded slots as `none`/inline-SVG.
  - **Included raster kinds are ON when a provider exists.** If the list includes any raster kind (`raster-photo` / `raster-foreground` / `video`) and an image-generation provider is available this run, `visual-orchestrator` is pre-ticked and the source MUST carry real slots for the photographic/illustrative parts of the page (`photography-orchestrator` / `illustration-orchestrator` pre-ticked as the slots warrant). Do NOT draw those slots as inline-SVG to avoid generation; the policy committed to real imagery. Inline-SVG-only is right only when no provider is available or the list omits raster.
  - `"auto"`/absent → no constraint either way.
- `buildPolicy.polish` → `"none"` pre-unticks (and forbids) interactive-polish-orchestrator; `subtle`/`playful`/`theatrical` pre-ticks it and sets its register; `"auto"`/absent → decide normally.

The user can always override the seeded proposal in their reply - buildPolicy sets the default, the gate still gives them the final say. State in the proposal preamble when it was seeded from the DS ("pre-ticked from this DS's build policy").

**Composing the proposal:**

1. Candidates come from the locked axes + the Phase E chain: `photography-orchestrator`, `illustration-orchestrator`, `creative-visual-orchestrator`, `visual-orchestrator`, `material-orchestrator`, `interactive-polish-orchestrator` - plus any experience-family orchestrator the brief's predicates match (`simulation` / `interactive-media` / `narrative-experience` / `game-experience` / `scrapbook-experience` / `motion-studio`; see the capabilities preamble's predicate table). When the DS declares `buildPolicy.orchestrators`, that list IS the candidate set (pre-ticked); other orchestrators appear unticked.
   - **`art-director-orchestrator` is the one PRE-build candidate.** When an image-gen model is wired, pre-tick it FIRST in the roster: it generates a north-star key visual (UI chrome + imagery composed as one frame), inspects the pixels, and writes `workflow/art-direction-contract.json` - the single design source the Phase C build AND every Phase E asset orchestrator read, so the chrome and the generated imagery cohere instead of drifting into two looks. It is the structural fix for "radiant generated art on a timid template UI". With NO image-gen model it is unavailable - omit it from the roster (it fails closed; the build runs from the text-only committed aesthetic exactly as today). It does NOT enumerate slots and is NOT part of the Phase E post-build chain - it runs in Phase A.7, before source is written.
2. Each option's label is a one-line PLAN, not a category name: which pages / sections / slots it will fill, with what, and WHY the locked direction earns it ("photography-orchestrator - hero + 3 feature photos in Y2K-halftone register; acid-design is raster-heavy"). Rough volume where it drives cost ("≈ 14 slots"). The user must be able to veto from the label alone.
3. Pre-tick recommended orchestrators with the bare `checked` attribute. List plausible-but-not-recommended candidates UNchecked with a plan line saying what opting in would add - proposing an orchestrator as N/A-by-default is a valid shape. `visual-orchestrator` is pre-ticked whenever the source will carry any visual slot (it almost always will). Always include a `none` option last.
4. Emit at the end of the turn:

```
<decision-request id="orchestrator-plan" multiSelect="true" minPicks="1" prompt="Direction locked. Here's the orchestrator plan I propose - untick anything you don't want, tick anything extra, then Send. I'll build with exactly that roster.">
  <option value="art-director-orchestrator" checked>art-director-orchestrator - PRE-BUILD: generate one north-star key visual (chrome + imagery in one frame), then build the whole UI from its palette/ratios/composition/material DNA so the generated art and the chrome read as one world (only offered because an image-gen model is wired)</option>
  <option value="photography-orchestrator" checked>photography-orchestrator - hero + 3 feature photos, Y2K-halftone register; acid-design is raster-heavy</option>
  <option value="illustration-orchestrator" checked>illustration-orchestrator - 6 sticker-style spot illustrations on the pricing + about sections; distorted-chrome rave register</option>
  <option value="creative-visual-orchestrator" checked>creative-visual-orchestrator - promotes the hero img into asset-cut-into-letters; acid-design is editorial-loud, this is its signature move</option>
  <option value="visual-orchestrator" checked>visual-orchestrator - enumerates all ~14 visual slots, classifies media, fans out the per-asset drawers (reads the photo/illust enrichments above)</option>
  <option value="material-orchestrator">material-orchestrator - optional: reactive chrome/holographic sheen on cards; adds tilt-tracked light (off by default, the style reads fine flat)</option>
  <option value="interactive-polish-orchestrator">interactive-polish-orchestrator - optional post-pass: hover surprises + pointer-tinted background; loud register allows it</option>
  <option value="none">None - skip every orchestrator pass; CSS/SVG-only build</option>
</decision-request>
```

**Reply handling:** picked set (minus `none`) = the APPROVED roster. `none` → Phase E becomes a no-op and the Phase F report says the build is CSS/SVG-only. A prose reply ("skip material, add motion-studio") is just as valid - apply the edits and continue without re-asking. If `art-director-orchestrator` was approved, it runs in **Phase A.7 (below), before Phase B/C** - its `art-direction-contract.json` must exist before source is written, because the build derives its tokens/composition/type/motion from it. If an experience-family orchestrator with a pre-build phase was approved (`motion-studio-orchestrator` `mode=brainstorm`), its brainstorm dispatch likewise runs BEFORE Phase C so the returned slot tags land in the source write. Approval covers this build pass; a later "regenerate" ask re-fires the gate.

**The approved roster is a filter, not a forced march:** Phase E dispatches ONLY approved orchestrators, and each still self-gates via its manifest (an approved photography-orchestrator with zero photo slots returns a clean no-op). Unapproved orchestrators are skipped even when their manifest gate would fire.

**`owns-surface` picks are a DIRECTION decision, not a slot tick (reconciliation rule).** Some candidates are tagged `directionImpact: "owns-surface"` in their manifest (game-experience / simulation / motion-studio / interactive-media / narrative-experience / scrapbook-experience / scene-3d). Each embeds a self-contained runtime that owns a whole surface with its OWN feel - adding one is choosing to make the app part-X, not adding a slot. So when the user ticks an owns-surface orchestrator that you did NOT pre-recommend (the realistic "good idea, add a game" case), do NOT silently accept it as a peer. Reconcile, two parts:
  1. **Bind it to the art-direction contract.** If `art-director-orchestrator` is also in the roster (or you can add it - image-gen wired), the surface inherits the app's DNA via `surfaceContracts[<containerId>]` (Phase A.7 composes it into the plate, Phase E's owns-surface dispatch reads it). If art-director is NOT in the roster, say plainly that the surface will be built from its own independent research and may not match the chrome - and offer to add art-director so they cohere. This is the explicit fix for the "two halves stitched together" failure.
  2. **Name the completeness asymmetry.** An owns-surface orchestrator ships a fully-wired runtime, while the surrounding prototype is a clickable mock by design (placeholder handlers, demo data). So the game/sim/scene will be the ONLY fully-interactive surface unless the app's primary loop is also wired. Surface this in one line at the gate ("the feed game will be fully playable; the rest of the app stays a clickable demo unless you want me to wire the core loop too") so the user chooses the fidelity balance instead of discovering it after.

## Phase A.7 - Pre-build art direction (run ONLY when `art-director-orchestrator` was approved at A.5)

This is the one orchestrator that runs **before** source is written. Dispatch it immediately after the A.5 reply, before Phase B:

```
Task(subagent_type: "art-director-orchestrator",
     description: "Generate north-star plate + art-direction contract",
     prompt: "<envelope: committedDirection, committedAesthetic slug or null, brief, styleCue, successFeel, sensoryTargets, antiPatterns, the brief's unresolved tensionAxis if any, imageGenSkills from GET /__capabilities, dsRef if a DS is locked, mode='create', AND approvedOwnsSurface=[every orchestrator in the A.5-approved roster whose manifest directionImpact=='owns-surface' - game-experience / simulation / motion-studio / interactive-media / narrative-experience / scrapbook-experience / scene-3d - each as {id, containerId, oneLine}]>")
```

**Pass `approvedOwnsSurface` from the A.5 roster.** This is what makes the choice precede the contract: art-director composes each approved owns-surface region INTO the north-star plate and writes a binding `surfaceContracts[<containerId>]` sub-brief for it, so when that orchestrator builds in Phase E its register is a translation of the app's DNA, not an independent pick. With the roster known here, no contract revision is needed for THIS build (revision is only for owns-surface added in a later turn - see Phase E's late-add note).

It generates the north-star plate(s), surfaces them for the user's approve/pick/steer/reject (its own §12.5 gate - this is a real stop-and-ask; honour it before proceeding), and on approval commits `workflow/art-direction-contract.json`. **Block on its hand-off before Phase B/C** - the contract is an input to Phase B.5 and Phase C.

Failure / skip handling (do not stall the build):
- It returns `runStatus: error` "no image-gen model" → it should never have been pre-ticked; proceed to Phase B with no contract (text-only aesthetic, as today).
- The user rejects at the art-director gate → proceed with no contract; note it in Phase F.
- A contract exists → Phase B.5 and Phase C treat it as authoritative per the precedence below.

## Phase B - Read the detail files for genre vocabulary

Once Phase A is locked, `Read` the three detail files identified in `<axes>`:

- `./design-library/shell-<id>.md` - layout primitives, density classes, skeleton HTML
- `./design-library/style-<id>.md` - surface treatment vocabulary, depth grammar, shape language, optical inheritance
- `./design-library/aesthetic-<id>.md` (if not "(none)") - cultural register, era cues, decoration vocabulary, named references

Plus, if a `recipe-<id>.md` was named, `Read` that too - recipes bundle all three picks with proven combinations.

**These detail files inform vocabulary, not Phase A locks.** The style detail file may suggest a default font; **the picked `<display font>` overrides that suggestion** - Phase A wins every conflict. The detail files exist to fill in the picks the Step -1 UI didn't surface (shape language, motion budget, voice register, secondary tokens, slot annotation conventions). When an aesthetic was committed, how it ranks against the style's own vocabulary is governed by Phase B.5 below - do not treat aesthetic and style as co-equal flavour.

## Phase B.5 - Aesthetic authority: the committed aesthetic is NOT optional flavour (run when `<axes>` aesthetic ≠ none)

This is the rule whose absence caused the recurring failure: **the picked aesthetic gets silently overridden by the style/shell/recipe template, and the build snaps back to that template's native look** (dense-mono-dark → Bloomberg, swiss-grid → Müller-Brockmann, sf-pro → iOS). The style and shell detail files carry a strong implicit aesthetic; without this gate the agent reads that concrete native look, treats the committed aesthetic as faint seasoning, and ships the template. The user picked the aesthetic on purpose. Dropping it back to the template default is the single most disappointing outcome of this flow and is **forbidden**.

When `<axes>` committed an aesthetic that is not `(none)`, that aesthetic is the **authoritative cultural register for the build**. It outranks the style's and the recipe's *native* aesthetic. Precedence, top to bottom:

1. **Phase A locks** (palette hexes, font families) - immutable, win every conflict.
2. **Art-direction contract** (`workflow/art-direction-contract.json`, when Phase A.7 produced one) - authoritative for everything the picks didn't pin: colour-use *ratios* (`extracted.palette[].ratio`), value structure, composition logic, material directive, type rhythm/scale, component style, motion character. It does NOT override Phase A's locked hexes/families - it fills and governs the dimensions *between* the locks. When the contract and the committed aesthetic disagree on how a surface should feel, the contract wins (it was derived from a generated frame the user approved; the aesthetic slug is the more abstract input). Honour `bindingRules`: inherit the plate's DNA, never replicate its literal subject/layout/copy.
3. **Committed aesthetic** - owns decoration vocabulary, ornament, texture, era cues, motion personality, type *personality* (within the locked families), and palette *mood* (within the locked hexes). When the style's native register and the committed aesthetic disagree about how a surface should feel, the aesthetic wins.
4. **Style** - owns surface/depth grammar, density, shape language, optical inheritance: the chassis the aesthetic is dressed onto, not the look itself.
5. **Shell** - owns layout skeleton only.

(With no contract - no image-gen model, or the user skipped art direction - this collapses to the original four-rung ranking and the build behaves exactly as before.)

A recipe's own `Aesthetic:` line (often `(none)`) does NOT override a separately-committed aesthetic. If the picked option paired `aesthetic-vaporwave` with `style-dense-mono-dark`, the build is "a dense data terminal rendered in vaporwave" - magenta/cyan gradients, chrome bezels, Floral-Shoppe melancholy on the dense chassis - NOT a stock Bloomberg terminal with the aesthetic quietly discarded.

### Translation assessment - run it before writing source, act on the verdict

Before Phase C, decide how far the style/shell chassis can actually carry the committed aesthetic, and act:

- **Translatable** - the aesthetic's decoration vocabulary maps cleanly onto the chassis. Build the fusion; note it in the Phase F summary.
- **Partial** - some cues translate, some fight the chassis (e.g. vaporwave's wide tracking + airy density vs dense-mono's every-pixel-earns-its-keep). Build every cue that translates, push the rest as far as the chassis allows, and in Phase F name the one or two cues the chassis could not fully carry and why.
- **In tension** - aesthetic and style pull hard against each other. STILL apply the aesthetic to the maximum degree the chassis physically allows (never fall back to the bare template), AND in the Phase F report add a one-line note offering to swap the style for one that carries the aesthetic better. The decision is the user's; the default is "keep the aesthetic, flag the friction", never "silently keep the template".

The forbidden outcome in every case is shipping the style's native look with the committed aesthetic absent. If the aesthetic is genuinely impossible to express on the chosen chassis, say so explicitly and ask - do not decide it away.

## Phase C - Write source per Subagent 1 conventions

Standard source-write per `docs/agents/subagents/1-source.md`:

- Token block at the TOP of `styles.css` carries Phase A's locked palette + font vars + the genre-commit comment, in that order. **When `workflow/art-direction-contract.json` exists**, the surface/accent/ground token scale, the colour-use proportions across the UI, the type scale (`authored.typography.modularScale` / `displayToBodyRatio` / `lineHeight`), the spacing rhythm, the component treatment (`authored.componentStyle`), and the motion budget (`authored.motionCharacter`) all derive from the contract - not from the style detail file's defaults. The locked hexes/families still win where they conflict (precedence rung 1); the contract governs the ratios and rhythm between them. Do NOT reproduce the plate's literal composition - inherit its principles per `bindingRules`.
- `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?...">` in every page's `<head>` for the picked Google Fonts families.
- Pages link the DS stylesheet first (if a DS is present), then optional prototype overlay.
- Every visual slot is annotated for Subagent 1.V - `img-placeholder` with `data-asset-intent` for static imagery, `motion-placeholder` with `data-motion` for decorative loops (see PROTOTYPE.md → Slot annotations).
- The `data-asset-intent` and `data-motion` strings inherit the picked option's `<vibe>` + style detail file's mood. For an `acid-design` pick, slot intents read "neon-on-black acid graphics, distorted chrome, rave-flyer attitude" not "generic hero illustration".

`prototype.json` is written per the AGENTS.md schema (frames / arrows / lanes / entities) - same flow as the prior pipeline, the Step -1 ask doesn't change it.

## Phase D - Render-verify

Standard: every authored HTML opens and renders without console errors, navigation works, demo data is non-undefined. Fix any errors before Phase E. Screenshot or eval-snapshot to confirm clean state.

## Phase E - Post-build orchestrator dispatch

**Phase E is reachable ONLY after Phases A → B → C → D complete in this turn.** Orchestrators enumerate slots in *already-written source HTML*; they do not exist for pre-commit previews, +draft mockups, "show me an image" requests, or any other pre-build flow. If `source/<branch>/` has no files in it AND no Phase A lock has been written, every orchestrator listed below is **forbidden**. The agent in studio2 broke this by dispatching `visual-orchestrator` from inside the +draft loop - that's a Phase E rule violation and a category error.

After source is written and render-verified, the agent MUST walk the orchestrator dispatch chain - **restricted to the roster the user approved at the Phase A.5 plan gate**. Each orchestrator's gate is defined in its own manifest under `.claude/agents/<name>.manifest.json`, so the agent's job is sequencing, not gate-evaluation. Dispatch each APPROVED orchestrator via the `Task` tool with `subagent_type` matching the manifest's `subagentName`; skip unapproved ones even when their manifest gate would fire (the user said no). If the user picked `none`, Phase E is a no-op - go straight to Phase F and say so. Walk in this order:

1. **`photography-orchestrator`** - its manifest trigger: "fires when (a) at least one slot will resolve to raster-photo AND (b) an image-generation model is wired into the project". For the acid-design / scrapbook / editorial-warm-restraint family this almost always fires. The orchestrator picks a photo style from `docs/research/photography-library.md`, writes a `pe_photo_<slotId>` enrichment node per photographic slot. Visual-orchestrator reads these later.
2. **`illustration-orchestrator`** - same shape, for raster-foreground (illustrated subjects with transparency, mascots, vector-with-character). Fires for acid-design, corporate-memphis, kawaii, Y2K-memphis-loud, etc. Picks an illustration style from `docs/research/illustration-library.md`.
3. **`creative-visual-orchestrator`** - fires when the committed aesthetic is editorial-loud (acid-design, web-brutalism, y2k-memphis-loud, oversized-neo-grotesque, wacky-pomo, etc.). Promotes flat `<img>` slots into compositions (text-as-mask, asset-cut-into-letters, irregular-clip-path, asset-as-drop-cap). Optional but powerful for the loud register.
4. **`visual-orchestrator` (Subagent 1.V)** - **mandatory** unless `source/` has zero visual slots. Enumerates every slot, classifies the medium, scaffolds the per-asset node graph in `workflow/workflow.json`, dispatches per-asset drawers (raster-photo, raster-foreground, vector-mark, shader, particle-gl, lottie, 3d, video, motion). Reads the photo/illust enrichments from steps 1-2.
5. **`material-orchestrator`** - fires when the committed style is material-bearing per `docs/research/material-library.md` decision tree (skeuomorphism, glassmorphism, claymorphism, holographic-iridescent, neumorphism, frutiger-aero, brushed-metal, paper-grain, etc.). Adds reactive material fidelity (refraction on tilt, parallax on scroll, ripple on hover).
6. **`interactive-polish-orchestrator`** - fires when (a) a DS is present AND (b) the genre is in the restrained-register allow-list per its gate. Adds microanimations, pointer-driven effects, scroll-driven reveals, hover surprises, shader overlays.

For each APPROVED orchestrator, the agent **does NOT pre-evaluate the trigger** - that's the orchestrator's own job per its manifest. The agent dispatches with the standard envelope (project slug, sourceRoot, projectRoot, genre commit line); the orchestrator reads its manifest's gate against the source and either runs or returns `runStatus:error` if its conditions don't match. The agent moves to the next approved orchestrator regardless.

**`owns-surface` orchestrators (game-experience / simulation / motion-studio / interactive-media / narrative-experience / scrapbook-experience / scene-3d) dispatch in Phase E too, AND must be handed the contract.** When `workflow/art-direction-contract.json` exists, include `contractPath` (and the surface's own `surfaceContracts[<containerId>]` key) in their dispatch envelope. Their research step reads it and commits a register that is a TRANSLATION of the app's DNA (palette from the surface contract, motion bounded by it) - never an independent pick. That is the mechanism that keeps the playable/cinematic surface from forking into a second look.

**Late-add reconciliation (a different turn, not this build):** when a *later* "add a game / add a motion scene" ask approves an owns-surface orchestrator and a contract ALREADY exists from the first build, re-fire **Phase A.7 with `mode="revise"`** FIRST (art-director reads the prior contract, composes the new surface into the existing world, bumps `contractVersion`, and may emit `revisionNotes` for any chrome token to re-touch) - THEN dispatch the new owns-surface orchestrator against the revised contract. Do not dispatch the new surface against a contract that never anticipated it; that is exactly how the two halves diverged.

The acid-design studio case would propose steps 1, 2, 3, 4 pre-ticked (and likely offer 6 unticked) at the Phase A.5 gate - that's the orchestrator routing that worked before Step -1 was added, now run with the user's sign-off instead of silently.

## Phase F - Report done

After Phases A-E complete, summarise to the user: what was locked from the pick (palette + fonts + axes), and - when an aesthetic was committed - the Phase B.5 translation verdict (translatable / partial / in-tension), naming any aesthetic cue the chassis could not fully carry and, for an in-tension verdict, offering the style swap. The approved roster from the Phase A.5 gate, which orchestrators actually ran (with their reported outcomes - `kept N slots, dropped M`) and which self-gated to a no-op, and what's next (typically: "click Run on the workflow canvas to generate the per-asset bitmaps", or "the polish layer is live - refresh to see microanimations"). If the user picked `none`, say the build shipped CSS/SVG-only and which passes remain available on ask.

If any phase failed (Phase B detail-file missing, Phase C render error, Phase E orchestrator dispatch error), report it explicitly - don't claim "done" when the pipeline broke partway.
