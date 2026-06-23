"""Agent authoring guide for the Woven Logic Graph (now MODULAR).

This module exports ``LOGIC_AUTHORING_GUIDE`` (the SHORT index that the
capabilities preamble points to) and ``get_section(name)`` (loads one focused
markdown module on demand). The full guide used to be ONE ~16KB blob; it is now
split into small files under ``editor/prompts/logic/`` so the always-on preamble
carries only the small index and the in-app agent fetches a focused section
(dataflow / catalogue / runtime / patterns / recipes / verify) instead of
reverse-engineering the composer runtime from source.

It teaches the agent how to turn a natural-language app request ("a camera that
detects a hand, draws a polygon between the fingertips, with a glitchy image
behind") into a concrete wired logic graph: which node kinds to place, which
ports to wire, which controls to set, and how outputs reach their targets.

ACCURACY CONTRACT: every kind / port / dtype / mode / effect / force named in
these modules is verified against ``LOGIC_NODE_DEFS`` + ``SPEC_SOURCE_TEMPLATES``
+ ``SPEC_NODE_DEFS`` in ``editor/app.js`` (the authoritative client-side
registry), the spec-node connect defs, and ``PHYSICS_WORLD_DESIGN.md``. If you
edit the registry, update the matching module.

3.9-safe: pure module-level code, no annotations needing evaluation, no 3.10+
syntax. No em or en dashes anywhere in the text or this file.
"""
from __future__ import annotations
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_LOGIC_DIR = os.path.join(_HERE, "logic")

# Whitelist of fetchable sections. The path is built ONLY from this set, never
# from caller-supplied text, so there is no path-traversal surface.
_SECTIONS = (
    "index",
    "dataflow",
    "catalogue",
    "runtime",
    "patterns",
    "recipes",
    "verify",
    "sketch",
)


def _load(name):
    """Read editor/prompts/logic/<name>.md. Fail-soft to an empty string so an
    import / serve never raises just because a module file is missing."""
    path = os.path.join(_LOGIC_DIR, name + ".md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def get_section(name):
    """Return ONE logic-guide section's markdown by name.

    `name` is matched against the whitelist `_SECTIONS`; anything else (incl.
    any path-traversal attempt) returns a short "unknown section" message that
    also lists the valid names. Never touches the filesystem with a
    caller-controlled path."""
    key = (name or "").strip().lower()
    if key not in _SECTIONS:
        return (
            "unknown section: " + (name or "") + "\n"
            "valid sections: " + ", ".join(_SECTIONS) + "\n"
            "fetch one with GET /__logic_guide?section=<name>&project=<id>"
        )
    text = _load(key)
    if not text:
        return "section '" + key + "' is currently unavailable (file missing)."
    return text


# The always-on preamble points here; keep it SHORT (just the index map).
LOGIC_AUTHORING_GUIDE = _load("index")
