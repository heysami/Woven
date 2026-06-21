/* ===========================================================================
   LOGICVISION - shared camera + computer-vision for the logic graph (W2D).

   Owns webcam capture and the two processors (vision-detect via MediaPipe Tasks
   Vision, vision-ocr via tesseract.js). W2C calls frame(handles) once per rAF and
   merges the result into LogicGraph.tick's `inputs.streams` (see logicgraph.js:
   vision-detect reads st.detections[], vision-ocr reads st.ocr):

     LogicVision.requestCamera(opts) -> Promise<streamHandle>   // getUserMedia, gesture-gated
     LogicVision.attachVideo(videoEl) -> streamHandle           // a wired <video> as a source
     LogicVision.detect(handle, { detector, target }) -> { present,count,pos,region,gesture,confidence }
     LogicVision.ocr(handle, { query, interval })    -> { text, matched, region, count }
     LogicVision.frame(handles) -> { '<handle>': { detections:[{x,y,w,h,confidence,gesture}], ocr:{text,words} } }
     LogicVision.dispose()

   A handle is an opaque string id; either a camera OR a wired video element can
   feed either detect or ocr. detect() / ocr() REGISTER intent (which detector,
   which throttle) and return the latest cached result; the heavy work runs
   frame-rate-limited inside frame(). All bboxes / centroids are normalized 0..1.

   CDN loads are LAZY (only when a camera / detector / ocr is actually used) and
   FAIL SOFT: if a CDN is unavailable the processor returns empty detections /
   empty text and NEVER throws, so the graph keeps ticking.

   Self-contained sibling of sources.js; any tool iframe can
   `import { LogicVision } from '../_shared/logicvision.js'`.
   =========================================================================== */

import { LogicPermission } from './logicpermission.js';

// ── CDN endpoints (pinned). All optional - the module fails soft if any 404s. ──
const CDN = {
  // MediaPipe Tasks Vision ESM bundle + its wasm/model asset roots.
  mpVision: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs',
  mpWasm: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm',
  faceModel: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
  handModel: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
  objectModel: 'https://storage.googleapis.com/mediapipe-models/object_detector/efdetlite0/int8/1/efdetlite0.tflite',
  // tesseract.js UMD build (loaded via <script>, exposes window.Tesseract).
  tesseract: 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js',
};

const DETECT_INTERVAL_MS = 66;   // ~15fps cap for MediaPipe inference
const num = (v, f) => { const n = Number(v); return Number.isFinite(n) ? n : f; };
const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

// Lazy script loader (one promise per URL). Resolves false on failure (fail-soft).
const _scriptCache = new Map();
function loadScript(url) {
  if (_scriptCache.has(url)) return _scriptCache.get(url);
  const p = new Promise((resolve) => {
    try {
      const s = document.createElement('script');
      s.src = url; s.async = true;
      s.onload = () => resolve(true);
      s.onerror = () => resolve(false);
      document.head.appendChild(s);
    } catch (e) { resolve(false); }
  });
  _scriptCache.set(url, p);
  return p;
}

// Lazy ESM import (fail-soft). Uses a dynamic import so it stays build-less.
const _esmCache = new Map();
function loadEsm(url) {
  if (_esmCache.has(url)) return _esmCache.get(url);
  const p = import(/* @vite-ignore */ url).then((m) => m).catch(() => null);
  _esmCache.set(url, p);
  return p;
}

export const LogicVision = {

  _streams: {},     // handle -> { kind:'camera'|'video', el, stream, t, playing }
  _detect: {},      // handle -> { detector, target, last, result, busy }
  _ocr: {},         // handle -> { query, interval, last, result, busy }
  _mp: null,        // resolved MediaPipe vision namespace (or false)
  _mpTasks: {},     // detector -> task instance (or null)
  _tess: null,      // resolved Tesseract worker (or false)
  _nextId: 1,

  // ── camera (getUserMedia, gesture-gated) ─────────────────────────────────--
  requestCamera(opts) {
    opts = opts || {};
    const res = opts.resolution || 'medium';
    const dim = res === 'low' ? { width: 320, height: 240 } : res === 'high' ? { width: 1280, height: 720 } : { width: 640, height: 480 };
    const constraints = {
      audio: false,
      video: {
        facingMode: opts.facing === 'environment' ? 'environment' : 'user',
        width: { ideal: dim.width }, height: { ideal: dim.height },
      },
    };
    return LogicPermission.requestGesture({
      title: 'Use the camera',
      body: 'This piece reacts to the camera. Your browser will ask for camera access next.',
      allowLabel: 'Enable camera',
    }, () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('no getUserMedia');
      return navigator.mediaDevices.getUserMedia(constraints);
    }).then((stream) => {
      if (!stream || stream === true) return null;
      const handle = 'cam_' + (this._nextId++);
      const video = document.createElement('video');
      video.autoplay = true; video.muted = true; video.playsInline = true;
      try { video.srcObject = stream; } catch (e) {}
      const playing = video.play();
      if (playing && playing.catch) playing.catch(() => {});
      this._streams[handle] = { kind: 'camera', el: video, stream: stream, t: 0, playing: true };
      return handle;
    }).catch(() => null);
  },

  // ── wired <video> element as a stream source (no permission) ───────────────-
  attachVideo(videoEl) {
    if (!videoEl) return null;
    const handle = 'vid_' + (this._nextId++);
    this._streams[handle] = { kind: 'video', el: videoEl, stream: null, t: 0, playing: !videoEl.paused };
    return handle;
  },

  // ── register a detection processor; returns latest cached result ───────────-
  detect(handle, opts) {
    opts = opts || {};
    if (handle == null) return emptyDetect();
    let rec = this._detect[handle];
    if (!rec) { rec = this._detect[handle] = { detector: 'face', target: 'present', last: 0, result: emptyDetect(), busy: false }; }
    rec.detector = opts.detector || rec.detector || 'face';
    rec.target = opts.target || rec.target || 'present';
    return rec.result;
  },

  // ── register an OCR processor; returns latest cached result ─────────────────
  ocr(handle, opts) {
    opts = opts || {};
    if (handle == null) return emptyOcr();
    let rec = this._ocr[handle];
    if (!rec) { rec = this._ocr[handle] = { query: '', interval: 500, last: 0, result: emptyOcr(), busy: false }; }
    rec.query = opts.query != null ? String(opts.query) : rec.query;
    rec.interval = Math.max(50, num(opts.interval, rec.interval || 500));
    return rec.result;
  },

  // ── per-rAF pump: run frame-limited inference, return streams map ───────────-
  // Returns { '<handle>': { detections, ocr } } shaped exactly as logicgraph.js
  // reads (st.detections[] for vision-detect, st.ocr for vision-ocr).
  frame(handles) {
    const out = {};
    const list = handles && handles.length ? handles : Object.keys(this._streams);
    const t = now();

    for (const handle of list) {
      const st = this._streams[handle];
      const entry = { detections: [], ocr: { text: '', words: [] }, t: 0, playing: false };
      if (st && st.el) {
        entry.t = num(st.el.currentTime, 0);
        entry.playing = !st.el.paused;
        st.t = entry.t; st.playing = entry.playing;
      }

      const dRec = this._detect[handle];
      if (dRec) {
        if (!dRec.busy && (t - dRec.last) >= DETECT_INTERVAL_MS && st && st.el) {
          dRec.last = t; dRec.busy = true;
          this._runDetect(st.el, dRec).then((r) => { dRec.result = r; dRec.busy = false; }).catch(() => { dRec.busy = false; });
        }
        entry.detections = (dRec.result && dRec.result._dets) || [];
      }

      const oRec = this._ocr[handle];
      if (oRec) {
        if (!oRec.busy && (t - oRec.last) >= oRec.interval && st && st.el) {
          oRec.last = t; oRec.busy = true;
          this._runOcr(st.el, oRec).then((r) => { oRec.result = r; oRec.busy = false; }).catch(() => { oRec.busy = false; });
        }
        entry.ocr = (oRec.result && oRec.result._ocr) || { text: '', words: [] };
      }

      out[handle] = entry;
    }
    return out;
  },

  // ── MediaPipe detection (lazy, fail-soft) ──────────────────────────────────-
  _runDetect(videoEl, rec) {
    return this._ensureMp(rec.detector).then((task) => {
      if (!task || !videoEl || !videoEl.videoWidth) return emptyDetect();
      const ts = now();
      let raw;
      try { raw = task.detectForVideo(videoEl, ts); }
      catch (e) { return emptyDetect(); }
      return normalizeMpResult(rec.detector, raw, videoEl);
    }).catch(() => emptyDetect());
  },

  _ensureMp(detector) {
    if (this._mp === false) return Promise.resolve(null);
    const ready = this._mp ? Promise.resolve(this._mp) : loadEsm(CDN.mpVision).then((mod) => {
      if (!mod || !mod.FilesetResolver) { this._mp = false; return null; }
      this._mp = mod; return mod;
    });
    return ready.then((mod) => {
      if (!mod) return null;
      if (this._mpTasks[detector] !== undefined) return this._mpTasks[detector];
      this._mpTasks[detector] = null;  // mark in-flight (avoids double init)
      return mod.FilesetResolver.forVisionTasks(CDN.mpWasm).then((fileset) => {
        const baseFor = (url) => ({ baseOptions: { modelAssetPath: url, delegate: 'GPU' }, runningMode: 'VIDEO' });
        let create;
        if (detector === 'hand') create = mod.HandLandmarker.createFromOptions(fileset, Object.assign(baseFor(CDN.handModel), { numHands: 4 }));
        else if (detector === 'object') create = mod.ObjectDetector.createFromOptions(fileset, Object.assign(baseFor(CDN.objectModel), { scoreThreshold: 0.4, maxResults: 8 }));
        else create = mod.FaceLandmarker.createFromOptions(fileset, Object.assign(baseFor(CDN.faceModel), { numFaces: 4, outputFaceBlendshapes: false }));
        return create.then((task) => { this._mpTasks[detector] = task; return task; });
      }).catch(() => { this._mpTasks[detector] = null; return null; });
    }).catch(() => null);
  },

  // ── tesseract OCR (lazy, fail-soft) ────────────────────────────────────────-
  _runOcr(videoEl, rec) {
    return this._ensureTess().then((worker) => {
      if (!worker || !videoEl || !videoEl.videoWidth) return emptyOcr();
      const w = videoEl.videoWidth, h = videoEl.videoHeight;
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const cx = cv.getContext('2d');
      try { cx.drawImage(videoEl, 0, 0, w, h); } catch (e) { return emptyOcr(); }
      return worker.recognize(cv).then((res) => normalizeOcr(res, w, h)).catch(() => emptyOcr());
    }).catch(() => emptyOcr());
  },

  _ensureTess() {
    if (this._tess === false) return Promise.resolve(null);
    if (this._tess) return Promise.resolve(this._tess);
    return loadScript(CDN.tesseract).then((ok) => {
      if (!ok || !window.Tesseract || !window.Tesseract.createWorker) { this._tess = false; return null; }
      return window.Tesseract.createWorker('eng').then((worker) => { this._tess = worker; return worker; })
        .catch(() => { this._tess = false; return null; });
    }).catch(() => { this._tess = false; return null; });
  },

  // ── teardown ───────────────────────────────────────────────────────────────
  dispose() {
    for (const h in this._streams) {
      const st = this._streams[h];
      if (st && st.stream) { try { st.stream.getTracks().forEach((t) => t.stop()); } catch (e) {} }
      if (st && st.el && st.kind === 'camera') { try { st.el.srcObject = null; } catch (e) {} }
    }
    for (const d in this._mpTasks) { const task = this._mpTasks[d]; if (task && task.close) { try { task.close(); } catch (e) {} } }
    if (this._tess && this._tess.terminate) { try { this._tess.terminate(); } catch (e) {} }
    this._streams = {}; this._detect = {}; this._ocr = {}; this._mpTasks = {};
  },
};

// ── result shaping helpers ───────────────────────────────────────────────────
function emptyDetect() { const r = { present: false, count: 0, pos: { x: 0, y: 0 }, region: { x: 0, y: 0, w: 0, h: 0 }, gesture: '', confidence: 0 }; r._dets = []; return r; }
function emptyOcr() { const r = { text: '', matched: false, region: { x: 0, y: 0, w: 0, h: 0 }, count: 0 }; r._ocr = { text: '', words: [] }; return r; }

// Convert a MediaPipe result into the normalized detections[] the engine reads
// ({x,y,w,h,confidence,gesture}) plus a flattened summary for direct callers.
function normalizeMpResult(detector, raw, videoEl) {
  const dets = [];
  if (detector === 'object' && raw && raw.detections) {
    const W = videoEl.videoWidth || 1, H = videoEl.videoHeight || 1;
    for (const d of raw.detections) {
      const bb = d.boundingBox; if (!bb) continue;
      const x = bb.originX / W, y = bb.originY / H, w = bb.width / W, h = bb.height / H;
      const cat = (d.categories && d.categories[0]) || {};
      dets.push({ x: x + w / 2, y: y + h / 2, w: w, h: h, confidence: num(cat.score, 0), gesture: String(cat.categoryName || '') });
    }
  } else if (detector === 'hand' && raw && raw.landmarks) {
    for (let i = 0; i < raw.landmarks.length; i++) {
      const lm = raw.landmarks[i];
      const bb = bboxOfLandmarks(lm);
      const handed = (raw.handednesses && raw.handednesses[i] && raw.handednesses[i][0]) || {};
      // Per-landmark points (21 normalized {x,y}) + named fingertip convenience
      // points so apps can draw between individual fingers (see logicgraph.js
      // vision-detect: it reads first.landmarks / first.<namedPoint>).
      const pts = normalizedLandmarks(lm);
      dets.push({
        x: bb.cx, y: bb.cy, w: bb.w, h: bb.h,
        confidence: num(handed.score, 1), gesture: classifyHand(lm),
        landmarks: pts,
        wrist: pts[0] || null, thumbTip: pts[4] || null, indexTip: pts[8] || null,
        middleTip: pts[12] || null, ringTip: pts[16] || null, pinkyTip: pts[20] || null,
      });
    }
  } else if (detector === 'face' && raw && raw.faceLandmarks) {
    for (const lm of raw.faceLandmarks) {
      const bb = bboxOfLandmarks(lm);
      // FaceLandmarker emits 478 mesh points; expose a few named convenience
      // points (canonical mesh indices) so apps can read nose / eyes directly.
      const pts = normalizedLandmarks(lm);
      dets.push({
        x: bb.cx, y: bb.cy, w: bb.w, h: bb.h, confidence: 1, gesture: '',
        landmarks: pts,
        nose: pts[1] || null, leftEye: pts[33] || null, rightEye: pts[263] || null,
      });
    }
  }
  const first = dets[0] || null;
  const r = {
    present: dets.length > 0, count: dets.length,
    pos: first ? { x: first.x, y: first.y } : { x: 0, y: 0 },
    region: first ? { x: first.x - first.w / 2, y: first.y - first.h / 2, w: first.w, h: first.h } : { x: 0, y: 0, w: 0, h: 0 },
    gesture: first ? first.gesture : '', confidence: first ? first.confidence : 0,
  };
  r._dets = dets;
  return r;
}

// Copy a MediaPipe landmark list into a plain normalized [{x,y}] array (each
// coord clamped to 0..1; z dropped). Fail-soft: returns [] for a bad input.
function normalizedLandmarks(lm) {
  if (!Array.isArray(lm)) return [];
  const out = [];
  for (const p of lm) {
    if (!p) { out.push({ x: 0, y: 0 }); continue; }
    out.push({ x: clamp01(num(p.x, 0)), y: clamp01(num(p.y, 0)) });
  }
  return out;
}
function clamp01(n) { return n < 0 ? 0 : (n > 1 ? 1 : n); }

// Normalized bbox + centroid of a landmark list (each {x,y} already 0..1).
function bboxOfLandmarks(lm) {
  let minX = 1, minY = 1, maxX = 0, maxY = 0;
  for (const p of lm) { if (p.x < minX) minX = p.x; if (p.y < minY) minY = p.y; if (p.x > maxX) maxX = p.x; if (p.y > maxY) maxY = p.y; }
  const w = Math.max(0, maxX - minX), h = Math.max(0, maxY - minY);
  return { cx: minX + w / 2, cy: minY + h / 2, w: w, h: h };
}

// Cheap open/closed/point heuristic from hand landmarks (no extra model).
function classifyHand(lm) {
  if (!lm || lm.length < 21) return '';
  const tipIds = [8, 12, 16, 20], pipIds = [6, 10, 14, 18];
  let extended = 0;
  for (let i = 0; i < tipIds.length; i++) { if (lm[tipIds[i]].y < lm[pipIds[i]].y) extended++; }
  const indexUp = lm[8].y < lm[6].y;
  if (extended === 0) return 'fist';
  if (extended >= 4) return 'open';
  if (extended === 1 && indexUp) return 'point';
  return 'partial';
}

// Convert a tesseract result into { text, matched, region, count } plus the raw
// words[] (normalized bbox) the engine reads via st.ocr.words.
function normalizeOcr(res, w, h) {
  const data = (res && res.data) || {};
  const text = (data.text || '').trim();
  const rawWords = Array.isArray(data.words) ? data.words : [];
  const words = rawWords.map((wd) => {
    const b = wd.bbox || {};
    return {
      text: String(wd.text || ''),
      bbox: { x: num(b.x0, 0) / w, y: num(b.y0, 0) / h, w: (num(b.x1, 0) - num(b.x0, 0)) / w, h: (num(b.y1, 0) - num(b.y0, 0)) / h },
    };
  });
  const r = {
    text: text, matched: false, count: words.length,
    region: words.length ? words[0].bbox : { x: 0, y: 0, w: 0, h: 0 },
  };
  r._ocr = { text: text, words: words };
  return r;
}
