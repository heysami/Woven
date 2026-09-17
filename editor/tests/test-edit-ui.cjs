/* Mount the actual preview and workflow inspector against an isolated fixture. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('../tools/node_modules/playwright');
const root = path.join(__dirname, '..');
let saveCount = 0;
let componentsUnavailable = false;
let source = '<!doctype html><html><head><style>:root{--accent:#126b68;--space:12px;--radius:6px}body{font:16px Arial;padding:32px}main{display:flex;gap:16px}button{padding:12px;border-radius:var(--radius)}</style></head><body><main><button id="sample"><span>Continue</span></button><button>Cancel</button></main><script>setInterval(()=>{document.querySelector("#sample span").textContent="Continue"},20)</script></body></html>';
const nestedPath = 'source/demo/component.html';
let nestedSource = '<!doctype html><html><head></head><body><h2>Nested original</h2><script>setInterval(()=>{document.querySelector("h2").textContent="Nested original"},20)</script></body></html>';
source = source.replace('</main>', '</main><iframe data-zoom-import="' + nestedPath + '" src="/' + nestedPath + '" style="height:150px;width:500px"></iframe>');
const hash = (value=source) => crypto.createHash('sha256').update(value).digest('hex').slice(0,16);
const library = {definitions:[],version:'initial'};
const server = http.createServer(async (req,res)=>{
  const u = new URL(req.url,'http://fixture');
  if (u.pathname.startsWith('/__')) {
    res.setHeader('content-type','application/json');
    if (u.pathname === '/__edit_source') {const value=u.searchParams.get('path')===nestedPath?nestedSource:source;return res.end(JSON.stringify({html:value,version:hash(value)}));}
    if (u.pathname === '/__edit_components') { if (componentsUnavailable) {res.setHeader('content-type','text/html'); res.statusCode=404; return res.end('<!DOCTYPE html><html>Not found</html>');} return res.end(JSON.stringify(library)); }
    if (u.pathname === '/__html_save') {
      let data=''; for await (const b of req) data+=b; const body=JSON.parse(data);
      if (body.expectedVersion!==hash(body.path===nestedPath?nestedSource:source)) {res.statusCode=409;return res.end(JSON.stringify({error:'Source changed'}));}
      if(body.path===nestedPath)nestedSource=body.html;else source=body.html;saveCount++;return res.end(JSON.stringify({ok:true,version:hash()}));
    }
    return res.end('{}');
  }
  if (u.pathname === '/'+nestedPath) {res.setHeader('content-type','text/html');return res.end(nestedSource.replace('<head>','<head><meta name="woven-source-revision" content="'+hash(nestedSource)+'">'));}
  if (u.pathname === '/source/demo/index.html') {res.setHeader('content-type','text/html');return res.end(source.replace('<head>','<head><meta name="woven-source-revision" content="'+hash()+'">'));}
  res.setHeader('content-type','text/html');res.end('<!doctype html><html><head></head><body><div id="root"></div></body></html>');
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];
    page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
    await page.goto('http://127.0.0.1:'+server.address().port+'/?project=fixture');
    for (const url of ['https://unpkg.com/react@18.3.1/umd/react.development.js','https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js','https://unpkg.com/htm@3.1.1/dist/htm.umd.js']) await page.addScriptTag({url});
    await page.addStyleTag({content:fs.readFileSync(path.join(root,'styles.css'),'utf8')});
    for (const name of ['edit-engine.js','edit-components.js','edit-controls.js','context-policy.js']) await page.addScriptTag({path:path.join(root,name)});
    await page.evaluate(()=>{ window.EDITOR_DATA={meta:{project:'Fixture',prototype:'demo',dsRef:{id:'fixture',version:'1'}},frames:[],entities:[],tokens:[],library:[],primitives:[{name:'Button',variants:['primary'],htmlByVariant:{primary:'<button class="button"><span>Button</span></button>'}}]}; });
    let app=fs.readFileSync(path.join(root,'app.js'),'utf8');
    app=app.replace('createRoot(document.getElementById("root")).render(html`<${React.Fragment}><${Root}/><${DialogHost}/><//>`);', 'window.fixtureRoot = createRoot(document.getElementById("root")); window.fixtureRoot.render(html`<${React.Fragment}><${ZoomOverlay} filePath="source/demo/index.html" branch="demo" data=${{nodes:[],edges:[]}} setData=${()=>{}} onClose=${()=>{}}/><${DialogHost}/><//>`);');
    app += `
      function WorkflowFixture() {
        const frame = useRef(null), selected = useRef(null);
        const [picked,setPicked] = useState(null);
        useEffect(()=>{
          const listener=e=>setPicked(e.detail);
          window.addEventListener('th:element-picked',listener);
          return ()=>window.removeEventListener('th:element-picked',listener);
        },[]);
        const load=()=>{
          if(WovenEdit.isolate(frame.current,'source/demo/index.html',apiUrl))return;
          const doc=frame.current.contentDocument;
          WovenEdit.bind(doc,'source/demo/index.html',apiUrl);
          selected.current=doc.querySelector('button');
          setPicked({nodeId:'fixture',path:elementCssPath(selected.current),tagName:'button'});
        };
        return html\`<div><div className="workflow-node" data-node-id="fixture" style=\${{position:'absolute',left:'260px',top:'32px',width:'600px',height:'1000px'}}>
          <iframe id="wf-fixture" ref=\${frame} src="/source/demo/index.html" onLoad=\${load} style=\${{width:'580px',height:'900px'}}/>
          </div>\${picked && html\`<\${WorkflowPickedInspectorDock} node=\${{id:'fixture',x:260,y:32,w:600,h:1000}} zoom=\${1}
          pickerIframeRef=\${frame} pickedDomRef=\${selected} pickedElement=\${picked}
          onStageInspectorEdit=\${(ifr,doc,op)=>WovenEdit.stage(doc,op)}/>\`}</div>\`;
      }
    `;
    await page.addScriptTag({content:app});
    await page.waitForFunction(()=>document.querySelector('.zoom-overlay iframe')?.contentDocument?.querySelector('meta[name="woven-authoring"]'));
    const frame=page.frameLocator('.zoom-overlay iframe').first();
    await frame.locator('#sample').click();
    assert.equal(await page.locator('.woven-edit-variables').count(),0,'Variables are disclosed on demand');
    assert.equal(await page.getByRole('tree',{name:'Page layers'}).count(),1);
    await page.getByRole('treeitem',{name:'sample',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('[role="treeitem"][aria-label="sample"]')?.getAttribute('aria-selected')==='true');
    assert.equal(await page.getByLabel('Width resizing').count(),1);
    assert.equal(await page.getByLabel('Min width',{exact:true}).isVisible(),false,'Size limits start collapsed');
    assert.equal(await page.locator('.woven-inspector').evaluate(n=>getComputedStyle(n).fontSize),'11px');
    await page.screenshot({path:path.join(require('node:os').tmpdir(),'woven-inspector-preview.png'),fullPage:true});
    componentsUnavailable=true;
    await page.getByRole('button',{name:'Add',exact:true}).click();
    await page.getByRole('button',{name:'Retry component library'}).waitFor();
    assert.ok((await page.locator('.woven-edit-error').innerText()).includes('Restart Woven'));
    assert.ok(!(await page.locator('.woven-inspector').innerText()).includes('Unexpected token'));
    componentsUnavailable=false;
    await page.getByRole('button',{name:'Retry component library'}).click();
    await page.waitForFunction(()=>!document.querySelector('.woven-edit-error'));
    await page.getByLabel('Search components').fill('Button');
    await page.locator('.woven-edit-component-list button').first().click();
    assert.equal(await frame.locator('[data-woven-component]').count(),1);
    await page.getByRole('button',{name:'Copy',exact:true}).click();
    for(let i=0;i<3;i++) await page.getByRole('button',{name:'Paste',exact:true}).click();
    assert.equal(await frame.locator('[data-woven-component]').count(),4);
    await page.getByRole('button',{name:'Variables',exact:true}).click();
    await page.getByLabel('Variable property').selectOption('padding');
    await page.getByLabel('Bind variable',{exact:true}).selectOption('--space');
    assert.equal(await frame.locator('[data-woven-component]').last().evaluate(n=>n.style.padding),'var(--space)');
    await page.getByRole('button',{name:'Save',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.zoom-tool-save').dataset.dirty==='false');
    assert.equal(saveCount,1);
    assert.ok(source.includes('setInterval'), 'UI save preserves application source');
    assert.ok(!source.includes('woven-authoring'), 'UI save does not ship authoring isolation');
    await page.getByRole('button',{name:'Undo',exact:true}).click();
    assert.equal(await frame.locator('[data-woven-component]').last().evaluate(n=>n.style.padding),'');
    await page.getByRole('button',{name:'Save',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.zoom-tool-save').dataset.dirty==='false');
    assert.equal(saveCount,2);
    const parentSource = source;
    const nested=frame.frameLocator('iframe[data-zoom-import]');
    await nested.locator('h2').dblclick({position:{x:20,y:10}});
    await nested.locator('h2[contenteditable]').fill('Nested updated');
    await nested.locator('h2').press('Enter');
    await page.getByRole('button',{name:'Save',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.zoom-tool-save').dataset.dirty==='false');
    assert.ok(nestedSource.includes('Nested updated'));
    assert.ok(nestedSource.includes('setInterval'));
    assert.ok(!nestedSource.includes('woven-authoring'));
    assert.equal(source,parentSource,'An imported edit must save only the imported source');
    // Mount the production workflow inspector against the same pending session.
    await page.evaluate(()=>{
      window.fixtureRoot.render(html`<${React.Fragment}><${WorkflowFixture}/><${DialogHost}/><//>`);
    });
    await page.waitForFunction(()=>document.querySelector('#wf-fixture')?.contentDocument?.querySelector('meta[name="woven-authoring"]'));
    await page.getByRole('button',{name:'Add',exact:true}).click();
    await page.getByRole('button',{name:'Text',exact:true}).click();
    const workflowFrame=page.frameLocator('#wf-fixture');
    assert.equal(await workflowFrame.locator('p').count(),1);
    await page.getByRole('button',{name:'Copy',exact:true}).click();
    for(let i=0;i<3;i++) await page.getByRole('button',{name:'Paste',exact:true}).click();
    assert.equal(await workflowFrame.locator('p').count(),4);
    await page.getByRole('button',{name:'Variables',exact:true}).click();
    await page.getByLabel('Variable property').selectOption('padding');
    await page.getByLabel('Bind variable',{exact:true}).selectOption('--space');
    assert.equal(await workflowFrame.locator('p').last().evaluate(n=>n.style.padding),'var(--space)');
    await page.getByRole('button',{name:'Close variables'}).click();
    await page.getByRole('button',{name:'Close insert'}).click();
    await page.getByRole('treeitem',{name:'Main',exact:true}).click();
    await page.getByRole('button',{name:'Grid layout',exact:true}).click();
    await page.locator('.woven-inspector-more > summary').click();
    await page.getByLabel('Columns',{exact:true}).fill('repeat(2, minmax(0, 1fr))');
    await page.getByLabel('Columns',{exact:true}).press('Enter');
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.gridTemplateColumns),'repeat(2, minmax(0px, 1fr))');
    await page.locator('.woven-inspector-more > summary').click();
    await page.getByRole('button',{name:'Horizontal layout',exact:true}).click();
    await page.getByRole('button',{name:'Bottom right',exact:true}).click();
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.justifyContent),'flex-end');
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.alignItems),'flex-end');
    await page.getByLabel('Gap',{exact:true}).fill('20');
    await page.getByLabel('Gap',{exact:true}).press('Enter');
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.gap),'20px');
    await page.getByRole('button',{name:'Bind variable to Gap',exact:true}).click();
    await page.getByRole('dialog',{name:'Gap variables'}).getByRole('button',{name:'--space 12px',exact:true}).click();
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.gap),'var(--space)');
    await page.getByLabel('Width resizing').selectOption('fixed');
    await page.getByLabel('Width',{exact:true}).fill('440');
    await page.getByLabel('Width',{exact:true}).press('Enter');
    assert.equal(await workflowFrame.locator('main').evaluate(n=>n.style.width),'440px');
    await page.screenshot({path:path.join(require('node:os').tmpdir(),'woven-inspector-layout.png'),fullPage:true});
    await page.getByRole('treeitem',{name:'Main',exact:true}).press('ArrowRight');
    await page.keyboard.press('Enter');
    assert.equal(await page.getByRole('treeitem',{name:'sample',exact:true}).getAttribute('aria-selected'),'true');
    await page.screenshot({path:path.join(require('node:os').tmpdir(),'woven-edit-ui.png'),fullPage:true});
    assert.ok(await page.locator('.woven-inspector').evaluate(n=>n.scrollWidth <= n.clientWidth),'Properties must not overflow horizontally');
    assert.deepEqual(errors,[]);
    console.log('PASS: actual preview and workflow inspectors, DS Add, repeated clipboard paste, variable controls, source-preserving UI Save, Undo after Save, and independent imported-content saves. Screenshot: '+path.join(require('node:os').tmpdir(),'woven-edit-ui.png'));
  } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
