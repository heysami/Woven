"""Phase 3 — discovery flow prompt blocks.

When the user kicks off a new prototype (empty `source/main/`) or a new fork
branch, the agent's first turn should emit a discovery `<question-form>` to
lock in the brief — output shape, subject, activity, tone, brand direction —
before scaffolding any source. After the user answers, if they picked
"pick a direction for me", a second `<question-form id="direction">` follows
with five pre-defined visual directions; the chat UI renders rich tiles
(palette swatches + font samples) by looking up each option's metadata in
`window.TH_DIRECTIONS` from `directions.js`.

The form is split into two pieces:
- `CORE_DISCOVERY_QUESTIONS` — Output, Subject, Activity, Tone, Personas,
  Brand. Always asked when the discovery flow fires; relevant to ANY
  prototype build (single-page, marketing site, mobile screen, etc.).
- `EDITOR_VIEWS_QUESTION` — the "which editor views should regenerate
  populate?" picker. Only relevant when the active workflow actually
  populates editor views (Workflow 1 / regenerate). Excluded from plain
  freeform runs so the agent doesn't ambush the user with editor-specific
  options that don't apply to what they're building.

This module exposes:
- `DIRECTIONS` — the same five-direction library mirrored on the UI side.
  IDs MUST match `directions.js`; descriptions feed the question form so the
  agent has a one-liner per option (the rich tile is rendered client-side).
- `discovery_form_json(include_views=False)` — builds the form JSON the
  agent should emit on turn 1. Pass `include_views=True` only when the
  workflow will populate editor views.
- `DIRECTION_FORM_JSON` — exact JSON the agent should emit when the user
  picked "pick a direction for me" on the discovery form.
- `discovery_rules_prompt(branch, include_views=False)` — the RULE 1/2/3
  system-prompt block. Appended to the agent's system prompt only on the
  first run of a fresh prototype.
- `wants_discovery(kind, project_root, branch)` — daemon-side trigger test.
- `wants_editor_views(kind)` — daemon-side trigger test for whether the
  Views question should be appended.
"""
from __future__ import annotations
import json
import os
from typing import Optional


# ── 1. Direction library ─────────────────────────────────────────────────────
# IDs MUST match `editor/prompts/directions.js` exactly. The chat surface looks
# the rendered option labels up by slug, so if the agent emits a label here
# the UI knows which palette / font samples to render. The `mood` line below
# also appears in the discovery form's option `description` so the agent has
# context to write a coherent reply.
DIRECTIONS = [
    {
        "id": "editorial-mono",
        "label": "Editorial Mono",
        "mood": "Print magazine — generous whitespace, considered hierarchy, one warm accent against monochrome.",
        "references": ["The Browser Company website", "Are.na", "Magazine-style longform editorial"],
        "displayFont": "EB Garamond",
        "bodyFont": "Inter",
        "palette": ["#0a0a0a", "#fafafa", "#ffffff", "#8a8a8a", "#c2410c", "#f0ece4"],
    },
    {
        "id": "trading-floor",
        "label": "Trading Floor",
        "mood": "Bloomberg-dense. Tabular data, dark panels, every pixel earns its place.",
        "references": ["Bloomberg Terminal", "TradingView dark", "Polymarket"],
        "displayFont": "IBM Plex Sans",
        "bodyFont": "IBM Plex Mono",
        "palette": ["#d4d8de", "#0a0e15", "#131822", "#6b7280", "#10b981", "#ef4444"],
    },
    {
        "id": "warm-consumer",
        "label": "Warm Consumer",
        "mood": "Soft and welcoming. Off-white surfaces, terracotta accents, type with a little flourish.",
        "references": ["Notion landing pages", "Substack newsletter UI", "Headspace"],
        "displayFont": "Fraunces",
        "bodyFont": "Inter",
        "palette": ["#1f1612", "#fdf6e8", "#faedd6", "#a08570", "#d4634b", "#2e6f5e"],
    },
    {
        "id": "control-room",
        "label": "Control Room",
        "mood": "Industrial control panel. Carbon surfaces, amber accents, mono-flavoured chrome.",
        "references": ["NASA mission-control HUDs", "Linear dark theme", "Vercel observability"],
        "displayFont": "JetBrains Mono",
        "bodyFont": "Inter",
        "palette": ["#e8eaed", "#1a1c1f", "#25282d", "#7a838f", "#ffaa00", "#ff3838"],
    },
    {
        "id": "brutalist-pop",
        "label": "Brutalist Pop",
        "mood": "Big type, hard edges, accent-as-statement. The interface is the poster.",
        "references": ["Off-White / Virgil Abloh web", "Are.na archive views", "Working Not Working"],
        "displayFont": "Space Grotesk",
        "bodyFont": "Inter",
        "palette": ["#000000", "#f7f4ec", "#ffffff", "#555555", "#ff5500", "#0033ff"],
    },
]


# ── 2. Form JSON literals ───────────────────────────────────────────────────
# The agent emits these verbatim. Keys match the chat UI's `parseQuestionForms`
# schema: each question has `header`, `question`, optional `multiSelect`, and
# `options[].{label, description}` (the description renders as a one-liner
# under the label).
CORE_DISCOVERY_QUESTIONS = [
    {
        "header": "Output",
        "question": "What are we making?",
        "multiSelect": False,
        "options": [
            {"label": "Web prototype / landing", "description": "Single-page or short-flow app"},
            {"label": "Multi-page app", "description": "Several screens, real navigation"},
            {"label": "Marketing site", "description": "Hero + content sections + CTAs"},
            {"label": "Mobile app screen", "description": "Phone-frame focus, taps + sheets"},
            {"label": "Magazine / poster", "description": "Layout-first editorial piece"},
        ],
    },
    {
        "header": "Subject",
        "question": "Subject vocabulary — what world does this live in?",
        "multiSelect": False,
        "options": [
            {"label": "Trading / Bloomberg-style", "description": "Markets, tickers, dense data"},
            {"label": "Productivity / Linear-style", "description": "Tasks, queues, scannable lists"},
            {"label": "Editorial / magazine", "description": "Articles, photo-led, long reads"},
            {"label": "Consumer / warm", "description": "Habit-forming, soft, encouraging"},
            {"label": "Control room / dense", "description": "Monitoring, ops, telemetry"},
        ],
    },
    {
        "header": "Activity",
        "question": "Primary activity — what does the user mostly do?",
        "multiSelect": False,
        "options": [
            {"label": "Read", "description": "Sit and consume — articles, briefings"},
            {"label": "Scan", "description": "Triage at speed — lists, queues"},
            {"label": "Decide", "description": "Pick between alternatives — comparisons"},
            {"label": "Compare", "description": "Side-by-side evaluation"},
            {"label": "Configure", "description": "Set up, settings-heavy"},
            {"label": "Browse", "description": "Wander and discover — galleries"},
        ],
    },
    {
        "header": "Tone",
        "question": "Tone (pick up to 2)",
        "multiSelect": True,
        "options": [
            {"label": "Institutional", "description": "Quiet authority"},
            {"label": "Warm", "description": "Welcoming, human"},
            {"label": "Bold", "description": "Confident, declarative"},
            {"label": "Edgy", "description": "Punchy, opinionated"},
            {"label": "Minimal", "description": "Pare back to essentials"},
        ],
    },
    {
        "header": "Personas",
        "question": "Who uses this? (Impact D §9.2 — feeds lane enumeration for Subagent 4)",
        "multiSelect": False,
        "options": [
            {"label": "Single persona / one user role", "description": "All actions happen in one lane"},
            {"label": "Multiple roles handing off work", "description": "Cross-lane handoffs — name them in your reply"},
        ],
    },
    {
        "header": "Brand",
        "question": "Visual direction",
        "multiSelect": False,
        "options": [
            {"label": "Pick a direction for me", "description": "Show me five curated directions and I'll choose"},
            {"label": "I have a brand spec", "description": "Tokens, colours, type are already decided — I'll share them"},
            {"label": "Match a reference site", "description": "I'll point you at a URL whose look I want to match"},
        ],
    },
]


# The View-picker question (Impact J §11.3) — editor-view specific. Only
# included when the active workflow will populate those views (Workflow 1
# regenerate). NOT relevant to plain freeform prototype builds.
EDITOR_VIEWS_QUESTION = {
    "header": "Views",
    "question": "Which views should the regenerate pass populate? Source + Canvas always run.",
    "multiSelect": True,
    "options": [
        {"label": "Prototype iframe loadability", "description": "Per-frame w/h, hash, setupScript — default ON"},
        {"label": "User flow + lanes", "description": "Arrow graph + lane assignments — default ON"},
        {"label": "Design system", "description": "Tokens + primitives + design-system.html — default ON"},
        {"label": "Information architecture", "description": "Sitemap parent links + per-frame entities — default OFF"},
        {"label": "Entities (data shapes)", "description": "Entity model + links — default OFF"},
        {"label": "State machines", "description": "Lifecycle FSMs per entity — default OFF"},
        {"label": "Timelines", "description": "Time-driven event sequences — default OFF"},
        {"label": "Grids", "description": "2D variance maps / decision matrices — default OFF"},
    ],
}


def discovery_form_json(*, include_views: bool = False) -> dict:
    """Build the discovery `<question-form>` JSON.

    `include_views=True` inserts the editor-view picker between Personas and
    Brand — only set this when the workflow that's about to run will
    populate editor views (Workflow 1 regenerate / view-aware fork). Plain
    freeform prototype builds should leave it False.
    """
    questions = list(CORE_DISCOVERY_QUESTIONS)
    if include_views:
        # Insert Views just before the final "Brand" question so the form
        # reads brief → views → branding, matching the regenerate flow.
        questions = questions[:-1] + [EDITOR_VIEWS_QUESTION] + questions[-1:]
    return {"questions": questions}


def _direction_form_json() -> dict:
    return {
        "questions": [
            {
                "header": "Direction",
                "question": "Pick the visual direction that best matches the vibe you want.",
                "multiSelect": False,
                "options": [
                    {"label": d["id"], "description": d["mood"]}
                    for d in DIRECTIONS
                ],
            }
        ]
    }


DIRECTION_FORM_JSON = _direction_form_json()


# ── 3. System-prompt text ───────────────────────────────────────────────────
def _block(s: str) -> str:
    """Strip per-line leading whitespace so the prompt is left-aligned."""
    return "\n".join(line.lstrip() for line in s.strip().splitlines())


_VIEWS_RULE_FRAGMENT = _block("""
The form includes a `Views` multi-select — that picks which editor-view
populators run during Workflow 1's modular dispatch. Subagents 1 + 2 always
run; the optional subagents (IA, entities, state machines, timelines, grids)
run only if the user selected the matching view.
""")


def _build_template(*, include_views: bool) -> str:
    form_json = json.dumps(discovery_form_json(include_views=include_views), indent=2)
    direction_json = json.dumps(DIRECTION_FORM_JSON, indent=2)
    views_clause = (
        "\n\n" + _VIEWS_RULE_FRAGMENT
        if include_views else ""
    )
    rule3_tail = (
        " and the user's `Views` selection. The selected views feed Workflow"
        " 1's modular dispatch (Subagents 1 + 2 always run; the optional ones"
        " run only if the user selected them)."
        if include_views
        else "."
    )
    return "\n\n## Discovery flow (new prototype)\n\n" + _block(f"""
This branch is a fresh prototype — `source/__BRANCH__/` is empty (or you've been
asked to scaffold a new fork). Before writing any code, lock in the brief.

RULE 1 — On your VERY FIRST turn, emit this exact block and nothing else.
No text before, no text after, no tool calls, no thinking out loud. The form
is your entire turn — the chat surface renders it as clickable buttons, and
your turn ends naturally so the user can answer:

<question-form id="discovery">
{form_json}
</question-form>{views_clause}

RULE 2 — When the user replies with their answers, branch on the
"Brand / Visual direction" answer:

  • If they picked "Pick a direction for me" — emit this exact second form,
    nothing else. The chat surface renders each option as a tile with the
    palette + display/body font preview baked in (the data lives in
    `editor/prompts/directions.js → window.TH_DIRECTIONS`; do NOT inline
    palette hex values yourself — the UI fills them in by option label).

    <question-form id="direction">
{direction_json}
    </question-form>

    After the user picks a direction, commit its palette + font choices to
    `source/__BRANCH__/styles.css :root` (read the canonical values from
    `editor/prompts/directions.js → window.TH_DIRECTIONS[<id>].palette` /
    `displayFont` / `bodyFont`) and then proceed.

  • If they picked "I have a brand spec" — reply with ONE sentence asking
    them to paste or describe the brand spec (tokens, fonts, colours).
    After they reply, write the spec to `source/__BRANCH__/brand-spec.md`
    and use it as the source of truth for `styles.css :root`.

  • If they picked "Match a reference site" — reply with ONE sentence
    asking for the URL. Once received, fetch (`WebFetch` is enabled) the
    landing page, extract the palette + type system, save your notes to
    `source/__BRANCH__/brand-spec.md`, and use that as the source of truth.

RULE 3 — Once branding is resolved, call TodoWrite with the breakdown of
the build (skeleton → tokens → primitives → screens → polish), then proceed
according to PROTOTYPE.md{rule3_tail}

Do NOT ask the user to name frames — frame IDs derive from filenames per
`docs/agents/conventions.md` (U-Frame-ID-naming). Do NOT skip RULE 1 even
if you think you know the answer — the user's brief is the ground truth.
""")


def discovery_rules_prompt(branch: str, *, include_views: bool = False) -> str:
    """Return the discovery system-prompt block with the active branch slug
    interpolated. Uses `str.replace` rather than `str.format` to avoid having
    to double-escape the dozens of curly braces in the embedded JSON.

    Pass `include_views=True` when the workflow that's about to run will
    populate editor views (Workflow 1 regenerate). For plain freeform builds
    leave it False — the editor-view picker is irrelevant there and asking
    it on every freeform run was generating user confusion.
    """
    template = _build_template(include_views=include_views)
    slug = (branch or "main").strip().lower() or "main"
    return template.replace("__BRANCH__", slug)


# ── 4. Trigger detection ────────────────────────────────────────────────────
def _source_branch_dir(project_root: str, branch: str) -> str:
    return os.path.join(project_root, "source", (branch or "main").strip().lower() or "main")


def _is_empty_source(project_root: str, branch: str) -> bool:
    """True when the branch's source folder is empty or missing.

    A blank scaffolded project has `source/main/` but no `index.html` —
    `os.listdir` returns an empty list (or just `.DS_Store` on macOS). We
    treat 'no real entry file' as empty so the discovery flow fires on
    freshly created projects as well as truly missing folders.
    """
    d = _source_branch_dir(project_root, branch)
    if not os.path.isdir(d):
        return True
    real = [n for n in os.listdir(d)
            if not n.startswith(".") and not n.endswith(".tmp")]
    if not real:
        return True
    # If there's no .html entry at all, consider it empty too — the source
    # folder may hold stray notes from an aborted scaffold attempt.
    return not any(n.lower().endswith(".html") for n in real)


# Sentinels of a non-minimal prompt. If any one of these markers is present
# in the user's prompt body, we assume the user has already given a complete
# brief (or wired the prompt node to PROTOTYPE.md / a workflow template) and
# we skip discovery so the agent doesn't ambush them with a form they don't
# need. These are the markers most likely to appear in a real wired prompt
# without showing up in a casual "build me a todo app" one-liner.
_NON_MINIMAL_MARKERS = (
    "prototype drawing — system prompt",   # PROTOTYPE.md header (em-dash)
    "prototype drawing - system prompt",   # ASCII-hyphen variant
    "step zero — decide the genre",
    "step zero - decide the genre",
    "=== instructions (wired system prompt) ===",
    "=== workspace scope ===",
    "decide a genre",                      # core PROTOTYPE.md instruction
    "genre playbook",                       # PROTOTYPE.md section header
    "genre selection is multi-axis",        # PROTOTYPE.md sentence
)

# Below this length we assume the user typed a one-liner and benefits from the
# discovery form. Above it, the prompt is rich enough (multi-paragraph brief,
# explicit personas, named references, etc.) that the form is just noise.
# Tuned generously: a 600-char prompt is roughly 100 words = a real paragraph.
_MIN_NONMINIMAL_LEN = 600


def _is_minimal_prompt(user_prompt: str) -> bool:
    """True when the prompt looks like a casual one-liner that benefits from
    the discovery form. False when it's a wired/extensive brief that should
    proceed directly.

    Two signals — either one flipping us to "non-minimal":
      1. Length: ≥600 chars of user text usually means a real paragraph brief.
      2. Marker strings: presence of any PROTOTYPE.md header, the workflow
         canvas's `=== wired system prompt ===` separator, or other clear
         signs the prompt is composed not casual.
    """
    p = (user_prompt or "").strip()
    if not p:
        return True
    if len(p) >= _MIN_NONMINIMAL_LEN:
        return False
    low = p.lower()
    for marker in _NON_MINIMAL_MARKERS:
        if marker in low:
            return False
    return True


def wants_discovery(kind: str, project_root: str, branch: str,
                    user_prompt: str = "") -> bool:
    """Daemon-side trigger test for the Phase 3 discovery prompt.

    Fires when ALL of these are true:
      • kind == "freeform" AND the branch's `source/` is empty (fresh
        prototype, first conversational run), OR kind == "fork".
      • The user's prompt is "minimal" — a casual one-liner like "build me
        a habit tracker". Once the user pastes a real brief or wires the
        prompt node to PROTOTYPE.md, the form would just get in the way.

    Does NOT fire for:
      • edits-apply / merge / regenerate / *-request — those are structural
        operations on existing source; no discovery needed.
      • freeform runs on a branch that already has source — the agent should
        just answer the user's question, not ambush them with a form.
      • Non-minimal prompts on a fresh branch — the user clearly knows what
        they want; don't waste a turn asking.
    """
    k = (kind or "").strip().lower()
    if k == "fork":
        # Fork runs scaffold a branch from FORK_REQUEST.md, which IS the brief
        # — no need for a separate discovery form when the user already wrote
        # one. Mirror the same minimal check; if the request is detailed,
        # skip the form.
        return _is_minimal_prompt(user_prompt)
    if k != "freeform":
        return False
    if not _is_empty_source(project_root, branch):
        return False
    return _is_minimal_prompt(user_prompt)


def wants_editor_views(kind: str) -> bool:
    """Daemon-side trigger test for the editor-view picker in the discovery
    form. Only fires when the workflow being kicked off actually populates
    editor views — currently `regenerate` (Workflow 1 modular dispatch) and
    its request variants. Plain freeform / fork prototype builds get the
    core questions only, never the editor-view picker."""
    k = (kind or "").strip().lower()
    return k.startswith("regenerate")
