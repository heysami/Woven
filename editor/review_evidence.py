"""Evidence provenance and honest separation of rendering from visual review."""
import hashlib
import os


def source_revision(root):
    """Hash the reviewed directory, including its local scripts and assets."""
    if not root or not os.path.isdir(root):
        return None
    digest = hashlib.sha256()
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in ("node_modules", "workflow"))
        for name in sorted(names):
            path = os.path.join(directory, name)
            if os.path.islink(path) or name.startswith("."):
                continue
            digest.update(os.path.relpath(path, root).encode())
            try:
                with open(path, "rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                return None
    return digest.hexdigest()


def attach(report, expected=None, before=None, after=None):
    result = dict(report)
    judge = result.get("judge") or {}
    mechanical = result.get("renderVerdict", result.get("verdict"))
    status = "not-requested" if not expected else "unavailable" if not judge.get("available") else (
        "passed" if judge.get("ok") is True else "failed" if judge.get("ok") is False else "inconclusive")
    stale = before is not None and after != before
    result["visualReview"] = {"status": status, "model": judge.get("model"),
        "transport": judge.get("transport"), "expected": expected, "frames": judge.get("stripFrames"),
        "sourceRevision": before, "sourceRevisionAfter": after, "stale": stale}
    result["renderVerdict"] = mechanical
    if stale:
        result["verdict"] = "stale"
    elif expected and status != "passed" and mechanical == "pass":
        result["verdict"] = "effect-wrong" if status == "failed" else "inconclusive"
    return result
