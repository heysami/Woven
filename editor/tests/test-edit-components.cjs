/* Component updates must preserve per-instance overrides and valid HTML IDs. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('../tools/node_modules/playwright');

(async()=>{
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage();const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.setContent('<!doctype html><html><body></body></html>');
    for(const name of ['edit-engine.js','edit-components.js'])await page.addScriptTag({path:path.join(__dirname,'..',name)});
    const result=await page.evaluate(()=>{
      const C=WovenComponents;
      const def=C.definition('local:field','Field','<div style="padding:4px"><label for="field">Name</label><input id="field" placeholder="Name"></div>');
      const first=C.instance(def),second=C.instance(def);document.body.append(first,second);
      first.querySelector('input').placeholder='Your name';
      C.capture(first.querySelector('input'),'text','Your name','placeholder');
      C.capture(second.querySelector('label'),'text','Team name','text');
      second.querySelector('label').textContent='Team name';
      const newer={...def,html:def.html.replace('4px','16px')};
      const script=document.createElement('script');script.type='application/json';script.setAttribute('data-woven-library','');script.textContent=JSON.stringify({definitions:[newer]});document.head.append(script);
      C.runtime(document);
      const instances=[...document.querySelectorAll('[data-woven-component]')];
      const rows=instances.map(n=>({padding:n.style.padding,label:n.querySelector('label').textContent,placeholder:n.querySelector('input').placeholder,id:n.querySelector('input').id,for:n.querySelector('label').htmlFor}));
      const reset=C.refresh(instances[0],newer,true);
      const detached=C.detach(instances[1]);
      const gallery=new DOMParser().parseFromString('<section id="buttons"><h2>Buttons</h2><div class="ds-sample" data-variant="primary"><button>Go</button></div></section>','text/html');
      return {rows,reset:reset.querySelector('input').placeholder,detached:detached.hasAttribute('data-woven-component'),catalog:C.catalogFromGallery(gallery,'example').map(d=>({id:d.id,name:d.name,html:d.html}))};
    });
    assert.equal(result.rows[0].placeholder,'Your name');assert.equal(result.rows[1].label,'Team name');
    assert.ok(result.rows.every(n=>n.padding==='16px'&&n.id===n.for));
    assert.notEqual(result.rows[0].id,result.rows[1].id);
    assert.equal(result.reset,'Name');assert.equal(result.detached,false);
    assert.equal(result.catalog[0].id,'example:buttons.primary');
    assert.ok(result.catalog[0].html.includes('data-woven-part'));
    assert.deepEqual(errors,[]);
    console.log('PASS: standalone main updates, independent text and input overrides, remapped label IDs, reset, detach, and canonical gallery extraction.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
