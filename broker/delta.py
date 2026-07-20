"""Hosted-snapshot extraction with manifest deltas.

A snapshot tar.gz arrives in one of two shapes:

  full   - every gate-servable file (the legacy shape; also the fallback
           whenever a delta cannot be applied). The R2 prefix is wiped by the
           caller first, then every member is uploaded.
  delta  - the FIRST file member is `__delta.json` carrying the complete new
           manifest ({arcname: {"h": sha256, "s": size}}); the remaining
           members are only the files whose hash changed since the manifest
           stored at s/<token>/__manifest.json. Unchanged objects stay put,
           objects missing from the new manifest are deleted (share/ keys
           only - fonts are shared across an install's shares).

Either way the resulting manifest is returned so the caller can persist it as
the baseline for the next delta. Pure stdlib + injected put/delete callables,
so it unit-tests without the FastAPI/boto3 stack (editor/tests/test_hosted_delta.py).
"""
from __future__ import annotations

import hashlib
import json
import tarfile
from typing import Callable, Optional

DELTA_MEMBER = "__delta.json"          # tar member announcing a delta upload
MANIFEST_OBJECT = "__manifest.json"    # baseline object under s/<token>/
_HASH_HEX = 64                         # sha256 hexdigest length


def manifest_object_key(token: str) -> str:
    return "s/" + token + "/" + MANIFEST_OBJECT


def _clean_name(name: str) -> tuple[str, list]:
    """Validate a tar member / manifest arcname. Raises ValueError on anything
    hostile (absolute, dotted segments, traversal) - same rules the legacy
    extractor enforced."""
    name = name.lstrip("./")
    parts = name.split("/")
    if (not name or name.startswith("/") or ".." in parts
            or any(p.startswith(".") for p in parts)):
        raise ValueError(f"unsafe member path: {name!r}")
    if name == "share/" + MANIFEST_OBJECT:
        raise ValueError(f"reserved member path: {name!r}")
    return name, parts


def r2_key_for(name: str, token: str, install_id: str) -> str:
    """Map a validated arcname to its bucket key."""
    name, parts = _clean_name(name)
    if parts[0] == "share" and len(parts) >= 2:
        return "s/" + token + "/" + "/".join(parts[1:])
    if parts[0] == "fonts" and len(parts) == 2:
        return "fonts/" + install_id + "/" + parts[1]
    raise ValueError(f"unexpected member outside share//fonts/: {name!r}")


def _validate_member(name: str) -> None:
    """Header-walk validation: same rules as r2_key_for, no key built. Lets
    load_snapshot reject a bad archive BEFORE the caller touches the bucket."""
    r2_key_for(name, "", "")


def _parse_manifest(raw: bytes) -> dict:
    """Parse + validate a manifest payload. Returns {arcname: {"h","s"}}."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("bad delta manifest: not JSON")
    files = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(files, dict) or not files:
        raise ValueError("bad delta manifest: missing files")
    out = {}
    for name, ent in files.items():
        _validate_member(str(name))
        h = (ent or {}).get("h") if isinstance(ent, dict) else None
        s = (ent or {}).get("s") if isinstance(ent, dict) else None
        if (not isinstance(h, str) or len(h) != _HASH_HEX
                or not isinstance(s, int) or s < 0):
            raise ValueError(f"bad delta manifest entry: {name!r}")
        out[str(name)] = {"h": h, "s": s}
    return out


def parse_stored_manifest(raw: Optional[bytes]) -> Optional[dict]:
    """Baseline manifest from R2 - None (not hosted yet / pre-delta upload or
    corrupt) simply means the next upload must be full."""
    if not raw:
        return None
    try:
        return _parse_manifest(raw)
    except ValueError:
        return None


def manifest_bytes(manifest: dict) -> bytes:
    return json.dumps({"v": 1, "files": manifest}).encode("utf-8")


def load_snapshot(tmp_path: str) -> dict:
    """Cheap header walk before anything is written to the bucket. Returns
      {"mode": "full"|"delta", "manifest": dict|None, "total": int, "files": int}
    where total/files describe the COMPLETE resulting snapshot (delta included -
    its manifest covers unchanged files too). Raises ValueError / tarfile.TarError."""
    with tarfile.open(tmp_path, "r:gz") as tf:
        first = True
        manifest = None
        total = 0
        files = 0
        for m in tf:
            if not m.isfile():
                continue          # no dirs needed, no symlinks EVER
            if first and m.name.lstrip("./") == DELTA_MEMBER:
                f = tf.extractfile(m)
                manifest = _parse_manifest(f.read() if f else b"")
                first = False
                continue
            first = False
            _validate_member(m.name)
            total += m.size
            files += 1
    if manifest is not None:
        return {"mode": "delta", "manifest": manifest,
                "total": sum(e["s"] for e in manifest.values()),
                "files": len(manifest)}
    if files == 0:
        raise ValueError("empty snapshot")
    return {"mode": "full", "manifest": None, "total": total, "files": files}


def apply_full(tmp_path: str, token: str, install_id: str,
               put_bytes: Callable) -> dict:
    """Upload every member; the caller has already cleared the prefix.
    Returns the manifest of what was written."""
    manifest = {}
    with tarfile.open(tmp_path, "r:gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            name, _parts = _clean_name(m.name)
            key = r2_key_for(name, token, install_id)
            f = tf.extractfile(m)
            if f is None:
                continue
            body = f.read()
            put_bytes(key, body)
            manifest[name] = {"h": hashlib.sha256(body).hexdigest(),
                              "s": len(body)}
    if not manifest:
        raise ValueError("empty snapshot")
    return manifest


def apply_delta(tmp_path: str, snap: dict, token: str, install_id: str,
                stored: dict, put_bytes: Callable,
                delete_keys: Callable) -> dict:
    """Apply a delta tar on top of the stored baseline: put changed members
    (hash-verified against the announced manifest), delete share/ objects that
    left the manifest, keep everything else untouched. Returns the new
    manifest. Raises ValueError when the delta is inconsistent - the caller
    responds 400 and the daemon falls back to a full upload."""
    manifest = snap["manifest"] or {}
    needed = set(k for k, v in manifest.items() if stored.get(k) != v)
    uploaded = set()
    with tarfile.open(tmp_path, "r:gz") as tf:
        first = True
        for m in tf:
            if not m.isfile():
                continue
            if first and m.name.lstrip("./") == DELTA_MEMBER:
                first = False
                continue
            first = False
            name, _parts = _clean_name(m.name)
            ent = manifest.get(name)
            if ent is None:
                raise ValueError(f"delta member not in manifest: {name!r}")
            f = tf.extractfile(m)
            if f is None:
                continue
            body = f.read()
            if len(body) != ent["s"] or hashlib.sha256(body).hexdigest() != ent["h"]:
                raise ValueError(f"delta member does not match manifest: {name!r}")
            put_bytes(r2_key_for(name, token, install_id), body)
            uploaded.add(name)
    missing = needed - uploaded
    if missing:
        raise ValueError("delta incomplete: {} changed file(s) not in archive"
                         .format(len(missing)))
    # Objects that left the snapshot. Only share/ keys - fonts/<install>/ is
    # shared by every share of the install, so font removal is left to the
    # full-upload path / install deprovision.
    stale = [k for k in stored
             if k not in manifest and k.startswith("share/")]
    if stale:
        keys = []
        for k in stale:
            try:
                keys.append(r2_key_for(k, token, install_id))
            except ValueError:
                continue          # hostile baseline entry - nothing to delete
        for i in range(0, len(keys), 1000):
            delete_keys(keys[i:i + 1000])
    return manifest
