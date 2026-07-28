---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-persona-5-heist-pop-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-persona-5-heist-pop-isolated.png
    reason: Signature motif, isolated.
# Orchestrator hint for the plan gate. NOT a mandate: the gate still proposes
# and the user still decides. It exists because this entry's defining quality
# NEEDS a medium a CSS build cannot reach, and that intent was previously only
# prose no gate could read.
suggestsOrchestrator:
  - sound-orchestrator
suggestsOrchestratorWhy: Animation pacing is sound-effect-synced: every UI motion lands on a click or paper-crinkle.
---
# Persona 5 heist-pop UI (aesthetic)

**Tag:** `aesthetic-persona-5-heist-pop`

**Canonical references:**
- **Persona 5** (Atlus 2016) + **Persona 5 Royal** (2019) - the canonical titles
- UI designer: **Masayoshi Sutou** (Atlus) - the credited author of the style
- Game UI Database - Persona 5 and Persona 5 Royal entries
- "Atlus Reveals The Design Secrets Behind Persona 5's Distinctive UI" - Siliconera 2017 interview
- p5ui.tumblr.com - community-curated archive of every menu screen
- Visual ancestors: Cowboy Bebop title sequences (Sunrise / Yoko Kanno era), Samurai Champloo (Manglobe / Nujabes era), Saul Bass mid-century film posters, Bauhaus heist-movie iconography, French New Wave (À bout de souffle credits)

## Cultural identity

Persona 5's UI is widely considered the **most influential JRPG menu design of the 2010s** - Atlus credits the success to a single design move: treating the menu as a stylish-anime title sequence rather than a database to look at. Every screen has the kinetic energy of an opening credits roll, with motion design carrying functional information.

The cultural reading: this is what a Japanese studio (Atlus / P-Studio) built when they refused the conventional JRPG menu vocabulary (parchment scrolls, square dialog boxes, gold-leaf borders) and instead committed to **heist-movie graphic-design language** - ransom-note typography, halftone silhouettes, sharp angular edges, RED as the active color of theft and confidence.

The defining gesture is **everything-tilted** - text labels rotate -8° to +8°, edges chamfer rather than meet at 90°, transition animations don't fade-in/fade-out but slash-and-swipe like a knife cut. The aesthetic IS the kinetic confidence.

**Persona 5 vs Persona 3 Reload:** these are siblings (both Atlus, both styled by P-Studio) but tonally opposite. P5 is aggressive-kinetic-red; P3 Reload is melancholic-flowing-cyan. Pick the one that matches the project's emotional register; never mix the two.

## Palette anchor

- **Phantom red** `#E50914` (or `#D31E2A`) - the active passionate red, the genre's whole identity
- **Pure black** `#0A0A0A` - never `#222`, never softened
- **Off-white paper** `#F5F0E5` (slightly warm, never pure white) - secondary substrate
- **Health-bar yellow** `#FFD700` and **MP cyan** `#4FC3F7` - the ONLY sub-colors permitted, and exclusively for HP/MP gauges (literally the only place the canonical game allowed sub-color)
- **Halftone dot black** for shadow tone variations

Three-color discipline is non-negotiable: red, black, paper. Adding a fourth chromatic to a P5-aesthetic screen instantly breaks the register.

## Decoration motifs

**Mandatory signatures:**
- **Angular edged boxes** - every container has at least one corner cut diagonally (chamfered), never four rounded corners, never four 90° corners
- **Halftone character silhouettes** - full-figure pose silhouettes in red-over-black, halftone-dotted, used as compositional anchors at edges of frame
- **Ransom-note typography** - display text mixes multiple typefaces and weights *within a single word*, like a magazine cutout pasted together (catalog serif + chunky sans + slanted script in one wordmark)
- **Red diagonal slash motion line** - when a menu opens, a thick red line draws diagonally across the screen, then the menu appears in its wake (the canonical "red line draws the eye"). ALWAYS present at menu state changes.
- **Vertical text strips** - small vertical Japanese text running up the side of panels (decorative + flavor)
- **Negative-space arrow shapes** carved into red blocks (the All-Out Attack visual)

**Animation grammar:**
- Slash-and-swipe transitions (left-right wipes with a thick black or red leading edge), 200-300ms ease-out
- Tilted-rotation reveal - elements rotate from -15° to 0° as they enter
- Multi-layer asymmetric parallax during scrolling
- Sound-effect-synced animation pacing (every UI motion in canonical P5 has a slot-machine *click* or paper-crinkle sound)

**Forbidden:** rounded buttons, gradient fills, soft drop shadows, generic Material / Lucide icons, more than 3 colors on screen, centered-symmetric compositions, smooth fade-in/out transitions (slash and cut, never fade).

## Voice register

Sharp, confident, slightly mischievous. Examples:
- "TAKE YOUR HEART"
- "ALL-OUT ATTACK"
- "Your skills will be needed."
- "The shadow has been defeated."

Title-case bold for headlines, ALL-CAPS for system actions, sentence case for dialog. Translated-from-Japanese register (slightly elevated phrasing). Never lowercase-defiant, never marketing-corporate, never gamer-bro "let's go."

## Raster requirement

This aesthetic needs raster for the **halftone character silhouettes** and the **painted character portraits** that anchor each scene. SVG-only P5 is just red rectangles tilted slightly - without the silhouette artwork and painted portraits, the heist register doesn't land. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

Red + black + white color palette on a page with normal centered Inter typography and standard rounded buttons = "we used red" cosplay, not P5. The aesthetic's signature is the SPECIFIC kinetic-typography + chamfered-corner + ransom-note + halftone-silhouette + diagonal-slash discipline. Skip any one of those and it doesn't read as P5.

Second tell: more than 3 colors on screen. P5 is famously disciplined - even sub-colors only appear on HP/MP gauges. A green button next to a red button next to a blue link instantly breaks the register.

Third tell: smooth transitions. P5 cuts and slashes - fading is the wrong rhythm.

Fourth tell: symmetric centered compositions. P5 is asymmetric-tilted by design.

Fifth tell: clean single-typeface wordmarks. The ransom-note typography is the genre tell.

## Best for

- Music streaming / album drops (especially rap, electronic, indie-rock)
- Indie game studio sites with heist / action / stylish-anime sensibility
- Streetwear / sneaker collab drop pages
- Conference / event sites for design and gaming
- Companion apps for Persona-series titles
- Crypto / web3 with "stylish heist" positioning
- Anime / manga sites with action register
- High-energy product launches (sports drinks, energy products, gaming peripherals)

## Pairs well with

- **Shells:** `shell-mobile-app`, `shell-canvas-floating`, `shell-editorial-broken-grid`, `shell-hero-stack`
- **Styles:** `style-neubrutalism` (the sticker-tilted-shadow grammar overlaps), `style-bold-display`, `style-oversized-neo-grotesque`, `style-pixel-bitmap` (for the halftone discipline)
