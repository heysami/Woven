/* Woven user-testing REVIEWER REPLAY RUNTIME - researcher-facing surface that
   replays ONE testee's recorded prototype session. Served by the user-testing
   gate at /r/<token>/ (sibling of editor/shares.py's share gate). React 18 +
   htm UMD, no build step, mirrors editor/share/viewer.js architecture.

   ──────────────────────────────────────────────────────────────────────────
   SELF-REVIEW - the gate API + stream shapes this runtime depends on (the
   server author conforms to THIS; another stream owns serve.py / shares.py).
   All urls are RELATIVE to the page (location.pathname = /r/<token>/).

   GET  api/meta
        -> { sessionLabel, prototype,
             config:{ flows:[{id,name,tasks?}],
                      questions:[{id,at,kind,prompt,choices?,min?,max?}],
                      rating:{enabled,min,max,label},
                      recording:{rrweb,cursor,audio,gaze} },
             participant:{ id, name },
             meta:{ t0, durationMs, status },
             answers:{ answers:[{questionId,value}], rating } | null,
             markers:{ startAt, endAt, flows:[{id,startAt,endAt}] } | null }
        (answers / markers may be null or empty; config sub-objects may be
        partially absent and are defaulted here.)

   GET  api/stream?name=rrweb
        -> JSON ARRAY of rrweb events. The SERVER parses rrweb.jsonl for us.
           Events keep their NATIVE epoch-ms `timestamp`; rrweb-player consumes
           them as-is (it rebases internally to the first event).
   GET  api/stream?name=cursor
        -> JSON ARRAY of { t, x, y, type }  (t = ms relative to meta.t0)
   GET  api/stream?name=gaze
        -> JSON ARRAY of { t, x, y, conf }  (t = ms relative to meta.t0)
   GET  api/stream?name=audio
        -> raw audio.webm bytes, HTTP Range supported. Used directly as an
           <audio> src. Play head maps to meta.t0 + (offset ms).

   POST api/markers   body { startAt, endAt, flows:[{id,startAt,endAt}] }
        -> { ok: true }   (each value is ms relative to meta.t0, or null)

   TIMING MODEL (RECORDING FORMAT CONTRACT, pinned in editor/usertesting.py):
   • meta.t0 is the epoch-ms instant recording started.
   • cursor / gaze sample `t` are ms SINCE t0.
   • rrweb events keep native epoch-ms timestamps; subtract t0 to get ms-since-
     t0. rrweb-player's getMetaData().startTime is the first event's epoch-ms.
   • The PLAYHEAD this runtime tracks (playMs) is ms-since-t0. We derive it from
     the player's own time (player time + rrwebStart - t0) so cursor, gaze, and
     audio all align to the same clock as the DOM replay.
   • AUDIO SYNC: audio.currentTime (seconds) === playMs/1000. We keep audio
     slaved to the rrweb player: on a > tolerance drift we hard-seek audio to
     the player time; play/pause drives both together. The rrweb player is the
     master clock (it owns the DOM frames the researcher is reading).
   ────────────────────────────────────────────────────────────────────────── */

/* global React, ReactDOM, htm, rrwebPlayer */
(() => {
  const html = htm.bind(React.createElement);
  const { useState, useEffect, useRef, useMemo, useCallback } = React;

  // ── URL plumbing - location.pathname is /r/<token>/ (gate 301s slash-less).
  const BASE = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  const api = (p) => BASE + "api/" + p;
  const streamUrl = (name) => api("stream?name=" + encodeURIComponent(name));

  // rrweb-player UMD exposes window.rrwebPlayer; the constructor is its
  // `default` export. Tolerate either shape so a future bundle change is safe.
  const RRWebPlayer = (typeof rrwebPlayer !== "undefined")
    ? (rrwebPlayer && (rrwebPlayer.default || rrwebPlayer)) : null;

  // ── Line icons (Woven Icon.* set - 16-box, 1.5pt round stroke, currentColor).
  const Icon = {
    Play: ({ size = 14 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="currentColor"
        aria-hidden="true" style=${{ display: "block" }}>
        <path d="M4 3.2v9.6a.6.6 0 00.92.5l7.2-4.8a.6.6 0 000-1L4.92 2.7A.6.6 0 004 3.2z"/></svg>`,
    Pause: ({ size = 14 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="currentColor"
        aria-hidden="true" style=${{ display: "block" }}>
        <rect x="4" y="3" width="3" height="10" rx="1"/><rect x="9" y="3" width="3" height="10" rx="1"/></svg>`,
    Flag: ({ size = 14 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
        aria-hidden="true" style=${{ display: "block" }}>
        <path d="M4 14V2.5"/><path d="M4 3h7l-1.4 2.2L11 7.4H4"/></svg>`,
    Save: ({ size = 14 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
        aria-hidden="true" style=${{ display: "block" }}>
        <path d="M3 3h8l2 2v8H3z"/><path d="M5 3v3h5V3"/><path d="M5 13v-4h6v4"/></svg>`,
  };

  // ── Timecode mm:ss.t (ms in -> "1:23.4"). Negative / NaN clamp to 0.
  const fmt = (ms) => {
    if (ms == null || !isFinite(ms)) return "0:00.0";
    const s = Math.max(0, ms) / 1000;
    const m = Math.floor(s / 60);
    const r = s - m * 60;
    return m + ":" + (r < 10 ? "0" : "") + r.toFixed(1);
  };

  // ── Nearest-sample lookup over a t-sorted array (binary search on `.t`).
  // Returns the sample whose t is closest to `t`, or null for an empty list.
  const nearestSample = (samples, t) => {
    if (!samples || samples.length === 0) return null;
    let lo = 0, hi = samples.length - 1;
    if (t <= samples[0].t) return samples[0];
    if (t >= samples[hi].t) return samples[hi];
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const mt = samples[mid].t;
      if (mt === t) return samples[mid];
      if (mt < t) lo = mid + 1; else hi = mid - 1;
    }
    // lo is the first sample with t > target; hi the last with t < target.
    const a = samples[hi], b = samples[lo];
    if (!a) return b; if (!b) return a;
    return (t - a.t) <= (b.t - t) ? a : b;
  };

  // Defensive config defaulting - the server may omit sub-objects.
  const normConfig = (c) => {
    c = c || {};
    return {
      flows: Array.isArray(c.flows) ? c.flows : [],
      questions: Array.isArray(c.questions) ? c.questions : [],
      rating: c.rating || { enabled: false, min: 1, max: 5, label: "Overall experience" },
      recording: c.recording || { rrweb: true, cursor: true, audio: true, gaze: true },
    };
  };

  // ── Overlay canvas - draws cursor + gaze heat trail over the player surface.
  // Sample coords are in the IFRAME VIEWPORT space the testee recorded at
  // (meta.viewport when present, else the rrweb player's own width/height). We
  // map them onto the player's RENDERED prototype rect each frame so the dots
  // track the DOM even as rrweb-player letterboxes/scales the replay.
  function Overlay({ stageRef, getPlayerFrame, cursor, gaze, playMsRef, recCfg }) {
    const canvasRef = useRef(null);
    const trailRef = useRef([]);          // rolling gaze trail [{x,y,a}]
    const lastGazeTRef = useRef(-1);

    useEffect(() => {
      const canvas = canvasRef.current;
      const stage = stageRef.current;
      if (!canvas || !stage) return;
      const ctx = canvas.getContext("2d");
      let raf = 0, alive = true;
      // Cache the stage rect; only re-measure on resize (never per frame - that
      // thrashes layout; Woven canvas memory).
      let stageRect = stage.getBoundingClientRect();
      const remeasure = () => { stageRect = stage.getBoundingClientRect(); };
      const ro = new ResizeObserver(remeasure);
      ro.observe(stage);
      window.addEventListener("scroll", remeasure, true);

      // Map a recorded (x,y) in iframe-viewport space onto stage-local px.
      const mapPoint = (x, y) => {
        const fr = getPlayerFrame();   // { left, top, width, height, vw, vh } | null
        if (!fr || !fr.width || !fr.height) return null;
        const sx = (x / fr.vw) * fr.width;
        const sy = (y / fr.vh) * fr.height;
        return { x: fr.left - stageRect.left + sx, y: fr.top - stageRect.top + sy };
      };

      const draw = () => {
        if (!alive) return;
        const w = stage.clientWidth, h = stage.clientHeight;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
          canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
          canvas.style.width = w + "px"; canvas.style.height = h + "px";
        }
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
        const t = playMsRef.current;

        // ── Gaze heat trail (smoothed, semi-transparent - approximate, NOT
        // pixel-precise). Accumulate a short rolling window around the playhead.
        if (recCfg.gaze && gaze && gaze.length) {
          const g = nearestSample(gaze, t);
          if (g && g.t !== lastGazeTRef.current) {
            lastGazeTRef.current = g.t;
            const p = mapPoint(g.x, g.y);
            if (p) trailRef.current.push({ x: p.x, y: p.y, a: 1, conf: g.conf == null ? 1 : g.conf });
            if (trailRef.current.length > 28) trailRef.current.shift();
          }
          const trail = trailRef.current;
          for (let i = 0; i < trail.length; i++) {
            const pt = trail[i];
            pt.a *= 0.92;                       // fade the tail
            const r = 26 + 18 * (pt.conf || 1); // soft blob, scaled by confidence
            const alpha = Math.max(0, pt.a) * 0.22 * (0.4 + 0.6 * (pt.conf || 1));
            const grad = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, r);
            grad.addColorStop(0, "rgba(225,74,42," + alpha.toFixed(3) + ")");
            grad.addColorStop(1, "rgba(225,74,42,0)");
            ctx.fillStyle = grad;
            ctx.beginPath(); ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2); ctx.fill();
          }
          // Drop fully-faded points off the head of the trail.
          while (trail.length && trail[0].a < 0.04) trail.shift();
        }

        // ── Cursor (precise) - a ring + dot at the nearest cursor sample.
        if (recCfg.cursor && cursor && cursor.length) {
          const c = nearestSample(cursor, t);
          const p = c && mapPoint(c.x, c.y);
          if (p) {
            ctx.lineWidth = 2;
            ctx.strokeStyle = "rgba(20,20,24,0.9)";
            ctx.fillStyle = "rgba(255,255,255,0.95)";
            ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
            ctx.fillStyle = "rgba(20,20,24,0.95)";
            ctx.beginPath(); ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2); ctx.fill();
          }
        }
        raf = requestAnimationFrame(draw);
      };
      raf = requestAnimationFrame(draw);
      return () => {
        alive = false; cancelAnimationFrame(raf);
        ro.disconnect(); window.removeEventListener("scroll", remeasure, true);
      };
    }, [cursor, gaze, recCfg, getPlayerFrame, stageRef, playMsRef]);

    return html`<canvas ref=${canvasRef} className="rv-overlay"></canvas>
      ${recCfg.gaze && gaze && gaze.length ? html`<div className="rv-gaze-label">gaze (approximate)</div>` : null}`;
  }

  // ── App ───────────────────────────────────────────────────────────────
  function App() {
    const [meta, setMeta] = useState(null);
    const [metaErr, setMetaErr] = useState(null);
    const [rrwebEvents, setRrwebEvents] = useState(null);
    const [cursor, setCursor] = useState([]);
    const [gaze, setGaze] = useState([]);
    const [streamErr, setStreamErr] = useState(null);

    const [playing, setPlaying] = useState(false);
    const [playMs, setPlayMs] = useState(0);     // ms-since-t0 playhead (for UI)
    const [markers, setMarkers] = useState({ startAt: null, endAt: null, flows: [] });
    const [saving, setSaving] = useState(false);
    const [savedAt, setSavedAt] = useState(null);
    const [toast, setToast] = useState(null);

    const stageRef = useRef(null);          // the player container (overlay anchor)
    const playerHostRef = useRef(null);     // div rrweb-player mounts into
    const playerRef = useRef(null);         // rrwebPlayer instance
    const replayerRef = useRef(null);       // player.getReplayer()
    const audioRef = useRef(null);          // <audio> element
    const playMsRef = useRef(0); playMsRef.current = playMs;
    const rrwebStartRef = useRef(0);        // first rrweb event epoch-ms
    const t0Ref = useRef(0);

    const showToast = (m) => { setToast(m); setTimeout(() => setToast(null), 4000); };

    const cfg = useMemo(() => normConfig(meta && meta.config), [meta]);
    const durationMs = (meta && meta.meta && meta.meta.durationMs) || 0;
    const recCfg = cfg.recording;

    // ── Boot: meta first, then the three streams in parallel.
    useEffect(() => {
      fetch(api("meta")).then((r) => {
        if (!r.ok) throw new Error("session unavailable");
        return r.json();
      }).then((m) => {
        setMeta(m);
        t0Ref.current = (m.meta && m.meta.t0) || 0;
        // Seed marker tools from any markers already saved on the session.
        if (m.markers) {
          setMarkers({
            startAt: m.markers.startAt ?? null,
            endAt: m.markers.endAt ?? null,
            flows: Array.isArray(m.markers.flows) ? m.markers.flows : [],
          });
        }
      }).catch(() => setMetaErr("This replay link is no longer available."));
    }, []);

    useEffect(() => {
      if (!meta) return;
      const want = recCfg;
      const jobs = [];
      if (want.rrweb !== false) jobs.push(
        fetch(streamUrl("rrweb")).then((r) => (r.ok ? r.json() : [])).then((a) => setRrwebEvents(Array.isArray(a) ? a : []))
      ); else setRrwebEvents([]);
      if (want.cursor !== false) jobs.push(
        fetch(streamUrl("cursor")).then((r) => (r.ok ? r.json() : [])).then((a) => setCursor((Array.isArray(a) ? a : []).slice().sort((x, y) => x.t - y.t)))
      );
      if (want.gaze !== false) jobs.push(
        fetch(streamUrl("gaze")).then((r) => (r.ok ? r.json() : [])).then((a) => setGaze((Array.isArray(a) ? a : []).slice().sort((x, y) => x.t - y.t)))
      );
      Promise.all(jobs).catch(() => setStreamErr("Some recording streams failed to load."));
    }, [meta, recCfg]);

    // ── Build the rrweb-player once events are in. rrweb-player bundles the
    // rrweb replayer; we hand it the raw event array.
    useEffect(() => {
      if (!rrwebEvents || !playerHostRef.current || !RRWebPlayer) return;
      if (playerRef.current) return;          // build once
      if (rrwebEvents.length < 2) return;     // replayer needs >= 2 events
      let inst;
      try {
        inst = new RRWebPlayer({
          target: playerHostRef.current,
          props: {
            events: rrwebEvents,
            showController: false,
            autoPlay: false,
            mouseTail: false,            // we draw our own cursor overlay
            speedOption: [1, 2, 4, 8],
          },
        });
      } catch (e) {
        setStreamErr("The DOM replay could not be initialised.");
        return;
      }
      playerRef.current = inst;
      const replayer = (typeof inst.getReplayer === "function") ? inst.getReplayer() : null;
      replayerRef.current = replayer;
      try {
        const md = replayer && replayer.getMetaData ? replayer.getMetaData() : null;
        rrwebStartRef.current = (md && md.startTime) || (rrwebEvents[0] && rrwebEvents[0].timestamp) || 0;
      } catch {
        rrwebStartRef.current = (rrwebEvents[0] && rrwebEvents[0].timestamp) || 0;
      }

      // rrweb-player emits "ui-update-current-time" (ms from replay start) and
      // "finish" / "start" / "pause". We track its time as the master clock and
      // convert to ms-since-t0: playerTime + rrwebStart - t0.
      const onTime = (e) => {
        const playerMs = (e && e.payload != null) ? e.payload : 0;
        const sinceT0 = playerMs + rrwebStartRef.current - t0Ref.current;
        setPlayMs(sinceT0);
        syncAudio(playerMs);
      };
      const onState = (e) => {
        const s = e && e.payload && e.payload.player;
        if (s === "playing") { setPlaying(true); playAudio(); }
        else if (s === "paused") { setPlaying(false); pauseAudio(); }
      };
      const onFinish = () => { setPlaying(false); pauseAudio(); };
      try {
        inst.addEventListener("ui-update-current-time", onTime);
        inst.addEventListener("ui-update-player-state", onState);
        inst.addEventListener("finish", onFinish);
      } catch {}

      // Expose the rendered prototype rect for the overlay. rrweb-player wraps
      // the replay in `.rr-player` containing the iframe; we read the iframe's
      // box + the recorded viewport (replayer dimensions) so overlay coords map
      // onto the scaled/letterboxed replay correctly.
      // (read lazily via getPlayerFrame, never cached per frame here.)

      return () => {
        try {
          inst.removeEventListener("ui-update-current-time", onTime);
          inst.removeEventListener("ui-update-player-state", onState);
          inst.removeEventListener("finish", onFinish);
        } catch {}
      };
    }, [rrwebEvents]);

    // ── Audio control - slaved to the rrweb player (the master clock).
    const playAudio = useCallback(() => {
      const a = audioRef.current;
      if (a && a.src) { a.play().catch(() => {}); }
    }, []);
    const pauseAudio = useCallback(() => {
      const a = audioRef.current; if (a) { try { a.pause(); } catch {} }
    }, []);
    // Keep audio.currentTime within tolerance of the player time. playerMs is ms
    // from the rrweb replay START; audio offset is ms from t0; the two share t0
    // only if recording started together - we align via rrwebStart - t0 so the
    // audio second-clock matches the DOM frames.
    const syncAudio = useCallback((playerMs) => {
      const a = audioRef.current;
      if (!a || !a.src || !isFinite(a.duration)) return;
      const targetSec = (playerMs + rrwebStartRef.current - t0Ref.current) / 1000;
      if (targetSec < 0 || targetSec > a.duration + 0.5) return;
      if (Math.abs(a.currentTime - targetSec) > 0.25) {
        try { a.currentTime = Math.max(0, Math.min(a.duration, targetSec)); } catch {}
      }
    }, []);

    // ── Transport - play/pause/seek drive BOTH player and audio together.
    const togglePlay = useCallback(() => {
      const p = playerRef.current; if (!p) return;
      if (playing) { try { p.pause(); } catch {} setPlaying(false); pauseAudio(); }
      else { try { p.play(); } catch {} setPlaying(true); playAudio(); }
    }, [playing, playAudio, pauseAudio]);

    // Seek by ms-since-t0. rrweb-player.goto wants ms-from-replay-start.
    const seekToMs = useCallback((sinceT0) => {
      const p = playerRef.current; if (!p) return;
      const playerMs = Math.max(0, sinceT0 - (rrwebStartRef.current - t0Ref.current));
      try { p.goto(playerMs, playing); } catch {}
      setPlayMs(sinceT0);
      const a = audioRef.current;
      if (a && a.src && isFinite(a.duration)) {
        try { a.currentTime = Math.max(0, Math.min(a.duration, sinceT0 / 1000)); } catch {}
      }
    }, [playing]);

    // ── Marker tools - each sets the marker to the CURRENT playhead.
    const setStart = () => setMarkers((m) => ({ ...m, startAt: Math.round(playMsRef.current) }));
    const setEnd = () => setMarkers((m) => ({ ...m, endAt: Math.round(playMsRef.current) }));
    const setFlowEdge = (flowId, edge) => setMarkers((m) => {
      const key = edge === "in" ? "startAt" : "endAt";
      const at = Math.round(playMsRef.current);
      const flows = Array.isArray(m.flows) ? m.flows.slice() : [];
      const i = flows.findIndex((x) => x.id === flowId);
      if (i === -1) flows.push({ id: flowId, startAt: null, endAt: null, [key]: at });
      else flows[i] = { ...flows[i], [key]: at };
      return { ...m, flows };
    });
    const clearMarker = (kind, flowId, edge) => setMarkers((m) => {
      if (kind === "start") return { ...m, startAt: null };
      if (kind === "end") return { ...m, endAt: null };
      const flows = (m.flows || []).map((x) => x.id === flowId
        ? { ...x, [edge === "in" ? "startAt" : "endAt"]: null } : x);
      return { ...m, flows };
    });

    const flowOf = (flowId) => (markers.flows || []).find((x) => x.id === flowId) || {};

    const saveMarkers = useCallback(async () => {
      setSaving(true);
      try {
        const body = {
          startAt: markers.startAt ?? null,
          endAt: markers.endAt ?? null,
          flows: (markers.flows || []).map((f) => ({
            id: f.id, startAt: f.startAt ?? null, endAt: f.endAt ?? null,
          })),
        };
        const r = await fetch(api("markers"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || !j.ok) throw new Error(j.error || "save failed");
        setSavedAt(Date.now());
        showToast("Markers saved");
      } catch (e) {
        showToast("Could not save markers: " + (e.message || e));
      } finally { setSaving(false); }
    }, [markers]);

    // The rendered prototype rect for the overlay. Reads the player iframe box
    // + the recorded viewport so overlay coords (iframe space) map onto the
    // possibly-scaled replay. Called from the overlay's rAF; cheap DOM reads.
    const getPlayerFrame = useCallback(() => {
      const host = playerHostRef.current;
      if (!host) return null;
      const iframe = host.querySelector("iframe");
      if (!iframe) return null;
      const r = iframe.getBoundingClientRect();
      if (!r.width || !r.height) return null;
      // Recorded viewport: rrweb sets the iframe's width/height attributes to
      // the replay dimensions; the wrapper CSS-scales it. Prefer the attribute
      // size (recording space) and fall back to the rendered box.
      const vw = parseFloat(iframe.getAttribute("width")) || r.width;
      const vh = parseFloat(iframe.getAttribute("height")) || r.height;
      return { left: r.left, top: r.top, width: r.width, height: r.height, vw, vh };
    }, []);

    // ── Keyboard: Space toggles play, arrows nudge 1s.
    useEffect(() => {
      const onKey = (e) => {
        if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
        if (e.code === "Space") { e.preventDefault(); togglePlay(); }
        else if (e.key === "ArrowLeft") { e.preventDefault(); seekToMs(Math.max(0, playMsRef.current - 1000)); }
        else if (e.key === "ArrowRight") { e.preventDefault(); seekToMs(Math.min(durationMs, playMsRef.current + 1000)); }
      };
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }, [togglePlay, seekToMs, durationMs]);

    // ── Derived durations.
    const taskDuration = (markers.startAt != null && markers.endAt != null)
      ? markers.endAt - markers.startAt : null;

    // ── Render guards.
    if (metaErr) {
      return html`<div className="rv-app"><div className="rv-empty" style=${{ marginTop: 120 }}>
        <b>Replay unavailable</b>${metaErr}</div></div>`;
    }
    if (!meta) return html`<div className="rv-app"><div className="rv-boot">Loading session…</div></div>`;

    const pct = durationMs ? Math.max(0, Math.min(100, (playMs / durationMs) * 100)) : 0;
    const markPct = (ms) => (ms == null || !durationMs) ? null : Math.max(0, Math.min(100, (ms / durationMs) * 100));

    return html`
      <div className="rv-app">
        <div className="rv-topbar">
          <span className="rv-brand">
            <svg width="30" height="16" viewBox="0 0 76 40" fill="#1c1c1e" aria-hidden="true">
              <path d="M14 2L26 14L14 26L2 14Z"/><path d="M38 2L50 14L38 26L26 14Z"/>
              <path d="M62 2L74 14L62 26L50 14Z"/><path d="M26 14L38 26L26 38L14 26Z"/>
              <path d="M50 14L62 26L50 38L38 26Z"/>
            </svg>
            ${meta.sessionLabel || "Session replay"}
            <span className="rv-brand-sub">· user-testing replay</span>
          </span>
          <span className="rv-topbar-spacer"></span>
          ${meta.participant && html`<span className="rv-participant">${meta.participant.name || "Participant"}</span>`}
          <span className="rv-status-chip">${(meta.meta && meta.meta.status) || "complete"}</span>
        </div>

        <div className="rv-main">
          <div className="rv-stage-wrap">
            ${streamErr && html`<div className="rv-banner">${streamErr}</div>`}
            <div className="rv-stage" ref=${stageRef}>
              <div className="rv-player-host" ref=${playerHostRef}></div>
              ${rrwebEvents && rrwebEvents.length < 2 && html`
                <div className="rv-empty rv-empty-stage"><b>No DOM replay</b>
                  This recording has no replayable frames.</div>`}
              <${Overlay}
                stageRef=${stageRef}
                getPlayerFrame=${getPlayerFrame}
                cursor=${cursor} gaze=${gaze}
                playMsRef=${playMsRef} recCfg=${recCfg}
              />
            </div>

            <!-- Hidden audio element, driven by the player clock. -->
            <audio ref=${audioRef} src=${recCfg.audio !== false ? streamUrl("audio") : null}
              preload="auto" style=${{ display: "none" }}></audio>

            <!-- Transport + scrubber + marker rail -->
            <div className="rv-transport">
              <button className="rv-play" onClick=${togglePlay}
                title=${playing ? "Pause (Space)" : "Play (Space)"}>
                ${playing ? html`<${Icon.Pause} size=${16}/>` : html`<${Icon.Play} size=${16}/>`}
              </button>
              <span className="rv-time">${fmt(playMs)} <span className="rv-time-sep">/</span> ${fmt(durationMs)}</span>
              <div className="rv-scrub" onClick=${(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                seekToMs(frac * durationMs);
              }}>
                <div className="rv-scrub-track"></div>
                <div className="rv-scrub-fill" style=${{ width: pct + "%" }}></div>
                <!-- marker ticks -->
                ${markPct(markers.startAt) != null && html`<div className="rv-tick rv-tick-start"
                  style=${{ left: markPct(markers.startAt) + "%" }} title=${"Start " + fmt(markers.startAt)}></div>`}
                ${markPct(markers.endAt) != null && html`<div className="rv-tick rv-tick-end"
                  style=${{ left: markPct(markers.endAt) + "%" }} title=${"End " + fmt(markers.endAt)}></div>`}
                ${(markers.flows || []).map((f) => html`
                  ${markPct(f.startAt) != null && html`<div key=${f.id + "-in"} className="rv-tick rv-tick-flow-in"
                    style=${{ left: markPct(f.startAt) + "%" }} title=${"Flow in " + fmt(f.startAt)}></div>`}
                  ${markPct(f.endAt) != null && html`<div key=${f.id + "-out"} className="rv-tick rv-tick-flow-out"
                    style=${{ left: markPct(f.endAt) + "%" }} title=${"Flow out " + fmt(f.endAt)}></div>`}
                `)}
                <div className="rv-scrub-head" style=${{ left: pct + "%" }}></div>
              </div>
            </div>

            <!-- Marker tools -->
            <div className="rv-markers">
              <div className="rv-marker-group">
                <span className="rv-marker-label"><${Icon.Flag}/> Task</span>
                <button className="rv-mbtn" onClick=${setStart}>Set start</button>
                <span className="rv-marker-val">${markers.startAt != null ? fmt(markers.startAt) : "·"}
                  ${markers.startAt != null && html`<button className="rv-clear" title="Clear"
                    onClick=${() => clearMarker("start")}>×</button>`}</span>
                <button className="rv-mbtn" onClick=${setEnd}>Set end</button>
                <span className="rv-marker-val">${markers.endAt != null ? fmt(markers.endAt) : "·"}
                  ${markers.endAt != null && html`<button className="rv-clear" title="Clear"
                    onClick=${() => clearMarker("end")}>×</button>`}</span>
                ${taskDuration != null && html`<span className="rv-duration">task ${fmt(taskDuration)}</span>`}
              </div>
              ${cfg.flows.map((flow) => {
                const fm = flowOf(flow.id);
                const dur = (fm.startAt != null && fm.endAt != null) ? fm.endAt - fm.startAt : null;
                return html`
                  <div className="rv-marker-group" key=${flow.id}>
                    <span className="rv-marker-label rv-flow-name">${flow.name || flow.id}</span>
                    <button className="rv-mbtn" onClick=${() => setFlowEdge(flow.id, "in")}>Set in</button>
                    <span className="rv-marker-val">${fm.startAt != null ? fmt(fm.startAt) : "·"}
                      ${fm.startAt != null && html`<button className="rv-clear" title="Clear"
                        onClick=${() => clearMarker("flow", flow.id, "in")}>×</button>`}</span>
                    <button className="rv-mbtn" onClick=${() => setFlowEdge(flow.id, "out")}>Set out</button>
                    <span className="rv-marker-val">${fm.endAt != null ? fmt(fm.endAt) : "·"}
                      ${fm.endAt != null && html`<button className="rv-clear" title="Clear"
                        onClick=${() => clearMarker("flow", flow.id, "out")}>×</button>`}</span>
                    ${dur != null && html`<span className="rv-duration">${fmt(dur)}</span>`}
                  </div>`;
              })}
              <div className="rv-marker-save">
                <button className="rv-btn rv-btn-primary" disabled=${saving} onClick=${saveMarkers}>
                  <${Icon.Save}/> ${saving ? "Saving…" : "Save markers"}</button>
                ${savedAt && html`<span className="rv-saved">saved</span>`}
              </div>
            </div>
          </div>

          <!-- Side panel: answers + rating -->
          <div className="rv-side">
            <div className="rv-side-head">
              <span className="rv-side-title">Responses</span>
              ${meta.prototype && html`<span className="rv-proto" title=${meta.prototype}>${meta.prototype}</span>`}
            </div>
            <div className="rv-side-body">
              <${AnswerList} questions=${cfg.questions} answers=${meta.answers} rating=${cfg.rating}/>
            </div>
          </div>
        </div>
        ${toast && html`<div className="rv-toast">${toast}</div>`}
      </div>
    `;
  }

  // ── Answers + rating panel ────────────────────────────────────────────
  function AnswerList({ questions, answers, rating }) {
    const map = useMemo(() => {
      const m = new Map();
      const list = (answers && Array.isArray(answers.answers)) ? answers.answers : [];
      for (const a of list) m.set(a.questionId, a.value);
      return m;
    }, [answers]);
    const ratingVal = answers ? answers.rating : null;
    const fmtVal = (v) => {
      if (v == null || v === "") return html`<span className="rv-no-answer">no answer</span>`;
      if (Array.isArray(v)) return v.join(", ");
      if (typeof v === "boolean") return v ? "Yes" : "No";
      return String(v);
    };
    const hasQuestions = questions && questions.length;
    if (!hasQuestions && ratingVal == null) {
      return html`<div className="rv-empty"><b>No responses</b>
        The testee did not leave answers, or they have not been recorded yet.</div>`;
    }
    return html`
      <div className="rv-answers">
        ${rating && rating.enabled && html`
          <div className="rv-rating">
            <div className="rv-rating-label">${rating.label || "Overall experience"}</div>
            <div className="rv-rating-val">
              ${ratingVal != null
                ? html`<span className="rv-rating-num">${ratingVal}</span>
                    <span className="rv-rating-scale">/ ${rating.max != null ? rating.max : 5}</span>`
                : html`<span className="rv-no-answer">not rated</span>`}
            </div>
          </div>`}
        ${(questions || []).map((q) => html`
          <div className="rv-answer" key=${q.id}>
            <div className="rv-q-prompt">${q.prompt || q.id}
              ${q.at && q.at !== "general" && html`<span className="rv-q-at">${q.at}</span>`}</div>
            <div className="rv-q-value">${fmtVal(map.get(q.id))}</div>
          </div>`)}
      </div>`;
  }

  ReactDOM.createRoot(document.getElementById("root")).render(html`<${App}/>`);
})();
