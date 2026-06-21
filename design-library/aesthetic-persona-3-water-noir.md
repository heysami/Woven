---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-persona-3-water-noir-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-persona-3-water-noir-isolated.png
    reason: Signature motif, isolated.
---
# Persona 3 Reload water-noir UI (aesthetic)

**Tag:** `aesthetic-persona-3-water-noir`

**Canonical references:**
- **Persona 3 Reload** (Atlus 2024) - the canonical title (modernized remake of original Persona 3, 2006)
- "Persona 3 Reload Art Design and Direction Interview" - Persona Central
- Automaton West feature: "Persona 3 Reload's viral 'sexy UI'"
- "A Love Letter to Persona 3 Reload's UI" - Michelle Kwan on Medium
- Game UI Database - Persona 3 Reload entry (gameuidatabase.com/gameData.php?id=1884)
- Sibling reference: **Persona 5 heist-pop** (the active red sibling - opposite emotional register)
- Visual ancestors: noir cinematography, Wong Kar-wai water-window-light, Tatsumi Port Island sea iconography, Edo-period sumi-e water-flow, fashion editorial cyan-and-melancholy 2010s era

## Cultural identity

If Persona 5 is the aggressive-kinetic-red sibling, **Persona 3 Reload is the melancholic-flowing-cyan sibling**. Same studio (Atlus / P-Studio), same author lineage, opposite emotional register. The Reload UI designers consciously made the move: P5 was the aggressive comparison, so P3 needed **slower softer animations**, **water-themed transitions** (sinking, submerging, flowing, glass-shard reflections), and a palette closer to **cyan than to the original P3's deep navy**.

The cultural reading: this is what happens when a 2024 design team revisits a 2006 game whose original color was "blue that evokes death" - they keep the death-blue heart but modernize the cyan toward **"tranquility, youth, and energy"** appropriate for high-school-students-on-an-island-city. The aesthetic carries melancholy without despair - it's "the sea around Tatsumi Port Island," not "the bottom of the abyss."

The defining gesture is the **water motif at every layer** - menu transitions animate as if elements are sinking into water, character cards are reflected in glass-shard surfaces, the main-menu logo animates as if submerged. Even the typography choices feel "submerged" (slightly heavier weights, more letter-spacing, slower kerning rhythm).

## Palette anchor

- **Seaside cyan** `#1FC2D9` → `#5FDDEC` - primary brand chromatic (modernized from original P3's navy)
- **Reload navy** `#0A1E3D` - dark substrate, the deep-end of the pool
- **Glass shard white** `#EAF5F9` - text and reflection-highlight color (cool-cast white, never warm)
- **Armband red** `#D62B30` - the single warm accent (SEES armband color), used sparingly
- **Bubble pale** `#A8D4DC` - secondary highlight tone
- **Pure black** `#000510` - text contrast and shadow base

Three-color discipline like P5, but cyan-navy-paper instead of red-black-paper. The armband red appears as a single accent (often one small dot or tag), never as a button-fill or large area.

## Decoration motifs

**Mandatory signatures (the water grammar):**
- **Submerging transition** - when a menu opens, the previous element appears to sink downward as new content rises from below (slow 600-800ms ease)
- **Bubbles** rising through panels during loading / waiting states (subtle, 3-5 small bubbles per second drifting upward)
- **Glass-shard reflection** - character portraits reflected in faceted-glass surfaces, with displaced color-shift
- **Card-flip with cyan glow trail** - when cards flip to reveal options, a cyan trail follows the flip edge
- **Flowing-water surface ripple** as a background animation behind static panels (very subtle - 1-2% movement)
- **Vertical Japanese text strip** along one side of panels, slightly distorted as if seen through water (slight chromatic aberration)

**Iconography:** custom underwater-inspired symbols (waveforms, droplets, bubbles), always with text labels. Never generic Lucide / Material icons.

**Forbidden:** P5's aggressive diagonal slashes, ransom-note typography, halftone silhouettes, chamfered angular corners (those are sibling-only), warm colors beyond the single armband-red dot, fast-cut transitions.

## Voice register

Quiet, contemplative, slightly poetic. Examples:
- "The night is upon us."
- "Memento mori. / 死を忘れるな."
- "S.E.E.S. - Specialized Extracurricular Execution Squad"
- "Tartarus shifts. Proceed."

Sentence case for body, title case for headlines, lower-fronted serif (Source Serif or similar) for melancholic moments. Translated-from-Japanese register, slightly literary. Never aggressive-CAPS, never marketing-warm, never lowercase-meme.

## Raster requirement

Character portraits (painted-and-photographed style with strong cyan rim-light) and **water-surface texture references** (rippling pool surfaces, condensation on glass, blurred underwater photography) are the brand carriers. Pure SVG P3 doesn't reach the submerged-melancholy register. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

Cyan + navy + white on a page with normal Inter typography and snappy 200ms transitions = "we used blue" cosplay. P3's signature is the SPECIFIC slow-water-grammar discipline (submerging transitions, bubble effects, glass-shard reflections, distorted vertical Japanese text) plus the cool-cast cyan palette. Skip those and it reads as generic dark-mode SaaS with a cyan accent.

Second tell: aggressive animation timing. P3 transitions are 600-800ms, slow and contemplative. P5's 200-300ms snap is the wrong rhythm.

Third tell: warm colors. P3's only warm element is the single armband-red dot - adding warm-orange or warm-yellow breaks the cool-cast water register instantly.

Fourth tell: hard-edge geometric chrome. P3 favors slight asymmetric distortion as if seen through water - pure-precise Swiss grid is the wrong sibling.

Fifth tell: P5 motifs (diagonal slashes, halftone silhouettes, ransom-note type). The two aesthetics are deliberate opposites - mixing them collapses both registers.

## Best for

- Reflective / contemplative consumer products (journaling apps, meditation, mental-health adjacent)
- Music streaming for ambient / lo-fi / shoegaze / mono-no-aware register
- Indie game studios with melancholic / coming-of-age narrative sensibility
- High-school / coming-of-age fiction sites
- Memorial / commemoration / archive sites
- Companion apps for Persona-series titles (the P3 sibling specifically)
- Aquarium / marine-research / oceanography sites
- Fashion editorial pages with melancholic-youth register

## Pairs well with

- **Shells:** `shell-mobile-app`, `shell-canvas-floating`, `shell-centered-column`, `shell-hero-stack`
- **Styles:** `style-glassmorphism` (the glass-shard reflection variant), `style-liquid-glass`, `style-restrained-hairline`, `style-serif-warm-paper` (inverted to cool/cyan)
