"""Revision-aware HTML storage shared by visual editing endpoints."""
import hashlib
import os
import tempfile
import threading
import stat
from pathlib import Path

_locks = [threading.RLock() for _ in range(64)]


def revision(content):
    return hashlib.sha256(content).hexdigest()[:16]


def lock(path):
    return _locks[hash(str(Path(path).resolve())) % len(_locks)]


def read(path):
    with lock(path):
        content = Path(path).read_bytes()
        return {"html": content.decode("utf-8"), "version": revision(content)}


def source_path(root, relative):
    base = (Path(root) / "source").resolve()
    path = (Path(root) / relative).resolve()
    if os.path.commonpath([str(path), str(base)]) != str(base):
        raise ValueError("Source edits cannot leave the project's source folder")
    return str(path)


class Conflict(Exception):
    pass


def write(path, html, expected=None):
    with lock(path):
        current = Path(path).read_bytes()
        if expected is not None and expected != revision(current):
            raise Conflict("This file changed outside this editing session. Your edits are still pending. Reload the latest version before saving again.")
        content = html.encode("utf-8")
        fd, staging = tempfile.mkstemp(prefix=".woven-edit-", dir=Path(path).parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                os.fchmod(handle.fileno(), stat.S_IMODE(os.stat(path).st_mode))
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging, path)
        finally:
            if os.path.exists(staging):
                os.unlink(staging)
        return {"ok": True, "size": len(content), "version": revision(content)}
