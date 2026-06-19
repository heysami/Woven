// Extracts Material Lab's verbatim sources and assembles the dispersion-prism
// material as a standalone, self-contained HTML (the same thing the in-app
// "Export" button / bakeHTML() produces) so it can be opened directly in a
// browser (file://) to verify the REAL material — no server, no daemon.
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, 'index.html');
const html = fs.readFileSync(SRC, 'utf8');

// --- pull a <script id="X"> ... </script> body verbatim ---
function scriptById(id) {
  const re = new RegExp('<script id="' + id + '"[^>]*>([\\s\\S]*?)</script>');
  const m = html.match(re);
  if (!m) throw new Error('script id=' + id + ' not found');
  return m[1].trim();
}

// --- brace-match a `function NAME(...) { ... }` verbatim, skipping braces that
//     live inside strings / comments (glassRuntime embeds GLSL braces in strings) ---
function funcText(name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('function ' + name + ' not found');
  let i = html.indexOf('{', start);
  let depth = 0, str = null, line = false, block = false;
  for (; i < html.length; i++) {
    const c = html[i], n = html[i + 1];
    if (line) { if (c === '\n') line = false; continue; }
    if (block) { if (c === '*' && n === '/') { block = false; i++; } continue; }
    if (str) { if (c === '\\') { i++; continue; } if (c === str) str = null; continue; }
    if (c === '/' && n === '/') { line = true; i++; continue; }
    if (c === '/' && n === '*') { block = true; i++; continue; }
    if (c === "'" || c === '"' || c === '`') { str = c; continue; }
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) return html.slice(start, i + 1); }
  }
  throw new Error('unbalanced braces in ' + name);
}

// --- pull the dispersion-prism shade backtick string verbatim ---
function dispersionShade() {
  const key = "'dispersion-prism':";
  const at = html.indexOf(key);
  if (at < 0) throw new Error('dispersion-prism material not found');
  const sAt = html.indexOf('shade:`', at);
  const begin = sAt + 'shade:`'.length;
  const end = html.indexOf('`', begin);
  return html.slice(begin, end);
}

const VS_SRC    = scriptById('vsrc');
const GLSL_HEAD = scriptById('glslHead');
const GLSL_MAIN = scriptById('glslMain');
const SHADE     = dispersionShade();
const FRAG_SRC  = GLSL_HEAD + '\n' + SHADE + '\n' + GLSL_MAIN;   // == composeFrag()

const hexRGB           = funcText('hexRGB');
const matToUniforms    = funcText('matToUniforms');
const drawBackdropInto = funcText('drawBackdropInto');
const glassRuntime     = funcText('glassRuntime');

// dispersion-prism params (Material Lab BASE_PARAMS + the preset's overrides)
const STATE = {
  background: '#0b0d12',
  backdrop: 'aurora-gradient',
  bgImage: '',
  palette: ['#7cc7ff', '#b388ff', '#ff8ad1', '#7CF5C8', '#FFD75E'],
  material: {
    type: 'dispersion-prism',
    profile: 'convex', ior: 1.52, thickness: 46, bezel: 0.40, dispersion: 0.40,
    frost: 0.02, specular: 0.5, shininess: 90, fresnel: 0.8,
    tint: '#ffffff', tintAmt: 0.0, alpha: 0.92, holo: false,
    colorA: '#c9d2de', colorB: '#1a1f27', scale: 22, rough: 0.5, anis: 0.6, glow: 1.0,
  },
};

const radius = (10 + STATE.material.thickness * 0.35).toFixed(0) + 'px';
const acc = STATE.palette[0], acc2 = STATE.palette[1];
const swatches = STATE.palette.slice(0, 5)
  .map(c => `<div class="swatch" style="background:${c}"></div>`).join('');

const runtimeJS = [
  'const VS_SRC=' + JSON.stringify(VS_SRC) + ';',
  'const FRAG_SRC=' + JSON.stringify(FRAG_SRC) + ';',
  'const STATE=' + JSON.stringify(STATE) + ';',
  hexRGB,
  matToUniforms,
  drawBackdropInto,
  glassRuntime,
  'let bgImg=null;',
  'const RT=glassRuntime({canvas:document.getElementById("glcanvas"),stage:document.getElementById("stage"),vsSrc:VS_SRC,panelSelector:".mat",' +
    'getFragSrc:()=>FRAG_SRC,getUniforms:()=>matToUniforms(STATE.material),isFluid:()=>false,drawBackdrop:(ctx,w,h)=>drawBackdropInto(ctx,w,h,STATE,bgImg),' +
    'onError:(m)=>{var w=document.getElementById("glwarn");if(w){w.style.display="flex";w.textContent="Glass shader error: "+m;}}});',
  'if(RT){var sr=null;function cr(){sr=document.getElementById("stage").getBoundingClientRect();}cr();window.addEventListener("resize",()=>{cr();RT.resize();});',
  'document.getElementById("stage").addEventListener("pointermove",e=>{RT.setLight(e.clientX-sr.left,e.clientY-sr.top);});',
  'RT.setLight(document.getElementById("stage").clientWidth*0.42,document.getElementById("stage").clientHeight*0.30);}',
].join('\n');

const out = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dispersion Prism — Material Lab export</title>
<style>
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;background:${STATE.background};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
  #wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:40px}
  #stage{position:relative;width:760px;max-width:100%;border-radius:20px;overflow:hidden;box-shadow:0 30px 90px #000a;background:${STATE.background};--m-radius:${radius};--m-accent:${acc};--m-accent2:${acc2}}
  #backdrop{position:absolute;inset:0;z-index:0;background-color:${STATE.background};
    background-image:radial-gradient(70% 60% at 20% 15%,#2a4cffcc,transparent 60%),radial-gradient(60% 55% at 85% 20%,#b34cffbb,transparent 62%),radial-gradient(80% 70% at 60% 100%,#16d6b4bb,transparent 60%)}
  #glcanvas{position:absolute;inset:0;z-index:1;pointer-events:none;display:block}
  #glwarn{position:absolute;inset:0;z-index:1;display:none;align-items:center;justify-content:center;color:#ffb4b4;font-family:ui-monospace,Menlo,monospace;font-size:12px;text-align:center;padding:30px;background:#0008}
  #gallery{position:relative;z-index:2;padding:26px 28px;display:flex;flex-direction:column;gap:22px}
  .mat{position:relative;border-radius:var(--m-radius)}.mat>*{position:relative;z-index:2}
  .ds-card{padding:24px 26px}
  .head{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#fff;opacity:.6;margin-bottom:14px;font-weight:700;text-shadow:0 1px 3px #0006}
  .type-display{font-size:38px;font-weight:800;line-height:1.05;letter-spacing:-.02em;color:#fff;margin:0;text-shadow:0 2px 10px #0007}
  .type-heading{font-size:21px;font-weight:700;color:#fff;margin:8px 0 0;text-shadow:0 1px 6px #0007}
  .type-body{font-size:13px;color:#fff;opacity:.85;margin:6px 0 0;line-height:1.5;text-shadow:0 1px 4px #0006}
  .swatches{display:flex;gap:10px}.swatch{width:46px;height:46px;border-radius:12px;box-shadow:inset 0 0 0 1px #ffffff33,0 4px 14px #0007}
  .tabs{display:flex;gap:6px;border-bottom:1px solid #ffffff2f}.tab{padding:9px 16px;font-size:13px;color:#fff;opacity:.6;border-bottom:2px solid transparent;font-weight:600;text-shadow:0 1px 3px #0006}.tab.active{opacity:1;border-bottom-color:var(--m-accent)}
  .ds-input{display:flex;align-items:center;padding:0 14px;height:42px;font-size:13px;color:#fff;opacity:.85;text-shadow:0 1px 3px #0006}
  .btnrow{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.ds-btn{height:40px;padding:0 20px;font-size:13px;font-weight:600;color:#fff;display:inline-flex;align-items:center;border-radius:calc(var(--m-radius)*0.7);text-shadow:0 1px 3px #0007}
  .galrow{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-start}.galcol{display:flex;flex-direction:column;gap:14px;flex:1;min-width:240px}
</style></head><body>
<div id="wrap"><div id="stage" data-surface="dark">
  <div id="backdrop"></div><canvas id="glcanvas"></canvas><div id="glwarn"></div>
  <div id="gallery">
    <div class="mat ds-card"><div class="head">Dispersion Prism · Material Lab</div><h1 class="type-display">Display Large</h1><div class="type-heading">Heading Medium</div><div class="type-body">Body — the quick brown fox jumps over the lazy dog. Move your pointer to see the spectral fringe ride the rim.</div></div>
    <div class="galrow"><div class="galcol">
      <div class="mat ds-card"><div class="head">Palette</div><div class="swatches">${swatches}</div></div>
      <div class="mat ds-card"><div class="head">Tabs</div><div class="tabs"><div class="tab active">Overview</div><div class="tab">Activity</div><div class="tab">Settings</div></div></div>
      <div class="mat ds-input">Enter text…</div>
      <div class="mat ds-card"><div class="head">Buttons</div><div class="btnrow"><div class="mat ds-btn">Primary</div><div class="mat ds-btn">Secondary</div></div></div>
    </div></div>
  </div>
</div></div>
<script>${runtimeJS}<\/script>
</body></html>`;

const DEST = path.join(__dirname, '..', '..', 'default-design-system', 'themes', '_glass-dispersion-prism.demo.html');
fs.writeFileSync(DEST, out);
console.log('wrote', DEST);
console.log('VS_SRC', VS_SRC.length, 'FRAG_SRC', FRAG_SRC.length, 'glassRuntime', glassRuntime.length, 'chars');

/* =====================================================================
   INTEGRATED demo — REAL design-system components (via all.css +
   data-theme="glassmorphism"), with the SAME verbatim dispersion-prism
   runtime rendering glass behind them. Fixed (non-scrolling) stage so
   glassRuntime's panel measurement (stage.querySelectorAll, ≤24) works
   unchanged. Open directly in a browser (file://) to verify.
   ===================================================================== */
const PANEL_SEL = '.card,.section-card,.stat-hero,.chart-card,.btn--primary,.btn--outline,.input,.badge,.tag';
const integRuntimeJS = [
  'const VS_SRC=' + JSON.stringify(VS_SRC) + ';',
  'const FRAG_SRC=' + JSON.stringify(FRAG_SRC) + ';',
  'const STATE=' + JSON.stringify(STATE) + ';',
  hexRGB, matToUniforms, drawBackdropInto, glassRuntime,
  'let bgImg=null;',
  'const stage=document.getElementById("stage");',
  'const RT=glassRuntime({canvas:document.getElementById("glcanvas"),stage:stage,vsSrc:VS_SRC,panelSelector:' + JSON.stringify(PANEL_SEL) + ',' +
    'getFragSrc:()=>FRAG_SRC,getUniforms:()=>matToUniforms(STATE.material),isFluid:()=>false,drawBackdrop:(ctx,w,h)=>drawBackdropInto(ctx,w,h,STATE,bgImg),' +
    'onError:(m)=>{var w=document.getElementById("glwarn");if(w){w.style.display="flex";w.textContent="Glass shader error: "+m;}}});',
  // mark GL active so the theme drops its backdrop-filter fallback and goes fully transparent
  'if(RT){document.documentElement.classList.add("glass-gl");',
  // re-measure on layout shifts + every frame (cheap for <=24 panels) so the glass tracks the components
  'var ro=new ResizeObserver(()=>RT.resize());ro.observe(stage);window.addEventListener("resize",()=>RT.resize());',
  'function tick(){RT.remeasure();requestAnimationFrame(tick);}requestAnimationFrame(tick);',
  'var sr=stage.getBoundingClientRect();stage.addEventListener("pointermove",e=>RT.setLight(e.clientX-sr.left,e.clientY-sr.top));',
  'window.addEventListener("scroll",()=>{sr=stage.getBoundingClientRect();},{passive:true});',
  'RT.setLight(stage.clientWidth*0.42,stage.clientHeight*0.30);}',
].join('\n');

const integ = `<!doctype html><html lang="en" data-theme="glassmorphism"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Glassmorphism — real dispersion-prism on DS components</title>
<link rel="stylesheet" href="../all.css">
<style>
  html,body{margin:0;min-height:100%;background:${STATE.background}}
  #wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:40px}
  /* fixed-size stage: holds the DS components + the glass canvas behind them */
  #stage{position:relative;width:980px;max-width:100%;border-radius:24px;overflow:hidden;box-shadow:0 30px 90px #000a;background:${STATE.background}}
  #backdrop{position:absolute;inset:0;z-index:0;background-color:${STATE.background};
    background-image:radial-gradient(70% 60% at 20% 15%,#2a4cffcc,transparent 60%),radial-gradient(60% 55% at 85% 20%,#b34cffbb,transparent 62%),radial-gradient(80% 70% at 60% 100%,#16d6b4bb,transparent 60%)}
  #glcanvas{position:absolute;inset:0;z-index:1;pointer-events:none;display:block}
  #glwarn{position:absolute;inset:0;z-index:1;display:none;align-items:center;justify-content:center;color:#ffb4b4;font:12px ui-monospace,Menlo,monospace;text-align:center;padding:30px;background:#0008}
  #content{position:relative;z-index:2;padding:34px;display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
  #content > h1{grid-column:1/-1;color:#fff;font-size:34px;margin:0 0 4px;text-shadow:0 2px 12px #0008}
  #content > .lead{grid-column:1/-1;color:#fff;opacity:.85;margin:0 0 8px;text-shadow:0 1px 6px #0007}
  /* GL mode: once the WebGL glass mounts, the DS surfaces go fully transparent
     (the canvas IS the surface) but KEEP their border (the lens edge), radius,
     padding + sit above the canvas. Text goes light to read on the dark glass. */
  html.glass-gl [data-theme="glassmorphism"] #content :is(.card,.section-card,.stat-hero,.chart-card,.btn--primary,.btn--outline,.input,.badge,.tag),
  html.glass-gl #content :is(.card,.section-card,.stat-hero,.chart-card,.btn--primary,.btn--outline,.input,.badge,.tag){
    background:transparent !important;-webkit-backdrop-filter:none !important;backdrop-filter:none !important;
    position:relative;z-index:2;border-color:rgba(255,255,255,.40);
  }
  html.glass-gl #content,html.glass-gl #content :is(h1,h2,h3,h4,h5,p,span,div,a,label){color:#fff !important;text-shadow:0 1px 4px #0007}
  html.glass-gl #content :is(.btn--primary,.btn--outline){color:#fff !important}
</style></head><body>
<div id="wrap"><div id="stage">
  <div id="backdrop"></div><canvas id="glcanvas"></canvas><div id="glwarn"></div>
  <div id="content">
    <h1>Glassmorphism</h1>
    <p class="lead">Real Material Lab <strong>dispersion-prism</strong> rendered behind live design-system components. Move your pointer — the spectral fringe rides each bezel.</p>

    <div class="stat-hero">
      <div class="stat-hero__label">Revenue · 30d</div>
      <div class="stat-hero__value">$48,210</div>
      <div class="stat-hero__delta is-up">+12.4%</div>
    </div>

    <div class="card">
      <h3 class="h3">Card title</h3>
      <p class="text-body">A line of body text describing the card content, sitting on real refractive glass.</p>
      <div style="display:flex;gap:10px;margin-top:14px">
        <button class="btn btn--primary">Primary</button>
        <button class="btn btn--outline">Secondary</button>
      </div>
    </div>

    <div class="section-card">
      <h4 class="h4">Form</h4>
      <input class="input" placeholder="Enter text…" style="margin-top:10px;width:100%">
      <div style="display:flex;gap:8px;margin-top:12px">
        <span class="badge">Badge</span><span class="tag">Tag</span><span class="badge is-up">+ Active</span>
      </div>
    </div>

    <div class="card">
      <h4 class="h4">Tags &amp; chips</h4>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">
        <span class="tag">Design</span><span class="tag">System</span><span class="tag">Glass</span><span class="badge">v2</span>
      </div>
    </div>
  </div>
</div></div>
<script>${integRuntimeJS}<\/script>
</body></html>`;

const DEST2 = path.join(__dirname, '..', '..', 'default-design-system', 'themes', '_glassmorphism.integrated.demo.html');
fs.writeFileSync(DEST2, integ);
console.log('wrote', DEST2);

/* =====================================================================
   themes/glassmorphism.js — the SHIPPING runtime module. Self-activating:
   mounts a fixed full-viewport WebGL glass canvas behind the page ONLY when
   <html data-theme="glassmorphism">, points the verbatim dispersion-prism
   runtime at the design-system surfaces, tracks them on scroll/resize, and
   toggles the `glass-gl` class so the theme CSS drops its backdrop-filter
   fallback and goes transparent. Reacts live to data-theme changes (editor
   preview). Degrades to the CSS fallback if WebGL2 is unavailable.
   GENERATED from Material Lab — do not hand-edit; re-run _bake-dispersion-prism.js.
   ===================================================================== */
const moduleJS = `/* GENERATED from editor/tools/materiallab — verbatim dispersion-prism runtime. */
(function(){
"use strict";
var VS_SRC=${JSON.stringify(VS_SRC)};
var FRAG_SRC=${JSON.stringify(FRAG_SRC)};
var STATE=${JSON.stringify(STATE)};
${hexRGB}
${matToUniforms}
${drawBackdropInto}
${glassRuntime}
/* ---- self-activating bootstrap ---- */
var SURF=${JSON.stringify(PANEL_SEL + ',.modal,.slideout,.kpi,.metric-tile')};
var RT=null, canvas=null, raf=0;
function isOn(){ return document.documentElement.getAttribute("data-theme")==="glassmorphism"; }
function stageProxy(){ return {
  get clientWidth(){ return window.innerWidth; },
  get clientHeight(){ return window.innerHeight; },
  getBoundingClientRect:function(){ return {left:0,top:0,right:innerWidth,bottom:innerHeight,width:innerWidth,height:innerHeight}; },
  querySelectorAll:function(s){ return document.querySelectorAll(s); }
}; }
function loop(){ if(!RT) return; RT.remeasure(); raf=requestAnimationFrame(loop); }
function onResize(){ if(RT) RT.resize(); }
function onMove(e){ if(RT) RT.setLight(e.clientX, e.clientY); }
function mount(){
  if(RT || !document.body) return;
  canvas=document.createElement("canvas");
  canvas.id="__glass-canvas";
  canvas.style.cssText="position:fixed;inset:0;z-index:-1;pointer-events:none;display:block";
  document.body.appendChild(canvas);
  RT=glassRuntime({canvas:canvas,stage:stageProxy(),vsSrc:VS_SRC,panelSelector:SURF,
    getFragSrc:function(){return FRAG_SRC;},getUniforms:function(){return matToUniforms(STATE.material);},
    isFluid:function(){return false;},drawBackdrop:function(ctx,w,h){drawBackdropInto(ctx,w,h,STATE,null);},
    onError:function(m){ if(window.console)console.warn("[glassmorphism] "+m); teardown(); }});
  if(!RT){ if(canvas&&canvas.parentNode)canvas.parentNode.removeChild(canvas); canvas=null; return; }
  document.documentElement.classList.add("glass-gl");
  window.addEventListener("resize",onResize,{passive:true});
  window.addEventListener("pointermove",onMove,{passive:true});
  loop();
}
function teardown(){
  if(raf){ cancelAnimationFrame(raf); raf=0; }
  window.removeEventListener("resize",onResize); window.removeEventListener("pointermove",onMove);
  if(RT && RT.dispose) RT.dispose(); RT=null;
  if(canvas && canvas.parentNode) canvas.parentNode.removeChild(canvas); canvas=null;
  document.documentElement.classList.remove("glass-gl");
}
function sync(){ if(isOn()) mount(); else teardown(); }
try{ new MutationObserver(sync).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]}); }catch(e){}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",sync); else sync();
})();
`;
const DEST3 = path.join(__dirname, '..', '..', 'default-design-system', 'themes', 'glassmorphism.js');
fs.writeFileSync(DEST3, moduleJS);
console.log('wrote', DEST3, '(' + moduleJS.length + ' chars)');
