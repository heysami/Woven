# Editor development notes (Claude Code)

Project-agent protocol lives in [AGENTS.md](AGENTS.md); this file is for sessions editing the editor itself (`editor/app.js`, `editor/styles.css`, `editor/tools/`, `editor/serve.py`).

> **Never use em dashes.** Same rule as AGENTS.md: no U+2014 or U+2013 anywhere you write. A plain hyphen "-" is the only dash.

## Canvas rule: two object families, always

The workflow canvas renders two separate families with PARALLEL code paths:

- **Workflow nodes** - `data.nodes`, DOM roots `[data-node-id]`, one `Workflow*Node` component per kind.
- **Whiteboard items** - `data.wb`, DOM roots `[data-wb-id]`, rendered by `WorkflowWbItem` inside `.workflow-wb-layer`.

Any canvas interaction or visual effect (drag, create/delete, selection, snapping, hover, context menus, animations, micro-fx) MUST be implemented for BOTH families before the change is considered done. History shows the wb side gets forgotten; audit it explicitly.

If one family genuinely cannot support the interaction (e.g. connector ports exist only on nodes), state that explicitly in the change description instead of silently skipping it.

Useful chokepoints that already cover both families: `shiftNodes` / `shiftWbItems` (move), `removeNode` / `removeWbItems` (delete), the id-diff enter-animation effect and the `wfx` micro-fx engine in `app.js` (search `useWorkflowFx`).
