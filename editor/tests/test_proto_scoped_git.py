"""Contract test - prototype-scoped commit and merge.

Background: Woven's commit staged everything (`git add -A`) and merge took
the whole branch, so collaborators working on different prototypes in one
project always shipped each other's in-flight work. Scoped variants fix
that: commit(paths=[source/<slug>, share metadata]) records ONE prototype's
changes and leaves the rest dirty; merge_prototype(root, branch, slug) is a
path-scoped take-theirs - the branch's source/<slug>/ tree (including its
deletions) replaces ours in a single commit, nothing else touched.

Run: `python3 editor/tests/test_proto_scoped_git.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import git_ops as G   # noqa: E402


def main():
    if not G.git_available():
        print("git not available - SKIP")
        return
    root = tempfile.mkdtemp(prefix="proto-scoped-")

    def run(*a):
        subprocess.run(a, cwd=root, check=True, capture_output=True)

    def write(rel, text):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)

    def read(rel):
        with open(os.path.join(root, rel)) as f:
            return f.read()

    def head_files():
        out = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"],
                             cwd=root, check=True, capture_output=True, text=True)
        return sorted(out.stdout.split())

    run("git", "init", "-b", "main")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    write("source/alpha/index.html", "alpha v1")
    write("source/beta/index.html", "beta v1")
    run("git", "add", "-A")
    run("git", "commit", "-m", "base")

    # ── scoped commit: only alpha's edits land; beta stays dirty ────────────
    write("source/alpha/index.html", "alpha v2")
    write("source/beta/index.html", "beta v2")
    write("share/comments.json", '{"comments": [], "deleted": []}')
    res = G.commit(root, "alpha only", paths=["source/alpha", "share/comments.json",
                                              "share/links.json"])
    assert not res.get("empty"), "scoped commit records the alpha change"
    st = G.status(root)
    assert st["dirty"] and st["changed"] == ["source/beta/index.html"], \
        "beta's edit stays uncommitted, got %r" % st["changed"]
    assert "share/comments.json" in head_files(), "review data rides the scoped commit"

    # a scope with nothing to commit reports empty (absent optional paths dropped)
    res = G.commit(root, "noop", paths=["source/alpha", "share/links.json"])
    assert res.get("empty"), "clean scope -> empty commit"

    # settle beta so branches diverge cleanly
    G.commit(root, "beta too", paths=["source/beta"])

    # ── scoped merge: take ONE prototype from a branch, deletions included ──
    run("git", "checkout", "-b", "feature")
    write("source/alpha/index.html", "alpha FEATURE")
    write("source/alpha/extra.js", "new file")
    write("source/beta/index.html", "beta FEATURE")
    run("git", "add", "-A")
    run("git", "commit", "-m", "feature edits both")
    os.remove(os.path.join(root, "source", "alpha", "extra.js"))
    write("source/alpha/only-on-feature.css", "css")
    run("git", "add", "-A")
    run("git", "commit", "-m", "feature reshapes alpha")

    run("git", "checkout", "main")
    res = G.merge_prototype(root, "feature", "alpha")
    assert res["ok"] and res["prototype"] == "alpha"
    assert read("source/alpha/index.html") == "alpha FEATURE", "alpha taken from feature"
    assert os.path.isfile(os.path.join(root, "source/alpha/only-on-feature.css")), \
        "file added on feature arrives"
    assert not os.path.exists(os.path.join(root, "source/alpha/extra.js")), \
        "file feature deleted does not linger"
    assert read("source/beta/index.html") == "beta v2", "beta untouched by scoped merge"
    st = G.status(root)
    assert not st["dirty"], "scoped merge commits itself, tree clean - got %r" % st["changed"]

    # merging again is a no-op, not an error
    res = G.merge_prototype(root, "feature", "alpha")
    assert "up to date" in (res.get("detail") or ""), "idempotent re-merge"

    # guards: unknown prototype on the branch / bad slug
    try:
        G.merge_prototype(root, "feature", "nope")
        raise AssertionError("missing prototype must raise")
    except RuntimeError as e:
        assert "no source/nope/" in str(e)
    try:
        G.merge_prototype(root, "feature", "../evil")
        raise AssertionError("bad slug must raise")
    except RuntimeError as e:
        assert "invalid prototype" in str(e)

    shutil.rmtree(root)
    print("test_proto_scoped_git: ALL PASS")


if __name__ == "__main__":
    main()
