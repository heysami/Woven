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
                  out_dir: str) -> Dict[str, Any]:
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

        for i, case in enumerate(cases):
            entry = _run_one_case(context, url, case, base_ctx, settle_ms,
                                  out_dir)
            report["cases"].append(entry)
            log("case %d/%d %s: %s" % (i + 1, len(cases),
                                       entry.get("id"), entry["verdict"]))

        report["soak"] = _run_soak(context, url, doc, base_ctx, settle_ms,
                                   out_dir)
        if report["soak"]:
            log("soak: %s (%d injections)"
                % (report["soak"]["verdict"], report["soak"]["injected"]))

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
            diff_prev = None
            if prev_path is not None:
                diff_prev = diff_frames(prev_path, fpath)
            idle_frames.append({"t": float(t), "path": fpath,
                                "diffFromPrev": diff_prev})
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

    # ----- OPTIONAL LLM FRAME-JUDGE -----
    # Precedence: the judge only ESCALATES or CONFIRMS; it never relaxes an
    # error/static/no-reaction pixel verdict.
    #   - judge unavailable        -> verdict unchanged (pixel-diff stands).
    #   - judge ok:false           -> verdict becomes "effect-wrong" (the wrong
    #                                 thing renders even if pixels moved), but
    #                                 only when the pixel verdict was "pass"
    #                                 (an existing error/static/no-reaction is a
    #                                 stronger signal and is kept).
    #   - judge ok:true            -> CONFIRMS; verdict unchanged (still pass).
    #   - judge inconclusive       -> verdict unchanged.
    if args.judge:
        judge = run_judge(report, out_dir, args)
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
                reasons.append("frame-judge inconclusive: %s"
                               % (judge.get("message") or "no parseable verdict"))
        else:
            reasons.append("frame-judge unavailable: %s"
                           % (judge.get("message") or "unknown reason"))
        log(judge.get("message") or "frame-judge completed")

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
    if verdict == "effect-wrong":
        return 4  # pixels moved but the wrong thing renders (frame-judge)
    if verdict == "blank":
        return 5  # render mode: loaded but painted nothing / unstyled wash
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
                        "no LLM is reachable, judge.available=false and the "
                        "pixel-diff verdict is unchanged.")
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
    p.add_argument("--judge-model", default=None, metavar="MODEL",
                   help="Vision model id (default %s for the direct API; the "
                        "daemon picks its own default if omitted)."
                        % JUDGE_DEFAULT_MODEL)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.out is None:
        args.out = os.path.join(os.getcwd(), "qa-out")
    if args.cases:
        return run_cases(args)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
