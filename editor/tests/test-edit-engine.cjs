/* Real DOM regressions for the shared engine and the actual saved patch code. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { chromium } = require('../tools/node_modules/playwright');
const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
const patchCode = app.slice(app.indexOf('function _extractPatchOps('), app.indexOf('function pickSerializeClean('));
const helpers = vm.runInNewContext(patchCode + '\n({_mergePatchOps,_injectInspectorPatch,_extractPatchOps})');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.setContent('<style>:root{--accent:#123456;--semantic:var(--accent)}#field{border-color:var(--semantic)}</style><main style="display:flex;width:500px"><section id="original"><label for="field">Name</label><input id="field"><span style="color:var(--semantic)">Alpha</span></section></main>');
    await page.addScriptTag({ path: path.join(__dirname, '../edit-engine.js') });
    const result = await page.evaluate(() => {
      const E = WovenEdit;
      const original = document.querySelector('section');
      E.copy(original);
      original.querySelector('span').textContent = 'Changed after copy';
      let target = original;
      for (let i = 0; i < 5; i++) {
        target = E.paste(target).nodes[0];
        if (target.querySelector('span').textContent !== 'Alpha') throw new Error('Clipboard was not a snapshot');
        target.querySelector('span').textContent = 'Copy ' + i;
      }
      const copies = [...document.querySelectorAll('section')].slice(1);
      E.applyStyles(copies[0], E.sizing('w', 'fill', 100, { display: 'flex', flexDirection: 'row' }, {}));
      const fill = [copies[0].style.flexGrow, copies[0].style.flexBasis, E.sizeMode(copies[0], 'width')];
      E.applyStyles(copies[0], E.sizing('w', 'fixed', 80, { display: 'flex', flexDirection: 'row' }, {}));
      E.applyStyles(copies[0], { color: 'red' }); E.applyStyles(copies[0], { color: null, alignSelf: 'auto' });
      return { count: copies.length, ids: copies.map(n => n.querySelector('input').id),
        labels: copies.every(n => n.querySelector('label').htmlFor === n.querySelector('input').id),
        values: copies.map(n => n.querySelector('span').textContent),
        bindings: copies.every(n => n.querySelector('span').style.color === 'var(--semantic)'),
        idStyles: copies.every(n => n.querySelector('input').style.borderColor === 'var(--semantic)'),
        fill, fixed: [copies[0].style.width, copies[0].style.flexGrow, copies[0].style.flexBasis],
        reset: copies[0].style.color, auto: copies[0].style.alignSelf,
        alias: E.variables(document)['--semantic'] };
    });
    assert.equal(result.count, 5);
    assert.equal(new Set(result.ids).size, 5);
    assert.equal(result.labels, true);
    assert.deepEqual(result.values, ['Copy 0','Copy 1','Copy 2','Copy 3','Copy 4']);
    assert.equal(result.bindings, true);
    assert.equal(result.idStyles, true);
    assert.deepEqual(result.fill, ['1', '0px', 'fill']);
    assert.deepEqual(result.fixed, ['80px','0','auto']);
    assert.equal(result.reset, ''); assert.equal(result.auto, 'auto');
    assert.equal(result.alias.raw, 'var(--accent)'); assert.equal(result.alias.value, '#123456');

    // Deleting the first pasted sibling must not orphan later paste anchors.
    const chain = [
      {type:'insert',anchor:'#title',position:'after',key:'i1',html:'<p data-woven-id="a" data-th-ins="i1">First</p>'},
      {type:'insert',anchor:'[data-woven-id="a"]',position:'after',key:'i2',html:'<p data-woven-id="b" data-th-ins="i2">Second</p>'},
      {type:'insert',anchor:'[data-woven-id="b"]',position:'after',key:'i3',html:'<p data-woven-id="c" data-th-ins="i3">Third</p>'},
      {type:'delete',selector:'[data-woven-id="a"]',cancelIns:'i1'},
    ];
    const beforeMerge = JSON.stringify(chain);
    await page.setContent(helpers._injectInspectorPatch('<h1 id="title">Anchor</h1>', chain));
    assert.deepEqual(await page.locator('p').allTextContents(), ['Second', 'Third']);
    assert.equal(JSON.stringify(chain), beforeMerge, 'Save must not mutate undo history commands');

    const base = '<!doctype html><html><body><h1 id="title">Alpha</h1></body></html>';
    const first = { type:'text', selector:'#title', id:'stable', fp:{tag:'h1',text:'Alpha'}, text:'Bravo' };
    const second = { ...first, fp:{tag:'h1',text:'Bravo'}, text:'Charlie' };
    const saved = helpers._injectInspectorPatch(helpers._injectInspectorPatch(base, [first]), [second]);
    await page.setContent(saved);
    assert.equal(await page.locator('h1').textContent(), 'Charlie');
    await page.evaluate(() => { document.querySelector('h1').firstChild.nodeValue = 'Alpha'; });
    await page.waitForFunction(() => document.querySelector('h1').textContent === 'Charlie');
    const reset = helpers._injectInspectorPatch(base, [{type:'style',selector:'#title',styles:{color:null}}], [{type:'style',selector:'#title',styles:{color:'red'}}]);
    await page.setContent(reset);
    assert.equal(await page.locator('h1').evaluate(n => n.style.color), '');
    await page.setContent(helpers._injectInspectorPatch('<h1>Alpha</h1><h1>Alpha</h1>', [
      {type:'text',selector:'#missing',fp:{tag:'h1',text:'Alpha'},text:'Changed'},
    ]));
    assert.deepEqual(await page.locator('h1').allTextContents(),['Alpha','Alpha']);
    assert.equal(await page.evaluate(()=>window.__wovenEditConflicts.length),1);
    assert.deepEqual(errors, []);
    console.log('PASS: immutable repeated paste, editable descendants, unique IDs/references, bindings, layout transitions, aliases, repeated text replay, text-node rerenders, style reset.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
