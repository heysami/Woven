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
    dsFound: { components: [{ cls: 'btn' }], offSystem: [] },
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
      ${app.slice(app.indexOf('const JUDGE_AXIS_LABEL'), app.indexOf('\n', app.indexOf('const JUDGE_AXIS_LABEL')) + 1)}
      ${slice('function JudgeProposal(')}
      window.replies = []; window.decisions = [];
      async function postRunReply(runId, text) { window.replies.push(text); }
      const _fetch = window.fetch;
      window.fetch = (u, o) => { if (String(u).includes('/__decision/')) { window.decisions.push(JSON.parse(o.body)); return Promise.resolve({ ok: true, json: async () => ({}) }); } return _fetch(u, o); };
      function Picker({ data }) {
        const [ans, setAns] = useState(undefined);
        return React.createElement(JudgeProposal, { data, runId: 'r1', answered: ans, onAnswered: (k, v) => setAns(v) });
      }
      window.renderProposal = (data) => { const d = document.createElement('div'); d.id = 'jp' + (data.error ? 'e' : '');
        document.body.appendChild(d); ReactDOM.createRoot(d).render(React.createElement(Picker, { data })); };
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
    // The text judge's ranking of the library, under the first message.
    await page.evaluate(() => window.renderProposal({ provider: 'clef', ms: 1600, needsDirection: 0.66,
      thresholds: { low: 0.45, high: 0.7 },
      axes: { style: { top: [{ id: 'pixel-grid-bitmap', label: 'pixel grid bitmap', p: 0.8 }, { id: 'flat-design', label: 'flat design', p: 0.03 }] },
              aesthetic: { top: [{ id: 'pixel-ps1', label: 'pixel ps1', p: 0.16 }] } },
      proposals: [0, 1, 2].map(i => ({ spread: 'aesthetic', picks: {
        shell: { id: 'canvas', label: 'canvas floating panels', p: 0.23 },
        style: { id: 'pixel-grid-bitmap', label: 'pixel grid bitmap', p: 0.8, preview: 'design-library/style-pixel-bitmap-ui.png' },
        aesthetic: { id: 'a' + i, label: ['pixel ps1', '8 bit generic', 'pixel modern cozy'][i], p: [0.16, 0.15, 0.14][i],
                     preview: 'design-library/aesthetic-x-ui.png' } } })) }));
    await page.evaluate(() => window.renderProposal({ error: 'no text judge is set up' }));
    await page.waitForSelector('#jp .chat-judge-option');
    const jp = await page.locator('#jp').innerText();
    assert.match(jp, /Judge's 3 proposals from the library/);
    assert.match(jp, /Cloudflare Clef · 1\.6 s/);
    assert.equal(await page.locator('#jp .chat-judge-option').count(), 3);
    assert.equal(await page.locator('#jp .chat-judge-option').first().locator('img').count(), 2,
      'each part with a library preview shows it');
    assert.match(await page.locator('#jp .chat-judge-option').nth(1).innerText(), /Aesthetic\s+8 bit generic 0\.15/);
    assert.match(jp, /the three differ in aesthetic/);
    await page.locator('#jp summary').click();
    assert.equal(await page.locator('#jp .chat-judge-pick.is-strong').innerText(), 'pixel grid bitmap 0.80',
      'in the full ranking, a pick over the high threshold stands out');
    assert.match(await page.locator('#jpe').innerText(), /Could not rank the library: no text judge is set up/);
    // A pick IS the direction decision: sent as the reply and saved with the library ids.
    await page.locator('#jp .chat-judge-option').nth(1).getByRole('button', { name: 'Use this' }).click();
    await page.waitForFunction(() => window.decisions.length === 1);
    assert.deepEqual(await page.evaluate(() => window.replies),
      ['[decision:prototype-direction] judge2 - shell canvas, style pixel-grid-bitmap, aesthetic a1']);
    assert.deepEqual(await page.evaluate(() => window.decisions[0].detail),
      { shell: 'canvas', style: 'pixel-grid-bitmap', aesthetic: 'a1', source: 'judge' });
    assert.equal(await page.locator('#jp .chat-judge-option').nth(1).getByRole('button').innerText(), 'Chosen');
    assert.equal(await page.locator('#jp .chat-judge-option').nth(0).getByRole('button').isDisabled(), true,
      'one direction: the others close');
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
