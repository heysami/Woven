/* Shared commands in a real layout engine, including saved replay. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');
const root = path.join(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const patch = app.slice(app.indexOf('function _extractPatchOps('), app.indexOf('function pickSerializeClean('));
const selectors = app.slice(app.indexOf('function elementCssPath('), app.indexOf('/* WorkflowAssetActionBar:'));
const commands = app.slice(app.indexOf('function performSelectionCommand('), app.indexOf('function PickedInspectorBody('));
const source = `<!doctype html><html><head><style>
body{font:16px Arial}.row{display:flex;width:400px;gap:8px;margin-bottom:10px}.row>div,.grid>div{width:60px;height:30px}
.grid{display:grid;grid-template-columns:80px 80px;gap:8px;margin-bottom:10px}
#locked{translate:none!important}#positioned{position:absolute;right:10%;top:500px;transform:rotate(3deg);translate:10% 0;width:100px}
</style></head><body>
<div class="row" id="row"><div>Alpha</div><div>Beta</div><div>Gamma</div></div>
<div class="row" id="reverse" style="flex-direction:row-reverse"><div>First</div><div>Second</div></div>
<div class="row" id="rtl" dir="rtl"><div>First</div><div>Second</div></div>
<div class="row" id="column" style="flex-direction:column"><div>First</div><div>Second</div></div>
<div class="grid" id="grid"><div>One</div><div>Two</div><div>Three</div><div>Four</div></div>
<div class="row" id="ordered"><div style="order:1">First</div><div style="order:2">Second</div></div>
<div id="normal">Normal flow <span id="text">Real text width</span></div>
<div id="locked">Cannot move</div><div id="positioned">Anchored</div>
<div id="contents" style="display:contents">Text without a box</div>
<div id="abs-parent" style="position:relative"><span style="position:absolute">Out of flow text</span></div>
</body></html>`;
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.setContent(source);
    for (const name of ['edit-engine.js', 'edit-components.js']) await page.addScriptTag({ path: path.join(root, name) });
    await page.addScriptTag({ content: patch + selectors + commands });
    const result = await page.evaluate(source => {
      const ops = [], E = WovenEdit;
      const first = id => document.querySelector('#' + id).firstElementChild;
      const move = (el, direction, step) => { const r = performSelectionCommand(el, 'move', { direction, step }); ops.push(r.op); return r; };
      const reject = (el, direction) => { try { move(el, direction); return ''; } catch (e) { return e.message; } };
      const a = first('row');
      move(a, 'right'); move(a, 'left');
      const insert=performSelectionCommand(a,'insert',{html:'<div id="pasted">Pasted</div>'}); ops.push(insert.op);
      move(a, 'right'); move(a, 'right'); move(a, 'right');
      const order = [...a.parentElement.children].map(n => n.textContent);
      const edge = reject(a, 'right'), wrongAxis = reject(a, 'up');
      move(first('reverse'), 'left'); move(first('rtl'), 'left'); move(first('column'), 'down');
      move(first('grid'), 'down');
      const ordered = reject(first('ordered'), 'right');
      const orderAfterFailure = [...document.querySelector('#ordered').children].map(n => n.textContent);
      const normal = document.querySelector('#normal'), old = normal.getBoundingClientRect();
      move(normal, 'right'); move(normal, 'down', 10);
      const now = normal.getBoundingClientRect();
      const text = document.querySelector('#text');
      const width = E.dimension(text, 'width'), height = E.dimension(text, 'height');
      const textBefore = text.getBoundingClientRect().x;
      move(text, 'left'); move(text, 'left');
      const textMoved = text.getBoundingClientRect().x - textBefore;
      E.applyStyles(text, E.sizing('w', 'hug', width, getComputedStyle(text.parentElement), getComputedStyle(text)));
      E.applyStyles(text, E.sizing('h', 'hug', height, getComputedStyle(text.parentElement), getComputedStyle(text)));
      const hug = { width: E.dimension(text, 'width'), height: E.dimension(text, 'height'), mode: E.sizeMode(text, 'width') };
      const abs = document.querySelector('#positioned'), absBefore = abs.getBoundingClientRect();
      move(abs, 'right', 10);
      const absAfter = abs.getBoundingClientRect();
      const lock = document.querySelector('#locked');
      const locked = reject(lock, 'right');
      const contents = reject(document.querySelector('#contents'), 'left');
      const absNote = E.sizingNote(document.querySelector('#abs-parent'));
      return { order, edge, wrongAxis, ordered, orderAfterFailure, reversed: first('reverse').textContent, rtl: first('rtl').textContent,
        column: first('column').textContent, grid: [...document.querySelector('#grid').children].map(n => n.textContent),
        delta: [now.x-old.x, now.y-old.y], width, height, textMoved, hug,
        abs: { delta: absAfter.x-absBefore.x, width: absAfter.width-absBefore.width, right: abs.style.right, transform: abs.style.transform },
        locked, lockStyle: lock.getAttribute('style'), contents, absNote, saved: _injectInspectorPatch(source, ops) };
    }, source);
    assert.deepEqual(result.order, ['Pasted', 'Beta', 'Gamma', 'Alpha']);
    assert.match(result.edge, /No layer/); assert.match(result.wrongAxis, /horizontally/);
    assert.match(result.ordered, /CSS order/); assert.deepEqual(result.orderAfterFailure, ['First', 'Second']);
    assert.equal(result.reversed, 'Second'); assert.equal(result.rtl, 'Second'); assert.equal(result.column, 'Second');
    assert.deepEqual(result.grid, ['Two', 'Three', 'One', 'Four']);
    assert.deepEqual(result.delta, [1, 10]); assert.equal(result.textMoved, -2);
    assert.ok(result.width > 50 && result.height > 10); assert.equal(result.hug.mode, 'hug');
    assert.ok(result.hug.width > 50 && result.hug.height > 10);
    assert.ok(Math.abs(result.abs.delta - 10) < .1 && Math.abs(result.abs.width) < .1);
    assert.equal(result.abs.right, ''); assert.equal(result.abs.transform, '');
    assert.match(result.locked, /stylesheet prevents/); assert.ok(!result.lockStyle);
    assert.match(result.contents, /no box/); assert.match(result.absNote, /Positioned children/);
    await page.setContent(result.saved);
    assert.deepEqual(await page.locator('#row > div').allTextContents(), ['Pasted', 'Beta', 'Gamma', 'Alpha']);
    assert.equal(await page.locator('#text').evaluate(n => n.style.left), '-2px');
    const replay = await page.locator('#normal').evaluate(n => getComputedStyle(n).translate);
    assert.equal(replay, '1px 10px');
    await page.evaluate(() => { document.body.append(document.createElement('aside')); });
    await page.waitForTimeout(50);
    assert.deepEqual(await page.locator('#row > div').allTextContents(), ['Pasted', 'Beta', 'Gamma', 'Alpha'], 'Repeated replay preserves the final order');
    assert.deepEqual(errors, []);
    console.log('PASS: shared movement, visual flex/RTL/grid order, blocked feedback and rollback, normal/inline/anchored nudges, text Hug measurement, and saved movement replay.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
