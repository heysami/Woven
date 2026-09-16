"""Lossless context helpers. No model calls, shared state, or project discovery."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def project_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("a project-relative path is required")
    base = Path(root).resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base) or target == base:
        raise ValueError("path escapes project")
    return target


def atomic_json(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n")


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique staging file, safe with concurrent readers and writers.
    fd, staging = tempfile.mkstemp(prefix=".context-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(staging, path)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def reference_key(source, revision, request):
    if not all(isinstance(v, str) and v.strip() for v in (source, revision, request)):
        raise ValueError("source, verified revision, and exact request are required")
    return digest({"version": 1, "source": source, "revision": revision, "request": request})


def reference_get(root, key):
    path = project_path(root, "workflow/context-cache/" + key + ".json")
    try:
        cached = json.loads(path.read_text())
        if cached.get("key") == key and digest(cached["value"]) == cached.get("valueHash"):
            return cached["value"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def reference_put(root, key, value):
    # Cache only successful, non-empty extractions; callers retain raw evidence.
    if not value:
        raise ValueError("cannot cache an empty extraction")
    path = project_path(root, "workflow/context-cache/" + key + ".json")
    atomic_json(path, {"key": key, "valueHash": digest(value), "value": value})


def qa_packet(report):
    """Collapse only explicitly successful entries, never failures or unknowns.

    Frames, metrics, errors, skipped checks, and overall verdict stay intact.
    The daemon stores the complete report before applying this projection.
    """
    summaries = []

    def walk(value, path=""):
        if isinstance(value, dict):
            return {k: walk(v, path + "/" + k) for k, v in value.items()}
        if isinstance(value, list):
            if path.rsplit("/", 1)[-1] in ("checks", "cases", "results"):
                kept, passed = [], []
                for index, row in enumerate(value):
                    # Warnings or evidence alongside a pass can still be useful.
                    clean = isinstance(row, dict) and (
                        row.get("pass") is True or row.get("status") == "pass" or row.get("verdict") == "pass")
                    clean = clean and not any(row.get(k) for k in (
                        "error", "errors", "failure", "failures", "failedExpect",
                        "pageErrors", "consoleErrors", "warning", "warnings", "skipped"))
                    clean = clean and all(row.get(k) not in (False, "fail", "error", "skip", "skipped")
                                          for k in ("pass", "status", "verdict"))
                    if clean:
                        passed.append({"index": index, "id": row.get("id", row.get("name", row.get("check")))})
                        # Preserve evidence references for visual reviewers, even
                        # for passing cases. Deep detail stays in the full report.
                        kept.append({k: v for k, v in row.items() if k in (
                            "id", "name", "check", "kind", "verdict", "status", "pass",
                            "title", "frames", "screenshots", "path", "metrics")
                                     or isinstance(v, (int, float))})
                    else:
                        kept.append(walk(row, path + "/" + str(index)))
                if passed:
                    summaries.append({"path": path, "count": len(passed)})
                return kept
            return [walk(v, path + "/" + str(i)) for i, v in enumerate(value)]
        return value

    result = walk(copy.deepcopy(report))
    result["passedChecks"] = summaries
    return result


def assemble_contract(draft, defaults):
    """Fill shared boilerplate without rewriting any authored value."""
    if not isinstance(draft, dict):
        raise ValueError("draft must be an object")

    def merge(base, supplied):
        if isinstance(base, dict) and isinstance(supplied, dict):
            return {k: merge(base.get(k), supplied[k]) if k in supplied else copy.deepcopy(base[k])
                    for k in base.keys() | supplied.keys()}
        return copy.deepcopy(supplied)

    result = merge(defaults, draft)
    required = {"platePath": str, "extracted": dict, "authored": dict,
                "crossSurfaceContract": dict, "voice": dict, "buildRegister": dict,
                "itemReferences": list, "surfaceContracts": dict, "formatCommitments": list}
    for field, kind in required.items():
        if field not in draft or not isinstance(draft[field], kind):
            raise ValueError("draft requires " + field)
    for field in ("extracted", "authored", "crossSurfaceContract", "voice", "buildRegister"):
        if not draft[field]:
            raise ValueError("author creative decisions for " + field)
    required_fields = {
        "extracted": ("moodWords", "palette", "valueStructure", "contrastRegister", "lightModel",
                      "materialRead", "composition", "typeConstruction"),
        "authored": ("typography", "componentStyle", "motionCharacter", "spacing"),
        "crossSurfaceContract": ("sharedPaletteHexes", "colorUsePrinciple", "imageryRegister",
                                 "materialDirective", "antiPatterns"),
        "voice": ("audience", "toneWords"), "buildRegister": ("deriveFrom", "cadence"),
    }
    for group, fields in required_fields.items():
        for field in fields:
            if field not in draft[group]:
                raise ValueError("draft requires " + group + "." + field)
    for ref in draft["itemReferences"]:
        if not isinstance(ref, dict) or not all(k in ref for k in ("itemId", "role", "refPath", "matchesSlots", "bboxNote")):
            raise ValueError("incomplete item reference")
    version = result.get("contractVersion")
    if type(version) is not int or version < 1:
        raise ValueError("contractVersion must be a positive integer")
    # Serialize and parse to verify fidelity of all types and nested values.
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
    checked = json.loads(encoded)

    def contains(supplied, actual):
        if isinstance(supplied, dict):
            return all(k in actual and contains(v, actual[k]) for k, v in supplied.items())
        return supplied == actual

    if not contains(draft, checked):
        raise ValueError("contract fidelity check failed")
    return checked
