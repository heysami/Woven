"""Regression test - review comments must survive a branch switch.

Background: share/comments.json is deliberately git-TRACKED (comments sync
across machines with the project), which means `git checkout <branch>`
swaps the file to THAT branch's committed snapshot. Every comment added
while on the previous branch silently vanished from the panel - users saw
"my comments got replaced by the old ones" after switching branches.

The fix: after every branch switch, serve._carry_comments_across_switch()
3-way merges the two branches' comment stores against their merge-base
(union by id, deletions win - shares.comments_merge_texts) and keeps the
union in the working tree, restoring carried comments' screenshot /
attachment files from the previous branch too. This test pins that
contract: stale-snapshot replacement, deletion-wins, sidecar restore,
round-trip stability (no spurious dirty tree), and divergent-adds union.

Run: `python3 editor/tests/test_comments_carry.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Make `import serve` resolve from editor/ when this file is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import git_ops as G   # noqa: E402
import serve           # noqa: E402  - import after sys.path mutation; module guards top-level on __main__


def main():
    if not G.git_available():
        print("git not available - SKIP")
        return
    root = tempfile.mkdtemp(prefix="comments-carry-")

    def run(*a):
        subprocess.run(a, cwd=root, check=True, capture_output=True)

    def write_comments(ids):
        os.makedirs(os.path.join(root, "share"), exist_ok=True)
        data = {"comments": [{"id": i, "text": "t-" + i, "prototype": "main",
                              "createdAt": "2026-07-01T00:00:0%dZ" % (len(i) % 10)}
                             for i in ids]}
        with open(os.path.join(root, "share", "comments.json"), "w") as f:
            json.dump(data, f, indent=2)

    def read_ids():
        with open(os.path.join(root, "share", "comments.json")) as f:
            return sorted(c["id"] for c in json.load(f)["comments"])

    run("git", "init", "-b", "main")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")

    # main: comments a, b
    write_comments(["a", "b"])
    run("git", "add", "-A")
    run("git", "commit", "-m", "base")

    # explore: add comment c (+ its shot & attachment), delete b
    run("git", "checkout", "-b", "explore")
    write_comments(["a", "c"])
    os.makedirs(os.path.join(root, "share", "comment-shots"), exist_ok=True)
    os.makedirs(os.path.join(root, "share", "comment-attach", "c"), exist_ok=True)
    with open(os.path.join(root, "share", "comment-shots", "c.jpg"), "wb") as f:
        f.write(b"JPG")
    with open(os.path.join(root, "share", "comment-attach", "c", "a1.png"), "wb") as f:
        f.write(b"PNG")
    run("git", "add", "-A")
    run("git", "commit", "-m", "explore edits")

    # switch explore -> main: the reported bug path. Plain checkout leaves the
    # stale snapshot; the carry must union it with explore's comments.
    prev = G.current_branch(root)
    res = G.switch_branch(root, "main")
    assert read_ids() == ["a", "b"], "sanity: plain checkout shows the stale snapshot"
    changed = serve._carry_comments_across_switch(root, prev, res["branch"])
    assert changed, "carry should report a change"
    assert read_ids() == ["a", "c"], "union with deletion-wins, got %r" % read_ids()
    assert os.path.isfile(os.path.join(root, "share", "comment-shots", "c.jpg")), "shot restored"
    assert os.path.isfile(os.path.join(root, "share", "comment-attach", "c", "a1.png")), "attachment restored"

    # commit the carried union on main (what auto-versioning would do)
    run("git", "add", "-A")
    run("git", "commit", "-m", "carried")

    # switch main -> explore: round trip must be stable, no spurious writes
    prev = G.current_branch(root)
    res = G.switch_branch(root, "explore")
    changed = serve._carry_comments_across_switch(root, prev, res["branch"])
    assert read_ids() == ["a", "c"], "round trip stable, got %r" % read_ids()
    assert not changed, "no-op switch must not report a change"

    # divergent adds on both branches union together
    write_comments(["a", "c", "d"])
    run("git", "add", "-A")
    run("git", "commit", "-m", "explore adds d")
    run("git", "checkout", "main")
    write_comments(["a", "c", "e"])
    run("git", "add", "-A")
    run("git", "commit", "-m", "main adds e")
    prev = G.current_branch(root)
    res = G.switch_branch(root, "explore")
    serve._carry_comments_across_switch(root, prev, res["branch"])
    assert read_ids() == ["a", "c", "d", "e"], "divergent adds union, got %r" % read_ids()

    shutil.rmtree(root)
    print("test_comments_carry: ALL PASS")


if __name__ == "__main__":
    main()
