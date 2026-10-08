/* Component DS runtime (editor/tools/ds/runtime/ds-runtime.src.js), run in a
   real browser against the fixture DS. Covers: tags expand to the template's
   own markup with no wrapper, mid-parse scripts already see expanded markup,
   DS.html is synchronous, behaviors (delegated click + init on JS-inserted
   markup), the self-check, DS.update keeping slotted nodes, and DS.serialize
   round-tripping expanded markup back to <ds-*> source.
   Build first:  python3 editor/tools/ds/build_ds.py --ds-dir editor/tools/ds/fixtures/mini-project/design-systems/mini */
const assert = require('node:assert/strict');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { chromium } = require('../tools/node_modules/playwright');

const TOOLS = path.join(__dirname, '..', 'tools', 'ds');
const PROJECT = path.join(TOOLS, 'fixtures', 'mini-project');
const DS_DIR = path.join(PROJECT, 'design-systems', 'mini');
const url = p => 'file://' + path.join(PROJECT, p);

(async () => {
  execFileSync('python3', [path.join(TOOLS, 'build_ds.py'), '--ds-dir', DS_DIR, '--quiet'], { stdio: 'pipe' });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url('source/main/index.html'));
  await page.waitForFunction(() => document.documentElement.classList.contains('ds-ready'));

  // 1. expansion
  const s = await page.evaluate(() => ({
    leftover: [...document.querySelectorAll('*')].filter(e => e.localName.startsWith('ds-')).length,
    boot: !!document.querySelector('style[data-ds-boot]'),
    mid: window.__midParse, after: window.__afterHtml,
    shell: (() => { const e = document.getElementById('shell'); return e && [e.className, e.getAttribute('data-ds')]; })(),
    edit: (() => { const e = document.querySelector('[data-step="2"]'); return e && [e.className, !!e.querySelector('svg.icon path'), e.closest('.app__bar') !== null]; })(),
    card: (() => { const e = document.querySelector('.card.orders-grid'); return e && [e.getAttribute('data-ds'), !!e.querySelector('.card__actions .btn--text'), e.querySelector('.stack #body-p') !== null]; })(),
    field: (() => { const e = document.querySelector('.field select.select'); return e && [...e.options].map(o => o.textContent); })(),
    custom: document.body.innerHTML.includes('<!--ds-custom#') && !!document.querySelector('.timeline'),
    radius: getComputedStyle(document.querySelector('.filter-chip')).borderTopLeftRadius,
    inited: [...document.querySelectorAll('.filter-chip')].map(e => e.getAttribute('data-ds-inited')),
    violations: DS.violations.map(v => v.code),
  }));
  assert.equal(s.leftover, 0, 'every <ds-*> tag expands');
  assert.equal(s.boot, false, 'boot style removed once ready');
  assert.deepEqual(s.mid, { chips: 2, tags: 0 }, 'a script mid-parse sees expanded markup');
  assert.equal(s.after, 1, 'DS.html output is queryable synchronously');
  assert.deepEqual(s.shell, ['app', 'app']);
  assert.deepEqual(s.edit, ['btn btn--outline', true, true], 'named slot + nested icon block + passthrough data-*');
  assert.deepEqual(s.card, ['card', true, true], 'page class appended, actions slot, default slot inside nested stack');
  assert.deepEqual(s.field, ['Open', 'Closed'], 'list prop + each loop');
  assert.ok(s.custom, 'ds-custom becomes comment markers around raw content');
  assert.equal(s.radius, '999px', 'layered tokens reach block CSS');
  await page.waitForTimeout(50);
  const inited = await page.evaluate(() => [...document.querySelectorAll('.filter-chip')].map(e => e.getAttribute('data-ds-inited')));
  assert.deepEqual(inited, ['1', '1', '1'], 'init runs for tag-expanded AND DS.html-inserted blocks');
  assert.deepEqual(s.violations, [], 'clean page has no violations');

  // 2. behavior + event
  const ev = await page.evaluate(() => new Promise(res => {
    const chip = document.getElementById('chip-status');
    chip.addEventListener('ds:change', e => res([e.detail.open, chip.classList.contains('is-open'), chip.getAttribute('aria-expanded')]), { once: true });
    chip.querySelector('.filter-chip__label').click();
  }));
  assert.deepEqual(ev, [true, true, 'true'], 'delegated click from a descendant reaches the block behavior');

  // 3. serialize back to source form
  const src = await page.evaluate(() => DS.serialize(document.body));
  for (const want of [
    '<ds-app title="Orders" id="shell">',
    '<ds-button variant="outline" icon="edit" data-step="2" slot="actions">Edit</ds-button>',
    '<ds-filter-chip label="Status" count="2" id="chip-status"></ds-filter-chip>',
    '<ds-filter-chip label="Owner" size="s"></ds-filter-chip>',
    '<ds-card title="Recent" class="orders-grid">',
    '<p id="body-p">First &amp; second</p>',
    '<ds-field label="Status" hint="Pick one"><ds-select options="Open,Closed" name="status"></ds-select></ds-field>',
    '<ds-custom reason="one-off timeline, no block yet"><div class="timeline">t</div></ds-custom>',
    '<ds-card title="Dynamic"><ds-filter-chip label="From JS"></ds-filter-chip></ds-card>',
  ]) assert.ok(src.includes(want), 'serialize keeps: ' + want + '\n---\n' + src);
  for (const bad of ['data-ds', 'filter-chip__label', 'is-open', 'aria-expanded', 'ds-slot', 'Nothing here yet']) {
    assert.ok(!src.includes(bad), 'serialize drops ' + bad);
  }

  // 4. round trip: serialized source expands to the same DOM
  const strip = h => h.replace(/ data-ds-i="\d+"/g, '').replace(/#\d+/g, '#').replace(/ data-ds-inited="1"/g, '').replace(/\s+/g, ' ');
  const before = await page.evaluate(() => {
    const c = document.getElementById('chip-status'); c.classList.remove('is-open'); c.setAttribute('aria-expanded', 'false');
    return document.getElementById('shell').outerHTML;
  });
  const page2 = await browser.newPage();
  await page2.goto(url('source/main/index.html'));
  await page2.waitForFunction(() => document.documentElement.classList.contains('ds-ready'));
  const after = await page2.evaluate(src => {
    const host = document.createElement('div'); host.innerHTML = src; DS.expand(host);
    return host.querySelector('#shell').outerHTML;
  }, src.replace(/^<body>|<\/body>$/g, ''));
  assert.equal(strip(after), strip(before), 'serialize -> expand reproduces the same markup');

  // 5. DS.update keeps slotted nodes (identity) and applies the new prop
  const upd = await page.evaluate(() => {
    const card = document.querySelector('.card.orders-grid'); const p = document.getElementById('body-p');
    const next = DS.update(card, { title: 'Renamed' });
    return [next.querySelector('.card__title').textContent, next.contains(p), next.classList.contains('orders-grid')];
  });
  assert.deepEqual(upd, ['Renamed', true, true]);

  // 6. self-check catches hand-built blocks and raw replaced elements
  const v = await page.evaluate(() => new Promise(res => {
    document.body.insertAdjacentHTML('beforeend', '<div id="hb"><button class="btn btn--primary">hand</button><select><option>x</option></select></div>');
    setTimeout(() => res(DS.violations.map(x => x.code)), 400);
  }));
  assert.ok(v.includes('hand-built-block'), 'hand-built .btn reported: ' + v);
  assert.ok(v.includes('raw-replaced-element'), 'raw <select> reported: ' + v);

  // 7. tags inserted after load expand via the observer
  const late = await page.evaluate(() => new Promise(res => {
    document.getElementById('dyn').insertAdjacentHTML('beforeend', '<ds-stack gap="s"><ds-button label="Late"></ds-button></ds-stack>');
    queueMicrotask(() => res([!!document.querySelector('#dyn .stack--s .btn'), document.querySelectorAll('ds-stack').length]));
  }));
  assert.deepEqual(late, [true, 0], 'observer expands before the next task');

  // 8. gallery (build/ and the root mirror the editor opens) renders every example
  for (const rel of [['build', 'gallery.html'], ['gallery.html']]) {
    const g = await browser.newPage();
    const gerr = [];
    g.on('pageerror', e => gerr.push(String(e)));
    await g.goto('file://' + path.join(DS_DIR, ...rel));
    await g.waitForFunction(() => document.documentElement.classList.contains('ds-ready'));
    await g.waitForTimeout(150);
    const gal = await g.evaluate(() => {
      const st = [...document.querySelectorAll('[data-dsg-example]')];
      const frame = document.querySelector('.dsg-frame');
      return { total: st.length, empty: st.filter(e => !e.firstElementChild).length, errs: document.querySelectorAll('.dsg-err').length,
               framed: !!(frame && frame.contentDocument && frame.contentDocument.querySelector('.app .app__bar')) };
    });
    assert.ok(gal.total >= 12, rel.join('/') + ': gallery has every example');
    assert.equal(gal.empty, 0, rel.join('/') + ': every gallery example rendered');
    assert.equal(gal.errs, 0);
    assert.ok(gal.framed, rel.join('/') + ': iframe (shell) example rendered with the DS');
    assert.deepEqual(gerr, []);
  }

  // 9. the editor's save-back (app.js pickSerializeClean) writes source form
  const APP = require('node:fs').readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');
  const start = APP.indexOf('function pickSerializeClean(doc)');
  const end = APP.indexOf('\n}\n', start) + 3;
  assert.ok(start > 0 && end > start, 'pickSerializeClean found in app.js');
  const saved = await page2.evaluate(fn => { eval(fn); return pickSerializeClean(document); }, APP.slice(start, end));
  assert.ok(saved.startsWith('<!DOCTYPE html>\n<html lang="en">'), 'doctype + html kept, ds-ready class dropped');
  assert.ok(saved.includes('<ds-app title="Orders" id="shell">'), 'blocks saved as tags');
  assert.ok(!saved.includes('data-ds') && !saved.includes('data-ds-boot'), 'no runtime residue in the saved file');
  assert.ok(saved.includes('<script src="../../design-systems/mini/build/ds-runtime.js"></script>'));

  assert.deepEqual(errors, [], 'no page errors');
  await browser.close();
  console.log('test-component-ds-runtime: ok');
})().catch(e => { console.error(e); process.exit(1); });
