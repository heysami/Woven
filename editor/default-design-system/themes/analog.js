/* themes/analog.js - the live "analog" halftone runtime.
   ==========================================================================
   Activates on <html data-theme="analog">. For each brand surface (side nav,
   filled cards/hero, primary buttons) it mounts a per-element <canvas> child
   and paints a HALFTONE GRADIENT into it: a tonal ramp screened into dots whose
   SIZE is varied per-cell by grain mixed INTO the tone before screening (so the
   dots read hand-printed, not a mechanical grid - and the grain is not a layer
   on top). Tones run from --analog-start (light) to --analog-end (ink), so the
   surfaces stay light and text stays readable.

   Per-element canvas (not one fullscreen canvas) on purpose: a fixed fullscreen
   canvas vanishes inside the editor's preview iframe; a canvas CHILD of each
   chrome element survives it. Mirrors the glassmorphism.js architecture, minus
   the rAF loop / page capture - the halftone is static, so we only redraw on
   resize, DPR change, and scheme change.

   Tunable per surface via the CONFIGS below (the values the design tuner
   produced). No bake step - edit a number, reload, see it.
   ========================================================================== */
(function () {
  "use strict";

  var ATTR = "analog";

  // The two tuned recipes. lo/hi = tone (dot density) at the ramp ends; p0/p1 =
  // where along the surface the ramp lives (0..1); gAng = gradient direction
  // (deg); scrAng = dot-screen angle (deg); cell = dot pitch (px); grain = how
  // much the per-cell tone (and thus dot size) jitters.
  var NAV = { lo: 0, hi: 0.15, p0: 0.46, p1: 1, gAng: 65, scrAng: 12, cell: 3, grain: 0.35 };
  var BTN = { lo: 0, hi: 0.15, p0: 0.74, p1: 1, gAng: 30, scrAng: 12, cell: 3, grain: 0.35 };

  // selector -> recipe. Big tonal surfaces use NAV; compact brand controls BTN.
  var TARGETS = [
    { sel: ".sidebar", cfg: NAV },
    // Filled cards + the landing CTA band are brand-gradient surfaces; give them
    // the BUTTON profile (corner halftone accent) rather than the full nav ramp.
    { sel: ".card--filled, .lp-cta, .stat-hero--brand", cfg: BTN },
    { sel: ".btn--primary, .btn-split__caret", cfg: BTN },
  ];

  var DPR = Math.min(2, window.devicePixelRatio || 1);
  var units = [];            // { el, cv, ctx, cfg, ro }
  var mounted = false;
  var resyncTimer = 0;
  var _probe = null;

  function isOn() { return document.documentElement.getAttribute("data-theme") === ATTR; }

  // Resolve any CSS color string (hex / rgb() / token value) to [r,g,b] via the
  // canvas's own normaliser, so we don't hand-parse hsl()/named colors.
  function toRGB(str, fallback) {
    if (!_probe) _probe = document.createElement("canvas").getContext("2d");
    try {
      _probe.fillStyle = "#000";
      _probe.fillStyle = str;
      var v = _probe.fillStyle;            // normalised to #rrggbb or rgb(...)
      if (v[0] === "#") return [parseInt(v.substr(1, 2), 16), parseInt(v.substr(3, 2), 16), parseInt(v.substr(5, 2), 16)];
      var m = v.match(/(\d+(\.\d+)?)/g);
      if (m) return [+m[0], +m[1], +m[2]];
    } catch (e) {}
    return fallback;
  }

  function colors() {
    var cs = getComputedStyle(document.documentElement);
    function tok(n, f) { var x = cs.getPropertyValue(n).trim(); return x || f; }
    return {
      start: tok("--analog-start", tok("--primary-50", "#eef2fd")),
      end: tok("--analog-end", tok("--primary-900", "#1a2e78")),
    };
  }

  // deterministic per-cell pseudo-random in [0,1) - same grid every redraw
  function hash(i, j) { var s = Math.sin(i * 127.1 + j * 311.7) * 43758.5453; return s - Math.floor(s); }

  function paint(u, col) {
    var el = u.el, ctx = u.ctx, cfg = u.cfg;
    var w = el.clientWidth, h = el.clientHeight;
    if (w <= 0 || h <= 0) return;
    var cv = u.cv;
    if (cv.width !== Math.round(w * DPR) || cv.height !== Math.round(h * DPR)) {
      cv.width = Math.round(w * DPR); cv.height = Math.round(h * DPR);
    }
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Clip the texture to the host's rounded-rect. CSS `border-radius:inherit`
    // on a <canvas> does NOT reliably clip the drawn bitmap (it renders as a
    // rectangle - the dot field showed square corners on pill buttons), so we
    // clip the 2D context explicitly to the computed corner radius.
    var rad = radiusOf(el, w, h);
    ctx.save();
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(0, 0, w, h, rad);
    else roundRectPath(ctx, 0, 0, w, h, rad);
    ctx.clip();

    var start = toRGB(col.start, [238, 242, 253]);
    var end = toRGB(col.end, [26, 46, 120]);
    ctx.fillStyle = "rgb(" + start[0] + "," + start[1] + "," + start[2] + ")";
    ctx.fillRect(0, 0, w, h);
    var ink = end[0] + "," + end[1] + "," + end[2];

    var ang = cfg.scrAng * Math.PI / 180, cs = Math.cos(ang), sn = Math.sin(ang);
    var gr = cfg.gAng * Math.PI / 180, dx = Math.cos(gr), dy = Math.sin(gr);
    var pmin = Math.min(0, dx) + Math.min(0, dy), prange = (Math.max(0, dx) + Math.max(0, dy)) - pmin || 1;
    var span = Math.max(0.001, cfg.p1 - cfg.p0);
    var cell = cfg.cell, R = Math.ceil((w + h) / cell);

    ctx.beginPath();
    for (var i = -R; i < R; i++) {
      for (var j = -R; j < R; j++) {
        var rx = i * cell, ry = j * cell;
        var sx = rx * cs - ry * sn, sy = rx * sn + ry * cs;
        if (sx < -cell || sy < -cell || sx > w + cell || sy > h + cell) continue;
        var pos = ((sx / w) * dx + (sy / h) * dy - pmin) / prange;
        var ramp = Math.min(1, Math.max(0, (pos - cfg.p0) / span));
        var base = cfg.lo + (cfg.hi - cfg.lo) * ramp;
        var gate = 4 * base * (1 - base);
        var t = base + cfg.grain * gate * (hash(i, j) * 2 - 1);
        if (t < 0) t = 0; else if (t > 1) t = 1;
        var r = Math.sqrt(t) * cell * 0.72;
        if (r <= 0.2) continue;
        ctx.moveTo(sx + r, sy);
        ctx.arc(sx, sy, r, 0, 6.2832);
      }
    }
    ctx.fillStyle = "rgb(" + ink + ")";
    ctx.fill();
    ctx.restore();
  }

  // Resolve the host's rendered corner radius (px), clamped to a pill, so the
  // canvas clip follows the same shape as the button/card/rail.
  function radiusOf(el, w, h) {
    var s = getComputedStyle(el).borderTopLeftRadius || "0";
    var px = parseFloat(s) || 0;
    if (/%\s*$/.test(s)) px = (parseFloat(s) / 100) * Math.min(w, h);
    return Math.max(0, Math.min(px, Math.min(w, h) / 2));
  }

  function roundRectPath(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function makeUnit(el, cfg, col) {
    var cv = document.createElement("canvas");
    cv.className = "analog-tex";
    cv.setAttribute("aria-hidden", "true");
    var s = cv.style;
    s.position = "absolute"; s.left = "0"; s.top = "0"; s.width = "100%"; s.height = "100%";
    s.pointerEvents = "none"; s.zIndex = "-1"; s.borderRadius = "inherit";
    // Host establishes a stacking context (isolate) so the z-index:-1 texture
    // sits ABOVE the host background but BELOW all content - including text-only
    // buttons that have no element child to bump above a z-index:0 layer.
    var cssPos = getComputedStyle(el).position;
    if (cssPos === "static") el.style.position = "relative";
    el.style.isolation = "isolate";   // contain the z-index:-1 texture above the host bg
    el.insertBefore(cv, el.firstChild);
    var u = { el: el, cv: cv, ctx: cv.getContext("2d"), cfg: cfg };
    paint(u, col);
    try { u.ro = new ResizeObserver(function () { paint(u, colors()); }); u.ro.observe(el); } catch (e) {}
    return u;
  }

  function destroyUnit(u) {
    try { u.ro && u.ro.disconnect(); } catch (e) {}
    try { u.cv.parentNode && u.cv.parentNode.removeChild(u.cv); } catch (e) {}
  }

  function syncUnits() {
    if (!isOn()) return;
    var col = colors();
    var seen = [];
    for (var t = 0; t < TARGETS.length; t++) {
      var els = document.querySelectorAll(TARGETS[t].sel);
      for (var k = 0; k < els.length; k++) {
        var el = els[k];
        if (el.querySelector(":scope > .analog-tex")) { seen.push(el); continue; }
        units.push(makeUnit(el, TARGETS[t].cfg, col));
        seen.push(el);
      }
    }
    // drop units whose host left the DOM
    for (var i = units.length - 1; i >= 0; i--) {
      if (!document.contains(units[i].el)) { destroyUnit(units[i]); units.splice(i, 1); }
    }
  }

  function repaintAll() { var col = colors(); for (var i = 0; i < units.length; i++) paint(units[i], col); }

  function scheduleResync() { clearTimeout(resyncTimer); resyncTimer = setTimeout(syncUnits, 150); }
  function onResize() { DPR = Math.min(2, window.devicePixelRatio || 1); repaintAll(); }

  var mo = null, bodyMo = null;
  function mount() {
    if (mounted) { syncUnits(); repaintAll(); return; }
    mounted = true;
    syncUnits();
    window.addEventListener("resize", onResize, { passive: true });
    try { bodyMo = new MutationObserver(scheduleResync); bodyMo.observe(document.body, { childList: true, subtree: true }); } catch (e) {}
  }

  function teardown() {
    if (!mounted) return;
    mounted = false;
    window.removeEventListener("resize", onResize);
    try { bodyMo && bodyMo.disconnect(); } catch (e) {}
    for (var i = 0; i < units.length; i++) destroyUnit(units[i]);
    units = [];
  }

  function sync() { if (isOn()) mount(); else teardown(); }

  // The customizer re-reads tokens / flips scheme by injecting CSS; let it ask
  // us to re-read colors and repaint (mirrors window.__renderTokenDocs).
  window.__analog = { refresh: function () { if (isOn()) { syncUnits(); repaintAll(); } } };

  try { new MutationObserver(sync).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] }); } catch (e) {}
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", sync); else sync();
})();
