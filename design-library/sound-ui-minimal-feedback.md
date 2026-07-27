---
registerId: ui-minimal-feedback
name: Minimal interface feedback
category: interface
role: feedback
pairsPrototypes: [style-restrained-hairline, recipe-linear-product-ui, recipe-devtools-marketing, aesthetic-swiss-modernist, aesthetic-monochrome-tech-editorial]
notForUseWhen: Games, marketing hype pages, anything that wants atmosphere or a bed.
---

# Minimal interface feedback

Short, dry, close-miked confirmations that tell you an action landed and then get out of the way.

## Sonic signature

This register is built out of very small physical events recorded very close. A fingernail on brushed aluminium, a magnetic catch seating, a fabric-damped key bottoming out, a single grain of sand dropped on glass. Nothing rings. Nothing has a tail. The whole cue is over in a fifth of a second and the room it was recorded in is deliberately dead, so there is no sense of a place at all, only of a surface responding under your hand.

Tonally it sits high and narrow. Energy lives between roughly 1kHz and 6kHz with the low end rolled away entirely, because low end reads as weight and weight reads as consequence, which is wrong for a toggle. Cues are differentiated by material and pitch rather than by length or volume: a confirm is slightly brighter and rounder than a select, an error is the same gesture with the pitch pulled down and a touch of damping added, never a buzzer. The set should sound like one object family, as though every control on the page were cut from the same block.

There is no music bed and there is no ambience. Silence between cues is not an absence in this register, it is the ground the cues stand on. A visitor who never notices the sound layer at all, but who feels the interface is slightly more responsive than it was, is the target outcome.

## Prompt keywords per mode

**SFX**: close-miked, dry booth, no reverb, brushed aluminium, machined detent, magnetic catch, fabric-damped, single tick, soft click, muted thock, short 120ms, no tail, no ring, tiny

**TTS delivery**: level, unhurried, low affect, short clauses, no rising inflection, matter-of-fact, quiet room, spoken not performed

**Music**: not used in this register

## Example prompt templates

**SFX**

> A single machined aluminium detent clicking into position, close-miked in a dry acoustically dead booth, no reverb and no tail, a very short 120ms tick with a soft rounded transient.

> A small magnetic catch seating against a steel plate, one event only, close-miked with no room, crisp and quiet, roughly 150ms, no ring and no decay.

> A fingertip releasing a fabric-damped key switch, a muted low-mid thock with the click damped out, dry booth, no reverb, under 200ms.

**TTS**

> Saved. Your changes are live on this branch.

> That address does not look complete. Check the postcode and try again.

**Music**

> Not used. This register ships with no bed. If a brief demands one, it has picked the wrong register.

## Voice casting

Voice is rare here and used only for confirmations that genuinely need words, such as an accessibility announcement or a completed long-running job. **Rachel** (`21m00Tcm4TlvDq8ikWAM`) is the cast: neutral, warm enough not to sound robotic, and completely uninterested in drawing attention. **Antoni** (`ErXwobaYiN019PkySvjV`) is the alternate when the product's written voice is already friendly.

Direct for flatness. High `stability` around 0.75 so repeated announcements are identical, `style` at 0 because any performance at all sounds wrong on a system message, and short single-clause scripts with a full stop at the end so the read does not drift upward into a question.

## Loudness defaults

- `masterGainBudget`: 0.55
- `fx`: 0.35
- `music`: 0.0
- `voice`: 0.8
- `duckMusicTo`: 0.0
- `duckReleaseMs`: 300

## When to use

Productivity tools, dashboards, developer products, settings surfaces, anything dense and frequently used. Any brief where the visual register is restrained and the visitor is working rather than visiting.

## When NOT to use

Games, marketing hype pages, anything that wants atmosphere or a bed.

## Pairs with (prototype slugs)

- `style-restrained-hairline`
- `recipe-linear-product-ui`
- `recipe-devtools-marketing`
- `aesthetic-swiss-modernist`
- `aesthetic-monochrome-tech-editorial`
