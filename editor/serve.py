#!/usr/bin/env python3
"""Editor dev server.

Serves the project root statically (so editor iframes can resolve `../source/…`)
AND exposes a small JSON API for the editor:

  POST /__save?name=<file>            Write a whitelisted file at the repo root.
  POST /__layout                       Persist canvas layout state.
  POST /__workflow                     Persist workflow.json.

v3.1 — project-level branches deprecated. /__branch, /__promote,
/__promote_frame removed. Asset-versioning's sibling-node branching
(workflow/runs/<nodeId>/) is the replacement for "explore alternatives".
See docs/features/deprecate-project-branches.md.

All writes are confined to the repo root; sources/targets can't escape via `..`.
"""
import atexit
import datetime as _dt
import hashlib
import http.server
import json
import os
import re
import shutil
import signal
import socketserver
import stat
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
import base64
import contextlib

# Ensure the editor directory is on sys.path so `from prompts.discovery import …`
# resolves regardless of how serve.py is launched (double-clicked .command,
# `python3 editor/serve.py`, or `python3 -m editor.serve`). When run as a
# script the script's directory is added automatically; this guard covers
# the `-m` and double-launch-from-elsewhere cases.
_EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
if _EDITOR_DIR not in sys.path:
    sys.path.insert(0, _EDITOR_DIR)

from prompts import node_agent_preambles as _node_preambles  # v2.1 — per-node agent preambles
import exports as _exports  # per-asset export bundles (README + serve.* + files)


def _pick_port() -> int:
    # Allow the host (Claude preview, double-click serve.command, plain CLI) to choose.
    # Precedence: explicit CLI arg → PORT env (Claude preview) → EDITOR_PORT → default.
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    for key in ("PORT", "EDITOR_PORT"):
        v = os.environ.get(key)
        if v and v.isdigit():
            return int(v)
    return 5731


PORT = _pick_port()

# ── Three-tier roots (Phase 6 workspace mode) ────────────────────────────────
# INSTALL_ROOT  — where this file's parent lives. Holds the editor binary
#                 (editor/app.js, styles.css, serve.py, index.html) and, in
#                 the install layout, the shared agent protocol (AGENTS.md,
#                 PROTOTYPE.md, docs/agents/**). Always derived from __file__.
# WORKSPACE_DIR — opt-in. When set via TH_WORKSPACE_DIR env, the daemon
#                 becomes multi-project: every request resolves to a per-
#                 project root via ?project=<id> in the query or body.
# project_root  — per-request. <WORKSPACE_DIR>/<id>/ in workspace mode,
#                 INSTALL_ROOT in single-project mode (= today's behavior).
#                 Holds source/, editor/branches/, editor/data.js, plus
#                 per-project docs (DESIGN.md, NOTES.md, prototype.json,
#                 MERGES.md, FORK_REQUEST.md, ...).
#
# Back-compat: with no TH_WORKSPACE_DIR set, the daemon behaves identically
# to the pre-Phase-6 single-repo install (INSTALL_ROOT == project root).
INSTALL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EDITOR_DIR   = os.path.join(INSTALL_ROOT, "editor")

_workspace_env = os.environ.get("TH_WORKSPACE_DIR")
_single_env = (os.environ.get("TH_SINGLE_PROJECT") or "").strip().lower()
_single_optout = _single_env in {"1", "true", "yes", "on"}
if _single_optout:
    # Explicit opt-out — keep the pre-Phase-6 single-repo behavior.
    WORKSPACE_DIR = None
elif _workspace_env:
    WORKSPACE_DIR = os.path.abspath(os.path.expanduser(_workspace_env))
    if not os.path.isdir(WORKSPACE_DIR):
        print(
            f"warning: TH_WORKSPACE_DIR={WORKSPACE_DIR!r} is not a directory — "
            "falling back to single-project mode",
            flush=True,
        )
        WORKSPACE_DIR = None
else:
    # Default (no env vars): auto-detect the workspace by checking the on-disk
    # shape around INSTALL_ROOT. Two valid layouts:
    #
    #   A. INSTALL_ROOT IS the workspace (post-Phase-6 cleanup, the right shape):
    #      INSTALL_ROOT contains no source/ of its own but holds the editor/
    #      toolchain plus N project subfolders (each with their own source/).
    #      Use INSTALL_ROOT itself as the workspace. This is the layout you
    #      get when running serve.py from `<workspace>/editor/serve.py`.
    #
    #   B. INSTALL_ROOT IS a project sitting alongside other projects
    #      (legacy / entangled layout where the install dir doubles as a
    #      project): INSTALL_ROOT has its own source/, and the workspace is
    #      one level up. Fall back to parent(INSTALL_ROOT).
    #
    # TH_SINGLE_PROJECT=1 disables both (legacy single-repo behavior).
    _install_is_project = os.path.isdir(os.path.join(INSTALL_ROOT, "source"))
    if not _install_is_project:
        # Layout A — INSTALL_ROOT is the workspace itself.
        WORKSPACE_DIR = INSTALL_ROOT
    else:
        # Layout B — install dir is a project, workspace is one level up.
        _candidate = os.path.dirname(INSTALL_ROOT)
        if _candidate and _candidate != INSTALL_ROOT and os.path.isdir(_candidate):
            WORKSPACE_DIR = _candidate
        else:
            WORKSPACE_DIR = None

# In single-project mode this is the only project root the daemon ever resolves.
# In Layout A (INSTALL_ROOT == WORKSPACE_DIR), this points at the workspace dir
# itself — which has no source/ so it can't satisfy /source/* requests on its
# own, but it's only consulted as a translate_path fallback after Referer
# resolution has already had its chance.
DEFAULT_PROJECT_ROOT = INSTALL_ROOT

# Phase-6.2 cleanup — projects live under a dedicated `projects/` subfolder of
# the workspace (instead of being root-level siblings of editor/, AGENTS.md,
# etc.). Keeps the workspace root readable at a glance. The folder is created
# lazily by /__projects/new; if it doesn't exist yet, _list_projects() falls
# back to scanning the root for back-compat with the pre-cleanup layout.
PROJECTS_DIR = os.path.join(WORKSPACE_DIR, "projects") if WORKSPACE_DIR else None

NAME_OK = re.compile(r"^[A-Za-z0-9._-]+$")
SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
PROJECT_ID_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_NAMES = {
    # v3.1 — branches deprecated. MERGES.md / FORK_REQUEST.md no longer allowed.
    "edits.json", "DESIGN.md", "NOTES.md", "UPDATE_SOURCE.txt",
    # Per-view "please-populate" requests. Each is written by clicking the
    # "Generate" button on the matching empty-state card. The agent reads it
    # on the next Workflow 1 run, runs the corresponding Step 5d sub-step,
    # and deletes the file when done.
    "STATEMACHINE_REQUEST.md", "TIMELINE_REQUEST.md", "GRID_REQUEST.md",
}
MAX_BYTES = 20 * 1024 * 1024  # 20 MB — annotated screenshots can be chunky

# Phase 4a — BYOK media config. Sits outside the workspace so multiple projects
# share the same keys; mode 0600 so it isn't world-readable.
MEDIA_CONFIG_DIR  = os.path.expanduser("~/.test-harness")
MEDIA_CONFIG_PATH = os.path.join(MEDIA_CONFIG_DIR, "media-config.json")

# Aspect ratio → OpenAI gpt-image-1 size mapping. The model accepts a small
# fixed set: 1024×1024, 1536×1024, 1024×1536, or "auto". Unknown aspect strings
# fall through unchanged so users can pass a literal size if they need to.
ASPECT_TO_SIZE = {
    "1:1":  "1024x1024",
    "3:2":  "1536x1024",
    "16:9": "1536x1024",
    "2:3":  "1024x1536",
    "9:16": "1024x1536",
    "auto": "auto",
}


def _media_config_load():
    if not os.path.isfile(MEDIA_CONFIG_PATH):
        return {}
    try:
        with open(MEDIA_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _media_config_save(cfg):
    try:
        os.makedirs(MEDIA_CONFIG_DIR, exist_ok=True)
        try: os.chmod(MEDIA_CONFIG_DIR, 0o700)
        except Exception: pass
    except Exception:
        pass
    with open(MEDIA_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    try: os.chmod(MEDIA_CONFIG_PATH, 0o600)
    except Exception: pass


# Phase 4b — Per-provider key resolution. Env var first (TH_<PROVIDER>_API_KEY),
# then media-config.json. New providers slot in by adding an entry.
_PROVIDER_ENV_KEYS = {
    "openai":      "TH_OPENAI_API_KEY",
    "anthropic":   "TH_ANTHROPIC_API_KEY",
    "fal":         "TH_FAL_API_KEY",
    "xai":         "TH_XAI_API_KEY",
    "volcengine":  "TH_VOLCENGINE_API_KEY",
    "bfl":         "TH_BFL_API_KEY",
    "recraft":     "TH_RECRAFT_API_KEY",
    "nanobanana":  "TH_GEMINI_API_KEY",
    "leonardo":    "TH_LEONARDO_API_KEY",
    "meshy":       "TH_MESHY_API_KEY",
    "elevenlabs":  "TH_ELEVENLABS_API_KEY",
    "imagerouter": "TH_IMAGEROUTER_API_KEY",
    "quiver":      "TH_QUIVER_API_KEY",
}

def _resolve_provider_key(provider):
    env_name = _PROVIDER_ENV_KEYS.get(provider)
    if env_name:
        v = os.environ.get(env_name)
        if v and v.strip(): return v.strip()
    cfg = _media_config_load()
    p = cfg.get(provider) if isinstance(cfg, dict) else None
    if isinstance(p, dict):
        k = p.get("api_key")
        if isinstance(k, str) and k.strip(): return k.strip()
    return None


def _media_resolve_openai_key():
    # Back-compat shim — older code paths still call this name.
    return _resolve_provider_key("openai")


def _guess_image_mime(path):
    pl = (path or "").lower()
    if pl.endswith(".jpg") or pl.endswith(".jpeg"): return "image/jpeg"
    if pl.endswith(".webp"): return "image/webp"
    if pl.endswith(".gif"):  return "image/gif"
    if pl.endswith(".svg"):  return "image/svg+xml"
    return "image/png"


def _file_to_data_uri(abs_path):
    """Read a local file and return a data URI suitable for external APIs."""
    with open(abs_path, "rb") as f:
        bytes_ = f.read()
    mime = _guess_image_mime(abs_path)
    return f"data:{mime};base64,{base64.b64encode(bytes_).decode('ascii')}"


def _download_bytes(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


# ── Provider renderers ────────────────────────────────────────────────────
# Each renderer returns raw bytes for the generated/transformed asset. They
# do NOT touch the filesystem — the dispatcher in _asset_generate is the
# only thing that writes to disk. This keeps renderer code thin and testable.

# Per-model size mappings. gpt-image-* / dall-e-* / dall-e-2 differ.
_OPENAI_GPT_IMAGE_SIZES = {
    "1:1":  "1024x1024", "3:2": "1536x1024", "16:9": "1536x1024",
    "2:3":  "1024x1536", "9:16": "1024x1536", "auto": "auto",
}
_OPENAI_DALLE3_SIZES = {
    "1:1":  "1024x1024", "3:2": "1792x1024", "16:9": "1792x1024",
    "2:3":  "1024x1792", "9:16": "1024x1792",
}
_OPENAI_DALLE2_SIZES = {
    "1:1":  "1024x1024", "3:2": "1024x1024", "16:9": "1024x1024",
    "2:3":  "1024x1024", "9:16": "1024x1024",
}

def _openai_edit_image(api_key, prompt, model, image_bytes, image_mime, aspect, options):
    """OpenAI /v1/images/edits — image-to-image via multipart/form-data.

    Used when a generate-image call also carries `input_path` / `input_data_uri`
    AND the model is in the gpt-image-1 family. Same response shape as
    /v1/images/generations (b64_json data array), but the model now
    consults the input image instead of generating purely from text.

    Hand-rolled multipart so we don't pull in `requests`/`httpx`."""
    import uuid
    model = model or "gpt-image-2"  # v3.4.7 — gpt-image-1 deprecates Oct 23, 2026
    boundary = "thMP" + uuid.uuid4().hex
    parts = []
    def add_field(name, value):
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )
    def add_file(name, filename, data, content_type):
        head = (f'--{boundary}\r\nContent-Disposition: form-data; '
                f'name="{name}"; filename="{filename}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n').encode("utf-8")
        parts.append(head)
        parts.append(data)
        parts.append(b"\r\n")
    add_field("model",  model)
    add_field("prompt", prompt)
    add_field("n",      "1")
    if model.startswith("gpt-image"):
        add_field("size", _OPENAI_GPT_IMAGE_SIZES.get(aspect, "1024x1024"))
    if isinstance(options, dict):
        if options.get("quality"):
            add_field("quality", options["quality"])
    ext_for_mime = {
        "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg",
        "image/webp": "webp",
    }.get((image_mime or "image/png").lower(), "png")
    add_file("image", f"input.{ext_for_mime}", image_bytes, image_mime or "image/png")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/edits",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        data=body,
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    try:
        b64 = data["data"][0]["b64_json"]
    except Exception:
        raise RuntimeError(f"unexpected OpenAI edits response shape: {list(data.keys())}")
    return base64.b64decode(b64)


def _openai_generate_image(api_key, prompt, model, aspect, options):
    """OpenAI Images. Handles the gpt-image-2 / gpt-image-1.5 / gpt-image-1
    family. The gpt-image-* models return b64_json natively (setting
    response_format actually 400s). DALL·E 2 + DALL·E 3 were shut down
    May 12, 2026 — their branches are kept below as dead code so legacy
    workflow.json files with old model IDs return a clean error rather
    than crashing."""
    model = model or "gpt-image-2"
    body = {"model": model, "prompt": prompt, "n": 1}
    if isinstance(options, dict):
        if options.get("quality"):    body["quality"]    = options["quality"]
        if options.get("background"): body["background"] = options["background"]

    if model.startswith("gpt-image"):
        body["size"] = _OPENAI_GPT_IMAGE_SIZES.get(aspect, "1024x1024")
    elif model == "dall-e-3":
        body["size"] = _OPENAI_DALLE3_SIZES.get(aspect, "1024x1024")
        body["response_format"] = "b64_json"
    elif model == "dall-e-2":
        body["size"] = _OPENAI_DALLE2_SIZES.get(aspect, "1024x1024")
        body["response_format"] = "b64_json"
    else:
        body["size"] = _OPENAI_GPT_IMAGE_SIZES.get(aspect, "1024x1024")

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    try:
        b64 = data["data"][0]["b64_json"]
    except Exception:
        raise RuntimeError(f"unexpected OpenAI response shape: {list(data.keys())}")
    return base64.b64decode(b64)


_FAL_IMAGE_SIZES = {
    "1:1":  "square_hd",
    "3:2":  "landscape_4_3",
    "16:9": "landscape_16_9",
    "2:3":  "portrait_4_3",
    "9:16": "portrait_16_9",
}

def _fal_request(api_key, model_path, body, timeout=300):
    """Sync POST to fal.run/<model_path>. fal accepts `Authorization: Key <…>`
    and returns JSON whose shape varies per model — callers parse out the
    output URL themselves."""
    url = f"https://fal.run/{model_path}"
    req = urllib.request.Request(
        url, method="POST",
        headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _fal_extract_image_url(payload):
    """Most fal endpoints return one of:
         { images: [{ url }] }
         { image:    { url } }
       Walk both shapes; raise if nothing usable."""
    if isinstance(payload, dict):
        imgs = payload.get("images")
        if isinstance(imgs, list) and imgs:
            first = imgs[0]
            if isinstance(first, dict) and isinstance(first.get("url"), str):
                return first["url"]
            if isinstance(first, str):
                return first
        img = payload.get("image")
        if isinstance(img, dict) and isinstance(img.get("url"), str):
            return img["url"]
    raise RuntimeError(f"fal: no image url in response (keys: {list(payload.keys()) if isinstance(payload, dict) else '?'})")


def _fal_extract_video_url(payload):
    """fal video endpoints return one of:
         { video:  { url } }
         { videos: [{ url }] }
         { url: "..." }  (some t2v wrappers)
       Walk all shapes; raise if nothing usable."""
    if isinstance(payload, dict):
        vid = payload.get("video")
        if isinstance(vid, dict) and isinstance(vid.get("url"), str):
            return vid["url"]
        if isinstance(vid, str):
            return vid
        vids = payload.get("videos")
        if isinstance(vids, list) and vids:
            first = vids[0]
            if isinstance(first, dict) and isinstance(first.get("url"), str):
                return first["url"]
            if isinstance(first, str):
                return first
        u = payload.get("url")
        if isinstance(u, str) and any(u.lower().endswith(ext) for ext in (".mp4", ".webm", ".mov")):
            return u
    raise RuntimeError(f"fal: no video url in response (keys: {list(payload.keys()) if isinstance(payload, dict) else '?'})")


def _fal_generate_image(api_key, prompt, model, aspect, options):
    """fal.ai text-to-image. Works for fal-ai/flux/*, recraft-v3, ideogram, SD3.5."""
    body = {
        "prompt":     prompt,
        "image_size": _FAL_IMAGE_SIZES.get(aspect, "square_hd"),
        "num_images": 1,
    }
    if isinstance(options, dict):
        # Pass through common knobs; per-model overrides land via skill node options.
        for k in ("num_inference_steps", "guidance_scale", "seed", "enable_safety_checker", "output_format", "style"):
            if k in options and options[k] is not None: body[k] = options[k]
    payload = _fal_request(api_key, model, body)
    image_url = _fal_extract_image_url(payload)
    return _download_bytes(image_url)


def _fal_generate_video(api_key, prompt, model, aspect, options):
    """fal.ai text-to-video / image-to-video. Works for fal-ai/veo3.1,
    fal-ai/luma-dream-machine/ray-2/text-to-video, fal-ai/kling-video/v2.5-turbo,
    fal-ai/minimax/hailuo-2.3-fast, fal-ai/seedance-2.0, etc. Returns mp4
    bytes downloaded from the response's video URL. Aspect ratios per
    fal's vocabulary (16:9 / 9:16 / 1:1) — most models accept any of them.
    NOTE: the bare `fal-ai/luma-dream-machine` endpoint was deprecated in
    June 2026; use the ray-2 sub-paths instead."""
    body = {"prompt": prompt}
    # fal's video models use different param names per family; pass a
    # superset of common knobs and rely on the model to ignore the ones
    # it doesn't understand. Per-model overrides land via skill node options.
    # v3.4.12 — 1:1 collapses to 16:9 because almost every video endpoint
    # rejects square (Luma Ray, Veo 3.1, Kling 2.5, Hailuo all return
    # `{"detail":[{"msg":"Input should be '16:9' or '9:16'"}]}` for 1:1).
    # Square is meaningful for still images, not for video — so the safe
    # default is landscape until the user explicitly picks a portrait.
    ASPECT_MAP_VIDEO = {
        "1:1":  "16:9",
        "3:2":  "16:9",
        "16:9": "16:9",
        "2:3":  "9:16",
        "9:16": "9:16",
    }
    body["aspect_ratio"] = ASPECT_MAP_VIDEO.get(aspect, "16:9")
    if isinstance(options, dict):
        for k in ("duration", "fps", "seed", "loop", "guidance_scale", "negative_prompt", "image_url"):
            if k in options and options[k] is not None: body[k] = options[k]
    payload = _fal_request(api_key, model, body, timeout=300)
    video_url = _fal_extract_video_url(payload)
    return _download_bytes(video_url)


def _fal_transform_image(api_key, model, input_abs_path, options, input_data_uri=None):
    """fal.ai image-in / image-out endpoints (rembg, upscale, etc.). Accepts
    either a local file path (encoded server-side) or a pre-built data URI
    (when the input is inline-SVG or another non-file source)."""
    if input_data_uri:
        url = input_data_uri
    else:
        if not os.path.isfile(input_abs_path):
            raise RuntimeError(f"input image not found: {input_abs_path}")
        url = _file_to_data_uri(input_abs_path)
    body = {"image_url": url}
    if isinstance(options, dict):
        for k, v in options.items():
            if v is not None and k != "image_url": body[k] = v
    payload = _fal_request(api_key, model, body)
    image_url = _fal_extract_image_url(payload)
    return _download_bytes(image_url)


# Quiver AI — vector-native generator that returns an SVG document directly.
# Endpoint: POST https://api.quiver.ai/v1/svgs/generations
# Returns:  { data: [ { svg: "<svg…/>", mime_type: "image/svg+xml" } ], credits, … }
# Falls back to Pathway B (Claude hand-authoring) when no key is set, so the
# skill node behaves the same to the user — just faster & higher fidelity
# whenever a Quiver key is present.
def _quiver_generate_svg(api_key, prompt, model, options):
    model = (model or "").strip() or "arrow-1.1"
    body = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "stream": False,
    }
    if isinstance(options, dict):
        inst = options.get("instructions")
        if isinstance(inst, str) and inst.strip():
            body["instructions"] = inst.strip()
    req = urllib.request.Request(
        "https://api.quiver.ai/v1/svgs/generations",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    try:
        svg_text = data["data"][0]["svg"]
    except Exception:
        raise RuntimeError(f"unexpected Quiver response shape: {list(data.keys())}")
    if not isinstance(svg_text, str) or "<svg" not in svg_text.lower():
        raise RuntimeError("Quiver returned no <svg> payload")
    return svg_text.encode("utf-8")


# Phase 4c — find an inline SVG in the project's source files and replace it
# with new markup. Used when a skill writes to an inline-SVG asset target —
# the resulting bytes replace the original SVG in place, so the prototype
# renders the regenerated visual.
#
# Matching strategy:
#   1. Exact substring match (works for plain HTML sources).
#   2. JSX-style match — convert the rendered SVG's HTML-style attributes
#      back to React JSX conventions (class → className, kebab → camelCase,
#      xlink:href → xlinkHref) before searching. Handles common JSX cases.
#   3. Fallback path-data match — extract the SVG's most distinctive content
#      (the first <path d="…"/>) and locate any SVG element in source whose
#      path data matches. The whole containing SVG element is then replaced.
# Scans common source extensions: .html, .htm, .jsx, .tsx, .js, .ts.

# Rendered HTML → JSX attribute mapping for SVG. Covers the kebab-case
# attributes React JSX rewrites; the remaining attrs (already camelCase
# in both, like preserveAspectRatio / viewBox) need no transform.
_HTML_TO_JSX_SVG_ATTRS = [
    ("class",                  "className"),
    ("stroke-width",           "strokeWidth"),
    ("stroke-dasharray",       "strokeDasharray"),
    ("stroke-dashoffset",      "strokeDashoffset"),
    ("stroke-linecap",         "strokeLinecap"),
    ("stroke-linejoin",        "strokeLinejoin"),
    ("stroke-miterlimit",      "strokeMiterlimit"),
    ("stroke-opacity",         "strokeOpacity"),
    ("fill-rule",              "fillRule"),
    ("fill-opacity",           "fillOpacity"),
    ("clip-path",              "clipPath"),
    ("clip-rule",              "clipRule"),
    ("font-family",            "fontFamily"),
    ("font-size",              "fontSize"),
    ("font-weight",            "fontWeight"),
    ("font-style",             "fontStyle"),
    ("text-anchor",            "textAnchor"),
    ("text-decoration",        "textDecoration"),
    ("dominant-baseline",      "dominantBaseline"),
    ("alignment-baseline",     "alignmentBaseline"),
    ("xlink:href",             "xlinkHref"),
    ("xlink:title",            "xlinkTitle"),
    ("stop-color",             "stopColor"),
    ("stop-opacity",           "stopOpacity"),
    ("vector-effect",          "vectorEffect"),
    ("paint-order",            "paintOrder"),
    ("color-interpolation",    "colorInterpolation"),
    ("marker-end",             "markerEnd"),
    ("marker-start",           "markerStart"),
    ("marker-mid",             "markerMid"),
]

def _to_jsx_svg(html):
    """Rewrite an HTML-style SVG markup string to JSX conventions so we can
    search for it inside a React JSX source file. Only handles attribute
    naming — element structure is unchanged."""
    out = html
    for html_attr, jsx_attr in _HTML_TO_JSX_SVG_ATTRS:
        # \b doesn't match the colon in xlink:href, so use a lookbehind for
        # whitespace/quote/< boundary to avoid stomping partial words.
        out = re.sub(
            r"(?<=[\s\"'<])" + re.escape(html_attr) + r"=",
            jsx_attr + "=",
            out,
        )
    return out


def _extract_first_path_d(svg_html):
    """Pull the first <path d="…"/> string from an SVG. Used as a stable
    content fingerprint for fuzzy matching when normalized matching fails."""
    m = re.search(r'<path\b[^>]*\sd\s*=\s*"([^"]+)"', svg_html)
    return m.group(1) if m else None


def _replace_inline_svg_in_sources(project_root, branch, original_svg, new_content):
    # v3.1 — branches deprecated. `branch` arg ignored; source/ is flat.
    src_root = os.path.join(project_root, "source")
    if not os.path.isdir(src_root):
        raise RuntimeError("source/ not found")
    EXTS = (".html", ".htm", ".jsx", ".tsx", ".js", ".ts")
    files = []
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "dist", "build")]
        for fname in filenames:
            if fname.lower().endswith(EXTS):
                files.append(os.path.join(dirpath, fname))

    # Pre-compute candidates for the three match strategies.
    jsx_candidate = _to_jsx_svg(original_svg)
    fingerprint_d = _extract_first_path_d(original_svg)

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue

        # Strategy 1: exact match.
        new_text = None
        if original_svg in text:
            new_text = text.replace(original_svg, new_content, 1)

        # Strategy 2: JSX-normalized match.
        elif jsx_candidate != original_svg and jsx_candidate in text:
            new_text = text.replace(jsx_candidate, new_content, 1)

        # Strategy 3: fingerprint match — locate any <svg>...</svg> block
        # in source that contains the same first-path "d" attribute, then
        # replace that whole block.
        elif fingerprint_d:
            # Escape the path data for use inside a regex pattern. Path data
            # is mostly digits/letters/spaces so this stays cheap.
            d_escaped = re.escape(fingerprint_d)
            # Walk every <svg> element in the file and check if its inner
            # text contains the fingerprint path. Non-greedy match across
            # newlines for the SVG element.
            for m in re.finditer(r"<svg\b[^>]*>.*?</svg\s*>", text, re.DOTALL):
                block = m.group(0)
                if re.search(r'd\s*=\s*"' + d_escaped + r'"', block):
                    new_text = text[:m.start()] + new_content + text[m.end():]
                    break

        if new_text is not None:
            try:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_text)
            except Exception as e:
                raise RuntimeError(f"could not write {os.path.basename(fpath)}: {e}")
            return [os.path.relpath(fpath, project_root)]

    raise RuntimeError(
        "could not locate the inline SVG in source/ — tried exact match, "
        "JSX-normalized attribute names (class/className, kebab/camel), and "
        "path-data fingerprint. The PNG was still written to disk; you can "
        "manually replace the <svg> in your prototype with an <img> tag."
    )


# (skill_id, provider) → renderer for image-producing skills. The dispatcher
# in _asset_generate looks up here; unknown pairs respond 400 with a clear
# message. Renderers return raw bytes; the dispatcher owns disk writes.
_GENERATE_DISPATCH = {
    ("generate-image", "openai"): "openai_image",
    ("generate-image", "fal"):    "fal_image",
    # Pathway-A SVG generation via Quiver. When the user runs an svg-gen
    # node and a Quiver key is configured, the editor routes here instead
    # of falling back to Pathway B (Claude writing the SVG by hand).
    ("svg-gen",        "quiver"): "quiver_svg",
    # Real video generation via fal. The skill catalog's `video-gen`
    # declares `output: "video"` + `pathwayAFallback: { provider: "fal",
    # model: "fal-ai/veo3.1" }` (was luma-dream-machine until June 2026 when
    # that bare endpoint was deprecated). The dispatcher routes here, calls
    # fal.run, parses the response with _fal_extract_video_url, and
    # downloads the mp4 bytes to the spawned `.mp4` path.
    ("video-gen",      "fal"):    "fal_video",
}
_TRANSFORM_DISPATCH = {
    ("rembg",   "local"): "local_rembg",
    ("rembg",   "fal"):   "fal_transform",
    ("upscale", "fal"):   "fal_transform",
}


# Phase 4c — Local transform via the rembg python package (Daniel Gatis,
# github.com/danielgatis/rembg). No API key required.
#
# Why subprocess instead of `import rembg` in-process:
# the daemon's sys.path is fixed at startup, so packages installed via the
# Install button (`pip install --user rembg`) wouldn't be importable until
# the daemon restarts. Spawning `python3 -c "from rembg import remove; …"`
# re-evaluates sys.path on every invocation, so a freshly-installed rembg
# is usable immediately. Per-call overhead is ~1-3 s (Python startup +
# model load); first call downloads the ONNX model (~170 MB) into ~/.u2net/.
def _local_rembg(input_abs_path, model_name, options):
    if not os.path.isfile(input_abs_path):
        raise RuntimeError(f"input image not found: {input_abs_path}")
    with open(input_abs_path, "rb") as f:
        input_bytes = f.read()
    name = (model_name or "u2net").strip()
    # Tiny driver script piped via stdin/stdout. Keeps the daemon agnostic of
    # rembg's actual import path and version-specific API differences.
    script = (
        "import sys\n"
        f"from rembg import remove, new_session\n"
        f"sess = new_session({name!r})\n"
        "data = sys.stdin.buffer.read()\n"
        "out = remove(data, session=sess)\n"
        "sys.stdout.buffer.write(out)\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            input=input_bytes, capture_output=True, timeout=300, check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("python3 not found")
    except subprocess.TimeoutExpired:
        raise RuntimeError("rembg timed out after 5 minutes")
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", "replace")
        if "No module named 'rembg'" in stderr or "No module named rembg" in stderr:
            raise RuntimeError(
                "rembg is not installed. Open Settings (⚙) → Local skills → click Install rembg.",
            )
        raise RuntimeError(f"rembg failed: {stderr.strip()[:500]}")
    return result.stdout


# Phase 4c — text-output skills (LLM call, describe image). These don't
# write to disk; they return the generated text inline so the UI can route
# it into downstream prompt nodes.
def _openai_chat(api_key, messages, model="gpt-4o-mini", options=None):
    body = {"model": model or "gpt-4o-mini", "messages": messages}
    if isinstance(options, dict):
        for k in ("temperature", "max_tokens", "top_p"):
            if k in options and options[k] is not None: body[k] = options[k]
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"unexpected OpenAI chat response shape: {list(data.keys())}")


# Phase 4d — agent tool loop. Returns (final_text, tool_log). dispatch is a
# function(name, args_dict) → str. Caps the tool loop at MAX_ITERS so a
# runaway model can't infinite-loop us.
def _openai_chat_tools(api_key, messages, model, tools, dispatch, options=None, max_iters=12):
    msgs = list(messages)
    tool_log = []
    for _ in range(max_iters):
        body = {"model": model or "gpt-4o-mini", "messages": msgs, "tools": tools, "tool_choice": "auto"}
        if isinstance(options, dict):
            for k in ("temperature", "max_tokens", "top_p"):
                if k in options and options[k] is not None: body[k] = options[k]
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps(body).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        msg = data["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return (msg.get("content") or ""), tool_log
        # Echo the assistant turn with its tool_calls, then dispatch each.
        msgs.append({
            "role": "assistant",
            "content": msg.get("content") or "",
            "tool_calls": tool_calls,
        })
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            try: args = json.loads(fn.get("arguments") or "{}")
            except Exception: args = {}
            try: result = dispatch(name, args)
            except Exception as e: result = f"Error: {type(e).__name__}: {e}"
            result_str = result if isinstance(result, str) else json.dumps(result)
            tool_log.append({"name": name, "args": args, "result_preview": result_str[:200]})
            msgs.append({
                "role": "tool",
                "tool_call_id": tc.get("id") or "",
                "content": result_str[:32000],
            })
    return "(agent stopped: exceeded max tool iterations)", tool_log


# Phase 4d — sandboxed file dispatch. read_root_abs and write_root_abs must
# be absolute, normalized paths under the project root. All tool args resolve
# through this and reject anything that escapes.
def _make_agent_dispatch(read_root_abs, write_root_abs, max_file_bytes=200_000):
    read_real = os.path.realpath(read_root_abs) if read_root_abs else None
    def _resolve(root_abs, rel):
        rel = (rel or "").strip().lstrip("/")
        if ".." in rel.split("/"): raise ValueError("path may not contain '..'")
        target = os.path.realpath(os.path.join(root_abs, rel)) if rel else os.path.realpath(root_abs)
        root_real = os.path.realpath(root_abs)
        if target != root_real and not target.startswith(root_real + os.sep):
            raise ValueError("path escapes root")
        return target
    def dispatch(name, args):
        if name == "list_dir":
            if not read_real: return "Error: no folder-read connected"
            target = _resolve(read_real, args.get("path") or "")
            if not os.path.isdir(target): return f"Error: not a directory"
            entries = []
            for n in sorted(os.listdir(target)):
                if n.startswith("."): continue
                p = os.path.join(target, n)
                if os.path.isdir(p): entries.append(f"dir   {n}/")
                else: entries.append(f"file  {n}  ({os.path.getsize(p)} bytes)")
            return "\n".join(entries) if entries else "(empty directory)"
        if name == "read_file":
            if not read_real: return "Error: no folder-read connected"
            target = _resolve(read_real, args.get("path") or "")
            if not os.path.isfile(target): return f"Error: not a file"
            size = os.path.getsize(target)
            if size > max_file_bytes:
                return f"Error: file too large ({size} bytes > {max_file_bytes} limit). Read a smaller file or ask for a specific section."
            with open(target, "rb") as f: raw = f.read()
            try: return raw.decode("utf-8")
            except UnicodeDecodeError: return f"Error: file is binary, not text"
        return f"Error: unknown tool: {name}"
    return dispatch


# Fenced-block writer. Scans the assistant reply for ```<path>\n<body>``` where
# <path> looks like a file path (contains . or /, no spaces). Writes each into
# write_root and returns list of (rel_path, bytes_written).
_FENCED_RE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)
def _write_fenced_blocks(text, write_root_abs):
    if not write_root_abs: return []
    write_real = os.path.realpath(write_root_abs)
    written = []
    for m in _FENCED_RE.finditer(text or ""):
        tag = (m.group(1) or "").strip()
        body = m.group(2)
        if not tag or " " in tag: continue
        if "." not in tag and "/" not in tag: continue
        rel = tag.lstrip("/")
        if ".." in rel.split("/"): continue
        target = os.path.realpath(os.path.join(write_real, rel))
        if target != write_real and not target.startswith(write_real + os.sep): continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if body.endswith("\n"): body = body[:-1]
        data = body.encode("utf-8")
        with open(target, "wb") as f: f.write(data)
        written.append({"path": rel, "bytes": len(data)})
    return written


_LLM_DISPATCH = {
    ("llm",      "openai"):    "openai_chat",
    ("llm",      "anthropic"): "anthropic_chat",
    ("describe", "openai"):    "openai_chat_vision",
    ("describe", "anthropic"): "anthropic_chat_vision",
}


def _claude_cli_complete(messages, model=None, timeout=600):
    """Phase 8 — one-shot completion via the Claude CLI's --print mode.
    Used as a fallback in /__llm_run when no Anthropic API key is configured
    in media-config but the user has the `claude` binary authenticated. The
    CLI handles auth via its own session, so no API key is needed here.

    `messages` is a list of {role, content} dicts (system / user / assistant).
    System messages get joined and passed via --append-system-prompt; the rest
    are flattened into a single prompt the CLI accepts as its positional arg.

    Returns the assistant's text (rstrip newlines).

    Default timeout 600s (10 min) — the CLI is slow on long inputs (1-3 min
    typical for ~3KB prompts with max_tokens=8000 output). Below 600s and
    Blend / Refiner runs hit subprocess.TimeoutExpired."""
    bin_path = detect_agent_bin("claude")
    if not bin_path:
        raise FileNotFoundError("claude")
    system_parts = []
    convo_parts = []
    for m in (messages or []):
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content: continue
        if role == "system":
            system_parts.append(content)
        elif role in ("user", "assistant"):
            tag = "USER" if role == "user" else "ASSISTANT"
            convo_parts.append(f"[{tag}]\n{content}")
    flat = "\n\n".join(convo_parts).strip() or "Hello"
    # NOTE: don't pass --bare. It disables OAuth + keychain reads, which is
    # exactly the auth path most users have. With --bare, the CLI requires
    # ANTHROPIC_API_KEY in the env — but if the user had a key, they'd be on
    # the API-key path, not the CLI fallback. So this code path needs OAuth.
    args = [
        bin_path, "--print",
        "--output-format", "text",
        "--no-session-persistence",
        "--disable-slash-commands",   # hermetic: skip skill resolution
    ]
    if system_parts:
        args.extend(["--append-system-prompt", "\n\n".join(system_parts)])
    # Map full model IDs onto CLI aliases when possible — they accept either,
    # but the alias is more forgiving across CLI versions.
    if model:
        m = model.lower()
        if "sonnet" in m:    args.extend(["--model", "sonnet"])
        elif "opus" in m:    args.extend(["--model", "opus"])
        elif "haiku" in m:   args.extend(["--model", "haiku"])
    args.append(flat)
    # stdin=DEVNULL is mandatory: the CLI waits up to 3s for stdin (warning
    # then proceed) when invoked under `subprocess.run` because the inherited
    # stdin is a pipe. Closing it explicitly skips the warning + the wait.
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        # CLI prints helpful errors to stderr (auth failures, model unavailable, etc.)
        msg = (result.stderr or f"exit {result.returncode}").strip()[:600]
        raise RuntimeError(msg)
    return (result.stdout or "").rstrip("\n")


def _codex_cli_complete(messages, model=None, timeout=600):
    """One-shot completion via the Codex CLI's `exec` subcommand. Mirror of
    _claude_cli_complete for users who installed Codex (OpenAI's CLI) and
    signed in via `codex login` — no OPENAI_API_KEY needed.

    Codex's non-interactive surface is `codex exec [--model <m>] "<prompt>"`,
    which prints the assistant text to stdout. Older versions of codex accept
    the prompt on stdin as well; we use the positional argv form for
    compatibility.

    Returns the assistant's text (rstrip newlines)."""
    bin_path = detect_agent_bin("codex")
    if not bin_path:
        raise FileNotFoundError("codex")
    system_parts = []
    convo_parts = []
    for m in (messages or []):
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content: continue
        if role == "system":
            system_parts.append(content)
        elif role in ("user", "assistant"):
            tag = "USER" if role == "user" else "ASSISTANT"
            convo_parts.append(f"[{tag}]\n{content}")
    # Codex exec doesn't expose an explicit --append-system-prompt flag the
    # way Claude does, so fold system text into the prompt prefix.
    prompt_parts = []
    if system_parts:
        prompt_parts.append("[SYSTEM]\n" + "\n\n".join(system_parts))
    if convo_parts:
        prompt_parts.append("\n\n".join(convo_parts))
    flat = "\n\n".join(prompt_parts).strip() or "Hello"
    args = [bin_path, "exec"]
    if model:
        args.extend(["--model", model])
    args.append(flat)
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        msg = (result.stderr or f"exit {result.returncode}").strip()[:600]
        raise RuntimeError(msg)
    return (result.stdout or "").rstrip("\n")


def _codex_cli_generate_image(prompt, model, aspect, project_root, timeout=600):
    """Generate an image via the Codex CLI's built-in image-gen tool.

    Codex's agent loop ships with a `generate_image` tool that calls
    OpenAI's image API internally, authenticating via the user's
    `codex login` OAuth token — so no OPENAI_API_KEY is required. This
    helper instructs Codex to invoke that tool and write the PNG into a
    tempdir we control, then reads the bytes back.

    Why a tempdir inside project_root: Codex's default sandbox includes
    the project's working directory + writable subdirs. /tmp is sometimes
    outside its allowed-write set, depending on Codex's settings. Keeping
    the staging dir under project_root sidesteps that uncertainty.

    Args:
        prompt: user-supplied image brief
        model:  gpt-image-2 / gpt-image-1 / etc. — passed verbatim. The
                "codex-default" sentinel means "let Codex pick its own
                default" and we omit the model line from the prompt.
        aspect: "1:1" / "3:2" / etc. — passed into the prompt as a hint
        project_root: absolute path of the active project; tempdir lives
                here so Codex's sandbox can write into it
        timeout: subprocess timeout in seconds (image gen via the agent
                 loop is slow — 5+ minutes is realistic)

    Returns the PNG bytes. Raises:
      • FileNotFoundError("codex") if codex isn't on PATH
      • RuntimeError("codex stderr…") if codex exits non-zero
      • RuntimeError("no PNG produced") if codex ran but no image was saved
      • subprocess.TimeoutExpired if the timeout hits
    """
    bin_path = detect_agent_bin("codex")
    if not bin_path:
        raise FileNotFoundError("codex")
    # Stage the output in a tempdir under project_root so Codex's sandbox
    # is happy. We clean it up regardless of outcome.
    import tempfile as _tempfile, glob as _glob
    staging_root = os.path.join(project_root, ".codex-imagegen-staging")
    os.makedirs(staging_root, exist_ok=True)
    tmpdir = _tempfile.mkdtemp(prefix="codex-img-", dir=staging_root)
    out_path = os.path.join(tmpdir, "out.png")
    try:
        # Prompt: explicit, no-ambiguity instructions. The agent loop
        # tends to chat ("Here's the image…") otherwise; we want a deterministic
        # write to a known path. The "If you can't, say UNABLE" exit hatch lets
        # us catch sandbox/tool-availability failures without parsing stderr.
        model_clause = ""
        m_lower = (model or "").lower().strip()
        if m_lower and m_lower not in ("codex-default", "cli-default", "default", ""):
            model_clause = f"Use the {model} image model.\n"
        aspect_clause = f"Aspect ratio: {aspect}.\n" if aspect else ""
        codex_prompt = (
            "Generate one image and save it to disk. No commentary.\n\n"
            f"Image brief: {prompt}\n\n"
            f"{model_clause}{aspect_clause}"
            f"Write the PNG bytes to exactly this absolute path: {out_path}\n\n"
            "When done, print ONLY the path on its own line. If you cannot "
            "generate an image for any reason (tool unavailable, sandbox, "
            "policy), print 'UNABLE: <one-line reason>' and exit."
        )
        # v3.5 — Use only `codex exec` + the prompt. Earlier code added
        # --full-auto, but we don't actually know it exists on every
        # version (`codex exec --help` is the source of truth on a given
        # install). `codex exec` is non-interactive by default; if a
        # specific version blocks on approval, we'll see that in the
        # error and add the right flag here.
        args = [bin_path, "exec", codex_prompt]
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
            stdin=subprocess.DEVNULL,
        )
        # Codex may exit 0 even when the agent gave up. Check the file
        # first, regardless of exit code.
        if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
            with open(out_path, "rb") as f:
                data = f.read()
            return data
        # No file at the expected path — look for any PNG the agent might
        # have written elsewhere in the staging dir (sometimes it picks
        # a different filename despite the instructions).
        candidates = _glob.glob(os.path.join(tmpdir, "*.png"))
        for c in candidates:
            if os.path.getsize(c) > 0:
                with open(c, "rb") as f:
                    return f.read()
        # No image. Surface stderr/stdout snippets so the UI can show why.
        stderr_tail = (result.stderr or "").strip()[-500:]
        stdout_tail = (result.stdout or "").strip()[-500:]
        # If the agent printed "UNABLE: ..." that's the cleanest message.
        for line in (result.stdout or "").splitlines():
            if line.startswith("UNABLE:"):
                raise RuntimeError(f"codex image-gen unavailable: {line}")
        raise RuntimeError(
            f"codex ran but no PNG was produced. stderr: {stderr_tail!r} "
            f"stdout: {stdout_tail!r}"
        )
    finally:
        # Best-effort cleanup. Leave the staging root in place across runs;
        # this turn's tmpdir alone is removed.
        try:
            import shutil as _shutil
            _shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def _anthropic_chat(api_key, messages, model="claude-sonnet-4-6", options=None, vision=False):
    """Anthropic Messages API. Accepts the same OpenAI-style `messages` array
    we use everywhere — system messages are folded into a top-level `system`
    field (Anthropic's API doesn't accept system in the messages list), and
    user/assistant content blocks pass through. For vision, the OpenAI-style
    {type: "image_url", image_url: {url: <data-uri>}} block is rewritten to
    {type: "image", source: {type: "base64", media_type, data}}.
    """
    # Pull out system messages → top-level field. Everything else stays in `messages`.
    system_chunks = []
    msgs_out = []
    for m in messages:
        if not isinstance(m, dict): continue
        role = m.get("role")
        content = m.get("content")
        if role == "system":
            if isinstance(content, str) and content.strip():
                system_chunks.append(content)
            continue
        if role not in ("user", "assistant"): continue
        # Vision: rewrite OpenAI-style content arrays.
        if isinstance(content, list):
            blocks_out = []
            for blk in content:
                if not isinstance(blk, dict): continue
                t = blk.get("type")
                if t == "text" and isinstance(blk.get("text"), str):
                    blocks_out.append({"type": "text", "text": blk["text"]})
                elif t == "image_url":
                    url = (blk.get("image_url") or {}).get("url") or ""
                    m_match = re.match(r"^data:([^;]+);base64,(.*)$", url, re.DOTALL)
                    if not m_match:
                        # Anthropic doesn't fetch URLs server-side; reject.
                        raise RuntimeError("Anthropic vision needs a base64 data: URL, got a plain URL")
                    blocks_out.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": m_match.group(1), "data": m_match.group(2)},
                    })
            msgs_out.append({"role": role, "content": blocks_out})
        elif isinstance(content, str):
            msgs_out.append({"role": role, "content": content})
    body = {
        "model": model or "claude-sonnet-4-6",
        "max_tokens": (options or {}).get("max_tokens") or 4096,
        "messages": msgs_out,
    }
    if system_chunks: body["system"] = "\n\n".join(system_chunks)
    if isinstance(options, dict):
        for k in ("temperature", "top_p"):
            if k in options and options[k] is not None: body[k] = options[k]
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    try:
        # content is a list of blocks; concat text blocks.
        chunks = []
        for blk in data.get("content") or []:
            if isinstance(blk, dict) and blk.get("type") == "text":
                chunks.append(blk.get("text") or "")
        return "\n".join(chunks)
    except Exception:
        raise RuntimeError(f"unexpected Anthropic response shape: {list(data.keys())}")


def _slugify(label: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", label.strip().lower()).strip("-")
    return s[:40] or ""


def _qs_get(qs_or_body, key, default=None):
    """Read a single value from either a parse_qs dict (list-valued) or a
    plain dict (JSON body). Returns `default` when missing or empty."""
    if qs_or_body is None:
        return default
    v = qs_or_body.get(key, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v


def _qs_prototype(qs_or_body, default="main"):
    """Read the prototype slug from a parse_qs dict or JSON body. Prefers the
    new `prototype` key; falls back to legacy `branch` for older clients
    (workflow.json files written pre-v3.7, URLs minted by older editor
    builds). Centralised so every endpoint that scopes by prototype reads
    the same key with the same fallback semantics."""
    v = _qs_get(qs_or_body, "prototype")
    if v is None or v == "":
        v = _qs_get(qs_or_body, "branch")
    if v is None or v == "":
        return default
    return v


def resolve_project_root(qs_or_body=None, *, require_explicit=True):
    """Return absolute path to the active project's root.

    Single-project mode (TH_WORKSPACE_DIR unset): always DEFAULT_PROJECT_ROOT.
    The `project` param is silently ignored so legacy URLs keep working.

    Workspace mode: reads `project` from qs/body. By default (v3.7) every
    request MUST carry an explicit `?project=<id>` when more than one
    project exists — the route raises `ValueError` and its handler returns
    400. This makes cross-project leaks impossible: the daemon never has
    to guess which project an agent meant.

    `require_explicit=False` re-enables the legacy silent fallback to the
    first-discovered project. Reserved for a small number of UI-only read
    endpoints whose absence of `?project=` is intentional (e.g. landing-
    page polls before any project is open). Mutation endpoints + every
    endpoint reachable from a per-project subagent context must keep the
    default. Loose-fallback historic bug: musem chat curl'd /__workflow
    without ?project= and received the install's brand-landing workflow
    (27 unrelated nodes from project=changing).
    """
    if not WORKSPACE_DIR:
        return DEFAULT_PROJECT_ROOT
    proj = (_qs_get(qs_or_body, "project") or "").strip()
    if not proj:
        if require_explicit:
            projects = _list_projects()
            if len(projects) > 1:
                ids = ", ".join(p["id"] for p in projects)
                raise ValueError(
                    f"workspace mode with {len(projects)} projects "
                    f"requires explicit ?project=<id> (known: {ids})"
                )
        proj = _first_project_id() or ""
        if not proj:
            raise ValueError("workspace mode: no projects available under TH_WORKSPACE_DIR")
    if not PROJECT_ID_OK.match(proj):
        raise ValueError(f"invalid project id: {proj!r}")
    # New layout: projects live under <WORKSPACE_DIR>/projects/<id>/. Fall back
    # to the old root-level location if a project hasn't been migrated yet.
    candidate = _safe_join(PROJECTS_DIR, proj) if PROJECTS_DIR and os.path.isdir(os.path.join(PROJECTS_DIR, proj)) \
                else _safe_join(WORKSPACE_DIR, proj)
    if not os.path.isdir(os.path.join(candidate, "source")):
        raise ValueError(f"no such project (no source/ folder): {proj}")
    return candidate


def _project_paths(project_root: str) -> dict:
    """Per-project derived paths. v3.1 — branches deprecated; `merges`
    retained for legacy callers but no longer used."""
    return {
        "source_dir": os.path.join(project_root, "source"),
        "editor_dir": os.path.join(project_root, "editor"),
        "registry":   os.path.join(project_root, "editor", "data.js"),
        "merges":     os.path.join(project_root, ".archive", "MERGES.md"),
    }


def _last_activity(project_root: str):
    """Most recent mtime under source/, as ISO string."""
    latest = 0.0
    for sub in ("source",):
        p = os.path.join(project_root, sub)
        if not os.path.isdir(p):
            continue
        for root, _dirs, files in os.walk(p):
            for f in files:
                try:
                    m = os.path.getmtime(os.path.join(root, f))
                    if m > latest:
                        latest = m
                except OSError:
                    continue
    if latest == 0.0:
        return None
    return _dt.datetime.fromtimestamp(latest).isoformat(timespec="seconds")


def _project_dir_candidates(pid: str) -> list:
    """Where a given project ID might live on disk. Prefer the new
    `projects/<id>/` location; fall back to root-level for pre-migration
    installs. Returns absolute paths in priority order."""
    out = []
    if PROJECTS_DIR:
        out.append(os.path.join(PROJECTS_DIR, pid))
    if WORKSPACE_DIR:
        out.append(os.path.join(WORKSPACE_DIR, pid))
    return out


def _starred_for_project(project_root: str) -> list:
    """Read <project>/.starred-prototypes.json and resolve each id to a
    full {id, path, label, exists} entry. Module-level helper so
    _list_projects() (which is also module-level) can call it."""
    path = os.path.join(project_root, ".starred-prototypes.json")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        ids = [s for s in (data.get("starred") or []) if isinstance(s, str) and s]
    except Exception:
        return []
    if not ids:
        return []
    src_root = os.path.join(project_root, "source")
    found = {}
    if os.path.isdir(src_root):
        try:
            for name in os.listdir(src_root):
                if name.startswith("."): continue
                lvl1 = os.path.join(src_root, name)
                if not os.path.isdir(lvl1): continue
                if os.path.isfile(os.path.join(lvl1, "index.html")):
                    found[name] = {"id": name, "path": f"source/{name}/index.html", "label": name, "depth": 1}
                for sub in os.listdir(lvl1):
                    if sub.startswith(".") or sub == "index.html": continue
                    lvl2 = os.path.join(lvl1, sub)
                    if not os.path.isdir(lvl2): continue
                    if os.path.isfile(os.path.join(lvl2, "index.html")):
                        cid = f"{name}/{sub}"
                        found[cid] = {"id": cid, "path": f"source/{name}/{sub}/index.html", "label": sub, "branch": name, "depth": 2}
        except OSError:
            pass
    out = []
    for sid in ids:
        if sid in found:
            e = dict(found[sid]); e["exists"] = True; out.append(e)
        else:
            label = sid.rsplit("/", 1)[-1] or sid
            out.append({"id": sid, "path": f"source/{sid}/index.html", "label": label, "exists": False})
    return out


def _thumbnail_for_project(project_root: str) -> "dict | None":
    """Read <project>/.thumbnail-prototype.json and resolve the stored
    target to a {path, label, exists} entry. Returns None if no thumbnail
    is set. Module-level helper paralleling _starred_for_project.

    Storage shape v2: { "path": "source/<...>/file.html" }
    Storage shape v1: { "id": "<prototype-slug>" } — promoted on the fly to
    source/<slug>/index.html so older saves keep working."""
    path = os.path.join(project_root, ".thumbnail-prototype.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return None
    tp = data.get("path")
    if not (isinstance(tp, str) and tp):
        sid = data.get("id")
        if isinstance(sid, str) and sid:
            tp = f"source/{sid}/index.html"
        else:
            return None
    norm = tp.replace("\\", "/").lstrip("/")
    if not norm.startswith("source/") or not (norm.lower().endswith(".html") or norm.lower().endswith(".htm")):
        return {"path": tp, "label": tp.rsplit("/", 1)[-1] or tp, "exists": False}
    abs_path = os.path.join(project_root, norm)
    exists = os.path.isfile(abs_path)
    parts = norm.split("/")
    if parts[-1] == "index.html" and len(parts) >= 3:
        label = "/".join(parts[1:-1])
    else:
        label = parts[-1]
    return {"path": norm, "label": label, "exists": exists}


def _list_projects() -> list:
    """In workspace mode: subdirs of WORKSPACE_DIR/projects/ (or WORKSPACE_DIR
    itself as a fallback) with a source/ folder, augmented + ordered by
    workspace.json if present. In single-project mode: one virtual project
    rooted at DEFAULT_PROJECT_ROOT (id='default')."""
    if not WORKSPACE_DIR:
        return [{
            "id": "default",
            "label": os.path.basename(DEFAULT_PROJECT_ROOT) or "default",
            "path": DEFAULT_PROJECT_ROOT,
            "hasSource": os.path.isdir(os.path.join(DEFAULT_PROJECT_ROOT, "source")),
            "lastActivity": _last_activity(DEFAULT_PROJECT_ROOT),
            "starredPrototypes": _starred_for_project(DEFAULT_PROJECT_ROOT),
            "thumbnailPrototype": _thumbnail_for_project(DEFAULT_PROJECT_ROOT),
        }]
    out: list = []
    seen: set = set()
    overrides: dict = {}
    order: list = []
    ws_json = os.path.join(WORKSPACE_DIR, "workspace.json")
    if os.path.isfile(ws_json):
        try:
            with open(ws_json, "r", encoding="utf-8") as f:
                cfg = json.load(f) or {}
            for p in (cfg.get("projects") or []):
                pid = (p.get("id") or "").strip()
                if pid and PROJECT_ID_OK.match(pid):
                    overrides[pid] = (p.get("label") or pid)
                    order.append(pid)
        except Exception:
            pass

    def _resolve_dir(pid: str):
        for c in _project_dir_candidates(pid):
            if os.path.isdir(c): return c
        return None

    for pid in order:
        p = _resolve_dir(pid)
        if pid in seen or not p:
            continue
        seen.add(pid)
        out.append({
            "id": pid,
            "label": overrides.get(pid, pid),
            "path": p,
            "hasSource": os.path.isdir(os.path.join(p, "source")),
            "lastActivity": _last_activity(p),
            "starredPrototypes": _starred_for_project(p),
            "thumbnailPrototype": _thumbnail_for_project(p),
        })
    # Scan order: projects/ first (canonical), then root (legacy fallback).
    scan_dirs = []
    if PROJECTS_DIR and os.path.isdir(PROJECTS_DIR):
        scan_dirs.append(PROJECTS_DIR)
    if WORKSPACE_DIR != PROJECTS_DIR:
        scan_dirs.append(WORKSPACE_DIR)
    for base in scan_dirs:
        try:
            for name in sorted(os.listdir(base)):
                if name in seen or not PROJECT_ID_OK.match(name):
                    continue
                p = os.path.join(base, name)
                if not os.path.isdir(p):
                    continue
                if not os.path.isdir(os.path.join(p, "source")):
                    continue
                seen.add(name)
                out.append({
                    "id": name,
                    "label": name,
                    "path": p,
                    "hasSource": True,
                    "lastActivity": _last_activity(p),
                    "starredPrototypes": _starred_for_project(p),
                    "thumbnailPrototype": _thumbnail_for_project(p),
                })
        except OSError:
            pass
    return out


def _first_project_id():
    projs = _list_projects()
    return projs[0]["id"] if projs else None


# ── Per-project export folder ────────────────────────────────────────────
# Stored on each project entry in workspace.json as `exportFolder`. Used by
# the ⤓ Exports dialog (UI, mounted in the workflow toolbar) and the
# /__export_asset endpoint (daemon). In single-project mode the value lives
# on the virtual default project, also persisted to workspace.json.

def _workspace_json_path():
    base = WORKSPACE_DIR or INSTALL_ROOT
    return os.path.join(base, "workspace.json")


def _workspace_json_load():
    p = _workspace_json_path()
    if not os.path.isfile(p):
        return {"projects": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return {"projects": []}
    if not isinstance(data, dict):
        return {"projects": []}
    data.setdefault("projects", [])
    if not isinstance(data["projects"], list):
        data["projects"] = []
    return data


def _workspace_json_save(data):
    p = _workspace_json_path()
    try:
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    except OSError:
        pass
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


def _export_folder_get(pid: str) -> "str | None":
    data = _workspace_json_load()
    for entry in data.get("projects", []):
        if isinstance(entry, dict) and entry.get("id") == pid:
            v = entry.get("exportFolder")
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _export_folder_set(pid: str, folder: "str | None") -> str:
    """Persist `folder` (absolute path) on the named project entry. Pass
    None or "" to clear. Returns the normalised stored value (or empty
    string when cleared). Creates the project entry if it doesn't exist
    yet — workspace.json's projects[] is the authoritative list."""
    data = _workspace_json_load()
    projects = data.get("projects", [])
    found = None
    for entry in projects:
        if isinstance(entry, dict) and entry.get("id") == pid:
            found = entry
            break
    if found is None:
        found = {"id": pid, "label": pid}
        projects.append(found)
        data["projects"] = projects
    if folder is None or not str(folder).strip():
        found.pop("exportFolder", None)
        _workspace_json_save(data)
        return ""
    norm = os.path.expanduser(str(folder).strip())
    if not os.path.isabs(norm):
        raise ValueError(f"export folder must be an absolute path; got {folder!r}")
    found["exportFolder"] = norm
    _workspace_json_save(data)
    return norm


def _export_folder_status(folder: "str | None") -> dict:
    """Resolve usability flags for an export folder so the Settings UI can
    show actionable state (exists / writable / will be created)."""
    if not folder:
        return {"exists": False, "writable": False, "isAbsolute": False}
    norm = os.path.expanduser(folder)
    exists  = os.path.isdir(norm)
    parent  = os.path.dirname(norm) or "/"
    parent_writable = os.path.isdir(parent) and os.access(parent, os.W_OK)
    writable = (exists and os.access(norm, os.W_OK)) or (not exists and parent_writable)
    return {
        "exists":     exists,
        "writable":   writable,
        "isAbsolute": os.path.isabs(norm),
        "resolved":   norm,
    }


def _v31_migrate_data_js(project_root: str) -> bool:
    """Lazy in-place migration to the v3.1 flat shape. Returns True if any
    migration was applied this call.

    The OLD shape:
        editor/data.js                    ← EDITOR_BRANCHES + document.write
        editor/branches/main.js           ← window.EDITOR_DATA = {...}

    The NEW shape:
        editor/data.js                    ← window.EDITOR_DATA = {...} directly
        (no editor/branches/ directory needed)

    Strategy: if editor/branches/main.js exists, promote it to editor/data.js
    (overwriting). Then rename editor/branches/ → editor/.archive/branches/
    so subsequent calls are no-ops. This is the most aggressive policy and
    handles every state: old bootstrap shim, partial migrations, or already-
    flat projects with a stale branches/ dir hanging around.
    """
    editor_dir = os.path.join(project_root, "editor")
    data_js = os.path.join(editor_dir, "data.js")
    branches_dir = os.path.join(editor_dir, "branches")
    main_js = os.path.join(branches_dir, "main.js")
    if not os.path.isdir(branches_dir):
        return False
    # Decide what to do: promote main.js if it exists, otherwise just archive.
    applied = False
    if os.path.isfile(main_js):
        try:
            with open(main_js, "r", encoding="utf-8") as f:
                main_text = f.read()
        except OSError:
            main_text = None
        if main_text and "window.EDITOR_DATA" in main_text:
            tmp = data_js + ".v31-tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write("// v3.1 migrated from editor/branches/main.js\n"
                            "// (project-level branches deprecated).\n"
                            + main_text)
                os.replace(tmp, data_js)
                applied = True
            except OSError:
                try: os.remove(tmp)
                except OSError: pass
    # Ensure data.js exists in some usable form.
    if not os.path.isfile(data_js):
        try:
            with open(data_js, "w", encoding="utf-8") as f:
                f.write("// v3.1 migration: empty seed (no branches/main.js was promotable).\n"
                        "window.EDITOR_DATA = { meta: {}, frames: [], lanes: [], "
                        "arrows: [], entities: [], primitives: [], links: [] };\n")
            applied = True
        except OSError:
            pass
    # Archive the branches/ dir so this migration never fires again for
    # this project. Move to editor/.archive/branches/.
    try:
        archive_root = os.path.join(editor_dir, ".archive")
        os.makedirs(archive_root, exist_ok=True)
        archived = os.path.join(archive_root, "branches")
        if os.path.isdir(archived):
            # Already migrated once; tag the second one with a timestamp.
            import time as _t
            archived = os.path.join(archive_root, f"branches.{int(_t.time())}")
        os.rename(branches_dir, archived)
        applied = True
        print(f"[v3.1 migrate] {os.path.basename(project_root.rstrip('/'))}: "
              f"editor/branches/ → {os.path.relpath(archived, project_root)}",
              flush=True)
    except OSError as e:
        print(f"[v3.1 migrate] archive failed: {e}", flush=True)
    return applied


def _write_registry(reg: dict, project_root: str = None) -> None:
    """v3.1 — branches deprecated. The "registry" file is now just a stub
    bootstrap shim that document.write's the single editor/data.js carrying
    the project's EDITOR_DATA. Kept for backward compat so old data.js
    upgrade paths don't crash; `reg` is ignored (it described branch
    listings that no longer exist).

    The actual project data is in editor/data.js (formerly
    editor/branches/main.js), written by Workflow 1 / orchestrator / user."""
    if project_root is None:
        project_root = DEFAULT_PROJECT_ROOT
    # No-op in v3.1 — the editor/data.js file IS the project data file now,
    # not a bootstrap shim. Leave it untouched if it already exists; create
    # an empty placeholder if it doesn't (so `_load_registry` can re-read).
    registry = _project_paths(project_root)["registry"]
    if os.path.isfile(registry):
        return
    os.makedirs(os.path.dirname(registry), exist_ok=True)
    with open(registry, "w", encoding="utf-8") as f:
        f.write("// editor/data.js — project data (v3.1; branches deprecated).\n"
                "// This file carries window.EDITOR_DATA directly. Workflow 1\n"
                "// writes it after parsing source/.\n"
                "window.EDITOR_DATA = { meta: {}, frames: [], primitives: [], entities: [] };\n")


def _safe_join(base: str, *parts: str) -> str:
    """Join parts under base and refuse anything resolving outside it."""
    p = os.path.abspath(os.path.join(base, *parts))
    if os.path.commonpath([p, base]) != base:
        raise ValueError(f"refusing path outside {base}: {p}")
    return p


def _branch_source_dir(slug: str = "main", project_root: str = None) -> str:
    """v3.1 — branches deprecated. Always returns source/. The slug arg is
    kept for ABI compat; ignored."""
    if project_root is None:
        project_root = DEFAULT_PROJECT_ROOT
    return _project_paths(project_root)["source_dir"]


def _branch_data_file(slug: str = "main", project_root: str = None) -> str:
    """v3.1 — branches deprecated. Always returns editor/data.js."""
    if project_root is None:
        project_root = DEFAULT_PROJECT_ROOT
    return os.path.join(_project_paths(project_root)["editor_dir"], "data.js") \
        if "editor_dir" in _project_paths(project_root) \
        else _safe_join(project_root, "editor", "data.js")


# ── Onboarding workflow scaffold ─────────────────────────────────────────────
# Phase 2 of the onboarding orchestration plan. Given the chosen stages
# (subset of A..I), emit a workflow.json with exactly the nodes the agent
# will run, laid out left-to-right column-by-column. Layout is deterministic
# so users see the same shape every time.
#
# Position math (world coords, single column per stage):
#   x = COL_X[stage] (base for first node in the stage's column)
#   y = stacked downward within the stage
#   w/h = per-kind defaults
ONBOARDING_COL_W = 340
ONBOARDING_COL_GAP = 60
def _ob_col_x(stage_idx: int) -> int:
    return stage_idx * (ONBOARDING_COL_W + ONBOARDING_COL_GAP)

# Per-kind default sizes (world units).
# Heights here MUST fit the node's whole body — header + fields + the
# bottom action row (Run / Setup loop / Build). If a kind has its own
# renderer that uses a `Math.max(MIN_H, …)` floor, set the scaffold
# default >= that floor so newly-seeded nodes don't snap up on first
# render (which would also shift sibling node positions on the canvas).
_OB_SIZE = {
    "folder":            {"w": 280, "h": 140},
    "prompt":            {"w": 340, "h": 220},
    "skill":             {"w": 340, "h": 220},
    "agent":             {"w": 360, "h": 280},
    "ds-brainstorm":     {"w": 320, "h": 360},
    "iterator-refiner":  {"w": 420, "h": 520},
    "iterator-remix":    {"w": 360, "h": 420},
    "iterator-repeater": {"w": 360, "h": 400},
    "iterator-blend":    {"w": 380, "h": 440},
}

# v2.19 — exported scaffolder defaults that the daemon's /run gate compares
# against to detect "orchestrator hasn't customized this yet" state. Kept at
# module scope so both the scaffolder (writes them in) and _workflow_node_run
# (refuses dispatch when still equal) reference the SAME literal strings.
def _bs_html_default_text(i):
    return (f"Generate a single self-contained HTML page for the "
            f"chunk-PRD page #{i+1}. Load the wired DS tokens AND "
            f"the page's shell stylesheet from `design-systems/"
            f"<id>/shells/<shell>.css` (shell named in chunks "
            f"output). Apply BRAINSTORM_VISUAL_RULES and "
            f"CONTENT_DISCIPLINE (≤180 LOC for exploration HTMLs, "
            f"every block earns its place, no filler copy). "
            # v2.50 — Coherence Pass: canonical fixture + shared chrome.
            f"DATA: every numeric or proper-noun fact (case ids, "
            f"counts, percentages, confidence scores, operator names) "
            f"MUST be referenced from window.DEMO (which derives from "
            f"_coherence/model.json written by cp_fixture upstream). "
            f"Never author a figure inline. If a fact isn't in the "
            f"model, request it via /commit error — don't invent it. "
            f"CHROME: include the canonical chrome partial "
            f"(_coherence/chrome.html written by cp_chrome upstream) "
            f"verbatim — you may set the active nav item (aria-current) "
            f"but MUST NOT redefine the brand, nav structure, seal slot, "
            f"or nav location. The downstream Coherence Pass enforces "
            f"both rules; violations block the prototype release.")

REMIX_VARIANT_DEFAULTS = [
    "Denser + tighter spacing — more information visible at once, "
    "smaller type scale, hairline dividers, less whitespace between sections. "
    "Push toward an inspector-style read.",
    "Calmer + more generous whitespace — fewer competing focal points, "
    "larger type scale, sections breathe with 40-80px gaps, single accent. "
    "Push toward an editorial-narrative read.",
    "Asymmetric editorial — magazine-like grid with one oversized hero "
    "element, contrasting type scales for display vs body, pull-quote or "
    "decorative rule break, off-center alignment for at least one section. "
    "Push toward a print-feature read.",
]


def _ob_node(*, id, kind, col, row, title=None, **extra):
    """Build a workflow node dict. `col` is stage column index (0-based),
    `row` is the vertical slot within the column (0-based, top to bottom)."""
    size = _OB_SIZE.get(kind, {"w": 320, "h": 200})
    base = {
        "id": id,
        "kind": kind,
        "x": _ob_col_x(col),
        "y": row * (size["h"] + 40),
        "w": size["w"],
        "h": size["h"],
        "runStatus": "queued",
    }
    if title is not None:
        # Prompt + agent + skill all surface a top-line title in their UI.
        base["title"] = title
        base["name"]  = title
    base.update(extra)
    return base

def _copytree(src: str, dst: str) -> list:
    """Copy src/* → dst (creating dst). Returns relative paths copied."""
    os.makedirs(dst, exist_ok=False)
    copied = []
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
            for root, _, files in os.walk(d):
                for f in files:
                    copied.append(os.path.relpath(os.path.join(root, f), dst))
        else:
            shutil.copy2(s, d)
            copied.append(name)
    return copied


# ── Undo / redo history ──────────────────────────────────────────────────────
# Per-project ring buffer of file snapshots. Every "change" (UI write, agent
# run, workflow op) lands as one entry with a before/ and after/ snapshot of
# just the touched files. See docs/features/history-plan.md.
#
# Storage: <project_root>/.history/
#   index.json                  { entries: [...], cursor }
#   <id>/meta.json              entry metadata (same as the row in index)
#   <id>/before/<rel-path>      pre-change file contents
#   <id>/after/<rel-path>       post-change file contents
#
# A file present in `before/` but absent in `after/` means "the change created
# this file" (undo deletes it). Symmetric for delete. Tracked explicitly in
# meta.json.files[].existed_before / existed_after so we don't rely on
# directory listings.
HISTORY_MAX_ENTRIES = 20
HISTORY_MAX_FILE_BYTES = 10 * 1024 * 1024   # skip individual files larger than 10 MB
HISTORY_LOCK = threading.RLock()  # serialise multi-step index updates per process

def _history_dir(project_root: str) -> str:
    d = _safe_join(project_root, ".history")
    os.makedirs(d, exist_ok=True)
    return d

def _history_index_path(project_root: str) -> str:
    return os.path.join(_history_dir(project_root), "index.json")

def _history_load_index(project_root: str) -> dict:
    p = _history_index_path(project_root)
    if not os.path.isfile(p):
        return {"entries": [], "cursor": -1}
    try:
        with open(p, "r", encoding="utf-8") as f:
            idx = json.load(f)
        if not isinstance(idx, dict): raise ValueError("not a dict")
        if not isinstance(idx.get("entries"), list): idx["entries"] = []
        if not isinstance(idx.get("cursor"), int):   idx["cursor"] = len(idx["entries"]) - 1
        return idx
    except Exception:
        # Corrupt index → start fresh but DON'T delete the entry dirs; the user
        # might want to recover them manually.
        return {"entries": [], "cursor": -1}

def _history_save_index(project_root: str, idx: dict) -> None:
    p = _history_index_path(project_root)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, sort_keys=True)
    os.replace(tmp, p)

def _history_new_id() -> str:
    # ULID-ish: timestamp-prefix + random hex. Sortable, unique enough.
    ts = int(time.time() * 1000)
    return f"{ts:013x}{uuid.uuid4().hex[:10]}"

def _history_capture_file(project_root: str, rel_path: str, dest_dir: str) -> dict:
    """Copy <project_root>/<rel_path> → <dest_dir>/<rel_path> if it exists and
    is under the size cap. Returns a row for meta.json.files: {path, existed,
    size, skipped?}.
    """
    abs_src = _safe_join(project_root, rel_path)
    row = {"path": rel_path, "existed": False, "size": 0}
    if not os.path.isfile(abs_src):
        return row
    row["existed"] = True
    try:
        size = os.path.getsize(abs_src)
    except OSError:
        return row
    row["size"] = size
    if size > HISTORY_MAX_FILE_BYTES:
        row["skipped"] = "size"
        return row
    abs_dst = os.path.join(dest_dir, rel_path)
    os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
    shutil.copy2(abs_src, abs_dst)
    return row

def _history_capture_paths(project_root: str, rel_paths, dest_dir: str) -> list:
    """Capture a set of paths into dest_dir. Returns list of file rows."""
    rows = []
    seen = set()
    for rel in rel_paths:
        rel = rel.replace("\\", "/").lstrip("/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        # Guard the join so a malicious path can't escape — _history_capture_file
        # calls _safe_join internally, so we let the ValueError propagate.
        rows.append(_history_capture_file(project_root, rel, dest_dir))
    return rows

def _history_prune_entry(project_root: str, entry: dict) -> None:
    """Delete the on-disk directory for one entry. Safe if it's missing."""
    eid = entry.get("id")
    if not eid:
        return
    try:
        d = _safe_join(_history_dir(project_root), eid)
    except ValueError:
        return
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)

def _history_record(project_root: str, *, kind: str, label: str, source: str,
                    before_paths, after_paths, extra=None) -> dict:
    """Append a new history entry. before_paths / after_paths are iterables of
    rel paths to capture; usually they're the same set (the union of files
    touched by the change). Returns the entry dict.

    On append:
      - If cursor < latest, the redo tail is dropped (pruned from disk + index).
      - If the resulting stack exceeds HISTORY_MAX_ENTRIES, the oldest entry
        is dropped.
    """
    with HISTORY_LOCK:
        idx = _history_load_index(project_root)
        # Drop the redo tail.
        if idx["cursor"] < len(idx["entries"]) - 1:
            for stale in idx["entries"][idx["cursor"] + 1:]:
                _history_prune_entry(project_root, stale)
            idx["entries"] = idx["entries"][:idx["cursor"] + 1]
        eid = _history_new_id()
        edir = _safe_join(_history_dir(project_root), eid)
        bdir = os.path.join(edir, "before")
        adir = os.path.join(edir, "after")
        os.makedirs(bdir, exist_ok=True)
        os.makedirs(adir, exist_ok=True)
        before_rows = _history_capture_paths(project_root, before_paths, bdir)
        after_rows  = _history_capture_paths(project_root, after_paths, adir)
        # If neither side captured anything, drop the entry — empty events
        # would clutter the stack.
        any_touched = any(r["existed"] for r in before_rows + after_rows)
        if not any_touched:
            shutil.rmtree(edir, ignore_errors=True)
            return None
        entry = {
            "id": eid,
            "kind": kind,
            "label": label,
            "source": source,
            "timestamp": time.time(),
            "before": before_rows,
            "after": after_rows,
        }
        if extra:
            entry.update(extra)
        # Write per-entry meta first (so a crash before index save doesn't
        # orphan the entry's files invisibly).
        with open(os.path.join(edir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, sort_keys=True)
        idx["entries"].append(entry)
        idx["cursor"] = len(idx["entries"]) - 1
        # Ring-buffer prune: drop oldest until <= MAX.
        while len(idx["entries"]) > HISTORY_MAX_ENTRIES:
            old = idx["entries"].pop(0)
            _history_prune_entry(project_root, old)
            idx["cursor"] -= 1
        _history_save_index(project_root, idx)
        return entry

def _history_restore(project_root: str, entry: dict, direction: str) -> list:
    """Restore the entry's `before/` (direction='before') or `after/`
    (direction='after') snapshot onto disk. Returns the list of rel paths
    that changed (created, overwritten, or deleted).

    Files captured as `existed=False` are deleted on restore — that's the
    inverse of "the change created this file."
    """
    if direction not in ("before", "after"):
        raise ValueError(f"bad direction: {direction!r}")
    rows = entry.get(direction) or []
    snapshot_dir = _safe_join(_history_dir(project_root), entry["id"], direction)
    changed = []
    for row in rows:
        rel = row["path"]
        abs_dst = _safe_join(project_root, rel)
        if row.get("skipped"):
            # Couldn't capture this file's bytes — leave it alone but report
            # it so the UI can surface the warning.
            continue
        if row.get("existed"):
            src = os.path.join(snapshot_dir, rel)
            if not os.path.isfile(src):
                # Snapshot file missing from disk (manual deletion?). Skip.
                continue
            os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
            shutil.copy2(src, abs_dst)
            changed.append(rel)
        else:
            # File did not exist at this snapshot point → delete current copy.
            if os.path.isfile(abs_dst):
                try: os.remove(abs_dst)
                except OSError: pass
                changed.append(rel)
    return changed

# Branch-data writes (and a handful of other endpoints) follow the same
# capture-before, write, capture-after pattern. This wrapper makes the
# bracket explicit at the call site.
def _history_bracket(project_root: str, rel_paths, *, kind: str, label: str,
                     source: str = "editor", extra=None):
    """Context-manager-ish helper. Usage:

        with _history_bracket(root, ["edits.json"], kind="ui-edit",
                              label="Save edits.json") as bracket:
            <perform the write>
        # bracket auto-records the entry on exit if any file changed.

    Implementation note: this is a tiny ad-hoc class rather than a contextmanager
    so the bracket can swallow exceptions in the recorder without masking the
    caller's exception path.
    """
    class _Bracket:
        def __enter__(self_inner):
            self_inner.paths = [p.replace("\\", "/").lstrip("/") for p in rel_paths]
            self_inner.before_dir = None
            # Capture the BEFORE state into a temporary staging dir. We move it
            # into the final entry dir on __exit__ only if a change actually
            # happened. This avoids leaving orphan .history entries for no-ops.
            tmp = _safe_join(_history_dir(project_root), ".staging-" + _history_new_id())
            os.makedirs(tmp, exist_ok=True)
            self_inner.before_dir = tmp
            self_inner.before_rows = _history_capture_paths(project_root,
                                                            self_inner.paths, tmp)
            return self_inner
        def __exit__(self_inner, exc_type, exc, tb):
            try:
                if exc_type is not None:
                    # Caller's write failed; nothing to record. Clean up staging.
                    shutil.rmtree(self_inner.before_dir, ignore_errors=True)
                    return False
                # Capture AFTER, then commit the entry.
                with HISTORY_LOCK:
                    idx = _history_load_index(project_root)
                    if idx["cursor"] < len(idx["entries"]) - 1:
                        for stale in idx["entries"][idx["cursor"] + 1:]:
                            _history_prune_entry(project_root, stale)
                        idx["entries"] = idx["entries"][:idx["cursor"] + 1]
                    eid = _history_new_id()
                    edir = _safe_join(_history_dir(project_root), eid)
                    os.makedirs(edir, exist_ok=True)
                    # Move staging → entry/before.
                    final_before = os.path.join(edir, "before")
                    shutil.move(self_inner.before_dir, final_before)
                    self_inner.before_dir = None
                    adir = os.path.join(edir, "after")
                    os.makedirs(adir, exist_ok=True)
                    after_rows = _history_capture_paths(project_root,
                                                        self_inner.paths, adir)
                    # No-op detection: same existed flag and same size on every
                    # path → drop the entry, nothing actually changed.
                    pre_map  = {r["path"]: (r["existed"], r["size"]) for r in self_inner.before_rows}
                    post_map = {r["path"]: (r["existed"], r["size"]) for r in after_rows}
                    if pre_map == post_map and not _history_size_diff_real(final_before, adir, self_inner.paths):
                        shutil.rmtree(edir, ignore_errors=True)
                        return False
                    entry = {
                        "id": eid,
                        "kind": kind,
                        "label": label,
                        "source": source,
                        "timestamp": time.time(),
                        "before": self_inner.before_rows,
                        "after": after_rows,
                    }
                    if extra: entry.update(extra)
                    with open(os.path.join(edir, "meta.json"), "w", encoding="utf-8") as f:
                        json.dump(entry, f, indent=2, sort_keys=True)
                    idx["entries"].append(entry)
                    idx["cursor"] = len(idx["entries"]) - 1
                    while len(idx["entries"]) > HISTORY_MAX_ENTRIES:
                        old = idx["entries"].pop(0)
                        _history_prune_entry(project_root, old)
                        idx["cursor"] -= 1
                    _history_save_index(project_root, idx)
            finally:
                if self_inner.before_dir and os.path.isdir(self_inner.before_dir):
                    shutil.rmtree(self_inner.before_dir, ignore_errors=True)
            return False
    return _Bracket()

def _history_scope_bracket(project_root: str, dirs, root_files=(), *,
                           kind: str, label: str, source: str, extra=None):
    """Context manager for multi-file ops where the changed-file set isn't
    known until the write completes. Walks `dirs` + `root_files`, snapshots
    before the wrapped block, snapshots+diffs after, and commits one entry
    covering everything that changed.

    Use this for endpoints like /__replace_exposed_svg or /__rewrite_img_src
    that scan many HTML files. Single-file writes use _history_bracket
    instead — it's lighter (no directory walk).
    """
    class _ScopeBracket:
        def __enter__(self_inner):
            self_inner.scope_walker = lambda r: _history_walk_scope(r, dirs, root_files)
            self_inner.paths = self_inner.scope_walker(project_root)
            try:
                self_inner.eid = _history_new_id()
                edir = _safe_join(_history_dir(project_root), self_inner.eid)
                os.makedirs(edir, exist_ok=True)
                bdir = os.path.join(edir, "before")
                os.makedirs(bdir, exist_ok=True)
                self_inner.rows = _history_capture_paths(project_root, self_inner.paths, bdir)
            except Exception:
                self_inner.eid = None
                self_inner.rows = []
            return self_inner
        def __exit__(self_inner, exc_type, exc, tb):
            if not self_inner.eid:
                return False
            if exc_type is not None:
                # Caller's write failed; drop staging.
                try:
                    shutil.rmtree(_safe_join(_history_dir(project_root), self_inner.eid),
                                  ignore_errors=True)
                except Exception:
                    pass
                return False
            try:
                _history_run_snapshot_finish(
                    project_root, self_inner.eid,
                    self_inner.paths, self_inner.rows,
                    kind=kind, label=label, source=source, extra=extra,
                    scope_walker=self_inner.scope_walker,
                )
            except Exception:
                pass
            return False
    return _ScopeBracket()


# ── Agent-run snapshots ──────────────────────────────────────────────────────
# At /__run spawn we take a before-snapshot of the bounded scope. At run finish
# we take an after-snapshot, diff it, and commit one entry covering ALL files
# the run touched. The scope is hardcoded — anything written outside it is
# invisible to undo. Documented in docs/features/history-plan.md §"Agent-run
# scope" so users know the contract.
HISTORY_AGENT_SCOPE_DIRS = [
    "source",
    "editor/branches",
    "editor/design-systems",
    "design-systems",
    "workflow",
]
HISTORY_AGENT_SCOPE_ROOT_FILES = {
    # v3.1 — MERGES.md / FORK_REQUEST.md dropped with project-level branches.
    "NOTES.md", "DESIGN.md",
    "DS_PROPOSAL.md", "DS_DEFERRED.md", "DS_ACCEPTED.json",
    "edits.json", "UPDATE_SOURCE.txt",
    "STATEMACHINE_REQUEST.md", "TIMELINE_REQUEST.md", "GRID_REQUEST.md",
}
# Subdir names skipped during scope enumeration. _attachments/ holds user
# uploads (some are huge); .history/ is our own storage; the rest are obvious.
HISTORY_AGENT_SKIP_DIR_NAMES = {".history", "__pycache__", "_attachments", ".trash", "node_modules", ".git"}

def _history_walk_scope(project_root: str, dirs, root_files=()) -> list:
    """Walk a set of subdirs recursively + optional root files. Returns
    sorted rel paths (forward-slash) that exist on disk.
    """
    out = []
    for sub in dirs:
        try:
            abs_sub = _safe_join(project_root, sub)
        except ValueError:
            continue
        if not os.path.isdir(abs_sub):
            continue
        for r, d, files in os.walk(abs_sub):
            d[:] = [x for x in d if x not in HISTORY_AGENT_SKIP_DIR_NAMES]
            for f in files:
                rel = os.path.relpath(os.path.join(r, f), project_root)
                out.append(rel.replace("\\", "/"))
    for name in root_files:
        try:
            abs_p = _safe_join(project_root, name)
        except ValueError:
            continue
        if os.path.isfile(abs_p):
            out.append(name)
    return sorted(set(out))

def _history_agent_scope_paths(project_root: str) -> list:
    """Bounded scope for agent runs. Documented in history-plan.md."""
    return _history_walk_scope(project_root,
                               HISTORY_AGENT_SCOPE_DIRS,
                               HISTORY_AGENT_SCOPE_ROOT_FILES)

def _history_run_snapshot_before(project_root: str):
    """Snapshot the bounded scope to .history/<id>/before/. Returns the
    pending entry id + the captured rows (for diffing on finish).
    Idempotent: if the snapshot fails partway (disk full, permission), the
    partial entry dir is cleaned up and the spawn proceeds without history.
    """
    eid = _history_new_id()
    try:
        edir = _safe_join(_history_dir(project_root), eid)
        os.makedirs(edir, exist_ok=True)
        bdir = os.path.join(edir, "before")
        os.makedirs(bdir, exist_ok=True)
        paths = _history_agent_scope_paths(project_root)
        rows = _history_capture_paths(project_root, paths, bdir)
        return eid, paths, rows, edir
    except Exception:
        # Best-effort cleanup; never let history failure block a run.
        try:
            shutil.rmtree(_safe_join(_history_dir(project_root), eid), ignore_errors=True)
        except Exception:
            pass
        return None, [], [], None

def _history_run_snapshot_finish(project_root: str, eid: str, before_paths: list,
                                 before_rows: list, *, kind: str, label: str,
                                 source: str, extra=None, scope_walker=None):
    """Take after-snapshot, diff against before, commit the entry. Drops the
    entry entirely if no files changed (avoids cluttering the stack with
    no-op runs like pure-chat freeform turns). Returns the committed entry
    or None.

    `scope_walker` is a callable `project_root -> [rel_paths]` used at finish
    time to find newly-created files. Defaults to the agent-run scope.
    Scoped brackets pass their narrower walker so we don't accidentally
    scan files outside the bracket's intent.
    """
    if scope_walker is None:
        scope_walker = _history_agent_scope_paths
    try:
        edir = _safe_join(_history_dir(project_root), eid)
    except ValueError:
        return None
    if not os.path.isdir(edir):
        return None
    bdir = os.path.join(edir, "before")
    adir = os.path.join(edir, "after")
    os.makedirs(adir, exist_ok=True)
    # The agent may have CREATED files we didn't enumerate at start — union
    # the current scope with our pre-existing path set so creations show up.
    after_paths = sorted(set(scope_walker(project_root)) | set(before_paths))
    after_rows  = _history_capture_paths(project_root, after_paths, adir)

    before_by_path = {r["path"]: r for r in before_rows}
    after_by_path  = {r["path"]: r for r in after_rows}
    changed = set()
    for p in after_paths:
        b = before_by_path.get(p, {"existed": False, "size": 0})
        a = after_by_path.get(p,  {"existed": False, "size": 0})
        if b.get("existed") != a.get("existed"):
            changed.add(p); continue
        if not a.get("existed"):
            continue
        # Both sides exist — content compare via the snapshot copies. Cheaper
        # than rehashing the original files (we just wrote those copies, so
        # they're in OS page cache).
        bp = os.path.join(bdir, p); ap = os.path.join(adir, p)
        if not os.path.isfile(bp) or not os.path.isfile(ap):
            # Either snapshot is missing — assume the file changed (safe default).
            changed.add(p); continue
        try:
            with open(bp, "rb") as f1, open(ap, "rb") as f2:
                if hashlib.sha1(f1.read()).digest() != hashlib.sha1(f2.read()).digest():
                    changed.add(p)
        except OSError:
            changed.add(p)

    if not changed:
        # No file changes — drop the entry directory entirely.
        shutil.rmtree(edir, ignore_errors=True)
        return None

    # Prune unchanged file copies from before/ and after/ to save disk.
    for p in (set(before_paths) | set(after_paths)) - changed:
        for sub in (bdir, adir):
            ap_full = os.path.join(sub, p)
            if os.path.isfile(ap_full):
                try: os.remove(ap_full)
                except OSError: pass
            # Best-effort: prune now-empty parent dirs.
            d = os.path.dirname(ap_full)
            try:
                while d.startswith(sub) and d != sub and not os.listdir(d):
                    os.rmdir(d); d = os.path.dirname(d)
            except OSError:
                pass

    # Every changed path needs a row in BOTH before_kept and after_kept so
    # _history_restore can tell "delete this file on undo" (existed=False)
    # from "leave it alone" (no row at all). Pad with phantom rows where the
    # path didn't exist at that snapshot point.
    before_by_path = {r["path"]: r for r in before_rows}
    after_by_path  = {r["path"]: r for r in after_rows}
    before_kept, after_kept = [], []
    for p in sorted(changed):
        before_kept.append(before_by_path.get(p, {"path": p, "existed": False, "size": 0}))
        after_kept .append(after_by_path .get(p, {"path": p, "existed": False, "size": 0}))

    with HISTORY_LOCK:
        idx = _history_load_index(project_root)
        if idx["cursor"] < len(idx["entries"]) - 1:
            for stale in idx["entries"][idx["cursor"] + 1:]:
                _history_prune_entry(project_root, stale)
            idx["entries"] = idx["entries"][:idx["cursor"] + 1]
        entry = {
            "id": eid,
            "kind": kind,
            "label": label,
            "source": source,
            "timestamp": time.time(),
            "before": before_kept,
            "after": after_kept,
        }
        if extra: entry.update(extra)
        with open(os.path.join(edir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, sort_keys=True)
        idx["entries"].append(entry)
        idx["cursor"] = len(idx["entries"]) - 1
        while len(idx["entries"]) > HISTORY_MAX_ENTRIES:
            old = idx["entries"].pop(0)
            _history_prune_entry(project_root, old)
            idx["cursor"] -= 1
        _history_save_index(project_root, idx)
    return entry


def _history_size_diff_real(before_dir: str, after_dir: str, rel_paths) -> bool:
    """Same-size files can still differ in content. Hash-compare to be sure
    we don't drop a real edit as a no-op.
    """
    for rel in rel_paths:
        b = os.path.join(before_dir, rel)
        a = os.path.join(after_dir, rel)
        if os.path.isfile(b) != os.path.isfile(a):
            return True
        if not os.path.isfile(b):
            continue
        with open(b, "rb") as f1, open(a, "rb") as f2:
            if hashlib.sha1(f1.read()).digest() != hashlib.sha1(f2.read()).digest():
                return True
    return False


# ── React-fiber poke helpers ─────────────────────────────────────────────────
# Injected into every source/*.html response so per-frame `setupScript` can
# flip a useState branch with a single call instead of hand-rolling fiber
# walks. See AGENTS.md → Step 5b (useState render-branch enumeration).
#
#   window.__poke(componentName, hookIndex, value)
#     Walks the React tree for a fiber whose component function is named
#     `componentName` (matched against `displayName` then `.name`), gets the
#     Nth state hook on that fiber (counting only hooks with `queue.dispatch`,
#     so useEffect/useRef/useMemo etc. don't shift the index), and calls the
#     setter with `value`. Fire-and-forget; retries up to ~1s on rAF if the
#     fiber tree hasn't committed yet (React 18 defers the first commit past
#     the iframe load event).
#
#   window.__pokeBy(componentName, stateName, value)
#     Same, but maps `stateName` → hookIndex by regex-parsing the component's
#     source for `const [stateName, setStateName] = useState(...)` decls in
#     declaration order. Naming convention required; falls back silently if
#     the destructuring style doesn't match.
POKE_HELPER = r"""
(function(){
  if (window.__poke) return;
  // Resolve the *live committed* HostRoot fiber across React 16/17/18 + variants:
  //   • Legacy ReactDOM.render: container._reactRootContainer is a ReactRoot
  //     wrapper whose ._internalRoot.current is the HostRoot fiber.
  //   • React 17 / 18 createRoot: container[__reactContainer$<id>] holds the
  //     FiberRootNode directly — .current is the HostRoot fiber.
  //   • Some builds / older snapshots: the container slot IS already a fiber
  //     (HostRoot). We must NOT return it directly — React double-buffers
  //     fibers, FiberRootNode.current flips on each commit, and the slot is
  //     pinned at mount time. If the page re-rendered (mount-time useEffect,
  //     drawer setup, etc.), the cached slot is now the STALE alternate whose
  //     .child chain isn't wired. The fix: hop through slot.stateNode.current
  //     so we always read the live committed fiber. Symptom of getting this
  //     wrong: __pokeBy works for some modals (no post-mount rerender) and
  //     silently no-ops for others (post-mount rerender flipped the buffer).
  // Uses getOwnPropertyNames so non-enumerable internal keys are still found
  // (older `for (var k in el)` could miss them on some builds).
  function rootFromContainer(el){
    if (!el) return null;
    var names;
    try { names = Object.getOwnPropertyNames(el); } catch (e) { names = []; }
    // for-in also picks up enumerable keys not on getOwnPropertyNames in some
    // edge browsers; merge both into a unique list.
    for (var kk in el) if (names.indexOf(kk) < 0) names.push(kk);
    for (var i = 0; i < names.length; i++) {
      var k = names[i];
      if (k.indexOf('__reactContainer$') !== 0 && k !== '_reactRootContainer') continue;
      var v = el[k];
      if (!v) continue;
      // Most common shape — FiberRootNode with .current → live HostRoot fiber.
      if (v.current && typeof v.current === 'object' && v.current.tag != null) return v.current;
      // Legacy ReactRoot wrapper.
      if (v._internalRoot && v._internalRoot.current) return v._internalRoot.current;
      // Slot is itself a HostRoot fiber — hop through stateNode (the
      // FiberRootNode) to read the live committed fiber rather than the
      // stale alternate this slot was pinned to at mount time.
      if (v.tag != null && v.stateNode && v.stateNode.current && v.stateNode.current.tag != null) {
        return v.stateNode.current;
      }
      // Defensive fallback — slot is a fiber but no FiberRootNode to deref.
      // Last resort; likely stale, but better than returning null.
      if (v.tag != null && v.stateNode !== undefined) return v;
    }
    return null;
  }
  function getRootFiber(){
    var el = document.getElementById('root');
    var r = rootFromContainer(el);
    if (r) return r;
    function scan(n){
      if (!n) return null;
      r = rootFromContainer(n);
      if (r) return r;
      var c = n.children || [];
      for (var i = 0; i < c.length; i++) { var rr = scan(c[i]); if (rr) return rr; }
      return null;
    }
    return scan(document.body || document.documentElement);
  }
  function findFiber(name){
    var root = getRootFiber();
    if (!root) return null;
    var stack = [root];
    while (stack.length) {
      var f = stack.shift();
      if (!f) continue;
      var T = f.type || f.elementType;
      if (typeof T === 'function' && (T.displayName === name || T.name === name)) return f;
      if (f.child)   stack.push(f.child);
      if (f.sibling) stack.push(f.sibling);
    }
    return null;
  }
  function stateHooks(fiber){
    var out = [], h = fiber.memoizedState;
    while (h) { if (h.queue && typeof h.queue.dispatch === 'function') out.push(h); h = h.next; }
    return out;
  }
  function nameToIdx(fiber, stateName){
    var src = String(fiber.type || fiber.elementType);
    var re = /const\s*\[\s*([A-Za-z_$][\w$]*)\s*,\s*set[A-Za-z_$][\w$]*\s*\]\s*=\s*(?:React\s*\.\s*)?useState\b/g;
    var m, i = 0;
    while ((m = re.exec(src))) { if (m[1] === stateName) return i; i++; }
    return -1;
  }
  // Retry budget — was 60 (≈1s at 60fps). Bumped to 180 (≈3s) so prototypes
  // that mount slowly (large CDN modules, throttled background iframes, slow
  // first paint) still resolve before we give up. The retry is rAF-driven so
  // it costs effectively nothing while React is still mounting.
  var POKE_RETRY_BUDGET = 180;
  function tryPoke(name, idx, value, attempts){
    var fiber = findFiber(name);
    if (fiber) {
      var hooks = stateHooks(fiber);
      var h = hooks[idx];
      if (h) { h.queue.dispatch(value); return true; }
    }
    if (attempts < POKE_RETRY_BUDGET) requestAnimationFrame(function(){ tryPoke(name, idx, value, attempts + 1); });
    return false;
  }
  window.__poke = function(name, idx, value){ return tryPoke(name, idx, value, 0); };
  window.__pokeBy = function(name, stateName, value){
    function tryByName(attempts){
      var fiber = findFiber(name);
      if (fiber) {
        var idx = nameToIdx(fiber, stateName);
        if (idx >= 0) return tryPoke(name, idx, value, 0);
      }
      if (attempts < POKE_RETRY_BUDGET) requestAnimationFrame(function(){ tryByName(attempts + 1); });
      return false;
    }
    return tryByName(0);
  };
})();
""".strip()


# ── Agent daemon (Phase 1 of OPEN_DESIGN_MIGRATION_PLAN) ─────────────────────
# Spawns Claude Code / Codex as a child process, normalises their stream-json
# output into a unified event list, exposes the list as Server-Sent Events.
# Two CLIs only on day one; both speak Claude's stream-json shape (Codex matches
# closely). Adding more CLIs = adding more entries to AGENT_DEFS + a normaliser
# branch in _normalize_frame. No daemon refactor needed.
#
# Adapted patterns from nexu-io/open-design (Apache 2.0):
#   apps/daemon/src/runtimes/executables.ts → detect_agent_bin
#   apps/daemon/src/runtimes/defs/claude.ts → AGENT_DEFS["claude"]
#   apps/daemon/src/json-event-stream.ts    → _normalize_claude_frame
#   apps/daemon/src/claude-stream.ts        → _drain_stdout's frame loop

AGENT_BIN_ENV = {"claude": "CLAUDE_BIN", "codex": "CODEX_BIN"}

# Permission mode for spawned agents. In non-interactive (-p / stream-json) mode
# Claude Code can't show its tool-permission prompt — without a mode set, every
# tool call silently auto-denies. The harness runs on 127.0.0.1 and only spawns
# on user click, so bypassPermissions matches the migration plan's "execution
# starts immediately" semantics. Users who want a tighter policy can override
# per-run via the /__run body (`permissionMode`) or globally via TH_PERMISSION_MODE.
#
# Choices (Claude Code 2.1): acceptEdits | auto | bypassPermissions | default | dontAsk | plan
AGENT_PERMISSION_MODE_DEFAULT = os.environ.get("TH_PERMISSION_MODE") or "bypassPermissions"

AGENT_DEFS = {
    "claude": {
        "bin": "claude",
        # Base args. Permission flag is appended at spawn-time so per-run
        # overrides work without rebuilding this list.
        #
        # AskUserQuestion is disallowed because in `-p --input-format
        # stream-json` mode there's no TTY for it to bind to. Claude Code
        # auto-completes the call as "dismissed" within a beat, which races
        # the user's click on our React answer card — the agent moves on and
        # narrates "Looks like the question prompt was dismissed…" before the
        # tool_result POST can land. With the tool disallowed the agent has to
        # phrase questions as plain text, which the composer handles naturally.
        "args": [
            "-p",
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--verbose",
            "--disallowedTools", "AskUserQuestion",
        ],
        "permission_flag": "--permission-mode",
        "permission_default": AGENT_PERMISSION_MODE_DEFAULT,
        "prompt_via_stdin": True,
        "stdin_format": "stream-json",   # newline-delimited JSON frames
    },
    "codex": {
        "bin": "codex",
        # v3.5 — Empirical flag surface for Codex CLI v0.138+:
        #   • exec: non-interactive run
        #   • --sandbox danger-full-access: required for two reasons.
        #       (1) Writes to project cwd. (`workspace-write` also enables
        #           this and is preferable for file safety.)
        #       (2) Outbound network to localhost so the agent can dispatch
        #           planners via curl POST to /__dispatch_planner.
        #           `workspace-write` BLOCKS outbound network, which broke
        #           the planner dispatch architecture from codex chats —
        #           the curl just got refused at the sandbox layer, never
        #           reached the daemon.
        #     If codex grows a finer-grained option (e.g. a sandbox config
        #     that allows network in workspace-write mode, or a separate
        #     --allow-network flag) we should switch back to the
        #     write-restricted variant. For now `danger-full-access` is
        #     the only mode I've confirmed lets codex talk to localhost.
        # Codex eats the prompt as the trailing positional argv, NOT as a
        # stream-json frame on stdin (prompt_via_stdin=False below).
        # Codex's output goes to STDERR with a structured but plain-text
        # protocol (banner / user / codex / exec / succeeded markers) —
        # _drain_stderr_codex parses it into proper agent events.
        "args": ["exec", "--sandbox", "danger-full-access"],
        "permission_flag": None,
        "permission_default": None,
        "prompt_via_stdin": False,
        "stdin_format": "argv",
    },
}

# Default agent for run-time fall-backs (chat composer with no explicit pick).
AGENT_DEFAULT = "claude"

# In-memory run registry. Runs are ephemeral; if the daemon dies the user
# re-issues. No SQLite. Map run_id → RunState.
RUNS: dict = {}
RUNS_LOCK = threading.Lock()

# v2.30 — workflow-event SSE channel. Per-project waiter set the daemon
# signals whenever workflow.json mutates (POST /__workflow, POST /__workflow/
# node/<id>/status, completion hook). Replaces v2.22's 5s client-side polling
# with event-driven push. Subscribers receive a `workflow-changed` event +
# fetch + merge — no periodic ticking.
#
# v2.50 — waiters now carry a per-event queue so the daemon can multiplex
# multiple SSE event types (workflow-changed, asset-changed) on the same
# subscription. Each event carries optional JSON data. See Deliverable 1
# of WORKFLOW_TRUTHFULNESS_PLAN.md.
class WorkflowWaiter:
    """Per-SSE-connection waiter. Holds a wake signal and an ordered queue
    of pending events to send. Broadcasters call .push(event_type, data);
    the SSE handler calls .wait() then .drain() to flush events to the
    client. Thread-safe."""
    __slots__ = ("_signal", "_pending", "_lock")

    def __init__(self):
        self._signal = threading.Event()
        self._pending = []                  # list of (event_type, data_dict)
        self._lock = threading.Lock()

    def push(self, event_type: str, data) -> None:
        with self._lock:
            self._pending.append((event_type, data))
        self._signal.set()

    def wait(self, timeout: float = 25.0) -> bool:
        fired = self._signal.wait(timeout=timeout)
        if fired:
            self._signal.clear()
        return fired

    def drain(self):
        with self._lock:
            out = self._pending[:]
            self._pending.clear()
            return out


WORKFLOW_WAITERS: dict = {}        # {project_id: set[WorkflowWaiter]}
WORKFLOW_WAITERS_LOCK = threading.Lock()

def _broadcast_workflow_change(project_id: str) -> None:
    """Notify all SSE subscribers for this project that workflow.json mutated.
    Triggers a client-side fetch + merge."""
    if not project_id: return
    with WORKFLOW_WAITERS_LOCK:
        waiters = list(WORKFLOW_WAITERS.get(project_id) or [])
    for w in waiters:
        try: w.push("workflow-changed", {})
        except Exception: pass

def _broadcast_asset_change(project_id: str, paths) -> None:
    """v2.50 — notify SSE subscribers that source/<branch>/** or
    design-systems/** files changed on disk. Frontend dispatches
    th:asset-refresh with the paths; affected asset/iframe cards refresh
    themselves. Catches writes that bypass /commit (chat agents, manual
    edits, external producers).

    `paths` is a list of project-relative paths."""
    if not project_id or not paths: return
    # Dedupe + sort for stable client-side diffing.
    paths = sorted(set(p for p in paths if isinstance(p, str) and p))
    if not paths: return
    with WORKFLOW_WAITERS_LOCK:
        waiters = list(WORKFLOW_WAITERS.get(project_id) or [])
    for w in waiters:
        try: w.push("asset-changed", {"paths": paths})
        except Exception: pass


# v2.50 — File-system watcher (polling, no external `watchdog` dependency).
# Scans `source/<branch>/**` and `design-systems/**` for every known project
# at FILE_WATCHER_INTERVAL_SEC. When files change (mtime moved, new file,
# deletion), broadcasts an `asset-changed` SSE event with the project-relative
# paths. Catches writes that bypass /commit — chat agents, manual file edits,
# orchestrator drops — so the canvas auto-refreshes without manual reload.
# See WORKFLOW_TRUTHFULNESS_PLAN.md Deliverable 1 / Principle 10.
FILE_WATCHER_INTERVAL_SEC = 1.0
FILE_WATCHER_DEBOUNCE_SEC = 0.25
FILE_WATCHER_THREAD = None
FILE_WATCHER_THREAD_LOCK = threading.Lock()
FILE_WATCHER_STATE: dict = {}      # {project_id: {rel_path: mtime}}
FILE_WATCHER_PENDING: dict = {}    # {project_id: {rel_path: detected_at}}
FILE_WATCHER_LOCK = threading.Lock()
# Skip these directory names entirely (case-sensitive). Hidden dirs and
# *_staging dirs (in-flight writes — see /commit atomic rename) never
# trigger asset-refresh: the canvas only cares about settled state.
_FILE_WATCHER_SKIP_DIRNAMES = {
    "__pycache__", "node_modules", ".history", ".git",
}

def _file_watcher_should_skip_dir(name: str) -> bool:
    if not name: return True
    if name.startswith("."): return True
    if name.endswith("_staging"): return True
    if name in _FILE_WATCHER_SKIP_DIRNAMES: return True
    return False

def _file_watcher_should_skip_file(name: str) -> bool:
    if not name: return True
    if name.startswith("."): return True
    # Editor scratchpads / OS junk
    if name.endswith("~") or name.endswith(".swp"): return True
    if name == ".DS_Store": return True
    return False

def _file_watcher_scan_one(project_root: str) -> dict:
    """Walk source/, design-systems/, AND workflow/ under `project_root`.
    Return {rel_path: mtime} for every regular file we care about. Errors
    are swallowed (file may have been deleted between scan and stat).

    v2.50 — also tracks DECISION_*.json files at project root and the
    .onboarding-pending marker, plus workflow/workflow.json. Any write
    to these — whether by the daemon, an external agent's Bash tool, a
    manual edit, or a future scaffolder — triggers a broadcast so the
    canvas auto-refreshes without manual reload. This is the fix for
    'I created new nodes but had to manually refresh to see them.'"""
    out = {}
    for sub in ("source", "design-systems", "workflow"):
        root = os.path.join(project_root, sub)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not _file_watcher_should_skip_dir(d)]
            for fn in filenames:
                if _file_watcher_should_skip_file(fn):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    rel = os.path.relpath(fp, project_root)
                    out[rel] = os.path.getmtime(fp)
                except Exception:
                    continue
    # Project-root JSON markers: DECISION_*.json + .onboarding-pending.
    # These also drive canvas state (checkpoint resolution, stage tracker).
    try:
        for entry in os.scandir(project_root):
            if not entry.is_file(): continue
            name = entry.name
            if name == ".onboarding-pending" or (name.startswith("DECISION_") and name.endswith(".json")):
                try:
                    out[name] = entry.stat().st_mtime
                except Exception:
                    continue
    except Exception:
        pass
    return out

def _file_watcher_known_projects():
    """Return list of (project_id, project_root) for every project the
    daemon currently considers. In workspace mode, enumerates PROJECTS_DIR
    plus any legacy single-project siblings. In single mode, just the
    default project root."""
    out = []
    seen_ids = set()
    if PROJECTS_DIR and os.path.isdir(PROJECTS_DIR):
        try:
            for entry in os.scandir(PROJECTS_DIR):
                if not entry.is_dir(follow_symlinks=False): continue
                if entry.name.startswith("."): continue
                if entry.name in seen_ids: continue
                # Only count entries that look like projects (have source/ or workflow/).
                if (os.path.isdir(os.path.join(entry.path, "source")) or
                    os.path.isdir(os.path.join(entry.path, "workflow"))):
                    out.append((entry.name, entry.path))
                    seen_ids.add(entry.name)
        except Exception:
            pass
    # Single-project fallback — DEFAULT_PROJECT_ROOT may be a legacy install.
    if DEFAULT_PROJECT_ROOT and os.path.isdir(DEFAULT_PROJECT_ROOT):
        pid = os.path.basename(DEFAULT_PROJECT_ROOT.rstrip("/")) or "default"
        if pid not in seen_ids:
            if (os.path.isdir(os.path.join(DEFAULT_PROJECT_ROOT, "source")) or
                os.path.isdir(os.path.join(DEFAULT_PROJECT_ROOT, "workflow"))):
                out.append((pid, DEFAULT_PROJECT_ROOT))
    return out

def _file_watcher_loop():
    """Daemon-thread main loop. Polls every project at
    FILE_WATCHER_INTERVAL_SEC. First pass per project seeds a baseline
    silently (no events fire); subsequent passes diff and broadcast."""
    while True:
        try:
            projects = _file_watcher_known_projects()
            now = time.time()
            for project_id, project_root in projects:
                try:
                    current = _file_watcher_scan_one(project_root)
                except Exception:
                    continue
                with FILE_WATCHER_LOCK:
                    prev = FILE_WATCHER_STATE.get(project_id)
                    FILE_WATCHER_STATE[project_id] = current
                    is_baseline = prev is None
                    if is_baseline:
                        # First scan for this project — seed silently.
                        FILE_WATCHER_PENDING.setdefault(project_id, {})
                        continue
                    pending = FILE_WATCHER_PENDING.setdefault(project_id, {})
                    # Detect modified + added.
                    for rel, mtime in current.items():
                        if prev.get(rel) != mtime:
                            pending[rel] = now
                    # Detect deletions (file present before, gone now).
                    for rel in prev:
                        if rel not in current:
                            pending[rel] = now
                # Flush any pending entries that have settled past the
                # debounce window. Burst writes (e.g. 17 files in 50ms)
                # collapse into one event.
                # v2.50 — split flushed paths by category:
                #   • workflow.json / DECISION_*.json / .onboarding-pending →
                #     these are CANVAS STATE; fire workflow-changed so the
                #     frontend re-fetches /__workflow and merges new nodes.
                #   • everything else (source/, design-systems/) → asset
                #     content; fire asset-changed with the path list.
                # Without this split, the scaffolder writing workflow.json
                # (or any external writer) wouldn't refresh the canvas.
                to_emit_assets = []
                to_emit_workflow = False
                with FILE_WATCHER_LOCK:
                    pending = FILE_WATCHER_PENDING.get(project_id) or {}
                    for rel, ts in list(pending.items()):
                        if (now - ts) >= FILE_WATCHER_DEBOUNCE_SEC:
                            if (rel == "workflow/workflow.json"
                                    or rel == ".onboarding-pending"
                                    or (rel.startswith("DECISION_") and rel.endswith(".json"))):
                                to_emit_workflow = True
                            else:
                                to_emit_assets.append(rel)
                            del pending[rel]
                # v2.50 — before broadcasting asset-changed, run auto-heal.
                # NO path-pattern filtering: file-pattern lists can't be
                # exhaustive — an agent can drop any file shape into the
                # folder convention's outputsRoot. The reconciler is
                # idempotent (every detector bails on already-healed state)
                # and fast (<100ms typical), so we run it on every emit.
                # Whoever knows what counts as a healable orphan is the
                # reconciler, driven by the registry's openEnded contracts —
                # not the watcher trying to guess from file names.
                if to_emit_assets:
                    project_root = next((pr for (pid, pr) in projects if pid == project_id), None)
                    if project_root:
                        try:
                            with _workflow_lock_timeout(project_id, timeout_sec=2.0):
                                # v3.0 — asset-versioning hook. This is the
                                # FOUNDATION: every file write that lands in
                                # source/ triggers a snapshot for any asset
                                # node referencing that path. Endpoint-level
                                # hooks (_workflow_node_run, _asset_generate)
                                # are kept for lineage tracking, but THIS is
                                # what guarantees every visible asset has a
                                # version, regardless of which endpoint or
                                # subprocess wrote the bytes.
                                try:
                                    wf_path = os.path.join(project_root, "workflow", "workflow.json")
                                    if os.path.isfile(wf_path):
                                        with open(wf_path, "r", encoding="utf-8") as f:
                                            wf_for_vsn = json.load(f)
                                        from kinds.versioning import (
                                            snapshot_changed_assets,
                                            flush_pending_scope_snapshots,
                                        )
                                        snaps = snapshot_changed_assets(
                                            project_root, wf_for_vsn, to_emit_assets)
                                        # v3.2 — Also try any deferred scope
                                        # snapshots (multi-file prototype /
                                        # design-system writes that were
                                        # waiting for quiescence).
                                        snaps += flush_pending_scope_snapshots(
                                            project_root, wf_for_vsn)
                                        if snaps:
                                            with open(wf_path, "w", encoding="utf-8") as f:
                                                json.dump(wf_for_vsn, f, indent=2)
                                            print(f"[asset-versioning] project={project_id} "
                                                  f"snapshots={len(snaps)}", flush=True)
                                except Exception as _vsn_err:
                                    print(f"[asset-versioning] watcher snapshot error: {_vsn_err}", flush=True)

                                from kinds.reconcile import apply_auto_heals
                                applied = apply_auto_heals(project_root)
                                if applied:
                                    print(f"[auto-heal] project={project_id} applied={len(applied)} "
                                          f"types={sorted(set(a['drift'] for a in applied if a.get('applied')))}",
                                          flush=True)
                        except LockTimeoutError:
                            pass        # next tick will retry
                        except Exception as e:
                            print(f"[auto-heal] error: {e}", flush=True)
                # v3.2 — Unconditional deferred-scope flush. The previous
                # block above only runs when `to_emit_assets` is non-empty
                # (i.e. when new files changed this tick). But the scope
                # quiescence rule means a multi-file prototype burst that
                # STOPS without further writes would never reach quiescence
                # via the regular path. Flush every tick so a deferred
                # snapshot fires once 15s of inactivity has passed, even if
                # no new edits arrive.
                project_root = next((pr for (pid, pr) in projects if pid == project_id), None)
                if project_root:
                    try:
                        with _workflow_lock_timeout(project_id, timeout_sec=1.0):
                            wf_path = os.path.join(project_root, "workflow", "workflow.json")
                            if os.path.isfile(wf_path):
                                with open(wf_path, "r", encoding="utf-8") as f:
                                    wf_for_flush = json.load(f)
                                from kinds.versioning import flush_pending_scope_snapshots
                                deferred = flush_pending_scope_snapshots(
                                    project_root, wf_for_flush)
                                if deferred:
                                    with open(wf_path, "w", encoding="utf-8") as f:
                                        json.dump(wf_for_flush, f, indent=2)
                                    print(f"[asset-versioning] project={project_id} "
                                          f"deferred-flush={len(deferred)}", flush=True)
                                    to_emit_workflow = True
                    except LockTimeoutError:
                        pass        # next tick
                    except Exception as e:
                        print(f"[asset-versioning] flush error: {e}", flush=True)
                # If watcher snapshots ran, broadcast a workflow-changed too
                # so the canvas refetches workflow.json and shows new dots.
                if to_emit_assets:
                    to_emit_workflow = True
                if to_emit_workflow:
                    _broadcast_workflow_change(project_id)
                if to_emit_assets:
                    _broadcast_asset_change(project_id, to_emit_assets)
        except Exception as e:
            try: print(f"[file-watcher] loop error: {e}", file=sys.stderr, flush=True)
            except Exception: pass
        time.sleep(FILE_WATCHER_INTERVAL_SEC)

def _file_watcher_ensure_started() -> None:
    """Idempotent — first SSE subscriber for any project triggers the
    watcher. Cheaper than starting in main() because daemons launched
    just to serve a single GET don't need it."""
    global FILE_WATCHER_THREAD
    with FILE_WATCHER_THREAD_LOCK:
        if FILE_WATCHER_THREAD is not None and FILE_WATCHER_THREAD.is_alive():
            return
        t = threading.Thread(
            target=_file_watcher_loop,
            daemon=True,
            name="th-file-watcher",
        )
        t.start()
        FILE_WATCHER_THREAD = t


# v2.31 — per-project workflow.json mutex. Every read-modify-write on
# workflow.json (editor /__workflow POST, /__workflow/node/<id>/status,
# subprocess completion hook) MUST hold this lock so concurrent writers
# don't clobber each other's snapshots. Without this, the editor's save
# (with the user's typed edit) and the orchestrator's /status update
# (read BEFORE the user's save landed) race — whichever writes second
# wins, and the user sees their edit reverted seconds later.
WORKFLOW_MUTEX: dict = {}          # {project_id: threading.Lock}
WORKFLOW_MUTEX_GUARD = threading.Lock()

def _workflow_lock(project_id: str) -> threading.Lock:
    if not project_id: project_id = "_anonymous"
    with WORKFLOW_MUTEX_GUARD:
        lk = WORKFLOW_MUTEX.get(project_id)
        if lk is None:
            lk = threading.Lock()
            WORKFLOW_MUTEX[project_id] = lk
        return lk


# v2.50 — Deliverable 2 concurrency guardrails (G3 lock timeout, G5 semaphore,
# G6 request-ID correlation). See WORKFLOW_TRUTHFULNESS_PLAN.md §9 / §11 D2.
class LockTimeoutError(Exception):
    """Raised when the per-project workflow lock can't be acquired within
    the timeout window. The endpoint should translate this into a 503 with
    a retry hint, not a silent hang."""
    pass

@contextlib.contextmanager
def _workflow_lock_timeout(project_id: str, timeout_sec: float = 2.0):
    """Acquire the per-project workflow lock with a bounded wait. On
    timeout, raise LockTimeoutError so the caller can return HTTP 503
    with a retry hint — distinguishing "daemon busy" from "daemon down"
    so the frontend's daemon-status badge doesn't false-positive."""
    lk = _workflow_lock(project_id)
    acquired = lk.acquire(timeout=timeout_sec)
    if not acquired:
        raise LockTimeoutError(f"workflow lock for {project_id!r} held > {timeout_sec}s")
    try:
        yield lk
    finally:
        lk.release()


# Per-project request semaphore (G5). Caps concurrent expensive operations
# per project so one project's burst (e.g. 9 parallel remix subagents) can't
# saturate the server's threads and starve other projects.
REQUEST_SEMAPHORE_CAP = 3
REQUEST_SEMAPHORES: dict = {}      # {project_id: threading.BoundedSemaphore}
REQUEST_SEMAPHORES_GUARD = threading.Lock()

def _request_semaphore(project_id: str) -> threading.BoundedSemaphore:
    if not project_id: project_id = "_anonymous"
    with REQUEST_SEMAPHORES_GUARD:
        sem = REQUEST_SEMAPHORES.get(project_id)
        if sem is None:
            sem = threading.BoundedSemaphore(REQUEST_SEMAPHORE_CAP)
            REQUEST_SEMAPHORES[project_id] = sem
        return sem

class SemaphoreBusyError(Exception):
    """Per-project semaphore is full. Endpoint should 503."""
    pass


class _VersioningHTTPError(Exception):
    """Carry an HTTP status + JSON body up through the versioning endpoints.

    Used by the v3.0 asset-versioning handlers (_workflow_version_*,
    _workflow_composition_*, _workflow_node_size) so the shared open/find
    helpers can bail out with a typed reply without dragging the response
    object through every call site."""
    def __init__(self, status: int, body: dict):
        self.status = status
        self.body = body
        super().__init__(body.get("error") if isinstance(body, dict) else str(body))

@contextlib.contextmanager
def _project_request_slot(project_id: str, timeout_sec: float = 5.0):
    """Bounded concurrency per project. Returns 503 if the project is
    already running REQUEST_SEMAPHORE_CAP requests."""
    sem = _request_semaphore(project_id)
    acquired = sem.acquire(timeout=timeout_sec)
    if not acquired:
        raise SemaphoreBusyError(f"project {project_id!r} has > {REQUEST_SEMAPHORE_CAP} concurrent ops")
    try:
        yield
    finally:
        try: sem.release()
        except ValueError: pass        # already released; tolerate


def _new_request_id() -> str:
    """Short, human-grep-able request ID for correlation across browser
    console + daemon logs. 8 hex chars is enough at single-user scale."""
    return uuid.uuid4().hex[:8]


# Daemon-shutdown cleanup. Without this, restarting the daemon (preview_stop,
# Ctrl-C, SIGTERM, any normal kill) would orphan its child CLI subprocesses:
# the Python daemon exits, the children get reparented to launchd/init, and
# they keep running for minutes (sometimes hours) talking to the API and
# billing tokens that nobody can read. The orphan + the run record's
# in-memory state diverge — restart leaves you with active CLIs you can't
# stop from the UI.
#
# This hook walks RUNS, sends SIGTERM to every state.proc that's still
# alive, gives it a beat to exit cleanly, then SIGKILLs anything that
# refused. Registered for SIGTERM (preview_stop sends this), SIGINT
# (Ctrl-C), and atexit (any clean Python exit, including KeyboardInterrupt
# unwind in the main loop).
#
# The handler is idempotent — once-only via _cleanup_ran so a SIGTERM that
# unwinds through KeyboardInterrupt + atexit doesn't run kills twice.
_cleanup_ran = False
_cleanup_lock = threading.Lock()

def _cleanup_subprocesses(reason: str = "shutdown") -> None:
    global _cleanup_ran
    with _cleanup_lock:
        if _cleanup_ran: return
        _cleanup_ran = True
    # Snapshot the run map under the lock, then operate without it (so
    # finish() / append() inside child threads don't deadlock if the
    # cleanup races with a still-active reader).
    with RUNS_LOCK:
        snapshot = list(RUNS.items())
    alive = []
    for run_id, state in snapshot:
        proc = getattr(state, "proc", None)
        if proc is None: continue
        try:
            if proc.poll() is not None: continue   # already exited
        except Exception:
            continue
        alive.append((run_id, proc))
    if not alive:
        try: print(f"shutdown ({reason}): no active subprocesses to clean up", flush=True)
        except Exception: pass
        return
    try: print(f"shutdown ({reason}): SIGTERM {len(alive)} active CLI subprocess(es)…", flush=True)
    except Exception: pass
    # Pass 1: SIGTERM.
    for run_id, proc in alive:
        try: proc.terminate()
        except Exception: pass
    # Give them 2s to exit cleanly.
    deadline = time.time() + 2.0
    for run_id, proc in alive:
        remaining = max(0.0, deadline - time.time())
        try: proc.wait(timeout=remaining if remaining > 0 else 0.01)
        except Exception: pass
    # Pass 2: SIGKILL anything still alive.
    survivors = []
    for run_id, proc in alive:
        try:
            if proc.poll() is None: survivors.append((run_id, proc))
        except Exception: pass
    if survivors:
        try: print(f"shutdown ({reason}): SIGKILL {len(survivors)} subprocess(es) that ignored SIGTERM…", flush=True)
        except Exception: pass
        for run_id, proc in survivors:
            try: proc.kill()
            except Exception: pass
        deadline = time.time() + 1.0
        for run_id, proc in survivors:
            remaining = max(0.0, deadline - time.time())
            try: proc.wait(timeout=remaining if remaining > 0 else 0.01)
            except Exception: pass
    # Mark all of them done in the run record so a re-adopted daemon (or
    # the JSONL replay) sees a clean lifecycle terminator instead of a
    # mid-flight zombie.
    for run_id, proc in alive:
        st = None
        with RUNS_LOCK:
            st = RUNS.get(run_id)
        if not st: continue
        try:
            ec = proc.poll() if proc.poll() is not None else None
            st.append("status", {"label": "interrupted", "reason": reason})
            st.finish(ec)
        except Exception: pass

def _install_shutdown_hooks():
    """Wire SIGTERM (preview_stop, `kill`), SIGINT (Ctrl-C), and atexit to
    the subprocess cleanup. atexit covers normal Python exits including the
    KeyboardInterrupt-unwind path in the main loop."""
    def _on_signal(signum, frame):
        try: _cleanup_subprocesses(reason=f"signal {signum}")
        finally:
            # Re-raise via default disposition so the process actually exits.
            # signal.SIG_DFL would deliver again; safer to sys.exit which
            # triggers atexit (already guarded by _cleanup_ran).
            try: sys.exit(0)
            except SystemExit: raise
    try: signal.signal(signal.SIGTERM, _on_signal)
    except Exception: pass
    try: signal.signal(signal.SIGINT,  _on_signal)
    except Exception: pass
    atexit.register(_cleanup_subprocesses, reason="atexit")

# ── Phase 5b — Step 4f render-check screenshot queue ────────────────────────
# The orchestrator agent needs to capture a screenshot of every editor view after
# Workflow 1 finishes, as the integration-test step that proves the data file
# actually renders. Headless Chrome would mean a heavy dependency; instead the
# editor's already-loaded `html2canvas-pro` runs inside the user's open editor
# tab — daemon brokers the request via a small job queue.
#
# Lifecycle:
#   1. Agent calls POST /__screenshot { branch, view? | file?, waitMs? }.
#      Daemon creates an SsJob, parks the response on `result_event`.
#   2. Editor's `ScreenshotWorker` long-polls GET /__screenshot/jobs?branch=.
#      Daemon atomically claims a queued job (flips state→running), returns it.
#   3. Editor runs html2canvas, POSTs the PNG to /__screenshot/jobs/<id>/result.
#   4. Daemon stores bytes on the job, fires `result_event`, the original POST
#      unblocks and streams the PNG back to the agent.
#
# Job retention: done/error jobs stay in the dict for SCREENSHOT_JOB_TTL_S so
# late-arriving worker results (race after the caller already timed out) get
# logged sanely, then they're GC'd on the next /__screenshot create.
SCREENSHOT_JOBS_LOCK = threading.Lock()
SCREENSHOT_JOBS: dict = {}                # job_id → SsJob
SCREENSHOT_WAITERS: dict = {}             # branch → set[threading.Event] (worker pollers)
SCREENSHOT_JOB_TTL_S = 120.0
SCREENSHOT_CALLER_TIMEOUT_S = 30.0        # how long /__screenshot blocks before returning timeout
SCREENSHOT_WORKER_POLL_TIMEOUT_S = 25.0   # how long GET /__screenshot/jobs hangs before returning empty
SCREENSHOT_MAX_PNG_BYTES = 20 * 1024 * 1024  # 20 MB cap on POST'd result

# View IDs the editor's worker knows how to render. Mirrors the toolbar tabs.
SCREENSHOT_VIEWS = {
    "canvas", "prototype", "flow", "ia", "ds",
    "entities", "stateMachine", "timeline", "grid",
}


class SsJob:
    __slots__ = (
        "job_id", "branch", "kind", "view", "file", "frame_id", "wait_ms",
        "selector", "scale", "created_at", "state",
        "png_bytes", "error", "result_event", "width", "height",
    )

    def __init__(self, job_id, branch, kind, view=None, file=None, frame_id=None,
                 wait_ms=600, selector=None, scale=1):
        self.job_id = job_id
        self.branch = branch
        self.kind = kind          # "view" | "file"
        self.view = view
        self.file = file
        self.frame_id = frame_id
        self.wait_ms = wait_ms
        self.selector = selector
        self.scale = scale
        self.created_at = time.time()
        self.state = "queued"     # "queued" | "running" | "done" | "error"
        self.png_bytes = None
        self.error = None
        self.result_event = threading.Event()
        self.width = None
        self.height = None

    def public_dict(self) -> dict:
        return {
            "id":       self.job_id,
            "branch":   self.branch,
            "kind":     self.kind,
            "view":     self.view,
            "file":     self.file,
            "frameId":  self.frame_id,
            "waitMs":   self.wait_ms,
            "selector": self.selector,
            "scale":    self.scale,
            "createdAt": self.created_at,
        }


def _ss_wake_branch(branch: str) -> None:
    """Wake every worker long-poll listening on this branch."""
    with SCREENSHOT_JOBS_LOCK:
        waiters = list(SCREENSHOT_WAITERS.get(branch, ()))
    for w in waiters:
        w.set()


def _ss_gc_locked() -> None:
    """Drop done/error jobs older than the TTL. Must be called with
    SCREENSHOT_JOBS_LOCK held."""
    now = time.time()
    dead = [jid for jid, job in SCREENSHOT_JOBS.items()
            if job.state in ("done", "error") and (now - job.created_at) > SCREENSHOT_JOB_TTL_S]
    for jid in dead:
        SCREENSHOT_JOBS.pop(jid, None)


# Phase 5a — per-branch chat history persistence. Each spawned agent run
# writes its full event stream to `<project_root>/editor/branches/<slug>.chat.jsonl`
# (one JSON object per line). The file is append-only across runs, so a single
# branch's JSONL contains every chat turn ever — re-opening a branch in a fresh
# daemon shows yesterday's conversation. Writes are best-effort; failures must
# never break the in-memory event log that the live SSE stream consumes.

# Serialize writes per file path. Multiple runs on the same branch race here.
_CHAT_JSONL_LOCKS: dict = {}
_CHAT_JSONL_LOCKS_GUARD = threading.Lock()


def _chat_jsonl_path(project_root: str, branch: str = "main") -> str:
    """v3.1 — branches deprecated. All chat history collapses to one
    file at editor/chat.jsonl. `branch` arg kept for ABI compat; ignored."""
    return os.path.join(project_root, "editor", "chat.jsonl")


def _chat_jsonl_lock(path: str) -> threading.Lock:
    with _CHAT_JSONL_LOCKS_GUARD:
        lk = _CHAT_JSONL_LOCKS.get(path)
        if lk is None:
            lk = threading.Lock()
            _CHAT_JSONL_LOCKS[path] = lk
        return lk


def _chat_jsonl_append(state, seq: int, ev_type: str, data) -> None:
    """Append one event line to the active branch's chat JSONL. Each line is
    self-describing — the rehydrator on the UI side parses lines independently
    and groups by `runId`. `seq` < 0 marks a synthetic lifecycle event (see
    RunState.finish) that doesn't correspond to an SSE frame."""
    project_root = getattr(state, "project_root", None) or DEFAULT_PROJECT_ROOT
    branch = getattr(state, "branch", None) or "main"
    if not SLUG_OK.match(branch):
        return  # defensive — branch slug should always be validated upstream
    path = _chat_jsonl_path(project_root, branch)
    line = {
        "runId":   state.run_id,
        "branch":  branch,
        "agentId": state.agent_id,
        "kind":    state.kind,
        "title":   state.title,
        "startedAt": state.started_at,
        "seq":     seq,
        "type":    ev_type,
        "data":    data,
        "ts":      time.time(),
    }
    serialized = json.dumps(line, ensure_ascii=False)
    lk = _chat_jsonl_lock(path)
    with lk:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(serialized + "\n")


def _chat_jsonl_candidate_files(project_root: str) -> list:
    """Single source of truth for "where chat.jsonl lives for this project".

    Returns [(abs_path, branch_slug)] in read priority order: the flat v3.1
    layout (editor/chat.jsonl, slug="main") first, then any legacy
    editor/branches/*.chat.jsonl files for in-flight installs that haven't
    been migrated yet.

    Every reader that wants to scan chat history MUST go through here. If you
    are adding a new layout (or removing the legacy fallback), this is the
    only function that should change. See historical incident: v3.1 missed
    updating _rehydrate_run_from_jsonl when the flat layout shipped, which
    broke session resume for every project created after the migration."""
    out = []
    flat = os.path.join(project_root, "editor", "chat.jsonl")
    if os.path.isfile(flat):
        out.append((flat, "main"))
    branches_dir = os.path.join(project_root, "editor", "branches")
    if os.path.isdir(branches_dir):
        try:
            for name in os.listdir(branches_dir):
                if name.endswith(".chat.jsonl"):
                    out.append((
                        os.path.join(branches_dir, name),
                        name[:-len(".chat.jsonl")],
                    ))
        except OSError:
            pass
    return out


def _chat_jsonl_scan_historical(project_root: str) -> dict:
    """v3.1 — branches deprecated. Reads the single editor/chat.jsonl
    (falling back to legacy editor/branches/*.chat.jsonl files if found,
    so existing in-flight installs aren't lost on upgrade)."""
    out: dict = {}
    for path, _branch_slug in _chat_jsonl_candidate_files(project_root):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except Exception:
                        continue
                    rid = rec.get("runId")
                    if not rid:
                        continue
                    meta = out.get(rid)
                    if meta is None:
                        meta = {
                            "runId":          rid,
                            "agentId":        rec.get("agentId") or "claude",
                            "branch":         rec.get("branch") or "main",
                            "kind":           rec.get("kind") or "freeform",
                            "title":          rec.get("title") or "",
                            "startedAt":      rec.get("startedAt") or rec.get("ts") or 0,
                            "done":           False,
                            "turnDone":       False,
                            "turnsCompleted": 0,
                            "exitCode":       None,
                            "lastSeq":        -1,
                            "modifying":      False,
                            "historical":     True,
                        }
                        out[rid] = meta
                    # Track lifecycle terminators
                    if rec.get("type") == "__finish":
                        meta["done"] = True
                        ec = (rec.get("data") or {}).get("exitCode")
                        if ec is not None:
                            meta["exitCode"] = ec
                    # Track "turn done" — claude-code emits status:done at end
                    # of each agent turn. Useful so the UI dot picks "waiting"
                    # over "live" when reopening.
                    if (rec.get("type") == "agent"
                            and isinstance(rec.get("data"), dict)
                            and rec["data"].get("type") == "status"
                            and rec["data"].get("label") == "done"):
                        meta["turnDone"] = True
                        meta["turnsCompleted"] = int(meta.get("turnsCompleted") or 0) + 1
                    # Track the highest seq so the UI can compute "after"
                    seq_v = rec.get("seq")
                    if isinstance(seq_v, int) and seq_v > meta["lastSeq"]:
                        meta["lastSeq"] = seq_v
        except OSError:
            continue
    return out


def _rehydrate_run_from_jsonl(run_id: str, project_root: str):
    """v2.29b — when an /__run/<id>/* endpoint is hit after a daemon restart
    (RUNS is in-memory only — every restart wipes it), the runId 404s even
    though the conversation is persisted on disk. This helper scans the chat
    JSONL(s) for the run, extracts session_id + metadata, and constructs a
    minimal RunState so the existing resume / stop / chat endpoints can do
    their work without spawning a fresh chat from scratch. Returns the
    RunState on success, None if the run isn't found or session_id is
    missing (can't resume without it).

    Layout knowledge lives in _chat_jsonl_candidate_files — do not duplicate
    the flat-vs-branches scan logic here."""
    candidates = _chat_jsonl_candidate_files(project_root)
    if not candidates:
        return None
    for path, branch_slug in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        # First pass: confirm this file has the run
        run_lines = []
        for raw in lines:
            raw = raw.strip()
            if not raw: continue
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if rec.get("runId") == run_id:
                run_lines.append(rec)
        if not run_lines:
            continue
        # Extract metadata from collected records
        first = run_lines[0]
        agent_id = first.get("agentId") or "claude"
        kind = first.get("kind") or "freeform"
        title = first.get("title") or ""
        started_at = first.get("startedAt") or first.get("ts") or 0
        session_id = None
        exit_code = None
        done = False
        events = []
        seq = 0
        # v3.8.3 — also rehydrate permission_mode from the persisted
        # `spawned` event. Earlier this was dropped, so after a daemon
        # restart every /resume spawn fell through both branches of
        # _run_resume's flag-selector (state.permission_mode == None)
        # and the subprocess was launched with NO bypass flags at all.
        # Symptom: every Edit / Write came back as "Claude requested
        # permissions to write to … but you haven't granted it yet."
        # The JSONL's `spawned` event has carried permissionMode since
        # v2.x so we just read it back here.
        permission_mode = None
        for rec in run_lines:
            data = rec.get("data") or {}
            # Capture session_id from any agent frame that carries it
            if isinstance(data, dict) and data.get("sessionId") and not session_id:
                session_id = data["sessionId"]
            # Capture permission_mode from the initial spawn event
            if isinstance(data, dict) and data.get("label") == "spawned" \
                    and data.get("permissionMode") and permission_mode is None:
                permission_mode = data["permissionMode"]
            if rec.get("type") == "__finish":
                done = True
                ec = data.get("exitCode") if isinstance(data, dict) else None
                if ec is not None: exit_code = ec
            # Re-build the events list so /__chat?runId= returns the transcript
            if rec.get("type") and rec.get("type") != "__finish":
                evt = {"type": rec["type"], "data": data, "seq": rec.get("seq", seq)}
                events.append(evt)
                seq = max(seq, rec.get("seq", seq)) + 1
        # Construct the ghost RunState. No proc — endpoints that need a live
        # subprocess (tool-result) will still error, but /resume re-spawns
        # the CLI with --resume <session_id> so it doesn't need state.proc.
        project_id = os.path.basename(project_root.rstrip("/"))
        state = RunState(
            run_id=run_id, proc=None, agent_id=agent_id, branch=branch_slug,
            kind=kind, title=title, project_id=project_id, project_root=project_root,
        )
        state.session_id = session_id
        state.started_at = started_at
        state.done = done
        state.exit_code = exit_code
        state.events = events
        # Fall back to the daemon default if the spawn event predates the
        # permissionMode field (old runs from before that field landed).
        state.permission_mode = permission_mode or AGENT_DEFS.get(agent_id, {}).get("permission_default")
        with RUNS_LOCK:
            RUNS[run_id] = state
        return state
    return None


def _chat_jsonl_read_branch(project_root: str, branch: str) -> list:
    """Load every event line for a single branch's chat history. Returns a
    flat list ordered by file position (which is also chronological since we
    only ever append)."""
    path = _chat_jsonl_path(project_root, branch)
    if not os.path.isfile(path):
        return []
    out: list = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    out.append(json.loads(raw))
                except Exception:
                    continue
    except OSError:
        return []
    return out


class RunState:
    """One spawned agent. Holds the subprocess, the append-only event log, and
    a set of `threading.Event`s waiters block on. SSE handlers register an
    event, wait, then drain new entries.

    Two lifecycle flags:
      - `turn_done`: True after the agent emits a `result` frame. Becomes
        False again when the user sends a follow-up. Drives the UI's "done,
        you can reply" state. The process is still alive.
      - `done`: True only after the subprocess actually exits (Stop button,
        daemon shutdown, agent crash).
    """

    __slots__ = ("run_id", "proc", "agent_id", "branch", "kind", "title",
                 "session_id", "permission_mode", "bin_path", "modifying",
                 "project_id", "project_root",
                 "started_at", "events", "lock", "waiters",
                 "done", "exit_code", "turn_done", "turns_completed",
                 # Phase 3 — undo/redo history snapshot bookkeeping. The
                 # before-snapshot is taken at spawn (id + path inventory),
                 # the after-snapshot + diff is committed at state.finish().
                 "history_pending_id", "history_before_paths", "history_before_rows",
                 # v2.1 — when this run was spawned by /__workflow/node/<id>/run
                 # for an agent-kind node, this tags the originating node so the
                 # completion hook in _drain_stdout can flip the canvas node to
                 # done/error. None for plain freeform / other run kinds.
                 "workflow_node_id",
                 # v2.28 — intentional-termination flag ("completed-orchestrator",
                 # "user-stop", or None for natural exit). Lets finish() report
                 # SIGTERM-after-success as exit 0 instead of "failed".
                 "stop_reason",
                 # v2.24 — set on the first status:done frame for a node-agent
                 # run so the finally-block fallback doesn't double-fire.
                 "_node_completion_fired")

    def __init__(self, run_id, proc, agent_id, branch, kind, title, project_id=None, project_root=None):
        self.run_id = run_id
        self.proc = proc
        self.agent_id = agent_id
        self.branch = branch
        self.kind = kind
        self.title = title
        # Phase 6 — remember which project this run was spawned in so /resume
        # can rebuild the same env + cwd, and so /__runs can group by project.
        self.project_id = project_id
        self.project_root = project_root or DEFAULT_PROJECT_ROOT
        self.started_at = time.time()
        self.events: list = []
        self.lock = threading.Lock()
        self.waiters: set = set()
        self.done = False
        self.exit_code = None
        self.turn_done = False
        self.turns_completed = 0
        # v2.28 — intentional-termination flag. None = natural exit (exit_code
        # is the truth: 0 = done, !=0 = failed). Otherwise: a string naming
        # WHY we terminated the subprocess on purpose, so the run record can
        # distinguish "done" / "stopped" / "failed" instead of conflating
        # SIGTERM (exit 143) with real failures.
        #   "completed-orchestrator" — v2.24's SIGTERM after status:done
        #   "user-stop" — user clicked Stop (or some other intentional API)
        self.stop_reason = None
        # Claude Code emits a session_id in its system/init frame. We capture
        # it so that, after the user clicks Stop and types a follow-up, we can
        # respawn the CLI with --resume <session_id> + the new message and
        # keep the full conversation context. Without this, post-Stop replies
        # would start a fresh conversation with no memory.
        self.session_id = None
        # Stored so /resume can replicate the original spawn config.
        self.permission_mode = None
        self.bin_path = None
        # Phase 3 history bookkeeping. Populated by _run_create immediately
        # after the RunState is constructed; consumed by _drain_stdout after
        # state.finish().
        self.history_pending_id   = None
        self.history_before_paths = []
        self.history_before_rows  = []
        # v2.1 — set by _spawn_node_agent when this run was dispatched for an
        # agent-kind workflow node. Consumed by _drain_stdout's auto-completion
        # hook to flip the canvas node to done/error on subprocess exit.
        self.workflow_node_id = None
        # Whether THIS run is touching files. Kinds that always modify
        # (edits-apply, regenerate, fork, merge, *-request) set this true at
        # spawn time; freeform runs flip it on the first Write/Edit/MultiEdit/
        # NotebookEdit tool_use. The UI uses this to scope the "interactions
        # paused" lock to runs that actually need it — a plain chat asking for
        # a visualization doesn't freeze the canvas.
        self.modifying = False

    def append(self, ev_type: str, data) -> None:
        with self.lock:
            seq = len(self.events)
            self.events.append({"seq": seq, "type": ev_type, "data": data})
            waiters = list(self.waiters)
        # Phase 5a — also persist the event to the per-branch chat JSONL so the
        # conversation survives daemon restarts. Fire-and-forget; a write
        # failure here must never break the live SSE stream above.
        try:
            _chat_jsonl_append(self, seq, ev_type, data)
        except Exception:
            pass
        for w in waiters:
            w.set()

    def finish(self, exit_code) -> None:
        with self.lock:
            self.done = True
            self.exit_code = exit_code
            waiters = list(self.waiters)
            reason = self.stop_reason  # snapshot under lock
        # Mirror the lifecycle terminator so a re-hydrated JSONL knows the run
        # is closed (otherwise the UI would treat every historical run as
        # mid-flight). v2.28 — include stopReason so the UI can render
        # "done"/"stopped" instead of conflating with "failed".
        try:
            _chat_jsonl_append(self, -1, "__finish",
                               {"exitCode": exit_code, "stopReason": reason})
        except Exception:
            pass
        for w in waiters:
            w.set()


def detect_agent_bin(agent_id: str):
    """Return the resolved path to the agent's binary, or None if not on PATH.
    Honours the per-agent env override (CLAUDE_BIN / CODEX_BIN) first.
    """
    env_key = AGENT_BIN_ENV.get(agent_id)
    if env_key:
        override = os.environ.get(env_key)
        if override and os.path.isfile(override):
            return override
    defs = AGENT_DEFS.get(agent_id)
    if not defs:
        return None
    return shutil.which(defs["bin"])


def _agent_version(bin_path: str):
    try:
        out = subprocess.run(
            [bin_path, "--version"], capture_output=True, text=True, timeout=5,
        )
        v = (out.stdout or out.stderr or "").strip().splitlines()
        return v[0] if v else None
    except Exception:
        return None


def _list_available_agents() -> list:
    """Catalog every known agent + whether it's invocable on this machine."""
    out = []
    for agent_id, defs in AGENT_DEFS.items():
        bin_path = detect_agent_bin(agent_id)
        out.append({
            "id": agent_id,
            "label": agent_id.capitalize(),
            "bin": bin_path,
            "version": _agent_version(bin_path) if bin_path else None,
            "available": bool(bin_path),
        })
    return out


# ── stream-json normaliser ──────────────────────────────────────────────────
# Claude Code's --output-format=stream-json emits one JSON object per line, of
# shape (paraphrased):
#   { "type": "system",    "subtype": "init", ... }
#   { "type": "assistant", "message": { "content": [ { type:"text", text:"…" },
#                                                    { type:"tool_use", id, name, input } ] } }
#   { "type": "user",      "message": { "content": [ { type:"tool_result", tool_use_id, content, is_error } ] } }
#   { "type": "result",    "subtype": "success" | "error_during_execution",
#                          "duration_ms", "total_cost_usd", "usage": { ... } }
# Codex matches closely; the only divergences I expect are top-level field
# casing — handle both. Normalise into the StreamEvent shape from
# open-design's json-event-stream.ts so the UI doesn't branch per CLI.

def _normalize_frame(agent_id: str, frame: dict) -> list:
    """Return a list of normalised event dicts for one upstream stream-json
    frame. Many frames yield multiple events (an assistant message with text +
    a tool_use produces two)."""
    out = []
    ftype = frame.get("type") or frame.get("Type")

    if ftype == "system":
        sub = frame.get("subtype")
        if sub == "init":
            out.append({
                "type": "status",
                "label": "starting",
                "model": frame.get("model"),
                "sessionId": frame.get("session_id"),
            })
        elif sub == "thinking_tokens":
            # v3.1 — thinking_tokens streams every ~50 tokens while the model
            # is reasoning. Surface it as a structured event the frontend
            # consolidates into ONE rolling progress chip (see buildBlocks /
            # thinking_progress in app.js).
            out.append({
                "type":                   "system",
                "subtype":                "thinking_tokens",
                "estimated_tokens":       frame.get("estimated_tokens"),
                "estimated_tokens_delta": frame.get("estimated_tokens_delta"),
            })
        elif sub == "task_progress":
            # v3.2 — task_progress streams while a subagent is mid-tool-use
            # ("Reading workflow/workflow.json", "Editing source/foo.html",
            # etc.). Surface as a structured event the frontend consolidates
            # into a single rolling chip per parent tool block.
            out.append({
                "type":           "system",
                "subtype":        "task_progress",
                "description":    frame.get("description"),
                "subagent_type":  frame.get("subagent_type"),
                "taskId":         frame.get("task_id"),
                "toolUseId":      frame.get("tool_use_id"),
            })
        # v3.2 — any OTHER system subtype is SDK chatter (perms, mcp_status,
        # post_tool_use diagnostics, etc.). Drop entirely — these events
        # have no user-actionable content. Previously we wrapped them in a
        # `raw` envelope, which dumped raw JSON into the chat (user reported:
        # "still seeing all of these {type:system blah blah}").
        return out

    if ftype == "assistant":
        msg = frame.get("message") or {}
        for part in (msg.get("content") or []):
            kind = part.get("type")
            if kind == "text":
                out.append({"type": "text_delta", "delta": part.get("text") or ""})
            elif kind == "thinking":
                out.append({"type": "thinking_delta", "delta": part.get("thinking") or part.get("text") or ""})
            elif kind == "tool_use":
                out.append({
                    "type": "tool_use",
                    "id": part.get("id"),
                    "name": part.get("name"),
                    "input": part.get("input"),
                })
            else:
                out.append({"type": "raw", "subtype": f"assistant/{kind}", "part": part})
        usage = msg.get("usage")
        if usage:
            out.append({"type": "usage", "usage": usage})
        return out

    if ftype == "user":
        # Tool results come back addressed to the assistant on `user` frames.
        # v3.1 — preserve image parts. When Claude reads a PNG/JPG, or when a
        # Bash command (e.g. screenshot) returns an image-typed content part,
        # the SDK emits `content: [{type:"image", source:{type:"base64",
        # media_type:"image/png", data:"…"}}, …]`. Previously we walked the
        # list and concatenated only `.text` — image blocks were silently
        # dropped because they have no `.text` field. Now we split the list:
        # text parts go to `content` (unchanged), image parts go to a sibling
        # `images: [{mediaType, data}]` array the frontend renders inline.
        msg = frame.get("message") or {}
        for part in (msg.get("content") or []):
            if part.get("type") == "tool_result":
                content = part.get("content")
                text_chunks = []
                images = []
                if isinstance(content, list):
                    for p in content:
                        if not isinstance(p, dict):
                            continue
                        ptype = p.get("type")
                        if ptype == "text" and p.get("text"):
                            text_chunks.append(p.get("text") or "")
                        elif ptype == "image":
                            src = p.get("source") or {}
                            if src.get("type") == "base64" and src.get("data"):
                                images.append({
                                    "mediaType": src.get("media_type") or "image/png",
                                    "data":      src.get("data"),
                                })
                            elif src.get("type") == "url" and src.get("url"):
                                images.append({"url": src.get("url")})
                        else:
                            # Unknown content part — keep its raw JSON visible
                            # so a future SDK addition doesn't disappear silently.
                            try:
                                text_chunks.append(json.dumps(p, ensure_ascii=False))
                            except Exception:
                                pass
                    text = "".join(text_chunks)
                else:
                    text = content if isinstance(content, str) else json.dumps(content)
                event = {
                    "type": "tool_result",
                    "toolUseId": part.get("tool_use_id"),
                    "content": text,
                    "isError": bool(part.get("is_error")),
                }
                if images:
                    event["images"] = images
                out.append(event)
        return out

    if ftype == "result":
        out.append({
            "type": "status",
            "label": "done" if frame.get("subtype") == "success" else "error",
            "subtype": frame.get("subtype"),
            "durationMs": frame.get("duration_ms"),
            "costUsd": frame.get("total_cost_usd"),
            "usage": frame.get("usage"),
            "result": frame.get("result"),
        })
        return out

    if ftype == "error":
        out.append({
            "type": "error",
            "message": frame.get("message") or frame.get("error") or str(frame),
        })
        return out

    if ftype == "rate_limit_event":
        # Claude Code emits these periodically with shape
        # { rate_limit_info: { status: "allowed"|"warning"|"rejected",
        #                      resetsAt, rateLimitType: "five_hour"|"weekly"|…,
        #                      overageStatus, overageDisabledReason, … } }.
        # "allowed" is healthy telemetry — drop. Anything else is actionable
        # (the user needs to know they're throttled or close to it), so surface
        # as a thin status row with a single readable line.
        info = frame.get("rate_limit_info") or {}
        status = (info.get("status") or "").lower()
        if status == "allowed":
            return out
        kind = info.get("rateLimitType") or "rate"
        bits = [f"rate limit · {kind} {status or 'limited'}"]
        resets = info.get("resetsAt")
        if isinstance(resets, (int, float)):
            mins = max(0, int((resets - int(__import__('time').time())) / 60))
            if mins > 60:
                bits.append(f"resets in ~{mins // 60}h{mins % 60:02d}m")
            else:
                bits.append(f"resets in ~{mins}m")
        out.append({"type": "status", "label": " · ".join(bits)})
        return out

    # Unknown — pass through so we can see it in the UI's "raw" tab.
    out.append({"type": "raw", "frame": frame})
    return out


def _fire_node_completion_hook(state, *, exit_code):
    """v2.24 — flip a workflow node's runStatus + record runId, atomically.

    Extracted from `_drain_stdout`'s finally block so the same logic can fire
    both from process-exit (legacy path) AND from turn-done (new path for
    node-agent dispatches that stay alive after one turn because they're in
    stream-json mode but have no follow-up). Best-effort — never raises.
    """
    wf_node_id = getattr(state, "workflow_node_id", None)
    if not wf_node_id or not state.project_root: return
    wf_path = os.path.join(state.project_root, "workflow", "workflow.json")
    if not os.path.isfile(wf_path): return
    # v2.31 — same lock as editor /__workflow + /status. Without it, the
    # subprocess completion hook would race the editor's debounced save,
    # writing stale snapshot back over a user edit.
    project_id = state.project_id or os.path.basename(state.project_root.rstrip("/"))
    with _workflow_lock(project_id):
     with open(wf_path, "r", encoding="utf-8") as f:
        wf = json.load(f)
     nodes = wf.get("nodes") or []
     target = next((n for n in nodes if isinstance(n, dict) and n.get("id") == wf_node_id), None)
     if target is None: return
     target["runStatus"] = "done" if exit_code == 0 else "error"
     if exit_code == 0:
        target.pop("runError", None)
     else:
        target["runError"] = f"subprocess exit {exit_code}"
     # v2.20 — keep runId + runRunId both populated so the chat tab can find
     # the transcript via /__chat?runId= regardless of which field the
     # frontend reads.
     target["runId"]    = state.run_id
     target["runRunId"] = state.run_id
     # v3.0 — asset-versioning snapshot hook for async agent runs. Only fires
     # on success; failure leaves the run in error state with no snapshot.
     if exit_code == 0:
         try:
             from kinds.versioning import snapshot_downstream_assets
             snapshot_downstream_assets(state.project_root, wf, wf_node_id)
         except Exception as _vsn_err:
             print(f"[asset-versioning] async snapshot error on {wf_node_id}: {_vsn_err}", flush=True)
     with _history_bracket(state.project_root, ["workflow/workflow.json"],
                           kind="workflow-op",
                           label=f"Node finish: {target.get('title') or wf_node_id} → {target['runStatus']}",
                           source="workflow",
                           extra={"nodeId": wf_node_id, "runId": state.run_id, "exitCode": exit_code}):
         with open(wf_path, "w", encoding="utf-8") as f:
             json.dump(wf, f, indent=2)
    # v2.30 — notify SSE subscribers that workflow.json changed (outside the lock)
    _broadcast_workflow_change(state.project_id)


def _drain_stdout(state: "RunState") -> None:
    """Read newline-delimited JSON from the child, normalise, append events.

    Claude Code in `--input-format stream-json` mode keeps the agent process
    alive across turns — each `result` frame ends one turn, but the process
    stays open on stdin waiting for follow-up `user` frames. We mirror that
    multi-turn model: surface `turn_done` (per-turn) on each result so the UI
    can show "done, you can reply" without killing the process. The hard
    `state.done` flag only flips when the subprocess actually exits (user
    clicks Stop, or daemon shuts down).
    """
    try:
        for raw in state.proc.stdout:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except Exception:
                # Some CLIs print non-JSON header lines. Keep them as raw text
                # so the user can see something even if the parser is wrong.
                state.append("agent", {"type": "raw", "text": line})
                continue
            for ev in _normalize_frame(state.agent_id, frame):
                state.append("agent", ev)
                # Capture the session id off the first init frame — needed
                # by /__run/:id/resume so post-Stop replies can rejoin the
                # same Claude conversation instead of starting fresh.
                if ev.get("type") == "status" and ev.get("sessionId") and not state.session_id:
                    state.session_id = ev["sessionId"]
                # Promote chat runs to "modifying" the first time the agent
                # actually touches a file. The lock is scoped to runs that
                # need it; ad-hoc chats (visualization, Q&A) don't freeze
                # the UI even though they're "active."
                if (not state.modifying
                        and ev.get("type") == "tool_use"
                        and ev.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit")):
                    state.modifying = True
                # Turn lifecycle tracking — distinct from process lifecycle.
                if ev.get("type") == "status":
                    if ev.get("label") in ("done", "error"):
                        state.turn_done = True
                        state.turns_completed += 1
                        # v2.24 + v2.26 — for node-agent dispatches: fire the
                        # canvas completion hook ONLY on `status: done`
                        # (genuine success). Status: error covers a wide range
                        # of cases including TRANSIENT mid-run errors the
                        # agent can recover from (tool retries, WebSearch
                        # returning nothing, single WebFetch failing) — those
                        # shouldn't terminate the subprocess or mark the node
                        # as failed. If the agent eventually emits `done`,
                        # we fire success then. If it just hangs or dies, the
                        # finally-block fallback below picks up the actual
                        # subprocess exit code as the verdict. (Reported by
                        # user: "The research run flipped to error but wrote
                        # an 8.2 KB research.md on disk.")
                        if (ev.get("label") == "done"
                                and getattr(state, "workflow_node_id", None)
                                and not getattr(state, "_node_completion_fired", False)):
                            try:
                                _fire_node_completion_hook(state, exit_code=0)
                            except Exception as _e:
                                state.append("status", {"label": "node-status-update-failed", "detail": str(_e)})
                            state._node_completion_fired = True
                            # Terminate the subprocess so the reader loop
                            # exits cleanly and we stop burning the open
                            # SSE/CLI session. v2.28 — tag the termination
                            # reason so finish() knows this was intentional;
                            # the SIGTERM exit code (143) shouldn't be
                            # reported as a failure to the chat UI.
                            state.stop_reason = "completed-orchestrator"
                            try: state.proc.terminate()
                            except Exception: pass
                    elif ev.get("label") == "starting":
                        state.turn_done = False
    finally:
        # Reader saw EOF on stdout — usually because the CLI emitted its
        # terminal stream-json frame and closed the pipe. But the
        # subprocess may still be alive doing post-turn cleanup (telemetry
        # flush, retry loops, etc). Escalate: wait briefly, then SIGTERM,
        # then SIGKILL, so we never leave a zombie that bills tokens
        # against a closed pipe. The old behavior (just `wait(timeout=5)`
        # then move on) is exactly what produced the "done=True,
        # exit_code=None, CLI still running for 45 min" pattern.
        exit_code = None
        try:
            exit_code = state.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try: state.proc.terminate()
            except Exception: pass
            try:
                exit_code = state.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try: state.proc.kill()
                except Exception: pass
                try: exit_code = state.proc.wait(timeout=3)
                except Exception: exit_code = state.proc.returncode
            except Exception:
                exit_code = state.proc.returncode
        except Exception:
            exit_code = state.proc.returncode
        # v2.28 — intentional terminations override the raw exit code so the
        # UI doesn't render "failed" for graceful SIGTERMs (v2.24 success
        # path, user-stop, etc.). The actual exitCode is still stored on the
        # event payload for diagnostics; finish() also stores stopReason so
        # the chat can render "done"/"stopped" correctly.
        if state.stop_reason in ("completed-orchestrator", "user-stop") and exit_code in (143, -15, None):
            effective_exit = 0
        else:
            effective_exit = exit_code or 0 if exit_code is not None else exit_code
        state.append("end", {"exitCode": exit_code, "effectiveExitCode": effective_exit, "stopReason": state.stop_reason})
        state.finish(effective_exit if state.stop_reason else exit_code)
        # ── v2.1 — workflow-node auto-completion hook ────────────────────
        # v2.24 — guarded by _node_completion_fired so we don't double-flip
        # when the turn_done branch above already called the hook. (The
        # turn_done path is the primary trigger now; this finally-block
        # version is a fallback for subprocesses that exit WITHOUT emitting
        # a "done" status frame — e.g. crashed mid-turn or got SIGKILLed.)
        wf_node_id = getattr(state, "workflow_node_id", None)
        if wf_node_id and state.project_root and not getattr(state, "_node_completion_fired", False):
            try:
                _fire_node_completion_hook(state, exit_code=exit_code or 0)
            except Exception as e:
                state.append("status", {"label": "node-status-update-failed", "detail": str(e)})
        # ── History snapshot — AFTER state ───────────────────────────────
        # The subprocess is gone. Diff what changed against the snapshot we
        # took at spawn and commit one atomic entry for the whole run. If
        # nothing changed (typical for pure-chat freeform turns), the entry
        # is dropped so the stack doesn't fill with empty rows.
        if getattr(state, "history_pending_id", None) and state.project_root:
            try:
                kind_label = f"Agent run: {state.title or state.kind or 'run'}"
                _history_run_snapshot_finish(
                    state.project_root,
                    state.history_pending_id,
                    state.history_before_paths or [],
                    state.history_before_rows  or [],
                    kind="run",
                    label=kind_label,
                    source="agent",
                    extra={
                        "agentId": state.agent_id,
                        "runKind": state.kind,
                        "runId": state.run_id,
                        "branch": state.branch,
                        "exitCode": exit_code,
                    },
                )
            except Exception as e:
                # Don't crash the run-finish path on history failure.
                state.append("status", {"label": "history-finalize-failed", "detail": str(e)})


def _drain_stderr(state: "RunState") -> None:
    # v3.5 — Codex emits its entire chat content on STDERR with a structured
    # plain-text protocol (banner / role markers / tool exec / tool result).
    # Route codex through a parser that converts those into agent events so
    # the chat UI renders text + tool calls properly instead of dumping
    # every line as a "STDERR" prefixed bubble. Claude (and unknown agents)
    # keep the legacy raw-stderr passthrough.
    if state.agent_id == "codex":
        parser = _CodexStderrParser()
        try:
            for raw in state.proc.stderr:
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                events, raw_passthrough = parser.feed(line)
                for ev in events:
                    state.append("agent", ev)
                for line_text in raw_passthrough:
                    state.append("agent", {"type": "text_delta", "delta": line_text + "\n"})
        except Exception:
            pass
        # End-of-stream flush — if the last tool didn't get a clean role
        # marker before stderr closed, surface its accumulated output now.
        try:
            tail = parser.finish()
            if tail:
                state.append("agent", tail)
        except Exception:
            pass
        return
    try:
        for raw in state.proc.stderr:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            if not line:
                continue
            state.append("stderr", {"text": line})
    except Exception:
        pass


class _CodexStderrParser:
    """Parse `codex exec` stderr output into normalised agent events.

    Codex's stderr is structured plain text. A typical run looks like:

        2026-06-09T07:39:36Z ERROR rmcp::transport::worker: …   ← noise
        OpenAI Codex v0.138.0                                    ← banner head
        --------
        workdir: /Users/.../projects/hyperpop                    ← banner body
        model: gpt-5.5
        sandbox: workspace-write
        --------
        user
        <user prompt body>                                       ← echoed prompt
        codex
        <assistant text body, possibly multi-line>
        exec
        /bin/zsh -lc "<command>" in <cwd>
        succeeded in 0ms

    We feed line-by-line; each feed() returns (events, raw_passthrough)
    where events are normalised agent dicts and raw_passthrough is a list
    of lines that didn't match any known marker (genuine errors etc.) —
    callers emit these as plain text_delta events.
    """
    _NOISE_PATTERNS = (
        # Codex's MCP transport spam when the local MCP socket can't bind.
        re.compile(r"rmcp::transport"),
        # Timestamp-prefixed log lines (Codex's tracing layer).
        re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\bERROR\b"),
        re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\bWARN\b"),
    )

    def __init__(self):
        self.state = "pre_banner"
        self.dashes_seen = 0
        self.tool_counter = 0
        self.current_tool_id = None

    def _is_noise(self, line: str) -> bool:
        for rx in self._NOISE_PATTERNS:
            if rx.search(line):
                return True
        return False

    # A bare lowercase token (with optional underscores) on its own line —
    # codex's marker pattern: "user", "codex", "exec", "apply_patch",
    # "read_file", "thinking", etc.
    _MARKER_RX = re.compile(r"^[a-z][a-z0-9_]*$")
    _ROLE_MARKERS = {"user", "codex", "thinking"}
    # Reserved bare-tokens that AREN'T tool names (handled separately).
    _RESERVED_NON_TOOL = {"user", "codex", "thinking"}
    # Status line: "succeeded in 0ms" / "failed in 200ms" / "exited 1 in 0ms"
    # — with optional trailing ":" when more output follows.
    _STATUS_RX = re.compile(r"^\s*(succeeded|failed|exited(?:\s+\d+)?)\s+in\s+\d+ms(:?)\s*$")

    def __init__(self):
        self.state = "pre_banner"
        self.dashes_seen = 0
        self.tool_counter = 0
        self.current_tool_id = None
        self._pending_tool_name = None
        # Accumulator for the current tool call's output (lines between
        # the command line and the next role/tool marker).
        self._tool_output_lines: list = []
        # The last status line we saw for the current tool (succeeded /
        # failed / exited). Folded into the tool_result content on flush.
        self._tool_status: str = ""

    def _flush_tool(self) -> dict:
        """Emit a tool_result event for the currently-open tool call, if any.
        Returns the event dict or None. Resets accumulator state."""
        if self.current_tool_id is None:
            return None
        body = "\n".join(self._tool_output_lines).rstrip()
        if self._tool_status and body:
            text = self._tool_status + "\n" + body
        elif self._tool_status:
            text = self._tool_status
        else:
            text = body or "(no output)"
        is_error = bool(self._tool_status) and (
            "failed" in self._tool_status or "exited" in self._tool_status
        )
        ev = {
            "type": "tool_result",
            "id": self.current_tool_id,
            "content": [{"type": "text", "text": text}],
            "is_error": is_error,
        }
        self.current_tool_id = None
        self._pending_tool_name = None
        self._tool_output_lines = []
        self._tool_status = ""
        return ev

    def feed(self, line: str):
        events: list = []
        raw: list = []
        if self._is_noise(line):
            return events, raw
        # Banner traversal — strip every line between the two `--------`
        # separators (inclusive of header + dashes), then switch to content.
        if self.state == "pre_banner":
            if not line.strip():
                return events, raw
            if line.startswith("OpenAI Codex"):
                return events, raw
            if line.startswith("---"):
                self.dashes_seen = 1
                self.state = "in_banner"
                return events, raw
            # Some Codex versions don't print the header; fall through.
            self.state = "post_banner"
        if self.state == "in_banner":
            if line.startswith("---"):
                self.dashes_seen += 1
                if self.dashes_seen >= 2:
                    self.state = "post_banner"
            return events, raw
        stripped = line.strip()
        # Status line for the open tool call — capture the marker, don't
        # close the tool yet (more output may follow when it ends with ":").
        if self.current_tool_id is not None:
            m_st = self._STATUS_RX.match(line)
            if m_st:
                self._tool_status = stripped.rstrip(":").strip()
                # If the status line ended with ":", subsequent non-marker
                # lines are tool output (continued). If not, the tool is
                # done; we wait for the next role marker to flush.
                return events, raw
        # Role / tool markers — bare lowercase tokens on their own line.
        # A marker flushes any open tool first (so its output ends up in
        # the right tool_result and doesn't bleed into the next event).
        if stripped and self._MARKER_RX.match(stripped):
            if stripped in self._ROLE_MARKERS:
                ev = self._flush_tool()
                if ev:
                    events.append(ev)
                if stripped == "user":
                    self.state = "user"
                elif stripped == "codex":
                    self.state = "codex"
                else:  # thinking
                    self.state = "thinking"
                return events, raw
            if stripped not in self._RESERVED_NON_TOOL:
                # New tool starting — flush previous, open new.
                ev = self._flush_tool()
                if ev:
                    events.append(ev)
                self.tool_counter += 1
                self.current_tool_id = f"codex-{stripped}-{self.tool_counter}"
                self._pending_tool_name = stripped
                self.state = "tool_pending_input"
                return events, raw
        # Per-state content handling.
        if self.state == "user":
            # We already know what we sent; skip the echo.
            return events, raw
        if self.state == "codex":
            if not line.strip():
                return events, raw
            events.append({"type": "text_delta", "delta": line + "\n"})
            return events, raw
        if self.state == "thinking":
            if not line.strip():
                return events, raw
            events.append({"type": "thinking_delta", "delta": line + "\n"})
            return events, raw
        if self.state == "tool_pending_input":
            # First line after the tool name is the input (command for
            # exec, patch header for apply_patch, etc.). Emit tool_use and
            # then accumulate following lines as the tool's output.
            tool_name = self._pending_tool_name or "tool"
            events.append({
                "type": "tool_use",
                "id": self.current_tool_id,
                "name": tool_name,
                "input": {"text": line},
            })
            self.state = "tool_body"
            return events, raw
        if self.state == "tool_body":
            # Tool's stdout/stderr — accumulate, do NOT emit as text.
            # Flushed into tool_result when the next marker arrives.
            self._tool_output_lines.append(line)
            return events, raw
        # Fallback for post_banner with no active context — likely an
        # assistant continuation Codex didn't mark explicitly. Treat as text.
        if line.strip():
            events.append({"type": "text_delta", "delta": line + "\n"})
            return events, raw
        return events, raw

    def finish(self):
        """Called when the run ends — flush any still-open tool call."""
        return self._flush_tool()


# ── Prompt composer ──────────────────────────────────────────────────────────
# The agent's stdin is fed Claude-style stream-json `user` frames so we can
# inject follow-up messages mid-run (forms, clarifications). For Phase 1 we
# only ever send the initial prompt; later phases add `/__run/:id/user-message`
# for the form-answer round-trip described in §2.3 of the migration plan.

def _claude_user_frame(text: str) -> bytes:
    return (json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    }) + "\n").encode("utf-8")


def _claude_tool_result_frame(tool_use_id: str, content: str, is_error: bool = False) -> bytes:
    """Synthesize a Claude stream-json `user` frame containing a `tool_result`
    content block. Used by /__run/:id/tool-result so the UI can answer
    AskUserQuestion (and any other agent-side tool prompt) without going
    through the agent's text channel."""
    part = {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}
    if is_error:
        part["is_error"] = True
    return (json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [part]},
    }) + "\n").encode("utf-8")


# Trigger-file → prompt template. Lifted from §9.2.C "Impact C — Phase 1's
# submit() generalises to a triggerRun() over all serve.py allowlisted files".
# Workflow names are stable repo paths; the agent reads them with Read.
TRIGGER_PROMPTS = {
    "edits-apply": (
        "Apply edits.json. Follow docs/agents/workflows/2-edits.md verbatim. "
        "After applying, summarise what changed and which files were touched. "
        "Do NOT delete edits.json until every edit has succeeded."
    ),
    "regenerate": (
        "Run Workflow 1 (regenerate). "
        "Read docs/agents/workflows/1-regenerate.md for the architecture. "
        "Read docs/agents/orchestrator.md as your orchestrator playbook. "
        "Read docs/agents/conventions.md before dispatching any subagent. "
        "Whenever you write into editor/data.js, follow "
        "docs/agents/data-schema.md.\n\n"
        "Render-check (Step 4f): no screenshot tool is wired in this version — "
        "surface 'render check skipped — no screenshot tool available' in your report."
    ),
    "statemachine-request": (
        "Run Workflow 1 with `overrides.stateMachine: true`. "
        "Read docs/agents/orchestrator.md and docs/agents/subagents/8-state-machine.md."
    ),
    "timeline-request": (
        "Run Workflow 1 with `overrides.timeline: true`. "
        "Read docs/agents/orchestrator.md and docs/agents/subagents/9-timeline.md."
    ),
    "grid-request": (
        "Run Workflow 1 with `overrides.grids: true`. "
        "Read docs/agents/orchestrator.md and docs/agents/subagents/10-grids.md."
    ),
    "freeform": "{prompt}",
}


def _compose_initial_prompt(kind: str, user_prompt: str = "") -> str:
    template = TRIGGER_PROMPTS.get(kind) or TRIGGER_PROMPTS["freeform"]
    return template.format(prompt=user_prompt or "").strip()


# ── question-form protocol ──────────────────────────────────────────────────
# Claude Code's built-in AskUserQuestion is disabled in this environment (see
# AGENT_DEFS["claude"]["args"] — `--disallowedTools AskUserQuestion`) because
# in `-p --input-format stream-json` mode it has no TTY to bind to. The CLI's
# runtime auto-completes the call as "dismissed" before our /__run/:id/tool-
# result POST can land, so any answer the user clicks loses the race.
#
# Replacement: append a system prompt instructing the model to emit a
# <question-form>...</question-form> block at the END of its turn when it
# genuinely needs a clarifying answer, then stop. The agent's turn ends
# naturally (no race), the UI renders the form as clickable buttons, and
# the user's pick is POSTed to /__run/:id/user-message — same channel as
# the composer, so the agent resumes via the existing stdin path.
QUESTION_FORM_SYSTEM_PROMPT = """\
## Chat rendering capabilities

This conversation is NOT a terminal. The chat surface renders rich content \
inline. When the user asks for a quick visualization, demo, chart, mockup, \
illustration, or sample (i.e. "show me…", "draw…", "preview…", "what does X \
look like", "give me an example of…"), respond DIRECTLY in chat using the \
renderers below. **Do NOT scaffold a prototype in `source/<branch>/`** for \
ad-hoc visuals — that path is reserved for actual multi-page navigable apps \
the user explicitly asks you to build via the prototype/regenerate workflow.

Available renderers (use the appropriate one for the task):

1. **Markdown tables** — `| Col | Col |` with a `|---|---|` separator.
2. **Fenced ```html blocks** — full HTML + inline `<style>` + `<script>`. \
Rendered inside a sandboxed iframe (`allow-scripts` only — null origin, no \
access to the parent page). Use this for any interactive mockup, styled \
card, layout sketch, **CSS animations** (`@keyframes`), or any markup with \
DOM event handlers (`onclick`, `onmousemove`, `onscroll`, hover via `:hover`).
3. **Fenced ```svg blocks** — vector graphics, icons, diagrams, charts, \
illustrations. Rendered in the same sandboxed iframe. SVG events work too.
4. **Fenced ```mermaid blocks** — `graph LR`, `sequenceDiagram`, `flowchart`, \
`erDiagram`, etc. Rendered as SVG via mermaid.js.
5. **Fenced ```glsl / ```shader blocks** — fragment-shader playground in the \
shadertoy style. Write a `void mainImage(out vec4 fragColor, in vec2 fragCoord)` \
function with these uniforms available:
   - `uniform vec3 iResolution;` (viewport in pixels)
   - `uniform float iTime;` (seconds since start)
   - `uniform vec4 iMouse;` (xy = current pos, zw = last click)
The host wires up WebGL, a full-screen quad, the animation loop, and mouse \
tracking. The user can move/click on the canvas and the shader receives \
`iMouse` updates immediately.
6. **Fenced ```three / ```webgl blocks** — three.js sandbox. Globals \
exposed: `THREE`, `scene`, `camera`, `renderer`. Call `__animate(t => …)` \
to register a per-frame callback (receives elapsed seconds). The renderer \
canvas is already mounted; raycasting, hover, click, scroll-zoom all work \
via the standard three.js patterns.
7. **Fenced ```p5 blocks** — p5.js sketch. Define `setup()` and `draw()` \
at top level, or instance mode `function sketch(p) {{ … }}`. `mousePressed`, \
`mouseMoved`, `keyPressed`, `mouseWheel` etc. all bind as usual.
8. **Inline color values** — `#hex`, `rgb()`, `rgba()`, `hsl()`, `oklch()`, \
`oklab()`, `linear-gradient(...)`, `radial-gradient(...)`. The chat auto-decorates \
each with a swatch. Just write the value as prose — no fencing needed.
9. **Inline image URLs** — any `https://…/foo.png|jpg|webp|gif|svg|avif` URL \
auto-renders as a thumbnail.
10. **Inline font URLs** — any `https://…/foo.woff2|woff|ttf|otf` URL \
auto-renders as a `Aa Bb 123` sample in that font.
11. **Bare `<svg>...</svg>`** inside prose — picked up and rendered the same \
way as a fenced svg block.

All sandboxed previews (html/svg/shader/three/p5) are **fully interactive**: \
click, mouse position, scroll, hover, keyboard — they all work because the \
iframe has `allow-scripts`. The sandbox guarantees null-origin isolation so \
your code can't reach the host page; it just can't.

Pick the lightest renderer that does the job. A 3-row Markdown table beats a \
fenced HTML block. A `#hex` chip beats a fenced ```html block with `<div \
style="background:#hex">`. A simple SVG icon beats a three.js scene. Use \
the heavy hitters (shader / three / p5) when you genuinely need WebGL or \
canvas animation.

When in doubt: render in chat. Only write to `source/` when the user said the \
word "prototype" or "branch" or asked for something multi-page.

**Exception — visual ASSETS go through visual-orchestrator.** The chat-rendering \
rules above are for visualizations the user wants to *see in conversation* \
("show me a chart of X", "draw what a Bauhaus poster looks like", \
"preview an oklch palette"). When the user asks you to *create / produce / \
generate / add* an image, illustration, mascot, character, icon, mark, \
shader, particle field, 3D scene, lottie animation, or video that should \
land on the workflow canvas as an asset — even if it's "just one" — you do \
NOT render it inline as a fenced block. You dispatch \
`Task(subagent_type: "visual-orchestrator", …)` as your first action. See the \
"Image creation: dispatch visual-orchestrator FIRST" rule in the capabilities \
section below for the exact decision table.

## Prototype folder convention (v3.2 — multi-prototype)

`source/` is a CONTAINER for many independent prototypes, not a single workspace. \
Every prototype lives in its own subfolder: `source/<slug>/`. The bare `source/` \
root is reserved for project-level artefacts (PRD, research notes, coherence \
contracts) — **never** write `source/index.html` or any page directly under it.

When the user asks you to build something:

1. **List existing prototypes first.** Run `ls source/` (or `Bash` with that \
command) to see which `<slug>/` folders already contain `index.html`. Show the \
user a one-line summary ("Existing prototypes: `wizard-app/`, `landing-v1/`") \
before you start writing.

2. **Pick the right slug.**
   - If the user said "extend / iterate on / fix the X one" and `source/X/` \
     exists, write into that folder.
   - If the user said "another one / a new one / a variant" — or if no \
     existing prototype matches the brief — derive a NEW kebab-case slug from \
     the brief (1–3 words, e.g. `wizard-onboarding`, `notes-app`, \
     `landing-v2`). Confirm the slug with the user in one sentence: \
     "I'll scaffold this as `source/<slug>/` — say so if you want a different \
     name." Then proceed without waiting (unless they push back).
   - If the user named a slug explicitly ("call it `studio`"), use it verbatim.

3. **Never overwrite an existing prototype without explicit confirmation.** If \
`source/<slug>/index.html` exists and the brief sounds like a fresh start, ask \
via a `<question-form>` whether to overwrite OR pick a new slug — do not \
silently clobber the previous prototype's work.

4. **Every file the prototype needs goes under its `<slug>/` root** — \
`source/<slug>/index.html`, `source/<slug>/styles.css`, \
`source/<slug>/images/hero.png`, sub-pages at `source/<slug>/about/index.html`, \
etc. The workflow canvas's prototype node iframe loads \
`/source/<slug>/` directly, so anything outside that subtree is invisible to \
the prototype.

5. **Multi-page apps** are sub-folders WITHIN the prototype, e.g. \
`source/<slug>/dashboard/index.html`, `source/<slug>/settings/index.html`. \
The slug folder is the application root; the sub-folders are its pages.

This convention is what makes the "branch" model work: the user can drag \
multiple Prototype nodes onto the same workflow canvas and each renders a \
different `source/<slug>/` in parallel. Writing to bare `source/` collapses \
that into a single global prototype and destroys whatever was there before.

## Question-form protocol

When you need a focused answer from the user before continuing (a fork in the \
plan, a missing requirement, a choice between options), emit ONE \
<question-form>...</question-form> block at the END of your turn, then STOP. \
Do not call the AskUserQuestion tool — it is disabled in this environment. \
Do not keep working after the form. The chat composer is the only way for the \
user to reply; your form will be rendered as clickable buttons and the \
answers come back as a regular user message.

Syntax (the JSON inside must parse — do not wrap it in code fences):

<question-form id="<short-stable-id>">
{
  "questions": [
    {
      "header": "<≤2-word chip>",
      "question": "<one clear sentence>",
      "multiSelect": false,
      "options": [
        { "label": "<display>", "description": "<optional one-liner>" }
      ]
    }
  ]
}
</question-form>

Rules:
- Use only when the answer materially affects what you do next. If a \
reasonable default exists, just proceed without asking.
- 1–4 questions per form, never more. 2–5 concrete options per question; no \
free-text questions in this protocol.
- The form MUST be the FINAL block of your turn. Do not call any tool after \
emitting it. Do not write any text after the closing </question-form> tag.
- After the user replies, treat their message as the answer to your form and \
continue with the agreed plan.
"""


# Appended to QUESTION_FORM_SYSTEM_PROMPT only in workspace mode (Phase 6).
# Tells the agent that its cwd is the active project and that protocol docs
# live at a separate mount, added via --add-dir. In single-project mode the
# two roots coincide and this paragraph is a no-op, so we skip it to save
# input tokens.
WORKSPACE_LAYOUT_PROMPT = """

## Workspace layout

Your cwd is the active project's root. Project-scoped artifacts live here \
and you read/write them via relative paths:

- `source/` — prototype source (HTML, CSS, JS, prototype.json, …)
- `editor/data.js` — editor data file for this project (window.EDITOR_DATA)
- `DESIGN.md`, `NOTES.md`, `edits.json` — per-project docs and ephemeral \
handoff files

The **agent protocol** — the shared playbook every project follows — lives \
at a separate read-only mount, exposed to you via `--add-dir $TH_PROTOCOL_ROOT`. \
Read it from there; do NOT copy these files into the project:

- `AGENTS.md` — entry point + workflow index
- `PROTOTYPE.md` — design skill
- `docs/agents/**` — workflows, subagents, orchestrator, conventions, data-schema

Useful env vars set on every spawn: `TH_PROJECT_ROOT` (your cwd as an \
absolute path), `TH_PROTOCOL_ROOT` (the shared protocol mount), \
`TH_PROJECT_ID` (the workspace id of the active project).
"""


# Env vars Claude Code Desktop / IDE plugins leak into child processes that
# break standalone `claude` invocations. Symptoms:
#   • ANTHROPIC_API_KEY="" — CLI sees "API key is set", sends `Authorization:
#     Bearer ` with empty bearer ⇒ 401 invalid credentials.
#   • CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=1 — CLI defers auth to the host
#     process (the desktop app). Once we fork outside that host, nothing
#     answers the auth probe ⇒ retry loop.
#   • CLAUDE_CODE_SESSION_ID / CLAUDE_CODE_ENTRYPOINT / CLAUDE_CODE_EXECPATH —
#     identify the parent process; carrying them into a sibling spawn
#     confuses telemetry and pins to the bundled in-app binary.
# Strip them so the spawned child falls through to its own OAuth credentials
# (populated by `claude login` in a plain terminal). Users who *want* to pass
# through an API key can set TH_PRESERVE_CLAUDE_ENV=1 on the daemon.
_HOST_LEAK_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_SDK_HAS_OAUTH_REFRESH",
    "CLAUDE_AGENT_SDK_VERSION",
    "CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES",
    "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL",
    "CLAUDE_CODE_DISABLE_CRON",
)


# ── harness settings auto-install ──────────────────────────────────────────
# v3.1.2 — Called from every spawn site (and from __main__ at boot). Ensures
# `.claude/settings-harness.json` exists with the correct PreToolUse hook
# registration BEFORE we hand --settings to the spawned `claude`. Idempotent:
# generates the file if missing, leaves it alone if present and well-formed.
# This is what makes the visual-orchestrator enforcement self-installing — no
# user step required beyond running the daemon.
def _ensure_harness_settings() -> "str | None":
    """Generate INSTALL_ROOT/.claude/settings-harness.json on demand and
    return its absolute path. Returns None if the hook script itself is
    missing (in which case spawn sites silently skip --settings — the
    enforcement is unavailable but the daemon keeps working).

    The hook is the per-family orchestrator gate (require-orchestrator.sh) — it
    routes by file path: simulations/ → simulation-orchestrator, interactives/
    → interactive-media-orchestrator, narratives/ → narrative-experience-orchestrator,
    and the visual binary slots elsewhere → visual-orchestrator. Renamed from
    the legacy require-visual-orchestrator.sh in v3.6 when sim/im/nx orchestrators
    landed."""
    hook_path     = os.path.join(INSTALL_ROOT, ".claude", "hooks",
                                  "require-orchestrator.sh")
    settings_path = os.path.join(INSTALL_ROOT, ".claude",
                                  "settings-harness.json")
    if not os.path.isfile(hook_path):
        # Hook script absent — nothing to register. Spawn sites get None
        # and skip --settings; visual-orchestrator gating is unavailable but
        # the daemon stays functional.
        return None
    # Build the canonical config every time so we self-heal if a stale or
    # broken file sits there from a prior daemon version.
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks":   [{"type": "command", "command": hook_path}],
                }
            ]
        }
    }
    # Short-circuit if the file already matches — avoid disk churn at every
    # spawn (a typical session triggers many spawns).
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            if json.load(f) == settings:
                return settings_path
    except (OSError, ValueError):
        pass  # missing or unparseable — regenerate below
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        # Surface but don't crash — visual-orchestrator gating becomes
        # advisory-only, which is the same fail-mode as a missing hook.
        print(f"  [harness] failed to write {settings_path}: {e}", flush=True)
        return None
    return settings_path


def _ensure_sanitised_codex_home():
    """Build a Woven-managed CODEX_HOME that gives codex its auth + config
    but hides user-level skills.

    Why: codex CLI has no `--disable-skills` equivalent of Claude's
    `--disable-slash-commands`. User skills live in ~/.codex/skills/ and
    are auto-loaded whenever codex's matcher fires. Inside the Woven
    harness we want only the harness-supplied skill context — letting
    user skills like prototype-drawing leak in mixes vocabularies and
    breaks the source-agnostic pipeline guarantee.

    Strategy: create `<INSTALL_ROOT>/.codex-home/` once at boot. Symlink
    every entry from the user's real ~/.codex/ into it EXCEPT `skills/`.
    Codex reads auth.json / config.toml / sessions/ etc. through the
    symlinks (login persists, sessions accumulate). It looks for skills
    inside CODEX_HOME/skills/ — which doesn't exist in our dir — and
    finds none.

    Re-runs are idempotent: existing symlinks are validated; if the user
    added new top-level entries to ~/.codex/ since boot they're picked
    up the next time this is called. If the user has no ~/.codex/ yet
    (codex never run), we return None and the caller falls back to the
    default CODEX_HOME (which also has no skills, so harmless).

    Returns the absolute path to the sanitised home, or None on failure.
    """
    real_home = os.path.expanduser("~/.codex")
    if not os.path.isdir(real_home):
        # User hasn't run codex yet; nothing to gate. Codex will pick its
        # own default ($HOME/.codex), which won't have skills either.
        return None
    sanitised = os.path.join(INSTALL_ROOT, ".codex-home")
    try:
        os.makedirs(sanitised, exist_ok=True)
    except Exception:
        return None
    # Re-link any entries that have appeared in the user's real ~/.codex/
    # since last run, and replace any broken/stale links.
    try:
        for name in os.listdir(real_home):
            if name == "skills":
                # The whole point — never link skills/.
                continue
            src = os.path.join(real_home, name)
            dst = os.path.join(sanitised, name)
            # If dst exists and is a symlink, validate it points to src.
            if os.path.islink(dst):
                try:
                    if os.readlink(dst) == src:
                        continue
                except OSError:
                    pass
                try: os.unlink(dst)
                except OSError: pass
            elif os.path.exists(dst):
                # Non-symlink (file or dir) already there — leave it
                # untouched; the user may have customised this slot.
                continue
            try:
                os.symlink(src, dst)
            except OSError:
                # Cross-filesystem or permission issue; skip this entry.
                continue
    except Exception:
        # If we can't introspect ~/.codex/, fall back to leaving
        # CODEX_HOME unset; codex will use its default and we accept the
        # user-skill leak rather than crashing the spawn.
        return None
    return sanitised


def _build_child_env(agent_id: str, run_id: str, project_root: str = None, project_id: str = None) -> dict:
    env = dict(os.environ)
    preserve = (os.environ.get("TH_PRESERVE_CLAUDE_ENV") or "").strip()
    if not preserve or preserve == "0":
        for k in _HOST_LEAK_ENV_VARS:
            # Only strip empty / 0 / 1 values that are clearly host-leaks.
            # If the user set ANTHROPIC_API_KEY to a real key in their shell,
            # leave it alone — they explicitly want API-key auth.
            v = env.get(k)
            if v is None:
                continue
            if k == "ANTHROPIC_API_KEY":
                # Strip empty or whitespace-only; preserve real keys.
                if not v.strip():
                    env.pop(k, None)
                continue
            if k == "ANTHROPIC_AUTH_TOKEN":
                if not v.strip():
                    env.pop(k, None)
                continue
            # Host-management hints — always strip; the desktop host isn't
            # answering on the other end of this spawn.
            env.pop(k, None)
    env.update({
        "TH_DAEMON_URL": f"http://127.0.0.1:{PORT}",
        "TH_RUN_ID": run_id,
        "TH_AGENT": agent_id,
        # Phase 6 — let skill blocks resolve project paths without inferring
        # from cwd. TH_PROTOCOL_ROOT is the shared-protocol mount (AGENTS.md,
        # docs/agents/**) added to the agent's context via --add-dir.
        "TH_PROJECT_ROOT": project_root or DEFAULT_PROJECT_ROOT,
        "TH_PROTOCOL_ROOT": INSTALL_ROOT,
    })
    # v3.1 — Skill isolation. The earlier approach of overriding
    # CLAUDE_CONFIG_DIR broke macOS Keychain auth (different userID
    # generated → Keychain tokens unreachable). The correct mechanism is
    # the `--disable-slash-commands` CLI flag (added to spawn_args at
    # dispatch time, see _spawn_node_agent and freeform spawn paths).
    # That flag hides the user's ~/.claude/commands/ slash commands
    # WITHOUT touching CLAUDE_CONFIG_DIR, so Keychain auth keeps working.
    # No env override needed here.
    # v3.5 — Codex equivalent. Codex CLI has no `--disable-skills` flag,
    # so we sanitise CODEX_HOME instead: point it at a Woven-managed dir
    # that symlinks everything from the user's real ~/.codex/ EXCEPT the
    # `skills/` subtree. Codex still finds its auth, config, and sessions
    # via the symlinks (login persists), but its skill matcher finds no
    # user-level skills like prototype-drawing / grill-me / emil-design-eng.
    # Only the harness preamble (TH_PROTOCOL_ROOT + the prompt we ship)
    # drives the agent.
    if agent_id == "codex":
        sanitised = _ensure_sanitised_codex_home()
        if sanitised:
            env["CODEX_HOME"] = sanitised
    if project_id:
        env["TH_PROJECT_ID"] = project_id
    # If the user configured an Anthropic API key in the editor's Settings
    # (media-config.json) and didn't already inject one via shell env,
    # forward it to the Claude CLI so it bills against API credits instead
    # of the Pro/Max 7-day session quota. Without this the CLI authenticates
    # via OAuth — which is what gets throttled by the "seven_day allowed_warning"
    # we see at high build volumes. With it, the CLI sets
    # `Authorization: Bearer <key>` on every API call and uses pay-as-you-go.
    # Only injected for the claude agent; other agents have their own auth.
    if agent_id == "claude" and not env.get("ANTHROPIC_API_KEY"):
        try:
            from_cfg = _resolve_provider_key("anthropic")
        except Exception:
            from_cfg = None
        if from_cfg:
            env["ANTHROPIC_API_KEY"] = from_cfg
    return env


def _default_run_title(kind: str, body: dict) -> str:
    meta = body.get("meta") or {}
    if kind == "edits-apply":
        n = meta.get("editCount")
        ann = meta.get("annotationCount")
        bits = []
        if n is not None:
            bits.append(f"{n} edit{'' if n == 1 else 's'}")
        if ann:
            bits.append(f"{ann} annotation{'' if ann == 1 else 's'}")
        return f"Applying {', '.join(bits) or 'edits'}"
    if kind == "regenerate":
        return "Regenerating"
    if kind.endswith("-request"):
        return f"View request ({kind.replace('-request', '')})"
    snippet = (body.get("prompt") or "").strip().splitlines()
    return (snippet[0][:60] + "…") if snippet and len(snippet[0]) > 60 else (snippet[0] if snippet else "Run")


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        # `directory=INSTALL_ROOT` is mostly a fallback — translate_path()
        # below routes every request manually based on path + ?project= so
        # the per-tier (install / project) split works in workspace mode.
        super().__init__(*a, directory=INSTALL_ROOT, **kw)

    # ── URL → filesystem routing (Phase 6) ───────────────────────────────
    # Three tiers:
    #   • editor binary + protocol docs (shared) → INSTALL_ROOT
    #     paths: /editor/{app.js,styles.css,index.html,serve.py,serve.command,
    #            ...everything except branches/ and data.js},
    #            /AGENTS.md, /PROTOTYPE.md, /docs/**
    #   • per-project data file + branch data → project_root
    #     paths: /editor/data.js, /editor/branches/**
    #   • per-project sources + docs → project_root
    #     paths: /source/**, /DESIGN.md, /NOTES.md, /MERGES.md, /prototype.json,
    #            and anything else not matched above
    #
    # Single-project mode (no TH_WORKSPACE_DIR): project_root == INSTALL_ROOT
    # so every tier resolves to the same place — exact pre-Phase-6 behavior.
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        raw = urllib.parse.unquote(parsed.path)
        norm = raw.lstrip("/")
        if not norm:
            # Leave the default mapping to INSTALL_ROOT so SimpleHTTPRequestHandler
            # can do its directory-index lookup; do_GET issues a 301 to /editor/
            # for bare `/` before this is consulted, so this fallback only fires
            # for HEAD-style probes.
            return INSTALL_ROOT
        parts = [seg for seg in norm.split("/") if seg and seg != "."]
        if any(seg == ".." for seg in parts):
            # Path traversal — return a definitely-missing path so the parent
            # 404s the request cleanly instead of leaking outside any root.
            return os.path.join(INSTALL_ROOT, "____invalid____")
        qs = urllib.parse.parse_qs(parsed.query)
        # In workspace mode, when the request URL has no `?project=` (typical
        # for relative loads inside an iframe — browsers strip query strings
        # when resolving relative URLs), fall back to the Referer header so
        # `<img src="./logo.png">` inside `/source/main/?project=test-harness`
        # still loads from the test-harness project, not whichever project
        # `_first_project_id()` returns. Without this, alphabetically-earlier
        # projects silently serve every other project's assets.
        if WORKSPACE_DIR and not _qs_get(qs, "project"):
            referer = self.headers.get("Referer", "")
            if referer:
                try:
                    ref_q = urllib.parse.parse_qs(urllib.parse.urlparse(referer).query)
                    rp = _qs_get(ref_q, "project")
                    if rp:
                        qs = {**qs, "project": [rp]}
                except Exception: pass
        try:
            project_root = resolve_project_root(qs)
        except ValueError:
            project_root = DEFAULT_PROJECT_ROOT
        # Per-project data first (more-specific match before /editor/ catch-all).
        if parts[:2] == ["editor", "branches"]:
            return os.path.join(project_root, *parts)
        if parts == ["editor", "data.js"]:
            # v3.1 — lazy migration: if editor/data.js is the old bootstrap
            # shim (defines EDITOR_BRANCHES + document.write's branches/main.js)
            # and editor/branches/main.js exists, replace data.js with that
            # file's content so the browser gets EDITOR_DATA directly. Idempotent:
            # once data.js carries EDITOR_DATA, subsequent calls skip the rewrite.
            try:
                _v31_migrate_data_js(project_root)
            except Exception as e:
                print(f"[v3.1 migrate] {project_root}: {e}", flush=True)
            # Per-prototype data routing. A project hosting multiple prototypes
            # (e.g. demo-inhouse has source/main/ + source/main2/) needs its
            # OWN frames + sourceRoot + entries per prototype. The editor URL
            # carries ?prototype=<slug> (legacy: ?branch=<slug>) when launched
            # from a starred prototype star or a canvas-frames node. If
            # editor/<slug>.data.js exists, serve THAT instead of the project-
            # level editor/data.js. Falls back transparently to editor/data.js
            # so single-prototype projects (and pre-migration projects whose
            # per-prototype files don't exist yet) keep working unchanged.
            proto_slug = _qs_prototype(qs, default="").strip()
            # Reject malformed slugs and traversal attempts. Flat slugs only —
            # nested prototypes (`<name>/<sub>`) still resolve to editor/data.js
            # for now; per-prototype data.js doesn't support the nested form.
            if proto_slug and re.match(r"^[A-Za-z0-9_.-]{1,80}$", proto_slug):
                per_proto = os.path.join(project_root, "editor", f"{proto_slug}.data.js")
                if os.path.isfile(per_proto):
                    return per_proto
            return os.path.join(project_root, *parts)
        # Per-project layout sidecar — editor/<slug>.layout.js. Written by
        # /__layout, loaded by index.html before app.js so positions + grid
        # meta survive reload.
        if len(parts) == 2 and parts[0] == "editor" and parts[1].endswith(".layout.js"):
            return os.path.join(project_root, *parts)
        # Editor binary (shared).
        if parts[:1] == ["editor"]:
            return os.path.join(INSTALL_ROOT, *parts)
        # Protocol docs (shared).
        if parts[:1] == ["docs"] or parts in (["AGENTS.md"], ["PROTOTYPE.md"]):
            return os.path.join(INSTALL_ROOT, *parts)
        # Per-project sources + per-project docs (DESIGN.md, NOTES.md,
        # prototype.json, MERGES.md, FORK_REQUEST.md, edits.json, ...).
        return os.path.join(project_root, *parts)

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        # v2.50 — stamp every POST with a short correlation id so logs on
        # both sides can be matched. _reply() picks this up and writes both
        # an X-Request-Id header and a requestId field in the JSON body.
        self.request_id = _new_request_id()
        self._post_started_at = time.time()
        try:
            if parsed.path == "/__save":
                return self._save(qs)
            # v3.1 — /__branch, /__promote, /__promote_frame removed.
            # Stubs at _branch_create / _branch_promote / _frame_promote still
            # return 410 for any stale client that hits them directly, but the
            # routes here are deleted so the do_POST table reads cleanly.
            if parsed.path == "/__layout":
                return self._layout_save(qs)
            if parsed.path == "/__workflow":
                return self._workflow_save(qs)
            if parsed.path == "/__design_system":
                return self._design_system_save(qs)
            if parsed.path == "/__ds_proposals":
                return self._ds_proposals_save(qs)
            if parsed.path == "/__upload_font":
                return self._upload_font_post(qs)
            if parsed.path == "/__orchestrators/disable":
                return self._orchestrators_disable(qs)
            if parsed.path == "/__cc_skills/upload":
                return self._cc_skills_upload()
            if parsed.path == "/__cc_skills/delete":
                return self._cc_skills_delete()
            if parsed.path == "/__media_config":
                return self._media_config_set()
            if parsed.path == "/__media_config/test":
                return self._media_config_test(qs)
            if parsed.path == "/__asset_generate":
                return self._asset_generate(qs)
            if parsed.path == "/__llm_run":
                return self._llm_run(qs)
            if parsed.path == "/__dispatch_planner":
                return self._dispatch_planner(qs)
            if parsed.path == "/__attachment":
                return self._attachment_upload(qs)
            if parsed.path == "/__write_text":
                return self._write_text(qs)
            if parsed.path == "/__html_save":
                return self._html_save(qs)
            if parsed.path == "/__starred_prototypes/toggle":
                return self._starred_prototypes_toggle(qs)
            if parsed.path == "/__thumbnail_prototype/set":
                return self._thumbnail_prototype_set(qs)
            if parsed.path == "/__component_export":
                return self._component_export(qs)
            if parsed.path == "/__copy_file":
                return self._copy_file(qs)
            if parsed.path == "/__replace_exposed_svg":
                return self._replace_exposed_svg(qs)
            if parsed.path == "/__rewrite_img_src":
                return self._rewrite_img_src(qs)
            if parsed.path == "/__rewrite_element_for_kind":
                return self._rewrite_element_for_kind(qs)
            if parsed.path == "/__native_folder_picker":
                return self._native_folder_picker()
            if parsed.path == "/__export_config":
                return self._export_config_set(qs)
            if parsed.path == "/__export_asset":
                return self._export_asset(qs)
            if parsed.path == "/__mkdir":
                return self._mkdir(qs)
            if parsed.path == "/__rmdir":
                return self._rmdir(qs)
            if parsed.path == "/__rename_dir":
                return self._rename_dir(qs)
            if parsed.path == "/__screenshot":
                return self._screenshot_create(qs)
            m_ss = re.match(r"^/__screenshot/jobs/([0-9a-f]{6,64})/result$", parsed.path)
            if m_ss:
                return self._screenshot_result(m_ss.group(1))
            if parsed.path == "/__upload":
                return self._upload_files(qs)
            m_up = re.match(r"^/__upload/delete$", parsed.path)
            if m_up:
                return self._upload_delete(qs)
            if parsed.path == "/__local_install":
                return self._local_install()
            if parsed.path == "/__assets/delete":
                return self._asset_delete(qs)
            if parsed.path == "/__prompts":
                return self._prompt_save(qs)
            m = re.match(r"^/__prompts/([a-z0-9][a-z0-9-]{0,60})/delete$", parsed.path)
            if m:
                return self._prompt_delete(qs, m.group(1))
            if parsed.path == "/__projects/new":
                return self._project_create(qs)
            if parsed.path == "/__projects/rename":
                return self._project_rename(qs)
            if parsed.path == "/__projects/delete":
                return self._project_delete(qs)
            if parsed.path == "/__history/undo":
                return self._history_step(qs, "undo")
            if parsed.path == "/__history/redo":
                return self._history_step(qs, "redo")
            m_wn = re.match(r"^/__workflow/node/([A-Za-z0-9_.-]{1,80})/run$", parsed.path)
            if m_wn:
                return self._workflow_node_run(qs, m_wn.group(1))
            m_wnstatus = re.match(r"^/__workflow/node/([A-Za-z0-9_.-]{1,80})/status$", parsed.path)
            if m_wnstatus:
                return self._workflow_node_status(qs, m_wnstatus.group(1))
            # v2.50 — D4: atomic producer endpoint. Validates against the
            # kind contract, stages files, renames atomically, updates
            # workflow.json, fires SSE asset-changed.
            m_wncommit = re.match(r"^/__workflow/node/([A-Za-z0-9_.-]{1,80})/commit$", parsed.path)
            if m_wncommit:
                return self._workflow_node_commit(qs, m_wncommit.group(1))
            # ── v3.0 — Asset-versioning POST routes ─────────────────────
            # Tight regexes per route so node-ids and version ulids land in
            # named groups. ULIDs are 26-char [0-9A-Z]; we relax to a wider
            # alphanumeric pattern to tolerate hand-written ids in tests.
            _NID = r"[A-Za-z0-9_.-]{1,80}"
            _VID = r"[A-Za-z0-9_-]{1,64}"
            m = re.match(rf"^/__workflow/node/({_NID})/version/branch$", parsed.path)
            if m:
                return self._workflow_version_branch(qs, m.group(1))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/revert$", parsed.path)
            if m:
                return self._workflow_version_revert(qs, m.group(1), m.group(2))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/pin$", parsed.path)
            if m:
                return self._workflow_version_pin(qs, m.group(1), m.group(2))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/label$", parsed.path)
            if m:
                return self._workflow_version_label(qs, m.group(1), m.group(2))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/thumb$", parsed.path)
            if m:
                return self._workflow_version_thumb(qs, m.group(1), m.group(2))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition$", parsed.path)
            if m:
                return self._workflow_composition_save(qs, m.group(1), m.group(2))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition/({_VID})/switch$", parsed.path)
            if m:
                return self._workflow_composition_switch(qs, m.group(1), m.group(2), m.group(3))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition/({_VID})/pin$", parsed.path)
            if m:
                return self._workflow_composition_pin(qs, m.group(1), m.group(2), m.group(3))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition/({_VID})/label$", parsed.path)
            if m:
                return self._workflow_composition_label(qs, m.group(1), m.group(2), m.group(3))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition/({_VID})/thumb$", parsed.path)
            if m:
                return self._workflow_composition_thumb(qs, m.group(1), m.group(2), m.group(3))
            m = re.match(rf"^/__workflow/node/({_NID})/size$", parsed.path)
            if m:
                return self._workflow_node_size(qs, m.group(1))
            m_dec = re.match(r"^/__decision/([A-Za-z0-9_.-]{1,80})$", parsed.path)
            if m_dec:
                return self._decision_save(qs, m_dec.group(1))
            if parsed.path == "/__run":
                return self._run_create(qs)
            # /__run/<id>/stop · user-message · tool-result — RESTish nested
            m = re.match(r"^/__run/([0-9a-f]{6,64})/(stop|user-message|tool-result|resume)$", parsed.path)
            if m:
                run_id, action = m.group(1), m.group(2)
                if action == "stop":
                    return self._run_stop(run_id)
                if action == "tool-result":
                    return self._run_tool_result(run_id)
                if action == "resume":
                    return self._run_resume(run_id)
                return self._run_user_message(run_id)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        except Exception as e:
            return self._reply(500, {"error": f"{type(e).__name__}: {e}"})
        self._reply(404, {"error": "unknown endpoint", "path": parsed.path})

    # ── DELETE — v3.0 asset versioning manual prune ──────────────────────
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        self.request_id = _new_request_id()
        try:
            _NID = r"[A-Za-z0-9_.-]{1,80}"
            _VID = r"[A-Za-z0-9_-]{1,64}"
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})/composition/({_VID})$", parsed.path)
            if m:
                return self._workflow_composition_delete(qs, m.group(1), m.group(2), m.group(3))
            m = re.match(rf"^/__workflow/node/({_NID})/version/({_VID})$", parsed.path)
            if m:
                return self._workflow_version_delete(qs, m.group(1), m.group(2))
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        except Exception as e:
            return self._reply(500, {"error": f"{type(e).__name__}: {e}"})
        self._reply(404, {"error": "unknown endpoint", "path": parsed.path})

    # ── GET — intercept source/*.html to inject the poke helpers ─────────
    # Every other path falls through to SimpleHTTPRequestHandler.
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        url_path = parsed.path
        # Bare root → 301 to /editor/ so the browser's base URL is correct
        # and the relative <script src> paths in editor/index.html resolve
        # under /editor/, not under /. (Pre-Phase-6 the same happened via
        # SimpleHTTPRequestHandler's directory listing → user clicks editor/;
        # now we make it explicit.)
        if url_path == "" or url_path == "/":
            qs = parsed.query
            target = "/editor/" + (("?" + qs) if qs else "")
            self.send_response(301)
            self.send_header("Location", target)
            self.end_headers()
            return
        # Daemon JSON endpoints first — they take precedence over static files.
        if url_path == "/__agents":
            return self._agents_list()
        if url_path == "/__healthz":
            return self._healthz()
        # v2.50 — D3/D5 endpoints: registry as JSON + on-demand drift scan.
        if url_path == "/__kinds/registry":
            return self._kinds_registry()
        if url_path == "/__kinds/reconcile":
            return self._kinds_reconcile(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__capabilities":
            return self._capabilities()
        if url_path == "/__orchestrators":
            return self._orchestrators_registry(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__cc_skills":
            return self._cc_skills_list()
        if url_path == "/__workspace":
            return self._workspace_info()
        if url_path == "/__projects":
            return self._projects_list()
        if url_path == "/__runs":
            return self._runs_list(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__chat":
            return self._chat_history(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__doc":
            return self._branch_doc(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__screenshot/jobs":
            return self._screenshot_poll(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__upload/list":
            return self._upload_list(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__workflow":
            return self._workflow_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__design_system":
            return self._design_system_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__ds_bootstrap":
            return self._ds_bootstrap(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__ds_proposals":
            return self._ds_proposals_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__resolve_font":
            return self._resolve_font_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__media_config":
            return self._media_config_get()
        if url_path == "/__export_config":
            return self._export_config_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__ls_dirs":
            return self._ls_dirs(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__list_files":
            return self._list_files(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__source_prototypes":
            return self._source_prototypes(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__starred_prototypes":
            return self._starred_prototypes_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__thumbnail_prototype":
            return self._thumbnail_prototype_get(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__source_htmls":
            return self._source_htmls(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__local_status":
            return self._local_status(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__assets":
            return self._assets_list(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__prompts":
            return self._prompts_list(urllib.parse.parse_qs(parsed.query))
        m = re.match(r"^/__prompts/([a-z0-9][a-z0-9-]{0,60})$", url_path)
        if m:
            return self._prompt_get(urllib.parse.parse_qs(parsed.query), m.group(1))
        if url_path == "/__history":
            return self._history_get(urllib.parse.parse_qs(parsed.query))
        m_wnget = re.match(r"^/__workflow/node/([A-Za-z0-9_.-]{1,80})$", url_path)
        if m_wnget:
            return self._workflow_node_get(urllib.parse.parse_qs(parsed.query), m_wnget.group(1))
        m_wnprev = re.match(r"^/__workflow/node/([A-Za-z0-9_.-]{1,80})/preview$", url_path)
        if m_wnprev:
            return self._workflow_node_preview(urllib.parse.parse_qs(parsed.query), m_wnprev.group(1))
        if url_path == "/__stream":
            return self._run_stream(urllib.parse.parse_qs(parsed.query))
        if url_path == "/__workflow/events":   # v2.30 — SSE for workflow.json mutations
            return self._workflow_events(urllib.parse.parse_qs(parsed.query))
        m = re.match(r"^/__run/([0-9a-f]{6,64})$", url_path)
        if m:
            return self._run_get(m.group(1))
        # Match `/source/...html`, `source/...html`, `../source/...html` (the
        # editor often loads iframes with `../source/main/index.html`-style
        # paths). Normalise once and check the on-disk extension.
        norm = url_path.lstrip("/")
        if norm.endswith(".html") and ("source/" in norm):
            # Use the new tier-aware router so workspace mode resolves
            # /source/<x>.html under the active project root.
            file_path = self.translate_path(self.path)
            if file_path and os.path.isfile(file_path):
                # Resolve the project so the HTML rewrite can stamp every
                # relative src/href with the right ?project= — needed because
                # browsers strip the parent's query when resolving relative
                # URLs from inside the iframe.
                qs = urllib.parse.parse_qs(parsed.query)
                project_id = _qs_get(qs, "project") or ""
                if not project_id and WORKSPACE_DIR:
                    # Last-resort: probe the Referer (covers the rare case
                    # where the iframe URL itself lacks ?project=).
                    try:
                        ref_q = urllib.parse.parse_qs(urllib.parse.urlparse(self.headers.get("Referer", "")).query)
                        project_id = _qs_get(ref_q, "project") or ""
                    except Exception:
                        project_id = ""
                return self._serve_source_html(file_path, project_id)
        return super().do_GET()

    # Match `src="..."`, `href="..."`, `data-src="..."`, etc. — single-URL
    # attrs we should stamp with ?project=. Captures the URL value in group 3.
    _HTML_URL_ATTR_RE = re.compile(
        rb"""\b(src|href|data-src|data-href|poster)\s*=\s*(['"])([^'"]+)\2""",
        re.IGNORECASE,
    )

    @classmethod
    def _stamp_project_on_html(cls, data: bytes, project_id: str) -> bytes:
        """Rewrite every relative src/href in the HTML to carry ?project=<id>.

        Browsers drop a parent document's query string when resolving relative
        URLs. The editor's iframe loads /source/main/index.html?project=<id>,
        but `<link href="styles.css">` then fetches /source/main/styles.css
        with no project query. Daemon-side Referer fallback handles most of
        this, but is fragile (strict referrer policies, sandboxed iframes,
        nested loads). Baking the query directly into the served HTML closes
        that gap once and for all.

        Skips: data: / about: / javascript: / blob: / mailto: / tel: / #anchor
        URLs, http(s):// absolute URLs, and protocol-relative `//host/...`.
        Server-absolute paths starting with `/__` (daemon endpoints) are also
        skipped — they already use apiUrl() in the editor.
        """
        if not project_id:
            return data
        proj = urllib.parse.quote(project_id, safe="")
        proj_q = ("project=" + proj).encode("utf-8")

        def _is_external(val: bytes) -> bool:
            v = val.lstrip()
            if not v: return True
            if v.startswith(b"#"): return True
            if v.startswith(b"//"): return True
            if v[:1] in (b"?",): return False
            # Scheme-prefixed → external / non-fetched.
            head = v[:32].lower()
            for sch in (b"http:", b"https:", b"data:", b"about:", b"blob:",
                        b"javascript:", b"mailto:", b"tel:"):
                if head.startswith(sch): return True
            return False

        def _stamp(match: "re.Match[bytes]") -> bytes:
            attr, q, val = match.group(1), match.group(2), match.group(3)
            if _is_external(val):
                return match.group(0)
            # Skip daemon endpoints — they manage their own ?project=.
            if val.startswith(b"/__") or val.startswith(b"__"):
                return match.group(0)
            # Append `?project=…` (or `&project=…` if a query already exists).
            # Don't touch a value that already has project=.
            if b"project=" in val:
                return match.group(0)
            if b"?" in val:
                new_val = val + b"&" + proj_q
            else:
                # Split off fragment first so the query goes BEFORE the #hash.
                hash_at = val.find(b"#")
                if hash_at >= 0:
                    new_val = val[:hash_at] + b"?" + proj_q + val[hash_at:]
                else:
                    new_val = val + b"?" + proj_q
            return attr + b"=" + q + new_val + q

        return cls._HTML_URL_ATTR_RE.sub(_stamp, data)

    def _serve_source_html(self, file_path: str, project_id: str = "") -> None:
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except OSError:
            return super().do_GET()
        # Stamp `?project=<id>` onto every relative src/href so nested loads
        # (styles.css, app.jsx, data.js, images) resolve to the right project
        # without depending on the Referer header.
        if project_id:
            data = self._stamp_project_on_html(data, project_id)
        inject = b"<script>" + POKE_HELPER.encode("utf-8") + b"</script>"
        lower = data.lower()
        head = lower.find(b"<head>")
        if head >= 0:
            cut = head + len(b"<head>")
            data = data[:cut] + inject + data[cut:]
        else:
            # No <head> — try the start of <body>; failing that, prepend.
            body = lower.find(b"<body")
            if body >= 0:
                close = lower.find(b">", body)
                if close >= 0:
                    cut = close + 1
                    data = data[:cut] + inject + data[cut:]
                else:
                    data = inject + data
            else:
                data = inject + data
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ── POST /__layout ───────────────────────────────────────────────────
    # Persist Canvas-view frame positions + meta overrides (default frame
    # size, canvas gap) to a sidecar file the editor reloads on next boot.
    # This is intentionally separate from the design-edits queue
    # (edits.json + Workflow 2): rearranging frames and tweaking the grid
    # are editor-organization, not "design changes" that should round-trip
    # through an LLM run.
    #
    # Body: { "positions": { "<frame-id>": { "col": <int>, "row": <int> }, ... },
    #         "meta":      { "defaultFrame": { "w": <int>, "h": <int> },
    #                        "canvasGap":    <int> } }
    # Writes: editor/branches/<slug>.layout.js with `window.EDITOR_LAYOUT = …`.
    #
    # The sidecar shape is { positions: {...}, meta: {...} }. Legacy sidecars
    # (flat id → {col,row}) are auto-upgraded on the next write.
    def _layout_save(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        slug = _qs_prototype(qs).strip().lower()
        if not slug or not SLUG_OK.match(slug):
            return self._reply(400, {"error": "invalid prototype slug", "slug": slug})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large", "bytes": length, "max": MAX_BYTES})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        positions = body.get("positions") or {}
        if not isinstance(positions, dict):
            return self._reply(400, {"error": "positions must be an object"})
        # Sanitize positions — only id → { col:int, row:int } allowed.
        sanitized_positions = {}
        for fid, pos in positions.items():
            if not isinstance(fid, str) or not fid:
                continue
            if not isinstance(pos, dict):
                continue
            col = pos.get("col"); row = pos.get("row")
            if not isinstance(col, int) or not isinstance(row, int):
                continue
            sanitized_positions[fid] = {"col": col, "row": row}
        # Sanitize meta — defaultFrame.{w,h} ints, canvasGap int.
        sanitized_meta = {}
        meta_in = body.get("meta") if isinstance(body.get("meta"), dict) else {}
        df = meta_in.get("defaultFrame") if isinstance(meta_in.get("defaultFrame"), dict) else None
        if df:
            w = df.get("w"); h = df.get("h")
            if isinstance(w, int) and isinstance(h, int) and w >= 100 and h >= 100:
                sanitized_meta["defaultFrame"] = {"w": w, "h": h}
        gap = meta_in.get("canvasGap")
        if isinstance(gap, int) and gap >= 0:
            sanitized_meta["canvasGap"] = gap
        dest_dir = _project_paths(project_root)["editor_dir"]
        if not os.path.isdir(dest_dir):
            return self._reply(404, {"error": "editor dir missing", "dir": dest_dir})
        dest = os.path.join(dest_dir, slug + ".layout.js")
        payload = {"positions": sanitized_positions}
        if sanitized_meta:
            payload["meta"] = sanitized_meta
        js = (
            "// Auto-generated by /__layout. Carries editor preferences:\n"
            "//   positions — frame.id → { col, row } for the Canvas grid.\n"
            "//   meta      — defaultFrame { w, h }, canvasGap (px).\n"
            "// Hand-edits OK but the editor overwrites on next rearrange\n"
            "// or frame-size change. Delete to reset everything.\n"
            "window.EDITOR_LAYOUT = " + json.dumps(payload, indent=2, sort_keys=True) + ";\n"
        )
        rel_dest = os.path.relpath(dest, project_root)
        with _history_bracket(project_root, [rel_dest],
                              kind="ui-edit",
                              label=f"Layout: {slug}",
                              source="editor",
                              extra={"prototype": slug}):
            with open(dest, "w", encoding="utf-8") as f:
                f.write(js)
        return self._reply(200, {"ok": True, "path": rel_dest, "frames": len(sanitized)})

    # ── GET /__workflow / POST /__workflow ──────────────────────────────
    # Persists the Workflow Canvas surface (Phase 3.5b+): pan/zoom + a flat
    # nodes list (prototype instances, asset/skill/prompt nodes in later
    # phases) + edges (3.5d+). One file per project at
    # <project_root>/workflow/workflow.json. Kept deliberately schema-light
    # so 3.5c/3.5d/Phase-4 can extend nodes[] without daemon updates.
    def _workflow_get(self, qs):
        # v3.7 — require_explicit=True. In workspace mode with more than one
        # project, hitting /__workflow without ?project=<id> used to silently
        # fall back to the first-discovered project, which surfaced as the
        # musem bug: a chat agent in project=musem ran
        # `curl $TH_DAEMON_URL/__workflow` (forgetting `?project=$TH_PROJECT_ID`)
        # and got back the install's brand-landing workflow (27 nodes about
        # Vermeer's studio). Claude then thought 27 nodes had appeared in
        # musem and asked the user whether to clear them. The editor UI
        # always passes ?project= via apiUrl() — only ad-hoc curls need the
        # explicit failure. require_explicit=True returns 400 with a list of
        # known project ids when >1 exists; single-project workspaces still
        # auto-resolve.
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e), "hint": "append ?project=$TH_PROJECT_ID to the URL"})
        # v3.0 — every workflow GET ensures the file watcher is running so
        # the asset-versioning snapshot hook fires on subsequent writes.
        # Previously only SSE subscribers started the watcher; loads that
        # only hit GET /__workflow (e.g. integration tests, curl probes,
        # browsers that briefly load without SSE) saw no snapshots and
        # `versions[]` never accumulated past the first migration entry.
        try: _file_watcher_ensure_started()
        except Exception: pass
        path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(path):
            return self._reply(200, {"pan": {"x": 0, "y": 0}, "zoom": 1, "nodes": [], "edges": []})
        # v3.0 — asset-versioning migration. Idempotent; writes back only when
        # an asset node was synthesized to carry versions[0] + activeVersionId.
        # See docs/features/asset-versioning.md §11.
        try:
            from kinds.reconcile import apply_versioning_migration
            apply_versioning_migration(project_root)
        except Exception as e:
            print(f"[asset-versioning] migration error: {e}", flush=True)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return self._reply(500, {"error": f"workflow.json unreadable: {e}"})
        # Tolerate missing top-level keys — frontend treats them as empty defaults.
        if not isinstance(data, dict):
            data = {}
        data.setdefault("pan", {"x": 0, "y": 0})
        data.setdefault("zoom", 1)
        data.setdefault("nodes", [])
        data.setdefault("edges", [])
        # v2.20 — backward-compat projection for `runId`. Older daemons (pre-
        # v2.20) wrote only `runRunId` when dispatching agent-kind nodes;
        # WorkflowAgentNode reads `node.runId`. Project the value on the wire
        # so existing projects with only `runRunId` on disk still surface a
        # working chat tab. New writes set both fields directly.
        try:
            for n in (data.get("nodes") or []):
                if not isinstance(n, dict): continue
                if n.get("runId"): continue
                rr = n.get("runRunId")
                if rr: n["runId"] = rr
        except Exception:
            pass
        # v2.17c — display hydration for auto:true intermediary prompt nodes.
        # These nodes sit between a skill dispatch and its downstream consumers
        # (e.g. an intermediate text node between the producer and consumer).
        # The daemon's upstream walk for downstream /run calls reads the
        # upstream skill's .output directly, bypassing the intermediary — so
        # the intermediary's .text stays empty on disk forever even when real
        # data flowed through. To stop the canvas from lying, hydrate `.text`
        # on the wire from upstream skill `.output` when the intermediary's
        # own `.text` is still empty. This is read-only (GET-time) projection
        # — never written to disk — so it doesn't conflict with the v2.17a
        # save guard or orchestrator's explicit POSTs.
        try:
            nodes = data.get("nodes") or []
            edges = data.get("edges") or []
            by_id = {n.get("id"): n for n in nodes if isinstance(n, dict) and n.get("id")}
            # Map: intermediary_id -> upstream_skill_id (first one wins; auto-
            # intermediaries are scaffolded with a single upstream skill edge).
            upstream_of = {}
            for e in edges:
                if not isinstance(e, dict): continue
                t = (e.get("to") or "").split(".", 1)[0]
                f = (e.get("from") or "").split(".", 1)[0]
                if not t or not f: continue
                tnode = by_id.get(t)
                if not tnode: continue
                if tnode.get("auto") is True and tnode.get("kind") == "prompt":
                    upstream_of.setdefault(t, f)
            for nid, upstream_id in upstream_of.items():
                n = by_id.get(nid)
                if not n: continue
                # Don't override if the intermediary already has its own text
                # (orchestrator or user populated it explicitly).
                if (n.get("text") or "").strip(): continue
                up = by_id.get(upstream_id)
                if not up: continue
                up_out = up.get("output")
                up_text = ""
                if isinstance(up_out, dict):
                    up_text = up_out.get("text") or ""
                elif isinstance(up_out, str):
                    up_text = up_out
                if up_text.strip():
                    # Annotate the projected source so the frontend can label
                    # it ("from <producer>.output") rather than imply this
                    # is user-edited text.
                    n["text"] = up_text
                    n["textProjectedFrom"] = upstream_id
        except Exception:
            pass  # projection failure must not break the GET — fall through.
        # v2.40 — hydrate ds-brainstorm node spec from its downstream HTML
        # asset's <script id="variant-spec"> JSON. The orchestrator writes
        # the HTML directly (Pattern C) without POSTing the spec back to
        # the parent node, so its form fields look empty even though the
        # actual variant content (genre / targetAudience / emotion / etc.)
        # is on disk. Project the JSON onto the node so the canvas card
        # reflects reality. Read-only — never written to disk.
        try:
            import re as _re
            # Helper: read a project-relative file. Returns string or None.
            def _read_proj_file(rel):
                if not rel: return None
                fp = os.path.join(project_root, rel.lstrip("/"))
                if not os.path.isfile(fp): return None
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        return fh.read()
                except Exception:
                    return None
            # Helper: edges as (from_id, to_id) tuples
            edge_pairs = []
            for e in edges:
                if not isinstance(e, dict): continue
                f = (e.get("from") or "").split(".", 1)[0]
                t = (e.get("to") or "").split(".", 1)[0]
                if f and t: edge_pairs.append((f, t))
            def _downstream_of(node_id, predicate=None):
                for (f, t) in edge_pairs:
                    if f == node_id:
                        c = by_id.get(t)
                        if c and (predicate is None or predicate(c)): return c
                return None

            # ───────── v2.40 — ds-brainstorm.spec from <script id="variant-spec"> ─────────
            for n in nodes:
                if n.get("kind") != "ds-brainstorm": continue
                if isinstance(n.get("spec"), dict) and n["spec"].get("genre"):
                    continue
                child = _downstream_of(n["id"],
                    lambda c: c.get("kind") == "asset" and c.get("assetKind") == "html")
                if not child: continue
                html = _read_proj_file(child.get("path") or "")
                if not html: continue
                m = _re.search(r'<script[^>]+id=["\']variant-spec["\'][^>]*>(.*?)</script>', html, _re.S | _re.I)
                if not m: continue
                try:
                    spec = json.loads(m.group(1).strip())
                    if isinstance(spec, dict):
                        n["spec"] = spec
                        n["specProjectedFrom"] = child.get("path")
                except Exception:
                    pass

            # ───────── v2.42a — bp_ds_gen.spec from DECISION + picked variant ─────────
            # When the user picked a brainstorm variant, the orchestrator was
            # supposed to POST that variant's spec onto bp_ds_gen so the
            # ▶ Build button has a non-empty genre. Project it instead so
            # the field shows up even if the orchestrator didn't.
            for n in nodes:
                if n.get("kind") != "design-system": continue
                sp = n.get("spec") if isinstance(n.get("spec"), dict) else {}
                if sp.get("genre"): continue  # already set
                # Read DECISION_cp_ds_pick.json
                dec = _read_proj_file("DECISION_cp_ds_pick.json")
                if not dec: continue
                try:
                    dj = json.loads(dec)
                    picked = (dj.get("values") or [dj.get("value")])[0]
                    if not picked: continue
                    # picked is a variant id (a/b/c). Find the brainstorm
                    # asset whose path matches.
                    for nn in nodes:
                        if nn.get("kind") != "asset": continue
                        if nn.get("assetKind") != "html": continue
                        p = nn.get("path") or ""
                        if f"_ds_brainstorm/{picked}.html" not in p: continue
                        html = _read_proj_file(p)
                        if not html: break
                        m = _re.search(r'<script[^>]+id=["\']variant-spec["\'][^>]*>(.*?)</script>', html, _re.S | _re.I)
                        if not m: break
                        try:
                            vspec = json.loads(m.group(1).strip())
                            n["spec"] = {
                                **sp,
                                "genre":       vspec.get("direction") or vspec.get("label") or "",
                                "extraBrief":  f"Built from picked brainstorm variant {picked} ({vspec.get('label','')}). "
                                              f"Compatible shells: {', '.join(vspec.get('compatibleShells') or [])}.",
                                "personaModes": vspec.get("personaModes") or sp.get("personaModes") or [],
                            }
                            n["specProjectedFrom"] = f"DECISION_cp_ds_pick.json + {p}"
                        except Exception:
                            pass
                        break
                except Exception:
                    pass

            # ───────── v2.42b — bs_html_*.text from bp_chunks.output ─────────
            # bp_chunks emits an array of 3 page specs. Each bs_html_<N>
            # should have its prompt populated with chunks[N-1]. Otherwise
            # the LLM dispatch gets a generic "page #N" placeholder.
            chunks_node = by_id.get("bp_chunks")
            if chunks_node:
                co = chunks_node.get("output")
                chunks_text = (co.get("text") if isinstance(co, dict) else co) or ""
                if isinstance(chunks_text, str) and chunks_text.strip():
                    # Try to find a JSON array inside the output
                    chunks_arr = None
                    try:
                        # Often the output is wrapped in markdown ```json blocks
                        m = _re.search(r'\[\s*\{.*?\}\s*\]', chunks_text, _re.S)
                        if m: chunks_arr = json.loads(m.group(0))
                    except Exception:
                        pass
                    if isinstance(chunks_arr, list):
                        for i in range(min(3, len(chunks_arr))):
                            target = by_id.get(f"bs_html_{i+1}")
                            if not target: continue
                            # Don't override user/orchestrator-customized text — only
                            # project when the field is still the scaffolder default.
                            cur = target.get("text") or ""
                            if "chunk-PRD page #" not in cur and cur.strip():
                                continue
                            chunk = chunks_arr[i]
                            if not isinstance(chunk, dict): continue
                            spec_json = json.dumps(chunk, indent=2)
                            target["text"] = (
                                f"Generate a single self-contained HTML page for THIS page spec:\n\n"
                                f"```json\n{spec_json}\n```\n\n"
                                f"Apply BRAINSTORM_VISUAL_RULES + CONTENT_DISCIPLINE (≤180 LOC, "
                                f"real product copy, every block earns its place, no filler)."
                            )
                            target["textProjectedFrom"] = "bp_chunks.output"

            # ───────── v2.42c — cp_ds_pick / cp_remix_pick decision state ─────────
            # When DECISION_*.json exists, surface the picked values on the
            # checkpoint card so the user sees what they picked without
            # having to dig into the json file.
            for nid_pick, decision_file in (("cp_ds_pick",    "DECISION_cp_ds_pick.json"),
                                             ("cp_remix_pick", "DECISION_cp_remix_pick.json")):
                target = by_id.get(nid_pick)
                if not target: continue
                if target.get("decision"): continue  # already set
                dec = _read_proj_file(decision_file)
                if not dec: continue
                try:
                    target["decision"] = json.loads(dec)
                    target["decisionProjectedFrom"] = decision_file
                except Exception:
                    pass
        except Exception:
            pass
        return self._reply(200, data)

    def _workflow_save(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large", "bytes": length, "max": MAX_BYTES})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "workflow body must be an object"})
        # Sanitize — keep only structural fields we expect, pass arbitrary
        # extras through on nodes so future kinds (asset/skill/prompt/llm)
        # can ship their own fields without a daemon round-trip.
        pan = body.get("pan") or {"x": 0, "y": 0}
        if not isinstance(pan, dict): pan = {"x": 0, "y": 0}
        try:
            pan = {"x": float(pan.get("x", 0)), "y": float(pan.get("y", 0))}
        except Exception:
            pan = {"x": 0, "y": 0}
        try:
            zoom = float(body.get("zoom", 1)) or 1.0
        except Exception:
            zoom = 1.0
        nodes = body.get("nodes") or []
        if not isinstance(nodes, list):
            return self._reply(400, {"error": "nodes must be an array"})
        edges = body.get("edges") or []
        if not isinstance(edges, list):
            return self._reply(400, {"error": "edges must be an array"})
        clean_nodes = []
        seen_ids = set()
        for n in nodes:
            if not isinstance(n, dict): continue
            nid = n.get("id")
            kind = n.get("kind")
            if not isinstance(nid, str) or not nid: continue
            if nid in seen_ids: continue
            if not isinstance(kind, str) or not kind: continue
            try:
                x = float(n.get("x", 0)); y = float(n.get("y", 0))
            except Exception:
                continue
            seen_ids.add(nid)
            # Copy the whole node through — daemon doesn't gate the
            # per-kind fields. Just normalize id/kind/x/y to canonical types.
            entry = dict(n)
            entry["id"] = nid
            entry["kind"] = kind
            entry["x"] = x
            entry["y"] = y
            clean_nodes.append(entry)
        clean_edges = []
        for e in edges:
            if not isinstance(e, dict): continue
            f = e.get("from"); t = e.get("to")
            if not isinstance(f, str) or not isinstance(t, str): continue
            clean_edges.append({"from": f, "to": t})
        # Merge protection — preserve nodes added by background writers
        # (the visual-orchestrator subagent + its per-medium drawers scaffold
        # node trios using a `p_`/`s_`/`r_`/`a_` id namespace) that the
        # editor hasn't seen yet. Without this, the editor's debounced
        # save races the subagent's write and silently clobbers any
        # node trio that landed between the editor's last refetch and
        # this POST. We only protect THIS namespace — user-created and
        # editor-spawned nodes use `n<hash>` ids and follow normal save
        # semantics (including deletes).
        #
        # The editor ships `deletedIds` — ids the user just removed via
        # the canvas — so the merge knows NOT to restore a subagent-
        # namespace node the user is deliberately deleting. Without this
        # the user wouldn't be able to delete agent-generated trios at
        # all (the merge would keep re-adding them).
        deleted_ids = set()
        raw_deleted = body.get("deletedIds")
        if isinstance(raw_deleted, list):
            for x in raw_deleted:
                if isinstance(x, str): deleted_ids.add(x)
        # v2.31 — serialize the WHOLE read-modify-write under the per-project lock
        # so concurrent /status POSTs can't write their stale snapshot AFTER our
        # write and revert the user's edit.
        # v2.50 — bounded by a per-project semaphore (cap 3) AND a 2s lock
        # acquire timeout. On timeout/queue-full, return 503 with retry hint so
        # the frontend distinguishes "busy" from "down". See WORKFLOW_TRUTHFULNESS_PLAN.md §11 D2.
        project_id = os.path.basename(project_root.rstrip("/"))
        _sem = _request_semaphore(project_id)
        if not _sem.acquire(timeout=5.0):
            return self._reply(503, {
                "error": "project request queue full (cap=3)",
                "hint": "retry in ~1s; another request on this project is still in flight",
                "retryAfterMs": 1000,
            })
        try:
          _lk = _workflow_lock(project_id)
          if not _lk.acquire(timeout=2.0):
            return self._reply(503, {
                "error": "workflow locked (another write in progress)",
                "hint": "retry in ~1s",
                "retryAfterMs": 1000,
            })
          try:
            wf_dir = os.path.join(project_root, "workflow")
            path = os.path.join(wf_dir, "workflow.json")
            preserved_nodes = []
            preserved_edges = []
            try:
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as f:
                        disk = json.load(f) or {}
                    disk_nodes = disk.get("nodes") or []
                    disk_edges = disk.get("edges") or []
                    posted_ids = {n["id"] for n in clean_nodes if isinstance(n, dict) and "id" in n}
                    for n in disk_nodes:
                        if not isinstance(n, dict): continue
                        nid = n.get("id")
                        if not isinstance(nid, str): continue
                        if nid in posted_ids: continue
                        if nid in deleted_ids: continue  # user tombstone — don't restore
                        # Visual-orchestrator / drawer namespace AND onboarding-orchestrator
                        # namespace (bp_/bs_/br_/cp_ — see onboarding plan §Phase 2).
                        # v3.3 — simulation / interactive-media / narrative-experience
                        # families (sim_/im_/nx_) are also background-writer namespaces:
                        # the *-orchestrator subagents + their component drawers scaffold node
                        # trios the editor hasn't refetched yet. Without this guard a
                        # debounced editor canvas-save races the orchestrator's research-fleet
                        # write and silently clobbers the whole sim_<id> trio (observed:
                        # a mid-research "Update workflow canvas" save wiped all four
                        # sim_research_* nodes for an in-flight simulation).
                        if (nid[:2] in ("p_", "s_", "r_", "a_")
                                or nid[:3] in ("bp_", "bs_", "br_", "cp_", "im_", "nx_")
                                or nid[:4] == "sim_"):
                            preserved_nodes.append(n)
                    # Preserve edges whose endpoints both still exist (in
                    # either posted or preserved nodes).
                    if preserved_nodes:
                        posted_edge_keys = {(e.get("from"), e.get("to")) for e in clean_edges}
                        all_ids = posted_ids | {n["id"] for n in preserved_nodes}
                        for e in disk_edges:
                            if not isinstance(e, dict): continue
                            f_str = e.get("from"); t_str = e.get("to")
                            if (f_str, t_str) in posted_edge_keys: continue
                            # endpoint id is the part before the first `.`
                            fid = (f_str or "").split(".", 1)[0]
                            tid = (t_str or "").split(".", 1)[0]
                            if fid not in all_ids or tid not in all_ids: continue
                            if fid in deleted_ids or tid in deleted_ids: continue
                            if (fid[:2] in ("p_", "s_", "r_", "a_") or tid[:2] in ("p_", "s_", "r_", "a_")
                                or fid[:3] in ("bp_", "bs_", "br_", "cp_") or tid[:3] in ("bp_", "bs_", "br_", "cp_")):
                                preserved_edges.append({"from": f_str, "to": t_str})
            except Exception:
                # Disk read failed — fall through to plain write. Worst case
                # we lose subagent additions; we don't want to break the
                # editor's save flow over a malformed prior file.
                preserved_nodes = []
                preserved_edges = []
            if preserved_nodes: clean_nodes = clean_nodes + preserved_nodes
            if preserved_edges: clean_edges = clean_edges + preserved_edges
            # v2.17a — daemon-authoritative field guard. When the editor POSTs an
            # existing node, certain fields are owned by the DAEMON (not the
            # editor) and must NEVER be overwritten by what the editor sent:
            #   - `text` of `auto:true` intermediary nodes — these are populated
            #     by the orchestrator via POST /status.
            #     The editor renders them empty and would otherwise erase the
            #     orchestrator's writes on its next debounced save. Same root
            #     cause as v2.12a but for prompt-intermediary `text` rather than
            #     skill `output`.
            #   - `output` of any node — set by daemon `/run` dispatch.
            #   - `runStatus`, `runError`, `runRunId` — set by daemon completion
            #     hooks + POST /status calls.
            # We re-read disk for these fields and override whatever the editor
            # sent, so a stale editor cache can never silently erase live state.
            # The editor's reload-merge (app.js v2.12a) will sync these back in
            # on its next refetch — they just won't be lost in the meantime.
            try:
                if os.path.isfile(path):
                    # disk_nodes was loaded above in the merge-protection block;
                    # re-fetch to handle the case where that block bailed out.
                    with open(path, "r", encoding="utf-8") as f:
                        _existing = json.load(f) or {}
                    _disk_by_id = {
                        n.get("id"): n for n in (_existing.get("nodes") or [])
                        if isinstance(n, dict) and isinstance(n.get("id"), str)
                    }
                    for n in clean_nodes:
                        disk_n = _disk_by_id.get(n.get("id"))
                        if not disk_n: continue
                        # Always preserve daemon-owned status fields if disk has them.
                        # v2.20 — `runId` added alongside `runRunId` so the chat
                        # transcript pointer survives the editor's debounced save.
                        # v3.0 — asset-versioning adds `versions`, `activeVersionId`
                        # to the daemon-owned set. Both are mutated ONLY by the
                        # daemon (snapshot_asset / revert / branch endpoints);
                        # the frontend reads them but never re-posts authoritative
                        # values. Without this preservation, the frontend's
                        # debounced /__workflow POST (which echoes back the
                        # asset node from React state at FETCH time) overwrites
                        # the version history with a stale snapshot. Verified
                        # against a real project where 4 snapshot dirs existed
                        # under workflow/runs/<assetId>/ but workflow.json had
                        # only one versions[] entry.
                        for daemon_field in ("output", "runRunId", "runId",
                                              "versions", "activeVersionId"):
                            if daemon_field in disk_n:
                                disk_val = disk_n.get(daemon_field)
                                # Only override if the disk value is non-None;
                                # let the editor clear (e.g. via "reset run") work.
                                if disk_val is not None:
                                    n[daemon_field] = disk_val
                        # v3.4.11 — runStatus + runError narrowed preservation.
                        # The old broad preservation ("if disk has non-None,
                        # override editor's POST") clobbered legitimate editor
                        # clears. Concrete bug: runRemix spawns a variant card
                        # with runStatus="pending", the first 350ms-debounced
                        # save writes "pending" to disk, the variant LLM call
                        # finishes ~2s later and the editor sets runStatus=null
                        # in memory, the next save POSTs null — but the
                        # preservation here saw disk still had "pending" and
                        # rewrote it back. The card was permanently stuck on
                        # the "Generating…" skeleton even though the file
                        # landed on disk. Same root cause for runRepeater +
                        # any other editor-managed pending state.
                        #
                        # The orchestrator race the broad preservation was
                        # protecting against ONLY applies when disk has
                        # "running" — that state is ONLY set by the per-node
                        # /__workflow/node/<id>/status endpoint (atomic
                        # daemon-side flip during an active agent run). Every
                        # other runStatus value (pending / paused / error /
                        # done / null) flows through the editor, so editor
                        # wins. Narrow the preservation to just "running":
                        disk_status = disk_n.get("runStatus")
                        if disk_status == "running":
                            n["runStatus"] = "running"
                            disk_error = disk_n.get("runError")
                            if disk_error is not None:
                                n["runError"] = disk_error
                        # else: trust editor's posted runStatus + runError —
                        # editor is authoritative for pending → null clears
                        # (variant succeeded), pending → error flips (variant
                        # failed), and final-state cleanups (done/error → null
                        # from the polling self-heal).
                        # v2.18d — kind-specific orchestrator-set fields.
                        # v2.25 — only preserve disk when the editor sends back
                        # EMPTY (the stomp pattern: stale React state lost the
                        # orchestrator's POST and is echoing back null/empty/
                        # default). If the editor sends a non-empty value that
                        # differs from disk, that's the user MANUALLY EDITING
                        # the field — let it through. Without this nuance, the
                        # iterator-refiner / iterator-remix / design-system
                        # fields became read-only on the canvas — every typed
                        # character got reverted on the next 350ms debounced
                        # save. (Reported by user: "why i can't edit the node
                        # manually?")
                        def _is_empty(v):
                            return v in (None, "", [], {})
                        nkind = disk_n.get("kind")
                        kind_fields = {
                            "iterator-refiner": ("goal", "focus", "pushPast", "maxTurns"),
                            "iterator-remix":   ("variants",),
                            "design-system":    ("spec",),
                        }.get(nkind, ())
                        for f in kind_fields:
                            if f not in disk_n: continue
                            disk_val = disk_n.get(f)
                            if _is_empty(disk_val): continue  # editor can set initially
                            posted_val = n.get(f)
                            if not _is_empty(posted_val): continue  # user edit wins
                            n[f] = disk_val  # only override empty-posted with non-empty disk
                        # Auto-intermediary text guard: if disk has its own text
                        # (from an orchestrator POST), keep it. If the editor is
                        # echoing back a v2.17c-projected text (recognisable by
                        # `textProjectedFrom`), strip both — the projection is a
                        # wire-only display field; persisting it to disk would
                        # defeat the read-only intent and stomp future updates.
                        if disk_n.get("auto") is True:
                            disk_text = disk_n.get("text") or ""
                            if "textProjectedFrom" in n:
                                n.pop("textProjectedFrom", None)
                                # If the posted text equals the projection (editor
                                # didn't edit it), reset to whatever disk has.
                                n["text"] = disk_text
                            else:
                                posted_text = n.get("text") or ""
                                if disk_text and not posted_text:
                                    n["text"] = disk_text
            except Exception:
                pass  # disk read failed — fall through; we still write what was posted.
            out = {"pan": pan, "zoom": zoom, "nodes": clean_nodes, "edges": clean_edges}
            try:
                os.makedirs(wf_dir, exist_ok=True)
            except Exception as e:
                return self._reply(500, {"error": f"could not create workflow dir: {e}"})
            rel_path = os.path.relpath(path, project_root)
            try:
                with _history_bracket(project_root, [rel_path],
                                       kind="workflow-op",
                                       label="Update workflow canvas",
                                       source="workflow",
                                       extra={"nodes": len(clean_nodes), "edges": len(clean_edges)}):
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(out, f, indent=2)
            except Exception as e:
                return self._reply(500, {"error": f"could not write workflow.json: {e}"})
            # v2.30 — notify SSE subscribers
            _broadcast_workflow_change(os.path.basename(project_root.rstrip("/")))
            return self._reply(200, {"ok": True, "path": rel_path,
                                      "nodes": len(clean_nodes), "edges": len(clean_edges),
                                      "preservedSubagentNodes": len(preserved_nodes)})
          finally:
            _lk.release()
        finally:
          _sem.release()

    # ── GET /__design_system / POST /__design_system ─────────────────────
    # Reads / writes a Design System library node at
    # <project_root>/design-systems/<id>/. The DS is a first-class library
    # asset that the prototype regen workflow gates on — Workflow 1 will not
    # run against a branch whose meta.dsRef points at a missing DS.
    #
    # GET /__design_system                  → list every DS folder under
    #                                          design-systems/, with id +
    #                                          version + label per entry.
    # GET /__design_system?id=<id>          → return the trio + meta.json for
    #                                          one DS. The agent that consumes
    #                                          this is Subagent 0 (DS builder)
    #                                          or 6 (DS auditor); the editor
    #                                          consumes it to render the
    #                                          DesignSystemNode card.
    # POST /__design_system?id=<id>         → write the trio + meta.json
    #                                          atomically. Body shape:
    #                                          { "spec": {...},  ← workflow-mode spec snapshot
    #                                            "trio": {
    #                                              "stylesCss":   "...",
    #                                              "galleryHtml": "...",
    #                                              "designMd":    "..." },
    #                                            "label": "v1" }
    #                                          version is auto-computed as a
    #                                          content hash of the trio.

    # ── v2.7 — shared LLM dispatch helper for skill=llm + prompt-refiner ─
    # Both kinds resolve provider/model from the node fields and route
    # through _anthropic_chat / _openai_chat / _claude_cli_complete in the
    # same shape. Extracting this lets the two branches diverge ONLY in how
    # they compose the prompt — refiner prepends its meta-prompt, skill=llm
    # just stacks upstream + node text.
    def _llm_dispatch(self, node, full_prompt):
        provider = (node.get("provider") or "anthropic").strip()
        model    = (node.get("model")    or ("claude-opus-4-7" if provider == "anthropic" else "gpt-4o-mini")).strip()
        api_key  = _resolve_provider_key(provider)
        messages = [{"role": "user", "content": full_prompt}]
        if provider == "anthropic":
            if api_key:
                resp = _anthropic_chat(api_key, messages, model=model)
            else:
                # CLI fallback when no API key is set but `claude` is on PATH.
                resp = {"text": _claude_cli_complete(messages, model=model, timeout=600)}
        elif provider == "openai":
            if not api_key: raise ValueError("no openai API key configured")
            resp = _openai_chat(api_key, messages, model=model)
        else:
            raise ValueError(f"unsupported provider: {provider}")
        return (resp.get("text") if isinstance(resp, dict) else "") or ""

    # ── v2.1 — node-agent subprocess spawn helper ───────────────────────
    # Focused per-node `claude` spawn used by /__workflow/node/<id>/run when
    # the node's kind is "agent". Unlike _run_create, no discovery /
    # orchestrator preamble is added — the per-node preamble from
    # node_agent_preambles.py is the entire system prompt. The spawned run
    # is tagged with `workflow_node_id` so _drain_stdout's completion hook
    # can mark the node done (or error) on the canvas automatically.
    #
    # Returns (run_id, None) on success, (None, (status, error_dict)) on
    # failure — caller passes error_dict to self._reply.
    def _spawn_node_agent(self, *, project_root, project_id, branch,
                          node_id, system_prompt, prompt_text, title):
        agent_id = "claude"
        defs = AGENT_DEFS.get(agent_id)
        if not defs:
            return None, (500, {"error": "claude agent not registered"})
        bin_path = detect_agent_bin(agent_id)
        if not bin_path:
            return None, (500, {"error": "claude binary not on PATH"})
        permission_mode = "bypassPermissions"
        spawn_args = list(defs["args"])
        # v2.45 — Claude Code 2.1.150 split bypass into two flags. The mode
        # string "bypassPermissions" no longer skips prompts for high-risk
        # tools like Bash and Write; only --dangerously-skip-permissions
        # does. Map the UI's "Auto — bypass" to the actual full-bypass flag.
        # v3.8 — Claude Code 2.1.163 (and likely later) split it further:
        # --dangerously-skip-permissions BY ITSELF no longer skips prompts.
        # You also need --allow-dangerously-skip-permissions to ENABLE the
        # behaviour. From `claude --help`:
        #   --allow-dangerously-skip-permissions   Enable bypassing all permission checks
        #   --dangerously-skip-permissions         Bypass all permission checks.
        # Skipping the enable flag is what caused museuuum's chat to hit
        # "Claude requested permissions to write ... but you haven't granted
        # it yet" after running 4 hours: every Write/Edit/Bash that the
        # orchestrator subagents triggered queued behind a permission prompt the
        # user couldn't approve.
        if permission_mode == "bypassPermissions":
            spawn_args += [
                "--allow-dangerously-skip-permissions",
                "--dangerously-skip-permissions",
            ]
        elif defs.get("permission_flag"):
            spawn_args += [defs["permission_flag"], permission_mode]
        # v3.1 — Hide user-level slash commands (~/.claude/commands/). The
        # daemon's capabilities preamble + Woven subagents (visual-orchestrator,
        # raster-foreground, etc.) are the only image-pipeline path; the
        # user's personal /prototype skill used to override visual-orchestrator
        # by telling the agent to use placeholder rectangles instead.
        spawn_args += ["--disable-slash-commands"]
        # v3.1 — Hook gate. PreToolUse on Write/Edit/MultiEdit blocks any
        # *.html write until the agent has called Task with
        # subagent_type='visual-orchestrator'. Soft preamble rules ("you MUST
        # dispatch visual-orchestrator") were ignored; this is hard enforcement
        # at the tool-call boundary.
        _harness_settings = _ensure_harness_settings()
        if _harness_settings:
            spawn_args += ["--settings", _harness_settings]
        # The per-node preamble IS the full system prompt for this run. Plus
        # the question-form protocol so <decision-request> / <question-form>
        # still parses if the subagent emits one. Workspace layout block too
        # so the subagent knows where AGENTS.md / PROTOTYPE.md live.
        sys_prompt = QUESTION_FORM_SYSTEM_PROMPT
        if WORKSPACE_DIR and project_root != INSTALL_ROOT:
            sys_prompt += WORKSPACE_LAYOUT_PROMPT
        # v2.50 — bake the capabilities catalog into the preamble so the
        # spawned subagent knows what the app supports (image providers,
        # subagent drawers, endpoints, node kinds). Without this, agents
        # answer "I don't have <X>" for features that ARE integrated.
        try:
            from kinds.capabilities import capabilities_preamble
            sys_prompt += "\n\n" + capabilities_preamble()
        except Exception:
            pass
        sys_prompt += "\n\n" + system_prompt
        spawn_args += ["--append-system-prompt", sys_prompt]
        # The agent's workspace is the PROJECT, not the editor installation.
        # Previously this also added --add-dir INSTALL_ROOT so the agent could
        # Read protocol docs (AGENTS.md, PROTOTYPE.md, docs/agents/**), but
        # --add-dir grants WRITE access too — and one or more agent runs used
        # that to modify editor/app.js, editor/styles.css, and drop generated
        # files into editor/assets/ without user permission. The protocol-root
        # write access is the bug; protocol-root READ access is what was
        # actually needed. Claude Code's Read tool can open absolute paths
        # outside --add-dir'd directories (and Bash `cat` runs at the shell's
        # filesystem permission level, which can read anywhere the user can),
        # so dropping --add-dir INSTALL_ROOT preserves reads while removing
        # the unsanctioned-write surface. See AGENTS.md "Editor source is OFF
        # LIMITS" for the policy this enforces.
        spawn_args += ["--add-dir", project_root]
        run_id = uuid.uuid4().hex[:16]
        env = _build_child_env(agent_id, run_id,
                               project_root=project_root, project_id=project_id)
        try:
            proc = subprocess.Popen(
                [bin_path, *spawn_args],
                cwd=project_root,
                stdin=subprocess.PIPE if defs["prompt_via_stdin"] else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,
            )
        except FileNotFoundError:
            return None, (500, {"error": f"{bin_path}: not executable"})
        except Exception as e:
            return None, (500, {"error": f"spawn failed: {type(e).__name__}: {e}"})
        state = RunState(run_id, proc, agent_id, branch, "node-agent", title,
                         project_id=project_id, project_root=project_root)
        state.bin_path = bin_path
        state.permission_mode = permission_mode
        state.modifying = True
        # Tag for the auto-completion hook in _drain_stdout — when this
        # subprocess exits, the daemon flips the workflow node to done/error.
        state.workflow_node_id = node_id
        # History bracket — same shape as _run_create's pre/post-snapshot.
        state.history_pending_id = None
        state.history_before_paths = []
        state.history_before_rows  = []
        try:
            eid, paths, rows, _ = _history_run_snapshot_before(project_root)
            state.history_pending_id  = eid
            state.history_before_paths = paths
            state.history_before_rows  = rows
        except Exception as e:
            state.append("status", {"label": "history-snapshot-failed", "detail": str(e)})
        state.append("status", {
            "label": "spawned",
            "agentId": agent_id,
            "branch": branch,
            "kind": "node-agent",
            "nodeId": node_id,
            "promptPreview": prompt_text[:240],
        })
        with RUNS_LOCK:
            RUNS[run_id] = state
        if defs["prompt_via_stdin"]:
            try:
                proc.stdin.write(_claude_user_frame(prompt_text))
                proc.stdin.flush()
            except Exception as e:
                state.append("error", {"message": f"failed to write prompt to stdin: {e}"})
        threading.Thread(target=_drain_stdout, args=(state,), daemon=True,
                         name=f"run-{run_id}-stdout").start()
        threading.Thread(target=_drain_stderr, args=(state,), daemon=True,
                         name=f"run-{run_id}-stderr").start()
        return run_id, None

    # ── POST /__workflow/node/<id>/run ──────────────────────────────────
    # Phase 3 of onboarding orchestration: the missing "run this node by id"
    # verb. Looks up the node in workflow.json, walks upstream edges to
    # build an input context, dispatches based on the node's kind/skill,
    # writes the output back to the node's `text` field, updates runStatus,
    # and returns the result synchronously. Wraps the workflow.json write
    # in a history bracket so the whole node-run is undoable as one entry.
    #
    # v2.1 — agent-kind nodes now spawn a focused subprocess via
    # `_spawn_node_agent` (no longer return `manual: true`). The endpoint
    # returns the runId immediately; the canvas node's runStatus is updated
    # automatically when the subprocess exits (hook in `_drain_stdout`).
    def _workflow_node_run(self, qs, node_id):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        # Body is optional — most calls just need the node id from the URL.
        # When present, body can override the node's stored prompt etc.
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception:
            body = {}
        if not isinstance(body, dict): body = {}

        # Load workflow.json
        wf_path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(wf_path):
            return self._reply(404, {"error": "workflow.json not found", "path": wf_path})
        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf = json.load(f)
        except Exception as e:
            return self._reply(500, {"error": f"failed to read workflow.json: {e}"})
        nodes_by_id = {n.get("id"): n for n in (wf.get("nodes") or []) if isinstance(n, dict) and n.get("id")}
        node = nodes_by_id.get(node_id)
        if not node:
            return self._reply(404, {"error": f"node not found: {node_id!r}", "known": sorted(nodes_by_id.keys())[:20]})

        # Collect upstream content by walking incoming edges. The result is a
        # single text blob the dispatcher prepends to the node's own prompt.
        upstream_chunks = []
        for e in (wf.get("edges") or []):
            to_ref = (e.get("to") or "")
            if to_ref.split(".", 1)[0] != node_id: continue
            from_id = (e.get("from") or "").split(".", 1)[0]
            up = nodes_by_id.get(from_id)
            if not up: continue
            label = up.get("title") or up.get("name") or from_id
            kind = up.get("kind")
            if kind == "folder":
                rel = (up.get("path") or "").lstrip("/")
                try:
                    fp = _safe_join(project_root, rel)
                except ValueError:
                    continue
                if os.path.isfile(fp):
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                            upstream_chunks.append(f"### {label} (file: {rel})\n{fh.read()}")
                    except OSError:
                        pass
            elif kind in ("prompt", "skill"):
                # v2.12a — skill nodes store the LLM response in `output`; the
                # `text` field is the user-editable prompt. Prefer output when
                # set so downstream consumers walk the response, not the
                # instruction. For prompt kind, only text exists.
                txt = ((up.get("output") if kind == "skill" else None) or up.get("text") or "").strip()
                if txt: upstream_chunks.append(f"### {label}\n{txt}")
            elif kind in ("ds-brainstorm", "iterator-remix", "agent"):
                # Pull whatever the node stored as output, if anything.
                txt = (up.get("output") or up.get("text") or "").strip() if isinstance(up.get("output"), str) else (up.get("text") or "").strip()
                if txt: upstream_chunks.append(f"### {label} ({kind})\n{txt}")
        upstream_text = "\n\n".join(upstream_chunks)

        # v2.50 — DOWNSTREAM walk. Previously only incoming edges were read, so
        # wiring `agent → asset(path=foo.html)` told the agent NOTHING about
        # where to write — the link was decorative and the agent was clueless
        # about its output destination. Now: walk OUTGOING edges, and for any
        # downstream node that declares a file destination (asset.path,
        # folder.path) OR a kind whose registry contract has an outputsRoot,
        # tell the agent explicitly to write there. This makes the link
        # semantically meaningful: you wire an agent to a file node to say
        # "your output goes here."
        downstream_targets = []
        for e in (wf.get("edges") or []):
            from_ref = (e.get("from") or "")
            if from_ref.split(".", 1)[0] != node_id: continue
            to_id = (e.get("to") or "").split(".", 1)[0]
            dn = nodes_by_id.get(to_id)
            if not dn: continue
            dkind = dn.get("kind")
            dlabel = dn.get("title") or dn.get("name") or to_id
            dpath = (dn.get("path") or "").lstrip("/")
            if dkind == "asset" and dpath:
                ak = dn.get("assetKind") or "file"
                downstream_targets.append(f"- Write your {ak} output to `{dpath}` (wired to asset node “{dlabel}”).")
            elif dkind == "folder" and dpath:
                downstream_targets.append(f"- Write outputs into `{dpath}` (wired to folder node “{dlabel}”).")
            else:
                # Registry-declared outputsRoot for the downstream kind.
                try:
                    from kinds.registry import kind_contract as _kc
                    c = _kc(dkind, to_id)
                    root = c.get("outputsRoot") if c else None
                    if root:
                        proto_slug = node.get("prototype") or node.get("branch") or "main"
                        resolved = root.replace("{prototype}", proto_slug) \
                                       .replace("{branch}", proto_slug) \
                                       .replace("{variant}", dn.get("variant") or "") \
                                       .replace("{dsId}", dn.get("dsId") or "main") \
                                       .replace("{id}", to_id)
                        downstream_targets.append(f"- Feed the `{dlabel}` node ({dkind}); it expects its inputs under `{resolved}`.")
                except Exception:
                    pass
        downstream_text = ""
        if downstream_targets:
            downstream_text = ("This node is wired to the following OUTPUT destinations — "
                               "write your results there so the canvas reflects them:\n"
                               + "\n".join(downstream_targets))

        kind = node.get("kind")
        out  = None
        err  = None

        # v2.19a/b — populate-before-dispatch gate. Refuse /run when the node
        # carries the scaffolder's generic template (which is project-agnostic
        # placeholder content meant for the orchestrator to override). Without
        # this gate, the orchestrator can silently dispatch with template text
        # that produces generic output — the "lying canvas" pattern the user
        # called out for v2.18. Gates run BEFORE the runStatus="running" flip
        # so a refused dispatch leaves the node untouched.
        if kind == "skill" and isinstance(node_id, str) and node_id.startswith("bs_html_"):
            try:
                idx = int(node_id.split("_")[-1]) - 1
                if 0 <= idx <= 2:
                    if (node.get("text") or "").strip() == _bs_html_default_text(idx).strip():
                        return self._reply(400, {
                            "error": "bs_html_* dispatch refused — text is still the scaffolder generic template",
                            "nodeId": node_id,
                            "hint": (
                                "Per skill §5.9, the orchestrator MUST overwrite "
                                f"{node_id}.text with the page #{idx+1} spec from "
                                "bp_chunks.output (project-specific page goal, "
                                "audience, shell, imagery) before calling /run."
                            ),
                        })
            except (ValueError, TypeError):
                pass
        if kind == "iterator-remix" and isinstance(node_id, str) and node_id.startswith("br_remix_p"):
            variants = node.get("variants")
            if isinstance(variants, list) and variants == REMIX_VARIANT_DEFAULTS:
                return self._reply(400, {
                    "error": "iterator-remix dispatch refused — variants are still the scaffolder defaults",
                    "nodeId": node_id,
                    "hint": (
                        "Per skill §5.9, the orchestrator MUST POST picked-DS-aware "
                        f"variants to {node_id} via /status before calling /run. The "
                        "defaults (denser/calmer/editorial) are project-agnostic — "
                        "they need to reference the picked DS's tokens, the page's "
                        "actual purpose, and the audience emotion."
                    ),
                })

        # Flip status to "running" on disk so the editor / orchestrator can
        # see it spinning. Saved at the very end with the final status.
        node["runStatus"] = "running"
        # v2.1 — agent kind dispatches an async subprocess; we keep
        # runStatus="running" on disk and let the completion hook in
        # _drain_stdout flip it to done/error when the child exits. Sync
        # dispatches (folder, prompt, skill=llm) still mark "done" inline.
        async_dispatched = False

        try:
            if kind == "folder":
                rel = (node.get("path") or "").lstrip("/")
                try:
                    fp = _safe_join(project_root, rel)
                except ValueError:
                    raise ValueError(f"bad folder path: {rel!r}")
                if os.path.isfile(fp):
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        out = {"text": fh.read(), "path": rel}
                elif os.path.isdir(fp):
                    listing = sorted(os.listdir(fp))
                    out = {"text": "\n".join(listing), "path": rel, "dir": True}
                else:
                    out = {"text": "", "path": rel, "missing": True}

            elif kind == "prompt":
                # Static prompt — its "output" is just its stored text.
                out = {"text": (node.get("text") or "").strip()}

            elif kind == "skill" and node.get("skill") == "llm":
                # Build the prompt by stacking upstream + the node's own
                # instruction. Body can override `prompt` per-call.
                base = (body.get("prompt") or node.get("text") or "").strip()
                if not base and not upstream_text:
                    raise ValueError("no prompt and no upstream content — nothing to send to the LLM")
                full_prompt = base
                if upstream_text:
                    full_prompt = f"<context>\n{upstream_text}\n</context>\n\n{base}".strip()
                # v2.50 — include downstream output destinations so the LLM
                # knows where its result is expected to land.
                if downstream_text:
                    full_prompt = full_prompt + "\n\n<output-destinations>\n" + downstream_text + "\n</output-destinations>"
                text = self._llm_dispatch(node, full_prompt)
                out = {"text": text, "provider": node.get("provider") or "anthropic",
                       "model": node.get("model") or "claude-opus-4-7"}
                # v2.12a — store the LLM response in node['output'], NOT
                # node['text']. node['text'] stays the user-editable prompt;
                # the response lives in 'output' so the frontend's debounced
                # workflow.json save can't stomp it back to the prompt.
                # Downstream upstream-walks prefer .output over .text for
                # skill kind, so the data flow is unchanged.
                node["output"] = text

            # v2.10 — `prompt-refiner` (my v2.7 kind) was removed. The
            # existing `iterator-refiner` library node owns brief refinement;
            # it's driven client-side via setupRefiner (not /run-dispatchable
            # from the daemon yet). Orchestrator handles it as a user-action
            # checkpoint and reads the spawned output node after completion.

            elif kind == "agent":
                # v2.1 — focused per-node subprocess dispatch. The per-node
                # preamble (from node_agent_preambles) is the entire system
                # prompt; the upstream walk gives the dispatched subagent
                # context about wired inputs. Returns the runId immediately;
                # the canvas node flips to "done" / "error" automatically
                # when the subprocess exits via _drain_stdout's hook.
                branch = _qs_prototype(qs) if hasattr(qs, "get") else "main"
                # Resolve the prototype slug — prefer the project's active one, else "main".
                try:
                    ws_json = os.path.join(project_root, "..", "..", "workspace.json")
                    if os.path.isfile(ws_json):
                        # Branch hint from workspace.json may be future work; for v2.1
                        # the workflow only scaffolds against branch=main.
                        pass
                except Exception: pass
                preamble_title, preamble_body = _node_preambles.render(
                    node_id, node.get("text") or "", branch,
                )
                # Compose the per-run prompt: upstream context block + a short
                # kick-off line + downstream output destinations. The system
                # prompt carries the task framing.
                kick = f"Begin the task for node `{node_id}`. The wired upstream context follows:"
                prompt_text = (kick + "\n\n<context>\n" + (upstream_text or "(no upstream context)") + "\n</context>") if upstream_text else kick
                # v2.50 — tell the agent where its output goes (downstream wiring).
                if downstream_text:
                    prompt_text += "\n\n<output-destinations>\n" + downstream_text + "\n</output-destinations>"
                project_id = (qs.get("project") or ["default"])[0] if hasattr(qs, "get") else "default"
                run_id, err_reply = self._spawn_node_agent(
                    project_root = project_root,
                    project_id   = project_id,
                    branch       = branch,
                    node_id      = node_id,
                    system_prompt= preamble_body,
                    prompt_text  = prompt_text,
                    title        = preamble_title,
                )
                if err_reply:
                    raise RuntimeError(err_reply[1].get("error") or "spawn failed")
                # Leave runStatus="running" — the subprocess completion hook
                # will set it to "done" or "error" when it exits.
                node["runStatus"] = "running"
                # v2.20 — write BOTH field names. `runRunId` is the original
                # daemon-side field (kept for daemon-merge backward compat in
                # app.js:11297); `runId` is what WorkflowAgentNode (app.js
                # :26435 and ~12 other sites) actually reads to fetch the
                # SSE-backed transcript via /__run/<id>. Without `runId` the
                # chat tab on agent nodes shows nothing even though the subprocess
                # is producing events the daemon captured.
                node["runId"]    = run_id
                node["runRunId"] = run_id
                node.pop("runError", None)
                async_dispatched = True
                out = {
                    "spawned": True,
                    "runId":   run_id,
                    "kind":    kind,
                    "hint":    "Subprocess dispatched. Poll /__run/<runId> for live status; the node's runStatus will flip on the canvas when the subprocess exits.",
                }

            elif kind in ("ds-brainstorm", "iterator-remix"):
                # Still manual in v2.1 — the orchestrator handles these by
                # writing the artifact files directly + POSTing
                # /__workflow/node/<id>/status to flip the canvas. Future v2.4
                # may add a daemon dispatch for these too.
                out = {
                    "manual": True,
                    "hint":   f"kind={kind!r} is handled by the orchestrator skill — write artifacts then POST /__workflow/node/<id>/status to advance the canvas.",
                    "nodeFields": {k: node.get(k) for k in ("title", "name", "skill", "provider", "model", "variant", "n", "text") if k in node},
                }

            else:
                out = {
                    "manual": True,
                    "hint":   f"unhandled kind={kind!r} / skill={node.get('skill')!r}",
                }

            if not async_dispatched:
                node["runStatus"] = "done"
                node.pop("runError", None)
                # v3.0 — asset-versioning snapshot hook. Walk outgoing edges to
                # asset nodes and snapshot their canonical files into
                # workflow/runs/. Best-effort; failures don't fail the run.
                try:
                    from kinds.versioning import snapshot_downstream_assets
                    snapshot_downstream_assets(project_root, wf, node_id)
                except Exception as _vsn_err:
                    print(f"[asset-versioning] sync snapshot error on {node_id}: {_vsn_err}", flush=True)
        except Exception as e:
            node["runStatus"] = "error"
            node["runError"] = f"{type(e).__name__}: {e}"
            err = node["runError"]

        # Persist the updated workflow.json. Wrap in a history bracket so
        # the whole run becomes one undo entry (covering BOTH the status
        # flip and the cached output).
        try:
            with _history_bracket(project_root, ["workflow/workflow.json"],
                                   kind="workflow-op",
                                   label=f"Run node: {node.get('title') or node_id}",
                                   source="workflow",
                                   extra={"nodeId": node_id, "kind": kind}):
                with open(wf_path, "w", encoding="utf-8") as f:
                    json.dump(wf, f, indent=2)
        except Exception as e:
            return self._reply(500, {"error": f"failed to persist workflow.json: {e}"})
        # v2.30 — notify SSE subscribers
        _broadcast_workflow_change(os.path.basename(project_root.rstrip("/")))

        if err:
            return self._reply(500, {"ok": False, "nodeId": node_id, "kind": kind, "error": err})
        final_status = "running" if async_dispatched else "done"
        return self._reply(200, {"ok": True, "nodeId": node_id, "kind": kind, "runStatus": final_status, "output": out})

    # ── POST /__decision/<id>  (body: { value, label }) ─────────────────
    # Phase 4 of onboarding orchestration. Durability for the chat
    # `<decision-request>` protocol — when the user clicks an option, the
    # frontend BOTH sends a tagged user-message to the run AND POSTs here
    # so the choice survives a page reload. The orchestrator skill reads
    # DECISION_<id>.json on every turn (its first instruction) so it can
    # resume from a checkpoint without re-asking. Wrapped in _history_bracket
    # so undo reverts the decision artefact.
    def _decision_save(self, qs, decision_id):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        if not re.match(r"^[A-Za-z0-9_.-]{1,80}$", decision_id):
            return self._reply(400, {"error": f"invalid decision id: {decision_id!r}"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception:
            body = {}
        if not isinstance(body, dict): body = {}
        # v2.2 — `values` (array) is canonical. Legacy `value` (string) is
        # still accepted and normalised to a single-element array. Same
        # treatment for `labels` vs `label`. Empty submission → 400.
        raw_values = body.get("values")
        raw_labels = body.get("labels")
        if isinstance(raw_values, list):
            values = [str(v).strip() for v in raw_values if str(v).strip()]
        else:
            single = (body.get("value") or "").strip()
            values = [single] if single else []
        if isinstance(raw_labels, list):
            labels = [str(l).strip() for l in raw_labels]
        else:
            single_label = (body.get("label") or "").strip()
            labels = [single_label] if single_label else []
        if not values:
            return self._reply(400, {"error": "values required (or legacy value)"})
        # Pad labels to match values count.
        while len(labels) < len(values):
            labels.append(values[len(labels)])
        labels = labels[:len(values)]
        payload = {
            "id":         decision_id,
            "values":     values,
            "labels":     labels,
            # Legacy single-pick consumers read .value / .label — populate
            # with the first pick so they still work.
            "value":      values[0],
            "label":      labels[0],
            "answeredAt": _dt.datetime.now().isoformat(timespec="seconds"),
        }
        rel = f"DECISION_{decision_id}.json"
        try:
            abs_path = _safe_join(project_root, rel)
        except ValueError as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        pretty = ", ".join(labels[:3]) + ("…" if len(labels) > 3 else "")
        with _history_bracket(project_root, [rel],
                               kind="workflow-op",
                               label=f"Decision: {decision_id} → {pretty}",
                               source="workflow",
                               extra={"decisionId": decision_id, "values": values}):
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        return self._reply(200, {"ok": True, "path": rel, "values": values})

    # ── POST /__workflow/node/<id>/status (v2.1) ────────────────────────
    # Body: { runStatus?, text?, runError?, output? }. Atomically updates a
    # single node's status fields without rewriting the whole workflow.json
    # via the editor's PATCH path. Wrapped in _history_bracket so undo
    # rewinds the status change as one entry. Used by the orchestrator skill
    # after manual handling (e.g. "wrote 3 brainstorm HTMLs → mark bs_ds_*
    # as done") and by the auto-completion hook in _drain_stdout for
    # node-agent subprocesses.
    def _workflow_node_status(self, qs, node_id):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception:
            body = {}
        if not isinstance(body, dict): body = {}
        # v2.31 — serialize this read-modify-write block under the per-project
        # lock so concurrent /__workflow saves and other /status POSTs don't
        # write stale snapshots that revert the user's edit.
        # v2.50 — bounded by per-project semaphore (G5) + 2s acquire timeout
        # (G3). 503 + retry hint on contention so "busy" doesn't false-positive
        # as "daemon down". See WORKFLOW_TRUTHFULNESS_PLAN.md §11 D2.
        project_id = os.path.basename(project_root.rstrip("/"))
        _sem = _request_semaphore(project_id)
        if not _sem.acquire(timeout=5.0):
            return self._reply(503, {
                "error": "project request queue full (cap=3)",
                "hint": "retry in ~1s",
                "retryAfterMs": 1000,
            })
        try:
          _lk = _workflow_lock(project_id)
          if not _lk.acquire(timeout=2.0):
            return self._reply(503, {
                "error": "workflow locked (another write in progress)",
                "hint": "retry in ~1s",
                "retryAfterMs": 1000,
            })
          try:
            wf_path = os.path.join(project_root, "workflow", "workflow.json")
            if not os.path.isfile(wf_path):
                return self._reply(404, {"error": "workflow.json not found"})
            try:
                with open(wf_path, "r", encoding="utf-8") as f:
                    wf = json.load(f)
            except Exception as e:
                return self._reply(500, {"error": f"failed to read workflow.json: {e}"})
            nodes_by_id = {n.get("id"): n for n in (wf.get("nodes") or []) if isinstance(n, dict) and n.get("id")}
            node = nodes_by_id.get(node_id)
            if not node:
                return self._reply(404, {"error": f"node not found: {node_id!r}"})
            # Whitelist what callers can mutate via this endpoint. Mutating other
            # fields (kind, position, wiring) goes through the full /__workflow
            # PATCH path so the canvas merge logic runs.
            changed = {}
            if "runStatus" in body:
                v = body["runStatus"]
                if v in (None, "queued", "running", "done", "error", "skipped"):
                    # v2.17b — truthfulness guard for prompt-kind nodes. Marking a
                    # prompt node "done" while its text is empty (and the same POST
                    # isn't supplying text) creates a lying-canvas state: the node
                    # claims completion but has no content. Reject loudly so the
                    # caller fixes their flow (POST text + runStatus in one call,
                    # or POST text first then status). "skipped" stays unrestricted
                    # — that's the explicit "I'm choosing not to populate" signal.
                    if v == "done" and node.get("kind") == "prompt":
                        will_have_text = (
                            (isinstance(body.get("text"), str) and body["text"].strip())
                            or (isinstance(node.get("text"), str) and node["text"].strip())
                        )
                        if not will_have_text:
                            return self._reply(400, {
                                "error": "cannot mark prompt node 'done' with empty text",
                                "nodeId": node_id,
                                "hint": (
                                    "POST {text: '...', runStatus: 'done'} in one call, or "
                                    "POST the text first then the status. Use 'skipped' if "
                                    "you're intentionally leaving the node empty."
                                ),
                            })
                    node["runStatus"] = v
                    changed["runStatus"] = v
                    if v != "error": node.pop("runError", None)
            if "runError" in body and isinstance(body["runError"], (str, type(None))):
                if body["runError"]:
                    node["runError"] = body["runError"]
                    changed["runError"] = body["runError"]
                else:
                    node.pop("runError", None)
            if "text" in body and isinstance(body["text"], str):
                node["text"] = body["text"]
                changed["text"] = body["text"][:200] + ("…" if len(body["text"]) > 200 else "")
            if "output" in body:
                node["output"] = body["output"]
                changed["output"] = True
            # v2.13b — allow the orchestrator to populate the DS-generator's spec
            # (kind="design-system" node) from the picked variant's variant-spec
            # JSON. The React component validates spec.genre before letting the
            # user click ▶ Build, so the orchestrator MUST fill this in. Whitelist
            # is a shallow merge — top-level spec keys replace; the orchestrator
            # passes the full object.
            if "spec" in body and isinstance(body["spec"], dict):
                current = node.get("spec") if isinstance(node.get("spec"), dict) else {}
                merged = {**current, **body["spec"]}
                node["spec"] = merged
                changed["spec"] = list(body["spec"].keys())
            # v2.14c — allow the orchestrator to populate iterator-remix variants
            # (per-variant guidance strings). Array of 1..8 strings; replaces the
            # whole variants array (not a per-index merge — orchestrator passes
            # the full set). The React runRemix reads node.variants[i] as the
            # i-th variant's guidance, so populating these before the user clicks
            # Run gives meaningful direction differentiation.
            if "variants" in body and isinstance(body["variants"], list):
                cleaned = [str(v) for v in body["variants"]][:8]
                if cleaned:
                    node["variants"] = cleaned
                    changed["variants"] = len(cleaned)
            # v2.18a — iterator-refiner field whitelist. Lets the orchestrator
            # customize the interviewer prompt to the specific project (mentioning
            # the actual app domain / audience / emotion) instead of leaving the
            # scaffolder's generic templates that say "thin intake of App /
            # Audience / Emotion." setupRefiner reads these on click-time to
            # build the interviewer + interviewee prompts, so they MUST be
            # project-specific by the time the user clicks "✦ Setup loop".
            if node.get("kind") == "iterator-refiner":
                if "goal" in body and isinstance(body["goal"], str) and body["goal"].strip():
                    node["goal"] = body["goal"]
                    changed["goal"] = body["goal"][:120] + ("…" if len(body["goal"]) > 120 else "")
                if "focus" in body and isinstance(body["focus"], str) and body["focus"].strip():
                    node["focus"] = body["focus"]
                    changed["focus"] = body["focus"][:120] + ("…" if len(body["focus"]) > 120 else "")
                if "pushPast" in body and isinstance(body["pushPast"], list):
                    # Each entry must be {from, to} with string values.
                    cleaned_pp = []
                    for entry in body["pushPast"][:10]:
                        if not isinstance(entry, dict): continue
                        f = entry.get("from"); t = entry.get("to")
                        if not isinstance(f, str) or not isinstance(t, str): continue
                        if not f.strip() or not t.strip(): continue
                        cleaned_pp.append({"from": f, "to": t})
                    if cleaned_pp:
                        node["pushPast"] = cleaned_pp
                        changed["pushPast"] = len(cleaned_pp)
                if "maxTurns" in body:
                    try:
                        mt = int(body["maxTurns"])
                        if 1 <= mt <= 20:
                            node["maxTurns"] = mt
                            changed["maxTurns"] = mt
                    except (TypeError, ValueError):
                        pass
            if not changed:
                return self._reply(400, {"error": "no recognised fields in body",
                                          "accepted": ["runStatus", "text", "runError", "output", "spec", "variants",
                                                       "goal", "focus", "pushPast", "maxTurns (iterator-refiner only)"]})
            try:
                with _history_bracket(project_root, ["workflow/workflow.json"],
                                       kind="workflow-op",
                                       label=f"Node status: {node.get('title') or node_id} → {changed.get('runStatus') or 'updated'}",
                                       source="workflow",
                                       extra={"nodeId": node_id, "changed": list(changed.keys())}):
                    with open(wf_path, "w", encoding="utf-8") as f:
                        json.dump(wf, f, indent=2)
            except Exception as e:
                return self._reply(500, {"error": f"failed to persist workflow.json: {e}"})
            # v2.30 — notify SSE subscribers
            _broadcast_workflow_change(os.path.basename(project_root.rstrip("/")))
            return self._reply(200, {"ok": True, "nodeId": node_id, "changed": changed})
          finally:
            _lk.release()
        finally:
          _sem.release()

    # ── POST /__workflow/node/<id>/commit — D4 atomic producer ───────────
    # Implements WORKFLOW_TRUTHFULNESS_PLAN.md §6 and Rule 6 of AGENT_HARNESS.md.
    # Body shape:
    #   { outputs: {...}, files: [{relPath, content | contentBase64}, ...],
    #     runStatus: "done"|"error"|"running", runError?: "...",
    #     addNodes?: [...], addEdges?: [...] }
    # Actions, in order:
    #   1. Validate request (kind contract: outputs shape, completion criteria)
    #   2. Stage files: write to outputsRoot_staging/ first
    #   3. Validate staged: non-empty files, must-consume check on upstream
    #   4. Atomic rename: outputsRoot_staging/ → outputsRoot/
    #      (rotate any pre-existing outputsRoot/ to .prev.<timestamp>/)
    #   5. Update workflow.json (outputs + runStatus + commitRef + addNodes/addEdges)
    #   6. Broadcast workflow-changed + asset-changed SSE events
    def _workflow_node_commit(self, qs, node_id):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        # Concurrency guardrails (D2) — same shape as /save and /status.
        project_id = os.path.basename(project_root.rstrip("/"))
        _sem = _request_semaphore(project_id)
        if not _sem.acquire(timeout=5.0):
            return self._reply(503, {
                "error": "project request queue full (cap=3)",
                "hint": "retry in ~1s",
                "retryAfterMs": 1000,
            })
        try:
          try:
            body = self._read_json_body() or {}
          except Exception as e:
            return self._reply(400, {"error": f"invalid JSON body: {e}"})
          if not isinstance(body, dict):
            return self._reply(400, {"error": "commit body must be an object"})

          posted_outputs = body.get("outputs") or {}
          posted_files = body.get("files") or []
          run_status = body.get("runStatus") or "done"
          run_error = body.get("runError") or ""
          add_nodes = body.get("addNodes") or []
          add_edges = body.get("addEdges") or []
          caller_session_id = self.headers.get("X-Claude-Session-Id") or body.get("callerSessionId") or ""

          if not isinstance(posted_outputs, dict):
            return self._reply(400, {"error": "outputs must be an object"})
          if not isinstance(posted_files, list):
            return self._reply(400, {"error": "files must be an array"})
          if run_status not in ("running", "done", "error"):
            return self._reply(400, {"error": f"invalid runStatus: {run_status!r}"})

          # Lock + load workflow.json
          _lk = _workflow_lock(project_id)
          if not _lk.acquire(timeout=2.0):
            return self._reply(503, {"error": "workflow locked", "retryAfterMs": 1000})
          try:
            wf_path = os.path.join(project_root, "workflow", "workflow.json")
            if not os.path.isfile(wf_path):
              return self._reply(404, {"error": "workflow.json not found"})
            with open(wf_path, "r", encoding="utf-8") as f:
              wf = json.load(f)
            nodes_by_id = {n.get("id"): n for n in (wf.get("nodes") or []) if isinstance(n, dict)}
            node = nodes_by_id.get(node_id)
            if not node:
              return self._reply(404, {"error": f"node not found: {node_id!r}"})

            # Resolve the contract (kind + per-id overrides)
            try:
              from kinds.registry import kind_contract
              from kinds.validate  import validate_node, validate_consume
            except Exception as e:
              return self._reply(500, {"error": f"registry import failed: {e}"})
            contract = kind_contract(node.get("kind"), node_id)
            if not contract:
              return self._reply(400, {"error": f"unknown kind {node.get('kind')!r}", "nodeId": node_id})

            # Build a probe-node mirroring the proposed final state for
            # validation. Don't mutate workflow.json yet.
            probe = dict(node)
            probe["outputs"] = {**(node.get("outputs") or {}), **posted_outputs}
            probe["runStatus"] = run_status
            if run_error: probe["runError"] = run_error

            # Stage files first so completion's file-exists checks see them.
            outputs_root_tmpl = contract.get("outputsRoot")
            staging_dir = None
            committed_dir = None
            files_written = []
            if outputs_root_tmpl and posted_files:
              # Resolve outputsRoot path. If template ends with .md/.html (no
              # trailing slash) the target is a single file at that path —
              # we still write atomically (temp file + rename).
              resolved = outputs_root_tmpl
              _proto = node.get("prototype") or node.get("branch") or "main"
              for k, v in (("prototype", _proto),
                           ("branch", _proto),   # legacy alias
                           ("variant", node.get("variant") or ""),
                           ("dsId", node.get("dsId") or "main"),
                           ("simId", node.get("simId") or ""),
                           ("id", node_id)):
                resolved = resolved.replace("{" + k + "}", str(v))
              if "{" in resolved or "}" in resolved:
                return self._reply(400, {"error": "unresolved template in outputsRoot", "outputsRoot": resolved})
              committed_dir = os.path.join(project_root, resolved.lstrip("/").rstrip("/"))
              # Treat a path with an extension and a single posted file as
              # single-file commit semantics; otherwise it's a folder commit.
              is_single_file_target = (os.path.splitext(resolved)[1] != "" and len(posted_files) == 1
                                        and posted_files[0].get("relPath","") in ("", os.path.basename(resolved)))
              if is_single_file_target:
                # Write the one file atomically.
                tmp_path = committed_dir + ".staging"
                os.makedirs(os.path.dirname(committed_dir) or ".", exist_ok=True)
                content = posted_files[0].get("content")
                if content is None and posted_files[0].get("contentBase64"):
                  content = base64.b64decode(posted_files[0]["contentBase64"])
                if isinstance(content, str): content_bytes = content.encode("utf-8")
                elif isinstance(content, (bytes, bytearray)): content_bytes = bytes(content)
                else: return self._reply(400, {"error": "file content missing or wrong type"})
                with open(tmp_path, "wb") as f:
                  f.write(content_bytes)
                if len(content_bytes) == 0:
                  os.unlink(tmp_path)
                  return self._reply(400, {"error": "file is 0 bytes; commit rejected", "path": resolved})
                # Atomic rename
                os.replace(tmp_path, committed_dir)
                files_written.append(resolved)
              else:
                # Folder commit. Write everything to outputsRoot_staging/ then rename.
                staging_dir = committed_dir.rstrip("/") + "_staging"
                if os.path.exists(staging_dir):
                  # Clear previous staging
                  import shutil as _sh
                  try: _sh.rmtree(staging_dir)
                  except Exception: pass
                os.makedirs(staging_dir, exist_ok=True)
                for fspec in posted_files:
                  if not isinstance(fspec, dict): continue
                  rel = fspec.get("relPath") or ""
                  if not rel or ".." in rel.split("/"): continue
                  full = os.path.join(staging_dir, rel)
                  os.makedirs(os.path.dirname(full) or staging_dir, exist_ok=True)
                  content = fspec.get("content")
                  if content is None and fspec.get("contentBase64"):
                    content = base64.b64decode(fspec["contentBase64"])
                  if isinstance(content, str): cb = content.encode("utf-8")
                  elif isinstance(content, (bytes, bytearray)): cb = bytes(content)
                  else: continue
                  if len(cb) == 0:
                    # Skip empty files at staging — completion will catch.
                    continue
                  with open(full, "wb") as f:
                    f.write(cb)
                  files_written.append(os.path.join(resolved, rel))
                # Atomic rename: stage → committed; rotate any prior dir
                if os.path.exists(committed_dir):
                  prev = committed_dir.rstrip("/") + f".prev.{int(time.time())}"
                  try: os.replace(committed_dir, prev)
                  except Exception: pass
                os.replace(staging_dir, committed_dir)
                staging_dir = None  # cleaned up

                # v3.1 — MANIFEST.json auto-synthesis. If the subagent didn't
                # ship one, synthesize from the committed file list so the
                # versioning snapshotter can read subAssetInputs / files later.
                # The contract is: every multi-file producer emits MANIFEST.
                # We log a warning when synthesizing so subagent authors can
                # see they should fix their output. See
                # docs/features/asset-versioning.md §9.
                manifest_path = os.path.join(committed_dir, "MANIFEST.json")
                if not os.path.isfile(manifest_path):
                    try:
                        synthesized_files = []
                        for w in files_written:
                            rel = os.path.relpath(w, committed_dir)
                            if rel == "MANIFEST.json": continue
                            role = "entry" if rel.endswith(("index.html", "index.htm")) else "asset"
                            synthesized_files.append({"path": rel, "role": role})
                        manifest = {
                            "nodeId": node_id,
                            "synthesizedByDaemon": True,
                            "synthesizedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "files": synthesized_files,
                            "subAssetInputs": [],   # daemon can't infer; left empty
                        }
                        with open(manifest_path, "w", encoding="utf-8") as f:
                            json.dump(manifest, f, indent=2)
                        print(f"[manifest] synthesized for {node_id!r} (subagent should emit MANIFEST.json itself; "
                              f"sub-asset lineage will be empty until it does)", flush=True)
                    except Exception as e:
                        print(f"[manifest] synthesis failed for {node_id!r}: {e}", flush=True)

            # Now validate the probe (after files are placed)
            viols = validate_node(probe, "commit" if run_status == "done" else "status:" + run_status,
                                  project_root=project_root)
            # Run must-consume check if this is a consumer kind with consumeFrom
            cf = contract.get("consumeFrom")
            if cf and run_status == "done":
              # Resolve upstream folder via DECISION_cp_ds_pick if applicable
              src_tmpl = cf.get("source") or ""
              upstream_folder = None
              if "{picked.outputsRoot}" in src_tmpl:
                dec_path = os.path.join(project_root, "DECISION_cp_ds_pick.json")
                if os.path.isfile(dec_path):
                  try:
                    with open(dec_path) as df: dec = json.load(df)
                    picked = (dec.get("values") or [dec.get("value")])[0] if (dec.get("values") or dec.get("value")) else None
                    if picked:
                      from kinds.registry import KINDS as _K
                      ds_tmpl = (_K.get("ds-brainstorm") or {}).get("outputsRoot") or ""
                      _proto = node.get("prototype") or node.get("branch") or "main"
                      upstream_folder = os.path.join(project_root,
                        ds_tmpl.replace("{prototype}", _proto)
                               .replace("{branch}", _proto)
                               .replace("{variant}", picked).rstrip("/"))
                  except Exception: pass
              if upstream_folder:
                consume_viols = validate_consume(probe, upstream_folder, project_root)
                # Treat reject-policy violations as commit-blocking
                for v in consume_viols:
                  if v.get("severity") != "warn":
                    viols.append(v)
            if viols and run_status == "done":
              # Roll back: don't update workflow.json (files already on disk
              # remain; user can heal via reconciler).
              return self._reply(400, {
                "error": "contract validation failed",
                "nodeId": node_id,
                "violations": viols,
                "hint": "fix the violations and retry, OR set runStatus=error with runError",
              })

            # Mutate workflow.json
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")
            node["runStatus"] = run_status
            if run_error: node["runError"] = run_error
            if posted_outputs:
              node["outputs"] = {**(node.get("outputs") or {}), **posted_outputs}
            node["commitRef"] = {
              "at": now_iso,
              "callerSessionId": caller_session_id,
              "requestId": getattr(self, "request_id", None),
            }
            # Append addNodes / addEdges if extendsGraph
            extends_graph = bool(contract.get("extendsGraph"))
            added_node_ids = []
            added_edge_count = 0
            if extends_graph:
              if add_nodes:
                wf_nodes = wf.get("nodes") or []
                existing = {n.get("id") for n in wf_nodes if isinstance(n, dict)}
                for nn in add_nodes:
                  if not isinstance(nn, dict): continue
                  if not nn.get("id") or nn["id"] in existing: continue
                  wf_nodes.append(nn)
                  existing.add(nn["id"])
                  added_node_ids.append(nn["id"])
                wf["nodes"] = wf_nodes
              if add_edges:
                wf_edges = wf.get("edges") or []
                for ee in add_edges:
                  if not isinstance(ee, dict): continue
                  if not ee.get("from") or not ee.get("to"): continue
                  wf_edges.append(ee)
                  added_edge_count += 1
                wf["edges"] = wf_edges

            # Persist
            try:
              with _history_bracket(project_root, ["workflow/workflow.json"],
                                     kind="workflow-op",
                                     label=f"Commit: {node.get('title') or node_id} → {run_status}",
                                     source="workflow-commit",
                                     extra={"nodeId": node_id, "requestId": getattr(self, "request_id", None)}):
                with open(wf_path, "w", encoding="utf-8") as f:
                  json.dump(wf, f, indent=2)
            except Exception as e:
              return self._reply(500, {"error": f"failed to persist workflow.json: {e}"})

            _broadcast_workflow_change(project_id)
            if files_written:
              _broadcast_asset_change(project_id, files_written)
            return self._reply(200, {
              "ok": True,
              "nodeId": node_id,
              "runStatus": run_status,
              "filesWritten": files_written,
              "addedNodes": added_node_ids,
              "addedEdges": added_edge_count,
              "commitRef": node["commitRef"],
            })
          finally:
            _lk.release()
        finally:
          _sem.release()

    # ═══════════════════════════════════════════════════════════════════════
    # Asset-versioning endpoints (v3.0)
    # See docs/features/asset-versioning.md §7.2.
    # Every endpoint follows the same shape:
    #   1. resolve project + body
    #   2. acquire per-project semaphore + workflow lock (5s/2s timeouts)
    #   3. read workflow.json, find target node/version/composition
    #   4. mutate
    #   5. persist + _broadcast_workflow_change
    # ═══════════════════════════════════════════════════════════════════════

    def _versioning_open(self, qs):
        """Common boilerplate for all versioning endpoints. Resolves project,
        acquires lock + sem, loads workflow.json, returns (project_root,
        project_id, wf_path, wf, release_fn) or raises _VersioningHTTPError.

        The release_fn MUST be called in a finally block (lock + sem release).
        """
        project_root = resolve_project_root(qs, require_explicit=True)
        project_id = os.path.basename(project_root.rstrip("/"))
        sem = _request_semaphore(project_id)
        if not sem.acquire(timeout=5.0):
            raise _VersioningHTTPError(503, {
                "error": "project request queue full (cap=3)",
                "hint": "retry in ~1s", "retryAfterMs": 1000,
            })
        try:
            lk = _workflow_lock(project_id)
            if not lk.acquire(timeout=2.0):
                sem.release()
                raise _VersioningHTTPError(503, {
                    "error": "workflow locked (another write in progress)",
                    "hint": "retry in ~1s", "retryAfterMs": 1000,
                })
        except _VersioningHTTPError:
            raise
        except Exception:
            sem.release(); raise
        wf_path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(wf_path):
            lk.release(); sem.release()
            raise _VersioningHTTPError(404, {"error": "workflow.json not found"})
        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf = json.load(f)
        except Exception as e:
            lk.release(); sem.release()
            raise _VersioningHTTPError(500, {"error": f"failed to read workflow.json: {e}"})
        def _release():
            try: lk.release()
            finally: sem.release()
        return project_root, project_id, wf_path, wf, _release

    def _versioning_persist(self, project_root, project_id, wf_path, wf, label):
        """Persist workflow.json wrapped in a history bracket; broadcast SSE."""
        with _history_bracket(project_root, ["workflow/workflow.json"],
                              kind="workflow-op",
                              label=label,
                              source="versioning",
                              extra={"requestId": getattr(self, "request_id", None)}):
            with open(wf_path, "w", encoding="utf-8") as f:
                json.dump(wf, f, indent=2)
        _broadcast_workflow_change(project_id)

    def _versioning_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception:
            body = {}
        if not isinstance(body, dict): body = {}
        return body

    def _versioning_find(self, wf, node_id, vid=None, cid=None):
        """Locate (node, version, composition). Returns tuple with None for
        unrequested levels. Raises _VersioningHTTPError on miss."""
        nodes_by_id = {n.get("id"): n for n in (wf.get("nodes") or [])
                       if isinstance(n, dict) and n.get("id")}
        node = nodes_by_id.get(node_id)
        if not node:
            raise _VersioningHTTPError(404, {"error": f"node not found: {node_id!r}"})
        # v3.1 — versioning covers asset + prototype + design-system kinds.
        if node.get("kind") not in ("asset", "prototype", "design-system"):
            raise _VersioningHTTPError(400, {"error": f"node {node_id!r} is not versionable (kind={node.get('kind')!r}; expected asset / prototype / design-system)"})
        if vid is None: return node, None, None
        version = next((v for v in (node.get("versions") or [])
                        if isinstance(v, dict) and v.get("id") == vid), None)
        if not version:
            raise _VersioningHTTPError(404, {"error": f"version not found: {vid!r}"})
        if cid is None: return node, version, None
        comp = next((c for c in (version.get("compositions") or [])
                     if isinstance(c, dict) and c.get("id") == cid), None)
        if not comp:
            raise _VersioningHTTPError(404, {"error": f"composition not found: {cid!r}"})
        return node, version, comp

    # ── POST /__workflow/node/<id>/version/<vid>/revert ────────────────────
    def _workflow_version_revert(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, version, _ = self._versioning_find(wf, node_id, vid)
            node["activeVersionId"] = vid
            # Refresh source/ from the version's active composition's view dir.
            try:
                from kinds.versioning import refresh_source_from_view
                refresh_source_from_view(project_root, node)
            except Exception as e:
                print(f"[asset-versioning] revert refresh error: {e}", flush=True)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Revert: {node.get('title') or node_id} → {vid[:8]}")
            return self._reply(200, {"ok": True, "nodeId": node_id, "activeVersionId": vid,
                                     "activeCompositionId": version.get("activeCompositionId")})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/pin ───────────────────────
    def _workflow_version_pin(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, version, _ = self._versioning_find(wf, node_id, vid)
            body = self._versioning_body()
            if "pinned" in body and isinstance(body["pinned"], bool):
                version["pinned"] = body["pinned"]
            else:
                version["pinned"] = not bool(version.get("pinned"))
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Pin v={vid[:8]} pinned={version['pinned']}")
            return self._reply(200, {"ok": True, "pinned": version["pinned"]})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/label ─────────────────────
    def _workflow_version_label(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, version, _ = self._versioning_find(wf, node_id, vid)
            body = self._versioning_body()
            label = body.get("label")
            if label is not None and not isinstance(label, str):
                return self._reply(400, {"error": "label must be a string or null"})
            version["label"] = (label or None)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Label v={vid[:8]} → {version['label']!r}")
            return self._reply(200, {"ok": True, "label": version["label"]})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/thumb ─────────────────────
    # Body: raw PNG bytes (Content-Type: image/png). Or, for compatibility,
    # a JSON body { "dataUrl": "data:image/png;base64,..." }.
    def _workflow_version_thumb(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, version, _ = self._versioning_find(wf, node_id, vid)
            png_bytes = self._read_png_body()
            if not png_bytes:
                return self._reply(400, {"error": "no PNG body"})
            from kinds.versioning import runs_dir
            thumb_path = os.path.join(runs_dir(project_root, node_id, vid), "thumb.png")
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            with open(thumb_path, "wb") as f:
                f.write(png_bytes)
            # Path inside workflow.json stays as we declared in snapshot.
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Thumb v={vid[:8]} ({len(png_bytes)} bytes)")
            return self._reply(200, {"ok": True, "bytes": len(png_bytes),
                                     "path": version.get("thumbPath")})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── DELETE /__workflow/node/<id>/version/<vid> ─────────────────────────
    def _workflow_version_delete(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, version, _ = self._versioning_find(wf, node_id, vid)
            if node.get("activeVersionId") == vid:
                return self._reply(409, {"error": "cannot delete active version",
                                         "hint": "revert to another version first"})
            if version.get("pinned"):
                return self._reply(409, {"error": "cannot delete pinned version",
                                         "hint": "unpin first"})
            from kinds.versioning import _purge_version_dirs
            comp_ids = [c.get("id") for c in (version.get("compositions") or [])
                        if isinstance(c, dict) and c.get("id")]
            _purge_version_dirs(project_root, node_id, vid, comp_ids)
            node["versions"] = [v for v in node.get("versions") or []
                                if isinstance(v, dict) and v.get("id") != vid]
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Delete v={vid[:8]}")
            return self._reply(200, {"ok": True, "deleted": vid})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/branch ──────────────────────────
    # Body: { sourceVersionId: "...", sourceCompositionId?: "..." }
    # Creates a new asset node positioned below the source, with v0 copied
    # from the picked version + chosen composition.
    def _workflow_version_branch(self, qs, node_id):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            body = self._versioning_body()
            src_vid = body.get("sourceVersionId")
            src_cid = body.get("sourceCompositionId")
            if not isinstance(src_vid, str) or not src_vid:
                return self._reply(400, {"error": "sourceVersionId required"})
            node, version, _ = self._versioning_find(wf, node_id, src_vid)
            comp = None
            if src_cid:
                _, _, comp = self._versioning_find(wf, node_id, src_vid, src_cid)
            else:
                # Use the version's active composition.
                cid = version.get("activeCompositionId")
                if cid:
                    comp = next((c for c in (version.get("compositions") or [])
                                 if isinstance(c, dict) and c.get("id") == cid), None)

            from kinds.versioning import (make_ulid, runs_dir, view_dir,
                                           copy_tree_into, materialise_view)
            # Build new sibling node id (collision suffix _b, _b2, _b3, ...).
            existing_ids = {n.get("id") for n in (wf.get("nodes") or [])
                            if isinstance(n, dict) and n.get("id")}
            base_id = f"{node_id}_b"
            new_id = base_id
            n = 2
            while new_id in existing_ids:
                new_id = f"{base_id}{n}"; n += 1

            # Allocate new version + composition ids for the sibling.
            new_vid = make_ulid()
            new_cid = make_ulid()

            # ── BUG FIX: sibling must own its OWN canonical path. ─────────
            # If both nodes point at the same source/foo.png, the canvas
            # asset card renders from the live tree — which always shows
            # whatever the ORIGINAL's active version contains. Branching
            # then "appears" to just clone the active version. Reuse the
            # original's basename with a suffix derived from the new node id
            # so the sibling has independent bytes on disk and the picker's
            # picked-version content is what the user sees.
            existing_paths = set()
            for nn in (wf.get("nodes") or []):
                if not isinstance(nn, dict): continue
                p = nn.get("path")
                if isinstance(p, str) and p: existing_paths.add(p)
                ps = nn.get("paths")
                if isinstance(ps, list):
                    for x in ps:
                        if isinstance(x, str) and x: existing_paths.add(x)
            def _rename_path(orig: str) -> str:
                """Insert a suffix before the file extension so the sibling
                has a distinct path. Collision-shift if needed."""
                if not isinstance(orig, str) or not orig:
                    return orig
                base, ext = os.path.splitext(orig)
                # First try: just append "_b" (or _b2, _b3, ...) matching the
                # new_id suffix the user already sees on the node.
                suffix_n = new_id[len(node_id):] if new_id.startswith(node_id) else "_b"
                cand = f"{base}{suffix_n}{ext}"
                i = 2
                while cand in existing_paths:
                    cand = f"{base}{suffix_n}_{i}{ext}"
                    i += 1
                existing_paths.add(cand)
                return cand
            new_path  = _rename_path(node.get("path") or "")
            new_paths = [_rename_path(p) for p in (node.get("paths") or [])]
            # Build a rename map: original canonical → sibling canonical.
            rename_map: dict = {}
            if isinstance(node.get("path"), str) and node.get("path"):
                rename_map[node["path"]] = new_path
            if isinstance(node.get("paths"), list):
                for orig, renamed in zip(node["paths"], new_paths):
                    if isinstance(orig, str) and orig:
                        rename_map[orig] = renamed

            # Copy source version files → sibling's runs dir, RENAMING any
            # file whose canonical path is being remapped. This is what makes
            # the sibling's snap distinct from the original's.
            src_dir = runs_dir(project_root, node_id, src_vid)
            dst_dir = runs_dir(project_root, new_id, new_vid)
            os.makedirs(dst_dir, exist_ok=True)
            def _strip_source(p: str) -> str:
                return p[len("source/"):] if p.startswith("source/") else p
            # Build per-file rename within the runs dir layout.
            src_files = []
            for fe in (version.get("files") or []):
                if not isinstance(fe, dict): continue
                in_ver = fe.get("path")            # e.g. "main/images/foo.png"
                canon  = fe.get("canonical")       # e.g. "source/main/images/foo.png"
                if not in_ver: continue
                new_canon = rename_map.get(canon, canon)
                new_in_ver = _strip_source(new_canon) if isinstance(new_canon, str) else in_ver
                src_files.append({"in_old": in_ver, "in_new": new_in_ver,
                                  "canonical_new": new_canon})
            for fe in src_files:
                src_path = os.path.join(src_dir, fe["in_old"])
                dst_path = os.path.join(dst_dir, fe["in_new"])
                if not os.path.isfile(src_path): continue
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
            # Wipe any composition subdir that got copied along (we'll recreate one).
            shutil.rmtree(os.path.join(dst_dir, "compositions"), ignore_errors=True)
            # Also materialise the live canonical bytes for the sibling so the
            # asset card shows the PICKED version's image immediately, not the
            # original's active content.
            for fe in src_files:
                if not fe.get("canonical_new"): continue
                live = os.path.join(project_root, fe["canonical_new"].lstrip("/"))
                snap_src = os.path.join(dst_dir, fe["in_new"])
                if not os.path.isfile(snap_src): continue
                os.makedirs(os.path.dirname(live), exist_ok=True)
                shutil.copy2(snap_src, live)

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            # Sibling's v0 entry — deep copy of the source version's files +
            # canonical paths (REMAPPED) + non-asset consumedVersions.
            renamed_files = [{"path": fe["in_new"], "canonical": fe["canonical_new"]}
                             for fe in src_files]
            renamed_canonical = [fe["canonical_new"] for fe in src_files]
            new_version = {
                "id":                  new_vid,
                "createdAt":           now_iso,
                "runId":               None,
                "files":               renamed_files,
                "canonicalPaths":      renamed_canonical,
                "thumbPath":           f"workflow/runs/{new_id}/{new_vid}/thumb.png",
                "label":               f"branched from {(node.get('title') or node_id)} v{src_vid[:6]}",
                "pinned":              False,
                "branchedFrom":        {"nodeId": node_id, "versionId": src_vid,
                                         "compositionId": (comp or {}).get("id")},
                "consumedVersions":    json.loads(json.dumps(version.get("consumedVersions") or {})),
                "compositions":        [],
                "activeCompositionId": new_cid,
            }
            # Sibling's c0 — deep copy of the chosen composition (or a fresh
            # empty one if no comp was supplied).
            new_composition = {
                "id":                    new_cid,
                "createdAt":             now_iso,
                "consumedSubVersions":   json.loads(json.dumps((comp or {}).get("consumedSubVersions") or {})),
                "subAssetMounts":        json.loads(json.dumps((comp or {}).get("subAssetMounts") or {})),
                "thumbPath":             f"workflow/runs/{new_id}/{new_vid}/compositions/{new_cid}/thumb.png",
                "label":                 None,
                "pinned":                False,
                "degraded":              False,
            }
            new_version["compositions"].append(new_composition)

            # Compute placement: below source + collision shift.
            src_x = float(node.get("x") or 0)
            src_y = float(node.get("y") or 0)
            src_w = float(node.get("w") or 320)
            src_h = float(node.get("h") or 240)
            new_x, new_y = src_x, src_y + src_h + 80
            # Collision shift: scan existing nodes; bump right in 32px steps.
            def _collides(x, y, w, h):
                for nn in (wf.get("nodes") or []):
                    if not isinstance(nn, dict): continue
                    nx = float(nn.get("x") or 0); ny = float(nn.get("y") or 0)
                    nw = float(nn.get("w") or 320); nh = float(nn.get("h") or 240)
                    if (x < nx + nw and x + w > nx and y < ny + nh and y + h > ny):
                        return True
                return False
            steps = 0
            while _collides(new_x, new_y, src_w, src_h) and steps < 13:
                new_x += 32; steps += 1

            # Construct the sibling node — points at its OWN renamed paths.
            new_node = {
                "id":              new_id,
                "kind":             "asset",
                "assetKind":        node.get("assetKind"),
                "title":            f"{node.get('title') or node_id} (branch)",
                "x":                new_x,
                "y":                new_y,
                "w":                node.get("w"),
                "h":                node.get("h"),
                "size":             json.loads(json.dumps(node.get("size") or {})),
                "path":             new_path or node.get("path"),
                "paths":            new_paths or list(node.get("paths") or []),
                "versions":         [new_version],
                "activeVersionId":  new_vid,
                "branchedFrom":     {"nodeId": node_id, "versionId": src_vid,
                                      "compositionId": (comp or {}).get("id")},
                "runStatus":        "done",
            }
            wf.setdefault("nodes", []).append(new_node)

            # Materialise the sibling's view dir from its own runs/ snapshot.
            try:
                materialise_view(project_root, new_node, new_version, new_composition,
                                 sub_asset_pins=new_composition.get("consumedSubVersions"),
                                 sub_asset_mounts=new_composition.get("subAssetMounts"))
            except Exception as e:
                print(f"[asset-versioning] branch view materialise error: {e}", flush=True)

            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Branch from {node_id} v={src_vid[:8]} → {new_id}")
            return self._reply(200, {"ok": True, "newNodeId": new_id,
                                     "newVersionId": new_vid,
                                     "newCompositionId": new_cid,
                                     "placement": {"x": new_x, "y": new_y}})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/composition/<cid>/switch ──
    def _workflow_composition_switch(self, qs, node_id, vid, cid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, version, _ = self._versioning_find(wf, node_id, vid, cid)
            version["activeCompositionId"] = cid
            # Only switch source/ if this version is also the active one.
            try:
                if node.get("activeVersionId") == vid:
                    from kinds.versioning import refresh_source_from_view
                    refresh_source_from_view(project_root, node)
            except Exception as e:
                print(f"[asset-versioning] comp switch refresh error: {e}", flush=True)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Switch comp v={vid[:8]} → {cid[:8]}")
            return self._reply(200, {"ok": True, "activeCompositionId": cid})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/composition/<cid>/pin ─────
    def _workflow_composition_pin(self, qs, node_id, vid, cid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, _, comp = self._versioning_find(wf, node_id, vid, cid)
            body = self._versioning_body()
            if "pinned" in body and isinstance(body["pinned"], bool):
                comp["pinned"] = body["pinned"]
            else:
                comp["pinned"] = not bool(comp.get("pinned"))
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Pin comp v={vid[:8]} c={cid[:8]} → {comp['pinned']}")
            return self._reply(200, {"ok": True, "pinned": comp["pinned"]})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/composition/<cid>/label ───
    def _workflow_composition_label(self, qs, node_id, vid, cid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, _, comp = self._versioning_find(wf, node_id, vid, cid)
            body = self._versioning_body()
            label = body.get("label")
            if label is not None and not isinstance(label, str):
                return self._reply(400, {"error": "label must be a string or null"})
            comp["label"] = (label or None)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Label comp v={vid[:8]} c={cid[:8]} → {comp['label']!r}")
            return self._reply(200, {"ok": True, "label": comp["label"]})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/composition/<cid>/thumb ───
    def _workflow_composition_thumb(self, qs, node_id, vid, cid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, _, comp = self._versioning_find(wf, node_id, vid, cid)
            png_bytes = self._read_png_body()
            if not png_bytes:
                return self._reply(400, {"error": "no PNG body"})
            from kinds.versioning import runs_dir
            thumb_path = os.path.join(
                runs_dir(project_root, node_id, vid, cid), "thumb.png")
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            with open(thumb_path, "wb") as f:
                f.write(png_bytes)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Comp thumb v={vid[:8]} c={cid[:8]} ({len(png_bytes)} bytes)")
            return self._reply(200, {"ok": True, "bytes": len(png_bytes),
                                     "path": comp.get("thumbPath")})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/version/<vid>/composition ───────────────
    # Body: { subVersions: {subId: subVersionId, ...}, mounts?: {...},
    #         label?: "..." }
    def _workflow_composition_save(self, qs, node_id, vid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, version, _ = self._versioning_find(wf, node_id, vid)
            body = self._versioning_body()
            subv = body.get("subVersions") or {}
            mounts = body.get("mounts") or {}
            label = body.get("label")
            if not isinstance(subv, dict):
                return self._reply(400, {"error": "subVersions must be an object"})
            from kinds.versioning import make_ulid, materialise_view
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cid = make_ulid()
            comp = {
                "id":                    cid,
                "createdAt":             now_iso,
                "consumedSubVersions":   {k: v for k, v in subv.items() if isinstance(v, str)},
                "subAssetMounts":        {k: v for k, v in mounts.items() if isinstance(v, str)},
                "thumbPath":             f"workflow/runs/{node_id}/{vid}/compositions/{cid}/thumb.png",
                "label":                 label if isinstance(label, str) else None,
                "pinned":                False,
                "degraded":              False,
            }
            version.setdefault("compositions", []).append(comp)
            version["activeCompositionId"] = cid
            # Materialise the view dir.
            try:
                materialise_view(project_root, node, version, comp,
                                 sub_asset_pins=comp["consumedSubVersions"],
                                 sub_asset_mounts=comp["subAssetMounts"])
            except Exception as e:
                print(f"[asset-versioning] comp-save view error: {e}", flush=True)
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Save comp v={vid[:8]} → {cid[:8]}")
            return self._reply(200, {"ok": True, "compositionId": cid})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── DELETE /__workflow/node/<id>/version/<vid>/composition/<cid> ───────
    def _workflow_composition_delete(self, qs, node_id, vid, cid):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            _, version, comp = self._versioning_find(wf, node_id, vid, cid)
            if version.get("activeCompositionId") == cid:
                return self._reply(409, {"error": "cannot delete active composition",
                                         "hint": "switch to another composition first"})
            if comp.get("pinned"):
                return self._reply(409, {"error": "cannot delete pinned composition",
                                         "hint": "unpin first"})
            from kinds.versioning import _purge_composition_dirs
            _purge_composition_dirs(project_root, node_id, vid, cid)
            version["compositions"] = [c for c in (version.get("compositions") or [])
                                       if isinstance(c, dict) and c.get("id") != cid]
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Delete comp v={vid[:8]} c={cid[:8]}")
            return self._reply(200, {"ok": True, "deleted": cid})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    # ── POST /__workflow/node/<id>/size ────────────────────────────────────
    # Body: { w?: number, h?: number, auto?: true }
    def _workflow_node_size(self, qs, node_id):
        try:
            project_root, project_id, wf_path, wf, release = self._versioning_open(qs)
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        try:
            node, _, _ = self._versioning_find(wf, node_id)
            body = self._versioning_body()
            if body.get("auto") is True:
                node.pop("w", None); node.pop("h", None)
                sz = node.setdefault("size", {})
                # Hard reset to fit-canvas. The previous `sz.get("scale") or
                # "fit-canvas"` preserved whatever was set (typically "custom"
                # from a prior drag), so "auto" never actually un-custom'd
                # the size. Caught by step 12 of the e2e test.
                sz["scale"] = "fit-canvas"
                msg = "auto"
            else:
                w, h = body.get("w"), body.get("h")
                if isinstance(w, (int, float)) and w > 0: node["w"] = float(w)
                if isinstance(h, (int, float)) and h > 0: node["h"] = float(h)
                sz = node.setdefault("size", {})
                sz["scale"] = "custom"
                msg = f"w={node.get('w')} h={node.get('h')}"
            self._versioning_persist(project_root, project_id, wf_path, wf,
                                     f"Size {node_id} → {msg}")
            return self._reply(200, {"ok": True, "w": node.get("w"), "h": node.get("h"),
                                     "size": node.get("size")})
        except _VersioningHTTPError as e:
            return self._reply(e.status, e.body)
        finally:
            release()

    def _read_png_body(self):
        """Read raw bytes from the POST body. Accepts either:
          • Content-Type: image/png — raw bytes
          • Content-Type: application/json {"dataUrl": "data:image/png;base64,..."}
        Returns bytes (possibly empty)."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except Exception:
            length = 0
        if length <= 0: return b""
        ctype = (self.headers.get("Content-Type") or "").lower()
        raw = self.rfile.read(length)
        if "image/png" in ctype:
            return raw
        # Else try to parse as JSON.
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            return b""
        if not isinstance(body, dict): return b""
        url = body.get("dataUrl") or body.get("data") or ""
        if not isinstance(url, str): return b""
        if url.startswith("data:"):
            try:
                url = url.split(",", 1)[1]
            except Exception:
                return b""
        try:
            import base64 as _b64
            return _b64.b64decode(url)
        except Exception:
            return b""

    # ── GET /__workflow/node/<id>/preview (v2.4) ─────────────────────────
    # Returns the prompt the daemon WOULD build right now for this node, by
    # walking upstream edges + concatenating node.text. Same logic as
    # _workflow_node_run uses on dispatch, just stops before the LLM/spawn
    # call. Lets the skill node UI render "this is what the next run will
    # send" so users can sanity-check the composed prompt or edit it.
    def _workflow_node_preview(self, qs, node_id):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        wf_path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(wf_path):
            return self._reply(404, {"error": "workflow.json not found"})
        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf = json.load(f)
        except Exception as e:
            return self._reply(500, {"error": f"failed to read workflow.json: {e}"})
        nodes_by_id = {n.get("id"): n for n in (wf.get("nodes") or []) if isinstance(n, dict) and n.get("id")}
        node = nodes_by_id.get(node_id)
        if not node:
            return self._reply(404, {"error": f"node not found: {node_id!r}"})
        # Walk incoming edges (same as _workflow_node_run) and compose the
        # upstream-context block. Keeping this in lockstep with the dispatch
        # logic is important — the preview must match what /run would send.
        upstream_chunks = []
        for e in (wf.get("edges") or []):
            to_ref = (e.get("to") or "")
            if to_ref.split(".", 1)[0] != node_id: continue
            from_id = (e.get("from") or "").split(".", 1)[0]
            up = nodes_by_id.get(from_id)
            if not up: continue
            label = up.get("title") or up.get("name") or from_id
            kind  = up.get("kind")
            if kind == "folder":
                rel = (up.get("path") or "").lstrip("/")
                try:
                    fp = _safe_join(project_root, rel)
                except ValueError:
                    continue
                if os.path.isfile(fp):
                    try:
                        with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                            upstream_chunks.append(f"### {label} (file: {rel})\n{fh.read()}")
                    except OSError:
                        pass
            elif kind in ("prompt", "skill"):
                # v2.12a — skill nodes store the LLM response in `output`; the
                # `text` field is the user-editable prompt. Prefer output when
                # set so downstream consumers walk the response, not the
                # instruction. For prompt kind, only text exists.
                txt = ((up.get("output") if kind == "skill" else None) or up.get("text") or "").strip()
                if txt: upstream_chunks.append(f"### {label}\n{txt}")
            elif kind in ("ds-brainstorm", "iterator-remix", "agent", "asset"):
                txt = (up.get("output") or up.get("text") or "").strip() if isinstance(up.get("output"), str) else (up.get("text") or "").strip()
                if txt: upstream_chunks.append(f"### {label} ({kind})\n{txt}")
        upstream_text = "\n\n".join(upstream_chunks)
        # Compose what /run would actually send for a skill=llm node. Other
        # kinds return their text or a "no preview available" hint.
        kind = node.get("kind")
        skill = node.get("skill")
        base = (node.get("text") or "").strip()
        if kind == "skill" and skill == "llm":
            if upstream_text:
                composed = f"<context>\n{upstream_text}\n</context>\n\n{base}".strip()
            else:
                composed = base
            return self._reply(200, {
                "ok": True, "nodeId": node_id, "kind": kind,
                "skill": skill,
                "upstream": upstream_text,
                "nodeText": base,
                "composed": composed,
                # v2.12a — expose the last LLM response so the UI / orchestrator
                # can see the actual output without dispatching again. None when
                # the node hasn't been run yet.
                "output":   node.get("output"),
                "provider": node.get("provider") or "anthropic",
                "model":    node.get("model")    or "claude-opus-4-7",
            })
        # v2.10 — `prompt-refiner` removed; iterator-refiner has no /preview
        # path (it's client-driven and its output is a separately spawned
        # prompt node, not a daemon-composable string).
        return self._reply(200, {
            "ok": True, "nodeId": node_id, "kind": kind,
            "upstream": upstream_text,
            "nodeText": base,
            "composed": base,
            "hint": f"Preview only assembles a 'composed prompt' for skill=llm nodes; this is kind={kind!r}.",
        })

    # ── GET /__workflow/node/<id> ───────────────────────────────────────
    # Read-only inspector for one node — used by the orchestrator skill to
    # poll a node's current `runStatus` / cached output without re-running.
    def _workflow_node_get(self, qs, node_id):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        wf_path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(wf_path):
            return self._reply(404, {"error": "workflow.json not found"})
        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf = json.load(f)
        except Exception as e:
            return self._reply(500, {"error": f"failed to read workflow.json: {e}"})
        node = next((n for n in (wf.get("nodes") or []) if isinstance(n, dict) and n.get("id") == node_id), None)
        if not node:
            return self._reply(404, {"error": f"node not found: {node_id!r}"})
        # v2.20 — backward-compat projection (see _workflow_get for the wider
        # version): project runRunId → runId on the wire so older nodes (pre-
        # v2.20) work with WorkflowAgentNode's chat tab without disk rewrites.
        if not node.get("runId") and node.get("runRunId"):
            node = dict(node)  # copy before mutating; don't pollute the in-memory wf
            node["runId"] = node["runRunId"]
        return self._reply(200, {"ok": True, "node": node})

    def _design_system_get(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        ds_root = os.path.join(project_root, "design-systems")
        ds_id = (qs.get("id") or [""])[0].strip().lower()
        # List mode: no id → enumerate every DS folder.
        if not ds_id:
            items = []
            if os.path.isdir(ds_root):
                for entry in sorted(os.listdir(ds_root)):
                    sub = os.path.join(ds_root, entry)
                    if not os.path.isdir(sub):
                        continue
                    if not SLUG_OK.match(entry):
                        continue
                    meta = self._design_system_read_meta(sub)
                    items.append({
                        "id": entry,
                        "version": meta.get("version") or "",
                        "label": meta.get("label") or "",
                        "genre": meta.get("genre") or "",
                        "exists": True,
                        "hasGallery": os.path.isfile(os.path.join(sub, "gallery.html")),
                        "hasStyles":  os.path.isfile(os.path.join(sub, "styles.css")),
                        "hasDesignMd": os.path.isfile(os.path.join(sub, "DESIGN.md")),
                    })
            return self._reply(200, {"items": items})
        # Single-DS mode.
        if not SLUG_OK.match(ds_id):
            return self._reply(400, {"error": "invalid ds id", "id": ds_id})
        ds_dir = os.path.join(ds_root, ds_id)
        if not os.path.isdir(ds_dir):
            return self._reply(404, {"error": "design system not found", "id": ds_id})
        styles_css   = self._design_system_read_file(ds_dir, "styles.css")
        gallery_html = self._design_system_read_file(ds_dir, "gallery.html")
        design_md    = self._design_system_read_file(ds_dir, "DESIGN.md")
        meta         = self._design_system_read_meta(ds_dir)
        return self._reply(200, {
            "id": ds_id,
            "version": meta.get("version") or "",
            "label":   meta.get("label") or "",
            "genre":   meta.get("genre") or "",
            "builtFrom": meta.get("builtFrom") or [],
            "parentRef": meta.get("parentRef"),
            "updates":   meta.get("updates") or [],
            "trio": {
                "stylesCss":   styles_css,
                "galleryHtml": gallery_html,
                "designMd":    design_md,
            },
            "exists": True,
        })

    def _design_system_save(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        ds_id = (qs.get("id") or [""])[0].strip().lower()
        if not ds_id or not SLUG_OK.match(ds_id):
            return self._reply(400, {"error": "missing or invalid ds id", "id": ds_id})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large", "bytes": length, "max": MAX_BYTES})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "body must be an object"})
        trio = body.get("trio") or {}
        if not isinstance(trio, dict):
            return self._reply(400, {"error": "trio must be an object"})
        styles_css   = trio.get("stylesCss") or ""
        gallery_html = trio.get("galleryHtml") or ""
        design_md    = trio.get("designMd") or ""
        spec         = body.get("spec") or {}
        label        = (body.get("label") or "").strip() or "v1"
        # Atomic writes — write to .staging/ first, then rename into place.
        ds_dir       = os.path.join(project_root, "design-systems", ds_id)
        staging_dir  = os.path.join(ds_dir, ".staging")
        try:
            os.makedirs(staging_dir, exist_ok=True)
        except Exception as e:
            return self._reply(500, {"error": f"could not create staging dir: {e}"})
        try:
            with open(os.path.join(staging_dir, "styles.css"),   "w", encoding="utf-8") as f: f.write(styles_css)
            with open(os.path.join(staging_dir, "gallery.html"), "w", encoding="utf-8") as f: f.write(gallery_html)
            with open(os.path.join(staging_dir, "DESIGN.md"),    "w", encoding="utf-8") as f: f.write(design_md)
        except Exception as e:
            return self._reply(500, {"error": f"could not write staging files: {e}"})
        # Content hash = sha256 of stylesCss + galleryHtml (DESIGN.md is
        # derived, so excluding it keeps re-export from bumping the version).
        h = hashlib.sha256()
        h.update(styles_css.encode("utf-8", errors="replace"))
        h.update(b"\x00")
        h.update(gallery_html.encode("utf-8", errors="replace"))
        version = h.hexdigest()[:16]
        # Preserve existing builtFrom + updates if present; append an updates
        # entry recording this write.
        prev_meta = self._design_system_read_meta(ds_dir)
        meta = {
            "id":        ds_id,
            "version":   version,
            "label":     label,
            "genre":     (spec.get("genre") if isinstance(spec, dict) else "") or prev_meta.get("genre") or "",
            "builtFrom": spec if isinstance(spec, dict) and spec else (prev_meta.get("builtFrom") or []),
            "parentRef": (spec.get("parentRef") if isinstance(spec, dict) else None) or prev_meta.get("parentRef"),
            "updates":   prev_meta.get("updates") or [],
        }
        meta["updates"].append({
            "version":    version,
            "label":      label,
            "appliedAt":  _dt.datetime.now().isoformat(timespec="seconds"),
        })
        try:
            with open(os.path.join(staging_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            return self._reply(500, {"error": f"could not write meta.json: {e}"})
        # Promote staging → live, one file at a time. os.replace is atomic
        # within the same filesystem. Wrap the promote + mirror write block
        # with a history bracket so undo restores the whole DS trio + mirror
        # atomically — DS edits should never be reverted half-way.
        mirror_dir  = os.path.join(project_root, "editor", "design-systems")
        try:
            os.makedirs(mirror_dir, exist_ok=True)
        except Exception:
            pass
        mirror_path = os.path.join(mirror_dir, ds_id + ".js")
        ds_paths = [
            os.path.relpath(os.path.join(ds_dir, n), project_root)
            for n in ("styles.css", "gallery.html", "DESIGN.md", "meta.json")
        ] + [os.path.relpath(mirror_path, project_root)]
        bracket_cm = _history_bracket(
            project_root, ds_paths,
            kind="workflow-op",
            label=f"DS update: {ds_id} → {label}",
            source="workflow",
            extra={"dsId": ds_id, "version": version},
        )
        with bracket_cm:
            for name in ("styles.css", "gallery.html", "DESIGN.md", "meta.json"):
                src = os.path.join(staging_dir, name)
                dst = os.path.join(ds_dir, name)
                try:
                    os.replace(src, dst)
                except Exception as e:
                    return self._reply(500, {"error": f"could not promote {name}: {e}"})
            try:
                os.rmdir(staging_dir)
            except Exception:
                pass  # leave .staging/ around if rmdir fails — harmless.
            # Runtime mirror — write editor/design-systems/<id>.js so the editor
            # can load the DS via a synchronous <script> tag at boot. Schema
            # mirrors window.EDITOR_DS_<id> in docs/agents/data-schema.md.
            mirror_body = (
                "// EDITOR_DS_" + ds_id + " — runtime mirror of design-systems/" + ds_id + "/.\n"
                "// Written by daemon on " + _dt.datetime.now().isoformat(timespec="seconds") + " (POST /__design_system).\n"
                "// The trio inlines the canonical files; tokens / primitives are derived offline.\n"
                "window.EDITOR_DS_" + ds_id + " = " + json.dumps({
                    "id":      ds_id,
                    "version": version,
                    "label":   label,
                    "trio": {
                        "stylesCss":   styles_css,
                        "galleryHtml": gallery_html,
                        "designMd":    design_md,
                    },
                    "meta": meta,
                }, ensure_ascii=False, indent=2) + ";\n"
            )
            try:
                with open(mirror_path, "w", encoding="utf-8") as f:
                    f.write(mirror_body)
            except Exception as e:
                return self._reply(500, {"error": f"could not write runtime mirror: {e}"})
        return self._reply(200, {
            "ok":      True,
            "id":      ds_id,
            "version": version,
            "label":   label,
            "paths": {
                "stylesCss":   os.path.relpath(os.path.join(ds_dir, "styles.css"),   project_root),
                "galleryHtml": os.path.relpath(os.path.join(ds_dir, "gallery.html"), project_root),
                "designMd":    os.path.relpath(os.path.join(ds_dir, "DESIGN.md"),    project_root),
                "meta":        os.path.relpath(os.path.join(ds_dir, "meta.json"),    project_root),
                "mirror":      os.path.relpath(mirror_path, project_root),
            },
        })

    # ── GET /__ds_bootstrap ──────────────────────────────────────────────
    # Concatenates every editor/design-systems/*.js runtime mirror into a
    # single JS response, plus a window.EDITOR_DS_REGISTRY index of available
    # ids. The editor's index.html includes this as a <script> tag right
    # after data.js so window.EDITOR_DS_<id> is available globally before
    # app.js mounts. Per-DS files are produced by POST /__design_system.
    def _ds_bootstrap(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        mirror_dir = os.path.join(project_root, "editor", "design-systems")
        ids = []
        body_parts = ["// /__ds_bootstrap — concatenated DS runtime mirrors\n"]
        if os.path.isdir(mirror_dir):
            for entry in sorted(os.listdir(mirror_dir)):
                if not entry.endswith(".js"):
                    continue
                ds_id = entry[:-3]
                if not SLUG_OK.match(ds_id):
                    continue
                fp = os.path.join(mirror_dir, entry)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        body_parts.append(f.read())
                        body_parts.append("\n")
                    ids.append(ds_id)
                except Exception:
                    # Skip unreadable files; surfacing wouldn't help here
                    # — the per-DS GET will produce a useful error.
                    continue
        body_parts.append("window.EDITOR_DS_REGISTRY = " + json.dumps(ids) + ";\n")
        body = "".join(body_parts).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # No-cache so a POST /__design_system → page reload immediately picks
        # up the new mirror. Bootstrap is small; caching adds no real win.
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
        return

    # ── GET /__ds_proposals ──────────────────────────────────────────────
    # Reports whether DS_PROPOSAL.md is present at project root, counts the
    # proposal sections, AND parses each entry into structured form so the
    # editor's review modal can render verdict toggles without re-parsing
    # the markdown client-side. The file itself remains the source of truth
    # — POST /__ds_proposals writes verdicts back.
    def _ds_proposals_get(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        path = os.path.join(project_root, "DS_PROPOSAL.md")
        if not os.path.isfile(path):
            return self._reply(200, {"exists": False, "count": 0, "entries": [], "path": "DS_PROPOSAL.md"})
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            return self._reply(500, {"error": f"DS_PROPOSAL.md unreadable: {e}"})
        entries = self._ds_proposals_parse(text)
        by_primitive = {}
        for ent in entries:
            prim = ent.get("primitive") or ""
            if prim:
                by_primitive[prim] = by_primitive.get(prim, 0) + 1
        return self._reply(200, {
            "exists":      True,
            "count":       len(entries),
            "byPrimitive": by_primitive,
            "entries":     entries,
            "path":        "DS_PROPOSAL.md",
            "bytes":       len(text.encode("utf-8")),
        })

    # Parses DS_PROPOSAL.md into structured entries. Tolerant of missing
    # fields — agents may not always fill every line. The shape mirrors
    # what Subagent 6 (DS-audit) emits per
    # docs/agents/subagents/6-design-system.md.
    def _ds_proposals_parse(self, text):
        # Split on the H2 headers. A header line looks like:
        #   ## Proposal 1: Button — primary-icon-small variant
        # We use a regex that captures everything from one header to the
        # next-header-or-EOF, then parse fields out of each chunk.
        headers = list(re.finditer(
            r"(?m)^##\s+Proposal\s+(\d+):\s*(.+?)\s*$",
            text,
        ))
        entries = []
        for i, m in enumerate(headers):
            idx = int(m.group(1))
            title = m.group(2).strip()
            body_start = m.end()
            body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            body = text[body_start:body_end]
            # Title pattern: "Button — primary-icon-small variant" or
            # "Button - primary-icon-small variant" — split on em-dash or hyphen.
            primitive = ""
            variant = ""
            tm = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*[—–-]\s*(.+?)(?:\s+variant)?\s*$", title)
            if tm:
                primitive = tm.group(1)
                variant = tm.group(2).strip()
            else:
                primitive = (title.split()[0] if title else "")
            # Field extractors — bold-marker pattern with optional inline-code value.
            def grab(label):
                pat = r"\*\*" + re.escape(label) + r":\*\*\s*([^\n]+)"
                mm = re.search(pat, body)
                return (mm.group(1).strip() if mm else "")
            class_signature = grab("Class signature")
            # Strip surrounding backticks if present
            class_signature = class_signature.strip("`").strip()
            closest_existing = grab("Closest existing in DS")
            # The "Closest existing" line often has trailing parens with delta info — keep it as-is.
            rationale = grab("Rationale")
            used_in_raw = grab("Used in")
            used_in = []
            for ref in used_in_raw.split(","):
                ref = ref.strip()
                if not ref:
                    continue
                # Strip leading inline-code backticks
                ref = ref.strip("`").strip()
                line = 0
                file_part = ref
                if ":" in ref:
                    parts = ref.rsplit(":", 1)
                    if parts[1].isdigit():
                        file_part = parts[0]
                        line = int(parts[1])
                used_in.append({"file": file_part, "line": line})
            # Verdict — find the first checked box in the entry body.
            verdict = None
            for label in ("Accept", "Reject", "Defer"):
                if re.search(r"-\s+\[x\]\s+" + re.escape(label), body, re.IGNORECASE):
                    verdict = label.lower()
                    break
            entries.append({
                "index":           idx,
                "primitive":       primitive,
                "variant":         variant,
                "classSignature":  class_signature,
                "closestExisting": closest_existing,
                "rationale":       rationale,
                "usedIn":          used_in,
                "verdict":         verdict,
            })
        return entries

    # ── POST /__ds_proposals ─────────────────────────────────────────────
    # Writes verdicts back into DS_PROPOSAL.md by flipping the checkbox per
    # entry. Body: { "verdicts": [{ "index": 1, "verdict": "accept" }, …] }.
    # `verdict` is one of: "accept" | "reject" | "defer" | null (clears all).
    # The file's structure is otherwise preserved — only the three checkbox
    # lines per entry are rewritten. Workflow 6 reads the resulting file to
    # partition entries by verdict.
    def _ds_proposals_save(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        path = os.path.join(project_root, "DS_PROPOSAL.md")
        if not os.path.isfile(path):
            return self._reply(404, {"error": "DS_PROPOSAL.md not found"})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large", "bytes": length, "max": MAX_BYTES})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        verdicts_in = body.get("verdicts") or []
        if not isinstance(verdicts_in, list):
            return self._reply(400, {"error": "verdicts must be an array"})
        # index → verdict map
        wanted = {}
        for v in verdicts_in:
            if not isinstance(v, dict): continue
            idx = v.get("index")
            verd = v.get("verdict")
            if not isinstance(idx, int): continue
            if verd not in (None, "accept", "reject", "defer"): continue
            wanted[idx] = verd
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            return self._reply(500, {"error": f"DS_PROPOSAL.md unreadable: {e}"})
        # Re-parse to get entry spans, then rewrite the checkbox lines in
        # each entry that has a verdict in `wanted`.
        headers = list(re.finditer(
            r"(?m)^##\s+Proposal\s+(\d+):\s*(.+?)\s*$",
            text,
        ))
        chunks = []
        cursor = 0
        applied = 0
        for i, m in enumerate(headers):
            idx = int(m.group(1))
            body_start = m.end()
            body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            # Append pre-entry text unchanged
            chunks.append(text[cursor:body_start])
            entry_body = text[body_start:body_end]
            if idx in wanted:
                desired = wanted[idx]
                # Clear all three first, then set the desired one (if any).
                def _flip(b, label, on):
                    pat = re.compile(r"(-\s+\[)([ x])(\]\s+" + re.escape(label) + r")", re.IGNORECASE)
                    return pat.sub(lambda mm: mm.group(1) + ("x" if on else " ") + mm.group(3), b, count=1)
                entry_body = _flip(entry_body, "Accept", desired == "accept")
                entry_body = _flip(entry_body, "Reject", desired == "reject")
                entry_body = _flip(entry_body, "Defer",  desired == "defer")
                applied += 1
            chunks.append(entry_body)
            cursor = body_end
        chunks.append(text[cursor:])
        new_text = "".join(chunks)
        try:
            # Atomic write: tmp file → rename.
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new_text)
            os.replace(tmp, path)
        except Exception as e:
            return self._reply(500, {"error": f"could not write DS_PROPOSAL.md: {e}"})
        return self._reply(200, {"ok": True, "applied": applied, "path": "DS_PROPOSAL.md"})

    def _design_system_read_file(self, ds_dir, name):
        path = os.path.join(ds_dir, name)
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _design_system_read_meta(self, ds_dir):
        path = os.path.join(ds_dir, "meta.json")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    # ── GET /__resolve_font?name=<family> ────────────────────────────────
    # Tries multiple font hosts in order and returns the first one that
    # responds with a valid CSS stylesheet. Used by the typography node so
    # arbitrary font names (not just Google Fonts) work without the user
    # having to know which host serves which family.
    #
    # Response shape:
    #   { "ok": true, "url": "...", "source": "google" | "bunny" | "fontsource",
    #     "family": "Inter", "preview": "/* first 200 chars of CSS */" }
    # On no-match:
    #   { "ok": false, "family": "Inter", "providers_tried": ["google", "bunny", "fontsource"] }
    #
    # The font name is used verbatim (after url-encoding) — case + spelling
    # matter. We do NOT search for fuzzy matches; that's the user's job.
    def _resolve_font_get(self, qs):
        name = (qs.get("name") or [""])[0].strip()
        if not name:
            return self._reply(400, {"error": "name required", "hint": "?name=Inter"})
        if len(name) > 128:
            return self._reply(400, {"error": "name too long (max 128)"})
        # Sanitize against header/URL injection — keep letters/digits/spaces/+/-
        if not re.match(r"^[A-Za-z0-9 +\-_]+$", name):
            return self._reply(400, {"error": "invalid characters in name", "name": name})

        family_url = urllib.parse.quote(name).replace("%20", "+")
        # slug = lower-case dash-joined (Fontsource convention)
        slug = re.sub(r"\s+", "-", name.strip().lower())

        candidates = [
            ("google", f"https://fonts.googleapis.com/css2?family={family_url}:wght@400;500;600;700;800&display=swap"),
            ("bunny",  f"https://fonts.bunny.net/css?family={family_url.lower()}:400,500,600,700,800"),
            ("fontsource", f"https://cdn.jsdelivr.net/fontsource/css/{slug}@latest/index.css"),
        ]
        tried = []
        for source, url in candidates:
            tried.append(source)
            try:
                # GET (not HEAD — Google 405s HEAD) with short timeout + tiny
                # body read so we can verify the response is real CSS.
                req = urllib.request.Request(url, headers={
                    # Google Fonts gates the CSS by User-Agent: an Inter-only browser
                    # gets minimal CSS; a Chrome UA gets the variable font. Use Chrome.
                    "User-Agent": "Mozilla/5.0 (compatible; ThPrototypeEditor/1.0; like Chrome/120.0.0.0)",
                    "Accept": "text/css,*/*;q=0.1",
                })
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status != 200:
                        continue
                    head_bytes = resp.read(2048)
                # Heuristic: valid font CSS contains @font-face. Empty / 404-fallback
                # responses don't.
                head_text = head_bytes.decode("utf-8", errors="replace")
                if "@font-face" not in head_text and "src:" not in head_text:
                    continue
                return self._reply(200, {
                    "ok":      True,
                    "url":     url,
                    "source":  source,
                    "family":  name,
                    "preview": head_text[:300],
                })
            except urllib.error.HTTPError:
                # Non-2xx — try next candidate.
                continue
            except (urllib.error.URLError, TimeoutError, OSError):
                # Network unreachable — try next candidate. The dev server is
                # offline-tolerant: if all three fail because of no internet,
                # the user gets a clear "not found" response (with all three
                # listed as tried) and the manual-upload fallback in the UI.
                continue
            except Exception:
                continue
        return self._reply(200, {
            "ok":              False,
            "family":          name,
            "providers_tried": tried,
            "hint":            "Font not found on Google Fonts / Bunny Fonts / Fontsource. Upload a .woff2 / .ttf manually via POST /__upload_font.",
        })

    # ── POST /__upload_font?ds=<id>&name=<family> ────────────────────────
    # Accepts a raw font file (woff2 / woff / ttf / otf), writes it to
    # design-systems/<dsId>/fonts/<slug>.<ext>, and returns the relative URL
    # the editor can <link> via an auto-generated @font-face stylesheet
    # sibling. The fallback when /__resolve_font returns ok=false.
    def _upload_font_post(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        ds_id = (qs.get("ds") or [""])[0].strip().lower() or "main"
        name  = (qs.get("name") or [""])[0].strip()
        if not name:
            return self._reply(400, {"error": "name required (?name=<family>)"})
        if not SLUG_OK.match(ds_id):
            return self._reply(400, {"error": "invalid ds id", "id": ds_id})
        if not re.match(r"^[A-Za-z0-9 +\-_]+$", name):
            return self._reply(400, {"error": "invalid characters in font name"})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 5 * 1024 * 1024:
            return self._reply(413, {"error": "font file required; max 5MB", "bytes": length})
        # Content-Type header tells us the extension. Accept the common ones;
        # fall back to ".woff2" since that's by far the most common modern
        # font format users will paste in.
        ctype = (self.headers.get("Content-Type") or "").lower()
        ext = {
            "font/woff2":      "woff2",
            "application/font-woff2": "woff2",
            "font/woff":       "woff",
            "application/font-woff": "woff",
            "font/ttf":        "ttf",
            "application/x-font-ttf": "ttf",
            "font/otf":        "otf",
            "application/x-font-otf": "otf",
            "application/octet-stream": "woff2",
        }.get(ctype, "woff2")
        body = self.rfile.read(length)
        slug = re.sub(r"\s+", "-", name.strip().lower())
        # Write under design-systems/<dsId>/fonts/. Auto-create dirs.
        fonts_dir = os.path.join(project_root, "design-systems", ds_id, "fonts")
        try:
            os.makedirs(fonts_dir, exist_ok=True)
        except Exception as e:
            return self._reply(500, {"error": f"could not create fonts dir: {e}"})
        font_path = os.path.join(fonts_dir, slug + "." + ext)
        try:
            with open(font_path, "wb") as f:
                f.write(body)
        except Exception as e:
            return self._reply(500, {"error": f"could not write font file: {e}"})
        # Sibling CSS — append to design-systems/<dsId>/fonts/_fontface.css.
        # This is what the editor <link>s to register the uploaded face. We
        # rebuild it from scratch each call so deleted fonts vanish.
        css_path = os.path.join(fonts_dir, "_fontface.css")
        files = sorted(f for f in os.listdir(fonts_dir)
                       if f.lower().endswith((".woff2", ".woff", ".ttf", ".otf")))
        css_chunks = ["/* Auto-generated by /__upload_font. Edit at your own risk. */\n"]
        for f in files:
            face_name = f.rsplit(".", 1)[0]
            face_fmt  = {"woff2": "woff2", "woff": "woff", "ttf": "truetype", "otf": "opentype"}.get(f.rsplit(".", 1)[1].lower(), "woff2")
            # Use display family name (de-slug) for font-family
            display = " ".join(p.capitalize() for p in face_name.split("-"))
            css_chunks.append(
                f"@font-face {{\n"
                f"  font-family: '{display}';\n"
                f"  src: url('./{f}') format('{face_fmt}');\n"
                f"  font-weight: 100 900;\n"
                f"  font-style: normal;\n"
                f"  font-display: swap;\n"
                f"}}\n"
            )
        try:
            with open(css_path, "w", encoding="utf-8") as f:
                f.write("\n".join(css_chunks))
        except Exception as e:
            return self._reply(500, {"error": f"could not write _fontface.css: {e}"})
        css_url = "/design-systems/" + ds_id + "/fonts/_fontface.css"
        return self._reply(200, {
            "ok":     True,
            "family": name,
            "fontPath": os.path.relpath(font_path, project_root),
            "cssUrl":  css_url,
            "source":  "uploaded",
        })

    # ── Phase 4a — BYOK media config + asset generation ──────────────────
    # GET  /__media_config            → masked config status (has_key/last_test_*)
    # POST /__media_config            → set/clear keys per provider
    # POST /__media_config/test?provider=openai
    # POST /__asset_generate?project= → run a generator, write bytes under
    #                                   source/<branch>/<output>
    def _media_config_get(self):
        cfg = _media_config_load()
        masked = {}
        # v3.4.7 — Also mark providers whose key is in the env (TH_*) — the
        # resolver checks env first, so a provider with an env key but
        # nothing in media-config.json is still "available".
        for provider in _PROVIDER_ENV_KEYS:
            settings = cfg.get(provider, {}) if isinstance(cfg.get(provider), dict) else {}
            key = settings.get("api_key") or os.environ.get(_PROVIDER_ENV_KEYS.get(provider) or "", "")
            masked[provider] = {
                "has_key": bool(key),
                "saved":   bool(settings.get("api_key")),
                "from_env": bool(not settings.get("api_key") and key),
                "last_test_ok": bool(settings.get("last_test_ok")),
                "last_test_at": settings.get("last_test_at"),
            }
        # v3.4.7 — Surface CLI availability so the editor's "Auto" resolver
        # can decide between API and CLI fallback without making the user
        # guess. detect_agent_bin returns None when not on PATH.
        # v3.5 — Codex CLI is the OpenAI counterpart: when present, openai
        # provider falls back to Codex (not Claude) so the picked provider
        # actually answers.
        claude_avail = detect_agent_bin("claude") is not None
        codex_avail  = detect_agent_bin("codex")  is not None
        return self._reply(200, {
            "providers": masked,
            "claude_cli_available": claude_avail,
            "codex_cli_available":  codex_avail,
        })

    def _media_config_set(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0: return self._reply(400, {"error": "empty body"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON", "detail": str(e)})
        cfg = _media_config_load()
        for provider, settings in body.items():
            if not isinstance(settings, dict): continue
            if provider not in cfg or not isinstance(cfg.get(provider), dict):
                cfg[provider] = {}
            if "api_key" in settings:
                k = settings["api_key"]
                if isinstance(k, str):
                    cfg[provider]["api_key"] = k.strip() or None
                    if not cfg[provider]["api_key"]:
                        # Empty string clears the key.
                        cfg[provider].pop("api_key", None)
                        cfg[provider].pop("last_test_ok", None)
                        cfg[provider].pop("last_test_at", None)
        _media_config_save(cfg)
        return self._reply(200, {"ok": True})

    def _media_config_test(self, qs):
        provider = (_qs_get(qs, "provider") or "openai").strip()
        if provider not in _PROVIDER_ENV_KEYS:
            return self._reply(400, {"error": f"unknown provider: {provider}"})
        api_key = _resolve_provider_key(provider)
        if not api_key:
            return self._reply(502, {"error": "no api key configured"})
        ok = False
        detail = None
        try:
            if provider == "openai":
                req = urllib.request.Request(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read())
                ok = isinstance(data, dict) and "data" in data
            elif provider == "anthropic":
                # Cheapest valid call: 1-token completion against Haiku.
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    method="POST",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps({
                        "model": "claude-haiku-4-5",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    }).encode("utf-8"),
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read())
                ok = isinstance(data, dict) and data.get("type") == "message"
            elif provider == "fal":
                # fal.ai has no free auth-check endpoint. Hit a tiny model
                # info GET with the key — succeeds (200/404 model-not-found)
                # if the key parses, 401s if not. We treat anything other
                # than 401 as "key shape OK".
                try:
                    req = urllib.request.Request(
                        "https://fal.run/health",
                        headers={"Authorization": f"Key {api_key}"},
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        resp.read()
                    ok = True
                except urllib.error.HTTPError as e:
                    ok = e.code != 401
                    if not ok: detail = {"status": e.code, "hint": "fal rejected the key"}
            else:
                # No specific test for other providers yet — saving the key counts.
                ok = True
        except urllib.error.HTTPError as e:
            try: detail = json.loads(e.read().decode("utf-8", "replace"))
            except Exception: detail = {"status": e.code}
        except Exception as e:
            detail = {"error": f"{type(e).__name__}: {e}"}
        cfg = _media_config_load()
        if provider not in cfg or not isinstance(cfg[provider], dict): cfg[provider] = {}
        cfg[provider]["last_test_ok"] = bool(ok)
        cfg[provider]["last_test_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _media_config_save(cfg)
        if not ok:
            return self._reply(502, {"ok": False, "detail": detail})
        return self._reply(200, {"ok": True})

    def _asset_generate(self, qs):
        """Phase 4b dispatcher. Body shape:
           {
             skill:    "generate-image" | "rembg" | "upscale",
             provider: "openai" | "fal",
             model:    "<provider-specific model id>",
             prompt?:   "..."                       # for generate-* skills
             input_path?: "source/<branch>/<file>"  # for transform skills
             output:   "source/<branch>/<file>",
             aspect?:  "1:1" | "3:2" | "16:9" | "2:3" | "9:16",
             options?: { ... }
           }"""
        try:
            # require_explicit: drawer subagents have historically forgotten
            # `?project=<id>` and the silent alphabetical-first fallback wrote
            # 12 images into the wrong project's source/ tree. Force the
            # caller to be explicit when multiple projects exist.
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})

        skill    = (body.get("skill") or "generate-image").strip()
        provider = (body.get("provider") or "").strip()
        model    = (body.get("model") or "").strip()
        output   = (body.get("output") or "").strip()
        aspect   = (body.get("aspect") or "1:1").strip()
        options  = body.get("options") or {}
        # v3.1 — soft gate: every image-gen call SHOULD carry a `medium`
        # classified by the visual-orchestrator subagent (raster-foreground,
        # raster-photo, vector-icon, vector-mark, shader, particle-2d,
        # particle-gl, lottie, 3d, video). Without one, we log a warning
        # so we can audit which call sites bypassed the orchestrator. Don't
        # reject — that would break inline agent-driven scaffolds. Tracked
        # downstream by routing to the project's .asset-gen-audit.jsonl.
        medium = (body.get("medium") or "").strip() or "unspecified"
        _ALLOWED_MEDIA = {
            "raster-foreground", "raster-photo", "vector-icon", "vector-mark",
            "shader", "particle-2d", "particle-gl", "lottie", "3d", "video",
            "unspecified",
        }
        if medium not in _ALLOWED_MEDIA:
            medium = "unspecified"
        if medium == "unspecified":
            print(f"[asset-gen audit] {output!r}: medium NOT classified by visual-orchestrator. "
                  f"Caller should dispatch visual-orchestrator () first.",
                  flush=True)
        # Append an audit entry so we can grep call sites later.
        # v3.1 — bounded rotation: when the file exceeds 1 MB, rename it to
        # .asset-gen-audit.jsonl.prev and start a fresh one. Two-file
        # ring buffer caps disk usage at ~2 MB regardless of how long the
        # project runs.
        try:
            audit_path = os.path.join(project_root, ".asset-gen-audit.jsonl")
            if os.path.isfile(audit_path) and os.path.getsize(audit_path) > 1_000_000:
                try: os.replace(audit_path, audit_path + ".prev")
                except OSError: pass
            with open(audit_path, "a", encoding="utf-8") as af:
                af.write(json.dumps({
                    "ts": time.time(), "output": output, "skill": skill,
                    "provider": provider, "model": model, "medium": medium,
                    "requestId": getattr(self, "request_id", None),
                }) + "\n")
        except Exception:
            pass

        if not output:
            return self._reply(400, {"error": "output path required"})
        if ".." in output.split("/") or output.startswith("/"):
            return self._reply(400, {"error": "output path must be relative and stay under source/"})
        if not output.startswith("source/"):
            return self._reply(400, {"error": "output path must be under source/"})

        # Pick the renderer family — generation vs transform.
        gen_key = (skill, provider)
        is_generate  = gen_key in _GENERATE_DISPATCH
        is_transform = gen_key in _TRANSFORM_DISPATCH
        if not is_generate and not is_transform:
            return self._reply(400, {
                "error": f"no renderer for skill={skill!r} provider={provider!r}",
                "known_generate":  list(_GENERATE_DISPATCH.keys()),
                "known_transform": list(_TRANSFORM_DISPATCH.keys()),
            })

        # provider="local" runs in-process via a Python library (e.g., rembg).
        # No credentials required — skip the key lookup entirely.
        api_key = None
        # v3.5 — Codex CLI fallback for openai image generation. Codex's
        # agent loop has a built-in image-gen tool that calls OpenAI's
        # image endpoints using the user's `codex login` OAuth — no API
        # key required. Only applies to image generation (not video / svg /
        # transforms), because that's the only path where Codex has a
        # native tool we can call.
        use_codex_image_fallback = False
        if provider != "local":
            api_key = _resolve_provider_key(provider)
            if not api_key:
                if (provider == "openai"
                    and skill == "generate-image"
                    and detect_agent_bin("codex") is not None):
                    use_codex_image_fallback = True
                else:
                    return self._reply(502, {
                        "error": f"no {provider} API key configured — open Settings (⚙ in the workflow toolbar) and paste your key",
                    })

        # Validate inputs per family.
        input_abs = None
        input_data_uri = None
        if is_generate:
            prompt = (body.get("prompt") or "").strip()
            if not prompt:
                return self._reply(400, {"error": "prompt required for generate skills"})
            # Phase 8 — generate-image with an input image. Currently only
            # OpenAI's gpt-image-1 family supports image-to-image; everyone
            # else gets a 400 telling them to pick a different model. This
            # used to SILENTLY DROP the input image — Blend / Remix would
            # call generate-image with input_path set and the daemon ignored
            # it, producing a text-only result.
            raw_uri = body.get("input_data_uri")
            in_path = (body.get("input_path") or "").strip()
            if raw_uri or in_path:
                if provider != "openai" or not (model or "").startswith("gpt-image"):
                    return self._reply(400, {
                        "error":
                            f"This skill ({skill}, {model}) doesn't accept an input image. " +
                            "Use OpenAI gpt-image-1 / gpt-image-1-mini for image-to-image, " +
                            "or wire to a transform skill (rembg / upscale / etc.).",
                    })
                if isinstance(raw_uri, str) and raw_uri.startswith("data:"):
                    input_data_uri = raw_uri
                elif in_path:
                    if ".." in in_path.split("/") or in_path.startswith("/"):
                        return self._reply(400, {"error": "input_path must be relative and stay under source/"})
                    try:
                        input_abs = _safe_join(project_root, in_path)
                    except Exception as e:
                        return self._reply(400, {"error": f"invalid input_path: {e}"})
                    if not os.path.isfile(input_abs):
                        return self._reply(404, {"error": f"input file not found: {in_path}"})
        else:
            # Transform skills accept either a file path OR a pre-built data
            # URI (e.g., inline-SVG sources don't have a file on disk).
            raw_uri = body.get("input_data_uri")
            if isinstance(raw_uri, str) and raw_uri.startswith("data:"):
                input_data_uri = raw_uri
            else:
                input_path = (body.get("input_path") or "").strip()
                if not input_path:
                    return self._reply(400, {"error": "input_path or input_data_uri required for transform skills"})
                if ".." in input_path.split("/") or input_path.startswith("/"):
                    return self._reply(400, {"error": "input_path must be relative and stay under source/"})
                try:
                    input_abs = _safe_join(project_root, input_path)
                except Exception as e:
                    return self._reply(400, {"error": f"invalid input_path: {e}"})
                if not os.path.isfile(input_abs):
                    return self._reply(404, {"error": f"input file not found: {input_path}"})

        # Dispatch.
        try:
            if is_generate:
                # Image-to-image branch: generate-image with an input image
                # promotes to the edit endpoint so the image actually
                # influences the output. (Validated above.)
                has_image_input = bool(input_abs or input_data_uri)
                if has_image_input and provider == "openai":
                    if use_codex_image_fallback:
                        return self._reply(400, {
                            "error":
                                "Image-to-image (input image attached) requires the OpenAI HTTP /v1/images/edits endpoint. "
                                "Codex CLI doesn't expose an image-edit tool — please paste an OpenAI API key in Settings, "
                                "or use a text-to-image variant (drop the input image)."
                        })
                    if input_abs:
                        with open(input_abs, "rb") as f:
                            img_bytes = f.read()
                        img_mime = _guess_image_mime(input_abs)
                    else:
                        # Strip the data URI header and decode the base64 payload.
                        m = re.match(r"^data:([^;]+);base64,(.+)$", input_data_uri or "", re.S)
                        if not m:
                            return self._reply(400, {"error": "input_data_uri must be a base64 data URI"})
                        img_mime  = m.group(1)
                        img_bytes = base64.b64decode(m.group(2))
                    bytes_ = _openai_edit_image(api_key, prompt, model, img_bytes, img_mime, aspect, options)
                elif provider == "openai":
                    if use_codex_image_fallback:
                        # v3.5 — no API key + codex on PATH: run the agent.
                        # Timeout is generous (5 min) — codex's agent loop
                        # can take a while for image gen.
                        bytes_ = _codex_cli_generate_image(
                            prompt, model, aspect, project_root, timeout=300,
                        )
                    else:
                        bytes_ = _openai_generate_image(api_key, prompt, model, aspect, options)
                elif provider == "fal" and skill == "video-gen":
                    # v3.4.1 — Real video. Dispatches to fal's text-to-video
                    # endpoint and downloads the mp4 bytes. Unlike image
                    # generation, this can take 30s–5min depending on
                    # the model, so we extend timeout to 300s.
                    bytes_ = _fal_generate_video(api_key, prompt, model, aspect, options)
                elif provider == "fal":
                    bytes_ = _fal_generate_image(api_key, prompt, model, aspect, options)
                elif provider == "quiver" and skill == "svg-gen":
                    bytes_ = _quiver_generate_svg(api_key, prompt, model, options)
                else:
                    return self._reply(400, {"error": f"unhandled provider: {provider}"})
            else:  # transform
                if provider == "fal":
                    bytes_ = _fal_transform_image(api_key, model, input_abs, options, input_data_uri=input_data_uri)
                elif provider == "local" and skill == "rembg":
                    if input_data_uri:
                        return self._reply(400, {"error":
                            "local rembg can't read SVG / data URIs — needs raster bytes. "
                            "Use a file-backed asset or a fal-based rembg in a later phase."})
                    bytes_ = _local_rembg(input_abs, model, options)
                else:
                    return self._reply(400, {"error": f"unhandled transform provider: {provider}"})
        except urllib.error.HTTPError as e:
            try: detail = json.loads(e.read().decode("utf-8", "replace"))
            except Exception: detail = {"status": e.code}
            return self._reply(502, {"error": f"{provider} API error", "detail": detail})
        except Exception as e:
            return self._reply(500, {"error": f"{type(e).__name__}: {e}"})

        try:
            out_path = _safe_join(project_root, output)
        except Exception as e:
            return self._reply(400, {"error": f"invalid output path: {e}"})
        out_dir = os.path.dirname(out_path)
        # Bracket scope: the branch's source/ folder. This catches both the
        # generated output file AND the optional inline-SVG replacement that
        # rewrites HTML files under the same branch. Extract the branch from
        # the output path; if it doesn't match the canonical shape, fall
        # back to the whole source/ tree.
        scope_dir = "source"
        if output.startswith("source/"):
            parts = output.split("/", 2)
            if len(parts) >= 2:
                scope_dir = f"source/{parts[1]}"
        replaced_files = None
        replace_error = None
        with _history_scope_bracket(project_root, [scope_dir],
                                     kind="asset-gen",
                                     label=f"Generate {skill}: {os.path.basename(output)}",
                                     source="asset",
                                     extra={"skill": skill, "provider": provider, "model": model}):
            try:
                os.makedirs(out_dir, exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(bytes_)
            except Exception as e:
                return self._reply(500, {"error": f"could not write {output}: {e}"})

            # Optional: replace an inline SVG in source with an <img> reference
            # to the freshly-written file. Used when a skill outputs to an
            # inline-svg asset card — the prototype's source HTML/JSX is
            # edited so the regenerated visual actually renders in the iframe.
            ir = body.get("inline_replace")
            if isinstance(ir, dict) and isinstance(ir.get("original_svg"), str) and isinstance(ir.get("branch"), str):
                try:
                    # Build the <img> tag. Relative path is from the prototype's
                    # entry HTML's directory. We assume entry is at source/<branch>/
                    # so output "source/<branch>/images/foo.png" becomes "images/foo.png".
                    rel = output
                    prefix = f"source/{ir['branch']}/"
                    if rel.startswith(prefix): rel = rel[len(prefix):]
                    bbox = ir.get("bbox") or {}
                    w_attr = f' width="{int(bbox["w"])}"' if isinstance(bbox.get("w"), (int, float)) else ""
                    h_attr = f' height="{int(bbox["h"])}"' if isinstance(bbox.get("h"), (int, float)) else ""
                    new_img = f'<img src="{rel}"{w_attr}{h_attr} alt="regenerated"/>'
                    replaced_files = _replace_inline_svg_in_sources(
                        project_root, ir["branch"], ir["original_svg"], new_img,
                    )
                except Exception as e:
                    replace_error = str(e)

        # v3.0 — asset-versioning snapshot. After a successful image / SVG
        # generation, find the matching workflow asset node by output path
        # and snapshot it so the user can revert. Best-effort: a snapshot
        # failure must not fail the generation.
        snapshot_info = None
        try:
            wf_path = os.path.join(project_root, "workflow", "workflow.json")
            if os.path.isfile(wf_path):
                project_id = os.path.basename(project_root.rstrip("/"))
                with _workflow_lock_timeout(project_id, timeout_sec=2.0):
                    with open(wf_path, "r", encoding="utf-8") as f:
                        wf = json.load(f)
                    from kinds.versioning import snapshot_asset_by_output_path
                    snapshot_info = snapshot_asset_by_output_path(
                        project_root, wf, output,
                        run_id=getattr(self, "request_id", None),
                    )
                    if snapshot_info:
                        with open(wf_path, "w", encoding="utf-8") as f:
                            json.dump(wf, f, indent=2)
                if snapshot_info:
                    _broadcast_workflow_change(project_id)
        except Exception as _vsn_err:
            print(f"[asset-versioning] /__asset_generate snapshot error: {_vsn_err}", flush=True)

        return self._reply(200, {
            "ok": True, "path": output, "bytes": len(bytes_),
            "skill": skill, "provider": provider, "model": model,
            "medium": medium,
            "snapshot": snapshot_info,
            "inline_replace": (
                {"ok": True, "files": replaced_files} if replaced_files
                else ({"ok": False, "error": replace_error} if replace_error else None)
            ),
        })

    def _dispatch_planner(self, qs):
        """POST /__dispatch_planner?project=<id>
        Body: { type: "<subagent>", brief: "..." }

        Streams the planner run as Server-Sent Events. The HTTP response
        opens immediately (so callers like codex shelling out via curl
        don't block on a long synchronous body), heartbeats keep the
        connection alive across multi-minute planner runs, normalised
        agent events flow as they're produced, and a final `planner-done`
        event carries the synthesized output before the stream closes.

        The run is spawned via subprocess.Popen + the existing RunState
        machinery, so it shows up in /__runs, can be stopped via
        /__run/<id>/stop, and shares the same drain/normalise pipeline
        chat runs use. Any subagent in `.claude/agents/` is a valid type;
        the endpoint is reentrant so an orchestrator running on one
        runtime can dispatch nested subagents that the daemon routes to
        another runtime, without any caller-side branching.

        Runtime selection: Claude (preferred — native Task tool for
        nested dispatch) → Codex (via translation note that substitutes
        Task with curl POST back to this endpoint) → 502 if neither.

        SSE event types emitted:
          • planner-dispatched — first event; { runId, type, runtime }
          • agent — normalised agent event (text_delta, tool_use, …)
          • status / stderr / user_message — passed through verbatim
          • planner-done — final; { output, exitCode, error? } before close
        """
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        project_id = os.path.basename(project_root.rstrip("/"))
        body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        planner_type = (body.get("type") or "").strip()
        brief = (body.get("brief") or "").strip()
        if not planner_type:
            return self._reply(400, {"error": "type required"})
        if not brief:
            return self._reply(400, {"error": "brief required"})
        planner_path = os.path.join(INSTALL_ROOT, ".claude", "agents", f"{planner_type}.md")
        if not os.path.isfile(planner_path):
            return self._reply(404, {
                "error": f"unknown planner type: {planner_type!r}",
                "hint": f"expected {planner_path}",
            })
        try:
            with open(planner_path, "r", encoding="utf-8") as f:
                planner_md = f.read()
        except Exception as e:
            return self._reply(500, {"error": f"could not read planner: {e}"})
        planner_body = re.sub(r"^---\n.*?\n---\n", "", planner_md, count=1, flags=re.S).strip()
        # Pick runtime + build spawn shape.
        claude_bin = detect_agent_bin("claude")
        codex_bin  = detect_agent_bin("codex")
        if claude_bin:
            agent_id, bin_path = "claude", claude_bin
            spawn_args = [
                "--print",
                "--output-format", "stream-json",
                "--input-format", "stream-json",
                "--verbose",
                "--disallowedTools", "AskUserQuestion",
                "--no-session-persistence",
                "--disable-slash-commands",
                "--allow-dangerously-skip-permissions",
                "--dangerously-skip-permissions",
                "--add-dir", project_root,
                "--append-system-prompt", planner_body,
            ]
            stdin_pipe = subprocess.PIPE
            prompt_stdin = _claude_user_frame(brief)
            prompt_argv = None
        elif codex_bin:
            agent_id, bin_path = "codex", codex_bin
            translation_note = (
                "===== RUNTIME NOTE =====\n"
                "The planner spec above was written for Claude Code's `Task` "
                "tool. You are running on the Codex CLI runtime. Wherever the "
                "spec instructs you to invoke `Task(subagent_type: \"<type>\", "
                "prompt: \"<brief>\")`, instead run this shell command:\n\n"
                "  curl -s -X POST "
                f"'http://127.0.0.1:{PORT}/__dispatch_planner?project={project_id}' "
                "-H 'content-type: application/json' "
                "-d '{\"type\": \"<type>\", \"brief\": \"<brief>\"}'\n\n"
                "The daemon routes the nested dispatch to whichever LLM is "
                "available and streams its events back as SSE. Parse the "
                "final `planner-done` event's `output` field and treat it the "
                "way the spec would have treated a Task tool return value.\n"
                "===== END RUNTIME NOTE =====\n"
            )
            full_prompt = (
                "===== PLANNER SPEC =====\n"
                + planner_body
                + "\n===== END PLANNER SPEC =====\n\n"
                + translation_note
                + "\n===== YOUR BRIEF =====\n"
                + brief
            )
            # danger-full-access matches AGENT_DEFS["codex"]["args"] —
            # required so the planner can curl back to /__dispatch_planner
            # for nested subagent dispatch (workspace-write blocks network).
            spawn_args = ["exec", "--sandbox", "danger-full-access"]
            stdin_pipe = None
            prompt_stdin = None
            prompt_argv = full_prompt
        else:
            return self._reply(502, {
                "error": "no LLM runtime available — install Claude Code or Codex CLI",
                "hint": "npm install -g @anthropic-ai/claude-code  OR  npm install -g @openai/codex",
            })
        # Spawn the planner subprocess.
        run_id = uuid.uuid4().hex[:16]
        env = _build_child_env(agent_id, run_id,
                               project_root=project_root, project_id=project_id)
        argv = [bin_path, *spawn_args]
        if prompt_argv is not None:
            argv.append(prompt_argv)
        try:
            proc = subprocess.Popen(
                argv,
                cwd=project_root,
                stdin=stdin_pipe,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,
            )
        except Exception as e:
            return self._reply(500, {"error": f"planner spawn failed: {type(e).__name__}: {e}"})
        state = RunState(run_id, proc, agent_id, branch="planner",
                         kind=f"planner:{planner_type}",
                         title=f"Planner · {planner_type}",
                         project_id=project_id, project_root=project_root)
        state.bin_path = bin_path
        state.permission_mode = "bypassPermissions"
        with RUNS_LOCK:
            RUNS[run_id] = state
        state.append("status", {"label": "planner-dispatched",
                                "type": planner_type, "runtime": agent_id})
        # Feed the prompt if the runtime takes stdin (Claude stream-json).
        if prompt_stdin is not None:
            try:
                proc.stdin.write(prompt_stdin)
                proc.stdin.flush()
            except Exception as e:
                state.append("error", {"message": f"failed to write prompt to stdin: {e}"})
        # Start the drains — same machinery the chat path uses, so codex's
        # stderr protocol gets parsed by _CodexStderrParser and Claude's
        # stream-json frames get normalised by _normalize_frame.
        threading.Thread(target=_drain_stdout, args=(state,), daemon=True,
                         name=f"planner-{run_id}-stdout").start()
        threading.Thread(target=_drain_stderr, args=(state,), daemon=True,
                         name=f"planner-{run_id}-stderr").start()
        # SSE response setup.
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        def _write_sse(event_name: str, data) -> bool:
            try:
                payload = json.dumps(data, separators=(",", ":"))
                frame = f"event: {event_name}\ndata: {payload}\n\n".encode("utf-8")
                self.wfile.write(frame)
                self.wfile.flush()
                return True
            except Exception:
                return False
        # Initial metadata event so the caller can immediately log the runId.
        if not _write_sse("planner-dispatched", {
            "runId": run_id, "type": planner_type, "runtime": agent_id,
        }):
            return
        # Subscribe to the run's event log and stream as new events land.
        waker = threading.Event()
        with state.lock:
            state.waiters.add(waker)
        last_seen = -1
        try:
            while True:
                with state.lock:
                    pending = state.events[last_seen + 1:]
                    is_done = state.done
                for ev in pending:
                    if not _write_sse(ev["type"], ev["data"]):
                        return  # client gone
                    last_seen = ev["seq"]
                if is_done:
                    break
                fired = waker.wait(timeout=25)
                waker.clear()
                if not fired:
                    # Heartbeat — keeps the connection alive across long
                    # planner runs without producing visible output.
                    try:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                    except Exception:
                        return
            # Synthesize the final output: concatenate every text_delta from
            # the agent event stream. Tool calls / results are visible in
            # the events themselves; the `output` field is the planner's
            # final narrative reply.
            chunks = []
            with state.lock:
                events_snapshot = list(state.events)
            for ev in events_snapshot:
                if ev["type"] != "agent":
                    continue
                d = ev.get("data") or {}
                if d.get("type") == "text_delta":
                    chunks.append(d.get("delta") or "")
            output = "".join(chunks).strip()
            _write_sse("planner-done", {
                "runId": run_id,
                "type": planner_type,
                "runtime": agent_id,
                "exitCode": state.exit_code,
                "output": output,
                "error": None if state.exit_code in (None, 0) else f"exit {state.exit_code}",
            })
        finally:
            with state.lock:
                state.waiters.discard(waker)

    def _llm_run(self, qs):
        """Phase 4c — text-output skills. Body:
           {
             skill:    "llm" | "describe",
             provider: "openai",
             model:    "gpt-4o-mini" | ...,
             prompt?:   "..."                       # for llm
             input_path?: "source/<branch>/<image>" # for describe
             options?: { temperature, max_tokens, ... }
           }
           Returns: { ok, text, skill, provider, model }"""
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})

        skill    = (body.get("skill") or "llm").strip()
        provider = (body.get("provider") or "openai").strip()
        model    = (body.get("model") or "gpt-4o-mini").strip()
        options  = body.get("options") or {}

        if (skill, provider) not in _LLM_DISPATCH:
            return self._reply(400, {
                "error": f"no LLM renderer for skill={skill!r} provider={provider!r}",
                "known": list(_LLM_DISPATCH.keys()),
            })

        api_key = _resolve_provider_key(provider)
        # v3.4.6 — CLI fallback policy:
        #   • CLI is ALWAYS preferred when authenticated, regardless of which
        #     provider the user picked. The user's mental model is "I have
        #     Claude Code installed; it should just work" — making them
        #     paste an API key for a model they're not even using is
        #     friction. The CLI uses their existing subscription (no per-
        #     token cost), so it's also the cheaper default.
        #   • For provider=anthropic: trivial — Claude CLI IS the anthropic
        #     model, just routed through Claude Code's auth instead of the
        #     API directly.
        # v3.5 — For provider=openai with no API key:
        #   • Prefer Codex (OpenAI's CLI) when installed — same provider,
        #     just routed through `codex login`. The picked model passes
        #     through to `codex exec --model`.
        #   • Fall through to Claude CLI as a last-resort substitute when
        #     Codex is not on PATH. The response annotates provider=
        #     "claude-cli" so the UI can surface the substitution.
        # This block restricts to skill="llm" — "describe" always carries
        # an image payload that the one-shot CLI helpers don't accept yet.
        claude_avail = detect_agent_bin("claude") is not None
        codex_avail  = detect_agent_bin("codex")  is not None
        cli_available = claude_avail or codex_avail
        if cli_available and not api_key and provider in ("anthropic", "openai") and skill == "llm":
            try:
                msgs_in = body.get("messages")
                if isinstance(msgs_in, list) and msgs_in:
                    cli_msgs = []
                    for m in msgs_in:
                        if not isinstance(m, dict): continue
                        role = m.get("role")
                        content = m.get("content")
                        if role not in ("system", "user", "assistant"): continue
                        if not isinstance(content, str) or not content.strip(): continue
                        cli_msgs.append({"role": role, "content": content})
                    if not cli_msgs:
                        return self._reply(400, {"error": "messages array had no valid entries"})
                else:
                    p = (body.get("prompt") or "").strip()
                    if not p:
                        return self._reply(400, {"error": "prompt or messages required for llm skill"})
                    cli_msgs = [{"role": "user", "content": p}]
                # Pick which CLI runs the call:
                #   • openai → codex CLI when present, else claude as substitute
                #   • anthropic → claude CLI when present, else codex as substitute
                use_codex = (
                    (provider == "openai" and codex_avail)
                    or (provider == "anthropic" and not claude_avail and codex_avail)
                )
                if use_codex:
                    # Sentinel "" / "cli-default" / "codex-default" → let codex
                    # use its built-in default model (don't pass --model).
                    m_lower = (model or "").lower().strip()
                    cli_default_sentinels = ("", "cli-default", "codex-default", "default")
                    effective_model = None if m_lower in cli_default_sentinels else model
                    text = _codex_cli_complete(cli_msgs, model=effective_model, timeout=600)
                    response_provider = "codex-cli"
                    fallback_reason = (
                        None if provider == "openai" else
                        "anthropic CLI not installed — answered by Codex CLI as fallback"
                    )
                else:
                    m_lower = (model or "").lower().strip()
                    cli_default_sentinels = ("", "cli-default", "claude-default", "default")
                    if m_lower in cli_default_sentinels:
                        effective_model = None    # let Claude CLI pick its default
                    elif "claude" in m_lower:
                        effective_model = model
                    else:
                        effective_model = "sonnet"
                    text = _claude_cli_complete(cli_msgs, model=effective_model, timeout=600)
                    response_provider = "claude-cli" if provider == "openai" else "anthropic-cli"
                    fallback_reason = (
                        "openai API key not configured AND codex CLI not installed — answered by Claude CLI as fallback"
                        if provider == "openai" else None
                    )
                return self._reply(200, {
                    "ok": True, "text": text, "skill": skill,
                    "provider": response_provider, "model": effective_model or "default",
                    "fallback_reason": fallback_reason,
                })
            except FileNotFoundError as e:
                want_cli = "codex" if provider == "openai" else "claude"
                return self._reply(502, {"error": f"no {provider} API key AND {want_cli} CLI not on PATH ({e}). Open Settings (⚙ in the workflow toolbar) to paste an API key, or install the {want_cli} CLI."})
            except subprocess.TimeoutExpired:
                return self._reply(504, {
                    "error":
                        "Claude CLI fallback timed out after 10 minutes. "
                        "This usually means the prompt is too large or the response is too long for one-shot CLI mode. "
                        "Workarounds: (1) paste an Anthropic API key into Settings (⚙ in the workflow toolbar) — direct HTTP is 4-5× faster than the CLI; "
                        "(2) shorten the prompt; (3) lower the requested max_tokens (currently 8000) by editing the iterator's call site.",
                })
            except Exception as e:
                # Truncate noisy reprs (TimeoutExpired/CalledProcessError dump the full argv).
                msg = str(e)
                return self._reply(502, {"error": f"CLI fallback failed: {msg[:300]}{'…' if len(msg) > 300 else ''}"})
        if not api_key:
            return self._reply(502, {
                "error": f"no {provider} API key configured — open Settings (⚙ in the workflow toolbar) and paste your key",
            })

        # v3.5 — Sentinel models pick the provider's API default when there's
        # an API key. Without this, picking "Codex CLI default" + having an
        # OpenAI key would forward "codex-default" to the API and fail.
        _CLI_DEFAULT_MODELS = {
            ("openai", "codex-default"):  "gpt-5",
            ("openai", "cli-default"):    "gpt-5",
            ("openai", "default"):        "gpt-5",
            ("anthropic", "claude-default"): "claude-opus-4-8",
            ("anthropic", "cli-default"):    "claude-opus-4-8",
            ("anthropic", "default"):        "claude-opus-4-8",
        }
        _remap = _CLI_DEFAULT_MODELS.get((provider, (model or "").lower().strip()))
        if _remap:
            model = _remap

        # Phase 4d — agent mode is enabled when any of these are set. When on,
        # the LLM gets tool-use access to read_root and writes are applied.
        read_root  = (body.get("read_root")  or "").strip().lstrip("/")
        write_root = (body.get("write_root") or "").strip().lstrip("/")
        file_out_path = (body.get("file_out_path") or "").strip().lstrip("/")
        agent_mode = bool(read_root or write_root or file_out_path)

        if skill == "llm":
            # Two body shapes accepted: a single `prompt` (one-shot) or a
            # full `messages` array (multi-turn agent chat). The array form
            # is used by the agent-node chat dialog.
            msgs_in = body.get("messages")
            if isinstance(msgs_in, list) and msgs_in:
                # Sanitize: only role + content strings, allowed roles.
                messages = []
                for m in msgs_in:
                    if not isinstance(m, dict): continue
                    role = m.get("role")
                    content = m.get("content")
                    if role not in ("system", "user", "assistant"): continue
                    if not isinstance(content, str) or not content.strip(): continue
                    messages.append({"role": role, "content": content})
                if not messages:
                    return self._reply(400, {"error": "messages array had no valid entries"})
            else:
                prompt = (body.get("prompt") or "").strip()
                if not prompt:
                    return self._reply(400, {"error": "prompt or messages required for llm skill"})
                messages = [{"role": "user", "content": prompt}]
        elif skill == "describe":
            prompt = (body.get("prompt") or "Describe this image in vivid detail.").strip()
            # Accept either a file path or a pre-built data URI (e.g., inline SVG).
            raw_uri = body.get("input_data_uri")
            if isinstance(raw_uri, str) and raw_uri.startswith("data:"):
                data_uri = raw_uri
            else:
                input_path = (body.get("input_path") or "").strip()
                if not input_path:
                    return self._reply(400, {"error": "input_path or input_data_uri required for describe skill"})
                if ".." in input_path.split("/") or input_path.startswith("/"):
                    return self._reply(400, {"error": "input_path must be relative"})
                try:
                    input_abs = _safe_join(project_root, input_path)
                except Exception as e:
                    return self._reply(400, {"error": f"invalid input_path: {e}"})
                if not os.path.isfile(input_abs):
                    return self._reply(404, {"error": f"input image not found: {input_path}"})
                data_uri = _file_to_data_uri(input_abs)
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }]
        else:
            return self._reply(400, {"error": f"unknown llm skill: {skill}"})

        # Resolve agent paths against project_root and validate they stay inside.
        read_root_abs = write_root_abs = file_out_abs = None
        if agent_mode:
            try:
                if read_root:  read_root_abs  = _safe_join(project_root, read_root)
                if write_root: write_root_abs = _safe_join(project_root, write_root)
                if file_out_path: file_out_abs = _safe_join(project_root, file_out_path)
            except Exception as e:
                return self._reply(400, {"error": f"invalid agent path: {e}"})
            if read_root_abs and not os.path.isdir(read_root_abs):
                return self._reply(400, {"error": f"read_root is not a directory: {read_root}"})
            # Default: writes go to read_root if write_root not given.
            if not write_root_abs and read_root_abs:
                write_root_abs = read_root_abs

        tool_log = []
        try:
            if agent_mode and skill == "llm":
                # Build an agent guide telling the model what's wired and how
                # to read/write files. Injected as a system message above the
                # user-supplied system, so the agent's plumbing instructions
                # take precedence over content-level direction.
                guide_bits = []
                if read_root_abs:
                    guide_bits.append("You are an agent with read access to a project folder via two tools:")
                    guide_bits.append("  • list_dir(path) — list files/dirs at a relative path under the read root.")
                    guide_bits.append("  • read_file(path) — read a text file's content (UTF-8, max 200KB).")
                    guide_bits.append(f"Read root: {read_root}")
                    guide_bits.append("Always inspect the relevant files first with read_file before writing changes.")
                if write_root_abs:
                    guide_bits.append(f"Write root: {write_root or read_root}")
                    guide_bits.append("To WRITE files, emit fenced code blocks where the language tag is the relative path.")
                    guide_bits.append("Example:  ```src/foo.js\nconsole.log('hi');\n``` → writes src/foo.js")
                    guide_bits.append("Every fenced block tagged as a path will be written automatically after you finish.")
                if file_out_abs:
                    guide_bits.append(f"A single-file output is wired to: {file_out_path}")
                    guide_bits.append("Your entire reply (or the matching fenced block) will be written there.")
                if guide_bits:
                    messages = [{"role": "system", "content": "\n".join(guide_bits)}] + messages

                if read_root_abs:
                    tools = [
                        {"type": "function", "function": {
                            "name": "list_dir",
                            "description": "List files and directories under the agent's read root. Pass '' or '.' for the root.",
                            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                        }},
                        {"type": "function", "function": {
                            "name": "read_file",
                            "description": "Read a text file's content (UTF-8, max 200KB).",
                            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                        }},
                    ]
                    dispatch = _make_agent_dispatch(read_root_abs, write_root_abs)
                    text, tool_log = _openai_chat_tools(api_key, messages, model=model, tools=tools, dispatch=dispatch, options=options)
                else:
                    # write_root / file_out only — no tools, but the model gets
                    # the fenced-block instruction so writes still flow.
                    if provider == "anthropic":
                        text = _anthropic_chat(api_key, messages, model=model, options=options)
                    else:
                        text = _openai_chat(api_key, messages, model=model, options=options)
            else:
                if provider == "anthropic":
                    text = _anthropic_chat(api_key, messages, model=model, options=options, vision=(skill == "describe"))
                else:
                    text = _openai_chat(api_key, messages, model=model, options=options)
        except urllib.error.HTTPError as e:
            try: detail = json.loads(e.read().decode("utf-8", "replace"))
            except Exception: detail = {"status": e.code}
            return self._reply(502, {"error": f"{provider} API error", "detail": detail})
        except Exception as e:
            return self._reply(500, {"error": f"{type(e).__name__}: {e}"})

        # Apply writes after the final assistant reply.
        wrote = []
        write_error = None
        if agent_mode and skill == "llm":
            try:
                if write_root_abs:
                    wrote = _write_fenced_blocks(text, write_root_abs)
                if file_out_abs:
                    # If exactly one fenced block, write its body; otherwise the whole reply.
                    blocks = list(_FENCED_RE.finditer(text or ""))
                    if len(blocks) == 1:
                        out_content = blocks[0].group(2)
                        if out_content.endswith("\n"): out_content = out_content[:-1]
                    else:
                        out_content = text or ""
                    os.makedirs(os.path.dirname(file_out_abs), exist_ok=True)
                    with open(file_out_abs, "wb") as f: f.write(out_content.encode("utf-8"))
                    # Record file-out separately so the UI can highlight it.
                    if not any(w["path"] == file_out_path for w in wrote):
                        wrote.append({"path": file_out_path, "bytes": len(out_content.encode("utf-8")), "file_out": True})
            except Exception as e:
                write_error = f"{type(e).__name__}: {e}"

        return self._reply(200, {
            "ok": True, "text": text or "",
            "skill": skill, "provider": provider, "model": model,
            "agent": {"mode": agent_mode, "tool_log": tool_log, "wrote": wrote, "write_error": write_error} if agent_mode else None,
        })

    # ── Phase 4d — branch attachments (reference materials for agents) ──
    # POST /__attachment?project=<id>&branch=<slug>
    # Body: JSON { name: "foo.png", data_uri: "data:image/png;base64,…" }
    # Writes under source/<branch>/_attachments/<ts>-<slug>.<ext>.
    # Returns { ok, path: "_attachments/<ts>-<slug>.ext", abs_path, size }.
    #
    # Originally images-only (chat composer drag-and-drop), now also accepts
    # the kinds of files agents read as supporting brief: HTML/PDF/Markdown
    # moodboards, JSON specs, plain text notes, CSS tokens, fonts, archives.
    # The allow-list is explicit so unknown formats fail with a clear error
    # instead of silently writing binary blobs the agent can't open.
    _ATTACHMENT_MIME = {
        # Images
        "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg",
        "image/webp": "webp", "image/gif": "gif", "image/svg+xml": "svg",
        "image/avif": "avif", "image/heic": "heic", "image/bmp": "bmp",
        "image/tiff": "tiff",
        # Documents
        "application/pdf": "pdf",
        "text/html": "html", "application/xhtml+xml": "html",
        "text/markdown": "md", "text/x-markdown": "md",
        "text/plain": "txt",
        "text/css": "css",
        "text/javascript": "js", "application/javascript": "js",
        "application/json": "json", "text/json": "json",
        "application/xml": "xml", "text/xml": "xml",
        "text/csv": "csv",
        "text/yaml": "yaml", "application/yaml": "yaml", "application/x-yaml": "yaml",
        # Fonts
        "font/woff": "woff", "application/font-woff": "woff",
        "font/woff2": "woff2", "application/font-woff2": "woff2",
        "font/ttf": "ttf", "application/x-font-ttf": "ttf",
        "font/otf": "otf", "application/x-font-otf": "otf",
        # Archives (zip-packed design kits)
        "application/zip": "zip", "application/x-zip-compressed": "zip",
        # Audio / video (occasionally part of moodboards)
        "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/wav": "wav", "audio/ogg": "ogg",
        "video/mp4": "mp4", "video/webm": "webm", "video/quicktime": "mov",
    }
    # Browsers sometimes report MIME as "" or "application/octet-stream" for
    # files they don't recognize. Fall back to extension-based detection
    # against this map so a `.md` file still lands correctly.
    _ATTACHMENT_EXT_FALLBACK = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml",
        "avif": "image/avif", "heic": "image/heic", "bmp": "image/bmp", "tiff": "image/tiff",
        "pdf": "application/pdf",
        "html": "text/html", "htm": "text/html",
        "md": "text/markdown", "markdown": "text/markdown",
        "txt": "text/plain",
        "css": "text/css",
        "js": "text/javascript", "mjs": "text/javascript",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "yaml": "text/yaml", "yml": "text/yaml",
        "woff": "font/woff", "woff2": "font/woff2",
        "ttf": "font/ttf", "otf": "font/otf",
        "zip": "application/zip",
        "mp3": "audio/mpeg", "m4a": "audio/mp4", "wav": "audio/wav", "ogg": "audio/ogg",
        "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
    }
    def _attachment_upload(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=20 * 1024 * 1024)  # 20MB cap
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        branch = (
            body.get("prototype") or body.get("branch")
            or _qs_prototype(qs)
        ).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid prototype slug", "slug": branch})
        name_in = (body.get("name") or "attachment").strip()
        data_uri = body.get("data_uri") or ""
        if not isinstance(data_uri, str) or not data_uri.startswith("data:"):
            return self._reply(400, {"error": "data_uri must be a data: URL"})
        # Parse the data URI header.
        m = re.match(r"^data:([^;]*);base64,(.*)$", data_uri, re.DOTALL)
        if not m:
            return self._reply(400, {"error": "data_uri must be base64-encoded"})
        mime = (m.group(1) or "").lower().strip()
        ext = self._ATTACHMENT_MIME.get(mime)
        if not ext:
            # MIME-based lookup failed — try extension-based fallback. Useful
            # when browsers report an empty / generic MIME for known types.
            name_ext = (os.path.splitext(name_in)[1].lstrip(".") or "").lower()
            inferred_mime = self._ATTACHMENT_EXT_FALLBACK.get(name_ext)
            if inferred_mime and inferred_mime in self._ATTACHMENT_MIME:
                mime = inferred_mime
                ext = self._ATTACHMENT_MIME[inferred_mime]
        if not ext:
            return self._reply(400, {
                "error": f"unsupported attachment type: {mime or '(empty mime)'} (filename: {name_in})",
                "hint": "Allowed: common images, PDF, Markdown, HTML, text, JSON, CSS, JS, fonts (woff/woff2/ttf/otf), audio, video, zip. Convert or rename to a known extension.",
                "allowed_mimes": list(self._ATTACHMENT_MIME.keys()),
            })
        try:
            raw = base64.b64decode(m.group(2), validate=False)
        except Exception as e:
            return self._reply(400, {"error": f"base64 decode failed: {e}"})
        if len(raw) > 16 * 1024 * 1024:
            return self._reply(413, {"error": f"attachment too large ({len(raw)} bytes, max 16MB)"})
        base = _slugify(os.path.splitext(name_in)[0]) or "attachment"
        fname = f"{int(time.time() * 1000)}-{base}.{ext}"
        rel = f"_attachments/{fname}"
        try:
            abs_path = _safe_join(project_root, f"source/{branch}/{rel}")
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        rel_full = f"source/{branch}/{rel}"
        with _history_bracket(project_root, [rel_full],
                               kind="asset-gen", label=f"Upload: {os.path.basename(rel)}",
                               source="asset", extra={"branch": branch, "mime": mime}):
            with open(abs_path, "wb") as f: f.write(raw)
        return self._reply(200, {"ok": True, "path": rel, "size": len(raw), "mime": mime})

    # POST /__write_text?project=<id>
    # Body: JSON { path: "source/<branch>/<rel>", text: "..." }
    # Writes raw UTF-8 text to a project-scoped path. Used by Blend / Remix
    # output kinds "html" and (transitively) "text" when they want to emit
    # a file the user can open later. 2 MB cap keeps a single LLM response
    # from filling the disk if the model gets verbose.
    def _write_text(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=2 * 1024 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        rel = (body.get("path") or "").strip()
        text = body.get("text")
        if not isinstance(text, str):
            return self._reply(400, {"error": "text must be a string"})
        if not rel.startswith("source/"):
            return self._reply(400, {"error": "path must start with source/"})
        try:
            abs_path = _safe_join(project_root, rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with _history_bracket(project_root, [rel],
                                   kind="ui-edit", label=f"Write {rel}",
                                   source="editor"):
                with open(abs_path, "w", encoding="utf-8") as f: f.write(text)
        except OSError as e:
            return self._reply(500, {"error": f"write failed: {e}"})
        return self._reply(200, {"ok": True, "path": rel, "size": len(text.encode("utf-8"))})

    # POST /__html_save?project=<id>
    # Body: JSON { path: "source/<branch>/index.html", html: "<!doctype html>..." }
    # Writes a full HTML document atomically (.staging → os.replace). Used by
    # the Zoom overlay's Select / Text / Move / Resize tools — the overlay
    # mutates the iframe DOM in-place, serialises, and posts the entire doc
    # back. Robust against ops that html.parser can't apply granularly
    # (style/text/structure all flow through the same endpoint).
    # Refuses paths outside the project root and any extension that isn't
    # .html / .htm. 4 MB cap matches typical prototype size headroom.
    def _html_save(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        rel = (body.get("path") or "").strip()
        html = body.get("html")
        if not isinstance(html, str):
            return self._reply(400, {"error": "html must be a string"})
        if not rel.startswith("source/"):
            return self._reply(400, {"error": "path must start with source/"})
        if not (rel.endswith(".html") or rel.endswith(".htm")):
            return self._reply(400, {"error": "path must end in .html or .htm"})
        try:
            abs_path = _safe_join(project_root, rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isfile(abs_path):
            return self._reply(404, {"error": f"file not found: {rel}"})
        # Atomic write: stage next to target, then os.replace.
        staging = abs_path + ".staging"
        try:
            with _history_bracket(project_root, [rel],
                                   kind="ui-edit", label=f"Edit HTML: {rel}",
                                   source="editor"):
                with open(staging, "w", encoding="utf-8") as f:
                    f.write(html)
                os.replace(staging, abs_path)
        except OSError as e:
            try: os.unlink(staging)
            except Exception: pass
            return self._reply(500, {"error": f"write failed: {e}"})
        h = hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()[:16]
        return self._reply(200, {"ok": True, "path": rel, "size": len(html.encode("utf-8")), "version": h})

    # POST /__component_export?project=<id>
    # Body: JSON { path: "source/<branch>/components/<name>.html",
    #              html: "<!doctype html>...", overwrite?: bool }
    # Phase-7 export from the Zoom overlay. Creates a new standalone HTML file
    # under the branch's components/ folder containing a cloned DOM subtree +
    # extracted CSS rules. Refuses to clobber unless overwrite === true.
    def _component_export(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        rel = (body.get("path") or "").strip()
        # v3.4.1 — accept either `html` (legacy alias) or `content` for any
        # text-payload export. The endpoint is now used by llm/describe text
        # outputs, lottie-gen json, svg-gen svg, etc., not just HTML.
        html = body.get("html")
        content = body.get("content")
        payload = content if isinstance(content, str) and content.strip() else html
        overwrite = bool(body.get("overwrite"))
        if not isinstance(payload, str) or not payload.strip():
            return self._reply(400, {"error": "content (or html) must be a non-empty string"})
        if not rel.startswith("source/"):
            return self._reply(400, {"error": "path must start with source/"})
        ALLOWED_EXTS = (".html", ".htm", ".md", ".markdown", ".txt", ".svg",
                        ".json", ".css", ".js", ".mjs", ".ts", ".tsx", ".jsx")
        if not rel.lower().endswith(ALLOWED_EXTS):
            return self._reply(400, {"error": "path must end in one of " + ", ".join(ALLOWED_EXTS)})
        html = payload  # downstream write uses `html` var name
        try:
            abs_path = _safe_join(project_root, rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if os.path.exists(abs_path) and not overwrite:
            return self._reply(409, {"error": f"file exists: {rel}", "hint": "pass overwrite: true to clobber"})
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            staging = abs_path + ".staging"
            with _history_bracket(project_root, [rel],
                                   kind="ui-edit", label=f"Export component: {os.path.basename(rel)}",
                                   source="editor"):
                with open(staging, "w", encoding="utf-8") as f:
                    f.write(html)
                os.replace(staging, abs_path)
        except OSError as e:
            return self._reply(500, {"error": f"export failed: {e}"})
        return self._reply(200, {"ok": True, "path": rel, "size": len(html.encode("utf-8"))})

    # POST /__copy_file?project=<id>
    # Body: JSON { from: "source/<branch>/<rel>", to: "source/<branch>/<rel>" }
    # Copies a project-scoped file over another, preserving raw bytes. Used
    # by the asset card's "replace output" button so a generated variant
    # (Remix / Blend output) can overwrite a downstream asset (typically an
    # exposed file referenced by a prototype) in one click.
    def _copy_file(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        src_rel = (body.get("from") or "").strip()
        dst_rel = (body.get("to")   or "").strip()
        if not src_rel.startswith("source/") or not dst_rel.startswith("source/"):
            return self._reply(400, {"error": "from/to must start with source/"})
        if src_rel == dst_rel:
            return self._reply(400, {"error": "from and to are the same path"})
        try:
            src_abs = _safe_join(project_root, src_rel)
            dst_abs = _safe_join(project_root, dst_rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isfile(src_abs):
            return self._reply(404, {"error": f"source not found: {src_rel}"})
        try:
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            with open(src_abs, "rb") as f: raw = f.read()
            with _history_bracket(project_root, [dst_rel],
                                   kind="ui-edit",
                                   label=f"Copy → {os.path.basename(dst_rel)}",
                                   source="editor",
                                   extra={"from": src_rel}):
                with open(dst_abs, "wb") as f: f.write(raw)
        except OSError as e:
            return self._reply(500, {"error": f"copy failed: {e}"})
        return self._reply(200, {"ok": True, "from": src_rel, "to": dst_rel, "size": len(raw)})

    # POST /__replace_exposed_svg?project=<id>
    # Body: JSON {
    #   branch:  "main",
    #   surface: "<svg …>…</svg>",   # exact markup as stored in boundTo.surface
    #   new_src: "source/<branch>/images/<file>.png",
    #   width?:  140, height?: 150,
    #   alt?:    "..."
    # }
    # Walks every .html file under source/<branch>/ and replaces ALL exact
    # occurrences of `surface` with an <img> tag pointing at `new_src`. Used
    # by the asset card's "↻ replace" button when the connected target is an
    # inline-SVG exposed from a prototype: the prototype HTML gets rewritten
    # so the iframe re-renders with the PNG instead of the SVG.
    def _replace_exposed_svg(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        branch = (body.get("branch") or "main").strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})
        surface = body.get("surface")
        new_src = (body.get("new_src") or "").strip()
        if not isinstance(surface, str) or "<svg" not in surface.lower():
            return self._reply(400, {"error": "surface must be an SVG markup string"})
        if not new_src.startswith("source/"):
            return self._reply(400, {"error": "new_src must start with source/"})
        try:
            new_abs = _safe_join(project_root, new_src)
        except Exception as e:
            return self._reply(400, {"error": f"new_src path resolution failed: {e}"})
        if not os.path.isfile(new_abs):
            return self._reply(404, {"error": f"new_src not found: {new_src}"})
        try:
            branch_root = _safe_join(project_root, "source", branch)
        except Exception as e:
            return self._reply(400, {"error": f"branch path resolution failed: {e}"})
        if not os.path.isdir(branch_root):
            return self._reply(404, {"error": f"branch not found: source/{branch}/"})
        width  = body.get("width")
        height = body.get("height")
        alt    = (body.get("alt") or "").strip()
        # The `<img>` tag is built per-file inside the walk loop below — the
        # src needs to be relative to the HTML file's directory so the
        # browser resolves it correctly when the prototype iframe loads
        # (the iframe's URL is /source/<branch>/<file>.html, so an absolute
        # `source/<branch>/...` would resolve to /source/<branch>/source/...).
        def _build_img_tag(html_file_abs):
            html_dir = os.path.dirname(html_file_abs)
            src_abs  = _safe_join(project_root, new_src)
            rel = os.path.relpath(src_abs, html_dir).replace(os.sep, "/")
            attrs = [f'src="{rel}"']
            try:
                if width  and int(width)  > 0: attrs.append(f'width="{int(width)}"')
                if height and int(height) > 0: attrs.append(f'height="{int(height)}"')
            except (TypeError, ValueError): pass
            attrs.append(f'alt="{alt}"' if alt else 'alt=""')
            # JSX-safe self-closing form. The prototype HTML is JSX inside
            # <script type="text/babel">, where `<img>` MUST be `<img … />`;
            # the open-only form is a parse error and kills the whole
            # script. In plain HTML5 the trailing slash is ignored, so
            # this form is safe for non-JSX files too.
            return f'<img {" ".join(attrs)} />'

        # The `surface` arrives from the iframe's runtime-serialized
        # outerHTML: one line, void elements written as <foo …></foo>. The
        # raw HTML on disk usually has indentation + self-closing <foo …/>.
        # Normalize both so we can match across that gap, then replace the
        # ORIGINAL <svg>…</svg> block (not the normalized form) so we don't
        # disturb the file's formatting outside the replacement window.
        def _normalize(s):
            # Convert self-closing tags to explicit open/close: <foo a="b"/> →
            # <foo a="b"></foo>. Skip <br/> / <img/> / <meta/> / <link/>
            # since the surface format may or may not close those — they
            # don't appear inside the SVG anyway.
            def _expand_self_closing(text):
                out = []
                i = 0
                while i < len(text):
                    if text[i] == "<":
                        # Find tag end
                        j = i + 1
                        while j < len(text) and text[j] != ">":
                            j += 1
                        if j >= len(text):
                            out.append(text[i:]); break
                        tag_body = text[i+1:j]
                        if tag_body.endswith("/") and not tag_body.startswith("/"):
                            inner = tag_body[:-1].rstrip()
                            name_m = re.match(r"^([a-zA-Z][a-zA-Z0-9:-]*)", inner)
                            if name_m:
                                name = name_m.group(1)
                                out.append(f"<{inner}></{name}>")
                                i = j + 1
                                continue
                        out.append(text[i:j+1])
                        i = j + 1
                    else:
                        out.append(text[i])
                        i += 1
                return "".join(out)
            t = _expand_self_closing(s)
            # The prototype HTML is JSX inside <script type="text/babel">,
            # so attribute names are camelCase (`strokeWidth`, `fillRule`).
            # The runtime-serialized surface from the iframe DOM is the
            # rendered output — React lowers those to kebab-case
            # (`stroke-width`). Convert any camelCase attribute name to
            # kebab-case so both sides line up. We only touch the name
            # before `=`, never the value, so quoted strings (which may
            # contain capitals) are unaffected.
            t = re.sub(
                r'(\s)([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)(\s*=)',
                lambda m: m.group(1) + re.sub(r'([A-Z])', r'-\1', m.group(2)).lower() + m.group(3),
                t,
            )
            # Collapse whitespace between tags (>\s+< → ><) and inside attrs.
            t = re.sub(r">\s+<", "><", t)
            t = re.sub(r"\s+", " ", t)
            return t.strip()

        norm_surface = _normalize(surface)
        updated_files = []
        # Wrap the whole branch-wide scan with a scope bracket so undo
        # restores every file the scan touched in one atomic step.
        with _history_scope_bracket(project_root, [f"source/{branch}"],
                                     kind="asset-gen",
                                     label="Replace inline SVG with image",
                                     source="asset",
                                     extra={"branch": branch}):
          for dirpath, _, filenames in os.walk(branch_root):
            for fname in filenames:
                if not fname.endswith(".html"): continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f: html = f.read()
                except OSError: continue
                # Cheap pre-filter: skip files that don't even contain the
                # SVG opening fingerprint (first 40 chars of the surface).
                fingerprint = surface[:40]
                if fingerprint not in html and _normalize(fingerprint) not in _normalize(html):
                    continue
                img_tag = _build_img_tag(fpath)
                # Walk every <svg…</svg> block and check its normalized form.
                new_html_parts = []
                cursor = 0
                replacements = 0
                while True:
                    open_at = html.find("<svg", cursor)
                    if open_at < 0:
                        new_html_parts.append(html[cursor:])
                        break
                    close_at = html.find("</svg>", open_at)
                    if close_at < 0:
                        new_html_parts.append(html[cursor:])
                        break
                    block_end = close_at + len("</svg>")
                    block = html[open_at:block_end]
                    if _normalize(block) == norm_surface:
                        new_html_parts.append(html[cursor:open_at])
                        new_html_parts.append(img_tag)
                        replacements += 1
                        cursor = block_end
                    else:
                        new_html_parts.append(html[cursor:open_at + 1])
                        cursor = open_at + 1
                if replacements == 0: continue
                new_html = "".join(new_html_parts)
                try:
                    with open(fpath, "w", encoding="utf-8") as f: f.write(new_html)
                except OSError as e:
                    return self._reply(500, {"error": f"write failed for {fpath}: {e}"})
                updated_files.append({
                    "path": os.path.relpath(fpath, project_root),
                    "replacements": replacements,
                    "img_tag": img_tag,
                })
        if not updated_files:
            return self._reply(404, {"error": "no HTML file under source/" + branch + "/ contains that SVG surface (after whitespace / self-closing normalisation)"})
        return self._reply(200, {"ok": True, "files": updated_files})

    # ── Phase 4c — local skills (rembg etc.) install + status ────────────
    # Whitelist of installable packages and the extras to bundle. Limiting
    # to a known set prevents the install button from being a pip-arbitrary-
    # package exploit if the daemon is ever exposed beyond localhost.
    _LOCAL_PACKAGES = {
        "rembg": {"packages": ["rembg", "onnxruntime"], "import": "rembg"},
    }

    # GET /__ls_dirs?project=<id>&root=<rel-or-abs>
    # Returns a list of immediate child directories under `root`. Used by the
    # agent's "folder output" picker so the user can browse the project tree
    # (or any local path) to pick where the agent should write. If `root` is
    # a relative path it's resolved against the project root (so paths like
    # `source/main` work the same as in other endpoints). Absolute paths are
    # honored as-is. Symlinks are followed but never traversed past the user-
    # specified root in one call.
    def _ls_dirs(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError:
            project_root = None
        root = (_qs_get(qs, "root") or "").strip()
        # Default to the active project's source/ when nothing specified.
        if not root:
            if not project_root: return self._reply(400, {"error": "no project and no root specified"})
            root = "source"
        if os.path.isabs(root):
            abs_root = root
        else:
            if not project_root:
                return self._reply(400, {"error": "relative root needs a project"})
            try:
                abs_root = _safe_join(project_root, root)
            except Exception as e:
                return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isdir(abs_root):
            return self._reply(404, {"error": f"not a directory: {root}"})
        try:
            entries = []
            for name in sorted(os.listdir(abs_root)):
                if name.startswith("."): continue
                full = os.path.join(abs_root, name)
                if not os.path.isdir(full): continue
                entries.append({
                    "name": name,
                    "abs":  full,
                    "rel":  os.path.relpath(full, project_root).replace(os.sep, "/") if project_root else None,
                })
        except OSError as e:
            return self._reply(500, {"error": f"listdir failed: {e}"})
        return self._reply(200, {
            "ok": True,
            "root_abs": abs_root,
            "root_rel": os.path.relpath(abs_root, project_root).replace(os.sep, "/") if project_root and abs_root.startswith(project_root) else None,
            "parent_abs": os.path.dirname(abs_root) if abs_root != "/" else None,
            "dirs": entries,
        })

    # GET /__list_files?project=<id>&root=<rel>&exts=html,htm
    # Recursively walks `root` (relative to project root or absolute) and
    # returns every file whose extension is in `exts` (case-insensitive,
    # dot-prefix optional). Skips `_attachments/`, `_tmp/`, hidden dirs,
    # and anything under .staging/. Used by the prototype DS-audit feature
    # to enumerate all HTML files the audit should walk.
    #
    # Response shape: { ok, root_rel, files: [{ path, size, modified }] }
    # where `path` is project-relative, normalised with forward slashes.
    def _list_files(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        root = (_qs_get(qs, "root") or "").strip()
        if not root:
            return self._reply(400, {"error": "root is required (relative or absolute)"})
        exts_raw = (_qs_get(qs, "exts") or "").strip()
        exts = set()
        for e in exts_raw.split(","):
            e = e.strip().lstrip(".").lower()
            if e: exts.add(e)
        if not exts:
            return self._reply(400, {"error": "exts is required (e.g. exts=html,htm)"})
        if os.path.isabs(root):
            abs_root = root
        else:
            try:
                abs_root = _safe_join(project_root, root)
            except Exception as e:
                return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isdir(abs_root):
            return self._reply(404, {"error": f"not a directory: {root}"})
        SKIP_DIR_NAMES = {"_attachments", "_tmp", ".staging", ".git", "node_modules"}
        files = []
        try:
            for dirpath, dirnames, filenames in os.walk(abs_root):
                # Prune hidden + skipped dirs in-place so os.walk doesn't descend.
                dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIR_NAMES]
                for name in filenames:
                    if name.startswith("."): continue
                    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                    if ext not in exts: continue
                    full = os.path.join(dirpath, name)
                    try:
                        st = os.stat(full)
                    except OSError:
                        continue
                    rel = os.path.relpath(full, project_root).replace(os.sep, "/") if project_root else full
                    files.append({
                        "path": rel,
                        "size": st.st_size,
                        "modified": int(st.st_mtime),
                    })
        except OSError as e:
            return self._reply(500, {"error": f"walk failed: {e}"})
        files.sort(key=lambda f: f["path"])
        return self._reply(200, {
            "ok": True,
            "root_rel": os.path.relpath(abs_root, project_root).replace(os.sep, "/") if project_root and abs_root.startswith(project_root) else None,
            "files": files,
        })

    # POST /__native_folder_picker[?project=<id>]
    # Invokes the OS-native folder picker (macOS via osascript) and returns
    # the chosen absolute path. If a project query is included AND the
    # chosen path is INSIDE that project's root, we ALSO return a
    # project-relative path the caller can prefer — so the picked folder
    # gets stored as `source/<branch>/foo` instead of `/Users/…/source/<branch>/foo`,
    # which is what the daemon's file-serving and safe-join paths expect.
    def _native_folder_picker(self):
        if sys.platform != "darwin":
            return self._reply(501, {"error": f"native folder picker not implemented on {sys.platform}"})
        try:
            r = subprocess.run(
                ["osascript", "-e", 'POSIX path of (choose folder with prompt "Pick a folder for the agent output")'],
                capture_output=True, timeout=60, check=False,
            )
        except subprocess.TimeoutExpired:
            return self._reply(504, {"error": "folder picker timed out"})
        except FileNotFoundError:
            return self._reply(501, {"error": "osascript not on PATH"})
        if r.returncode != 0:
            return self._reply(200, {"ok": True, "cancelled": True})
        path = r.stdout.decode("utf-8", "replace").strip()
        if not path:
            return self._reply(200, {"ok": True, "cancelled": True})
        # osascript appends a trailing slash to POSIX paths; strip for consistency.
        if path.endswith("/") and len(path) > 1: path = path[:-1]
        # Compute project-relative form if the chosen path is inside the
        # active project's root. The caller can use this to keep paths
        # portable across machines + compatible with the daemon's safe-join.
        rel = None
        try:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            project_root = resolve_project_root(qs)
            if project_root:
                pr = os.path.realpath(project_root)
                pp = os.path.realpath(path)
                if pp == pr or pp.startswith(pr + os.sep):
                    rel = os.path.relpath(pp, pr).replace(os.sep, "/")
        except Exception:
            rel = None
        return self._reply(200, {"ok": True, "path": path, "rel": rel})

    # GET /__export_config[?project=<id>]
    # POST /__export_config?project=<id>  body {path:string|null}
    #
    # Per-project export folder. Stored on each project entry in
    # workspace.json as `exportFolder`. No body → returns map of every
    # known project's current value (Settings dialog reads this). A
    # `project=<id>` query narrows to a single entry. POST updates the
    # named project's entry (creating it if absent).
    def _export_config_get(self, qs):
        pid = (qs.get("project") or [""])[0].strip() if isinstance(qs, dict) else ""
        if pid:
            folder = _export_folder_get(pid) or ""
            return self._reply(200, {
                "project":      pid,
                "exportFolder": folder,
                "status":       _export_folder_status(folder) if folder else None,
            })
        # No project query → enumerate every workspace.json project entry.
        data = _workspace_json_load()
        out = []
        for entry in data.get("projects", []):
            if not isinstance(entry, dict): continue
            eid = entry.get("id")
            if not eid: continue
            folder = entry.get("exportFolder") or ""
            out.append({
                "id":           eid,
                "label":        entry.get("label") or eid,
                "exportFolder": folder,
                "status":       _export_folder_status(folder) if folder else None,
            })
        # Also include any discoverable on-disk projects that aren't in
        # workspace.json yet — so the Settings UI lists every project the
        # user can actually open, not just the ones with a saved entry.
        seen = {p["id"] for p in out}
        for p in _list_projects():
            if p["id"] not in seen:
                out.append({
                    "id":           p["id"],
                    "label":        p.get("label") or p["id"],
                    "exportFolder": "",
                    "status":       None,
                })
        return self._reply(200, {"projects": out})

    def _export_config_set(self, qs):
        pid = (qs.get("project") or [""])[0].strip() if isinstance(qs, dict) else ""
        if not pid:
            return self._reply(400, {"error": "missing ?project=<id>"})
        if not PROJECT_ID_OK.match(pid):
            return self._reply(400, {"error": "invalid project id"})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "body must be an object"})
        raw = body.get("path")
        if raw is None:
            stored = _export_folder_set(pid, None)
        else:
            if not isinstance(raw, str):
                return self._reply(400, {"error": "path must be a string or null"})
            try:
                stored = _export_folder_set(pid, raw)
            except ValueError as e:
                return self._reply(400, {"error": str(e)})
        return self._reply(200, {
            "ok":           True,
            "project":      pid,
            "exportFolder": stored,
            "status":       _export_folder_status(stored) if stored else None,
        })

    # POST /__export_asset?project=<id>  body {nodeId:string}
    # Bundles the named asset/prototype/container node into the project's
    # configured export folder. Returns the absolute bucket path so the UI
    # can reveal it in Finder. See editor/exports.py for the per-kind
    # dispatch + README templates + serve.command helper.
    def _export_asset(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        pid = (qs.get("project") or [""])[0].strip() if isinstance(qs, dict) else ""
        if not pid:
            # Single-project mode resolves project_root without an id; in
            # that case use the virtual "default" project for storage.
            pid = "default"
        try:
            body = self._read_json_body(max_bytes=64 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "body must be an object"})
        node_id = (body.get("nodeId") or "").strip()
        if not node_id:
            return self._reply(400, {"error": "missing nodeId in body"})
        export_root = _export_folder_get(pid)
        if not export_root:
            return self._reply(400, {
                "error":     "no export folder set for this project",
                "hint":      "open the ⤓ Exports button in the workflow toolbar and pick a destination folder",
                "project":   pid,
            })
        # Find the node in workflow.json.
        wf_path = os.path.join(project_root, "workflow", "workflow.json")
        if not os.path.isfile(wf_path):
            return self._reply(404, {"error": "workflow.json not found"})
        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf = json.load(f)
        except Exception as e:
            return self._reply(500, {"error": f"workflow.json unreadable: {e}"})
        node = next((n for n in (wf.get("nodes") or [])
                     if isinstance(n, dict) and n.get("id") == node_id), None)
        if not node:
            return self._reply(404, {"error": f"node not found: {node_id!r}"})
        try:
            manifest = _exports.export_node(node, project_root, export_root)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        except OSError as e:
            return self._reply(500, {"error": f"export failed: {e}"})
        return self._reply(200, manifest)

    # GET /__source_prototypes?project=<id>
    # Walks `source/` to find every folder containing an `index.html`. Returns
    # them as a flat list so the workflow library can surface agent-generated
    # prototypes (e.g. `source/new/`, `source/main/sketches/`) alongside the
    # registered workspace branches. Two levels deep — `source/<branch>/...`
    # is the canonical structure, so we scan one extra level beyond branches.
    def _source_prototypes(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        src_root = os.path.join(project_root, "source")
        if not os.path.isdir(src_root):
            return self._reply(200, {"prototypes": []})
        found = []
        try:
            # Level 1: source/<dir>/index.html (canonical branch root).
            for name in sorted(os.listdir(src_root)):
                if name.startswith("."): continue
                lvl1 = os.path.join(src_root, name)
                if not os.path.isdir(lvl1): continue
                idx1 = os.path.join(lvl1, "index.html")
                if os.path.isfile(idx1):
                    found.append({
                        "id":    name,
                        "path":  f"source/{name}/index.html",
                        "label": name,
                        "depth": 1,
                    })
                # Level 2: source/<dir>/<sub>/index.html (sub-prototype).
                for sub in sorted(os.listdir(lvl1)):
                    if sub.startswith(".") or sub == "index.html": continue
                    lvl2 = os.path.join(lvl1, sub)
                    if not os.path.isdir(lvl2): continue
                    idx2 = os.path.join(lvl2, "index.html")
                    if os.path.isfile(idx2):
                        found.append({
                            "id":    f"{name}/{sub}",
                            "path":  f"source/{name}/{sub}/index.html",
                            "label": sub,
                            "branch": name,
                            "depth": 2,
                        })
        except OSError as e:
            return self._reply(500, {"error": f"scan failed: {e}"})
        return self._reply(200, {"prototypes": found})

    # ─────────────────────────────────────────────────────────────────────
    # Starred prototypes — per-project bookmarks of specific prototype slugs
    # that the user has chosen to surface on the projects landing + in the
    # workflow library. Storage: <project>/.starred-prototypes.json with
    # shape { "starred": ["<id1>", "<id2>", ...] } where each id matches
    # the `id` returned by /__source_prototypes (e.g. "main", "main/sketches").
    # ─────────────────────────────────────────────────────────────────────
    def _starred_prototypes_path(self, project_root):
        return os.path.join(project_root, ".starred-prototypes.json")

    def _read_starred_ids(self, project_root):
        path = self._starred_prototypes_path(project_root)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            arr = data.get("starred") if isinstance(data.get("starred"), list) else []
            return [s for s in arr if isinstance(s, str) and s]
        except Exception:
            return []

    def _write_starred_ids(self, project_root, ids):
        path = self._starred_prototypes_path(project_root)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"starred": ids}, f, indent=2)
                f.write("\n")
            return True
        except OSError:
            return False

    def _hydrate_starred(self, project_root, ids):
        """Resolve each starred id to a full {id, path, label, exists} entry
        by reusing the prototype-scan logic. ids that no longer match a real
        prototype on disk still come back, marked exists=False, so the UI
        can render them as broken without losing the bookmark."""
        src_root = os.path.join(project_root, "source")
        found_by_id = {}
        if os.path.isdir(src_root):
            try:
                for name in sorted(os.listdir(src_root)):
                    if name.startswith("."): continue
                    lvl1 = os.path.join(src_root, name)
                    if not os.path.isdir(lvl1): continue
                    if os.path.isfile(os.path.join(lvl1, "index.html")):
                        found_by_id[name] = {
                            "id": name,
                            "path": f"source/{name}/index.html",
                            "label": name,
                            "depth": 1,
                        }
                    for sub in sorted(os.listdir(lvl1)):
                        if sub.startswith(".") or sub == "index.html": continue
                        lvl2 = os.path.join(lvl1, sub)
                        if not os.path.isdir(lvl2): continue
                        if os.path.isfile(os.path.join(lvl2, "index.html")):
                            cid = f"{name}/{sub}"
                            found_by_id[cid] = {
                                "id": cid,
                                "path": f"source/{name}/{sub}/index.html",
                                "label": sub,
                                "branch": name,
                                "depth": 2,
                            }
            except OSError:
                pass
        out = []
        for sid in ids:
            if sid in found_by_id:
                e = dict(found_by_id[sid])
                e["exists"] = True
                out.append(e)
            else:
                # Bookmark lives on; we just couldn't find the prototype on disk.
                label = sid.rsplit("/", 1)[-1] or sid
                out.append({
                    "id": sid,
                    "path": f"source/{sid}/index.html",
                    "label": label,
                    "exists": False,
                })
        return out

    # GET /__starred_prototypes?project=<id>
    def _starred_prototypes_get(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        ids = self._read_starred_ids(project_root)
        return self._reply(200, {"starred": self._hydrate_starred(project_root, ids)})

    # POST /__starred_prototypes/toggle  body: { id, starred?: bool }
    # If `starred` is omitted, flips the current state. Returns the new full list.
    def _starred_prototypes_toggle(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        body = self._read_json_body() or {}
        sid = (body.get("id") or "").strip()
        if not sid:
            return self._reply(400, {"error": "missing id"})
        # Sanity-bound the id — must look like the slugs we scan for.
        if not re.match(r"^[A-Za-z0-9_.-]{1,80}(?:/[A-Za-z0-9_.-]{1,80})?$", sid):
            return self._reply(400, {"error": "invalid id shape", "id": sid})
        ids = self._read_starred_ids(project_root)
        want = body.get("starred")
        if want is None:
            want = sid not in ids
        if want and sid not in ids:
            ids.append(sid)
        elif not want and sid in ids:
            ids = [s for s in ids if s != sid]
        if not self._write_starred_ids(project_root, ids):
            return self._reply(500, {"error": "write failed"})
        return self._reply(200, {
            "starred": self._hydrate_starred(project_root, ids),
            "ids": ids,
            "toggled": sid,
            "now": bool(want),
        })

    # ─────────────────────────────────────────────────────────────────────
    # Thumbnail prototype — per-project pick of a SINGLE prototype slug
    # to render as the landing-card preview. Distinct from starred prototypes
    # (multi-item list, surfaced as a starred list under the card). Storage:
    # <project>/.thumbnail-prototype.json with shape { "id": "<slug>" } or
    # { "id": "" } / missing file → no thumbnail. Same slug schema as
    # /__starred_prototypes and /__source_prototypes ("main", "main/sketches").
    # ─────────────────────────────────────────────────────────────────────
    def _thumbnail_prototype_path(self, project_root):
        return os.path.join(project_root, ".thumbnail-prototype.json")

    def _read_thumbnail_path(self, project_root):
        """Return the project-relative source path of the chosen thumbnail
        ("" if none). Backwards-compatible read: the v1 shape stored a
        prototype slug under "id" — if we encounter that we promote it to
        the v2 path (source/<slug>/index.html) on the fly so old saves keep
        working without a migration script."""
        path = self._thumbnail_prototype_path(project_root)
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            tp = data.get("path")
            if isinstance(tp, str) and tp:
                return tp
            sid = data.get("id")
            if isinstance(sid, str) and sid:
                # v1 → v2 promotion: prototype slug → source path.
                return f"source/{sid}/index.html"
            return ""
        except Exception:
            return ""

    def _write_thumbnail_path(self, project_root, tp):
        path = self._thumbnail_prototype_path(project_root)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"path": tp or ""}, f, indent=2)
                f.write("\n")
            return True
        except OSError:
            return False

    def _hydrate_thumbnail(self, project_root, tp):
        """Resolve a project-relative `tp` (e.g. "source/main/index.html",
        "source/main/page-bento.html", "source/main/_ds/v1/page.html") to
        a {path, label, exists} entry. Returns None on empty tp. Anything
        outside source/ is rejected — keeps the thumbnail strictly to
        user-generated HTML."""
        if not tp:
            return None
        norm = tp.replace("\\", "/").lstrip("/")
        if not norm.startswith("source/") or not (norm.lower().endswith(".html") or norm.lower().endswith(".htm")):
            return {"path": tp, "label": tp.rsplit("/", 1)[-1] or tp, "exists": False}
        abs_path = os.path.join(project_root, norm)
        exists = os.path.isfile(abs_path)
        # Label: for an index.html, surface the parent dir name (prototype
        # slug); for any other html page, surface its filename.
        parts = norm.split("/")
        if parts[-1] == "index.html" and len(parts) >= 3:
            label = "/".join(parts[1:-1])
        else:
            label = parts[-1]
        return {"path": norm, "label": label, "exists": exists}

    # GET /__thumbnail_prototype?project=<id>
    def _thumbnail_prototype_get(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        tp = self._read_thumbnail_path(project_root)
        return self._reply(200, {"path": tp, "thumbnail": self._hydrate_thumbnail(project_root, tp)})

    # POST /__thumbnail_prototype/set  body: { path }   ("" to clear)
    # Accepts a v1 `id` field too (prototype slug → promoted to source path).
    def _thumbnail_prototype_set(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        body = self._read_json_body() or {}
        tp = (body.get("path") or "").strip()
        if not tp:
            # Back-compat with the v1 caller that sent {id: "<slug>"}.
            sid = (body.get("id") or "").strip()
            if sid and re.match(r"^[A-Za-z0-9_.\-]{1,80}(?:/[A-Za-z0-9_.\-]{1,80})?$", sid):
                tp = f"source/{sid}/index.html"
        if tp:
            norm = tp.replace("\\", "/").lstrip("/")
            # Must be a project-relative html file under source/. No "..",
            # no absolute paths, length-bounded.
            if (".." in norm.split("/")
                    or not norm.startswith("source/")
                    or not (norm.lower().endswith(".html") or norm.lower().endswith(".htm"))
                    or len(norm) > 400
                    or not re.match(r"^[A-Za-z0-9_./\-]+$", norm)):
                return self._reply(400, {"error": "invalid path", "path": tp})
            tp = norm
        if not self._write_thumbnail_path(project_root, tp):
            return self._reply(500, {"error": "write failed"})
        return self._reply(200, {
            "path": tp,
            "thumbnail": self._hydrate_thumbnail(project_root, tp),
        })

    # GET /__source_htmls?project=<id>
    # Walks source/ for every .html / .htm file EXCEPT the index.html files
    # picked up by /__source_prototypes (which already surface as Prototypes
    # in the workflow library). Used by the Library "HTML pages" section to
    # surface agent-generated pages — DS brainstorm outputs (page-*.html,
    # ds-samples.html), iterator-produced variants, ad-hoc Write outputs.
    # Walks up to MAX_DEPTH levels deep so deeply nested generators land too.
    # Returns relative paths + branch + mtime; sorted newest first.
    def _source_htmls(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        src_root = os.path.join(project_root, "source")
        if not os.path.isdir(src_root):
            return self._reply(200, {"htmls": []})
        MAX_DEPTH = 5
        # Collect the set of prototype index.html paths so we can exclude them.
        # Matches the depth-1 + depth-2 logic in _source_prototypes.
        prototype_indexes = set()
        try:
            for name in os.listdir(src_root):
                if name.startswith("."): continue
                lvl1 = os.path.join(src_root, name)
                if not os.path.isdir(lvl1): continue
                idx1 = os.path.join(lvl1, "index.html")
                if os.path.isfile(idx1):
                    prototype_indexes.add(idx1)
                for sub in os.listdir(lvl1):
                    if sub.startswith("."): continue
                    lvl2 = os.path.join(lvl1, sub)
                    if not os.path.isdir(lvl2): continue
                    idx2 = os.path.join(lvl2, "index.html")
                    if os.path.isfile(idx2):
                        prototype_indexes.add(idx2)
        except OSError:
            pass
        found = []
        try:
            for root, dirs, files in os.walk(src_root):
                # Skip hidden dirs (.git, .DS_Store) and the per-branch
                # _attachments / _tmp helper folders we use for reference
                # materials and intermediate raster bytes.
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("_attachments", "_tmp", "node_modules")]
                rel_root = os.path.relpath(root, src_root)
                depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
                if depth > MAX_DEPTH:
                    dirs[:] = []
                    continue
                # Split rel_root into segments. The first segment (if any) is
                # the branch slug — we use it as the entry's branch field.
                segs = [] if rel_root == "." else rel_root.split(os.sep)
                branch = segs[0] if segs else ""
                for fname in files:
                    if not fname.lower().endswith((".html", ".htm")): continue
                    if fname.startswith("."): continue
                    fpath = os.path.join(root, fname)
                    if fpath in prototype_indexes: continue
                    if not os.path.isfile(fpath): continue
                    # v3.4.16 — Skip HTML files living inside the asset
                    # subdirs (images/, svg/, shaders/, viz/, models/,
                    # video/, audio/). Those are skill outputs from
                    # shader / threejs / canvas-gen / viz / motion-gen /
                    # lottie-gen, already enumerated by /__assets with
                    # the correct extension-based kind. Listing them
                    # again here produced duplicate library entries —
                    # the user sees the same scene twice, once as an
                    # HTML page (renders fine) and once as an "image"
                    # asset (broken when dragged).
                    if len(segs) >= 2 and segs[1] in self._LIB_ASSET_SUBDIRS:
                        continue
                    try: st = os.stat(fpath)
                    except Exception: continue
                    rel = os.path.relpath(fpath, project_root).replace("\\", "/")
                    # Label: folder/file when nested, just file when at prototype root.
                    if len(segs) <= 1:
                        label = fname
                    else:
                        label = "/".join(segs[1:]) + "/" + fname
                    # v3.7 — Classify DS-related pages so the editor can surface
                    # them in their own Library section ("Design system pages")
                    # between Prototypes and plain HTML pages. Two signals:
                    #   • Anywhere under a `_ds_brainstorm/` folder (the
                    #     Workflow 0 brainstorm fan-out lands here).
                    #   • Files exactly named `gallery.html` or `ds-samples.html`
                    #     at any depth (legacy DS scaffolds + one-offs). We DO
                    #     NOT match `ds-*` or `page-*` generically — those
                    #     prefixes overlap with regular feature pages
                    #     (e.g. `page-about.html` is a normal HTML page).
                    fname_lower = fname.lower()
                    in_ds_brainstorm = "_ds_brainstorm" in segs
                    is_ds_named = (
                        fname_lower == "gallery.html"
                        or fname_lower == "ds-samples.html"
                    )
                    entry = {
                        "path":   rel,
                        "name":   fname,
                        "label":  label,
                        "branch": branch,
                        "size":   st.st_size,
                        "mtime":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
                    }
                    if in_ds_brainstorm or is_ds_named:
                        entry["kind"] = "ds-page"
                    found.append(entry)
        except OSError as e:
            return self._reply(500, {"error": f"scan failed: {e}"})
        # Also enumerate design-systems/<id>/gallery.html so DS library
        # nodes show up in the Library → Outputs → HTML pages section and
        # can be dragged onto the canvas as an HTML asset card (1920×1440
        # iframe of the kitchen-sink gallery).
        ds_root = os.path.join(project_root, "design-systems")
        if os.path.isdir(ds_root):
            try:
                for ds_id in sorted(os.listdir(ds_root)):
                    if ds_id.startswith("."): continue
                    ds_dir = os.path.join(ds_root, ds_id)
                    if not os.path.isdir(ds_dir): continue
                    gpath = os.path.join(ds_dir, "gallery.html")
                    if not os.path.isfile(gpath): continue
                    try: st = os.stat(gpath)
                    except Exception: continue
                    rel = os.path.relpath(gpath, project_root).replace("\\", "/")
                    found.append({
                        "path":   rel,                          # "design-systems/<id>/gallery.html"
                        "name":   "gallery.html",
                        "label":  f"DS · {ds_id} · gallery",   # distinct from "source/<branch>/" rows
                        "branch": "design-system",
                        "kind":   "ds-gallery",
                        "size":   st.st_size,
                        "mtime":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
                    })
            except OSError:
                pass
        found.sort(key=lambda x: x["mtime"], reverse=True)
        return self._reply(200, {"htmls": found})

    # POST /__rewrite_img_src?project=<id>
    # Body: JSON {
    #   branch:  "main",
    #   old_src: "source/<branch>/images/foo.png",
    #   new_src: "source/<branch>/images/foo.svg",
    # }
    # Walks every .html / .htm / .jsx / .tsx / .js / .ts file under
    # source/<branch>/ and, for each `<img>` tag whose `src` resolves to the
    # SAME file as `old_src` (matched by file basename — relative paths to a
    # different folder still hit), rewrites the `src` attribute to point at
    # `new_src`. Used by the asset card's "replace output" button when the
    # user swaps a PNG/JPG/etc. on a prototype for an SVG (or any other
    # extension change). Without this rewrite, the prototype's `<img>` tag
    # would keep referencing the old file extension and the new file would
    # be orphaned on disk, making the image vanish from the iframe.
    def _rewrite_img_src(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        branch  = (body.get("branch") or "main").strip().lower()
        old_src = (body.get("old_src") or "").strip()
        new_src = (body.get("new_src") or "").strip()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})
        if not old_src.startswith("source/") or not new_src.startswith("source/"):
            return self._reply(400, {"error": "old_src/new_src must start with source/"})
        try:
            branch_root = _safe_join(project_root, "source", branch)
        except Exception as e:
            return self._reply(400, {"error": f"branch path resolution failed: {e}"})
        if not os.path.isdir(branch_root):
            return self._reply(404, {"error": f"branch not found: source/{branch}/"})

        # Match strategy: we don't know exactly how each `<img>` source was
        # spelled (absolute "source/<branch>/images/foo.png", or relative
        # "images/foo.png", or "./images/foo.png"). Strip the per-branch
        # prefix from both old and new to get the "tail" that any tag's src
        # is likely to end with, then match by that tail. This covers JSX
        # `<img src="images/foo.png"/>` AND plain HTML `<img src="./images/
        # foo.png">` AND the rare absolute form.
        prefix = f"source/{branch}/"
        old_tail = old_src[len(prefix):] if old_src.startswith(prefix) else old_src
        new_tail = new_src[len(prefix):] if new_src.startswith(prefix) else new_src
        old_base = os.path.basename(old_tail)
        new_base = os.path.basename(new_tail)

        EXTS = (".html", ".htm", ".jsx", ".tsx", ".js", ".ts")
        files_changed = []
        # Regex: `<img …src="<dir>/<old_basename>"…>` where <dir> ends in `/`
        # OR is empty (when src is exactly the basename). The mandatory `/`
        # boundary prevents partial-basename matches — e.g., asking to swap
        # `foo.png` must NOT rewrite `<img src="other-foo.png">`. Handles
        # both single and double quotes; case-insensitive for the tag name
        # and the basename.
        img_src_re = re.compile(
            r'(<img\b[^>]*?\bsrc\s*=\s*["\'])'    # 1: prefix incl opening quote
            r'((?:[^"\']*/)?)'                     # 2: optional directory ending in /
            r'(' + re.escape(old_base) + r')'      # 3: the basename
            r'(["\'])',                            # 4: closing quote
            re.IGNORECASE,
        )

        def _swap(text):
            def repl(m):
                # Group 2 captures the directory ending in `/` (or is empty
                # when src is just the basename). The mandatory `/` boundary
                # is enforced by the pattern itself, so any match here is a
                # true basename hit — safe to rewrite.
                return m.group(1) + m.group(2) + new_base + m.group(4)
            new_text, n = img_src_re.subn(repl, text)
            return new_text, n

        with _history_scope_bracket(project_root, [f"source/{branch}"],
                                     kind="asset-gen",
                                     label=f"Rewrite img src: {old_base} → {new_base}",
                                     source="asset",
                                     extra={"branch": branch, "old": old_src, "new": new_src}):
          for dirpath, dirnames, filenames in os.walk(branch_root):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in ("node_modules", "dist", "build")]
            for fname in filenames:
                if not fname.lower().endswith(EXTS):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    continue
                new_text, count = _swap(text)
                if count and new_text != text:
                    try:
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(new_text)
                        files_changed.append({
                            "path": os.path.relpath(fpath, project_root),
                            "rewrites": count,
                        })
                    except OSError as e:
                        return self._reply(500, {"error": f"write failed for {fname}: {e}"})

        # v3.4.22 — Broadcast the rewritten file paths so the prototype
        # iframe handler refreshes immediately (instead of waiting for the
        # file-watcher's 1–2s polling cycle).
        try:
            project_id = os.path.basename(project_root.rstrip("/"))
            changed_paths = [f["path"] for f in files_changed]
            if changed_paths:
                _broadcast_asset_change(project_id, changed_paths)
        except Exception:
            pass
        return self._reply(200, {
            "ok": True,
            "old_src": old_src,
            "new_src": new_src,
            "files": files_changed,
            "total_rewrites": sum(f["rewrites"] for f in files_changed),
        })

    # POST /__rewrite_element_for_kind?project=<id>
    # Body: { branch, old_src, new_src, new_kind }
    # Like /__rewrite_img_src but ALSO rewrites the HTML ELEMENT TYPE when
    # the new file's kind doesn't match an <img>. Used by the Replace flow
    # on exposed asset cards so the user can swap a raster <img> for a video
    # / 3D scene / lottie animation in one click. Element mapping:
    #
    #   new_kind = "image" | "svg"  → keep <img>, just rewrite the src.
    #   new_kind = "video"          → <video src="…" muted playsInline
    #                                  autoplay loop preload="auto"></video>
    #   new_kind = "html"           → <iframe src="…" sandbox="allow-scripts
    #                                  allow-same-origin" frameborder="0"
    #                                  style="width:100%;height:100%;
    #                                  border:0"></iframe>
    #     (covers shader / 3d / threejs / viz / canvas-gen / motion-gen —
    #      every Pathway-B HTML scene)
    #   new_kind = "lottie"         → <lottie-player src="…" autoplay loop
    #                                  background="transparent"
    #                                  style="width:100%;height:100%">
    #                                </lottie-player>
    #     (when no <script src="…lottie-player…"> exists in the file, the
    #      endpoint also injects one before </head> so the web component
    #      actually registers — silently noop if a player is already loaded)
    #
    # Width / height / class / id / style attributes on the original <img>
    # are preserved on the new element so layout doesn't shift.
    def _rewrite_element_for_kind(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        branch   = (body.get("branch") or "main").strip().lower()
        old_src  = (body.get("old_src")  or "").strip()
        new_src  = (body.get("new_src")  or "").strip()
        new_kind = (body.get("new_kind") or "").strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})
        if not old_src.startswith("source/") or not new_src.startswith("source/"):
            return self._reply(400, {"error": "old_src/new_src must start with source/"})
        ALLOWED_KINDS = ("image", "svg", "video", "html", "lottie")
        if new_kind not in ALLOWED_KINDS:
            return self._reply(400, {"error": f"unsupported new_kind: {new_kind}",
                                      "allowed": list(ALLOWED_KINDS)})
        try:
            branch_root = _safe_join(project_root, "source", branch)
        except Exception as e:
            return self._reply(400, {"error": f"branch path resolution failed: {e}"})
        if not os.path.isdir(branch_root):
            return self._reply(404, {"error": f"branch not found: source/{branch}/"})

        prefix = f"source/{branch}/"
        old_tail = old_src[len(prefix):] if old_src.startswith(prefix) else old_src
        new_tail = new_src[len(prefix):] if new_src.startswith(prefix) else new_src
        old_base = os.path.basename(old_tail)
        new_base = os.path.basename(new_tail)

        # Match an entire <img …> tag whose src ends with the old basename.
        # Used both to extract preserved attributes and to splice the new
        # element in. Same /-boundary safeguard as /__rewrite_img_src.
        img_tag_re = re.compile(
            r'<img\b([^>]*?)\bsrc\s*=\s*["\']'    # 1: attrs BEFORE src
            r'((?:[^"\']*/)?)'                     # 2: optional directory ending in /
            + re.escape(old_base) +
            r'["\']'                               # closing quote of src
            r'([^>]*?)'                            # 3: attrs AFTER src
            r'\s*/?>',                             # closing of the tag (self-closing or not)
            re.IGNORECASE,
        )

        # Pull width / height / class / id / style off the original <img>
        # so the replacement element keeps the same footprint. Anything else
        # is dropped (alt / loading / decoding / etc. don't apply to video /
        # iframe / lottie-player).
        PRESERVE = ("width", "height", "class", "id", "style")
        attr_re = re.compile(
            r'\b(' + "|".join(PRESERVE) + r')\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))',
            re.IGNORECASE,
        )

        def _build_replacement(attrs_before, dir_in_src, attrs_after):
            preserved_pairs = []
            for m in attr_re.finditer(attrs_before + " " + attrs_after):
                name = m.group(1).lower()
                val = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(5))
                preserved_pairs.append((name, val))
            preserved_str = "".join(f' {k}="{v}"' for k, v in preserved_pairs)
            new_url = (dir_in_src or "") + new_base
            if new_kind in ("image", "svg"):
                return f'<img src="{new_url}"{preserved_str}>'
            if new_kind == "video":
                return f'<video src="{new_url}" muted playsinline autoplay loop preload="auto"{preserved_str}></video>'
            if new_kind == "html":
                style_in_preserved = any(k == "style" for k, _ in preserved_pairs)
                fallback_style = '' if style_in_preserved else ' style="width:100%;height:100%;border:0"'
                return f'<iframe src="{new_url}" sandbox="allow-scripts allow-same-origin" frameborder="0"{preserved_str}{fallback_style}></iframe>'
            if new_kind == "lottie":
                style_in_preserved = any(k == "style" for k, _ in preserved_pairs)
                fallback_style = '' if style_in_preserved else ' style="width:100%;height:100%"'
                return (f'<lottie-player src="{new_url}" autoplay loop '
                        f'background="transparent"{preserved_str}{fallback_style}></lottie-player>')
            # Should not reach due to upfront ALLOWED_KINDS guard.
            return f'<img src="{new_url}"{preserved_str}>'

        # Lottie additionally needs the <lottie-player> custom element loader
        # included once per page. We append a marker comment so re-runs don't
        # double-inject. Idempotent.
        LOTTIE_LOADER_MARKER = "<!-- woven:lottie-player-loaded -->"
        LOTTIE_LOADER_MARKER_LEGACY = "<!-- limn:lottie-player-loaded -->"
        LOTTIE_LOADER_BLOCK = (
            '\n  ' + LOTTIE_LOADER_MARKER + '\n'
            '  <script src="https://unpkg.com/@lottiefiles/lottie-player@2.0.8/dist/lottie-player.js" defer></script>\n'
        )

        EXTS = (".html", ".htm", ".jsx", ".tsx", ".js", ".ts")
        files_changed = []

        def _swap(text):
            count = 0
            def repl(m):
                nonlocal count
                count += 1
                return _build_replacement(m.group(1), m.group(2), m.group(3))
            new_text = img_tag_re.sub(repl, text)
            if count == 0:
                return text, 0
            # Inject the lottie loader for lottie kind, once per file.
            if new_kind == "lottie" and LOTTIE_LOADER_MARKER not in new_text and LOTTIE_LOADER_MARKER_LEGACY not in new_text:
                # Insert just before </head>; fall back to before <body if no
                # head closer exists; if neither, prepend at the top.
                if re.search(r'</head\s*>', new_text, re.IGNORECASE):
                    new_text = re.sub(r'</head\s*>', LOTTIE_LOADER_BLOCK + '</head>', new_text, count=1, flags=re.IGNORECASE)
                elif re.search(r'<body\b', new_text, re.IGNORECASE):
                    new_text = re.sub(r'<body\b', LOTTIE_LOADER_BLOCK + '<body', new_text, count=1, flags=re.IGNORECASE)
                else:
                    new_text = LOTTIE_LOADER_BLOCK + new_text
            return new_text, count

        with _history_scope_bracket(project_root, [f"source/{branch}"],
                                     kind="asset-gen",
                                     label=f"Rewrite element ({new_kind}): {old_base} → {new_base}",
                                     source="asset",
                                     extra={"branch": branch, "old": old_src,
                                            "new": new_src, "new_kind": new_kind}):
          for dirpath, dirnames, filenames in os.walk(branch_root):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in ("node_modules", "dist", "build")]
            for fname in filenames:
                if not fname.lower().endswith(EXTS):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    continue
                new_text, count = _swap(text)
                if count and new_text != text:
                    try:
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(new_text)
                        files_changed.append({
                            "path": os.path.relpath(fpath, project_root),
                            "rewrites": count,
                        })
                    except OSError as e:
                        return self._reply(500, {"error": f"write failed for {fname}: {e}"})

        # v3.4.22 — Broadcast both an asset-change (for the rewritten HTML
        # files) and a workflow-change so subscribers can re-fetch and
        # re-render. Without this the rewrite SUCCEEDS server-side but the
        # frontend iframe sometimes shows stale content because the file-
        # watcher's 1–2s polling hadn't yet picked up the writes when the
        # iframe was already trying to reload via the frontend's immediate
        # th:asset-refresh dispatch.
        try:
            project_id = os.path.basename(project_root.rstrip("/"))
            changed_paths = [f["path"] for f in files_changed]
            if changed_paths:
                _broadcast_asset_change(project_id, changed_paths)
        except Exception:
            pass
        return self._reply(200, {
            "ok": True,
            "old_src": old_src,
            "new_src": new_src,
            "new_kind": new_kind,
            "files": files_changed,
            "total_rewrites": sum(f["rewrites"] for f in files_changed),
        })

    # ── Folder management for the agent output picker ────────────────────
    # All three endpoints are project-scoped + path-safe-joined. Used by the
    # folder picker dialog's New / Rename / Delete buttons so the user can
    # build out their output tree without leaving the canvas.

    # POST /__mkdir?project=<id>     body: { path: "source/<branch>/..." }
    # Each path segment must match SLUG_OK so the resulting folder can also
    # serve as a Claude Code /__run cwd slug — the agent's run path derives
    # its spawn cwd from the folder name, and a non-slug name would break
    # the spawn ("invalid branch slug").
    def _mkdir(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        rel = (body.get("path") or "").strip()
        if not rel or not rel.startswith("source/"):
            return self._reply(400, {"error": "path must be project-relative and start with source/"})
        for seg in rel.split("/"):
            if not seg: continue
            if not SLUG_OK.match(seg):
                return self._reply(400, {"error": f"invalid path segment '{seg}': lowercase letters / digits / hyphens / underscores only"})
        try:
            abs_path = _safe_join(project_root, rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if os.path.exists(abs_path):
            return self._reply(409, {"error": "already exists", "path": rel})
        try:
            os.makedirs(abs_path)
        except OSError as e:
            return self._reply(500, {"error": f"mkdir failed: {e}"})
        return self._reply(200, {"ok": True, "path": rel})

    # POST /__rmdir?project=<id>     body: { path: "source/<branch>/..." }
    # Recursive. Refuses to delete the branch root or anything above it.
    def _rmdir(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        rel = (body.get("path") or "").strip()
        if not rel or not rel.startswith("source/"):
            return self._reply(400, {"error": "path must be project-relative and start with source/"})
        # Refuse to delete `source` itself or the canonical `source/main`
        # branch — both are load-bearing. Other top-level folders (e.g.
        # ones the user spawned via the picker for an agent run) are
        # fair game.
        norm = rel.rstrip("/")
        if norm == "source" or norm == "source/main":
            return self._reply(400, {"error": "won't remove " + norm + " — that's load-bearing"})
        try:
            abs_path = _safe_join(project_root, rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isdir(abs_path):
            return self._reply(404, {"error": "not a directory", "path": rel})
        import shutil
        try:
            shutil.rmtree(abs_path)
        except OSError as e:
            return self._reply(500, {"error": f"rmtree failed: {e}"})
        return self._reply(200, {"ok": True, "path": rel})

    # POST /__rename_dir?project=<id> body: { from: "source/<...>", to: "source/<...>" }
    def _rename_dir(self, qs):
        try:
            project_root = resolve_project_root(qs, require_explicit=True)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body(max_bytes=4 * 1024)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        src_rel = (body.get("from") or "").strip()
        dst_rel = (body.get("to")   or "").strip()
        if not src_rel.startswith("source/") or not dst_rel.startswith("source/"):
            return self._reply(400, {"error": "from/to must be project-relative under source/"})
        if src_rel == dst_rel:
            return self._reply(400, {"error": "from and to are the same path"})
        try:
            src_abs = _safe_join(project_root, src_rel)
            dst_abs = _safe_join(project_root, dst_rel)
        except Exception as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        if not os.path.isdir(src_abs):
            return self._reply(404, {"error": "from not a directory", "path": src_rel})
        if os.path.exists(dst_abs):
            return self._reply(409, {"error": "to already exists", "path": dst_rel})
        try:
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            os.rename(src_abs, dst_abs)
        except OSError as e:
            return self._reply(500, {"error": f"rename failed: {e}"})
        return self._reply(200, {"ok": True, "from": src_rel, "to": dst_rel})

    def _local_status(self, qs):
        """GET /__local_status?package=rembg → {installed, version?}.
        Probes via a subprocess `python -c "import rembg"` so we read the
        live sys.path that pip install --user would have updated."""
        pkg = (_qs_get(qs, "package") or "").strip()
        if pkg not in self._LOCAL_PACKAGES:
            return self._reply(400, {"error": f"unknown local package: {pkg}", "known": list(self._LOCAL_PACKAGES.keys())})
        import_name = self._LOCAL_PACKAGES[pkg]["import"]
        try:
            r = subprocess.run(
                [sys.executable, "-c", f"import {import_name}; import sys; print(getattr({import_name}, '__version__', 'unknown'))"],
                capture_output=True, timeout=15, check=False,
            )
            installed = (r.returncode == 0)
            version = (r.stdout.decode("utf-8", "replace").strip() if installed else None)
        except Exception as e:
            return self._reply(500, {"error": f"probe failed: {e}"})
        return self._reply(200, {"package": pkg, "installed": installed, "version": version})

    def _local_install(self):
        """POST /__local_install body: { package: "rembg" }.
        Runs `python -m pip install --user <pkgs>` synchronously. Can take
        1-3 minutes for rembg (downloads onnxruntime wheels + deps).
        Returns final status + last 4 KB of pip output."""
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 64 * 1024:
            return self._reply(400, {"error": "empty or oversized body"})
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        pkg = (body.get("package") or "").strip()
        if pkg not in self._LOCAL_PACKAGES:
            return self._reply(400, {"error": f"unknown local package: {pkg}", "known": list(self._LOCAL_PACKAGES.keys())})
        packages = self._LOCAL_PACKAGES[pkg]["packages"]
        # --user installs into ~/Library/Python/.../site-packages on macOS
        # without touching the system Python. `--quiet` keeps the output
        # small enough to ship back in the JSON reply.
        #
        # --break-system-packages — required for Homebrew-installed Python
        # ≥3.12 which ships with a PEP-668 EXTERNALLY-MANAGED marker that
        # otherwise blocks pip entirely. Combined with --user the flag is
        # safe: installs only land in the per-user site dir, never touching
        # the brew-managed prefix. (PEP 668 itself recommends this exact
        # combo as the escape hatch.) No-op on Pythons without the marker.
        cmd = [sys.executable, "-m", "pip", "install",
               "--user", "--break-system-packages", "--quiet", *packages]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=600, check=False)
        except subprocess.TimeoutExpired:
            return self._reply(504, {"error": "pip install timed out after 10 minutes"})
        except Exception as e:
            return self._reply(500, {"error": f"pip spawn failed: {e}"})
        stdout = (r.stdout or b"").decode("utf-8", "replace")
        stderr = (r.stderr or b"").decode("utf-8", "replace")
        # Verify post-install.
        import_name = self._LOCAL_PACKAGES[pkg]["import"]
        verify = subprocess.run(
            [sys.executable, "-c", f"import {import_name}"],
            capture_output=True, timeout=15, check=False,
        )
        installed = (verify.returncode == 0)
        return self._reply(200 if installed else 502, {
            "ok": installed,
            "package": pkg,
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
            "verify_returncode": verify.returncode,
            "verify_stderr": (verify.stderr or b"").decode("utf-8", "replace")[-2000:],
        })

    # ── Phase 4c — library: project asset listing + delete ─────────────
    # Surfaces every generated file under source/<branch>/{images,svg,video,
    # models,shaders,viz,audio}/ as a draggable library item. Delete removes
    # the file from disk (destructive — the user is in control of their own
    # source tree). Newest first.
    _LIB_ASSET_SUBDIRS = ("images", "svg", "video", "models", "shaders", "viz", "audio")
    _LIB_KIND_FOR_DIR  = {
        "images": "image", "svg": "svg", "video": "video", "models": "3d",
        "shaders": "shader", "viz": "viz", "audio": "audio",
    }
    # v3.4.16 — Extension → asset kind. Wins over the folder-derived default
    # in `_LIB_KIND_FOR_DIR`. Background: skill outputs (shader / threejs /
    # viz / lottie / svg-gen / video-gen / motion-gen) all land in
    # source/<branch>/images/ regardless of file type. The folder default
    # of "image" tagged every one of those as kind:"image", so the library's
    # drag-payload was {assetKind:"image", path:"…/threejs-xxx.html"} →
    # dropped onto the canvas it spawned an <img src=".html"> that rendered
    # broken. AND the same files appeared again in /__source_htmls →
    # duplicate library entries. Classifying by extension makes the
    # library + drag-payload match the file's real kind.
    _LIB_EXT_KIND = {
        # raster
        "png": "image", "jpg": "image", "jpeg": "image", "webp": "image", "gif": "image", "avif": "image",
        # vector
        "svg": "svg",
        # video
        "mp4": "video", "webm": "video", "mov": "video", "m4v": "video", "ogv": "video",
        # audio
        "mp3": "audio", "wav": "audio", "ogg": "audio", "flac": "audio", "aac": "audio", "m4a": "audio",
        # 3d / scene
        "glb": "3d", "gltf": "3d", "obj": "3d", "fbx": "3d", "usdz": "3d",
        # html-driven scenes (shader / threejs / viz / canvas-gen / motion-gen)
        "html": "html", "htm": "html",
        # lottie JSON
        "json": "lottie",
    }

    def _assets_list(self, qs):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        items = []
        src_root = os.path.join(project_root, "source")
        if os.path.isdir(src_root):
            for branch in sorted(os.listdir(src_root)):
                branch_dir = os.path.join(src_root, branch)
                if not os.path.isdir(branch_dir): continue
                for sub in self._LIB_ASSET_SUBDIRS:
                    sub_dir = os.path.join(branch_dir, sub)
                    if not os.path.isdir(sub_dir): continue
                    for fname in sorted(os.listdir(sub_dir)):
                        if fname.startswith("."): continue
                        fpath = os.path.join(sub_dir, fname)
                        if not os.path.isfile(fpath): continue
                        try: st = os.stat(fpath)
                        except Exception: continue
                        rel = os.path.relpath(fpath, project_root).replace("\\", "/")
                        # Prefer the file extension when it maps to a known
                        # kind — that's the truth. Fall back to the folder
                        # default only when the extension is unrecognised.
                        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                        kind = self._LIB_EXT_KIND.get(ext) or self._LIB_KIND_FOR_DIR.get(sub, "image")
                        items.append({
                            "path":   rel,
                            "name":   fname,
                            "kind":   kind,
                            "branch": branch,
                            "size":   st.st_size,
                            "mtime":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
                        })
        items.sort(key=lambda x: x["mtime"], reverse=True)
        return self._reply(200, {"items": items})

    def _asset_delete(self, qs):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(400, {"error": "empty or oversized body"})
        try: body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e: return self._reply(400, {"error": "invalid JSON", "detail": str(e)})
        rel = (body.get("path") or "").strip()
        if not rel or rel.startswith("/") or ".." in rel.split("/") or not rel.startswith("source/"):
            return self._reply(400, {"error": "invalid path (must be source/<branch>/<subdir>/<file>)"})
        try: abs_path = _safe_join(project_root, rel)
        except Exception as e: return self._reply(400, {"error": str(e)})
        if not os.path.isfile(abs_path):
            return self._reply(404, {"error": "file not found"})
        try: os.remove(abs_path)
        except Exception as e: return self._reply(500, {"error": f"could not delete: {e}"})
        return self._reply(200, {"ok": True, "path": rel})

    # ── Phase 4c — library: saved prompts (markdown "skills") ──────────
    # Stored at <project>/workflow/prompts/<slug>.md. Filename is the slug;
    # first markdown H1 line is the human title. Used by the prompt-node
    # "Save" button and surfaced as draggable items in the Library →
    # Prompts section.
    _PROMPT_SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")

    def _prompts_dir(self, project_root):
        return os.path.join(project_root, "workflow", "prompts")

    def _prompts_list(self, qs):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        d = self._prompts_dir(project_root)
        items = []
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                if not fname.lower().endswith(".md"): continue
                slug = fname[:-3]
                if not self._PROMPT_SLUG_OK.match(slug): continue
                fpath = os.path.join(d, fname)
                try: st = os.stat(fpath)
                except Exception: continue
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        body_text = f.read()
                except Exception:
                    body_text = ""
                first_line = (body_text.split("\n", 1)[0] if body_text else "").strip()
                title = first_line.lstrip("# ").strip() or slug
                # Strip the H1 title line out of body for the preview; what
                # the user typed is everything after the title + blank line.
                if first_line.startswith("# "):
                    rest = body_text.split("\n", 2)
                    text = rest[2] if len(rest) >= 3 else ""
                    text = text.lstrip("\n")
                else:
                    text = body_text
                items.append({
                    "slug": slug, "title": title, "body": text,
                    "size": st.st_size,
                    "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
                })
        items.sort(key=lambda x: x["mtime"], reverse=True)
        return self._reply(200, {"items": items})

    def _prompt_get(self, qs, slug):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        if not self._PROMPT_SLUG_OK.match(slug):
            return self._reply(400, {"error": "invalid slug"})
        fpath = os.path.join(self._prompts_dir(project_root), slug + ".md")
        if not os.path.isfile(fpath):
            return self._reply(404, {"error": "not found"})
        try:
            with open(fpath, "r", encoding="utf-8") as f: body = f.read()
        except Exception as e: return self._reply(500, {"error": f"read failed: {e}"})
        first_line = (body.split("\n", 1)[0] if body else "").strip()
        title = first_line.lstrip("# ").strip() or slug
        if first_line.startswith("# "):
            rest = body.split("\n", 2)
            text = rest[2] if len(rest) >= 3 else ""
            text = text.lstrip("\n")
        else:
            text = body
        return self._reply(200, {"slug": slug, "title": title, "body": text, "raw": body})

    def _prompt_save(self, qs):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload too large"})
        try: body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e: return self._reply(400, {"error": "invalid JSON body", "detail": str(e)})
        slug = (body.get("slug") or "").strip().lower()
        if not self._PROMPT_SLUG_OK.match(slug):
            return self._reply(400, {"error": "invalid slug (lowercase letters/digits/hyphens, 1-60 chars, starting with letter or digit)"})
        title = (body.get("title") or slug).strip()
        text  = body.get("body") if isinstance(body.get("body"), str) else (body.get("text") or "")
        if not isinstance(text, str): text = str(text)
        d = self._prompts_dir(project_root)
        try: os.makedirs(d, exist_ok=True)
        except Exception as e: return self._reply(500, {"error": f"mkdir failed: {e}"})
        fpath = os.path.join(d, slug + ".md")
        md = f"# {title}\n\n{text}\n"
        try:
            with open(fpath, "w", encoding="utf-8") as f: f.write(md)
        except Exception as e: return self._reply(500, {"error": f"write failed: {e}"})
        return self._reply(200, {"ok": True, "slug": slug, "title": title})

    def _prompt_delete(self, qs, slug):
        try: project_root = resolve_project_root(qs)
        except ValueError as e: return self._reply(400, {"error": str(e)})
        if not self._PROMPT_SLUG_OK.match(slug):
            return self._reply(400, {"error": "invalid slug"})
        fpath = os.path.join(self._prompts_dir(project_root), slug + ".md")
        if not os.path.isfile(fpath):
            return self._reply(404, {"error": "not found"})
        try: os.remove(fpath)
        except Exception as e: return self._reply(500, {"error": f"delete failed: {e}"})
        return self._reply(200, {"ok": True, "slug": slug})

    # ── POST /__save?name=<file> ─────────────────────────────────────────
    def _save(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        name = (qs.get("name") or [""])[0].strip()
        if not name or not NAME_OK.match(name):
            return self._reply(400, {"error": "invalid name", "name": name})
        if name not in ALLOWED_NAMES:
            return self._reply(403, {"error": "name not in allowlist", "allowed": sorted(ALLOWED_NAMES)})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES:
            return self._reply(413, {"error": "payload missing or too large", "bytes": length, "max": MAX_BYTES})
        body = self.rfile.read(length)
        dest = _safe_join(project_root, name)
        with _history_bracket(project_root, [name],
                              kind="ui-edit",
                              label=f"Save {name}",
                              source="editor"):
            with open(dest, "wb") as f:
                f.write(body)
        return self._reply(200, {"ok": True, "path": os.path.relpath(dest, project_root), "bytes": len(body)})

    # ── DEPRECATED in v3.1: project-level branches removed (see
    # docs/features/deprecate-project-branches.md). The handlers below are
    # left as 410 Gone stubs so any stale client gets a clear error rather
    # than a hang. Asset-versioning's sibling-node branching (Phase 5) is
    # the replacement for "explore alternatives without losing the line."
    def _branch_create(self, qs):
        return self._reply(410, {
            "error": "branch endpoints removed in v3.1",
            "hint": "Project branches deprecated. Use asset-node sibling branching from the version picker on a workflow asset card.",
        })
    def _branch_promote(self, qs):
        return self._reply(410, {"error": "branch endpoints removed in v3.1"})
    def _frame_promote(self, qs):
        return self._reply(410, {"error": "branch endpoints removed in v3.1"})


    # ── Liveness ─────────────────────────────────────────────────────────

    def _healthz(self):
        """v2.50 — Dedicated daemon-liveness probe. Touches NO locks
        (workflow / runs / history) and reads NO files. Returns in <5ms
        regardless of load. The frontend uses this as its canonical
        "daemon up" signal so application-traffic slowness no longer
        false-positives as "daemon down". See WORKFLOW_TRUTHFULNESS_PLAN.md
        Deliverable 1 / Guardrail G1."""
        return self._reply(200, {
            "ok":   True,
            "ts":   time.time(),
            "pid":  os.getpid(),
        })

    # ── /__kinds/registry — D3 source of truth ────────────────────────────

    def _kinds_registry(self):
        """v2.50 — D3: serve the per-kind registry as JSON. Frontend
        renderers, validators, and orchestrator skills all read this.
        Single source of truth (Principle 1)."""
        try:
            from kinds.registry import to_jsonable
            return self._reply(200, to_jsonable())
        except Exception as e:
            return self._reply(500, {"error": f"registry load failed: {e}"})

    # ── /__kinds/reconcile — D5 drift scan ────────────────────────────────

    def _kinds_reconcile(self, qs):
        """v2.50 — D5: walk the project and return drift list + lineage.
        See kinds/reconcile.py. Auto-heal class items get applied when the
        client posts to /__kinds/reconcile/heal (TODO: that endpoint is
        a future enhancement; today the user can Heal one at a time)."""
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            from kinds.reconcile import reconcile
            return self._reply(200, reconcile(project_root))
        except Exception as e:
            return self._reply(500, {"error": f"reconcile failed: {e}"})

    def _capabilities(self):
        """v2.50 — canonical 'what does this app support' catalog. Aggregates
        image-gen providers (from media-models.js), subagent drawers (from
        .claude/agents/*.md), HTTP endpoints, and node kinds (from
        kinds/registry.py). Returned as JSON; also baked into every spawn's
        system preamble so agents never have to guess what's integrated.

        Fixes the 'user asks about Quiver AI, agent says we don't have it'
        class of bug — the catalog is authoritative."""
        try:
            from kinds.capabilities import get_capabilities
            return self._reply(200, get_capabilities())
        except Exception as e:
            return self._reply(500, {"error": f"capabilities load failed: {e}"})

    # ── Orchestrator registry routes (v3.3) ──────────────────────────────────
    #
    # GET  /__orchestrators?project=<id>             — list every orchestrator manifest
    #                                              + per-orchestrator enabled state
    #                                              for this project.
    # POST /__orchestrators/disable?project=<id>     — body {orchestratorId, enabled}
    #                                              flips one orchestrator's toggle.
    #
    # Orchestrators are auto-discovered from `.claude/agents/<name>.manifest.json`.
    # Per-project disable state persists at `<projectRoot>/.orchestrators-disabled.json`.
    # The capabilities preamble (capabilities.capabilities_preamble) reads the
    # enabled set and omits hard-rule blocks for disabled orchestrators, so agents
    # spawned in that project never see "dispatch <X>-orchestrator FIRST" cues for
    # off orchestrators.

    def _orchestrators_disable_target(self, qs):
        """Resolve where to read/write the orchestrator disable state.

        Priority:
          1. `?project=<id>` present → that project's root.
          2. WORKSPACE_DIR set (no project) → workspace dir (landing-page case;
             toggle affects every project in the workspace).
          3. single-project install → install root (legacy).

        Returns a path string or raises ValueError if no target can be determined."""
        try:
            return resolve_project_root(qs)
        except ValueError:
            if WORKSPACE_DIR:
                return WORKSPACE_DIR
            return os.getcwd()

    def _orchestrators_registry(self, qs):
        """GET /__orchestrators?project=<id> — return aggregated manifests + state.

        When called without a ?project= param, falls back to the workspace
        disable state (landing-page case). Toggles made there affect every
        project in the workspace until per-project overrides land."""
        target = self._orchestrators_disable_target(qs)
        try:
            import orchestrators as _pl
            reg = _pl.get_registry(target)
            reg["scope"]      = "project" if "?project=" in qs.__class__.__name__ else (
                                  "workspace" if target == WORKSPACE_DIR else "project")
            reg["targetRoot"] = target
            return self._reply(200, reg)
        except Exception as e:
            return self._reply(500, {"error": f"orchestrators load failed: {e}"})

    def _orchestrators_disable(self, qs):
        """POST /__orchestrators/disable?project=<id>
        Body: {"orchestratorId": "<id>", "enabled": <bool>}
        Returns the updated disable list.

        Without ?project=, writes to the workspace disable file (landing-page
        scope) so the toggle affects every project until per-project overrides
        land. See `_orchestrators_disable_target`."""
        try:
            project_root = self._orchestrators_disable_target(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        try:
            body = self._read_json_body() or {}
        except Exception as e:
            return self._reply(400, {"error": f"invalid JSON body: {e}"})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "body must be an object"})
        orchestrator_id = body.get("orchestratorId")
        enabled    = body.get("enabled")
        if not isinstance(orchestrator_id, str) or not orchestrator_id:
            return self._reply(400, {"error": "orchestratorId required (string)"})
        if not isinstance(enabled, bool):
            return self._reply(400, {"error": "enabled required (boolean)"})
        try:
            import orchestrators as _pl
            new_disabled = _pl.set_orchestrator_enabled(project_root, orchestrator_id, enabled)
            return self._reply(200, {
                "ok":          True,
                "orchestratorId":   orchestrator_id,
                "enabled":     enabled,
                "disabledIds": new_disabled,
            })
        except Exception as e:
            return self._reply(500, {"error": f"orchestrator toggle failed: {e}"})

    # ── Harness-local skills routes ──────────────────────────────────────
    #
    # GET  /__cc_skills           — list every SKILL.md installed in the
    #                                harness-local skills dir. THIS HARNESS
    #                                DELIBERATELY DOES NOT READ THE USER'S
    #                                GLOBAL ~/.claude/ INSTALL — agents
    #                                spawned by the harness do not get
    #                                access to the user's Claude Code
    #                                skill library, so they have to be
    #                                added to the harness explicitly here.
    # POST /__cc_skills/upload    — multipart upload. Each part is either a
    #                                SKILL.md file (installed verbatim) or a
    #                                .zip whose first top-level dir becomes
    #                                the skill slug. Lands under the
    #                                harness skills dir.
    # POST /__cc_skills/delete    — body {"slug": "<name>"} removes
    #                                <skills_dir>/<slug>/.
    #
    # Storage location resolution (first match wins):
    #   1. WORKSPACE_DIR is set        → <WORKSPACE_DIR>/.harness-skills/
    #   2. otherwise                   → <INSTALL_ROOT>/.harness-skills/
    # The route name (/__cc_skills) is kept for backwards compatibility
    # with the frontend; the prior implementation walked the global
    # ~/.claude/ tree and was replaced when the harness pivoted to a
    # closed-skill model.

    def _cc_skills_root_user(self):
        base = WORKSPACE_DIR if WORKSPACE_DIR else INSTALL_ROOT
        return os.path.join(base, ".harness-skills")

    def _parse_skill_md_frontmatter(self, path):
        """Return {name, description, argument_hint} from a SKILL.md's YAML
        frontmatter. Tolerates missing fields; returns None if the file
        isn't readable or has no frontmatter."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                head = f.read(8192)
        except OSError:
            return None
        if not head.startswith("---"):
            return None
        end = head.find("\n---", 3)
        if end < 0:
            return None
        block = head[3:end]
        meta = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            k = k.strip().lower()
            v = v.strip().strip('"').strip("'")
            if k in ("name", "description", "argument-hint"):
                meta[k.replace("-", "_")] = v
        return meta or None

    def _cc_skills_list(self):
        """Walk the harness skills dir and emit a flat list. Each entry:
            {slug, name, description, source: "user", path, invocation}

        Only the harness-local dir is scanned — the user's global
        ~/.claude/ install is deliberately NOT read. Agents spawned by the
        harness don't get access to the user's global Claude Code skill
        library, so a skill the agent should be able to invoke has to be
        added here explicitly."""
        out = []
        user_root = self._cc_skills_root_user()
        if os.path.isdir(user_root):
            for slug in sorted(os.listdir(user_root)):
                sk_dir = os.path.join(user_root, slug)
                if not os.path.isdir(sk_dir):
                    continue
                md = os.path.join(sk_dir, "SKILL.md")
                if not os.path.isfile(md):
                    continue
                meta = self._parse_skill_md_frontmatter(md) or {}
                name = meta.get("name") or slug
                # Path shown to the user — relative to workspace if applicable,
                # else absolute (still useful for "where did this land?").
                show_path = md
                if WORKSPACE_DIR and md.startswith(WORKSPACE_DIR):
                    show_path = "<workspace>" + md[len(WORKSPACE_DIR):]
                out.append({
                    "slug":        slug,
                    "name":        name,
                    "description": meta.get("description", ""),
                    "source":      "user",
                    "plugin":      None,
                    "path":        show_path,
                    "invocation":  "/" + slug,
                })
        return self._reply(200, {"count": len(out), "skills": out, "root": user_root})

    def _cc_skills_upload(self):
        """POST /__cc_skills/upload — multipart body. Each part is either a
        SKILL.md (installed as <harness_skills>/<slug>/SKILL.md) or a .zip
        whose first directory becomes the skill slug.

        For raw SKILL.md uploads, the slug is derived from the frontmatter
        `name:` if present, else the upload filename's stem.

        Refuses uploads outside the harness skills root (path-traversal
        guard) — the harness deliberately never writes into the user's
        global ~/.claude/ install."""
        ctype = self.headers.get("Content-Type", "")
        if not ctype.lower().startswith("multipart/form-data"):
            return self._reply(400, {"error": "expected multipart/form-data body"})
        # Reuse the daemon's hand-rolled multipart parser (cgi is gone in
        # Python 3.13 and FieldStorage was the only stdlib option).
        m = re.search(r'boundary\s*=\s*"?([^";]+)"?', ctype)
        if not m:
            return self._reply(400, {"error": "missing multipart boundary"})
        boundary = m.group(1).encode("latin-1", errors="replace")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return self._reply(400, {"error": "missing or zero Content-Length"})
        body = self.rfile.read(length)
        try:
            parts = self._upload_parse_multipart(body, boundary)
        except Exception as e:
            return self._reply(400, {"error": f"multipart parse failed: {e}"})

        user_root = self._cc_skills_root_user()
        os.makedirs(user_root, exist_ok=True)

        installed = []
        errors    = []

        def safe_slug(s):
            s = re.sub(r"[^A-Za-z0-9_.-]", "-", s).strip("-").lower()
            return s[:80] or "skill"

        for headers, data in parts:
            cd = headers.get("content-disposition", "")
            raw_name = self._upload_extract_filename(cd)
            if not raw_name:
                # form-data field without filename — ignore
                continue
            lower = raw_name.lower()
            if lower.endswith(".md"):
                stem = os.path.splitext(os.path.basename(raw_name))[0]
                # Try to harvest slug from frontmatter `name:` if present
                head = data[:8192].decode("utf-8", errors="replace")
                slug = stem
                if head.startswith("---"):
                    end = head.find("\n---", 3)
                    if end >= 0:
                        for line in head[3:end].splitlines():
                            ll = line.strip().lower()
                            if ll.startswith("name:"):
                                cand = line.split(":", 1)[1].strip().strip('"').strip("'")
                                if cand:
                                    slug = cand
                                    break
                slug = safe_slug(slug)
                out_dir = os.path.join(user_root, slug)
                # Path-traversal guard
                if os.path.commonpath([os.path.abspath(out_dir), os.path.abspath(user_root)]) != os.path.abspath(user_root):
                    errors.append({"name": raw_name, "reason": "path traversal"})
                    continue
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, "SKILL.md"), "wb") as f:
                    f.write(data)
                installed.append({"slug": slug, "kind": "md"})

            elif lower.endswith(".zip"):
                import io, zipfile
                try:
                    zf = zipfile.ZipFile(io.BytesIO(data))
                except zipfile.BadZipFile as e:
                    errors.append({"name": raw_name, "reason": f"bad zip: {e}"})
                    continue
                # Slug = filename stem; if the zip has a single top-level
                # dir, prefer that.
                stem = os.path.splitext(os.path.basename(raw_name))[0]
                names = zf.namelist()
                # Top-level dirs (first segment of every entry path)
                tops = set()
                for n in names:
                    n2 = n.lstrip("/").split("/", 1)[0]
                    if n2:
                        tops.add(n2)
                if len(tops) == 1:
                    stem = next(iter(tops))
                slug = safe_slug(stem)
                out_dir = os.path.join(user_root, slug)
                if os.path.commonpath([os.path.abspath(out_dir), os.path.abspath(user_root)]) != os.path.abspath(user_root):
                    errors.append({"name": raw_name, "reason": "path traversal"})
                    continue
                os.makedirs(out_dir, exist_ok=True)
                bad = False
                for n in names:
                    # Strip the leading top-level dir if every entry shares one
                    rel = n
                    if len(tops) == 1:
                        top = next(iter(tops))
                        if rel.startswith(top + "/"):
                            rel = rel[len(top) + 1:]
                        elif rel == top:
                            continue
                    if not rel:
                        continue
                    if rel.endswith("/"):
                        os.makedirs(os.path.join(out_dir, rel), exist_ok=True)
                        continue
                    # Guard against zip-slip
                    dest = os.path.normpath(os.path.join(out_dir, rel))
                    if os.path.commonpath([os.path.abspath(dest), os.path.abspath(out_dir)]) != os.path.abspath(out_dir):
                        bad = True
                        break
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(zf.read(n))
                if bad:
                    errors.append({"name": raw_name, "reason": "zip slip"})
                    continue
                # Require a SKILL.md to have landed
                if not os.path.isfile(os.path.join(out_dir, "SKILL.md")):
                    errors.append({"name": raw_name, "reason": "no SKILL.md in archive"})
                    continue
                installed.append({"slug": slug, "kind": "zip"})
            else:
                errors.append({"name": raw_name, "reason": "unsupported file type (.md or .zip)"})

        if not installed and errors:
            return self._reply(400, {"error": "no skill installed", "errors": errors})
        return self._reply(200, {
            "ok":        True,
            "installed": len(installed),
            "items":     installed,
            "errors":    errors,
        })

    def _cc_skills_delete(self):
        """POST /__cc_skills/delete — body {"slug": "<name>"}.
        Removes <harness_skills>/<slug>/ recursively. Refuses to touch
        any path outside that root."""
        try:
            body = self._read_json_body() or {}
        except Exception as e:
            return self._reply(400, {"error": f"invalid JSON body: {e}"})
        if not isinstance(body, dict):
            return self._reply(400, {"error": "body must be an object"})
        slug = body.get("slug")
        if not isinstance(slug, str) or not slug:
            return self._reply(400, {"error": "slug required (string)"})
        # Validate slug: filesystem-safe, no traversal
        if not re.match(r"^[A-Za-z0-9_.-]{1,80}$", slug):
            return self._reply(400, {"error": "invalid slug shape"})
        user_root = self._cc_skills_root_user()
        target = os.path.join(user_root, slug)
        # Strict containment check
        if os.path.commonpath([os.path.abspath(target), os.path.abspath(user_root)]) != os.path.abspath(user_root):
            return self._reply(400, {"error": "path outside skills root"})
        if not os.path.isdir(target):
            return self._reply(404, {"error": "skill not found"})
        try:
            import shutil
            shutil.rmtree(target)
        except OSError as e:
            return self._reply(500, {"error": f"delete failed: {e}"})
        return self._reply(200, {"ok": True, "slug": slug})

    # ── Workspace routes (Phase 6) ───────────────────────────────────────

    def _workspace_info(self):
        """Tells the UI which mode the daemon is in. Lets <ProjectPicker>
        hide itself when there's only one project (legacy single-repo install)
        and surface itself in workspace mode."""
        if WORKSPACE_DIR:
            return self._reply(200, {
                "mode": "workspace",
                "workspaceDir": WORKSPACE_DIR,
                "installRoot": INSTALL_ROOT,
                "defaultProjectId": _first_project_id(),
            })
        return self._reply(200, {
            "mode": "single",
            "workspaceDir": None,
            "installRoot": INSTALL_ROOT,
            "defaultProjectId": "default",
        })

    def _projects_list(self):
        """Enumerate every project the workspace knows about. In single-
        project mode returns one virtual project with id='default'."""
        return self._reply(200, {"projects": _list_projects()})

    # POST /__projects/new  body: { id, label? }
    # Scaffolds <WORKSPACE_DIR>/projects/<id>/{source/main/, editor/data.js}.
    # Only valid in workspace mode. Post-v3.5 onboarding cut — no scope,
    # no intent, no reference, no PRD upload, no DS ref, no .onboarding-pending
    # marker, no workflow.json scaffold. The user drops into an empty editor
    # with a blank canvas; they build by typing in chat or dropping nodes.
    def _project_create(self, qs):
        if not WORKSPACE_DIR:
            return self._reply(400, {
                "error": "workspace mode not enabled",
                "hint": "set TH_WORKSPACE_DIR=<path> on the daemon to scaffold projects",
            })
        body = self._read_json_body()
        proj_id = (body.get("id") or "").strip()
        if not proj_id or not PROJECT_ID_OK.match(proj_id):
            return self._reply(400, {"error": "invalid project id (alphanumeric + ._- only, 1..64 chars)", "id": proj_id})
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        dest = _safe_join(PROJECTS_DIR, proj_id)
        # Also refuse if a legacy project with the same id sits at the root.
        legacy = os.path.join(WORKSPACE_DIR, proj_id)
        if os.path.exists(dest) or (os.path.isdir(legacy) and os.path.isdir(os.path.join(legacy, "source"))):
            return self._reply(409, {"error": "project already exists", "id": proj_id})
        label = (body.get("label") or proj_id).strip()
        try:
            os.makedirs(os.path.join(dest, "source", "main"), exist_ok=False)
            os.makedirs(os.path.join(dest, "editor"), exist_ok=True)
            main_data = (
                "// Auto-generated by /__projects/new — minimal project seed.\n"
                "window.EDITOR_DATA = {\n"
                f'  meta: {{ project: {json.dumps(label)}, sourceRoot: "../source/main/", sourceEntry: "index.html" }},\n'
                "  frames: [], lanes: [], arrows: [], entities: [], primitives: [], links: [],\n"
                "};\n"
            )
            with open(os.path.join(dest, "editor", "data.js"), "w", encoding="utf-8") as f:
                f.write(main_data)
        except OSError as e:
            return self._reply(500, {"error": f"scaffold failed: {type(e).__name__}: {e}"})

        # Persist the label in workspace.json so /__projects reports it back
        # (auto-discovery would otherwise fall back to id == label).
        ws_json = os.path.join(WORKSPACE_DIR, "workspace.json")
        try:
            cfg = {}
            if os.path.isfile(ws_json):
                with open(ws_json, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
            entries = cfg.setdefault("projects", [])
            if not any((e.get("id") or "").strip() == proj_id for e in entries):
                entries.append({"id": proj_id, "label": label})
            with open(ws_json, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass  # auto-discovery still picks the project up via folder scan
        return self._reply(200, {"ok": True, "id": proj_id, "label": label, "path": dest})

    # POST /__projects/rename  body: { id, label }
    # Updates the project's display label by writing workspace.json. The on-disk
    # folder name (the `id`) is immutable — renaming that would break running
    # agents, branch URLs, and run history. Workspace-mode only.
    def _project_rename(self, qs):
        if not WORKSPACE_DIR:
            return self._reply(400, {"error": "workspace mode not enabled"})
        body = self._read_json_body()
        proj_id = (body.get("id") or "").strip()
        new_label = (body.get("label") or "").strip()
        if not proj_id or not PROJECT_ID_OK.match(proj_id):
            return self._reply(400, {"error": "invalid project id", "id": proj_id})
        if not new_label:
            return self._reply(400, {"error": "label required"})
        # Look in projects/<id>/ first, then root-level fallback for legacy.
        dest = None
        for c in _project_dir_candidates(proj_id):
            if os.path.isdir(c): dest = c; break
        if not dest:
            return self._reply(404, {"error": "no such project", "id": proj_id})
        ws_json = os.path.join(WORKSPACE_DIR, "workspace.json")
        try:
            cfg = {}
            if os.path.isfile(ws_json):
                with open(ws_json, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
            entries = cfg.setdefault("projects", [])
            found = False
            for e in entries:
                if (e.get("id") or "").strip() == proj_id:
                    e["label"] = new_label
                    found = True
                    break
            if not found:
                entries.append({"id": proj_id, "label": new_label})
            with open(ws_json, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            return self._reply(500, {"error": f"workspace.json write failed: {type(e).__name__}: {e}"})
        return self._reply(200, {"ok": True, "id": proj_id, "label": new_label})

    # POST /__projects/delete  body: { id }
    # Moves <WORKSPACE_DIR>/projects/<id>/ to projects/.trash/<id>-<timestamp>/
    # — recoverable, no hard-rm. Falls back to <WORKSPACE_DIR>/<id>/ for any
    # legacy project that hasn't been migrated into projects/ yet. Also
    # removes the entry from workspace.json if present. Workspace-mode only.
    def _project_delete(self, qs):
        if not WORKSPACE_DIR:
            return self._reply(400, {"error": "workspace mode not enabled"})
        body = self._read_json_body()
        proj_id = (body.get("id") or "").strip()
        if not proj_id or not PROJECT_ID_OK.match(proj_id):
            return self._reply(400, {"error": "invalid project id", "id": proj_id})
        dest = None
        for c in _project_dir_candidates(proj_id):
            if os.path.isdir(c): dest = c; break
        if not dest:
            return self._reply(404, {"error": "no such project", "id": proj_id})
        # Don't let the user delete the install dir out from under themselves.
        try:
            if os.path.samefile(dest, INSTALL_ROOT):
                return self._reply(400, {
                    "error": "refusing to delete the install root",
                    "hint": "this project hosts the editor binary; move the editor elsewhere first",
                })
        except OSError:
            pass
        # Refuse if a run is currently scoped to this project.
        try:
            with RUNS_LOCK:
                active = [s for s in RUNS.values() if s.project_id == proj_id and not s.done]
            if active:
                return self._reply(409, {
                    "error": "project has active agent runs",
                    "runIds": [s.run_id for s in active],
                })
        except NameError:
            pass  # RUNS isn't defined yet at module import — only at request time
        # Trash sits next to the active projects (projects/.trash/) so deleting
        # doesn't clutter the workspace root. Legacy installs may still have
        # a .trash at the root; we prefer the new location for new deletions.
        trash_dir = os.path.join(PROJECTS_DIR, ".trash") if PROJECTS_DIR else os.path.join(WORKSPACE_DIR, ".trash")
        os.makedirs(trash_dir, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        target = os.path.join(trash_dir, f"{proj_id}-{stamp}")
        try:
            shutil.move(dest, target)
        except OSError as e:
            return self._reply(500, {"error": f"move failed: {type(e).__name__}: {e}"})
        # Drop from workspace.json if listed.
        ws_json = os.path.join(WORKSPACE_DIR, "workspace.json")
        if os.path.isfile(ws_json):
            try:
                with open(ws_json, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
                entries = cfg.get("projects") or []
                cfg["projects"] = [e for e in entries if (e.get("id") or "").strip() != proj_id]
                with open(ws_json, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
            except Exception:
                pass
        return self._reply(200, {"ok": True, "id": proj_id, "trashedTo": target})

    # ── Agent daemon routes (Phase 1) ─────────────────────────────────────

    def _agents_list(self):
        return self._reply(200, {
            "available": _list_available_agents(),
            "default": AGENT_DEFAULT,
        })

    def _runs_list(self, qs):
        """Lightweight registry of every run we know about. Lets the UI show a
        list of past runs and reopen any of them. Phase 5a — also folds in
        historical runs read from each branch's chat.jsonl so the menu still
        reflects yesterday's conversation after a daemon restart."""
        try:
            project_root = resolve_project_root(qs)
        except ValueError:
            project_root = DEFAULT_PROJECT_ROOT
        project_id = (_qs_get(qs, "project") or "default").strip() or "default"
        live = []
        live_ids: set = set()
        with RUNS_LOCK:
            states = list(RUNS.values())
        for s in states:
            with s.lock:
                last_seq = s.events[-1]["seq"] if s.events else -1
            live_ids.add(s.run_id)
            live.append({
                "runId": s.run_id,
                "agentId": s.agent_id,
                "branch": s.branch,
                "kind": s.kind,
                "title": s.title,
                "startedAt": s.started_at,
                "done": s.done,
                "turnDone": s.turn_done,
                "turnsCompleted": s.turns_completed,
                "exitCode": s.exit_code,
                "stopReason": s.stop_reason,  # v2.28
                "lastSeq": last_seq,
                "modifying": s.modifying,
                "project": s.project_id,
                "historical": False,
            })
        # Merge in historical runs that aren't in RUNS. Only runs from the
        # active project — the chat JSONLs live under the project root so this
        # is naturally project-scoped.
        historical = _chat_jsonl_scan_historical(project_root)
        for rid, meta in historical.items():
            if rid in live_ids:
                continue
            # By construction these runs aren't in RUNS, so the spawned
            # process cannot be alive. Force `done: True` even if the JSONL
            # never recorded a __finish line (e.g., the daemon was killed
            # mid-run). Otherwise the UI's "waiting / reply allowed" branch
            # would prompt the user to send to a dead subprocess.
            meta["done"] = True
            meta["project"] = project_id
            live.append(meta)
        live.sort(key=lambda r: r.get("startedAt") or 0, reverse=True)
        return self._reply(200, {"runs": live})

    # GET /__chat?branch=<slug>[&runId=<id>][&project=<id>]
    #   Returns the persisted chat history for a branch (Phase 5a). When
    #   `runId` is provided, the result is filtered to that one run; otherwise
    #   every event for every run on the branch is returned in file order.
    def _chat_history(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        branch = _qs_prototype(qs).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})
        run_filter = (_qs_get(qs, "runId") or "").strip()
        all_rows = _chat_jsonl_read_branch(project_root, branch)
        if run_filter:
            rows = [r for r in all_rows if r.get("runId") == run_filter]
        else:
            rows = all_rows
        return self._reply(200, {"branch": branch, "events": rows})

    # GET /__doc?branch=<slug>&name=<NOTES.md|brand-spec.md>[&project=<id>]
    #   Phase 5a — bounded doc fetch for the toolbar Notes / Brand-spec
    #   buttons. Returns { exists, name, branch, text, bytes }. We don't reuse
    #   the static-file mapping because the UI wants a structured response
    #   (so a 404 can be presented as "no notes yet" rather than a console
    #   error).
    # v3.1 — branches deprecated. MERGES.md / FORK_REQUEST.md dropped.
    _BRANCH_DOC_NAMES = {"NOTES.md", "brand-spec.md", "DESIGN.md"}

    def _branch_doc(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        name = (_qs_get(qs, "name") or "").strip()
        if name not in self._BRANCH_DOC_NAMES:
            return self._reply(400, {
                "error": "doc name not allowed",
                "allowed": sorted(self._BRANCH_DOC_NAMES),
            })
        branch = _qs_prototype(qs).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})
        # Per-branch sources live at <project_root>/source/<branch>/<name>.
        # Project-wide docs (DESIGN.md / MERGES.md / FORK_REQUEST.md) live at
        # <project_root>/<name> per AGENTS.md §"Your cwd is the active
        # project's root". Probe both with branch-scoped winning.
        candidates = [
            os.path.join(project_root, "source", branch, name),
            os.path.join(project_root, name),
        ]
        chosen = None
        for path in candidates:
            if os.path.isfile(path):
                chosen = path
                break
        if not chosen:
            return self._reply(200, {
                "exists": False, "name": name, "branch": branch, "text": "", "bytes": 0,
            })
        try:
            with open(chosen, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            return self._reply(500, {"error": f"read failed: {e}"})
        return self._reply(200, {
            "exists": True, "name": name, "branch": branch,
            "text": text, "bytes": len(text.encode("utf-8")),
            "path": os.path.relpath(chosen, project_root),
        })

    # ── Phase 5b — render-check screenshot endpoints ──────────────────────
    # POST /__screenshot  body: { branch, view?|file?, frameId?, waitMs?, selector?, scale? }
    #   Synchronously waits up to SCREENSHOT_CALLER_TIMEOUT_S for a connected
    #   editor tab to capture and return the PNG. Replies application/json
    #   with `{ok, pngBase64, width, height, bytes}` or `{ok: false, error}`.
    def _screenshot_create(self, qs):
        try:
            body = self._read_json_body()
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        branch = (body.get("branch") or "main").strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})

        view = body.get("view")
        file = body.get("file")
        if (view is None) == (file is None):
            return self._reply(400, {"error": "request must specify exactly one of `view` or `file`"})

        kind = "view" if view else "file"

        if view is not None:
            view = str(view).strip()
            if view not in SCREENSHOT_VIEWS:
                return self._reply(400, {
                    "error": f"unknown view: {view!r}",
                    "known": sorted(SCREENSHOT_VIEWS),
                })

        if file is not None:
            file = str(file).strip()
            # File must be a relative path inside the branch source; reject
            # absolute and any `..` segments. The worker resolves it as
            # `/source/<branch>/<file>` so the daemon's translate_path then
            # serves it from the project root.
            if not file or file.startswith("/") or ".." in file.split("/"):
                return self._reply(400, {"error": "invalid file path", "file": file})

        frame_id = (body.get("frameId") or None)
        if frame_id is not None:
            frame_id = str(frame_id).strip() or None

        try: wait_ms = int(body.get("waitMs") or 600)
        except Exception: wait_ms = 600
        wait_ms = max(0, min(10_000, wait_ms))

        selector = body.get("selector") or None
        if selector is not None:
            selector = str(selector).strip()[:200] or None

        try: scale = float(body.get("scale") or 1)
        except Exception: scale = 1.0
        scale = max(0.25, min(3.0, scale))

        job_id = uuid.uuid4().hex[:16]
        job = SsJob(job_id, branch, kind, view=view, file=file, frame_id=frame_id,
                    wait_ms=wait_ms, selector=selector, scale=scale)

        with SCREENSHOT_JOBS_LOCK:
            _ss_gc_locked()
            SCREENSHOT_JOBS[job_id] = job

        _ss_wake_branch(branch)

        # Block until either the result lands or we time out. We hold the
        # connection open the whole time so the agent's `curl` call simply
        # returns the answer.
        finished = job.result_event.wait(timeout=SCREENSHOT_CALLER_TIMEOUT_S)
        if not finished:
            # Mark the job error so a late worker result is dropped on the
            # floor rather than left dangling.
            with SCREENSHOT_JOBS_LOCK:
                if job.state in ("queued", "running"):
                    job.state = "error"
                    job.error = "caller timeout (no editor tab responded)"
            return self._reply(504, {"ok": False, "error": job.error, "jobId": job_id})

        if job.state == "error" or job.png_bytes is None:
            return self._reply(502, {"ok": False, "error": job.error or "unknown error", "jobId": job_id})

        return self._reply(200, {
            "ok":        True,
            "jobId":     job_id,
            "pngBase64": base64.b64encode(job.png_bytes).decode("ascii"),
            "bytes":     len(job.png_bytes),
            "width":     job.width,
            "height":    job.height,
            "view":      job.view,
            "file":      job.file,
            "branch":    job.branch,
        })

    # GET /__screenshot/jobs?branch=<slug>
    #   Editor-side long-poll. Returns up to one queued job at a time, marks
    #   it running atomically before returning so two tabs on the same branch
    #   don't double-execute it. Reply shape: `{job: <SsJob.public_dict>}` or
    #   `{job: null}` on timeout (worker reconnects).
    def _screenshot_poll(self, qs):
        branch = _qs_prototype(qs, default="").strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})

        def claim():
            with SCREENSHOT_JOBS_LOCK:
                for job in SCREENSHOT_JOBS.values():
                    if job.branch == branch and job.state == "queued":
                        job.state = "running"
                        return job
            return None

        job = claim()
        if job:
            return self._reply(200, {"job": job.public_dict()})

        # Park: register a wake event for this branch, wait, retry once.
        waker = threading.Event()
        with SCREENSHOT_JOBS_LOCK:
            SCREENSHOT_WAITERS.setdefault(branch, set()).add(waker)
        try:
            waker.wait(timeout=SCREENSHOT_WORKER_POLL_TIMEOUT_S)
            job = claim()
            if job:
                return self._reply(200, {"job": job.public_dict()})
            return self._reply(200, {"job": None})
        finally:
            with SCREENSHOT_JOBS_LOCK:
                SCREENSHOT_WAITERS.get(branch, set()).discard(waker)

    # POST /__screenshot/jobs/<id>/result
    #   Editor posts back the captured PNG. Body:
    #     { ok: true,  pngBase64, width, height }
    #     { ok: false, error }
    def _screenshot_result(self, job_id: str):
        try:
            body = self._read_json_body(max_bytes=SCREENSHOT_MAX_PNG_BYTES + 4096)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        with SCREENSHOT_JOBS_LOCK:
            job = SCREENSHOT_JOBS.get(job_id)
            if not job:
                return self._reply(404, {"error": "unknown jobId", "jobId": job_id})
            if job.state in ("done", "error"):
                # The caller already timed out and we marked the job error.
                # Don't overwrite the terminal state — just acknowledge.
                return self._reply(200, {"ok": True, "alreadyTerminal": True, "state": job.state})

        if body.get("ok") is False:
            job.error = str(body.get("error") or "editor reported failure")
            job.state = "error"
            job.result_event.set()
            return self._reply(200, {"ok": True})

        png_b64 = body.get("pngBase64") or ""
        if not isinstance(png_b64, str) or not png_b64:
            job.error = "missing pngBase64 in result body"
            job.state = "error"
            job.result_event.set()
            return self._reply(400, {"error": job.error})

        try:
            png_bytes = base64.b64decode(png_b64, validate=True)
        except Exception as e:
            job.error = f"invalid base64 payload: {e}"
            job.state = "error"
            job.result_event.set()
            return self._reply(400, {"error": job.error})

        if len(png_bytes) > SCREENSHOT_MAX_PNG_BYTES:
            job.error = f"png exceeds {SCREENSHOT_MAX_PNG_BYTES} bytes"
            job.state = "error"
            job.result_event.set()
            return self._reply(413, {"error": job.error})

        # Defensive size hints — editor sends them; we don't recompute.
        try: w = int(body.get("width") or 0) or None
        except Exception: w = None
        try: h = int(body.get("height") or 0) or None
        except Exception: h = None

        job.png_bytes = png_bytes
        job.width = w
        job.height = h
        job.state = "done"
        job.result_event.set()
        return self._reply(200, {"ok": True, "bytes": len(png_bytes)})

    # ── Phase 5c — multipart upload of project assets ─────────────────────
    # Distinct from `/__attachment` (Phase 4d): that route is single-image,
    # base64, vision-bound (lives in `source/<branch>/_attachments/`). This
    # route is multi-file, multipart/form-data, lives in
    # `source/<branch>/uploads/`, accepts any file type. Agents reference the
    # files by path (e.g., `--image uploads/sketch.png` for img2img).
    _UPLOAD_MAX_PER_FILE   = 50 * 1024 * 1024   # 50 MB per file
    _UPLOAD_MAX_TOTAL      = 200 * 1024 * 1024  # 200 MB per request
    _UPLOAD_BAD_FILENAME   = re.compile(r"[\x00-\x1f/\\]")  # control, slash, backslash

    @classmethod
    def _upload_sanitize_filename(cls, raw: str) -> str:
        """Normalize an uploaded filename into something safe to live on disk.
        Strip directory parts, refuse traversal, fall back to a slug if the
        cleaned name is empty."""
        if not isinstance(raw, str):
            raw = ""
        # Some browsers send "C:\\Users\\foo\\bar.png" for absolute Windows paths.
        # `os.path.basename` only catches forward-slash; manually split on both.
        base = raw.replace("\\", "/").split("/")[-1].strip()
        if base in ("", ".", ".."):
            return ""
        # Replace dangerous chars with `_`. Keep the original-ish name so the
        # agent can reference uploads/<filename> verbatim from chat.
        base = cls._UPLOAD_BAD_FILENAME.sub("_", base)
        if len(base) > 200:
            # Preserve extension if present.
            stem, dot, ext = base.rpartition(".")
            if dot and len(ext) <= 10:
                base = stem[: 200 - len(ext) - 1] + "." + ext
            else:
                base = base[:200]
        return base

    @staticmethod
    def _upload_parse_multipart(body: bytes, boundary: bytes) -> list:
        """Minimal multipart/form-data parser. Returns list of
        `(headers_dict, payload_bytes)` for every part. Skips parts without a
        Content-Disposition header (defensive: legitimate browsers always
        include one for form fields)."""
        sep = b"--" + boundary
        out = []
        for raw in body.split(sep)[1:]:
            if raw[:2] == b"--":   # end-of-stream marker `--boundary--`
                continue
            # Each part starts with CRLF after the boundary line.
            if raw[:2] == b"\r\n":
                raw = raw[2:]
            elif raw[:1] == b"\n":
                raw = raw[1:]
            # Header/body split.
            sp = raw.find(b"\r\n\r\n")
            if sp >= 0:
                hb, payload = raw[:sp], raw[sp+4:]
            else:
                sp = raw.find(b"\n\n")
                if sp < 0:
                    continue
                hb, payload = raw[:sp], raw[sp+2:]
            # Strip trailing CRLF before the next boundary line.
            if payload.endswith(b"\r\n"):
                payload = payload[:-2]
            elif payload.endswith(b"\n"):
                payload = payload[:-1]
            headers = {}
            for line in hb.decode("utf-8", errors="replace").splitlines():
                k, _, v = line.partition(":")
                headers[k.strip().lower()] = v.strip()
            if "content-disposition" not in headers:
                continue
            out.append((headers, payload))
        return out

    @staticmethod
    def _upload_extract_filename(cd_header: str) -> str:
        """Pull the filename out of a Content-Disposition: form-data header.
        Honours both `filename="..."` and the RFC 5987 `filename*=UTF-8''...`
        forms; bare `filename=foo` (no quotes) also works."""
        if not cd_header:
            return ""
        # Try RFC 5987 first (browsers prefer it for non-ASCII names).
        m = re.search(r'filename\*\s*=\s*([^\';]+)\'[^\']*\'([^;]+)', cd_header)
        if m:
            try:
                return urllib.parse.unquote(m.group(2).strip(), encoding=m.group(1).strip() or "utf-8")
            except Exception:
                pass
        m = re.search(r'filename\s*=\s*"([^"]*)"', cd_header)
        if m:
            return m.group(1).strip()
        m = re.search(r'filename\s*=\s*([^;]+)', cd_header)
        if m:
            return m.group(1).strip()
        return ""

    def _upload_files(self, qs):
        """POST /__upload?branch=<slug>[&project=<id>]
        Body: multipart/form-data with one or more file parts (field name
        ignored; we accept any number of files in any field).
        Writes each file under `source/<branch>/uploads/<sanitized-filename>`
        and returns `{ ok, files: [{ name, path, bytes, mime }, ...] }`."""
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        branch = _qs_prototype(qs).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})

        ctype = self.headers.get("Content-Type", "")
        if not ctype.lower().startswith("multipart/form-data"):
            return self._reply(400, {"error": "expected multipart/form-data",
                                      "got": ctype[:120]})
        m = re.search(r'boundary\s*=\s*"?([^";]+)"?', ctype)
        if not m:
            return self._reply(400, {"error": "missing multipart boundary"})
        boundary = m.group(1).encode("latin-1", errors="replace")

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except Exception:
            length = 0
        if length <= 0:
            return self._reply(400, {"error": "missing Content-Length"})
        if length > self._UPLOAD_MAX_TOTAL:
            return self._reply(413, {"error": f"body too large: {length} > {self._UPLOAD_MAX_TOTAL}"})
        body = self.rfile.read(length)

        try:
            parts = self._upload_parse_multipart(body, boundary)
        except Exception as e:
            return self._reply(400, {"error": f"multipart parse failed: {e}"})

        # Resolve target dir once; refuses any branch slug that would escape.
        try:
            uploads_dir = _safe_join(project_root, "source", branch, "uploads")
        except ValueError as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})
        try:
            os.makedirs(uploads_dir, exist_ok=True)
        except OSError as e:
            return self._reply(500, {"error": f"mkdir failed: {e}"})

        written = []
        skipped = []
        for headers, payload in parts:
            cd = headers.get("content-disposition", "")
            raw_name = self._upload_extract_filename(cd)
            name = self._upload_sanitize_filename(raw_name)
            if not name:
                # form-data field without filename → not a file upload, ignore
                continue
            if len(payload) > self._UPLOAD_MAX_PER_FILE:
                skipped.append({"name": name, "reason": f"too large: {len(payload)} > {self._UPLOAD_MAX_PER_FILE}"})
                continue
            # Avoid clobbering an existing file: if the name collides, suffix
            # with `-<ts>` before the extension.
            try:
                abs_path = _safe_join(uploads_dir, name)
            except ValueError:
                skipped.append({"name": name, "reason": "path traversal blocked"})
                continue
            if os.path.exists(abs_path):
                stem, dot, ext = name.rpartition(".")
                ts = int(time.time() * 1000)
                if dot:
                    name = f"{stem}-{ts}.{ext}"
                else:
                    name = f"{name}-{ts}"
                abs_path = _safe_join(uploads_dir, name)
            try:
                with open(abs_path, "wb") as f:
                    f.write(payload)
            except OSError as e:
                skipped.append({"name": name, "reason": f"write failed: {e}"})
                continue
            written.append({
                "name":  name,
                "path":  f"uploads/{name}",
                "bytes": len(payload),
                "mime":  headers.get("content-type", "") or "application/octet-stream",
            })

        return self._reply(200, {
            "ok":      bool(written),
            "branch":  branch,
            "files":   written,
            "skipped": skipped,
        })

    def _upload_list(self, qs):
        """GET /__upload/list?branch=<slug>[&project=<id>]
        Lists every file under `source/<branch>/uploads/`. Returns
        `{ branch, files: [{ name, path, bytes, mtime }] }` newest-first."""
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        branch = _qs_prototype(qs).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})

        try:
            uploads_dir = _safe_join(project_root, "source", branch, "uploads")
        except ValueError as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})

        if not os.path.isdir(uploads_dir):
            return self._reply(200, {"branch": branch, "files": []})

        files = []
        try:
            for name in os.listdir(uploads_dir):
                if name.startswith("."):
                    continue
                p = os.path.join(uploads_dir, name)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if not stat.S_ISREG(st.st_mode):
                    continue
                files.append({
                    "name":  name,
                    "path":  f"uploads/{name}",
                    "bytes": st.st_size,
                    "mtime": st.st_mtime,
                })
        except OSError as e:
            return self._reply(500, {"error": f"listdir failed: {e}"})

        files.sort(key=lambda r: r["mtime"], reverse=True)
        return self._reply(200, {"branch": branch, "files": files})

    def _upload_delete(self, qs):
        """POST /__upload/delete?branch=<slug>&name=<filename>[&project=<id>]
        Removes one file from `source/<branch>/uploads/`. The UI's per-file
        × button targets this — agents that need to clean up should use the
        regular `Bash rm` tool instead. 404 if the file is already gone."""
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        branch = _qs_prototype(qs).strip().lower()
        if not SLUG_OK.match(branch):
            return self._reply(400, {"error": "invalid branch slug", "slug": branch})

        raw_name = (_qs_get(qs, "name") or "").strip()
        name = self._upload_sanitize_filename(raw_name)
        if not name:
            return self._reply(400, {"error": "missing or invalid name"})

        try:
            uploads_dir = _safe_join(project_root, "source", branch, "uploads")
            abs_path = _safe_join(uploads_dir, name)
        except ValueError as e:
            return self._reply(400, {"error": f"path resolution failed: {e}"})

        if not os.path.isfile(abs_path):
            return self._reply(404, {"error": "not found", "name": name})

        try:
            os.remove(abs_path)
        except OSError as e:
            return self._reply(500, {"error": f"delete failed: {e}"})

        return self._reply(200, {"ok": True, "name": name})

    def _run_get(self, run_id: str):
        """Snapshot a single run's metadata + last event seq. Used by the UI on
        startup to validate a remembered `lastRunId` and resume streaming."""
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            # v2.29b — rehydrate from JSONL after daemon restart, same as
            # /__run/<id>/resume. Without this the canvas polling loop +
            # WorkflowAgentNode chat-fetch keep 404ing for every prior run.
            try:
                qs = urllib.parse.parse_qs((self.path.split("?", 1) + [""])[1])
                project_root = resolve_project_root(qs)
                state = _rehydrate_run_from_jsonl(run_id, project_root)
            except Exception:
                state = None
            if not state:
                return self._reply(404, {"error": "unknown runId", "runId": run_id})
        with state.lock:
            last_seq = state.events[-1]["seq"] if state.events else -1
        return self._reply(200, {
            "runId": state.run_id,
            "agentId": state.agent_id,
            "branch": state.branch,
            "kind": state.kind,
            "title": state.title,
            "startedAt": state.started_at,
            "done": state.done,
            "turnDone": state.turn_done,
            "turnsCompleted": state.turns_completed,
            "exitCode": state.exit_code,
            "stopReason": state.stop_reason,  # v2.28
            "lastSeq": last_seq,
            "modifying": state.modifying,
            "project": state.project_id,
        })

    def _read_json_body(self, max_bytes: int = 256 * 1024):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > max_bytes:
            raise ValueError(f"missing or oversized JSON body (bytes={length}, max={max_bytes})")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as e:
            raise ValueError(f"invalid JSON body: {e}")

    # POST /__run  body: { branch, agentId?, kind?, prompt?, title?, meta? }
    def _run_create(self, qs):
        body = self._read_json_body()
        # v3.8 — resolve project from EITHER qs (editor UI puts it there via
        # apiUrl()) OR body (legacy ad-hoc curl callers). Earlier this only
        # read from body, which worked when resolve_project_root had a silent
        # first-project fallback; the v3.7 strict-require flip exposed it as
        # a hard 400 on every chat spawn from the editor. Merge so either
        # source resolves; body takes precedence (explicit JSON beats URL).
        merged = dict(qs) if qs else {}
        for k, v in body.items():
            if k == "project" and v: merged["project"] = v
        try:
            project_root = resolve_project_root(merged)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        project_id = (_qs_get(merged, "project") or "default").strip() or "default"
        agent_id = (body.get("agentId") or AGENT_DEFAULT).strip().lower()
        if agent_id not in AGENT_DEFS:
            return self._reply(400, {"error": f"unknown agentId: {agent_id}",
                                      "known": list(AGENT_DEFS.keys())})
        bin_path = detect_agent_bin(agent_id)
        if not bin_path:
            env_key = AGENT_BIN_ENV.get(agent_id, "")
            return self._reply(400, {
                "error": f"agent '{agent_id}' is not on PATH",
                "hint": f"install it, or set ${env_key} to an absolute binary path",
            })

        # v3.4.31 — Per-prototype editor scope.
        # In v3.1 branches collapsed into source/<slug>/ and this used to be
        # hardcoded to "main" because there was no per-call slug carrier.
        # The editor now passes ?branch=<slug> in the URL when the user
        # picks a starred prototype, the chat dispatcher forwards that as
        # `branch` in the body, so honor it here. We validate against the
        # same alphabet _starred_prototypes_toggle accepts (one or two
        # path segments, each [A-Za-z0-9_.-]) — malformed slugs silently
        # fall back to "main" so the agent always gets a usable scope.
        _raw_branch = (body.get("branch") or "main").strip()
        if re.match(r"^[A-Za-z0-9_.-]{1,80}(?:/[A-Za-z0-9_.-]{1,80})?$", _raw_branch):
            branch = _raw_branch
        else:
            branch = "main"
        kind = (body.get("kind") or "freeform").strip()
        user_prompt = (body.get("prompt") or "").strip()
        if kind == "freeform" and not user_prompt:
            return self._reply(400, {"error": "freeform run requires a prompt"})
        title = (body.get("title") or _default_run_title(kind, body)).strip()

        prompt_text = _compose_initial_prompt(kind, user_prompt)
        defs = AGENT_DEFS[agent_id]

        # Resolve the permission mode (per-run override > daemon default).
        # For Claude Code in -p mode this MUST be set or every tool auto-denies.
        permission_mode = (body.get("permissionMode") or defs.get("permission_default") or "").strip()
        spawn_args = list(defs["args"])
        # v2.45 / v3.8.1 — Claude Code 2.1.163 split the bypass into TWO
        # flags. --dangerously-skip-permissions alone no longer skips
        # prompts; --allow-dangerously-skip-permissions must ENABLE the
        # bypass first. See `claude --help`:
        #   --allow-dangerously-skip-permissions   Enable bypassing all permission checks
        #   --dangerously-skip-permissions         Bypass all permission checks.
        # The /__run path at this site was missed when the other spawn
        # site (_spawn_node_agent) was patched — every chat spawn from
        # the editor UI flows through here, so the missing flag is what
        # made "i try to run and nothing happens" — the spawn would
        # succeed structurally but the subprocess hit a permission wall
        # on its first tool call and emitted empty text.
        # v3.5 — Claude-only flag block. Codex's CLI surface differs:
        #   • permission bypass: codex uses --full-auto, not the Claude pair
        #   • --disable-slash-commands / --settings / --append-system-prompt
        #     are Claude Code-specific and would crash codex with "unknown flag"
        # Gate them behind agent_id == "claude" so a Codex spawn stays clean.
        if agent_id == "claude":
            if permission_mode == "bypassPermissions":
                spawn_args += [
                    "--allow-dangerously-skip-permissions",
                    "--dangerously-skip-permissions",
                ]
            elif defs.get("permission_flag") and permission_mode:
                spawn_args += [defs["permission_flag"], permission_mode]
            # v3.1 — Hide user-level slash commands so /prototype etc. don't
            # auto-load and override the visual-orchestrator pipeline. Subagents
            # dispatched via the Task tool are unaffected.
            spawn_args += ["--disable-slash-commands"]
            # v3.1 — Hook gate: block *.html writes until visual-orchestrator dispatched.
            _harness_settings = _ensure_harness_settings()
            if _harness_settings:
                spawn_args += ["--settings", _harness_settings]
        elif agent_id == "codex":
            # v3.5 — Codex's permission flags are version-specific
            # (--full-auto / --approval-mode full-auto / a config key).
            # We don't know which the user's install accepts so we pass
            # nothing here. `codex exec` is non-interactive by definition,
            # so most versions just run without prompts; if a future error
            # shows codex blocking, add the right flag here based on the
            # empirical message.
            pass
        # Append the question-form protocol so disabling AskUserQuestion
        # doesn't lose the "ask the user" capability — see
        # QUESTION_FORM_SYSTEM_PROMPT for the rationale. In workspace mode
        # also append the layout paragraph so the agent knows where the
        # shared protocol mount lives (cwd ≠ protocol root).
        # v3.5 — onboarding cut: no discovery flow, no orchestration mount.
        # Every spawn drops into the workflow canvas with the capabilities
        # preamble; the user steers from chat (Path A / Path B orchestrator
        # dispatch, `/prototype` skill, or library nodes).
        wants_discovery     = False
        wants_orchestration = False
        include_views       = False
        if agent_id == "claude":
            sys_prompt = QUESTION_FORM_SYSTEM_PROMPT
            if WORKSPACE_DIR and project_root != INSTALL_ROOT:
                sys_prompt = sys_prompt + WORKSPACE_LAYOUT_PROMPT
            # v3.4.31 — When the spawn carries a non-default branch slug
            # (the user is editing a specific starred prototype), tell the
            # agent which `source/<slug>/` subtree is "active" so file
            # reads/writes default to that subtree. Only emitted for non-
            # "main" slugs so legacy single-prototype projects keep their
            # current behavior verbatim. The phrasing matches AGENTS.md /
            # PROTOTYPE.md "scope" vocabulary the agent already knows.
            if branch and branch != "main":
                sys_prompt = sys_prompt + (
                    "\n\n## Active prototype scope\n\n"
                    f"The user is currently editing the `source/{branch}/` "
                    "prototype. Default every file read, edit, and write to "
                    f"that subtree unless the user explicitly names a different "
                    "prototype. When a relative file path is ambiguous (e.g. "
                    "`index.html`), resolve it under "
                    f"`source/{branch}/`. Other `source/<slug>/` subtrees in "
                    "this project belong to sibling prototypes — leave them "
                    "alone unless the user asks for a cross-prototype change."
                )
            # v3.5 — onboarding cut. Discovery + orchestrator hooks removed.
            # The capabilities preamble (appended below) is the only thing
            # the agent reads beyond QUESTION_FORM_SYSTEM_PROMPT.
            # v2.50 — capabilities catalog. Every spawn (orchestrator,
            # freeform, discovery) gets a compact list of integrated
            # providers + subagents + endpoints + node kinds, so the agent
            # doesn't answer "I don't have X" for features that ARE
            # integrated (the Quiver AI case). See kinds/capabilities.py.
            try:
                from kinds.capabilities import capabilities_preamble
                sys_prompt = sys_prompt + "\n\n" + capabilities_preamble()
            except Exception:
                pass
            spawn_args += ["--append-system-prompt", sys_prompt]
        elif agent_id == "codex":
            # v3.5 — Codex chats get the SAME capabilities preamble as Claude
            # (so they know visual-orchestrator etc. exist), plus a translation
            # note that maps Claude's `Task(subagent_type: ...)` dispatch
            # pattern to a POST against /__dispatch_planner — codex doesn't
            # have a native Task tool but has shell + curl. The endpoint is
            # reentrant and picks whichever runtime is available, so the
            # nested planner can run on Claude or another codex; codex doesn't
            # have to care.
            codex_sys_bits = [QUESTION_FORM_SYSTEM_PROMPT]
            if WORKSPACE_DIR and project_root != INSTALL_ROOT:
                codex_sys_bits.append(WORKSPACE_LAYOUT_PROMPT)
            if branch and branch != "main":
                codex_sys_bits.append(
                    "\n## Active prototype scope\n\n"
                    f"The user is currently editing the `source/{branch}/` "
                    "prototype. Default every file read, edit, and write to "
                    f"that subtree unless the user explicitly names a "
                    f"different prototype."
                )
            try:
                from kinds.capabilities import capabilities_preamble
                codex_sys_bits.append(capabilities_preamble())
            except Exception:
                pass
            codex_sys_bits.append(
                "\n## Subagent dispatch on this runtime\n\n"
                "You are running on the Codex CLI, which has no native `Task` "
                "tool. Wherever the capabilities preamble or any subagent spec "
                "instructs you to dispatch a planner subagent via the Task "
                "tool, instead run this shell command:\n\n"
                "```\n"
                "curl -N -s -X POST "
                f"'http://127.0.0.1:{PORT}/__dispatch_planner?project={project_id}' "
                "-H 'content-type: application/json' "
                "-d '{\"type\":\"<orchestrator-id>\",\"brief\":\"<plain text brief>\"}'\n"
                "```\n\n"
                "The daemon streams the planner's progress as Server-Sent "
                "Events. The connection stays open (with heartbeats) for the "
                "full duration of the planner run — minutes to tens of "
                "minutes is normal. Events you'll see:\n"
                "  • `event: planner-dispatched` — first; carries `runId`\n"
                "  • `event: agent` — agent text / tool calls / tool results\n"
                "  • `event: planner-done` — last; carries the synthesized "
                "    `output` you treat as the Task return value\n\n"
                "Wait for the `planner-done` event to arrive, then parse its "
                "`data:` JSON and use the `output` field. The endpoint is "
                "reentrant — a planner that needs nested subagent dispatch "
                "will use the same curl pattern, and the daemon picks the "
                "best runtime for each level."
            )
            # Codex's preamble is prepended to the user prompt rather than
            # passed via a flag — codex `exec` has no --append-system-prompt
            # equivalent. The shape mirrors `_dispatch_planner_via_codex`.
            codex_preamble = "\n\n".join(p.strip() for p in codex_sys_bits if p and p.strip())
            prompt_text = (
                "===== HARNESS PREAMBLE =====\n"
                + codex_preamble
                + "\n===== END HARNESS PREAMBLE =====\n\n"
                + "===== USER REQUEST =====\n"
                + prompt_text
            )
        # The agent's workspace is the PROJECT only. We do NOT add
        # INSTALL_ROOT to --add-dir — that would extend the writable
        # sandbox to the editor binary itself, which several past runs
        # abused (editing editor/app.js, dropping files into editor/assets/).
        # See _build_child_env's TH_PROTOCOL_ROOT env var + AGENTS.md
        # "Editor source is OFF LIMITS" — protocol-root reads happen via
        # absolute paths through Read/Bash, which don't require --add-dir.
        #
        # v2.44 — Claude Code 2.1.150+ no longer auto-allows writes to cwd
        # even with --permission-mode bypassPermissions. Explicitly add the
        # project root so Write/Edit calls inside it don't trigger
        # "Claude requested permissions" prompts. cwd is project_root for
        # this spawn (see subprocess.Popen below), so this is purely
        # confirming "yes, you can write inside your own working directory."
        # v3.5 — Claude-only; Codex uses cwd directly without an --add-dir flag.
        if agent_id == "claude":
            spawn_args += ["--add-dir", project_root]

        # v3.5 — When the agent doesn't accept a stream-json prompt on stdin
        # (codex), pass the prompt as the trailing positional argv. Codex
        # exec's signature is `codex exec [OPTIONS] [PROMPT]`.
        if not defs["prompt_via_stdin"]:
            spawn_args.append(prompt_text)

        run_id = uuid.uuid4().hex[:16]
        env = _build_child_env(agent_id, run_id,
                               project_root=project_root, project_id=project_id)

        try:
            proc = subprocess.Popen(
                [bin_path, *spawn_args],
                cwd=project_root,
                stdin=subprocess.PIPE if defs["prompt_via_stdin"] else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,  # line-buffered for stream-json line-at-a-time read
            )
        except FileNotFoundError:
            return self._reply(500, {"error": f"{bin_path}: not executable"})
        except Exception as e:
            return self._reply(500, {"error": f"spawn failed: {type(e).__name__}: {e}"})

        state = RunState(run_id, proc, agent_id, branch, kind, title,
                         project_id=project_id, project_root=project_root)
        state.bin_path = bin_path
        state.permission_mode = permission_mode or None
        # ── History snapshot — BEFORE state ──────────────────────────────
        # The subprocess is running but hasn't received its prompt yet (we
        # write to stdin further down). It can't have produced any file
        # writes between Popen and this point, so the snapshot we take here
        # is the canonical "before agent ran" state. _drain_stdout calls
        # _history_run_snapshot_finish after state.finish() to commit the
        # entry with the after-snapshot diff.
        state.history_pending_id = None
        state.history_before_paths = []
        state.history_before_rows  = []
        try:
            eid, paths, rows, _ = _history_run_snapshot_before(project_root)
            state.history_pending_id  = eid
            state.history_before_paths = paths
            state.history_before_rows  = rows
        except Exception as e:
            # Never block a run on history failure. Log + continue.
            state.append("status", {"label": "history-snapshot-failed", "detail": str(e)})
        # Kinds whose entire purpose is to modify files — lock the UI from
        # the moment of spawn. Freeform runs only flip `modifying=True` if a
        # Write/Edit/MultiEdit/NotebookEdit tool_use is actually observed.
        if kind in ("edits-apply", "fork", "merge", "regenerate",
                    "statemachine-request", "timeline-request", "grid-request"):
            state.modifying = True
        # Record a startup banner so the UI has something to show before the
        # CLI's first frame arrives.
        state.append("status", {
            "label": "spawned",
            "agentId": agent_id,
            "binPath": bin_path,
            "branch": branch,
            "kind": kind,
            "permissionMode": permission_mode or None,
            "promptPreview": prompt_text[:240],
        })
        # For freeform chats, the prompt IS the user's first message — echo it
        # so the UI shows "you: <prompt>" before the agent replies. Other kinds
        # (edits-apply, regenerate) wrap the user's intent in a system-style
        # instruction; we keep those out of the chat log so it stays clean.
        if kind == "freeform" and user_prompt:
            state.append("user_message", {"text": user_prompt})

        with RUNS_LOCK:
            RUNS[run_id] = state

        # Feed the initial prompt as a Claude-style stream-json `user` frame.
        # Both Claude Code and Codex accept this shape on stdin when launched
        # with `--input-format stream-json`. We leave stdin open so phases 3+
        # can pipe follow-up user messages (form answers) through the same fd.
        if defs["prompt_via_stdin"]:
            try:
                proc.stdin.write(_claude_user_frame(prompt_text))
                proc.stdin.flush()
            except Exception as e:
                state.append("error", {"message": f"failed to write prompt to stdin: {e}"})

        threading.Thread(target=_drain_stdout, args=(state,), daemon=True,
                         name=f"run-{run_id}-stdout").start()
        threading.Thread(target=_drain_stderr, args=(state,), daemon=True,
                         name=f"run-{run_id}-stderr").start()

        return self._reply(200, {
            "runId": run_id,
            "agentId": agent_id,
            "branch": branch,
            "kind": kind,
            "title": title,
        })

    # GET /__stream?runId=<id>&after=<seq>  →  Server-Sent Events
    def _run_stream(self, qs):
        run_id = (qs.get("runId") or [""])[0]
        try:
            after = int((qs.get("after") or ["-1"])[0])
        except ValueError:
            after = -1
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            return self._reply(404, {"error": "unknown runId", "runId": run_id})

        # Stream forever (until the run finishes AND we've flushed all events).
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        # Each connection gets its own waker so other waiters aren't disturbed.
        waker = threading.Event()
        with state.lock:
            state.waiters.add(waker)

        def flush_from(after_seq):
            with state.lock:
                pending = state.events[after_seq + 1:]
            for ev in pending:
                payload = (
                    f"id: {ev['seq']}\n"
                    f"event: {ev['type']}\n"
                    f"data: {json.dumps(ev['data'])}\n\n"
                ).encode("utf-8")
                try:
                    self.wfile.write(payload)
                    self.wfile.flush()
                except Exception:
                    return None  # client disconnected
            return state.events[-1]["seq"] if state.events else after_seq

        try:
            last_seen = flush_from(after)
            if last_seen is None:
                return
            while True:
                with state.lock:
                    have_more = state.events and state.events[-1]["seq"] > last_seen
                    is_done = state.done
                if is_done and not have_more:
                    break
                # 25 s heartbeat — beneath proxy idle thresholds.
                waker.wait(timeout=25)
                waker.clear()
                with state.lock:
                    have_more = state.events and state.events[-1]["seq"] > last_seen
                if have_more:
                    last_seen = flush_from(last_seen)
                    if last_seen is None:
                        return
                else:
                    try:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                    except Exception:
                        return
        finally:
            with state.lock:
                state.waiters.discard(waker)

    # GET /__workflow/events?project=<id>  →  Server-Sent Events
    # v2.30 — push notification of workflow.json mutations. Each event is
    # `event: workflow-changed` with an empty `data: {}` body — clients
    # then fetch /__workflow to merge. Heartbeat every 25s so proxies don't
    # drop the connection. Per-project waiter set; unregister on disconnect.
    def _workflow_events(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        project_id = os.path.basename(project_root.rstrip("/"))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        waker = WorkflowWaiter()
        with WORKFLOW_WAITERS_LOCK:
            WORKFLOW_WAITERS.setdefault(project_id, set()).add(waker)
        # Make sure the file-watcher is running and has seeded the baseline
        # for this project so the first scan after subscribe doesn't emit a
        # spurious flood of "every existing file just changed".
        _file_watcher_ensure_started()
        try:
            # Initial hello so the client knows the subscription is live.
            try:
                self.wfile.write(b"event: workflow-events-connected\ndata: {}\n\n")
                self.wfile.flush()
            except Exception:
                return
            while True:
                fired = waker.wait(timeout=25)
                if fired:
                    # Drain all pending events at once so a burst of file
                    # changes flushes in one wake-up rather than dripping.
                    events = waker.drain()
                    sent_ok = True
                    for evt_type, evt_data in events:
                        try:
                            payload = json.dumps(evt_data or {}, separators=(",", ":"))
                            frame = f"event: {evt_type}\ndata: {payload}\n\n".encode("utf-8")
                            self.wfile.write(frame)
                            self.wfile.flush()
                        except Exception:
                            sent_ok = False
                            break
                    if not sent_ok:
                        return
                else:
                    # heartbeat keeps proxies + browsers from idle-killing
                    # the conn; the frontend also uses it to refresh the
                    # daemon-liveness probe (see app.js `useDaemonStatus`).
                    try:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                    except Exception:
                        return
        finally:
            with WORKFLOW_WAITERS_LOCK:
                bucket = WORKFLOW_WAITERS.get(project_id)
                if bucket is not None:
                    bucket.discard(waker)
                    if not bucket:
                        WORKFLOW_WAITERS.pop(project_id, None)

    # POST /__run/<id>/stop
    def _run_stop(self, run_id):
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            return self._reply(404, {"error": "unknown runId", "runId": run_id})
        if state.done:
            return self._reply(200, {"ok": True, "alreadyDone": True})
        # v2.28 — tag intent BEFORE terminate(), so the drain-loop's finally
        # block sees the reason when it computes the finish record. Without
        # this the UI would render user-initiated stops as "failed" (because
        # SIGTERM = exit 143 ≠ 0).
        state.stop_reason = "user-stop"
        try:
            state.proc.terminate()
        except Exception as e:
            return self._reply(500, {"error": f"terminate failed: {e}"})
        state.append("status", {"label": "interrupted"})
        return self._reply(200, {"ok": True})

    # POST /__run/<id>/tool-result  body: { toolUseId, content, isError? }
    # Pipes the user's answer to an agent-side tool prompt (AskUserQuestion,
    # custom permission tools, …) back into the child's stdin as a Claude
    # stream-json tool_result content part. Phase 1 finish-touch — required
    # for the AskUserQuestion clickable card.
    def _run_tool_result(self, run_id):
        body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        tool_use_id = (body.get("toolUseId") or "").strip()
        if not tool_use_id:
            return self._reply(400, {"error": "missing toolUseId"})
        content = body.get("content")
        if content is None:
            return self._reply(400, {"error": "missing content"})
        if not isinstance(content, str):
            content = json.dumps(content)
        is_error = bool(body.get("isError"))
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            return self._reply(404, {"error": "unknown runId", "runId": run_id})
        if state.done:
            return self._reply(409, {"error": "run already finished"})
        if not state.proc.stdin or state.proc.stdin.closed:
            return self._reply(409, {"error": "agent stdin not available"})
        try:
            state.proc.stdin.write(_claude_tool_result_frame(tool_use_id, content, is_error))
            state.proc.stdin.flush()
        except Exception as e:
            return self._reply(500, {"error": f"stdin write failed: {e}"})
        # Same turn lifecycle as a follow-up message: agent will keep talking.
        state.turn_done = False
        # Echo into the event log so the UI shows the answered question in-thread.
        state.append("tool_answer", {"toolUseId": tool_use_id, "content": content, "isError": is_error})
        return self._reply(200, {"ok": True})

    # POST /__run/<id>/user-message  body: { text }
    # Pipes a follow-up user message to the child's stdin. Used by Phase 3's
    # form-answer round-trip and by any future "send another message" composer.
    def _run_user_message(self, run_id):
        body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        text = (body.get("text") or "").strip()
        if not text:
            return self._reply(400, {"error": "empty text"})
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            return self._reply(404, {"error": "unknown runId", "runId": run_id})
        if state.done:
            return self._reply(409, {"error": "run already finished"})
        if not state.proc.stdin or state.proc.stdin.closed:
            return self._reply(409, {"error": "agent stdin not available"})
        try:
            state.proc.stdin.write(_claude_user_frame(text))
            state.proc.stdin.flush()
        except Exception as e:
            return self._reply(500, {"error": f"stdin write failed: {e}"})
        # Flip turn back to in-flight so the chip + Runs row reflect "agent
        # is processing the reply" instead of "done, waiting on you."
        state.turn_done = False
        # Echo into the event log so the UI shows the message in-thread.
        state.append("user_message", {"text": text})
        return self._reply(200, {"ok": True})

    # POST /__run/<id>/resume  body: { text }
    # Spawns a NEW Claude process with --resume <sessionId> and pipes the
    # user's new message as its initial input. Used when the previous
    # process exited (user clicked Stop, or it crashed) but the user wants
    # to continue the same conversation with full context. The new process
    # replaces state.proc in-place so the chat drawer keeps streaming on
    # the same runId — the user perceives one continuous conversation, as
    # they would with any normal chat UI.
    def _run_resume_codex(self, state, run_id, text):
        """Fake resume for codex: reconstruct prior conversation as a
        text transcript, prepend it to the new user message, spawn a
        fresh `codex exec` with the combined prompt. Same run_id, same
        event log appended.

        Why fake: codex's exec mode is single-shot per spawn. There's no
        `codex exec --resume <id>` equivalent. The transcript approach
        loses things like tool-call provenance from the model's
        perspective but gives the model enough context to answer follow-
        up questions like "what happened?" after a crash.
        """
        defs = AGENT_DEFS["codex"]
        bin_path = state.bin_path or detect_agent_bin("codex")
        if not bin_path:
            return self._reply(500, {"error": "codex binary not on PATH"})
        # Reconstruct the conversation. Each event-log entry of type "agent"
        # carries a normalised event dict; we walk those and rebuild a
        # transcript that reads naturally.
        lines = []
        with state.lock:
            events = list(state.events)
        for ev in events:
            t = ev.get("type")
            d = ev.get("data") or {}
            if t == "user_message":
                u = (d.get("text") or "").strip()
                if u:
                    lines.append(f"USER: {u}")
            elif t == "agent":
                dt = d.get("type")
                if dt == "text_delta":
                    delta = (d.get("delta") or "").rstrip()
                    if delta:
                        # Coalesce consecutive deltas into one ASSISTANT block.
                        if lines and lines[-1].startswith("ASSISTANT: "):
                            lines[-1] = lines[-1] + "\n" + delta
                        else:
                            lines.append(f"ASSISTANT: {delta}")
                elif dt == "tool_use":
                    name = d.get("name") or "tool"
                    inp = d.get("input") or {}
                    cmd = inp.get("text") or inp.get("command") or json.dumps(inp)
                    lines.append(f"[TOOL CALL: {name}]\n{cmd}")
                elif dt == "tool_result":
                    parts = d.get("content") or []
                    body_txt = ""
                    for p in parts:
                        if isinstance(p, dict) and p.get("type") == "text":
                            body_txt += (p.get("text") or "")
                    err = " (error)" if d.get("is_error") else ""
                    # Truncate large tool results so the prompt doesn't blow up.
                    if len(body_txt) > 4000:
                        body_txt = body_txt[:4000] + "\n…(truncated)"
                    lines.append(f"[TOOL RESULT{err}]\n{body_txt}")
                # status / thinking_delta / usage — skip; transcript noise.
        transcript = "\n\n".join(lines).strip()
        # Compose the resume prompt. Frame it explicitly so codex knows the
        # prior conversation is context, not instructions to repeat.
        if transcript:
            new_prompt = (
                "You are continuing a previous conversation. Below is the "
                "transcript so far; the previous agent process exited before "
                "the user could reply, so resume from where it left off.\n\n"
                "===== PRIOR CONVERSATION =====\n"
                f"{transcript}\n"
                "===== END PRIOR CONVERSATION =====\n\n"
                f"USER (new message): {text}"
            )
        else:
            new_prompt = text
        # Spawn fresh codex with the combined prompt.
        spawn_args = list(defs["args"]) + [new_prompt]
        env = _build_child_env(state.agent_id, run_id,
                               project_root=state.project_root, project_id=state.project_id)
        try:
            proc = subprocess.Popen(
                [bin_path, *spawn_args],
                cwd=state.project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,
            )
        except Exception as e:
            return self._reply(500, {"error": f"codex resume spawn failed: {type(e).__name__}: {e}"})
        # Reset run lifecycle for the new process.
        state.proc = proc
        state.done = False
        state.exit_code = None
        state.turn_done = False
        state.append("status", {"label": "resumed", "agentId": "codex"})
        state.append("user_message", {"text": text})
        threading.Thread(target=_drain_stdout, args=(state,), daemon=True,
                         name=f"run-{run_id}-stdout-resumed").start()
        threading.Thread(target=_drain_stderr, args=(state,), daemon=True,
                         name=f"run-{run_id}-stderr-resumed").start()
        return self._reply(200, {"ok": True, "agentId": "codex"})


    def _run_resume(self, run_id):
        body = self._read_json_body(max_bytes=4 * 1024 * 1024)
        text = (body.get("text") or "").strip()
        if not text:
            return self._reply(400, {"error": "empty text"})
        with RUNS_LOCK:
            state = RUNS.get(run_id)
        if not state:
            # v2.29b — rehydrate from JSONL after daemon restart. Without
            # this, every prior chat became unresumable across daemon
            # restarts (RUNS is in-memory only). project param must be
            # present so we know where to scan.
            try:
                qs = urllib.parse.parse_qs((self.path.split("?", 1) + [""])[1])
                project_root = resolve_project_root(qs)
                state = _rehydrate_run_from_jsonl(run_id, project_root)
            except Exception:
                state = None
            if not state:
                return self._reply(404, {"error": "unknown runId", "runId": run_id,
                                          "hint": "tried to rehydrate from JSONL but the run wasn't found in any branch under the project"})
        if not state.done:
            return self._reply(409, {
                "error": "run is still active; use /user-message instead",
            })
        # v3.5 — Codex resume. Codex doesn't have Claude's stream-json
        # --resume <session-id> protocol; each `codex exec` is a fresh
        # session. We fake resume by reconstructing the prior conversation
        # as a transcript and prepending it to the new prompt, then spawning
        # a fresh codex with that combined prompt. Same run_id, same event
        # log — new process underneath.
        if state.agent_id == "codex":
            return self._run_resume_codex(state, run_id, text)
        if state.agent_id != "claude":
            return self._reply(400, {"error": f"resume not yet supported for agent {state.agent_id!r}"})
        if not state.session_id:
            return self._reply(409, {
                "error": "no session id captured for this run; cannot resume",
                "hint": "Claude Code may not have emitted its init frame before exit",
            })

        defs = AGENT_DEFS[state.agent_id]
        bin_path = state.bin_path or detect_agent_bin(state.agent_id)
        if not bin_path:
            return self._reply(500, {"error": f"agent '{state.agent_id}' binary not found"})

        spawn_args = list(defs["args"])
        # v2.45 / v3.8.2 — third spawn site (continuing an existing chat
        # via /__run/<id>/resume) also needs BOTH bypass flags. Claude
        # Code 2.1.163 split the bypass into --allow-… (enables the
        # option) + --dangerously-… (activates it); passing only the
        # second one makes every subsequent Edit/Write prompt the user,
        # which in -p stream-json mode silently denies. The two other
        # spawn sites (_run_create, _spawn_node_agent) were patched in
        # 19aab27 / 26d13f3 but this one was missed — and it's the path
        # the editor hits every time the user types in an existing
        # chat, so the symptom looked like "permissions are still
        # broken even after the fix landed."
        if state.permission_mode == "bypassPermissions":
            spawn_args += [
                "--allow-dangerously-skip-permissions",
                "--dangerously-skip-permissions",
            ]
        elif defs.get("permission_flag") and state.permission_mode:
            spawn_args += [defs["permission_flag"], state.permission_mode]
        # v3.1 — match the freeform / node-agent paths: hide user slash commands.
        spawn_args += ["--disable-slash-commands"]
        # v3.1 — Hook gate: block *.html writes until visual-orchestrator dispatched.
        _harness_settings = _ensure_harness_settings()
        if _harness_settings:
            spawn_args += ["--settings", _harness_settings]
        sys_prompt = QUESTION_FORM_SYSTEM_PROMPT
        if WORKSPACE_DIR and state.project_root != INSTALL_ROOT:
            sys_prompt = sys_prompt + WORKSPACE_LAYOUT_PROMPT
        # v2.50 — resumed agents also get the capabilities catalog.
        try:
            from kinds.capabilities import capabilities_preamble
            sys_prompt = sys_prompt + "\n\n" + capabilities_preamble()
        except Exception:
            pass
        spawn_args += ["--append-system-prompt", sys_prompt]
        spawn_args += ["--resume", state.session_id]
        # The agent's workspace is the PROJECT only — INSTALL_ROOT is NOT
        # added to --add-dir on resume either, mirroring the policy applied
        # on the initial spawn (see _run_create's _spawn_node_agent path).
        # Protocol-root reads still work via absolute paths through Read/Bash.
        # v2.44 — explicitly allow writes inside the project root.
        spawn_args += ["--add-dir", state.project_root]

        env = _build_child_env(state.agent_id, run_id,
                               project_root=state.project_root, project_id=state.project_id)

        # v3.8.3 — log just the permission-related flags so a future
        # regression in this code path is immediately visible in the
        # daemon log without leaking the system prompt or settings path.
        try:
            _flags = [a for a in spawn_args if a.startswith("--allow-")
                      or a.startswith("--dangerously-") or a.startswith("--permission-")]
            print(f"[resume-spawn] runId={run_id} sessionId={state.session_id} "
                  f"permission_mode={state.permission_mode!r} permission_flags={_flags!r}", flush=True)
        except Exception:
            pass

        try:
            proc = subprocess.Popen(
                [bin_path, *spawn_args],
                cwd=state.project_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=1,
            )
        except Exception as e:
            return self._reply(500, {"error": f"resume spawn failed: {type(e).__name__}: {e}"})

        # Reset RunState lifecycle flags for the new process. Same runId,
        # same event log — new process underneath.
        state.proc = proc
        state.done = False
        state.exit_code = None
        state.turn_done = False
        state.append("status", {
            "label": "resumed",
            "sessionId": state.session_id,
        })
        state.append("user_message", {"text": text})

        try:
            proc.stdin.write(_claude_user_frame(text))
            proc.stdin.flush()
        except Exception as e:
            state.append("error", {"message": f"failed to write resume message to stdin: {e}"})

        threading.Thread(target=_drain_stdout, args=(state,), daemon=True,
                         name=f"run-{run_id}-stdout-resumed").start()
        threading.Thread(target=_drain_stderr, args=(state,), daemon=True,
                         name=f"run-{run_id}-stderr-resumed").start()

        return self._reply(200, {"ok": True, "sessionId": state.session_id})

    # ── GET /__history · POST /__history/(undo|redo) ────────────────────────
    # Per-project undo/redo stack. Each entry has a before/ and after/ snapshot
    # of the files touched; restore writes one or the other onto disk.
    def _history_get(self, qs):
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        with HISTORY_LOCK:
            idx = _history_load_index(project_root)
        run_active = False
        try:
            with RUNS_LOCK:
                run_active = any(not s.done for s in RUNS.values())
        except Exception:
            run_active = False
        return self._reply(200, {
            "entries": idx["entries"],
            "cursor":  idx["cursor"],
            "max":     HISTORY_MAX_ENTRIES,
            "runActive": run_active,
        })

    def _history_step(self, qs, direction: str):
        """direction='undo' or 'redo'. On undo we restore the CURRENT entry's
        before/ and decrement cursor. On redo we increment cursor first and
        restore the NEW current entry's after/.
        """
        try:
            project_root = resolve_project_root(qs)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})
        # Refuse stepping only while a run is ACTIVELY producing output — i.e.
        # mid-turn (process alive AND its current turn hasn't finished). Such a
        # run is about to land an atomic history entry, so undo/redo would race
        # it. v2.50 — previously this blocked on `not s.done`, which also caught
        # runs that finished their turn and are idle WAITING FOR THE USER'S
        # REPLY (turnDone=true, done=false). That's the normal resting state of
        # any chat you've talked to — so a single idle chat permanently blocked
        # undo. Only block on genuinely mid-turn runs. Scope to the active
        # project so another project's run doesn't block this one.
        try:
            this_project = os.path.basename(project_root.rstrip("/"))
            with RUNS_LOCK:
                active_runs = [
                    s for s in RUNS.values()
                    if (getattr(s, "project_id", None) in (None, this_project))
                    and not s.done and not getattr(s, "turn_done", False)
                ]
            if active_runs:
                return self._reply(409, {
                    "error": "a run is mid-turn; undo/redo locked until it finishes its turn",
                    "hint": "wait for the agent to finish its current turn, or Stop it",
                    "activeRuns": [getattr(s, "run_id", "?") for s in active_runs],
                })
        except Exception:
            pass
        with HISTORY_LOCK:
            idx = _history_load_index(project_root)
            entries = idx["entries"]; cursor = idx["cursor"]
            if direction == "undo":
                if cursor < 0:
                    return self._reply(409, {"error": "nothing to undo"})
                entry = entries[cursor]
                changed = _history_restore(project_root, entry, "before")
                idx["cursor"] = cursor - 1
            elif direction == "redo":
                if cursor >= len(entries) - 1:
                    return self._reply(409, {"error": "nothing to redo"})
                entry = entries[cursor + 1]
                changed = _history_restore(project_root, entry, "after")
                idx["cursor"] = cursor + 1
            else:
                return self._reply(400, {"error": f"bad direction: {direction!r}"})
            _history_save_index(project_root, idx)
        # v2.50 — notify SSE subscribers so the canvas reloads the restored
        # state immediately. Without this, the editor kept showing the
        # pre-undo state until the file-watcher tick (up to ~1s later) OR
        # until a manual refresh — and a debounced autosave firing in that
        # window could overwrite the restore. Broadcasting now closes the gap.
        try:
            _broadcast_workflow_change(os.path.basename(project_root.rstrip("/")))
        except Exception:
            pass
        return self._reply(200, {
            "ok": True,
            "direction": direction,
            "restored": entry,
            "changedFiles": changed,
            "cursor": idx["cursor"],
        })

    def _reply(self, code, payload):
        # v2.50 — attach X-Request-Id header (and inline into JSON payload as
        # `requestId` when missing) so the browser console + daemon logs can
        # correlate the same request across both sides. Request IDs are
        # assigned at do_POST entry (see do_POST) and stored on self.
        req_id = getattr(self, "request_id", None)
        if req_id and isinstance(payload, dict) and "requestId" not in payload:
            payload = {**payload, "requestId": req_id}
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if req_id:
            self.send_header("X-Request-Id", req_id)
        self.end_headers()
        self.wfile.write(data)


class ReusableThreadingTCP(socketserver.ThreadingTCPServer):
    """Threading server so SSE long-polls don't block other requests.
    daemon_threads ensures Ctrl-C exits cleanly even with open streams."""
    allow_reuse_address = True
    daemon_threads = True

    # v2.35 — suppress the giant traceback Python's HTTPServer prints when
    # the CLIENT closes a connection before/during a request. This happens
    # constantly in normal operation: page reload, EventSource reconnect,
    # AbortController, navigation, browser idle-killing the SSE channel.
    # The default behavior fills the terminal with `ConnectionResetError`
    # + `BrokenPipeError` tracebacks that look catastrophic but actually
    # mean nothing was lost on the server — the client just gave up first.
    # We replace handle_error with a one-liner log for these cases and
    # keep the full traceback only for genuinely unexpected exceptions.
    def handle_error(self, request, client_address):
        import sys, traceback
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
            # Normal — client disconnected. Skip the noise.
            return
        # Anything else, keep the original behavior so real bugs surface.
        print(f"Exception during processing for {client_address}:", flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    # ── Highlighted startup URL banner ──
    # ANSI escapes when stdout is a TTY and NO_COLOR isn't set; plain ASCII
    # box otherwise (CI logs, piped output). Pads to a fixed inner width so
    # the right border lines up. The URL is the load-bearing piece — users
    # were missing it in the noise of endpoint listings.
    _use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    def _ansi(code: str) -> str:
        return code if _use_color else ""
    _C_BOLD = _ansi("\033[1m")
    _C_CYAN = _ansi("\033[36m")
    _C_GREEN = _ansi("\033[32m")
    _C_DIM = _ansi("\033[2m")
    _C_RESET = _ansi("\033[0m")

    def _print_url_banner(url: str, hint=None) -> None:
        # Visible width of the contents, used for box padding. Strip any ANSI
        # so colorisation doesn't break alignment.
        import re as _re
        def _vwidth(s: str) -> int:
            return len(_re.sub(r"\033\[[0-9;]*m", "", s))
        title = f"  ▶  Open in browser:  {_C_BOLD}{_C_CYAN}{url}{_C_RESET}"
        sub   = f"     {_C_DIM}{hint}{_C_RESET}" if hint else None
        # Box width = max content width + 2 padding on each side, but keep
        # within a sensible terminal envelope.
        inner = max(_vwidth(title), _vwidth(sub or ""))
        inner = min(max(inner + 2, 56), 100)
        top    = f"  {_C_GREEN}┌{'─' * inner}┐{_C_RESET}"
        bottom = f"  {_C_GREEN}└{'─' * inner}┘{_C_RESET}"
        def _row(content: str) -> str:
            pad = inner - _vwidth(content)
            return f"  {_C_GREEN}│{_C_RESET}{content}{' ' * pad}{_C_GREEN}│{_C_RESET}"
        print("", flush=True)
        print(top, flush=True)
        print(_row(title), flush=True)
        if sub:
            print(_row(sub), flush=True)
        print(bottom, flush=True)
        print("", flush=True)

    if WORKSPACE_DIR:
        projects = _list_projects()
        print(f"serving install {INSTALL_ROOT}", flush=True)
        if _workspace_env:
            _ws_origin = "TH_WORKSPACE_DIR"
        elif WORKSPACE_DIR == INSTALL_ROOT:
            _ws_origin = "auto (install root = workspace)"
        else:
            _ws_origin = "auto (install parent)"
        print(f"  workspace mode — {WORKSPACE_DIR}  [{_ws_origin}]", flush=True)
        if projects:
            print(f"  {len(projects)} project(s):", flush=True)
            for p in projects:
                print(f"    · {p['id']:<24}  {p['label']}", flush=True)
                # v3.1 — _load_registry call removed. The data.js bootstrap
                # shim used to be auto-upgraded on startup; the lazy
                # migration shim _v31_migrate_data_js (in translate_path) now
                # handles it on the first GET instead, so we don't need
                # eager upgrade per project at boot.
        else:
            print("  no projects found — scaffold one with POST /__projects/new "
                  "or create a subdir with source/ inside", flush=True)
        _print_url_banner(
            f"http://localhost:{PORT}/",
            "add ?project=<id> to scope a specific project",
        )
    else:
        print(f"serving {INSTALL_ROOT}  (single-project mode)", flush=True)
        print("  to enable multi-project: set TH_WORKSPACE_DIR=<path> before launching", flush=True)
        _print_url_banner(f"http://localhost:{PORT}/")
    print(
        "  endpoints: /__save  /__layout  /__workflow\n"
        "             /__agents  /__run  /__runs  /__stream\n"
        "             /__workspace  /__projects  /__projects/new  /__projects/rename  /__projects/delete",
        flush=True,
    )
    # v3.1 — Skill isolation. Spawned `claude` gets `--disable-slash-commands`
    # so user-level commands (~/.claude/commands/) can't auto-load and
    # override the visual-orchestrator pipeline. Auth via macOS Keychain stays
    # intact (no CLAUDE_CONFIG_DIR override).
    print("  agent isolation: spawned `claude` runs with --disable-slash-commands "
          "(user-level slash commands at ~/.claude/commands/ hidden)", flush=True)

    # v3.1.2 — Hook-gate auto-install. The real generation lives in
    # `_ensure_harness_settings()` which is ALSO called at every claude
    # spawn site (so a missing/deleted file self-heals without restarting
    # the daemon). Calling it here at boot is just for the console banner
    # — by the time the first spawn fires, the file would be regenerated
    # anyway.
    _settings_path = _ensure_harness_settings()
    if _settings_path:
        print(f"  hook gate: PreToolUse Write/Edit/MultiEdit routes by path "
              f"to the right family orchestrator (simulation / interactive / "
              f"narrative / visual)", flush=True)
        print(f"    settings: {_settings_path}", flush=True)
    else:
        _hook_path = os.path.join(INSTALL_ROOT, ".claude", "hooks",
                                  "require-orchestrator.sh")
        print(f"  hook gate: hook script missing at {_hook_path}; writes are NOT gated",
              flush=True)
    # If a stale symlink was left over from the earlier CLAUDE_CONFIG_DIR
    # approach, clean it up so it doesn't shadow user state.
    try:
        _stale = os.path.join(INSTALL_ROOT, ".claude", ".claude.json")
        if os.path.islink(_stale):
            os.remove(_stale)
            print("    cleaned up stale .claude.json symlink from earlier attempt", flush=True)
    except OSError:
        pass
    # Surface host-leak diagnostics so 401s from spawned `claude` are easy to
    # trace. See _HOST_LEAK_ENV_VARS for the rationale.
    leaked = [k for k in _HOST_LEAK_ENV_VARS if k in os.environ
              and (k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
                   or not (os.environ[k] or "").strip())]
    if leaked:
        preserve = (os.environ.get("TH_PRESERVE_CLAUDE_ENV") or "").strip()
        action = "PRESERVED (TH_PRESERVE_CLAUDE_ENV=1)" if preserve and preserve != "0" else "stripped before spawn"
        print(f"  note: detected Claude Code host envelope leakage — {action}:", flush=True)
        for k in leaked:
            v = os.environ.get(k, "")
            shown = "<empty>" if not v else (v if len(v) < 24 else v[:20] + "…")
            print(f"    {k}={shown}", flush=True)
        if not preserve or preserve == "0":
            print(
                "  → run `claude login` in a plain Terminal.app shell once so the spawned\n"
                "    CLI can read OAuth credentials from disk (~/.claude/.credentials.json).",
                flush=True,
            )
    _install_shutdown_hooks()
    # v2.23 — auto-replace any stale serve.py holding our port. Without this,
    # the user gets EADDRINUSE every time the previous daemon wasn't cleaned
    # up (common during development: editor reloads, separate launchers, my
    # own restart races). Detect the squatter via lsof, confirm it's another
    # `serve.py`, kill it, wait briefly, then bind. Anything else holding
    # the port (random process) prints a clear error and exits — we never
    # blindly kill unrelated processes.
    def _try_take_port():
        try:
            import socket as _s
            probe = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            probe.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
            try:
                probe.bind(("", PORT))
            finally:
                probe.close()
            return True  # port is free
        except OSError:
            return False
    if not _try_take_port():
        try:
            import subprocess as _sp
            out = _sp.run(["lsof", "-nP", "-iTCP:%d" % PORT, "-sTCP:LISTEN", "-Fp"],
                          capture_output=True, text=True, timeout=3)
            pids = [int(ln[1:]) for ln in (out.stdout or "").splitlines() if ln.startswith("p")]
            squatter_pid = pids[0] if pids else None
            squatter_cmd = ""
            if squatter_pid:
                try:
                    cmd_out = _sp.run(["ps", "-o", "command=", "-p", str(squatter_pid)],
                                      capture_output=True, text=True, timeout=2)
                    squatter_cmd = (cmd_out.stdout or "").strip()
                except Exception:
                    pass
            if squatter_pid and "serve.py" in squatter_cmd and squatter_pid != os.getpid():
                print(f"  port {PORT} held by stale serve.py (pid {squatter_pid}) — killing it", flush=True)
                try:
                    os.kill(squatter_pid, 15)  # SIGTERM
                    # Wait up to 3s for it to exit + release the port
                    for _ in range(30):
                        if _try_take_port(): break
                        import time as _t; _t.sleep(0.1)
                    if not _try_take_port():
                        os.kill(squatter_pid, 9)  # SIGKILL
                        for _ in range(20):
                            if _try_take_port(): break
                            import time as _t; _t.sleep(0.1)
                except ProcessLookupError:
                    pass  # already gone
            elif squatter_pid:
                print(f"  port {PORT} held by another process (pid {squatter_pid}): {squatter_cmd[:120]}", flush=True)
                print(f"  refusing to kill non-serve.py process — free port {PORT} manually then retry", flush=True)
                raise SystemExit(1)
            else:
                print(f"  port {PORT} in use but couldn't identify holder via lsof — retrying anyway", flush=True)
        except Exception as e:
            print(f"  could not auto-clear port {PORT}: {e}", flush=True)
    with ReusableThreadingTCP(("", PORT), H) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("stopping", flush=True)
        finally:
            # Belt-and-suspenders — the signal handlers + atexit already
            # cover SIGTERM/SIGINT, but call directly so an exception path
            # that skips atexit still cleans up.
            _cleanup_subprocesses(reason="main-exit")
