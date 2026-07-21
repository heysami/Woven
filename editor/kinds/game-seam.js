/* game-seam.js - the STRUCTURAL seam library (docs/agents/game-seam-contract.md).
 *
 * This file is the contract AS CODE. It is auto-copied verbatim into
 * games/<gameId>/seam.js by the QA compile step - never hand-edit the copy.
 * The runtime composer loads it and calls __seam.makeHarness(cfg) instead of
 * hand-building window.__game; drivers use applyFacing/forwardToYaw instead of
 * inventing a facing convention. What used to be eight prose rules is one call.
 *
 * Conventions baked in (fixed, non-negotiable):
 *   - models rest facing world -Z; yaw = atan2(forward.x, forward.z) + PI
 *   - facing crosses the seam as a forward VECTOR {x,z} / [x,z], never a bare angle
 *   - model forward for QA = -getWorldDirection() of the avatar root (non-camera)
 */
(function () {
  'use strict';

  function fx(f) { return (f && f.x !== undefined) ? f.x : (f ? f[0] : 0) || 0; }
  function fz(f) { return (f && f.z !== undefined) ? f.z : (f ? f[1] : 0) || 0; }

  /* forward vector -> rotation.y under the rest-facing--Z convention. */
  function forwardToYaw(f) { return Math.atan2(fx(f), fz(f)) + Math.PI; }

  /* Rotate a model root to face its forward vector. No-op on a ~zero vector
   * (hold last facing while standing still). */
  function applyFacing(object3D, forward) {
    var x = fx(forward), z = fz(forward);
    if ((x * x + z * z) > 1e-9) object3D.rotation.y = Math.atan2(x, z) + Math.PI;
  }

  /* makeHarness(cfg) installs the full window.__game QA harness.
   * cfg (all functions, bound by the composer):
   *   state()          -> the loop's live state object
   *   intents          -> array of every intent kind injectFakeInput accepts
   *   injectFakeInput(kind, opts) -> forwards to the input layer; false when ignored
   *   tick(seconds)    -> deterministic fast-forward through the fixed-step loop
   *   snapshot()       -> { phase, avatar: { pos:[x,y,z], forward:[x,z], speed }, ... }
   *                       plus every field the overlay binds, at its documented path
   *   avatarObject()   -> the RENDERED avatar's root Object3D (or null pre-boot).
   *                       2D paradigms (Pixi/canvas) pass modelForward instead.
   *   modelForward()   -> optional override returning [x,y,z] world forward of the
   *                       RENDERED avatar (2D: derive from sprite rotation, y=0).
   *                       Games with NO steerable avatar omit both avatarObject and
   *                       modelForward AND omit snapshot().avatar - QA skips the
   *                       facing/anim asserts for them.
   *   activeClip()     -> { name, clock } for the avatar's active anim clip; the clock
   *                       value must change whenever the clip visually advances
   *   start()          -> optional; begins play as the gate click would
   *   debugDraw(on)    -> optional; compass + forward-gizmo + breadcrumb overlay
   *   spawnTarget(x,y,z,label) -> optional
   */
  function makeHarness(cfg) {
    var errors = [];
    function phaseOf() {
      try { var s = cfg.snapshot(); return s ? s.phase : null; } catch (_) { return null; }
    }
    function pushErr(message, stack) {
      if (errors.length >= 10) errors.shift();
      errors.push({ message: String(message).slice(0, 300),
                    stack: stack ? String(stack).slice(0, 400) : null,
                    phase: phaseOf() });
    }
    window.addEventListener('error', function (e) {
      pushErr(e.message || e, e.error && e.error.stack);
    });
    window.addEventListener('unhandledrejection', function (e) {
      pushErr(e.reason || 'unhandledrejection', e.reason && e.reason.stack);
    });

    var _lastClip = { name: null, clock: null };
    function animState() {
      var c = null;
      try { c = cfg.activeClip ? cfg.activeClip() : null; } catch (_) {}
      if (!c) return { name: null, clockAdvancing: false };
      var advancing = (_lastClip.name === c.name) ? (c.clock !== _lastClip.clock) : true;
      _lastClip.name = c.name; _lastClip.clock = c.clock;
      return { name: c.name, clockAdvancing: advancing };
    }

    function modelForward() {
      if (cfg.modelForward) {
        try { return cfg.modelForward(); } catch (_) { return null; }
      }
      var o = null;
      try { o = cfg.avatarObject ? cfg.avatarObject() : null; } catch (_) {}
      if (!o || typeof o.getWorldDirection !== 'function') return null;
      var v = o.getWorldDirection(new o.position.constructor());
      return [-v.x, -v.y, -v.z];   // rest-facing--Z: forward is the negated +Z axis
    }

    var game = {
      get state() { try { return cfg.state(); } catch (_) { return null; } },
      intents: (cfg.intents || []).slice(),
      injectFakeInput: function (kind, opts) {
        try { return cfg.injectFakeInput(kind, opts || {}); }
        catch (e) { pushErr('injectFakeInput(' + kind + '): ' + e); return false; }
      },
      tick: function (seconds) {
        try { return cfg.tick(seconds); }
        catch (e) { pushErr('tick(' + seconds + '): ' + e); }
      },
      snapshot: function () { return cfg.snapshot(); },
      errors: errors,
      qa: {
        modelForward: modelForward,
        animState: animState,
        debug: cfg.debugDraw || function () {},
        spawnTarget: cfg.spawnTarget || function () {}
      }
    };
    if (cfg.start) game.start = cfg.start;
    window.__game = game;
    return game;
  }

  window.__seam = {
    makeHarness: makeHarness,
    applyFacing: applyFacing,
    forwardToYaw: forwardToYaw
  };
})();
