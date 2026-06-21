/* Woven Live Session - guest collab client (vanilla, gate-served).
   Served at /s/<token>/live/ ; all paths here are relative to that base, so
   `api/*` → /s/<token>/live/api/*, `../p/*` → /s/<token>/p/* (prototype files). */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const S = {
    token: "", guestId: "", role: "viewer", color: "#888", meta: null,
    nodes: [], wb: [], nodeEls: new Map(),
    pan: { x: 160, y: 140 }, participants: new Map(), leases: {},
    selected: null, editing: null, pendingWfRefresh: false, rect: null, es: null,
    gh: { login: "", forked: null, device: null, pollTimer: null },
  };

  // ── tiny REST helper ─────────────────────────────────────────────────
  async function api(path, opts = {}) {
    const o = Object.assign({ headers: {} }, opts);
    o.headers["X-Live-Token"] = S.token;
    if (o.body && typeof o.body !== "string") {
      o.headers["Content-Type"] = "application/json";
      o.body = JSON.stringify(o.body);
    }
    // Hard timeout so a stalled tunnel surfaces as a visible error instead of
    // an infinite silent hang (which looks like "stuck").
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 12000);
    o.signal = ctrl.signal;
    let r;
    try {
      r = await fetch(path, o);
    } catch (e) {
      clearTimeout(timer);
      const full = (() => { try { return new URL(path, location.href).href; } catch { return path; } })();
      if (e && e.name === "AbortError") throw new Error(`timed out after 12s → ${full}`);
      throw new Error(`network error → ${full} (${e && e.message || e})`);
    }
    clearTimeout(timer);
    let j = null; try { j = await r.json(); } catch (_) {}
    if (!r.ok) throw new Error((j && j.error) || `HTTP ${r.status} → ${new URL(path, location.href).href}`);
    return j;
  }
  function setDiag(msg) { const d = document.getElementById("diag"); if (d) d.textContent = msg; }

  let toastT = null;
  function toast(msg, kind) {
    const t = $("toast"); t.textContent = msg; t.dataset.kind = kind || "";
    t.hidden = false; clearTimeout(toastT);
    toastT = setTimeout(() => { t.hidden = true; }, 2600);
  }

  // ── Join gate ────────────────────────────────────────────────────────
  async function boot() {
    setDiag("page: " + location.href);
    let meta;
    try { meta = await api("api/meta"); }
    catch (e) {
      // session likely not live yet - OR a routing/tunnel problem; show which
      $("join-sub").textContent = "This session isn't live right now (or the link is stale). Ask the host to start it, then open a fresh link.";
      $("join-btn").disabled = true;
      setDiag("meta failed: " + (e.message || e));
      return;
    }
    setDiag("ready · " + location.href);
    S.meta = meta;
    $("join-label").textContent = meta.label || "Live session";
    if (meta.emailGate) $("join-email-wrap").hidden = false;
    const saved = loadIdent();
    if (saved) { $("join-name").value = saved.name || ""; $("join-email").value = saved.email || ""; }
    $("join-btn").addEventListener("click", doJoin);
    $("join-name").addEventListener("keydown", (e) => { if (e.key === "Enter") doJoin(); });
  }

  function loadIdent() { try { return JSON.parse(localStorage.getItem("woven-live-ident") || "null"); } catch { return null; } }
  function saveIdent(name, email) { try { localStorage.setItem("woven-live-ident", JSON.stringify({ name, email })); } catch {} }

  async function doJoin() {
    const name = $("join-name").value.trim();
    const email = $("join-email").value.trim();
    const err = $("join-err");
    if (!name) { err.hidden = false; err.textContent = "Please enter your name."; return; }
    $("join-btn").disabled = true; err.hidden = true;
    setDiag("joining… POST " + (() => { try { return new URL("api/join", location.href).href; } catch { return "api/join"; } })());
    try {
      const out = await api("api/join", { method: "POST", body: { name, email } });
      S.token = out.token; S.guestId = out.guestId; S.role = out.role; S.color = out.color;
      saveIdent(name, email);
      setDiag("joined ✓");
      startApp();
    } catch (e) {
      err.hidden = false; err.textContent = e.message || "Could not join.";
      setDiag("join failed: " + (e.message || e));
      $("join-btn").disabled = false;
    }
  }

  // ── App ──────────────────────────────────────────────────────────────
  function startApp() {
    $("join").hidden = true; $("app").hidden = false;
    $("bar-label").textContent = S.meta.label || "";
    const chip = $("role-chip"); chip.textContent = S.role;
    chip.style.color = S.role === "editor" ? "var(--ink)" : "var(--ink-dim)";
    cacheRect();
    applyPan();
    wireStage();
    wireBar();
    connect();
    loadWorkflow();
  }

  function cacheRect() { S.rect = $("stage").getBoundingClientRect(); }
  window.addEventListener("resize", () => { cacheRect(); });

  function applyPan() { $("world").style.transform = `translate(${S.pan.x}px,${S.pan.y}px)`; }
  function screenToWorld(cx, cy) { return { x: cx - S.rect.left - S.pan.x, y: cy - S.rect.top - S.pan.y }; }

  // ── SSE ──────────────────────────────────────────────────────────────
  function connect() {
    if (S.es) S.es.close();
    const es = new EventSource(`events?lt=${encodeURIComponent(S.token)}`);
    S.es = es;
    es.addEventListener("live-connected", () => toast("Connected", "ok"));
    es.addEventListener("roster", (e) => onRoster(JSON.parse(e.data)));
    es.addEventListener("presence", (e) => onPresence(JSON.parse(e.data)));
    es.addEventListener("lock", (e) => onLock(JSON.parse(e.data)));
    es.addEventListener("workflow-changed", () => onWorkflowChanged());
    es.addEventListener("asset-changed", () => reloadFrame());
    es.addEventListener("session-ended", () => endScreen("The host ended this session."));
    es.addEventListener("kicked", (e) => { if (JSON.parse(e.data).guestId === S.guestId) endScreen("You were removed from this session."); });
    es.onerror = () => { /* EventSource auto-reconnects; show nothing unless it persists */ };
  }

  function endScreen(msg) {
    if (S.es) S.es.close();
    document.body.innerHTML = `<div class="join"><div class="join-card"><div class="join-brand">woven<span>·live</span></div><div class="join-label">Session closed</div><p class="join-sub">${esc(msg)}</p></div></div>`;
  }

  // ── Roster + cursors ─────────────────────────────────────────────────
  function onRoster(d) {
    const seen = new Set();
    (d.participants || []).forEach((p) => {
      seen.add(p.guestId);
      const cur = S.participants.get(p.guestId) || {};
      S.participants.set(p.guestId, Object.assign(cur, p));
    });
    for (const id of [...S.participants.keys()]) if (!seen.has(id)) { S.participants.delete(id); removeCursor(id); }
    renderRoster(); renderCursors();
  }
  function onPresence(p) {
    const cur = S.participants.get(p.guestId) || { name: p.name, color: p.color };
    cur.cursor = p.cursor; cur.color = p.color; cur.name = p.name;
    S.participants.set(p.guestId, cur);
    placeCursor(p.guestId, cur);
  }

  function renderRoster() {
    const r = $("roster"); r.innerHTML = "";
    for (const [id, p] of S.participants) {
      const a = document.createElement("div");
      a.className = "avatar"; a.style.background = p.color || "#888";
      a.title = p.name + (p.role ? ` · ${p.role}` : "");
      a.textContent = (p.name || "?").slice(0, 1).toUpperCase();
      if (id === S.guestId) a.dataset.you = "1";
      r.appendChild(a);
    }
  }

  function renderCursors() {
    for (const [id, p] of S.participants) if (id !== S.guestId && p.cursor) placeCursor(id, p);
  }
  function placeCursor(id, p) {
    if (id === S.guestId || !p.cursor) return;
    let el = document.getElementById("cur-" + id);
    if (!el) {
      el = document.createElement("div"); el.id = "cur-" + id; el.className = "cursor";
      el.innerHTML = `<svg width="18" height="18" viewBox="0 0 18 18"><path d="M2 2l5 14 2.2-5.6L15 8.2z" fill="${p.color}"/></svg><div class="tag" style="background:${p.color}">${esc(p.name || "")}</div>`;
      $("cursors").appendChild(el);
    }
    el.style.left = p.cursor.x + "px"; el.style.top = p.cursor.y + "px";
  }
  function removeCursor(id) { const el = document.getElementById("cur-" + id); if (el) el.remove(); }

  // ── Workflow render ──────────────────────────────────────────────────
  async function loadWorkflow() {
    try {
      const wf = await api("api/workflow");
      S.nodes = Array.isArray(wf.nodes) ? wf.nodes : [];
      S.wb = Array.isArray(wf.wb) ? wf.wb : [];
      renderNodes();
    } catch (e) { toast("Could not load canvas: " + e.message, "err"); }
  }
  function onWorkflowChanged() {
    if (S.editing) { S.pendingWfRefresh = true; return; }
    loadWorkflow();
  }

  function renderNodes() {
    const host = $("nodes"); host.innerHTML = ""; S.nodeEls.clear();
    for (const n of S.nodes) {
      const el = document.createElement("div");
      el.className = "node"; el.dataset.id = n.id;
      el.style.left = (Number(n.x) || 0) + "px"; el.style.top = (Number(n.y) || 0) + "px";
      const title = n.title || n.label || n.id;
      const status = n.runStatus || "";
      el.innerHTML =
        `<div class="lock-badge" hidden></div>` +
        `<div class="node-kind">${esc(n.kind || "node")}</div>` +
        `<div class="node-title">${esc(title)}</div>` +
        `<div class="node-foot">` +
          (status ? `<span class="node-status" data-s="${esc(status)}">${esc(status)}</span>` : `<span class="node-status">idle</span>`) +
          (S.role === "editor" ? `<button class="node-run">Run</button>` : ``) +
        `</div>`;
      host.appendChild(el);
      S.nodeEls.set(n.id, el);
      wireNode(el, n);
    }
    applyLocks();
  }

  // ── Locks ────────────────────────────────────────────────────────────
  function onLock(d) {
    S.leases = {};
    (d.leases || []).forEach((l) => { S.leases[l.target] = l; });
    applyLocks();
  }
  function applyLocks() {
    for (const [id, el] of S.nodeEls) {
      const l = S.leases["node:" + id];
      const badge = el.querySelector(".lock-badge");
      const runBtn = el.querySelector(".node-run");
      if (!l) { el.dataset.locked = ""; badge.hidden = true; if (runBtn) runBtn.disabled = false; }
      else if (l.holder === "agent") {
        el.dataset.locked = "agent"; badge.hidden = false; badge.textContent = "🔒 " + (l.holderName || "agent");
        badge.style.background = "var(--accent-2)"; if (runBtn) runBtn.disabled = true;
      } else if (l.holder === S.guestId) {
        el.dataset.locked = "mine"; badge.hidden = false; badge.textContent = "✎ you";
        badge.style.background = "var(--accent)"; if (runBtn) runBtn.disabled = false;
      } else {
        el.dataset.locked = "other"; badge.hidden = false; badge.textContent = "✎ " + (l.holderName || "someone");
        badge.style.background = "var(--warn)"; if (runBtn) runBtn.disabled = true;
      }
    }
  }
  function lockedByOther(id) {
    const l = S.leases["node:" + id];
    return l && l.holder !== S.guestId;
  }

  // ── Presence emit (throttled) ────────────────────────────────────────
  let lastPres = 0;
  function emitPresence(cx, cy) {
    const now = performance.now();
    if (now - lastPres < 45) return;
    lastPres = now;
    const w = screenToWorld(cx, cy);
    api("api/presence", { method: "POST", body: { cursor: { x: w.x, y: w.y, page: "canvas" } } }).catch(() => {});
  }

  // ── Leases ───────────────────────────────────────────────────────────
  async function acquireLease(id) {
    if (S.role !== "editor") return false;
    try {
      const r = await api("api/lease/acquire", { method: "POST", body: { target: "node:" + id } });
      if (!r.ok) { toast(`Locked by ${r.holderName || "someone"}`, "err"); return false; }
      return true;
    } catch (e) { toast(e.message, "err"); return false; }
  }
  function releaseLease(id) {
    if (!id) return;
    api("api/lease/release", { method: "POST", body: { target: "node:" + id } }).catch(() => {});
  }
  setInterval(() => {
    if (S.selected) api("api/lease/heartbeat", { method: "POST", body: { targets: ["node:" + S.selected] } }).catch(() => {});
  }, 10000);

  async function selectNode(id) {
    if (S.selected === id) return;
    if (S.selected) { releaseLease(S.selected); S.selected = null; }
    if (await acquireLease(id)) S.selected = id;
  }
  function deselect() {
    if (S.editing) commitEdit();
    if (S.selected) { releaseLease(S.selected); S.selected = null; }
  }

  // ── Node interactions ────────────────────────────────────────────────
  function wireNode(el, n) {
    const titleEl = el.querySelector(".node-title");
    const runBtn = el.querySelector(".node-run");

    if (runBtn) runBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      runBtn.disabled = true;
      try { await api("api/run", { method: "POST", body: { nodeId: n.id } }); toast("Run started", "ok"); }
      catch (err) { toast(err.message, "err"); runBtn.disabled = false; }
    });

    // double-click title → edit (requires lease)
    if (S.role === "editor") titleEl.addEventListener("dblclick", async (e) => {
      e.stopPropagation();
      if (lockedByOther(n.id)) { toast("Someone else is editing this", "err"); return; }
      if (await acquireLease(n.id)) { S.selected = n.id; beginEdit(n.id, titleEl); }
    });
    titleEl.addEventListener("blur", () => { if (S.editing === n.id) commitEdit(); });
    titleEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); titleEl.blur(); }
      if (e.key === "Escape") { titleEl.textContent = (n.title || n.label || n.id); titleEl.blur(); }
    });

    // drag to move (requires editor + not locked by other)
    el.addEventListener("pointerdown", (e) => {
      if (e.target === runBtn || S.editing === n.id) return;
      if (S.role !== "editor") return;
      if (lockedByOther(n.id)) { toast("Locked by someone else", "err"); return; }
      e.stopPropagation();
      selectNode(n.id);
      startNodeDrag(el, n, e);
    });
  }

  function beginEdit(id, titleEl) {
    S.editing = id;
    titleEl.setAttribute("contenteditable", "true");
    titleEl.focus();
    const r = document.createRange(); r.selectNodeContents(titleEl); r.collapse(false);
    const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
  }
  async function commitEdit() {
    const id = S.editing; if (!id) return;
    S.editing = null;
    const el = S.nodeEls.get(id); if (!el) return;
    const titleEl = el.querySelector(".node-title");
    titleEl.removeAttribute("contenteditable");
    const value = titleEl.textContent.trim();
    const n = S.nodes.find((x) => x.id === id);
    if (n && value && value !== (n.title || n.label || n.id)) {
      try { await api("api/op", { method: "POST", body: { op: { op: "setField", target: "node:" + id, field: "title", value } } }); n.title = value; }
      catch (e) { toast(e.message, "err"); }
    }
    if (S.pendingWfRefresh) { S.pendingWfRefresh = false; loadWorkflow(); }
  }

  let drag = null;
  function startNodeDrag(el, n, e) {
    const w = screenToWorld(e.clientX, e.clientY);
    drag = { id: n.id, el, n, offX: w.x - (Number(n.x) || 0), offY: w.y - (Number(n.y) || 0), moved: false, last: 0 };
    el.setPointerCapture(e.pointerId);
    el.addEventListener("pointermove", onNodeDragMove);
    el.addEventListener("pointerup", onNodeDragEnd);
    el.addEventListener("pointercancel", onNodeDragEnd);
  }
  function onNodeDragMove(e) {
    if (!drag) return;
    const w = screenToWorld(e.clientX, e.clientY);
    const nx = w.x - drag.offX, ny = w.y - drag.offY;
    drag.n.x = nx; drag.n.y = ny; drag.moved = true;
    drag.el.style.left = nx + "px"; drag.el.style.top = ny + "px";
    const now = performance.now();
    if (now - drag.last > 50) { drag.last = now; sendMove(drag.id, nx, ny); }
    emitPresence(e.clientX, e.clientY);
  }
  function onNodeDragEnd(e) {
    if (!drag) return;
    const d = drag; drag = null;
    try { d.el.releasePointerCapture(e.pointerId); } catch {}
    d.el.removeEventListener("pointermove", onNodeDragMove);
    d.el.removeEventListener("pointerup", onNodeDragEnd);
    d.el.removeEventListener("pointercancel", onNodeDragEnd);
    if (d.moved) sendMove(d.id, d.n.x, d.n.y);
  }
  function sendMove(id, x, y) {
    api("api/op", { method: "POST", body: { op: { op: "move", target: "node:" + id, x, y } } }).catch(() => {});
  }

  // ── Stage panning + presence ─────────────────────────────────────────
  function wireStage() {
    const stage = $("stage");
    let pan = null;
    stage.addEventListener("pointerdown", (e) => {
      if (e.target.closest(".node")) return;
      deselect();
      pan = { sx: e.clientX, sy: e.clientY, px: S.pan.x, py: S.pan.y };
      stage.classList.add("panning"); stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener("pointermove", (e) => {
      if (pan) {
        S.pan.x = pan.px + (e.clientX - pan.sx);
        S.pan.y = pan.py + (e.clientY - pan.sy);
        applyPan();
      }
      emitPresence(e.clientX, e.clientY);
    });
    const endPan = (e) => { if (pan) { pan = null; stage.classList.remove("panning"); try { stage.releasePointerCapture(e.pointerId); } catch {} } };
    stage.addEventListener("pointerup", endPan);
    stage.addEventListener("pointercancel", endPan);
  }

  // ── Bar buttons ──────────────────────────────────────────────────────
  function wireBar() {
    const proto = $("proto");
    $("toggle-proto").addEventListener("click", () => {
      const show = proto.hidden;
      proto.hidden = !show;
      if (show && !$("frame").src && S.meta.entry) $("frame").src = "../" + S.meta.entry;
    });
    $("proto-reload").addEventListener("click", reloadFrame);
    $("leave").addEventListener("click", async () => {
      try { await api("api/leave", { method: "POST", body: {} }); } catch {}
      endScreen("You left the session.");
    });
    if (S.meta && S.meta.githubConfigured) {
      $("fork-btn").hidden = false;
      $("fork-btn").addEventListener("click", openFork);
      $("fork-x").addEventListener("click", () => {
        $("fork").hidden = true; if (S.gh.pollTimer) clearTimeout(S.gh.pollTimer);
      });
    }
    window.addEventListener("beforeunload", () => {
      if (S.selected) navigator.sendBeacon && navigator.sendBeacon("api/lease/release"); // best-effort
    });
  }
  function reloadFrame() {
    const f = $("frame");
    if (f.src) { const u = f.src.split("#")[0]; f.src = u + (u.includes("?") ? "&" : "?") + "_r=" + Date.now(); }
    else if (S.meta && S.meta.entry && !$("proto").hidden) f.src = "../" + S.meta.entry;
  }

  // ── Fork / GitHub (device flow → fork → PR) ──────────────────────────
  function forkBody(h) { $("fork-body").innerHTML = h; $("fork").hidden = false; }
  function openFork() {
    if (S.gh.forked) return renderForked();
    if (S.gh.login) return renderFork();
    renderConnect();
  }
  function renderConnect() {
    forkBody(`<h3>Connect your GitHub</h3><p>Take a copy of this prototype to your own GitHub so you can edit it independently in your own Woven. You'll authorize Woven once with a short code.</p><button id="gh-go" class="btn-primary">Connect GitHub</button>`);
    $("gh-go").addEventListener("click", startDevice);
  }
  async function startDevice() {
    try {
      const d = await api("api/github/device/start", { method: "POST", body: {} });
      S.gh.device = d;
      forkBody(`<h3>Authorize Woven</h3><p>Open <b>${esc(d.verification_uri)}</b> and enter this code:</p><div class="code-box big-code">${esc(d.user_code)}</div><p class="m-spin">Waiting for you to authorize… keep this window open.</p><button id="gh-open" class="btn-primary">Open GitHub ↗</button>`);
      $("gh-open").addEventListener("click", () => window.open(d.verification_uri, "_blank"));
      pollDevice(d.interval || 5);
    } catch (e) { toast(e.message, "err"); }
  }
  function pollDevice(interval) {
    S.gh.pollTimer = setTimeout(async () => {
      try {
        const r = await api("api/github/device/poll", { method: "POST", body: {} });
        if (r.status === "ok") { S.gh.login = r.login; toast("GitHub connected: " + r.login, "ok"); renderFork(); return; }
        if (r.status === "pending") { pollDevice(r.slowDown ? interval + 5 : interval); return; }
        toast(r.error || "authorization failed", "err");
      } catch (e) { toast(e.message, "err"); }
    }, interval * 1000);
  }
  function renderFork() {
    forkBody(`<h3>Fork to your GitHub</h3><p>Signed in as <b>${esc(S.gh.login)}</b>. This creates your own copy of the prototype's repository under your account.</p><button id="gh-fork" class="btn-primary">Fork this prototype</button>`);
    $("gh-fork").addEventListener("click", doFork);
  }
  async function doFork() {
    const btn = $("gh-fork"); if (btn) btn.disabled = true;
    try {
      S.gh.forked = await api("api/github/fork", { method: "POST", body: {} });
      renderForked();
    } catch (e) { toast(e.message, "err"); if (btn) btn.disabled = false; }
  }
  function renderForked() {
    const f = S.gh.forked;
    forkBody(`<h3>Forked ✓</h3><p>Your copy: <b>${esc(f.full_name)}</b>. Clone it and open it in your own Woven to edit independently:</p><div class="code-box">git clone ${esc(f.clone_url)}</div><p>When you've pushed changes you want merged back, open a pull request to the host:</p><div class="m-row"><input id="pr-title" placeholder="PR title" value="Changes from live session"/></div><button id="gh-pr" class="btn-primary">Open pull request</button><p style="margin-top:14px"><a href="${esc(f.html_url)}" target="_blank" style="color:var(--accent)">View your fork on GitHub ↗</a></p>`);
    $("gh-pr").addEventListener("click", openPr);
  }
  async function openPr() {
    try {
      const title = ($("pr-title").value || "Changes from live session").trim();
      const r = await api("api/github/pr", { method: "POST", body: { head: S.gh.login + ":main", title } });
      forkBody(`<h3>Pull request opened ✓</h3><p><a href="${esc(r.url)}" target="_blank" style="color:var(--accent)">${esc(r.url)} ↗</a></p>`);
    } catch (e) { toast(e.message, "err"); }
  }

  boot();
})();
