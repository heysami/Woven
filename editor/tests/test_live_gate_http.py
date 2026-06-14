"""HTTP smoke test of the real share GATE serving /s/<token>/live* routes.
Stands up shares.start_gate_server (the actual gate) + live, no full daemon."""
import os, sys, json, tempfile, time, threading, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))   # .../Woven
sys.path.insert(0, os.path.join(REPO, "editor"))

import shares, live

def req(url, method="GET", body=None, headers=None, timeout=4):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if data is not None: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)

def main():
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(proj, "workflow"))
    os.makedirs(os.path.join(proj, "source", "main"))
    json.dump({"nodes": [{"id": "n1", "kind": "prototype", "x": 1, "y": 2, "title": "Hero"}], "edges": [], "wb": []},
              open(os.path.join(proj, "workflow", "workflow.json"), "w"))
    open(os.path.join(proj, "source", "main", "index.html"), "w").write("<h1>proto</h1>")

    resolve = lambda pid: proj
    shares.init(tmp, REPO, resolve)
    live.init(REPO, resolve,
              lambda root: json.load(open(os.path.join(root, "workflow", "workflow.json"))),
              lambda pid, op, author: {"ok": 1},
              lambda pid, nid, author: {"runId": "r1"})
    shares.register_live(live.GATE)
    port = shares.start_gate_server(8900)
    base = f"http://127.0.0.1:{port}"

    rec, _ = shares.share_create("proj", "main", label="Demo")
    tok = rec["token"]; sid = rec["id"]
    L = f"{base}/s/{tok}/live"

    # before start → 409
    st, b, _ = req(f"{L}/api/meta")
    assert st == 409, f"meta before start {st} {b}"

    live.session_start(sid)

    # client shell: /live → 301 → /live/
    st, _b, h = req(f"{L}", timeout=4)
    # urllib follows redirects; final should be 200 html
    assert st == 200, f"client shell {st}"

    # meta
    st, b, _ = req(f"{L}/api/meta"); assert st == 200, f"meta {st} {b}"
    meta = json.loads(b); assert meta["prototype"] == "main"

    # workflow
    st, b, _ = req(f"{L}/api/workflow"); assert st == 200
    assert json.loads(b)["nodes"][0]["id"] == "n1"

    # join
    st, b, _ = req(f"{L}/api/join", "POST", {"name": "Alex"}); assert st == 200, f"join {st} {b}"
    join = json.loads(b); token = join["token"]
    H = {"X-Live-Token": token}

    # presence
    st, b, _ = req(f"{L}/api/presence", "POST", {"cursor": {"x": 3, "y": 4}}, H); assert st == 200, f"pres {st} {b}"

    # lease
    st, b, _ = req(f"{L}/api/lease/acquire", "POST", {"target": "node:n1"}, H)
    assert st == 200 and json.loads(b)["ok"], f"lease {st} {b}"

    # op (move) routes through apply callback
    st, b, _ = req(f"{L}/api/op", "POST", {"op": {"op": "move", "target": "node:n1", "x": 9, "y": 9}}, H)
    assert st == 200, f"op {st} {b}"

    # prototype file served at share-root /p/
    st, b, _ = req(f"{base}/s/{tok}/p/source/main/index.html")
    assert st == 200 and "proto" in b, f"proto {st} {b}"

    # SSE: open events, expect a 'roster' frame, then trigger a presence broadcast
    sse_url = f"{L}/events?lt={token}"
    got = {"frames": []}
    def reader():
        rq = urllib.request.Request(sse_url)
        with urllib.request.urlopen(rq, timeout=5) as resp:
            buf = ""
            t0 = time.time()
            while time.time() - t0 < 3:
                line = resp.readline().decode()
                if not line: break
                if line.startswith("event:"): got["frames"].append(line.strip())
                if len(got["frames"]) >= 3: break
    th = threading.Thread(target=reader, daemon=True); th.start()
    time.sleep(0.5)
    # second guest joins → triggers roster broadcast to Alex's SSE
    req(f"{L}/api/join", "POST", {"name": "Bo"})
    time.sleep(0.5)
    live.broadcast(sid, "presence", {"guestId": "x", "name": "Bo", "color": "#fff", "cursor": {"x": 1, "y": 1}})
    th.join(timeout=4)
    assert any("roster" in f for f in got["frames"]), f"no roster in SSE: {got['frames']}"

    # viewer-role write rejected
    live.set_role(sid, join["guestId"], "viewer")
    st, b, _ = req(f"{L}/api/lease/acquire", "POST", {"target": "node:n1"}, H)
    assert st == 403, f"viewer should 403, got {st} {b}"

    print("test_live_gate_http: ALL PASS  (gate port", port, ")")

if __name__ == "__main__":
    main()
