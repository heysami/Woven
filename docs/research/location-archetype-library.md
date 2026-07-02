# Location-archetype library

> The WHERE catalogue for `immersive-place` scenes. An **archetype** is a
> place-type (a reef, a room, a valley, a dream). A **register** (`photoreal` |
> `stylized-<family>`, from `immersive-world-study.md` §2/§5) is how it is
> rendered. Any archetype supports either register.
>
> `s3d-research-technique` reads `location-archetype-library.index.json` to pick
> one `archetypeId`, then reads that archetype's full entry below to inherit its
> `lightingModel · atmosphere · materialPalette · subsystemSet · motionSignature
> · compositionNote · paletteHexes · antiPatterns`, translates them to the
> committed register, and seeds §10 `subsystems[]` from `subsystemSet`.
>
> Never invent an `archetypeId`. If the brief's place fits none of these, pick
> the nearest and note the stretch, or add a library entry first.

Each entry is a starting contract, not a cage: research tunes it to the brief.
The six coherence pillars (immersive-world-study §3) apply to every archetype.

---

## `outdoor-natural`
Forests, alpine valleys, meadows, ravines, deserts, coastlines above water. The fable5 register.
- **exemplars:** fable5-world-demo (photoreal); Firewatch, Sable, BOTW (stylized).
- **lightingModel:** one directional sun (golden-hour default) + sky IBL + hemisphere fill (sky-blue / ground-warm). Long soft shadows; `three-csm` for wide range.
- **atmosphere:** `FogExp2` tinted to time-of-day + aerial perspective (warm-near/cool-far) + `Sky` shader dome; optional god-ray shafts through canopy.
- **materialPalette:** terrain (triplanar noise, macro-meso-micro), rock (ridged noise, craggy silhouette), foliage (instanced, translucent leaves), water margins.
- **subsystemSet:** `terrain` (lead, 3d, triplanar noise displacement), `foliage-scatter` (support, instanced 3d), `sky-atmosphere` (ambient, shader), `wind-motion` (ambient), optional `water-margin` (support, shader).
- **motionSignature:** wind through grass/canopy; drifting particles (pollen/leaves/dust) in light; slow cloud drift.
- **compositionNote:** dark foreground frame, lit midground subject, luminous atmospheric background; horizon in upper third.
- **paletteHexes:** ["#2f3d2a","#6b7f4e","#c8b273","#e6d8a8","#8fb3c9","#3a5568"]
- **antiPatterns:** smooth low-poly peaks; bare terrain texture underfoot; green-fog forests; cloned trees; fog hiding the horizon.

## `indoor-architectural`
Rooms, halls, studios, galleries, temples, interiors of any scale. Bounded space, portal light.
- **exemplars:** Vermeer studio (museuuum project); The Witness interiors; Monument Valley chambers (stylized).
- **lightingModel:** `RoomEnvironment` IBL + window/portal key light casting soft shadows + hemisphere fill so corners never go black. Warm interior bounce.
- **atmosphere:** gentle depth haze + dust motes in the light shaft; NO heavy outdoor fog. Volumetric shaft from windows is the signature.
- **materialPalette:** wall/floor surfaces (subtle procedural variation, not flat paint), wood/stone/plaster (macro variation), fabric/props, glass at windows.
- **subsystemSet:** `room-shell` (lead, 3d, walls/floor/ceiling with real material), `props-dressing` (support, instanced 3d), `window-shaft` (support, billboard/shader god-ray), `dust-motes` (ambient, particle).
- **motionSignature:** dust drifting in the shaft; slow curtain/fabric sway; a candle/screen flicker if present. Otherwise intentional stillness.
- **compositionNote:** light shaft as the focal beam; the room frames the subject; leading lines along floor/beams.
- **paletteHexes:** ["#2a2320","#5c4a38","#a8895f","#d8c9a8","#e8dcc0","#7a6a52"]
- **antiPatterns:** flat-lit box with black corners; walls as single-flat-color planes; empty room with no props; outdoor fog indoors.

## `sea-surface`
Above-water seascapes: open ocean, lagoons, shorelines seen from above the waterline, horizon-dominant.
- **exemplars:** Abzu surface; Sea of Thieves (stylized); photoreal ocean demos.
- **lightingModel:** low sun + strong specular sun-glint path on water + sky IBL + hemisphere fill. Bright, high-key.
- **atmosphere:** horizon haze, sea-spray mist near breaks, `Sky` dome meeting water at a soft horizon.
- **materialPalette:** water (Gerstner waves + depth-absorption teal + foam), sky, distant landmasses as hazed silhouettes.
- **subsystemSet:** `ocean-surface` (lead, shader, Gerstner + screen-space refraction + foam), `sky-atmosphere` (support, shader), `spray-particles` (ambient, particle), optional `horizon-landmass` (ambient, 3d billboard).
- **motionSignature:** rolling swells, foam crests, sun-glint shimmer, spray at obstacles.
- **compositionNote:** horizon line placement is the whole composition; sun-glint as leading line to the focal point.
- **paletteHexes:** ["#0e3a4a","#1c6b7a","#3fa8b0","#bfe3e0","#eaf3f0","#d9c48a"]
- **antiPatterns:** flat-plane water; tiling wave texture; hard horizon seam; still ocean.

## `underwater`
Submerged worlds: reefs, kelp forests, deep zones, sunken ruins. Volumetric depth is the medium.
- **exemplars:** Abzu, Subnautica (stylized); photoreal dive footage.
- **lightingModel:** god-ray shafts from the surface + blue depth-attenuated ambient + colored fog acting as the light medium. Everything reads through water color.
- **atmosphere:** strong depth fog (blue-green) with distance, floating particulate (marine snow), caustic light patterns on the seabed.
- **materialPalette:** seabed/sand, coral (instanced, vivid), rock, kelp (instanced, current-swayed), fish schools (instanced).
- **subsystemSet:** `depth-fog-medium` (lead, shader/scene fog), `caustics-projector` (support, animated caustic texture on floor), `god-ray-shafts` (support, billboard/shader), `particulate-drift` (ambient, particle), `reef-scatter` (support, instanced 3d), optional `buoyant-hero` (support, 3d).
- **motionSignature:** buoyant drift on everything, current-sway of kelp/coral, rising bubbles, caustics rippling, fish schooling.
- **compositionNote:** shafts from above as vertical leading lines; layered depth planes fading to blue; focal creature/ruin lit by a shaft.
- **paletteHexes:** ["#04202e","#0a4a5c","#1c8a8f","#3fd0c0","#a8ead8","#0d3550"]
- **antiPatterns:** clear-air lighting underwater; no depth fog; static kelp; caustics missing on the floor.

## `surreal-dreamscape`
Impossible geometry, floating islands, dream logic, invented spaces that must still read coherent.
- **exemplars:** Monument Valley, Gris, Journey's ascent (stylized); surreal render art.
- **lightingModel:** non-physical but *consistent* - one invented key direction + colored ambient that obeys its own rule; glow/bloom on emissive forms. Coherence over realism.
- **atmosphere:** gradient sky/void, soft haze between floating elements, dust/particles suggesting scale, bloom halos.
- **materialPalette:** matte pastel or monochrome forms, emissive accents, gradient surfaces; texture-light (shape carries it).
- **subsystemSet:** `dream-forms` (lead, 3d, the floating/impossible geometry), `gradient-void` (support, shader/dome background), `drift-particles` (ambient, particle), `emissive-accents` (support, 3d/bloom), optional `soft-shadow-ground` (ambient, contact plane).
- **motionSignature:** slow float/orbit of elements, gentle particle drift, breathing scale pulses, drifting light.
- **compositionNote:** negative space dominates; symmetry or sacred-geometry framing; one luminous focal form.
- **paletteHexes:** ["#241a3a","#5a3f7a","#b56fb0","#f2a6c2","#ffe0b0","#8fd0e0"]
- **antiPatterns:** incoherent light (breaks its own rule); cluttered void; photoreal detail fighting the dream; dead-still elements.

## `cosmic-space`
Space vistas, planetary surfaces, nebulae, orbital scenes, alien skies.
- **exemplars:** No Man's Sky, Outer Wilds, Elite (stylized/photoreal blend).
- **lightingModel:** one hard star key (long sharp shadows, near-black-but-tinted shadow side rescued by faint starlight/planet-bounce fill) + emissive nebula ambient. High contrast.
- **atmosphere:** starfield, nebula gradient clouds (sprite/shader), planetary atmosphere rim glow, thin haze on surfaces.
- **materialPalette:** planetary terrain (procedural, alien palette), rock, metallic structures; emissive stars/nebula.
- **subsystemSet:** `celestial-body` (lead, 3d, planet/structure with real material), `starfield` (ambient, points/shader), `nebula-clouds` (support, sprite/shader), `atmosphere-rim` (support, shader glow), optional `particle-drift` (ambient).
- **motionSignature:** slow orbital/rotational drift, twinkling stars, nebula churn, dust motes.
- **compositionNote:** dark frame with a luminous body; rim-lit silhouette; rule-of-thirds planet placement.
- **paletteHexes:** ["#050512","#1a1440","#3a2a8a","#8a5fd0","#e0a0ff","#ffd9a0"]
- **antiPatterns:** flat black shadows with no rescue fill; billboard-dome-only sky; static starfield; smooth featureless planet.

---

*Companion doctrine: `immersive-world-study.md`. Index for cheap lookup: `location-archetype-library.index.json`. Read by: `s3d-research-technique` (archetype pick + inheritance), and the `aesthetic-lens` immersive block (scores against the chosen archetype's paletteHexes + antiPatterns).*
