---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-bright-tertiaries-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-frutiger-bright-tertiaries-isolated.png
    reason: Signature motif, isolated.
---
# Frutiger Bright Tertiaries (aesthetic)

**Tag:** `aesthetic`, `frutiger`

**Canonical references:**
- OXO Good Grips mid-2000s packaging — soft black handles + saturated tertiary lockups on warm white
- Skype 2005 logo — lockup of cloud-blob behind rounded VAG Rounded type
- Target in-store 2007 — color-blocked aisles in lime/orange/fuchsia against bright white
- Mid-2000s school/college brochure interiors — confident block panels with one oversized hero color
- Web 2.0 startup brand sheets c.2005–2009 — rounded sans, asymmetric color blocks, friendly voice

## Cultural identity

The post-skeuomorph, pre-flat moment of Web 2.0 optimism: roughly 2005–2010, after the bursting bubble had been forgotten and before iOS 7 made everything thin and grey. This is the look of consumer-product confidence in a near-recession era — the design dialect of a startup that wants to feel earnest and physical without slipping into kitsch. It is graphic-design-heavy, not photographic; it descends from poster work and packaging more than from screens. Where Frutiger Aero said "the future is glass and water and dolphins," Bright Tertiaries said "the present is color-blocked, friendly, and made of real things you can hold." It is unmistakably mid-2000s and unmistakably American mass-market.

## Palette anchor

Three full-saturation tertiaries on warm-or-cool white, never grey, never pure `#fff`. Pick exactly three of the five per surface — one dominant, two accents.

- Lime `#b8e346` — the OXO/Skype signature
- Orange `#ff8a2a` — the Target/Nickelodeon-adjacent warm anchor
- Purple `#7d3cad` — the deep accent that gives the palette an adult register
- Teal `#3eb8b3` — the cool counter-balance, often used for hardware/electronics
- Fuchsia `#e23a8a` — the Lisa-Frank-adjacent warm pop, used sparingly

Body text is warm low-chroma near-black; backgrounds are warm white or cool white. Greys are warm and chroma-tinted (0.005–0.012), never neutral.

## Decoration motifs

- Flat circular dots (5–12px) scattered as accent confetti
- One oversized rounded blob or rounded-rectangle as background shape behind hero copy
- Color-block lockup behind a logo
- Asymmetric panel arrangements with one oversized hero block and smaller satellites
- Optional thick horizontal color band across header
- Single flat offset "poster registration" shadow `2px 2px 0` in matching darker tertiary — never blurred

**Forbidden:** gradients, glass/glossy/aqua, blurred drop shadows, bokeh, nature photography, dolphins, clouds, Memphis squiggles/zigzags/grid-paper (that is 1985, this is 2007), beveled buttons, skeuomorphism, isometric illustration, Corporate Memphis blob people.

## Voice register

Friendly-confident-declarative. Short sentences. Contraction-friendly. Mid-2000s Web 2.0 startup register — "Type smarter.", "All your stuff. One place.", "Made for the way you actually work." The occasional exclamation mark is earned, not sprinkled. No corporate hedging, no whimsical anthropomorphism, no quirky-friend voice.

Typography is rounded sans: VAG Rounded primary, with Frutiger / Myriad / FF DIN Round / Helvetica Rounded as fallbacks. **Never Inter, never Geist, never Söhne** — those mark the work as 2022, not 2007.

## Failure mode

Muted "tasteful" pastels + Inter + 24px pillowy radius + soft drop shadows = Corporate Memphis 2022, not Bright Tertiaries. Gradients or any glass = drifted forward into Frutiger Aero. Squiggles, zigzags, scribbled outlines = drifted backward into genuine 1985 Memphis. Pure `#fff` background or neutral grey body text = the rounded-corner saturation reads as flat-design 2014. The tell is always desaturation, neutralization, or softening — this aesthetic dies the moment any of its three signatures (warm-tinted white, full-saturation tertiary, rounded-not-pillowy radius) gets compromised.

## Best for

- Consumer-product marketing pages (housewares, hardware, simple consumer software)
- EdTech and education products targeting families
- Kid-and-family apps that need to feel optimistic without being childish
- Mid-market SaaS that wants physical, earnest, anti-corporate energy
- Anything intentionally invoking 2005–2010 Web 2.0 nostalgia
- Brand work for products that sit on a shelf in a Target

## Pairs well with

- **Shells:** `shell-bento-grid` (asymmetric variant, one oversized hero block), `shell-hero-stack`, `shell-two-column-app`, `shell-mobile-app`, `shell-centered-column`
- **Styles:** `style-flat-design` (closest match — flat fills, no shadows, no gradients), `style-bold-display` (for the confident display type), `style-neubrutalism` (if leaning into the offset poster shadow — but watch the radius; pillowy = wrong era)
