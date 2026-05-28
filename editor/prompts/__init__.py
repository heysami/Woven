# Prompt blocks injected into spawned agents at runtime.
#
# Each Phase contributes its own module (`discovery.py` for Phase 3, future
# `media_contract.py` for Phase 4, etc.). The daemon (`serve.py`) imports the
# blocks it needs and appends them to the system prompt for runs that match a
# trigger condition.
#
# Companion JS data (visualised in the chat surface — e.g. direction palettes,
# font samples) lives next to these files as `.js` modules so the editor can
# load them via a normal `<script>` tag. Keeping both halves in `editor/prompts/`
# means the install/workspace tier split (Phase 6) already routes them as
# shared assets — no per-project copies, no drift.
