# Clean tech-lifestyle hero (photo)

**Tag:** photo-clean-tech-lifestyle  ·  **Era:** current  ·  **Category:** lifestyle  ·  **Role affinity:** hero, section, portrait

Subject mid-action with the product, natural ambient light.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/photography-library.md`](../docs/research/photography-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- styleId: clean-tech-lifestyle
  name: Clean tech-lifestyle hero
  era: current
  category: lifestyle
  visualSignatures:
    - Subject mid-action with the product, natural ambient light
    - Modernist or biophilic interior context
    - Slight cool tone, faithful color
    - Hands-and-product detail or wide environmental shot
    - Soft natural daylight, no hard shadow, neutral palette
  promptKeywords:
    primary: [subject in modernist interior with product, mid-action, hands and product detail, natural ambient]
    lighting: [soft window daylight, even ambient, no hard shadow]
    cameraOrLens: [Sony A7R, 35mm at f/4]
    filmStockOrPostProcessing: [faithful slightly-cool color, retained product detail, no grain]
    mood: [capable, modern, present]
    avoidKeywords: [moody, hard flash, kinetic, gritty]
  namedReferences:
    photographers: [Apple lifestyle in-house, Patagonia worn-wear lifestyle, Notion / Linear marketing]
    magazines: [Monocle product, Wallpaper* tech]
    movements: [contemporary tech-marketing lifestyle]
    brands: [Apple, Linear, Notion, Arc Browser, Rivian]
  examplePromptTemplate: |
    A person in a soft wool sweater seated at a pale ash desk in a modernist office with a single large plant camera-right, hands resting on a sleek laptop, mid-thought looking just past the camera. Soft window daylight from camera-left, even ambient, no hard shadow. Shot on a Sony A7R with a 35mm at f/4, faithful slightly-cool color, retained product detail and wool texture. Capable, modern, present mood. Clean tech-lifestyle hero photograph.
  whenToUse: SaaS marketing hero, premium tech product pages, modern lifestyle apps, productivity-tool marketing.
  pairsWith:
    prototypeStyles: [recipe-devtools-marketing, recipe-restrained-ai-marketing, recipe-bento-marketing, recipe-linear-product-ui]
  notForUseWhen: Editorial mood, fast fashion, anything kinetic.

---

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
| recipe-editorial-magazine | helmut-newton-flash, tillmans-candid, sorrenti-grain, leibovitz-key-light, magnum-monochrome, shore-color, goldin-diary, weingart-staged, environmental-portrait, vivian-maier-square, backstage-fashion | The editorial magazine recipe is a catch-all for serious photography. Pick by topic warmth: Newton/Sorrenti for cool, Leibovitz/Tillmans for warm. |
| recipe-bento-marketing | apple-clean-studio, high-key-beauty, leibovitz-key-light, clean-tech-lifestyle | Bento panels need product-clarity photography. Studio precision over candid. |
| recipe-restrained-ai-marketing | clean-tech-lifestyle, apple-clean-studio, cereal-lifestyle, cos-lookbook, laundry-light-lookbook, tillmans-candid | Restrained AI marketing rejects gloss; prefers daylight, plaster walls, and quietly capable subjects. |
| recipe-warm-restraint | aesop-apothecary, kinfolk-warm-minimal, cereal-lifestyle, sorrenti-grain (monochrome), shore-color, environmental-portrait, seventies-soft-grain | The luxury-apothecary recipe. Warm, slow, daylight, single subject, no flash. |
| aesthetic-y2k-futurism | y2k-flash-glam, genz-flash-disposable, y2k-halftone, frutiger-aero-product, chrome-hearts-editorial, vaporwave-still-life | Y2K wants hard flash and chrome. Halftone for print-look. Frutiger-Aero for product. |
| aesthetic-y2k-memphis-loud | y2k-halftone, y2k-flash-glam, surreal-still-life, bowie-rock-glamour, eighties-cocaine-glam, skate-zine | Loud Memphis wants oversaturated single hues, hard flash, halftone graphics overlay. |
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
| recipe-newspaper-of-record | magnum-monochrome, salgado-contrast, vivian-maier-square, shore-color, war-photojournalism |
| recipe-brutalist-web | gilden-flash-street, skate-zine, y2k-halftone, circuit-bent-glitch |
| aesthetic-cyberpunk | night-flash-noir, cinematic-street-anamorphic, circuit-bent-glitch, chrome-hearts-editorial |
| aesthetic-corporate-grunge | archival-found-photo, y2k-halftone, backstage-fashion, skate-zine |
| aesthetic-vector-hands-up / acid-design / acid-graphics | y2k-halftone, y2k-flash-glam, surreal-still-life, bowie-rock-glamour |
| aesthetic-angelcore / fairycore | dreamy-haze, fantasy-glow, magic-glow, seventies-soft-grain |
| recipe-devtools-marketing | clean-tech-lifestyle, leibovitz-key-light, apple-clean-studio, environmental-portrait |
| recipe-readcv | tillmans-candid, shore-color, archival-found-photo, environmental-portrait, laundry-light-lookbook |

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
- `war-photojournalism` + any commercial style — never.
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
| Recipe / food card | food | nyt-cooking-food (bright) or bon-appetit-food (moody) |
| E-comm product tile | product | apple-clean-studio (clean) or aesop-apothecary (warm) |
| Editorial story image | editorial-fashion or documentary | tillmans-candid or magnum-monochrome |
| Behind-the-scenes feature | BTS | backstage-fashion |
| Music / streaming card art | conceptual or street | night-flash-noir or vaporwave-still-life |
| Heritage brand image | archival or documentary | archival-found-photo or vivian-maier-square |
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
```

## When NOT to use

Editorial mood, fast fashion, anything kinetic.

## Pairs with (prototype slugs)

- `recipe-devtools-marketing`
- `recipe-restrained-ai-marketing`
- `recipe-bento-marketing`
- `recipe-linear-product-ui`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1397–1618 of `docs/research/photography-library.md`. Full index: `docs/research/photography-library.index.json`._
