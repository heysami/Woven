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

Rule of thumb: when in doubt, `curl $TH_DAEMON_URL/__capabilities` before saying the app can't do something."""
