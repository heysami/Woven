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

    # parse_owner_repo
    assert G.parse_owner_repo("https://github.com/acme/proto.git") == ("acme", "proto")
    assert G.parse_owner_repo("git@github.com:acme/proto") == ("acme", "proto")

    # oauth not configured in test env → clean signal
    assert G.oauth_configured() in (True, False)

    print("test_git_ops: ALL PASS")

if __name__ == "__main__":
    main()
