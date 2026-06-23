# Sketch (imperative code layer)

A `sketch` is the escape hatch for interactions the logic-graph primitives cannot
express: per-pixel, temporal, or stateful effects (slit-scan, ring-buffer trails,
custom pointer mappings, particle toys). You write arbitrary JS; it runs in a
SANDBOXED iframe inside mm-composer and is composited as a real layer (the
per-layer effect / mask / blend stack applies on top), and it survives bake as
interactive HTML. Author the module at `source/<branch>/sketch-<id>.js`.

## The module contract

```js
export const controls = {
  // numeric controls auto-expose param:<key> input ports, so input-pointer /
  // op-math / state-* nodes can DRIVE them; non-numeric controls are panel-only.
  speed: { type: 'number', value: 1, min: 0, max: 5, step: 0.01 },
  hue:   { type: 'number', value: 200, min: 0, max: 360 },
  mode:  { type: 'select', value: 'a', options: ['a', 'b'] },
};
export function setup(ctx, env) { /* optional; runs once. env = { width, height } */ }
export function draw(ctx, frame, controls, content) { /* per frame */ }
```

- `ctx` - a 2D context on an OffscreenCanvas sized to the layer (`ctx.canvas.width/height`).
- `frame` - the canonical input frame (same shape logic nodes read), coords 0..1:
  `{ pointer:{x,y,isDown,clicked,downX,downY,upX,upY,hover}, touch, keyboard,
     scroll, gyro, audio:{level,pitch,band,beat}, dt, time }`.
- `controls.get(key)` - the live value: the schema default OVERLAID with any wired
  `param:<key>` binding (logic port or number-generator).
- `content` - `[{ kind:'image'|'video'|'camera', bitmap }]` from the node's `in`
  port; `bitmap` is a drawable source (`ctx.drawImage(content[0].bitmap, ...)`).

## Rules

- Keep `draw` allocation-light (it runs every frame). Persist state in module-scope
  variables (declared outside `draw`), not by reallocating per frame.
- Never call `getBoundingClientRect` or touch the DOM outside `ctx`.
- Clear what you need each frame (`ctx.clearRect(0,0,w,h)`) unless you WANT trails.
- The sketch owns its own layout: it draws in its own canvas space, full-bleed.
- On a compile/draw error the layer shows a labelled error box (never silent), so
  watch the composer while iterating.

## Recipes

### Pointer-follow (the "it just works" baseline)
```js
export const controls = { size:{type:'number',value:0.12,min:0.01,max:0.5,step:0.01} };
export function draw(ctx, frame, controls) {
  const w = ctx.canvas.width, h = ctx.canvas.height;
  ctx.clearRect(0, 0, w, h);
  const p = frame.pointer || { x:0.5, y:0.5 };
  ctx.fillStyle = '#6ee7ff';
  ctx.beginPath();
  ctx.arc(p.x*w, p.y*h, controls.get('size')*Math.min(w,h), 0, Math.PI*2);
  ctx.fill();
}
```

### Ring-buffer trail (stateful: keep recent pointer positions)
```js
const trail = [];
export const controls = { len:{type:'number',value:40,min:2,max:200,step:1} };
export function draw(ctx, frame, controls) {
  const w = ctx.canvas.width, h = ctx.canvas.height;
  trail.push({ x: frame.pointer.x*w, y: frame.pointer.y*h });
  while (trail.length > controls.get('len')) trail.shift();
  ctx.clearRect(0, 0, w, h);
  for (let i = 0; i < trail.length; i++) {
    ctx.globalAlpha = i / trail.length;
    ctx.beginPath(); ctx.arc(trail[i].x, trail[i].y, 8, 0, Math.PI*2); ctx.fill();
  }
  ctx.globalAlpha = 1;
}
```

### Slit-scan (per-row temporal delay of a wired camera)
Wire an `input-camera` node into the sketch's `in` content port, then:
```js
const frames = [];               // ring buffer of recent camera frames
export const controls = { depth:{type:'number',value:60,min:2,max:150,step:1} };
export function draw(ctx, frame, controls, content) {
  const w = ctx.canvas.width, h = ctx.canvas.height;
  const cam = content.find(c => c.kind === 'camera');
  if (!cam) { ctx.clearRect(0,0,w,h); return; }
  // snapshot this frame into the ring buffer
  const snap = new OffscreenCanvas(w, h);
  snap.getContext('2d').drawImage(cam.bitmap, 0, 0, w, h);
  frames.push(snap);
  const depth = controls.get('depth') | 0;
  while (frames.length > depth) frames.shift();
  // each row reads from a progressively older frame
  for (let y = 0; y < h; y++) {
    const age = Math.floor((y / h) * (frames.length - 1));
    const src = frames[frames.length - 1 - age] || frames[0];
    if (src) ctx.drawImage(src, 0, y, w, 1, 0, y, w, 1);
  }
}
```

## Wiring

- The sketch's `out` is a layer: wire it into the Interactive composer's `in` port.
- Drive a control from the graph: wire a logic node's output (or a number-generator)
  into the sketch's `param:<key>` port (the port exists for every numeric control).
- Add visual effects on top: wire `effect` nodes into the sketch like any layer; they
  run on the sketch's rendered output.
