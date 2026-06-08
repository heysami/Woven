# Scene-based addendum — drawing-time details

Drawing-time vocabulary for scene-based genres. Read after committing a scene-based genre from the main playbook.

### Permitted runtime — CDN-only, no build step

The "no build, opens by double-clicking" commitment is preserved. Scene libraries enter via ESM importmap in the same `index.html`:

```html
<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/",
    "maplibre-gl": "https://unpkg.com/maplibre-gl@4.0.0/dist/maplibre-gl.js",
    "openseadragon": "https://unpkg.com/openseadragon@4.1.0/build/openseadragon/openseadragon.min.js"
  }
}
</script>
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.0.0/dist/maplibre-gl.css"/>
```

| Need | Library (CDN ESM) | Notes |
|---|---|---|
| 3D scene (default) | `three` | Corpus default; inherits the most. Raw WebGL only when the shader IS the entire subject. |
| 3D inside React/htm | `@react-three/fiber` + `@react-three/drei` via esm.sh | Optional — vanilla Three.js with one `useEffect` is usually less ceremony. |
| Gaussian splat viewer | `@mkkellogg/gaussian-splats-3d` via esm.sh | Sample splats from public archives, not generated on the fly. |
| Photogrammetry mesh | Three.js `GLTFLoader` | For Smithsonian / Open Heritage 3D / Sketchfab CC0 captures. |
| Real-world map (vector) | **`maplibre-gl`** (default, free, no token) | Use `mapbox-gl` only if a real Mapbox token is in the brief — prototypes prefer MapLibre. |
| Real-world map (raster) | `leaflet` + OSM tiles | When you don't need vector terrain or 3D camera. |
| Geospatial overlays / large data | `deck.gl` layered on MapLibre | Point clouds, arcs, hexagons, trip animations. |
| Globe | `globe.gl` (Three.js wrapper, declarative) | CesiumJS only when geodetic accuracy and terrain matter. |
| Deep-zoom imagery (IIIF) | `openseadragon` | IIIF Image API 3.0 endpoints from public museum archives. |
| Annotations on deep-zoom | OpenSeadragon overlays or `Annotorious` | For curator notes, region highlights, conservation layers. |
| Shaders | Three.js `ShaderMaterial` with inline GLSL | Raw WebGL2 when shader IS the subject. WebGPU when compute is required. |
| Spatial audio | Web Audio `AudioContext` + `PannerNode` (no library) | Anchor voices to scene coordinates; listener tied to camera. |
| GPU compute / simulation | WebGPU via vanilla API | Modern-browser baseline must be set in the brief. |
| Node graph / structured canvas | `@xyflow/react` (React Flow) via esm.sh | Default for typed nodes + edges (n8n / Zapier / agent graphs). |
| Freeform whiteboard | `tldraw` via CDN | When the canvas is freeform-drawing-led (hand-sketched boxes, ink). |
| Hand-drawn diagram | `@excalidraw/excalidraw` via esm.sh | Only when "explicitly hand-drawn" is in the brief. |
| Video / audio timeline canvas | `konva` via CDN + HTML5 `<video>` | Multi-track timeline as Konva stage; vanilla video for playback. |
| Waveform UI / scrubber | `wavesurfer.js` via CDN | Default for waveform display + transport. Pair with Web Audio `AnalyserNode` for spectrogram (no library). |
| Music synthesis / sequencing | `tone.js` via CDN | Only when the brief calls for synthesis or step-sequencing. |
| Product 3D hero (one part) | `@google/model-viewer` web component via CDN | Hero rotation / configurator at landing scale. For full CAD viewer, use Three.js. |
| Parametric CAD geometry | `replicad` or `opencascade.js` via esm.sh | When a slider changes a dimension and the geometry rebuilds. |
| VR session (declarative) | `aframe` via CDN | Corpus default for prototype WebXR — `<a-scene>` / `<a-entity>` HTML. |
| VR session (custom render) | Three.js with `WebXR` API + `XRControllerModelFactory` | When custom shaders / per-frame logic are in the brief. |
| AR face / image tracking | `mind-ar` via CDN | For face filters, image-anchored overlays, try-on. |
| AR surface / hit-test | WebXR `immersive-ar` session via vanilla API | When the brief calls for surface plane detection and the device supports it. |
| 2D particle / sprite simulation | `pixi.js` via CDN | Default for 2D particle fields up to millions of sprites. |
| Low-level WebGL bindings | `regl` via CDN | When you want declarative data-bound WebGL without Three.js. |

**Forbidden even in scene mode:** physics engines (Cannon, Rapier — unless the simulation IS the brief), full game frameworks (Phaser, Babylon, PlayCanvas — Three is the corpus default), networking SDKs, analytics, telemetry, anything that talks to a private API or requires keys not in the brief. Read-only public endpoints (IIIF, OSM, MapTiler free tier, NASA GIBS, USGS, Polyhaven, Natural Earth, Wikimedia) are fine.

### Asset vocabulary — real sources, not placeholders

The `<div class="img-placeholder">` rule from step nine is **suspended** for scene-based genres. Placeholder rectangles in a Three.js scene look worse than nothing. Real assets from public, citable sources are mandatory:

| Asset class | Source | Licence |
|---|---|---|
| HDRIs / environment maps | Polyhaven (`polyhaven.com/hdris`) | CC0 |
| PBR textures / materials | Polyhaven, ambientCG | CC0 |
| 3D models (GLB / GLTF) | Polyhaven models, Sketchfab CC0, Quaternius, Kenney | CC0 / CC-BY (attribute in code comment) |
| Gaussian splats | Hugging Face splat archives, public Luma AI captures | per-asset |
| Photogrammetry meshes | Open Heritage 3D, Smithsonian 3D Open Access | per-asset |
| Gigapixel / IIIF imagery | National Gallery DC, Rijksmuseum, Getty, Yale Center for British Art, Smithsonian, J. Paul Getty, Wellcome Collection | CC0 / public domain (verify per work) |
| Map tiles | OpenStreetMap raster, MapTiler free tier, Stadia Stamen, MapLibre demo tiles | per-provider (respect attribution + usage policy) |
| Map styles (vector) | MapLibre demo, OpenFreeMap, MapTiler free styles | per-provider |
| Satellite imagery | NASA GIBS WMTS, USGS Landsat, Sentinel Hub free tier | per-provider |
| Terrain / elevation | AWS Terrain Tiles, Mapzen, NASA SRTM | open |
| Geocoded sample data | Natural Earth (countries, cities, terrain), OurAirports, GTFS open transit feeds | CC0 / CC-BY |
| Climate / weather | NOAA, ECMWF open data | open |

**Name the asset specifically in code.** Not `loader.load("model.glb")` but `loader.load("https://dl.polyhaven.org/file/.../delft_window_4k.hdr")` with a one-line comment naming what it is and its licence. Specificity prevents the AI-generic failure mode in 3D too — a generic untextured grey box is the 3D equivalent of a soft purple gradient blob.

### Motion budget — held breath, not entrance fireworks

Scene-based genres unlock motion forbidden in drawing genres, but only the quiet kinds:

- **Held breath of the scene** — slow camera drift, light shifting through a window, dust in a sunbeam, water rippling, painter's hand barely moving. Loops at 0.05–0.3 Hz, amplitude small. The scene feels alive, not performed.
- **Continuous simulation** — particle flow, fluid, shader-driven generative motion at frame rate. Justified when the simulation IS the content.
- **Camera moves on visitor input** — orbit, pan, zoom, dolly. Damped. Inertia. No snap-to.
- **Element transitions inside the scene** — layer fades (surface → underdrawing), depth changes, voice ducking, marker pulses. Mirror the drawing-genre budget: 0.3–0.6s with calm easing.

**Still forbidden:** scroll-jacked camera flythroughs, scroll-tells-a-story gimmicks, entrance-animation fireworks, parallax on everything, particle explosions for state changes, the warehouse Immersive-Van-Gogh kitsch. Motion serves the work; the work never serves the motion.

### Performance and graceful degradation

A scene-based prototype must still open and run on the demo machine.

- **One scene per page.** Don't mount five Three.js canvases on one page; the GPU will choke. Mount on tab activation, dispose on leave.
- **Cap by device pixel ratio.** `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`. Cap mesh complexity at what a five-year-old MacBook can render.
- **Stills path.** If the scene is the front door, always provide a high-fidelity still + spatial-audio alternative for low-bandwidth contexts. Render the still from the same scene or include a baked image.
- **Lazy-load large assets** (splats, HDRIs > 10 MB) behind a visible "Load scene" affordance — never auto-load on page open.

### Accessibility — scenes must still be readable

Drawing genres inherit accessibility from semantic HTML. Scenes don't. Three additions are mandatory:

- **Every scene has an `aria-label` and a text equivalent.** A described still + transcript of any spoken content, reachable from a visible button on the canvas.
- **Keyboard controls for camera moves.** Arrow keys = orbit, +/− = zoom, Home = reset. Documented in a visible legend on the canvas.
- **`prefers-reduced-motion: reduce` respected.** Disables ambient drift, freezes shader animation, falls back to a still.

### Token additions for scene-based prototypes

In addition to the base token block, scene-based prototypes need a small extension at the top of `styles.css` for the canvas-overlaid chrome:

```css
:root {
  /* Scene chrome — overlays floating on the canvas */
  --scene-overlay-bg: oklch(98% 0.002 80 / 0.78);   /* paper, translucent */
  --scene-overlay-border: oklch(50% 0.005 80 / 0.18);
  --scene-overlay-blur: 16px;                        /* glass panel */
  --scene-control: oklch(20% 0.01 80);               /* canvas-readable text */

  /* Scene ambient — sampled from the keystone asset */
  --scene-ink: ...;            /* a deep, scene-derived ink */
  --scene-light: ...;          /* warm tint of the light source */
  --scene-accent: ...;         /* the single curatorial accent for in-canvas affordances */
}
```

Glass panel overlays use `backdrop-filter: blur(var(--scene-overlay-blur))` with the translucent background. **One overlay style across the whole scene** — never per-panel variation.
