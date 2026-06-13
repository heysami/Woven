# 3D capabilities — render sources, texture policy, advanced effects

Shared contract for every drawer that renders real 3D. Read by: the hero-3d
cluster (`hero-3d-orchestrator`, `h3d-research-technique`, `h3d-scene-author`,
`h3d-material-author`, `h3d-runtime-composer` — the WebGPU/TSL escalation in
§1.4 is theirs first), `sim-3d-scene-builder`, `game-world-builder`
(paradigm=`3d-environment`), `im-output-3d`, the narrative-experience 3D scene
drawers, the generic `3d` drawer, and the research drawers that commit the
fields in §4 (`sim-research-technique`, `game-research-technique`,
`im-research-technique`, `nx-research-technique`). The "3D must feel 3D" contract
(`sim-3d-scene-builder.md §1.0` / capabilities.py HARD CHECK D) applies to
EVERYTHING in this file — a textured, particle-dusted scene that is static and
flat-lit still fails.

## 1. Render sources

Research commits ONE `renderSource`; the scene drawer obeys it.

### 1.1 `three.js` (default)

The standing default. Pinned CDN import (r163+), `InstancedMesh`/`BatchedMesh`
above ~500 entities, pixelRatio capped at 2, fov ~50°. Full rules live in
`sim-3d-scene-builder.md §1.1–§1.4` — this file only adds what's NEW (textures
§2, effects §3).

### 1.2 `spline` — designed scenes via the Spline runtime

**When:** the brief calls for a DESIGNED 3D register — product-page hero
objects, soft-3D UI scenes, character vignettes with hand-tuned materials —
AND a Spline scene source exists. Spline scenes are authored in the Spline
editor (spline.design); they arrive with their own materials, lighting,
physics, and events already art-directed.

**The gate (hard):** agents cannot synthesize `.splinecode` from text. A scene
source must exist as one of:
- a user-provided public scene URL (`https://prod.spline.design/<id>/scene.splinecode`),
- a `.splinecode` file the user exported into the project
  (`source/<branch>/spline/<name>.splinecode`),
- a glTF/GLB the user exported from Spline → load with three.js `GLTFLoader`
  instead (you keep three.js as the renderSource; Spline is then the asset
  pipeline, not the runtime).

If none exists and the user asked for "Spline-grade" 3D, surface a
`<decision-request>` asking for a scene URL/export — do NOT silently fake it.
Fall back to `three.js` when the user declines.

**How:**

```js
import { Application } from 'https://unpkg.com/@splinetool/runtime@1.9.48/build/runtime.js';

const canvas = document.getElementById('scene-<id>');
const spline = new Application(canvas);
await spline.load('<sceneUrl or ./spline/<name>.splinecode>');

// Drive the scene from sim/game/mapping state — the runtime API is the bridge:
const hero = spline.findObjectByName('Hero');     // position / rotation / scale are writable
spline.setVariable('score', state.score);          // Spline variables wired in the editor
spline.emitEvent('mouseDown', 'Hero');             // trigger authored Spline events
```

**Rules:**
- ONE Spline scene per page — the runtime is heavier than a hand-rolled
  three.js scene; loading two tanks mobile.
- The loop still owns time: drive Spline objects from `onFrame(state, alpha)`
  exactly like an InstancedMesh — don't fork a second animation clock.
- The "3D must feel 3D" contract is verified the same way (look-around /
  self-motion / light response) — Spline's authored orbit + events usually
  satisfy it, but VERIFY with the §1.0 preview self-checks; an exported scene
  with a locked camera fails like any other.
- Spline scenes ignore `texturePolicy` (§2) — materials are authored upstream.
  Effects (§3) may still layer on top via a transparent three.js canvas only
  at `rich`/`showcase` budget; prefer Spline-native particles authored in the
  scene.

### 1.3 `three.js + generated glTF` — Meshy text-to-3D

**When:** the brief needs a SPECIFIC hero mesh (a katana, a sneaker, a
low-poly fox) that primitives can't reach, AND the Meshy provider is wired
(`TH_MESHY_API_KEY` registered — verify via `GET /__capabilities`). Meshy
returns a textured PBR `.glb`.

- Commission via the `meshy` skill trio (visual-orchestrator co-dispatch, same
  shape as a raster asset; output `source/<branch>/<family>/<id>/models/<name>.glb`).
- Load with `GLTFLoader`; keep hero meshes ≤30k tris; reuse one mesh via
  `InstancedMesh` when the brief wants a field of them.
- If Meshy is NOT wired: build the hero from three.js primitives/CSG +
  §2 textures. Do not block the whole piece on a missing provider.

### 1.4 `three.js-webgpu` — WebGPURenderer + TSL (the high-fidelity escalation)

**When:** material quality IS the message — refractive / dispersion glass,
chrome luxe, polished-floor product heroes, the "how is this running in a
browser" tier. Reference-grade exemplar: **vectrfl.com** (Astro shell + a single
hydrated three.js island: WebGPURenderer→WebGL2 fallback, TSL node materials,
HDR-IBL, Draco glTF, KTX2 textures, a mirror floor, GSAP ScrollTrigger). Escalate
here from §1.1 when the piece is a hero-3d / `showcase` scene AND the lead
material needs physically-correct reflection/refraction under IBL. This is NOT
the default — plain `three.js` (§1.1) stays the standing pick for sim / game /
everyday 3D; it carries a bundle + an async-init cost you only pay back when the
materials are the spectacle.

**What it is:** the SAME three.js, swapping `WebGLRenderer` for
`WebGPURenderer` (`three/webgpu`), which **auto-falls-back to WebGL2** when
`navigator.gpu` is absent. Shaders are authored in **TSL (Three Shading
Language)** node materials (`three/tsl`) — one shader graph compiles to BOTH
WGSL (WebGPU) and GLSL (WebGL2), so you write the material once and it runs on
every device. This is the only renderer path where you do NOT hand-fork a
backend; do not pair raw GLSL `ShaderMaterial` with it.

**The recipe that makes it look expensive** (copy vectrfl's exact stack):
- **HDR/EXR environment map** for image-based lighting → `HDRLoader` /
  `EXRLoader` + `PMREMGenerator`. This IS the reflections; metals and glass are
  invisible without it. (§1.1's `RoomEnvironment` is the no-asset fallback.)
- **Draco-compressed glTF** hero meshes → `GLTFLoader` + `DRACOLoader` (decoder
  from the pinned CDN). ~20× smaller payload than raw `.glb`.
- **KTX2 / Basis** GPU-compressed textures → `KTX2Loader`; loads to VRAM
  already compressed. Reach for it above a couple of 2K maps.
- **Reflective floor** → `Reflector` (mirror) or a roughness-mapped ground plane
  catching the IBL. The polished-ground reflection is most of why these scenes
  read as "rendered, not real-time." ONE reflector max — it re-renders the scene
  (§3.2 cost), never on mobile.
- **`InstancedMesh`** for any repeated geometry; **GSAP `ScrollTrigger`** for
  scroll-driven camera/material choreography (the binding lives in the
  interaction drawer, not here).

**Import pins** (importmap — bump in lockstep across `three`, `three/tsl`,
`three/addons/`):

```json
{ "three": "https://cdn.jsdelivr.net/npm/three@0.178.0/build/three.webgpu.js",
  "three/tsl": "https://cdn.jsdelivr.net/npm/three@0.178.0/build/three.tsl.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.178.0/examples/jsm/" }
```
```js
import * as THREE from 'three';
import { uniform, float, mix, /* … */ } from 'three/tsl';
const renderer = new THREE.WebGPURenderer({ antialias: true, alpha: true });
await renderer.init();          // WebGPU init is ASYNC — gate the first frame on it
```

**Rules / gates:**
- `renderer.init()` is **async** — the loading veil holds until it resolves;
  never start the loop before init (this is why the runtime composer owns the
  veil for WebGPU pieces).
- Post-processing uses the **TSL post stack** (`three/addons/tsl/display/…`,
  the `PostProcessing` node), NOT pmndrs `postprocessing` (WebGL-only). At
  `rich`/`showcase` budget only (§3.6 / §4).
- **Perf fallback adds one rung above §1.1's:** WebGPU→WebGL2 is automatic; if
  even WebGL2 + the post stack misses the fps floor, drop the reflector first,
  then the post stack, then DPR. §4 lens-gating thresholds are unchanged.
- The "3D must feel 3D" contract (§1.0) is verified identically — a WebGPU scene
  that is static and flat-lit still fails. The renderer never earns the pass;
  the light story + ambient motion do.

## 2. Texture policy — "if the style permits, the object gets a texture"

Untextured default-gray `MeshStandardMaterial` on a hero object is the 3D
equivalent of Tabler-default icons next to an in-vibe hero — an
**aesthetic-lens block** whenever `texturePolicy != none-flat`. Research
commits ONE policy from this table; the scene drawer implements it.

| `texturePolicy` | When (style register) | Implementation |
|---|---|---|
| `none-flat` | flat-design, outline/wireframe, de-stijl, bauhaus-pure, vector-* — flat color IS the style | Solid `MeshStandardMaterial` colors from the project tokens. Untextured is CORRECT here. |
| `matcap-stylized` | claymorphism, kawaii, corporate-memphis, soft-3D | `MeshMatcapMaterial` (one matcap raster sets the whole light response) or solid colors + strong AO. Cheap, reads instantly as "clay". |
| `painted-plates` | painterly, cottagecore, dark-academia, storybook | Hand-painted-register albedo maps (generated, §2.1) on key surfaces; rough ≥0.8, no metalness. |
| `pbr-generated` | skeuomorph, frutiger-aero, product-render, realistic material-bearing | Albedo + roughness (+ normal when budget allows) per key material, generated §2.1 or from a Meshy glb's baked set. |
| `pixel-lowres` | PS1 / N64 / pixel-* aesthetics | 64–256px textures, `NearestFilter`, no mipmap blur. The crunch is the style. |

### 2.1 Generated textures — the visual-orchestrator co-dispatch

When the policy needs raster maps and an image generator is wired, commission
each texture exactly like any other asset:

```
Task(subagent_type: "visual-orchestrator",
     description: "Tileable texture for <family>:<id>",
     prompt: "Seamless tileable texture: <material — e.g. 'mossy cobblestone,
       hand-painted storybook register'>. Inherit styleCue verbatim: <styleCue>.
       FLAT top-down, even diffuse lighting, no shadows, no vignette, no
       perspective, exact square. Output:
       source/<branch>/<family>/<id>/textures/<name>.png")
```

The tileable contract (flat / even light / no vignette / square) is
load-bearing — a vignetted texture shows seams on every repeat. Power-of-two
sizes (512 or 1024).

Apply:

```js
const tex = new THREE.TextureLoader().load('./textures/<name>.png');
tex.colorSpace = THREE.SRGBColorSpace;            // albedo only — NOT normal/roughness
tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
tex.repeat.set(ru, rv);
tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.85 });
```

### 2.2 Procedural fallback (no image-gen wired)

Never ship gray defaults because the generator is missing. Build a
`CanvasTexture` procedurally — noise grain, stripes, gradients, checker —
toned with the project palette. 20 lines of canvas2D beats an untextured
hero. (`pixel-lowres` policies are often BETTER served procedurally.)

## 3. Advanced effects catalog

Effects are budget-gated (§4) and style-gated — an effect ships only when the
brief's style register earns it AND the committed `effectsBudget` permits it.

### 3.1 Particle effects (dust, sparks, snow, rain, fireflies, magic)

- **`THREE.Points` + custom `ShaderMaterial`** — per-particle attributes
  (seed, phase, size), motion computed in the vertex shader from a `uTime`
  uniform. Zero per-frame JS cost; this is the default.
  Budgets: ≤50k points desktop, ≤8k mobile.
- **`InstancedMesh` particles** — when particles need real 3D shape (petals,
  shards, embers with depth). ≤10k desktop, ≤2k mobile.
- Never allocate in the rAF body — pre-allocate buffers, recycle via a ring
  index. Spawn = rewinding a dead particle's attributes.
- For 2D contexts (HUD bursts, screen-space confetti) co-dispatch the existing
  `particle-2d` / `particle-gl` drawers instead of hand-rolling.

### 3.2 Water simulation

| Register | Technique | Cost |
|---|---|---|
| Calm reflective (pond, marble lobby pool) | `Water2` / `Reflector` from `three/examples/jsm/objects/` + two scrolling normal maps | A reflector re-renders the scene — roughly halves fps. ONE reflective surface max; never on mobile. |
| Stylized ocean / lake | Plane (64×64+ segments) + 2–4 summed **Gerstner waves** in the vertex shader + fresnel tint in the fragment | Cheap. The default water. |
| Toon / flat-shaded water | Scrolling voronoi-foam bands + banded fresnel, `MeshToonMaterial`-adjacent | Cheapest. Right for stylized registers. |

Match the register to the brief: glassy `Water2` under a cottagecore rowboat
is an aesthetic-lens block — the WATER must wear the style too.

### 3.3 Hair / fur / strand dynamics (honest scope)

Real groom simulation is out of scope — do not attempt film-style hair. What
ships well:

- **Verlet strand chains** — each strand = 4–8 segments integrated on CPU with
  distance constraints, root pinned to the mesh. ≤300 strands. Right for:
  grass tufts, ribbons, tentacles, kelp, banner tassels, a character's few
  hero hair locks reacting to motion/wind.
- **Shell fur** — 16–32 instanced expanded copies of the base mesh with an
  alpha-noise cutoff per shell. Reads as plush/moss/peach-fuzz. GPU-cheap;
  no dynamics (add vertex-shader wind sway).
- **Static cards + wind sway** — hair/foliage cards with a vertex-shader
  `sin(uTime + worldPos)` sway. The budget option.

### 3.4 Cloth (flags, banners, curtains, capes)

- **Verlet grid** — N×M particle grid (≤32×32) with structural + shear
  constraints, pinned edge, wind as a noise-driven force. CPU, one cloth per
  scene at this fidelity.
- **Vertex-shader sway** for non-interactive cloth — same trick as foliage.

### 3.5 Smoke / fire / atmosphere

- Billboarded sprite particles (§3.1) with procedural noise erosion in the
  fragment shader, additive blending for fire, normal blending for smoke.
- Fog: `THREE.FogExp2` is nearly free and adds more depth than any particle —
  reach for it FIRST when the brief says "atmosphere".
- True ray-marched volumetrics: `showcase` budget, desktop only, one volume.

### 3.6 Post-processing

`EffectComposer` (`UnrealBloomPass`, vignette, chromatic aberration) only at
`rich`/`showcase` budgets. Desktop ≤2 passes, mobile ≤1 (bloom OR vignette,
not both). Honour the style: bloom on a flat-design register is a block.

## 4. The contract — research commits, drawers obey, lenses verify

When paradigm/output is 3D, research.md MUST carry three extra committed
fields (the scene drawer does not improvise them):

```markdown
## Committed 3D extras
- renderSource:  three.js | three.js-webgpu | spline | three.js+gltf | hybrid   (+ scene URL / model list if not pure three.js; §1.4 if webgpu)
- texturePolicy: none-flat | matcap-stylized | painted-plates | pbr-generated | pixel-lowres
- effectsBudget: none | ambient | rich | showcase   (+ which §3 effects, named)
```

`three.js-webgpu` (§1.4) is reserved for `effectsBudget: rich`/`showcase`
material-bearing heroes — it almost always pairs with `texturePolicy:
pbr-generated` (or a Meshy/Draco glb's baked PBR set) under an HDR environment.
Committing it on an `ambient`/`none-flat` piece is a research error: the
async-init + bundle cost buys nothing a flat-lit `three.js` scene wouldn't.

| `effectsBudget` | Permits |
|---|---|
| `none` | Lighting + fog only. |
| `ambient` | ONE §3.1 particle system ≤2k points (motes, drift) + fog. |
| `rich` | Particles ≤20k + ONE of {water, cloth, strand/fur} + ≤2 post passes. |
| `showcase` | Desktop-first everything; a named mobile demotion plan is REQUIRED (which effects drop, which budgets halve). |

- **prefers-reduced-motion:** halve effect intensity, quarter particle counts,
  freeze camera micro-motion. The scene still LIVES (per the living-world
  contract) — never zero it out.
- **Lens gating:** craft — fps 60 target / warn 45 / block 30, dispose
  hygiene, no rAF allocation; aesthetic — textures + effects wear the
  committed style (water reads as the BRIEF's water); concept — effects serve
  `successFeel`, not confetti for its own sake.
