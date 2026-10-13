# Typed judgment: Jev, Clef, OpenAI, and a visual tier

Status: BUILT, 2026-10-13. Extends `docs/features/jev-integration.md`; every invariant there (I1-I4, flag never block) still holds. See "What shipped" at the bottom for where the build differs from this plan and why.

**Request**
1. Extend Jev support to Clef (Cloudflare).
2. Extend Jev support to the OpenAI Decisions API.
3. Add a visual QA path that uses these classifiers.
4. Jev cannot take images, so each classifier gets its own level of support.
5. Jev may take images later, so that upgrade must be a small change.

## 1. UI

BEFORE - Settings -> Context and cost -> Typed judgment

```text
+---------------------------------------------------------------+
| Typed judgment                                                |
| A judgment model that answers many small typed questions ...  |
| [x] Use typed judgment for checks that support it             |
|     Applies to requirement QA, design-system conformance ...  |
| No TypeSafe key yet. Add one under Model Config, API keys ... |
+---------------------------------------------------------------+
```

AFTER - same section

```text
+---------------------------------------------------------------+
| Typed judgment                                                |
| A judgment model that answers many small typed questions ...  |
| [x] Use typed judgment for text checks                        |
|     Requirement QA, design-system conformance, direction ...  |
|     Judge                        [ Auto: TypeSafe Jev     v ] |
| [ ] Use typed judgment for visual checks                      |
|     Frame judge, sprite facing, visual requirement items ...  |
|     Judge                        [ Auto: Cloudflare Clef  v ] |
|     Mode                         [ Shadow                 v ] |
| Text: TypeSafe Jev. Images: Cloudflare Clef.                  |
+---------------------------------------------------------------+
```

BEFORE - Settings -> Model Config -> API keys (one row per provider, key + Test)

```text
| TypeSafe (Jev)     [ key ............ ] [Test]               |
```

AFTER - two new rows; a row's Test result also says whether it reads images

```text
| TypeSafe (Jev)     [ key ............ ] [Test]  Text only    |
| Cloudflare (Clef)  [ Account ID ..... ]                      |
|                    [ token .......... ] [Test]  Reads images |
| Local Clef         [ Endpoint ....... ] [Test]  Not checked  |
| OpenAI             [ key ............ ] [Test]  (existing)   |
```

## 2. Logic

Interface contract, fixed here so items 2 and 3 can build against it before item 1 lands:

- `typed_judge.judge(state, questions, tier="text"|"image", images=None, kind="default", provider=None) -> {answers, provider, model, tier}` with `answers` always in System One shape.
- `typed_judge.pick(tier) -> provider id | None` and `jev.ask(...)` keep their current signatures (`jev.py` becomes a shim).
- Config keys in compact-config: `jevJudge` (text on, existing), `typedJudgeVisual` (bool, false), `typedJudgeTextProvider` and `typedJudgeImageProvider` ("auto" or an id), `typedJudgeVisualMode` ("shadow" or "flag").
- `POST /__judge` body `{state, questions, kind?, tier?, images?: [{path}|{node}], provider?}` -> 200 `{ok, answers, thresholds, provider, model, tier}`, 503 `{reason: off|no-key|no-image-judge, hint}`, 400 for shape or limit errors; `/__jev` stays as an alias with `tier=text`.
- `GET /__judge/status` -> `{text: {id, name}|null, image: {id, name}|null, providers: [{id, name, keyed, maxImages, imagesVerified}]}` for the Settings rows.

| Trigger | What happens | State read or written | Edge case |
|---|---|---|---|
| A consumer asks for a text judgment | Router uses the chosen text provider if keyed, else the first keyed provider in the text `autoRank` | `compact-config.json`, `media-config.json`, `editor/judges.json` | Nothing keyed -> `JudgeUnavailable`, consumer keeps today's path |
| A consumer asks for an image judgment | Same routing, filtered to providers with `maxImages >= len(images)` and `imagesVerified != false` | `editor/judges.json`, media-config probe flags | None capable -> 503 `no-image-judge`, consumer keeps today's path |
| Chosen provider speaks System One (Jev, Clef, Local Clef) | Send the body as-is, images in an `images` array | - | Clef REST wraps the reply in `result`; `model` must be `clef` or `clef-flash` (error 5006 otherwise) |
| Chosen provider is OpenAI | Translate to `POST /v1/decisions`: questions map -> array with `name`, noul -> `predicate`, choice -> `choices[{value, description}]`, score -> `levels[{label, description}]`, images -> `input_image` data URLs | - | Object state is JSON-stringified; noul `criteria.true/false` is folded into `instructions` |
| OpenAI replies | Translate back: answers array -> map by `name`, `probability` -> `noul`, probability arrays -> maps, score keys -> level index, `legend` rebuilt from the request | - | A `refusal` answer is dropped, so the existing readers escalate it |
| A request carries images | Daemon loads `{path}` under the project root or a `{node}` asset, checks PNG/JPEG/WebP, downscales over 4 MiB or 16 MP, sends a base64 data URI | project files | Path outside the project root -> 400; oversize with no Pillow -> 400 naming the limit |
| Before any send | Validate against the chosen provider's caps (questions, options, levels, context, images) | `editor/judges.json` | A `null` cap means unpublished: not enforced locally, the API's 4xx comes back as 400 |
| User clicks Test on a judge row | One text noul; image-capable rows also send a solid red and a solid blue PNG with "The image is mostly red" and pass only when red is high and blue is low | writes `<provider>.imagesVerified` in media-config | Text passes but the probe fails -> the row says "Text only" and the image tier skips it |
| TypeSafe ships image input | Raise `maxImages` on the `jev` row in `editor/judges.json`; the next Test verifies it; Jev joins the image tier at its `autoRank` | `editor/judges.json` | No other code changes, asserted by test P7 |
| A consumer reads thresholds | Lookup order `providers[p][kind]`, then `providers[p].default`, then `kind`, then `default` | `editor/tools/qa/jev_thresholds.json` | Clef at 0.8 does not mean Jev at 0.8, so bands are per provider |
| `/__qa/run ...&checks=<json>` (or a `visual-checks.json` next to the target) with visual on | `visual_qa.py` asks one noul per check: a literal sentence about what is visible, with only the capture it names (plus an optional `compare` capture as image 1), cropped to its `selector` as it was at that moment | report `typedChecks` | A statement that restates intent or counts is rejected unasked; an element missing at that capture is reported without a model call; the `judge=` prose is never sent to the typed judge |
| Visual mode is Shadow | Typed verdict is recorded and the LLM verdict stands; one line is appended to the shadow log | `~/.test-harness/typed-judge-shadow.jsonl` | Log rotates at 5 MB |
| Visual mode is Flag | A confident typed FAIL adds a `typed-judge` finding next to the LLM verdict | QA report | Never removes or softens an LLM finding (I3); never blocks |
| Calibration set `trustPass` for (provider, kind) | A confident typed PASS skips the LLM call for that kind | `jev_thresholds.json` | Only `jev_calibrate.py` writes `trustPass`, never the UI |
| Animated-sprite facing gate runs with visual on | One noul per cell "The subject faces <facing>", up to 4 cells per request, Shadow or Flag as above | QA report | The describe-skill gate stays authoritative |
| Requirement QA Step 2b hits an item about what is visibly shown | Agent writes one literal check per item (statement in the requirement's nouns, the element's selector) and sends them with `/__qa/run page=...&checks=`; it never Reads the PNG | - | No `typedChecks` in the reply -> the item is judged the way it is today |
| `jev_calibrate.py` runs | Reads the shadow log, reports agreement per (provider, kind), and lists disagreements to label | shadow log, thresholds | Agreement is not accuracy; only the labelled set decides `trustPass` |
| Preamble is built | The typed-judgment block names the text judge, the image judge or "none", and which checks each covers | `editor/kinds/capabilities.py` | Toggles off -> block absent, P5 unchanged |

## 3. Copy

| New copy | Component | Dynamic value | Case | Type family |
|---|---|---|---|---|
| Use typed judgment for text checks | Typed judgment toggle label | - | Sentence | settings-guard-label |
| Requirement QA, design-system conformance and direction picking. Off, or with no judge set up, each keeps the behaviour it has today. | Text toggle hint | - | Sentence | settings-guard-hint |
| Use typed judgment for visual checks | Typed judgment toggle label | - | Sentence | settings-guard-label |
| Frame judge, sprite facing and visual requirement items. Shadow records its answer next to the current judge and changes nothing. Flag adds a finding when it is confident something failed. | Visual toggle hint | - | Sentence | settings-guard-hint |
| Judge | Provider select label | - | Sentence | workflow-default-provider-label |
| Auto: {name} | Provider select option | resolved provider name | - | - |
| Mode | Mode select label | - | Sentence | workflow-default-provider-label |
| Shadow / Flag | Mode select options | - | - | - |
| Text: {text}. Images: {image}. | Typed judgment status line | resolved names, or "none set up" | Sentence | workflow-settings-section-group-sub |
| No judge that reads images is set up. Add a Cloudflare or OpenAI key under Model Config, API keys. | Status line, no image judge | - | Sentence | workflow-settings-section-group-sub |
| Cloudflare (Clef) | API key row label | - | Title | provider row label |
| Typed judgment that also reads images. Needs your account ID and a token allowed to use Workers AI. | Cloudflare row hint | - | Sentence | provider row hint |
| Account ID | Cloudflare row field label | - | Sentence | provider row field |
| Local Clef | API key row label | - | Title | provider row label |
| Clef running on this computer through Ollama. No key, nothing leaves the machine. | Local Clef row hint | - | Sentence | provider row hint |
| Endpoint | Local Clef row field label | - | Sentence | provider row field |
| Reads images / Text only / Not checked | Row test result | probe result | Sentence | provider row status |

## 4. Split

Item 1 lands first; items 2 and 3 build against the interface contract above with a stubbed `typed_judge` and switch to the real one when it merges.

1. Provider-aware typed-judge client, provider table, image loading, the `/__judge` endpoint, key tests with the image probe, and per-provider thresholds.
   Owns: `editor/typed_judge.py`, `editor/judges.json`, `editor/jev.py`, `editor/tools/qa/jev_thresholds.json`, `editor/tools/qa/jev_calibrate.py`, `editor/tests/test_typed_judge.py`, `editor/tests/test_jev_client.py`, `editor/serve.py#_jev_run + /__judge, /__judge/status routes`, `editor/serve.py#_PROVIDER_ENV_KEYS`, `editor/serve.py#key test: typesafe/cloudflare/clef_local/openai branches`, `editor/serve.py#COMPACT_DEFAULTS + both compact save whitelists`
2. Settings: the Typed judgment section with two toggles, two provider selects, the mode select and the status line, plus the Cloudflare and Local Clef key rows with extra fields.
   Owns: `editor/app.js#WorkflowContextCostSection: Typed judgment group`, `editor/app.js#WorkflowProviderSection: provider.fields inputs + images status`, `editor/prompts/media-models.js#PROVIDERS: cloudflare, clef_local rows`
3. Visual consumers and agent-facing text: the frame judge, the sprite facing gate, requirement QA visual items, the preamble block, and the doc amendment.
   Owns: `editor/tools/qa/visual_qa.py#run_judge + typed path`, `editor/serve.py#_qa_run: typed judge flags`, `editor/serve.py#animated-sprite _vision_judge`, `docs/agents/requirement-qa.md#Step 2b`, `editor/kinds/capabilities.py#JEV_FAST_PATH_STUB, _jev_enabled, /__jev roster line`, `editor/tests/test_jev_parity.py`, `docs/features/jev-integration.md#Rejected: the image path`

Left out: lens-trio pre-screen - rubric questions are the ~74% accuracy case from the rejected-image notes; revisit after calibration.
Left out: direction picking from `design-library/*-ui.png` previews - 4 images per request against 130 aesthetics.
Left out: OpenRouter's Decisions endpoint as one key for Jev and Clef - alpha, shape unpublished.
Left out: the CSSOM render dump - still the right tool for overlap, contrast and overflow, separate work.

## Reference: provider tiers (`editor/judges.json`)

`null` = not published; not enforced locally.

| id | wire | key | model | maxImages | maxQuestions | choice options | context | $/M input | autoRank text / image |
|---|---|---|---|---|---|---|---|---|---|
| jev | systemone | typesafe | `jev-latest` | 0 | null | 255 | 64k | 0.042 | 1 / 5 (inert while maxImages is 0) |
| clef | systemone, CF REST | cloudflare (token + account ID) | `clef` | 4 | 64 | 255 | 65,536 incl. images | 0.24 | 3 / 1 |
| clef-flash | systemone, CF REST | cloudflare | `clef-flash` | 4 | 64 | 255 | 24,576 incl. images | 0.038 | 2 / 2 |
| clef-local | systemone | none (endpoint) | `clef` | 4, unverified | 64 | 26 | null | 0 | 5 / 4 |
| openai | openai-decisions | openai (existing) | `gpt-6-luna` | null | null | null | null | 0.10 | 4 / 3 |

Unverified until the first live call per provider (none has been made, Jev included):

- Clef's `images[]` entries: the Workers AI schema accepts a data URL or `{content_type, base64}` (Woven sends data URLs); Ollama's Local Clef takes raw base64 only. Set per row by `imageEncoding` in `editor/judges.json`.
- The Clef REST `result` wrapper is the generic Workers AI envelope; the Clef model page itself shows no response.
- OpenAI publishes no limits for questions, options or images.
- A forum report says OpenAI `choice` skews toward the top option while `predicate` stays calibrated; calibration decides, not this note.
- Whether Local Clef through Ollama reads images.

Sources: [Cloudflare blog](https://blog.cloudflare.com/clef-decision-models/), [Workers AI Clef model page](https://developers.cloudflare.com/workers-ai/models/clef/), [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions), [TypeSafe API](https://docs.typesafe.ai/api), [eesel on Clef](https://www.eesel.ai/blog/cloudflare-clef), [OpenAI forum](https://community.openai.com/t/decisions-api-is-now-available-in-public-beta/1403877).

```json
{"items": [
  {"title": "Typed judge: providers, tiers, /__judge",
   "owns": ["editor/typed_judge.py", "editor/judges.json", "editor/jev.py", "editor/tools/qa/jev_thresholds.json", "editor/tools/qa/jev_calibrate.py", "editor/tests/test_typed_judge.py", "editor/tests/test_jev_client.py", "editor/serve.py#_jev_run + /__judge, /__judge/status routes", "editor/serve.py#_PROVIDER_ENV_KEYS", "editor/serve.py#key test: typesafe/cloudflare/clef_local/openai branches", "editor/serve.py#COMPACT_DEFAULTS + both compact save whitelists"],
   "brief": "Make Woven's typed-judgment client provider-aware. Read docs/features/typed-judgment-providers.md (Logic, Reference) and docs/features/jev-integration.md first. Build editor/typed_judge.py (stdlib only, Python 3.9-safe, run editor/check-compat.sh): judge(state, questions, tier, images, kind, provider) returning {answers, provider, model, tier} with answers ALWAYS in System One shape, pick(tier), and adapters for wire 'systemone' (Jev at api.typesafe.ai/v1/systemone; Clef at api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/{clef|clef-flash} with the reply unwrapped from `result`; Local Clef at a configured endpoint, default http://localhost:11434/v1/systemone) and wire 'openai-decisions' (POST https://api.openai.com/v1/decisions, model gpt-6-luna; translate questions map -> array with name, noul -> predicate with criteria folded into instructions, choice -> choices[{value,description}], score -> levels[{label,description}], images -> input_image data URLs inside one user message; translate answers back, dropping refusals). Provider capabilities live in editor/judges.json per the Reference table; null caps are not enforced. Routing: chosen provider from compact-config typedJudgeTextProvider / typedJudgeImageProvider when keyed and capable, else first keyed in autoRank; the image tier filters on maxImages >= len(images) and imagesVerified != false. Images: {path} confined to the project root or {node} asset, PNG/JPEG/WebP only, downscale over 4 MiB or 16 MP with Pillow when present, else 400. Turn editor/jev.py into a shim that keeps ask/noul_pass/choice_ranked/confidence/band/thresholds/enabled/available and JevError/JevUnavailable working for ds_lint and existing tests. Thresholds: add a `providers` level to jev_thresholds.json with lookup providers[p][kind] -> providers[p].default -> kind -> default, plus an optional trustPass flag; extend jev_calibrate.py to read ~/.test-harness/typed-judge-shadow.jsonl and report agreement per (provider, kind) with a disagreement list. In editor/serve.py: rename _jev_run to _judge_run serving POST /__judge (body {state, questions, kind?, tier?, images?, provider?}; 503 reasons off|no-key|no-image-judge; 400 for shape/limits) and keep /__jev as an alias with tier=text; add GET /__judge/status returning {text, image, providers:[{id,name,keyed,maxImages,imagesVerified}]}; add `cloudflare` to _PROVIDER_ENV_KEYS (token, with account_id read from media-config); add key-test branches: one text noul for every judge, and for image-capable ones a red and a blue solid PNG with noul 'The image is mostly red', passing only when red >= 0.8 and blue <= 0.2, writing <provider>.imagesVerified to media-config; add compact-config keys typedJudgeVisual (false), typedJudgeTextProvider ('auto'), typedJudgeImageProvider ('auto'), typedJudgeVisualMode ('shadow') to COMPACT_DEFAULTS and both save whitelists (string keys validated against allowed values). Tests on recorded fixtures, no network: adapter round-trip (P6: an OpenAI fixture translates to the same reader outputs as the System One fixture), routing (P7: raising jev maxImages in a test copy of judges.json puts Jev in the image tier with no other change), degradation per provider (P4: absent key, 401, exhausted 429, malformed body all fall back). Siblings own: app.js / media-models.js (item 2); visual_qa.py, serve.py _qa_run and animated-sprite _vision_judge, requirement-qa.md, capabilities.py, test_jev_parity.py, jev-integration.md (item 3). Never start or restart the daemon. Done = all tests green, check-compat passes, existing test_jev_parity.py still green."},
  {"title": "Typed judgment Settings: tiers + judge key rows",
   "owns": ["editor/app.js#WorkflowContextCostSection: Typed judgment group", "editor/app.js#WorkflowProviderSection: provider.fields inputs + images status", "editor/prompts/media-models.js#PROVIDERS: cloudflare, clef_local rows"],
   "brief": "Update the Settings UI for multi-provider typed judgment. Read docs/features/typed-judgment-providers.md sections UI and Copy and use their wireframes and strings exactly; no em or en dashes anywhere, no emoji, no pills, compact single rows. In editor/app.js WorkflowContextCostSection, replace the single Typed judgment toggle with: toggle jevJudge labelled 'Use typed judgment for text checks' plus a 'Judge' select bound to typedJudgeTextProvider; toggle typedJudgeVisual labelled 'Use typed judgment for visual checks' plus a 'Judge' select bound to typedJudgeImageProvider and a 'Mode' select bound to typedJudgeVisualMode (Shadow, Flag); and a status line 'Text: {name}. Images: {name}.' or the no-image-judge sentence. Selects list 'Auto: {resolved name}' first, then only keyed providers capable of that tier, read from GET /__judge/status ({text:{id,name}|null, image:{id,name}|null, providers:[{id,name,keyed,maxImages,imagesVerified}]}); reuse the existing workflow-default-provider-row markup and save() from useContextCostConfig. In editor/prompts/media-models.js PROVIDERS add `cloudflare` (label 'Cloudflare (Clef)', fields [{key:'account_id', label:'Account ID'}], testable) and `clef_local` (label 'Local Clef', no key, fields [{key:'endpoint', label:'Endpoint', default:'http://localhost:11434/v1/systemone'}], testable). In WorkflowProviderSection render any provider.fields as extra inputs saved into that provider's media-config entry, and show the test result's image status as 'Reads images', 'Text only' or 'Not checked' from imagesVerified. Until item 1 merges, stub /__judge/status with the shape above. Siblings own: typed_judge.py, judges.json, jev.py, serve.py judge routes/keys/COMPACT_DEFAULTS (item 1); visual_qa.py, capabilities.py, requirement-qa.md, test_jev_parity.py (item 3). Verify in the browser preview against a static server, never by starting the daemon; check both light and dark editor themes. Done = both sections match the AFTER wireframes, toggles and selects persist across reload, and a provider with no key never appears in a select."},
  {"title": "Visual typed judgment: frame judge, sprites, req QA",
   "owns": ["editor/tools/qa/visual_qa.py#run_judge + typed path", "editor/serve.py#_qa_run: typed judge flags", "editor/serve.py#animated-sprite _vision_judge", "docs/agents/requirement-qa.md#Step 2b", "editor/kinds/capabilities.py#JEV_FAST_PATH_STUB, _jev_enabled, /__jev roster line", "editor/tests/test_jev_parity.py", "docs/features/jev-integration.md#Rejected: the image path"],
   "brief": "Wire the image tier of typed judgment into Woven's visual checks. Read docs/features/typed-judgment-providers.md (Logic rows from '/__qa/run' down) and docs/features/jev-integration.md (invariants I1-I4, Rejected: the image path). Use typed_judge.judge(..., tier='image', images=[...], kind=...) and typed_judge.pick('image'); until item 1 merges, stub them. Read config typedJudgeVisual (bool) and typedJudgeVisualMode ('shadow'|'flag') from ~/.test-harness/compact-config.json. (a) editor/tools/qa/visual_qa.py run_judge: when visual is on and an image judge exists, send up to 4 key frames (idle start, most-motion idle, before, after) as separate images with one noul 'The frames show this effect: <expected>', kind 'frame_effect'; store the result in judge.typed {provider, noul, band}; the LLM frame judge ALWAYS still runs unless jev_thresholds.json has trustPass for (provider, frame_effect) and the typed pass is confident; Shadow records only and appends one JSON line {ts, provider, kind, noul, llmOk, project} to ~/.test-harness/typed-judge-shadow.jsonl (rotate at 5 MB); Flag additionally adds a 'typed-judge' finding on a confident fail, never removing or softening an LLM finding, never changing the exit code. editor/serve.py _qa_run passes the needed flags. (b) editor/serve.py animated-sprite _vision_judge facing gate: same Shadow/Flag treatment with one noul per cell 'The subject faces <facing>', up to 4 cells per request, kind 'sprite_facing'; the describe-skill verdict stays authoritative. (c) docs/agents/requirement-qa.md Step 2b: items about what is visibly shown are judged by rendering with GET /__qa/run page=, then POST /__judge tier=image with the frame path in images; the agent must never Read the PNG (the visual-delegation hook denies it in the main thread); a 503 no-image-judge means judge the item the way it is judged today. (d) editor/kinds/capabilities.py: the typed-judgment block names the active text judge and image judge (or 'none') and which checks each covers; the /__jev roster line becomes /__judge with tier and images, noting /__jev still works; the block stays absent when both toggles are off. (e) editor/tests/test_jev_parity.py: keep P1-P5 green, add P8 asserting Shadow mode never changes visual_qa's exit code or LLM verdict on recorded fixtures. (f) In jev-integration.md, amend 'Rejected: the image path': native-vision judges remove the adapter objection; the base-rate objection stands and is answered by Shadow -> Flag -> calibrated trustPass. Geometry and colour stay deterministic; lens-trio and direction-picking are out of scope. No em or en dashes. Siblings own: typed_judge.py, judges.json, jev.py, thresholds, calibrate, serve.py judge routes/keys/COMPACT_DEFAULTS (item 1); app.js, media-models.js (item 2). Never start or restart the daemon. Done = tests green on fixtures, check-compat passes, and a /__qa/run with judge= on a fixture page shows judge.typed in Shadow without changing the verdict."}
]}
```

## What shipped

Every item is in the tree. Tests: `editor/tests/test_typed_judge.py` (routing, both wires, P4 per provider, P6, P7, limits, images, the key-row probe, thresholds, the shadow log, calibration, and the daemon routes through the real handlers), `editor/tests/test_jev_parity.py` (P1-P5, plus P8), `editor/tests/test_jev_client.py`, `editor/tests/test-jev-settings.cjs` (Playwright, both settings sections). An end-to-end run of the real `visual_qa.py` against a local fake judge showed Shadow and Flag leave the verdict and exit code untouched, with 4 key frames sent.

| piece | where |
|---|---|
| router, both wires, images, probe, thresholds, shadow log | `editor/typed_judge.py` |
| provider table | `editor/judges.json` |
| text-check shim (`ask`, readers, `enabled`, `available`) | `editor/jev.py` |
| `POST /__judge`, `POST /__jev` alias, `GET /__judge/status` | `_judge_run` and the GET route in `editor/serve.py` |
| keys, fields, key-row Test with the image probe | `_PROVIDER_ENV_KEYS`, `_JUDGE_FIELDS`, `_media_config_get/_set/_test` in `editor/serve.py` |
| settings keys | `COMPACT_DEFAULTS` and both whitelists in `editor/serve.py`, validated by `typed_judge.valid_setting` |
| Settings UI | `WorkflowContextCostSection`, `useJudgeStatus`, `WorkflowProviderSection` in `editor/app.js`; `cloudflare`, `clef_local` in `editor/prompts/media-models.js` |
| check shapes, option lists, field table | `editor/visual_checks.py` |
| visual checks | `parse_checks`, `capture_boxes`, `run_visual_checks`, `apply_frame_judges` in `editor/tools/qa/visual_qa.py`; `--checks` and `--typed-judge` passed by `_qa_run` |
| DS off-system judgment | `off_system_units`, `run_jev_pass` in `editor/tools/qa/ds_lint.py`; `skin` per component in `ds_contract.py` |
| asset checks | `expect` on `POST /__asset_generate` in `editor/serve.py` |
| sprite checks | `_typed_fields` beside `_vision_judge` in `editor/serve.py` (facing on every frame, endState on the last, same character first vs last); results in the node run's `typedChecks` |
| requirement QA visual items | Step 2b in `docs/agents/requirement-qa.md` |
| preamble | `typed_judgment_block`, `_typed_judgment_state` in `editor/kinds/capabilities.py` |
| calibration | `--shadow`, per-provider bands, `--trust-pass` in `editor/tools/qa/jev_calibrate.py` |

### Where the build differs from this plan, and why

- **Numbers from the published docs replace the plan's.** Clef Flash holds 24,576 tokens (not 64k) at $0.038/M input. Clef and Clef Flash take 2-255 choice options and 2-10 score levels; Local Clef takes 2-26 of each and raw base64 images. Cloudflare's "wrong model" error is not 5006 (undocumented); its error table lists 5007 for an unknown model. A System One score answer indexes its levels from 0 (`legend` and `probabilities` keyed `"0"`, `"1"`, ...); the OpenAI adapter rebuilds that shape and passes `score` through rather than deriving a scale nobody published.
- **Jev has an image rank (5) already.** The table said "-", but then raising `maxImages` alone could not put Jev in the image tier, which is what P7 asserts. Rank 5 is inert while `maxImages` is 0.
- **Auto skips a judge the request does not fit.** Direction picking sends ~50k tokens and a 130-option choice; Clef Flash and Local Clef would refuse it. Auto now tries the next judge whose caps the request fits, and only when none fits does the first usable one answer, so its limit still comes back as the 400 the plan specifies. A configured choice that does not fit falls through to Auto the same way.
- **The typed judge never gets the frame judge's prose (changed 2026-10-13, after review).** The plan's one noul, "The frames show this effect: <expected>", gave a classifier nothing to classify: "expected" is not visible. It is replaced by CHECKS: literal statements, each tied to the capture it is about and cropped to its element at that moment, with vague restatements of intent and counts rejected before any call (P8). With no checks, the typed judge does not run on frames at all; the LLM frame judge keeps the prose.
- **The DS judgment finds invented UI by STYLING and judges it against the whole vocabulary (changed 2026-10-13, after review).** The first live Clef call was refused at 231k characters: the whole contract as state plus all 99 options repeated in every element's question. A first fix scoped each element to 1-3 components picked from linter evidence; that was wrong, because an invented component follows neither our naming nor our structure, so it skipped exactly what the guard is for. Now, only under `--jev`: every styling source that paints an element from outside the design system (any page or linked prototype CSS rule, any selector shape, any inline style, `:hover`/`::before` merged into their base) is one unit. Stage 1 asks every unit, with no cap, a choice over three fixed options (ds-copy / new-ui / layout), the component names travelling once per request in state. Stage 2 asks only confident ds-copy units which component, over EVERY component of the same family (control / overlay / box) plus none-of-these: what each component IS travels once per request in the state, and each option is its short title. "What it is" is the authors' own text, now derived into the contract as `description` (+ `title`): the component's gallery.html section paragraph plus the indented body of its DESIGN.md entry. The old `oneLine` kept only an entry's first line, which is usually the selector list ("Card .card [--plain|--filled]"); it is unchanged for its existing readers. suss: 66 of 123 substantial components carry a description. Batches run 4 at a time. suss-cal fa-application.html: 13 units, one 1-request stage 1. With the classifier off the linter's output is unchanged (verified on suss-cal: the same 335 findings).
- **Questions are built from shapes, never written (changed 2026-10-13, after review).** `editor/visual_checks.py` holds the sentence shapes (shows, changed, same_as, intact, subject_is, which), the closed option lists (direction, position, empty_area, control_state, ds_origin) and the FIELD_RULES table that turns a stored field (facing, endState, alt, subject, cutout, subjectPosition, quietZone) into a check. Page checks name a shape and `x`; the sprite gate and `POST /__asset_generate` (`expect: {...}`) build checks from fields the caller already has. A field with no rule, or a value that cannot be graded, produces no check.
- **Each screen keeps its own criteria, asked in one call per screenshot (added 2026-10-13).** Visual QA screenshots each screen and checks it against that screen's criteria. They live in `source/<prototype>/visual-checks.json`: `pages["<page>.html"]` for one screen, top-level `checks` for every screen, each check optionally tagged with its `source` (requirement, story, change). The agent that builds or changes a screen writes or updates its entry from the requirement items that apply, the user stories mapped to it in `docs/story-map.json`, and what its change must show (the typed-judgment preamble block says so when visual checks are on). Every `/__qa/run` of that page loads them (`_page_visual_checks` in `serve.py`), and `run_visual_checks` asks every criterion that shares the same images (the screenshot, or one element's crop) in ONE request, up to 64 per call.
- **Every typed answer is logged, labelled by id (added 2026-10-13).** The DS check writes kinds `ds_origin` and `ds_component` to `~/.test-harness/typed-judge-shadow.jsonl` with the element's evidence, probabilities, confidence and band, and returns them in the lint report's `jev.judged`. `jev_calibrate.py --log` lists them, `--label ID=ANSWER` records the right answer in `typed-judge-labels.json`, and `--fit-log --write` sets the provider's own band from the labelled rows. First live run (suss-cal, Clef): sensible answers, but Clef's confidences (max 0.88) all sat under the pre-calibration 0.90 bar, so nothing was promoted; that bar is what the log exists to calibrate.
- **QA frames are allowed outside the project root.** `/__qa/run` writes frames to a `woven-qa-*` temp directory, so "path outside the project root -> 400" would have refused the one image requirement QA is told to send. That one daemon-made directory is allowed; anything else outside the project is still a 400.
- **A pinned judge ignores a failed probe.** The key-row Test is itself a pinned call; if a failed probe excluded the judge, it could never be re-verified. A pin still respects `maxImages: 0`.
- **trustPass only acts in Flag mode.** Shadow "changes nothing" by definition, so a calibrated trustPass never skips the LLM call there.
- **The OpenAI key row never fails because Decisions did.** The key serves generation and text too; the Decisions probe only fills the judge status, and the row shows no image status until a Test has checked it.
- **Local Clef is set up by a saved endpoint.** A default endpoint alone would have Auto calling localhost on every install. A successful Test at the default endpoint saves it.
- **The shadow log is written in Flag mode too.** Both modes produce the calibration pairs; lines with no LLM verdict are kept but skipped by `jev_calibrate.py --shadow`.
- **The sprite gate checks more frames than the describe gate.** The base plate, then up to the first 4 sheet frames in one request. Findings go in the node run's `typedJudge`; the describe gate stays the only thing that rejects a sheet.

