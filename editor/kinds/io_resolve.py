"""Contract-driven edge I/O resolver for the workflow agent dispatch.

This module replaces the two hand-written ``if/elif`` chains that used to live
inline in ``serve.py``'s ``/run`` handler (one building the upstream
``<context>`` block, one building the ``<output-destinations>`` block). Both
walks are now keyed on each peer node's ``io`` contract (``KIND_IO`` in
``kinds/registry.py``), so a new node kind needs only a ``KIND_IO`` entry — the
running agent adapts to it automatically.

The daemon owns the filesystem / web-fetch primitives, so the caller passes
them in via ``ctx`` (a plain dict of callables + state) rather than this module
importing the giant ``serve.py``.

``ctx`` keys:
    project_root      str
    safe_join         callable(project_root, rel) -> abspath (raises ValueError)
    web_fetch         callable(url) -> {"body": ...}
    web_extract_text  callable(body, cap=int) -> (title, text)
    list_local_fonts  callable(project_root) -> [{"family":..., "ds":...}, ...]
    proto_slug        str   (the running node's prototype/branch slug)
"""
from __future__ import annotations

import json
import os
import re

from kinds.registry import kind_contract, ASSET_KIND_AUTHORING, MEDIA_MODEL_AUTHORING


# ── small helpers ───────────────────────────────────────────────────────────

def _label(node):
    return node.get("title") or node.get("name") or node.get("id")


def _io(node):
    """The resolved io contract block for a node (honours per-id overrides)."""
    c = kind_contract(node.get("kind"), node.get("id"))
    return (c or {}).get("io") or {}


def _edge_port(ref: str) -> str:
    """`nodeId.port` -> `port` (everything after the last dot)."""
    i = (ref or "").rfind(".")
    return ref[i + 1:] if i >= 0 else ""


def _pick(entries, port):
    """Pick the io entry matching `port`; fall back to the first entry."""
    if not entries:
        return None
    for e in entries:
        if e.get("port") == port:
            return e
    return entries[0]


def _resolve_tpl(tpl: str, node, proto_slug: str) -> str:
    return (tpl or "").replace("{prototype}", proto_slug) \
                      .replace("{branch}", proto_slug) \
                      .replace("{variant}", node.get("variant") or "") \
                      .replace("{dsId}", node.get("dsId") or "main") \
                      .replace("{id}", node.get("id") or "")


# ── upstream resolvers: provider node -> context chunk (str) or None ─────────

def _r_text(up, prov, ctx):
    args = prov.get("resolveArgs") or {}
    fields = args.get("fields") or ["text"]
    txt = ""
    for f in fields:
        v = up.get(f)
        if isinstance(v, str) and v.strip():
            txt = v.strip()
            break
    if not txt:
        return None
    suffix = f" ({up.get('kind')})" if args.get("headerKind") else ""
    return f"### {_label(up)}{suffix}\n{txt}"


def _r_folder(up, prov, ctx):
    rel = (up.get("path") or "").lstrip("/")
    try:
        fp = ctx["safe_join"](ctx["project_root"], rel)
    except ValueError:
        return None
    if os.path.isfile(fp):
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                return f"### {_label(up)} (file: {rel})\n{fh.read()}"
        except OSError:
            return None
    return None


def _r_webfetch(up, prov, ctx):
    web_url = str(up.get("url") or "").strip()
    if not re.match(r"^https?://", web_url, re.I):
        return None
    cap = (prov.get("resolveArgs") or {}).get("cap", 16000)
    try:
        page = ctx["web_fetch"](web_url)
        title, text = ctx["web_extract_text"](page["body"], cap=cap)
        head = f"### {_label(up)} (web page: {web_url}" + (f" — {title}" if title else "") + ")"
        return head + "\n" + (text or "(no readable text)")
    except Exception as e:  # noqa: BLE001 — degrade to a note, never block the run
        return f"### {_label(up)} (web page: {web_url})\n(unreachable: {e})"


def _r_baked(up, prov, ctx):
    """A baked container (composer / vector / spline / formatted-text) wired
    directly into an agent. Contributes its baked artifact as context — this
    closes the gap where wiring one of these straight into an agent gave the
    running agent nothing."""
    kind = up.get("kind")
    bp = (up.get("bakedPath") or "").lstrip("/")
    if not bp:
        return (f"### {_label(up)} ({kind})\n"
                "(not baked yet — click Bake on this node so its content is "
                "written to disk and available here. No content until then.)")
    try:
        fp = ctx["safe_join"](ctx["project_root"], bp)
    except ValueError:
        return None
    if not os.path.isfile(fp):
        return f"### {_label(up)} ({kind}: {bp})\n(baked file missing on disk)"
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as fh:
            return f"### {_label(up)} ({kind}, baked: {bp})\n{fh.read()}"
    except OSError:
        return None


def _r_asset(up, prov, ctx):
    path = (up.get("path") or "").strip()
    if not path:
        return None
    ak = up.get("assetKind") or "file"
    return f"### {_label(up)} (asset)\nFile: {path} ({ak})"


def _r_typed(up, prov, ctx):
    flavor = (prov.get("resolveArgs") or {}).get("flavor")
    if flavor == "palette":
        sw = ", ".join(f"{s.get('name')}={s.get('value')}"
                       for s in (up.get("swatches") or []) if isinstance(s, dict))
        return f"### {_label(up)} (color palette)\n{sw}" if sw else None
    if flavor == "typography":
        lv = ", ".join(f"{l.get('name')} {l.get('size')}px/{l.get('weight')}"
                       for l in (up.get("levels") or []) if isinstance(l, dict))
        head = f"### {_label(up)} (typography)\nsans={up.get('fontFamily') or ''}, mono={up.get('monoFamily') or ''}"
        return head + (f". Scale: {lv}" if lv else "")
    # Composable spec nodes (effect / position / trigger / layer) — the node's
    # `spec` JSON IS the payload; hand the agent the literal spec so it can
    # reason about (or replace) it.
    if flavor in ("effect", "position", "trigger", "layer"):
        spec = up.get("spec")
        try:
            body = json.dumps(spec, ensure_ascii=False) if spec is not None else "{}"
        except (TypeError, ValueError):
            body = "{}"
        return f"### {_label(up)} ({flavor} spec)\n{body}"
    return None


def _r_dsref(up, prov, ctx):
    ds_ref = up.get("dsId") or "main"
    fonts = [f["family"] for f in ctx["list_local_fonts"](ctx["project_root"]) if f.get("ds") == ds_ref]
    line = f"id={ds_ref}"
    if fonts:
        line += f". Local uploaded fonts (PREFER these): {', '.join(fonts)}"
    return f"### {_label(up)} (design system reference)\n{line}"


def _section_line(cn, ctx):
    """One bullet for a node contained inside a section frame. Faithful port of
    the legacy inline section walk — formatting kept byte-for-byte."""
    ck = cn.get("kind")
    clabel = cn.get("title") or cn.get("name") or cn.get("id")
    if ck in ("prompt", "skill"):
        ctxt = ((cn.get("output") if ck == "skill" else None) or cn.get("text") or "")
        ctxt = ctxt.strip() if isinstance(ctxt, str) else ""
        return f"- {clabel}:\n{ctxt}" if ctxt else None
    if ck == "color-palette":
        sw = ", ".join(f"{s.get('name')}={s.get('value')}"
                       for s in (cn.get("swatches") or []) if isinstance(s, dict))
        return f"- color palette '{clabel}': {sw}" if sw else None
    if ck == "typography":
        lv = ", ".join(f"{l.get('name')} {l.get('size')}px/{l.get('weight')}"
                       for l in (cn.get("levels") or []) if isinstance(l, dict))
        return (f"- typography '{clabel}': sans={cn.get('fontFamily') or ''}, "
                f"mono={cn.get('monoFamily') or ''}" + (f". Scale: {lv}" if lv else ""))
    if ck == "asset" and str(cn.get("path") or "").startswith("source/"):
        return f"- asset ({cn.get('assetKind') or 'file'}): {cn.get('path')}"
    if ck == "design-system":
        ds_ref = cn.get("dsId") or "main"
        fonts = [f["family"] for f in ctx["list_local_fonts"](ctx["project_root"]) if f.get("ds") == ds_ref]
        return ("- design system reference: id=" + ds_ref
                + (f". Local uploaded fonts (PREFER these): {', '.join(fonts)}" if fonts else ""))
    if ck == "folder" and str(cn.get("path") or "").strip():
        return f"- folder: {cn.get('path')}"
    return None


def _r_section(up, prov, ctx):
    """A section frame wired upstream: the combination of every node whose
    CENTER sits inside the frame rect (same containment rule as the editor's
    group-drag)."""
    wf = ctx["wf"]
    sx0 = float(up.get("x") or 0); sy0 = float(up.get("y") or 0)
    sx1 = sx0 + float(up.get("w") or 880); sy1 = sy0 + float(up.get("h") or 560)
    parts = []
    for cn in (wf.get("nodes") or []):
        if not cn or cn.get("id") == up.get("id") or cn.get("kind") == "section":
            continue
        cx = float(cn.get("x") or 0) + float(cn.get("w") or 280) / 2
        cy = float(cn.get("y") or 0) + float(cn.get("h") or 200) / 2
        if not (sx0 <= cx <= sx1 and sy0 <= cy <= sy1):
            continue
        line = _section_line(cn, ctx)
        if line:
            parts.append(line)
    if not parts:
        return None
    return (f"### {_label(up)} (section — combined contents of every node inside)\n"
            + "\n".join(parts))


_UP_RESOLVERS = {
    "text": _r_text,
    "folder": _r_folder,
    "webfetch": _r_webfetch,
    "bakedFile": _r_baked,
    "assetFile": _r_asset,
    "typed": _r_typed,
    "dsRef": _r_dsref,
    "sectionBundle": _r_section,
}


# ── public: upstream walk ────────────────────────────────────────────────────

def resolve_upstream(wf, node_id, ctx) -> str:
    """Walk incoming edges and build the agent's <context> blob, keyed on each
    upstream node's io.provides contract."""
    ctx = dict(ctx); ctx["wf"] = wf
    nodes_by_id = ctx["nodes_by_id"]
    chunks = []
    for e in (wf.get("edges") or []):
        to_ref = (e.get("to") or "")
        if to_ref.split(".", 1)[0] != node_id:
            continue
        up = nodes_by_id.get((e.get("from") or "").split(".", 1)[0])
        if not up:
            continue
        prov = _pick((_io(up).get("provides") or []), _edge_port(e.get("from") or ""))
        if not prov:
            continue
        fn = _UP_RESOLVERS.get(prov.get("resolve"))
        if not fn:
            continue
        chunk = fn(up, prov, ctx)
        if chunk:
            chunks.append(chunk)
    return "\n\n".join(chunks)


# ── downstream instructors: consumer node -> instruction (str) or None ───────

def _section_grid_instr(node_id, dn):
    """Build the sectionWrite instruction from the declared `authoring` contract
    (single source of truth in registry._SECTION_AUTHORING), injecting the live
    canvas rect + this section's node id. Falls back to a minimal line if the
    contract somehow lacks authoring (the import-time check forbids that)."""
    sx = float(dn.get("x") or 0); sy = float(dn.get("y") or 0)
    sw = float(dn.get("w") or 880); sh = float(dn.get("h") or 560)
    dlabel = _label(dn)
    rect = f"“{dlabel}” — canvas rect x={sx:.0f} y={sy:.0f} w={sw:.0f} h={sh:.0f}"
    accepts = _io(dn).get("accepts") or []
    sw_accept = next((a for a in accepts if a.get("ingest") == "sectionWrite"), None)
    authoring = (sw_accept or {}).get("authoring") or ""
    if authoring:
        body = authoring.replace("{rect}", rect).replace("{id}", str(node_id))
        return "- " + body
    return (f"- Generate INTO the section frame {rect}. Register each output as an asset node "
            f"inside that rect via POST /__workflow/node/{node_id}/commit addNodes:[…].")


def resolve_downstream(wf, node_id, node, ctx) -> str:
    """Walk outgoing edges and build the agent's <output-destinations> blob,
    keyed on each downstream node's io.accepts contract."""
    nodes_by_id = ctx["nodes_by_id"]
    proto_slug = ctx.get("proto_slug") or node.get("prototype") or node.get("branch") or "main"
    targets = []
    for e in (wf.get("edges") or []):
        from_ref = (e.get("from") or "")
        if from_ref.split(".", 1)[0] != node_id:
            continue
        dn = nodes_by_id.get((e.get("to") or "").split(".", 1)[0])
        if not dn:
            continue
        dkind = dn.get("kind")
        dlabel = _label(dn)
        dpath = (dn.get("path") or "").lstrip("/")
        accepts = _io(dn).get("accepts") or []

        # Section frame: generate INTO it (verbatim layout contract).
        if dkind == "section":
            targets.append(_section_grid_instr(node_id, dn))
            continue

        # Agent wired INTO a complex node = EDIT it. The agent rewrites the
        # node's canonical JSON, which the editor re-imports live.
        edit = next((a for a in accepts if a.get("ingest") == "editTarget"), None)
        if edit:
            resolved = _resolve_tpl(edit.get("canonical") or "", dn, proto_slug)
            authoring = edit.get("authoring")
            if authoring:
                # The contract carries the target's schema + production modes, so the
                # agent produces VALID content for this node instead of a generic asset.
                targets.append(
                    f"- WIRED TARGET — the {dkind} node “{dlabel}” (canonical file `{resolved}`).\n  "
                    + _resolve_tpl(authoring, dn, proto_slug))
            else:
                targets.append(
                    f"- EDIT the {dkind} node “{dlabel}”: write its canonical source file "
                    f"`{resolved}` (a JSON document describing the node's contents — read the "
                    f"existing file first, then write the modified JSON back). The editor "
                    f"re-imports this file automatically, so your changes appear live on the "
                    f"canvas. Edit this exact path; do NOT write a sibling file.")
            continue

        # Asset destination: write the file the asset node points at. The
        # assetKind tells the agent what format to produce.
        aw = next((a for a in accepts if a.get("ingest") == "assetWrite"), None)
        if aw and dpath:
            ak = dn.get("assetKind") or "file"
            # Prefer the node's MEDIUM (generating media-model id, e.g. "shader",
            # "viz", "threejs") over the storage assetKind ("html") — many
            # Pathway-B media models all store as html but expect a specific kind
            # of result. mediaModel contract wins; else fall back to assetKind.
            mm = dn.get("mediaModel")
            medium = MEDIA_MODEL_AUTHORING.get(mm) if mm else None
            medium_key = mm if medium else ak
            if not medium:
                medium = ASSET_KIND_AUTHORING.get(ak)
            line = f"- Write your {medium_key} output to `{dpath}` (wired to asset node “{dlabel}”)."
            if medium:
                line += "\n  " + _resolve_tpl(medium, dn, proto_slug)
            targets.append(line)
            continue

        fw = next((a for a in accepts if a.get("ingest") == "folderWrite"), None)
        if fw and dpath:
            targets.append(f"- Write outputs into `{dpath}` (wired to folder node “{dlabel}”).")
            continue

        # Fallback: a downstream kind with a registry outputsRoot expects its
        # inputs there (e.g. design-system, agent per-id drawers).
        try:
            c = kind_contract(dkind, dn.get("id"))
            root = c.get("outputsRoot") if c else None
        except Exception:  # noqa: BLE001
            root = None
        if root:
            targets.append(
                f"- Feed the `{dlabel}` node ({dkind}); it expects its inputs under "
                f"`{_resolve_tpl(root, dn, proto_slug)}`.")

    if not targets:
        return ""
    return ("This node is wired to the following OUTPUT destinations — "
            "write your results there so the canvas reflects them:\n" + "\n".join(targets))
