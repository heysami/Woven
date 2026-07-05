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
           Events keep their NATIVE epoch-ms `timestamp`; rrweb.Replayer
           consumes them as-is (it rebases internally to the first event).
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
   • The PLAYHEAD this runtime tracks (playMs) is ms-since-t0, advanced by a
     WALL-CLOCK rAF loop (anchor + real elapsed) - NOT by the replayer's own
     clock. The rrweb DOM stream can be shorter than the session and the
     replayer's clock freezes at its last event, so the wall clock is the
     master: the replayer follows the playhead and holds its last frame past
     its own end. Cursor, gaze, and audio all align to the same playhead.
   • AUDIO SYNC: audio.currentTime (seconds) tracks the playhead; on a
     > tolerance drift we hard-seek audio; play/pause drives both together.
   • SCALING: rrweb.Replayer renders into `.replayer-wrapper` at the RECORDED
     viewport size and does NOT auto-fit (rrweb-player used to). We CSS-scale
     the wrapper to fit `.rv-player-host` (transform: scale, origin top-left)
     and recompute on host resize + after the first full snapshot is built.
   ────────────────────────────────────────────────────────────────────────── */

/* global React, ReactDOM, htm, rrweb */
(() => {
  const html = htm.bind(React.createElement);
  const { useState, useEffect, useRef, useMemo, useCallback } = React;

  // ── URL plumbing - location.pathname is /r/<token>/ (gate 301s slash-less).
  const BASE = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  const api = (p) => BASE + "api/" + p;
  const streamUrl = (name) => api("stream?name=" + encodeURIComponent(name));

  // rrweb UMD exposes window.rrweb with the Replayer constructor (the same
  // build testee.js records with). We drive it directly.
  const RRWebReplayer = (typeof rrweb !== "undefined" && rrweb && rrweb.Replayer)
    ? rrweb.Replayer : null;

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

  // ── Pre-rendered gaze blob sprite - ONE radial gradient rasterised to an
  // offscreen canvas, then drawImage'd per trail point with per-point alpha +
  // scale (a createRadialGradient per point per frame is needless work in the
  // rAF draw path). Colour and falloff are fixed constants, so the sprite
  // builds once; key a rebuild here if either ever becomes configurable.
  const GAZE_BLOB_R = 128;   // sprite radius px; trail radii scale down from it
  let gazeBlobSprite = null;
  const getGazeBlob = () => {
    if (gazeBlobSprite) return gazeBlobSprite;
    const c = document.createElement("canvas");
    c.width = c.height = GAZE_BLOB_R * 2;
    const g = c.getContext("2d");
    const grad = g.createRadialGradient(GAZE_BLOB_R, GAZE_BLOB_R, 0, GAZE_BLOB_R, GAZE_BLOB_R, GAZE_BLOB_R);
    grad.addColorStop(0, "rgba(225,74,42,1)");
    grad.addColorStop(1, "rgba(225,74,42,0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, GAZE_BLOB_R * 2, GAZE_BLOB_R * 2);
    gazeBlobSprite = c;
    return gazeBlobSprite;
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
          const blob = getGazeBlob();
          for (let i = 0; i < trail.length; i++) {
            const pt = trail[i];
            pt.a *= 0.92;                       // fade the tail
            const r = 26 + 18 * (pt.conf || 1); // soft blob, scaled by confidence
            // Sprite alpha is 1 at the centre; globalAlpha carries the per-point
            // fade, so the composite matches the old per-point gradient exactly.
            ctx.globalAlpha = Math.max(0, pt.a) * 0.22 * (0.4 + 0.6 * (pt.conf || 1));
            ctx.drawImage(blob, pt.x - r, pt.y - r, r * 2, r * 2);
          }
          ctx.globalAlpha = 1;
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
    const [replayerReady, setReplayerReady] = useState(false);
    const detectedRef = useRef(false);
    const [saving, setSaving] = useState(false);
    const [savedAt, setSavedAt] = useState(null);
    const [toast, setToast] = useState(null);

    const stageRef = useRef(null);          // the player container (overlay anchor)
    const playerHostRef = useRef(null);     // div rrweb.Replayer mounts into
    const replayerRef = useRef(null);       // rrweb.Replayer instance
    const audioRef = useRef(null);          // <audio> element
    const playMsRef = useRef(0); playMsRef.current = playMs;
    const playingRef = useRef(false);       // mirrors `playing` for the rAF loop
    const rrwebStartRef = useRef(0);        // first rrweb event epoch-ms
    const t0Ref = useRef(0);
    const rafRef = useRef(0);               // playhead rAF handle (driven by us)
    const scaleRef = useRef(1);             // current wrapper CSS scale (fit)
    const fitRef = useRef(null);            // recompute-fit fn (set after build)
    const wrapRef = useRef(null);           // cached .replayer-wrapper element
    const wrapRectRef = useRef(null);       // cached player frame (getPlayerFrame)
    // Wall-clock anchors. The rrweb DOM stream can be SHORTER than the session
    // (the page goes static, or it ends early) - if we used the replayer's own
    // clock as master it would freeze the whole transport at the last DOM event.
    // So the playhead is a wall clock spanning the full session; the replayer
    // just holds its last frame past its own end.
    const anchorWallRef = useRef(0);        // performance.now() at last play/seek
    const anchorMsRef = useRef(0);          // playhead (sinceT0) at that anchor

    const showToast = (m) => { setToast(m); setTimeout(() => setToast(null), 4000); };

    const cfg = useMemo(() => normConfig(meta && meta.config), [meta]);
    const durationMs = (meta && meta.meta && meta.meta.durationMs) || 0;
    const durationMsRef = useRef(0); durationMsRef.current = durationMs;
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

    // ── Build the rrweb.Replayer once events are in. The Replayer renders the
    // DOM replay into a `.replayer-wrapper` (containing the iframe) at the
    // RECORDED viewport size; it does NOT auto-fit, so we CSS-scale the wrapper
    // to the host below. rrweb.Replayer emits no per-frame time event, so the
    // transport (play/pause/seek) drives our own rAF playhead loop instead.
    useEffect(() => {
      if (!rrwebEvents || !playerHostRef.current || !RRWebReplayer) return;
      if (replayerRef.current) return;        // build once
      if (rrwebEvents.length < 2) return;     // replayer needs >= 2 events
      const host = playerHostRef.current;
      let replayer;
      try {
        replayer = new RRWebReplayer(rrwebEvents, {
          root: host,
          mouseTail: false,        // we draw our own cursor overlay
          skipInactive: false,
          speed: 1,
          UNSAFE_replayCanvas: true,   // replay the canvas image-snapshots (games/polish layers)
        });
      } catch (e) {
        setStreamErr("The DOM replay could not be initialised.");
        return;
      }
      replayerRef.current = replayer;
      try {
        const md = replayer.getMetaData ? replayer.getMetaData() : null;
        rrwebStartRef.current = (md && md.startTime) || (rrwebEvents[0] && rrwebEvents[0].timestamp) || 0;
      } catch {
        rrwebStartRef.current = (rrwebEvents[0] && rrwebEvents[0].timestamp) || 0;
      }

      // Recorded viewport: prefer the first meta (type-4) event's width/height,
      // fall back to the wrapper's own box.
      const metaEvt = rrwebEvents.find((ev) => ev && ev.type === 4 && ev.data);
      const recW = (metaEvt && metaEvt.data.width) || 0;
      const recH = (metaEvt && metaEvt.data.height) || 0;

      // Scale the `.replayer-wrapper` to fit `.rv-player-host`, centred. The
      // wrapper sits at the recorded viewport size; we transform: scale() it.
      const fit = () => {
        const wrap = host.querySelector(".replayer-wrapper");
        if (!wrap) return;
        const w = recW || parseFloat(wrap.style.width) || wrap.offsetWidth || 1;
        const h = recH || parseFloat(wrap.style.height) || wrap.offsetHeight || 1;
        const hostW = host.clientWidth || 1;
        const hostH = host.clientHeight || 1;
        const scale = Math.min(hostW / w, hostH / h) || 1;
        scaleRef.current = scale;
        // Centre: host is flex-centered, but a scaled element keeps its layout
        // box at the unscaled size, so we offset by the leftover space.
        const offX = Math.max(0, (hostW - w * scale) / 2);
        const offY = Math.max(0, (hostH - h * scale) / 2);
        wrap.style.position = "absolute";
        wrap.style.left = "0";
        wrap.style.top = "0";
        wrap.style.transformOrigin = "top left";
        wrap.style.transform = "translate(" + offX + "px," + offY + "px) scale(" + scale + ")";
        // The overlay's cached frame is stale the moment the transform changes -
        // refresh the element cache, drop the rect (getPlayerFrame re-measures).
        wrapRef.current = wrap;
        wrapRectRef.current = null;
        // rrweb resizes the wrapper on viewport meta events mid-replay; observing
        // it routes those through fit too (observe() is a no-op when repeated).
        ro.observe(wrap);
      };
      fitRef.current = fit;
      // Recompute on host resize.
      const ro = new ResizeObserver(fit);
      ro.observe(host);
      // Ancestor scroll shifts the wrapper's viewport rect; the overlay
      // remeasures its stage rect on the same event, so the cached wrapper rect
      // must drop with it or the two drift apart.
      const dropWrapRect = () => { wrapRectRef.current = null; };
      window.addEventListener("scroll", dropWrapRect, true);
      // The wrapper + its iframe snapshot land asynchronously; fit once now and
      // again on the next frames so the first full snapshot is sized correctly.
      fit();
      const t1 = setTimeout(fit, 0);
      const t2 = setTimeout(fit, 120);
      const t3 = setTimeout(fit, 400);

      // Show the FIRST snapshot immediately, paused at 0 (not blank).
      try { replayer.pause(0); } catch {}
      setReplayerReady(true);
      setTimeout(fit, 0);

      // The DOM stream can end before the session does, so the replayer firing
      // "finish" does NOT mean the session is over - hold the last frame and let
      // the wall clock keep the playhead + audio running to the real end. Only
      // hard-stop here if we have no known session duration to fall back on.
      const onFinish = () => {
        if (!durationMsRef.current) { stopRaf(); setPlaying(false); playingRef.current = false; pauseAudio(); }
      };
      try { replayer.on("finish", onFinish); } catch {}

      return () => {
        stopRaf();
        try { ro.disconnect(); } catch {}
        window.removeEventListener("scroll", dropWrapRect, true);
        clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
        try { replayer.off && replayer.off("finish", onFinish); } catch {}
        try { replayer.pause(); } catch {}
        fitRef.current = null;
        replayerRef.current = null;
        wrapRef.current = null;
        wrapRectRef.current = null;
      };
    }, [rrwebEvents]);

    // ── Playhead rAF loop. The playhead is a WALL CLOCK (anchor + real elapsed),
    // NOT the replayer's clock - so it spans the full session even after the DOM
    // stream ends. Advances ms-since-t0 + audio sync; stops at durationMs.
    const stopRaf = useCallback(() => {
      if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = 0; }
    }, []);
    const startRaf = useCallback(() => {
      stopRaf();
      const tick = () => {
        if (!playingRef.current) { rafRef.current = 0; return; }
        // Wall clock: playhead = anchor + real elapsed. Independent of the rrweb
        // replayer's clock (which caps at the last DOM event), so the transport
        // runs the FULL session even when the DOM goes static partway through.
        const sinceT0 = anchorMsRef.current + (performance.now() - anchorWallRef.current);
        const dur = durationMsRef.current || 0;
        if (dur && sinceT0 >= dur) {
          setPlayMs(dur);
          stopRaf(); setPlaying(false); playingRef.current = false; pauseAudio();
          return;
        }
        setPlayMs(sinceT0);
        syncAudio(sinceT0ToReplayer(sinceT0));
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
      // NOTE: deps stay [stopRaf] only. pauseAudio/syncAudio/sinceT0ToReplayer are
      // declared BELOW this callback; listing them here reads them in their TDZ
      // during render and crashes the whole reviewer. The tick uses them at rAF
      // time (after init), and they are stable, so the closure stays correct.
    }, [stopRaf]);

    // ── Audio control - kept in step with the wall-clock playhead.
    const playAudio = useCallback(() => {
      const a = audioRef.current;
      if (a && a.src) { a.play().catch(() => {}); }
    }, []);
    const pauseAudio = useCallback(() => {
      const a = audioRef.current; if (a) { try { a.pause(); } catch {} }
    }, []);
    // Keep audio.currentTime within tolerance of the replayer time. replayerMs
    // is ms from the rrweb replay START; audio offset is ms from t0; the two
    // share t0 only if recording started together - we align via rrwebStart - t0
    // so the audio second-clock matches the DOM frames.
    const syncAudio = useCallback((replayerMs) => {
      const a = audioRef.current;
      if (!a || !a.src || !isFinite(a.duration)) return;
      const targetSec = (replayerMs + rrwebStartRef.current - t0Ref.current) / 1000;
      if (targetSec < 0 || targetSec > a.duration + 0.5) return;
      if (Math.abs(a.currentTime - targetSec) > 0.25) {
        try { a.currentTime = Math.max(0, Math.min(a.duration, targetSec)); } catch {}
      }
    }, []);

    // MediaRecorder webm ships with NO duration header, so a.duration is Infinity
    // and the element cannot seek - every syncAudio/seek above bails on the
    // isFinite() guard and the audio free-runs, ignoring the timeline. Force the
    // browser to scan the file (seek past the end) so duration + seeking work.
    useEffect(() => {
      const a = audioRef.current;
      if (!a) return;
      let done = false;
      const onMeta = () => { if (a.duration === Infinity) { try { a.currentTime = 1e101; } catch {} } };
      const onDur = () => {
        if (!done && isFinite(a.duration) && a.duration > 0) {
          done = true;
          try { a.currentTime = 0; } catch {}
        }
      };
      a.addEventListener("loadedmetadata", onMeta);
      a.addEventListener("durationchange", onDur);
      if (a.readyState >= 1 && a.duration === Infinity) onMeta();   // metadata already cached
      return () => {
        a.removeEventListener("loadedmetadata", onMeta);
        a.removeEventListener("durationchange", onDur);
      };
    }, [meta, recCfg]);

    // ── Transport - play/pause/seek drive BOTH replayer and audio together.
    // replayer.play(ms)/pause(ms) take ms from the replay START; our playhead is
    // ms-since-t0, so convert via (sinceT0 - (rrwebStart - t0)).
    const sinceT0ToReplayer = (sinceT0) =>
      Math.max(0, sinceT0 - (rrwebStartRef.current - t0Ref.current));

    const togglePlay = useCallback(() => {
      const r = replayerRef.current; if (!r) return;
      if (playingRef.current) {
        try { r.pause(); } catch {}
        setPlaying(false); playingRef.current = false; stopRaf(); pauseAudio();
      } else {
        const fromMs = sinceT0ToReplayer(playMsRef.current);
        try { r.play(fromMs); } catch {}
        anchorWallRef.current = performance.now();
        anchorMsRef.current = playMsRef.current;
        const a = audioRef.current;
        if (a && a.src && isFinite(a.duration)) { try { a.currentTime = Math.max(0, Math.min(a.duration, playMsRef.current / 1000)); } catch {} }
        setPlaying(true); playingRef.current = true; playAudio(); startRaf();
      }
    }, [playAudio, pauseAudio, startRaf, stopRaf]);

    // Seek by ms-since-t0. replayer.pause(ms) jumps + holds; if we were playing
    // we resume from there. Keep audio in sync.
    const seekToMs = useCallback((sinceT0) => {
      const r = replayerRef.current; if (!r) return;
      const replayerMs = sinceT0ToReplayer(sinceT0);
      const wasPlaying = playingRef.current;
      try { r.pause(replayerMs); } catch {}
      if (wasPlaying) { try { r.play(replayerMs); } catch {} }
      setPlayMs(sinceT0);
      anchorWallRef.current = performance.now();
      anchorMsRef.current = sinceT0;
      syncAudio(replayerMs);
      const a = audioRef.current;
      if (a && a.src && isFinite(a.duration)) {
        try { a.currentTime = Math.max(0, Math.min(a.duration, sinceT0 / 1000)); } catch {}
      }
    }, [syncAudio]);

    // ── Marker tools - each sets the marker to the CURRENT playhead.
    const setStart = () => setMarkers((m) => ({ ...m, startAt: Math.round(playMsRef.current) }));
    const setEnd = () => setMarkers((m) => ({ ...m, endAt: Math.round(playMsRef.current) }));
    const setFlowEdge = (flowId, edge) => setMarkers((m) => {
      const key = edge === "in" ? "startAt" : "endAt";
      const at = Math.round(playMsRef.current);
      const flows = Array.isArray(m.flows) ? m.flows.slice() : [];
      const i = flows.findIndex((x) => x.id === flowId);
      if (i === -1) flows.push({ id: flowId, startAt: null, endAt: null, [key]: at, overridden: true });
      else flows[i] = { ...flows[i], [key]: at, overridden: true };
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

    // ── Auto-derive markers from the per-flow triggers defined on the prototype.
    // Start = when the start element was clicked; End = when the end element was
    // clicked, or (kind:"page") when that page was reached. We scan rrweb's
    // MouseInteraction events and resolve each click's node via the replayer's
    // live DOM mirror (stepping the replayer to the click moment so the node
    // exists), testing it against the trigger's selector (with a tag+text
    // fuzzy fallback). All times convert to ms-since-t0.
    const nodeMatches = (node, anchor) => {
      if (!node || node.nodeType !== 1 || !anchor) return false;
      if (anchor.selector) {
        try { if (node.matches && node.matches(anchor.selector)) return true; } catch {}
        try { if (node.closest && node.closest(anchor.selector)) return true; } catch {}
      }
      if (anchor.tag && anchor.text && node.tagName && node.tagName.toLowerCase() === anchor.tag) {
        if ((node.textContent || "").trim().slice(0, 200) === anchor.text) return true;
      }
      return false;
    };
    const detectMarkers = useCallback(() => {
      const r = replayerRef.current, evs = rrwebEvents;
      if (!r || !evs || typeof r.getMirror !== "function") return;
      const mirror = r.getMirror();
      const t0 = t0Ref.current, rrwebStart = rrwebStartRef.current;
      const restoreMs = playMsRef.current;
      const clicks = evs.filter((ev) => ev && ev.type === 3 && ev.data && ev.data.source === 2 && (ev.data.type === 1 || ev.data.type === 2));
      const firstClickEpoch = (anchor, afterEpoch) => {
        for (const ev of clicks) {
          if (afterEpoch != null && ev.timestamp < afterEpoch) continue;
          try { r.pause(Math.max(0, ev.timestamp - rrwebStart)); } catch {}
          let node = null;
          try { node = mirror.getNode(ev.data.id); } catch {}
          if (nodeMatches(node, anchor)) return ev.timestamp;
        }
        return null;
      };
      const norm = (s) => (s || "").split("?")[0].split("#")[0];
      const pageEpoch = (page) => {
        for (let i = 1; i < evs.length; i++) {
          const ev = evs[i];
          if (ev && ev.type === 4 && ev.data && page && norm(ev.data.href).endsWith(norm(page))) return ev.timestamp;
        }
        let seen = 0;
        for (const ev of evs) { if (ev && ev.type === 2) { seen++; if (seen >= 2) return ev.timestamp; } }
        return null;
      };
      const outFlows = (cfg.flows || []).map((f) => {
        const sE = f.start ? firstClickEpoch(f.start, null) : null;
        let eE = null;
        if (f.end) eE = (f.end.kind === "page") ? pageEpoch(f.end.page) : firstClickEpoch(f.end, sE);
        const sAt = sE != null ? Math.round(sE - t0) : null;
        const eAt = eE != null ? Math.round(eE - t0) : null;
        return { id: f.id, startAt: sAt, endAt: eAt, startAuto: sAt, endAuto: eAt };
      });
      // Restore the playhead - and keep playing if we were (Re-detect can be
      // clicked mid-playback; otherwise the replay would freeze while the UI
      // still showed "playing").
      try {
        const back = Math.max(0, sinceT0ToReplayer(restoreMs));
        if (playingRef.current) r.play(back); else r.pause(back);
      } catch {}
      setMarkers((m) => {
        const prev = new Map((m.flows || []).map((f) => [f.id, f]));
        const merged = outFlows.map((f) => {
          const p = prev.get(f.id);
          if (p && p.overridden) return { ...f, startAt: p.startAt ?? f.startAt, endAt: p.endAt ?? f.endAt, overridden: true };
          return f;
        });
        const ms = merged.map((f) => f.startAt).filter((x) => x != null);
        const me = merged.map((f) => f.endAt).filter((x) => x != null);
        return { startAt: ms.length ? Math.min.apply(null, ms) : null, endAt: me.length ? Math.max.apply(null, me) : null, flows: merged };
      });
    }, [rrwebEvents, cfg]);
    const reDetect = () => { detectedRef.current = true; detectMarkers(); };

    // Auto-detect once the replayer is ready, unless markers were already saved.
    useEffect(() => {
      if (!replayerReady || detectedRef.current) return;
      detectedRef.current = true;
      const hasSaved = markers && ((markers.flows || []).some((f) => f.startAt != null || f.endAt != null) || markers.startAt != null);
      const hasTriggers = (cfg.flows || []).some((f) => f.start || f.end);
      if (!hasSaved && hasTriggers) detectMarkers();
    }, [replayerReady]);

    const saveMarkers = useCallback(async () => {
      setSaving(true);
      try {
        const body = {
          startAt: markers.startAt ?? null,
          endAt: markers.endAt ?? null,
          flows: (markers.flows || []).map((f) => ({
            id: f.id, startAt: f.startAt ?? null, endAt: f.endAt ?? null,
            startAuto: f.startAuto ?? null, endAuto: f.endAuto ?? null, overridden: !!f.overridden,
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

    // The rendered prototype rect for the overlay. Reads the ON-SCREEN scaled
    // `.replayer-wrapper` box + the recorded viewport (its unscaled CSS size) so
    // overlay coords (recorded iframe space) map onto the scaled replay. Called
    // from the overlay's rAF (several times per frame), so the wrapper element +
    // frame are CACHED - a querySelector + getBoundingClientRect per call
    // thrashes layout. The fit path / host resize / scroll invalidate the cache;
    // a disconnected wrapper (replayer rebuilt) forces a one-time re-query.
    const getPlayerFrame = useCallback(() => {
      const host = playerHostRef.current;
      if (!host) return null;
      let wrap = wrapRef.current;
      if (!wrap || !wrap.isConnected) {
        wrap = wrapRef.current = host.querySelector(".replayer-wrapper");
        wrapRectRef.current = null;
      }
      if (!wrap) return null;
      let fr = wrapRectRef.current;
      if (!fr) {
        const r = wrap.getBoundingClientRect();  // post-transform, on-screen px
        if (!r.width || !r.height) return null;  // not laid out yet; retry next call
        // Recorded viewport = the wrapper's UNSCALED size. rrweb sets the wrapper's
        // inline width/height (and the iframe matches); fall back to the rendered
        // box divided by the current scale.
        const scale = scaleRef.current || 1;
        const vw = parseFloat(wrap.style.width) || (r.width / scale);
        const vh = parseFloat(wrap.style.height) || (r.height / scale);
        fr = wrapRectRef.current = { left: r.left, top: r.top, width: r.width, height: r.height, vw, vh };
      }
      return fr;
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
            <svg width="16" height="16" viewBox="0 0 834 865" fill="#1c1c1e" aria-hidden="true">
              <path d="M164.411 285.641C196.359 284.677 230.639 291.674 258.864 305.701C275.286 313.727 290.065 324.404 302.52 337.239C341.158 377.583 361.371 447.312 378.116 498.308C388.132 482.744 399.684 467.642 409.951 452.186C412.242 448.739 414.925 444.943 417.595 441.774C431.351 459.34 443.577 480.938 457.207 498.242C472.875 448.395 490.877 391.963 523.907 349.544C579.307 278.402 700.654 264.845 774.789 317.785C806.94 340.863 827.783 375.104 832.598 412.756C843.943 495.181 782.673 564.588 695.92 574.484C644.003 580.405 591.842 563.575 548.833 536.139C539.957 530.476 537.74 518.741 543.151 509.709C548.815 500.254 561.262 497.253 570.658 503.014C601.126 521.693 634.227 536.411 671.754 536.037C705.405 535.7 737.72 524.768 761.424 502.003C781.4 482.798 792.329 456.906 791.766 430.103C791.184 402.032 779.11 377.683 757.679 358.122C705.931 310.886 611.818 317.258 563.019 365.51C553.686 374.887 545.719 385.378 539.322 396.709C524.787 421.893 514.739 451.179 504.773 478.261C499.913 491.473 494.674 506.261 491.301 519.841C489.776 525.958 489.826 533.047 489.985 539.289C493.054 556.978 502.4 565.69 510.272 582.07C534.621 632.717 554.85 688.575 544.486 744.747C537.215 784.135 519.592 821.978 483.663 845.418C457.84 862.041 426.03 868.39 395.209 863.072C363.919 857.517 336.291 840.509 318.457 815.814C307.872 801.34 301.629 787.115 295.942 770.657C275.203 710.66 291.644 652.082 318.36 596.153C322.081 588.342 326.05 580.644 330.262 573.052C340.062 555.493 348.796 545.91 344.696 524.508C342.606 513.599 339.127 503.14 335.6 492.533C322.683 453.678 309.302 413.312 284.963 379.2C243.189 321.492 147.774 309.019 88.4573 349.581C64.3919 366.037 48.2945 389.328 43.7834 417.025C39.4073 443.486 46.4486 470.485 63.3567 492.083C93.1026 529.784 142.471 541.77 190.296 534.226C217.38 529.955 240.84 518.044 262.986 503.814C272.662 497.595 285.65 500.284 291.593 510.132C296.878 518.889 294.7 530.302 286.062 535.779C215.211 580.708 114.661 593.303 48.261 536.056C19.1106 510.632 1.8151 475.501 0.113512 438.245C-1.43994 398.716 12.9754 362.821 41.8772 333.94C73.8144 302.026 118.587 287.315 164.411 285.641ZM416.722 512.527C379.203 567.165 343.362 618.778 329.984 683.963C318.364 740.591 343.994 824.697 418.027 824.976C479.127 823.074 509.74 757.077 506.74 707.2C503.171 647.807 469.774 589.865 436.743 540.45C433.377 535.493 419.886 515.43 416.722 512.527ZM409.73 0.675811C437.369 -2.92606 472.166 8.29862 493.776 24.1416C524.015 46.3095 543.194 80.7427 547.699 116.211C561.045 221.334 486.296 312.27 421.665 390.357L417.78 394.772C405.573 381.446 392.688 364.92 381.071 350.798C336.182 296.042 296.156 233.386 287.029 163.654C279.36 105.059 308.709 39.0645 366.61 11.6826C380.614 5.06005 394.208 2.19545 409.73 0.675811ZM508.772 125.402C503.305 78.2536 464.224 35.4344 409.775 40.9278C348.153 48.2369 319.059 107.407 326.737 160.33C336.002 224.199 376.222 281.983 417.501 331.837L421.652 326.068C465.597 272.347 517.023 196.544 508.772 125.402Z"/>
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

            <!-- Marker tools: auto-derived from each flow's prototype triggers;
                 the tester can nudge a marker to the playhead or clear it. -->
            <div className="rv-markers">
              <div className="rv-marker-group rv-marker-task">
                <span className="rv-marker-label"><${Icon.Flag}/> Task</span>
                <span className="rv-marker-val">${markers.startAt != null ? fmt(markers.startAt) : "·"} → ${markers.endAt != null ? fmt(markers.endAt) : "·"}</span>
                ${taskDuration != null && html`<span className="rv-duration">total ${fmt(taskDuration)}</span>`}
                <button className="rv-mbtn" title="Recompute markers from the prototype triggers" onClick=${reDetect}>Re-detect</button>
              </div>
              ${(cfg.flows || []).length === 0 && html`<div className="rv-marker-hint">No tasks defined for this session.</div>`}
              ${(cfg.flows || []).map((flow) => {
                const fm = flowOf(flow.id);
                const dur = (fm.startAt != null && fm.endAt != null) ? fm.endAt - fm.startAt : null;
                const hasTrig = !!(flow.start || flow.end);
                return html`
                  <div className="rv-marker-group" key=${flow.id}>
                    <span className="rv-marker-label rv-flow-name">${flow.name || flow.id}${fm.overridden ? html`<span className="rv-edited" title="Manually adjusted">edited</span>` : null}</span>
                    <span className="rv-marker-val" title="Task start (auto, from the start trigger)">${fm.startAt != null ? fmt(fm.startAt) : (hasTrig ? "not found" : "·")}
                      <button className="rv-clear" title="Set start to the current playhead" onClick=${() => setFlowEdge(flow.id, "in")}>set</button>
                      ${fm.startAt != null && html`<button className="rv-clear" title="Clear" onClick=${() => clearMarker("flow", flow.id, "in")}>×</button>`}</span>
                    <span className="rv-marker-val" title="Task end (auto, from the end trigger)">${fm.endAt != null ? fmt(fm.endAt) : (hasTrig ? "not found" : "·")}
                      <button className="rv-clear" title="Set end to the current playhead" onClick=${() => setFlowEdge(flow.id, "out")}>set</button>
                      ${fm.endAt != null && html`<button className="rv-clear" title="Clear" onClick=${() => clearMarker("flow", flow.id, "out")}>×</button>`}</span>
                    ${dur != null && html`<span className="rv-duration">${fmt(dur)}</span>`}
                    ${!hasTrig && html`<span className="rv-marker-hint">no trigger set</span>`}
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
              <${TranscriptPanel} transcript=${meta.transcript} onSeek=${seekToMs} fmt=${fmt} playMs=${playMs}/>
              <${AnswerList} questions=${cfg.questions} answers=${meta.answers} rating=${cfg.rating}/>
            </div>
          </div>
        </div>
        ${toast && html`<div className="rv-toast">${toast}</div>`}
      </div>
    `;
  }

  // ── Transcript panel - the voice STT (whisper) segments, click to seek ──
  function TranscriptPanel({ transcript, onSeek, fmt, playMs }) {
    const segs = (transcript && Array.isArray(transcript.segments))
      ? transcript.segments.filter((s) => (s.text || "").trim()) : [];
    const engine = (transcript && transcript.engine) || "";
    const full = (transcript && (transcript.full || "")).trim();
    return html`
      <div className="rv-transcript">
        <div className="rv-side-subhead">Voice transcript
          ${engine && engine !== "none" ? html`<span className="rv-transcript-engine">${engine}</span>` : null}</div>
        ${!transcript && html`<div className="rv-no-answer">Not transcribed yet.</div>`}
        ${transcript && engine === "none" && html`<div className="rv-no-answer">${transcript.note || "No transcription engine available."}</div>`}
        ${transcript && engine !== "none" && segs.length === 0 && html`<div className="rv-no-answer">${full || "No speech detected in the recording."}</div>`}
        ${segs.map((s, i) => {
          const active = playMs != null && s.t0 != null && s.t1 != null && playMs >= s.t0 && playMs < s.t1;
          return html`<button key=${i} type="button"
            className=${"rv-transcript-seg" + (active ? " is-active" : "")}
            onClick=${() => { if (onSeek && s.t0 != null) onSeek(s.t0); }}>
            <span className="rv-transcript-t">${s.t0 != null ? fmt(s.t0) : ""}</span>
            <span className="rv-transcript-text">${s.text}</span>
          </button>`;
        })}
      </div>`;
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
