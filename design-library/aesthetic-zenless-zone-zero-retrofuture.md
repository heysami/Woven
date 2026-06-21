---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-zenless-zone-zero-retrofuture-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-zenless-zone-zero-retrofuture-isolated.png
    reason: Signature motif, isolated.
---
# Zenless Zone Zero retrofuture urban (aesthetic)

**Tag:** `aesthetic-zenless-zone-zero-retrofuture`

**Canonical references:**
- **Zenless Zone Zero** by HoYoverse (2024-current) - the canonical title
- **New Eridu** city setting - Sixth Street, Lumina Square, Blazewood districts
- Z·Z·Z Behance UI concept design (behance.net/gallery/188673799)
- Zenless website UI concept on Figma Community
- Direct ancestors: Jet Set Radio (Sega 2000), Persona 5 (kinetic-pop UI), 90s VHS / CRT TV graphics, hip-hop golden-age (Wu-Tang, Native Tongues) cover art

## Cultural identity

Zenless Zone Zero (ZZZ) is HoYoverse's deliberate counter-pole to Honkai Star Rail's polished sci-fantasy - it leans **gritty-neon-urban** instead of cosmic-polished. The aesthetic mashes 90s street culture + golden-age hip-hop + analog tech (VHS tapes, vinyl records, CRT television sets) with sci-fi infrastructure ("Ether energy corruption" justifies the in-lore presence of both VHS *and* smartphones).

The defining cultural reading: this is what a HoYoverse art team built when they wanted to refuse Genshin / Star Rail's high-fantasy and instead worship 1990s NYC street culture filtered through a Tokyo art studio's nostalgia for it. New Eridu's UI mimics **old TV screens and VHS aesthetics** - when you open the in-game phone interface, it reads as a CRT boot screen, not an iOS app.

The aesthetic is **distinct from cyberpunk** because cyberpunk is grimy-dystopian and ZZZ is groovy-optimistic-urban - the city is dangerous but the soundtrack is funky and the characters are cool, not desperate.

## Palette anchor

- **Concrete grey** `#3A3A3F` and `#2A2A2E` - the urban substrate
- **Neon pink** `#FF3D7F` - Bangboo / Sixth Street accent
- **Cyan-cyber** `#00E5FF` - UI active state, holographic HUD
- **Sodium-streetlight orange** `#FFA94D` - late-night-urban warmth
- **Hazard yellow** `#FFD60A` - Hollow Zero warning chromatic
- **Pure black** `#0A0A0C` - VHS-letterbox bars
- **Off-white CRT** `#E8E5DA` - old-television raster off-white (NOT pure white)

Always neon-on-concrete. Always at least one chroma. Often two neons fighting (pink + cyan).

## Decoration motifs

**Mandatory analog-tech artifacts:**
- **VHS tracking-bar overlays** at top/bottom of frame
- **CRT scanlines** (1px horizontal, 50-70% opacity, multiply-blended)
- **Cassette tape labels** with hand-written marker type as section dividers
- **Vinyl record sleeve** layout grammar for character cards
- **Old TV CRT bezel / chassis frame** around hero compositions
- **"REC" red circle + timecode overlay** in the corner of video / live elements
- **Static/snow noise burst** as page-transition reveal

**Period-appropriate iconography:** boomboxes, walkmen, pagers, payphones, magnetic-stripe metro passes, graffiti-style spray-paint marks, hip-hop chain pendants, sneaker silhouettes.

**Forbidden:** clean iOS-style UI glass, soft Material drop shadows, generic dark-mode SaaS chrome, Frutiger-Aero bubbles, polished Honkai-Star-Rail hexagonal frame corners (that's the sibling aesthetic - different register).

## Voice register

Slang-heavy, casual, urban, ALL-CAPS shouting for system labels and lowercase for character chatter. Examples:
- "PUBLIC SECURITY BUREAU // INVESTIGATION CASE #0042"
- "yo, what's the move tonight?"
- "Bangboo Authentication: ID 6-EM-024"
- "DJ Zhu Yuan now spinning at the Sixth Street Cafe."

Mixed Latin + occasional Japanese / Chinese signage detail (street-bilingual, not formally bilingual). Never marketing-corporate, never high-fantasy-formal - that's the wrong sister.

## Raster requirement

This aesthetic ABSOLUTELY needs raster - VHS noise textures, CRT scanlines, graffiti tags, cassette-tape labels, painted character art on streetwear backgrounds. SVG-only ZZZ collapses to "dark page with neon font" - losing the whole analog-tech-meets-sci-fi soul. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

Stock cyberpunk-2077 dark-mode dashboard with magenta-cyan neon + a generic "Tokyo at night" stock photo background = cyberpunk cosplay, not ZZZ. ZZZ has the SPECIFIC analog-artifact discipline (VHS bars + CRT scanlines + cassette labels + spray-paint tags) that cyberpunk doesn't.

Second tell: pure photoreal modern interface elements (Apple SF Pro on a smartphone mockup) - ZZZ's in-world phones look like CRT boot screens, not iPhone UIs. Hold the analog-tech register or break the aesthetic.

Third tell: clean monoline icons. ZZZ icons are chunky, hand-drawn, marker-on-paper, often with imperfect angles.

Fourth tell: no music context. ZZZ's whole vibe is "what's playing in the cafe" - without typographic music callouts (DJ name, track title, BPM, sticker label) it loses the cultural anchor.

Fifth tell: high-fantasy ornament. Hexagonal frame corners belong to Honkai Star Rail. ZZZ uses spray-paint tags and tape-label rectangles instead.

## Best for

- Music streaming / DJ / indie-label brand pages
- Skate / streetwear / sneaker drop pages
- Indie game studio sites with arcade / brawler / hip-hop sensibility
- Crypto / web3 projects with "street-luxury" positioning (not generic crypto-degen)
- Late-night events, club listings, after-hours brand sites
- Companion apps for ZZZ or ZZZ-adjacent indie titles
- Anime / manga sites with urban-action register
- Hip-hop podcast / interview / archive sites

## Pairs well with

- **Shells:** `shell-mobile-app` (in-game phone-UI variant), `shell-canvas-floating`, `shell-scrapbook-substrate` (mixtape-cover variant), `shell-editorial-broken-grid`, `shell-hero-stack`
- **Styles:** `style-holographic`, `style-pixel-bitmap` (for the CRT moments), `style-terminal-mono`, `style-neubrutalism` (for the spray-paint tag sticker discipline)
