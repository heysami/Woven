# Subagent 1.V.shader - Asset drawer (medium: GLSL fragment shader)

You own **ONE asset** of medium `shader` - a decorative background loop, ambient gradient wash, aurora, noise field, or generative pattern that runs in WebGL. **Pathway B**: you write the GLSL fragment shader directly.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","shader-skill"]
nodeIds: { prompt, skill, asset }
```

Slot is typically a `<div data-shader="…">` or a `<canvas data-webgl="…">`.

**You ship the runtime, not just the shader.** There is NO host mount loop in a built prototype - `window.mountShader` and the editor's canvas runtime exist ONLY inside the editor app, never in the page a user opens. A prototype "opens by double-clicking" (`file://`), so the mount cannot `fetch()` the `.glsl` either. Therefore the shader is DEAD unless YOUR `slotEditDiff` inlines a self-contained mount: the `<canvas>` + an inline `<script>` that carries the fragment source as a string, compiles it against the standard fullscreen-triangle vertex shader, binds `iResolution` / `iTime` / `iMouse` (shadertoy-compatible), and drives a rAF loop. Self-contained per slot is the contract - do not rely on any shared/global runtime, and do not fight the page's existing scripts.

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<1-sentence design intent>",
  "skillCode": "<the full GLSL fragment shader source>",
  "params": {
    "outputPath": "<slot.outputPath e.g. assets/shaders/hero-aurora.glsl>",
    "uniforms": ["iResolution", "iTime"],
    "performance": "background" | "hero"
  },
  "slotEditDiff": "<REQUIRED - the self-contained canvas + inline mount script (see §6)>"
}
```

`skillCode` (the raw `.glsl` at `outputPath`) is the editable source-of-truth the editor + re-runs read. But it is NOT what makes the page work - `slotEditDiff` is, because it inlines that same source into a running mount. `slotEditDiff` is REQUIRED for this medium; a shader asset with `slotEditDiff: null` ships a dead canvas and fails self-audit.

## Recipe

### 1. Read slot + genre

Same start as the other drawers. The shader-allowed genres (Marketing, Bento, Editorial in limited cases) all have different visual languages - pick the right one:

| Genre | Allowed shader vocabulary |
|---|---|
| Marketing / consumer | Aurora gradients, noise washes, animated grain, hue cycles, soft bokeh |
| Bento / Apple-style | Subtle per-cell gradients, gentle parallax noise, no aggressive motion |
| Editorial | One section divider at most - gentle paper-grain or scan-line wash. No color shift. |

### 2. Write the fragment shader

Shadertoy-compatible structure, GLSL ES 1.00 (broad WebGL1 compatibility) or GLSL ES 3.00 if the runtime explicitly supports it. Default to 1.00:

```glsl
precision mediump float;

uniform vec3  iResolution;   // px width, px height, aspect
uniform float iTime;          // seconds since mount
uniform vec4  iMouse;         // xy = last pos, zw = last click

// ---- helpers ----
float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i + vec2(0,0)), hash(i + vec2(1,0)), u.x),
    mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x),
    u.y);
}

// ---- main ----
void main() {
  vec2 uv = gl_FragCoord.xy / iResolution.xy;
  vec2 p  = (uv - 0.5) * vec2(iResolution.x / iResolution.y, 1.0);

  // your composition here - see "Composition primitives" below

  vec3 col = vec3(0.0);
  // …
  gl_FragColor = vec4(col, 1.0);
}
```

If the runtime is shadertoy-style with `void mainImage(out vec4 fragColor, in vec2 fragCoord)`, use that signature instead and let the host's wrapper supply `gl_FragColor`.

### 3. Composition primitives (recall, don't compute)

| Effect | Recipe |
|---|---|
| Soft gradient wash | `mix(colA, colB, smoothstep(0.0, 1.0, uv.y + 0.1 * sin(iTime * 0.2)))` |
| Aurora | Two value-noise layers at different scales, additively blended into a hue-shifted palette: `vec3 col = palette(noise(p * 2.0 + iTime * 0.05) + noise(p * 6.0 + iTime * 0.1))` |
| Animated grain | `noise(gl_FragCoord.xy + iTime * 60.0) * 0.05` added to final color |
| Drift particles (in shader) | N circles at `vec2(hash(seed * i), hash(seed * i * 2.) + iTime * 0.1)` summed with `smoothstep`-based discs |
| Scan-line wash | `sin(uv.y * iResolution.y * 0.5) * 0.04` added to brightness |
| Color cycle | `palette(t)` helper where `t = fract(iTime * 0.05 + uv.x * 0.1)` and palette is IQ's cosine palette |

### 4. Performance budget

The slot's `performance` flag tells you how aggressive to be:

| Performance | Pixel budget | Constraints |
|---|---|---|
| `background` | Cheap - runs on every page | ≤30 ALU ops per pixel, no loops > 4 iter, no derivatives, no `texture()` lookups |
| `hero` | One-time hero | Up to 200 ALU ops, loops up to 32 iter, may sample one input texture |

If unsure, default to `background` - slower iteration is better than a stuttering preview.

### 5. Palette - anchor to tokens

The prototype's `:root` color tokens are the truth source. Open `styles.css :root` and convert the two or three colors you need into vec3 literals:

```glsl
// --accent: oklch(48% 0.13 252)  ≈ rgb(0.27, 0.42, 0.68) in linear sRGB
const vec3 ACCENT  = vec3(0.27, 0.42, 0.68);
const vec3 SURFACE = vec3(0.97, 0.97, 0.97);
```

Hardcoding palette in the shader is acceptable; the alternative (passing tokens as uniforms) requires runtime plumbing this medium doesn't have.

### 6. Output file + self-contained mount (REQUIRED)

Two writes, both mandatory:

**(a) The editable source.** Write the shader source to `slot.outputPath` (e.g. `assets/shaders/hero-aurora.glsl`). This is what the editor's asset-controls and a re-run read to regenerate. It does NOT run on its own.

**(b) The self-contained mount.** Emit a `slotEditDiff` that replaces the slot with a `<canvas>` plus an inline `<script>` that carries the SAME fragment source (inlined as a string - no `fetch`, the page opens via `file://`) and a minimal WebGL bootstrap. Nothing external, nothing global. This is what actually renders in the shipped page.

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"hero-bg\"></div>",
  "replace": "<canvas class=\"hero-bg\" data-shader=\"hero-aurora\"></canvas>\n<script>\n(function(){\n  var cvs=document.currentScript.previousElementSibling;\n  var gl=cvs.getContext('webgl');if(!gl)return;\n  var FRAG=`<PASTE THE EXACT FRAGMENT SOURCE FROM outputPath HERE>`;\n  var VERT='attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';\n  function sh(t,s){var o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);return o;}\n  var pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,VERT));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,FRAG));gl.linkProgram(pr);gl.useProgram(pr);\n  var b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);\n  var lp=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(lp);gl.vertexAttribPointer(lp,2,gl.FLOAT,false,0,0);\n  var uR=gl.getUniformLocation(pr,'iResolution'),uT=gl.getUniformLocation(pr,'iTime'),uM=gl.getUniformLocation(pr,'iMouse');\n  var mx=0,my=0;cvs.addEventListener('pointermove',function(e){var r=cvs.getBoundingClientRect();mx=(e.clientX-r.left);my=(r.height-(e.clientY-r.top));});\n  function size(){var r=cvs.getBoundingClientRect();cvs.width=r.width*devicePixelRatio;cvs.height=r.height*devicePixelRatio;gl.viewport(0,0,cvs.width,cvs.height);}\n  addEventListener('resize',size);size();\n  var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches,vis=true;\n  document.addEventListener('visibilitychange',function(){vis=!document.hidden;});\n  var t0=performance.now();\n  function frame(now){requestAnimationFrame(frame);if(!vis)return;var t=reduce?0:(now-t0)/1000;\n    gl.uniform3f(uR,cvs.width,cvs.height,cvs.width/cvs.height);gl.uniform1f(uT,t);gl.uniform4f(uM,mx,my,0,0);\n    gl.drawArrays(gl.TRIANGLES,0,3);}\n  requestAnimationFrame(frame);\n})();\n</script>"
}
```

Adapt the template to the slot's real markup (tag, classes, `id`). Keep it a background: give the `<canvas>` the same CSS box the placeholder had (usually `position:absolute;inset:0;width:100%;height:100%;z-index:0`) so UI on top still reads. If your fragment uses the shadertoy `mainImage` signature, append a `void main(){mainImage(gl_FragColor,gl_FragCoord.xy);}` wrapper to `FRAG`. Under `prefers-reduced-motion` the loop freezes `iTime` at 0 (a still frame) rather than stopping - a blank canvas is worse than a static one.

## Self-audit

- [ ] Genre allows shader medium (Marketing / Bento / limited Editorial).
- [ ] Shader compiles in WebGL1 (no GLSL ES 3.00 features unless runtime is confirmed).
- [ ] Palette is anchored to `--accent` / `--surface` from `styles.css :root`, not invented.
- [ ] No `texture()` lookups unless `performance: hero`.
- [ ] No `dFdx` / `dFdy` (WebGL1 needs the `OES_standard_derivatives` extension; assume unavailable).
- [ ] Loops bounded by compile-time constants (no `while(true)`).
- [ ] Final `gl_FragColor.a` is `1.0` unless the slot explicitly composites (rare).
- [ ] Shader is written to `slot.outputPath` (editable source).
- [ ] `slotEditDiff` inlines a self-contained `<canvas>` + `<script>` mount with the fragment source pasted in - NOT a `data-shader` attribute pointing at an external runtime that does not ship. The page must render the shader when opened directly via `file://` (no `fetch`, no host runtime, no external `<script src>`).
- [ ] The inlined `FRAG` string is byte-identical to what I wrote at `outputPath` (no drift between source and shipped copy).
- [ ] Canvas is positioned as a background (behind UI) and freezes `iTime` under `prefers-reduced-motion`.
- [ ] Adjustable controls exposed via the asset-controls shim (tint/accent color, speed, scale, intensity - 3-6 knobs), per `../asset-controls-contract.md`. Each `apply(v)` writes the matching uniform.

## Don't

- Don't use shader recipes that ignore the genre's restraint. Linear/Vercel/Bloomberg are not allowed to have shaders - your envelope is wrong if you got one of these. Return `error: "genre forbids shader medium"`.
- Don't write a shader that's beautiful in isolation but fights the UI on top of it. The shader is a background - it should support, not compete.
- Don't request input textures unless your runtime confirmed `texture()` support.
- Don't animate so fast that the user's eye is pulled to the background. Decoration is supposed to be felt, not noticed.
