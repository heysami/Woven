"""Git / GitHub backbone for Live Session (docs/features/live-session.md §7).

Two layers:

  LOCAL (git)   - connect a project to git, deliberate commit (host-pressed,
                  never automatic), publish (push). Commits credit in-session
                  guests as Co-authored-by trailers (the Claude Code
                  convention). Fully offline; this is the merge/history engine.

  REMOTE (GitHub) - fork, pull-request, and the GitHub OAuth token exchange the
                  collab client needs so guests authenticate in-place. Reads the
                  OAuth app credentials from a config file the user fills (see
                  docs/features/live-session-setup.md); without it the remote
                  layer reports a clear "not configured" error and the local
                  layer still works.

Design choices that match the doc:
  • Commit is DELIBERATE - there is no auto-commit anywhere here; serve.py only
    calls commit() when the host presses the button.
  • Canvas layout is per-machine and NO LONGER lives in the synced file: node
    positions (x/y) and pan/zoom are written to workflow/viewport.json, which is
    gitignored (see serve._GITIGNORE_LOCAL / _workflow_save). So cosmetic canvas
    moves can't churn workflow.json or produce the line-merge conflicts that used
    to corrupt it. workflow.json now carries only the durable graph (node data +
    edges + wb), which merges meaningfully; a real conflict is surfaced by
    conflicted_files() and, as a backstop, healed on load by serve._heal_workflow_json.
  • Agent-assisted conflict resolution: conflicted_files() surfaces the paths;
    serve.py hands them to the host agent. We never hand-merge LLM-regenerated
    HTML/CSS/JS ourselves.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

# ── config ───────────────────────────────────────────────────────────────────
# OAuth app credentials live OUTSIDE the repo. First match wins.
_OAUTH_PATHS = [
    os.path.expanduser("~/.woven/github-oauth.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "github-oauth.json"),
]


def _git(root, *args, timeout=30, input_text=None):
    """Run a git command in `root`. Returns (code, stdout, stderr)."""
    try:
        p = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
            timeout=timeout, input=input_text,
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "git not found - install git"
    except subprocess.TimeoutExpired:
        return 124, "", "git timed out"


def git_available():
    code, _o, _e = _git(".", "--version", timeout=5)
    return code == 0


# ═════════════════════════════════════════════════════════════════════════
# LOCAL - connect / status / commit / publish
# ═════════════════════════════════════════════════════════════════════════

def is_repo(root):
    """True ONLY when `root` is the TOPLEVEL of its own git repo - not when it
    merely sits INSIDE an enclosing repo. This matters because a Woven project
    folder (projects/<id>/) is nested inside the Woven APP's repo: a plain
    --is-inside-work-tree check would walk up, find the app's .git, and make the
    panel show the APP's remote + history (and skip `git init` for the project).
    Requiring toplevel == root keeps git scoped to THIS project and lets
    connect() create a dedicated repo when there isn't one yet."""
    code, out, _e = _git(root, "rev-parse", "--show-toplevel", timeout=8)
    if code != 0 or not out.strip():
        return False
    try:
        return os.path.realpath(out.strip()) == os.path.realpath(root)
    except Exception:
        return False


def connect(root, remote=None, name=None, email=None, default_branch="main"):
    """Make `root` a git repo (idempotent). Optionally set the origin remote +
    a committer identity. Returns status()."""
    if not is_repo(root):
        code, _o, err = _git(root, "init", "-b", default_branch)
        if code != 0:
            # older git without -b
            code, _o, err = _git(root, "init")
            if code != 0:
                raise RuntimeError(f"git init failed: {err.strip()}")
            _git(root, "checkout", "-b", default_branch)
    if name:
        _git(root, "config", "user.name", name)
    if email:
        _git(root, "config", "user.email", email)
    if remote:
        # set-url if origin exists, else add
        code, _o, _e = _git(root, "remote", "get-url", "origin")
        if code == 0:
            _git(root, "remote", "set-url", "origin", remote)
        else:
            _git(root, "remote", "add", "origin", remote)
    return status(root)


def status(root):
    """Working-tree + remote summary for the host's commit/publish UI."""
    if not is_repo(root):
        return {"repo": False}
    out = {"repo": True}
    _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    out["branch"] = branch.strip() or "HEAD"
    _c, porcelain, _e = _git(root, "status", "--porcelain")
    changed = [ln[3:] for ln in porcelain.splitlines() if ln.strip()]
    out["dirty"] = bool(changed)
    out["changed"] = changed[:200]
    out["changedCount"] = len(changed)
    _c, remote, _e = _git(root, "remote", "get-url", "origin")
    out["remote"] = remote.strip() if _c == 0 else ""
    # ahead/behind vs upstream, if any
    out["ahead"] = out["behind"] = 0
    _c, ab, _e = _git(root, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    if _c == 0 and ab.strip():
        try:
            b, a = ab.split()
            out["behind"], out["ahead"] = int(b), int(a)
        except Exception:
            pass
    _c, last, _e = _git(root, "log", "-1", "--pretty=%h %s")
    out["lastCommit"] = last.strip() if _c == 0 else ""
    out["hasCommits"] = _c == 0
    return out


def draft_message(root):
    """Propose a commit message from the changed files. The host edits it; this
    is just a sensible default that names what moved."""
    # -uall so untracked directories aren't collapsed to "source/" (which would
    # hide which prototypes changed on a fresh connect).
    _c, porcelain, _e = _git(root, "status", "--porcelain", "-uall")
    changed = [ln[3:] for ln in porcelain.splitlines() if ln.strip()]
    if not changed:
        return "Woven live session - no changes"
    protos = sorted({p.split("/")[1] for p in changed if p.startswith("source/") and "/" in p[7:]})
    n = len(changed)
    if protos:
        head = "Update " + ", ".join(protos[:3]) + (f" +{len(protos)-3} more" if len(protos) > 3 else "")
    else:
        head = f"Woven live session - {n} file{'s' if n != 1 else ''} changed"
    return head


def clear_stale_index_lock(root, max_age=8):
    """Remove a leftover .git/index.lock when it's older than `max_age` seconds.
    The daemon serialises its own git ops, so a lingering lock means a prior op
    was interrupted (tab close / daemon restart / crash) - not a live op. The age
    floor avoids racing a just-started external `git` in a terminal. Best-effort."""
    lock = os.path.join(root, ".git", "index.lock")
    try:
        import time as _t
        if os.path.isfile(lock) and (_t.time() - os.path.getmtime(lock)) >= max_age:
            os.remove(lock)
            return True
    except OSError:
        pass
    return False


def conflict_marker_files(root):
    """TRACKED, changed files that still contain git conflict markers
    (`<<<<<<< ` / `>>>>>>> ` at line start). Committing these is exactly how a
    synced project ends up with a corrupt, un-openable workflow.json - so commit()
    refuses when this returns anything. Binary / very large / unreadable files are
    skipped (they can't carry the text markers we care about).

    Uses `-uno` (NO untracked files): conflict markers only ever appear in TRACKED
    files coming out of a merge - a brand-new untracked file can't have them.
    Scanning untracked too means reading the entire untracked tree (100k+ files on
    a big project), which turned every commit into a multi-second stall for nothing."""
    code, out, _e = _git(root, "status", "--porcelain", "-uno")
    if code != 0:
        return []
    hits = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        rel = ln[3:].strip()
        if " -> " in rel:                 # rename - take the destination path
            rel = rel.split(" -> ", 1)[1]
        rel = rel.strip().strip('"')
        if not rel or rel.endswith("/"):
            continue
        path = os.path.join(root, rel)
        try:
            if os.path.getsize(path) > 8 * 1024 * 1024:
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("<<<<<<< ") or line.startswith(">>>>>>> "):
                        hits.append(rel)
                        break
        except (OSError, UnicodeDecodeError):
            continue                      # binary / unreadable - no text markers
    return hits


def commit(root, message, coauthors=None, name=None, email=None):
    """Stage everything and commit. `coauthors` is a list of 'Name <email>'
    strings appended as Co-authored-by trailers. Deliberate - only called when
    the host presses Commit. Returns {sha, message}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo - connect it first")
    # Refuse to bake unresolved conflict markers into a commit - that's what
    # corrupts a project's workflow.json and makes it un-openable downstream.
    marked = conflict_marker_files(root)
    if marked:
        shown = ", ".join(marked[:5]) + (f" (+{len(marked) - 5} more)" if len(marked) > 5 else "")
        raise RuntimeError(
            "unresolved merge conflicts - these files still contain conflict "
            f"markers: {shown}. Remove the <<<<<<< / ======= / >>>>>>> lines "
            "(keep the content you want), then commit.")
    msg = (message or "").strip() or draft_message(root)
    trailers = ""
    for ca in (coauthors or []):
        ca = (ca or "").strip()
        if ca:
            trailers += f"\nCo-authored-by: {ca}"
    full = msg + ("\n" + trailers.lstrip("\n") if trailers else "")
    code, _o, err = _git(root, "add", "-A")
    if code != 0:
        raise RuntimeError(f"git add failed: {err.strip()}")
    # nothing staged?
    code, _o, _e = _git(root, "diff", "--cached", "--quiet")
    if code == 0:
        return {"sha": "", "message": full, "empty": True}
    args = ["commit", "-m", full]
    if name:
        args = ["-c", f"user.name={name}"] + args
    if email:
        args = ["-c", f"user.email={email}"] + args
    code, out, err = _git(root, *args)
    if code != 0:
        raise RuntimeError(f"git commit failed: {(err or out).strip()}")
    _c, sha, _e = _git(root, "rev-parse", "HEAD")
    return {"sha": sha.strip(), "message": full, "empty": False}


def publish(root, token=None):
    """Push HEAD to origin. If a token is given, use it for this push only
    (https remote) so we never persist credentials. Returns {ok, detail}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    code, remote, _e = _git(root, "remote", "get-url", "origin")
    if code != 0 or not remote.strip():
        raise RuntimeError("no 'origin' remote - connect the project to GitHub first")
    _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip() or "main"
    push_args = ["push", "-u", "origin", branch]
    env_remote = None
    if token and remote.strip().startswith("https://"):
        # one-shot authenticated URL; not written to config
        env_remote = remote.strip().replace("https://", f"https://x-access-token:{token}@", 1)
        push_args = ["push", "-u", env_remote, branch]
    code, out, err = _git(root, *push_args, timeout=120)
    if code != 0:
        raise RuntimeError(f"git push failed: {(err or out).strip()[:400]}")
    return {"ok": True, "branch": branch, "detail": (err or out).strip()[:400]}


def pull(root, token=None):
    """Fetch + merge origin into the current branch. GUARDED by the caller:
    serve.py only invokes this on a clean tree with no active live session, so
    we never merge remote history on top of in-flight host/guest edits (Live is
    host-authoritative). On conflict we leave the tree mid-merge and report the
    conflicted paths so the existing resolve() flow picks them up. If a token is
    given, use it for this fetch only (https remote) so we never persist creds.
    Returns {ok, branch, detail, conflicts}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    code, remote, _e = _git(root, "remote", "get-url", "origin")
    if code != 0 or not remote.strip():
        raise RuntimeError("no 'origin' remote - connect the project to GitHub first")
    _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip() or "main"
    # --no-rebase pins the MERGE strategy. Without it, modern git (2.27+) refuses
    # to reconcile DIVERGENT branches unless pull.rebase is configured, failing
    # with "Need to specify how to reconcile divergent branches". We always merge
    # (host-authoritative): conflicts land in the working tree for resolve().
    pull_args = ["pull", "--no-rebase", "--no-edit", "origin", branch]
    if token and remote.strip().startswith("https://"):
        # one-shot authenticated URL; not written to config
        env_remote = remote.strip().replace("https://", f"https://x-access-token:{token}@", 1)
        pull_args = ["pull", "--no-rebase", "--no-edit", env_remote, branch]
    code, out, err = _git(root, *pull_args, timeout=120)
    conflicts = conflicted_files(root)
    if code != 0 and not conflicts:
        raise RuntimeError(f"git pull failed: {(err or out).strip()[:400]}")
    return {"ok": not conflicts, "branch": branch,
            "detail": (out or err).strip()[:400], "conflicts": conflicts}


def discard_local(root):
    """Throw away UNCOMMITTED changes - reset the working tree back to the last
    local commit (HEAD) and remove untracked files. No remote involved. This is
    the escape hatch for "I just want my unsaved edits gone": `git reset --hard
    HEAD` + `git clean -fd`. `clean` is intentionally WITHOUT -x, so .gitignore'd
    runtime artifacts survive - only untracked *tracked-worthy* files are removed.
    Returns {ok, head, removed}. Destructive; the caller confirms first."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    _c, head_before, _e = _git(root, "rev-parse", "HEAD")
    if _c != 0:
        raise RuntimeError("no commits yet - nothing to reset to")
    code, out, err = _git(root, "reset", "--hard", "HEAD", timeout=120)
    if code != 0:
        raise RuntimeError(f"git reset failed: {(err or out).strip()[:400]}")
    _c, cleaned, _e = _git(root, "clean", "-fd", timeout=120)
    removed = [ln[len("Removing "):].strip() for ln in cleaned.splitlines()
               if ln.startswith("Removing ")]
    _c, head, _e = _git(root, "rev-parse", "--short", "HEAD")
    return {"ok": True, "head": head.strip(), "removed": removed[:200]}


def discard_to_remote(root, token=None):
    """Roll the branch ALL the way back to match origin - `git fetch` then
    `git reset --hard origin/<branch>` + `git clean -fd`. Unlike pull() (which
    only merges remote commits FORWARD and can never remove a local commit), this
    DISCARDS local commits AND uncommitted changes so the tree exactly matches
    GitHub. Works on a dirty tree (no forced commit). If a token is given, use it
    for the fetch only (https remote) so we never persist credentials. `clean` is
    WITHOUT -x so .gitignore'd runtime artifacts survive. Returns {ok, branch,
    head, removed, detail}. Destructive; the caller confirms first."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    code, remote, _e = _git(root, "remote", "get-url", "origin")
    if code != 0 or not remote.strip():
        raise RuntimeError("no 'origin' remote - connect the project to GitHub first")
    _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip() or "main"
    fetch_args = ["fetch", "origin", branch]
    if token and remote.strip().startswith("https://"):
        # one-shot authenticated URL; not written to config
        env_remote = remote.strip().replace("https://", f"https://x-access-token:{token}@", 1)
        fetch_args = ["fetch", env_remote, branch]
    code, out, err = _git(root, *fetch_args, timeout=120)
    if code != 0:
        raise RuntimeError(f"git fetch failed: {(err or out).strip()[:400]}")
    # Reset to the freshly-fetched ref. FETCH_HEAD is what we just brought down
    # (origin/<branch> may not exist yet on a never-fetched repo); it points at
    # the same commit and always exists post-fetch.
    code, out, err = _git(root, "reset", "--hard", "FETCH_HEAD", timeout=120)
    if code != 0:
        raise RuntimeError(f"git reset failed: {(err or out).strip()[:400]}")
    _c, cleaned, _e = _git(root, "clean", "-fd", timeout=120)
    removed = [ln[len("Removing "):].strip() for ln in cleaned.splitlines()
               if ln.startswith("Removing ")]
    _c, head, _e = _git(root, "rev-parse", "--short", "HEAD")
    return {"ok": True, "branch": branch, "head": head.strip(),
            "removed": removed[:200], "detail": (out or err).strip()[:400]}


def clone(dest, clone_url, token=None):
    """git clone `clone_url` into `dest` (which must NOT already exist). When a
    token is given and the URL is https, authenticate with a one-shot
    x-access-token URL (same pattern as publish()/pull()) so private repos work
    and the credential is never written to .git/config. `git clone` sets
    `origin` itself, so the resulting repo is ready for pull()/publish() with no
    follow-up connect(). Returns {ok, dest}; raises RuntimeError on failure."""
    url = (clone_url or "").strip()
    if not url:
        raise RuntimeError("missing clone url")
    fetch_url = url
    if token and url.startswith("https://"):
        # one-shot authenticated URL; not persisted (git clone records the bare
        # `url` as origin because we pass it via the source arg, not config -
        # but to be safe we reset origin to the token-free URL after cloning).
        fetch_url = url.replace("https://", f"https://x-access-token:{token}@", 1)
    parent = os.path.dirname(os.path.abspath(dest))
    os.makedirs(parent, exist_ok=True)
    code, out, err = _git(parent, "clone", fetch_url, os.path.abspath(dest), timeout=300)
    if code != 0:
        raise RuntimeError(f"git clone failed: {(err or out).strip()[:400]}")
    # Make sure origin carries the clean (token-free) URL even if git recorded
    # the authenticated one - we never persist credentials in config.
    if fetch_url != url:
        _git(dest, "remote", "set-url", "origin", url)
    return {"ok": True, "dest": os.path.abspath(dest)}


# ── sync-version + gitignore helpers ─────────────────────────────────────────
# A project repo records the Woven SYNC version (an int the daemon bumps only
# when a synced on-disk format changes) in `.woven/version`. push/pull are gated
# on it so an OLD daemon can't merge a repo written by a newer (incompatible)
# Woven - which is how a project gets corrupted across machines. serve.py owns
# the WOVEN_SYNC_VERSION constant and calls these.

def read_sync_version(root):
    """Sync version recorded in the working tree's .woven/version, or None."""
    try:
        with open(os.path.join(root, ".woven", "version"), "r", encoding="utf-8") as f:
            s = f.read().strip()
        return int(s) if s else None
    except (FileNotFoundError, NotADirectoryError, ValueError, OSError):
        return None


def write_sync_version(root, version):
    """Stamp .woven/version with `version` (creates .woven/ if needed)."""
    d = os.path.join(root, ".woven")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "version"), "w", encoding="utf-8") as f:
        f.write(str(int(version)) + "\n")


def remote_sync_version(root, branch=None, token=None):
    """Sync version recorded on origin/<branch> WITHOUT merging - fetch the ref
    (one-shot token URL for private repos), then read it out of FETCH_HEAD.
    Returns int, or None when there's no origin / no version file / offline.
    The caller treats None as 'legacy, compatible'."""
    code, remote, _e = _git(root, "remote", "get-url", "origin")
    if code != 0 or not remote.strip():
        return None
    if not branch:
        _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
        branch = branch.strip() or "main"
    fetch_ref = remote.strip()
    if token and fetch_ref.startswith("https://"):
        fetch_ref = fetch_ref.replace("https://", f"https://x-access-token:{token}@", 1)
    # Updates FETCH_HEAD only; never touches the working tree.
    fcode, _fo, _fe = _git(root, "fetch", fetch_ref, branch, timeout=60)
    if fcode != 0:
        return None
    code, out, _e = _git(root, "show", "FETCH_HEAD:.woven/version")
    if code != 0:
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def ensure_gitignore(root, lines):
    """Idempotently ensure each entry in `lines` is present in <root>/.gitignore,
    keeping per-machine local files (e.g. workflow/viewport.json) out of the
    synced repo. No-op for entries already listed."""
    path = os.path.join(root, ".gitignore")
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    except (FileNotFoundError, OSError):
        existing = ""
    have = {ln.strip() for ln in existing.splitlines()}
    add = [ln for ln in lines if ln.strip() and ln.strip() not in have]
    if add:
        block = ""
        if existing and not existing.endswith("\n"):
            block += "\n"
        if "# Woven - per-machine local state" not in existing:
            block += "# Woven - per-machine local state (never sync)\n"
        block += "\n".join(add) + "\n"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(block)
        except OSError:
            pass
    # A path added to .gitignore that git is ALREADY tracking keeps getting
    # committed - ignore rules only suppress UNtracked files. Untrack any
    # now-ignored-but-still-tracked path (e.g. a legacy repo that committed
    # editor/chat.jsonl before it was ignored) so the next commit drops it.
    # Runs even when `add` is empty so already-listed-but-tracked files
    # still self-heal.
    untrack_ignored(root)


def ensure_gitattributes(root, lines):
    """Idempotently ensure each entry in `lines` is present in
    <root>/.gitattributes. Used to pin merge strategies for files the daemon
    merges SEMANTICALLY: share/comments.json is marked merge=binary so git
    never line-merges it - a lucky line merge works, an unlucky one bakes
    invalid JSON with no conflict markers (which then reads as "every comment
    vanished"). merge=binary makes concurrent edits always conflict, and the
    daemon's union merge resolves them (serve._autoresolve_comments_conflict).
    The file is committed, so the strategy rides the sync to every machine."""
    path = os.path.join(root, ".gitattributes")
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    except (FileNotFoundError, OSError):
        existing = ""
    have = {ln.strip() for ln in existing.splitlines()}
    add = [ln for ln in lines if ln.strip() and ln.strip() not in have]
    if not add:
        return
    block = ""
    if existing and not existing.endswith("\n"):
        block += "\n"
    if "# Woven - daemon-managed merge strategies" not in existing:
        block += "# Woven - daemon-managed merge strategies\n"
    block += "\n".join(add) + "\n"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(block)
    except OSError:
        pass


def untrack_ignored(root):
    """Drop tracked files that match .gitignore from the INDEX, keeping them on
    disk. Ignore rules never apply to already-tracked paths, so a file committed
    before it was ignored dirties the tree on every regeneration - forever.
    `-c` = cached/tracked, `-i --exclude-standard` = filtered to .gitignore
    matches; `rm --cached` removes only the index entry. The removals are left
    STAGED - a commit (the user's next one, or heal_tracked_ignored's
    housekeeping commit) still has to land for the tree to go clean. Chunked:
    a legacy repo can carry thousands of these (undo history, run thumbnails)
    and one argv would blow the exec limit. Returns the untracked paths."""
    if not is_repo(root):
        return []
    code, out, _e = _git(root, "ls-files", "-z", "-ci", "--exclude-standard")
    if code != 0 or not out:
        return []
    paths = [p for p in out.split("\0") if p]
    for i in range(0, len(paths), 500):
        _git(root, "rm", "--cached", "-r", "--quiet", "--", *paths[i:i + 500], timeout=60)
    return paths


def heal_tracked_ignored(root):
    """One-shot self-heal for the 'panel always says commit' trap: untrack
    ignored-but-tracked paths AND commit just those deletions as a housekeeping
    commit, so the tree goes clean without user action. Strictly scoped - it
    refuses to commit when the staged set contains ANYTHING besides deletions
    of ignore-matched paths (never sweeps user work into the housekeeping
    commit) and skips entirely mid-merge. Returns {healed, count, ...}."""
    if not is_repo(root):
        return {"healed": False, "reason": "not a repo"}
    if conflicted_files(root):
        return {"healed": False, "reason": "merge in progress"}
    untrack_ignored(root)
    # Everything staged now must be a deletion of an ignore-matched path. A
    # deletion may also predate this call (an earlier ensure_gitignore untrack
    # that never got committed) - that's fine, it passes the same check.
    code, out, _e = _git(root, "diff", "--cached", "--name-status", "-z")
    if code != 0:
        return {"healed": False, "reason": "no HEAD"}
    toks = out.split("\0")
    staged = []
    i = 0
    while i < len(toks) - 1:
        s = toks[i]
        if not s:
            i += 1
            continue
        if s[0] in ("R", "C"):        # rename/copy - not a deletion, bail
            return {"healed": False, "reason": "user work already staged"}
        staged.append((s[0], toks[i + 1]))
        i += 2
    if not staged:
        return {"healed": False, "count": 0}
    if any(s != "D" for s, _p in staged):
        return {"healed": False, "reason": "user work already staged"}
    paths = [p for _s, p in staged]
    code, out, _e = _git(root, "check-ignore", "-z", "--stdin",
                         input_text="\0".join(paths) + "\0")
    matched = {p for p in out.split("\0") if p} if code in (0, 1) else set()
    if set(paths) - matched:
        return {"healed": False, "reason": "staged deletion not ignore-matched"}
    n = len(paths)
    msg = "Stop tracking {} generated file{} covered by .gitignore".format(
        n, "s" if n != 1 else "")
    args = ["commit", "-m", msg]
    _c, uname, _e = _git(root, "config", "user.name")
    if not uname.strip():                 # identity fallback - never fail on config
        args = ["-c", "user.name=Woven", "-c", "user.email=woven@local"] + args
    code, out, err = _git(root, *args, timeout=120)
    if code != 0:
        return {"healed": False, "reason": (err or out).strip()[:200]}
    _c, sha, _e = _git(root, "rev-parse", "HEAD")
    return {"healed": True, "count": n, "sha": sha.strip()}


def log(root, limit=30):
    """Recent commit history for the panel's history view. Returns a list of
    {sha, short, subject, author, relative, iso}, newest first. \\x1f field +
    \\n record separators so subjects with spaces/pipes survive the split."""
    if not is_repo(root):
        return []
    fmt = "%H%x1f%h%x1f%s%x1f%an%x1f%ar%x1f%aI"
    code, out, _e = _git(root, "log", f"-{int(limit)}", f"--pretty=format:{fmt}")
    if code != 0:
        return []
    rows = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\x1f")
        if len(parts) < 6:
            continue
        rows.append({"sha": parts[0], "short": parts[1], "subject": parts[2],
                     "author": parts[3], "relative": parts[4], "iso": parts[5]})
    return rows


def conflicted_files(root):
    """Paths with merge conflicts (for agent-assisted resolution)."""
    if not is_repo(root):
        return []
    code, out, _e = _git(root, "diff", "--name-only", "--diff-filter=U")
    return [ln for ln in out.splitlines() if ln.strip()] if code == 0 else []


def conflict_stage_text(root, rel, stage):
    """Content of one side of a conflicted file - stage 1=base, 2=ours,
    3=theirs. Empty string when that stage doesn't exist (an add/add conflict
    has no base). Feeds the semantic mergers (share comments) that resolve a
    conflict without hand-editing markers."""
    code, out, _e = _git(root, "show", ":{}:{}".format(int(stage), rel), timeout=30)
    return out if code == 0 else ""


def resolve_conflict_file(root, rel, text):
    """Overwrite a conflicted file with merged content and stage it - the git
    half of a semantic auto-resolution. The merge itself stays with the caller
    (e.g. shares.comments_merge_texts); this just writes + `git add`s."""
    path = os.path.join(root, rel)
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    code, _o, err = _git(root, "add", "--", rel)
    if code != 0:
        raise RuntimeError("git add failed: {}".format(err.strip()))


def conclude_merge_if_resolved(root):
    """Finish an in-progress merge once nothing is conflicted anymore (the
    commit `git pull` would have made had the merge been clean). No-op unless
    MERGE_HEAD exists and conflicted_files() is empty - a half-resolved merge
    stays mid-merge for the agent-assisted resolve flow. Returns True when a
    merge commit landed."""
    if not is_repo(root):
        return False
    code, _o, _e = _git(root, "rev-parse", "-q", "--verify", "MERGE_HEAD")
    if code != 0:
        return False
    if conflicted_files(root):
        return False
    args = ["commit", "--no-edit"]
    _c, uname, _e = _git(root, "config", "user.name")
    if not uname.strip():                 # identity fallback - never fail on config
        args = ["-c", "user.name=Woven", "-c", "user.email=woven@local"] + args
    code, out, err = _git(root, *args, timeout=120)
    return code == 0


# ═════════════════════════════════════════════════════════════════════════
# LOCAL - branches (fork / switch / merge), the offline divergent-work engine
# ═════════════════════════════════════════════════════════════════════════
# Distinct from Woven "prototypes" (source/<slug>/ subdirs in ONE repo): these
# are real git branches. Forking = make a branch off HEAD and keep editing it;
# merging = fold a branch back into the current one. Conflicts land in the tree
# for the SAME agent-assisted resolve() flow that pull() uses.

# A branch name git accepts but that we still refuse: anything with whitespace,
# control chars, or the patterns `git check-ref-format` rejects. We keep the
# check permissive (git is the real gate) but block the obvious foot-guns.
_BAD_BRANCH = ("..", "~", "^", ":", "?", "*", "[", "\\", " ", "\t", "@{")


def current_branch(root):
    """The checked-out branch name (or 'HEAD' when detached / empty repo)."""
    _c, branch, _e = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return (branch.strip() or "HEAD")


def _norm_branch_name(root, name):
    n = (name or "").strip().strip("/")
    if not n:
        raise RuntimeError("branch name required")
    if n.startswith("-") or n.endswith(".") or n.endswith(".lock"):
        raise RuntimeError(f"invalid branch name: {name!r}")
    for bad in _BAD_BRANCH:
        if bad in n:
            raise RuntimeError(f"invalid branch name (contains {bad!r}): {name!r}")
    # Let git have the final say (catches anything our blocklist misses).
    code, _o, err = _git(root, "check-ref-format", "--branch", n)
    if code != 0:
        raise RuntimeError(f"invalid branch name: {err.strip() or name!r}")
    return n


def branches(root):
    """Local branches with per-branch divergence vs their upstream. Returns
    {current, branches:[{name, current, upstream, ahead, behind}]}. Cheap enough
    to fold into status() (a couple of `git for-each-ref` reads)."""
    if not is_repo(root):
        return {"current": "", "branches": []}
    cur = current_branch(root)
    # name + upstream + ahead/behind in one shot; \x1f field separator.
    fmt = "%(refname:short)%1f%(upstream:short)%1f%(upstream:track)"
    code, out, _e = _git(root, "for-each-ref", "--sort=-committerdate",
                         f"--format={fmt}", "refs/heads/")
    rows = []
    if code == 0:
        for ln in out.splitlines():
            if not ln.strip():
                continue
            parts = ln.split("\x1f")
            name = parts[0].strip()
            upstream = parts[1].strip() if len(parts) > 1 else ""
            track = parts[2].strip() if len(parts) > 2 else ""
            ahead = behind = 0
            # `[ahead 2, behind 1]` / `[ahead 3]` / `[behind 4]` / `[gone]`
            ma = re.search(r"ahead (\d+)", track)
            mb = re.search(r"behind (\d+)", track)
            if ma:
                ahead = int(ma.group(1))
            if mb:
                behind = int(mb.group(1))
            rows.append({"name": name, "current": name == cur,
                         "upstream": upstream, "ahead": ahead, "behind": behind})
    return {"current": cur, "branches": rows}


def create_branch(root, name, checkout=True):
    """Make a new branch off the current HEAD (the 'fork'). With checkout=True
    (default) switch to it, CARRYING any uncommitted edits onto the new branch -
    so 'fork this' keeps your in-flight work. Returns {ok, branch}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo - connect it first")
    n = _norm_branch_name(root, name)
    code, _o, err = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{n}")
    if code == 0:
        raise RuntimeError(f"branch {n!r} already exists")
    args = ["checkout", "-b", n] if checkout else ["branch", n]
    code, out, err = _git(root, *args, timeout=60)
    if code != 0:
        raise RuntimeError(f"create branch failed: {(err or out).strip()[:400]}")
    return {"ok": True, "branch": n}


def switch_branch(root, name):
    """Check out an existing branch. GUARDED by the caller (serve.py refuses on a
    dirty tree / active live session) so we never carry edits across branches by
    surprise. Returns {ok, branch}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    n = (name or "").strip()
    if not n:
        raise RuntimeError("branch name required")
    code, out, err = _git(root, "checkout", n, timeout=60)
    if code != 0:
        raise RuntimeError(f"switch failed: {(err or out).strip()[:400]}")
    return {"ok": True, "branch": current_branch(root)}


def merge_branch(root, name):
    """Merge `name` INTO the current branch (`git merge --no-ff --no-edit`). On
    conflict, leave the tree mid-merge and report the conflicted paths so the
    existing resolve() flow picks them up - identical to pull()'s contract.
    Returns {ok, branch, merged, conflicts, detail}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    src = (name or "").strip()
    if not src:
        raise RuntimeError("branch to merge required")
    cur = current_branch(root)
    if src == cur:
        raise RuntimeError("can't merge a branch into itself")
    code, _o, err = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{src}")
    if code != 0:
        raise RuntimeError(f"branch {src!r} does not exist")
    # --no-ff keeps a merge commit so the history shows the fork was folded back.
    code, out, err = _git(root, "merge", "--no-ff", "--no-edit", src, timeout=120)
    conflicts = conflicted_files(root)
    if code != 0 and not conflicts:
        raise RuntimeError(f"merge failed: {(err or out).strip()[:400]}")
    return {"ok": not conflicts, "branch": cur, "merged": src,
            "conflicts": conflicts, "detail": (out or err).strip()[:400]}


def delete_branch(root, name, force=False):
    """Delete a local branch (`git branch -d`, or `-D` when force). Refuses to
    delete the checked-out branch. Returns {ok, branch}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo")
    n = (name or "").strip()
    if not n:
        raise RuntimeError("branch name required")
    if n == current_branch(root):
        raise RuntimeError("can't delete the branch you're on - switch away first")
    flag = "-D" if force else "-d"
    code, out, err = _git(root, "branch", flag, n)
    if code != 0:
        msg = (err or out).strip()[:400]
        if not force and "not fully merged" in msg:
            raise RuntimeError(
                f"branch {n!r} has commits not merged into another branch - "
                "delete with force to discard them.")
        raise RuntimeError(f"delete branch failed: {msg}")
    return {"ok": True, "branch": n}


def head_sha(root):
    """Full sha of HEAD ('' when no commits / not a repo)."""
    if not is_repo(root):
        return ""
    code, out, _e = _git(root, "rev-parse", "HEAD")
    return out.strip() if code == 0 else ""


def show_at_ref(root, ref, rel):
    """Content of a tracked file at a ref ('' when the ref or path doesn't
    exist). Feeds the cross-branch semantic mergers (share comments carry
    across a branch switch)."""
    if not is_repo(root) or not (ref or "").strip() or not (rel or "").strip():
        return ""
    code, out, _e = _git(root, "show", "{}:{}".format(ref.strip(), rel.strip()), timeout=30)
    return out if code == 0 else ""


def merge_base(root, a, b):
    """Common-ancestor sha of two refs ('' when unrelated or unknown)."""
    if not is_repo(root) or not (a or "").strip() or not (b or "").strip():
        return ""
    code, out, _e = _git(root, "merge-base", a.strip(), b.strip(), timeout=30)
    return out.strip() if code == 0 else ""


def ls_files_at_ref(root, ref, prefix):
    """Tracked file paths under `prefix` at a ref ([] when none / no ref)."""
    if not is_repo(root) or not (ref or "").strip():
        return []
    code, out, _e = _git(root, "ls-tree", "-r", "--name-only",
                         ref.strip(), "--", prefix, timeout=30)
    return [ln for ln in out.splitlines() if ln.strip()] if code == 0 else []


def restore_paths_from_ref(root, ref, rels):
    """Materialise specific paths from a ref into the working tree
    (`git checkout <ref> -- <paths>`; also stages them). Used to carry
    comment screenshots/attachments across a branch switch. Best-effort."""
    rels = [r for r in (rels or []) if (r or "").strip()]
    if not is_repo(root) or not (ref or "").strip() or not rels:
        return False
    code, _o, _e = _git(root, "checkout", ref.strip(), "--", *rels, timeout=60)
    return code == 0


def dirty_entries(root):
    """[(xy, rel)] for every non-clean path. `-uall` so files inside untracked
    directories are listed individually (a bare dir entry can't be reverted
    path-by-path). Rename entries keep the NEW side."""
    if not is_repo(root):
        return []
    code, out, _e = _git(root, "status", "--porcelain", "-uall")
    entries = []
    if code == 0:
        for ln in out.splitlines():
            if not ln.strip():
                continue
            xy, rel = ln[:2], ln[3:]
            if " -> " in rel:
                rel = rel.split(" -> ", 1)[1]
            entries.append((xy, rel.strip()))
    return entries


def revert_paths(root, entries):
    """Clear local changes on exactly these dirty entries: untracked files are
    deleted, tracked modifications restored from HEAD, staged-new files
    unstaged then removed. Callers SNAPSHOT the content first - this exists so
    a tree-touching op (switch / merge / pull) can run on mechanically-merged
    files (share metadata) whose content is put back by a carry afterwards."""
    for xy, rel in entries or []:
        rel = (rel or "").strip()
        if not rel:
            continue
        p = os.path.join(root, rel)
        if xy == "??":
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
            continue
        _git(root, "reset", "-q", "HEAD", "--", rel)
        code, _o, _e = _git(root, "checkout", "--", rel)
        if code != 0 and os.path.isfile(p):
            # Not in HEAD (was staged-new) - clearing means removing.
            try:
                os.remove(p)
            except OSError:
                pass
    return True


# ═════════════════════════════════════════════════════════════════════════
# LOCAL - diff / compare (read-only; powers the panel's compare view)
# ═════════════════════════════════════════════════════════════════════════

_DIFF_MAX = 400 * 1024  # cap any single diff payload so a huge file can't OOM the panel


def _cap(text):
    if text and len(text) > _DIFF_MAX:
        return text[:_DIFF_MAX] + "\n… (diff truncated)\n"
    return text or ""


def diff_working(root, path=None):
    """Unified diff of the working tree vs HEAD (staged + unstaged), optionally
    scoped to one path. This is 'what changed since my last commit'. Returns
    {kind:'working', path, diff}."""
    if not is_repo(root):
        return {"kind": "working", "path": path or "", "diff": ""}
    args = ["diff", "HEAD", "--"]
    if path:
        args.append(path)
    else:
        args = ["diff", "HEAD"]
    code, out, _e = _git(root, *args, timeout=30)
    return {"kind": "working", "path": path or "", "diff": _cap(out) if code == 0 else ""}


def diff_commit(root, sha):
    """Unified diff a single commit introduced (`git show`). Returns
    {kind:'commit', sha, diff}."""
    if not is_repo(root) or not (sha or "").strip():
        return {"kind": "commit", "sha": sha or "", "diff": ""}
    code, out, _e = _git(root, "show", "--no-color", sha.strip(), timeout=30)
    return {"kind": "commit", "sha": sha.strip(), "diff": _cap(out) if code == 0 else ""}


def diff_range(root, a, b):
    """Unified diff between two refs/branches `a..b` (what b has that a doesn't).
    Returns {kind:'range', a, b, diff}."""
    if not is_repo(root):
        return {"kind": "range", "a": a or "", "b": b or "", "diff": ""}
    a = (a or "").strip(); b = (b or "").strip()
    if not a or not b:
        raise RuntimeError("two refs required to compare")
    code, out, _e = _git(root, "diff", "--no-color", f"{a}...{b}", timeout=30)
    return {"kind": "range", "a": a, "b": b, "diff": _cap(out) if code == 0 else ""}


def diff_conflict(root, path):
    """The three sides of a conflicted file for a side-by-side compare:
    base (merge ancestor, stage :1), ours (stage :2), theirs (stage :3), plus the
    working copy WITH markers. Empty string for any stage that doesn't exist
    (add/add conflicts have no base). Returns {kind:'conflict', path, base, ours,
    theirs, merged}."""
    if not is_repo(root) or not (path or "").strip():
        return {"kind": "conflict", "path": path or "", "base": "", "ours": "", "theirs": "", "merged": ""}
    p = path.strip()

    def _stage(n):
        code, out, _e = _git(root, "show", f":{n}:{p}", timeout=30)
        return _cap(out) if code == 0 else ""

    merged = ""
    try:
        with open(os.path.join(root, p), "r", encoding="utf-8") as f:
            merged = _cap(f.read())
    except (OSError, UnicodeDecodeError):
        merged = ""
    return {"kind": "conflict", "path": p, "base": _stage(1),
            "ours": _stage(2), "theirs": _stage(3), "merged": merged}


# ═════════════════════════════════════════════════════════════════════════
# REMOTE - GitHub OAuth + fork + PR
# ═════════════════════════════════════════════════════════════════════════

def oauth_config():
    """Load the GitHub OAuth app credentials, or None if not set up."""
    for p in _OAUTH_PATHS:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("client_id") and cfg.get("client_secret"):
                    return cfg
            except Exception:
                pass
    return None


def oauth_configured():
    return oauth_config() is not None


def _gh_api(method, path, token=None, body=None, timeout=20):
    url = "https://api.github.com" + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Woven-Live")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"message": str(e)}


def oauth_exchange(code, redirect_uri=None):
    """Exchange an OAuth `code` for an access token. Returns {access_token,...}
    or raises with the GitHub error."""
    cfg = oauth_config()
    if cfg is None:
        raise RuntimeError("GitHub OAuth is not configured on this host (see live-session-setup.md)")
    body = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
    }
    if redirect_uri:
        body["redirect_uri"] = redirect_uri
    data = json.dumps(body).encode()
    req = urllib.request.Request("https://github.com/login/oauth/access_token",
                                 data=data, method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Woven-Live")
    with urllib.request.urlopen(req, timeout=20) as resp:
        out = json.loads(resp.read().decode() or "{}")
    if "access_token" not in out:
        raise RuntimeError(out.get("error_description") or out.get("error") or "token exchange failed")
    return out


# ── Device Flow - the OAuth variant for changing tunnel hostnames ────────────
# Web OAuth needs a fixed registered callback URL; quick-tunnel hostnames churn
# every restart, so we use the Device Flow instead: the guest enters a short
# code at github.com/login/device, no redirect URI involved. Requires the OAuth
# app to have "Device Flow" enabled (a checkbox). Scope `repo` so the guest can
# fork (incl. private) and open PRs.
GH_DEVICE_SCOPE = "repo"

def _gh_form_post(url, body, timeout=20):
    data = urllib.parse.urlencode(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "Woven-Live")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")

def device_start(scope=GH_DEVICE_SCOPE):
    cfg = oauth_config()
    if cfg is None:
        raise RuntimeError("GitHub OAuth is not configured on this host (see live-session-setup.md)")
    out = _gh_form_post("https://github.com/login/device/code",
                        {"client_id": cfg["client_id"], "scope": scope})
    if "device_code" not in out:
        raise RuntimeError(out.get("error_description") or "device flow start failed")
    return out  # {device_code, user_code, verification_uri, expires_in, interval}

def device_poll(device_code):
    """Poll for the token. Returns {access_token,...} when authorized, else
    {error: 'authorization_pending'|'slow_down'|'expired_token'|...}."""
    cfg = oauth_config()
    if cfg is None:
        raise RuntimeError("GitHub OAuth is not configured on this host")
    return _gh_form_post("https://github.com/login/oauth/access_token", {
        "client_id": cfg["client_id"], "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    })


def gh_user(token):
    code, j = _gh_api("GET", "/user", token=token)
    if code != 200:
        raise RuntimeError(j.get("message") or f"GitHub /user {code}")
    return {"login": j.get("login"), "name": j.get("name"), "avatar": j.get("avatar_url")}


# ── Host token store ─────────────────────────────────────────────────────────
# The editor host signs in ONCE with their GitHub account; the token is reused
# for repo listing + push/pull across ALL of the host's projects. The ACCOUNT is
# per-host, the REPO is per-project (set as that project's origin remote). The
# token lives OUTSIDE any repo at ~/.woven/github-token.json, mode 0600, and is
# never sent to the browser - only the login + avatar are surfaced.
_TOKEN_PATH = os.path.expanduser("~/.woven/github-token.json")


def save_token(access_token, login="", avatar=""):
    os.makedirs(os.path.dirname(_TOKEN_PATH), exist_ok=True)
    with open(_TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"access_token": access_token, "login": login, "avatar": avatar}, f)
    try:
        os.chmod(_TOKEN_PATH, 0o600)
    except OSError:
        pass
    return {"login": login, "avatar": avatar}


def load_token():
    try:
        with open(_TOKEN_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def clear_token():
    try:
        os.remove(_TOKEN_PATH)
    except OSError:
        pass
    return {"ok": True}


def host_token():
    """The stored access token, or None - what push/pull/list reach for."""
    return (load_token() or {}).get("access_token") or None


# The status endpoint polls every ~10s from two UI surfaces, so the validity
# probe caches per token. Only an explicit 401 from GitHub marks the token
# expired - network trouble or rate limiting must never raise a false alarm.
_TOKEN_CHECK = {"token": None, "expired": False, "ts": 0.0}
_TOKEN_CHECK_TTL = 600  # seconds


def token_expired(force=False):
    """True only when GitHub explicitly rejects the stored token (HTTP 401)."""
    tok = host_token()
    if not tok:
        return False
    now = time.time()
    if (not force and _TOKEN_CHECK["token"] == tok
            and now - _TOKEN_CHECK["ts"] < _TOKEN_CHECK_TTL):
        return _TOKEN_CHECK["expired"]
    expired = False
    try:
        code, _ = _gh_api("GET", "/user", token=tok, timeout=6)
        expired = code == 401
    except Exception:
        expired = False
    _TOKEN_CHECK["token"] = tok
    _TOKEN_CHECK["expired"] = expired
    _TOKEN_CHECK["ts"] = now
    return expired


def list_repos(token, limit=100):
    """The signed-in account's repos, most-recently-pushed first, that the user
    owns or collaborates on. For the per-project repo picker."""
    repos, page = [], 1
    while len(repos) < limit and page <= 5:
        code, j = _gh_api("GET", f"/user/repos?per_page=50&page={page}"
                          "&sort=pushed&affiliation=owner,collaborator", token=token)
        if code != 200 or not isinstance(j, list) or not j:
            break
        for r in j:
            repos.append({"full_name": r.get("full_name"), "clone_url": r.get("clone_url"),
                          "private": bool(r.get("private")),
                          "pushed_at": r.get("pushed_at"),
                          "default_branch": r.get("default_branch") or "main"})
        if len(j) < 50:
            break
        page += 1
    return repos[:limit]


def search_repos(token, query, login=None, limit=30):
    """Search the signed-in account's repos by name via GitHub's search API, so
    repos beyond the recently-pushed page are findable. Scoped to the user's own
    repos (incl. forks). Returns [] on empty query or error."""
    q = (query or "").strip()
    if not q:
        return []
    terms = f"{q} in:name fork:true"
    if login:
        terms += f" user:{login}"
    qq = urllib.parse.quote(terms)
    code, j = _gh_api("GET", f"/search/repositories?q={qq}&per_page={int(limit)}"
                      "&sort=updated&order=desc", token=token)
    if code != 200 or not isinstance(j, dict):
        return []
    return [{"full_name": r.get("full_name"), "clone_url": r.get("clone_url"),
             "private": bool(r.get("private")), "pushed_at": r.get("pushed_at"),
             "default_branch": r.get("default_branch") or "main"}
            for r in (j.get("items") or [])][:limit]


def create_repo(token, name, private=True, description=""):
    """Create a new repo under the signed-in account (no auto-init, so the
    project's existing history pushes cleanly). Returns {full_name, clone_url,
    html_url, default_branch}."""
    body = {"name": name, "private": bool(private), "auto_init": False}
    if description:
        body["description"] = description[:300]
    code, j = _gh_api("POST", "/user/repos", token=token, body=body)
    if code not in (200, 201):
        raise RuntimeError(j.get("message") or f"create repo failed ({code})")
    return {"full_name": j.get("full_name"), "clone_url": j.get("clone_url"),
            "html_url": j.get("html_url"), "default_branch": j.get("default_branch") or "main"}


def parse_owner_repo(remote_url):
    """github.com/owner/repo(.git) → (owner, repo)."""
    u = (remote_url or "").strip()
    for pre in ("git@github.com:", "https://github.com/", "ssh://git@github.com/"):
        if u.startswith(pre):
            u = u[len(pre):]
            break
    u = u[:-4] if u.endswith(".git") else u
    parts = u.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def fork(token, owner, repo):
    """Fork owner/repo under the authenticated guest. Returns {full_name,
    clone_url, html_url}."""
    code, j = _gh_api("POST", f"/repos/{owner}/{repo}/forks", token=token, body={})
    if code not in (200, 201, 202):
        raise RuntimeError(j.get("message") or f"fork failed ({code})")
    return {"full_name": j.get("full_name"), "clone_url": j.get("clone_url"),
            "html_url": j.get("html_url")}


def open_pr(token, base_owner, base_repo, head, title, body="", base="main"):
    """Open a PR base_owner/base_repo <- head ('forkowner:branch'). Returns the
    PR url."""
    payload = {"title": title, "head": head, "base": base, "body": body}
    code, j = _gh_api("POST", f"/repos/{base_owner}/{base_repo}/pulls",
                      token=token, body=payload)
    if code not in (200, 201):
        raise RuntimeError(j.get("message") or f"PR failed ({code})")
    return {"url": j.get("html_url"), "number": j.get("number")}
