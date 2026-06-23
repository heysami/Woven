// =============================================================================
// pop.js - minimal GPU particle (POP) engine.
//
// Per-particle position + velocity live in float textures (a texW x texH grid =
// texW*texH particles). Each frame two fullscreen fragment passes integrate the
// sim (velocity then position, ping-ponged - no MRT needed), and a gl.POINTS
// draw renders them: the vertex shader has NO vertex buffer, it derives each
// particle's texel from gl_VertexID and texelFetch()es its position. The result
// is rendered to an offscreen canvas the composer drawImage()s into a layer,
// exactly like the camera / sketch content kinds.
//
// Self-contained WebGL2 context. Float render targets are required; if the GPU
// can't render to RGBA16F the engine reports unavailable and the caller skips it
// (the layer simply shows nothing) - a clean degrade, never a crash.
//
// API:
//   const pop = createPOPEngine();
//   pop.available();                 // false on a stub (no WebGL2 / no float)
//   pop.step(id, { w, h, count, params, pointer, dt, time }) -> canvas | null
//   pop.disposeInstance(id);         // free one layer's buffers
//   pop.dispose();                   // free everything
//
// params (all optional, sensible defaults): size, gravityX, gravityY, noise,
//   drag, attract, life, r, g, b, blend ('add' | 'alpha').
// pointer: { x, y, down } in 0..1 stage space.
// =============================================================================

const POP_VERT_QUAD = `#version 300 es
precision highp float;
layout(location = 0) in vec2 aPos;
out vec2 vUv;
void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

const POP_GLSL_LIB = `
float popHash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float popNoise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  float a = popHash(i), b = popHash(i + vec2(1.0,0.0)), c = popHash(i + vec2(0.0,1.0)), d = popHash(i + vec2(1.0,1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}`;

const POP_SIM_HEADER = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 o;
uniform sampler2D uPos;   // xy = position (0..1), z = age, w = life
uniform sampler2D uVel;   // xy = velocity
uniform float uDt;
uniform float uTime;
uniform vec2  uPointer;
uniform float uDown;
uniform vec2  uGravity;
uniform float uNoise;
uniform float uDrag;
uniform float uAttract;
uniform float uSeed;
` + POP_GLSL_LIB;

// Velocity integration: curl-ish noise + gravity + pointer attraction, with drag.
const POP_FRAG_VEL = POP_SIM_HEADER + `
void main(){
  vec2 v = texture(uVel, vUv).xy;
  vec4 p = texture(uPos, vUv);
  vec2 np = p.xy * 3.0 + uTime * 0.2;
  vec2 curl = vec2(popNoise(np + vec2(5.2, 1.3)) - 0.5, -(popNoise(np) - 0.5)) * uNoise;
  vec2 attr = (uPointer - p.xy) * uAttract * uDown;
  v += (uGravity + curl + attr) * uDt;
  v *= (1.0 - clamp(uDrag, 0.0, 1.0) * uDt * 10.0);
  o = vec4(v, 0.0, 1.0);
}`;

// Position integration: advance, age, respawn aged-out / off-screen particles.
const POP_FRAG_POS = POP_SIM_HEADER + `
void main(){
  vec4 p = texture(uPos, vUv);
  vec2 v = texture(uVel, vUv).xy;
  float age = p.z + uDt;
  float life = p.w > 0.0 ? p.w : 1.0;
  vec2 pos = p.xy + v * uDt;
  if(age > life || pos.x < -0.1 || pos.x > 1.1 || pos.y < -0.1 || pos.y > 1.1){
    vec2 scatter = vec2(popHash(vUv + uSeed), popHash(vUv.yx + uSeed + 0.7));
    pos = mix(scatter, uPointer, uDown);
    age = 0.0;
  }
  o = vec4(pos, age, life);
}`;

// First-frame seed: random positions, zero velocity, random life around the mean.
const POP_FRAG_SEED_POS = POP_SIM_HEADER + `
void main(){
  vec2 pos = vec2(popHash(vUv + uSeed), popHash(vUv.yx + uSeed + 0.7));
  float life = uDrag; // reuse uDrag uniform slot to carry mean life at seed time
  o = vec4(pos, popHash(vUv + 3.1) * life, life);
}`;

const POP_FRAG_SEED_VEL = `#version 300 es
precision highp float;
out vec4 o;
void main(){ o = vec4(0.0, 0.0, 0.0, 1.0); }`;

// Points render: no vertex buffer; gl_VertexID -> texel -> position.
const POP_VERT_POINTS = `#version 300 es
precision highp float;
uniform sampler2D uPos;
uniform int uTexW;
uniform float uSize;
out float vLife;
void main(){
  int id = gl_VertexID;
  ivec2 t = ivec2(id % uTexW, id / uTexW);
  vec4 p = texelFetch(uPos, t, 0);
  vec2 cl = p.xy * 2.0 - 1.0;
  cl.y = -cl.y;
  gl_Position = vec4(cl, 0.0, 1.0);
  gl_PointSize = uSize;
  vLife = (p.w > 0.0) ? clamp(1.0 - p.z / p.w, 0.0, 1.0) : 1.0;
}`;

const POP_FRAG_POINTS = `#version 300 es
precision highp float;
in float vLife;
out vec4 o;
uniform vec3 uColor;
void main(){
  vec2 d = gl_PointCoord - 0.5;
  float r = length(d);
  if(r > 0.5) discard;
  float a = smoothstep(0.5, 0.15, r) * vLife;
  o = vec4(uColor * a, a);
}`;

function popCompile(gl, vsSrc, fsSrc){
  const vs = gl.createShader(gl.VERTEX_SHADER); gl.shaderSource(vs, vsSrc); gl.compileShader(vs);
  if(!gl.getShaderParameter(vs, gl.COMPILE_STATUS)){ console.warn('[pop] vert:', gl.getShaderInfoLog(vs)); return null; }
  const fs = gl.createShader(gl.FRAGMENT_SHADER); gl.shaderSource(fs, fsSrc); gl.compileShader(fs);
  if(!gl.getShaderParameter(fs, gl.COMPILE_STATUS)){ console.warn('[pop] frag:', gl.getShaderInfoLog(fs)); return null; }
  const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs);
  gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p);
  gl.deleteShader(vs); gl.deleteShader(fs);
  if(!gl.getProgramParameter(p, gl.LINK_STATUS)){ console.warn('[pop] link:', gl.getProgramInfoLog(p)); return null; }
  return { p, u: {} };
}

function popNum(v, d){ const n = Number(v); return Number.isFinite(n) ? n : d; }

export function createPOPEngine(){
  const canvas = (typeof OffscreenCanvas !== 'undefined')
    ? new OffscreenCanvas(2, 2)
    : (typeof document !== 'undefined' ? document.createElement('canvas') : null);
  if(!canvas) return popStub();
  const gl = canvas.getContext('webgl2', { premultipliedAlpha: false, alpha: true, antialias: false });
  if(!gl) return popStub();
  gl.getExtension('EXT_color_buffer_float');
  if(!popProbeFloat(gl)) return popStub();

  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);

  const progVel = popCompile(gl, POP_VERT_QUAD, POP_FRAG_VEL);
  const progPos = popCompile(gl, POP_VERT_QUAD, POP_FRAG_POS);
  const seedPos = popCompile(gl, POP_VERT_QUAD, POP_FRAG_SEED_POS);
  const seedVel = popCompile(gl, POP_VERT_QUAD, POP_FRAG_SEED_VEL);
  const progDraw = popCompile(gl, POP_VERT_POINTS, POP_FRAG_POINTS);
  if(!progVel || !progPos || !seedPos || !seedVel || !progDraw) return popStub();

  const insts = {};
  let cw = 2, ch = 2;

  function uloc(entry, name){
    if(name in entry.u) return entry.u[name];
    const l = gl.getUniformLocation(entry.p, name); entry.u[name] = l; return l;
  }
  function makeTex(channels){
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return { tex, channels };
  }
  function ensureInst(id, count){
    const texW = Math.max(2, Math.ceil(Math.sqrt(count)));
    const texH = texW;
    let inst = insts[id];
    if(inst && inst.texW === texW) return inst;
    if(inst) freeInst(inst);
    const alloc = () => {
      const a = makeTex(4), b = makeTex(4);
      for(const t of [a, b]){
        gl.bindTexture(gl.TEXTURE_2D, t.tex);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, texW, texH, 0, gl.RGBA, gl.HALF_FLOAT, null);
      }
      return { a, b, cur: 0 };
    };
    inst = { texW, texH, count: texW * texH, pos: alloc(), vel: alloc(), fbo: gl.createFramebuffer(), frame: 0, seed: (id.length % 97) / 97 + 0.01 };
    insts[id] = inst;
    return inst;
  }
  function freeInst(inst){
    for(const set of [inst.pos, inst.vel]){ gl.deleteTexture(set.a.tex); gl.deleteTexture(set.b.tex); }
    gl.deleteFramebuffer(inst.fbo);
  }
  function rd(set){ return set.cur === 0 ? set.a : set.b; }
  function wr(set){ return set.cur === 0 ? set.b : set.a; }
  function swap(set){ set.cur = 1 - set.cur; }

  // Run one fullscreen sim pass into `dstTex`, sampling uPos/uVel from the read sides.
  function simPass(prog, dstTex, inst, setU){
    gl.bindFramebuffer(gl.FRAMEBUFFER, inst.fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, dstTex.tex, 0);
    gl.viewport(0, 0, inst.texW, inst.texH);
    gl.useProgram(prog.p);
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, rd(inst.pos).tex); gl.uniform1i(uloc(prog, 'uPos'), 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, rd(inst.vel).tex); gl.uniform1i(uloc(prog, 'uVel'), 1);
    if(setU) setU(prog);
    gl.disable(gl.BLEND);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.activeTexture(gl.TEXTURE0);
  }

  function step(id, o){
    o = o || {};
    const w = Math.max(2, o.w | 0), h = Math.max(2, o.h | 0);
    const count = Math.max(4, Math.min(262144, (o.count | 0) || 4096));
    const p = o.params || {};
    const ptr = o.pointer || {};
    const dt = Math.min(0.05, Math.max(0.0001, popNum(o.dt, 1 / 60)));
    const time = popNum(o.time, 0);
    const life = Math.max(0.2, popNum(p.life, 3));
    const inst = ensureInst(id, count);

    const common = (prog) => {
      gl.uniform1f(uloc(prog, 'uDt'), dt);
      gl.uniform1f(uloc(prog, 'uTime'), time);
      gl.uniform2f(uloc(prog, 'uPointer'), Math.min(1, Math.max(0, popNum(ptr.x, 0.5))), Math.min(1, Math.max(0, popNum(ptr.y, 0.5))));
      gl.uniform1f(uloc(prog, 'uDown'), ptr.down ? 1 : 0);
      gl.uniform2f(uloc(prog, 'uGravity'), popNum(p.gravityX, 0), popNum(p.gravityY, 0));
      gl.uniform1f(uloc(prog, 'uNoise'), popNum(p.noise, 0.4));
      gl.uniform1f(uloc(prog, 'uDrag'), popNum(p.drag, 0.1));
      gl.uniform1f(uloc(prog, 'uAttract'), popNum(p.attract, 0));
      gl.uniform1f(uloc(prog, 'uSeed'), inst.seed);
    };

    if(inst.frame === 0){
      simPass(seedPos, wr(inst.pos), inst, (prog) => { gl.uniform1f(uloc(prog, 'uSeed'), inst.seed); gl.uniform1f(uloc(prog, 'uDrag'), life); }); swap(inst.pos);
      simPass(seedVel, wr(inst.vel), inst, null); swap(inst.vel);
    }
    simPass(progVel, wr(inst.vel), inst, common); swap(inst.vel);
    simPass(progPos, wr(inst.pos), inst, (prog) => { common(prog); }); swap(inst.pos);
    inst.frame++;

    // Render the points to the output canvas at the layer resolution.
    if(cw !== w || ch !== h){ canvas.width = w; canvas.height = h; cw = w; ch = h; }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(progDraw.p);
    gl.disableVertexAttribArray(0);
    gl.enable(gl.BLEND);
    if(p.blend === 'alpha') gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    else gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, rd(inst.pos).tex); gl.uniform1i(uloc(progDraw, 'uPos'), 0);
    gl.uniform1i(uloc(progDraw, 'uTexW'), inst.texW);
    gl.uniform1f(uloc(progDraw, 'uSize'), Math.max(1, popNum(p.size, 2)));
    gl.uniform3f(uloc(progDraw, 'uColor'), popNum(p.r, 0.55), popNum(p.g, 0.85), popNum(p.b, 1));
    gl.drawArrays(gl.POINTS, 0, inst.count);
    gl.disable(gl.BLEND);
    return canvas;
  }

  function disposeInstance(id){ if(insts[id]){ freeInst(insts[id]); delete insts[id]; } }
  function dispose(){ for(const id in insts) freeInst(insts[id]); }
  return { step, disposeInstance, dispose, available: () => true };
}

function popProbeFloat(gl){
  try {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, 4, 4, 0, gl.RGBA, gl.HALF_FLOAT, null);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.deleteFramebuffer(fbo); gl.deleteTexture(tex);
    return ok;
  } catch(_e){ return false; }
}

function popStub(){
  return { step: () => null, disposeInstance: () => {}, dispose: () => {}, available: () => false };
}
