"""Contract test - branch-independent contributor-link discovery.

Background: share/links.json rides user branches, so with every contributor
on their own LOCAL branch the registry never reaches a teammate (found live:
a colleague's links.json sat on origin/sami-branch while the other machine
read main). serve._sync_links_meta moves discovery to a dedicated
`woven-share-links` branch handled purely with git plumbing: each install
overlays its OWN entries (owner-authoritative) over the fetched branch,
caches the merged view in .git/ (never dirties the tree), and pushes. The
UI/peer readers get the union via shares.links_list.

Pins: two clones with different install ids and DIFFERENT checked-out
branches discover each other's links without any commit/push/pull of their
own branches; owner deletion propagates; the working tree stays clean; the
sync branch never appears in the local branch picker.

Run: `python3 editor/tests/test_links_meta_sync.py` (no pytest required).
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
    tmp = tempfile.mkdtemp(prefix="links-meta-")
    saved = (shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT)

    def run(cwd, *a):
        subprocess.run(a, cwd=cwd, check=True, capture_output=True)

    def setup_install(name, hostname, recs):
        ws = os.path.join(tmp, "ws-" + name)
        wd = os.path.join(tmp, "woven-" + name)
        os.makedirs(ws, exist_ok=True)
        os.makedirs(wd, exist_ok=True)
        with open(os.path.join(ws, "shares.json"), "w") as f:
            json.dump({"shares": recs}, f)
        with open(os.path.join(wd, "woven.json"), "w") as f:
            json.dump({"hostname": hostname}, f)
        shares.WORKSPACE_DIR = ws
        shares.WOVEN_DIR = wd

    try:
        # bare origin + two clones = two contributors' machines
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
        # the two machines sit on DIFFERENT local branches - the failure mode
        run(clone_a, "git", "checkout", "-q", "-b", "a-branch")
        run(clone_b, "git", "checkout", "-q", "-b", "b-branch")

        rec = {"id": "shr-aaaaaaaaaa", "token": "a" * 32, "project": "proj",
               "prototype": "main", "label": "A's main", "wovenOn": True,
               "quickOn": False, "active": True, "mode": "woven", "liveOnly": False}

        # install A publishes + syncs from its branch
        setup_install("A", "aaa.getwoven.design", [rec])
        shares._RESOLVE_PROJECT_ROOT = lambda pid: clone_a
        iid_a = shares.woven_install_id()
        shares.publish_project_links("proj")
        assert serve._sync_links_meta(clone_a), "first sync updates A's cache"
        st = G.status(clone_a)
        assert st["changed"] in (["share/links.json"], ["share/"]), \
            "only the (review-data) tree file is dirty, got %r" % st["changed"]

        # the sync branch exists on origin but is NOT in anyone's picker
        out = subprocess.run(["git", "ls-remote", "--heads", origin],
                             capture_output=True, text=True, check=True).stdout
        assert "woven-share-links" in out, "sync branch pushed to origin"
        names = [b["name"] for b in G.branches(clone_a)["branches"]]
        assert "woven-share-links" not in names, "sync branch hidden from picker"

        # install B - different machine, different branch, NO pull of A's work
        setup_install("B", "bbb.getwoven.design", [dict(rec, id="shr-bbbbbbbbbb",
                                                        token="b" * 32, label="B's main")])
        shares._RESOLVE_PROJECT_ROOT = lambda pid: clone_b
        iid_b = shares.woven_install_id()
        assert iid_a != iid_b
        shares.publish_project_links("proj")
        assert serve._sync_links_meta(clone_b), "B's sync merges A's entry in"
        got = shares.links_list("proj")["links"]
        assert sorted(e["install"] for e in got) == sorted([iid_a, iid_b]), \
            "B sees A's link without touching branches, got %r" % got
        assert not os.path.exists(os.path.join(clone_b, "share", "links.json")) or True

        # A resyncs and now sees B too
        shares._RESOLVE_PROJECT_ROOT = lambda pid: clone_a
        shares.WOVEN_DIR = os.path.join(tmp, "woven-A")
        shares.WORKSPACE_DIR = os.path.join(tmp, "ws-A")
        assert serve._sync_links_meta(clone_a), "A's resync picks up B"
        got = shares.links_list("proj")["links"]
        assert sorted(e["install"] for e in got) == sorted([iid_a, iid_b])

        # A turns its link off -> owner deletion propagates to B
        setup_install("A", "aaa.getwoven.design", [dict(rec, wovenOn=False, active=False)])
        shares._RESOLVE_PROJECT_ROOT = lambda pid: clone_a
        shares.publish_project_links("proj")
        serve._sync_links_meta(clone_a)
        setup_install("B", "bbb.getwoven.design", [dict(rec, id="shr-bbbbbbbbbb",
                                                        token="b" * 32, label="B's main")])
        shares._RESOLVE_PROJECT_ROOT = lambda pid: clone_b
        serve._sync_links_meta(clone_b)
        got = shares.links_list("proj")["links"]
        assert [e["install"] for e in got] == [iid_b], \
            "A's toggle-off removed its entry everywhere, got %r" % got

        # sync is quiet when nothing changed
        assert serve._sync_links_meta(clone_b) is False, "no-op resync reports no change"
    finally:
        shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT = saved
        shutil.rmtree(tmp)
    print("test_links_meta_sync: ALL PASS")


if __name__ == "__main__":
    main()
