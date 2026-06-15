/* Live Session — guest top bar + "Connect your AI" (multi-provider + CLI).

   Guests run on the HOST's daemon (no daemon setup, no Projects nav — that's why
   the host's .workflow-bar stays hidden). But AI actions must spend the GUEST's
   own credentials, never the host's. This script:

     1. Wraps fetch so every same-origin /__ request carries the guest's live
        token (X-Live-Token) AND, when set, their credentials:
          • X-Th-Llm-Key  — legacy single Anthropic key (back-compat).
          • X-Th-Llm-Keys — base64(JSON) map of per-provider API keys PLUS a
            "claudeCli" entry: a Claude Code subscription token (from
            `claude setup-token`, sk-ant-oat…) that runs the agent on the
            GUEST's own subscription via the CLI. The gate forwards these; the
            daemon spends them for that run only.
     2. Renders a slim guest top bar with an AI status pill + a Connect panel
        mirroring the host's API-key settings (keys live ONLY in this browser's
        localStorage — never on the host).
     3. Blocks AI endpoints until SOME credential is connected, prompting the
        panel instead of letting the run fail.

   Injected into the guest editor by the gate (after locks.js / cursors.js). */
(() => {
  "use strict";
  if (window.__thAiKey) return;
  window.__thAiKey = true;

  // Providers mirror the host's Settings · API keys (editor/prompts/media-models.js).
  // `id` must match the daemon's provider id (serve.py _PROVIDER_ENV_KEYS) so the
  // guest's key is used for that provider's runs. The special "claudeCli" row is
  // a Claude Code subscription token, not an API key — the daemon routes it to
  // CLAUDE_CODE_OAUTH_TOKEN so the agent runs on the guest's subscription.
  const CLI_ID = "claudeCli";
  const PROVIDERS = [
    { id: "anthropic",   label: "Anthropic · Claude",    ph: "sk-ant-…",  agent: true },
    { id: "openai",      label: "OpenAI",                ph: "sk-…",      agent: true },
    { id: "nanobanana",  label: "Google Gemini",         ph: "AIza… / key" },
    { id: "fal",         label: "fal.ai",                ph: "key" },
    { id: "xai",         label: "xAI · Grok Imagine",    ph: "xai-…" },
    { id: "elevenlabs",  label: "ElevenLabs",            ph: "key" },
    { id: "recraft",     label: "Recraft",               ph: "key" },
    { id: "leonardo",    label: "Leonardo.ai",           ph: "key" },
    { id: "bfl",         label: "Black Forest Labs",     ph: "key" },
    { id: "quiver",      label: "Quiver AI",             ph: "key" },
    { id: "volcengine",  label: "Volcengine Ark",        ph: "key" },
    { id: "meshy",       label: "Meshy",                 ph: "key" },
    { id: "imagerouter", label: "ImageRouter",           ph: "key" },
  ];

  const LS_PREFIX = "th-live-key-";
  const LS_LEGACY = "th-live-llm-key";   // pre-multi-provider single key
  const lsGet = (id) => { try { return (localStorage.getItem(LS_PREFIX + id) || "").trim(); } catch (e) { return ""; } };
  const lsSet = (id, v) => { try { v ? localStorage.setItem(LS_PREFIX + id, v) : localStorage.removeItem(LS_PREFIX + id); } catch (e) {} };

  // One-time migration: fold the old single Anthropic key into the new scheme.
  try {
    const legacy = (localStorage.getItem(LS_LEGACY) || "").trim();
    if (legacy && !lsGet("anthropic")) { lsSet("anthropic", legacy); }
    if (legacy) localStorage.removeItem(LS_LEGACY);
  } catch (e) {}

  // Map of every credential the guest has set (provider id → value, incl. claudeCli).
  function allKeys() {
    const out = {};
    for (const p of PROVIDERS) { const v = lsGet(p.id); if (v) out[p.id] = v; }
    const cli = lsGet(CLI_ID); if (cli) out[CLI_ID] = cli;
    return out;
  }
  const anyKey = () => Object.keys(allKeys()).length > 0;
  // Can the guest run AGENTS (Claude/Codex)? Needs an agent-capable API key OR a CLI token.
  const canAgent = () => !!(lsGet("anthropic") || lsGet("openai") || lsGet(CLI_ID));

  function keysHeader() {
    const m = allKeys();
    if (!Object.keys(m).length) return "";
    try { return btoa(JSON.stringify(m)); } catch (e) { return ""; }
  }

  // AI / agent endpoints — kept in sync with live.py _LLM_WRITE_PREFIXES.
  const LLM_RE = /\/__(llm_run|asset_generate|run|runs|system_runs|orchestrators|orchestrator_models|stream)\b/;

  // ── fetch wrapper — attach identity + credentials to same-origin /__ requests ──
  const _origFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    let url = "";
    try { url = (typeof input === "string") ? input : (input && input.url) || ""; } catch (e) {}
    if (url.indexOf("/__") !== 0) return _origFetch(input, init);
    // Block AI runs with no credential at all — flash the pill to draw the eye.
    // NB: do NOT auto-open the panel here — the editor fires background AI
    // calls (model lists, run polls) that also hit this block, and opening on
    // each one made the panel reopen the instant you closed it. The flash is
    // enough of a nudge; the user opens the panel by clicking the pill.
    if (LLM_RE.test(url) && !anyKey()) {
      flash();
      return Promise.resolve(new Response(
        JSON.stringify({ error: "llm-key-required", message: "Connect your own AI (API key or Claude subscription) to run agents." }),
        { status: 412, headers: { "Content-Type": "application/json" } }));
    }
    init = Object.assign({}, init);
    const headers = new Headers((init.headers) || (typeof input !== "string" && input && input.headers) || {});
    try { if (window.__thLiveToken) headers.set("X-Live-Token", window.__thLiveToken); } catch (e) {}
    const anth = lsGet("anthropic");
    if (anth) headers.set("X-Th-Llm-Key", anth);   // legacy single-key path
    const blob = keysHeader();
    if (blob) headers.set("X-Th-Llm-Keys", blob);  // full multi-provider + CLI map
    init.headers = headers;
    return _origFetch(input, init);
  };

  // ── slim guest top bar ─────────────────────────────────────────────────────
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  let barEl = null, pillEl = null;

  function injectStyle() {
    if (document.getElementById("th-ai-style")) return;
    const style = document.createElement("style");
    style.id = "th-ai-style";
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
      "#th-live-bar .th-ai-flash{animation:th-ai-flash .35s ease 2}" +
      // panel
      "#th-ai-scrim{position:fixed;inset:0;z-index:99998;background:rgba(15,23,42,.45);display:flex;" +
      "align-items:flex-start;justify-content:center;padding:64px 16px}" +
      "#th-ai-panel{width:440px;max-width:100%;max-height:80vh;overflow:auto;background:var(--surface,#fff);" +
      "color:var(--text,#111827);border:1px solid var(--border,#e5e7eb);border-radius:14px;" +
      "box-shadow:0 24px 64px rgba(0,0,0,.28);font:400 13px -apple-system,system-ui,sans-serif}" +
      "#th-ai-panel .th-ai-hd{display:flex;align-items:center;gap:8px;padding:16px 18px 8px}" +
      "#th-ai-panel .th-ai-hd b{font-size:15px;font-weight:700}" +
      "#th-ai-panel .th-ai-x{margin-left:auto;cursor:pointer;border:none;background:none;font-size:20px;line-height:1;" +
      "color:var(--text-muted,#6b7280);padding:2px 6px;border-radius:6px}" +
      "#th-ai-panel .th-ai-sub{padding:0 18px 10px;color:var(--text-muted,#6b7280);font-size:12px;line-height:1.5}" +
      "#th-ai-panel .th-ai-sec{padding:10px 18px;border-top:1px solid var(--border,#eef1f4)}" +
      "#th-ai-panel .th-ai-sec h4{margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:.04em;" +
      "text-transform:uppercase;color:var(--text-muted,#6b7280)}" +
      "#th-ai-panel .th-ai-cli{background:rgba(99,102,241,.07)}" +
      "#th-ai-panel .th-ai-row{display:flex;align-items:center;gap:10px;margin:7px 0}" +
      "#th-ai-panel .th-ai-row label{flex:0 0 132px;font-size:12px;font-weight:500}" +
      "#th-ai-panel .th-ai-row .th-ai-dot{flex:0 0 auto;width:7px;height:7px;border-radius:50%;background:#cbd5e1}" +
      "#th-ai-panel .th-ai-row .th-ai-dot.on{background:#10b981}" +
      "#th-ai-panel input{flex:1;min-width:0;padding:7px 9px;border:1px solid var(--border,#d1d5db);border-radius:8px;" +
      "background:var(--bg,#fff);color:var(--text,#111827);font:inherit;font-size:12px}" +
      "#th-ai-panel input:focus{outline:none;border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,.15)}" +
      "#th-ai-panel code{background:rgba(127,127,127,.14);padding:1px 5px;border-radius:5px;font-size:11px}" +
      "#th-ai-panel .th-ai-ft{padding:12px 18px;border-top:1px solid var(--border,#eef1f4);display:flex;gap:8px;align-items:center}" +
      "#th-ai-panel .th-ai-ft .th-ai-note{font-size:11px;color:var(--text-muted,#6b7280);flex:1}" +
      "#th-ai-panel button.th-ai-done{padding:7px 16px;border:none;border-radius:8px;background:#111827;color:#fff;" +
      "font-weight:600;font-size:13px;cursor:pointer}";
    document.head.appendChild(style);
  }

  function ensureBar() {
    if (barEl && barEl.isConnected) return;
    injectStyle();
    barEl = document.createElement("div");
    barEl.id = "th-live-bar";
    const title = document.createElement("div");
    let proj = ""; try { proj = new URLSearchParams(location.search).get("project") || ""; } catch (e) {}
    title.innerHTML = '<span style="opacity:.6">Live session</span>' + (proj ? ' · <b>' + esc(proj) + "</b>" : "");
    pillEl = document.createElement("button");
    pillEl.className = "th-ai-pill";
    pillEl.onclick = openPanel;
    barEl.appendChild(title);
    barEl.appendChild(pillEl);
    document.body.appendChild(barEl);
    renderPill();
  }

  function renderPill() {
    if (!pillEl) return;
    const n = Object.keys(allKeys()).length;
    const on = n > 0;
    pillEl.className = "th-ai-pill " + (on ? "th-ai-on" : "th-ai-off");
    pillEl.innerHTML = (on ? "● " : "○ ") + (on ? ("AI connected" + (n > 1 ? " · " + n : "")) : "Connect your AI");
    pillEl.title = on ? "Your credentials are set (stored only in this browser). Click to manage."
                      : "Run agents with your own API key or Claude subscription (stored only in this browser).";
  }

  function flash() {
    ensureBar();
    if (!pillEl) return;
    pillEl.classList.remove("th-ai-flash"); void pillEl.offsetWidth; pillEl.classList.add("th-ai-flash");
  }

  // ── Connect panel ───────────────────────────────────────────────────────────
  let scrimEl = null;
  function closePanel() { if (scrimEl) { scrimEl.remove(); scrimEl = null; } renderPill(); }

  function row(id, label, ph) {
    const wrap = document.createElement("div");
    wrap.className = "th-ai-row";
    const dot = document.createElement("span");
    dot.className = "th-ai-dot" + (lsGet(id) ? " on" : "");
    const lab = document.createElement("label");
    lab.textContent = label;
    const inp = document.createElement("input");
    inp.type = "password";
    inp.autocomplete = "off";
    inp.spellcheck = false;
    inp.placeholder = ph;
    inp.value = lsGet(id);
    const commit = () => { lsSet(id, inp.value.trim()); dot.className = "th-ai-dot" + (lsGet(id) ? " on" : ""); renderPill(); };
    inp.addEventListener("change", commit);
    inp.addEventListener("blur", commit);
    wrap.appendChild(dot); wrap.appendChild(lab); wrap.appendChild(inp);
    return wrap;
  }

  function openPanel() {
    injectStyle();
    if (scrimEl) { scrimEl.remove(); scrimEl = null; }
    scrimEl = document.createElement("div");
    scrimEl.id = "th-ai-scrim";
    scrimEl.addEventListener("mousedown", (e) => { if (e.target === scrimEl) closePanel(); });

    const panel = document.createElement("div");
    panel.id = "th-ai-panel";

    const hd = document.createElement("div");
    hd.className = "th-ai-hd";
    hd.innerHTML = "<b>Connect your AI</b>";
    const x = document.createElement("button");
    x.className = "th-ai-x"; x.innerHTML = "&times;"; x.title = "Close"; x.onclick = closePanel;
    hd.appendChild(x);
    panel.appendChild(hd);

    const sub = document.createElement("div");
    sub.className = "th-ai-sub";
    sub.innerHTML = "Runs in this live session use <b>your</b> credentials — the host never sees them. " +
                    "Everything below is stored only in this browser.";
    panel.appendChild(sub);

    // Claude subscription (local CLI) section — highlighted.
    const cli = document.createElement("div");
    cli.className = "th-ai-sec th-ai-cli";
    cli.innerHTML = "<h4>Use your Claude subscription (local CLI)</h4>";
    const cliNote = document.createElement("div");
    cliNote.className = "th-ai-sub";
    cliNote.style.padding = "0 0 8px";
    cliNote.innerHTML = "Run <code>claude setup-token</code> in your terminal and paste the <code>sk-ant-oat…</code> " +
                        "token. Agents then run on your own Claude Pro/Max subscription via the CLI — no API key, no host billing.";
    cli.appendChild(cliNote);
    cli.appendChild(row(CLI_ID, "Claude token", "sk-ant-oat01-…"));
    panel.appendChild(cli);

    // Agent API keys.
    const agentSec = document.createElement("div");
    agentSec.className = "th-ai-sec";
    agentSec.innerHTML = "<h4>Agent API keys</h4>";
    for (const p of PROVIDERS) { if (p.agent) agentSec.appendChild(row(p.id, p.label, p.ph)); }
    panel.appendChild(agentSec);

    // Media / image / video / audio providers.
    const mediaSec = document.createElement("div");
    mediaSec.className = "th-ai-sec";
    mediaSec.innerHTML = "<h4>Image · video · audio providers</h4>";
    for (const p of PROVIDERS) { if (!p.agent) mediaSec.appendChild(row(p.id, p.label, p.ph)); }
    panel.appendChild(mediaSec);

    const ft = document.createElement("div");
    ft.className = "th-ai-ft";
    const note = document.createElement("div");
    note.className = "th-ai-note";
    note.textContent = "Keys are saved as you type. Clear a field to disconnect it.";
    const done = document.createElement("button");
    done.className = "th-ai-done"; done.textContent = "Done"; done.onclick = closePanel;
    ft.appendChild(note); ft.appendChild(done);
    panel.appendChild(ft);

    scrimEl.appendChild(panel);
    document.body.appendChild(scrimEl);
    const first = panel.querySelector("input");
    if (first) { try { first.focus(); } catch (e) {} }
  }

  // Mount once the editor shell exists.
  const t = setInterval(() => {
    if (document.getElementById("root") || document.querySelector(".workflow-root") || document.body) {
      clearInterval(t); ensureBar();
    }
  }, 300);
  setTimeout(() => clearInterval(t), 20000);
})();
