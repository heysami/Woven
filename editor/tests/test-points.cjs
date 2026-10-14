/* Point tool store (editor/points.js): numbering, the sent-number reserve,
   draft -> run migration, persistence per project + thread, the one-shot
   mode, fingerprint resolution, and the <pointed-targets> block the agent
   reads. Plain node: points.js only needs window / location / localStorage,
   so a tiny shim runs it verbatim. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'points.js'), 'utf8');

function boot({ search = '?project=demo', storage } = {}) {
  const store = storage || new Map();
  const localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => { store.set(k, String(v)); },
    removeItem: (k) => { store.delete(k); },
  };
  const location = { search, href: 'http://127.0.0.1/editor/index.html' + search };
  const window = {};
  const ctx = { window, location, localStorage, URL, URLSearchParams, Date, Math, JSON };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx);
  return { WP: window.WovenPoints, store };
}

// ── numbering + reserve ──
{
  const { WP } = boot();
  const a = WP.add('run1', { kind: 'node', nodeId: 'n1' });
  const b = WP.add('run1', { kind: 'node', nodeId: 'n2' });
  const c = WP.add('run1', { kind: 'node', nodeId: 'n3' });
  assert.deepEqual([a.n, b.n, c.n], [1, 2, 3]);
  // an unsent point frees its number
  WP.remove('run1', 2);
  assert.equal(WP.add('run1', { kind: 'node', nodeId: 'n4' }).n, 2);
  // a sent point reserves it, even after removal
  WP.markSent('run1', [1]);
  WP.remove('run1', 1);
  assert.equal(WP.add('run1', { kind: 'node', nodeId: 'n5' }).n, 4);
  assert.equal(WP.removeIfUnsent('run1', 3), true);
  WP.markSent('run1', [2]);
  assert.equal(WP.removeIfUnsent('run1', 2), false, 'a sent point is not removed by a chip delete');
  // threads are independent
  assert.equal(WP.add('run2', { kind: 'node', nodeId: 'x' }).n, 1);
}

// ── events + one-shot mode + reference ──
{
  const { WP } = boot();
  const seen = [];
  const off = WP.subscribe((e) => seen.push(e.type));
  WP.arm({ threadKey: 't', oneShot: true, insertAt: 4 });
  assert.deepEqual(JSON.parse(JSON.stringify(WP.mode())), { armed: true, oneShot: true, threadKey: 't', insertAt: 4 });
  const p = WP.add('t', { kind: 'wb', wbId: 'w1', wbType: 'sticky', wbText: 'todo' });
  WP.reference('t', p.n);
  WP.disarm();
  assert.equal(WP.mode().armed, false);
  off();
  WP.add('t', { kind: 'node', nodeId: 'n' });
  assert.deepEqual(seen, ['mode', 'added', 'added', 'mode']);
  // switching the active thread disarms a mode armed for another thread
  WP.arm({ threadKey: 'a' });
  WP.setActive('b');
  assert.equal(WP.mode().armed, false);
}

// ── draft -> run migration keeps the sent flag ──
{
  const { WP } = boot();
  WP.add('draft', { kind: 'node', nodeId: 'n1' });
  WP.add('draft', { kind: 'node', nodeId: 'n2' });
  WP.markSent('draft', [1, 2]);
  WP.migrate('draft', 'run9');
  assert.equal(WP.list('draft').length, 0);
  assert.deepEqual(JSON.parse(JSON.stringify(WP.list('run9').map(p => [p.n, p.sent]))), [[1, true], [2, true]]);
}

// ── persistence per project + thread, and ?embed=1 never writes ──
{
  const shared = new Map();
  const one = boot({ storage: shared });
  one.WP.add('run1', { kind: 'node', nodeId: 'n1' });
  one.WP.add('run1', { kind: 'node', nodeId: 'n2' });
  one.WP.markSent('run1', [1]);
  const two = boot({ storage: shared });
  assert.deepEqual(JSON.parse(JSON.stringify(two.WP.list('run1').map(p => p.n))), [1], 'only the SENT point comes back after a reload');
  assert.equal(two.WP.add('run1', { kind: 'node', nodeId: 'n3' }).n, 2, 'the dropped unsent number is free again');
  const other = boot({ storage: shared, search: '?project=other' });
  assert.equal(other.WP.list('run1').length, 0, 'another project never sees it');
  const embed = boot({ storage: new Map(), search: '?project=demo&embed=1' });
  embed.WP.add('run1', { kind: 'node', nodeId: 'n1' });
  assert.equal(embed.store.size, 0, 'embed mode does not touch localStorage');
}

// ── pruneUnsent: a badge never outlives its chip ──
{
  const { WP } = boot();
  WP.add('t', { kind: 'node', nodeId: 'a' });
  WP.add('t', { kind: 'node', nodeId: 'b' });
  WP.add('t', { kind: 'node', nodeId: 'c' });
  WP.markSent('t', [3]);
  const removed = [];
  WP.subscribe((e) => { if (e.type === 'removed') removed.push(e.n); });
  WP.pruneUnsent('t', new Set([2]));
  assert.deepEqual(JSON.parse(JSON.stringify(WP.list('t').map(p => p.n))), [2, 3], 'unchipped unsent go, chipped and sent stay');
  WP.pruneUnsent('t', null);
  assert.deepEqual(JSON.parse(JSON.stringify(WP.list('t').map(p => p.n))), [3]);
  assert.deepEqual(removed, [1, 2]);
}

// ── the agent block ──
{
  const { WP } = boot();
  const el = WP.add('r', {
    kind: 'element', page: 'source/main/index.html', nodeId: 'prototype_main', nodeTitle: 'main', nodeKind: 'prototype',
    anchor: { selector: 'header > a.cta', fp: { tag: 'a', cls: 'cta' }, label: 'a.cta', snippet: '<a class="cta" href="#">', text: 'Get started' },
  });
  const wb = WP.add('r', { kind: 'wb', wbId: 'w1', wbType: 'sticky', wbText: 'todo: header' });
  const nd = WP.add('r', { kind: 'node', nodeId: 'prototype_about', nodeTitle: 'About', nodeKind: 'prototype' });
  const block = WP.formatPointedTargets([nd, el, wb]);
  assert.ok(block.startsWith('<pointed-targets>\n[1] element on source/main/index.html, inside canvas node prototype_main ("main")\n'));
  assert.ok(block.includes('    selector: header > a.cta\n    element: <a class="cta" href="#">  text: "Get started"\n'));
  assert.ok(block.includes('[2] whiteboard sticky w1: "todo: header"\n'));
  assert.ok(block.includes('[3] canvas node prototype_about ("About", prototype)\n'));
  assert.ok(block.includes('In the message, [1] [2] [3] point at exactly these targets. Keep the change scoped to them.\n</pointed-targets>\n\n'));
  assert.equal(WP.formatPointedTargets([]), '');
  WP.setLost('r', 1, true);
  assert.ok(WP.formatPointedTargets([WP.get('r', 1)]).includes('no longer found on the page, last seen as <a class="cta" href="#">'));
  assert.ok(/\[1\] points at exactly this target/.test(WP.formatPointedTargets([WP.get('r', 1)])));
  assert.equal(WP.labelOf(el), 'a.cta');
  assert.equal(WP.whereOf(el), 'index.html');
}

// ── fingerprint resolution: selector verified by fp, else a unique fp match ──
{
  const { WP } = boot();
  const mk = (tag, cls, text) => ({ tagName: tag.toUpperCase(), className: cls, textContent: text });
  const target = mk('a', 'cta', 'Get started');
  const decoy = mk('a', 'cta', 'Sign in');
  const doc = (bySel, all) => ({ querySelector: () => bySel, querySelectorAll: () => all });
  const anchor = { selector: 'header > a.cta', fp: { tag: 'a', cls: 'cta', text: 'Get started' } };
  assert.equal(WP.resolve(doc(target, [target, decoy]), anchor), target, 'selector hit with a matching fingerprint');
  assert.equal(WP.resolve(doc(decoy, [decoy, target]), anchor), target, 'selector drifted: fingerprint scan finds it');
  assert.equal(WP.resolve(doc(null, [target, mk('a', 'cta', 'Get started')]), anchor), null, 'ambiguous: better lost than wrong');
}

console.log('test-points: ok');
