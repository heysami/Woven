"""editor/exports.py — per-asset export bundles.

Given one workflow node + the active project root, copy the asset's files
into a per-project export folder along with:

  • README.md — structure + run-server instructions tuned to the asset kind
  • serve.command / serve.sh / serve.bat — tiny port-fallback helpers
    that probe 8000 → 8009 then a random port, then open the browser.

The output layout is uniform per kind:

  Prototype / runnable container (simulation, interactive-media, narrative-
  experience, game-experience, scrapbook-experience, interactive-polish):
      <bucket>/
          source/<branch>/...
          design-systems/<dsId>/...        (if meta.dsRef set)
          README.md
          serve.command  serve.sh  serve.bat

  Asset · assetKind=html:
      <bucket>/
          source/<branch>/...              (full prototype tree if the html
                                             lives under source/<branch>/)
          —or—
          <basename(path)>                  (single file fallback)
          README.md  serve.command  serve.sh  serve.bat

  Asset · assetKind=html-set:
      <bucket>/
          (every paths[] file, preserving its relative structure)
          README.md  serve.command  serve.sh  serve.bat

  Asset · any other assetKind (image, svg, video, audio, 3d, shader,
  markdown, text) AND every single-file media kind:
      <bucket>/
          resources/<assetKind>/<filename>
          README.md                        (integration snippet, no serve.*)

  Design-system node:
      <bucket>/
          design-systems/<dsId>/...
          README.md

  Container kinds with no exportable artifact (prompt, skill, agent,
  iterator-*, folder, section, ds-brainstorm, color-palette, typography,
  frames, composer, vector-editor, formatted-text, mermaid):
      <bucket>/
          README.md                        (explains the node and points at
                                             what it produces upstream/down-
                                             stream, no files to ship)

Nothing in this module touches the network. Filesystem writes are confined
to <bucket> (= <exportFolder>/<safe-name>__<timestamp>/). The caller is
responsible for resolving project_root + exportFolder + node from
workflow.json; this module is a pure I/O layer over those inputs.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import stat


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\- ]+")


class BucketExistsError(ValueError):
    """Raised by export_node when the caller asks for a specific bucket name
    that already exists and `overwrite` is false. The daemon turns this into
    HTTP 409 so the UI can prompt the user to enable override."""
    def __init__(self, bucket_name: str, bucket_dir: str):
        super().__init__(
            f"a folder named {bucket_name!r} already exists at {bucket_dir!r}"
        )
        self.bucket_name = bucket_name
        self.bucket_dir  = bucket_dir


def safe_bucket_name(label: str, fallback: str = "asset") -> str:
    """Slugify a node label into a folder-name fragment. Spaces are kept
    so a user-typed name like 'Onboarding deck' stays human-readable on
    disk; other unsafe chars collapse to a single dash. Empty → fallback."""
    if not isinstance(label, str):
        label = ""
    s = _SAFE_NAME_RE.sub("-", label).strip(" -")
    return s or fallback


def timestamp() -> str:
    """Local-timezone YYYYMMDD-HHMMSS, used as the bucket-folder suffix so
    repeated exports of the same node don't clobber each other."""
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


# ── serve helpers ────────────────────────────────────────────────────────
# Three port-probing servers that try 8000 → 8009, then a random high port,
# write the chosen port to ./.serve-port, and open the system browser. The
# helper is intentionally stdlib-only — no pip install, no npm install. The
# only assumption is `python3` on PATH (macOS / Linux) or `python` (Windows).
# Identical behavior on every kind that ships these helpers.

_SERVE_PY_TEMPLATE = r'''#!/usr/bin/env python3
"""Tiny static server with automatic port fallback.

Tries 8000 → 8009. If all are taken, asks the OS for a free port. Writes
the chosen port to ./.serve-port and prints the URL. Ctrl-C to stop.

The browser is opened at ENTRY (set by the export pass to the bundle's
entry page — e.g. source/<branch>/index.html or design-systems/<dsId>/
gallery.html). Falls back to the bucket root if ENTRY is empty.
"""
import http.server, os, socket, socketserver, sys, webbrowser

# Entry path the browser opens, relative to the bucket root. Empty string
# means "open the bucket root" (which shows a directory listing if there
# is no index.html at the root — useful for resources/ bundles).
ENTRY = __ENTRY_LITERAL__

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

def _free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()

def _pick():
    for p in range(8000, 8010):
        if _free(p):
            return p
    # All 8000-8009 occupied — let the OS pick.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p

PORT = _pick()
with open(os.path.join(HERE, ".serve-port"), "w", encoding="utf-8") as f:
    f.write(str(PORT))
root_url = f"http://localhost:{PORT}/"
entry_url = root_url + ENTRY.lstrip("/") if ENTRY else root_url
print(f"\n  Serving {HERE}\n  on {root_url}")
if ENTRY:
    print(f"  Opening {entry_url}")
print(f"  (Ctrl-C to stop)\n")

class _Q(http.server.SimpleHTTPRequestHandler):
    # Disable noisy per-request log lines; print errors only.
    def log_message(self, fmt, *args):
        if args and args[0] and str(args[0])[0] in "45":
            sys.stderr.write("%s - - %s\n" % (self.address_string(), fmt % args))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), _Q) as httpd:
    try:
        webbrowser.open(entry_url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
'''

_SERVE_COMMAND = '''#!/usr/bin/env bash
# Double-clickable on macOS — Finder runs .command files in Terminal.
cd "$(dirname "$0")"
exec python3 ./_serve.py
'''

_SERVE_SH = '''#!/usr/bin/env bash
cd "$(dirname "$0")"
exec python3 ./_serve.py
'''

_SERVE_BAT = '''@echo off
cd /d "%~dp0"
where python >nul 2>&1
if %errorlevel%==0 (
    python _serve.py
) else (
    py -3 _serve.py
)
'''


def write_serve_helpers(bucket_dir: str, entry: "str | None" = None) -> None:
    """Drop the four serve.* files into bucket_dir and chmod the unix
    ones so Finder + a fresh terminal can launch them without extra
    steps. Idempotent — overwrites any previous helper.

    `entry` is the path (relative to bucket_dir) the browser should open
    when the server starts — e.g. `source/main/index.html` or
    `design-systems/main/gallery.html`. If omitted, opens the bucket
    root (which falls back to a directory listing when there's no
    index.html at the root)."""
    # Bake the entry literal into _serve.py so the helper has no extra
    # state to read at runtime. Use repr() so backslashes / quotes in
    # paths don't break the literal.
    entry_literal = repr(entry.strip() if isinstance(entry, str) and entry.strip() else "")
    serve_py = _SERVE_PY_TEMPLATE.replace("__ENTRY_LITERAL__", entry_literal)
    files = [
        ("_serve.py", serve_py, 0o755),
        ("serve.command", _SERVE_COMMAND, 0o755),
        ("serve.sh", _SERVE_SH, 0o755),
        ("serve.bat", _SERVE_BAT, 0o644),
    ]
    for name, body, mode in files:
        path = os.path.join(bucket_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        try:
            os.chmod(path, mode)
        except OSError:
            pass


# ── README templates ─────────────────────────────────────────────────────
# One block per node kind. Each receives a dict of facts the dispatcher
# resolves up-front (label, branch, dsRef, files copied, etc.) and returns
# a full Markdown body. They share a common "How to run" footer for the
# kinds that ship serve.* helpers; resource-only kinds get an integration
# snippet instead.


_RUN_FOOTER = """## How to run

This bundle is a plain static site — no build step, no Node, no npm.

### macOS · double-click

Double-click **`serve.command`** in Finder. A terminal opens, the server
starts on the first free port in the 8000-8009 range, and your default
browser opens to `http://localhost:<port>/`.

### macOS / Linux · terminal

```bash
cd "<this-folder>"
./serve.sh
```

### Windows · double-click or terminal

Double-click **`serve.bat`**, or in PowerShell / cmd:

```bat
cd "<this-folder>"
serve.bat
```

### What if port 8000 is already in use?

The helper probes 8000, then 8001, … 8009. If all ten are busy (e.g. you
already have other static servers running) it asks the OS for any free
high port and uses that. The chosen port is printed in the terminal and
also written to `./.serve-port` so a wrapper script can read it back.

### Without the helper · plain `python3`

```bash
cd "<this-folder>"
python3 -m http.server 8000           # then open http://localhost:8000/
# If 8000 is taken:
python3 -m http.server 8080           # or any free port — try 8001, 5173, 5500, …
```

### Stopping the server

`Ctrl-C` in the terminal window.
"""


def _kind_line(kind: str, sub: str = "") -> str:
    if sub:
        return f"- **Kind:** `{kind}` · subKind `{sub}`"
    return f"- **Kind:** `{kind}`"


def readme_prototype(facts: dict) -> str:
    """README for prototype + every runnable-container kind (simulation,
    interactive-media, narrative-experience, game-experience, scrapbook-
    experience, interactive-polish). `facts.branch` is the source slug.
    `facts.dsRef` is the DS id if the prototype references one."""
    label  = facts.get("label") or facts.get("nodeId") or "prototype"
    kind   = facts.get("kind") or "prototype"
    branch = facts.get("branch") or "main"
    dsRef  = facts.get("dsRef")
    files  = facts.get("files") or []
    head = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    # Immersive containers (simulation / interactive-media / narrative-experience
    # / game / scrapbook / interactive-polish) keep their user-facing entry at
    # `source/<branch>/<subfolder>/<assetId>/runtime.html`. Plain prototypes
    # use the branch-root index.html. facts["entry"] is set by the dispatcher
    # when it can resolve the assetId from the node.
    entry_path = facts.get("entry") or f"source/{branch}/index.html"
    meta = (
        f"{_kind_line(kind)}\n"
        f"- **Branch slug:** `{branch}` — the prototype source tree lives at `source/{branch}/`.\n"
        f"- **Entry:** open `{entry_path}` to read the page directly, or run the server (see below).\n"
    )
    if dsRef:
        meta += (
            f"- **Design system:** `{dsRef}` — bundled at `design-systems/{dsRef}/`. "
            "The prototype's HTML/CSS references it via the same relative path it had inside the workspace, "
            "so the export runs standalone (no further linking step).\n"
        )
    else:
        meta += "- **Design system:** none referenced by this prototype.\n"
    structure = """
## Structure

```
./
  source/<branch>/
    index.html               — the prototype's entry
    styles.css               — page-level styles
    *.html  *.css  *.js      — additional pages + assets
  design-systems/<dsId>/      — only present when the prototype references a DS
    DESIGN.md                — the token + component spec
    styles.css               — tokens as CSS variables + base styles
    gallery.html             — every component rendered in one frame
  README.md                  — this file
  serve.command  serve.sh    — port-fallback static server
  serve.bat                  — Windows variant
  _serve.py                  — the actual Python server the helpers call
```

The HTML/CSS/JS uses **relative paths only** — no absolute URLs, no
external CDN dependencies beyond what's already in the page. Anything
fetched from a CDN was loaded at build time and stays loaded at runtime.

## What this is for

For agents and reviewers picking up this bundle:

- This is a **prototype**, not a production codebase. It draws an
  interface but doesn't architect an app. There's no router, no build
  system, no test suite. Edits land directly in the HTML/CSS/JS files.
- If a `design-systems/<id>/` folder is present, treat it as the source
  of truth for tokens and components. Page-level overrides are allowed
  but should be surfaced as candidate-DS-updates when they generalise.
- The page may include inline `<script>` setup helpers Woven added at
  generation time (data hydration, picker overlays, etc.) — these are
  safe to leave in place. They're inert unless the editor is driving.
"""
    file_list = ""
    if files:
        file_list = "\n## Files included\n\n```\n" + "\n".join(files) + "\n```\n"
    return head + meta + structure + file_list + "\n" + _RUN_FOOTER


def readme_html(facts: dict) -> str:
    """README for a standalone html asset node (assetKind=html)."""
    label = facts.get("label") or facts.get("nodeId") or "page"
    entry = facts.get("entry") or "index.html"
    head = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    meta = (
        f"{_kind_line('asset', 'html')}\n"
        f"- **Entry:** `{entry}`\n"
    )
    structure = f"""
## Structure

```
./
  {entry}
  (sibling .css / .js / image files referenced relatively by the HTML)
  README.md
  serve.command  serve.sh  serve.bat  _serve.py
```

Open `{entry}` directly to read it offline, or run the server (below) so
relative `fetch()` / iframe / module URLs resolve correctly.
"""
    return head + meta + structure + "\n" + _RUN_FOOTER


def readme_html_set(facts: dict) -> str:
    """README for assetKind=html-set — multiple HTML files exported as a set."""
    label = facts.get("label") or facts.get("nodeId") or "html-set"
    paths = facts.get("files") or []
    head = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    meta = (
        f"{_kind_line('asset', 'html-set')}\n"
        f"- **Pages:** {len(paths)}\n"
    )
    if paths:
        meta += "\n### Pages included\n\n" + "\n".join(f"- `{p}`" for p in paths) + "\n"
    structure = """
## Structure

```
./
  <every file from the set, preserving relative structure>
  README.md
  serve.command  serve.sh  serve.bat  _serve.py
```
"""
    return head + meta + structure + "\n" + _RUN_FOOTER


def readme_design_system(facts: dict) -> str:
    label = facts.get("label") or facts.get("nodeId") or "design-system"
    ds_id = facts.get("dsRef") or "ds"
    head = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    meta = (
        f"{_kind_line('design-system')}\n"
        f"- **DS id:** `{ds_id}`\n"
        f"- **Folder:** `design-systems/{ds_id}/`\n"
    )
    structure = f"""
## Structure

```
./
  design-systems/{ds_id}/
    DESIGN.md       — token + component spec
    styles.css      — tokens (CSS custom props) + base styles
    gallery.html    — every component rendered together
  README.md
  serve.command  serve.sh  serve.bat  _serve.py
```

`gallery.html` is the human-readable entry — open it in a browser to see
every component side-by-side. `styles.css` is the file any consuming
prototype links via `<link rel="stylesheet" href="…/styles.css">`.
"""
    return head + meta + structure + "\n" + _RUN_FOOTER


_INTEGRATION_SNIPPETS = {
    "image": (
        "Place the file under `resources/image/` and reference it from an HTML page:\n\n"
        "```html\n<img src=\"./resources/image/<filename>\" alt=\"…\">\n```"
    ),
    "svg": (
        "Two ways to use an exported SVG — link or inline:\n\n"
        "```html\n<!-- as a linked image -->\n"
        "<img src=\"./resources/svg/<filename>\" alt=\"…\">\n\n"
        "<!-- inlined so CSS can theme it -->\n"
        "<object data=\"./resources/svg/<filename>\" type=\"image/svg+xml\"></object>\n"
        "```\n\n"
        "For inline SVG that takes its colour from `currentColor`, paste the file's "
        "`<svg>…</svg>` directly into your HTML."
    ),
    "video": (
        "```html\n<video src=\"./resources/video/<filename>\" autoplay muted loop playsinline></video>\n```"
    ),
    "audio": (
        "```html\n<audio src=\"./resources/audio/<filename>\" controls></audio>\n```\n\n"
        "For programmatic playback use the WebAudio API and decode the file via `fetch()`."
    ),
    "3d": (
        "Load the model with [three.js](https://threejs.org/) and the loader matched to its extension "
        "(`GLTFLoader`, `FBXLoader`, `OBJLoader`). The file sits at `./resources/3d/<filename>`."
    ),
    "shader": (
        "The shader is a GLSL fragment program. Mount it on a fullscreen canvas using your favourite micro-runtime "
        "(e.g. [twgl.js](https://twgljs.org/) or raw WebGL2). The file sits at `./resources/shader/<filename>`. "
        "A typical wiring reads it via `fetch()` at startup and compiles it into a single program."
    ),
    "markdown": (
        "Markdown isn't directly browser-renderable. Either:\n\n"
        "- preview it in any markdown viewer (VS Code, Typora, the `marked` CLI), or\n"
        "- render it client-side with [marked](https://marked.js.org/) / "
        "[markdown-it](https://github.com/markdown-it/markdown-it) inside a host HTML page that fetches "
        "`./resources/markdown/<filename>`."
    ),
    "text": (
        "Plain text — open it in any editor, or `fetch('./resources/text/<filename>')` from a host HTML page."
    ),
    "particle-2d": (
        "Single-file canvas-2D / SVG particle module. Reference it from a host HTML page:\n\n"
        "```html\n<canvas id=\"particles\"></canvas>\n"
        "<script type=\"module\" src=\"./resources/particle-2d/<filename>\"></script>\n```"
    ),
    "particle-gl": (
        "WebGL particle system — the module owns its own canvas + GL context. Reference it from a host HTML page:\n\n"
        "```html\n<script type=\"module\" src=\"./resources/particle-gl/<filename>\"></script>\n```"
    ),
    "lottie": (
        "Lottie JSON animation. Pair it with the official player on a CDN (smallest path):\n\n"
        "```html\n<script src=\"https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js\"></script>\n"
        "<lottie-player src=\"./resources/lottie/<filename>\" autoplay loop></lottie-player>\n```"
    ),
    "vector-icon": (
        "Inline the SVG directly inside the HTML so it picks up `currentColor`, or `<img>`-tag it as a file:\n\n"
        "```html\n<img src=\"./resources/vector-icon/<filename>\" alt=\"\" width=\"24\" height=\"24\">\n```"
    ),
    "vector-mark": (
        "Brand marks are best inlined so CSS can theme them and the SVG paths can animate:\n\n"
        "```html\n<!-- inline mode -->\n<div class=\"mark\">…paste <svg>…</svg> here…</div>\n\n"
        "<!-- linked mode (no CSS theming) -->\n<img src=\"./resources/vector-mark/<filename>\" alt=\"Brand\">\n```"
    ),
    "motion": (
        "Hyperframes-flavoured GSAP HTML — a self-contained `.html` that plays standalone. Open it directly, "
        "or embed via an iframe:\n\n"
        "```html\n<iframe src=\"./resources/motion/<filename>\" style=\"border:0;width:100%;aspect-ratio:16/9\"></iframe>\n```"
    ),
}


_INTEGRATION_SNIPPETS["vector"] = _INTEGRATION_SNIPPETS["svg"]


def readme_single_resource(facts: dict) -> str:
    """README for any single-file asset that goes under resources/<kind>/.
    Covers asset.assetKind in {image,svg,video,audio,3d,shader,markdown,text}
    AND every standalone media kind (particle-2d, particle-gl, lottie,
    vector-icon, vector-mark, motion)."""
    label    = facts.get("label") or facts.get("nodeId") or "asset"
    kind     = facts.get("kind") or "asset"
    sub_kind = facts.get("subKind") or kind
    res_kind = facts.get("resourceKind") or sub_kind
    filename = facts.get("filename") or "asset"
    head = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    meta = (
        f"{_kind_line(kind, sub_kind if sub_kind != kind else '')}\n"
        f"- **File:** `resources/{res_kind}/{filename}`\n"
    )
    structure = f"""
## Structure

```
./
  resources/
    {res_kind}/
      {filename}
  README.md
```

The file sits under `resources/<kind>/` so it slots into a typical web
project structure with no path edits — drop the `resources/` folder
next to your existing `index.html` and reference the file with a
relative path.
"""
    integ = _INTEGRATION_SNIPPETS.get(res_kind) or _INTEGRATION_SNIPPETS.get(sub_kind) or (
        "Reference the file from a host HTML page with a relative path."
    )
    body = head + meta + structure + "\n## Integration\n\n" + integ + "\n"
    return body


def readme_no_artifact(facts: dict) -> str:
    """README for node kinds with no exportable file (prompt, skill, agent,
    folder, section, iterator-*, ds-brainstorm, color-palette, typography,
    frames, composer, vector-editor, formatted-text, mermaid)."""
    label = facts.get("label") or facts.get("nodeId") or "node"
    kind  = facts.get("kind") or "node"
    head  = f"# {label}\n\nExported from Woven on {facts.get('exportedAt') or timestamp()}.\n\n"
    meta  = f"{_kind_line(kind)}\n"
    expl  = facts.get("explanation") or (
        f"This node has no file artifact on disk — it carries inline state "
        f"that the editor uses (prompt text, agent conversation, palette swatches, "
        f"typography ramps, mermaid source, etc.). To capture it, copy the node "
        f"itself from `workflow/workflow.json` in the source project rather than "
        f"trying to export a file."
    )
    body = head + meta + "\n## What this is\n\n" + expl + "\n"
    return body


# ── per-kind dispatch ────────────────────────────────────────────────────


# Container kinds whose user-facing artifact lives under source/<branch>/.
_PROTOTYPE_KINDS = {
    "prototype",
    "simulation",
    "interactive-media",
    "narrative-experience",
    "game-experience",
    "scrapbook-experience",
    "interactive-polish",
}

# Single-file media kinds (the node kind itself dictates how to treat it,
# independent of the asset.assetKind unification).
_SINGLE_FILE_MEDIA_KINDS = {
    "particle-2d",
    "particle-gl",
    "lottie",
    "vector-icon",
    "vector-mark",
    "motion",
    "shader",
    "raster-foreground",
    "raster-photo",
    "video",
    "3d",
}

_RESOURCE_BUCKET = {
    "particle-2d":       "particle-2d",
    "particle-gl":       "particle-gl",
    "lottie":            "lottie",
    "vector-icon":       "vector-icon",
    "vector-mark":       "vector-mark",
    "motion":            "motion",
    "shader":            "shader",
    "raster-foreground": "image",
    "raster-photo":      "image",
    "video":             "video",
    "3d":                "3d",
    # asset.assetKind values
    "image":             "image",
    "svg":               "svg",
    "vector":            "svg",   # editor's EXT_TO_ASSET_KIND maps .svg → "vector"
    "audio":             "audio",
    "markdown":          "markdown",
    "text":              "text",
    "html":              "html",       # only used for single-file html fallback
}


# Immersive-container subfolders. simulation / interactive-media /
# narrative-experience / game-experience / scrapbook-experience /
# interactive-polish each park their per-asset tree at
# `source/<branch>/{subfolder}/<assetId>/`, with `runtime.html` as the
# user-facing entry (see editor/app.js WorkflowSimOrInteractiveNode).
# The plain `prototype` kind has no subfolder — its entry sits at
# `source/<branch>/index.html`.
_CONTAINER_SUBFOLDER = {
    "simulation":            ("simulations",   "simId"),
    "interactive-media":     ("interactives",  "imId"),
    "narrative-experience":  ("narratives",    "nxId"),
    "game-experience":       ("games",         "gameId"),
    "scrapbook-experience":  ("scrapbooks",    "sbId"),
    "interactive-polish":    ("polish",        "polishId"),
}


def _node_field(node: dict, *keys: str) -> "str | list | None":
    """Read a node field that may live at the top level OR under inputs/spec.

    The editor (editor/app.js) stores most node-shape fields as TOP-LEVEL
    keys on the node — `node.assetKind`, `node.path`, `node.paths`,
    `node.prototype`, `node.dsId`, etc. A few older / scaffolder code-
    paths store the same fields under `node.inputs.*` or `node.spec.*`.
    This helper checks top-level first, then `inputs`, then `spec`, and
    returns the first non-empty match for any of the supplied keys (in
    order). Used by every per-kind dispatch path so a freshly-built node
    exports the same as one loaded from disk.
    """
    if not isinstance(node, dict):
        return None
    containers = [node, node.get("inputs") or {}, node.get("spec") or {}]
    for k in keys:
        for c in containers:
            if not isinstance(c, dict):
                continue
            v = c.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, list) and v:
                return v
    return None


def _is_exportable_source_path(p) -> bool:
    """An asset's `path` field is exportable when it points inside one of
    the two project-rooted subtrees we ship: `source/<branch>/...` or
    `design-systems/<dsId>/...`. The latter is how the editor surfaces
    DS gallery / spec / token files as assets so they can be picked into
    prototypes; without this, those nodes fall through to a no-artifact
    README even though the file exists on disk."""
    return (
        isinstance(p, str)
        and (p.startswith("source/") or p.startswith("design-systems/"))
    )


def _ds_tree_for_path(path: str) -> "tuple[str, str] | None":
    """If `path` lives under design-systems/<dsId>/..., return
    (dsId, ds_rel_path) where ds_rel_path is the entry's path relative
    to the DS root. Returns None for non-DS paths."""
    if not isinstance(path, str) or not path.startswith("design-systems/"):
        return None
    parts = path.split("/", 2)
    if len(parts) < 3 or not parts[1]:
        return None
    return parts[1], parts[2]


def _resolve_inline_svg_from_boundto(node: dict, project_root: str) -> "str | None":
    """Resolve an `inline-svg:<selector>` asset by reading the bound
    prototype's HTML and extracting the <svg> inside the matching
    element.

    The editor (see app.js, the prototype-iframe scanner) emits asset
    nodes for icons stamped into prototype HTML at a CSS slot — e.g.
    `[data-slot="icon-ticket"]`. These nodes carry no `src` because the
    SVG markup lives in the prototype, not on the node. `boundTo.node`
    points at the prototype node id; `boundTo.surface` is the CSS
    selector inside it.

    Returns the SVG markup string, or None if anything can't be resolved
    (no boundTo, prototype not found, slot not in HTML, no <svg> inside).
    All failures are non-fatal — the caller falls through to a clear
    no-artifact README pointing the user at the prototype.
    """
    bound = node.get("boundTo") if isinstance(node.get("boundTo"), dict) else None
    if not bound:
        return None
    proto_id = bound.get("node")
    surface  = bound.get("surface") or ""
    if not isinstance(proto_id, str) or not isinstance(surface, str):
        return None

    # Find the prototype node in workflow.json so we know which source/<slug>/
    # tree to scan. Tolerate a missing workflow.json — caller already verified
    # project_root exists.
    wf_path = os.path.join(project_root, "workflow", "workflow.json")
    if not os.path.isfile(wf_path):
        return None
    try:
        with open(wf_path, "r", encoding="utf-8") as f:
            wf = json.load(f)
    except (OSError, ValueError):
        return None
    proto = next(
        (n for n in (wf.get("nodes") or [])
         if isinstance(n, dict) and n.get("id") == proto_id),
        None
    )
    if not proto:
        return None
    slug = (proto.get("prototype") or proto.get("branch") or "main")
    if not isinstance(slug, str) or not slug.strip():
        return None
    slug = slug.strip()

    # Pull the slot id out of the selector — supports [data-slot="x"],
    # [data-slot='x'], [data-slot=x], and the id-shortcut #x.
    slot_match = re.search(r'data-slot=["\']?([^"\'\]]+)["\']?', surface)
    if slot_match:
        slot = slot_match.group(1)
        elem_pat = re.compile(
            r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*data-slot=["\']?'
            + re.escape(slot) + r'["\']?[^>]*>(.*?)</\1>',
            re.S,
        )
    else:
        id_match = re.search(r'#([A-Za-z_][\w-]*)', surface)
        if not id_match:
            return None
        slot = id_match.group(1)
        elem_pat = re.compile(
            r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*\bid=["\']?'
            + re.escape(slot) + r'["\']?[^>]*>(.*?)</\1>',
            re.S,
        )

    # Scan every HTML file under source/<slug>/ for the slot.
    branch_root = os.path.join(project_root, "source", slug)
    if not os.path.isdir(branch_root):
        return None
    candidates = []
    for dirpath, dirnames, filenames in os.walk(branch_root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d != "__pycache__"]
        for name in filenames:
            if name.endswith(".html"):
                candidates.append(os.path.join(dirpath, name))
    # Prefer index.html first, then alphabetical — gives the most likely hit
    # before we read the rest.
    candidates.sort(key=lambda p: (0 if os.path.basename(p) == "index.html" else 1, p))
    for html_path in candidates:
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
        except OSError:
            continue
        em = elem_pat.search(html)
        if not em:
            continue
        svg = re.search(r"<svg\b.*?</svg>", em.group(2), re.S)
        if svg:
            return svg.group(0)
    return None


def _read_dsref_from_data_js(project_root: str, branch: str) -> "str | None":
    """Parse editor/data.js for meta.dsRef. Cheap regex — the file is a
    JS literal but the meta block is shallow and stable. Returns None if
    the file is missing or the field absent."""
    p = os.path.join(project_root, "editor", "data.js")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = re.search(r'"dsRef"\s*:\s*"([a-z0-9][a-z0-9-]{0,40})"', text)
    if m:
        return m.group(1)
    m = re.search(r"\bdsRef\s*:\s*['\"]([a-z0-9][a-z0-9-]{0,40})['\"]", text)
    return m.group(1) if m else None


def _safe_copy_tree(src_dir: str, dst_dir: str, files_out: list,
                     bucket_root: "str | None" = None) -> None:
    """Walk src_dir, copy every file into dst_dir preserving structure.
    Appends every written path to `files_out` for the README's `Files
    included` block — relative to `bucket_root` if provided (so the
    listing shows the full per-bucket layout, e.g. `source/main/x.css`
    + `design-systems/luna/styles.css`), else relative to dst_dir.
    Skips dotfiles, __pycache__, node_modules."""
    if not os.path.isdir(src_dir):
        return
    rel_base = bucket_root or dst_dir
    for dirpath, dirnames, filenames in os.walk(src_dir):
        # Prune hidden + skip-listed dirs so os.walk doesn't descend.
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".")
                       and d != "__pycache__"
                       and d != "node_modules"]
        rel_dir = os.path.relpath(dirpath, src_dir)
        out_dir = dst_dir if rel_dir == "." else os.path.join(dst_dir, rel_dir)
        os.makedirs(out_dir, exist_ok=True)
        for name in filenames:
            if name.startswith(".") or name == "Thumbs.db":
                continue
            src = os.path.join(dirpath, name)
            dst = os.path.join(out_dir, name)
            try:
                shutil.copy2(src, dst)
                rel = os.path.relpath(dst, rel_base).replace(os.sep, "/")
                files_out.append(rel)
            except OSError:
                pass


def _resolve_branch_from_node(node: dict, project_root: str) -> "str | None":
    """Container nodes carry their source slug at the TOP LEVEL as
    `node.prototype` (canonical, see editor/app.js `nodePrototype()`),
    with `node.branch` accepted as a legacy alias and `node.inputs.branch`
    accepted for older scaffolder payloads. Asset-style containers may
    also embed the slug inside `node.path` under `source/<branch>/…`.
    Several scaffold conventions also encode the branch in the node id
    (`prototype_<branch>`) or label, so we fall through to those when
    none of the field reads find anything (common for half-scaffolded
    placeholder nodes that haven't been run yet)."""
    branch = _node_field(node, "prototype", "branch")
    if isinstance(branch, str) and branch.strip():
        return branch.strip()
    path = _node_field(node, "path")
    if isinstance(path, str) and path.startswith("source/"):
        parts = path.split("/", 2)
        if len(parts) >= 2 and parts[1]:
            return parts[1]
    nid = (node or {}).get("id") or ""
    for prefix in ("prototype_", "sim_", "im_", "nx_", "game_", "sb_", "polish_"):
        if nid.startswith(prefix):
            candidate = nid[len(prefix):]
            if candidate and os.path.isdir(os.path.join(project_root, "source", candidate)):
                return candidate
            break
    label = (node or {}).get("label") or ""
    if isinstance(label, str) and label.strip():
        candidate = label.strip()
        if os.path.isdir(os.path.join(project_root, "source", candidate)):
            return candidate
    return None


def _resolve_file_from_node(node: dict) -> "str | None":
    """Single-file kinds keep their file at top-level `node.path` (the
    editor's canonical shape — see app.js asset-node construction), with
    `file` / `src` / `url` accepted as aliases and the same keys under
    `node.inputs.*` accepted for older scaffolder payloads. Returns the
    project-relative path or None."""
    v = _node_field(node, "path", "file", "src", "url")
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None


def export_node(
    node: dict,
    project_root: str,
    export_root: str,
    bucket_name: str | None = None,
    overwrite: bool = False,
) -> dict:
    """Top-level entry. Picks a per-kind strategy, writes the bucket,
    returns a structured manifest the caller turns into a JSON response.

    Raises ValueError on any input-shape problem the caller should
    surface as HTTP 400; raises OSError on filesystem problems (caller
    turns into 500). Raises BucketExistsError (a ValueError subclass)
    when a caller-provided `bucket_name` already exists and overwrite
    is false — the daemon surfaces this as HTTP 409 so the UI can ask
    the user to confirm replacement.

    If `bucket_name` is None or empty, the bucket falls back to
    `<safe_label>__<timestamp>` with auto-increment to avoid collisions
    (the historical behavior).
    """
    if not isinstance(node, dict):
        raise ValueError("node must be an object")
    if not isinstance(project_root, str) or not os.path.isdir(project_root):
        raise ValueError("project_root must be an existing directory")
    if not isinstance(export_root, str) or not export_root.strip():
        raise ValueError("export folder is empty — set it via the ⤓ Exports button in the workflow toolbar")
    export_root = os.path.expanduser(export_root)
    if not os.path.isabs(export_root):
        raise ValueError(f"export folder must be an absolute path; got {export_root!r}")
    try:
        os.makedirs(export_root, exist_ok=True)
    except OSError as e:
        raise ValueError(f"could not create export folder {export_root!r}: {e}")
    if not os.access(export_root, os.W_OK):
        raise ValueError(f"export folder is not writable: {export_root!r}")

    kind   = (node.get("kind") or "").strip()
    label  = (node.get("label") or node.get("title") or node.get("id") or kind or "node").strip()
    nodeId = node.get("id") or ""
    # Bucket name resolution:
    #   • Caller supplied a name → slugify, place it directly under export_root.
    #       Collision is a hard error unless overwrite=True (then rmtree first).
    #   • Caller did NOT supply a name → fall back to <safe_label>__<timestamp>
    #     with a 2-digit suffix to dodge a sub-second collision (historical).
    if isinstance(bucket_name, str) and bucket_name.strip():
        bucket_name = safe_bucket_name(bucket_name.strip(), fallback=safe_bucket_name(label))
        bucket_dir  = os.path.join(export_root, bucket_name)
        if os.path.exists(bucket_dir):
            if not overwrite:
                raise BucketExistsError(bucket_name, bucket_dir)
            # Overwrite — rmtree the existing bucket so the fresh export
            # doesn't accidentally merge with stale files. Refuse to delete
            # anything that isn't a directory inside export_root (defense
            # against export_root being a symlink target or the user picking
            # a weird path).
            real_root   = os.path.realpath(export_root)
            real_bucket = os.path.realpath(bucket_dir)
            if not real_bucket.startswith(real_root + os.sep):
                raise ValueError(
                    f"refusing to overwrite {bucket_dir!r}: not inside export folder {export_root!r}"
                )
            if os.path.isdir(bucket_dir) and not os.path.islink(bucket_dir):
                shutil.rmtree(bucket_dir)
            else:
                os.remove(bucket_dir)
        os.makedirs(bucket_dir, exist_ok=False)
    else:
        base_name   = f"{safe_bucket_name(label)}__{timestamp()}"
        bucket_name = base_name
        bucket_dir  = os.path.join(export_root, bucket_name)
        for i in range(1, 20):
            try:
                os.makedirs(bucket_dir, exist_ok=False)
                break
            except FileExistsError:
                bucket_name = f"{base_name}-{i:02d}"
                bucket_dir  = os.path.join(export_root, bucket_name)
        else:
            os.makedirs(bucket_dir, exist_ok=False)  # propagate the final exc

    facts = {
        "nodeId":    nodeId,
        "kind":      kind,
        "label":     label,
        "exportedAt": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    files_written: list = []

    # ── prototype-shaped containers ──────────────────────────────────────
    if kind in _PROTOTYPE_KINDS:
        branch = _resolve_branch_from_node(node, project_root) or "main"
        facts["branch"] = branch
        # Immersive containers carry an additional per-asset id (simId /
        # imId / nxId / gameId / sbId / polishId). Their runtime entry
        # lives under source/<branch>/<subfolder>/<assetId>/runtime.html.
        sub = _CONTAINER_SUBFOLDER.get(kind)
        if sub:
            subfolder, id_field = sub
            asset_id = _node_field(node, id_field, "assetId")
            if isinstance(asset_id, str) and asset_id.strip():
                facts["assetId"] = asset_id.strip()
                facts["entry"]   = (
                    f"source/{branch}/{subfolder}/{asset_id.strip()}/runtime.html"
                )
        src_dir = os.path.join(project_root, "source", branch)
        if not os.path.isdir(src_dir):
            facts["explanation"] = (
                f"This `{kind}` node points at `source/{branch}/`, but that folder "
                "doesn't exist on disk yet — the prototype hasn't been built. Run the "
                "upstream pipeline to populate `source/`, then re-export."
            )
            readme = readme_no_artifact(facts)
            with open(os.path.join(bucket_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme)
            return {
                "ok":         True, "exportPath": bucket_dir, "bucketName": bucket_name,
                "files":      [], "kind": kind, "nodeId": nodeId, "label": label,
                "branch":     branch,
            }
        dst_branch_dir = os.path.join(bucket_dir, "source", branch)
        _safe_copy_tree(src_dir, dst_branch_dir, files_written, bucket_root=bucket_dir)
        # Bundle the design system if one is referenced.
        ds_ref = _read_dsref_from_data_js(project_root, branch)
        if ds_ref:
            ds_src = os.path.join(project_root, "design-systems", ds_ref)
            if os.path.isdir(ds_src):
                ds_dst = os.path.join(bucket_dir, "design-systems", ds_ref)
                _safe_copy_tree(ds_src, ds_dst, files_written, bucket_root=bucket_dir)
                facts["dsRef"] = ds_ref
        facts["files"] = files_written
        # Prototypes open at the branch-root index.html unless the
        # dispatcher set a more specific entry (immersive containers do —
        # see _CONTAINER_SUBFOLDER + assetId resolution above).
        write_serve_helpers(bucket_dir,
                            facts.get("entry") or f"source/{branch}/index.html")
        readme = readme_prototype(facts)

    # ── design-system node ──────────────────────────────────────────────
    elif kind == "design-system":
        # design-system nodes (per editor/app.js) carry the DS id as
        # top-level `node.dsId`. `inputs.id` / `inputs.dsId` /
        # `inputs.path` cover legacy scaffolder payloads. NOTE: we do
        # NOT consult top-level `node.id` here — that's the node
        # identifier (e.g. `n1k2…`), not the design-system id.
        ds_id = ""
        candidates = [
            node.get("dsId"),
            (node.get("inputs") or {}).get("dsId"),
            (node.get("inputs") or {}).get("id"),
            (node.get("inputs") or {}).get("path"),
            (node.get("spec")   or {}).get("dsId"),
        ]
        for c in candidates:
            if isinstance(c, str) and c.strip():
                ds_id = c.strip()
                break
        # Normalise: input may be just an id or a full design-systems/<id> path.
        if ds_id.startswith("design-systems/"):
            ds_id = ds_id.split("/", 2)[1] if "/" in ds_id else ""
        # Fall back to label or node id if inputs are empty (placeholder
        # node that hasn't been wired yet).
        if not ds_id:
            for candidate in [(node.get("label") or "").strip(),
                              (node.get("title") or "").strip(),
                              (nodeId or "").lstrip("_")]:
                if candidate and os.path.isdir(os.path.join(project_root, "design-systems", candidate)):
                    ds_id = candidate
                    break
        ds_src = ds_id and os.path.join(project_root, "design-systems", ds_id)
        if ds_id and ds_src and os.path.isdir(ds_src):
            ds_dst = os.path.join(bucket_dir, "design-systems", ds_id)
            _safe_copy_tree(ds_src, ds_dst, files_written, bucket_root=bucket_dir)
            facts["dsRef"] = ds_id
            facts["files"] = files_written
            # gallery.html is the canonical human-readable entry for a
            # design-system bundle.
            write_serve_helpers(bucket_dir,
                                f"design-systems/{ds_id}/gallery.html")
            readme = readme_design_system(facts)
        else:
            # Empty / unwired DS node — surface a no-artifact README that
            # explains the gap rather than 400ing on every export click.
            facts["explanation"] = (
                "This design-system node is not wired to an on-disk `design-systems/<id>/` "
                "folder yet — either no DS has been built for this project, or the node's "
                "`inputs.id` is empty. Build a DS via Workflow 0, then re-export."
            )
            readme = readme_no_artifact(facts)

    # ── asset node — dispatch on assetKind ──────────────────────────────
    elif kind == "asset":
        # Asset nodes (per editor/app.js) store `assetKind`, `path`, and
        # `paths` as TOP-LEVEL keys on the node. Older scaffolder code-
        # paths put them under `inputs.*`; _node_field() covers both.
        asset_sub_raw = _node_field(node, "assetKind")
        asset_sub = (asset_sub_raw or "").strip().lower() if isinstance(asset_sub_raw, str) else ""
        facts["subKind"] = asset_sub
        path_raw = _node_field(node, "path")
        path = path_raw if isinstance(path_raw, str) else None
        paths_raw = _node_field(node, "paths")
        paths = paths_raw if isinstance(paths_raw, list) else []

        # Inline-content assets carry their bytes/text in `node.src`, or
        # need to be resolved by reading a bound prototype's HTML. Two
        # path schemes the editor produces (see app.js scanner + slot
        # binder):
        #   • `inline:svg/<hash>`  — src = "<svg>…</svg>" markup.
        #   • `inline:canvas/...`  — src = "data:image/png;base64,…".
        #   • `inline-svg:<selector>` — NO src; the SVG lives inside a
        #     bound prototype's HTML at the CSS selector. Resolved by
        #     scanning source/<slug>/*.html for the slot element.
        inline_src = node.get("src") if isinstance(node.get("src"), str) else None
        is_inline_with_src = (
            isinstance(path, str) and path.startswith("inline:")
            and isinstance(inline_src, str) and inline_src.strip()
        )
        is_inline_bound = (
            isinstance(path, str) and path.startswith("inline-svg:")
            and not is_inline_with_src
        )
        if is_inline_bound:
            resolved = _resolve_inline_svg_from_boundto(node, project_root)
            if resolved:
                inline_src = resolved
                is_inline_with_src = True
        is_inline = is_inline_with_src

        # Placeholder / unwired asset node — no path AND no paths AND no
        # inline content — fall through to a no-artifact README instead of
        # 400ing. Common for nodes the user just dragged in but hasn't run yet.
        # Accepts both `source/<branch>/…` and `design-systems/<dsId>/…`
        # paths (the editor exposes DS gallery / spec files as assets).
        has_path  = _is_exportable_source_path(path)
        has_paths = any(_is_exportable_source_path(p) for p in paths)
        if not has_path and not has_paths and not is_inline:
            if is_inline_bound:
                # We tried to resolve via boundTo + HTML scan and failed.
                # Tell the user which prototype + selector to chase.
                bound = node.get("boundTo") or {}
                facts["explanation"] = (
                    "This icon is bound to a prototype slot but the export pass "
                    f"couldn't extract the SVG. Path: `{path}`. Bound prototype: "
                    f"`{bound.get('node') or '?'}`. Selector: `{bound.get('surface') or '?'}`. "
                    "Either the prototype HTML doesn't have an element matching that "
                    "selector with an inner `<svg>`, or the prototype hasn't been built "
                    "yet. Export the bound prototype directly to bundle the icon in "
                    "context, or open the prototype in the editor to verify the slot."
                )
            else:
                facts["explanation"] = (
                    "This asset node has no `path` (or `paths`) pointing at a `source/` "
                    "file yet — it's an empty placeholder waiting for an upstream producer "
                    "to write its file. Run the upstream skill/agent first, then re-export "
                    "and you'll get the bundled file with an integration README."
                )
            readme = readme_no_artifact(facts)

        elif is_inline:
            # Materialise the inline content as a real file under
            # resources/<bucket>/<hash>.<ext>. Branches on inline path
            # prefix to pick the right extension + bucket + write mode.
            sub_hint = path.split(":", 1)[1].split("/", 1)[0] if ":" in path else asset_sub
            # Filename stem: prefer svgHash, then a slot id extracted from
            # an `inline-svg:<selector>` path, then the inline:svg/<hash>
            # tail, then the node id, then "asset". Strip filesystem-
            # hostile characters so the bucket reads cleanly.
            stem = node.get("svgHash")
            if not stem and path.startswith("inline-svg:"):
                bound_surface = ((node.get("boundTo") or {}).get("surface") or "")
                slot_m = re.search(r'data-slot=["\']?([^"\']+?)["\']?[\]\s]', bound_surface + " ")
                if slot_m:
                    stem = slot_m.group(1)
                else:
                    id_m = re.search(r'#([A-Za-z_][\w-]*)', bound_surface)
                    if id_m: stem = id_m.group(1)
            if not stem and "/" in path:
                stem = path.rsplit("/", 1)[-1]
            stem = (stem or nodeId or "asset")
            hash_or_id = _SAFE_NAME_RE.sub("-", str(stem)).strip("-") or "asset"
            data_uri = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", inline_src, re.S)
            if sub_hint == "svg" or asset_sub in ("svg", "vector"):
                ext, bucket, payload, binary = "svg", "svg", inline_src, False
            elif data_uri:
                # Data URI — extract MIME + decoded payload.
                mime = (data_uri.group(1) or "application/octet-stream").lower()
                ext_by_mime = {
                    "image/png": ("png", "image"),
                    "image/jpeg": ("jpg", "image"),
                    "image/webp": ("webp", "image"),
                    "image/gif": ("gif", "image"),
                    "image/svg+xml": ("svg", "svg"),
                    "text/html": ("html", "html"),
                    "text/plain": ("txt", "text"),
                }
                ext, bucket = ext_by_mime.get(mime, ("bin", "asset"))
                if data_uri.group(2):  # ;base64
                    import base64, binascii
                    try:
                        payload = base64.b64decode(data_uri.group(3))
                        binary = True
                    except (binascii.Error, ValueError):
                        payload, binary = inline_src, False
                else:
                    import urllib.parse as _u
                    payload, binary = _u.unquote(data_uri.group(3)), False
            else:
                # Generic inline text — map by assetKind.
                ext_by_kind = {
                    "html": ("html", "html"), "text": ("txt", "text"),
                    "markdown": ("md", "markdown"),
                }
                ext, bucket = ext_by_kind.get(asset_sub, ("txt", "text"))
                payload, binary = inline_src, False
            fname   = f"{hash_or_id}.{ext}"
            rel_dst = os.path.join("resources", bucket, fname)
            abs_dst = os.path.join(bucket_dir, rel_dst)
            os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
            if binary:
                with open(abs_dst, "wb") as f: f.write(payload)
            else:
                with open(abs_dst, "w", encoding="utf-8") as f: f.write(payload)
            files_written.append(rel_dst.replace(os.sep, "/"))
            facts["resourceKind"] = bucket
            facts["filename"]     = fname
            facts["files"]        = files_written
            readme = readme_single_resource(facts)

        elif asset_sub == "html-set":
            # Multi-file set. Copy every entry preserving the relative
            # structure relative to its common prefix.
            valid_paths = [p for p in paths if _is_exportable_source_path(p)]
            if not valid_paths and _is_exportable_source_path(path):
                valid_paths = [path]
            if not valid_paths:
                raise ValueError(f"html-set node has no source/ paths (node {nodeId!r})")
            # Compute common prefix at the directory level for clean copy.
            split_paths = [p.split("/") for p in valid_paths]
            common = []
            for parts in zip(*split_paths):
                if all(p == parts[0] for p in parts): common.append(parts[0])
                else: break
            prefix = "/".join(common[:-1]) if len(common) >= 1 and not all(len(sp) == len(common) for sp in split_paths) else "/".join(common)
            for rel in valid_paths:
                abs_src = os.path.join(project_root, rel)
                if not os.path.isfile(abs_src):
                    continue
                # Strip the common dir prefix; keep file structure beyond it.
                rel_under = os.path.relpath(rel, prefix).replace(os.sep, "/") if prefix and rel.startswith(prefix + "/") else os.path.basename(rel)
                dst = os.path.join(bucket_dir, rel_under)
                os.makedirs(os.path.dirname(dst), exist_ok=True) if os.path.dirname(dst) else None
                shutil.copy2(abs_src, dst)
                files_written.append(rel_under)
            facts["files"] = files_written
            # html-set has no single canonical entry; open the first file
            # so the user lands on something. The README still lists all.
            first_entry = files_written[0] if files_written else ""
            write_serve_helpers(bucket_dir, first_entry)
            readme = readme_html_set(facts)

        elif asset_sub in ("html", "three", "viz") or (
                # Path-extension fallback for assetKinds the editor invents
                # for canvas / three.js / viz scenes that ship as a single
                # .html file but carry a non-html assetKind label.
                isinstance(path, str)
                and path.lower().endswith(".html")
                and asset_sub not in {"text", "markdown", "image", "audio",
                                      "video", "3d", "lottie"}):
            if not _is_exportable_source_path(path):
                raise ValueError(f"html asset node has no source/ or design-systems/ path (node {nodeId!r})")
            abs_src = os.path.join(project_root, path)
            if not os.path.isfile(abs_src):
                # File referenced but not on disk — fall through to a
                # no-artifact README rather than 400ing. Common when an
                # upstream producer hasn't run yet, or the file was
                # deleted out-of-band.
                facts["explanation"] = (
                    f"This `{kind}` (assetKind `{asset_sub}`) node points at `{path}` "
                    "but no file exists at that path on disk. Either the upstream "
                    "producer hasn't written the file yet, or the file was removed "
                    "after the node was created. Re-run the producer or update the "
                    "node's path, then re-export."
                )
                readme = readme_no_artifact(facts)
                with open(os.path.join(bucket_dir, "README.md"), "w", encoding="utf-8") as f:
                    f.write(readme)
                return {
                    "ok":         True, "exportPath": bucket_dir, "bucketName": bucket_name,
                    "files":      files_written, "kind": kind, "nodeId": nodeId,
                    "label":      label,
                }
            # Pick the bundling strategy based on where the HTML lives.
            # Three exclusive cases:
            #   A. design-systems/<dsId>/...  → bundle whole DS tree.
            #   B. source/<branch>/...        → bundle whole branch tree.
            #   C. source/<file>.html        → copy single file alone.
            # Every branch ends with readme + files_written populated; no
            # branch falls through to the next.
            ds_info = _ds_tree_for_path(path)
            parts   = path.split("/", 2)
            if ds_info:
                ds_id, ds_rel = ds_info
                ds_root = os.path.join(project_root, "design-systems", ds_id)
                if os.path.isdir(ds_root):
                    ds_dst = os.path.join(bucket_dir, "design-systems", ds_id)
                    _safe_copy_tree(ds_root, ds_dst, files_written, bucket_root=bucket_dir)
                    facts["dsRef"] = ds_id
                    facts["entry"] = f"design-systems/{ds_id}/{ds_rel}"
                    facts["files"] = files_written
                    write_serve_helpers(bucket_dir, facts["entry"])
                    # Re-use the prototype README template, but mark it
                    # as a DS bundle so the header reads as such.
                    readme = readme_prototype({
                        **facts, "kind": "design-system", "branch": ds_id,
                    })
                else:
                    fname = os.path.basename(path)
                    shutil.copy2(abs_src, os.path.join(bucket_dir, fname))
                    files_written.append(fname)
                    facts["entry"] = fname
                    facts["files"] = files_written
                    write_serve_helpers(bucket_dir, fname)
                    readme = readme_html(facts)
            elif len(parts) >= 3:
                # source/<branch>/<rest>.html — bundle the whole branch.
                branch = parts[1]
                branch_root = os.path.join(project_root, "source", branch)
                if os.path.isdir(branch_root):
                    dst_branch_dir = os.path.join(bucket_dir, "source", branch)
                    _safe_copy_tree(branch_root, dst_branch_dir, files_written, bucket_root=bucket_dir)
                    ds_ref = _read_dsref_from_data_js(project_root, branch)
                    if ds_ref:
                        ds_src = os.path.join(project_root, "design-systems", ds_ref)
                        if os.path.isdir(ds_src):
                            ds_dst = os.path.join(bucket_dir, "design-systems", ds_ref)
                            _safe_copy_tree(ds_src, ds_dst, files_written, bucket_root=bucket_dir)
                            facts["dsRef"] = ds_ref
                    facts["branch"] = branch
                    facts["entry"]  = os.path.relpath(abs_src, os.path.join(project_root, "source", branch)).replace(os.sep, "/")
                    facts["entry"]  = f"source/{branch}/{facts['entry']}"
                    facts["files"]  = files_written
                    write_serve_helpers(bucket_dir, facts["entry"])
                    readme = readme_prototype({**facts, "kind": "prototype"})
                else:
                    fname = os.path.basename(path)
                    shutil.copy2(abs_src, os.path.join(bucket_dir, fname))
                    files_written.append(fname)
                    facts["entry"] = fname
                    facts["files"] = files_written
                    write_serve_helpers(bucket_dir, fname)
                    readme = readme_html(facts)
            else:
                # Single file at source/<file>.html — copy alone.
                fname = os.path.basename(path)
                shutil.copy2(abs_src, os.path.join(bucket_dir, fname))
                files_written.append(fname)
                facts["entry"] = fname
                facts["files"] = files_written
                write_serve_helpers(bucket_dir, fname)
                readme = readme_html(facts)

        else:
            # Single-file resource — image / svg / video / audio / 3d /
            # shader / markdown / text. Goes under resources/<kind>/.
            # Accepts both `source/...` and `design-systems/...` paths.
            if not _is_exportable_source_path(path):
                raise ValueError(
                    f"asset node has no source/ or design-systems/ path "
                    f"(node {nodeId!r}, assetKind={asset_sub!r})"
                )
            abs_src = os.path.join(project_root, path)
            if not os.path.isfile(abs_src):
                facts["explanation"] = (
                    f"This asset (kind `{asset_sub}`) points at `{path}` but no file "
                    "exists at that path on disk. Either the upstream producer hasn't "
                    "written the file yet, or the file was removed after the node was "
                    "created. Re-run the producer or update the node's path, then "
                    "re-export."
                )
                readme = readme_no_artifact(facts)
            else:
                res_kind = _RESOURCE_BUCKET.get(asset_sub) or (asset_sub or "asset")
                fname = os.path.basename(path)
                rel_dst = os.path.join("resources", res_kind, fname)
                abs_dst = os.path.join(bucket_dir, rel_dst)
                os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
                shutil.copy2(abs_src, abs_dst)
                files_written.append(rel_dst.replace(os.sep, "/"))
                facts["resourceKind"] = res_kind
                facts["filename"]     = fname
                facts["files"]        = files_written
                # No serve.* for single-file resources — the README's
                # integration snippet covers usage.
                readme = readme_single_resource(facts)

    # ── single-file media kinds with no `asset` wrapper ─────────────────
    elif kind in _SINGLE_FILE_MEDIA_KINDS:
        path = _resolve_file_from_node(node)
        if not _is_exportable_source_path(path):
            # Placeholder media node — fall back to a no-artifact README
            # rather than 400ing.
            facts["subKind"] = kind
            facts["explanation"] = (
                f"This `{kind}` node has no file on disk yet. Its upstream producer "
                "hasn't written a file to `source/` (or `design-systems/`) — run the "
                "producer first, then re-export."
            )
            readme = readme_no_artifact(facts)
            with open(os.path.join(bucket_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme)
            return {
                "ok":         True, "exportPath": bucket_dir, "bucketName": bucket_name,
                "files":      files_written, "kind": kind, "nodeId": nodeId,
                "label":      label,
            }
        abs_src = os.path.join(project_root, path)
        if not os.path.isfile(abs_src):
            facts["subKind"] = kind
            facts["explanation"] = (
                f"This `{kind}` node points at `{path}` but no file exists at that "
                "path on disk. Re-run the producer or update the node's path, then "
                "re-export."
            )
            readme = readme_no_artifact(facts)
            with open(os.path.join(bucket_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme)
            return {
                "ok":         True, "exportPath": bucket_dir, "bucketName": bucket_name,
                "files":      files_written, "kind": kind, "nodeId": nodeId,
                "label":      label,
            }
        res_kind = _RESOURCE_BUCKET.get(kind) or kind
        fname = os.path.basename(path)
        rel_dst = os.path.join("resources", res_kind, fname)
        abs_dst = os.path.join(bucket_dir, rel_dst)
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
        shutil.copy2(abs_src, abs_dst)
        files_written.append(rel_dst.replace(os.sep, "/"))
        facts["resourceKind"] = res_kind
        facts["filename"]     = fname
        facts["subKind"]      = kind
        facts["files"]        = files_written
        readme = readme_single_resource(facts)

    # ── no-artifact kinds ───────────────────────────────────────────────
    else:
        readme = readme_no_artifact(facts)

    with open(os.path.join(bucket_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    return {
        "ok":          True,
        "exportPath":  bucket_dir,
        "bucketName":  bucket_name,
        "files":       files_written,
        "kind":        kind,
        "nodeId":      nodeId,
        "label":       label,
        "branch":      facts.get("branch"),
        "dsRef":       facts.get("dsRef"),
        "resourceKind": facts.get("resourceKind"),
    }
