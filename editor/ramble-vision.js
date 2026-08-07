/* Ramble hand tracking - the vision engine behind the editor's Ramble mode.

   Wraps MediaPipe HandLandmarker (same pinned CDN build as
   tools/_shared/logicvision.js, which drops handedness + z and only knows
   fist/open/point - Ramble needs more, so this module keeps both and derives
   the full gesture vocabulary):

     - anatomical left/right hands (handedness labels, mirror-corrected)
     - palm orientation up/down (2D chirality of the metacarpal fan, latched)
     - pinch (thumb-index distance, hysteresis pair, scale-normalized)
     - thumb-to-fingertip touch (menu selection)
     - pose: open / fist / point / partial (rotation-invariant)
     - fist shake (delete gesture)
     - one-euro smoothing per landmark, presence grace for dropped frames

   Emits one HandState per video frame:
     { t, left: HandFrame|null, right: HandFrame|null, source: "vision" }
   HandFrame = { landmarks:[21 x {x,y,z}], palm, pose, pinch:{active,dist,x,y},
                 thumbTouch, wrist, tips:{thumb,index,middle,ring,pinky},
                 scale, vel:{x,y}, shake, stale }
   Coordinates are normalized DISPLAY space (0..1 of the video frame, already
   x-flipped when mirroring is on - consumers never handle mirror themselves).

   Fail-soft: if the CDN or model cannot load, start() resolves with
   ctl.status() === "failed" and never emits - the caller shows a visible
   "hand tracking unavailable" state. Never throws into the page. */

const CDN = {
  mpVision: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs',
  mpWasm: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm',
  handModel: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
};

const DETECT_INTERVAL_MS = 40;   // ~25fps inference cap (matches logicvision)

const DEFAULT_CONFIG = {
  // Pinch = thumbTip-indexTip distance normalized by the thumb DISTAL segment
  // (IP->tip, scaled x1.55 to keep familiar units), with the index proximal
  // phalanx as an occlusion floor. The thumb's distal bone sits at the SAME
  // DEPTH as the pinching tips, so close-to-camera perspective inflates the
  // numerator and denominator together and the ratio stays depth-invariant
  // (the old palm/phalanx references sat deeper and broke up close).
  // Relaxed open hand ~1.2-2.0, actual pinch ~0.2-0.5.
  pinchOn: 0.7,
  pinchOff: 1.05,
  // Relative release: while pinched, remember the tightest gap seen; the gap
  // growing past (tightest x releaseRatio) is a release regardless of the
  // absolute band - self-calibrating per pinch and per hand height.
  releaseRatio: 1.7,
  // Consecutive frames under pinchOn required to engage (debounces the
  // single-frame flickers occluded top-down hands produce).
  pinchOnFrames: 2,
  // Palm-up release factor: with the palm toward an overhead camera the
  // fingertips point AT the lens and their estimated positions stay glued
  // together after a real release. Scale the release threshold down so the
  // pinch lets go sooner in that orientation.
  pinchOffUpFactor: 0.72,
  // No pinch ENGAGEMENT while edge-on or this soon after a palm flip - the
  // rotating hand's collapsed landmarks read as phantom pinches. Kept SHORT:
  // the edge-on state already covers the rotation itself, and a long tail
  // reads as post-flip deadness when pinching right after a flip.
  flipGuardMs: 100,
  // Thumb-to-fingertip touch (same phalanx normalization).
  touchOn: 0.55,
  touchOff: 0.85,
  // Palm flip must hold this long before we latch the new orientation.
  palmLatchMs: 150,
  // Extended-finger test: tip must be this factor further from the wrist than
  // its PIP joint to count as extended (rotation-invariant).
  extendFactor: 1.12,
  // Shake: >= shakeReversals sign flips of wrist velocity within shakeWindowMs,
  // each swing at least shakeAmp (normalized units), fist pose required.
  shakeWindowMs: 600,
  shakeReversals: 3,
  shakeAmp: 0.035,
  shakeCooldownMs: 500,
  // Presence grace: reuse the last frame (stale:true) for this long after the
  // detector loses a hand, so single-frame dropouts don't dismiss menus.
  graceMs: 200,
  // One-euro filter tuning. minCutoff lower = steadier at rest; beta higher =
  // snappier in motion.
  euroMinCutoff: 1.6,
  euroBeta: 0.03,
  euroDCutoff: 1.0,
  // Palm chirality sign per anatomical hand, for an UNMIRRORED feed. The 2D
  // cross product of (indexMcp - wrist) x (pinkyMcp - wrist) flips sign when
  // the palm turns; these pin which sign means "palm toward camera" (= palm
  // "up" under an overhead camera). Pinned empirically on a real desk camera:
  // when handedness labels were still swapped, the physical LEFT hand ran on
  // palmSignRight=+1 and gated correctly, so left=+1 / right=-1 are the true
  // anatomical signs. Override via setConfig (the HUD persists overrides).
  palmSignRight: -1,
  palmSignLeft: 1,
  // Handedness label swap. Detection always runs on the RAW camera frames
  // (CSS/display flips never change the pixels), and tasks-vision 0.10 labels
  // raw webcam feeds anatomically correctly in practice (verified on a real
  // desk camera), so auto (null) means NO swap. Override via setConfig if a
  // particular camera pipeline disagrees.
  swapHandedness: null,
};

const _esmCache = new Map();
function loadEsm(url) {
  if (_esmCache.has(url)) return _esmCache.get(url);
  const p = import(/* @vite-ignore */ url).then((m) => m).catch(() => null);
  _esmCache.set(url, p);
  return p;
}

let _landmarkerPromise = null;
function ensureLandmarker() {
  if (_landmarkerPromise) return _landmarkerPromise;
  _landmarkerPromise = (async () => {
    try {
      const mod = await loadEsm(CDN.mpVision);
      if (!mod || !mod.FilesetResolver || !mod.HandLandmarker) return null;
      const fileset = await mod.FilesetResolver.forVisionTasks(CDN.mpWasm);
      const lm = await mod.HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: CDN.handModel, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numHands: 2,
      });
      return lm || null;
    } catch (e) {
      return null;
    }
  })();
  return _landmarkerPromise;
}

/* ── one-euro filter ─────────────────────────────────────────────────────── */
function makeEuro(cfg) {
  // State per scalar channel: previous value + previous derivative.
  return { x: null, dx: 0, t: 0, cfg };
}
function euroAlpha(cutoff, dt) {
  const tau = 1 / (2 * Math.PI * cutoff);
  return 1 / (1 + tau / dt);
}
function euroStep(f, v, t) {
  if (f.x == null || t <= f.t) { f.x = v; f.dx = 0; f.t = t; return v; }
  const dt = Math.max(1e-3, (t - f.t) / 1000);
  const dv = (v - f.x) / dt;
  const aD = euroAlpha(f.cfg.euroDCutoff, dt);
  f.dx = f.dx + aD * (dv - f.dx);
  const cutoff = f.cfg.euroMinCutoff + f.cfg.euroBeta * Math.abs(f.dx);
  const a = euroAlpha(cutoff, dt);
  f.x = f.x + a * (v - f.x);
  f.t = t;
  return f.x;
}

const dist2 = (a, b) => {
  const dx = a.x - b.x, dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy);
};

/* Per-hand tracker: smoothing filters + latched gesture state. */
function makeHandTracker(cfg) {
  return {
    cfg,
    filters: null,          // [21 x {x,y,z}] one-euro filters
    lastFrame: null,        // last emitted HandFrame
    lastSeen: 0,            // last time the detector actually saw this hand
    palm: 'down',
    palmCandidate: null,    // { value, since }
    pinchActive: false,
    pinchOnStreak: 0,       // consecutive frames under pinchOn (debounce)
    pinchMin: 0,            // tightest gap of the current pinch (relative release)
    lastPalmFlipAt: 0,      // pinch-engage guard window after a flip
    thumbTouch: null,
    prevWrist: null,        // { x, y, t } smoothed, for velocity
    vel: { x: 0, y: 0 },
    swings: [],             // [{ sign, t }] velocity sign flips for shake
    lastVelSign: 0,
    lastShakeAt: 0,
  };
}

function trackerReset(tr) {
  tr.filters = null;
  tr.lastFrame = null;
  tr.palmCandidate = null;
  tr.pinchActive = false;
  tr.thumbTouch = null;
  tr.prevWrist = null;
  tr.vel = { x: 0, y: 0 };
  tr.swings = [];
  tr.lastVelSign = 0;
}

function trackerUpdate(tr, rawLm, t, hand, chiralitySign) {
  const cfg = tr.cfg;
  if (!tr.filters) {
    tr.filters = [];
    for (let i = 0; i < 21; i++) {
      tr.filters.push({ x: makeEuro(cfg), y: makeEuro(cfg), z: makeEuro(cfg) });
    }
  }
  const lm = new Array(21);
  for (let i = 0; i < 21; i++) {
    const r = rawLm[i] || { x: 0, y: 0, z: 0 };
    lm[i] = {
      x: euroStep(tr.filters[i].x, r.x, t),
      y: euroStep(tr.filters[i].y, r.y, t),
      z: euroStep(tr.filters[i].z, r.z || 0, t),
    };
  }
  const wrist = lm[0];
  const tips = { thumb: lm[4], index: lm[8], middle: lm[12], ring: lm[16], pinky: lm[20] };
  const scale = Math.max(1e-4, dist2(wrist, lm[9]));   // wrist -> middle MCP

  // Palm orientation: 2D cross of the metacarpal fan, sign pinned per hand.
  const v1 = { x: lm[5].x - wrist.x, y: lm[5].y - wrist.y };
  const v2 = { x: lm[17].x - wrist.x, y: lm[17].y - wrist.y };
  const cross = v1.x * v2.y - v1.y * v2.x;
  const sign = (hand === 'right' ? cfg.palmSignRight : cfg.palmSignLeft) * (chiralitySign || 1);
  const mag = Math.abs(cross) / (scale * scale);
  const edgeOn = mag <= 0.15;   // hand roughly side-on to the camera (mid-flip)
  if (!edgeOn) {
    const cand = (cross * sign > 0) ? 'up' : 'down';
    if (cand !== tr.palm) {
      if (!tr.palmCandidate || tr.palmCandidate.value !== cand) {
        tr.palmCandidate = { value: cand, since: t };
      } else if (t - tr.palmCandidate.since >= cfg.palmLatchMs) {
        tr.palm = cand;
        tr.palmCandidate = null;
        tr.lastPalmFlipAt = t;
      }
    } else {
      tr.palmCandidate = null;
    }
  }

  // Pose (rotation-invariant): extended = tip meaningfully further from the
  // wrist than its PIP joint.
  const ext = (tipI, pipI) => dist2(lm[tipI], wrist) > dist2(lm[pipI], wrist) * cfg.extendFactor;
  const extIndex = ext(8, 6), extMiddle = ext(12, 10), extRing = ext(16, 14), extPinky = ext(20, 18);
  const extCount = (extIndex ? 1 : 0) + (extMiddle ? 1 : 0) + (extRing ? 1 : 0) + (extPinky ? 1 : 0);
  let pose = 'partial';
  if (extCount === 0) pose = 'fist';
  else if (extCount >= 3) pose = 'open';
  else if (extIndex && extCount === 1) pose = 'point';

  // Pinch with hysteresis + engage debounce; depth-invariant reference - see
  // DEFAULT_CONFIG for why the thumb distal segment is the normalizer.
  const phalanx = Math.max(1e-4, dist2(lm[5], lm[6]));
  const thumbSeg = dist2(lm[3], lm[4]);
  const ref = Math.max(1e-4, Math.max(thumbSeg * 1.55, phalanx * 0.6));
  const pinchDist = dist2(tips.thumb, tips.index) / ref;
  const absoluteOff = tr.palm === 'up'
    ? cfg.pinchOff * (cfg.pinchOffUpFactor || 1)
    : cfg.pinchOff;
  // Release fires on EITHER the absolute band or the relative one (gap grew
  // releaseRatio-fold past this pinch's tightest point), whichever is lower -
  // floored near the engage band so an ultra-tight pinch cannot self-release.
  const relativeOff = Math.max(cfg.pinchOn * 0.9, (tr.pinchMin || 1) * (cfg.releaseRatio || 1.7));
  const offThreshold = Math.min(absoluteOff, relativeOff);
  // Never ENGAGE a pinch while the hand is edge-on or fresh out of a palm
  // flip: rotating hands collapse the landmarks and read as phantom pinches.
  // Already-active pinches are untouched (flip-and-keep-drawing still works).
  const flipGuard = edgeOn || (t - (tr.lastPalmFlipAt || 0) < (cfg.flipGuardMs || 250));
  if (tr.pinchActive) {
    tr.pinchMin = Math.min(tr.pinchMin || pinchDist, pinchDist);
    if (pinchDist > offThreshold) { tr.pinchActive = false; tr.pinchOnStreak = 0; tr.pinchMin = 0; }
  } else if (flipGuard) {
    tr.pinchOnStreak = 0;
  } else if (pinchDist < cfg.pinchOn) {
    tr.pinchOnStreak += 1;
    if (tr.pinchOnStreak >= Math.max(1, cfg.pinchOnFrames || 1)) {
      tr.pinchActive = true;
      tr.pinchMin = pinchDist;
    }
  } else {
    tr.pinchOnStreak = 0;
  }

  // Thumb-to-fingertip touch (nearest of the four, hysteresis on the held
  // one), on the same depth-invariant reference.
  const touchD = {
    index: dist2(tips.thumb, tips.index) / ref,
    middle: dist2(tips.thumb, tips.middle) / ref,
    ring: dist2(tips.thumb, tips.ring) / ref,
    pinky: dist2(tips.thumb, tips.pinky) / ref,
  };
  if (tr.thumbTouch && touchD[tr.thumbTouch] <= cfg.touchOff) {
    // keep the current touch until it clearly releases
  } else {
    tr.thumbTouch = null;
    let best = null, bestD = cfg.touchOn;
    for (const k of ['index', 'middle', 'ring', 'pinky']) {
      if (touchD[k] < bestD) { best = k; bestD = touchD[k]; }
    }
    tr.thumbTouch = best;
  }

  // Wrist velocity (normalized units/s) + shake detection.
  if (tr.prevWrist) {
    const dt = Math.max(1e-3, (t - tr.prevWrist.t) / 1000);
    tr.vel = { x: (wrist.x - tr.prevWrist.x) / dt, y: (wrist.y - tr.prevWrist.y) / dt };
  }
  tr.prevWrist = { x: wrist.x, y: wrist.y, t };
  let shake = false;
  if (pose === 'fist') {
    const speed = Math.abs(tr.vel.x) + Math.abs(tr.vel.y);
    const dom = Math.abs(tr.vel.x) >= Math.abs(tr.vel.y) ? tr.vel.x : tr.vel.y;
    const s = dom > 0 ? 1 : dom < 0 ? -1 : 0;
    if (s !== 0 && speed * 0.016 > cfg.shakeAmp) {   // per-frame amplitude proxy
      if (tr.lastVelSign !== 0 && s !== tr.lastVelSign) tr.swings.push({ t });
      tr.lastVelSign = s;
    }
    tr.swings = tr.swings.filter((sw) => t - sw.t <= cfg.shakeWindowMs);
    if (tr.swings.length >= cfg.shakeReversals && t - tr.lastShakeAt > cfg.shakeCooldownMs) {
      shake = true;
      tr.lastShakeAt = t;
      tr.swings = [];
    }
  } else {
    tr.swings = [];
    tr.lastVelSign = 0;
  }

  tr.lastSeen = t;
  tr.lastFrame = {
    landmarks: lm,
    palm: tr.palm,
    pose,
    pinch: {
      active: tr.pinchActive,
      // solid = fingers still fully closed (below the ENGAGE band). Between
      // solid and released lies the hysteresis dead zone where a top-down
      // palm-up release hides; consumers freeze scrubbing there so a hidden
      // release can never drift a selection.
      solid: tr.pinchActive && pinchDist < cfg.pinchOn,
      dist: pinchDist,
      x: (tips.thumb.x + tips.index.x) / 2,
      y: (tips.thumb.y + tips.index.y) / 2,
    },
    thumbTouch: tr.thumbTouch,
    wrist,
    tips,
    scale,
    vel: tr.vel,
    shake,
    stale: false,
  };
  return tr.lastFrame;
}

export const RambleVision = {
  async listCameras() {
    try {
      const list = await navigator.mediaDevices.enumerateDevices();
      return list.filter((d) => d.kind === 'videoinput')
        .map((d) => ({ deviceId: d.deviceId, label: d.label || 'Camera' }));
    } catch (e) {
      return [];
    }
  },

  /* Attach hand tracking to an already-playing <video>. The caller owns the
     camera stream (RambleView acquires it for the visible feed); this module
     only reads frames - no second getUserMedia.

     flipH / flipV mirror the DISPLAY (the caller flips the <video> with CSS);
     landmarks are emitted in that same display space, and palm chirality is
     sign-corrected when exactly one axis is flipped (a mirror flips winding;
     a 180-degree rotation does not). Anatomical handedness never changes with
     display flips - it is a property of the raw frame. */
  async start(opts) {
    const videoEl = opts.videoEl;
    const onFrame = opts.onFrame || (() => {});
    const cfg = Object.assign({}, DEFAULT_CONFIG, opts.config || {});
    let flipH = !!(opts.flipH != null ? opts.flipH : opts.mirror);
    let flipV = !!opts.flipV;
    let status = 'loading';
    let running = true;

    const trackers = { left: makeHandTracker(cfg), right: makeHandTracker(cfg) };
    let lastDetect = 0;
    let rvfcId = 0, rafId = 0;

    const landmarker = await ensureLandmarker();
    if (!landmarker) status = 'failed';
    else status = 'on';

    const swapNow = () => (cfg.swapHandedness == null ? false : !!cfg.swapHandedness);
    // Exactly one display flip inverts the winding the palm test reads.
    const chiralityAdjust = () => (flipH !== flipV ? -1 : 1);

    const step = (t) => {
      if (!running) return;
      schedule();
      if (status !== 'on' || !videoEl || videoEl.readyState < 2) return;
      const now = performance.now();
      if (now - lastDetect < DETECT_INTERVAL_MS) return;
      lastDetect = now;
      let res = null;
      try { res = landmarker.detectForVideo(videoEl, now); } catch (e) { return; }
      const seen = { left: false, right: false };
      const lms = (res && res.landmarks) || [];
      const hands = (res && (res.handednesses || res.handedness)) || [];
      for (let i = 0; i < lms.length; i++) {
        const cat = hands[i] && hands[i][0];
        if (!cat) continue;
        let label = String(cat.categoryName || cat.displayName || '').toLowerCase();
        if (label !== 'left' && label !== 'right') continue;
        if (swapNow()) label = label === 'left' ? 'right' : 'left';
        if (seen[label]) continue;   // one hand per side
        seen[label] = true;
        // Normalize into display space: apply the same flips the caller puts
        // on the <video> so consumers always match what they see on screen.
        const raw = lms[i].map((p) => ({
          x: flipH ? 1 - p.x : p.x,
          y: flipV ? 1 - p.y : p.y,
          z: p.z || 0,
        }));
        trackerUpdate(trackers[label], raw, now, label, chiralityAdjust());
      }
      // Presence grace for unseen hands.
      const out = { t: now, left: null, right: null, source: 'vision' };
      for (const hand of ['left', 'right']) {
        const tr = trackers[hand];
        if (seen[hand]) {
          out[hand] = tr.lastFrame;
        } else if (tr.lastFrame && now - tr.lastSeen <= cfg.graceMs) {
          out[hand] = Object.assign({}, tr.lastFrame, { stale: true, shake: false });
        } else if (tr.lastFrame) {
          trackerReset(tr);
        }
      }
      onFrame(out);
    };

    const schedule = () => {
      if (!running) return;
      if (videoEl && typeof videoEl.requestVideoFrameCallback === 'function') {
        rvfcId = videoEl.requestVideoFrameCallback(() => step());
      } else {
        rafId = requestAnimationFrame(() => step());
      }
    };
    schedule();

    return {
      status: () => status,
      stop: () => {
        running = false;
        try { if (rvfcId && videoEl.cancelVideoFrameCallback) videoEl.cancelVideoFrameCallback(rvfcId); } catch (e) {}
        try { if (rafId) cancelAnimationFrame(rafId); } catch (e) {}
      },
      setMirror: (m) => { flipH = !!m; },
      setFlips: (f) => {
        if (f && f.h != null) flipH = !!f.h;
        if (f && f.v != null) flipV = !!f.v;
      },
      setConfig: (partial) => { Object.assign(cfg, partial || {}); },
      getConfig: () => Object.assign({}, cfg),
    };
  },
};

export default RambleVision;
