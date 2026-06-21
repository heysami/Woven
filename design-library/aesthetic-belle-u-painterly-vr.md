---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-belle-u-painterly-vr-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-belle-u-painterly-vr-isolated.png
    reason: Signature motif, isolated.
---
# Belle U painterly-metaverse (aesthetic)

**Tag:** `aesthetic-belle-u-painterly-vr`

**Canonical references:**
- **Belle** (Mamoru Hosoda, 2021) - Japanese title: *Ryū to Sobakasu no Hime*
- Director: Mamoru Hosoda; studio: **Studio Chizu**
- Virtual-world architecture: **Eric Wong** (architect commissioned to design U)
- Avatar designer: **Jin Kim** (Disney Renaissance lineage - Frozen, Moana, Over the Moon)
- **U** - the in-film 5-billion-account metaverse, the "linear city that continues to infinity"
- Direct sibling reference: **Summer Wars' OZ** (2009) - same director, opposite emotional register
- Stylistic ancestor: 1991 Disney *Beauty and the Beast* (frame-by-frame homages in U sequences)
- Architectural reference: Eric Wong's hand-drawn imaginary cityscapes

## Cultural identity

Belle's **U** is the 2021 evolution of the Hosoda-metaverse concept - twelve years after Summer Wars' bright-cute OZ, Hosoda revisits the metaverse premise but with a darker, more sublime, more mature emotional register. The cultural reading: this is what Hosoda built when he wanted to reflect *"the way people have weaponized the internet, turning it into a battleground for culture wars, disinformation campaigns, and anonymous attacks"* - colder than OZ, painterly rather than flat, sublime rather than cute.

The defining gesture is the **infinite linear city at evening** - Eric Wong designed U as a city that "continues to infinity, with viewers able to zoom out and get a perfect horizon line where the equator would sit," peering through massive metropolitan visuals that express *"how you can feel very lonely within these massive metropolitan visuals."* The architecture IS the emotional content - the scale of the place dwarfs the avatars.

**Belle vs Summer Wars (OZ):** both are Hosoda metaverses, both designed by the same director, but tonally opposite. OZ is 2009-cute-bright-public-internet; U is 2021-sublime-lonely-weaponized-metaverse. OZ avatars are flat-saturated kawaii mascots on pure white; U avatars are painted Disney-Renaissance characters on volumetric cathedral spaces. Never mix.

The other defining gesture: **frame-by-frame Disney Renaissance homage moments** - the balcony scene, the ball scene, the dragon-collapse scene in U directly quote *Beauty and the Beast* (1991). The mature evolution still loves cinema.

## Palette anchor

- **Twilight indigo** `#1B1F4F` and `#2D2F6C` - primary substrate (the evening tone Hosoda specified)
- **Belle pink** `#FFA9C5` - heroine signature chromatic, used as light/identity color
- **U gold** `#E8C572` - architectural-detail highlight, cathedral chandelier tone
- **Painterly cyan** `#5FBFD9` - distance / atmospheric perspective
- **Dragon midnight** `#0A0E2C` - deep-end, shadow, beast-character base
- **Soft pearl** `#F0E5DC` - text and bright highlight (warm-cast cream, never pure white)
- **Atmospheric blue-grey** `#7A8AAC` - far-distance city haze

Volumetric color depth - atmospheric perspective tints distant elements cooler/cyaner, near elements warmer/pinker. Unlike OZ's flat-saturated palette, U uses gradients and depth tinting throughout.

## Decoration motifs

**Mandatory signatures:**
- **Infinite linear cityscape** as the background - a horizon-line of architecture continuing into distance, painted volumetrically with atmospheric perspective
- **Cathedral-scale architectural framing** - soaring vertical structures, ornate Eric-Wong-style buildings that read as both modern and gothic
- **Disney-Renaissance painted avatars** - characters with painterly volumetric shading, soft rim-light, large expressive eyes (Jin Kim signature)
- **Volumetric god-rays** / atmospheric depth - light shafts through architectural openings, particle dust motes drifting
- **Concentric ring / orb compositional anchors** - circular framings (the U logo, lighting rigs around heroes, audience rings around stages)
- **Painted volumetric fog** at horizons and distant elements (cyan-to-indigo gradient atmospheric tint)
- **Audience-of-millions silhouettes** - when scale is invoked, vast crowds of small floating avatars stretching into distance

**Animation grammar:**
- **Slow camera dolly / orbit** through cathedral spaces (always moving, always sublime)
- **Cross-fade with painterly bloom** during transitions
- **Particles** (dust, fireflies, light shimmer) constantly drifting in the foreground
- **Architectural reveal** - pulling back to show vast scale is a recurring motion

**Forbidden:** flat-shaded saturated avatars (those are OZ), cute kawaii mascot register, dark-grungy cyberpunk neon, pure-white backgrounds, sticker-flat UI chrome. Belle's U has volumetric paint at every layer.

## Voice register

Lyrical, slightly literary, occasionally melancholic. Examples:
- "Welcome to U."
- "5 billion accounts await."
- "The Dragon is in U."
- "Belle's voice echoes through the cathedral."

Sentence case for body, title case for headlines, often paired with poetic Japanese subtitles (Hosoda's films are bilingual by export). Never marketing-corporate, never tech-clinical, never cute-mascot - the tone is *cinematic*, like film opening credits.

## Raster requirement

This aesthetic ABSOLUTELY needs raster - painted volumetric backgrounds, Disney-Renaissance character art, atmospheric perspective cityscapes, god-rays and particles. SVG-only U is just a dark page with painterly gradient - losing the entire architectural-cathedral-cinematic identity. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Failure mode

A dark-mode page with painterly cyan-pink gradient and a vague cathedral SVG = generic fantasy-game-marketing cosplay, not U. The aesthetic's signature is SPECIFIC: Eric Wong infinite-linear-city architecture + Jin Kim painted avatars + volumetric god-rays + atmospheric perspective tinting + concentric ring/orb framing + slow camera-orbit motion. Skip those and it doesn't read as U.

Second tell: flat-saturated mascot avatars. That's OZ (the 2009 sibling). U avatars are PAINTED, volumetric, Disney-Renaissance.

Third tell: pure-white backdrop. OZ is white, U is evening-indigo. Mixing breaks both.

Fourth tell: no architectural-cathedral compositional anchor. U's signature is the SCALE of the architecture dwarfing the avatars - without the architecture, just floating avatars on indigo, it reads as generic dark-fantasy.

Fifth tell: cute / kawaii register. U is mature, sublime, sometimes melancholic - not cute. Save cute for OZ.

Sixth tell: snappy P5-style transitions. U is slow-cinematic-dolly motion. Snap-cuts break the cathedral pacing.

## Best for

- Premium VR / spatial-computing platform branding (Apple Vision Pro tier)
- Music streaming for orchestral / classical / cinematic-score / opera register
- Film / theatre / opera companion sites
- Memorial / cathedral / sacred-architecture digital experiences
- High-end fashion (haute couture) brand pages with romantic-cinematic register
- Companion apps for Belle / Hosoda films / Studio Chizu works
- Concert hall / symphony / live-performance streaming
- Luxury hotel / destination microsites with cinematic-architectural sensibility
- Web3 / NFT projects positioning as "digital cathedral" rather than crypto-degen

## Pairs well with

- **Shells:** `shell-canvas-floating` (the canonical use - avatars in vast painterly space), `shell-hero-stack` (cinematic-poster-style hero), `shell-centered-column` (when the architecture frames a single column of content)
- **Styles:** `style-aurorism`, `style-liquid-glass`, `style-glassmorphism`, `style-cream-humanist` (inverted to dark, for the literary moments)
