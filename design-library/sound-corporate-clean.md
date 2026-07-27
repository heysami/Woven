---
registerId: corporate-clean
name: Corporate clean
category: interface
role: feedback
pairsPrototypes: [recipe-bento-marketing, recipe-scientific-infra-marketing, style-glassmorphism, recipe-material-3, recipe-linear-product-ui]
notForUseWhen: Anything with grit, irony, or a handmade register.
---

# Corporate clean

Polished, tuned, optimistic. Glass and soft synth, all in one key, nothing rough.

## Sonic signature

Everything in this register is tuned. Cues are pitched to a shared key so a sequence of them never produces a dissonant interval, which is what makes a busy product surface feel composed rather than clattery. The palette is glassy and synthetic in a premium way: bell and marimba-adjacent tones, soft filtered sines, gentle plucked synths with a short bright attack and a clean decay. There is always a small tasteful reverb, enough to imply a bright room, never enough to smear.

Compared to `ui-minimal-feedback` this register is allowed to be pleasant. A confirm can be a two-note rising interval rather than a tick, a completion can have a small shimmer, an onboarding step can get a soft chord. The upper bound is that nothing may sound like a game. If a cue would make someone smile, it is close to the edge; if it would make them grin, it is over it.

The music bed, when present, is a slow ascending arpeggio pad with no percussion, sitting very low. It exists for hero moments and product-tour sections, not for the whole application, and it should be arranged so it can start and stop on a section boundary without needing a resolution. Transitions between sections get a soft filtered whoosh rather than an impact.

## Prompt keywords per mode

**SFX**: glassy, tuned, bell tone, soft synth pluck, filtered sine, small bright reverb, polished, clean decay, gentle whoosh, premium, optimistic, no distortion

**TTS delivery**: clear, warm, confident, mid pace, friendly but not casual, even emphasis, no hard sell

**Music**: ambient electronic, ascending synth arpeggio, warm pad, 90 to 110 bpm or free time, no percussion, major key, optimistic, loops seamlessly

## Example prompt templates

**SFX**

> A soft glassy confirmation chime: two clean bell tones rising a major third, gentle attack, smooth decay with a small bright room reverb, tuned and polished, about 600ms.

> A gentle filtered whoosh for a section transition: soft filtered noise sweeping upward over 800ms into a quiet glassy tail, clean and premium, no distortion and no impact.

> A soft synth pluck for a selection: single filtered sine with a short bright attack and a clean 300ms decay, tuned, small room, unobtrusive.

**TTS**

> Your workspace is ready. Everything you connected has already synced.

> Two steps left. This next one takes about a minute.

**Music**

> Ambient electronic bed in free time, slow ascending synth arpeggio over a warm major pad, no percussion, bright and optimistic, very low in the mix, loops seamlessly with no build and no ending.

## Voice casting

**Antoni** (`ErXwobaYiN019PkySvjV`) is the primary: warm, well rounded, credible on a product tour without sounding like an advert. **Rachel** (`21m00Tcm4TlvDq8ikWAM`) is the alternate and the safer pick when the copy is dense or instructional.

Direct for clarity and even emphasis. `stability` around 0.65 so a long tour stays consistent, `similarity_boost` around 0.75, `style` at 0.15. Write in short declarative sentences and resist the urge to add enthusiasm markers; the optimism should come from the sound design, not from the read. Set `previous_text` and `next_text` across tour steps so the sequence reads as one voice rather than as separate recordings.

## Loudness defaults

- `masterGainBudget`: 0.7
- `fx`: 0.45
- `music`: 0.2
- `voice`: 0.9
- `duckMusicTo`: 0.08
- `duckReleaseMs`: 600

## When to use

SaaS marketing, onboarding flows, product tours, bento marketing pages, glassmorphic and material registers, anything premium and reassuring.

## When NOT to use

Anything with grit, irony, or a handmade register.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-scientific-infra-marketing`
- `style-glassmorphism`
- `recipe-material-3`
- `recipe-linear-product-ui`
