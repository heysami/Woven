---
registerId: documentary-narration
name: Documentary narration
category: spoken
role: narration
pairsPrototypes: [recipe-newspaper-of-record, style-serif-warm-paper, recipe-editorial-magazine, aesthetic-monochrome-tech-editorial]
notForUseWhen: Games, playful brands, anything where the voice would be a character rather than a witness.
---

# Documentary narration

A credible human explaining something they understand, over almost nothing.

## Sonic signature

The voice is the whole design here, and everything else is subtraction. The read sits close but not intimate, in a treated room with just enough early reflection to sound like a real space rather than a booth. There is no music under the first sentence and often none at all; where a bed exists it is a single sustained texture at the edge of audibility, present only so the silence between paragraphs does not sound like a dropout.

Sound effects are used sparingly and always diegetically: the object being discussed, recorded honestly. If the piece is about a printing press, you hear the press once, at the moment it is named, at real scale. There are no interface cues in this register at all. A tick under a scroll would break the frame, because the frame is that someone is talking to you and you are listening.

Structure carries the pacing. Paragraphs are separated by real silence of a second or more, which lets the previous idea settle and signals that a new one is coming. Emphasis comes from sentence construction rather than from performance: the important word goes at the end of a short sentence. The register fails when the read starts to sound like advertising, and the tell is always the same, a rising cadence at the end of a clause.

## Prompt keywords per mode

**SFX**: diegetic, recorded honestly, real scale, single event, treated room, no processing, archival, mechanical, distant traffic, paper, no interface cues

**TTS delivery**: measured, credible, mid pace, falling cadence, real pauses between paragraphs, informed rather than enthusiastic, no upward inflection

**Music**: single sustained string or synth pad, no rhythm, 60 bpm or free time, one chord, barely present, loops seamlessly, no development

## Example prompt templates

**SFX**

> A large flatbed printing press running one full cycle, recorded honestly from three metres in a factory space with real room reflections, mechanical and rhythmic, no processing, about four seconds.

> Distant city traffic heard from an upper-floor window, low and continuous with no distinct events, treated as a bed rather than a moment, seamless 30 second loop.

**TTS**

> The first machine took eleven months to build. The second took nine days. Nobody involved could explain the difference, and that, more than anything else, is what this chapter is about.

> She kept the notebooks for forty years. They are, as far as anyone can tell, complete.

**Music**

> A single sustained string pad on one minor chord, free time with no pulse, very quiet and slowly evolving, loops seamlessly with no development, no percussion and no melody.

## Voice casting

**Rachel** (`21m00Tcm4TlvDq8ikWAM`) is the default narrator for this register and the reason she is the daemon's default voice at all: calm, warm, neutral, credible. **Antoni** (`ErXwobaYiN019PkySvjV`) is the alternate for a male read that stays warm; **Adam** (`pNInz6obpgDQGcFmaJgB`) only when the subject matter genuinely wants gravity, because his weight can tip a piece from documentary into trailer.

Direct for consistency above all, because this register is almost always many clips long. `stability` high at about 0.75, `similarity_boost` around 0.7, `style` at 0 or 0.1. Set `previous_text` and `next_text` on every single clip; a documentary read is the worst case for cold-start prosody and the best case for continuity fields. Pin a `seed` once a take is approved so a rebuild does not reroll the performance halfway through a chapter.

## Loudness defaults

- `masterGainBudget`: 0.7
- `fx`: 0.35
- `music`: 0.12
- `voice`: 0.95
- `duckMusicTo`: 0.05
- `duckReleaseMs`: 1200

## When to use

Editorial long form, explainers, case studies, archival storytelling, any surface where the credibility of the speaker is the product.

## When NOT to use

Games, playful brands, anything where the voice would be a character rather than a witness.

## Pairs with (prototype slugs)

- `recipe-newspaper-of-record`
- `style-serif-warm-paper`
- `recipe-editorial-magazine`
- `aesthetic-monochrome-tech-editorial`
