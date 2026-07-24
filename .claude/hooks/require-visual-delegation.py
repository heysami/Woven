#!/usr/bin/env python3
"""require-visual-delegation.py - PreToolUse hook enforcing the
VISUAL_DELEGATION_DISCIPLINE deterministically (prose alone decayed: the
suss-cal FA thread took 64 inline preview screenshots + 36 inline image
Reads with the rule sitting in its preamble the whole time).

Rule: the MAIN chat thread must not LOOK at pixels itself - all visual
verification is delegated to a Task subagent whose throwaway context absorbs
the images. Subagents keep full screenshot/Read rights.

Discriminator (verified empirically 2026-07-24): PreToolUse payloads from
inside a Task subagent carry "agent_type" (+ "agent_id"); main-thread
payloads don't. See docs/agents/ds-guardian.md for the QA-side procedure.

Matcher (registered in serve.py:_ensure_harness_settings):
    Read|mcp__claude_preview__preview_screenshot
Decisions:
    - subagent (agent_type present)  -> allow
    - main: preview_screenshot       -> deny (delegate)
    - main: Read of an image file    -> deny (delegate), EXCEPT paths under
      attachments/ (user-pasted images: the discipline's one allowed
      exception - already in context, view once)
    - anything else                  -> allow

NOTE: a plain `python3 - <<'EOF'` bash heredoc CANNOT host this hook - the
heredoc replaces stdin, so the payload is lost and every call fails open.
This must stay a real script file that reads the payload from stdin.
"""
import json
import sys

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("{}")
        return  # unparseable - fail open, never brick the session

    # Inside a Task subagent: full visual rights.
    if payload.get("agent_type"):
        print("{}")
        return

    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}

    deny = None
    if "screenshot" in tool.lower():
        deny = (
            "Blocked: the main chat thread must not screenshot to check work itself "
            "(VISUAL_DELEGATION_DISCIPLINE - images poison this thread's prompt cache and "
            "judgment decays over long threads). Dispatch ONE general-purpose Task subagent "
            "to do the whole look-loop: give it the exact URL(s)/pages, what must be true "
            "visually, which interactions to try; it screenshots freely in its own context "
            "and returns a text verdict. For DS-bound page edits use the ds-guardian brief "
            "($TH_PROTOCOL_ROOT/docs/agents/ds-guardian.md)."
        )
    elif tool == "Read":
        path = str(tool_input.get("file_path") or "")
        low = path.lower()
        if low.endswith(IMAGE_EXTS) and "/attachments/" not in low:
            deny = (
                "Blocked: the main chat thread must not Read image files to judge work "
                "itself (VISUAL_DELEGATION_DISCIPLINE). Dispatch a general-purpose Task "
                "subagent to view %s and report what you need as text. (User-attached "
                "images under attachments/ stay readable here - view those ONCE.)" % path
            )

    if deny:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": deny,
            }
        }))
    else:
        print("{}")


if __name__ == "__main__":
    main()
