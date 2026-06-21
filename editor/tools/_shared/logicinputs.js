/* ===========================================================================
   LOGICINPUTS - shared input-capture for the logic graph (W2D).

   Attaches DOM listeners to the render surface and exposes a per-frame
   `sample()` whose shape EXACTLY matches the frame object LogicGraph.tick reads
   (see logicgraph.js: frame.pointer / touch / keyboard / scroll / gyro / audio):

     attach(surfaceEl, opts) -> {
       sample()         -> { pointer, touch, keyboard, scroll, gyro, audio, dt, time },
       requestSensor(k) -> Promise<bool>,   // 'gyro' | 'audio' (mic), gesture-gated
       dispose(),
     }

   Pointer / touch / keyboard / scroll attach immediately (no permission).
   gyro + audio are sensor / device APIs and are requested lazily on a user
   gesture via requestSensor(), behind the LogicPermission overlay (no native
   dialog). Coordinates are normalized 0..1 over the surface. The surface rect is
   CACHED and recomputed only on resize / scroll, never per sample / frame
   (hard project rule: no per-frame getBoundingClientRect).

   `isDown` is the RAW per-frame boolean - the engine edge-detects clicked/tap/
   pressed itself (LogicGraph._rise), so we pass isDown through and also surface a
   `clicked`/`tap` raw boolean for convenience.

   Self-contained sibling of sources.js; any tool iframe can
   `import { LogicInputs } from '../_shared/logicinputs.js'`. Audio extraction
   math (RMS level, autocorrelation pitch, band energy, level-rise beat) mirrors
   the trigger audio feature shape (app.js ~60704: loudness / pitch / band).
   =========================================================================== */

import { LogicPermission } from './logicpermission.js';

function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
function num(v, f) { const n = Number(v); return Number.isFinite(n) ? n : f; }

// Which keys map to the WASD / arrow axes.
const AXIS = {
  left: ['ArrowLeft', 'a', 'A'], right: ['ArrowRight', 'd', 'D'],
  up: ['ArrowUp', 'w', 'W'], down: ['ArrowDown', 's', 'S'],
};

export const LogicInputs = {

  attach(surfaceEl, opts) {
    opts = opts || {};
    const surface = surfaceEl || document.body;

    // ── cached surface rect (recomputed on resize / scroll only) ─────────────
    let rect = { left: 0, top: 0, width: 1, height: 1 };
    const recomputeRect = () => {
      try {
        const r = surface.getBoundingClientRect();
        rect = { left: r.left, top: r.top, width: r.width || 1, height: r.height || 1 };
      } catch (e) {}
    };
    recomputeRect();
    const normX = (clientX) => clamp((clientX - rect.left) / (rect.width || 1), 0, 1);
    const normY = (clientY) => clamp((clientY - rect.top) / (rect.height || 1), 0, 1);

    // ── pointer state ────────────────────────────────────────────────────────
    const pointer = {
      x: 0, y: 0, isDown: false, clicked: false,
      downX: 0, downY: 0, upX: 0, upY: 0, hover: false,
    };
    const buttonFilter = opts.button || (opts.pointerButton) || 'any';  // any|left|right|middle
    const buttonMatch = (e) => {
      if (buttonFilter === 'any') return true;
      if (buttonFilter === 'left') return e.button === 0;
      if (buttonFilter === 'right') return e.button === 2;
      if (buttonFilter === 'middle') return e.button === 1;
      return true;
    };

    const onPointerMove = (e) => { pointer.x = normX(e.clientX); pointer.y = normY(e.clientY); pointer.hover = true; };
    const onPointerDown = (e) => {
      if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;  // touch handled below
      if (!buttonMatch(e)) return;
      pointer.x = normX(e.clientX); pointer.y = normY(e.clientY);
      pointer.isDown = true; pointer.clicked = true;
      pointer.downX = pointer.x; pointer.downY = pointer.y;
    };
    const onPointerUp = (e) => {
      if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
      pointer.isDown = false;
      pointer.upX = normX(e.clientX); pointer.upY = normY(e.clientY);
    };
    const onPointerEnter = () => { pointer.hover = true; };
    const onPointerLeave = () => { pointer.hover = false; };

    // ── touch state (per-touch tracking + pinch / twist) ─────────────────────
    const touchPts = new Map();   // pointerId/identifier -> { x, y }
    const touch = {
      count: 0, pos: { x: 0, y: 0 }, touches: [], isDown: false,
      center: { x: 0, y: 0 }, spread: 0, pinchDelta: 0, rotation: 0, tap: false,
    };
    let lastSpread = 0, baseAngle = null;
    const maxPoints = Math.max(1, Math.floor(num(opts.maxPoints, 10)));

    const recomputeTouch = () => {
      const pts = Array.from(touchPts.values()).slice(0, maxPoints);
      touch.count = pts.length;
      touch.touches = pts.map((p) => ({ x: p.x, y: p.y }));
      touch.isDown = pts.length > 0;
      if (pts.length) {
        let cx = 0, cy = 0;
        for (const p of pts) { cx += p.x; cy += p.y; }
        cx /= pts.length; cy /= pts.length;
        touch.center = { x: cx, y: cy };
        touch.pos = { x: pts[0].x, y: pts[0].y };
      }
      if (pts.length >= 2) {
        const a = pts[0], b = pts[1];
        const dx = b.x - a.x, dy = b.y - a.y;
        const spread = Math.sqrt(dx * dx + dy * dy);
        touch.pinchDelta = spread - (lastSpread || spread);
        touch.spread = spread; lastSpread = spread;
        const angle = Math.atan2(dy, dx);
        if (baseAngle == null) baseAngle = angle;
        touch.rotation = angle - baseAngle;
      } else {
        lastSpread = 0; baseAngle = null; touch.pinchDelta = 0;
        if (!pts.length) { touch.spread = 0; touch.rotation = 0; }
      }
    };
    const onTouchPointerDown = (e) => {
      if (e.pointerType !== 'touch') return;
      touchPts.set(e.pointerId, { x: normX(e.clientX), y: normY(e.clientY) });
      touch.tap = true; recomputeTouch();
    };
    const onTouchPointerMove = (e) => {
      if (e.pointerType !== 'touch' || !touchPts.has(e.pointerId)) return;
      touchPts.set(e.pointerId, { x: normX(e.clientX), y: normY(e.clientY) });
      recomputeTouch();
    };
    const onTouchPointerUp = (e) => {
      if (e.pointerType !== 'touch') return;
      touchPts.delete(e.pointerId); recomputeTouch();
    };

    // ── keyboard state ───────────────────────────────────────────────────────
    const keysDown = new Set();
    const keyboard = { key: '', isDown: false, lastKey: '', axisX: 0, axisY: 0 };
    const recomputeAxes = () => {
      let ax = 0, ay = 0;
      for (const k of AXIS.left) if (keysDown.has(k)) ax -= 1;
      for (const k of AXIS.right) if (keysDown.has(k)) ax += 1;
      for (const k of AXIS.up) if (keysDown.has(k)) ay -= 1;
      for (const k of AXIS.down) if (keysDown.has(k)) ay += 1;
      keyboard.axisX = clamp(ax, -1, 1);
      keyboard.axisY = clamp(ay, -1, 1);
    };
    const onKeyDown = (e) => {
      if (e.repeat && opts.keyboardRepeat === false) return;
      keysDown.add(e.key);
      keyboard.key = e.key; keyboard.lastKey = e.key; keyboard.isDown = true;
      recomputeAxes();
    };
    const onKeyUp = (e) => {
      keysDown.delete(e.key);
      keyboard.isDown = keysDown.size > 0;
      if (keysDown.size) keyboard.key = Array.from(keysDown)[keysDown.size - 1];
      recomputeAxes();
    };

    // ── scroll state ─────────────────────────────────────────────────────────
    const scroll = { deltaX: 0, deltaY: 0, accumX: 0, accumY: 0, velocity: 0 };
    let lastWheel = 0;
    const onWheel = (e) => {
      const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      const dx = e.deltaX, dy = e.deltaY;
      scroll.deltaX = dx; scroll.deltaY = dy;
      scroll.accumX += dx; scroll.accumY += dy;
      const span = Math.max(1, now - lastWheel); lastWheel = now;
      scroll.velocity = dy / span;
    };

    // ── gyro state (lazy, permission-gated) ──────────────────────────────────
    const gyro = { alpha: 0, beta: 0, gamma: 0, tilt: { x: 0, y: 0 }, ready: false };
    const gyroSmoothing = clamp(num(opts.gyroSmoothing, 0.2), 0, 1);
    let gyroListening = false;
    const onOrientation = (e) => {
      const k = gyroSmoothing;
      gyro.alpha = gyro.alpha * k + num(e.alpha, 0) * (1 - k);
      gyro.beta = gyro.beta * k + num(e.beta, 0) * (1 - k);
      gyro.gamma = gyro.gamma * k + num(e.gamma, 0) * (1 - k);
      gyro.tilt = { x: clamp(gyro.beta / 90, -1, 1), y: clamp(gyro.gamma / 90, -1, 1) };
      gyro.ready = true;
    };

    // ── audio state (lazy, permission-gated) ─────────────────────────────────
    const audio = { level: 0, pitch: 0, band: 0, raw: 0, beat: false };
    const audioCfg = {
      band: opts.audioBand || 'full',        // bass | mid | treble | full
      fftSize: Math.max(32, Math.floor(num(opts.audioFftSize, 2048))),
      smoothing: clamp(num(opts.audioSmoothing, 0.8), 0, 1),
    };
    let audioCtx = null, analyser = null, micStream = null, freqBuf = null, timeBuf = null;
    let beatPrevLevel = 0;
    const sampleAudio = () => {
      if (!analyser) return;
      analyser.getByteFrequencyData(freqBuf);
      analyser.getByteTimeDomainData(timeBuf);
      // RMS loudness 0..1 from the time-domain waveform.
      let sum = 0;
      for (let i = 0; i < timeBuf.length; i++) { const v = (timeBuf[i] - 128) / 128; sum += v * v; }
      const level = Math.sqrt(sum / timeBuf.length);
      audio.raw = level;
      audio.level = clamp(level * 1.8, 0, 1);  // gentle gain so quiet rooms still read
      // Band energy (averaged frequency bins for the selected band).
      const N = freqBuf.length;
      let lo = 0, hi = N;
      if (audioCfg.band === 'bass') { lo = 0; hi = Math.floor(N * 0.08); }
      else if (audioCfg.band === 'mid') { lo = Math.floor(N * 0.08); hi = Math.floor(N * 0.4); }
      else if (audioCfg.band === 'treble') { lo = Math.floor(N * 0.4); hi = N; }
      let bsum = 0, bcount = 0;
      for (let i = lo; i < hi; i++) { bsum += freqBuf[i]; bcount++; }
      audio.band = bcount ? clamp((bsum / bcount) / 255, 0, 1) : 0;
      // Autocorrelation pitch estimate (Hz) from the time-domain buffer.
      audio.pitch = audioCtx ? autoCorrelate(timeBuf, audioCtx.sampleRate) : 0;
      // Beat = a sharp rise in level above the running floor.
      audio.beat = (audio.level - beatPrevLevel) > 0.12 && audio.level > 0.15;
      beatPrevLevel = beatPrevLevel * 0.86 + audio.level * 0.14;
    };

    // ── attach the gesture-free listeners now ────────────────────────────────
    const passive = { passive: true };
    surface.addEventListener('pointermove', onPointerMove, passive);
    surface.addEventListener('pointerdown', onPointerDown, passive);
    window.addEventListener('pointerup', onPointerUp, passive);
    surface.addEventListener('pointerenter', onPointerEnter, passive);
    surface.addEventListener('pointerleave', onPointerLeave, passive);
    surface.addEventListener('pointerdown', onTouchPointerDown, passive);
    surface.addEventListener('pointermove', onTouchPointerMove, passive);
    window.addEventListener('pointerup', onTouchPointerUp, passive);
    window.addEventListener('pointercancel', onTouchPointerUp, passive);
    // Keyboard: make surface focusable so it can receive key events directly.
    try { if (surface.tabIndex < 0) surface.tabIndex = 0; } catch (e) {}
    surface.addEventListener('keydown', onKeyDown);
    surface.addEventListener('keyup', onKeyUp);
    surface.addEventListener('wheel', onWheel, passive);
    window.addEventListener('resize', recomputeRect, passive);
    window.addEventListener('scroll', recomputeRect, passive);

    // ── per-frame dt / time clock ────────────────────────────────────────────
    let lastTime = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const startTime = lastTime;

    // ── public handle ────────────────────────────────────────────────────────
    let disposed = false;

    const sample = () => {
      const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      const dt = Math.max(0, (now - lastTime) / 1000);
      lastTime = now;
      if (analyser) sampleAudio();
      const snap = {
        pointer: {
          x: pointer.x, y: pointer.y, isDown: pointer.isDown, clicked: pointer.clicked,
          downX: pointer.downX, downY: pointer.downY, upX: pointer.upX, upY: pointer.upY,
          hover: pointer.hover,
        },
        touch: {
          count: touch.count, pos: { x: touch.pos.x, y: touch.pos.y },
          touches: touch.touches.map((p) => ({ x: p.x, y: p.y })),
          isDown: touch.isDown, center: { x: touch.center.x, y: touch.center.y },
          spread: touch.spread, pinchDelta: touch.pinchDelta, rotation: touch.rotation, tap: touch.tap,
        },
        keyboard: {
          key: keyboard.key, lastKey: keyboard.lastKey, isDown: keyboard.isDown,
          axisX: keyboard.axisX, axisY: keyboard.axisY,
        },
        scroll: {
          deltaX: scroll.deltaX, deltaY: scroll.deltaY,
          accumX: scroll.accumX, accumY: scroll.accumY, velocity: scroll.velocity,
        },
        gyro: { alpha: gyro.alpha, beta: gyro.beta, gamma: gyro.gamma, tilt: { x: gyro.tilt.x, y: gyro.tilt.y }, ready: gyro.ready },
        audio: { level: audio.level, pitch: audio.pitch, band: audio.band, raw: audio.raw, beat: audio.beat },
        dt: dt, time: (now - startTime) / 1000,
      };
      // Per-frame edge flags reset AFTER the snapshot is read (engine reads the raw
      // isDown and edge-detects itself; these are convenience raw pulses).
      pointer.clicked = false;
      touch.tap = false;
      scroll.deltaX = 0; scroll.deltaY = 0;
      return snap;
    };

    const requestSensor = (kind) => {
      if (kind === 'gyro') return requestGyro();
      if (kind === 'audio' || kind === 'mic') return requestAudio();
      return Promise.resolve(false);
    };

    function requestGyro() {
      if (gyroListening) return Promise.resolve(true);
      const start = () => {
        window.addEventListener('deviceorientation', onOrientation, true);
        gyroListening = true;
      };
      // iOS 13+ requires an explicit permission call from a user gesture.
      const needsPerm = typeof DeviceOrientationEvent !== 'undefined' &&
        typeof DeviceOrientationEvent.requestPermission === 'function';
      if (!needsPerm) {
        // Non-iOS: still show our overlay so it's a clear, gesture-anchored opt-in.
        return LogicPermission.requestGesture({
          title: 'Use device motion',
          body: 'This piece reacts to how you tilt your device.',
          allowLabel: 'Enable motion',
        }, () => { start(); return true; }).then((v) => !!v);
      }
      return LogicPermission.requestGesture({
        title: 'Use device motion',
        body: 'This piece reacts to how you tilt your device. Your browser will ask next.',
        allowLabel: 'Enable motion',
      }, () => DeviceOrientationEvent.requestPermission()).then((res) => {
        if (res === 'granted') { start(); return true; }
        return false;
      }).catch(() => false);
    }

    function requestAudio() {
      if (analyser) return Promise.resolve(true);
      return LogicPermission.requestGesture({
        title: 'Use the microphone',
        body: 'This piece reacts to sound. Your browser will ask for mic access next.',
        allowLabel: 'Enable microphone',
      }, () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('no getUserMedia');
        return navigator.mediaDevices.getUserMedia({ audio: true });
      }).then((stream) => {
        if (!stream || stream === true) return false;
        try {
          micStream = stream;
          const AC = window.AudioContext || window.webkitAudioContext;
          audioCtx = new AC();
          analyser = audioCtx.createAnalyser();
          analyser.fftSize = audioCfg.fftSize;
          analyser.smoothingTimeConstant = audioCfg.smoothing;
          freqBuf = new Uint8Array(analyser.frequencyBinCount);
          timeBuf = new Uint8Array(analyser.fftSize);
          const src = audioCtx.createMediaStreamSource(stream);
          src.connect(analyser);
          return true;
        } catch (e) { return false; }
      }).catch(() => false);
    }

    const dispose = () => {
      if (disposed) return; disposed = true;
      surface.removeEventListener('pointermove', onPointerMove, passive);
      surface.removeEventListener('pointerdown', onPointerDown, passive);
      window.removeEventListener('pointerup', onPointerUp, passive);
      surface.removeEventListener('pointerenter', onPointerEnter, passive);
      surface.removeEventListener('pointerleave', onPointerLeave, passive);
      surface.removeEventListener('pointerdown', onTouchPointerDown, passive);
      surface.removeEventListener('pointermove', onTouchPointerMove, passive);
      window.removeEventListener('pointerup', onTouchPointerUp, passive);
      window.removeEventListener('pointercancel', onTouchPointerUp, passive);
      surface.removeEventListener('keydown', onKeyDown);
      surface.removeEventListener('keyup', onKeyUp);
      surface.removeEventListener('wheel', onWheel, passive);
      window.removeEventListener('resize', recomputeRect, passive);
      window.removeEventListener('scroll', recomputeRect, passive);
      if (gyroListening) { window.removeEventListener('deviceorientation', onOrientation, true); gyroListening = false; }
      if (micStream) { try { micStream.getTracks().forEach((t) => t.stop()); } catch (e) {} micStream = null; }
      if (audioCtx) { try { audioCtx.close(); } catch (e) {} audioCtx = null; }
      analyser = null; freqBuf = null; timeBuf = null;
    };

    return { sample, requestSensor, dispose };
  },
};

// Autocorrelation pitch detector (Hz) over a Uint8 time-domain buffer.
// Returns 0 when no confident pitch is found. Standard ACF approach.
function autoCorrelate(buf, sampleRate) {
  const SIZE = buf.length;
  let rms = 0;
  const f = new Float32Array(SIZE);
  for (let i = 0; i < SIZE; i++) { f[i] = (buf[i] - 128) / 128; rms += f[i] * f[i]; }
  rms = Math.sqrt(rms / SIZE);
  if (rms < 0.01) return 0;  // too quiet to estimate

  let r1 = 0, r2 = SIZE - 1; const thres = 0.2;
  for (let i = 0; i < SIZE / 2; i++) { if (Math.abs(f[i]) < thres) { r1 = i; break; } }
  for (let i = 1; i < SIZE / 2; i++) { if (Math.abs(f[SIZE - i]) < thres) { r2 = SIZE - i; break; } }
  const trimmed = f.slice(r1, r2);
  const n = trimmed.length;
  if (n < 2) return 0;

  const c = new Float32Array(n);
  for (let lag = 0; lag < n; lag++) {
    let s = 0;
    for (let i = 0; i < n - lag; i++) s += trimmed[i] * trimmed[i + lag];
    c[lag] = s;
  }
  let d = 0; while (d < n - 1 && c[d] > c[d + 1]) d++;
  let maxVal = -1, maxPos = -1;
  for (let i = d; i < n; i++) { if (c[i] > maxVal) { maxVal = c[i]; maxPos = i; } }
  if (maxPos <= 0) return 0;
  // Parabolic interpolation around the peak for sub-sample accuracy.
  let T0 = maxPos;
  const x1 = c[maxPos - 1] || 0, x2 = c[maxPos], x3 = c[maxPos + 1] || 0;
  const a = (x1 + x3 - 2 * x2) / 2, b = (x3 - x1) / 2;
  if (a) T0 = maxPos - b / (2 * a);
  return T0 > 0 ? sampleRate / T0 : 0;
}
