---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-wacky-pomo-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-wacky-pomo-isolated.png
    reason: Signature motif, isolated.
---
# Wacky Pomo (Nickelodeon 90s) (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Nickelodeon Studios 1992-98 - the orange splat logo, slime, off-axis bumpers
- Saved by the Bell 1989 title card - each word its own typeface and shadow hue
- Toon Disney 1998 intros - tilted cards, hard drop shadows, no neutrals
- Memphis Milano 1981-88 - the design-school source of squiggles, checkerboards, clashing flats
- Ren & Stimpy bumpers - gross-out adjectives, hand-wobble outlines, splat stamps

## Cultural identity

A kids-TV / post-Memphis collision that peaked roughly 1989-1998 on Saturday-morning American cable. It rejects the corporate symmetry of 80s broadcast graphics and the muted good-taste of mid-century modernism in favour of loud, off-axis, gross-out, second-person energy aimed at 8-13-year-olds. The visual grammar comes from Memphis Milano (checkerboards, zigzags, squiggles, flat clashing colour) refracted through the splat-stamp + slime + chubby-cartoon-lettering lens of Nickelodeon's on-air brand. Adjacent to but NOT the same as Y2K Futurism (which is chrome and blobs), Curly Girly (which is glitter and Lisa Frank), or Wacky 90s Memphis (which is the adult-design version). This is specifically the *kids' TV* dialect - louder, sloppier, more orange, more proudly un-corporate.

## Palette anchor

Acid flats slammed adjacent with no neutral buffer:
- Nick Orange `#F57C13` - mandatory primary, the splat-stamp colour
- Slime Green `#A8D026`
- Hot Magenta `#E5267F`
- Electric Teal `#00C2C7`
- Hazard Yellow `#F2E930`
- Outline / body `#1A1A1A` - hand-wobble black, the only allowed "neutral"

Greys are forbidden as surfaces. Gradients, pastels, mauve/sage/dusty-rose are forbidden categorically.

## Decoration motifs

The visual vocabulary that signals the era:
- Splat / paint-stamp shapes (raster PNG, not CSS border-radius blobs)
- Checkerboard dado strips running across a viewport
- Zigzag and squiggle lines
- Polka-dot fields
- Hand-drawn outline arrows
- Tilted off-axis cards at 4-12deg rotations
- Hard-offset two-stop drop shadows in clashing hues (no blur, no alpha)
- Tab-tongues / dog-eared corners poking off panel edges
- Confetti-sprinkle background patterns

Lettering must include at least one tilted middle word in a different typeface and at least one drop-shadow in a clashing hue (Saved-by-the-Bell rule).

## Voice register

Shout-caps. Exclamation-heavy. Second person. Gross-out adjective adjacent. "SLIME TIME", "TOTALLY", "GUNK", "GROSS OUT", "WAY COOL". Never corporate, never mindful, never "discover" / "introducing" / "curated". Microcopy should sound like a kid yelling at a TV, not a brand voice doc.

## Failure mode

Comic Sans body + centered symmetric card + pastel mauve/sage palette + Inter heading + generic vector-perfect star/swirl clipart + soft blurred drop-shadow + 12px rounded radii = "AI Wacky Pomo cosplay" - looks like a 2024 Canva birthday template, not 1994 Nick. The dead giveaways: Comic Sans (wrong era, used by no actual Nick designer), centered symmetric layout, any pastel, any blur on a shadow, any uniform radius. Also fatal: CSS-only splat blobs that read as Memphis pure - the splat MUST be a raster paint-stamp with irregular edges.

## Raster requirement

This aesthetic does not render in pure SVG/CSS. It needs period raster: splat textures, slime drips, candy/VHS overlays, period 90s kids-TV screen captures. Before drawing, follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree.

## Best for

- Kids' content for 8-13 year olds
- Nostalgia-marketing aimed at millennials
- Snack / candy / cereal landing pages
- Summer camp, arcade, mini-golf, water-park brands
- Gaming Twitch overlays and indie animation studio portfolios
- Anything that wants to feel loud, gross, off-axis, and decidedly un-corporate

Bad fit for: finance, healthcare, B2B SaaS, anything requiring trust or calm.

## Pairs well with

- **Shells:** `shell-editorial-broken-grid` (the off-axis tilted-card stage), `shell-scrapbook-substrate` (splat-stamp collage), `shell-hero-stack` (giant Nick-splat hero), `shell-bento-grid` if every cell is rotated and outlined
- **Styles:** `style-neubrutalism` (closest off-the-shelf - solid borders, hard offset shadows, flat saturated colour), `style-raster-cutout` (for the paint-stamp splat treatment), `style-doodle` (for the hand-wobble outlines)
