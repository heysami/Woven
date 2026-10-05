// Behavioral regressions for Woven-Canvas-Audit F04-F18. No hardware or network.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const modules=new Map();
function moduleURL(name){
  const full=path.resolve(dir,name);if(modules.has(full))return modules.get(full);
  let src=fs.readFileSync(full,'utf8');src=src.replace(/from ['"](\.\/[^'"]+)['"]/g,(_,rel)=>"from '"+moduleURL(rel)+"'");
  const url='data:text/javascript;base64,'+Buffer.from(src).toString('base64');modules.set(full,url);return url;
}
const {LogicGraph:LG}=await import(moduleURL('logicgraph.js'));
const {LogicInputs:LI}=await import(moduleURL('logicinputs.js'));
const {LogicPermission:LP}=await import(moduleURL('logicpermission.js'));
const {LogicVision:LV}=await import(moduleURL('logicvision.js'));
LP.requestGesture=async(_opts,allow)=>allow();
const edge=(from,port,to,input)=>({from:{node:from,port},to:{node:to,port:input}});
const node=(id,kind,params={})=>({id,kind,params});
let passed=0;
async function test(name,fn){await fn();passed++;console.log('PASS '+name);}
function tick(plan,input={}){return LG.tick(plan,{dt:1/60,...input})._ports;}
class Surface extends EventTarget {tabIndex=-1;getBoundingClientRect(){return{left:10,top:20,width:800,height:400};}}
const win=new EventTarget();globalThis.window=win;
let pads=[];const midiPort={};const access={inputs:new Map([['port',midiPort]])};
Object.defineProperty(globalThis,'navigator',{configurable:true,value:{getGamepads:()=>pads,requestMIDIAccess:async()=>access}});
function dispatch(target,type,props={}){const e=new Event(type);Object.assign(e,props);target.dispatchEvent(e);}
await test('capture -> tick -> bound outputs: gamepad, accel and MIDI',async()=>{
  const surface=new Surface(),capture=LI.attach(surface,{audioNodes:[]});
  await capture.requestSensor('accel');await capture.requestSensor('midi');
  pads=[{axes:[0.7,-0.2,0.1,0.3],buttons:[{pressed:true}]}];
  dispatch(win,'devicemotion',{accelerationIncludingGravity:{x:3,y:4,z:5}});
  midiPort.onmidimessage({data:[0x90,64,127]});
  const plan=LG.compile({nodes:[node('g','input-gamepad'),node('a','input-accel'),node('m','input-midi')],outputs:[{sourceNode:'g',sourcePort:'x',targetNode:'shape',targetParam:'x'}]});
  const out=LG.tick(plan,capture.sample());assert.equal(out['shape.x'],0.7);assert.equal(out._ports.g.a,true);assert.equal(out._ports.m.note,64);assert.equal(out._ports.m.gate,true);assert.equal(out._ports.a.z,3.5);
  pads=[];assert.equal(tick(plan,capture.sample()).g.x,0);capture.dispose();
});
await test('same captured pointer has independent button and coordinate settings',()=>{
  const surface=new Surface(),capture=LI.attach(surface,{audioNodes:[]});
  const plan=LG.compile({nodes:[node('right','input-pointer',{space:'pixels',button:'right'}),node('left','input-pointer',{space:'normalized',button:'left'})]});
  dispatch(surface,'pointerdown',{pointerType:'mouse',clientX:410,clientY:120,button:0,buttons:1});
  let out=tick(plan,capture.sample());assert.equal(out.right.x,400);assert.equal(out.right.y,100);assert.equal(out.right.clicked,false);assert.equal(out.left.x,0.5);assert.equal(out.left.clicked,true);
  dispatch(surface,'pointerdown',{pointerType:'mouse',clientX:410,clientY:120,button:2,buttons:3});out=tick(plan,capture.sample());assert.equal(out.right.clicked,true);capture.dispose();
});
await test('touch limits/units, wheel units/clamp and keyboard repeats survive capture',()=>{
  const surface=new Surface(),capture=LI.attach(surface,{audioNodes:[]});
  const plan=LG.compile({nodes:[node('t','input-touch',{space:'pixels',maxPoints:1}),node('s','input-scroll',{clampMin:0,clampMax:0.3}),node('k','input-keyboard',{key:'a',repeat:true}),node('once','input-keyboard',{key:'a',repeat:false})]});
  dispatch(surface,'pointerdown',{pointerType:'touch',pointerId:1,clientX:210,clientY:120});dispatch(surface,'pointerdown',{pointerType:'touch',pointerId:2,clientX:610,clientY:320});
  dispatch(surface,'wheel',{deltaX:0,deltaY:200,deltaMode:0});dispatch(surface,'keydown',{key:'a',repeat:false});
  let out=tick(plan,capture.sample());assert.equal(out.t.count,1);assert.equal(out.t.pos.x,200);assert.equal(out.s.deltaY,0.5);assert.equal(out.s.accumY,0.3);assert.equal(out.k.pressed,true);
  dispatch(surface,'keydown',{key:'b',repeat:false});dispatch(surface,'keydown',{key:'a',repeat:true});out=tick(plan,capture.sample());assert.equal(out.k.pressed,true);assert.equal(out.once.pressed,false);assert.equal(out.once.isDown,true);capture.dispose();
});
await test('gyro smoothing is independent for two nodes',async()=>{
 const surface=new Surface(),capture=LI.attach(surface,{audioNodes:[]});await capture.requestSensor('gyro');dispatch(win,'deviceorientation',{alpha:10,beta:20,gamma:30});
 const out=tick(LG.compile({nodes:[node('raw','input-gyro',{smoothing:0}),node('smooth','input-gyro',{smoothing:0.5})]}),capture.sample());assert.equal(out.raw.beta,20);assert.equal(out.smooth.beta,10);capture.dispose();
});
await test('all vector modes follow declared ports',()=>{
 const nodes=[node('v','value-vec2',{x:3,y:4}),node('b','value-vec2',{x:6,y:8}),node('t','control-panel',{a:2})];
 for(const [mode,expected] of [['make',{v:{x:2,y:2}}],['break',{x:3,y:4}],['distance',{d:5}],['add',{v:{x:9,y:12}}],['scale',{v:{x:6,y:8}}],['lerp',{v:{x:6,y:8}}]]){
 const plan=LG.compile({nodes:[...nodes,node('op','op-vector',{mode})],edges:[edge('v','value','op','v'),edge('v','value','op','a'),edge('b','value','op','b'),edge('t','a','op','t'),edge('t','a','op','x'),edge('t','a','op','y')]});assert.deepEqual(tick(plan).op,expected);}
});
await test('delay warm-up and exact ramp/impulse timing for N=1,2,3',()=>{
 for(const n of [1,2,3])for(const values of [[10,20,30,40,50],[1,0,0,0,0]]){
 const source=node('p','control-panel');const plan=LG.compile({nodes:[source,node('d','state-delay',{frames:n})],edges:[edge('p','a','d','x')]});
 const actual=values.map(x=>{source.params.a=x;return tick(plan).d.value;});assert.deepEqual(actual,values.map((_,i)=>i<n?0:values[i-n]));}
});
await test('delay feedback accumulates independently of node order',()=>{
 for(const reverse of [false,true]){const nodes=[node('d','state-delay',{frames:1}),node('one','control-panel',{a:1}),node('add','op-math',{op:'add'})];if(reverse)nodes.reverse();
 const plan=LG.compile({nodes,edges:[edge('d','value','add','a'),edge('one','a','add','b'),edge('add','r','d','x')]});assert.deepEqual(plan.errors,[]);assert.deepEqual(Array.from({length:5},()=>tick(plan).add.r),[1,2,3,4,5]);}
});
await test('latch feedback holds captured output, pure self-loop is rejected',()=>{
 const gate=node('gate','value-bool',{value:true});const plan=LG.compile({nodes:[node('l','state-latch'),node('add','op-math',{op:'add'}),node('one','control-panel',{a:1}),gate],edges:[edge('l','value','add','a'),edge('one','a','add','b'),edge('add','r','l','hold'),edge('gate','value','l','set')]});
 assert.equal(tick(plan).add.r,1);gate.params.value=false;assert.equal(tick(plan).add.r,2);assert.equal(tick(plan).l.value,1);
 assert.ok(LG.compile({nodes:[node('x','op-math')],edges:[edge('x','r','x','a')]}).errors.length);
});
await test('face and hand detections remain independent on one camera',()=>{
 LV._detect={};LV.detect('cam',{detector:'face'});LV.detect('cam',{detector:'hand'});
 LV._detect.cam.face.result={_dets:[{x:0.2,y:0.3}]};LV._detect.cam.hand.result={_dets:[{x:0.7,y:0.8}]};
 const plan=LG.compile({nodes:[node('cam','input-camera'),node('f','vision-detect',{detector:'face'}),node('h','vision-detect',{detector:'hand'})],edges:[edge('cam','stream','f','stream'),edge('cam','stream','h','stream')]});
 const out=tick(plan,{streams:LV.frame(['cam'])});assert.equal(out.f.pos.x,0.2);assert.equal(out.h.pos.x,0.7);
});
await test('legacy tracking uses actual landmarks, including an empty result',()=>{
 const video={currentTime:0,paused:false};LV._detect={};LV.detect('legacy',{detector:'face'});LV._detect.legacy.face.busy=true;LV._detect.legacy.face.result={_dets:[{landmarks:[{x:0.2,y:0.7}]}]};
 assert.deepEqual(LV.positions('legacy',video,{mode:'face-3d',size:1}),[{x:0.2,y:0.7,scale:0.4,rot:0}]);LV._detect.legacy.face.result={_dets:[]};assert.deepEqual(LV.positions('legacy',video,{mode:'face-3d'}),[]);
});
await test('WebSocket retry, URL changes and disposal close the right resources',()=>{
 const sockets=[];globalThis.WebSocket=class{constructor(url){this.url=url;sockets.push(this);}close(){this.closed=true;}};
 const source=node('ws','dat-websocket',{url:'wss://example.invalid'}),plan=LG.compile({nodes:[source]});tick(plan,{time:0});assert.equal(sockets.length,1);sockets[0].onclose();tick(plan,{time:0.9});assert.equal(sockets.length,1);tick(plan,{time:1});assert.equal(sockets.length,2);
 source.params.url='wss://other.invalid';tick(plan,{time:2});assert.equal(sockets[1].closed,true);assert.equal(sockets.length,3);LG.dispose(plan);assert.equal(sockets[2].closed,true);assert.equal(sockets[2].onmessage,null);assert.deepEqual(LG.tick(plan,{}),{});
});
await test('string template supports v without replacement metacharacter expansion',()=>{
 const plan=LG.compile({nodes:[node('s','value-string',{value:'$&'}),node('f','op-tostring',{template:'value={v}'})],edges:[edge('s','value','f','a')]});assert.equal(tick(plan).f.s,'value=$&');
});
const app=fs.readFileSync(path.join(dir,'../../app.js'),'utf8');
const sandbox={};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(dir,'../../kinds/logic_nodes.js'),'utf8'),sandbox);
const defs=sandbox.TH_LOGIC_NODE_DEFS;
sandbox.workflowParseEdgeRef=s=>{const i=s.lastIndexOf('.');return i<0?null:{node:s.slice(0,i),port:s.slice(i+1)};};
sandbox._specDefault=kind=>({params:Object.fromEntries(Object.entries(defs[kind]?.controls||{}).map(([k,v])=>[k,v.value]))});
sandbox._isLogicKind=kind=>!!defs[kind]&&!['shape','type-motion','force'].includes(kind);
sandbox.workflowLogicPortSide=(n,p)=>defs[n.kind]?.accepts[p]?'in':null;
sandbox.workflowPortDtype=(n,p,side)=>defs[n.kind]?.[side][p]?.dtype;
sandbox._composerAssetUrl=n=>n.url;sandbox._paletteImageUrl=()=>null;
vm.runInContext(app.slice(app.indexOf('function _logicProjection('),app.indexOf('// Resolve the image asset URL wired into a palette')),sandbox);
await test('composer projection isolates inputs, forces, sound and sockets',()=>{
 const nodes=[{id:'c1',kind:'mm-composer'},{id:'c2',kind:'mm-composer'},...['1','2'].flatMap(i=>[{id:'shape'+i,kind:'shape'},{id:'p'+i,kind:'input-pointer'},{id:'sound'+i,kind:'audio-out'},{id:'force'+i,kind:'force'},{id:'socket'+i,kind:'dat-websocket'}]),{id:'orphan',kind:'audio-out'}];
 const edges=['1','2'].flatMap(i=>[{from:'shape'+i+'.out',to:'c'+i+'.in'},{from:'p'+i+'.pos',to:'shape'+i+'.p0'},{from:'sound'+i+'.out',to:'c'+i+'.in'},{from:'socket'+i+'.value',to:'sound'+i+'.frequency'},{from:'force'+i+'.out',to:'c'+i+'.in'}]);
 const projection=sandbox._logicProjection(nodes,edges,'c1');assert.deepEqual(Array.from(projection.nodes,n=>n.id).sort(),['force1','p1','socket1','sound1']);assert.equal(projection.forces.length,1);
});
await test('actual upstream resolver retains Video.asset as layer content',()=>{
 sandbox.WORKFLOW_BAKED_EDITABLE_KINDS=new Set();sandbox._composerLayerLabel=n=>n.id;sandbox._composerAssetKind=()=> 'video';
 sandbox.workflowKindIo=kind=>({provides:kind==='input-video'?[{port:'layer',tags:['layer'],resolve:'typed',resolveArgs:{flavor:'layer'}}]:[{port:'out',tags:['asset'],resolve:'assetFile'}]});
 vm.runInContext(app.slice(app.indexOf('function _ioProvideForPort('),app.indexOf('function _firstProvidePort(')),sandbox);
 const result=sandbox.resolveUpstreamInputs({id:'c'},[{id:'c',kind:'mm-composer'},{id:'v',kind:'input-video'},{id:'clip',kind:'asset',url:'clip.mp4'}],[{from:'clip.out',to:'v.asset'},{from:'v.layer',to:'c.in'}]);assert.equal(result[0].children[0].url,'clip.mp4');
});
await test('persistence callbacks keep stale bake metadata on HTTP failure and expose errors',async()=>{
 const start=app.indexOf('  const persistState = useCallback('),end=app.indexOf('  // Push the init payload.',start);
 const code=app.slice(start,end)+'\nthis.auditPersist={persistState,persistBaked};';let timers=[],changes=[];
 Object.assign(sandbox,{useCallback:fn=>fn,pendingRef:{current:null},saveTimerRef:{current:null},bakedSaveTimerRef:{current:null},lastWrittenRef:{current:null},cfg:{canonicalIsBaked:false,stateField:'state'},node:{bakedPath:'old.html'},canonicalPath:'state.json',bakedPathTarget:'new.html',onChange:p=>changes.push(p),onBakeAutoCreateOutput:()=>{throw new Error('must not publish');},apiUrl:p=>p,setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout:()=>{},fetch:async()=>({ok:false,status:500,text:async()=> 'write failed'})});
 vm.runInContext(code,sandbox);sandbox.auditPersist.persistState({v:1},{text:'new bake'});await timers.shift()();assert.equal(changes.at(-1).runStatus,'error');assert.ok(!changes.some(p=>p.bakedAt));
 changes=[];sandbox.auditPersist.persistBaked({text:'new bake'});await timers.shift()();assert.equal(changes.at(-1).runStatus,'error');assert.ok(!changes.some(p=>p.bakedAt));
});
await test('media projection retains wired asset URL and playback settings',()=>{
 const nodes=[{id:'clip',kind:'asset',url:'clip.mp4'},{id:'v',kind:'input-video',spec:{kind:'input-video',params:{loop:false,autoplay:false}}},{id:'c',kind:'mm-composer'}];
 const projection=sandbox._logicProjection(nodes,[{from:'clip.out',to:'v.asset'},{from:'v.layer',to:'c.in'}],'c');const v=projection.nodes.find(n=>n.id==='v');assert.equal(v.params._assetUrl,'clip.mp4');assert.equal(v.params.loop,false);
});
await test('failed persistence rejects instead of announcing a saved bake',async()=>{
 vm.runInContext(app.slice(app.indexOf('async function _writeToolArtifact('),app.indexOf('function _logicProjection(')),sandbox);sandbox.fetch=async()=>({ok:false,status:500,text:async()=> 'disk full'});await assert.rejects(sandbox._writeToolArtifact('/write',{}),/500.*disk full/);
});
const {bundleRuntime,bundleLocalMedia}=await import(moduleURL('bundle-runtime.js'));
await test('export recursively bundles modules and refuses a missing dependency',async()=>{
 const fetcher=async url=>({ok:true,text:async()=>fs.readFileSync(path.join(dir,new URL(url).pathname.split('/').pop()),'utf8')});
 const packed=await bundleRuntime({logicgraph:'https://fixture.invalid/logicgraph.js',logicinputs:'https://fixture.invalid/logicinputs.js'},fetcher);const {LogicGraph}=await import(packed.logicgraph);assert.equal(typeof LogicGraph.tick,'function');await import(packed.logicinputs);
 await assert.rejects(bundleRuntime({x:'https://fixture.invalid/x.js'},async()=>({ok:false,status:404})),/404/);
});
await test('export embeds media but leaves live data endpoints intact',async()=>{
 let reads=0;const result=await bundleLocalMedia({assets:[{kind:'video',url:'/clip.mp4'}],nodes:[{params:{url:'wss://live.invalid',_assetUrl:'/audio.wav'}}]},'https://fixture.invalid/',async()=>{reads++;return{ok:true,arrayBuffer:async()=>new Uint8Array([1,2]).buffer,headers:{get:()=> 'audio/wav'}};});assert.equal(reads,2);assert.match(result.assets[0].url,/^data:/);assert.equal(result.nodes[0].params.url,'wss://live.invalid');
});
console.log(`${passed} audit regression groups passed`);
