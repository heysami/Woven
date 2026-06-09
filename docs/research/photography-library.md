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

---

## 2. Style library

Each entry below is one distinct photographic style. The orchestrator should pick at most two and combine via the chaining rules in §5.

---

- styleId: helmut-newton-flash
  name: Helmut Newton on-camera flash glamour
  era: 1970s-1990s
  category: editorial-fashion
  visualSignatures:
    - Single hard flash on a tall confident female subject, falloff into pure black
    - Hotel rooms, swimming pools, parking garages, marble lobbies
    - Implied narrative of power, sex, surveillance
    - Often shot in daylight with fill flash, kicker shadow on the wall
  promptKeywords:
    primary: [tall confident woman, marble hotel lobby, stiletto heels, fall-off into black, mid-stride, oblique gaze, implied narrative]
    lighting: [single hard on-camera flash, fill flash in daylight, harsh kicker shadow]
    cameraOrLens: [Canon 35mm SLR, 35mm lens]
    filmStockOrPostProcessing: [Kodachrome 64, slight cyan in the shadows, deep blacks]
    mood: [imperious, voyeuristic, controlled]
    avoidKeywords: [soft, dreamy, pastel, candid, smiling, cluttered background]
  namedReferences:
    photographers: [Helmut Newton, Guy Bourdin, Newton-school disciples]
    magazines: [French Vogue 1970s-90s, Stern, Playboy editorial]
    movements: [Big Nudes, Sumo]
    brands: [Wolford, Yves Saint Laurent, Versace 1990s, Chanel 1980s]
  examplePromptTemplate: |
    A tall woman in a black tailored Yves Saint Laurent tuxedo and stiletto heels, mid-stride across a marble Monte Carlo hotel lobby at noon, half-turned toward the camera with an imperious oblique gaze. Single hard on-camera flash with daylight fill, sharp kicker shadow falling onto a column behind her, background fall-off into deep cyan-black. Shot on a Canon 35mm SLR with a 35mm lens, Kodachrome 64, slight cyan shadows, deep blacks. Imperious, controlled, voyeuristic mood. Helmut Newton 1980s editorial style.
  whenToUse: Premium fashion editorial, watch and jewelry campaigns, luxury hospitality, anything where the brief calls for power, control, sex, or coolness. The default for restrained-luxury fashion stories.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-warm-restraint, style-oversized-neo-grotesque, aesthetic-swiss-modernist]
  notForUseWhen: Brief is sincere, sentimental, family-friendly, or wholesome.

---

- styleId: chrome-hearts-editorial
  name: Chrome Hearts night-glam editorial
  era: 2000s revival, current
  category: editorial-fashion
  visualSignatures:
    - Heavy on-camera flash on goth-luxe subjects, leather and chrome jewelry catching highlights
    - Shot in private rooms, cars, hotel bathrooms, after-hours
    - Crushed blacks, warm shadow tones, slight motion blur
    - Subject often half-cropped, off-center, looking away
  promptKeywords:
    primary: [crystal-encrusted leather, silver hardware glinting, hotel bathroom mirror, after-hours, motion blur on the wrist, half-cropped]
    lighting: [hard on-camera flash, mixed warm tungsten ambient]
    cameraOrLens: [point-and-shoot digital, 35mm equivalent]
    filmStockOrPostProcessing: [slight color noise in shadows, warm highlight bloom, crushed black point]
    mood: [decadent, insomniac, casually wealthy]
    avoidKeywords: [clean studio, daylight, smiling, group shot, wide landscape]
  namedReferences:
    photographers: [Petra Collins (early), Hugo Comte, Jesse Jenkins, Chrome Hearts in-house campaigns]
    magazines: [Office Magazine, 032c, i-D 2010s revival]
    movements: [post-internet editorial, 2010s tumblr noir]
    brands: [Chrome Hearts, Vetements, Heaven by Marc Jacobs, Vaquera]
  examplePromptTemplate: |
    Close-up of a young person's wrist stacked with silver Chrome Hearts cuffs and a leather glove, hand resting on a hotel marble sink at 4 a.m., the chrome catching a hard direct flash. Slight motion blur as the wrist turns. Mixed warm tungsten ambient bleeding into the highlights. Crushed blacks, warm shadow tint, signature digital point-and-shoot color noise. Shot on an early 2000s compact digital, 35mm equivalent. Decadent, insomniac, after-hours mood. Off-center crop, the face out of frame.
  whenToUse: Streetwear drops, jewelry campaigns, fragrance for younger demos, club-luxe lookbooks, fashion editorial for brands that want to read as 2025-cool without being too referential.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-cyberpunk, recipe-editorial-magazine, aesthetic-web-brutalism]
  notForUseWhen: Family product, B2B, anything wholesome.

---

- styleId: tillmans-candid
  name: Wolfgang Tillmans degree-zero candid
  era: 1990s-current
  category: editorial-fashion
  visualSignatures:
    - One 50mm lens, no retouching, available light, point and shoot
    - Subject mid-action, slightly awkward, clearly not posed
    - Domestic interiors, kitchen counters, unmade beds, friend's apartment
    - Slight overexposure in highlights, faded warm tones
    - Wide tonal range; nothing crushed, nothing blown
  promptKeywords:
    primary: [friend on a kitchen counter, half-action, unposed, domestic interior, mid-laugh, slightly awkward, soft daylight]
    lighting: [available natural light, soft north window]
    cameraOrLens: [50mm prime, point-and-shoot 35mm]
    filmStockOrPostProcessing: [color negative film, no retouching, slightly faded warm tones, gentle highlight roll-off]
    mood: [intimate, equal, non-hierarchical, observational]
    avoidKeywords: [studio, retouched, posed, professional model, dramatic lighting, glamour]
  namedReferences:
    photographers: [Wolfgang Tillmans, Juergen Teller (when soft), Mark Borthwick]
    magazines: [i-D, Interview, Purple, The Face, Dazed]
    movements: [degree-zero photography, snapshot aesthetic, anti-glamour]
    brands: [APC, Margiela, Eckhaus Latta, Our Legacy, COS journal]
  examplePromptTemplate: |
    A friend in their late twenties sitting on a kitchen counter in a cotton tank top and worn jeans, mid-laugh, holding a coffee mug, head tilted away from the camera. North-facing window light from camera-left, slightly overexposed highlights on the cheekbone, no retouching, no makeup retouching. Shot on a 50mm prime, color negative film, gentle warm fade, soft grain. Intimate, equal, non-hierarchical mood. Wolfgang Tillmans candid editorial style. Slightly off-kilter composition, subject not centered.
  whenToUse: Indie fashion, magazine-style lifestyle, anything that needs to read as cool-because-it-doesn't-try. Strong for editorial websites that want to avoid the polished e-commerce look.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, aesthetic-cottagecore, recipe-restrained-ai-marketing]
  notForUseWhen: Luxury, glamour, conversion-focused product pages, B2B.

---

- styleId: sorrenti-grain
  name: Mario Sorrenti grain and tonality
  era: 1990s-current
  category: editorial-fashion
  visualSignatures:
    - Medium format Pentax 67 or Hasselblad, 80mm normal lens
    - Deep tritone black-and-white with every grain preserved
    - Subject very close, freckles and pores visible, often half-clothed
    - Natural light only, often beach or hotel room
    - Intimacy of romantic relationship between photographer and subject
  promptKeywords:
    primary: [tight close-up, freckles, sea-salted hair, half-closed eyes, natural light, intimate, single subject]
    lighting: [available daylight, soft window, no fill, gentle falloff]
    cameraOrLens: [Pentax 67 medium format, 80mm lens]
    filmStockOrPostProcessing: [black and white film, fine medium-format grain, deep tritone print, preserved highlight texture]
    mood: [intimate, dreamy, romantic, unguarded]
    avoidKeywords: [hard flash, studio, posed, retouched, glossy]
  namedReferences:
    photographers: [Mario Sorrenti, Paolo Roversi (atmospheric), Bruce Weber (when intimate)]
    magazines: [Calvin Klein Obsession campaign, French Vogue, W Magazine]
    movements: [heroin chic origin, intimate fashion photography]
    brands: [Calvin Klein, Jil Sander, The Row, Lemaire]
  examplePromptTemplate: |
    Tight black-and-white close-up of a young woman's face, freckles and sea-salted hair across the cheek, eyes half-closed, no makeup. Lit by soft late-afternoon window light from camera-right with no fill. Shot on a Pentax 67 with an 80mm lens, deep tritone print preserving every grain of the negative, gentle highlight roll-off. Intimate, dreamy, unguarded mood. Mario Sorrenti early-1990s Calvin Klein campaign feel. Subject slightly off-center, soft focus on the lashes.
  whenToUse: Fragrance campaigns, monochrome editorial, intimate portraiture, anywhere the brief reads as "tender" or "first love" or "skin."
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, style-cream-humanist, style-serif-warm-paper, aesthetic-coastal-grandmother]
  notForUseWhen: Anything needing color, product detail, or commercial-explicit subject.

---

- styleId: genz-flash-disposable
  name: Gen-Z disposable-camera flash editorial
  era: current
  category: editorial-fashion
  visualSignatures:
    - Hard on-camera flash, often at a party or backstage, slight red-eye risk
    - Subject mid-action, drink in hand, hair half-blown, slight motion blur
    - Plastic-lens vignette, soft focus at edges, sharp center
    - Color shift toward cool magenta, slight grain
    - Reflective Y2K styling: gloss, latex, chrome, mesh
  promptKeywords:
    primary: [backstage at a fashion show, late-night party, drink in hand, mid-action, mesh top, lipgloss sheen, slight red-eye]
    lighting: [hard on-camera flash, fall-off into dark club ambient]
    cameraOrLens: [Fujifilm QuickSnap disposable, plastic lens, 32mm equivalent]
    filmStockOrPostProcessing: [Fujifilm Superia 400, soft vignette, magenta color shift, light grain, blown highlights]
    mood: [careless, kinetic, in-the-moment]
    avoidKeywords: [studio, retouched, professional lighting, soft glamour, formal pose]
  namedReferences:
    photographers: [Sandy Kim, Petra Collins, Cobrasnake archive, Mark Hunter]
    magazines: [Office, Polyester, Mission, i-D web]
    movements: [Cobrasnake party photography, 2020s tumblr revival, Y2K resurgence]
    brands: [Heaven by Marc Jacobs, Diesel SS22, Blumarine, KNWLS]
  examplePromptTemplate: |
    Backstage at a fashion show, a young model in a chrome-finish mesh top mid-laugh with a plastic cup raised, head half-turned, hair caught in motion. Hard direct on-camera flash, mild red-eye, deep dark ambient fall-off, slight reflective sheen on the lipgloss and on the chrome rings of the top. Shot on a Fujifilm QuickSnap disposable on Superia 400, soft plastic-lens vignette, magenta color shift in the shadows, blown highlight on the forehead. Careless, kinetic mood, off-center crop. 2025 backstage editorial.
  whenToUse: Gen-Z fashion, fragrance for younger demos, music streaming, club-night posters, lookbooks for streetwear, anything that needs to read as 2024-25 cool.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-y2k-memphis-loud, aesthetic-acid-graphics, aesthetic-rgb-gamer]
  notForUseWhen: Luxury, B2B, anything sincere, anything elderly-targeted.

---

- styleId: leibovitz-key-light
  name: Annie Leibovitz one-light portraiture
  era: 1980s-current
  category: editorial-fashion
  visualSignatures:
    - Single large softbox or umbrella, ambient kept in
    - Subject in their world, with their objects, doing their thing
    - Painterly chiaroscuro, deep shadows but not crushed
    - Conceptual: subject costumed as themselves or a character
    - Wide-ish frame showing context, not close-up
  promptKeywords:
    primary: [subject in their own studio, surrounded by personal objects, costumed, theatrical, wide frame]
    lighting: [single soft key from above and to the side, ambient retained, gentle falloff]
    cameraOrLens: [Hasselblad medium format, 80mm or 50mm equivalent]
    filmStockOrPostProcessing: [rich color, retained ambient warmth, painterly tonality]
    mood: [theatrical, thoughtful, deliberate]
    avoidKeywords: [snapshot, candid, available light only, harsh flash, club]
  namedReferences:
    photographers: [Annie Leibovitz, Steve McCurry (when staged), Platon (when wider)]
    magazines: [Vanity Fair covers, Rolling Stone covers, Vogue celebrity]
    movements: [staged celebrity portraiture, one-light Profoto Acute style]
    brands: [American Express "What's in your wallet", Disney Dream Portraits, Louis Vuitton Core Values]
  examplePromptTemplate: |
    A mid-career architect in her studio, standing among rolled drawings and a half-built balsa model, wearing a navy linen apron over a white shirt, looking past camera-left in thought. Single 60" softlighter softbox above and camera-right, ambient daylight from a window retained at half power, gentle falloff into the studio interior. Shot on a Hasselblad H6D with an 80mm lens, rich color, painterly chiaroscuro tonality, retained warm ambient. Theatrical, deliberate, thoughtful mood. Annie Leibovitz Vanity Fair portrait style. Wide-ish three-quarter frame.
  whenToUse: Founder portraits, About Us photography, magazine-style profile shots, conference speaker headshots that need to feel cinematic. The default for "tell their story" briefs.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-devtools-marketing, recipe-bento-marketing, style-serif-warm-paper]
  notForUseWhen: Quick product, e-comm hero, anything needing many subjects in one shot.

---

- styleId: gilden-flash-street
  name: Bruce Gilden flash street portrait
  era: 1980s-current
  category: street
  visualSignatures:
    - 28mm wide lens, flash off-camera held in left hand, very close to subject's face
    - Subject caught mid-expression, often startled or annoyed
    - Crushed blacks, hot highlights on skin texture, every pore visible
    - NYC sidewalk, Coney Island, Tokyo, Mumbai
    - The "ugly side" of an outfit or expression, not flattering
  promptKeywords:
    primary: [NYC sidewalk, mid-stride pedestrian, very close to face, startled expression, every pore visible, ugly-beautiful]
    lighting: [hard off-camera flash held at arm's length, no fill, crushed background]
    cameraOrLens: [Leica M6, 28mm lens]
    filmStockOrPostProcessing: [Kodak Tri-X 400 or saturated color, hot highlight on skin, crushed black background, slight grain]
    mood: [aggressive, intrusive, raw, unflattering-true]
    avoidKeywords: [flattering, glamorous, posed, smiling, soft, distant]
  namedReferences:
    photographers: [Bruce Gilden, Mark Cohen, William Klein]
    magazines: [Magnum Photos archive, Aperture]
    movements: [aggressive street photography, photojournalism with flash]
    brands: [Diesel campaigns 1990s, Supreme lookbooks 2010s]
  examplePromptTemplate: |
    Extreme close-up of a middle-aged man in a fur coat mid-stride on Fifth Avenue at noon, caught startled by a hard flash held at arm's length, every wrinkle and skin pore in sharp detail, crushed black background, hot highlight bouncing off the forehead and the fur. Shot on a Leica M6 with a 28mm lens, Kodak Tri-X 400, harsh contrast, slight grain, slight motion blur on the hand. Aggressive, intrusive, raw mood. Bruce Gilden NYC street style. The composition off-center, the subject's face filling 80% of the frame.
  whenToUse: Editorial photography for music, streetwear, journalism-flavored marketing, anything that wants to read as confrontational and real.
  pairsWith:
    prototypeStyles: [recipe-brutalist-web, aesthetic-neubrutalism, aesthetic-web-brutalism, recipe-newspaper-of-record]
  notForUseWhen: Anything aspirational, hospitality, luxury, wellness.

---

- styleId: vivian-maier-square
  name: Vivian Maier square street observational
  era: 1950s-1970s archival
  category: street
  visualSignatures:
    - Square 6x6 medium format, waist-level finder
    - Subject unaware, observed at distance or in shop-window reflection
    - High-detail Rolleiflex sharpness across the frame
    - Strong everyday composition: child mid-game, woman in furs, worker on break
    - Soft mid-century black-and-white grayscale
  promptKeywords:
    primary: [chicago sidewalk 1959, child mid-game, woman in furs, shop-window reflection of the photographer, candid observation, square format]
    lighting: [overcast daylight or soft sun, even and forgiving]
    cameraOrLens: [Rolleiflex twin-lens reflex, 80mm waist-level]
    filmStockOrPostProcessing: [black and white medium format, full tonal range, high detail, fine grain]
    mood: [quiet, observed, dignified]
    avoidKeywords: [posed, flash, color, low-angle dramatic]
  namedReferences:
    photographers: [Vivian Maier, Saul Leiter (when monochrome), Helen Levitt]
    magazines: [retrospective monographs, museum]
    movements: [mid-century American street photography, twin-lens-reflex era]
    brands: [archival editorial, Aperture monographs]
  examplePromptTemplate: |
    Square black-and-white photograph of a woman in a wool coat and pillbox hat waiting at a bus stop on a Chicago sidewalk, 1959, observed from across the street unaware. Overcast daylight, full tonal range from rich black to soft highlight, fine medium-format grain, edge-to-edge sharpness. Shot on a Rolleiflex twin-lens reflex with an 80mm lens at waist height. Quiet, dignified, observational mood. Vivian Maier archival street style. Composition organized by the line of the storefront and the curb.
  whenToUse: Archival brands, heritage marketing, editorial pieces that reference mid-century Americana, museum projects, banking brand campaigns that want gravitas.
  pairsWith:
    prototypeStyles: [recipe-newspaper-of-record, style-serif-warm-paper, style-agate-broadsheet, recipe-editorial-magazine]
  notForUseWhen: Anything contemporary-fashion, fast-paced, conversion-driven.

---

- styleId: cinematic-street-anamorphic
  name: Cinematic anamorphic street
  era: current
  category: street
  visualSignatures:
    - Anamorphic 2.39:1 wide aspect, oval bokeh, blue horizontal lens flares
    - Subject silhouetted against neon or fog
    - Teal-and-orange color grade
    - Wide deep shadows, painterly highlights
    - Strong directional light: streetlamp, signage, vehicle headlight
  promptKeywords:
    primary: [silhouetted lone figure, wet asphalt, neon signage in the distance, volumetric fog, walking away from camera, 2.39:1]
    lighting: [single neon practical, volumetric light beams, deep ambient fall-off]
    cameraOrLens: [Arri Alexa, anamorphic 50mm, oval bokeh, horizontal blue flares]
    filmStockOrPostProcessing: [teal-and-orange grade, gentle film grain overlay, slight halation]
    mood: [contemplative, melancholy, observed]
    avoidKeywords: [bright, daylight, smiling, posed portrait, flat lighting]
  namedReferences:
    photographers: [Roger Deakins (when street), Rinko Kawauchi when atmospheric, contemporary cinematographers]
    magazines: [American Cinematographer, Sight & Sound]
    movements: [Blade Runner 2049 visual school, A24 cinematography]
    brands: [Squarespace film-look campaigns, Apple "Shot on iPhone" cinematic, Audi night campaigns]
  examplePromptTemplate: |
    A lone figure in a long overcoat walking away from camera down a wet, fog-filled alleyway at night, silhouetted against a distant pink neon sign. Single practical light source, volumetric beams cutting through the mist, deep ambient fall-off in the foreground. Shot on an Arri Alexa with a 50mm anamorphic lens, 2.39:1 aspect ratio, oval bokeh on the distant sign, horizontal blue flare across the frame, teal shadows and warm orange highlight grade, gentle filmic grain. Contemplative, melancholy, observed mood.
  whenToUse: Hero video stills, premium tech ads, fragrance, automotive, anything that needs to read as "film" not "photo."
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, recipe-ai-foundry-dark, style-dense-mono-dark]
  notForUseWhen: Anything bright, daylight-driven, product e-comm.

---

- styleId: night-flash-noir
  name: Night flash neon-noir portrait
  era: current
  category: street
  visualSignatures:
    - Hard direct on-camera flash on subject at night
    - Background drops into neon-tinted darkness with small bokeh from signage
    - High contrast, saturated reds and cyans
    - Subject usually a single person, posture confident
    - Crushed blacks, lit subject sharp and slightly cool
  promptKeywords:
    primary: [subject leather jacket, city corner at night, neon sign behind, confident stance, half-body]
    lighting: [hard direct on-camera flash, neon ambient bokeh background, no fill]
    cameraOrLens: [Canon EOS R6, 28mm or 35mm lens]
    filmStockOrPostProcessing: [CineStill 800T halation, saturated cyan-magenta, sharp focus on eyes, crushed black]
    mood: [confident, nocturnal, magnetic]
    avoidKeywords: [smiling group, daylight, soft lighting, pastel]
  namedReferences:
    photographers: [Liam Wong, Tokyo neon-noir cohort, Bonjour Tokyo school]
    magazines: [Hypebeast, Highsnobiety, indie tokyo photo zines]
    movements: [neon-noir, vaporwave-adjacent street]
    brands: [Acne Studios night campaigns, Off-White, JJJJound]
  examplePromptTemplate: |
    Half-body portrait of a person in a black leather biker jacket on a Shibuya street corner at 1 a.m., looking just past camera-left with a confident half-smile, hand in pocket. Hard direct on-camera flash punching the subject forward, cyan and magenta neon signs in the background out of focus as small bokeh circles, no fill light. Shot on a Canon EOS R6 with a 28mm lens at f/2.8, CineStill 800T halation around the highlights, crushed black background, sharp focus on the eyes. Confident, nocturnal, magnetic mood. Tokyo neon-noir street portrait.
  whenToUse: Streetwear campaigns, music streaming app art, neon-themed editorial, club marketing, anything that wants to read as 2 a.m.
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-y2k-futurism, recipe-ai-foundry-dark]
  notForUseWhen: Daylight product, family, wellness.

---

- styleId: apple-clean-studio
  name: Apple-clean studio product
  era: current
  category: product
  visualSignatures:
    - Pure white or pure black seamless backdrop, no horizon line
    - Even soft light wrapping the product, two large softboxes
    - Hero product floating or on invisible base
    - Sharp specular highlights on aluminum and glass edges
    - Hyperreal detail, microtexture preserved
  promptKeywords:
    primary: [seamless white backdrop, single product hero, floating, sharp edge highlight, microtexture]
    lighting: [two large softboxes left and right, soft gradient fill, controlled specular highlight]
    cameraOrLens: [Phase One IQ4, 80mm macro, f/11 for product sharpness]
    filmStockOrPostProcessing: [color-managed digital, no grain, controlled gradient, retouched dust-clean]
    mood: [precise, premium, certain]
    avoidKeywords: [grain, vignette, prop clutter, lifestyle context, hand holding]
  namedReferences:
    photographers: [Apple in-house studio team, Peter Belanger, Joey L for product]
    magazines: [Apple keynote stills, MKBHD product reviews]
    movements: [post-Steve Jobs Apple visual canon]
    brands: [Apple, Sonos, Dyson, Bose, Nothing]
  examplePromptTemplate: |
    A single titanium consumer product floating just above a pure white seamless backdrop, sharp edge highlights along the aluminum chamfer, soft gradient fill across the matte top surface. Two large 4x6 softboxes left and right at 45 degrees, controlled specular highlight, no shadow on the backdrop. Shot on a Phase One IQ4 with an 80mm macro at f/11, color-managed, dust-clean, no grain. Precise, premium, certain mood. Apple keynote product photography style.
  whenToUse: Hardware product, consumer electronics hero, e-commerce premium product page, app store icons-from-photo.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, recipe-ios-system, style-sf-pro-ios, style-glassmorphism, style-liquid-glass]
  notForUseWhen: Lifestyle storytelling, editorial, anything needing context or mood.

---

- styleId: aesop-apothecary
  name: Aesop apothecary minimal still life
  era: current
  category: product
  visualSignatures:
    - Stone, concrete, raw plaster, or linen substrate
    - Amber glass bottles, single-source soft daylight
    - Architectural shadow falling diagonally
    - Restrained dried botanical or industrial prop
    - Muted earth palette, no saturation push
  promptKeywords:
    primary: [amber glass bottle, raw concrete shelf, single dried branch, diagonal shadow, restrained still life]
    lighting: [single soft window light from upper-left, long architectural shadow]
    cameraOrLens: [Hasselblad H6D, 100mm macro, f/5.6]
    filmStockOrPostProcessing: [muted earth palette, no saturation, gentle film grain overlay]
    mood: [calm, considered, apothecary]
    avoidKeywords: [bright, saturated, plastic, glossy, busy backdrop]
  namedReferences:
    photographers: [Pelle Crepin for Aesop, Scott Trindle product, Daniel Riera]
    magazines: [The Gentlewoman, Cereal, Apartamento]
    movements: [post-Aesop apothecary still life, architectural product]
    brands: [Aesop, Le Labo, Byredo, Diptyque, Frama]
  examplePromptTemplate: |
    A single Aesop amber glass apothecary bottle on a raw concrete shelf with a sprig of dried lavender resting beside it, a diagonal hard-edged shadow from a window upper-left crossing the shelf. Single soft daylight, no fill. Shot on a Hasselblad H6D with a 100mm macro at f/5.6, muted earth palette, no saturation push, gentle film grain. Calm, considered, apothecary mood. Aesop-style product still life. Composition strict three-quarter angle, generous negative space camera-right.
  whenToUse: Skincare, fragrance, premium personal care, slow-luxury packaging, hospitality amenity kits.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, style-cream-humanist, style-serif-warm-paper, style-restrained-hairline]
  notForUseWhen: Mass-market product, anything loud, family CPG.

---

- styleId: bon-appetit-food
  name: Bon Appétit moody food overhead
  era: current
  category: food
  visualSignatures:
    - Dark wood, slate, or aged copper substrate
    - Top-down 90-degree or 45-degree overhead angle
    - Single soft window light from the side, long shadows
    - Imperfect plating: crumbs, oil drip, half-eaten edge
    - Saturated jewel-tone food on muted dark backdrop
  promptKeywords:
    primary: [dark walnut table, overhead 90-degree angle, half-eaten edge, crumbs and oil drip, vintage cutlery]
    lighting: [single soft window light from camera-left, long natural shadow across the table, no fill]
    cameraOrLens: [Canon R5, 50mm or 100mm macro, f/4]
    filmStockOrPostProcessing: [moody warm tone, deepened shadows, retained food color saturation]
    mood: [appetizing, narrative, lived-in]
    avoidKeywords: [bright white backdrop, perfect plating, harsh flash, plastic-looking food]
  namedReferences:
    photographers: [Alex Lau, Peden + Munk, Marcus Nilsson]
    magazines: [Bon Appétit, Cherry Bombe, Saveur, Food52]
    movements: [moody food photography, 2010s overhead canon]
    brands: [Bon Appétit, Food52, Brooklyn Brewery, Le Creuset]
  examplePromptTemplate: |
    Overhead 90-degree photograph of a half-eaten pasta dish on a vintage ceramic plate, crumbs and a drip of olive oil on a dark walnut table, a bone-handled fork resting on the edge of the plate, a linen napkin crumpled top-right. Single soft window light from camera-left, long natural shadow stretching camera-right, no fill. Shot on a Canon R5 with a 50mm at f/4, moody warm tone, deep shadow, jewel-tone food saturation retained. Appetizing, lived-in mood. Bon Appétit editorial food style.
  whenToUse: Restaurant marketing, recipe content, premium grocery, food magazine editorial.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, style-serif-warm-paper, recipe-warm-restraint, aesthetic-cottagecore]
  notForUseWhen: Fast casual, fast food, packaging hero shot, kid food.

---

- styleId: nyt-cooking-food
  name: NYT Cooking bright daylight food
  era: current
  category: food
  visualSignatures:
    - Bright daylight, light wood, marble, or pale linen surface
    - Slight overhead or 3/4 angle
    - Process shot: hands in the frame, half-prepped ingredient
    - Clean color palette, slightly cool, no heavy shadow
    - Natural plating, real-home not styled
  promptKeywords:
    primary: [pale ash wood counter, hands prepping ingredient, 3/4 angle, fresh herbs, real-home plating]
    lighting: [diffused bright daylight, light overcast, even and forgiving, no hard shadow]
    cameraOrLens: [Sony A7IV, 35mm or 50mm, f/4]
    filmStockOrPostProcessing: [slightly cool color grade, natural saturation, no vignette]
    mood: [bright, capable, friendly]
    avoidKeywords: [moody dark, dramatic shadow, professional restaurant plating, food styling perfection]
  namedReferences:
    photographers: [Andrew Scrivani, Linda Xiao, Christopher Testani]
    magazines: [NYT Cooking, Bon Appétit Healthyish, Smitten Kitchen]
    movements: [bright daylight food, home-cook editorial]
    brands: [NYT Cooking, Smitten Kitchen, King Arthur Baking]
  examplePromptTemplate: |
    Three-quarter angle photograph of a wooden cutting board on a pale ash counter, hands in frame slicing scallions diagonally, a small bowl of toasted sesame seeds and a half-empty bottle of soy sauce in soft focus background. Bright diffused daylight from a large window camera-right, even forgiving exposure, no hard shadow. Shot on a Sony A7IV with a 50mm at f/4, slightly cool natural color, no vignette. Bright, capable, friendly mood. NYT Cooking editorial home-cook style.
  whenToUse: Recipe content for daylight-positive brands, home-cooking app marketing, wellness food, kitchen tools, grocery.
  pairsWith:
    prototypeStyles: [recipe-readcv, style-cream-humanist, aesthetic-coastal-grandmother, recipe-restrained-ai-marketing]
  notForUseWhen: Fine dining, moody restaurant marketing, fast food.

---

- styleId: magnum-monochrome
  name: Magnum monochrome documentary
  era: 1950s-current
  category: documentary
  visualSignatures:
    - 35mm Leica with 35mm or 50mm lens, decisive moment
    - Full tonal range black-and-white, fine grain
    - Subject mid-action, environment carrying narrative
    - Composition organized around geometry of place
    - Truthful framing, never staged
  promptKeywords:
    primary: [marketplace, mid-action vendor, geometric composition, environmental context, decisive moment]
    lighting: [available daylight, soft direction, natural shadow]
    cameraOrLens: [Leica M6, 35mm lens]
    filmStockOrPostProcessing: [Kodak Tri-X 400, full tonal range, fine grain, archival black-and-white]
    mood: [observed, dignified, witness]
    avoidKeywords: [posed, smiling-at-camera, flash, dramatic color, glossy]
  namedReferences:
    photographers: [Henri Cartier-Bresson, Josef Koudelka, Alex Webb, Susan Meiselas]
    magazines: [Magnum archive, LIFE magazine archive, Aperture]
    movements: [Magnum Photos, decisive-moment school]
    brands: [Leica brand campaigns, NGO and editorial use]
  examplePromptTemplate: |
    Black-and-white photograph of a vegetable vendor mid-gesture handing change to an unseen customer in a covered Mumbai marketplace, environmental context of stacked produce and patterned awning, composition organized around the diagonal of the awning rope. Available daylight from above, soft natural shadow. Shot on a Leica M6 with a 35mm lens, Kodak Tri-X 400, full tonal range, fine grain. Observed, dignified, witness mood. Magnum decisive-moment style. Subject not aware of the camera.
  whenToUse: Editorial journalism, NGO marketing, humanitarian campaigns, museum, archival heritage brands.
  pairsWith:
    prototypeStyles: [recipe-newspaper-of-record, style-agate-broadsheet, style-serif-warm-paper, recipe-editorial-magazine]
  notForUseWhen: Product e-comm, anything aspirational-consumer.

---

- styleId: war-photojournalism
  name: Frontline war photojournalism
  era: 1990s-current
  category: documentary
  visualSignatures:
    - 35mm or 28mm wide lens, very close to action
    - Available light only, often harsh midday or smoke-filtered
    - Saturated color (Kodachrome era) or stark mono
    - Subject mid-trauma or mid-relief, unstaged
    - Composition imperfect, occasional motion blur, tilted horizon
  promptKeywords:
    primary: [mid-action civilians, dust and smoke, available light, imperfect composition, witness-distance]
    lighting: [available daylight, smoke-filtered diffusion, harsh fall-off]
    cameraOrLens: [Canon 5D with 28mm or 35mm prime]
    filmStockOrPostProcessing: [saturated journalism color, slight grain, gritty texture, slight motion blur]
    mood: [grave, witness, present]
    avoidKeywords: [staged, glossy, posed, retouched, beautiful]
  namedReferences:
    photographers: [James Nachtwey, Lynsey Addario, Don McCullin, Tyler Hicks]
    magazines: [TIME, National Geographic, New York Times Magazine]
    movements: [photojournalism canon]
    brands: [news editorial only — not used for consumer brand]
  examplePromptTemplate: |
    A civilian woman shielding a child crossing a dusty street, captured mid-stride in the harsh midday smoke-filtered light of a conflict zone, available light only, slight tilt to the horizon, imperfect composition with the edge of a broken vehicle clipping the right frame. Shot on a Canon 5D with a 28mm prime, saturated journalism color, slight grain, mild motion blur on the child's foot. Grave, witness mood. War photojournalism, James Nachtwey lineage.
  whenToUse: Editorial only — news, documentary film stills, NGO campaign. NEVER for consumer brand work.
  pairsWith:
    prototypeStyles: [recipe-newspaper-of-record, style-agate-broadsheet]
  notForUseWhen: Any commercial application. Reserved for editorial truth.

---

- styleId: salgado-contrast
  name: Sebastião Salgado biblical contrast
  era: 1980s-current
  category: documentary
  visualSignatures:
    - High-contrast monochrome, deep black point, retained shadow detail
    - Workers, refugees, environment-scale subjects
    - Compositional grandeur — biblical, almost painterly
    - Pentax 645 medium format prints, large-scale
    - Texture of skin, dust, sweat preserved
  promptKeywords:
    primary: [workers in motion, environment scale, biblical composition, dust and sweat, dignity through labor]
    lighting: [hard overhead sun, atmospheric haze, light cutting through dust]
    cameraOrLens: [Pentax 645 medium format, 75mm lens]
    filmStockOrPostProcessing: [high-contrast black and white, deep blacks with retained shadow detail, large-print tonality, fine medium-format grain]
    mood: [grave, dignified, monumental]
    avoidKeywords: [color, snapshot, low-contrast, flash, retouched]
  namedReferences:
    photographers: [Sebastião Salgado]
    magazines: [Workers, Migrations, Genesis monographs]
    movements: [social documentary monumental]
    brands: [editorial, museum, NGO — Patagonia campaign reference]
  examplePromptTemplate: |
    Black-and-white photograph of gold miners climbing a steep mud-walled pit in Serra Pelada, dozens of figures stacked diagonally, atmospheric dust haze cutting through hard overhead sun, biblical compositional grandeur. Shot on a Pentax 645 medium format with a 75mm lens, high-contrast print, deep black point but retained shadow detail in the figures, fine medium-format grain. Grave, dignified, monumental mood. Sebastião Salgado documentary style.
  whenToUse: Heritage industry brands, environmental campaign, sustainability marketing, museum content.
  pairsWith:
    prototypeStyles: [recipe-newspaper-of-record, style-agate-broadsheet, recipe-editorial-magazine, style-serif-warm-paper]
  notForUseWhen: Fashion, consumer product, anything cheerful.

---

- styleId: environmental-portrait
  name: Environmental documentary portrait
  era: 1970s-current
  category: documentary
  visualSignatures:
    - Subject in their own context (workshop, kitchen, fishing boat)
    - Wide-ish 35mm framing showing workplace
    - Natural light only, supplemented by single bounce or reflector
    - Subject acknowledges camera, calm and direct
    - Tools, environment, clothing all telling the story
  promptKeywords:
    primary: [subject in workshop with tools, half-body, calm direct gaze, environmental context, natural posture]
    lighting: [single window or open door light, soft natural fill from reflector]
    cameraOrLens: [Fuji X100V, 35mm equivalent, f/4]
    filmStockOrPostProcessing: [natural color, gentle highlight roll-off, slight grain, retained ambient warmth]
    mood: [grounded, dignified, present]
    avoidKeywords: [studio, posed glamour, smiling at camera, isolated white backdrop]
  namedReferences:
    photographers: [Arnold Newman, August Sander lineage, Platon (when wider), Christopher Anderson]
    magazines: [Monocle, The New Yorker portraiture]
    movements: [environmental portraiture canon]
    brands: [Patagonia worn-wear, Toast journal, Hermès artisan stories]
  examplePromptTemplate: |
    A potter in his late fifties standing at his wheel in a brick workshop, clay-streaked apron, half-body wide framing showing shelves of unfired ware behind him, hands resting on the wheel, calm direct gaze just past the camera. Single open-door daylight from camera-left, soft white reflector fill from camera-right. Shot on a Fuji X100V at 35mm equivalent at f/4, natural color, gentle highlight roll-off, slight grain, retained warmth in the brick wall. Grounded, dignified, present mood. Environmental documentary portrait.
  whenToUse: Founder portraits, artisan brand storytelling, About Us sections, "Behind the craft" series.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-warm-restraint, style-serif-warm-paper, style-cream-humanist]
  notForUseWhen: Fast e-comm, product hero, anything that should be impersonal.

---

- styleId: y2k-halftone
  name: Y2K halftone newsprint effect
  era: 2000s revival
  category: archival
  visualSignatures:
    - Photo passed through visible CMYK halftone dot pattern
    - Slight registration misalignment between channels
    - Newsprint paper warmth, slight yellowing
    - Saturated electric pink and cyan
    - Hard-edged graphics overlay, often with magazine layout artifacts
  promptKeywords:
    primary: [halftone dot pattern overlay, CMYK channel misregistration, newsprint paper warmth, electric pink and cyan]
    lighting: [original subject lighting any, post-processed as printed halftone]
    cameraOrLens: [any digital source, transformed in post]
    filmStockOrPostProcessing: [coarse halftone screen, slight ink registration shift, paper texture, slight yellow paper tone]
    mood: [zine, raw, kinetic]
    avoidKeywords: [smooth gradient, photoreal skin, perfect print, clean]
  namedReferences:
    photographers: [n/a — post-processing style]
    magazines: [The Face 1990s, Ray Gun, Sleazenation, Vice 2000s]
    movements: [David Carson typography era, zine culture, post-internet]
    brands: [Vetements, Heaven by Marc Jacobs, Eckhaus Latta]
  examplePromptTemplate: |
    Editorial half-body portrait of a young person in a chrome top, posed three-quarter, rendered as a coarse CMYK halftone print with visible large dot pattern, slight cyan-magenta channel misregistration, warm newsprint paper texture, electric pink and cyan dominant. The dot pattern roughly 60 LPI, the paper tone slightly yellow-warm. Zine, raw, kinetic mood. Y2K newsprint halftone treatment over a fashion editorial frame.
  whenToUse: Music posters, zine, streetwear lookbook, Gen-Z marketing, hero images for editorial websites that want to reference print culture.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-memphis-loud, aesthetic-y2k-futurism, aesthetic-acid-graphics, recipe-y2k-memphis-loud]
  notForUseWhen: Luxury, premium, anything aspirational-clean.

---

- styleId: y2k-flash-glam
  name: Y2K glossy flash glamour
  era: 2000s
  category: editorial-fashion
  visualSignatures:
    - Direct flash, glossy reflective fabrics, lipgloss high-shine
    - Cool color palette: silver, chrome, pale pink, ice blue
    - Subject in motion or club setting
    - Slight digital sharpness, early-2000s sensor signature
    - Saturated red-eye risk preserved
  promptKeywords:
    primary: [silver mesh top, lipgloss sheen, club setting, mid-dance, ice-blue palette]
    lighting: [hard direct flash, ambient cool club lighting]
    cameraOrLens: [early 2000s compact digital, 35mm equivalent]
    filmStockOrPostProcessing: [signature early-digital sharpness, cool color cast, slight magenta shift, blown highlight on the gloss]
    mood: [reflective, kinetic, slick]
    avoidKeywords: [film grain, warm, natural light, soft]
  namedReferences:
    photographers: [David LaChapelle (when 2000s), Ellen von Unwerth flash, Mark Liddell editorial]
    magazines: [Vogue Paris 2001-2005, Numero, V Magazine]
    movements: [Y2K maximalism, McBling glamour]
    brands: [Versace 2000s, Roberto Cavalli 2000s, Bratz dolls aesthetic, Heaven]
  examplePromptTemplate: |
    Half-body shot of a woman in a chrome-finish silver mesh top with rhinestone choker, mid-laugh at a club, head tilted back, lipgloss catching a hard direct flash. Cool ambient club lighting in the background falls off into ice blue, slight motion blur on the hands. Shot on an early 2000s compact digital camera, 35mm equivalent, signature early-digital sharpness, slight magenta shift, blown highlight on the forehead and gloss. Reflective, kinetic, slick mood. Y2K McBling glamour editorial.
  whenToUse: Pop music streaming art, energy drink, club, beauty for younger demos, fashion lookbook with Y2K reference.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-frutiger-aero, aesthetic-y2k-memphis-loud, aesthetic-curly-girly]
  notForUseWhen: Heritage brand, B2B, wellness.

---

- styleId: frutiger-aero-product
  name: Frutiger Aero glossy product environment
  era: 2004-2013
  category: product
  visualSignatures:
    - Glossy 3D-rendered surfaces, water droplets, bubbles
    - Saturated sky-blue and grass-green palette
    - Bokeh from sunlight or glow spheres
    - Subject mid-frame with depth-of-field shallow
    - Bright cheerful, slight skeuomorphic gloss
  promptKeywords:
    primary: [glossy product on grass, sky background, water droplets, bubble bokeh, sky-blue and grass-green]
    lighting: [bright outdoor daylight, slight golden bokeh, glossy specular highlights]
    cameraOrLens: [Canon 5D, 100mm macro at f/2.8]
    filmStockOrPostProcessing: [oversaturated cheerful color, glossy specular, slight HDR, blown sky]
    mood: [optimistic, sky-fresh, 2007-internet]
    avoidKeywords: [moody, dark, gritty, monochrome, restrained]
  namedReferences:
    photographers: [Asadal stock library, 2000s consumer-electronics photographers]
    magazines: [Wired 2007-2010, Macworld, GQ Tech]
    movements: [Frutiger Aero, Apple iLife era]
    brands: [Windows XP, early Vista, Sony BRAVIA campaigns, iPhone 1G launch imagery]
  examplePromptTemplate: |
    A translucent glossy consumer headphone floating just above a vivid green grass surface with macro water droplets clinging to the rim, bright sky-blue background with golden bokeh spheres, two small soap bubbles drifting in the upper-right. Bright outdoor daylight, glossy specular highlights on the chrome detailing, slight HDR pop. Shot on a Canon 5D with a 100mm macro at f/2.8, oversaturated cheerful color, blown sky highlight. Optimistic, sky-fresh, 2007 mood. Frutiger Aero glossy product environment.
  whenToUse: Consumer-electronics retro campaigns, Y2K-aesthetic stock, sky-positive product marketing, nostalgia plays.
  pairsWith:
    prototypeStyles: [aesthetic-frutiger-aero, aesthetic-frutiger-chromecore, aesthetic-frutiger-tranquil-serenity, style-glassmorphism, style-liquid-glass]
  notForUseWhen: Luxury, restrained, premium B2B.

---

- styleId: vaporwave-still-life
  name: Vaporwave pastel still life
  era: 2010s revival of 1980s-90s
  category: conceptual
  visualSignatures:
    - Pastel pink and cyan dominant, soft pastel gradient backdrop
    - Plaster bust, glitchy CRT screen, palm leaf, marble pedestal
    - Soft even studio light, no hard shadow
    - VHS scanline overlay optional
    - Slight color separation chromatic aberration
  promptKeywords:
    primary: [plaster bust, palm leaf, marble pedestal, pastel gradient backdrop, CRT glow, vaporwave still life]
    lighting: [soft even studio light, single colored gel ambient]
    cameraOrLens: [Canon 5D, 50mm at f/8, color filter overlay]
    filmStockOrPostProcessing: [pastel pink-cyan grade, slight chromatic aberration, VHS scanline overlay, soft gradient]
    mood: [dreamy, ironic, nostalgic-future]
    avoidKeywords: [natural light, warm grade, photojournalism]
  namedReferences:
    photographers: [Vaporwave moodboards, Tumblr 2014-2017 community]
    magazines: [Dis Magazine, Toiletpaper Magazine]
    movements: [Vaporwave, Seapunk, post-internet art]
    brands: [Jaden Smith MSFTSrep, MTV revival, Vaporwave Spotify playlists]
  examplePromptTemplate: |
    Studio still life of a small plaster Roman bust on a chrome pedestal, a single palm leaf entering from upper-right, a CRT screen in the background showing static, pastel pink and cyan gradient backdrop. Soft even studio light with a pink gel ambient from camera-left. Shot on a Canon 5D with a 50mm at f/8, pastel pink-cyan grade, slight chromatic aberration, faint VHS scanlines overlay. Dreamy, ironic, nostalgic-future mood. Vaporwave still life conceptual photography.
  whenToUse: Music streaming art, ironic-nostalgic brand campaigns, indie game key art, club night posters.
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-y2k-futurism, aesthetic-cassette-futurism, aesthetic-dreamcore]
  notForUseWhen: Heritage, wellness, premium consumer.

---

- styleId: eighties-cocaine-glam
  name: 1980s cocaine-glam editorial
  era: 1980s
  category: glamour
  visualSignatures:
    - Hard rim light from behind, soft fill from front
    - Glossy fabric, sequins, leather, big hair
    - Saturated punchy color, slight blue-magenta cast
    - Studio backdrop with painted gradient
    - Glamour smile, eye contact, confident gaze
  promptKeywords:
    primary: [sequined gown, big teased hair, gradient studio backdrop, confident eye contact, half-body glamour]
    lighting: [hard rim light from behind, soft front fill from large softbox, shaped catch light]
    cameraOrLens: [Mamiya RB67 medium format, 90mm]
    filmStockOrPostProcessing: [Kodak Ektachrome saturated, slight blue-magenta cast, glossy specular]
    mood: [confident, brassy, Studio 54]
    avoidKeywords: [muted, natural light, candid, minimal]
  namedReferences:
    photographers: [Francesco Scavullo, Richard Avedon when commercial, Patrick Demarchelier 1980s]
    magazines: [Vogue 1985-89, Cosmopolitan 1980s, Interview]
    movements: [Studio 54 glamour, supermodel era origin]
    brands: [Versace 1980s, Yves Saint Laurent Opium era, Estée Lauder 1980s]
  examplePromptTemplate: |
    Half-body editorial of a woman in a black sequined gown with shoulder pads and a single large gold earring, big teased hair, head tilted with a confident half-smile, eye contact through camera. Hard rim light from behind catching every sequin, large softbox front fill creating shaped catchlights in the eyes, painted gradient blue-to-mauve studio backdrop. Shot on a Mamiya RB67 with a 90mm, Kodak Ektachrome saturated color, slight blue-magenta cast. Confident, brassy, Studio 54 mood. 1980s cocaine-glam editorial.
  whenToUse: Beauty for older or nostalgia demos, premium spirit and tobacco-adjacent marketing, hospitality nostalgia, retro music marketing.
  pairsWith:
    prototypeStyles: [aesthetic-urbling, aesthetic-y2k-memphis-loud, recipe-editorial-magazine, aesthetic-vector-hands-up]
  notForUseWhen: Restrained luxury, minimal, anything wellness.

---

- styleId: seventies-soft-grain
  name: 1970s soft warm grain editorial
  era: 1970s
  category: editorial-fashion
  visualSignatures:
    - Warm Kodachrome amber and earth tones
    - Slight soft focus, dreamy halation
    - Natural daylight, golden hour, indoor tungsten
    - Subject hair and clothing in motion, scarves, suede
    - Landscape or country setting
  promptKeywords:
    primary: [suede jacket, long hair in motion, country meadow, golden afternoon, dreamy, soft focus]
    lighting: [golden hour low sun, soft natural fill, dreamy halation]
    cameraOrLens: [Pentax K1000, 50mm f/1.4]
    filmStockOrPostProcessing: [Kodachrome 64, amber and earth tones, soft halation, warm grain]
    mood: [dreamy, romantic, free]
    avoidKeywords: [studio, hard flash, cool, modern, sharp]
  namedReferences:
    photographers: [Sarah Moon, Deborah Turbeville, David Hamilton, early Bruce Weber]
    magazines: [Vogue 1972-78, Harper's Bazaar 1970s]
    movements: [1970s soft fashion, dreamy-romantic editorial]
    brands: [Chloé 1970s, Ralph Lauren original, Yves Saint Laurent Rive Gauche]
  examplePromptTemplate: |
    Editorial of a young woman in a suede jacket and silk scarf walking through a sunlit meadow at golden hour, long hair caught in motion, mid-laugh looking back over her shoulder. Low golden sun from camera-right, soft natural fill, dreamy halation around the rim of her hair. Shot on a Pentax K1000 with a 50mm f/1.4, Kodachrome 64, amber and warm earth tones, soft warm grain. Dreamy, romantic, free mood. 1970s soft-grain editorial.
  whenToUse: Heritage fashion, nostalgia campaigns, wellness for older demographics, hospitality summer marketing.
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-coastal-grandmother, recipe-warm-restraint, style-cream-humanist]
  notForUseWhen: Tech, B2B, modern minimal.

---

- styleId: shore-color
  name: Stephen Shore Uncommon Places banal-color
  era: 1970s
  category: fine-art
  visualSignatures:
    - 4x5 large format, deep depth of field, full edge sharpness
    - Saturated 1970s color, slight cyan or magenta cast
    - Banal American subject: motel parking lot, dinette plate, gas pump
    - Composition mathematically organized
    - Sky a third, foreground a third, the strange middle ground
  promptKeywords:
    primary: [1973 American main street, parking lot at noon, gas station, dinette table, mathematically organized composition]
    lighting: [hard noon sun, even flat lighting, deep shadows under awnings]
    cameraOrLens: [4x5 large format view camera, 90mm equivalent, f/22]
    filmStockOrPostProcessing: [Kodak 4x5 transparency, slight cyan cast, saturated period color, every-grain-sharp]
    mood: [observed, attentive, banal-transformed]
    avoidKeywords: [shallow focus, candid, dramatic, glamorous, modern]
  namedReferences:
    photographers: [Stephen Shore, William Eggleston, Joel Sternfeld]
    magazines: [Aperture, Steidl monographs]
    movements: [New Color Photography, New Topographics adjacent]
    brands: [archival editorial, fine art print]
  examplePromptTemplate: |
    Color photograph of an empty motel parking lot at noon in 1973 Texas, a single yellow Buick parked diagonally, ice-machine and sun-bleached sign in the middle ground, flat blue sky filling the upper third. Hard noon sun, deep shadows under the motel awning, even flat lighting. Shot on a 4x5 large format view camera at f/22, Kodak 4x5 transparency, saturated 1970s color, slight cyan cast, edge-to-edge sharpness. Observed, attentive, banal-transformed mood. Stephen Shore Uncommon Places fine-art style.
  whenToUse: Editorial fine-art content, slow travel brands, archive-driven storytelling, brand books that want gravitas without gloss.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, style-serif-warm-paper, recipe-warm-restraint]
  notForUseWhen: Conversion product, fashion, anything fast.

---

- styleId: goldin-diary
  name: Nan Goldin diary flash
  era: 1980s-current
  category: fine-art
  visualSignatures:
    - Direct on-camera flash in intimate domestic interiors
    - Saturated film color, deep oranges and reds
    - Subjects mid-life: in bed, in bathroom mirror, smoking, dressing
    - Imperfect framing, slightly tilted, sometimes blurred
    - LGBTQ+ chosen-family subjects
  promptKeywords:
    primary: [intimate bedroom interior, subject mid-dressing, bathroom mirror, smoking, imperfect framing]
    lighting: [hard direct on-camera flash, available tungsten ambient retained]
    cameraOrLens: [Nikon F2 with on-camera flash, 35mm lens]
    filmStockOrPostProcessing: [Kodachrome 64 or Ektachrome, saturated reds and ambers, slight grain]
    mood: [intimate, vulnerable, honest, lived]
    avoidKeywords: [studio, retouched, posed, glamour, professional model]
  namedReferences:
    photographers: [Nan Goldin, Ryan McGinley (when intimate), Larry Clark]
    magazines: [Aperture, Artforum, Visionaire]
    movements: [snapshot aesthetic, diary photography, queer fine art]
    brands: [Marc Jacobs Heaven, Calvin Klein 1990s when intimate]
  examplePromptTemplate: |
    Intimate flash photograph of two people sitting on the edge of an unmade bed in a small apartment, one half-dressed in a slip, the other in a t-shirt smoking, slight tilt to the framing, hard direct on-camera flash with available tungsten lamp ambient retained, saturated reds and ambers, slight grain. Shot on a Nikon F2 with on-camera flash and a 35mm lens, Kodachrome 64. Intimate, vulnerable, honest, lived mood. Nan Goldin Ballad of Sexual Dependency diary style.
  whenToUse: Indie fashion, LGBTQ-targeted campaigns, music for indie scenes, AIDS-history editorial, intimate documentary content.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-cottagegoth, aesthetic-dark-academia, aesthetic-dreamcore]
  notForUseWhen: Family-friendly product, B2B, anything wholesome.

---

- styleId: weingart-staged
  name: Staged conceptual fine-art (Wolfgang Weingart adjacent)
  era: current
  category: fine-art
  visualSignatures:
    - Highly constructed scene, every element placed intentionally
    - Single bold color or single bold prop
    - Studio lighting controlled to near-flat
    - Slight surreal: object out of context, scale off
    - Saturated single hue, painterly
  promptKeywords:
    primary: [single oversized object, neutral plaster room, surreal scale, deliberate placement, painterly tonality]
    lighting: [single soft window or single softbox, no fill, even falloff]
    cameraOrLens: [Hasselblad medium format, 80mm, f/8]
    filmStockOrPostProcessing: [single-hue saturation, painterly highlight, retained shadow detail]
    mood: [contemplative, surreal, deliberate]
    avoidKeywords: [candid, snapshot, journalism, busy composition]
  namedReferences:
    photographers: [Maurizio Cattelan-Toiletpaper, Roe Ethridge, Jamie Hawkesworth (staged)]
    magazines: [Toiletpaper Magazine, Apartamento, Modern Matter]
    movements: [post-internet still life, conceptual fashion]
    brands: [Loewe campaigns, Acne Studios, JW Anderson]
  examplePromptTemplate: |
    A single oversized ceramic lemon sitting on a small wooden stool in the corner of an empty plaster-walled room, scale slightly off, every element deliberately placed. Single soft daylight from a high window upper-right, no fill, even falloff into the corner shadow. Shot on a Hasselblad medium format with an 80mm at f/8, single-hue yellow saturation against the warm plaster, painterly highlight, retained shadow detail. Contemplative, surreal, deliberate mood. Conceptual fine-art still life, Toiletpaper Magazine adjacent.
  whenToUse: High-concept editorial, luxury fashion campaign, perfume, niche book covers, gallery print.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-dreamcore, style-bold-display, aesthetic-anti-design]
  notForUseWhen: Mass-market product, B2B SaaS, anything quick-to-decode.

---

- styleId: cereal-lifestyle
  name: Cereal magazine slow-travel lifestyle
  era: current
  category: lifestyle
  visualSignatures:
    - Cool muted palette, slight blue-gray cast
    - Architectural lines, modernist interiors, empty landscape
    - Single human as small scale element, not the subject
    - Soft overcast or window light, no hard shadow
    - Negative space dominant
  promptKeywords:
    primary: [architectural modernist interior, single small human, soft overcast, cool muted palette, generous negative space]
    lighting: [soft overcast daylight, large window light, no hard shadow]
    cameraOrLens: [Fuji GFX medium format, 50mm equivalent, f/5.6]
    filmStockOrPostProcessing: [cool muted color grade, slight blue-gray cast, retained highlight detail]
    mood: [calm, considered, slow]
    avoidKeywords: [warm, saturated, busy, crowd, motion]
  namedReferences:
    photographers: [Rich Stapleton for Cereal, Salva Lopez, Mariell Lind Hansen]
    magazines: [Cereal, Openhouse, Apartamento, Avaunt]
    movements: [slow travel, quiet lifestyle editorial]
    brands: [COS journal, The Row, Aesop hospitality, Nordic small hotels]
  examplePromptTemplate: |
    A small human figure walking through a wide cool-toned concrete and oak-floor modernist apartment interior, generous negative space, cool muted palette dominated by gray and oak. Soft overcast daylight from a large window upper-left, no hard shadow. Shot on a Fuji GFX medium format with a 50mm equivalent at f/5.6, cool muted color grade, slight blue-gray cast, retained highlight detail. Calm, considered, slow mood. Cereal magazine slow-lifestyle editorial.
  whenToUse: Hospitality, real estate, modernist furniture, Scandi brands, slow-lifestyle apps, premium travel.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, recipe-restrained-ai-marketing, style-restrained-hairline, style-cream-humanist]
  notForUseWhen: Tech B2B, fast-paced consumer, anything kinetic.

---

- styleId: kinfolk-warm-minimal
  name: Kinfolk warm minimal editorial
  era: 2011-current
  category: lifestyle
  visualSignatures:
    - Warm muted palette, beige, cream, soft brown
    - Soft window light, often blown highlights, no hard shadow
    - Subjects in everyday activity: cooking, reading, folding linen
    - Knit textures, ceramic mugs, linen, dried flowers
    - Generous negative space, slow composition
  promptKeywords:
    primary: [woman folding linen, knit sweater, ceramic mug of tea, soft cream interior, slow activity]
    lighting: [soft window light, slightly blown highlights, no hard shadow]
    cameraOrLens: [Canon 5D, 50mm at f/2.8]
    filmStockOrPostProcessing: [warm beige palette, slightly faded, soft contrast]
    mood: [slow, warm, considered]
    avoidKeywords: [saturated, hard light, kinetic, urban grit]
  namedReferences:
    photographers: [Parker Fitzgerald, Andrew Jacono, Nicole Franzen]
    magazines: [Kinfolk, The Gentlewoman, Toast]
    movements: [Portland-Brooklyn slow lifestyle 2011-2018]
    brands: [Toast, Frama, Skagerak, Bellocq Tea, Heath Ceramics]
  examplePromptTemplate: |
    A woman folding cream linen at a soft-cream kitchen counter, wearing a wheat-colored knit sweater, a small ceramic mug of tea steaming beside her, dried lavender in a stoneware vase upper-right. Soft window light from camera-left with slightly blown highlights on the linen, no hard shadow. Shot on a Canon 5D with a 50mm at f/2.8, warm beige palette, slightly faded soft contrast. Slow, warm, considered mood. Kinfolk warm-minimal editorial.
  whenToUse: Wellness, slow lifestyle, hospitality, home goods, tea and coffee brands, parenting for older demos.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, style-cream-humanist, aesthetic-cottagecore, aesthetic-coastal-grandmother]
  notForUseWhen: Tech, fast e-comm, B2B, edgy fashion.

---

- styleId: cos-lookbook
  name: COS lookbook clean editorial
  era: current
  category: lookbook
  visualSignatures:
    - Plaster wall or seamless paper backdrop, neutral palette
    - Subject 3/4 to full-body, garment-first composition
    - Soft window or single large softbox
    - Slightly cool tone, faithful color
    - Minimal styling, no smile, slight forward posture
  promptKeywords:
    primary: [full-body garment-first composition, neutral plaster backdrop, neutral pose, no smile, slight forward step]
    lighting: [single large softbox or north window, soft even, gentle shadow]
    cameraOrLens: [Sony A7R, 50mm or 85mm, f/4]
    filmStockOrPostProcessing: [faithful color, slightly cool, retained fabric texture]
    mood: [composed, modern, restrained]
    avoidKeywords: [hard flash, busy backdrop, smile, candid, retouched skin perfection]
  namedReferences:
    photographers: [Karim Sadli, Daniel Shea, Heji Shin]
    magazines: [COS journal, The Gentlewoman lookbook content]
    movements: [modern minimal lookbook, post-COS clean editorial]
    brands: [COS, Arket, Lemaire, Studio Nicholson, The Row]
  examplePromptTemplate: |
    Full-body lookbook photograph of a person in an oversized wool coat over a knit polo and wide-leg trousers, standing against a plaster wall backdrop, neutral pose with a slight forward step, looking just past camera-right with no smile. Single large softbox from camera-left, soft even gentle shadow on the wall. Shot on a Sony A7R with an 85mm at f/4, faithful slightly-cool color, retained wool texture and trouser drape. Composed, modern, restrained mood. COS lookbook editorial.
  whenToUse: Apparel e-comm, contemporary fashion lookbook, modern minimal hospitality, premium home goods, premium tech apparel.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-restrained-ai-marketing, style-restrained-hairline, style-oversized-neo-grotesque]
  notForUseWhen: Loud or kinetic brand, fast e-comm with high SKU count.

---

- styleId: surreal-still-life
  name: Surreal still-life conceptual
  era: current
  category: conceptual
  visualSignatures:
    - Single saturated backdrop, no horizon
    - Object combinations that should not exist (banana with chain, ice on velvet)
    - Hard directional light with clean drop shadow
    - Single hue dominant
    - Studio precision but conceptual content
  promptKeywords:
    primary: [single saturated backdrop, surreal object combination, hard clean drop shadow, single dominant hue]
    lighting: [single hard directional studio light, no fill, clean shadow on backdrop]
    cameraOrLens: [Phase One IQ4, 100mm macro, f/8]
    filmStockOrPostProcessing: [single-hue palette, oversaturated, dust-clean retouch]
    mood: [surreal, ironic, witty]
    avoidKeywords: [natural light, candid, soft, busy backdrop]
  namedReferences:
    photographers: [Roe Ethridge, Bobby Doherty, Sarah Illenberger]
    magazines: [New York Magazine still life, Toiletpaper, Wallpaper*]
    movements: [post-internet still life, modernist conceptual]
    brands: [Hermès still life, Glossier campaign, Aesop conceptual]
  examplePromptTemplate: |
    A single ripe banana balanced upright on a small silver chain coiled on a flat saturated cobalt blue backdrop, no horizon, hard directional studio light from camera-right casting a clean diagonal shadow, dominant cobalt single-hue palette. Shot on a Phase One IQ4 with a 100mm macro at f/8, oversaturated, dust-clean retouch. Surreal, ironic, witty mood. Conceptual still-life editorial in Toiletpaper Magazine lineage.
  whenToUse: High-concept beauty, snack and beverage editorial, conceptual e-comm hero, gallery and magazine, ironic premium.
  pairsWith:
    prototypeStyles: [aesthetic-y2k-memphis-loud, aesthetic-wacky-pomo, style-bold-display, aesthetic-acid-graphics]
  notForUseWhen: Anything sincere, B2B, wellness, heritage.

---

- styleId: dreamy-haze
  name: Dreamy soft haze portrait
  era: current
  category: conceptual
  visualSignatures:
    - Diffusion filter or smoke, soft halation around all highlights
    - Pale pastel palette, slight pink or peach cast
    - Subject in soft focus, edges dissolving
    - Slow exposure feel, light bloom
    - Often outdoors at golden hour with backlight
  promptKeywords:
    primary: [backlit subject in pale field, diffusion bloom, peach-pink cast, dissolving edges, dreamy halation]
    lighting: [backlit golden hour sun, soft diffusion, light bloom]
    cameraOrLens: [Canon 5D, 85mm at f/1.4, BPM Pro Mist filter]
    filmStockOrPostProcessing: [pastel grade, peach cast, soft halation, light bloom, mild diffusion]
    mood: [dreamy, tender, suspended]
    avoidKeywords: [hard flash, gritty, dark, saturated, sharp focus]
  namedReferences:
    photographers: [Petra Collins, Solve Sundsbo when soft, Carlota Guerrero]
    magazines: [Office, Polyester, Rookie, Self Service]
    movements: [Tumblr soft-grunge, post-Petra Collins dreamy]
    brands: [Glossier, Gucci Bloom, Acne Studios pastel campaign]
  examplePromptTemplate: |
    Half-body portrait of a young person standing in a pale wheat field at golden hour, backlit by low sun, hair dissolving into bright haze, soft diffusion bloom around every highlight, pale peach-pink cast. Shot on a Canon 5D with an 85mm at f/1.4 through a Pro Mist diffusion filter, pastel grade, soft halation, light bloom. Dreamy, tender, suspended mood. Petra Collins-era dreamy haze editorial.
  whenToUse: Skincare and beauty for younger demos, music video stills, indie fashion, fragrance, Gen-Z wellness.
  pairsWith:
    prototypeStyles: [aesthetic-dreamcore, aesthetic-angelcore, aesthetic-fairycore, aesthetic-positivity-kawaii]
  notForUseWhen: Hardware product, B2B, anything needing clarity and detail.

---

- styleId: fantasy-glow
  name: Fantasy glow magical lighting
  era: current
  category: conceptual
  visualSignatures:
    - Volumetric god-rays cutting through atmosphere
    - Rim-lit subject with halo of warm light
    - Forest, cathedral, ruins, or fantasy environment
    - Saturated emerald and gold palette
    - Slight cinematic anamorphic flare optional
  promptKeywords:
    primary: [forest clearing, god-rays through canopy, rim-lit subject, halo of light, emerald and gold palette]
    lighting: [volumetric god-rays, warm rim light, soft natural fill]
    cameraOrLens: [Arri Alexa, 50mm or 85mm with cinematic glow filter]
    filmStockOrPostProcessing: [warm cinematic grade, emerald saturation, gentle halation, slight grain]
    mood: [magical, reverent, dreamlike]
    avoidKeywords: [flash, hard noon sun, urban, modern]
  namedReferences:
    photographers: [fantasy cinematography, Roger Deakins when atmospheric, Annie Leibovitz Disney Dream Portraits]
    magazines: [film stills publications]
    movements: [fantasy cinema visual canon, Disney Dream Portraits]
    brands: [Disney, fantasy publishers, RPG marketing, Sephora premium fragrance]
  examplePromptTemplate: |
    A figure in a long velvet cloak standing in a sunlit forest clearing, volumetric god-rays cutting through the canopy from upper-right, warm rim light haloing the subject, soft natural fill from the moss-covered ground. Shot on an Arri Alexa with an 85mm and a cinematic glow filter, warm grade, emerald saturation, gentle halation, slight grain. Magical, reverent, dreamlike mood. Fantasy editorial in the lineage of Annie Leibovitz Disney Dream Portraits.
  whenToUse: Game marketing, fantasy publishing, premium fragrance with mythological angle, theme park, niche perfume.
  pairsWith:
    prototypeStyles: [aesthetic-fairycore, aesthetic-cottagegoth, aesthetic-cottagecore, aesthetic-solarpunk]
  notForUseWhen: B2B, modern minimal, tech product.

---

- styleId: magic-glow
  name: Magic glow product or beauty
  era: current
  category: beauty
  visualSignatures:
    - Internal glow as if subject is lit from within
    - Slight bloom around edges, soft particle dust
    - Saturated single-hue background, often warm gold or rose
    - Macro detail of skin, product, jewelry catching the glow
    - Studio precision with conceptual overlay
  promptKeywords:
    primary: [internal subject glow, soft particle dust, single-hue gold or rose background, macro skin detail, bloom]
    lighting: [single soft warm key, glow overlay, particle backlight]
    cameraOrLens: [Canon R5, 100mm macro at f/4]
    filmStockOrPostProcessing: [warm gold or rose grade, soft bloom, particle highlights, retained skin texture]
    mood: [enchanted, luminous, magical]
    avoidKeywords: [hard flash, cool, gritty, harsh]
  namedReferences:
    photographers: [Sølve Sundsbø, Nick Knight beauty]
    magazines: [Allure, Vogue Beauty, Numéro Beauty]
    movements: [post-2015 beauty CGI-photo hybrid]
    brands: [Lancôme, Charlotte Tilbury, Dior beauty, Pat McGrath]
  examplePromptTemplate: |
    Macro beauty shot of a cheek with a single dusting of gold pigment shimmer, the skin appearing lit from within, soft particle dust floating in the warm gold ambient, single-hue rose-gold background. Single soft warm key light from camera-left with a glow overlay, particle backlight from upper-right. Shot on a Canon R5 with a 100mm macro at f/4, warm gold grade, soft bloom, particle highlights, retained skin texture. Enchanted, luminous, magical mood. Magic glow beauty editorial.
  whenToUse: Luxury beauty, premium fragrance, jewelry, fine watch detail, anything aspirational-magical.
  pairsWith:
    prototypeStyles: [aesthetic-angelcore, aesthetic-fairycore, style-holographic, style-claymorphism]
  notForUseWhen: Documentary, gritty, B2B, hardware.

---

- styleId: circuit-bent-glitch
  name: Circuit-bent glitch photo effect
  era: current
  category: conceptual
  visualSignatures:
    - Datamoshing, channel shift, scanline artifacts
    - Pixel sorting in vertical or horizontal stripes
    - Saturated RGB primaries
    - Subject recognizable but corrupted
    - Often layered with VHS noise, JPEG compression artifacts
  promptKeywords:
    primary: [datamoshed subject, channel shift, pixel sorting stripes, RGB primaries, JPEG compression artifacts]
    lighting: [original lighting irrelevant, post-processed corruption]
    cameraOrLens: [any source]
    filmStockOrPostProcessing: [glitch art treatment, datamoshing, channel shift, scanline overlay, posterized color]
    mood: [aggressive, broken, kinetic]
    avoidKeywords: [clean, smooth, calm, restrained]
  namedReferences:
    photographers: [glitch art community, Rosa Menkman, Phillip Stearns]
    magazines: [Wired retro features, Vice]
    movements: [glitch art, circuit bending, post-internet aesthetics]
    brands: [Cyberdog, Vetements glitch campaigns, Hyundai glitch ads]
  examplePromptTemplate: |
    Editorial portrait of a young person in a chrome jacket transformed by circuit-bent glitch treatment, datamoshed channel shift across the face, vertical pixel-sorting stripes through the lower frame, saturated RGB primaries, JPEG compression artifacts, scanline overlay, slight VHS noise. Aggressive, broken, kinetic mood. Glitch art editorial treatment.
  whenToUse: Music streaming art, electronic music posters, cyberpunk-themed game key art, edgy fashion, indie experimental editorial.
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-acid-graphics, style-holographic]
  notForUseWhen: Premium, B2B, anything restrained or sincere.

---

- styleId: skate-zine
  name: Skate zine 35mm flash
  era: 1990s-current
  category: documentary
  visualSignatures:
    - 35mm point and shoot, on-camera flash
    - Mid-trick or mid-fall skate action
    - Concrete plazas, ledges, handrails at night
    - Grain heavy, slight overexposure, off-kilter framing
    - Subject often partially out of frame
  promptKeywords:
    primary: [skater mid-trick, concrete plaza, on-camera flash at night, off-kilter framing, partial subject out of frame]
    lighting: [hard on-camera flash, ambient streetlight, fall-off to black]
    cameraOrLens: [Yashica T4 or Olympus mju II, 35mm lens]
    filmStockOrPostProcessing: [Kodak Gold 200 push-processed, heavy grain, slight overexposure]
    mood: [raw, kinetic, in-the-action]
    avoidKeywords: [studio, posed, retouched, soft light, glossy]
  namedReferences:
    photographers: [Thrasher house photographers, Atiba Jefferson, Ari Marcopoulos]
    magazines: [Thrasher, Slap, Quartersnacks]
    movements: [90s and 00s skate zine culture]
    brands: [Supreme, Palace, Polar Skate Co, Adidas Skateboarding]
  examplePromptTemplate: |
    Frame of a skater mid-kickflip over a concrete ledge at a downtown plaza at night, board visible mid-air, foot partially out of frame, hard on-camera flash punching the subject forward against ambient streetlight in the background. Shot on a Yashica T4 with a 35mm lens, Kodak Gold 200 push-processed, heavy grain, slight overexposure on the white t-shirt. Raw, kinetic, in-the-action mood. Skate zine 35mm flash editorial.
  whenToUse: Streetwear, skateboard brands, youth-targeted music, energy drinks, action sports.
  pairsWith:
    prototypeStyles: [aesthetic-web-brutalism, recipe-brutalist-web, aesthetic-acid-graphics, aesthetic-y2k-memphis-loud]
  notForUseWhen: Premium, wellness, luxury, family.

---

- styleId: backstage-fashion
  name: Backstage editorial BTS
  era: current
  category: BTS
  visualSignatures:
    - Available light, sometimes mixed with hair-light or makeup-station tungsten
    - Models mid-prep: hair in foil, robe, half-makeup, phone in hand
    - Cluttered context: garment racks, clothespins, stylist's hands
    - Slightly desaturated, journalism-tone
    - Wide-ish 28-35mm framing
  promptKeywords:
    primary: [model in robe mid-prep, garment racks behind, hair in foil, phone in hand, half-makeup]
    lighting: [available mixed tungsten, soft window, slight motion blur tolerated]
    cameraOrLens: [Leica Q2, 28mm at f/2]
    filmStockOrPostProcessing: [natural color, slight desaturation, journalism tone]
    mood: [observed, in-process, intimate-professional]
    avoidKeywords: [studio polish, retouched, posed, glamour final-look]
  namedReferences:
    photographers: [Tim Walker BTS, Sonny Vandevelde, Kevin Tachman]
    magazines: [Vogue Runway BTS, AnOther backstage features]
    movements: [backstage editorial, Show Studio BTS]
    brands: [used by all major fashion houses for BTS social content]
  examplePromptTemplate: |
    Backstage photograph of a model in a white silk robe sitting in a director's chair, hair in foil curlers, phone in hand, half-applied makeup, garment racks of metallic dresses out of focus behind. Available mixed tungsten from makeup station with soft natural light from a window upper-right, slight tolerated motion blur on the phone. Shot on a Leica Q2 with a 28mm at f/2, natural color with slight desaturation. Observed, in-process, intimate-professional mood. Backstage editorial BTS, fashion week documentary.
  whenToUse: Behind-the-scenes content for fashion, beauty launches, behind-the-craft brand storytelling, documentary marketing.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, aesthetic-corporate-grunge, recipe-restrained-ai-marketing]
  notForUseWhen: Polished hero, conversion product page.

---

- styleId: archival-found-photo
  name: Archival found-photograph treatment
  era: 1950s-90s
  category: archival
  visualSignatures:
    - Period-correct degradation: faded color, slight yellowing, edge wear
    - Snapshot-album composition, slightly off-center
    - Period clothing, vehicles, signage
    - Subject often unaware, candid, family snapshot tone
    - Slight white border, scan dust
  promptKeywords:
    primary: [1978 family snapshot, period clothing, off-center composition, faded color, slight white border]
    lighting: [available period light, often direct sun or kitchen tungsten]
    cameraOrLens: [Kodak Instamatic, Polaroid, period point-and-shoot]
    filmStockOrPostProcessing: [Kodachrome 64 faded, slight yellowing, edge wear, scan dust, slight white border, color shift toward magenta with age]
    mood: [nostalgic, lived, found]
    avoidKeywords: [retouched, sharp, modern, posed editorial]
  namedReferences:
    photographers: [n/a — found-photograph aesthetic]
    magazines: [Found Magazine, Slice of Life archive, Anthology]
    movements: [vernacular photography, found photo, family-album aesthetic]
    brands: [Tuna Melts My Heart, vintage merch brands, era-themed apparel]
  examplePromptTemplate: |
    A 1978 family snapshot of three children on a faded yellow couch in a wood-paneled living room, period clothing and a console TV in the background, off-center snapshot composition, slight motion blur on the youngest child's wave. Faded Kodachrome 64 with slight magenta shift, scan dust, edge wear, soft white border, slight yellowing of the highlights. Shot on a Kodak Instamatic 110 with available kitchen tungsten light. Nostalgic, lived, found mood. Archival vernacular photography.
  whenToUse: Heritage brand, nostalgia marketing, music for older demos, memoir publishing, period drama promo.
  pairsWith:
    prototypeStyles: [aesthetic-cluttercore, recipe-readcv, aesthetic-corporate-grunge, aesthetic-cottagecore]
  notForUseWhen: Modern tech, restrained luxury, anything aspirational-future.

---

- styleId: laundry-light-lookbook
  name: Daylight lookbook plaster wall
  era: current
  category: lookbook
  visualSignatures:
    - Empty pale plaster or stucco backdrop, natural texture
    - Side natural light from open door or large window
    - Single subject 3/4 to full-body in garment
    - Subdued styling, casual real-world pose
    - Sometimes outdoor against a textured wall
  promptKeywords:
    primary: [pale plaster backdrop, side daylight, full-body garment, casual real pose, textured wall outdoor]
    lighting: [natural side daylight from open door or window, soft natural fill]
    cameraOrLens: [Sony A7IV, 50mm at f/2.8]
    filmStockOrPostProcessing: [natural color, faithful tonality, slight grain]
    mood: [easy, considered, real-world]
    avoidKeywords: [studio flash, polished, busy, kinetic]
  namedReferences:
    photographers: [Daniel Riera, Quentin de Briey, Joanna Totolici]
    magazines: [The Gentlewoman, AnOther, Self Service]
    movements: [post-Margiela quiet lookbook, daylight editorial]
    brands: [Lemaire, Toteme, Studio Nicholson, Khaite]
  examplePromptTemplate: |
    Full-body lookbook of a person in a sand-colored linen suit standing against a textured pale plaster outdoor wall, side daylight from camera-left casting a soft natural shadow camera-right, casual real-world pose with one hand in pocket. Shot on a Sony A7IV with a 50mm at f/2.8, natural faithful color, slight grain, retained linen texture. Easy, considered, real-world mood. Daylight plaster-wall lookbook editorial.
  whenToUse: Premium contemporary apparel, slow fashion, modern minimal lookbooks, hospitality lifestyle.
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, recipe-restrained-ai-marketing, style-cream-humanist, style-restrained-hairline]
  notForUseWhen: Fast fashion volume e-comm, loud or kinetic brand.

---

- styleId: high-key-beauty
  name: High-key beauty white seamless
  era: current
  category: beauty
  visualSignatures:
    - Pure white seamless backdrop, even all around
    - Ring flash or clamshell beauty lighting, near-shadowless
    - Tight head and shoulders or beauty crop
    - Skin texture retained but smoothed
    - Sharp eyes, gloss on lips, single accent jewelry
  promptKeywords:
    primary: [tight beauty crop, white seamless, sharp eyes, gloss lip, single accent earring]
    lighting: [clamshell beauty: large softbox above and reflector below, near-shadowless]
    cameraOrLens: [Canon R5, 100mm macro at f/8]
    filmStockOrPostProcessing: [pure even white, retained skin texture, slight color saturation push on lips]
    mood: [graphic, clean, iconic]
    avoidKeywords: [moody, shadow, environment, candid]
  namedReferences:
    photographers: [Solve Sundsbo, Nick Knight, Steven Meisel beauty]
    magazines: [Allure, Vogue beauty section]
    movements: [modern beauty editorial, post-2010 cosmetics canon]
    brands: [MAC, Glossier (when high-key), Pat McGrath, Fenty]
  examplePromptTemplate: |
    Tight beauty crop of a woman's face on a pure white seamless backdrop, sharp focus on the eyes, glossy lip highlight, single architectural gold earring. Clamshell beauty lighting: large softbox above, white reflector below, near-shadowless. Shot on a Canon R5 with a 100mm macro at f/8, pure even white, retained skin pore texture, slight saturation push on the lip. Graphic, clean, iconic mood. High-key beauty editorial.
  whenToUse: Cosmetics e-comm hero, beauty product launch, fragrance for modern minimal brands.
  pairsWith:
    prototypeStyles: [recipe-bento-marketing, style-glassmorphism, style-liquid-glass, recipe-restrained-ai-marketing]
  notForUseWhen: Editorial mood, lifestyle, anything narrative.

---

- styleId: bowie-rock-glamour
  name: Rock-glamour stage editorial
  era: 1970s-1980s
  category: glamour
  visualSignatures:
    - Stage lighting recreated in studio: hot rim from behind, single colored gel
    - Glitter, makeup, asymmetric costume, theatrical
    - Smoke or haze in air
    - Saturated single hue background, often red or blue
    - Subject mid-performance pose
  promptKeywords:
    primary: [theatrical costume, glitter makeup, hot rim from behind, smoke haze, single hue background, mid-performance]
    lighting: [hard rim backlight, single colored gel ambient, smoke haze in air]
    cameraOrLens: [Hasselblad 500CM, 80mm]
    filmStockOrPostProcessing: [Kodak Ektachrome saturated, slight haze diffusion, retained costume detail]
    mood: [theatrical, defiant, iconic]
    avoidKeywords: [candid, natural light, restrained]
  namedReferences:
    photographers: [Mick Rock, Bob Gruen, Lynn Goldsmith]
    magazines: [Rolling Stone covers, Creem, NME]
    movements: [rock photography canon, glam rock visual era]
    brands: [music marketing, Gucci 2017 archive, Saint Laurent rock-revival]
  examplePromptTemplate: |
    Half-body editorial of a performer in glitter makeup and an asymmetric sequined jumpsuit, mid-performance pose with one arm raised, head tilted back. Hot rim backlight from upper-right catching the glitter, smoke haze in the air, single blue colored gel ambient from camera-left. Shot on a Hasselblad 500CM with an 80mm, Kodak Ektachrome saturated, slight diffusion, retained sequin detail. Theatrical, defiant, iconic mood. 1970s glam-rock stage editorial in the Mick Rock lineage.
  whenToUse: Music marketing, concert posters, fashion editorial for music-adjacent brands, retro nostalgia.
  pairsWith:
    prototypeStyles: [aesthetic-vector-hands-up, aesthetic-y2k-memphis-loud, aesthetic-rgb-gamer, aesthetic-acid-design]
  notForUseWhen: Restrained luxury, B2B, wellness.

---

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
