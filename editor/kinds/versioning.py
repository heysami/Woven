"""editor/kinds/versioning.py — asset-node versioning + composition machinery.

See docs/features/asset-versioning.md for the full design.

Two-tier model per asset node:
  • VERSIONS — snapshots of this asset's own files. Capped at 20 unpinned.
  • COMPOSITIONS — per-version tuples of (sub-asset → sub-version). Capped at
    50 unpinned per parent version. Materialised into workflow/views/.

Storage layout per project:

  workflow/runs/<nodeId>/<versionId>/
      meta.json
      thumb.png
      <files…>                              ← this asset's own files only
      compositions/<compositionId>/
          meta.json
          thumb.png

  workflow/views/<nodeId>/<versionId>/<compositionId>/
      <files…>                              ← parent + sub-asset files,
                                             hardlinked from runs/ for
                                             zero-cost materialisation

  source/                                   ← live working tree; mirrors
                                             active version + active
                                             composition for all assets

This module is pure logic (no HTTP, no daemon dependencies). All filesystem
mutations happen through helpers in this file. Imported by:
  • serve.py — after producer runs, on revert/switch/branch/etc. endpoints
  • reconcile.py — on workflow.json load, for legacy migration
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_MAX_UNPINNED_VERSIONS = 20
DEFAULT_MAX_UNPINNED_COMPOSITIONS = 50
RUNS_DIRNAME = "runs"
VIEWS_DIRNAME = "views"
WORKFLOW_DIRNAME = "workflow"
SOURCE_DIRNAME = "source"
MANIFEST_FILENAME = "MANIFEST.json"

# Crockford base32 alphabet (ulid). Excludes I, L, O, U.
_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


# ── ULID ───────────────────────────────────────────────────────────────────

def make_ulid() -> str:
    """Lexicographically sortable 26-char id. Time prefix + random suffix.

    Not a strict ulid (no overflow handling, no monotonic clamp), but good
    enough for per-node version ordering and avoids a new dependency."""
    ms = int(time.time() * 1000)
    # 10 chars of time (48 bits) + 16 chars of randomness (80 bits)
    time_chars = []
    for _ in range(10):
        ms, rem = divmod(ms, 32)
        time_chars.append(_ULID_ALPHABET[rem])
    time_part = "".join(reversed(time_chars))
    rand_part = "".join(_ULID_ALPHABET[secrets.randbelow(32)] for _ in range(16))
    return time_part + rand_part


# ── Path helpers ───────────────────────────────────────────────────────────

def workflow_dir(project_root: str) -> str:
    return os.path.join(project_root, WORKFLOW_DIRNAME)


def runs_dir(project_root: str, node_id: Optional[str] = None,
             version_id: Optional[str] = None,
             composition_id: Optional[str] = None) -> str:
    parts = [project_root, WORKFLOW_DIRNAME, RUNS_DIRNAME]
    if node_id: parts.append(node_id)
    if version_id: parts.append(version_id)
    if composition_id: parts.extend(["compositions", composition_id])
    return os.path.join(*parts)


def view_dir(project_root: str, node_id: str, version_id: str,
             composition_id: str) -> str:
    return os.path.join(
        project_root, WORKFLOW_DIRNAME, VIEWS_DIRNAME,
        node_id, version_id, composition_id,
    )


def source_root(project_root: str) -> str:
    return os.path.join(project_root, SOURCE_DIRNAME)


# ── Asset node introspection ───────────────────────────────────────────────

def asset_files(node: Dict[str, Any]) -> List[str]:
    """Return the list of project-relative paths this asset references.

    Accepts both `path` (single, from registry) and `paths` (list, used by
    html-set scaffolds). Strips leading slashes; preserves order; dedupes."""
    out: List[str] = []
    seen: set = set()
    p = node.get("path")
    if isinstance(p, str) and p.strip():
        rel = p.strip().lstrip("/")
        if rel and rel not in seen:
            out.append(rel); seen.add(rel)
    ps = node.get("paths")
    if isinstance(ps, list):
        for x in ps:
            if not isinstance(x, str): continue
            rel = x.strip().lstrip("/")
            if rel and rel not in seen:
                out.append(rel); seen.add(rel)
    return out


def is_asset(node: Dict[str, Any]) -> bool:
    return isinstance(node, dict) and node.get("kind") == "asset"


# ── Versionable kinds: asset, prototype, design-system ─────────────────────
#
# Every kind in this set gets snapshot/picker/revert/branch coverage. The
# `kind_scope_dirs(node, project_root)` helper returns the project-relative
# directories this node "owns" — the file watcher's snapshot trigger fires
# when ANY file under any of those dirs changes.

VERSIONABLE_KINDS = ("asset", "prototype", "design-system")

# v3.2 — Deferral state for scope-level (prototype / design-system) snapshots.
# Maps `abs(project_root)` → { nodeId → file_mtime_observed }. Populated by
# snapshot_changed_assets() when a multi-file scope is still in flight; the
# watcher calls flush_pending_scope_snapshots() on every tick to revisit
# deferred scopes once they've gone quiet.
_PENDING_SCOPE_SNAPSHOTS: Dict[str, Dict[str, float]] = {}


def flush_pending_scope_snapshots(project_root: str,
                                   workflow: Dict[str, Any],
                                   ) -> List[Dict[str, Any]]:
    """Re-attempt deferred prototype/design-system snapshots whose scope has
    now gone quiet (last write older than SCOPE_QUIESCENCE_SEC). Called by
    the file watcher on every tick — cheap if there are no deferrals.

    Returns the same shape as snapshot_changed_assets: list of
    {nodeId, versionId} for any new snapshots that landed.
    """
    project_key = os.path.abspath(project_root)
    pending = _PENDING_SCOPE_SNAPSHOTS.get(project_key)
    if not pending:
        return []
    # For each deferred node, synthesize a paths set covering its scope and
    # re-call snapshot_changed_assets. The quiescence re-check inside it
    # will either snapshot (if quiet) or re-defer (if still active).
    out: List[Dict[str, Any]] = []
    nodes_by_id = {n.get("id"): n for n in (workflow.get("nodes") or [])
                   if isinstance(n, dict) and n.get("id")}
    for nid in list(pending.keys()):
        node = nodes_by_id.get(nid)
        if not node or node.get("kind") not in ("prototype", "design-system"):
            # Node is gone or no longer scope-kind — drop the deferral.
            pending.pop(nid, None)
            continue
        scope_rels = list(node_scope_files(project_root, node))
        if not scope_rels:
            pending.pop(nid, None)
            continue
        snaps = snapshot_changed_assets(project_root, workflow, scope_rels)
        out.extend(snaps)
    # If pending is now empty, GC the project entry.
    if not pending:
        _PENDING_SCOPE_SNAPSHOTS.pop(project_key, None)
    return out

# Paths under source/ that we skip when walking prototype scope. These are
# either editor / daemon state or owned by other versioned nodes.
_PROTOTYPE_SKIP_PARTS = {".history", ".archive", "node_modules", ".git", ".DS_Store"}


def is_versionable(node: Dict[str, Any]) -> bool:
    return isinstance(node, dict) and node.get("kind") in VERSIONABLE_KINDS


def kind_scope_dirs(node: Dict[str, Any]) -> List[str]:
    """Return project-relative root dirs this node's snapshot covers.

    asset         → empty list (uses asset_files() for explicit paths)
    prototype     → ["source"]
    design-system → ["design-systems/<dsId>"] (dsId from node.dsId or path).
    """
    kind = node.get("kind") if isinstance(node, dict) else None
    if kind == "prototype":
        return [SOURCE_DIRNAME]
    if kind == "design-system":
        ds_id = node.get("dsId") or (node.get("spec") or {}).get("id")
        if isinstance(ds_id, str) and ds_id.strip():
            return [f"design-systems/{ds_id.strip()}"]
        # Fallback: snapshot all of design-systems/ when dsId unknown.
        return ["design-systems"]
    return []


def walk_scope_files(project_root: str, scope_dirs: Iterable[str],
                      skip_parts: Iterable[str] = _PROTOTYPE_SKIP_PARTS,
                      ) -> List[str]:
    """Recursively list every file under each scope dir as project-relative
    paths. Skips directories named in skip_parts at any depth."""
    skip = set(skip_parts or ())
    out: List[str] = []
    for rel in scope_dirs:
        if not isinstance(rel, str) or not rel: continue
        abs_root = os.path.join(project_root, rel.lstrip("/"))
        if not os.path.isdir(abs_root): continue
        for root, dirs, files in os.walk(abs_root):
            # Prune skip dirs in place so os.walk doesn't descend.
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
            for name in files:
                if name in skip or name.startswith("."): continue
                abs_p = os.path.join(root, name)
                rel_p = os.path.relpath(abs_p, project_root)
                out.append(rel_p)
    return out


def node_scope_files(project_root: str, node: Dict[str, Any]) -> List[str]:
    """Unified file enumeration for any versionable node.

    asset         → asset_files() (declared paths)
    prototype     → walk_scope_files(['source'])
    design-system → walk_scope_files(['design-systems/<dsId>'])
    """
    if not isinstance(node, dict): return []
    kind = node.get("kind")
    if kind == "asset":
        return asset_files(node)
    if kind in ("prototype", "design-system"):
        return walk_scope_files(project_root, kind_scope_dirs(node))
    return []


def hash_text(text: Optional[str]) -> str:
    """sha256 of a string; '' for None/empty so divergence is detectable."""
    if text is None: text = ""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Manifest reading ───────────────────────────────────────────────────────

def read_manifest(project_root: str, search_dirs: Iterable[str]) -> Optional[Dict[str, Any]]:
    """Look for MANIFEST.json inside any of the given project-relative dirs.

    Returns the parsed dict on first hit, or None. Order is the iteration
    order of search_dirs — caller should pass most-specific dir first."""
    for rel in search_dirs:
        if not rel: continue
        p = os.path.join(project_root, rel.lstrip("/"), MANIFEST_FILENAME)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                continue
    return None


# ── File ops with hardlink fallback ────────────────────────────────────────

def hardlink_or_copy(src: str, dst: str) -> str:
    """Materialise src at dst, preferring hardlinks (zero cost) and falling
    back to a full copy when hardlinks aren't available (rare). Returns
    'link' or 'copy' so the caller can log/diagnose.

    Idempotent: if dst already points at the same inode as src, no-op.
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        try:
            if os.path.samefile(src, dst):
                return "link"
        except OSError:
            pass
        try: os.remove(dst)
        except OSError: pass
    try:
        os.link(src, dst)
        return "link"
    except (OSError, NotImplementedError):
        shutil.copy2(src, dst)
        return "copy"


def copy_tree_into(src_dir: str, dst_dir: str, *, use_link: bool = True) -> int:
    """Recursively copy every file under src_dir into dst_dir, preserving
    relative paths. Hardlinks when use_link is True. Returns file count."""
    n = 0
    if not os.path.isdir(src_dir):
        return 0
    for root, _, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        for name in files:
            src = os.path.join(root, name)
            dst = os.path.join(dst_dir, rel, name) if rel != "." else os.path.join(dst_dir, name)
            if use_link:
                hardlink_or_copy(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            n += 1
    return n


# ── Snapshot ───────────────────────────────────────────────────────────────

def snapshot_asset(project_root: str, node: Dict[str, Any], *,
                   consumed_versions: Optional[Dict[str, Dict[str, str]]] = None,
                   sub_asset_pins: Optional[Dict[str, str]] = None,
                   sub_asset_mounts: Optional[Dict[str, str]] = None,
                   run_id: Optional[str] = None,
                   manifest: Optional[Dict[str, Any]] = None,
                   max_unpinned_versions: int = DEFAULT_MAX_UNPINNED_VERSIONS,
                   max_unpinned_compositions: int = DEFAULT_MAX_UNPINNED_COMPOSITIONS,
                   ) -> Optional[Dict[str, Any]]:
    """Capture the asset's current canonical files as a new version + auto-
    locked composition. Materialise the view dir. Run eviction.

    Mutates `node` in place. Returns the new version entry, or None if the
    asset has no files on disk to snapshot.

    Arguments:
      consumed_versions  — non-asset upstream lineage map (id → {outputHash}).
      sub_asset_pins     — sub-asset id → versionId at run time.
      sub_asset_mounts   — sub-asset id → project-relative mount path under
                           which its files should appear in the view dir.
      run_id             — runId tag for the version entry.
      manifest           — optional MANIFEST.json contents (for files[] /
                           subAssetInputs[]).
    """
    consumed_versions = dict(consumed_versions or {})
    sub_asset_pins   = dict(sub_asset_pins or {})
    sub_asset_mounts = dict(sub_asset_mounts or {})

    # Resolve the file list to snapshot. Order of preference:
    #   1. manifest.files[].path (most specific — subagent declared)
    #   2. asset_files(node) for kind=asset (declared path/paths)
    #   3. node_scope_files() for prototype/design-system (full scope walk)
    files: List[str] = []
    if manifest and isinstance(manifest.get("files"), list):
        for fe in manifest["files"]:
            if isinstance(fe, dict) and isinstance(fe.get("path"), str):
                files.append(fe["path"].lstrip("/"))
    if not files:
        if node.get("kind") == "asset":
            files = asset_files(node)
        else:
            files = node_scope_files(project_root, node)
    files = [f for f in files if f]
    if not files:
        return None

    node_id = node.get("id")
    if not isinstance(node_id, str) or not node_id:
        return None

    # Resolve absolute paths + filter to those that exist.
    abs_files: List[Tuple[str, str]] = []  # (rel, abs)
    for rel in files:
        src_abs = os.path.join(project_root, rel)
        if os.path.isfile(src_abs):
            abs_files.append((rel, src_abs))
    if not abs_files:
        return None

    # Allocate new ids.
    vid = make_ulid()
    cid = make_ulid()

    # Layout the snapshot: workflow/runs/<nodeId>/<vid>/<files>
    # Files are stored relative to source/ so revert can copy them back cleanly.
    # We choose the storage path inside the version dir to mirror the
    # project-relative path stripped of any leading "source/" prefix.
    def in_version_path(rel: str) -> str:
        # Strip leading "source/" so revert restores to canonical paths.
        if rel.startswith("source/"):
            return rel[len("source/"):]
        return rel

    snap_dir = runs_dir(project_root, node_id, vid)
    os.makedirs(snap_dir, exist_ok=True)
    snap_files: List[Dict[str, str]] = []
    canonical_paths: List[str] = []
    # Snapshots must be IMMUTABLE — use full copies, never hardlinks, so an
    # in-place write to the source file (e.g. `open(p, "w")` truncates and
    # rewrites the same inode) cannot mutate the snapshot. View dirs are
    # safe to hardlink because they derive from snapshots, which are copies.
    for rel, src in abs_files:
        rel_in_version = in_version_path(rel)
        dst = os.path.join(snap_dir, rel_in_version)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        snap_files.append({"path": rel_in_version, "canonical": rel})
        canonical_paths.append(rel)

    # Build the version entry.
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    version_entry: Dict[str, Any] = {
        "id":              vid,
        "createdAt":       now_iso,
        "runId":           run_id,
        "files":           snap_files,
        "canonicalPaths":  canonical_paths,
        "thumbPath":       f"{WORKFLOW_DIRNAME}/{RUNS_DIRNAME}/{node_id}/{vid}/thumb.png",
        "label":           None,
        "pinned":          False,
        "branchedFrom":    None,
        "consumedVersions": consumed_versions,
        "compositions":    [],
        "activeCompositionId": None,
    }

    # Composition[0] auto-locked from current sub-asset pins.
    composition_entry: Dict[str, Any] = {
        "id":                cid,
        "createdAt":         now_iso,
        "consumedSubVersions": dict(sub_asset_pins),
        "subAssetMounts":    dict(sub_asset_mounts),
        "thumbPath":         f"{WORKFLOW_DIRNAME}/{RUNS_DIRNAME}/{node_id}/{vid}/compositions/{cid}/thumb.png",
        "label":             None,
        "pinned":            False,
        "degraded":          False,
    }
    version_entry["compositions"].append(composition_entry)
    version_entry["activeCompositionId"] = cid

    # Persist meta.json for both (so an outside tool can read).
    os.makedirs(runs_dir(project_root, node_id, vid, cid), exist_ok=True)
    with open(os.path.join(snap_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(version_entry, f, indent=2)
    with open(os.path.join(runs_dir(project_root, node_id, vid, cid), "meta.json"),
              "w", encoding="utf-8") as f:
        json.dump(composition_entry, f, indent=2)

    # Mutate the node.
    versions = node.setdefault("versions", [])
    versions.append(version_entry)
    node["activeVersionId"] = vid

    # Materialise view dir.
    materialise_view(project_root, node, version_entry, composition_entry,
                     sub_asset_pins=sub_asset_pins,
                     sub_asset_mounts=sub_asset_mounts)

    # Eviction (versions then per-version compositions).
    evict_versions(project_root, node, max_unpinned=max_unpinned_versions)
    for v in node.get("versions", []):
        evict_compositions(project_root, node, v, max_unpinned=max_unpinned_compositions)

    return version_entry


# ── View materialisation ───────────────────────────────────────────────────

def materialise_view(project_root: str, node: Dict[str, Any],
                     version: Dict[str, Any], composition: Dict[str, Any],
                     *, sub_asset_pins: Optional[Dict[str, str]] = None,
                     sub_asset_mounts: Optional[Dict[str, str]] = None,
                     resolve_sub_asset_files=None) -> str:
    """Build workflow/views/<nodeId>/<vid>/<compId>/ for this composition.

    Contains:
      • parent asset's own files at their canonical relative paths
        (hardlinked from runs/<nodeId>/<vid>/)
      • each sub-asset's files at its declared mountPath
        (hardlinked from runs/<subAssetId>/<subVid>/)

    `resolve_sub_asset_files` is an optional callback (sub_asset_id, sub_vid)
    → list of (rel, abs) so this module doesn't depend on workflow.json
    schema. If omitted, sub-asset materialisation is skipped (e.g. tests).
    """
    node_id = node.get("id")
    vdir = view_dir(project_root, node_id, version["id"], composition["id"])
    # Wipe + rebuild so the view always exactly reflects the composition.
    if os.path.isdir(vdir):
        shutil.rmtree(vdir, ignore_errors=True)
    os.makedirs(vdir, exist_ok=True)

    # Parent asset files — copy at their canonical relative path so HTML
    # imports under source/ continue to resolve when iframes load this dir.
    snap = runs_dir(project_root, node_id, version["id"])
    for fe in version.get("files") or []:
        rel = fe.get("path") if isinstance(fe, dict) else None
        canon = fe.get("canonical") if isinstance(fe, dict) else None
        if not rel: continue
        src = os.path.join(snap, rel)
        if not os.path.isfile(src): continue
        # Strip optional leading "source/" from canonical to root the view at
        # the same layout source/ has.
        if isinstance(canon, str) and canon:
            view_rel = canon[len("source/"):] if canon.startswith("source/") else canon
        else:
            view_rel = rel
        dst = os.path.join(vdir, view_rel)
        hardlink_or_copy(src, dst)

    # Sub-asset files.
    pins = sub_asset_pins or composition.get("consumedSubVersions") or {}
    mounts = sub_asset_mounts or composition.get("subAssetMounts") or {}
    if resolve_sub_asset_files and pins:
        for sub_id, sub_vid in pins.items():
            mount = mounts.get(sub_id) or ""
            mount = mount.strip("/")
            try:
                file_list = resolve_sub_asset_files(sub_id, sub_vid) or []
            except Exception:
                file_list = []
            for rel, src in file_list:
                # Place sub-asset file at <mount>/<rel> within the view.
                view_rel = os.path.join(mount, rel) if mount else rel
                dst = os.path.join(vdir, view_rel)
                if os.path.isfile(src):
                    hardlink_or_copy(src, dst)
    return vdir


def refresh_source_from_view(project_root: str, node: Dict[str, Any]) -> int:
    """Copy the active view dir of an asset into source/ at canonical paths.

    Used after revert / composition switch. Returns the file count.
    Only touches the asset's OWN canonicalPaths — sub-asset files are owned
    by their respective asset nodes and refreshed by their own active state.
    """
    active_vid = node.get("activeVersionId")
    if not active_vid: return 0
    version = next((v for v in (node.get("versions") or [])
                    if isinstance(v, dict) and v.get("id") == active_vid), None)
    if not version: return 0
    canonical = version.get("canonicalPaths") or []
    snap = runs_dir(project_root, node.get("id"), active_vid)
    n = 0
    for canon_rel in canonical:
        if not isinstance(canon_rel, str): continue
        # Find the matching file under snap. Use canonical-stripped-of-source/
        # to locate within version dir.
        rel_in_version = canon_rel[len("source/"):] if canon_rel.startswith("source/") else canon_rel
        src = os.path.join(snap, rel_in_version)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(project_root, canon_rel.lstrip("/"))
        # Copy (not hardlink) so a subsequent in-place edit of the live file
        # doesn't mutate the snapshot the user just reverted to.
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


# ── Eviction ───────────────────────────────────────────────────────────────

def _eviction_protected_version_ids(node: Dict[str, Any]) -> set:
    """Versions that must NOT be evicted: the active one + any referenced
    by another version's composition (… but compositions reference sub-asset
    versions on OTHER nodes; on this node only the active is protected by
    reference). Pinned status is checked separately."""
    out = set()
    av = node.get("activeVersionId")
    if av: out.add(av)
    return out


def evict_versions(project_root: str, node: Dict[str, Any], *,
                   max_unpinned: int = DEFAULT_MAX_UNPINNED_VERSIONS) -> List[str]:
    """Cap unpinned versions on this node. Returns evicted version ids.

    Active version + pinned versions never evicted. Eviction cascades to the
    version's compositions and view dirs.
    """
    versions = node.get("versions") or []
    if not versions: return []
    protected = _eviction_protected_version_ids(node)
    unpinned = [v for v in versions
                if isinstance(v, dict)
                and not v.get("pinned")
                and v.get("id") not in protected]
    overflow = len(unpinned) - max_unpinned
    if overflow <= 0: return []
    # Evict oldest first — versions are appended chronologically, so slice
    # from the front of the unpinned-in-order list.
    to_evict = unpinned[:overflow]
    evicted_ids: List[str] = []
    for v in to_evict:
        vid = v.get("id")
        if not vid: continue
        # Remove version + all its view dirs.
        _purge_version_dirs(project_root, node.get("id"), vid,
                            [c.get("id") for c in (v.get("compositions") or [])
                             if isinstance(c, dict) and c.get("id")])
        evicted_ids.append(vid)
    if evicted_ids:
        node["versions"] = [v for v in versions
                            if isinstance(v, dict) and v.get("id") not in set(evicted_ids)]
    return evicted_ids


def evict_compositions(project_root: str, node: Dict[str, Any],
                       version: Dict[str, Any], *,
                       max_unpinned: int = DEFAULT_MAX_UNPINNED_COMPOSITIONS) -> List[str]:
    """Cap unpinned compositions on a version. Active never evicted."""
    comps = version.get("compositions") or []
    if not comps: return []
    active_cid = version.get("activeCompositionId")
    unpinned = [c for c in comps
                if isinstance(c, dict)
                and not c.get("pinned")
                and c.get("id") != active_cid]
    overflow = len(unpinned) - max_unpinned
    if overflow <= 0: return []
    to_evict = unpinned[:overflow]
    evicted: List[str] = []
    for c in to_evict:
        cid = c.get("id")
        if not cid: continue
        _purge_composition_dirs(project_root, node.get("id"), version.get("id"), cid)
        evicted.append(cid)
    if evicted:
        version["compositions"] = [c for c in comps
                                   if isinstance(c, dict) and c.get("id") not in set(evicted)]
    return evicted


def _purge_version_dirs(project_root: str, node_id: str, version_id: str,
                        composition_ids: List[str]) -> None:
    """Remove a version's runs/ + views/ dirs (cascades to compositions)."""
    shutil.rmtree(runs_dir(project_root, node_id, version_id), ignore_errors=True)
    # View dirs are organised as views/<nodeId>/<vid>/<compId>/, so removing
    # the version-level dir cleans them all up.
    vdir_parent = os.path.join(project_root, WORKFLOW_DIRNAME, VIEWS_DIRNAME,
                               node_id, version_id)
    shutil.rmtree(vdir_parent, ignore_errors=True)


def _purge_composition_dirs(project_root: str, node_id: str,
                            version_id: str, composition_id: str) -> None:
    """Remove a single composition's runs/<…>/compositions/<…>/ + view dir."""
    shutil.rmtree(runs_dir(project_root, node_id, version_id, composition_id),
                  ignore_errors=True)
    shutil.rmtree(view_dir(project_root, node_id, version_id, composition_id),
                  ignore_errors=True)


# ── Migration ──────────────────────────────────────────────────────────────

def reconcile_orphan_versions(project_root: str, node: Dict[str, Any]) -> int:
    """Walk workflow/runs/<nodeId>/ on disk and append any version dirs that
    aren't already in node.versions[]. Returns the number of recovered
    versions. Idempotent — orphans only get added once.

    The orphan scenario: snapshot_asset successfully wrote bytes + dir, but
    a concurrent /__workflow POST stomped the appended versions[] entry
    back to a stale state. The dirs remain on disk; this helper recovers
    them so the picker UI shows them.

    Recovered versions are inserted in createdAt order (from meta.json
    inside each dir, falling back to dir mtime). The active version is
    NOT reset — that stays at whatever node already says.
    """
    nid = node.get("id")
    if not isinstance(nid, str): return 0
    runs_root = runs_dir(project_root, nid)
    if not os.path.isdir(runs_root): return 0
    known_vids = {(v.get("id") or "") for v in (node.get("versions") or [])
                  if isinstance(v, dict)}
    recovered = []
    for entry in os.scandir(runs_root):
        if not entry.is_dir(): continue
        vid = entry.name
        if vid in known_vids: continue
        # Try to load meta.json for a faithful version entry; else synthesize
        # a minimal one from filesystem inspection.
        meta_path = os.path.join(entry.path, "meta.json")
        version_entry: Optional[Dict[str, Any]] = None
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    v = json.load(f)
                if isinstance(v, dict) and v.get("id") == vid:
                    version_entry = v
            except Exception:
                pass
        if version_entry is None:
            # Synthesize from disk: walk the dir for files, build canonical
            # paths from "main/foo.png" → "source/main/foo.png" heuristic.
            files = []
            canonical = []
            for root, _, names in os.walk(entry.path):
                rel_root = os.path.relpath(root, entry.path)
                for name in names:
                    if name in ("meta.json", "thumb.png"): continue
                    if rel_root == ".":
                        rel = name
                    else:
                        rel = os.path.join(rel_root, name)
                    if rel.startswith("compositions" + os.sep): continue
                    files.append({"path": rel, "canonical": "source/" + rel})
                    canonical.append("source/" + rel)
            if not files: continue
            try:
                mtime = os.path.getmtime(entry.path)
                iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime))
            except Exception:
                iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            version_entry = {
                "id":                vid,
                "createdAt":         iso,
                "runId":             None,
                "files":             files,
                "canonicalPaths":    canonical,
                "thumbPath":         f"workflow/runs/{nid}/{vid}/thumb.png",
                "label":             "(recovered)",
                "pinned":            False,
                "branchedFrom":      None,
                "consumedVersions":  {},
                "compositions":      [],
                "activeCompositionId": None,
            }
        recovered.append(version_entry)
    if not recovered: return 0
    # Sort recovered + existing together by createdAt to keep the array
    # chronologically ordered.
    merged = (node.get("versions") or []) + recovered
    def _ts(v):
        iso = v.get("createdAt") if isinstance(v, dict) else ""
        try:
            import calendar as _cal
            return _cal.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))
        except Exception:
            return 0
    merged.sort(key=_ts)
    node["versions"] = merged
    return len(recovered)


def migrate_legacy_asset(project_root: str, node: Dict[str, Any],
                         current_sub_asset_pins: Optional[Dict[str, str]] = None,
                         ) -> bool:
    """Synthesize versions[0] + compositions[0] for a VERSIONABLE node that
    doesn't have them yet. Reads current files from disk. Returns True if
    the node was mutated.

    Covers all VERSIONABLE_KINDS: asset (declared paths), prototype (full
    source/ tree), design-system (full design-systems/<dsId>/ tree)."""
    if not is_versionable(node): return False
    if (node.get("versions") or []) and node.get("activeVersionId"):
        return False
    # Use unified file enumeration so prototype/design-system kinds work too.
    if node.get("kind") == "asset":
        files = asset_files(node)
    else:
        files = node_scope_files(project_root, node)
    if not files: return False
    # Only snapshot files that actually exist on disk — synthesizing a
    # version pointing at missing files would create a broken history.
    existing = [r for r in files if os.path.isfile(os.path.join(project_root, r))]
    if not existing: return False
    # Reuse snapshot — sets activeVersionId, etc.
    out = snapshot_asset(project_root, node,
                         consumed_versions=None,
                         sub_asset_pins=current_sub_asset_pins,
                         sub_asset_mounts=None,
                         run_id=None)
    return out is not None


# ── Sub-asset declaration resolution ───────────────────────────────────────

def resolve_sub_assets(workflow: Dict[str, Any], node_id: str,
                       manifest: Optional[Dict[str, Any]] = None,
                       ) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (sub_asset_pins, sub_asset_mounts) for an asset node.

    sub_asset_pins  — sub-asset node id → that node's current activeVersionId
    sub_asset_mounts — sub-asset node id → declared mount path in the parent
                       asset's view tree (from manifest.subAssetInputs[])

    Source of declaration: manifest.subAssetInputs[] (preferred). Without a
    manifest, returns empty maps — there's no safe way to infer mount paths.
    """
    pins: Dict[str, str] = {}
    mounts: Dict[str, str] = {}
    if not manifest: return pins, mounts
    decls = manifest.get("subAssetInputs")
    if not isinstance(decls, list): return pins, mounts
    nodes_by_id = {n.get("id"): n for n in (workflow.get("nodes") or [])
                   if isinstance(n, dict) and n.get("id")}
    for d in decls:
        if not isinstance(d, dict): continue
        sid = d.get("nodeId")
        mount = d.get("mountPath")
        if not isinstance(sid, str) or not sid: continue
        sub = nodes_by_id.get(sid)
        if not sub or not is_asset(sub): continue
        av = sub.get("activeVersionId")
        if isinstance(av, str) and av:
            pins[sid] = av
        if isinstance(mount, str) and mount:
            mounts[sid] = mount
    return pins, mounts


# ── Downstream-asset snapshot hook ─────────────────────────────────────────

def _auto_sub_assets_from_edges(workflow: Dict[str, Any], target_id: str,
                                 nodes_by_id: Optional[Dict[str, Dict[str, Any]]] = None,
                                 ) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Walk `target_id`'s incoming edges; for each upstream node whose kind
    is in VERSIONABLE_KINDS (asset/prototype/design-system), record its
    current activeVersionId as a sub-asset pin and derive a mount path from
    the upstream's canonical path.

    This is the fallback when no MANIFEST.json declares subAssetInputs[]
    — without it, compositions[].consumedSubVersions is permanently empty.
    """
    pins: Dict[str, str] = {}
    mounts: Dict[str, str] = {}
    if nodes_by_id is None:
        nodes_by_id = {n.get("id"): n for n in (workflow.get("nodes") or [])
                       if isinstance(n, dict) and n.get("id")}
    for e in (workflow.get("edges") or []):
        if not isinstance(e, dict): continue
        if (e.get("to") or "").split(".", 1)[0] != target_id: continue
        from_id = (e.get("from") or "").split(".", 1)[0]
        up = nodes_by_id.get(from_id)
        if not up: continue
        if up.get("kind") not in VERSIONABLE_KINDS: continue
        if up.get("kind") != "asset": continue   # only assets fit the sub-asset model
        av = up.get("activeVersionId")
        if isinstance(av, str) and av:
            pins[from_id] = av
        # Mount: parent directory of the upstream's canonical path, relative
        # to project root. Falls back to "_assets/<upstream_id>/" if path
        # missing. The view materialiser uses this as the prefix.
        rel_paths = asset_files(up)
        if rel_paths:
            mount = os.path.dirname(rel_paths[0])
            mounts[from_id] = mount.lstrip("/") or f"_assets/{from_id}"
        else:
            mounts[from_id] = f"_assets/{from_id}"
    return pins, mounts


def snapshot_changed_assets(project_root: str, workflow: Dict[str, Any],
                             changed_paths: Iterable[str],
                             run_id: Optional[str] = None,
                             ) -> List[Dict[str, Any]]:
    """File-watcher driven snapshotter. Given a batch of project-relative
    paths that just changed on disk, snapshot any VERSIONABLE node (asset,
    prototype, design-system) whose scope contains those paths.

    Matching:
      • asset         → exact path match against node.path / paths[]
      • prototype     → any change under source/  (everywhere in the tree)
      • design-system → any change under design-systems/<dsId>/

    Deduplicates by node (one snapshot per node per batch) and skips nodes
    whose latest version is already newer than the file's mtime (so back-to-
    back writes within the watcher debounce don't double-snap).

    Returns a list of {nodeId, versionId} for snapshots that were created.
    Mutates workflow in place when versions are appended.
    """
    out: List[Dict[str, Any]] = []
    if not changed_paths: return out
    nodes = workflow.get("nodes") or []
    nodes_by_id = {n.get("id"): n for n in nodes if isinstance(n, dict) and n.get("id")}

    # Index asset nodes by their declared paths (exact match).
    asset_by_path: Dict[str, Dict[str, Any]] = {}
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") != "asset": continue
        for rel in asset_files(n):
            asset_by_path.setdefault(rel.lstrip("/"), n)

    # Index prototype + design-system nodes by their scope root prefix.
    # Each entry: (prefix, node). Match by `rel == prefix or rel.startswith(prefix + "/")`.
    scope_nodes: List[Tuple[str, Dict[str, Any]]] = []
    for n in nodes:
        if not isinstance(n, dict): continue
        if n.get("kind") in ("prototype", "design-system"):
            for s in kind_scope_dirs(n):
                scope_nodes.append((s.rstrip("/"), n))

    # Collect affected nodes; dedupe.
    affected: Dict[str, Dict[str, Any]] = {}
    for raw in changed_paths:
        if not isinstance(raw, str): continue
        rel = raw.lstrip("/")
        # Exact-path match (asset).
        node = asset_by_path.get(rel)
        if node:
            nid = node.get("id")
            if nid and nid not in affected:
                affected[nid] = node
        # Prefix match (prototype / design-system).
        for prefix, snode in scope_nodes:
            if rel == prefix or rel.startswith(prefix + "/"):
                # Skip files OWNED by the scope's machinery (workflow/ runs
                # would create infinite recursion if we ever versioned files
                # under workflow/runs).
                if rel.startswith(WORKFLOW_DIRNAME + "/"):
                    continue
                nid = snode.get("id")
                if nid and nid not in affected:
                    affected[nid] = snode

    if not affected: return out

    # Snapshot each affected node — but only if the file is genuinely newer
    # than the node's latest version.
    import time as _t
    def _file_mtime(node):
        """Latest mtime across files this node's snapshot covers. Uses the
        unified node_scope_files so it works for prototype/design-system too
        (where asset_files() returns empty)."""
        latest = 0.0
        rels = node_scope_files(project_root, node)
        for rel in rels:
            ap = os.path.join(project_root, rel.lstrip("/"))
            try:
                m = os.path.getmtime(ap)
                if m > latest: latest = m
            except OSError:
                continue
        return latest

    def _latest_version_created_at(node):
        vs = node.get("versions") or []
        if not vs: return 0.0
        # versions[] is append-ordered; last one is newest.
        last = vs[-1]
        if not isinstance(last, dict): return 0.0
        iso = last.get("createdAt") or ""
        try:
            # createdAt is "YYYY-MM-DDTHH:MM:SSZ" — UTC. Use calendar.timegm
            # which interprets the struct_time as UTC; time.mktime would
            # treat it as local and shift by the timezone offset (causing
            # the dedup to fail anywhere outside UTC).
            import calendar as _cal
            return _cal.timegm(_t.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))
        except Exception:
            return 0.0

    # v3.2 — Scope-level quiescence debounce. For multi-file scopes
    # (prototype, design-system) the agent's edit burst typically writes
    # 5–20 files spread across several seconds (HTML, then CSS, then a few
    # images, then a tweak). The watcher's 0.25s debounce was way too short
    # — every file write past 250ms became its own snapshot, producing the
    # "21 versions in 5 minutes" pattern the user reported.
    #
    # New rule for prototype/design-system: don't snapshot until the LATEST
    # mtime in the scope is at least SCOPE_QUIESCENCE_SEC old (default 15s).
    # If the latest mtime is more recent, the burst is still in flight —
    # record the node in `_PENDING_SCOPE_SNAPSHOTS` so a subsequent watcher
    # tick can re-attempt the snapshot even if no NEW file writes arrived
    # in the interim. Without this, a burst that ends without further edits
    # would never get snapshotted at all.
    # Single-file asset nodes keep the original behaviour (the 1s clock-
    # skew check below) because a single file's snapshot is already 1:1
    # with the write event.
    SCOPE_QUIESCENCE_SEC = 15.0
    now_wall = _t.time()
    project_key = os.path.abspath(project_root)
    project_pending = _PENDING_SCOPE_SNAPSHOTS.setdefault(project_key, {})
    for nid, node in affected.items():
        file_mtime = _file_mtime(node)
        if file_mtime <= 0:
            project_pending.pop(nid, None)
            continue
        kind = node.get("kind")
        if kind in ("prototype", "design-system"):
            if (now_wall - file_mtime) < SCOPE_QUIESCENCE_SEC:
                # Scope is still being actively written — defer until quiet.
                # Record the deferral so the watcher's next tick checks it
                # again. We store the file_mtime we observed so the watcher
                # can detect when quiescence is satisfied without needing
                # to know anything about scope internals.
                project_pending[nid] = file_mtime
                continue
            # We're past quiescence; clear the deferral marker.
            project_pending.pop(nid, None)
        last_v_ts = _latest_version_created_at(node)
        # Skip if the file hasn't been touched since the last version was
        # taken (with a 1s slop for clock skew between filesystem and snap
        # timestamps).
        if last_v_ts > 0 and file_mtime <= last_v_ts + 1.0:
            continue

        # Compute non-asset upstream lineage from this asset's edges.
        consumed: Dict[str, Dict[str, str]] = {}
        for e in (workflow.get("edges") or []):
            if (e.get("to") or "").split(".", 1)[0] != nid: continue
            from_id = (e.get("from") or "").split(".", 1)[0]
            up = nodes_by_id.get(from_id)
            if not up: continue
            if up.get("kind") == "asset": continue
            text = up.get("output") if isinstance(up.get("output"), str) else (up.get("text") or "")
            consumed[from_id] = {"outputHash": hash_text(text)}

        # v3.1 — auto-derive sub-asset pins from edges when no manifest exists.
        sub_pins, sub_mounts = _auto_sub_assets_from_edges(workflow, nid, nodes_by_id)
        try:
            v = snapshot_asset(project_root, node,
                               consumed_versions=consumed,
                               sub_asset_pins=sub_pins or None,
                               sub_asset_mounts=sub_mounts or None,
                               run_id=run_id)
            if v:
                out.append({"nodeId": nid, "versionId": v["id"]})
        except Exception:
            continue
    return out


def snapshot_asset_by_output_path(project_root: str, workflow: Dict[str, Any],
                                   output_path: str,
                                   run_id: Optional[str] = None,
                                   ) -> Optional[Dict[str, Any]]:
    """Find a workflow asset node whose declared path (or paths[]) matches
    `output_path` and snapshot it. Used by file-writing endpoints that
    don't go through the normal node-run dispatch (e.g. /__asset_generate).

    Returns `{nodeId, versionId}` if a snapshot was taken, else None.
    """
    if not isinstance(output_path, str) or not output_path:
        return None
    rel = output_path.lstrip("/")
    nodes = workflow.get("nodes") or []
    # Match on exact path or membership in paths[].
    target = None
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") != "asset": continue
        if (n.get("path") or "").strip().lstrip("/") == rel:
            target = n; break
        ps = n.get("paths")
        if isinstance(ps, list) and any(
            isinstance(p, str) and p.strip().lstrip("/") == rel for p in ps
        ):
            target = n; break
    if not target:
        return None
    # Build non-asset upstream lineage from this asset's own incoming edges.
    nodes_by_id = {n.get("id"): n for n in nodes if isinstance(n, dict) and n.get("id")}
    consumed: Dict[str, Dict[str, str]] = {}
    for e in (workflow.get("edges") or []):
        if (e.get("to") or "").split(".", 1)[0] != target.get("id"): continue
        from_id = (e.get("from") or "").split(".", 1)[0]
        up = nodes_by_id.get(from_id)
        if not up: continue
        if up.get("kind") == "asset": continue
        text = up.get("output") if isinstance(up.get("output"), str) else (up.get("text") or "")
        consumed[from_id] = {"outputHash": hash_text(text)}
    # v3.1 — auto-derive sub-asset pins from edges.
    sub_pins, sub_mounts = _auto_sub_assets_from_edges(workflow, target.get("id"))
    v = snapshot_asset(project_root, target,
                       consumed_versions=consumed,
                       sub_asset_pins=sub_pins or None,
                       sub_asset_mounts=sub_mounts or None,
                       run_id=run_id)
    if not v: return None
    return {"nodeId": target.get("id"), "versionId": v["id"]}


def snapshot_downstream_assets(project_root: str, workflow: Dict[str, Any],
                               producer_node_id: str) -> List[Dict[str, Any]]:
    """After a producer node completes, walk outgoing edges to asset nodes
    and snapshot each one. Mutates workflow.nodes in place.

    Returns a list of (asset_node_id, version_id) tuples for the snapshots
    that were created. Best-effort: a failure on one asset does not abort
    the others.
    """
    created: List[Dict[str, Any]] = []
    nodes_by_id = {n.get("id"): n for n in (workflow.get("nodes") or [])
                   if isinstance(n, dict) and n.get("id")}
    producer = nodes_by_id.get(producer_node_id)
    if not producer: return created

    # Find downstream versionable nodes. v3.2 — was `is_asset(n)`, which
    # silently skipped prototype + design-system children even though both
    # are in VERSIONABLE_KINDS. Producer-completion (
    # ds-builder, etc.) snapshots now cover all three kinds, matching the
    # file-watcher's `snapshot_changed_assets` coverage.
    downstream_asset_ids: List[str] = []
    for e in (workflow.get("edges") or []):
        from_ref = (e.get("from") or "")
        if from_ref.split(".", 1)[0] != producer_node_id: continue
        to_id = (e.get("to") or "").split(".", 1)[0]
        n = nodes_by_id.get(to_id)
        if n and is_versionable(n):
            downstream_asset_ids.append(to_id)

    if not downstream_asset_ids: return created

    def _non_asset_upstream_of(target_id: str) -> Dict[str, Dict[str, str]]:
        """Walk incoming edges of `target_id`, returning a non-asset lineage
        map. Asset upstream is excluded — it belongs in compositions."""
        out: Dict[str, Dict[str, str]] = {}
        for e in (workflow.get("edges") or []):
            to_ref = (e.get("to") or "")
            if to_ref.split(".", 1)[0] != target_id: continue
            from_id = (e.get("from") or "").split(".", 1)[0]
            up = nodes_by_id.get(from_id)
            if not up: continue
            if up.get("kind") == "asset": continue
            text = up.get("output")
            if not isinstance(text, str):
                text = up.get("text") if isinstance(up.get("text"), str) else ""
            out[from_id] = {"outputHash": hash_text(text)}
        return out

    # Resolver for sub-asset files (used by view materialisation).
    def _resolve(sub_id: str, sub_vid: str) -> List[Tuple[str, str]]:
        sub = nodes_by_id.get(sub_id)
        if not sub: return []
        snap = runs_dir(project_root, sub_id, sub_vid)
        out: List[Tuple[str, str]] = []
        if not os.path.isdir(snap): return out
        for root, _, files in os.walk(snap):
            for name in files:
                if name in ("meta.json",): continue
                p = os.path.join(root, name)
                rel = os.path.relpath(p, snap)
                # Skip composition meta files.
                if rel.startswith("compositions" + os.sep):
                    continue
                out.append((rel, p))
        return out

    for asset_id in downstream_asset_ids:
        node = nodes_by_id[asset_id]
        try:
            # Look for a manifest the producer might have left for this asset.
            # Search in: source/ root, and any declared asset path's parent.
            search_dirs = []
            for rel in asset_files(node):
                search_dirs.append(os.path.dirname(rel))
            search_dirs.append("source")
            manifest = read_manifest(project_root, search_dirs)
            sub_pins, sub_mounts = resolve_sub_assets(workflow, asset_id, manifest)
            # v3.1 — fallback when no manifest: walk THIS asset's upstream
            # edges and treat any asset upstream as a sub-asset. Without
            # this, compositions[].consumedSubVersions is always empty
            # because no subagent emits MANIFEST.json today.
            if not sub_pins:
                sub_pins, sub_mounts = _auto_sub_assets_from_edges(
                    workflow, asset_id, nodes_by_id)
            # Non-asset lineage: walk this asset's own incoming edges so the
            # producer itself + any sibling non-asset feeders appear in
            # consumedVersions. Asset upstream goes into compositions.
            consumed_versions = _non_asset_upstream_of(asset_id)
            v = snapshot_asset(
                project_root, node,
                consumed_versions=consumed_versions,
                sub_asset_pins=sub_pins,
                sub_asset_mounts=sub_mounts,
                run_id=producer.get("runId") or producer.get("runRunId"),
                manifest=manifest,
            )
            if v:
                # Rerun view materialisation so sub-asset bytes get linked
                # in too (snapshot_asset's own call passed no resolver).
                active_comp = next(
                    (c for c in (v.get("compositions") or [])
                     if isinstance(c, dict) and c.get("id") == v.get("activeCompositionId")),
                    None,
                )
                if active_comp:
                    materialise_view(project_root, node, v, active_comp,
                                     sub_asset_pins=sub_pins,
                                     sub_asset_mounts=sub_mounts,
                                     resolve_sub_asset_files=_resolve)
                # Refresh source/ from the new view so the canvas iframe
                # sees a consistent live state.
                refresh_source_from_view(project_root, node)
                created.append({"nodeId": asset_id, "versionId": v["id"]})
        except Exception:
            # Best-effort: keep going.
            continue
    return created
