---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-corporate-memphis-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-corporate-memphis-isolated.png
    reason: Signature motif, isolated.
---
# Corporate Memphis (noodle people) (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Facebook Alegria 2017 - the originator; bendy-limb figures across product
- Slack 2017 Pentagram rebrand - saturated anchor color + faceless figures
- Lyft Buck illustration system - codified rules for active poses
- Headspace - wellness-meets-noodle-limb
- Spotify Wrapped 2017-19 - annual peak of the style in mass marketing

## Cultural identity

The defining illustration language of platform-era SaaS (2017-2022). Born from Facebook's Alegria system and spread by Pentagram, Buck, and in-house teams at every Series B startup with a marketing budget. It exists to make scale feel friendly: faceless figures stand in for "any user," impossible-bendy limbs signal "playful and human," and one saturated anchor color carries the whole brand. The aesthetic peaked around the Spotify Wrapped era and has since become shorthand for "tech company that wants to seem approachable" - both its strength (instantly legible) and its curse (instantly dated).

## Palette anchor

Pick **one saturated anchor** and let it carry the brand:
- Alegria coral `#FF6B6B`
- Slack aubergine `#4A154B`
- Lyft magenta `#FF00BF`
- Headspace marigold `#FFAA13`

Support with 2-3 muted seconds from `#FFD166` mustard, `#06D6A0` mint, `#118AB2` teal, `#EF476F` coral, `#073B4C` navy. Ground on off-white `#FAFAF7` or warm cream `#FBF6EE` - never washed lavender gradient. Skin tones are non-representational on purpose (lavender, mint, peach) - that's the whole point of "faceless universal."

## Decoration motifs

- **Bendy-limb figures**: small heads on long torsos, oversized hands and feet, limbs that bend at impossible angles, ACTIVE not standing - cartwheeling, reaching, leaning out of frame, hand-holding the headline
- **Facelessness**: no features, or dot-eyes-only with no mouth
- **Flat tonal offset shadow**: a darker-shade shape offset 4-8px behind the figure - NOT a CSS box-shadow blur. This is the single biggest tell of canonical vs cheap execution.
- **Supporting marks**: one squiggle, dot-grid, or starburst echoing the figure's color
- **Color blocks**: saturated anchor butted hard against cream, no gradient transition
- **Illustration over type**: composition is illustration-LED, with headline tucked beside the figure (not above it)

## Voice register

Warm-encouraging, second person, short sentences. One mild exclamation is OK ("Let's get started", "Nice work!"). Never wry, never corporate-formal, never edgy. The figures are doing the emotional work - the copy just confirms the vibe.

## Failure mode

The humaaans.com / unDraw / Storyset stock-pack hero: washed lavender-gradient background, Inter 16 body, "Trusted by 1000+ teams" subhead, rounded-12 button, and one generic noodle figure slotted in as an afterthought. Tells: text-led page with illustration as decoration (it should be illustration-LED), inconsistent line weights across figures, CSS blur drop-shadows instead of flat offset shapes, washed-pastel anchor instead of one saturated anchor + muted seconds, figures standing still instead of cartwheeling, realistic skin tones, mouths with teeth.

## Best for

SaaS marketing pages, fintech onboarding, wellness/health apps, edtech, HR-tech, friendly-bureaucracy (government services), end-of-year recap/data-viz. Subjects where "approachable, optimistic, faceless-universal" is the brief. Avoid for: luxury, B2B enterprise (now reads dated), news/editorial, anything claiming craft seriousness.

> **Raster required:** the noodle-people illustrations ARE the brand. Before drawing, follow the [**Raster requirements**](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree: check image-gen MCPs, fetch public-domain archives, check project assets, ask the user. If all fail, switch to a non-raster aesthetic rather than fake noodle figures in SVG.

## Pairs well with

- **Shells**: `shell-hero-stack` (canonical marketing), `shell-bento-grid` (feature pages), `shell-centered-column` (onboarding flows), `shell-mobile-app` (in-product empty states), `shell-two-column-app`, `shell-three-column-app`
- **Styles**: `style-flat-design`, `style-bold-display`, `style-claymorphism` (for 2022-era softer variant), `style-sf-pro-ios` (in-product), `style-material-m3` (Android product surfaces)
