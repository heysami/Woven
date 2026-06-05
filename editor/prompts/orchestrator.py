"""Phase 5 — workflow-orchestrator skill loader.

When a project was created with a non-Blank scope (Phase 1), the daemon wrote
`.onboarding-pending` at the project root. When the user opens the workflow
chat, the freeform-claude spawn path checks `wants_orchestration()` here and,
if true, prepends the workflow-orchestrator skill PLUS a small per-project
context block to the agent's system prompt. The agent then drives the
pre-scaffolded workflow.json end-to-end per the chosen scope.

Resolution order for the skill markdown:
  1. `<project_root>/.claude/agents/workflow-orchestrator.md`  (per-project override)
  2. `<INSTALL_ROOT>/.claude/agents/workflow-orchestrator.md`  (workspace-shared default)

Mirrors how Claude Code resolves agent definitions in its CLI — project copy
wins over the shared one.

Exposes:
- `wants_orchestration(project_root)` — True if `.onboarding-pending` exists.
- `orchestrator_prompt(project_root, install_root, branch)` — returns the full
  system-prompt extension (skill body + marker snapshot + DECISION_* status).
  Returns "" if the skill file can't be located.
"""
from __future__ import annotations
import json
import os
from typing import Optional


SKILL_REL_PATH = os.path.join(".claude", "agents", "workflow-orchestrator.md")
MARKER_NAME    = ".onboarding-pending"


def wants_orchestration(project_root: str) -> bool:
    """Cheap on-disk check — no parsing, no caching. The marker is removed by
    the orchestrator itself on successful completion (§9 of the skill), so its
    presence is the live signal that an unfinished onboarding exists."""
    if not project_root: return False
    try:
        return os.path.isfile(os.path.join(project_root, MARKER_NAME))
    except OSError:
        return False


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _resolve_skill_path(project_root: str, install_root: str) -> Optional[str]:
    """Project copy wins over the workspace-shared default. Either may be
    missing — returns None if neither exists so the caller can no-op cleanly."""
    candidates = []
    if project_root:
        candidates.append(os.path.join(project_root, SKILL_REL_PATH))
    if install_root and install_root != project_root:
        candidates.append(os.path.join(install_root, SKILL_REL_PATH))
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def _read_marker(project_root: str) -> Optional[dict]:
    try:
        with open(os.path.join(project_root, MARKER_NAME), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _list_decision_files(project_root: str) -> list:
    """List existing `DECISION_<id>.json` files at the project root so the
    orchestrator's first turn knows which checkpoints already have answers
    (e.g. user picked, then reloaded the page)."""
    out = []
    try:
        for name in sorted(os.listdir(project_root)):
            if not name.startswith("DECISION_") or not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(project_root, name), "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                out.append({
                    "file":  name,
                    "id":    data.get("id"),
                    "value": data.get("value"),
                    "label": data.get("label"),
                })
            except (OSError, ValueError):
                out.append({"file": name, "id": None, "value": None, "label": None})
    except OSError:
        pass
    return out


def orchestrator_prompt(project_root: str, install_root: str, branch: str = "main") -> str:
    """Build the system-prompt extension for the orchestrator. Returns "" if
    the skill file is missing — caller should just no-op in that case (the
    user still gets the normal workflow-mode chat).

    The output structure:
      1. Skill body (the markdown frontmatter is left intact — the agent gets
         the description too, which is informative).
      2. A per-project context block with the current marker snapshot,
         resolved branch, and any DECISION_*.json files already on disk.

    Keeping the per-project context as a tail block (not interleaved into the
    skill) lets us evolve the skill without re-templating it on every spawn.
    """
    # Defence-in-depth: callers gate on wants_orchestration() before calling
    # us, but if the marker isn't there we still bail — re-asking the user via
    # the discovery flow would be the right fallback, and a stale prompt with
    # an empty marker snapshot would just confuse the agent.
    marker = _read_marker(project_root)
    if marker is None: return ""
    skill_path = _resolve_skill_path(project_root, install_root)
    if not skill_path: return ""
    body = _read_text(skill_path).strip()
    if not body: return ""

    # Branch-aware substitution. The skill markdown carries `{branch}`
    # placeholders in path references; we resolve them against the dispatch's
    # branch param (default "main"). Mirrors how node_agent_preambles.render
    # substitutes — keeps the skill author honest about the branch axis
    # without requiring multiple skill files for multi-prototype futures.
    body = body.replace("{branch}", branch)

    # v2.11 — skill freshness header. The agent's system prompt is FROZEN at
    # spawn time; later edits to the skill markdown don't propagate to a
    # running agent. The freshness header tells the agent to re-read the
    # canonical file on EVERY turn so updates take effect immediately. The
    # spawn-time snapshot below is just a fallback (in case the file moved
    # or the agent's first action fails).
    #
    # Path resolution: if there's a per-project override at
    # <project_root>/.claude/agents/workflow-orchestrator.md, prefer it;
    # otherwise the shared install-root copy.
    project_local_path = os.path.join(project_root, SKILL_REL_PATH) if project_root else None
    if project_local_path and os.path.isfile(project_local_path):
        canonical_path_var = "$TH_PROJECT_ROOT/" + SKILL_REL_PATH
    else:
        canonical_path_var = "$TH_PROTOCOL_ROOT/" + SKILL_REL_PATH
    freshness_header = (
        "## ⚠ STAY FRESH — re-read this spec on EVERY turn\n\n"
        f"Your canonical instructions live at `{canonical_path_var}`. Before "
        "doing ANYTHING else on every turn (including the first), run:\n\n"
        f"```bash\ncat {canonical_path_var}\n```\n\n"
        "The content of that file always wins over the copy in your context. "
        "Your context was frozen when this subprocess was spawned and may be "
        "stale if the skill was updated mid-session. If the file says X and "
        "your memory says Y, **follow the file**. Do not skip the re-read "
        "even if the previous turn's content seemed complete.\n\n"
        "What follows below is a SNAPSHOT of the file taken at spawn-time, "
        "included as a fallback in case the canonical path is unreadable. "
        "Read it now for your first action, BUT re-read the canonical path "
        "on every turn after that.\n\n"
        # The canonical file on disk uses `{branch}` as a placeholder for
        # the active branch slug. The daemon substitutes it into the
        # snapshot below at spawn time, but a live re-read of the file
        # shows the literal placeholder text. Tell the agent how to read
        # both forms so divergence between cached + live versions doesn't
        # confuse it.
        f"**Branch convention.** Paths in the canonical file use `{{branch}}` "
        f"as a placeholder for the active branch slug, which on this run is "
        f"`{branch}` (also available as `$TH_BRANCH` in any subprocess you "
        f"spawn). The snapshot below already has that substituted; if a live "
        f"re-read shows `{{branch}}` literally, mentally substitute the same "
        f"value.\n\n---\n\n"
    )

    decisions = _list_decision_files(project_root)

    ctx_lines = [
        "",
        "---",
        "",
        "## Current project context (auto-injected by the daemon)",
        "",
        f"- Project root: `{project_root}`",
        f"- Branch: `{branch}`",
        f"- Marker present: `.onboarding-pending` (read it first; the snapshot below is just a hint).",
        "",
        "Marker snapshot at run-spawn time:",
        "",
        "```json",
        json.dumps(marker, indent=2),
        "```",
        "",
    ]
    if decisions:
        ctx_lines.append("Existing `DECISION_*.json` files (consume these before re-asking a checkpoint):")
        ctx_lines.append("")
        for d in decisions:
            ctx_lines.append(f"- `{d['file']}` — id={d.get('id')!r}, value={d.get('value')!r}, label={d.get('label')!r}")
        ctx_lines.append("")
    else:
        ctx_lines.append("No `DECISION_*.json` files present yet — every checkpoint still needs an answer.")
        ctx_lines.append("")
    ctx_lines.append(
        "Start your first turn by: (1) `cat " + canonical_path_var + "` to "
        "load the fresh skill; (2) `cat $TH_PROJECT_ROOT/.onboarding-pending` "
        "to load the marker; (3) announcing the scope in one sentence; "
        "(4) dispatching the next undone stage per §4 of the skill."
    )
    return freshness_header + body + "\n" + "\n".join(ctx_lines)
