"""Standalone Live Session demo - stands up the real gate + a demo project +
an active session, prints the local /live URL, and serves forever so a browser
can exercise the collab client. For manual + automated browser verification.

  python3 tests/live_demo_server.py
  → open the printed http://127.0.0.1:<port>/s/<token>/live/ in two tabs
"""
import os, sys, json, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "editor"))
import shares, live

def build():
    tmp = tempfile.mkdtemp(prefix="woven-live-demo-")
    proj = os.path.join(tmp, "demoproj")
    os.makedirs(os.path.join(proj, "workflow"))
    os.makedirs(os.path.join(proj, "source", "main"))
    nodes = [
        {"id": "n1", "kind": "prototype", "x": 80,  "y": 60,  "title": "Landing page", "runStatus": "done"},
        {"id": "n2", "kind": "prompt",    "x": 360, "y": 60,  "title": "Hero copy"},
        {"id": "n3", "kind": "design-system", "x": 80, "y": 240, "title": "Design system"},
        {"id": "n4", "kind": "agent",     "x": 360, "y": 240, "title": "Build agent"},
    ]
    json.dump({"nodes": nodes, "edges": [{"from": "n2", "to": "n1"}], "wb": []},
              open(os.path.join(proj, "workflow", "workflow.json"), "w"))
    open(os.path.join(proj, "source", "main", "index.html"), "w").write(
        "<!doctype html><html><body style='font-family:sans-serif;padding:40px'>"
        "<h1>Demo prototype</h1><p>Live-session preview.</p></body></html>")
    resolve = lambda pid: proj
    shares.init(tmp, REPO, resolve)
    live.init(REPO, resolve,
              lambda root: json.load(open(os.path.join(root, "workflow", "workflow.json"))),
              _apply_factory(proj), lambda pid, nid, author: {"runId": "r-demo"})
    shares.register_live(live.GATE)
    port = shares.start_gate_server(8950)
    rec, _ = shares.share_create("demoproj", "main", label="Demo prototype")
    live.session_start(rec["id"])
    return port, rec["token"]

def _apply_factory(proj):
    def apply(pid, op, author):
        wfp = os.path.join(proj, "workflow", "workflow.json")
        wf = json.load(open(wfp))
        kind, _, tid = (op.get("target") or "").partition(":")
        arr = wf.get("nodes") if kind == "node" else wf.get("wb")
        t = next((n for n in arr if n.get("id") == tid), None)
        if t:
            if op.get("op") == "move":
                for f in ("x", "y"):
                    if f in op: t[f] = float(op[f])
            elif op.get("op") == "setField":
                t[op["field"]] = op["value"]
            json.dump(wf, open(wfp, "w"))
        return {"ok": 1}
    return apply

if __name__ == "__main__":
    port, token = build()
    url = f"http://127.0.0.1:{port}/s/{token}/live/"
    try:
        with open("/tmp/woven-live-demo-url.txt", "w") as f:
            f.write(url)
    except Exception:
        pass
    print("LIVE_DEMO_URL=" + url, flush=True)
    print("Open in two browser tabs to see cursors + co-editing.", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
