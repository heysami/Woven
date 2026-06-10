# Photography Library — research dossier for photography-orchestrator

This dossier exists so the `photography-orchestrator` subagent can scan a source HTML, find a slot that needs a photographic raster, and emit a prompt-enrichment node that downstream generators (Imagen, Flux, Nano Banana, Midjourney, DALL-E) will read. The orchestrator does not generate; it specifies. Everything below is written to be pasted, sliced, or recombined into a prompt — never as prose for a human reader.

## 1. Prompting fundamentals

### Anatomy of a strong photography prompt

Every paste-ready prompt should layer these seven ingredients in roughly this order. Order matters because most diffusion models weight earlier tokens more heavily.

1. **Subject** — who or what, with one specific attribute (age, posture, expression, garment, surface). Never "a person" — always "a woman in her 30s in a wool peacoat, half-turned away from the lens."
2. **Setting** — where, time of day, season, one prop. "On a wet asphalt sidewalk outside a 24-hour deli, 2 a.m., late November."
3. **Lighting** — direction, hardness, color temperature, and the single dominant source. "Single hard on-camera flash, fall-off into pure black."
4. **Camera + lens** — body or format, focal length, aperture. "Shot on a Leica M6 with a 28mm f/2 wide open."
5. **Film stock or post-processing** — the visual fingerprint. "Kodak Portra 400 push-pulled one stop, mild halation in the highlights."
6. **Mood** — one or two emotional words. "Unguarded, slightly suspicious."
7. **Composition + framing** — rule of thirds, low angle, 3/4 portrait, edge bleed. "Half-body, subject's eyes on upper third, negative space camera-right."

### Specific film stocks worth naming

Naming a real stock encodes ten unspoken choices (grain, color science, dynamic range, halation) in one token. Generators trained on Flickr/Unsplash strongly associate these:

- **Kodak Portra 400** — the default for warm, forgiving skin; gentle highlight roll-off; medium grain. Use for portraits, weddings, lifestyle.
- **Kodak Portra 160** — finer grain, slightly cooler, more pastel. Editorial portraits, daylight.
- **Kodak Ektar 100** — saturated, sharp, almost cinematic. Travel, product, landscape.
- **Kodak Gold 200** — warm consumer-grade, golden cast, nostalgia. Family, summer, suburban.
- **Kodak Tri-X 400** — punchy contrast black-and-white grain. Photojournalism, street, hip-hop.
- **Ilford HP5 400** — softer than Tri-X, longer tonal range. Documentary, fine art portrait.
- **Ilford Delta 3200** — chunky high-ISO grain. Nightclub, intimate, lo-fi.
- **Fujifilm Pro 400H** — cool greens and creamy whites. Fashion outdoors, weddings, pastel editorial.
- **Fujifilm Velvia 50** — hyper-saturated landscape stock; not for skin.
- **CineStill 800T** — tungsten-balanced motion-picture stock; signature red halation around highlights, neon-noir signature. Night street, neon, cinematic.
- **CineStill 50D** — daylight equivalent, fine grain, filmic color science.
- **Polaroid SX-70 / 600** — square, soft, milky, light leaks, color shift toward magenta. Diaristic, intimate, nostalgia.
- **Fuji Instax Mini** — modern instant, slightly cooler than Polaroid, signature white border.
- **Disposable / Fujifilm QuickSnap** — soft plastic-lens vignette, harsh on-camera flash, slight color shift, red-eye risk. Y2K and party.

### Specific lighting setups worth naming

- **Rembrandt** — key light at 45 degrees up and to the side, creates triangle of light under far eye. Portraiture canon.
- **Butterfly / Paramount** — key directly above and slightly in front, creates butterfly-shaped shadow under nose. Glamour, beauty, old Hollywood.
- **Split** — light hits exactly half the face. Dramatic, secretive, noir.
- **Loop** — between Rembrandt and split, small loop-shaped shadow off the nose. Standard portrait default.
- **Clamshell** — key above, fill below, both soft. Beauty, cosmetics.
- **Broad / short** — key on the side of the face turned toward camera (broad) or away (short). Short slims, broad widens.
- **On-camera direct flash** — hard frontal, blown highlights, crushed background, slight harshness. Y2K, Goldin, Gilden, club, party.
- **Bounced flash** — softer, ceiling-fill, ambient warmth. Editorial behind-the-scenes.
- **Ring flash** — uniform circular catchlight in the eye, almost shadowless. Beauty, fashion, medical, late-90s glam.
- **Golden hour** — 30–60 min after sunrise / before sunset, warm amber, long shadows, low contrast. Lifestyle, cinematic, wedding.
- **Blue hour** — 20–30 min after sunset, indigo sky + tungsten warmth, mixed color temperatures. Urban, cinematic, melancholy.
- **Overcast / soft box sky** — even, shadowless, low contrast, slightly cool. Editorial, lookbook, documentary.
- **Harsh midday** — top-down, deep shadows under brows, slight squint. Editorial summer, fashion outdoor.
- **Neon ambient** — colored ambient light, mixed temperatures, signature pink/cyan/magenta cast. Night street.
- **Candle / single tungsten** — warm 2200K, falloff into black, low motion blur risk. Intimate, fine-art.
- **Practicals only** — only light visible in the scene (lamp, screen, sign). Cinematic naturalism.
- **Window light** — soft directional, often north-facing, used for painterly portraits. Vermeer, editorial portrait.

### Lens vocabulary worth naming

- **14mm / 16mm ultra-wide** — landscape, architecture, environmental portrait with distortion.
- **24mm wide** — environmental street, group shots, journalism.
- **28mm f/2** — Gilden, classic street reportage, slight distortion at edges.
- **35mm f/1.4** — Tillmans, the documentary humanist standard, close to human eye.
- **50mm f/1.4** — the "normal" lens; flattering, undistorted.
- **85mm f/1.4 / 85mm f/1.8** — the portrait lens; flattering compression, soft background.
- **100mm macro** — product, food, jewelry, beauty close-ups.
- **135mm f/2** — long portrait, isolating subject, fashion editorial.
- **Medium format 80mm (Hasselblad / Pentax 67)** — Sorrenti, fashion canon, three-dimensional rendering, deep tonality.
- **Anamorphic 40mm / 50mm / 75mm** — oval bokeh, horizontal lens flares, 2.39:1 cinematic wide.
- **Fisheye 8mm** — skate, music, party distortion.
- **Tilt-shift 90mm** — selective focus, miniature effect, architectural.

### Cliches to AVOID

These phrases are tells that the prompt was written by someone who doesn't know photography. They reduce realism because the training data associates them with generic AI slop:

- "professional photography"
- "high quality"
- "8k" / "4k" / "ultra HD"
- "ultra realistic" / "hyper realistic" / "photorealistic"
- "award winning"
- "masterpiece"
- "trending on artstation"
- "stunning"
- "beautiful"
- "highly detailed"
- "depth of field" (use an aperture instead: "f/1.4")
- "bokeh" alone (use "85mm wide-open bokeh" or "anamorphic oval bokeh")
- "cinematic" by itself (replace with a named film, director, or DP: "Roger Deakins lit", "shot on Arri Alexa", "Portra 400 grain")

### Universal negative-prompt list

These go in every photography prompt regardless of style, unless the brief specifically calls for one of them:

`no watermark, no stock-photo logo, no shutterstock, no getty images caption, no text overlay, no caption, no extra fingers, no deformed hands, no fused fingers, no plastic skin, no airbrushed skin, no over-smoothed skin, no waxy skin, no AI-generated face symmetry, no centered subject (unless directed), no smiling-at-camera (unless directed), no over-saturated, no over-sharpened, no HDR halos, no over-processed, no Instagram filter, no VSCO preset look, no generic stock-photo composition, no double face, no extra limbs, no glitched eyes, no asymmetric pupils, no melted earrings, no warped jewelry, no warped text on garments`

### Universal positive-baseline — ALWAYS append "color graded" (load-bearing)

**Every photography prompt the orchestrator composes ends with the keyword `color graded`.** Non-negotiable. Reason: a photograph that follows the brief's design system / palette / theme can still ship looking flat, washed, or "uncooked" — generators that don't know to color-grade default to a neutral RAW look that feels amateur next to actual editorial work. The `color graded` token is a small lever that consistently pushes the output toward "this looks like someone post-processed it for publication" instead of "this is a straight camera dump."

How to use:

- **Append verbatim** to every prompt's tail, after the named style and before the universal-negatives. The phrase is `color graded` — two words, lowercase, no hyphen, no modifier required.
- **Pair with a grade direction when the style supplies one.** Many §2 entries declare a specific grade in `filmStockOrPostProcessing` (e.g. "teal-and-orange color grade", "cool muted color grade", "warm shadow tint", "cross-processed E6 in C-41"). When present, use BOTH the style's specific grade AND the universal `color graded` anchor — they reinforce.
- **When the brief is restrained** (cream-humanist, restrained-AI-marketing, warm-restraint): use `subtly color graded` or `gently color graded` so the polish reads as quiet, not theatrical. The token still goes in — restrained briefs need polish too, just calibrated lower.
- **When the brief is theatrical** (editorial-magazine, y2k-memphis-loud, vaporwave, cyberpunk): use `boldly color graded` or `aggressively color graded with [palette]` and name the palette anchor when known.

Common pairings for quick reference:

| Brief register | Recommended tail |
|---|---|
| Restrained / minimal | `subtly color graded` |
| Editorial / standard | `color graded` |
| Cinematic / mood-led | `cinematically color graded` (often with teal-orange or muted-warm-shadow) |
| Loud / theatrical / era-specific | `boldly color graded with <palette>` |
| Documentary / archival | `restored and color graded` (when the brief allows; otherwise plain `color graded`) |

Anti-pattern: do NOT prompt for `"unedited"`, `"raw"`, `"straight out of camera"`, `"SOOC"`, `"no post-processing"` even when the brief reads documentary or archival. The orchestrator's job is to ship polished work; the documentary register comes from composition + lighting + film stock keywords, not from forfeiting the grade.

---

## Entry catalogue — moved to per-file sources

**Each of the 54 entries in this library is its own source-of-truth file in `design-library/photo-<entryId>.md`** — hand-editable, with YAML frontmatter + markdown sections. Editing one entry doesn't require scanning the rest of the library.

Where to find an entry:

- **Browse the System tab → Design library** in the editor. The Photography bucket lists all entries as cards with image-sample slots.
- **List from the shell:** `ls design-library/photo-*.md`
- **Read one programmatically:** the `.index.json` companion file (e.g. `docs/research/photography-library.index.json`) maps every entry id to its source path, and orchestrators consume that index to route a slot to the right entry without scanning the big primer.

To add a new entry, create a new `design-library/photo-<entryId>.md` with YAML frontmatter and markdown body (use any existing file as a template), then re-run `python3 scripts/build-library-indexes.py` to refresh the index. That script reads the prototype directory; the primer below is for principles only.

## 3. Style-pick decision tree

> **Normalised schema (read this before parsing the table below).** Every entry conforms to:
>
> - **Column 1 — `Prototype slug`** — kebab-case slug from prototype.md (recipes, aesthetics, styles, shells). Orchestrators match their `committedAesthetic` envelope field against this. Exact-match only; no fuzzy matching.
> - **Column 2 — `Default`** — the PRIMARY photography `styleId` (kebab-case, matches an entry in §2 above). Orchestrator uses this by default unless overridden by `explicitStylePicks[slotId]` or by an antiPattern conflict.
> - **Column 3 — `Alternatives`** — comma-separated additional `styleId`s. Orchestrator picks from these when (a) the default conflicts with an antiPattern, OR (b) the project has multiple photographic slots and the orchestrator wants variety across them.
> - **Column 4 — `Notes`** — advisory prose; orchestrator may use this to weigh the default vs alternatives but does NOT need to parse it programmatically.
>
> The same schema is mirrored in `illustration-library.md §3` and `material-library.md §7` so an orchestrator that reads one knows how to read all three.

When the source HTML has committed to a prototype.md aesthetic, the orchestrator maps that aesthetic to compatible photography styles. The first column is the prototype slug, the second column lists photography `styleId`s, the third explains the bias.

| Prototype aesthetic / style | Photography styles that fit | Notes |
|---|---|---|
| recipe-editorial-magazine | helmut-newton-flash, tillmans-candid, sorrenti-grain, leibovitz-key-light, magnum-monochrome, shore-color, goldin-diary, weingart-staged, environmental-portrait, vivian-maier-square | The editorial magazine recipe is a catch-all for serious photography. Pick by topic warmth: Newton/Sorrenti for cool, Leibovitz/Tillmans for warm. |
| recipe-bento-marketing | apple-clean-studio, high-key-beauty, leibovitz-key-light, clean-tech-lifestyle | Bento panels need product-clarity photography. Studio precision over candid. |
| recipe-restrained-ai-marketing | clean-tech-lifestyle, apple-clean-studio, cereal-lifestyle, cos-lookbook, laundry-light-lookbook, tillmans-candid | Restrained AI marketing rejects gloss; prefers daylight, plaster walls, and quietly capable subjects. |
| recipe-warm-restraint | aesop-apothecary, kinfolk-warm-minimal, cereal-lifestyle, sorrenti-grain (monochrome), shore-color, environmental-portrait, seventies-soft-grain | The luxury-apothecary recipe. Warm, slow, daylight, single subject, no flash. |
| aesthetic-y2k-futurism | y2k-flash-glam, genz-flash-disposable, y2k-halftone, frutiger-aero-product, chrome-hearts-editorial, vaporwave-still-life | Y2K wants hard flash and chrome. Halftone for print-look. Frutiger-Aero for product. |
| aesthetic-y2k-memphis-loud | y2k-halftone, y2k-flash-glam, surreal-still-life, eighties-cocaine-glam, skate-zine | Loud Memphis wants oversaturated single hues, hard flash, halftone graphics overlay. |
| aesthetic-frutiger-aero | frutiger-aero-product, magic-glow, high-key-beauty, dreamy-haze | Glossy bright sky-blue-and-grass-green, bokeh, water droplets, optimism. |
| aesthetic-cottagecore | seventies-soft-grain, kinfolk-warm-minimal, environmental-portrait, fantasy-glow, dreamy-haze | Soft golden warm grain. Window light. Natural texture. No urban subjects. |
| aesthetic-dark-academia | sorrenti-grain (monochrome), goldin-diary, magnum-monochrome, vivian-maier-square, environmental-portrait | Cool monochrome with warm tungsten accents. Books, candlelight, single window. |
| aesthetic-vaporwave | vaporwave-still-life, circuit-bent-glitch, y2k-halftone, surreal-still-life, night-flash-noir | Pastel pink-cyan, plaster busts, glitches, CRT glow, neon street. |
| aesthetic-dreamcore | dreamy-haze, fantasy-glow, magic-glow, vaporwave-still-life, surreal-still-life, goldin-diary | Soft halation, pastel grade, dissolving edges, slight surreal scale. |
| aesthetic-coastal-grandmother | kinfolk-warm-minimal, cereal-lifestyle, nyt-cooking-food, seventies-soft-grain, sorrenti-grain | Warm linen and stoneware. Daylight. Soft cream palette. Slow activity. |
| style-cream-humanist | kinfolk-warm-minimal, cereal-lifestyle, aesop-apothecary, environmental-portrait, sorrenti-grain | Warm-paper editorial. Slow daylight portraiture. Apothecary still life. |
| style-serif-warm-paper | shore-color, magnum-monochrome, salgado-contrast, sorrenti-grain, vivian-maier-square, environmental-portrait | Newspaper-of-record editorial. Tonally serious. Often archival or documentary. |
| style-glassmorphism | apple-clean-studio, frutiger-aero-product, high-key-beauty, magic-glow | Glass and gloss product. Bright, sky, optimistic. |
| style-liquid-glass | frutiger-aero-product, apple-clean-studio, magic-glow, vaporwave-still-life | Reflective wet gloss. Saturated single hue. |

Additional implicit mappings:

| Prototype slug | Photo styles |
|---|---|
| recipe-newspaper-of-record | magnum-monochrome, salgado-contrast, vivian-maier-square, shore-color |
| recipe-brutalist-web | gilden-flash-street, skate-zine, y2k-halftone, circuit-bent-glitch |
| aesthetic-cyberpunk | night-flash-noir, cinematic-street-anamorphic, circuit-bent-glitch, chrome-hearts-editorial |
| aesthetic-corporate-grunge | y2k-halftone, skate-zine |
| aesthetic-vector-hands-up / acid-design / acid-graphics | y2k-halftone, y2k-flash-glam, surreal-still-life |
| aesthetic-angelcore / fairycore | dreamy-haze, fantasy-glow, magic-glow, seventies-soft-grain |
| recipe-devtools-marketing | clean-tech-lifestyle, leibovitz-key-light, apple-clean-studio, environmental-portrait |
| recipe-readcv | tillmans-candid, shore-color, environmental-portrait, laundry-light-lookbook |

---

## 4. Universal negative-keyword list

These are the negatives every photography prompt should include unless the brief specifically asks for one of these qualities. Listed in suggested prompt-paste order:

```
no watermark, no stock-photo logo, no shutterstock signature, no getty images caption,
no text overlay, no caption, no watermark text, no logo bug,
no extra fingers, no fused fingers, no missing fingers, no extra hands, no warped hands,
no deformed face, no asymmetric pupils, no glitched eyes, no melted teeth,
no plastic skin, no airbrushed skin, no over-smoothed skin, no waxy skin, no doll-skin,
no perfect AI-generated face symmetry,
no centered subject (unless directed), no rule-of-thirds violation away from intent,
no smiling-at-camera (unless directed by brief),
no over-saturated, no HDR halos, no aggressive sharpening, no over-processed,
no Instagram filter, no obvious VSCO preset, no Lightroom mobile preset look,
no generic stock-photo composition, no LinkedIn-headshot look,
no "professional photography" tag-style render, no "high quality 8k" generic AI look,
no double face, no twin face, no extra limb, no extra leg, no fused limb,
no warped jewelry, no melted earrings, no warped text on garments, no warped logos,
no over-bokehed background (unless directed), no background blur covering whole scene,
no random anachronistic objects in background, no out-of-period props
```

Style-specific entries in §2 also list `avoidKeywords` — those are additional negatives the orchestrator should prepend when that style is selected.

---

## 5. Implementation notes for the orchestrator

### 5.1 Style-pick algorithm when the brief is ambiguous

When the source HTML hasn't committed to a clear prototype aesthetic, the orchestrator falls back to this decision flow:

1. **Subject classification.** Detect from the slot's neighboring DOM and alt text: is the slot for `product`, `person`, `food`, `environment`, `still-life`, `editorial`, or `BTS`?
2. **Tone classification.** Scan the page for adjective cues: `premium`, `restrained`, `loud`, `playful`, `serious`, `nostalgic`, `kinetic`, `modern`, `slow`. Map to a tone axis (warm-cool, restrained-loud, fast-slow).
3. **Era cue.** If the source explicitly references a decade (y2k, 70s, mid-century), bias toward era-coded styles.
4. **Default fallback.** For `editorial` + `restrained` + `modern` with no era cue, the orchestrator defaults to `cos-lookbook` for fashion, `apple-clean-studio` for product, `leibovitz-key-light` for person, `aesop-apothecary` for still-life, `nyt-cooking-food` for food.
5. **Confidence threshold.** If two styles tie, the orchestrator picks the safer one (lower risk of generating brand-inappropriate imagery). "Safer" means: `magnum-monochrome` is safer than `gilden-flash-street`; `kinfolk-warm-minimal` is safer than `goldin-diary`.

### 5.2 Chaining multiple styles

The orchestrator can chain two styles when the brief explicitly calls for a hybrid look. The chaining rule is:

- **Primary** style supplies the camera, lens, film stock, and lighting setup.
- **Secondary** style supplies the post-processing or stylistic overlay.

Example legal chains:

- `genz-flash-disposable` (primary) + `y2k-halftone` (secondary post-processing) — flash editorial, then halftoned. Use for Y2K zine covers.
- `magnum-monochrome` (primary) + `salgado-contrast` (secondary tonality push) — documentary, biblical contrast.
- `cos-lookbook` (primary camera and pose) + `sorrenti-grain` (secondary monochrome film treatment) — modern lookbook printed as Sorrenti.
- `apple-clean-studio` (primary) + `magic-glow` (secondary overlay) — premium beauty with glow bloom.

Illegal chains (the orchestrator must refuse):

- Any documentary style + any fashion-flash style — the truth-claim of documentary is broken by editorial post.
- More than two styles — model coherence breaks down past two.

When chaining, the prompt template is:

```
<primary subject + setting + lighting + camera + lens>,
<primary film stock or tonal treatment>,
treated with <secondary post-processing overlay>,
<combined mood>,
<combined negative prompts>
```

### 5.3 Video / animated raster

Yes, the same style library serves as the art-direction layer for video prompts (Runway, Pika, Sora). The orchestrator switches mode when the slot is `video`:

- The `cameraOrLens` key swaps from still cameras to cinema camera equivalents: replace `Leica M6` with `Arri Alexa`, replace `Canon 5D` with `Sony FX3`, replace `Hasselblad` with `RED Komodo`.
- Add cinema-specific tokens: `24fps`, `shallow DOF rack focus`, `slow dolly-in`, `handheld`, `static lock-off`.
- Aspect ratio defaults to `2.39:1` for cinematic styles, `16:9` for lookbook, `9:16` for vertical social.
- The `mood` keyword carries directly; the `filmStockOrPostProcessing` becomes the color grade reference (e.g. "graded like CineStill 800T" stays valid).
- One additional negative for video: `no AI-morphing artifacts, no frame-to-frame flicker, no morphing limbs between frames`.

### 5.4 Generator-specific notes

The same enriched prompt is read by different downstream generators. The orchestrator emits a single prompt and lets each provider's adapter layer rewrite it. Key per-generator biases:

- **Midjourney** — responds best to comma-separated keyword stacks; expects `--ar`, `--stylize`, `--style raw`. Style raw is essential for photoreal.
- **Flux (Pro / Dev / Schnell)** — responds best to natural-language paragraphs, not keyword stacks. The orchestrator should compose paragraph-form for Flux.
- **Imagen 3 / 4** — responds well to both, prefers explicit lens and lighting tokens. Less responsive to photographer names; substitute the style description.
- **Nano Banana (Gemini)** — strong on subject editing, weaker on stylistic transfer. Use shorter prompts with explicit composition.
- **DALL-E 3 / GPT-Image** — long natural-language prompts; will resist explicit named photographers unless the style is described in plain words.

### 5.5 Slot-type to style category mapping

Quick reference for the orchestrator's first-pass:

| Slot intent (from DOM) | Default category | Default styleId |
|---|---|---|
| Hero image, fashion brand | editorial-fashion | cos-lookbook or helmut-newton-flash |
| Hero image, tech product | product | apple-clean-studio |
| Hero image, lifestyle / SaaS | lifestyle | clean-tech-lifestyle |
| Founder portrait, About Us | editorial-fashion or documentary | leibovitz-key-light or environmental-portrait |
| Recipe / food card | food | nyt-cooking-food |
| E-comm product tile | product | apple-clean-studio (clean) or aesop-apothecary (warm) |
| Editorial story image | editorial-fashion or documentary | tillmans-candid or magnum-monochrome |
| Behind-the-scenes feature | BTS | — |
| Music / streaming card art | conceptual or street | night-flash-noir or vaporwave-still-life |
| Heritage brand image | archival or documentary | vivian-maier-square |
| Beauty product hero | beauty | high-key-beauty or magic-glow |
| Beauty editorial story | beauty or editorial-fashion | dreamy-haze or sorrenti-grain |
| News / journalism | documentary | magnum-monochrome |
| Hospitality, slow travel | lifestyle | cereal-lifestyle or kinfolk-warm-minimal |
| Fragrance | beauty or editorial-fashion | sorrenti-grain or magic-glow or fantasy-glow |
| Game key art | conceptual | fantasy-glow or circuit-bent-glitch |

### 5.6 The orchestrator must NOT emit

- A prompt without at least subject + lighting + camera. Any one of these missing produces inconsistent generation.
- Two photographer names from competing schools (e.g. "Helmut Newton meets Wolfgang Tillmans" — these cancel each other).
- The cliche tells in §1 (`8k`, `professional photography`, `ultra realistic`).
- Period-incorrect props (e.g. iPhone in a 1970s style, sneakers in a Newton 1980s editorial).
- Trademarked logos or visible brand identifiers — generators refuse or hallucinate badly.

### 5.7 Output shape the orchestrator writes downstream

The enrichment node downstream image generators consume is roughly:

```yaml
photographyPrompt:
 positive: |
 <natural-language paragraph prompt, 60-100 words>
 negative: |
 <comma-separated negative keyword list from §4 + style-specific avoidKeywords>
 meta:
 styleId: <kebab slug>
 secondaryStyleId: <kebab slug or null>
 aspectRatio: <e.g. 2.39:1, 4:5, 1:1, 9:16>
 aperture: <e.g. f/1.4, f/8>
 intent: <hero | product | portrait | still-life | editorial | bts | food>
 confidence: <0.0-1.0>
```

The `confidence` field is set lower (under 0.6) when the orchestrator had to guess between two roughly equally compatible styles; downstream the generator may then produce two candidates instead of one for human selection.

---

End of dossier.
