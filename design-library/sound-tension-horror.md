---
registerId: tension-horror
name: Tension horror
category: cinematic
role: ambient
pairsPrototypes: [aesthetic-weirdcore, aesthetic-dreamcore, aesthetic-cottagegoth, aesthetic-cosmic-horizon]
notForUseWhen: Anything for a general audience without warning, onboarding, or a surface a visitor cannot leave quickly.
---

# Tension horror

A room that is slightly wrong, held for too long, with almost nothing in it.

## Sonic signature

This register works by withholding. The bed is a low drone somewhere under 100Hz with a slow beating between two detuned layers, so it never quite settles and the ear keeps waiting for it to. Over it, sparse high partials that arrive without a cause: a distant metallic scrape, a settling structure, something rubbing that stops before you can identify it. The events must be rare. Tension is a function of the gap between events, and a piece that puts something in every four seconds is not tense, it is busy.

Frequency content is deliberately uncomfortable at both ends. There is sub energy you feel rather than hear, and there are thin high partials with slow beating that sit in the range the ear finds hardest to localise. The mid is largely empty, which is why anything that does appear there reads as significant. Reverb is long and slightly metallic, as if the room has hard surfaces in the wrong places.

Restraint is the craft. The genre's cheap move is the stinger, a loud sharp hit on a reveal, and it works exactly once per piece. Everything else should be pressure: the drone rising a semitone over thirty seconds, a layer being added that the visitor does not consciously notice, silence being introduced where sound had been. Removing the bed entirely for three seconds is the most frightening thing this register can do and it costs nothing.

## Prompt keywords per mode

**SFX**: low drone, detuned beating, sub-bass pressure, distant metallic scrape, structure settling, sparse, unresolved, long metallic reverb, breath, dread, unidentifiable

**TTS delivery**: quiet, close, slightly too calm, uneven pauses, flat affect, no projection, unresolved cadence

**Music**: dark ambient, no pulse, detuned sustained strings, prepared piano, 50 bpm or free time, minor second intervals, slowly rising, no resolution, loops seamlessly

## Example prompt templates

**SFX**

> A low sustained drone built from two slightly detuned layers beating slowly against each other, heavy sub content, no melody and no resolution, dark and pressurising, seamless 40 second loop.

> A distant metallic scrape somewhere above and behind, brief and unidentifiable, long slightly metallic reverb tail, quiet, about one and a half seconds.

> A large wooden structure settling once in an empty building, low and soft with a long decay, no bright transient, roughly two seconds.

**TTS**

> There is nothing on the third floor. There has not been for some time.

> You can stop. I am not going to tell you to stop... but you can.

**Music**

> Dark ambient bed in free time with no pulse, detuned sustained strings and prepared piano resonances, minor second intervals held unresolved, slowly rising in pitch over the loop, very quiet, loops seamlessly with no resolution.

## Voice casting

**Charlotte** (`XB0fDUnXU5powFXDhCwa`) is the strongest cast here, because measured and luxurious delivered against a wrong room reads as far more unsettling than anything performed as scary. **Josh** (`TxGEqnHWrfWFTfGW9XjX`) is the alternate for a first-person voice inside the world.

Direct for calm, not for menace. `stability` high at about 0.7 so the read stays level, `style` at 0.1 or below, and let the discomfort come from what is being said and from the uneven placement of pauses. Ellipses are useful here in a way they are almost nowhere else. Never direct for a whisper or a growl; both read as costume and break the register instantly.

**This register needs consent.** Do not autostart it, warn before it begins, and keep the mute affordance visible at all times.

## Loudness defaults

- `masterGainBudget`: 0.75
- `fx`: 0.5
- `music`: 0.25
- `voice`: 0.9
- `duckMusicTo`: 0.1
- `duckReleaseMs`: 1500

## When to use

Horror and unease pieces, weirdcore and dreamcore surfaces, a single unsettling passage inside a larger narrative, anything where discomfort is the intended reading.

## When NOT to use

Anything for a general audience without warning, onboarding, or a surface a visitor cannot leave quickly.

## Pairs with (prototype slugs)

- `aesthetic-weirdcore`
- `aesthetic-dreamcore`
- `aesthetic-cottagegoth`
- `aesthetic-cosmic-horizon`
