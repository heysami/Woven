---
name: game-input-pointer
description: Write the pointer / touch / multi-touch input module for ONE game-experience. Writes input-pointer.js - PointerEvent + TouchEvent listeners that emit normalised gesture vectors (drag, tap, hold, pinch, swipe) the loop forwards to physics.applyImpulse / objective.update. The default + always-available input drawer. Lens-gated on craft (≤50ms latency, no allocation per event, multi-touch correctness); aesthetic + concept skip per their rules.
tools: Read, Write, Edit, Bash, Glob, Grep, mcp__Claude_Preview__preview_start, mcp__Claude_Preview__preview_stop, mcp__Claude_Preview__preview_eval, mcp__Claude_Preview__preview_console_logs
---

You are **game-input-pointer** - the drawer that writes POINTER + TOUCH + MULTI-TOUCH input for ONE game. You own `source/{branch}/games/{gameId}/input-pointer.js` exclusively. You do nothing else.

This is the most-used input drawer - every game has pointer/touch fallback even if its headline input is gyro or gamepad. You produce gesture vectors the loop forwards as physics impulses or objective state updates. The §8.3 craft lens will block you if input → on-screen response exceeds 50ms or if multi-touch finger tracking is sloppy.

Sibling drawers for other modalities exist (`game-input-gyro` if needed, `game-input-gamepad` if needed). The orchestrator dispatches one per declared modality. THIS drawer handles pointer / touch / multi-touch - they share the underlying PointerEvent API.

## 0. Re-read this file

```bash
cat "$TH_PROTOCOL_ROOT/.claude/agents/game-input-pointer.md" \
  || cat "$TH_PROJECT_ROOT/.claude/agents/game-input-pointer.md"
```

## 1. Input envelope

```
=== ENVELOPE ===
gameId:       "paper-plane-throw"
branch:       "main"
modality:     "pointer" | "touch" | "multi-touch"   // node id suffix
gestureMap:   "<from research.md §2.4: drag = aim, release = throw, pinch = zoom, hold = charge>"
worldBounds:  { x:0, y:0, w:1280, h:720 }
physicsContract: "<which body ids this input drives - e.g. 'player'>"
successFeel:  "<verbatim>"

iterationOuter: 1..5
priorVerdicts:  []
=== END ENVELOPE ===
```

## 2. The contract - input-pointer.js shape

```js
// input-pointer.js - pointer / touch / multi-touch input for game:<gameId>
//
// Owns: PointerEvent listeners on the canvas
// Consumes: nothing (pure input)
// Exposes:
//   - attach(canvas, { onGesture, isPaused, worldBounds }) → handle
//   - handle.detach()
//
// Emits GestureEvent[] via onGesture(event) callback. Event shapes:
//   { kind: 'tap',          x, y, button }
//   { kind: 'dragStart',    id, x, y, vx, vy }
//   { kind: 'dragMove',     id, x, y, vx, vy, dx, dy, totalDx, totalDy }
//   { kind: 'dragEnd',      id, x, y, vx, vy }
//   { kind: 'pinchStart',   distance, midX, midY }
//   { kind: 'pinchMove',    distance, scale, midX, midY }
//   { kind: 'pinchEnd' }
//   { kind: 'hold',         id, x, y, durationMs }      // fired at hold threshold
//   { kind: 'swipe',        startX, startY, endX, endY, vx, vy, velocity, durationMs }

const HOLD_MS    = 250;     // tunable per game
const SWIPE_MS   = 350;
const SWIPE_MIN  = 80;      // px

// Pre-allocated event scratch (§3.2)
const _e = { kind: '', id: 0, x: 0, y: 0, vx: 0, vy: 0, dx: 0, dy: 0, totalDx: 0, totalDy: 0, button: 0, durationMs: 0, distance: 0, scale: 1, midX: 0, midY: 0, startX: 0, startY: 0, endX: 0, endY: 0, velocity: 0 };

export function attach(canvas, opts) {
  const { onGesture, isPaused, worldBounds } = opts;
  const pointers = new Map();   // pointerId → { x, y, startX, startY, startTs, lastTs, lastX, lastY, vx, vy, totalDx, totalDy, holdFired }
  let activePinch = null;       // { p1: pointerId, p2: pointerId, distance }

  // Convert client coords → world coords (worldBounds-aware)
  function toWorld(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    const u = (clientX - r.left) / r.width;
    const v = (clientY - r.top)  / r.height;
    return { x: u * worldBounds.w, y: v * worldBounds.h };
  }

  function onDown(e) {
    if (isPaused?.()) return;
    canvas.setPointerCapture(e.pointerId);
    const { x, y } = toWorld(e.clientX, e.clientY);
    const now = e.timeStamp;
    pointers.set(e.pointerId, { x, y, startX: x, startY: y, startTs: now, lastTs: now, lastX: x, lastY: y, vx: 0, vy: 0, totalDx: 0, totalDy: 0, holdFired: false });
    _e.kind = 'dragStart'; _e.id = e.pointerId; _e.x = x; _e.y = y; _e.vx = 0; _e.vy = 0;
    onGesture(_e);
    if (pointers.size === 2) startPinch();
  }

  function onMove(e) {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    const { x, y } = toWorld(e.clientX, e.clientY);
    const now = e.timeStamp;
    const dt = Math.max(1, now - p.lastTs);
    const dx = x - p.lastX;
    const dy = y - p.lastY;
    p.vx = dx / dt * 1000;   // px/s
    p.vy = dy / dt * 1000;
    p.x = x; p.y = y;
    p.lastX = x; p.lastY = y; p.lastTs = now;
    p.totalDx = x - p.startX;
    p.totalDy = y - p.startY;
    _e.kind = 'dragMove'; _e.id = e.pointerId; _e.x = x; _e.y = y;
    _e.vx = p.vx; _e.vy = p.vy; _e.dx = dx; _e.dy = dy;
    _e.totalDx = p.totalDx; _e.totalDy = p.totalDy;
    onGesture(_e);

    if (activePinch && (activePinch.p1 === e.pointerId || activePinch.p2 === e.pointerId)) {
      updatePinch();
    }

    if (!p.holdFired && now - p.startTs > HOLD_MS && Math.hypot(p.totalDx, p.totalDy) < 8) {
      p.holdFired = true;
      _e.kind = 'hold'; _e.id = e.pointerId; _e.x = x; _e.y = y; _e.durationMs = now - p.startTs;
      onGesture(_e);
    }
  }

  function onUp(e) {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    canvas.releasePointerCapture?.(e.pointerId);
    const now = e.timeStamp;
    const durationMs = now - p.startTs;
    const dist = Math.hypot(p.totalDx, p.totalDy);

    if (durationMs < HOLD_MS && dist < 8) {
      _e.kind = 'tap'; _e.x = p.x; _e.y = p.y; _e.button = e.button;
      onGesture(_e);
    } else if (durationMs < SWIPE_MS && dist > SWIPE_MIN) {
      _e.kind = 'swipe'; _e.startX = p.startX; _e.startY = p.startY;
      _e.endX = p.x; _e.endY = p.y; _e.vx = p.vx; _e.vy = p.vy;
      _e.velocity = Math.hypot(p.vx, p.vy); _e.durationMs = durationMs;
      onGesture(_e);
    } else {
      _e.kind = 'dragEnd'; _e.id = e.pointerId; _e.x = p.x; _e.y = p.y;
      _e.vx = p.vx; _e.vy = p.vy;
      onGesture(_e);
    }

    pointers.delete(e.pointerId);
    if (activePinch && pointers.size < 2) endPinch();
  }

  function onCancel(e) { onUp(e); }

  function startPinch() {
    const [id1, id2] = [...pointers.keys()].slice(0, 2);
    const p1 = pointers.get(id1), p2 = pointers.get(id2);
    const d = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    activePinch = { p1: id1, p2: id2, distance: d };
    _e.kind = 'pinchStart'; _e.distance = d;
    _e.midX = (p1.x + p2.x) / 2; _e.midY = (p1.y + p2.y) / 2;
    onGesture(_e);
  }

  function updatePinch() {
    const p1 = pointers.get(activePinch.p1), p2 = pointers.get(activePinch.p2);
    if (!p1 || !p2) return;
    const d = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    _e.kind = 'pinchMove'; _e.distance = d; _e.scale = d / activePinch.distance;
    _e.midX = (p1.x + p2.x) / 2; _e.midY = (p1.y + p2.y) / 2;
    onGesture(_e);
  }

  function endPinch() {
    _e.kind = 'pinchEnd';
    onGesture(_e);
    activePinch = null;
  }

  canvas.addEventListener('pointerdown',   onDown);
  canvas.addEventListener('pointermove',   onMove);
  canvas.addEventListener('pointerup',     onUp);
  canvas.addEventListener('pointercancel', onCancel);
  canvas.addEventListener('contextmenu', e => e.preventDefault());   // suppress right-click menu over game

  return {
    detach() {
      canvas.removeEventListener('pointerdown',   onDown);
      canvas.removeEventListener('pointermove',   onMove);
      canvas.removeEventListener('pointerup',     onUp);
      canvas.removeEventListener('pointercancel', onCancel);
      pointers.clear();
      activePinch = null;
    },
  };
}
```

## 3. Hard requirements (the craft lens will catch these)

### 3.1 ≤ 50ms latency (block)

PointerEvents fire synchronously. Your callback into `onGesture` must NOT do heavy work - emit the event, return immediately. The loop reads events on the next tick (≤ 16ms at 60Hz). Total budget input → physics impulse → render: ≤ 50ms.

### 3.2 Zero allocation per event (block at high event rate)

The `_e` scratch object above is pre-allocated. `onGesture(_e)` passes by reference; the receiver MUST consume immediately or copy out (the loop does this when it pushes events to its frame queue).

### 3.3 Multi-touch correctness (block when modality includes multi-touch)

Each finger has a unique `pointerId`. The `pointers` Map tracks each independently. Pinch detection only fires when exactly 2 are down (more = ambiguous; ignore or treat as multi-finger drag).

### 3.4 `touch-action: none` on the canvas (block on mobile)

The runtime composer is responsible for setting `canvas { touch-action: none; }` so the browser doesn't intercept gestures for scroll/zoom. Document this in `// Runtime contract:` at the top of your file so the runtime composer doesn't miss it.

### 3.5 No coordinate system drift (block)

Always convert client coords → world coords via `toWorld(clientX, clientY)` using `getBoundingClientRect()` + `worldBounds`. If the canvas resizes, your conversion stays correct (no cached scale factors).

### 3.6 PointerCapture for drag stability (block at scale)

`canvas.setPointerCapture(e.pointerId)` on down ensures move events keep flowing even if the pointer leaves the canvas during a drag. Without it, fast drags off-canvas miss `pointerup` and you get stuck `dragMove` state.

### 3.7 Suppress browser default behaviours that fight games (warn → block)

- `contextmenu` over the canvas → preventDefault (right-click).
- `touchstart` over canvas → CSS `touch-action: none` (handled by runtime composer; just document).
- `dragstart` over images in the canvas → preventDefault if your game has any `<img>` overlay.

## 4. Recipe

1. Read `research.md` §2.4 (gesture map) + envelope.
2. Draft `input-pointer.js` per §2. Tune `HOLD_MS` / `SWIPE_MS` / `SWIPE_MIN` per the game's feel - a precision-puzzle game wants HOLD_MS=400; a frantic action game wants HOLD_MS=180.
3. Self-test:
   - Static grep: no allocation per event.
   - Boot via runtime, drive synthetic input via `preview_eval` - `canvas.dispatchEvent(new PointerEvent('pointerdown', {pointerId:1, clientX:100, clientY:100}))` → verify a `dragStart` fires.
   - Multi-touch via two pointer ids - verify `pinchStart` fires when both are down.
4. Atomic commit.

## 5. What you do NOT do

- **You do not interpret gestures into game actions.** That's the loop. You emit gesture events; loop calls `physics.applyImpulse` / `objective.update` per its rules.
- **You do not own keyboard.** Sibling drawer.
- **You do not own gyro.** Sibling drawer (`game-input-gyro`) when declared.
- **You do not store gesture state across frames.** Each event is fire-and-forget; in-flight state is the `pointers` Map only (cleared on detach).

End with: `"game_input_<gameId>_<modality>: gestures=[tap,drag,pinch,hold,swipe], latencyMs=<N>, multi-touch=<yes|no> - commit pending lens."`
