#!/bin/bash
# Woven v3.9 - PreToolUse hook that gates Write/Edit/MultiEdit per family.
#
# Each orchestrator owns a territory. The top-level agent (the chat) is allowed
# to write the app shell freely (source/<branch>/*.html, styles.css, app.js,
# any file at the top level of source/<branch>/). But writing INSIDE one of
# the orchestrator-owned folders, or writing a visual binary anywhere, requires
# the matching orchestrator to have been dispatched in this session.
#
# v3.9 adds the LEAF-TERRITORY HARD GATE: the main chat thread may not write
# inside family territories AT ALL - not even Edits to existing files. The
# indonesiaaa build showed why: three s3d subsystem leaves died on 529s and
# the main chat absorbed their work inline (130 Write/Edits at a ~620K-token
# context, ~59% of the project's entire token spend). Leaf work belongs in
# node agents (POST /__workflow/node/<id>/run) or Task subagents, whose
# throwaway contexts stay cheap. The old "edits to existing files always
# pass" rule still applies OUTSIDE territories (shell HTML, css, top-level
# js), and EDITOR-mode chats keep full hand-edit rights everywhere.
#
# Territory map:
#   source/<branch>/simulations/<simId>/*   → simulation-orchestrator
#   source/<branch>/interactives/<imId>/*   → interactive-media-orchestrator
#   source/<branch>/narratives/<nxId>/*     → narrative-experience-orchestrator
#   Visual binaries (png/jpg/svg/video/lottie) NOT inside the three folders
#     above                                  → visual-orchestrator
#   Anything else (HTML shell, css, js, md) → allowed
#
# Subagent exemption: orchestrator subagents (simulation-orchestrator, etc.) and their
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
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)

# No file path → not a file write we can gate; let it through.
if [ -z "$FILE_PATH" ]; then exit 0; fi

# ── Task-subagent exemption (payload discriminator) ──────────────────────
# PreToolUse payloads from inside a Task subagent carry `agent_type`; main
# thread payloads don't (verified empirically 2026-07-24 - same discriminator
# require-visual-delegation.py uses). Subagents - orchestrators, drawers, and
# general-purpose fixers alike - burn their own throwaway context, which is
# exactly where leaf work belongs. Full rights.
if [ -n "$AGENT_TYPE" ]; then exit 0; fi

# ── Node-agent exemption ─────────────────────────────────────────────────
# A per-node spawn (POST /__workflow/node/<id>/run) IS the leaf worker - its
# whole process exists to build inside its territory. Two markers, either
# suffices:
#   1. TH_SPAWN_KIND env, stamped by serve.py at spawn/resume time
#      ("node-agent" for node runs, "planner" for /__dispatch_planner
#      workers - both are delegated throwaway contexts).
#   2. The daemon's kick line ("Begin the task for node `...`") in the
#      transcript - covers spawns from a daemon predating the env stamp.
case "${TH_SPAWN_KIND:-}" in node-agent|planner) exit 0 ;; esac
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] \
   && grep -aq 'Begin the task for node \`' "$TRANSCRIPT" 2>/dev/null; then
    exit 0
fi

# ── Subagent exemption ───────────────────────────────────────────────────
# Each orchestrator subagent's playbook is loaded as its system prompt. The
# subagent transcript begins with the system prompt including "You are
# **<orchestrator>**" (the playbook opening line). Drawer subagents (sim_*,
# im_*, nx_*, *_lens) similarly identify themselves. If the transcript
# carries any of those markers, the calling agent IS the family worker
# and is allowed to write inside its own territory.
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    if grep -aEq 'You are \*\*(simulation-orchestrator|interactive-media-orchestrator|narrative-experience-orchestrator|visual-orchestrator|sim-[a-z0-9-]+|im-[a-z0-9-]+|nx-[a-z0-9-]+|raster-foreground|raster-photo|vector-icon|vector-mark|shader|particle-(2d|gl)|lottie|3d|video|craft-lens|aesthetic-lens|concept-lens)\*\*' "$TRANSCRIPT" 2>/dev/null; then
        exit 0
    fi
fi

# ── Editor-mode chats ────────────────────────────────────────────────────
# Editor-mode is hand-editing existing source files; not the right context
# for orchestrator-gating. (composeModeAwarePrompt() stamps the marker.)
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    LAST_MODE=$(grep -aE "Context: you're chatting from (EDITOR|WORKFLOW) MODE" "$TRANSCRIPT" 2>/dev/null | tail -1)
    case "$LAST_MODE" in
        *"EDITOR MODE"*) exit 0 ;;
    esac
fi

# ── LEAF-TERRITORY HARD GATE (main chat thread only) ─────────────────────
# Reaching here means: not a Task subagent, not a node-agent spawn, not an
# editor-mode chat. This is the long-lived main working thread. It must not
# do leaf work inline - creating OR editing files inside a family territory.
# Every one of these directories has (or gets) an owning canvas node; work
# in them re-reads the main thread's entire context per turn, which is how
# a $0.25-per-trivial-turn thread happens. Re-dispatch instead.
case "$FILE_PATH" in
    */source/*/simulations/*  | */source/*/interactives/* | \
    */source/*/narratives/*   | */source/*/games/*        | \
    */source/*/motionscenes/* | */source/*/scene3d/*      | \
    */source/*/hero3d/*       | */source/*/appnodes/*     | \
    */source/*/_polish/*      | */source/*/_material/*    | \
    */source/*/_artdir/*      | */source/*/audio/*)
        TERRITORY=$(echo "$FILE_PATH" | sed -E 's#.*/source/[^/]+/([^/]+)/.*#\1#')
        BASENAME="${FILE_PATH##*/}"
        cat >&2 <<MSG
[Woven v3.9 leaf-delegation gate] Blocked: the main chat thread must not write ${BASENAME} inside the ${TERRITORY}/ territory - not even a small fix. Leaf work done inline bloats this thread's context (every later turn re-reads it) and starves the owning node of its history.

Do ONE of these instead:

  1. The artefact has an owning canvas node (research/storyboard/scenes/motion/runtime/subsystem/qa_gate...): re-dispatch it -
       curl -X POST "\$TH_DAEMON_URL/__workflow/node/<nodeId>/run"
     If the node's last run died on a transient API error (529 etc), re-running it IS the recovery path - do not absorb its job here.

  2. No node exists yet: dispatch the matching orchestrator via Task to scaffold it (simulation- / interactive-media- / narrative-experience- / game-experience- / motion-studio- / scene-3d- / scrapbook-experience- / interactive-polish- / material- / sound-orchestrator).

  3. Genuinely tiny targeted fix: dispatch a general-purpose Task subagent with a self-contained brief (exact file, exact change, verify step). Task subagents pass this gate; their context is throwaway.

This gate is unconditional for the main thread. EDITOR-mode chats and node agents are exempt.
MSG
        exit 2 ;;
esac

# ── Edits to existing files always pass ─────────────────────────────────
# Orchestrator gating is for SCAFFOLDING - creating the initial sim/im/nx file
# tree, where the orchestrator enforces structure, schema, and lens trios. Once
# those files exist, the editor chat is allowed to apply small targeted
# fixes (a keyboard-focus bug, a CSS tweak, a typo) without re-dispatching
# the orchestrator. That's how the visual-orchestrator works too - once an asset is
# committed, the user can hand-tweak the file.
#
# This check fires AFTER the subagent exemption (so an orchestrator subagent
# creating its initial files still passes) and BEFORE the territory
# resolution (so we don't bother classifying writes that pass for this
# reason). If the file exists on disk, this is an Edit/MultiEdit on
# existing content, not a creation - let it through.
if [ -f "$FILE_PATH" ]; then exit 0; fi

# ── Decide which orchestrator this write belongs to (if any) ─────────────────
REQUIRED=""
KIND=""

# Family-folder writes are gated by the matching orchestrator - these checks come
# FIRST so a visual binary inside a sim folder is correctly gated by
# simulation-orchestrator (not visual-orchestrator).
case "$FILE_PATH" in
    */source/*/simulations/*/*)
        REQUIRED="simulation-orchestrator"
        KIND="simulation runtime / drawer file" ;;
    */source/*/interactives/*/*)
        REQUIRED="interactive-media-orchestrator"
        KIND="interactive-media runtime / drawer file" ;;
    */source/*/narratives/*/*)
        REQUIRED="narrative-experience-orchestrator"
        KIND="narrative-experience runtime / drawer file" ;;
esac

# If not inside a family folder, check whether it's a visual binary anywhere.
if [ -z "$REQUIRED" ]; then
    case "$FILE_PATH" in
        *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif|*.svg|*.mp4|*.webm|*.mov|*.lottie|*.lottie.json)
            REQUIRED="visual-orchestrator"
            case "$FILE_PATH" in
                *.png|*.jpg|*.jpeg|*.webp|*.gif|*.avif)        KIND="raster image" ;;
                *.svg)                                          KIND="SVG / vector" ;;
                *.mp4|*.webm|*.mov)                            KIND="video" ;;
                *.lottie|*.lottie.json)                        KIND="Lottie animation" ;;
            esac ;;
    esac
fi

# Nothing matched → not a gated write (shell HTML / CSS / JS / Markdown
# at the source root, config files, docs, etc.) - let it through.
if [ -z "$REQUIRED" ]; then exit 0; fi

# ── Check whether the required orchestrator was dispatched this session ──────
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

The file path is in ${REQUIRED}'s territory. The agent in chat doesn't write content inside that territory directly - it scaffolds the app shell HTML with a slot reference (an <iframe src='…'> for sim/im/nx, an <img src='…'> for visual), then dispatches the matching orchestrator to fill the slot's canonical output path.

Do this now:

  Task(subagent_type: "${REQUIRED}",
       description:   "<short>",
       prompt:        "<intent + slotFile + slotLine if any + simId/imId/nxId + branch + projectRoot>")

The orchestrator's playbook covers the slot contract verbatim. Once it's been dispatched at least once this session, further writes inside its territory pass.
MSG
exit 2
