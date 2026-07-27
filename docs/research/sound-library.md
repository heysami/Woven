# Sound Library - research dossier for sound-orchestrator

> Canonical reference for the **sound design** family: the sonic register a prototype wears, and the prompt grammar that gets ElevenLabs to render it. Every entry is one REGISTER - a coherent world of interface ticks, ambience, voice casting and music bed that belong together.
>
> Per-entry source files: `design-library/sound-<registerId>.md` (YAML frontmatter for routing + markdown body for the prompt grammar). Machine index: `docs/research/sound-library.index.json` (regenerate via `python3 scripts/build-library-indexes.py`). **The index is the runtime read; this file is the primer.**
>
> Distinct from the live WebAudio drawers (`im-output-audio`, `game-feedback-author`): those SYNTHESISE sound in the browser from oscillators and envelopes. This library is about COMMISSIONED audio - real generated `.mp3` files written to `source/<branch>/audio/` and decoded into the same graph. The two coexist: synth for anything parametric per hit, generated clips for fixed characterful one-shots, narration and beds.

---

## 0. How this document is used

The `sound-orchestrator` walks a project, finds the surfaces that want sound (interface feedback, an ambient bed, a narrated passage, a title stinger, a game feedback layer), reads the project's committed aesthetic, and picks ONE register from this library. It then writes the per-surface enrichment node that downstream generators and audio drawers consume.

The decision flow at runtime:

1. Read `docs/research/sound-library.index.json`. **This is the hot path.** The index carries every `registerId`, its `name`, `category`, `role`, `oneLine`, `notForUseWhen`, `pairsPrototypes` and `sourceFile`. It is small enough to hold in context on every dispatch.
2. Match the project's `committedAesthetic` slug against the index `decisionTree`. Exact match only; no fuzzy matching. The tree's `default` is the pick, `alternatives[]` exist for variety across surfaces or when the default collides with a stated antiPattern.
3. Read the picked entry's `sourceFile` ONLY when actually composing a prompt. The per-entry file carries the sonic signature, the per-mode keyword lists, the paste-ready templates, the voice casting and the loudness defaults. It is never read speculatively.
4. Read THIS primer once per session at most, and only for fundamentals: mode grammar, voice ids, mixing doctrine, universal negatives. It carries no per-entry data.

Same contract as `photography-library.md`, `illustration-library.md`, `motion-scene-library.md` and `shader-library.md`. An agent that knows how to read one knows how to read all of them.

---

## 1. The three generation modes and their prompt grammar

Ground truth is the daemon renderer `_elevenlabs_generate_audio` in `editor/serve.py`. The `model` id selects the mode; all three return raw mp3 bytes in the response body, so the asset lands as a file with no polling step. Auth is the `xi-api-key` header, never Bearer. Commission through `POST /__asset_generate` with skill `audio-gen`, provider `elevenlabs`, the model id, the prompt, an `output` path under `source/<branch>/audio/`, and the per-mode `options` object.

### 1.1 SFX - `elevenlabs/sfx`, `POST /v1/sound-generation`

The prompt IS a description of one sound event. The grammar that works:

**material + action + space + duration.**

- **Material** - name the thing AND the surface it meets. Not "a click" but "a hard plastic key bottoming out on a foam pad". Not "a footstep" but "a leather sole on wet cobblestone". The generator has no idea what your object is made of unless you say so, and material is what separates a generic tick from a tick that belongs to your world.
- **Action** - the verb, with force. "Struck once", "scraped slowly", "released under tension", "brushed past". Force words are the difference between a tap and an impact.
- **Space** - the acoustic room. "In a small dry booth", "in a tiled stairwell with a long tail", "outdoors with no reflections", "close-mic, no room". Space is the single most under-specified ingredient and the one that makes a set of cues sound like one place instead of a bag of stock files.
- **Duration** - state the intended length in words as well as in `duration_seconds`, because the wording steers the envelope. "A short 200ms tick" renders differently from "a slow four second swell" even at the same requested length.

Keep it to ONE event unless you explicitly want a sequence. "A door latch closing" gives a latch. "A door latch closing, then footsteps walking away, then a distant car" gives a three-beat scene, which is the right call for a narrative moment and the wrong call for a UI tick you will trigger a hundred times.

Knobs in `options`:

- `duration_seconds` - up to **22**. Anything longer is a music or ambience job, not an SFX job. For interface cues, ask for 0.2 to 0.8; for impacts, 0.5 to 1.5; for whooshes and transitions, 1 to 3; for a one-shot ambience swell, 5 to 12.
- `prompt_influence` - 0 to 1. Low values let the model invent and give more organic, surprising results; high values hold it to the literal description. Use high influence for interface cues that must be exact and repeatable, low influence for texture and ambience where variation is a feature.
- `loop` - request a seamless loop. Essential for any ambient bed rendered as SFX rather than music. Without it you get a clip with an audible seam.
- `model_id`, `output_format` - pass through when the project pins them.

### 1.2 TTS - `elevenlabs/tts`, `POST /v1/text-to-speech/{voice_id}`

**The prompt IS the script.** There is no separate style field, so everything you want the delivery to do has to live in the words and the punctuation. Treat this as scriptcraft, not prompting.

- **Punctuation drives pacing.** A full stop is a real stop. A comma is a breath. Semicolons and dashes are read as short holds. Line breaks between sentences lengthen the gap. If a line reads too fast, add commas; if it reads choppy, remove them.
- **Ellipses buy hesitation.** "It was... not what we expected." lands the pause. Use sparingly; three ellipses in a paragraph makes the narrator sound uncertain about everything.
- **Capitals and italics do nothing reliable.** Do not shout in caps hoping for emphasis. Rewrite the sentence so the stressed word sits where a human would naturally stress it, or split it into its own short sentence.
- **Numbers and abbreviations should be spelled out** when the reading matters: "twenty twenty six" not "2026", "kilometres" not "km", unless you have checked how the voice handles it.
- **Write for the ear.** Short clauses. One idea per sentence. Read it aloud before committing it; if you stumble, the model will too.

Continuity across multiple clips is the thing most builds get wrong. When a narration is split into several files (one per section, one per scroll beat), each clip is generated independently and the prosody resets, so clip three starts cold and the seam is audible. Fix it with:

- **`previous_text`** - the text that immediately precedes this clip. The model uses it as context and carries the intonation contour forward.
- **`next_text`** - the text that follows. It stops the clip from landing on a hard falling cadence when the sentence actually continues.

Set both on every clip in a multi-clip narration. It costs nothing and it is the difference between a read and a stitched read.

Other knobs in `options`:

- **`voice_settings`** - an object with three levers that matter:
  - `stability` (0 to 1). Low means expressive and variable, and consecutive generations of the same line differ. High means flat, consistent and predictable. Narration that must match across a dozen clips wants high stability; a character line that wants life wants low. Around 0.5 is the neutral default.
  - `similarity_boost` (0 to 1). How hard the model clings to the reference timbre of the voice. High keeps the voice recognisably itself but can drag artefacts along with it; low lets the model smooth things out and drift off the voice's character.
  - `style` (0 to 1). Style exaggeration. It amplifies the voice's own performance tendencies. It also costs latency and destabilises long reads, so keep it low for narration and reach for it only when a line needs theatre.
- **`language_code`** - pin the language when the script is not English, or when an English script contains enough foreign proper nouns to confuse the model.
- **`seed`** - fixes the generation so a re-run reproduces the same take. Set it once a take is approved so a later rebuild does not silently reroll the performance.
- **`model_id`** - defaults to `eleven_multilingual_v2`, which is the right default for anything non-English or mixed.

### 1.3 MUSIC - `elevenlabs/music`, `POST /v1/music`

The prompt grammar is **genre + instrumentation + bpm + mood + loopability.**

- **Genre** - name a real one, and be narrow. "Ambient" is a hole. "Slow generative ambient in the Eno register, no percussion" is a brief.
- **Instrumentation** - list the instruments and, where it matters, how they are played. "Felted upright piano, bowed double bass, soft brushed kit." Naming instruments is the single highest-leverage token group in a music prompt.
- **BPM** - always give a number or a tight range. "Around 72 bpm" changes the whole result versus leaving it open.
- **Mood** - one or two words, no more. "Patient, unresolved."
- **Loopability** - say it explicitly if you need it: "loops seamlessly, no intro, no ending, no build". Music generators default to writing an arc with a beginning and an end, which is exactly wrong for a bed under a page.

Knobs in `options`: `music_length_ms` (default 30000), `model_id`, `output_format`.

**`/v1/music` is plan-gated on some ElevenLabs accounts.** A key that generates SFX and TTS happily can still return an error on the music endpoint. Treat a failed music generation as **non-fatal**: drop the bed, note it in the build's research or report file, and ship SFX and TTS. A sound design with no music bed is a legitimate outcome and often a better one. Never block a build on it, and never retry it in a loop.

---

## 2. The curated voice map

These are ElevenLabs premade-library voices, the same set `editor/voicekit.py` exposes as `CURATED_VOICES` through `GET /__voice/voices`. Cast from this table by default so the runtime voice endpoint and the baked audio agree on who is speaking.

| Voice | Voice id | Character | Cast for |
|---|---|---|---|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Calm, warm, neutral American female | The default narrator. Documentary, museum, product walkthrough, anything that must not draw attention to itself. |
| Adam | `pNInz6obpgDQGcFmaJgB` | Deep, grounded male | Trailers, authority, the voice that states the stakes. Cinematic titles, serious infrastructure marketing. |
| Antoni | `ErXwobaYiN019PkySvjV` | Well rounded, warm male | Product narration, onboarding, explainers. The friendly-competent register. |
| Domi | `AZnzlk1XvdvUeBnXmlld` | Strong, confident female | Energetic interface callouts, arcade announcements, anything with forward lean. |
| Elli | `MF3mGyEYCl7XYWbV9V6O` | Young, emotive female | Character voice, playful lines, cartoon delivery, a mascot that talks. |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Deep young male | Cinematic, game protagonist, first-person narration inside a world. |
| Arnold | `VR6AewLTigWG4xSOukaG` | Crisp, resonant male | Announcer, sports, scoreboard, the voice that calls a result. |
| Charlotte | `XB0fDUnXU5powFXDhCwa` | Measured, luxurious female | Museum hush, luxury, gallery label read aloud, slow and expensive. |

**Verify ids at cast time.** Call `GET https://api.elevenlabs.io/v1/voices` with the wired key before committing a voice, because the user's plan and library can differ from this table and a stale id renders as an error rather than a fallback. On a miss, fall back to **Rachel** (`21m00Tcm4TlvDq8ikWAM`), the daemon's `DEFAULT_VOICE_ID`, and say so in the build report rather than silently substituting.

**Delivery direction is phrased per register, never hardcoded.** The voice id picks a timbre; it does not pick a performance. Pace, warmth and pause length come from the register entry's `TTS delivery` keywords and from the script's punctuation. The same Rachel reads a museum label and a product tour, and they should not sound the same. Never bake a fixed `voice_settings` triple into a register and call it done; state the intent (slower, cooler, longer gaps) and let the entry's numbers be a starting point.

---

## 3. Loudness and mixing doctrine

Generated clips arrive at whatever level the model felt like. The build is responsible for the mix. Rules that apply to every register:

**Gain budget per layer.** Three buses under one master, in a fixed order of loudness: **voice loudest, then fx, then music bed.** The bed is furniture. If a listener can hum the bed after one visit, it is too loud. Concrete defaults per register live in each entry's `Loudness defaults` block as `masterGainBudget`, `fx`, `music`, `voice`, `duckMusicTo` and `duckReleaseMs`; the doctrine-level defaults are master `0.7`, voice `0.9`, fx `0.5`, music `0.22`.

**Duck the music under narration with ramps, never with jumps.** When a voice clip starts, ramp the music bus down to `duckMusicTo` over roughly 120ms, hold it for the length of the clip, then ramp back over `duckReleaseMs`. Use `linearRampToValueAtTime` on the gain param. A hard `gain.value =` assignment produces a click, which is the most common audible bug in a generated soundtrack.

**Put a limiter on the master.** A `DynamicsCompressorNode` with threshold around -1dB on the master path, after all buses. Nothing on the master path is ever allowed a gain above 1. This is the only thing standing between a stacked cue and a clipped output.

**Gate audio start on a user gesture.** Browsers block autoplay and an `AudioContext` created before a real gesture starts suspended. Create the context in the first pointerdown, keydown or touchstart handler, then ramp the master from 0 to its budget over about 200ms so the first sound fades in rather than snapping on. Everything the sound layer does must survive the context never being created at all.

**Ship a persistent mute affordance.** A visible, reachable control that is not buried in a settings pane, that persists its state, and that mutes everything by ramping the master to 0 rather than tearing the graph down. A soundtrack a visitor cannot switch off is a soundtrack they leave the page to escape.

**Respect `prefers-reduced-motion` for ambient beds.** The media query is about vestibular load, and a continuous droning bed sits in the same territory as continuous motion. When `reduce` is set: start muted with the graph alive, keep discrete confirmation cues available, and let the visitor opt in. Never auto-start an ambient loop under a reduced-motion preference.

---

## 4. Picking a register

The structured version of this lives in the generated index's `decisionTree`, keyed by prototype slug. This section is the reasoning behind those rows, for the cases the tree does not cover.

Start from the project's committed aesthetic and genre, not from the surface. A settings toggle in a horror piece and a settings toggle in a productivity tool are the same interaction and must not make the same sound.

Ask, in order:

1. **Is this a working tool or a place to be?** Tools want `ui-minimal-feedback` or `corporate-clean`: short, dry, quiet, no bed, no personality. Places want an ambient register: `cozy-ambient`, `natural-field-recording`, `museum-hush`, `lofi-focus`.
2. **Does the piece have a goal and a score?** Then it is a game, and it wants juice: `arcade-juice` for modern, `retro-console-chip` when the visual register is pixel-era, `playful-cartoon` when the world is drawn rather than rendered.
3. **Is there a voice?** If the piece explains, guides or remembers, the register must include a narration doctrine: `documentary-narration` for serious editorial, `museum-hush` for slow and curated, `corporate-clean` for product tours.
4. **What is the emotional temperature?** Warm and slow points at `cozy-ambient` and `natural-field-recording`. Cool and grand points at `cinematic-trailer`. Cool and wrong points at `tension-horror`. Neutral and busy points at `lofi-focus`.
5. **How loud is the visual register?** Loud visuals (y2k, memphis, acid, arcade) tolerate and want loud sound. Restrained visuals (hairline, cream humanist, swiss) want almost none, and the correct answer for a restrained brief is often three cues and silence.

When two registers both fit, pick the quieter one. Sound is the fastest thing in a prototype to overdo, and the failure is not subtle.

---

## 5. Universal negatives

These hold regardless of register.

- **No clipping.** Anything above 0dBFS on the master is a defect, not a style choice. Limiter always on.
- **No vocal music under narration.** Lyrics and speech compete for the same perceptual channel and both lose. If the bed has a voice in it, it cannot play under a voice.
- **No startle transients on routine interface ticks.** A hover, a toggle, a tab change: fast attack is fine, a sharp high-frequency spike is not. Reserve transient force for events that earned it.
- **At most one music bed per page.** Two beds cross-fading is one bed. Two beds playing is a bug.
- **No ambient loop that never varies.** A four second loop becomes audible as a loop within a minute. Either commission a longer bed, layer two loops of different lengths so the combination drifts, or let the bed rest periodically.
- **No narration that duplicates on-screen text verbatim.** A voice reading the headline you can already see is redundant and slightly insulting. Narration either says something the text does not, or it does not exist.
- **No sound on destructive confirmation without a distinct cue.** If delete and save sound the same, the sound layer is actively misleading.

---

## 6. Orchestrator integration notes

`sound-orchestrator` is the entry point. It:

1. Reads `docs/research/sound-library.index.json`, matches the project's committed aesthetic against `decisionTree`, and commits ONE register for the project (a second register is allowed only when a surface is genuinely a different world, for example a game embedded in an editorial page).
2. Commissions clips via the **`audio-gen`** skill through `POST /__asset_generate` (provider `elevenlabs`, model `elevenlabs/sfx` | `elevenlabs/tts` | `elevenlabs/music`), writing every file into **`source/<branch>/audio/`** with stable, descriptive names. Music failures are non-fatal per section 1.3.
3. Writes one **`pe_sound_<surfaceId>`** enrichment node per sound-bearing surface, carrying the picked `registerId`, the per-mode prompts it composed, the cast voice id, the loudness block, and the paths of the clips it commissioned.

Downstream readers of `pe_sound_<surfaceId>`:

- **`game-feedback-author`** reads it for the juice register, the impact and pickup cues, and the gain budget it applies to `_audioBus.fx`. It keeps its WebAudio synth path as the no-key fallback.
- **The narrative-experience ambient drawer** reads it for the bed, the room tone, and the narration clips the spine triggers and cross-fades.
- **`im-output-audio`** reads it for the register's palette and gain budget when an interactive piece's output medium is sound, so a synthesised output still lands in the same world as the commissioned clips.

The enrichment node is advisory data, not an instruction to the drawer about how to build its graph. Drawers own their own audio graph; the node tells them what it should sound like and how loud.

---

## Entry catalogue - moved to per-file sources

**Each of the 12 entries in this library is its own source-of-truth file in `design-library/sound-<registerId>.md`** - hand-editable, with YAML frontmatter + markdown sections. Editing one entry does not require scanning the rest of the library.

Where to find an entry:

- **List from the shell:** `ls design-library/sound-*.md`
- **Read one programmatically:** the `.index.json` companion file (`docs/research/sound-library.index.json`) maps every `registerId` to its source path, and orchestrators consume that index to route a surface to the right entry without scanning this primer.

To add a new entry, create `design-library/sound-<registerId>.md` with YAML frontmatter and a markdown body (use any existing entry as a template), then re-run `python3 scripts/build-library-indexes.py` to refresh the index.
