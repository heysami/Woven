---
registerId: museum-hush
name: Museum hush
category: ambient
role: narration
pairsPrototypes: [aesthetic-sculptural-minimal, style-cream-humanist, aesthetic-dark-academia, recipe-neo-grotesque-portfolio, recipe-editorial-magazine]
notForUseWhen: Anything commercial, urgent, or competing for attention.
---

# Museum hush

The sound of a large quiet room with stone floors, and one measured voice standing in it.

## Sonic signature

The bed is a room, not a texture. A gallery at low occupancy has a specific signature: a broad low-level hush from ventilation, a long decay time from hard floors and high ceilings, and occasional distant human events that are never quite legible as speech. That last part is essential. A footstep three rooms away, a door easing shut on the far side of a hall, a chair moving. They arrive rarely and heavily reverberated, and they are what tell the ear the space is large and populated without ever becoming content.

Cues are almost absent. Where a surface needs feedback it gets something felt rather than heard: a very soft low thud with a long tail, at a level where the visitor is not sure whether it sounded or not. Nothing bright, nothing fast, nothing that could be described as a click. The register treats an audible interface as a category error, because the fiction is that you are in a building, not using software.

The voice is the counterweight. It is close, dry and measured against the wet distant room, which produces the exact effect of a curator standing next to you while the hall stretches away behind. That contrast between an intimate voice and a huge space is the whole trick and it should be preserved in the mix rather than smoothed out.

## Prompt keywords per mode

**SFX**: large stone hall, long reverb tail, low ventilation hush, distant footsteps, muffled far-off door, high ceiling, sparse, felt not heard, soft low thud, unhurried

**TTS delivery**: slow, measured, low volume, generous pauses, precise diction, no enthusiasm, standing close in a large room

**Music**: single bowed string or glass harmonica tone, free time, one slowly shifting chord, extremely quiet, loops seamlessly, no rhythm, no melody

## Example prompt templates

**SFX**

> The ambience of a large empty stone gallery: broad low ventilation hush, very long natural reverb decay, occasional distant unintelligible footsteps far across the hall, sparse and calm, seamless 40 second loop.

> A heavy wooden door easing shut two rooms away in a marble-floored building, heavily reverberated, soft and distant, about two seconds including the tail.

> A very soft low thud with a long slow decay in a large hall, felt more than heard, no transient brightness, about 900ms.

**TTS**

> This piece was never finished. What you are looking at is the last state the artist left it in, in the winter of nineteen seventy one.

> Take the left doorway when you are ready. There is no particular order to any of this.

**Music**

> A single bowed glass tone sustaining and slowly shifting in free time, no pulse and no melody, extremely quiet, recorded in a large reverberant hall, loops seamlessly with no development.

## Voice casting

**Charlotte** (`XB0fDUnXU5powFXDhCwa`) is the cast for this register and the reason she is in the map: measured and luxurious, with the natural slowness a gallery label wants read aloud. **Rachel** (`21m00Tcm4TlvDq8ikWAM`) is the alternate when the piece wants a warmer, less formal curator.

Direct for slowness and lowered volume. `stability` around 0.7, `style` low at 0.1, and write scripts with commas and full stops placed where you want the visitor to look up. Long clauses are fine here in a way they are not elsewhere, because the register rewards a sentence that unfolds. Leave at least a second of silence at the head and tail of every clip so the room can be heard around the voice.

## Loudness defaults

- `masterGainBudget`: 0.6
- `fx`: 0.28
- `music`: 0.14
- `voice`: 0.9
- `duckMusicTo`: 0.06
- `duckReleaseMs`: 1400

## When to use

Exhibition microsites, memorial pieces, portfolio and gallery surfaces, luxury brands with restraint, archival collections.

## When NOT to use

Anything commercial, urgent, or competing for attention.

## Pairs with (prototype slugs)

- `aesthetic-sculptural-minimal`
- `style-cream-humanist`
- `aesthetic-dark-academia`
- `recipe-neo-grotesque-portfolio`
- `recipe-editorial-magazine`
