// Run with node editor/tools/_shared/canvas-audit.browser.cjs.
// Serves only this checkout and synthetic fixtures; never calls a live daemon.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('../node_modules/playwright');
const root=path.resolve(__dirname,'../../..');
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2'};
function wave(){const rate=8000,n=rate,buf=Buffer.alloc(44+n*2);buf.write('RIFF');buf.writeUInt32LE(buf.length-8,4);buf.write('WAVEfmt ',8);buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);buf.writeUInt16LE(1,22);buf.writeUInt32LE(rate,24);buf.writeUInt32LE(rate*2,28);buf.writeUInt16LE(2,32);buf.writeUInt16LE(16,34);buf.write('data',36);buf.writeUInt32LE(n*2,40);for(let i=0;i<n;i++)buf.writeInt16LE(Math.round(16000*Math.sin(i*2*Math.PI*440/rate)),44+i*2);return buf;}
const hooks=`\nwindow.__audit={bake,LogicBridge,storeWired,videoStreamEl,Positioning,Input,Engine,setState(s){STATE=normalizeState(s);rebuild();},setContent(c){CONTENT=c;}};\n`;
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://local');
 if(req.method!=='GET'){res.writeHead(405);return res.end();}
 if(url.pathname==='/tone.wav'){res.setHeader('content-type','audio/wav');return res.end(wave());}
 if(url.pathname==='/card.html'){res.setHeader('content-type','text/html');return res.end('<!doctype html><html><head><link rel="stylesheet" href="card.css"></head><body><img src="mark.svg"></body></html>');}
 if(url.pathname==='/card.css'){res.setHeader('content-type','text/css');return res.end('html,body{margin:0;width:100%;height:100%;background:rgb(255,0,0)}img{width:32px;height:32px}');}
 if(url.pathname==='/mark.svg'){res.setHeader('content-type','image/svg+xml');return res.end('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="blue"/></svg>');}
 if(url.pathname==='/blank'){res.setHeader('content-type','text/html');return res.end('<!doctype html><body><div id="surface" tabindex="0" style="width:800px;height:400px"></div></body>');}
 const file=path.resolve(root,'.'+url.pathname);if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
 try{let bytes=fs.readFileSync(file);if(url.pathname==='/editor/tools/mmcomposer/index.html'){let text=bytes.toString();const at=text.lastIndexOf('</script>');text=text.slice(0,at)+hooks+text.slice(at);bytes=Buffer.from(text);}res.setHeader('content-type',mime[path.extname(file)]||'application/octet-stream');res.end(bytes);}catch(_){res.writeHead(404);res.end();}
});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,args:['--autoplay-policy=no-user-gesture-required']});
try{
 const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{const u=route.request().url();return u.startsWith(base)||u.startsWith('data:')?route.continue():route.abort();});
 await page.goto(base+'/editor/tools/mmcomposer/index.html');await page.waitForFunction(()=>window.__audit);
 const logic={nodes:[{id:'pointer',kind:'input-pointer',params:{space:'pixels',button:'right'}},{id:'point',kind:'input-pointer',params:{}},{id:'left',kind:'value-vec2',params:{x:0.2,y:0.8}},{id:'right',kind:'value-vec2',params:{x:0.8,y:0.8}}],outputs:[],edges:[]};
 await page.evaluate(async logic=>{const a=window.__audit;a.setState({canvasW:800,canvasH:400,background:'#000000',layers:[]});a.storeWired({logic,layers:[{id:'triangle',spec:{_shape:true,params:{fill:'#ff0000',closed:true,strokeWidth:0},_points:Object.fromEntries(['point','left','right'].map((id,i)=>['p'+i,{kind:'logic',ref:{node:id,port:id==='point'?'pos':'value'}}]))},children:[]}]});a.Engine.logicRun=true;await a.LogicBridge._ensureModules();},logic);
 await page.waitForFunction(()=>window.__audit.LogicBridge._inputHandle);
 const pointer=await page.evaluate(()=>{const a=window.__audit,el=a.LogicBridge._attachedEl,r=el.getBoundingClientRect();el.dispatchEvent(new PointerEvent('pointerdown',{clientX:r.left+r.width/2,clientY:r.top+r.height/4,button:0,buttons:1,pointerType:'mouse'}));const input=a.LogicBridge._inputHandle.sample();return {input,ports:a.LogicBridge.plan&&a.LogicBridge.plan.nodes};});
 assert.equal(pointer.input.pointer.buttons,1);
 const html=await page.evaluate(()=>window.__audit.bake());assert.ok(html.includes('window.__MM_MODULES__'));assert.ok(!html.includes("import('/editor/tools/_shared/"));console.log('PASS real composer bakes embedded runtime dependencies');
 const exportPage=await browser.newPage({viewport:{width:800,height:400}}),requests=[];const exportErrors=[];exportPage.on('pageerror',e=>exportErrors.push(e.message));
 const instrumented=html.replace('  TOPFX=TOPFX||[];', '  TOPFX=TOPFX||[];window.__bakedAudit=()=>({ports:LB.ports,plan:LB.plan,handle:LB.handle});');
 await exportPage.route('**/*',route=>{const u=route.request().url();if(u==='https://empty-export.invalid/')return route.fulfill({status:200,contentType:'text/html',body:instrumented});requests.push(u);return route.abort();});
 await exportPage.goto('https://empty-export.invalid/');await exportPage.waitForFunction(()=>window.__bakedAudit&&window.__bakedAudit().handle);
 await exportPage.mouse.move(400,100);await exportPage.mouse.down({button:'left'});await exportPage.waitForFunction(()=>window.__bakedAudit().ports.pointer?.x>300);
 const baked=await exportPage.evaluate(()=>window.__bakedAudit().ports.pointer);assert.equal(baked.isDown,false);assert.ok(Math.abs(baked.x-400)<1);assert.ok(Math.abs(baked.y-100)<1);assert.deepEqual(exportErrors,[]);assert.deepEqual(requests.filter(u=>!u.endsWith('favicon.ico')),[]);console.log('PASS baked pointer interaction from an empty origin, no editor requests');
 const redPixel=()=>{const c=document.getElementById('c2d'),p=c.getContext('2d').getImageData(400,240,1,1).data;return p[0]>200&&p[1]<20;};
 await exportPage.waitForFunction(redPixel);await exportPage.mouse.move(400,390);await exportPage.waitForFunction(()=>{const p=document.getElementById('c2d').getContext('2d').getImageData(400,240,1,1).data;return p[0]<20;});console.log('PASS pointer movement changes rendered triangle pixels');
 const clip=await page.evaluate(async()=>{const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;const ctx=canvas.getContext('2d');ctx.fillStyle='red';ctx.fillRect(0,0,64,64);const stream=canvas.captureStream(20),rec=new MediaRecorder(stream,{mimeType:'video/webm'}),parts=[];rec.ondataavailable=e=>parts.push(e.data);const done=new Promise(resolve=>rec.onstop=resolve);rec.start();await new Promise(r=>setTimeout(r,160));ctx.fillStyle='blue';ctx.fillRect(0,0,64,64);await new Promise(r=>setTimeout(r,160));rec.stop();await done;stream.getTracks().forEach(t=>t.stop());return await new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(new Blob(parts,{type:'video/webm'}));});});
 await page.evaluate(async clip=>{const a=window.__audit;a.storeWired({logic:{nodes:[{id:'vid',kind:'input-video',params:{_assetUrl:clip,loop:false,autoplay:false}}],edges:[],outputs:[]},layers:[{id:'vid',spec:{_camera:true,_cameraKind:'video',params:{loop:false,autoplay:false}},children:[{type:'asset',fromId:'clip',url:clip}]}]});await a.LogicBridge._ensureModules();},clip);
 await page.waitForFunction(()=>window.__audit.videoStreamEl('vid').readyState>=2);
 const playback=await page.evaluate(()=>{const v=window.__audit.videoStreamEl('vid');return{loop:v.loop,autoplay:v.autoplay,paused:v.paused,width:v.videoWidth};});assert.deepEqual(playback,{loop:false,autoplay:false,paused:true,width:64});
 await page.evaluate(()=>window.__audit.videoStreamEl('vid').play());await page.waitForFunction(()=>window.__audit.LogicBridge._ports.vid?.playing===true);console.log('PASS wired video decodes, honors controls, and reaches stream output');

 const audio=await browser.newPage();await audio.goto(base+'/blank');
 await audio.evaluate(async()=>{let mic=0;Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>{mic++;throw new Error('unexpected microphone');}},configurable:true});const {LogicInputs}=await import('/editor/tools/_shared/logicinputs.js');const {LogicGraph}=await import('/editor/tools/_shared/logicgraph.js');window.capture=LogicInputs.attach(document.getElementById('surface'),{audioNodes:[{id:'audio',params:{source:'asset',_assetUrl:'/tone.wav',fftSize:1000,smoothing:0,band:'full'}}]});window.audioPlan=LogicGraph.compile({nodes:[{id:'audio',kind:'input-audio',params:{source:'asset'}}]});window.sampleAudio=()=>LogicGraph.tick(window.audioPlan,window.capture.sample())._ports.audio;window.micCalls=()=>mic;window.requestAudio=window.capture.requestSensor('audio');});
 await audio.getByRole('button',{name:'Play sound',exact:true}).click();assert.equal(await audio.evaluate(()=>window.requestAudio),true);
 await audio.waitForFunction(()=>window.sampleAudio().level>0.1&&window.sampleAudio().pitch>400);const measured=await audio.evaluate(()=>({out:window.sampleAudio(),mic:window.micCalls()}));assert.equal(measured.mic,0);assert.ok(measured.out.band>0);assert.ok(measured.out.pitch>400&&measured.out.pitch<480,JSON.stringify(measured));await audio.evaluate(()=>window.capture.dispose());console.log('PASS deterministic WAV -> asset analyser -> graph, without microphone access');

 await page.evaluate(()=>{const a=window.__audit;a.storeWired({});a.setContent([{id:'card',kind:'html',url:'/card.html',label:'Card'}]);a.setState({canvasW:800,canvasH:400,background:'#000000',layers:[{id:'card-layer',visible:true,content:{kind:'asset',assetId:'card'},positioning:{mode:'single',x:0.5,y:0.5,scale:1,rot:0}}]});});
 const htmlAssetBake=await page.evaluate(()=>window.__audit.bake());const htmlPage=await browser.newPage({viewport:{width:800,height:400}}),htmlRequests=[];htmlPage.on('pageerror',e=>errors.push(e.message));
 await htmlPage.route('**/*',route=>{const u=route.request().url();if(u==='https://empty-html.invalid/')return route.fulfill({status:200,contentType:'text/html',body:htmlAssetBake});htmlRequests.push(u);return route.abort();});await htmlPage.goto('https://empty-html.invalid/');await htmlPage.waitForFunction(()=>{const p=document.getElementById('c2d').getContext('2d').getImageData(400,200,1,1).data;return p[0]>200&&p[1]<20;});assert.deepEqual(htmlRequests.filter(u=>!u.endsWith('favicon.ico')),[]);console.log('PASS exported HTML layer includes stylesheet, image and raster runtime');
 assert.deepEqual(errors,[]);console.log('6 browser integration groups passed');
}finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
