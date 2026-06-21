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
    [--spec <spec.json>] [--out <dir>] [--viewport 1280x720] \
    [--settle-ms 300] [--no-interact]
```

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

Output: the full JSON report is printed to stdout AND written to
`<out>/report.json`. Every captured frame is a PNG in `<out>/` so a human or an
agent can also judge the piece visually. The frame strip is part of the
deliverable.

Exit code: `0` for `pass`, nonzero otherwise (`1` static / no-reaction, `2`
error, `3` setup failure such as Playwright/Chrome missing). This makes it
CI / agent friendly.

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
- `pass`        It animates and/or reacts to input.

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

This v1 verifies a single URL you hand it. The NEXT phase is to resolve a
Woven node id to its served runtime URL automatically, and to auto-trigger this
harness during a build so a piece that "did not achieve its effect" is caught
before it ships. An optional further step is an LLM frame-judge that looks at
the saved frame strip to catch effects that move pixels but are still wrong
(e.g. animates but renders the wrong thing).

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
  "reasons": [ "..." ]
}
```
