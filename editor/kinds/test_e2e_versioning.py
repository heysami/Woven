"""End-to-end integration test for asset versioning.

Spins up serve.py in a subprocess against a tempdir workspace, then exercises
the actual HTTP endpoints + file-system writes that the editor would trigger.
Verifies that:

  1. Writing a file under source/ creates a version (file-watcher path).
  2. Overwriting that file creates a NEW version (not replacing the first).
  3. A frontend /__workflow POST with stale state (no versions[]) does NOT
     stomp the version history.
  4. /__asset_generate-style writes also accumulate versions.
  5. workflow.json always agrees with the runs/ dirs on disk.

Run: python kinds/test_e2e_versioning.py
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(EDITOR_DIR)


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Daemon:
    def __init__(self, workspace_dir: str):
        self.workspace = workspace_dir
        self.port = _free_port()
        env = os.environ.copy()
        env["TH_WORKSPACE_DIR"] = workspace_dir
        env["PORT"] = str(self.port)
        # Capture stderr so we can diagnose crashes.
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(EDITOR_DIR, "serve.py")],
            cwd=REPO_ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self._wait_healthy()

    def _wait_healthy(self):
        deadline = time.time() + 12
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/__healthz", timeout=1) as r:
                    if r.status == 200: return
            except (urllib.error.URLError, ConnectionRefusedError):
                pass
            if self.proc.poll() is not None:
                err = self.proc.stderr.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"daemon crashed during startup:\n{err}")
            time.sleep(0.15)
        raise TimeoutError("daemon never came up")

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def get_json(self, path: str) -> dict:
        with urllib.request.urlopen(self.url(path), timeout=3) as r:
            return json.loads(r.read().decode("utf-8"))

    def post_json(self, path: str, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.url(path), data=data, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))

    def shutdown(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired: self.proc.kill()


def setup_project(workspace: str, pid: str) -> str:
    """Scaffold a minimal project with one image asset node already wired."""
    pdir = os.path.join(workspace, "projects", pid)
    os.makedirs(os.path.join(pdir, "source", "images"))
    os.makedirs(os.path.join(pdir, "editor"))
    os.makedirs(os.path.join(pdir, "workflow"))
    with open(os.path.join(pdir, "editor", "data.js"), "w") as f:
        f.write('window.EDITOR_DATA = { meta: {project: "e2e"}, frames: [], '
                'lanes: [], arrows: [], entities: [], primitives: [], links: [] };\n')
    wf = {
        "pan": {"x": 0, "y": 0}, "zoom": 1,
        "nodes": [
            {"id": "asset1", "kind": "asset", "assetKind": "image",
             "path": "source/images/foo.png",
             "title": "foo.png", "x": 100, "y": 100},
        ],
        "edges": [],
    }
    with open(os.path.join(pdir, "workflow", "workflow.json"), "w") as f:
        json.dump(wf, f, indent=2)
    return pdir


def fail(msg: str):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    workspace = tempfile.mkdtemp(prefix="vsn-e2e-")
    pid = "e2e"
    pdir = setup_project(workspace, pid)
    print(f"workspace={workspace}")
    print(f"project={pdir}")
    daemon = Daemon(workspace)
    print(f"daemon port {daemon.port} OK")

    try:
        # ── Step 1: write the initial image. ───────────────────────────
        img = os.path.join(pdir, "source/images/foo.png")
        with open(img, "wb") as f: f.write(b"\x89PNG\r\n\x1a\nIMAGE_V1_BYTES" * 50)
        print(f"[step1] wrote img v1 ({os.path.getsize(img)} bytes)")

        # Trigger /__workflow GET to run the migration (which synthesizes v0
        # from the on-disk file if no versions exist yet).
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        assert len(asset.get("versions") or []) == 1, \
            f"[step1] expected 1 version after migration, got {len(asset.get('versions') or [])}"
        v1_id = asset["versions"][0]["id"]
        print(f"[step1] migration synthesized v1={v1_id[:8]}")

        # ── Step 2: simulate the frontend's debounced /__workflow POST. ──
        # Stale state: no versions[], no activeVersionId. THIS IS THE BUG.
        # After the fix, the disk's versions[] must survive.
        stale = {
            "pan": {"x": 0, "y": 0}, "zoom": 1,
            "nodes": [
                {"id": "asset1", "kind": "asset", "assetKind": "image",
                 "path": "source/images/foo.png",
                 "title": "foo.png", "x": 100, "y": 100},
                # ↑ NOTICE: no versions, no activeVersionId - stomp attempt.
            ],
            "edges": [],
        }
        r = daemon.post_json(f"/__workflow?project={pid}", stale)
        print(f"[step2] /__workflow POST returned {r.get('ok')}")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        n_versions = len(asset.get("versions") or [])
        if n_versions != 1:
            fail(f"[step2] STOMP CHECK: expected 1 version after stale POST, got {n_versions}")
        if asset.get("activeVersionId") != v1_id:
            fail(f"[step2] STOMP CHECK: activeVersionId lost (was {v1_id[:8]}, now {asset.get('activeVersionId')})")
        print(f"[step2] PASS - stale POST did not stomp versions or activeVersionId")

        # ── Step 3: overwrite the image (simulating regenerate). ────────
        # Sleep first so mtime moves past the v1 createdAt + 1s dedup slop.
        time.sleep(2)
        with open(img, "wb") as f: f.write(b"\x89PNG\r\n\x1a\nIMAGE_V2_BYTES_REGEN" * 50)
        print(f"[step3] overwrote img v2 ({os.path.getsize(img)} bytes)")

        # Wait for the file watcher to pick up the change + snapshot.
        # The watcher runs on a 0.5s tick with a debounce; give it 4s.
        deadline = time.time() + 8
        n_versions = 0
        while time.time() < deadline:
            wf = daemon.get_json(f"/__workflow?project={pid}")
            asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
            n_versions = len(asset.get("versions") or [])
            if n_versions >= 2: break
            time.sleep(0.4)
        if n_versions < 2:
            fail(f"[step3] expected ≥2 versions after regenerate, got {n_versions}")
        v2_id = asset["versions"][-1]["id"]
        print(f"[step3] PASS - got {n_versions} versions, newest v2={v2_id[:8]}")

        # ── Step 4: another stale POST after v2 exists. ─────────────────
        stale["nodes"][0].pop("versions", None)
        stale["nodes"][0].pop("activeVersionId", None)
        daemon.post_json(f"/__workflow?project={pid}", stale)
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        n_versions = len(asset.get("versions") or [])
        if n_versions != 2:
            fail(f"[step4] STOMP CHECK: expected 2 versions after stale POST, got {n_versions}")
        print(f"[step4] PASS - second stale POST still preserved both versions")

        # ── Step 5: regenerate again. ───────────────────────────────────
        time.sleep(2)
        with open(img, "wb") as f: f.write(b"\x89PNG\r\n\x1a\nIMAGE_V3_BYTES_AGAIN" * 50)
        deadline = time.time() + 8
        n_versions = 0
        while time.time() < deadline:
            wf = daemon.get_json(f"/__workflow?project={pid}")
            asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
            n_versions = len(asset.get("versions") or [])
            if n_versions >= 3: break
            time.sleep(0.4)
        if n_versions < 3:
            fail(f"[step5] expected 3 versions after second regen, got {n_versions}")
        print(f"[step5] PASS - third regen produced version #3")

        # ── Step 6: confirm workflow.json + runs/ agree. ────────────────
        runs_dir = os.path.join(pdir, "workflow", "runs", "asset1")
        dirs_on_disk = sorted([d for d in os.listdir(runs_dir)
                                if os.path.isdir(os.path.join(runs_dir, d))])
        version_ids = sorted([v["id"] for v in asset["versions"]])
        if set(dirs_on_disk) != set(version_ids):
            fail(f"[step6] versions[] {version_ids} mismatch with runs/ dirs {dirs_on_disk}")
        print(f"[step6] PASS - versions[] and runs/ agree: {len(version_ids)} entries")

        # ── Step 7: revert + verify file restored. ──────────────────────
        v1 = asset["versions"][0]
        r = daemon.post_json(f"/__workflow/node/asset1/version/{v1['id']}/revert?project={pid}", {})
        with open(img, "rb") as f: now_bytes = f.read()
        if b"IMAGE_V1_BYTES" not in now_bytes:
            fail(f"[step7] revert didn't restore v1 content; file starts with {now_bytes[:40]!r}")
        print(f"[step7] PASS - revert to v1 restored original bytes")

        # ── Step 8: pin a version. The disk MUST reflect pinned=true
        # immediately (this is bug "pin doesn't refresh"). ─────────────
        v2 = asset["versions"][1]
        daemon.post_json(f"/__workflow/node/asset1/version/{v2['id']}/pin?project={pid}",
                          {"pinned": True})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        pinned_state = next(v for v in asset["versions"] if v["id"] == v2["id"]).get("pinned")
        if pinned_state is not True:
            fail(f"[step8] pin endpoint didn't persist pinned=true (got {pinned_state})")
        print(f"[step8] PASS - pin persisted on disk")

        # ── Step 8.5: path edit + versions preserved. The user-editable
        # fields path/paths/size should win over disk; daemon-owned
        # versions/activeVersionId should preserve disk values. ─────────
        edit = {
            "pan": {"x": 0, "y": 0}, "zoom": 1,
            "nodes": [
                {"id": "asset1", "kind": "asset", "assetKind": "image",
                 # User typed a new path.
                 "path": "source/images/renamed.png",
                 "title": "renamed.png", "x": 100, "y": 100},
            ],
            "edges": [],
        }
        daemon.post_json(f"/__workflow?project={pid}", edit)
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        if asset.get("path") != "source/images/renamed.png":
            fail(f"[step8.5] path edit was reverted: {asset.get('path')}")
        if len(asset.get("versions") or []) < 2:
            fail(f"[step8.5] versions array was stomped by path edit POST: "
                 f"{len(asset.get('versions') or [])} entries")
        # Restore original path so subsequent steps don't drift.
        edit["nodes"][0]["path"] = "source/images/foo.png"
        daemon.post_json(f"/__workflow?project={pid}", edit)
        print(f"[step8.5] PASS - path edit wins, versions preserved")

        # ── Step 9: branch a NON-ACTIVE historical version. The sibling's
        # canonical path MUST differ from the original's path, and its
        # bytes MUST match the picked version (not the original's active). ──
        # Pre-state: active version is v1 (restored in step 7).
        # Pick v3 to branch (an older non-active version).
        v3 = asset["versions"][-1]
        # Snap the v3 bytes from disk for later comparison.
        v3_snap_path = os.path.join(pdir, "workflow", "runs", "asset1", v3["id"],
                                     "images", "foo.png")
        with open(v3_snap_path, "rb") as f: v3_bytes = f.read()
        if b"IMAGE_V3_BYTES" not in v3_bytes:
            fail(f"[step9-prep] v3 snap didn't contain expected bytes; got {v3_bytes[:40]!r}")
        # Branch v3.
        r = daemon.post_json(f"/__workflow/node/asset1/version/branch?project={pid}",
                              {"sourceVersionId": v3["id"]})
        sibling_id = r.get("newNodeId")
        if not sibling_id:
            fail(f"[step9] branch endpoint didn't return newNodeId: {r}")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        sibling = next((n for n in wf["nodes"] if n["id"] == sibling_id), None)
        if not sibling:
            fail(f"[step9] sibling node {sibling_id!r} not in workflow.json")
        if sibling["path"] == asset["path"]:
            fail(f"[step9] sibling SHARES the original's canonical path "
                 f"({sibling['path']!r}) - branch should give it independent bytes")
        # Verify the sibling's canonical file on disk has v3 bytes (not v1's).
        sibling_file = os.path.join(pdir, sibling["path"].lstrip("/"))
        if not os.path.isfile(sibling_file):
            fail(f"[step9] sibling's canonical file missing on disk: {sibling['path']}")
        with open(sibling_file, "rb") as f: sib_bytes = f.read()
        if b"IMAGE_V3_BYTES" not in sib_bytes:
            fail(f"[step9] sibling's canonical bytes don't match the picked v3 "
                 f"(starts with {sib_bytes[:40]!r}) - branch is showing the wrong version")
        # And the original's canonical path STILL has v1's bytes (the active one).
        with open(img, "rb") as f: orig_bytes = f.read()
        if b"IMAGE_V1_BYTES" not in orig_bytes:
            fail(f"[step9] original's canonical bytes were disturbed by branching "
                 f"(starts with {orig_bytes[:40]!r})")
        print(f"[step9] PASS - branch produced an independent sibling with the "
              f"picked version's bytes (sibling path={sibling['path']!r}; original "
              f"path stays {asset['path']!r})")

        # ── Step 10: delete a non-active, non-pinned version. ───────────
        # Re-fetch fresh asset since previous steps mutated state.
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        active_vid = asset["activeVersionId"]
        target = next((v for v in asset["versions"]
                        if v["id"] != active_vid and not v.get("pinned")), None)
        if not target:
            fail(f"[step10] no deletable version available")
        # DELETE via raw urllib (post_json is JSON-only).
        req = urllib.request.Request(
            daemon.url(f"/__workflow/node/asset1/version/{target['id']}?project={pid}"),
            method="DELETE")
        with urllib.request.urlopen(req, timeout=3) as r:
            del_resp = json.loads(r.read().decode("utf-8"))
        if not del_resp.get("ok"):
            fail(f"[step10] DELETE didn't return ok: {del_resp}")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        if any(v["id"] == target["id"] for v in (asset.get("versions") or [])):
            fail(f"[step10] deleted version still in versions[]")
        # The runs/ dir should also be gone.
        ddir = os.path.join(pdir, "workflow", "runs", "asset1", target["id"])
        if os.path.exists(ddir):
            fail(f"[step10] runs/ dir still on disk after DELETE: {ddir}")
        print(f"[step10] PASS - DELETE removed both versions[] entry and runs/ dir")

        # ── Step 11: DELETE on active version should be rejected (409). ─
        try:
            req = urllib.request.Request(
                daemon.url(f"/__workflow/node/asset1/version/{active_vid}?project={pid}"),
                method="DELETE")
            with urllib.request.urlopen(req, timeout=3) as r:
                fail(f"[step11] DELETE on active version returned {r.status} (should be 409)")
        except urllib.error.HTTPError as e:
            if e.code != 409:
                fail(f"[step11] expected 409 on active version delete, got {e.code}")
        print(f"[step11] PASS - DELETE on active version correctly rejected with 409")

        # ── Step 12: size endpoint persists explicit + auto. ────────────
        daemon.post_json(f"/__workflow/node/asset1/size?project={pid}",
                          {"w": 420, "h": 320})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        if asset.get("w") != 420 or asset.get("h") != 320:
            fail(f"[step12] /size didn't persist explicit w/h: {asset.get('w')}, {asset.get('h')}")
        if (asset.get("size") or {}).get("scale") != "custom":
            fail(f"[step12] /size with w/h didn't flip scale to custom: {asset.get('size')}")
        # Now auto-size.
        daemon.post_json(f"/__workflow/node/asset1/size?project={pid}",
                          {"auto": True})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        if asset.get("w") is not None or asset.get("h") is not None:
            fail(f"[step12] /size auto didn't clear w/h: {asset.get('w')}, {asset.get('h')}")
        if (asset.get("size") or {}).get("scale") != "fit-canvas":
            fail(f"[step12] /size auto didn't reset scale: {asset.get('size')}")
        print(f"[step12] PASS - /size endpoint handles explicit + auto correctly")

        # ── Step 13: save composition + switch + delete. ────────────────
        # Add a sub-asset upstream so the composition has substance.
        wf = daemon.get_json(f"/__workflow?project={pid}")
        wf["nodes"].append({
            "id": "sub_a", "kind": "asset", "assetKind": "image",
            "path": "source/images/sub.png", "title": "sub.png", "x": 500, "y": 100,
        })
        wf["edges"].append({"from": "sub_a.out", "to": "asset1.in"})
        daemon.post_json(f"/__workflow?project={pid}", wf)
        # Write the sub file so the daemon can synthesize a version.
        sub_img = os.path.join(pdir, "source/images/sub.png")
        os.makedirs(os.path.dirname(sub_img), exist_ok=True)
        with open(sub_img, "wb") as f: f.write(b"SUB_BYTES_V1")
        # Re-GET to trigger migration on the sub asset.
        wf = daemon.get_json(f"/__workflow?project={pid}")
        sub = next(n for n in wf["nodes"] if n["id"] == "sub_a")
        if len(sub.get("versions") or []) < 1:
            fail(f"[step13] sub_a didn't get a v0 from migration")
        sub_vid = sub["activeVersionId"]
        # Save a composition on asset1 capturing sub_a's current version.
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        active_vid_a1 = asset["activeVersionId"]
        r = daemon.post_json(
            f"/__workflow/node/asset1/version/{active_vid_a1}/composition?project={pid}",
            {"subVersions": {"sub_a": sub_vid}, "label": "with-sub-v1"})
        new_cid = r.get("compositionId")
        if not new_cid:
            fail(f"[step13] saveComposition didn't return compositionId: {r}")
        # Switch back to the auto-locked comp (the first one).
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        ver = next(v for v in asset["versions"] if v["id"] == active_vid_a1)
        if len(ver["compositions"]) < 2:
            fail(f"[step13] expected ≥2 compositions, got {len(ver['compositions'])}")
        first_cid = ver["compositions"][0]["id"]
        daemon.post_json(
            f"/__workflow/node/asset1/version/{active_vid_a1}/composition/{first_cid}/switch?project={pid}",
            {})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        ver = next(v for v in next(n for n in wf["nodes"] if n["id"] == "asset1")["versions"]
                    if v["id"] == active_vid_a1)
        if ver["activeCompositionId"] != first_cid:
            fail(f"[step13] composition switch didn't persist: {ver['activeCompositionId']}")
        print(f"[step13] PASS - saveComposition + switch persist correctly")

        # ── Step 14: delete the saved composition. ──────────────────────
        req = urllib.request.Request(
            daemon.url(
                f"/__workflow/node/asset1/version/{active_vid_a1}/composition/{new_cid}?project={pid}"),
            method="DELETE")
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.loads(r.read().decode("utf-8"))
        if not d.get("ok"):
            fail(f"[step14] composition delete didn't return ok: {d}")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        ver = next(v for v in next(n for n in wf["nodes"] if n["id"] == "asset1")["versions"]
                    if v["id"] == active_vid_a1)
        if any(c["id"] == new_cid for c in (ver.get("compositions") or [])):
            fail(f"[step14] deleted composition still in compositions[]")
        print(f"[step14] PASS - composition DELETE removes from compositions[]")

        # ── Step 15: prototype kind versioning. Write any file under
        # source/ → the prototype node accumulates a snapshot. ──────────
        wf = daemon.get_json(f"/__workflow?project={pid}")
        wf["nodes"].append({
            "id": "proto1", "kind": "prototype",
            "title": "Live prototype", "x": 800, "y": 400,
        })
        daemon.post_json(f"/__workflow?project={pid}", wf)
        # Migration on next GET should synthesize v0 for the prototype.
        wf = daemon.get_json(f"/__workflow?project={pid}")
        proto = next((n for n in wf["nodes"] if n["id"] == "proto1"), None)
        if not proto:
            fail(f"[step15] prototype node missing after POST")
        proto_v_count_initial = len(proto.get("versions") or [])
        if proto_v_count_initial < 1:
            fail(f"[step15] prototype didn't get v0 from migration; versions={proto_v_count_initial}")
        # Write a brand new file under source/. Should trigger snapshot.
        # Sleep past the 1s mtime dedup slop window so the file is genuinely
        # newer than v0's createdAt.
        time.sleep(2)
        new_file = os.path.join(pdir, "source", "index.html")
        with open(new_file, "w") as f: f.write("<html><body>v1 of prototype</body></html>")
        # Wait for watcher.
        deadline = time.time() + 8
        while time.time() < deadline:
            wf = daemon.get_json(f"/__workflow?project={pid}")
            proto = next(n for n in wf["nodes"] if n["id"] == "proto1")
            if len(proto.get("versions") or []) > proto_v_count_initial:
                break
            time.sleep(0.4)
        if len(proto.get("versions") or []) <= proto_v_count_initial:
            fail(f"[step15] prototype watcher didn't snapshot after source/ write; "
                 f"got {len(proto.get('versions') or [])} versions, expected > {proto_v_count_initial}")
        print(f"[step15] PASS - prototype version accumulates on source/ writes")

        # ── Step 16: design-system kind versioning. ─────────────────────
        ds_dir = os.path.join(pdir, "design-systems", "ds1")
        os.makedirs(ds_dir, exist_ok=True)
        with open(os.path.join(ds_dir, "styles.css"), "w") as f:
            f.write(":root { --color-bg: white; }")
        with open(os.path.join(ds_dir, "gallery.html"), "w") as f:
            f.write("<html><body>gallery v1</body></html>")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        wf["nodes"].append({
            "id": "ds_ds1", "kind": "design-system", "dsId": "ds1",
            "title": "Design system ds1", "x": 1200, "y": 400,
        })
        daemon.post_json(f"/__workflow?project={pid}", wf)
        wf = daemon.get_json(f"/__workflow?project={pid}")
        ds = next((n for n in wf["nodes"] if n["id"] == "ds_ds1"), None)
        if not ds:
            fail(f"[step16] design-system node missing")
        ds_v_initial = len(ds.get("versions") or [])
        if ds_v_initial < 1:
            fail(f"[step16] design-system didn't get v0 from migration; versions={ds_v_initial}")
        # Modify the DS file.
        time.sleep(1.5)
        with open(os.path.join(ds_dir, "styles.css"), "w") as f:
            f.write(":root { --color-bg: black; }")
        deadline = time.time() + 8
        while time.time() < deadline:
            wf = daemon.get_json(f"/__workflow?project={pid}")
            ds = next(n for n in wf["nodes"] if n["id"] == "ds_ds1")
            if len(ds.get("versions") or []) > ds_v_initial:
                break
            time.sleep(0.4)
        if len(ds.get("versions") or []) <= ds_v_initial:
            fail(f"[step16] design-system watcher didn't snapshot after DS file edit; "
                 f"got {len(ds.get('versions') or [])} versions")
        print(f"[step16] PASS - design-system version accumulates on DS file writes")

        # ── Step 17: sub-asset lineage auto-populates from edges. ───────
        # Set up two asset nodes wired together: sub_b → consumer_c.
        os.makedirs(os.path.join(pdir, "source", "subs"), exist_ok=True)
        with open(os.path.join(pdir, "source/subs/icon.png"), "wb") as f:
            f.write(b"SUB_ICON_V1" * 30)
        os.makedirs(os.path.join(pdir, "source/pages"), exist_ok=True)
        with open(os.path.join(pdir, "source/pages/page.html"), "w") as f:
            f.write("<html><body><img src='../subs/icon.png'></body></html>")
        wf = daemon.get_json(f"/__workflow?project={pid}")
        wf["nodes"].extend([
            {"id":"sub_b","kind":"asset","assetKind":"image",
             "path":"source/subs/icon.png","title":"icon.png","x":700,"y":500},
            {"id":"consumer_c","kind":"asset","assetKind":"html",
             "path":"source/pages/page.html","title":"page.html","x":1000,"y":500},
        ])
        wf["edges"].append({"from":"sub_b.out","to":"consumer_c.in"})
        daemon.post_json(f"/__workflow?project={pid}", wf)
        wf = daemon.get_json(f"/__workflow?project={pid}")
        sub_b = next(n for n in wf["nodes"] if n["id"]=="sub_b")
        consumer = next(n for n in wf["nodes"] if n["id"]=="consumer_c")
        if not sub_b.get("versions"):
            fail(f"[step17] sub_b never got migrated v0")
        if not consumer.get("versions"):
            fail(f"[step17] consumer_c never got migrated v0")
        # Trigger a fresh consumer snapshot by bumping the file's mtime.
        time.sleep(2)
        with open(os.path.join(pdir, "source/pages/page.html"), "w") as f:
            f.write("<html><body><img src='../subs/icon.png'><!-- v2 --></body></html>")
        deadline = time.time() + 8
        while time.time() < deadline:
            wf = daemon.get_json(f"/__workflow?project={pid}")
            consumer = next(n for n in wf["nodes"] if n["id"]=="consumer_c")
            if len(consumer.get("versions") or []) >= 2: break
            time.sleep(0.4)
        if len(consumer.get("versions") or []) < 2:
            fail(f"[step17] consumer_c didn't snapshot after edit; v={len(consumer.get('versions') or [])}")
        latest = consumer["versions"][-1]
        active_comp_id = latest.get("activeCompositionId")
        active_comp = next((c for c in latest.get("compositions") or [] if c.get("id")==active_comp_id), None)
        if not active_comp:
            fail(f"[step17] no active composition on consumer_c's latest version")
        pins = active_comp.get("consumedSubVersions") or {}
        if "sub_b" not in pins:
            fail(f"[step17] sub-asset lineage missing 'sub_b' in consumedSubVersions: {pins}")
        if pins["sub_b"] != sub_b["activeVersionId"]:
            fail(f"[step17] sub_b pin mismatch: composition pinned {pins['sub_b']}, sub_b active is {sub_b['activeVersionId']}")
        print(f"[step17] PASS - sub-asset lineage auto-populated from edges (sub_b pinned at {pins['sub_b'][:8]})")

        # ── Step 18: label endpoint (version + composition). ────────────
        wf = daemon.get_json(f"/__workflow?project={pid}")
        asset = next(n for n in wf["nodes"] if n["id"] == "asset1")
        v_target = asset["versions"][0]
        daemon.post_json(
            f"/__workflow/node/asset1/version/{v_target['id']}/label?project={pid}",
            {"label": "golden master"})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        v_after = next(v for v in next(n for n in wf["nodes"] if n["id"]=="asset1")["versions"]
                        if v["id"] == v_target["id"])
        if v_after.get("label") != "golden master":
            fail(f"[step18] version label didn't persist: {v_after.get('label')!r}")
        # Clear it
        daemon.post_json(
            f"/__workflow/node/asset1/version/{v_target['id']}/label?project={pid}",
            {"label": None})
        wf = daemon.get_json(f"/__workflow?project={pid}")
        v_after = next(v for v in next(n for n in wf["nodes"] if n["id"]=="asset1")["versions"]
                        if v["id"] == v_target["id"])
        if v_after.get("label") is not None:
            fail(f"[step18] label clear didn't work: {v_after.get('label')!r}")
        print(f"[step18] PASS - version label set + clear works")

        # ── Step 19: thumb endpoint accepts dataUrl. ────────────────────
        import base64
        # 1x1 transparent PNG
        png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        data_url = "data:image/png;base64," + png_b64
        v = next(v for v in next(n for n in wf["nodes"] if n["id"]=="asset1")["versions"])
        daemon.post_json(
            f"/__workflow/node/asset1/version/{v['id']}/thumb?project={pid}",
            {"dataUrl": data_url})
        thumb_path = os.path.join(pdir, "workflow", "runs", "asset1", v["id"], "thumb.png")
        if not os.path.isfile(thumb_path):
            fail(f"[step19] thumb file not written: {thumb_path}")
        if os.path.getsize(thumb_path) < 50:
            fail(f"[step19] thumb file too small ({os.path.getsize(thumb_path)} bytes)")
        print(f"[step19] PASS - version thumb POST writes bytes correctly")

        # ── Step 20: DS revert restores the styles.css content. ─────────
        wf = daemon.get_json(f"/__workflow?project={pid}")
        ds = next(n for n in wf["nodes"] if n["id"] == "ds_ds1")
        if len(ds.get("versions") or []) < 2:
            fail(f"[step20-prep] need ≥2 DS versions, have {len(ds.get('versions') or [])}")
        first_ds_v = ds["versions"][0]   # the one with --color-bg: white
        r = daemon.post_json(
            f"/__workflow/node/ds_ds1/version/{first_ds_v['id']}/revert?project={pid}",
            {})
        with open(os.path.join(pdir, "design-systems/ds1/styles.css")) as f:
            css_now = f.read()
        if "white" not in css_now:
            fail(f"[step20] DS revert didn't restore white styles.css; got {css_now[:80]!r}")
        print(f"[step20] PASS - DS revert restored styles.css content")

        print("\nALL 20 STEPS PASSED - full versioning surface verified end-to-end")
        return 0
    finally:
        daemon.shutdown()
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
