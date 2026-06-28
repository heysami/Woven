/* ───────────────────────────────────────────────────────────────────────────
   Woven instant tooltips for tool-iframe chrome.

   Native `title` tooltips are slow (~1s), can fail to appear, and - worse for us
   - get CLIPPED by a panel/toolbar that has `overflow:auto` (e.g. the floating
   icon toolbar). This replaces them with a custom tooltip that:
     • shows INSTANTLY on hover,
     • is appended to <body> as position:fixed, so it escapes any panel overflow,
     • flips to the other side if it would run off the viewport edge.

   It adopts every element that has a `title`, moves the text to `data-th-tip`
   (and mirrors it to `aria-label` for screen readers), and removes `title` so the
   native delayed tooltip never fires. A MutationObserver adopts buttons that
   tools build dynamically (voxel/material/pixel inspectors, etc.).

   Drop-in: <script src="/editor/tools/_shared/tooltip.js" defer></script>
   The #wv-tip styling lives in _shared/woven-theme.css.
   ─────────────────────────────────────────────────────────────────────────── */
(function () {
  "use strict";
  if (window.__wvTipInstalled) return;
  window.__wvTipInstalled = true;

  function adoptEl(el) {
    if (!el || el.nodeType !== 1) return;
    const t = el.getAttribute && el.getAttribute("title");
    if (t == null || t === "") return;
    el.setAttribute("data-th-tip", t);
    if (!el.hasAttribute("aria-label")) el.setAttribute("aria-label", t);
    el.removeAttribute("title");
  }
  function adoptTree(root) {
    if (!root || !root.querySelectorAll) return;
    adoptEl(root);
    root.querySelectorAll("[title]").forEach(adoptEl);
  }

  let tip = null;
  function ensureTip() {
    if (!tip) {
      tip = document.createElement("div");
      tip.id = "wv-tip";
      (document.body || document.documentElement).appendChild(tip);
    }
    return tip;
  }
  function show(el) {
    const text = el.getAttribute("data-th-tip");
    if (!text) return;
    const d = ensureTip();
    d.textContent = text;
    d.style.display = "block";
    const r = el.getBoundingClientRect();
    const w = d.offsetWidth, h = d.offsetHeight;
    // Default: to the RIGHT of the element (vertical toolbars sit at the edge).
    let left = r.right + 8;
    if (left + w > window.innerWidth - 4) left = r.left - 8 - w; // flip left
    if (left < 4) left = 4;
    let top = r.top + r.height / 2 - h / 2;
    top = Math.max(4, Math.min(top, window.innerHeight - h - 4));
    d.style.left = left + "px";
    d.style.top = top + "px";
  }
  function hide() { if (tip) tip.style.display = "none"; }

  document.addEventListener("mouseover", (e) => {
    const el = e.target.closest && e.target.closest("[data-th-tip]");
    if (el) show(el);
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest && e.target.closest("[data-th-tip]")) hide();
  });
  document.addEventListener("mousedown", hide, true);
  window.addEventListener("blur", hide);

  function init() {
    adoptTree(document);
    const mo = new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === "attributes" && m.target.getAttribute("title")) { adoptEl(m.target); continue; }
        m.addedNodes && m.addedNodes.forEach(adoptTree);
      }
    });
    mo.observe(document.body || document.documentElement, {
      childList: true, subtree: true, attributes: true, attributeFilter: ["title"],
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

/* ── Slider fill ─────────────────────────────────────────────────────────────
   The Woven slider is a slim custom track whose teal fill is driven by --wv-fill
   (Chrome can't auto-fill a custom track). Set it on every <input type=range> so
   every tool gets the reference look with zero per-control wiring. */
(function () {
  function setFill(el) {
    if (!el || el.type !== "range") return;
    var min = parseFloat(el.min); if (isNaN(min)) min = 0;
    var max = parseFloat(el.max); if (isNaN(max)) max = 100;
    var v = parseFloat(el.value); if (isNaN(v)) v = min;
    var pct = max > min ? ((v - min) / (max - min)) * 100 : 0;
    el.style.setProperty("--wv-fill", Math.max(0, Math.min(100, pct)) + "%");
  }
  function scan() {
    var list = document.querySelectorAll('input[type="range"]');
    for (var i = 0; i < list.length; i++) setFill(list[i]);
  }
  document.addEventListener("input", function (e) { if (e.target && e.target.type === "range") setFill(e.target); }, true);
  document.addEventListener("change", function (e) { if (e.target && e.target.type === "range") setFill(e.target); }, true);
  var pending = 0;
  function schedule() { if (pending) return; pending = setTimeout(function () { pending = 0; scan(); }, 120); }
  function initFill() {
    scan();
    try { new MutationObserver(schedule).observe(document.body || document.documentElement, { childList: true, subtree: true }); } catch (e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initFill);
  else initFill();
})();
