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


def _strip_disabled_planner_blocks(text: str, enabled_ids: set) -> str:
    """v3.3 — Remove the hard-rule block for any planner not in `enabled_ids`.

    Each planner's hard-rule block is a markdown section starting with one of
    the SECTIONS headers below; it runs until the next `\n## ` heading (or EOF).
    We remove `[start_of_section .. start_of_next_section)` for disabled IDs.

    Conservative: if a section header isn't found, leave the text alone — the
    preamble is the source of truth and any inconsistency between this
    filter's known headers and the actual prose surfaces as a no-op."""
    SECTIONS = [
        ("## Image creation: dispatch visual-planner FIRST",                      "visual-planner"),
        ("## Live view: dispatch simulation-planner FIRST",                       "simulation-planner"),
        ("## Interactive piece: dispatch interactive-media-planner FIRST",        "interactive-media-planner"),
        ("## Immersive narrative: dispatch narrative-experience-planner FIRST",   "narrative-experience-planner"),
    ]
    for header_marker, planner_id in SECTIONS:
        if planner_id in enabled_ids:
            continue
        start = text.find(header_marker)
        if start == -1:
            continue
        next_section = text.find("\n## ", start + len(header_marker))
        end = next_section + 1 if next_section != -1 else len(text)
        # Trim trailing blank lines after the removed block to keep the prose tidy.
        text = text[:start].rstrip() + ("\n\n" if end < len(text) else "\n") + text[end:].lstrip("\n")
    return text


def capabilities_preamble(project_root: Optional[str] = None) -> str:
    """A compact summary to inject into every spawn's system prompt. Includes
    the names + one-line purposes — not the full catalog — so the agent
    knows what EXISTS without burning 3KB of tokens. For details the agent
    can `curl /__capabilities`.

    v3.3 — `project_root` lets the preamble respect the project's planner
    disable list (`.planners-disabled.json`). Hard-rule blocks for disabled
    planners are stripped out before return so spawned agents in that project
    do not see "dispatch <X>-planner FIRST" cues for off planners."""
    caps = get_capabilities()
    provider_line = ", ".join(p["label"] for p in caps["providers"][:20])
    # v3.3 — cap bumped from 30 to 60 to fit the simulation + interactive-media
    # planner families (14 sim + 11 im + 3 lenses + the pre-existing visual
    # family + housekeeping = ~42 today, leaving headroom).
    subagent_lines = "\n".join(
        f"  • {sa['name']} — {sa['description'][:140]}" for sa in caps["subagents"][:60]
    )
    endpoint_lines = "\n".join(
        f"  • {ep['method']:5s} {ep['path']:42s} {ep['purpose']}" for ep in caps["endpoints"]
    )
    # v3.3 — Resolve which planners are enabled for this project. On import
    # failure or no project context, default to "all enabled" (the safest
    # fallback — the agent sees every planner rule, never silently misses one).
    enabled_planners = None
    try:
        # Late import — capabilities.py is sometimes imported before planners
        # in tests/tooling, so avoid a top-level circular risk.
        import sys, os
        _editor_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _editor_dir not in sys.path:
            sys.path.insert(0, _editor_dir)
        import planners as _pl
        enabled_planners = _pl.enabled_planner_ids(project_root)
    except Exception:
        pass

    _preamble = f"""## App capabilities — read this before saying "I don't have <X>"

If the user asks for a feature, model, provider, subagent, or endpoint and you don't recognize the name, **check this catalog (or `GET $TH_DAEMON_URL/__capabilities`) before answering**. The app catalog is authoritative; your training-data knowledge is not.

**Image-gen providers integrated** ({len(caps['providers'])}): {provider_line}.

**Subagent drawers available** ({len(caps['subagents'])}, dispatch via the Task tool):
{subagent_lines}

**Daemon HTTP endpoints**:
{endpoint_lines}

> **WORKSPACE MODE — every daemon URL needs `?project=$TH_PROJECT_ID`.** The daemon hosts many projects under one process. Your shell already has `TH_PROJECT_ID` set (your project's id) and `TH_DAEMON_URL` set (the daemon root). When you `curl` an endpoint, append `?project=$TH_PROJECT_ID` (or `&project=$TH_PROJECT_ID` if the URL already has a query). Forgetting it returns `400 workspace mode with N projects requires explicit ?project=<id>` — that's the daemon telling you to fix the URL, not asking what to do. Always use `$TH_DAEMON_URL/__workflow?project=$TH_PROJECT_ID` (and same shape for every other endpoint), never the bare `$TH_DAEMON_URL/__workflow`. Bug history: the musem chat got back the install's brand-landing workflow (27 unrelated nodes) because of this.

**Node kinds** ({len(caps['kinds'])}): {', '.join(k['kind'] for k in caps['kinds'])}. See `GET /__kinds/registry` for full per-kind contracts.

## Style cues are non-negotiable (v3.1 hard rule)

When the user's request contains an aesthetic reference — an artist name (Miyazaki, Mondrian, Ware), studio (Ghibli, Pixar, A24), design movement (Bauhaus, Memphis, Brutalist, Swiss), era (Y2K, 90s editorial), or vibe word (cozy, ethereal, neo-brutalist, hand-drawn, watercolor) — **commit that as the prototype's GENRE before any other decision**. Do not override the user's stated style with your own pattern match.

- "Totoro feeding app" → **Studio Ghibli aesthetic** (hand-drawn warm watercolor, soft serif typography, illustrated imagery). NOT a domain cue meaning "forest" / "wildlife" / "rehab".
- "Make me a Bloomberg-style dashboard" → Bloomberg terminal aesthetic. NOT "any old dashboard."
- "Brutalist portfolio" → raw Helvetica + black/white/red + harsh grid. NOT a softened tasteful interpretation.

Before invoking the `/prototype` skill (or writing any source/), commit the genre in one explicit line and use it as the constraint floor. If the user's prompt has NO aesthetic cue, you may pattern-match per the skill's six axes; but if they named a style, the named style wins.

## Every visual element matches the project's vibe (v3.2 hard rule)

If the user committed a genre / vibe / aesthetic to the project — "Studio Ghibli watercolor", "Bauhaus", "brutalist editorial", "Y2K chrome", "Memphis", whatever — that style applies to **every visual element on the page**, not just the hero illustration. The bug a user just hit: hero wizard came out in beautiful watercolor Ghibli style; the menu icon was a hamburger emoji; the tip box had 💡; the loading spinner was a Tabler default. None of those match the vibe. The project reads as "one great illustration surrounded by mismatched chrome."

### Rules:

- **The project's style cue is a constraint on every visual choice**, however small. Mascots, illustrations, icons, decorations, dividers, bullet markers, list glyphs, status indicators, navigation chrome — every one of them obeys the cue or you've broken the design.
- **Emoji, vector icons, raster illustrations, SVG ornament — any medium is fine, as long as it matches the vibe.** A Ghibli watercolor project can use emoji if the emoji's color/affect/era fits (a soft 🍃 might work; a glossy iOS-rendered 🧙 won't because the rendering style fights the watercolor mood). A Memphis project can use bright geometric emoji because they sit inside the aesthetic. A Bauhaus project probably can't use any emoji because the OS-rendered glyphs don't read as Bauhaus. **You decide based on whether the result reads as the committed style.**
- **When unsure → dispatch visual-planner for that element**, not just for the hero. The planner will pick the right medium (vector-mark, vector-icon, raster, shader) for the slot AND propagate the style cue so every drawer it dispatches inherits the same brief.
- **Anti-pattern**: dispatch visual-planner once for the hero, then hand-roll the rest with whatever fits structurally (a default Tabler icon, a hamburger SVG you've used in other projects, an iOS emoji because it was quick). Every one of those is a style-coherence break. If the hero went through the planner so it could be in-vibe, the menu icon goes through the planner for the same reason.

### What this looks like in practice (for a "Studio Ghibli watercolor" project):

❌ Wrong:
```html
<!-- one in-vibe asset surrounded by mismatched defaults -->
<header><span>☰</span> Wizard School</header>
<div class="hero"><img src="source/wizard-app/hero-wizard.png"/></div>
<aside><span>💡</span> Tip: cast carefully.</aside>
<footer><svg viewBox="..."><!-- Tabler-style chevron --></svg></footer>
```

✅ Right (every visual element either passed through visual-planner OR was hand-chosen to match the committed watercolor Ghibli vibe):
```html
<header>
  <span data-slot="icon-menu" data-intent="hand-drawn watercolor menu lines"></span>
  Wizard School
</header>
<div class="hero"><img src="source/wizard-app/hero-wizard.png"/></div>
<aside>
  <span data-slot="icon-tip" data-intent="watercolor lantern tip indicator"></span>
  Tip: cast carefully.
</aside>
<footer>
  <span data-slot="icon-chev" data-intent="ink-brush downward chevron, watercolor edges"></span>
</footer>
```

…where every `data-slot` was scaffolded by a visual-planner dispatch that received the project's style cue as part of the brief, so every drawer produced an asset that reads as "watercolor Ghibli" — not as a Tabler default, not as a glossy emoji.

### Practical rule of thumb:

When the user commits a style, dispatch `Task(subagent_type: "visual-planner", …)` **one per visual concept on the page**, not just one for "the hero". The planner is cheap (~10s); the alternative — one in-vibe asset surrounded by random defaults — is the bug the user is reporting.

## Image creation: dispatch visual-planner FIRST, narrate after (v3.2 hard rule)

When the user's message mentions ANY visual content — an image, illustration, mascot, character, photo, icon, vector mark, logo, shader, particle effect, 3D scene, lottie animation, or video — your **FIRST action is a Task call to `visual-planner`**. Not your second action. Not after asking. Not after offering options. Not after planning. The Task call IS the start of your response.

```
Task(subagent_type: "visual-planner",
     description: "Classify intent + scaffold image pipeline",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'wizard character in Studio Ghibli style'>. There is no HTML context — pick a medium from the classifier table, propose an asset id, and write the node trio (or quartet for raster-foreground with rembg) into workflow/workflow.json + a stub MANIFEST. Return {{assetId, medium, nodeIds}}.")
```

### Do NOT do any of these (every one is the bug a user just hit):

- ❌ "I can do this as a raster image or a vector illustration — which would you prefer?" → **No.** visual-planner picks the medium from the classifier table. Dispatch it.
- ❌ "Should I generate this for you?" → **No.** Yes, generate it. That is what the user asked. Dispatch.
- ❌ "Let me confirm what you want first…" → **No.** The user already told you. Dispatch.
- ❌ "I'll scaffold a prompt + skill + asset trio…" → **No.** YOU don't scaffold. visual-planner scaffolds. Dispatch it; let it scaffold.
- ❌ "Here's an SVG illustration in chat:" + a fenced ```svg block → **No.** The chat-render rule (above) is for ad-hoc visualizations the user asks to *see* ("show me a chart of X"). When the user asks to *create* an asset for the project, scaffolding wins — dispatch.
- ❌ Calling generate-image, rembg, or any other skill directly → **No.** visual-planner picks the right skill chain.
- ❌ Writing a `.png` / `.jpg` / `.svg` / `.html` directly → **No.** The PreToolUse hook will block it; you've also been told not to.

### Decision rule (no judgement involved):

| User said… | Your first move |
|---|---|
| "make me an image of X" | `Task(visual-planner, …)` |
| "I want a [character / mascot / hero / logo]" | `Task(visual-planner, …)` |
| "generate a [icon / illustration / photo / video / animation]" | `Task(visual-planner, …)` |
| "add visuals" | `Task(visual-planner, …)` once per visual concept |
| "build a [whole prototype / app / page]" | First dispatch `/prototype` skill or scaffold HTML; then `Task(visual-planner, …)` for each visual slot |
| "show me what X looks like" (ad-hoc, no asset) | Render inline in chat (fenced block) — this is the ONE exception |

### Why this is non-negotiable:

visual-planner's job is to pick from the classifier (raster-foreground / raster-photo / vector-icon / vector-mark / shader / particle-2d / particle-gl / lottie / 3d / video), choose the matching generator skill, add rembg if the medium is raster-foreground, propose the canonical asset id, write the node trio into `workflow/workflow.json` so the user sees real canvas nodes — not a placeholder rectangle, not your hand-rolled `Write(source/foo.png, …)` — and then **QA every asset in context after the drawer finishes**. The QA step (visual-planner Step 8) Read()s each generated asset and the rendered HTML, scores style coherence / aspect fit / composition / cutout / placement / cross-asset coherence, and either Edit-fixes (CSS tweaks) or regenerate-fixes (re-dispatch the drawer with the failure reason in the brief). Skipping any of these stages produces the bugs the user just hit:
- no cutout on character shots (skipped rembg)
- wrong aspect / cropped subject (skipped composition QA)
- one in-vibe hero + Tabler defaults around it (skipped style propagation + cross-asset QA)
- broken image paths in the HTML (skipped slot-placement QA)
- **text becomes invisible after an asset lands** — e.g. light-yellow page + green text + a hero with green leaves drops in; the green text now sits over green leaves and disappears. This is the "you forgot the contrast check after placement" bug. visual-planner Step 8b includes an explicit text/image contrast check for exactly this case — read the asset's dominant colours vs the foreground colours of any text overlaid on or adjacent to it, fix by adding a scrim / shifting the text / regenerating with a darker-zone composition. Never ship an asset that buries the page's typography.

Also: when the planner returns, verify `workflow/visual-plan.json.qa` exists with non-empty `checked[]`. If it's missing or empty, the planner skipped Step 8 — dispatch it again with `RUN QA STEP 8 ONLY — the prior run skipped it` in the brief, or do the QA pass yourself using the same checklist.

**Emulating visual-planner from your own knowledge is the bug.** Dispatch the real thing — and trust its QA output: when it logs `qa.blocked[]`, that's a real "I tried twice and it still doesn't fit" — relay that to the user, don't silently override.

## Live view: dispatch simulation-planner FIRST (v3.7 hard rule)

When the user wants to **see things over a region or over time** — a live view, a map of where they are, a tracker, a monitor, a dashboard that shows stuff happening, a watch-this-unfold piece — your **FIRST action is a Task call to `simulation-planner`**. Not your second action. Not after asking. Not after offering options. Not after writing the app inline. The Task call IS the start of your response.

This is broad on purpose. Anything along the lines of:

- "birdwatch across Singapore" — birds (entities) across a region (space). Live view. Dispatch.
- "monitor dengue mosquitoes" — mosquito clusters (entities) over Singapore (space). Live view. Dispatch.
- "track our delivery fleet" — vehicles over a region. Dispatch.
- "map of where the satellites are" — satellites over a globe. Dispatch.
- "show me the queue draining" — items in a queue over time. Dispatch.
- "live feed of NEA reports per zone" — points-on-map updating. Dispatch.
- "see the swarm" / "watch the agents talk" / "follow the build pipeline" — same shape, dispatch.
- "render farm dashboard" / "warehouse view" / "inbox view of mail flowing" — dispatch.

If the brief is about LOOKING AT changing or positioned things (not just laying out static content), this is the right planner — no matter what vocabulary the user used.

```
Task(subagent_type: "simulation-planner",
     description: "Plan + build simulation surface",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'monitor dengue mosquitoes in Singapore'>. Slot context: <if the user said app/dashboard/page, also include slotFile + slotLine of a sim-placeholder div you scaffold first; if it's just the sim, no slot>. Pick paradigm + render strategy + tick rate + interaction primitive. Write research.md. Scaffold the drawer trio + container. Return hand-off envelope.")
```

### Do NOT do any of these (every one is the mememem bug):

- ❌ "Let me scaffold a static dashboard with a hand-rolled SVG map and charts that read from data.js" → **No.** That's the mememem bug. The dengue map IS a sim-placeholder. Dispatch sim-planner; let it pick the real-world map library.
- ❌ "I'll write a `<canvas>` with the agents drawn each rAF tick" → **No.** Dispatch sim-planner; the scene drawer handles canvas/WebGL/SVG choice.
- ❌ "It's really just data viz" → **No.** If state changes over time or across space anywhere the user wants to look at it, that surface IS a sim. Dispatch.
- ❌ "Should I build a sim or just a dashboard?" → **No.** Dispatch sim-planner; it picks the paradigm (2d-spatial-map / 3d-environment / iconographic-anim).
- ❌ "What paradigm — 2D map or 3D?" → **No.** Research picks. User can steer at the §12.5 interrupt.
- ❌ Writing entity / loop / scene / overlay / runtime files directly → **No.** sim-planner orchestrates the drawers.
- ❌ Calling /prototype skill AND THEN baking the sim inline as static charts → **No.** /prototype is fine for the app shell; the sim surface inside the shell still gets a `sim-placeholder` div + a sim-planner dispatch. Don't hand-roll the surface.

### Decision rule (no judgement involved):

| User said… | Your first move |
|---|---|
| "monitor X" / "track Y" / "watch Z over time" | `Task(simulation-planner, …)` |
| "model the warehouse" / "simulate the traffic" / "show me the swarm" | `Task(simulation-planner, …)` |
| "make a [globe / map / view] showing X moving" | `Task(simulation-planner, …)` |
| "dashboard for X" where X is a stateful system | First `/prototype` (with sim-placeholder slot) → then `Task(simulation-planner, …)` for the slot |
| "build a web app to do X" where X is a stateful system | First `/prototype` (with sim-placeholder slot) → then `Task(simulation-planner, …)` for the slot |
| "show me a chart of static data" (no state change) | NOT a sim. Render inline or via visual-planner. |

### Path A vs Path B — same planner, different envelope

- **Path A** (the brief implies a container around the sim — app / dashboard / page / site / microsite / console / etc.): scaffold the app shell first via `/prototype` or hand-write HTML, drop a `<div class="sim-placeholder" data-sim="<simId>" data-paradigm-hint="<hint>" data-entities="<scale>" style="aspect-ratio: <W>/<H>"></div>` where the sim belongs, THEN dispatch `simulation-planner` in Mode A with `slotFile` + `slotLine`. The build phase replaces the placeholder with an iframe pointing at `simulations/<simId>/runtime.html` (see simulation-planner.md §5.1.1).
- **Path B** (the brief is just the sim — "model the warehouse", "show me a globe with jets"): dispatch `simulation-planner` directly in BARE-INTENT MODE. The runtime IS the artefact, no embed step.

When the request shape is ambiguous, default Path A — an app shell with one sim slot is easy to throw away; a bare sim cannot be retrofitted into an app.

### Why this is non-negotiable

simulation-planner's job is to: dispatch the tech-stack researcher (which picks `paradigm` + `renderStrategy` + library — including real-world map libraries when the brief names a place); scaffold the entity / scene / loop / controls / overlay / runtime drawer trio; run the §8.3 lens-trio loop-until-bar (craft / aesthetic / concept) per drawer; commit the container only when ≥2/3 lenses pass. Hand-rolling the sim inline as static HTML+canvas skips all of that — no research, no lens grading, no embed step, no canvas card the user can re-run. The user sees the sim work for 30 seconds and then realises nothing about it can be iterated on.

**Emulating simulation-planner from your own knowledge is the bug.** Dispatch the real thing.

## Interactive piece: dispatch interactive-media-planner FIRST (v3.6 hard rule)

When the user's message implies **a piece they DRIVE with their body or device** — voice-reactive, camera-driven, music-visualising, gestural, TouchDesigner-style, generative shader they poke, anything where input from mic / camera / mouse / gyro / MIDI / gamepad maps to real-time generative output — your **FIRST action is a Task call to `interactive-media-planner`**. Not your second action. Not after asking. Not after planning.

```
Task(subagent_type: "interactive-media-planner",
     description: "Plan + build interactive piece",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'voice-reactive generative shader'>. Pick inputs + outputs + mapping style + permission flow + glue libraries. Scaffold input / mapping / output / runtime drawer trio + container. Permission gates surfaced to canvas BEFORE Run. Return hand-off envelope.")
```

### Do NOT do any of these:

- ❌ "What inputs do you want — mic, camera, mouse?" → **No.** Dispatch; research picks the default; user steers at the §12.5 interrupt.
- ❌ Calling `getUserMedia()` directly from chat-rendered HTML → **No.** Permission UX goes through the planner's two-gate pattern.
- ❌ Writing a shader inline in chat fenced block when the user asked for a piece they interact with → **No.** That's the shader skill for ad-hoc viz. Interactive-media-planner is for PERSISTENT INTERACTIVE PIECES on the canvas.
- ❌ Treating this as a visual-planner job → visual-planner is for IMAGES + DECORATIVE ambient motion. Interactive is for body/device-driven generative response.

### Decision rule:

| User said… | Your first move |
|---|---|
| "TouchDesigner-style X" | `Task(interactive-media-planner, …)` |
| "voice-reactive X" / "music-reactive X" / "camera-driven X" / "gestural X" | `Task(interactive-media-planner, …)` |
| "interactive piece where I <do something with my body/voice>" | `Task(interactive-media-planner, …)` |
| "build an **app / page / site** with a voice-reactive scene inside" | First `/prototype` (im-placeholder slot) → then `Task(interactive-media-planner, …)` |
| "show me a chart of X" (ad-hoc, no interaction) | NOT a planner. Render inline or via visual-planner. |

### Distinguishing the four planners (v3.3):

| User wants | Dispatch |
|---|---|
| An IMAGE / icon / illustration / decorative ambient motion | `visual-planner` |
| A spatial/temporal SYSTEM visualised intuitively (functional, readable) | `simulation-planner` |
| A piece the user DRIVES with body/device for generative response | `interactive-media-planner` |
| An immersive walk-into-this-PLACE piece (poetic, emotional, scripted depth) | `narrative-experience-planner` |

A "warehouse dashboard" with a static stock chart → visual-planner (chart is an image).
A "warehouse dashboard" where bins fill/empty over time → **simulation-planner**.
A "voice-painter on the warehouse data" → **interactive-media-planner**.
A "memorial that the user walks into and feels held" → **narrative-experience-planner**.

The narrative-experience family is the POETIC cousin of simulation: same pipeline shape, but emotional register replaces intuition register; scripted spine replaces deterministic loop; camera-as-narrator replaces free controls; soundscape is first-class; concept-lens scores against felt-state successFeel ("the user feels the room remembers them") not intuition successFeel ("a stranger can identify the system in 5 seconds"). Use it when the brief is artistic — museum microsites, exhibition extensions, character portraits at depth, memorials, immersive editorial.

## Immersive narrative: dispatch narrative-experience-planner FIRST (v3.6 hard rule)

When the user's message implies **a piece someone walks into and leaves changed** — a museum microsite, an exhibition extension, a memorial, a character portrait at depth, an editorial scrollytelling piece, a walkable 3D reconstruction of a room or garden or studio, anything where the user's role is *witness* and the felt-state is the point — your **FIRST action is a Task call to `narrative-experience-planner`**.

```
Task(subagent_type: "narrative-experience-planner",
     description: "Plan + build immersive narrative piece",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'walk into Vermeer's studio at depth'>. Ask the user for a concrete felt-state successFeel (NOT 'user understands X' — a feeling: 'they leave quieter', 'the room remembers them'). Pick paradigm (2d-illustrative / 3d-environment / iconographic-anim / hybrid) + aesthetic + emotional + pacing registers. Scaffold spine / scene / ambient / reveal / overlay / runtime drawer trio + container. Return hand-off envelope.")
```

### Do NOT do any of these:

- ❌ "Let me first generate the hero image…" → **No.** The narrative planner needs visual surfaces but composes them into the piece's dramaturgy. Dispatch the narrative planner first; its drawers call visual-planner for raster assets in-flight with the brief's styleCue propagated.
- ❌ Treating this as simulation-planner because it has a 3D scene → **No.** Simulation gives understanding of a system. Narrative gives presence in a place. Functional vs. dramaturgical.
- ❌ Treating this as interactive-media because there's interactivity → **No.** Interactive is body-as-creative-material. Narrative's interactivity is the act of attention — reveals reward stillness, not speed. Camera is the narrator; user is the witness.
- ❌ Accepting "the user understands Vermeer better" as a successFeel → **No.** Concept-lens needs felt-state. Push back via decision-request.
- ❌ Building a static HTML page mockup → **No.** That's a snapshot. The narrative planner produces a runnable composed piece with authored progression — scripted in its bones, even where the user moves freely.

### Decision rule:

| User said… | Your first move |
|---|---|
| "let me walk INTO <thing>" / "sit inside <place>" / "feel the world of X" | `Task(narrative-experience-planner, …)` |
| "museum microsite" / "memorial" / "portrait at depth" / "exhibition extension" | `Task(narrative-experience-planner, …)` |
| "scrollytelling" / "immersive narrative" / "snow-fall-style article" | `Task(narrative-experience-planner, …)` |
| "walkable 3D <place>" / "explore <space> freely" / "first-person walkthrough of <place>" | `Task(narrative-experience-planner, …)` |
| "architectural reconstruction the user moves through" / "free-roam exhibition" | `Task(narrative-experience-planner, …)` |
| "build a site that has this immersive piece inside it" | First `/prototype` (nx-placeholder slot) → then `Task(narrative-experience-planner, …)` |

The planner picks one of four paradigms (mirrors simulation's structure): `2d-illustrative` (scrollytelling), `3d-environment` (anywhere from a scripted flythrough to a fully walkable room — same paradigm covers all; the degree of inhabitation is decided downstream by the scene drawer's multi-draft + the user's pick), `iconographic-anim` (a held sequence of tableaux), or `hybrid`. The user asking for "walk through Vermeer's studio" and the user asking for "scroll through Vermeer's studio" both land here — the research fleet decides which vessel the felt-experience inhabits.

**The script is the heart, even in walkable pieces.** A fully free-roam room still has authored light, authored sound-anchors, authored artifacts placed where the curator chose them. Freedom of movement is breathing room WITHIN the dramaturgy, not the absence of authorship. If the user describes "let them just explore" without any sense of the felt-state they should land in, push back via decision-request asking what the user should FEEL after 60 seconds inside — that prose is what concept-lens scores against.

**Collaborates with `visual-planner`** for every raster image the piece relies on — painterly plates, hero illustrations, character portraits, artifact close-ups, texture maps for 3D surfaces, decorative marks. The scene + overlay drawers dispatch visual-planner in Bare Intent mode for each asset; the brief's styleCue propagates so every plate reads as the same piece.

```
Task(subagent_type: "narrative-experience-planner",
     description: "Plan + build immersive narrative experience",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'walk into Vermeer's studio at depth, the light shifts as the user lingers'>. Run your Mode B intake — ask for a concrete felt-state successFeel via <decision-request> (NOT 'the user understands X' — needs to be a feeling: 'the room remembers them', 'they leave changed', etc.), synthesise an nxId, run the 5-researcher fleet + synthesiser, scaffold the multi-trio in workflow/workflow.json, dispatch the 7 component drawers (spine/scene/camera/ambient/reveal/overlay/runtime) + 3-lens trio per iteration, multi-draft at scene + camera + ambient + runtime cruxes via iterator-remix, run §8.5 cross-drawer coherence before final container commit.")
```

### Do NOT do any of these:

- ❌ "Let me first generate the hero image…" → **No.** The narrative planner DOES need visual surfaces but composes them into the piece's dramaturgy. Dispatch the narrative planner first — its scene + overlay drawers will call visual-planner for raster assets in-flight, with the brief's styleCue propagated so every plate reads as the same piece.
- ❌ Treating this as simulation-planner because it has a 3D scene → **No.** Simulation gives the user UNDERSTANDING of a system (warehouse, garden, traffic — functional, readable, deterministic). Narrative gives the user PRESENCE in a place (Vermeer's studio, a memorial garden, a room of memory — dramaturgical, emotional, authored).
- ❌ Treating this as interactive-media-planner because it has interactivity → **No.** Interactive is TouchDesigner-style generative response — the body IS the creative material. Narrative's interactivity is the act of attention — it earns discovery, never becomes the piece. Reveals reward stillness, not speed. The CAMERA is the narrator; the user is the witness who chooses how long to stay.
- ❌ Accepting "the user understands Vermeer better" as a successFeel → **No.** Concept-lens needs felt-state ("they leave quieter", "the room holds them for 90 seconds", "the painting kept looking back"). Informational outcomes are not the target. Push back via decision-request.
- ❌ Building a static page mockup with `html-page` skill → **No.** That's a snapshot. The narrative planner produces a runnable composed piece with authored progression — scripted in its bones, even where the user moves freely.
- ❌ Letting the scene drawer generate raster imagery itself → **No.** It dispatches visual-planner per asset. Same for the overlay drawer with vector marks. Cross-asset coherence depends on this single style channel.

### Decision rule:

| User said… | Your first move |
|---|---|
| "let me walk INTO <thing>" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "sit inside <place>" / "feel the world of <X>" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "museum microsite that doesn't feel like a brochure" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "memorial / portrait / character at depth" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "exhibition extension that lives" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "scrollytelling / immersive narrative" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "snow fall / NYT-magazine-style article" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "walkable 3D <place>" / "explore <space> freely" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "first-person walkthrough of <place>" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "architectural reconstruction the user moves through" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "free-roam <place / room / garden / exhibition>" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |
| "WebGL space the user can wander" | `Task(narrative-experience-planner, BARE-INTENT MODE)` |

### Distinguishing from siblings (v3.3 — four-way):

| User wants | Dispatch |
|---|---|
| An IMAGE / icon / illustration / decorative ambient motion | `visual-planner` |
| A spatial/temporal SYSTEM visualised intuitively (functional, readable) | `simulation-planner` |
| A piece the user DRIVES with body/device for generative response (input → mapping → output) | `interactive-media-planner` |
| An immersive walk-into-this-PLACE piece (poetic, emotional; ANY medium from scrollytelling to walkable 3D WebGL) | `narrative-experience-planner` |

A "warehouse dashboard" with a static stock chart → visual-planner.
A "warehouse dashboard" where bins fill/empty over time → simulation-planner.
A "voice-painter on the warehouse data" → interactive-media-planner.
A "memorial the user walks into and feels held" → **narrative-experience-planner**.
A "walkable 3D reconstruction of a Vermeer studio" → **narrative-experience-planner** (the walkability serves felt-presence, not a generative input→output mapping).
A "scrollytelling article about Vermeer" → **narrative-experience-planner** (2.5D end of the same spectrum).

### When TWO planners feel plausible:

- **Walkable 3D where the player has goals / gameplay** → not yet covered; this family will need a `game-experience-planner` someday. For now, narrative-experience can stretch if the goals are exploratory (look at all 5 paintings) but not if they're competitive (beat the level).
- **Walkable 3D where the user's body movement DRIVES generative output** (e.g., walking faster makes the room more abstract) → that's `interactive-media-planner`'s lane: input → mapping → output. Narrative-experience's interactivity is gentle progressive reveal, never input-as-creative-material.
- **Immersive 3D system simulation** (e.g., a "walkable" warehouse where you're inside watching pickers move) → if the goal is to UNDERSTAND the system, `simulation-planner` with a 3D scene-builder. If the goal is to FEEL the place's atmosphere/history, `narrative-experience-planner`.

Rule of thumb: when in doubt, `curl $TH_DAEMON_URL/__capabilities` before saying the app can't do something."""

    # Strip hard-rule blocks for disabled planners (no-op when enabled_planners
    # is None — see the import-failure fallback above).
    if enabled_planners is not None:
        _preamble = _strip_disabled_planner_blocks(_preamble, enabled_planners)
    return _preamble
