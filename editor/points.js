/* Point tool store - window.WovenPoints.

   A "point" is a numbered orange badge the user drops on a canvas node, a
   whiteboard item, or one element inside an html / prototype page (canvas
   node iframe or the Preview viewer). Points belong to a CHAT THREAD: the
   composer shows each one as an inline [n] chip, and every send carries a
   <pointed-targets> block that spells out exactly what each number means.

   Plain JS, no React: the composer (chips), the canvas (badges, hit-testing)
   and the preview viewer (badges, hit-testing) all read and write the same
   store and re-render on its events, so none of them has to thread props
   through the others.

   Thread keys: the run id of the open thread, or "draft" for the new-chat
   shell (moved onto the real run id the moment it spawns, see migrate()).

   Numbering: the lowest number free in the thread. A number that was SENT is
   never handed out again, even after its point is removed (kept in `tomb`),
   so an earlier "[2]" in the transcript keeps meaning what the agent read.

   Persistence: localStorage per project + thread, the 40 most recently
   touched threads kept. Skipped under ?embed=1, which shares localStorage
   with the outer editor. Only SENT points are stored: an unsent point lives
   exactly as long as its chip in the composer draft, and the draft itself is
   not kept across a reload, so neither is the point. */
(function () {
  "use strict";

  var PREFIX = "th.points.v1.";
  var MAX_THREADS = 40;
  var EMBED = false;
  try { EMBED = new URLSearchParams(location.search).get("embed") === "1"; } catch (e) {}

  function project() {
    try {
      if (window.__TH_PROJECT) return window.__TH_PROJECT;
      return new URL(location.href).searchParams.get("project") || "default";
    } catch (e) { return "default"; }
  }
  function storeKey(tk) { return PREFIX + project() + "." + tk; }
  function indexKey() { return PREFIX + project() + ".__index"; }

  // threadKey -> { points: [...], tomb: [n...] }, scoped by project through
  // the cache key so a project switch never shows another project's points.
  var cache = {};
  function cacheKey(tk) { return project() + "\u0000" + tk; }

  function load(tk) {
    var ck = cacheKey(tk);
    if (cache[ck]) return cache[ck];
    var rec = { points: [], tomb: [] };
    if (!EMBED) {
      try {
        var raw = localStorage.getItem(storeKey(tk));
        if (raw) {
          var j = JSON.parse(raw);
          if (j && Array.isArray(j.points)) rec.points = j.points.filter(function (p) { return p && p.n > 0 && p.sent; });
          if (j && Array.isArray(j.tomb)) rec.tomb = j.tomb.filter(function (n) { return n > 0; });
        }
      } catch (e) { /* unreadable - start empty */ }
    }
    cache[ck] = rec;
    return rec;
  }

  function save(tk) {
    if (EMBED || !tk) return;
    var rec = load(tk);
    var sent = rec.points.filter(function (p) { return p.sent; });
    try {
      if (!sent.length && !rec.tomb.length) localStorage.removeItem(storeKey(tk));
      else localStorage.setItem(storeKey(tk), JSON.stringify({ points: sent, tomb: rec.tomb }));
    } catch (e) { return; }
    // Touch the per-project index and prune the oldest threads past the cap.
    try {
      var idx = {};
      try { idx = JSON.parse(localStorage.getItem(indexKey()) || "{}") || {}; } catch (e2) { idx = {}; }
      if (sent.length || rec.tomb.length) idx[tk] = Date.now(); else delete idx[tk];
      var keys = Object.keys(idx).sort(function (a, b) { return idx[b] - idx[a]; });
      for (var i = MAX_THREADS; i < keys.length; i++) {
        try { localStorage.removeItem(storeKey(keys[i])); } catch (e3) {}
        delete cache[cacheKey(keys[i])];
        delete idx[keys[i]];
      }
      localStorage.setItem(indexKey(), JSON.stringify(idx));
    } catch (e4) { /* quota or disabled storage - the in-memory copy still works */ }
  }

  var listeners = [];
  function emit(evt) {
    rev++;
    var ls = listeners.slice();
    for (var i = 0; i < ls.length; i++) {
      try { ls[i](evt); } catch (e) { /* one bad listener must not stop the rest */ }
    }
  }
  var rev = 0;

  function sortByN(a, b) { return a.n - b.n; }

  function nextN(tk) {
    var rec = load(tk);
    var used = {};
    rec.points.forEach(function (p) { used[p.n] = true; });
    rec.tomb.forEach(function (n) { used[n] = true; });
    var n = 1;
    while (used[n]) n++;
    return n;
  }

  function list(tk) {
    if (!tk) return [];
    return load(tk).points.slice().sort(sortByN);
  }

  function get(tk, n) {
    if (!tk) return null;
    var pts = load(tk).points;
    for (var i = 0; i < pts.length; i++) if (pts[i].n === n) return pts[i];
    return null;
  }

  function add(tk, data) {
    if (!tk || !data) return null;
    var rec = load(tk);
    var p = {};
    for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) p[k] = data[k];
    p.n = nextN(tk);
    p.id = "pt-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    p.sent = false;
    p.createdAt = Date.now();
    rec.points = rec.points.concat([p]);
    save(tk);
    emit({ type: "added", threadKey: tk, point: p });
    return p;
  }

  // Removing a sent point reserves its number; an unsent one frees it.
  function remove(tk, n) {
    if (!tk) return false;
    var rec = load(tk);
    var p = get(tk, n);
    if (!p) return false;
    rec.points = rec.points.filter(function (x) { return x.n !== n; });
    if (p.sent && rec.tomb.indexOf(n) < 0) rec.tomb = rec.tomb.concat([n]);
    save(tk);
    emit({ type: "removed", threadKey: tk, n: n, point: p });
    return true;
  }

  // Pointing at a target that already has a point names that point again:
  // the composer gets the same "added" event and inserts its chip.
  function reference(tk, n) {
    var p = get(tk, n);
    if (!p) return null;
    emit({ type: "added", threadKey: tk, point: p, existing: true });
    return p;
  }

  function removeIfUnsent(tk, n) {
    var p = get(tk, n);
    if (!p || p.sent) return false;
    return remove(tk, n);
  }

  // Drop every unsent point of a thread that the composer draft no longer
  // names (keep: a Set of numbers still chipped). The composer calls it when
  // it mounts (its draft starts empty), unmounts (the draft is lost) and
  // leaves a thread, so no badge outlives its chip.
  function pruneUnsent(tk, keep) {
    if (!tk) return;
    var rec = load(tk);
    var gone = rec.points.filter(function (p) { return !p.sent && !(keep && keep.has(p.n)); });
    if (!gone.length) return;
    rec.points = rec.points.filter(function (p) { return gone.indexOf(p) < 0; });
    save(tk);
    for (var i = 0; i < gone.length; i++) emit({ type: "removed", threadKey: tk, n: gone[i].n, point: gone[i] });
  }

  function markSent(tk, ns) {
    if (!tk || !ns || !ns.length) return;
    var rec = load(tk);
    var changed = false;
    rec.points = rec.points.map(function (p) {
      if (ns.indexOf(p.n) < 0 || p.sent) return p;
      changed = true;
      var q = {};
      for (var k in p) if (Object.prototype.hasOwnProperty.call(p, k)) q[k] = p[k];
      q.sent = true;
      return q;
    });
    if (!changed) return;
    save(tk);
    emit({ type: "sent", threadKey: tk, ns: ns.slice() });
  }

  // The canvas / preview mark a point lost when its element no longer
  // resolves on the page, so the badge dims and the agent block says so.
  // Emits only on an actual flip, so a re-measure pass costs nothing.
  function setLost(tk, n, lost) {
    var rec = load(tk);
    var changed = false;
    rec.points = rec.points.map(function (p) {
      if (p.n !== n || !!p.lost === !!lost) return p;
      changed = true;
      var q = {};
      for (var k in p) if (Object.prototype.hasOwnProperty.call(p, k)) q[k] = p[k];
      if (lost) q.lost = true; else delete q.lost;
      return q;
    });
    if (!changed) return;
    save(tk);
    emit({ type: "lost", threadKey: tk, n: n, lost: !!lost });
  }

  // The new-chat shell ("draft") became a real run: its points move over.
  function migrate(from, to) {
    if (!from || !to || from === to) return;
    var src = load(from);
    if (!src.points.length && !src.tomb.length) return;
    var dst = load(to);
    var taken = {};
    dst.points.forEach(function (p) { taken[p.n] = true; });
    dst.tomb.forEach(function (n) { taken[n] = true; });
    src.points.forEach(function (p) { if (!taken[p.n]) dst.points = dst.points.concat([p]); });
    src.tomb.forEach(function (n) { if (dst.tomb.indexOf(n) < 0) dst.tomb = dst.tomb.concat([n]); });
    src.points = [];
    src.tomb = [];
    save(from);
    save(to);
    if (activeKey === from) activeKey = to;
    emit({ type: "migrated", from: from, to: to });
  }

  // ── Point mode (armed / one-shot) ───────────────────────────────────────
  // armed:    clicks on the canvas / preview create points.
  // oneShot:  armed by typing "=" - the first point replaces that token and
  //           disarms; the toolbar button arms with oneShot false.
  // insertAt: index of the "=" in the composer text (one-shot only).
  var modeState = { armed: false, oneShot: false, threadKey: null, insertAt: -1 };
  function mode() { return modeState; }
  function arm(opts) {
    opts = opts || {};
    if (!opts.threadKey) return;
    modeState = {
      armed: true,
      oneShot: !!opts.oneShot,
      threadKey: opts.threadKey,
      insertAt: typeof opts.insertAt === "number" ? opts.insertAt : -1,
    };
    emit({ type: "mode", mode: modeState });
  }
  function disarm() {
    if (!modeState.armed) return;
    modeState = { armed: false, oneShot: false, threadKey: null, insertAt: -1 };
    emit({ type: "mode", mode: modeState });
  }

  // ── Active thread (the one whose badges the canvas / preview draw) ──────
  var activeKey = null;
  function setActive(tk) {
    tk = tk || null;
    if (tk === activeKey) return;
    activeKey = tk;
    if (modeState.armed && modeState.threadKey !== tk) disarm();
    emit({ type: "active", threadKey: tk });
  }
  function active() { return activeKey; }

  function subscribe(fn) {
    listeners.push(fn);
    return function () { listeners = listeners.filter(function (f) { return f !== fn; }); };
  }

  // ── Element anchors ─────────────────────────────────────────────────────
  // Same fingerprint the data-th-patch replay uses (tag + editor-class-free
  // classes + digit-free text), so a point survives the same re-renders a
  // patch op does.
  function fpText(n) {
    return (n.textContent || "").replace(/[\d%.,]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 64);
  }
  function fpOk(n, fp) {
    if (!n || !n.tagName || !fp) return false;
    if (fp.tag && n.tagName.toLowerCase() !== fp.tag) return false;
    if (fp.cls) {
      var cl = (typeof n.className === "string" ? n.className : "").trim().split(/\s+/)
        .filter(function (c) { return c && c.indexOf("th-pick-") !== 0; }).sort().join(" ");
      if (cl !== fp.cls) return false;
    }
    if (fp.text && fpText(n) !== fp.text) return false;
    return true;
  }
  // Resolution order mirrors the patch replay's resolveTarget: the selector
  // when the fingerprint agrees, else a unique fingerprint match.
  function resolve(doc, anchor) {
    if (!doc || !anchor) return null;
    var el = null;
    if (anchor.selector) {
      try { el = doc.querySelector(anchor.selector); } catch (e) { el = null; }
    }
    if (el && (!anchor.fp || fpOk(el, anchor.fp))) return el;
    if (!anchor.fp || !doc.querySelectorAll) return null;
    var cands;
    try { cands = doc.querySelectorAll(anchor.fp.tag || "*"); } catch (e) { return null; }
    var match = null;
    for (var i = 0; i < cands.length; i++) {
      if (fpOk(cands[i], anchor.fp)) {
        if (match) return null;   // ambiguous - better lost than wrong
        match = cands[i];
      }
    }
    return match;
  }

  // ── The agent block ─────────────────────────────────────────────────────
  function q(s) { return "\"" + String(s || "").replace(/\s+/g, " ").trim() + "\""; }
  function describe(p) {
    var lines = [];
    if (p.kind === "element") {
      var where = p.page || "an unknown page";
      var host = p.nodeId ? ", inside canvas node " + p.nodeId + (p.nodeTitle ? " (" + q(p.nodeTitle) + ")" : "") : ", in the Preview viewer";
      lines.push("[" + p.n + "] element on " + where + host);
      var a = p.anchor || {};
      if (a.selector) lines.push("    selector: " + a.selector);
      var tagLine = a.snippet ? "    element: " + a.snippet : "";
      if (a.text) tagLine += (tagLine ? "  text: " : "    text: ") + q(a.text);
      if (tagLine) lines.push(tagLine);
      if (p.lost) lines.push("    no longer found on the page, last seen as " + (a.snippet || a.label || "the element above"));
    } else if (p.kind === "wb") {
      lines.push("[" + p.n + "] whiteboard " + (p.wbType || "item") + " " + p.wbId + (p.wbText ? ": " + q(p.wbText) : ""));
    } else {
      lines.push("[" + p.n + "] canvas node " + p.nodeId + " (" + (p.nodeTitle ? q(p.nodeTitle) + ", " : "") + (p.nodeKind || "node") + ")"
        + (p.page ? ", showing " + p.page : ""));
    }
    return lines.join("\n");
  }
  function formatPointedTargets(points) {
    if (!points || !points.length) return "";
    var sorted = points.slice().sort(sortByN);
    var ns = sorted.map(function (p) { return "[" + p.n + "]"; }).join(" ");
    return "<pointed-targets>\n"
      + sorted.map(describe).join("\n")
      + "\nIn the message, " + ns + " point" + (sorted.length === 1 ? "s" : "") + " at exactly "
      + (sorted.length === 1 ? "this target" : "these targets")
      + ". Keep the change scoped to " + (sorted.length === 1 ? "it" : "them") + ".\n"
      + "</pointed-targets>\n\n";
  }

  // Short "{label}  {where}" pair the menu rows, chip popover and badge
  // tooltip show next to the number.
  function labelOf(p) {
    if (!p) return "";
    if (p.kind === "element") return (p.anchor && p.anchor.label) || "element";
    if (p.kind === "wb") return p.wbText ? String(p.wbText).replace(/\s+/g, " ").trim().slice(0, 40) : (p.wbType || "item");
    return p.nodeTitle || p.nodeId || "node";
  }
  function whereOf(p) {
    if (!p) return "";
    if (p.kind === "element") return p.page ? p.page.split("/").pop() : "page";
    if (p.kind === "wb") return p.wbType || "whiteboard";
    return (p.nodeKind || "") + " node";
  }

  window.WovenPoints = {
    subscribe: subscribe,
    rev: function () { return rev; },
    list: list,
    get: get,
    add: add,
    remove: remove,
    reference: reference,
    removeIfUnsent: removeIfUnsent,
    pruneUnsent: pruneUnsent,
    markSent: markSent,
    setLost: setLost,
    migrate: migrate,
    nextN: nextN,
    mode: mode,
    arm: arm,
    disarm: disarm,
    setActive: setActive,
    active: active,
    resolve: resolve,
    fpOk: fpOk,
    formatPointedTargets: formatPointedTargets,
    labelOf: labelOf,
    whereOf: whereOf,
  };
})();
