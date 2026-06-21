---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-tranquil-serenity-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-frutiger-tranquil-serenity-isolated.png
    reason: Signature motif, isolated.
---
# Frutiger Tranquil Serenity (aesthetic)

**Tag:** `aesthetic-frutiger-tranquil-serenity`

**Canonical references:**
- Bath & Body Works Aromatherapy 2010 - sage/eucalyptus/lavender SKU system; the canonical drug-store-spa wash
- Aveda Botanical Kinetics 2008-2012 - all-lowercase humanist sans, amber-glass product, plant-derived voice
- Method body care (Karim Rashid era) - soft-curved bottles, candy-warm pastels with botanical restraint
- Origins Spa Living - earth-tone packaging, warm oat + sage as house palette
- Spafinder print 2010 - full-bleed dewy nature photography with floating lowercase type

## Cultural identity

A late-2000s / early-2010s sub-strain of Frutiger Aero that traded the sky-and-bubbles of consumer tech for the warm, plant-derived calm of the spa aisle and the boutique wellness brand. Where parent Frutiger Aero was optimistic about the future (Vista, Wii, water droplets on glass), Tranquil Serenity is optimistic about the present moment - drug-store aromatherapy, hotel-spa retreats, the candle as a household object, the bath as a ritual.

Its native habitat is print catalogues, in-store signage, candle labels, and the websites of brands that smelled like eucalyptus. It peaked around 2008-2012 alongside the boom in "wellness as lifestyle category" and faded as the wellness industry pivoted to clinical minimalism (Goop white, The Ordinary lab type) and millennial pink.

The mood is dusty, warm, and humid - never cool or clinical. It is restoration, not productivity.

## Palette anchor

- Sage primary `#A8C3A0` - the through-line color
- Water-blue secondary `#B3CEE5` - soft, dusty, never cyan
- Deep teal accent `#2F7F7A` - for type and rare emphasis
- Warm oat neutral `#EADFD3` - paper and surface
- Candle-amber `#D9A86C` - one warm flame per screen, used sparingly

Greys are warm stone, never cool slate. The whole palette is desaturated by ~15% versus parent Frutiger Aero.

## Decoration motifs

- Dewy macro botanical photography (single leaf, water bead, eucalyptus sprig)
- Stacked river stones in silhouette
- Single bamboo stalk
- Soft candle glow rendered as additive radial gradient
- Water-ripple SVG at very low opacity
- Warm bokeh particle field (never sharp specular highlights)
- Amber glass bottles, ceramic vessels, linen textures in product photography

**Forbidden decoration:** lotus emoji, cartoon dolphins (that's Frutiger Aqua), Apple Aqua dock pastiche, neon teal, purple/lavender accents, sepia/brown wood-grain (that's Cottagecore Wellness, different family).

## Voice register

Gentle lowercase imperative: "breathe.", "begin your ritual", "soften the day", "settle in."

Never exclamation. Never tech jargon. Never wellness-influencer caps or em-dashed manifesto. Sentences end in periods, often single-clause. Microcopy reads like the side of a candle, not the side of a productivity app.

## Raster requirement

This aesthetic is photography-led. Spa product photography (amber glass, ceramic, water surfaces, candles, botanical macro) carries the brand identity - the photographs are the brand. Before drawing, follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree. SVG botanicals are an acceptable fallback only at very low opacity as ambient texture.

## Failure mode

Cyan-teal `#00C9B7` gradient + Inter 14 + AI-stock lotus on white + emoji garnish + 12px radius card = generic AI "zen app" cosplay. The tell is a cool, over-saturated palette where it should be warm and dusty, plus hard UI chrome where there should be dissolving mist. The second tell is exclamation points and "Let's do this!" energy - Tranquil Serenity never raises its voice.

## Best for

Spa booking, meditation and breathwork, body-care e-commerce, sleep and ritual apps, premium wellness retreats, candle and aromatherapy commerce, gentle habit trackers, hotel-spa concierge. Audiences seeking restoration, not productivity. Subjects where the user arrives tired and should leave softer.

Bad fit for: dashboards, fintech, anything requiring data density, anything aimed at urgency or hustle.

## Pairs well with

- **Shells:** shell-centered-column, shell-hero-stack, shell-mobile-app, shell-canvas-floating, shell-masonry
- **Styles:** style-glassmorphism (warm-tinted variant), style-claymorphism (desaturated), style-aurorism (sage/oat mesh), style-cream-humanist, style-serif-warm-paper
