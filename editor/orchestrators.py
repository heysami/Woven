"""editor/orchestrators.py - orchestrator-registry aggregator + enable/disable state.

Single source of truth for "what orchestrators does this app ship, what does each
do, and which are turned on for this project."

Adding a new orchestrator is a single-file operation: drop a
`.claude/agents/<name>.manifest.json` next to its `.md` playbook. This module
walks the directory and auto-discovers it; the daemon's /__orchestrators endpoint
+ the landing-page Orchestrators view pick it up without code changes.

State model:
  • Per-orchestrator default: `defaultEnabled` field in the manifest (almost always true).
  • Per-project override: `<projectRoot>/.orchestrators-disabled.json` lists IDs
    the user has switched off. Empty / missing = all defaults respected.

The capabilities preamble (capabilities.capabilities_preamble) consults the
project's disable list when composing the per-spawn system prompt - disabled
orchestrators' hard-rule blocks are omitted, so agents spawned in that project
do NOT see "dispatch this orchestrator FIRST" cues for off orchestrators.
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional


_HERE          = os.path.dirname(os.path.abspath(__file__))
_PROTOCOL_ROOT = os.path.dirname(_HERE)
_AGENTS_DIR    = os.path.join(_PROTOCOL_ROOT, ".claude", "agents")
_DISABLED_FILE = ".orchestrators-disabled.json"   # per project, at project root


# ── Manifest discovery ───────────────────────────────────────────────────


def _scan_manifests() -> list[dict]:
    """Walk .claude/agents/*.manifest.json and return parsed manifests.

    Manifests are pure data - parse failures are silently skipped so a single
    broken file can't take down the whole registry. The caller can detect
    "missing orchestrator" by absence in the returned list.
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
    """Return the list of orchestrator IDs the user has switched off for this
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
    """Atomically persist the disable list to <project_root>/.orchestrators-disabled.json.

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


def set_orchestrator_enabled(project_root: str, orchestrator_id: str, enabled: bool) -> list[str]:
    """Flip one orchestrator's enabled state in the project's disable list.

    Returns the new disable list (sorted alphabetically for caller convenience)."""
    if not orchestrator_id:
        raise ValueError("orchestrator_id required")
    cur = load_disabled(project_root)
    s = set(cur)
    if enabled:
        s.discard(orchestrator_id)
    else:
        s.add(orchestrator_id)
    new_list = sorted(s)
    save_disabled(project_root, new_list)
    return new_list


# ── Public registry ──────────────────────────────────────────────────────


def get_registry(project_root: Optional[str] = None) -> dict:
    """Aggregate every manifest + resolve per-orchestrator enabled state for the
    given project. Returns a structure the /__orchestrators HTTP handler returns
    verbatim.

    Each orchestrator in `orchestrators[]` carries an `enabled` field merging the
    manifest's `defaultEnabled` with the project's disable list - `enabled`
    is False iff the orchestrator is in the disable list (or absent and the
    manifest set defaultEnabled to False)."""
    manifests = _scan_manifests()
    disabled  = set(load_disabled(project_root))

    # v3.13 - per-orchestrator art. A square SVG illustration at
    # editor/orchestrator-art/<id>.svg, served (shared) at
    # /editor/orchestrator-art/<id>.svg. `art` is null when no file exists
    # (e.g. a freshly-added orchestrator) so the landing card shows a
    # placeholder instead of a broken image.
    art_dir = os.path.join(_HERE, "orchestrator-art")

    orchestrators: list[dict] = []
    for m in manifests:
        default_enabled = bool(m.get("defaultEnabled", True))
        is_disabled     = m.get("id") in disabled
        enabled         = default_enabled and not is_disabled
        oid             = m.get("id")
        art_url = None
        if oid and os.path.isfile(os.path.join(art_dir, f"{oid}.svg")):
            art_url = f"/editor/orchestrator-art/{oid}.svg"
        orchestrators.append({
            **m,
            "enabled":        enabled,
            "defaultEnabled": default_enabled,
            "userDisabled":   is_disabled,
            "art":            art_url,
        })

    return {
        "version":       "1",
        "count":         len(orchestrators),
        "disabledIds":   sorted(disabled),
        "orchestrators": orchestrators,
    }


def enabled_orchestrator_ids(project_root: Optional[str] = None) -> set:
    """Cheap helper for capabilities_preamble: which orchestrators' hard-rule
    blocks should be included in the per-spawn system prompt?"""
    reg = get_registry(project_root)
    return {p["id"] for p in reg["orchestrators"] if p.get("enabled")}


def direction_impact_map() -> dict:
    """Map every orchestrator id -> its manifest `directionImpact`.

    The archetype classifier the pipeline reconciler consults. Values seen in
    the manifests: `owns-surface` (embeds a self-contained full-feel runtime -
    game / sim / motion / narrative / scrapbook / scene-3d / interactive-media),
    `sets-direction` (art-director, pre-build), `fills-slots` /
    `imposes-register` (page-build enrichers), `none`. An orchestrator with no
    declared impact defaults to `fills-slots` (a page enricher - the safe,
    non-archetype-claiming assumption). Read from the manifests so the taxonomy
    can't drift out of sync with a hardcoded list in serve.py."""
    out: dict = {}
    for m in _scan_manifests():
        oid = m.get("id")
        if oid:
            out[oid] = str(m.get("directionImpact") or "fills-slots")
    return out


def render_layer_map() -> dict:
    """Map orchestrator id -> the owns-surface HOST families it can fold into
    as a subordinate render layer (manifest `renderLayerFor`).

    Consulted by the pipeline reconciler: an owns-surface picked ALONGSIDE one
    of its declared hosts (e.g. scene-3d next to narrative-experience) is an
    ESCALATION of that host's scene, not a second whole-app - so it must fold
    into the host instead of demoting the host out of the `whole` resolution.
    Only ids that declare the field appear in the map."""
    out: dict = {}
    for m in _scan_manifests():
        oid = m.get("id")
        hosts = m.get("renderLayerFor")
        if oid and isinstance(hosts, list):
            out[oid] = [str(h) for h in hosts if isinstance(h, str) and h]
    return out
