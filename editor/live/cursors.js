/* Live cursors overlay — injected into the REAL editor when served to a guest
   through the gate (/s/<token>/live/). Joins the live session, broadcasts this
   guest's pointer in CANVAS-WORLD coords, and renders every other guest's
   cursor mapped through the workflow canvas's pan/zoom layer so cursors point
   at the same nodes regardless of each viewer's pan/zoom. Self-contained; talks
   only to the gate's /live/api/* + /live/events (relative paths). */
(() => {
  "use strict";
  let TOKEN = "", GID = "", COLOR = "#2D7FF9";
  const parts = new Map();              // guestId -> {name,color,x,y,el}
  let layer = null, geom = { left: 0, top: 0, scale: 1 };

  function api(path, body) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Live-Token": TOKEN },
      body: JSON.stringify(body || {}),
    }).then((r) => r.json());
  }

  // The pan/zoom layer = nearest ancestor of a node carrying a real transform.
  function findLayer() {
    const node = document.querySelector('[class*="workflow-node"]');
    let el = node;
    while (el && el !== document.body) {
      const t = getComputedStyle(el).transform;
      if (t && t !== "none" && t !== "matrix(1, 0, 0, 1, 0, 0)") return el;
      el = el.parentElement;
    }
    return document.querySelector(".workflow-canvas-wrap") || document.body;
  }
  // Read layer geometry sparingly (never per-frame — see canvas-rect memory).
  function readGeom() {
    if (!layer || !layer.isConnected) layer = findLayer();
    if (!layer) return;
    const r = layer.getBoundingClientRect();
    const ow = layer.offsetWidth || 1;
    geom = { left: r.left, top: r.top, scale: r.width / ow || 1 };
  }
  function overlay() {
    let o = document.getElementById("th-live-cursors");
    if (!o) {
      o = document.createElement("div");
      o.id = "th-live-cursors";
      o.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:99998";
      document.body.appendChild(o);
    }
    clipToCanvas(o);
    return o;
  }
  // Cursors live on the CANVAS, not above the side panels — clip the
  // viewport-covering overlay to the canvas rect so a remote cursor mapping
  // into a panel column is hidden behind it (panels are separate grid columns).
  function clipToCanvas(o) {
    const c = document.querySelector(".workflow-canvas-wrap");
    if (!c) { o.style.clipPath = ""; return; }
    const r = c.getBoundingClientRect();
    o.style.clipPath = "inset(" + Math.max(0, r.top) + "px " + Math.max(0, innerWidth - r.right) +
      "px " + Math.max(0, innerHeight - r.bottom) + "px " + Math.max(0, r.left) + "px)";
  }
  function render(p) {
    if (p.gid === GID) return;
    let el = p.el;
    if (!el) {
      el = document.createElement("div");
      el.style.cssText = "position:absolute;transition:left .08s linear,top .08s linear;will-change:left,top";
      el.innerHTML =
        '<svg width="20" height="20" viewBox="0 0 20 20" style="filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))">' +
        '<path d="M3 3l6 15 2.4-6.1L17.5 9.6z" fill="' + p.color + '"/></svg>' +
        '<div style="margin:-3px 0 0 13px;background:' + p.color + ';color:#fff;font:600 11px -apple-system,sans-serif;' +
        'padding:2px 7px;border-radius:6px;white-space:nowrap;display:inline-block">' + esc(p.name || "") + "</div>";
      overlay().appendChild(el);
      p.el = el;
    }
    el.style.left = (geom.left + (p.x || 0) * geom.scale) + "px";
    el.style.top = (geom.top + (p.y || 0) * geom.scale) + "px";
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function drop(gid) { const p = parts.get(gid); if (p && p.el) p.el.remove(); parts.delete(gid); }

  function start() {
    readGeom();
    const es = new EventSource("events?lt=" + encodeURIComponent(TOKEN));
    es.addEventListener("presence", (e) => {
      const d = JSON.parse(e.data);
      if (d.guestId === GID) return;
      const p = parts.get(d.guestId) || { gid: d.guestId };
      p.name = d.name; p.color = d.color || "#888";
      if (d.cursor) { p.x = d.cursor.x; p.y = d.cursor.y; }
      parts.set(d.guestId, p); render(p);
    });
    es.addEventListener("roster", (e) => {
      const d = JSON.parse(e.data);
      const seen = new Set((d.participants || []).map((x) => x.guestId));
      for (const g of [...parts.keys()]) if (!seen.has(g)) drop(g);
    });
    es.addEventListener("lock", (e) => {
      try { window.__thLocks && window.__thLocks.setLeases(JSON.parse(e.data).leases); } catch (_) {}
    });
    es.addEventListener("session-ended", () => { for (const g of [...parts.keys()]) drop(g); es.close(); try { window.__thLiveActive = false; } catch (e) {} });
    es.addEventListener("kicked", (e) => { if (JSON.parse(e.data).guestId === GID) { for (const g of [...parts.keys()]) drop(g); es.close(); try { window.__thLiveActive = false; } catch (e) {} } });

    let last = 0;
    window.addEventListener("pointermove", (ev) => {
      const now = performance.now();
      if (now - last < 50) return;
      last = now;
      readGeom();
      const x = (ev.clientX - geom.left) / geom.scale;
      const y = (ev.clientY - geom.top) / geom.scale;
      api("api/presence", { cursor: { x, y, page: "canvas" } }).catch(() => {});
    }, { passive: true });

    // Soft node locks — show "locked by <name>" as collaborators grab nodes.
    if (window.__thLocks) {
      window.__thLocks.config({
        myGid: GID,
        acquire:  (t)  => api("api/lease/acquire",  { target: t }).catch(() => {}),
        release:  (t)  => api("api/lease/release",  { target: t }).catch(() => {}),
        heartbeat:(ts) => api("api/lease/heartbeat", { targets: ts }).catch(() => {}),
        colorFor: (gid) => { const p = parts.get(gid); return p && p.color; },
      });
    }

    // Re-place cursors periodically so they stay glued to nodes while *I* pan/
    // zoom (idle remote guests send no presence). 120ms — not per-frame.
    setInterval(() => { if (!parts.size) return; readGeom(); for (const p of parts.values()) render(p); }, 120);
    // Heartbeat keeps me in the roster while only viewing.
    setInterval(() => { api("api/presence", {}).catch(() => {}); }, 20000);
  }

  async function boot() {
    let meta;
    try { meta = await fetch("api/meta").then((r) => r.json()); } catch (e) { return; }
    if (!meta || meta.error) return;
    let name = "";
    try { name = localStorage.getItem("th-live-name") || ""; } catch (e) {}
    if (!name) { name = (window.prompt("Your name for this live session:") || "Guest").slice(0, 40); try { localStorage.setItem("th-live-name", name); } catch (e) {} }
    // Stable per-browser id so a refresh reuses the same participant instead of
    // adding a duplicate user to the roster.
    let cid = "";
    try {
      cid = localStorage.getItem("th-live-cid") || "";
      if (!cid) { cid = "c-" + Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem("th-live-cid", cid); }
    } catch (e) {}
    try { const j = await api("api/join", { name, clientId: cid }); TOKEN = j.token; GID = j.guestId; COLOR = j.color; try { window.__thLiveActive = true; window.__thLiveToken = TOKEN; } catch (e) {} start(); } catch (e) {}
  }

  // Wait for the canvas to mount, then boot.
  const t = setInterval(() => {
    if (document.querySelector('[class*="workflow-node"]') || document.querySelector(".workflow-canvas-wrap")) {
      clearInterval(t); boot();
    }
  }, 400);
  setTimeout(() => clearInterval(t), 20000);
})();
