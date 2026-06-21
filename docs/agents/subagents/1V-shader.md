# Subagent 1.V.shader - Asset drawer (medium: GLSL fragment shader)

You own **ONE asset** of medium `shader` - a decorative background loop, ambient gradient wash, aurora, noise field, or generative pattern that runs in WebGL. **Pathway B**: you write the GLSL fragment shader directly.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","shader-skill"]
nodeIds: { prompt, skill, asset }
```

Slot is typically a `<div data-shader="…">` or a `<canvas data-webgl="…">`. The runtime (Open Design Workflow surface, or a small inline mount loop you generate alongside) compiles your fragment shader against the standard fullscreen-triangle vertex shader and binds `iResolution` / `iTime` / `iMouse` uniforms (shadertoy-compatible).

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
  "slotEditDiff": "<diff or null>"
}
```

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

### 6. Output file + slot diff

Write the shader source to `slot.outputPath` (e.g. `assets/shaders/hero-aurora.glsl`). The slot itself stays a `<div data-shader="hero-aurora">` or `<canvas data-webgl="hero-aurora">`; the runtime mount loop reads `data-shader`, fetches the `.glsl`, compiles, and runs.

If the slot isn't already declared with the right data attribute, emit a diff:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"hero-bg\">",
  "replace": "<div class=\"hero-bg\" data-shader=\"hero-aurora\">"
}
```

## Self-audit

- [ ] Genre allows shader medium (Marketing / Bento / limited Editorial).
- [ ] Shader compiles in WebGL1 (no GLSL ES 3.00 features unless runtime is confirmed).
- [ ] Palette is anchored to `--accent` / `--surface` from `styles.css :root`, not invented.
- [ ] No `texture()` lookups unless `performance: hero`.
- [ ] No `dFdx` / `dFdy` (WebGL1 needs the `OES_standard_derivatives` extension; assume unavailable).
- [ ] Loops bounded by compile-time constants (no `while(true)`).
- [ ] Final `gl_FragColor.a` is `1.0` unless the slot explicitly composites (rare).
- [ ] Shader is written to `slot.outputPath`. If the slot wasn't declared with `data-shader`, I emitted a diff.

## Don't

- Don't use shader recipes that ignore the genre's restraint. Linear/Vercel/Bloomberg are not allowed to have shaders - your envelope is wrong if you got one of these. Return `error: "genre forbids shader medium"`.
- Don't write a shader that's beautiful in isolation but fights the UI on top of it. The shader is a background - it should support, not compete.
- Don't request input textures unless your runtime confirmed `texture()` support.
- Don't animate so fast that the user's eye is pulled to the background. Decoration is supposed to be felt, not noticed.
