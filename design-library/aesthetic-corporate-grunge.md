---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-corporate-grunge-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-corporate-grunge-isolated.png
    reason: Signature motif, isolated.
---
# Corporate Grunge (1990s) (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- OK Soda 1994 - sardonic anti-marketing manifesto cans, the platonic ideal.
- Ray Gun magazine (David Carson, 1992-1998) - illegible-as-design, deconstructed typography.
- Nike 'I Am Not a Role Model' 1993 (Charles Barkley) - confrontational ad copy on photocopy substrate.
- Apple 'Think Different' 1997 - monochrome portraiture, sparse manifesto voice.
- Mountain Dew 'Do the Dew' 1993 - extreme-sport collage with one muted electric accent.

## Cultural identity

The aesthetic of late-Cold-War corporations pretending to be the disaffected teenager dunking on them. Peaked 1993-1998, when MTV-era brand managers learned that Gen X read irony as authenticity, and that a photocopied zine could sell more soda than a glossy billboard. Visually it descends from real punk/hardcore zine culture (Maximumrocknroll, Sniffin' Glue) but laundered through ad agencies - Wieden+Kennedy, CAA, the OK Soda team at Coca-Cola. The point is anti-slickness as a product attribute: the surface signals "we are not lying to you" by performing exhaustion with its own medium.

Emotionally it sits between sardonic-deadpan and confessional-manifesto. It refuses the centered hero, the smiling stock model, the round corner. It is the visual register of someone who has read too much Adbusters and still has to ship a campaign on Monday.

## Palette anchor

Muted bleach / rust / asphalt. Never pure black on pure white - the substrate is always warm-grey newsprint or carbon page, as if printed on a Xerox running low on toner.

- Ink `#1a1a1a` - not true black.
- Paper `#cdbcb1` - dirty warm-grey newsprint.
- Ash `#3b3c36` and asphalt `#252525` - dark fields.
- Oxide rust `#8a3b2b` and mustard `#b49a3a` - earth accents.
- ONE saturated accent only - OK Soda red `#7f2f2b` OR Mountain Dew muted electric green `#a6c83a`, applied via `mix-blend-mode: multiply` so it reads as ink on paper, not pixel on screen.

## Decoration vocabulary

Mandatory: photocopy grain plus halftone dots; at least one piece of masking tape; at least one staple; at least one handwritten margin annotation in red ballpoint; at least one barcode or registration-mark glyph; asymmetric column layout; intentionally crooked image crops (-4deg to +3deg rotations); torn edges via SVG `clip-path`, never rounded corners.

Forbidden: emoji, smooth Material drop shadows, lens flare, centered hero blocks, gradient backgrounds (except multi-stop sepia photocopy degradation), any saturated color outside the single accent, stock "grunge brush" Photoshop stamps.

Typography leans on FF Trixie / Trixie Pro, Courier Prime, American Typewriter for body and pullquote; heavy condensed sans (Knockout, Compacta, Impact) at jagged baselines for headlines, with per-glyph translate/rotate jitter on `<span>` wraps.

## Voice register

Sardonic-deadpan manifesto. Lowercase confessional OR ALL-CAPS proclamation, never sentence case. Microcopy direction: "don't be fooled into thinking there has to be a reason for everything" (OK Soda) over "discover amazing experiences." Treat the user as a co-conspirator who already gets the joke.

## Failure mode

The torn-PNG-on-Squarespace tell: a clean 12-col grid, Inter body, one sepia gradient overlay, a Permanent Marker headline, and a centered hero block. That is AI cosplay, not corporate grunge. The real thing is asymmetric photocopy collage on a carbon-warm-grey substrate (not pure black or pure white), typewriter or distressed-display body type, and texture BAKED IN through multiply-blend halftone and displacement-mapped letterforms - not stamped on top as a single overlay PNG.

## Best for

Gen-X/millennial nostalgia plays. Alt-music, skate, streetwear, harm-reduction and recovery copy that needs to feel un-slick. Zine-style editorial. Anti-corporate brand voice for actual corporations. Manifesto landing pages, ironic SaaS rebrands, indie game splash pages. Anything where slickness would read as a lie.

Raster required: photocopy textures, distressed Xerox grain, and 1990s magazine collage scrap photography are the genre. Follow the main playbook's raster requirements decision tree before drawing - if no image source is available, switch genre rather than fake it in SVG.

## Pairs well with

- Shells: shell-editorial-broken-grid, shell-scrapbook-substrate, shell-masonry, shell-hero-stack, shell-centered-column
- Styles: style-raster-cutout, style-serif-warm-paper, style-brutalist-raw, style-terminal-mono
