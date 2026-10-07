/* The `@designsystem` picker has to reach ONE rendered permutation, not just
   the section that holds dozens of them. Its reference is the class
   COMBINATION the gallery actually renders (".btn.btn--outline-mono
   .is-pressed"), so this covers the two pieces that produce it: the combo
   scan over gallery markup, and apiUrl's fragment handling - a `?project=`
   appended AFTER a `#anchor` is swallowed by the fragment, and the preview
   then silently renders whatever project happens to be active. */
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require('../tools/node_modules/playwright');

const APP = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');

// Lift a module-scope declaration out of app.js by name. app.js is not
// importable (one huge browser module) and a copy of these functions in the
// test would only ever prove the copy right, so the source is read verbatim.
//
// The body runs to the next COLUMN-ZERO declaration rather than to a matched
// closing brace: these functions are dense with regex literals containing
// braces (/(?:^|[},{])\s*([^{}@][^{}]*)\{/), and a brace counter walking raw
// text cannot tell those from real ones.
const BOUNDARY = /\n(?=(?:async function |function |const |let |\/\/|\/\*))/g;
function lift(name) {
  let i = APP.indexOf(`function ${name}(`);
  if (i < 0) i = APP.indexOf(`const ${name} =`);
  assert.ok(i >= 0, `cannot find ${name} in app.js`);
  BOUNDARY.lastIndex = i + 1;
  const m = BOUNDARY.exec(APP);
  const body = APP.slice(i, m ? m.index : APP.length);
  // Trailing comment lines belong to the NEXT declaration, and an unclosed
  // block comment would take the rest of the test down with it.
  const trimmed = body.replace(/\n\s*(?:\/\/[^\n]*|\/\*[\s\S]*)$/, '');
  // A direct eval keeps its `const`/`let` bindings to itself and only lets
  // `function` declarations reach the enclosing scope, so the arrow-function
  // helpers have to arrive as `var` or the rest cannot see them.
  return trimmed.replace(/^(?:const|let) /, 'var ');
}

const NAMES = ['escAttr', 'apiUrl', '__pickerGallerySections', '__pickerSectionCombos',
               '__pickerParseDsCss', '__pickerClassRoot', '__pickerSignatureRoots'];

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.setContent('<!doctype html><html><body></body></html>');

    const gallery = fs.readFileSync(path.join(__dirname, '../default-design-system/gallery.html'), 'utf8');
    const css     = fs.readFileSync(path.join(__dirname, '../default-design-system/styles.css'), 'utf8');
    const src     = NAMES.map(lift).join('\n');

    const out = await page.evaluate(({ src, gallery, css }) => {
      let activeProjectId = () => 'proj-a';
      eval(src);

      // --- apiUrl: the query must land BEFORE the fragment ---
      const plain   = apiUrl('/design-systems/x/gallery.html');
      const anchored= apiUrl('/design-systems/x/gallery.html#c-button');
      const queried = apiUrl('/__list_files?root=a');
      activeProjectId = () => '';
      const unscoped = apiUrl('/design-systems/x/gallery.html#c-button');
      activeProjectId = () => 'proj-a';

      // --- combos over the real default gallery ---
      const sections = __pickerGallerySections(gallery);
      const combos   = __pickerSectionCombos(gallery);
      const vocab    = __pickerParseDsCss(css);

      const doc = new DOMParser().parseFromString(gallery, 'text/html');
      const rows = [];
      for (const sec of sections) {
        const roots = __pickerSignatureRoots(sec.code).cls;
        if (!roots.size) continue;
        const seen = new Set();
        for (const row of (combos.get(sec.id) || [])) {
          const cls = row.classes.filter(c => vocab.classes.has(c));
          if (cls.length < 2) continue;
          if (!cls.some(c => roots.has(__pickerClassRoot(c)))) continue;
          const sel = '.' + cls.join('.');
          if (seen.has(sel)) continue;
          seen.add(sel);
          rows.push({ sec: sec.id, sel, group: row.group,
                      el: '#' + escAttr(sec.id) + ' ' + cls.map(c => '.' + escAttr(c)).join('') });
        }
      }
      // Every emitted selector must resolve, inside its own section.
      const unresolved = rows.filter(r => {
        const hit = doc.querySelector(r.el);
        return !hit || hit.closest('section[id]').id !== r.sec;
      }).map(r => r.el);

      return {
        plain, anchored, queried, unscoped,
        rowCount: rows.length,
        unresolved,
        // gallery chrome lives in the gallery's own <style>, never the DS
        // sheet, so the vocab filter alone must keep it out
        chrome: rows.filter(r => /\.(comp|vgroup|matrix)\b/.test(r.sel)).map(r => r.sel),
        button: rows.filter(r => r.sec === 'c-button').map(r => r.sel),
        grouped: rows.filter(r => r.group).length,
      };
    }, { src, gallery, css });

    assert.deepEqual(errors, [], 'page errors: ' + errors.join('; '));

    // apiUrl
    assert.equal(out.plain,    '/design-systems/x/gallery.html?project=proj-a');
    assert.equal(out.anchored, '/design-systems/x/gallery.html?project=proj-a#c-button',
      'the query must precede the fragment, or the server never sees project=');
    assert.equal(out.queried,  '/__list_files?root=a&project=proj-a');
    assert.equal(out.unscoped, '/design-systems/x/gallery.html#c-button', 'no project, no rewrite');

    // combos
    assert.ok(out.rowCount > 100, `expected a real permutation list, got ${out.rowCount}`);
    assert.deepEqual(out.unresolved, [], 'every combo selector must resolve inside its own section');
    assert.deepEqual(out.chrome, [], 'gallery chrome leaked into the component vocabulary');
    assert.ok(out.grouped > 0, 'no combo picked up its <h5> group label');
    assert.ok(out.button.includes('.btn.btn--primary'), 'missing the plain primary button');
    assert.ok(out.button.some(s => /^\.btn\.btn--\w[\w-]*\.is-/.test(s)),
      'missing a variant x state permutation - the whole point of the combo row');
    assert.ok(out.button.length >= 10, `c-button should expose many permutations, got ${out.button.length}`);

    console.log(`ok - ${out.rowCount} variant rows, ${out.button.length} on c-button, apiUrl fragment-safe`);
  } finally {
    await browser.close();
  }
})();
