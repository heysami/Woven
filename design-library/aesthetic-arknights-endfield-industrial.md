---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-arknights-endfield-industrial-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-arknights-endfield-industrial-isolated.png
    reason: Signature motif, isolated.
---
# Arknights Endfield clean-industrial (aesthetic)

**Tag:** `aesthetic-arknights-endfield-industrial`

**Canonical references:**
- **Arknights: Endfield** by Hypergryph (2024-current) — the canonical title
- **Talos-II** setting + **Endfield Industries** corporate identity within the game
- Game UI Database — Arknights / Endfield entries (gameuidatabase.com/gameData.php?id=478)
- "Analysis of the Aesthetic System in Arknights" — Oreate AI design analysis
- Sibling references: parent Arknights mobile UI, ACRONYM streetwear, post-Bauhaus industrial Swiss-modernist work, NASA / SpaceX engineering signage

## Cultural identity

Arknights: Endfield's aesthetic is the **highly industrial but clean** lane that's hard to deliver — most "industrial" briefs collapse to either dieselpunk-gritty or sterile-corporate-boring. Endfield threads the needle by committing to **triangle geometry as a DNA motif** woven through every layer: architecture, mechanical devices, environmental decor, character costuming, UI panels, even font construction. The triangle is the through-line.

The cultural reading: this is what a Chinese game studio (Hypergryph) builds when they refuse both the JRPG fantasy register AND the cyberpunk-grunge register, landing instead on **precise corporate-tactical futurism** — Endfield Industries reads as a real engineering firm whose visual identity could hang in a real architecture office. The brand-tactical fashion crossover (techwear merch with the triangle DNA) confirms the discipline is consciously cross-medium.

The defining gesture is **sharp clean lines + holographic projections + floating modular interfaces** — HUD elements appear suspended in space as if projected from devices, never as flat overlays. The aesthetic is industrial but *engineered-clean*, not weathered.

## Palette anchor

- **Endfield steel** `#2C3138` — primary dark substrate (cool grey, not blue, not green)
- **Talos concrete** `#A8AEB4` — secondary mid-grey for panels
- **Hi-vis caution amber** `#FFB000` — single warning chromatic
- **Endfield cyan** `#3FB5C5` — UI active state, holographic projection
- **Pure white** `#FAFAFA` — primary text, hologram fill
- **Deep ink** `#0C0E12` — text contrast and shadow base
- Accent (optional, one only): **Endministrator orange** `#FF6A2C` for hero / hero-character

Restrained palette discipline — at most 3 hues per screen including substrate. Hi-vis amber and orange are NEVER on screen together; pick one.

## Decoration motifs

**Mandatory — the triangle DNA:**
- **Triangle (equilateral or right-angled) appears at every scale** — in icon construction, in panel corners, in tile-pattern backgrounds, in mechanical-device silhouettes, in architectural facade vocabulary, in cursor / pointer shapes
- The triangle is *modular* — composed shapes break down to triangle primitives, never to circles or squares
- **Hexagonal grids** as a secondary background pattern (triangles tessellated)

**Engineering signage vocabulary:**
- **Hairline 1px frame** around every floating panel (no shadow, no blur — line only)
- **Hi-vis amber hazard chevrons** on safety-critical UI states
- **Catalogue / equipment-spec readouts** with mono numerals (Series IDs, calibration values, capacity counters)
- **Holographic projection grain** — subtle vertical-scanline overlay (1-2% opacity) on UI panels to suggest projected-from-emitter, not flat-overlay
- **Triangle-corner accents** on interactive elements (4 small triangular ticks at panel corners — Endfield's signature flourish)

**Iconography:** custom triangulated symbols, no Lucide / Material defaults. Always small text labels under icons.

**Forbidden:** soft skeuomorphism (no gradient buttons, no rounded corners > 4px, no soft shadows), Aurora-mesh chromatics, decorative ornament that isn't structural, friendly mascot characters.

## Voice register

Corporate-tactical, declarative, mildly clinical — sibling of DORFic but warmer and less hostile. Examples:
- "Endfield Industries / Sector 04 Operational"
- "Operator dispatched: Wulfgard, calibration nominal."
- "Cargo throughput: 2,400 units / shift"
- "Endministrator authorization confirmed."

Title case for headlines, sentence case for body, ALL-CAPS tracked for system labels. Never warm-marketing, never gamer-bro, never lowercase-defiant. The voice matches the engineered visual register.

## Raster requirement

Character art (clean-line painted illustrations of operators in techwear) and architectural concept art (Talos-II city renderings) are the brand carriers. UI chrome alone is engineering-clean but emotionally cold — it needs the character/architecture raster to read as Endfield. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

Generic dark-mode dashboard with cyan accents and "industrial-looking" graph cards — that's enterprise-fintech-dashboard cosplay. Endfield's specific tell is the TRIANGLE DNA discipline at every scale + the holographic-projection grain + the triangle-corner-tick frame accents. Skip those and it collapses to generic B2B.

Second tell: weathered / grimy / oil-stained surfaces. That's dieselpunk. Endfield is engineered-CLEAN — surfaces are matte-precision, not weathered.

Third tell: rounded corners > 4px. Endfield is sharp.

Fourth tell: multi-color UI states (success-green + warning-yellow + error-red + info-blue all on one screen). Endfield's discipline is hi-vis amber for warning, cyan for info, nothing else. Most "states" use weight/opacity instead of color.

Fifth tell: missing the triangle DNA. If no triangulated geometry appears in icon, frame, or background pattern, the visual identity is gone.

## Best for

- B2B engineering / industrial software (logistics, robotics, manufacturing, defence-adjacent)
- Game UI prototypes (especially tactical RPG, strategy, sim-management)
- Premium hardware product launches (Ledger-Stax-tier devices, dev hardware, wearables)
- Crypto / web3 with "infrastructure" positioning (DePIN-adjacent — though we just removed that aesthetic, the brief lives on)
- Architecture / engineering firm portfolios
- Conference sites for game-dev / hardware / industrial-design industries
- Companion apps for Arknights / Endfield titles

## Pairs well with

- **Shells:** `shell-canvas-floating` (the projected-hologram canonical use), `shell-three-column-app`, `shell-top-bar-canvas`, `shell-bento-grid`
- **Styles:** `style-dense-mono-dark`, `style-terminal-mono`, `style-restrained-hairline`, `style-oversized-neo-grotesque`, `style-flat-design`
