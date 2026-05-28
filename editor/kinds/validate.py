"""editor/kinds/validate.py — synchronous contract checks.

See WORKFLOW_TRUTHFULNESS_PLAN.md §5. Called at three points with three
modes:

  save:           PERMISSIVE — drafts always allowed. Only catches structural
                  errors (unknown kind, wrong field type on populated fields).
                  Critical: this preserves manual canvas use (Principle 11).
  status:running  PERMISSIVE — node can be marked running freely.
  status:done     STRICT — completion.requires must be satisfied.
  status:error    PERMISSIVE — but runError must be non-empty if set.
  commit          STRICT — outputs + files + completion + must-consume.
"""
import glob
import os

from .registry import KINDS, kind_contract


# ── Violation types ─────────────────────────────────────────────────────
SCHEMA_MISMATCH        = "SCHEMA_MISMATCH"
REQUIRED_MISSING       = "REQUIRED_MISSING"
COMPLETION_UNSATISFIED = "COMPLETION_UNSATISFIED"
FILE_MISSING           = "FILE_MISSING"
FILE_EMPTY             = "FILE_EMPTY"
UNHANDLED_OUTPUT       = "UNHANDLED_OUTPUT"
UNKNOWN_KIND           = "UNKNOWN_KIND"
RUN_ERROR_MISSING      = "RUN_ERROR_MISSING"


def _violation(type_, message, **kw):
    """Construct a violation dict. `type_` is one of the constants above."""
    out = {"type": type_, "message": message}
    out.update(kw)
    return out


# ── Field-shape sanity (used at save time, permissively) ────────────────
def _coerce_value_type(value, declared_type):
    """Best-effort: is `value` plausibly of `declared_type`?
    Permissive — we only reject blatantly wrong shapes (an object where the
    contract expects a string, etc.). Empty/missing is always fine at save.
    """
    if value is None or value == "":
        return True
    if declared_type in ("text", "markdown"):
        return isinstance(value, str)
    if declared_type == "enum":
        return isinstance(value, (str, bool, int, float))
    if declared_type == "bool":
        return isinstance(value, bool)
    if declared_type == "number":
        return isinstance(value, (int, float))
    if declared_type == "array":
        return isinstance(value, list)
    if declared_type == "object":
        return isinstance(value, dict)
    if declared_type == "fileList":
        return isinstance(value, list)
    if declared_type == "ref":
        return isinstance(value, str)
    # Unknown declared_type — accept (forward-compat).
    return True


def _check_schema(node, contract, mode):
    """Per-field schema check. Returns list of violations. Save-mode is
    permissive (only flags populated fields with wrong types)."""
    viols = []
    if not isinstance(node, dict): return viols
    inputs = contract.get("inputs") or {}
    for key, spec in inputs.items():
        if not isinstance(spec, dict): continue
        # Resolve dotted keys (e.g. spec.genre → node["spec"]["genre"])
        path = key.split(".")
        cur = node
        present = True
        for p in path:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                present = False
                break
        if not present:
            continue   # absent fields are always OK at save; required-at-commit checked separately
        if not _coerce_value_type(cur, spec.get("type")):
            viols.append(_violation(SCHEMA_MISMATCH,
                f"field {key!r} has wrong type (got {type(cur).__name__})",
                field=key, expected=spec.get("type")))
    return viols


# ── Completion checks (used at status:done and commit) ─────────────────
def _resolve_path_template(template, node, project_root):
    """Resolve {branch}, {variant}, {dsId}, etc. in an outputsRoot/file path.
    Returns the resolved absolute path under project_root."""
    if not template:
        return None
    # node may carry branch/variant/dsId in various places
    repl = {
        "branch":  node.get("branch") or "main",
        "variant": node.get("variant") or "",
        "dsId":    node.get("dsId") or "main",
        "id":      node.get("id") or "",
    }
    out = template
    for k, v in repl.items():
        out = out.replace("{" + k + "}", str(v))
    # Defensive: ensure no leftover {placeholder}
    if "{" in out and "}" in out:
        return None
    return os.path.join(project_root, out.lstrip("/"))


def _check_files_exist(node, contract, project_root):
    """Check the contract's completion.requires entries that reference
    files. Returns list of violations."""
    viols = []
    requires = (contract.get("completion") or {}).get("requires") or []
    outputs_root_tmpl = contract.get("outputsRoot")
    outputs_root = _resolve_path_template(outputs_root_tmpl, node, project_root) if outputs_root_tmpl else None

    for req in requires:
        if not isinstance(req, str): continue
        rs = req.strip()
        # Parse "files: <path-or-pattern> exists" / "files: <pattern> non-empty"
        if rs.startswith("files:"):
            spec = rs[len("files:"):].strip()
            # Substitute {outputsRoot}
            if outputs_root:
                spec = spec.replace("outputsRoot", outputs_root.replace(project_root + "/", ""))
            # Patterns we recognize:
            #   <path> exists
            #   <path> exists, non-empty
            #   <pattern> contains at least one <ext>
            lower = spec.lower()
            if " exists" in lower:
                rel = spec.split(" ", 1)[0].strip()
                full = os.path.join(project_root, rel)
                if not os.path.exists(full):
                    viols.append(_violation(FILE_MISSING,
                        f"required file missing: {rel}", path=rel))
                elif ("non-empty" in lower) and os.path.isfile(full) and os.path.getsize(full) == 0:
                    viols.append(_violation(FILE_EMPTY,
                        f"required file is 0 bytes: {rel}", path=rel))
            elif " contains at least one " in lower:
                # e.g. "outputsRoot/shells/ contains at least one .css"
                left, ext = spec.lower().split(" contains at least one ", 1)
                dir_path = os.path.join(project_root, spec[:len(left)].strip())
                ext = ext.strip().lstrip(".")
                if not os.path.isdir(dir_path):
                    viols.append(_violation(FILE_MISSING,
                        f"required directory missing: {left}", path=left))
                else:
                    matches = glob.glob(os.path.join(dir_path, f"*.{ext}"))
                    if not matches:
                        viols.append(_violation(FILE_MISSING,
                            f"no .{ext} files in {left}", path=left))
        # outputs.X set / non-empty
        elif rs.startswith("outputs."):
            field = rs.split(" ", 1)[0][len("outputs."):]
            outputs = node.get("outputs") or {}
            val = outputs.get(field)
            empty = (val is None) or (isinstance(val, (str, list, dict)) and len(val) == 0)
            if empty:
                viols.append(_violation(REQUIRED_MISSING,
                    f"required output missing or empty: {field}", field=field))
        # consumeFrom: 0 unhandled files — caller verifies separately
        elif rs.startswith("consumeFrom:"):
            pass  # handled by validate_consume
        # Other freeform requirements logged as completion checks the
        # validator can't autoverify — agent must self-report.
    return viols


def _check_required_outputs(node, contract):
    """Check that all outputs marked required=True are populated."""
    viols = []
    outputs_spec = contract.get("outputs") or {}
    outputs_val  = node.get("outputs") or {}
    for key, spec in outputs_spec.items():
        if not isinstance(spec, dict): continue
        if not spec.get("required"): continue
        v = outputs_val.get(key)
        if v is None or (isinstance(v, (str, list, dict)) and len(v) == 0):
            viols.append(_violation(REQUIRED_MISSING,
                f"required output {key!r} missing or empty",
                field=key))
    return viols


def validate_node(node, action, project_root=None):
    """Validate a node against its kind contract.
    Returns list of violations. Empty list = pass.

    `action` is one of:
      'save'           — PERMISSIVE (structural-only)
      'status:running' — PERMISSIVE
      'status:done'    — STRICT (completion)
      'status:error'   — runError must be non-empty if runStatus=error
      'commit'         — STRICT (completion + must-consume; caller validates upstream)
    """
    if not isinstance(node, dict):
        return [_violation(SCHEMA_MISMATCH, "node must be an object")]
    kind = node.get("kind")
    if not kind:
        return [_violation(SCHEMA_MISMATCH, "node.kind required")]
    contract = kind_contract(kind, node.get("id"))
    if not contract:
        # Unknown kind: legacy/forward-compat. Save permissively (Principle 11);
        # reject on commit only.
        if action == "commit":
            return [_violation(UNKNOWN_KIND, f"unknown kind: {kind!r}", kind=kind)]
        return []

    viols = []
    # All actions get a structural schema check (cheap; flags blatant type mismatches)
    viols.extend(_check_schema(node, contract, action))

    if action == "save" or action == "status:running":
        # Save is always permissive — schema check above is the only gate.
        return viols

    if action == "status:error":
        if node.get("runStatus") == "error" and not node.get("runError"):
            viols.append(_violation(RUN_ERROR_MISSING,
                "runStatus=error requires non-empty runError"))
        return viols

    # status:done OR commit — strict.
    viols.extend(_check_required_outputs(node, contract))
    if project_root:
        viols.extend(_check_files_exist(node, contract, project_root))
    return viols


def validate_consume(node, upstream_folder, project_root):
    """For consumer kinds (design-system etc.), enumerate upstream's
    outputsRoot folder and verify every file matches a consumeFrom rule.
    Returns list of UNHANDLED_OUTPUT violations (empty = pass).

    `upstream_folder` is an absolute path to the upstream producer's
    outputsRoot folder."""
    if not isinstance(node, dict): return []
    contract = kind_contract(node.get("kind"), node.get("id"))
    if not contract: return []
    cf = contract.get("consumeFrom")
    if not cf: return []   # this kind doesn't consume — nothing to check
    rules = cf.get("rules") or []
    unhandled_policy = (cf.get("unhandled") or "reject").lower()
    if not os.path.isdir(upstream_folder):
        # Upstream missing — that's a different drift (caller checks).
        return []

    import fnmatch
    viols = []
    for dirpath, dirnames, filenames in os.walk(upstream_folder):
        # Skip hidden + staging
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and not d.endswith("_staging")]
        for fn in filenames:
            if fn.startswith("."): continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, upstream_folder)
            matched = False
            for rule in rules:
                pat = rule.get("match", "")
                # fnmatch handles glob basics; ** matched as *
                if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(fn, pat) or fnmatch.fnmatch(rel.replace("**/", "")
                        , pat.replace("**/", "")):
                    matched = True
                    break
            if not matched:
                viols.append(_violation(UNHANDLED_OUTPUT,
                    f"upstream file not routed by any consumeFrom rule: {rel}",
                    file=rel, upstreamFolder=upstream_folder, policy=unhandled_policy))
    if unhandled_policy == "warn":
        # Demote to warnings — still surfaced, but caller won't 400.
        for v in viols:
            v["severity"] = "warn"
    return viols
