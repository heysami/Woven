---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
#
# CRITICAL IMAGE-GEN LOCK: previous image-generation passes regressed this
# entry to its Frutiger Aero parent (waterfalls, blue glass bottles, ferns,
# water droplets). DO NOT regenerate that. The DORFic register is the
# OPPOSITE: stark concrete-white industrial CITY, hi-vis safety orange #FF6600
# as the single chromatic punch, hard-edged flat-shaded low-poly facets,
# cold-cast lighting, NO bubbles, NO dolphins, NO ferns, NO water, NO sky-blue,
# NO glass bottles. Mirror's Edge / SUPERHOT / Ghostrunner reference space -
# NOT Frutiger Aero Wiki summer-living-room reference space.
images:
  - src: aesthetic-frutiger-dorfic-ui.png
    reason: |
      DORFic dashboard UI mockup - stark concrete off-white #F2F3F4 background,
      cool-cast graphite #0E1014 text, ONE safety-orange #FF6600 geometric block
      detonating against the cool-grey field, Eurostile/DIN system labels in
      ALL-CAPS tracked, ALL-CAPS data readouts ("RUNNER 04 / STATUS: ENGAGED"),
      hairline 1px black rules separating modules, low-poly architectural-render
      thumbnail of a hi-vis orange faceted shape against a concrete-grey
      cityscape, hard parallel-line symmetric geometric pattern as a single
      accent band. Mirror's Edge / SUPERHOT industrial-dashboard register.
      ABSOLUTELY NO: bubbles, dolphins, ferns, water, sky, blue glass, leaves,
      Frutiger Aero greenery, soft drop shadows, aurora bokeh, gradient mesh,
      friendly isometric tech illustration. Cool-cast industrial CITY, not warm
      summer livingroom.
  - src: aesthetic-frutiger-dorfic-isolated.png
    reason: |
      Single DORFic signature motif on a stark concrete off-white #F2F3F4
      backdrop - a hard-edged flat-shaded low-poly object (geodesic dome OR
      faceted sphere OR exploded cube OR factory turbine) rendered with hard
      polygon edges and ONE explosive safety-orange #FF6600 highlight facet.
      Cool-cast directional lighting, hard sharp shadow falling onto the
      concrete ground. The object is engineered, not friendly. ABSOLUTELY NO:
      bubbles, blue glass bottle, ferns, water droplets, dolphin, leaf, ocean,
      sky-blue, aurora glow, soft bevel, plastic glossy sheen, Frutiger Aero
      summer-product-still-life. Industrial pole of Frutiger family - NOT the
      Aero parent.
---
# DORFic - clinical industrial CITY (aesthetic)

**Tag:** `aesthetic-frutiger-dorfic`

> **Image-gen discipline:** This aesthetic is the **industrial pole** of the Frutiger family - concrete-white cityscape + safety-orange punch. It is NOT Frutiger Aero (water / bubbles / ferns / blue glass / dolphins / sky). When generating sample imagery, the title's "Frutiger" lineage is for taxonomic record only; the visual content must be Mirror's Edge / SUPERHOT industrial concrete, period.

**Canonical references:**
- Mirror's Edge (2008) - the canonical safety-orange-on-stark-white runner-POV cityscape
- SUPERHOT (2016) - hard-edged red/white/black industrial minimalism, hostile geometry
- Ghostrunner (2020) - cyber-industrial vertical architecture with hi-vis accent
- DORFic Frutiger Aero Wiki spec - the codified "industrial pole" sibling of Frutiger Aero (sibling, NOT same)
- Stark-white industrial-corporate-futurism 2005-2016 (semiconductor / robotics / defence-adjacent brand sites)
- ACRONYM techwear lookbooks, Boston Dynamics product pages, Tesla factory videos - adjacent aesthetics

**Sibling distinction - read before generating:**
- **Frutiger Aero** (parent): warm-consumer optimism - water, bubbles, dolphins, ferns, summer sky, blue glass, aurora, sunlight through leaves. THIS IS NOT WHAT DORFIC IS.
- **DORFic** (this entry): clinical industrial pole - concrete, hi-vis orange, factory floor, calibration complete, hostile geometry. NO water, NO bubbles, NO ferns, NO sky.

## Cultural identity

DORFic is the **industrial, clinical pole** of the Frutiger family - the sibling aesthetic to Frutiger Aero's warm-consumer optimism. Where Aero says *bubbles, dolphins, sky, summer*, DORFic says *concrete, hi-vis, factory floor, calibration complete*. It peaks 2005-2016 in AAA action-game art direction (Mirror's Edge, SUPERHOT), semiconductor and robotics corporate identity, smart-factory dashboards, and architectural-render studios. The mood is **advanced, efficient, cutting-edge, slightly cold** - engineered, not friendly.

The cultural reading: this is what corporate-futurism looked like when the promise was *productivity* rather than *delight*. It inherits Frutiger Aero's humanist body face but swaps the warm-consumer header for a geometric-industrial one - a tonal lock that signals "this is engineered."

## Palette anchor

- **Concrete off-white** `#F2F3F4` with a cool cast (NOT paper-white, NOT sky-blue) - the architectural ground
- **Safety orange** `#FF6600` - the Mirror's Edge / hi-vis / construction-cone canonical accent, used singly and explosively
- **Hot red** `#E63027` - alerts, threats, SUPERHOT register
- **Graphite** `#0E1014` - cool-cast dark, the inverted ground
- **Signal yellow** `#FFB000` - caution states, sparingly

Pick ONE chroma per screen (orange OR red OR yellow). DORFic is a graphic punch, not a rainbow.

## Decoration motifs

**Mandatory** - at least one of:
- A **flat-shaded low-poly 3D object** (geodesic dome, factory turbine, architectural facade, faceted sphere, exploded cube) with hard polygon edges and a single orange highlight facet
- A **stark white architectural photograph or render** with one orange geometric element punched into it
- A **parallel-line symmetric geometric pattern** (Op-Art-adjacent) in hairline black on the off-white ground

**Period-appropriate imagery:** protective-gear silhouettes (jumpsuit, visor reticle, gloves, hard-hat outline), military/factory iconography (vent grilles, hazard chevrons, catalogue stencils), runner-POV verticals, sterile-lab cutaways.

**Forbidden:** bubbles, dolphins, grass blades, aurora bokeh, sky photography (those are Frutiger Aero parent motifs); Memphis squiggles; friendly isometric illustrations of laptops/people/clouds (the 2014-2018 Slack-era marketing-illustration tell); claymorphism; glass blur.

## Voice register

Corporate-technocratic, declarative, mildly clinical. Examples:
- "RUNNER 04 / STATUS: ENGAGED"
- "Sector clear. Proceed to next checkpoint."
- "Output: 2,400 units/hour"
- "Calibration complete."

Sentence case with terminal periods for narrative copy; ALL-CAPS tracked for system labels and chrome. Never warm-marketing ("Unleash your potential"), never gamer-bro ("LOCKED IN"), never lowercase-defiant.

## Raster requirement

Low-poly 3D renders (architectural geometry, Mirror's-Edge-style cityscapes) OR AAA-game screenshots OR industrial-architectural photography are required for the hero composition. Flat SVG triangles with soft shadows read as Frutiger Aero parent or generic isometric tech illustration - not DORFic. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

## Failure mode

**The #1 failure mode (and why this entry's images were previously wrong):** the image generator reads "Frutiger" in the title/tag and regresses to the Frutiger Aero parent - generating waterfalls, blue glass bottles, ferns, water droplets, dolphins, summer sky, aurora bokeh, and friendly green leaves. Every one of those motifs collapses DORFic back into Aero and is **categorically forbidden**. DORFic is the industrial pole - concrete cityscape with safety-orange punch, never the sunlit livingroom.

Other tells of cheap imitation:

- Generic 2010s "tech startup" isometric - friendly purple-teal corporate-Memphis blobs with rounded floating laptops, Inter 14px body, flat `#FF6B00` CTA, smooth Lottie micro-interactions - masquerading as DORFic instead of the period-correct stark off-white cityscape with hard low-poly orange shards.
- Warm autumn orange used like a Frutiger Aero amber accent on a sky-blue page. DORFic orange detonates against grey-white concrete, NEVER against sky-blue.
- Anti-aliased SVG "low-poly" triangles with soft 24px shadows and oklch gradient fills, when real DORFic low-poly is hard-edged flat-shaded facets.
- Humanist Frutiger/Segoe used as the only face (the parent family's voice) instead of swapping the header to a geometric-industrial Eurostile/DIN/Bank Gothic.
- ANY bubble, dolphin, grass blade, fern leaf, sky-blue background, glass-bottle still-life, water droplet, summer-meadow vignette, aurora gradient, sunlit-livingroom photography - these collapse DORFic back into its Frutiger Aero parent and break the industrial pole.
- Warm-cast lighting. DORFic is cool-cast (overcast cement-light, sodium-arc-warning glare, hospital fluorescents). Warm lighting belongs to Aero, never DORFic.
- Green vegetation of any kind. DORFic has NO plants. The environment is poured concrete, anodised aluminum, hi-vis stencil, raw cinder block, exposed structural steel.

## Best for

- Industrial-corporate brand sites (logistics, semiconductors, robotics, defence-adjacent)
- AAA action-game landing pages and HUD prototypes
- Smart-factory and Industry-4.0 dashboards
- Architectural-render studios
- Athletic-performance and quantified-self products with a clinical register
- Mid-2000s product-anniversary microsites for tech hardware
- Sterile-laboratory and biotech brands wanting futurist gravity without warm-consumer softness

## Pairs well with

- **Shells:** `shell-top-bar-canvas`, `shell-canvas-floating`, `shell-three-column-app`, `shell-hero-stack`, `shell-bento-grid`, `shell-terminal-frame`
- **Styles:** `style-oversized-neo-grotesque`, `style-dense-mono-dark`, `style-restrained-hairline`, `style-flat-design`
