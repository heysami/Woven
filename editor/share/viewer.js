/* Woven share viewer — visitor-facing review surface for ONE shared
   prototype. Served by the share gate at /s/<token>/ (see editor/shares.py).

   Architecture notes:
   • The prototype lives in a SAME-ORIGIN iframe (gate serves both this page
     and the prototype files), so we can reach contentDocument directly:
     element picking, pin anchoring, scroll/highlight all work without any
     script injected into the prototype's own bundle.
   • Comments anchor to elements as { selector, tag, text } — selector is
     the primary locator; tag+text are a fuzzy fallback for when the
     prototype's DOM drifts after agent edits. Pins are {x,y} fractions of
     the element's box so they survive responsive reflow.
   • No SSE for visitors — plain polling (8s) keeps the gate surface tiny.
   • Identity is localStorage-only ("woven-share-identity"); the gate
     enforces name-required (and email-required when the share's emailGate
     is on) at POST time — the modal here is UX, the gate is policy. */

/* global React, ReactDOM, htm */
(() => {
  const html = htm.bind(React.createElement);
  const { useState, useEffect, useRef, useMemo, useCallback } = React;

  // Woven line-icon — mirrors editor's Icon.Comment (16-box, 1.5pt round
  // stroke). `size` defaults to the editor's 14px glyph footprint.
  const CommentIcon = ({ size = 14 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <path d="M3 4a1 1 0 011-1h8a1 1 0 011 1v6a1 1 0 01-1 1H7l-3 3v-3a1 1 0 01-1-1z"/>
    </svg>`;

  // ── URL plumbing ──────────────────────────────────────────────────────
  // location.pathname is /s/<token>/ (gate 301s the slash-less form).
  const BASE = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  const api = (p) => BASE + "api/" + p;

  const IDENTITY_KEY = "woven-share-identity";
  const loadIdentity = () => {
    try { return JSON.parse(localStorage.getItem(IDENTITY_KEY) || "null") || null; }
    catch { return null; }
  };
  const saveIdentity = (id) => {
    try { localStorage.setItem(IDENTITY_KEY, JSON.stringify(id)); } catch {}
  };

  const timeAgo = (iso) => {
    if (!iso) return "";
    const then = new Date(iso).getTime();
    if (!isFinite(then)) return iso;
    const s = Math.max(0, (Date.now() - then) / 1000);
    if (s < 60) return "just now";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    if (s < 86400) return Math.floor(s / 3600) + "h ago";
    return Math.floor(s / 86400) + "d ago";
  };

  // ── Element anchoring helpers (operate on the IFRAME's document) ─────
  const cssPath = (el) => {
    if (!el || el.nodeType !== 1) return "";
    const parts = [];
    let cur = el;
    while (cur && cur.nodeType === 1 && cur.tagName !== "HTML" && cur.tagName !== "BODY") {
      // id short-circuit — unique enough, stop climbing.
      if (cur.id && /^[A-Za-z][\w-]*$/.test(cur.id)) {
        parts.unshift("#" + cur.id);
        return parts.join(" > ");
      }
      let part = cur.tagName.toLowerCase();
      const cls = Array.from(cur.classList || [])
        .filter((c) => /^[A-Za-z_][\w-]*$/.test(c)).slice(0, 2);
      if (cls.length) part += "." + cls.join(".");
      const parent = cur.parentElement;
      if (parent) {
        const sibs = Array.from(parent.children).filter((s) => s.tagName === cur.tagName);
        if (sibs.length > 1) part += ":nth-of-type(" + (sibs.indexOf(cur) + 1) + ")";
      }
      parts.unshift(part);
      cur = parent;
    }
    return parts.join(" > ");
  };

  const resolveEl = (doc, anchor) => {
    if (!doc || !anchor) return null;
    if (anchor.selector) {
      try {
        const el = doc.querySelector(anchor.selector);
        if (el) return el;
      } catch {}
    }
    // Fuzzy fallback: same tag + same leading text snippet.
    if (anchor.tag && anchor.text) {
      try {
        const cands = doc.querySelectorAll(anchor.tag);
        for (const c of cands) {
          if ((c.textContent || "").trim().slice(0, 200) === anchor.text) return c;
        }
      } catch {}
    }
    return null;
  };

  // Inject (once per document) the hover/flash styles used by comment mode.
  const ensureDocStyles = (doc) => {
    if (!doc || doc.getElementById("__sv_styles")) return;
    const st = doc.createElement("style");
    st.id = "__sv_styles";
    st.textContent = [
      ".__sv-hover { outline: 2px solid #16a06b !important; outline-offset: 2px !important; cursor: crosshair !important; }",
      ".__sv-flash { outline: 3px solid #16a06b !important; outline-offset: 3px !important; transition: outline-color .25s; }",
      ".__sv-flash-fade { outline-color: transparent !important; }",
    ].join("\n");
    (doc.head || doc.documentElement).appendChild(st);
  };

  // Strip the gate prefix off the iframe's pathname → page id relative to
  // source/<slug>/ ("index.html", "screens/detail.html", …) + hash.
  const pageOfWin = (win, prototype) => {
    try {
      const prefix = BASE + "p/source/" + prototype + "/";
      let p = win.location.pathname;
      p = p.startsWith(prefix) ? p.slice(prefix.length) : p.split("/").pop();
      if (!p) p = "index.html";
      return p + (win.location.hash || "");
    } catch {
      return "index.html";
    }
  };
  const pathPart = (page) => (page || "index.html").split("#")[0] || "index.html";

  // ── Identity modal ────────────────────────────────────────────────────
  function IdentityModal({ emailGate, initial, onDone, onCancel, reason }) {
    const [name, setName] = useState(initial?.name || "");
    const [email, setEmail] = useState(initial?.email || "");
    const [err, setErr] = useState(null);
    const ok = name.trim() && (!emailGate || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim()));
    const submit = () => {
      if (!name.trim()) { setErr("Please enter your name."); return; }
      if (emailGate && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
        setErr("A valid email is required for this share."); return;
      }
      onDone({ name: name.trim(), email: email.trim() });
    };
    return html`
      <div className="sv-modal-scrim">
        <div className="sv-modal">
          <h2>Introduce yourself</h2>
          <p>${reason || (emailGate
            ? "This shared prototype asks reviewers to sign comments with a name and email."
            : "Add a name so the team knows who's commenting.")}</p>
          ${err && html`<div className="sv-modal-err">${err}</div>`}
          <div className="sv-field">
            <label>Name</label>
            <input value=${name} autoFocus
              onInput=${(e) => setName(e.target.value)}
              onKeyDown=${(e) => { if (e.key === "Enter") submit(); }}
              placeholder="Ada Lovelace"/>
          </div>
          ${emailGate && html`
            <div className="sv-field">
              <label>Email</label>
              <input value=${email} type="email"
                onInput=${(e) => setEmail(e.target.value)}
                onKeyDown=${(e) => { if (e.key === "Enter") submit(); }}
                placeholder="ada@example.com"/>
            </div>
          `}
          <div className="sv-modal-row">
            ${onCancel && html`<button className="sv-btn" onClick=${onCancel}>Cancel</button>`}
            <button className="sv-btn sv-btn-primary" disabled=${!ok} onClick=${submit}>Continue</button>
          </div>
        </div>
      </div>
    `;
  }

  // ── One sidebar card ──────────────────────────────────────────────────
  function CommentCard({ c, num, active, onFocus, onReply, onStatus, onDelete, onEdit }) {
    const [replyText, setReplyText] = useState("");
    const [busy, setBusy] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editText, setEditText] = useState(c.text);
    const doReply = async () => {
      const t = replyText.trim();
      if (!t || busy) return;
      setBusy(true);
      try { await onReply(c, t); setReplyText(""); } finally { setBusy(false); }
    };
    const startEdit = () => { setEditText(c.text); setEditing(true); };
    const cancelEdit = () => { setEditing(false); setEditText(c.text); };
    const doEdit = async () => {
      const t = editText.trim();
      if (!t || busy) return;
      setBusy(true);
      try { await onEdit(c, t); setEditing(false); } finally { setBusy(false); }
    };
    const st = c.status || "open";
    return html`
      <div
        className=${"sv-comment" + (active ? " is-active" : "") + (st !== "open" ? " is-done" : "")}
        onClick=${() => onFocus(c)}
      >
        <div className="sv-comment-head">
          <span className="sv-comment-pin-num">${num}</span>
          <span className="sv-comment-author">${(c.author && c.author.name) || "Anonymous"}</span>
          ${st === "done" && html`<span className="sv-status-chip done">done</span>`}
          ${st === "archived" && html`<span className="sv-status-chip archived">archived</span>`}
          ${c.processedAt && html`<span className="sv-status-chip processed" title="Sent to the build agent">processed</span>`}
          <span className="sv-comment-time">${timeAgo(c.createdAt)}${c.editedAt ? " · edited" : ""}</span>
        </div>
        <div className="sv-comment-page" title=${c.page}>${c.page}${c.anchor && c.anchor.selector ? " · " + c.anchor.selector : ""}</div>
        ${editing ? html`
          <div className="sv-edit-row" onClick=${(e) => e.stopPropagation()}>
            <textarea className="sv-reply-input" autoFocus
              value=${editText}
              onInput=${(e) => setEditText(e.target.value)}
              onKeyDown=${(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) doEdit();
                if (e.key === "Escape") cancelEdit();
              }}></textarea>
            <div className="sv-edit-actions">
              <button className="sv-mini-btn" disabled=${busy} onClick=${cancelEdit}>Cancel</button>
              <button className="sv-mini-btn" disabled=${busy || !editText.trim()} onClick=${doEdit}>Save</button>
            </div>
          </div>
        ` : html`<div className="sv-comment-text">${c.text}</div>`}
        ${(c.replies || []).length > 0 && html`
          <div className="sv-replies">
            ${c.replies.map((r) => html`
              <div className="sv-reply" key=${r.id}>
                <div className="sv-reply-head">
                  <span className="sv-reply-author">${(r.author && r.author.name) || "Anonymous"}</span>
                  <span className="sv-reply-time">${timeAgo(r.createdAt)}</span>
                </div>
                <div className="sv-reply-text">${r.text}</div>
              </div>
            `)}
          </div>
        `}
        <div className="sv-reply-row" onClick=${(e) => e.stopPropagation()}>
          <input className="sv-reply-input" placeholder="Reply…"
            value=${replyText}
            onInput=${(e) => setReplyText(e.target.value)}
            onKeyDown=${(e) => { if (e.key === "Enter") doReply(); }}/>
          ${replyText.trim() && html`<button className="sv-mini-btn" disabled=${busy} onClick=${doReply}>Send</button>`}
        </div>
        <div className="sv-comment-actions" onClick=${(e) => e.stopPropagation()}>
          ${!editing && html`<button className="sv-mini-btn" onClick=${startEdit}>Edit</button>`}
          ${st !== "done" && html`<button className="sv-mini-btn" onClick=${() => onStatus(c, "done")}>✓ Done</button>`}
          ${st === "done" && html`<button className="sv-mini-btn" onClick=${() => onStatus(c, "open")}>Reopen</button>`}
          ${st !== "archived" && html`<button className="sv-mini-btn" onClick=${() => onStatus(c, "archived")}>Archive</button>`}
          <button className="sv-mini-btn danger" onClick=${() => onDelete(c)}>Delete</button>
        </div>
      </div>
    `;
  }

  // ── App ───────────────────────────────────────────────────────────────
  function App() {
    const [meta, setMeta] = useState(null);
    const [metaErr, setMetaErr] = useState(null);
    const [identity, setIdentity] = useState(loadIdentity);
    const [needIdentity, setNeedIdentity] = useState(false);     // modal open
    const [identityReason, setIdentityReason] = useState(null);
    const [comments, setComments] = useState([]);
    const [filter, setFilter] = useState("open");
    const [commentMode, setCommentMode] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [draft, setDraft] = useState(null);    // {anchor, pin, page, x, y}
    const [draftText, setDraftText] = useState("");
    const [activeId, setActiveId] = useState(null);
    const [pins, setPins] = useState([]);        // [{id, x, y, num, done, draft}]
    const [page, setPage] = useState("index.html");
    const [error, setError] = useState(null);
    const [posting, setPosting] = useState(false);

    const iframeRef = useRef(null);
    const commentModeRef = useRef(false); commentModeRef.current = commentMode;
    const draftRef = useRef(null); draftRef.current = draft;
    const hoverElRef = useRef(null);
    const cleanupArmRef = useRef(null);

    const showError = (msg) => { setError(msg); setTimeout(() => setError(null), 5000); };

    // Boot: meta + comments. Meta failure = revoked/unknown share.
    useEffect(() => {
      fetch(api("meta")).then((r) => {
        if (!r.ok) throw new Error("share unavailable");
        return r.json();
      }).then(setMeta).catch(() => setMetaErr("This share link is no longer available."));
    }, []);

    const refetchComments = useCallback(() => {
      fetch(api("comments")).then((r) => (r.ok ? r.json() : { comments: [] }))
        .then((j) => setComments(j.comments || []))
        .catch(() => {});
    }, []);
    useEffect(() => {
      if (!meta) return;
      refetchComments();
      const t = setInterval(refetchComments, 8000);
      return () => clearInterval(t);
    }, [meta, refetchComments]);

    // Email-gated shares introduce the visitor up front; open shares ask
    // lazily on the first comment instead.
    useEffect(() => {
      if (!meta) return;
      if (meta.emailGate && !(identity && identity.name && identity.email)) {
        setNeedIdentity(true);
      }
    }, [meta]);

    // Stable pin numbers: position in the full createdAt-ordered list.
    const numbered = useMemo(() => {
      const sorted = [...comments].sort((a, b) => (a.createdAt || "").localeCompare(b.createdAt || ""));
      const numOf = new Map(sorted.map((c, i) => [c.id, i + 1]));
      return { sorted, numOf };
    }, [comments]);

    const visibleComments = useMemo(() => {
      let list = numbered.sorted;
      if (filter !== "all") list = list.filter((c) => (c.status || "open") === filter);
      return [...list].reverse();   // newest first in the sidebar
    }, [numbered, filter]);

    const counts = useMemo(() => {
      const c = { open: 0, done: 0, archived: 0 };
      for (const x of comments) c[(x.status || "open")] = (c[(x.status || "open")] || 0) + 1;
      return c;
    }, [comments]);

    // ── Pin layout loop — repositions pins as the iframe scrolls/reflows.
    useEffect(() => {
      let alive = true;
      const tick = () => {
        if (!alive) return;
        const frame = iframeRef.current;
        const doc = frame && frame.contentDocument;
        const out = [];
        if (doc && doc.readyState !== "loading") {
          const curPath = pathPart(page);
          for (const c of comments) {
            if ((c.status || "open") === "archived") continue;
            if (pathPart(c.page) !== curPath) continue;
            const el = resolveEl(doc, c.anchor);
            if (!el) continue;
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            // Pin label is the thread's message count (comment + replies).
            // A lone comment shows no number; a reply makes it 2, and so on.
            const msgs = 1 + ((c.replies && c.replies.length) || 0);
            out.push({
              id: c.id,
              num: msgs > 1 ? msgs : "",
              x: r.left + r.width * ((c.pin && c.pin.x) ?? 0.5),
              y: r.top + r.height * ((c.pin && c.pin.y) ?? 0.5),
              done: (c.status || "open") === "done",
            });
          }
        }
        const d = draftRef.current;
        if (d) out.push({ id: "__draft", num: "+", x: d.x, y: d.y, draft: true });
        setPins((prev) => {
          if (prev.length === out.length &&
              prev.every((p, i) => p.id === out[i].id && p.x === out[i].x && p.y === out[i].y
                                   && p.done === out[i].done && p.num === out[i].num)) return prev;
          return out;
        });
        raf = setTimeout(tick, 120);
      };
      let raf = setTimeout(tick, 120);
      return () => { alive = false; clearTimeout(raf); };
    }, [comments, page, numbered]);

    // ── Comment-mode arming — installs hover/click hooks in the iframe doc.
    const disarm = useCallback(() => {
      if (cleanupArmRef.current) { cleanupArmRef.current(); cleanupArmRef.current = null; }
    }, []);
    const arm = useCallback(() => {
      disarm();
      const frame = iframeRef.current;
      const doc = frame && frame.contentDocument;
      const win = frame && frame.contentWindow;
      if (!doc || !win || !meta) return;
      ensureDocStyles(doc);
      const onMove = (ev) => {
        const t = ev.target;
        if (hoverElRef.current === t) return;
        if (hoverElRef.current) { try { hoverElRef.current.classList.remove("__sv-hover"); } catch {} }
        hoverElRef.current = (t && t.nodeType === 1 && t.tagName !== "HTML" && t.tagName !== "BODY") ? t : null;
        if (hoverElRef.current) { try { hoverElRef.current.classList.add("__sv-hover"); } catch {} }
      };
      const onClick = (ev) => {
        if (!commentModeRef.current) return;
        ev.preventDefault(); ev.stopPropagation();
        const el = (ev.target && ev.target.nodeType === 1) ? ev.target : null;
        if (!el || el.tagName === "HTML" || el.tagName === "BODY") return;
        const r = el.getBoundingClientRect();
        const pin = {
          x: r.width ? Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) : 0.5,
          y: r.height ? Math.max(0, Math.min(1, (ev.clientY - r.top) / r.height)) : 0.5,
        };
        setDraft({
          anchor: {
            selector: cssPath(el),
            tag: el.tagName.toLowerCase(),
            text: (el.textContent || "").trim().slice(0, 200),
          },
          pin,
          page: pageOfWin(win, meta.prototype),
          x: ev.clientX, y: ev.clientY,
        });
        setDraftText("");
        setCommentMode(false);
      };
      doc.addEventListener("mousemove", onMove, true);
      doc.addEventListener("click", onClick, true);
      cleanupArmRef.current = () => {
        try { doc.removeEventListener("mousemove", onMove, true); } catch {}
        try { doc.removeEventListener("click", onClick, true); } catch {}
        if (hoverElRef.current) { try { hoverElRef.current.classList.remove("__sv-hover"); } catch {} }
        hoverElRef.current = null;
      };
    }, [meta, disarm]);

    useEffect(() => {
      if (commentMode) arm(); else disarm();
      return disarm;
    }, [commentMode, arm, disarm]);

    // Esc anywhere in the viewer chrome exits comment mode / the composer.
    // (Esc pressed while the IFRAME has focus lands in the prototype's doc
    // instead — acceptable; the hint pill stays visible as the off switch.)
    useEffect(() => {
      const onKey = (e) => {
        if (e.key === "Escape") { setCommentMode(false); setDraft(null); }
      };
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }, []);

    // ── Iframe lifecycle — track page, rearm comment mode after navigation.
    const onFrameLoad = useCallback(() => {
      const frame = iframeRef.current;
      const win = frame && frame.contentWindow;
      if (!win || !meta) return;
      const sync = () => setPage(pageOfWin(win, meta.prototype));
      sync();
      try { win.addEventListener("hashchange", sync); } catch {}
      try { ensureDocStyles(frame.contentDocument); } catch {}
      if (commentModeRef.current) arm();
    }, [meta, arm]);

    // ── Focus a comment: navigate if needed, then scroll + flash.
    const focusComment = useCallback((c) => {
      setActiveId(c.id);
      const frame = iframeRef.current;
      if (!frame || !meta) return;
      const go = () => {
        const doc = frame.contentDocument;
        const el = resolveEl(doc, c.anchor);
        if (!el) return;
        try { el.scrollIntoView({ behavior: "smooth", block: "center" }); } catch {}
        try {
          el.classList.add("__sv-flash");
          setTimeout(() => { try { el.classList.add("__sv-flash-fade"); } catch {} }, 1100);
          setTimeout(() => {
            try { el.classList.remove("__sv-flash", "__sv-flash-fade"); } catch {}
          }, 1700);
        } catch {}
      };
      if (pathPart(c.page) !== pathPart(page)) {
        const onceLoad = () => { frame.removeEventListener("load", onceLoad); setTimeout(go, 250); };
        frame.addEventListener("load", onceLoad);
        frame.src = BASE + "p/source/" + meta.prototype + "/" + (c.page || "index.html");
      } else if (c.page && c.page.includes("#") && frame.contentWindow) {
        try { frame.contentWindow.location.hash = c.page.split("#")[1] || ""; } catch {}
        setTimeout(go, 250);
      } else {
        go();
      }
    }, [meta, page]);

    // ── Mutations ─────────────────────────────────────────────────────
    const requireIdentity = (reason) => {
      if (identity && identity.name && (!meta.emailGate || identity.email)) return true;
      setIdentityReason(reason || null);
      setNeedIdentity(true);
      return false;
    };

    const submitDraft = async () => {
      const d = draft;
      const text = draftText.trim();
      if (!d || !text || posting) return;
      if (!requireIdentity()) return;
      setPosting(true);
      try {
        const r = await fetch(api("comments"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ page: d.page, anchor: d.anchor, pin: d.pin, text, author: identity }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || "failed to post comment");
        setDraft(null); setDraftText("");
        refetchComments();
      } catch (e) {
        showError(String(e.message || e));
      } finally { setPosting(false); }
    };

    const mutate = async (path, body) => {
      try {
        const r = await fetch(api(path), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body || {}),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || "request failed");
        refetchComments();
      } catch (e) { showError(String(e.message || e)); }
    };
    const onReply = async (c, text) => {
      if (!requireIdentity("Add a name to reply.")) return;
      await mutate("comments/" + c.id + "/reply", { text, author: identity });
    };
    const onEdit = async (c, text) => {
      if (!requireIdentity("Add a name to edit a comment.")) return;
      await mutate("comments/" + c.id + "/edit", { text, author: identity });
    };
    const onStatus = (c, status) => mutate("comments/" + c.id + "/status", { status });
    const onDelete = (c) => {
      if (confirm("Delete this comment thread?")) mutate("comments/" + c.id + "/delete", {});
    };

    // ── Render ────────────────────────────────────────────────────────
    if (metaErr) {
      return html`<div className="sv-app"><div className="sv-empty" style=${{ marginTop: 120 }}>
        <b>Link unavailable</b>${metaErr}
      </div></div>`;
    }
    if (!meta) return html`<div className="sv-app"></div>`;

    // Email-gated shares hard-block the prototype behind the modal.
    const gateBlocked = meta.emailGate && !(identity && identity.name && identity.email);

    // Clamp composer near its pin inside the stage.
    const composerStyle = draft ? {
      left: Math.min(Math.max(draft.x - 10, 8), Math.max(8, window.innerWidth - (sidebarOpen ? 320 : 0) - 300)) + "px",
      top: Math.min(draft.y + 16, window.innerHeight - 220) + "px",
    } : null;

    return html`
      <div className="sv-app">
        <div className="sv-topbar">
          <span className="sv-brand">
            <svg width="30" height="16" viewBox="0 0 76 40" fill="#1c1c1e" aria-hidden="true">
              <path d="M14 2L26 14L14 26L2 14Z"/><path d="M38 2L50 14L38 26L26 14Z"/>
              <path d="M62 2L74 14L62 26L50 14Z"/><path d="M26 14L38 26L26 38L14 26Z"/>
              <path d="M50 14L62 26L50 38L38 26Z"/>
            </svg>
            ${meta.label}
            <span className="sv-brand-sub">· shared for review</span>
          </span>
          <span className="sv-topbar-spacer"></span>
          <span className="sv-page-chip" title=${page}>${page}</span>
          <button
            className=${"sv-btn" + (commentMode ? " is-active" : "")}
            title=${commentMode ? "Exit comment mode (Esc)" : "Comment on an element — click anything in the prototype"}
            onClick=${() => {
              if (!commentMode && !requireIdentity("Add a name before commenting.")) return;
              setDraft(null); setCommentMode(!commentMode);
            }}
          ><${CommentIcon}/> ${commentMode ? "Click an element…" : "Comment"}</button>
          <button
            className=${"sv-btn" + (sidebarOpen ? " is-active" : "")}
            onClick=${() => setSidebarOpen(!sidebarOpen)}
            title="Toggle the comments sidebar"
          >Comments <span className="sv-btn-count">${counts.open}</span></button>
        </div>
        <div className="sv-main">
          <div className=${"sv-stage" + (commentMode ? " is-commenting" : "")}>
            ${!gateBlocked && html`<iframe
              ref=${iframeRef}
              src=${BASE + meta.entry}
              title="Shared prototype"
              onLoad=${onFrameLoad}
            ></iframe>`}
            ${commentMode && html`<div className="sv-hint">Click any element to pin a comment — Esc to cancel</div>`}
            ${pins.map((p) => html`
              <button
                key=${p.id}
                className=${"sv-pin" + (p.draft ? " sv-pin-draft" : "") + (p.done ? " is-done" : "")
                           + (p.id === activeId ? " is-active" : "")}
                style=${{ left: p.x + "px", top: p.y + "px" }}
                title=${p.draft ? "New comment" : "Open comment"}
                onClick=${() => {
                  if (p.draft) return;
                  const c = comments.find((x) => x.id === p.id);
                  if (c) { setSidebarOpen(true); focusComment(c); }
                }}
              >${p.num}</button>
            `)}
            ${draft && html`
              <div className="sv-composer" style=${composerStyle}>
                <div className="sv-composer-target" title=${draft.anchor.selector}>
                  ${draft.anchor.tag}${draft.anchor.selector ? " · " + draft.anchor.selector : ""}
                </div>
                <textarea
                  autoFocus
                  placeholder="What should change here?"
                  value=${draftText}
                  onInput=${(e) => setDraftText(e.target.value)}
                  onKeyDown=${(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submitDraft();
                    if (e.key === "Escape") { setDraft(null); }
                  }}
                ></textarea>
                <div className="sv-composer-row">
                  <button className="sv-btn" onClick=${() => setDraft(null)}>Cancel</button>
                  <button className="sv-btn sv-btn-primary" disabled=${!draftText.trim() || posting}
                    onClick=${submitDraft}>${posting ? "Posting…" : "Comment"}</button>
                </div>
              </div>
            `}
            ${error && html`<div className="sv-banner">${error}</div>`}
          </div>
          ${sidebarOpen && html`
            <div className="sv-sidebar">
              <div className="sv-sidebar-head">
                <span className="sv-sidebar-title">Comments</span>
                <div className="sv-filters">
                  ${["open", "done", "archived", "all"].map((f) => html`
                    <button key=${f}
                      className=${"sv-filter" + (filter === f ? " is-active" : "")}
                      onClick=${() => setFilter(f)}
                    >${f === "open" ? `Open ${counts.open}` : f === "done" ? `Done ${counts.done}`
                       : f === "archived" ? "Archived" : "All"}</button>
                  `)}
                </div>
              </div>
              <div className="sv-comments">
                ${visibleComments.length === 0 && html`
                  <div className="sv-empty">
                    <b>${filter === "open" ? "No open comments" : "Nothing here"}</b>
                    Use the Comment button above, then click any element in the prototype to leave feedback.
                  </div>
                `}
                ${visibleComments.map((c) => html`
                  <${CommentCard}
                    key=${c.id}
                    c=${c}
                    num=${numbered.numOf.get(c.id) || "•"}
                    active=${activeId === c.id}
                    onFocus=${focusComment}
                    onReply=${onReply}
                    onStatus=${onStatus}
                    onDelete=${onDelete}
                    onEdit=${onEdit}
                  />
                `)}
              </div>
            </div>
          `}
        </div>
        ${needIdentity && html`
          <${IdentityModal}
            emailGate=${meta.emailGate}
            initial=${identity}
            reason=${identityReason}
            onCancel=${meta.emailGate ? null : () => setNeedIdentity(false)}
            onDone=${(id) => { setIdentity(id); saveIdentity(id); setNeedIdentity(false); }}
          />
        `}
      </div>
    `;
  }

  function Root() {
    return html`<${App}/>`;
  }
  ReactDOM.createRoot(document.getElementById("root")).render(html`<${Root}/>`);
})();
