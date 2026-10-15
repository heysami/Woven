/* The zoomable lightbox (ChatImageLightbox), rendered from the real component
   code: an image opens fitted, pinch zooms at the pointer, scroll and drag
   pan, the keys and the bar zoom and fit, a click on the image keeps it open
   and a click on the backdrop or Esc closes. A live page opens framed on its
   element. A loaded PickerPreview (the / @ = menus and the point-chip hover
   card) opens the lightbox on click, and useHoverHold keeps a hover card open
   across the trip from its trigger. */
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
const constLine = name => {
  const i = app.indexOf('const ' + name + ' =');
  assert.ok(i >= 0, 'missing const ' + name);
  return app.slice(i, app.indexOf('\n', i) + 1);
};

const PAGE = `<!doctype html><html><head><style>
  body { margin: 0; font: 16px sans-serif; } .spacer { height: 1400px; }
  #target { width: 200px; height: 100px; margin-left: 900px; background: #c33; }
</style></head><body><div class="spacer"></div><div id="target">target</div><div class="spacer"></div></body></html>`;

(async () => {
  const css = fs.readFileSync(path.join(__dirname, '../styles.css'), 'utf8');
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/page.html')) { res.setHeader('Content-Type', 'text/html'); return res.end(PAGE); }
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html data-theme="light"><head><meta charset="utf-8"></head><body><div id="root"></div><div id="pp"></div></body></html>');
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
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
      const { useState, useEffect, useRef, useCallback } = React;
      const html = htm.bind(React.createElement);
      const createPortal = ReactDOM.createPortal;
      const apiUrl = p => p;
      const Icon = { Minus: () => null, Plus: () => null, FitReset: () => null, X: () => null, Spark: () => null, NotesDoc: () => null, Crosshair: () => null };
      const SKILL_ICON = {};
      ${constLine('escAttr')}
      ${constLine('PICKER_PREVIEW_SETTLE_MS')}
      ${constLine('PICKER_PAGE_W')}
      ${constLine('PICKER_PAGE_H')}
      ${constLine('PICKER_FIT_PAD')}
      ${constLine('PICKER_FIT_MIN_W')}
      ${constLine('PICKER_FIT_MIN_SCALE')}
      ${constLine('__clamp')}
      ${constLine('LIGHTBOX_PAD')}
      ${constLine('LIGHTBOX_BAR')}
      ${constLine('LIGHTBOX_MAX')}
      ${slice('function dispatchChatImageZoom(')}
      ${slice('function dispatchPageZoom(')}
      ${slice('function lightboxFit(')}
      ${slice('function ChatImageLightbox(')}
      ${slice('function PickerPreview(')}
      ${slice('function useHoverHold(')}
      ReactDOM.createRoot(document.getElementById('root')).render(html\`<\${ChatImageLightbox}/>\`);
      window.mountPreview = (item) => ReactDOM.createRoot(document.getElementById('pp')).render(
        html\`<div style=\${{ width: '300px', padding: '20px' }}><\${PickerPreview} item=\${item}/></div>\`);
      window.hoverLog = [];
      function HoverProbe() {
        const [open, setOpen] = useState(true);
        const h = useHoverHold(() => { setOpen(false); window.hoverLog.push('closed'); }, 120);
        window.hoverApi = h;
        return open ? html\`<span id="probe">open</span>\` : null;
      }
      const probeRoot = document.createElement('div'); document.body.appendChild(probeRoot);
      ReactDOM.createRoot(probeRoot).render(html\`<\${HoverProbe}/>\`);
    ` });

    const st = () => page.evaluate(() => {
      const lb = document.querySelector('.chat-image-lightbox');
      if (!lb) return null;
      const c = lb.querySelector('.chat-image-lightbox-content');
      return { left: parseFloat(c.style.left), top: parseFloat(c.style.top), w: parseFloat(c.style.width), h: parseFloat(c.style.height),
               visible: c.style.visibility === 'visible', pct: lb.querySelector('.chat-image-lightbox-pct').textContent, kind: c.dataset.kind };
    });
    const ready = () => page.waitForFunction(() => document.querySelector('.chat-image-lightbox-content')?.style.visibility === 'visible', null, { timeout: 8000 });
    const wheel = (x, y, o) => page.evaluate(([x, y, o]) => document.querySelector('.chat-image-lightbox')
      .dispatchEvent(new WheelEvent('wheel', { clientX: x, clientY: y, bubbles: true, cancelable: true, ...o })), [x, y, o]);

    // ── an image ──
    const img = await page.evaluate(() => {
      const c = document.createElement('canvas'); c.width = 1600; c.height = 1000;
      const g = c.getContext('2d'); g.fillStyle = '#ddd'; g.fillRect(0, 0, 1600, 1000);
      return c.toDataURL('image/png');
    });
    await page.evaluate(u => dispatchChatImageZoom(u, 'test'), img);
    await ready();
    const fit = await st();
    assert.equal(fit.kind, 'image');
    // fitted inside the viewport minus the padding and the bar, never upscaled
    assert.ok(fit.w <= 1200 - 64 + 0.5 && fit.h <= 800 - 64 - 64 + 0.5, 'fits ' + JSON.stringify(fit));
    assert.ok(Math.abs(fit.w / fit.h - 1.6) < 0.01, 'keeps the aspect ratio');

    // pinch zooms at the pointer: the image point under it stays put
    const px = fit.left + fit.w * 0.25, py = fit.top + fit.h * 0.75;
    for (let i = 0; i < 5; i++) await wheel(px, py, { deltaY: -40, ctrlKey: true });
    const z = await st();
    assert.ok(z.w > fit.w * 2, 'pinch zooms in');
    assert.ok(Math.abs((px - z.left) / z.w - 0.25) < 0.005 && Math.abs((py - z.top) / z.h - 0.75) < 0.005, 'zooms at the pointer');
    // zoom stops at the cap
    for (let i = 0; i < 40; i++) await wheel(px, py, { deltaY: -60, metaKey: true });
    assert.equal((await st()).pct, '1200%', 'capped at 12x');
    await page.keyboard.press('0');

    // scroll pans, drag pans and does not close
    const a = await st();
    await wheel(600, 400, { deltaX: 30, deltaY: 70 });
    const b = await st();
    assert.ok(Math.abs(b.left - (a.left - 30)) < 0.5 && Math.abs(b.top - (a.top - 70)) < 0.5 && b.w === a.w, 'scroll pans');
    await page.mouse.move(600, 400); await page.mouse.down(); await page.mouse.move(650, 380, { steps: 4 }); await page.mouse.up();
    const c = await st();
    assert.ok(c && Math.abs(c.left - (b.left + 50)) < 1 && Math.abs(c.top - (b.top - 20)) < 1, 'drag pans and stays open');

    // keys and the bar
    await page.keyboard.press('1');
    assert.equal((await st()).pct, '100%', '1 shows actual size');
    await page.keyboard.press('-');
    assert.equal((await st()).pct, '80%', '- zooms out');
    await page.click('.chat-image-lightbox-bar [aria-label="Fit to screen"]');
    assert.ok(Math.abs((await st()).w - fit.w) < 0.5, 'Fit button fits');
    await page.click('.chat-image-lightbox-bar [aria-label="Actual size"]');
    assert.equal((await st()).pct, '100%', '1:1 button');
    await page.keyboard.press('0');

    // double-click: in at the pointer, then back to fit
    await page.mouse.dblclick(fit.left + fit.w / 2, fit.top + fit.h / 2);
    assert.ok(Math.abs((await st()).w - fit.w * 2) < 1, 'double-click zooms in');
    await page.mouse.dblclick(600, 380);
    assert.ok(Math.abs((await st()).w - fit.w) < 0.5, 'double-click again fits');

    // a click on the image keeps it, the backdrop or Esc closes
    await page.mouse.click(fit.left + 40, fit.top + 40);
    assert.ok(await st(), 'click on the image keeps it open');
    await page.mouse.click(8, 400);
    assert.equal(await st(), null, 'backdrop click closes');
    await page.evaluate(u => dispatchChatImageZoom(u, 'test'), img);
    await page.waitForSelector('.chat-image-lightbox');
    await page.keyboard.press('Escape');
    assert.equal(await st(), null, 'Esc closes');

    // ── a live page, framed on its element ──
    await page.evaluate(() => dispatchPageZoom({ src: '/page.html', el: '#target' }, 'page'));
    await ready();
    const p = await st();
    assert.equal(p.kind, 'page');
    const tgt = await page.evaluate(() => {
      const f = document.querySelector('.chat-image-lightbox-frame');
      const r = f.contentDocument.querySelector('#target').getBoundingClientRect();
      const s = parseFloat(document.querySelector('.chat-image-lightbox-content').style.width) / 1280;
      const c = document.querySelector('.chat-image-lightbox-content').getBoundingClientRect();
      return { cx: c.left + (r.left + r.width / 2) * s, cy: c.top + (r.top + r.height / 2) * s, s };
    });
    assert.ok(Math.abs(tgt.cx - 600) < 2 && Math.abs(tgt.cy - (800 - 64) / 2) < 2, 'element centred ' + JSON.stringify(tgt));
    assert.ok(tgt.s > 1 && tgt.s <= 2, 'element scaled up, at most 2x');
    await page.keyboard.press('Escape');

    // ── PickerPreview opens it on click ──
    await page.evaluate(() => mountPreview({ kind: 'file', ns: 'file', slug: 'p', name: 'page.html', preview: { kind: 'page', src: '/page.html', el: '#target' } }));
    await page.waitForSelector('.chat-slash-detail-frame.is-zoomable', { timeout: 8000 });
    await page.click('.chat-slash-detail-frame.is-zoomable');
    await ready();
    assert.equal((await st()).kind, 'page', 'page preview opens the page lightbox');
    await page.keyboard.press('Escape');
    await page.evaluate(i => mountPreview({ kind: 'library', ns: 'library', slug: 'i', name: 'still', preview: { kind: 'image', src: i } }), img);
    await page.waitForSelector('.chat-slash-detail-frame[data-kind="image"].is-zoomable', { timeout: 8000 });
    await page.click('.chat-slash-detail-frame.is-zoomable');
    await ready();
    assert.equal((await st()).kind, 'image', 'image preview opens the image lightbox');
    await page.keyboard.press('Escape');

    // ── useHoverHold ──
    await page.evaluate(() => { hoverApi.drop(); hoverApi.drop(); });
    await page.waitForTimeout(60);
    await page.evaluate(() => hoverApi.hold());
    await page.waitForTimeout(200);
    assert.ok(await page.$('#probe'), 'hold cancels a pending close');
    await page.evaluate(() => hoverApi.drop());
    await page.waitForTimeout(250);
    assert.equal(await page.$('#probe'), null, 'drop closes after the delay');
    assert.deepEqual(await page.evaluate(() => hoverLog), ['closed'], 'closes once');

    assert.deepEqual(errors, []);
    console.log('PASS: image lightbox - fit, zoom at pointer, pan, keys, bar, close; page framed on its element; previews open it; hover hold.');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
