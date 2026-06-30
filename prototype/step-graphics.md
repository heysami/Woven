# Step nine - graphic elements

Same rule as everything else: inherited from genre, applied top-down, leaning on primitives. But because graphics are where the AI tell shows up most visibly, the rules are stricter.

### Categories have different rules

| Category | Function | Decided when |
|---|---|---|
| **Iconography** | Functional - labels and affordances | With components, never separately |
| **Brand mark / logo** | Identity - fixed constant | At step zero, before anything else |
| **Data viz** (charts, maps, trees, heatmaps) | Functional - the data IS the graphic | Drives the panel layout |
| **Empty-state illustrations** | Mixed - signals "nothing here" + carries genre tone | With the empty-state component |
| **Hero illustrations / product shots** | Decorative + narrative | With the hero section |
| **Background patterns / gradients / blobs** | Decorative only - mood | Last, only if genre demands |
| **Editorial ornaments** (drop caps, dingbats, rules) | Genre-mandatory decoration | With the body component |
| **Photography** | Mixed - content + texture | At the point the slot exists |

### Three rules govern decoration

1. **Default to no graphics.** Empty space and typography are graphics enough. The bar to add a graphic is high. If the panel "looks empty," try larger type or more confident negative space first.
2. **Functional graphics earn pixels by carrying data.** A status dot signals live state. A sparkline shows trend. A confidence-map track shows score. **If the same information could be conveyed by a number or label alone, the graphic is decorative.** Use only when visualization adds comprehension that text doesn't.
3. **Decorative graphics earn pixels only when the genre demands them.** Editorial demands drop caps. Bento demands per-cell visual treatments. Marketing demands hero imagery. Brutalist demands intentional ugly graphics. **Control-room dashboards forbid decoration entirely.** Match decoration to genre, not to "panel looks empty."

The corollary that matters: **the rarer the decoration, the more weight each instance carries.** One ornament in a sparse design is loud and intentional. Five identical ornaments dilute each other. Restraint is the master move.

### When the product is about a person, the person is not optional

The "default to no graphics" rule is overridden by ONE subject: people. If the product is about a person or people - an artist, musician, founder, creator, performer, author, team, character, or any brand whose identity IS a human - then a real human image is **content, not decoration**, and it must appear, prominently. Scaffold a real human-imagery slot at the hero (and usually an about / press / bio section too):

```html
<img data-slot="hero-portrait" data-medium="raster-photo"
     alt="<who the person is, described as a photographic subject>">
```

Use human-descriptive alt text so the photography pass classifies it correctly and fills it with a real, vibe-matched photograph. The failure to avoid: a person-centred product whose hero is a logo / wordmark / mascot / product shot and **zero human pixels** (a music-artist page whose hero is a chrome wordmark + a worm mascot has dropped its own subject). Do not substitute a placeholder rectangle or an illustrated stand-in for a real human when the aesthetic is photographic.

The representation matches the genre: a photographic aesthetic → real photography in that register (Y2K-flash-glam, editorial, candid, golden-hour, etc.); an illustration-only aesthetic (corporate-memphis, anime, pixel) → the human rendered in that register. What is never acceptable is the human being absent.

### Position rules - also genre-inherited

- **Brand mark**: top-left, fixed size, never moves (almost universal).
- **Empty-state illustration**: centered in panel, illustration ~120-200px above caption above CTA.
- **Hero illustration**: full-bleed behind text *or* right-side split *or* top-of-stack - pick by genre.
- **Charts / data viz**: takes the panel area; padding and title minimal frame.
- **Background pattern**: low-contrast, section-clipped, fixed-position, behind content.
- **Editorial marginalia**: hangs in the margin column, smaller than body, typographically distinct.

### Sequencing - when graphics are decided

There's no separate "graphics phase." Three timings:

- **With genre commit (step zero/one)**: brand mark, shape language, pattern vocabulary
- **With the component that holds them**: icons, data viz (drives panel layout), empty states, editorial ornaments
- **After the layout, if at all**: background patterns, decorative shapes

**Functional graphics dictate layout. Decorative graphics fill slack. Brand graphics are constants from the start.**

### Rules that prevent the AI tell

The AI tell on graphics shows up as: generic dribbble illustrations, soft purple gradient blobs, isometric people-with-laptops, abstract "tech" patterns, charts with placeholder data that looks chart-shaped but doesn't make sense.

To prevent it:

1. **Build functional graphics from primitives.** Inline SVG with real geometry, CSS bars and tracks. Draw the bare elements yourself - never import a chart library. This forces shape-language tokens to apply.
2. **Replace illustrations with typography or geometric shapes when possible.** Big numbers, oversized type, single solid blocks of color, hairline diagrams. These inherit the design system automatically and never look generic.
3. **Use placeholder rectangles for imagery you don't have.** `<div class="img-placeholder" data-aspect="4:3">PHOTO · café interior</div>`. More honest than a stock blob and often reads better.
4. **If you must have an illustration, name it specifically.** "Hand-drawn pencil sketch of a café floor plan" not "hero illustration." Specific cues unlock specific corners of the inheritance bank.
5. **One decorative move per page, max.** The first one carries the genre. The second dilutes the first.
6. **Charts must use believable data.** If you're drawing a sparkline, use real data shape (rising trend with one anomaly, not random noise). If you're drawing a heatmap, the highs and lows should map to a believable story.
