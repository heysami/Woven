---
registerId: natural-field-recording
name: Natural field recording
category: ambient
role: ambient
pairsPrototypes: [aesthetic-solarpunk, aesthetic-frutiger-eco, aesthetic-organic-overgrowth, aesthetic-bioluminescent-deep, aesthetic-cottagecore]
notForUseWhen: Interfaces that need clear discrete feedback, dense tools, anything indoors and urban.
---

# Natural field recording

An outdoor place captured honestly, with distance and weather in it, and no music at all.

## Sonic signature

This register commits to a location and stays there. A specific place at a specific hour: a broadleaf wood an hour after dawn, a tidal estuary at low water, a high meadow with wind moving through it. What makes a field recording read as real rather than as a nature-sounds product is depth. There must be near events, mid events and far events, and the far ones must be quieter and duller in a way that is consistent with distance. A bird two metres away and a bird two hundred metres away are not the same sound at different volumes.

There is no music in this register. Adding a pad under a field recording is the single most common way to ruin one, because the pad supplies an emotional reading that the recording was doing better on its own. If a brief insists on tonality, it should come from something in the place: water over stone has pitch, wind through a gap has pitch, a distant bell has pitch.

Interaction cues are drawn from the same place. A footstep on the actual surface, a branch moving, water displaced. They are recorded at the same distance and in the same weather as the bed so they sit inside it rather than on top of it. Anything synthetic, anything indoor and anything with a hard gate is out. Where a cue would be intrusive, use a very slight lift in the bed instead and let the place respond rather than the interface.

## Prompt keywords per mode

**SFX**: field recording, binaural, outdoor, dawn chorus, wind in leaves, water over stone, distant birdsong, near and far layers, natural depth, no processing, unhurried, weather

**TTS delivery**: quiet, unhurried, spoken outdoors, low volume, close mic against a wide background, no projection

**Music**: not used in this register

## Example prompt templates

**SFX**

> A broadleaf woodland an hour after dawn recorded from a clearing: layered birdsong with near and distant voices, soft wind moving high in the canopy, one stream faintly audible far off, natural depth and no processing, seamless 45 second loop.

> A shallow stream running over rounded stones, recorded half a metre from the surface with the far bank audible behind it, continuous and bright without hiss, seamless 30 second loop.

> A single footstep on wet leaf litter in an open wood, recorded at the same distance and in the same weather as the surrounding ambience, soft and unprocessed, about 600ms.

**TTS**

> The tide turns at about four. Until then this whole flat is walkable.

> Listen for a moment before you go on. There are three different birds in this, and only one of them is close.

**Music**

> Not used. Tonality in this register comes from the place itself, never from an added pad.

## Voice casting

**Rachel** (`21m00Tcm4TlvDq8ikWAM`) for a warm neutral guide, or **Antoni** (`ErXwobaYiN019PkySvjV`) when the piece wants someone who clearly knows the ground. Avoid the deep cinematic voices entirely; weight is the wrong quality outdoors.

Direct for quietness and lack of projection. The fiction is someone speaking near you outdoors, not narrating over a picture of outdoors, so the read should be low in volume and slightly under-articulated rather than crisp. `stability` around 0.6, `style` at 0.1, and the mix should place the voice close and dry against the wide wet bed rather than adding reverb to match it.

## Loudness defaults

- `masterGainBudget`: 0.65
- `fx`: 0.45
- `music`: 0.0
- `voice`: 0.88
- `duckMusicTo`: 0.0
- `duckReleaseMs`: 1000

## When to use

Environmental and ecological briefs, solarpunk and eco registers, slow scrolling journeys through a place, anything where the subject is the outdoors itself.

## When NOT to use

Interfaces that need clear discrete feedback, dense tools, anything indoors and urban.

## Pairs with (prototype slugs)

- `aesthetic-solarpunk`
- `aesthetic-frutiger-eco`
- `aesthetic-organic-overgrowth`
- `aesthetic-bioluminescent-deep`
- `aesthetic-cottagecore`
