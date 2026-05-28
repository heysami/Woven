"""editor/kinds/capabilities.py — single source of truth for "what this app can do".

The problem this solves: when a user asks an agent "do you have <X>?", today
the agent answers from whatever happens to be in its context window. If the
capability is real (e.g. Quiver AI image-gen, the visual-planner subagent,
the /commit endpoint) but wasn't in the agent's preamble, the agent says "no"
incorrectly. This is the same shape as the kinds-registry problem: the app
HAS the capability, the agent just doesn't know.

This module aggregates four sources into a single CAPABILITIES dict the agent
can consult (via `GET /__capabilities`) or that's summarised into every spawn
preamble:

  1. Image-gen providers + their models  — read from prompts/media-models.js
  2. Subagent drawers (raster-foreground, vector-icon, lottie, …) — read from
     .claude/agents/*.md frontmatter
  3. Daemon endpoints + their purposes
  4. Node kinds — from kinds/registry.py (already canonical)

The agent is told at spawn: "Before saying you don't have a capability, check
/__capabilities — it's authoritative."
"""
from __future__ import annotations
import json
import os
import re
from typing import Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR_DIR = os.path.dirname(_HERE)
_PROTOCOL_ROOT = os.path.dirname(_EDITOR_DIR)


# ── 1. Image-gen providers + skills ── parsed from prompts/media-models.js ──
# media-models.js is a JS file the frontend loads synchronously. We parse it
# with regexes (not a JS interpreter) to avoid runtime dependency on node.
# If the parse breaks because the file shape changes, the test below
# (get_capabilities()['providers']) will return empty; that's the signal to
# update the regex.

_MEDIA_MODELS_PATH = os.path.join(_EDITOR_DIR, "prompts", "media-models.js")

def _parse_media_models() -> dict:
    out = {"providers": [], "skills": [], "imageModels": [], "textModels": []}
    if not os.path.isfile(_MEDIA_MODELS_PATH):
        return out
    try:
        with open(_MEDIA_MODELS_PATH, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return out

    # Providers: each is a block `{ id: "...", label: "...", hint: "...", docsUrl: "..." }`
    # inside the PROVIDERS object. We extract id+label+hint+docsUrl+integrated.
    provider_block_re = re.compile(
        r"id:\s*\"([^\"]+)\"[,\s]+label:\s*\"([^\"]+)\"[^}]*?"
        r"(?:hint:\s*\"([^\"]*)\")?[^}]*?"
        r"(?:docsUrl:\s*\"([^\"]+)\")?[^}]*?"
        r"(?:integrated:\s*(true|false))?",
        re.DOTALL,
    )
    seen_provider_ids = set()
    # First scan: just inside PROVIDERS section
    provider_section = re.search(r"const\s+PROVIDERS\s*=\s*\{(.+?)\n\s*\};", src, re.DOTALL)
    if provider_section:
        section_src = provider_section.group(1)
        for m in provider_block_re.finditer(section_src):
            pid, label, hint, docs, integ = m.group(1), m.group(2), m.group(3) or "", m.group(4) or "", m.group(5) or ""
            if pid in seen_provider_ids: continue
            seen_provider_ids.add(pid)
            out["providers"].append({
                "id":         pid,
                "label":      label,
                "hint":       hint,
                "docsUrl":    docs,
                "integrated": (integ == "true") if integ else None,
            })

    # Image models: `{ id: "...", provider: "...", label: "...", hint: "...", caps: [...], integrated: ... }`
    image_model_re = re.compile(
        r"\{\s*id:\s*\"([^\"]+)\"\s*,\s*provider:\s*\"([^\"]+)\"\s*,\s*label:\s*\"([^\"]+)\"\s*,"
        r"[^}]*?caps:\s*\[([^\]]*)\][^}]*?(?:integrated:\s*(true|false))?[^}]*?\}",
        re.DOTALL,
    )
    seen_model_ids = set()
    for m in image_model_re.finditer(src):
        mid, prov, label, caps_str, integ = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5) or ""
        if mid in seen_model_ids: continue
        seen_model_ids.add(mid)
        caps = [c.strip().strip('"') for c in caps_str.split(",") if c.strip()]
        out["imageModels"].append({
            "id":         mid,
            "provider":   prov,
            "label":      label,
            "caps":       caps,
            "integrated": (integ == "true") if integ else None,
        })

    # Skills: each is a top-level object with `{ id: "...", ... }` inside a SKILLS-shaped block.
    # Look for entries with explicit modelsFilter / modelKind keys (rembg, upscale, llm, describe, generate-image).
    skill_block_re = re.compile(
        r"\{\s*id:\s*\"([^\"]+)\"[^}]{0,800}\}",
        re.DOTALL,
    )
    for m in skill_block_re.finditer(src):
        block = m.group(0)
        # Heuristic: it's a skill if the block has modelsFilter OR provider:"local" OR a model: "..." key
        if "modelsFilter" in block or "modelKind" in block or 'provider: "local"' in block:
            sid = m.group(1)
            # Avoid double-listing providers / image models we already captured
            if sid in seen_provider_ids: continue
            if sid in seen_model_ids: continue
            out["skills"].append({"id": sid, "snippet": block[:200].replace("\n", " ")})

    return out


# ── 2. Subagent drawers ── scanned from .claude/agents/*.md frontmatter ──

def _scan_subagents() -> list:
    """Walk .claude/agents/*.md, extract `name:` + `description:` from frontmatter."""
    out = []
    agents_dir = os.path.join(_PROTOCOL_ROOT, ".claude", "agents")
    if not os.path.isdir(agents_dir):
        return out
    for fn in sorted(os.listdir(agents_dir)):
        if not fn.endswith(".md"): continue
        path = os.path.join(agents_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read(2000)        # first 2KB enough for frontmatter
        except Exception:
            continue
        # YAML-ish frontmatter between two `---` lines
        fm_match = re.match(r"^---\s*\n(.+?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        name_m = re.search(r"^name:\s*(.+?)$", fm, re.MULTILINE)
        desc_m = re.search(r"^description:\s*(.+?)(?:\n[a-z]+:|\Z)", fm, re.MULTILINE | re.DOTALL)
        tools_m = re.search(r"^tools:\s*(.+?)$", fm, re.MULTILINE)
        if not name_m: continue
        name = name_m.group(1).strip()
        desc = (desc_m.group(1) if desc_m else "").strip().replace("\n", " ")[:300]
        tools = (tools_m.group(1) if tools_m else "").strip()
        out.append({"name": name, "description": desc, "tools": tools, "file": f".claude/agents/{fn}"})
    return out


# ── 3. Daemon HTTP endpoints (curated; the actual list is in serve.py routing) ──

def _daemon_endpoints() -> list:
    return [
        {"method": "GET",  "path": "/__healthz",            "purpose": "Liveness probe — lockless, <5ms"},
        {"method": "GET",  "path": "/__workspace",          "purpose": "Workspace mode + default project id"},
        {"method": "GET",  "path": "/__projects",           "purpose": "Enumerate every project"},
        {"method": "POST", "path": "/__projects/new",       "purpose": "Scaffold a new project"},
        {"method": "GET",  "path": "/__workflow",           "purpose": "Get the canvas (nodes + edges + projections)"},
        {"method": "POST", "path": "/__workflow",           "purpose": "Save the canvas (full or partial)"},
        {"method": "GET",  "path": "/__workflow/events",    "purpose": "SSE stream: workflow-changed / asset-changed events"},
        {"method": "POST", "path": "/__workflow/node/<id>/run",    "purpose": "Dispatch one node (skill/agent)"},
        {"method": "POST", "path": "/__workflow/node/<id>/status", "purpose": "Patch runStatus/text on a node"},
        {"method": "POST", "path": "/__workflow/node/<id>/commit", "purpose": "Atomic producer commit — outputs + files + status, all-or-nothing"},
        {"method": "POST", "path": "/__run",                "purpose": "Spawn an agent subprocess (freeform / per-node)"},
        {"method": "GET",  "path": "/__runs",               "purpose": "Enumerate active + recent runs"},
        {"method": "GET",  "path": "/__stream?runId=<id>",  "purpose": "SSE stream of agent events"},
        {"method": "POST", "path": "/__run/<id>/stop",      "purpose": "Stop a running agent (SIGTERM)"},
        {"method": "POST", "path": "/__run/<id>/resume",    "purpose": "Respawn a stopped agent with --resume sessionId (preserves conversation)"},
        {"method": "GET",  "path": "/__kinds/registry",     "purpose": "Per-kind contracts: inputs, outputs, dispatch, fanOut"},
        {"method": "GET",  "path": "/__kinds/reconcile",    "purpose": "Drift detection across workflow.json vs disk"},
        {"method": "GET",  "path": "/__capabilities",       "purpose": "This catalog — what the app can do"},
        {"method": "GET",  "path": "/__design_system",      "purpose": "Read DS metadata + token files"},
        {"method": "POST", "path": "/__design_system",      "purpose": "Write a DS trio (vars/primitives/index)"},
        {"method": "POST", "path": "/__decision/<id>",      "purpose": "Persist a checkpoint pick (DECISION_<id>.json)"},
    ]


# ── 4. Node kinds — delegate to registry.py ──

def _node_kinds() -> list:
    try:
        from .registry import KINDS
    except Exception:
        return []
    out = []
    for k, contract in KINDS.items():
        out.append({
            "kind":         k,
            "title":        contract.get("title", k),
            "category":     contract.get("category", ""),
            "dispatch":     contract.get("dispatch", ""),
            "openEnded":    bool(contract.get("openEnded")),
            "outputsRoot":  contract.get("outputsRoot"),
            "fanOut":       (contract.get("fanOut") or {}).get("kind"),
        })
    return out


# ── Public API ────────────────────────────────────────────────────────────

def get_capabilities() -> dict:
    """Aggregate every source into one snapshot. Cheap enough to call per
    request — file I/O against a handful of small files. No caching."""
    return {
        "version":         "1",
        "summary":         "Canonical catalog of what this app supports. If the user asks about something not listed here, it genuinely isn't integrated.",
        "providers":       _parse_media_models().get("providers", []),
        "imageModels":     _parse_media_models().get("imageModels", []),
        "skills":          _parse_media_models().get("skills", []),
        "subagents":       _scan_subagents(),
        "endpoints":       _daemon_endpoints(),
        "kinds":           _node_kinds(),
    }


def capabilities_preamble() -> str:
    """A compact summary to inject into every spawn's system prompt. Includes
    the names + one-line purposes — not the full catalog — so the agent
    knows what EXISTS without burning 3KB of tokens. For details the agent
    can `curl /__capabilities`."""
    caps = get_capabilities()
    provider_line = ", ".join(p["label"] for p in caps["providers"][:20])
    subagent_lines = "\n".join(
        f"  • {sa['name']} — {sa['description'][:140]}" for sa in caps["subagents"][:30]
    )
    endpoint_lines = "\n".join(
        f"  • {ep['method']:5s} {ep['path']:42s} {ep['purpose']}" for ep in caps["endpoints"]
    )
    return f"""## App capabilities — read this before saying "I don't have <X>"

If the user asks for a feature, model, provider, subagent, or endpoint and you don't recognize the name, **check this catalog (or `GET $TH_DAEMON_URL/__capabilities`) before answering**. The app catalog is authoritative; your training-data knowledge is not.

**Image-gen providers integrated** ({len(caps['providers'])}): {provider_line}.

**Subagent drawers available** ({len(caps['subagents'])}, dispatch via the Task tool):
{subagent_lines}

**Daemon HTTP endpoints**:
{endpoint_lines}

**Node kinds** ({len(caps['kinds'])}): {', '.join(k['kind'] for k in caps['kinds'])}. See `GET /__kinds/registry` for full per-kind contracts.

Rule of thumb: when in doubt, `curl $TH_DAEMON_URL/__capabilities` before saying the app can't do something."""
