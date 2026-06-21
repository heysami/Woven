---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-solarpunk-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-solarpunk-isolated.png
    reason: Signature motif, isolated.
---
# Solarpunk (aesthetic)

**Tag:** Solarpunk Magazine, Properly Studio ETHWarsaw, Velvetyne Brassia/Hypha/Plantasia, Solarpunk Studio, William Morris Kelmscott revival

**Canonical references:**
- **Solarpunk Magazine** - the journal-as-library voice; essayistic, not promotional.
- **Properly Studio ETHWarsaw** - proof solarpunk can hold a tech subject without going SaaS-green.
- **Velvetyne Brassia / Hypha / Plantasia (Bioma)** - the botanical-display faces that define the masthead register.
- **Solarpunk Studio** - contemporary editorial tone, hand-illustrated ornaments over photography.
- **William Morris / Kelmscott Press revival** - the historical taproot: craft, ornament, the printed book as garden.

## Cultural identity

Solarpunk is a near-future utopian movement that emerged in the early 2010s as a deliberate counter to cyberpunk's dystopian default. It imagines climate-adapted, community-scaled, post-scarcity futures - bicycles and bioregions, not jetpacks and corporate towers. Visually it borrows from Arts & Crafts (Morris, Kelmscott), Art Nouveau botanical line, and small-press independent magazines, then runs them through a contemporary editorial sensibility.

The register is the *library*, not the *pitch deck*. Tone is measured, plainspoken-utopian, often essayistic. The aesthetic is hostile to eco-cheer, greenwashed SaaS, and AI-rendered "lush future city" imagery - those are the lazy stand-in. Solarpunk done right reads more like *Aesop's journal nudged one chroma step toward green* than a Webflow template skinned with a Midjourney prompt.

## Palette anchor

Warm, sage-tinted, low-chroma. No primary yellow. No Material green.

- Background cream `#F4ECD8` (warm, faintly green - never pure white, never Solarized `#fdf6e3` flat)
- Ink warm dark green-black `#1F2A22` (never pure black, never blue-black)
- Deep forest `#2E5339` ("Mythical Forest")
- Mustard amber `#C99A3B` ("Golden Opportunity" - not primary yellow)
- Optional: clay terracotta `#B8643D`, muted sage `#A5B49A`

Pair forest + amber **or** clay + sage. Never all four. Chroma cap stays low - this is a botanical garden in October, not Material in spring.

## Decoration motifs

- One hand-drawn botanical ornament per page, max - a vine sprig, a seed, a leaf rule - inline SVG, 1px stroke, sage or forest.
- A drop cap on the lede paragraph (serif, forest, ~4em, floated) is the second permitted decorative move.
- A masthead dingbat or a section divider with a single botanical glyph - chosen, not tiled.
- Hairline rules above and below the masthead, in forest.

**Forbidden**: Midjourney "solarpunk cityscape" hero renders, vine-curtain dividers, isometric solar-panel skyscrapers, sunflower icons, tiled William-Morris pattern wallpapers (they belong in 1895 - one ornament, not a field), Lucide leaf icons, hop-vine borders around everything.

## Voice register

Measured-imperative, present-tense, plainspoken-utopian. The voice of a curator or a librarian, not a marketer.

- Yes: "Tend the commons." / "A library of solar futures." / "Issue 12 - colorful roots."
- No: "Join the revolution!" / "Sustainable. Smart. Sunny." / "Build a better tomorrow ✨" / emoji of any kind / second-person sales copy.

Headlines lean essayistic. Microcopy is patient. Numbers and dates appear in small uppercase sans kickers ("A JOURNAL OF FUTURES - ISSUE TWELVE").

## Failure mode

Cream background + Inter + Material `#4CAF50` button + sunflower emoji + AI-rendered vine-covered-skyscraper hero = **SaaS-pretending-to-be-eco**. The cheap version always reaches for the literal: leaves on every icon, photographs of solar panels, "100% sustainable" badges. The tasteful version reads as a journal you'd find in a small press bookshop - Morris's politics, not Morris's wallpaper.

Other tells of the cheap version: spring-bouncy hover micro-interactions, scroll-parallax pollen particles, two display faces fighting, full pill buttons, 12px+ rounded cards.

## Best for

- Ecological journals and small-press climate publications
- Climate-tech / clean-energy startups that want to read like a library, not a pitch deck
- Regenerative agriculture, community-land trusts, seed libraries
- Public-interest tech and civic infrastructure
- Biophilic-architecture portfolios
- Botanical apothecary and sustainable beauty brands that want more politics than Aesop
- Near-future speculative fiction publishers and essayistic newsletters

## Pairs well with

- Shells: `shell-centered-column` (essay / journal pages - the primary fit), `shell-editorial-broken-grid` (issue covers, longform features), `shell-masonry` (issue archive / project index), `shell-hero-stack` (publication landing - if the hero is a masthead, not a render)
- Styles: `style-serif-warm-paper` (the default pairing - humanist serif on cream), `style-cream-humanist`, `style-restrained-hairline` (for the metadata strata and price lists), `style-doodle` (only for the single ornament, used sparingly)
