---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-vector-vector-musica-ui.png
    reason: Generated UI mockup committing this aesthetic's vocabulary at a usable density — palette, type tone, decoration motifs in context.
  - src: aesthetic-vector-vector-musica-isolated.png
    reason: Isolated subject sample — the aesthetic's signature motif / texture / illustration treatment on a neutral background.
---
# Vector Música (aesthetic)

**Tag:** Suite PreCure♪ 2011, Winx Club / Musa Harmonix key art, Bratz: Forever Diamondz CD sleeve, Vectordelia parent style, Frutiger Metro archive

**Canonical references:**
- Suite PreCure♪ 2011 — staff-line title card, scattered notes, magical-girl earnestness
- Winx Club / Musa Harmonix key art — pastel bokeh + ribbon banners + idol pose
- Bratz: Forever Diamondz CD sleeve — script wordmark over pearl gradient with gold-foil glyphs
- Vectordelia (parent style) — the vector-illustration lineage this branches from
- Frutiger Metro archive — the 2005–2011 pastel-pearl key-art moment

## Cultural identity

Vector Música is the *música* branch of the late-2000s/early-2010s vector-illustration moment — specifically the magical-girl, idol-show, and tween-pop key-art lineage where the subject is literally **singing**. It descends from Vectordelia but commits hard to femme-coded, sincere, melodic register: PreCure title cards, Winx Harmonix transformations, Bratz Rock Angelz / Forever Diamondz CD packaging. Era window roughly 2005–2012, with a current revival tied to PreCure 20th-anniversary nostalgia and Sanrio-merch culture. Audience is 8–16 or nostalgic-for-being-8–16. Sincere, not ironic. Earnest, not edgy.

## Palette anchor

Pearl-cream base with magical-girl jewel accents — never neutral grey, never black, never neon:
- Magenta primary `#E94B9B`
- Lavender `#B79CED`
- Mint `#9FE3D0`
- Peach `#FFD3B5`
- Gold-foil accent `#F6C453` reserved for hearts, stars, and the wordmark only

Body text is desaturated lilac, headings are deep plum — black is banned.

## Decoration motifs

Mandatory visual vocabulary:
- One curved 5-line musical staff sweeping diagonally across the layout as the compositional spine
- Scattered 8th/16th notes with beams, drawn as vector shapes (never Unicode `♪`)
- At least one ornamental treble clef as decorative anchor
- Layered bokeh discs (12+, varied sizes, screen blend) behind everything
- Floral filigree in corners (inherited from Vectorbloom sibling)
- Hearts, 5-point stars, sparkle bursts
- Ribbon banners for titles and at least one CTA
- Scalloped or wave dividers between sections — never straight rules

Forbidden: black DJ/turntable silhouettes (that's Vectorfunk), halftone CMYK splats (parent Vectordelia urban branch), neon cyan-on-magenta contrast, photographic textures, brushed metal, dark mode.

## Voice register

Sincere, melodic, feminine-coded but earnest not ironic. "Let your heart sing" — not "vibes only." Spanish or Japanese accents are welcome (the *música* is literal). Exclamation marks and `♪` half-note glyphs as titlecard punctuation (e.g. `Suite Pretty Cure♪`). Microcopy reads like a magical-girl transformation line, not a SaaS landing page.

Typographic mood: a formal English script (Bickham Script Pro, Lavanderia, Allura, Pinyon Script) for the wordmark and one hero phrase; Trajan small-caps or Optima for eyebrows; humanist sans (Myriad, Frutiger, Avenir Next) for body. Never Inter, never Poppins.

## Failure mode

- Flat `#FFC0CB` pink rectangle with Inter 14px and a Unicode `♪` emoji — AI cosplay
- Reggaetón-Vectorfunk silhouette + spraypaint splatter mis-labeled "Vector Música" — wrong sibling of the Vectordelia family
- Unicode music notes instead of drawn vector clefs and beamed notes
- Missing the curved 5-line staff sweep that should anchor the composition
- One CSS radial-gradient called "bokeh" instead of 12+ layered semi-transparent discs at varied sizes
- Sans-serif wordmark where Bickham / Lavanderia script is mandatory
- Black body text where it must be plum
- Dark mode of any kind

## Best for

- Kids' and tween music properties
- Magical-girl and idol-show fan sites
- Music-school, choir, and youth-orchestra brands
- Lullaby and sleep apps for children
- Romantic-pop playlist covers and album microsites
- Sanrio-adjacent merch and fandom pages
- Anything where the subject is *singing* and the audience is 8–16 or nostalgic for being 8–16

Wrong for: adult reggaetón, club/DJ apps, urban music (use Vectorfunk); psychedelic florals without a music subject (use Vectorbloom); anything ironic.

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`, `shell-scrapbook-substrate`, `shell-editorial-broken-grid`, `shell-masonry`, `shell-mobile-app`
- Styles: `style-aurorism`, `style-holographic`, `style-glassmorphism` (gloss only, not frosted), `style-cream-humanist`, `style-raster-cutout`
