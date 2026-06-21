// General: extract a Material Lab material (verbatim shader + runtime) and emit
// a self-activating design-system theme runtime themes/<theme>.js - the same
// machinery glassmorphism uses, parameterised by material. Run:  node _bake-material-theme.js
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, 'index.html');
const html = fs.readFileSync(SRC, 'utf8');

function scriptById(id) {
  const m = html.match(new RegExp('<script id="' + id + '"[^>]*>([\\s\\S]*?)</script>'));
  if (!m) throw new Error('script id=' + id + ' not found');
  return m[1].trim();
}
function funcText(name) {
  const start = html.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('function ' + name + ' not found');
  let i = html.indexOf('{', start), depth = 0, str = null, line = false, block = false;
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
function materialShade(id) {
  const at = html.indexOf("'" + id + "':");
  if (at < 0) throw new Error('material ' + id + ' not found');
  const begin = html.indexOf('shade:`', at) + 'shade:`'.length;
  return html.slice(begin, html.indexOf('`', begin));
}

const VS_SRC = scriptById('vsrc');
const GLSL_HEAD = scriptById('glslHead');
const GLSL_MAIN = scriptById('glslMain');
const hexRGB = funcText('hexRGB');
const matToUniforms = funcText('matToUniforms');
const drawBackdropInto = funcText('drawBackdropInto');
const glassRuntime = funcText('glassRuntime');

// Material Lab BASE_PARAMS (index.html) - themes layer their material overrides on top.
const BASE_PARAMS = {
  profile: 'convex', ior: 1.50, thickness: 38, bezel: 0.45, dispersion: 0.18, frost: 0.0,
  specular: 0.70, shininess: 80, fresnel: 0.50, tint: '#ffffff', tintAmt: 0.0, alpha: 1.0, holo: false,
  colorA: '#c9d2de', colorB: '#1a1f27', scale: 22, rough: 0.5, anis: 0.6, glow: 1.0,
};
// Shader runs on NON-SCROLLING chrome only - zero lag under native scroll.
const SURF = '.topbar,.sidebar,.appbar,.tabbar,.phone__tabbar,.modal,.slideout,.fab,.fab-stack .fab,[data-float-panel]';

function emitTheme(cfg) {
  // cfg: { theme, materialId, activationClass, params, backdrop }
  const STATE = {
    background: cfg.background || '#0b0d12',
    backdrop: cfg.backdrop || 'aurora-gradient',
    bgImage: '',
    palette: ['#7cc7ff', '#b388ff', '#ff8ad1', '#7CF5C8', '#FFD75E'],
    material: Object.assign({ type: cfg.materialId }, BASE_PARAMS, cfg.params || {}),
  };
  const FRAG_SRC = GLSL_HEAD + '\n' + materialShade(cfg.materialId) + '\n' + GLSL_MAIN;
  const mod = `/* GENERATED from editor/tools/materiallab - verbatim ${cfg.materialId} runtime. Do not hand-edit. */
(function(){
"use strict";
var VS_SRC=${JSON.stringify(VS_SRC)};
var FRAG_SRC=${JSON.stringify(FRAG_SRC)};
var STATE=${JSON.stringify(STATE)};
${hexRGB}
${matToUniforms}
${drawBackdropInto}
${glassRuntime}
var THEME=${JSON.stringify(cfg.theme)};
var GLCLASS=${JSON.stringify(cfg.activationClass)};
var SURF=${JSON.stringify(SURF)};
var RT=null, canvas=null, raf=0;
function isOn(){ return document.documentElement.getAttribute("data-theme")===THEME; }
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
  canvas.id="__mat-canvas-"+THEME;
  canvas.style.cssText="position:fixed;inset:0;z-index:-1;pointer-events:none;display:block";
  document.body.appendChild(canvas);
  RT=glassRuntime({canvas:canvas,stage:stageProxy(),vsSrc:VS_SRC,panelSelector:SURF,
    getFragSrc:function(){return FRAG_SRC;},getUniforms:function(){return matToUniforms(STATE.material);},
    isFluid:function(){return false;},drawBackdrop:function(ctx,w,h){drawBackdropInto(ctx,w,h,STATE,null);},
    onError:function(m){ if(window.console)console.warn("["+THEME+"] "+m); teardown(); }});
  if(!RT){ if(canvas&&canvas.parentNode)canvas.parentNode.removeChild(canvas); canvas=null; return; }
  document.documentElement.classList.add(GLCLASS);
  window.addEventListener("resize",onResize,{passive:true});
  window.addEventListener("pointermove",onMove,{passive:true});
  loop();
}
function teardown(){
  if(raf){ cancelAnimationFrame(raf); raf=0; }
  window.removeEventListener("resize",onResize); window.removeEventListener("pointermove",onMove);
  if(RT && RT.dispose) RT.dispose(); RT=null;
  if(canvas && canvas.parentNode) canvas.parentNode.removeChild(canvas); canvas=null;
  document.documentElement.classList.remove(GLCLASS);
}
function sync(){ if(isOn()) mount(); else teardown(); }
try{ new MutationObserver(sync).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]}); }catch(e){}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",sync); else sync();
})();
`;
  const dest = path.join(__dirname, '..', '..', 'default-design-system', 'themes', cfg.theme + '.js');
  fs.writeFileSync(dest, mod);
  console.log('wrote', dest, '(' + mod.length + ' chars, material=' + cfg.materialId + ')');
}

// claymorphism → Material Lab "soft-ui-foam" (opaque light neumorphic emboss).
emitTheme({
  theme: 'claymorphism',
  materialId: 'soft-ui-foam',
  activationClass: 'clay-gl',
  background: '#e9eef5',
  backdrop: 'mono-soft',
  params: { colorA: '#e9eef5', alpha: 1.0 },
});
