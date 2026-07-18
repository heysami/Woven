# Visual QA harness

A standalone dev tool that verifies an interactive piece actually ACHIEVES ITS
EFFECT. Instead of a single screenshot, it samples an idle timeline AND a
battery of simulated interactions, then measures per-frame pixel change to tell
the difference between a piece that animates / reacts and one that is static,
ignores input, or errors out.

This is a dev tool, NOT shipped editor runtime code. It uses Playwright with
system Chrome (channel="chrome") so no browser download is needed. It does not
touch, start, or restart the Woven daemon.

## Requirements

- Python 3 with `playwright` importable (`python3 -m pip install playwright`).
- Google Chrome installed (used via `channel="chrome"`). If that launch fails,
  the harness falls back to Playwright's bundled chromium and reports which it
  used.
- Optional for better diff precision: Pillow (`PIL`) or numpy. If neither is
  usable it falls back to a coarse raw-PNG-bytes diff (reduced precision) and
  says so. It never crashes on a missing optional dependency.

The source is Python 3.9-safe (`from __future__ import annotations`, no 3.10+
syntax), so it can live alongside the rest of `editor/` which runs on 3.9.

## Usage

```
python3 editor/tools/qa/visual_qa.py --url <url-or-file> \
    [--mode interactive|render] \
    [--spec <spec.json>] [--out <dir>] [--viewport 1280x720] \
    [--settle-ms 300] [--no-interact] \
    [--judge "<expected effect>"] \
    [--judge-daemon <base-url> --judge-project <id>] \
    [--judge-provider anthropic|openai] [--judge-model <id>]
```

- `--mode`       What "working" means for this target (default `interactive`):
                 - `interactive` - the piece must ANIMATE or REACT. A static,
                   motionless result fails as `static`. Use for a single baked
                   interactive node (its isolated runtime).
                 - `render` - a COMPOSED page/app surface must RENDER correctly.
                   A correctly painted static page PASSES; a blank / unstyled
                   flat wash fails as `blank` (the broken-imports failure). The
                   interaction battery is skipped unless `--spec` supplies steps.
                 Either mode pairs with `--judge` to also check the RIGHT thing
                 rendered.

- `--url`        URL (http/https) or a local path / file:// URL. A bare path is
                 resolved to an absolute file:// URL.
- `--spec`       Optional JSON spec (see below) for custom interactions/timing.
- `--out`        Output directory for the frame strip + report.json
                 (default: `./qa-out`).
- `--viewport`   `WIDTHxHEIGHT`, default `1280x720`.
- `--settle-ms`  Delay after navigation before the t=0 idle frame
                 (default 300).
- `--no-interact` Skip the interaction battery (idle timeline only). With this
                 flag the verdict is derived from idle animation alone.
- `--judge`      OPTIONAL LLM frame-judge. Pass a plain-English description of
                 the intended effect (e.g. `"a shape moves"`,
                 `"the chart bars grow when clicked"`). The harness montages a
                 labeled frame strip and asks a vision LLM whether the captured
                 behaviour matches. Fail-soft: if no LLM is reachable the run
                 still completes on the pixel-diff verdict. See the frame-judge
                 section below.
- `--judge-daemon` Base URL of an ALREADY-RUNNING Woven daemon (e.g.
                 `http://localhost:5747`) to route the judge through its
                 `/__llm_run` describe endpoint. Requires `--judge-project`.
                 This tool NEVER starts or restarts the daemon.
- `--judge-project` Project id stamped onto the daemon `/__llm_run` call
                 (required by `--judge-daemon`).
- `--judge-provider` Provider for the daemon describe call (`anthropic` default
                 or `openai`). Ignored by the direct-API fallback, which is
                 always Anthropic.
- `--judge-model` Vision model id (default `claude-sonnet-4-6` for the direct
                 API; the daemon picks its own default if omitted).

Output: the full JSON report is printed to stdout AND written to
`<out>/report.json`. Every captured frame is a PNG in `<out>/` so a human or an
agent can also judge the piece visually. The frame strip is part of the
deliverable.

Exit code: `0` for `pass`, nonzero otherwise (`1` static / no-reaction, `2`
error, `3` setup failure such as Playwright/Chrome missing, `4` effect-wrong
from the `--judge` frame-judge). This makes it CI / agent friendly. The full
exit-code table is under "Verdict semantics" below.

## What it does

1. Launch headless Chrome via Playwright at the requested viewport. Collect
   console errors and uncaught page errors for the whole run.
2. Navigate to the URL (waits for DOM content + a short settle).
3. IDLE TIMELINE: screenshots at t = 0, 0.3, 0.7, 1.2, 2.0 s with NO input.
4. INTERACTION BATTERY (unless `--no-interact`): either the steps from `--spec`,
   or an AUTO battery over the main stage (largest `<canvas>`, else `<body>`):
   a 6-point pointer sweep, a center click, a drag across, a scroll, and an
   arrow key. Each step captures a BEFORE and AFTER frame with a small settle.
5. PIXEL DIFF: for consecutive idle frames and for each interaction
   before/after pair, downsample to ~160px-wide grayscale and compute the
   fraction of pixels whose delta exceeds the threshold.
6. VERDICT + JSON report (below).

## Verdict semantics

- `error`       Any uncaught page error or severe console error was seen.
- `static`      No idle animation AND (no interaction reaction, or interaction
                was disabled). Nothing renders or moves.
- `no-reaction` Idle may animate, but interaction caused effectively no change
                when interaction was expected. The piece ignores input.
- `pass`        It animates and/or reacts to input (interactive mode), or it
                rendered real content without errors (render mode).
- `blank`       RENDER MODE ONLY. The page loaded but painted a blank / flat
                uniform frame - nothing real rendered. Usually broken CSS/JS
                imports (e.g. a missing `?project` stamp so the design-system
                `@import`s 404) or a script bailout. Navigation "succeeded" and
                no error was thrown, yet the surface is empty/unstyled.
- `effect-wrong` Pixels DID move (or the page rendered), but the optional
                `--judge` frame-judge said the intended effect / content was NOT
                achieved. Only reachable when `--judge` is supplied and ran.

### Exit codes

- `0`  `pass`
- `1`  `static` / `no-reaction`
- `2`  `error`
- `3`  setup failure (Playwright / Chrome missing, bad spec)
- `4`  `effect-wrong` (pixels moved but the frame-judge rejected the effect)
- `5`  `blank` (render mode: loaded but painted nothing / an unstyled wash)
- `6`  `cases-fail` (--cases mode: a planned test case, the harness-contract
       preflight, or the soak failed)

### Thresholds (documented + tunable in the source)

- `PIXEL_DELTA_THRESHOLD = 18` per-pixel grayscale delta (0..255) above which a
  pixel counts as changed. Filters anti-aliasing / sub-pixel noise.
- `DIFF_EPSILON = 0.005` fraction of changed pixels below which a frame pair is
  treated as effectively identical (noise floor). A pair must exceed this to
  count as "animated" or "reacted".
- `DIFF_WIDTH = 160` downsample width for the comparison.

These are conservative: a real animation or a shape following the cursor moves
far more than 0.5% of the frame, while static AA jitter stays under it.

## Spec format

A spec JSON may set any of:

```json
{
  "idleTimes": [0.0, 0.3, 0.7, 1.2, 2.0],
  "settleMs": 300,
  "interactSettleMs": 250,
  "interactions": [
    { "type": "move",   "x": 200, "y": 200, "label": "hover" },
    { "type": "click",  "x": 640, "y": 360 },
    { "type": "drag",   "x": 100, "y": 100, "x2": 900, "y2": 500 },
    { "type": "scroll", "x": 640, "y": 360, "deltaY": 400 },
    { "type": "key",    "key": "ArrowRight" }
  ]
}
```

Step types: `move` (x,y), `click` (x,y), `drag` (x,y -> x2,y2), `scroll`
(deltaY, optional x,y to position the pointer first), `key` (key). Coordinates
are CSS pixels in the viewport. `label` is optional and used in frame
filenames. If `interactions` is omitted, the AUTO battery runs.

## Pointing it at a Woven piece

Two ways:

1. A local file: pass the path to a baked runtime HTML, e.g.
   `--url editor/.../runtime.html`. Note that a baked piece whose CSS/JS use
   `?project=` stamped imports may need to be served by the daemon to resolve
   those imports; a raw file:// load can miss them.
2. A served URL: the Woven daemon serves the IN USE workspace at
   `http://localhost:5747`. Point `--url` at the node's runtime URL there. Do
   NOT start or restart the daemon from this tool; only use it if it is already
   running.

### The easy path: the daemon `/__qa/*` endpoints

You usually do not invoke this script by hand. An ALREADY-RUNNING Woven daemon
exposes two endpoints (see `serve.py` `_qa_resolve_url` / `_qa_run`) that resolve
a target to the exact daemon-served URL the editor renders, then run this script
for you and return the report JSON:

```
GET $TH_DAEMON_URL/__qa/resolve?project=<id>&node=<nodeId>     # isolated piece
GET $TH_DAEMON_URL/__qa/resolve?project=<id>&page=<slug|path>  # composed surface
GET $TH_DAEMON_URL/__qa/run?project=<id>&node=<nodeId>[&judge=<text>]
GET $TH_DAEMON_URL/__qa/run?project=<id>&page=<slug>[&judge=<text>][&mode=render]
```

- `node=<id>` resolves `node.bakedPath` to `/<bakedPath>?project=<id>` and
  defaults to `mode=interactive`.
- `page=<slug>` resolves to `/source/<slug>/index.html?project=<id>` (or a
  relative `<slug>/<file>.html`) and defaults to `mode=render`. Because it
  serves through the daemon with the `?project=` stamp, the design-system
  imports resolve EXACTLY as they do in the editor iframe - this is the
  realistic "how it appears in the app" view, not a raw `file://` or a separate
  preview server that would 404 the DS CSS and render unstyled.
- `&mode=interactive|render` overrides the per-target default; `&judge=<text>`
  forwards to `--judge`; `&nointeract=1` forwards to `--no-interact`.

The endpoint NEVER starts the daemon; it runs inside the daemon process you
already have up. The capabilities preamble surfaces this to every spawned
builder agent under "Verify your visual work before you tell the user it is
done", so agents verify a deliverable instead of self-certifying it.

## LLM frame-judge (`--judge`)

The pixel-diff verdict answers "did anything move / react?" but not "did the
RIGHT thing render?". A piece can animate vigorously while showing the wrong
content. The optional `--judge` frame-judge closes that gap with a vision LLM.

### What it does

1. After frames are captured, it assembles a compact FRAME STRIP: it picks a
   representative set (the first idle frame, the two idle frames with the most
   motion, and the BEFORE/AFTER of the interaction step with the largest pixel
   change), downscales each, labels each tile with its moment (`t=0.70s`,
   `before click_center`, `after click_center`, etc.), and montages them into
   ONE image saved as `<out>/judge_strip.png`. (If Pillow is unavailable it
   falls back to sending the picked frames as an ordered list of images.)
2. It sends the strip plus the expectation to a vision LLM with a prompt that
   asks: given these frames over time and before/after interaction, and the
   intended effect `<expected>`, did the piece achieve it? Reply strict JSON
   `{ok, reasoning, observed}`.
3. It merges a `judge` block into the report and adjusts the verdict per the
   precedence below.

### Transport order (first reachable wins)

1. **Daemon LLM.** If you pass `--judge-daemon <base-url> --judge-project <id>`,
   the strip is POSTed to that already-running daemon's `/__llm_run` endpoint
   with `skill=describe` and `provider=<--judge-provider>` (the strip rides as
   an `input_data_uri` data URL). The harness never starts the daemon; it only
   talks to one you tell it is already up. The daemon supplies the API key /
   CLI auth, so no local key is needed on this path.
2. **Direct Anthropic API.** If the daemon path is not configured (or fails),
   the harness reads an Anthropic key from `~/.test-harness/media-config.json`
   (the `anthropic.api_key` field) and calls the Anthropic Messages API
   directly over `urllib` (no SDK) with a vision model
   (`claude-sonnet-4-6` by default, override with `--judge-model`).
3. **Unavailable.** If neither is reachable (no daemon configured, no key, or an
   LLM/network error), the judge is UNAVAILABLE: `judge.available=false` with a
   clear message. The run still completes and the pixel-diff verdict is
   unchanged. The strip is still saved either way.

### Verdict precedence

The judge only ESCALATES or CONFIRMS; it never relaxes a worse pixel verdict.

- judge **unavailable**  -> verdict unchanged (pixel-diff stands).
- judge **ok:false**     -> verdict becomes `effect-wrong` (exit code `4`), but
                            ONLY when the pixel verdict was `pass`. An existing
                            `error` / `static` / `no-reaction` is a stronger
                            signal and is kept.
- judge **ok:true**      -> CONFIRMS; verdict unchanged (a `pass` stays `pass`).
- judge **inconclusive** (LLM reply not parseable as JSON) -> verdict unchanged,
                            noted in `reasons` and `judge.message`.

### The `judge` block

```json
{
  "available": true,
  "ok": false,
  "reasoning": "why the model decided",
  "observed": "what the frames actually show",
  "expected": "a shape moves",
  "stripPath": "<out>/judge_strip.png",
  "model": "claude-sonnet-4-6",
  "transport": "direct anthropic api",
  "message": "judge ran via direct anthropic api"
}
```

When unavailable, `available` is `false`, `ok`/`reasoning`/`observed` are
`null`, and `message` explains why (and confirms the strip was still saved).

## Report shape

```json
{
  "url": "...",
  "browser": "chrome (channel=chrome)",
  "viewport": "1280x720",
  "diffBackend": "pillow",
  "idleFrames":   [ { "t": 0.0, "path": "...", "diffFromPrev": null }, ... ],
  "interactions": [ { "step": "click_center", "type": "click",
                      "beforePath": "...", "afterPath": "...",
                      "diff": 0.0 }, ... ],
  "consoleErrors": [],
  "pageErrors":    [],
  "metrics": { "maxIdleDiff": 0.0, "maxInteractionDiff": 0.0,
               "pixelDeltaThreshold": 18, "diffEpsilon": 0.005 },
  "verdict": "pass",
  "reasons": [ "..." ],
  "judge": { "available": false, "ok": null, "stripPath": "...", ... }
}
```

The `judge` block is present only when `--judge` was supplied. See the
frame-judge section above for its shape.

## Test-cases mode (`--cases <test-cases.json>`)

Runs a piece's PLAN-TIME test cases instead of the idle timeline + generic
battery. The file is written by the family researcher when the piece is
planned (design: `docs/features/qa-test-cases.md`) and lives next to the
piece's `research.md`. Every case runs end to end on a FRESH page; then the
auto-expanded intent x phase matrix, the applied abuse templates, and a
seeded soak (random-but-replayable inputs).

```
python3 visual_qa.py --url <url> --cases <path>/test-cases.json --out <dir>
```

Self-test fixture: `fixtures/cases-demo.html` +
`fixtures/cases-demo.test-cases.json`.

- Step types: the raw five (`move` `click` `drag` `scroll` `key`) plus
  `intent` (harness `injectFakeInput`), `eval`, `waitFor`, `tick`
  (deterministic fast-forward), `settle`, `resize`.
- Expect types: `noPageErrors` (implicit on EVERY case), `noConsoleErrors`
  (optional `allow` regex list), `eval` (+ `equals` / `in` / `truthy`),
  `notBlank`, `frameChanged`.
- Matrix: `"matrix": {"auto": true}` expands `phases` x `intents`, driving
  each phase via its `phaseSetups` entry; `phaseExpr` (optional) asserts the
  piece is still in a known phase afterwards. `exclude: [[intent, phase]]`
  skips pairs.
- Abuse templates: `"abuse": {"apply": [...], "phase": "..."}` with
  `spam-intents`, `pointer-storm`, `resize-cycle`, `long-idle`.
- Soak: `"soak": {"seconds": 45, "seed": 1337, "fastForward": true,
  "phase": "...", "optsPool": {"<intent>": [{...}, ...]}}`. Reproducible by
  seed.
- Preflight: the harness global must exist, `injectFakeInput` must be a
  function, and (when the harness publishes `intents`) every intent in the
  file must be covered. A gap FAILS the run - it is a runtime-composer
  contract violation, not a skip.
- Report: `report.json` gains `cases[]` (per-case verdict + failedExpect +
  pageErrors + frames), `preflight`, `soak`, and `casesSummary`. Verdict is
  `pass` or `cases-fail` (exit 6). A failed case entry IS the reproduction
  recipe.
- Budget: each case is capped by its `budgetMs` (default 8000) so a freeze
  fails fast instead of hanging the run.

Daemon route: `/__qa/run` auto-detects a `test-cases.json` next to the
resolved target (same dir or one level up) and runs cases mode by default;
pass `&cases=0` to force the generic battery. EXCEPTION - game targets
(`games/<id>/runtime.html`): no cases file is a HARD FAIL (no opt-out), and
cases mode additionally runs the deterministic seam test (facing vs travel,
anim clock, harness contract) per `docs/agents/game-seam-contract.md`.
