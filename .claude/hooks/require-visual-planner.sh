#!/bin/bash
# Limn v3.1.1 — PreToolUse hook that blocks Write/Edit/MultiEdit on any
# visual-asset path (HTML, raster images, vectors, video) until the agent
# has dispatched the visual-planner subagent at least once in the current
# session.
#
# IMPORTANT: the daemon spawns claude with --dangerously-skip-permissions,
# which makes claude IGNORE `permissionDecision: "deny"` JSON output. The
# only mechanism that blocks the tool call regardless of permission-skip
# mode is `exit 2` with the reason written to stderr (the docs:
# "A hook that exits with code 2 stops the tool call before permission
# rules are evaluated, so the block applies even when an allow rule would
# otherwise let the call proceed.")
#
# Hook input arrives on stdin as JSON:
#   {
#     "tool_name": "Write",
#     "tool_input": { "file_path": "...", "content": "..." },
#     "transcript_path": "/path/to/session.jsonl",
#     ...
#   }
#
# Exit 0 = allow.
# Exit 2 + stderr text = block, agent reads the stderr as the deny reason.

set -u

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

# v3.1.1 — Enforce on every visual-output surface the agent might touch:
# HTML pages, raster images, vectors, animations, video. Skipping any of
# these gives the agent an escape hatch to bypass visual-planner entirely
# (e.g. "I'll just write the PNG directly"). Config / docs / source code
# still flow without gating.
case "$FILE_PATH" in
    *.html|*.htm) ;;
    *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif) ;;
    *.svg) ;;
    *.mp4|*.webm|*.mov) ;;
    *.lottie|*.lottie.json) ;;
    *) exit 0 ;;
esac

# If no transcript path was provided, can't verify — let it through to
# avoid breaking edge cases.
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
    exit 0
fi

# Has visual-planner been dispatched this session? Look for a Task tool
# call with subagent_type: visual-planner anywhere in the transcript.
if grep -E '"(name|tool_name)"\s*:\s*"Task"' "$TRANSCRIPT" 2>/dev/null \
   | grep -q '"subagent_type"\s*:\s*"visual-planner"'; then
    exit 0
fi

# Determine the asset kind from the file extension for a tailored message.
KIND="HTML"
case "$FILE_PATH" in
    *.html|*.htm)                                   KIND="HTML page" ;;
    *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif)         KIND="raster image" ;;
    *.svg)                                           KIND="SVG / vector" ;;
    *.mp4|*.webm|*.mov)                             KIND="video" ;;
    *.lottie|*.lottie.json)                         KIND="Lottie animation" ;;
esac

# Block via exit 2 + stderr message. The agent reads the stderr text as
# the reason for the denial and adjusts its plan.
cat >&2 <<MSG
[Limn v3.1.1 enforcement] Cannot write to this ${KIND} (${FILE_PATH##*/}) until visual-planner has been dispatched.

You MUST first call the Task tool with:
  subagent_type: "visual-planner"
  description:   "Classify intent + scaffold image pipeline"
  prompt:        "BARE-INTENT MODE. The user wants: <one-line description, e.g. 'wizard character in Studio Ghibli style'>. Pick a medium from the classifier table, propose an asset id, write the node trio (or quartet for raster-foreground with rembg) into workflow/workflow.json, and dispatch the matching per-medium drawer. Return {assetId, medium, nodeIds}."

Dispatch visual-planner once per visual asset the user needs (hero illustrations, character mascots, photos, icons, etc.). Each call scaffolds a prompt + skill + asset trio on the workflow canvas — the user sees real generated assets, not placeholder rectangles or files you wrote directly.

The classifier table lives at docs/agents/subagents/1V-visual-planner.md (raster-foreground / raster-photo / vector-icon / vector-mark / shader / particle-2d / particle-gl / lottie / 3d / video). Don't emulate the planner from memory — call it via Task.

Once visual-planner has been called at least once this session, you may write source files. They should reference the assets visual-planner scaffolded (using each asset's \`path\` from workflow.json).
MSG
exit 2
