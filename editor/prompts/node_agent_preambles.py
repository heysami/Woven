"""v3.5 - per-node preamble templates for agent-kind workflow nodes.

When the daemon dispatches an agent-kind node via
`POST /__workflow/node/<id>/run`, it spawns a fresh `claude` subprocess
scoped to that node's task. The subprocess gets:
  • a focused system prompt (the per-node preamble, when registered)
  • the upstream-walk text already composed by `_workflow_node_run`
  • cwd = project root, normal env vars (TH_PROJECT_ROOT etc.)

Per-node preambles let specific node ids ship with bespoke instructions.
After the v3.5 onboarding cut, no node ids are pre-registered here - every
agent-kind node falls through to `generic_preamble`, which hands the
dispatch over to the node's own `text` field. Orchestrators populate that text
when they scaffold their drawers; the user can edit it on the canvas.

If you want to re-introduce a baked preamble for a specific id, add it to
NODE_AGENT_PREAMBLES below. Format: `id: (short_title, preamble_template)`.
Use `{branch}` / `{id}` placeholders - `render()` substitutes them.
"""
from __future__ import annotations
from typing import Optional


# Registry - { node_id: (title, preamble_template) }. Empty by default after
# the v3.5 onboarding cut. Add entries here for IDs that need a pre-baked
# system prompt; everything else uses `generic_preamble`.
NODE_AGENT_PREAMBLES: dict = {}


def lookup(node_id: str) -> Optional[tuple]:
    """Return (title, preamble) for a known node id, or None if not in the
    registry. Callers should fall back to a generic preamble."""
    return NODE_AGENT_PREAMBLES.get(node_id)


def generic_preamble(node_id: str, node_text: str) -> str:
    """Fallback for agent-kind nodes not in the registry - typically a
    user-added agent node on the canvas. Hands the dispatch over to the
    node's own `text` field after a one-paragraph framing."""
    safe_text = (node_text or "").strip() or "(no instructions on the node)"
    return f"""You are dispatched for ONE workflow node: `{node_id}`.

The node's instructions (from its `text` field on the canvas):

{safe_text}

Use the wired upstream context provided above. Write artifacts where instructed; stop when done."""


def render(node_id: str, node_text: str, branch: str) -> tuple:
    """Resolve the preamble for a node id. Returns (title, preamble) - title
    is a short label for the run title, preamble is the system-prompt body
    handed to the spawned subprocess.

    Substitutes `{branch}` and `{id}` placeholders in the registered
    preamble. For unknown ids, returns a generic preamble that echoes the
    node's own text."""
    hit = lookup(node_id)
    if hit:
        title, template = hit
        # Manual format to avoid braces-in-prose tripping str.format().
        body = template.replace("{branch}", branch).replace("{id}", node_id)
        return (title, body)
    return (f"Node agent: {node_id}", generic_preamble(node_id, node_text))
