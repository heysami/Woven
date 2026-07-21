"""Contract test - review comments over the woven-share-comments sync branch.

Background: peer comment sync pulls each contributor's gate over HTTP, which
requires every daemon to reach every other install's public URL. Found live:
one contributor's network never completed those pulls, so their share's
public discussion sat forked at their own comments while the link registry
(which rides git) stayed perfectly fresh. serve._sync_comments_meta rides the
same git-plumbing channel: fetch the branch's union doc, union it into the
local store (comments_peer_union - adds + field-merge + tombstones-win),
push the local union back when it adds anything.

Pins: two clones with different checked-out branches converge on the union
without any commit/pull of their own branches; deletion tombstones
propagate; a no-op resync reports no change; the sync branch stays out of
the local branch picker.

Run: `python3 editor/tests/test_comments_meta_sync.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import git_ops as G    # noqa: E402
import serve            # noqa: E402
import shares           # noqa: E402


def main():
    if not G.git_available():
        print("git not available - SKIP")
        return
    tmp = tempfile.mkdtemp(prefix="comments-meta-")
    saved = (shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT)

    def run(cwd, *a):
        subprocess.run(a, cwd=cwd, check=True, capture_output=True)

    try:
        origin = os.path.join(tmp, "origin.git")
        os.makedirs(origin)
        run(origin, "git", "init", "--bare", "-b", "main")
        seed = os.path.join(tmp, "seed")
        run(tmp, "git", "clone", "-q", origin, seed)
        run(seed, "git", "config", "user.email", "t@t")
        run(seed, "git", "config", "user.name", "t")
        with open(os.path.join(seed, "README"), "w") as f:
            f.write("hi")
        run(seed, "git", "add", "-A")
        run(seed, "git", "commit", "-m", "base")
        run(seed, "git", "push", "-q", "origin", "main")
        clone_a = os.path.join(tmp, "clone-a")
        clone_b = os.path.join(tmp, "clone-b")
        run(tmp, "git", "clone", "-q", origin, clone_a)
        run(tmp, "git", "clone", "-q", origin, clone_b)
        for c in (clone_a, clone_b):
            run(c, "git", "config", "user.email", "t@t")
            run(c, "git", "config", "user.name", "t")
        # different local branches - the environment where user-branch riding fails
        run(clone_a, "git", "checkout", "-q", "-b", "a-branch")
        run(clone_b, "git", "checkout", "-q", "-b", "b-branch")

        # A comments; B comments; neither commits or pulls anything.
        ca = shares.comment_add(clone_a, "prototype", page="index.html",
                                anchor={"selector": "h1"}, pin={"x": 0.5, "y": 0.5},
                                text="from A", author={"name": "A"})
        cb = shares.comment_add(clone_b, "prototype", page="index.html",
                                anchor={"selector": "p"}, pin={"x": 0.1, "y": 0.1},
                                text="from B", author={"name": "B"})

        assert serve._sync_comments_meta(clone_a) is False, \
            "A's first sync pushes but gains nothing new locally"
        assert serve._sync_comments_meta(clone_b) is True, \
            "B's sync unions A's comment in"
        ids_b = {c["id"] for c in shares.comments_list(clone_b, "prototype")}
        assert ids_b == {ca["id"], cb["id"]}, "B holds the union, got %r" % ids_b

        assert serve._sync_comments_meta(clone_a) is True, "A's resync picks up B"
        ids_a = {c["id"] for c in shares.comments_list(clone_a, "prototype")}
        assert ids_a == {ca["id"], cb["id"]}, "A holds the union, got %r" % ids_a

        # branch picker stays clean; sync branch exists on origin
        out = subprocess.run(["git", "ls-remote", "--heads", origin],
                             capture_output=True, text=True, check=True).stdout
        assert "woven-share-comments" in out, "sync branch pushed to origin"
        names = [b["name"] for b in G.branches(clone_a)["branches"]]
        assert "woven-share-comments" not in names, "sync branch hidden from picker"

        # deletion on A tombstones everywhere
        shares.comment_delete(clone_a, ca["id"])
        serve._sync_comments_meta(clone_a)
        assert serve._sync_comments_meta(clone_b) is True, "B applies the tombstone"
        ids_b = {c["id"] for c in shares.comments_list(clone_b, "prototype")}
        assert ids_b == {cb["id"]}, "deletion propagated, got %r" % ids_b

        # quiet when converged
        assert serve._sync_comments_meta(clone_a) is False
        assert serve._sync_comments_meta(clone_b) is False

        # Rename-proofing: a record filed under a PRE-RENAME slug (a peer
        # store that never applied main->prototype) must still (a) show
        # through the current slug's filter and (b) normalize on union.
        # Found live: 25 comments rode the sync doc as "main" and every
        # gate's exact-match filter hid them.
        for c in (clone_a, clone_b):
            os.makedirs(os.path.join(c, "source", "prototype"), exist_ok=True)
            os.makedirs(os.path.join(c, "share"), exist_ok=True)
            with open(os.path.join(c, "share", "renames.json"), "w") as f:
                json.dump({"renames": [{"old": "main", "new": "prototype",
                                        "at": "2026-01-01T00:00:00",
                                        "install": "c" * 32}]}, f)
        shares._RENAMES_PAIRS_CACHE.clear()
        cm = shares.comment_add(clone_a, "main", page="index.html",
                                anchor={"selector": "b"}, pin={"x": 0.2, "y": 0.2},
                                text="filed pre-rename", author={"name": "A"})
        ids_a = {c["id"] for c in shares.comments_list(clone_a, "prototype")}
        assert cm["id"] in ids_a, "old-slug record visible through current filter"
        serve._sync_comments_meta(clone_a)
        assert serve._sync_comments_meta(clone_b) is True, "B unions the record"
        got = [c for c in shares.comments_list(clone_b, "prototype")
               if c["id"] == cm["id"]]
        assert got and got[0].get("prototype") == "prototype", \
            "union normalized the old slug, got %r" % (got and got[0].get("prototype"))
    finally:
        shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT = saved
        shutil.rmtree(tmp)
    print("test_comments_meta_sync: ALL PASS")


if __name__ == "__main__":
    main()
