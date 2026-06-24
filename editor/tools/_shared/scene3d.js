// =============================================================================
// scene3d.js - minimal self-contained 3D layer engine.
//
// Renders N points distributed on a parametric 3D surface (sphere / torus /
// wave grid), rotated in 3D (auto-spin + pointer orbit) and perspective-
// projected, depth-shaded, as a gl.POINTS cloud - so a layer reads as real 3D
// without a full mesh/lighting pipeline. Like pop.js it has NO vertex buffer:
// the vertex shader derives each point from gl_VertexID. Renders to an
// offscreen canvas the composer drawImage()s into a layer (Scene3DHost), so the
// per-layer effect / mask / blend stack composes on top.
//
// This is the "3D becomes a TOP layer" half of the 3D<->2D bridge, delivered as
// a standalone engine (there is no drivable window.__scene3d runtime to bridge).
//
// API:
//   const s = createScene3D();
//   s.available();                                 // false on a stub
//   s.step({ w, h, count, params, pointer, time }) -> canvas | null
//   s.dispose();
// params: shape ('sphere'|'torus'|'wave'), size, spin, r, g, b, blend.
// pointer: { x, y, down } in 0..1 (orbits the camera).
// =============================================================================

const S3D_VERT = `#version 300 es
precision highp float;
uniform float uCount, uShape, uTime, uYaw, uPitch, uSize, uAspect;
out float vDepth;
const float PI = 3.14159265359;

vec3 shapePos(float i, float n){
  if(uShape < 0.5){
    // Fibonacci sphere (even coverage).
    float phi = acos(1.0 - 2.0 * (i + 0.5) / n);
    float th = PI * (1.0 + sqrt(5.0)) * i;
    return vec3(sin(phi) * cos(th), cos(phi), sin(phi) * sin(th));
  } else if(uShape < 1.5){
    // Torus.
    float a = (i + 0.5) / n * PI * 2.0 * 7.0;
    float b = (i + 0.5) / n * PI * 2.0;
    float R = 0.7, r = 0.3;
    return vec3((R + r * cos(a)) * cos(b), r * sin(a), (R + r * cos(a)) * sin(b));
  }
  // Wave grid.
  float side = floor(sqrt(n));
  float gx = mod(i, side) / side - 0.5;
  float gz = floor(i / side) / side - 0.5;
  float y = 0.18 * sin(gx * 12.0 + uTime) * cos(gz * 12.0 + uTime * 0.8);
  return vec3(gx * 1.6, y, gz * 1.6);
}
vec3 rot(vec3 p, float yaw, float pitch){
  float cy = cos(yaw), sy = sin(yaw);
  p = vec3(cy * p.x + sy * p.z, p.y, -sy * p.x + cy * p.z);
  float cp = cos(pitch), sp = sin(pitch);
  p = vec3(p.x, cp * p.y - sp * p.z, sp * p.y + cp * p.z);
  return p;
}
void main(){
  vec3 p = shapePos(float(gl_VertexID), uCount);
  p = rot(p, uYaw, uPitch);
  p.z += 3.0;                       // push in front of the camera
  float f = 2.2;
  vec2 proj = vec2(p.x / uAspect, p.y) * f / p.z;
  gl_Position = vec4(proj, 0.0, 1.0);
  gl_PointSize = clamp(uSize * (3.0 / p.z), 1.0, 64.0);
  vDepth = clamp((p.z - 2.0) / 2.0, 0.0, 1.0);   // 0 near .. 1 far
}`;

const S3D_FRAG = `#version 300 es
precision highp float;
in float vDepth;
out vec4 o;
uniform vec3 uColor;
void main(){
  vec2 d = gl_PointCoord - 0.5;
  float r = length(d);
  if(r > 0.5) discard;
  float edge = smoothstep(0.5, 0.15, r);
  float shade = mix(1.0, 0.25, vDepth);          // near brighter than far
  float a = edge * shade;
  o = vec4(uColor * a, a);
}`;

function s3dCompile(gl, vsSrc, fsSrc){
  const vs = gl.createShader(gl.VERTEX_SHADER); gl.shaderSource(vs, vsSrc); gl.compileShader(vs);
  if(!gl.getShaderParameter(vs, gl.COMPILE_STATUS)){ console.warn('[scene3d] vert:', gl.getShaderInfoLog(vs)); return null; }
  const fs = gl.createShader(gl.FRAGMENT_SHADER); gl.shaderSource(fs, fsSrc); gl.compileShader(fs);
  if(!gl.getShaderParameter(fs, gl.COMPILE_STATUS)){ console.warn('[scene3d] frag:', gl.getShaderInfoLog(fs)); return null; }
  const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
  gl.deleteShader(vs); gl.deleteShader(fs);
  if(!gl.getProgramParameter(p, gl.LINK_STATUS)){ console.warn('[scene3d] link:', gl.getProgramInfoLog(p)); return null; }
  return p;
}
function s3dNum(v, d){ const n = Number(v); return Number.isFinite(n) ? n : d; }
function s3dRgb(hex){ hex = String(hex || '#9ad0ff').replace('#',''); if(hex.length === 3) hex = hex.split('').map(c=>c+c).join(''); const n = parseInt(hex, 16) || 0; return [((n>>16)&255)/255, ((n>>8)&255)/255, (n&255)/255]; }

export function createScene3D(){
  const canvas = (typeof OffscreenCanvas !== 'undefined')
    ? new OffscreenCanvas(2, 2)
    : (typeof document !== 'undefined' ? document.createElement('canvas') : null);
  if(!canvas) return s3dStub();
  const gl = canvas.getContext('webgl2', { premultipliedAlpha: false, alpha: true, antialias: true });
  if(!gl) return s3dStub();
  const prog = s3dCompile(gl, S3D_VERT, S3D_FRAG);
  if(!prog) return s3dStub();
  const U = {};
  const u = (name) => (name in U ? U[name] : (U[name] = gl.getUniformLocation(prog, name)));
  let cw = 2, ch = 2;
  let yaw = 0, pitch = 0;   // smoothed orbit state

  function step(o){
    o = o || {};
    const w = Math.max(2, o.w | 0), h = Math.max(2, o.h | 0);
    const count = Math.max(16, Math.min(200000, (o.count | 0) || 6000));
    const p = o.params || {};
    const ptr = o.pointer || {};
    const time = s3dNum(o.time, 0);
    const shape = p.shape === 'torus' ? 1 : p.shape === 'wave' ? 2 : 0;
    const rgb = s3dRgb(p.color);
    // auto-spin + damped pointer orbit
    const tgtYaw = time * s3dNum(p.spin, 0.3) + (s3dNum(ptr.x, 0.5) - 0.5) * 3.0;
    const tgtPitch = (s3dNum(ptr.y, 0.5) - 0.5) * 2.0;
    yaw += (tgtYaw - yaw) * 0.1; pitch += (tgtPitch - pitch) * 0.1;

    if(cw !== w || ch !== h){ canvas.width = w; canvas.height = h; cw = w; ch = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    gl.enable(gl.BLEND);
    if(p.blend === 'alpha') gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    else gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.uniform1f(u('uCount'), count);
    gl.uniform1f(u('uShape'), shape);
    gl.uniform1f(u('uTime'), time);
    gl.uniform1f(u('uYaw'), yaw);
    gl.uniform1f(u('uPitch'), pitch);
    gl.uniform1f(u('uSize'), Math.max(1, s3dNum(p.size, 3)));
    gl.uniform1f(u('uAspect'), w / h);
    gl.uniform3f(u('uColor'), rgb[0], rgb[1], rgb[2]);
    gl.drawArrays(gl.POINTS, 0, count);
    gl.disable(gl.BLEND);
    return canvas;
  }
  function dispose(){ try { gl.deleteProgram(prog); } catch(_e){} }
  return { step, dispose, available: () => true };
}

function s3dStub(){ return { step: () => null, dispose: () => {}, available: () => false }; }
