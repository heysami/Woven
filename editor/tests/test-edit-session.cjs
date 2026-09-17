/* Source preservation and cross-host editing in real, same-origin iframes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { chromium } = require('../tools/node_modules/playwright');
const root = path.join(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const patch = app.slice(app.indexOf('function _extractPatchOps('), app.indexOf('function pickSerializeClean('));
const selectors = app.slice(app.indexOf('function elementCssPath('), app.indexOf('/* WorkflowAssetActionBar:'));
const commands = app.slice(app.indexOf('function performSelectionCommand('), app.indexOf('function PickedInspectorBody('));
const slotStart = app.indexOf('function thTextSlot(');
const slotEnd = app.indexOf('\nfunction ', slotStart + 10);
const slots = app.slice(slotStart, slotEnd);
let source = '<!doctype html><html><head><style>:root{--accent:#125555}</style></head><body><button id="button">Original</button><script>setInterval(()=>{document.querySelector("#button").textContent="Original"},10)</script></body></html>';
const original = source;
const version = () => crypto.createHash('sha256').update(source).digest('hex').slice(0,16);
const library = { definitions: [], version: 'initial' };
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/__edit_source') { res.setHeader('content-type','application/json'); return res.end(JSON.stringify({html:source,version:version()})); }
  if (url.pathname === '/__edit_components') {
    if (req.method === 'POST') { let raw=''; for await (const chunk of req) raw+=chunk; const body=JSON.parse(raw); library.definitions=[...library.definitions.filter(d=>d.id!==body.definition.id),body.definition]; }
    res.setHeader('content-type','application/json'); return res.end(JSON.stringify(library));
  }
  if (url.pathname === '/__html_save') {
    let raw=''; for await (const chunk of req) raw+=chunk; const body=JSON.parse(raw);
    res.setHeader('content-type','application/json');
    if (body.expectedVersion !== version()) { res.statusCode=409; return res.end(JSON.stringify({error:'Revision conflict'})); }
    source=body.html; return res.end(JSON.stringify({ok:true,version:version()}));
  }
  res.setHeader('content-type','text/html');
  if (url.pathname.startsWith('/source/')) return res.end(source.replace('<head>','<head><meta name="woven-source-revision" content="'+version()+'">'));
  res.end('<!doctype html><div id="controls"></div><iframe id="workflow" src="/source/demo/index.html"></iframe>');
});

(async () => {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch({headless:true});
  try {
    const context = await browser.newContext();
    const page = await context.newPage(); const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:'+server.address().port);
    for (const file of ['edit-engine.js','edit-components.js']) await page.addScriptTag({path:path.join(root,file)});
    await page.addScriptTag({content:'const apiUrl = p => p + "?project=fixture";\n'+patch+selectors+slots+commands});
    await page.route('**/__edit_source?*', route => route.fulfill({status:404,contentType:'text/html',body:'<!DOCTYPE html><html>Older daemon</html>'}));
    await page.evaluate(() => WovenEdit.isolate(document.querySelector('iframe'),'source/demo/index.html',apiUrl));
    await page.waitForFunction(()=>document.querySelector('iframe').contentDocument?.querySelector('meta[name="woven-authoring"]'));
    await page.evaluate(async () => {
      const doc=document.querySelector('iframe').contentDocument;
      const state = WovenEdit.bind(doc,'source/demo/index.html',apiUrl);
      await state.ready.catch(() => {});
      if (!state.error.includes('Restart Woven') || state.error.includes('Unexpected token')) throw new Error('Missing service error must be actionable');
      const r=performSelectionCommand(doc.querySelector('button'),'text',{text:'Edited'}); WovenEdit.stage(doc,r.op);
    });
    await page.unroute('**/__edit_source?*');
    await page.evaluate(async () => {
      const doc=document.querySelector('iframe').contentDocument;
      await WovenEdit.retry(doc);
      if (WovenEdit.state(doc).error || !WovenEdit.state(doc).dirty) throw new Error('Retry must preserve pending edits');
    });
    await page.waitForTimeout(100);
    assert.equal(await page.frameLocator('#workflow').locator('button').textContent(),'Edited');
    await page.evaluate(async () => {
      const frame=document.createElement('iframe'); frame.id='preview'; frame.src='/source/demo/index.html';
      const loaded=new Promise(r=>frame.onload=r); document.body.append(frame); await loaded;
      WovenEdit.isolate(frame,'source/demo/index.html',apiUrl);
    });
    await page.waitForFunction(()=>document.querySelector('#preview').contentDocument?.querySelector('meta[name="woven-authoring"]'));
    await page.evaluate(()=>WovenEdit.bind(document.querySelector('#preview').contentDocument,'source/demo/index.html',apiUrl));
    assert.equal(await page.frameLocator('#preview').locator('button').textContent(),'Edited');
    await page.evaluate(()=>WovenEdit.history(document.querySelector('#preview').contentDocument,-1));
    assert.equal(await page.frameLocator('#workflow').locator('button').textContent(),'Original');
    await page.evaluate(()=>WovenEdit.history(document.querySelector('#workflow').contentDocument,1));
    assert.equal(await page.frameLocator('#preview').locator('button').textContent(),'Edited');
    await page.evaluate(async()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      await WovenEdit.save(doc,'source/demo/index.html',apiUrl,[],_injectInspectorPatch,'',true);
    });
    assert.ok(source.includes('setInterval'), 'Authored application script must survive');
    assert.ok(source.includes('<button id="button">Original</button>'), 'Runtime DOM must not replace authored source');
    assert.ok(!source.includes('woven-authoring'), 'Editor isolation must not ship in source');
    assert.ok(source.includes('Edited'));
    await page.evaluate(async()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      WovenEdit.history(doc,-1);
      await WovenEdit.save(doc,'source/demo/index.html',apiUrl,[],_injectInspectorPatch,'',true);
    });
    assert.equal(source, original, 'Undo then save restores the source baseline, including after a previous save');

    // Components keep independent overrides while shared structure/style updates.
    await page.evaluate(()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      const def=WovenComponents.definition('local:button','Button','<button style="border-radius:4px"><span>Default</span></button>');
      const result=performSelectionCommand(doc.querySelector('button'),'insert-component',{definition:def});
      WovenEdit.stage(doc,result.op);
      const span=result.element.querySelector('span');
      const edit=performSelectionCommand(span,'text',{text:'Continue'}); WovenEdit.stage(doc,edit.op);
      const copy=performSelectionCommand(result.element,'duplicate'); WovenEdit.stage(doc,copy.op);
      const newer={...def,html:def.html.replace('4px','12px')};
      const updated=performSelectionCommand(result.element,'publish-component',newer); WovenEdit.stage(doc,updated.op);
    });
    const components = await page.frameLocator('#workflow').locator('[data-woven-component]').evaluateAll(nodes=>nodes.map(n=>({text:n.textContent,radius:n.style.borderRadius,instance:n.getAttribute('data-woven-instance')})));
    assert.equal(components.length,2); assert.ok(components.every(n=>n.text==='Continue'&&n.radius==='12px'));
    assert.notEqual(components[0].instance,components[1].instance);

    await page.evaluate(async()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      const result=performSelectionCommand(doc.querySelector('button'),'mode',{mode:{attribute:'data-theme',value:'dark'},attributes:['data-theme']});
      WovenEdit.stage(doc,result.op);
      if(doc.documentElement.getAttribute('data-theme')!=='dark')throw new Error('Mode was not applied');
      WovenEdit.history(doc,-1);
      if(doc.documentElement.hasAttribute('data-theme'))throw new Error('Undo did not restore root attributes');
      await WovenEdit.save(doc,'source/demo/index.html',apiUrl,[],_injectInspectorPatch,'',true);
    });

    // Hold the network response so another edit definitely arrives mid-save.
    let releaseSave, saveStarted;
    const gate = new Promise(resolve=>{releaseSave=resolve;});
    const started = new Promise(resolve=>{saveStarted=resolve;});
    await page.route('**/__html_save?*', async route=>{saveStarted();await gate;await route.continue();});
    await page.evaluate(()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      const result=performSelectionCommand(doc.querySelector('#button'),'text',{text:'First save'});WovenEdit.stage(doc,result.op);
      window.savePromise=WovenEdit.save(doc,'source/demo/index.html',apiUrl,[],_injectInspectorPatch,'',true);
    });
    await started;
    await page.evaluate(()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      const result=performSelectionCommand(doc.querySelector('#button'),'text',{text:'Newer edit'});WovenEdit.stage(doc,result.op);
    });
    releaseSave();
    assert.equal(await page.evaluate(async()=>{await window.savePromise;return WovenEdit.state(document.querySelector('#workflow').contentDocument).dirty;}),true);
    await page.unroute('**/__html_save?*');
    assert.ok(source.includes('First save')); assert.ok(!source.includes('Newer edit'));

    source += '<!-- external source change -->';
    const conflict = await page.evaluate(async()=>{
      const doc=document.querySelector('#workflow').contentDocument;
      try {await WovenEdit.save(doc,'source/demo/index.html',apiUrl,[],_injectInspectorPatch,'',true);return false;}
      catch {return WovenEdit.state(doc).dirty && doc.querySelector('#button').textContent==='Newer edit';}
    });
    assert.equal(conflict,true);assert.ok(source.includes('external source change'));

    // A fresh editor document recovers the pending snapshot, with the old
    // source revision retained so recovery cannot overwrite the external edit.
    const recovery = await page.context().newPage();
    await recovery.goto('http://127.0.0.1:'+server.address().port);
    await recovery.addScriptTag({path:path.join(root,'edit-engine.js')});
    await recovery.evaluate(()=>WovenEdit.isolate(document.querySelector('iframe'),'source/demo/index.html',p=>p+'?project=fixture'));
    await recovery.waitForFunction(()=>document.querySelector('iframe').contentDocument?.querySelector('meta[name="woven-authoring"]'));
    const recovered = await recovery.evaluate(async()=>{
      const doc=document.querySelector('iframe').contentDocument;
      const state=WovenEdit.bind(doc,'source/demo/index.html',p=>p+'?project=fixture');await state.ready;
      return {dirty:state.dirty,recovered:state.recovered,text:doc.querySelector('#button').textContent,error:state.error};
    });
    assert.equal(recovered.dirty,true);assert.equal(recovered.recovered,true);assert.equal(recovered.text,'Newer edit');assert.ok(recovered.error.includes('source changed'));
    await recovery.close();
    assert.deepEqual(errors,[]);
    console.log('PASS: isolated authoring, cross-view undo, original-source saves, linked instances and overrides, mode undo, edits during save, revision conflicts, and browser draft recovery.');
  } finally { await browser.close(); server.close(); }
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
