"""Smoke tests for asset-node versioning.

Exercises every public function in versioning.py against a synthetic
project tree under a tmpdir. Designed to run standalone:

  python -m editor.kinds.test_versioning
  or
  cd editor/kinds && python test_versioning.py

No pytest dependency - every check is a plain assert with a descriptive
message. Exits 0 on success, non-zero on first failure.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

# Allow running from anywhere.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from kinds import versioning as V  # noqa: E402


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _touch(project_root: str, rel: str, body: str = "x") -> str:
    abs_path = os.path.join(project_root, rel)
    _write(abs_path, body)
    return abs_path


def test_ulid_uniqueness():
    seen = set()
    for _ in range(2000):
        u = V.make_ulid()
        assert isinstance(u, str) and len(u) == 26, f"bad ulid: {u!r}"
        assert u not in seen, f"ulid collision: {u}"
        seen.add(u)


def test_asset_files_helpers():
    n1 = {"id": "a", "kind": "asset", "path": "source/foo.html"}
    n2 = {"id": "b", "kind": "asset", "paths": ["source/x.html", "source/y.html"]}
    n3 = {"id": "c", "kind": "asset", "path": "/source/a.html",
          "paths": ["source/b.html", "source/a.html"]}  # dedupe
    assert V.asset_files(n1) == ["source/foo.html"]
    assert V.asset_files(n2) == ["source/x.html", "source/y.html"]
    assert V.asset_files(n3) == ["source/a.html", "source/b.html"]


def test_hash_text():
    assert V.hash_text("") == V.hash_text(None)
    assert V.hash_text("hello") != V.hash_text("world")
    assert V.hash_text("hello").startswith("sha256:")


def test_snapshot_and_revert_roundtrip():
    proj = tempfile.mkdtemp(prefix="vsn-")
    try:
        # Set up an asset with a single canonical file under source/.
        _touch(proj, "source/page/index.html", "<h1>v1</h1>")
        node = {"id": "asset_page", "kind": "asset", "assetKind": "html",
                "path": "source/page/index.html"}

        ver = V.snapshot_asset(proj, node)
        assert ver is not None, "first snapshot returned None"
        assert node.get("activeVersionId") == ver["id"]
        assert len(node["versions"]) == 1
        assert len(ver["compositions"]) == 1
        assert ver["activeCompositionId"] == ver["compositions"][0]["id"]
        # Snapshot files written under workflow/runs/<nodeId>/<vid>/
        snap_dir = V.runs_dir(proj, "asset_page", ver["id"])
        assert os.path.isfile(os.path.join(snap_dir, "page/index.html"))
        # View dir materialised.
        vdir = V.view_dir(proj, "asset_page", ver["id"], ver["activeCompositionId"])
        assert os.path.isdir(vdir)
        assert os.path.isfile(os.path.join(vdir, "page/index.html"))

        # Second snapshot after modifying the live file.
        _write(os.path.join(proj, "source/page/index.html"), "<h1>v2</h1>")
        ver2 = V.snapshot_asset(proj, node)
        assert ver2 is not None and ver2["id"] != ver["id"]
        assert node["activeVersionId"] == ver2["id"]
        assert len(node["versions"]) == 2

        # Revert: simulate setting active back to v1 + refreshing source/.
        node["activeVersionId"] = ver["id"]
        refreshed = V.refresh_source_from_view(proj, node)
        assert refreshed == 1
        with open(os.path.join(proj, "source/page/index.html"), encoding="utf-8") as f:
            assert f.read() == "<h1>v1</h1>", "revert did not restore v1 content"
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_eviction_keeps_active_and_pinned():
    proj = tempfile.mkdtemp(prefix="vsn-")
    try:
        _touch(proj, "source/x.html", "v")
        node = {"id": "a1", "kind": "asset", "assetKind": "html",
                "path": "source/x.html"}
        # Snapshot 25 times - small cap so we can observe eviction.
        ids = []
        for i in range(25):
            _write(os.path.join(proj, "source/x.html"), f"v{i}")
            v = V.snapshot_asset(proj, node, max_unpinned_versions=5)
            assert v is not None
            ids.append(v["id"])
        # Cap is 5 unpinned; active never evicted.
        assert len(node["versions"]) <= 6, f"too many versions kept: {len(node['versions'])}"
        # Active should still be the latest.
        assert node["activeVersionId"] == ids[-1]
        # Pin one of the surviving older versions and verify it's protected
        # across the next eviction wave.
        survivors = [v["id"] for v in node["versions"]]
        # Pin the oldest survivor (not the active one).
        pin_target = next(vid for vid in survivors if vid != node["activeVersionId"])
        pinned_v = next(v for v in node["versions"] if v["id"] == pin_target)
        pinned_v["pinned"] = True
        for i in range(10):
            _write(os.path.join(proj, "source/x.html"), f"w{i}")
            V.snapshot_asset(proj, node, max_unpinned_versions=5)
        assert any(v["id"] == pin_target for v in node["versions"]), \
            "pinned version was evicted"
        # The pinned version's snapshot dir must still exist.
        assert os.path.isdir(V.runs_dir(proj, "a1", pin_target)), \
            "pinned version's runs dir was deleted"
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_composition_eviction():
    proj = tempfile.mkdtemp(prefix="vsn-")
    try:
        _touch(proj, "source/x.html", "v")
        node = {"id": "a1", "kind": "asset", "assetKind": "html",
                "path": "source/x.html"}
        v = V.snapshot_asset(proj, node)
        assert v is not None
        # Add many compositions manually then evict.
        version = node["versions"][0]
        for i in range(10):
            cid = V.make_ulid()
            version["compositions"].append({
                "id": cid, "createdAt": "x", "consumedSubVersions": {},
                "subAssetMounts": {}, "thumbPath": "", "label": None,
                "pinned": False, "degraded": False,
            })
        # Cap to 3 unpinned; active is protected.
        evicted = V.evict_compositions(proj, node, version, max_unpinned=3)
        assert len(evicted) > 0
        # Active still present.
        assert any(c["id"] == version["activeCompositionId"]
                   for c in version["compositions"])
        # Survivor count = max_unpinned + 1 (active).
        assert len(version["compositions"]) == 4
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_migration_synthesizes_v0():
    proj = tempfile.mkdtemp(prefix="vsn-")
    try:
        _touch(proj, "source/page/index.html", "<h1>legacy</h1>")
        node = {"id": "legacy_asset", "kind": "asset",
                "assetKind": "html", "path": "source/page/index.html"}
        # No versions yet - migration synthesizes v0.
        assert V.migrate_legacy_asset(proj, node) is True
        assert node.get("activeVersionId")
        assert len(node["versions"]) == 1
        # Idempotent: second call is a no-op.
        assert V.migrate_legacy_asset(proj, node) is False
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_hardlink_or_copy():
    tmp = tempfile.mkdtemp(prefix="vsn-link-")
    try:
        src = os.path.join(tmp, "src.txt")
        dst = os.path.join(tmp, "out", "dst.txt")
        _write(src, "hello")
        mode = V.hardlink_or_copy(src, dst)
        assert mode in ("link", "copy")
        # Content matches.
        with open(dst, encoding="utf-8") as f:
            assert f.read() == "hello"
        # Idempotent: re-running doesn't error.
        V.hardlink_or_copy(src, dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_snapshot_changed_assets_dedup_and_mtime():
    """File-watcher path: every disk write snapshots the matching asset,
    deduped by node and skipped when file's mtime <= last version's createdAt."""
    proj = tempfile.mkdtemp(prefix="vsn-wtcr-")
    try:
        # Two image assets in the same workflow.
        _touch(proj, "source/img/a.png", "A1")
        _touch(proj, "source/img/b.png", "B1")
        workflow = {
            "nodes": [
                {"id": "asset_a", "kind": "asset", "assetKind": "image",
                 "path": "source/img/a.png"},
                {"id": "asset_b", "kind": "asset", "assetKind": "image",
                 "path": "source/img/b.png"},
            ],
            "edges": [],
        }
        # First batch - both assets are newly written.
        snaps = V.snapshot_changed_assets(proj, workflow, ["source/img/a.png", "source/img/b.png"])
        assert len(snaps) == 2, f"expected 2 snapshots, got {len(snaps)}"
        ids = {s["nodeId"] for s in snaps}
        assert ids == {"asset_a", "asset_b"}

        # Second batch with same paths but no file change - should dedup
        # because the file mtime hasn't advanced past the version's createdAt.
        snaps2 = V.snapshot_changed_assets(proj, workflow, ["source/img/a.png"])
        assert len(snaps2) == 0, f"expected 0 (file unchanged), got {len(snaps2)}"

        # Third batch - change one file's mtime forward then re-snap.
        import time as _t
        future = _t.time() + 5
        os.utime(os.path.join(proj, "source/img/a.png"), (future, future))
        snaps3 = V.snapshot_changed_assets(proj, workflow, ["source/img/a.png"])
        assert len(snaps3) == 1, f"expected 1 after mtime bump, got {len(snaps3)}"
        assert snaps3[0]["nodeId"] == "asset_a"

        # Same-batch dedup: include the same path twice - one snap only.
        future += 5
        os.utime(os.path.join(proj, "source/img/b.png"), (future, future))
        snaps4 = V.snapshot_changed_assets(proj, workflow,
                                            ["source/img/b.png", "source/img/b.png"])
        assert len(snaps4) == 1
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def test_snapshot_downstream_assets():
    """End-to-end: a producer node with a downstream asset triggers snapshot."""
    proj = tempfile.mkdtemp(prefix="vsn-e2e-")
    try:
        _touch(proj, "source/out.html", "<h1>fresh</h1>")
        workflow = {
            "nodes": [
                {"id": "prod", "kind": "skill", "text": "do it",
                 "output": "the output"},
                {"id": "sink", "kind": "asset", "assetKind": "html",
                 "path": "source/out.html"},
            ],
            "edges": [
                {"from": "prod.out", "to": "sink.in"},
            ],
        }
        created = V.snapshot_downstream_assets(proj, workflow, "prod")
        assert len(created) == 1
        assert created[0]["nodeId"] == "sink"
        sink = next(n for n in workflow["nodes"] if n["id"] == "sink")
        assert sink.get("activeVersionId")
        # Non-asset upstream output got hashed into consumedVersions.
        ver = sink["versions"][0]
        assert "prod" in ver["consumedVersions"]
        assert ver["consumedVersions"]["prod"]["outputHash"].startswith("sha256:")
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def main():
    tests = [
        test_ulid_uniqueness,
        test_asset_files_helpers,
        test_hash_text,
        test_hardlink_or_copy,
        test_snapshot_and_revert_roundtrip,
        test_eviction_keeps_active_and_pinned,
        test_composition_eviction,
        test_migration_synthesizes_v0,
        test_snapshot_downstream_assets,
        test_snapshot_changed_assets_dedup_and_mtime,
    ]
    passed = 0
    for t in tests:
        name = t.__name__
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {name}: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
        passed += 1
        print(f"OK   {name}")
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
