/* ===========================================================================
   LOGICGRAPH - shared atomic node-graph engine (Blueprints / TouchDesigner style).

   A logic graph wires typed SOURCE nodes (pointer / camera detect / video OCR)
   through OPERATORS, CONTROL FLOW and STATE nodes into target params. The editor
   serializes a PROJECTION of the canvas (see LOGICGRAPH_DESIGN.md §3):

     logic = {
       nodes:   [ { id, kind, params } ],
       edges:   [ { from:{node,port,dtype}, to:{node,port,dtype} } ],
       outputs: [ { sourceNode, sourcePort, targetNode, targetParam } ],
     }

   `compile(logic) -> plan` topo-sorts the nodes once. Cycles are a compile error
   UNLESS they pass through a `state-*` node: state nodes read PREVIOUS-frame state
   so they break the dependency cycle (the back-edge is dropped from the topo sort).
   `tick(plan, inputs, ctx) -> outputs` evaluates one frame in topo order, memoizing
   each node's output ports; the returned map is keyed "<targetNode>.<param>" per
   logic.outputs, plus plan._ports[nodeId] for UI port preview.

   `event` ports are true ONLY on the frame they fire (edge-detected against the
   previous frame's value kept in plan.state). `state-*` nodes carry memory in
   plan.state[nodeId] and advance using inputs.dt.

   Self-contained sibling of sources.js (own finiteNumber / no DOM / no IO) so any
   tool iframe can `import { LogicGraph } from '../_shared/logicgraph.js'`. Reuses
   Sources primitives where the contract asks (Sources._interp easing in op-map;
   Sources.eval for wired number-generator inputs). Time / dt are passed in by the
   caller (each tool owns its own clock).
   =========================================================================== */

import { Sources } from './sources.js';

function finiteNumber(v, fallback) { const n = Number(v); return Number.isFinite(n) ? n : fallback; }
function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
function truthy(v) {
  if (v == null) return false;
  if (typeof v === 'number') return v !== 0;
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') return v.length > 0;
  if (typeof v === 'object') return true;
  return !!v;
}
function asNumber(v) {
  if (typeof v === 'number') return finiteNumber(v, 0);
  if (typeof v === 'boolean') return v ? 1 : 0;
  if (v && typeof v === 'object' && 'x' in v) return finiteNumber(v.x, 0);
  return finiteNumber(v, 0);
}
function vec2(x, y) { return { x: finiteNumber(x, 0), y: finiteNumber(y, 0) }; }
// color dtype: {r,g,b,a} components 0..1. extract*() return this shape.
function color(r, g, b, a) {
  return { r: clamp(finiteNumber(r, 0), 0, 1), g: clamp(finiteNumber(g, 0), 0, 1),
    b: clamp(finiteNumber(b, 0), 0, 1), a: a == null ? 1 : clamp(finiteNumber(a, 1), 0, 1) };
}

// state-* kinds break cycles: they read previous-frame state, so a back-edge
// into a state node does NOT count as a hard dependency for the topo sort.
function isStateKind(kind) { return typeof kind === 'string' && kind.indexOf('state-') === 0; }

export const LogicGraph = {

  // ── compile ────────────────────────────────────────────────────────────────
  // Parse the serialized subgraph into an executable plan. Topo-sort the nodes,
  // detect cycles (legal only through a state node), pre-resolve each node's input
  // wiring as plan.wiring[nodeId][inPort] = { node, port }.
  compile(logic) {
    logic = logic || {};
    const nodes = Array.isArray(logic.nodes) ? logic.nodes : [];
    const edges = Array.isArray(logic.edges) ? logic.edges : [];
    const outputs = Array.isArray(logic.outputs) ? logic.outputs : [];

    const byId = {};
    for (const n of nodes) { if (n && n.id != null) byId[n.id] = n; }

    // Per-node input wiring: wiring[node][inPort] = { node, port }.
    const wiring = {};
    for (const id in byId) wiring[id] = {};
    // Full dependency adjacency: edge A.out -> B.in means A must run before B.
    const deps = {};        // node -> Set of nodes it depends on
    const dependents = {};  // node -> Set of nodes depending on it
    for (const id in byId) { deps[id] = new Set(); dependents[id] = new Set(); }

    for (const e of edges) {
      if (!e || !e.from || !e.to) continue;
      const f = e.from, t = e.to;
      if (byId[t.node] == null) continue;
      wiring[t.node][t.port] = { node: f.node, port: f.port };
      if (byId[f.node] == null) continue;            // wired from a non-logic node
      if (f.node === t.node) continue;               // ignore trivial self-loop here
      deps[t.node].add(f.node);
      dependents[f.node].add(t.node);
    }

    const errors = [];

    // Cycle handling: a cycle is legal ONLY if it passes through a state-* node
    // (which reads last frame). For every back-edge found by DFS, if its HEAD is a
    // state node we drop that single edge (the state node breaks the cycle); else
    // we record a compile error on the offending nodes. We keep all other edges so
    // legitimate state-node fan-in (e.g. pick.r -> smooth.target) still orders the
    // smooth node AFTER pick.
    const WHITE = 0, GREY = 1, BLACK = 2;
    const color = {};
    for (const id in byId) color[id] = WHITE;
    const drop = {};  // "from->to" edges removed to break a legal state cycle
    const dfs = (id, stack) => {
      color[id] = GREY; stack.push(id);
      for (const d of dependents[id]) {
        const edgeKey = id + '->' + d;
        if (drop[edgeKey]) continue;
        if (color[d] === GREY) {
          // back-edge id->d closes a cycle (d is somewhere up the stack).
          const cyc = stack.slice(stack.indexOf(d));
          let breaker = null;
          for (let k = 0; k < cyc.length; k++) {
            const a = cyc[k], b = cyc[(k + 1) % cyc.length];
            if (isStateKind((byId[b] || {}).kind)) { breaker = a + '->' + b; break; }
          }
          if (breaker) { drop[breaker] = true; }
          else { for (const cn of cyc) errors.push({ node: cn, message: 'cycle does not pass through a state node' }); }
        } else if (color[d] === WHITE) {
          dfs(d, stack);
        }
      }
      color[id] = BLACK; stack.pop();
    };
    for (const id in byId) if (color[id] === WHITE) dfs(id, []);

    // Rebuild hard deps + dependents minus the dropped state back-edges.
    for (const id in byId) { deps[id] = new Set(); dependents[id] = new Set(); }
    for (const e of edges) {
      if (!e || !e.from || !e.to) continue;
      const f = e.from, t = e.to;
      if (byId[f.node] == null || byId[t.node] == null || f.node === t.node) continue;
      if (drop[f.node + '->' + t.node]) continue;
      deps[t.node].add(f.node);
      dependents[f.node].add(t.node);
    }

    // Kahn topo sort over the (now acyclic) hard edges.
    const indeg = {};
    for (const id in byId) indeg[id] = deps[id].size;
    const queue = [];
    for (const id in byId) if (indeg[id] === 0) queue.push(id);
    const order = [];
    while (queue.length) {
      const id = queue.shift();
      order.push(id);
      for (const d of dependents[id]) { indeg[d]--; if (indeg[d] === 0) queue.push(d); }
    }

    // Anything left with indeg>0 sits on a cycle that does NOT pass through a state
    // node (state back-edges were already dropped above): that is a compile error.
    if (order.length < Object.keys(byId).length) {
      for (const id in byId) {
        if (order.indexOf(id) === -1) {
          errors.push({ node: id, message: 'cycle does not pass through a state node' });
          order.push(id);  // still run it (best-effort) so a partial graph ticks
        }
      }
    }

    // Dedupe error entries (a node can appear in more than one cycle walk).
    const seen = {}, dedup = [];
    for (const er of errors) { const k = er.node + '|' + er.message; if (!seen[k]) { seen[k] = 1; dedup.push(er); } }

    const plan = {
      nodes: byId,
      order: order,
      wiring: wiring,
      outputs: outputs,
      errors: dedup,
      state: {},      // per-node persistent memory + event edge-detect cache
      _ports: {},     // last frame's resolved out-ports per node (UI preview)
    };
    return plan;
  },

  // ── tick ─────────────────────────────────────────────────────────────────--
  // Evaluate one frame in topo order. Memoize each node's out-ports for the frame
  // in plan._ports. Returns { "<targetNode>.<param>": value } for every output.
  tick(plan, inputs, ctx) {
    if (!plan) return {};
    inputs = inputs || {};
    ctx = ctx || {};
    const frame = {
      pointer: inputs.pointer || {}, touch: inputs.touch || {},
      keyboard: inputs.keyboard || {}, scroll: inputs.scroll || {},
      gyro: inputs.gyro || {}, audio: inputs.audio || {},
      streams: inputs.streams || {}, readback: inputs.readback || {},
      palettes: inputs.palettes || {},
      dt: finiteNumber(inputs.dt, 0), time: finiteNumber(inputs.time, ctx.time || 0),
    };
    const ports = {};
    plan._ports = ports;

    const readIn = (nodeId, inPort, fallback) => {
      const src = plan.wiring[nodeId] && plan.wiring[nodeId][inPort];
      if (!src) return fallback;
      const op = ports[src.node];
      if (op && (src.port in op)) return op[src.port];
      // Wired from a non-logic node (number-generator): eval via Sources.
      const ext = plan.nodes[src.node];
      if (!ext) return fallback;
      if (ext.spec || ext.params) {
        const spec = ext.spec || { kind: ext.kind, params: ext.params };
        if (spec && (spec.kind === 'number-generator' || spec.kind === 'timeline' || spec.sub)) {
          return finiteNumber(Sources.eval(spec, ctx), fallback);
        }
      }
      return fallback;
    };

    for (const id of plan.order) {
      const node = plan.nodes[id];
      if (!node) { ports[id] = {}; continue; }
      const ev = this.evaluators[node.kind];
      if (!ev) { ports[id] = {}; continue; }
      let out;
      try { out = ev(node, readIn, frame, ctx, plan.state); }
      catch (e) { out = {}; }
      ports[id] = out || {};
    }

    const outMap = {};
    for (const o of plan.outputs) {
      if (!o) continue;
      const op = ports[o.sourceNode];
      const val = op ? op[o.sourcePort] : undefined;
      outMap[o.targetNode + '.' + o.targetParam] = val;
    }
    outMap._ports = ports;
    return outMap;
  },

  // ── read ─────────────────────────────────────────────────────────────────--
  read(plan, outputs, targetNode, param) {
    if (!outputs) return undefined;
    return outputs[targetNode + '.' + param];
  },

  // helper: rising-edge detector keyed by node+slot, kept in plan.state.
  _rise(state, key, value) {
    const cache = state.__edge || (state.__edge = {});
    const prev = !!cache[key];
    const now = !!value;
    cache[key] = now;
    return now && !prev;
  },

  // ── per-kind evaluators ───────────────────────────────────────────────────--
  // signature: (node, read, frame, ctx, state) -> outPorts
  //   read(nodeId, inPort, fallback) pulls a wired input value.
  evaluators: {

    // ---- 2.1 input sources (map already-captured frame state to ports) --------
    'input-pointer'(node, read, frame, ctx, state) {
      const p = frame.pointer || {};
      const clicked = LogicGraph._rise(state, node.id + ':click', p.isDown) || !!p.clicked;
      return {
        x: finiteNumber(p.x, 0), y: finiteNumber(p.y, 0),
        isDown: !!p.isDown, clicked: clicked,
        downX: finiteNumber(p.downX, 0), downY: finiteNumber(p.downY, 0),
        upX: finiteNumber(p.upX, 0), upY: finiteNumber(p.upY, 0),
        hover: !!p.hover, pos: vec2(p.x, p.y),
      };
    },

    'input-touch'(node, read, frame, ctx, state) {
      const t = frame.touch || {};
      const tap = LogicGraph._rise(state, node.id + ':tap', t.isDown) || !!t.tap;
      return {
        count: finiteNumber(t.count, 0), pos: vec2((t.pos || {}).x, (t.pos || {}).y),
        touches: Array.isArray(t.touches) ? t.touches : [],
        isDown: !!t.isDown, center: vec2((t.center || {}).x, (t.center || {}).y),
        spread: finiteNumber(t.spread, 0), pinchDelta: finiteNumber(t.pinchDelta, 0),
        rotation: finiteNumber(t.rotation, 0), tap: tap,
      };
    },

    'input-keyboard'(node, read, frame, ctx, state) {
      const k = frame.keyboard || {};
      const filter = (node.params && node.params.key) || '';
      const isDown = filter ? (k.key === filter && !!k.isDown) : !!k.isDown;
      const pressed = LogicGraph._rise(state, node.id + ':press', isDown);
      const released = !isDown && !!(state.__kbWasDown && state.__kbWasDown[node.id]);
      (state.__kbWasDown || (state.__kbWasDown = {}))[node.id] = isDown;
      return {
        key: k.key != null ? String(k.key) : '', isDown: isDown,
        pressed: pressed, released: released,
        axisX: finiteNumber(k.axisX, 0), axisY: finiteNumber(k.axisY, 0),
      };
    },

    'input-scroll'(node, read, frame, ctx, state) {
      const s = frame.scroll || {};
      return {
        deltaY: finiteNumber(s.deltaY, 0), deltaX: finiteNumber(s.deltaX, 0),
        accumY: finiteNumber(s.accumY, 0), accumX: finiteNumber(s.accumX, 0),
        velocity: finiteNumber(s.velocity, 0),
      };
    },

    'input-gyro'(node, read, frame, ctx, state) {
      const g = frame.gyro || {};
      return {
        alpha: finiteNumber(g.alpha, 0), beta: finiteNumber(g.beta, 0),
        gamma: finiteNumber(g.gamma, 0),
        tilt: vec2(clamp(finiteNumber(g.beta, 0) / 90, -1, 1), clamp(finiteNumber(g.gamma, 0) / 90, -1, 1)),
        ready: !!g.ready,
      };
    },

    'input-audio'(node, read, frame, ctx, state) {
      const a = frame.audio || {};
      const beat = LogicGraph._rise(state, node.id + ':beat', a.beat) || !!a.beat;
      return {
        level: finiteNumber(a.level, 0), pitch: finiteNumber(a.pitch, 0),
        band: finiteNumber(a.band, 0), beat: beat,
        spectrum: { data: a.spectrum || new Float32Array(0), rate: 0 },
        bands: { data: a.bands || new Float32Array(0), rate: 0 },
      };
    },

    'input-camera'(node, read, frame, ctx, state) {
      return { stream: String(node.id), ready: !!(frame.streams && frame.streams[node.id]) };
    },

    'input-video'(node, read, frame, ctx, state) {
      const st = (frame.streams && frame.streams[node.id]) || {};
      return { stream: String(node.id), t: finiteNumber(st.t, 0), playing: !!st.playing };
    },

    // ---- 2.2 processors (read a stream handle, map detections to ports) -------
    'vision-detect'(node, read, frame, ctx, state) {
      const handle = read(node.id, 'stream', null);
      const st = handle != null ? (frame.streams && frame.streams[handle]) : null;
      const dets = (st && Array.isArray(st.detections)) ? st.detections : [];
      const present = dets.length > 0;
      // Detection selector. Default `primary` = dets[0] (the legacy behavior).
      // With more than one detection present (e.g. detector=hand running two
      // hands) `hand` addresses a SPECIFIC one, so two vision-detect nodes can
      // read two different hands: `leftmost`/`rightmost` pick by on-screen x
      // (self-consistent with the landmark coords a shape/mask reads off the
      // same det), `second` = dets[1]. Selection never changes present/count
      // (those stay global); pos/region/gesture/confidence + the named landmark
      // points all reflect the SELECTED detection.
      const which = (node.params && node.params.hand) || 'primary';
      let first = dets[0] || null;
      if (dets.length > 1) {
        if (which === 'second') first = dets[1];
        else if (which === 'leftmost') first = dets.reduce((a, b) => (b.x < a.x ? b : a), dets[0]);
        else if (which === 'rightmost') first = dets.reduce((a, b) => (b.x > a.x ? b : a), dets[0]);
      }
      // Named landmark vector2 ports read the SELECTED detection's named point
      // (hand: wrist/thumbTip/indexTip/middleTip/ringTip/pinkyTip; face:
      // nose/leftEye/rightEye), produced by logicvision normalizeMpResult. A
      // missing point degrades to {x:0,y:0} like every other vector2 port here.
      const pt = (name) => (first && first[name]) ? vec2(first[name].x, first[name].y) : vec2(0, 0);
      return {
        present: present, count: dets.length,
        pos: first ? vec2(first.x, first.y) : vec2(0, 0),
        region: first ? { x: finiteNumber(first.x, 0), y: finiteNumber(first.y, 0), w: finiteNumber(first.w, 0), h: finiteNumber(first.h, 0) } : { x: 0, y: 0, w: 0, h: 0 },
        gesture: first && first.gesture != null ? String(first.gesture) : '',
        confidence: first ? finiteNumber(first.confidence, 0) : 0,
        // hand landmark points (vector2, normalized 0..1)
        wrist: pt('wrist'), thumbTip: pt('thumbTip'), indexTip: pt('indexTip'),
        middleTip: pt('middleTip'), ringTip: pt('ringTip'), pinkyTip: pt('pinkyTip'),
        // face landmark points (vector2, normalized 0..1)
        nose: pt('nose'), leftEye: pt('leftEye'), rightEye: pt('rightEye'),
      };
    },

    'vision-ocr'(node, read, frame, ctx, state) {
      const handle = read(node.id, 'stream', null);
      const st = handle != null ? (frame.streams && frame.streams[handle]) : null;
      const ocr = (st && st.ocr) || {};
      const text = ocr.text != null ? String(ocr.text) : '';
      const words = Array.isArray(ocr.words) ? ocr.words : [];
      const query = (node.params && node.params.query) || '';
      const matched = !!query && text.toLowerCase().indexOf(String(query).toLowerCase()) !== -1;
      let region = { x: 0, y: 0, w: 0, h: 0 };
      if (words.length && words[0].bbox) { const b = words[0].bbox; region = { x: finiteNumber(b.x, 0), y: finiteNumber(b.y, 0), w: finiteNumber(b.w, 0), h: finiteNumber(b.h, 0) }; }
      return { text: text, matched: matched, region: region, count: words.length };
    },

    // ---- palette extraction (source over a wired image) -----------------------
    // The N dominant colors of a wired image. Extraction (image decode + median
    // cut) runs in the RUNTIME (mmcomposer / slimPlayer) - canvas / Image are not
    // available here in the pure engine - and the resulting colors are entered
    // into frame.palettes[node.id] = { colors:[{r,g,b,a}], dominant:{r,g,b,a} },
    // EXACTLY how vision-detect results reach the engine via frame.streams. The
    // runtime caches by image-url + count so it never re-extracts per frame. This
    // evaluator just maps the cached colors onto the node's typed output ports:
    //   color0..color7 (dtype color), dominant (color),
    //   domR / domG / domB (number 0..1) so the dominant can ALSO drive numeric
    //   params (e.g. an effect color channel) through the normal logic binding.
    'palette'(node, read, frame, ctx, state) {
      const pal = (frame.palettes && frame.palettes[node.id]) || {};
      const colors = Array.isArray(pal.colors) ? pal.colors : [];
      const count = Math.max(2, Math.min(8, Math.floor(finiteNumber(node.params && node.params.count, 5))));
      const out = {};
      for (let i = 0; i < 8; i++) {
        const c = colors[i] || colors[colors.length ? (i % colors.length) : 0] || null;
        out['color' + i] = c ? color(c.r, c.g, c.b, c.a) : color(0, 0, 0, 1);
      }
      const dom = pal.dominant || colors[0] || null;
      const dc = dom ? color(dom.r, dom.g, dom.b, dom.a) : color(0, 0, 0, 1);
      out.dominant = dc;
      out.domR = dc.r; out.domG = dc.g; out.domB = dc.b;
      out.ready = colors.length > 0;
      out.count = Math.min(count, colors.length);
      return out;
    },

    // ---- 2.3 literals ---------------------------------------------------------
    'value-bool'(node) { return { value: !!(node.params && node.params.value) }; },
    'value-string'(node) { return { value: String((node.params && node.params.value) || '') }; },
    'value-vec2'(node) { const p = node.params || {}; return { value: vec2(p.x, p.y) }; },

    // ---- 2.4 operators (pure) -------------------------------------------------
    'op-math'(node, read) {
      const a = asNumber(read(node.id, 'a', 0)), b = asNumber(read(node.id, 'b', 0));
      const op = (node.params && node.params.op) || 'add';
      let r = 0;
      switch (op) {
        case 'add': r = a + b; break;
        case 'sub': r = a - b; break;
        case 'mul': r = a * b; break;
        case 'div': r = b === 0 ? 0 : a / b; break;
        case 'mod': r = b === 0 ? 0 : a % b; break;
        case 'min': r = Math.min(a, b); break;
        case 'max': r = Math.max(a, b); break;
        case 'pow': r = Math.pow(a, b); break;
        case 'atan2': r = Math.atan2(a, b); break;
        default: r = a + b;
      }
      return { r: finiteNumber(r, 0) };
    },

    'op-unary'(node, read) {
      const a = asNumber(read(node.id, 'a', 0));
      const op = (node.params && node.params.op) || 'abs';
      let r = 0;
      switch (op) {
        case 'abs': r = Math.abs(a); break;
        case 'neg': r = -a; break;
        case 'floor': r = Math.floor(a); break;
        case 'round': r = Math.round(a); break;
        case 'sin': r = Math.sin(a); break;
        case 'cos': r = Math.cos(a); break;
        case 'sqrt': r = a < 0 ? 0 : Math.sqrt(a); break;
        case 'sign': r = Math.sign(a); break;
        default: r = Math.abs(a);
      }
      return { r: finiteNumber(r, 0) };
    },

    'op-compare'(node, read) {
      const a = asNumber(read(node.id, 'a', 0)), b = asNumber(read(node.id, 'b', 0));
      const op = (node.params && node.params.op) || 'eq';
      const eps = finiteNumber(node.params && node.params.epsilon, 0);
      let r = false;
      switch (op) {
        case 'eq': r = Math.abs(a - b) <= eps; break;
        case 'ne': r = Math.abs(a - b) > eps; break;
        case 'lt': r = a < b - eps; break;
        case 'gt': r = a > b + eps; break;
        case 'le': r = a <= b + eps; break;
        case 'ge': r = a >= b - eps; break;
        default: r = a === b;
      }
      return { r: r };
    },

    'op-logic'(node, read) {
      const a = truthy(read(node.id, 'a', false)), b = truthy(read(node.id, 'b', false));
      const op = (node.params && node.params.op) || 'and';
      let r = false;
      switch (op) {
        case 'and': r = a && b; break;
        case 'or': r = a || b; break;
        case 'xor': r = a !== b; break;
        case 'nand': r = !(a && b); break;
        case 'nor': r = !(a || b); break;
        default: r = a && b;
      }
      return { r: r };
    },

    'op-map'(node, read) {
      const x = asNumber(read(node.id, 'x', 0));
      const p = node.params || {};
      const inMin = finiteNumber(p.inMin, 0), inMax = finiteNumber(p.inMax, 1);
      const outMin = finiteNumber(p.outMin, 0), outMax = finiteNumber(p.outMax, 1);
      const span = (inMax - inMin) || 1;
      let f = (x - inMin) / span;
      if (p.clamp) f = clamp(f, 0, 1);
      // Reuse Sources._interp easing names via a 2-key ramp so easing stays in sync.
      const ease = p.ease || 'linear';
      if (ease !== 'linear') {
        // Reuse Sources._interp easing (linear/in/out/inout) on the 0..1 fraction.
        f = Sources._interp([{ t: 0, value: 0, ease: ease }, { t: 1, value: 1 }], clamp(f, 0, 1));
      }
      let r = outMin + (outMax - outMin) * f;
      if (p.clamp) r = clamp(r, Math.min(outMin, outMax), Math.max(outMin, outMax));
      return { r: finiteNumber(r, 0) };
    },

    'op-vector'(node, read) {
      const mode = (node.params && node.params.mode) || 'make';
      if (mode === 'make') {
        return { v: vec2(asNumber(read(node.id, 'x', 0)), asNumber(read(node.id, 'y', 0))) };
      }
      if (mode === 'break') {
        const v = read(node.id, 'v', null) || { x: 0, y: 0 };
        return { x: finiteNumber(v.x, 0), y: finiteNumber(v.y, 0) };
      }
      const a = read(node.id, 'a', null) || { x: 0, y: 0 };
      const b = read(node.id, 'b', null) || { x: 0, y: 0 };
      if (mode === 'distance') {
        const dx = finiteNumber(a.x, 0) - finiteNumber(b.x, 0), dy = finiteNumber(a.y, 0) - finiteNumber(b.y, 0);
        return { d: Math.sqrt(dx * dx + dy * dy) };
      }
      if (mode === 'add') { return { v: vec2(finiteNumber(a.x, 0) + finiteNumber(b.x, 0), finiteNumber(a.y, 0) + finiteNumber(b.y, 0)) }; }
      if (mode === 'scale') { const s = asNumber(read(node.id, 's', 1)); return { v: vec2(finiteNumber(a.x, 0) * s, finiteNumber(a.y, 0) * s) }; }
      if (mode === 'lerp') { const t = clamp(asNumber(read(node.id, 't', 0)), 0, 1); return { v: vec2(finiteNumber(a.x, 0) + (finiteNumber(b.x, 0) - finiteNumber(a.x, 0)) * t, finiteNumber(a.y, 0) + (finiteNumber(b.y, 0) - finiteNumber(a.y, 0)) * t) }; }
      return { v: vec2(0, 0) };
    },

    'op-tostring'(node, read) {
      const a = read(node.id, 'a', 0);
      const tmpl = (node.params && node.params.template) || '';
      let s;
      if (a && typeof a === 'object' && 'x' in a) s = '(' + finiteNumber(a.x, 0) + ', ' + finiteNumber(a.y, 0) + ')';
      else s = String(a);
      if (tmpl) {
        const ax = (a && typeof a === 'object') ? finiteNumber(a.x, 0) : a;
        const ay = (a && typeof a === 'object') ? finiteNumber(a.y, 0) : '';
        s = tmpl.replace(/\{x\}/g, ax).replace(/\{y\}/g, ay).replace(/\{a\}/g, String(a));
      }
      return { s: String(s) };
    },

    // ---- 2.5 control flow -----------------------------------------------------
    'flow-if'(node, read) {
      const cond = truthy(read(node.id, 'cond', false));
      return { r: cond ? read(node.id, 'then', undefined) : read(node.id, 'else', undefined) };
    },

    'flow-gate'(node, read, frame, ctx, state) {
      const open = truthy(read(node.id, 'open', false));
      const holdLast = !(node.params && node.params.holdLast === false);
      const slot = (state.__gate || (state.__gate = {}));
      if (open) { slot[node.id] = read(node.id, 'value', undefined); return { r: slot[node.id] }; }
      return { r: holdLast ? slot[node.id] : undefined };
    },

    // Bounded per-frame loop: re-reads `body` while `cond` holds, capped by
    // maxIterations. NEVER unbounded. Since inputs are frame-constant the loop is
    // really an accumulator over a fixed cap (cond is a guard, not a mutator).
    'flow-while'(node, read) {
      const max = Math.max(0, Math.floor(finiteNumber(node.params && node.params.maxIterations, 0)));
      let count = 0, last = 0;
      while (count < max && truthy(read(node.id, 'cond', false))) {
        last = asNumber(read(node.id, 'body', 0));
        count++;
      }
      return { count: count, last: last };
    },

    // Runs `body` n times with i=0..n-1 in ctx; emits sum + per-iteration vector.
    'flow-repeat'(node, read, frame, ctx) {
      const n = Math.max(0, Math.floor(asNumber(read(node.id, 'n', 0))));
      const cap = Math.min(n, 100000);  // hard ceiling, no unbounded loops
      const values = [];
      let sum = 0;
      const baseI = ctx.index || 0;
      for (let i = 0; i < cap; i++) {
        ctx.index = i;
        const v = asNumber(read(node.id, 'body', 0));
        values.push(v); sum += v;
      }
      ctx.index = baseI;
      return { sum: finiteNumber(sum, 0), values: values };
    },

    // ---- 2.6 state (memory in plan.state; legal cycle breakers) ---------------
    'state-counter'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { count: 0 }));
      const step = finiteNumber(node.params && node.params.step, 1);
      const wrap = finiteNumber(node.params && node.params.wrap, 0);
      if (LogicGraph._rise(state, node.id + ':reset', truthy(read(node.id, 'reset', false)))) s.count = 0;
      if (LogicGraph._rise(state, node.id + ':inc', truthy(read(node.id, 'inc', false)))) {
        s.count += step;
        if (wrap > 0) { s.count = ((s.count % wrap) + wrap) % wrap; }
      }
      return { count: s.count };
    },

    'state-toggle'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { on: !!(node.params && node.params.initial) }));
      if (LogicGraph._rise(state, node.id + ':flip', truthy(read(node.id, 'flip', false)))) s.on = !s.on;
      return { on: s.on };
    },

    'state-latch'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { value: undefined }));
      const set = truthy(read(node.id, 'set', false));
      if (LogicGraph._rise(state, node.id + ':set', set)) s.value = read(node.id, 'hold', undefined);
      return { value: s.value };
    },

    'state-timer'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { elapsed: 0, running: !!(node.params && node.params.autostart) }));
      if (LogicGraph._rise(state, node.id + ':start', truthy(read(node.id, 'start', false)))) s.running = true;
      if (LogicGraph._rise(state, node.id + ':stop', truthy(read(node.id, 'stop', false)))) s.running = false;
      if (s.running) s.elapsed += Math.max(0, finiteNumber(frame.dt, 0));
      return { elapsed: s.elapsed, running: s.running };
    },

    // Critically-damped pursuit toward `target` (the smoothing every pointer-driven
    // value should pass through). x'' = -k*(x-target) - c*x' with c = 2*sqrt(k).
    'state-smooth'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { value: 0, vel: 0, init: false }));
      const target = asNumber(read(node.id, 'target', 0));
      if (!s.init) { s.value = target; s.init = true; }
      const stiffness = Math.max(0.0001, finiteNumber(node.params && node.params.stiffness, 120));
      const damping = finiteNumber(node.params && node.params.damping, 2 * Math.sqrt(stiffness));
      const dt = clamp(finiteNumber(frame.dt, 0), 0, 0.064);
      const accel = -stiffness * (s.value - target) - damping * s.vel;
      s.vel += accel * dt;
      s.value += s.vel * dt;
      return { value: finiteNumber(s.value, 0) };
    },

    // ---- 2.65 CHOP signal generators / operators / channel bridges -----------
    // Low-frequency oscillator. Stateless (phase from frame.time) so it is
    // deterministic and needs no cycle-breaker.
    'gen-lfo'(node, read, frame) {
      const p = node.params || {};
      const freq = finiteNumber(p.freq, 1), phase = finiteNumber(p.phase, 0);
      const lo = finiteNumber(p.lo, 0), hi = finiteNumber(p.hi, 1);
      let x = (finiteNumber(frame.time, 0) * freq + phase) % 1; if (x < 0) x += 1;
      let w;
      if (p.wave === 'tri') w = 1 - Math.abs(x * 2 - 1);
      else if (p.wave === 'saw') w = x;
      else if (p.wave === 'square') w = x < 0.5 ? 0 : 1;
      else w = 0.5 - 0.5 * Math.cos(x * 6.283185307);
      return { value: lo + (hi - lo) * w, phase: x };
    },
    // Smooth 1D value noise over time.
    'gen-noise'(node, read, frame) {
      const p = node.params || {};
      const t = finiteNumber(frame.time, 0) * finiteNumber(p.speed, 1) + finiteNumber(p.seed, 0);
      const lo = finiteNumber(p.lo, 0), hi = finiteNumber(p.hi, 1);
      const i = Math.floor(t), f = t - i;
      const h = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
      const u = f * f * (3 - 2 * f);
      return { value: lo + (hi - lo) * (h(i) * (1 - u) + h(i + 1) * u) };
    },
    // Wall clock: seconds, integer frame count, fps.
    'gen-clock'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { frame: 0 }));
      s.frame++;
      const dt = clamp(finiteNumber(frame.dt, 0), 0, 1);
      return { time: finiteNumber(frame.time, 0), frame: s.frame, fps: dt > 0 ? 1 / dt : 0 };
    },
    // Derivative: rate of change per second.
    'op-slope'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { prev: 0, init: false }));
      const x = asNumber(read(node.id, 'x', 0));
      const dt = clamp(finiteNumber(frame.dt, 0), 1e-4, 1);
      if (!s.init) { s.prev = x; s.init = true; }
      const slope = (x - s.prev) / dt; s.prev = x;
      return { slope: finiteNumber(slope, 0) };
    },
    // One-pole low/high-pass filter.
    'chop-filter'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { y: 0, init: false }));
      const x = asNumber(read(node.id, 'x', 0));
      const k = clamp(finiteNumber(node.params && node.params.cutoff, 0.2), 0, 1);
      if (!s.init) { s.y = x; s.init = true; }
      s.y += k * (x - s.y);
      return { value: (node.params && node.params.mode === 'high') ? (x - s.y) : s.y };
    },
    // Delay a number by N frames (ring buffer).
    'state-delay'(node, read, frame, ctx, state) {
      const n = Math.max(1, Math.min(240, Math.round(finiteNumber(node.params && node.params.frames, 8))));
      const s = (state[node.id] || (state[node.id] = { buf: [], n }));
      if (s.n !== n) { s.buf = []; s.n = n; }
      const x = asNumber(read(node.id, 'x', 0));
      s.buf.push(x); while (s.buf.length > n) s.buf.shift();
      return { value: s.buf.length >= n ? s.buf[0] : x };
    },
    // ADSR envelope driven by a gate event/boolean.
    'state-trigger'(node, read, frame, ctx, state) {
      const s = (state[node.id] || (state[node.id] = { v: 0, peaked: false }));
      const p = node.params || {};
      const a = Math.max(1e-3, finiteNumber(p.attack, 0.05)), d = Math.max(1e-3, finiteNumber(p.decay, 0.1));
      const sus = clamp(finiteNumber(p.sustain, 0.6), 0, 1), rel = Math.max(1e-3, finiteNumber(p.release, 0.3));
      const dt = clamp(finiteNumber(frame.dt, 0), 0, 0.064);
      const gate = truthy(read(node.id, 'gate', false));
      if (gate) {
        if (!s.peaked) { s.v += dt / a; if (s.v >= 1) { s.v = 1; s.peaked = true; } }
        else { s.v += (sus - s.v) * Math.min(1, dt / d); }
      } else {
        s.peaked = false; s.v += (0 - s.v) * Math.min(1, dt / rel); if (s.v < 1e-4) s.v = 0;
      }
      return { value: clamp(s.v, 0, 1) };
    },
    // Record a scalar into a rolling CHANNEL (oldest->newest) - a scope source.
    'state-trail'(node, read, frame, ctx, state) {
      const n = Math.max(2, Math.min(4096, Math.round(finiteNumber(node.params && node.params.length, 128))));
      const s = (state[node.id] || (state[node.id] = { data: new Float32Array(n), n, head: 0, count: 0 }));
      if (s.n !== n) { s.data = new Float32Array(n); s.n = n; s.head = 0; s.count = 0; }
      s.data[s.head] = asNumber(read(node.id, 'x', 0)); s.head = (s.head + 1) % n; if (s.count < n) s.count++;
      const out = new Float32Array(s.count);
      for (let i = 0; i < s.count; i++) out[i] = s.data[(s.head - s.count + i + n * 2) % n];
      return { channel: { data: out, rate: 0 } };
    },
    // Channel -> number: read one sample by index or by phase (0..1).
    'chan-sample'(node, read) {
      const ch = read(node.id, 'channel', null);
      const data = ch && ch.data; if (!data || !data.length) return { value: 0 };
      let idx;
      if (node.params && node.params.mode === 'phase') idx = Math.round(clamp(asNumber(read(node.id, 'phase', 0)), 0, 1) * (data.length - 1));
      else idx = Math.round(asNumber(read(node.id, 'index', 0)));
      idx = Math.max(0, Math.min(data.length - 1, idx));
      return { value: finiteNumber(data[idx], 0) };
    },
    // Channel -> number: reduce (min/max/avg/rms/sum).
    'chan-analyze'(node, read) {
      const ch = read(node.id, 'channel', null);
      const data = ch && ch.data; if (!data || !data.length) return { value: 0 };
      const mode = (node.params && node.params.mode) || 'avg';
      let mn = Infinity, mx = -Infinity, sum = 0, sq = 0;
      for (let i = 0; i < data.length; i++) { const v = data[i]; if (v < mn) mn = v; if (v > mx) mx = v; sum += v; sq += v * v; }
      const n = data.length;
      const r = mode === 'min' ? mn : mode === 'max' ? mx : mode === 'sum' ? sum : mode === 'rms' ? Math.sqrt(sq / n) : sum / n;
      return { value: finiteNumber(r, 0) };
    },

    // ---- 2.7 output sink ------------------------------------------------------
    'output-binding'(node, read) {
      return { value: asNumber(read(node.id, 'value', 0)) };
    },

    // ---- audio output (synth SINK) --------------------------------------------
    // audio-out is a SINK: it consumes wired logic values (or its own control
    // defaults) and republishes them as resolved out-ports so the runtime bridge
    // can read them and push them into LogicAudio.set() each frame. The actual
    // WebAudio graph lives in logicaudio.js (gesture-gated); the engine just
    // resolves the parameter values deterministically. `trigger` is edge-detected
    // here so the bridge gets a one-frame note-on pulse. waveform comes from the
    // node control (no numeric input). Numeric inputs fall back to the control
    // value when unwired, so a bare audio-out still plays a steady tone.
    'audio-out'(node, read, frame, ctx, state) {
      const p = node.params || {};
      const freq = asNumber(read(node.id, 'frequency', finiteNumber(p.frequency, 220)));
      const gain = clamp(asNumber(read(node.id, 'gain', finiteNumber(p.gain, 0.2))), 0, 1);
      const cutoff = asNumber(read(node.id, 'cutoff', finiteNumber(p.cutoff, 8000)));
      const wave = (typeof p.waveform === 'string') ? p.waveform : 'sine';
      const trigger = LogicGraph._rise(state, node.id + ':trig', truthy(read(node.id, 'trigger', false)));
      return {
        frequency: finiteNumber(freq, 220), gain: gain,
        cutoff: finiteNumber(cutoff, 8000), waveform: wave, trigger: trigger,
      };
    },
  },
};
