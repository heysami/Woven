---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-punk-fanzine-fluoro-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-punk-fanzine-fluoro-isolated.png
    reason: Signature motif, isolated.
---
# Punk fanzine fluoro (aesthetic)

**Tag:** Scene-magazine paste-up - dry-brush masthead, fluoro tape-labels over halftone b/w portraits on newsprint

**Canonical references:**
- La Movida Madrilena scene magazines (Madrid, early 1980s) - post-dictatorship cultural explosion in cheap ink
- UK punk fanzines (Sniffin' Glue lineage) - photocopied urgency, hand-slapped labels
- Two-color risograph / offset zine printing - fluorescent pink and acid green as the only spot inks a zine could afford
- Paste-up production: waxed galleys, tape, misregistered plates, crop marks left visible

## Cultural identity

A scene magazine assembled the night before the printer deadline: a dry-brush splatter masthead painted in one take, black-and-white halftone portraits of whoever showed up, and fluorescent pink / acid green blocks slapped over everything like tape labels - each carrying a shouted phrase in rough caps. The substrate is warm newsprint with visible grain and tear; inks misregister so pink peeks out from behind green; crop marks and registration crosses survive to the final page.

The defining gesture is **the slapped label**: torn-edged fluoro rectangles thrown across a monochrome photo at casual angles, text punched through in black - the layout energy of someone labeling the revolution with a tape gun.

Where `aesthetic-zine-type-wall` gets its density from TYPE alone (colliding type blocks as the entire surface, rigorously art-directed underneath), fanzine fluoro is photo-anchored: the b/w halftone portrait is the star and the fluoro labels orbit it. And unlike `style-ransom-glyph-mix` (letterforms cut from different sources within one word), the lettering here is unified dry-brush and stencil - the collage happens at the block level, not inside words.

## Palette anchor

Two spot inks, one black, one paper - the print budget is the palette:
- Fluo pink `oklch(66% 0.27 358)`
- Acid green `oklch(88% 0.25 125)`
- Ink black `oklch(12% 0 0)`
- Newsprint white `oklch(96% 0.01 95)`
- Misregister moment: pink and green overlapping to a dirty `oklch(70% 0.15 60)`

Photography is ALWAYS black-only halftone - the spot inks never tint a photo, they sit on top of it.

## Decoration motifs

- Dry-brush splatter masthead - one word, painted fast, flicked ink around it
- Torn-edge fluoro blocks as labels/buttons at 1-3 degree angles, black text knocked rough
- B/w halftone portraits with coarse newspaper dot; hard crops, faces at page edge
- Typewriter mono body text; hand-drawn X marks, stars, and lightning glyphs as icons
- Misregistration fringes (pink ghost behind green), crop marks, registration crosses left visible
- Dry-ink streaks and skips on any large black area

**Raster required:** the halftone b/w portraits (raster-photo, coarse newsprint screen) and the dry-brush masthead + splatter strokes (raster-foreground on transparent). Newsprint grain and torn edges ride as overlay textures; the fluoro blocks themselves are CSS.

## Voice register

Manifesto shorthand, bilingual-friendly, all caps on labels: "NO FUTURE PERO YA", "NEW NOISE", "ZINES TO THE PEOPLE". Body copy runs lowercase typewriter, run-on and breathless. Never polite marketing, never hashtags, never emoji.

## Failure mode

Clean vector "grunge" brushes from a free pack + a pink drop shadow = mall-punk template. If the photo is full-color, the print economics collapse - it must be black halftone. Perfectly aligned labels with square corners read as a modern card grid; they must sit at slight angles with torn edges. Fluoro used as page background instead of slapped blocks turns it into a neon poster and loses the paste-up grammar.

## Best for

- Music scenes, venues, radio shows, festival editorial
- Counterculture magazines, interview features, photo essays
- Campaign and protest microsites that want urgency with craft
- Fashion and streetwear drops trading on zine authenticity

## Pairs well with

- Shells: `shell-editorial-broken-grid`, `shell-scrapbook-substrate`, `shell-masonry`
- Styles: `style-brutalist-raw`, `style-raster-cutout`, `style-bold-display`
