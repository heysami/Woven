/* Woven share viewer - visitor-facing review surface for ONE shared
   prototype. Served by the share gate at /s/<token>/ (see editor/shares.py).

   Architecture notes:
   • The prototype lives in a SAME-ORIGIN iframe (gate serves both this page
     and the prototype files), so we can reach contentDocument directly:
     element picking, pin anchoring, scroll/highlight all work without any
     script injected into the prototype's own bundle.
   • Comments anchor to elements as { selector, tag, text } - selector is
     the primary locator; tag+text are a fuzzy fallback for when the
     prototype's DOM drifts after agent edits. Pins are {x,y} fractions of
     the element's box so they survive responsive reflow.
   • No SSE for visitors - plain polling (8s) keeps the gate surface tiny.
   • Identity is localStorage-only ("woven-share-identity"); the gate
     enforces name-required (and email-required when the share's emailGate
     is on) at POST time - the modal here is UX, the gate is policy. */

/* global React, ReactDOM, htm */
(() => {
  const html = htm.bind(React.createElement);
  const { useState, useEffect, useRef, useMemo, useCallback } = React;

  // Woven line-icon - mirrors editor's Icon.Comment (16-box, 1.5pt round
  // stroke). `size` defaults to the editor's 14px glyph footprint.
  const CommentIcon = ({ size = 14 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <path d="M3 4a1 1 0 011-1h8a1 1 0 011 1v6a1 1 0 01-1 1H7l-3 3v-3a1 1 0 01-1-1z"/>
    </svg>`;

  // Home glyph for the "Reset" button - sends the prototype iframe back to its
  // first page (reviewers wander deep and don't want to click all the way back).
  const HomeIcon = ({ size = 14 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <path d="M2.5 7L8 2.5L13.5 7"/><path d="M4 6.5V13h8V6.5"/><path d="M6.5 13V9.5h3V13"/>
    </svg>`;

  // Pencil glyph - toggles the freehand annotation layer over the screenshot.
  const PencilIcon = ({ size = 13 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <path d="M11.5 2.5l2 2L6 12l-2.7.7L4 10z"/><path d="M10 4l2 2"/>
    </svg>`;

  // Panel glyph - the "Comments" sidebar toggle (right-hand panel outline).
  const PanelIcon = ({ size = 14 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M10 3v10"/>
    </svg>`;

  // Image glyph - the "attach images" affordance on the composer.
  const ImageIcon = ({ size = 13 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <rect x="2" y="3" width="12" height="10" rx="1.5"/><circle cx="5.5" cy="6.5" r="1"/>
      <path d="M3 11l3-3 2.5 2.5L11 7l2 2"/>
    </svg>`;

  // Flow glyph - the "Flows" screen-map toggle (two screens + a hop arrow).
  const FlowIcon = ({ size = 14 }) => html`
    <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none"
      stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      stroke-linejoin="round" aria-hidden="true" style=${{ display: "block" }}>
      <rect x="1.5" y="2" width="6" height="5" rx="1"/>
      <rect x="8.5" y="9" width="6" height="5" rx="1"/>
      <path d="M7.5 4.5h3.5a1.5 1.5 0 011.5 1.5v3"/>
      <path d="M10.8 7.3l1.7 1.7 1.7-1.7"/>
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
      // id short-circuit - unique enough, stop climbing.
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

  // Capture what the reviewer is currently looking at in the prototype iframe
  // and return it as a JPEG data URL (or null). The iframe is same-origin, so
  // html2canvas can render its document directly. We crop to the visible
  // viewport (what they actually see); no annotation is baked in here - the
  // freehand-stroke baking below handles markup. Best-effort: any failure
  // returns null and the comment posts without a screenshot.
  const captureShot = async (frame, anchor) => {
    try {
      const win = frame && frame.contentWindow;
      const doc = frame && frame.contentDocument;
      if (!win || !doc || typeof window.html2canvas !== "function") return null;
      const scale = Math.min(window.devicePixelRatio || 1, 2);
      const vw = Math.max(1, win.innerWidth || doc.documentElement.clientWidth || 1);
      const vh = Math.max(1, win.innerHeight || doc.documentElement.clientHeight || 1);
      const canvas = await window.html2canvas(doc.documentElement, {
        backgroundColor: "#ffffff", useCORS: true, allowTaint: false, logging: false,
        scale,
        x: win.scrollX || 0, y: win.scrollY || 0,
        width: vw, height: vh, windowWidth: vw, windowHeight: vh,
      });
      // Clean capture of the visible viewport - no annotation baked in.
      return canvas.toDataURL("image/jpeg", 0.82);
    } catch { return null; }
  };

  // Bake freehand annotation strokes INTO the screenshot raster so the reviewer's
  // drawing and the UI ship as one image. Strokes are in stage/iframe-viewport
  // CSS px (top-left origin); the screenshot is the same viewport at html2canvas
  // `scale`, so the px→shot factor is shotWidth / viewportWidth. No strokes →
  // the clean shot passes through unchanged. Best-effort: any failure returns
  // the original shot so the comment still carries an image.
  const compositeAnnotation = async (shotDataUrl, strokes, frame) => {
    if (!shotDataUrl || !strokes || !strokes.length) return shotDataUrl;
    try {
      const win = frame && frame.contentWindow;
      const vw = Math.max(1, (win && win.innerWidth) || 1);
      const img = new Image();
      img.src = shotDataUrl;
      await new Promise((res, rej) => { img.onload = res; img.onerror = rej; });
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth || img.width;
      canvas.height = img.naturalHeight || img.height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      const k = canvas.width / vw;            // stage CSS px → screenshot px
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = Math.max(2, 3 * k);
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (const s of strokes) {
        const pts = (s && s.points) || [];
        if (pts.length < 2) continue;
        ctx.beginPath();
        ctx.moveTo(pts[0].x * k, pts[0].y * k);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x * k, pts[i].y * k);
        ctx.stroke();
      }
      return canvas.toDataURL("image/jpeg", 0.82);
    } catch { return shotDataUrl; }
  };

  // ── Freehand annotation overlay ───────────────────────────────────────
  // Sits over the prototype stage while a comment draft is open and "Draw" is
  // armed. Captures strokes in stage-local CSS px (origin = stage top-left,
  // which equals the iframe viewport, so the points map 1:1 into the
  // screenshot). The live stroke is local state for a smooth trail; completed
  // strokes are lifted to the parent via onAddStroke for compositing at submit.
  function DrawOverlay({ strokes, onAddStroke }) {
    const ref = useRef(null);
    const rectRef = useRef(null);
    const [cur, setCur] = useState(null);
    const ptOf = (ev) => {
      const r = rectRef.current;
      const src = (ev.touches && ev.touches[0]) ? ev.touches[0] : ev;
      return { x: Math.round(src.clientX - r.left), y: Math.round(src.clientY - r.top) };
    };
    const start = (ev) => {
      ev.preventDefault();
      // Cache the rect at stroke start - never per pointermove (layout thrash).
      rectRef.current = ref.current.getBoundingClientRect();
      setCur([ptOf(ev)]);
    };
    const move = (ev) => {
      if (!cur) return;
      ev.preventDefault();
      setCur((p) => (p ? [...p, ptOf(ev)] : p));
    };
    const end = () => {
      setCur((p) => { if (p && p.length > 1) onAddStroke({ points: p }); return null; });
    };
    const toPoints = (pts) => pts.map((p) => p.x + "," + p.y).join(" ");
    const line = (pts, key) => html`<polyline key=${key} points=${toPoints(pts)}
      fill="none" stroke="#ef4444" stroke-width="3"
      stroke-linecap="round" stroke-linejoin="round"/>`;
    return html`
      <svg ref=${ref} className="sv-draw-layer"
        onMouseDown=${start} onMouseMove=${move} onMouseUp=${end} onMouseLeave=${end}
        onTouchStart=${start} onTouchMove=${move} onTouchEnd=${end}>
        ${strokes.map((s, i) => line(s.points, i))}
        ${cur && cur.length > 1 && line(cur, "cur")}
      </svg>`;
  }

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
  // source/<slug>/ ("index.html", "screens/detail.html", …) + hash. Marker
  // search rather than exact-prefix so branch-scoped paths (/b/<branch>/p/…)
  // yield the SAME page id - comments anchor to the page, not the branch.
  const pageOfWin = (win, prototype) => {
    try {
      const marker = "/p/source/" + prototype + "/";
      let p = win.location.pathname;
      const i = p.indexOf(marker);
      p = i >= 0 ? p.slice(i + marker.length) : p.split("/").pop();
      if (!p) p = "index.html";
      return p + (win.location.hash || "");
    } catch {
      return "index.html";
    }
  };
  const pathPart = (page) => (page || "index.html").split("#")[0] || "index.html";

  // ── Screen flows (read-only frames + arrows map) ──────────────────────
  // flowdata.js is the editor's own data files served verbatim by the gate
  // (window.EDITOR_DATA + window.EDITOR_LAYOUT assignments). Evaluate them
  // against a bare stand-in window - same contract editor/index.html uses.
  const parseFlowData = (srcText) => {
    try {
      const win = {};
      new Function("window", "document", srcText)(win, { write: () => {} });
      const D = win.EDITOR_DATA;
      if (!D || !Array.isArray(D.frames) || D.frames.length === 0) return null;
      return { D, L: win.EDITOR_LAYOUT || null };
    } catch {
      return null;
    }
  };

  // ── Edge routing + label placement ─────────────────────────────────────
  // Verbatim ports of the editor's canvas helpers (app.js routeEdge /
  // routeEdges / cubicPt / labelBBox / rectsOverlap / placeLabel) so the
  // shared flow map draws the SAME arrows and chip placement the owner sees
  // in Woven's Architecture canvas. Pure functions - keep in sync by copy.
  const routeEdge = (A, B, opts = {}) => {
    const ax = A.x + A.w / 2, ay = A.y + A.h / 2;
    const bx = B.x + B.w / 2, by = B.y + B.h / 2;
    const sideOf = (rect, towardX, towardY) => {
      const cx = rect.x + rect.w / 2, cy = rect.y + rect.h / 2;
      const ddx = towardX - cx, ddy = towardY - cy;
      if (Math.abs(ddy) * rect.w > Math.abs(ddx) * rect.h) return ddy > 0 ? "bottom" : "top";
      return ddx > 0 ? "right" : "left";
    };
    const ptOf = (rect, side, t = 0.5) => {
      switch (side) {
        case "right":  return { x: rect.x + rect.w,     y: rect.y + rect.h * t, nx:  1, ny:  0 };
        case "left":   return { x: rect.x,              y: rect.y + rect.h * t, nx: -1, ny:  0 };
        case "bottom": return { x: rect.x + rect.w * t, y: rect.y + rect.h,     nx:  0, ny:  1 };
        default:       return { x: rect.x + rect.w * t, y: rect.y,              nx:  0, ny: -1 };
      }
    };
    const sideA = opts.sideA != null ? opts.sideA : sideOf(A, bx, by);
    const sideB = opts.sideB != null ? opts.sideB : sideOf(B, ax, ay);
    const A0 = ptOf(A, sideA, opts.exitT != null ? opts.exitT : 0.5);
    const B0 = ptOf(B, sideB, opts.entryT != null ? opts.entryT : 0.5);
    const tMin = opts.tensionMin != null ? opts.tensionMin : 40;
    const tMax = opts.tensionMax != null ? opts.tensionMax : 180;
    const tension = Math.max(tMin, Math.min(tMax, Math.hypot(bx - ax, by - ay) * 0.4));
    return {
      fx: A0.x, fy: A0.y, tx: B0.x, ty: B0.y,
      c1x: A0.x + A0.nx * tension, c1y: A0.y + A0.ny * tension,
      c2x: B0.x + B0.nx * tension, c2y: B0.y + B0.ny * tension,
      sideA, sideB,
    };
  };
  const routeEdges = (arrows, getRect, opts = {}) => {
    const sides = arrows.map((a) => {
      const A = getRect(a.from), B = getRect(a.to);
      if (!A || !B) return null;
      const probe = routeEdge(A, B, opts);
      return { sideA: probe.sideA, sideB: probe.sideB };
    });
    const counts = new Map();
    const inc = (k) => counts.set(k, (counts.get(k) || 0) + 1);
    sides.forEach((r, i) => {
      if (!r) return;
      inc(arrows[i].from + ":out:" + r.sideA);
      inc(arrows[i].to   + ":in:"  + r.sideB);
    });
    const used = new Map();
    return arrows.map((a, i) => {
      const r = sides[i]; if (!r) return null;
      const A = getRect(a.from), B = getRect(a.to);
      const outKey = a.from + ":out:" + r.sideA;
      const inKey  = a.to   + ":in:"  + r.sideB;
      const outTotal = counts.get(outKey), inTotal = counts.get(inKey);
      const outIdx = used.get(outKey) || 0, inIdx = used.get(inKey) || 0;
      used.set(outKey, outIdx + 1);
      used.set(inKey,  inIdx  + 1);
      const exitT  = (outIdx + 1) / (outTotal + 1);
      const entryT = (inIdx  + 1) / (inTotal  + 1);
      return routeEdge(A, B, { ...opts, sideA: r.sideA, sideB: r.sideB, exitT, entryT });
    });
  };
  const cubicPt = (e, t) => {
    const u = 1 - t;
    return {
      x: u*u*u*e.fx + 3*u*u*t*e.c1x + 3*u*t*t*e.c2x + t*t*t*e.tx,
      y: u*u*u*e.fy + 3*u*u*t*e.c1y + 3*u*t*t*e.c2y + t*t*t*e.ty,
    };
  };
  const labelBBox = (pt, text, opts = {}) => {
    const maxW = opts.maxWidth != null ? opts.maxWidth : 160;
    const charW = opts.charW != null ? opts.charW : 7.2;
    const lineH = opts.lineH != null ? opts.lineH : 16;
    const padX = opts.padX != null ? opts.padX : 18;
    const padY = opts.padY != null ? opts.padY : 10;
    const minW = opts.minW != null ? opts.minW : 48;
    const t = String(text || "");
    const naturalW = t.length * charW + padX;
    const w = Math.min(maxW, Math.max(minW, naturalW));
    const lines = naturalW > maxW ? Math.ceil(naturalW / (maxW - padX)) : 1;
    const h = lines * lineH + padY;
    return { x: pt.x - w/2, y: pt.y - h/2, w, h, cx: pt.x, cy: pt.y };
  };
  const rectsOverlap = (a, b, pad = 4) =>
    !(a.x + a.w + pad < b.x || b.x + b.w + pad < a.x ||
      a.y + a.h + pad < b.y || b.y + b.h + pad < a.y);
  const placeLabel = (edge, text, obstacles, opts = {}) => {
    const tries = opts.tries || [0.5, 0.42, 0.58, 0.34, 0.66, 0.28, 0.72];
    const perpAmts = opts.perpAmts || [0, -16, 16, -28, 28];
    for (const perp of perpAmts) {
      for (const t of tries) {
        const pt = cubicPt(edge, t);
        const dt = 0.01;
        const p2 = cubicPt(edge, Math.min(1, t + dt));
        const dx = p2.x - pt.x, dy = p2.y - pt.y;
        const len = Math.hypot(dx, dy) || 1;
        const nx = -dy / len, ny = dx / len;
        const offsetPt = { x: pt.x + nx * perp, y: pt.y + ny * perp };
        const bbox = labelBBox(offsetPt, text, opts);
        if (!obstacles.some((o) => rectsOverlap(bbox, o))) {
          return { pt: offsetPt, bbox, t, perp };
        }
      }
    }
    const pt = cubicPt(edge, 0.5);
    return { pt, bbox: labelBBox(pt, text, opts), t: 0.5, perp: 0 };
  };

  // Port of the editor's runSetupScriptWithRetry (app.js): evals a frame's
  // setupScript inside its same-origin embed, re-firing across DOM mutations
  // for ~3s so single-page prototypes land on the right useState branch even
  // when React commits after iframe load. Without this every substep frame
  // renders its page's DEFAULT state - not the state the editor shows.
  // (The gate injects the __poke/__pokeBy helpers the scripts call.)
  const runSetupScriptWithRetry = (iframeEl, script) => {
    if (!iframeEl || !script) return;
    const win = iframeEl.contentWindow;
    const doc = iframeEl.contentDocument;
    if (!win || !doc) return;
    try { win.eval(script); } catch (_) { /* cross-origin or syntax */ }
    const target = doc.body || doc.documentElement;
    if (!target || typeof MutationObserver !== "function") return;
    let fires = 0;
    const MAX_FIRES = 8;
    const DEADLINE_MS = 3000;
    const deadline = Date.now() + DEADLINE_MS;
    let observer;
    let timer;
    const fire = () => {
      if (Date.now() > deadline || fires >= MAX_FIRES) {
        if (observer) observer.disconnect();
        if (timer) clearTimeout(timer);
        return;
      }
      fires++;
      try { win.eval(script); } catch (_) { /* cross-origin or syntax */ }
    };
    try {
      observer = new MutationObserver(() => fire());
      observer.observe(target, { childList: true, subtree: true });
    } catch (_) { return; }
    setTimeout(fire, 250);
    setTimeout(fire, 1000);
    timer = setTimeout(() => { if (observer) observer.disconnect(); }, DEADLINE_MS);
  };

  // The flow map itself: every frame as a live page embed on the editor's
  // col/row grid, arrows as SVG curves, drag to pan, Cmd/Ctrl-scroll or the
  // corner buttons to zoom, click a screen to open it in the prototype view.
  function FlowMap({ flow, base, prototype, onOpenFrame }) {
    const stageRef = useRef(null);
    const [view, setView] = useState(null);   // {x, y, k}; null until first fit
    const dragRef = useRef(null);
    const suppressClickRef = useRef(false);

    // World layout - mirrors the editor's grid math (CANVAS_MARGIN 120,
    // pitch = defaultFrame + canvasGap, layout sidecar positions win over
    // the frame's own col/row, unplaced frames take the first free cell).
    const world = useMemo(() => {
      const D = flow.D || {};
      const L = flow.L || {};
      const meta = D.meta || {};
      const lmeta = L.meta || {};
      const df = lmeta.defaultFrame || meta.defaultFrame || {};
      const cellW = df.w || 1440, cellH = df.h || 900;
      const gap = lmeta.canvasGap != null ? lmeta.canvasGap
        : (meta.canvasGap != null ? meta.canvasGap : 120);
      const MARGIN = 120;
      const pitchX = cellW + gap, pitchY = cellH + gap;
      const pos = L.positions || {};
      const frames = (D.frames || []).filter((f) => f && f.id && f.entry);
      const occupied = new Set();
      const cells = new Map();
      for (const f of frames) {
        const p = pos[f.id];
        const col = p && p.col != null ? p.col : f.col;
        const row = p && p.row != null ? p.row : f.row;
        if (col != null && row != null) {
          cells.set(f.id, { col, row });
          occupied.add(col + "," + row);
        }
      }
      for (const f of frames) {
        if (cells.has(f.id)) continue;
        let cell = null;
        for (let r = 0; r < 200 && !cell; r++) {
          for (let c = 0; c < 40; c++) {
            if (!occupied.has(c + "," + r)) { cell = { col: c, row: r }; break; }
          }
        }
        cell = cell || { col: 0, row: 0 };
        cells.set(f.id, cell);
        occupied.add(cell.col + "," + cell.row);
      }
      const placed = frames.map((f) => {
        const cell = cells.get(f.id);
        return {
          ...f,
          x: MARGIN + cell.col * pitchX,
          y: MARGIN + cell.row * pitchY,
          w: f.w || cellW,
          h: f.h || cellH,
        };
      });
      // Arrow routing + chip placement - the editor's exact pipeline: rects
      // include the 32px label band, anchors spread per (frame, side), chips
      // collision-avoid against frames and each other (see ArrowLayer).
      const LABEL_BAND = 32;
      const byId = new Map(placed.map((f) => [f.id, f]));
      const rectFor = (f) => ({ x: f.x, y: f.y, w: f.w, h: f.h + LABEL_BAND });
      const getRect = (id) => { const f = byId.get(id); return f ? rectFor(f) : null; };
      const rawArrows = (D.arrows || [])
        .filter((a) => a && a.from !== a.to && byId.has(a.from) && byId.has(a.to));
      const routes = routeEdges(rawArrows, getRect, { tensionMin: 60, tensionMax: 220 });
      const sourceCount = new Map();
      rawArrows.forEach((a) => sourceCount.set(a.from, (sourceCount.get(a.from) || 0) + 1));
      const sourceIdx = new Map();
      const obstacles = placed.map(rectFor);
      const arrows = rawArrows.map((a, i) => {
        const r = routes[i];
        if (!r) return null;
        let chip = null;
        if (a.action) {
          const N = sourceCount.get(a.from) || 1;
          const k = sourceIdx.get(a.from) || 0;
          sourceIdx.set(a.from, k + 1);
          const center = N === 1 ? 0.5 : 0.3 + (k / Math.max(1, N - 1)) * 0.4;
          const tries = [center, center - 0.08, center + 0.08, center - 0.16, center + 0.16, 0.5, 0.35, 0.65]
            .map((t) => Math.max(0.15, Math.min(0.85, t)));
          chip = placeLabel(r, a.action, obstacles, { tries });
          obstacles.push(chip.bbox);
        }
        return {
          ...a,
          key: a.id || "arrow-" + i,
          d: `M ${r.fx} ${r.fy} C ${r.c1x} ${r.c1y}, ${r.c2x} ${r.c2y}, ${r.tx} ${r.ty}`,
          ends: r,
          chip,
        };
      }).filter(Boolean);
      const w = Math.max(0, ...placed.map((f) => f.x + f.w)) + MARGIN;
      const h = Math.max(0, ...placed.map((f) => f.y + f.h + LABEL_BAND)) + MARGIN;
      return { frames: placed, arrows, w, h, labelBand: LABEL_BAND };
    }, [flow]);

    const fit = useCallback(() => {
      const el = stageRef.current;
      if (!el || !world.w || !world.h) return;
      const sw = el.clientWidth, sh = el.clientHeight;
      const k = Math.max(0.02, Math.min(1, (sw - 48) / world.w, (sh - 48) / world.h));
      setView({ k, x: (sw - world.w * k) / 2, y: (sh - world.h * k) / 2 });
    }, [world]);
    useEffect(() => { fit(); }, [fit]);

    const zoomAt = (factor, cx, cy) => setView((v) => {
      if (!v) return v;
      const k = Math.max(0.02, Math.min(2, v.k * factor));
      const f = k / v.k;
      return { k, x: cx - (cx - v.x) * f, y: cy - (cy - v.y) * f };
    });
    const zoomCenter = (factor) => {
      const el = stageRef.current;
      if (el) zoomAt(factor, el.clientWidth / 2, el.clientHeight / 2);
    };

    // Wheel: pan by default, zoom with Cmd/Ctrl (covers trackpad pinch, which
    // arrives as ctrlKey wheel). Attached natively so preventDefault sticks.
    useEffect(() => {
      const el = stageRef.current;
      if (!el) return;
      const onWheel = (e) => {
        e.preventDefault();
        if (e.ctrlKey || e.metaKey) {
          const r = el.getBoundingClientRect();
          zoomAt(Math.exp(-e.deltaY * 0.01), e.clientX - r.left, e.clientY - r.top);
        } else {
          setView((v) => v ? { ...v, x: v.x - e.deltaX, y: v.y - e.deltaY } : v);
        }
      };
      el.addEventListener("wheel", onWheel, { passive: false });
      return () => el.removeEventListener("wheel", onWheel);
    }, []);

    const onPointerDown = (e) => {
      if (e.button !== 0 || !view) return;
      // No capture yet: grabbing the pointer here would eat the click on
      // whatever button is under it (zoom tools, frame-open). Capture only
      // once the gesture provably becomes a drag (onPointerMove).
      dragRef.current = {
        sx: e.clientX, sy: e.clientY, vx: view.x, vy: view.y,
        moved: false, pointerId: e.pointerId, el: e.currentTarget,
      };
    };
    const onPointerMove = (e) => {
      const d = dragRef.current;
      if (!d) return;
      const dx = e.clientX - d.sx, dy = e.clientY - d.sy;
      if (!d.moved && Math.abs(dx) + Math.abs(dy) > 4) {
        d.moved = true;
        try { d.el.setPointerCapture(d.pointerId); } catch {}
      }
      if (d.moved) setView((v) => v ? { ...v, x: d.vx + dx, y: d.vy + dy } : v);
    };
    const onPointerUp = () => {
      const d = dragRef.current;
      dragRef.current = null;
      if (d && d.moved) {
        // A pan ends with a click on whatever's under the pointer - eat it.
        suppressClickRef.current = true;
        setTimeout(() => { suppressClickRef.current = false; }, 0);
      }
    };

    return html`
      <div className="sv-flow" ref=${stageRef}
        onPointerDown=${onPointerDown}
        onPointerMove=${onPointerMove}
        onPointerUp=${onPointerUp}
        onPointerCancel=${onPointerUp}>
        ${view && html`
          <div className="sv-flow-world"
            style=${{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})` }}>
            <svg className="sv-flow-arrows" width=${world.w} height=${world.h}
              viewBox=${`0 0 ${world.w} ${world.h}`}>
              <defs>
                <marker id="sv-arrowhead" viewBox="0 0 12 12" refX="10" refY="6"
                  markerWidth="8" markerHeight="8" orient="auto">
                  <path d="M0 0 L10 6 L0 12 L3 6 z" fill="oklch(54% 0.16 252)"/>
                </marker>
              </defs>
              ${world.arrows.map((a, i) => html`
                <g key=${a.key}>
                  <linearGradient id=${"sv-grad-" + i} gradientUnits="userSpaceOnUse"
                    x1=${a.ends.fx} y1=${a.ends.fy} x2=${a.ends.tx} y2=${a.ends.ty}>
                    <stop offset="0%"   stopColor="oklch(54% 0.16 252)" stopOpacity="0.1"/>
                    <stop offset="100%" stopColor="oklch(54% 0.16 252)" stopOpacity="1"/>
                  </linearGradient>
                  <path className="sv-edge-flow" d=${a.d} fill="none"
                    stroke=${`url(#sv-grad-${i})`} stroke-width="2"
                    marker-end="url(#sv-arrowhead)"/>
                </g>
              `)}
              ${world.arrows.filter((a) => a.chip).map((a) => html`
                <foreignObject key=${"chip-" + a.key}
                  x=${a.chip.bbox.x} y=${a.chip.bbox.y}
                  width=${a.chip.bbox.w} height=${a.chip.bbox.h}
                  style=${{ overflow: "visible", pointerEvents: "none" }}>
                  <div xmlns="http://www.w3.org/1999/xhtml" className="sv-edge-chip"
                    title=${a.action}>${a.action}</div>
                </foreignObject>
              `)}
            </svg>
            ${world.frames.map((f) => html`
              <div key=${f.id} className="sv-flow-frame"
                style=${{ left: f.x + "px", top: f.y + "px", width: f.w + "px",
                          height: (f.h + world.labelBand) + "px" }}>
                <div className="sv-flow-frame-head">
                  <span className="sv-flow-frame-kind" data-kind=${f.kind || "page"}>${f.kind || "page"}</span>
                  <span className="sv-flow-frame-name">${f.label || f.id}</span>
                  <span className="sv-flow-frame-meta">${f.hash || "-"}</span>
                </div>
                <div className="sv-flow-frame-shot">
                  <iframe src=${base + "p/source/" + prototype + "/" + f.entry + (f.hash || "")}
                    loading="lazy" scrolling="no" tabIndex=${-1} title=${f.label || f.id}
                    onLoad=${(e) => { if (f.setupScript) runSetupScriptWithRetry(e.currentTarget, f.setupScript); }}></iframe>
                  <button type="button" className="sv-flow-frame-open"
                    title=${"Open " + (f.label || f.entry) + " in the prototype"}
                    onClick=${() => { if (!suppressClickRef.current) onOpenFrame(f); }}></button>
                </div>
              </div>
            `)}
          </div>
        `}
        <div className="sv-flow-tools">
          <button className="sv-btn" title="Zoom out" onClick=${() => zoomCenter(1 / 1.25)}>−</button>
          <span className="sv-flow-zoom">${view ? Math.round(view.k * 100) + "%" : ""}</span>
          <button className="sv-btn" title="Zoom in" onClick=${() => zoomCenter(1.25)}>+</button>
          <button className="sv-btn" title="Fit every screen in view" onClick=${fit}>Fit</button>
        </div>
        <div className="sv-flow-hint">Drag to pan, Cmd/Ctrl-scroll to zoom, click a screen to open it</div>
      </div>
    `;
  }

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
    // Two-step inline delete confirm (no native confirm() dialogs). First
    // click arms the button; it disarms itself after 4s if not confirmed.
    const [armDelete, setArmDelete] = useState(false);
    useEffect(() => {
      if (!armDelete) return;
      const t = setTimeout(() => setArmDelete(false), 4000);
      return () => clearTimeout(t);
    }, [armDelete]);
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
        ${c.shot && html`
          <a className="sv-comment-shot" href=${api("comments/" + c.id + "/shot")}
            target="_blank" rel="noopener" title="Open the captured page screenshot"
            onClick=${(e) => e.stopPropagation()}>
            <img src=${api("comments/" + c.id + "/shot")} alt="Page at comment time" loading="lazy"/>
          </a>
        `}
        ${(c.attachments || []).length > 0 && html`
          <div className="sv-comment-attachments">
            ${c.attachments.map((a) => html`
              <a className="sv-attach-item" key=${a.id}
                href=${api("comments/" + c.id + "/attach/" + a.id)}
                target="_blank" rel="noopener" title=${a.name || "Attached image"}
                onClick=${(e) => e.stopPropagation()}>
                <img src=${api("comments/" + c.id + "/attach/" + a.id)}
                  alt=${a.name || "Attached image"} loading="lazy"/>
              </a>
            `)}
          </div>
        `}
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
          <button className="sv-mini-btn danger"
            onClick=${() => { if (armDelete) { setArmDelete(false); onDelete(c); } else { setArmDelete(true); } }}
          >${armDelete ? "Really delete?" : "Delete"}</button>
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
    // Branch being reviewed: "" = the share's checked-out branch (served from
    // the working tree). Anything else routes through /b/<branch>/, which the
    // gate serves out of that branch's COMMITTED tree - picking a branch here
    // never touches the owner's checkout.
    const [viewBranch, setViewBranch] = useState("");
    // Sibling shares from the contributor registry: the project's OTHER
    // published links (more prototypes, other installs' branches). Boot meta
    // carries the upload-time copy for hosted shares; /api/links refreshes it
    // through the worker whenever the owner's daemon answers.
    const [links, setLinks] = useState(null);
    const [error, setError] = useState(null);
    const [posting, setPosting] = useState(false);
    const [drawing, setDrawing] = useState(false);    // annotation layer armed
    const [strokes, setStrokes] = useState([]);       // committed annotation strokes
    const [attachments, setAttachments] = useState([]); // [{name, dataUrl}] pending upload
    const [flowData, setFlowData] = useState(null);   // parsed screen-flow model (null = none)
    const [flowsOpen, setFlowsOpen] = useState(false); // Flows map replaces the prototype stage

    // URL prefix that pins prototype loads to the picked branch ("" when
    // reviewing the checked-out branch). Slashes in branch names stay literal
    // path segments - the gate's /b/ route matches across them.
    const branchPathPfx = (b) =>
      (meta && b && b !== meta.branch)
        ? "b/" + encodeURIComponent(b).replace(/%2F/gi, "/") + "/" : "";
    const branchPfx = branchPathPfx(viewBranch);

    const iframeRef = useRef(null);
    const commentModeRef = useRef(false); commentModeRef.current = commentMode;
    const draftRef = useRef(null); draftRef.current = draft;
    const hoverElRef = useRef(null);
    const cleanupArmRef = useRef(null);

    const showError = (msg) => { setError(msg); setTimeout(() => setError(null), 5000); };
    const [notice, setNotice] = useState(null);
    const showNotice = (msg) => { setNotice(msg); setTimeout(() => setNotice(null), 7000); };
    // Comments accepted while the owner is OFFLINE (hosted shares queue them
    // at the broker). Kept locally so they stay visible in this session even
    // though the server list can't include them yet.
    const queuedRef = useRef([]);

    // Closing a draft (cancel / Esc / submit / reset) drops any annotation
    // strokes + pending attachments so the next comment starts clean.
    useEffect(() => {
      if (!draft) { setStrokes([]); setAttachments([]); setDrawing(false); }
    }, [draft]);

    // Read picked image files into data URLs held on the draft until submit.
    const MAX_ATTACH = 8, MAX_ATTACH_BYTES = 12 * 1024 * 1024;
    const onPickFiles = (e) => {
      const files = Array.from((e.target && e.target.files) || []);
      if (e.target) e.target.value = "";   // allow re-picking the same file
      for (const f of files) {
        if (!/^image\//.test(f.type || "")) continue;
        if (f.size > MAX_ATTACH_BYTES) { showError("Image too large (max 12MB): " + f.name); continue; }
        const reader = new FileReader();
        reader.onload = () => setAttachments((list) =>
          list.length >= MAX_ATTACH ? list : [...list, { name: f.name, dataUrl: String(reader.result) }]);
        reader.readAsDataURL(f);
      }
    };

    // Boot: meta + comments. Meta failure = revoked/unknown share.
    useEffect(() => {
      fetch(api("meta")).then((r) => {
        if (!r.ok) throw new Error("share unavailable");
        return r.json();
      }).then(setMeta).catch(() => setMetaErr("This share link is no longer available."));
    }, []);
    useEffect(() => {
      if (!meta) return;
      fetch(api("links")).then((r) => (r.ok ? r.json() : null)).then((j) => {
        if (j && Array.isArray(j.links)) setLinks(j.links);
      }).catch(() => {});   // owner offline / pre-links gate - meta.links stands
    }, [meta]);

    // Screen-flow data: the gate serves the editor's frames/arrows model at
    // /flowdata.js when the project has one. 404 = no map; hide the button.
    useEffect(() => {
      if (!meta) return;
      fetch(BASE + "flowdata.js").then((r) => (r.ok ? r.text() : null)).then((t) => {
        if (!t) return;
        const fd = parseFlowData(t);
        if (fd) setFlowData(fd);
      }).catch(() => {});
    }, [meta]);

    const refetchComments = useCallback(() => {
      fetch(api("comments")).then((r) => (r.ok ? r.json() : { comments: [] }))
        .then((j) => {
          const server = j.comments || [];
          // Drop queued copies the server now knows (owner came back online
          // and collected the inbox); keep the rest visible locally.
          queuedRef.current = queuedRef.current.filter(
            (q) => !server.some((c) => c.id === q.id));
          setComments([...server, ...queuedRef.current]);
        })
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

    // ── Pin layout loop - repositions pins as the iframe scrolls/reflows.
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
            const st = (c.status || "open");
            if (st === "archived" || st === "done") continue;
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

    // ── Comment-mode arming - installs hover/click hooks in the iframe doc.
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
    // instead - acceptable; the hint pill stays visible as the off switch.)
    useEffect(() => {
      const onKey = (e) => {
        if (e.key === "Escape") { setCommentMode(false); setDraft(null); }
      };
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }, []);

    // ── Iframe lifecycle - track page, rearm comment mode after navigation.
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
        frame.src = BASE + branchPfx + "p/source/" + meta.prototype + "/" + (c.page || "index.html");
      } else if (c.page && c.page.includes("#") && frame.contentWindow) {
        try { frame.contentWindow.location.hash = c.page.split("#")[1] || ""; } catch {}
        setTimeout(go, 250);
      } else {
        go();
      }
    }, [meta, page, branchPfx]);

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
        // Snapshot the page BEFORE tearing the composer down - this captures
        // exactly what the reviewer is looking at. The composer/pins live in
        // THIS document (not the iframe), so they don't bleed into the shot.
        const shotRaw = await captureShot(iframeRef.current, d.anchor);
        // Bake any freehand strokes into the screenshot so the drawing + UI
        // ship as one raster (no strokes → the clean shot passes through).
        const shot = await compositeAnnotation(shotRaw, strokes, iframeRef.current);
        const r = await fetch(api("comments"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ page: d.page, anchor: d.anchor, pin: d.pin, text, author: identity }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || "failed to post comment");
        // Owner offline: the comment was queued at the broker, not stored on
        // the share. Show it locally, skip the shot/attachment uploads (they
        // need the owner's machine), and say what happened.
        if (j.queued && j.comment) {
          queuedRef.current = [...queuedRef.current, j.comment];
          setComments((cs) => [...cs, j.comment]);
          setDraft(null); setDraftText("");
          showNotice("Comment saved - the owner is offline right now and will "
            + "receive it when they're back. Screenshots aren't included while offline.");
          return;
        }
        // Attach the screenshot to the freshly-created comment. Best-effort:
        // the comment already exists, so a failed upload just means no image.
        const cid = j.comment && j.comment.id;
        if (cid && shot) {
          try {
            await fetch(api("comments/" + cid + "/shot"), {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ shot }),
            });
          } catch {}
        }
        // Upload reviewer image attachments as distinct items. Best-effort and
        // sequential - the comment already exists, so a failure just drops one
        // image rather than the whole comment.
        if (cid && attachments.length) {
          for (const a of attachments) {
            try {
              await fetch(api("comments/" + cid + "/attach"), {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ data: a.dataUrl, name: a.name }),
              });
            } catch {}
          }
        }
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
    const onDelete = (c) => mutate("comments/" + c.id + "/delete", {});

    // Reset = reload the prototype iframe at its first page (index.html). Pure
    // navigation - touches no comments. onFrameLoad re-syncs the page chip and
    // rearms comment mode. We also drop any in-flight draft/comment mode so the
    // composer doesn't dangle over a page that's about to change underfoot.
    const resetToFirstPage = useCallback(() => {
      const frame = iframeRef.current;
      if (!frame || !meta) return;
      setCommentMode(false);
      setDraft(null);
      setFlowsOpen(false);
      frame.src = BASE + branchPfx + meta.entry;
    }, [meta, branchPfx]);

    // Flows → prototype hop: land the main iframe on the clicked screen.
    const openFlowFrame = useCallback((f) => {
      setFlowsOpen(false);
      setCommentMode(false);
      setDraft(null);
      const frame = iframeRef.current;
      if (frame && meta) {
        frame.src = BASE + branchPfx + "p/source/" + meta.prototype + "/" + f.entry + (f.hash || "");
      }
    }, [meta, branchPfx]);

    // Pick a branch to review: reload the prototype from that branch's
    // committed tree. Comment mode and any draft drop first - the page is
    // about to change underfoot, same as reset.
    const onPickBranch = (b) => {
      if (!meta || b === (viewBranch || meta.branch)) return;
      setViewBranch(b === meta.branch ? "" : b);
      setCommentMode(false);
      setDraft(null);
      const frame = iframeRef.current;
      if (frame) frame.src = BASE + branchPathPfx(b) + meta.entry;
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

    // Brand: branch reads BEFORE the prototype name (project · ⎇branch / proto).
    // A custom label can't be decomposed, so it keeps label-then-branch order.
    const defaultLabel = meta.project && meta.label === meta.project + " / " + meta.prototype;
    const branchShown = viewBranch || meta.branch;

    // Sibling shares from the contributor registry (live refetch wins over the
    // boot meta's upload-time copy). "Self" = the entry whose URL carries this
    // page's token - never offered as a hop target.
    const curToken = (location.pathname.match(/\/s\/([a-f0-9]+)/) || [])[1] || "";
    const allLinks = (links || meta.links || []).filter((e) => e && e.url && e.prototype);
    const isSelf = (e) => curToken && e.url.indexOf("/s/" + curToken + "/") !== -1;
    const selfEntry = allLinks.find(isSelf) || null;
    const linkScore = (e) =>
      (selfEntry && e.install === selfEntry.install ? 4 : 0) + (e.hosted ? 2 : 0) + (e.live ? 1 : 0);

    // One hop target per OTHER shared prototype. Same-install links win when
    // several installs share a prototype (stay on the host you were given);
    // hosted beats live-only among the rest.
    const protoOptions = [];
    for (const e of allLinks) {
      if (e.prototype === meta.prototype) continue;
      const i = protoOptions.findIndex((o) => o.prototype === e.prototype);
      if (i === -1) protoOptions.push(e);
      else if (linkScore(e) > linkScore(protoOptions[i])) protoOptions[i] = e;
    }
    protoOptions.sort((a, b) => a.prototype.localeCompare(b.prototype));

    // Branch options: local branches switch IN PLACE via the /b/ gate route
    // (live shares only - meta.branches); other installs' shares of THIS
    // prototype on other branches are navigation hops. Local wins on a name
    // clash - an in-place flip beats leaving the page. An entry with NO
    // branch (published by an install predating the branch field) is still
    // offered - it IS another contributor's copy, we just can't name the
    // branch yet - keyed per install so several such contributors coexist.
    const localBranches = meta.branches || [];
    const crossBranches = [];
    for (const e of allLinks) {
      if (e.prototype !== meta.prototype || isSelf(e)) continue;
      if (e.branch && (e.branch === meta.branch || localBranches.indexOf(e.branch) !== -1)) continue;
      const key = e.branch || "@" + (e.install || e.url);
      const i = crossBranches.findIndex((o) => (o.branch || "@" + (o.install || o.url)) === key);
      if (i === -1) crossBranches.push(e);
      else if (linkScore(e) > linkScore(crossBranches[i])) crossBranches[i] = e;
    }
    const onPickBranchOption = (v) => {
      if (v.slice(0, 2) === "b:") onPickBranch(v.slice(2));
      else if (v.slice(0, 2) === "l:") {
        const e = crossBranches[+v.slice(2)];
        if (e) location.href = e.url;
      }
    };
    const branchDropdown = localBranches.length > 1 || crossBranches.length > 0;
    const branchEl = meta.branch ? html`<span className="sv-brand-sub sv-brand-branch" title=${"git branch: " + branchShown}>
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>
      </svg>${branchDropdown ? html`<select
          className="sv-branch-select" value=${"b:" + branchShown}
          title="Review another branch of this prototype - the owner's checkout is untouched"
          onChange=${(e) => onPickBranchOption(e.target.value)}>
          ${(localBranches.length ? localBranches : [branchShown]).map((b) => html`
            <option key=${"b:" + b} value=${"b:" + b}>${b}</option>`)}
          ${crossBranches.map((e, i) => html`
            <option key=${"l:" + (e.branch || e.install || i)} value=${"l:" + i}>${e.branch
              ? e.branch + (e.owner ? " · " + e.owner : "")
              : (e.owner || "contributor") + " · their copy"}</option>`)}
        </select><svg className="sv-branch-caret" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M6 9l6 6 6-6"/>
        </svg>` : branchShown}</span>` : null;

    // Prototype chip: a dropdown when the project has other shared prototypes
    // to hop to; a plain label otherwise.
    const protoEl = protoOptions.length ? html`<span className="sv-brand-label sv-brand-proto sv-brand-proto-pick">/<select
        className="sv-branch-select sv-proto-select" value=""
        title="Open another shared prototype of this project"
        onChange=${(e) => { if (e.target.value) location.href = e.target.value; }}>
        <option value="">${meta.prototype}</option>
        ${protoOptions.map((e) => html`<option key=${e.prototype} value=${e.url}>${e.prototype}</option>`)}
      </select><svg className="sv-branch-caret" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M6 9l6 6 6-6"/>
      </svg></span>` : html`<span className="sv-brand-label sv-brand-proto">/ ${meta.prototype}</span>`;

    // Clamp composer near its pin inside the stage.
    const composerStyle = draft ? {
      left: Math.min(Math.max(draft.x - 10, 8), Math.max(8, window.innerWidth - (sidebarOpen ? 320 : 0) - 300)) + "px",
      top: Math.min(draft.y + 16, window.innerHeight - 220) + "px",
    } : null;

    return html`
      <div className="sv-app">
        <div className="sv-topbar">
          <span className="sv-brand">
            <svg width="16" height="16" viewBox="0 0 834 865" fill="#1c1c1e" aria-hidden="true">
              <path d="M164.411 285.641C196.359 284.677 230.639 291.674 258.864 305.701C275.286 313.727 290.065 324.404 302.52 337.239C341.158 377.583 361.371 447.312 378.116 498.308C388.132 482.744 399.684 467.642 409.951 452.186C412.242 448.739 414.925 444.943 417.595 441.774C431.351 459.34 443.577 480.938 457.207 498.242C472.875 448.395 490.877 391.963 523.907 349.544C579.307 278.402 700.654 264.845 774.789 317.785C806.94 340.863 827.783 375.104 832.598 412.756C843.943 495.181 782.673 564.588 695.92 574.484C644.003 580.405 591.842 563.575 548.833 536.139C539.957 530.476 537.74 518.741 543.151 509.709C548.815 500.254 561.262 497.253 570.658 503.014C601.126 521.693 634.227 536.411 671.754 536.037C705.405 535.7 737.72 524.768 761.424 502.003C781.4 482.798 792.329 456.906 791.766 430.103C791.184 402.032 779.11 377.683 757.679 358.122C705.931 310.886 611.818 317.258 563.019 365.51C553.686 374.887 545.719 385.378 539.322 396.709C524.787 421.893 514.739 451.179 504.773 478.261C499.913 491.473 494.674 506.261 491.301 519.841C489.776 525.958 489.826 533.047 489.985 539.289C493.054 556.978 502.4 565.69 510.272 582.07C534.621 632.717 554.85 688.575 544.486 744.747C537.215 784.135 519.592 821.978 483.663 845.418C457.84 862.041 426.03 868.39 395.209 863.072C363.919 857.517 336.291 840.509 318.457 815.814C307.872 801.34 301.629 787.115 295.942 770.657C275.203 710.66 291.644 652.082 318.36 596.153C322.081 588.342 326.05 580.644 330.262 573.052C340.062 555.493 348.796 545.91 344.696 524.508C342.606 513.599 339.127 503.14 335.6 492.533C322.683 453.678 309.302 413.312 284.963 379.2C243.189 321.492 147.774 309.019 88.4573 349.581C64.3919 366.037 48.2945 389.328 43.7834 417.025C39.4073 443.486 46.4486 470.485 63.3567 492.083C93.1026 529.784 142.471 541.77 190.296 534.226C217.38 529.955 240.84 518.044 262.986 503.814C272.662 497.595 285.65 500.284 291.593 510.132C296.878 518.889 294.7 530.302 286.062 535.779C215.211 580.708 114.661 593.303 48.261 536.056C19.1106 510.632 1.8151 475.501 0.113512 438.245C-1.43994 398.716 12.9754 362.821 41.8772 333.94C73.8144 302.026 118.587 287.315 164.411 285.641ZM416.722 512.527C379.203 567.165 343.362 618.778 329.984 683.963C318.364 740.591 343.994 824.697 418.027 824.976C479.127 823.074 509.74 757.077 506.74 707.2C503.171 647.807 469.774 589.865 436.743 540.45C433.377 535.493 419.886 515.43 416.722 512.527ZM409.73 0.675811C437.369 -2.92606 472.166 8.29862 493.776 24.1416C524.015 46.3095 543.194 80.7427 547.699 116.211C561.045 221.334 486.296 312.27 421.665 390.357L417.78 394.772C405.573 381.446 392.688 364.92 381.071 350.798C336.182 296.042 296.156 233.386 287.029 163.654C279.36 105.059 308.709 39.0645 366.61 11.6826C380.614 5.06005 394.208 2.19545 409.73 0.675811ZM508.772 125.402C503.305 78.2536 464.224 35.4344 409.775 40.9278C348.153 48.2369 319.059 107.407 326.737 160.33C336.002 224.199 376.222 281.983 417.501 331.837L421.652 326.068C465.597 272.347 517.023 196.544 508.772 125.402Z"/>
            </svg>
            ${defaultLabel ? html`
              <span className="sv-brand-label">${meta.project}</span>
              ${branchEl}
              ${protoEl}` : html`
              <span className="sv-brand-label">${meta.label}</span>
              ${branchEl}
              ${protoOptions.length ? protoEl : null}`}
            <span className="sv-brand-sub">· shared for review</span>
          </span>
          <span className="sv-topbar-spacer"></span>
          <span className="sv-page-chip" title=${flowsOpen ? "Screen flows" : page}>${flowsOpen ? "screen flows" : page}</span>
          ${!gateBlocked && flowData && html`<button
            className=${"sv-btn" + (flowsOpen ? " is-active" : "")}
            title=${flowsOpen ? "Back to the prototype" : "Screen flows - every screen and how they connect"}
            onClick=${() => {
              setCommentMode(false); setDraft(null);
              setFlowsOpen(!flowsOpen);
            }}
          ><${FlowIcon}/><span className="sv-btn-label">Flows</span></button>`}
          ${!gateBlocked && html`<button
            className="sv-btn"
            disabled=${!flowsOpen && page === "index.html"}
            title=${!flowsOpen && page === "index.html" ? "Already on the first page" : "Reset - back to the first page of the prototype"}
            onClick=${resetToFirstPage}
          ><${HomeIcon}/><span className="sv-btn-label">Reset</span></button>`}
          <button
            className=${"sv-btn" + (commentMode ? " is-active" : "")}
            title=${commentMode ? "Exit comment mode (Esc)" : "Comment on an element - click anything in the prototype"}
            onClick=${() => {
              if (!commentMode && !requireIdentity("Add a name before commenting.")) return;
              setFlowsOpen(false);
              setDraft(null); setCommentMode(!commentMode);
            }}
          ><${CommentIcon}/><span className="sv-btn-label">${commentMode ? "Click an element…" : "Comment"}</span></button>
          <button
            className=${"sv-btn" + (sidebarOpen ? " is-active" : "")}
            onClick=${() => setSidebarOpen(!sidebarOpen)}
            title="Toggle the comments sidebar"
          ><${PanelIcon}/><span className="sv-btn-label">Comments</span><span className="sv-btn-count">${counts.open}</span></button>
        </div>
        <div className="sv-main">
          <div className=${"sv-stage" + (commentMode ? " is-commenting" : "")}>
            ${!gateBlocked && html`<iframe
              ref=${iframeRef}
              src=${BASE + meta.entry}
              title="Shared prototype"
              style=${flowsOpen ? { display: "none" } : null}
              onLoad=${onFrameLoad}
            ></iframe>`}
            ${!gateBlocked && flowsOpen && flowData && html`
              <${FlowMap}
                flow=${flowData}
                base=${BASE}
                prototype=${meta.prototype}
                onOpenFrame=${openFlowFrame}
              />
            `}
            ${commentMode && html`<div className="sv-hint">Click any element to pin a comment - Esc to cancel</div>`}
            ${commentMode && pins.map((p) => html`
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
              >${p.draft ? "+" : ""}</button>
            `)}
            ${draft && drawing && html`
              <${DrawOverlay} strokes=${strokes}
                onAddStroke=${(s) => setStrokes((a) => [...a, s])}/>
            `}
            ${draft && drawing && html`
              <div className="sv-draw-hint">Draw on the screen - your marks bake into the screenshot</div>
            `}
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
                <div className="sv-composer-tools">
                  <button className=${"sv-tool-btn" + (drawing ? " is-active" : "")}
                    title="Draw on the prototype - strokes bake into the screenshot"
                    onClick=${() => setDrawing((d) => !d)}><${PencilIcon}/> Draw</button>
                  ${strokes.length > 0 && html`
                    <button className="sv-tool-btn" title="Clear the drawing"
                      onClick=${() => setStrokes([])}>Clear</button>`}
                  <label className="sv-tool-btn" title="Attach images to this comment">
                    <${ImageIcon}/> Attach
                    <input type="file" accept="image/*" multiple
                      style=${{ display: "none" }} onChange=${onPickFiles}/>
                  </label>
                </div>
                ${attachments.length > 0 && html`
                  <div className="sv-attach-thumbs">
                    ${attachments.map((a, i) => html`
                      <div className="sv-attach-thumb" key=${i} title=${a.name}>
                        <img src=${a.dataUrl} alt=${a.name}/>
                        <button className="sv-attach-x" title="Remove"
                          onClick=${() => setAttachments((list) => list.filter((_, j) => j !== i))}>×</button>
                      </div>
                    `)}
                  </div>
                `}
                <div className="sv-composer-row">
                  <button className="sv-btn" onClick=${() => setDraft(null)}>Cancel</button>
                  <button className="sv-btn sv-btn-primary" disabled=${!draftText.trim() || posting}
                    onClick=${submitDraft}>${posting ? "Posting…" : "Comment"}</button>
                </div>
              </div>
            `}
            ${error && html`<div className="sv-banner">${error}</div>`}
            ${notice && html`<div className="sv-banner sv-banner-info">${notice}</div>`}
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
