# DrawKit / Blush Isometric Stickers (illust)

**Tag:** illust-drawkit-isometric-stickers  ·  **Category:** 3D  ·  **Role affinity:** spot-illustration

everyday objects (laptop, coffee, book) in true 2:1 isometric.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/illustration-library.md`](../docs/research/illustration-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
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
```

## When NOT to use

editorial magazine, brutalism, dark cinematic UI

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-linear-product-ui`
- `aesthetic-positivity-kawaii`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 189–223 of `docs/research/illustration-library.md`. Full index: `docs/research/illustration-library.index.json`._
