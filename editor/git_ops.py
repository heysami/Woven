"""Git / GitHub backbone for Live Session (docs/features/live-session.md §7).

Two layers:

  LOCAL (git)   — connect a project to git, deliberate commit (host-pressed,
                  never automatic), publish (push). Commits credit in-session
                  guests as Co-authored-by trailers (the Claude Code
                  convention). Fully offline; this is the merge/history engine.

  REMOTE (GitHub) — fork, pull-request, and the GitHub OAuth token exchange the
                  collab client needs so guests authenticate in-place. Reads the
                  OAuth app credentials from a config file the user fills (see
                  docs/features/live-session-setup.md); without it the remote
                  layer reports a clear "not configured" error and the local
                  layer still works.

Design choices that match the doc:
  • Commit is DELIBERATE — there is no auto-commit anywhere here; serve.py only
    calls commit() when the host presses the button.
  • Canvas layout (workflow.json node positions) is cosmetic; we still commit it
    (it's one file) but never special-case merges for it — git's line merge on
    the indent=2 JSON is good enough and the doc accepts last-writer-wins there.
  • Agent-assisted conflict resolution: conflicted_files() surfaces the paths;
    serve.py hands them to the host agent. We never hand-merge LLM-regenerated
    HTML/CSS/JS ourselves.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import json
import os
import subprocess
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
        return 127, "", "git not found — install git"
    except subprocess.TimeoutExpired:
        return 124, "", "git timed out"


def git_available():
    code, _o, _e = _git(".", "--version", timeout=5)
    return code == 0


# ═════════════════════════════════════════════════════════════════════════
# LOCAL — connect / status / commit / publish
# ═════════════════════════════════════════════════════════════════════════

def is_repo(root):
    """True ONLY when `root` is the TOPLEVEL of its own git repo — not when it
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
        return "Woven live session — no changes"
    protos = sorted({p.split("/")[1] for p in changed if p.startswith("source/") and "/" in p[7:]})
    n = len(changed)
    if protos:
        head = "Update " + ", ".join(protos[:3]) + (f" +{len(protos)-3} more" if len(protos) > 3 else "")
    else:
        head = f"Woven live session — {n} file{'s' if n != 1 else ''} changed"
    return head


def commit(root, message, coauthors=None, name=None, email=None):
    """Stage everything and commit. `coauthors` is a list of 'Name <email>'
    strings appended as Co-authored-by trailers. Deliberate — only called when
    the host presses Commit. Returns {sha, message}."""
    if not is_repo(root):
        raise RuntimeError("project is not a git repo — connect it first")
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
        raise RuntimeError("no 'origin' remote — connect the project to GitHub first")
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
        raise RuntimeError("no 'origin' remote — connect the project to GitHub first")
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
        # `url` as origin because we pass it via the source arg, not config —
        # but to be safe we reset origin to the token-free URL after cloning).
        fetch_url = url.replace("https://", f"https://x-access-token:{token}@", 1)
    parent = os.path.dirname(os.path.abspath(dest))
    os.makedirs(parent, exist_ok=True)
    code, out, err = _git(parent, "clone", fetch_url, os.path.abspath(dest), timeout=300)
    if code != 0:
        raise RuntimeError(f"git clone failed: {(err or out).strip()[:400]}")
    # Make sure origin carries the clean (token-free) URL even if git recorded
    # the authenticated one — we never persist credentials in config.
    if fetch_url != url:
        _git(dest, "remote", "set-url", "origin", url)
    return {"ok": True, "dest": os.path.abspath(dest)}


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


# ═════════════════════════════════════════════════════════════════════════
# REMOTE — GitHub OAuth + fork + PR
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


# ── Device Flow — the OAuth variant for changing tunnel hostnames ────────────
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
# never sent to the browser — only the login + avatar are surfaced.
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
    """The stored access token, or None — what push/pull/list reach for."""
    return (load_token() or {}).get("access_token") or None


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
