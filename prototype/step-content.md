# Step eight - content cascade and voice

Visual leads, content cascades. The slot determines the shape; the genre determines the voice.

### The cascade


```
Subject  →  Genre  →  Shell  →  Components  →  Slots  →  Voice  →  Drafted content  →  Specifics
```


Subject is the only input from outside. From there everything cascades top-down. **You don't draft copy and find a slot. You pick the slot - fixed by genre - and write into its budget.**

### Slot shape determines length

| Slot | Length | Form |
|---|---|---|
| Button label | 1-3 words | imperative verb. "Pause stage" not "Click here to pause this stage." |
| Panel title (uppercase) | 2-4 words | nominal phrase. "Active Runs" not "These are runs that are active." |
| Row primary text | a phrase | declarative. "Microtest plan - objection simulation v3." |
| Row metadata (mono) | abbreviated | technical. "S2 / quiet-hours / b3" not "Stage two, quiet hours, branch three." |
| Status pill | 1 word | uppercase tag. `KEEP` `WARN` `DISCARD`. |
| Description body | 1-2 sentences | full sentences with periods. |
| Editorial body | paragraphs | measured prose with rhythm. |
| Marketing hero | 5-9 words | benefit-led. "Ship when the data says ship." |

A 3-word button slot with 9 words in it is wrong. The slot is a budget - respect it.

### Voice is set by genre, applied at every leaf

All copy in one prototype shares one register. If panel titles are terse-technical, error messages can't be chatty. If a hero is poetic, status pills can't be jokey. **One voice end-to-end.**

| Genre | Voice register |
|---|---|
| Control-room / dashboard | Terse, technical, abbreviated, present tense, lots of fragments |
| Editorial | Measured, narrative, varied sentence length, considered punctuation |
| Marketing | Benefit-first, second person, short declaratives |
| Brutalist | Blunt, declarative, sometimes abrasive, no qualifiers |
| iOS / friendly product | Warm, direct, contractions ("you're set") |
| Bloomberg / finance | Nominal phrases, abbreviations, numbers without commentary |
| Read.cv / portfolio | Restrained, precise, plainspoken, third-person bio |

### Address the audience, never the build team

Every string speaks TO the person using the product, about THEIR world. It never answers the instruction that commissioned the build, never narrates the page to the reader, never describes a feature to a "development team". This is the single most common copywriting failure in generated prototypes: the copy reads like a reply to the brief instead of like the product.

| Write this (to the reader) | Not this (to the build team / instruction) |
|---|---|
| "Ship when the data says ship." | "A clean, modern landing page for a developer-analytics SaaS." |
| "Your last run flagged 3 regressions." | "This dashboard displays the user's key metrics." |
| "Start free. No card." | "Below you will find the pricing section." |
| "Welcome back, Mara." | "Welcome to our website." |

Banned as final copy: instruction-echo, meta-narration ("This section showcases…"), spec/stakeholder address, and lorem/`[BRACKETED TODO]`. Name the benefit, not the mechanism.

**When an `art-direction-contract.json` exists, its `voice` block is authoritative** - write `voice.audience` in `voice.toneWords`, obey `voice.addressPrinciple`, and treat `voice.copyAntiPatterns` as hard bans. The genre voice table above is the fallback when no contract is present.

**Guard - `buildRegister` must NOT bleed into user-facing copy.** The contract may also carry a top-level `buildRegister` block; that governs the LANGUAGE of the build BRIEFS (naming the craft's own model of a thing), and it is a different register from the copy the reader sees. User copy continues to derive ONLY from `voice` (`voice.audience` / `voice.toneWords` / `voice.addressPrinciple`) - never phrase a shipped string in the build register. Two lanes: `buildRegister` for briefs, `voice` for copy.

### Specificity at every leaf

- **Named entities, not "Item 1".** Real-sounding people, projects, branches, IDs, slugs.
- **Specific numbers, not round ones.** `$2.10` and `184k`, not `$2.00` and `200k`.
- **Voice the strings.** "Tester confusion ↓ on tone preset switch (0.42 → 0.31)" beats "Confusion decreased."
- **One coherent fictional world.** All entries belong to one company / publication / domain / week. 5-12 high-quality entries beat 50 generic ones.
- **Information density of language matches information density of layout.** Dense UI demands dense language; breathable UI wants breathable language.
