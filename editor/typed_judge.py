#!/usr/bin/env python3
"""typed_judge.py - provider-aware typed judgment (System One shape everywhere).

A typed judge does not generate text. It answers TYPED questions (noul, choice,
score) about one state and returns calibrated probabilities. Several services
now speak that shape, at different levels of support:

  jev         TypeSafe Jev - text only, cheapest, the original
  clef        Cloudflare Clef via Workers AI REST - reads up to 4 images
  clef-flash  Cloudflare Clef Flash - cheaper, reads up to 4 images
  clef-local  Clef on this computer through Ollama - no key, nothing leaves
  openai      OpenAI Decisions - a different wire format, translated both ways

What each one can do lives in editor/judges.json, never in code, so the day
TypeSafe ships image input the whole change is one number in that file
(`maxImages` on the jev row) and a Test click that verifies it.

ONE CONTRACT. `judge()` always returns answers in System One shape whatever
answered, so every reader below (and every consumer of editor/jev.py) works
unchanged. Plan: docs/features/typed-judgment-providers.md.

POSTURE - flag, never block (docs/features/jev-integration.md). Every failure
is a JudgeError the caller catches and carries on from; JudgeUnavailable is
"not set up", which callers report as "kept today's path", never as an error.

Routing. A consumer asks for a TIER, not a provider:
  text   - any keyed judge; the user's choice first, else the first keyed one
           in the text autoRank.
  image  - the same, filtered to judges whose maxImages covers the request and
           whose image probe has not failed (imagesVerified != false).

Stdlib only, Python 3.9-safe (the daemon's fresh-install floor). Pillow is used
only to downscale an oversized image, and only when it is importable.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import random
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_HARNESS = os.path.expanduser("~/.test-harness")

# Module-level so tests (and the calibrate tool) can point them elsewhere.
JUDGES_PATH = os.path.join(_HERE, "judges.json")
THRESHOLDS_PATH = os.path.join(_HERE, "tools", "qa", "jev_thresholds.json")
MEDIA_CONFIG_PATH = os.path.join(_HARNESS, "media-config.json")
COMPACT_CONFIG_PATH = os.path.join(_HARNESS, "compact-config.json")
# Every typed answer Woven acts on or shadows (visual checks, sprite and asset
# checks, the DS check), one JSON line each with an `id`. Labels for
# calibration live beside it, keyed by that id, so the log is never rewritten.
SHADOW_LOG_PATH = os.path.join(_HARNESS, "typed-judge-shadow.jsonl")
LABELS_PATH = os.path.join(_HARNESS, "typed-judge-labels.json")
SHADOW_LOG_MAX_BYTES = 5 * 1024 * 1024

TIERS = ("text", "image")
QUESTION_TYPES = ("noul", "choice", "score")
MIN_CHOICE_OPTIONS = 2
MIN_SCORE_LEVELS = 2
VISUAL_MODES = ("shadow", "flag")

# Credentials, by the media-config id a judge row names in `config`. Mirrors
# _PROVIDER_ENV_KEYS in serve.py so CLI tools (ds_lint, visual_qa) resolve the
# same key the daemon would with no daemon running.
ENV_KEYS = {
    "typesafe": "TH_TYPESAFE_API_KEY",
    "cloudflare": "TH_CLOUDFLARE_API_KEY",
    "openai": "TH_OPENAI_API_KEY",
}
ACCOUNT_ENV = {"cloudflare": "TH_CLOUDFLARE_ACCOUNT_ID"}
ENDPOINT_ENV = {"clef_local": "TH_CLEF_LOCAL_ENDPOINT"}

# Images. Over either limit the image is downscaled (Pillow) or refused.
IMAGE_MAX_BYTES = 4 * 1024 * 1024
IMAGE_MAX_PIXELS = 16_000_000
IMAGE_MIME = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
# Context cost of one image for judges whose budget counts images
# (contextIncludesImages). Clef caps each image at 1,024 tokens.
_IMAGE_TOKEN_ESTIMATE = 1024
_CHARS_PER_TOKEN = 3.6


class JudgeError(RuntimeError):
    """Any failure reaching or parsing a judge. ALWAYS catchable: no consumer
    may let this escape into a build. `status` carries the HTTP status when the
    service answered with one. The message never carries a key."""

    def __init__(self, message, status=None):
        # type: (str, Optional[int]) -> None
        super().__init__(message)
        self.status = status


class JudgeUnavailable(JudgeError):
    """Nothing set up for this request. `reason` is one of off / no-key /
    no-image-judge, the same words the /__judge endpoint answers 503 with."""

    def __init__(self, message, reason="no-key"):
        # type: (str, str) -> None
        super().__init__(message)
        self.reason = reason


# ── Settings (compact-config.json), read straight off disk ──────────────────
# Read here rather than through serve so ds_lint and visual_qa honour them with
# no daemon running. serve.py validates with the same coerce_config, so a value
# the daemon refuses to save is a value this never acts on.

CONFIG_DEFAULTS = {
    "jevJudge": False,                 # text checks
    "typedJudgeVisual": False,         # visual checks
    "typedJudgeTextProvider": "auto",
    "typedJudgeImageProvider": "auto",
    "typedJudgeVisualMode": "shadow",
}
_CHOICE_KEY = {"text": "typedJudgeTextProvider", "image": "typedJudgeImageProvider"}
_ENABLED_KEY = {"text": "jevJudge", "image": "typedJudgeVisual"}


def valid_setting(key, value):
    # type: (str, Any) -> bool
    if key in ("jevJudge", "typedJudgeVisual"):
        return isinstance(value, bool)
    if key in ("typedJudgeTextProvider", "typedJudgeImageProvider"):
        return value == "auto" or (isinstance(value, str) and provider(value) is not None)
    if key == "typedJudgeVisualMode":
        return value in VISUAL_MODES
    return False


def coerce_config(saved):
    # type: (Any) -> Dict[str, Any]
    """The typed-judgment keys of a saved compact-config, each one valid or
    replaced by its default."""
    out = dict(CONFIG_DEFAULTS)
    if isinstance(saved, dict):
        for key in CONFIG_DEFAULTS:
            if key in saved and valid_setting(key, saved[key]):
                out[key] = saved[key]
    return out


def _read_json(path):
    # type: (str) -> Any
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def config():
    # type: () -> Dict[str, Any]
    return coerce_config(_read_json(COMPACT_CONFIG_PATH))


# A chat thread's own choice, stamped on the agent's env by the daemon
# (serve.py _apply_guard_env) when the user overrode Settings for that thread.
# Tools the agent runs itself (ds_lint --jev) inherit it, so they agree with
# what the daemon's endpoints apply to the same thread.
_ENABLED_ENV = {"text": "TH_JUDGE_TEXT", "image": "TH_JUDGE_IMAGE"}


def enabled(tier="text"):
    # type: (str) -> bool
    """The user's switch for this tier: the thread's override when the env
    carries one, else the global setting. An intent, not a capability:
    callers gate on enabled(tier) AND pick(tier)."""
    env = os.environ.get(_ENABLED_ENV.get(tier, "TH_JUDGE_TEXT"))
    if env in ("0", "1"):
        return env == "1"
    return bool(config().get(_ENABLED_KEY.get(tier, "jevJudge")))


def visual_mode():
    # type: () -> str
    return config()["typedJudgeVisualMode"]


# ── Providers (editor/judges.json) ──────────────────────────────────────────

def providers():
    # type: () -> List[Dict[str, Any]]
    """Every judge row. Read on every call (it is tiny) so an edit to
    judges.json takes effect without a restart."""
    doc = _read_json(JUDGES_PATH)
    rows = doc.get("providers") if isinstance(doc, dict) else None
    return [r for r in (rows or []) if isinstance(r, dict) and r.get("id")]


def provider(pid):
    # type: (Any) -> Optional[Dict[str, Any]]
    for row in providers():
        if row["id"] == pid:
            return row
    return None


# `judge()` takes a `provider` argument, which shadows the function above.
_row_for = provider


def _media_config():
    # type: () -> Dict[str, Any]
    cfg = _read_json(MEDIA_CONFIG_PATH)
    return cfg if isinstance(cfg, dict) else {}


def _entry(row, media):
    # type: (Dict[str, Any], Dict[str, Any]) -> Dict[str, Any]
    e = media.get(row.get("config") or "")
    return e if isinstance(e, dict) else {}


def default_key(config_id, media=None):
    # type: (str, Optional[Dict[str, Any]]) -> Optional[str]
    """Env var first, then media-config.json - the order serve.py's
    _resolve_provider_key uses. The daemon passes its own resolver instead,
    which keeps guest-key isolation intact."""
    env = ENV_KEYS.get(config_id)
    if env:
        v = os.environ.get(env)
        if v and v.strip():
            return v.strip()
    media = _media_config() if media is None else media
    e = media.get(config_id)
    k = e.get("api_key") if isinstance(e, dict) else None
    return k.strip() if isinstance(k, str) and k.strip() else None


def credentials(row, resolve_key=None, media=None):
    # type: (Dict[str, Any], Optional[Callable[[str], Optional[str]]], Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]
    """{token, url} for one judge, or None when it is not set up. A keyless
    judge (Local Clef) counts as set up once an endpoint is saved."""
    media = _media_config() if media is None else media
    cid = row.get("config") or ""
    entry = media.get(cid) if isinstance(media.get(cid), dict) else {}
    if row.get("keyless"):
        endpoint = str(entry.get("endpoint") or os.environ.get(ENDPOINT_ENV.get(cid, ""), "") or "").strip()
        return {"token": None, "url": endpoint} if endpoint else None
    token = resolve_key(cid) if resolve_key else default_key(cid, media)
    if not token:
        return None
    url = str(row.get("url") or "")
    if "{account_id}" in url:
        acct = str(entry.get("account_id") or os.environ.get(ACCOUNT_ENV.get(cid, ""), "") or "").strip()
        if not acct:
            return None
        url = url.replace("{account_id}", urllib.parse.quote(acct, safe=""))
    return {"token": token, "url": url}


def images_verified(row, media=None):
    # type: (Dict[str, Any], Optional[Dict[str, Any]]) -> Optional[bool]
    """What the last key-row Test found: True (read the red/blue probe), False
    (answered text but failed the probe), None (never checked)."""
    media = _media_config() if media is None else media
    v = _entry(row, media).get("imagesVerified")
    return v if isinstance(v, bool) else None


def reads_images(row, n=1, media=None):
    # type: (Dict[str, Any], int, Optional[Dict[str, Any]]) -> bool
    cap = row.get("maxImages")
    if cap is not None and (not isinstance(cap, int) or cap < max(1, int(n))):
        return False
    return images_verified(row, media) is not False


def _rank(row, tier):
    # type: (Dict[str, Any], str) -> Optional[float]
    r = (row.get("autoRank") or {}).get(tier)
    return float(r) if isinstance(r, (int, float)) and not isinstance(r, bool) else None


def _usable(row, tier, n, resolve_key, media, fits=None):
    # type: (Dict[str, Any], str, int, Any, Dict[str, Any], Any) -> bool
    if credentials(row, resolve_key, media) is None:
        return False
    if fits is not None and not fits(row):
        return False
    return tier == "text" or reads_images(row, n, media)


def auto_pick(tier="text", n_images=None, resolve_key=None, media=None, fits=None):
    # type: (str, Optional[int], Optional[Callable[[str], Optional[str]]], Optional[Dict[str, Any]], Any) -> Optional[str]
    """What "Auto" resolves to: the first usable judge in the tier's autoRank.
    `fits(row)` narrows it to judges whose caps a given request fits."""
    n = n_images if n_images is not None else (1 if tier == "image" else 0)
    media = _media_config() if media is None else media
    ranked = sorted((r for r in providers() if _rank(r, tier) is not None),
                    key=lambda r: _rank(r, tier))
    for row in ranked:
        if _usable(row, tier, n, resolve_key, media, fits):
            return row["id"]
    return None


def pick(tier="text", n_images=None, resolve_key=None, choice=None, media=None, fits=None):
    # type: (str, Optional[int], Optional[Callable[[str], Optional[str]]], Optional[str], Optional[Dict[str, Any]], Any) -> Optional[str]
    """The judge a request for this tier goes to: the user's choice when it is
    set up and capable, else Auto. None when nothing is."""
    if tier not in TIERS:
        raise ValueError("tier must be one of %s" % ", ".join(TIERS))
    n = n_images if n_images is not None else (1 if tier == "image" else 0)
    media = _media_config() if media is None else media
    if choice is None:
        choice = config()[_CHOICE_KEY[tier]]
    if choice and choice != "auto":
        row = provider(choice)
        if row and _usable(row, tier, n, resolve_key, media, fits):
            return row["id"]
    return auto_pick(tier, n, resolve_key, media, fits)


def status(resolve_key=None):
    # type: (Optional[Callable[[str], Optional[str]]]) -> Dict[str, Any]
    """The Settings view: who answers each tier, what Auto would pick, and
    every judge with whether it is set up and whether it reads images."""
    media = _media_config()

    def named(pid):
        row = provider(pid) if pid else None
        return {"id": row["id"], "name": row.get("name") or row["id"]} if row else None

    rows = []
    for row in providers():
        rows.append({
            "id": row["id"],
            "name": row.get("name") or row["id"],
            "config": row.get("config"),
            "keyed": credentials(row, resolve_key, media) is not None,
            "maxImages": row.get("maxImages"),
            "imagesVerified": images_verified(row, media),
            "tiers": ["text"] + (["image"] if reads_images(row, 1, media) else []),
        })
    cfg = config()
    return {
        "text": named(pick("text", resolve_key=resolve_key, media=media)),
        "image": named(pick("image", resolve_key=resolve_key, media=media)),
        "auto": {"text": named(auto_pick("text", resolve_key=resolve_key, media=media)),
                 "image": named(auto_pick("image", resolve_key=resolve_key, media=media))},
        "enabled": {"text": bool(cfg["jevJudge"]), "image": bool(cfg["typedJudgeVisual"])},
        "visualMode": cfg["typedJudgeVisualMode"],
        "providers": rows,
    }


# ── Question shape, checked against the chosen judge's caps ─────────────────

def _cap(row, key):
    # type: (Optional[Dict[str, Any]], str) -> Optional[int]
    v = (row or {}).get(key)
    return int(v) if isinstance(v, int) and not isinstance(v, bool) else None


def validate_questions(questions, row=None):
    # type: (Dict[str, Dict[str, Any]], Optional[Dict[str, Any]]) -> None
    """Enforce the mechanical limits BEFORE spending a request. Raises
    ValueError naming the offending question id. A null cap in judges.json is
    unpublished and not enforced here; the service's own 4xx covers it."""
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a non-empty object keyed by question id")
    max_q = _cap(row, "maxQuestions")
    if max_q is not None and len(questions) > max_q:
        raise ValueError("%d questions in one request, %s takes at most %d - "
                         "split the request" % (len(questions), row["id"], max_q))
    max_opts = _cap(row, "maxChoiceOptions")
    max_levels = _cap(row, "maxScoreLevels")
    id_pattern = (row or {}).get("idPattern")
    for qid, q in questions.items():
        if isinstance(id_pattern, str) and not re.match(id_pattern, str(qid)):
            raise ValueError("question id %r is not accepted by %s (%s)"
                             % (qid, row["id"], id_pattern))
        if not isinstance(q, dict):
            raise ValueError("question %r must be an object" % qid)
        qtype = q.get("type")
        if qtype not in QUESTION_TYPES:
            raise ValueError("question %r: type must be one of %s"
                             % (qid, ", ".join(QUESTION_TYPES)))
        criteria = q.get("criteria")
        if qtype == "choice":
            if not isinstance(criteria, dict) or len(criteria) < MIN_CHOICE_OPTIONS:
                raise ValueError("question %r: choice needs a criteria map of at "
                                 "least %d options {optionId: rubric}"
                                 % (qid, MIN_CHOICE_OPTIONS))
            if max_opts is not None and len(criteria) > max_opts:
                raise ValueError("question %r: choice has %d options, the cap is %d"
                                 % (qid, len(criteria), max_opts))
        elif qtype == "score":
            if not isinstance(criteria, list):
                raise ValueError("question %r: score needs an ORDERED criteria "
                                 "array of levels" % qid)
            hi = max_levels if max_levels is not None else len(criteria)
            if not (MIN_SCORE_LEVELS <= len(criteria) <= hi):
                raise ValueError("question %r: score has %d levels, allowed %d-%s"
                                 % (qid, len(criteria), MIN_SCORE_LEVELS,
                                    max_levels if max_levels is not None else "any"))
        elif criteria is not None and not isinstance(criteria, dict):
            raise ValueError("question %r: noul criteria must be a "
                             "{true, false} object when present" % qid)
        if not str(q.get("instructions") or "").strip():
            raise ValueError("question %r: instructions required (one clause, "
                             "read literally)" % qid)


def _state_text(state):
    # type: (Any) -> str
    if isinstance(state, str):
        return state
    try:
        return json.dumps(state, ensure_ascii=False)
    except Exception:
        return str(state)


def estimate_tokens(state, questions, n_images=0):
    # type: (Any, Any, int) -> int
    """Rough character-based estimate. Rough is fine: it catches the
    order-of-magnitude mistake (a whole page sent as state) before a round
    trip spends money on a 413."""
    chars = len(_state_text(state))
    try:
        chars += len(json.dumps(questions, ensure_ascii=False))
    except Exception:
        chars += sum(len(str(q)) for q in (questions or {}).values())
    return int(chars / _CHARS_PER_TOKEN) + int(n_images) * _IMAGE_TOKEN_ESTIMATE


def check_context(state, questions, row, n_images=0):
    # type: (Any, Any, Optional[Dict[str, Any]], int) -> None
    cap = _cap(row, "contextTokens")
    if cap is None:
        return
    counted = n_images if (row or {}).get("contextIncludesImages") else 0
    est = estimate_tokens(state, questions, counted)
    if est > cap:
        raise ValueError(
            "request is ~%dk tokens, over the %dk context budget - shard it "
            "(one request per page / per checklist chunk) rather than "
            "truncating; see jaggedness rule 6, small state"
            % (est // 1000, cap // 1000))


# ── Images ──────────────────────────────────────────────────────────────────

def sniff_image(data):
    # type: (bytes) -> Optional[str]
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def image_size(data, kind):
    # type: (bytes, str) -> Optional[Tuple[int, int]]
    """(width, height) from the header alone, so the pixel limit is checked
    without Pillow. None when the header is not one this recognises."""
    try:
        if kind == "png" and data[12:16] == b"IHDR":
            return struct.unpack(">II", data[16:24])
        if kind == "jpeg":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
            return None
        if kind == "webp":
            chunk = data[12:16]
            if chunk == b"VP8X":
                w = 1 + int.from_bytes(data[24:27], "little")
                h = 1 + int.from_bytes(data[27:30], "little")
                return w, h
            if chunk == b"VP8L":
                b = data[21:25]
                w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                return w, h
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
    except Exception:
        return None
    return None


def _downscale(data, w, h):
    # type: (bytes, int, int) -> Tuple[bytes, str]
    try:
        from PIL import Image  # type: ignore
    except Exception:
        raise ValueError(
            "image is %s (%dx%d), over the %d MiB / %d MP limit, and Pillow is "
            "not installed to downscale it - send a smaller frame"
            % (_fmt_bytes(len(data)), w, h, IMAGE_MAX_BYTES // (1024 * 1024),
               IMAGE_MAX_PIXELS // 1_000_000))
    img = Image.open(io.BytesIO(data))
    img.load()
    scale = min(1.0, math.sqrt(IMAGE_MAX_PIXELS / float(max(1, w * h))) * 0.98)
    for _ in range(6):
        if scale < 1.0:
            size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            img = img.resize(size, getattr(Image, "LANCZOS", 1))
        out = io.BytesIO()
        img.convert("RGB").save(out, "JPEG", quality=85)
        if out.tell() <= IMAGE_MAX_BYTES:
            return out.getvalue(), "jpeg"
        scale = 0.7
    raise ValueError("image could not be brought under %d MiB"
                     % (IMAGE_MAX_BYTES // (1024 * 1024)))


def _fmt_bytes(n):
    # type: (int) -> str
    return "%.1f MiB" % (n / (1024.0 * 1024.0))


def _inside(path, roots):
    # type: (str, List[str]) -> bool
    real = os.path.realpath(path)
    for root in roots:
        base = os.path.realpath(root)
        try:
            if os.path.commonpath([real, base]) == base:
                return True
        except ValueError:
            continue
    return False


def load_image(item, roots=None):
    # type: (Any, Optional[List[str]]) -> str
    """One image as a data URI. `item` is a path, {"path": ...}, raw bytes, or
    a data URI. With `roots`, a path must resolve inside one of them (the
    daemon passes the project root). PNG, JPEG and WebP only. Over 4 MiB or
    16 MP it is downscaled with Pillow, or refused when Pillow is missing."""
    if isinstance(item, dict):
        item = item.get("path") if item.get("path") is not None else item.get("data_uri")
    if isinstance(item, (bytes, bytearray)):
        data = bytes(item)
    elif isinstance(item, str) and item.startswith("data:"):
        try:
            data = base64.b64decode(item.split(",", 1)[1], validate=False)
        except Exception:
            raise ValueError("image data URI is not valid base64")
    elif isinstance(item, str) and item.strip():
        path = item if os.path.isabs(item) else os.path.join((roots or [os.getcwd()])[0], item)
        if roots is not None and not _inside(path, roots):
            raise ValueError("image path is outside the project: %s" % item)
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            raise ValueError("image not found: %s" % item)
    else:
        raise ValueError("each image is a path, {path}, or a data URI")
    kind = sniff_image(data)
    if kind is None:
        raise ValueError("images must be PNG, JPEG or WebP")
    size = image_size(data, kind)
    w, h = size if size else (0, 0)
    if len(data) > IMAGE_MAX_BYTES or w * h > IMAGE_MAX_PIXELS:
        data, kind = _downscale(data, w, h)
    return "data:%s;base64,%s" % (IMAGE_MIME[kind], base64.b64encode(data).decode("ascii"))


def solid_png(rgb, size=64):
    # type: (Tuple[int, int, int], int) -> bytes
    """A solid-colour PNG, stdlib only. The key-row image probe sends a red one
    and a blue one; a judge that reads images tells them apart."""
    import zlib
    row = b"\x00" + bytes(rgb) * size
    raw = row * size

    def chunk(tag, body):
        # type: (bytes, bytes) -> bytes
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


# ── Transport ───────────────────────────────────────────────────────────────

def _sleep_backoff(attempt, retry_after):
    # type: (int, Optional[str]) -> None
    delay = None
    if retry_after:
        try:
            delay = float(retry_after)
        except (TypeError, ValueError):
            delay = None
    if delay is None:
        delay = (2.0 ** attempt) + random.random()
    time.sleep(min(delay, 30.0))


def _post_json(label, url, body, headers, timeout, max_retries):
    # type: (str, str, Dict[str, Any], Dict[str, str], float, int) -> Any
    """POST with retries on 429 and 529 (honouring retry-after) and on network
    errors. Any other 4xx is a caller error and fails at once: retrying a
    malformed request only spends the budget slower."""
    data = json.dumps(body).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers)
    last = None  # type: Optional[str]
    for attempt in range(max(1, int(max_retries)) + 1):
        req = urllib.request.Request(url, method="POST", data=data, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                detail = ""
            last = "http %s %s" % (exc.code, detail)
            if exc.code not in (429, 529) or attempt >= max_retries:
                raise JudgeError("%s request failed: %s" % (label, last), status=exc.code)
            _sleep_backoff(attempt, exc.headers.get("retry-after") if exc.headers else None)
        except Exception as exc:
            last = "%s: %s" % (type(exc).__name__, exc)
            if attempt >= max_retries:
                raise JudgeError("%s request failed: %s" % (label, last))
            _sleep_backoff(attempt, None)
    raise JudgeError("%s request failed: %s" % (label, last or "unknown"))  # pragma: no cover


def _encode_images(uris, encoding):
    # type: (List[str], str) -> List[str]
    if encoding == "base64":
        return [u.split(",", 1)[1] for u in uris]
    return list(uris)


def _send_systemone(row, creds, state, questions, uris, model, timeout, max_retries):
    # type: (Dict[str, Any], Dict[str, Any], Any, Dict[str, Any], List[str], str, float, int) -> Dict[str, Any]
    body = {"state": state, "model": model, "questions": questions}  # type: Dict[str, Any]
    if uris:
        body["images"] = _encode_images(uris, row.get("imageEncoding") or "data-uri")
    headers = {"Authorization": "Bearer " + creds["token"]} if creds.get("token") else {}
    payload = _post_json(row["id"], creds["url"], body, headers, timeout, max_retries)
    wrap = row.get("unwrap")
    if wrap and isinstance(payload, dict) and isinstance(payload.get(wrap), dict):
        payload = payload[wrap]
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict):
        raise JudgeError("%s response has no answers object (got keys: %s)"
                         % (row["id"], (", ".join(sorted(payload))[:120]
                                        if isinstance(payload, dict) else type(payload).__name__)))
    return answers


# ── OpenAI Decisions: translated both ways ──────────────────────────────────
# Questions are a map in System One and an array with `name` in OpenAI; noul is
# a `predicate`, choice options are `choices[{value, description}]`, score
# levels are `levels[{label, description}]`, and images are `input_image` data
# URLs inside the one user message. Replies come back as an array and are
# rebuilt into the System One answer shapes every reader expects.

def _score_levels(criteria):
    # type: (List[Any]) -> List[Tuple[str, str]]
    """A score's ordered criteria as [(label, description)]. Accepts the
    shapes callers write: "label: description", {label, description}, or a
    one-key {label: description}."""
    out = []  # type: List[Tuple[str, str]]
    for i, level in enumerate(criteria or []):
        if isinstance(level, dict):
            if "label" in level:
                lab = str(level.get("label"))
                out.append((lab, str(level.get("description") or lab)))
            elif len(level) == 1:
                k, v = next(iter(level.items()))
                out.append((str(k), str(v)))
            else:
                out.append(("level_%d" % (i + 1), json.dumps(level, ensure_ascii=False)))
        else:
            text = str(level)
            lab, sep, desc = text.partition(":")
            out.append((lab.strip(), desc.strip()) if sep and lab.strip() and len(lab) <= 40
                       else (text.strip(), text.strip()))
    return out


def to_openai(state, questions, uris, model):
    # type: (Any, Dict[str, Dict[str, Any]], List[str], str) -> Dict[str, Any]
    content = [{"type": "input_text", "text": _state_text(state)}]  # type: List[Dict[str, Any]]
    for u in uris:
        content.append({"type": "input_image", "image_url": u})
    qs = []  # type: List[Dict[str, Any]]
    for qid, q in questions.items():
        instructions = str(q.get("instructions") or "").strip()
        qtype = q.get("type")
        if qtype == "noul":
            crit = q.get("criteria") if isinstance(q.get("criteria"), dict) else {}
            extra = []
            if crit.get("true"):
                extra.append("Counts as true when: %s" % crit["true"])
            if crit.get("false"):
                extra.append("Counts as false when: %s" % crit["false"])
            qs.append({"name": qid, "type": "predicate",
                       "instructions": " ".join([instructions] + extra)})
        elif qtype == "choice":
            qs.append({"name": qid, "type": "choice", "instructions": instructions,
                       "choices": [{"value": str(k), "description": str(v)}
                                   for k, v in (q.get("criteria") or {}).items()]})
        else:
            qs.append({"name": qid, "type": "score", "instructions": instructions,
                       "levels": [{"label": lab, "description": desc}
                                  for lab, desc in _score_levels(q.get("criteria"))]})
    return {"model": model, "input": [{"role": "user", "content": content}],
            "questions": qs}


def _num(v):
    # type: (Any) -> Optional[float]
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _prob_map(raw, key_names):
    # type: (Any, Tuple[str, ...]) -> Dict[str, float]
    """A probability distribution as {option: p}, from a map or from an array
    of {value|label|..., probability} rows."""
    out = {}  # type: Dict[str, float]
    if isinstance(raw, dict):
        for k, v in raw.items():
            p = _num(v)
            if p is not None:
                out[str(k)] = p
    elif isinstance(raw, list):
        for rowv in raw:
            if not isinstance(rowv, dict):
                continue
            name = next((rowv[k] for k in key_names if rowv.get(k) is not None), None)
            p = _num(rowv.get("probability", rowv.get("p")))
            if name is not None and p is not None:
                out[str(name)] = p
    return out


def from_openai(payload, questions):
    # type: (Any, Dict[str, Dict[str, Any]]) -> Dict[str, Any]
    rows = None
    if isinstance(payload, dict):
        for k in ("answers", "decisions", "results", "output"):
            if isinstance(payload.get(k), list):
                rows = payload[k]
                break
    if rows is None:
        raise JudgeError("openai response has no answers array (got keys: %s)"
                         % (", ".join(sorted(payload))[:120] if isinstance(payload, dict)
                            else type(payload).__name__))
    answers = {}  # type: Dict[str, Any]
    for item in rows:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("id")
        q = questions.get(name) if isinstance(name, str) else None
        if q is None:
            continue
        # A refusal is DROPPED, so the readers see a missing answer and the
        # consumer escalates that item, exactly as for any other unknown.
        if item.get("refusal") or item.get("type") == "refusal" or item.get("status") == "refused":
            continue
        conf = _num(item.get("confidence"))
        qtype = q.get("type")
        if qtype == "noul":
            p = _num(item.get("probability", item.get("noul")))
            if p is None:
                continue
            a = {"type": "noul", "noul": p}  # type: Dict[str, Any]
            if conf is not None:
                a["confidence"] = conf
        elif qtype == "choice":
            probs = _prob_map(item.get("probabilities"), ("value", "choice", "label", "name"))
            winner = item.get("choice") or item.get("value")
            if not probs and isinstance(winner, str):
                probs = {winner: conf if conf is not None else 1.0}
            if not probs:
                continue
            if not isinstance(winner, str):
                winner = max(probs.items(), key=lambda kv: kv[1])[0]
            a = {"type": "choice", "choice": winner, "probabilities": probs,
                 "confidence": conf if conf is not None else max(probs.values())}
        else:
            # System One indexes score levels from 0, lowest first: legend and
            # probabilities are keyed "0", "1", ... OpenAI sends each level's
            # int `value` (and its label); a label alone is mapped back through
            # the request's own level list, which is where the legend comes from.
            labels = [lab for lab, _d in _score_levels(q.get("criteria"))]
            legend = {str(i): lab for i, lab in enumerate(labels)}
            probs = {}  # type: Dict[str, float]
            for lv in item.get("probabilities") if isinstance(item.get("probabilities"), list) else []:
                if not isinstance(lv, dict) or _num(lv.get("probability")) is None:
                    continue
                idx = lv.get("value")
                if not (isinstance(idx, int) and not isinstance(idx, bool)) and lv.get("label") in labels:
                    idx = labels.index(lv["label"])
                if isinstance(idx, int) and not isinstance(idx, bool):
                    probs[str(idx)] = float(lv["probability"])
            if isinstance(item.get("probabilities"), dict):
                probs = {str(k): v for k, v in _prob_map(item["probabilities"], ()).items()}
            score = _num(item.get("score"))
            if score is None and not probs:
                continue
            # The weighted `score` is passed through, never derived: neither
            # service publishes its scale, and an invented one would read as real.
            a = {"type": "score", "legend": legend, "probabilities": probs}
            if score is not None:
                a["score"] = score
            c = conf if conf is not None else (max(probs.values()) if probs else None)
            if c is not None:
                a["confidence"] = c
        answers[name] = a
    return answers


def _send_openai(row, creds, state, questions, uris, model, timeout, max_retries):
    # type: (Dict[str, Any], Dict[str, Any], Any, Dict[str, Any], List[str], str, float, int) -> Dict[str, Any]
    body = to_openai(state, questions, uris, model)
    payload = _post_json(row["id"], creds["url"], body,
                         {"Authorization": "Bearer " + creds["token"]}, timeout, max_retries)
    return from_openai(payload, questions)


_WIRES = {"systemone": _send_systemone, "openai-decisions": _send_openai}


# ── The one call ────────────────────────────────────────────────────────────

def judge(state, questions, tier="text", images=None, kind="default", provider=None,
          resolve_key=None, model=None, timeout=45, max_retries=3, image_roots=None,
          url=None, api_key=None):
    # type: (...) -> Dict[str, Any]
    """Ask the judge for `tier` and return
    {answers, provider, model, tier, thresholds} with `answers` in System One
    shape whatever answered.

    `provider` pins one judge (the key-row Test, a caller that names it); it
    must then be set up and capable or this raises JudgeUnavailable. `api_key`
    and `url` override that pinned judge's credentials. Raises ValueError for
    a request shape or limit the judge would refuse, JudgeUnavailable when
    nothing is set up, and JudgeError for everything else."""
    if tier not in TIERS:
        raise ValueError("tier must be one of %s" % ", ".join(TIERS))
    images = list(images or [])
    if tier == "text" and images:
        raise ValueError("images need tier=image")
    if tier == "image" and not images:
        raise ValueError("tier=image needs at least one image")
    media = _media_config()
    if provider:
        row = _row_for(provider)
        if row is None:
            raise ValueError("unknown judge: %s" % provider)
        creds = credentials(row, resolve_key, media)
        if api_key:
            creds = dict(creds or {"url": row.get("url")}, token=api_key)
        if url:
            creds = dict(creds or {"token": None}, url=url)
        if not creds or (not row.get("keyless") and not creds.get("token")):
            raise JudgeUnavailable("%s is not set up (no key%s)"
                                   % (row["id"], ", or no account ID" if "{account_id}" in str(row.get("url")) else ""),
                                   reason="no-key")
        # A pin checks the table's cap but not a failed probe: the key-row Test
        # is itself a pinned call, and a judge whose earlier probe failed has to
        # stay re-verifiable.
        # Too MANY images for a judge that reads some is a limit (400, below).
        if tier == "image" and _cap(row, "maxImages") == 0:
            raise JudgeUnavailable("%s does not read images" % row["id"],
                                   reason="no-image-judge")
    else:
        # Prefer a judge this request fits (Clef Flash holds 24k tokens, Local
        # Clef 26 options, Jev no images); when none fits, the first usable one
        # still answers so its limit comes back as the ValueError (a 400).
        def fits(r):
            # type: (Dict[str, Any]) -> bool
            try:
                validate_questions(questions, r)
                cap = _cap(r, "maxImages")
                if cap is not None and len(images) > cap:
                    return False
                check_context(state, questions, r, len(images))
                return True
            except ValueError:
                return False
        pid = (pick(tier, len(images), resolve_key, media=media, fits=fits)
               or pick(tier, len(images), resolve_key, media=media))
        if pid is None:
            if tier == "image":
                raise JudgeUnavailable("no judge that reads images is set up",
                                       reason="no-image-judge")
            raise JudgeUnavailable("no typed judge is set up (add a TypeSafe, Cloudflare "
                                   "or OpenAI key)", reason="no-key")
        row = _row_for(pid)
        creds = credentials(row, resolve_key, media)
    validate_questions(questions, row)
    max_images = _cap(row, "maxImages")
    if max_images is not None and len(images) > max_images:
        raise ValueError("%d images in one request, %s takes at most %d"
                         % (len(images), row["id"], max_images))
    uris = [load_image(img, image_roots) for img in images]
    total_cap = _cap(row, "maxImageBytesTotal")
    if total_cap is not None:
        total = sum(len(u) - len(u.split(",", 1)[0]) - 1 for u in uris) * 3 // 4
        if total > total_cap:
            raise ValueError("images total %s decoded, %s takes at most %s - send fewer "
                             "or smaller frames" % (_fmt_bytes(total), row["id"], _fmt_bytes(total_cap)))
    check_context(state, questions, row, len(uris))
    use_model = model or row.get("model")
    sender = _WIRES.get(row.get("wire"))
    if sender is None:
        raise JudgeError("%s: unknown wire %r in judges.json" % (row["id"], row.get("wire")))
    answers = sender(row, creds, state, questions, uris, use_model, timeout, max_retries)
    return {"answers": answers, "provider": row["id"], "model": use_model, "tier": tier,
            "thresholds": thresholds(kind, row["id"])}


def probe(pid, resolve_key=None, url=None, api_key=None, timeout=20):
    # type: (str, Optional[Callable[[str], Optional[str]]], Optional[str], Optional[str], float) -> Dict[str, Any]
    """The key-row Test: one text noul for every judge, and for a judge whose
    table entry can read images, a solid red and a solid blue PNG with "The
    image is mostly red". Images pass only when red >= 0.8 and blue <= 0.2.
    Returns {text: bool, images: True|False|None, detail}; never raises."""
    out = {"text": False, "images": None, "detail": None}  # type: Dict[str, Any]
    row = provider(pid)
    if row is None:
        out["detail"] = "unknown judge %s" % pid
        return out
    common = dict(provider=pid, resolve_key=resolve_key, url=url, api_key=api_key,
                  timeout=timeout, max_retries=0)
    try:
        res = judge("The sky is blue.",
                    {"t": {"type": "noul", "instructions": "This statement mentions the sky."}},
                    **common)
        out["text"] = noul_value(res["answers"].get("t")) is not None
        if not out["text"]:
            out["detail"] = "answered without a usable noul"
            return out
    except (JudgeError, ValueError) as exc:
        out["detail"] = str(exc)[:300]
        return out
    cap = row.get("maxImages")
    if cap is not None and (not isinstance(cap, int) or cap < 1):
        return out  # the table says text only; nothing to verify
    q = {"red": {"type": "noul", "instructions": "The image is mostly red."}}
    seen = {}  # type: Dict[str, Optional[float]]
    for name, rgb in (("red", (220, 30, 30)), ("blue", (30, 60, 220))):
        try:
            res = judge("An image is attached.", q, tier="image",
                        images=[solid_png(rgb)], **common)
            seen[name] = noul_value(res["answers"].get("red"))
        except JudgeUnavailable as exc:
            out["detail"] = str(exc)[:300]
            return out
        except (JudgeError, ValueError) as exc:
            seen[name] = None
            out["detail"] = "image probe: %s" % str(exc)[:280]
    red, blue = seen.get("red"), seen.get("blue")
    out["images"] = bool(red is not None and blue is not None and red >= 0.8 and blue <= 0.2)
    out["probe"] = {"red": red, "blue": blue}
    return out


# ── Reading an answer ───────────────────────────────────────────────────────
# Every reader is TOTAL: a missing or malformed answer yields the conservative
# value (a noul that does not pass, an empty ranking, an "escalate" band),
# never an exception. A judge that throws on a shape it did not expect would
# take a build down with it.

def noul_value(answer):
    # type: (Any) -> Optional[float]
    if isinstance(answer, (int, float)) and not isinstance(answer, bool):
        return float(answer)
    if isinstance(answer, dict):
        return _num(answer.get("noul"))
    return None


def noul_pass(answer, threshold=0.5):
    # type: (Any, float) -> bool
    v = noul_value(answer)
    return v is not None and v >= threshold


def choice_ranked(answer, n=None):
    # type: (Any, Optional[int]) -> List[Tuple[str, float]]
    probs = None
    if isinstance(answer, dict):
        probs = answer.get("probabilities")
        if not isinstance(probs, dict) and isinstance(answer.get("choice"), str):
            probs = {answer["choice"]: float(answer.get("confidence") or 1.0)}
    if not isinstance(probs, dict):
        return []
    rows = [(str(k), float(v)) for k, v in probs.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)]
    rows.sort(key=lambda kv: kv[1], reverse=True)
    return rows[:n] if n else rows


def confidence(answer):
    # type: (Any) -> Optional[float]
    return _num(answer.get("confidence")) if isinstance(answer, dict) else None


def band(conf, low=0.55, high=0.8):
    # type: (Optional[float], float, float) -> str
    """act / confirm / escalate. A missing confidence escalates: an unknown is
    not a pass."""
    if conf is None:
        return "escalate"
    if conf >= high:
        return "act"
    if conf >= low:
        return "confirm"
    return "escalate"


def noul_verdict(answer, th):
    # type: (Any, Dict[str, Any]) -> Dict[str, Any]
    """One noul read against a threshold row: {noul, pass, confidence, band}.
    A noul's own distance from the midpoint is its confidence when the judge
    sends none: 0.97 and 0.03 are both decisive, 0.52 is not. `pass` is None
    when there is no usable answer."""
    v = noul_value(answer)
    if v is None:
        return {"noul": None, "pass": None, "confidence": None, "band": "escalate"}
    conf = confidence(answer)
    if conf is None:
        conf = round(abs(v - 0.5) * 2.0, 4)
    return {"noul": v, "pass": v >= float(th.get("noul", 0.5)), "confidence": conf,
            "band": band(conf, float(th.get("low", 0.55)), float(th.get("high", 0.8)))}


# ── Thresholds, per provider and per kind ───────────────────────────────────
# Lookup order: providers[p][kind] -> providers[p].default -> kind -> default.
# Clef at 0.8 does not mean Jev at 0.8, so a calibrated band is per provider.
# `trustPass` lets a confident PASS skip the model call it shadows; only
# tools/qa/jev_calibrate.py writes it, from a labelled set.

_THRESHOLD_FALLBACK = {"low": 0.55, "high": 0.80, "noul": 0.50}


def thresholds(kind="default", provider=None):
    # type: (str, Optional[str]) -> Dict[str, Any]
    table = _read_json(THRESHOLDS_PATH)
    table = table if isinstance(table, dict) else {}
    per = table.get("providers") if isinstance(table.get("providers"), dict) else {}
    mine = per.get(provider) if provider and isinstance(per.get(provider), dict) else {}
    row = None
    for cand in (mine.get(kind), mine.get("default"), table.get(kind), table.get("default")):
        if isinstance(cand, dict):
            row = cand
            break
    out = dict(_THRESHOLD_FALLBACK)  # type: Dict[str, Any]
    for k in ("low", "high", "noul"):
        v = _num((row or {}).get(k))
        if v is not None:
            out[k] = v
    out["trustPass"] = bool((row or {}).get("trustPass") is True)
    return out


# ── Shadow log ──────────────────────────────────────────────────────────────

def shadow_log(entry):
    # type: (Dict[str, Any]) -> None
    """Append one JSON line to the shadow log (rotated at 5 MB to one .1
    generation). Shadow mode's whole output; never raises."""
    try:
        os.makedirs(os.path.dirname(SHADOW_LOG_PATH), exist_ok=True)
        try:
            if os.path.getsize(SHADOW_LOG_PATH) >= SHADOW_LOG_MAX_BYTES:
                os.replace(SHADOW_LOG_PATH, SHADOW_LOG_PATH + ".1")
        except OSError:
            pass
        line = dict(entry)
        line.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        if "id" not in line:
            import hashlib
            line["id"] = hashlib.sha1(json.dumps([line["ts"], line.get("kind"), line.get("subject"),
                                                  line.get("source"), random.random()],
                                                 default=str).encode("utf-8")).hexdigest()[:10]
        with open(SHADOW_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_log(paths=None):
    # type: (Optional[List[str]]) -> List[Dict[str, Any]]
    """Every row of the answer log (the .1 generation first), with its label
    merged in as `expected` when one has been given. Unparseable lines are
    skipped."""
    labels = load_labels()
    rows = []  # type: List[Dict[str, Any]]
    for path in paths or [SHADOW_LOG_PATH + ".1", SHADOW_LOG_PATH]:
        try:
            with open(path, encoding="utf-8") as f:
                for raw in f:
                    try:
                        row = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(row, dict):
                        if row.get("id") in labels:
                            row["expected"] = labels[row["id"]]
                        rows.append(row)
        except OSError:
            continue
    return rows


def load_labels():
    # type: () -> Dict[str, Any]
    data = _read_json(LABELS_PATH)
    return data if isinstance(data, dict) else {}


def save_labels(pairs):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Merge {logId: expected answer} into the labels file and return it."""
    data = load_labels()
    data.update(pairs)
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)
    tmp = LABELS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.replace(tmp, LABELS_PATH)
    return data

