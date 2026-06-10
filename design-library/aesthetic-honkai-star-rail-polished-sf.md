---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-honkai-star-rail-polished-sf-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-honkai-star-rail-polished-sf-isolated.png
    reason: Signature motif, isolated.
---
# Honkai Star Rail polished sci-fantasy UI (aesthetic)

**Tag:** `aesthetic-honkai-star-rail-polished-sf`

**Canonical references:**
- **Honkai: Star Rail** by HoYoverse (2023-current) — the canonical title
- Game UI Database — Honkai Star Rail entry (interfaceingame.com/games/honkai-star-rail)
- ArtStation "Independent UI/UX Case Study: Honkai Star Rail" by Eyween
- HSR UI Elements Pack (acrock.itch.io) — community-curated grammar
- Sibling reference: Genshin Impact UI (HoYoverse's parent grammar), but HSR refines the parent's busy moments
- Persona series UI sensibility as a distant ancestor (kinetic but restrained)

## Cultural identity

Honkai: Star Rail's interface is one of the most-quoted modern game-UI grammars — it earned that status by **balancing functionality and flavor without tipping into noise**. Every flavor element (ornate frame corners, runic side-marks, secondary dot animations above and below buttons) is *just enough* — never too much. The cultural reading: this is what high-budget Chinese game studios converged on in 2023 as the sophisticated "polished sci-fantasy" UI register — fantasy ornament married to sci-fi clarity, applied to a JRPG turn-based combat system.

The defining gesture is the **functionality + flavor balance**: every interactive element has a clearly readable core (button, panel, label) plus a thin ornamental frame that signals "this is from the Star Rail universe" without obstructing function. The UI is either the **center of attention** (combat menus, character cards) or in **support of other elements** (HUD chrome, world UI) — never decorative noise that competes for attention.

## Palette anchor

- **Deep space ink** `#0A0E1F` — the canonical dark substrate
- **Cosmic purple** `#5A3FA0` → `#7B5FC9` — primary brand chromatic
- **Stellaron teal** `#1FCDD0` — accent / highlight / catalyst color
- **Pathfinder gold** `#E8C672` — premium / reward / hero-card chromatic
- **Pure white** `#FFFFFF` — primary text
- **Neutral grey** `#8A8FA8` — secondary text / inactive states

Typically two chromatics per screen (purple + teal, OR purple + gold). Never four. The dark substrate is non-negotiable — HSR on light mode collapses to generic web app.

## Decoration motifs

**Frame elements (signature):**
- **Hexagonal corner ornaments** at panel intersections — small triangular accents, often gold-foil on dark
- **Hairline runic side-marks** along the long edges of menu panels — geometric not figurative
- **Dot animations** secondary to the primary motion (the "dots above and below" tell — a small ⋅⋅⋅ that pulses during state changes)
- **Soft outer glow** on selected items (5-10px purple bloom), NOT a heavy drop shadow

**Iconography:** custom in-universe symbols (paths, elements, types) rather than generic Lucide / Material icons. Always paired with a small text label — never icon-only.

**Animation grammar:**
- **Special-move sequences** as the visual climax — 2D character art swept across a transition into 3D animation
- **Highlight-traverse** — a thin highlight line travels across a button when selected (≈400ms ease-out)
- **Card-flip + cross-fade** for navigation transitions
- **Subtle parallax** on background art when scrolling lists

## Voice register

Sci-fantasy formal — mythological + technological vocabulary mixed naturally. Examples:
- "Stellaron Hunters — Path of Destruction"
- "Light Cone equipped: In the Night"
- "Trailblaze EXP: 1,240 / 2,400"

Title case for headlines, sentence case for descriptions. Translated-from-Chinese register (slightly elevated phrasing, never colloquial). Never lowercase-defiant, never meme-y, never "let's go!" gamer-bro.

## Raster requirement

Character art (high-fidelity 2D illustrations on dark cosmic backgrounds) is the carrier of brand identity. The UI chrome alone is just dark panels with gold frame corners — it needs the painted character cards to read as Star Rail. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

Generic dark-mode game UI with purple accent and a wizard icon — that's "fantasy MMO 2010s tell." HSR's signature is the SPECIFIC corner-ornament discipline + the dot-animation pacing + the hexagonal frame grammar. Skip those and it reads as Diablo IV menu.

Second tell: too much ornament. Every panel framed with elaborate filigree borders = early-2000s WoW gold-leaf cosplay, not HSR. HSR's ornament is restrained — corners only, not full borders.

Third tell: animation that doesn't punctuate. HSR animations have a **start, climax, settle** rhythm. Linear loops that just rotate forever are wrong register.

Fourth tell: light mode. HSR is dark-substrate-native.

Fifth tell: more than two chromatics. Purple + teal + gold + green + red = busy mobile-game store screen, not the calm-with-flavor HSR signature.

## Best for

- Game UI prototypes (especially JRPG / gacha / fantasy-RPG / live-service)
- Web3 / NFT projects wanting "sci-fantasy premium" register (NOT the cyber-punk register)
- Fantasy / sci-fi reading or worldbuilding apps
- Conference sites for game-dev / VTuber / anime industry
- Premium subscription tiers ("Trailblazer" / "Founder" / "Stellar" branding)
- Companion apps for HoYoverse titles or HSR-adjacent fan tools
- Astronomy / space-themed consumer products that want depth without sterility

## Pairs well with

- **Shells:** `shell-mobile-app`, `shell-canvas-floating`, `shell-three-column-app`, `shell-hero-stack`
- **Styles:** `style-glassmorphism` (the panel-blur variant of HSR's HUD), `style-aurorism`, `style-holographic`, `style-dense-mono-dark` (for system-spec readouts inside HSR panels)
