---
name: preflight-checklist
description: The full pre-flight checklist — every checkbox the agent walks BEFORE declaring a prototype "done". Covers genre commit, tokens, layout, type, graphics, voice, motion, Woven-specific manifest + storyboard + demo-dock + gallery + slot-annotation checks, and scene-based extras (skip-if-drawing-only). Loaded at Phase F (final review) before reporting completion.

→ Decision lives in PROTOTYPE.md §"Pre-flight checklist".
---

# Pre-flight checklist

- [ ] Genre was decided explicitly using the six axes (or the closest-shipped-product test).
- [ ] Genre is committed in a top-of-file comment so drift is obvious.
- [ ] Page shell matches the genre.
- [ ] Macro proportions are recalled values (1:2:1, `260+1fr`, `65ch`, 12-col bento), not invented.
- [ ] Density gradient is right: periphery dense, center breathable.
- [ ] Token block covers: surfaces · text · semantic + `-soft` · type stack · radii · shadows · spacing · **shape language**.
- [ ] All colors are OKLCH (or hex only where brand-mandated).
- [ ] Chroma calibrated to genre (see [`step-tokens.md`](./prototype/step-tokens.md)).
- [ ] At most 5 type sizes; at most 2 fonts; second font has assigned job.
- [ ] One stroke weight, one endcap style, one icon fill style across all graphics.
- [ ] All list rows share one grid-template-columns; `min-width: 0` on the flexible cell.
- [ ] Numbers in columns use mono or `tabular-nums`.
- [ ] No icon library imported — icons inline SVG matching shape-language tokens.
- [ ] No build step. Opens by double-clicking the HTML.
- [ ] No `fetch`, no API. All data is `window.DEMO`.
- [ ] Demo data has named entities, specific numbers, voiced microcopy.
- [ ] **Voice is consistent across every string** — panels, buttons, errors, microcopy.
- [ ] **Slot budgets respected** — buttons aren't paragraphs, descriptions aren't headlines.
- [ ] **Information density of language matches information density of layout.**
- [ ] **No generic stock illustrations**, soft gradient blobs, or isometric scenes unless genre-specific imagery was named.
- [ ] **Functional graphics carry real data** with believable story; decorative graphics earn pixels via genre.
- [ ] At most one decorative move per page.
- [ ] Motion matches genre — none in brutalist, ambient in product UI, scroll-driven in marketing.
- [ ] No drop shadows beyond `--shadow-sm` except on overlays.
- [ ] No gradients except meaningful data gradients OR genre-mandated.
- [ ] No `<Card>` / `<Button>` wrappers unless used 5+ times.
- [ ] No `console.log`, no commented-out code, no unused tokens, no dead CSS.

**Woven repo-specific checks:**

- [ ] `prototype.json` is written alongside the source — frames / arrows / lanes / IA inferred per AGENTS.md.
- [ ] Multi-HTML projects use `index.html` as a Step 0b storyboard (personas + workflow cards + page inventory + no UI chrome); the storyboard itself is metadata, never a Canvas frame / Flow node / Prototype iframe.
- [ ] Every prototype-only switcher (view / persona / stage / time) is in a **Demo dock §11**, not inline; dock self-hides when iframed and on `?demo=off`.
- [ ] `design-systems/<dsRef.id>/gallery.html` (§12) renders every primitive variant in idle state inside `.ds-sample` blocks with REAL product class names. Gallery chrome uses `.ds-*` prefix only; product classes never carry `.ds-*`. Selectors resolve on first load. (Feature-page authors don't write this file — Workflow 0 / 6b owns it. This checkbox is for the DS-builder and DS-update workflows.)
- [ ] Every visual slot is annotated for **Subagent 1.V** — `img-placeholder` for static imagery, `motion-placeholder` for decorative loops, each carrying `data-slot` + (`data-asset-intent` or `data-motion`). Functional motion stays inline in `styles.css`.

**Scene-based prototypes — additional checks (skip if drawing-only):**
- [ ] Scene gate was opened by the brief itself (inhabitable space, real geography, deep-zoom, shader, globe, splat, spatial audio) — not added as decoration.
- [ ] If hybrid: one drawing genre committed for the chrome; each scene moment commits its own scene-based genre. No blended scene genres inside a single moment.
- [ ] Scene-overlay tokens are derived (via `color-mix` or direct reference) from the chrome's drawing-genre tokens — never invented neon.
- [ ] Voice register is consistent across chrome and scene overlays (no marketing-flat captions inside a curatorial scene).
- [ ] Only one scene instance live at a time — mount on route entry, dispose on exit. No simultaneous Three.js + OpenSeadragon + MapLibre instances.
- [ ] Runtime libraries loaded via ESM importmap CDN; no Webpack / Vite / Next.
- [ ] Real assets named in code with source URL and licence comment — Polyhaven HDRI, public IIIF endpoint, real coordinates, Open Heritage mesh, etc. No untextured grey boxes, no `[0,0]` coordinates.
- [ ] No default Leaflet pin, no `globe.gl` placeholder texture, no Shadertoy plasma noise.
- [ ] Motion is held-breath, not entrance fireworks. No scroll-jacked flythroughs.
- [ ] `prefers-reduced-motion: reduce` falls back to a still.
- [ ] Keyboard controls present (arrows = orbit, +/− = zoom, Home = reset) and documented in a visible legend.
- [ ] Every canvas has an `aria-label` and a text/still equivalent reachable from a visible button.
- [ ] `setPixelRatio` capped at 2; large assets (>10 MB) gated behind a visible Load affordance.
- [ ] Shader uniforms read from the design tokens (OKLCH accent → `uniform vec3`), not invented neon.
- [ ] Spatial audio uses `PannerNode` with listener tied to the camera; transcript visible and synced.

---

