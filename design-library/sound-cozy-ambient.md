---
registerId: cozy-ambient
name: Cozy ambient
category: ambient
role: ambient
pairsPrototypes: [aesthetic-cottagecore, recipe-warm-restraint, aesthetic-pixel-modern-cozy, aesthetic-pastoral-serene]
notForUseWhen: Urgency, competition, anything with a timer or a score.
---

# Cozy ambient

A warm indoor room with something quietly happening in it: rain on glass, a kettle settling, wool on wood.

## Sonic signature

The organising idea is a room you would be happy to sit in. There is always a bed, and the bed is a real interior: rain against a window with the low rumble filtered out, a fire that ticks rather than roars, the soft broadband hush of a kitchen at the far end of the house. It is warm because the high end is gently rolled off and the low mids are allowed to stay, which is the opposite of the interface registers. Nothing is close-miked; everything sits a metre or two back with a little room around it.

Interactions in this register are made of soft materials meeting soft materials. Wool sliding on wood, a ceramic mug set down on a cloth, a page turning, a wooden drawer easing shut. Transients are rounded off, attacks are slow by cue standards, and every event has a short natural tail rather than a hard gate. The palette deliberately excludes anything metallic, electronic or sharp; if a cue needs to be more noticeable, it gets slightly closer rather than slightly brighter.

Variation over time is what keeps this from becoming wallpaper. The rain should thicken and thin, the fire should occasionally pop, a distant sound should pass every minute or so. Two loops of different lengths layered against each other is the cheapest way to get this: a forty second base and a twenty three second detail layer will not repeat their combination for a long time.

## Prompt keywords per mode

**SFX**: soft rain on glass, crackling hearth, wool on wood, ceramic on cloth, page turn, wooden drawer, muffled, warm, rounded transient, gentle, distant, room tone, indoor

**TTS delivery**: slow, warm, low and close, generous pauses, unhurried, gently smiling, like reading to one person

**Music**: felted piano, acoustic guitar, soft brushed kit, 65 to 80 bpm, major seventh chords, warm and unhurried, loops seamlessly, no build, no drums after the first minute

## Example prompt templates

**SFX**

> Steady soft rain against a single-pane window heard from inside a small wooden room, low rumble rolled off, warm and continuous, loops seamlessly over 30 seconds with no distinct events.

> A ceramic mug set down gently on a folded cloth on a wooden table, close but with a little room around it, rounded transient with a short warm tail, about 500ms.

> A small wood-burning stove: low continuous crackle with occasional soft pops, recorded a metre back in a carpeted room, warm and enveloping, seamless 30 second loop.

**TTS**

> Take your time. Nothing here needs to be finished today.

> The kettle is on. Come back when you are ready and it will still be here.

**Music**

> Slow warm ambient loop at 68 bpm on a felted upright piano with soft acoustic guitar harmonics and a distant bowed cello pad, major seventh voicings, no percussion, patient and unhurried, loops seamlessly with no intro, no build and no ending.

## Voice casting

**Rachel** (`21m00Tcm4TlvDq8ikWAM`) is the natural cast: warm, calm and neutral enough to feel like a friend rather than a brand. **Elli** (`MF3mGyEYCl7XYWbV9V6O`) works when the piece has a character in it and the voice belongs to someone specific rather than to the room.

Direct for slowness and closeness. `stability` around 0.6, `similarity_boost` high so the warmth of the reference timbre survives, `style` low at about 0.15 because the softness should come from the writing, not from performance. Write short sentences with commas where a breath belongs and leave real gaps between clips; a cozy read that rushes is not cozy.

## Loudness defaults

- `masterGainBudget`: 0.65
- `fx`: 0.4
- `music`: 0.2
- `voice`: 0.85
- `duckMusicTo`: 0.09
- `duckReleaseMs`: 900

## When to use

Reading and journalling surfaces, slow-craft product pages, cozy games, anything pastoral or domestic, briefs where the target feeling is permission to slow down.

## When NOT to use

Urgency, competition, anything with a timer or a score.

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `recipe-warm-restraint`
- `aesthetic-pixel-modern-cozy`
- `aesthetic-pastoral-serene`
