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
        ("## Image creation: dispatch visual-planner FIRST",                       "visual-planner"),
        ("## Simulation surfaces: dispatch simulation-planner FIRST",              "simulation-planner"),
        ("## Interactive pieces: dispatch interactive-media-planner FIRST",        "interactive-media-planner"),
        ("## Narrative experiences: dispatch narrative-experience-planner FIRST",  "narrative-experience-planner"),
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

## Simulation surfaces: scaffold-then-planner, the visual-planner pattern (v3.4 hard rule)

When the user wants to **see a system whose parts have state and change** — *whatever the parts are made of* — there are **TWO paths**, and you MUST pick the right one based on whether the user is asking for a *whole app* OR for *just the simulation*. This mirrors visual-planner's split exactly.

### Path A — "build an app / dashboard / page / tool / site that does X"  (the bzzzzz case)

If the user's message contains framing words like **app, web app, dashboard, page, site, tool, monitor, monitoring tool, tracker, viewer, system, platform, prototype** alongside the system they want visualised, the flow is THREE steps — exactly parallel to how visual-planner sits inside a prototype build:

1. **FIRST — scaffold the app shell.** Dispatch the `/prototype` skill (or scaffold the app HTML+CSS+JS into `source/<branch>/` yourself if `/prototype` doesn't fit). The shell has pages, navigation, layout, copy, the chrome — everything that makes it feel like an app.
2. **SECOND — add the placeholder + brief the planner.** If `/prototype` didn't already drop one in, hand-edit the relevant source page to insert a `<div class="sim-placeholder" data-sim="<simId>" data-paradigm-hint="<hint>" data-entities="<scale>" style="aspect-ratio: <W>/<H>"></div>` exactly where the simulation belongs (main panel, sidebar widget, full-bleed hero — wherever the user's intent puts it). Then dispatch `simulation-planner` with the slot info in Mode A:
   ```
   Task(subagent_type: "simulation-planner",
        description: "Plan + build sim for slot <simId>",
        prompt: "Mode A envelope: slotFile=source/<branch>/<page>.html, slotLine=<line of placeholder div>, simId=<simId>, branch=<branch>, projectRoot=<absolute project root>. The placeholder is <div class='sim-placeholder' data-sim='<simId>' data-paradigm-hint='<hint>' data-entities='<scale>' style='aspect-ratio: <W>/<H>'>. User's intent: <verbatim>. successFeel: <ask user if vague>. Run §2 research fleet → §3 user steerage → §4 scaffold drawers → §5 hand-off envelope. Per §5.1.1: the build phase (which I drive) will replace the placeholder with the iframe embed after runtime.html is committed.")
   ```
3. **THIRD — drive the build + embed.** After the planner returns its hand-off envelope, YOU drive the build phase per `bp_simulation_build` preamble — dispatch drawers, run lens trios, commit container. The container commit MUST include the embed step (sim-planner playbook §5.1.1): read the slot file, replace the placeholder div with the iframe embed below, write back. Without this step the runtime exists but isn't IN the app.
   ```html
   <div class="sim-mount" data-sim="<simId>" style="aspect-ratio: <W>/<H>; width:100%;">
     <iframe
       src="simulations/<simId>/runtime.html"
       style="width:100%; height:100%; border:0; display:block; aspect-ratio: <W>/<H>;"
       title="<simId> simulation"
       loading="lazy">
     </iframe>
   </div>
   ```
   (iframe src is relative to the slot file's directory — `source/<branch>/<page>.html` + `simulations/<simId>/runtime.html` resolves to the right runtime path.)

This is the **visual-planner pattern**. The app exists; the planner is a delegated subprocess for the sim slot; the build phase wires the runtime back into the app. The simulation is NEVER the whole artefact when the user asked for an app.

Repeat steps 2+3 per `<simId>` — multiple sims in one app are normal (e.g. a dashboard with a fleet map + a queue depth viz + a heat field).

### Path B — "model / simulate / show me JUST the X" (no app shell, just the sim itself)

If the user asks for the simulation as the artefact itself — "model the warehouse for me", "make me a swarm of agents", "show me how the traffic flows" — with NO app/dashboard/page framing, then dispatch `simulation-planner` in BARE-INTENT MODE directly. The runtime IS the artefact. There's no app to embed it in.

```
Task(subagent_type: "simulation-planner",
     description: "Plan + build standalone simulation",
     prompt: "BARE-INTENT MODE. The user wants: <one-line intent>. No app shell — runtime.html IS the artefact. Run your Mode B intake, etc.")
```

### Disambiguation rule (when in doubt)

If the user says BOTH "I want X simulation" AND uses an app-framing word, **Path A wins**. The default for ambiguous requests is Path A — apps are easy to throw away if the user only wanted the bare sim, but a bare sim with no surrounding app cannot be retrofitted into an app without rebuilding.

### The abstract pattern (this is what the simulation trigger is, not a keyword list)

A simulation surface — wherever it lives, app slot or standalone — is anything with:

### The abstract pattern (this is what the trigger is, not a keyword list)

A simulation surface is anything with:

1. **Entities** — discrete parts of the thing. Could be physical (bins, vehicles, animals, people), digital (agents, requests, messages, tasks, signals), conceptual (ideas in a process, items in a queue, branches of a decision), informational (records, events, transactions), biological (cells, organisms, populations), or compositional (modules in a pipeline, stages in a workflow).
2. **State** — each entity has attributes (position, status, level, score, age, health, payload, location, relationship to others) that hold values at a moment.
3. **Change or interaction** — those attributes evolve over time, OR the entities transform each other, OR they move through a structure, OR they pass things between themselves, OR they respond to inputs / events / each other.
4. **A wish to see it happen** — the user wants the SYSTEM, not a static snapshot of it. They want to watch the bins fill, the agents talk, the requests propagate, the queue drain, the pipeline digest, the populations shift, the signals flow, the energy redistribute. Some kind of *temporal or relational unfolding* is the heart of the brief.

If those four properties are present, this is the right planner — regardless of vocabulary. The user might say "monitoring tool", "dashboard", "visualization", "interactive demo", "explorer", "app to see", "thing that shows me how X works", "agent network", "process pipeline", "information flow", "ecosystem", "swarm", "feedback loop", "supply chain", "queue depth", "render farm", "neural-network-style visualization of <abstract thing>", "show how X talks to Y over time" — same answer.

### Range of what this covers (illustrative — not exhaustive, not authoritative)

The vocabulary is deliberately wide:

- **Physical / spatial**: warehouse stock + pick paths, garden, traffic, kitchen mid-service, power grid, aquarium, hospital triage, shift schedules.
- **Population / ecological**: disease vectors over a geography, animal/insect/plant populations, ecosystem dynamics.
- **Asset / fleet**: vehicles, drones, satellites, sensors — wherever they are, however they move.
- **Process / pipeline**: build systems, render farms, ETL pipelines, manufacturing lines, queue processors, batch jobs digesting through stages.
- **Agent / multi-actor**: agents passing information to each other, an org's people doing work and handing off, mailing list / inbox traffic, a multi-agent system with delegations, a swarm.
- **Network / flow**: information flow through a graph, packets through a topology, money through markets, energy through a grid, signals through a feedback loop, narratives spreading through groups.
- **Computational / abstract**: a neural network's activations, a memory hierarchy, a cache eviction policy, a consensus protocol, anything with stateful nodes interacting.
- **Domain-specific**: scientific simulations (cell biology, climate, fluid), engineering systems (traffic, logistics), social systems (voting, polarization, diffusion), economic systems (market microstructure, supply chains).

If the user names something that *looks like a system with stateful parts that interact or change*, you dispatch this planner. The 4-paradigm research fleet decides downstream how to represent it — spatial map, 3D environment, iconographic anim, hybrid — based on the system's actual cognitive model. Don't pre-decide the representation from the trigger; that's the planner's job.

### Do NOT do any of these:

- ❌ "Should I scaffold a simulation for you?" → **No.** Yes. Dispatch.
- ❌ "What paradigm do you want — 2D map, 3D environment, or iconographic?" → **No.** Research fleet decides; user can steer at the §12.5 interrupt.
- ❌ "Let me first build out a PRD…" → **No.** Bare Intent mode bypasses onboarding.
- ❌ Writing entity / loop / scene / overlay / runtime files directly → **No.** simulation-planner orchestrates the drawers.
- ❌ Inlining `<canvas>` + raw simulation JS into a source page → **No.** That's the wrong family (visual-planner's `canvas-gen` skill is for AMBIENT decoration, not entity-state simulations).
- ❌ **Going to Path B when the user said "app".** This is the bzzzzz bug. If the user typed "generate a web app to monitor X", the answer is Path A: scaffold the app first, then dispatch the planner for the slot. The simulation is NOT the app.
- ❌ Dispatching the planner before any app shell exists in Path A. The planner expects a `sim-placeholder` slot in source/; without one, the runtime.html has nowhere to live and the user ends up with a standalone sim instead of an app — the exact bug we are fixing.

### Decision rule:

| User said… | Path | First move |
|---|---|---|
| "generate a **web app** to monitor X" | **A** | `/prototype` (with sim-placeholder slot) → then `Task(simulation-planner)` for the slot |
| "build a **dashboard** that tracks Y" | **A** | `/prototype` → then `Task(simulation-planner)` per sim slot |
| "build a **page / site / tool / system** that shows Z" | **A** | `/prototype` → then `Task(simulation-planner)` per sim slot |
| "build a **prototype / monitor / viewer** for X" | **A** | `/prototype` → then `Task(simulation-planner)` per sim slot |
| "model the warehouse for me" (no app framing) | **B** | `Task(simulation-planner, BARE-INTENT MODE)` directly |
| "simulate <real-world system>" (no app framing) | **B** | `Task(simulation-planner, BARE-INTENT MODE)` directly |
| "I want to SEE how <system> works" (no app framing) | **B** | `Task(simulation-planner, BARE-INTENT MODE)` directly |
| "show me where <Y> are right now" (no app framing) | **B** | `Task(simulation-planner, BARE-INTENT MODE)` directly |

## Interactive pieces: scaffold-then-planner, same as simulation (v3.4 hard rule)

When the user's message mentions a **distinct creative or playful interactive piece** — TouchDesigner-style, voice-reactive, camera-driven, music-visualising, generative shader they can poke, gestural canvas, anything where THE USER'S BODY/DEVICE becomes a creative material and the OUTPUT is real-time generative response — same two-path rule as simulation.

### Path A — "build an app / page / site that has this interactive piece in it"

The user wants the interactive piece embedded in an app. First scaffold the app via `/prototype` (or hand-write the HTML), writing a `<div class="im-placeholder" data-im="<imId>" data-inputs="<csv>" data-outputs="<csv>" data-mapping="<style>" style="aspect-ratio: <W>/<H>"></div>` at the slot. Then dispatch `interactive-media-planner` per imId.

### Path B — "make me JUST the interactive piece"

The user wants the piece itself, no app shell. Dispatch `interactive-media-planner` in BARE-INTENT MODE directly. The piece IS the artefact.

```
# Path B example
Task(subagent_type: "interactive-media-planner",
     description: "Plan + build interactive piece",
     prompt: "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'voice-reactive generative shader'>. Run your Mode B intake — ask for the concrete successFeel + propose default inputs/outputs/mappingStyle via <decision-request>, synthesise an imId, run the 5-researcher fleet + synthesiser, scaffold the multi-trio, dispatch input/mapping/output drawers + runtime composer + lens trio + cross-drawer coherence review per playbook §5/§6. Permission gates surfaced to canvas BEFORE Run.")
```

### Disambiguation (same as simulation)

App-framing words ("app", "page", "site", "dashboard") → Path A. Pure piece-framing ("make me a voice-reactive shader", "I want a TouchDesigner-style piece") → Path B. If ambiguous, default to Path A — easier to throw away than rebuild.

### Do NOT do any of these:

- ❌ "What inputs do you want — mic, camera, mouse?" → **No** to gate-keep. Yes to ASK after research synthesis when the planner emits its §12.5 interrupt with a proposed set. Don't substitute your judgement.
- ❌ Calling `getUserMedia()` directly from chat-rendered HTML → **No.** Permission UX goes through the planner's two-gate pattern.
- ❌ Writing a shader inline in chat → **Use shader skill for ad-hoc visualisation in chat (triple-backtick `shader` fenced block). Use interactive-media-planner when the user wants a PERSISTENT INTERACTIVE PIECE on the canvas they can interact with.**
- ❌ Treating this as a visual-planner job → visual-planner is for IMAGES + DECORATIVE ambient motion. Interactive-media-planner is for surfaces the user DRIVES with their body/device.
- ❌ Path B when the user said "app" → same bzzzzz bug, same fix: Path A.

### Decision rule:

| User said… | Path | First move |
|---|---|---|
| "build an **app / page / site** with a voice-reactive scene" | **A** | `/prototype` (im-placeholder slot) → `Task(interactive-media-planner)` |
| "build an **interactive demo / installation / portfolio** featuring X" | **A** | `/prototype` (im-placeholder slot) → `Task(interactive-media-planner)` |
| "TouchDesigner-style <X>" (no app framing) | **B** | `Task(interactive-media-planner, BARE-INTENT MODE)` |
| "voice-reactive <X>" / "music-reactive <X>" / "camera-driven <X>" (no app framing) | **B** | `Task(interactive-media-planner, BARE-INTENT MODE)` |
| "playful generative <X>" / "interactive piece where I <Y>" (no app framing) | **B** | `Task(interactive-media-planner, BARE-INTENT MODE)` |
| "show me a chart of X" (ad-hoc, no interaction) | — | Render inline in chat (fenced block) — NOT a planner |

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

## Narrative experiences: scaffold-then-planner, same as simulation + interactive (v3.4 hard rule)

When the user wants to make a piece where someone **walks into a place and leaves changed** — a museum microsite that lives, an exhibition extension that breathes, a memorial that holds, a character portrait at depth, an editorial scrollytelling piece that earns its long-form, a walkable 3D reconstruction of a room/garden/studio — same two-path rule as simulation + interactive.

### Path A — "build an app / site / page that contains this immersive piece"

The user wants the experience embedded in a larger app or site. First scaffold via `/prototype` (or hand-write the HTML), writing a `<div class="nx-placeholder" data-nx="<nxId>" data-paradigm-hint="<hint>" data-aesthetic="<register>" style="aspect-ratio: <W>/<H>"></div>` at the slot. Then dispatch `narrative-experience-planner` per nxId. The runtime embeds at the placeholder.

(Note: `nx-placeholder` is the convention parallel to `sim-placeholder` and `im-placeholder`. The `bp_proto_build` scaffolder already understands the `narratives/{nxId}/` output path per the registry.)

### Path B — "the piece IS the artefact, no surrounding app"

Most narrative pieces are this — a museum microsite where the experience IS the site, a memorial that fills the viewport, a scrollytelling piece that is the whole page. Dispatch `narrative-experience-planner` in BARE-INTENT MODE directly. The runtime IS the artefact.

### Disambiguation

For narrative the default leans Path B — most museum microsites / memorials / scrollytelling pieces are the artefact themselves. Path A only when the user clearly wants the experience inside something larger (a museum's main site WITH a microsite section, an exhibition program WITH an embedded piece). When ambiguous → Path B for narrative (the opposite default vs. simulation + interactive, because narrative pieces are usually whole-page).

Trigger phrases include: "inside the studio", "walk into the painting", "sit inside the room", "let me feel the world of X", "the world breathing through the window", "memorial visualisation", "emotional portrait at depth", "museum microsite that lives", "walkable 3D space", "explore the room freely", "first-person walkthrough of <place>", "wander the garden", "architectural reconstruction the user can move through", "free-roam exhibition", "scrollytelling", "snow-fall-style piece", "the piece holds the user", "they leave changed".

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
