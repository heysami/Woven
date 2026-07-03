/* Woven User-Testing TESTEE RECORDING RUNTIME - the page a study participant
   ("testee") sees at /t/<token>/. Served by the user-testing GATE (the gate
   server that resolves the token via editor/usertesting.py::resolve_token),
   never by the main daemon. Hosts the prototype in a SAME-ORIGIN iframe and
   RECORDS the full session (DOM/screen via rrweb, cursor, microphone audio,
   webcam gaze via webgazer) plus collects task answers + a numeric rating,
   uploading everything in append-chunks before finalizing.

   ───────────────────────────────────────────────────────────────────────────
   SELF-REVIEW - the exact gate API this runtime calls (server author conforms)
   ───────────────────────────────────────────────────────────────────────────
   All urls are RELATIVE to this page's own base (location.pathname is
   "/t/<token>/", so the gate sees e.g. "api/meta", "api/chunk?stream=rrweb").

   GET  api/meta
        -> { sessionLabel, prototype, entry, config, participant, status }
           entry     : prototype iframe src, relative (e.g.
                       "p/source/<slug>/index.html").
           config    : { flows:[{id,name,tasks:[str]}],
                         questions:[{id, at, kind, prompt, choices?, min?, max?}],
                         rating:{enabled?,min,max,label},
                         recording:{rrweb,cursor,audio,gaze} }
           participant : { id, name }
           status    : participant lifecycle string ("invited" | ...).

   POST api/begin    Content-Type application/json
        body { t0:<epoch-ms int>, device:{ ua, dpr, screenW, screenH,
                                           viewportW, viewportH, lang, tz } }
        -> { ok, meta }
        Called ONCE when the testee presses Start (after calibration +
        permissions). t0 == Date.now() at record start; it is the epoch-ms
        origin every per-stream `t` is measured from.

   POST api/chunk?stream=<rrweb|cursor|gaze|audio>&seq=<n>
        TEXT streams (rrweb|cursor|gaze):
            Content-Type text/plain
            body = raw newline-delimited JSON TEXT. Append semantics. Each POST
            is kept UNDER 16MB by the client (events flushed every ~3s / ~64
            events; oversize single payloads are sliced).
            line shapes:
              rrweb  : one native rrweb event object per line, its own
                       `timestamp` (epoch ms) kept AS-IS (NOT rebased).
              cursor : {t, x, y, type}   t = Date.now()-t0 (ms), x/y in the
                       iframe viewport coordinate space, type in
                       {"move","down","up"}.
              gaze   : {t, x, y, conf}   t = Date.now()-t0 (ms), x/y in screen
                       px (webgazer space), conf in [0,1] or null.
        AUDIO stream:
            Content-Type application/octet-stream
            body = raw webm BYTES (one MediaRecorder dataavailable Blob).
            Append semantics; concatenation yields one continuous audio.webm.
        seq increments per stream, starting at 0.
        -> { ok, size }

   POST api/answers  Content-Type application/json
        body { answers:[{questionId, value}], rating:<number|null> }
        -> { ok }

   POST api/finalize Content-Type application/json
        body { durationMs:<int> }   durationMs == Date.now()-t0 at finish.
        -> { ok }
        Called LAST.

   Assumptions the server side must honor:
   - The page is served at "/t/<token>/" with a TRAILING slash so relative urls
     resolve under the token base; the gate 301s the slash-less form.
   - The prototype files are served same-origin under the page base at
     `entry` (and sibling pages), so rrweb captures the iframe inline and we
     can read iframe.contentDocument for cursor coords.
   - chunk POSTs may arrive out of nothing-buffered order only within the
     last in-flight flush; we send them sequentially per stream so append
     order == seq order.
*/

/* global React, ReactDOM, htm, rrweb, webgazer */
(() => {
  const html = htm.bind(React.createElement);
  const { useState, useEffect, useRef, useCallback } = React;

  // ── URL plumbing ─────────────────────────────────────────────────────────
  // location.pathname is "/t/<token>/" (gate 301s the slash-less form).
  const BASE = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  const api = (p) => BASE + "api/" + p;

  const MAX_CHUNK_BYTES = 15 * 1024 * 1024;   // stay safely under the 16MB cap
  const RRWEB_FLUSH_MS = 3000;
  const RRWEB_FLUSH_EVENTS = 64;
  const CURSOR_THROTTLE_MS = 50;
  const GAZE_FLUSH_EVENTS = 40;
  const AUDIO_TIMESLICE_MS = 5000;

  // ── Inline line-icons (currentColor, no emoji) ─────────────────────────────
  const Icon = {
    Mic: ({ size = 16 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
        style=${{ display: "block" }}>
        <rect x="6" y="2" width="4" height="8" rx="2"/><path d="M3.5 7.5a4.5 4.5 0 009 0"/>
        <path d="M8 12v2"/><path d="M6 14h4"/></svg>`,
    Eye: ({ size = 16 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
        style=${{ display: "block" }}>
        <path d="M1.5 8s2.5-4.5 6.5-4.5S14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/>
        <circle cx="8" cy="8" r="2"/></svg>`,
    Screen: ({ size = 16 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
        style=${{ display: "block" }}>
        <rect x="2" y="3" width="12" height="8" rx="1"/><path d="M6 13h4"/><path d="M8 11v2"/></svg>`,
    Check: ({ size = 16 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} fill="none" stroke="currentColor"
        stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
        style=${{ display: "block" }}><path d="M3 8.5L6.5 12L13 4"/></svg>`,
    Dot: ({ size = 16 }) => html`
      <svg viewBox="0 0 16 16" width=${size} height=${size} aria-hidden="true"
        style=${{ display: "block" }}><circle cx="8" cy="8" r="4" fill="currentColor"/></svg>`,
  };

  // ── Recorder - owns all four streams + sequencing. Created on Start. ────────
  // Each stream buffers locally and POSTs sequentially so append order == seq.
  function makeRecorder(t0) {
    const seq = { rrweb: 0, cursor: 0, gaze: 0, audio: 0 };
    // One in-flight tail per stream so chunk POSTs stay ordered without await
    // blocking the recorders.
    const tail = { rrweb: Promise.resolve(), cursor: Promise.resolve(),
                   gaze: Promise.resolve(), audio: Promise.resolve() };

    const postText = (stream, text) => {
      const n = seq[stream]++;
      tail[stream] = tail[stream].then(() =>
        fetch(api("chunk?stream=" + stream + "&seq=" + n), {
          method: "POST",
          headers: { "Content-Type": "text/plain" },
          body: text,
          keepalive: text.length < 60000,
        }).catch(() => {})
      );
      return tail[stream];
    };

    const postBytes = (stream, blob) => {
      const n = seq[stream]++;
      tail[stream] = tail[stream].then(() =>
        fetch(api("chunk?stream=" + stream + "&seq=" + n), {
          method: "POST",
          headers: { "Content-Type": "application/octet-stream" },
          body: blob,
        }).catch(() => {})
      );
      return tail[stream];
    };

    // jsonl text builder that slices to stay under the byte cap.
    const flushLines = (stream, lines) => {
      if (!lines.length) return Promise.resolve();
      let buf = "";
      const sends = [];
      for (const line of lines) {
        const next = buf + line + "\n";
        // Boundary check uses string length (UTF-16 code units) as a cheap
        // proxy for bytes - accurate enough for these JSON event lines,
        // which are overwhelmingly ASCII.
        if (next.length > MAX_CHUNK_BYTES && buf) {
          sends.push(postText(stream, buf));
          buf = line + "\n";
        } else {
          buf = next;
        }
      }
      if (buf) sends.push(postText(stream, buf));
      return Promise.all(sends);
    };

    return { seq, postText, postBytes, flushLines, tail };
  }

  // ── App ────────────────────────────────────────────────────────────────────
  function App() {
    const [meta, setMeta] = useState(null);
    const [metaErr, setMetaErr] = useState(null);
    // phase: loading -> consent -> permissions -> calibrate -> tasks -> done
    const [phase, setPhase] = useState("loading");
    const [permState, setPermState] = useState({ mic: "idle", cam: "idle" });
    const [permErr, setPermErr] = useState(null);
    const [stepIndex, setStepIndex] = useState(0);   // index into the task/question script
    const [answers, setAnswers] = useState({});      // questionId -> value
    const [rating, setRating] = useState(null);
    const [banner, setBanner] = useState(null);

    const iframeRef = useRef(null);
    const t0Ref = useRef(0);
    const recRef = useRef(null);            // makeRecorder()
    const micStreamRef = useRef(null);
    const camStreamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const rrwebStopRef = useRef(null);
    const cursorBufRef = useRef([]);
    const gazeBufRef = useRef([]);
    const gazeValidRef = useRef(0);   // gaze points captured (via polling)
    const gazePollRef = useRef(0);    // getCurrentPrediction() poll interval id
    const [gazeStats, setGazeStats] = useState(null);
    const rrwebBufRef = useRef([]);
    const flushTimerRef = useRef(null);
    const lastCursorRef = useRef(0);
    const cleanupCursorRef = useRef(null);

    const showBanner = (msg) => { setBanner(msg); setTimeout(() => setBanner(null), 5000); };

    // Boot: fetch meta.
    useEffect(() => {
      fetch(api("meta")).then((r) => {
        if (!r.ok) throw new Error("unavailable");
        return r.json();
      }).then((m) => { setMeta(m); setPhase("consent"); })
        .catch(() => setMetaErr("This testing link is no longer available."));
    }, []);

    // ── Build the linear step script from config (flows + placed questions). ──
    // Each step is one of:
    //   {kind:"question", q}              (a single question)
    //   {kind:"flow", flow}               (task instructions for one flow)
    // Order: start-questions, then per flow [flow-questions(before)?, flow,
    // flow-questions(after)?], then end + general questions, then the rating.
    const buildScript = useCallback((cfg) => {
      const qs = (cfg.questions || []);
      const at = (a) => qs.filter((q) => (q.at || "general") === a);
      const flowQs = (fid) => qs.filter((q) => q.at === "flow:" + fid);
      const steps = [];
      for (const q of at("start")) steps.push({ kind: "question", q });
      for (const flow of (cfg.flows || [])) {
        steps.push({ kind: "flow", flow });
        for (const q of flowQs(flow.id)) steps.push({ kind: "question", q });
      }
      for (const q of at("end")) steps.push({ kind: "question", q });
      for (const q of at("general")) steps.push({ kind: "question", q });
      const rcfg = cfg.rating || {};
      if (rcfg.enabled !== false) steps.push({ kind: "rating", rating: rcfg });
      return steps;
    }, []);

    const script = meta ? buildScript(meta.config || {}) : [];

    // ── Device selection (mic + camera) + live mic level meter ────────────────
    const [audioDevices, setAudioDevices] = useState([]);
    const [videoDevices, setVideoDevices] = useState([]);
    const [micId, setMicId] = useState("");
    const [camId, setCamId] = useState("");
    const [micLevel, setMicLevel] = useState(0);      // 0..1 for the meter
    const audioCtxRef = useRef(null);
    const analyserRef = useRef(null);
    const meterRafRef = useRef(0);

    const stopMeter = useCallback(() => {
      try { cancelAnimationFrame(meterRafRef.current); } catch {}
      try { if (audioCtxRef.current) { audioCtxRef.current.close(); audioCtxRef.current = null; } } catch {}
      analyserRef.current = null;
    }, []);
    const startMeter = useCallback((stream) => {
      stopMeter();
      try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        const ctx = new Ctx();
        audioCtxRef.current = ctx;
        const an = ctx.createAnalyser();
        an.fftSize = 512;
        ctx.createMediaStreamSource(stream).connect(an);
        analyserRef.current = an;
        const buf = new Uint8Array(an.fftSize);
        const tick = () => {
          const a = analyserRef.current;
          if (!a) return;
          a.getByteTimeDomainData(buf);
          let sum = 0;
          for (let i = 0; i < buf.length; i++) { const v = (buf[i] - 128) / 128; sum += v * v; }
          setMicLevel(Math.min(1, Math.sqrt(sum / buf.length) * 3.5));  // scale so quiet speech shows
          meterRafRef.current = requestAnimationFrame(tick);
        };
        meterRafRef.current = requestAnimationFrame(tick);
      } catch {}
    }, [stopMeter]);
    const enumerate = useCallback(async () => {
      try {
        const devs = await navigator.mediaDevices.enumerateDevices();
        const ai = devs.filter((d) => d.kind === "audioinput");
        const vi = devs.filter((d) => d.kind === "videoinput");
        setAudioDevices(ai); setVideoDevices(vi);
        return { ai, vi };
      } catch { return { ai: [], vi: [] }; }
    }, []);
    const pickMic = useCallback(async (id) => {
      setMicId(id);
      setPermErr(null);
      try {
        (micStreamRef.current || {}).getTracks?.().forEach((t) => t.stop());
        const mic = await navigator.mediaDevices.getUserMedia({
          audio: id ? { deviceId: { exact: id } } : true });
        micStreamRef.current = mic;
        startMeter(mic);
      } catch (e) {
        setPermErr("Could not open that microphone. Pick another one.");
      }
    }, [startMeter]);
    useEffect(() => () => stopMeter(), [stopMeter]);

    // ── Permissions gate (BLOCKING) ───────────────────────────────────────────
    const requestPermissions = useCallback(async () => {
      setPermErr(null);
      setPermState({ mic: "asking", cam: "asking" });
      // Mic first (its own stream so we can hand it straight to MediaRecorder).
      try {
        const mic = await navigator.mediaDevices.getUserMedia({ audio: true });
        micStreamRef.current = mic;
        setPermState((p) => ({ ...p, mic: "granted" }));
      } catch (e) {
        setPermState((p) => ({ ...p, mic: "denied" }));
        setPermErr("Microphone access is required to record your spoken feedback. "
          + "Allow the microphone in your browser, then try again.");
        return;
      }
      // Camera (gaze is always on for this product; webgazer needs the webcam).
      try {
        const cam = await navigator.mediaDevices.getUserMedia({ video: true });
        camStreamRef.current = cam;
        setPermState((p) => ({ ...p, cam: "granted" }));
      } catch (e) {
        setPermState((p) => ({ ...p, cam: "denied" }));
        setPermErr("Camera access is required for gaze tracking, which this study "
          + "always records. Allow the camera in your browser, then try again.");
        return;
      }
      // Permission granted unlocks device labels - let the testee pick the right
      // microphone (e.g. their headset) and camera, with a live mic meter.
      const { ai, vi } = await enumerate();
      try {
        const ms = micStreamRef.current, cs = camStreamRef.current;
        const at = ms && ms.getAudioTracks && ms.getAudioTracks()[0];
        let mId = (at && at.getSettings && at.getSettings().deviceId) || "";
        if (!ai.some((d) => d.deviceId === mId)) mId = (ai[0] && ai[0].deviceId) || "";
        setMicId(mId);
        const vt = cs && cs.getVideoTracks && cs.getVideoTracks()[0];
        let cId = (vt && vt.getSettings && vt.getSettings().deviceId) || "";
        if (!vi.some((d) => d.deviceId === cId)) cId = (vi[0] && vi[0].deviceId) || "";
        setCamId(cId);
      } catch {}
      startMeter(micStreamRef.current);
      setPhase("devices");
    }, [enumerate, startMeter]);

    // ── Calibration - webgazer + a 9-point click grid ─────────────────────────
    // We start webgazer (it claims the webcam stream itself), hide its video +
    // face overlay, and require the testee to click each of 9 dots a few times
    // so the regression has data. Gaze is NOT skippable.
    const calibPoints = [
      [10, 10], [50, 10], [90, 10],
      [10, 50], [50, 50], [90, 50],
      [10, 90], [50, 90], [90, 90],
    ];
    const CLICKS_PER_POINT = 3;
    const [pointHits, setPointHits] = useState(() => calibPoints.map(() => 0));
    const webgazerReadyRef = useRef(false);
    const [gazeReady, setGazeReady] = useState(false);
    const [gazeTimedOut, setGazeTimedOut] = useState(false);
    const gazeTimeoutRef = useRef(0);

    const startWebgazer = useCallback(async () => {
      if (webgazerReadyRef.current) return;
      try {
        webgazer.setRegression("ridge");
        // webgazer passes params.camConstraints STRAIGHT to getUserMedia, so it
        // MUST be shaped { video: {...} }; a bare { deviceId } throws and kills
        // gaze entirely. deviceId is ideal (not exact) so a busy/odd camera does
        // not hard-fail.
        try {
          if (webgazer.params) {
            const v = { width: { ideal: 640 }, height: { ideal: 480 } };
            if (camId) v.deviceId = camId;
            webgazer.params.camConstraints = { video: v };
          }
        } catch {}
        // Free the permission-check camera stream so webgazer can claim the device.
        try { (camStreamRef.current || {}).getTracks?.().forEach((t) => t.stop()); camStreamRef.current = null; } catch {}
        // Keep the video preview ON (rendering): webgazer extracts eye features
        // from the live <video>. A display:none OR fully off-screen video stops
        // decoding frames -> ZERO gaze, so testee.css keeps the container ON-SCREEN
        // but 1px + near-transparent. Only the cosmetic overlays are turned off.
        webgazer.showVideoPreview(true);
        webgazer.showPredictionPoints(false);
        webgazer.showFaceOverlay(false);
        webgazer.showFaceFeedbackBox(false);
        try {
          await webgazer.begin();
        } catch (e1) {
          // The chosen camera may be unavailable - retry with any camera.
          try { if (webgazer.params) webgazer.params.camConstraints = { video: { width: { ideal: 640 }, height: { ideal: 480 } } }; } catch {}
          await webgazer.begin();
        }
        try { webgazer.showVideoPreview(true); } catch {}
        webgazerReadyRef.current = true;
        // Flip the indicator only on the FIRST REAL gaze prediction - begin()
        // succeeding does NOT mean frames/face are being read. This validation
        // listener is replaced by the recording listener in start().
        try {
          webgazer.setGazeListener((data) => {
            if (data && Number.isFinite(data.x) && Number.isFinite(data.y)) setGazeReady(true);
          });
        } catch {}
        // Don't block forever if gaze never locks on (poor light / odd camera).
        try { clearTimeout(gazeTimeoutRef.current); } catch {}
        gazeTimeoutRef.current = setTimeout(() => setGazeTimedOut(true), 9000);
      } catch (e) {
        setPermErr("Could not start gaze tracking. Make sure the camera is not in "
          + "use by another app, then reload.");
      }
    }, [camId]);

    useEffect(() => {
      if (phase === "calibrate") startWebgazer();
    }, [phase, startWebgazer]);

    const onCalibClick = (i) => {
      setPointHits((prev) => {
        const next = prev.slice();
        next[i] = Math.min(CLICKS_PER_POINT, next[i] + 1);
        return next;
      });
    };
    const calibCount = pointHits.reduce((a, b) => a + b, 0);
    const calibDone = pointHits.every((h) => h >= CLICKS_PER_POINT);

    // ── Start recording ───────────────────────────────────────────────────────
    const start = useCallback(async () => {
      const t0 = Date.now();
      t0Ref.current = t0;
      const rec = makeRecorder(t0);
      recRef.current = rec;

      // 1. begin
      const device = {
        ua: navigator.userAgent,
        dpr: window.devicePixelRatio || 1,
        screenW: screen.width, screenH: screen.height,
        viewportW: window.innerWidth, viewportH: window.innerHeight,
        lang: navigator.language || "",
        tz: (Intl.DateTimeFormat().resolvedOptions().timeZone) || "",
      };
      try {
        await fetch(api("begin"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ t0, device }),
        });
      } catch { /* recording proceeds; begin is best-effort to seed meta */ }

      // 2. rrweb - exclude our own chrome via ut-norecord (block + ignore).
      try {
        rrwebStopRef.current = rrweb.record({
          emit(ev) {
            const buf = rrwebBufRef.current;
            buf.push(ev);
            if (buf.length >= RRWEB_FLUSH_EVENTS) flushRrweb();
          },
          // Capture canvas content (games, shader/polish layers) as periodic
          // IMAGE snapshots, NOT command recording. rrweb's command mode
          // (sampling.canvas "all", the DEFAULT when recordCanvas is just true)
          // wraps the WebGL context methods, which breaks webgazer's TF.js
          // tracker -> estimateFaces throws -> ZERO gaze. The NUMERIC
          // sampling.canvas path uses toDataURL snapshots and leaves the GL
          // context untouched, so canvas replay AND gaze both work.
          recordCanvas: true,
          sampling: { canvas: 2 },
          dataURLOptions: { type: "image/jpeg", quality: 0.6 },
          // Never snapshot webgazer's webcam canvases (privacy + size).
          blockClass: "ut-norecord",
          blockSelector: "[id^='webgazer']",
          ignoreClass: "ut-norecord",
        });
      } catch (e) { showBanner("Screen recording could not start."); }

      // periodic rrweb flush
      flushTimerRef.current = setInterval(flushRrweb, RRWEB_FLUSH_MS);

      // 3. cursor - top document + same-origin iframe document.
      installCursor();

      // 4. gaze. webgazer's setGazeListener callback goes silent once recording
      // starts, so POLL getCurrentPrediction() instead - it computes a fresh
      // {x,y} on demand, independent of webgazer's rAF loop. resume() guards
      // against an auto-pause. (rrweb recordCanvas MUST stay off, above, or the
      // TF.js WebGL tracker throws and this yields nothing.)
      try { if (webgazer.resume) webgazer.resume(); } catch {}
      try { webgazer.showPredictionPoints(false); } catch {}
      try {
        gazePollRef.current = setInterval(async () => {
          // Browsers pause a tiny/occluded <video>; that would freeze the
          // tracker, so keep webgazer's feed decoding.
          try {
            const v = document.getElementById("webgazerVideoFeed");
            if (v && v.paused) await v.play();
          } catch {}
          let p = null;
          try { p = await Promise.resolve(webgazer.getCurrentPrediction()); } catch {}
          if (!p || !Number.isFinite(p.x) || !Number.isFinite(p.y)) return;
          gazeValidRef.current++;
          gazeBufRef.current.push({ t: Date.now() - t0Ref.current, x: Math.round(p.x), y: Math.round(p.y), conf: null });
          if (gazeBufRef.current.length >= GAZE_FLUSH_EVENTS) flushGaze();
        }, 100);
      } catch {}

      // 5. audio - MediaRecorder on the mic stream, timesliced.
      try {
        const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus" : "audio/webm";
        const mr = new MediaRecorder(micStreamRef.current, { mimeType: mime });
        mr.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) rec.postBytes("audio", e.data);
        };
        mr.start(AUDIO_TIMESLICE_MS);
        mediaRecorderRef.current = mr;
      } catch (e) { showBanner("Audio recording could not start."); }

      setPhase("tasks");
      setStepIndex(0);
    }, []);

    // ── Flushers (read refs so they're stable across renders) ─────────────────
    const flushRrweb = useCallback(() => {
      const rec = recRef.current;
      const buf = rrwebBufRef.current;
      if (!rec || !buf.length) return;
      const lines = buf.map((ev) => JSON.stringify(ev));
      rrwebBufRef.current = [];
      rec.flushLines("rrweb", lines);
    }, []);

    const flushCursor = useCallback(() => {
      const rec = recRef.current;
      const buf = cursorBufRef.current;
      if (!rec || !buf.length) return;
      const lines = buf.map((o) => JSON.stringify(o));
      cursorBufRef.current = [];
      rec.flushLines("cursor", lines);
    }, []);

    const flushGaze = useCallback(() => {
      const rec = recRef.current;
      const buf = gazeBufRef.current;
      if (!rec || !buf.length) return;
      const lines = buf.map((o) => JSON.stringify(o));
      gazeBufRef.current = [];
      rec.flushLines("gaze", lines);
    }, []);

    // ── Cursor capture - throttled pointermove on both docs ───────────────────
    const installCursor = useCallback(() => {
      const push = (clientX, clientY, type) => {
        const now = Date.now();
        if (type === "move" && now - lastCursorRef.current < CURSOR_THROTTLE_MS) return;
        lastCursorRef.current = now;
        cursorBufRef.current.push({
          t: now - t0Ref.current,
          x: Math.round(clientX), y: Math.round(clientY),
          type,
        });
        if (cursorBufRef.current.length >= 64) flushCursor();
      };

      // The prototype iframe viewport is the coordinate space we want. For
      // pointer events on the TOP document we offset by the iframe's box so
      // both sources land in the same (iframe-viewport) space.
      const topMove = (e) => {
        const frame = iframeRef.current;
        if (!frame) return push(e.clientX, e.clientY, "move");
        const r = frame.getBoundingClientRect();
        push(e.clientX - r.left, e.clientY - r.top, "move");
      };
      const topDown = (e) => {
        const frame = iframeRef.current;
        const r = frame ? frame.getBoundingClientRect() : { left: 0, top: 0 };
        push(e.clientX - r.left, e.clientY - r.top, "down");
      };
      const topUp = (e) => {
        const frame = iframeRef.current;
        const r = frame ? frame.getBoundingClientRect() : { left: 0, top: 0 };
        push(e.clientX - r.left, e.clientY - r.top, "up");
      };
      document.addEventListener("pointermove", topMove, true);
      document.addEventListener("pointerdown", topDown, true);
      document.addEventListener("pointerup", topUp, true);

      // Iframe document - its clientX/Y are ALREADY in the iframe viewport.
      let idoc = null;
      const iMove = (e) => push(e.clientX, e.clientY, "move");
      const iDown = (e) => push(e.clientX, e.clientY, "down");
      const iUp = (e) => push(e.clientX, e.clientY, "up");
      const attachIframe = () => {
        try {
          const d = iframeRef.current && iframeRef.current.contentDocument;
          if (!d || d === idoc) return;
          idoc = d;
          d.addEventListener("pointermove", iMove, true);
          d.addEventListener("pointerdown", iDown, true);
          d.addEventListener("pointerup", iUp, true);
        } catch { /* cross-origin would throw; same-origin here */ }
      };
      attachIframe();
      const reattach = setInterval(attachIframe, 1000);

      cleanupCursorRef.current = () => {
        clearInterval(reattach);
        document.removeEventListener("pointermove", topMove, true);
        document.removeEventListener("pointerdown", topDown, true);
        document.removeEventListener("pointerup", topUp, true);
        try {
          if (idoc) {
            idoc.removeEventListener("pointermove", iMove, true);
            idoc.removeEventListener("pointerdown", iDown, true);
            idoc.removeEventListener("pointerup", iUp, true);
          }
        } catch {}
      };
    }, [flushCursor]);

    const onFrameLoad = useCallback(() => {
      // Re-attach cursor listeners to the freshly-loaded iframe document.
      if (phase === "tasks" && recRef.current) {
        // installCursor's interval reattaches; nothing else needed here.
      }
    }, [phase]);

    // ── Finish - stop everything, flush, answers, finalize ────────────────────
    const finish = useCallback(async () => {
      const t0 = t0Ref.current;
      // Stop recorders.
      try { if (rrwebStopRef.current) rrwebStopRef.current(); } catch {}
      try { if (flushTimerRef.current) clearInterval(flushTimerRef.current); } catch {}
      try { if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive")
        mediaRecorderRef.current.stop(); } catch {}
      try { webgazer.clearGazeListener(); } catch {}
      try { clearInterval(gazePollRef.current); } catch {}
      try { webgazer.pause(); } catch {}
      try { if (cleanupCursorRef.current) cleanupCursorRef.current(); } catch {}

      // Confirm to the testee (and us) that gaze was captured.
      setGazeStats({ valid: gazeValidRef.current });
      try { console.log("[ut] gaze points captured: " + gazeValidRef.current); } catch {}

      // Flush remaining buffers, then wait for every stream tail to drain.
      flushRrweb(); flushCursor(); flushGaze();
      const rec = recRef.current;
      if (rec) {
        try {
          await Promise.all([rec.tail.rrweb, rec.tail.cursor, rec.tail.gaze, rec.tail.audio]);
        } catch {}
      }

      // Answers.
      try {
        const ans = Object.keys(answers).map((qid) => ({ questionId: qid, value: answers[qid] }));
        await fetch(api("answers"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers: ans, rating }),
        });
      } catch { showBanner("Could not save your answers."); }

      // Finalize.
      try {
        await fetch(api("finalize"), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ durationMs: Date.now() - t0 }),
        });
      } catch {}

      // Release devices.
      try { (micStreamRef.current || {}).getTracks?.().forEach((t) => t.stop()); } catch {}
      try { (camStreamRef.current || {}).getTracks?.().forEach((t) => t.stop()); } catch {}
      try { webgazer.end(); } catch {}

      setPhase("done");
    }, [answers, rating, flushRrweb, flushCursor, flushGaze]);

    // ── Step navigation in the tasks phase ────────────────────────────────────
    const step = script[stepIndex] || null;
    const isLastStep = stepIndex >= script.length - 1;

    const setAnswer = (qid, value) => setAnswers((a) => ({ ...a, [qid]: value }));

    const canAdvance = () => {
      if (!step) return true;
      if (step.kind === "question") {
        // Soft requirement: allow advancing even if blank (testers may skip).
        return true;
      }
      return true;
    };

    const advance = () => {
      if (isLastStep) { finish(); return; }
      setStepIndex((i) => i + 1);
    };

    // ── Renders ───────────────────────────────────────────────────────────────
    if (metaErr) {
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-card ut-center">
          <h1>Link unavailable</h1>
          <p>${metaErr}</p>
        </div>
      </div>`;
    }
    if (!meta) {
      return html`<div className="ut-shell ut-norecord"><div className="ut-card ut-center">
        <p className="ut-muted">Loading your session…</p>
      </div></div>`;
    }

    // The prototype iframe is mounted once we begin recording (phase tasks).
    // Everything else (chrome) is wrapped in ut-norecord so rrweb excludes it.

    // CONSENT
    if (phase === "consent") {
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-card">
          <div className="ut-eyebrow">User testing session</div>
          <h1>${meta.sessionLabel || "Prototype test"}</h1>
          <p>Hi ${(meta.participant && meta.participant.name) || "there"}, thanks for helping
             test this prototype. Before we begin, here is exactly what gets recorded:</p>
          <ul className="ut-consent-list">
            <li><span className="ut-ci"><${Icon.Screen}/></span>
              <div><b>Your screen</b><span>The prototype and how you move through it.</span></div></li>
            <li><span className="ut-ci"><${Icon.Mic}/></span>
              <div><b>Your voice</b><span>Through your microphone, so we hear your thoughts.</span></div></li>
            <li><span className="ut-ci"><${Icon.Eye}/></span>
              <div><b>Your gaze</b><span>Through your webcam, to see where you look. The video is
                used only to estimate gaze and is not saved as video.</span></div></li>
          </ul>
          <p className="ut-muted">Recording starts only after you finish a short camera setup and
             press Start. You can stop at the end by finishing the questions.</p>
          <div className="ut-actions">
            <button className="ut-btn ut-btn-primary" onClick=${() => setPhase("permissions")}>
              I understand, continue</button>
          </div>
        </div>
      </div>`;
    }

    // PERMISSIONS
    if (phase === "permissions") {
      const row = (label, IconC, state) => html`
        <div className=${"ut-perm-row is-" + state}>
          <span className="ut-ci"><${IconC}/></span>
          <div className="ut-perm-label">${label}</div>
          <div className="ut-perm-state">${
            state === "granted" ? html`<${Icon.Check}/> Allowed`
            : state === "denied" ? "Blocked"
            : state === "asking" ? "Requesting…" : "Needed"}</div>
        </div>`;
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-card">
          <div className="ut-eyebrow">Step 1 of 3 · Permissions</div>
          <h1>Allow microphone and camera</h1>
          <p>This study records your voice and your gaze. Your browser will ask for permission
             for each. Both are required to continue.</p>
          <div className="ut-perm-list">
            ${row("Microphone", Icon.Mic, permState.mic)}
            ${row("Camera", Icon.Eye, permState.cam)}
          </div>
          ${permErr && html`<div className="ut-error">${permErr}</div>`}
          <div className="ut-actions">
            <button className="ut-btn ut-btn-primary"
              disabled=${permState.mic === "asking" || permState.cam === "asking"}
              onClick=${requestPermissions}>
              ${permState.mic === "denied" || permState.cam === "denied"
                ? "Try again" : "Allow access"}</button>
          </div>
        </div>
      </div>`;
    }

    // DEVICE SELECTION (mic + camera) - lets a headset user pick the right mic.
    if (phase === "devices") {
      const lvlPct = Math.round(micLevel * 100);
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-card">
          <div className="ut-eyebrow">Step 2 of 3 · Microphone & camera</div>
          <h1>Choose your devices</h1>
          <p>Pick the microphone you will speak into (your headset, if you wear one) and the webcam
             for gaze tracking. Speak now - the bar below should move. If it does not, choose a
             different microphone.</p>
          <div className="ut-dev-field">
            <label className="ut-dev-label"><${Icon.Mic}/> Microphone</label>
            <select className="ut-dev-select" value=${micId} onChange=${(e) => pickMic(e.target.value)}>
              ${audioDevices.map((d, i) => html`<option key=${d.deviceId} value=${d.deviceId}>${d.label || ("Microphone " + (i + 1))}</option>`)}
            </select>
            <div className=${"ut-meter" + (micLevel > 0.06 ? " is-live" : "")}>
              <div className="ut-meter-fill" style=${{ width: lvlPct + "%" }}></div>
            </div>
            <div className="ut-meter-hint">${micLevel > 0.06 ? "Good - your mic is picking up sound." : "Speak to test your microphone."}</div>
          </div>
          <div className="ut-dev-field">
            <label className="ut-dev-label"><${Icon.Eye}/> Camera (for gaze)</label>
            <select className="ut-dev-select" value=${camId} onChange=${(e) => setCamId(e.target.value)}>
              ${videoDevices.map((d, i) => html`<option key=${d.deviceId} value=${d.deviceId}>${d.label || ("Camera " + (i + 1))}</option>`)}
            </select>
          </div>
          ${permErr && html`<div className="ut-error">${permErr}</div>`}
          <div className="ut-actions">
            <button className="ut-btn ut-btn-primary" onClick=${() => { stopMeter(); setPhase("calibrate"); }}>Continue to calibration</button>
          </div>
        </div>
      </div>`;
    }

    // CALIBRATE
    if (phase === "calibrate") {
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-calib-overlay">
          <div className="ut-calib-head">
            <div className="ut-eyebrow">Step 3 of 3 · Calibrate gaze</div>
            <h2>Calibrate gaze tracking</h2>
            <p>Look at each dot and click it ${CLICKS_PER_POINT} times. Keep your head steady and
               your face well lit. ${calibCount} of ${calibPoints.length * CLICKS_PER_POINT} clicks.</p>
            ${permErr && html`<div className="ut-error">${permErr}</div>`}
          </div>
          ${calibPoints.map((p, i) => html`
            <button key=${i}
              className=${"ut-calib-dot" + (pointHits[i] >= CLICKS_PER_POINT ? " is-done" : "")}
              style=${{ left: p[0] + "%", top: p[1] + "%",
                        opacity: 0.35 + 0.65 * (pointHits[i] / CLICKS_PER_POINT) }}
              onClick=${() => onCalibClick(i)}
              aria-label=${"Calibration point " + (i + 1)}></button>
          `)}
          <div className="ut-calib-foot">
            ${gazeReady && html`<span className="ut-gaze-status is-ok"><${Icon.Check}/> Gaze tracking active</span>`}
            ${!gazeReady && !gazeTimedOut && !permErr && html`<span className="ut-gaze-status">Starting gaze tracking…</span>`}
            ${!gazeReady && gazeTimedOut && html`<span className="ut-gaze-status is-warn">Gaze did not lock on. Check lighting/camera - you can still continue.</span>`}
            <button className="ut-btn ut-btn-primary" disabled=${!calibDone || (!gazeReady && !gazeTimedOut)} onClick=${start}>
              Start the test</button>
          </div>
        </div>
      </div>`;
    }

    // DONE
    if (phase === "done") {
      return html`<div className="ut-shell ut-norecord">
        <div className="ut-card ut-center">
          <div className="ut-done-mark"><${Icon.Check} size=${28}/></div>
          <h1>Thank you</h1>
          <p>Your session has been recorded and uploaded. You can close this tab now.</p>
          ${gazeStats && html`<p className="ut-gaze-diag">${gazeStats.valid > 0 ? `Gaze: ${gazeStats.valid} points captured.` : "Gaze tracking produced no usable points during the test."}</p>`}
        </div>
      </div>`;
    }

    // TASKS - prototype iframe + a floating chrome panel (ut-norecord).
    return html`
      <div className="ut-stage">
        <iframe
          ref=${iframeRef}
          className="ut-frame"
          src=${BASE + (meta.entry || "")}
          title="Prototype under test"
          onLoad=${onFrameLoad}
        ></iframe>
        <div className="ut-panel ut-norecord">
          <div className="ut-panel-head">
            <span className="ut-rec-dot" aria-hidden="true"></span>
            <span className="ut-rec-label">Recording</span>
            <span className="ut-step-count">Step ${stepIndex + 1} of ${script.length}</span>
          </div>
          ${step && step.kind === "flow" && html`
            <div className="ut-panel-body">
              <div className="ut-task-name">${step.flow.name || "Task"}</div>
              <ol className="ut-task-list">
                ${(step.flow.tasks || []).map((t, i) => html`<li key=${i}>${t}</li>`)}
              </ol>
              <p className="ut-muted">Try the task in the prototype, thinking aloud. When you are
                 done, continue.</p>
            </div>
          `}
          ${step && step.kind === "question" && html`
            <${QuestionView} q=${step.q} value=${answers[step.q.id]}
              onChange=${(v) => setAnswer(step.q.id, v)} />
          `}
          ${step && step.kind === "rating" && html`
            <${RatingView} cfg=${step.rating} value=${rating} onChange=${setRating} />
          `}
          ${!step && html`<div className="ut-panel-body"><p>Ready to wrap up.</p></div>`}
          <div className="ut-panel-foot">
            <button className="ut-btn ut-btn-primary" disabled=${!canAdvance()} onClick=${advance}>
              ${isLastStep ? "Finish and submit" : "Continue"}</button>
          </div>
        </div>
        ${banner && html`<div className="ut-banner ut-norecord">${banner}</div>`}
      </div>
    `;
  }

  // ── Question renderer ───────────────────────────────────────────────────────
  function QuestionView({ q, value, onChange }) {
    const kind = q.kind || "text";
    return html`
      <div className="ut-panel-body">
        <div className="ut-q-prompt">${q.prompt || "Question"}</div>
        ${kind === "text" && html`
          <textarea className="ut-input ut-textarea" placeholder="Type your answer…"
            value=${value || ""} onInput=${(e) => onChange(e.target.value)}></textarea>`}
        ${kind === "boolean" && html`
          <div className="ut-choice-row">
            ${["Yes", "No"].map((opt) => html`
              <button key=${opt}
                className=${"ut-choice" + (value === opt ? " is-active" : "")}
                onClick=${() => onChange(opt)}>${opt}</button>`)}
          </div>`}
        ${kind === "choice" && html`
          <div className="ut-choice-col">
            ${(q.choices || []).map((opt) => html`
              <button key=${opt}
                className=${"ut-choice" + (value === opt ? " is-active" : "")}
                onClick=${() => onChange(opt)}>${opt}</button>`)}
          </div>`}
        ${kind === "rating" && html`
          <${ScaleRow} min=${q.min != null ? q.min : 1} max=${q.max != null ? q.max : 5}
            value=${value} onChange=${onChange} />`}
      </div>`;
  }

  // ── Final numeric rating ────────────────────────────────────────────────────
  function RatingView({ cfg, value, onChange }) {
    return html`
      <div className="ut-panel-body">
        <div className="ut-q-prompt">${cfg.label || "Overall experience"}</div>
        <${ScaleRow} min=${cfg.min != null ? cfg.min : 1} max=${cfg.max != null ? cfg.max : 5}
          value=${value} onChange=${onChange} />
      </div>`;
  }

  function ScaleRow({ min, max, value, onChange }) {
    const lo = Number(min), hi = Number(max);
    const nums = [];
    for (let n = lo; n <= hi; n++) nums.push(n);
    return html`
      <div className="ut-scale">
        ${nums.map((n) => html`
          <button key=${n}
            className=${"ut-scale-btn" + (value === n ? " is-active" : "")}
            onClick=${() => onChange(n)}>${n}</button>`)}
      </div>`;
  }

  function Root() { return html`<${App}/>`; }
  ReactDOM.createRoot(document.getElementById("root")).render(html`<${Root}/>`);
})();
