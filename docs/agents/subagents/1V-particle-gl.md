# Subagent 1.V.particle-gl - Asset drawer (medium: WebGL particle field)

You own **ONE asset** of medium `particle-gl` - a high-density particle field rendered on the GPU. Two implementation paths:

| Path | When | Output |
|---|---|---|
| **GLSL fragment shader** | Field-pattern particles (flow noise, animated stippling, screen-space distribution where each "particle" is a brightness peak in shader output) | `.glsl` written to `slot.outputPath` |
| **three.js InstancedMesh** | Discrete particles with position state (thousands of orbs, sparks with trails, geometry-bound emitters) | `.js` written to `slot.outputPath` |

Pick one per asset. Mixing is out of scope. **Pathway B** either way.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","shader-skill"] OR ["prompt","three-skill"]
nodeIds: { prompt, skill, asset }
```

The orchestrator chooses the pipeline (`shader-skill` for the fragment-shader path, `three-skill` for the InstancedMesh path) based on the slot's `data-motion` modifier - `field` → shader, `discrete` → three.

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<1-sentence design intent>",
  "skillCode": "<full GLSL OR full three.js code>",
  "params": {
    "outputPath": "<slot.outputPath>",
    "implementation": "shader" | "instanced",
    "density": "<count or implicit-by-uv>",
    "performance": "background" | "hero"
  },
  "slotEditDiff": "<diff or null>"
}
```

## Recipe

### Path A - GLSL fragment shader (screen-space)

Use when: the brief is "drifting dots across the whole viewport", "flow noise stippling", "starfield" - anything where the particles ARE the screen-space output and don't need discrete state.

Defer to [`1V-shader.md`](1V-shader.md) for the GLSL scaffolding. The particle-specific recipes:

```glsl
// Drifting dot field (screen-space) - every pixel decides if it's "on" a dot
float dotField(vec2 p, float density, float t) {
  vec2 cell = floor(p * density);
  vec2 ci   = fract(p * density);
  float seed = hash(cell);
  vec2 jitter = vec2(hash(cell.yx), seed) - 0.5;
  jitter += 0.3 * vec2(sin(t * 0.4 + seed * 6.28), cos(t * 0.3 + seed * 6.28));
  float d = length(ci - 0.5 - jitter);
  return smoothstep(0.08, 0.0, d) * (0.4 + 0.6 * seed);
}

void main() {
  vec2 uv = gl_FragCoord.xy / iResolution.xy;
  vec2 p  = uv * vec2(iResolution.x / iResolution.y, 1.0);
  float field = dotField(p, 18.0, iTime);
  vec3 col = vec3(0.93) * field;     // anchor to --surface
  gl_FragColor = vec4(col, field);
}
```

Density is a uniform-free constant - pick from the brief.

### Path B - three.js InstancedMesh (discrete particles)

Use when: the brief wants discrete entities with position state - sparks with trails, orbital fields, particles emerging from a logo. Defer to [`1V-3d.md`](1V-3d.md) for the three.js scaffolding. The particle-specific recipe:

```js
const COUNT = 2000;
const geo   = new THREE.PlaneGeometry(0.02, 0.02);
const mat   = new THREE.MeshBasicMaterial({
  color: 0xffe7c2,
  transparent: true,
  opacity: 0.7,
  blending: THREE.AdditiveBlending,
  depthWrite: false
});
const mesh = new THREE.InstancedMesh(geo, mat, COUNT);

const dummy = new THREE.Object3D();
const state = Array.from({ length: COUNT }, () => ({
  pos: new THREE.Vector3(
    (Math.random() - 0.5) * 8,
    (Math.random() - 0.5) * 6,
    (Math.random() - 0.5) * 2
  ),
  vel: new THREE.Vector3(0, 0.005 + Math.random() * 0.01, 0),
  life: Math.random()
}));

for (let i = 0; i < COUNT; i++) {
  dummy.position.copy(state[i].pos);
  dummy.updateMatrix();
  mesh.setMatrixAt(i, dummy.matrix);
}
mesh.instanceMatrix.needsUpdate = true;
scene.add(mesh);

camera.position.set(0, 0, 5);

__animate((t) => {
  for (let i = 0; i < COUNT; i++) {
    const s = state[i];
    s.pos.add(s.vel);
    s.life += 0.001;
    if (s.pos.y > 4) {
      s.pos.set((Math.random() - 0.5) * 8, -3, (Math.random() - 0.5) * 2);
      s.life = 0;
    }
    dummy.position.copy(s.pos);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
  }
  mesh.instanceMatrix.needsUpdate = true;
});
```

Always use `InstancedMesh` for >100 particles - non-instanced meshes blow the draw-call budget.

### Performance budget

| Performance | Path A density | Path B count |
|---|---|---|
| `background` | `dotField(..., 14.0, …)` or lower | ≤1500 instances, additive blending only, no depth |
| `hero` | up to `dotField(..., 24.0, …)` | ≤4000 instances, may add one trail effect via `setColorAt` per-frame |

Add the same mobile gate as 3D: `if (window.innerWidth < 768) return;` if `hero`.

### Slot diff

Same pattern - declare `data-shader` (Path A) or `data-three` (Path B) on the slot.

## Self-audit

- [ ] Picked exactly one path (shader or instanced). Did not mix.
- [ ] If `instanced` path: used `InstancedMesh`, not 2000 separate meshes.
- [ ] If `instanced` path: `instanceMatrix.needsUpdate = true` is set each frame.
- [ ] Additive blending + `depthWrite: false` for instanced - otherwise z-fighting wrecks the look.
- [ ] Palette anchored to `:root` tokens.
- [ ] Density matches `performance` budget.
- [ ] DPR / resize handled by host runtime (three.js renderer / shader fullscreen quad - no manual DPR code unless host is bare WebGL).
- [ ] Mobile gate present if `hero`.

## Don't

- Don't loop `scene.add(mesh)` 2000 times. `InstancedMesh` is non-negotiable.
- Don't enable shadow casting on particles. Massively expensive, looks wrong.
- Don't use depth-write - particles need to z-blend additively.
- Don't use a particle library (three-nebula, particles.js). You're the generator.
- Don't run on every device unconditionally. Mobile gate for `hero` performance.
