/* Exercise real model pickers without mounting a chat or hardcoding new models. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');

const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
const between = (start, end) => {
  const a = app.indexOf(start), b = app.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, 'component markers exist');
  return app.slice(a, b);
};
const fn = name => between('function ' + name + '(', '\nfunction ');
const components = [
  between('let __runtimeCustomModels', 'function loadSteerableAgents('),
  between('function useContextCostConfig(', 'function WorkflowContextCostSection('),
  ...['listModelsForCapability', 'listOrchestratorModelChoices', 'WorkflowDefaultProviderRow',
    'OrchestratorModelSelect', 'SubagentModelSelect', 'AssistantModelSelect',
    'AssetActionRemixProviderRow'].map(fn),
].join('\n');
const astra = { id: 'codex:gpt-6-astra', model: 'gpt-6-astra', runtime: 'codex', label: 'GPT-6-Astra', modalities: ['text', 'image'] };
const packet = checkedAt => ({ runtime: 'codex', checkedAt, source: 'authenticated runtime model/list', models: [astra] });
const privateModel = { id: 'codex:private-model', model: 'private-model', runtime: 'codex', label: 'Private model' };
const selectors = ['#agent select', '#writer select', '#summary select', '#orchestrator select', '#subagent select', '#assistant select', '#remix select'];

(async () => {
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  const origin = 'http://127.0.0.1:' + server.address().port;
  try {
    for (const scenario of ['cold', 'cached', 'stale', 'failed-refresh']) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      let discovery = scenario === 'cold' ? {} : { codex: packet(scenario === 'cached' ? Date.now() / 1000 : 1) };
      let config = { modelCatalog: [privateModel], contractWriterModel: 'fast', summaryModel: 'fast', helperConcurrency: { codex: 2 } };
      let reads = 0, refreshes = 0;
      const writes = [];
      await page.route(origin + '/__**', async route => {
        const request = route.request();
        const pathname = new URL(request.url()).pathname;
        let result;
        let status = 200;
        if (pathname === '/__models') {
          reads++;
          result = { custom: config.modelCatalog, discovery };
        } else if (pathname === '/__media_config') {
          result = { codex_cli_available: true, opencode_cli_available: false };
        } else if (pathname === '/__models/refresh') {
          refreshes++;
          assert.equal(request.postDataJSON().runtime, 'codex', 'only an installed discoverable runtime is probed');
          if (scenario === 'failed-refresh') { status = 502; result = { error: 'Runtime is offline', cachedModelsRetained: true }; }
          else {
            // Let the pickers mount with an empty catalog before discovery finishes.
            await new Promise(resolve => setTimeout(resolve, 75));
            result = packet(Date.now() / 1000);
            discovery = { codex: result };
          }
        } else if (pathname === '/__compact_config') {
          if (request.method() === 'POST') {
            const patch = request.postDataJSON();
            writes.push(patch);
            config = { ...config, ...patch };
          }
          result = config;
        } else throw new Error('Unexpected endpoint ' + pathname);
        await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(result) });
      });
      await page.goto(origin);
      for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js', 'https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js', 'https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) await page.addScriptTag({ url });
      await page.addScriptTag({ content: `
        const { useState, useEffect, useMemo } = React;
        const html = htm.bind(React.createElement);
        const apiUrl = p => p;
        let __steerableAgentsPromise = null;
        window.TH_MEDIA = { textModels: [{id:'gpt-5.6-sol',provider:'openai',label:'Sol',integrated:true}], providers: {openai:{label:'OpenAI'}} };
        const CAPABILITY_LABELS = {agent:'Agent'}, CAPABILITY_MODEL_PER_CONTENT = {};
        const modelPinnableAsDefault = () => true, defaultModelNeedsInput = () => false;
        const _pickAutoForCapability = () => null, _providerAvailability = () => ({ok:true,source:'cli'});
        const getActiveAgentProvider = () => 'openai', getDefaultForCapability = () => null;
        const getOrchestratorModel = () => null, getSubagentModel = () => null;
        const saveOrchestratorModel = (id, value) => { window.lastSelection = value; };
        const saveSubagentModel = saveOrchestratorModel;
        const uiPrompt = async () => null;
        ${components}
        function Fixture() {
          const { config, save } = useContextCostConfig();
          const [shown, setShown] = useState(true);
          const [agent, setAgent] = useState({provider:'openai',model:'gpt-5.6-sol'});
          const [form, setForm] = useState({outputKind:'html',provider:'openai',model:'gpt-5.6-sol'});
          return html\`<div>
            <button onClick=\${() => setShown(s => !s)}>Toggle pickers</button>
            <button onClick=\${() => save({referenceReuse:true})}>Save preference</button>
            <\${RuntimeModelSettings} config=\${config} save=\${save}/>
            \${shown && html\`<div>
              <div id="agent"><\${WorkflowDefaultProviderRow} capability="agent" value=\${agent} onChange=\${value => {setAgent(value);window.lastSelection=value;}}/></div>
              <div id="writer"><\${ContractWriterModelControl} config=\${config} save=\${save}/></div>
              <div id="summary"><\${RuntimeModelSelect} config=\${config} current=\${config?.summaryModel || 'fast'} label="Summary model" onChange=\${value => save({summaryModel:value})}/></div>
              <div id="orchestrator"><\${OrchestratorModelSelect} orchestratorId="review"/></div>
              <div id="subagent"><\${SubagentModelSelect} name="reviewer"/></div>
              <div id="assistant"><\${AssistantModelSelect} onChange=\${value => {window.lastSelection=value;}}/></div>
              <div id="remix"><\${AssetActionRemixProviderRow} form=\${form} setForm=\${setForm}/></div>
            </div>\`}
          </div>\`;
        }
        ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Fixture));
      ` });
      const verifyOptions = async () => {
        for (const selector of selectors) {
          await page.locator(selector + ' option[value="codex:gpt-6-astra"]').waitFor({ state: 'attached' });
          assert.equal(await page.locator(selector + ' option[value="codex:gpt-6-astra"]').count(), 1);
          assert.equal(await page.locator(selector + ' option[value="codex:private-model"]').count(), 1);
        }
      };
      await verifyOptions();
      await page.evaluate(() => loadRuntimeModelCatalog());
      assert.equal(reads, 1, 'picker mounts share one catalog load');
      assert.equal(refreshes, scenario === 'cached' ? 0 : 1, 'fresh cache avoids a CLI probe');
      assert.deepEqual(writes, [], 'discovery must not change preferences or register discovered models');
      assert.equal(await page.locator('#agent select').nth(1).inputValue(), 'gpt-5.6-sol', 'discovery preserves the current selection');
      await page.locator('#agent select').nth(1).selectOption(astra.id);
      assert.deepEqual(await page.evaluate(() => window.lastSelection), { provider: 'openai', model: astra.id });
      await page.locator('#subagent select').selectOption(astra.id);
      assert.deepEqual(await page.evaluate(() => window.lastSelection), { provider: 'openai', model: astra.id });
      const revision = await page.evaluate(() => __runtimeCustomRevision);
      await page.getByRole('button', { name: 'Save preference', exact: true }).click();
      await page.waitForFunction(before => __runtimeCustomRevision > before, revision);
      assert.deepEqual(writes, [{ referenceReuse: true }]);
      await verifyOptions();
      await page.getByRole('button', { name: 'Toggle pickers', exact: true }).click();
      await page.getByRole('button', { name: 'Toggle pickers', exact: true }).click();
      await verifyOptions();
      assert.equal(reads, 1, 'remounts are coalesced');
      await page.getByRole('button', { name: 'Refresh models', exact: true }).click();
      await page.getByRole('status').filter({ hasText: scenario === 'failed-refresh' ? 'Runtime is offline' : '1 models: authenticated' }).waitFor();
      await verifyOptions();
      assert.deepEqual(config.modelCatalog, [privateModel], 'manual refresh does not copy discovery into registration');
      assert.deepEqual(errors, []);
      console.log('PASS: ' + scenario + ' catalog, seven pickers, exact selection, preference save, remount, and manual refresh');
      await page.close();
    }
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
