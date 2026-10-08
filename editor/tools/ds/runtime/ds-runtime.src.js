/* Woven component design system runtime (format v1).
 *
 * Source of truth: editor/tools/ds/runtime/ds-runtime.src.js. build_ds.py
 * copies this file into design-systems/<id>/build/ds-runtime.js, followed by
 * the DS payload (DS.__load) and every behavior / service file, then DS.__boot().
 * Spec: docs/features/component-ds-format.md.
 *
 * What it does:
 *   - expands <ds-*> tags into the block's template markup (no wrapper left),
 *     outer-first, moving slotted children into the template's <ds-slot> points;
 *   - DS.html(name, props, slots) returns expanded markup synchronously for JS
 *     that builds UI with innerHTML;
 *   - DS.serialize(root) turns expanded markup back into <ds-*> source form,
 *     so editor save-back keeps the short form in files;
 *   - registers delegated behaviors and services;
 *   - self-check: logs hand-built copies of blocks (DS class without data-ds)
 *     and raw elements a block replaces, into DS.violations + console.
 */
(function (global) {
  "use strict";
  if (global.DS && global.DS.__runtime) return;

  var doc = global.document;
  var DS = { __runtime: 1, format: 1, blocks: {}, manifest: null, violations: [],
             config: { check: true } };
  var behaviors = {};          // name -> { on: {...}, init: fn }
  var delegated = {};          // event type -> true (listener installed)
  var compiled = {};           // name -> compiled template
  var seq = 0;                 // instance id counter (data-ds-i)
  var readyFns = [];
  var booted = false, ready = false;
  var warned = typeof WeakMap === "function" ? new WeakMap() : null;   // element -> {code: 1}

  var PASSTHROUGH = { id: 1, "class": 1, style: 1, hidden: 1, title: 1, role: 1, tabindex: 1, lang: 1, dir: 1 };
  var STATE_ATTRS = { "aria-expanded": 1, "aria-selected": 1, "aria-pressed": 1, "aria-checked": 1, "aria-hidden": 0 };
  var NON_BUBBLING = { focus: 1, blur: 1, mouseenter: 1, mouseleave: 1, load: 1, error: 1, scroll: 1, toggle: 1 };
  var VOID = { area: 1, base: 1, br: 1, col: 1, embed: 1, hr: 1, img: 1, input: 1, link: 1, meta: 1, param: 1, source: 1, track: 1, wbr: 1 };
  var RAW_TEXT = { script: 1, style: 1 };

  // ── small helpers ──────────────────────────────────────────────────────────
  function esc(v) {
    if (v == null) return "";
    if (Array.isArray(v)) v = v.join(", ");
    else if (typeof v === "object") return "";
    return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function escAttr(v) { return String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/ /g, "&nbsp;"); }
  function escText(v) { return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/ /g, "&nbsp;"); }
  function kebab(k) { return String(k).replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase(); }
  function isDsTag(el) { return el && el.nodeType === 1 && el.localName.indexOf("ds-") === 0 && el.localName !== "ds-slot"; }
  function report(code, msg, el) {
    if (el && warned) {
      var seen = warned.get(el) || {};
      if (seen[code]) return;
      seen[code] = 1; warned.set(el, seen);
    }
    DS.violations.push({ code: code, message: msg, element: el || null });
    try { console.warn("[ds] " + code + ": " + msg, el || ""); } catch (_) {}
  }
  function truthy(v) {
    if (v == null || v === false || v === "") return false;
    if (typeof v === "number") return v !== 0;
    if (Array.isArray(v)) return v.length > 0;
    return true;
  }

  // ── template engine (logic-less subset, see spec) ─────────────────────────
  // Nodes: {t:"text",v} {t:"var",path} {t:"if",cond,yes,no} {t:"each",path,as,body}
  //        {t:"icon",args} {t:"iconbox",args}
  function parseArgs(s) {
    var out = [], re = /"((?:[^"\\]|\\.)*)"|([A-Za-z_@][\w.\-]*)/g, m;
    while ((m = re.exec(s))) out.push(m[1] != null ? { lit: m[1] } : { path: m[2] });
    return out;
  }
  function parseCond(s) {
    var m = /^(.+?)\s*(==|!=)\s*"((?:[^"\\]|\\.)*)"\s*$/.exec(s);
    if (m) return { path: m[1].trim(), op: m[2], lit: m[3] };
    return { path: s.trim() };
  }
  function compile(src, name) {
    var re = /\{\{\s*([#\/]?)([^}]*?)\s*\}\}/g, pos = 0, m;
    var root = { body: [] }, stack = [root], cur = root.body;
    function push(n) { cur.push(n); }
    while ((m = re.exec(src))) {
      if (m.index > pos) push({ t: "text", v: src.slice(pos, m.index) });
      pos = re.lastIndex;
      var sigil = m[1], body = m[2].trim(), head = body.split(/\s+/)[0];
      if (sigil === "#") {
        if (head === "if") {
          var n = { t: "if", cond: parseCond(body.slice(2)), yes: [], no: [] };
          push(n); stack.push(n); cur = n.yes;
        } else if (head === "each") {
          var em = /^each\s+([\w.\-]+)\s+as\s+([A-Za-z_][\w\-]*)$/.exec(body);
          if (!em) throw new Error(name + ": bad each: " + body);
          var e = { t: "each", path: em[1], as: em[2], body: [] };
          push(e); stack.push(e); cur = e.body;
        } else throw new Error(name + ": unknown block {{#" + head + "}}");
      } else if (sigil === "/") {
        var top = stack.pop();
        if (!top || top === root || (top.t !== head)) throw new Error(name + ": unbalanced {{/" + head + "}}");
        var parent = stack[stack.length - 1];
        cur = parent === root ? root.body : (parent.t === "if" ? (parent._inElse ? parent.no : parent.yes) : parent.body);
      } else if (head === "else") {
        var ifn = stack[stack.length - 1];
        if (!ifn || ifn.t !== "if") throw new Error(name + ": {{else}} outside if");
        ifn._inElse = true; cur = ifn.no;
      } else if ((head === "icon" || head === "iconViewBox") && body.length > head.length) {
        push({ t: head === "icon" ? "icon" : "iconbox", args: parseArgs(body.slice(head.length)) });
      } else {
        push({ t: "var", path: body });
      }
    }
    if (pos < src.length) push({ t: "text", v: src.slice(pos) });
    if (stack.length !== 1) throw new Error(name + ": unclosed block");
    return root.body;
  }
  function lookup(path, ctx) {
    if (path === "@index") return ctx.index;
    var parts = path.split("."), v;
    if (ctx.scope && Object.prototype.hasOwnProperty.call(ctx.scope, parts[0])) v = ctx.scope[parts[0]];
    else v = ctx.props[parts[0]];
    for (var i = 1; i < parts.length && v != null; i++) v = v[parts[i]];
    return v;
  }
  function argVal(a, ctx) { return a.lit != null ? a.lit : lookup(a.path, ctx); }
  function iconData(name, style) {
    var icons = (DS.manifest && DS.manifest.icons) || {};
    style = style || (DS.manifest && DS.manifest.defaultIconStyle) || "filled";
    var set = icons[style] || {};
    var hit = set[name];
    if (!hit) { report("unknown-icon", "icon '" + name + "' (" + style + ") is not in the DS"); return null; }
    return hit;
  }
  function run(nodes, ctx) {
    var out = "";
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.t === "text") out += n.v;
      else if (n.t === "var") out += esc(lookup(n.path, ctx));
      else if (n.t === "if") {
        var v = lookup(n.cond.path, ctx), ok;
        if (n.cond.op === "==") ok = String(v == null ? "" : v) === n.cond.lit;
        else if (n.cond.op === "!=") ok = String(v == null ? "" : v) !== n.cond.lit;
        else ok = truthy(v);
        out += run(ok ? n.yes : n.no, ctx);
      } else if (n.t === "each") {
        var list = lookup(n.path, ctx);
        if (Array.isArray(list)) for (var j = 0; j < list.length; j++) {
          var scope = Object.create(ctx.scope || null); scope[n.as] = list[j];
          out += run(n.body, { props: ctx.props, scope: scope, index: j });
        }
      } else if (n.t === "icon" || n.t === "iconbox") {
        var nm = argVal(n.args[0] || {}, ctx), st = n.args[1] ? argVal(n.args[1], ctx) : null;
        var d = nm ? iconData(nm, st) : null;
        if (d) out += n.t === "icon" ? d.b : esc(d.v);
      }
    }
    return out;
  }
  function render(name, props) {
    var b = DS.blocks[name];
    if (!compiled[name]) compiled[name] = compile(b.template, name);
    return run(compiled[name], { props: props, scope: null, index: 0 });
  }

  // ── props ──────────────────────────────────────────────────────────────────
  function coerce(spec, raw, fromAttr, name, el) {
    var t = spec.type || "string";
    if (t === "boolean") {
      if (fromAttr) return raw !== "false";
      return raw === true || raw === "true" || raw === "";
    }
    if (t === "number") { var n = typeof raw === "number" ? raw : parseFloat(raw); return isNaN(n) ? undefined : n; }
    if (t === "list") {
      if (Array.isArray(raw)) return raw;
      return String(raw).split(",").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    }
    if (t === "json") {
      if (!fromAttr || typeof raw !== "string") return raw;
      try { return JSON.parse(raw); } catch (e) { report("bad-prop-type", name + ": json prop is not valid JSON", el); return undefined; }
    }
    if (t === "enum") {
      var s = String(raw);
      if (spec.values && spec.values.indexOf(s) < 0) report("bad-enum", name + "='" + s + "' not in " + spec.values.join("|"), el);
      return s;
    }
    return String(raw);
  }
  function withDefaults(block, explicit) {
    var props = {}, specs = block.props || {}, k;
    for (k in specs) if (specs[k] && specs[k].default !== undefined) props[k] = specs[k].default;
    for (k in explicit) props[k] = explicit[k];
    return props;
  }
  function readTag(el, block, name) {
    var specs = block.props || {}, explicit = {}, pass = [];
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i], an = a.name;
      if (specs[an]) { var v = coerce(specs[an], a.value, true, an, el); if (v !== undefined) explicit[an] = v; }
      else if (an === "slot") continue;
      else if (PASSTHROUGH[an] || an.indexOf("data-") === 0 || an.indexOf("aria-") === 0) {
        if (an.indexOf("data-ds") === 0) continue;
        if (an === "style") report("inline-style-on-block", "ds-" + name + " has an inline style; use props", el);
        pass.push([an, a.value]);
      } else report("unknown-prop", "ds-" + name + " has no prop '" + an + "'", el);
    }
    return { explicit: explicit, pass: pass };
  }
  function normalizeProps(block, name, props) {
    var specs = block.props || {}, out = {};
    for (var k in props || {}) {
      var key = specs[k] ? k : kebab(k);
      if (!specs[key]) { report("unknown-prop", "ds-" + name + " has no prop '" + k + "'"); continue; }
      if (props[k] === undefined || props[k] === null) continue;
      var v = coerce(specs[key], props[k], false, key);
      if (v !== undefined) out[key] = v;
    }
    return out;
  }
  function checkRequired(block, name, props, el) {
    var specs = block.props || {};
    for (var k in specs) if (specs[k] && specs[k].required && (props[k] === undefined || props[k] === "")) {
      report("missing-required", "ds-" + name + " needs '" + k + "'", el);
    }
  }
  function propsAttr(explicit) {
    var keep = {}, omitted = [], any = false;
    for (var k in explicit) {
      var s = JSON.stringify(explicit[k]);
      if (s && s.length > 2000) { omitted.push(k); continue; }
      keep[k] = explicit[k]; any = true;
    }
    if (omitted.length) { keep.$omitted = omitted; any = true; }
    return any ? JSON.stringify(keep) : null;
  }

  // ── expansion ──────────────────────────────────────────────────────────────
  function templateRoot(name, props, ownerDoc) {
    var t = ownerDoc.createElement("template");
    t.innerHTML = render(name, props);
    var frag = ownerDoc.importNode(t.content, true);
    var root = null;
    for (var c = frag.firstChild; c; c = c.nextSibling) if (c.nodeType === 1) { root = c; break; }
    return root;
  }
  function collectSlots(el) {
    var slots = {}, nodes = [];
    for (var c = el.firstChild; c; c = c.nextSibling) nodes.push(c);
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i], s = "default";
      if (n.nodeType === 1 && n.hasAttribute("slot")) { s = n.getAttribute("slot"); n.removeAttribute("slot"); }
      (slots[s] = slots[s] || []).push(n);
    }
    return slots;
  }
  function onlyWhitespace(list) {
    for (var i = 0; i < list.length; i++) {
      var n = list[i];
      if (n.nodeType === 1) return false;
      if (n.nodeType === 3 && /\S/.test(n.nodeValue)) return false;
    }
    return true;
  }
  function checkSlot(block, name, slotName, nodes, el) {
    var spec = block.slots && block.slots[slotName];
    if (!spec) {
      if (!onlyWhitespace(nodes)) report(block.slots ? "slot-not-allowed" : "no-slots", "ds-" + name + " has no '" + slotName + "' slot", el);
      return false;
    }
    if (Array.isArray(spec.accepts)) {
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        if (n.nodeType === 3 && !/\S/.test(n.nodeValue)) continue;
        if (n.nodeType === 8) continue;
        var child = n.nodeType === 1 ? (n.getAttribute("data-ds") || (isDsTag(n) ? n.localName.slice(3) : null)) : null;
        if (!child || spec.accepts.indexOf(child) < 0) {
          report("slot-not-allowed", "ds-" + name + " slot '" + slotName + "' accepts " + spec.accepts.join(", "), n.nodeType === 1 ? n : el);
        }
      }
    }
    return true;
  }
  function expandCustom(el) {
    var id = ++seq, reason = el.getAttribute("reason") || "";
    if (!reason) report("custom-without-reason", "ds-custom needs a reason", el);
    var ownerDoc = el.ownerDocument, parent = el.parentNode;
    var start = ownerDoc.createComment("ds-custom#" + id + " reason=\"" + reason.replace(/-->/g, "") + "\"");
    var end = ownerDoc.createComment("/ds-custom#" + id);
    parent.insertBefore(start, el);
    var kids = [];
    while (el.firstChild) { kids.push(el.firstChild); parent.insertBefore(el.firstChild, el); }
    parent.insertBefore(end, el);
    parent.removeChild(el);
    return kids;
  }
  // Expand ONE <ds-name> element. Returns the new root (or null when unknown).
  function expandElement(el, pending) {
    var name = el.localName.slice(3);
    var block = DS.blocks[name];
    if (!block) { report("unknown-block", "<" + el.localName + "> is not a block in this DS", el); el.setAttribute("data-ds-unknown", ""); return null; }
    var tag = el.__dsPreset ? { explicit: el.__dsPreset, pass: [] } : readTag(el, block, name);
    if (el.__dsPreset) for (var i = 0; i < el.attributes.length; i++) {
      var pa = el.attributes[i]; if (pa.name !== "slot" && pa.name.indexOf("data-ds") !== 0) tag.pass.push([pa.name, pa.value]);
    }
    var props = withDefaults(block, tag.explicit);
    checkRequired(block, name, props, el);
    var slots = el.__dsSlots || collectSlots(el);
    var root;
    try { root = templateRoot(name, props, el.ownerDocument); }
    catch (err) { report("template-error", "ds-" + name + ": " + err.message, el); return null; }
    if (!root) { report("template-error", "ds-" + name + " rendered no element", el); return null; }
    var id = ++seq;
    var points = root.querySelectorAll("ds-slot");
    var used = {};
    for (var p = 0; p < points.length; p++) {
      var pt = points[p], sn = pt.getAttribute("name") || "default", content = slots[sn];
      used[sn] = 1;
      var parent = pt.parentNode;
      if (content && !onlyWhitespace(content)) {
        checkSlot(block, name, sn, content, el);
        parent.insertBefore(el.ownerDocument.createComment("ds-slot:" + sn + "#" + id), pt);
        for (var q = 0; q < content.length; q++) parent.insertBefore(content[q], pt);
        parent.insertBefore(el.ownerDocument.createComment("/ds-slot#" + id), pt);
      } else {
        while (pt.firstChild) parent.insertBefore(pt.firstChild, pt);   // fallback content
      }
      parent.removeChild(pt);
    }
    for (var s in slots) if (!used[s] && !onlyWhitespace(slots[s])) checkSlot(block, name, s, slots[s], el);
    for (var k = 0; k < tag.pass.length; k++) {
      var an = tag.pass[k][0], av = tag.pass[k][1];
      if (an === "class") { av.split(/\s+/).forEach(function (c) { if (c) root.classList.add(c); }); }
      else root.setAttribute(an, av);
    }
    root.setAttribute("data-ds", name);
    root.setAttribute("data-ds-i", String(id));
    var pj = propsAttr(tag.explicit);
    if (pj) root.setAttribute("data-ds-props", pj);
    el.parentNode.replaceChild(root, el);
    if (behaviors[name] && behaviors[name].init && pending) pending.push([name, root, props]);
    return root;
  }
  function walk(node, pending) {
    var child = node.firstChild;
    while (child) {
      var next = child.nextSibling;
      if (child.nodeType === 1) {
        if (child.localName === "ds-custom") {
          var kids = expandCustom(child);
          for (var i = 0; i < kids.length; i++) {
            var k = kids[i];
            if (k.nodeType !== 1) continue;
            if (isDsTag(k)) { var r = k.localName === "ds-custom" ? null : expandElement(k, pending); if (r) walk(r, pending); else if (k.parentNode) walk(k, pending); }
            else walk(k, pending);
          }
        } else if (isDsTag(child)) {
          var root = expandElement(child, pending);
          walk(root || child, pending);
        } else if (child.localName !== "template") {
          walk(child, pending);
        }
      }
      child = next;
    }
  }
  var inited = typeof WeakSet === "function" ? new WeakSet() : null;
  function runInits(pending) {
    for (var i = 0; i < pending.length; i++) {
      var p = pending[i];
      if (!p[1].isConnected || (inited && inited.has(p[1]))) continue;
      if (inited) inited.add(p[1]);
      try { behaviors[p[0]].init(p[1], p[2]); } catch (e) { try { console.error("[ds] init " + p[0], e); } catch (_) {} }
    }
  }
  // Markup from DS.html() arrives already expanded, so it never passes through
  // expandElement on the live page. Queue init for any block root in `node`
  // that has an init and has not run it yet.
  function collectInits(node, pending) {
    if (!inited || !node || node.nodeType !== 1) return;
    var list = node.hasAttribute("data-ds") ? [node] : [];
    var more = node.querySelectorAll ? node.querySelectorAll("[data-ds]") : [];
    for (var i = 0; i < more.length; i++) list.push(more[i]);
    for (var j = 0; j < list.length; j++) {
      var name = list[j].getAttribute("data-ds"), b = behaviors[name];
      if (b && b.init && !inited.has(list[j])) pending.push([name, list[j], readProps(list[j])]);
    }
  }
  function expand(container) {
    if (!container) return container;
    var pending = [];
    if (container.nodeType === 1 && isDsTag(container) && container.parentNode) {
      var r = container.localName === "ds-custom" ? null : expandElement(container, pending);
      if (r) { walk(r, pending); runInits(pending); scheduleCheck(); return r; }
    }
    walk(container, pending);
    collectInits(container.nodeType === 1 ? container : null, pending);
    runInits(pending);
    scheduleCheck();
    return container;
  }

  // ── DS.html: synchronous expanded markup for JS builders ───────────────────
  function toNodes(html, ownerDoc) {
    var t = ownerDoc.createElement("template");
    t.innerHTML = html == null ? "" : String(html);
    var frag = ownerDoc.importNode(t.content, true), out = [];
    while (frag.firstChild) out.push(frag.removeChild(frag.firstChild));
    return out;
  }
  function html(name, props, slots) {
    var block = DS.blocks[name];
    if (!block) { report("unknown-block", "DS.html('" + name + "') is not a block in this DS"); return ""; }
    var host = doc.createElement("div");
    var el = doc.createElement("ds-" + name);
    var p = props || {}, pass = {};
    var specs = block.props || {};
    for (var k in p) {
      if (specs[k] || specs[kebab(k)]) continue;
      if (PASSTHROUGH[k] || k.indexOf("data-") === 0 || k.indexOf("aria-") === 0) { pass[k] = p[k]; }
    }
    var real = {};
    for (k in p) if (!pass.hasOwnProperty(k)) real[k] = p[k];
    el.__dsPreset = normalizeProps(block, name, real);
    for (k in pass) if (pass[k] != null && pass[k] !== false) el.setAttribute(k, pass[k] === true ? "" : String(pass[k]));
    var map = {};
    if (typeof slots === "string" || Array.isArray(slots)) slots = { "default": slots };
    for (var s in slots || {}) {
      var v = slots[s];
      map[s] = toNodes(Array.isArray(v) ? v.join("") : v, doc);
    }
    el.__dsSlots = map;
    host.appendChild(el);
    var pending = [];
    var root = expandElement(el, pending);
    if (root) walk(root, pending);
    // Inits are not run here: this copy is detached. They run when the markup
    // lands in the live page (observer, or DS.expand on the container).
    return host.innerHTML;
  }

  // ── serialize: expanded markup -> source form ──────────────────────────────
  function attrString(name, value) { return value === "" ? " " + name : " " + name + "=\"" + escAttr(value) + "\""; }
  function propAttrs(block, explicit) {
    var specs = block.props || {}, out = "";
    for (var k in explicit) {
      if (k === "$omitted") continue;
      var v = explicit[k], t = (specs[k] && specs[k].type) || "string";
      if (t === "boolean") { if (v === true) out += " " + k; else out += attrString(k, "false"); }
      else if (t === "list") out += attrString(k, Array.isArray(v) ? v.join(",") : String(v));
      else if (t === "json") out += attrString(k, JSON.stringify(v));
      else out += attrString(k, String(v));
    }
    return out;
  }
  function templateAttrs(name, props) {
    var info = { attrs: {}, classes: {} };
    try {
      var r = templateRoot(name, props, doc);
      if (r) {
        for (var i = 0; i < r.attributes.length; i++) info.attrs[r.attributes[i].name] = r.attributes[i].value;
        for (var j = 0; j < r.classList.length; j++) info.classes[r.classList[j]] = 1;
      }
    } catch (_) {}
    return info;
  }
  function isStateClass(c) { return /^(is|has|js)-/.test(c); }
  function ownMarkers(root, id) {
    // Returns [{name, nodes:[...]}] for slot regions that belong to instance `id`.
    var regions = [], walker = (root.ownerDocument || doc).createTreeWalker(root, 128 /* SHOW_COMMENT */, null, false), c;
    var reStart = new RegExp("^ds-slot:([\\w-]+)#" + id + "$"), endText = "/ds-slot#" + id;
    while ((c = walker.nextNode())) {
      var m = reStart.exec(c.nodeValue);
      if (!m) continue;
      var nodes = [], n = c.nextSibling;
      while (n && !(n.nodeType === 8 && n.nodeValue === endText)) { nodes.push(n); n = n.nextSibling; }
      regions.push({ name: m[1], nodes: nodes });
    }
    return regions;
  }
  function serializeBlock(el, slotName) {
    var name = el.getAttribute("data-ds"), block = DS.blocks[name], id = el.getAttribute("data-ds-i");
    if (!block || !id) return serializeElement(el, slotName, true);
    var explicit = {};
    try { explicit = JSON.parse(el.getAttribute("data-ds-props") || "{}"); } catch (_) {}
    var tinfo = templateAttrs(name, withDefaults(block, explicit));
    var out = "<ds-" + name + propAttrs(block, explicit);
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i], an = a.name;
      if (an.indexOf("data-ds") === 0 || an === "slot") continue;
      if ((block.props || {})[an] && an !== "class" && an !== "id") continue;
      if (an === "class") {
        var extra = [];
        for (var j = 0; j < el.classList.length; j++) {
          var c = el.classList[j];
          if (!tinfo.classes[c] && !isStateClass(c) && c.indexOf("th-") !== 0) extra.push(c);
        }
        if (extra.length) out += attrString("class", extra.join(" "));
        continue;
      }
      if (STATE_ATTRS[an]) continue;
      if (!(PASSTHROUGH[an] || an.indexOf("data-") === 0 || an.indexOf("aria-") === 0)) continue;
      if (tinfo.attrs[an] === a.value) continue;
      out += attrString(an, a.value);
    }
    if (slotName && slotName !== "default") out += attrString("slot", slotName);
    out += ">";
    var regions = ownMarkers(el, id);
    for (var r = 0; r < regions.length; r++) out += serializeList(regions[r].nodes, regions[r].name);
    return out + "</ds-" + name + ">";
  }
  function serializeElement(el, slotName, plain) {
    var tag = el.localName;
    var out = "<" + tag;
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      if (a.name === "data-ds-i" || a.name === "data-ds-unknown") continue;
      out += attrString(a.name, a.value);
    }
    if (slotName && slotName !== "default") out += attrString("slot", slotName);
    out += ">";
    if (VOID[tag]) return out;
    if (RAW_TEXT[tag]) return out + el.textContent + "</" + tag + ">";
    if (tag === "template") return out + el.innerHTML + "</" + tag + ">";
    return out + serializeList(Array.prototype.slice.call(el.childNodes), null) + "</" + tag + ">";
  }
  function serializeList(nodes, slotName) {
    var out = "";
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.nodeType === 1) out += n.hasAttribute("data-ds") && n.hasAttribute("data-ds-i") ? serializeBlock(n, slotName) : serializeElement(n, slotName);
      else if (n.nodeType === 3) out += n.parentNode && RAW_TEXT[n.parentNode.localName] ? n.nodeValue : escText(n.nodeValue);
      else if (n.nodeType === 8) {
        var v = n.nodeValue, cm = /^ds-custom#(\d+) reason="([^"]*)"$/.exec(v);
        if (cm) {
          var inner = [], j = i + 1, endText = "/ds-custom#" + cm[1];
          while (j < nodes.length && !(nodes[j].nodeType === 8 && nodes[j].nodeValue === endText)) inner.push(nodes[j++]);
          out += "<ds-custom" + attrString("reason", cm[2]) + (slotName && slotName !== "default" ? attrString("slot", slotName) : "") + ">" + serializeList(inner, null) + "</ds-custom>";
          i = j;
          continue;
        }
        if (/^\/?ds-(slot|custom)/.test(v)) continue;   // stray marker
        out += "<!--" + v + "-->";
      }
    }
    return out;
  }
  function serialize(root) {
    if (!root) return "";
    if (root.nodeType === 9) {
      var d = root, dt = "<!DOCTYPE html>";
      if (d.doctype) dt = "<!DOCTYPE " + d.doctype.name + ">";
      return dt + "\n" + serialize(d.documentElement);
    }
    if (root.nodeType === 11) return serializeList(Array.prototype.slice.call(root.childNodes), null);
    var hide = root.querySelector ? root.querySelector("style[data-ds-boot]") : null;
    var out = root.nodeType === 1 && root.hasAttribute("data-ds") && root.hasAttribute("data-ds-i")
      ? serializeBlock(root, null) : serializeList([root], null);
    if (hide) out = out.replace(/<style data-ds-boot[^>]*>[\s\S]*?<\/style>/, "");
    return out.replace(/ class="([^"]*)\bds-ready\b([^"]*)"/, function (m, a, b) {
      var rest = (a + b).trim().replace(/\s+/g, " ");
      return rest ? " class=\"" + rest + "\"" : "";
    });
  }

  // ── DS.update / DS.props ───────────────────────────────────────────────────
  function readProps(root) {
    var name = root && root.getAttribute("data-ds"), block = name && DS.blocks[name];
    if (!block) return null;
    var explicit = {};
    try { explicit = JSON.parse(root.getAttribute("data-ds-props") || "{}"); } catch (_) {}
    delete explicit.$omitted;
    return withDefaults(block, explicit);
  }
  function update(root, next) {
    var name = root.getAttribute("data-ds"), block = DS.blocks[name], id = root.getAttribute("data-ds-i");
    if (!block) return root;
    var explicit = {};
    try { explicit = JSON.parse(root.getAttribute("data-ds-props") || "{}"); } catch (_) {}
    delete explicit.$omitted;
    var add = normalizeProps(block, name, next || {});
    for (var k in add) explicit[k] = add[k];
    var el = root.ownerDocument.createElement("ds-" + name);
    el.__dsPreset = explicit;
    var slots = {}, regions = ownMarkers(root, id);
    for (var r = 0; r < regions.length; r++) slots[regions[r].name] = regions[r].nodes;
    el.__dsSlots = slots;
    var tinfo = templateAttrs(name, withDefaults(block, explicit));
    for (var i = 0; i < root.attributes.length; i++) {
      var a = root.attributes[i];
      if (a.name.indexOf("data-ds") === 0) continue;
      if ((block.props || {})[a.name] && a.name !== "class" && a.name !== "id") continue;
      if (a.name === "class") {
        var extra = [];
        for (var j = 0; j < root.classList.length; j++) if (!tinfo.classes[root.classList[j]] && !isStateClass(root.classList[j])) extra.push(root.classList[j]);
        if (extra.length) el.setAttribute("class", extra.join(" "));
      } else if ((PASSTHROUGH[a.name] || a.name.indexOf("data-") === 0 || a.name.indexOf("aria-") === 0) && tinfo.attrs[a.name] !== a.value) el.setAttribute(a.name, a.value);
    }
    root.parentNode.replaceChild(el, root);
    var pending = [], out = expandElement(el, pending);
    if (out) walk(out, pending);
    runInits(pending);
    return out;
  }

  // ── behaviors, services, events ────────────────────────────────────────────
  function installDelegate(type) {
    if (delegated[type]) return;
    delegated[type] = true;
    doc.addEventListener(type, function (e) {
      var t = e.target && e.target.nodeType === 1 ? e.target : (e.target && e.target.parentElement);
      if (!t || !t.closest) return;
      for (var name in behaviors) {
        var hs = behaviors[name].__byType[type];
        if (!hs) continue;
        var root = t.closest("[data-ds=\"" + name + "\"]");
        if (!root) continue;
        for (var i = 0; i < hs.length; i++) {
          var h = hs[i], match = root;
          if (h.sel) { match = t.closest(h.sel); if (!match || !root.contains(match)) continue; }
          try { h.fn.call(match, e, root, match); } catch (err) { try { console.error("[ds] behavior " + name, err); } catch (_) {} }
        }
      }
    }, !!NON_BUBBLING[type]);
  }
  function behavior(name, def) {
    def = def || {};
    def.__byType = {};
    for (var key in def.on || {}) {
      var sp = key.indexOf(" "), type = sp < 0 ? key : key.slice(0, sp), sel = sp < 0 ? null : key.slice(sp + 1).trim();
      (def.__byType[type] = def.__byType[type] || []).push({ sel: sel, fn: def.on[key] });
      installDelegate(type);
    }
    behaviors[name] = def;
  }
  var BUILTIN = { html: 1, expand: 1, serialize: 1, emit: 1, icon: 1, props: 1, update: 1, behavior: 1, service: 1, ready: 1, manifest: 1, blocks: 1, config: 1, violations: 1, check: 1 };
  function service(name, factory) {
    if (BUILTIN[name]) { report("service-name", "service '" + name + "' clashes with a runtime built-in"); return; }
    try { DS[name] = factory(DS); } catch (e) { try { console.error("[ds] service " + name, e); } catch (_) {} }
  }
  function emit(el, type, detail) {
    var ev;
    try { ev = new CustomEvent(type, { bubbles: true, detail: detail }); }
    catch (_) { ev = doc.createEvent("CustomEvent"); ev.initCustomEvent(type, true, false, detail); }
    el.dispatchEvent(ev);
    return ev;
  }
  function icon(name, opts) {
    opts = opts || {};
    var d = iconData(name, opts.style);
    if (!d) return "";
    var size = opts.size ? " width=\"" + esc(opts.size) + "\" height=\"" + esc(opts.size) + "\"" : "";
    return "<svg class=\"" + esc(opts["class"] || "icon") + "\" viewBox=\"" + esc(d.v) + "\"" + size + " fill=\"currentColor\" aria-hidden=\"true\">" + d.b + "</svg>";
  }

  // ── self-check ─────────────────────────────────────────────────────────────
  var checkTimer = null;
  function scheduleCheck() {
    if (!DS.config.check || !booted) return;
    if (checkTimer) clearTimeout(checkTimer);
    checkTimer = setTimeout(check, 250);
  }
  function check() {
    checkTimer = null;
    if (!doc.body || (doc.documentElement.getAttribute("data-ds-check") === "off")) return DS.violations;
    var roots = {}, replaced = {}, name;
    for (name in DS.blocks) {
      var b = DS.blocks[name];
      if (b.rootClass) roots[b.rootClass] = name;
      (b.replaces || []).forEach(function (t) { replaced[t] = replaced[t] || name; });
    }
    var inCustom = 0;
    var w = doc.createTreeWalker(doc.body, 1 | 128, null, false), n;
    while ((n = w.nextNode())) {
      if (n.nodeType === 8) {
        if (/^ds-custom#/.test(n.nodeValue)) inCustom++;
        else if (/^\/ds-custom#/.test(n.nodeValue)) inCustom = Math.max(0, inCustom - 1);
        continue;
      }
      if (n.hasAttribute("data-ds")) continue;
      if (n.closest("[data-ds-gallery-chrome]")) continue;
      var tg = n.localName, cl = n.classList, hit = null;
      for (var i = 0; i < cl.length; i++) if (roots[cl[i]]) { hit = cl[i]; break; }
      var raw = !inCustom && replaced[tg] && !(tg === "input" && n.type === "hidden");
      if (!hit && !raw) continue;
      // Markup a block's own template produced is DS code (validated at
      // build time). Only page content - outside every block, or placed into
      // a block's slot - can be hand-built.
      if (templateOwned(n)) continue;
      if (hit) report("hand-built-block", "." + hit + " written by hand; use <ds-" + roots[hit] + "> or DS.html('" + roots[hit] + "')" + (inCustom ? " (inside ds-custom)" : ""), n);
      if (raw) report("raw-replaced-element", "raw <" + tg + ">; use <ds-" + replaced[tg] + ">", n);
    }
    return DS.violations;
  }
  // True when `el` was rendered by a block TEMPLATE, false when it is page
  // content (outside every block, or placed into a slot). Walk up the
  // enclosing blocks: if el sits in a slot region of block B, its author is
  // whoever wrote B's tag, so keep climbing; the first enclosing block whose
  // slots do NOT hold el is the template that rendered it.
  function blockAncestor(n) {
    n = n.parentNode;
    while (n && n.nodeType === 1 && !n.hasAttribute("data-ds")) n = n.parentNode;
    return n && n.nodeType === 1 ? n : null;
  }
  function inSlotOf(el, root) {
    var id = root.getAttribute("data-ds-i");
    if (!id) return false;
    var startRe = new RegExp("^ds-slot:[\\w-]+#" + id + "$"), endText = "/ds-slot#" + id;
    for (var node = el; node && node !== root; node = node.parentNode) {
      for (var sib = node.previousSibling; sib; sib = sib.previousSibling) {
        if (sib.nodeType !== 8) continue;
        if (sib.nodeValue === endText) break;
        if (startRe.test(sib.nodeValue)) return true;
      }
    }
    return false;
  }
  function templateOwned(el) {
    for (var root = blockAncestor(el); root; root = blockAncestor(root)) {
      if (!inSlotOf(el, root)) return true;
    }
    return false;
  }

  // ── boot ───────────────────────────────────────────────────────────────────
  function rightmostLeaf() {
    var n = doc.documentElement;
    while (n && n.lastChild) n = n.lastChild;
    return n;
  }
  var pendingTags = [];
  function onMutations(records) {
    if (!booted) return;
    var pending = [];
    if (!ready) {
      // still parsing: expand tags whose end tag has been parsed (they no
      // longer contain the parser's insertion point) so inline scripts that
      // run mid-parse already see expanded markup.
      for (var r = 0; r < records.length; r++) {
        var added = records[r].addedNodes;
        for (var a = 0; a < added.length; a++) if (isDsTag(added[a])) pendingTags.push(added[a]);
        else if (added[a].nodeType === 1 && added[a].querySelector) {
          var inner = added[a].getElementsByTagName("*");
          for (var x = 0; x < inner.length; x++) if (isDsTag(inner[x])) pendingTags.push(inner[x]);
        }
      }
      var leaf = rightmostLeaf(), keep = [];
      for (var i = 0; i < pendingTags.length; i++) {
        var el = pendingTags[i];
        if (!el.isConnected || !isDsTag(el)) continue;
        if (el.contains(leaf)) { keep.push(el); continue; }
        var outer = el.parentNode, nested = false;
        while (outer && outer.nodeType === 1) { if (isDsTag(outer)) { nested = true; break; } outer = outer.parentNode; }
        if (nested) { keep.push(el); continue; }
        if (el.localName === "ds-custom") expandCustomIn(el, pending);
        else { var rr = expandElement(el, pending); if (rr) walk(rr, pending); }
      }
      pendingTags = keep;
    } else {
      for (var r2 = 0; r2 < records.length; r2++) {
        var add2 = records[r2].addedNodes;
        for (var b = 0; b < add2.length; b++) {
          var nd = add2[b];
          if (nd.nodeType !== 1 || !nd.isConnected) continue;
          if (isDsTag(nd)) {
            if (nd.localName === "ds-custom") expandCustomIn(nd, pending);
            else { var r3 = expandElement(nd, pending); if (r3) walk(r3, pending); }
          } else if (nd.getElementsByTagName) {
            var has = false, all = nd.getElementsByTagName("*");
            for (var y = 0; y < all.length; y++) if (isDsTag(all[y])) { has = true; break; }
            if (has) walk(nd, pending);
            collectInits(nd, pending);
          }
        }
      }
    }
    runInits(pending);
    if (ready) scheduleCheck();
  }
  function expandCustomIn(el, pending) {
    var kids = expandCustom(el);
    for (var i = 0; i < kids.length; i++) if (kids[i].nodeType === 1) {
      if (isDsTag(kids[i])) { var r = kids[i].localName === "ds-custom" ? null : expandElement(kids[i], pending); if (r) walk(r, pending); }
      else walk(kids[i], pending);
    }
  }
  function finish() {
    if (ready) return;
    var pending = [];
    try { if (doc.body) { walk(doc.body, pending); collectInits(doc.body, pending); } runInits(pending); }
    catch (e) { try { console.error("[ds] expand failed", e); } catch (_) {} }
    ready = true;
    pendingTags = [];
    doc.documentElement.classList.add("ds-ready");
    var hide = doc.querySelector("style[data-ds-boot]");
    if (hide) hide.parentNode.removeChild(hide);
    for (var i = 0; i < readyFns.length; i++) { try { readyFns[i](DS); } catch (e2) { try { console.error(e2); } catch (_) {} } }
    readyFns = [];
    scheduleCheck();
  }
  function boot() {
    if (booted) return;
    booted = true;
    if (!doc) return;
    var observer = new MutationObserver(onMutations);
    observer.observe(doc.documentElement, { childList: true, subtree: true });
    if (doc.readyState === "loading") {
      var st = doc.createElement("style");
      st.setAttribute("data-ds-boot", "");
      st.textContent = "html:not(.ds-ready) body{visibility:hidden}";
      (doc.head || doc.documentElement).appendChild(st);
      doc.addEventListener("DOMContentLoaded", finish);
      setTimeout(finish, 4000);   // fail-safe: never leave the page hidden
    } else finish();
  }

  DS.__load = function (manifest) {
    DS.manifest = manifest;
    DS.blocks = manifest.blocks || {};
  };
  DS.__boot = boot;
  DS.html = html;
  DS.expand = expand;
  DS.serialize = serialize;
  DS.emit = emit;
  DS.icon = icon;
  DS.props = readProps;
  DS.update = update;
  DS.behavior = behavior;
  DS.service = service;
  DS.check = function () { return check(); };
  DS.ready = function (fn) { if (ready) fn(DS); else readyFns.push(fn); };
  global.DS = DS;
})(typeof window !== "undefined" ? window : this);
