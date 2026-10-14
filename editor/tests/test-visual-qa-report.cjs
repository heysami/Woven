/* A visual-qa subagent's report inside its Tasks & subagents panel, rendered
   from the real component code. Only what was sent to the judge and what came
   back: the counts for every answer, then each "sure no" and "unsure" with the
   images it was asked about, the question, the answer and its confidence. A
   sure yes is counted, never listed, and nothing else (dates, file names,
   sizes, crop labels, timings) is shown. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');

const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
function slice(head) {
  const start = app.indexOf(head);
  assert.ok(start >= 0, 'missing ' + head);
  return app.slice(start, app.indexOf('\n}\n', start) + 2);
}
const constLine = name => { const i = app.indexOf('const ' + name + ' ='); return app.slice(i, app.indexOf('\n', i) + 1); };

const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
const report = {
  id: '20261013-161310-ab12cd', page: 'source/prototype/fa-application.html', created: '2026-10-13 16:13:10',
  url: 'http://127.0.0.1:5747/x', verdict: 'pass', sizes: { 'screen_00.png': [1280, 1482] },
  typedChecks: {
    provider: 'clef', mode: 'shadow',
    calls: [
      { n: 1, state: 'A screenshot of a web page.', ms: 600, images: [{ file: 'sent_01_1.png', label: 'screen 1 cropped to #chip', width: 388, height: 52, bytes: 8300 }] },
      { n: 2, state: 'A screenshot of a web page: image 1 is ref, image 2 is crop.', images: [{ file: 'ref_btn.png', label: 'ref' }, { file: 'sent_02_2.png', label: 'crop' }] },
      { n: 3, state: 'A screenshot of a web page.', images: [{ file: 'sent_03_1.png', label: 'screen 1 cropped to #title' }] },
    ],
    checks: [
      { id: 's0_txt_10', call: 1, status: 'answered', band: 'act', passed: false, noul: 0.02, confidence: 0.96,
        question: { type: 'noul', instructions: 'The image shows the text "Applications close 30 June 2026", fully readable and not covered.' } },
      { id: 's0_btn', call: 2, status: 'answered', band: 'escalate', passed: true, noul: 0.66, confidence: 0.32,
        question: { type: 'noul', instructions: 'Image 2 shows the same Button component as image 1, in the same visual style.' },
        escalation: { value: true, passed: true, note: 'same primary button' } },
      { id: 's0_txt_1', call: 3, status: 'answered', band: 'act', passed: true, noul: 0.98, confidence: 0.96,
        question: { type: 'noul', instructions: 'The image shows the text "Choose the support you need", fully readable and not covered.' } },
      { id: 's0_gone', status: 'not-visible', message: '#toast is not visible' },
    ],
    elements: { mode: 'page', message: '2 judge call(s) via clef: 1 finding(s)' },
    findings: [{ id: 's0_d1', kind: 'covered', count: 9, confirmed: true, label: 'fm fail "No bursary awarded"',
                 within: 'Data grid', measured: 'it and the next cell overlap by 24x18px', judged: '2 of 2 crops show it' }],
  },
};

(async () => {
  const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/__qa/visual-report/file')) { res.setHeader('Content-Type', 'image/png'); return res.end(PNG); }
    if (req.url.startsWith('/__qa/visual-report')) { res.setHeader('Content-Type', 'application/json'); return res.end(JSON.stringify(report)); }
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html data-theme="light"><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>');
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 520, height: 900 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:' + server.address().port);
    await page.addStyleTag({ content: css });
    for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js',
                       'https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js',
                       'https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) {
      await page.addScriptTag({ url });
    }
    await page.addScriptTag({ content: `
      const { useState, useEffect } = React; const html = htm.bind(React.createElement);
      const apiUrl = p => p;
      ${slice('function visualQaReportIds(')}
      ${constLine('VQA_ORDER')}
      ${slice('function visualQaOutcome(')}
      ${slice('function VisualQaReport(')}
      const _judgeCounts = new Map();
      ${slice('function JudgeMark(')}
      const Icon = { Bot: () => null, Refresh: () => null };
      const chatRowsToEvents = rows => rows;
      function extractRunSubagents() { return []; }
      const { useRef } = React;
      ${slice('function SubagentPanel(')}
      window.renderPanel = () => ReactDOM.createRoot(document.getElementById('panel')).render(
        html\`<\${SubagentPanel} agent=\${{ id: 'a1', type: 'woven:visual-qa', label: 'Visual QA', done: true,
          prompt: 'Project root: /x. Pages: fa-application.html.', actions: ['Running QA', 'Reading answers'],
          result: 'VISUAL-QA FAIL - fa-application.html\\nfa-application.html: QA pass · report 20261013-161310-ab12cd' }}/>\`);
      const ids = visualQaReportIds("VISUAL-QA FAIL - fa-application.html\\nfa-application.html: QA pass · 3 criteria · report 20261013-161310-ab12cd\\n- CONFIRMED s0_txt_10: covered");
      window.ids = ids;
      ReactDOM.createRoot(document.getElementById('root')).render(
        html\`<div>\${ids.map(id => html\`<\${VisualQaReport} key=\${id} id=\${id}/>\`)}</div>\`);
    ` });
    await page.waitForSelector('.th-vqa-counts');
    assert.deepEqual(await page.evaluate(() => window.ids), ['20261013-161310-ab12cd']);
    assert.deepEqual(await page.locator('.th-vqa-counts span').allTextContents(), ['1 sure no', '1 unsure', '1 sure yes']);
    const rows = page.locator('.th-vqa-row');
    assert.equal(await rows.count(), 2, 'only the sure no and the unsure are listed');
    const text = await page.locator('.th-vqa').innerText();
    assert.match(text, /Applications close 30 June 2026/);
    assert.match(text, /covered\s*fm fail "No bursary awarded" · x9/i, 'each finding, counted, above the calls');
    assert.match(text, /overlap by 24x18px · 2 of 2 crops show it/);
    assert.match(text, /same Button component/);
    assert.match(text, /Looked: meets it, same primary button/);
    assert.doesNotMatch(text, /Choose the support you need/, 'a sure yes is never listed');
    for (const extra of ['screen_00', 'sent_01', '388', 'KB', 'cropped to', '2026-10-13', 'clef', 'shadow', '0.6 s', 'Found on']) {
      assert.ok(!text.includes(extra), 'shows nothing but what went to the judge: ' + extra);
    }
    const srcs = await page.locator('.th-vqa-imgs img').evaluateAll(els => els.map(e => e.getAttribute('src')));
    assert.deepEqual(srcs.map(s => decodeURIComponent(s.split('f=')[1])), ['sent_01_1.png', 'ref_btn.png', 'sent_02_2.png'],
      'the images of the listed calls, as sent; none of the sure-yes call');
    await page.waitForFunction(() => [...document.querySelectorAll('.th-vqa-imgs img')].every(i => i.complete && i.naturalWidth > 0));
    // The Subagents list marks a subagent that has a Judge tab.
    await page.evaluate(() => { const d = document.createElement('div'); d.id = 'mark'; document.body.appendChild(d);
      ReactDOM.createRoot(d).render(React.createElement(JudgeMark, { ids: ['20261013-161310-ab12cd'] })); });
    await page.waitForFunction(() => /unsure/.test(document.querySelector('#mark').innerText));
    assert.equal((await page.locator('#mark').innerText()).trim(), '· judge 1 no, 1 unsure');
    // The subagent panel: tabs, the judge's answers first.
    await page.evaluate(() => { const d = document.createElement('div'); d.id = 'panel'; document.body.appendChild(d); window.renderPanel(); });
    await page.waitForSelector('#panel [role=tab]');
    assert.deepEqual(await page.locator('#panel [role=tab]').allTextContents(), ['Judge', 'Result', 'Activity · 2', 'Prompt']);
    await page.waitForSelector('#panel .th-vqa-counts');
    assert.equal(await page.locator('#panel [role=tab][aria-selected=true]').innerText(), 'Judge');
    await page.locator('#panel [role=tab]', { hasText: 'Result' }).click();
    assert.match(await page.locator('#panel [role=tabpanel]').innerText(), /VISUAL-QA FAIL/);
    assert.equal(await page.locator('#panel .th-vqa').count(), 0, 'one tab at a time, no long scroll');
    await page.locator('#panel [role=tab]', { hasText: 'Prompt' }).click();
    assert.match(await page.locator('#panel [role=tabpanel]').innerText(), /Pages: fa-application.html/);
    assert.deepEqual(errors, []);
    console.log('PASS: visual-qa report - counts, only no and unsure, images as sent, nothing else; panel tabs.');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
