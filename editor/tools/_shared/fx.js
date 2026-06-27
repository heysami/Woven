// fx.js - Shared GPU effect catalog for the Woven editor (shader-lab taxonomy).
// =============================================================================
// Self-contained WebGL2 effects module. No build, no deps, raw WebGL2.
//
// API
// ---
//   import { createFXChain, FX_TYPES } from './fx.js';
//   const chain = createFXChain();
//   const canvas = chain.apply(source, effects);          // -> HTMLCanvasElement
//   const imgData = chain.applyToImageData(source, effects); // -> ImageData
//   chain.resize(w, h);   // pre-size (apply() also auto-sizes from source)
//   chain.setTime(t);     // seconds, for time-based effects (uTime uniform)
//   chain.dispose();      // free all GL resources
//
// Stateful, multi-pass effects (NEW - additive, separate from apply())
// --------------------------------------------------------------------
// apply()/applyToImageData() above are STATELESS: every effect is one fullscreen
// pass and the two ping-pong FBOs are transient (reused, never read across
// frames). Some effects (a Stam fluid solver, feedback trails, GPU particles)
// need PERSISTENT per-instance state that survives across frames. The stateful
// subsystem adds that without touching the stateless path:
//
//   const out = chain.stepStateful(instanceId, type, {
//     params,                 // effect controls (same shape as `effects[].params`)
//     intensity,              // 0..1 mix amount for the display pass
//     source,                 // the layer's rendered pixels (canvas/img/ImageData)
//     pointer:{x,y,dx,dy,down,hover}, // normalised 0..1 pointer + per-frame delta
//     dt,                     // seconds since last step (clamped internally)
//     time,                   // seconds (uTime)
//     iterations,             // solver iteration count override (e.g. pressure xN)
//     target,                 // optional 2D canvas to draw the result into
//   }) -> HTMLCanvasElement (a fresh 2D canvas, like apply()) or `target` if given.
//
//   chain.disposeStateful(instanceId);   // free THAT instance's persistent buffers
//   chain.hasStateful(type);             // is `type` a registered stateful effect?
//   chain.statefulAvailable();           // false on the stub / when WebGL2 absent
//
// Each stateful instance owns a set of PERSISTENT textures (single or ping-pong
// pairs) keyed by instanceId (the caller's layer id) and sized to the source.
// They are lazily created on first stepStateful(instanceId,...), resized when the
// source size changes, and freed by disposeStateful(instanceId) (or dispose(),
// which frees them all). The subsystem is GENERIC: a stateful effect definition
// declares its N persistent textures + an ordered pass list, so feedback and
// particle systems can adopt the same path later. Float textures (RGBA16F via
// EXT_color_buffer_float) are used when available, falling back to RGBA8.
//
// Registered stateful types today: 'fluid' (GPU Stam stable-fluids - see
// STATEFUL_EFFECTS below). The stub chain (no WebGL2) returns null from
// stepStateful so the caller can fall back to a CPU implementation.
//
//   `source` may be an HTMLCanvasElement, HTMLImageElement, ImageBitmap,
//   HTMLVideoElement, ImageData, or an OffscreenCanvas. width/height are read
//   from the source.
//
//   `effects` is an ordered array of specs:
//     { type, intensity = 1, params = {}, glsl }
//   Each effect is a fullscreen fragment pass. Passes ping-pong through two
//   FBOs so an arbitrary chain composes. Every pass receives:
//     sampler2D uTex     - previous pass result (or the source for pass 0)
//     vec2      uResolution
//     float     uTime    - seconds (see setTime)
//     float     uIntensity - 0..1 (mix amount; 0 == passthrough)
//     vec2      vUv       - 0..1 fragment uv
//   plus per-effect uniforms derived from `params` (see each effect below).
//
// intensity: every built-in pass ends with mix(src, fx, uIntensity), so
//   intensity 0 is an exact passthrough of that pass's input.
//
// Robustness: unknown type -> passthrough (skipped). Empty effects -> the
//   source is returned unchanged (cheap path, no GL work). A `custom` pass
//   whose GLSL fails to compile is skipped with console.warn (never throws).
//
// Effect types (FX_TYPES)
// -----------------------
//   distortion: chromatic-aberration, directional-blur, displacement, slice
//   pixel:      pixelate, dither, posterize, pixel-sort
//   artistic:   ascii, crt, halftone, ink, edge-detect
//   generative: particle-grid, pattern
//   custom:     glsl-string fragment body
//
// =============================================================================

export const FX_TYPES = [
  // distortion
  'chromatic-aberration', 'directional-blur', 'displacement', 'displace-by', 'slice',
  'transform', 'lens-distort',
  // pixel
  'pixelate', 'dither', 'posterize', 'pixel-sort',
  // color / filter
  'color', 'tonemap', 'convolve',
  // artistic
  'ascii', 'crt', 'halftone', 'ink', 'edge-detect',
  // generative
  'particle-grid', 'pattern',
  // multi-input (read a SECOND layer: displace/composite/key/grade)
  'blend', 'matte', 'lookup',
  // frame-history (read the per-layer ring of recent frames)
  'row-delay', 'cache-select', 'optical-flow',
  // illustrative-shader SOURCES (procedural generative fills; ignore uTex)
  'mesh-gradient', 'fractal-noise', 'clouds', 'nebula', 'glowing-wave', 'neuro-noise',
  'godrays', 'water-caustics', 'particle-web', 'magnetic-field', 'metaball-merge',
  'moire-interference', 'concentric-patterns', 'dither-waves',
  // illustrative-shader FILTERS (transform the layer beneath)
  'gradient-map', 'color-outline', 'channel-mixer', 'hatching', 'pattern-refraction',
  'chromatic-metal', 'bokeh-blur', 'riso-print',
  // escape hatch
  'custom',
];

// Human labels for each type (UI pickers, building-block node templates).
export const FX_LABELS = {
  'chromatic-aberration': 'Chromatic aberration',
  'directional-blur': 'Directional blur',
  'displacement': 'Displacement',
  'displace-by': 'Displace by layer',
  'transform': 'Transform',
  'lens-distort': 'Lens distort',
  'color': 'Color grade',
  'tonemap': 'Tone map',
  'convolve': 'Convolve',
  'slice': 'Slice',
  'pixelate': 'Pixelate',
  'dither': 'Dither',
  'posterize': 'Posterize',
  'pixel-sort': 'Pixel sort',
  'ascii': 'ASCII',
  'crt': 'CRT scanline',
  'halftone': 'Halftone',
  'ink': 'Ink',
  'edge-detect': 'Edge detect',
  'particle-grid': 'Particle grid',
  'pattern': 'Pattern',
  'blend': 'Blend layers',
  'matte': 'Matte (key by layer)',
  'lookup': 'Color lookup (LUT)',
  'row-delay': 'Row delay (rolling shutter)',
  'cache-select': 'Echo (frame delay)',
  'optical-flow': 'Optical flow',
  // illustrative-shader sources
  'mesh-gradient': 'Mesh gradient',
  'fractal-noise': 'Fractal noise',
  'clouds': 'Clouds',
  'nebula': 'Nebula',
  'glowing-wave': 'Glowing wave',
  'neuro-noise': 'Neuro noise',
  'godrays': 'Godrays',
  'water-caustics': 'Water caustics',
  'particle-web': 'Particle web',
  'magnetic-field': 'Magnetic field',
  'metaball-merge': 'Metaball merge',
  'moire-interference': 'Moire interference',
  'concentric-patterns': 'Concentric patterns',
  'dither-waves': 'Dither waves',
  // illustrative-shader filters
  'gradient-map': 'Gradient map',
  'color-outline': 'Color outline',
  'channel-mixer': 'Channel mixer',
  'hatching': 'Hatching',
  'pattern-refraction': 'Pattern refraction',
  'chromatic-metal': 'Chromatic metal',
  'bokeh-blur': 'Bokeh blur',
  'riso-print': 'Riso print',
  'custom': 'Custom shader',
};

// Effects that read a per-layer FRAME-HISTORY RING (a TEXTURE_2D_ARRAY of recent
// source frames) via `uniform sampler2DArray uHistory` + uHistDepth + uHistHead.
// The host (GLFx + the baked slimPlayer) allocates one ring per layer, pushes the
// layer's source frame each tick, and binds it for these types. Depth = max
// supported delay (60 frames) + 1 live slice. Baked into EFFECT_SPECS via the
// `history` flag in fxProgramSpecs() so the standalone twin needs no import.
export const FX_HISTORY_TYPES = new Set(['row-delay', 'cache-select', 'optical-flow']);
export const FX_HISTORY_DEPTH = 61;

// ---------------------------------------------------------------------------
// Shared GLSL
// ---------------------------------------------------------------------------

const VERT = `#version 300 es
precision highp float;
layout(location = 0) in vec2 aPos;
out vec2 vUv;
void main() {
  vUv = aPos * 0.5 + 0.5;
  gl_Position = vec4(aPos, 0.0, 1.0);
}`;

const FRAG_HEADER = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 fragColor;
uniform sampler2D uTex;
uniform vec2 uResolution;
uniform float uTime;
uniform float uIntensity;
`;

// Small helpers injected into every built-in fragment.
const GLSL_LIB = `
float fxLuma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
float fxHash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}
// value noise
float fxNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = fxHash(i);
  float b = fxHash(i + vec2(1.0, 0.0));
  float c = fxHash(i + vec2(0.0, 1.0));
  float d = fxHash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
// fractal brownian motion (4 octaves of value noise)
float fxFbm(vec2 p) {
  float v = 0.0, amp = 0.5;
  for (int i = 0; i < 4; i++) { v += amp * fxNoise(p); p *= 2.0; amp *= 0.5; }
  return v;
}
// RGB<->HSV (hue in 0..1) and ACES filmic tonemap - shared by color/tonemap effects.
vec3 fxRgb2Hsv(vec3 c) {
  vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
  vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
  vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
  float d = q.x - min(q.w, q.y);
  float e = 1.0e-10;
  return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
vec3 fxHsv2Rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
vec3 fxAces(vec3 x) {
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}
`;

// Per-effect fragment bodies. Each defines `vec4 fxMain()` returning the full
// effect color; the host wrapper mixes it with the untouched src by uIntensity.
const EFFECTS = {

  // ---- distortion --------------------------------------------------------
  'chromatic-aberration': {
    uniforms: { uAmount: { k: '1f', from: 'amount', def: 0.01 }, uAngle: { k: '1f', from: 'angle', def: 0.0 } },
    decls: 'uniform float uAmount; uniform float uAngle;',
    body: `
vec4 fxMain() {
  vec2 dir = vec2(cos(uAngle), sin(uAngle));
  vec2 off = dir * uAmount;
  float r = texture(uTex, vUv + off).r;
  float g = texture(uTex, vUv).g;
  float b = texture(uTex, vUv - off).b;
  float a = texture(uTex, vUv).a;
  return vec4(r, g, b, a);
}`,
  },

  'directional-blur': {
    uniforms: { uAngle: { k: '1f', from: 'angle', def: 0.0 }, uLength: { k: '1f', from: 'length', def: 0.02 } },
    decls: 'uniform float uAngle; uniform float uLength;',
    body: `
vec4 fxMain() {
  vec2 dir = vec2(cos(uAngle), sin(uAngle)) * uLength;
  vec4 sum = vec4(0.0);
  const int N = 9;
  for (int i = 0; i < N; i++) {
    float t = float(i) / float(N - 1) - 0.5;
    sum += texture(uTex, vUv + dir * t);
  }
  return sum / float(N);
}`,
  },

  'displacement': {
    uniforms: { uScale: { k: '1f', from: 'scale', def: 0.03 } },
    decls: 'uniform float uScale;',
    body: `
vec4 fxMain() {
  vec2 p = vUv * 6.0 + uTime * 0.3;
  float nx = fxNoise(p) - 0.5;
  float ny = fxNoise(p + vec2(31.7, 19.3)) - 0.5;
  return texture(uTex, vUv + vec2(nx, ny) * uScale);
}`,
  },

  // Multi-input: warp uTex by a SECOND layer's pixels (the displacement map).
  // `inputs` declares the extra sampler(s) this effect needs; the host binds the
  // wired layer's buffer to `uMap` at a texture unit > 0 (see GLFx.blit). The
  // map's R,G channels are read as a signed offset (0.5 = no shift).
  'displace-by': {
    inputs: [{ name: 'uMap', label: 'Displacement map' }],
    uniforms: { uAmount: { k: '1f', from: 'amount', def: 0.05 } },
    decls: 'uniform sampler2D uMap; uniform float uAmount;',
    body: `
vec4 fxMain() {
  vec2 off = (texture(uMap, vUv).rg - 0.5) * uAmount;
  return texture(uTex, vUv + off);
}`,
  },

  // Composite this layer (uTex) with a SECOND layer (uSrcB) in a chosen mode.
  'blend': {
    inputs: [{ name: 'uSrcB', label: 'Blend layer' }],
    uniforms: { uMode: { k: '1i', from: 'mode', def: 0 } },
    decls: 'uniform sampler2D uSrcB; uniform int uMode;',
    body: `
vec4 fxMain() {
  vec4 a = texture(uTex, vUv);
  vec4 b = texture(uSrcB, vUv);
  vec3 r;
  if      (uMode == 1) r = a.rgb + b.rgb;                       // add
  else if (uMode == 2) r = a.rgb * b.rgb;                       // multiply
  else if (uMode == 3) r = 1.0 - (1.0 - a.rgb) * (1.0 - b.rgb); // screen
  else if (uMode == 4) r = abs(a.rgb - b.rgb);                  // difference
  else if (uMode == 5) r = a.rgb - b.rgb;                       // subtract
  else if (uMode == 6) r = min(a.rgb, b.rgb);                   // darken
  else if (uMode == 7) r = max(a.rgb, b.rgb);                   // lighten
  else if (uMode == 8) r = mix(2.0 * a.rgb * b.rgb, 1.0 - 2.0 * (1.0 - a.rgb) * (1.0 - b.rgb), step(0.5, a.rgb)); // overlay
  else if (uMode == 9) r = a.rgb + b.rgb - 2.0 * a.rgb * b.rgb; // exclusion
  else                 r = mix(a.rgb, b.rgb, b.a);              // over
  return vec4(r, max(a.a, b.a));
}`,
  },

  // Matte / key: drive this layer's alpha by a channel of a SECOND layer.
  'matte': {
    inputs: [{ name: 'uMatte', label: 'Matte layer' }],
    uniforms: { uChannel: { k: '1i', from: 'channel', def: 0 }, uInvert: { k: '1f', from: 'invert', def: 0.0, bool: true } },
    decls: 'uniform sampler2D uMatte; uniform int uChannel; uniform float uInvert;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  vec4 m = texture(uMatte, vUv);
  float mv = uChannel == 1 ? m.r : uChannel == 2 ? m.g : uChannel == 3 ? m.b : uChannel == 4 ? m.a : fxLuma(m.rgb);
  if (uInvert > 0.5) mv = 1.0 - mv;
  c.a *= clamp(mv, 0.0, 1.0);
  return c;
}`,
  },

  // Color lookup: grade this layer through a SECOND layer used as a gradient/LUT,
  // indexing the LUT horizontally by this pixel's luminance.
  'lookup': {
    inputs: [{ name: 'uLut', label: 'LUT / gradient layer' }],
    uniforms: {},
    decls: 'uniform sampler2D uLut;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float l = clamp(fxLuma(c.rgb), 0.0, 1.0);
  vec3 mapped = texture(uLut, vec2(l, 0.5)).rgb;
  return vec4(mapped, c.a);
}`,
  },

  // ---- transform / color / filter super-nodes (TOP vocabulary) -----------
  // 2D UV transform: translate / rotate / zoom, with clamp|tile|mirror wrap.
  'transform': {
    uniforms: {
      uTx: { k: '1f', from: 'tx', def: 0.0 }, uTy: { k: '1f', from: 'ty', def: 0.0 },
      uRot: { k: '1f', from: 'rot', def: 0.0 }, uScale: { k: '1f', from: 'scale', def: 1.0 },
      uWrap: { k: '1i', from: 'wrap', def: 0 },
    },
    decls: 'uniform float uTx; uniform float uTy; uniform float uRot; uniform float uScale; uniform int uWrap;',
    body: `
vec4 fxMain() {
  vec2 uv = vUv - 0.5;
  float c = cos(uRot), s = sin(uRot);
  uv = mat2(c, -s, s, c) * uv;
  uv /= max(uScale, 1e-4);
  uv += 0.5 - vec2(uTx, uTy);
  if (uWrap == 1) uv = fract(uv);
  else if (uWrap == 2) uv = abs(fract(uv * 0.5) * 2.0 - 1.0);
  else uv = clamp(uv, 0.0, 1.0);
  return texture(uTex, uv);
}`,
  },

  // Color grade: brightness / contrast / gamma / saturation / hue / invert.
  'color': {
    uniforms: {
      uBright: { k: '1f', from: 'brightness', def: 0.0 }, uContrast: { k: '1f', from: 'contrast', def: 1.0 },
      uGamma: { k: '1f', from: 'gamma', def: 1.0 }, uSat: { k: '1f', from: 'saturation', def: 1.0 },
      uHue: { k: '1f', from: 'hue', def: 0.0 }, uInvert: { k: '1f', from: 'invert', def: 0.0, bool: true },
    },
    decls: 'uniform float uBright; uniform float uContrast; uniform float uGamma; uniform float uSat; uniform float uHue; uniform float uInvert;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  vec3 rgb = c.rgb;
  if (uInvert > 0.5) rgb = 1.0 - rgb;
  rgb = (rgb - 0.5) * max(uContrast, 0.0) + 0.5 + uBright;
  rgb = pow(clamp(rgb, 0.0, 1.0), vec3(1.0 / max(uGamma, 1e-3)));
  vec3 hsv = fxRgb2Hsv(rgb);
  hsv.x = fract(hsv.x + uHue);
  hsv.y = clamp(hsv.y * uSat, 0.0, 1.0);
  return vec4(fxHsv2Rgb(hsv), c.a);
}`,
  },

  // 3x3 convolution: edge (laplacian) / box-blur / sharpen, mixed by amount.
  'convolve': {
    uniforms: { uMode: { k: '1i', from: 'mode', def: 0 }, uAmount: { k: '1f', from: 'amount', def: 1.0 } },
    decls: 'uniform int uMode; uniform float uAmount;',
    body: `
vec4 fxMain() {
  vec2 t = 1.0 / uResolution;
  float ce, ed, co, norm;
  if (uMode == 1) { ce = -4.0; ed = 1.0; co = 0.0; norm = 1.0; }
  else if (uMode == 2) { ce = 1.0; ed = 1.0; co = 1.0; norm = 9.0; }
  else { ce = 5.0; ed = -1.0; co = 0.0; norm = 1.0; }
  vec3 sum = texture(uTex, vUv).rgb * ce
    + (texture(uTex, vUv + vec2(t.x, 0.0)).rgb + texture(uTex, vUv - vec2(t.x, 0.0)).rgb
     + texture(uTex, vUv + vec2(0.0, t.y)).rgb + texture(uTex, vUv - vec2(0.0, t.y)).rgb) * ed
    + (texture(uTex, vUv + t).rgb + texture(uTex, vUv - t).rgb
     + texture(uTex, vUv + vec2(t.x, -t.y)).rgb + texture(uTex, vUv + vec2(-t.x, t.y)).rgb) * co;
  sum /= norm;
  vec4 c = texture(uTex, vUv);
  return vec4(mix(c.rgb, sum, clamp(uAmount, 0.0, 1.0)), c.a);
}`,
  },

  // HDR->LDR tone map: ACES (default) or Reinhard, with exposure.
  'tonemap': {
    uniforms: { uMode: { k: '1i', from: 'mode', def: 0 }, uExposure: { k: '1f', from: 'exposure', def: 1.0 } },
    decls: 'uniform int uMode; uniform float uExposure;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  vec3 x = c.rgb * max(uExposure, 0.0);
  vec3 r = (uMode == 1) ? x / (1.0 + x) : fxAces(x);
  return vec4(r, c.a);
}`,
  },

  // Radial lens distortion: barrel (amount>0) / pincushion (amount<0).
  'lens-distort': {
    uniforms: { uK: { k: '1f', from: 'amount', def: 0.2 } },
    decls: 'uniform float uK;',
    body: `
vec4 fxMain() {
  vec2 uv = vUv - 0.5;
  uv *= 1.0 + uK * dot(uv, uv);
  uv += 0.5;
  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return vec4(0.0);
  return texture(uTex, uv);
}`,
  },

  // ---- frame-history effects (read the per-layer ring via uHistory) -------
  // Rolling shutter: each row (or column) shows the source from N frames ago,
  // shaped by a curve. The flagship history effect.
  'row-delay': {
    uniforms: { uMaxDelay: { k: '1f', from: 'maxDelay', def: 16 }, uCurve: { k: '1f', from: 'curve', def: 1.0 }, uVertical: { k: '1i', from: 'vertical', def: 0, bool: true } },
    decls: 'precision highp sampler2DArray;\nuniform sampler2DArray uHistory; uniform int uHistDepth; uniform int uHistHead; uniform float uMaxDelay; uniform float uCurve; uniform int uVertical;',
    body: `
vec4 fxMain() {
  if (uHistDepth <= 0) return texture(uTex, vUv);
  float ramp = (uVertical == 1) ? vUv.x : (1.0 - vUv.y);
  ramp = clamp(ramp, 0.0, 1.0);
  int age = int(floor(pow(ramp, max(uCurve, 0.0001)) * uMaxDelay + 0.5));
  age = max(0, min(age, uHistDepth - 1));
  int slice = ((uHistHead - age) % uHistDepth + uHistDepth) % uHistDepth;
  return texture(uHistory, vec3(vUv, float(slice)));
}`,
  },

  // Echo: show the whole frame from `delay` frames ago (ghost / trail when
  // stacked or combined with a layer feedback).
  'cache-select': {
    uniforms: { uDelay: { k: '1f', from: 'delay', def: 8.0 } },
    decls: 'precision highp sampler2DArray;\nuniform sampler2DArray uHistory; uniform int uHistDepth; uniform int uHistHead; uniform float uDelay;',
    body: `
vec4 fxMain() {
  if (uHistDepth <= 0) return texture(uTex, vUv);
  int off = max(0, min(int(floor(uDelay + 0.5)), uHistDepth - 1));
  int slice = ((uHistHead - off) % uHistDepth + uHistDepth) % uHistDepth;
  return texture(uHistory, vec3(vUv, float(slice)));
}`,
  },

  // Optical flow: per-pixel motion between the current and previous ring frame,
  // encoded as RG centered at 0.5 so a downstream displace-by consumes it.
  'optical-flow': {
    uniforms: { uScale: { k: '1f', from: 'scale', def: 10.0 } },
    decls: 'precision highp sampler2DArray;\nuniform sampler2DArray uHistory; uniform int uHistDepth; uniform int uHistHead; uniform float uScale;',
    body: `
vec4 fxMain() {
  if (uHistDepth <= 0) return vec4(0.5, 0.5, 0.0, 1.0);
  int cur = uHistHead;
  int prev = ((uHistHead - 1) % uHistDepth + uHistDepth) % uHistDepth;
  vec2 t = 1.0 / uResolution;
  float c = fxLuma(texture(uHistory, vec3(vUv, float(cur))).rgb);
  float p = fxLuma(texture(uHistory, vec3(vUv, float(prev))).rgb);
  float gx = fxLuma(texture(uHistory, vec3(vUv + vec2(t.x, 0.0), float(cur))).rgb)
           - fxLuma(texture(uHistory, vec3(vUv - vec2(t.x, 0.0), float(cur))).rgb);
  float gy = fxLuma(texture(uHistory, vec3(vUv + vec2(0.0, t.y), float(cur))).rgb)
           - fxLuma(texture(uHistory, vec3(vUv - vec2(0.0, t.y), float(cur))).rgb);
  float mag2 = gx * gx + gy * gy + 1e-4;
  vec2 flow = -(c - p) * vec2(gx, gy) / mag2 * uScale;
  return vec4(clamp(flow, -1.0, 1.0) * 0.5 + 0.5, 0.0, 1.0);
}`,
  },

  // Slice / glitch: cut the frame into N bands perpendicular to one axis and
  // shove each band along that axis by a time-hashed amount.
  'slice': {
    uniforms: {
      uSlices: { k: '1f', from: 'count', def: 16 },
      uOffset: { k: '1f', from: 'offset', def: 0.1 },
      uVertical: { k: '1f', from: 'vertical', def: 0, bool: true },
    },
    decls: 'uniform float uSlices; uniform float uOffset; uniform float uVertical;',
    body: `
vec4 fxMain() {
  bool vert = uVertical > 0.5;
  float n = max(uSlices, 1.0);
  float band = vert ? vUv.x : vUv.y;
  float idx = floor(band * n);
  float rnd = fxHash(vec2(idx, floor(uTime * 2.0))) * 2.0 - 1.0;
  float shift = rnd * uOffset;
  vec2 uv = vert ? vec2(vUv.x, fract(vUv.y + shift)) : vec2(fract(vUv.x + shift), vUv.y);
  return texture(uTex, uv);
}`,
  },

  // ---- pixel -------------------------------------------------------------
  'pixelate': {
    uniforms: { uSize: { k: '1f', from: 'size', def: 8.0 } },
    decls: 'uniform float uSize;',
    body: `
vec4 fxMain() {
  float s = max(uSize, 1.0);
  vec2 cell = uResolution / s;
  vec2 uv = (floor(vUv * cell) + 0.5) / cell;
  return texture(uTex, uv);
}`,
  },

  'dither': {
    uniforms: { uLevels: { k: '1f', from: 'levels', def: 4.0 } },
    decls: 'uniform float uLevels;',
    body: `
const float bayer[16] = float[16](
  0.0,  8.0,  2.0, 10.0,
 12.0,  4.0, 14.0,  6.0,
  3.0, 11.0,  1.0,  9.0,
 15.0,  7.0, 13.0,  5.0);
vec4 fxMain() {
  ivec2 ip = ivec2(mod(gl_FragCoord.xy, 4.0));
  float th = (bayer[ip.y * 4 + ip.x] + 0.5) / 16.0 - 0.5;
  vec4 c = texture(uTex, vUv);
  float lv = max(uLevels, 2.0);
  vec3 q = floor(c.rgb * (lv - 1.0) + th + 0.5) / (lv - 1.0);
  return vec4(clamp(q, 0.0, 1.0), c.a);
}`,
  },

  'posterize': {
    uniforms: { uLevels: { k: '1f', from: 'levels', def: 5.0 } },
    decls: 'uniform float uLevels;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float lv = max(uLevels, 2.0);
  vec3 q = floor(c.rgb * lv) / lv;
  return vec4(q, c.a);
}`,
  },

  // Approximate GPU pixel-sort: within luminance bands, shift samples along the
  // sort axis so similar-luma runs streak. Cheap, single-pass, order-stable-ish.
  'pixel-sort': {
    uniforms: {
      uThreshold: { k: '1f', from: 'threshold', def: 0.5 },
      uVertical: { k: '1f', from: 'vertical', def: 0, bool: true },
    },
    decls: 'uniform float uThreshold; uniform float uVertical;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float l = fxLuma(c.rgb);
  // band membership: only "bright enough" pixels streak
  if (l < uThreshold) return c;
  bool vert = uVertical > 0.5;
  float axis = vert ? vUv.y : vUv.x;
  float texel = vert ? (1.0 / uResolution.y) : (1.0 / uResolution.x);
  // walk forward along the axis, accumulate the brightest sample seen
  vec4 best = c;
  float bestL = l;
  for (int i = 1; i <= 24; i++) {
    float d = float(i) * texel;
    vec2 uv = vert ? vec2(vUv.x, axis - d) : vec2(axis - d, vUv.y);
    vec4 s = texture(uTex, uv);
    float sl = fxLuma(s.rgb);
    if (sl < uThreshold) break;
    if (sl > bestL) { bestL = sl; best = s; }
  }
  return best;
}`,
  },

  // ---- artistic ----------------------------------------------------------
  // ASCII via luminance -> block ramp drawn procedurally per cell (no atlas
  // texture needed; the glyph density is approximated by sub-cell coverage).
  'ascii': {
    uniforms: { uCell: { k: '1f', from: 'cell', def: 8.0 } },
    decls: 'uniform float uCell;',
    body: `
// 5 ramp glyphs approximated by coverage thresholds drawn in a 4x4 sub-grid.
float glyph(float lum, vec2 sub) {
  // sub in [0,1] within cell. Build a 4x4 dot mask whose density ~ lum.
  vec2 g = floor(sub * 4.0);
  float idx = g.y * 4.0 + g.x;       // 0..15 dot index
  float order = mod(idx * 7.0, 16.0) / 16.0; // pseudo ordered pattern
  return step(order, lum);
}
vec4 fxMain() {
  float s = max(uCell, 2.0);
  vec2 cell = uResolution / s;
  vec2 cidx = floor(vUv * cell);
  vec2 cuv = (cidx + 0.5) / cell;
  vec4 c = texture(uTex, cuv);
  float lum = fxLuma(c.rgb);
  vec2 sub = fract(vUv * cell);
  float on = glyph(lum, sub);
  vec3 col = c.rgb * on;
  return vec4(col, c.a);
}`,
  },

  'crt': {
    uniforms: {
      uScan: { k: '1f', from: 'scanline', def: 0.6 },
      uCurv: { k: '1f', from: 'curvature', def: 0.15 },
      uVig: { k: '1f', from: 'vignette', def: 0.4 },
    },
    decls: 'uniform float uScan; uniform float uCurv; uniform float uVig;',
    body: `
vec2 curve(vec2 uv) {
  uv = uv * 2.0 - 1.0;
  vec2 off = abs(uv.yx) / vec2(3.0, 3.0);
  uv += uv * off * off * uCurv;
  return uv * 0.5 + 0.5;
}
vec4 fxMain() {
  vec2 uv = curve(vUv);
  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
    return vec4(0.0, 0.0, 0.0, 1.0);
  vec4 c = texture(uTex, uv);
  float scan = 1.0 - uScan * 0.5 * (0.5 + 0.5 * sin(uv.y * uResolution.y * 3.14159));
  c.rgb *= scan;
  vec2 v = uv * (1.0 - uv.yx);
  float vig = pow(v.x * v.y * 15.0, uVig);
  c.rgb *= clamp(vig, 0.0, 1.0);
  return c;
}`,
  },

  'halftone': {
    uniforms: { uCell: { k: '1f', from: 'cell', def: 8.0 }, uAngle: { k: '1f', from: 'angle', def: 0.4 } },
    decls: 'uniform float uCell; uniform float uAngle;',
    body: `
vec4 fxMain() {
  float s = max(uCell, 2.0);
  float ca = cos(uAngle), sa = sin(uAngle);
  mat2 rot = mat2(ca, -sa, sa, ca);
  vec2 px = vUv * uResolution;
  vec2 rp = rot * px;
  vec2 cell = (floor(rp / s) + 0.5) * s;
  vec2 sampleUv = (inverse(rot) * cell) / uResolution;
  vec4 c = texture(uTex, clamp(sampleUv, 0.0, 1.0));
  float lum = fxLuma(c.rgb);
  vec2 local = fract(rp / s) - 0.5;
  float dist = length(local);
  float radius = (1.0 - lum) * 0.7;
  float dot = smoothstep(radius, radius - 0.08, dist);
  vec3 col = mix(vec3(1.0), c.rgb, dot);
  return vec4(col, c.a);
}`,
  },

  'ink': {
    uniforms: { uThreshold: { k: '1f', from: 'threshold', def: 0.25 }, uLevels: { k: '1f', from: 'levels', def: 4.0 } },
    decls: 'uniform float uThreshold; uniform float uLevels;',
    body: `
float lumAt(vec2 uv) { return fxLuma(texture(uTex, uv).rgb); }
vec4 fxMain() {
  vec2 t = 1.0 / uResolution;
  // Sobel edge magnitude
  float tl = lumAt(vUv + t * vec2(-1.0,  1.0));
  float  l = lumAt(vUv + t * vec2(-1.0,  0.0));
  float bl = lumAt(vUv + t * vec2(-1.0, -1.0));
  float tr = lumAt(vUv + t * vec2( 1.0,  1.0));
  float  r = lumAt(vUv + t * vec2( 1.0,  0.0));
  float br = lumAt(vUv + t * vec2( 1.0, -1.0));
  float  tt = lumAt(vUv + t * vec2( 0.0,  1.0));
  float  bb = lumAt(vUv + t * vec2( 0.0, -1.0));
  float gx = -tl - 2.0 * l - bl + tr + 2.0 * r + br;
  float gy =  tl + 2.0 * tt + tr - bl - 2.0 * bb - br;
  float edge = length(vec2(gx, gy));
  vec4 c = texture(uTex, vUv);
  float lv = max(uLevels, 2.0);
  vec3 flatCol = floor(c.rgb * lv) / lv;     // flattened color ('flat' is reserved)
  float ink = step(uThreshold, edge);        // ink line mask
  vec3 col = mix(flatCol, vec3(0.0), ink);
  return vec4(col, c.a);
}`,
  },

  'edge-detect': {
    uniforms: {},
    decls: '',
    body: `
float lumAt(vec2 uv) { return fxLuma(texture(uTex, uv).rgb); }
vec4 fxMain() {
  vec2 t = 1.0 / uResolution;
  float tl = lumAt(vUv + t * vec2(-1.0,  1.0));
  float  l = lumAt(vUv + t * vec2(-1.0,  0.0));
  float bl = lumAt(vUv + t * vec2(-1.0, -1.0));
  float tr = lumAt(vUv + t * vec2( 1.0,  1.0));
  float  r = lumAt(vUv + t * vec2( 1.0,  0.0));
  float br = lumAt(vUv + t * vec2( 1.0, -1.0));
  float  tt = lumAt(vUv + t * vec2( 0.0,  1.0));
  float  bb = lumAt(vUv + t * vec2( 0.0, -1.0));
  float gx = -tl - 2.0 * l - bl + tr + 2.0 * r + br;
  float gy =  tl + 2.0 * tt + tr - bl - 2.0 * bb - br;
  float edge = clamp(length(vec2(gx, gy)), 0.0, 1.0);
  return vec4(vec3(edge), texture(uTex, vUv).a);
}`,
  },

  // ---- generative --------------------------------------------------------
  'particle-grid': {
    uniforms: { uCell: { k: '1f', from: 'cell', def: 12.0 }, uDrift: { k: '1f', from: 'drift', def: 0.0 } },
    decls: 'uniform float uCell; uniform float uDrift;',
    body: `
vec4 fxMain() {
  float s = max(uCell, 2.0);
  vec2 cell = uResolution / s;
  vec2 cidx = floor(vUv * cell);
  vec2 center = (cidx + 0.5) / cell;
  // drift each cell by time * noise
  float n = fxHash(cidx);
  vec2 drift = vec2(cos(uTime + n * 6.28), sin(uTime * 1.3 + n * 6.28)) * uDrift * (1.0 / cell);
  vec4 c = texture(uTex, clamp(center + drift, 0.0, 1.0));
  float lum = fxLuma(c.rgb);
  vec2 local = (fract(vUv * cell) - 0.5) - drift * cell;
  float dist = length(local);
  float radius = 0.15 + lum * 0.35;
  float dotMask = smoothstep(radius, radius - 0.06, dist);
  return vec4(c.rgb * dotMask, c.a);
}`,
  },

  'pattern': {
    uniforms: { uScale: { k: '1f', from: 'scale', def: 12.0 }, uMix: { k: '1f', from: 'mix', def: 0.5 } },
    decls: 'uniform float uScale; uniform float uMix;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  vec2 p = vUv * uResolution / max(uScale, 1.0);
  float stripes = 0.5 + 0.5 * sin(p.x + p.y + uTime);
  float grid = step(0.5, fract(p.x)) * step(0.5, fract(p.y));
  float pat = mix(stripes, grid, 0.5);
  vec3 col = mix(c.rgb, c.rgb * pat, uMix);
  return vec4(col, c.a);
}`,
  },

  // ====================================================================
  // ILLUSTRATIVE SHADERS - stackable Figma-shaders / paper-design register.
  // SOURCES generate their own field (ignore uTex); FILTERS sample uTex.
  // Colours are driven by scalar hue/sat/value uniforms (the chain is
  // scalar-uniform); stack a `gradient-map` / `color` / `lookup` pass on top
  // to rebrand. See docs/research/shader-library.md + design-library/shader-*.md.
  // ====================================================================

  // ---- sources ----------------------------------------------------------
  'mesh-gradient': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.6 }, uSpread: { k: '1f', from: 'spread', def: 0.3 }, uSpeed: { k: '1f', from: 'speed', def: 0.2 }, uVal: { k: '1f', from: 'value', def: 0.9 } },
    decls: 'uniform float uHue; uniform float uSpread; uniform float uSpeed; uniform float uVal;',
    body: `
vec4 fxMain() {
  float t = uTime * uSpeed;
  vec3 col = vec3(0.0); float tot = 0.0;
  for (int i = 0; i < 3; i++) {
    float fi = float(i);
    vec2 c = vec2(0.5) + 0.4 * vec2(sin(t + fi * 2.1), cos(t * 0.8 + fi * 1.7));
    float w = smoothstep(0.75, 0.0, length(vUv - c));
    col += fxHsv2Rgb(vec3(fract(uHue + fi * uSpread), 0.6, uVal)) * w;
    tot += w;
  }
  col /= max(tot, 0.001);
  col += (fxHash(vUv * 1000.0) - 0.5) * 0.02;
  return vec4(col, 1.0);
}`,
  },

  'fractal-noise': {
    uniforms: { uScale: { k: '1f', from: 'scale', def: 3.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.05 }, uHue: { k: '1f', from: 'hue', def: 0.6 }, uSat: { k: '1f', from: 'saturation', def: 0.0 }, uContrast: { k: '1f', from: 'contrast', def: 1.0 } },
    decls: 'uniform float uScale; uniform float uSpeed; uniform float uHue; uniform float uSat; uniform float uContrast;',
    body: `
vec4 fxMain() {
  float n = fxFbm(vUv * uScale + uTime * uSpeed);
  n = clamp((n - 0.5) * uContrast + 0.5, 0.0, 1.0);
  return vec4(fxHsv2Rgb(vec3(uHue, uSat, n)), 1.0);
}`,
  },

  'clouds': {
    uniforms: { uCover: { k: '1f', from: 'cover', def: 0.5 }, uScale: { k: '1f', from: 'scale', def: 3.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.02 }, uHue: { k: '1f', from: 'hue', def: 0.6 } },
    decls: 'uniform float uCover; uniform float uScale; uniform float uSpeed; uniform float uHue;',
    body: `
vec4 fxMain() {
  float c = fxFbm(vUv * uScale + vec2(uTime * uSpeed, 0.0));
  c = smoothstep(uCover - 0.18, uCover + 0.18, c);
  vec3 sky = mix(fxHsv2Rgb(vec3(uHue, 0.45, 0.85)), fxHsv2Rgb(vec3(uHue, 0.12, 1.0)), vUv.y);
  return vec4(mix(sky, vec3(1.0), c), 1.0);
}`,
  },

  'nebula': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.72 }, uDensity: { k: '1f', from: 'density', def: 1.5 }, uSpeed: { k: '1f', from: 'speed', def: 0.01 }, uStars: { k: '1f', from: 'stars', def: 0.6 } },
    decls: 'uniform float uHue; uniform float uDensity; uniform float uSpeed; uniform float uStars;',
    body: `
vec4 fxMain() {
  float g = fxFbm(vUv * 3.0 + uTime * uSpeed);
  vec3 gas = fxHsv2Rgb(vec3(fract(uHue + g * 0.2), 0.7, pow(g, max(uDensity, 0.1))));
  vec2 sg = floor(vUv * uResolution / 2.0);
  float s = step(0.996, fxHash(sg));
  float tw = 0.5 + 0.5 * sin(uTime * 3.0 + fxHash(sg + 3.0) * 6.2831);
  gas += vec3(s * tw * uStars);
  return vec4(gas, 1.0);
}`,
  },

  'glowing-wave': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.55 }, uFreq: { k: '1f', from: 'frequency', def: 8.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.6 }, uGlow: { k: '1f', from: 'glow', def: 2.0 } },
    decls: 'uniform float uHue; uniform float uFreq; uniform float uSpeed; uniform float uGlow;',
    body: `
vec4 fxMain() {
  float w = 0.5 + 0.5 * sin(vUv.y * uFreq + vUv.x * 1.5 + uTime * uSpeed);
  float glow = pow(clamp(w, 0.0, 1.0), max(uGlow, 0.1));
  return vec4(fxHsv2Rgb(vec3(uHue, 0.8, 1.0)) * glow, 1.0);
}`,
  },

  'neuro-noise': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.6 }, uFolds: { k: '1f', from: 'folds', def: 3.0 }, uScale: { k: '1f', from: 'scale', def: 2.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.02 } },
    decls: 'uniform float uHue; uniform float uFolds; uniform float uScale; uniform float uSpeed;',
    body: `
vec4 fxMain() {
  vec2 q = vUv * uScale;
  for (int i = 0; i < 3; i++) q += 0.4 * vec2(fxFbm(q + uTime * uSpeed), fxFbm(q.yx + 3.1));
  float n = fxFbm(q * 2.0);
  float ridge = abs(2.0 * fract(n * uFolds) - 1.0);
  vec3 col = mix(fxHsv2Rgb(vec3(uHue, 0.5, 0.22)), fxHsv2Rgb(vec3(fract(uHue + 0.08), 0.4, 0.85)), smoothstep(0.15, 0.85, ridge));
  return vec4(col, 1.0);
}`,
  },

  'godrays': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.12 }, uCount: { k: '1f', from: 'count', def: 14.0 }, uGain: { k: '1f', from: 'gain', def: 1.0 }, uOx: { k: '1f', from: 'originX', def: 0.5 }, uOy: { k: '1f', from: 'originY', def: 0.15 } },
    decls: 'uniform float uHue; uniform float uCount; uniform float uGain; uniform float uOx; uniform float uOy;',
    body: `
vec4 fxMain() {
  vec2 d = vUv - vec2(uOx, uOy);
  float a = atan(d.y, d.x);
  float rays = 0.5 + 0.5 * sin(a * uCount + uTime * 0.3);
  rays *= fxFbm(vec2(a * 3.0, uTime * 0.1));
  float fall = smoothstep(1.1, 0.0, length(d));
  return vec4(fxHsv2Rgb(vec3(uHue, 0.5, 1.0)) * rays * fall * uGain, 1.0);
}`,
  },

  'water-caustics': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.5 }, uScale: { k: '1f', from: 'scale', def: 6.0 }, uSharp: { k: '1f', from: 'sharpness', def: 2.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.3 } },
    decls: 'uniform float uHue; uniform float uScale; uniform float uSharp; uniform float uSpeed;',
    body: `
vec4 fxMain() {
  vec2 p = vUv * uScale + vec2(sin(uTime * uSpeed), cos(uTime * uSpeed * 0.8));
  float n = fxFbm(p);
  float c = pow(1.0 - abs(2.0 * n - 1.0), max(uSharp, 0.1));
  return vec4(fxHsv2Rgb(vec3(uHue, 0.4, 1.0)) * c, 1.0);
}`,
  },

  'particle-web': {
    uniforms: { uCount: { k: '1f', from: 'count', def: 10.0 }, uHue: { k: '1f', from: 'hue', def: 0.6 }, uSpeed: { k: '1f', from: 'speed', def: 0.3 }, uLink: { k: '1f', from: 'link', def: 0.6 } },
    decls: 'uniform float uCount; uniform float uHue; uniform float uSpeed; uniform float uLink;',
    body: `
vec4 fxMain() {
  float n = max(uCount, 2.0);
  vec2 ci = floor(vUv * n);
  float glow = 0.0; float web = 0.0;
  for (int y = -1; y <= 1; y++) {
    for (int x = -1; x <= 1; x++) {
      vec2 cc = ci + vec2(float(x), float(y));
      vec2 jit = vec2(fxHash(cc), fxHash(cc + 7.0));
      vec2 p = (cc + 0.3 + 0.4 * vec2(sin(uTime * uSpeed + jit.x * 6.2831), cos(uTime * uSpeed + jit.y * 6.2831))) / n;
      float d = length(vUv - p);
      glow += smoothstep(0.025, 0.0, d);
      web += smoothstep(0.18 * uLink, 0.0, d);
    }
  }
  float v = clamp(glow + web * 0.2, 0.0, 1.0);
  return vec4(fxHsv2Rgb(vec3(uHue, 0.55, 1.0)) * v, 1.0);
}`,
  },

  'magnetic-field': {
    uniforms: { uScale: { k: '1f', from: 'scale', def: 3.0 }, uHue: { k: '1f', from: 'hue', def: 0.6 }, uSpeed: { k: '1f', from: 'speed', def: 0.05 }, uDensity: { k: '1f', from: 'density', def: 40.0 } },
    decls: 'uniform float uScale; uniform float uHue; uniform float uSpeed; uniform float uDensity;',
    body: `
vec4 fxMain() {
  float ang = fxFbm(vUv * uScale + uTime * uSpeed) * 12.566;
  vec2 dir = vec2(cos(ang), sin(ang));
  float stream = sin(dot(vUv * uDensity, vec2(-dir.y, dir.x)));
  float line = smoothstep(0.75, 1.0, abs(stream));
  return vec4(fxHsv2Rgb(vec3(uHue, 0.5, 1.0)) * line, 1.0);
}`,
  },

  'metaball-merge': {
    uniforms: { uCount: { k: '1f', from: 'count', def: 5.0 }, uHue: { k: '1f', from: 'hue', def: 0.55 }, uSpeed: { k: '1f', from: 'speed', def: 0.4 }, uThresh: { k: '1f', from: 'threshold', def: 1.0 } },
    decls: 'uniform float uCount; uniform float uHue; uniform float uSpeed; uniform float uThresh;',
    body: `
vec4 fxMain() {
  float field = 0.0;
  for (int i = 0; i < 8; i++) {
    if (float(i) >= uCount) break;
    float fi = float(i);
    vec2 c = vec2(0.5) + 0.35 * vec2(sin(uTime * uSpeed + fi * 2.0), cos(uTime * uSpeed * 0.9 + fi * 1.3));
    field += 0.04 / max(length(vUv - c), 0.001);
  }
  float blob = smoothstep(uThresh - 0.12, uThresh + 0.12, field);
  return vec4(mix(vec3(0.04), fxHsv2Rgb(vec3(uHue, 0.6, 1.0)), blob), 1.0);
}`,
  },

  'moire-interference': {
    uniforms: { uFreqA: { k: '1f', from: 'frequencyA', def: 40.0 }, uFreqB: { k: '1f', from: 'frequencyB', def: 42.0 }, uAngle: { k: '1f', from: 'angle', def: 0.08 }, uHue: { k: '1f', from: 'hue', def: 0.6 }, uSpeed: { k: '1f', from: 'speed', def: 0.02 } },
    decls: 'uniform float uFreqA; uniform float uFreqB; uniform float uAngle; uniform float uHue; uniform float uSpeed;',
    body: `
vec4 fxMain() {
  float a = sin(vUv.x * uFreqA);
  float ang = uAngle + uTime * uSpeed;
  float b = sin((cos(ang) * vUv.x + sin(ang) * vUv.y) * uFreqB);
  float m = a * b;
  return vec4(fxHsv2Rgb(vec3(uHue, 0.3, 0.5 + 0.5 * m)), 1.0);
}`,
  },

  'concentric-patterns': {
    uniforms: { uFreq: { k: '1f', from: 'frequency', def: 20.0 }, uHue: { k: '1f', from: 'hue', def: 0.05 }, uSpeed: { k: '1f', from: 'speed', def: 0.3 }, uShape: { k: '1i', from: 'shape', def: 0 } },
    decls: 'uniform float uFreq; uniform float uHue; uniform float uSpeed; uniform int uShape;',
    body: `
vec4 fxMain() {
  vec2 d = vUv - 0.5;
  float r = (uShape == 1) ? max(abs(d.x), abs(d.y)) : length(d);
  float ring = step(0.5, fract(r * uFreq - uTime * uSpeed));
  vec3 col = mix(fxHsv2Rgb(vec3(uHue, 0.6, 0.95)), fxHsv2Rgb(vec3(fract(uHue + 0.5), 0.6, 0.2)), ring);
  return vec4(col, 1.0);
}`,
  },

  'dither-waves': {
    uniforms: { uHue: { k: '1f', from: 'hue', def: 0.45 }, uFreq: { k: '1f', from: 'frequency', def: 8.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.6 }, uLevels: { k: '1f', from: 'levels', def: 2.0 } },
    decls: 'uniform float uHue; uniform float uFreq; uniform float uSpeed; uniform float uLevels;',
    body: `
const float bwm[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
vec4 fxMain() {
  float w = 0.5 + 0.5 * sin(vUv.y * uFreq + vUv.x * 2.0 + uTime * uSpeed);
  w *= smoothstep(0.0, 0.3, vUv.y) * smoothstep(1.0, 0.7, vUv.y);
  ivec2 ip = ivec2(mod(gl_FragCoord.xy, 4.0));
  float th = (bwm[ip.y * 4 + ip.x] + 0.5) / 16.0 - 0.5;
  float lv = max(uLevels, 2.0);
  float q = clamp(floor(w * (lv - 1.0) + th + 0.5) / (lv - 1.0), 0.0, 1.0);
  return vec4(fxHsv2Rgb(vec3(uHue, 0.8, 1.0)) * q, 1.0);
}`,
  },

  // ---- filters ----------------------------------------------------------
  'gradient-map': {
    uniforms: { uHueLo: { k: '1f', from: 'hueLow', def: 0.66 }, uHueHi: { k: '1f', from: 'hueHigh', def: 0.12 }, uSat: { k: '1f', from: 'saturation', def: 0.6 } },
    decls: 'uniform float uHueLo; uniform float uHueHi; uniform float uSat;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float l = clamp(fxLuma(c.rgb), 0.0, 1.0);
  float hue = mix(uHueLo, uHueHi, l);
  return vec4(fxHsv2Rgb(vec3(hue, uSat, mix(0.12, 1.0, l))), c.a);
}`,
  },

  'color-outline': {
    uniforms: { uThresh: { k: '1f', from: 'threshold', def: 0.2 }, uHue: { k: '1f', from: 'hue', def: 0.6 }, uThick: { k: '1f', from: 'thickness', def: 1.0 } },
    decls: 'uniform float uThresh; uniform float uHue; uniform float uThick;',
    body: `
vec4 fxMain() {
  vec2 t = uThick / uResolution;
  float l00 = fxLuma(texture(uTex, vUv + vec2(-t.x, -t.y)).rgb);
  float l10 = fxLuma(texture(uTex, vUv + vec2(0.0, -t.y)).rgb);
  float l20 = fxLuma(texture(uTex, vUv + vec2(t.x, -t.y)).rgb);
  float l01 = fxLuma(texture(uTex, vUv + vec2(-t.x, 0.0)).rgb);
  float l21 = fxLuma(texture(uTex, vUv + vec2(t.x, 0.0)).rgb);
  float l02 = fxLuma(texture(uTex, vUv + vec2(-t.x, t.y)).rgb);
  float l12 = fxLuma(texture(uTex, vUv + vec2(0.0, t.y)).rgb);
  float l22 = fxLuma(texture(uTex, vUv + vec2(t.x, t.y)).rgb);
  float gx = l00 + 2.0 * l01 + l02 - l20 - 2.0 * l21 - l22;
  float gy = l00 + 2.0 * l10 + l20 - l02 - 2.0 * l12 - l22;
  float e = clamp(length(vec2(gx, gy)), 0.0, 1.0);
  float line = step(uThresh, e);
  vec4 c = texture(uTex, vUv);
  vec3 col = fxHsv2Rgb(vec3(fract(uHue + e * 0.5), 0.85, 1.0));
  return vec4(mix(c.rgb, col, line), c.a);
}`,
  },

  'channel-mixer': {
    uniforms: { uMode: { k: '1i', from: 'mode', def: 1 }, uAmount: { k: '1f', from: 'amount', def: 1.0 } },
    decls: 'uniform int uMode; uniform float uAmount;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  vec3 s = c.rgb; vec3 r;
  float l = fxLuma(s);
  if (uMode == 1) r = s.bgr;
  else if (uMode == 2) r = fxHsv2Rgb(vec3(mix(0.66, 0.0, l), 0.9, 1.0));
  else if (uMode == 3) r = l * vec3(1.12, 0.95, 0.72);
  else r = s;
  return vec4(mix(s, r, clamp(uAmount, 0.0, 1.0)), c.a);
}`,
  },

  'hatching': {
    uniforms: { uFreq: { k: '1f', from: 'frequency', def: 140.0 } },
    decls: 'uniform float uFreq;',
    body: `
float fxHatch(vec2 uv, float a, float f) {
  float v = abs(sin((uv.x * cos(a) + uv.y * sin(a)) * f));
  return step(0.88, v);
}
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float l = fxLuma(c.rgb);
  float h = 0.0;
  if (l < 0.85) h = max(h, fxHatch(vUv, 0.0, uFreq));
  if (l < 0.6)  h = max(h, fxHatch(vUv, 0.785, uFreq));
  if (l < 0.4)  h = max(h, fxHatch(vUv, 1.5708, uFreq));
  if (l < 0.2)  h = max(h, fxHatch(vUv, 2.356, uFreq));
  return vec4(mix(vec3(0.96), vec3(0.05), h), c.a);
}`,
  },

  'pattern-refraction': {
    uniforms: { uFreq: { k: '1f', from: 'frequency', def: 30.0 }, uStrength: { k: '1f', from: 'strength', def: 0.02 }, uAngle: { k: '1f', from: 'angle', def: 0.0 }, uSpeed: { k: '1f', from: 'speed', def: 0.0 } },
    decls: 'uniform float uFreq; uniform float uStrength; uniform float uAngle; uniform float uSpeed;',
    body: `
vec4 fxMain() {
  vec2 dir = vec2(cos(uAngle), sin(uAngle));
  float rib = sin((vUv.x * dir.x + vUv.y * dir.y) * uFreq + uTime * uSpeed);
  vec2 off = dir * rib * uStrength;
  return texture(uTex, vUv + off);
}`,
  },

  'chromatic-metal': {
    uniforms: { uBands: { k: '1f', from: 'bands', def: 3.0 }, uCA: { k: '1f', from: 'aberration', def: 0.01 } },
    decls: 'uniform float uBands; uniform float uCA;',
    body: `
vec4 fxMain() {
  vec4 c = texture(uTex, vUv);
  float l = fxLuma(c.rgb);
  float m = 0.5 + 0.5 * sin(l * 6.2831 * uBands + uTime * 0.5);
  float r = fxLuma(texture(uTex, vUv + vec2(uCA, 0.0)).rgb);
  float b = fxLuma(texture(uTex, vUv - vec2(uCA, 0.0)).rgb);
  vec3 chrome = vec3(m) * vec3(0.85, 0.92, 1.0);
  chrome.r *= 0.6 + 0.7 * r;
  chrome.b *= 0.6 + 0.7 * b;
  return vec4(chrome, c.a);
}`,
  },

  'bokeh-blur': {
    uniforms: { uRadius: { k: '1f', from: 'radius', def: 0.012 }, uThresh: { k: '1f', from: 'threshold', def: 0.7 }, uBloom: { k: '1f', from: 'bloom', def: 2.0 } },
    decls: 'uniform float uRadius; uniform float uThresh; uniform float uBloom;',
    body: `
vec4 fxMain() {
  vec3 acc = vec3(0.0); float w = 0.0;
  const int N = 16;
  for (int i = 0; i < N; i++) {
    float a = float(i) / float(N) * 6.2831;
    float rr = (mod(float(i), 2.0) == 0.0) ? 1.0 : 0.55;
    vec3 s = texture(uTex, vUv + vec2(cos(a), sin(a)) * uRadius * rr).rgb;
    float b = 1.0 + step(uThresh, fxLuma(s)) * uBloom;
    acc += s * b; w += b;
  }
  return vec4(acc / w, texture(uTex, vUv).a);
}`,
  },

  'riso-print': {
    uniforms: { uCell: { k: '1f', from: 'cell', def: 6.0 }, uHueA: { k: '1f', from: 'hueA', def: 0.92 }, uHueB: { k: '1f', from: 'hueB', def: 0.5 }, uShift: { k: '1f', from: 'registration', def: 0.004 } },
    decls: 'uniform float uCell; uniform float uHueA; uniform float uHueB; uniform float uShift;',
    body: `
float fxHtDot(vec2 uv, vec2 res, float cell, float ang, float cov) {
  float ca = cos(ang), sa = sin(ang);
  vec2 rp = mat2(ca, -sa, sa, ca) * (uv * res);
  vec2 local = fract(rp / cell) - 0.5;
  return smoothstep(cov * 0.72, cov * 0.72 - 0.12, length(local));
}
vec4 fxMain() {
  float la = fxLuma(texture(uTex, vUv + uShift).rgb);
  float lb = fxLuma(texture(uTex, vUv - uShift).rgb);
  float cell = max(uCell, 2.0);
  float da = fxHtDot(vUv, uResolution, cell, 0.26, 1.0 - la);
  float db = fxHtDot(vUv, uResolution, cell, -0.26, 1.0 - lb);
  vec3 col = vec3(0.96, 0.95, 0.92);
  col *= mix(vec3(1.0), fxHsv2Rgb(vec3(uHueA, 0.7, 1.0)), da);
  col *= mix(vec3(1.0), fxHsv2Rgb(vec3(uHueB, 0.7, 1.0)), db);
  return vec4(col, 1.0);
}`,
  },
};

// ===========================================================================
// STATEFUL, MULTI-PASS EFFECTS (the persistent-buffer subsystem)
// ===========================================================================
// A stateful effect is a definition with:
//   textures: { name: { channels:1|2|4, ping:bool, filter:'nearest'|'linear',
//                       wrap:'clamp'|'repeat' } }
//     ping=true allocates a read/write PAIR (ping-pong) keyed by `name`. The
//     instance owns one such set, sized to the source, PERSISTENT across frames.
//   programs: { name: fragSrc }   // compiled once per chain (shared by instances)
//   passes(ctx) -> [ Pass, ... ]  // ordered, called every step; may repeat a
//     program N times for solver iterations. A Pass declares the program, the
//     output texture (a ping target swaps after the pass), the input texture
//     bindings (sampler name -> texture key), and a uniform setter.
//   display: { program }          // FINAL pass: combines state + uIntensity ->
//     the visible RGBA result (drawn to the chain canvas / target).
// The runtime (createStatefulRunner inside createFXChain) lazily creates an
// instance's textures, resizes them, runs passes() into the persistent set, then
// the display pass to the canvas. disposeStateful frees one instance.
//
// This is GENERIC: feedback (one ping texture + a fade/composite pass) and GPU
// particles (a position/velocity ping pair + an update + a draw pass) can be
// added as further STATEFUL_EFFECTS entries with NO runtime changes.
// ---------------------------------------------------------------------------

// Shared header for stateful fragment shaders. Float-friendly: outputs are
// written to RGBA16F when available; the runtime binds whatever attachment the
// instance allocated. Each shader reads simulation textures at vUv.
const SFX_HEADER = `#version 300 es
precision highp float;
precision highp sampler2D;
in vec2 vUv;
out vec4 fragColor;
uniform vec2 uResolution;   // sim resolution in texels
uniform vec2 uTexel;        // 1.0 / uResolution
uniform float uTime;
uniform float uDt;
`;

// Bilinear-correct neighbour sampling is implicit (LINEAR filter). gl_FragCoord
// is NOT used; everything is in vUv space so it survives any viewport.

// ---- GPU FLUID (Stam stable-fluids, the first stateful effect) ------------
// Persistent textures (per instance, sized to the layer's sim resolution):
//   vel   - velocity field, RG, ping-pong (advected + projected each frame)
//   pres  - pressure field, R,  ping-pong (Jacobi solved each frame)
//   div   - divergence,     R,  single    (recomputed each frame)
//   dye   - colour carried by the flow, RGBA, ping-pong (the layer pixels)
// Pass sequence per step:
//   1. seedDye   - refresh a fraction of dye from the layer source (uSrc)
//   2. splat     - inject velocity + dye from the pointer (gaussian splat)
//   3. advectVel - semi-Lagrangian advect velocity by itself
//   4. curl/vort - (optional) vorticity confinement to re-add swirl
//   5. divergence- compute div of velocity
//   6. pressure  - Jacobi solve x N (configurable iterations, default 24)
//   7. gradient  - subtract pressure gradient (make velocity divergence-free)
//   8. advectDye - advect dye by the (now divergence-free) velocity, then fade
//   9. display   - composite dye over the layer source by uIntensity
const FLUID_SHADERS = {
  // Refresh dye from the live layer source so the flow stirs real content.
  // uSeed=1 on the first frame (full copy), small (~0.06) afterwards.
  seedDye: SFX_HEADER + `
uniform sampler2D uDye;
uniform sampler2D uSrc;
uniform float uSeed;
void main(){
  vec4 prev = texture(uDye, vUv);
  vec4 src  = texture(uSrc, vUv);
  fragColor = mix(prev, src, clamp(uSeed, 0.0, 1.0));
}`,
  // Inject pointer velocity + a dye splat in a gaussian falloff around uPoint.
  splatVel: SFX_HEADER + `
uniform sampler2D uVel;
uniform vec2 uPoint;     // pointer pos 0..1
uniform vec2 uForce;     // velocity to add at the centre
uniform float uRadius;   // splat radius (uv units)
void main(){
  vec2 v = texture(uVel, vUv).xy;
  vec2 d = vUv - uPoint;
  float f = exp(-dot(d, d) / max(1e-5, uRadius * uRadius));
  fragColor = vec4(v + uForce * f, 0.0, 1.0);
}`,
  // Semi-Lagrangian advection (shared by velocity + dye). uField is what we
  // carry, uVel is the velocity that transports it. uDissipation fades the
  // result (1.0 = no fade).
  advect: SFX_HEADER + `
uniform sampler2D uVel;
uniform sampler2D uField;
uniform float uDissipation;
void main(){
  vec2 vel = texture(uVel, vUv).xy;
  vec2 coord = vUv - uDt * vel * uTexel;
  fragColor = uDissipation * texture(uField, coord);
}`,
  // Vorticity / curl: compute scalar curl of velocity (stored in R).
  curl: SFX_HEADER + `
uniform sampler2D uVel;
void main(){
  float l = texture(uVel, vUv - vec2(uTexel.x, 0.0)).y;
  float r = texture(uVel, vUv + vec2(uTexel.x, 0.0)).y;
  float b = texture(uVel, vUv - vec2(0.0, uTexel.y)).x;
  float t = texture(uVel, vUv + vec2(0.0, uTexel.y)).x;
  float c = 0.5 * ((r - l) - (t - b));
  fragColor = vec4(c, 0.0, 0.0, 1.0);
}`,
  // Vorticity confinement: push velocity toward concentrations of curl.
  vorticity: SFX_HEADER + `
uniform sampler2D uVel;
uniform sampler2D uCurl;
uniform float uAmount;
void main(){
  float l = texture(uCurl, vUv - vec2(uTexel.x, 0.0)).x;
  float r = texture(uCurl, vUv + vec2(uTexel.x, 0.0)).x;
  float b = texture(uCurl, vUv - vec2(0.0, uTexel.y)).x;
  float t = texture(uCurl, vUv + vec2(0.0, uTexel.y)).x;
  float c = texture(uCurl, vUv).x;
  vec2 force = 0.5 * vec2(abs(t) - abs(b), abs(r) - abs(l));
  force /= (length(force) + 1e-5);
  force *= uAmount * c;
  force.y *= -1.0;
  vec2 vel = texture(uVel, vUv).xy + force * uDt;
  fragColor = vec4(vel, 0.0, 1.0);
}`,
  // Divergence of the velocity field (stored in R).
  divergence: SFX_HEADER + `
uniform sampler2D uVel;
void main(){
  float l = texture(uVel, vUv - vec2(uTexel.x, 0.0)).x;
  float r = texture(uVel, vUv + vec2(uTexel.x, 0.0)).x;
  float b = texture(uVel, vUv - vec2(0.0, uTexel.y)).y;
  float t = texture(uVel, vUv + vec2(0.0, uTexel.y)).y;
  float div = 0.5 * ((r - l) + (t - b));
  fragColor = vec4(div, 0.0, 0.0, 1.0);
}`,
  // One Jacobi iteration of the pressure Poisson equation.
  pressure: SFX_HEADER + `
uniform sampler2D uPres;
uniform sampler2D uDiv;
void main(){
  float l = texture(uPres, vUv - vec2(uTexel.x, 0.0)).x;
  float r = texture(uPres, vUv + vec2(uTexel.x, 0.0)).x;
  float b = texture(uPres, vUv - vec2(0.0, uTexel.y)).x;
  float t = texture(uPres, vUv + vec2(0.0, uTexel.y)).x;
  float div = texture(uDiv, vUv).x;
  float p = (l + r + b + t - div) * 0.25;
  fragColor = vec4(p, 0.0, 0.0, 1.0);
}`,
  // Subtract the pressure gradient so velocity becomes divergence-free.
  gradient: SFX_HEADER + `
uniform sampler2D uVel;
uniform sampler2D uPres;
void main(){
  float l = texture(uPres, vUv - vec2(uTexel.x, 0.0)).x;
  float r = texture(uPres, vUv + vec2(uTexel.x, 0.0)).x;
  float b = texture(uPres, vUv - vec2(0.0, uTexel.y)).x;
  float t = texture(uPres, vUv + vec2(0.0, uTexel.y)).x;
  vec2 vel = texture(uVel, vUv).xy - 0.5 * vec2(r - l, t - b);
  fragColor = vec4(vel, 0.0, 1.0);
}`,
  // Display: composite the stirred dye over the layer source by intensity.
  display: SFX_HEADER + `
uniform sampler2D uDye;
uniform sampler2D uSrc;
uniform float uIntensity;
void main(){
  vec4 src = texture(uSrc, vUv);
  vec4 dye = texture(uDye, vUv);
  fragColor = mix(src, dye, clamp(uIntensity, 0.0, 1.0));
}`,
};

// The fluid stateful effect definition. `sim` divides the source resolution so
// the solver runs on a coarse grid (cheap + stable); the display pass samples
// the full-res source. Params map to the existing `fluid` template:
//   viscosity (dissipation of velocity), force, fade (dye dissipation),
//   radius (splat size), iterations (Jacobi count), curl (vorticity amount).
const STATEFUL_EFFECTS = {
  fluid: {
    // sim resolution = source long axis capped, to keep the solver coarse.
    simLongAxis(params) {
      // `grid` keeps the legacy control name; default 128 (finer than the CPU 72
      // because the GPU can afford it). Clamp to a sane GPU range.
      return Math.max(32, Math.min(512, Math.round(num(params.grid, 128))));
    },
    textures: {
      vel:  { channels: 2, ping: true,  filter: 'linear', wrap: 'clamp' },
      pres: { channels: 1, ping: true,  filter: 'nearest', wrap: 'clamp' },
      div:  { channels: 1, ping: false, filter: 'nearest', wrap: 'clamp' },
      dye:  { channels: 4, ping: true,  filter: 'linear', wrap: 'clamp' },
      curl: { channels: 1, ping: false, filter: 'nearest', wrap: 'clamp' },
    },
    programs: FLUID_SHADERS,
    display: { program: 'display' },
  },
};

// num(): coerce a param to a finite number with fallback.
function num(v, d) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

// Resolve a declarative uniform descriptor against an effect's params.
// Descriptor shape: { k:'1f'|'1i', from:'<paramName>', def:<number>, bool?:true }
// This is the single contract both this chain and the mmcomposer GLFx use to
// turn a spec's `params` into uniform values, so the param NAMES are canonical.
export function fxUniformValue(u, params) {
  params = params || {};
  if (u.bool) return params[u.from] ? 1 : 0;
  return num(params[u.from], u.def);
}

// Build the full fragment source for a built-in effect.
function buildBuiltinFrag(def) {
  return (
    FRAG_HEADER + GLSL_LIB + (def.decls || '') + def.body +
    `\nvoid main() {\n  vec4 src = texture(uTex, vUv);\n  vec4 fx = fxMain();\n  fragColor = mix(src, fx, clamp(uIntensity, 0.0, 1.0));\n}\n`
  );
}

// Legacy uniform/varying aliases so custom fragments authored against the older
// mmcomposer convention (tex / uv / uRes / o / outColor) still compile against
// this header (uTex / vUv / uResolution / fragColor).
const LEGACY_FX_ALIASES = `#define tex uTex
#define uv vUv
#define uRes uResolution
#define o fragColor
#define outColor fragColor
`;

// Build the full fragment source for a custom effect. Accepts three authoring
// shapes so one custom contract covers every entry point:
//   (a) a fully self-authored shader (its own `#version`) - used verbatim;
//   (b) a full `void main(){…}` using legacy names - wrapped with header+aliases;
//   (c) a bare body that `return`s a vec4 - wrapped as `vec4 fxMain()`.
function buildCustomFrag(glsl) {
  const s = String(glsl || '');
  if (/#version/.test(s)) return s;
  if (/\bvoid\s+main\s*\(/.test(s)) {
    return FRAG_HEADER + LEGACY_FX_ALIASES + GLSL_LIB + '\n' + s;
  }
  return (
    FRAG_HEADER + GLSL_LIB +
    `\nvec4 fxMain() {\n${s}\n}\n` +
    `\nvoid main() {\n  vec4 src = texture(uTex, vUv);\n  vec4 fx = fxMain();\n  fragColor = mix(src, fx, clamp(uIntensity, 0.0, 1.0));\n}\n`
  );
}

// Stable short hash (djb2) of a string - used to key a `custom-stateful` effect's
// per-instance buffers + compiled programs so two distinct custom effects sharing
// the `custom-stateful` type never collide in the instance/program caches.
function hashStr(s) {
  let h = 5381;
  s = String(s);
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

// Build the full fragment source for a STATEFUL program authored declaratively
// (the `custom-stateful` path). The body is written against the SFX_HEADER
// contract (vUv, fragColor, uResolution, uTexel, uTime, uDt already declared);
// the author adds only their own `uniform sampler2D`s + extra uniforms + main().
// A self-versioned shader (its own `#version`) is used verbatim.
function buildStatefulFrag(glsl) {
  const s = String(glsl || '');
  if (/#version/.test(s)) return s;
  return SFX_HEADER + '\n' + s;
}

// ---------------------------------------------------------------------------
// Serializable program specs - the single source of truth shared with other
// runtimes (the mmcomposer editor GLFx + its baked standalone player). Each
// entry is plain JSON (fragment source + declarative uniform list, no
// functions), so it survives JSON.stringify into a baked, self-contained file.
// ---------------------------------------------------------------------------
export function fxProgramSpecs() {
  const out = {};
  for (const type of FX_TYPES) {
    if (type === 'custom') continue;
    const def = EFFECTS[type];
    if (!def) continue;
    out[type] = {
      label: FX_LABELS[type] || type,
      frag: buildBuiltinFrag(def),
      uniforms: Object.keys(def.uniforms || {}).map((name) => ({ name, ...def.uniforms[name] })),
      // Extra texture inputs this effect samples (e.g. a displacement map). The
      // host binds each wired layer buffer to the named sampler; empty for the
      // single-input effects. Plain JSON so it survives the bake into the twin.
      inputs: def.inputs || [],
      // True if this effect reads the per-layer frame-history ring (uHistory).
      // The host allocates/pushes the ring + binds uHistory/uHistDepth/uHistHead.
      history: FX_HISTORY_TYPES.has(type),
    };
  }
  return out;
}
export function fxCustomFrag(glsl) { return buildCustomFrag(glsl); }
export const FX_VERT = VERT;

// ---------------------------------------------------------------------------
// The chain
// ---------------------------------------------------------------------------

export function createFXChain() {
  const canvas =
    typeof OffscreenCanvas !== 'undefined'
      ? new OffscreenCanvas(2, 2)
      : (typeof document !== 'undefined' ? document.createElement('canvas') : null);

  if (!canvas) {
    // No DOM/Offscreen available (e.g. plain node parse). Return a stub so the
    // module still imports cleanly; apply() is a passthrough.
    return stubChain();
  }

  const gl = canvas.getContext('webgl2', {
    premultipliedAlpha: false,
    preserveDrawingBuffer: true,
    antialias: false,
  });

  if (!gl) {
    console.warn('[fx] WebGL2 unavailable; createFXChain returns a passthrough stub.');
    return stubChain();
  }

  let width = 2;
  let height = 2;
  let time = 0;

  // Fullscreen triangle/quad.
  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 3, -1, -1, 3]),
    gl.STATIC_DRAW
  );

  // Vertex shader is shared by all programs.
  const vert = compileShader(gl, gl.VERTEX_SHADER, VERT);

  // Program cache keyed by full fragment source.
  const programs = new Map(); // src -> { program, uniforms:Map }

  // Source texture (uploaded once per apply()).
  const srcTex = gl.createTexture();
  setupTex(gl, srcTex);

  // Ping-pong FBOs.
  const fbos = [makeFBO(gl), makeFBO(gl)];

  // Float-texture support for the stateful subsystem (RGBA16F render targets).
  // EXT_color_buffer_float lets us render TO float textures; without it we fall
  // back to RGBA8 (clamped, lower precision, still works for the fluid solver).
  // HALF_FLOAT (0x140B) sized internal formats are core in WebGL2.
  gl.getExtension('EXT_color_buffer_float');
  const floatLinear = !!gl.getExtension('OES_texture_float_linear');
  const HALF_FLOAT = 0x140B;
  // Probe whether an RGBA16F FBO is actually renderable on this GPU.
  const useFloat = probeFloatRenderable(gl, HALF_FLOAT);

  function ensureSize(w, h) {
    w = Math.max(1, w | 0);
    h = Math.max(1, h | 0);
    if (w === width && h === height) return;
    width = w;
    height = h;
    canvas.width = w;
    canvas.height = h;
    for (const f of fbos) resizeFBO(gl, f, w, h);
  }

  function getProgram(fragSrc) {
    let entry = programs.get(fragSrc);
    if (entry) return entry;
    const frag = compileShader(gl, gl.FRAGMENT_SHADER, fragSrc);
    if (!frag) return null;
    const program = gl.createProgram();
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.bindAttribLocation(program, 0, 'aPos');
    gl.linkProgram(program);
    gl.deleteShader(frag);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.warn('[fx] program link failed:', gl.getProgramInfoLog(program));
      gl.deleteProgram(program);
      return null;
    }
    entry = { program, uniforms: new Map() };
    programs.set(fragSrc, entry);
    return entry;
  }

  function uloc(entry, name) {
    if (entry.uniforms.has(name)) return entry.uniforms.get(name);
    const loc = gl.getUniformLocation(entry.program, name);
    entry.uniforms.set(name, loc);
    return loc;
  }

  // Resolve a single effect spec to a fragment source + a uniform setter.
  function resolveEffect(spec) {
    if (!spec || typeof spec !== 'object') return null;
    const type = spec.type;
    const params = spec.params || {};

    if (type === 'custom') {
      if (typeof spec.glsl !== 'string' || !spec.glsl.trim()) return null;
      const fragSrc = buildCustomFrag(spec.glsl);
      return { fragSrc, def: { uniforms: {} }, params };
    }

    const def = EFFECTS[type];
    if (!def) return null; // unknown -> skip (passthrough)
    return { fragSrc: buildBuiltinFrag(def), def, params };
  }

  function setUniforms(entry, def, params, intensity) {
    gl.uniform1i(uloc(entry, 'uTex'), 0);
    gl.uniform2f(uloc(entry, 'uResolution'), width, height);
    gl.uniform1f(uloc(entry, 'uTime'), time);
    gl.uniform1f(uloc(entry, 'uIntensity'), clamp01(intensity));
    const us = def.uniforms || {};
    for (const name in us) {
      const u = us[name];
      const loc = uloc(entry, name);
      if (loc == null) continue;
      const val = fxUniformValue(u, params);
      if (u.k === '1i') gl.uniform1i(loc, val | 0);
      else gl.uniform1f(loc, val);
    }
  }

  function uploadSource(source) {
    let w = 0, h = 0;
    if (source instanceof ImageData) { w = source.width; h = source.height; }
    else { w = source.width || source.videoWidth || 0; h = source.height || source.videoHeight || 0; }
    ensureSize(w, h);

    gl.bindTexture(gl.TEXTURE_2D, srcTex);
    // Flip so vUv.y matches image-space top-left origin on readback.
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    if (source instanceof ImageData) {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, source.data);
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
    }
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    return { w, h };
  }

  // Render the chain. Leaves the final result in `dstFbo` if given, else in the
  // default framebuffer (the canvas). Returns true on success.
  function renderChain(passes, dstFbo) {
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.viewport(0, 0, width, height);
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);

    let inputTex = srcTex;
    let pingIdx = 0;

    for (let i = 0; i < passes.length; i++) {
      const pass = passes[i];
      const last = i === passes.length - 1;

      // Bind output target.
      if (last) {
        if (dstFbo) gl.bindFramebuffer(gl.FRAMEBUFFER, dstFbo.fbo);
        else gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      } else {
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbos[pingIdx].fbo);
      }

      gl.useProgram(pass.entry.program);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, inputTex);
      setUniforms(pass.entry, pass.def, pass.params, pass.intensity);
      gl.drawArrays(gl.TRIANGLES, 0, 3);

      if (!last) {
        inputTex = fbos[pingIdx].tex;
        pingIdx = 1 - pingIdx;
      }
    }
    return true;
  }

  // Compile/resolve all valid passes from an effects list.
  function compilePasses(effects) {
    const passes = [];
    for (const spec of effects) {
      const resolved = resolveEffect(spec);
      if (!resolved) continue; // unknown/invalid -> skip
      const entry = getProgram(resolved.fragSrc);
      if (!entry) {
        if (spec && spec.type === 'custom')
          console.warn('[fx] custom shader failed to compile; pass skipped.');
        continue;
      }
      passes.push({
        entry,
        def: resolved.def,
        params: resolved.params,
        intensity: spec.intensity == null ? 1 : num(spec.intensity, 1),
      });
    }
    return passes;
  }

  function apply(source, effects) {
    if (!source) return null;
    if (!Array.isArray(effects) || effects.length === 0) {
      return sourceToCanvas(source); // cheap passthrough
    }
    const passes = compilePasses(effects);
    if (passes.length === 0) return sourceToCanvas(source);

    uploadSource(source);
    renderChain(passes, null); // -> draws into `canvas`

    // Copy GL canvas into a plain 2D canvas so callers get a stable, detached
    // result independent of this chain's reused GL canvas.
    return glCanvasToCanvas();
  }

  function applyToImageData(source, effects) {
    if (!source) return null;
    if (!Array.isArray(effects) || effects.length === 0) {
      return sourceToImageData(source);
    }
    const passes = compilePasses(effects);
    if (passes.length === 0) return sourceToImageData(source);

    uploadSource(source);
    renderChain(passes, null);

    const px = new Uint8Array(width * height * 4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, px);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    // readPixels is bottom-up; flip rows to image-space top-down.
    const out = new Uint8ClampedArray(width * height * 4);
    const rowBytes = width * 4;
    for (let y = 0; y < height; y++) {
      const src = (height - 1 - y) * rowBytes;
      out.set(px.subarray(src, src + rowBytes), y * rowBytes);
    }
    return new ImageData(out, width, height);
  }

  // --- result conversions ---
  function glCanvasToCanvas() {
    const out = mk2DCanvas(width, height);
    out.ctx.drawImage(canvas, 0, 0);
    return out.canvas;
  }

  function sourceToCanvas(source) {
    let w, h;
    if (source instanceof ImageData) { w = source.width; h = source.height; }
    else { w = source.width || source.videoWidth; h = source.height || source.videoHeight; }
    const out = mk2DCanvas(w, h);
    if (source instanceof ImageData) out.ctx.putImageData(source, 0, 0);
    else out.ctx.drawImage(source, 0, 0);
    return out.canvas;
  }

  function sourceToImageData(source) {
    if (source instanceof ImageData) return source;
    const w = source.width || source.videoWidth;
    const h = source.height || source.videoHeight;
    const out = mk2DCanvas(w, h);
    out.ctx.drawImage(source, 0, 0);
    return out.ctx.getImageData(0, 0, w, h);
  }

  function resize(w, h) { ensureSize(w, h); }
  function setTime(t) { time = num(t, 0); }

  // =========================================================================
  // STATEFUL SUBSYSTEM RUNTIME
  // =========================================================================
  // Per-stateful-type GLSL programs are compiled once and shared by all
  // instances (keyed by `${type}:${progName}` in the same `programs` cache).
  // Per-instance persistent textures live in `statefulInstances` keyed by
  // instanceId. Each instance carries its own sim size + texture set.
  const statefulInstances = new Map(); // instanceId -> instance record
  // A small upload texture for the stateful source (the layer pixels), separate
  // from `srcTex` so a stateful step never disturbs the stateless path's state.
  let sfxSrcTex = null;
  // A reusable RGBA8 FBO we render the display pass into (then copy to a 2D
  // canvas), independent of `fbos` / `width` / `height` so stateful steps and
  // apply() never collide on the shared ping-pong.
  let sfxOutFBO = null;

  function sfxProgram(type, progName, fragSrc) {
    const key = type + ':' + progName;
    let entry = programs.get(key);
    if (entry) return entry;
    const frag = compileShader(gl, gl.FRAGMENT_SHADER, fragSrc);
    if (!frag) return null;
    const program = gl.createProgram();
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.bindAttribLocation(program, 0, 'aPos');
    gl.linkProgram(program);
    gl.deleteShader(frag);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.warn('[fx] stateful program link failed (' + key + '):', gl.getProgramInfoLog(program));
      gl.deleteProgram(program);
      return null;
    }
    entry = { program, uniforms: new Map() };
    programs.set(key, entry);
    return entry;
  }

  // Allocate ONE sim texture (+ FBO) of the given channel count at sw x sh.
  function makeSimTex(channels, filter, wrap, sw, sh) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    const fmt = simFormat(channels);
    // Linear filtering on float textures requires OES_texture_float_linear; fall
    // back to NEAREST when filtering a float target we cannot linearly sample.
    const usableLinear = filter === 'linear' && (!useFloat || floatLinear);
    const f = usableLinear ? gl.LINEAR : gl.NEAREST;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
    const wmode = wrap === 'repeat' ? gl.REPEAT : gl.CLAMP_TO_EDGE;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wmode);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wmode);
    gl.texImage2D(gl.TEXTURE_2D, 0, fmt.internal, sw, sh, 0, fmt.format, fmt.type, null);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { tex, fbo, channels };
  }

  // Internal/format/type triplet for a sim texture of `channels` components.
  function simFormat(channels) {
    if (useFloat) {
      if (channels === 1) return { internal: gl.R16F,    format: gl.RED,  type: HALF_FLOAT };
      if (channels === 2) return { internal: gl.RG16F,   format: gl.RG,   type: HALF_FLOAT };
      return { internal: gl.RGBA16F, format: gl.RGBA, type: HALF_FLOAT };
    }
    // RGBA8 fallback: pack everything into RGBA8 (single/dual channel waste some
    // components but the math is identical at lower precision).
    if (channels === 1) return { internal: gl.R8,    format: gl.RED,  type: gl.UNSIGNED_BYTE };
    if (channels === 2) return { internal: gl.RG8,   format: gl.RG,   type: gl.UNSIGNED_BYTE };
    return { internal: gl.RGBA8, format: gl.RGBA, type: gl.UNSIGNED_BYTE };
  }

  // Create / fetch / resize an instance's persistent textures for `type`.
  // `def` is the effect definition (STATEFUL_EFFECTS[type] for built-ins, or the
  // spec's inline definition for custom-stateful). `sig` distinguishes two
  // custom-stateful effects that share the type string - a changed sig (different
  // textures/programs) forces a rebuild just like a changed size.
  function ensureStatefulInstance(instanceId, type, def, sw, sh, sig) {
    if (!def) return null;
    let inst = statefulInstances.get(instanceId);
    if (inst && inst.type === type && inst.sig === sig && inst.sw === sw && inst.sh === sh) return inst;
    if (inst) disposeStatefulInstance(inst);   // type/sig/size changed -> rebuild
    inst = { type, sig, sw, sh, tex: {}, frame: 0 };
    for (const name in def.textures) {
      const t = def.textures[name];
      if (t.ping) {
        inst.tex[name] = {
          ping: true,
          a: makeSimTex(t.channels, t.filter, t.wrap, sw, sh),
          b: makeSimTex(t.channels, t.filter, t.wrap, sw, sh),
          cur: 0,
        };
      } else {
        inst.tex[name] = { ping: false, a: makeSimTex(t.channels, t.filter, t.wrap, sw, sh) };
      }
    }
    statefulInstances.set(instanceId, inst);
    return inst;
  }

  // Read side of a ping texture (or the single texture).
  function sfxRead(inst, name) {
    const e = inst.tex[name];
    return e.ping ? (e.cur === 0 ? e.a : e.b) : e.a;
  }
  // Write side of a ping texture (the slot we render INTO this pass).
  function sfxWrite(inst, name) {
    const e = inst.tex[name];
    return e.ping ? (e.cur === 0 ? e.b : e.a) : e.a;
  }
  // Swap a ping texture after a pass that wrote into its write side.
  function sfxSwap(inst, name) {
    const e = inst.tex[name];
    if (e.ping) e.cur = 1 - e.cur;
  }

  // Bind named textures to texture units and set the matching sampler uniforms.
  // `binds` is [{ name:samplerUniform, tex:<GLTexture | {tex:GLTexture}> }] - the
  // `tex` may be a raw GL texture (uSrc) OR a sim-texture record (sfxRead returns
  // { tex, fbo }); we unwrap the record so both forms work.
  function sfxBindSamplers(prog, binds) {
    for (let u = 0; u < binds.length; u++) {
      gl.activeTexture(gl.TEXTURE0 + u);
      const t = binds[u].tex;
      gl.bindTexture(gl.TEXTURE_2D, (t && t.tex !== undefined) ? t.tex : t);
      const loc = sfxUloc(prog, binds[u].name);
      if (loc != null) gl.uniform1i(loc, u);
    }
  }
  function sfxUloc(entry, name) {
    if (entry.uniforms.has(name)) return entry.uniforms.get(name);
    const loc = gl.getUniformLocation(entry.program, name);
    entry.uniforms.set(name, loc);
    return loc;
  }

  // Run one fullscreen stateful pass: program, output FBO, sampler binds, and a
  // uniform setter callback that receives (gl, prog, sfxUloc).
  function sfxPass(prog, outFBO, sw, sh, binds, setUniforms) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, outFBO);
    gl.viewport(0, 0, sw, sh);
    gl.useProgram(prog.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(sfxUloc(prog, 'uResolution'), sw, sh);
    gl.uniform2f(sfxUloc(prog, 'uTexel'), 1 / sw, 1 / sh);
    gl.uniform1f(sfxUloc(prog, 'uTime'), time);
    if (setUniforms) setUniforms(prog);
    sfxBindSamplers(prog, binds);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  // The public step. Returns a 2D canvas (or draws into opts.target) or null on
  // failure / unknown type (caller may then fall back to a CPU path).
  function stepStateful(instanceId, type, opts) {
    // Built-in stateful effects resolve their def from the static registry; a
    // `custom-stateful` effect carries its serializable def inline on the spec
    // (opts.def), so a per-project effect node can ship a brand-new stateful
    // effect with NO engine change.
    const custom = type === 'custom-stateful';
    const def = custom ? (opts && opts.def) : STATEFUL_EFFECTS[type];
    if (!def || !opts || !opts.source) return null;
    const source = opts.source;
    // Output (display) resolution = source resolution.
    let ow = 0, oh = 0;
    if (source instanceof ImageData) { ow = source.width; oh = source.height; }
    else { ow = source.width || source.videoWidth || 0; oh = source.height || source.videoHeight || 0; }
    if (ow < 2 || oh < 2) return null;

    // Sim resolution. Built-ins (fluid) downscale to a coarse solver grid via
    // simLongAxis(). A declarative def may set `sim` to a long-axis cap, or leave
    // it 0/absent to run at FULL source resolution - image-fidelity effects like
    // a per-row delay need every real row, not a coarse grid.
    const params = opts.params || {};
    let simCap = 0;
    if (def.simLongAxis) simCap = def.simLongAxis(params);
    else if (typeof def.sim === 'number') simCap = def.sim;
    let sw, sh;
    if (simCap && simCap > 0) {
      if (ow >= oh) { sw = simCap; sh = Math.max(8, Math.round(simCap * oh / ow)); }
      else { sh = simCap; sw = Math.max(8, Math.round(simCap * ow / oh)); }
    } else {
      sw = ow; sh = oh;
    }

    // A custom-stateful def shares the `custom-stateful` type string, so key its
    // instance buffers + programs by a hash of its textures + programs.
    const sig = custom
      ? hashStr(JSON.stringify(def.textures || {}) + '|' + JSON.stringify(def.programs || {}))
      : type;
    const inst = ensureStatefulInstance(instanceId, type, def, sw, sh, sig);
    if (!inst) return null;

    // Upload the layer source into a dedicated texture.
    if (!sfxSrcTex) { sfxSrcTex = gl.createTexture(); setupTex(gl, sfxSrcTex); }
    gl.bindTexture(gl.TEXTURE_2D, sfxSrcTex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    if (source instanceof ImageData) {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, ow, oh, 0, gl.RGBA, gl.UNSIGNED_BYTE, source.data);
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
    }
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);

    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);

    const dt = Math.min(0.033, Math.max(0.0005, num(opts.dt, 1 / 60)));
    const ptr = opts.pointer || {};
    const seed = inst.frame === 0 ? 1 : 0.06;

    // Dispatch the per-step pass orchestration: the hand-written fluid solver, or
    // the GENERIC declarative runner for any def that carries a `passes` list.
    if (type === 'fluid') {
      runFluidPasses(inst, type, def, params, opts, ptr, dt, seed, sw, sh);
    } else if (Array.isArray(def.passes)) {
      runDeclarativePasses(inst, sig, def, params, ptr, dt, sw, sh);
    }
    inst.frame++;

    // DISPLAY pass -> RGBA8 output FBO at output (source) resolution.
    if (!sfxOutFBO || sfxOutFBO.w !== ow || sfxOutFBO.h !== oh) {
      if (sfxOutFBO) { gl.deleteFramebuffer(sfxOutFBO.fbo); gl.deleteTexture(sfxOutFBO.tex); }
      sfxOutFBO = makeRGBA8FBO(gl, ow, oh);
    }
    const dispName = def.display && def.display.program;
    const dispFrag = custom ? buildStatefulFrag(def.programs[dispName]) : (dispName ? def.programs[dispName] : null);
    const disp = dispName ? sfxProgram(sig, dispName, dispFrag) : null;
    if (disp) {
      const intensity = clamp01(opts.intensity == null ? 1 : opts.intensity);
      if (Array.isArray(def.display.inputs)) {
        // Generic display: bind declared inputs ('source' -> the layer pixels,
        // any other name -> that persistent texture's read side).
        const binds = def.display.inputs.map((b) => ({
          name: b.sampler,
          tex: b.tex === 'source' ? sfxSrcTex : sfxRead(inst, b.tex),
        }));
        sfxPass(disp, sfxOutFBO.fbo, ow, oh, binds, (prog) => {
          applyDeclUniforms(prog, def.display, params, ptr, dt);
          gl.uniform1f(sfxUloc(prog, 'uIntensity'), intensity);
        });
      } else {
        // Built-in fluid display (uSrc + uDye), unchanged.
        sfxPass(disp, sfxOutFBO.fbo, ow, oh,
          [{ name: 'uSrc', tex: sfxSrcTex }, { name: 'uDye', tex: sfxRead(inst, 'dye') }],
          (prog) => {
            gl.uniform1f(sfxUloc(prog, 'uDt'), dt);
            gl.uniform1f(sfxUloc(prog, 'uIntensity'), intensity);
          });
      }
    }

    // Read the output FBO into a 2D canvas (flip rows: GL is bottom-up).
    return sfxReadToCanvas(ow, oh, opts.target);
  }

  // Fluid solver pass orchestration (Stam stable-fluids on the GPU).
  function runFluidPasses(inst, type, def, params, opts, ptr, dt, seed, sw, sh) {
    const P = (name) => sfxProgram(type, name, def.programs[name]);
    // 1) seed dye from the layer source.
    {
      const pr = P('seedDye'); if (!pr) return;
      sfxPass(pr, sfxWrite(inst, 'dye').fbo, sw, sh,
        [{ name: 'uDye', tex: sfxRead(inst, 'dye') }, { name: 'uSrc', tex: sfxSrcTex }],
        (prog) => { gl.uniform1f(sfxUloc(prog, 'uDt'), dt); gl.uniform1f(sfxUloc(prog, 'uSeed'), seed); });
      sfxSwap(inst, 'dye');
    }
    // 2) splat pointer velocity (only while the pointer is over the stage).
    if (ptr.hover || ptr.down) {
      const pr = P('splatVel');
      if (pr) {
        const force = num(params.force, 1) * 6.0;
        // dx/dy are per-frame normalised pointer deltas; scale into velocity.
        const fx = num(ptr.dx, 0) * force;
        const fy = num(ptr.dy, 0) * force;
        const radius = Math.max(0.01, num(params.radius, 0.12)) * 0.5;
        sfxPass(pr, sfxWrite(inst, 'vel').fbo, sw, sh,
          [{ name: 'uVel', tex: sfxRead(inst, 'vel') }],
          (prog) => {
            gl.uniform1f(sfxUloc(prog, 'uDt'), dt);
            gl.uniform2f(sfxUloc(prog, 'uPoint'), clamp01(num(ptr.x, 0.5)), clamp01(num(ptr.y, 0.5)));
            gl.uniform2f(sfxUloc(prog, 'uForce'), fx, fy);
            gl.uniform1f(sfxUloc(prog, 'uRadius'), radius);
          });
        sfxSwap(inst, 'vel');
      }
    }
    // 3) advect velocity by itself (viscosity acts as velocity dissipation).
    {
      const pr = P('advect'); if (!pr) return;
      const velDiss = 1 - Math.min(0.5, Math.max(0, num(params.viscosity, 0.2))) * 0.5;
      sfxPass(pr, sfxWrite(inst, 'vel').fbo, sw, sh,
        [{ name: 'uVel', tex: sfxRead(inst, 'vel') }, { name: 'uField', tex: sfxRead(inst, 'vel') }],
        (prog) => { gl.uniform1f(sfxUloc(prog, 'uDt'), dt); gl.uniform1f(sfxUloc(prog, 'uDissipation'), velDiss); });
      sfxSwap(inst, 'vel');
    }
    // 4) optional vorticity confinement (curl -> vorticity force).
    const curlAmt = num(params.curl, 0);
    if (curlAmt > 0) {
      const cp = P('curl');
      if (cp) {
        sfxPass(cp, inst.tex.curl.a.fbo, sw, sh,
          [{ name: 'uVel', tex: sfxRead(inst, 'vel') }],
          (prog) => gl.uniform1f(sfxUloc(prog, 'uDt'), dt));
        const vp = P('vorticity');
        if (vp) {
          sfxPass(vp, sfxWrite(inst, 'vel').fbo, sw, sh,
            [{ name: 'uVel', tex: sfxRead(inst, 'vel') }, { name: 'uCurl', tex: inst.tex.curl.a.tex }],
            (prog) => { gl.uniform1f(sfxUloc(prog, 'uDt'), dt); gl.uniform1f(sfxUloc(prog, 'uAmount'), curlAmt); });
          sfxSwap(inst, 'vel');
        }
      }
    }
    // 5) divergence.
    {
      const pr = P('divergence'); if (!pr) return;
      sfxPass(pr, inst.tex.div.a.fbo, sw, sh,
        [{ name: 'uVel', tex: sfxRead(inst, 'vel') }],
        (prog) => gl.uniform1f(sfxUloc(prog, 'uDt'), dt));
    }
    // 6) pressure Jacobi x iterations (default 24). Clear pressure first.
    {
      const pr = P('pressure'); if (!pr) return;
      // zero the read side of pressure so the solve starts from 0.
      clearFBO(sfxRead(inst, 'pres').fbo, sw, sh);
      const iters = Math.max(1, Math.min(60, Math.round(num(opts.iterations, num(params.iterations, 24)))));
      for (let k = 0; k < iters; k++) {
        sfxPass(pr, sfxWrite(inst, 'pres').fbo, sw, sh,
          [{ name: 'uPres', tex: sfxRead(inst, 'pres') }, { name: 'uDiv', tex: inst.tex.div.a.tex }],
          (prog) => gl.uniform1f(sfxUloc(prog, 'uDt'), dt));
        sfxSwap(inst, 'pres');
      }
    }
    // 7) subtract pressure gradient (velocity becomes ~divergence-free).
    {
      const pr = P('gradient'); if (!pr) return;
      sfxPass(pr, sfxWrite(inst, 'vel').fbo, sw, sh,
        [{ name: 'uVel', tex: sfxRead(inst, 'vel') }, { name: 'uPres', tex: sfxRead(inst, 'pres') }],
        (prog) => gl.uniform1f(sfxUloc(prog, 'uDt'), dt));
      sfxSwap(inst, 'vel');
    }
    // 8) advect dye by the divergence-free velocity, fade by `fade`.
    {
      const pr = P('advect'); if (!pr) return;
      const dyeDiss = 1 - Math.min(0.5, Math.max(0, num(params.fade, 0.04)));
      sfxPass(pr, sfxWrite(inst, 'dye').fbo, sw, sh,
        [{ name: 'uVel', tex: sfxRead(inst, 'vel') }, { name: 'uField', tex: sfxRead(inst, 'dye') }],
        (prog) => { gl.uniform1f(sfxUloc(prog, 'uDt'), dt); gl.uniform1f(sfxUloc(prog, 'uDissipation'), dyeDiss); });
      sfxSwap(inst, 'dye');
    }
  }

  // Generic declarative stateful runner - the engine side of `custom-stateful`.
  // Turns a SERIALIZABLE spec (textures + GLSL program strings + an ordered pass
  // list) into the exact ping-pong FBO orchestration runFluidPasses does by hand,
  // so a brand-new stateful effect needs ZERO engine code. Each pass:
  //   { program, output, inputs:[{sampler,tex}], uniforms:[{name,from,def,bool,k}],
  //     swap?:bool (default true), when?:'always'|'pointer' }
  // `tex` resolves 'source' -> the layer pixels, else a persistent texture name.
  // Use a ping texture for feedback (read + write the same buffer); a single
  // (non-ping) texture must not be both an input and the output of one pass.
  function runDeclarativePasses(inst, sig, def, params, ptr, dt, sw, sh) {
    const passes = def.passes || [];
    for (let i = 0; i < passes.length; i++) {
      const p = passes[i];
      if (!p || !p.program || !p.output || !inst.tex[p.output]) continue;
      if (p.when === 'pointer' && !(ptr.hover || ptr.down)) continue;
      const prog = sfxProgram(sig, p.program, buildStatefulFrag(def.programs[p.program]));
      if (!prog) continue;
      const binds = (p.inputs || []).map((b) => ({
        name: b.sampler,
        tex: b.tex === 'source' ? sfxSrcTex : sfxRead(inst, b.tex),
      }));
      sfxPass(prog, sfxWrite(inst, p.output).fbo, sw, sh, binds,
        (prg) => applyDeclUniforms(prg, p, params, ptr, dt));
      if (p.swap !== false) sfxSwap(inst, p.output); // advances a ping; no-op for single
    }
  }

  // Set the standard stateful uniforms (uDt + pointer) plus a descriptor's own
  // declarative uniforms (resolved from `params` via fxUniformValue) on `prog`.
  // A uniform the shader does not declare resolves to a null location and is
  // silently ignored by GL, so over-setting is safe.
  function applyDeclUniforms(prog, descr, params, ptr, dt) {
    gl.uniform1f(sfxUloc(prog, 'uDt'), num(dt, 1 / 60));
    gl.uniform2f(sfxUloc(prog, 'uPointer'), clamp01(num(ptr.x, 0.5)), clamp01(num(ptr.y, 0.5)));
    gl.uniform2f(sfxUloc(prog, 'uPointerDelta'), num(ptr.dx, 0), num(ptr.dy, 0));
    gl.uniform1f(sfxUloc(prog, 'uDown'), ptr.down ? 1 : 0);
    gl.uniform1f(sfxUloc(prog, 'uHover'), ptr.hover ? 1 : 0);
    const us = (descr && descr.uniforms) || [];
    for (let i = 0; i < us.length; i++) {
      const u = us[i];
      if (!u || !u.name) continue;
      const loc = sfxUloc(prog, u.name);
      if (loc == null) continue;
      const v = fxUniformValue(u, params);
      if (u.k === '1i') gl.uniform1i(loc, v | 0);
      else gl.uniform1f(loc, v);
    }
  }

  // bottom-up readPixels -> top-down 2D canvas (or provided target).
  function sfxReadToCanvas(w, h, target) {
    const px = new Uint8Array(w * h * 4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, sfxOutFBO.fbo);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    const out = new Uint8ClampedArray(w * h * 4);
    const rowBytes = w * 4;
    for (let y = 0; y < h; y++) {
      const src = (h - 1 - y) * rowBytes;
      out.set(px.subarray(src, src + rowBytes), y * rowBytes);
    }
    const id = new ImageData(out, w, h);
    let cv, ctx;
    if (target && target.getContext) { cv = target; if (cv.width !== w) cv.width = w; if (cv.height !== h) cv.height = h; ctx = cv.getContext('2d'); }
    else { const m = mk2DCanvas(w, h); cv = m.canvas; ctx = m.ctx; }
    ctx.putImageData(id, 0, 0);
    return cv;
  }

  function clearFBO(fbo, w, h) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }

  function disposeStatefulInstance(inst) {
    for (const name in inst.tex) {
      const e = inst.tex[name];
      gl.deleteTexture(e.a.tex); gl.deleteFramebuffer(e.a.fbo);
      if (e.ping) { gl.deleteTexture(e.b.tex); gl.deleteFramebuffer(e.b.fbo); }
    }
  }
  function disposeStateful(instanceId) {
    const inst = statefulInstances.get(instanceId);
    if (!inst) return;
    disposeStatefulInstance(inst);
    statefulInstances.delete(instanceId);
  }
  function hasStateful(type) { return type === 'custom-stateful' || !!STATEFUL_EFFECTS[type]; }
  function statefulAvailable() { return true; }

  function dispose() {
    for (const { program } of programs.values()) gl.deleteProgram(program);
    programs.clear();
    for (const f of fbos) { gl.deleteFramebuffer(f.fbo); gl.deleteTexture(f.tex); }
    for (const inst of statefulInstances.values()) disposeStatefulInstance(inst);
    statefulInstances.clear();
    if (sfxSrcTex) gl.deleteTexture(sfxSrcTex);
    if (sfxOutFBO) { gl.deleteFramebuffer(sfxOutFBO.fbo); gl.deleteTexture(sfxOutFBO.tex); }
    gl.deleteTexture(srcTex);
    gl.deleteBuffer(quad);
    gl.deleteShader(vert);
  }

  return {
    apply, applyToImageData, resize, dispose, setTime,
    stepStateful, disposeStateful, hasStateful, statefulAvailable,
  };
}

// ---------------------------------------------------------------------------
// GL helpers
// ---------------------------------------------------------------------------

function compileShader(gl, type, src) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    console.warn('[fx] shader compile failed:', gl.getShaderInfoLog(sh), '\n', src);
    gl.deleteShader(sh);
    return null;
  }
  return sh;
}

function setupTex(gl, tex) {
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
}

function makeFBO(gl) {
  const tex = gl.createTexture();
  setupTex(gl, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  const fbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  return { fbo, tex, w: 1, h: 1 };
}

function resizeFBO(gl, f, w, h) {
  if (f.w === w && f.h === h) return;
  f.w = w; f.h = h;
  gl.bindTexture(gl.TEXTURE_2D, f.tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  gl.bindTexture(gl.TEXTURE_2D, null);
}

// A plain RGBA8 FBO at w x h (used for the stateful display output). Carries its
// size so the caller can decide whether to reallocate on resize.
function makeRGBA8FBO(gl, w, h) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  const fbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  return { fbo, tex, w, h };
}

// Probe whether a small RGBA16F texture is actually framebuffer-complete here.
// Returns false on GPUs that report the extension but cannot render to float.
function probeFloatRenderable(gl, halfFloatType) {
  try {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, 4, 4, 0, gl.RGBA, halfFloatType, null);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.deleteFramebuffer(fbo);
    gl.deleteTexture(tex);
    return ok;
  } catch (_e) {
    return false;
  }
}

function clamp01(v) {
  v = Number(v);
  if (!Number.isFinite(v)) return 1;
  return v < 0 ? 0 : v > 1 ? 1 : v;
}

function mk2DCanvas(w, h) {
  w = Math.max(1, w | 0);
  h = Math.max(1, h | 0);
  const canvas =
    typeof OffscreenCanvas !== 'undefined' && typeof document === 'undefined'
      ? new OffscreenCanvas(w, h)
      : document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  return { canvas, ctx };
}

// Passthrough stub for environments without WebGL2.
function stubChain() {
  return {
    apply(source) {
      if (!source) return null;
      try { return passthroughCanvas(source); } catch (_e) { return null; }
    },
    applyToImageData(source) {
      if (!source) return null;
      if (source instanceof ImageData) return source;
      try { return passthroughImageData(source); } catch (_e) { return null; }
    },
    resize() {},
    dispose() {},
    setTime() {},
    // Stateful subsystem: unavailable on the stub. stepStateful returns null so
    // the caller falls back to its CPU implementation; the other methods are
    // present (no-op) so the API surface matches the real chain.
    stepStateful() { return null; },
    disposeStateful() {},
    hasStateful(type) { return type === 'custom-stateful' || !!STATEFUL_EFFECTS[type]; },
    statefulAvailable() { return false; },
  };
}

function passthroughCanvas(source) {
  let w, h;
  if (source instanceof ImageData) { w = source.width; h = source.height; }
  else { w = source.width || source.videoWidth; h = source.height || source.videoHeight; }
  const out = mk2DCanvas(w, h);
  if (source instanceof ImageData) out.ctx.putImageData(source, 0, 0);
  else out.ctx.drawImage(source, 0, 0);
  return out.canvas;
}

function passthroughImageData(source) {
  const w = source.width || source.videoWidth;
  const h = source.height || source.videoHeight;
  const out = mk2DCanvas(w, h);
  out.ctx.drawImage(source, 0, 0);
  return out.ctx.getImageData(0, 0, w, h);
}

// ---------------------------------------------------------------------------
// Optional self-test (no-op unless window.__FX_SELFTEST is set).
// ---------------------------------------------------------------------------
if (typeof window !== 'undefined' && window.__FX_SELFTEST) {
  try {
    const src = mk2DCanvas(2, 2);
    src.ctx.fillStyle = '#f00'; src.ctx.fillRect(0, 0, 1, 2);
    src.ctx.fillStyle = '#0f0'; src.ctx.fillRect(1, 0, 1, 2);
    const chain = createFXChain();
    const out = chain.apply(src.canvas, [
      { type: 'posterize', intensity: 1, params: { levels: 3 } },
      { type: 'chromatic-aberration', intensity: 0.5, params: { amount: 0.1 } },
      { type: 'custom', intensity: 1, glsl: 'return texture(uTex, vUv);' },
      { type: 'this-type-does-not-exist', intensity: 1 }, // skipped
    ]);
    const id = chain.applyToImageData(src.canvas, [{ type: 'edge-detect', intensity: 1 }]);
    chain.dispose();
    // eslint-disable-next-line no-console
    console.log('[fx] selftest ok', out && out.width, id && id.width);
  } catch (e) {
    // eslint-disable-next-line no-console
    console.warn('[fx] selftest failed', e);
  }
}
