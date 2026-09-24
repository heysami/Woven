/* Actual workflow surface + frames node + nested Frame, without a daemon. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('../tools/node_modules/playwright');
const root = path.join(__dirname, '..');
const revision = html => crypto.createHash('sha256').update(html).digest('hex').slice(0,16);
const from = 'source/demo/index.html';
const original = '<!doctype html><html><head><style>body{font:16px Arial;margin:24px}main{display:flex;gap:12px}button{padding:8px}h1{font-size:24px}</style></head><body><h1 id="title">Original title</h1><main><button id="first">First</button><button>Second</button><button>Third</button></main><script>setInterval(()=>{document.querySelector("h1").textContent="Original title"},30)</script></body></html>';
const files = new Map([[from,original]]);
let failDraftSave = false, failApply = false;
const writes = [];
const data = { meta: { project: 'Draft fixture', prototype: 'demo', sourceRoot: '../source/demo/', sourceEntry: 'index.html', defaultFrame: {w:500,h:300}, gridGap: 32 }, frames: [{id:'screen',label:'Screen',kind:'page',entry:'index.html',x:0,y:0,w:500,h:300}], arrows:[],entities:[],tokens:[],primitives:[],library:[] };
const bootstrap = `
function DraftEmbed() {
  const [drafts,setDrafts] = useState({});
  useEffect(()=>{window.__wovenSetDraftFrames=setDrafts; window.__wovenSetFrameVisibility=()=>{};return()=>delete window.__wovenSetDraftFrames;},[]);
  return html\`<\${Frame} frame=\${D.frames[0]} selected=\${true} onSelect=\${()=>{}} edits=\${[]} strokes=\${[]} gridMeta=\${D.meta} draft=\${drafts.screen || null}/>\`;
}
function DraftFixture() {
  const [data,setData]=useState({pan:{x:270,y:100},zoom:1,nodes:[{id:'frames-one',kind:'frames',prototype:'demo',x:0,y:0,w:560,h:460}],edges:[],wb:[]});
  const selected=useRef(null), deleted=useRef(new Set()), deletedWb=useRef(new Set());
  window.draftFixtureData=data;
  return html\`<\${WorkflowSurface} data=\${data} setData=\${setData} selectionRef=\${selected} deletedIdsRef=\${deleted} deletedWbIdsRef=\${deletedWb} history=\${[]} openKinds=\${[]} />\`;
}
createRoot(document.getElementById('root')).render(html\`<\${React.Fragment}><\${new URLSearchParams(location.search).has('embed') ? DraftEmbed : DraftFixture}/><\${DialogHost}/><//>\`);
`;
const app = fs.readFileSync(path.join(root,'app.js'),'utf8').replace('createRoot(document.getElementById("root")).render(html`<${React.Fragment}><${Root}/><${DialogHost}/><//>`);',bootstrap);
const server = http.createServer(async(req,res)=>{
  const url = new URL(req.url,'http://fixture');
  res.setHeader('cache-control','no-store');
  if (url.pathname.startsWith('/__')) {
    res.setHeader('content-type','application/json');
    let raw=''; for await (const b of req) raw+=b;
    const body=raw?JSON.parse(raw):{};
    if (url.pathname==='/__edit_source') {
      const html=files.get(url.searchParams.get('path'));
      if(html==null){res.statusCode=404;return res.end(JSON.stringify({error:'Missing fixture source'}));}
      return res.end(JSON.stringify({html,version:revision(html)}));
    }
    if (url.pathname==='/__component_export') {files.set(body.path,body.html);return res.end('{"ok":true}');}
    if (url.pathname==='/__html_save') {
      if ((failDraftSave && body.path!==from) || (failApply && body.path===from)) {res.statusCode=409;return res.end('{"error":"Fixture revision conflict"}');}
      if(body.expectedVersion && body.expectedVersion!==revision(files.get(body.path))){res.statusCode=409;return res.end('{"error":"Source changed"}');}
      files.set(body.path,body.html);writes.push(body);return res.end(JSON.stringify({ok:true,version:revision(body.html)}));
    }
    if(url.pathname==='/__edit_components')return res.end('{"definitions":[],"version":"v1"}');
    if(url.pathname==='/__projects')return res.end('{"projects":[]}');
    return res.end('{}');
  }
  const file=url.pathname.slice(1);
  if(files.has(file)){const html=files.get(file);res.setHeader('content-type','text/html');return res.end(html.replace('<head>','<head><meta name="woven-source-revision" content="'+revision(html)+'">'));}
  if(url.pathname==='/editor/app.js'){res.setHeader('content-type','text/javascript');return res.end(app);}
  if(['/editor/styles.css','/editor/edit-engine.js','/editor/edit-components.js','/editor/edit-controls.js','/editor/context-policy.js'].includes(url.pathname)) {
    res.setHeader('content-type',url.pathname.endsWith('.css')?'text/css':'text/javascript');return res.end(fs.readFileSync(path.join(root,path.basename(url.pathname))));
  }
  res.setHeader('content-type','text/html');
  res.end('<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/editor/styles.css"></head><body><div id="root"></div><script>localStorage.setItem("th-workflow-wb-mode","0");window.EDITOR_DATA='+JSON.stringify(data)+';</script>'+['https://unpkg.com/react@18.3.1/umd/react.development.js','https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js','https://unpkg.com/htm@3.1.1/dist/htm.umd.js','/editor/context-policy.js','/editor/edit-engine.js','/editor/edit-components.js','/editor/edit-controls.js','/editor/app.js'].map(src=>'<script src="'+src+'"></script>').join('')+'</body></html>');
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1550,height:1100}});
  const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
  try {
    await page.goto('http://127.0.0.1:'+server.address().port+'/editor/index.html?project=fixture&prototype=demo');
    await page.locator('.workflow-node-frames-bodydrag').click({position:{x:20,y:20}});
    await page.getByRole('button',{name:'Draft',exact:true}).click();
    const embedded=page.frameLocator('iframe.workflow-node-iframe');
    const draft=embedded.frameLocator('iframe[data-draft-id]');
    await draft.locator('meta[name="woven-authoring"]').waitFor({state:'attached'});
    await draft.locator('#first').click();
    await page.getByRole('tree',{name:'Page layers'}).waitFor();
    await page.getByLabel('Width resizing').waitFor();
    await page.waitForTimeout(1400);
    assert.equal(await draft.locator('meta[name="woven-authoring"]').count(),1,'Navigation pin must retain the authoring document');
    assert.equal(files.get(from),original);
    const draftPath=await page.evaluate(()=>draftFixtureData.nodes[0].drafts.screen.path);
    assert.equal(files.get(draftPath),original,'Draft clones raw source, without server instrumentation');
    await draft.locator('#first').press('ArrowRight');
    assert.deepEqual(await draft.locator('main > button').allTextContents(),['Second','First','Third'],'One arrow press moves one position');
    await draft.locator('#first').press('ArrowLeft');
    assert.equal(await draft.locator('main > button').first().getAttribute('id'),'first');
    await draft.locator('#title').dblclick({position:{x:20,y:10}});
    await draft.locator('#title[contenteditable]').fill('Draft title');
    await draft.locator('#title').press('Enter');
    await page.waitForTimeout(700);
    assert.equal(await draft.locator('#title').textContent(),'Draft title','Application scripts cannot revert edited text');
    const before=await draft.locator('#title').evaluate(n=>n.getBoundingClientRect().x);
    await draft.locator('#title').press('ArrowRight');
    assert.equal(await draft.locator('#title').evaluate(n=>n.getBoundingClientRect().x),before+1,'Keyboard forwarding must not double the nudge');
    await draft.locator('#title').press('Control+c');
    for(let i=0;i<3;i++) {
      await draft.locator('h1').last().press('Control+v');
      await draft.locator('h1').nth(i+1).waitFor();
    }
    assert.equal(await draft.locator('h1').count(),4);
    await draft.locator('h1').last().dblclick({position:{x:20,y:10}});
    await draft.locator('h1[contenteditable]').fill('Pasted title');
    await draft.locator('h1').last().press('Enter');
    assert.equal(await draft.locator('h1').last().textContent(),'Pasted title');
    await page.getByRole('button',{name:'Add',exact:true}).click();
    await page.getByRole('button',{name:'Text',exact:true}).click();
    assert.equal(await draft.locator('p').count(),1);
    await page.getByRole('button',{name:'Close insert'}).click();
    failDraftSave=true;
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('[role="alert"]')?.textContent.includes('Fixture revision conflict'));
    assert.equal(files.get(from),original,'Failed draft Save must prevent Apply');
    assert.equal(await draft.locator('h1').count(),4);
    failDraftSave=false;
    failApply=true;
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.getByRole('alertdialog').waitFor();
    assert.match(await page.getByRole('alertdialog').innerText(),/Fixture revision conflict/);
    assert.equal(files.get(from),original,'A source conflict leaves the real page untouched');
    assert.equal(await draft.locator('h1').count(),4);
    await page.getByRole('button',{name:'OK',exact:true}).click();
    failApply=false;
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.waitForFunction(()=>!draftFixtureData.nodes[0].drafts.screen);
    assert.ok(files.get(from).includes('Pasted title'));
    assert.ok(files.get(from).includes('setInterval'));
    assert.ok(!files.get(from).includes('woven-source-revision'));
    assert.ok(!files.get(from).includes('woven-authoring'));
    assert.equal(writes.filter(w=>w.path===from).length,1);
    await embedded.locator('iframe:not([data-draft-id])').waitFor();
    assert.equal(await embedded.locator('iframe[srcdoc]').count(),0,'Apply remounts the real page, without old srcdoc');
    await page.getByRole('button',{name:'Draft',exact:true}).click();
    await draft.locator('meta[name="woven-authoring"]').waitFor({state:'attached'});
    await draft.locator('#title').dblclick({position:{x:20,y:10}});
    await draft.locator('#title[contenteditable]').fill('Throw this away');
    await draft.locator('#title').press('Enter');
    await page.getByRole('button',{name:'Discard',exact:true}).click();
    await page.getByRole('button',{name:'Confirm',exact:true}).click();
    await page.waitForFunction(()=>!draftFixtureData.nodes[0].drafts.screen);
    await page.getByRole('button',{name:'Draft',exact:true}).click();
    await draft.locator('meta[name="woven-authoring"]').waitFor({state:'attached'});
    assert.equal(await draft.locator('#title').textContent(),'Draft title','Discarded edits must not recover into a new draft');
    await page.screenshot({path:path.join(require('node:os').tmpdir(),'woven-frame-draft-fixed.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('PASS: nested Draft editing, stable text, arrows, repeated paste, editable pasted text, Add, guarded Apply, raw source preservation, and clean re-draft after Discard.');
  } catch(error) {
    await page.screenshot({path:path.join(require('node:os').tmpdir(),'woven-frame-draft-failure.png'),fullPage:true});
    throw error;
  } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
