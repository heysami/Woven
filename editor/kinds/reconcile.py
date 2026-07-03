"""editor/kinds/reconcile.py - drift detection + auto-heal.

Walks the project on demand (invoked from /__kinds/reconcile and on
every /__workflow GET) and returns a list of drifts plus a per-node
lineage manifest.

Two classes of drift:

  AUTO_HEALABLE - silently resolved on next refresh:
    ORPHAN_VARIANT      - folder under producer's outputsRoot has no node
    LYING_STATUS        - node claims queued but completion satisfied (or vice versa)
    PHANTOM_DECISION    - DECISION points at a node that doesn't exist (self-resolves after orphan promote)

  MANUAL_HEAL - surfaces a Heal button, no silent action:
    UNHANDLED_OUTPUT    - consumer has unrouted upstream files
    ABANDONED_STAGING   - *_staging/ folder exists with no completing commit

Auto-heal applies its proposed mutations through the same /commit
contract so the validator + folder convention all apply uniformly.
"""
import json
import os
import re

from .registry import KINDS, kind_contract
from . import versioning as _vsn


# ── Drift types ─────────────────────────────────────────────────────────
ORPHAN_VARIANT     = "ORPHAN_VARIANT"
LYING_STATUS       = "LYING_STATUS"
PHANTOM_DECISION   = "PHANTOM_DECISION"
UNHANDLED_OUTPUT   = "UNHANDLED_OUTPUT"
ABANDONED_STAGING  = "ABANDONED_STAGING"
COHERENCE_NOT_RUN  = "COHERENCE_NOT_RUN"
DATA_DRIFT         = "DATA_DRIFT"      # any block-severity entry in COHERENCE_REPORT.json
KIND_MIGRATION     = "KIND_MIGRATION"  # node's kind disagrees with registry's declared kind for that id
ORPHAN_ASSET_NO_PROTOTYPE_EDGE = "ORPHAN_ASSET_NO_PROTOTYPE_EDGE"  # v3.1 - asset has no edge to prototype
ORPHAN_PROTOTYPE_FOLDER        = "ORPHAN_PROTOTYPE_FOLDER"        # v3.2 - source/<slug>/index.html on disk, no Prototype node
PROTOTYPE_FOLDER_SETTLE        = "PROTOTYPE_FOLDER_SETTLE"        # v3.9 - eager pending Prototype node; index.html now landed → flip to done
PROTOTYPE_FOLDER_ABANDON       = "PROTOTYPE_FOLDER_ABANDON"       # v3.9 - eager pending Prototype node whose folder lost all artifacts → remove


def _load_workflow(project_root):
    p = os.path.join(project_root, "workflow", "workflow.json")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _scan_producer_folders(project_root, kind_name, contract):
    """For openEnded producer kinds (ds-brainstorm, iterator-remix), scan
    the parent of outputsRoot and yield (variant_id, full_path) for each
    candidate. Used by orphan detection.

    Supports both the new folder convention (`_ds_brainstorm/{variant}/index.html`)
    AND the legacy flat layout (`_ds_brainstorm/{variant}.html`) - so projects
    that haven't yet migrated still get orphan detection. The migration
    script normalizes to folder layout later."""
    tmpl = contract.get("outputsRoot")
    if not tmpl: return []
    if "{variant}" not in tmpl: return []
    parent_tmpl = tmpl.split("{variant}", 1)[0].rstrip("/")
    parent_path = parent_tmpl.replace("{prototype}", "main").replace("{branch}", "main")
    full_parent = os.path.join(project_root, parent_path.lstrip("/"))
    if not os.path.isdir(full_parent):
        return []
    out = []
    for entry in os.scandir(full_parent):
        name = entry.name
        if name.startswith("."): continue
        if entry.is_dir():
            # New folder layout - accept any non-suffixed subfolder.
            # Skip *_assets / *_staging which are companion dirs, not variants.
            if name.endswith("_assets") or name.endswith("_staging"):
                continue
            out.append((name, entry.path))
        elif entry.is_file() and name.endswith(".html"):
            # Legacy flat layout - a.html, b.html, d.html each = one variant.
            variant_id = name[:-len(".html")]
            out.append((variant_id, entry.path))
    return out


def _detect_orphan_variants(workflow, project_root, drifts):
    """For every kind with openEnded=True and a {variant}-templated
    outputsRoot, check the filesystem for folders that have no
    corresponding node. Emit ORPHAN_VARIANT drift per missing node."""
    nodes_by_id = {n.get("id"): n for n in (workflow.get("nodes") or []) if isinstance(n, dict)}
    for kind_name, contract in KINDS.items():
        if not contract.get("openEnded"): continue
        if not contract.get("outputsRoot"): continue
        if "{variant}" not in contract.get("outputsRoot", ""): continue
        # Find existing variants represented in the workflow
        existing_variants = {
            (n.get("variant") or "")
            for n in (workflow.get("nodes") or [])
            if isinstance(n, dict) and n.get("kind") == kind_name and n.get("variant")
        }
        # Scan disk
        for variant_id, candidate_path in _scan_producer_folders(project_root, kind_name, contract):
            if variant_id in existing_variants:
                continue
            # Resolve the artifact:
            #   - If candidate_path is a directory (new layout): look for index.html
            #   - If candidate_path is a file (legacy flat): the file IS the artifact
            artifact = None
            if os.path.isdir(candidate_path):
                for cand in ("index.html", f"{variant_id}.html"):
                    p = os.path.join(candidate_path, cand)
                    if os.path.isfile(p):
                        artifact = p
                        break
            elif os.path.isfile(candidate_path):
                artifact = candidate_path
            if not artifact:
                continue
            # Try to extract variant-spec
            spec = {}
            try:
                with open(artifact, "r", encoding="utf-8") as f:
                    html = f.read()
                m = re.search(r'<script[^>]+id=["\']variant-spec["\'][^>]*>(.*?)</script>',
                              html, re.S | re.I)
                if m:
                    spec = json.loads(m.group(1).strip())
            except Exception:
                pass
            drifts.append({
                "type":     ORPHAN_VARIANT,
                "kind":     kind_name,
                "variant":  variant_id,
                "folder":   os.path.relpath(candidate_path, project_root),
                "artifact": os.path.relpath(artifact, project_root),
                "spec":     spec,
                "class":    "auto",
                "suggest":  f"create {kind_name} node for variant {variant_id!r} with spec from {artifact}",
            })


def _detect_lying_status(workflow, project_root, drifts):
    """A node claims runStatus done/queued that disagrees with disk reality."""
    nodes = (workflow.get("nodes") or [])
    for n in nodes:
        if not isinstance(n, dict): continue
        kind = n.get("kind")
        if not kind: continue
        # v2.50 - DO NOT touch agent-kind nodes. They own their own lifecycle:
        # the subprocess completion hook flips runStatus on exit, and the
        # editor's client-side polling state machine (WorkflowAgentNode) drives
        # the downstream target upgrade (clear the asset's "Generating…"
        # pending state + promote asset/html → prototype on done+file-exists).
        # If the reconciler flips an agent to "done" out-of-band, the client
        # reloads, sees "done", and EARLY-RETURNS before running settleTargets
        # - stranding the asset at "Generating…" even though the file is on
        # disk. That's the stuck-prototype bug. Agent status is the client's
        # job, not the reconciler's. (The client also self-heals an orphaned
        # agent whose runId is gone after a daemon restart.)
        if kind == "agent": continue
        contract = kind_contract(kind, n.get("id"))
        if not contract: continue
        # Only check kinds that have outputsRoot (the others are user-driven
        # or have no disk artifact to check against)
        if not contract.get("outputsRoot"): continue
        # Skip kinds we can't autodetect completeness for (no completion requires
        # or only freeform requirements).
        requires = (contract.get("completion") or {}).get("requires") or []
        file_reqs = [r for r in requires if isinstance(r, str) and r.startswith("files:")]
        if not file_reqs: continue
        # Compute the "actual" status by re-running the file checks
        from . import validate as _v
        outputs_root_full = _v._resolve_path_template(
            contract.get("outputsRoot"), n, project_root)
        if not outputs_root_full: continue
        actual_satisfied = True
        for req in file_reqs:
            spec = req[len("files:"):].strip()
            if outputs_root_full:
                rel_outputs_root = contract.get("outputsRoot").replace("{prototype}", "main").replace("{branch}", "main").replace(
                    "{variant}", n.get("variant") or "").replace("{dsId}", n.get("dsId") or "main").rstrip("/")
                spec = spec.replace("outputsRoot", rel_outputs_root)
            lower = spec.lower()
            if " exists" in lower:
                rel = spec.split(" ", 1)[0].strip()
                full = os.path.join(project_root, rel)
                if not os.path.exists(full):
                    actual_satisfied = False
                    break
                if "non-empty" in lower and os.path.isfile(full) and os.path.getsize(full) == 0:
                    actual_satisfied = False
                    break
            elif " contains at least one " in lower:
                left, ext = spec.lower().split(" contains at least one ", 1)
                dir_path = os.path.join(project_root, spec[:len(left)].strip())
                ext = ext.strip().lstrip(".")
                import glob
                if not (os.path.isdir(dir_path) and glob.glob(os.path.join(dir_path, f"*.{ext}"))):
                    actual_satisfied = False
                    break
        claimed = n.get("runStatus") or "queued"
        if actual_satisfied and claimed == "queued":
            drifts.append({
                "type":     LYING_STATUS,
                "nodeId":   n.get("id"),
                "kind":     kind,
                "claimed":  claimed,
                "actual":   "done",
                "class":    "auto",
                "suggest":  f"flip {n.get('id')} runStatus to done - files exist on disk",
            })
        elif (not actual_satisfied) and claimed == "done":
            drifts.append({
                "type":     LYING_STATUS,
                "nodeId":   n.get("id"),
                "kind":     kind,
                "claimed":  claimed,
                "actual":   "queued",
                "class":    "auto",
                "suggest":  f"flip {n.get('id')} runStatus to queued - required files absent",
            })


def _detect_phantom_decisions(workflow, project_root, drifts):
    """DECISION_*.json files reference a value that doesn't appear as a
    variant on any node. Self-resolves once orphan-variant auto-heal runs."""
    nodes = workflow.get("nodes") or []
    for entry in os.scandir(project_root):
        if not entry.is_file(): continue
        if not entry.name.startswith("DECISION_"): continue
        if not entry.name.endswith(".json"): continue
        try:
            with open(entry.path, "r", encoding="utf-8") as f:
                dec = json.load(f)
        except Exception:
            continue
        values = dec.get("values") or ([dec.get("value")] if dec.get("value") else [])
        if not values: continue
        # Heuristic: if the decision id ends with _ds_pick, the values are
        # ds-brainstorm variant ids; if _remix_pick, iterator-remix.
        dec_id = dec.get("id", "")
        kind_hint = None
        if "ds_pick" in dec_id: kind_hint = "ds-brainstorm"
        elif "remix_pick" in dec_id: kind_hint = "iterator-remix"
        if not kind_hint:
            continue
        existing = {
            (n.get("variant") or "")
            for n in nodes
            if isinstance(n, dict) and n.get("kind") == kind_hint
        }
        for v in values:
            if v and v not in existing:
                drifts.append({
                    "type":      PHANTOM_DECISION,
                    "decision":  entry.name,
                    "value":     v,
                    "kindHint":  kind_hint,
                    "class":     "auto",
                    "suggest":   "auto-resolves once ORPHAN_VARIANT for this value is healed",
                })


def _detect_unhandled_outputs(workflow, project_root, drifts):
    """For consumer kinds (design-system, iterator-remix), walk the upstream
    folder and emit UNHANDLED_OUTPUT for any file no rule matches."""
    from . import validate as _v
    # Find consumer nodes that should be checking
    for n in (workflow.get("nodes") or []):
        if not isinstance(n, dict): continue
        contract = kind_contract(n.get("kind"), n.get("id"))
        if not contract: continue
        cf = contract.get("consumeFrom")
        if not cf: continue
        # Determine upstream folder. For design-system, source = picked variant
        # - resolve via DECISION_cp_ds_pick.json if it points at one.
        upstream = None
        src_tmpl = cf.get("source") or ""
        if "{picked.outputsRoot}" in src_tmpl:
            dec_path = os.path.join(project_root, "DECISION_cp_ds_pick.json")
            if os.path.isfile(dec_path):
                try:
                    with open(dec_path) as f: dec = json.load(f)
                    picked = (dec.get("values") or [dec.get("value")])[0] if (dec.get("values") or dec.get("value")) else None
                    if picked:
                        # Assume ds-brainstorm; reuse its outputsRoot
                        ds_contract = KINDS.get("ds-brainstorm") or {}
                        ds_tmpl = ds_contract.get("outputsRoot") or ""
                        upstream = os.path.join(project_root,
                            ds_tmpl.replace("{prototype}", "main").replace("{branch}", "main")
                                   .replace("{variant}", picked)
                                   .rstrip("/"))
                except Exception:
                    pass
        if not upstream:
            # Skip - we can't resolve the upstream without more context.
            continue
        viols = _v.validate_consume(n, upstream, project_root)
        for v in viols:
            drifts.append({
                "type":         UNHANDLED_OUTPUT,
                "nodeId":       n.get("id"),
                "kind":         n.get("kind"),
                "file":         v.get("file"),
                "policy":       v.get("policy"),
                "severity":     v.get("severity", "reject"),
                "class":        "manual" if v.get("severity") != "warn" else "auto",
                "suggest":      f"route {v.get('file')} per consumeFrom rules, or extend the contract",
            })


def _detect_abandoned_staging(workflow, project_root, drifts):
    """*_staging folders that exist on disk indicate an interrupted
    commit. The user should inspect."""
    src_root = os.path.join(project_root, "source")
    if not os.path.isdir(src_root): return
    for dirpath, dirnames, filenames in os.walk(src_root):
        for d in list(dirnames):
            if d.endswith("_staging") or d.endswith(".staging"):
                full = os.path.join(dirpath, d)
                drifts.append({
                    "type":     ABANDONED_STAGING,
                    "folder":   os.path.relpath(full, project_root),
                    "class":    "manual",
                    "suggest":  "inspect staging folder; delete or rename to canonical name",
                })
                dirnames.remove(d)


def _detect_kind_migration(workflow, project_root, drifts):
    """Detect nodes whose `kind` disagrees with the registry's declared kind
    for that id. v2.50 - when bs_html_* / bp_prd_* / etc. migrate from
    skill·llm to agent kind in the scaffolder, existing projects' workflow.json
    keeps the old kind. This drift surfaces those so they can auto-heal.

    The signal: the per-id override declares an outputsRoot AND a completion
    contract that only makes sense for one dispatch shape (agent). If the
    node's current kind != the implied kind, migrate.

    Currently auto-heals known kind transitions:
      skill → agent  (for ids whose per-id override has `outputsRoot` set)
    """
    nodes = workflow.get("nodes") or []
    # Heuristic: a node id with a per-id override that includes `outputsRoot`
    # AND a completion.requires referencing files is meant to be agent kind.
    # If the node's current kind is `skill`, propose migration.
    agent_overrides = (KINDS.get("agent") or {}).get("perIdOverrides") or {}
    for n in nodes:
        if not isinstance(n, dict): continue
        nid = n.get("id")
        if not nid: continue
        override = agent_overrides.get(nid)
        if not override: continue
        if not override.get("outputsRoot"): continue
        current_kind = n.get("kind")
        if current_kind == "agent": continue   # already correct
        if current_kind not in ("skill", "prompt"): continue  # don't touch unknown kinds
        drifts.append({
            "type":       KIND_MIGRATION,
            "nodeId":     nid,
            "fromKind":   current_kind,
            "toKind":     "agent",
            "outputsRoot": override.get("outputsRoot"),
            "class":      "auto",
            "suggest":    f"migrate {nid} from {current_kind!r} to 'agent' per registry's per-id override",
        })


def _detect_coherence(workflow, project_root, drifts):
    """Coherence-pass drift checks (Subagent 11 - see coherence-auditor.md):

      • COHERENCE_NOT_RUN - all generation stages are done but
        COHERENCE_REPORT.json doesn't exist yet. Manual-class - the user
        decides whether to dispatch the audit now or skip it.

      • DATA_DRIFT - COHERENCE_REPORT.json exists and contains
        block-severity findings. Manual-class - block findings always
        need a human choice (Retry / Patch / Accept-override).
    """
    nodes = workflow.get("nodes") or []
    # The Coherence Pass applies once "prototype-shaped output exists on
    # disk." Two triggers, OR-ed:
    #   (a) all canonical generation nodes (bs_html_*, br_remix_*) report done - the
    #       clean-pipeline path; OR
    #   (b) the project has a data.js + ≥2 HTML pages under source/<branch>/ - the
    #       legacy-or-out-of-band path (covers super where bs_html_* still show
    #       queued because their outputs landed at pre-folder-convention paths).
    # The reconciler can't tell from workflow.json alone whether generation
    # actually completed; trigger (b) catches projects whose prototype was
    # built before the registry contracts existed.
    gen_nodes = [n for n in nodes
                 if isinstance(n, dict) and (n.get("id", "").startswith("bs_html_")
                                              or n.get("id", "").startswith("br_remix_"))]
    all_done = bool(gen_nodes) and all((n.get("runStatus") or "queued") == "done" for n in gen_nodes)
    # Trigger (b): prototype-shaped output on disk?
    legacy_prototype = False
    src_root = os.path.join(project_root, "source")
    if os.path.isdir(src_root):
        for entry in os.scandir(src_root):
            if not entry.is_dir(): continue
            branch_dir = entry.path
            data_js = os.path.join(branch_dir, "data.js")
            if not os.path.isfile(data_js): continue
            # Count top-level .html files (excluding _ds_brainstorm, _pages, etc.)
            html_count = 0
            for e in os.scandir(branch_dir):
                if e.is_file() and e.name.endswith(".html") and not e.name.startswith("_"):
                    html_count += 1
            if html_count >= 2:
                legacy_prototype = True
                break
    has_output = all_done or legacy_prototype
    if not has_output:
        return   # No prototype-shaped output yet - Coherence doesn't apply.
    # Repurpose all_done downstream for the report check
    all_done = has_output
    report_path = os.path.join(project_root, "source", "main", "COHERENCE_REPORT.json")
    # Try other branches if main doesn't fit
    if not os.path.isfile(report_path):
        # Glob source/*/COHERENCE_REPORT.json
        src_root = os.path.join(project_root, "source")
        if os.path.isdir(src_root):
            for entry in os.scandir(src_root):
                if entry.is_dir():
                    cand = os.path.join(entry.path, "COHERENCE_REPORT.json")
                    if os.path.isfile(cand):
                        report_path = cand
                        break

    if all_done and not os.path.isfile(report_path):
        drifts.append({
            "type":    COHERENCE_NOT_RUN,
            "class":   "manual",
            "suggest": ("dispatch Subagent 11 (Coherence) via the Task tool to audit "
                        "data + chrome + asset coherence; see "
                        "editor/.claude/agents/coherence-auditor.md"),
        })
        return

    if os.path.isfile(report_path):
        try:
            with open(report_path, "r") as f:
                report = json.load(f)
        except Exception:
            return
        findings = report.get("findings") or []
        block = [f for f in findings if f.get("severity") == "block"]
        if block:
            for f in block[:10]:   # cap surfaced drifts
                drifts.append({
                    "type":      DATA_DRIFT,
                    "lint":      f.get("lint"),
                    "rule":      f.get("rule"),
                    "surface":   f.get("surface"),
                    "entity":    f.get("entity"),
                    "expected":  f.get("expected"),
                    "found":     f.get("found"),
                    "class":     "manual",
                    "suggest":   ("Retry the generator with the finding fed back, OR "
                                  "Patch the page to match the model, OR "
                                  "Accept-override (recorded as waived in DECISION_cp_coherence.json)"),
                })


# v3.5 - `_detect_premature_stage` deleted. It mapped onboarding stage
# letters (A/B/C/.../J) to bp_*_build / bp_prd_* / bs_html_* / etc. node id
# prefixes for the guided-onboarding flow. Both the flow and the bp_*
# preambles are gone; nothing writes `.onboarding-pending` anymore, so this
# detector had no inputs to act on. Removed wholesale.


_VISUAL_ASSET_KINDS = ("image", "svg", "video", "audio", "3d", "shader")
_SOURCE_WRITE_ASSET_KINDS = ("html", "html-set", "markdown", "text")


def _asset_target_port(assetKind: str) -> str:
    """Pick which prototype port an asset of a given kind should wire to:
       visual-assets for images/SVG/etc., source-write for HTML/markdown/etc.
       Default to visual-assets for anything we don't recognise (safer than
       source-write, which is meant for tree-write producers)."""
    if assetKind in _SOURCE_WRITE_ASSET_KINDS: return "source-write"
    return "visual-assets"


def _detect_orphan_asset_no_prototype_edge(workflow, project_root, drifts):
    """v4.0 - auto-wire an asset to a prototype ONLY when there is an EXPLICIT
    relationship between them. An asset belongs to a prototype when it was
    exposed FROM that prototype (`asset.boundTo.node` points at the prototype)
    or it is listed in that prototype's `exposedAssets[]` (by id or path).

    The pre-v4.0 rule wired ANY unwired asset to the prototype whenever exactly
    one prototype existed - so a standalone asset the user created (never
    associated with the prototype) got force-wired, and the edge re-appeared
    every time the user deleted it. It also did nothing with 2+ prototypes.
    Keying off the explicit binding fixes both: unrelated assets are left
    alone, and each exposed asset re-wires to ITS prototype regardless of how
    many prototypes exist.

    Routing branches by assetKind:
      • image/svg/video/audio/3d/shader → prototype.visual-assets
      • html/html-set/markdown/text      → prototype.source-write
    """
    nodes = workflow.get("nodes") or []
    prototypes = [n for n in nodes if isinstance(n, dict) and n.get("kind") == "prototype"]
    if not prototypes:
        return
    proto_ids = {p.get("id") for p in prototypes if isinstance(p.get("id"), str)}
    # Map exposed asset id / path → owning prototype id. Entries may be plain
    # path strings or {id, path, intent} dicts (both shapes exist in the wild).
    exposed_id_to_proto, exposed_path_to_proto = {}, {}
    for p in prototypes:
        pid = p.get("id")
        for entry in (p.get("exposedAssets") or []):
            if isinstance(entry, str):
                exposed_path_to_proto.setdefault(entry, pid)
            elif isinstance(entry, dict):
                if isinstance(entry.get("id"), str):   exposed_id_to_proto.setdefault(entry["id"], pid)
                if isinstance(entry.get("path"), str): exposed_path_to_proto.setdefault(entry["path"], pid)
    edges = workflow.get("edges") or []
    assets = [n for n in nodes if isinstance(n, dict) and n.get("kind") == "asset"]
    for a in assets:
        aid = a.get("id")
        if not isinstance(aid, str): continue
        # Which prototype, if any, does this asset explicitly belong to?
        bound = a.get("boundTo")
        bound_node = bound.get("node") if isinstance(bound, dict) else None
        target_proto = None
        if bound_node in proto_ids:
            target_proto = bound_node
        elif aid in exposed_id_to_proto:
            target_proto = exposed_id_to_proto[aid]
        elif isinstance(a.get("path"), str) and a.get("path") in exposed_path_to_proto:
            target_proto = exposed_path_to_proto[a["path"]]
        if not target_proto:
            continue   # no explicit prototype relationship → never auto-wire
        target_port = _asset_target_port(a.get("assetKind") or "image")
        # Already wired to ANY port on its prototype (either direction)?
        wired = any(
            (e.get("from") or "").split(".", 1)[0] == aid
            and (e.get("to") or "").split(".", 1)[0] == target_proto
            for e in edges if isinstance(e, dict)
        ) or any(
            (e.get("to") or "").split(".", 1)[0] == aid
            and (e.get("from") or "").split(".", 1)[0] == target_proto
            for e in edges if isinstance(e, dict)
        )
        if wired: continue
        drifts.append({
            "type": ORPHAN_ASSET_NO_PROTOTYPE_EDGE,
            "class": "auto",
            "assetNodeId": aid,
            "prototypeNodeId": target_proto,
            "targetPort": target_port,
            "summary": f"asset {aid!r} ({a.get('assetKind') or '?'}) not wired to its "
                       f"prototype {target_proto!r}.{target_port}",
        })


def _autoheal_orphan_asset_no_prototype_edge(workflow, drift):
    """Wire `<assetNodeId>.out → <prototypeNodeId>.<targetPort>` and append
    the asset to the prototype's exposedAssets[]. targetPort comes from the
    drift (branched by assetKind). Idempotent."""
    aid = drift.get("assetNodeId")
    pid = drift.get("prototypeNodeId")
    port = drift.get("targetPort") or "visual-assets"
    if not isinstance(aid, str) or not isinstance(pid, str): return False
    edges = workflow.setdefault("edges", [])
    # Re-check inside the heal to avoid TOCTOU duplicates.
    for e in edges:
        if not isinstance(e, dict): continue
        if ((e.get("from") or "").split(".", 1)[0] == aid
            and (e.get("to") or "").split(".", 1)[0] == pid):
            return False
    edges.append({"from": f"{aid}.out", "to": f"{pid}.{port}"})
    # Update prototype.exposedAssets[].
    nodes = workflow.get("nodes") or []
    proto = next((n for n in nodes if isinstance(n, dict) and n.get("id") == pid), None)
    asset = next((n for n in nodes if isinstance(n, dict) and n.get("id") == aid), None)
    if proto and asset:
        exposed = proto.setdefault("exposedAssets", [])
        if not isinstance(exposed, list):
            exposed = []
            proto["exposedAssets"] = exposed
        if not any(isinstance(x, dict) and x.get("id") == aid for x in exposed):
            exposed.append({
                "id":     aid,
                "path":   asset.get("path") or "",
                "intent": (asset.get("title") or "").strip(),
            })
    return True


def _autoheal_orphan_variant(workflow, drift, project_root):
    """For an ORPHAN_VARIANT drift, append a new node + asset child to
    workflow.json and wire it into the kind's existing checkpoint if
    present. Returns True if mutation applied, False if the node already
    exists (idempotent).

    The new node id is built from the kind contract's `idTemplate`
    (substituting {variant}). Kinds without an idTemplate are not
    auto-healed - we don't guess the canonical id pattern from the
    kind name (that's the "list of names" anti-pattern). Adding a new
    openEnded kind to the registry with a clear idTemplate is the ONLY
    code change needed to extend auto-heal coverage."""
    kind_name = drift.get("kind")
    variant_id = drift.get("variant")
    if not kind_name or not variant_id: return False
    contract = KINDS.get(kind_name) or {}
    id_template = contract.get("idTemplate")
    if not id_template:
        # No declared id pattern - refuse to guess. Reconciler still
        # reports the drift; user can heal manually by adding the node.
        return False
    new_node_id = id_template.replace("{variant}", variant_id)
    nodes = workflow.get("nodes") or []
    # Idempotency - already healed?
    if any(isinstance(n, dict) and n.get("id") == new_node_id for n in nodes):
        return False
    # Compute placement: stack below existing siblings of the same kind.
    siblings = [n for n in nodes
                if isinstance(n, dict) and n.get("kind") == kind_name]
    if siblings:
        # Same column as the rightmost-bottommost sibling.
        x = max(n.get("x", 0) for n in siblings)
        y = max(n.get("y", 0) for n in siblings) + 280
    else:
        x, y = 1200, 0

    # Try to extract the variant-spec script tag for richer initial state.
    spec = drift.get("spec") or {}

    new_node = {
        "id":         new_node_id,
        "kind":       kind_name,
        "x":          x,
        "y":          y,
        "w":          320,
        "h":          220,
        "runStatus":  "done",          # The artifact already exists - truthful.
        "title":      f"DS variant {variant_id.upper()}" if kind_name == "ds-brainstorm" else f"Variant {variant_id}",
        "variant":    variant_id,
        "spec":       spec,
        "specProjectedFrom": drift.get("artifact"),
        "commitRef":  {
            "at":              _now_iso(),
            "callerSessionId": "auto-heal",
            "requestId":       "reconciler",
        },
        "healedBy":   "reconciler.orphan-variant",
    }
    # Asset-child node holds the HTML file as a first-class object.
    asset_node_id = f"{new_node_id}_html"
    asset_node = {
        "id":        asset_node_id,
        "kind":      "asset",
        "x":         x + 380,
        "y":         y,
        "w":         320,
        "h":         200,
        "runStatus": "done",
        "title":     f"Variant {variant_id.upper()} sample",
        "assetKind": "html",
        "path":      drift.get("artifact"),
        "healedBy":  "reconciler.orphan-variant",
    }
    nodes.append(new_node)
    nodes.append(asset_node)
    workflow["nodes"] = nodes

    # Wire edges: new variant ─► its asset child, asset child ─► checkpoint (if declared by contract)
    edges = workflow.get("edges") or []
    edges.append({"from": f"{new_node_id}.out", "to": f"{asset_node_id}.in"})
    checkpoint_id = contract.get("checkpointNodeId")
    if checkpoint_id and any(isinstance(n, dict) and n.get("id") == checkpoint_id for n in nodes):
        edges.append({"from": f"{asset_node_id}.out", "to": f"{checkpoint_id}.in"})
    workflow["edges"] = edges
    return True


def _autoheal_kind_migration(workflow, drift):
    """Flip an existing node's kind to match the registry's per-id override.
    Drops skill-only fields (skill / provider / model) and ensures the
    agent-required fields (conversation) are present. Idempotent."""
    nid = drift.get("nodeId")
    to_kind = drift.get("toKind")
    if not nid or not to_kind: return False
    for n in (workflow.get("nodes") or []):
        if not isinstance(n, dict) or n.get("id") != nid:
            continue
        if n.get("kind") == to_kind:
            return False   # already migrated
        n["kind"] = to_kind
        if to_kind == "agent":
            # Drop skill-only fields
            for k in ("skill", "provider", "model"):
                n.pop(k, None)
            # Ensure conversation array exists (agent UI relies on it)
            if "conversation" not in n:
                n["conversation"] = []
            n["healedBy"] = "reconciler.kind-migration"
        return True
    return False


def _autoheal_lying_status(workflow, drift):
    """For a LYING_STATUS drift, flip runStatus to match disk reality.
    Returns True if applied."""
    node_id = drift.get("nodeId")
    actual = drift.get("actual")
    if not node_id or not actual: return False
    for n in (workflow.get("nodes") or []):
        if isinstance(n, dict) and n.get("id") == node_id:
            # v2.50 - never flip agent-kind status (it owns its lifecycle via
            # the subprocess completion hook + client polling). Belt-and-
            # suspenders: _detect_lying_status already skips agents so this
            # branch shouldn't be reached for them, but guard anyway.
            if n.get("kind") == "agent": return False
            if (n.get("runStatus") or "queued") != actual:
                n["runStatus"] = actual
                n["healedBy"] = "reconciler.lying-status"
                return True
            return False
    return False


# v3.5 - `_autoheal_premature_stage` deleted along with its detector.


def _now_iso():
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


# v3.2 - Prototype-folder auto-detection.
# When the agent (or a freeform Write) drops `source/<slug>/index.html` on
# disk, the user expects a live Prototype node to appear on the canvas
# WITHOUT dragging one in from the library. This detector + autoheal pair
# closes the loop: file watcher → reconcile → auto-mount.

# Subdirs that look like prototype folders but are project-level scratch
# space - never get a prototype node. Leading-underscore is the standing
# convention for scratch under source/.
_PROTOTYPE_FOLDER_SKIP_PREFIXES = ("_",)
_PROTOTYPE_FOLDER_SKIP_NAMES = {
    "_attachments", "_coherence", "_pages", "_remix", "_ds_brainstorm",
    "_staging", "_tmp", ".staging", ".trash",
}

# v3.9 - "is this folder a prototype build in progress?" A prototype's entry
# is index.html, but an agent typically writes it LAST (tokens → styles.css →
# data.js → component JS → finally index.html), or writes other pages first
# in a multi-HTML build. So a freshly-created slug folder can hold real build
# output for many seconds before index.html exists. We treat the presence of
# ANY html page, or the styles.css/data.js prototype skeleton, as the signal
# that a build is underway - enough to mount an eager "building" node so the
# canvas reflects what's happening instead of staying empty until the last
# write. Cheap, shallow-ish scan (root + one nested level).
# App-node editor tools bake their OWN deliverable into source/<slug>/ as
# `<prefix>-<nodeId>.html` - mm-composer (`mm-*.html`), material-lab
# (`material-*.html`), Hyperframes (`hyperframes-*.html`), gaussian-splat-3d (`gsplat-*.html`). Those are app-node
# outputs, NOT prototype pages. A folder holding only app-node bakes is an
# app-node build, and must NOT mount an eager "building" Prototype node - it
# would hang forever, since no index.html ever lands (the orphan-prototype-folder
# bug a user hit: an mm-composer build spawned a permanently-"Building…" node).
# If a new .html-baking app-node tool is added, list its prefix here.
_APP_NODE_HTML_PREFIXES = ("mm-", "material-", "hyperframes-", "gsplat-")


def _folder_has_prototype_artifacts(folder_path):
    try:
        for entry in os.scandir(folder_path):
            nm = entry.name
            if entry.is_file(follow_symlinks=False):
                low = nm.lower()
                if low.endswith((".html", ".htm")) and not low.startswith(_APP_NODE_HTML_PREFIXES):
                    return True
                if low in ("styles.css", "data.js"):
                    return True
            elif entry.is_dir(follow_symlinks=False) and not nm.startswith((".", "_")):
                # one level deep - multi-HTML builds drop pages/ first
                try:
                    for sub in os.scandir(entry.path):
                        sl = sub.name.lower()
                        if (sub.is_file(follow_symlinks=False)
                                and sl.endswith((".html", ".htm"))
                                and not sl.startswith(_APP_NODE_HTML_PREFIXES)):
                            return True
                except OSError:
                    pass
    except OSError:
        return False
    return False


def _detect_orphan_prototype_folder(workflow, project_root, drifts):
    """Keep the canvas in step with prototype folders on disk, across the
    whole build lifecycle:

      • `source/<slug>/index.html` exists, no Prototype node covers the slug
        → ORPHAN_PROTOTYPE_FOLDER (mount a done node). [v3.2]
      • `source/<slug>/` has build artifacts (any .html page, or the
        styles.css / data.js skeleton) but NO index.html yet, and no node
        covers the slug → ORPHAN_PROTOTYPE_FOLDER with `building: True`
        (mount an eager *pending* node so the canvas shows the build the
        moment it starts, complete with the "working" badge). [v3.9]
      • index.html has since landed for a slug already covered by an eager
        pending/running node → PROTOTYPE_FOLDER_SETTLE (flip it to done so
        the iframe renders and the badge stops). [v3.9]
      • an eager pending node whose folder vanished or lost every artifact
        (build abandoned before index.html) → PROTOTYPE_FOLDER_ABANDON
        (remove it, so we never leave a forever-"building" creature). [v3.9]

    This makes the per-prototype subfolder convention feel automatic: the
    agent writes `source/<slug>/...`, the user sees a Prototype node appear
    within ~1.5 s - now from the FIRST write, not the last."""
    source_dir = os.path.join(project_root, "source")
    if not os.path.isdir(source_dir):
        return
    nodes = workflow.get("nodes") or []
    # `prototype` is the canonical slug field (`branch` kept as fallback for
    # legacy nodes - see app.js prototypeSlugForNode). A node
    # carrying only `prototype` covers the slug just as fully as one carrying
    # only `branch`; reading only `branch` here causes the autoheal to spawn
    # duplicate prototype_<slug> siblings every reconcile tick, and worse, to
    # respawn one immediately after the user deletes it (the canonical-field
    # node still exists, so the slug stays "orphaned" in this detector's eyes).
    # v3.9 - also remember the covering node so we can settle / abandon eager
    # pending nodes (keyed by canonical slug → node).
    slug_to_node = {}
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") != "prototype":
            continue
        slug = (n.get("prototype") or n.get("branch") or "").strip()
        if slug and slug not in slug_to_node:
            slug_to_node[slug] = n
    existing_branches = set(slug_to_node.keys())

    # User-dismissed prototypes. Deleting a Prototype node from the canvas must
    # STICK - but this detector would re-mount it from the still-present
    # source/<slug>/ folder on the very next tick, making prototype deletion
    # (uniquely among node kinds) impossible. The frontend records the slug in
    # this project-level list on delete (app.js removeNode); honour it here by
    # never auto-mounting a dismissed slug. The folder on disk is untouched.
    dismissed = set()
    for s in (workflow.get("dismissedPrototypeSlugs") or []):
        if isinstance(s, str) and s.strip():
            dismissed.add(s.strip())

    def _index_for(folder_path):
        for cand in ("index.html", "index.htm"):
            p = os.path.join(folder_path, cand)
            if os.path.isfile(p):
                return os.path.relpath(p, project_root)
        return None

    try:
        entries = sorted(os.scandir(source_dir), key=lambda e: e.name)
    except OSError:
        return
    seen_slugs = set()
    for entry in entries:
        if not entry.is_dir(follow_symlinks=False):
            continue
        slug = entry.name
        seen_slugs.add(slug)
        if slug in _PROTOTYPE_FOLDER_SKIP_NAMES:
            continue
        if any(slug.startswith(p) for p in _PROTOTYPE_FOLDER_SKIP_PREFIXES):
            continue
        if slug in dismissed:
            # User deleted this prototype from the canvas - don't resurrect it.
            continue
        index_path = _index_for(entry.path)
        covering = slug_to_node.get(slug)
        if covering is not None:
            # Already on the canvas. The only thing left to do is settle an
            # eager pending node once its page finally lands.
            if (index_path
                    and covering.get("_building")
                    and covering.get("runStatus") in ("pending", "running")):
                drifts.append({
                    "type":     PROTOTYPE_FOLDER_SETTLE,
                    "class":    "auto",
                    "slug":     slug,
                    "nodeId":   covering.get("id"),
                    "indexPath": index_path,
                    "summary":  f"`source/{slug}/index.html` landed; settling the "
                                f"eager Prototype node to done.",
                })
            continue
        if index_path:
            drifts.append({
                "type":     ORPHAN_PROTOTYPE_FOLDER,
                "class":    "auto",
                "slug":     slug,
                "indexPath": index_path,
                "summary":  f"`source/{slug}/index.html` exists but no Prototype node "
                            f"covers slug={slug!r}; mounting one.",
            })
        elif _folder_has_prototype_artifacts(entry.path):
            drifts.append({
                "type":     ORPHAN_PROTOTYPE_FOLDER,
                "class":    "auto",
                "slug":     slug,
                "building": True,
                "summary":  f"`source/{slug}/` is being built (no index.html yet); "
                            f"mounting an eager 'building' Prototype node.",
            })

    # Abandon pass - an eager pending node whose folder disappeared or was
    # emptied of artifacts before producing index.html. Without this, a
    # cancelled / failed build would leave a node stuck "building" forever.
    for slug, covering in slug_to_node.items():
        if not covering.get("_building"):
            continue
        folder = os.path.join(source_dir, slug)
        gone = (slug not in seen_slugs) or (not os.path.isdir(folder))
        emptied = (not gone
                   and _index_for(folder) is None
                   and not _folder_has_prototype_artifacts(folder))
        if gone or emptied:
            drifts.append({
                "type":     PROTOTYPE_FOLDER_ABANDON,
                "class":    "auto",
                "slug":     slug,
                "nodeId":   covering.get("id"),
                "summary":  f"eager 'building' Prototype node for slug={slug!r} "
                            f"has no artifacts on disk; removing it.",
            })


def _autoheal_orphan_prototype_folder(workflow, drift):
    """Append a Prototype node anchored to `source/<slug>/`. Placement
    stacks new prototypes in a column on the right side of the canvas so
    they don't overlap with the agent / asset clusters typically growing
    on the left. Returns True if mutation applied; False if a sibling
    prototype with the same branch already exists (idempotent - TOCTOU
    guard against the same drift being applied twice in one tick)."""
    slug = (drift.get("slug") or "").strip()
    if not slug: return False
    nodes = workflow.get("nodes") or []
    # Idempotency. Same canonical-field rule as the detector - a node carrying
    # `prototype: <slug>` covers the slug just as fully as one carrying
    # `branch: <slug>`.
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") != "prototype":
            continue
        existing_slug = (n.get("prototype") or n.get("branch") or "").strip()
        if existing_slug == slug:
            return False
    # Placement: stack vertically below existing prototype siblings to keep
    # multi-prototype canvases tidy. If none yet, anchor at a comfortable
    # right-side default.
    siblings = [n for n in nodes
                if isinstance(n, dict) and n.get("kind") == "prototype"]
    if siblings:
        x = max(n.get("x", 0) for n in siblings)
        y = max(n.get("y", 0) for n in siblings) + 560
    else:
        x, y = 1600, 80
    new_id = f"prototype_{slug}"
    # Collision-safe id - if something already uses prototype_<slug>, append
    # a short suffix. Rare, but possible if the user manually added a node
    # with the same id without setting branch.
    base = new_id
    existing_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
    i = 2
    while new_id in existing_ids:
        new_id = f"{base}_{i}"
        i += 1
    # v3.2 - Default node size matches the prototype's natural viewport
    # aspect ratio (1440×900 → 16:10). The iframe scale-to-fit transform in
    # the frontend renders the prototype at its natural viewport size and
    # CSS-scales to fit the node body - but choosing a node size with the
    # same aspect means no letterbox. 720×482 = 16:10 (with +32 title bar
    # → 720×450 body region, which has the same 16:10 ratio as 1440×900).
    # v3.9 - eager "building" mount. The folder has artifacts but no
    # index.html yet, so render a pending node (the frontend shows a
    # "Building…" placeholder + the working badge) instead of a 404 iframe.
    # PROTOTYPE_FOLDER_SETTLE flips it to done once index.html lands.
    building = bool(drift.get("building"))
    node = {
        "id":         new_id,
        "kind":       "prototype",
        "branch":     slug,
        "x":          x,
        "y":          y,
        "w":          720,
        "h":          482,
        "viewport":   {"w": 1440, "h": 900},
        "runStatus":  "pending" if building else "done",
        "title":      (slug + " (building…)") if building else slug,
        "healedBy":   "reconciler.orphan-prototype-folder-building" if building
                      else "reconciler.orphan-prototype-folder",
        "commitRef":  {
            "at":              _now_iso(),
            "callerSessionId": "auto-heal",
            "requestId":       "reconciler",
        },
    }
    if building:
        node["_building"] = True
    nodes.append(node)
    workflow["nodes"] = nodes
    return True


def _autoheal_prototype_folder_settle(workflow, drift):
    """Flip an eager 'building' Prototype node to done now that its
    `index.html` has landed: clear the pending state + the _building marker
    so the frontend swaps the placeholder for the live iframe and the
    working badge stops. Idempotent - bails if the node is gone or already
    settled."""
    node_id = drift.get("nodeId")
    slug = (drift.get("slug") or "").strip()
    for n in workflow.get("nodes") or []:
        if not isinstance(n, dict) or n.get("kind") != "prototype":
            continue
        matches = (n.get("id") == node_id) if node_id else \
                  ((n.get("prototype") or n.get("branch") or "").strip() == slug)
        if not matches:
            continue
        if not n.get("_building") and n.get("runStatus") == "done":
            return False
        n["runStatus"] = "done"
        n.pop("_building", None)
        if n.get("title") == (slug + " (building…)"):
            n["title"] = slug
        return True
    return False


def _autoheal_prototype_folder_abandon(workflow, drift):
    """Remove an eager 'building' Prototype node whose folder produced no
    lasting artifacts (cancelled / failed build). Only ever removes nodes
    this reconciler mounted as eager-building - never user- or
    agent-authored prototype nodes. Idempotent."""
    node_id = drift.get("nodeId")
    slug = (drift.get("slug") or "").strip()
    nodes = workflow.get("nodes") or []
    keep = []
    removed = False
    removed_ids = set()
    for n in nodes:
        if (isinstance(n, dict) and n.get("kind") == "prototype"
                and n.get("_building")
                and ((n.get("id") == node_id) if node_id
                     else ((n.get("prototype") or n.get("branch") or "").strip() == slug))):
            removed = True
            removed_ids.add(n.get("id"))
            continue
        keep.append(n)
    if not removed:
        return False
    workflow["nodes"] = keep
    # Drop any edges touching the removed node so we don't strand connectors.
    edges = workflow.get("edges") or []
    workflow["edges"] = [e for e in edges
                         if (e.get("from") or "").split(".")[0] not in removed_ids
                         and (e.get("to") or "").split(".")[0] not in removed_ids]
    return True


def apply_auto_heals(project_root):
    """Run reconcile(), apply every class:"auto" drift, write the
    workflow.json back atomically. Returns a list of summaries of
    what got applied. Idempotent - calling twice in a row applies
    nothing the second time.

    This is what makes the canvas tell the truth WITHOUT a Heal click:
    when a ds-brainstorm subagent drops a new `_ds_brainstorm/d.html`
    on disk, the file watcher emits asset-changed; the watcher loop
    calls this function; auto-heal creates the bs_ds_d card + wires
    it into cp_ds_pick; the workflow.json write then fires
    workflow-changed; the canvas refreshes and shows the new card.
    All within ~1.5 s, no manual reload."""
    out = []
    report = reconcile(project_root)
    drifts = report.get("drifts") or []
    auto_drifts = [d for d in drifts if d.get("class") == "auto"]
    if not auto_drifts:
        return out

    # Load workflow.json (under no lock - caller serialises).
    wf_path = os.path.join(project_root, "workflow", "workflow.json")
    if not os.path.isfile(wf_path):
        return out
    try:
        with open(wf_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception:
        return out

    mutated = False
    for drift in auto_drifts:
        t = drift.get("type")
        applied = False
        try:
            if t == ORPHAN_VARIANT:
                applied = _autoheal_orphan_variant(workflow, drift, project_root)
            elif t == LYING_STATUS:
                applied = _autoheal_lying_status(workflow, drift)
            elif t == KIND_MIGRATION:
                applied = _autoheal_kind_migration(workflow, drift)
            elif t == ORPHAN_ASSET_NO_PROTOTYPE_EDGE:
                applied = _autoheal_orphan_asset_no_prototype_edge(workflow, drift)
            elif t == ORPHAN_PROTOTYPE_FOLDER:
                applied = _autoheal_orphan_prototype_folder(workflow, drift)
            elif t == PROTOTYPE_FOLDER_SETTLE:
                applied = _autoheal_prototype_folder_settle(workflow, drift)
            elif t == PROTOTYPE_FOLDER_ABANDON:
                applied = _autoheal_prototype_folder_abandon(workflow, drift)
            # PHANTOM_DECISION auto-resolves once ORPHAN_VARIANT runs (same loop).
            # COHERENCE_NOT_RUN is manual-class - never auto-heals.
        except Exception as e:
            out.append({"drift": t, "applied": False, "error": str(e)})
            continue
        if applied:
            mutated = True
            out.append({"drift": t, "applied": True,
                        "detail": {k: drift.get(k) for k in ("nodeId","variant","kind","stage","claimed","actual")
                                    if drift.get(k) is not None}})

    if mutated:
        try:
            with open(wf_path, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2)
        except Exception as e:
            out.append({"drift": "WRITE_BACK_FAILED", "applied": False, "error": str(e)})

    return out


def apply_versioning_migration(project_root):
    """Idempotently bring asset nodes' versions[] into sync with disk state.
    Two steps per asset node:
      1. If no versions exist yet AND the canonical file is on disk → synthesize v0.
      2. Walk workflow/runs/<nodeId>/ and append any orphan version dirs that
         aren't already in versions[] (recovers snapshots whose entries were
         stomped by a stale /__workflow POST race before v3.0 fixed it).

    Returns a list of {nodeId, action} entries describing what changed.
    """
    wf_path = os.path.join(project_root, "workflow", "workflow.json")
    if not os.path.isfile(wf_path):
        return []
    try:
        with open(wf_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception:
        return []
    nodes = workflow.get("nodes") or []
    actions = []
    for n in nodes:
        if not isinstance(n, dict): continue
        # v3.0 - versioning covers asset, prototype, design-system kinds.
        if not _vsn.is_versionable(n): continue
        try:
            if _vsn.migrate_legacy_asset(project_root, n):
                actions.append({"nodeId": n.get("id"), "action": "synthesize-v0"})
        except Exception:
            pass
        try:
            recovered = _vsn.reconcile_orphan_versions(project_root, n)
            if recovered > 0:
                actions.append({"nodeId": n.get("id"),
                                "action": "recover-orphans",
                                "count": recovered})
        except Exception:
            continue
    if actions:
        try:
            with open(wf_path, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2)
        except Exception:
            return []
    return actions


def reconcile(project_root):
    """Walk the project and return drift + lineage. Returns a dict:
       { "drifts": [...], "lineage": {...} }"""
    out = {"drifts": [], "lineage": {}}
    wf = _load_workflow(project_root)
    if not wf:
        return out
    drifts = out["drifts"]

    # Order matters slightly: detect orphans first so phantom-decision
    # checks see a more complete picture of "what variants exist."
    try: _detect_orphan_variants(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"orphan"})

    try: _detect_lying_status(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"status"})

    try: _detect_phantom_decisions(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"decision"})

    try: _detect_unhandled_outputs(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"unhandled"})

    try: _detect_abandoned_staging(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"staging"})

    try: _detect_coherence(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"coherence"})

    try: _detect_kind_migration(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"kind_migration"})

    try: _detect_orphan_asset_no_prototype_edge(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"orphan_asset_prototype"})

    # v3.2 - Detect source/<slug>/index.html with no Prototype node referencing
    # it. Must run BEFORE the asset-no-prototype-edge detector noticed nothing
    # to wire to (because there WAS no prototype yet); the autoheal in the
    # same loop creates the prototype, and the asset-edge detector will fire
    # again on the NEXT watcher tick to wire any unattached assets to it.
    try: _detect_orphan_prototype_folder(wf, project_root, drifts)
    except Exception as e: drifts.append({"type":"reconciler_error","detail":str(e),"phase":"orphan_prototype_folder"})

    # Compute summary counts
    out["summary"] = {
        "total": len(drifts),
        "autoHealable": len([d for d in drifts if d.get("class") == "auto"]),
        "manualHeal":   len([d for d in drifts if d.get("class") == "manual"]),
        "byType": {},
    }
    for d in drifts:
        t = d.get("type", "unknown")
        out["summary"]["byType"][t] = out["summary"]["byType"].get(t, 0) + 1

    return out
