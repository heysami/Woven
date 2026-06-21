/* Glassmorphism theme runtime - OUR POC liquid glass, verbatim.
   Activates on <html data-theme="glassmorphism">. Mounts ONE full-viewport WebGL
   canvas behind the page, RASTERISES the page once (html2canvas) - the rule that
   lets a WebGL shader refract real DOM - and renders the POC glass shader into the
   rect of every STATIC chrome element (topbar / sidebar / modal / fab / float
   panel), refracting the captured page PANNED by scroll. Re-rasterises only when
   the DOM settles (debounced). Falls back to plain CSS glass if WebGL2 or
   html2canvas is unavailable. Hand-written - uses the EXACT pill-POC shader. */
(function(){
"use strict";
var DPR=Math.min(2, window.devicePixelRatio||1);

/* static surfaces the glass renders on (they don't move on scroll, so the fixed
   canvas glued to them has zero lag; scrolling content keeps the CSS fallback). */
/* SEMANTIC chrome list - which surfaces are glass. NOT gated on scroll: a child
   canvas tracks its host every frame (renderUnit reads getBoundingClientRect; the
   shader's uScroll cancels for elements that scroll with the page), so sticky AND
   scrolling chrome both render correctly. breadcrumb/page-head are deliberately
   excluded - they are content, not chrome. */
/* NB: .phone__status (the mobile status bar) is deliberately NOT glass - it reads
   as device chrome, not a glass surface, so it stays a plain bar (see glassmorphism.css). */
var SURF=".topbar,.sidebar,.appbar,.tabbar,.phone__tabbar,.modal,.slideout,.drawer,.fab,.fab-stack .fab,[data-float-panel],.toolbar,.rail,.style-switcher,.sh-top,.lp-nav";

/* OUR pill-POC presets, VERBATIM - light + dark (px values scaled by DPR where
   the shader expects px). The theme picks light/dark per the page's theme. */
var PRESETS={
  light:{bend:8, disp:4, frost:5.5,  bez:16, rad:24, tint:0.58, Lfloor:0.74, rim:0.22, caus:0.30, curve:1, veil:0.20, rimAngle:45},
  dark :{bend:8, disp:4, frost:3.25, bez:16, rad:24, tint:0.45, Lfloor:0.19, rim:0.66, caus:0.00, curve:1, veil:0.22, rimAngle:45}
};
/* The POC (tools/materiallab/_shader_pill_nav_poc.html) persists the user's tuned
   dials to localStorage['woven-lg-presets'] - and runs on the SAME origin as these
   templates, so the key is shared. Adopt whatever the user tuned there; the values
   above are only the fallback. This is why the DS glass == the user's POC default. */
try{ var _lg=JSON.parse(localStorage.getItem("woven-lg-presets")||"null");
  if(_lg){ if(_lg.light) for(var k in _lg.light) PRESETS.light[k]=_lg.light[k];
           if(_lg.dark)  for(var k2 in _lg.dark)  PRESETS.dark[k2]=_lg.dark[k2]; }
}catch(e){}

var VS="#version 300 es\n"+
"in vec2 p; out vec2 uv; void main(){ uv=p*0.5+0.5; gl_Position=vec4(p,0.,1.); }";
var FS="#version 300 es\n"+
"precision highp float; in vec2 uv; out vec4 o;\n"+
"uniform sampler2D uPage; uniform vec2 uPagePx,uCanvas,uCardTL; uniform float uScroll;\n"+
"uniform float uBend,uDisp,uFrost,uBez,uRad,uTint,uLfloor,uRim,uCaus,uCurve,uVeil,uDark,uRimMouse,uRimAngle;\n"+
"uniform vec2 uMouse; uniform vec3 uTintColor;\n"+
"float sd(vec2 p, vec2 b, float r){ vec2 q=abs(p)-b+r; return min(max(q.x,q.y),0.0)+length(max(q,0.0))-r; }\n"+
"vec2 nrm(vec2 p, vec2 b, float r){ float e=1.0;\n"+
"  return normalize(vec2(sd(p+vec2(e,0),b,r)-sd(p-vec2(e,0),b,r), sd(p+vec2(0,e),b,r)-sd(p-vec2(0,e),b,r))); }\n"+
"vec3 frostSample(vec2 px, float lod){\n"+
"  vec3 s=textureLod(uPage,px/uPagePx,lod).rgb;\n"+
"  float rad=max(lod,0.0)*1.7; const float GA=2.39996323;\n"+
"  for(int i=1;i<=16;i++){ float ang=GA*float(i);\n"+
"    vec2 q=vec2(cos(ang),sin(ang))*rad*sqrt(float(i)/16.0);\n"+
"    s+=textureLod(uPage,(px+q)/uPagePx,lod).rgb; }\n"+
"  return s/17.0;\n"+
"}\n"+
"void main(){\n"+
"  vec2 frag=vec2(uv.x*uCanvas.x,(1.0-uv.y)*uCanvas.y);\n"+
"  vec2 p=frag-uCanvas*0.5;\n"+
"  vec2 b=uCanvas*0.5-vec2(6.0);\n"+
"  float r=min(uRad, min(b.x,b.y));\n"+
"  float d=sd(p,b,r);\n"+
"  if(d>0.5){ o=vec4(0.0); return; }\n"+
"  vec2 n=nrm(p,b,r);\n"+
"  float into=clamp(-d,0.0,uBez);\n"+
"  float u=1.0-into/uBez;\n"+
"  u=pow(clamp(u,0.0,1.0), uCurve);\n"+
"  vec2 docPx=vec2(uCardTL.x+frag.x, uCardTL.y+frag.y+uScroll);\n"+
"  float fold=sin(3.14159265*u), crunch=pow(u,3.0);\n"+
"  float bend=fold*uBend + crunch*uBend*1.4;\n"+
"  vec2 dir=-n;\n"+
"  float lod=mix(uFrost*0.7, uFrost, smoothstep(0.0,1.0,u));\n"+
"  float disp=(fold*0.5+crunch)*uDisp;\n"+
"  vec3 col;\n"+
"  col.r=frostSample(docPx+dir*(bend+disp),lod).r;\n"+
"  col.g=frostSample(docPx+dir*(bend),      lod).g;\n"+
"  col.b=frostSample(docPx+dir*(bend-disp),lod).b;\n"+
"  vec3 veilCol = (uDark>0.5) ? vec3(0.04,0.05,0.07) : vec3(0.99,1.0,1.0);\n"+   // glass stays WHITE/neutral - not scheme-tinted (accents carry the colour)
"  col=mix(col, veilCol, uVeil);\n"+
"  float V=max(max(col.r,col.g),col.b);\n"+
"  float Vn = (uDark>0.5) ? min(V, uLfloor) : mix(uLfloor, 1.0, V);\n"+
"  col*=Vn/max(V,1e-4);\n"+
"  float lit;\n"+
"  if(uRimMouse>0.5){\n"+
"    float sig=max(uCanvas.x,uCanvas.y)*0.13;\n"+
"    float md=distance(frag, uMouse);\n"+
"    lit=exp(-md*md/(2.0*sig*sig));\n"+
"  } else {\n"+
"    vec2 Ld=vec2(cos(radians(uRimAngle)),sin(radians(uRimAngle)));\n"+
"    lit=pow(max(dot(n,Ld),0.0),2.0)+pow(max(dot(n,-Ld),0.0),2.0);\n"+
"  }\n"+
"  col+=smoothstep(0.94,1.0,u)*uRim*lit;\n"+
"  float rim=smoothstep(0.72,1.0,u);\n"+
"  float hue=fract(atan(n.y,n.x)/6.2831);\n"+
"  col+=(0.55+0.5*cos(6.2831*(hue+vec3(0.0,0.33,0.67))))*rim*uCaus;\n"+
"  o=vec4(clamp(col,0.0,1.0),1.0);\n"+
"}";

var MAX_UNITS=14;                 // WebGL context budget (browsers cap ~16)
var units=[], byEl=new WeakMap(); // one GL canvas per chrome element
var pageCap=null, pageCapW=0, pageCapH=0, capturing=false, capTimer=0, mo=null, raf=0, mounted=false, mouse=[-9999,-9999];

function isOn(){ return document.documentElement.getAttribute("data-theme")==="glassmorphism"; }

/* Follow the SELECTED COLOUR SCHEME + light/dark, read from live DS tokens so it
   adapts however the scheme is applied (data-theme, class, or injected roles):
   --primary-surface drives the glass tint; the luminance of --surface decides
   light vs dark (→ which preset + light/dark chrome text via the .lg-dark class). */
var gBrand=[0.03,0.31,0.81], gDark=false;
function parseColor(s){
  s=(s||"").trim(); if(!s) return null;
  var h=s.match(/^#([0-9a-fA-F]{6})$/);
  if(h){ var n=parseInt(h[1],16); return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255]; }
  var r=s.match(/rgba?\(([^)]+)\)/); if(r){ var p=r[1].split(","); return [(+p[0])/255,(+p[1])/255,(+p[2])/255]; }
  return null;
}
function readScheme(){
  /* read the RAW ramp tokens, which glassmorphism.css does NOT hijack (it does
     override the semantic roles --surface/--fg-default/--primary-surface to its own
     iOS-blue light palette). --primary-500 = the scheme's brand; --neutral-50 flips
     light↔dark (light #F7F7F7 → dark #2B2E33) so its luminance tells us the mode. */
  var cs=getComputedStyle(document.documentElement);
  var b=parseColor(cs.getPropertyValue("--primary-500")); if(b) gBrand=b;
  var n=parseColor(cs.getPropertyValue("--neutral-50"));
  if(n){ var lum=0.2126*n[0]+0.7152*n[1]+0.0722*n[2]; gDark=lum<0.5; }
  document.documentElement.classList.toggle("lg-dark", gDark);
}
function isDark(){ return gDark; }

function sh(gl,t,src){ var oo=gl.createShader(t); gl.shaderSource(oo,src); gl.compileShader(oo);
  if(!gl.getShaderParameter(oo,gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(oo)); return oo; }

function uploadToUnit(u,cv){
  var gl=u.gl; gl.bindTexture(gl.TEXTURE_2D,u.tex); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,cv);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  u.texReady=true;
}
/* The rasterise rule needs html2canvas. The editor already loads html2canvas-pro
   (index.html); standalone template pages don't - so lazy-load the SAME CDN build
   on demand. No-op when it's already present. */
var h2cLoading=false;
function ensureH2C(cb){
  if(window.html2canvas){ cb&&cb(); return; }
  if(h2cLoading) return;
  h2cLoading=true;
  var s=document.createElement("script");
  s.src="https://unpkg.com/html2canvas-pro@1.5.8/dist/html2canvas-pro.min.js";
  s.onload=function(){ h2cLoading=false; cb&&cb(); };
  s.onerror=function(){ h2cLoading=false; if(window.console)console.warn("[glassmorphism] html2canvas load failed"); };
  (document.head||document.documentElement).appendChild(s);
}
/* RASTERISE RULE: capture the page ONCE (and on settle). We IGNORE the glass hosts
   themselves so the texture is the clean content the chrome sits over (the POC
   captures content WITHOUT its pill) - the glass refracts that, panned by scroll. */
function capturePage(){
  if(capturing||!document.body) return;
  if(!window.html2canvas){ ensureH2C(capturePage); return; }
  var bg=getComputedStyle(document.body).backgroundColor||"#F4F6FB";
  var de=document.documentElement, bd=document.body;
  var docW=Math.max(de.scrollWidth, bd.scrollWidth, 1);
  var docH=Math.max(de.scrollHeight, bd.scrollHeight, 1);
  /* The capture is one WebGL texture, so it must fit MAX_TEXTURE_SIZE. A very long
     page (the gallery is ~31000px tall) at scale=DPR blows past ~8192/16384 → the
     texImage2D upload silently fails and the shader samples a broken/grey texture.
     Cap the capture scale to fit; uPagePx still uses the LOGICAL device size
     (docCSS*DPR) so the device-px coords the shader samples normalise correctly
     regardless of the texture's real (smaller) resolution. */
  var maxTex=8192; if(units.length){ try{ maxTex=Math.min(maxTex, units[0].gl.getParameter(units[0].gl.MAX_TEXTURE_SIZE)); }catch(e){} }
  var sc=Math.min(DPR, maxTex/docW, maxTex/docH);
  capturing=true;
  try{
    /* Hide the glass chrome in the CLONE via visibility:hidden - NOT ignoreElements.
       ignoreElements DELETES the element from the clone, so the rest of the layout
       reflows and the texture no longer lines up with on-screen positions. */
    window.html2canvas(document.body,{backgroundColor:bg,scale:sc,logging:false,useCORS:true,allowTaint:false,
      onclone:function(doc){ var h=doc.querySelectorAll(".lg-host"); for(var i=0;i<h.length;i++){ try{h[i].style.visibility="hidden";}catch(e){} } }})
      .then(function(cv){ pageCap=cv; pageCapW=docW*DPR; pageCapH=docH*DPR; for(var i=0;i<units.length;i++){ try{uploadToUnit(units[i],cv);}catch(e){} } capturing=false; })
      .catch(function(){ capturing=false; });
  }catch(e){ capturing=false; }
}
function scheduleCap(){ clearTimeout(capTimer); capTimer=setTimeout(capturePage, 400); }

/* Glass only on chrome that is VISIBLE (templates ship hidden modals that still lay
   out) and does NOT scroll away (fixed/sticky, or inside one) - the rasterise-once-
   pan-by-scroll trick only holds for non-scrolling surfaces. */
function visible(e,b){
  var cs=getComputedStyle(e);
  if(cs.display==="none" || cs.visibility==="hidden" || parseFloat(cs.opacity||"1")<0.05) return false;
  if(b.right<=0 || b.bottom<=0 || b.left>=innerWidth || b.top>=innerHeight) return false;
  return true;
}
function nonScrolling(e){
  for(var n=e; n && n!==document.body && n!==document.documentElement; n=n.parentElement){
    var ps=getComputedStyle(n).position;
    if(ps==="fixed" || ps==="sticky") return true;
  }
  return false;
}
function targets(){
  var out=[], els=document.querySelectorAll(SURF);
  for(var i=0;i<els.length && out.length<MAX_UNITS;i++){ var e=els[i], b=e.getBoundingClientRect();
    if(b.width>1 && b.height>1 && visible(e,b)) out.push(e); }   // no scroll gate - SURF is the filter
  return out;
}

/* POC architecture: a WebGL canvas injected as a CHILD of the chrome element,
   absolute inset:0, so the glass IS that element's surface; the host's own content
   sits above it (CSS lifts it to z-index:1). */
function makeUnit(el){
  if(byEl.has(el)) return byEl.get(el);
  var canvas=document.createElement("canvas"); canvas.className="lg-canvas";
  /* positioning set INLINE, not only via glassmorphism.css: a <canvas> defaults to
     display:inline with its BUFFER as intrinsic size. If the CSS rule is stale in
     cache / not yet applied, the canvas sits IN FLOW at its buffer height, growing
     the host → renderUnit grows the buffer → runaway to the browser 2^24 max-height
     (saw shTop height = 16777216). Inline absolute makes it out-of-flow always. */
  canvas.style.cssText="position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;display:block;border-radius:inherit";
  var gl=canvas.getContext("webgl2",{alpha:true,premultipliedAlpha:false});
  if(!gl){ byEl.set(el,false); return null; }   // record failure so syncUnits won't retry-storm
  var prog,U={},buf,tex;
  try{
    prog=gl.createProgram(); gl.attachShader(prog,sh(gl,gl.VERTEX_SHADER,VS)); gl.attachShader(prog,sh(gl,gl.FRAGMENT_SHADER,FS));
    gl.linkProgram(prog); if(!gl.getProgramParameter(prog,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  }catch(e){ if(window.console)console.warn("[glassmorphism] "+e.message); byEl.set(el,false); return null; }
  gl.useProgram(prog);
  buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
  tex=gl.createTexture();
  ["uPage","uPagePx","uCanvas","uCardTL","uScroll","uBend","uDisp","uFrost","uBez","uRad","uTint","uLfloor","uRim","uCaus","uCurve","uVeil","uDark","uRimMouse","uRimAngle","uMouse","uTintColor"]
    .forEach(function(k){ U[k]=gl.getUniformLocation(prog,k); });
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  /* the absolute canvas needs a positioned host - but only force it when the host is
     STATIC. If it is sticky/fixed/relative/absolute, leave it (clobbering sticky =
     the bar scrolls away). */
  var cs0=getComputedStyle(el);
  if(cs0.position==="static") el.style.position="relative";
  el.classList.add("lg-host");
  el.insertBefore(canvas, el.firstChild);
  /* lift STATIC children above the canvas without disturbing already-positioned ones
     (an absolute decorative wave must STAY absolute, or it drops into flow and pushes
     the nav off-screen). CSS gives them z-index:1; relative makes z-index apply. */
  for(var ci=0;ci<el.children.length;ci++){ var ch=el.children[ci];
    if(ch===canvas) continue;
    if(getComputedStyle(ch).position==="static") ch.style.position="relative"; }
  var rad=parseFloat(cs0.borderTopLeftRadius)||0;
  var u={el:el,canvas:canvas,gl:gl,prog:prog,buf:buf,tex:tex,U:U,rad:rad,texReady:false,w:0,h:0};
  if(pageCap){ try{uploadToUnit(u,pageCap);}catch(e){} }
  byEl.set(el,u); units.push(u);
  return u;
}
function destroyUnit(u){
  try{ var lo=u.gl.getExtension("WEBGL_lose_context"); if(lo)lo.loseContext(); }catch(e){}
  if(u.canvas.parentNode) u.canvas.parentNode.removeChild(u.canvas);
  u.el.classList.remove("lg-host"); byEl.delete(u.el);
}
function syncUnits(){
  if(!isOn()) return;
  /* STABLE lifecycle - the #1 cause of the glass "blinking" against the CSS panel:
     adding .lg-host changes the host's layout, which can make targets() momentarily
     re-judge the element invalid; destroying on that transient flip removes .lg-host,
     the element becomes valid again, recreate, destroy… an infinite blink. So a unit
     is ONLY torn down when its element actually leaves the DOM - never on a transient
     visibility/rect change. targets() gates CREATION only. */
  for(var j=units.length-1;j>=0;j--){ if(!units[j].el.isConnected){ destroyUnit(units[j]); units.splice(j,1); } }
  var want=targets();
  for(var k=0;k<want.length;k++){ if(!byEl.has(want[k])) makeUnit(want[k]); }
}

function renderUnit(u){
  if(!u.texReady||!pageCap) return;
  var gl=u.gl, el=u.el, rc=el.getBoundingClientRect();
  if(rc.width<1||rc.height<1) return;
  var cw=Math.min(16384,Math.max(1,Math.round(rc.width*DPR))), ch=Math.min(16384,Math.max(1,Math.round(rc.height*DPR)));  // clamp: never let a stray rect explode the buffer
  if(u.w!==cw||u.h!==ch){ u.canvas.width=cw; u.canvas.height=ch; u.w=cw; u.h=ch;
    u.rad=parseFloat(getComputedStyle(el).borderTopLeftRadius)||0; }
  gl.viewport(0,0,cw,ch); gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.useProgram(u.prog);
  gl.bindBuffer(gl.ARRAY_BUFFER,u.buf); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,u.tex); gl.uniform1i(u.U.uPage,0);
  gl.uniform2f(u.U.uPagePx, pageCapW, pageCapH);   // LOGICAL device size, not the (possibly down-scaled) texture px
  /* Pan the captured backdrop by the TOTAL scroll under this host: window scroll
     PLUS every scrollable ancestor (e.g. the mobile .phone__screen). The texture is
     captured once; scrolling just samples it at a shifted offset, so a bar over an
     inner scroll container refracts the content moving behind it without re-capture. */
  var sY = window.scrollY||0;
  for(var an=el.parentElement; an && an!==document.body && an!==document.documentElement; an=an.parentElement){ if(an.scrollTop) sY += an.scrollTop; }
  gl.uniform1f(u.U.uScroll, sY*DPR);
  gl.uniform2f(u.U.uCanvas, cw, ch);
  gl.uniform2f(u.U.uCardTL, rc.left*DPR, rc.top*DPR);
  var dark=isDark()?1:0, P=dark?PRESETS.dark:PRESETS.light;
  var rad=u.rad>0.5 ? u.rad : P.rad;   // match the element's own corner radius
  gl.uniform1f(u.U.uBend,P.bend*DPR); gl.uniform1f(u.U.uDisp,P.disp*DPR); gl.uniform1f(u.U.uFrost,P.frost);
  gl.uniform1f(u.U.uBez,P.bez*DPR); gl.uniform1f(u.U.uRad,rad*DPR); gl.uniform1f(u.U.uTint,P.tint); gl.uniform1f(u.U.uLfloor,P.Lfloor);
  gl.uniform1f(u.U.uRim,P.rim); gl.uniform1f(u.U.uCaus,P.caus); gl.uniform1f(u.U.uCurve,P.curve); gl.uniform1f(u.U.uVeil,P.veil);
  gl.uniform1f(u.U.uDark,dark); gl.uniform1f(u.U.uRimMouse,0); gl.uniform1f(u.U.uRimAngle,P.rimAngle);
  gl.uniform2f(u.U.uMouse,(mouse[0]-rc.left)*DPR,(mouse[1]-rc.top)*DPR);
  gl.uniform3f(u.U.uTintColor, gBrand[0],gBrand[1],gBrand[2]);   // tint follows the selected scheme
  gl.drawArrays(gl.TRIANGLES,0,3);
}
var schemeTick=0;
function frame(){
  raf=requestAnimationFrame(frame);
  if((schemeTick++ % 12)===0) readScheme();   // pick up scheme / dark-mode changes (throttled)
  for(var i=0;i<units.length;i++) renderUnit(units[i]);
}

var syncTimer=0;
function scheduleSync(){ clearTimeout(syncTimer); syncTimer=setTimeout(syncUnits, 200); }
function onResize(){ syncUnits(); scheduleCap(); }
function onScroll(){ /* sticky hosts hold their rect; renderUnit reads rc + per-unit scroll each frame */ }
function onMove(e){ mouse=[e.clientX*DPR, e.clientY*DPR]; }

function mount(){
  if(mounted || !document.body) return;
  mounted=true;
  readScheme();
  document.documentElement.classList.add("glass-gl");
  window.addEventListener("resize",onResize,{passive:true});
  window.addEventListener("pointermove",onMove,{passive:true});
  window.addEventListener("scroll",onScroll,{passive:true});
  /* observe ONLY to discover new/removed chrome (debounced syncUnits). We do NOT
     re-capture on mutation - html2canvas adds + removes its own clone nodes while
     capturing, which would re-trigger capture forever and hang the page. */
  try{ mo=new MutationObserver(scheduleSync); mo.observe(document.body,{childList:true,subtree:true}); }catch(e){}
  syncUnits();
  frame();
  setTimeout(capturePage, 300);    // initial rasterise
  setTimeout(capturePage, 1400);   // one retry after late content/fonts settle
}
function teardown(){
  if(!mounted) return; mounted=false;
  if(raf){ cancelAnimationFrame(raf); raf=0; }
  if(capTimer){ clearTimeout(capTimer); capTimer=0; }
  if(mo){ try{mo.disconnect();}catch(e){} mo=null; }
  window.removeEventListener("resize",onResize); window.removeEventListener("pointermove",onMove); window.removeEventListener("scroll",onScroll);
  for(var i=units.length-1;i>=0;i--){ destroyUnit(units[i]); } units=[]; byEl=new WeakMap(); pageCap=null;
  document.documentElement.classList.remove("glass-gl");
}
function sync(){ if(isOn()) mount(); else teardown(); }
try{ new MutationObserver(sync).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]}); }catch(e){}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",sync); else sync();
})();
