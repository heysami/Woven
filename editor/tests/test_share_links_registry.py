"""Contract test - the contributor share-link registry (share/links.json).

Background: shares.json is per-install, so a collaborator could never see the
links a teammate published. share/links.json fixes that: each install writes
its OWN stable links (woven tunnel / hosted snapshot - never quick URLs, which
rotate every restart) into the project, and the file rides git like
comments.json. Merge is fully mechanical (entries keyed <install>:<prototype>,
only ever written by their owner install): shares.links_merge_texts unions by
key, newest updatedAt wins, a deletion after the merge base beats a stale copy.

Pins: merge semantics, two-install publish round trip (union, idempotence,
toggle-off removal, other installs' entries untouched), no-hostname no-op, and
the branch-switch / discard carry in serve.py (same treatment comments get).

Run: `python3 editor/tests/test_share_links_registry.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Make `import serve` / `import shares` resolve from editor/ when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import git_ops as G    # noqa: E402
import serve            # noqa: E402
import shares           # noqa: E402


def entry(install, proto, ts, **kw):
    e = {"key": install + ":" + proto, "install": install, "owner": "u-" + install,
         "prototype": proto, "label": proto, "url": "https://" + install + ".x/s/t/",
         "hosted": False, "live": True, "updatedAt": ts}
    e.update(kw)
    return e


def T(links):
    return json.dumps({"links": links})


def test_merge():
    # both sides carry the key -> newest updatedAt wins
    m = shares.links_merge_texts(
        T([entry("A", "main", "2026-01-01T00:00:00")]),
        T([entry("A", "main", "2026-01-02T00:00:00", label="new")]),
        T([entry("A", "main", "2026-01-01T00:00:00")]))
    assert len(m["links"]) == 1 and m["links"][0]["label"] == "new", "newest wins"

    # new on each side (absent from base) -> union
    m = shares.links_merge_texts(
        "", T([entry("A", "main", "2026-01-01T00:00:00")]),
        T([entry("B", "main", "2026-01-01T00:00:00")]))
    assert len(m["links"]) == 2, "add/add unions"

    # in base, deleted on one side, unchanged on the other -> deletion wins
    m = shares.links_merge_texts(
        T([entry("A", "main", "2026-01-01T00:00:00")]),
        T([entry("A", "main", "2026-01-01T00:00:00")]),
        T([]))
    assert m["links"] == [], "deletion wins over the unchanged copy"

    # in base, deleted on one side, but EDITED after base on the other -> edit survives
    m = shares.links_merge_texts(
        T([entry("A", "main", "2026-01-01T00:00:00")]),
        T([entry("A", "main", "2026-01-03T00:00:00", label="edited")]),
        T([]))
    assert len(m["links"]) == 1 and m["links"][0]["label"] == "edited", \
        "post-base edit beats a stale delete"

    # garbage input parses to empty, never raises
    m = shares.links_merge_texts("not json", "[]", T([entry("A", "m", "1")]))
    assert len(m["links"]) == 1, "garbage-safe"


def test_publish():
    tmp = tempfile.mkdtemp(prefix="links-registry-")
    proj_root = os.path.join(tmp, "proj")
    os.makedirs(proj_root)
    saved = (shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT)

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
        shares._RESOLVE_PROJECT_ROOT = lambda pid: proj_root

    try:
        rec_woven = {"id": "shr-aaaaaaaaaa", "token": "a" * 32, "project": "proj",
                     "prototype": "main", "label": "proj / main", "wovenOn": True,
                     "quickOn": False, "active": True, "mode": "woven", "liveOnly": False}
        rec_hosted = {"id": "shr-cccccccccc", "token": "c" * 32, "project": "proj",
                      "prototype": "alt", "label": "proj / alt", "wovenOn": False,
                      "quickOn": True, "active": True, "mode": "quick",
                      "liveOnly": False, "hostedOn": True}
        rec_quick = {"id": "shr-dddddddddd", "token": "d" * 32, "project": "proj",
                     "prototype": "q", "label": "quick only", "wovenOn": False,
                     "quickOn": True, "active": True, "mode": "quick", "liveOnly": False}
        rec_live = {"id": "shr-eeeeeeeeee", "token": "e" * 32, "project": "proj",
                    "prototype": "__multiplayer__", "label": "mp", "wovenOn": True,
                    "quickOn": False, "active": True, "mode": "woven", "liveOnly": True}

        setup_install("A", "aaa.getwoven.design", [rec_woven, rec_hosted, rec_quick, rec_live])
        assert shares.publish_project_links("proj") is True, "first publish writes"
        reg = shares.links_load(proj_root)["links"]
        iid_a = shares.woven_install_id()
        # woven + hosted publish; quick-only and the multiplayer share never do
        assert len(reg) == 2, "stable links only, got %r" % [e["key"] for e in reg]
        assert any(e["prototype"] == "alt" and e["hosted"] and not e["live"] for e in reg)
        assert all(e["url"].startswith("https://aaa.getwoven.design/s/") for e in reg)

        # republish with nothing changed: no write, timestamps preserved
        ts = sorted(e["updatedAt"] for e in reg)
        assert shares.publish_project_links("proj") is False, "idempotent"
        assert sorted(e["updatedAt"] for e in shares.links_load(proj_root)["links"]) == ts

        # install B publishes into the SAME project - A's entries survive
        rec_b = {"id": "shr-bbbbbbbbbb", "token": "b" * 32, "project": "proj",
                 "prototype": "main", "label": "b's main", "wovenOn": True,
                 "quickOn": False, "active": True, "mode": "woven", "liveOnly": False}
        setup_install("B", "bbb.getwoven.design", [rec_b])
        shares.publish_project_links("proj")
        reg = shares.links_load(proj_root)["links"]
        iid_b = shares.woven_install_id()
        assert iid_a != iid_b, "distinct installs"
        assert len(reg) == 3, "union across installs"
        assert sum(1 for e in reg if e["install"] == iid_a) == 2, "A untouched"

        # B flips its link off - B's entry goes, A's stay
        setup_install("B", "bbb.getwoven.design", [dict(rec_b, wovenOn=False, active=False)])
        shares.publish_project_links("proj")
        reg = shares.links_load(proj_root)["links"]
        assert sum(1 for e in reg if e["install"] == iid_b) == 0, "toggle-off removes"
        assert sum(1 for e in reg if e["install"] == iid_a) == 2, "A still untouched"

        # links_list hands the client the split key
        out = shares.links_list("proj")
        assert out["installId"] == iid_b and len(out["links"]) == 2

        # a tunnel/broker failure inside set_modes must NOT skip the registry
        # write (the boot restore calls set_modes; a cloudflared hiccup there
        # silently left teammates without the link). try/finally pins it.
        setup_install("A", "aaa.getwoven.design", [rec_woven, rec_hosted, rec_quick, rec_live])
        os.remove(os.path.join(proj_root, "share", "links.json"))
        saved_start = shares._woven_tunnel_start
        shares._woven_tunnel_start = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            try:
                shares.set_modes("shr-aaaaaaaaaa", woven=True)
                raise AssertionError("tunnel failure must surface to the caller")
            except RuntimeError as e:
                assert "boom" in str(e)
        finally:
            shares._woven_tunnel_start = saved_start
        assert os.path.isfile(os.path.join(proj_root, "share", "links.json")), \
            "registry published despite the tunnel failure"

        # without a provisioned hostname publish must not mint the file
        proj2 = os.path.join(tmp, "proj2")
        os.makedirs(proj2)
        shares._RESOLVE_PROJECT_ROOT = lambda pid: proj2
        shares.WOVEN_DIR = os.path.join(tmp, "woven-none")
        os.makedirs(shares.WOVEN_DIR)
        shares.publish_project_links("proj2")
        assert not os.path.exists(os.path.join(proj2, "share", "links.json")), \
            "no hostname -> no file"
    finally:
        shares.WORKSPACE_DIR, shares.WOVEN_DIR, shares._RESOLVE_PROJECT_ROOT = saved
        shutil.rmtree(tmp)


def test_carry():
    if not G.git_available():
        print("git not available - SKIP carry test")
        return
    root = tempfile.mkdtemp(prefix="links-carry-")

    def run(*a):
        subprocess.run(a, cwd=root, check=True, capture_output=True)

    def write_links(installs):
        os.makedirs(os.path.join(root, "share"), exist_ok=True)
        with open(os.path.join(root, "share", "links.json"), "w") as f:
            json.dump({"links": [entry(i, "main", "2026-07-0%dT00:00:00" % (n + 1))
                                 for n, i in enumerate(installs)]}, f, indent=2)

    def read_installs():
        with open(os.path.join(root, "share", "links.json")) as f:
            return sorted(e["install"] for e in json.load(f)["links"])

    run("git", "init", "-b", "main")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")

    write_links(["A"])
    run("git", "add", "-A")
    run("git", "commit", "-m", "base")

    # explore: teammate B's link lands (e.g. via a pull) while on this branch
    run("git", "checkout", "-b", "explore")
    write_links(["A", "B"])
    run("git", "add", "-A")
    run("git", "commit", "-m", "B appears")

    # switch back to main: plain checkout shows the stale snapshot; the carry
    # must union B's link across, exactly like comments.
    prev = G.current_branch(root)
    res = G.switch_branch(root, "main")
    assert read_installs() == ["A"], "sanity: stale snapshot after checkout"
    changed = serve._carry_links_across_switch(root, prev, res["branch"])
    assert changed, "carry should report a change"
    assert read_installs() == ["A", "B"], "union carried, got %r" % read_installs()

    # discard must not destroy an uncommitted registry update
    run("git", "add", "-A")
    run("git", "commit", "-m", "carried")
    write_links(["A", "B", "C"])                       # uncommitted entry C
    links_snap = open(os.path.join(root, "share", "links.json")).read()
    prev_head = G.head_sha(root)
    G.discard_local(root)
    assert read_installs() == ["A", "B"], "sanity: reset wiped C"
    assert serve._carry_links_after_reset(root, prev_head, links_snap), "carry reports change"
    assert read_installs() == ["A", "B", "C"], "entry survives discard"

    # ── share-metadata dirt must not block a switch (the reported bug:
    # "comments seem to be considered as git now, i can't switch without
    # committing"). The guard splits share-meta dirt from real dirt; the
    # snapshot + revert_paths + after-reset carry sequence the handler runs
    # must leave the union on the target branch.
    meta, other = serve._split_share_meta_dirt(root)
    assert [r for _xy, r in meta] == ["share/links.json"], "links dirt is share-meta"
    assert other == [], "no real dirt"
    snap_text = serve._share_links_text(root)
    prev_head = G.head_sha(root)
    G.revert_paths(root, meta)
    assert read_installs() == ["A", "B"], "revert cleared the uncommitted entry"
    st = G.status(root)
    assert not st["dirty"], "tree clean for the switch"
    res = G.switch_branch(root, "explore")
    assert res.get("ok")
    serve._carry_links_after_reset(root, prev_head, snap_text)
    assert "C" in read_installs(), "uncommitted entry carried onto the target branch"

    # a REAL dirty file still counts as blocking dirt
    with open(os.path.join(root, "code.txt"), "w") as fh:
        fh.write("real work")
    meta, other = serve._split_share_meta_dirt(root)
    assert other == ["code.txt"], "real work is not share-meta, got %r" % other

    shutil.rmtree(root)


def main():
    test_merge()
    test_publish()
    test_carry()
    print("test_share_links_registry: ALL PASS")


if __name__ == "__main__":
    main()
