/* The typed-judgment rows in Settings, rendered from the real component code:
   Context and cost -> Typed judgment (two tiers, a Judge pick each, a Mode, a
   status line) and the Model Config key rows for the judges (extra fields,
   keyless Local Clef, the "reads images" status). A switch that silently does
   nothing is worse than no switch, so the section has to say which judge
   answers each tier, and a judge that is not set up never appears in a pick. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');

function slice(app, name) {
  const start = app.indexOf(name);
  assert.ok(start >= 0, 'missing ' + name);
  return app.slice(start, app.indexOf('\nfunction ', start + 10));
}

(async () => {
  const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
  const section = slice(app, 'function WorkflowContextCostSection(');
  const status = slice(app, 'function useJudgeStatus(');
  const rowStart = app.indexOf('const JUDGE_IMAGES_LABEL');
  const providerRow = app.slice(rowStart, app.indexOf('\nfunction ', app.indexOf('function WorkflowProviderSection(')));
  const media = fs.readFileSync(path.join(__dirname, '../prompts/media-models.js'), 'utf8');
  const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html data-theme="light"><head><meta charset="utf-8"></head><body><div id="root"></div></body></html>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 1600 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:' + server.address().port);
    await page.addStyleTag({ content: css + '\nbody{padding:24px}#root{width:620px;max-width:100%}' });
    for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js',
                       'https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js',
                       'https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) {
      await page.addScriptTag({ url });
    }
    await page.addScriptTag({ content: media });
    await page.addScriptTag({ content: `
      const { useState, useEffect } = React; const html = htm.bind(React.createElement);
      const RuntimeModelSettings = () => null;
      const ContractWriterModelControl = () => null;
      const RuntimeModelSelect = () => null;
      const fmtTokens = n => String(n);
      const apiUrl = p => p;
      const uiAlert = m => { window.alerted = m; };
      const uiConfirm = async () => true;
      window.saved = [];
      window.posted = [];
      // The daemon, as far as these rows can see it.
      window.judgeStatus = {
        text: { id: "jev", name: "TypeSafe Jev" }, image: null,
        auto: { text: { id: "jev", name: "TypeSafe Jev" }, image: null },
        providers: [
          { id: "jev", name: "TypeSafe Jev", keyed: true, tiers: ["text"], maxImages: 0, imagesVerified: null },
          { id: "clef", name: "Cloudflare Clef", keyed: false, tiers: ["text", "image"], maxImages: 4, imagesVerified: null },
          { id: "openai", name: "OpenAI Decisions", keyed: false, tiers: ["text", "image"], maxImages: null, imagesVerified: null },
        ] };
      window.fetch = async (url, opts) => {
        if (url === "/__judge/status") return { ok: true, json: async () => window.judgeStatus };
        if (url === "/__media_config") { window.posted.push(JSON.parse(opts.body)); return { ok: true, json: async () => ({ ok: true }) }; }
        if (url.startsWith("/__media_config/test")) return { ok: true, json: async () => ({ ok: true }) };
        throw new Error("unexpected fetch " + url);
      };
      function useContextCostConfig() {
        const [config, setConfig] = useState({ jevJudge: false, typedJudgeVisual: false,
          typedJudgeTextProvider: "auto", typedJudgeImageProvider: "auto", typedJudgeVisualMode: "shadow",
          referenceReuse: true, compactQa: true, autoCompact: false, autoContinue: true, thresholdTokens: 400000 });
        const save = async patch => { window.saved.push(patch); setConfig(c => ({ ...c, ...patch })); };
        return { config, saving: false, error: "", save };
      }
      ${status}
      ${section}
      ${providerRow}
      function Fixture() {
        const [tick, setTick] = useState(0);
        const [rows, setRows] = useState({
          typesafe: { has_key: true, judgeImages: "text" },
          cloudflare: { has_key: true, fields: { account_id: null }, judgeImages: "reads", imagesVerified: true },
          clef_local: { has_key: false, fields: { endpoint: null }, judgeImages: "unchecked" },
          openai: { has_key: true, judgeImages: "unchecked" },
        });
        window.setRows = setRows;
        const P = window.TH_MEDIA.providers;
        return html\`<div>
          <button id="rescan" onClick=\${() => setTick(t => t + 1)}>rescan</button>
          <\${WorkflowContextCostSection} mediaConfig=\${{ tick }}/>
          \${["typesafe", "cloudflare", "clef_local", "openai"].map(id => html\`
            <div data-row=\${id} key=\${id}>
              <\${WorkflowProviderSection} provider=\${P[id]} status=\${rows[id]} onChanged=\${async () => {
                // As the dialog does: re-read the saved entry after a change.
                const last = window.posted.at(-1) || {};
                if (last[id]) setRows(r => ({ ...r, [id]: { ...r[id], fields: { ...(r[id].fields || {}), ...last[id] } } }));
              }}/>
            </div>\`)}
        </div>\`;
      }
      ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Fixture));
    ` });

    // ── Context and cost -> Typed judgment ──────────────────────────────────
    const textToggle = page.getByLabel('Use typed judgment for text checks');
    const visualToggle = page.getByLabel('Use typed judgment for visual checks');
    await textToggle.waitFor();
    assert.equal(await textToggle.isChecked(), false, 'text checks must default OFF');
    assert.equal(await visualToggle.isChecked(), false, 'visual checks must default OFF');

    await textToggle.check();
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { jevJudge: true });
    await visualToggle.check();
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { typedJudgeVisual: true });
    await visualToggle.uncheck();
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { typedJudgeVisual: false });

    // Auto is named by what it resolves to; only judges that are set up appear.
    const textPick = page.locator('#typed-judge-text');
    const imagePick = page.locator('#typed-judge-image');
    await page.waitForFunction(() => document.querySelector('#typed-judge-text option')?.textContent === 'Auto: TypeSafe Jev');
    assert.deepEqual(await textPick.locator('option').allTextContents(), ['Auto: TypeSafe Jev', 'TypeSafe Jev']);
    assert.deepEqual(await imagePick.locator('option').allTextContents(), ['Auto: none set up'],
      'Jev reads no images and nothing else is keyed, so the image pick offers nothing');
    const statusLine = page.locator('[role=status]', { hasText: 'Text:' });
    assert.equal((await statusLine.innerText()).trim(),
      'Text: TypeSafe Jev. No judge that reads images is set up. Add a Cloudflare or OpenAI key under Model Config, API keys.');

    // A Cloudflare key arrives: the picks and the status line follow.
    await page.evaluate(() => {
      const s = window.judgeStatus;
      s.providers[1].keyed = true; s.image = { id: "clef", name: "Cloudflare Clef" };
      s.auto.image = { id: "clef", name: "Cloudflare Clef" };
    });
    await page.locator('#rescan').click();
    await page.waitForFunction(() => document.querySelector('#typed-judge-image option')?.textContent === 'Auto: Cloudflare Clef');
    assert.deepEqual(await imagePick.locator('option').allTextContents(), ['Auto: Cloudflare Clef', 'Cloudflare Clef']);
    assert.deepEqual(await textPick.locator('option').allTextContents(),
      ['Auto: TypeSafe Jev', 'TypeSafe Jev', 'Cloudflare Clef']);
    assert.equal((await statusLine.innerText()).trim(), 'Text: TypeSafe Jev. Images: Cloudflare Clef.');
    for (const opt of await page.locator('#typed-judge-text option, #typed-judge-image option').allTextContents()) {
      assert.ok(!/OpenAI/.test(opt), 'a judge with no key never appears in a pick');
    }

    await imagePick.selectOption('clef');
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { typedJudgeImageProvider: 'clef' });
    await page.locator('#typed-judge-mode').selectOption('flag');
    assert.deepEqual(await page.evaluate(() => window.saved.at(-1)), { typedJudgeVisualMode: 'flag' });
    assert.deepEqual(await page.locator('#typed-judge-mode option').allTextContents(), ['Shadow', 'Flag']);

    const group = page.locator('.workflow-default-providers', { hasText: 'Typed judgment' }).first();
    assert.match(await group.innerText(), /Frame judge, sprite facing and visual requirement items/);

    // ── Model Config -> API keys rows ───────────────────────────────────────
    const row = id => page.locator(`[data-row="${id}"]`);
    assert.equal((await row('typesafe').locator('.workflow-settings-images').innerText()).trim(), 'Text only');
    assert.equal((await row('cloudflare').locator('.workflow-settings-images').innerText()).trim(), 'Reads images');
    assert.equal((await row('clef_local').locator('.workflow-settings-images').innerText()).trim(), 'Not checked');
    assert.equal(await row('openai').locator('.workflow-settings-images').count(), 0,
      'the OpenAI row stays quiet until a Test has checked the judge');
    assert.match(await row('cloudflare').innerText(), /Cloudflare \(Clef\)/);
    assert.match(await row('clef_local').innerText(), /Local Clef/);

    // Cloudflare: an Account ID field above the token, saved into its entry.
    const acct = row('cloudflare').getByLabel('Account ID');
    await acct.fill('abc123');
    await acct.press('Enter');
    await page.waitForFunction(() => window.posted.length > 0);
    assert.deepEqual(await page.evaluate(() => window.posted.at(-1)), { cloudflare: { account_id: 'abc123' } });
    await page.waitForFunction(() => document.querySelector('[data-row=cloudflare] input[aria-label="Account ID"]').value === 'abc123');

    // Local Clef: no key input at all; the endpoint shows its default and Test
    // works before anything is saved.
    assert.equal(await row('clef_local').locator('input[type=password]').count(), 0);
    const endpoint = row('clef_local').getByLabel('Endpoint');
    assert.equal(await endpoint.getAttribute('placeholder'), 'http://localhost:11434/v1/systemone');
    const localTest = row('clef_local').getByRole('button', { name: 'Test' });
    assert.equal(await localTest.isDisabled(), false, 'a keyless judge is testable with no key');
    await localTest.click();
    await assert.doesNotReject(row('clef_local').getByText('Local Clef answered.').waitFor({ timeout: 2000 }));

    assert.deepEqual(errors, [], 'no page errors');
    console.log('PASS: typed-judgment settings - two tiers, keyed-only picks, status line, judge key rows.');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
