#!/usr/bin/env python3
"""guard-shared-tree.py - PreToolUse(Bash) hook: no git command that discards
working-tree changes, in any project agent.

Every thread in a project edits ONE working tree at the same time: split
threads opened from a plan, other chats the user started, node agents, and the
subagents all of them dispatch. A discard (`git checkout -- f`, `git restore`,
`git stash`, `git reset --hard`, `git clean -f`, a branch switch) throws away
EVERY uncommitted change in that path, not just the caller's. On suss-cal
(2026-09-29) a split thread saw its sibling's edit in `git status`, decided its
own ds-guardian had strayed there, and ran `git checkout -- admin-nav.js`,
erasing the sibling's work. The prose rule telling threads to stay in their
files is what made it "clean up". So this is a hook, not a sentence.

Matcher (registered in serve.py:_ensure_harness_settings): Bash. Applies to
subagents too (agent_type present) - a subagent shares the same tree.

Allowed on purpose: read-only git, `git restore --staged` without
--worktree (unstaging touches no file), `git reset` without --hard/--merge/
--keep (index only), `git stash list|show`, `git clean -n`. Undoing your OWN
edit is an edit, not a discard. Discarding on the user's behalf goes through
the app's git panel.

Must stay a real script file: a bash heredoc replaces stdin and loses the
payload (see require-visual-delegation.py).
"""
import json
import re
import shlex
import sys

DENY = (
    "Blocked: `%s` discards uncommitted changes, and other threads are editing this "
    "same working tree right now (split siblings, other chats, their subagents). It "
    "wipes THEIR work in that path too, not just yours. A changed file you did not "
    "change is someone else's work in progress: leave it, and mention it in your "
    "report if it matters. To undo your OWN edit, edit it back. If the user asked to "
    "discard changes, tell them to use the discard control in the app's git panel."
)

_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n.*?\n\s*\2\s*(?:\n|$)", re.S)
_SPLIT_RE = re.compile(r"&&|\|\||;|\||\n|\$\(|`|\(|\)")
_GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def _strip_heredocs(cmd: str) -> str:
    """Heredoc bodies are data (python scripts, docs), not commands."""
    return _HEREDOC_RE.sub("\n", cmd)


def _git_argv(segment: str):
    """The git subcommand + its args if this segment runs git, else None."""
    try:
        toks = shlex.split(segment, posix=True)
    except ValueError:
        toks = segment.split()
    # Skip env assignments and harmless prefixes (`FOO=1 git ...`, `command git`).
    while toks and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])
                    or toks[0] in ("command", "exec", "nohup", "time", "sudo")):
        toks = toks[1:]
    if not toks or toks[0].rsplit("/", 1)[-1] != "git":
        return None
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        i += 2 if toks[i] in _GIT_GLOBAL_WITH_ARG else 1
    return toks[i:]


def _is_discard(args) -> bool:
    if not args:
        return False
    sub, rest = args[0], args[1:]
    flags = set(a for a in rest if a.startswith("-"))
    if sub in ("checkout", "switch", "checkout-index"):
        return not (flags & {"-h", "--help"})
    if sub == "restore":
        staged_only = ("--staged" in flags or "-S" in flags) and not (flags & {"--worktree", "-W"})
        return not staged_only
    if sub == "stash":
        return not (rest and rest[0] in ("list", "show"))
    if sub == "reset":
        return bool(flags & {"--hard", "--merge", "--keep"})
    if sub == "clean":
        dry = bool(flags & {"-n", "--dry-run"}) or any(
            re.match(r"^-[a-zA-Z]*n", a) for a in rest if not a.startswith("--"))
        forced = "--force" in flags or any(
            re.match(r"^-[a-zA-Z]*f", a) for a in rest if not a.startswith("--"))
        return forced and not dry
    return False


def offending(command: str):
    """The first discarding git segment in a Bash command, or None."""
    for seg in _SPLIT_RE.split(_strip_heredocs(command or "")):
        seg = seg.strip()
        if not seg:
            continue
        args = _git_argv(seg)
        if args is not None and _is_discard(args):
            return seg
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("{}")
        return  # unparseable - fail open, never brick the session
    if (payload.get("tool_name") or "") != "Bash":
        print("{}")
        return
    seg = offending(str((payload.get("tool_input") or {}).get("command") or ""))
    if not seg:
        print("{}")
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY % seg[:160],
        }
    }))


if __name__ == "__main__":
    main()
