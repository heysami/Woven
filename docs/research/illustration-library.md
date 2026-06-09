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

## 2. Style library

Entries are grouped by source/category for browsability but each is self-contained. Target: 60+ entries.

### 2.1 — DrawKit 3D collections (source: drawkit.com/illustration-types/3d)

- styleId: drawkit-jelly-3d
  name: DrawKit Jelly Characters 3D
  category: 3D
  subCategory: jelly-gummy
  role: mascot
  source: drawkit.com/illustration-types/3d (Jelly Characters: Work & Life)
  visualSignatures:
    - translucent gummy-bear surface with subsurface light
    - rounded jellybean limbs, no separate hands/feet
    - bright candy palette — neon yellow, magenta, cyan
    - subtle inner glow + glossy specular cap on top of head
  promptKeywords:
    primary: [3d, jelly, gummy, translucent, character, glossy, subsurface scattering, bouncy]
    material: ["soft jelly material", "gummy candy resin", "subsurface scattering", "translucent silicone"]
    line: ["no line", "soft edge"]
    color: ["bright candy palette", "saturated translucent fills", "neon accent"]
    style: ["studio lighting", "soft shadow", "playful mascot pose"]
    avoidKeywords: [opaque matte, metallic, realistic skin, sharp angular]
  namedReferences:
    illustrators: [DrawKit]
    movements: [post-claymorphism mascot wave]
    productsOrFilms: [Haribo gummy aesthetics, fintech onboarding mascots circa 2023]
  examplePromptTemplate: |
    3D translucent jelly character mascot, rounded bouncy limbs, no facial features
    or simple dot eyes, subsurface scattering with inner glow, glossy specular highlight,
    bright candy palette of neon yellow magenta and cyan, studio three-point lighting,
    soft contact shadow on white background, playful pose, isolated subject, 8k render.
  whenToUse: When a marketing surface needs an empty-headed friendly mascot that
    signals "approachable fintech / startup with personality." Pairs with
    style-claymorphism and recipe-restrained-ai-marketing when you need a single
    accent that doesn't read as corporate-Memphis fatigue.
  pairsWith:
    prototypeStyles: [style-claymorphism, aesthetic-positivity-kawaii, recipe-restrained-ai-marketing, style-skeuomorphism]
  notForUseWhen: dense Bloomberg-style data UI, brutalist or editorial layouts

- styleId: drawkit-bubbly-tech-ui
  name: DrawKit Bubbly Tech / UI 3D
  category: 3D
  subCategory: plastic-glossy
  role: spot-illustration
  source: drawkit.com/illustration-types/3d (Bubbly Tech & UI)
  visualSignatures:
    - tech objects (laptops, phones, cards) rendered as inflated bubble forms
    - corner radii so high every prism looks like a pillow
    - pastel-to-mid-saturation gradient on each face
    - tiny bubble decorations floating in the scene
  promptKeywords:
    primary: [3d, bubbly, tech, pillow-shape, inflated, plastic, glossy, pastel]
    material: ["inflated plastic", "soft pillow form", "glossy lacquer"]
    line: ["no line"]
    color: ["pastel gradient", "lilac to mint", "bubblegum pink accent"]
    style: ["floating composition", "studio bg", "isometric or 3/4 view"]
    avoidKeywords: [sharp edge, photoreal device, hairline detail, metal chrome]
  namedReferences:
    illustrators: [DrawKit]
    movements: [post-claymorphism tech aesthetic]
    productsOrFilms: [Notion-era SaaS marketing 2022-2024]
  examplePromptTemplate: |
    3D bubbly tech illustration of a laptop with chat bubble, inflated pillow forms,
    pastel lilac-to-mint gradient surfaces, glossy plastic lacquer finish, soft pink
    accent floating bubbles, 3/4 isometric view, studio lighting on pale lavender
    background, soft contact shadow, no hard edges, octane render quality.
  whenToUse: SaaS hero or feature-block where you want to show product capability
    without showing the product literally. Pairs with style-claymorphism heroes and
    bento-marketing recipes.
  pairsWith:
    prototypeStyles: [style-claymorphism, recipe-bento-marketing, recipe-restrained-ai-marketing, style-neumorphism]
  notForUseWhen: dev-tools marketing wanting credibility, terminal-on-web

- styleId: drawkit-wooden-icons
  name: DrawKit Wooden Icons 3D
  category: 3D
  subCategory: wood-craft
  role: spot-illustration
  source: drawkit.com/illustration-types/3d (Wooden Icons)
  visualSignatures:
    - hand-carved beech / pine grain visible on every surface
    - all forms simplified to wood-block shapes joined by visible seams
    - natural sap/honey/walnut palette only
    - matte studio light, no specular
  promptKeywords:
    primary: [3d, wooden, carved, craft, handmade, grain, matte, natural]
    material: ["beech wood", "pine grain", "hand-carved", "matte sealed timber"]
    line: ["no line, joined by carved seam"]
    color: ["honey beech", "walnut", "natural unstained timber"]
    style: ["studio diffuse light", "soft shadow on cream"]
    avoidKeywords: [plastic, neon, glossy, gradient]
  namedReferences:
    illustrators: [DrawKit, House Industries wooden blocks]
    movements: [Solarpunk craft]
    productsOrFilms: [Areaware wooden toys, Eames House Bird]
  examplePromptTemplate: |
    3D wooden craft icon of a [SUBJECT], hand-carved beech with visible grain,
    simplified block forms joined by carved seams, natural honey-to-walnut palette,
    matte sealed timber finish, soft studio diffuse light on warm cream background,
    soft contact shadow, no specular, artisanal quality.
  whenToUse: Cottagecore, solarpunk, warm-restraint, dark-academia — anything that
    wants to whisper "natural, slow, made-by-hand."
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-solarpunk, recipe-warm-restraint, aesthetic-dark-academia, aesthetic-coastal-grandmother]
  notForUseWhen: crypto-degen, cyberpunk, RGB gamer

- styleId: drawkit-hands-3d
  name: DrawKit Hands Illustrations
  category: 3D
  subCategory: render-cinematic
  role: spot-illustration
  source: drawkit.com/illustration-types/3d (Hands Illustrations)
  visualSignatures:
    - anatomically simplified but realistically lit hand renders
    - holding objects in mid-air with explicit purpose
    - skin tones with subsurface scattering
    - neutral cream or grey studio bg
  promptKeywords:
    primary: [3d, hand, render, holding, gesture, cinematic]
    material: ["soft skin shader", "subsurface scattering", "matte fingernail"]
    line: ["no line"]
    color: ["neutral skin tone", "muted background"]
    style: ["studio cinematic light", "shallow depth of field"]
    avoidKeywords: [cartoon glove, mickey-mouse hand, mitten]
  namedReferences:
    illustrators: [DrawKit]
    movements: [Apple keynote product showcase]
    productsOrFilms: [Apple Vision Pro hand gestures marketing]
  examplePromptTemplate: |
    3D photoreal-stylized hand holding [SUBJECT], anatomically simplified but
    cinematically lit with soft skin shader and subsurface scattering, neutral
    cream studio background, shallow depth of field, Apple-keynote quality
    rendering, soft contact shadow, single light source from upper left.
  whenToUse: Premium tech marketing, AI demo heroes, when you want to show
    "this product is for humans" but with restraint.
  pairsWith:
    prototypeStyles: [recipe-restrained-ai-marketing, style-liquid-glass, style-sf-pro-ios, recipe-ios-system]
  notForUseWhen: cartoon contexts, brutalism, dense data UI

- styleId: drawkit-isometric-stickers
  name: DrawKit / Blush Isometric Stickers
  category: 3D
  subCategory: isometric-tech
  role: spot-illustration
  source: drawkit + blush.design (Isometric Stickers by Mariana Gonzalez Vega)
  visualSignatures:
    - everyday objects (laptop, coffee, book) in true 2:1 isometric
    - flat color fills with a single highlight stroke
    - white outline halo around the whole sticker
    - drop shadow detached from the object
  promptKeywords:
    primary: [isometric, sticker, 30-degree, flat-shaded, white halo]
    material: ["flat-shaded plastic"]
    line: ["white halo outline 6px"]
    color: ["pastel + one saturated accent"]
    style: ["sticker pack composition", "drop shadow"]
    avoidKeywords: [perspective, vanishing point, photorealism]
  namedReferences:
    illustrators: [Mariana Gonzalez Vega]
    movements: [2.5D SaaS marketing]
    productsOrFilms: [Notion, Asana feature illustrations]
  examplePromptTemplate: |
    Isometric sticker of [SUBJECT] at 30-degree axonometric angle, flat-shaded
    plastic surfaces with single highlight stroke per facet, 6px white halo
    outline around the entire form, detached drop shadow at 15% opacity, pastel
    palette with one saturated accent color, isolated on neutral background.
  whenToUse: B2B SaaS where the product needs to be cute but legible, Notion-era
    feature blocks, onboarding state illos.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-linear-product-ui, aesthetic-positivity-kawaii]
  notForUseWhen: editorial magazine, brutalism, dark cinematic UI

### 2.2 — Blush Design collections (source: blush.design/collections)

- styleId: blush-humaaans
  name: Humaaans
  category: Flat vector
  subCategory: noodle-people
  role: subject
  source: blush.design — Humaaans by Pablo Stanley
  visualSignatures:
    - rigid geometric torso + modular limbs that snap together
    - flat color, zero shading, no line
    - diverse skin tones, faceless heads (just hair shape)
    - figures stand alone or in 2-3 person groupings on flat color bg
  promptKeywords:
    primary: [flat vector, modular character, faceless, geometric body, diverse]
    material: ["flat fill", "no texture"]
    line: ["no line"]
    color: ["muted modern palette", "earth-tone skin + accent clothing"]
    style: ["isolated figure", "no background detail"]
    avoidKeywords: [3D, shading, gradient, facial expression]
  namedReferences:
    illustrators: [Pablo Stanley]
    movements: [Inclusive flat-vector wave 2019+]
    productsOrFilms: [Twilio docs, Mailchimp empty states]
  examplePromptTemplate: |
    Flat vector illustration of a single human figure, modular geometric body,
    faceless head with simple hair silhouette, flat solid color clothing in
    earth-tone palette with one accent pop, no line, no shading, no background,
    standing in casual pose, Pablo Stanley Humaaans style.
  whenToUse: Inclusive product surfaces, empty states, status pages, where you
    need a person but want zero personality projection.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-restrained-ai-marketing, aesthetic-corporate-memphis, recipe-linear-product-ui]
  notForUseWhen: editorial, brutalism, anything emotive

- styleId: blush-open-peeps
  name: Open Peeps
  category: Hand-drawn / sketch
  subCategory: ink-line-brush
  role: subject
  source: blush.design — Open Peeps by Pablo Stanley
  visualSignatures:
    - all forms drawn with 4-6px wobbly black brush line
    - white or off-white fill only — never colored
    - characters mix and match modular hair, body, expression
    - warm imperfect line wobble suggests human hand
  promptKeywords:
    primary: [hand-drawn, brush line, black-and-white, modular character, peeps]
    material: ["ink on white paper", "uncolored fills"]
    line: ["wobbly brush line 5px", "imperfect"]
    color: ["pure black on cream", "no color fill"]
    style: ["modular pose", "isolated figure"]
    avoidKeywords: [color fill, perfect line, vector polish, 3d]
  namedReferences:
    illustrators: [Pablo Stanley]
    movements: [hand-drawn revival 2019]
    productsOrFilms: [Sketch app marketing, indie SaaS blog headers]
  examplePromptTemplate: |
    Hand-drawn character in Open Peeps style, drawn with wobbly 5px black brush
    line on cream paper, white interior fills no color, modular hair and clothing,
    expressive natural pose, imperfect human line quality, isolated subject,
    Pablo Stanley aesthetic.
  whenToUse: When a corporate-Memphis surface needs a warmer alternative; blogs,
    indie startups, documentation that wants to feel made-by-a-person.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-readcv, recipe-editorial-magazine, aesthetic-cottagecore]
  notForUseWhen: cinematic 3D contexts, brutalism, dense data UI

- styleId: blush-wavy-buddies
  name: Wavy Buddies
  category: Hand-drawn / sketch
  subCategory: ink-line-brush
  role: subject
  source: blush.design — Wavy Buddies by Susana Salas
  visualSignatures:
    - everything is a wavy curving line — limbs, hair, shadows
    - characters mid-action: shopping, scrolling, dancing
    - bright primary fills behind black wobble line
    - frequent ecommerce / lifestyle subject matter
  promptKeywords:
    primary: [doodle, wavy line, character, lifestyle, ecommerce]
    material: ["brush ink + flat color fill"]
    line: ["wavy black 4px line"]
    color: ["bright primary on cream"]
    style: ["mid-action figure", "playful"]
    avoidKeywords: [straight line, 3d, photoreal]
  namedReferences:
    illustrators: [Susana Salas]
    movements: [Doodle-vector hybrid]
    productsOrFilms: [Shopify partner marketing]
  examplePromptTemplate: |
    Hand-drawn character mid-action shopping, every line is wavy and curving
    including limbs and hair, 4px black brush line outline, flat bright primary
    color fills behind line, cream background, playful Susana Salas Wavy Buddies
    style, isolated subject.
  whenToUse: Ecommerce empty states, lifestyle content, content blog headers
    that want movement and personality.
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-curly-girly, aesthetic-positivity-kawaii]
  notForUseWhen: B2B serious, brutalism, financial dashboards

- styleId: blush-cool-kids
  name: Cool Kids
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — Cool Kids by Irene Falgueras
  visualSignatures:
    - bold abstract patterns on clothing (checkerboard, stripes, dots)
    - vibrant saturated palette with high contrast
    - chunky simplified bodies
    - dynamic poses, characters lean and tilt
  promptKeywords:
    primary: [flat vector, bold pattern, vibrant, character, chunky, dynamic]
    material: ["flat fill with overlaid pattern"]
    line: ["no line, color blocks"]
    color: ["saturated bold contrast — fuchsia + teal + yellow"]
    style: ["dynamic tilted pose", "abstract patterned clothing"]
    avoidKeywords: [muted, pastel, faceless modular]
  namedReferences:
    illustrators: [Irene Falgueras]
    movements: [Maximalist flat-vector]
    productsOrFilms: [Spotify Wrapped era illustrations]
  examplePromptTemplate: |
    Flat vector character with chunky simplified body in dynamic tilted pose,
    clothing covered in bold abstract patterns — checkerboard stripes and dots —
    vibrant saturated palette of fuchsia teal and yellow, high contrast, no
    outline, Irene Falgueras Cool Kids aesthetic.
  whenToUse: Music, culture, youth-targeted product — when you want personality
    over neutrality.
  pairsWith:
    prototypeStyles: [aesthetic-maximalism, aesthetic-y2k-memphis-loud, aesthetic-positivity-kawaii, aesthetic-acid-design]
  notForUseWhen: enterprise, serious finance, restrained AI marketing

- styleId: blush-fancy-plants
  name: Fancy Plants
  category: Hand-drawn / sketch
  subCategory: gouache
  role: decoration
  source: blush.design — Fancy Plants by Susana Ortiz
  visualSignatures:
    - hand-painted plants in terracotta or ceramic pots
    - gouache-like matte texture with visible brush
    - soft earth-tone palette — sage, terracotta, cream
    - no characters, just botanical objects
  promptKeywords:
    primary: [hand-painted, plant, pot, gouache, botanical, matte]
    material: ["gouache matte", "subtle brush texture"]
    line: ["no line, painted edge"]
    color: ["sage green", "terracotta", "warm cream"]
    style: ["spot illustration", "isolated object"]
    avoidKeywords: [vector flat, 3d, photoreal]
  namedReferences:
    illustrators: [Susana Ortiz]
    movements: [Cottagecore botanical illustration]
    productsOrFilms: [The Sill marketing, plant-care apps]
  examplePromptTemplate: |
    Hand-painted gouache illustration of a houseplant in terracotta pot, matte
    chalky finish with subtle brush texture, sage-green leaves and warm cream
    background, no outline, painted edge quality, isolated as spot illustration,
    Susana Ortiz Fancy Plants style.
  whenToUse: Cottagecore, wellness brands, plant care, food editorial, cozy
    lifestyle content.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-solarpunk, aesthetic-coastal-grandmother, recipe-warm-restraint]
  notForUseWhen: tech, finance, anything cool-toned

- styleId: blush-hyperspace
  name: Hyperspace
  category: Flat vector
  subCategory: geometric-mid-century
  role: spot-illustration
  source: blush.design — Hyperspace by Mathew Wong
  visualSignatures:
    - retro-futurist space doodles: rockets, planets, astronauts
    - flat 60s sci-fi palette: orange, teal, mustard
    - thick rounded forms with subtle line texture
    - composition often diagonal — things flying
  promptKeywords:
    primary: [retro-futurist, space, doodle, mid-century, flat, planet, rocket]
    material: ["flat fill + light grain texture"]
    line: ["thick rounded line 3px"]
    color: ["mid-century orange teal mustard"]
    style: ["diagonal motion", "spot illustration"]
    avoidKeywords: [photoreal space, 3d render, neon cyber]
  namedReferences:
    illustrators: [Mathew Wong]
    movements: [Mid-century Atomic Age revival]
    productsOrFilms: [Saul Bass-adjacent, Atompunk]
  examplePromptTemplate: |
    Retro-futurist mid-century illustration of a rocket and planet, thick rounded
    flat shapes with subtle paper grain, palette of mid-century orange teal and
    mustard, 3px rounded line, diagonal flying composition, Mathew Wong Hyperspace
    aesthetic, spot illustration on cream.
  whenToUse: When you want retro-cool, atompunk, or playful tech without going Y2K.
  pairsWith:
    prototypeStyles: [aesthetic-atompunk, aesthetic-cassette-futurism, aesthetic-frutiger-eco]
  notForUseWhen: photoreal, dense data UI

- styleId: blush-moneyverse
  name: Moneyverse
  category: Flat vector
  subCategory: geometric-mid-century
  role: spot-illustration
  source: blush.design — Moneyverse by Pau Barbaro
  visualSignatures:
    - money/finance objects in cosmic context (bitcoins flying through space)
    - same retro-futurist palette as Hyperspace
    - playful absurd compositions
  promptKeywords:
    primary: [retro, finance, cosmic, doodle, fintech]
    material: ["flat fill + grain"]
    line: ["rounded 3px"]
    color: ["mid-century orange teal mustard + gold accent"]
    style: ["absurd cosmic composition"]
    avoidKeywords: [photoreal currency, 3d coin]
  namedReferences:
    illustrators: [Pau Barbaro]
    movements: [Crypto-doodle 2021]
  examplePromptTemplate: |
    Retro-futurist flat illustration of bitcoins flying through cosmic space,
    rounded thick shapes with subtle paper grain texture, mid-century palette of
    orange teal mustard with gold coin accent, playful absurd composition, Pau
    Barbaro Moneyverse style, isolated on cream.
  whenToUse: Friendly fintech, crypto-onramp products, finance blog headers.
  pairsWith:
    prototypeStyles: [aesthetic-defi-cosmic, aesthetic-crypto-degen, recipe-bento-marketing]
  notForUseWhen: serious financial dashboards, Bloomberg

- styleId: blush-currency-crush
  name: Currency Crush
  category: Flat vector
  subCategory: flat-iconographic
  role: decoration
  source: blush.design — Currency Crush by Gustavo Pedrosa
  visualSignatures:
    - cute stylized cash, coins, cards as flat icons
    - candy-color palette — pink, mint, lavender
    - chunky friendly forms, slight 3D pillow shading
    - sticker-style with white halo optional
  promptKeywords:
    primary: [finance, sticker, cute, flat, candy-color]
    material: ["flat fill with slight pillow shade"]
    line: ["soft 2px line optional"]
    color: ["candy pink mint lavender"]
    style: ["icon sticker", "isolated"]
    avoidKeywords: [photoreal cash, gold metallic]
  namedReferences:
    illustrators: [Gustavo Pedrosa]
  examplePromptTemplate: |
    Cute flat icon illustration of a dollar bill, chunky friendly form with
    subtle pillow shading, candy palette of pink mint and lavender, sticker
    style with optional white halo, Gustavo Pedrosa Currency Crush aesthetic.
  whenToUse: Consumer fintech onboarding, neobank, friendly money UI.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, recipe-bento-marketing, style-claymorphism]
  notForUseWhen: institutional finance, brutalism

- styleId: blush-allura
  name: Allura
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Allura by Vijay Verma
  visualSignatures:
    - everyday-life scenes (office, park, walking)
    - clean vector with rounded extremities
    - muted earth + dusty pink palette
    - distinct head-shape variety
  promptKeywords:
    primary: [flat vector, everyday-life, character, dusty palette]
    material: ["flat fill"]
    line: ["no line"]
    color: ["muted dusty pink + sage + cream"]
    style: ["scene composition with bg"]
    avoidKeywords: [bright saturated, pattern-heavy]
  namedReferences:
    illustrators: [Vijay Verma]
  examplePromptTemplate: |
    Flat vector everyday-life scene of [SUBJECT], clean rounded vector characters,
    muted dusty palette of pink sage and cream, simple background with one prop,
    Vijay Verma Allura aesthetic, friendly creative storytelling.
  whenToUse: Blog headers, content marketing for lifestyle / wellness SaaS.
  pairsWith:
    prototypeStyles: [aesthetic-corporate-memphis, recipe-bento-marketing, recipe-warm-restraint, aesthetic-coastal-grandmother]
  notForUseWhen: youth-music brands, brutalism

- styleId: blush-tutto-ricco
  name: Tutto Ricco
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — Tutto Ricco by Jorge Margarido
  visualSignatures:
    - sleek confident characters with bouncy pink dogs
    - vivid doodle accents around them
    - cosmopolitan palette — pink, navy, gold
    - composition feels editorial, fashion-y
  promptKeywords:
    primary: [flat vector, sleek, fashion, character, vivid doodle]
    material: ["flat fill + doodle overlay"]
    line: ["selective doodle line accents"]
    color: ["hot pink navy gold"]
    style: ["fashion editorial", "confident pose"]
    avoidKeywords: [cute kawaii, muted]
  namedReferences:
    illustrators: [Jorge Margarido]
  examplePromptTemplate: |
    Sleek confident flat vector character in fashion editorial pose with bouncy
    pink dog at heel, vivid doodle accents floating around, palette of hot pink
    navy and gold, Jorge Margarido Tutto Ricco style, no outline, isolated.
  whenToUse: Fashion ecommerce, lifestyle apps with attitude, beauty brand blogs.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-memphis-loud, aesthetic-curly-girly, aesthetic-maximalism]
  notForUseWhen: B2B serious

- styleId: blush-dayflow
  name: Dayflow
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Dayflow by Pau Barbaro
  visualSignatures:
    - daily-life micro-moments (coffee, cat, books)
    - soft pastel palette with cream base
    - cats are recurring motif
    - characters with simple dot eyes
  promptKeywords:
    primary: [flat vector, daily-life, pastel, cat, positivity]
    material: ["flat fill, light grain"]
    line: ["no line"]
    color: ["pastel peach mint lilac cream"]
    style: ["small intimate scene"]
    avoidKeywords: [intense color, dramatic action]
  namedReferences:
    illustrators: [Pau Barbaro]
  examplePromptTemplate: |
    Flat vector small intimate scene of a person with cat and coffee, pastel
    palette of peach mint lilac on cream, simple dot eyes on character, light
    grain texture, Pau Barbaro Dayflow positivity aesthetic, no outline.
  whenToUse: Wellness apps, journaling, gratitude content, cozy SaaS.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, aesthetic-cottagecore, aesthetic-coastal-grandmother, recipe-readcv]
  notForUseWhen: enterprise, technical, dark themes

- styleId: blush-yuppies
  name: Yuppies
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Yuppies by Irene Falgueras
  visualSignatures:
    - polished modern characters with relatable office scenes
    - high-quality vector with thoughtful component logic
    - sophisticated muted palette
    - explicit UI-friendly composition (isolated, ready to drop in)
  promptKeywords:
    primary: [flat vector, modern, refined, character, office, scene]
    material: ["flat fill, no texture"]
    line: ["no line, subtle internal detail"]
    color: ["muted sage rust cream taupe"]
    style: ["UI-ready isolated scene"]
    avoidKeywords: [maximal pattern, neon, cute kawaii]
  namedReferences:
    illustrators: [Irene Falgueras]
  examplePromptTemplate: |
    Refined modern flat vector character in office scene, polished friendly
    pose, sophisticated muted palette of sage rust cream and taupe, no outline
    with subtle internal detail lines, UI-ready isolated composition, Irene
    Falgueras Yuppies aesthetic.
  whenToUse: Productivity SaaS, B2B with personality, onboarding flows.
  pairsWith:
    prototypeStyles: [recipe-linear-product-ui, recipe-bento-marketing, recipe-restrained-ai-marketing]
  notForUseWhen: editorial, brutalism, youth-music

- styleId: blush-palz
  name: Palz
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Palz by Ana Copenicker
  visualSignatures:
    - modern characters with fun colors + simple abstract shape accents
    - rounded chunky bodies, simple dot eyes
    - friendly palette but with vibrant pop accents
  promptKeywords:
    primary: [flat vector, character, fun-color, abstract-accent]
    material: ["flat fill"]
    line: ["no line"]
    color: ["mid saturation + accent pop"]
    style: ["isolated with floating shapes"]
    avoidKeywords: [muted, photoreal]
  namedReferences:
    illustrators: [Ana Copenicker]
  examplePromptTemplate: |
    Modern flat vector character with rounded chunky body, simple dot eyes,
    surrounded by floating abstract geometric shape accents, fun mid-saturation
    palette with one vibrant pop color, Ana Copenicker Palz aesthetic.
  whenToUse: Consumer apps wanting friendly approachable feel.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis, recipe-bento-marketing]
  notForUseWhen: editorial, brutalism

- styleId: blush-croods
  name: Croods
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — Croods by Vijay Verma
  visualSignatures:
    - vibrant bold-color characters with strong expressive faces
    - actually has facial expressions (unlike Humaaans)
    - dynamic action poses
  promptKeywords:
    primary: [flat vector, bold color, expressive face, dynamic]
    material: ["flat fill"]
    line: ["no line"]
    color: ["bold saturated"]
    style: ["expressive face", "action pose"]
    avoidKeywords: [faceless, muted, static]
  namedReferences:
    illustrators: [Vijay Verma]
  examplePromptTemplate: |
    Vibrant flat vector character with expressive face and dynamic action pose,
    bold saturated palette, fully formed facial features unlike noodle-people,
    Vijay Verma Croods aesthetic, isolated subject.
  whenToUse: When corporate-Memphis fatigue hits — needs an expressive face but
    still vector.
  pairsWith:
    prototypeStyles: [aesthetic-maximalism, aesthetic-positivity-kawaii, aesthetic-y2k-memphis-loud]
  notForUseWhen: restrained AI marketing, brutalism

- styleId: blush-family-values
  name: Family Values
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Family Values by Veronica Iezzi
  visualSignatures:
    - groups of 2-4 figures sharing moments
    - warm earth palette
    - clear family/intimate-group composition
  promptKeywords:
    primary: [flat vector, family, group, warm-palette]
    material: ["flat fill"]
    line: ["no line"]
    color: ["warm earth — rust ochre cream"]
    style: ["multi-figure intimate scene"]
    avoidKeywords: [single figure, cold palette]
  namedReferences:
    illustrators: [Veronica Iezzi]
  examplePromptTemplate: |
    Flat vector scene of 3 figures sharing intimate moment, warm earth palette
    of rust ochre and cream, no outline, friendly faces, Veronica Iezzi Family
    Values aesthetic.
  whenToUse: Healthcare, family services, community products.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, aesthetic-corporate-memphis, aesthetic-coastal-grandmother]
  notForUseWhen: solo-product hero

- styleId: blush-power-moves
  name: Power Moves
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — Power Moves by Isabela Humphrey
  visualSignatures:
    - bright colors, bold patterns, fierce style
    - mix of color backgrounds + character splash
    - confident attitude poses
  promptKeywords:
    primary: [flat vector, bright, bold pattern, fierce, attitude]
    material: ["flat fill + bold pattern"]
    line: ["no line"]
    color: ["bright fuchsia electric blue yellow"]
    style: ["confident pose", "bold bg"]
    avoidKeywords: [muted, soft]
  namedReferences:
    illustrators: [Isabela Humphrey]
  examplePromptTemplate: |
    Bold flat vector character in fierce confident pose, bright palette of
    fuchsia electric blue and yellow, bold geometric patterns in clothing and
    background, Isabela Humphrey Power Moves aesthetic.
  whenToUse: Women-empowerment, beauty, athleisure, music branding.
  pairsWith:
    prototypeStyles: [aesthetic-maximalism, aesthetic-y2k-memphis-loud, aesthetic-acid-design]
  notForUseWhen: B2B serious, restrained AI

- styleId: blush-cityscapes
  name: Cityscapes
  category: Flat vector
  subCategory: geometric-mid-century
  role: decoration
  source: blush.design — Cityscapes by Pablo Stanley
  visualSignatures:
    - towns, cities, hilly landscapes
    - flat vector buildings, no perspective
    - muted modern palette with one accent
    - background-decoration role
  promptKeywords:
    primary: [flat vector, cityscape, landscape, building, scene background]
    material: ["flat fill"]
    line: ["no line, color blocks"]
    color: ["muted modern + one accent"]
    style: ["wide horizontal landscape"]
    avoidKeywords: [perspective, photoreal city, 3d]
  namedReferences:
    illustrators: [Pablo Stanley]
  examplePromptTemplate: |
    Flat vector cityscape landscape with buildings and hills, no perspective,
    muted modern palette of beige sage and dusty pink with one accent color,
    wide horizontal composition for background decoration use, Pablo Stanley
    Cityscapes aesthetic.
  whenToUse: As background bands for marketing pages; hero sub-scene.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-restrained-ai-marketing, aesthetic-corporate-memphis]
  notForUseWhen: brutalism, editorial

- styleId: blush-stuck-at-home
  name: Stuck at Home
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Stuck at Home by Mariana Gonzalez Vega
  visualSignatures:
    - domestic daily-life scenes during lockdown
    - small interior vignettes
    - cozy muted palette
  promptKeywords:
    primary: [flat vector, domestic, interior, daily life, cozy]
    material: ["flat fill"]
    line: ["no line"]
    color: ["cozy muted — peach lavender sage"]
    style: ["interior vignette"]
    avoidKeywords: [outdoor, bright]
  namedReferences:
    illustrators: [Mariana Gonzalez Vega]
  examplePromptTemplate: |
    Flat vector cozy domestic interior scene with figure on couch with book,
    palette of peach lavender and sage, small intimate vignette composition,
    no outline, Mariana Gonzalez Vega Stuck at Home aesthetic.
  whenToUse: WFH product marketing, journaling, wellness, home decor apps.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, aesthetic-cottagecore, aesthetic-coastal-grandmother]
  notForUseWhen: outdoor/adventure, brutalism

- styleId: blush-happy-bunch
  name: Happy Bunch
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — Happy Bunch by Pablo Stanley
  visualSignatures:
    - bouncy characters mid-action
    - dope poses, slightly comic exaggeration
    - bright friendly palette
  promptKeywords:
    primary: [flat vector, bouncy, character, energetic, dope]
    material: ["flat fill"]
    line: ["no line"]
    color: ["bright friendly"]
    style: ["bouncy action pose"]
    avoidKeywords: [static, muted]
  namedReferences:
    illustrators: [Pablo Stanley]
  examplePromptTemplate: |
    Bouncy flat vector character mid-action in dope energetic pose, bright
    friendly palette, comic exaggeration, no outline, Pablo Stanley Happy
    Bunch aesthetic.
  whenToUse: When your brand voice is "good vibes."
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis]
  notForUseWhen: serious enterprise

- styleId: blush-shopaholics
  name: Shopaholics
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Shopaholics by Veronica Iezzi
  visualSignatures:
    - e-commerce + retail scenes
    - shopping bags, carts, browsing
    - friendly muted palette
  promptKeywords:
    primary: [flat vector, ecommerce, shopping, retail, character]
    material: ["flat fill"]
    line: ["no line"]
    color: ["friendly muted"]
    style: ["retail scene"]
    avoidKeywords: [photoreal product]
  namedReferences:
    illustrators: [Veronica Iezzi]
  examplePromptTemplate: |
    Flat vector character with shopping bags browsing retail, friendly muted
    palette, no outline, Veronica Iezzi Shopaholics ecommerce aesthetic.
  whenToUse: Ecommerce empty states, checkout flows, retail SaaS.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, aesthetic-corporate-memphis]
  notForUseWhen: B2B serious, editorial

- styleId: blush-hobbies
  name: Hobbies
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Hobbies by Jal Reed
  visualSignatures:
    - characters doing favorite activities (weight lifting, skateboarding, dancing, travel)
    - active poses, mid-motion
    - friendly bright palette
  promptKeywords:
    primary: [flat vector, hobby, activity, dynamic, lifestyle]
    material: ["flat fill"]
    line: ["no line"]
    color: ["bright friendly"]
    style: ["mid-motion action"]
    avoidKeywords: [static]
  namedReferences:
    illustrators: [Jal Reed]
  examplePromptTemplate: |
    Flat vector character doing a hobby (skateboarding), mid-motion action pose,
    bright friendly palette, no outline, Jal Reed Hobbies aesthetic.
  whenToUse: Lifestyle apps, fitness, hobby-marketplace SaaS.
  pairsWith:
    prototypeStyles: [aesthetic-corporate-memphis, aesthetic-positivity-kawaii, recipe-bento-marketing]
  notForUseWhen: enterprise

- styleId: blush-shiny-happy
  name: Shiny Happy
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Shiny Happy by Brandon Mendoza
  visualSignatures:
    - shiny happy people holding hands and laughing
    - bright joyful palette
    - inclusive group compositions
  promptKeywords:
    primary: [flat vector, joyful, group, inclusive, bright]
    material: ["flat fill"]
    line: ["no line"]
    color: ["bright sunny"]
    style: ["group composition", "laughter"]
    avoidKeywords: [dramatic, dark]
  namedReferences:
    illustrators: [Brandon Mendoza]
  examplePromptTemplate: |
    Joyful flat vector group of people holding hands and laughing, bright sunny
    palette, inclusive diverse composition, no outline, Brandon Mendoza Shiny
    Happy aesthetic.
  whenToUse: Community, social impact, celebration marketing.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis]
  notForUseWhen: dark themes, brutalism

- styleId: blush-big-shoes
  name: Big Shoes
  category: Flat vector
  subCategory: flat-iconographic
  role: subject
  source: blush.design — Big Shoes by Elina Cecilia Giglio
  visualSignatures:
    - exaggerated big-shoe characters (oversized footwear)
    - playful proportions
    - friendly mid-saturation palette
  promptKeywords:
    primary: [flat vector, exaggerated shoe, playful proportion, friendly]
    material: ["flat fill"]
    line: ["thin 2px optional"]
    color: ["mid-saturation friendly"]
    style: ["exaggerated proportion"]
    avoidKeywords: [realistic anatomy]
  namedReferences:
    illustrators: [Elina Cecilia Giglio]
  examplePromptTemplate: |
    Flat vector character with exaggerated oversized shoes, playful disproportionate
    body, friendly mid-saturation palette, optional thin 2px outline, Elina Cecilia
    Giglio Big Shoes aesthetic.
  whenToUse: Sneakers, fashion, playful lifestyle brands.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis]
  notForUseWhen: B2B serious

- styleId: blush-fitz
  name: Fitz
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — Fitz by Ana Copenicker
  visualSignatures:
    - sports characters (basketball, baseball, soccer)
    - athletic active poses
    - team-uniform color palettes
  promptKeywords:
    primary: [flat vector, sport, athlete, dynamic, athletic]
    material: ["flat fill"]
    line: ["no line"]
    color: ["team-uniform brights"]
    style: ["athletic action"]
    avoidKeywords: [static, muted]
  namedReferences:
    illustrators: [Ana Copenicker]
  examplePromptTemplate: |
    Flat vector athlete mid-action playing basketball, team uniform bright
    palette, dynamic athletic pose, no outline, Ana Copenicker Fitz aesthetic.
  whenToUse: Sports apps, fitness, team SaaS.
  pairsWith:
    prototypeStyles: [aesthetic-corporate-memphis, aesthetic-positivity-kawaii]
  notForUseWhen: editorial

- styleId: blush-go-green
  name: Go Green
  category: Flat vector
  subCategory: corporate-memphis
  role: spot-illustration
  source: blush.design — Go Green by Edward Tapia
  visualSignatures:
    - eco-doodles: trees, recycling, solar panels
    - sage / forest green dominant palette
    - simple flat shapes
  promptKeywords:
    primary: [flat vector, eco, sustainability, green, doodle]
    material: ["flat fill"]
    line: ["no line or subtle 2px"]
    color: ["sage forest green + warm cream + sky blue"]
    style: ["eco spot illustration"]
    avoidKeywords: [neon, dark, dystopian]
  namedReferences:
    illustrators: [Edward Tapia]
  examplePromptTemplate: |
    Flat vector eco illustration of a tree with solar panels and recycling
    motif, sage forest green palette with cream and sky blue accents, friendly
    simple shapes, Edward Tapia Go Green aesthetic.
  whenToUse: Sustainability brands, climate-tech, solarpunk-adjacent.
  pairsWith:
    prototypeStyles: [aesthetic-solarpunk, aesthetic-frutiger-eco, aesthetic-cottagecore]
  notForUseWhen: edgy, brutalism, neon

- styleId: blush-isometric-stickers-vega
  name: Blush Isometric Stickers (Mariana Gonzalez Vega)
  category: 3D
  subCategory: isometric-tech
  role: spot-illustration
  source: blush.design — Isometric Stickers by Mariana Gonzalez Vega
  visualSignatures:
    - everyday isometric objects with white halo
    - 60+ items: books, coffee, pencil, laptop, spaceship
    - flat-shaded pastel + accent
  promptKeywords:
    primary: [isometric, sticker, everyday object, white halo, pastel]
    material: ["flat-shaded plastic"]
    line: ["white halo 6px"]
    color: ["pastel + saturated accent"]
    style: ["sticker isolated"]
    avoidKeywords: [perspective, photoreal]
  namedReferences:
    illustrators: [Mariana Gonzalez Vega]
  examplePromptTemplate: |
    Isometric sticker of [SUBJECT], 30-degree angle, flat-shaded surfaces,
    6px white halo outline, pastel palette with saturated accent, isolated on
    neutral bg, Mariana Gonzalez Vega Blush isometric aesthetic.
  whenToUse: Same as drawkit-isometric-stickers; tighter sticker-pack feel.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-linear-product-ui, aesthetic-positivity-kawaii]
  notForUseWhen: editorial, brutalism

- styleId: blush-we-are-women
  name: We Are Women
  category: Flat vector
  subCategory: flat-with-pattern
  role: subject
  source: blush.design — We Are Women (Mariana Gonzalez Vega + collaborators)
  visualSignatures:
    - diverse female + non-binary figures
    - empowerment imagery with bold colors
    - inclusive composition with multiple skin tones
  promptKeywords:
    primary: [flat vector, women, empowerment, diverse, inclusive]
    material: ["flat fill"]
    line: ["no line"]
    color: ["bold saturated"]
    style: ["diverse group"]
    avoidKeywords: [stereotyped, muted]
  namedReferences:
    illustrators: [Mariana Gonzalez Vega + team]
  examplePromptTemplate: |
    Flat vector diverse group of women and non-binary figures in empowerment
    pose, bold saturated palette, inclusive composition with varied skin tones
    and body types, no outline, Blush We Are Women aesthetic.
  whenToUse: International Women's Day, equality campaigns, social-impact brands.
  pairsWith:
    prototypeStyles: [aesthetic-corporate-memphis, aesthetic-maximalism]
  notForUseWhen: B2B technical

- styleId: blush-little-things
  name: The Little Things
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: blush.design — The Little Things by Susana Salas
  visualSignatures:
    - cozy small joys: coffee, books, popcorn
    - warm cream + muted accent palette
    - intimate vignette compositions
  promptKeywords:
    primary: [flat vector, cozy, small joy, intimate, vignette]
    material: ["flat fill"]
    line: ["no line"]
    color: ["warm cream + dusty accent"]
    style: ["intimate vignette"]
    avoidKeywords: [grand, dramatic]
  namedReferences:
    illustrators: [Susana Salas]
  examplePromptTemplate: |
    Cozy flat vector intimate vignette of coffee and book on table, warm cream
    palette with dusty pink accent, small joyful composition, Susana Salas Little
    Things aesthetic.
  whenToUse: Wellness, journaling, lifestyle blogs.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, aesthetic-cottagecore, recipe-readcv]
  notForUseWhen: B2B technical

- styleId: blush-transhumans
  name: Transhumans
  category: 3D
  subCategory: plastic-glossy
  role: subject
  source: blush.design — Transhumans by Pablo Stanley
  visualSignatures:
    - characters transcending biological limits — cyborg parts, robot heads
    - glossy 3D-ish plastic look (technically flat but reads dimensional)
    - futurist saturated palette — magenta + cyan
  promptKeywords:
    primary: [transhuman, cyborg, plastic, futurist, sticker]
    material: ["glossy plastic shading"]
    line: ["subtle 1px highlight"]
    color: ["magenta cyan electric futurist"]
    style: ["sticker isolated"]
    avoidKeywords: [organic only, muted]
  namedReferences:
    illustrators: [Pablo Stanley]
  examplePromptTemplate: |
    Stylized 3D-ish flat vector character with cyborg elements (robotic arm,
    visor), glossy plastic shading with subtle 1px highlights, electric magenta
    and cyan futurist palette, sticker style isolated, Pablo Stanley Transhumans
    aesthetic.
  whenToUse: AI products, futurism marketing, cyberpunk-adjacent positive UX.
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-y2k-futurism, aesthetic-vaporwave]
  notForUseWhen: cottagecore, editorial

- styleId: blush-lifesavers
  name: Lifesavers
  category: Flat vector
  subCategory: flat-iconographic
  role: spot-illustration
  source: blush.design — Lifesavers by Deivid Saenz
  visualSignatures:
    - medical objects: organs, bones, pills, wheelchairs
    - clean medical illustration look
    - clinical palette with friendly warmth
  promptKeywords:
    primary: [medical, flat vector, organ, healthcare, friendly clinical]
    material: ["flat fill"]
    line: ["no line"]
    color: ["clinical white + soft pink + sage"]
    style: ["medical iconography"]
    avoidKeywords: [photoreal anatomy, graphic medical]
  namedReferences:
    illustrators: [Deivid Saenz]
  examplePromptTemplate: |
    Friendly flat vector medical illustration of a heart organ, clean clinical
    look with soft pink and sage palette on white, no outline, Deivid Saenz
    Lifesavers healthcare aesthetic.
  whenToUse: Health tech, telemedicine, pharma onboarding.
  pairsWith:
    prototypeStyles: [recipe-restrained-ai-marketing, recipe-bento-marketing]
  notForUseWhen: gore, brutalism, editorial

- styleId: blush-spooky-stickers
  name: Spooky Stickers
  category: Flat vector
  subCategory: thick-border-cartoon
  role: decoration
  source: blush.design — Spooky Stickers by Team Blush
  visualSignatures:
    - Halloween doodles: ghosts, pumpkins, cats in costume
    - sticker style with thick black outline
    - orange + black + purple palette
  promptKeywords:
    primary: [Halloween, sticker, ghost, pumpkin, spooky cute]
    material: ["flat fill"]
    line: ["thick 3px black"]
    color: ["orange black purple"]
    style: ["sticker isolated"]
    avoidKeywords: [photoreal horror, gore]
  namedReferences:
    illustrators: [Team Blush]
  examplePromptTemplate: |
    Spooky-cute Halloween sticker of [SUBJECT], thick 3px black outline, palette
    of orange black and purple, flat fill, isolated, Blush Spooky Stickers style.
  whenToUse: Seasonal Halloween, gaming, edgy-friendly brand moments.
  pairsWith:
    prototypeStyles: [aesthetic-cottagegoth, aesthetic-dreamcore, aesthetic-positivity-kawaii]
  notForUseWhen: enterprise, restrained AI

- styleId: blush-goodies
  name: Goodies
  category: Flat vector
  subCategory: flat-iconographic
  role: decoration
  source: blush.design — Goodies by Team Blush
  visualSignatures:
    - small assorted sticker-style objects
    - mixed palette, mixed theme
    - decorative accent role
  promptKeywords:
    primary: [sticker, object, decoration, mixed]
    material: ["flat fill"]
    line: ["soft 2px optional"]
    color: ["varied playful"]
    style: ["sticker isolated"]
    avoidKeywords: [unified palette, single subject]
  namedReferences:
    illustrators: [Team Blush]
  examplePromptTemplate: |
    Flat vector sticker of [SUBJECT], playful flat fill, optional 2px soft
    outline, isolated on white, Blush Goodies aesthetic.
  whenToUse: Decorative accents on marketing surfaces.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, aesthetic-cluttercore, aesthetic-maximalism]
  notForUseWhen: minimalist single-hero

- styleId: blush-patterns
  name: Patterns (Pablo Stanley)
  category: Abstract / decoration
  subCategory: geometric-primitive
  role: decoration
  source: blush.design — Patterns by Pablo Stanley
  visualSignatures:
    - tileable repeating patterns
    - mix of dots, lines, squiggles, simple shapes
    - editorial-modern palette
  promptKeywords:
    primary: [pattern, repeating, tileable, abstract]
    material: ["flat fill"]
    line: ["mixed"]
    color: ["editorial modern muted + one accent"]
    style: ["repeating tile pattern"]
    avoidKeywords: [single subject, scene]
  namedReferences:
    illustrators: [Pablo Stanley]
  examplePromptTemplate: |
    Tileable repeating pattern of dots squiggles and simple shapes, editorial
    modern muted palette with one accent color, flat fill no shading, Pablo
    Stanley Blush Patterns aesthetic.
  whenToUse: Background bands, section dividers, wallpaper accents.
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-de-stijl, aesthetic-corporate-memphis, recipe-bento-marketing]
  notForUseWhen: cluttered scenes, photoreal

### 2.3 — Lev Inunnink Humanities Illustrations

- styleId: humanities-marginalia
  name: Humanities (medieval-marginalia revival)
  category: Hand-drawn / sketch
  subCategory: marginalia-quirky
  role: spot-illustration
  source: levinunnink.gumroad.com/l/humanities-illustrations
  visualSignatures:
    - quirky hand-drawn characters echoing medieval-manuscript marginalia
    - black ink line on transparent PNG, works on light or dark
    - playful absurd subjects (knight, monk, hybrid creature)
    - intentionally amateur / naïve quality — stands against AI slop
    - 35 distinct illustrations, transparent PNG
  promptKeywords:
    primary: [hand-drawn, medieval marginalia, ink line, quirky, naive]
    material: ["ink on parchment", "transparent PNG"]
    line: ["scratchy ink quill 2px"]
    color: ["pure black on transparent", "no fill"]
    style: ["medieval marginalia", "absurd character"]
    avoidKeywords: [polished, vector perfect, AI-render, color fill]
  namedReferences:
    illustrators: [Lev Inunnink]
    movements: [medieval marginalia revival, anti-AI illustration manifesto]
    productsOrFilms: [The Luttrell Psalter, Smith of Wootton Major]
  examplePromptTemplate: |
    Hand-drawn quirky character in medieval manuscript marginalia style,
    scratchy ink quill line 2px, pure black on transparent background, naive
    amateur quality intentionally rough, absurd hybrid creature or robed
    figure, Lev Inunnink Humanities aesthetic — anti-AI human warmth.
  whenToUse: Editorial blogs that want to signal human craft over AI slop;
    long-form essays; sites where the illustration says "a person made this."
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, recipe-editorial-magazine, recipe-newspaper-of-record, recipe-readcv, style-serif-warm-paper]
  notForUseWhen: SaaS marketing, cute-friendly contexts, 3D contexts

### 2.4 — Scribbbles

- styleId: scribbbles-funky-vector
  name: Scribbbles funky vector scribble
  category: Abstract / decoration
  subCategory: squiggle-line
  role: decoration
  source: scribbbles.design (100+ vectorized scribbles)
  visualSignatures:
    - single-line abstract scribbles — squiggles, loops, tangles
    - 100% vector, color customizable
    - feels like a marker test on white
    - decoration role only, never depicts a subject
  promptKeywords:
    primary: [scribble, vector, loose line, abstract, marker]
    material: ["vector line, single weight"]
    line: ["loose marker line 3-5px"]
    color: ["single color customizable"]
    style: ["abstract loose squiggle"]
    avoidKeywords: [filled shape, character, scene]
  namedReferences:
    illustrators: [Igor Saveliev]
    movements: [doodle UI revival]
    productsOrFilms: [Notion-era hand-drawn marketing accents]
  examplePromptTemplate: |
    Loose abstract scribble made with single 4px marker line, vector shape,
    monochrome, decoration-only no subject, isolated on white, Scribbbles.design
    funky aesthetic — like a marker doodle test.
  whenToUse: Background accent, replacing solid divider lines, highlighting
    words like a manual underline.
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-corporate-memphis, recipe-bento-marketing, aesthetic-positivity-kawaii]
  notForUseWhen: editorial, brutalism, photoreal

### 2.5 — HandyArrows multi-page (handyarrows.com)

> The site exposes 5 navigation buckets — Arrows, Doodles, Infographic,
> Illustrations, Underlines. Each is a distinct decoration-role family.

- styleId: handyarrows-arrows
  name: HandyArrows — Hand-drawn Arrows (185+)
  category: Abstract / decoration
  subCategory: doodle-arrow
  role: decoration
  source: handyarrows.com (Arrows category)
  visualSignatures:
    - 185+ hand-drawn arrow SVGs in varied styles
    - mix of: straight, curved, squiggly, looped, double-line, sketchy, chunky
    - all drawn with single black line, no fill
    - common terminus styles: simple chevron, feathered, splayed
  promptKeywords:
    primary: [hand-drawn arrow, doodle, SVG, single line, marker]
    material: ["vector SVG"]
    line: ["hand-drawn marker 3-4px, slight wobble"]
    color: ["black line, mono"]
    style: ["arrow with chevron terminus"]
    avoidKeywords: [3d arrow, polished icon, photoreal]
  namedReferences:
    illustrators: [Eren Can Arica / Eronred]
    movements: [doodle UI accent]
  examplePromptTemplate: |
    Hand-drawn arrow with slight wobble, 3px marker line, single black stroke
    on white, simple chevron terminus, vector SVG decoration, HandyArrows style,
    decoration-only no subject.
  whenToUse: Pointing at headlines, marking flow steps, illustrating "click here."
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-corporate-memphis, recipe-bento-marketing, recipe-readcv]
  notForUseWhen: dense data UI, brutalism

- styleId: handyarrows-doodles
  name: HandyArrows — Doodles
  category: Abstract / decoration
  subCategory: squiggle-line
  role: decoration
  source: handyarrows.com (Doodles category)
  visualSignatures:
    - playful hand-drawn elements: stars, hearts, sparkles, dots, swirls
    - intentionally informal, kid-like quality
    - black single-line
  promptKeywords:
    primary: [hand-drawn doodle, sparkle, star, heart, swirl]
    material: ["vector SVG"]
    line: ["informal marker 2-3px"]
    color: ["mono black"]
    style: ["playful accent"]
    avoidKeywords: [polished, geometric perfect]
  namedReferences:
    illustrators: [Eren Can Arica]
  examplePromptTemplate: |
    Hand-drawn playful doodle of a sparkle/star/heart with informal marker line
    2-3px, mono black on white, decoration accent, HandyArrows Doodles style.
  whenToUse: Sprinkle around headlines, between sections, as bullet substitutes.
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-positivity-kawaii, recipe-readcv, aesthetic-curly-girly]
  notForUseWhen: minimalist, brutalism

- styleId: handyarrows-infographic
  name: HandyArrows — Infographic
  category: Abstract / decoration
  subCategory: doodle-arrow
  role: decoration
  source: handyarrows.com (Infographic category)
  visualSignatures:
    - circles, brackets, numbers, callout elements
    - hand-drawn diagram pieces — for marking up wireframes
    - all single-line black
  promptKeywords:
    primary: [infographic, hand-drawn circle, callout, bracket, diagram]
    material: ["vector SVG"]
    line: ["marker 2-3px"]
    color: ["mono black"]
    style: ["diagram accent"]
    avoidKeywords: [photoreal data viz, polished]
  namedReferences:
    illustrators: [Eren Can Arica]
  examplePromptTemplate: |
    Hand-drawn infographic accent — circle around a word or bracket to group
    elements, 2-3px marker line, mono black, HandyArrows Infographic style.
  whenToUse: Annotating screenshots, wireframe markup, highlighting key terms.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-bento-marketing, recipe-readcv]
  notForUseWhen: high-polish enterprise

- styleId: handyarrows-illustrations
  name: HandyArrows — Illustrations
  category: Hand-drawn / sketch
  subCategory: ink-line-brush
  role: spot-illustration
  source: handyarrows.com (Illustrations category)
  visualSignatures:
    - full-figure hand-drawn illustrations
    - same maker's hand as the arrows — wobbly marker line
    - characters and small scenes
  promptKeywords:
    primary: [hand-drawn, illustration, character, scene, marker]
    material: ["vector SVG"]
    line: ["marker 3-4px"]
    color: ["mono or limited"]
    style: ["editorial spot"]
    avoidKeywords: [vector perfect, 3d]
  namedReferences:
    illustrators: [Eren Can Arica]
  examplePromptTemplate: |
    Full hand-drawn spot illustration of a [SUBJECT], marker 3-4px line, mono
    or limited two-color, single artist's hand, HandyArrows Illustrations style.
  whenToUse: Editorial articles, indie SaaS blog headers, indie product hero.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-readcv, recipe-editorial-magazine]
  notForUseWhen: corporate Fortune-500

- styleId: handyarrows-underlines
  name: HandyArrows — Underlines & Brackets
  category: Abstract / decoration
  subCategory: doodle-arrow
  role: decoration
  source: handyarrows.com (Underlines category)
  visualSignatures:
    - underline strokes in many flavors: wavy, looped, double, sketch
    - bracket marks for grouping
    - all decorative emphasis tools, never standalone illustration
  promptKeywords:
    primary: [underline, bracket, emphasis, marker, hand-drawn]
    material: ["vector SVG"]
    line: ["marker 2-4px"]
    color: ["mono"]
    style: ["underline stroke", "bracket grouping mark"]
    avoidKeywords: [solid CSS rule, pixel-perfect]
  namedReferences:
    illustrators: [Eren Can Arica]
  examplePromptTemplate: |
    Hand-drawn underline stroke (wavy/looped/double) or bracket grouping mark,
    2-4px marker line, mono black on white, HandyArrows Underlines style,
    decoration accent only.
  whenToUse: Emphasizing words in display headlines, grouping related items.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-readcv, aesthetic-corporate-memphis, aesthetic-y2k-memphis-loud]
  notForUseWhen: hairline-restraint design systems

### 2.6 — Abstract shape libraries (Spectrums & Shapes Gallery)

> These are decoration-only — they never depict a subject. Tagged `role: decoration`.

- styleId: spectrums-vector-shape-circle
  name: Spectrums — Circle family
  category: Abstract / decoration
  subCategory: geometric-primitive
  role: decoration
  source: spectrums.framer.website (Sachin Dhyani)
  visualSignatures:
    - clean geometric circles with variations: dotted, double-stroked, segmented
    - solid black or single accent color
    - large hero-decoration scale
  promptKeywords:
    primary: [circle, geometric, vector, decoration]
    material: ["vector flat"]
    line: ["1-3px stroke or solid fill"]
    color: ["single mono or accent"]
    style: ["geometric primitive"]
    avoidKeywords: [scene, subject, photoreal]
  examplePromptTemplate: |
    Geometric circle decoration — variant (dotted/double-stroked/segmented),
    single accent color, vector flat, isolated, Spectrums library aesthetic.
  whenToUse: Background hero accents, bullet substitutes.
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-de-stijl, aesthetic-swiss-modernist, recipe-swiss-grid]
  notForUseWhen: cluttered scenes

- styleId: spectrums-organic-blob
  name: Spectrums — Organic blob
  category: Abstract / decoration
  subCategory: gradient-blob
  role: decoration
  source: spectrums.framer.website
  visualSignatures:
    - asymmetric organic free-form blob shapes
    - solid fill or soft gradient
    - bounded by no straight edges
  promptKeywords:
    primary: [blob, organic, asymmetric, vector, decoration]
    material: ["solid fill or soft gradient"]
    line: ["no line"]
    color: ["pastel single or 2-stop gradient"]
    style: ["free-form organic"]
    avoidKeywords: [geometric, sharp]
  examplePromptTemplate: |
    Asymmetric organic vector blob shape, solid pastel fill or 2-stop soft
    gradient, no outline, isolated decoration accent, Spectrums library style.
  whenToUse: Behind text as background mask, hero background bands.
  pairsWith:
    prototypeStyles: [style-aurorism, aesthetic-frutiger-aero, recipe-aurora-marketing, style-glassmorphism]
  notForUseWhen: brutalism, hairline-restraint

- styleId: spectrums-complex-flower
  name: Spectrums — Complex / Flower
  category: Abstract / decoration
  subCategory: geometric-primitive
  role: decoration
  source: spectrums.framer.website (Complex / Star categories)
  visualSignatures:
    - flower-like radial shapes, complex stars, mandala-adjacent forms
    - multi-petal symmetric geometry
    - single fill color
  promptKeywords:
    primary: [flower, star, radial, geometric, vector]
    material: ["solid fill"]
    line: ["no line"]
    color: ["single accent"]
    style: ["radial symmetric"]
    avoidKeywords: [photoreal flower]
  examplePromptTemplate: |
    Radial symmetric flower or star vector shape, solid single-color fill,
    multi-petal geometric form, isolated decoration, Spectrums complex
    shape aesthetic.
  whenToUse: Hero accents, decorative section dividers, headline halos.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-memphis-loud, aesthetic-curly-girly, aesthetic-positivity-kawaii, aesthetic-acid-design]
  notForUseWhen: minimalist hairline UI

- styleId: shapes-gallery-michalczyk
  name: Shapes.gallery — Monika Michalczyk shapes
  category: Abstract / decoration
  subCategory: geometric-primitive
  role: decoration
  source: shapes.gallery
  visualSignatures:
    - 80+ SVG shapes spanning organic + geometric
    - more curated / refined feel than Spectrums
    - includes wavy lines, soft polygons, drip shapes
  promptKeywords:
    primary: [vector shape, soft polygon, wave, decoration]
    material: ["flat fill or 2-stop gradient"]
    line: ["mostly no line"]
    color: ["editorial mid-saturation"]
    style: ["refined geometric"]
    avoidKeywords: [scene, subject]
  examplePromptTemplate: |
    Refined geometric or organic vector shape (wave/drip/soft polygon), flat
    fill or 2-stop gradient, editorial mid-saturation color, decoration only,
    Monika Michalczyk Shapes.gallery style.
  whenToUse: Designer portfolios, editorial sites, refined SaaS marketing.
  pairsWith:
    prototypeStyles: [recipe-neo-grotesque-portfolio, recipe-readcv, style-bold-display, recipe-bento-marketing]
  notForUseWhen: dense data UI, brutalism

### 2.7 — Illustrative typography (research-derived)

- styleId: typo-y2k-chrome-3d
  name: Y2K Chrome 3D typography
  category: Illustrative typography
  subCategory: y2k-chrome-3d
  role: typography
  source: research (Kittl, Behance, Y2K revival 2020+)
  visualSignatures:
    - bulbous 3D letterforms with chrome / liquid metal surface
    - environment-mapped reflections (sky, neon, gradient)
    - drop shadow with cyan or pink bleed
    - paired with neon backgrounds, lens flares, sparkles
  promptKeywords:
    primary: [Y2K, chrome, 3D type, liquid metal, bulbous, environment map]
    material: ["liquid chrome", "polished metal", "environment-mapped"]
    line: ["no line, reflection on surface"]
    color: ["chrome silver + cyan + magenta accent"]
    style: ["bulbous wordmark", "lens flare", "neon bg"]
    avoidKeywords: [matte, flat, hand-drawn, paper texture]
  namedReferences:
    illustrators: [Dean Quigley, Lucas Lemaire]
    movements: [Y2K revival, vaporwave-chrome]
    productsOrFilms: [Rosalia MOTOMAMI lettering, Bad Bunny album art]
  examplePromptTemplate: |
    Y2K chrome 3D typography of the word [WORD], bulbous liquid-metal letterforms
    with environment-mapped chrome surface reflecting cyan-and-magenta sky,
    polished mirror finish, drop shadow with pink bleed, lens flare sparkle,
    early-2000s retro-futurist wordmark, isolated on gradient background.
  whenToUse: Y2K revival branding, music marketing, beauty drops, Gen-Z fashion.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-y2k-memphis-loud, aesthetic-vaporwave, aesthetic-frutiger-chromecore]
  notForUseWhen: editorial restraint, B2B, Bauhaus

- styleId: typo-weingart-deconstructed
  name: Weingart deconstructed typography
  category: Illustrative typography
  subCategory: weingart-deconstructed
  role: typography
  source: research (Wolfgang Weingart, Basel School)
  visualSignatures:
    - letterforms stretched to extreme spacing, layered halftones
    - reversed type out of heavy black blocks
    - typographic landscape — letters as terrain
    - Swiss grid disrupted intentionally
  promptKeywords:
    primary: [Weingart, deconstructed, Swiss punk, stretched letter spacing, halftone layered]
    material: ["letterpress on paper", "screen halftone"]
    line: ["bold geometric letterform"]
    color: ["high contrast — black on cream + 1 accent"]
    style: ["disrupted grid", "reversed text out of black block"]
    avoidKeywords: [polished, perfectly aligned, decorative ornament]
  namedReferences:
    illustrators: [Wolfgang Weingart, April Greiman, Dan Friedman]
    movements: [Swiss Punk, New Wave typography 1970s-80s]
  examplePromptTemplate: |
    Weingart-style deconstructed typography of [WORD] with extreme letter-spacing,
    reversed-out on heavy black block, layered halftone screen overlay, single
    red accent, disrupted-grid composition, letterpress paper texture, Basel
    School Swiss Punk aesthetic.
  whenToUse: Editorial covers, art books, design-conference posters, brutalist-
    adjacent serious work.
  pairsWith:
    prototypeStyles: [aesthetic-web-brutalism, recipe-brutalist-web, aesthetic-swiss-modernist, recipe-editorial-magazine]
  notForUseWhen: friendly consumer UI, kids, Y2K bling

- styleId: typo-art-nouveau-ornament
  name: Art Nouveau ornamental lettering
  category: Illustrative typography
  subCategory: art-nouveau-ornament
  role: typography
  source: research (Alphonse Mucha, Eugène Grasset)
  visualSignatures:
    - letterforms entwined with floral vines, buds, tendrils
    - whiplash organic curves
    - terminals curl into leaves
    - frame ornament around the wordmark
  promptKeywords:
    primary: [Art Nouveau, Mucha, ornamental lettering, floral entwined, whiplash curve]
    material: ["lithograph poster", "ink and gouache"]
    line: ["fluid organic stroke"]
    color: ["muted gold ochre sage burgundy"]
    style: ["framed by floral ornament"]
    avoidKeywords: [geometric sans, Bauhaus, modern minimal]
  namedReferences:
    illustrators: [Alphonse Mucha, Eugène Grasset, Aubrey Beardsley]
    movements: [Art Nouveau 1890-1910]
  examplePromptTemplate: |
    Art Nouveau ornamental wordmark of [WORD], letterforms entwined with floral
    vines and curling tendrils, whiplash organic curves, terminals curl into
    leaves, framed by botanical ornament, lithograph poster aesthetic, muted
    palette of gold ochre sage and burgundy, Alphonse Mucha style.
  whenToUse: Boutique apothecary, perfume, natural-wine labels, museum poster.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, aesthetic-dark-academia, aesthetic-cottagecore, aesthetic-fairycore]
  notForUseWhen: tech, brutalism, neon

- styleId: typo-fella-anti-design
  name: Ed Fella anti-design hand-letter
  category: Illustrative typography
  subCategory: fella-anti-design
  role: typography
  source: research (Edward Fella, CalArts)
  visualSignatures:
    - intentionally misshapen, irregular hand-lettered glyphs
    - each letter individually drawn, no consistency
    - collaged onto paper with hand-drawn ornament
    - rejection of every typographic rule
  promptKeywords:
    primary: [Ed Fella, hand-lettered, anti-design, irregular glyph, expressive]
    material: ["sharpie on paper", "collage"]
    line: ["irregular hand stroke"]
    color: ["mostly black + occasional accent"]
    style: ["each letter different", "no baseline"]
    avoidKeywords: [Helvetica, grid, polished vector]
  namedReferences:
    illustrators: [Edward Fella, David Carson]
    movements: [Anti-design, CalArts typography 1990s]
  examplePromptTemplate: |
    Hand-lettered wordmark of [WORD] in Ed Fella style — each letter individually
    drawn with irregular shape, no consistent baseline, sharpie-on-paper texture,
    collaged with hand-drawn ornament, mostly black with one red accent,
    intentionally amateur anti-design aesthetic.
  whenToUse: Art-school flyers, indie zines, underground music, brutalism-
    adjacent editorial.
  pairsWith:
    prototypeStyles: [aesthetic-anti-design, aesthetic-web-brutalism, recipe-brutalist-web, aesthetic-corporate-grunge]
  notForUseWhen: enterprise, polished SaaS

- styleId: typo-vectorheart-decorative
  name: Vectorheart decorative typography
  category: Illustrative typography
  subCategory: vectorheart-decorative
  role: typography
  source: research + prototype/aesthetic-vector-neovectorheart
  visualSignatures:
    - hand-crafted vector letterforms with floral / heart / bauble accents
    - swashes, dingbats, stars embedded in letters
    - palette: pink, cream, brick red, sage
    - feels romance-novel + indie-craft
  promptKeywords:
    primary: [vectorheart, decorative typography, floral letter, hand-crafted, swash]
    material: ["vector with decorative ornament"]
    line: ["custom drawn"]
    color: ["pink cream brick sage"]
    style: ["dingbats embedded", "swashes"]
    avoidKeywords: [generic serif, Helvetica]
  namedReferences:
    illustrators: [Naomi Wilkinson, House Industries]
    movements: [Vectorheart aesthetic, late-2010s indie craft revival]
  examplePromptTemplate: |
    Decorative hand-crafted vector wordmark of [WORD], custom letterforms with
    embedded dingbats stars and hearts inside the counters, swashes curling
    from terminals, palette of pink cream brick red and sage, romance-novel
    indie-craft Vectorheart aesthetic.
  whenToUse: Boutique brands, craft-cocktail menus, indie publications.
  pairsWith:
    prototypeStyles: [aesthetic-vector-neovectorheart, aesthetic-vector-vectorbloom, aesthetic-curly-girly, recipe-warm-restraint]
  notForUseWhen: tech, B2B, brutalism

- styleId: typo-vector-musica
  name: Vector Música typographic illustration
  category: Illustrative typography
  subCategory: hand-lettered-editorial
  role: typography
  source: research + prototype/aesthetic-vector-vector-musica
  visualSignatures:
    - music-festival poster lettering: chunky display + decorative motif
    - mix of vintage scripts + geometric sans
    - layered with illustrative musical motifs (notes, instruments, stage)
    - rich gradient + halftone color
  promptKeywords:
    primary: [Vector Música, music poster, layered typography, illustrative]
    material: ["vector + halftone overlay"]
    line: ["mixed scripts + sans"]
    color: ["rich gradient with halftone"]
    style: ["festival poster", "layered illustration + type"]
    avoidKeywords: [minimal text-only, hairline]
  namedReferences:
    illustrators: [Latin American festival posters, Lisbon design scene]
  examplePromptTemplate: |
    Music festival poster typography for [WORD], chunky display lettering mixed
    with vintage scripts and geometric sans, layered with illustrative musical
    motifs (notes, instruments, stage silhouette), rich gradient with halftone
    overlay, Vector Música aesthetic.
  whenToUse: Music marketing, festival branding, nightlife.
  pairsWith:
    prototypeStyles: [aesthetic-vector-vector-musica, aesthetic-acid-design, aesthetic-vaporwave]
  notForUseWhen: editorial restraint, B2B

- styleId: typo-illuminated-drop-cap
  name: Illuminated drop cap (medieval revival)
  category: Illustrative typography
  subCategory: illuminated-drop-cap
  role: typography
  source: research (medieval manuscripts, William Morris Kelmscott)
  visualSignatures:
    - single large initial letter painted with gold leaf
    - botanical / animal motifs entwined in the letterform
    - sized 4-8 lines tall, drops into body text
    - palette: gold + lapis blue + vermillion + ivory
  promptKeywords:
    primary: [illuminated, drop cap, initial letter, gold leaf, medieval]
    material: ["gold leaf", "gouache on vellum"]
    line: ["fine ink outline"]
    color: ["gold + lapis blue + vermillion + ivory"]
    style: ["botanical entwined initial"]
    avoidKeywords: [modern sans, geometric, vector flat]
  namedReferences:
    illustrators: [Kelmscott Press, Book of Kells, William Morris]
  examplePromptTemplate: |
    Illuminated drop cap initial letter [LETTER], painted with gold leaf and
    gouache on vellum, botanical vines and small creatures entwined around
    the form, palette of gold lapis blue vermillion and ivory, fine ink
    outline, medieval manuscript aesthetic, 6 lines tall.
  whenToUse: Long-form editorial, literary site, book-cover design.
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, recipe-editorial-magazine, recipe-newspaper-of-record, style-serif-warm-paper]
  notForUseWhen: tech, brutalism, anything sans-serif

- styleId: typo-blackletter-neo-gothic
  name: Blackletter / Neo-Gothic illustrative
  category: Illustrative typography
  subCategory: blackletter-neo-gothic
  role: typography
  source: research (current 2025 type trends)
  visualSignatures:
    - blackletter foundation with sharp ornate flourishes
    - high stroke contrast, broken-pen angularity
    - paired with cross, dagger, flame ornament
    - mono black or single saturated color
  promptKeywords:
    primary: [blackletter, neo-gothic, sharp, ornate, broken pen]
    material: ["ink letterpress feel"]
    line: ["high contrast broken pen"]
    color: ["mono black + occasional crimson"]
    style: ["sharp ornate flourish"]
    avoidKeywords: [rounded sans, friendly]
  namedReferences:
    illustrators: [Erik Marinovich, fashion-streetwear lettering 2020s]
  examplePromptTemplate: |
    Blackletter neo-gothic wordmark of [WORD], high-contrast broken-pen strokes,
    sharp ornate flourishes, paired with dagger or flame ornament, mono black
    or crimson accent, fashion-streetwear blackletter aesthetic.
  whenToUse: Streetwear, metal music, dark editorial, gothic brands.
  pairsWith:
    prototypeStyles: [aesthetic-cottagegoth, aesthetic-dark-academia, aesthetic-corporate-grunge]
  notForUseWhen: friendly SaaS, Bauhaus, kawaii

- styleId: typo-bubble-graffiti
  name: Bubble graffiti display
  category: Illustrative typography
  subCategory: bubble-graffiti
  role: typography
  source: research (graffiti, hip-hop typography)
  visualSignatures:
    - rounded chunky bubble letterforms
    - outlined with thick contrasting stroke
    - drop-shadow at offset for dimension
    - spray-paint texture or solid candy color
  promptKeywords:
    primary: [bubble letter, graffiti, chunky, rounded, outlined]
    material: ["spray paint or vector candy"]
    line: ["3-5px contrast outline"]
    color: ["candy bright or chrome"]
    style: ["offset drop shadow"]
    avoidKeywords: [thin elegant, serif]
  namedReferences:
    illustrators: [Stash, Mode 2, NYC subway graffiti]
    movements: [hip-hop typography, 1980s graffiti]
  examplePromptTemplate: |
    Bubble graffiti wordmark of [WORD], rounded chunky letterforms outlined
    with 4px contrasting stroke, offset drop shadow for dimension, spray-paint
    texture or solid candy color, NYC subway-style hip-hop aesthetic.
  whenToUse: Street brands, music, youth-skate-culture.
  pairsWith:
    prototypeStyles: [aesthetic-urbling, aesthetic-y2k-memphis-loud, aesthetic-acid-graphics]
  notForUseWhen: B2B, editorial restraint

- styleId: typo-house-industries-revival
  name: House Industries pop-baroque revival
  category: Illustrative typography
  subCategory: house-industries-revival
  role: typography
  source: research (House Industries, Yorklyn Delaware)
  visualSignatures:
    - mid-century American commercial lettering revival
    - influences: Doyald Young, Tom Carnese, Herb Lubalin, pinstripers
    - polished retro script + display
    - paired with subtle ornament
  promptKeywords:
    primary: [House Industries, retro American lettering, polished script, display]
    material: ["lithograph crisp print"]
    line: ["polished smooth stroke"]
    color: ["retro coral + cream + navy"]
    style: ["1960s commercial sign", "subtle ornament"]
    avoidKeywords: [crude, hand-drawn rough, blackletter]
  namedReferences:
    illustrators: [Ken Barber, Andy Cruz, Rich Roat, Herb Lubalin]
    movements: [American mid-century commercial revival]
  examplePromptTemplate: |
    Polished retro American commercial lettering for [WORD], 1960s sign-painter
    style with subtle ornament accent, palette of coral cream and navy,
    lithograph crisp print quality, House Industries revival aesthetic.
  whenToUse: Beverage brands, premium consumer goods, retro restaurant identity.
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-coastal-grandmother, recipe-warm-restraint, recipe-editorial-magazine]
  notForUseWhen: brutalism, tech-futurist

- styleId: typo-wood-type-letterpress
  name: Wood-type letterpress slab
  category: Illustrative typography
  subCategory: wood-type-letterpress
  role: typography
  source: research (American wood-type tradition, Hatch Show Print)
  visualSignatures:
    - chunky slab letterforms with grain showing through ink
    - registration imperfection
    - palette: vintage red + black + cream
    - poster composition with hand-laid baseline
  promptKeywords:
    primary: [wood type, letterpress, slab, grain, vintage poster]
    material: ["letterpress ink on wood", "visible grain"]
    line: ["chunky slab serif"]
    color: ["vintage red black cream"]
    style: ["circus poster", "hand-laid baseline"]
    avoidKeywords: [perfect register, vector smooth]
  namedReferences:
    illustrators: [Hatch Show Print, Yee-Haw Industries]
    movements: [American wood-type tradition 19th c.]
  examplePromptTemplate: |
    Wood-type letterpress poster wordmark of [WORD], chunky slab letterforms
    with wood grain showing through inked impression, registration imperfections,
    palette of vintage red black on cream, Hatch Show Print circus-poster
    aesthetic.
  whenToUse: Music venues, craft beer, festival posters, americana branding.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, recipe-warm-restraint, recipe-editorial-magazine, aesthetic-corporate-grunge]
  notForUseWhen: tech, brutalism

- styleId: typo-hand-lettered-editorial
  name: Hand-lettered editorial (modern brush)
  category: Illustrative typography
  subCategory: hand-lettered-editorial
  role: typography
  source: research (Jessica Hische, Erik Marinovich, contemporary lettering)
  visualSignatures:
    - bespoke brush lettering with confident smooth curves
    - subtle ornament — swashes, hairline accent
    - high-end editorial polish
  promptKeywords:
    primary: [hand-lettered, brush, bespoke, editorial, smooth]
    material: ["digital brush"]
    line: ["confident smooth stroke"]
    color: ["mono or restrained 2-color"]
    style: ["editorial swash", "ornament accent"]
    avoidKeywords: [generic font, sloppy, anti-design]
  namedReferences:
    illustrators: [Jessica Hische, Erik Marinovich, Stefan Kunz]
  examplePromptTemplate: |
    Bespoke hand-lettered wordmark of [WORD] with confident smooth brush curves,
    subtle swash and hairline ornament, restrained 2-color palette, high-end
    editorial polish, Jessica Hische contemporary lettering aesthetic.
  whenToUse: Premium editorial, book covers, magazine titles, restaurant identity.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-warm-restraint, style-serif-warm-paper, recipe-readcv]
  notForUseWhen: brutalism, sans-only design system

### 2.8 — Canonical curator additions

These are not from the URL sources but are essential to a serious library.

- styleId: clay-3d-soft-sculpt
  name: 3D Clay / Soft Sculpt
  category: 3D
  subCategory: clay
  role: subject
  source: curator addition
  visualSignatures:
    - matte fingerprinted clay surface with subtle thumbprint dents
    - soft rounded forms with no sharp edges
    - matte muted palette — terracotta, dusty pink, butter yellow
    - characters or objects sit on coordinated paper stage
  promptKeywords:
    primary: [clay, sculpted, matte, fingerprinted, soft 3d]
    material: ["polymer clay matte", "fingerprint texture", "no specular"]
    line: ["no line"]
    color: ["muted dusty terracotta butter sage"]
    style: ["isolated on paper stage"]
    avoidKeywords: [glossy plastic, chrome, hairline, photoreal skin]
  namedReferences:
    illustrators: [Wallace & Gromit, Aardman, Lia Griffith]
    movements: [post-claymorphism 3D UI 2020-2024]
    productsOrFilms: [Apple AirPods 3D claymation ads]
  examplePromptTemplate: |
    Handcrafted polymer clay sculpture of [SUBJECT], matte fingerprinted surface
    with subtle thumbprint texture, soft rounded forms no sharp edges, muted
    palette of dusty terracotta butter yellow and sage, isolated on coordinated
    paper stage, soft top-down studio light, octane render, claymation aesthetic.
  whenToUse: Style-claymorphism interfaces, warm-restraint marketing, premium
    children's brands.
  pairsWith:
    prototypeStyles: [style-claymorphism, recipe-warm-restraint, aesthetic-cottagecore, aesthetic-positivity-kawaii]
  notForUseWhen: cyberpunk, brutalism, neon

- styleId: plasticine-3d-rougher
  name: 3D Plasticine (rougher than clay)
  category: 3D
  subCategory: plasticine
  role: subject
  source: curator addition
  visualSignatures:
    - oilier surface than clay, more visible tool marks
    - slightly chunkier proportion
    - palette includes more saturated primaries
    - feels like a school-art-room maquette
  promptKeywords:
    primary: [plasticine, modeling clay, tool marks, oily surface, chunky]
    material: ["plasticine modeling clay", "tool-mark texture"]
    line: ["no line"]
    color: ["saturated primary + earth"]
    style: ["school maquette feel"]
    avoidKeywords: [smooth polished, matte refined]
  namedReferences:
    illustrators: [Pingu, early Aardman]
    movements: [Stop-motion plasticine animation]
  examplePromptTemplate: |
    Plasticine modeling-clay 3D sculpture of [SUBJECT] with visible tool-mark
    texture and oilier surface, slightly chunky proportions, palette of
    saturated primary plus earth tones, school-art-room maquette feel,
    octane render, Pingu-era stop-motion aesthetic.
  whenToUse: Playful kid-targeted brands, retro stop-motion-feel marketing.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-corporate-memphis, aesthetic-wacky-pomo]
  notForUseWhen: refined, restrained, AI marketing

- styleId: fluffy-plush-3d
  name: 3D Fluffy / Plush
  category: 3D
  subCategory: fluffy-plush
  role: mascot
  source: curator addition (3D illustration trend 2023+)
  visualSignatures:
    - long fiber fur shader covering the whole form
    - characters look like plush stuffed toys
    - palette: pastel pink, ivory, sky blue
    - soft studio light with slight backlight
  promptKeywords:
    primary: [fluffy, plush, fur shader, stuffed toy, soft 3d]
    material: ["long fiber fur shader", "felt fabric inlay"]
    line: ["no line"]
    color: ["pastel pink ivory sky blue"]
    style: ["plush mascot pose"]
    avoidKeywords: [glossy, sharp, hairline]
  namedReferences:
    illustrators: [Jellycat brand, Pinkfong, Boya]
    movements: [Plush 3D mascot trend 2023+]
  examplePromptTemplate: |
    3D fluffy plush stuffed-toy character of [SUBJECT], long fiber fur shader
    covering the whole form, felt fabric inlay for accents, pastel palette of
    pink ivory and sky blue, soft studio light with slight backlight, mascot
    pose, octane render, Jellycat-inspired plush aesthetic.
  whenToUse: Kids brands, comfort apps, plush product marketing.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-curly-girly, style-claymorphism, aesthetic-fairycore]
  notForUseWhen: B2B, brutalism, dark themes

- styleId: wireframe-3d
  name: 3D Wireframe / Mesh
  category: 3D
  subCategory: wireframe
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - polygon mesh wireframe shown without solid fill
    - thin neon line on dark background
    - reads as "behind the scenes 3D" or "tech diagram"
  promptKeywords:
    primary: [wireframe, mesh, polygon, line render, technical]
    material: ["wireframe only", "no fill"]
    line: ["thin neon 1px"]
    color: ["cyan or magenta line on dark navy"]
    style: ["isometric tech diagram"]
    avoidKeywords: [filled, photoreal, soft]
  namedReferences:
    illustrators: [Vector graphics renaissance, Tron]
    movements: [Cyberpunk tech aesthetic]
  examplePromptTemplate: |
    3D wireframe mesh rendering of [SUBJECT], polygon mesh shown as thin 1px
    neon cyan lines on dark navy background, no surface fill, isometric
    composition, technical-diagram cyberpunk aesthetic.
  whenToUse: Tech marketing for 3D / spatial / engineering products, Tron-
    inspired branding.
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, recipe-terminal-on-web, recipe-ai-foundry-dark]
  notForUseWhen: warm consumer, cottagecore, friendly

- styleId: origami-paper-3d
  name: Origami / Folded Paper 3D
  category: 3D
  subCategory: origami
  role: subject
  source: curator addition
  visualSignatures:
    - subject built from folded paper planes
    - visible fold creases
    - solid pastel paper color
    - cast shadow includes triangular fold-shadows
  promptKeywords:
    primary: [origami, folded paper, crease, paper craft, geometric]
    material: ["folded paper", "matte paper texture"]
    line: ["no line, crease as line"]
    color: ["solid pastel paper"]
    style: ["paper-craft sculpture"]
    avoidKeywords: [smooth organic, glossy, soft]
  namedReferences:
    illustrators: [Akira Yoshizawa, Robert Lang]
    movements: [Origami art, paper-craft 3D]
  examplePromptTemplate: |
    Origami folded-paper 3D sculpture of [SUBJECT], visible fold creases as
    structural lines, solid pastel paper color (mint / coral / cream), matte
    paper texture, triangular cast shadows, studio light, paper-craft sculpture
    aesthetic, Akira Yoshizawa inspired.
  whenToUse: Japanese-influenced brands, paper-product companies, mindfulness apps.
  pairsWith:
    prototypeStyles: [aesthetic-solarpunk, aesthetic-coastal-grandmother, recipe-warm-restraint, style-skeuomorphism]
  notForUseWhen: cyberpunk, brutalism

- styleId: low-poly-paper-3d
  name: Low-Poly Paper Craft 3D
  category: 3D
  subCategory: low-poly-paper
  role: subject
  source: curator addition
  visualSignatures:
    - faceted polygon surfaces like a paper Pepakura model
    - visible polygon edges as crisp lines
    - each face flat-shaded slightly different
    - reads as geometric trophy
  promptKeywords:
    primary: [low-poly, paper craft, faceted, polygon edges, Pepakura]
    material: ["folded card stock", "flat-shaded facets"]
    line: ["sharp polygon edge"]
    color: ["solid per-face flat shading"]
    style: ["trophy / wall mount"]
    avoidKeywords: [smooth subdiv, organic, soft]
  namedReferences:
    illustrators: [Pepakura, paperwolf]
    movements: [Low-poly paper sculpture]
  examplePromptTemplate: |
    Low-poly paper-craft 3D sculpture of [SUBJECT], faceted polygon surfaces
    like a Pepakura model, sharp polygon edges as visible creases, per-face
    flat shading in muted palette, wall-mount trophy composition, paper-craft
    aesthetic.
  whenToUse: Modern minimalist marketing, geometric brand identities.
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-constructivism, aesthetic-swiss-modernist]
  notForUseWhen: cute, soft, photoreal

- styleId: voxel-magicavoxel
  name: Voxel Art (MagicaVoxel)
  category: 3D
  subCategory: voxel
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - 3D pixel art — cubes assembled into figures
    - per-cube color, no smoothing
    - soft global illumination from MagicaVoxel render
    - reads as "modern Minecraft diorama"
  promptKeywords:
    primary: [voxel, 3d pixel, cube, MagicaVoxel, diorama]
    material: ["voxel cube", "soft GI render"]
    line: ["pixel edge per cube"]
    color: ["limited per-cube palette"]
    style: ["isometric diorama"]
    avoidKeywords: [smooth, organic, hairline]
  namedReferences:
    illustrators: [Sir carma, Zach Soares]
    movements: [Voxel art movement]
    productsOrFilms: [Crossy Road, Minecraft]
  examplePromptTemplate: |
    Voxel 3D pixel-art diorama of [SUBJECT], cubes assembled into form with
    per-cube color, soft MagicaVoxel global illumination, isometric composition,
    limited palette, modern voxel diorama aesthetic.
  whenToUse: Gaming brands, indie tech, pixel-revival marketing.
  pairsWith:
    prototypeStyles: [aesthetic-pixel-modern-cozy, aesthetic-pixel-snes-jrpg, aesthetic-pixel-arcade, aesthetic-rgb-gamer]
  notForUseWhen: editorial, brutalism, warm-restraint

- styleId: pixar-render-cinematic
  name: Pixar / Disney CGI cinematic
  category: 3D
  subCategory: render-cinematic
  role: subject
  source: curator addition (research)
  visualSignatures:
    - smooth 3D character with expressive big eyes
    - cinematic 3-point lighting with rim
    - subsurface skin, soft hair shader
    - vibrant saturated palette
  promptKeywords:
    primary: [Pixar, CGI, cinematic, expressive eyes, smooth render]
    material: ["smooth subsurface", "soft hair shader"]
    line: ["no line"]
    color: ["vibrant saturated"]
    style: ["3-point cinematic light", "rim highlight"]
    avoidKeywords: [photoreal-human, uncanny, flat]
  namedReferences:
    illustrators: [Pixar Animation Studios, Disney]
    movements: [CGI feature animation]
    productsOrFilms: [Inside Out, Soul, Coco]
  examplePromptTemplate: |
    Pixar-style CGI character of [SUBJECT], smooth 3D form with expressive
    oversized eyes, subsurface skin shader, soft hair, cinematic 3-point
    lighting with rim highlight, vibrant saturated palette, RenderMan-quality
    feature-animation aesthetic.
  whenToUse: Family brands, kid products, premium-friendly mascots.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, style-claymorphism]
  notForUseWhen: editorial, brutalism, restrained-AI

- styleId: ghibli-watercolor-bg
  name: Studio Ghibli watercolor background
  category: Anime / manga
  subCategory: ghibli-watercolor-bg
  role: hero
  source: curator addition (research)
  visualSignatures:
    - hand-painted watercolor matte background
    - layered cumulus skies, dappled forest light
    - pastoral European-village or Japanese-countryside settings
    - characters drawn in gentle line over painted bg
  promptKeywords:
    primary: [Studio Ghibli, watercolor background, hand-painted, pastoral]
    material: ["watercolor on textured paper"]
    line: ["gentle character line over painted bg"]
    color: ["soft natural palette — sky blue sage cream"]
    style: ["pastoral landscape", "layered cumulus sky"]
    avoidKeywords: [photoreal, neon, 3d render]
  namedReferences:
    illustrators: [Kazuo Oga, Studio Ghibli background team]
    movements: [Ghibli watercolor tradition]
    productsOrFilms: [My Neighbor Totoro, Spirited Away]
  examplePromptTemplate: |
    Studio Ghibli watercolor background of [SCENE], hand-painted matte watercolor,
    layered cumulus sky, dappled forest light, pastoral Japanese countryside,
    soft natural palette of sky blue sage and cream, gentle character outline
    over painted background, Kazuo Oga inspired.
  whenToUse: Wellness, mindfulness, nature brands, premium editorial.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-solarpunk, aesthetic-coastal-grandmother, recipe-warm-restraint, aesthetic-fairycore]
  notForUseWhen: tech, brutalism, neon

- styleId: shinkai-hyperreal-anime
  name: Makoto Shinkai hyperreal anime
  category: Anime / manga
  subCategory: shinkai-hyperreal
  role: hero
  source: curator addition (research)
  visualSignatures:
    - near-photographic anime backgrounds with stratus clouds
    - golden hour lens flare, dense cityscape
    - quiet two-shot character framing
    - melancholic palette — gold + dusk blue + neon sign
  promptKeywords:
    primary: [Makoto Shinkai, hyperreal anime, cinematic background, golden hour]
    material: ["digital paint cinematic"]
    line: ["clean character outline"]
    color: ["gold + dusk blue + neon"]
    style: ["stratus cloud sky", "lens flare", "two-shot framing"]
    avoidKeywords: [chibi, kawaii, flat]
  namedReferences:
    illustrators: [Makoto Shinkai, CoMix Wave Films]
    productsOrFilms: [Your Name, Weathering with You, Suzume]
  examplePromptTemplate: |
    Makoto Shinkai hyperreal anime scene of [SUBJECT], near-photographic detailed
    background, stratus cloud sky with golden hour lens flare, dense Japanese
    cityscape or suburban level crossing, palette of gold dusk blue and neon
    sign accents, quiet two-shot character framing, cinematic anime aesthetic.
  whenToUse: Premium anime-influenced product marketing, lifestyle storytelling.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, recipe-warm-restraint, aesthetic-coastal-grandmother]
  notForUseWhen: B2B serious, brutalism

- styleId: shoujo-soft-line-anime
  name: Shoujo soft-line anime
  category: Anime / manga
  subCategory: shoujo-soft-line
  role: subject
  source: curator addition
  visualSignatures:
    - delicate thin character lines
    - sparkles and screentone halos around characters
    - pastel pink and cream palette
    - large expressive eyes with star glints
  promptKeywords:
    primary: [shoujo, anime, soft line, sparkle, pastel]
    material: ["screentone overlay"]
    line: ["delicate 1-2px"]
    color: ["pastel pink cream sky"]
    style: ["sparkle halo", "star-glint eyes"]
    avoidKeywords: [thick brush, shonen action, dark]
  namedReferences:
    illustrators: [Naoshi Komi (later Nisekoi), Ai Yazawa, Arina Tanemura]
    movements: [Shoujo manga tradition]
  examplePromptTemplate: |
    Shoujo soft-line anime character [SUBJECT], delicate 1-2px line, large
    expressive eyes with star glints, pastel pink cream sky palette, screentone
    sparkle halo around character, Naoshi Komi / Ai Yazawa inspired soft shoujo
    aesthetic.
  whenToUse: Youth lifestyle, beauty, friendship apps, romance fiction.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-curly-girly, aesthetic-pc-98]
  notForUseWhen: B2B, brutalism

- styleId: kawaii-mascot
  name: Kawaii mascot
  category: Anime / manga
  subCategory: kawaii-mascot
  role: mascot
  source: curator addition
  visualSignatures:
    - super-cute round simplified character
    - oversized head, tiny body
    - simple dot eyes + smile mouth
    - pastel palette
  promptKeywords:
    primary: [kawaii, mascot, cute, chibi, oversized head]
    material: ["flat vector or soft 3d"]
    line: ["thin or no line"]
    color: ["pastel pink mint cream"]
    style: ["dot eye, simple smile"]
    avoidKeywords: [scary, edgy, brutalism]
  namedReferences:
    illustrators: [Sanrio, San-X]
    productsOrFilms: [Hello Kitty, Rilakkuma, Pusheen]
  examplePromptTemplate: |
    Super-cute kawaii mascot of [SUBJECT], oversized round head with tiny body,
    simple dot eyes and small smile mouth, pastel pink mint cream palette,
    Sanrio-style cute mascot aesthetic.
  whenToUse: Kid products, comfort apps, kawaii youth brands.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-curly-girly]
  notForUseWhen: B2B serious

- styleId: corporate-memphis-noodle
  name: Corporate Memphis noodle-people
  category: Flat vector
  subCategory: corporate-memphis
  role: subject
  source: curator addition (research)
  visualSignatures:
    - flat geometric humans, disproportionate
    - bendy noodle limbs, small heads
    - non-representational skin colors (blue, purple, green)
    - no facial features
    - flat saturated background
  promptKeywords:
    primary: [Corporate Memphis, noodle-people, flat geometric, faceless]
    material: ["pure flat vector"]
    line: ["no line"]
    color: ["non-representational skin — blue purple green + accent"]
    style: ["bendy noodle limbs", "flat solid bg"]
    avoidKeywords: [hand-drawn, 3d, photoreal skin]
  namedReferences:
    illustrators: [Alice Lee (Slack), Pablo Stanley, Buck Studio]
    movements: [Big Tech illustration 2019-2024]
    productsOrFilms: [Slack rebrand 2019, Google, Lyft, Airbnb]
  examplePromptTemplate: |
    Corporate Memphis flat vector illustration of figures, disproportionate
    bodies with bendy noodle limbs and small heads, non-representational skin
    colors (blue / purple / green), no facial features, flat solid-color
    background, Alice Lee Slack style.
  whenToUse: Big-tech mainstream marketing where neutrality is the safe choice.
    Use sparingly given fatigue.
  pairsWith:
    prototypeStyles: [aesthetic-corporate-memphis, recipe-bento-marketing, recipe-restrained-ai-marketing]
  notForUseWhen: indie / editorial / brutalism — anywhere personality matters

- styleId: thick-border-cartoon
  name: Thick-border cartoon (neubrutalism vector)
  category: Flat vector
  subCategory: thick-border-cartoon
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - 4-6px black outline around everything
    - flat saturated color fills
    - drop shadow offset 8px solid
    - reads as web brutalism cartoon
  promptKeywords:
    primary: [thick border, neubrutalism, flat color, hard outline]
    material: ["flat fill"]
    line: ["4-6px black"]
    color: ["saturated primary + bright pop"]
    style: ["8px offset hard drop shadow"]
    avoidKeywords: [soft, gradient, thin line]
  namedReferences:
    illustrators: [Gumroad rebrand 2021, neubrutalism designers]
    movements: [Neubrutalism]
  examplePromptTemplate: |
    Flat vector illustration of [SUBJECT] with 5px black hard outline, flat
    saturated primary color fills, 8px offset solid drop shadow, neubrutalism
    cartoon aesthetic, Gumroad-rebrand style.
  whenToUse: Indie SaaS, brutalist-adjacent marketing, devtools.
  pairsWith:
    prototypeStyles: [style-neubrutalism, aesthetic-neubrutalism, recipe-brutalist-web, aesthetic-web-brutalism]
  notForUseWhen: warm-restraint, editorial, refined

- styleId: jean-jullien-thick-line
  name: Jean Jullien thick brush cartoon
  category: Children's book / storybook
  subCategory: jean-jullien-thick-line
  role: subject
  source: curator addition (research)
  visualSignatures:
    - thick black brush stroke (8-10px) outlining everything
    - lively colored flat fill inside
    - simple sweet absurd subject matter
    - French Bande-Dessinée influence
  promptKeywords:
    primary: [Jean Jullien, thick brush, cartoon, witty, French BD]
    material: ["thick brush ink + flat color"]
    line: ["8-10px black brush"]
    color: ["lively flat fill, mid saturation"]
    style: ["humorous one-liner", "absurd observation"]
    avoidKeywords: [thin line, photoreal, complex shading]
  namedReferences:
    illustrators: [Jean Jullien, Sempé, Savignac, Tomi Ungerer]
    movements: [French BD revival]
  examplePromptTemplate: |
    Thick-brush cartoon illustration of [SUBJECT] in Jean Jullien style, 8-10px
    black brush stroke outlining everything, lively flat color fills, witty
    absurd one-liner observation, French Bande-Dessinée aesthetic.
  whenToUse: Editorial humor, indie books, friendly campaign branding.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-editorial-magazine, recipe-readcv]
  notForUseWhen: enterprise, photoreal

- styleId: risograph-illustration
  name: Risograph 2-color illustration
  category: Hand-drawn / sketch
  subCategory: gouache
  role: spot-illustration
  source: curator addition (research)
  visualSignatures:
    - 2-3 ink colors, semi-transparent overlays
    - visible grain (diffusion dither) or halftone screen
    - intentional registration shift creating colored fringes
    - palette: riso fluorescent pink + teal, or yellow + blue
  promptKeywords:
    primary: [risograph, riso, 2-color, registration shift, grain]
    material: ["soy-based riso ink", "diffusion dither grain"]
    line: ["selective"]
    color: ["riso fluorescent pink + teal", "registration misalignment"]
    style: ["visible halftone or grain"]
    avoidKeywords: [perfect register, smooth gradient, photoreal]
  namedReferences:
    illustrators: [Risotto Studio, Hato Press, Drawer]
    movements: [Risograph print revival]
  examplePromptTemplate: |
    Risograph 2-color illustration of [SUBJECT], soy-ink riso palette of
    fluorescent pink and teal, visible diffusion-dither grain, intentional
    registration shift creating colored fringes at edges, Risotto Studio
    aesthetic.
  whenToUse: Indie editorial, music zines, contemporary art posters.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, aesthetic-anti-design, style-raster-cutout]
  notForUseWhen: enterprise polish, photoreal

- styleId: saul-bass-cutout
  name: Saul Bass cutout collage
  category: Mid-century / vintage
  subCategory: saul-bass-cutout
  role: hero
  source: curator addition (research)
  visualSignatures:
    - bold cut-paper shapes with rough scissor edges
    - flat 2-3 color palette
    - dramatic composition with single strong concept
    - jagged hand-cut typography integrated
  promptKeywords:
    primary: [Saul Bass, cutout, paper collage, mid-century, dramatic]
    material: ["cut paper", "rough scissor edge"]
    line: ["no line, cut edge"]
    color: ["flat 2-3 saturated"]
    style: ["single strong concept", "dramatic composition"]
    avoidKeywords: [photoreal, soft, gradient]
  namedReferences:
    illustrators: [Saul Bass]
    productsOrFilms: [Anatomy of a Murder, Vertigo, Man with the Golden Arm]
  examplePromptTemplate: |
    Saul Bass cutout collage poster for [CONCEPT], bold cut-paper shapes with
    rough hand-cut scissor edges, flat 3-color palette of black + cream + red,
    single dramatic concept, jagged hand-cut typography integrated, mid-century
    film-title aesthetic.
  whenToUse: Editorial hero, premium film/event marketing, museum-quality identity.
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-atompunk, recipe-editorial-magazine, aesthetic-constructivism]
  notForUseWhen: friendly SaaS, brutalism, cottagecore

- styleId: charley-harper-minimal-realism
  name: Charley Harper minimal-realism nature
  category: Mid-century / vintage
  subCategory: charley-harper-minimal-realism
  role: spot-illustration
  source: curator addition (research)
  visualSignatures:
    - nature subjects (birds, fish, mammals) distilled to geometric shapes
    - flat clean color, no shading
    - symmetric balanced composition
    - palette: muted warm + spot of bright
  promptKeywords:
    primary: [Charley Harper, minimal realism, geometric nature, flat]
    material: ["screen print, flat ink"]
    line: ["clean edge, occasional hairline"]
    color: ["muted warm + bright spot"]
    style: ["symmetric balanced", "geometric distillation"]
    avoidKeywords: [photoreal nature, painterly, soft watercolor]
  namedReferences:
    illustrators: [Charley Harper]
    movements: [Mid-century modern nature illustration]
  examplePromptTemplate: |
    Charley Harper minimal-realism nature illustration of [BIRD/ANIMAL],
    distilled to geometric shapes, flat clean ink color, symmetric balanced
    composition, muted warm palette with one bright spot accent, US National
    Park Service poster aesthetic.
  whenToUse: Nature brands, conservation, premium outdoor goods.
  pairsWith:
    prototypeStyles: [aesthetic-solarpunk, aesthetic-cottagecore, recipe-warm-restraint, aesthetic-coastal-grandmother]
  notForUseWhen: photoreal, brutalism, cyberpunk

- styleId: mary-blair-stylized
  name: Mary Blair stylized mid-century
  category: Mid-century / vintage
  subCategory: mary-blair-stylized
  role: hero
  source: curator addition (research)
  visualSignatures:
    - 2D stylized characters with bold non-naturalistic color
    - flat geometric composition, swirling imaginative shapes
    - gouache and tempera matte texture
    - palette: turquoise + magenta + gold
  promptKeywords:
    primary: [Mary Blair, stylized, gouache, mid-century, swirling]
    material: ["gouache + tempera matte"]
    line: ["selective"]
    color: ["turquoise magenta gold non-naturalistic"]
    style: ["flat geometric", "swirling"]
    avoidKeywords: [photoreal, hyperreal anime, 3d]
  namedReferences:
    illustrators: [Mary Blair]
    productsOrFilms: [Cinderella concept, Alice in Wonderland, it's a small world]
  examplePromptTemplate: |
    Mary Blair stylized mid-century illustration of [SCENE], 2D flat geometric
    composition with swirling imaginative shapes, bold non-naturalistic palette
    of turquoise magenta and gold, gouache and tempera matte texture, Disney
    concept-art aesthetic.
  whenToUse: Premium kids brands, theme-park identity, vintage-feel editorial.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, recipe-editorial-magazine, aesthetic-fairycore]
  notForUseWhen: B2B, brutalism, tech

- styleId: eric-carle-tissue-collage
  name: Eric Carle tissue-paper collage
  category: Children's book / storybook
  subCategory: eric-carle-collage
  role: subject
  source: curator addition (research)
  visualSignatures:
    - subjects assembled from torn painted tissue paper
    - visible brush texture from underlying tissue painting
    - bright bold color, semi-transparent layered
    - rough torn edges
  promptKeywords:
    primary: [Eric Carle, tissue paper collage, torn edge, layered, painted texture]
    material: ["painted tissue paper", "acrylic brushwork", "glued layers"]
    line: ["no line, torn edge"]
    color: ["bright bold, semi-transparent overlap"]
    style: ["children's book illustration"]
    avoidKeywords: [vector flat, 3d, smooth digital]
  namedReferences:
    illustrators: [Eric Carle]
    productsOrFilms: [The Very Hungry Caterpillar, Brown Bear]
  examplePromptTemplate: |
    Eric Carle tissue-paper collage of [SUBJECT], assembled from torn painted
    tissue paper with visible acrylic brush texture, bright bold layered color
    with semi-transparent overlap, rough torn edges, children's book aesthetic.
  whenToUse: Kids brands, education products, picture-book aesthetic.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-cottagecore, style-raster-cutout]
  notForUseWhen: B2B, brutalism, polished tech

- styleId: beatrix-potter-watercolor
  name: Beatrix Potter soft watercolor
  category: Children's book / storybook
  subCategory: beatrix-potter-watercolor
  role: subject
  source: curator addition (research)
  visualSignatures:
    - animals in human clothing (dresses, suits)
    - soft muted watercolor + pen-and-ink line
    - palette: moss green, cranberry, tan, walnut
    - cottage / pastoral setting
  promptKeywords:
    primary: [Beatrix Potter, watercolor, pen-and-ink, animal in clothing, pastoral]
    material: ["soft watercolor on paper", "pen-and-ink outline"]
    line: ["fine 0.5px ink"]
    color: ["moss green cranberry tan walnut"]
    style: ["humanized animal", "pastoral cottage"]
    avoidKeywords: [vector flat, neon, photoreal]
  namedReferences:
    illustrators: [Beatrix Potter]
    productsOrFilms: [The Tale of Peter Rabbit]
  examplePromptTemplate: |
    Beatrix Potter soft watercolor illustration of [ANIMAL] wearing tiny human
    clothing (dress / coat), fine pen-and-ink outline, muted palette of moss
    green cranberry tan and walnut, pastoral cottage setting, classic children's
    book aesthetic.
  whenToUse: Children's bookstore brands, cottagecore lifestyle, English-country
    apothecary, heritage brands.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-cottagegoth, recipe-warm-restraint, aesthetic-dark-academia]
  notForUseWhen: tech, brutalism, modern minimal

- styleId: gouache-storybook
  name: Modern gouache storybook
  category: Hand-drawn / sketch
  subCategory: gouache
  role: subject
  source: curator addition (research)
  visualSignatures:
    - opaque matte gouache layered blocky color
    - dry-brush highlights visible
    - paper grain showing through midtones
    - hand-painted edges
  promptKeywords:
    primary: [gouache, opaque matte, dry-brush, paper grain]
    material: ["gouache on cold-press paper"]
    line: ["selective ink line"]
    color: ["muted layered"]
    style: ["storybook painterly"]
    avoidKeywords: [vector smooth, digital flat]
  namedReferences:
    illustrators: [Carson Ellis, Yelena Bryksenkova]
  examplePromptTemplate: |
    Modern gouache storybook illustration of [SUBJECT], opaque matte gouache
    layered blocky color, dry-brush highlights, subtle paper grain in midtones,
    hand-painted edges, muted palette, Carson Ellis aesthetic.
  whenToUse: Children's books, editorial, indie storytelling.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, recipe-warm-restraint, recipe-editorial-magazine, aesthetic-dark-academia]
  notForUseWhen: tech, brutalism

- styleId: niemann-puzzle-conceptual
  name: Christoph Niemann puzzle-design
  category: Editorial conceptual
  subCategory: niemann-puzzle
  role: spot-illustration
  source: curator addition (research)
  visualSignatures:
    - minimal line work over real object photo
    - clever conceptual visual puzzle
    - 2-3 elements max — viewer fills in 98%
  promptKeywords:
    primary: [Christoph Niemann, puzzle, conceptual, minimal, witty]
    material: ["mixed media — object + line over"]
    line: ["minimal precise 1-2px"]
    color: ["limited 1-2 color"]
    style: ["conceptual one-idea"]
    avoidKeywords: [busy, decorative, photoreal]
  namedReferences:
    illustrators: [Christoph Niemann]
    productsOrFilms: [Sunday Sketches, New Yorker covers]
  examplePromptTemplate: |
    Christoph Niemann conceptual puzzle illustration: a [REAL OBJECT] photographed
    flat on white, minimal 2px precise line drawn over it transforms it into
    [CONCEPT] — viewer's brain completes the joke, 2 colors maximum, Sunday
    Sketches aesthetic.
  whenToUse: Editorial think-pieces, op-ed, magazine cover.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-newspaper-of-record, recipe-readcv, style-serif-warm-paper]
  notForUseWhen: marketing-decorative, brutalism

- styleId: keith-haring-radiant
  name: Keith Haring radiant pop
  category: Mid-century / vintage
  subCategory: 1960s-psychedelic
  role: subject
  source: curator addition (research)
  visualSignatures:
    - thick uniform black lines defining all forms
    - simple cartoon figures, often dancing
    - radiant motion lines around figures
    - block-color background, no shading
  promptKeywords:
    primary: [Keith Haring, thick black line, dancing figure, radiant lines]
    material: ["felt-tip marker", "flat block color"]
    line: ["uniform thick 6px"]
    color: ["primary red yellow blue green"]
    style: ["radiant motion lines", "simplified figure"]
    avoidKeywords: [thin line, gradient, photoreal]
  namedReferences:
    illustrators: [Keith Haring]
    movements: [1980s NYC street art / pop]
  examplePromptTemplate: |
    Keith Haring pop-art illustration of dancing figures, thick uniform 6px
    black outline, radiant motion lines around figures, flat primary palette
    of red yellow blue and green, no shading, 1980s NYC street-art aesthetic.
  whenToUse: Pride campaigns, activism brands, youth culture, music venues.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-maximalism, aesthetic-anti-design]
  notForUseWhen: enterprise, brutalism, cottagecore

- styleId: hilma-af-klint-symbolist
  name: Hilma af Klint esoteric symbolism
  category: Surreal / esoteric
  subCategory: hilma-symbolist
  role: hero
  source: curator addition (research)
  visualSignatures:
    - geometric forms with spiritual symbolic meaning
    - spirals, helixes, vesica piscis, U/W glyphs
    - pastel palette — sea green, lilac, rose pink, soft yellow
    - botanical motifs overlaid with sacred geometry
  promptKeywords:
    primary: [Hilma af Klint, esoteric, symbolist, spiral, sacred geometry, pastel]
    material: ["watercolor + gouache on paper"]
    line: ["fine hand-drawn"]
    color: ["pastel sea-green lilac rose-pink soft yellow"]
    style: ["spiral evolution motif", "botanical + geometry overlay"]
    avoidKeywords: [neon, photoreal, brutalism]
  namedReferences:
    illustrators: [Hilma af Klint]
    movements: [Symbolism, Theosophy, abstract pioneers]
  examplePromptTemplate: |
    Hilma af Klint esoteric symbolist composition with logarithmic spirals,
    vesica piscis, U-glyph for spiritual realm, botanical flower motif with
    sacred geometry overlay, pastel palette of sea green lilac rose pink and
    soft yellow, watercolor and gouache, Paintings for the Temple aesthetic.
  whenToUse: Mindfulness, wellness, esoteric brands, premium editorial hero.
  pairsWith:
    prototypeStyles: [aesthetic-angelcore, aesthetic-dreamcore, aesthetic-fairycore, style-aurorism]
  notForUseWhen: tech, brutalism, neon

- styleId: mc-escher-paradox
  name: M.C. Escher impossible geometry
  category: Surreal / esoteric
  subCategory: mc-escher-paradox
  role: hero
  source: curator addition (research)
  visualSignatures:
    - tessellated repeating shapes that transform
    - impossible architecture (Penrose stairs, infinite stairwell)
    - high-contrast lithograph black-and-white
    - mathematical precision lines
  promptKeywords:
    primary: [Escher, tessellation, impossible geometry, Penrose, lithograph]
    material: ["lithograph wood engraving"]
    line: ["mathematical precision"]
    color: ["pure black on warm cream"]
    style: ["tessellated metamorphosis", "impossible architecture"]
    avoidKeywords: [color, soft, photoreal]
  namedReferences:
    illustrators: [M.C. Escher, Roger Penrose]
  examplePromptTemplate: |
    M.C. Escher impossible-geometry composition with tessellated shapes
    metamorphosing across the plane, impossible architectural staircase
    based on Penrose triangle, lithograph black-on-cream, mathematical
    precision lines, mid-century surrealist aesthetic.
  whenToUse: Math / science brands, puzzle products, premium editorial.
  pairsWith:
    prototypeStyles: [aesthetic-op-art, aesthetic-constructivism, recipe-editorial-magazine]
  notForUseWhen: friendly consumer, cottagecore

- styleId: cyriak-bodyhorror
  name: Cyriak surreal multiplication
  category: Surreal / esoteric
  subCategory: cyriak-bodyhorror
  role: hero
  source: curator addition (research)
  visualSignatures:
    - photoreal source material multiplied into impossible forms
    - eyes, limbs, mouths replicating across the form
    - Droste-effect recursion
    - body horror but darkly comic
  promptKeywords:
    primary: [Cyriak, surreal multiplication, body horror, Droste effect]
    material: ["photo composite", "After Effects layering"]
    line: ["mask-cut edge"]
    color: ["photoreal source"]
    style: ["impossible multiplication", "recursive"]
    avoidKeywords: [cute, friendly, hand-drawn]
  namedReferences:
    illustrators: [Cyriak Harris]
  examplePromptTemplate: |
    Cyriak-style surreal photo composite of [SUBJECT] with limbs and eyes
    multiplied across the form into Droste-effect recursion, masked photoreal
    source material, darkly comic body horror, impossible multiplication
    aesthetic.
  whenToUse: Music videos, edgy editorial, surreal art-house brands. Use carefully.
  pairsWith:
    prototypeStyles: [aesthetic-dreamcore, aesthetic-anti-design, aesthetic-acid-graphics]
  notForUseWhen: friendly, B2B, family

- styleId: beeple-dystopia
  name: Beeple dystopian 3D
  category: Surreal / esoteric
  subCategory: beeple-dystopia
  role: hero
  source: curator addition (research)
  visualSignatures:
    - oversized human figures in bleak future landscape
    - Cinema 4D + Octane render quality
    - dramatic post-apocalyptic lighting
    - political commentary subject
  promptKeywords:
    primary: [Beeple, dystopian 3D, Cinema 4D, Octane, oversized figure]
    material: ["Octane render", "physically based"]
    line: ["no line"]
    color: ["smoky red sky", "industrial grey"]
    style: ["bleak landscape", "oversized figure"]
    avoidKeywords: [friendly, pastel, soft]
  namedReferences:
    illustrators: [Mike Winkelmann / Beeple]
    productsOrFilms: [EVERYDAYS, Manifest Destiny]
  examplePromptTemplate: |
    Beeple-style dystopian 3D scene of an oversized human figure in bleak
    post-apocalyptic landscape, dramatic smoky red sky with industrial grey,
    Cinema 4D + Octane render quality, political commentary subject,
    EVERYDAYS aesthetic.
  whenToUse: Edgy cultural commentary, NFT-adjacent art brand, music album.
  pairsWith:
    prototypeStyles: [aesthetic-crypto-degen, aesthetic-cyberpunk, recipe-ai-foundry-dark]
  notForUseWhen: friendly SaaS, kids, restrained AI marketing

- styleId: frida-folk-surreal
  name: Frida Kahlo folk surrealism
  category: Surreal / esoteric
  subCategory: frida-folk-surreal
  role: hero
  source: curator addition (research)
  visualSignatures:
    - botanical vines framing portrait
    - symbolic animals (monkeys, deer)
    - vibrant Mexican folk palette
    - personal-iconography surreal
  promptKeywords:
    primary: [Frida Kahlo, folk surrealism, botanical frame, Mexican palette, symbolic]
    material: ["oil on tin / canvas"]
    line: ["fine detailed"]
    color: ["vibrant Mexican — vermillion turquoise jade gold"]
    style: ["botanical framing", "symbolic animal"]
    avoidKeywords: [European surrealism, hands-off, abstract]
  namedReferences:
    illustrators: [Frida Kahlo]
    movements: [Mexican folk art, personal surrealism]
  examplePromptTemplate: |
    Frida Kahlo folk-surrealist composition of [SUBJECT], framed by lush
    botanical vines with symbolic monkeys and parrots, vibrant Mexican palette
    of vermillion turquoise jade and gold, oil-on-tin texture, personal
    symbolic surrealism aesthetic.
  whenToUse: Mexican-influenced brands, latina identity, cultural celebration.
  pairsWith:
    prototypeStyles: [aesthetic-maximalism, aesthetic-cottagecore, aesthetic-y2k-memphis-loud]
  notForUseWhen: minimalist tech, brutalism

- styleId: vector-hands-up-eurodance
  name: Vector hands-up Eurodance
  category: Anime / manga
  subCategory: pc98-visual-novel
  role: subject
  source: curator addition (research) + prototype/aesthetic-vector-hands-up
  visualSignatures:
    - high-gloss anime-inflected vector characters
    - cyan + lime green + hot pink palette
    - rave-gear (headphones, visors, glowsticks)
    - bright sparkles, lens flare
  promptKeywords:
    primary: [Eurodance, vector anime, hands up, rave, glossy]
    material: ["glossy vector", "specular highlights"]
    line: ["clean 1px"]
    color: ["cyan lime hot pink silver"]
    style: ["raised arms pose", "headphones visor"]
    avoidKeywords: [matte, muted, hand-drawn rough]
  namedReferences:
    illustrators: [Eurodance / Hands Up record sleeves, early Nightcore]
  examplePromptTemplate: |
    High-gloss vector anime character with raised arms in Eurodance pose, rave
    headphones and visor, glossy specular highlights, palette of cyan lime green
    hot pink and chrome silver, sparkles and lens flare, late-90s Hands-Up
    record-sleeve aesthetic.
  whenToUse: Music marketing, rave/dance branding, Y2K revival.
  pairsWith:
    prototypeStyles: [aesthetic-vector-hands-up, aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-acid-design]
  notForUseWhen: editorial restraint, B2B

- styleId: isometric-tech-saas
  name: Isometric tech SaaS scene
  category: 3D
  subCategory: isometric-tech
  role: hero
  source: curator addition (research)
  visualSignatures:
    - 2.5D isometric scenes of platform architecture
    - gradient backgrounds (purple-to-blue tech)
    - soft shadows and glows for depth
    - characters interacting with floating UI panels
  promptKeywords:
    primary: [isometric, tech, SaaS, 2.5D, platform architecture]
    material: ["soft-shaded vector + gradient"]
    line: ["selective hairline"]
    color: ["purple-to-blue gradient bg + accent"]
    style: ["floating UI panels", "soft glow"]
    avoidKeywords: [hand-drawn, photoreal, brutalism]
  namedReferences:
    illustrators: [IBM Design Language, Intercom, Google Cloud]
    movements: [B2B SaaS marketing 2020+]
  examplePromptTemplate: |
    2.5D isometric SaaS scene showing platform architecture with floating UI
    panels and small characters interacting, soft-shaded vector with subtle
    gradient surfaces, purple-to-blue tech gradient background, soft glow
    accents, IBM-era B2B isometric aesthetic.
  whenToUse: B2B SaaS hero, platform marketing, technical onboarding.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-linear-product-ui, recipe-devtools-marketing, recipe-scientific-infra-marketing]
  notForUseWhen: editorial, brutalism, cottagecore

- styleId: dreamcore-liminal
  name: Dreamcore liminal scene
  category: Surreal / esoteric
  subCategory: dreamcore-liminal
  role: hero
  source: curator addition + prototype/aesthetic-dreamcore
  visualSignatures:
    - faded photo of empty mundane space (hallway, pool, mall)
    - oversaturated nostalgic palette
    - subtle wrong-ness (impossible architecture, no people)
    - VHS / film-grain texture
  promptKeywords:
    primary: [dreamcore, liminal space, nostalgic, faded photo, wrong]
    material: ["VHS grain texture", "film-photo"]
    line: ["no line"]
    color: ["oversaturated nostalgic — yellow-green + carpet pink"]
    style: ["empty mundane space", "no people", "subtle architectural wrongness"]
    avoidKeywords: [vector clean, bright happy, character]
  namedReferences:
    illustrators: [r/LiminalSpace, Backrooms creepypasta]
    movements: [Dreamcore, Backrooms, weirdcore]
  examplePromptTemplate: |
    Dreamcore liminal-space photo of empty 1990s motel hallway with no people,
    oversaturated nostalgic palette of yellow-green carpet pink and fluorescent
    cream, VHS grain texture, subtle architectural wrongness, faded film-photo
    quality, weirdcore aesthetic.
  whenToUse: Art-house brand, surreal music, indie horror.
  pairsWith:
    prototypeStyles: [aesthetic-dreamcore, aesthetic-vaporwave, aesthetic-cottagegoth]
  notForUseWhen: SaaS friendly, B2B, kids

- styleId: hand-drawn-pencil-sketch
  name: Pencil graphite sketch
  category: Hand-drawn / sketch
  subCategory: pencil-graphite
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - HB-to-6B graphite range on cream paper
    - cross-hatching for shadow
    - visible eraser marks and construction lines
    - feels like sketchbook page
  promptKeywords:
    primary: [pencil, graphite, cross-hatch, sketchbook]
    material: ["HB-6B graphite on cream paper"]
    line: ["soft graphite stroke"]
    color: ["mono graphite + paper cream"]
    style: ["construction lines visible", "sketchbook"]
    avoidKeywords: [vector clean, color, photoreal]
  namedReferences:
    illustrators: [da Vinci notebooks, Quentin Blake]
  examplePromptTemplate: |
    Pencil-graphite sketch of [SUBJECT] on cream paper, HB-to-6B range with
    cross-hatched shadows, visible construction lines and faint eraser marks,
    sketchbook-page aesthetic.
  whenToUse: Editorial illustration, design portfolios, hand-craft brands.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, aesthetic-dark-academia, recipe-warm-restraint]
  notForUseWhen: tech, brutalism, polished

- styleId: charcoal-loose
  name: Loose charcoal sketch
  category: Hand-drawn / sketch
  subCategory: charcoal
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - smudged willow charcoal
    - rich darks contrasted with paper white
    - bold expressive strokes
  promptKeywords:
    primary: [charcoal, smudged, willow, expressive]
    material: ["willow charcoal on white paper"]
    line: ["broad smudged stroke"]
    color: ["pure black + paper white"]
    style: ["expressive mark-making"]
    avoidKeywords: [precise, vector, color]
  examplePromptTemplate: |
    Loose willow-charcoal sketch of [SUBJECT] with smudged broad strokes, rich
    darks, paper white showing through, expressive mark-making.
  whenToUse: Editorial portrait, art-school brand.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-dark-academia]
  notForUseWhen: tech, brutalism, polished

- styleId: crayon-wax-children
  name: Crayon / wax children
  category: Hand-drawn / sketch
  subCategory: crayon-wax
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - waxy texture with visible drag marks
    - bright bold primary colors
    - intentional childlike quality
  promptKeywords:
    primary: [crayon, wax, childlike, drag mark]
    material: ["wax crayon on textured paper"]
    line: ["waxy thick stroke"]
    color: ["bright primary"]
    style: ["intentionally childlike"]
    avoidKeywords: [refined, vector, smooth]
  examplePromptTemplate: |
    Wax-crayon drawing of [SUBJECT] with visible drag-mark texture, bright
    primary colors, intentionally childlike quality on textured paper.
  whenToUse: Kids products, education, playful campaigns.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, aesthetic-wacky-pomo, aesthetic-cluttercore]
  notForUseWhen: enterprise, brutalism

- styleId: pixel-bitmap-illustration
  name: Pixel bitmap illustration
  category: 3D
  subCategory: voxel
  role: subject
  source: curator addition + prototype/style-pixel-bitmap
  visualSignatures:
    - explicit pixel grid, no anti-aliasing
    - limited palette per era (NES 4-color, GameBoy 4-shade, SNES 16-color)
    - dithering for shading
  promptKeywords:
    primary: [pixel art, bitmap, dithering, limited palette]
    material: ["8-bit or 16-bit pixel"]
    line: ["pixel-grid edge"]
    color: ["era-limited palette"]
    style: ["dither shading", "explicit grid"]
    avoidKeywords: [smooth, vector, anti-aliased]
  namedReferences:
    illustrators: [Capcom NES era, eBoy]
    productsOrFilms: [NES Mario, GameBoy Pokemon, Stardew Valley]
  examplePromptTemplate: |
    Pixel bitmap illustration of [SUBJECT] with explicit pixel grid no anti-
    aliasing, [ERA]-limited palette, dithering for shading, isolated on
    transparent or solid color background.
  whenToUse: Gaming brands, retro tech, indie game marketing.
  pairsWith:
    prototypeStyles: [aesthetic-pixel-nes-mario, aesthetic-pixel-game-boy-mono, aesthetic-pixel-snes-jrpg, aesthetic-pixel-arcade, aesthetic-pixel-modern-cozy, aesthetic-pixel-ps1-tactics-ogre, style-pixel-bitmap]
  notForUseWhen: cinematic, photoreal, warm-restraint

- styleId: claymation-stop-motion
  name: Claymation stop-motion 3D
  category: 3D
  subCategory: claymation-stop-motion
  role: subject
  source: curator addition (research)
  visualSignatures:
    - clay character with armature bones showing through pose
    - imperfect surface — thumbprints, tool marks
    - hand-painted backdrop
    - palette: school-set primaries
  promptKeywords:
    primary: [claymation, stop motion, armature, imperfect, hand-painted backdrop]
    material: ["plasticine over wire armature", "matte clay"]
    line: ["no line"]
    color: ["school primary"]
    style: ["hand-painted backdrop", "single frame from animation"]
    avoidKeywords: [smooth digital, photoreal, vector]
  namedReferences:
    illustrators: [Aardman, Laika, Henry Selick]
    productsOrFilms: [Wallace & Gromit, Coraline, Chicken Run]
  examplePromptTemplate: |
    Claymation stop-motion still of [SUBJECT], plasticine clay character over
    wire armature with visible thumbprints and tool marks, hand-painted backdrop,
    school-set primary palette, Aardman Wallace-and-Gromit aesthetic.
  whenToUse: Children's brands, premium kid film marketing.
  pairsWith:
    prototypeStyles: [aesthetic-positivity-kawaii, style-claymorphism, aesthetic-wacky-pomo]
  notForUseWhen: enterprise, brutalism

- styleId: aurorism-mesh-gradient
  name: Aurorism mesh gradient
  category: Abstract / decoration
  subCategory: aurorism-mesh
  role: decoration
  source: curator addition + prototype/style-aurorism
  visualSignatures:
    - smooth multi-stop mesh gradient
    - aurora borealis colors flowing
    - background-fill role
    - no defined shape — fills the canvas
  promptKeywords:
    primary: [mesh gradient, aurora, smooth blend, background, ethereal]
    material: ["mesh gradient"]
    line: ["no line"]
    color: ["aurora — teal violet pink sage flow"]
    style: ["full-bleed background fill"]
    avoidKeywords: [hard edge, geometric, line]
  namedReferences:
    illustrators: [Stripe website, Apple iOS wallpapers, Vercel]
  examplePromptTemplate: |
    Aurora mesh-gradient background, smooth multi-stop blend of teal violet
    pink and sage flowing like northern lights, full-bleed canvas decoration,
    ethereal Aurorism aesthetic.
  whenToUse: Hero backgrounds, AI/tech marketing decoration.
  pairsWith:
    prototypeStyles: [style-aurorism, recipe-aurora-marketing, recipe-ai-foundry-dark, recipe-restrained-ai-marketing, style-holographic, style-liquid-glass]
  notForUseWhen: brutalism, editorial, terminal

- styleId: halftone-shape
  name: Halftone retro shape
  category: Abstract / decoration
  subCategory: halftone-shape
  role: decoration
  source: curator addition
  visualSignatures:
    - circle / arc / wave with halftone-dot fill
    - retro print-press aesthetic
    - mono or 2-color
  promptKeywords:
    primary: [halftone, dot pattern, retro print, shape decoration]
    material: ["halftone screen"]
    line: ["selective"]
    color: ["mono or 2-color"]
    style: ["retro print accent"]
    avoidKeywords: [smooth gradient, photoreal]
  examplePromptTemplate: |
    Halftone-dot fill geometric shape (circle / arc / wave), retro print-press
    aesthetic, mono or 2-color, decoration accent.
  whenToUse: Editorial accents, indie posters, retro branding.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-anti-design, aesthetic-y2k-memphis-loud]
  notForUseWhen: minimalist clean SaaS

- styleId: sticker-cutout-puffy
  name: Sticker cutout puffy
  category: Abstract / decoration
  subCategory: sticker-cutout
  role: decoration
  source: curator addition
  visualSignatures:
    - subject with white halo outline like die-cut sticker
    - subtle drop shadow for "stuck on" feel
    - slight 3D pillow lift
  promptKeywords:
    primary: [sticker, die-cut, white halo, puffy]
    material: ["flat fill or soft 3d"]
    line: ["white halo 8px"]
    color: ["mixed varied"]
    style: ["puffy lift", "drop shadow"]
    avoidKeywords: [no halo, integrated]
  examplePromptTemplate: |
    Die-cut sticker of [SUBJECT] with 8px white halo outline, subtle drop
    shadow for stuck-on feel, slight 3D pillow lift, isolated on background.
  whenToUse: Casual product pages, scrapbook substrates, playful marketing.
  pairsWith:
    prototypeStyles: [shell-scrapbook-substrate, aesthetic-cluttercore, recipe-bento-marketing]
  notForUseWhen: editorial restraint, brutalism

- styleId: editorial-thick-brush
  name: Editorial thick-brush op-ed
  category: Editorial conceptual
  subCategory: editorial-thick-brush
  role: spot-illustration
  source: curator addition
  visualSignatures:
    - bold thick painted strokes
    - 1-2 colors max plus paper white
    - conceptual single-idea composition
    - newspaper opinion-page aesthetic
  promptKeywords:
    primary: [editorial, thick brush, op-ed, conceptual, mono color]
    material: ["sumi-e style ink brush"]
    line: ["thick gestural brush"]
    color: ["mono + cream paper"]
    style: ["op-ed conceptual"]
    avoidKeywords: [decorative, vector polished, full color]
  namedReferences:
    illustrators: [Brian Stauffer, Wesley Bedrosian]
  examplePromptTemplate: |
    Editorial op-ed conceptual illustration of [IDEA] with bold thick painted
    brush strokes, 1-2 colors plus cream paper, single concept, NYT-opinion-
    page aesthetic.
  whenToUse: News op-eds, think-pieces, magazine articles.
  pairsWith:
    prototypeStyles: [recipe-newspaper-of-record, recipe-editorial-magazine, style-agate-broadsheet]
  notForUseWhen: marketing, friendly, decorative

- styleId: outline-wireframe-illustration
  name: Outline wireframe illustration
  category: Flat vector
  subCategory: hairline
  role: spot-illustration
  source: curator addition + prototype/style-outline-wireframe
  visualSignatures:
    - 1-2px line, no fill
    - all forms in single stroke weight
    - clean geometric
  promptKeywords:
    primary: [outline, wireframe, hairline, line only, no fill]
    material: ["vector hairline only"]
    line: ["1-2px uniform"]
    color: ["mono or single accent"]
    style: ["clean geometric"]
    avoidKeywords: [filled, gradient, shading]
  examplePromptTemplate: |
    Hairline outline illustration of [SUBJECT], 1.5px uniform stroke, no fill,
    all forms in single weight, mono or single accent color, clean geometric
    wireframe aesthetic.
  whenToUse: Restrained AI marketing, premium tech, technical diagrams.
  pairsWith:
    prototypeStyles: [style-outline-wireframe, style-restrained-hairline, recipe-restrained-ai-marketing, recipe-linear-product-ui]
  notForUseWhen: cottagecore, brutalism, kids

- styleId: bauhaus-geometric
  name: Bauhaus pure geometric
  category: Mid-century / vintage
  subCategory: eames-mid-century
  role: hero
  source: curator addition + prototype/aesthetic-bauhaus
  visualSignatures:
    - primary geometric shapes — circle, square, triangle
    - primary colors only — red blue yellow on black/white
    - rigid composition
  promptKeywords:
    primary: [Bauhaus, geometric primitive, primary color, rigid composition]
    material: ["flat ink"]
    line: ["geometric edge"]
    color: ["primary red blue yellow + black"]
    style: ["rigid grid"]
    avoidKeywords: [organic, soft, decorative]
  namedReferences:
    illustrators: [Herbert Bayer, László Moholy-Nagy, Josef Albers]
  examplePromptTemplate: |
    Bauhaus geometric composition of [SUBJECT] using primary shapes (circle
    square triangle) and primary colors (red blue yellow) on black or white,
    rigid grid composition, Herbert Bayer aesthetic.
  whenToUse: Design education, modernist brand, architectural firms.
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-de-stijl, aesthetic-constructivism, aesthetic-swiss-modernist]
  notForUseWhen: warm, cottagecore, playful

- styleId: raster-cutout-collage
  name: Raster cutout collage
  category: Mid-century / vintage
  subCategory: 1970s-airbrush
  role: hero
  source: curator addition + prototype/style-raster-cutout
  visualSignatures:
    - photo cutouts assembled into surreal scene
    - intentionally ragged edges
    - mixed-media zine aesthetic
    - includes magazine-clip texture
  promptKeywords:
    primary: [photo cutout, collage, ragged edge, mixed media, zine]
    material: ["scanned photo + paper texture"]
    line: ["cut edge"]
    color: ["mixed source photos"]
    style: ["surreal arrangement", "zine"]
    avoidKeywords: [vector flat, smooth digital]
  namedReferences:
    illustrators: [Linder Sterling, Hannah Höch]
  examplePromptTemplate: |
    Raster photo-cutout collage of [SCENE], scanned magazine photos assembled
    with intentionally ragged cut edges, mixed-media zine aesthetic, surreal
    arrangement.
  whenToUse: Music posters, fashion editorial, contemporary art.
  pairsWith:
    prototypeStyles: [style-raster-cutout, aesthetic-anti-design, aesthetic-acid-design, recipe-editorial-magazine]
  notForUseWhen: B2B, polished SaaS

- styleId: doodle-ui-handdrawn
  name: Doodle UI hand-drawn (Excalidraw-style)
  category: Hand-drawn / sketch
  subCategory: scribble-marker
  role: spot-illustration
  source: curator addition + prototype/style-doodle
  visualSignatures:
    - wobbly hand-drawn line as if on whiteboard
    - irregular shape — never perfectly circular
    - subtle marker texture
    - black or single-color, white fill
  promptKeywords:
    primary: [doodle, hand-drawn UI, whiteboard, Excalidraw]
    material: ["whiteboard marker"]
    line: ["wobbly 2px, slight irregularity"]
    color: ["mono black or 1 accent"]
    style: ["informal sketch"]
    avoidKeywords: [precise vector, gradient]
  namedReferences:
    illustrators: [Excalidraw, tldraw, Whimsical]
  examplePromptTemplate: |
    Doodle UI hand-drawn illustration of [SUBJECT] with wobbly 2px marker line,
    irregular shapes never perfectly geometric, mono black with one accent,
    Excalidraw whiteboard-sketch aesthetic.
  whenToUse: Devtools marketing, design-thinking brands, whiteboard-app products.
  pairsWith:
    prototypeStyles: [style-doodle, recipe-devtools-marketing, recipe-readcv]
  notForUseWhen: photoreal, enterprise polish

- styleId: liquid-glass-3d
  name: Liquid glass 3D translucent
  category: 3D
  subCategory: plastic-glossy
  role: spot-illustration
  source: curator addition + prototype/style-liquid-glass
  visualSignatures:
    - translucent refractive glass-like surface
    - chromatic aberration on edges
    - iOS-style liquid blob
  promptKeywords:
    primary: [liquid glass, translucent, refractive, glass blob, iOS]
    material: ["refractive glass", "chromatic aberration"]
    line: ["no line, refractive edge"]
    color: ["light blue tint + caustic highlight"]
    style: ["iOS liquid"]
    avoidKeywords: [matte, opaque, hand-drawn]
  namedReferences:
    illustrators: [Apple iOS 18+, Apple Vision Pro UI]
  examplePromptTemplate: |
    Liquid-glass 3D translucent object of [SUBJECT], refractive glass surface
    with chromatic aberration on edges, light blue tint with caustic highlight,
    Apple iOS liquid-glass aesthetic.
  whenToUse: Apple-ecosystem products, premium iOS-aligned brands.
  pairsWith:
    prototypeStyles: [style-liquid-glass, recipe-ios-system, style-sf-pro-ios, style-glassmorphism]
  notForUseWhen: brutalism, cottagecore, hand-drawn

- styleId: skeuomorphic-detailed
  name: Skeuomorphic detailed object
  category: 3D
  subCategory: render-cinematic
  role: spot-illustration
  source: curator addition + prototype/style-skeuomorphism
  visualSignatures:
    - photoreal materials — leather stitch, brushed metal, wood grain
    - extensive detail
    - iOS 6-era textures
  promptKeywords:
    primary: [skeuomorphic, photoreal material, leather, brushed metal, wood grain]
    material: ["leather stitched", "brushed aluminum", "polished wood"]
    line: ["detail stitches"]
    color: ["natural materials"]
    style: ["iOS 6 texture"]
    avoidKeywords: [flat, vector, abstract]
  namedReferences:
    illustrators: [Apple iOS 6 design]
  examplePromptTemplate: |
    Skeuomorphic detailed 3D rendering of [SUBJECT] with photoreal material
    detail — leather stitching, brushed aluminum, polished wood grain, iOS-6
    era texture quality, octane render.
  whenToUse: Premium consumer products with material storytelling.
  pairsWith:
    prototypeStyles: [style-skeuomorphism, recipe-warm-restraint]
  notForUseWhen: flat-vector marketing, brutalism

---

## 3. Category × prototype decision tree

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
