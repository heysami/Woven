# Art direction: finalize

Requires the user's chosenPlate. Read the chosen full-resolution plate again,
then follow the crop, observation, and assembly steps below. The plate is a
source of principles, not a screenshot to reproduce.

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

## 4.5 Phase C.5 - (mode: finalize) DETECT + crop the reference regions FIRST - this is the close-read that grounds the contract

Runs in the `mode: "finalize"` dispatch (the caller re-dispatched you with `chosenPlate: <n>` after the pick). **Crop BEFORE you author the contract (§4.6), not after.** Isolating the real objects IS the inspection: you cannot write an accurate `extracted` (palette ratios, composition, material, type construction) or a useful `crossSurfaceContract` from a vague overall glance - you write it from having actually cut out and examined the person, the UI, and the key items. So detect + crop here, then author the contract in §4.6 from what you found.

**What to crop - in PRIORITY order. The two highest-value references are the ones the old pass skipped: the human subject and the UI sample. Do NOT bias toward discrete text stickers/wordmarks just because they are easy to box.**

1. **The human subject(s)** - if the product is people-centred (artist / founder / performer / character), the person is THE most important reference. Crop tight to the figure and rembg it. This becomes the i2i identity reference for the hero / portrait / press raster-photo slots, so the shipped people-photos are the same person as the approved plate. `role: "subject"`, `matchesSlots: [hero-portrait, about-portrait, ...]`.
2. **The UI / chrome sample** - the nav + hero lockup + a primary card + the primary button, as one rectangular crop (NO rembg - keep the layout intact). This is the composition + component ground-truth: the build's layout/components step and the final aesthetic-lens read it as "this is how the UI should look". `role: "ui"`, `matchesSlots: []` (it is not an image-gen input; it is a build/lens reference).
2b. **Game-direction extras (game / pixel / retro / sci-fi-HUD plates only).** Beyond the whole-UI sample, ALSO cut each framed chrome element as its own TIGHT crop - the dialog frame, one button, the HP/status panel - each boxed exactly to its frame (NO rembg; the frame must stay intact). These are slice9 atlas sources: downstream cuts them into `border-image` pieces with `editor/slice9_detect.py`, so the shipped chrome is literally the approved plate's frames. `role: "chrome-frame"`, one crop per distinct frame construction. And for every creature / character / avatar crop you take under 1/3, prefer the cleanest whole-body pose-neutral view in the plate - those crops seed `animated-sprite` walk/idle sheets, and a cropped-off or mid-action subject makes a poor cycle base.
3. **Key identity / product items** - a mascot, the logo mark, an album object, the product itself. rembg each. i2i references for their matching raster slots. `role: "item"`.
4. **Decorative items** (stickers, badges, starbursts) - LAST, and only the few that genuinely recur as their own slots. Most decoration is reproduced by the build in CSS/SVG and does NOT need a crop; do not fill the references with text badges.

Skip the i2i crops (subject/item/decoration) when the image model is not i2i-capable (provider `openai`, gpt-image-1 family) - leaving `itemReferences` empty of those; the `ui` crop is a build/lens reference, not an image-gen input, so take it regardless. For each crop:

```bash
# crop (writes under source/ - the only tree the gen endpoint reads/writes)
python3 -c "from PIL import Image; Image.open('$TH_PROJECT_ROOT/workflow/artdirection/north-star-<chosen>.png').crop((L,T,R,B)).save('$TH_PROJECT_ROOT/source/<branch>/_artdir_refs/<id>.raw.png')"
# rembg ONLY for subject/item crops (isolate the figure); SKIP rembg for the ui crop (keep layout). Both paths project-root-relative under source/:
curl -fsS -X POST "$TH_DAEMON_URL/__asset_generate?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "skill":"rembg","provider":"local","model":"u2net",
  "input_path":"source/<branch>/_artdir_refs/<id>.raw.png",
  "output":"source/<branch>/_artdir_refs/<id>.png"}'
```

**Verify each crop landed on the right region** before trusting it - Read back the output and confirm it shows the intended person / UI / item cleanly; re-crop with a corrected bbox if not. A bad bbox both wastes the reference AND poisons the contract you are about to write from it. `source/<branch>/_artdir_refs/` is the right home: it is the only tree the gen endpoint can write AND the only tree downstream `raster-foreground` reads as `input_path`.

## 4.6 Phase C.6 - (mode: finalize) author + write the contract, GROUNDED in the §4.5 crops

Read `$TH_PROTOCOL_ROOT/docs/agents/art-direction-contract.md`. Now author the project-specific contract decisions from the chosen plate, using the crops you just took as the close-read: `extracted` palette/ratios/value/material/composition read off the real isolated regions (the UI crop tells you the component + composition truth; the subject crop tells you the human register), `typeConstruction` off the rendered display/body text, `authored` harmonised with all of it. **This is the first write to disk for the direction.** Also author `buildRegister` here from the CHOSEN plate, same derivation discipline as the rest of the contract: derive the build-brief vocabulary from the plate + each downstream slot's actual behaviour (name each thing by its craft/model, not its look), set the `cadence` the plate implies, and keep the `antiVoice` guards - ship the METHOD, never a fixed word list. This governs the language of build briefs, NOT shipped copy (that is `voice`). Set `platePath` = the chosen plate, `candidatesConsidered` = the set, and populate `itemReferences[]` from §4.5 - each `{ itemId, role: "subject"|"ui"|"item"|"decoration", refPath, matchesSlots, bboxNote }`. **When §4.7 qualifies (envelope `motionPlates: true` + video provider wired + at least one motion-benefiting owns-surface), run §4.7's clip generation + inspection BEFORE this write** so each `surfaceContracts[*].motionPlate` is populated in the same single write. Use the shared writer protocol in
`$TH_PROTOCOL_ROOT/docs/agents/contract-writer.md`. Save these decisions once as
compact notes in the existing schema at `workflow/art-direction-decisions.json`.
Call `/__context/writer/prepare` with this orchestrator's ID, that draft path,
`outputPath: "workflow/art-direction-contract.json"`, and only the narrative
`prosePaths` (for example `/crossSurfaceContract/colorUsePrinciple` and
`/authored/componentStyle/recipeNotes`). The writer has its own configured model;
this orchestrator still owns every observation, choice, and exact value. Review
its returned edits, then publish the accepted paths through
`/__context/writer/publish`. Shared contract fields are assembled by code.
Do not send the writer font resolution, palette values, paths, approvals,
exceptions, or promised formats. Keep required approval and crop checks above.
For revisions, supply the prior contract hash per the writer protocol. A 409
means another writer changed the contract: read and reconcile before retrying.
Do not weaken the schema or overwrite a newer contract to pass validation.
Because finalize only runs after a `plate-<n>` pick, no stale contract is ever left for a steered/rejected direction.

Downstream consumption is by `role`: entries with a non-empty `matchesSlots` (subject / item / recurring decoration) are i2i references - the illustration/photography enrichers copy `refPath` into the matched slot's `refImagePath`, visual-orchestrator carries it onto the skill node, raster-foreground POSTs it as `input_path`. The `role: "ui"` entry has no `matchesSlots`; the build's component/layout step and the aesthetic-lens read it as the composition ground-truth. No new plumbing.

## Optional motion inspection

If motionPlates is true, a video provider is available, and an approved surface is
narrative-experience, game-experience, interactive-media, motion-studio, or scene-3d,
read `$TH_PROTOCOL_ROOT/docs/agents/art-direction-motion.md` and complete it before
assembling the contract. Otherwise skip video entirely.

## 5. Phase D - (mode: finalize) wire the contract node into the build chain

Runs in the `mode: "finalize"` dispatch, after §4.5/§4.6. The plate image node(s) `ad_plate_<projectId>_<n>` already exist on the canvas (you committed them in §2 at generation time, so the user saw the plate at the gate). This phase adds the **contract** node and the edges. Two failures to avoid:

1. **The node kind must render the plate.** `kind: "art-direction"` (and `folder` / `section`) have **no thumbnail renderer** - the node draws empty. Commit the contract as a real **image asset node** (`kind: "asset"`, `assetKind: "image"`, `path` = the chosen plate). The canvas asset-node card renders any served `path` as a thumbnail; the daemon serves `workflow/artdirection/…png`. This is the ONLY kind that shows the picture.
2. **The node must be edge-wired, not orphaned.** Without edges the node floats free of the prototype chain - which is why it looked like "something happened but nothing connected." Add edges: each plate node → the contract node, and the contract node → the prototype node.

Use the **race-safe append** route (`POST /__workflow/nodes/add`) - it appends under the project lock without clobbering concurrent writers, and is idempotent on re-POST.

**Do NOT invent x/y.** Omit coordinates on every node you add (here and in §2): the daemon lays a coordinate-less batch out as a left-to-right chain, reading the order off your own `addEdges`, then finds it empty canvas - so the plate, the contract and the downstream research nodes land as a readable row instead of stacked on the origin. Hand-picked coordinates are written verbatim and are how nodes end up on top of each other. If you want a batch beside a SPECIFIC node, pass `"anchorId": "<nodeId>", "placement": "anchor"` rather than coordinates; an edge from an existing node into your batch already anchors it automatically.

```bash
# Discover the prototype node id to wire the contract into the build chain.
PROTO_ID=$(curl -fsS "$TH_DAEMON_URL/__workflow?project=$TH_PROJECT_ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((n['id'] for n in d.get('nodes',[]) if n.get('kind')=='prototype'), ''))")

curl -fsS -X POST "$TH_DAEMON_URL/__workflow/nodes/add?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "addNodes": [{
    "id": "ad_contract_<projectId>",
    "kind": "asset",
    "assetKind": "image",
    "title": "Art direction - north-star plate",
    "path": "workflow/artdirection/north-star-<chosen>.png",
    "projectId": "<project>",
    "platePath": "workflow/artdirection/north-star-<chosen>.png",
    "contractPath": "workflow/art-direction-contract.json",
    "boundTo": { "documentSetId": "<branch>" },
    "runStatus": "done",
    "outputs": { "contractPath": "workflow/art-direction-contract.json" }
  }],
  "addEdges": [
    { "from": "ad_plate_<projectId>_1", "to": "ad_contract_<projectId>" },
    { "from": "ad_plate_<projectId>_2", "to": "ad_contract_<projectId>" }
    // ...one per plate node you created in §2...
    // PLUS, only if PROTO_ID is non-empty, append: { "from": "ad_contract_<projectId>", "to": "<PROTO_ID>" }
  ]
}'
```

Emit the `ad_contract_<projectId>` → `<PROTO_ID>` edge only when `PROTO_ID` resolved (the prototype node may not exist yet at pre-build time; if it doesn't, the contract still renders its plate, and the build wires the contract by reading `workflow/art-direction-contract.json` regardless). Duplicate ids/edges are skipped, so re-running is safe.

`platePath` + `contractPath` stay on the node so downstream lookups keep working; the visible difference is purely that the node now draws the plate and connects into the graph.

## Return to the caller

Return orchestrator, mode, projectId, branch, contractPath, platePath, sha256,
changedFields (revisions only), and any unresolved exceptions. Do not repeat the
contract, implementation instructions, or consumer wiring lists. The build reads
the contract as its authority; consumers retrieve only the fields they need.
