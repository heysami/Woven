"""editor/planners.py — planner-registry aggregator + enable/disable state.

Single source of truth for "what planners does this app ship, what does each
do, and which are turned on for this project."

Adding a new planner is a single-file operation: drop a
`.claude/agents/<name>.manifest.json` next to its `.md` playbook. This module
walks the directory and auto-discovers it; the daemon's /__planners endpoint
+ the landing-page Planners view pick it up without code changes.

State model:
  • Per-planner default: `defaultEnabled` field in the manifest (almost always true).
  • Per-project override: `<projectRoot>/.planners-disabled.json` lists IDs
    the user has switched off. Empty / missing = all defaults respected.

The capabilities preamble (capabilities.capabilities_preamble) consults the
project's disable list when composing the per-spawn system prompt — disabled
planners' hard-rule blocks are omitted, so agents spawned in that project
do NOT see "dispatch this planner FIRST" cues for off planners.
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional


_HERE          = os.path.dirname(os.path.abspath(__file__))
_PROTOCOL_ROOT = os.path.dirname(_HERE)
_AGENTS_DIR    = os.path.join(_PROTOCOL_ROOT, ".claude", "agents")
_DISABLED_FILE = ".planners-disabled.json"   # per project, at project root


# ── Manifest discovery ───────────────────────────────────────────────────


def _scan_manifests() -> list[dict]:
    """Walk .claude/agents/*.manifest.json and return parsed manifests.

    Manifests are pure data — parse failures are silently skipped so a single
    broken file can't take down the whole registry. The caller can detect
    "missing planner" by absence in the returned list.
    """
    out: list[dict] = []
    if not os.path.isdir(_AGENTS_DIR):
        return out
    for fn in sorted(os.listdir(_AGENTS_DIR)):
        if not fn.endswith(".manifest.json"):
            continue
        path = os.path.join(_AGENTS_DIR, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                m = json.load(f)
            if not isinstance(m, dict) or not m.get("id"):
                continue
            out.append(m)
        except (json.JSONDecodeError, OSError):
            continue
    return out


# ── Per-project disable state ────────────────────────────────────────────


def _disabled_path(project_root: Optional[str]) -> Optional[str]:
    if not project_root:
        return None
    return os.path.join(project_root, _DISABLED_FILE)


def load_disabled(project_root: Optional[str]) -> list[str]:
    """Return the list of planner IDs the user has switched off for this
    project. Missing file = empty list."""
    p = _disabled_path(project_root)
    if not p or not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        disabled = data.get("disabled") if isinstance(data, dict) else None
        if isinstance(disabled, list):
            return [str(x) for x in disabled if isinstance(x, (str, int, float))]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_disabled(project_root: str, disabled_ids: list[str]) -> None:
    """Atomically persist the disable list to <project_root>/.planners-disabled.json.

    Empty list still writes the file so the toggle state is auditable; callers
    that want to delete the file should remove it explicitly."""
    if not project_root:
        raise ValueError("project_root required to save disabled state")
    p = _disabled_path(project_root)
    if not p:
        return
    # Dedupe + stringify defensively; preserve order so the UI shows a
    # stable list.
    seen: set = set()
    cleaned: list[str] = []
    for x in disabled_ids:
        s = str(x)
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"disabled": cleaned}, f, indent=2)
    os.replace(tmp, p)


def set_planner_enabled(project_root: str, planner_id: str, enabled: bool) -> list[str]:
    """Flip one planner's enabled state in the project's disable list.

    Returns the new disable list (sorted alphabetically for caller convenience)."""
    if not planner_id:
        raise ValueError("planner_id required")
    cur = load_disabled(project_root)
    s = set(cur)
    if enabled:
        s.discard(planner_id)
    else:
        s.add(planner_id)
    new_list = sorted(s)
    save_disabled(project_root, new_list)
    return new_list


# ── Public registry ──────────────────────────────────────────────────────


def get_registry(project_root: Optional[str] = None) -> dict:
    """Aggregate every manifest + resolve per-planner enabled state for the
    given project. Returns a structure the /__planners HTTP handler returns
    verbatim.

    Each planner in `planners[]` carries an `enabled` field merging the
    manifest's `defaultEnabled` with the project's disable list — `enabled`
    is False iff the planner is in the disable list (or absent and the
    manifest set defaultEnabled to False)."""
    manifests = _scan_manifests()
    disabled  = set(load_disabled(project_root))

    planners: list[dict] = []
    for m in manifests:
        default_enabled = bool(m.get("defaultEnabled", True))
        is_disabled     = m.get("id") in disabled
        enabled         = default_enabled and not is_disabled
        planners.append({
            **m,
            "enabled":        enabled,
            "defaultEnabled": default_enabled,
            "userDisabled":   is_disabled,
        })

    return {
        "version":     "1",
        "count":       len(planners),
        "disabledIds": sorted(disabled),
        "planners":    planners,
    }


def enabled_planner_ids(project_root: Optional[str] = None) -> set:
    """Cheap helper for capabilities_preamble: which planners' hard-rule
    blocks should be included in the per-spawn system prompt?"""
    reg = get_registry(project_root)
    return {p["id"] for p in reg["planners"] if p.get("enabled")}
