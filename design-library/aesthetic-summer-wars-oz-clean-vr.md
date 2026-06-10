---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-summer-wars-oz-clean-vr-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-summer-wars-oz-clean-vr-isolated.png
    reason: Signature motif, isolated.
---
# Summer Wars OZ clean-metaverse (aesthetic)

**Tag:** `aesthetic-summer-wars-oz-clean-vr`

**Canonical references:**
- **Summer Wars** (Mamoru Hosoda, 2009) — the canonical film
- Director: Mamoru Hosoda; CG / virtual-world studio: **Digital Frontier**
- Character designer: Yoshiyuki Sadamoto (Evangelion lineage)
- **OZ** — the in-film metaverse, "clean, white-backdropped one-billion-subscriber" platform
- **King Kazma** — the anthropomorphic snow-hare avatar (the iconic OZ avatar)
- Visual references Hosoda cited: Nintendo first-party game aesthetics, Takashi Murakami superflat
- Sibling reference: **Belle's U metaverse** (2021) — the painterly-sublime evolution by the same director

## Cultural identity

Summer Wars' OZ is **THE canonical "clean white metaverse" aesthetic** — every subsequent VR / virtual-world UI in film, game, advertising, or product design from 2009 to current day either quotes OZ or consciously avoids it. The cultural reading: this is what Mamoru Hosoda's team built when they imagined what a billion-subscriber social-virtual-platform would *look* if it were designed by a Japanese studio that cited Nintendo and Murakami as inspirations.

The defining gesture is the **pure-white solid-colored backdrop populated with diverse mascot avatars** — every account is a single anthropomorphic character (yellow squirrel, snow hare, demon, fish, abstract shape) rendered in flat saturated colors on infinite empty space. The whole metaverse reads as a Murakami superflat painting in motion.

Crucially: **the world is bright, the world is cute, the world is whimsical-but-clean** — OZ from 2009 is decisively NOT cyberpunk-grimy, NOT Tron-dark-with-glow, NOT photoreal Sword-Art-Online. It's the "happy public-internet" aesthetic that existed for a brief moment before the internet became something to fear.

## Palette anchor

- **OZ white** `#FFFFFF` (or `#FCFCFC`) — pure-white infinite backdrop, non-negotiable
- **Block-saturated primaries** for avatars and elements:
  - **Hosoda red** `#FF3B47`
  - **OZ blue** `#3B9DF5`
  - **Mascot yellow** `#FFD12B`
  - **Avatar green** `#2DCB6E`
  - **Account pink** `#FF7DC9`
  - **Profile orange** `#FF8A3B`
- **Soft grey** `#E5E5E5` — secondary surface tone (UI panels)
- **Pure black** `#0A0A0A` — text and outline

Multiple chromatics ARE the system here (unlike most aesthetics in this library). The diversity of saturated colors against pure-white backdrop IS the OZ signature.

## Decoration motifs

**Mandatory signatures:**
- **Pure-white empty space** as the dominant compositional element (60-80% of every frame)
- **Anthropomorphic mascot avatars** as account representations — every user is a unique cute character, never a profile photo. Animals, abstract shapes, food, vehicles — whimsical-diverse menagerie.
- **Floating account / element clouds** — UI elements float in space without ground plane, soft drop-shadow only (suggests perspective without committing to it)
- **Flat-shaded solid-color forms** — avatars are shaded with at most 2-3 flat tones, no gradients, no rim lights
- **Concentric circular "account orbits"** — when avatars move, they sweep along curved paths suggesting an orbital social-graph
- **Account name + speech-bubble labels** in clean rounded type, often with small kawaii flourishes

**Animation grammar:**
- Slow drift / float of avatars in idle states (no rigid grid layout — everything bobs)
- Cute squash-and-stretch on interactions (button presses, profile reveals)
- Expansion/collapse animations that puff outward with elastic ease
- Single-tone background never changes, but everything ON IT moves constantly

**Forbidden:** dark mode, cyberpunk neon, photoreal avatars, glass-blur backdrops, Tron-emissive edge glow, grit textures, scanlines, VHS overlays. Those belong to the sibling lane (Belle's U is colder; ZZZ is grimier-urban). OZ is bright, white, optimistic.

## Voice register

Friendly, accessible, multilingual-as-mascot-name-tags. Examples:
- "Welcome, King Kazma!"
- "Friend request from うさぎ太郎"
- "OZ Status: 1,000,000,000 active accounts"
- "You have 12 new messages."

Sentence case, often with small mascot-flavor flourishes. Translated-from-Japanese register, slightly cheerful. Never marketing-corporate, never tech-clinical, never edgy-meme.

## Raster requirement

This aesthetic is **rasterized character art carrying the entire identity** — OZ without the mascot avatars is just a white page. Each "account" or "user" must be a hand-designed flat-shaded character with personality. Stock illustrations break the register instantly because the OZ avatar style is specifically *whimsical-individual* — every one is different. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

A white page with a Memoji-style 3D profile photo and a generic Inter sans interface = generic social-app, not OZ. OZ's signature is the SPECIFIC flat-shaded individual-mascot avatar discipline + pure-white emptiness + floating-without-grid composition + Murakami-superflat color saturation. Skip those and it's just "white minimalism."

Second tell: photoreal avatars or generic profile photos. OZ avatars are 100% hand-illustrated mascots, never realistic.

Third tell: dark mode. OZ is white-substrate-native — toggling to dark mode collapses the brand.

Fourth tell: rigid grid layout. OZ floats — orbits, drifts, bobs. Stiff grids are wrong.

Fifth tell: heavy chrome / borders / shadows. OZ uses soft drop-shadow only, never heavy outlines or stamps.

Sixth tell: mixing with Belle's U cathedral-painterly aesthetic. OZ is 2009-cute-public-internet; U is 2021-sublime-lonely-metaverse. They're siblings but distinct generations — never combine.

## Best for

- Social network / community platforms (especially with avatar systems)
- Children's / family-oriented digital products
- Virtual event platforms wanting "happy public-internet" register
- Gaming companion / friend-list / online-lobby UIs
- Companion sites for Hosoda films
- Cute / mascot-driven brand identity work
- Y2K-revival projects (OZ was 2009 but its bright-cute-public-internet vibe is the Y2K-spirit refined)
- VTuber / streamer platform branding
- Wholesome metaverse / spatial-computing products

## Pairs well with

- **Shells:** `shell-canvas-floating` (the canonical use — avatars floating in white space), `shell-mobile-app`, `shell-masonry`, `shell-centered-column`
- **Styles:** `style-flat-design`, `style-claymorphism` (when the avatars want softer dimensionality), `style-skeuomorphism` (for kawaii-mascot detail work), `style-bold-display`
