---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-skeuomorphism-ui.png
    reason: Style surface UI mockup.
  - src: style-skeuomorphism-isolated.png
    reason: Signature surface, isolated.
---
# Skeuomorphism (style)

**Tag:** `style-skeuomorphism`

**Canonical references:** iOS 6 Notes · iOS 6 iBooks · Game Center · Letterpress · Vesper · Tweetbot

> **Raster required:** leather / wood / felt / brushed-metal / linen / paper textures (PNG with subtle grain) + the one committed metaphor object (page-curl, brass screw, tape-reel hub, wood-shelf grain). Faking textures in CSS gradients reads as plastic-toy mode. Before drawing, follow the [**Raster requirements**](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree in the main playbook.

## Surface treatment

**One committed metaphor per surface.** Named in the `GENRE` comment: `notes-as-legal-pad`, `library-as-wood-shelf`, `recorder-as-tape-deck`, `mixer-as-rack-unit`. Never stack metaphors - leather header + felt body + wood shelf = trashy by definition.

**Substrates** (raster, full-bleed where the metaphor lives):
- Legal-pad cream `#F8E9A4` with horizontal rule-lines `1px solid #D9C46B` at `22px` rhythm + single red margin-line `1.5px solid #C44` at `48px`
- Walnut wood `#6B4226 → #3E2412` vertical-grain
- Poker felt `#0F4D2A` with subtle noise
- Apple linen `#C8C0B0` (OS chrome only, never inside a card)

**Type stack:**
- Body / title / subtitle - Helvetica Neue Light 17 / Bold 17 / Regular 13 (iOS-6 system)
- Marker Felt / Noteworthy / Bradley Hand 17px - ONLY when the metaphor demands handwriting on a legal pad
- Forbidden: Lobster, Comic Sans, Pacifico

**Type sizes:** 11 / 13 / 15 / 17 / 20 / 24 (iOS-6 points)

**Accents:**
- iOS-6 system blue `#147EFB` for tappable text
- Metaphor's warm tone for the one surface the metaphor owns: `#C44` paper-margin red, `#B8860B` brass, `#2E7D32` felt-thread green

**Radii:** `5px` grouped table cells · `8px` buttons · `0` on the metaphor's surface (a legal pad has no rounded corners)

**Borders:** hairline `1px solid rgba(0,0,0,0.15)` on dividers. Stitching ONLY where the metaphor justifies it (leather case = yes; felt table = no):
```
border: 1.5px dashed #C9A878;
outline: 1px solid rgba(0,0,0,0.2);
outline-offset: 2px;
```

**Shadow recipes** - every raised element gets the iOS-6 pill:
```
/* Button */
box-shadow:
  inset 0 1px 0 rgba(255,255,255,0.5),
  inset 0 -1px 0 rgba(0,0,0,0.1),
  0 1px 2px rgba(0,0,0,0.25);

/* Card - one ambient drop only */
box-shadow: 0 2px 4px rgba(0,0,0,0.18);
```
Never stack shadows. Never apply shadow to text.

**Gradients:** button-fill is a 4-8% lightness step (`linear-gradient(180deg, #F4F4F4, #DCDCDC)`), not a 40% step. Big steps = plastic toy. No radial gradients. No "shine" sweeps.

## Decoration grammar

The metaphor IS the decoration. Mandatory if the metaphor implies them, forbidden otherwise: stitching, paper grain, wood grain, brass screws, tape-reel hubs, felt nap, leather creasing. Each instance must belong to the *one* metaphor committed in the `GENRE` comment.

## Motion budget

Motion is the metaphor moving, never decorative:
- Page-curl on paper-bound surfaces (Calendar / iBooks) - genre-mandatory if metaphor is paper
- Tape-reel rotation on tape-bound media - genre-mandatory if metaphor is tape
- Spring-pop on tile drag (Letterpress) - `cubic-bezier(0.5, 1.6, 0.4, 1)` 220ms

No motion on chrome that doesn't move in real life. No idle shimmer.

## Failure mode

Stacked metaphors (leather header + felt body + wood-shelf footer + linen behind). Lobster / Marker Felt-because-"paper" everywhere. Drop shadows on every text label. Brushed-metal title bar above poker-felt content (metals contradict fabrics). `box-shadow: inset 0 1px rgba(255,255,255,0.6), 0 4px 12px rgba(0,0,0,0.5)` slapped on a generic "Sign In" pill. Radial-gradient "glossy" reflections. Fake screws in the corners of a Notes app. Comic-Sans handwritten "Welcome!" on a wood shelf. Gruber's "rich Corinthian leather." If you can't name the *one* metaphor and the *one* function it carries in a single sentence in the `GENRE` comment, you've drifted into cosplay.

## Best for

Nostalgic single-purpose apps (calculator, notepad, metronome, tape-recorder, leveler). Micro-tool landing pages that lean on a real-world metaphor. Intentional-retro indie utilities. Museum / archive sites recreating the Forstall era.

Never for: dashboards, CRMs, anything where the metaphor isn't doing functional work.

## Pairs well with

- **Shells:** shell-mobile-app (the home genre - top-bar 44pt + content + tab-bar 49pt), shell-centered-column, shell-hero-stack
- **Aesthetics:** aesthetic-frutiger-aero, aesthetic-y2k-futurism, aesthetic-frutiger-chromecore, aesthetic-cottagecore (paper-bound metaphors), aesthetic-dark-academia (leather / book metaphors)
