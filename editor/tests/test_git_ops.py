"""Local git-core test — connect, commit w/ co-authors, status. Offline."""
import os, sys, tempfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import git_ops as G

def main():
    if not G.git_available():
        print("git not available — SKIP"); return
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "source", "main"))
    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>v1</h1>")

    assert not G.is_repo(root)
    st = G.connect(root, name="Host", email="host@woven.local")
    assert st["repo"] and st["dirty"], st

    msg = G.draft_message(root)
    assert "main" in msg, msg

    res = G.commit(root, "Initial prototype",
                   coauthors=["Alex <alex@users.noreply.github.com>", "Bo <bo@x.com>"],
                   name="Host", email="host@woven.local")
    assert res["sha"] and not res.get("empty"), res

    # verify co-author trailers landed
    log = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=root,
                         capture_output=True, text=True).stdout
    assert "Co-authored-by: Alex <alex@users.noreply.github.com>" in log, log
    assert "Co-authored-by: Bo <bo@x.com>" in log, log

    st = G.status(root)
    assert not st["dirty"] and st["hasCommits"], st
    assert st["lastCommit"], st

    # second commit only when dirty
    empty = G.commit(root, "noop")
    assert empty.get("empty"), empty

    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>v2</h1>")
    st = G.status(root); assert st["dirty"]
    res2 = G.commit(root, "Edit hero", name="Host", email="host@woven.local")
    assert res2["sha"] and not res2.get("empty")

    assert G.conflicted_files(root) == []

    # ── branches: fork / switch / merge / delete ─────────────────────────────
    binfo = G.branches(root)
    main_name = binfo["current"]
    assert any(b["current"] for b in binfo["branches"]), binfo

    # fork off HEAD (carries no edits — tree is clean here)
    fk = G.create_branch(root, "feature/hero")
    assert fk["branch"] == "feature/hero"
    assert G.current_branch(root) == "feature/hero"

    # diverge the fork
    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>fork</h1>")
    G.commit(root, "Fork edit", name="Host", email="host@woven.local")

    # bad branch names rejected
    for bad in ("", "has space", "a..b", "-leading"):
        try:
            G.create_branch(root, bad); assert False, "should reject " + repr(bad)
        except RuntimeError:
            pass

    # switch back, merge the fork in (no conflict — fast diverge on main side)
    G.switch_branch(root, main_name)
    assert G.current_branch(root) == main_name
    mg = G.merge_branch(root, "feature/hero")
    assert mg["ok"] and not mg["conflicts"], mg

    # can't delete the branch you're on; can delete a merged one
    try:
        G.delete_branch(root, main_name); assert False
    except RuntimeError:
        pass
    assert G.delete_branch(root, "feature/hero")["ok"]

    # ── merge conflict → resolve flow surfaces the file ──────────────────────
    G.create_branch(root, "left")
    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>LEFT</h1>")
    G.commit(root, "left change", name="Host", email="host@woven.local")
    G.switch_branch(root, main_name)
    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>RIGHT</h1>")
    G.commit(root, "right change", name="Host", email="host@woven.local")
    conf = G.merge_branch(root, "left")
    assert not conf["ok"] and conf["conflicts"], conf
    cpath = conf["conflicts"][0]

    # diff_conflict exposes ours/theirs/merged
    dc = G.diff_conflict(root, cpath)
    assert "RIGHT" in dc["ours"] and "LEFT" in dc["theirs"], dc
    assert "<<<<<<<" in dc["merged"], dc

    # abort the merge to clean up for the remaining assertions
    subprocess.run(["git", "merge", "--abort"], cwd=root)
    assert G.conflicted_files(root) == []

    # ── diff helpers ─────────────────────────────────────────────────────────
    open(os.path.join(root, "source", "main", "index.html"), "w").write("<h1>working</h1>")
    dw = G.diff_working(root)
    assert "working" in dw["diff"], dw
    G.commit(root, "working edit", name="Host", email="host@woven.local")
    head_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()
    assert "working" in G.diff_commit(root, head_sha)["diff"]

    # parse_owner_repo
    assert G.parse_owner_repo("https://github.com/acme/proto.git") == ("acme", "proto")
    assert G.parse_owner_repo("git@github.com:acme/proto") == ("acme", "proto")

    # oauth not configured in test env → clean signal
    assert G.oauth_configured() in (True, False)

    print("test_git_ops: ALL PASS")

if __name__ == "__main__":
    main()
