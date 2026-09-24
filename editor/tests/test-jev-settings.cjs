/* The typed-judgment row in Settings -> Context and cost, rendered from the real
   component code. A switch that silently does nothing is worse than no switch,
   so the row has to say which state it is in: keyed, or key-missing. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');

(async () => {
  const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
  const start = app.indexOf('function WorkflowContextCostSection(');
  const component = app.slice(start, app.indexOf('\nfunction ', start + 10));
  const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html data-theme="light"><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 1400 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:' + server.address().port);
    await page.addStyleTag({ content: css + '\nbody{padding:24px}#root{width:620px;max-width:100%}' });
    for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js',
                       'https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js',
                       'https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) {
      await page.addScriptTag({ url });
    }
    await page.addScriptTag({ content: `
      const { useState } = React; const html = htm.bind(React.createElement);
      const RuntimeModelSettings = () => null;
      const ContractWriterModelControl = () => null;
      const RuntimeModelSelect = () => null;
      const fmtTokens = n => String(n);
      window.saved = [];
      function useContextCostConfig() {
        const [config, setConfig] = useState({ jevJudge: false, referenceReuse: true,
          compactQa: true, autoCompact: false, autoContinue: true, thresholdTokens: 400000 });
        const save = async patch => { window.saved.push(patch); setConfig(c => ({ ...c, ...patch })); };
        return { config, saving: false, error: "", save };
      }
      ${component}
      function Fixture() {
        const [keyed, setKeyed] = useState(false);
        return html\`<div>
          <button id="flip" onClick=\${() => setKeyed(k => !k)}>flip</button>
          <\${WorkflowContextCostSection} mediaConfig=\${{ providers: { typesafe: { has_key: keyed } } }}/>
        </div>\`;
      }
      ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Fixture));
    ` });

    const toggle = page.getByLabel('Use typed judgment for checks that support it');
    await toggle.waitFor();
    assert.equal(await toggle.isChecked(), false, 'typed judgment must default OFF');

    // With no key the row says the switch changes nothing, rather than implying it works.
    await assert.doesNotReject(page.getByText('No TypeSafe key yet', { exact: false }).waitFor({ timeout: 2000 }));

    await toggle.check();
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { jevJudge: true });
    assert.equal(await toggle.isChecked(), true);
    await toggle.uncheck();
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { jevJudge: false });

    await page.locator('#flip').click();
    await assert.doesNotReject(page.getByText('TypeSafe key configured', { exact: false }).waitFor({ timeout: 2000 }));

    // It belongs to the checks it accelerates, not to compaction.
    const group = page.locator('.workflow-default-providers', { hasText: 'Typed judgment' }).first();
    assert.match(await group.innerText(), /requirement QA, design-system conformance and direction picking/);

    assert.deepEqual(errors, [], 'no page errors');
    console.log('PASS: typed-judgment settings row - defaults off, persists both ways, states its key status.');
  } finally {
    await browser.close();
    server.close();
  }
})();
