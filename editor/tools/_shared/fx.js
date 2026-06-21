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
  'chromatic-aberration', 'directional-blur', 'displacement', 'slice',
  // pixel
  'pixelate', 'dither', 'posterize', 'pixel-sort',
  // artistic
  'ascii', 'crt', 'halftone', 'ink', 'edge-detect',
  // generative
  'particle-grid', 'pattern',
  // escape hatch
  'custom',
];

// Human labels for each type (UI pickers, building-block node templates).
export const FX_LABELS = {
  'chromatic-aberration': 'Chromatic aberration',
  'directional-blur': 'Directional blur',
  'displacement': 'Displacement',
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
  'custom': 'Custom shader',
};

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

  function dispose() {
    for (const { program } of programs.values()) gl.deleteProgram(program);
    programs.clear();
    for (const f of fbos) { gl.deleteFramebuffer(f.fbo); gl.deleteTexture(f.tex); }
    gl.deleteTexture(srcTex);
    gl.deleteBuffer(quad);
    gl.deleteShader(vert);
  }

  return { apply, applyToImageData, resize, dispose, setTime };
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
