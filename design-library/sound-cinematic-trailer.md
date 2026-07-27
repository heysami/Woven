---
registerId: cinematic-trailer
name: Cinematic trailer
category: cinematic
role: score
pairsPrototypes: [aesthetic-luxury-cinematic-dark, recipe-ai-foundry-dark, aesthetic-cosmic-horizon, aesthetic-honkai-star-rail-polished-sf, aesthetic-cyberpunk]
notForUseWhen: Dense working tools, long reading surfaces, anything a visitor revisits daily.
---

# Cinematic trailer

Wide, slow, enormous. Sub-bass impacts, reverse swells and a voice that states the stakes.

## Sonic signature

This register is about scale, and scale in audio is made of two things: low frequency energy and long reverb tails. The signature event is the braam, a low brass or synthetic hit with a slow attack, huge sustain and a decay that runs for three or four seconds through a large hall. Under it sits a sub layer you feel more than hear. Around it, reverse swells: a rising sound played backwards so it arrives at a downbeat rather than leaving one, which is the single most effective way to make a title feel inevitable.

Space is enormous and consistent. Everything shares one large convolved hall so the mix reads as a single room the size of a cathedral. Transitions are wide risers and long whooshes with pronounced doppler. Silence is used aggressively: the moment before the biggest hit is a full stop, and cutting the bed to nothing for half a second before a title lands does more work than any amount of added layer.

The pacing is theatrical and finite. This register is designed for a thirty to ninety second arc with a build, a drop and a resolution, which makes it excellent for a hero moment and completely wrong as a persistent bed. If a page needs continuous sound, this register supplies the entrance and then hands over to something quieter.

## Prompt keywords per mode

**SFX**: braam, sub-bass impact, reverse swell, riser, long tail, huge hall reverb, cinematic whoosh, doppler, taiko hit, metallic scrape, tension drone, boom

**TTS delivery**: deep, slow, weighted, long pauses between clauses, gravitas, understated rather than shouted, one idea per breath

**Music**: orchestral hybrid, low brass, taiko and sub drums, 70 to 90 bpm half time, ostinato strings, builds to a single drop, dark and grand, no vocals

## Example prompt templates

**SFX**

> A single enormous cinematic braam: low synthetic brass with a slow half-second attack, huge sustain and a four second decay through a large stone hall, deep sub layer underneath, dark and final.

> A reverse cymbal and string swell rising over three seconds and cutting to silence at the peak, recorded in a very large reverberant hall, cinematic trailer transition.

> A deep taiko drum struck once in a cavernous space, long natural tail, heavy sub content, no processing beyond the room, about two and a half seconds.

**TTS**

> Everything you know about this... was a rehearsal.

> One system. Every model. Nothing left to configure.

**Music**

> Dark orchestral hybrid trailer cue at 84 bpm in half time, low brass ostinato, taiko and sub drums, tremolo strings rising, one hit at the drop then a long decay, grand and foreboding, no vocals.

## Voice casting

**Adam** (`pNInz6obpgDQGcFmaJgB`) is the cast, and it is not close: deep, grounded, and credible when stating stakes. **Josh** (`TxGEqnHWrfWFTfGW9XjX`) is the alternate when the narration is first person from inside the world rather than an outside voice describing it.

Direct for weight and space. `stability` high at about 0.7 so the read stays controlled, `style` around 0.3 for a little theatre but not more, and scripts broken into very short lines with real gaps so each clause lands against the bed. Use `previous_text` and `next_text` on every clip, because trailer narration is almost always cut into separate beats and the seams are brutally obvious otherwise. Never let the voice compete with a braam; the writing must leave holes for the music.

## Loudness defaults

- `masterGainBudget`: 0.85
- `fx`: 0.75
- `music`: 0.45
- `voice`: 0.95
- `duckMusicTo`: 0.18
- `duckReleaseMs`: 800

## When to use

Hero entrances, product launch moments, title cards, a single theatrical beat in an otherwise quiet page, dark premium marketing.

## When NOT to use

Dense working tools, long reading surfaces, anything a visitor revisits daily.

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `recipe-ai-foundry-dark`
- `aesthetic-cosmic-horizon`
- `aesthetic-honkai-star-rail-polished-sf`
- `aesthetic-cyberpunk`
