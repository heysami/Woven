#!/usr/bin/env python3
"""ds_page.py - check markup (a page, a block template, a gallery example)
against a component design system. Stdlib only, Python 3.9-safe.

Pages are checked in SOURCE form (the <ds-*> tags as written), which is what
the agent edits. JS-built markup is only scanned heuristically here; the
runtime self-check (DS.violations) is the authoritative check for it.
"""

import os
import re
from html.parser import HTMLParser

from ds_model import (Finding, VOID, is_passthrough, validate_props, selector_classes, strip_css_comments,
                      CLASS_IN_SEL_RE, VAR_USE_RE, VAR_DEF_RE)

INLINE_TAGS = {"b", "i", "em", "strong", "span", "a", "br", "code", "small", "sup", "sub", "mark", "abbr",
               "time", "u", "s", "kbd", "wbr"}
DS_HTML_RE = re.compile(r"DS\.html\(\s*[\"'`]([\w-]+)[\"'`]")
JS_CLASS_RE = re.compile(r"class(?:Name)?\s*=\s*\\?[\"']([^\"'\\]*)")
JS_RAW_TAG_RE = re.compile(r"<(select|button|table|textarea|input|dialog|details)\b")


class _Frame(object):
    __slots__ = ("tag", "block", "custom", "line", "proxy_slot")

    def __init__(self, tag, block, custom, line, proxy_slot=None):
        # proxy_slot: a <template slot="x"> inside a block; its children are
        # that block's slot-x content (table rows only parse inside <template>)
        self.tag, self.block, self.custom, self.line, self.proxy_slot = tag, block, custom, line, proxy_slot


class _Checker(HTMLParser):
    def __init__(self, ds, file, mode, owner, line_offset=0):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.ds, self.file, self.mode, self.owner, self.off = ds, file, mode, owner, line_offset
        self.out = []
        self.stack = []
        self.replaced = {}
        for b in sorted(ds.blocks.values(), key=lambda x: x.name):
            for t in b.spec.get("replaces", []) or []:
                self.replaced.setdefault(t, b.name)
        self.raw_mode = None          # "style" | "script" while inside one
        self.raw_buf = []
        self.raw_line = 0
        self.raw_attrs = {}
        self.styles = []              # (css, line)
        self.scripts = []             # (js, line)
        self.links = []               # (href, line)
        self.script_srcs = []         # (src, line)
        self.uses_blocks = False
        self.customs = []

    # helpers
    def line(self):
        return self.getpos()[0] + self.off

    def add(self, level, code, msg):
        self.out.append(Finding(level, code, msg, self.file, self.line()))

    def in_custom(self):
        return any(f.custom for f in self.stack)

    def parent_block(self):
        return self.stack[-1].block if self.stack and self.stack[-1].block else None

    def check_slot_child(self, tag, attrs, is_text=False):
        parent = self.parent_block()
        if not parent:
            return
        slots = parent.spec.get("slots")
        proxy = self.stack[-1].proxy_slot
        slot = proxy or ("default" if is_text else attrs.get("slot", "default"))
        if not slots or slot not in slots:
            self.add("error", "no-slots" if not slots else "slot-not-allowed",
                     "ds-" + parent.name + (" takes no children" if not slots else " has no '" + slot + "' slot"))
            return
        acc = slots[slot].get("accepts", "any") if isinstance(slots[slot], dict) else "any"
        child = tag[3:] if (tag and tag.startswith("ds-") and tag not in ("ds-custom", "ds-slot")) else None
        if isinstance(acc, list):
            if is_text or child not in acc:
                self.add("error", "slot-not-allowed", "ds-" + parent.name + " slot '" + slot + "' accepts only " + ", ".join("ds-" + a for a in acc))
        elif acc == "text" and not is_text:
            if child or tag not in INLINE_TAGS:
                self.add("error", "slot-not-allowed", "ds-" + parent.name + " slot '" + slot + "' accepts text and inline markup only")

    # parser callbacks
    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, push=tag not in VOID)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, push=False)

    def _start(self, tag, attrs_list, push):
        attrs = dict((k, v if v is not None else "") for k, v in attrs_list)
        if self.raw_mode:
            return
        if self.mode == "page" and (attrs.get("id") or "").startswith("ds-"):
            self.add("warn", "reserved-id", "id '" + attrs["id"] + "' uses the ds- prefix, which is reserved for ids the runtime generates (they are not saved)")
        if tag == "template" and "slot" in attrs and self.parent_block() and not self.stack[-1].proxy_slot:
            parent = self.parent_block()
            slots = parent.spec.get("slots") or {}
            if attrs["slot"] not in slots:
                self.add("error", "slot-not-allowed", "ds-" + parent.name + " has no '" + attrs["slot"] + "' slot")
            if push:
                self.stack.append(_Frame(tag, parent, False, self.line(), proxy_slot=attrs["slot"]))
            return
        if tag == "ds-slot":
            if self.mode != "template":
                self.add("error", "unknown-block", "<ds-slot> is only valid inside a block template")
            if push:
                self.stack.append(_Frame(tag, None, False, self.line()))
            return
        self.check_slot_child(tag, attrs)
        block, custom = None, False
        if tag == "ds-custom":
            self.uses_blocks = True
            if self.mode == "template":
                self.add("error", "unknown-block", "templates cannot contain ds-custom")
            elif not (attrs.get("reason") or "").strip():
                self.add("error", "custom-without-reason", "<ds-custom> needs reason=\"why this is not a block\"")
            else:
                self.customs.append((attrs.get("reason"), self.line()))
            custom = True
        elif tag.startswith("ds-"):
            self.uses_blocks = True
            name = tag[3:]
            block = self.ds.blocks.get(name)
            if not block:
                self.add("error", "unknown-block", "<" + tag + "> is not a block in design system '" + self.ds.id + "'")
            else:
                for f in validate_props(block, attrs, self.file, self.line()):
                    self.out.append(f)
                if self.mode == "page":
                    self._copy_rules(block, attrs)
        else:
            self._raw(tag, attrs)
            if tag in ("style", "script"):
                if tag == "script" and attrs.get("src"):
                    self.script_srcs.append((attrs["src"], self.line()))
                if push:
                    self.raw_mode, self.raw_buf, self.raw_line, self.raw_attrs = tag, [], self.line(), attrs
                return
            if tag == "link" and "stylesheet" in (attrs.get("rel") or "").split():
                self.links.append((attrs.get("href") or "", self.line()))
        if push:
            self.stack.append(_Frame(tag, block, custom, self.line()))

    def _raw(self, tag, attrs):
        inc = self.in_custom()
        owner = self.owner
        # `replaces` governs PAGES: a block's own template is DS code and may use
        # any raw element (a filter chip IS a <button>, just not the button block).
        if self.mode != "template" and tag in self.replaced and not inc \
                and not (tag == "input" and (attrs.get("type") or "").lower() == "hidden"):
            self.add("error", "raw-replaced-element", "raw <" + tag + ">; use <ds-" + self.replaced[tag] + ">")
        for c in (attrs.get("class") or "").split():
            ob = self.ds.owner_of_class(c)
            if not ob:
                continue
            # A template may use its own classes, and classes of blocks it
            # declares in `contains` (same-element composition such as
            # .card.stat-card, or deliberate part reuse such as .acc__title).
            if self.mode == "template" and owner and (ob is owner or ob.name in (owner.spec.get("contains") or [])):
                continue
            self.add("warn" if inc else "error", "hand-built-block",
                     "." + c + " is part of ds-" + ob.name + "; place <ds-" + ob.name + "> instead of writing its markup")
            break
        style = attrs.get("style")
        if style and not inc:
            decls = [d.strip() for d in style.split(";") if d.strip()]
            knobs_only = all(d.startswith("--") for d in decls)
            if self.mode == "page":
                self.add("warn", "inline-style", "inline style on <" + tag + ">; use layout blocks or a page class")
            elif self.mode == "template" and not knobs_only:
                self.add("warn", "inline-style", "template sets inline style other than --custom-property knobs")

    def _copy_rules(self, block, attrs):
        rules = block.spec.get("copy") or {}
        for pn, rule in rules.items():
            v = attrs.get(pn)
            if v is None or "{{" in v:
                continue
            if rule.get("maxWords") and len(v.split()) > rule["maxWords"]:
                self.add("warn", "copy-rule", pn + " of ds-" + block.name + " has " + str(len(v.split())) + " words (max " + str(rule["maxWords"]) + ")")
            if rule.get("maxChars") and len(v) > rule["maxChars"]:
                self.add("warn", "copy-rule", pn + " of ds-" + block.name + " has " + str(len(v)) + " characters (max " + str(rule["maxChars"]) + ")")
            case = rule.get("case")
            words = [w for w in re.findall(r"[A-Za-z][\w']*", v)]
            if case == "sentence" and len(words) > 1 and sum(1 for w in words[1:] if w[0].isupper() and not w.isupper()) > 0:
                self.add("warn", "copy-rule", pn + " of ds-" + block.name + " should be sentence case: '" + v + "'")
            if case == "title" and any(w[0].islower() and len(w) > 3 for w in words):
                self.add("warn", "copy-rule", pn + " of ds-" + block.name + " should be title case: '" + v + "'")

    def handle_endtag(self, tag):
        if self.raw_mode:
            if tag != self.raw_mode:
                return
            text = "".join(self.raw_buf)
            if tag == "style":
                self.styles.append((text, self.raw_line))
            elif not self.raw_attrs.get("src") and (self.raw_attrs.get("type") or "text/javascript") in ("text/javascript", "module", "application/javascript"):
                self.scripts.append((text, self.raw_line))
            self.raw_mode = None
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.raw_mode:
            self.raw_buf.append(data)
            return
        if data.strip() and self.parent_block():
            self.check_slot_child(None, {}, is_text=True)


def check_markup(ds, html, file, mode="page", owner=None, line_offset=0):
    c = _Checker(ds, file, mode, owner, line_offset)
    c.feed(html)
    c.close()
    return c.out if mode != "page" else c


def check_css(ds, css, file, line0, page_tokens):
    out = []
    for sel, line in selector_classes(css):
        hit = [c for c in CLASS_IN_SEL_RE.findall(re.sub(r"\[[^\]]*\]", "", sel)) if c in ds.ds_classes]
        if hit:
            out.append(Finding("error", "page-css-touches-ds",
                               "page CSS selects DS class ." + hit[0] + " (`" + sel[:70] + "`); DS classes are styled only by the DS",
                               file, line0 + line - 1))
    clean = strip_css_comments(css)
    for i, ln in enumerate(clean.split("\n")):
        for v in VAR_USE_RE.findall(ln):
            if v not in ds.tokens and v not in page_tokens:
                out.append(Finding("warn", "unknown-token", v + " is not a DS token", file, line0 + i))
    return out


def check_js(ds, js, file, line0, level="warn"):
    out = []
    for i, ln in enumerate(js.split("\n")):
        for m in DS_HTML_RE.finditer(ln):
            if m.group(1) not in ds.blocks:
                out.append(Finding("error", "unknown-block", "DS.html('" + m.group(1) + "') is not a block in '" + ds.id + "'", file, line0 + i))
        for m in JS_CLASS_RE.finditer(ln):
            for c in m.group(1).split():
                ob = ds.owner_of_class(c)
                if ob:
                    out.append(Finding(level, "hand-built-in-js", "JS writes ." + c + " markup by hand; use DS.html('" + ob.name + "', ...)", file, line0 + i))
                    break
        for m in JS_RAW_TAG_RE.finditer(ln):
            for b in ds.blocks.values():
                if m.group(1) in (b.spec.get("replaces") or []):
                    out.append(Finding(level, "raw-replaced-in-js", "JS builds a raw <" + m.group(1) + ">; use DS.html('" + b.name + "', ...)", file, line0 + i))
                    break
    return out


def _local(href, page_dir):
    if not href or re.match(r"^([a-z]+:|//|#|/__)", href):
        return None
    path = href.split("?")[0].split("#")[0]
    if path.startswith("/"):
        return None
    return os.path.normpath(os.path.join(page_dir, path))


def check_page(ds, page_path, html=None):
    """Full page check. Returns a list of Findings."""
    if html is None:
        with open(page_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
    c = check_markup(ds, html, page_path, mode="page")
    out = list(c.out)
    page_dir = os.path.dirname(os.path.abspath(page_path))
    page_tokens = set()
    for css, _ in c.styles:
        page_tokens.update(VAR_DEF_RE.findall(strip_css_comments(css)))
    for css, line in c.styles:
        out.extend(check_css(ds, css, page_path, line, page_tokens))
    build = os.path.join(ds.dir, "build")
    has_bundle = has_runtime = False
    for href, line in c.links:
        p = _local(href, page_dir)
        if p and os.path.normpath(p) == os.path.normpath(os.path.join(build, "ds.css")):
            has_bundle = True
            continue
        if p and p.startswith(ds.dir + os.sep) and not p.startswith(build + os.sep):
            out.append(Finding("warn", "legacy-stylesheet", "links " + href + "; a component DS page links only build/ds.css", page_path, line))
            continue
        if p and os.path.isfile(p) and p.endswith(".css"):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    out.extend(check_css(ds, f.read(), p, 1, page_tokens))
            except OSError:
                pass
    for src, line in c.script_srcs:
        p = _local(src, page_dir)
        if p and os.path.normpath(p) == os.path.normpath(os.path.join(build, "ds-runtime.js")):
            has_runtime = True
            continue
        if p and os.path.isfile(p) and p.endswith(".js") and not p.startswith(ds.dir + os.sep):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    out.extend(check_js(ds, f.read(), p, 1))
            except OSError:
                pass
    for js, line in c.scripts:
        out.extend(check_js(ds, js, page_path, line))
    uses_js_blocks = any(DS_HTML_RE.search(js) for js, _ in c.scripts)
    if (c.uses_blocks or uses_js_blocks) and not has_runtime:
        out.append(Finding("error", "missing-runtime", "page uses blocks but does not load design-systems/" + ds.id + "/build/ds-runtime.js in <head>", page_path, 1))
    if (c.uses_blocks or uses_js_blocks) and not has_bundle:
        out.append(Finding("error", "missing-bundle", "page uses blocks but does not link design-systems/" + ds.id + "/build/ds.css", page_path, 1))
    for reason, line in c.customs:
        out.append(Finding("info", "ds-custom", "custom markup: " + reason, page_path, line))
    return out
