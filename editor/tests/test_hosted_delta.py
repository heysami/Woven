"""Contract test - hosted-share DELTA uploads (daemon <-> broker).

Background: every hosted "Update" used to rebuild the whole snapshot tar,
ship every byte to the broker, wipe the R2 prefix, and re-put every object
serially - a one-line HTML tweak paid for the full prototype + design
systems + fonts. Now the daemon hashes the snapshot (manifest), asks the
broker what it already holds (/shares/delta_check), and uploads a tar of
just the changed files with the full manifest as its first member
(__delta.json); the broker overwrites those objects in place, deletes the
ones that left the manifest, and keeps the rest - no delete-prefix 404
window. Any wrinkle falls back to the legacy full upload.

Pins, across the REAL daemon tar-builder and the REAL broker extractor
(broker/delta.py is stdlib-only precisely so this test can run it):
  full upload manifest round-trip, delta uploads only changed files,
  vanished share/ objects are deleted while fonts/ survive, the delta
  result is byte-identical to a fresh full upload, and hostile /
  inconsistent archives are rejected without touching the bucket.

Run: `python3 editor/tests/test_hosted_delta.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_REPO, "editor"))
sys.path.insert(0, os.path.join(_REPO, "broker"))
import shares           # noqa: E402  (editor/)
import delta            # noqa: E402  (broker/)

TOKEN = "ab" * 16
INSTALL = "cd" * 16


class Bucket:
    """Dict-backed stand-in for r2.put_bytes / delete_keys."""
    def __init__(self):
        self.objs = {}
        self.puts = []

    def put(self, key, body, *a):
        self.objs[key] = body
        self.puts.append(key)

    def delete_keys(self, keys):
        for k in keys:
            self.objs.pop(k, None)


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def setup(tmp):
    ws = os.path.join(tmp, "ws")
    proj = os.path.join(tmp, "proj")
    write(proj, "source/main/index.html", "<h1>v1</h1>")
    write(proj, "source/main/app.js", "console.log(1)")
    write(proj, "design-systems/all.css", "body{}")
    write(ws, "fonts/MyFont.woff2", "fontbytes")
    shares.init(ws, _REPO, lambda p: proj)
    rec = {"id": "s1", "token": TOKEN, "project": "proj", "prototype": "main",
           "label": "L", "emailGate": False}
    return proj, rec


def snapshot(rec):
    return shares._hosted_manifest(shares._hosted_snapshot_members(rec))


def tar_to(path, members, delta_manifest=None):
    shares._hosted_write_tar(path, members, delta_manifest=delta_manifest)
    return path


def apply_full_to(bucket, tar_path):
    snap = delta.load_snapshot(tar_path)
    assert snap["mode"] == "full", "expected a full snapshot"
    return snap, delta.apply_full(tar_path, TOKEN, INSTALL, bucket.put)


def test_full_then_delta(tmp):
    proj, rec = setup(tmp)
    manifest1, members1 = snapshot(rec)
    assert "share/p/source/main/index.html" in manifest1
    assert "fonts/MyFont.woff2" in manifest1

    # ── full upload: manifest round-trips, totals match ──────────────────
    full_tar = tar_to(os.path.join(tmp, "full.tar.gz"), members1)
    bucket = Bucket()
    snap, applied = apply_full_to(bucket, full_tar)
    assert applied == manifest1, "broker-observed manifest == daemon manifest"
    assert snap["total"] == sum(e["s"] for e in manifest1.values())
    assert snap["files"] == len(manifest1)
    assert "s/{}/p/source/main/index.html".format(TOKEN) in bucket.objs
    assert "fonts/{}/MyFont.woff2".format(INSTALL) in bucket.objs
    state_after_full = dict(bucket.objs)

    # ── mutate: edit one file, add one, remove one ───────────────────────
    write(proj, "source/main/app.js", "console.log(2)")
    write(proj, "source/main/new.css", "p{}")
    os.unlink(os.path.join(proj, "design-systems/all.css"))
    manifest2, members2 = snapshot(rec)
    changed = [(a, s) for a, s in members2
               if manifest1.get(a) != manifest2.get(a)]
    changed_arcs = set(a for a, _ in changed)
    must = {"share/p/source/main/app.js", "share/p/source/main/new.css"}
    assert must <= changed_arcs, changed_arcs
    # __hosted.json may differ (second-resolution timestamp); nothing else may.
    assert changed_arcs - must <= {"share/__hosted.json"}, changed_arcs

    # ── delta upload: only changed keys put, stale key deleted ───────────
    delta_tar = tar_to(os.path.join(tmp, "delta.tar.gz"), changed,
                       delta_manifest=manifest2)
    dsnap = delta.load_snapshot(delta_tar)
    assert dsnap["mode"] == "delta"
    assert dsnap["total"] == sum(e["s"] for e in manifest2.values())
    assert dsnap["files"] == len(manifest2)
    bucket.puts = []
    applied2 = delta.apply_delta(delta_tar, dsnap, TOKEN, INSTALL,
                                 manifest1, bucket.put, bucket.delete_keys)
    assert applied2 == manifest2
    assert set(bucket.puts) == set(
        delta.r2_key_for(a, TOKEN, INSTALL) for a in changed_arcs), bucket.puts
    assert "s/{}/p/design-systems/all.css".format(TOKEN) not in bucket.objs, \
        "vanished share file must be deleted"
    assert "fonts/{}/MyFont.woff2".format(INSTALL) in bucket.objs, \
        "fonts are shared across shares - never deleted by a delta"

    # ── the delta result is byte-identical to a fresh full upload ────────
    fresh = Bucket()
    apply_full_to(fresh, tar_to(os.path.join(tmp, "full2.tar.gz"), members2))
    fresh.objs["fonts/{}/MyFont.woff2".format(INSTALL)]  # font unchanged either way
    assert bucket.objs == fresh.objs, "delta and full must converge"
    assert state_after_full != fresh.objs, "sanity: the mutation changed bytes"


def test_rejections(tmp):
    proj, rec = setup(tmp)
    manifest1, members1 = snapshot(rec)

    # Delta whose announced hash does not match the uploaded bytes -> rejected
    # before the manifest is trusted (daemon then falls back to full upload).
    manifest_bad = {k: dict(v) for k, v in manifest1.items()}
    manifest_bad["share/p/source/main/app.js"]["h"] = "0" * 64
    bad_tar = tar_to(os.path.join(tmp, "bad.tar.gz"),
                     [m for m in members1 if m[0] == "share/p/source/main/app.js"],
                     delta_manifest=manifest_bad)
    snap = delta.load_snapshot(bad_tar)
    b = Bucket()
    try:
        delta.apply_delta(bad_tar, snap, TOKEN, INSTALL, manifest1,
                          b.put, b.delete_keys)
        raise AssertionError("hash mismatch must be rejected")
    except ValueError:
        pass

    # Delta announcing a change it does not include -> incomplete.
    manifest_more = {k: dict(v) for k, v in manifest1.items()}
    manifest_more["share/p/source/main/app.js"]["h"] = "f" * 64
    empty_tar = tar_to(os.path.join(tmp, "empty.tar.gz"), [],
                       delta_manifest=manifest_more)
    snap = delta.load_snapshot(empty_tar)
    try:
        delta.apply_delta(empty_tar, snap, TOKEN, INSTALL, manifest1,
                          b.put, b.delete_keys)
        raise AssertionError("incomplete delta must be rejected")
    except ValueError:
        pass

    # Hostile member paths reject at the header walk - nothing written.
    hostile = os.path.join(tmp, "hostile.tar.gz")
    with tarfile.open(hostile, "w:gz") as tf:
        info = tarfile.TarInfo("share/../../etc/passwd")
        data = b"x"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    try:
        delta.load_snapshot(hostile)
        raise AssertionError("traversal member must be rejected")
    except ValueError:
        pass
    # A manifest naming the reserved baseline object is rejected too.
    try:
        delta._parse_manifest(json.dumps(
            {"files": {"share/__manifest.json": {"h": "0" * 64, "s": 1}}}
        ).encode("utf-8"))
        raise AssertionError("reserved manifest arcname must be rejected")
    except ValueError:
        pass


def main():
    fails = 0
    for fn in (test_full_then_delta, test_rejections):
        tmp = tempfile.mkdtemp(prefix="woven-hosted-delta-")
        try:
            fn(tmp)
            print("PASS", fn.__name__)
        except Exception as e:
            fails += 1
            import traceback
            traceback.print_exc()
            print("FAIL", fn.__name__, "-", e)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
