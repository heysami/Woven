# Image-generation playbook

Prompt-shaping playbook for the `generate-image` skill and any prompt the
visual / illustration / photography orchestrators author for it.

## When to use

- Generate a new bitmap image (concept art, product shot, hero, cover)
- Generate a new image using one or more reference images for style, composition, mood
- Edit an existing image (inpainting, lighting / weather change, background replacement, object removal, compositing)
- Produce many assets or variants for one task

## When not to use

- Extending or matching an existing SVG / vector icon set, logo system, or illustration library inside the repo - prefer the `svg-gen` skill or editing the source vector directly
- Simple shapes, diagrams, wireframes, or icons better produced as code (`svg-gen`, `viz`, `html-page`, `shader`)
- A small project-local edit when the source file already exists in an editable native format
- Any task where deterministic code-native output beats a generated bitmap

## Decision tree

Think about two separate axes:

1. **Intent** - new image or edit of an existing image?
2. **Execution strategy** - one asset or many?

### Intent

- Modifying an existing image while preserving parts of it → **edit**.
- Images supplied only as references for style / composition / mood / subject guidance → **generate** with references.
- No images supplied → **generate**.
- If the user wants to edit a local file that isn't already in the conversation context, load it first so the model can see it; otherwise the edit can't anchor to anything concrete.

### Execution strategy

- Many distinct assets → issue one image-gen call per asset. Do NOT use the model's `n` parameter as a substitute for separate prompts; `n` only makes variants of one prompt.
- Variants of one asset → use `n` (or repeated calls with the same prompt + different seeds).
- Edits → save non-destructively by default (versioned sibling filename like `hero-v2.png`) unless the user explicitly asked for in-place replacement.

Assume new image unless the user clearly asks to change an existing one.

## Use-case taxonomy

Classify each request into one of these buckets. Keep the slug consistent
across prompts and downstream references - orchestrators that read this file
use the slug to look up per-bucket tips and templates.

### Generate

- `photorealistic-natural` - candid / editorial lifestyle with real texture and natural lighting
- `product-mockup` - product / packaging shots, catalog imagery, merch concepts
- `ui-mockup` - app / web interface mockups and wireframes (specify fidelity)
- `infographic-diagram` - diagrams / infographics with structured layout and text
- `scientific-educational` - classroom explainers, scientific diagrams, learning visuals with label + accuracy constraints
- `ads-marketing` - campaign concepts and ad creatives with audience, brand position, scene, exact tagline
- `productivity-visual` - slide, chart, workflow, data-heavy business visuals
- `logo-brand` - logo / mark exploration, vector-friendly
- `illustration-story` - comics, children's book art, narrative scenes
- `stylized-concept` - style-driven concept art, 3D / stylized renders
- `historical-scene` - period-accurate world-knowledge scenes

### Edit

- `text-localization` - translate / replace in-image text, preserve layout
- `identity-preserve` - try-on, person-in-scene; lock face / body / pose
- `precise-object-edit` - remove / replace a specific element (including interior swaps)
- `lighting-weather` - time-of-day / season / atmosphere changes only
- `background-extraction` - transparent background / clean cutout (see [Transparent backgrounds](#transparent-backgrounds))
- `style-transfer` - apply reference style while changing subject / scene
- `compositing` - multi-image insert / merge with matched lighting / perspective
- `sketch-to-render` - drawing / line art to photoreal render

## Shared prompt schema

Use the following labeled spec as scaffolding. Lines are scaffolding, not a
closed schema - drop the ones that don't help, add a short extra labeled line
when it materially improves clarity.

```text
Use case: <taxonomy slug>
Asset type: <where the asset will be used>
Primary request: <user's main prompt>
Input images: <Image 1: role; Image 2: role>     (only when supplied)
Scene/backdrop: <environment>
Subject: <main subject>
Style/medium: <photo / illustration / 3D / etc>
Composition/framing: <wide / close / top-down; placement>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Materials/textures: <surface details>
Text (verbatim): "<exact text>"
Constraints: <must keep / must avoid>
Avoid: <negative constraints>
```

Notes:

- `Asset type` and `Input images` are prompt scaffolding; they don't map to
  any API flag in any image model. They make the spec clearer for the model
  and for future-you when you iterate.
- `Scene/backdrop` is the visual setting in the prompt. It is NOT the same as
  the `background` parameter some models expose for output transparency.

## Specificity policy

Tune augmentation to how specific the user's prompt already is.

- **Already specific and detailed** → normalize into a clean labeled spec
  without adding creative requirements. Do not invent extra characters,
  palette, slogans, or story beats.
- **Generic** → tasteful augmentation is allowed when it materially improves
  output quality.

### Allowed augmentation for generic prompts

- Composition / framing hints
- Polish level or intended-use hints (ad, UI mockup, infographic)
- Practical layout guidance (negative space for copy, mobile vs desktop frame)
- Reasonable scene concreteness that supports the stated request

### NOT allowed

- Extra characters, props, or objects not implied by the request
- Brand names, slogans, palettes, or narrative beats not implied
- Arbitrary side-specific placement unless the surrounding layout supports it

Treat the recipes in [Sample prompt recipes](#sample-prompt-recipes) as
fully-authored examples, not as the default amount of augmentation to apply
to every request.

## Composition, lighting, materials

- Specify framing and viewpoint (close-up / wide / top-down) and placement
  only when it materially helps.
- Call out negative space when the asset clearly needs room for UI or copy.
- Avoid left / right layout decisions unless the user or surrounding layout
  supports them.
- For people, describe body framing, scale, gaze, and object interactions
  when they matter (`full body visible`, `looking down at the book`,
  `hands naturally gripping the handlebars`).
- For photorealism: use photography language (lens, lighting, framing), call
  for real texture (pores, wrinkles, fabric wear, material grain), and
  include the word `photorealistic` directly when that's the goal.

## Constraints and invariants

- State what must NOT change (`keep background unchanged`).
- For edits, say `change only X; keep Y unchanged` and repeat invariants on
  every iteration to reduce drift.
- Add negative constraints (`no logos`, `no watermark`, `no text unless
  requested`) explicitly - image models default to "more, please" otherwise.

## Text in images

- Put literal text in quotes or ALL CAPS and specify typography (font style,
  size, color, placement).
- Spell uncommon words letter-by-letter if accuracy matters.
- Require verbatim rendering and no extra characters.
- Dense text (infographics, multi-font layouts, legends, axes, footnotes)
  benefits from the model's higher quality setting if one is exposed.

## Input images and references

- Don't assume every supplied image is an edit target.
- Label each image by index and role (`Image 1: edit target`,
  `Image 2: style reference`).
- Style / composition / mood references with no instruction to modify them
  → treat as generation with references.
- "Preserve this image while changing parts" → treat as edit.
- For compositing, describe how the images interact (`place the subject from
  Image 2 into Image 1`).

## Iterate deliberately

- Start with a clean base prompt; then make small single-change edits.
- Re-specify critical constraints when you iterate - image models drop them
  silently between turns.
- Prefer one targeted follow-up at a time over rewriting the whole prompt.

## Transparent backgrounds

The right path depends on what the chosen model supports. There's no single
correct workflow - pick by model and by subject complexity.

1. **Model supports `background=transparent` natively** (e.g., gpt-image-1.5,
   FLUX in some configurations, recraft-v3 with the `image_type=png` flag) →
   request transparent output directly. Cleanest path for hair, fur, glass,
   smoke, liquids, translucent materials, reflective objects, soft shadows.
2. **Model doesn't support native transparency** (gpt-image-2 today) →
   generate on a flat solid chroma-key background, then post-process. In
   Woven that's a separate node: chain a `generate-image` node into a
   `rembg` node. Choose a key color unlikely to appear in the subject:
   - default `#00ff00` (green)
   - `#ff00ff` (magenta) when the subject is green
   - avoid `#0000ff` (blue) for blue subjects
3. **Subject too complex for chroma-key** (delicate edges, translucency,
   reflections) AND your model doesn't support native transparency → switch
   to a model that does for this asset.

When prompting for the chroma-key path, include explicit language that
forbids background variation:

```text
Subject on a perfectly flat solid #00ff00 chroma-key background for background removal.
The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation.
Keep the subject fully separated from the background with crisp edges and generous padding.
Do not use #00ff00 anywhere in the subject.
No cast shadow, no contact shadow, no reflection, no watermark, and no text unless explicitly requested.
```

## Per-use-case tips

### Generate

- **`photorealistic-natural`** - prompt as if a real photo captured in the
  moment; use photography language (lens, lighting, framing); call for real
  texture; avoid over-stylized polish unless requested.
- **`product-mockup`** - describe product / packaging and materials; ensure
  clean silhouette and label clarity; for in-image text, require verbatim
  rendering and specify typography.
- **`ui-mockup`** - describe target fidelity first (shippable mockup or
  low-fi wireframe), then focus on layout, hierarchy, practical UI elements;
  avoid concept-art language.
- **`infographic-diagram`** - define audience and layout flow; label parts
  explicitly; require verbatim text; prefer higher model quality for dense
  labels.
- **`logo-brand`** - keep it simple and scalable; ask for a strong silhouette
  and balanced negative space; avoid decorative flourishes unless requested.
- **`ads-marketing`** - write like a creative brief; include brand
  positioning, audience, desired vibe, scene, and exact tagline if text must
  appear.
- **`productivity-visual`** - name the exact artifact (slide, chart, workflow
  diagram), define canvas + hierarchy, provide real labels / data, ask for
  readable typography and polished spacing.
- **`scientific-educational`** - define audience, lesson objective, required
  labels, scientific constraints, arrows, and scan-friendly whitespace.
- **`illustration-story`** - define panels or scene beats; keep each action
  concrete.
- **`stylized-concept`** - specify style cues, material finish, rendering
  approach (3D, painterly, clay) without inventing new story elements.
- **`historical-scene`** - state location / date and required period
  accuracy; constrain clothing, props, environment to match the era.

### Edit

- **`text-localization`** - change only the text; preserve layout,
  typography, spacing, hierarchy; no extra words or reflow unless needed.
- **`identity-preserve`** - lock identity (face, body, pose, hair,
  expression); change only the specified elements; match lighting and
  shadows.
- **`precise-object-edit`** - specify exactly what to remove / replace;
  preserve surrounding texture and lighting; keep everything else unchanged.
- **`lighting-weather`** - change only environmental conditions (light,
  shadows, atmosphere, precipitation); keep geometry, framing, subject
  identity.
- **`background-extraction`** - for simple opaque subjects, request a clean
  cutout on a flat chroma-key background (see [Transparent backgrounds]);
  crisp silhouette; generous padding; no shadows; no halos; preserve label
  text exactly; no restyling.
- **`style-transfer`** - specify style cues to preserve (palette, texture,
  brushwork) and what must change; add `no extra elements` to prevent drift.
- **`compositing`** - reference inputs by index; specify what moves where;
  match lighting, perspective, scale; keep base framing unchanged.
- **`sketch-to-render`** - preserve layout, proportions, perspective; choose
  materials and lighting that support the supplied sketch without adding new
  elements.

## Sample prompt recipes

Copy-paste starting points. Adapt - don't blindly apply. Specifically, do
NOT treat these as the default augmentation budget for every request; they
are full recipes for thoroughly-specified asks.

### Generate

#### photorealistic-natural

```text
Use case: photorealistic-natural
Primary request: candid photo of an elderly sailor on a small fishing boat adjusting a net
Scene/backdrop: coastal water with soft haze
Subject: weathered skin with wrinkles and sun texture
Style/medium: photorealistic candid photo
Composition/framing: medium close-up, eye-level
Lighting/mood: soft coastal daylight, shallow depth of field, subtle film grain
Materials/textures: real skin texture, worn fabric, salt-worn wood
Constraints: natural color balance; no heavy retouching; no glamorization; no watermark
Avoid: studio polish; staged look
```

#### product-mockup

```text
Use case: product-mockup
Primary request: premium product photo of a matte black shampoo bottle with a minimal label
Scene/backdrop: clean studio gradient from light gray to white
Subject: single bottle centered with subtle reflection
Style/medium: premium product photography
Composition/framing: centered, slight three-quarter angle, generous padding
Lighting/mood: softbox lighting, clean highlights, controlled shadows
Materials/textures: matte plastic, crisp label printing
Constraints: no logos or trademarks; no watermark
```

#### ui-mockup

```text
Use case: ui-mockup
Primary request: mobile app home screen for a local farmers market with vendors and daily specials
Asset type: mobile app screen
Style/medium: realistic product UI, not concept art
Composition/framing: clean vertical mobile layout with clear hierarchy
Constraints: practical layout, clear typography, no logos or trademarks, no watermark
```

#### infographic-diagram

```text
Use case: infographic-diagram
Primary request: detailed infographic of an automatic coffee machine flow
Scene/backdrop: clean, light neutral background
Subject: bean hopper -> grinder -> brew group -> boiler -> water tank -> drip tray
Style/medium: clean vector-like infographic with clear callouts and arrows
Composition/framing: vertical poster layout, top-to-bottom flow
Text (verbatim): "Bean Hopper", "Grinder", "Brew Group", "Boiler", "Water Tank", "Drip Tray"
Constraints: clear labels, strong contrast, no logos or trademarks, no watermark
```

#### scientific-educational

```text
Use case: scientific-educational
Primary request: biology diagram titled "Cellular Respiration at a Glance" for high school students
Scene/backdrop: clean white classroom handout background
Subject: glucose turns into energy inside a cell; include glycolysis, Krebs cycle, and electron transport chain
Style/medium: flat scientific diagram with consistent icons, arrows, and readable labels
Composition/framing: landscape slide-style layout with clear hierarchy and generous whitespace
Text (verbatim): "Cellular Respiration at a Glance", "Glucose", "Pyruvate", "ATP", "NADH", "FADH2", "CO2", "O2", "H2O"
Constraints: scientifically plausible; avoid tiny text; no extra decoration; no watermark
```

#### logo-brand

```text
Use case: logo-brand
Primary request: original logo for "Field & Flour", a local bakery
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: single centered logo on a plain background with generous padding
Constraints: strong silhouette, balanced negative space; original design only; no gradients unless essential; no trademarks; no watermark
```

#### illustration-story

```text
Use case: illustration-story
Primary request: 4-panel comic about a pet left alone at home
Scene/backdrop: cozy living room across panels
Subject: pet reacting to the owner leaving, then relaxing, then returning to a composed pose
Style/medium: comic illustration with clear panels
Composition/framing: 4 equal-sized vertical panels, readable actions per panel
Constraints: no text; no logos or trademarks; no watermark
```

#### stylized-concept

```text
Use case: stylized-concept
Primary request: cavernous hangar interior with tall support beams and drifting fog
Scene/backdrop: industrial hangar interior, deep scale, light haze
Subject: compact shuttle parked near the center
Style/medium: cinematic concept art, industrial realism
Composition/framing: wide-angle, low-angle
Lighting/mood: volumetric light rays cutting through fog
Constraints: no logos or trademarks; no watermark
```

#### ads-marketing

```text
Use case: ads-marketing
Primary request: campaign image for a streetwear brand called Thread
Subject: group of friends hanging out together in a stylish urban setting
Style/medium: polished youth streetwear campaign photography
Composition/framing: vertical ad layout with natural poses and integrated headline space
Lighting/mood: contemporary, energetic, tasteful
Text (verbatim): "Yours to Create."
Constraints: render the tagline exactly once; clean legible typography; no extra text; no watermarks; no unrelated logos
```

#### productivity-visual

```text
Use case: productivity-visual
Primary request: one pitch-deck slide titled "Market Opportunity"
Asset type: fundraising slide image
Style/medium: clean modern deck slide, white background, crisp sans-serif typography
Subject: TAM/SAM/SOM concentric-circle diagram plus a small growth bar chart from 2021 to 2026
Composition/framing: 16:9 landscape slide, clear data hierarchy, polished spacing
Text (verbatim): "Market Opportunity", "TAM: $42B", "SAM: $8.7B", "SOM: $340M", "AGI Research, 2024", "Internal analysis"
Constraints: readable labels, no clip art, no stock photography, no decorative clutter, no watermark
```

#### historical-scene

```text
Use case: historical-scene
Primary request: outdoor crowd scene in Bethel, New York on August 16, 1969
Scene/backdrop: open field with period-appropriate staging
Subject: crowd in period-accurate clothing, authentic environment
Style/medium: photorealistic photo
Composition/framing: wide shot, eye-level
Constraints: period-accurate details; no modern objects; no logos or trademarks; no watermark
```

### Edit

#### text-localization

```text
Use case: text-localization
Input images: Image 1: original infographic
Primary request: replace "Bean Hopper", "Grinder", "Brew Group", "Boiler", "Water Tank", and "Drip Tray" with "Tolva", "Molino", "Grupo de infusión", "Caldera", "Depósito de agua", and "Bandeja de goteo"
Constraints: change only the text; preserve layout, typography, spacing, and hierarchy; no extra words; do not alter logos or imagery
```

#### identity-preserve

```text
Use case: identity-preserve
Input images: Image 1: person photo; Image 2..N: clothing references
Primary request: replace only the clothing with the provided garments
Constraints: preserve face, body shape, pose, hair, expression, and identity; match lighting and shadows; keep the background unchanged; no accessories or text
```

#### precise-object-edit

```text
Use case: precise-object-edit
Input images: Image 1: room photo
Primary request: replace only the white chairs with wooden chairs
Constraints: preserve camera angle, room lighting, floor shadows, and surrounding objects; keep all other aspects unchanged
```

#### lighting-weather

```text
Use case: lighting-weather
Input images: Image 1: original photo
Primary request: make it look like a winter evening with gentle snowfall
Constraints: preserve subject identity, geometry, camera angle, and composition; change only lighting, atmosphere, and weather
```

#### background-extraction (chroma-key path)

```text
Use case: background-extraction
Input images: Image 1: product photo
Primary request: isolate the product on a clean transparent background
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for background removal
Constraints: background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation; crisp silhouette; generous padding; no halos or fringing; preserve label text exactly; no restyling; do not use #00ff00 anywhere in the subject
```

In Woven, chain the result into a `rembg` node to extract the alpha. If the
subject is too complex for chroma-key (hair, fur, glass, liquids, soft
shadows), use a model that supports native transparent output instead - see
[Transparent backgrounds](#transparent-backgrounds).

#### style-transfer

```text
Use case: style-transfer
Input images: Image 1: style reference
Primary request: apply Image 1's visual style to a man riding a motorcycle on a plain white backdrop
Constraints: preserve palette, texture, and brushwork; no extra elements
```

#### compositing

```text
Use case: compositing
Input images: Image 1: base scene; Image 2: subject to insert
Primary request: place the subject from Image 2 next to the person in Image 1
Constraints: match lighting, perspective, and scale; keep the base framing unchanged; no extra elements
```

#### character consistency

```text
Use case: identity-preserve
Input images: Image 1: previous character anchor illustration
Primary request: continue the story with the same character in a new scene and action
Scene/backdrop: snowy forest after a winter storm
Subject: same young forest hero gently helping a frightened squirrel out of a fallen tree
Style/medium: same children's book watercolor illustration style as Image 1
Constraints: do not redesign the character; preserve facial features, proportions, outfit, color palette, and personality; no text; no watermark
```

#### sketch-to-render

```text
Use case: sketch-to-render
Input images: Image 1: drawing
Primary request: turn the drawing into a photorealistic image
Constraints: preserve layout, proportions, and perspective; choose realistic materials and lighting; do not add new elements or text
```

## Asset-type templates

Drop in over the [Shared prompt schema](#shared-prompt-schema) when the
intended use is one of these common shapes.

### Website assets

```text
Use case: <photorealistic-natural | stylized-concept | product-mockup | infographic-diagram | ui-mockup>
Asset type: <hero image / section illustration / blog header>
Primary request: <short description>
Scene/backdrop: <environment or abstract backdrop>
Subject: <main subject>
Style/medium: <photo / illustration / 3D>
Composition/framing: <wide / centered; note usable negative space only if needed>
Lighting/mood: <soft / bright / neutral>
Color palette: <brand colors or neutral>
Constraints: <no text; no logos; no watermark; leave room for UI if needed>
```

Examples:

```text
Use case: stylized-concept
Asset type: landing page hero background
Primary request: minimal abstract background with a soft gradient and subtle texture
Style/medium: matte illustration / soft-rendered abstract background
Composition/framing: wide composition with usable negative space for page copy
Lighting/mood: gentle studio glow
Color palette: restrained neutral palette
Constraints: no text; no logos; no watermark
```

```text
Use case: stylized-concept
Asset type: feature section illustration
Primary request: simple abstract shapes suggesting connection and flow
Scene/backdrop: subtle light-gray backdrop with faint texture
Style/medium: flat illustration; soft shadows; restrained contrast
Composition/framing: centered cluster; open margins for UI
Color palette: muted neutral palette
Constraints: no text; no logos; no watermark
```

```text
Use case: photorealistic-natural
Asset type: blog header image
Primary request: overhead desk scene with notebook, pen, and coffee cup
Scene/backdrop: warm wooden tabletop
Style/medium: photorealistic photo
Composition/framing: wide crop with clean room for page copy
Lighting/mood: soft morning light
Constraints: no text; no logos; no watermark
```

### Game assets

```text
Use case: stylized-concept
Asset type: <game environment concept art / game character concept / game UI icon / tileable game texture>
Primary request: <biome / scene / character / icon / material>
Scene/backdrop: <location + set dressing>            (if applicable)
Subject: <main focal element(s)>
Style/medium: <realistic / stylized>; <concept art / character render / UI icon / texture>
Composition/framing: <wide / establishing / top-down>; <camera angle>; <focal point placement>
Lighting/mood: <time of day>; <mood>; <volumetric / fog / etc>
Constraints: no logos or trademarks; no watermark
```

Examples:

```text
Use case: stylized-concept
Asset type: game environment concept art
Primary request: cavernous hangar interior with tall support beams and drifting fog
Scene/backdrop: industrial hangar interior, deep scale, light haze
Subject: compact shuttle parked near the center
Style/medium: cinematic concept art, industrial realism
Composition/framing: wide-angle, low-angle
Lighting/mood: volumetric light rays cutting through fog
Constraints: no logos or trademarks; no watermark
```

```text
Use case: stylized-concept
Asset type: game character concept
Primary request: desert scout character with layered travel gear
Subject: long coat, satchel, practical travel clothing
Style/medium: character render; stylized realism
Composition/framing: neutral hero pose on a simple backdrop
Constraints: no logos or trademarks; no watermark
```

```text
Use case: stylized-concept
Asset type: game UI icon
Primary request: round shield icon with a subtle rune pattern
Style/medium: painted game UI icon
Composition/framing: centered icon; generous padding; clear silhouette
Constraints: no text; no background scene elements; no logos or trademarks; no watermark
```

```text
Use case: stylized-concept
Asset type: tileable game texture
Primary request: worn sandstone blocks
Style/medium: seamless tileable texture; PBR-ish look
Scene/backdrop: neutral lighting reference only
Constraints: seamless edges; no obvious focal elements; no text; no logos or trademarks; no watermark
```

### Wireframes

```text
Use case: ui-mockup
Asset type: website wireframe
Primary request: <page or flow to sketch>
Style/medium: low-fi grayscale wireframe
Composition/framing: <landscape or portrait to match expected device>
Subject: <sections in order; grid / columns; key labels>
Constraints: no color; no logos; no real photos; no watermark
```

Examples:

```text
Use case: ui-mockup
Asset type: website wireframe
Primary request: SaaS homepage layout with clear hierarchy
Style/medium: low-fi grayscale wireframe
Subject: top nav; hero with headline and CTA; three feature cards; testimonial strip; pricing preview; footer
Composition/framing: landscape desktop layout
Constraints: label major blocks; no color; no logos; no real photos; no watermark
```

```text
Use case: ui-mockup
Asset type: website wireframe
Primary request: pricing page layout with comparison table
Style/medium: low-fi grayscale wireframe
Subject: header; plan toggle; 3 pricing cards; comparison table; FAQ accordion; footer
Composition/framing: desktop or tablet layout
Constraints: label key areas; no color; no logos; no real photos; no watermark
```

```text
Use case: ui-mockup
Asset type: mobile onboarding wireframe
Primary request: three-screen mobile onboarding flow
Style/medium: low-fi grayscale wireframe
Subject: screen 1 headline and CTA; screen 2 feature bullets; screen 3 form fields and CTA
Composition/framing: portrait mobile layout
Constraints: label screens and blocks; no color; no logos; no real photos; no watermark
```

### Logos

```text
Use case: logo-brand
Asset type: logo concept
Primary request: <brand idea or symbol concept>
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: centered mark; clear silhouette; generous margin
Color palette: <1-2 colors; high contrast>
Text (verbatim): "<exact name>"                       (only if needed)
Constraints: no gradients; no mockups; no 3D; no watermark
```

Examples:

```text
Use case: logo-brand
Asset type: logo concept
Primary request: geometric leaf symbol suggesting sustainability and growth
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: centered mark; clear silhouette
Color palette: deep green and off-white
Constraints: no text unless requested; no gradients; no mockups; no 3D; no watermark
```

```text
Use case: logo-brand
Asset type: logo concept
Primary request: interlocking monogram of the letters "AV"
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: centered mark; balanced spacing
Color palette: black on white
Constraints: no gradients; no mockups; no 3D; no watermark
```

```text
Use case: logo-brand
Asset type: logo concept
Primary request: clean wordmark for a modern studio
Style/medium: vector wordmark; flat colors; minimal
Text (verbatim): "Studio North"
Composition/framing: centered text; even letter spacing
Constraints: no gradients; no mockups; no 3D; no watermark
```

## Workflow

A condensed pass that ties everything above together. Run through this once
per request before any image-gen call.

1. Decide intent - `generate` or `edit`.
2. Decide execution strategy - single asset vs many distinct assets (one call
   each) vs variants of one prompt (`n` or repeated calls + seeds).
3. Decide use-case slug from the [Use-case taxonomy](#use-case-taxonomy).
4. Collect inputs up front: prompt(s), exact text (verbatim), constraints,
   avoid list, input images.
5. For every input image, label its role explicitly - reference, edit
   target, supporting insert / style / compositing input.
6. Apply the [Specificity policy](#specificity-policy). Normalize specific
   prompts; tastefully augment generic ones; do NOT invent.
7. Fill in the [Shared prompt schema](#shared-prompt-schema). Drop lines that
   don't help.
8. Pick the right model for the job - text-heavy → a model with strong
   typography; photorealism → a high-quality general model; transparent
   output → a model with native transparency support, or chain through
   `rembg` after a chroma-key prompt.
9. Generate. Inspect against subject, style, composition, text accuracy,
   invariants, avoid items.
10. Iterate with single targeted changes. Re-state critical constraints each
    iteration - they drop silently otherwise.
11. Report the final prompt and the chosen model so future-you can resume.
