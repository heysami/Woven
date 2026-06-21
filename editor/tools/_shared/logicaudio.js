/* ===========================================================================
   LOGICAUDIO - WebAudio output sink for the logic graph (audio-out node).

   Mirrors the LogicInputs / LogicVision module shape (attach / set / dispose):
   a runtime module the mmcomposer LogicBridge (and the baked slimPlayer) drives
   each frame with the resolved logic values of the `audio-out` node. Builds a
   simple synth voice:

       oscillator (waveform) -> gain -> lowpass filter -> destination

   The AudioContext is NEVER created at module load: WebAudio requires a user
   gesture, so attach() returns immediately with a context-less handle and the
   real context is created lazily on the FIRST set() that wants sound, behind the
   shared LogicPermission overlay (no native dialog, per LOGICGRAPH_DESIGN.md §6).
   Once a context exists, set() is a cheap per-frame parameter ramp (no node
   churn, no allocation): frequency / gain / cutoff are smoothed via
   setTargetAtTime, the waveform is swapped only on change, and `trigger` fires a
   short note-on envelope.

     attach(opts) -> {
       set({ frequency, gain, waveform, cutoff, trigger, on }),  // per frame
       suspend(),   // mute + suspend context (paused piece)
       resume(),    // resume context (Live again)
       dispose(),
     }

   No native alert/confirm/prompt. No emoji. No CDN (WebAudio is native).
   Self-contained: any tool iframe can
   `import { LogicAudio } from '../_shared/logicaudio.js'`.
   =========================================================================== */

import { LogicPermission } from './logicpermission.js';

function num(v, f) { const n = Number(v); return Number.isFinite(n) ? n : f; }
function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
const WAVES = { sine: 'sine', square: 'square', saw: 'sawtooth', sawtooth: 'sawtooth', triangle: 'triangle' };

export const LogicAudio = {

  attach(opts) {
    opts = opts || {};
    const mount = opts.mount || (typeof document !== 'undefined' ? document.body : null);

    let ctx = null, osc = null, gainNode = null, filter = null;
    let started = false;          // oscillator.start() called
    let requesting = false;       // a permission request is in flight
    let denied = false;           // user cancelled - do not nag again until reset
    let curWave = 'sine';
    let suspended = false;
    let lastTrigger = false;      // edge-detect the trigger event
    let targetGain = 0;           // the gain the graph asks for (pre-envelope)
    let envUntil = 0;             // note-on envelope decay end (ctx time)

    // Build the WebAudio graph once a context exists (called inside the gesture).
    function build() {
      const AC = (typeof window !== 'undefined') && (window.AudioContext || window.webkitAudioContext);
      if (!AC) return false;
      try {
        ctx = new AC();
        gainNode = ctx.createGain();
        gainNode.gain.value = 0;                 // silent until set() ramps it up
        filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.value = 8000;
        filter.Q.value = 0.7;
        osc = ctx.createOscillator();
        osc.type = curWave;
        osc.frequency.value = 220;
        osc.connect(gainNode);
        gainNode.connect(filter);
        filter.connect(ctx.destination);
        osc.start();
        started = true;
        return true;
      } catch (e) { ctx = null; osc = null; gainNode = null; filter = null; return false; }
    }

    // Gesture-gated context creation. Returns a Promise<bool>; resolves true once
    // the context exists. Re-entrant-safe (a single in-flight request at a time).
    function ensureContext() {
      if (ctx) return Promise.resolve(true);
      if (denied || requesting) return Promise.resolve(false);
      requesting = true;
      return LogicPermission.requestGesture({
        title: 'Play sound',
        body: 'This piece reacts to sound and can play audio. Enable it to hear it.',
        allowLabel: 'Enable sound',
        cancelLabel: 'Stay muted',
        mount: mount,
      }, () => { return build(); }).then((res) => {
        requesting = false;
        if (res) return true;
        denied = true;   // user cancelled: respect it (reset() clears this)
        return false;
      }).catch(() => { requesting = false; denied = true; return false; });
    }

    // Per-frame parameter push. `p` carries the resolved logic values for the
    // audio-out node. The first call that WANTS sound (on !== false and gain > 0)
    // triggers the gesture-gated context creation; until the user allows it, this
    // is a silent no-op (nothing throws, nothing autostarts).
    function set(p) {
      p = p || {};
      const wantsSound = p.on !== false && num(p.gain, 0) > 0.0001;
      if (!ctx) {
        if (wantsSound && !suspended) ensureContext();   // fire-and-forget gesture
        // remember the latest target so the first audible frame after Allow ramps in
        targetGain = clamp(num(p.gain, 0), 0, 1);
        return;
      }
      if (suspended) return;
      const now = ctx.currentTime;
      const tc = 0.02;   // ~20ms smoothing time-constant (no zipper noise)

      // waveform: swap only on change (cheap, no node churn).
      const w = WAVES[String(p.waveform || 'sine')] || 'sine';
      if (w !== curWave && osc) { try { osc.type = w; } catch (e) {} curWave = w; }

      // frequency (Hz), clamped to the audible range.
      const freq = clamp(num(p.frequency, 220), 20, 20000);
      if (osc) { try { osc.frequency.setTargetAtTime(freq, now, tc); } catch (e) {} }

      // cutoff (Hz lowpass).
      const cutoff = clamp(num(p.cutoff, 8000), 20, 20000);
      if (filter) { try { filter.frequency.setTargetAtTime(cutoff, now, tc); } catch (e) {} }

      // trigger: a rising edge fires a short note-on envelope (a percussive pluck
      // on top of the sustained gain). We hold an envelope window and let the gain
      // ramp handle the body; the trigger gives an immediate attack transient.
      const trig = !!p.trigger;
      if (trig && !lastTrigger && gainNode) {
        const peak = clamp(Math.max(num(p.gain, 0), 0.2), 0, 1);
        try {
          gainNode.gain.cancelScheduledValues(now);
          gainNode.gain.setValueAtTime(Math.max(0.0001, gainNode.gain.value), now);
          gainNode.gain.linearRampToValueAtTime(peak, now + 0.005);   // 5ms attack
          envUntil = now + 0.25;                                       // 250ms decay
        } catch (e) {}
      }
      lastTrigger = trig;

      // sustained gain: outside an active note-on envelope, track the requested
      // gain with a smooth ramp; during the envelope decay let it fall to target.
      targetGain = (p.on === false) ? 0 : clamp(num(p.gain, 0), 0, 1);
      if (gainNode && now >= envUntil) {
        try { gainNode.gain.setTargetAtTime(targetGain, now, tc); } catch (e) {}
      } else if (gainNode) {
        // during the decay window glide toward target with a longer constant.
        try { gainNode.gain.setTargetAtTime(targetGain, now, 0.08); } catch (e) {}
      }
    }

    function suspend() {
      suspended = true;
      if (gainNode && ctx) { try { gainNode.gain.setTargetAtTime(0, ctx.currentTime, 0.02); } catch (e) {} }
      if (ctx && ctx.suspend) { try { ctx.suspend(); } catch (e) {} }
    }
    function resume() {
      suspended = false;
      if (ctx && ctx.resume) { try { ctx.resume(); } catch (e) {} }
    }
    function dispose() {
      suspended = true;
      try { if (osc) osc.stop(); } catch (e) {}
      try { if (osc) osc.disconnect(); } catch (e) {}
      try { if (gainNode) gainNode.disconnect(); } catch (e) {}
      try { if (filter) filter.disconnect(); } catch (e) {}
      try { if (ctx && ctx.close) ctx.close(); } catch (e) {}
      ctx = null; osc = null; gainNode = null; filter = null; started = false;
    }

    return { set, suspend, resume, dispose, get ready() { return !!ctx; } };
  },
};
