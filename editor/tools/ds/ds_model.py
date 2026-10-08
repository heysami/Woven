#!/usr/bin/env python3
"""ds_model.py - load and validate a component design system (format v1).

Shared by build_ds.py (generator) and ds_check.py (checker). Spec:
docs/features/component-ds-format.md. Stdlib only, Python 3.9-safe.

The template grammar here MUST stay in step with the JS runtime
(editor/tools/ds/runtime/ds-runtime.src.js). Python only parses and renders
templates to VALIDATE them (single root, known names); the runtime is the one
real expander.
"""

import glob
import hashlib
import json
import os
import re
from html.parser import HTMLParser

FORMAT = 1
# Block `layer` groups the catalog and gallery and ranks CSS order; build/ds.css
# itself is ONE plain stylesheet (no CSS @layer).
LAYER_RANK = ["layout", "atom", "molecule", "organism", "pattern", "shell"]
BLOCK_DIRS = {"components": ("layout", "atom", "molecule", "organism"), "patterns": ("pattern",), "shells": ("shell",)}
PROP_TYPES = ("string", "number", "boolean", "enum", "list", "json")
SPEC_FIELDS = {"name", "title", "layer", "oneLine", "useWhen", "notForUseWhen", "replaces", "rootClass", "classRoots", "props",
               "slots", "contains", "events", "states", "copy", "a11y", "desc"}
PROP_FIELDS = {"type", "values", "required", "default", "desc"}
COPY_FIELDS = {"maxWords", "maxChars", "case"}
EXAMPLE_FIELDS = {"title", "props", "slots", "frame", "desc", "attrs"}
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
DYN = "dsdynamic0"                  # stands in for {{...}} when reading template structure
ENUM_COVERAGE_MAX = 20              # bigger enums (icon names) are not expected in examples
RESERVED = {"custom", "slot"}
PASSTHROUGH = {"id", "class", "style", "hidden", "title", "role", "tabindex", "lang", "dir"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
COLOR_LITERAL_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\s*\(")


def is_passthrough(attr):
    return attr in PASSTHROUGH or attr.startswith("data-") or attr.startswith("aria-")


class Finding(object):
    __slots__ = ("level", "code", "message", "file", "line")

    def __init__(self, level, code, message, file=None, line=None):
        self.level, self.code, self.message, self.file, self.line = level, code, message, file, line

    def as_dict(self):
        return {"level": self.level, "code": self.code, "message": self.message, "file": self.file, "line": self.line}

    def fmt(self, root=None):
        f = self.file or ""
        if root and f.startswith(root):
            f = os.path.relpath(f, root)
        loc = f + (":" + str(self.line) if self.line else "") if f else ""
        return (loc + ": " if loc else "") + self.level + " " + self.code + ": " + self.message


# ── template grammar ─────────────────────────────────────────────────────────
TAG_RE = re.compile(r"\{\{\s*([#/]?)([^}]*?)\s*\}\}")
ARG_RE = re.compile(r'"((?:[^"\\]|\\.)*)"|([A-Za-z_@][\w.\-]*)')
COND_RE = re.compile(r'^(.+?)\s*(==|!=)\s*"((?:[^"\\]|\\.)*)"\s*$')
EACH_RE = re.compile(r"^each\s+([\w.\-]+)\s+as\s+([A-Za-z_][\w\-]*)$")


class TemplateError(Exception):
    pass


def compile_template(src, name="template"):
    """Parse a template into nodes. Raises TemplateError on bad syntax."""
    root = {"t": "root", "body": []}
    stack = [root]
    cur = root["body"]
    pos = 0
    for m in TAG_RE.finditer(src):
        if m.start() > pos:
            cur.append({"t": "text", "v": src[pos:m.start()]})
        pos = m.end()
        sigil, body = m.group(1), m.group(2).strip()
        head = body.split()[0] if body.split() else ""
        if sigil == "#":
            if head == "if":
                c = body[2:].strip()
                cm = COND_RE.match(c)
                cond = {"path": cm.group(1).strip(), "op": cm.group(2), "lit": cm.group(3)} if cm else {"path": c}
                if not cond["path"]:
                    raise TemplateError(name + ": empty {{#if}}")
                n = {"t": "if", "cond": cond, "yes": [], "no": [], "else": False}
                cur.append(n)
                stack.append(n)
                cur = n["yes"]
            elif head == "each":
                em = EACH_RE.match(body)
                if not em:
                    raise TemplateError(name + ": bad each: " + body)
                n = {"t": "each", "path": em.group(1), "as": em.group(2), "body": []}
                cur.append(n)
                stack.append(n)
                cur = n["body"]
            else:
                raise TemplateError(name + ": unknown block {{#" + head + "}}")
        elif sigil == "/":
            top = stack.pop() if len(stack) > 1 else None
            if not top or top["t"] != head:
                raise TemplateError(name + ": unbalanced {{/" + head + "}}")
            parent = stack[-1]
            if parent["t"] == "root":
                cur = parent["body"]
            elif parent["t"] == "if":
                cur = parent["no"] if parent["else"] else parent["yes"]
            else:
                cur = parent["body"]
        elif head == "else":
            top = stack[-1]
            if top["t"] != "if":
                raise TemplateError(name + ": {{else}} outside if")
            top["else"] = True
            cur = top["no"]
        elif head in ("icon", "iconViewBox") and len(body) > len(head):
            args = []
            for am in ARG_RE.finditer(body[len(head):]):
                args.append({"lit": am.group(1)} if am.group(1) is not None else {"path": am.group(2)})
            if not args:
                raise TemplateError(name + ": {{" + head + "}} needs an icon name")
            cur.append({"t": "icon" if head == "icon" else "iconbox", "args": args})
        elif body.startswith("{") or body.endswith("}"):
            raise TemplateError(name + ": raw {{{...}}} output is not allowed; use a slot")
        else:
            if not body:
                raise TemplateError(name + ": empty {{}}")
            cur.append({"t": "var", "path": body})
    if pos < len(src):
        cur.append({"t": "text", "v": src[pos:]})
    if len(stack) != 1:
        raise TemplateError(name + ": unclosed {{#" + stack[-1]["t"] + "}}")
    return root["body"]


def template_names(nodes, loop_vars=None, out=None):
    """Collect (path, is_loop_scoped) references used by a compiled template."""
    loop_vars = loop_vars or set()
    out = out if out is not None else []

    def ref(path):
        if path == "@index":
            return
        head = path.split(".")[0]
        out.append((head, head in loop_vars))

    for n in nodes:
        t = n["t"]
        if t == "var":
            ref(n["path"])
        elif t == "if":
            ref(n["cond"]["path"])
            template_names(n["yes"], loop_vars, out)
            template_names(n["no"], loop_vars, out)
        elif t == "each":
            ref(n["path"])
            template_names(n["body"], loop_vars | {n["as"]}, out)
        elif t in ("icon", "iconbox"):
            for a in n["args"]:
                if "path" in a:
                    ref(a["path"])
    return out


def _esc(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        v = "true" if v else "false"
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    elif isinstance(v, dict):
        return ""
    s = str(v)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def _truthy(v):
    if v is None or v is False or v == "":
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v != 0
    if isinstance(v, list):
        return len(v) > 0
    return True


def _lookup(path, props, scope, index):
    if path == "@index":
        return index
    parts = path.split(".")
    v = scope[parts[0]] if parts[0] in scope else props.get(parts[0])
    for p in parts[1:]:
        if isinstance(v, dict):
            v = v.get(p)
        else:
            return None
    return v


def render_template(nodes, props, icons=None, scope=None, index=0):
    scope = scope or {}
    out = []
    for n in nodes:
        t = n["t"]
        if t == "text":
            out.append(n["v"])
        elif t == "var":
            out.append(_esc(_lookup(n["path"], props, scope, index)))
        elif t == "if":
            v = _lookup(n["cond"]["path"], props, scope, index)
            op = n["cond"].get("op")
            sv = "" if v is None else (("true" if v else "false") if isinstance(v, bool) else str(v))
            ok = (sv == n["cond"]["lit"]) if op == "==" else (sv != n["cond"]["lit"]) if op == "!=" else _truthy(v)
            out.append(render_template(n["yes"] if ok else n["no"], props, icons, scope, index))
        elif t == "each":
            lst = _lookup(n["path"], props, scope, index)
            if isinstance(lst, list):
                for i, item in enumerate(lst):
                    s2 = dict(scope)
                    s2[n["as"]] = item
                    out.append(render_template(n["body"], props, icons, s2, i))
        elif t in ("icon", "iconbox"):
            out.append('<path d="M0 0"/>' if t == "icon" else "0 0 24 24")
    return "".join(out)


# ── html structure helpers ───────────────────────────────────────────────────
class _Outline(HTMLParser):
    """Records top-level elements and every start tag with its attributes."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.depth = 0
        self.top = []
        self.tags = []   # (tag, attrs dict, line, parent_tag_stack_copy)
        self.stack = []
        self.text_at_top = False

    def handle_starttag(self, tag, attrs):
        a = dict((k, v if v is not None else "") for k, v in attrs)
        if not self.stack:
            self.top.append(tag)
        self.tags.append((tag, a, self.getpos()[0], list(self.stack)))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        a = dict((k, v if v is not None else "") for k, v in attrs)
        if not self.stack:
            self.top.append(tag)
        self.tags.append((tag, a, self.getpos()[0], list(self.stack)))

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if not self.stack and data.strip():
            self.text_at_top = True


def outline(html):
    p = _Outline()
    p.feed(html)
    p.close()
    return p


def selector_classes(css):
    """Yield (selector_text, line) for every rule selector in a CSS string."""
    clean = re.sub(r"/\*[\s\S]*?\*/", lambda m: "\n" * m.group(0).count("\n"), css)
    for m in re.finditer(r"([^{};]+)\{", clean):
        sel = m.group(1).strip()
        if not sel or sel.startswith("@"):
            continue
        if re.match(r"^(from|to|\d+(\.\d+)?%)(\s*,\s*(from|to|\d+(\.\d+)?%))*$", sel):
            continue
        g = m.group(1)
        start = m.start(1) + (len(g) - len(g.lstrip()))
        yield sel, clean.count("\n", 0, start) + 1


CLASS_IN_SEL_RE = re.compile(r"\.(-?[A-Za-z_][\w-]*)")
VAR_USE_RE = re.compile(r"var\(\s*(--[\w-]+)")
# var(--x) with NO fallback: must be defined somewhere in the DS. var(--x, 4)
# is a knob (a page or parent may set it; the fallback is the default).
VAR_REQUIRED_RE = re.compile(r"var\(\s*(--[\w-]+)\s*\)")
VAR_DEF_RE = re.compile(r"(?<![\w-])(--[\w-]+)\s*:")


def css_classes(css):
    out = set()
    for sel, _ in selector_classes(css):
        for c in CLASS_IN_SEL_RE.findall(re.sub(r"\[[^\]]*\]", "", sel)):
            out.add(c)
    return out


def subject_classes(selector):
    """Classes on the LAST compound of each comma-separated selector."""
    out = set()
    for part in selector.split(","):
        part = re.sub(r"\[[^\]]*\]", "", part)
        part = re.sub(r":(not|is|where|has)\([^)]*\)", "", part)
        comps = re.split(r"\s+|>|\+|~", part.strip())
        comps = [c for c in comps if c]
        if comps:
            out.update(CLASS_IN_SEL_RE.findall(comps[-1]))
    return out


def strip_css_comments(css):
    return re.sub(r"/\*[\s\S]*?\*/", "", css)


# ── loading ──────────────────────────────────────────────────────────────────
class Block(object):
    def __init__(self, name, kind, path):
        self.name, self.kind, self.dir = name, kind, path
        self.spec = {}
        self.template = ""
        self.compiled = None
        self.style = None
        self.behavior = None
        self.examples = []
        self.root_class = None
        self.template_classes = set()

    @property
    def class_roots(self):
        roots = [self.root_class] if self.root_class else []
        roots += [r for r in (self.spec.get("classRoots") or []) if isinstance(r, str)]
        return roots

    def owns_class(self, c):
        for rc in self.class_roots:
            if c == rc or c.startswith(rc + "__") or c.startswith(rc + "--"):
                return True
        return False


class DesignSystem(object):
    def __init__(self, path):
        self.dir = os.path.abspath(path)
        self.id = os.path.basename(self.dir.rstrip("/"))
        self.meta = {}
        self.blocks = {}
        self.findings = []
        self.icons = {}             # style -> name -> {"v": viewBox, "b": body}
        self.services = []          # (name, desc, path)
        self.tokens = set()         # custom properties defined anywhere in DS css
        self.ds_classes = set()     # every class appearing in DS css selectors
        self.css_files = []         # (layer, path)

    def add(self, level, code, msg, file=None, line=None):
        self.findings.append(Finding(level, code, msg, file, line))

    @property
    def kind(self):
        return self.meta.get("kind", "document")

    def owner_of_class(self, c):
        for b in self.blocks.values():
            if b.owns_class(c):
                return b
        return None

    def version(self):
        h = hashlib.sha256()
        for root, dirs, files in os.walk(self.dir):
            dirs[:] = sorted(d for d in dirs if d not in ("build", "_legacy", ".git") and not d.startswith("."))
            for f in sorted(files):
                if f.startswith("."):
                    continue
                p = os.path.join(root, f)
                h.update(os.path.relpath(p, self.dir).encode())
                with open(p, "rb") as fh:
                    h.update(fh.read())
        return h.hexdigest()[:12]


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_json(ds, path, what):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError as e:
        ds.add("error", "schema-invalid", what + " is not valid JSON: " + str(e), path)
    except OSError:
        ds.add("error", "schema-invalid", what + " is missing", path)
    return None


def _validate_spec(ds, b, path):
    s = b.spec
    for k in s:
        if k not in SPEC_FIELDS:
            ds.add("error", "schema-invalid", "unknown field '" + k + "'", path)
    if s.get("name") != b.name:
        ds.add("error", "schema-invalid", "name must be '" + b.name + "' (the folder name)", path)
    allowed = BLOCK_DIRS[b.kind]
    if s.get("layer") not in allowed:
        ds.add("error", "schema-invalid", "layer must be one of " + "|".join(allowed) + " for " + b.kind + "/", path)
    if not s.get("oneLine"):
        ds.add("error", "schema-invalid", "oneLine is required (it is what the agent reads)", path)
    props = s.get("props", {})
    if not isinstance(props, dict):
        ds.add("error", "schema-invalid", "props must be an object", path)
        props = {}
    for pn, ps in props.items():
        if not NAME_RE.match(pn):
            ds.add("error", "schema-invalid", "prop name '" + pn + "' must be lowercase kebab-case", path)
        if pn in ("id", "class", "slot") or pn.startswith("data-") or pn.startswith("aria-"):
            ds.add("error", "schema-invalid", "prop '" + pn + "' clashes with a reserved attribute (id, class, slot, data-*, aria-*)", path)
        if not isinstance(ps, dict):
            ds.add("error", "schema-invalid", "prop '" + pn + "' must be an object", path)
            continue
        for k in ps:
            if k not in PROP_FIELDS:
                ds.add("error", "schema-invalid", "prop '" + pn + "': unknown field '" + k + "'", path)
        t = ps.get("type", "string")
        if t not in PROP_TYPES:
            ds.add("error", "schema-invalid", "prop '" + pn + "': type must be " + "|".join(PROP_TYPES), path)
        if t == "enum":
            vals = ps.get("values")
            if not isinstance(vals, list) or not vals:
                ds.add("error", "schema-invalid", "prop '" + pn + "': enum needs values", path)
            elif "default" in ps and ps["default"] not in vals:
                ds.add("error", "schema-invalid", "prop '" + pn + "': default not in values", path)
        if ps.get("required") and "default" in ps:
            ds.add("warn", "schema-invalid", "prop '" + pn + "' is required AND has a default", path)
    slots = s.get("slots")
    if slots is not None:
        if not isinstance(slots, dict):
            ds.add("error", "schema-invalid", "slots must be an object", path)
        else:
            for sn, sp in slots.items():
                if not isinstance(sp, dict):
                    ds.add("error", "schema-invalid", "slot '" + sn + "' must be an object", path)
                    continue
                acc = sp.get("accepts", "any")
                if not (acc in ("any", "text") or isinstance(acc, list)):
                    ds.add("error", "schema-invalid", "slot '" + sn + "': accepts must be any|text|[blocks]", path)
    for fld in ("replaces", "contains", "events", "states", "classRoots"):
        v = s.get(fld, [])
        if not isinstance(v, list):
            ds.add("error", "schema-invalid", fld + " must be a list", path)
    for ev in s.get("events", []) or []:
        if not str(ev).startswith("ds:"):
            ds.add("error", "schema-invalid", "event '" + str(ev) + "' must start with ds:", path)
    copy = s.get("copy", {})
    if isinstance(copy, dict):
        for pn, rule in copy.items():
            if pn not in props:
                ds.add("error", "schema-invalid", "copy rule for unknown prop '" + pn + "'", path)
            if isinstance(rule, dict):
                for k in rule:
                    if k not in COPY_FIELDS:
                        ds.add("error", "schema-invalid", "copy rule '" + pn + "': unknown field '" + k + "'", path)


def load(ds_dir):
    """Load + validate a component DS. Never raises; problems land in ds.findings."""
    ds = DesignSystem(ds_dir)
    meta_path = os.path.join(ds.dir, "meta.json")
    ds.meta = _load_json(ds, meta_path, "meta.json") or {}
    if ds.kind != "component":
        return ds
    if ds.meta.get("componentFormat") != FORMAT:
        ds.add("error", "schema-invalid", "meta.json componentFormat must be " + str(FORMAT), meta_path)

    # css inventory
    for p in sorted(glob.glob(os.path.join(ds.dir, "tokens", "*.css"))):
        ds.css_files.append(("tokens", p))
    for p in sorted(glob.glob(os.path.join(ds.dir, "foundations", "*.css"))):
        ds.css_files.append(("base", p))
    for p in sorted(glob.glob(os.path.join(ds.dir, "themes", "*.css"))):
        ds.css_files.append(("themes", p))
    if not glob.glob(os.path.join(ds.dir, "tokens", "*.css")):
        ds.add("error", "schema-invalid", "tokens/tokens.css is missing", ds.dir)

    # blocks
    for kind in BLOCK_DIRS:
        for d in sorted(glob.glob(os.path.join(ds.dir, kind, "*"))):
            if not os.path.isdir(d):
                continue
            name = os.path.basename(d)
            if not NAME_RE.match(name) or name in RESERVED:
                ds.add("error", "schema-invalid", "block folder name '" + name + "' is not allowed", d)
                continue
            if name in ds.blocks:
                ds.add("error", "duplicate-block-name", "'" + name + "' exists in " + ds.blocks[name].kind + "/ and " + kind + "/", d)
                continue
            b = Block(name, kind, d)
            spec_path = os.path.join(d, "component.json")
            b.spec = _load_json(ds, spec_path, "component.json") or {}
            if b.spec:
                _validate_spec(ds, b, spec_path)
            tpath = os.path.join(d, "template.html")
            if os.path.isfile(tpath):
                b.template = _read(tpath)
            else:
                ds.add("error", "schema-invalid", "template.html is missing", d)
            sp = os.path.join(d, "style.css")
            if os.path.isfile(sp):
                b.style = sp
                ds.css_files.append(("block", sp))
            bp = os.path.join(d, "behavior.js")
            if os.path.isfile(bp):
                b.behavior = bp
            ep = os.path.join(d, "examples.json")
            ex = _load_json(ds, ep, "examples.json") if os.path.isfile(ep) else None
            if not os.path.isfile(ep):
                ds.add("error", "missing-example", "examples.json is missing", d)
            elif not isinstance(ex, list) or not ex:
                ds.add("error", "missing-example", "examples.json needs at least one example", ep)
            else:
                b.examples = ex
            ds.blocks[name] = b

    # css vocabulary (tokens + classes)
    for _, p in ds.css_files:
        css = strip_css_comments(_read(p))
        ds.tokens.update(VAR_DEF_RE.findall(css))
        ds.ds_classes.update(css_classes(css))

    # templates
    for b in ds.blocks.values():
        if not b.template:
            continue
        try:
            b.compiled = compile_template(b.template, b.name)
        except TemplateError as e:
            ds.add("error", "template-error", str(e), os.path.join(b.dir, "template.html"))
            continue
        props = b.spec.get("props", {}) or {}
        for ref, scoped in template_names(b.compiled):
            if not scoped and ref not in props:
                ds.add("error", "template-unknown-name", "{{" + ref + "}} is not a prop of " + b.name,
                       os.path.join(b.dir, "template.html"))
        # Replace {{...}} with a sentinel so a templated class ("{{role}}",
        # "btn--{{variant}}") is recognisable as dynamic, never mistaken for
        # a literal class name.
        stripped = TAG_RE.sub(DYN, b.template)
        ol = outline(stripped)
        for t in ol.tags:
            for c in (t[1].get("class") or "").split():
                if DYN not in c:
                    b.template_classes.add(c)
        rc = b.spec.get("rootClass")
        if not rc and ol.tags:
            # default root class = the first class on the template root; a
            # templated first class means the block has no fixed root class
            first = (ol.tags[0][1].get("class") or "").split()
            rc = first[0] if first and DYN not in first[0] else None
        b.root_class = rc if rc and "{{" not in rc and DYN not in rc else None

    # root classes (rootClass + classRoots) must be unique across blocks
    seen = {}
    for b in ds.blocks.values():
        for rc in b.class_roots:
            if rc in seen and seen[rc] != b.name:
                ds.add("error", "duplicate-root-class", "'." + rc + "' is a class root of both " + seen[rc] + " and " + b.name,
                       os.path.join(b.dir, "component.json"))
            seen[rc] = b.name

    # icons
    for p in sorted(glob.glob(os.path.join(ds.dir, "icons", "*", "*.svg"))):
        style = os.path.basename(os.path.dirname(p))
        name = os.path.splitext(os.path.basename(p))[0]
        svg = _read(p)
        vb = re.search(r'viewBox\s*=\s*"([^"]+)"', svg)
        body = re.search(r"<svg\b[^>]*>([\s\S]*)</svg>", svg)
        if not vb or not body:
            ds.add("error", "icon-invalid", "icon needs an <svg viewBox> root", p)
            continue
        inner = re.sub(r"\s+fill=\"(?!none)[^\"]*\"", "", body.group(1).strip())
        ds.icons.setdefault(style, {})[name] = {"v": vb.group(1), "b": inner}

    # services
    for p in sorted(glob.glob(os.path.join(ds.dir, "services", "*.js"))):
        src = _read(p)
        name = os.path.splitext(os.path.basename(p))[0]
        m = re.search(r"@desc\s+(.+)", src)
        if not re.search(r"DS\.service\(\s*[\"']" + re.escape(name) + r"[\"']", src):
            ds.add("warn", "service-name", "services/" + name + ".js should call DS.service(\"" + name + "\", ...)", p)
        ds.services.append((name, m.group(1).strip() if m else "", p))

    _check_ds(ds)
    return ds


# ── DS-level checks ──────────────────────────────────────────────────────────
def _check_ds(ds):
    from ds_page import check_markup   # local import: ds_page imports this module
    for b in ds.blocks.values():
        spec_path = os.path.join(b.dir, "component.json")
        tpath = os.path.join(b.dir, "template.html")
        for c in b.spec.get("contains", []) or []:
            if c not in ds.blocks:
                ds.add("error", "unknown-block", "contains unknown block '" + c + "'", spec_path)
        for r in b.spec.get("replaces", []) or []:
            if not re.match(r"^[a-z][a-z0-9]*$", str(r)):
                ds.add("error", "schema-invalid", "replaces must list raw tag names, got '" + str(r) + "'", spec_path)
        slots = b.spec.get("slots") or {}
        for sn, sp in slots.items():
            acc = sp.get("accepts") if isinstance(sp, dict) else None
            if isinstance(acc, list):
                for a in acc:
                    if a not in ds.blocks:
                        ds.add("error", "unknown-block", "slot '" + sn + "' accepts unknown block '" + a + "'", spec_path)
        # template: nested blocks and raw markup, checked like a page
        if b.compiled is not None:
            # drop control tags, keep {{value}} tags so attribute checks know
            # the value is only known at render time
            stripped = TAG_RE.sub(lambda m: "" if (m.group(1) or m.group(2).strip() == "else") else m.group(0), b.template)
            for f in check_markup(ds, stripped, tpath, mode="template", owner=b):
                ds.findings.append(f)
            used_slots = set(re.findall(r'<ds-slot(?:\s+name="([\w-]+)")?', b.template))
            used_slots = set(s or "default" for s in used_slots)
            for sn in slots:
                if sn not in used_slots:
                    ds.add("error", "schema-invalid", "slot '" + sn + "' is declared but the template has no <ds-slot name=\"" + sn + "\">", tpath)
            for sn in used_slots:
                if sn not in slots:
                    ds.add("error", "schema-invalid", "template has <ds-slot name=\"" + sn + "\"> but component.json declares no such slot", tpath)
        # examples: valid props, single root
        props = b.spec.get("props", {}) or {}
        seen_enum = dict((k, set()) for k, v in props.items() if v.get("type") == "enum")
        for i, ex in enumerate(b.examples):
            ep = os.path.join(b.dir, "examples.json")
            if not isinstance(ex, dict):
                ds.add("error", "missing-example", "example " + str(i + 1) + " must be an object", ep)
                continue
            for k in ex:
                if k not in EXAMPLE_FIELDS:
                    ds.add("error", "schema-invalid", "example " + str(i + 1) + ": unknown field '" + k + "'", ep)
            ep_props = ex.get("props", {}) or {}
            for f in validate_props(b, ep_props, ep, None, from_attr=False):
                ds.findings.append(f)
            full = {}
            for k, v in props.items():
                if "default" in v:
                    full[k] = v["default"]
            full.update(ep_props)
            for k in seen_enum:
                if k in full:
                    seen_enum[k].add(full[k])
            if b.compiled is not None:
                html = render_template(b.compiled, full)
                ol = outline(html)
                if len(ol.top) != 1 or ol.text_at_top:
                    ds.add("error", "template-not-single-root", "example '" + str(ex.get("title", i + 1)) + "' renders " + str(len(ol.top)) + " top-level elements; a template needs exactly one root", tpath)
            for sn, html in (ex.get("slots") or {}).items():
                if sn not in slots:
                    ds.add("error", "slot-not-allowed", "example " + str(i + 1) + " fills unknown slot '" + sn + "'", ep)
                for f in check_markup(ds, html, ep, mode="example"):
                    ds.findings.append(f)
        for k, vals in seen_enum.items():
            if len(props[k].get("values", [])) > ENUM_COVERAGE_MAX:
                continue
            missing = [v for v in props[k].get("values", []) if v not in vals]
            if missing:
                ds.add("warn", "missing-example", "no example shows " + k + "=" + "|".join(missing), os.path.join(b.dir, "examples.json"))
        # behavior name
        if b.behavior:
            src = _read(b.behavior)
            names = re.findall(r"DS\.behavior\(\s*[\"']([\w-]+)[\"']", src)
            if not names:
                ds.add("error", "behavior-name", "behavior.js must call DS.behavior(\"" + b.name + "\", ...)", b.behavior)
            for n in names:
                if n != b.name:
                    ds.add("error", "behavior-name", "behavior.js registers '" + n + "' but lives in " + b.name + "/", b.behavior)

    # CSS rules
    for layer, p in ds.css_files:
        css = _read(p)
        clean = strip_css_comments(css)
        if re.search(r"@import\s+(url\()?[\"']?(?!https?:|//)", clean):
            ds.add("error", "css-import", "local @import is not allowed; the generator bundles every file", p)
        owner = None
        for b in ds.blocks.values():
            if b.style == p:
                owner = b
        for i, line in enumerate(clean.split("\n")):
            for v in VAR_REQUIRED_RE.findall(line):
                if v not in ds.tokens:
                    ds.add("error", "token-undefined", v + " is used without a fallback but never defined in the DS", p, i + 1)
            if layer not in ("tokens", "themes") and COLOR_LITERAL_RE.search(line):
                ds.add("error", "raw-value-in-block-css", "colour literal outside tokens/themes: " + line.strip()[:80], p, i + 1)
        if owner:
            allowed = set(owner.spec.get("contains", []) or [])
            for sel, line in selector_classes(css):
                for c in subject_classes(sel):
                    ob = ds.owner_of_class(c)
                    if ob and ob is not owner and ob.name not in allowed:
                        ds.add("warn", "css-outside-block", "styles ." + c + " (owned by " + ob.name + ") without listing it in contains", p, line)


def validate_props(block, attrs, file, line, from_attr=True):
    """Validate a block's props given as attributes (strings) or JSON values."""
    out = []
    specs = block.spec.get("props", {}) or {}
    for an, av in attrs.items():
        if an == "slot":
            continue
        spec = specs.get(an)
        if spec is None:
            if from_attr and is_passthrough(an):
                if an == "style":
                    out.append(Finding("error", "inline-style-on-block", "ds-" + block.name + " has an inline style; use props", file, line))
                continue
            out.append(Finding("error", "unknown-prop", "ds-" + block.name + " has no prop '" + an + "'", file, line))
            continue
        t = spec.get("type", "string")
        if "{{" in str(av):
            continue    # template interpolation: value known only at render time
        if t == "number":
            try:
                float(av)
            except (TypeError, ValueError):
                out.append(Finding("error", "bad-prop-type", an + "='" + str(av) + "' is not a number", file, line))
        elif t == "enum":
            if str(av) not in [str(x) for x in spec.get("values", [])]:
                out.append(Finding("error", "bad-enum", an + "='" + str(av) + "' not in " + "|".join(spec.get("values", [])), file, line))
        elif t == "json" and from_attr:
            try:
                json.loads(av)
            except ValueError:
                out.append(Finding("error", "bad-prop-type", an + " is not valid JSON", file, line))
        elif t == "boolean" and from_attr and av not in ("", "true", "false", an):
            out.append(Finding("error", "bad-prop-type", an + "='" + av + "' must be empty, true or false", file, line))
    for pn, spec in specs.items():
        if spec.get("required") and pn not in attrs:
            out.append(Finding("error", "missing-required", "ds-" + block.name + " needs '" + pn + "'", file, line))
    return out
