/* GENERATED from editor/tools/materiallab — verbatim soft-ui-foam runtime. Do not hand-edit. */
(function(){
"use strict";
var VS_SRC="#version 300 es\nlayout(location=0) in vec2 aPos;\nvoid main(){ gl_Position = vec4(aPos, 0.0, 1.0); }";
var FRAG_SRC="#version 300 es\nprecision highp float;\n\n/* ---- scene ---- */\nuniform sampler2D uBackdrop;   // the scene rendered behind the glass\nuniform vec2  uRes;            // canvas size in device px\nuniform vec2  uLight;          // light / pointer position in device px (top-left origin)\nuniform float uTime;           // seconds\n\n/* ---- panel geometry (one rounded rect per .mat element) ---- */\n#define MAXP 24\nuniform int   uCount;\nuniform vec4  uRect[MAXP];     // x, y, w, h  (device px, top-left origin)\nuniform float uRadius[MAXP];   // corner radius (device px)\n\n/* ---- material (every dial below is a REAL optical control) ---- */\nuniform float uIOR;       // index of refraction (1.0 = none, glass ~1.5)\nuniform float uThick;     // glass thickness -> refraction displacement strength (px)\nuniform float uBezel;     // bezel width as a fraction of the panel half-extent (0..1)\nuniform int   uProfile;   // bezel shape: 0 convex  1 concave  2 lip  3 squircle\nuniform float uDisp;      // chromatic dispersion (per-channel IOR spread)\nuniform float uFrost;     // frosted blur amount\nuniform float uSpec;      // specular highlight strength\nuniform float uShine;     // specular tightness (shininess exponent)\nuniform float uFresnel;   // edge fresnel rim strength\nuniform vec3  uTint;      // glass tint colour\nuniform float uTintAmt;   // tint strength\nuniform float uAlpha;     // glass fill opacity (1 = solid, <1 = see-through)\nuniform int   uHolo;      // 1 = iridescent / holographic sheen\n\n/* ---- generic material params (used by the non-glass surfaces) ---- */\nuniform vec3  uColorA;     // primary material colour\nuniform vec3  uColorB;     // secondary material colour\nuniform float uScale;      // pattern / weave / texture frequency\nuniform float uRough;      // micro-surface roughness\nuniform float uAnis;       // anisotropy strength\nuniform float uGlow;       // emissive strength\n\n/* ---- interaction / simulation feed ---- */\nuniform vec2  uMouseVel;   // pointer velocity this frame (device px/frame)\nuniform sampler2D uState;  // ping-pong simulation state (fluid materials only)\nuniform int   uHasState;   // 1 when uState holds a live sim texture\n\nout vec4 frag;\n\n/* signed distance to a rounded rectangle (p relative to rect centre) */\nfloat sdRound(vec2 p, vec2 b, float r){\n  vec2 q = abs(p) - b + r;\n  return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;\n}\n\n/* height of the bezel surface at normalised edge distance t (0 rim -> 1 flat top),\n   returning height h and its slope dh/dt used to tilt the surface normal. */\nvoid profile(int kind, float t, out float h, out float slope){\n  if(kind == 1){                 // concave — dish curving down toward the rim\n    float x = 1.0 - t;\n    h = 1.0 - sqrt(max(0.0, 1.0 - x*x));\n    slope = -x / max(0.001, sqrt(max(0.0,1.0 - x*x)));\n  } else if(kind == 2){          // lip — raised rounded rim then flat\n    float rim = exp(-pow((t - 0.18) / 0.12, 2.0));\n    h = 1.0 - rim * 0.6;\n    slope = (t < 0.18 ? 1.0 : -1.0) * rim * 3.0;\n  } else if(kind == 3){          // squircle — Apple-style smooth shoulder\n    h = smoothstep(0.0, 1.0, t);\n    slope = (1.0 - abs(2.0*t - 1.0)) * 1.6;\n  } else {                       // convex — spherical cap (default liquid glass)\n    float x = 1.0 - t;\n    h = sqrt(max(0.0, 1.0 - x*x));\n    slope = x / max(0.001, h);\n  }\n}\n\n/* ---- general helpers shared by every material's shade() ---- */\nfloat hash21(vec2 p){ p = fract(p * vec2(123.34, 345.45)); p += dot(p, p + 34.345); return fract(p.x * p.y); }\nfloat vnoise(vec2 p){\n  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);\n  float a = hash21(i), b = hash21(i + vec2(1.0,0.0)), c = hash21(i + vec2(0.0,1.0)), d = hash21(i + vec2(1.0,1.0));\n  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);\n}\nfloat fbm(vec2 p){ float s = 0.0, a = 0.5; for(int i = 0; i < 5; i++){ s += a * vnoise(p); p *= 2.02; a *= 0.5; } return s; }\nvec3  pal(float t){ return 0.5 + 0.5 * cos(6.28318 * (t + vec3(0.0, 0.33, 0.66))); }\nconst float BAYER[16] = float[16](0.,8.,2.,10., 12.,4.,14.,6., 3.,11.,1.,9., 15.,7.,13.,5.);\n\n/* per-pixel surface context handed to every material's shade() */\nstruct Ctx {\n  vec2  uv;     // 0..1 screen uv (top-left origin)\n  vec2  fc;     // device-px coordinate\n  vec2  pos;    // local position within the panel, -1..1 on each axis\n  float t;      // 0 at the rim -> 1 on the flat interior\n  float edge;   // px distance in from the rim\n  vec3  N;      // bezel surface normal\n  vec3  V;      // view direction\n  vec3  L;      // light direction (mouse-driven)\n  float fres;   // fresnel term (rim-weighted)\n  vec2  refr;   // base refraction uv offset through the bezel\n  vec2  grad;   // outward 2D gradient of the rounded rect\n  float aspect; // panel width / height\n  vec3  H;      // half-vector (light + view), normalised\n  float rim;    // 1 at the rim -> 0 across the flat interior (highlight mask)\n  float spec;   // Blinn-Phong term off the bezel normal (uShine exponent)\n  vec4  flow;   // sampled fluid state (rg = velocity, b = dye, a = pressure)\n};\n\n/* Edge-confined specular: keeps the hot highlight riding the rounded bezel\n   instead of blooming a readability-killing blob across the flat top where the\n   UI text sits. Every surface routes its sheen through this so presets stay\n   legible by construction. */\nfloat bezelSpec(Ctx c){ return c.spec * c.rim; }\n\n/* sample the refracted backdrop with per-channel dispersion + optional frost */\nvec3 sampleRefract(Ctx c){\n  vec2 uv = c.uv, off = c.refr;\n  vec2 oR = off * (1.0 + uDisp), oG = off, oB = off * (1.0 - uDisp);\n  if(uFrost > 0.001){\n    float rad = uFrost * 0.02; vec3 acc = vec3(0.0);\n    for(int k = -2; k <= 2; k++){\n      vec2 j = vec2(float(k)) * (rad / 4.0);\n      acc.r += texture(uBackdrop, uv + oR + j).r;\n      acc.g += texture(uBackdrop, uv + oG + j.yx).g;\n      acc.b += texture(uBackdrop, uv + oB + j).b;\n    }\n    return acc / 5.0;\n  }\n  return vec3(texture(uBackdrop, uv + oR).r, texture(uBackdrop, uv + oG).g, texture(uBackdrop, uv + oB).b);\n}\nvec4 shade(Ctx c){\n  vec3 base = uColorA;\n  float lt = dot(normalize(c.N), normalize(vec3(-0.5,-0.5,1.0)));\n  vec3 col = base + lt*0.12;                                     // neumorphic dual emboss\n  col = mix(col, base, c.t*0.5);\n  return vec4(col, 1.0);\n}\nvoid main(){\n  // pixel in top-left-origin device space (matches the backdrop texture + uRect)\n  vec2 fc = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);\n  vec2 uv = fc / uRes;\n\n  // find the innermost panel containing this pixel (smallest area wins -> nested\n  // surfaces like buttons-on-a-card sit above the larger surface)\n  int   hit = -1;\n  float bestArea = 1e20, dHit = 0.0, rHit = 0.0;\n  vec2  cHit = vec2(0.0), bHit = vec2(0.0);\n  for(int i = 0; i < MAXP; i++){\n    if(i >= uCount) break;\n    vec4 R = uRect[i];\n    vec2 c = R.xy + R.zw * 0.5;\n    vec2 b = R.zw * 0.5;\n    float d = sdRound(fc - c, b, uRadius[i]);\n    if(d < 0.0){\n      float area = R.z * R.w;\n      if(area < bestArea){ bestArea = area; hit = i; dHit = d; cHit = c; bHit = b; rHit = uRadius[i]; }\n    }\n  }\n  if(hit < 0){ frag = vec4(0.0); return; }   // outside all panels -> show real backdrop\n\n  // normalised distance in from the rim, scaled by the bezel width (in px)\n  float edgePx  = -dHit;\n  float bezelPx = max(3.0, uBezel * min(bHit.x, bHit.y));\n  float t = clamp(edgePx / bezelPx, 0.0, 1.0);\n\n  float h, slope; profile(uProfile, t, h, slope);\n\n  // outward 2D normal of the rounded rect via SDF central difference\n  float dx = sdRound((fc + vec2(1.0,0.0)) - cHit, bHit, rHit) - sdRound((fc - vec2(1.0,0.0)) - cHit, bHit, rHit);\n  float dy = sdRound((fc + vec2(0.0,1.0)) - cHit, bHit, rHit) - sdRound((fc - vec2(0.0,1.0)) - cHit, bHit, rHit);\n  vec2  grad = normalize(vec2(dx, dy) + 1e-6);   // points outward from the surface\n  float bend = (1.0 - t);                        // tilt is strongest at the rim\n  vec3  N = normalize(vec3(grad * slope * bend, 1.0));\n  vec3  V = vec3(0.0, 0.0, 1.0);                 // viewer looks straight on\n\n  // base refraction through the bezel (Snell's law via the GLSL refract intrinsic)\n  float eta  = 1.0 / max(1.0001, uIOR);\n  vec3  Rdir = refract(-V, N, eta);\n  vec2  off  = Rdir.xy * (uThick / uRes.y);      // lateral displacement in uv\n\n  vec3  L = normalize(vec3((uLight - fc) / uRes.y, 0.55));\n  vec3  H = normalize(L + V);\n\n  Ctx c;\n  c.uv = uv; c.fc = fc; c.pos = (fc - cHit) / max(bHit, vec2(1.0));\n  c.t = t; c.edge = edgePx; c.N = N; c.V = V; c.L = L;\n  c.fres = pow(1.0 - N.z, 3.0); c.refr = off; c.grad = grad;\n  c.aspect = bHit.x / max(1.0, bHit.y);\n  c.H = H;\n  // rim: hot at the bezel, ~0 across the flat interior. Squared falloff keeps\n  // the readable centre genuinely calm rather than just dimmer.\n  c.rim = pow(1.0 - t, 2.0);\n  c.spec = pow(max(dot(N, H), 0.0), max(1.0, uShine));\n  if(uHasState == 1){ vec4 st = texture(uState, uv); c.flow = vec4(st.rg*2.0-1.0, st.b, st.a); }\n  else c.flow = vec4(0.0);\n\n  frag = shade(c);\n}";
var STATE={"background":"#e9eef5","backdrop":"mono-soft","bgImage":"","palette":["#7cc7ff","#b388ff","#ff8ad1","#7CF5C8","#FFD75E"],"material":{"type":"soft-ui-foam","profile":"convex","ior":1.5,"thickness":38,"bezel":0.45,"dispersion":0.18,"frost":0,"specular":0.7,"shininess":80,"fresnel":0.5,"tint":"#ffffff","tintAmt":0,"alpha":1,"holo":false,"colorA":"#e9eef5","colorB":"#1a1f27","scale":22,"rough":0.5,"anis":0.6,"glow":1}};
function hexRGB(hex){
  hex=(hex||'#ffffff').replace('#','');
  if(hex.length===3) hex=hex.split('').map(c=>c+c).join('');
  if(hex.length>=6) return [parseInt(hex.slice(0,2),16)||0,parseInt(hex.slice(2,4),16)||0,parseInt(hex.slice(4,6),16)||0];
  return [255,255,255];
}
function matToUniforms(m){
  const c = hexRGB(m.tint||'#ffffff'), a = hexRGB(m.colorA||'#cccccc'), b = hexRGB(m.colorB||'#222222');
  const prof = {convex:0,concave:1,lip:2,squircle:3}[m.profile] || 0;
  return {
    ior:+m.ior, thick:+m.thickness, bezel:+m.bezel, profile:prof, disp:+m.dispersion,
    frost:+m.frost, spec:+m.specular, shine:+m.shininess, fresnel:+m.fresnel,
    tint:[c[0]/255,c[1]/255,c[2]/255], tintAmt:+m.tintAmt, alpha:+m.alpha, holo:m.holo?1:0,
    colorA:[a[0]/255,a[1]/255,a[2]/255], colorB:[b[0]/255,b[1]/255,b[2]/255],
    scale:+m.scale, rough:+m.rough, anis:+m.anis, glow:+m.glow,
  };
}
function drawBackdropInto(ctx,w,h,state,img){
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle = state.background || '#0b0d12';
  ctx.fillRect(0,0,w,h);
  let stops;
  if(state.backdrop==='aurora-gradient') stops=[{x:.2,y:.15,r:.7,c:'#2a4cffcc'},{x:.85,y:.2,r:.6,c:'#b34cffbb'},{x:.6,y:1,r:.8,c:'#16d6b4bb'}];
  else if(state.backdrop==='mesh-warm')  stops=[{x:.15,y:.2,r:.7,c:'#ff8a3dcc'},{x:.9,y:.3,r:.6,c:'#ff4d7dcc'},{x:.5,y:1.1,r:.8,c:'#6d3bffbb'}];
  else if(state.backdrop==='mono-soft')  stops=[{x:.3,y:.2,r:.7,c:'#ffffff2a'},{x:.8,y:.8,r:.6,c:'#ffffff18'}];
  else                                   stops=[{x:.5,y:-.1,r:1.1,c:'#2a2f3acc'}];
  stops.forEach(g=>{
    const rg=ctx.createRadialGradient(g.x*w,g.y*h,0,g.x*w,g.y*h,g.r*Math.max(w,h));
    rg.addColorStop(0,g.c); rg.addColorStop(1,'transparent');
    ctx.fillStyle=rg; ctx.fillRect(0,0,w,h);
  });
  if(img && img.complete && img.naturalWidth){
    const ir=img.naturalWidth/img.naturalHeight, cr=w/h; let dw,dh;
    if(ir>cr){ dh=h; dw=h*ir; } else { dw=w; dh=w/ir; }
    ctx.globalAlpha=0.92; ctx.drawImage(img,(w-dw)/2,(h-dh)/2,dw,dh); ctx.globalAlpha=1;
  }
}
function glassRuntime(opts){
  const canvas = opts.canvas, stage = opts.stage;
  const sel = opts.panelSelector || '.mat';
  const gl = canvas.getContext('webgl2', {alpha:true, premultipliedAlpha:false, antialias:true});
  if(!gl){ if(opts.onError) opts.onError('WebGL2 not available'); return null; }

  let prog=null, lastGoodFrag='';
  let buf=null, tex=null;
  const texCv=document.createElement('canvas'); const texCtx=texCv.getContext('2d',{willReadFrequently:false});
  let panels=[];                          // [x,y,w,h,r] in device px
  let dpr=Math.min(2, window.devicePixelRatio||1);
  let light=[0,0];
  let lightPrev=[0,0], lightVel=[0,0];    // pointer velocity (css px/frame), for fluid + reactive metals
  let running=true; const t0=performance.now();
  let backdropDirty=true;

  /* ---- interactive fluid: a ping-pong velocity+dye field advected each frame.
     Only allocated when a fluid material is active (opts.isFluid()). State is
     packed into RGBA8 (vel = rg*2-1, dye = b) so it runs without float-buffer
     extensions. The pointer injects force + dye, so the field genuinely flows
     where the mouse drags rather than playing a canned animation. ---- */
  const FLUID_FRAG =
    '#version 300 es\nprecision highp float;\n'+
    'uniform sampler2D uPrev; uniform vec2 uRes; uniform vec2 uMouse; uniform vec2 uMouseVel; out vec4 o;\n'+
    'void main(){ vec2 uv=gl_FragCoord.xy/uRes; vec2 px=1.0/uRes; vec4 s=texture(uPrev,uv);\n'+
    '  vec2 vel=s.rg*2.0-1.0; vec2 src=uv - vel*px*6.0; vec4 a=texture(uPrev,src); vel=a.rg*2.0-1.0; float dye=a.b;\n'+
    '  vec4 n=texture(uPrev,uv+vec2(0.0,px.y)),so=texture(uPrev,uv-vec2(0.0,px.y)),e=texture(uPrev,uv+vec2(px.x,0.0)),w=texture(uPrev,uv-vec2(px.x,0.0));\n'+
    '  vec2 avgV=((n.rg+so.rg+e.rg+w.rg)*0.25)*2.0-1.0; vel=mix(vel,avgV,0.14); dye=mix(dye,(n.b+so.b+e.b+w.b)*0.25,0.12);\n'+
    '  float d=length((uv-uMouse)*vec2(uRes.x/uRes.y,1.0)); float fall=exp(-d*d*90.0);\n'+
    '  vel+=uMouseVel*fall*40.0; dye+=fall*min(length(uMouseVel)*120.0,1.0);\n'+
    '  vel*=0.972; dye*=0.984; vel=clamp(vel,-1.0,1.0); o=vec4(vel*0.5+0.5,clamp(dye,0.0,1.0),1.0); }\n';
  let simProg=null, simA=null, simB=null, simFA=null, simFB=null, simW=0, simH=0, simReady=false;
  function ensureFluid(){
    if(simReady) return true;
    try{
      simProg = buildProgram(FLUID_FRAG);
      simW = Math.max(64, Math.round(canvas.width/2)); simH = Math.max(64, Math.round(canvas.height/2));
      const mk=()=>{ const t=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,t);
        gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,simW,simH,0,gl.RGBA,gl.UNSIGNED_BYTE, new Uint8Array(simW*simH*4).fill(128));
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); return t; };
      const mkfb=t=>{ const f=gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER,f); gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,t,0); return f; };
      // zero-velocity, zero-dye initial state: rg=128 (->0 vel), b=0 (->no dye)
      const init=new Uint8Array(simW*simH*4); for(let i=0;i<simW*simH;i++){ init[i*4]=128; init[i*4+1]=128; init[i*4+2]=0; init[i*4+3]=255; }
      simA=mk(); gl.bindTexture(gl.TEXTURE_2D,simA); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,simW,simH,0,gl.RGBA,gl.UNSIGNED_BYTE,init);
      simB=mk(); gl.bindTexture(gl.TEXTURE_2D,simB); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,simW,simH,0,gl.RGBA,gl.UNSIGNED_BYTE,init);
      simFA=mkfb(simA); simFB=mkfb(simB);
      gl.bindFramebuffer(gl.FRAMEBUFFER,null);
      simReady=true; return true;
    }catch(e){ if(opts.onError) opts.onError('fluid init: '+(e.message||e)); simReady=false; return false; }
  }
  function stepFluid(){
    // render sim into simB sampling simA, then swap
    gl.useProgram(simProg);
    gl.bindFramebuffer(gl.FRAMEBUFFER,simFB); gl.viewport(0,0,simW,simH);
    gl.bindBuffer(gl.ARRAY_BUFFER,buf); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
    const su=n=>gl.getUniformLocation(simProg,n);
    gl.uniform2f(su('uRes'),simW,simH);
    const cw=Math.max(1,stage.clientWidth), ch=Math.max(1,stage.clientHeight);
    gl.uniform2f(su('uMouse'), light[0]/cw, light[1]/ch);
    gl.uniform2f(su('uMouseVel'), lightVel[0]/cw, lightVel[1]/ch);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D,simA); gl.uniform1i(su('uPrev'),1);
    gl.drawArrays(gl.TRIANGLES,0,3);
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);
    const tA=simA,fA=simFA; simA=simB; simFA=simFB; simB=tA; simFB=fA;   // swap (display reads simA)
  }

  function compileShader(type,src){
    const s=gl.createShader(type); gl.shaderSource(s,src); gl.compileShader(s);
    if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){
      const log=gl.getShaderInfoLog(s); gl.deleteShader(s); throw new Error(log||'shader compile failed');
    }
    return s;
  }
  function buildProgram(fragSrc){
    const vs=compileShader(gl.VERTEX_SHADER, opts.vsSrc);
    const fs=compileShader(gl.FRAGMENT_SHADER, fragSrc);
    const p=gl.createProgram(); gl.attachShader(p,vs); gl.attachShader(p,fs);
    gl.bindAttribLocation(p,0,'aPos'); gl.linkProgram(p);
    gl.deleteShader(vs); gl.deleteShader(fs);
    if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
      const log=gl.getProgramInfoLog(p); gl.deleteProgram(p); throw new Error(log||'program link failed');
    }
    return p;
  }
  function setFrag(src){
    try{ const p=buildProgram(src); if(prog) gl.deleteProgram(prog); prog=p; lastGoodFrag=src; return null; }
    catch(e){ return String(e.message||e); }
  }

  function resize(){
    const w=Math.max(2,Math.round(stage.clientWidth*dpr)), h=Math.max(2,Math.round(stage.clientHeight*dpr));
    if(canvas.width!==w||canvas.height!==h){ canvas.width=w; canvas.height=h; }
    canvas.style.width=stage.clientWidth+'px'; canvas.style.height=stage.clientHeight+'px';
    backdropDirty=true; measure();
  }
  function measure(){
    const sr=stage.getBoundingClientRect();
    const els=stage.querySelectorAll(sel);
    const out=[];
    els.forEach(el=>{
      const r=el.getBoundingClientRect();
      if(r.width<2||r.height<2) return;
      let rad=parseFloat(getComputedStyle(el).borderTopLeftRadius)||0;
      const x=r.left-sr.left, y=r.top-sr.top, w=r.width, h=r.height;
      rad=Math.min(rad, Math.min(w,h)/2);
      out.push([x*dpr, y*dpr, w*dpr, h*dpr, rad*dpr]);
    });
    panels = out.slice(0,24);
  }
  function updateBackdrop(){
    const w=canvas.width, h=canvas.height;
    if(texCv.width!==w||texCv.height!==h){ texCv.width=w; texCv.height=h; }
    opts.drawBackdrop(texCtx,w,h);
    if(!tex) tex=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,texCv);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    backdropDirty=false;
  }

  const rects=new Float32Array(24*4), rads=new Float32Array(24);
  function frame(){
    if(!running) return;
    requestAnimationFrame(frame);
    if(!prog) return;
    if(backdropDirty) updateBackdrop();
    // pointer velocity (decays toward zero when the mouse is still)
    lightVel[0]=light[0]-lightPrev[0]; lightVel[1]=light[1]-lightPrev[1];
    lightPrev[0]=light[0]; lightPrev[1]=light[1];
    // advance the fluid field (only if the active material requested it)
    const fluid = opts.isFluid && opts.isFluid();
    if(fluid && ensureFluid()) stepFluid();
    gl.viewport(0,0,canvas.width,canvas.height);
    gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER,buf); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
    const u=name=>gl.getUniformLocation(prog,name);
    const U=opts.getUniforms();
    gl.uniform2f(u('uRes'),canvas.width,canvas.height);
    gl.uniform1f(u('uTime'),(performance.now()-t0)/1000);
    gl.uniform2f(u('uLight'),light[0]*dpr,light[1]*dpr);
    gl.uniform1i(u('uCount'),panels.length);
    for(let i=0;i<panels.length;i++){ rects[i*4]=panels[i][0]; rects[i*4+1]=panels[i][1]; rects[i*4+2]=panels[i][2]; rects[i*4+3]=panels[i][3]; rads[i]=panels[i][4]; }
    gl.uniform4fv(u('uRect'),rects); gl.uniform1fv(u('uRadius'),rads);
    gl.uniform1f(u('uIOR'),U.ior); gl.uniform1f(u('uThick'),U.thick); gl.uniform1f(u('uBezel'),U.bezel);
    gl.uniform1i(u('uProfile'),U.profile); gl.uniform1f(u('uDisp'),U.disp); gl.uniform1f(u('uFrost'),U.frost);
    gl.uniform1f(u('uSpec'),U.spec); gl.uniform1f(u('uShine'),U.shine); gl.uniform1f(u('uFresnel'),U.fresnel);
    gl.uniform3f(u('uTint'),U.tint[0],U.tint[1],U.tint[2]); gl.uniform1f(u('uTintAmt'),U.tintAmt);
    gl.uniform1f(u('uAlpha'),U.alpha); gl.uniform1i(u('uHolo'),U.holo);
    gl.uniform3f(u('uColorA'),U.colorA[0],U.colorA[1],U.colorA[2]); gl.uniform3f(u('uColorB'),U.colorB[0],U.colorB[1],U.colorB[2]);
    gl.uniform1f(u('uScale'),U.scale); gl.uniform1f(u('uRough'),U.rough); gl.uniform1f(u('uAnis'),U.anis); gl.uniform1f(u('uGlow'),U.glow);
    gl.uniform2f(u('uMouseVel'), lightVel[0]*dpr, lightVel[1]*dpr);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,tex); gl.uniform1i(u('uBackdrop'),0);
    if(fluid && simReady){ gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D,simA); gl.uniform1i(u('uState'),2); gl.uniform1i(u('uHasState'),1); }
    else { gl.uniform1i(u('uHasState'),0); }
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.drawArrays(gl.TRIANGLES,0,3);
  }

  // init
  buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1, 3,-1, -1,3]),gl.STATIC_DRAW);
  const initErr=setFrag(opts.getFragSrc());
  if(initErr && opts.onError) opts.onError(initErr);
  resize();
  requestAnimationFrame(frame);

  return {
    setFrag,
    lastGoodFrag:()=>lastGoodFrag,
    setLight:(x,y)=>{ light[0]=x; light[1]=y; },
    refreshBackdrop:()=>{ backdropDirty=true; },
    remeasure:measure,
    resize,
    dispose:()=>{ running=false; },
  };
}
var THEME="claymorphism";
var GLCLASS="clay-gl";
var SURF=".card,.section-card,.stat-hero,.chart-card,.modal,.slideout,.btn--primary,.btn--outline,.input,.select,.textarea,.badge,.tag,.kpi,.metric-tile,.topbar,.sidebar,.phone__tabbar";
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
