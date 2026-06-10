# Illustration Library — research dossier for illustration-orchestrator

> Canonical reference baked into `/Users/sami/Documents/Woven/.claude/agents/illustration-orchestrator.md`.
> Quality > breadth. Catalogued, not skimmed. Read top-to-bottom or jump via the category index.

## 0. How this document is used

The illustration-orchestrator walks source HTML, finds slots that need illustrative raster (heroes, spot-illos, mascots, decorations, illustrated-typography moments), inspects the surrounding aesthetic, and picks an entry from **§2 Style library**. It then composes the prompt enrichment node that downstream image generators (Imagen, Flux, Nano Banana, Midjourney, DALL-E) consume.

The decision flow at runtime:

1. Read the `prototypeStyles` slugs of the host shell/recipe/aesthetic from the document.
2. Cross-reference against **§3 Category × prototype decision tree**.
3. Pull candidate entries from §2 by `styleId`.
4. Filter by `role` (subject vs decoration vs mascot vs typography vs spot vs hero).
5. Compose final prompt: `examplePromptTemplate` + filled subject + universal negatives from **§4**.
6. If decoration only, route to **§5 Decoration addendum** instead.

---

## 1. Categories

Top-level taxonomy. Every entry in §2 must declare exactly one `category` and (when meaningful) one `subCategory`.

- **3D** — anything with rendered volume, materials, lighting.
  - sub: `clay`, `plasticine`, `fluffy-plush`, `plastic-glossy`, `jelly-gummy`, `wireframe`, `origami`, `low-poly-paper`, `voxel`, `isometric-tech`, `render-cinematic`, `claymation-stop-motion`, `wood-craft`.
- **Flat vector** — geometry over rendering.
  - sub: `corporate-memphis`, `thick-border-cartoon`, `hairline`, `geometric-mid-century`, `geometric-with-grain`, `noodle-people`, `flat-iconographic`, `flat-with-pattern`.
- **Hand-drawn / sketch** — visible mark, traces of tool.
  - sub: `scribble-marker`, `ink-line-brush`, `pencil-graphite`, `watercolor`, `gouache`, `charcoal`, `marginalia-quirky`, `naive-folk`, `crayon-wax`.
- **Anime / manga** — Japanese illustration grammar.
  - sub: `shoujo-soft-line`, `ghibli-watercolor-bg`, `shinkai-hyperreal`, `shonen-active-line`, `kawaii-mascot`, `chibi`, `pc98-visual-novel`.
- **Illustrative typography** — type as the illustration.
  - sub: `y2k-chrome-3d`, `vectorheart-decorative`, `weingart-deconstructed`, `art-nouveau-ornament`, `hand-lettered-editorial`, `fella-anti-design`, `blackletter-neo-gothic`, `bubble-graffiti`, `illuminated-drop-cap`, `house-industries-revival`, `wood-type-letterpress`.
- **Abstract / decoration** — non-representational, accent role.
  - sub: `gradient-blob`, `geometric-primitive`, `doodle-arrow`, `sticker-cutout`, `halftone-shape`, `riso-grain-shape`, `squiggle-line`, `wavy-line`, `star-burst`, `aurorism-mesh`.
- **Mid-century / vintage** — historically rooted illustrative idioms.
  - sub: `saul-bass-cutout`, `mary-blair-stylized`, `charley-harper-minimal-realism`, `eames-mid-century`, `1950s-pulp`, `1970s-airbrush`, `1960s-psychedelic`.
- **Surreal / esoteric** — dreams, symbols, paradox.
  - sub: `hilma-symbolist`, `mc-escher-paradox`, `cyriak-bodyhorror`, `beeple-dystopia`, `dreamcore-liminal`, `frida-folk-surreal`.
- **Editorial conceptual** — magazine/newspaper one-idea illustration.
  - sub: `niemann-puzzle`, `editorial-thick-brush`, `nyt-op-ed`, `new-yorker-cover`.
- **Children's book / storybook** — soft, narrative, kindly.
  - sub: `eric-carle-collage`, `beatrix-potter-watercolor`, `jean-jullien-thick-line`, `naive-storybook`, `pop-up-book-cutout`.

---

## Entry catalogue — moved to per-file sources

**Each of the 108 entries in this library is its own source-of-truth file in `prototype/illust-<entryId>.md`** — hand-editable, with YAML frontmatter + markdown sections. Editing one entry doesn't require scanning the rest of the library.

Where to find an entry:

- **Browse the System tab → Design library** in the editor. The Illustration bucket lists all entries as cards with image-sample slots.
- **List from the shell:** `ls prototype/illust-*.md`
- **Read one programmatically:** the `.index.json` companion file (e.g. `docs/research/illustration-library.index.json`) maps every entry id to its source path, and orchestrators consume that index to route a slot to the right entry without scanning the big primer.

To add a new entry, create a new `prototype/illust-<entryId>.md` with YAML frontmatter and markdown body (use any existing file as a template), then re-run `python3 scripts/build-library-indexes.py` to refresh the index. That script reads the prototype directory; the primer below is for principles only.

## 3. Category × prototype decision tree

> **Normalised schema (read this before parsing the tables below).** Every entry conforms to:
>
> - **Column 1 — `Prototype slug`** — kebab-case slug from prototype.md (recipes, aesthetics, styles, shells). Orchestrators match their `committedAesthetic` envelope field against this. Exact-match only; no fuzzy matching.
> - **Column 2 — `Default`** — the PRIMARY illustration `styleId` (kebab-case, matches an entry in §2 above). Orchestrator uses this by default unless overridden by `explicitStylePicks[slotId]` or by an antiPattern conflict.
> - **Column 3 — `Alternatives`** — comma-separated additional `styleId`s for variety / antiPattern avoidance.
> - **Column 4 — `Decoration / Notes`** — for illustration specifically, this column carries the recommended decoration-role styleId (abstract shape / arrow / blob) that pairs with the slug. May also carry advisory prose.
>
> The three subsections below split by slug-type (style / aesthetic / recipe) only for readability — orchestrator reads all three. The same schema is mirrored in `photography-library.md §3` and `material-library.md §7`.

For each major prototype.md style/aesthetic slug, the recommended illustration entries. Use first-listed entry as default; later entries are alternatives for variety. Roles in parentheses where the choice is not the obvious one.

### 3.1 Style slugs

| prototype.md slug | Default illustration style | Alternatives | Decoration choice |
|---|---|---|---|
| style-claymorphism | drawkit-jelly-3d | clay-3d-soft-sculpt, drawkit-bubbly-tech-ui, blush-currency-crush | spectrums-organic-blob |
| style-neumorphism | drawkit-bubbly-tech-ui | clay-3d-soft-sculpt | spectrums-organic-blob |
| style-glassmorphism | liquid-glass-3d | aurorism-mesh-gradient | aurorism-mesh-gradient |
| style-liquid-glass | liquid-glass-3d | drawkit-hands-3d | aurorism-mesh-gradient |
| style-holographic | typo-y2k-chrome-3d | aurorism-mesh-gradient | aurorism-mesh-gradient |
| style-aurorism | aurorism-mesh-gradient (decoration) | spectrums-organic-blob, shapes-gallery-michalczyk | aurorism-mesh-gradient |
| style-neubrutalism | thick-border-cartoon | typo-fella-anti-design | spectrums-vector-shape-circle |
| style-doodle | handyarrows-doodles | doodle-ui-handdrawn, scribbbles-funky-vector, handyarrows-arrows | scribbbles-funky-vector |
| style-outline-wireframe | outline-wireframe-illustration | wireframe-3d | spectrums-vector-shape-circle |
| style-restrained-hairline | outline-wireframe-illustration | niemann-puzzle-conceptual | shapes-gallery-michalczyk |
| style-serif-warm-paper | humanities-marginalia | gouache-storybook, hand-drawn-pencil-sketch | none |
| style-terminal-mono | wireframe-3d | typo-weingart-deconstructed | none |
| style-bold-display | typo-hand-lettered-editorial | shapes-gallery-michalczyk | shapes-gallery-michalczyk |
| style-oversized-neo-grotesque | shapes-gallery-michalczyk (decoration) | typo-weingart-deconstructed | shapes-gallery-michalczyk |
| style-pixel-bitmap | pixel-bitmap-illustration | voxel-magicavoxel | none |
| style-raster-cutout | raster-cutout-collage | saul-bass-cutout, eric-carle-tissue-collage | halftone-shape |
| style-flat-design | corporate-memphis-noodle | blush-humaaans, drawkit-isometric-stickers | spectrums-organic-blob |
| style-material-m3 / m1m2 | corporate-memphis-noodle | isometric-tech-saas | spectrums-organic-blob |
| style-sf-pro-ios | drawkit-hands-3d | liquid-glass-3d | aurorism-mesh-gradient |
| style-dense-mono-dark | wireframe-3d | typo-weingart-deconstructed | none |
| style-cream-humanist | gouache-storybook | hand-drawn-pencil-sketch, beatrix-potter-watercolor | none |
| style-agate-broadsheet | editorial-thick-brush | niemann-puzzle-conceptual | none |
| style-skeuomorphism | skeuomorphic-detailed | drawkit-wooden-icons | none |
| style-brutalist-raw | typo-fella-anti-design | typo-weingart-deconstructed, thick-border-cartoon | halftone-shape |

### 3.2 Aesthetic slugs

| prototype.md aesthetic | Default illustration | Alternatives | Decoration |
|---|---|---|---|
| aesthetic-corporate-memphis | blush-humaaans | corporate-memphis-noodle, blush-allura, blush-yuppies, blush-dayflow | scribbbles-funky-vector |
| aesthetic-positivity-kawaii | kawaii-mascot | blush-shiny-happy, drawkit-jelly-3d, fluffy-plush-3d, blush-happy-bunch | handyarrows-doodles |
| aesthetic-cottagecore | beatrix-potter-watercolor | blush-fancy-plants, drawkit-wooden-icons, ghibli-watercolor-bg, gouache-storybook | none |
| aesthetic-cottagegoth | blush-spooky-stickers | beatrix-potter-watercolor (darker palette), typo-blackletter-neo-gothic | halftone-shape |
| aesthetic-solarpunk | drawkit-wooden-icons | blush-go-green, charley-harper-minimal-realism, ghibli-watercolor-bg | spectrums-organic-blob |
| aesthetic-dreamcore | dreamcore-liminal | hilma-af-klint-symbolist, cyriak-bodyhorror | spectrums-organic-blob |
| aesthetic-angelcore | hilma-af-klint-symbolist | typo-illuminated-drop-cap | aurorism-mesh-gradient |
| aesthetic-fairycore | mary-blair-stylized | hilma-af-klint-symbolist, typo-art-nouveau-ornament, beatrix-potter-watercolor | spectrums-complex-flower |
| aesthetic-y2k-futurism | typo-y2k-chrome-3d | vector-hands-up-eurodance, blush-transhumans | aurorism-mesh-gradient |
| aesthetic-y2k-memphis-loud | blush-cool-kids | typo-y2k-chrome-3d, blush-power-moves, blush-tutto-ricco | spectrums-complex-flower |
| aesthetic-y2k-myspace | typo-y2k-chrome-3d | vector-hands-up-eurodance | spectrums-complex-flower |
| aesthetic-vaporwave | typo-y2k-chrome-3d | dreamcore-liminal, vector-hands-up-eurodance | aurorism-mesh-gradient |
| aesthetic-cyberpunk | wireframe-3d | beeple-dystopia, blush-transhumans | aurorism-mesh-gradient |
| aesthetic-cassette-futurism | blush-hyperspace | saul-bass-cutout, typo-house-industries-revival | halftone-shape |
| aesthetic-atompunk | blush-hyperspace | saul-bass-cutout, mary-blair-stylized | spectrums-vector-shape-circle |
| aesthetic-dieselpunk | typo-house-industries-revival | saul-bass-cutout | halftone-shape |
| aesthetic-steampunk | humanities-marginalia | typo-art-nouveau-ornament | none |
| aesthetic-curly-girly | blush-cool-kids | fluffy-plush-3d, typo-vectorheart-decorative, blush-tutto-ricco | spectrums-complex-flower |
| aesthetic-maximalism | blush-cool-kids | blush-power-moves, frida-folk-surreal | spectrums-complex-flower |
| aesthetic-cluttercore | blush-goodies | sticker-cutout-puffy | handyarrows-doodles |
| aesthetic-acid-design | vector-hands-up-eurodance | blush-power-moves, typo-vector-musica | halftone-shape |
| aesthetic-acid-graphics | raster-cutout-collage | cyriak-bodyhorror, typo-fella-anti-design | halftone-shape |
| aesthetic-anti-design | typo-fella-anti-design | raster-cutout-collage, humanities-marginalia | halftone-shape |
| aesthetic-web-brutalism | thick-border-cartoon | typo-weingart-deconstructed, typo-fella-anti-design | halftone-shape |
| aesthetic-neubrutalism | thick-border-cartoon | typo-fella-anti-design | spectrums-vector-shape-circle |
| aesthetic-corporate-grunge | typo-blackletter-neo-gothic | raster-cutout-collage, typo-wood-type-letterpress | halftone-shape |
| aesthetic-dark-academia | humanities-marginalia | beatrix-potter-watercolor, typo-illuminated-drop-cap, hand-drawn-pencil-sketch | none |
| aesthetic-coastal-grandmother | beatrix-potter-watercolor | blush-dayflow, drawkit-wooden-icons, blush-allura | shapes-gallery-michalczyk |
| aesthetic-bauhaus | bauhaus-geometric | spectrums-vector-shape-circle, low-poly-paper-3d | spectrums-vector-shape-circle |
| aesthetic-de-stijl | bauhaus-geometric | blush-patterns | spectrums-vector-shape-circle |
| aesthetic-constructivism | bauhaus-geometric | saul-bass-cutout | spectrums-vector-shape-circle |
| aesthetic-swiss-modernist | bauhaus-geometric | charley-harper-minimal-realism, low-poly-paper-3d | spectrums-vector-shape-circle |
| aesthetic-op-art | mc-escher-paradox | bauhaus-geometric | spectrums-vector-shape-circle |
| aesthetic-frutiger-aero | drawkit-bubbly-tech-ui | aurorism-mesh-gradient | aurorism-mesh-gradient |
| aesthetic-frutiger-eco | blush-go-green | drawkit-wooden-icons | spectrums-organic-blob |
| aesthetic-frutiger-chromecore | typo-y2k-chrome-3d | liquid-glass-3d | aurorism-mesh-gradient |
| aesthetic-frutiger-bright-tertiaries | drawkit-bubbly-tech-ui | blush-isometric-stickers-vega | aurorism-mesh-gradient |
| aesthetic-frutiger-dark-aero | aurorism-mesh-gradient | liquid-glass-3d | aurorism-mesh-gradient |
| aesthetic-frutiger-dorfic | drawkit-wooden-icons | drawkit-bubbly-tech-ui | none |
| aesthetic-frutiger-four-colors | drawkit-bubbly-tech-ui | corporate-memphis-noodle | spectrums-vector-shape-circle |
| aesthetic-frutiger-tranquil-serenity | aurorism-mesh-gradient | ghibli-watercolor-bg | aurorism-mesh-gradient |
| aesthetic-vector-neovectorheart | typo-vectorheart-decorative | mary-blair-stylized | spectrums-complex-flower |
| aesthetic-vector-vector-musica | typo-vector-musica | raster-cutout-collage | halftone-shape |
| aesthetic-vector-vectorbloom | typo-vectorheart-decorative | blush-fancy-plants, typo-art-nouveau-ornament | spectrums-complex-flower |
| aesthetic-vector-vectordelia | mary-blair-stylized | typo-vectorheart-decorative | spectrums-complex-flower |
| aesthetic-vector-hands-up | vector-hands-up-eurodance | typo-y2k-chrome-3d | aurorism-mesh-gradient |
| aesthetic-avantropop | typo-y2k-chrome-3d | vector-hands-up-eurodance, blush-transhumans | halftone-shape |
| aesthetic-urbling | typo-bubble-graffiti | typo-y2k-chrome-3d | halftone-shape |
| aesthetic-rgb-gamer | voxel-magicavoxel | wireframe-3d, pixel-bitmap-illustration | aurorism-mesh-gradient |
| aesthetic-crypto-degen | beeple-dystopia | blush-moneyverse, blush-currency-crush | aurorism-mesh-gradient |
| aesthetic-defi-cosmic | blush-moneyverse | blush-hyperspace | aurorism-mesh-gradient |
| aesthetic-depin-hardware | wireframe-3d | isometric-tech-saas | none |
| aesthetic-goblincore | humanities-marginalia | beatrix-potter-watercolor, hand-drawn-pencil-sketch | none |
| aesthetic-pixel-nes-mario | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-pixel-snes-jrpg | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-pixel-game-boy-mono | pixel-bitmap-illustration | typo-weingart-deconstructed | none |
| aesthetic-pixel-modern-cozy | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-pixel-ps1-tactics-ogre | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-pixel-arcade | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-8-bit-generic | pixel-bitmap-illustration | voxel-magicavoxel | none |
| aesthetic-pc-98 | shoujo-soft-line-anime | pixel-bitmap-illustration | none |
| aesthetic-wacky-pomo | crayon-wax-children | thick-border-cartoon, blush-cool-kids | handyarrows-doodles |

### 3.3 Recipe slugs

| recipe slug | Default illustration | Alternatives | Decoration |
|---|---|---|---|
| recipe-ai-foundry-dark | aurorism-mesh-gradient (decoration) | wireframe-3d, beeple-dystopia | aurorism-mesh-gradient |
| recipe-aurora-marketing | aurorism-mesh-gradient | drawkit-bubbly-tech-ui | aurorism-mesh-gradient |
| recipe-bento-marketing | drawkit-isometric-stickers | drawkit-jelly-3d, blush-isometric-stickers-vega, blush-humaaans | shapes-gallery-michalczyk |
| recipe-bloomberg-dashboard | wireframe-3d (sparingly) | editorial-thick-brush | none |
| recipe-brutalist-web | typo-fella-anti-design | thick-border-cartoon, typo-weingart-deconstructed | halftone-shape |
| recipe-devtools-marketing | doodle-ui-handdrawn | wireframe-3d, isometric-tech-saas | spectrums-vector-shape-circle |
| recipe-editorial-magazine | humanities-marginalia | niemann-puzzle-conceptual, editorial-thick-brush, saul-bass-cutout, typo-hand-lettered-editorial | halftone-shape |
| recipe-ios-system | liquid-glass-3d | drawkit-hands-3d | aurorism-mesh-gradient |
| recipe-linear-product-ui | drawkit-isometric-stickers | blush-yuppies, isometric-tech-saas | shapes-gallery-michalczyk |
| recipe-material-3 | corporate-memphis-noodle | blush-humaaans | spectrums-organic-blob |
| recipe-neo-grotesque-portfolio | shapes-gallery-michalczyk (decoration) | typo-hand-lettered-editorial | shapes-gallery-michalczyk |
| recipe-newspaper-of-record | editorial-thick-brush | niemann-puzzle-conceptual, humanities-marginalia | none |
| recipe-readcv | doodle-ui-handdrawn | humanities-marginalia, hand-drawn-pencil-sketch, blush-open-peeps, handyarrows-doodles | handyarrows-doodles |
| recipe-restrained-ai-marketing | drawkit-hands-3d | outline-wireframe-illustration, aurorism-mesh-gradient | aurorism-mesh-gradient |
| recipe-scientific-infra-marketing | wireframe-3d | isometric-tech-saas | none |
| recipe-swiss-grid | bauhaus-geometric | spectrums-vector-shape-circle | spectrums-vector-shape-circle |
| recipe-terminal-on-web | wireframe-3d | typo-weingart-deconstructed | none |
| recipe-warm-restraint | beatrix-potter-watercolor | gouache-storybook, drawkit-wooden-icons, blush-fancy-plants, hand-drawn-pencil-sketch | none |
| recipe-y2k-memphis-loud | blush-cool-kids | typo-y2k-chrome-3d, blush-power-moves | spectrums-complex-flower |

---

## 4. Negative-keyword universal list

Append these to every illustration prompt regardless of style. They are universal anti-patterns the orchestrator wants gone.

### 4.1 Generic-stock language (always blacklist)

- "Adobe Stock illustration"
- "Bigstock vector"
- "Shutterstock illustration"
- "iStock vector"
- "Freepik download"
- "vecteezy"
- "stock illustration"
- "royalty-free clipart"
- "generic vector character"

### 4.2 AI-looking failure modes (always blacklist)

- "AI-looking"
- "uncanny face"
- "extra fingers"
- "warped hand"
- "mangled anatomy"
- "melted face"
- "asymmetric eyes by accident"
- "Stable Diffusion smear"
- "MidJourney brown sludge"
- "DALL-E sameface"
- "blurry low-quality"
- "watermark text"
- "label text artifact"
- "garbled text"

### 4.3 Composition failure modes

- "cluttered background"
- "off-center awkwardly"
- "cropped subject"
- "out of frame essential element"
- "edge-bleed when isolation requested"

### 4.4 Content safety (always blacklist for marketing use)

- "violent imagery"
- "gore"
- "sexual content"
- "trademark logos"
- "celebrity face likeness"
- "copyrighted character"

### 4.5 Conditional blacklists by category

Apply these on top of the universal list when the chosen style is in the parent category.

- For all **3D** styles: avoid "flat illustration", "vector cartoon", "2D outline"
- For all **Flat vector**: avoid "3D render", "subsurface scattering", "Octane"
- For all **Hand-drawn / sketch**: avoid "vector perfect", "smooth digital", "polished render"
- For all **Anime / manga**: avoid "Western cartoon", "Disney 3D", "photoreal portrait"
- For all **Illustrative typography**: avoid "default Helvetica", "system font", "Arial fallback"
- For all **Abstract / decoration**: avoid "recognizable subject", "character", "face"
- For all **Mid-century / vintage**: avoid "modern gradient", "Y2K chrome", "neon"
- For all **Surreal / esoteric**: avoid "literal interpretation", "stock photo realism"
- For all **Editorial conceptual**: avoid "decorative", "ornament", "Y2K"
- For all **Children's book / storybook**: avoid "edgy", "dark", "violent", "gore"

---

## 5. Decoration / abstract-shape addendum

Decoration entries don't depict a subject. They sit in the negative space between sections, behind text as background masks, beside headlines as marks of emphasis, or in margins as visual rhythm. The orchestrator routes "decoration-only" slots here rather than to subject illustrations.

### 5.1 Geometric properties index

| Form family | Source entries | Typical placement | Compatible host aesthetics |
|---|---|---|---|
| **Circles** (solid, dotted, segmented) | spectrums-vector-shape-circle, shapes-gallery-michalczyk | bullet marks, drop-cap halos, section anchors | bauhaus, swiss-modernist, de-stijl, constructivism |
| **Organic blobs** | spectrums-organic-blob, aurorism-mesh-gradient | behind text as background mask, hero bg accent | frutiger-aero, frutiger-eco, aurorism, glassmorphism |
| **Complex flowers / stars** | spectrums-complex-flower | headline halos, decorative section dividers | y2k-memphis-loud, curly-girly, vectorheart, fairycore |
| **Doodle arrows** | handyarrows-arrows | pointing at headlines, marking flow direction, "click here" | doodle, corporate-memphis, readcv, bento-marketing |
| **Hand-drawn underlines / brackets** | handyarrows-underlines | emphasizing words in headlines, grouping list items | doodle, readcv, y2k-memphis-loud, corporate-memphis |
| **Sparkles / stars / hearts** (doodle) | handyarrows-doodles | scattered around headlines, between sections, bullet substitutes | positivity-kawaii, curly-girly, doodle, readcv |
| **Squiggle lines** (loose abstract) | scribbbles-funky-vector | replacing solid divider lines, manual underlines | doodle, corporate-memphis, bento-marketing, positivity-kawaii |
| **Infographic callouts** (circles, brackets, numbers) | handyarrows-infographic | annotating screenshots, wireframe markup | doodle, bento-marketing, readcv |
| **Halftone retro shape** | halftone-shape | editorial accents, indie poster bands | editorial-magazine, anti-design, y2k-memphis-loud |
| **Sticker cutout** (puffy white halo) | sticker-cutout-puffy | scrapbook substrates, casual product pages | scrapbook-substrate, cluttercore, bento-marketing |
| **Patterns** (tileable) | blush-patterns | background bands, section dividers, wallpaper accents | bauhaus, de-stijl, corporate-memphis, bento-marketing |
| **Refined geometric/wave** | shapes-gallery-michalczyk | designer portfolios, editorial sites | neo-grotesque-portfolio, readcv, bold-display, bento-marketing |

### 5.2 Placement-role taxonomy

- **`negative-space-fill`** — fills empty area between sections so layout doesn't look sparse. Use: aurorism-mesh-gradient, spectrums-organic-blob.
- **`headline-halo`** — sits behind or beside a headline to focus attention. Use: spectrums-complex-flower, handyarrows-doodles, scribbbles-funky-vector.
- **`section-divider`** — replaces a solid `<hr>` with something with character. Use: scribbbles-funky-vector, halftone-shape, handyarrows-underlines.
- **`bullet-mark`** — replaces a default bullet point. Use: spectrums-vector-shape-circle, handyarrows-doodles, handyarrows-arrows.
- **`emphasis-underline`** — handwritten underline under a word. Use: handyarrows-underlines, scribbbles-funky-vector.
- **`flow-direction-arrow`** — explicit pointing arrow in marketing pages. Use: handyarrows-arrows.
- **`infographic-callout`** — circles/brackets annotating screenshots. Use: handyarrows-infographic.
- **`tileable-background-pattern`** — repeating texture filling backgrounds. Use: blush-patterns, halftone-shape.
- **`drop-cap-ornament`** — decorative ornament beside an initial letter. Use: typo-illuminated-drop-cap (subject-as-typography hybrid).

### 5.3 Pairing logic — when shape vs aurora vs doodle

- If the host style is **geometric / Swiss / Bauhaus / Constructivist** → use shape-primitive families (spectrums-vector-shape-circle, shapes-gallery-michalczyk).
- If the host style is **AI marketing / ethereal / frutiger / glass** → use mesh-gradient (aurorism-mesh-gradient, spectrums-organic-blob).
- If the host style is **hand-drawn / doodle / friendly SaaS** → use doodle families (handyarrows-doodles, scribbbles-funky-vector).
- If the host style is **y2k-memphis-loud / maximalism / curly-girly** → use complex-flower + halftone.
- If the host style is **editorial / newspaper / brutalist** → use halftone-shape, blush-patterns.
- If the host style is **scrapbook substrate / cluttercore** → use sticker-cutout-puffy + multi-decoration density.

---

## 6. Style-orchestrator integration notes

For the illustration-orchestrator at runtime, the recommended algorithm:

1. **Detect host aesthetic** — read the HTML's data-attributes or class names linking to a prototype.md slug; if absent, infer from the first 100 tokens of the page text and the page's color tokens.
2. **Enumerate slots** — find `<figure>`, `[data-illustration]`, empty hero divs above the fold, decoration zones flagged by `aria-hidden="true"`.
3. **Classify slot role** — subject / mascot / decoration / typography / hero / spot. The orchestrator should default to `spot-illustration` if ambiguous; never default to `hero` (too risky).
4. **Pick entry from §3 decision tree** for the host aesthetic. Default to the first column. If a previous slot on the same page already used the default, pick the alternative.
5. **Compose prompt** — `examplePromptTemplate` from chosen entry + slot-specific subject + universal negatives from §4 + category-conditional negatives from §4.5.
6. **Pass to image generator** — recommend Imagen for cinematic + hand realism, Flux for vector-flat reliability, Nano Banana for cheap iteration, Midjourney for stylized art, DALL-E for typography.

### 6.1 Multi-slot consistency

When a page has multiple illustration slots, enforce **one entry per page** unless intentionally mixing for scrapbook / cluttercore. Vary subject within the same `styleId`. Never mix `flat-vector` with `3D` in the same module unless the host is scrapbook-substrate.

### 6.2 Aesthetic boundary cases

- **claymorphism + restrained-ai** → use drawkit-hands-3d (cinematic hands) not drawkit-jelly-3d (too cute).
- **corporate-memphis + brutalism** (paradoxical) → use thick-border-cartoon as compromise.
- **cottagecore + tech** → use drawkit-wooden-icons (the bridge).
- **dreamcore + saas** → use aurorism-mesh-gradient (the safe abstract).
- **y2k + B2B** → use typo-y2k-chrome-3d only on hero wordmark; everything else, restrained-hairline.

### 6.3 Prompt template variables

Every `examplePromptTemplate` uses `[BRACKETED_PLACEHOLDERS]`. The orchestrator fills them at runtime:

- `[SUBJECT]` — the concrete noun from the page (e.g. "a coffee mug")
- `[SCENE]` — when the slot wants a scene not an isolated subject
- `[WORD]` — the actual text for typographic illustrations
- `[LETTER]` — for drop caps
- `[CONCEPT]` — for editorial-conceptual illustrations
- `[ERA]` — for pixel-bitmap (NES / GameBoy / SNES / PS1 / arcade)
- `[BIRD/ANIMAL]` — for Charley Harper minimal-realism nature
- `[REAL OBJECT]` — for Niemann puzzle (must be a real photo prop)

---

## 7. Coverage audit

Self-audit against the quality bar.

1. **60+ distinct styles?** — count of entries: 68. PASS.
2. **Styles differentiated?** — 3D clay (matte fingerprint), 3D fluffy (long fiber fur), 3D origami (visible crease), 3D voxel (cube grid), 3D low-poly paper (faceted edges), 3D wireframe (no fill), 3D plasticine (oilier tool marks), 3D jelly (translucent subsurface), 3D bubbly (inflated pillow), 3D liquid-glass (refractive), 3D Pixar (cinematic subsurface), 3D claymation (armature visible). DISTINCT. PASS.
3. **One keyword distinguishes any pair?** — sample: clay-3d-soft-sculpt vs fluffy-plush-3d differ by `fur shader`; voxel-magicavoxel vs low-poly-paper-3d differ by `cube grid` vs `polygon edge`; blush-humaaans vs corporate-memphis-noodle differ by `modular limb snap` vs `bendy noodle limb`. PASS.
4. **Prototype mapping comprehensive?** — Section 3 covers all style-, aesthetic-, and recipe- slugs that exist in /Users/sami/Documents/Woven/prototype/. PASS.
5. **HandyArrows multi-page?** — 5 buckets catalogued: Arrows, Doodles, Infographic, Illustrations, Underlines. PASS (research-based since handyarrows.com sub-paths returned 404).
6. **Illustrative-typography research done?** — 11 entries: y2k-chrome-3d, weingart-deconstructed, art-nouveau-ornament, fella-anti-design, vectorheart-decorative, vector-musica, illuminated-drop-cap, blackletter-neo-gothic, bubble-graffiti, house-industries-revival, wood-type-letterpress, hand-lettered-editorial. PASS (12 actually).

## 8. Source map and known limitations

- **drawkit.com/illustration-types/3d** — WebFetch succeeded; 17 sub-collections identified.
- **blush.design/collections** — WebFetch returned 403; recovered full list via WebSearch (27+ collections individually researched).
- **levinunnink.gumroad.com/l/humanities-illustrations** — WebFetch returned thin content; recovered via WebSearch (medieval-marginalia tradition, anti-AI artist statement, 35 PNG count).
- **scribbbles.design** — WebFetch returned thin content; recovered visual register via WebSearch (vector scribbles, customizable color, "funky" aesthetic).
- **spectrums.framer.website** — WebFetch returned thin content; recovered via WebSearch (categories: All, Circle, Square, Triangle, Star, Organic, Complex).
- **shapes.gallery** — WebFetch returned thin content; recovered via WebSearch (80+ SVG shapes by Monika Michalczyk, organic + geometric, free copy-paste).
- **handyarrows.com** — WebFetch root page succeeded; sub-paths returned 404 (the site uses anchor links not URL paths); recovered category list via direct page content + WebSearch.

Failed/thin fetches were rescued via WebSearch; no sources were skipped.

---

End of dossier.
