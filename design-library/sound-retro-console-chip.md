---
registerId: retro-console-chip
name: Retro console chip
category: game-juice
role: feedback
pairsPrototypes: [aesthetic-8-bit-generic, aesthetic-pixel-nes-mario, aesthetic-pixel-game-boy-mono, aesthetic-pixel-snes-jrpg, aesthetic-pixel-arcade]
notForUseWhen: Modern product surfaces, anything where the retro reference would read as accidental rather than chosen.
---

# Retro console chip

Square waves, triangle bass and one noise channel, with the voice limits of the hardware left intact.

## Sonic signature

The whole register is defined by constraint. Period console audio had a handful of channels and a fixed palette: two pulse waves at a few duty cycles, a triangle for bass, a noise generator for percussion and impacts, and on later hardware a single low-rate sample channel. Everything must sound like it came out of that set. A cue with a lush pad or a real recorded impact breaks the illusion instantly, and the illusion is the point.

Cues are built from pitch, not from timbre. A confirm is a two-note ascending arpeggio on a pulse wave. A cancel is the same shape inverted. A hit is a short noise burst with a fast decay. Damage is a descending pitch slide with the duty cycle swept. Because the palette is so narrow, pitch contour does all the semantic work, and the set should be composed as a small vocabulary of intervals rather than as a bag of sounds.

Fidelity matters in both directions. Sample rate and bit depth should be audibly limited, with the aliasing left in rather than filtered out, and there is no reverb because the hardware had none. The Game Boy variant of this register goes further and is monophonic, narrower in band and slightly detuned; the SNES variant permits short sampled instruments and a little dry reverb, which is the top of what this register allows before it becomes something else.

## Prompt keywords per mode

**SFX**: chiptune, square wave, pulse wave, triangle bass, noise channel, 8-bit, NES, Game Boy, arpeggio, pitch slide, bitcrushed, aliased, no reverb, monophonic, low sample rate

**TTS delivery**: not typically used; when needed, short, dry, heavily bandlimited to sit inside the fiction

**Music**: chiptune, square lead over triangle bass, noise-channel percussion, 120 to 165 bpm, looped ABAB structure, bright and repetitive, no reverb, no acoustic instruments

## Example prompt templates

**SFX**

> A classic 8-bit coin pickup: a two-note ascending square wave arpeggio, fast attack, hard gate at the end, no reverb, bitcrushed to an early console sample rate, about 250ms.

> An 8-bit damage sound: a descending pulse wave pitch slide with the duty cycle sweeping, layered with a very short noise channel burst, harsh and dry, about 400ms.

> A Game Boy style menu confirm: a single short square wave blip at a high pitch, monophonic, narrow band, slightly detuned, no reverb, under 150ms.

**TTS**

> Level clear. Press start to continue.

> Not enough gold. Come back later.

**Music**

> Chiptune loop at 148 bpm with a bright square wave lead, a second pulse channel playing a counter melody, triangle wave bass and noise channel percussion, ABAB structure, no reverb and no acoustic instruments, loops seamlessly with no intro or ending.

## Voice casting

Voice is optional and slightly against the grain here, because the hardware being referenced could barely produce speech. When a piece needs it, cast **Elli** (`MF3mGyEYCl7XYWbV9V6O`) for a character line, or **Arnold** (`VR6AewLTigWG4xSOukaG`) for an announcer on an arcade-leaning variant.

Direct for brevity and treat the output as a sample, not as a performance: generate the line, then bandlimit and bitcrush it in the build so it belongs to the same machine as everything else. `stability` around 0.5, `style` low, scripts under six words. If the piece is committed to the Game Boy variant, prefer no voice at all and use a text box with a per-character blip instead, which is both period-correct and cheaper.

## Loudness defaults

- `masterGainBudget`: 0.75
- `fx`: 0.6
- `music`: 0.3
- `voice`: 0.85
- `duckMusicTo`: 0.14
- `duckReleaseMs`: 350

## When to use

Pixel-art games and pages, retro console tributes, anything where the visual register is explicitly period hardware.

## When NOT to use

Modern product surfaces, anything where the retro reference would read as accidental rather than chosen.

## Pairs with (prototype slugs)

- `aesthetic-8-bit-generic`
- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-pixel-snes-jrpg`
- `aesthetic-pixel-arcade`
