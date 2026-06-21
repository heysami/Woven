"""Core live-session state-machine test - no HTTP, drives live.py directly."""
import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shares, live

def main():
    tmp = tempfile.mkdtemp()
    proj_root = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(proj_root, "workflow"))
    os.makedirs(os.path.join(proj_root, "source", "main"))
    wf = {"nodes": [{"id": "n1", "kind": "prototype", "x": 10, "y": 20, "title": "Hero"}],
          "edges": [], "wb": []}
    with open(os.path.join(proj_root, "workflow", "workflow.json"), "w") as f:
        json.dump(wf, f)

    resolve = lambda pid: proj_root
    shares.init(tmp, tmp, resolve)

    applied = []
    def fake_apply(pid, op, author):
        applied.append((op, author)); return {"target": op.get("target")}
    def read_wf(root):
        with open(os.path.join(root, "workflow", "workflow.json")) as f: return json.load(f)
    def fake_dispatch(pid, nid, author): return {"runId": "r-test"}

    live.init(tmp, resolve, read_wf, fake_apply, fake_dispatch)

    rec, created = shares.share_create("proj", "main", label="Test")
    sid = rec["id"]
    assert created

    # not live yet → join refused
    try:
        live.join(rec, "Alex", ""); assert False, "should refuse before start"
    except PermissionError: pass

    live.session_start(sid)
    s = live._session(sid, "proj")

    # join two guests
    a = live.join(rec, "Alex", "")
    b = live.join(rec, "Bo", "")
    assert a["token"] != b["token"]
    assert a["role"] == "editor"
    assert len(live.session_summary(sid)["participants"]) == 2

    # auth
    gid, p = live._auth(s, a["token"])
    assert p["name"] == "Alex"
    try: live._auth(s, "deadbeef"*4 if False else "x"*32); assert False
    except PermissionError: pass

    # presence
    live.presence(s, a["token"], {"x": 5, "y": 6, "page": "canvas"}, None)
    _gid, pa = live._auth(s, a["token"])
    assert pa["cursor"]["x"] == 5

    # lease: Alex grabs n1, Bo is blocked
    r = live.lease_acquire(s, a["token"], "node:n1")
    assert r["ok"]
    r2 = live.lease_acquire(s, b["token"], "node:n1")
    assert not r2["ok"] and r2["held"]

    # Bo can't setField while Alex holds it
    try:
        live.apply_op(s, b["token"], {"op": "setField", "target": "node:n1", "field": "title", "value": "X"})
        assert False, "should be blocked"
    except PermissionError: pass

    # but Bo CAN move (cosmetic, lease-free)
    live.apply_op(s, b["token"], {"op": "move", "target": "node:n1", "x": 99, "y": 99})
    assert applied[-1][0]["op"] == "move"

    # Alex (holds lease) can setField
    live.apply_op(s, a["token"], {"op": "setField", "target": "node:n1", "field": "title", "value": "New"})
    assert applied[-1][0]["value"] == "New"

    # release → Bo can now grab
    live.lease_release(s, a["token"], "node:n1")
    r3 = live.lease_acquire(s, b["token"], "node:n1")
    assert r3["ok"]

    # run trigger sets agent lease
    live.session_stop(sid); live.session_start(sid)  # reset participants
    s = live._session(sid, "proj")
    c = live.join(rec, "Cy", "")
    live.trigger_run(s, c["token"], "n1")
    assert "node:n1" in s.leases and s.leases["node:n1"]["holder"] == "agent"
    live.release_agent_lease("proj", "n1")
    assert "node:n1" not in s.leases

    # viewer cannot edit
    live.set_role(sid, c["guestId"], "viewer")
    try:
        live.lease_acquire(s, c["token"], "node:n1"); assert False
    except PermissionError: pass

    # kick revokes token
    live.kick(sid, c["guestId"])
    try:
        live._auth(s, c["token"]); assert False
    except PermissionError: pass

    print("test_live_core: ALL PASS")

if __name__ == "__main__":
    main()
