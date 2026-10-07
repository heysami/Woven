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
import { createAudioInputs } from './logicaudioinput.js';

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
      buttons: 0, clickedButtons: 0,
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
      const bit = [1, 4, 2][e.button] || 0;
      pointer.buttons = e.buttons == null ? pointer.buttons | bit : e.buttons;
      pointer.clickedButtons |= bit;
      pointer.downX = pointer.x; pointer.downY = pointer.y;
    };
    const onPointerUp = (e) => {
      if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
      pointer.buttons = e.buttons == null ? pointer.buttons & ~([1, 4, 2][e.button] || 0) : e.buttons;
      pointer.isDown = pointer.buttons !== 0;
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
    const pressedKeys = new Set(), repeatKeys = new Set();
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
      (e.repeat ? repeatKeys : pressedKeys).add(e.key);
      keyboard.key = e.key; keyboard.lastKey = e.key; keyboard.isDown = true;
      recomputeAxes();
    };
    const onKeyUp = (e) => {
      keysDown.delete(e.key);
      keyboard.isDown = keysDown.size > 0;
      if (keysDown.size) keyboard.key = Array.from(keysDown)[keysDown.size - 1];
      recomputeAxes();
    };
    const onBlur = () => {
      keysDown.clear(); pressedKeys.clear(); repeatKeys.clear(); keyboard.isDown = false; recomputeAxes();
      pointer.buttons = 0; pointer.isDown = false; pointer.clicked = false; pointer.clickedButtons = 0;
      touchPts.clear(); recomputeTouch();
    };

    // ── scroll state ─────────────────────────────────────────────────────────
    const scroll = { deltaX: 0, deltaY: 0, accumX: 0, accumY: 0, velocity: 0 };
    let lastWheel = 0;
    const onWheel = (e) => {
      const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? rect.height : 1;
      const dx = e.deltaX * unit, dy = e.deltaY * unit;
      scroll.deltaX += dx; scroll.deltaY += dy;
      scroll.accumX += dx; scroll.accumY += dy;
      const span = Math.max(1, now - lastWheel); lastWheel = now;
      scroll.velocity = dy / span;
    };

    // ── gyro state (lazy, permission-gated) ──────────────────────────────────
    const gyro = { alpha: 0, beta: 0, gamma: 0, tilt: { x: 0, y: 0 }, ready: false };
    const gyroSmoothing = clamp(num(opts.gyroSmoothing, 0), 0, 1);
    let gyroListening = false;
    const onOrientation = (e) => {
      const k = gyroSmoothing;
      gyro.alpha = gyro.alpha * k + num(e.alpha, 0) * (1 - k);
      gyro.beta = gyro.beta * k + num(e.beta, 0) * (1 - k);
      gyro.gamma = gyro.gamma * k + num(e.gamma, 0) * (1 - k);
      gyro.tilt = { x: clamp(gyro.beta / 90, -1, 1), y: clamp(gyro.gamma / 90, -1, 1) };
      gyro.ready = true;
    };

    // ── gamepad / accel / midi state (input devices) ─────────────────────────
    const gamepad = { x: 0, y: 0, rx: 0, ry: 0, a: false, b: false, connected: false };
    const accel = { x: 0, y: 0, z: 0, ready: false };
    let accelListening = false;
    const onMotion = (e) => {
      const a = e.accelerationIncludingGravity || e.acceleration || {};
      const k = 0.3;
      accel.x = accel.x * k + num(a.x, 0) * (1 - k);
      accel.y = accel.y * k + num(a.y, 0) * (1 - k);
      accel.z = accel.z * k + num(a.z, 0) * (1 - k);
      accel.ready = true;
    };
    const midi = { note: 0, velocity: 0, cc: 0, ccValue: 0, gate: false, ready: false };
    let midiAccess = null;
    const onMidi = (e) => {
      const d = e.data; if (!d || d.length < 2) return;
      const status = d[0] & 0xf0;
      if (status === 0x90 && d[2] > 0) { midi.note = d[1]; midi.velocity = d[2] / 127; midi.gate = true; }
      else if (status === 0x80 || (status === 0x90 && d[2] === 0)) { if (d[1] === midi.note) midi.gate = false; }
      else if (status === 0xb0) { midi.cc = d[1]; midi.ccValue = (d[2] || 0) / 127; }
    };

    const audioCapture = createAudioInputs(opts.audioNodes || [{id:'__default',params:{source:'mic',band:opts.audioBand,fftSize:opts.audioFftSize,smoothing:opts.audioSmoothing}}]);

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
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur', onBlur);
    window.addEventListener('pointercancel', onPointerUp, passive);
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
      const audioNodes=audioCapture.sample();
      const audio=audioNodes.__default||Object.values(audioNodes)[0]||{};
      // Poll the first connected gamepad (no permission needed).
      const pads = (typeof navigator !== 'undefined' && navigator.getGamepads) ? navigator.getGamepads() : null;
      const gp = pads && (pads[0] || pads[1] || pads[2] || pads[3]);
      if (gp) { const ax = gp.axes || [], bt = gp.buttons || [];
        gamepad.connected = true;
        gamepad.x = num(ax[0], 0); gamepad.y = num(ax[1], 0); gamepad.rx = num(ax[2], 0); gamepad.ry = num(ax[3], 0);
        gamepad.a = !!(bt[0] && bt[0].pressed); gamepad.b = !!(bt[1] && bt[1].pressed);
      } else { Object.assign(gamepad, {x:0,y:0,rx:0,ry:0,a:false,b:false,connected:false}); }
      const snap = {
        surface: {width: rect.width, height: rect.height},
        pointer: {
          x: pointer.x, y: pointer.y, isDown: pointer.isDown, clicked: pointer.clicked,
          buttons: pointer.buttons, clickedButtons: pointer.clickedButtons,
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
          keys: Array.from(keysDown), pressedKeys: Array.from(pressedKeys), repeatKeys: Array.from(repeatKeys),
          axisX: keyboard.axisX, axisY: keyboard.axisY,
        },
        scroll: {
          deltaX: scroll.deltaX, deltaY: scroll.deltaY,
          accumX: scroll.accumX, accumY: scroll.accumY, velocity: scroll.velocity,
        },
        gyro: { alpha: gyro.alpha, beta: gyro.beta, gamma: gyro.gamma, tilt: { x: gyro.tilt.x, y: gyro.tilt.y }, ready: gyro.ready },
        gamepad: { x: gamepad.x, y: gamepad.y, rx: gamepad.rx, ry: gamepad.ry, a: gamepad.a, b: gamepad.b, connected: gamepad.connected },
        accel: { x: accel.x, y: accel.y, z: accel.z, ready: accel.ready },
        midi: { note: midi.note, velocity: midi.velocity, cc: midi.cc, ccValue: midi.ccValue, gate: midi.gate, ready: midi.ready },
        audioNodes,
        audio: { level: audio.level, pitch: audio.pitch, band: audio.band, raw: audio.raw, beat: audio.beat, spectrum: audio.spectrum, bands: audio.bands },
        dt: dt, time: (now - startTime) / 1000,
      };
      // Per-frame edge flags reset AFTER the snapshot is read (engine reads the raw
      // isDown and edge-detects itself; these are convenience raw pulses).
      pointer.clicked = false;
      pointer.clickedButtons = 0; pressedKeys.clear(); repeatKeys.clear();
      touch.tap = false;
      scroll.deltaX = 0; scroll.deltaY = 0;
      return snap;
    };

    const requestSensor = (kind) => {
      if (kind === 'gyro') return requestGyro();
      if (kind === 'audio' || kind === 'mic') return audioCapture.request();
      if (kind === 'accel' || kind === 'motion') return requestAccel();
      if (kind === 'midi') return requestMidi();
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

    function requestAccel() {
      if (accelListening) return Promise.resolve(true);
      const start = () => { window.addEventListener('devicemotion', onMotion, true); accelListening = true; };
      const needsPerm = typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function';
      if (!needsPerm) {
        return LogicPermission.requestGesture({ title: 'Use device motion', body: 'This piece reacts to how you move your device.', allowLabel: 'Enable motion' }, () => { start(); return true; }).then((v) => !!v);
      }
      return LogicPermission.requestGesture({ title: 'Use device motion', body: 'This piece reacts to how you move your device. Your browser will ask next.', allowLabel: 'Enable motion' },
        () => DeviceMotionEvent.requestPermission()).then((res) => { if (res === 'granted') { start(); return true; } return false; }).catch(() => false);
    }

    function requestMidi() {
      if (midiAccess) return Promise.resolve(true);
      return LogicPermission.requestGesture({ title: 'Use MIDI', body: 'This piece reacts to a connected MIDI controller.', allowLabel: 'Enable MIDI' }, () => {
        if (typeof navigator === 'undefined' || !navigator.requestMIDIAccess) throw new Error('no WebMIDI');
        return navigator.requestMIDIAccess();
      }).then((acc) => {
        if (!acc || acc === true) return false;
        midiAccess = acc;
        const bind = () => { acc.inputs.forEach((inp) => { inp.onmidimessage = onMidi; }); };
        bind(); acc.onstatechange = bind; midi.ready = true;
        return true;
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
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur', onBlur);
      window.removeEventListener('pointercancel', onPointerUp, passive);
      surface.removeEventListener('wheel', onWheel, passive);
      window.removeEventListener('resize', recomputeRect, passive);
      window.removeEventListener('scroll', recomputeRect, passive);
      if (gyroListening) { window.removeEventListener('deviceorientation', onOrientation, true); gyroListening = false; }
      if (accelListening) { window.removeEventListener('devicemotion', onMotion, true); accelListening = false; }
      if (midiAccess) { try { midiAccess.onstatechange = null; midiAccess.inputs.forEach((inp) => { inp.onmidimessage = null; }); } catch (e) {} midiAccess = null; }
      audioCapture.dispose();
    };

    return { sample, requestSensor, dispose };
  },
};
