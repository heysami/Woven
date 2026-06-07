#!/bin/bash
# Woven v3.8 — PreToolUse hook that gates Write/Edit/MultiEdit per family.
#
# Each planner owns a territory. The top-level agent (the chat) is allowed
# to write the app shell freely (source/<branch>/*.html, styles.css, app.js,
# any file at the top level of source/<branch>/). But writing INSIDE one of
# the planner-owned folders, or writing a visual binary anywhere, requires
# the matching planner to have been dispatched in this session.
#
# Territory map:
#   source/<branch>/simulations/<simId>/*   → simulation-planner
#   source/<branch>/interactives/<imId>/*   → interactive-media-planner
#   source/<branch>/narratives/<nxId>/*     → narrative-experience-planner
#   Visual binaries (png/jpg/svg/video/lottie) NOT inside the three folders
#     above                                  → visual-planner
#   Anything else (HTML shell, css, js, md) → allowed
#
# Subagent exemption: planner subagents (simulation-planner, etc.) and their
# drawer subagents (sim-runtime-composer, im-mapping-author, etc.) write
# INSIDE their territory by definition. They are detected by their session
# system prompt and bypass the gate.
#
# The daemon spawns Claude with --dangerously-skip-permissions, so the
# only effective block is `exit 2` with a stderr message.

set -u

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

# No file path → not a file write we can gate; let it through.
if [ -z "$FILE_PATH" ]; then exit 0; fi

# ── Subagent exemption ───────────────────────────────────────────────────
# Each planner subagent's playbook is loaded as its system prompt. The
# subagent transcript begins with the system prompt including "You are
# **<planner>**" (the playbook opening line). Drawer subagents (sim_*,
# im_*, nx_*, *_lens) similarly identify themselves. If the transcript
# carries any of those markers, the calling agent IS the family worker
# and is allowed to write inside its own territory.
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    if grep -aEq 'You are \*\*(simulation-planner|interactive-media-planner|narrative-experience-planner|visual-planner|sim-[a-z0-9-]+|im-[a-z0-9-]+|nx-[a-z0-9-]+|raster-foreground|raster-photo|vector-icon|vector-mark|shader|particle-(2d|gl)|lottie|3d|video|craft-lens|aesthetic-lens|concept-lens)\*\*' "$TRANSCRIPT" 2>/dev/null; then
        exit 0
    fi
fi

# ── Editor-mode chats ────────────────────────────────────────────────────
# Editor-mode is hand-editing existing source files; not the right context
# for planner-gating. (composeModeAwarePrompt() stamps the marker.)
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    LAST_MODE=$(grep -aE "Context: you're chatting from (EDITOR|WORKFLOW) MODE" "$TRANSCRIPT" 2>/dev/null | tail -1)
    case "$LAST_MODE" in
        *"EDITOR MODE"*) exit 0 ;;
    esac
fi

# ── Edits to existing files always pass ─────────────────────────────────
# Planner gating is for SCAFFOLDING — creating the initial sim/im/nx file
# tree, where the planner enforces structure, schema, and lens trios. Once
# those files exist, the editor chat is allowed to apply small targeted
# fixes (a keyboard-focus bug, a CSS tweak, a typo) without re-dispatching
# the planner. That's how the visual-planner works too — once an asset is
# committed, the user can hand-tweak the file.
#
# This check fires AFTER the subagent exemption (so a planner subagent
# creating its initial files still passes) and BEFORE the territory
# resolution (so we don't bother classifying writes that pass for this
# reason). If the file exists on disk, this is an Edit/MultiEdit on
# existing content, not a creation — let it through.
if [ -f "$FILE_PATH" ]; then exit 0; fi

# ── Decide which planner this write belongs to (if any) ─────────────────
REQUIRED=""
KIND=""

# Family-folder writes are gated by the matching planner — these checks come
# FIRST so a visual binary inside a sim folder is correctly gated by
# simulation-planner (not visual-planner).
case "$FILE_PATH" in
    */source/*/simulations/*/*)
        REQUIRED="simulation-planner"
        KIND="simulation runtime / drawer file" ;;
    */source/*/interactives/*/*)
        REQUIRED="interactive-media-planner"
        KIND="interactive-media runtime / drawer file" ;;
    */source/*/narratives/*/*)
        REQUIRED="narrative-experience-planner"
        KIND="narrative-experience runtime / drawer file" ;;
esac

# If not inside a family folder, check whether it's a visual binary anywhere.
if [ -z "$REQUIRED" ]; then
    case "$FILE_PATH" in
        *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif|*.svg|*.mp4|*.webm|*.mov|*.lottie|*.lottie.json)
            REQUIRED="visual-planner"
            case "$FILE_PATH" in
                *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif)        KIND="raster image" ;;
                *.svg)                                          KIND="SVG / vector" ;;
                *.mp4|*.webm|*.mov)                            KIND="video" ;;
                *.lottie|*.lottie.json)                        KIND="Lottie animation" ;;
            esac ;;
    esac
fi

# Nothing matched → not a gated write (shell HTML / CSS / JS / Markdown
# at the source root, config files, docs, etc.) — let it through.
if [ -z "$REQUIRED" ]; then exit 0; fi

# ── Check whether the required planner was dispatched this session ──────
# Without a transcript we cannot prove dispatch, so allow rather than
# falsely block.
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then exit 0; fi

if grep -aE '"(name|tool_name)"\s*:\s*"(Task|Agent)"' "$TRANSCRIPT" 2>/dev/null \
   | grep -q "\"subagent_type\"\s*:\s*\"$REQUIRED\""; then
    exit 0
fi

# ── Block with a clear, actionable message ──────────────────────────────
BASENAME="${FILE_PATH##*/}"
cat >&2 <<MSG
[Woven v3.8 enforcement] Cannot write this ${KIND} ($BASENAME) until ${REQUIRED} has been dispatched this session.

The file path is in ${REQUIRED}'s territory. The agent in chat doesn't write content inside that territory directly — it scaffolds the app shell HTML with a slot reference (an <iframe src='…'> for sim/im/nx, an <img src='…'> for visual), then dispatches the matching planner to fill the slot's canonical output path.

Do this now:

  Task(subagent_type: "${REQUIRED}",
       description:   "<short>",
       prompt:        "<intent + slotFile + slotLine if any + simId/imId/nxId + branch + projectRoot>")

The planner's playbook covers the slot contract verbatim. Once it's been dispatched at least once this session, further writes inside its territory pass.
MSG
exit 2
