#!/usr/bin/env python3
"""Visual QA harness for Woven interactive pieces.

Standalone dev tool (NOT shipped editor runtime code). It drives a URL (or a
local file) in a real browser via Playwright, captures an idle timeline plus a
battery of simulated interactions, measures per-frame pixel change, and emits a
verdict so a human or an agent can tell whether an interactive piece actually
achieves its effect (animates / reacts) rather than sitting static, ignoring
input, or erroring out.

Python 3.9-safe: from __future__ import annotations, no 3.10+ syntax.
No em/en dashes, no emoji. Fails soft with a clear message if Playwright or
Chrome is missing.

See README.md in this directory for usage, verdict semantics, and the spec
format.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional diff backends. We probe what is importable and pick the best one.
# Pillow (PIL) is preferred, then numpy, then a coarse raw-bytes fallback.
# We never crash on a missing optional dependency.
# ---------------------------------------------------------------------------

_PIL_OK = False
_NUMPY_OK = False
try:
    from PIL import Image  # type: ignore

    _PIL_OK = True
except Exception:
    Image = None  # type: ignore

try:
    import numpy as _np  # type: ignore

    _NUMPY_OK = True
except Exception:
    _np = None  # type: ignore


# Default idle timeline sample points, in seconds from page-settled.
DEFAULT_IDLE_TIMES = [0.0, 0.3, 0.7, 1.2, 2.0]

# Diff thresholds (documented in README).
#   PIXEL_DELTA_THRESHOLD: per-pixel grayscale delta (0..255) above which a
#       pixel counts as "changed".
#   DIFF_EPSILON: fraction of changed pixels below which we treat a frame pair
#       as effectively identical (noise floor / anti-aliasing jitter).
PIXEL_DELTA_THRESHOLD = 18
DIFF_EPSILON = 0.005

# Downsample target width for diffing (keeps the comparison cheap + robust to
# sub-pixel noise).
DIFF_WIDTH = 160


def log(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def which_diff_backend() -> str:
    if _PIL_OK:
        return "pillow"
    if _NUMPY_OK:
        return "numpy"
    return "raw"


# ---------------------------------------------------------------------------
# Pixel diff
# ---------------------------------------------------------------------------


def _diff_pillow(path_a: str, path_b: str) -> float:
    img_a = Image.open(path_a).convert("L")
    img_b = Image.open(path_b).convert("L")
    # Normalise size: downsample both to the same small width preserving ratio.
    w = DIFF_WIDTH
    ratio = img_a.height / float(img_a.width) if img_a.width else 1.0
    h = max(1, int(w * ratio))
    img_a = img_a.resize((w, h))
    img_b = img_b.resize((w, h))
    pa = img_a.load()
    pb = img_b.load()
    changed = 0
    total = w * h
    for y in range(h):
        for x in range(w):
            if abs(pa[x, y] - pb[x, y]) > PIXEL_DELTA_THRESHOLD:
                changed += 1
    return changed / float(total) if total else 0.0


def _diff_numpy(path_a: str, path_b: str) -> float:
    # numpy-only path: decode PNG without PIL is awkward, so we lean on the
    # raw fallback decode and then vectorise. To stay dependency-light we read
    # the PNG via a tiny decoder only if PIL is unavailable. In practice if
    # numpy is present but PIL is not, we still need pixels; we approximate by
    # comparing raw bytes (handled by _diff_raw). To keep numpy genuinely
    # useful we vectorise the raw byte comparison here.
    with open(path_a, "rb") as f:
        a = _np.frombuffer(f.read(), dtype=_np.uint8)
    with open(path_b, "rb") as f:
        b = _np.frombuffer(f.read(), dtype=_np.uint8)
    n = min(a.size, b.size)
    if n == 0:
        return 0.0
    a = a[:n].astype(_np.int16)
    b = b[:n].astype(_np.int16)
    changed = int(_np.count_nonzero(_np.abs(a - b) > PIXEL_DELTA_THRESHOLD))
    return changed / float(n)


def _diff_raw(path_a: str, path_b: str) -> float:
    """Coarse diff from raw PNG bytes. Reduced precision: PNG is compressed,
    so this measures byte-stream divergence, not true pixel change. Good enough
    to separate "identical" from "clearly different" frames."""
    with open(path_a, "rb") as f:
        a = f.read()
    with open(path_b, "rb") as f:
        b = f.read()
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    changed = 0
    for i in range(n):
        if abs(a[i] - b[i]) > PIXEL_DELTA_THRESHOLD:
            changed += 1
    # Length divergence also counts as change.
    changed += abs(len(a) - len(b))
    denom = max(len(a), len(b))
    return changed / float(denom) if denom else 0.0


def diff_frames(path_a: str, path_b: str) -> float:
    if _PIL_OK:
        try:
            return _diff_pillow(path_a, path_b)
        except Exception as exc:  # fall through on any decode trouble
            log("pillow diff failed (%s); falling back" % exc)
    if _NUMPY_OK:
        try:
            return _diff_numpy(path_a, path_b)
        except Exception as exc:
            log("numpy diff failed (%s); falling back" % exc)
    return _diff_raw(path_a, path_b)


# ---------------------------------------------------------------------------
# Browser launch (system Chrome via channel="chrome", fallback to chromium)
# ---------------------------------------------------------------------------


def launch_browser(pw: Any) -> Tuple[Any, str]:
    """Return (browser, label). Tries system Chrome first, then default
    chromium. Raises if neither works."""
    try:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        return browser, "chrome (channel=chrome)"
    except Exception as exc:
        log("channel=chrome launch failed (%s); trying default chromium" % exc)
    browser = pw.chromium.launch(headless=True)
    return browser, "chromium (bundled)"


# ---------------------------------------------------------------------------
# Stage discovery + interaction battery
# ---------------------------------------------------------------------------


def find_stage_box(page: Any) -> Dict[str, float]:
    """Return the bounding box of the main stage: the largest <canvas>, else
    the body. Box is {x, y, width, height} in CSS pixels."""
    box = page.evaluate(
        """() => {
            function rectOf(el) {
                const r = el.getBoundingClientRect();
                return { x: r.x, y: r.y, width: r.width, height: r.height,
                         area: r.width * r.height };
            }
            const canvases = Array.from(document.querySelectorAll('canvas'));
            let best = null;
            for (const c of canvases) {
                const r = rectOf(c);
                if (r.width < 2 || r.height < 2) continue;
                if (!best || r.area > best.area) best = r;
            }
            if (best) return best;
            const b = document.body || document.documentElement;
            return rectOf(b);
        }"""
    )
    return box


def clamp_point(box: Dict[str, float], fx: float, fy: float,
                viewport: Tuple[int, int]) -> Tuple[float, float]:
    x = box["x"] + box["width"] * fx
    y = box["y"] + box["height"] * fy
    x = max(1.0, min(float(viewport[0] - 1), x))
    y = max(1.0, min(float(viewport[1] - 1), y))
    return x, y


def default_battery(box: Dict[str, float],
                    viewport: Tuple[int, int]) -> List[Dict[str, Any]]:
    """A default interaction battery over the stage box."""
    steps: List[Dict[str, Any]] = []
    # Multi-point pointer sweep (6 positions across the element).
    sweep = [0.1, 0.25, 0.4, 0.55, 0.7, 0.9]
    for i, fx in enumerate(sweep):
        x, y = clamp_point(box, fx, 0.5, viewport)
        steps.append({"type": "move", "x": x, "y": y,
                      "label": "sweep_%d" % (i + 1)})
    # Click at center.
    cx, cy = clamp_point(box, 0.5, 0.5, viewport)
    steps.append({"type": "click", "x": cx, "y": cy, "label": "click_center"})
    # Drag across it.
    x1, y1 = clamp_point(box, 0.2, 0.3, viewport)
    x2, y2 = clamp_point(box, 0.8, 0.7, viewport)
    steps.append({"type": "drag", "x": x1, "y": y1, "x2": x2, "y2": y2,
                  "label": "drag_across"})
    # Scroll.
    steps.append({"type": "scroll", "x": cx, "y": cy, "deltaY": 400,
                  "label": "scroll_down"})
    # Arrow key.
    steps.append({"type": "key", "key": "ArrowRight", "label": "key_arrow"})
    return steps


def run_step(page: Any, step: Dict[str, Any]) -> None:
    kind = step.get("type")
    if kind == "move":
        page.mouse.move(step["x"], step["y"])
    elif kind == "click":
        page.mouse.click(step["x"], step["y"])
    elif kind == "drag":
        page.mouse.move(step["x"], step["y"])
        page.mouse.down()
        # Move in a few increments so drag handlers fire.
        steps_n = 6
        for i in range(1, steps_n + 1):
            t = i / float(steps_n)
            mx = step["x"] + (step["x2"] - step["x"]) * t
            my = step["y"] + (step["y2"] - step["y"]) * t
            page.mouse.move(mx, my)
        page.mouse.up()
    elif kind == "scroll":
        if "x" in step and "y" in step:
            page.mouse.move(step["x"], step["y"])
        page.mouse.wheel(step.get("deltaX", 0), step.get("deltaY", 300))
    elif kind == "key":
        page.keyboard.press(step.get("key", "ArrowRight"))
    else:
        log("unknown step type: %r (skipped)" % kind)


def step_label(step: Dict[str, Any], idx: int) -> str:
    if step.get("label"):
        return str(step["label"])
    return "%s_%d" % (step.get("type", "step"), idx + 1)


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------


def normalise_url(url: str) -> str:
    if "://" in url:
        return url
    # Treat as a local path.
    abspath = os.path.abspath(url)
    return "file://" + abspath


def run(args: argparse.Namespace) -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        log("ERROR: Playwright is not importable (%s)." % exc)
        log("Install it in this environment: python3 -m pip install playwright")
        return 3

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    vw, vh = args.viewport
    url = normalise_url(args.url)

    spec: Dict[str, Any] = {}
    if args.spec:
        try:
            with open(args.spec, "r") as f:
                spec = json.load(f)
        except Exception as exc:
            log("ERROR: could not read spec %s (%s)" % (args.spec, exc))
            return 3

    idle_times = spec.get("idleTimes") or DEFAULT_IDLE_TIMES
    settle_ms = int(spec.get("settleMs", args.settle_ms))
    interact_settle_ms = int(spec.get("interactSettleMs", 250))

    console_errors: List[str] = []
    page_errors: List[str] = []

    diff_backend = which_diff_backend()
    if diff_backend == "raw":
        log("NOTE: neither Pillow nor numpy usable for true pixel diff; "
            "using coarse raw-bytes diff (reduced precision).")
    elif diff_backend == "numpy":
        log("NOTE: Pillow unavailable; using numpy raw-bytes vectorised diff "
            "(reduced precision vs Pillow grayscale).")

    report: Dict[str, Any] = {
        "url": url,
        "browser": None,
        "viewport": "%dx%d" % (vw, vh),
        "diffBackend": diff_backend,
        "idleFrames": [],
        "interactions": [],
        "consoleErrors": console_errors,
        "pageErrors": page_errors,
        "metrics": {},
        "verdict": None,
        "reasons": [],
    }

    with sync_playwright() as pw:
        try:
            browser, browser_label = launch_browser(pw)
        except Exception as exc:
            log("ERROR: could not launch any browser (%s)." % exc)
            log("Confirm Google Chrome is installed at /Applications, or "
                "install Playwright browsers with: python3 -m playwright "
                "install chromium")
            return 3
        report["browser"] = browser_label
        log("browser: %s" % browser_label)

        context = browser.new_context(viewport={"width": vw, "height": vh})
        page = context.new_page()

        def on_console(msg: Any) -> None:
            try:
                if msg.type == "error":
                    console_errors.append(msg.text)
            except Exception:
                pass

        def on_pageerror(err: Any) -> None:
            page_errors.append(str(err))

        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        log("navigating to %s" % url)
        # Use domcontentloaded: a self-animating rAF page can keep the "load"
        # wait pending far too long. We add our own settle delay below anyway.
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as exc:
            log("WARN: navigation did not fully settle (%s); continuing" % exc)
        # Short settle for first paint + any boot logic.
        page.wait_for_timeout(settle_ms)

        # ----- IDLE TIMELINE -----
        idle_frames: List[Dict[str, Any]] = []
        prev_path: Optional[str] = None
        t0 = time.time()
        for i, t in enumerate(idle_times):
            target = t0 + float(t)
            now = time.time()
            if target > now:
                page.wait_for_timeout(int((target - now) * 1000))
            fname = "idle_%02d_t%0.2f.png" % (i, float(t))
            fpath = os.path.join(out_dir, fname)
            page.screenshot(path=fpath)
            diff_prev = None
            if prev_path is not None:
                diff_prev = diff_frames(prev_path, fpath)
            idle_frames.append({"t": float(t), "path": fpath,
                                "diffFromPrev": diff_prev})
            prev_path = fpath
        report["idleFrames"] = idle_frames

        # ----- INTERACTION BATTERY -----
        interactions: List[Dict[str, Any]] = []
        if not args.no_interact:
            spec_steps = spec.get("interactions")
            if spec_steps:
                steps = spec_steps
                log("running %d spec interaction step(s)" % len(steps))
            else:
                box = find_stage_box(page)
                steps = default_battery(box, (vw, vh))
                log("auto battery over stage box "
                    "x=%.0f y=%.0f w=%.0f h=%.0f (%d steps)"
                    % (box["x"], box["y"], box["width"], box["height"],
                       len(steps)))

            for idx, step in enumerate(steps):
                label = step_label(step, idx)
                before = os.path.join(out_dir, "ix_%02d_%s_before.png"
                                      % (idx, label))
                after = os.path.join(out_dir, "ix_%02d_%s_after.png"
                                     % (idx, label))
                page.screenshot(path=before)
                try:
                    run_step(page, step)
                except Exception as exc:
                    log("step %s failed (%s)" % (label, exc))
                page.wait_for_timeout(interact_settle_ms)
                page.screenshot(path=after)
                d = diff_frames(before, after)
                interactions.append({
                    "step": label,
                    "type": step.get("type"),
                    "beforePath": before,
                    "afterPath": after,
                    "diff": d,
                })
        report["interactions"] = interactions

        context.close()
        browser.close()

    # ----- METRICS + VERDICT -----
    idle_diffs = [f["diffFromPrev"] for f in report["idleFrames"]
                  if f["diffFromPrev"] is not None]
    ix_diffs = [ix["diff"] for ix in report["interactions"]]
    max_idle = max(idle_diffs) if idle_diffs else 0.0
    max_ix = max(ix_diffs) if ix_diffs else 0.0
    report["metrics"] = {
        "maxIdleDiff": max_idle,
        "maxInteractionDiff": max_ix,
        "pixelDeltaThreshold": PIXEL_DELTA_THRESHOLD,
        "diffEpsilon": DIFF_EPSILON,
    }

    reasons: List[str] = []
    verdict = "pass"

    severe_error = bool(page_errors) or bool(console_errors)
    interacted = (not args.no_interact) and bool(report["interactions"])

    animates = max_idle > DIFF_EPSILON
    reacts = max_ix > DIFF_EPSILON

    if severe_error:
        verdict = "error"
        if page_errors:
            reasons.append("uncaught page error(s): %d" % len(page_errors))
        if console_errors:
            reasons.append("console error(s): %d" % len(console_errors))
    elif not animates and (not interacted or not reacts):
        verdict = "static"
        reasons.append("no idle animation (maxIdleDiff=%.4f <= eps=%.4f)"
                       % (max_idle, DIFF_EPSILON))
        if interacted:
            reasons.append("no interaction reaction "
                           "(maxInteractionDiff=%.4f <= eps=%.4f)"
                           % (max_ix, DIFF_EPSILON))
        else:
            reasons.append("interaction disabled (--no-interact)")
    elif interacted and not reacts:
        verdict = "no-reaction"
        reasons.append("idle animates (maxIdleDiff=%.4f) but interaction "
                       "caused no change (maxInteractionDiff=%.4f <= eps=%.4f)"
                       % (max_idle, max_ix, DIFF_EPSILON))
    else:
        if animates:
            reasons.append("animates (maxIdleDiff=%.4f)" % max_idle)
        if reacts:
            reasons.append("reacts to input (maxInteractionDiff=%.4f)" % max_ix)
        if not interacted:
            reasons.append("interaction disabled (--no-interact); "
                           "verdict from idle only")

    report["verdict"] = verdict
    report["reasons"] = reasons

    # ----- OUTPUT -----
    report_path = os.path.join(out_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log("report written to %s" % report_path)

    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    sys.stdout.flush()

    if verdict == "pass":
        return 0
    if verdict == "error":
        return 2
    return 1  # static or no-reaction


def parse_viewport(s: str) -> Tuple[int, int]:
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except Exception:
        raise argparse.ArgumentTypeError(
            "viewport must look like 1280x720, got %r" % s)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Visual QA harness: verify an interactive piece achieves "
                    "its effect across multiple moments + simulated input.")
    p.add_argument("--url", required=True,
                   help="URL or local file path to test.")
    p.add_argument("--spec", default=None,
                   help="Optional JSON spec with custom interactions / timing.")
    p.add_argument("--out", default=None,
                   help="Output directory for frames + report.json "
                        "(default: ./qa-out next to this script's cwd).")
    p.add_argument("--viewport", type=parse_viewport, default=(1280, 720),
                   help="Viewport WIDTHxHEIGHT (default 1280x720).")
    p.add_argument("--settle-ms", type=int, default=300,
                   help="Settle delay after load before t=0 (default 300).")
    p.add_argument("--no-interact", action="store_true",
                   help="Skip the interaction battery (idle timeline only).")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.out is None:
        args.out = os.path.join(os.getcwd(), "qa-out")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
