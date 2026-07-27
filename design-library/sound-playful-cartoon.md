---
registerId: playful-cartoon
name: Playful cartoon
category: game-juice
role: stinger
pairsPrototypes: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis, aesthetic-curly-girly, aesthetic-wacky-pomo, aesthetic-pixel-modern-cozy]
notForUseWhen: Serious subjects, financial or medical surfaces, anything where a joke would undercut trust.
---

# Playful cartoon

Boings, pops and slide whistles. Every motion is exaggerated and every object is bouncy.

## Sonic signature

This register borrows the grammar of animation sound: physics that are funnier than real physics. Things do not land, they boing. Things do not appear, they pop. A rising motion gets a slide whistle, a falling one gets a descending pitch bend, a fast exit gets a zip. The exaggeration is the joke and the joke is consistent, which is what stops it becoming grating; a world where everything is springy is coherent, a world where one button boings is broken.

Materially it is bright and mid-forward with almost no sub content, because weight is the enemy of bounce. Sources are elastic and hollow: a plucked rubber band, a wooden block, a cork leaving a bottle, a spring under tension, a kazoo-adjacent buzz. Pitch bends are used constantly and generously, far more than any other register would tolerate. Decay times are short and everything is dry, because a cartoon world has no room in it.

Character voice is a first-class part of this register rather than an add-on. Small vocal reactions, an "oh!" on a mistake, a hum of approval on success, are more effective than any synthesised cue and they do enormous work on personality. Keep them very short and use a small set on rotation so the same reaction does not fire twice in a row.

## Prompt keywords per mode

**SFX**: boing, cartoon pop, slide whistle, rubber band pluck, wooden block, spring, cork pop, zip, pitch bend, bouncy, dry, mid-forward, exaggerated, comic

**TTS delivery**: bright, animated, expressive, wide pitch range, very short lines, playful, unafraid of a squeak

**Music**: playful acoustic, ukulele or pizzicato strings, wood block and shaker percussion, 110 to 130 bpm, major key, bouncy, loops seamlessly, light and comic

## Example prompt templates

**SFX**

> A cartoon boing: a plucked rubber band with a wide wobbling pitch bend, bright and mid-forward with no sub content, completely dry with no reverb, about 500ms.

> A comic pop as a cork leaves a bottle, bright and hollow with a tiny upward pitch bend on the tail, dry, under 200ms.

> A descending slide whistle over 700ms ending in a soft wooden block knock, dry and exaggerated, classic animation falling gag.

**TTS**

> Oops! Let us try that one again.

> Ta-da! You did it, and honestly, faster than most.

**Music**

> Playful acoustic loop at 122 bpm with pizzicato strings and a ukulele, wood block and shaker percussion, bright major key, bouncy and light, loops seamlessly with no build and no ending.

## Voice casting

**Elli** (`MF3mGyEYCl7XYWbV9V6O`) is the cast: young and emotive, with the expressive range this register lives on. **Domi** (`AZnzlk1XvdvUeBnXmlld`) is the alternate when the character should be confident rather than sweet.

Direct for expressiveness. Low `stability` around 0.3 so every take differs and repeated reactions do not feel canned, `style` lifted to around 0.5 which is the highest this library recommends anywhere, and scripts written as very short exclamations with exclamation marks that the punctuation can actually act on. Generate three or four variants of each reaction and rotate them at runtime; a single perfect "oops" heard four times in a minute stops being charming very quickly.

## Loudness defaults

- `masterGainBudget`: 0.75
- `fx`: 0.6
- `music`: 0.25
- `voice`: 0.9
- `duckMusicTo`: 0.11
- `duckReleaseMs`: 450

## When to use

Kids and family surfaces, mascot-led brands, kawaii and memphis registers, onboarding that wants to be disarming, casual games.

## When NOT to use

Serious subjects, financial or medical surfaces, anything where a joke would undercut trust.

## Pairs with (prototype slugs)

- `aesthetic-positivity-kawaii`
- `aesthetic-corporate-memphis`
- `aesthetic-curly-girly`
- `aesthetic-wacky-pomo`
- `aesthetic-pixel-modern-cozy`
