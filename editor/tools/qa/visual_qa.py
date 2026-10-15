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
import base64
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
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

# ---------------------------------------------------------------------------
# Frame-judge (optional --judge). Constants for the montage + LLM transport.
# ---------------------------------------------------------------------------

# Per-tile width in the montage strip (each frame is downscaled to this width,
# height preserved). Kept small so the assembled strip stays well under any
# vision-model size cap while remaining legible.
JUDGE_TILE_WIDTH = 320
# Default vision model for the direct Anthropic API fallback.
JUDGE_DEFAULT_MODEL = "claude-sonnet-4-6"
# Where to look for a direct Anthropic key when the daemon LLM is not used.
MEDIA_CONFIG_PATH = os.path.expanduser("~/.test-harness/media-config.json")


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


# Fraction of a 64x64 grayscale frame that must sit in the single dominant
# brightness bucket for the frame to count as "blank" (nothing rendered, or a
# flat unstyled wash because the design-system @imports 404'd). A real rendered
# page has text + colour variety, so its dominant bucket stays well below this.
BLANK_DOMINANCE = 0.992


def frame_is_blank(path: str) -> Optional[bool]:
    """Return True if the frame is effectively one flat colour, False if it has
    real content, or None when we cannot tell (no Pillow, decode error). None is
    deliberately NOT treated as blank by callers, so a missing optional
    dependency never turns into a false 'blank' failure.

    This is the realistic-render check: a composed page whose CSS/JS resolved
    paints text + colour and is NOT blank; a page that loaded but rendered an
    unstyled flat wash (broken imports, JS bailout) reads as blank here even
    though navigation 'succeeded' and no error was thrown."""
    if not _PIL_OK:
        return None
    try:
        img = Image.open(path).convert("L").resize((64, 64))
    except Exception as exc:
        log("blank-check: could not open %s (%s)" % (path, exc))
        return None
    hist = img.histogram()  # 256 buckets over the 64x64 = 4096 pixels
    total = sum(hist) or 1
    peak = max(hist) if hist else 0
    return (peak / float(total)) >= BLANK_DOMINANCE


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
# Synthetic camera (mock getUserMedia with a detectable fixture)
# ---------------------------------------------------------------------------
# A camera/vision piece is BLACK under headless QA (no webcam), so detection
# never fires and the verdict is a false "static". We inject a getUserMedia
# override that returns a canvas stream rendering stock fixtures (a hand + a
# face that MediaPipe reliably detects), so the piece gets a real, moving,
# DETECTABLE feed. This is what lets an agent verify camera pieces.

_FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _fixture_data_uri(name: str) -> Optional[str]:
    try:
        with open(os.path.join(_FIXTURE_DIR, name), "rb") as f:
            return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None


def camera_mock_script(choice: str = "both") -> Optional[str]:
    """JS injected BEFORE page scripts: override navigator.mediaDevices
    .getUserMedia to return a canvas MediaStream that renders the stock hand /
    face fixtures (moving slightly so motion-based checks see change). `choice`
    is hand | face | both | off."""
    if choice == "off":
        return None
    hand = _fixture_data_uri("hand_pointing.jpg") if choice in ("hand", "both") else None
    face = _fixture_data_uri("face_portrait.jpg") if choice in ("face", "both") else None
    if not hand and not face:
        return None
    return (
        "(function(){try{"
        "var HAND=%s,FACE=%s;"
        "var cv=document.createElement('canvas');cv.width=640;cv.height=480;var cx=cv.getContext('2d');"
        "var hi=null,fi=null;if(HAND){hi=new Image();hi.src=HAND;}if(FACE){fi=new Image();fi.src=FACE;}"
        "var t=0;function paint(){t++;cx.fillStyle='#16202c';cx.fillRect(0,0,640,480);"
        "if(fi&&fi.complete&&fi.naturalWidth){var s=Math.min(300/fi.width,440/fi.height);var w=fi.width*s,h=fi.height*s;cx.drawImage(fi,20+12*Math.sin(t/40),(480-h)/2,w,h);}"
        "if(hi&&hi.complete&&hi.naturalWidth){var s2=Math.min(320/hi.width,460/hi.height);var w2=hi.width*s2,h2=hi.height*s2;cx.drawImage(hi,330+34*Math.sin(t/32),(480-h2)/2,w2,h2);}"
        "requestAnimationFrame(paint);}paint();"
        "var stream=cv.captureStream(30);var md=navigator.mediaDevices;"
        "if(md){var orig=md.getUserMedia?md.getUserMedia.bind(md):null;"
        "md.getUserMedia=function(c){if(c&&c.video){window.__qaCam=(window.__qaCam||0)+1;return Promise.resolve(stream);}return orig?orig(c):Promise.reject(new Error('no media'));};}"
        "}catch(e){}})();"
    ) % (json.dumps(hand or ""), json.dumps(face or ""))


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
    sel = step.get("selector")
    if sel:
        # Element steps, for a screen's criteria ("click #yes", "fill #amount").
        if kind == "click":
            page.click(sel, timeout=3000)
        elif kind == "fill":
            page.fill(sel, str(step.get("value", "")), timeout=3000)
        elif kind == "select":
            page.select_option(sel, step.get("value"), timeout=3000)
        elif kind == "check":
            page.check(sel, timeout=3000)
        elif kind == "hover":
            page.hover(sel, timeout=3000)
        elif kind == "key":
            page.press(sel, step.get("key", "Enter"), timeout=3000)
        else:
            log("unknown step type: %r (skipped)" % kind)
        return
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
# Frame-judge: assemble a labeled frame strip, then ask a vision LLM whether
# the captured behaviour matches an expected effect description.
#
# This is OPTIONAL and FAIL-SOFT by design. If anything goes wrong (no Pillow,
# no transport reachable, no key, network/LLM error) the judge reports
# available=false and the pixel-diff verdict is left untouched.
#
# Transport precedence (first reachable wins):
#   1. Daemon LLM  -> POST <base>/__llm_run?project=<id> with skill=describe,
#                     provider=anthropic|openai. Used only when the caller
#                     passes --judge-daemon (+ --judge-project). The harness
#                     never starts the daemon; it only talks to one already up.
#   2. Direct API  -> Anthropic Messages API via urllib, key read from
#                     ~/.test-harness/media-config.json (anthropic.api_key).
#   3. Unavailable -> judge.available=false, clear message, run unaffected.
# ---------------------------------------------------------------------------


def _pick_strip_frames(report: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Pick a representative, ordered set of (label, path) frames: a few idle
    frames that show motion, then the before/after of the interaction step with
    the largest pixel change (the "key" interaction)."""
    picks: List[Tuple[str, str]] = []
    idle = report.get("idleFrames") or []
    # First idle frame for a baseline, then up to two more (prefer ones whose
    # diffFromPrev shows the most motion so the strip captures change).
    if idle:
        picks.append(("t=%.2fs (idle start)" % float(idle[0].get("t", 0.0)),
                      idle[0]["path"]))
    rest = idle[1:]
    rest_sorted = sorted(
        rest,
        key=lambda f: (f.get("diffFromPrev") or 0.0),
        reverse=True,
    )
    for f in rest_sorted[:2]:
        picks.append(("t=%.2fs (idle)" % float(f.get("t", 0.0)), f["path"]))

    interactions = report.get("interactions") or []
    if interactions:
        key_ix = max(interactions, key=lambda ix: ix.get("diff") or 0.0)
        step = key_ix.get("step", "interaction")
        picks.append(("before %s" % step, key_ix["beforePath"]))
        picks.append(("after %s" % step, key_ix["afterPath"]))
    return picks


def build_frame_strip(report: Dict[str, Any],
                      out_dir: str) -> Optional[Dict[str, Any]]:
    """Montage the representative frames into ONE labeled image. Requires
    Pillow; returns None (with a logged note) if Pillow is unavailable so the
    judge can degrade to a per-frame list. On success returns
    {path, frames:[{label, path}], width, height}."""
    frames = _pick_strip_frames(report)
    if not frames:
        return None
    if not _PIL_OK:
        log("NOTE: Pillow unavailable; cannot montage a single frame strip.")
        return {"path": None, "frames": [{"label": l, "path": p}
                                         for (l, p) in frames]}

    from PIL import ImageDraw  # type: ignore

    tw = JUDGE_TILE_WIDTH
    label_h = 22
    pad = 8
    tiles = []
    for (label, path) in frames:
        try:
            img = Image.open(path).convert("RGB")
        except Exception as exc:
            log("strip: could not open %s (%s); skipping" % (path, exc))
            continue
        ratio = img.height / float(img.width) if img.width else 0.5625
        th = max(1, int(tw * ratio))
        img = img.resize((tw, th))
        tile = Image.new("RGB", (tw, th + label_h), (16, 16, 24))
        tile.paste(img, (0, label_h))
        draw = ImageDraw.Draw(tile)
        # Default bitmap font; no external font dependency.
        draw.text((4, 4), label, fill=(235, 235, 240))
        tiles.append(tile)
    if not tiles:
        return None
    strip_w = pad + sum(t.width + pad for t in tiles)
    strip_h = pad * 2 + max(t.height for t in tiles)
    strip = Image.new("RGB", (strip_w, strip_h), (10, 10, 14))
    x = pad
    for t in tiles:
        strip.paste(t, (x, pad))
        x += t.width + pad
    strip_path = os.path.join(out_dir, "judge_strip.png")
    strip.save(strip_path)
    return {
        "path": strip_path,
        "frames": [{"label": l, "path": p} for (l, p) in frames],
        "width": strip_w,
        "height": strip_h,
    }


def _png_to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:image/png;base64," + b64


def _judge_prompt(expected: str) -> str:
    return (
        "Here are frames over time (and the before/after of a simulated "
        "interaction) of an interactive piece, montaged left to right and "
        "labeled with their moment. The intended effect is:\n\n"
        "  " + expected + "\n\n"
        "Did the piece achieve that intended effect? Judge ONLY from the "
        "frames. Reply with STRICT JSON and nothing else, of the form:\n"
        '{\"ok\": true|false, \"reasoning\": \"why you decided\", '
        '\"observed\": \"what the frames actually show\"}'
    )


def _parse_judge_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from the model's reply. Models sometimes
    wrap JSON in prose or a code fence; we slice from the first '{' to the
    matching last '}'."""
    if not text:
        return None
    s = text.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(s[start:end + 1])
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _read_anthropic_key() -> Optional[str]:
    try:
        with open(MEDIA_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
    except Exception:
        return None
    node = cfg.get("anthropic") if isinstance(cfg, dict) else None
    if isinstance(node, dict):
        key = node.get("api_key")
        if isinstance(key, str) and key.strip():
            return key.strip()
    # Some configs store the key as a bare string.
    if isinstance(node, str) and node.strip():
        return node.strip()
    return None


def _judge_via_daemon(strip: Dict[str, Any], expected: str, base_url: str,
                      project: str, provider: str, model: Optional[str]
                      ) -> Dict[str, Any]:
    """POST the strip to an already-running daemon's /__llm_run describe skill.
    Raises on transport / HTTP failure (caller catches)."""
    if not strip.get("path"):
        raise RuntimeError("daemon transport needs a montaged strip (Pillow)")
    data_uri = _png_to_data_uri(strip["path"])
    payload = {
        "skill": "describe",
        "provider": provider,
        "prompt": _judge_prompt(expected),
        "input_data_uri": data_uri,
    }
    if model:
        payload["model"] = model
    sep = "&" if "?" in base_url else "?"
    url = "%s/__llm_run%sproject=%s" % (
        base_url.rstrip("/"), sep,
        urllib.parse.quote(project, safe=""))
    req = urllib.request.Request(
        url, method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8", "replace"))
    if not body.get("ok"):
        raise RuntimeError("daemon /__llm_run returned not-ok: %s"
                           % (body.get("error") or body))
    return {"text": body.get("text") or "",
            "model": body.get("model") or model or "(daemon default)",
            "transport": "daemon (%s)" % (body.get("provider") or provider)}


def _judge_via_anthropic_api(strip: Dict[str, Any], expected: str,
                             api_key: str, model: str) -> Dict[str, Any]:
    """Direct Anthropic Messages API call via urllib (no SDK). Raises on
    failure (caller catches)."""
    blocks: List[Dict[str, Any]] = [
        {"type": "text", "text": _judge_prompt(expected)}]
    if strip.get("path"):
        with open(strip["path"], "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png",
                       "data": b64},
        })
    else:
        # No montage (no Pillow): send each picked frame as its own block.
        for fr in strip.get("frames") or []:
            p = fr.get("path")
            if not p:
                continue
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            blocks.append({"type": "text", "text": fr.get("label") or ""})
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png",
                           "data": b64},
            })
    body = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": blocks}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    chunks = []
    for blk in data.get("content") or []:
        if isinstance(blk, dict) and blk.get("type") == "text":
            chunks.append(blk.get("text") or "")
    return {"text": "\n".join(chunks), "model": model,
            "transport": "direct anthropic api"}


def run_judge(report: Dict[str, Any], out_dir: str,
              args: argparse.Namespace) -> Dict[str, Any]:
    """Assemble the strip and run the frame-judge. ALWAYS returns a dict with
    at least {available, message}. Never raises."""
    expected = args.judge
    judge: Dict[str, Any] = {
        "available": False,
        "ok": None,
        "reasoning": None,
        "observed": None,
        "expected": expected,
        "stripPath": None,
        "model": None,
        "transport": None,
        "message": None,
    }
    try:
        strip = build_frame_strip(report, out_dir)
    except Exception as exc:
        judge["message"] = "frame strip assembly failed: %s" % exc
        return judge
    if not strip:
        judge["message"] = "no frames available to build a strip"
        return judge
    judge["stripPath"] = strip.get("path")
    judge["stripFrames"] = strip.get("frames")

    provider = args.judge_provider
    model = args.judge_model

    # ---- Transport 1: daemon LLM (only if a daemon base url was given) ----
    if args.judge_daemon:
        if not args.judge_project:
            log("judge: --judge-daemon needs --judge-project; "
                "falling through to direct API")
        else:
            try:
                res = _judge_via_daemon(strip, expected, args.judge_daemon,
                                        args.judge_project, provider, model)
                return _finish_judge(judge, res)
            except Exception as exc:
                log("judge: daemon transport failed (%s); "
                    "falling through to direct API" % exc)

    # ---- Transport 2: direct Anthropic API ----
    key = _read_anthropic_key()
    if key:
        eff_model = model or JUDGE_DEFAULT_MODEL
        try:
            res = _judge_via_anthropic_api(strip, expected, key, eff_model)
            return _finish_judge(judge, res)
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:
                detail = str(exc)
            judge["message"] = ("direct anthropic api error: %s %s"
                                % (exc.code, detail[:300]))
            return judge
        except Exception as exc:
            judge["message"] = "direct anthropic api call failed: %s" % exc
            return judge

    # ---- Transport 3: unavailable ----
    judge["message"] = (
        "judge UNAVAILABLE: no daemon LLM endpoint configured (pass "
        "--judge-daemon + --judge-project to use a running daemon) and no "
        "anthropic.api_key in %s. Strip was still saved%s; pixel-diff verdict "
        "stands." % (MEDIA_CONFIG_PATH,
                     (" at %s" % strip.get("path")) if strip.get("path")
                     else ""))
    return judge


def _finish_judge(judge: Dict[str, Any], res: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the LLM reply into the judge block. If the JSON is unparseable we
    keep available=true but ok=None and record the raw text, so the run is not
    failed on a malformed reply."""
    judge["model"] = res.get("model")
    judge["transport"] = res.get("transport")
    text = res.get("text") or ""
    parsed = _parse_judge_json(text)
    if parsed is None:
        judge["available"] = True
        judge["message"] = ("LLM reply was not parseable JSON; "
                            "treating verdict as inconclusive")
        judge["raw"] = text[:1000]
        return judge
    judge["available"] = True
    judge["ok"] = bool(parsed.get("ok"))
    judge["reasoning"] = parsed.get("reasoning")
    judge["observed"] = parsed.get("observed")
    judge["message"] = "judge ran via %s" % res.get("transport")
    return judge


# ---------------------------------------------------------------------------
# Typed visual checks (optional, --checks FILE with --typed-judge shadow|flag).
#
# A typed judge (Cloudflare Clef, OpenAI Decisions; editor/typed_judge.py
# picks) is a classifier: it can only verify a LITERAL claim about the exact
# evidence the claim needs. "Do the frames show the expected effect?" is not
# such a claim - there is nothing to classify - so the typed judge never gets
# the --judge prose. It gets CHECKS, each one:
#
#   {"id": "menu_open",
#    "shape": "shows", "x": "a dropdown menu below the Account button",
#                                          a shape from editor/visual_checks.py
#                                          (shows / changed / same_as / intact /
#                                          subject_is / which + list + expect),
#                                          or a literal "statement" instead
#    "at": "after:click_account",          which capture it is about
#    "compare": "before:click_account",    optional reference capture, sent as
#                                          IMAGE 1 with `at` as IMAGE 2, so the
#                                          statement reads "Image 2 shows X that
#                                          image 1 does not."
#    "selector": "#account-menu",          optional: crop to that element's box
#                                          as it was AT that capture
#    "criteria": {"true": "...", "false": "..."}}   optional boundary cases
#
# Captures: page (= idle:start), idle:start | idle:end | idle:motion | idle:<n>,
# before:<step> | after:<step> (the step's label, or `last`).
# A statement that only restates intent ("works as expected", "is correct"),
# counts ("how many"), or has no capture is REJECTED with the reason, never
# asked. A selector that is not on the page at that capture is reported as
# element-missing without a model call.
#
# Posture (docs/features/typed-judgment-providers.md): shadow records the
# answers and changes nothing; flag also adds one `typed-judge` finding per
# confident failure. Neither changes the verdict, the reasons or the exit code
# (P8). Only a calibrated trustPass for (provider, frame_check), in flag mode,
# with EVERY check a confident pass, may stand in for the LLM frame judge.
# ---------------------------------------------------------------------------

TYPED_KIND = "frame_check"
MAX_CHECKS = 64
# The element passes (--typed-elements): every distinct screen the QA
# reaches (at most MAX_SCREENS), judged JUDGE_WORKERS calls at a time.
#   page - the region drill. CODE ONLY SCOPES: the part of each screen the
#          change reaches, as a tree of regions. THE JUDGE JUDGES: each part of
#          a region scored on its own (a choice over the parts favoured the
#          first one, 2026-10-14) plus how they sit together; a part scoring
#          DRILL_NOUL or more is gone into, down to a primitive or a DS
#          component; at most MAX_DRILL_CALLS calls a page. A region taller
#          than TALL_PX is split without being asked (the judge cannot read
#          it shrunk). It flags too much (warning icons, error ink): the
#          visual-qa agent reads every finding with its evidence and drops the
#          non-issues.
#   ds   - the elements the design system does not recognise: listed, then
#          compared with the components the ds-compare subagent shortlists
#          for them (shortlist_compare).
MAX_SCREENS = 8
MAX_DRILL_CALLS = 60
DRILL_NOUL = 0.5
TALL_PX = 1600
JUDGE_WORKERS = 6
_CHECK_ID = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_CAPTURE = re.compile(r"^(page|screen:\d+|idle:(start|end|motion|\d+)|(before|after):.+)$")
# A design-system reference rendered from the DS gallery (compare only).
_REF = re.compile(r"^ref:[A-Za-z_][\w.-]*$")
_CROP_PAD = 8


def _editor_module(name: str) -> Any:
    editor_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if editor_dir not in sys.path:
        sys.path.insert(0, editor_dir)
    import importlib
    return importlib.import_module(name)


def _typed_judge_module() -> Any:
    return _editor_module("typed_judge")


def parse_checks(raw: Any, limit: int = MAX_CHECKS) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(checks, rejected). Accepts a list or {"checks": [...]}. Each check is a
    shape from editor/visual_checks.py or a literal statement; the question is
    BUILT there, never written here. A rejected check carries the reason."""
    vc = _editor_module("visual_checks")
    rows = raw.get("checks") if isinstance(raw, dict) else raw
    checks: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for i, c in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(c, dict):
            rejected.append({"index": i, "reason": "a check is an object"})
            continue
        cid = str(c.get("id") or "check_%d" % (i + 1))
        at = str(c.get("at") or "").strip()
        cmp_ = str(c.get("compare") or "").strip()
        row: Dict[str, Any] = {"id": cid, "at": at}
        for k in ("shape", "x", "list", "statement", "criteria", "context", "source", "optional", "evidence"):
            if c.get(k) is not None:
                row[k] = c[k]
        if cmp_:
            row["compare"] = cmp_
        exp = c.get("expect")
        if isinstance(exp, str) and exp:
            row["expect"] = [exp]
        elif isinstance(exp, list) and exp:
            row["expect"] = [str(e) for e in exp]
        if isinstance(c.get("selector"), str) and c["selector"].strip():
            row["selector"] = c["selector"].strip()[:200]
        why = None
        if not _CHECK_ID.match(cid):
            why = "id must be letters, digits, _ . - (max 64)"
        elif not _CAPTURE.match(at):
            why = "at must be page, idle:start|end|motion|<n>, before:<step> or after:<step>"
        elif cmp_ and not (_CAPTURE.match(cmp_) or _REF.match(cmp_)):
            why = "compare must name a capture like at does"
        else:
            try:
                q, need = vc.question(row)
                if need != (2 if cmp_ else 1):
                    why = ("this shape needs %d image(s): %s" %
                           (need, "add compare" if need == 2 else "drop compare"))
                elif q["type"] == "choice" and row.get("expect") and \
                        not set(row["expect"]) <= set(q["criteria"]):
                    why = "expect must be options of list %s" % row.get("list")
                else:
                    row["question"] = q
            except ValueError as exc:
                why = str(exc)
        if why:
            rejected.append({"id": cid, "statement": row.get("statement") or row.get("x"), "reason": why})
            continue
        if len(checks) >= limit:
            rejected.append({"id": cid, "reason": "over %d checks" % limit})
            continue
        checks.append(row)
    return checks, rejected


def load_checks(path: Optional[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not path:
        return [], []
    try:
        with open(path, "r") as f:
            return parse_checks(json.load(f))
    except Exception as exc:
        return [], [{"reason": "could not read checks %s (%s)" % (path, exc)}]


_BOXES_JS = """(sels) => Object.fromEntries(sels.map(s => {
  let el = null; try { el = document.querySelector(s); } catch (e) { return [s, null]; }
  if (!el) return [s, null];
  if (el.checkVisibility && !el.checkVisibility({opacityProperty: true, visibilityProperty: true}))
    return [s, null];
  const r = el.getBoundingClientRect();
  if (!r.width || !r.height) return [s, null];
  return [s, {x: r.x, y: r.y, width: r.width, height: r.height}];
}))"""


def _with_query(url: str, query: str) -> str:
    """url with `query` ("a=1&b=2", a leading ? is fine) added before any #hash."""
    query = query.lstrip("?").strip("&")
    if not query:
        return url
    base, sep, frag = url.partition("#")
    return base + ("&" if "?" in base else "?") + query + sep + frag


def typed_capture_pass(context: Any, url: str, settle_ms: int, out_dir: str,
                       steps: List[Dict[str, Any]], selectors: List[str],
                       gallery_url: Optional[str] = None,
                       ref_classes: Optional[List[str]] = None,
                       ds_plan: Optional[Dict[str, Any]] = None,
                       collector: Optional["ScreenCollector"] = None,
                       what: str = "page", scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The captures the typed checks are asked on, taken on a FRESH page after
    the main QA so nothing here can touch its verdict: the settled screen as a
    full-page screenshot, then each criteria step with a before/after (all with
    every check's element box, in page coordinates), then each state the
    scope names (`states`: a query and/or click steps from the page, each on
    a fresh page). Nothing is explored: the scope says which screens the
    change shows on. Every distinct screen joins the screens the case runner
    already collected (with what the element pass `what` reads off each);
    then one crop from the DS gallery per component a stored criterion
    compares with. Never raises."""
    out: Dict[str, Any] = {"settled": None, "interactions": [], "refs": {}, "screens": []}
    scope = scope or {}
    collector = collector or ScreenCollector(out_dir, ds_plan, what=what, changed=scope.get("changed"))
    selectors = sorted(set(selectors))
    ref_classes = list(ref_classes or [])
    page = context.new_page()
    try:
        page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_timeout(settle_ms)
        collector.capture(page, "the page")
        path = os.path.join(out_dir, "typed_page.png")
        page.screenshot(path=path, full_page=True)
        out["settled"] = {"t": 0.0, "path": path, "diffFromPrev": None,
                          "boxes": capture_boxes(page, selectors, doc=True) or {}}
        for idx, step in enumerate(steps or []):
            label = step_label(step, idx)
            before = os.path.join(out_dir, "typed_%02d_%s_before.png" % (idx, label))
            after = os.path.join(out_dir, "typed_%02d_%s_after.png" % (idx, label))
            page.screenshot(path=before, full_page=True)
            b_boxes = capture_boxes(page, selectors, doc=True) or {}
            try:
                run_step(page, step)
            except Exception as exc:
                log("criteria step %s failed (%s)" % (label, exc))
            page.wait_for_timeout(int(step.get("settleMs", 300)))
            page.screenshot(path=after, full_page=True)
            out["interactions"].append({"step": label, "beforePath": before, "afterPath": after,
                                        "beforeBoxes": b_boxes,
                                        "afterBoxes": capture_boxes(page, selectors, doc=True) or {}})
            collector.capture(page, "after %s" % label)
    except Exception as exc:
        log("typed capture pass failed (%s)" % exc)
    finally:
        page.close()
    for i, st in enumerate(scope.get("states") or []):
        if not isinstance(st, dict) or not (st.get("query") or st.get("steps")):
            continue
        label = str(st.get("label") or "state %d" % (i + 1))[:60]
        page = context.new_page()
        try:
            page.goto(_with_query(url, str(st.get("query") or "")), wait_until="load", timeout=30000)
            page.wait_for_timeout(settle_ms)
            for idx, step in enumerate(st.get("steps") or []):
                try:
                    run_step(page, step)
                except Exception as exc:
                    log("scope state %s: step %s failed (%s)" % (label, step_label(step, idx), exc))
                page.wait_for_timeout(int(step.get("settleMs", 400)) if isinstance(step, dict) else 400)
            collector.capture(page, label, st.get("changed") if isinstance(st.get("changed"), list) else None,
                              named=True)
        except Exception as exc:
            log("scope state %s not captured (%s)" % (label, exc))
        finally:
            page.close()
    out["screens"] = collector.screens
    ref_classes = sorted(set(ref_classes))
    if gallery_url and ref_classes:
        g = context.new_page()
        try:
            g.goto(gallery_url, wait_until="load", timeout=30000)
            g.wait_for_timeout(settle_ms)
            for key in ref_classes:
                # The SAME variant in the gallery: an element whose cls--*
                # modifiers are exactly the page element's (so a plain .btn is
                # compared with a plain .btn, .btn.btn--outline with an outline
                # one); else the first visible base. The label says which.
                try:
                    pick = g.evaluate(_GALLERY_PICK_JS, key.split("."))
                except Exception as exc:
                    log("gallery reference for %s unavailable (%s)" % (key, exc))
                    pick = None
                if not pick:
                    continue
                shown, state = _ref_name(key)
                if pick.get("stateMismatch"):
                    out.setdefault("refNotes", {})[key] = (
                        "the design-system gallery shows no .%s in the state %s (it shows: %s), so the "
                        "comparison was not asked" % (shown, state or "default",
                                                      ", ".join(pick.get("seen") or [])))
                    continue
                try:
                    p = os.path.join(out_dir, "ref_%s.png" % re.sub(r"[^\w-]", "_", key))
                    _ref_shot(g, g.locator(pick["selector"]).first, p)
                    out["refs"][key] = {"label": "the design system's own .%s%s%s%s"
                                        % (shown, " (%s)" % state if state else "",
                                           "" if pick["exact"] else " (base, no matching variant)",
                                           " (set to %s for the comparison)" % state if pick.get("set") else ""),
                                        "path": p, "boxes": None, "exactVariant": pick["exact"],
                                        "style": pick.get("style"), "props": pick.get("props")}
                except Exception as exc:
                    log("gallery reference for %s unavailable (%s)" % (key, exc))
        except Exception as exc:
            log("design-system gallery unavailable (%s)" % exc)
        finally:
            g.close()
    return out


# An element's state as visible tokens: a native checkbox or radio (its own,
# or the one a label / checkbox-like role wraps) is checked/unchecked; ARIA and is-* classes add selected,
# pressed, expanded, open, disabled, active, current. A same_style comparison
# is only fair between two elements in the same state.
_STATE_JS = """
  const BOX = 'input[type=checkbox],input[type=radio]';
  const boxOf = el => (el.matches && el.matches(BOX)) ? el
    : (el.matches && el.matches('label,[role=checkbox],[role=radio],[role=switch],[role=option]')
       && el.querySelectorAll(BOX).length === 1 ? el.querySelector(BOX) : null);
  const stateOf = el => {
    const out = new Set();
    const box = boxOf(el);
    if (box) out.add(box.checked ? 'checked' : 'unchecked');
    const ac = el.getAttribute('aria-checked');
    if (!box && ac === 'true') out.add('checked');
    if (!box && ac === 'false') out.add('unchecked');
    if (el.getAttribute('aria-selected') === 'true') out.add('selected');
    if (el.getAttribute('aria-pressed') === 'true') out.add('pressed');
    if (el.getAttribute('aria-expanded') === 'true') out.add('expanded');
    if (el.disabled || el.getAttribute('aria-disabled') === 'true') out.add('disabled');
    if (el.open === true) out.add('open');
    for (const c of el.classList) {
      const m = /^(?:is-)?(active|selected|open|checked|disabled|current)$/.exec(c);
      if (m) out.add(m[1]);
    }
    return [...out].sort();
  };
"""

# The element as text, captured with its screenshot so whoever reads a
# judge's answer can tell what is wrong without looking at the image: its
# HTML, its computed look, what (if anything) sits on top of it, and whether
# its content is clipped.
_EVIDENCE_JS = """
  const styleOf = el => {
    const st = getComputedStyle(el), out = [];
    const add = (k, v) => { if (v && !/^(none|normal|0px|auto|static|1|rgba\\(0, 0, 0, 0\\))$/.test(v)) out.push(k + ' ' + v); };
    add('bg', st.backgroundColor);
    if (st.backgroundImage && st.backgroundImage !== 'none') out.push('bg-image yes');
    if (st.borderTopWidth !== '0px' && st.borderTopStyle !== 'none')
      out.push('border ' + st.borderTopWidth + ' ' + st.borderTopStyle + ' ' + st.borderTopColor);
    add('radius', st.borderTopLeftRadius);
    add('shadow', st.boxShadow);
    add('color', st.color);
    out.push('font ' + st.fontWeight + ' ' + st.fontSize + ' ' + (st.fontFamily || '').split(',')[0].replace(/["']/g, ''));
    add('padding', st.padding);
    add('position', st.position);
    add('z', st.zIndex);
    add('opacity', st.opacity);
    return out.join(' · ');
  };
  const codeOf = el => {
    const h = (el.outerHTML || '').replace(/\\s+/g, ' ');
    return h.length > 320 ? h.slice(0, 320) + '...' : h;
  };
  const coverOf = (el, pathOf) => {
    const r = el.getBoundingClientRect();
    for (const [x, y] of [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 6, r.top + r.height / 2],
                          [r.right - 6, r.top + r.height / 2]]) {
      const hit = document.elementFromPoint(x, y);
      if (hit && hit !== el && !el.contains(hit) && !hit.contains(el)) return pathOf(hit);
    }
    return null;
  };
  const clippedOf = el => {
    const st = getComputedStyle(el);
    return (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
      && /hidden|clip|ellipsis/.test(st.overflow + ' ' + st.overflowX + ' ' + st.textOverflow);
  };
  const evidenceOf = (el, pathOf) => ({code: codeOf(el), style: styleOf(el), coveredBy: coverOf(el, pathOf),
                                       clipped: clippedOf(el)});
  // The look as exact values, for measuring a component against the design
  // system's own: colours, border, corners, shadow, font, spacing.
  const propsOf = el => {
    const st = getComputedStyle(el);
    const side = s => (st['border' + s + 'Style'] === 'none' || st['border' + s + 'Width'] === '0px') ? 'none'
      : st['border' + s + 'Width'] + ' ' + st['border' + s + 'Style'] + ' ' + st['border' + s + 'Color'];
    const sides = ['Top', 'Right', 'Bottom', 'Left'].map(side);
    const radii = [st.borderTopLeftRadius, st.borderTopRightRadius, st.borderBottomRightRadius, st.borderBottomLeftRadius];
    return {
      'fill': st.backgroundColor,
      'background image': st.backgroundImage === 'none' ? 'none' : 'yes',
      'text colour': st.color,
      'border': sides.every(x => x === sides[0]) ? sides[0] : sides.join(' / '),
      'corners': radii.every(x => x === radii[0]) ? radii[0] : radii.join(' '),
      'shadow': st.boxShadow,
      'font': (st.fontFamily || '').split(',')[0].replace(/["']/g, '').trim() + ' ' + st.fontWeight,
      'font size': st.fontSize,
      'letter case': st.textTransform,
      'padding': st.padding,
    };
  };
"""

_GALLERY_PICK_JS = """(parts) => {""" + _STATE_JS + _EVIDENCE_JS + """
  const base = parts[0];
  const want = parts.slice(1).filter(p => p.indexOf('state-') !== 0).sort().join(' ');
  const wantState = parts.filter(p => p.indexOf('state-') === 0).map(p => p.slice(6)).sort();
  const sameState = el => stateOf(el).join(' ') === wantState.join(' ');
  const CHECK = new Set(['checked', 'unchecked']);
  // A native checkbox or radio that differs only in checked can be set to match.
  const settable = el => {
    if (!boxOf(el) || !wantState.some(t => CHECK.has(t))) return false;
    const rest = a => a.filter(t => !CHECK.has(t)).join(' ');
    return rest(stateOf(el)) === rest(wantState);
  };
  const visible = el => {
    if (el.checkVisibility && !el.checkVisibility({opacityProperty: true, visibilityProperty: true}))
      return false;
    const r = el.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4;
  };
  const path = el => {
    const out = [];
    while (el && el.nodeType === 1 && el !== document.body) {
      if (el.id) { out.unshift('#' + CSS.escape(el.id)); return out.join(' > '); }
      let i = 1, s = el;
      while ((s = s.previousElementSibling)) if (s.tagName === el.tagName) i++;
      out.unshift(el.tagName.toLowerCase() + ':nth-of-type(' + i + ')');
      el = el.parentElement;
    }
    return 'body > ' + out.join(' > ');
  };
  const all = [...document.querySelectorAll('.' + CSS.escape(base))].filter(visible);
  if (!all.length) return null;
  // A card that wraps a checkbox is not itself checked or unchecked unless
  // the design system shows the component checkable.
  if (!all.some(el => boxOf(el))) {
    for (let i = wantState.length - 1; i >= 0; i--) if (CHECK.has(wantState[i])) wantState.splice(i, 1);
  }
  // A part's variant includes its root's modifiers: the title inside
  // .blank-slate--noresults is the noresults title.
  const root = base.indexOf('__') > 0 ? base.slice(0, base.indexOf('__')) : null;
  const mods = el => {
    const out = [...el.classList].filter(c => c.indexOf(base + '--') === 0);
    const r = root && el.closest('.' + CSS.escape(root));
    if (r) out.push(...[...r.classList].filter(c => c.indexOf(root + '--') === 0));
    return out.sort().join(' ');
  };
  for (const variant of [true, false]) {
    const pool = variant ? all.filter(el => mods(el) === want) : all;
    let el = pool.find(sameState), set = false;
    if (!el) {
      el = pool.find(settable);
      if (el) { boxOf(el).checked = wantState.indexOf('checked') >= 0; set = true; }
    }
    if (el) return {selector: path(el), exact: variant, set: set, style: styleOf(el), props: propsOf(el)};
  }
  return {stateMismatch: true, seen: [...new Set(all.map(el => stateOf(el).join(' ') || 'default'))]};
}"""

# The second link of a design-system comparison: the gallery's own component
# given the page's words and icon (when every class inside them is the DS's)
# and set on the colour the page's sits on, so what is left to differ is the
# component's own style. _GALLERY_RESTORE_JS puts the gallery back.
_GALLERY_NORMALISE_JS = """(a) => {
  const el = document.querySelector(a.selector);
  if (!el) return false;
  const saved = {el: el, html: el.innerHTML, styles: []};
  if (a.html != null) el.innerHTML = a.html;
  for (let p = el.parentElement; p; p = p.parentElement) {
    saved.styles.push([p, p.style.getPropertyValue('background'), p.style.getPropertyPriority('background')]);
    p.style.setProperty('background', 'transparent', 'important');
  }
  document.documentElement.style.setProperty('background', a.backdrop || '#fff', 'important');
  window.__wovenNormalised = saved;
  return true;
}"""
_GALLERY_RESTORE_JS = """() => {
  const s = window.__wovenNormalised;
  if (!s) return;
  s.el.innerHTML = s.html;
  for (const [p, v, pr] of s.styles) {
    if (v) p.style.setProperty('background', v, pr); else p.style.removeProperty('background');
  }
  window.__wovenNormalised = null;
}"""


# Shared by the in-browser probes below: where an element is, whether it is
# on screen, and its selector.
_DOM_JS = """
  const visible = (el, min) => {
    if (el.checkVisibility && !el.checkVisibility({opacityProperty: true, visibilityProperty: true}))
      return false;
    const r = el.getBoundingClientRect();
    if (r.width < min || r.height < min) return false;
    // Cut away by a container (a collapsed panel, a scroll box) is not on
    // screen: most of the element has to be inside every clipping ancestor.
    let x1 = r.left, y1 = r.top, x2 = r.right, y2 = r.bottom;
    for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const st = getComputedStyle(p);
      if (st.overflowX === 'visible' && st.overflowY === 'visible') continue;
      const pr = p.getBoundingClientRect();
      if (st.overflowX !== 'visible') { x1 = Math.max(x1, pr.left); x2 = Math.min(x2, pr.right); }
      if (st.overflowY !== 'visible') { y1 = Math.max(y1, pr.top); y2 = Math.min(y2, pr.bottom); }
      if (x2 <= x1 || y2 <= y1) return false;
    }
    return (x2 - x1) * (y2 - y1) >= 0.6 * r.width * r.height;
  };
  const box = el => {
    const r = el.getBoundingClientRect();
    return {x: r.x + window.scrollX, y: r.y + window.scrollY, width: r.width, height: r.height};
  };
  // The part of an element that is on screen: its box cut by every clipping
  // ancestor (a wide table in a scroller shows only the scroller's width).
  // Null when less than min px of it shows.
  const seenBox = (el, min) => {
    if (el.checkVisibility && !el.checkVisibility({opacityProperty: true, visibilityProperty: true}))
      return null;
    const r = el.getBoundingClientRect();
    let x1 = r.left, y1 = r.top, x2 = r.right, y2 = r.bottom;
    for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const st = getComputedStyle(p);
      if (st.overflowX === 'visible' && st.overflowY === 'visible') continue;
      const pr = p.getBoundingClientRect();
      if (st.overflowX !== 'visible') { x1 = Math.max(x1, pr.left); x2 = Math.min(x2, pr.right); }
      if (st.overflowY !== 'visible') { y1 = Math.max(y1, pr.top); y2 = Math.min(y2, pr.bottom); }
    }
    const m = min || 6;
    if (x2 - x1 < m || y2 - y1 < m) return null;
    return {x: x1 + window.scrollX, y: y1 + window.scrollY, width: x2 - x1, height: y2 - y1};
  };
  const path = el => {
    const parts = [];
    while (el && el.nodeType === 1 && el !== document.body) {
      if (el.id) { parts.unshift('#' + CSS.escape(el.id)); return parts.join(' > '); }
      let i = 1, s = el;
      while ((s = s.previousElementSibling)) if (s.tagName === el.tagName) i++;
      parts.unshift(el.tagName.toLowerCase() + ':nth-of-type(' + i + ')');
      el = el.parentElement;
    }
    return 'body > ' + parts.join(' > ');
  };
"""

# The design system's vocabulary in the browser: which class is a documented
# component (or one of its parts, ".section-card__icon"), and the colour an
# element sits on.
_COMP_JS = """
  const dsClasses = new Set(a.dsClasses || []);
  const titles = {};
  for (const c of a.components || []) titles[c.cls] = c.title;
  const partRoot = c => {
    const i = c.indexOf('__');
    return i > 0 && c.indexOf('--') < 0 && dsClasses.has(c) && titles[c.slice(0, i)] ? c.slice(0, i) : null;
  };
  const compOf = el => {
    if (!el.classList || !dsClasses.size) return null;
    for (const c of el.classList) if (titles[c]) return {cls: c, title: titles[c], root: null};
    for (const c of el.classList) {
      const r = partRoot(c);
      if (r) return {cls: c, title: titles[r] + ' ' + c.slice(r.length + 2).replace(/[-_]+/g, ' '), root: r};
    }
    return null;
  };
  // A container (a card, a nav, a field) holds other DS components; a leaf
  // holds none.
  const leafComp = el => ![...el.querySelectorAll('[class]')].some(d => compOf(d));
  const CLEAR = /^(transparent|rgba\\(0, 0, 0, 0\\))$/;
  const backdropOf = el => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      const b = getComputedStyle(p).backgroundColor;
      if (b && !CLEAR.test(b)) return b;
    }
    return 'rgb(255, 255, 255)';
  };
"""

# What a change touches, MEASURED rather than guessed: the changed elements
# (a.changed, selectors from the change's own code) are hidden for a moment
# and every box on the page is measured before and after. An element that
# moves inside its container (what comes after it in a column, a flex row),
# that gets narrower or wider (the other columns of a table: their content
# reflows), or that gets taller with something inside it moving is impacted;
# one that only stretched to a taller container (a sidebar beside a longer
# page) is not. The smallest container holding
# all of it is where the checks start. Null when no selector matches.
_IMPACT_JS = """
  const impactOf = sels => {
    const changed = [];
    for (const s of sels || []) {
      let found = [];
      try { found = [...document.querySelectorAll(s)]; } catch (e) { continue; }
      for (const el of found) if (seenBox(el, 2)) changed.push(el);
    }
    const top = changed.filter(el => !changed.some(c => c !== el && c.contains(el)));
    if (!top.length) return null;
    const inChanged = el => top.some(c => c === el || c.contains(el));
    const all = [...document.body.querySelectorAll('*')].slice(0, 25000).filter(el => !inChanged(el));
    const rect = el => { const r = el.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
    const before = all.map(rect);
    const saved = top.map(el => [el, el.style.getPropertyValue('display'), el.style.getPropertyPriority('display')]);
    for (const el of top) el.style.setProperty('display', 'none', 'important');
    const after = all.map(rect);
    for (const [el, v, p] of saved) { if (v) el.style.setProperty('display', v, p); else el.style.removeProperty('display'); }
    const at = new Map(all.map((el, i) => [el, i]));
    const above = new Set();
    for (const c of top) for (let p = c.parentElement; p; p = p.parentElement) above.add(p);
    const shifted = new Set(), resized = new Set();
    all.forEach((el, i) => {
      if (above.has(el)) return;
      const b = before[i], f = after[i];
      if (!b[2] && !b[3] && !f[2] && !f[3]) return;
      const pi = el.parentElement ? at.get(el.parentElement) : undefined;
      const pb = pi === undefined ? [0, 0] : before[pi], pf = pi === undefined ? [0, 0] : after[pi];
      if (Math.abs((b[0] - pb[0]) - (f[0] - pf[0])) > 1 || Math.abs((b[1] - pb[1]) - (f[1] - pf[1])) > 1) shifted.add(el);
      else if (Math.abs(b[2] - f[2]) > 1) shifted.add(el);  // narrower or wider: its content reflows
      else if (Math.abs(b[3] - f[3]) > 1) resized.add(el);
    });
    const moved = new Set(shifted);
    for (const el of resized) {
      // Only taller or shorter: impacted when something inside it moved or it
      // is a text box, not when it only stretched to a taller container.
      if (!el.children.length || [...shifted, ...resized].some(d => d !== el && el.contains(d))) moved.add(el);
    }
    const hot = top.concat([...moved].filter(el => !(el.parentElement && moved.has(el.parentElement))));
    let lca = null;
    for (const el of hot) {
      const chain = [];
      for (let p = el; p; p = p.parentElement) chain.unshift(p);
      if (!lca) { lca = chain; continue; }
      let i = 0;
      while (i < lca.length && i < chain.length && lca[i] === chain[i]) i++;
      lca = lca.slice(0, i);
    }
    let root = lca[lca.length - 1];
    // A lone changed element is judged with what is around it.
    if (hot.includes(root) && root.parentElement && root !== document.body) root = root.parentElement;
    if (root === document.documentElement) root = document.body;
    const onPath = new Set();
    for (const el of hot) for (let p = el.parentElement; p && p !== root; p = p.parentElement) onPath.add(p);
    return {root: root, hot: new Set(hot), onPath: onPath, changed: top.length, moved: moved.size, changedEls: top};
  };
"""

# Text as it reads, words apart (textContent runs "Home" and "Students"
# together), cut early so a big container costs nothing.
_TEXT_JS = """
  const textOf = (el, max) => {
    const out = [];
    let n = 0;
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let t;
    while ((t = w.nextNode()) && n < (max || 60)) {
      const s = (t.nodeValue || '').replace(/\\s+/g, ' ').trim();
      if (s) { out.push(s); n += s.length + 1; }
    }
    return out.join(' ');
  };
"""

# The screen (or, with a.changed, the part of it the change impacts) as a
# tree of REGIONS read from the code: each node is an element on screen (or
# a run of similar siblings), its children the visible blocks it is made of.
# Wrappers with one child are skipped, a long list is cut into runs of at
# most maxKids, and a node stops at a primitive (text, image, control) or a
# design-system component that holds no other. Inside the impacted part,
# only the children on the way to something impacted are shown; inside an
# impacted element, all of them. The page QA asks the judge which child of a
# node has a defect and goes down only where it says so. Breadth first.
_REGIONS_JS = """(a) => {""" + _STATE_JS + _EVIDENCE_JS + _DOM_JS + _COMP_JS + _IMPACT_JS + _TEXT_JS + """
  const MAX_KIDS = a.maxKids || 10, MAX_NODES = a.maxNodes || 4000, MAX_DEPTH = a.maxDepth || 16;
  const SKIP = /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|LINK|META|BR|WBR)$/;
  const PRIM = /^(IMG|SVG|INPUT|SELECT|TEXTAREA|CANVAS|VIDEO|AUDIO|IFRAME|HR|PICTURE|PROGRESS|METER|OBJECT|EMBED)$/i;
  const imp = (a.changed && a.changed.length) ? impactOf(a.changed) : null;
  if (a.changed && a.changed.length && !imp) return {nodes: [], scoped: true, impact: null};
  const top = imp ? imp.root : document.body;
  // A container's code is its opening tag and the start of its text; the
  // whole outerHTML of a big container is the whole page again.
  const codeOfBlock = el => {
    if (!el.children.length) return evidenceOf(el, path).code;
    const h = el.outerHTML, open = h.slice(0, Math.min(h.indexOf('>') + 1 || 200, 200));
    const t = textOf(el, 100);
    return open + (t ? ' ' + t.slice(0, 100) + (t.length > 100 ? '...' : '') : '') + ' </' + el.tagName.toLowerCase() + '>';
  };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && /\\S/.test(n.nodeValue));
  const kidsOf = el => {
    const out = [];
    const walk = p => {
      for (const c of p.children) {
        if (SKIP.test(c.tagName)) continue;
        const st = getComputedStyle(c);
        if (st.display === 'none' || st.visibility === 'hidden') continue;
        if (st.display === 'contents') { walk(c); continue; }
        if (seenBox(c, 6)) out.push(c);
        else if (c.children.length) walk(c);
      }
    };
    walk(el);
    // In the impacted part, a container shows only what leads to the change.
    if (imp && (el === top || imp.onPath.has(el)) && !imp.hot.has(el))
      return out.filter(k => imp.hot.has(k) || imp.onPath.has(k));
    return out;
  };
  // Text with inline markup (a sentence with a link in it) is one thing.
  const isPrimitive = el => PRIM.test(el.tagName) || (ownText(el) && [...el.children].every(k =>
    /^inline/.test(getComputedStyle(k).display) && !k.children.length));
  const labelOf = el => {
    const c = compOf(el);
    const cls = [...el.classList].filter(x => !/^(is|has|js)-/.test(x))[0];
    const kind = c ? c.title : el.getAttribute('aria-label') ? '' : cls ? cls.replace(/[-_]+/g, ' ')
      : el.tagName.toLowerCase();
    const h = el.matches('h1,h2,h3,h4,h5,h6,legend,th,label') ? el
      : el.querySelector('h1,h2,h3,h4,h5,h6,legend,[role=heading],caption');
    const words = (el.getAttribute('aria-label') || (h && textOf(h, 60)) || textOf(el, 60)).trim();
    const quote = words ? '"' + (words.length > 40 ? words.slice(0, 40) + '...' : words) + '"' : '';
    return (kind && quote ? kind + ' ' + quote : kind || quote || el.tagName.toLowerCase()).slice(0, 72);
  };
  // What the JUDGE is told a part is: its role in plain words and the words
  // it shows, never a class name ("fa ref tail" means nothing on a
  // screenshot). The crop carries no marks, so this name is all it has to
  // find the part by (labelOf stays the code-side name for the agent).
  const ROLES = [
    ['th,[role=columnheader]', 'column header'], ['[role=rowheader]', 'row header'],
    ['thead', 'table header row'], ['tbody', 'table body'], ['tfoot', 'table footer'], ['caption', 'table caption'],
    ['table,[role=table],[role=grid]', 'table'],
    ['button,[role=button],input[type=button],input[type=submit]', 'button'], ['a[href],[role=link]', 'link'],
    ['input[type=checkbox],[role=checkbox]', 'checkbox'], ['input[type=radio],[role=radio]', 'radio button'],
    ['select,[role=combobox],[role=listbox]', 'dropdown'], ['textarea,input', 'input field'],
    ['img,picture,canvas,video', 'image'], ['svg', 'icon'], ['h1,h2,h3,h4,h5,h6,[role=heading]', 'heading'],
    ['label', 'label'], ['legend', 'legend'], ['nav,[role=navigation]', 'navigation'], ['[role=tablist]', 'tab bar'],
    ['[role=tab]', 'tab'], ['dialog,[role=dialog]', 'dialog'], ['form', 'form'], ['li,[role=listitem]', 'list item'],
    ['ul,ol,[role=list]', 'list'], ['header', 'header'], ['footer', 'footer'], ['aside', 'side panel'],
    ['p', 'paragraph'], ['hr', 'divider'], ['progress,meter,[role=progressbar]', 'progress bar']];
  const roleOf = el => { for (const [s, w] of ROLES) if (el.matches(s)) return w; return ''; };
  // Only what is ON SCREEN names a part: an aria-label or alt is not
  // visible, and a name cut short with "..." reads as text cut off on the
  // page (it drew false "cut off" flags on whole references, 2026-10-15).
  const seenText = el => (el.matches('input,select,textarea') ? (el.value || el.getAttribute('placeholder') || '')
    : textOf(el, 120)).replace(/ +/g, ' ').trim();
  const quoted = s => {
    if (s.length <= 48) return "'" + s + "'";
    const cut = s.slice(0, 48), sp = cut.lastIndexOf(' ');
    return "'" + (sp > 16 ? cut.slice(0, sp) : cut) + "' (first words)";
  };
  const isBlock = k => !/^inline/.test(getComputedStyle(k).display);
  // The visible texts a part shows, one per block inside it: a cell with a
  // name over a reference shows 'Loh Sok Cheng' and 'FAD-PTUG-FAS- 2026-06-07001'.
  const piecesOf = el => {
    const blocks = [...el.children].filter(k => isBlock(k) && seenText(k));
    return (blocks.length > 1 ? blocks.map(seenText) : [seenText(el)]).filter(Boolean);
  };
  const showing = el => {
    const p = piecesOf(el);
    if (!p.length) return '';
    return p.length === 1 ? quoted(p[0]) : p.length === 2 ? quoted(p[0]) + ' and ' + quoted(p[1])
      : quoted(p[0]) + ', ' + quoted(p[1]) + ' and more';
  };
  const article = w => (/^[aeiou]/.test(w) ? 'an ' : 'a ') + w;
  // A part with no visible words is named by what it holds: "a checkbox".
  const holdsOf = el => {
    const d = el.querySelector('input,select,textarea,button,a[href],img,svg,canvas,video,[role]');
    const r = d ? roleOf(d) : '';
    return r ? article(r) : '';
  };
  // The column a cell sits in, after its own words: the header is often not
  // in the cell's crop, so it is context, never how the cell is found.
  const columnOf = el => {
    const t = el.closest('table');
    const h = t && t.tHead && t.tHead.rows.length ? t.tHead.rows[0].cells[el.cellIndex] : null;
    const w = h ? seenText(h) : '';
    return w ? ' (the ' + quoted(w) + ' column)' : '';
  };
  // Text broken into inline pieces (spans around parts of a reference) still
  // reads as one text.
  const inlineOnly = el => el.children.length > 0 && [...el.children].every(k =>
    /^inline/.test(getComputedStyle(k).display) && !k.children.length);
  const nameOf = el => {
    const shows = showing(el), holds = shows ? '' : holdsOf(el);
    const tail = shows ? ' showing ' + shows : holds ? ' holding ' + holds : '';
    if (el.matches('td')) return 'the table cell' + tail + columnOf(el);
    if (el.matches('tr,[role=row]')) {
      const cell = [...el.children].find(k => piecesOf(k).length);
      return 'the table row' + (cell ? ' for ' + quoted(piecesOf(cell)[0]) : '');
    }
    const c = compOf(el), role = roleOf(el);
    if (c || role) return 'the ' + (c ? c.title.toLowerCase() : role) + (shows ? ' ' + shows : holds ? ' holding ' + holds : '');
    if (shows && (ownText(el) || isPrimitive(el) || inlineOnly(el))) return 'the text ' + shows;
    return 'the area' + tail;
  };
  const nodes = [];
  const add = (el, depth, parent) => {
    const n = {i: nodes.length, parent: parent, depth: depth, sel: path(el), box: seenBox(el, 1) || box(el),
               label: labelOf(el), say: nameOf(el), kids: [], hot: !!(imp && imp.hot.has(el)), ev: null};
    nodes.push(n);
    return n;
  };
  const union = list => {
    const x1 = Math.min(...list.map(n => n.box.x)), y1 = Math.min(...list.map(n => n.box.y));
    const x2 = Math.max(...list.map(n => n.box.x + n.box.width)), y2 = Math.max(...list.map(n => n.box.y + n.box.height));
    return {x: x1, y: y1, width: x2 - x1, height: y2 - y1};
  };
  // A long list is cut into runs: the judge is shown at most MAX_KIDS boxes.
  const runsOf = (members, parent, depth) => {
    if (members.length <= MAX_KIDS) return members;
    const size = Math.ceil(members.length / MAX_KIDS), out = [];
    for (let s = 0; s < members.length; s += size) {
      const part = members.slice(s, s + size);
      if (part.length === 1) { out.push(part[0]); continue; }
      const g = {i: nodes.length, parent: parent, depth: depth, sel: part[0].sel, box: union(part),
                 label: 'items ' + (s + 1) + '-' + (s + part.length) + ' of ' + members.length + ' (' + part[0].label + ' ...)',
                 say: 'the ' + (part[0].say.indexOf('the table row') === 0 ? 'table rows ' : 'items ') + (s + 1) + ' to '
                   + (s + part.length) + ' of ' + members.length + ' (from ' + part[0].say + ')',
                 kids: [], group: [part[0].sel, part[part.length - 1].sel], ev: null};
      nodes.push(g);
      for (const m of runsOf(part, g.i, depth + 1)) { m.parent = g.i; g.kids.push(m.i); }
      out.push(g);
    }
    return out;
  };
  const root = add(top, 0, null);
  if (top === document.body) root.label = root.say = 'the whole screen';
  root.ev = {code: codeOfBlock(top), style: '', coveredBy: null, clipped: false};
  const queue = [[root, top]];
  while (queue.length) {
    const [n, el] = queue.shift();
    let host = el, kids = kidsOf(host);
    // A wrapper around one block is that block.
    while (kids.length === 1 && !compOf(kids[0]) && !isPrimitive(kids[0])) { host = kids[0]; kids = kidsOf(host); }
    const members = [];
    for (const k of kids) {
      if (nodes.length >= MAX_NODES) break;
      const kn = add(k, n.depth + 1, n.i);
      const kc = compOf(k);
      kn.ev = evidenceOf(k, path);
      if (k.children.length) kn.ev.code = codeOfBlock(k);
      if (kc) kn.comp = {cls: kc.cls, title: kc.title, leaf: leafComp(k)};
      members.push(kn);
      if (!((kc && kn.comp.leaf) || isPrimitive(k) || n.depth + 1 >= MAX_DEPTH)) queue.push([kn, k]);
    }
    for (const m of runsOf(members, n.i, n.depth + 1)) n.kids.push(m.i);
  }
  return {nodes: nodes, truncated: nodes.length >= MAX_NODES, scoped: !!imp,
          impact: imp ? {changed: imp.changed, moved: imp.moved, root: path(top)} : null};
}"""

# EVIDENCE for the page QA's findings, measured by code in the part of the
# screen the change impacts (_IMPACT_JS; the whole screen without a scope).
# It never makes or drops a finding (the image judge does): a finding at or
# around one of these carries its measurement for the agent that reads it:
#   cut-off      text that is clipped (overflow, ellipsis, line clamp) or cut
#                by a container that hides its overflow (a scroller is not:
#                its content can be scrolled to);
#   covered      text with something else on top of it (not an open dialog
#                over the page: that covers by design);
#   spill        an in-flow element that sticks out of a container that does
#                not clip or scroll;
#   uneven-gaps  three or more similar siblings in a row or column whose gaps
#                differ - the parts are fine, how they sit together is not.
# Each comes with where it sits (`within`: the labelled blocks above it) and
# its code and look as evidence.
_DEFECTS_JS = """(a) => {""" + _STATE_JS + _EVIDENCE_JS + _DOM_JS + _COMP_JS + _IMPACT_JS + _TEXT_JS + """
  const MAX = a.maxDefects || 40;
  const imp = (a.changed && a.changed.length) ? impactOf(a.changed) : null;
  if (a.changed && a.changed.length && !imp) return {defects: [], scoped: true, impact: null};
  const root = imp ? imp.root : document.body;
  const hotList = imp ? [...imp.hot] : null;
  const inScope = el => !imp || hotList.some(h => h === el || h.contains(el));
  const opens = el => !imp || el === root || imp.onPath.has(el) || inScope(el);
  const SKIP = /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|LINK|META|BR|WBR|SVG|PATH|G|USE|OPTION)$/i;
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && /\\S/.test(n.nodeValue));
  const tidy = s => (s || '').replace(/\\s+/g, ' ').trim();
  const labelOf = el => {
    const c = compOf(el);
    const cls = [...el.classList].filter(x => !/^(is|has|js)-/.test(x))[0];
    const kind = c ? c.title : cls ? cls.replace(/[-_]+/g, ' ') : el.tagName.toLowerCase();
    const words = tidy(el.getAttribute('aria-label') || textOf(el, 60));
    return (words ? kind + ' "' + (words.length > 40 ? words.slice(0, 40) + '...' : words) + '"' : kind).slice(0, 72);
  };
  // Where it sits: the nearest blocks above it that are worth a name (a DS
  // component, a landmark, a heading's section), outermost first.
  const within = el => {
    const out = [];
    for (let p = el.parentElement; p && p !== document.body && out.length < 3; p = p.parentElement) {
      if (compOf(p) || /^(MAIN|NAV|ASIDE|HEADER|FOOTER|SECTION|TABLE|FORM|DIALOG|UL|OL)$/.test(p.tagName)
          || p.getAttribute('role') || p.id) out.unshift(labelOf(p));
      if (p === root) break;
    }
    return out.join(' > ');
  };
  const overlayOf = el => el.closest('[role=dialog],[aria-modal=true],dialog,[class*=slideout],[class*=modal]');
  // Cut by a container that hides its overflow. Per axis, the NEAREST
  // container that clips the element decides: a scroller (auto / scroll)
  // means the rest can be scrolled to, which is no defect.
  const hiddenCut = el => {
    const r = el.getBoundingClientRect();
    let doneX = false, doneY = false;
    for (let p = el.parentElement; p && p !== document.documentElement && !(doneX && doneY); p = p.parentElement) {
      const st = getComputedStyle(p), pr = p.getBoundingClientRect();
      const outX = r.left < pr.left - 1 || r.right > pr.right + 1, outY = r.top < pr.top - 1 || r.bottom > pr.bottom + 1;
      if (!doneX && st.overflowX !== 'visible' && outX) {
        if (/hidden|clip/.test(st.overflowX)) return path(p);
        doneX = true;
      }
      if (!doneY && st.overflowY !== 'visible' && outY) {
        if (/hidden|clip/.test(st.overflowY)) return path(p);
        doneY = true;
      }
    }
    return null;
  };
  const clampCut = el => {
    const st = getComputedStyle(el);
    const clips = /hidden|clip/.test(st.overflow + ' ' + st.overflowX + ' ' + st.overflowY)
      || st.textOverflow === 'ellipsis' || (st.webkitLineClamp && st.webkitLineClamp !== 'none');
    return clips && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1);
  };
  // What lies on top of the part of el that is on screen (coverOf samples
  // its whole box, which for a cell in a scrolled table is partly elsewhere).
  const coverSeen = el => {
    const sb = seenBox(el, 2);
    if (!sb) return null;
    const x1 = sb.x - window.scrollX, y1 = sb.y - window.scrollY;
    for (const [x, y] of [[x1 + sb.width / 2, y1 + sb.height / 2], [x1 + 4, y1 + sb.height / 2],
                          [x1 + sb.width - 4, y1 + sb.height / 2]]) {
      const hit = document.elementFromPoint(x, y);
      if (hit && hit !== el && !el.contains(hit) && !hit.contains(el)) return path(hit);
    }
    return null;
  };
  const out = [];
  const seen = new Set();
  const push = (kind, el, extra) => {
    if (out.length >= MAX || seen.has(kind + path(el))) return;
    seen.add(kind + path(el));
    const sb = seenBox(el, 2);
    if (!sb) return;
    out.push(Object.assign({kind: kind, selector: path(el), box: sb, label: labelOf(el), within: within(el),
                            text: textOf(el, 80), ev: evidenceOf(el, path)}, extra || {}));
  };
  const els = [...root.querySelectorAll('*')].slice(0, 12000);
  for (const el of els) {
    if (out.length >= MAX) break;
    if (SKIP.test(el.tagName) || !seenBox(el, 4)) continue;
    const st = getComputedStyle(el);
    if (inScope(el)) {
      if (ownText(el)) {
        const r = el.getBoundingClientRect();
        if (clampCut(el)) {
          push('cut-off', el, {cutBy: 'its own box', measured: 'its text needs ' + el.scrollWidth + 'x' + el.scrollHeight
                               + 'px and shows ' + el.clientWidth + 'x' + el.clientHeight + 'px'});
        } else {
          const cut = hiddenCut(el);
          if (cut) {
            const cr = document.querySelector(cut).getBoundingClientRect();
            const px = Math.round(Math.max(cr.left - r.left, r.right - cr.right, cr.top - r.top, r.bottom - cr.bottom));
            push('cut-off', el, {cutBy: cut, measured: 'it runs ' + px + 'px past the edge of ' + cut + ', which hides its overflow'});
          }
        }
        const hit = coverSeen(el);
        if (hit) {
          const hitEl = document.querySelector(hit);
          const ov = hitEl && overlayOf(hitEl);
          if (!(ov && !ov.contains(el))) {
            const hr = hitEl.getBoundingClientRect();
            const w = Math.round(Math.min(r.right, hr.right) - Math.max(r.left, hr.left));
            const h = Math.round(Math.min(r.bottom, hr.bottom) - Math.max(r.top, hr.top));
            let blk = el.parentElement;
            while (blk && /^inline/.test(getComputedStyle(blk).display)) blk = blk.parentElement;
            const past = blk && !blk.contains(hitEl) ? Math.round(r.right - blk.getBoundingClientRect().right) : 0;
            push('covered', el, {coveredBy: hit, measured: 'it and ' + hit + ' overlap by ' + w + 'x' + h + 'px'
                                 + (past > 0 ? '; it runs ' + past + 'px past the right edge of ' + path(blk) : '')});
          }
        }
      }
      const p = el.parentElement;
      if (p && p !== document.body && !/absolute|fixed|sticky/.test(st.position) && st.display !== 'contents') {
        const ps = getComputedStyle(p);
        if (ps.overflowX === 'visible' && ps.overflowY === 'visible' && !/^(TR|TBODY|THEAD|TABLE)$/.test(p.tagName)) {
          const r = el.getBoundingClientRect(), pr = p.getBoundingClientRect();
          const out_ = Math.max(pr.left - r.left, r.right - pr.right, pr.top - r.top, r.bottom - pr.bottom);
          // Text that runs out of its container over something else is
          // already a cover, which says how far it runs.
          if (out_ > 2 && !seen.has('covered' + path(el))
              && (ownText(el) || st.backgroundColor !== 'rgba(0, 0, 0, 0)' || st.borderTopStyle !== 'none'))
            push('spill', el, {container: {selector: path(p), box: seenBox(p, 2) || box(p), label: labelOf(p)},
                               measured: 'it sticks out ' + Math.round(out_) + 'px past ' + path(p)});
        }
      }
    }
    // Uneven gaps between similar siblings, in a container the change reaches.
    if (opens(el) && el.children.length >= 3 && !/^(TABLE|TBODY|THEAD|TR|SELECT)$/.test(el.tagName)) {
      const kids = [...el.children].filter(k => !SKIP.test(k.tagName) && seenBox(k, 4)
        && !/absolute|fixed/.test(getComputedStyle(k).position));
      const sig = k => k.tagName + '.' + ([...k.classList].filter(x => !/^(is|has|js)-/.test(x))[0] || '');
      if (kids.length >= 3 && kids.every(k => sig(k) === sig(kids[0]))) {
        const rs = kids.map(k => k.getBoundingClientRect());
        const row = rs.every(r => Math.abs(r.top - rs[0].top) < 2);
        const col = rs.every(r => Math.abs(r.left - rs[0].left) < 2);
        if (row || col) {
          const gaps = [];
          for (let i = 1; i < rs.length; i++) gaps.push(row ? rs[i].left - rs[i - 1].right : rs[i].top - rs[i - 1].bottom);
          const sorted = [...gaps].sort((x, y) => x - y), med = sorted[Math.floor(sorted.length / 2)];
          const worst = gaps.reduce((m, g) => Math.max(m, Math.abs(g - med)), 0);
          if (worst > Math.max(4, Math.abs(med) * 0.5))
            push('uneven-gaps', el, {gaps: gaps.map(g => Math.round(g)),
                                     parts: kids.slice(0, 10).map(k => seenBox(k, 1) || box(k))});
        }
      }
    }
  }
  return {defects: out, scoped: !!imp, impact: imp ? {changed: imp.changed, moved: imp.moved, root: path(root)} : null};
}"""

# The elements a design system does not recognise: each visible element that
# gets its own skin (background, border, shadow, outline, backdrop) from a
# stylesheet that is not the design system's, or from an inline style, and
# carries no DS class. Code written with the DS's classes is correct by
# construction and is not looked at; these are what may be a hand-made copy
# of a DS component, or a new pattern. With a.changed, only those inside
# what the change impacts.
_OFF_SYSTEM_JS = """(a) => {""" + _STATE_JS + _EVIDENCE_JS + _DOM_JS + _COMP_JS + _IMPACT_JS + _TEXT_JS + """
  const SKIN = /^(background|border|box-shadow|outline|backdrop-filter)/;
  const EMPTY = /^(none|transparent|0|0px|initial|inherit|unset|rgba\\(0, 0, 0, 0\\)|0px none.*)$/;
  const imp = (a.changed && a.changed.length) ? impactOf(a.changed) : null;
  if (a.changed && a.changed.length && !imp) return {off: [], scoped: true, impact: null};
  // Only what the change wrote: an unrecognised element that merely moved
  // because of it is older code.
  const within = el => !imp || imp.changedEls.some(h => h === el || h.contains(el));
  const hasDs = el => el.classList && [...el.classList].some(c => dsClasses.has(c));
  const skinOf = st => {
    const out = [];
    for (let i = 0; i < st.length; i++) {
      const p = st[i];
      if (!SKIN.test(p)) continue;
      const v = (st.getPropertyValue(p) || '').trim();
      if (v && !EMPTY.test(v)) out.push(p);
    }
    return out;
  };
  const off = new Map();
  const take = (el, source, skin) => {
    if (off.has(el) || hasDs(el) || !visible(el, 8) || !within(el)) return;
    off.set(el, {selector: path(el), source: source, skin: skin, box: box(el), ev: evidenceOf(el, path),
                 props: propsOf(el), text: !!textOf(el, 4), backdrop: backdropOf(el), content: null,
                 clearFill: CLEAR.test(getComputedStyle(el).backgroundColor)});
  };
  const visit = (rules, sheet) => {
    for (const rule of rules) {
      if (!rule.selectorText) {
        if (rule.cssRules) { try { visit(rule.cssRules, sheet); } catch (e) {} }
        continue;
      }
      const skin = rule.style ? skinOf(rule.style) : [];
      if (!skin.length) continue;
      for (const raw of rule.selectorText.split(',')) {
        const sel = raw.trim().replace(/::?[\\w-]+(\\([^)]*\\))?/g, '').trim();
        if (!sel || /^(html|body|\\*|:root)$/i.test(sel)) continue;
        let els = [];
        try { els = [...document.querySelectorAll(sel)]; } catch (e) { continue; }
        for (const el of els) take(el, sheet + ' ' + sel, skin);
      }
    }
  };
  if (dsClasses.size) {
    for (const sh of document.styleSheets) {
      if (sh.href && a.dsPath && sh.href.indexOf(a.dsPath) >= 0) continue;
      let rules = null;
      try { rules = sh.cssRules; } catch (e) { continue; }
      visit(rules, sh.href ? sh.href.split('/').pop().split('?')[0] : '<style>');
    }
    for (const el of document.querySelectorAll('[style]')) {
      const skin = skinOf(el.style);
      if (skin.length) take(el, 'inline style on <' + el.tagName.toLowerCase() + '>', skin);
    }
  }
  return {off: [...off.values()].slice(0, a.maxOff || 60), scoped: !!imp,
          impact: imp ? {changed: imp.changed, moved: imp.moved, root: path(imp.root)} : null};
}"""

# A screen's identity: the visible headings, dialogs and the URL hash. Two
# moments with the same identity are the same screen, captured once.
_SCREEN_SIG_JS = """() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const heads = [...document.querySelectorAll('h1,h2,h3,legend,[role=heading],[role=dialog],dialog[open],[aria-modal=true]')]
    .filter(vis).map(e => e.tagName + ':' + (e.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 60));
  return location.pathname + location.hash + '|' + heads.join('|');
}"""


# Has the screen stopped moving? Finite animations still running, the scroll
# position, the document height. Two equal readings with nothing running =
# settled (an infinite ambient animation never blocks).
_MOTION_JS = """() => {
  const running = document.getAnimations().filter(a => a.playState === 'running'
    && !(a.effect && a.effect.getTiming && a.effect.getTiming().iterations === Infinity)).length;
  const se = document.scrollingElement || document.documentElement;
  return running + ',' + Math.round(window.scrollY) + ',' + Math.round(se.scrollHeight);
}"""


def _settle_screen(page: Any, timeout_ms: int = 3000) -> None:
    """Wait until nothing on the screen moves: smooth scrolls, step
    transitions, fades. Boxes measured mid-motion crop the wrong pixels."""
    last, t0 = None, time.time()
    while (time.time() - t0) * 1000 < timeout_ms:
        try:
            now = str(page.evaluate(_MOTION_JS))
        except Exception:
            return
        if now == last and now.startswith("0,"):
            return
        last = now
        page.wait_for_timeout(150)


class ScreenCollector:
    """Every distinct screen the QA reaches, captured once: a full-page
    screenshot plus what its element pass reads from the code on the same
    layout - the candidate defects for the page QA (`what` page), the
    elements the design system does not recognise for the DS check (`what`
    ds) - each with its box. Fed by the typed capture pass (the settled page, each criteria step,
    the exploration) and by the case runner (each case's end state). Never
    raises: a failed capture is a screen not judged, not a failed QA."""

    def __init__(self, out_dir: str, plan: Optional[Dict[str, Any]], cap: int = MAX_SCREENS,
                 what: str = "page", changed: Optional[List[str]] = None):
        self.out_dir, self.plan, self.cap, self.what = out_dir, plan or {}, cap, what
        # The change's own selectors: each screen is read from where they
        # impact it (_IMPACT_JS), not as a whole.
        self.changed = [str(c) for c in (changed or []) if str(c).strip()]
        self.screens: List[Dict[str, Any]] = []
        self.seen: set = set()

    def capture(self, page: Any, label: str, changed: Optional[List[str]] = None,
                named: bool = False) -> Optional[Dict[str, Any]]:
        """`named`: a state the scope names is always captured; its headings
        can match another state's (edit and read-only of one tab), which the
        screen signature would take for the same screen."""
        if len(self.screens) >= self.cap:
            return None
        try:
            sig = str(page.evaluate(_SCREEN_SIG_JS))
        except Exception:
            sig = None
        if sig is not None and sig in self.seen and not named:
            return None
        self.seen.add(sig)
        n = len(self.screens)
        path = os.path.join(self.out_dir, "screen_%02d.png" % n)
        # Measure and shoot the SAME layout: at the top, settled, with the
        # viewport as tall as the page (what a full-page shot does inside),
        # so fixed and sticky bars sit where the boxes say they do.
        vp = None
        try:
            page.evaluate("window.scrollTo(0, 0)")
            _settle_screen(page)
            vp = page.viewport_size
            height = int(page.evaluate("(document.scrollingElement || document.documentElement).scrollHeight"))
            page.set_viewport_size({"width": vp["width"], "height": max(vp["height"], min(height, 12000))})
            _settle_screen(page, 1500)
        except Exception:
            vp = None
        found: Dict[str, Any] = {}
        try:
            probe = dict(self.plan, changed=[str(c) for c in changed if str(c).strip()]
                         if changed is not None else self.changed)
            if self.what == "ds":
                found = detect_off_system(page, probe) or {}
            else:
                found = detect_regions(page, probe) or {}
                found["measured"] = (detect_defects(page, probe) or {}).get("defects") or []
            page.screenshot(path=path, full_page=vp is None)
        except Exception as exc:
            log("screen capture %s failed (%s)" % (label, exc))
            return None
        finally:
            if vp:
                try:
                    page.set_viewport_size(vp)
                except Exception:
                    pass
        boxes: Dict[str, Any] = {}
        for item in found.get("off") or []:
            if item.get("selector") and item.get("box"):
                boxes[item["selector"]] = item["box"]
        screen = {"n": n, "label": label, "path": path, "found": found, "boxes": boxes}
        self.screens.append(screen)
        return screen


def detect_off_system(page: Any, plan: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The elements on the rendered screen the design system does not
    recognise (see _OFF_SYSTEM_JS). None when the probe fails."""
    try:
        return page.evaluate(_OFF_SYSTEM_JS, plan or {})
    except Exception as exc:
        log("off-system detection on the rendered page failed (%s)" % exc)
        return None


def detect_regions(page: Any, plan: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The rendered screen (or the part the change impacts) as a region tree
    (see _REGIONS_JS). None when the probe fails."""
    try:
        return page.evaluate(_REGIONS_JS, plan or {})
    except Exception as exc:
        log("region map of the rendered page failed (%s)" % exc)
        return None


def detect_defects(page: Any, plan: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """What code measures as wrong on the rendered screen (see _DEFECTS_JS),
    evidence for the judge's findings. None when the probe fails."""
    try:
        return page.evaluate(_DEFECTS_JS, plan or {})
    except Exception as exc:
        log("defect search on the rendered page failed (%s)" % exc)
        return None


def prepare_typed(args: argparse.Namespace) -> None:
    """Load everything the typed checks need into args: the screen's criteria
    (--checks), the design system's plan (--ds-visual) turned into checks, and
    the criteria steps (--typed-steps)."""
    checks, rejected = load_checks(getattr(args, "checks", None))
    args.ds_plan = None
    args.typed_steps_list = []
    for attr, key in (("ds_visual", "ds_plan"), ("typed_steps", "typed_steps_list")):
        path = getattr(args, attr, None)
        if not path:
            continue
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as exc:
            log("could not read %s (%s)" % (path, exc))
            continue
        if key == "typed_steps_list":
            data = data.get("steps") if isinstance(data, dict) else data
            data = [st for st in (data or []) if isinstance(st, dict)]
        setattr(args, key, data)
    args.parsed_checks = (checks[:MAX_CHECKS] if len(checks) > MAX_CHECKS else checks, rejected)


# A pair comparison (the design system's component A beside the page's B, in
# one image) is ONE call: "B is visually different from A" plus a score per
# dimension, and the branch is decided from those scores. A style dimension
# that scores high is what is wrong with B; the content dimensions (icon,
# arrangement, words) differ by design, since the gallery shows sample
# content. The cut-offs come from 16 judged pairs (2026-10-13), uncalibrated.
PAIR_DIMS = {
    "colour": "B's colours are visually different from A's.",
    "border": "B's border is visually different from A's.",
    "shape": "B's shape or corner rounding is visually different from A's.",
    "font": "B's font is visually different from A's.",
    "icon": "B's icon or picture is visually different from A's.",
    "layout": "B's parts are arranged visually differently from A's.",
    "words": "B's words are different from A's.",
}
PAIR_STYLE = ("colour", "border", "shape", "font")
PAIR_HIT = 0.8
PAIR_CLEAR = 0.5


def pair_verdict(answers: Dict[str, Any], rid: str) -> Dict[str, Any]:
    """The branch for one pair from its scores: a style dimension at or over
    PAIR_HIT -> B differs there (sure no); every style dimension under
    PAIR_CLEAR -> same style (sure yes), whatever the content does; anything
    between -> unsure, naming the dimensions in question."""
    tj = _typed_judge_module()
    dims = {d: tj.noul_value(answers.get("%s__%s" % (rid, d))) for d in PAIR_DIMS}
    overall = tj.noul_value(answers.get(rid))
    base = {"noul": overall, "dims": {d: (round(v, 4) if v is not None else None) for d, v in dims.items()}}
    style = {d: dims[d] for d in PAIR_STYLE}
    if any(v is None for v in style.values()):
        return dict(base, answer=None, passed=None, confidence=None, band="escalate")
    hits = [d for d in PAIR_STYLE if style[d] >= PAIR_HIT]
    if hits:
        return dict(base, answer="differs in " + ", ".join(hits), passed=False,
                    confidence=round(max(style[d] for d in hits), 4), band="act")
    top = max(style.values())
    if top < PAIR_CLEAR:
        content = [d for d in ("icon", "layout", "words") if (dims[d] or 0) >= PAIR_HIT]
        return dict(base, answer="same style" + (" (its %s differ)" % ", ".join(content) if content else ""),
                    passed=True, confidence=round(1 - top, 4), band="act")
    return dict(base, answer="unclear: " + ", ".join(d for d in PAIR_STYLE if style[d] >= PAIR_CLEAR),
                passed=None, confidence=round(top, 4), band="escalate")


def _label_font(size: int = 22) -> Any:
    from PIL import ImageFont
    for face in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(face, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _side_by_side(a: Any, b: Any) -> Optional[bytes]:
    """A (the design system's own) on the left, B (the page's) on the right, in
    one image at one height, each labelled. None without Pillow."""
    if not _PIL_OK:
        return None
    import io
    from PIL import ImageDraw

    def load(x: Any) -> Any:
        return Image.open(io.BytesIO(x) if isinstance(x, (bytes, bytearray)) else x["path"]).convert("RGB")
    try:
        A, B = load(a), load(b)
    except Exception:
        return None
    h = max(80, min(220, max(A.height, B.height)))
    A = A.resize((max(1, int(A.width * h / float(A.height))), h))
    B = B.resize((max(1, int(B.width * h / float(B.height))), h))
    if A.width + B.width + 60 > 1400:
        f = 1340.0 / (A.width + B.width)
        A = A.resize((max(1, int(A.width * f)), max(1, int(A.height * f))))
        B = B.resize((max(1, int(B.width * f)), max(1, int(B.height * f))))
        h = max(A.height, B.height)
    canvas = Image.new("RGB", (A.width + B.width + 60, h + 40), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    font = _label_font()
    draw.text((20, 4), "A", fill=(0, 0, 0), font=font)
    draw.text((A.width + 40, 4), "B", fill=(0, 0, 0), font=font)
    canvas.paste(A, (20, 34))
    canvas.paste(B, (A.width + 40, 34))
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# The element passes. Each is a CHAIN: the judge's answer to one call decides
# the next call, so only what it flagged is looked at more closely, and only
# the most specific thing that is wrong ends up in the report.
# ---------------------------------------------------------------------------

def _quota_refusal(exc: Any) -> bool:
    return getattr(exc, "status", None) in (402, 429) or "allocation" in str(exc) or "quota" in str(exc).lower()


class JudgeCalls:
    """Every judge call one element pass makes: numbered, recorded with its
    images exactly as sent (files named <prefix>_NN_K), asked JUDGE_WORKERS at
    a time. A quota refusal stops every call after it; a judge that is not
    set up stops the pass."""

    def __init__(self, judge_fn: Any, tj: Any, viewport_w: int, prefix: str):
        self.judge_fn, self.tj, self.vw, self.prefix = judge_fn, tj, viewport_w, prefix
        self.calls: List[Dict[str, Any]] = []
        self.rows: List[Dict[str, Any]] = []
        self.refused: Any = None
        self.unavailable: Any = None
        self.provider: Optional[str] = None
        self.model: Optional[str] = None

    def stopped(self) -> bool:
        return self.refused is not None or self.unavailable is not None

    def ask(self, jobs: List[Dict[str, Any]]) -> List[Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]],
                                                           Any, Dict[str, Any]]]:
        """jobs: [{state, questions, images, sources}] -> [(answers, thresholds,
        error, call record)] in the same order."""
        recs = []
        for j in jobs:
            n = len(self.calls) + 1
            call = {"n": n, "state": j["state"], "questions": list(j["questions"]),
                    "images": _sent_images(self.tj, j["images"], j["sources"], n, self.vw, self.prefix)}
            self.calls.append(call)
            recs.append(call)

        def one(j: Dict[str, Any]) -> Tuple[Any, Any, int]:
            if self.stopped():
                return None, self.refused or self.unavailable, 0
            t0 = time.time()
            try:
                return (self.judge_fn(j["state"], j["questions"], tier="image", images=j["images"],
                                      kind=TYPED_KIND), None, int((time.time() - t0) * 1000))
            except Exception as exc:
                if _quota_refusal(exc):
                    self.refused = exc
                elif getattr(exc, "reason", None) in ("off", "no-key", "no-image-judge"):
                    self.unavailable = exc
                return None, exc, int((time.time() - t0) * 1000)

        if len(jobs) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=JUDGE_WORKERS) as pool:
                outs = list(pool.map(one, jobs))
        else:
            outs = [one(j) for j in jobs]
        results = []
        for call, (res, exc, ms) in zip(recs, outs):
            call["ms"] = ms
            if exc is not None:
                call["error"] = str(exc)[:300]
                results.append((None, None, exc, call))
                continue
            self.provider, self.model = res.get("provider"), res.get("model")
            call.update({"provider": res.get("provider"), "model": res.get("model"),
                         "thresholds": res.get("thresholds")})
            results.append((res.get("answers") or {}, res.get("thresholds") or {}, None, call))
        return results


def _region_crop(path: str, box: Dict[str, float], viewport_w: int) -> Optional[bytes]:
    """One region's crop exactly as rendered, as PNG bytes: nothing is drawn
    on it. Its parts used to be outlined and numbered on the crop, and the
    judge read a number tag over a part's first letter as text cut off and
    outlines meeting as a layout defect (suss-cal, 2026-10-15: 12 of 27 flags
    on a clean page). The questions name each part instead (nameOf in
    _REGIONS_JS). None without Pillow or for an empty box."""
    if not _PIL_OK:
        return None
    import io
    img = Image.open(path).convert("RGB")
    scale = img.width / float(viewport_w or img.width)
    l = max(0, int((box["x"] - _CROP_PAD) * scale))
    t = max(0, int((box["y"] - _CROP_PAD) * scale))
    r = min(img.width, int((box["x"] + box["width"] + _CROP_PAD) * scale))
    b = min(img.height, int((box["y"] + box["height"] + _CROP_PAD) * scale))
    if r - l < 4 or b - t < 4:
        return None
    buf = io.BytesIO()
    img.crop((l, t, r, b)).save(buf, "PNG")
    return buf.getvalue()


_ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]


def _part_names(kids: List[Dict[str, Any]]) -> List[str]:
    """The name each part is asked about: its semantic name, and where two
    parts share one, which of them it is in reading order ("from the top"
    when they stack, "from the left" when they sit in a row)."""
    names = [str(k.get("say") or k.get("label") or "the part") for k in kids]
    out = list(names)
    for name in set(names):
        idx = [i for i, n in enumerate(names) if n == name]
        if len(idx) < 2:
            continue
        boxes = [kids[i]["box"] for i in idx]
        ys = sorted((b["y"], b["y"] + b["height"]) for b in boxes)
        stacked = all(ys[j + 1][0] >= ys[j][1] - 2 for j in range(len(ys) - 1))
        key = (lambda i: kids[i]["box"]["y"]) if stacked else (lambda i: kids[i]["box"]["x"])
        for rank, i in enumerate(sorted(idx, key=key)):
            nth = _ORDINALS[rank] if rank < len(_ORDINALS) else "number %d" % (rank + 1)
            out[i] = "%s (the %s of them from the %s)" % (name, nth, "top" if stacked else "left")
    return out


def _trail(nodes: List[Dict[str, Any]], n: Dict[str, Any]) -> str:
    """Where a region sits, from the top: "main column > register table > items 1-10"."""
    out: List[str] = []
    p = n.get("parent")
    while p is not None and p > 0:
        out.insert(0, nodes[p]["label"])
        p = nodes[p].get("parent")
    return " > ".join(out)


def _region_finding(sc: Dict[str, Any], nodes: List[Dict[str, Any]], n: Dict[str, Any],
                    kind: str, score: Optional[float], call: Optional[int]) -> Dict[str, Any]:
    """One finding of the page QA: what the judge flagged, at the most
    specific level it flagged. `kind`:
      element      - the smallest part the judge was shown flagged: a
                     primitive (text, image, control) or a DS component;
      arrangement  - the judge said the parts of this region sit badly
                     together (gaps, overlap, alignment between them);
      region       - the judge flagged this region, but none of its parts
                     nor their arrangement on a closer look;
      unexamined   - flagged, but the budget of judge calls ran out first."""
    ev = n.get("ev")
    if ev is None and n.get("parent") is not None:
        ev = nodes[n["parent"]].get("ev")
    out = {"id": "s%d_r%d" % (sc["n"], n["i"]), "screen": "screen %d (%s)" % (sc["n"] + 1, sc.get("label")),
           "kind": kind, "label": n["label"], "within": _trail(nodes, n),
           "selector": ("%s ... %s" % tuple(n["group"])) if n.get("group") else n["sel"],
           "score": round(score, 3) if score is not None else None, "call": call,
           "evidence": dict(ev or {})}
    if n.get("comp"):
        out["component"] = n["comp"].get("title")
    # The sentence the judge scored, so whoever decides the finding reads
    # what the judge was actually asked (an arrangement is about the region's
    # own parts; the rest about the part as its parent's call named it).
    if kind == "arrangement":
        out["asked"] = _editor_module("visual_checks").region_claim(n.get("say") or n["label"], layout=True)
    else:
        out["asked"] = _editor_module("visual_checks").region_claim(n.get("asked") or n.get("say") or n["label"])
    # What code measured at or inside this element, as evidence for whoever
    # reads the finding; it never makes or drops one.
    base = out["selector"].split(" ... ")[0]
    measured = [d.get("measured") for d in (sc.get("measured") or [])
                if d.get("measured") and (d.get("selector") == base or str(d.get("selector")).startswith(base + " > "))]
    if measured:
        out["measured"] = measured[:3]
    return out


_NTH = re.compile(r":nth-of-type\(\d+\)")


def _group_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The same flag on the same kind of element with the same text (forty
    rows of one table, or one element on two screens) is one finding,
    counted; the first keeps its evidence and call."""
    out: List[Dict[str, Any]] = []
    seen: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        key = "|".join([f.get("kind") or "", _NTH.sub("", f.get("selector") or ""), f.get("label") or ""])
        g = seen.get(key)
        if g is None:
            g = seen[key] = dict(f, count=1)
            out.append(g)
            continue
        g["count"] += 1
        if (f.get("score") or 0) > (g.get("score") or 0):
            g["score"] = f.get("score")
    return out


def region_drill(screens: List[Dict[str, Any]], calls: JudgeCalls, viewport_w: int) -> List[Dict[str, Any]]:
    """The page QA, one level at a time. Each screen starts as one region (the
    part the change impacts, or the whole screen). Its parts (read from the
    code by _REGIONS_JS) are named by what they are and the words they show,
    the crop goes as rendered with nothing drawn on it, and one call scores
    each named part on its own (box_N) and the parts as they sit together
    (layout). Every part scoring DRILL_NOUL or more is gone into the same way,
    down to a primitive or a DS component. What is reported is the most
    specific thing found:
      element      - a primitive or a DS component that scored;
      arrangement  - the parts of a region sit badly together (layout);
      region       - a region that scored while none of its parts or their
                     layout did on a closer look;
      unexamined   - scored, but the screen's share of the judge calls
                     (MAX_DRILL_CALLS split across the screens) ran out first.
    A region too tall to read on one image (over TALL_PX) is not asked: its
    parts are each looked at instead. Returns the findings."""
    vc = _editor_module("visual_checks")
    findings: List[Dict[str, Any]] = []
    # The budget is shared out: every screen the scope names gets its turn
    # (the first one used all 60 calls on a long register, 2026-10-14).
    drilled = [sc for sc in screens if ((sc.get("regions") or {}).get("nodes") or [])]
    share = max(12, MAX_DRILL_CALLS // max(1, len(drilled)))
    for sc in drilled:
        nodes = sc["regions"]["nodes"]
        start = len(calls.calls)
        # (node, score its parent's call gave it, that call's number)
        frontier: List[Tuple[Dict[str, Any], Optional[float], Optional[int]]] = [(nodes[0], None, None)]
        while frontier:
            if calls.stopped():
                break
            jobs, asked, nxt = [], [], []
            for n, p, by in frontier:
                if not n["kids"]:
                    if p is not None:
                        findings.append(_region_finding(sc, nodes, n, "element", p, by))
                    continue
                kids = [nodes[k] for k in n["kids"]]
                if n["box"]["height"] > TALL_PX:
                    nxt += [(k, p, by) for k in kids]
                    continue
                if len(calls.calls) - start + len(jobs) >= share:
                    findings.append(_region_finding(sc, nodes, n, "unexamined", p, by))
                    continue
                img = _region_crop(sc["path"], n["box"], viewport_w)
                if img is None:
                    continue
                names = _part_names(kids)
                for k, name in zip(kids, names):
                    k["asked"] = name
                where = n.get("say") or n["label"]
                qs = vc.region_questions(names, where)
                rid = "s%d_r%d" % (sc["n"], n["i"])
                jobs.append({"state": "A screenshot of %s on a web page, exactly as rendered: nothing is drawn "
                                      "on it. Each question names one of its parts by what it is and the words "
                                      "it shows." % where,
                             "questions": {"%s__%s" % (rid, k): q for k, q in qs.items()}, "images": [img],
                             "sources": [{"capture": sc["path"], "box": n["box"], "selector": n["sel"],
                                          "label": "screen %d (%s), %s" % (sc["n"] + 1, sc.get("label"),
                                                                          n["label"])}]})
                asked.append((n, p, by, kids, rid, qs))
            for (n, p, by, kids, rid, qs), (answers, th, exc, call) in zip(asked, calls.ask(jobs)):
                shown = {"type": "parts", "instructions": "Which of its parts has a visual defect?",
                         "criteria": {k: q["instructions"] for k, q in qs.items()}}
                row: Dict[str, Any] = {"id": rid, "shape": "region", "x": n["label"], "at": "screen:%d" % sc["n"],
                                       "call": call["n"], "question": shown, "claim": shown["instructions"],
                                       "selector": n["sel"], "source": "page regions",
                                       "images": [im.get("label") for im in call["images"]],
                                       "noul": None, "passed": None, "confidence": None, "band": None}
                if exc is not None:
                    row.update(status="unavailable", message=str(exc)[:200])
                    calls.rows.append(row)
                    findings.append(_region_finding(sc, nodes, n, "unexamined", p, by))
                    continue
                scores = {k: tj_noul(answers.get("%s__%s" % (rid, k))) for k in qs}
                if any(v is None for v in scores.values()):
                    row.update(status="no-answer", probabilities=scores)
                    calls.rows.append(row)
                    continue
                flagged = [(k, scores["box_%d" % (i + 1)]) for i, k in enumerate(kids)
                           if scores["box_%d" % (i + 1)] >= DRILL_NOUL]
                layout = scores["layout"] >= DRILL_NOUL
                top = max(scores.values())
                # Shown by the part's name: there are no numbers on the image.
                said = dict(zip(["box_%d" % (i + 1) for i in range(len(kids))], [k["asked"] for k in kids]),
                            layout="how its parts sit together")
                row.update({"status": "answered", "noul": round(top, 4),
                            "probabilities": {said.get(k, k): v for k, v in scores.items()},
                            "answer": "; ".join([k["asked"] for k, _s in flagged]
                                                + ([said["layout"]] if layout else [])) or "none",
                            "passed": not (flagged or layout),
                            "confidence": round(abs(top - 0.5) * 2, 4) if (flagged or layout)
                            else round(1 - top, 4),
                            "flagged": ["box_%d" % (kids.index(k) + 1) for k, _s in flagged]})
                row["band"] = "act" if row["confidence"] >= 0.6 else "escalate"
                calls.rows.append(row)
                nxt += [(k, s, call["n"]) for k, s in flagged]
                if layout:
                    findings.append(_region_finding(sc, nodes, n, "arrangement", scores["layout"], call["n"]))
                elif not flagged and p is not None:
                    findings.append(_region_finding(sc, nodes, n, "region", p, by))
            frontier = nxt
    return findings


def tj_noul(answer: Any) -> Optional[float]:
    v = _typed_judge_module().noul_value(answer)
    return None if v is None else float(v)


def _pair_questions(rid: str) -> Dict[str, Any]:
    vc = _editor_module("visual_checks")
    q, _n = vc.question({"shape": "pair", "x": "component"})
    out = {rid: q}
    for d, text in PAIR_DIMS.items():
        out["%s__%s" % (rid, d)] = {"type": "noul", "instructions": text}
    return out


def _png_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def _open_gallery(context: Any, gallery_url: str, settle_ms: int) -> Any:
    g = context.new_page()
    try:
        g.goto(gallery_url, wait_until="load", timeout=30000)
        g.wait_for_timeout(settle_ms)
    except Exception:
        g.close()
        raise
    return g


def _ring_colour(path: str, box: Dict[str, float], viewport_w: int) -> Optional[str]:
    """The colour an element sits on, read off the screenshot: the most common
    colour in the band just outside its box (a sidebar painted with an image
    or a gradient has no background-color to read). None without Pillow."""
    if not _PIL_OK:
        return None
    try:
        img = Image.open(path).convert("RGB")
        scale = img.width / float(viewport_w or img.width)
        l, t = int(box["x"] * scale), int(box["y"] * scale)
        r, b = int((box["x"] + box["width"]) * scale), int((box["y"] + box["height"]) * scale)
        d = max(2, int(4 * scale))
        counts: Dict[Tuple[int, int, int], int] = {}
        for x0, y0, x1, y1 in ((l - d, t - d, r + d, t), (l - d, b, r + d, b + d),
                               (l - d, t, l, b), (r, t, r + d, b)):
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)
            if x1 - x0 < 1 or y1 - y0 < 1:
                continue
            for n, c in (img.crop((x0, y0, x1, y1)).getcolors(1 << 20) or []):
                counts[c] = counts.get(c, 0) + n
        if not counts:
            return None
        c = max(counts, key=counts.get)
        return "rgb(%d, %d, %d)" % c
    except Exception:
        return None


def _diffs(page_props: Dict[str, Any], ds_props: Dict[str, Any]) -> Dict[str, Any]:
    return {k: {"page": v, "designSystem": ds_props.get(k)} for k, v in (page_props or {}).items()
            if (ds_props or {}).get(k) not in (None, v)}


def pair_chain(g: Any, pairs: List[Dict[str, Any]], calls: JudgeCalls, out_dir: str,
               viewport_w: int) -> Dict[str, Dict[str, Any]]:
    """The chained comparison of a page element (B) with a design-system
    component (A), for each pair {id, title, a: {selector, path, label, props,
    style}, b: {screen, box, selector, props, content, backdrop}}:
      1. A beside B in one image, scored as a whole and per dimension
         (PAIR_DIMS -> pair_verdict). Words, icon and arrangement are
         content and never fail it.
      2. Only when a style dimension (colour, border, shape, font) scored
         PAIR_CLEAR or more: A is re-shot with B's words and icon (when they
         are written in the DS's own classes) and on the colour B sits on, so
         a transparent component on a coloured bar and the gallery's sample
         text stop counting, and the dimensions are asked again. That answer
         decides.
    Rows go to calls.rows; returns {pair id: result}."""
    out: Dict[str, Dict[str, Any]] = {}

    def job(p: Dict[str, Any], a_path: str, rid: str, note: str) -> Optional[Dict[str, Any]]:
        b, sc = p["b"], p["b"]["screen"]
        crop = _crop(sc["path"], b["box"], viewport_w)
        a = _png_bytes(a_path)
        both = _side_by_side(a, crop) if (a and crop) else None
        if both is None:
            return None
        return {"state": ("One image with two UI components side by side: A on the left is the design "
                          "system's own %s, B on the right is one on the page.%s" % (p["title"], note)),
                "questions": _pair_questions(rid), "images": [both],
                "sources": [{"capture": sc["path"], "box": b["box"], "selector": b["selector"],
                             "label": "A: %s; B: screen %d (%s) cropped to %s"
                                      % (p["a"]["label"], sc["n"] + 1, sc.get("label"), b["selector"])}]}

    def record(p: Dict[str, Any], rid: str, answers: Any, exc: Any, call: Dict[str, Any],
               chain: bool) -> Dict[str, Any]:
        row: Dict[str, Any] = {"id": rid, "shape": "pair", "x": "%s component" % p["title"], "chain": chain,
                               "at": "screen:%d" % p["b"]["screen"]["n"], "call": call["n"],
                               "selector": p["b"]["selector"], "claim": "B is visually different from A.",
                               "question": {"type": "noul", "instructions": "B is visually different from A."},
                               "source": p.get("source") or "design system", "images":
                               [im.get("label") for im in call["images"]]}
        if exc is not None:
            row.update(status="unavailable", message=str(exc)[:200], passed=None, band=None)
        else:
            v = pair_verdict(answers, rid)
            row.update({"answer": v["answer"], "noul": v["noul"], "dims": v["dims"], "passed": v["passed"],
                        "confidence": v["confidence"], "band": v["band"], "probabilities": None,
                        "status": "answered" if v["noul"] is not None else "no-answer"})
        calls.rows.append(row)
        return row

    jobs, asked = [], []
    for p in pairs:
        rid = re.sub(r"[^\w.-]", "_", p["id"])[:84]
        j = job(p, p["a"]["path"], rid, "")
        if j:
            jobs.append(j)
            asked.append((p, rid))
    first: Dict[str, Dict[str, Any]] = {}
    for (p, rid), (answers, _th, exc, call) in zip(asked, calls.ask(jobs)):
        first[p["id"]] = record(p, rid, answers, exc, call, False)
    jobs2, asked2 = [], []
    for p, rid in asked:
        dims = first[p["id"]].get("dims") or {}
        if not any((dims.get(d) or 0) >= PAIR_CLEAR for d in PAIR_STYLE):
            continue
        b = p["b"]
        path = os.path.join(out_dir, "ref_%s__as_%s.png" % (re.sub(r"[^\w-]", "_", p["a"]["key"]), rid))
        backdrop = _ring_colour(b["screen"]["path"], b["box"], viewport_w) or b.get("backdrop") or "rgb(255, 255, 255)"
        note = " A has been given B's words and icon," if b.get("content") is not None else " A has been"
        note += " placed on the colour B sits on (%s)" % backdrop
        try:
            if not g.evaluate(_GALLERY_NORMALISE_JS, {"selector": p["a"]["selector"], "html": b.get("content"),
                                                      "backdrop": backdrop}):
                continue
            g.wait_for_timeout(120)
            _ref_shot(g, g.locator(p["a"]["selector"]).first, path)
        except Exception as exc:
            log("chained comparison for %s skipped (%s)" % (p["id"], exc))
            continue
        finally:
            try:
                g.evaluate(_GALLERY_RESTORE_JS)
            except Exception:
                pass
        j = job(p, path, rid + "_chain", note + ", so only the component's own style can differ.")
        if j:
            jobs2.append(j)
            asked2.append((p, rid + "_chain", note.strip()))
    second: Dict[str, Dict[str, Any]] = {}
    for (p, rid, note), (answers, _th, exc, call) in zip(asked2, calls.ask(jobs2)):
        second[p["id"]] = dict(record(p, rid, answers, exc, call, True), note=note)
    for p, _rid in asked:
        a, b = first[p["id"]], second.get(p["id"])
        final = b if (b and b.get("status") == "answered") else a
        out[p["id"]] = {"answer": final.get("answer"), "passed": final.get("passed"), "band": final.get("band"),
                        "confidence": final.get("confidence"), "call": final.get("call"),
                        "scores": a.get("dims"), "chainScores": (b or {}).get("dims"),
                        "chain": (b or {}).get("note"), "differences": _diffs(p["b"].get("props"), p["a"]["props"]),
                        "dsStyle": p["a"].get("style")}
    return out


def _unrecognised(screens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The elements the design system does not recognise (_OFF_SYSTEM_JS) on
    the screens, one per rule and look however often it repeats, counted.
    Each comes as text: its code, the rule that styles it, its look."""
    seen: Dict[str, Dict[str, Any]] = {}
    for sc in screens:
        for el in (sc.get("found") or {}).get("off") or []:
            sig = el.get("source", "") + "|" + json.dumps(el.get("props") or {}, sort_keys=True)
            if sig in seen:
                seen[sig]["count"] += 1
                continue
            ev = el.get("ev") or {}
            seen[sig] = {"id": "s%d_u%d" % (sc["n"], len(seen) + 1), "count": 1,
                         "screen": sc.get("label"), "selector": el["selector"], "source": el.get("source"),
                         "size": "%dx%d" % (round((el.get("box") or {}).get("width", 0)),
                                            round((el.get("box") or {}).get("height", 0))),
                         "code": ev.get("code"), "look": ev.get("style"), "props": el.get("props"),
                         "_el": el, "_screen": sc}
    return list(seen.values())


def shortlist_compare(context: Any, gallery_url: str, plan: Dict[str, Any], items: List[Dict[str, Any]],
                      compare: List[Dict[str, Any]], calls: JudgeCalls, settle_ms: int, out_dir: str,
                      viewport_w: int) -> Dict[str, Any]:
    """The second step of the design-system check. The ds-compare subagent
    read the unrecognised elements (_unrecognised) against the design
    system's catalog and shortlisted, for each, the components it may be a
    hand-made copy of: compare = [{selector, screen?, candidates: ["btn",
    "btn.btn--primary", ...]}]. The judge decides nothing here: each element
    (B) is put beside each candidate (A, the gallery's own of that variant)
    and scored (pair_chain). Returns {findings, unmatched}."""
    titles = {c["cls"]: c["title"] for c in (plan.get("components") or [])}
    out: Dict[str, Any] = {"findings": [], "unmatched": {}}
    todo = []
    for entry in compare or []:
        if not isinstance(entry, dict):
            continue
        sel, scr = str(entry.get("selector") or ""), entry.get("screen")
        it = next((i for i in items if i["selector"] == sel and (not scr or i["screen"] == scr)), None)
        keys = [re.sub(r"\s+", "", str(k)).lstrip(".") for k in entry.get("candidates") or [] if str(k).strip()][:3]
        if it is None:
            out["unmatched"][sel] = "not among the unrecognised elements on %s" % (scr or "the screens")
            continue
        if keys:
            todo.append((it, keys))
    if not todo:
        return out
    try:
        g = _open_gallery(context, gallery_url, settle_ms)
    except Exception as exc:
        out["error"] = "design-system gallery unavailable (%s)" % exc
        return out
    try:
        refs: Dict[str, Optional[Dict[str, Any]]] = {}
        for key in sorted({k for _it, ks in todo for k in ks}):
            parts = key.split(".")
            shown, _state = _ref_name(key)
            try:
                pick = g.evaluate(_GALLERY_PICK_JS, parts)
            except Exception as exc:
                pick = None
                out["unmatched"][key] = "the gallery could not be read (%s)" % exc
            if not pick or pick.get("stateMismatch"):
                out["unmatched"].setdefault(key, "the gallery shows no .%s" % shown)
                refs[key] = None
                continue
            p = os.path.join(out_dir, "ref_%s.png" % re.sub(r"[^\w-]", "_", key))
            try:
                _ref_shot(g, g.locator(pick["selector"]).first, p)
            except Exception as exc:
                out["unmatched"][key] = "the gallery's .%s could not be shot (%s)" % (shown, exc)
                refs[key] = None
                continue
            refs[key] = {"key": key, "selector": pick["selector"], "path": p, "props": pick.get("props"),
                         "style": pick.get("style"), "exact": pick.get("exact"),
                         "label": "the design system's own .%s%s" % (
                             shown, "" if pick.get("exact") else " (base: the gallery has no such variant)")}
        pairs = []
        for it, keys in todo:
            for k in keys:
                if refs.get(k):
                    pairs.append({"id": "%s_vs_%s" % (it["id"], re.sub(r"[^\w-]", "_", k)),
                                  "title": titles.get(k.split(".")[0]) or k.split(".")[0],
                                  "source": "shortlisted: .%s" % k, "a": refs[k],
                                  "b": dict(it["_el"], screen=it["_screen"]), "_item": it["id"], "_key": k})
        res = pair_chain(g, pairs, calls, out_dir, viewport_w)
        for it, keys in todo:
            mine = [p for p in pairs if p["_item"] == it["id"]]
            out["findings"].append({
                "id": it["id"], "kind": "shortlisted", "label": it.get("source"), "count": it["count"],
                "screen": it["screen"], "selector": it["selector"], "source": it.get("source"),
                "evidence": {"code": it.get("code"), "style": it.get("look")},
                "candidates": [dict(res.get(p["id"]) or {"answer": None}, key=p["_key"], title=p["title"],
                                    exactVariant=bool(p["a"].get("exact"))) for p in mine],
                "call": next((res[p["id"]]["call"] for p in mine if p["id"] in res), None)})
    finally:
        g.close()
    return out


def element_pass(context: Any, mode: str, screens: List[Dict[str, Any]], plan: Optional[Dict[str, Any]],
                 settle_ms: int, out_dir: str, viewport_w: int, judge_fn: Any = None,
                 scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run one element pass on the captured screens, while the browser is
    still open (the DS links re-shoot the gallery). Returns {mode, calls,
    rows, findings, unrecognised?, unmatched, message, provider, model};
    never raises.
      page - region_drill: the judge walks the part of each screen the
             change reaches, from the region down to what it flags;
      ds   - without scope.compare: the unrecognised elements, listed for
             the ds-compare subagent to shortlist (no judge call); with it:
             each beside its shortlisted components (shortlist_compare)."""
    out: Dict[str, Any] = {"mode": mode, "calls": [], "rows": [], "findings": [], "unmatched": {},
                           "message": None, "provider": None, "model": None}
    try:
        tj = _typed_judge_module()
    except Exception as exc:
        out["message"] = "typed judge unavailable: %s" % exc
        return out
    calls = JudgeCalls(judge_fn or tj.judge, tj, viewport_w, "drill" if mode == "page" else "ds")
    gallery = (plan or {}).get("gallery")
    findings: List[Dict[str, Any]] = []
    notes: List[str] = []
    for sc in screens:
        info = sc.get("found") or {}
        if info.get("scoped") and not info.get("impact"):
            notes.append("%s: none of the changed elements is on it" % sc.get("label"))
    try:
        if mode == "page":
            for sc in screens:  # the tree reads it; the findings carry it
                sc["measured"] = (sc.get("found") or {}).get("measured")
                sc["regions"] = sc.get("found")
            findings = _group_findings(region_drill(screens, calls, viewport_w))
        elif not gallery:
            out["message"] = "no design system is bound to this page"
            return out
        else:
            items = _unrecognised(screens)
            compare = (scope or {}).get("compare")
            if not isinstance(compare, list):
                out["unrecognised"] = [{k: v for k, v in it.items() if not k.startswith("_")} for it in items]
                out["message"] = ("%d unrecognised element(s): shortlist the design-system components each may "
                                  "copy, then run again with scope.compare" % len(items))
            else:
                ds = shortlist_compare(context, gallery, plan or {}, items, compare, calls, settle_ms, out_dir,
                                       viewport_w)
                findings = ds["findings"]
                out["unmatched"] = ds["unmatched"]
                if ds.get("error"):
                    out["message"] = ds["error"]
    except Exception as exc:
        log("element pass failed (%s)" % exc)
        out["message"] = "element pass failed: %s" % exc
    out.update({"calls": calls.calls, "rows": calls.rows, "findings": findings,
                "provider": calls.provider, "model": calls.model})
    if notes:
        out["notes"] = notes
    if calls.refused is not None:
        out["refused"] = _refusal_text(calls.refused)
    if calls.unavailable is not None and not calls.provider:
        out["message"] = "typed judge unavailable: %s" % calls.unavailable
    elif not out["message"]:
        out["message"] = "%d judge call(s)%s: %d finding(s)" % (
            len(calls.calls), " via %s" % calls.provider if calls.provider else "", len(findings))
        if out.get("refused"):
            out["message"] += "; the judge refused the rest: %s" % out["refused"]
    return out


def typed_checks_on_page(context: Any, url: str, args: argparse.Namespace,
                         settle_ms: int, out_dir: str, judge_fn: Any = None) -> Dict[str, Any]:
    """Every typed check for a page asked on a typed capture pass. Used where
    the battery does not run (cases mode)."""
    checks, rejected = getattr(args, "parsed_checks", None) or load_checks(getattr(args, "checks", None))
    tp = typed_pass_for(context, url, args, settle_ms, out_dir, checks, judge_fn)
    report = {"idleFrames": [], "interactions": [], "typedPass": tp}
    vw = int((getattr(args, "viewport", None) or (1280, 720))[0])
    return run_visual_checks(report, checks, rejected, args.typed_judge, vw, judge_fn)


def typed_pass_for(context: Any, url: str, args: argparse.Namespace, settle_ms: int,
                   out_dir: str, checks: List[Dict[str, Any]], judge_fn: Any = None) -> Dict[str, Any]:
    """The typed captures, then (with --typed-elements) the element pass on
    them while the browser is still open. The screens' region trees and
    component lists stay out of the report: the findings carry what they need."""
    plan = getattr(args, "ds_plan", None) or {}
    refs = sorted({c["compare"][4:] for c in checks if str(c.get("compare") or "").startswith("ref:")})
    mode = _full_pass(args)
    tp = typed_capture_pass(context, url, settle_ms, out_dir, getattr(args, "typed_steps_list", None) or [],
                            sorted({c["selector"] for c in checks if c.get("selector")}),
                            plan.get("gallery"), refs, plan or None,
                            getattr(args, "screen_collector", None),
                            what=mode or "page", scope=getattr(args, "scope_doc", None))
    if mode:
        vw = int((getattr(args, "viewport", None) or (1280, 720))[0])
        tp["elements"] = element_pass(context, mode, tp.get("screens") or [], plan, settle_ms, out_dir, vw,
                                      judge_fn, getattr(args, "scope_doc", None))
        for sc in tp.get("screens") or []:
            for k in ("found", "regions", "measured"):
                sc.pop(k, None)
    return tp


def _full_pass(args: argparse.Namespace) -> Optional[str]:
    """Which element pass was asked for: "page" (the region drill) or "ds"
    (the design-system comparison), else None. Programmatic callers that
    build args by hand get the page pass by default."""
    v = getattr(args, "typed_elements", "page")
    if v is True:
        return "page"
    return v if v in ("page", "ds") else None


def _ref_name(key: str) -> Tuple[str, str]:
    """("checkbox.checkbox--lg", "unchecked") for "checkbox.checkbox--lg.state-unchecked"."""
    parts = key.split(".")
    return (".".join(p for p in parts if not p.startswith("state-")),
            ", ".join(p[6:] for p in parts if p.startswith("state-")))


def _ref_shot(page: Any, loc: Any, path: str) -> None:
    """A gallery component framed like a page crop: its box plus _CROP_PAD on
    every side, so the two images of a same_style check show the element at
    the same scale with the same margin. Falls back to the bare element."""
    try:
        loc.scroll_into_view_if_needed(timeout=5000)
        bb = loc.bounding_box()
        if bb and bb["width"] > 0 and bb["height"] > 0:
            x, y = max(0.0, bb["x"] - _CROP_PAD), max(0.0, bb["y"] - _CROP_PAD)
            page.screenshot(path=path, clip={"x": x, "y": y,
                                             "width": bb["x"] + bb["width"] + _CROP_PAD - x,
                                             "height": bb["y"] + bb["height"] + _CROP_PAD - y})
            return
    except Exception:
        pass
    loc.screenshot(path=path, timeout=5000)


_DOC_BOXES_JS = _BOXES_JS.replace("{x: r.x, y: r.y,", "{x: r.x + window.scrollX, y: r.y + window.scrollY,")


def capture_boxes(page: Any, selectors: List[str], doc: bool = False) -> Optional[Dict[str, Any]]:
    """Where each check's element is at THIS capture, or None when no check
    needs a crop. `doc` gives page coordinates, for full-page screenshots.
    Never raises: a failed probe means no crop, not no run."""
    if not selectors:
        return None
    try:
        return page.evaluate(_DOC_BOXES_JS if doc else _BOXES_JS, selectors)
    except Exception as exc:
        log("element boxes unavailable (%s)" % exc)
        return {}


def _capture(report: Dict[str, Any], ref: str) -> Optional[Dict[str, Any]]:
    """{label, path, boxes} for a capture name, or None. The typed capture
    pass (full-page, taken after the main QA) answers `page`, its criteria
    steps and the gallery `ref:` crops; the main run answers the rest."""
    tp = report.get("typedPass") or {}
    if ref.startswith("screen:"):
        sc = next((x for x in tp.get("screens") or [] if "screen:%d" % x["n"] == ref), None)
        return ({"label": "screen %d (%s)" % (sc["n"] + 1, sc.get("label")), "path": sc["path"],
                 "boxes": sc.get("boxes") or {}, "full": True} if sc else None)
    if ref.startswith("ref:"):
        r = (tp.get("refs") or {}).get(ref[4:])
        return dict(r) if r else None
    if ref == "page" and tp.get("settled"):
        return {"label": "the page", "path": tp["settled"]["path"], "boxes": tp["settled"].get("boxes"),
                "full": True}
    if ref.startswith(("before:", "after:")):
        side, step = ref.split(":", 1)
        for ix in tp.get("interactions") or []:
            if ix.get("step") == step:
                return {"label": "%s %s" % (side, step), "path": ix["%sPath" % side],
                        "boxes": ix.get("%sBoxes" % side), "full": True}
    idle = report.get("idleFrames") or []
    if ref == "page":
        ref = "idle:start"
    if ref.startswith("idle:"):
        which = ref.split(":", 1)[1]
        frame = None
        if idle and which == "start":
            frame = idle[0]
        elif idle and which == "end":
            frame = idle[-1]
        elif idle and which == "motion":
            frame = max(idle[1:] or idle, key=lambda f: f.get("diffFromPrev") or 0.0)
        elif which.isdigit() and int(which) < len(idle):
            frame = idle[int(which)]
        if not frame:
            return None
        return {"label": "idle t=%.2fs" % float(frame.get("t", 0.0)), "path": frame["path"],
                "boxes": frame.get("boxes")}
    side, step = ref.split(":", 1)
    ixs = report.get("interactions") or []
    ix = (ixs[-1] if ixs and step == "last"
          else next((x for x in ixs if x.get("step") == step), None))
    if not ix:
        return None
    return {"label": "%s %s" % (side, ix.get("step")), "path": ix["%sPath" % side],
            "boxes": ix.get("%sBoxes" % side)}


def _crop(path: str, box: Dict[str, float], viewport_w: int) -> Optional[bytes]:
    if not _PIL_OK:
        return None
    import io
    img = Image.open(path)
    scale = img.width / float(viewport_w or img.width)
    l = max(0, int((box["x"] - _CROP_PAD) * scale))
    t = max(0, int((box["y"] - _CROP_PAD) * scale))
    r = min(img.width, int((box["x"] + box["width"] + _CROP_PAD) * scale))
    b = min(img.height, int((box["y"] + box["height"] + _CROP_PAD) * scale))
    if r - l < 4 or b - t < 4:
        return None
    buf = io.BytesIO()
    img.crop((l, t, r, b)).save(buf, "PNG")
    return buf.getvalue()


def _one_colour_share(data: bytes) -> Optional[float]:
    """Share of the image taken by its most common colour (1.0 = blank), on a
    64x64 thumbnail. None without Pillow."""
    if not _PIL_OK:
        return None
    import io
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB").resize((64, 64))
        colours = img.getcolors(64 * 64) or []
        return round(max(n for n, _c in colours) / 4096.0, 3) if colours else None
    except Exception:
        return None


def _sent_images(tj: Any, images: List[Any], sources: List[Dict[str, Any]], call_n: int,
                 viewport_w: int, prefix: str = "sent") -> List[Dict[str, Any]]:
    """Each image of one judge call as the judge receives it: load_image is
    what judge() runs (a tall full-page shot may be downscaled there), so the
    bytes saved here are the bytes sent. A crop is written next to its
    capture; a frame sent unchanged is its capture file. Never raises."""
    out: List[Dict[str, Any]] = []
    for i, (img, src) in enumerate(zip(images, sources)):
        rec: Dict[str, Any] = {"label": src.get("label"), "capture": src.get("capture"),
                               "box": src.get("box"), "selector": src.get("selector"),
                               "viewportW": viewport_w}
        try:
            uri = tj.load_image(img)
            head, b64 = uri.split(",", 1)
            data = base64.b64decode(b64)
            kind = tj.sniff_image(data) or "png"
            size = tj.image_size(data, kind) or (0, 0)
            same = False
            if isinstance(img, dict) and img.get("path"):
                try:
                    same = os.path.getsize(img["path"]) == len(data)
                except OSError:
                    same = False
            if same:
                path = img["path"]
            else:
                path = os.path.join(os.path.dirname(src.get("capture") or "."),
                                    "%s_%02d_%d.%s" % (prefix, call_n, i + 1, "jpg" if kind == "jpeg" else kind))
                with open(path, "wb") as f:
                    f.write(data)
            rec.update({"path": path, "width": size[0], "height": size[1], "bytes": len(data),
                        "oneColour": _one_colour_share(data)})
        except Exception as exc:
            rec["error"] = str(exc)[:200]
        out.append(rec)
    return out


def run_visual_checks(report: Dict[str, Any], checks: List[Dict[str, Any]],
                      rejected: List[Dict[str, Any]], mode: str, viewport_w: int,
                      judge_fn: Any = None) -> Dict[str, Any]:
    """Ask the image-tier typed judge each check, with exactly the images it
    names (cropped to its element when it has a selector). ALWAYS returns a
    block; never raises."""
    block: Dict[str, Any] = {"mode": mode, "kind": TYPED_KIND, "available": False,
                             "provider": None, "checks": [], "rejected": rejected,
                             "message": None}
    tp = report.get("typedPass") or {}
    if (tp.get("settled") or {}).get("path"):
        block["pageShot"] = tp["settled"]["path"]
    # The element pass (page drill or DS comparison) already asked its own
    # calls: they come first, its rows join the checks, its findings are the
    # report's findings.
    el = tp.get("elements") or {}
    el_rows: List[Dict[str, Any]] = list(el.get("rows") or [])
    if el:
        block["calls"] = list(el.get("calls") or [])
        block["findings"] = list(el.get("findings") or [])
        block["elements"] = {k: el.get(k) for k in ("mode", "message", "unmatched", "refused", "notes")
                             if el.get(k) not in (None, {}, [])}
        if "unrecognised" in el:
            block["unrecognised"] = el["unrecognised"]
        if el.get("provider"):
            block.update({"available": True, "provider": el["provider"], "model": el.get("model")})
            block["requests"] = sum(1 for c in block["calls"] if not c.get("error"))
    if not checks:
        block["checks"] = el_rows
        block["message"] = el.get("message") if el else (
            "no checks to run" + (" (%d rejected)" % len(rejected) if rejected else ""))
        if el_rows:
            block["summary"] = _typed_summary(el_rows)
        return block
    try:
        tj = _typed_judge_module()
    except Exception as exc:
        block["message"] = "typed judge unavailable: %s" % exc
        return block
    judge_fn = judge_fn or tj.judge
    vc = _editor_module("visual_checks")
    # Resolve every check to the exact images it needs, then ask ALL the
    # checks that share those images in ONE call: a screenshot (or one
    # element's crop) gets its whole criteria list at once.
    groups: Dict[str, Dict[str, Any]] = {}
    order: List[Tuple[str, Dict[str, Any]]] = []
    for c in checks:
        row: Dict[str, Any] = dict(c, status=None, noul=None, passed=None,
                                   confidence=None, band=None, images=[])
        refs = ([c["compare"]] if c.get("compare") else []) + [c["at"]]
        caps = [_capture(report, r) for r in refs]
        if any(cap is None for cap in caps):
            notes = (report.get("typedPass") or {}).get("refNotes") or {}
            row["status"] = "no-capture"
            row["message"] = "; ".join(
                notes.get(r[4:]) if r.startswith("ref:") and notes.get(r[4:]) else
                "no capture named %s in this run" % r for r, cap in zip(refs, caps) if cap is None)
            order.append(("", row))
            continue
        images: List[Any] = []
        sources: List[Dict[str, Any]] = []
        missing = None
        for ref, cap in zip(refs, caps):
            if ref.startswith("ref:") and cap.get("style"):
                row["evidence"] = dict(row.get("evidence") or {}, dsStyle=cap["style"])
            sel = c.get("selector")
            if sel and isinstance(cap.get("boxes"), dict):
                box = cap["boxes"].get(sel)
                if box is None:
                    missing = ref
                    break
                crop = _crop(cap["path"], box, viewport_w)
                if crop is None and _PIL_OK:
                    missing = ref  # a zero-size or off-image box: nothing to show
                    break
                images.append(crop if crop is not None else {"path": cap["path"]})
                row["images"].append(cap["label"] + (" cropped to " + sel if crop else " (full frame)"))
                sources.append({"capture": cap["path"], "label": row["images"][-1],
                                "box": box if crop is not None else None, "selector": sel})
            else:
                images.append({"path": cap["path"]})
                row["images"].append(cap["label"])
                sources.append({"capture": cap["path"], "label": cap["label"], "box": None})
        if missing:
            row["status"] = "not-visible" if c.get("optional") else "element-missing"
            row["message"] = "%s is not visible on the page at %s" % (c["selector"], missing)
            order.append(("", row))
            continue
        if c.get("shape") == "pair" and len(images) == 2:
            both = _side_by_side(images[0], images[1])
            if both is not None:
                images = [both]
                sources = [{"capture": sources[1].get("capture"), "box": None,
                            "label": "A: %s; B: %s" % (sources[0].get("label"), sources[1].get("label"))}]
        row["claim"] = c["question"]["instructions"]
        key = json.dumps([refs, c.get("selector") or "", c.get("context") or ""])
        g = groups.setdefault(key, {"images": images, "labels": row["images"], "rows": [],
                                    "context": c.get("context") or "", "sources": sources})
        g["rows"].append(row)
        order.append((key, row))
    # Every call is numbered and its images saved first, in order; then the
    # calls go to the judge JUDGE_WORKERS at a time.
    jobs: List[Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], str]] = []
    for key, g in groups.items():
        labels = g["labels"]
        state = ("A screenshot of a web page%s." % (
            "" if len(g["images"]) == 1 else
            ": image 1 is %s, image 2 is %s" % (labels[0], labels[1])))
        if g["rows"] and g["rows"][0].get("shape") == "pair" and len(g["images"]) == 1:
            state = ("One image with two UI components side by side: A on the left is the design system's "
                     "own %s, B on the right is the one on the page." % g["rows"][0].get("x"))
        if g["context"]:
            state += " " + g["context"]
        for start in range(0, len(g["rows"]), 64):
            part = g["rows"][start:start + 64]
            # The record of this call: the state text and every image exactly
            # as the judge receives it, so the report shows what was asked about.
            n = len(block.setdefault("calls", [])) + 1
            call: Dict[str, Any] = {"n": n, "state": state, "questions": [r["id"] for r in part],
                                    "images": _sent_images(tj, g["images"], g["sources"], n, viewport_w)}
            block["calls"].append(call)
            for r in part:
                r["call"] = n
            jobs.append((call, part, g, state))

    # A judge that refuses for quota (Cloudflare's daily free allowance, a
    # 429) refuses every call after it too: stop asking, say why once.
    refused: List[Any] = []

    def ask(job: Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], str]) -> Tuple[Any, Any, int]:
        _call, part, g, state = job
        if refused:
            return None, refused[0], 0
        t0 = time.time()
        try:
            questions: Dict[str, Any] = {}
            for r in part:
                questions[r["id"]] = r["question"]
                if r.get("shape") == "pair":
                    for d, text in PAIR_DIMS.items():
                        questions["%s__%s" % (r["id"], d)] = {"type": "noul", "instructions": text}
            return (judge_fn(state, questions, tier="image", images=g["images"], kind=TYPED_KIND),
                    None, int((time.time() - t0) * 1000))
        except Exception as exc:
            if getattr(exc, "status", None) in (402, 429) or "allocation" in str(exc) or "quota" in str(exc).lower():
                refused.append(exc)
            return None, exc, int((time.time() - t0) * 1000)

    if len(jobs) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=JUDGE_WORKERS) as pool:
            outcomes = list(pool.map(ask, jobs))
    else:
        outcomes = [ask(j) for j in jobs]
    unavailable = None
    for (call, part, _g, _state), (res, exc, ms) in zip(jobs, outcomes):
        call["ms"] = ms
        if exc is not None:
            call["error"] = str(exc)[:300]
            for r in part:
                r["status"] = "unavailable"
                r["message"] = str(exc)[:200]
            if getattr(exc, "reason", None) in ("off", "no-key", "no-image-judge"):
                unavailable = exc
            continue
        call.update({"provider": res.get("provider"), "model": res.get("model"),
                     "thresholds": res.get("thresholds")})
        block["available"] = True
        block["provider"] = res.get("provider")
        block["model"] = res.get("model")
        block["trustPass"] = bool(res["thresholds"].get("trustPass"))
        block["requests"] = int(block.get("requests") or 0) + 1
        for r in part:
            raw = res["answers"].get(r["id"])
            if r.get("shape") == "pair":
                v = pair_verdict(res["answers"], r["id"])
                r.update({"answer": v["answer"], "noul": v["noul"], "dims": v["dims"], "passed": v["passed"],
                          "confidence": v["confidence"], "band": v["band"], "probabilities": None,
                          "status": "answered" if v["noul"] is not None else "no-answer"})
                continue
            v = vc.verdict(r["question"], raw, res["thresholds"], r.get("expect"))
            r.update({"answer": v["answer"], "noul": v.get("noul"), "passed": v["passed"],
                      "confidence": v["confidence"], "band": v["band"],
                      "probabilities": (raw.get("probabilities") if isinstance(raw, dict) else None),
                      "status": "answered" if v["answer"] is not None else "no-answer"})
    if refused:
        block["refused"] = _refusal_text(refused[0])
    if unavailable is not None and not block["available"]:
        block["message"] = "typed judge unavailable: %s" % unavailable
        for _k, r in order:
            if r["status"] is None:
                r["status"] = "unavailable"
        block["checks"] = el_rows + [r for _k, r in order]
        return block
    block["checks"] = el_rows + [r for _k, r in order]
    answered = [r for _k, r in order if r["status"] == "answered"]
    block["summary"] = _typed_summary(block["checks"])
    block["message"] = "%d check(s) answered via %s" % (len(answered), block["provider"])
    if block.get("refused"):
        block["message"] += "; the judge refused the rest: %s" % block["refused"]
    if el.get("message"):
        block["message"] += "; %s" % el["message"]
    return block


def _typed_summary(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    answered = [r for r in rows if r.get("status") == "answered"]
    return {
        "confidentPass": sum(1 for r in answered if r.get("passed") is True and r.get("band") == "act"),
        "confidentFail": sum(1 for r in answered if r.get("passed") is False and r.get("band") == "act"),
        "unsure": sum(1 for r in answered if r.get("band") != "act"),
        "elementMissing": sum(1 for r in rows if r.get("status") == "element-missing"),
        "notAsked": sum(1 for r in rows if r.get("status") != "answered"),
    }


def _refusal_text(exc: Any) -> str:
    """One readable line for a judge's quota refusal."""
    text = str(exc)
    if "daily free allocation" in text:
        return ("Cloudflare's daily free allowance (10,000 neurons) is used up; it resets daily, "
                "or move the account to Workers Paid to keep going")
    return text[:200]


def _all_confident_pass(block: Optional[Dict[str, Any]]) -> bool:
    rows = (block or {}).get("checks") or []
    return bool(rows) and all(r.get("status") == "answered" and r.get("passed") is True
                              and r.get("band") == "act" for r in rows)


def apply_frame_judges(report: Dict[str, Any], verdict: str, reasons: List[str],
                       out_dir: str, args: argparse.Namespace,
                       llm_judge: Any = None, checks_fn: Any = None,
                       shadow_log: Any = None) -> str:
    """The optional judges, in their precedence. Mutates report/reasons and
    returns the verdict. The LLM frame judge (--judge prose) only ESCALATES or
    CONFIRMS; it never relaxes an error/static/no-reaction pixel verdict:
      - judge unavailable  -> a pixel pass becomes inconclusive.
      - judge ok:false     -> a pixel pass becomes "effect-wrong".
      - judge ok:true      -> CONFIRMS; verdict unchanged.
      - judge inconclusive -> a pixel pass becomes inconclusive.
    The typed checks (run_visual_checks) never change any of that."""
    mode = getattr(args, "typed_judge", None)
    checks, rejected = (getattr(args, "parsed_checks", None) or ([], []))
    block = None
    if mode and (checks or rejected or (report.get("typedPass") or {}).get("screens")):
        block = (checks_fn or run_visual_checks)(report, checks, rejected, mode,
                                                 int((getattr(args, "viewport", None) or (1280, 720))[0]))
        report["typedChecks"] = block
    if not args.judge:
        _flag_and_log(report, block, mode, args, shadow_log)
        return verdict

    if (block and mode == "flag" and block.get("trustPass") and _all_confident_pass(block)):
        judge = {"available": True, "ok": True, "expected": args.judge,
                 "reasoning": "every typed check is a confident pass (%s) and trustPass is "
                              "calibrated for %s" % (block.get("provider"), TYPED_KIND),
                 "observed": None, "model": block.get("model"), "transport": "typed-checks",
                 "skippedLlm": True,
                 "message": "LLM frame judge skipped: calibrated typed pass on every check"}
    else:
        judge = (llm_judge or run_judge)(report, out_dir, args)
    report["judge"] = judge
    if judge.get("available"):
        if judge.get("ok") is False and verdict == "pass":
            verdict = "effect-wrong"
            reasons.append(
                "frame-judge: expected effect NOT achieved (%s)"
                % (judge.get("reasoning") or "no reasoning given"))
        elif judge.get("ok") is True:
            reasons.append("frame-judge confirmed the expected effect")
        elif judge.get("ok") is None:
            if verdict == "pass":
                verdict = "inconclusive"
            reasons.append("frame-judge inconclusive: %s"
                           % (judge.get("message") or "no parseable verdict"))
    else:
        if verdict == "pass":
            verdict = "inconclusive"
        reasons.append("frame-judge unavailable: %s"
                       % (judge.get("message") or "unknown reason"))
    log(judge.get("message") or "frame-judge completed")
    _flag_and_log(report, block, mode, args, shadow_log)
    return verdict


def _flag_and_log(report: Dict[str, Any], block: Optional[Dict[str, Any]], mode: Optional[str],
                  args: argparse.Namespace, shadow_log: Any) -> None:
    """Shadow-log every answered check (for labelling; it is NOT paired with
    the LLM's whole-effect verdict, which answers a different question) and, in
    flag mode, add one finding per confident failure or missing element."""
    if not block:
        return
    try:
        sink = shadow_log or _typed_judge_module().shadow_log
    except Exception:
        sink = None
    for r in block.get("checks") or []:
        if r.get("status") == "answered" and sink:
            # The row keeps its log id, so whoever later looks at its images
            # (the visual-qa subagent) can label exactly this answer.
            r["logId"] = "%s%06x" % (time.strftime("%y%m%d%H%M%S"), random.getrandbits(24))
            try:
                sink({"id": r["logId"], "provider": block.get("provider"), "kind": TYPED_KIND,
                      "noul": r.get("noul"), "llmOk": None,
                      "project": getattr(args, "judge_project", None),
                      "answer": r.get("answer"), "confidence": r.get("confidence"),
                      "band": r.get("band"),
                      "subject": "%s: %s @ %s" % (r["id"], r.get("claim"), r["at"])})
            except Exception:
                pass
        if mode != "flag":
            continue
        if r.get("status") == "element-missing":
            report.setdefault("findings", []).append({
                "rule": "typed-judge", "severity": "warn", "kind": TYPED_KIND,
                "check": r["id"], "message": "check %s: %s" % (r["id"], r.get("message"))})
        elif r.get("status") == "answered" and r.get("passed") is False and r.get("band") == "act":
            report.setdefault("findings", []).append({
                "rule": "typed-judge", "severity": "warn", "kind": TYPED_KIND,
                "check": r["id"], "provider": block.get("provider"), "noul": r.get("noul"),
                "message": "check %s is confidently not met at %s (judge said %s): %s"
                           % (r["id"], ", ".join(r.get("images") or [r["at"]]), r.get("answer"),
                              r.get("claim"))})
    log(block.get("message") or "typed checks completed")


def exit_code(verdict: str) -> int:
    if verdict == "pass":
        return 0
    if verdict == "error":
        return 2
    if verdict == "effect-wrong":
        return 4  # pixels moved but the wrong thing renders (frame-judge)
    if verdict == "blank":
        return 5  # render mode: loaded but painted nothing / unstyled wash
    return 1  # static or no-reaction


# ---------------------------------------------------------------------------
# Test-case runner (--cases). Executes a piece's plan-time test-cases.json
# end to end: hand-written cases (journeys / abuse / regression), the
# auto-expanded intent x phase matrix, abuse templates, and a seeded soak.
# Design: docs/features/qa-test-cases.md. The file lives next to the piece's
# research.md and is written by the family researcher at planning time.
# ---------------------------------------------------------------------------

CASE_DEFAULT_BUDGET_MS = 8000
WAITFOR_DEFAULT_TIMEOUT_MS = 5000
CASE_SETTLE_DEFAULT_MS = 400
# Pause after the last step before judging expects, so async errors (next
# rAF tick, promise rejections) surface into the page-error listener.
CASE_ERROR_DRAIN_MS = 150
SOAK_DEFAULT_SECONDS = 30
SOAK_MAX_SECONDS = 120


def _js_expr(expr: str) -> str:
    """Wrap a JS expression so evaluation never throws into Playwright:
    returns {ok, val} or {ok:false, err}."""
    return ("(function(){try{return {ok:true,val:(" + expr + ")};}"
            "catch(e){return {ok:false,err:String(e)};}})()")


def _js_harness_call(harness: str, method: str, args_js: str) -> str:
    """Call <harness>.<method>(<args>) defensively. Returns {ok, val} or
    {ok:false, err}. A missing harness/method is an err, not a throw."""
    return ("(function(){var h=null;try{h=" + harness + ";}catch(e){}"
            "if(!h||typeof h." + method + "!=='function')"
            "{return {ok:false,err:'harness " + method + " missing'};}"
            "try{var r=h." + method + "(" + args_js + ");"
            "return {ok:true,val:(r===undefined?null:r)};}"
            "catch(e){return {ok:false,err:String(e)};}})()")


def run_case_step(page: Any, step: Dict[str, Any],
                  ctx: Dict[str, Any]) -> Optional[str]:
    """Execute ONE case step. Returns None on success or an error string.
    The raw pointer/keyboard five delegate to run_step()."""
    kind = step.get("type")
    if kind in ("move", "click", "drag", "scroll", "key"):
        run_step(page, step)
        return None
    if kind == "settle":
        page.wait_for_timeout(int(step.get("ms", CASE_SETTLE_DEFAULT_MS)))
        return None
    if kind == "resize":
        w = int(step.get("width", 900))
        h = int(step.get("height", 600))
        page.set_viewport_size({"width": w, "height": h})
        ctx["viewport"] = (w, h)
        return None
    if kind == "eval":
        res = page.evaluate(_js_expr(step.get("expr", "true")))
        if not res.get("ok"):
            return "eval threw: %s (expr: %s)" % (res.get("err"),
                                                  step.get("expr"))
        return None
    if kind == "waitFor":
        timeout_ms = int(step.get("timeoutMs", WAITFOR_DEFAULT_TIMEOUT_MS))
        expr = step.get("expr", "true")
        deadline = time.time() + timeout_ms / 1000.0
        while time.time() < deadline:
            res = page.evaluate(_js_expr(expr))
            if res.get("ok") and res.get("val"):
                return None
            page.wait_for_timeout(100)
        return "waitFor timed out after %dms: %s" % (timeout_ms, expr)
    if kind == "intent":
        intent = step.get("intent")
        opts = step.get("opts") or {}
        args_js = json.dumps(intent) + "," + json.dumps(opts)
        res = page.evaluate(
            _js_harness_call(ctx["harness"], "injectFakeInput", args_js))
        if not res.get("ok"):
            return "intent %r failed: %s" % (intent, res.get("err"))
        # A false return means "ignored in this phase" - legal, not a failure.
        # Crashes surface as page errors and are judged by expects.
        return None
    if kind == "tick":
        secs = float(step.get("seconds", 1.0))
        res = page.evaluate(
            _js_harness_call(ctx["harness"], "tick", json.dumps(secs)))
        if not res.get("ok"):
            return "tick failed: %s" % res.get("err")
        return None
    return "unknown step type: %r" % kind


def _expand_matrix_cases(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Auto-generate the intent x phase grid: for every phase that has a
    phaseSetups entry, inject every intent and require no crash. This is the
    direct check for 'fine in one state, breaks when you interact in
    another'."""
    m = doc.get("matrix") or {}
    if not m.get("auto"):
        return []
    phases = doc.get("phases") or []
    intents = doc.get("intents") or []
    setups = doc.get("phaseSetups") or {}
    excluded = set()
    for pair in (m.get("exclude") or []):
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            excluded.add((pair[0], pair[1]))
    phase_expr = doc.get("phaseExpr")
    cases: List[Dict[str, Any]] = []
    for ph in phases:
        if ph not in setups:
            log("matrix: no phaseSetups entry for phase %r; skipping its row"
                % ph)
            continue
        for it in intents:
            if (it, ph) in excluded:
                continue
            case: Dict[str, Any] = {
                "id": "mx-%s-%s" % (it, ph),
                "kind": "matrix",
                "title": "intent %r during phase %r must not crash" % (it, ph),
                "given": setups[ph],
                "steps": [{"type": "intent", "intent": it},
                          {"type": "settle", "ms": CASE_SETTLE_DEFAULT_MS}],
                "expect": [],
            }
            if phase_expr:
                case["expect"].append(
                    {"type": "eval", "expr": phase_expr, "in": phases})
            cases.append(case)
    return cases


# Named abuse templates the researcher can apply without writing the steps.
ABUSE_TEMPLATES = ("spam-intents", "pointer-storm", "resize-cycle",
                   "long-idle")


def _expand_abuse_cases(doc: Dict[str, Any],
                        viewport: Tuple[int, int]) -> List[Dict[str, Any]]:
    ab = doc.get("abuse") or {}
    apply_list = ab.get("apply") or []
    if not apply_list:
        return []
    setups = doc.get("phaseSetups") or {}
    setup = ab.get("setup")
    if setup is None and ab.get("phase"):
        setup = setups.get(ab.get("phase"))
    setup = setup or []
    intents = doc.get("intents") or []
    vw, vh = viewport
    cases: List[Dict[str, Any]] = []
    for name in apply_list:
        if name == "spam-intents":
            steps: List[Dict[str, Any]] = []
            for it in intents:
                for _ in range(15):
                    steps.append({"type": "intent", "intent": it})
            steps.append({"type": "settle", "ms": 800})
            cases.append({
                "id": "ab-spam-intents", "kind": "abuse",
                "title": "every intent spammed 15x fast must not crash",
                "given": setup, "steps": steps, "expect": [],
                "budgetMs": 20000,
            })
        elif name == "pointer-storm":
            # Deterministic storm: sweeps, corners, and out-of-stage points.
            pts = [(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95),
                   (0.5, 0.5), (0.01, 0.5), (0.99, 0.5), (0.5, 0.01),
                   (0.5, 0.99), (0.33, 0.66), (0.66, 0.33), (0.5, 0.5)]
            steps = []
            for (fx, fy) in pts:
                x = max(1.0, min(vw - 1.0, vw * fx))
                y = max(1.0, min(vh - 1.0, vh * fy))
                steps.append({"type": "move", "x": x, "y": y})
                steps.append({"type": "click", "x": x, "y": y})
            steps.append({"type": "settle", "ms": 600})
            cases.append({
                "id": "ab-pointer-storm", "kind": "abuse",
                "title": "rapid clicks across and outside the stage must "
                         "not crash",
                "given": setup, "steps": steps, "expect": [],
                "budgetMs": 20000,
            })
        elif name == "resize-cycle":
            steps = []
            for (w, h) in ((480, 800), (1440, 900), (700, 700), (vw, vh)):
                steps.append({"type": "resize", "width": w, "height": h})
                steps.append({"type": "settle", "ms": 350})
            cases.append({
                "id": "ab-resize-cycle", "kind": "abuse",
                "title": "viewport resizes mid-session must not crash",
                "given": setup, "steps": steps,
                "expect": [{"type": "notBlank"}],
                "budgetMs": 15000,
            })
        elif name == "long-idle":
            cases.append({
                "id": "ab-long-idle", "kind": "abuse",
                "title": "a long idle stretch must not crash or blank",
                "given": setup,
                "steps": [{"type": "settle", "ms": 10000}],
                "expect": [{"type": "notBlank"}],
                "budgetMs": 15000,
            })
        else:
            log("abuse: unknown template %r (known: %s); skipped"
                % (name, ", ".join(ABUSE_TEMPLATES)))
    return cases


def _eval_expects(page: Any, case: Dict[str, Any], ctx: Dict[str, Any],
                  page_errors: List[str], console_errors: List[str],
                  shots: Dict[str, str]) -> List[Dict[str, Any]]:
    """Evaluate a case's expects. noPageErrors is implicit on every case.
    Returns the list of FAILED expects (empty = case passed)."""
    fails: List[Dict[str, Any]] = []
    expects = list(case.get("expect") or [])
    if not any(e.get("type") == "noPageErrors" for e in expects):
        expects.append({"type": "noPageErrors"})
    for exp in expects:
        etype = exp.get("type")
        if etype == "noPageErrors":
            if page_errors:
                fails.append({"expect": "noPageErrors",
                              "detail": page_errors[:5]})
        elif etype == "noConsoleErrors":
            allow = exp.get("allow") or []
            errs = []
            for e in console_errors:
                allowed = False
                for pat in allow:
                    try:
                        if re.search(pat, e):
                            allowed = True
                            break
                    except re.error:
                        pass
                if not allowed:
                    errs.append(e)
            if errs:
                fails.append({"expect": "noConsoleErrors",
                              "detail": errs[:5]})
        elif etype == "eval":
            res = page.evaluate(_js_expr(exp.get("expr", "true")))
            if not res.get("ok"):
                fails.append({"expect": "eval", "expr": exp.get("expr"),
                              "detail": "expression threw: %s"
                                        % res.get("err")})
                continue
            val = res.get("val")
            if "equals" in exp:
                if val != exp["equals"]:
                    fails.append({"expect": "eval", "expr": exp.get("expr"),
                                  "detail": "expected == %r, got %r"
                                            % (exp["equals"], val)})
            elif "in" in exp:
                if val not in (exp["in"] or []):
                    fails.append({"expect": "eval", "expr": exp.get("expr"),
                                  "detail": "expected one of %r, got %r"
                                            % (exp["in"], val)})
            else:
                if not val:
                    fails.append({"expect": "eval", "expr": exp.get("expr"),
                                  "detail": "expected truthy, got %r" % val})
        elif etype == "notBlank":
            path = shots.get("after")
            if path:
                blank = frame_is_blank(path)
                if blank is True:
                    fails.append({"expect": "notBlank",
                                  "detail": "frame is a flat blank wash"})
        elif etype == "frameChanged":
            before = shots.get("before")
            after = shots.get("after")
            if before and after:
                d = diff_frames(before, after)
                if d <= DIFF_EPSILON:
                    fails.append({"expect": "frameChanged",
                                  "detail": "diff %.4f <= eps %.4f"
                                            % (d, DIFF_EPSILON)})
        else:
            fails.append({"expect": str(etype),
                          "detail": "unknown expect type"})
    return fails


def _case_needs_frames(case: Dict[str, Any]) -> bool:
    for e in case.get("expect") or []:
        if e.get("type") in ("notBlank", "frameChanged"):
            return True
    return False


def _safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s or "case")[:80]


def _run_one_case(context: Any, url: str, case: Dict[str, Any],
                  base_ctx: Dict[str, Any], settle_ms: int,
                  out_dir: str, on_screen: Any = None) -> Dict[str, Any]:
    """Run one case on a FRESH page (isolation between cases). Returns the
    per-case report entry."""
    console_errors: List[str] = []
    page_errors: List[str] = []
    result: Dict[str, Any] = {
        "id": case.get("id"),
        "kind": case.get("kind"),
        "title": case.get("title"),
        "verdict": "pass",
        "failedExpect": [],
        "error": None,
        "pageErrors": page_errors,
        "consoleErrors": console_errors,
    }
    ctx = dict(base_ctx)
    budget_ms = int(case.get("budgetMs", CASE_DEFAULT_BUDGET_MS))
    page = context.new_page()
    page.on("console", lambda m: console_errors.append(m.text)
            if getattr(m, "type", "") == "error" else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    started = time.time()
    shots: Dict[str, str] = {}
    sid = _safe_id(str(case.get("id")))
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(settle_ms)
        needs_frames = _case_needs_frames(case)
        step_err: Optional[str] = None
        for group_name in ("given", "steps"):
            if step_err:
                break
            if group_name == "steps" and needs_frames:
                shots["before"] = os.path.join(out_dir,
                                               "case_%s_before.png" % sid)
                page.screenshot(path=shots["before"])
            for step in (case.get(group_name) or []):
                if (time.time() - started) * 1000.0 > budget_ms:
                    step_err = ("budgetMs %d exceeded (possible freeze/hang)"
                                % budget_ms)
                    break
                err = run_case_step(page, step, ctx)
                if err:
                    step_err = "%s step failed: %s" % (group_name, err)
                    break
        if step_err:
            result["verdict"] = "fail"
            result["error"] = step_err
        # Let async errors (next tick / rejected promises) surface.
        page.wait_for_timeout(CASE_ERROR_DRAIN_MS)
        if needs_frames and not step_err:
            shots["after"] = os.path.join(out_dir, "case_%s_after.png" % sid)
            page.screenshot(path=shots["after"])
        fails = _eval_expects(page, case, ctx, page_errors, console_errors,
                              shots)
        # The screen this case ended on, for the typed checks: after the
        # expects, so it never touches the case's verdict.
        if on_screen and not step_err:
            try:
                on_screen(page, "after case %s" % case.get("id"))
            except Exception:
                pass
        if fails:
            result["verdict"] = "fail"
            result["failedExpect"] = fails
        if result["verdict"] == "fail" and "after" not in shots:
            try:
                fail_shot = os.path.join(out_dir, "case_%s_fail.png" % sid)
                page.screenshot(path=fail_shot)
                shots["fail"] = fail_shot
            except Exception:
                pass
    except Exception as exc:
        result["verdict"] = "fail"
        result["error"] = "case run threw: %s" % exc
    finally:
        result["frames"] = shots
        try:
            page.close()
        except Exception:
            pass
    return result


def _run_soak(context: Any, url: str, doc: Dict[str, Any],
              base_ctx: Dict[str, Any], settle_ms: int,
              out_dir: str) -> Optional[Dict[str, Any]]:
    """Seeded monkey run: random-but-replayable intents + pointer noise for
    N seconds. Reproducible by seed. Catches the combinations nobody wrote
    down."""
    soak = doc.get("soak")
    if not isinstance(soak, dict):
        return None
    seconds = min(float(soak.get("seconds", SOAK_DEFAULT_SECONDS)),
                  float(SOAK_MAX_SECONDS))
    seed = int(soak.get("seed", 1337))
    rng = random.Random(seed)
    intents = list(soak.get("intents") or doc.get("intents") or [])
    opts_pool = soak.get("optsPool") or {}
    fast = bool(soak.get("fastForward"))
    setups = doc.get("phaseSetups") or {}
    setup = setups.get(soak.get("phase")) if soak.get("phase") else None
    setup = setup or []
    console_errors: List[str] = []
    page_errors: List[str] = []
    res: Dict[str, Any] = {
        "seconds": seconds, "seed": seed, "injected": 0,
        "verdict": "pass", "error": None,
        "pageErrors": page_errors,
    }
    page = context.new_page()
    page.on("console", lambda m: console_errors.append(m.text)
            if getattr(m, "type", "") == "error" else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    ctx = dict(base_ctx)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(settle_ms)
        for step in setup:
            err = run_case_step(page, step, ctx)
            if err:
                res["verdict"] = "fail"
                res["error"] = "soak setup failed: %s" % err
                return res
        box = find_stage_box(page)
        vw, vh = ctx["viewport"]
        end = time.time() + seconds
        injected = 0
        tick_missing = False
        while time.time() < end:
            if page_errors:
                break
            roll = rng.random()
            if intents and roll < 0.7:
                it = rng.choice(intents)
                pool = opts_pool.get(it) or [{}]
                opts = rng.choice(pool)
                args_js = json.dumps(it) + "," + json.dumps(opts)
                page.evaluate(_js_harness_call(ctx["harness"],
                                               "injectFakeInput", args_js))
            elif roll < 0.9:
                x, y = clamp_point(box, rng.random(), rng.random(), (vw, vh))
                if rng.random() < 0.5:
                    page.mouse.move(x, y)
                else:
                    page.mouse.click(x, y)
            else:
                if rng.random() < 0.5:
                    page.keyboard.press(rng.choice(
                        ["ArrowRight", "ArrowLeft", "Space", "Escape"]))
                else:
                    page.mouse.wheel(0, rng.choice([-300, 300]))
            injected += 1
            if fast and not tick_missing and injected % 10 == 0:
                r = page.evaluate(_js_harness_call(ctx["harness"], "tick",
                                                   "0.5"))
                if not r.get("ok"):
                    tick_missing = True
            page.wait_for_timeout(40)
        res["injected"] = injected
        page.wait_for_timeout(CASE_ERROR_DRAIN_MS)
        shot = os.path.join(out_dir, "soak_final.png")
        try:
            page.screenshot(path=shot)
            res["finalFrame"] = shot
            if frame_is_blank(shot) is True:
                res["verdict"] = "fail"
                res["error"] = "final soak frame is blank"
        except Exception:
            pass
        if page_errors:
            res["verdict"] = "fail"
            res["error"] = res["error"] or ("page error after %d injections"
                                            % injected)
    except Exception as exc:
        res["verdict"] = "fail"
        res["error"] = "soak run threw: %s" % exc
    finally:
        try:
            page.close()
        except Exception:
            pass
    return res


def _preflight_harness(context: Any, url: str, doc: Dict[str, Any],
                       settle_ms: int) -> Dict[str, Any]:
    """Contract check BEFORE the cases run: the harness global exists,
    injectFakeInput is callable, and (when the harness publishes an
    `intents` list) every intent in the file is covered. A missing intent is
    a FAIL against the runtime composer, not a skip."""
    harness = doc.get("harness") or "window.__game"
    out: Dict[str, Any] = {"harness": harness, "ok": True, "problems": []}
    needs_harness = bool(doc.get("intents")) or _doc_uses_harness_steps(doc)
    if not needs_harness:
        out["skipped"] = "no intents / harness-driven steps in the file"
        return out
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(settle_ms)
        probe = page.evaluate(_js_expr(
            "(function(){var h=null;try{h=" + harness + ";}catch(e){}"
            "if(!h){return {present:false};}"
            "return {present:true,"
            "hasInject:typeof h.injectFakeInput==='function',"
            "hasTick:typeof h.tick==='function',"
            "intents:(Array.isArray(h.intents)?h.intents:null)};})()"))
        if not probe.get("ok"):
            out["ok"] = False
            out["problems"].append("harness probe threw: %s"
                                   % probe.get("err"))
            return out
        info = probe.get("val") or {}
        if not info.get("present"):
            out["ok"] = False
            out["problems"].append("harness global %s is missing" % harness)
            return out
        if not info.get("hasInject"):
            out["ok"] = False
            out["problems"].append(
                "%s.injectFakeInput is not a function" % harness)
        out["hasTick"] = bool(info.get("hasTick"))
        published = info.get("intents")
        if isinstance(published, list):
            missing = [i for i in (doc.get("intents") or [])
                       if i not in published]
            if missing:
                out["ok"] = False
                out["problems"].append(
                    "harness intents list does not cover: %s"
                    % ", ".join(map(str, missing)))
        else:
            out["intentsListPublished"] = False
    except Exception as exc:
        out["ok"] = False
        out["problems"].append("preflight failed: %s" % exc)
    finally:
        try:
            page.close()
        except Exception:
            pass
    return out


def _doc_uses_harness_steps(doc: Dict[str, Any]) -> bool:
    for case in doc.get("cases") or []:
        for group in ("given", "steps"):
            for step in case.get(group) or []:
                if step.get("type") in ("intent", "tick"):
                    return True
    for steps in (doc.get("phaseSetups") or {}).values():
        for step in steps or []:
            if step.get("type") in ("intent", "tick"):
                return True
    return False


# ---------------------------------------------------------------------------
# Game seam test (docs/agents/game-seam-contract.md). Deterministic, no LLM.
# Runs for every games/<id>/runtime.html target. Catches the seam-break class
# that state-level QA cannot see: a model rendered 180deg from its travel
# direction, an anim clip whose clock nobody advances, a harness that was
# never built. Any assert failing = the gate fails before any lens runs.
# ---------------------------------------------------------------------------

_GAME_TARGET_RE = re.compile(r"/games/[^/]+/runtime\.html")

_SEAM_KEYS_JS = (
    "(function(){var h=window.__game;if(!h){return {present:false};}"
    "var qa=h.qa||{};return {present:true,missing:["
    "(h.state===undefined?'state':null),"
    "(Array.isArray(h.intents)?null:'intents'),"
    "(typeof h.injectFakeInput==='function'?null:'injectFakeInput'),"
    "(typeof h.tick==='function'?null:'tick'),"
    "(typeof h.snapshot==='function'?null:'snapshot'),"
    "(Array.isArray(h.errors)?null:'errors'),"
    "(typeof qa.modelForward==='function'?null:'qa.modelForward'),"
    "(typeof qa.animState==='function'?null:'qa.animState'),"
    "(typeof qa.debug==='function'?null:'qa.debug')"
    "].filter(Boolean)};})()")

_SEAM_SNAP_JS = (
    "(function(){var s=window.__game.snapshot()||{};var a=s.avatar||{};"
    "return {pos:(a.pos||null),forward:(a.forward||null),"
    "speed:(a.speed===undefined?null:a.speed),phase:(s.phase===undefined?null:s.phase)};})()")


def is_game_target(url: str) -> bool:
    try:
        path = urllib.parse.urlparse(url).path
    except Exception:
        path = url
    return bool(_GAME_TARGET_RE.search(path or ""))


def _seam_eval(page: Any, js: str) -> Any:
    res = page.evaluate(_js_expr(js))
    if not res.get("ok"):
        raise RuntimeError("seam eval threw: %s" % res.get("err"))
    return res.get("val")


_SEAM_LIB_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "kinds", "game-seam.js"))


def sync_seam_library(cases_path: str) -> None:
    """Copy the canonical seam library (editor/kinds/game-seam.js) into the
    game dir as seam.js - test-cases.json lives in that dir, so its parent is
    the copy target. Verbatim refresh on every QA run so builds always execute
    the current library; the copy is never hand-edited (header says so).
    Non-fatal: a failed copy leaves the build's own copy in place and the
    seam asserts still judge the runtime."""
    try:
        with open(_SEAM_LIB_PATH, "r") as f:
            lib = f.read()
        dest = os.path.join(os.path.dirname(os.path.abspath(cases_path)),
                            "seam.js")
        try:
            with open(dest, "r") as f:
                if f.read() == lib:
                    return
        except Exception:
            pass
        with open(dest, "w") as f:
            f.write(lib)
        log("seam library synced -> %s" % dest)
    except Exception as exc:
        log("seam library sync skipped (%s)" % exc)


def run_seam_test(context: Any, url: str, settle_ms: int,
                  out_dir: str) -> Dict[str, Any]:
    """Boot the game, start it, drive one forward move, and assert the seam:
    position moves, the RENDERED model faces its travel direction, the active
    anim clip's clock advances, and the error ring stays empty."""
    out: Dict[str, Any] = {"ok": True, "problems": [], "evidence": {}}

    def fail(msg: str) -> None:
        out["ok"] = False
        out["problems"].append(msg)

    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(max(settle_ms, 1500))

        keys = _seam_eval(page, _SEAM_KEYS_JS)
        if not keys.get("present"):
            fail("window.__game harness is missing entirely "
                 "(seam contract: docs/agents/game-seam-contract.md)")
            return out
        missing = keys.get("missing") or []
        if missing:
            fail("harness contract incomplete - missing: %s"
                 % ", ".join(missing))
            return out

        # Start: gate click + explicit start() when exposed.
        try:
            vp = page.viewport_size or {"width": 1280, "height": 720}
            page.mouse.click(vp["width"] // 2, vp["height"] // 2)
        except Exception:
            pass
        _seam_eval(page, "(typeof window.__game.start==='function'"
                         "?(window.__game.start(),1):1)")
        page.wait_for_timeout(800)

        # Games with NO steerable avatar (pure drag-physics / puzzle pieces)
        # declare it by omitting snapshot().avatar - the facing/anim asserts
        # do not apply to them. Harness keys + error ring are still enforced.
        has_avatar = _seam_eval(
            page, "(function(){var s=window.__game.snapshot()||{};"
                  "return !!s.avatar;})()")
        if not has_avatar:
            out["evidence"]["skipped"] = ("no steerable avatar declared "
                                          "(snapshot().avatar absent)")
            errs = _seam_eval(page, "window.__game.errors.slice(0,10)")
            if errs:
                fail("harness error ring is not empty: %r" % (errs[:3],))
            return out

        s0 = _seam_eval(page, _SEAM_SNAP_JS)
        if not (isinstance(s0.get("pos"), list) and len(s0["pos"]) >= 3):
            fail("snapshot().avatar.pos missing or not [x,y,z] - got %r"
                 % (s0.get("pos"),))
            return out
        fwd = s0.get("forward")
        if not (isinstance(fwd, list) and len(fwd) >= 2):
            fail("snapshot().avatar.forward missing or not [x,z] - got %r; "
                 "pose crosses the seam as a VECTOR per the seam contract"
                 % (fwd,))
            return out

        # Drive forward for one simulated second.
        fx, fz = float(fwd[0]) or 0.0, float(fwd[1])
        if abs(fx) < 1e-6 and abs(fz) < 1e-6:
            fz = 1.0
        _seam_eval(page, "window.__game.injectFakeInput('move',{x:%r,z:%r})"
                   % (fx, fz))
        _seam_eval(page, "window.__game.tick(1.0)")
        page.wait_for_timeout(150)

        s1 = _seam_eval(page, _SEAM_SNAP_JS)
        dx = float(s1["pos"][0]) - float(s0["pos"][0])
        dz = float(s1["pos"][2]) - float(s0["pos"][2])
        dist = (dx * dx + dz * dz) ** 0.5
        out["evidence"]["moveDelta"] = [round(dx, 3), round(dz, 3)]
        if dist < 0.05:
            fail("avatar did not move on injectFakeInput('move') + tick(1) "
                 "(moved %.3f units)" % dist)
            return out

        mf = _seam_eval(page, "window.__game.qa.modelForward()")
        if not (isinstance(mf, list) and len(mf) >= 3):
            fail("qa.modelForward() did not return [x,y,z] - got %r" % (mf,))
            return out
        mfx, mfz = float(mf[0]), float(mf[2])
        mlen = (mfx * mfx + mfz * mfz) ** 0.5 or 1.0
        dot = (mfx * dx + mfz * dz) / (mlen * dist)
        out["evidence"]["facingDot"] = round(dot, 3)
        if dot < 0.5:
            fail("FACING SEAM BROKEN: rendered model forward vs travel "
                 "direction dot=%.2f (model faces %s its motion; the classic "
                 "180deg convention flip)" %
                 (dot, "against" if dot < -0.5 else "off"))

        anim = _seam_eval(page, "window.__game.qa.animState()")
        out["evidence"]["animState"] = anim
        # Still moving this tick: the active clip's clock must advance.
        _seam_eval(page, "window.__game.injectFakeInput('move',{x:%r,z:%r})"
                   % (fx, fz))
        _seam_eval(page, "window.__game.tick(0.25)")
        anim2 = _seam_eval(page, "window.__game.qa.animState()")
        if not (isinstance(anim2, dict) and anim2.get("clockAdvancing")):
            fail("ANIM SEAM BROKEN: qa.animState().clockAdvancing is not true "
                 "while moving (state %r) - a walk state with a frozen clip "
                 "clock renders as gliding" % (anim2,))

        _seam_eval(page, "window.__game.injectFakeInput('move',{x:0,z:0})")
        errs = _seam_eval(page, "window.__game.errors.slice(0,10)")
        if errs:
            fail("harness error ring is not empty: %r" % (errs[:3],))

        try:
            page.screenshot(path=os.path.join(out_dir, "seam_after_move.png"))
        except Exception:
            pass
    except Exception as exc:
        fail("seam test could not complete: %s" % exc)
    finally:
        try:
            page.close()
        except Exception:
            pass
    return out


def run_cases(args: argparse.Namespace) -> int:
    """--cases entry point. Runs every case on a fresh page, then the soak.
    Exit codes: 0 pass, 6 any case/preflight/soak failure, 3 setup failure."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        log("ERROR: Playwright is not importable (%s)." % exc)
        return 3
    try:
        with open(args.cases, "r") as f:
            doc = json.load(f)
    except Exception as exc:
        log("ERROR: could not read cases file %s (%s)" % (args.cases, exc))
        return 3
    if not isinstance(doc, dict):
        log("ERROR: cases file must be a JSON object")
        return 3

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    vw, vh = args.viewport
    url = normalise_url(args.url)
    settle_ms = int(args.settle_ms)
    harness = doc.get("harness") or "window.__game"
    base_ctx: Dict[str, Any] = {"harness": harness, "viewport": (vw, vh)}

    cases: List[Dict[str, Any]] = list(doc.get("cases") or [])
    cases += _expand_matrix_cases(doc)
    cases += _expand_abuse_cases(doc, (vw, vh))
    # A scoped run asks only for the cases the change touches.
    scoped_ids = (getattr(args, "scope_doc", None) or {}).get("cases")
    if isinstance(scoped_ids, list):
        want = {str(i) for i in scoped_ids}
        cases = [c for c in cases if str(c.get("id")) in want]
        log("scope: %d of the planned case(s)" % len(cases))

    report: Dict[str, Any] = {
        "url": url,
        "browser": None,
        "viewport": "%dx%d" % (vw, vh),
        "mode": "cases",
        "family": doc.get("family"),
        "pieceId": doc.get("pieceId"),
        "harness": harness,
        "casesFile": os.path.abspath(args.cases),
        "preflight": None,
        "cases": [],
        "soak": None,
        "casesSummary": {},
        "verdict": None,
        "reasons": [],
    }

    with sync_playwright() as pw:
        try:
            browser, browser_label = launch_browser(pw)
        except Exception as exc:
            log("ERROR: could not launch any browser (%s)." % exc)
            return 3
        report["browser"] = browser_label
        log("browser: %s" % browser_label)
        context = browser.new_context(viewport={"width": vw, "height": vh})
        try:
            context.grant_permissions(["camera", "microphone"])
        except Exception:
            pass
        _cam = camera_mock_script(getattr(args, "camera", "both") or "both")
        if _cam:
            try:
                context.add_init_script(_cam)
            except Exception:
                pass

        report["preflight"] = _preflight_harness(context, url, doc, settle_ms)
        if not report["preflight"].get("ok", True):
            log("preflight FAILED: %s"
                % "; ".join(report["preflight"].get("problems") or []))

        if is_game_target(url):
            sync_seam_library(args.cases)
            report["seam"] = run_seam_test(context, url, settle_ms, out_dir)
            log("seam test: %s"
                % ("pass" if report["seam"]["ok"]
                   else "; ".join(report["seam"]["problems"])))

        # Typed visual checks: every distinct screen a case ends on is
        # captured once, then judged with the settled page below.
        if getattr(args, "typed_judge", None):
            prepare_typed(args)
            if _full_pass(args):
                args.screen_collector = ScreenCollector(out_dir, args.ds_plan, what=_full_pass(args) or "page",
                                                        changed=(getattr(args, "scope_doc", None) or {}).get("changed"))
        collector = getattr(args, "screen_collector", None)
        for i, case in enumerate(cases):
            entry = _run_one_case(context, url, case, base_ctx, settle_ms,
                                  out_dir, collector.capture if collector else None)
            report["cases"].append(entry)
            log("case %d/%d %s: %s" % (i + 1, len(cases),
                                       entry.get("id"), entry["verdict"]))

        report["soak"] = (None if isinstance(scoped_ids, list) else
                          _run_soak(context, url, doc, base_ctx, settle_ms, out_dir))
        if report["soak"]:
            log("soak: %s (%d injections)"
                % (report["soak"]["verdict"], report["soak"]["injected"]))

        # Typed visual checks run here too: cases mode replaces the battery,
        # not the checks about the page. The settled page and the criteria
        # steps join the screens the cases ended on; every screen is asked.
        # Records beside the cases and never touches their verdict or the
        # exit code.
        if getattr(args, "typed_judge", None):
            try:
                report["typedChecks"] = typed_checks_on_page(context, url, args, settle_ms, out_dir)
                _flag_and_log(report, report["typedChecks"], args.typed_judge, args, None)
            except Exception as exc:
                report["typedChecks"] = {"message": "typed checks skipped: %s" % exc}

        context.close()
        browser.close()

    n_pass = sum(1 for c in report["cases"] if c["verdict"] == "pass")
    n_fail = len(report["cases"]) - n_pass
    by_kind: Dict[str, int] = {}
    for c in report["cases"]:
        k = str(c.get("kind") or "case")
        by_kind[k] = by_kind.get(k, 0) + 1
    report["casesSummary"] = {
        "total": len(report["cases"]),
        "pass": n_pass,
        "fail": n_fail,
        "byKind": by_kind,
        "preflightOk": bool(report["preflight"].get("ok", True)),
        "soakVerdict": (report["soak"] or {}).get("verdict"),
    }

    reasons: List[str] = []
    verdict = "pass"
    if not report["preflight"].get("ok", True):
        verdict = "cases-fail"
        reasons.append("harness contract preflight failed: %s"
                       % "; ".join(report["preflight"].get("problems") or []))
    if report.get("seam") and not report["seam"].get("ok", True):
        verdict = "cases-fail"
        reasons.append("seam test failed: %s"
                       % "; ".join(report["seam"].get("problems") or []))
    if n_fail:
        verdict = "cases-fail"
        failed_ids = [str(c.get("id")) for c in report["cases"]
                      if c["verdict"] != "pass"]
        reasons.append("%d/%d case(s) failed: %s"
                       % (n_fail, len(report["cases"]),
                          ", ".join(failed_ids[:12])))
    if report["soak"] and report["soak"]["verdict"] != "pass":
        verdict = "cases-fail"
        reasons.append("soak failed (seed %s): %s"
                       % (report["soak"]["seed"],
                          report["soak"].get("error") or "page errors"))
    if verdict == "pass":
        reasons.append("all %d case(s) passed%s"
                       % (len(report["cases"]),
                          "; soak clean" if report["soak"] else ""))
    report["verdict"] = verdict
    report["reasons"] = reasons

    report_path = os.path.join(out_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log("report written to %s" % report_path)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    sys.stdout.flush()
    return 0 if verdict == "pass" else 6


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

    # HARD STOP: a game runtime may only be gated through its plan-time
    # test-cases.json (cases mode). Reaching the generic battery here means
    # the researcher never wrote the file - that is a build failure, not a
    # fallback. No opt-out. See docs/agents/game-seam-contract.md.
    if is_game_target(url):
        report = {
            "url": url, "mode": args.mode, "verdict": "fail",
            "reasons": [
                "game runtime has no test-cases.json - the generic battery "
                "is not a valid gate for games. game-research-technique "
                "writes test-cases.json next to research.md; re-dispatch it. "
                "(docs/agents/game-seam-contract.md)"],
        }
        report_path = os.path.join(out_dir, "report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        log("HARD STOP: game target without test-cases.json")
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
        sys.stdout.flush()
        return 6

    spec: Dict[str, Any] = {}
    if args.spec:
        try:
            with open(args.spec, "r") as f:
                spec = json.load(f)
        except Exception as exc:
            log("ERROR: could not read spec %s (%s)" % (args.spec, exc))
            return 3

    # Typed visual checks: parsed up front so each capture can record where
    # the checked elements are at that moment (crops come from that moment).
    prepare_typed(args)
    check_selectors = sorted({c["selector"] for c in args.parsed_checks[0] if c.get("selector")})

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
        # Camera/mic pieces are black under headless QA. Grant the permissions and
        # inject a getUserMedia mock that returns a DETECTABLE stock-fixture feed
        # so vision detection actually fires (the agent can verify camera pieces).
        try:
            context.grant_permissions(["camera", "microphone"])
        except Exception:
            pass
        _cam = camera_mock_script(getattr(args, "camera", "both") or "both")
        if _cam:
            try:
                context.add_init_script(_cam)
                report["cameraMock"] = getattr(args, "camera", "both") or "both"
            except Exception:
                pass
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

        # Vision warmup: if the piece actually requested the (mocked) camera,
        # MediaPipe / tesseract load from CDN over several seconds and detection
        # only drives a visible effect once running - wait so the timeline below
        # captures the DETECTING state, not a black pre-load frame.
        if _cam and args.mode != "render":
            cam_used = 0
            for _ in range(20):  # poll up to ~2s for getUserMedia to be called
                try:
                    cam_used = int(page.evaluate("window.__qaCam||0"))
                except Exception:
                    cam_used = 0
                if cam_used:
                    break
                page.wait_for_timeout(100)
            if cam_used:
                log("camera piece (getUserMedia called); warming up vision ~7s")
                report["cameraUsed"] = True
                page.wait_for_timeout(7000)

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
            boxes = capture_boxes(page, check_selectors)
            diff_prev = None
            if prev_path is not None:
                diff_prev = diff_frames(prev_path, fpath)
            idle_frames.append({"t": float(t), "path": fpath,
                                "diffFromPrev": diff_prev})
            if boxes is not None:
                idle_frames[-1]["boxes"] = boxes
            prev_path = fpath
        report["idleFrames"] = idle_frames

        # ----- INTERACTION BATTERY -----
        # render mode is for composed pages where "did it render?" is the
        # question, not "does it move?"; skip the battery there unless the spec
        # explicitly asks for steps. interactive mode keeps the default battery.
        interactions: List[Dict[str, Any]] = []
        render_mode = (args.mode == "render")
        spec_has_steps = bool(spec.get("interactions"))
        do_interact = (not args.no_interact) and (
            spec_has_steps or not render_mode)
        if do_interact:
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
                before_boxes = capture_boxes(page, check_selectors)
                try:
                    run_step(page, step)
                except Exception as exc:
                    log("step %s failed (%s)" % (label, exc))
                page.wait_for_timeout(interact_settle_ms)
                page.screenshot(path=after)
                after_boxes = capture_boxes(page, check_selectors)
                d = diff_frames(before, after)
                interactions.append({
                    "step": label,
                    "type": step.get("type"),
                    "beforePath": before,
                    "afterPath": after,
                    "diff": d,
                })
                if before_boxes is not None:
                    interactions[-1]["beforeBoxes"] = before_boxes
                    interactions[-1]["afterBoxes"] = after_boxes
        report["interactions"] = interactions

        # The typed checks' own captures, on a fresh page AFTER everything
        # the verdict reads: the settled screen full-page, the criteria steps,
        # the design-system gallery crops.
        if getattr(args, "typed_judge", None):
            report["typedPass"] = typed_pass_for(context, url, args, settle_ms, out_dir,
                                                 args.parsed_checks[0])

        context.close()
        browser.close()

    # ----- METRICS + VERDICT -----
    idle_diffs = [f["diffFromPrev"] for f in report["idleFrames"]
                  if f["diffFromPrev"] is not None]
    ix_diffs = [ix["diff"] for ix in report["interactions"]]
    max_idle = max(idle_diffs) if idle_diffs else 0.0
    max_ix = max(ix_diffs) if ix_diffs else 0.0

    # Render mode: is the first painted frame blank (nothing rendered / flat
    # unstyled wash)? None = could not tell (no Pillow); treated as not-blank.
    first_blank = None
    if render_mode and report["idleFrames"]:
        first_blank = frame_is_blank(report["idleFrames"][0]["path"])

    report["metrics"] = {
        "mode": args.mode,
        "maxIdleDiff": max_idle,
        "maxInteractionDiff": max_ix,
        "firstFrameBlank": first_blank,
        "pixelDeltaThreshold": PIXEL_DELTA_THRESHOLD,
        "diffEpsilon": DIFF_EPSILON,
    }

    reasons: List[str] = []
    verdict = "pass"

    severe_error = bool(page_errors) or bool(console_errors)
    interacted = do_interact and bool(report["interactions"])

    animates = max_idle > DIFF_EPSILON
    reacts = max_ix > DIFF_EPSILON

    if render_mode:
        # Composed page: "did it render?" not "does it move?". A correctly
        # painted static page is a PASS; a blank/unstyled flat wash fails.
        if severe_error:
            verdict = "error"
            if page_errors:
                reasons.append("uncaught page error(s): %d" % len(page_errors))
            if console_errors:
                reasons.append("console error(s): %d" % len(console_errors))
        elif first_blank is True:
            verdict = "blank"
            reasons.append("page rendered a blank / flat-uniform frame - "
                           "likely broken CSS/JS imports (e.g. missing "
                           "?project stamping) or a script bailout; it loaded "
                           "but did not paint real content")
        else:
            reasons.append("rendered without errors")
            if first_blank is None:
                reasons.append("blank-check unavailable (no Pillow); rendered "
                               "+ error-free is the verdict basis")
            if animates:
                reasons.append("also animates (maxIdleDiff=%.4f)" % max_idle)
            if interacted and reacts:
                reasons.append("also reacts to input "
                               "(maxInteractionDiff=%.4f)" % max_ix)
    elif severe_error:
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

    # ----- OPTIONAL FRAME JUDGES (LLM, plus the typed judge alongside) -----
    # Precedence lives in apply_frame_judges: the LLM judge only escalates or
    # confirms, and the typed judge never changes the verdict.
    report["renderVerdict"] = verdict
    verdict = apply_frame_judges(report, verdict, reasons, out_dir, args)

    report["verdict"] = verdict
    report["reasons"] = reasons

    # ----- OUTPUT -----
    report_path = os.path.join(out_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log("report written to %s" % report_path)

    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    sys.stdout.flush()
    return exit_code(verdict)


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
    p.add_argument("--cases", default=None, metavar="TEST_CASES_JSON",
                   help="Run the piece's plan-time test-cases.json instead of "
                        "the idle timeline + battery: every case end to end "
                        "on a fresh page (journeys, auto intent x phase "
                        "matrix, abuse templates, seeded soak). Exit 6 on any "
                        "case failure. See docs/features/qa-test-cases.md.")
    p.add_argument("--out", default=None,
                   help="Output directory for frames + report.json "
                        "(default: ./qa-out next to this script's cwd).")
    p.add_argument("--viewport", type=parse_viewport, default=(1280, 720),
                   help="Viewport WIDTHxHEIGHT (default 1280x720).")
    p.add_argument("--settle-ms", type=int, default=300,
                   help="Settle delay after load before t=0 (default 300).")
    p.add_argument("--no-interact", action="store_true",
                   help="Skip the interaction battery (idle timeline only).")
    p.add_argument("--camera", default="both", choices=["both", "hand", "face", "off"],
                   help="Synthetic camera fixture fed to getUserMedia for vision "
                        "pieces (default both = hand+face; off = real/none).")
    p.add_argument("--mode", default="interactive",
                   choices=["interactive", "render"],
                   help="interactive (default): verify the piece ANIMATES / "
                        "REACTS - a static, motionless result fails as 'static'. "
                        "render: verify a composed page/app RENDERED correctly - "
                        "a correctly-painted static page PASSES; a blank / "
                        "unstyled flat wash fails as 'blank'. render mode skips "
                        "the interaction battery unless --spec supplies steps. "
                        "Pair either mode with --judge to also check the RIGHT "
                        "thing rendered.")
    p.add_argument("--judge", default=None, metavar="EXPECTED",
                   help="Optional LLM frame-judge. Pass a plain-English "
                        "description of the intended effect; the harness "
                        "montages a labeled frame strip and asks a vision LLM "
                        "whether the captured behaviour matches. Fail-soft: if "
                        "no LLM is reachable, judge.available=false and "
                        "an otherwise passing verdict becomes inconclusive.")
    p.add_argument("--judge-daemon", default=None, metavar="BASE_URL",
                   help="Base URL of an ALREADY-RUNNING Woven daemon (e.g. "
                        "http://localhost:5747) to route the judge through its "
                        "/__llm_run describe endpoint. Requires --judge-project. "
                        "This tool never starts the daemon.")
    p.add_argument("--judge-project", default=None, metavar="PROJECT",
                   help="Project id stamped onto the daemon /__llm_run call "
                        "(required by --judge-daemon).")
    p.add_argument("--judge-provider", default="anthropic",
                   choices=["anthropic", "openai"],
                   help="Provider for the daemon /__llm_run describe call "
                        "(default anthropic). Ignored by the direct-API "
                        "fallback, which is always Anthropic.")
    p.add_argument("--checks", default=None, metavar="CHECKS_JSON",
                   help="Typed visual checks: a JSON file of literal statements, "
                        "each tied to a capture (page, idle:start, after:<step>, ...) "
                        "and optionally cropped to a selector. See run_visual_checks. "
                        "Needs --typed-judge.")
    p.add_argument("--ds-visual", default=None, metavar="PLAN_JSON",
                   help="The design system's visual plan for this page (ds_lint.visual_plan "
                        "plus the gallery URL): off-system elements to crop and ask "
                        "ds-copy / new-ui / layout, components to compare with the gallery. "
                        "Needs --typed-judge.")
    p.add_argument("--typed-steps", default=None, metavar="STEPS_JSON",
                   help="Criteria steps for the page (click / fill / select / check / hover / "
                        "key on a selector), run on a fresh page after the main QA so "
                        "criteria can be about after:<step>.")
    p.add_argument("--typed-judge", default=None, choices=["shadow", "flag"],
                   help="Ask the image-tier typed judge (editor/typed_judge.py) each "
                        "--checks statement. shadow records the answers and changes "
                        "nothing; flag also adds a typed-judge finding per confident "
                        "failure. Never changes the verdict or the exit code. The "
                        "daemon passes this when typed judgment for visual checks is on.")
    p.add_argument("--typed-elements", nargs="?", const="page", default=None, choices=["page", "ds"],
                   help="With --typed-judge: an element pass over every screen the QA "
                        "reaches (the settled page, its test cases' end states, an "
                        "exploration of its clicks). page: the region drill (which part "
                        "of the screen has a visual defect, then which part of that, down "
                        "to a primitive or a DS component). ds: every distinct design-"
                        "system component beside the DS gallery's own, chained. Without "
                        "it only the --checks run.")
    p.add_argument("--scope", default=None, metavar="SCOPE_JSON",
                   help="What the change touches, from the caller's scoping: {states: "
                        "[{label, query?, steps?}], changed: [selectors from the change's "
                        "code], cases: [test case ids]}. The element pass captures the page "
                        "and those states only (no exploration), reads each screen from "
                        "where the changed elements impact it, and the cases mode runs only "
                        "the listed cases (no soak).")
    p.add_argument("--judge-model", default=None, metavar="MODEL",
                   help="Vision model id (default %s for the direct API; the "
                        "daemon picks its own default if omitted)."
                        % JUDGE_DEFAULT_MODEL)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.scope_doc = None
    if args.scope:
        try:
            with open(args.scope, "r") as f:
                args.scope_doc = json.load(f)
        except Exception as exc:
            log("could not read scope %s (%s)" % (args.scope, exc))
    if args.out is None:
        args.out = os.path.join(os.getcwd(), "qa-out")
    if args.cases:
        return run_cases(args)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
