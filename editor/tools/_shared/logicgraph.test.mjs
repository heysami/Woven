/* ===========================================================================
   LOGICGRAPH test harness - standalone, no DOM, no deps.
   Run:  node editor/tools/_shared/logicgraph.test.mjs
   Exercises operators, op-map easing, flow-if branch, flow-while bound, a
   state-counter across frames, state-smooth convergence, a topo-ordered
   multi-node graph, and a non-state cycle compile error. Prints PASS/FAIL per
   case + a final summary; exits non-zero on any failure.
   =========================================================================== */

// logicgraph.js / sources.js are ESM but live in a dir with no package.json
// "type":"module", so Node classifies bare .js as CommonJS. The browser/editor
// loads them as ESM directly; here we evaluate them as ESM via data: URLs (no
// edit to any existing file, no added package.json). The import graph
// (logicgraph -> sources) is preserved by rewriting the relative specifier to a
// data: URL too.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dir = dirname(fileURLToPath(import.meta.url));
function dataUrl(src) { return 'data:text/javascript;base64,' + Buffer.from(src, 'utf8').toString('base64'); }
const sourcesUrl = dataUrl(readFileSync(join(__dir, 'sources.js'), 'utf8'));
let lgSrc = readFileSync(join(__dir, 'logicgraph.js'), 'utf8');
lgSrc = lgSrc.replace(/from\s+['"]\.\/sources\.js['"]/, "from '" + sourcesUrl + "'");
const { LogicGraph } = await import(dataUrl(lgSrc));

let passed = 0, failed = 0;
function ok(name, cond, detail) {
  if (cond) { passed++; console.log('PASS  ' + name); }
  else { failed++; console.log('FAIL  ' + name + (detail != null ? '  -> ' + detail : '')); }
}
function approx(a, b, eps) { return Math.abs(a - b) <= (eps == null ? 1e-6 : eps); }

// helper: compile a graph then tick once with given inputs.
function once(logic, inputs, ctx) {
  const plan = LogicGraph.compile(logic);
  return { plan, out: LogicGraph.tick(plan, inputs || {}, ctx || {}) };
}
function ports(out, nodeId) { return out._ports[nodeId] || {}; }

// ── op-math ──────────────────────────────────────────────────────────────────
(function () {
  const cases = [['add', 2, 3, 5], ['sub', 7, 4, 3], ['mul', 3, 4, 12], ['div', 8, 2, 4],
    ['div', 1, 0, 0], ['mod', 7, 3, 1], ['min', 5, 2, 2], ['max', 5, 2, 5], ['pow', 2, 10, 1024]];
  let good = true;
  for (const [op, a, b, exp] of cases) {
    // Feed a,b via two vec2 literals (their .x is read as a number by op-math).
    const g = {
      nodes: [
        { id: 'va', kind: 'value-vec2', params: { x: a, y: 0 } },
        { id: 'vb', kind: 'value-vec2', params: { x: b, y: 0 } },
        { id: 'm', kind: 'op-math', params: { op } },
      ],
      edges: [
        { from: { node: 'va', port: 'value' }, to: { node: 'm', port: 'a' } },
        { from: { node: 'vb', port: 'value' }, to: { node: 'm', port: 'b' } },
      ],
      outputs: [{ sourceNode: 'm', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
    };
    const { out } = once(g, {});
    if (!approx(out['T.v'], exp)) { good = false; console.log('   op-math ' + op + ' got ' + out['T.v'] + ' want ' + exp); }
  }
  ok('op-math all ops', good);
})();

// ── op-unary / op-compare / op-logic ───────────────────────────────────────--
(function () {
  const g = {
    nodes: [
      { id: 'a', kind: 'value-vec2', params: { x: -4, y: 0 } },
      { id: 'u', kind: 'op-unary', params: { op: 'abs' } },
    ],
    edges: [{ from: { node: 'a', port: 'value' }, to: { node: 'u', port: 'a' } }],
    outputs: [{ sourceNode: 'u', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
  };
  ok('op-unary abs(-4)=4', approx(once(g, {}).out['T.v'], 4));

  const gc = {
    nodes: [
      { id: 'a', kind: 'value-vec2', params: { x: 3, y: 0 } },
      { id: 'b', kind: 'value-vec2', params: { x: 5, y: 0 } },
      { id: 'c', kind: 'op-compare', params: { op: 'lt' } },
    ],
    edges: [
      { from: { node: 'a', port: 'value' }, to: { node: 'c', port: 'a' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'c', port: 'b' } },
    ],
    outputs: [{ sourceNode: 'c', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
  };
  ok('op-compare 3<5 true', once(gc, {}).out['T.v'] === true);

  const gl = {
    nodes: [
      { id: 'a', kind: 'value-bool', params: { value: true } },
      { id: 'b', kind: 'value-bool', params: { value: false } },
      { id: 'x', kind: 'op-logic', params: { op: 'xor' } },
    ],
    edges: [
      { from: { node: 'a', port: 'value' }, to: { node: 'x', port: 'a' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'x', port: 'b' } },
    ],
    outputs: [{ sourceNode: 'x', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
  };
  ok('op-logic xor(t,f) true', once(gl, {}).out['T.v'] === true);
})();

// ── op-vector ─────────────────────────────────────────────────────────────--
(function () {
  const g = {
    nodes: [
      { id: 'a', kind: 'value-vec2', params: { x: 0, y: 0 } },
      { id: 'b', kind: 'value-vec2', params: { x: 3, y: 4 } },
      { id: 'd', kind: 'op-vector', params: { mode: 'distance' } },
    ],
    edges: [
      { from: { node: 'a', port: 'value' }, to: { node: 'd', port: 'a' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'd', port: 'b' } },
    ],
    outputs: [{ sourceNode: 'd', sourcePort: 'd', targetNode: 'T', targetParam: 'v' }],
  };
  ok('op-vector distance (0,0)->(3,4)=5', approx(once(g, {}).out['T.v'], 5));
})();

// ── op-map easing (reuses Sources._interp) ─────────────────────────────────--
(function () {
  function mapAt(ease, x) {
    const g = {
      nodes: [
        { id: 'in', kind: 'value-vec2', params: { x: x, y: 0 } },
        { id: 'm', kind: 'op-map', params: { inMin: 0, inMax: 1, outMin: 0, outMax: 1, clamp: true, ease: ease } },
      ],
      edges: [{ from: { node: 'in', port: 'value' }, to: { node: 'm', port: 'x' } }],
      outputs: [{ sourceNode: 'm', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
    };
    return once(g, {}).out['T.v'];
  }
  ok('op-map linear 0.5=0.5', approx(mapAt('linear', 0.5), 0.5));
  ok('op-map ease-in 0.5=0.25', approx(mapAt('in', 0.5), 0.25));
  ok('op-map ease-out 0.5=0.75', approx(mapAt('out', 0.5), 0.75));
  ok('op-map ease-inout 0.5=0.5', approx(mapAt('inout', 0.5), 0.5));
  ok('op-map clamp upper', approx(mapAt('linear', 2), 1));
  // remap range: 0..10 -> 0..100, x=5 -> 50
  const gr = {
    nodes: [
      { id: 'in', kind: 'value-vec2', params: { x: 5, y: 0 } },
      { id: 'm', kind: 'op-map', params: { inMin: 0, inMax: 10, outMin: 0, outMax: 100, clamp: false, ease: 'linear' } },
    ],
    edges: [{ from: { node: 'in', port: 'value' }, to: { node: 'm', port: 'x' } }],
    outputs: [{ sourceNode: 'm', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
  };
  ok('op-map remap 0..10->0..100 @5=50', approx(once(gr, {}).out['T.v'], 50));
})();

// ── flow-if branch ─────────────────────────────────────────────────────────--
(function () {
  function branch(condVal) {
    const g = {
      nodes: [
        { id: 'c', kind: 'value-bool', params: { value: condVal } },
        { id: 't', kind: 'value-vec2', params: { x: 111, y: 0 } },
        { id: 'e', kind: 'value-vec2', params: { x: 222, y: 0 } },
        { id: 'if', kind: 'flow-if', params: {} },
      ],
      edges: [
        { from: { node: 'c', port: 'value' }, to: { node: 'if', port: 'cond' } },
        { from: { node: 't', port: 'value' }, to: { node: 'if', port: 'then' } },
        { from: { node: 'e', port: 'value' }, to: { node: 'if', port: 'else' } },
      ],
      outputs: [{ sourceNode: 'if', sourcePort: 'r', targetNode: 'T', targetParam: 'v' }],
    };
    return once(g, {}).out['T.v'];
  }
  ok('flow-if true -> then', approx(branch(true).x, 111));
  ok('flow-if false -> else', approx(branch(false).x, 222));
})();

// ── flow-while bound enforcement ────────────────────────────────────────────-
(function () {
  // cond always true; body always 1. Must stop exactly at maxIterations, never hang.
  const g = {
    nodes: [
      { id: 'c', kind: 'value-bool', params: { value: true } },
      { id: 'b', kind: 'value-vec2', params: { x: 1, y: 0 } },
      { id: 'w', kind: 'flow-while', params: { maxIterations: 7 } },
    ],
    edges: [
      { from: { node: 'c', port: 'value' }, to: { node: 'w', port: 'cond' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'w', port: 'body' } },
    ],
    outputs: [
      { sourceNode: 'w', sourcePort: 'count', targetNode: 'T', targetParam: 'c' },
      { sourceNode: 'w', sourcePort: 'last', targetNode: 'T', targetParam: 'l' },
    ],
  };
  const { out } = once(g, {});
  ok('flow-while capped at maxIterations', out['T.c'] === 7, 'count=' + out['T.c']);
  ok('flow-while last body value', approx(out['T.l'], 1));
  // cond false -> zero iterations.
  const g0 = JSON.parse(JSON.stringify(g));
  g0.nodes[0].params.value = false;
  ok('flow-while cond false -> 0 iters', once(g0, {}).out['T.c'] === 0);
})();

// ── flow-repeat per-iteration vector ────────────────────────────────────────-
(function () {
  // body reads ctx.index via... we have no expr node here, so test sum/values shape
  // by feeding a constant body of 2 over n=4 -> sum 8, values length 4.
  const g = {
    nodes: [
      { id: 'n', kind: 'value-vec2', params: { x: 4, y: 0 } },
      { id: 'b', kind: 'value-vec2', params: { x: 2, y: 0 } },
      { id: 'r', kind: 'flow-repeat', params: {} },
    ],
    edges: [
      { from: { node: 'n', port: 'value' }, to: { node: 'r', port: 'n' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'r', port: 'body' } },
    ],
    outputs: [{ sourceNode: 'r', sourcePort: 'sum', targetNode: 'T', targetParam: 's' }],
  };
  const { out } = once(g, {});
  ok('flow-repeat sum 2*4=8', approx(out['T.s'], 8));
  ok('flow-repeat values length=4', ports(out, 'r').values.length === 4);
})();

// ── state-counter across frames (event semantics) ───────────────────────────-
(function () {
  // input-pointer.clicked is an event: true only on the frame isDown rises.
  // Wire clicked -> state-counter.inc; count should advance once per press.
  const g = {
    nodes: [
      { id: 'ptr', kind: 'input-pointer', params: {} },
      { id: 'ctr', kind: 'state-counter', params: { step: 1, wrap: 0 } },
    ],
    edges: [{ from: { node: 'ptr', port: 'clicked' }, to: { node: 'ctr', port: 'inc' } }],
    outputs: [{ sourceNode: 'ctr', sourcePort: 'count', targetNode: 'T', targetParam: 'c' }],
  };
  const plan = LogicGraph.compile(g);
  const seq = [false, true, true, false, true, false]; // 2 rising edges
  let last = 0;
  for (const down of seq) last = LogicGraph.tick(plan, { pointer: { isDown: down }, dt: 0.016 }, {})['T.c'];
  ok('state-counter counts rising edges (2)', last === 2, 'count=' + last);

  // also confirm clicked is true ONLY on the rising frame.
  const plan2 = LogicGraph.compile({
    nodes: [{ id: 'ptr', kind: 'input-pointer', params: {} }],
    edges: [], outputs: [{ sourceNode: 'ptr', sourcePort: 'clicked', targetNode: 'T', targetParam: 'k' }],
  });
  const f1 = LogicGraph.tick(plan2, { pointer: { isDown: true }, dt: 0.016 }, {})['T.k'];
  const f2 = LogicGraph.tick(plan2, { pointer: { isDown: true }, dt: 0.016 }, {})['T.k'];
  ok('event true only on firing frame', f1 === true && f2 === false);
})();

// ── state-toggle / state-timer ──────────────────────────────────────────────-
(function () {
  const g = {
    nodes: [
      { id: 'ptr', kind: 'input-pointer', params: {} },
      { id: 'tg', kind: 'state-toggle', params: { initial: false } },
    ],
    edges: [{ from: { node: 'ptr', port: 'clicked' }, to: { node: 'tg', port: 'flip' } }],
    outputs: [{ sourceNode: 'tg', sourcePort: 'on', targetNode: 'T', targetParam: 'on' }],
  };
  const plan = LogicGraph.compile(g);
  const press = (d) => LogicGraph.tick(plan, { pointer: { isDown: d }, dt: 0.016 }, {})['T.on'];
  press(false); const a = press(true); press(false); const b = press(true);
  ok('state-toggle flips per click', a === true && b === false);

  const gt = {
    nodes: [{ id: 'tm', kind: 'state-timer', params: { autostart: true } }],
    edges: [], outputs: [{ sourceNode: 'tm', sourcePort: 'elapsed', targetNode: 'T', targetParam: 'e' }],
  };
  const pt = LogicGraph.compile(gt);
  let el = 0; for (let i = 0; i < 10; i++) el = LogicGraph.tick(pt, { dt: 0.1 }, {})['T.e'];
  ok('state-timer accumulates dt', approx(el, 1.0, 1e-6), 'elapsed=' + el);
})();

// ── state-smooth convergence (critically damped) ────────────────────────────-
(function () {
  const g = {
    nodes: [
      { id: 'tgt', kind: 'value-vec2', params: { x: 1, y: 0 } },
      { id: 'sm', kind: 'state-smooth', params: { stiffness: 120 } },
    ],
    edges: [{ from: { node: 'tgt', port: 'value' }, to: { node: 'sm', port: 'target' } }],
    outputs: [{ sourceNode: 'sm', sourcePort: 'value', targetNode: 'T', targetParam: 'v' }],
  };
  // init samples target (x of vec2 -> 1) on first frame; push target to a NEW value
  // and watch convergence. Re-do with target literal 1 but seeded value 0 by
  // making the first sample 0: use a separate graph where target is read as number.
  const g2 = {
    nodes: [
      { id: 'va', kind: 'value-vec2', params: { x: 0, y: 0 } },
      { id: 'vb', kind: 'value-vec2', params: { x: 10, y: 0 } },
      { id: 'sw', kind: 'value-bool', params: { value: false } },
      { id: 'pick', kind: 'flow-if', params: {} },
      { id: 'sm', kind: 'state-smooth', params: { stiffness: 200 } },
    ],
    edges: [
      { from: { node: 'sw', port: 'value' }, to: { node: 'pick', port: 'cond' } },
      { from: { node: 'vb', port: 'value' }, to: { node: 'pick', port: 'then' } },
      { from: { node: 'va', port: 'value' }, to: { node: 'pick', port: 'else' } },
      { from: { node: 'pick', port: 'r' }, to: { node: 'sm', port: 'target' } },
    ],
    outputs: [{ sourceNode: 'sm', sourcePort: 'value', targetNode: 'T', targetParam: 'v' }],
  };
  const plan = LogicGraph.compile(g2);
  // frame 1: cond false -> target=0, value seeds to 0.
  let v = LogicGraph.tick(plan, { dt: 0.016 }, {})['T.v'];
  ok('state-smooth seeds to first target (0)', approx(v, 0, 1e-6), 'v=' + v);
  // flip cond true -> target=10; run ~2s, must converge near 10 without overshoot blowup.
  plan.nodes['sw'].params.value = true;
  let maxV = -Infinity;
  for (let i = 0; i < 200; i++) { v = LogicGraph.tick(plan, { dt: 0.016 }, {})['T.v']; if (v > maxV) maxV = v; }
  ok('state-smooth converges to target (10)', approx(v, 10, 0.05), 'v=' + v);
  ok('state-smooth no large overshoot', maxV <= 10.5, 'maxV=' + maxV);
})();

// ── topo-ordered multi-node graph ───────────────────────────────────────────-
(function () {
  // (a=3 + b=4) then *2 then map 0..14 -> 0..1 (=1.0). Tests deep topo ordering.
  const g = {
    nodes: [
      { id: 'a', kind: 'value-vec2', params: { x: 3, y: 0 } },
      { id: 'b', kind: 'value-vec2', params: { x: 4, y: 0 } },
      { id: 'two', kind: 'value-vec2', params: { x: 2, y: 0 } },
      { id: 'sum', kind: 'op-math', params: { op: 'add' } },
      { id: 'mul', kind: 'op-math', params: { op: 'mul' } },
      { id: 'map', kind: 'op-map', params: { inMin: 0, inMax: 14, outMin: 0, outMax: 1, clamp: true } },
    ],
    edges: [
      { from: { node: 'a', port: 'value' }, to: { node: 'sum', port: 'a' } },
      { from: { node: 'b', port: 'value' }, to: { node: 'sum', port: 'b' } },
      { from: { node: 'sum', port: 'r' }, to: { node: 'mul', port: 'a' } },
      { from: { node: 'two', port: 'value' }, to: { node: 'mul', port: 'b' } },
      { from: { node: 'mul', port: 'r' }, to: { node: 'map', port: 'x' } },
    ],
    outputs: [{ sourceNode: 'map', sourcePort: 'r', targetNode: 'T', targetParam: 'opacity' }],
  };
  const { plan, out } = once(g, {});
  // mul must come after sum in topo order.
  ok('topo: sum before mul before map', plan.order.indexOf('sum') < plan.order.indexOf('mul') && plan.order.indexOf('mul') < plan.order.indexOf('map'));
  ok('topo multi-node result (3+4)*2/14=1', approx(out['T.opacity'], 1), 'got ' + out['T.opacity']);
  ok('compile no errors on DAG', plan.errors.length === 0);
})();

// ── non-state cycle -> compile error ────────────────────────────────────────-
(function () {
  // m1.r -> m2.a, m2.r -> m1.a : a pure cycle with NO state node = compile error.
  const g = {
    nodes: [
      { id: 'm1', kind: 'op-math', params: { op: 'add' } },
      { id: 'm2', kind: 'op-math', params: { op: 'add' } },
    ],
    edges: [
      { from: { node: 'm1', port: 'r' }, to: { node: 'm2', port: 'a' } },
      { from: { node: 'm2', port: 'r' }, to: { node: 'm1', port: 'a' } },
    ],
    outputs: [],
  };
  const plan = LogicGraph.compile(g);
  ok('non-state cycle -> compile error', plan.errors.length > 0, 'errors=' + plan.errors.length);
  ok('compile does not throw on cycle', true);

  // contrast: same cycle but THROUGH a state node is legal (no error).
  const gs = {
    nodes: [
      { id: 'sm', kind: 'state-smooth', params: {} },
      { id: 'm', kind: 'op-math', params: { op: 'add' } },
    ],
    edges: [
      { from: { node: 'sm', port: 'value' }, to: { node: 'm', port: 'a' } },
      { from: { node: 'm', port: 'r' }, to: { node: 'sm', port: 'target' } },
    ],
    outputs: [],
  };
  const planS = LogicGraph.compile(gs);
  ok('cycle through state node is legal', planS.errors.length === 0, 'errors=' + planS.errors.length);
})();

// ── read() helper ───────────────────────────────────────────────────────────-
(function () {
  const g = {
    nodes: [{ id: 'v', kind: 'value-vec2', params: { x: 9, y: 0 } }],
    edges: [], outputs: [{ sourceNode: 'v', sourcePort: 'value', targetNode: 'N', targetParam: 'p' }],
  };
  const { plan, out } = once(g, {});
  const val = LogicGraph.read(plan, out, 'N', 'p');
  ok('read() returns output value', val && approx(val.x, 9));
})();

// ── summary ─────────────────────────────────────────────────────────────────-
console.log('\n========================================');
console.log('SUMMARY: ' + passed + ' passed, ' + failed + ' failed, ' + (passed + failed) + ' total');
console.log('========================================');
process.exit(failed ? 1 : 0);
