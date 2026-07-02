# Immersive-world study - the inhabitable-place render doctrine

> Companion to `spline-grade-3d-study.md`. That study defines the bar for a
> **hero OBJECT** (refractive glass, chrome luxe, product-on-a-stage - "look at
> this thing"). This study defines the bar for an inhabitable **PLACE** ("be
> *in* this world"): outdoor, indoor, sea, underwater, surreal, cosmic - at
> photoreal fidelity OR deliberately-stylized fidelity, both stunning, both
> coherent.
>
> The lineage on the photoreal side is `Braffolk/fable5-world-demo` - a fully
> procedural, image-free browser world (WebGPU, ~21k LOC). We cannot run that
> engine in one `runtime.html`; what we inherit from it is its **doctrine**, and
> we translate each technique to the cheapest web-affordable substitute (§4).
> The lineage on the stylized side is art-directed games (Journey, Sable, BOTW,
> Genshin, Gris, Firewatch) that are gorgeous *because* they refuse photorealism.

---

## 1. The two tracks (decide this FIRST)

`s3d-research-technique` commits `immersionMode` before anything else. It is the
"does this even want an immersive world?" gate the whole pipeline forks on.

| immersionMode | The claim | Reads | Feels like |
|---|---|---|---|
| **`object-hero`** | "Look at this object." One subject on a stage; the *material* is the message. | `spline-grade-3d-study.md` (unchanged) | A product render, a glass hero, a floating artefact. |
| **`immersive-place`** | "Be *in* this world." A coherent inhabitable environment; *presence* is the message. | THIS doc + `location-archetype-library.md` | Standing somewhere - a reef, a studio, a valley, a dream. |

**Choose `immersive-place` when** the brief describes a *location* the user occupies (a room, a landscape, underwater, a dreamscape), when the camera *moves through* the world, or when the caller is narrative/game/sim asking for an environment. **Choose `object-hero`** when the brief is one artefact the user rotates/admires and the surface finish is the point. When genuinely ambiguous, the deciding question is: *is the subject a thing, or a place?* Not every 3D scene should be an immersive world - a glossy hero object built as a "world" reads as an empty stage.

An `immersive-place` scene may *contain* a hero object (a lit sculpture in a room), but the object is dressed by the place, not floating on seamless void.

## 2. The two fidelity registers of `immersive-place`

Immersive is **not** a synonym for photoreal. Commit a `fidelityRegister`:

- **`photoreal`** - the fable5 lineage. Physically-based materials, IBL, soft shadows, atmospheric perspective, macro-meso-micro surface detail. The bar is "a viewer's eye doesn't snag on a category error within one second."
- **`stylized-<family>`** - one of the §5 families (e.g. `stylized-painterly-impressionist`, `stylized-cel-lit-anime`). Deliberately non-photoreal, and *more* disciplined for it: the coherence pillars still all apply, but "light transport" becomes hand-keyed warm/cool, "surface detail" becomes bold shape-language, "material" becomes matte/toon.

The six pillars in §3 apply to **both** registers. Only the *technique* per pillar changes with the register.

## 3. The six coherence pillars

Generalized from fable5's pillars + the stylized-game research. A scene must satisfy all six against its chosen archetype. These are what the aesthetic-lens immersive block scores.

**P1 - Coherent light transport; NO dead/black shadows.** Ambient always carries *color*. Photoreal: IBL from an environment map + a hemisphere fill light so shadows read sky-blue / bounce-green, never pure gray-black. Stylized: hand-keyed warm key + cool shadow fill (or the family's inverse), banded but never dead. *Fail:* sample any shadowed pixel - if it is desaturated gray-black, lighting has failed.

**P2 - Silhouette & geometry over flat texture.** Detail lives in shape, not in a flat photo-plane. Photoreal: macro-meso-micro surface layering (§4.4), craggy silhouettes, no smooth low-poly outlines in a hero frame. Stylized: bold readable silhouettes, outline-weight-as-depth, shape hierarchy. *Fail:* a flat textured billboard standing in for geometry the frame should carry; a smooth blob where the archetype wants a defined form.

**P3 - Nothing bare; everything occupied.** Every surface class an archetype declares has occupants (a forest floor has litter + undergrowth; a room has props + dust; a reef has coral + fish). Density via `InstancedMesh`. *Fail:* large empty untextured expanse in the near field.

**P4 - Distance holds.** Depth reads through atmospheric perspective + fog-as-art + LOD. Fog serves *mood and composition*, never hides pop-in or a missing horizon. *Fail:* fog deployed as a curtain to cover draw distance; visible LOD/impostor pops; a flat far plane.

**P5 - Art direction / color script.** A limited palette (5-7 dominant colors), a value structure (dark frame / lit subject / atmospheric background), a time-of-day logic, a composition. Restrained saturation for photoreal; emotional color-mapping for stylized. *Fail:* uncontrolled palette, flat value structure, no focal hierarchy.

**P6 - The world always moves.** A per-archetype ambient motion signature (wind through foliage, dust in shafts, buoyant drift underwater, cloth flutter). A frozen frame still feels one second from motion. *Fail:* a dead-still scene; OR motion on things that have no reason to move.

## 4. Web-budget technique matrix

fable5 runs offline-grade GPU passes. We have ONE `runtime.html` at ~16ms/frame on a mid laptop. Below is the affordable translation. Tags: `[CHEAP-WIN]` (take it), `[MODERATE]` (budget for it, lead subsystem only), `[EXPENSIVE-SKIP]` (do not; use the substitute).

### 4.1 Lighting (P1)
- `[CHEAP-WIN]` **IBL**: `PMREMGenerator` prefilter of an env map into `scene.environment` - free PBR ambience + reflections, no dead shadows. Env source: `RoomEnvironment` (indoor), a generated gradient/`Sky` capture (outdoor), or an HDRI URL when wired.
- `[CHEAP-WIN]` **`HemisphereLight`** sky/ground two-tone fill - the cheapest guarantee that shadows carry color.
- `[MODERATE]` `THREE.LightProbe` for multi-zone indoor bounce.
- `[EXPENSIVE-SKIP]` fable5's per-chunk irradiance-probe GI volume → substitute: IBL + hemisphere + one bounce-tinted fill light.

### 4.2 Shadows (P1)
- `[CHEAP-WIN]` `PCFSoftShadowMap`, one directional light, tuned bias. Tinted, soft.
- `[CHEAP-WIN]` fake contact shadow = a radial-gradient plane under grounded objects (~1 draw call).
- `[MODERATE]` `three-csm` cascaded shadow maps for wide outdoor range (4 cascades desktop / 2 mobile).
- `[EXPENSIVE-SKIP]` PCSS + screen-space contact shadows raymarch → substitute: PCFSoft + contact planes.

### 4.3 Atmosphere & depth (P4)
- `[CHEAP-WIN]` `THREE.Fog` / `FogExp2` - near-free depth; color it per archetype.
- `[CHEAP-WIN]` `THREE.Sky` (atmospheric-scattering shader) or a gradient dome.
- `[MODERATE]` god-ray light shafts as half-res radial-blur additive pass, OR billboard shafts.
- `[EXPENSIVE-SKIP]` raymarched volumetric clouds/fog → substitute: `FogExp2` + a Sky shader + billboard/sprite clouds.

### 4.4 Surface detail without image assets (P2)
- `[CHEAP-WIN]` procedural noise (Simplex/fBm) in the fragment/vertex shader; TSL node materials on the WebGPU branch. **Macro-meso-micro**: blend 2-3 incommensurate noise scales (large breakup / mid variation / fine grain) so tiling never reads - this is fable5's core surface trick and it ports directly.
- `[MODERATE]` normal maps baked from noise; triplanar mapping for seam-free terrain/rock (< ~100 visible objects).
- `[CHEAP-WIN]` `MeshStandardMaterial` is the PBR sweet spot; reserve `MeshPhysicalMaterial` (clearcoat/transmission) for a single hero.
- Stylized register: swap PBR for a toon/`MeshToonMaterial` + banded gradient ramp + optional outline (inverted-hull or post edge-detect).

### 4.5 Density / nothing-bare (P3)
- `[CHEAP-WIN]` `InstancedMesh` - thousands of props in one draw call. Instanced grass/foliage via vertex sway.
- `[MODERATE]` `THREE.LOD` + billboards for distance; dither the swap to avoid pop.
- `[EXPENSIVE-SKIP]` real-time captured impostors (fable5's octahedral bake) → substitute: static crossed-quad billboards + LOD.

### 4.6 Post (P5)
- `[CHEAP-WIN]` `ACESFilmicToneMapping` (always), LUT color grade (single 3D-texture lookup, huge payoff), vignette+grain.
- `[MODERATE]` Bloom (half-res) + SMAA (needed once EffectComposer bypasses MSAA).
- `[EXPENSIVE-SKIP]` SSAO → substitute: baked AO / contact planes / light probes.

### 4.7 Water (sea-surface / underwater archetypes)
- `[CHEAP-WIN]` Gerstner waves in the vertex shader (4-8 sines); animated caustic texture scroll.
- `[MODERATE]` `Reflector`/`Refractor` (ONE max); screen-space refraction distorting the framebuffer.
- `[EXPENSIVE-SKIP]` FFT ocean spectrum → substitute: Gerstner + normal-map detail.

### 4.8 Performance guardrails
- DPR cap 2 (1.5 if post is heavy); draw calls < ~200; texture/VRAM budget modest (procedural beats baked).
- WebGPU (`three/webgpu` + TSL) when: heavy instancing/compute, procedural density, node materials - always keep a WebGL2 fallback.
- Target ~8ms render / ~2ms post / ~2ms sim on a mid-2020s laptop; fallback ladder sheds heaviest subsystem → post → static poster.

## 5. The stylized families (register `stylized-<family>`)

Each is a coherent way to be stunning without photorealism. Pick ONE per scene. All six pillars still apply; the recipe below is how each pillar is expressed.

- **`stylized-painterly-impressionist`** - *Journey, Ori, Gris, Sky.* Hand-keyed warm/cool by location; limited complementary palette with emotional mapping; matte surfaces, no specular; watercolor color-bleed; fog as depth planes + bloom on lights; slow meditative motion, particles on every breath of wind. *Anti-pattern:* any photoreal detail, hard shadow, or glossy highlight.
- **`stylized-cel-lit-anime`** - *Genshin, Honkai, BOTW.* 1-2 light dirs, hard light/shadow boundary with soft feather, faint SSS tint on the shadow edge; highly saturated base, per-subject color identity, time-of-day script; toon banding (3-5 levels), matte + rim; hair/cloth/grass sway. *Anti-pattern:* physically-based GI, complex material variation.
- **`stylized-moebius-lineart-minimal`** - *Sable, Monument Valley, The Witness.* Light for silhouette not realism; earthy desaturated palette + ink outlines; flat fills, line-weight-as-form, strict geometry; fog fades outlines at distance; minimal motion, deliberate camera. *Anti-pattern:* texture, soft edges, saturation complexity.
- **`stylized-sumi-e-ink`** - *Okami, Abzu.* Ink-density replaces light/shadow; muted water-soaked palette, warm bleeding into cool; ink-on-paper matte, varying stroke thickness, visible paper texture; calligraphic flowing motion; asymmetric negative-space composition. *Anti-pattern:* hard geometric edges, bright accents.
- **`stylized-retro-pixel-neon`** - *Hyper Light Drifter.* Neon glow over a flat grid, vignette; 3-5 saturated colors, stark complements; flat color blocks, dithering, no AA up close; limited-frame sprite motion + screen-shake/flash; central radial framing. *Anti-pattern:* smooth gradients, realistic shading, soft focus.
- **`stylized-comic-ink-grotesque`** - *Borderlands, TF2.* Hard graphic shadows following ink contours; saturated complementary color blocking; hand-inked texture, exaggerated readable silhouettes; bouncy exaggerated motion; depth via scale+overlap not haze. *Anti-pattern:* photorealism, soft edges, low contrast.
- **`stylized-moody-atmospheric-indie`** - *Firewatch, Death Stranding vistas, No Man's Sky.* Directional golden-hour key + long shadows + IBL bounce; desaturated per-biome palette + one crimson-vessel accent; matte simple shaders, color-grade does the work; heavy fog-as-composition, warm-near/cool-far depth planes; wind-blown grass, dust/pollen particles; panoramic framing, horizon in upper third. *Anti-pattern:* glossy surfaces, busy high-frequency texture in fog-obscured zones.

## 6. Cross-family universal rules (both registers)

1. **Silhouette first** - every shape reads as a solid silhouette before detail.
2. **Palette discipline** - 5-7 dominant colors; vary value/saturation within a family, not wild hue shifts.
3. **Fog as art** - atmosphere always serves mood/composition, never just depth-sort or draw-distance cover.
4. **Motion minimalism** - move only what has a reason (wind, breath, current, player). Static-by-intent reads designed; static-by-neglect reads dead.
5. **Light-temperature logic** - warm key + cool fill (or the consistent inverse). Never temperature-incoherent.
6. **Distance legibility** - outline/detail weight thins with distance; near-field is where density and craft live.

---

*Companions: `spline-grade-3d-study.md` (the object-hero track), `location-archetype-library.md` (the WHERE catalogue this doctrine is applied through), `editor/kinds/3D_CAPABILITIES.md` (render routes + budgets). Read by: `s3d-research-technique` (§0), `s3d-subsystem-author` + `s3d-runtime-composer` (when immersionMode=immersive-place), and the `aesthetic-lens` immersive realism block.*
