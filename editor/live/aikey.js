/* Live Session — guest top bar + "Connect your AI".

   Guests run on the HOST's daemon (no daemon setup, no Projects nav — that's why
   the host's .workflow-bar stays hidden). But AI actions must spend the GUEST's
   own credentials, never the host's. This script:

     1. Wraps fetch so every same-origin /__ request carries the guest's live
        token (X-Live-Token) AND, when set, their API key (X-Th-Llm-Key). The
        gate forwards the key; the daemon uses it for that run only.
     2. Renders a slim guest top bar with an AI status pill + Connect control
        (the key is stored ONLY in this browser's localStorage — never on the
        host).
     3. Blocks AI endpoints until a key is connected, prompting "Connect your AI"
        instead of letting the run fail.

   Injected into the guest editor by the gate (after locks.js / cursors.js). */
(() => {
  "use strict";
  if (window.__thAiKey) return;
  window.__thAiKey = true;

  const LS_KEY = "th-live-llm-key";
  const getKey = () => { try { return (localStorage.getItem(LS_KEY) || "").trim(); } catch (e) { return ""; } };
  const setKey = (k) => { try { k ? localStorage.setItem(LS_KEY, k) : localStorage.removeItem(LS_KEY); } catch (e) {} };
  // AI / agent endpoints — kept in sync with live.py _LLM_WRITE_PREFIXES.
  const LLM_RE = /\/__(llm_run|asset_generate|run|runs|system_runs|orchestrators|orchestrator_models|stream)\b/;

  // ── fetch wrapper — attach identity + key to same-origin /__ requests ──────
  const _origFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    let url = "";
    try { url = (typeof input === "string") ? input : (input && input.url) || ""; } catch (e) {}
    // Only touch same-origin daemon endpoints (apiUrl returns "/__…?project=").
    if (url.indexOf("/__") !== 0) return _origFetch(input, init);
    // Block AI runs with no key — prompt instead of failing on the server.
    if (LLM_RE.test(url) && !getKey()) {
      flash();
      return Promise.resolve(new Response(
        JSON.stringify({ error: "llm-key-required", message: "Connect your own AI (API key) to run agents." }),
        { status: 412, headers: { "Content-Type": "application/json" } }));
    }
    init = Object.assign({}, init);
    const headers = new Headers((init.headers) || (typeof input !== "string" && input && input.headers) || {});
    try { if (window.__thLiveToken) headers.set("X-Live-Token", window.__thLiveToken); } catch (e) {}
    const k = getKey();
    if (k) headers.set("X-Th-Llm-Key", k);
    init.headers = headers;
    return _origFetch(input, init);   // init overrides input's headers for both string + Request
  };

  // ── slim guest top bar ─────────────────────────────────────────────────────
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  let barEl = null, pillEl = null;

  function ensureBar() {
    if (barEl && barEl.isConnected) return;
    const style = document.createElement("style");
    style.textContent =
      "#th-live-bar{position:fixed;top:0;left:0;right:0;height:40px;z-index:99996;display:flex;align-items:center;" +
      "gap:10px;padding:0 14px;background:var(--surface,#fff);border-bottom:1px solid var(--border,#e5e7eb);" +
      "font:500 13px -apple-system,system-ui,sans-serif;color:var(--text,#111827)}" +
      "body>#root,#root>.workflow-door,.workflow-root{margin-top:40px!important}" +
      "#th-live-bar .th-ai-pill{margin-left:auto;display:inline-flex;align-items:center;gap:6px;padding:4px 10px;" +
      "border-radius:999px;font-weight:600;font-size:12px;cursor:pointer;border:1px solid transparent}" +
      "#th-live-bar .th-ai-on{background:rgba(16,185,129,.12);color:#059669;border-color:rgba(16,185,129,.3)}" +
      "#th-live-bar .th-ai-off{background:rgba(245,23,42,.10);color:#dc2626;border-color:rgba(245,23,42,.3)}" +
      "@keyframes th-ai-flash{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}" +
      "#th-live-bar .th-ai-flash{animation:th-ai-flash .35s ease 2}";
    document.head.appendChild(style);

    barEl = document.createElement("div");
    barEl.id = "th-live-bar";
    const title = document.createElement("div");
    let proj = ""; try { proj = new URLSearchParams(location.search).get("project") || ""; } catch (e) {}
    title.innerHTML = '<span style="opacity:.6">Live session</span>' + (proj ? ' · <b>' + esc(proj) + "</b>" : "");
    pillEl = document.createElement("button");
    pillEl.className = "th-ai-pill";
    pillEl.onclick = connectFlow;
    barEl.appendChild(title);
    barEl.appendChild(pillEl);
    document.body.appendChild(barEl);
    renderPill();
  }

  function renderPill() {
    if (!pillEl) return;
    const on = !!getKey();
    pillEl.className = "th-ai-pill " + (on ? "th-ai-on" : "th-ai-off");
    const dot = on ? "●" : "○";
    pillEl.innerHTML = dot + " " + (on ? "AI connected" : "Connect your AI");
    pillEl.title = on ? "Your API key is set (stored only in this browser). Click to change or disconnect."
                      : "Run agents with your own API key (stored only in this browser).";
  }

  function flash() {
    ensureBar();
    if (!pillEl) return;
    pillEl.classList.remove("th-ai-flash"); void pillEl.offsetWidth; pillEl.classList.add("th-ai-flash");
  }

  function connectFlow() {
    const cur = getKey();
    const msg = cur
      ? "Your AI is connected (key stored only in this browser).\n\nPaste a new key to change it, or leave blank + OK to DISCONNECT:"
      : "Paste your Anthropic API key (sk-ant-…).\n\nIt is stored ONLY in this browser and sent only to run YOUR agents — the host never sees it.";
    const v = window.prompt(msg, "");
    if (v === null) return;               // cancelled
    const k = v.trim();
    if (k && !/^sk-/.test(k)) {
      if (!window.confirm("That doesn't look like an API key (expected sk-…). Save it anyway?")) return;
    }
    setKey(k);
    renderPill();
  }

  // Mount once the editor shell exists.
  const t = setInterval(() => {
    if (document.getElementById("root") || document.querySelector(".workflow-root") || document.body) {
      clearInterval(t); ensureBar();
    }
  }, 300);
  setTimeout(() => clearInterval(t), 20000);
})();
