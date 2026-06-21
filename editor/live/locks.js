/* Live node locks - a SOFT, visual "locked by <name>" overlay shared by the
   host (cursors-host.js) and guest (cursors.js) editors. Non-blocking by design:
   it shows who is currently holding a node and acquires/releases a lease as you
   grab and let go, but it never PREVENTS anyone from editing. Server leases are
   first-holder-wins, so the badge stays consistent across everyone.

   The two cursor scripts own the transport (different endpoints + SSE), so this
   module exposes window.__thLocks = { config(adapter), setLeases(list) } and they
   wire it up:
     - config({ myGid, acquire(t), release(t), heartbeat(ts), colorFor(gid) })
     - setLeases([{target, holder, holderName}])  ← called on every `lock` SSE frame

   No emoji icons - inline lock SVG drawn with currentColor (see no-emoji rule). */
(() => {
  "use strict";
  if (window.__thLocks) return;

  let cfg = null;                 // transport adapter set by the cursor script
  let leases = [];                // [{target, holder, holderName}]
  const held = new Map();         // target -> last-interaction timestamp
  const badges = new Map();       // target -> { box, tag }
  const GRACE_MS = 1500;          // release a hold this long after interaction goes idle

  const LOCK_SVG =
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2.4" style="vertical-align:-1px"><rect x="4.5" y="11" width="15" height="9" rx="2"/>' +
    '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>';

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }
  function cssEscape(s) { return (window.CSS && CSS.escape) ? CSS.escape(s) : s; }
  function overlay() {
    let o = document.getElementById("th-live-locks");
    if (!o) {
      o = document.createElement("div");
      o.id = "th-live-locks";
      o.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:99997";
      document.body.appendChild(o);
    }
    // Lock badges live on the CANVAS - clip to the canvas rect so a badge for a
    // node panned under a side panel is hidden behind it (panels are separate
    // grid columns), instead of floating over the panel.
    const c = document.querySelector(".workflow-canvas-wrap");
    if (c) {
      const r = c.getBoundingClientRect();
      o.style.clipPath = "inset(" + Math.max(0, r.top) + "px " + Math.max(0, innerWidth - r.right) +
        "px " + Math.max(0, innerHeight - r.bottom) + "px " + Math.max(0, r.left) + "px)";
    }
    return o;
  }
  function nodeEl(nid) {
    return document.querySelector('.workflow-node[data-node-id="' + cssEscape(nid) + '"]')
        || document.querySelector('[data-node-id="' + cssEscape(nid) + '"]');
  }
  function nodeIdFromEl(target) {
    let el = target;
    while (el && el !== document.body) {
      if (el.dataset && el.dataset.nodeId) return el.dataset.nodeId;
      el = el.parentElement;
    }
    return null;
  }

  // Mark a node as actively interacted-with: acquire its lease on first touch,
  // and (re)stamp its idle timer. Release is driven by a SWEEP on idleness, not
  // by catching a pointerup - a drag that ends with pointercancel / a missed
  // pointerup would otherwise leave us holding the lease forever (heartbeated
  // every 10s), which blocks the other side's edits to that node until refresh.
  function touch(target) {
    if (!held.has(target)) { try { cfg && cfg.acquire(target); } catch (e) {} }
    held.set(target, Date.now());
  }
  // Release any hold whose interaction has been idle past the grace. The lock
  // models "I am actively editing", not "my cursor rests here" - so a node
  // stays locked only while you keep typing/dragging, and unlocks GRACE_MS
  // after you stop, EVEN IF the field is still focused. This is the contract:
  // lock during the edit, unlock when the edit is done, then whoever edits next
  // wins (last-writer). Keying release off focus (the old behaviour) pinned the
  // lease for as long as a cursor sat in the textarea, so the previous editor
  // hard-locked the next one out and the next one's write got silently dropped
  // by the server lock - the "C reverts to B / never reaches the other side"
  // bug. Resuming typing re-acquires via touch() in the input/keydown handlers.
  function sweep() {
    const now = Date.now();
    for (const [t, ts] of [...held]) {
      if (now - ts > GRACE_MS) {
        held.delete(t);
        try { cfg && cfg.release(t); } catch (e) {}
      }
    }
  }

  // Render badges over every node held by SOMEONE ELSE. Called on lock frames
  // and on a 150ms tick (so a badge follows the node while either side pans/
  // zooms). 150ms is not per-frame - safe per the canvas-rect rule.
  function render() {
    if (!cfg) return;
    const o = overlay();
    const want = new Map();
    for (const l of leases) {
      if (!l || l.holder === cfg.myGid) continue;       // skip my own locks
      if (typeof l.target !== "string" || l.target.indexOf("node:") !== 0) continue;
      want.set(l.target, l);
    }
    for (const [tgt, b] of [...badges]) {
      if (!want.has(tgt)) { b.box.remove(); badges.delete(tgt); }
    }
    for (const [tgt, l] of want) {
      const el = nodeEl(tgt.slice(5));
      let b = badges.get(tgt);
      if (!el) { if (b) { b.box.remove(); badges.delete(tgt); } continue; }
      const r = el.getBoundingClientRect();
      const color = (cfg.colorFor && cfg.colorFor(l.holder)) || "#a855f7";
      if (!b) {
        const box = document.createElement("div");
        box.style.cssText = "position:absolute;border:2px solid;border-radius:8px;box-sizing:border-box;" +
          "transition:left .08s,top .08s,width .08s,height .08s";
        const tag = document.createElement("div");
        tag.style.cssText = "position:absolute;left:-2px;top:-22px;color:#fff;" +
          "font:600 11px -apple-system,system-ui,sans-serif;padding:2px 7px;border-radius:6px;" +
          "white-space:nowrap;display:inline-flex;align-items:center;gap:4px";
        box.appendChild(tag);
        o.appendChild(box);
        b = { box, tag };
        badges.set(tgt, b);
      }
      b.box.style.borderColor = color;
      b.tag.style.background = color;
      b.tag.innerHTML = LOCK_SVG + esc(l.holderName || "Someone");
      b.box.style.left = r.left + "px";
      b.box.style.top = r.top + "px";
      b.box.style.width = r.width + "px";
      b.box.style.height = r.height + "px";
    }
  }

  window.__thLocks = {
    config(adapter) {
      cfg = adapter;
      // Capture phase so we see the interaction before the editor's handlers.
      // Acquire on grab/focus; keep the hold alive while the drag is MOVING
      // (buttons down) or the field is being typed in; the sweep releases it
      // ~GRACE after interaction goes idle - no reliance on catching pointerup.
      window.addEventListener("pointerdown", (e) => { const n = nodeIdFromEl(e.target); if (n) touch("node:" + n); }, true);
      window.addEventListener("pointermove", (e) => {
        if (e.buttons === 0) return;              // only an active drag keeps a hold alive
        for (const t of held.keys()) held.set(t, Date.now());
      }, true);
      window.addEventListener("focusin", (e) => { const n = nodeIdFromEl(e.target); if (n) touch("node:" + n); }, true);
      // Typing (re)acquires + keeps the hold alive. Using touch() rather than a
      // bare restamp means that after the idle sweep releases a still-focused
      // node, the next keystroke re-locks it - so an active edit is always
      // protected, while an idle-but-focused node is free for the next editor.
      const keep = (e) => { const n = nodeIdFromEl(e.target); if (n) touch("node:" + n); };
      window.addEventListener("input", keep, true);
      window.addEventListener("keydown", keep, true);
      setInterval(sweep, 600);                    // idle-based release (robust vs missed pointerup)
      setInterval(() => { if (held.size) { try { cfg.heartbeat([...held.keys()]); } catch (e) {} } }, 10000);
      setInterval(render, 150);
    },
    setLeases(ls) { leases = Array.isArray(ls) ? ls : []; render(); },
  };
})();
