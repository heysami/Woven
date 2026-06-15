/* Host-side live cursors — injected by the daemon into the editor shell when a
   live session is active for the project. The HOST sees guests' cursors and
   broadcasts their own. Talks to the daemon's /__live_events + /__live_presence
   (no guest token; host is trusted). Mirrors editor/live/cursors.js, but
   daemon-flavored. */
(() => {
  "use strict";
  const MY_GID = "host";
  const PID = (() => { try { return new URLSearchParams(location.search).get("project") || ""; } catch (e) { return ""; } })();
  if (!PID) return;
  const parts = new Map();          // guestId -> {name,color,x,y,el}
  let layer = null, geom = { left: 0, top: 0, scale: 1 };
  let connected = false;

  function findLayer() {
    const node = document.querySelector('[class*="workflow-node"]');
    let el = node;
    while (el && el !== document.body) {
      const t = getComputedStyle(el).transform;
      if (t && t !== "none" && t !== "matrix(1, 0, 0, 1, 0, 0)") return el;
      el = el.parentElement;
    }
    return document.querySelector(".workflow-canvas") || document.body;
  }
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
  // Cursors live on the CANVAS, not above the panels — clip to the canvas rect
  // so a cursor mapping into a panel column is hidden behind it.
  function clipToCanvas(o) {
    const c = document.querySelector(".workflow-canvas");
    if (!c) { o.style.clipPath = ""; return; }
    const r = c.getBoundingClientRect();
    o.style.clipPath = "inset(" + Math.max(0, r.top) + "px " + Math.max(0, innerWidth - r.right) +
      "px " + Math.max(0, innerHeight - r.bottom) + "px " + Math.max(0, r.left) + "px)";
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function render(p) {
    if (p.gid === MY_GID || !p.cursor) return;
    let el = p.el;
    if (!el) {
      el = document.createElement("div");
      el.style.cssText = "position:absolute;transition:left .08s linear,top .08s linear;will-change:left,top";
      el.innerHTML =
        '<svg width="20" height="20" viewBox="0 0 20 20" style="filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))">' +
        '<path d="M3 3l6 15 2.4-6.1L17.5 9.6z" fill="' + (p.color || "#888") + '"/></svg>' +
        '<div style="margin:-3px 0 0 13px;background:' + (p.color || "#888") + ';color:#fff;font:600 11px -apple-system,sans-serif;' +
        'padding:2px 7px;border-radius:6px;white-space:nowrap;display:inline-block">' + esc(p.name || "") + "</div>";
      overlay().appendChild(el);
      p.el = el;
    }
    el.style.left = (geom.left + (p.cursor.x || 0) * geom.scale) + "px";
    el.style.top = (geom.top + (p.cursor.y || 0) * geom.scale) + "px";
  }
  function drop(gid) { const p = parts.get(gid); if (p && p.el) p.el.remove(); parts.delete(gid); }

  function connect() {
    readGeom();
    const es = new EventSource("/__live_events?project=" + encodeURIComponent(PID));
    es.addEventListener("presence", (e) => {
      const d = JSON.parse(e.data);
      if (d.guestId === MY_GID) return;
      const p = parts.get(d.guestId) || { gid: d.guestId };
      p.name = d.name; p.color = d.color || "#888"; p.cursor = d.cursor;
      parts.set(d.guestId, p); render(p);
    });
    es.addEventListener("roster", (e) => {
      const seen = new Set((JSON.parse(e.data).participants || []).map((x) => x.guestId));
      for (const g of [...parts.keys()]) if (!seen.has(g)) drop(g);
    });
    es.addEventListener("lock", (e) => {
      try { window.__thLocks && window.__thLocks.setLeases(JSON.parse(e.data).leases); } catch (_) {}
    });
    es.addEventListener("session-ended", () => { for (const g of [...parts.keys()]) drop(g); es.close(); connected = false; try { window.__thLiveActive = false; } catch (e) {} });

    // Soft node locks — host side. Acquire/release via the daemon's /__live_lease.
    if (window.__thLocks) {
      const lease = (action, extra) => fetch("/__live_lease?project=" + encodeURIComponent(PID), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({ action: action, name: "Host" }, extra || {})),
      }).catch(() => {});
      window.__thLocks.config({
        myGid: MY_GID,
        acquire:  (t)  => lease("acquire",   { target: t }),
        release:  (t)  => lease("release",   { target: t }),
        heartbeat:(ts) => lease("heartbeat", { targets: ts }),
        colorFor: (gid) => { const p = parts.get(gid); return p && p.color; },
      });
    }
    es.onerror = () => {};  // EventSource auto-reconnects

    let last = 0;
    window.addEventListener("pointermove", (ev) => {
      const now = performance.now();
      if (now - last < 50) return;
      last = now;
      readGeom();
      const x = (ev.clientX - geom.left) / geom.scale;
      const y = (ev.clientY - geom.top) / geom.scale;
      fetch("/__live_presence?project=" + encodeURIComponent(PID), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cursor: { x, y, page: "canvas" } }),
      }).catch(() => {});
    }, { passive: true });

    setInterval(() => { if (!parts.size) return; readGeom(); for (const p of parts.values()) render(p); }, 120);
  }

  function poll() {
    if (connected) return;
    fetch("/__live_status?project=" + encodeURIComponent(PID))
      .then((r) => r.json())
      .then((s) => { try { window.__thLiveActive = !!(s && s.live); } catch (e) {} if (s && s.live && !connected) { connected = true; connect(); } })
      .catch(() => {});
  }
  // Wait for the canvas, then poll for a live session and connect when one
  // starts — so cursors appear even if you go live AFTER opening the editor.
  const t = setInterval(() => {
    if (document.querySelector('[class*="workflow-node"]') || document.querySelector(".workflow-canvas")) {
      clearInterval(t);
      poll();
      setInterval(poll, 8000);
    }
  }, 400);
  setTimeout(() => clearInterval(t), 20000);
})();
