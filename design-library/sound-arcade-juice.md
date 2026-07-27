---
registerId: arcade-juice
name: Arcade juice
category: game-juice
role: feedback
pairsPrototypes: [aesthetic-pixel-arcade, aesthetic-rgb-gamer, aesthetic-y2k-memphis-loud, aesthetic-persona-5-heist-pop]
notForUseWhen: Productivity tools, editorial reading, anything a visitor uses for more than a few minutes at a time.
---

# Arcade juice

Loud, bright, escalating feedback where every action is rewarded and combos climb in pitch.

## Sonic signature

The defining property of this register is that sound is a reward, not a report. Every collision, pickup and score event gets a cue with real transient force and real brightness, and the cues are tuned so that a fast sequence of them reads as music rather than as noise. Pickups climb a scale as a combo builds and reset when it breaks, which turns the score system into something you can hear before you can read it. Impacts have a compressed punch with a short bright attack and a fast decay, so they cut through whatever else is playing without eating the whole mix.

Materially it is synthetic and proud of it. Bright saw and square tones, filtered noise bursts for hits, a pitched sine thump for weight, plate-style shimmer on the biggest events. Nothing here is trying to sound like a real object; it is trying to sound like a machine celebrating. Whooshes are wide and swept, failures are downward pitch slides rather than harsh buzzes, and the largest events get a short stinger with a tail long enough to feel like a full stop.

Density is the risk. The register only works if the loud events are rare relative to the quiet ones. A win fanfare that plays every four seconds is not a fanfare. Build the cue set as a pyramid: many very short ticks at the bottom, a handful of mid-weight impacts, and exactly one or two top-of-pyramid stingers per session.

## Prompt keywords per mode

**SFX**: bright synthetic, pitched ascending, arcade cabinet, coin pickup, power-up sweep, punchy transient, compressed, filtered noise burst, upward pitch slide, plate shimmer, chunky, energetic

**TTS delivery**: forward-leaning, high energy, clipped, announcer cadence, short exclamations, confident, no hesitation

**Music**: driving electronic, 128 to 150 bpm, syncopated bass, bright synth lead, four-on-the-floor kick, loops seamlessly, no intro and no ending, relentless, upbeat

## Example prompt templates

**SFX**

> A bright synthetic coin pickup, a short ascending two-note chime with a fast attack and a quick shimmering decay, arcade cabinet character, close and compressed, about 300ms.

> A chunky impact hit for a successful strike: a filtered white noise burst layered over a pitched sine thump that drops a fifth, punchy and compressed, no room, about 400ms.

> A power-up sweep: an upward filtered sawtooth rising over 900ms into a bright sustained ring, energetic and synthetic, ending with a short plate shimmer.

**TTS**

> Combo! Four in a row, keep it going.

> Round over. Nice run, that is a new personal best.

**Music**

> Driving electronic arcade loop at 140 bpm, syncopated bass synth, bright square lead, four-on-the-floor kick and tight closed hats, energetic and relentless, loops seamlessly with no intro, no build and no ending.

## Voice casting

**Domi** (`AZnzlk1XvdvUeBnXmlld`) is the primary cast: strong and confident, with natural forward lean, which is exactly what a callout needs. **Arnold** (`VR6AewLTigWG4xSOukaG`) is the alternate when the piece wants a scoreboard announcer rather than a companion.

Direct for speed and attack. Low `stability` around 0.3 so consecutive callouts differ slightly and repeated play does not feel canned, `style` lifted to about 0.4 for performance, and scripts written as short exclamations with no subordinate clauses. Keep every line under two seconds; a callout that outlasts the moment it is describing kills the pace.

## Loudness defaults

- `masterGainBudget`: 0.8
- `fx`: 0.7
- `music`: 0.3
- `voice`: 0.9
- `duckMusicTo`: 0.12
- `duckReleaseMs`: 400

## When to use

Score-driven games, high-energy landing pages, anything with a combo or streak mechanic, pixel and arcade aesthetics, RGB gamer registers.

## When NOT to use

Productivity tools, editorial reading, anything a visitor uses for more than a few minutes at a time.

## Pairs with (prototype slugs)

- `aesthetic-pixel-arcade`
- `aesthetic-rgb-gamer`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-persona-5-heist-pop`
