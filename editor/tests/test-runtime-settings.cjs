/* Browser coverage of the new settings controls using the real component code. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { chromium } = require('../tools/node_modules/playwright');

(async () => {
  const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
  const extractCode = app.slice(app.indexOf('function extractRunSubagents('), app.indexOf('/*', app.indexOf('function extractRunSubagents(')));
  const extract = vm.runInNewContext(extractCode + '\nextractRunSubagents');
  const events = [
    { type: 'tool_use', id: 'call', name: 'Agent', input: {} },
    { type: 'job', jobId: 'a', toolUseId: 'call', status: 'running' },
    { type: 'job', jobId: 'b', toolUseId: 'call', status: 'completed' },
  ].map(data => ({ event: 'agent', data }));
  assert.equal(extract(events)[0].done, false, 'one completed receiver must not hide a running receiver');
  events.push({ event: 'agent', data: { type: 'job', jobId: 'a', toolUseId: 'call', status: 'completed' } });
  assert.equal(extract(events)[0].done, true);
  const components = app.slice(app.indexOf('function RuntimeModelSelect('), app.indexOf('function WorkflowContextCostSection('));
  const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');
  const server = http.createServer((req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<!doctype html><html data-theme="light"><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>'); });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:' + server.address().port);
    await page.addStyleTag({ content: css + '\nbody{padding:24px}#root{width:620px;max-width:100%}' });
    for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js', 'https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js', 'https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) await page.addScriptTag({ url });
    await page.addScriptTag({ content: `
      const { useState } = React; const html = htm.bind(React.createElement);
      let __steerableAgentsPromise = null;
      window.TH_MEDIA = {textModels: []};
      const uiPrompt = async () => window.promptAnswer;
      const syncRuntimeModelCatalog = () => {};
      const apiUrl = p => p;
      ${components}
      function Fixture() {
        const [config, setConfig] = useState({economyModels:{codex:'gpt-5.6-luna',claude:'claude-haiku-4-5',opencode:'opencode-default'},runtimeDrivers:{codex:'exec',opencode:'run'},modelCatalog:[],contractWriterModel:'fast'});
        const save = async patch => { window.lastPatch = patch; setConfig(c => ({...c,...patch,economyModels:{...c.economyModels,...patch.economyModels},runtimeDrivers:{...c.runtimeDrivers,...patch.runtimeDrivers}})); };
        return html\`<div><\${RuntimeModelSettings} config=\${config} save=\${save}/><\${ContractWriterModelControl} config=\${config} save=\${save}/></div>\`;
      }
      ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Fixture));
    ` });
    await page.locator('#economy-codex').fill('gpt-6-astra');
    await page.locator('#economy-codex').blur();
    assert.deepEqual(await page.evaluate(() => window.lastPatch), { economyModels: { codex: 'gpt-6-astra' } });
    await page.locator('#driver-codex').selectOption('app-server');
    assert.deepEqual(await page.evaluate(() => window.lastPatch), { runtimeDrivers: { codex: 'app-server' } });
    await page.evaluate(() => { window.promptAnswer = 'gpt-6-astra'; });
    await page.getByRole('button', { name: 'Add model', exact: true }).click();
    await page.getByLabel('Contract and brief writer model').selectOption('codex:gpt-6-astra');
    assert.deepEqual(await page.evaluate(() => window.lastPatch), { contractWriterModel: 'codex:gpt-6-astra' });
    await page.evaluate(() => { window.promptAnswer = 'claude:claude-fable-5'; });
    await page.getByLabel('Contract and brief writer model').selectOption('__custom__');
    assert.deepEqual(await page.evaluate(() => window.lastPatch), { contractWriterModel: 'claude:claude-fable-5' });
    assert.deepEqual(errors, []);
    const screenshot = path.join(os.tmpdir(), 'woven-runtime-settings.png');
    await page.screenshot({ path: screenshot, fullPage: true });
    console.log('PASS: economy, transport, registration, and custom writer controls. Screenshot: ' + screenshot);
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
