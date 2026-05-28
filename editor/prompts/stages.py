"""v2.6 — canonical stage-name registry.

Single source of truth for mapping stage codes (A-I, J) to human-readable
names. The frontend mirrors this constant under ONBOARDING_STAGE_NAMES in
app.js so the wizard UI, daemon scaffolder, orchestrator skill, and per-node
preambles all speak the same language.

When adding / renaming / removing a stage:
  1. Update STAGES below.
  2. Update ONBOARDING_STAGE_NAMES in editor/app.js (search for that name).
  3. Update the orchestrator skill's §2 stage table.
  4. Update the v2 plan doc's stage references.

The short_name is the one-or-two-word label shown on the canvas mini-DAG and
in the wizard's stages strip; the title is the longer phrase shown in chat
narration and the review screen.
"""
from __future__ import annotations
from typing import Optional


# Ordered list — preserves stage flow when iterating.
STAGES = [
    {"code": "A", "short": "Intake",            "title": "Intake (3 questions + reference)"},
    {"code": "B", "short": "Refine PRD",        "title": "Refine PRD"},
    {"code": "C", "short": "DS brainstorm",     "title": "DS brainstorm — 3 variants"},
    {"code": "D", "short": "Generate DS",       "title": "Generate Design System"},
    {"code": "E", "short": "Quick HTML",        "title": "Chunk PRD → 3 quick HTML pages"},
    {"code": "F", "short": "Remix alts",        "title": "Remix — 3 alternatives per page"},
    {"code": "G", "short": "Refine with pick",  "title": "Refine PRD with picked alts"},
    {"code": "H", "short": "Update DS",         "title": "Update DS from refined PRD"},
    {"code": "H2","short": "Realign PRD",       "title": "Realign PRD with updated DS"},
    {"code": "I", "short": "Build prototype",   "title": "Build prototype source"},
    {"code": "J", "short": "Design brief",      "title": "Design brief + storyboard (DESIGN_BRIEF.html)"},
]

# Lookup tables for fast access.
_BY_CODE = {s["code"]: s for s in STAGES}


def short(code: str) -> str:
    """Return the short label for a stage code, or the code itself if unknown."""
    s = _BY_CODE.get(code)
    return s["short"] if s else code


def title(code: str) -> str:
    """Return the long title for a stage code, or the code itself if unknown."""
    s = _BY_CODE.get(code)
    return s["title"] if s else code


def labelled(code: str) -> str:
    """Return "<code> · <short>" — useful for narration and skill prose where
    both the code (for grepping) and the human name (for readability) matter.
    E.g. labelled("C") → "C · DS brainstorm"."""
    s = _BY_CODE.get(code)
    return f"{code} · {s['short']}" if s else code


def chain(codes: list, sep: str = " → ") -> str:
    """Render a sequence of stage codes as a readable arrow chain.
    E.g. chain(["A","C","D"]) → "Intake → DS brainstorm → Generate DS"."""
    if not codes: return "no automation"
    return sep.join(short(c) for c in codes)


def chain_labelled(codes: list, sep: str = " → ") -> str:
    """Render a sequence of stage codes as a readable arrow chain with both
    code + name. E.g. chain_labelled(["A","C"]) → "A · Intake → C · DS brainstorm"."""
    if not codes: return "no automation"
    return sep.join(labelled(c) for c in codes)
