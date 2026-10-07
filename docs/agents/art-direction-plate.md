## 2. Phase A - generate the north-star plate(s)

The plate is a **finished-product key visual of the intended total world**: a single composed frame showing UI chrome and imagery *together* in their final relationship - the way an art director paints one hero frame before the team builds the system. Not a moodboard collage; not a single isolated illustration. It must answer in pixels: *what does this whole product look and feel like when the chrome and the magic share one frame?*

- **VERIFY the direction against the DISK LEDGER before you count plates - never trust the caller's claim alone.** The dispatch prompt's "no direction committed" is a PREMISE composed by a thread that may never have read the project ledger (observed: a post-handoff working thread claimed no direction while `DECISION_prototype-direction.json` held the user's locked pick, and the resulting candidate set ignored the chosen style). Before deciding ONE-vs-candidates, read from the project root: `DECISION_prototype-direction.json` (the user's locked direction pick), `pipeline.json` (may carry the locked direction), and any DS binding. A committed direction found on disk = `committedDirection` IS SET, no matter what your dispatch prompt says - the ledger outranks the caller.
- **ONE plate is the default when the user already picked a direction.** The decisive signal is `committedDirection` being set - i.e. the user chose from the quick `prototype-direction` picker (the 3-options aesthetic/shell/style cards), OR a `committedAesthetic` library slug was chosen, OR `dsRef` is set. **Any one of these means the look is already chosen** and the art-director is NOT a place to re-choose it. A generated direction option (e.g. "Sticker-chaos maximalism") counts exactly the same as a library slug - do NOT require `committedAesthetic` to be non-null; `committedDirection` alone is enough. Generate a SINGLE plate that realises the picked direction and surface it for approve / steer / regenerate. Do NOT fan out to a candidate set just to populate the gate, and do NOT diverge on `tensionAxis` - the pick already resolved it.
- **A CANDIDATE SET of 2-3 plates ONLY when no direction was picked at all** - i.e. `committedDirection` is null AND `committedAesthetic` is null AND `dsRef` is null (the rare path: a free-form brief that never went through the direction picker). Only then give the user a real *box of visual choices*, diverging on `tensionAxis` when set, else the next most load-bearing variable (palette temperature, value key, focal density).
- **HARD INVARIANT (count-based, reason-agnostic):** if `committedDirection` (or `committedAesthetic` or `dsRef`) is set, you generate **exactly ONE plate, no matter the reason you think you need more.** This is a check on the *number* of plates, not on *why*. Before generating, count your intended plates; if the count is >1 while a direction is committed, STOP and collapse to ONE. The forbidden reasons explicitly include: (a) look-variants diverging on `tensionAxis`, AND (b) **surface-split - one plate per surface** (e.g. an in-game view + a title screen, or one plate per `approvedOwnsSurface` entry). Multiple surfaces are composed into a **single composite frame** (split-frame / inset / hero-plus-thumbnail), never one plate each. The only things that raise the count above 1 are `committedDirection == null` (a true candidate set) or an explicit "show me options" request (see Override).
- **Override:** an explicit user request for a single key visual always forces ONE plate; an explicit request to "show me options" forces the set even when a direction is committed.
- Cost is a few image calls, paid once, before the expensive build - cheap relative to what the contract anchors.

**Generate each plate DIRECTLY via `/__asset_generate` - do NOT co-dispatch visual-orchestrator.** Co-dispatching another orchestrator as a workflow node and `/run`-ing it from inside this subagent stalls (nested dispatch is unreliable in a subagent session). Generate the raster yourself in one call. **The endpoint only writes under `source/`** (`editor/serve.py` - output must start with `source/`), so generate there, then copy to the canonical served planning path `workflow/artdirection/`, then commit the plate as a real **image asset node** so it actually appears on the canvas (not a false "it's on canvas" claim):

```bash
# 1. generate (output MUST be under source/)
curl -fsS -X POST "$TH_DAEMON_URL/__asset_generate?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "skill":"generate-image","provider":"openai",
  "aspect":"<16:10 desktop | 9:16 mobile>","prompt":"<the full plate brief - see below>",
  "output":"source/<branch>/_artdir/north-star-<n>.png"}'
# OMIT "model" so the daemon applies the user-default image model. NEVER hardcode
# gpt-image-1 / guess from memory: the default is surfaced at GET /__capabilities
# `defaultImageModel` (and the capabilities preamble's "Image generation DEFAULT"
# row) - currently {id: gpt-image-2, provider: openai}. Set "model" only if the
# user named a specific one for this project.
# 2. copy to the canonical served planning location (servable: translate_path roots project-relative GETs at the project)
cp "$TH_PROJECT_ROOT/source/<branch>/_artdir/north-star-<n>.png" "$TH_PROJECT_ROOT/workflow/artdirection/north-star-<n>.png"
# 3. commit the plate as an image asset node on the canvas NOW (race-safe append) - so the user sees it immediately
curl -fsS -X POST "$TH_DAEMON_URL/__workflow/nodes/add?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "addNodes": [{"id":"ad_plate_<projectId>_<n>","kind":"asset","assetKind":"image",
    "title":"North-star plate <n>","path":"workflow/artdirection/north-star-<n>.png",
    "projectId":"<project>","runStatus":"done"}]}'
# on a generation failure: one retry with a corrected prompt; still no bytes → runError (cannot inspect blind)
```

**Plate brief** merges, in order: (1) the product surface drawn as a real screen - representative chrome (a header, primary content, one primary action, nav hinted) at true scale; (2) the hero imagery in its actual relationship to that chrome; (3) **for each entry in `approvedOwnsSurface`, compose that surface INTO the frame** in its real relationship to the chrome (e.g. a playable game panel sitting inside the home screen, a cinematic scene bleeding behind the nav) - so the plate shows the owns-surface region and the chrome as ONE composition, not the chrome alone; (4) the brief's `styleCue` + `sensoryTargets` as the visual register; (5) composition law - "one composed frame, edge to edge, no device mockup frame, no browser chrome, real words not lorem"; (6) negatives - no watermark, no stock-dashboard UI, no collage, no letterbox.

**The human subject is mandatory when the product is about people.** If the brief's subject is a person or people (artist, musician, founder, creator, performer, author, team, character - any product whose identity IS a human), a real human MUST be present in the plate, **prominently**, rendered in the committed register (real photography when the register is photographic; the genre's illustration register when it is illustration-only) - and the plate DECIDES WHERE the person lives in the composition (hero portrait, candid, press frame). A people-centred product whose north-star frame shows only chrome, product, or a mascot is a FAILED plate: the build inherits the plate's DNA, so a personless plate yields a personless site - the bug where an artist's site ships with a chrome wordmark and a mascot and not one human pixel. When in doubt about a human subject, put the human in.

**Game chrome is FRAMED RASTER chrome when the direction is game / pixel / retro / sci-fi-HUD.** For those directions the chrome idiom is the raster 9-slice frame (`slice9` - see the capabilities preamble): ornate/bevelled dialog frames, framed command menus, gold-trimmed buttons - the register of real game UI, NOT generic flat web panels. Paint the plate's chrome that way: the plate is the single source every downstream chrome decision inherits, so a plate with flat rectangles condemns the build to flat CSS imitation chrome, while a plate with real framed game chrome gets CUT INTO the shipped 9-slice atlases (§4.5) - the shipped frames ARE the approved art. Know also that downstream builds animate: creatures / characters / avatars in a game plate become `animated-sprite` sheets (walk / idle cycles redrawn pose-by-pose from YOUR reference crops), so depict them clean, whole and pose-neutral - a half-occluded or mid-action subject makes a poor cycle base.

Plates live under `workflow/artdirection/` - they are **planning artefacts, never shipped.** The runtime references none of them - and that covers the generation copy under `source/<branch>/_artdir/` and the crops under `_artdir_refs/` too: living inside the served source tree does NOT make them runtime assets (the observed bug: the grandauto / battle-team title screens shipped `<img src="_artdir/north-star-1.png">` as keyart - a flattened fake UI with a literal hero, fake stat numbers and painted HUD panels behind the real UI). A shell that wants keyart commissions a dedicated asset i2i-conditioned on the plate. This rule ships in the contract as `bindingRules.plateIsNotAnAsset` (§3) so every downstream builder reads it - do not leave it implicit here. (Contrast `ms-concept-frames`, whose plates double as i2v references; yours do not.)

## 3. Inspect the actual plates

Read each plate. For the gate, record palette chips and their relative use,
value structure, light, material, composition and density, observed display/body
letterform construction, audience and copy register, and reference-worthy regions.
Distinguish what the pixels show from authored decisions such as easing or type scale.
Keep only palette, type sample, vibe, and one reason in each gate card.
Do not read the full contract schema or write the contract in this phase.
Do not crop or generate video before approval. Finalization revisits the selected
plate at full detail. Gate preview notes are not a substitute for that inspection.

### 3.1 Match typography to the construction the plate ACTUALLY rendered

The image model draws the headline in whatever letterforms it invents - frequently a taller / more condensed / heavier interpretation than the family the brief named. The contract used to lock the abstract family (`Archivo Black`) while the plate, and every baked-lettering asset that inherits the plate's DNA (album covers, stickers, posters), shipped a condensed-and-tall variant. The chrome web-font then rendered standard-width and the aesthetic-lens flagged the two type surfaces as incoherent - when the condensed read was the better one all along. Close that:

1. **OBSERVE** the rendered construction into `extracted.typeConstruction` - width, weight, stroke contrast, case, slant, roundness - for both the display and body text the plate shows. You are already looking at the pixels; read the letterforms, not the brief's words.
2. **RESOLVE** `authored.typography.familyResolution` to the web-available family + variant/axis that realises that construction. If the named family has no matching axis, switch to the sibling that does: a static `Archivo Black` has no width axis, so a condensed-tall plate resolves to `Archivo` variable at high weight + reduced width (`wght 800 / wdth 75`), or `Archivo Narrow`; an extended plate resolves to `Archivo Expanded`. Same logic for round / italic / high-contrast reads - pick the variant, not the abstract name.
3. If no web font matches the observed construction, say so in `constructionMatch` and pick the nearest - **never silently keep the standard-width family** while the plate ships condensed. The scale / tracking / line-height / case stay authored; only the family + variant is now construction-bound.

### 3.2 Reference crops are DECLARED here, PRODUCED after the gate (§4.5), and the contract is authored FROM them (§4.6)

The plate's own rendering of the **human subject**, the **UI sample**, and the **key items** are the references that most improve the build: the subject crop is the i2i identity reference for the hero/portrait photos, the UI crop is the composition/component ground-truth, and item crops keep generated assets on the approved sample. These are far more valuable than discrete text stickers - do not let the easy-to-box text objects crowd them out.

**But do NOT crop anything in Phase B.** Cropping is real work (file writes + rembg) and must not run before the pick - it would spend on the agent's *recommended* plate, which the user may reject, before the §4 cost gate. So in Phase B you only **note in prose** which regions (subject / UI / items) look reference-worthy, as part of your steer summary at the gate. Leave `itemReferences: []`. The crops are produced in **§4.5, after the pick, from the CHOSEN plate** - and the contract is then authored in §4.6 GROUNDED in those crops (crop first, so the contract is an observation, not a glance).

### 3.3 Voice: copy speaks to the AUDIENCE, not the build team

The contract governs the copy register too, not only the visuals - because the same failure that stitches two visual halves together also ships copy that answers the *instruction* instead of addressing the *reader*. The tell: shipped strings that read like a reply to the brief ("A clean, modern landing page for a developer-analytics tool", "This section showcases the key features") instead of product copy a real person is meant to read ("Ship when the data says ship."). Copy that narrates the build to a development team is the copywriting equivalent of a personless plate.

You already have the sample: the plate was generated with **real words, not lorem** (§2 composition law #5). So, same motion as §3.1's typography reconciliation - OBSERVE, then author:

1. **OBSERVE** the register the plate's rendered copy implies (terse/warm/cocky/measured) → `voice.toneWords`, and name the real end reader the product serves → `voice.audience` (the fan, the buyer, the operator - never "the development team" / "the client" / "whoever wrote the brief").
2. **AUTHOR** `voice.addressPrinciple` (copy talks TO that audience about THEIR world, never back at the brief) and `voice.copyAntiPatterns` (instruction-echo, meta-narration, dev-team/spec address, lorem, mechanism-not-benefit).
3. This binds downstream: **step-content** writes every leaf against `voice` (audience + tone + budgets), and the **final QA gate runs a copywriting pass** - any string that answers the instruction rather than the reader is a fail, the copy sibling of the aesthetic-lens's cross-register diff.

## 4. Phase C - human steerage gate (§12.5) - emitted by the CALLER, not you

This is the cost gate the whole orchestrator earns. **You are a subagent - you CANNOT render this gate yourself.** A subagent's output is returned to the caller as a tool result; the chat only renders an interactive `<direction-options>` card from the **main loop's** output stream. If you "emit" the gate from here it is swallowed and the user sees nothing (or, worse, you fall back to describing the plate in prose with a file path, which renders no image) - that is the exact "agent says the plate is ready but nothing shows" failure. This is the same split motion-studio uses for its concept-plate gate: the subagent returns the gate, **the caller surfaces it.**

So: **do not emit the gate. RETURN the `<direction-options>` block below verbatim in your Phase E hand-off** (field `gateBlock`). The caller pastes it into the chat as-is, where it renders; the caller waits for the pick and then re-dispatches you with `mode: "finalize"` + `chosenPlate`.

**The block must be `<direction-options>`, NOT `<decision-request>`.** The chat only renders inline images + palette chips + type samples from `<direction-options>`'s per-`<opt>` `<image>` / `<palette>` children; a `<decision-request>` body is never parsed and any image in it is silently discarded. One `<opt>` per plate you generated. The plate `src` is the on-disk path `workflow/artdirection/north-star-<n>.png` - the daemon serves project-relative paths (`translate_path` roots them at the project), so it resolves.

```xml
<direction-options id="art_direction_<projectId>" prompt="Art direction: pick the north-star plate the whole app gets built from - chrome and imagery from one source. Cost so far: <N> image-gen call(s); the build has not started.">
  <!-- ONE <opt> per plate you generated. The card renders <image> + <palette> chips + the type sample. -->
  <opt value="plate-1" recommended>
    <label>Candidate 1 - <2-4 word handle for this direction></label>
    <image src="workflow/artdirection/north-star-1.png" alt="North-star plate 1"/>
    <palette><up to 6 extracted hexes, space-separated, focal/accent LAST></palette>
    <display font="<display family>"><a 2-4 word display sample in this plate's register></display>
    <body font="<body family>"><a short body sample></body>
    <vibe><moodWords - what the plate actually evokes></vibe>
    <why><one line: the value structure + focal strategy this candidate commits></why>
  </opt>
  <opt value="plate-2">
    <label>Candidate 2 - <handle></label>
    <image src="workflow/artdirection/north-star-2.png" alt="North-star plate 2"/>
    <palette><hexes></palette>
    <display font="<family>"><sample></display>
    <body font="<family>"><sample></body>
    <vibe><moodWords></vibe>
    <why><how it diverges from candidate 1 - name the axis (tensionAxis / palette / value key / density)></why>
  </opt>
  <!-- ...one <opt> per remaining plate (cap 3)... -->
  <opt value="steer"><label>Steer - adjust palette / type / register / the divergence axis; I regenerate the plate(s)</label></opt>
  <opt value="reject"><label>Reject - skip art direction, build from the text-only committed aesthetic</label></opt>
</direction-options>
```

**The CALLER** (not you) waits for `[decision:art_direction_<projectId>] <value>` and acts:
- `plate-<n>` → re-dispatches YOU with `mode: "finalize"`, `chosenPlate: <n>` → you run §4.5 + §4.6 + §5.
- `steer` → re-dispatches YOU with `mode: "plate"` + the correction → you regenerate the plate(s) and return a fresh gate. Nothing was committed.
- `reject` → the build proceeds text-only as today; you are not re-dispatched.

In your `mode: "plate"` dispatch you STOP after returning the `gateBlock`. You author NO contract and crop NOTHING - those happen only in the `mode: "finalize"` dispatch, after the pick. A single-plate set still uses `<direction-options>` (one plate `<opt>` + steer + reject) - never `<decision-request>`. Approval covers THIS build pass.

**Motion plates are a USER DECISION, not an auto-spend.** When `GET /__capabilities` reports a non-empty `videoModels` AND `approvedOwnsSurface` contains at least one motion-benefiting family (motion roster: narrative-experience, game-experience, interactive-media, motion-studio, scene-3d), ALSO return a second card in the hand-off (`motionGateBlock`, alongside `gateBlock`) asking whether to lock each such surface's motion feel with a short video, or stay stills-only. The caller emits it right after the plate gate and threads the answer into the finalize dispatch as `motionPlates: true|false`. When either eligibility condition fails, set `motionGateBlock: null` - do NOT ask a question the capability cannot honour.

```xml
<direction-options id="art_direction_motion_<projectId>" prompt="Motion plates: also lock the MOTION feel of <surface name(s)> with one short generated video each (~4s, i2v from the plate you pick), or keep art direction stills-only? Video cost: ~<N> clip(s).">
  <opt value="motion-plates" recommended>
    <label>Motion plates - one ~4s clip per <surface name(s)>; you approve pacing/energy in pixels before the build</label>
  </opt>
  <opt value="stills-only">
    <label>Stills only - the still plate binds look; motion registers stay prose-briefed (free)</label>
  </opt>
</direction-options>
```

Recommend `motion-plates` by default (the temporal register is what the still cannot lock); recommend `stills-only` instead when the brief is budget-sensitive or the motion-benefiting surface is minor. The recommendation is advisory - the pick is the user's.

## 6.5 Revise mode - a late-added owns-surface (the realistic "add a game to my finished app")

When `mode == "revise"`, a contract already exists and the user has just approved an owns-surface orchestrator that the original contract did NOT anticipate (it wasn't in the first build's roster). Do NOT fork - reconcile:

1. Read `priorContractPath`. Treat its `extracted` + `authored` + `crossSurfaceContract` as **the established law** - you are extending it, not re-deriving it. The chrome already shipped against it; gratuitous churn re-breaks the app.
2. Generate ONE new plate that places the **new** surface into the EXISTING world (reuse the established palette/material/type - the plate's job here is to prove the new surface can live in the current frame, not to redesign).
3. Generate + commit the revise plate node, inspect it, and **RETURN the gate block to the caller** exactly as `mode: "plate"` does (§4) - including the §4 `motionGateBlock` when the NEW surface is motion-benefiting (motion roster: narrative-experience, game-experience, interactive-media, motion-studio, scene-3d) and a video provider is wired - you cannot surface the gate yourself. Prepare (in memory, carried in the hand-off) the revised contract: `contractVersion` bumped (+1) and a new/updated `surfaceContracts["<newContainerId>"]` entry. Keep `extracted`/`authored` stable unless the new surface genuinely forces a small, named change - and if it does, record it in a `revisionNotes` array ("raised glow accent ratio 0.10→0.15 so the game surface and the chrome share a focal energy").
4. The caller surfaces the revised plate at the gate, waits for the pick, and re-dispatches you `mode: "finalize"`. **Only then** do you write the bumped contract to `workflow/art-direction-contract.json` (overwriting the prior version) - never before the pick, exactly as the create-path §4.6 rule (crop in §4.5, write in §4.6). Then the newly-added owns-surface orchestrator reads the bumped contract; if `revisionNotes` is non-empty, the caller re-touches the affected chrome tokens.

This is why the contract is **versioned, not write-once**: as soon as an owns-surface can be added after the build (and it always can), reconciliation requires a living contract.

## Return to the caller

Return orchestrator, mode, projectId, platesGenerated, gateBlock, and motionGateBlock
(null when ineligible). Include only unresolved choices or generation failures as notes.
The caller emits both eligible gate blocks verbatim and waits for the user's picks.
The common playbook defines the approved finalize, steer, and reject transitions.
No contract, crop, or video is written by this dispatch.
